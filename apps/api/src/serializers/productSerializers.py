import logging
import uuid

from flask import abort
from sqlalchemy import func
from werkzeug.exceptions import HTTPException

from configuration.db_routing import db, session_rollback
from models.product import Product
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
        validated_data["is_active"] = bool(validated_data.get("is_active", True))
        validated_data["is_public"] = bool(validated_data.get("is_public", True))
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

    def get_by_uuid(self, product_uuid):
        product = Product.query.filter_by(uuid=product_uuid).first()
        if not product:
            raise ProductInputError("Product not found")
        return product
