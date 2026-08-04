import datetime
import uuid
from decimal import Decimal, InvalidOperation

from werkzeug.exceptions import HTTPException

from configuration.db_routing import db, session_rollback
from models.ledger import SellerBalance, SellerPayout
from models.user import User
from utils.constants import USER_TYPE


class PayoutInputError(HTTPException):
    code = 400
    description = "Payout data is invalid"

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


class PayoutSerializer(object):
    PAYOUT_STATES = {"pending", "processing", "paid", "failed", "cancelled"}

    def __init__(self, data=None):
        self.data = data or {}

    def _serialize_payout(self, payout):
        return {
            "uuid": payout.uuid,
            "seller_uuid": payout.seller.uuid if payout.seller else None,
            "seller_username": payout.seller.username if payout.seller else None,
            "amount": str(payout.amount),
            "status": payout.status,
            "payout_method": payout.payout_method,
            "batch_id": payout.batch_id,
            "failure_reason": payout.failure_reason,
            "processed_at": payout.processed_at.isoformat() if payout.processed_at else None,
            "created_on": payout.created_on.isoformat() if payout.created_on else None,
            "modified_on": payout.modified_on.isoformat() if payout.modified_on else None,
        }

    def list_payouts(self):
        return SellerPayout.query.order_by(SellerPayout.created_on.desc()).all()

    def validate_seller(self, seller_uuid):
        seller = User.query.filter_by(uuid=seller_uuid).first()
        if not seller:
            raise PayoutInputError("Seller not found")
        if seller.user_type not in {USER_TYPE.SELLER.value, USER_TYPE.ADMIN.value}:
            raise PayoutInputError("Only seller or admin users can receive payouts")
        return seller

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

    def validate_create_data(self, validated_data):
        seller = self.validate_seller(validated_data.get("seller_uuid"))

        try:
            amount = Decimal(str(validated_data.get("amount")))
        except (InvalidOperation, TypeError, ValueError):
            raise PayoutInputError("amount must be numeric")

        if amount <= 0:
            raise PayoutInputError("amount must be greater than zero")

        seller_balance = self.get_or_create_seller_balance(seller)
        available_for_payout = Decimal(str(seller_balance.available_for_payout or 0))
        if amount > available_for_payout:
            raise PayoutInputError("amount exceeds available payout balance")

        status = validated_data.get("status") or "pending"
        if status not in self.PAYOUT_STATES:
            raise PayoutInputError("Invalid payout status")

        validated_data["uuid"] = validated_data.get("uuid") or f"payout::{uuid.uuid4()}"
        validated_data["seller_id"] = seller.id
        validated_data["amount"] = amount
        validated_data["status"] = status
        validated_data["payout_method"] = validated_data.get("payout_method") or "manual"
        validated_data["batch_id"] = validated_data.get("batch_id")
        validated_data["failure_reason"] = validated_data.get("failure_reason")
        return validated_data

    @session_rollback(db)
    def create(self, validated_data=None):
        validated_data = dict(validated_data or self.data)
        validated_data = self.validate_create_data(validated_data)

        payout = SellerPayout(
            uuid=validated_data["uuid"],
            seller_id=validated_data["seller_id"],
            amount=validated_data["amount"],
            status=validated_data["status"],
            payout_method=validated_data["payout_method"],
            batch_id=validated_data["batch_id"],
            failure_reason=validated_data["failure_reason"],
            processed_at=datetime.datetime.utcnow() if validated_data["status"] in {"paid", "processing"} else None,
        )
        db.session.add(payout)

        seller_balance = self.get_or_create_seller_balance(payout.seller)
        seller_balance.available_for_payout = Decimal(str(seller_balance.available_for_payout or 0)) - Decimal(
            str(payout.amount)
        )
        seller_balance.pending_payout = Decimal(str(seller_balance.pending_payout or 0))

        db.session.commit()
        return payout

    def serialize_payout(self, payout):
        return self._serialize_payout(payout)
