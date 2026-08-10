import logging
import uuid

from flask import abort
from sqlalchemy import func
from werkzeug.exceptions import HTTPException

from configuration.db_routing import db, session_rollback
from models.product import Product
from models.seller import SellerProfile
from models.user import User
from utils.constants import USER_TYPE


class ProductInputError(HTTPException):
    code = 400
    description = "Product data is invalid"

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


class ProductSerializer(object):
    def __init__(self, data=None):
        self.data = data or {}

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
        validated_data["image_uri"] = validated_data.get("image_uri")
        validated_data["image_alt"] = validated_data.get("image_alt")
        validated_data["image_provider"] = validated_data.get("image_provider")
        validated_data["image_key"] = validated_data.get("image_key")
        validated_data["image_mime_type"] = validated_data.get("image_mime_type")
        validated_data["image_size_bytes"] = self._normalize_optional_int(validated_data.get("image_size_bytes"))
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
