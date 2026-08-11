import datetime
from decimal import Decimal

from werkzeug.exceptions import HTTPException
from flask import g

from configuration.db_routing import db, session_rollback
from models.ledger import MarketplaceOrder, ProductAccess, RefundRecord, SellerBalance
from services.razorpay_gateway import RazorpayGateway


class PaymentInputError(HTTPException):
    code = 400
    description = "Payment data is invalid"

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


class PaymentSerializer(object):
    def __init__(self, data=None):
        self.data = data or {}
        self.gateway = RazorpayGateway()

    def _serialize_order(self, order):
        return {
            "uuid": order.uuid,
            "provider": order.provider,
            "provider_order_id": order.provider_order_id,
            "provider_payment_id": order.provider_payment_id,
            "payment_status": order.payment_status,
            "delivery_status": order.delivery_status,
            "refund_status": order.refund_status,
            "created_on": order.created_on.isoformat() if order.created_on else None,
            "modified_on": order.modified_on.isoformat() if order.modified_on else None,
        }

    def get_order(self, order_uuid):
        order = MarketplaceOrder.query.filter_by(uuid=order_uuid).first()
        if not order:
            raise PaymentInputError("Marketplace order not found")
        return order

    @session_rollback(db)
    def create_provider_order(self, order_uuid):
        order = self.get_order(order_uuid)
        self._require_buyer(order)
        if order.provider == "razorpay" and order.provider_order_id:
            return order, None

        created = self.gateway.create_order(
            amount=int(Decimal(str(order.gross_amount)) * 100),
            currency=order.product.currency or "INR",
            receipt=order.uuid,
            notes={
                "marketplace_order_uuid": order.uuid,
                "seller_uuid": order.seller.uuid if order.seller else "",
                "buyer_uuid": order.buyer.uuid if order.buyer else "",
                "product_uuid": order.product.uuid if order.product else "",
            },
        )
        order.provider = "razorpay"
        order.provider_order_id = created["id"]
        db.session.commit()
        return order, created

    def _grant_access_if_needed(self, order):
        access = ProductAccess.query.filter_by(order_id=order.id).first()
        if access:
            access.access_status = "granted"
            return access
        access = ProductAccess(
            uuid=f"access::{order.uuid}",
            order_id=order.id,
            access_status="granted",
            download_count=0,
        )
        db.session.add(access)
        return access

    def _move_funds_to_available(self, order):
        seller_balance = SellerBalance.query.filter_by(seller_id=order.seller_id).first()
        if not seller_balance:
            return None

        net_amount = Decimal(str(order.net_seller_amount))
        current_pending = Decimal(str(seller_balance.pending_payout or 0))
        current_available = Decimal(str(seller_balance.available_for_payout or 0))

        seller_balance.pending_payout = max(current_pending - net_amount, Decimal("0"))
        seller_balance.available_for_payout = current_available + net_amount
        seller_balance.currency = seller_balance.currency or order.product.currency or "INR"
        return seller_balance

    def _sync_seller_balance_on_refund(self, order, refund_amount):
        seller_balance = SellerBalance.query.filter_by(seller_id=order.seller_id).first()
        if not seller_balance:
            return None

        refund_amount = Decimal(str(refund_amount))
        current_pending = Decimal(str(seller_balance.pending_payout or 0))
        current_available = Decimal(str(seller_balance.available_for_payout or 0))

        if refund_amount <= current_pending:
            seller_balance.pending_payout = current_pending - refund_amount
        else:
            seller_balance.pending_payout = Decimal("0")
            seller_balance.available_for_payout = max(
                current_available - (refund_amount - current_pending),
                Decimal("0"),
            )
        seller_balance.currency = seller_balance.currency or order.product.currency or "INR"
        return seller_balance

    def _revoke_access_for_order(self, order):
        for access_record in order.product_access_records.all():
            access_record.access_status = "revoked"
            access_record.revoked_at = datetime.datetime.utcnow()

    def _mark_order_paid(self, order, payment_id):
        if order.payment_status == "paid" and order.provider_payment_id == payment_id:
            return order, False

        order.provider = "razorpay"
        order.provider_payment_id = payment_id
        order.payment_status = "paid"
        order.delivery_status = "ready"
        self._grant_access_if_needed(order)
        self._move_funds_to_available(order)
        return order, True

    def _mark_order_refunded(self, order, refund):
        if order.payment_status == "refunded" and order.refund_status == "processed":
            return order, False

        refund.status = "processed"
        refund.resolved_on = datetime.datetime.utcnow()
        order.payment_status = "refunded"
        order.delivery_status = "revoked"
        order.refund_status = "processed"
        self._sync_seller_balance_on_refund(order, refund.amount)
        self._revoke_access_for_order(order)
        return order, True

    @session_rollback(db)
    def confirm_checkout_payment(self, payload):
        provider_order_id = payload.get("razorpay_order_id")
        payment_id = payload.get("razorpay_payment_id")
        signature = payload.get("razorpay_signature")
        if not provider_order_id or not payment_id or not signature:
            raise PaymentInputError("razorpay_order_id, razorpay_payment_id and razorpay_signature are required")

        order = MarketplaceOrder.query.filter_by(provider_order_id=provider_order_id).first()
        if not order:
            raise PaymentInputError("Marketplace order not found for provider order id")
        self._require_buyer(order)
        if not self.gateway.verify_checkout_signature(order.provider_order_id, payment_id, signature):
            raise PaymentInputError("Signature mismatch")
        order, changed = self._mark_order_paid(order, payment_id)
        if changed:
            db.session.commit()
        return order

    @session_rollback(db)
    def process_webhook_event(self, payload, raw_body):
        event = payload.get("event")
        if event in {"refund.processed", "refund.failed"}:
            signature = payload.get("x_razorpay_signature") or self.data.get("x_razorpay_signature")
            if signature and not self.gateway.verify_webhook_signature(raw_body, signature):
                raise PaymentInputError("Webhook signature mismatch")
            entity = payload.get("payload", {}).get("refund", {}).get("entity", {})
            payment_id = entity.get("payment_id")
            refund_id = entity.get("id")
            if not payment_id or not refund_id:
                raise PaymentInputError("Refund webhook missing provider identifiers")
            order = MarketplaceOrder.query.filter_by(provider_payment_id=payment_id).first()
            if not order:
                raise PaymentInputError("Marketplace order not found for refund webhook")
            refund = RefundRecord.query.filter_by(provider_refund_id=refund_id).first()
            if not refund:
                refund = RefundRecord.query.filter_by(order_id=order.id).first()
            if not refund:
                raise PaymentInputError("Refund record not found for webhook")
            refund.provider_refund_id = refund_id
            refund.provider_status = entity.get("status") or event.rsplit(".", 1)[-1]
            if event == "refund.processed" and refund.status != "processed":
                self._mark_order_refunded(order, refund)
            elif event == "refund.failed":
                refund.failure_reason = entity.get("error_description") or "Provider refund failed"
            db.session.commit()
            return order
        if event not in {"payment.captured", "order.paid"}:
            return None

        signature = payload.get("x_razorpay_signature") or self.data.get("x_razorpay_signature")
        if signature and not self.gateway.verify_webhook_signature(raw_body, signature):
            raise PaymentInputError("Webhook signature mismatch")

        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        provider_order_id = entity.get("order_id")
        payment_id = entity.get("id")
        if not provider_order_id or not payment_id:
            raise PaymentInputError("Webhook payload missing payment identifiers")

        order = MarketplaceOrder.query.filter_by(provider_order_id=provider_order_id).first()
        if not order:
            raise PaymentInputError("Marketplace order not found for webhook payment")
        order, changed = self._mark_order_paid(order, payment_id)
        if changed:
            db.session.commit()
        return order

    def serialize_order(self, order):
        return self._serialize_order(order)

    def checkout_key_id(self):
        key_id, _, _ = self.gateway._credentials()
        return key_id

    def _require_buyer(self, order):
        user = getattr(g, "user", None)
        if not user or order.buyer_id != user.id:
            raise PaymentInputError("Authenticated user does not own this order")
        return user
