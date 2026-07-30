import logging
import uuid

from flask import abort
from sqlalchemy import func
from werkzeug.exceptions import HTTPException

from configuration.db_routing import db, session_rollback
from models.product import Product, ProductAsset, ProductAssetDownload
from services.s3_asset_gateway import S3AssetGateway, S3AssetGatewayError


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

    @session_rollback(db)
    def create_upload_target(self, validated_data=None):
        validated_data = dict(validated_data or self.data)
        product = self.get_product(validated_data.get("product_uuid"))
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
        asset = ProductAsset.query.filter_by(uuid=asset_uuid).first()
        if not asset:
            raise AssetInputError("Asset not found")
        asset.download_events.count()
        download = ProductAssetDownload(
            uuid=f"download::{uuid.uuid4()}",
            asset_id=asset.id,
            order_uuid=payload.get("order_uuid"),
            downloaded_by=payload.get("downloaded_by"),
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
