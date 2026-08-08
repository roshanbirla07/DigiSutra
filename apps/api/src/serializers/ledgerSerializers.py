import datetime
import logging
import uuid
from decimal import Decimal, InvalidOperation

from flask import abort
from flask import g
from sqlalchemy import func
from werkzeug.exceptions import HTTPException

from configuration.db_routing import db, session_rollback
from models.ledger import MarketplaceOrder, ProductAccess, RefundRecord, SellerBalance
from models.product import Product
from models.user import User
from services.razorpay_gateway import RazorpayGateway, RazorpayGatewayError
from utils.constants import USER_TYPE


class LedgerInputError(HTTPException):
    code = 400
    description = "Ledger data is invalid"

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


class LedgerSerializer(object):
    ORDER_PAYMENT_STATES = {"pending", "paid", "refunded", "failed"}
    ORDER_DELIVERY_STATES = {"pending", "ready", "revoked"}
    REFUND_STATES = {"none", "requested", "approved", "processed", "rejected"}

    def __init__(self, data=None):
        self.data = data or {}
        self.gateway = RazorpayGateway()

    def _validate_order_state(self, payment_status, delivery_status, refund_status):
        if payment_status not in self.ORDER_PAYMENT_STATES:
            raise LedgerInputError("Invalid payment_status")
        if delivery_status not in self.ORDER_DELIVERY_STATES:
            raise LedgerInputError("Invalid delivery_status")
        if refund_status not in self.REFUND_STATES:
            raise LedgerInputError("Invalid refund_status")
        if payment_status == "paid" and delivery_status == "pending":
            raise LedgerInputError("Paid orders must have a ready delivery status")
        if payment_status == "refunded" and delivery_status != "revoked":
            raise LedgerInputError("Refunded orders must have revoked delivery")
        if refund_status == "processed" and payment_status != "refunded":
            raise LedgerInputError("Processed refunds require refunded orders")

    def _grant_access_for_order(self, order):
        access_record = ProductAccess.query.filter_by(order_id=order.id).first()
        if access_record:
            access_record.access_status = "granted"
            access_record.revoked_at = None
            return access_record

        access_record = ProductAccess(
            uuid=f"access::{order.uuid}",
            order_id=order.id,
            access_status="granted",
            download_count=0,
        )
        db.session.add(access_record)
        return access_record

    def _revoke_access_for_order(self, order):
        for access_record in order.product_access_records.all():
            access_record.access_status = "revoked"
            access_record.revoked_at = datetime.datetime.utcnow()

    def _sync_seller_balance_on_payment(self, order):
        seller_balance = self.get_or_create_seller_balance(order.seller)
        current_pending = Decimal(str(seller_balance.pending_payout or 0))
        current_available = Decimal(str(seller_balance.available_for_payout or 0))
        net_amount = Decimal(str(order.net_seller_amount))

        seller_balance.pending_payout = max(current_pending - net_amount, Decimal("0"))
        seller_balance.available_for_payout = current_available + net_amount
        seller_balance.currency = seller_balance.currency or order.product.currency or "INR"
        return seller_balance

    def _sync_seller_balance_on_refund(self, order, refund_amount):
        seller_balance = self.get_or_create_seller_balance(order.seller)
        current_pending = Decimal(str(seller_balance.pending_payout or 0))
        current_available = Decimal(str(seller_balance.available_for_payout or 0))

        if refund_amount <= current_pending:
            seller_balance.pending_payout = current_pending - refund_amount
        else:
            seller_balance.pending_payout = Decimal("0")
            remaining_refund = refund_amount - current_pending
            seller_balance.available_for_payout = max(current_available - remaining_refund, Decimal("0"))

        seller_balance.currency = seller_balance.currency or order.product.currency or "INR"
        return seller_balance

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

    def _serialize_refund(self, refund):
        return {
            "uuid": refund.uuid,
            "order_uuid": refund.order.uuid if refund.order else None,
            "amount": str(refund.amount),
            "status": refund.status,
            "reason": refund.reason,
            "created_on": refund.created_on.isoformat() if refund.created_on else None,
            "modified_on": refund.modified_on.isoformat() if refund.modified_on else None,
            "resolved_on": refund.resolved_on.isoformat() if refund.resolved_on else None,
            "provider_refund_id": refund.provider_refund_id,
            "provider_status": refund.provider_status,
            "failure_reason": refund.failure_reason,
        }

    def _serialize_access_record(self, access_record):
        return {
            "uuid": access_record.uuid,
            "order_uuid": access_record.order.uuid if access_record.order else None,
            "asset_uuid": access_record.asset.uuid if getattr(access_record, "asset", None) else None,
            "access_status": access_record.access_status,
            "download_count": access_record.download_count,
            "revoked_at": access_record.revoked_at.isoformat() if access_record.revoked_at else None,
            "created_on": access_record.created_on.isoformat() if access_record.created_on else None,
            "modified_on": access_record.modified_on.isoformat() if access_record.modified_on else None,
        }

    def list_orders(self):
        return MarketplaceOrder.query.order_by(MarketplaceOrder.created_on.desc()).all()

    def list_orders_for_buyer(self, buyer_id):
        return MarketplaceOrder.query.filter_by(buyer_id=buyer_id).order_by(MarketplaceOrder.created_on.desc()).all()

    def list_orders_for_seller(self, seller_id):
        return MarketplaceOrder.query.filter_by(seller_id=seller_id).order_by(MarketplaceOrder.created_on.desc()).all()

    def validate_refund_request(self, order, validated_data):
        if order.refund_status in {"requested", "approved", "processed"}:
            raise LedgerInputError("Refund already exists for this order")

        try:
            refund_amount = Decimal(str(validated_data.get("amount") or order.net_seller_amount))
        except (InvalidOperation, TypeError, ValueError):
            raise LedgerInputError("amount must be numeric")

        if refund_amount <= 0:
            raise LedgerInputError("amount must be greater than zero")
        if refund_amount > Decimal(str(order.gross_amount)):
            raise LedgerInputError("amount cannot exceed order gross amount")

        return refund_amount

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

    def get_by_uuid(self, order_uuid):
        order = MarketplaceOrder.query.filter_by(uuid=order_uuid).first()
        if not order:
            raise ValueError("Marketplace order not found")
        return order

    def get_refund_by_uuid(self, refund_uuid):
        refund = RefundRecord.query.filter_by(uuid=refund_uuid).first()
        if not refund:
            raise ValueError("Refund record not found")
        return refund

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

    def _prepare_order_state(self, validated_data):
        payment_status = validated_data.get("payment_status") or "pending"
        delivery_status = validated_data.get("delivery_status") or "pending"
        refund_status = validated_data.get("refund_status") or "none"
        if payment_status == "refunded" and refund_status == "none":
            refund_status = "processed"
        self._validate_order_state(payment_status, delivery_status, refund_status)
        validated_data["payment_status"] = payment_status
        validated_data["delivery_status"] = delivery_status
        validated_data["refund_status"] = refund_status
        return validated_data

    def prepare_create_data(self, validated_data):
        auth_user = getattr(g, "user", None)
        buyer_uuid = validated_data.get("buyer_uuid") or (auth_user.uuid if auth_user else None)
        buyer = self.validate_user(buyer_uuid, "Buyer")
        if auth_user and buyer.uuid != auth_user.uuid:
            raise LedgerInputError("Authenticated buyer must match buyer_uuid")
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
        validated_data = self._prepare_order_state(validated_data)
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

    @session_rollback(db)
    def create_refund(self, order_uuid, validated_data=None):
        validated_data = dict(validated_data or self.data)
        order = self.get_by_uuid(order_uuid)
        refund_status = validated_data.get("status") or "processed"
        if refund_status not in self.REFUND_STATES:
            raise LedgerInputError("Invalid refund status")
        if refund_status == "none":
            raise LedgerInputError("Refund status cannot be none")

        refund_amount = self.validate_refund_request(order, validated_data)

        existing_refund = RefundRecord.query.filter_by(order_id=order.id).first()
        if existing_refund:
            raise LedgerInputError("Refund already exists for this order")

        refund = RefundRecord(
            uuid=validated_data.get("uuid") or f"refund::{uuid.uuid4()}",
            order_id=order.id,
            amount=refund_amount,
            status=refund_status,
            reason=validated_data.get("reason"),
            resolved_on=datetime.datetime.utcnow(),
        )
        if refund_status == "processed" and order.provider == "razorpay" and order.provider_payment_id:
            try:
                provider_refund = self.gateway.create_refund(
                    payment_id=order.provider_payment_id,
                    amount=int(refund_amount * 100),
                    currency=order.product.currency or "INR",
                    notes={"marketplace_order_uuid": order.uuid, "refund_uuid": refund.uuid},
                )
            except RazorpayGatewayError as exc:
                refund.status = "approved"
                refund.failure_reason = str(exc)
                refund.resolved_on = None
                db.session.add(refund)
                db.session.commit()
                return refund
            refund.provider_refund_id = provider_refund.get("id")
            refund.provider_status = provider_refund.get("status") or "created"
        db.session.add(refund)

        if refund_status == "processed":
            order.payment_status = "refunded"
            order.delivery_status = "revoked"
            self._sync_seller_balance_on_refund(order, refund_amount)
            order.refund_status = "processed"
            self._revoke_access_for_order(order)
        elif refund_status == "approved":
            order.refund_status = "approved"
        else:
            order.refund_status = "requested"

        self._validate_order_state(order.payment_status, order.delivery_status, order.refund_status)

        db.session.commit()
        return refund

    def serialize_order(self, order):
        return self._serialize_order(order)

    def serialize_refund(self, refund):
        return self._serialize_refund(refund)

    def list_buyer_purchases(self, buyer_id):
        orders = self.list_orders_for_buyer(buyer_id)
        history = []
        for order in orders:
            access_records = [
                self._serialize_access_record(access_record)
                for access_record in order.product_access_records.all()
            ]
            refunds = [self._serialize_refund(refund) for refund in order.refund_records.all()]
            history.append({
                "order": self._serialize_order(order),
                "access_records": access_records,
                "refunds": refunds,
                "assets": [{
                    "uuid": asset.uuid,
                    "product_uuid": order.product.uuid if order.product else None,
                    "original_filename": asset.original_filename,
                    "content_type": asset.content_type,
                    "asset_status": asset.asset_status,
                } for asset in order.product.assets.all()] if order.product else [],
            })
        return history
