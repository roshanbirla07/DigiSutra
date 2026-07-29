import logging
import uuid
from decimal import Decimal, InvalidOperation

from flask import abort
from sqlalchemy import func
from werkzeug.exceptions import HTTPException

from configuration.db_routing import db, session_rollback
from models.ledger import MarketplaceOrder, SellerBalance
from models.product import Product
from models.user import User
from utils.constants import USER_TYPE


class LedgerInputError(HTTPException):
    code = 400
    description = "Ledger data is invalid"

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


class LedgerSerializer(object):
    def __init__(self, data=None):
        self.data = data or {}

    def _serialize_order(self, order):
        return {
            "uuid": order.uuid,
            "buyer_uuid": order.buyer.uuid if order.buyer else None,
            "buyer_username": order.buyer.username if order.buyer else None,
            "seller_uuid": order.seller.uuid if order.seller else None,
            "seller_username": order.seller.username if order.seller else None,
            "product_uuid": order.product.uuid if order.product else None,
            "product_title": order.product.title if order.product else None,
            "gross_amount": str(order.gross_amount),
            "platform_fee": str(order.platform_fee),
            "tax_amount": str(order.tax_amount),
            "net_seller_amount": str(order.net_seller_amount),
            "payment_status": order.payment_status,
            "delivery_status": order.delivery_status,
            "refund_status": order.refund_status,
            "provider": order.provider,
            "provider_order_id": order.provider_order_id,
            "provider_payment_id": order.provider_payment_id,
            "created_on": order.created_on.isoformat() if order.created_on else None,
            "modified_on": order.modified_on.isoformat() if order.modified_on else None,
        }

    def list_orders(self):
        return MarketplaceOrder.query.order_by(MarketplaceOrder.created_on.desc()).all()

    def get_or_create_seller_balance(self, seller):
        seller_balance = SellerBalance.query.filter_by(seller_id=seller.id).first()
        if seller_balance:
            return seller_balance

        seller_balance = SellerBalance(
            seller_id=seller.id,
            available_for_payout=Decimal("0"),
            pending_payout=Decimal("0"),
            currency="INR",
        )
        db.session.add(seller_balance)
        return seller_balance

    def validate_user(self, user_uuid, field_name):
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            raise LedgerInputError(f"{field_name} not found")
        if user.is_active and str(user.is_active).lower() in ("false", "0", "inactive"):
            raise LedgerInputError(f"{field_name} is inactive")
        return user

    def validate_seller(self, seller):
        if seller.user_type not in {USER_TYPE.SELLER.value, USER_TYPE.ADMIN.value}:
            raise LedgerInputError("Only seller or admin users can own marketplace orders")
        return seller

    def validate_product(self, product_uuid, seller):
        product = Product.query.filter_by(uuid=product_uuid).first()
        if not product:
            raise LedgerInputError("Product not found")
        if product.owner_id != seller.id:
            raise LedgerInputError("Product does not belong to seller")
        if not product.is_active:
            raise LedgerInputError("Product is inactive")
        return product

    def prepare_create_data(self, validated_data):
        buyer = self.validate_user(validated_data.get("buyer_uuid"), "Buyer")
        seller = self.validate_seller(self.validate_user(validated_data.get("seller_uuid"), "Seller"))
        product = self.validate_product(validated_data.get("product_uuid"), seller)

        try:
            gross_amount = Decimal(str(validated_data.get("gross_amount")))
            platform_fee = Decimal(str(validated_data.get("platform_fee") or 0))
            tax_amount = Decimal(str(validated_data.get("tax_amount") or 0))
        except (InvalidOperation, TypeError, ValueError):
            raise LedgerInputError("gross_amount, platform_fee, and tax_amount must be numeric")

        validated_data["uuid"] = validated_data.get("uuid") or f"order::{uuid.uuid4()}"
        validated_data["buyer_id"] = buyer.id
        validated_data["seller_id"] = seller.id
        validated_data["product_id"] = product.id
        validated_data["gross_amount"] = gross_amount
        validated_data["platform_fee"] = platform_fee
        validated_data["tax_amount"] = tax_amount
        validated_data["net_seller_amount"] = gross_amount - platform_fee - tax_amount
        validated_data["payment_status"] = validated_data.get("payment_status") or "pending"
        validated_data["delivery_status"] = validated_data.get("delivery_status") or "pending"
        validated_data["refund_status"] = validated_data.get("refund_status") or "none"
        validated_data.pop("buyer_uuid", None)
        validated_data.pop("seller_uuid", None)
        validated_data.pop("product_uuid", None)
        return validated_data

    @session_rollback(db)
    def create(self, validated_data=None):
        validated_data = dict(validated_data or self.data)
        validated_data = self.prepare_create_data(validated_data)

        if validated_data.get("provider_order_id") and MarketplaceOrder.query.filter(
            func.lower(MarketplaceOrder.provider_order_id) == func.lower(validated_data["provider_order_id"])
        ).first():
            raise LedgerInputError("A marketplace order with this provider order id already exists")
        if validated_data.get("provider_payment_id") and MarketplaceOrder.query.filter(
            func.lower(MarketplaceOrder.provider_payment_id) == func.lower(validated_data["provider_payment_id"])
        ).first():
            raise LedgerInputError("A marketplace order with this provider payment id already exists")

        order = MarketplaceOrder(**validated_data)
        db.session.add(order)

        seller_balance = self.get_or_create_seller_balance(order.seller)
        seller_balance.pending_payout = Decimal(str(seller_balance.pending_payout or 0)) + Decimal(
            str(order.net_seller_amount)
        )
        seller_balance.currency = seller_balance.currency or order.product.currency or "INR"

        try:
            db.session.commit()
        except Exception as e:
            logging.error(f"Exception in Ledger Order Creation Serializer :: {e}")
            abort(400)

        return order

    def get_by_uuid(self, order_uuid):
        order = MarketplaceOrder.query.filter_by(uuid=order_uuid).first()
        if not order:
            raise ValueError("Marketplace order not found")
        return order

    def serialize_order(self, order):
        return self._serialize_order(order)
