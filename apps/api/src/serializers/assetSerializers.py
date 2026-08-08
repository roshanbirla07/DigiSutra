import datetime
import logging
import uuid

from flask import g
from flask import abort
from sqlalchemy import func
from werkzeug.exceptions import HTTPException

from configuration.db_routing import db, session_rollback
from configuration.variables import (
    ASSET_ACCESS_EXPIRES_IN_DAYS,
    ASSET_ACCESS_MAX_DOWNLOADS,
    ASSET_DELIVERY_TOKEN_TTL_SECONDS,
)
from models.ledger import MarketplaceOrder, ProductAccess
from models.product import Product, ProductAsset, ProductAssetDownload
from services.s3_asset_gateway import S3AssetGateway, S3AssetGatewayError
from utils.auth import create_delivery_token


class AssetInputError(HTTPException):
    code = 400
    description = "Asset data is invalid"

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


class AssetSerializer(object):
    def __init__(self, data=None):
        self.data = data or {}
        self.gateway = S3AssetGateway()

    def get_product(self, product_uuid):
        product = Product.query.filter_by(uuid=product_uuid).first()
        if not product:
            raise AssetInputError("Product not found")
        return product

    def serialize_asset(self, asset):
        return {
            "uuid": asset.uuid,
            "product_uuid": asset.product.uuid if asset.product else None,
            "storage_provider": asset.storage_provider,
            "bucket_name": asset.bucket_name,
            "object_key": asset.object_key,
            "original_filename": asset.original_filename,
            "content_type": asset.content_type,
            "size_bytes": asset.size_bytes,
            "checksum_sha256": asset.checksum_sha256,
            "cloudfront_url": asset.cloudfront_url,
            "asset_status": asset.asset_status,
            "created_on": asset.created_on.isoformat() if asset.created_on else None,
            "modified_on": asset.modified_on.isoformat() if asset.modified_on else None,
        }

    def serialize_download(self, download):
        return {
            "uuid": download.uuid,
            "asset_uuid": download.asset.uuid if download.asset else None,
            "order_uuid": download.order_uuid,
            "downloaded_by": download.downloaded_by,
            "download_url": download.download_url,
            "user_agent": download.user_agent,
            "ip_address": download.ip_address,
            "created_on": download.created_on.isoformat() if download.created_on else None,
        }

    def _normalize_optional_int(self, value):
        if value in (None, ""):
            return None
        return int(value)

    def authorize_asset_access(self, asset_uuid, order_uuid):
        asset = ProductAsset.query.filter_by(uuid=asset_uuid).first()
        if not asset:
            raise AssetInputError("Asset not found")

        if not order_uuid:
            raise AssetInputError("order_uuid is required")

        auth_user = getattr(g, "user", None)
        if not auth_user:
            raise AssetInputError("Authentication required")

        order = MarketplaceOrder.query.filter_by(uuid=order_uuid).first()
        if not order:
            raise AssetInputError("Marketplace order not found")
        if order.buyer_id != auth_user.id:
            raise AssetInputError("Authenticated user does not own this order")
        if order.product_id != asset.product_id:
            raise AssetInputError("Asset does not belong to the purchased product")

        access = ProductAccess.query.filter_by(order_id=order.id).first()
        if not access or access.access_status != "granted":
            raise AssetInputError("Access is not currently granted for this order")
        if self._is_access_expired(access):
            raise AssetInputError("Access has expired")
        if self._has_download_limit_been_reached(access):
            raise AssetInputError("Download limit reached")

        return asset, order, access

    def _get_access_limit(self):
        try:
            limit = int(ASSET_ACCESS_MAX_DOWNLOADS)
        except (TypeError, ValueError):
            return None
        return limit if limit > 0 else None

    def _get_access_expiry_days(self):
        try:
            days = int(ASSET_ACCESS_EXPIRES_IN_DAYS)
        except (TypeError, ValueError):
            return None
        return days if days > 0 else None

    def _is_access_expired(self, access):
        expiry_days = self._get_access_expiry_days()
        if not expiry_days:
            return False
        created_on = access.created_on
        if not created_on:
            return False
        return created_on + datetime.timedelta(days=expiry_days) < datetime.datetime.utcnow()

    def _has_download_limit_been_reached(self, access):
        limit = self._get_access_limit()
        if not limit:
            return False
        current_count = int(access.download_count or 0)
        return current_count >= limit

    def _register_download(self, access):
        access.download_count = int(access.download_count or 0) + 1
        return access

    @session_rollback(db)
    def create_upload_target(self, validated_data=None):
        validated_data = dict(validated_data or self.data)
        product = self.get_product(validated_data.get("product_uuid"))
        auth_user = getattr(g, "user", None)
        if not auth_user:
            raise AssetInputError("Authentication required")
        if str(auth_user.user_type).lower() != "admin" and product.owner_id != auth_user.id:
            raise AssetInputError("Authenticated user does not own this product")
        object_key = validated_data.get("object_key") or f"products/{product.uuid}/{uuid.uuid4()}"
        asset = ProductAsset(
            uuid=f"asset::{uuid.uuid4()}",
            product_id=product.id,
            storage_provider="s3",
            bucket_name=validated_data.get("bucket_name") or "",
            object_key=object_key,
            original_filename=validated_data.get("original_filename"),
            content_type=validated_data.get("content_type") or "application/octet-stream",
            size_bytes=self._normalize_optional_int(validated_data.get("size_bytes")),
            cloudfront_url=self.gateway.cloudfront_url_for(object_key),
            asset_status="pending_upload",
        )
        if not asset.bucket_name:
            raise AssetInputError("bucket_name is required")
        db.session.add(asset)
        try:
            db.session.commit()
        except Exception as e:
            logging.error(f"Exception in Asset Creation Serializer :: {e}")
            abort(400)

        try:
            presigned = self.gateway.create_presigned_put_url(
                object_key=asset.object_key,
                content_type=asset.content_type or "application/octet-stream",
            )
        except S3AssetGatewayError as exc:
            asset.asset_status = "upload_failed"
            db.session.commit()
            raise AssetInputError(str(exc))

        asset.asset_status = "upload_url_issued"
        db.session.commit()
        return asset, presigned

    @session_rollback(db)
    def log_download(self, asset_uuid, payload):
        auth_user = getattr(g, "user", None)
        asset, order, access = self.authorize_asset_access(asset_uuid, payload.get("order_uuid"))
        self._register_download(access)
        download = ProductAssetDownload(
            uuid=f"download::{uuid.uuid4()}",
            asset_id=asset.id,
            order_uuid=order.uuid,
            downloaded_by=auth_user.uuid,
            download_url=payload.get("download_url") or asset.cloudfront_url,
            user_agent=payload.get("user_agent"),
            ip_address=payload.get("ip_address"),
        )
        asset.asset_status = payload.get("asset_status") or asset.asset_status
        db.session.add(download)
        try:
            db.session.commit()
        except Exception as e:
            logging.error(f"Exception in Asset Download Log Serializer :: {e}")
            abort(400)
        return download

    @session_rollback(db)
    def authorize_download(self, asset_uuid, payload):
        asset, order, access = self.authorize_asset_access(asset_uuid, payload.get("order_uuid"))
        self._register_download(access)
        db.session.commit()
        token_ttl = self._get_delivery_token_ttl()
        delivery_token = create_delivery_token(
            user_uuid=order.buyer.uuid,
            asset_uuid=asset.uuid,
            order_uuid=order.uuid,
            download_url=asset.cloudfront_url,
            expires_in_seconds=token_ttl,
        )
        return {
            "asset_uuid": asset.uuid,
            "order_uuid": order.uuid,
            "download_url": asset.cloudfront_url,
            "delivery_token": delivery_token,
            "download_count": access.download_count,
            "expires_in_days": self._get_access_expiry_days(),
            "max_downloads": self._get_access_limit(),
            "delivery_token_ttl_seconds": token_ttl,
        }

    def _get_delivery_token_ttl(self):
        try:
            ttl = int(ASSET_DELIVERY_TOKEN_TTL_SECONDS)
        except (TypeError, ValueError):
            return 900
        return ttl if ttl > 0 else 900
