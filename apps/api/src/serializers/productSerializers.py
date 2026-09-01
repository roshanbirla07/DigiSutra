import logging
import uuid

from flask import abort, g
from sqlalchemy import func
from werkzeug.exceptions import HTTPException

from configuration.db_routing import db, session_rollback
from models.product import Product
from models.seller import SellerProfile
from models.user import User
from services.s3_asset_gateway import S3AssetGateway, S3AssetGatewayError
from utils.constants import USER_TYPE


class ProductInputError(HTTPException):
    code = 400
    description = "Product data is invalid"

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


class ProductSerializer(object):
    PREVIEW_CONTENT_TYPES = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    PREVIEW_MAX_BYTES = 5 * 1024 * 1024

    def __init__(self, data=None):
        self.data = data or {}
        self.gateway = S3AssetGateway()

    @staticmethod
    def _normalize_optional_int(value):
        if value in (None, ""):
            return None
        return int(value)

    @staticmethod
    def _normalize_optional_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off"}:
                return False
        return bool(value)

    def validate_owner(self, validated_data):
        owner_uuid = validated_data.get("owner_uuid")
        if not owner_uuid:
            raise ProductInputError("owner_uuid is required")

        owner = User.query.filter_by(uuid=owner_uuid).first()
        if not owner:
            raise ProductInputError("Owner not found")
        if owner.user_type not in {USER_TYPE.SELLER.value, USER_TYPE.ADMIN.value}:
            raise ProductInputError("Only seller or admin users can own products")
        if owner.is_active and str(owner.is_active).lower() in ("false", "0", "inactive"):
            raise ProductInputError("Inactive users cannot own products")
        if owner.user_type == USER_TYPE.SELLER.value:
            profile = SellerProfile.query.filter_by(user_id=owner.id).first()
            if not profile:
                raise ProductInputError("Seller profile is required before publishing products")
            if profile.is_suspended:
                raise ProductInputError("Seller account is suspended")
            if profile.kyc_status != "verified" or profile.fund_account_status != "validated":
                raise ProductInputError("Seller KYC and fund account validation are required before publishing products")
        return owner

    def prepare_create_data(self, validated_data):
        title = str(validated_data.get("title", "")).strip()
        price = validated_data.get("price")

        if not title:
            raise ProductInputError("title is required")
        if price is None:
            raise ProductInputError("price is required")

        owner = self.validate_owner(validated_data)

        validated_data["uuid"] = f"product::{uuid.uuid4()}"
        validated_data["title"] = title
        validated_data["description"] = validated_data.get("description")
        validated_data["currency"] = validated_data.get("currency") or "INR"
        validated_data["category"] = validated_data.get("category")
        external_image_uri = validated_data.get("image_uri")
        validated_data["image_uri"] = external_image_uri
        validated_data["image_alt"] = validated_data.get("image_alt")
        validated_data["image_provider"] = "external" if external_image_uri else None
        # S3 preview keys are issued only by the authenticated preview-upload endpoint.
        validated_data["image_key"] = None
        validated_data["image_mime_type"] = None
        validated_data["image_size_bytes"] = None
        validated_data["image_width"] = self._normalize_optional_int(validated_data.get("image_width"))
        validated_data["image_height"] = self._normalize_optional_int(validated_data.get("image_height"))
        validated_data["image_sort_order"] = self._normalize_optional_int(validated_data.get("image_sort_order")) or 0
        validated_data["image_is_primary"] = self._normalize_optional_bool(validated_data.get("image_is_primary"), True)
        validated_data["is_active"] = self._normalize_optional_bool(validated_data.get("is_active"), True)
        validated_data["is_public"] = self._normalize_optional_bool(validated_data.get("is_public"), True)
        validated_data["owner_id"] = owner.id
        validated_data.pop("owner_uuid", None)
        return validated_data

    @session_rollback(db)
    def create(self, validated_data=None):
        validated_data = dict(validated_data or self.data)
        validated_data = self.prepare_create_data(validated_data)

        if Product.query.filter(func.lower(Product.title) == func.lower(validated_data["title"])).\
                filter(Product.owner_id == validated_data["owner_id"]).first():
            raise ProductInputError("A product with this title already exists for this owner")

        product = Product(**validated_data)
        db.session.add(product)

        try:
            db.session.commit()
        except Exception as e:
            logging.error(f"Exception in Product Creation Serializer :: {e}")
            abort(400)

        return product

    def list_public(self):
        return Product.query.filter_by(is_active=True, is_public=True).order_by(Product.created_on.desc()).all()

    def list_owned(self, owner_id):
        return Product.query.filter_by(owner_id=owner_id).order_by(Product.created_on.desc()).all()

    def get_by_uuid(self, product_uuid):
        product = Product.query.filter_by(uuid=product_uuid).first()
        if not product:
            raise ProductInputError("Product not found")
        return product

    def _get_owned_product(self, product_uuid):
        product = self.get_by_uuid(product_uuid)
        user = getattr(g, "user", None)
        if not user:
            raise ProductInputError("Authentication is required")
        if str(user.user_type).lower() != USER_TYPE.ADMIN.value and product.owner_id != user.id:
            raise ProductInputError("You do not own this product")
        return product

    @classmethod
    def _validate_preview(cls, payload):
        content_type = str(payload.get("content_type") or "").strip().lower()
        if content_type not in cls.PREVIEW_CONTENT_TYPES:
            raise ProductInputError("Preview image must be JPEG, PNG, or WebP")
        try:
            size_bytes = int(payload.get("size_bytes") or 0)
        except (TypeError, ValueError) as exc:
            raise ProductInputError("Preview image size is invalid") from exc
        if size_bytes <= 0 or size_bytes > cls.PREVIEW_MAX_BYTES:
            raise ProductInputError("Preview image must be between 1 byte and 5 MB")
        return content_type, size_bytes

    @session_rollback(db)
    def create_preview_upload_target(self, product_uuid, payload):
        product = self._get_owned_product(product_uuid)
        content_type, size_bytes = self._validate_preview(payload)
        extension = self.PREVIEW_CONTENT_TYPES[content_type]
        object_key = f"previews/{product.uuid}/{uuid.uuid4()}.{extension}"
        try:
            presigned = self.gateway.create_presigned_put_url(object_key, content_type)
        except S3AssetGatewayError as exc:
            raise ProductInputError(str(exc)) from exc

        product.image_uri = None
        product.image_provider = "s3"
        product.image_key = object_key
        product.image_mime_type = content_type
        product.image_size_bytes = size_bytes
        product.image_alt = str(payload.get("image_alt") or product.title).strip()[:255]
        db.session.commit()
        return product, presigned

    @session_rollback(db)
    def complete_preview_upload(self, product_uuid, payload=None):
        product = self._get_owned_product(product_uuid)
        if not product.image_key or product.image_provider != "s3":
            raise ProductInputError("Preview upload has not been started")
        payload = payload or {}
        try:
            metadata = self.gateway.head_object(product.image_key)
        except S3AssetGatewayError as exc:
            raise ProductInputError(str(exc)) from exc
        actual_size = int(metadata.get("ContentLength") or 0)
        declared_size = int(payload.get("size_bytes") or product.image_size_bytes or 0)
        if actual_size <= 0 or actual_size > self.PREVIEW_MAX_BYTES:
            raise ProductInputError("Uploaded preview image size is invalid")
        if declared_size and actual_size != declared_size:
            raise ProductInputError("Uploaded preview image size does not match the selected file")
        actual_type = str(metadata.get("ContentType") or product.image_mime_type or "").lower()
        if actual_type not in self.PREVIEW_CONTENT_TYPES:
            raise ProductInputError("Uploaded preview object is not a supported image")
        product.image_mime_type = actual_type
        product.image_size_bytes = actual_size
        db.session.commit()
        return product

    def preview_url(self, product):
        if isinstance(product.image_key, str) and product.image_key:
            try:
                return self.gateway.create_presigned_get_url(product.image_key)
            except S3AssetGatewayError:
                return product.image_uri
        return product.image_uri

    @session_rollback(db)
    def delete(self, product_uuid):
        product = self.get_by_uuid(product_uuid)
        db.session.delete(product)
        try:
            db.session.commit()
        except Exception as e:
            logging.error(f"Exception in Product Delete Serializer :: {e}")
            abort(400)
        return True
