import datetime
import uuid
from decimal import Decimal, InvalidOperation

from sqlalchemy import func
from werkzeug.exceptions import HTTPException

from configuration.db_routing import db, session_rollback
from models.ledger import SellerBalance, SellerPayout
from models.user import User
from utils.constants import USER_TYPE
from models.seller import SellerProfile


class PayoutInputError(HTTPException):
    code = 400
    description = "Payout data is invalid"

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


class PayoutSerializer(object):
    PAYOUT_STATES = {"pending", "processing", "paid", "failed", "cancelled"}
    PAYOUT_TRANSITIONS = {
        "pending": {"processing", "cancelled"},
        "processing": {"paid", "failed", "cancelled"},
        "failed": {"processing", "cancelled"},
        "paid": set(),
        "cancelled": set(),
    }

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

    def validate_status_transition(self, current_status, next_status):
        if current_status not in self.PAYOUT_STATES:
            raise PayoutInputError("Invalid current payout status")
        if next_status not in self.PAYOUT_STATES:
            raise PayoutInputError("Invalid payout status")
        allowed_next_statuses = self.PAYOUT_TRANSITIONS.get(current_status, set())
        if next_status == current_status:
            return next_status
        if next_status not in allowed_next_statuses:
            raise PayoutInputError(f"Invalid payout transition from {current_status} to {next_status}")
        return next_status

    def transition_payout(self, payout, next_status, failure_reason=None):
        payout.status = self.validate_status_transition(payout.status, next_status)
        if next_status == "paid":
            payout.processed_at = datetime.datetime.utcnow()
            payout.failure_reason = None
        elif next_status == "failed":
            payout.failure_reason = failure_reason or payout.failure_reason
            payout.processed_at = datetime.datetime.utcnow()
        elif next_status == "processing":
            payout.failure_reason = None
        elif next_status == "cancelled":
            payout.failure_reason = failure_reason or payout.failure_reason
        return payout

    def list_payouts(self, seller_id=None):
        query = SellerPayout.query
        if seller_id is not None:
            query = query.filter_by(seller_id=seller_id)
        return query.order_by(SellerPayout.created_on.desc()).all()

    def list_retryable_payouts(self):
        return SellerPayout.query.filter_by(status="failed").order_by(SellerPayout.modified_on.desc()).all()

    def get_payout_by_uuid(self, payout_uuid):
        payout = SellerPayout.query.filter_by(uuid=payout_uuid).first()
        if not payout:
            raise PayoutInputError("Payout not found")
        return payout

    def get_payout_by_uuid_for_update(self, payout_uuid):
        payout = SellerPayout.query.filter_by(uuid=payout_uuid).with_for_update().first()
        if not payout:
            raise PayoutInputError("Payout not found")
        return payout

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
        profile = SellerProfile.query.filter_by(user_id=seller.id).first()
        if seller.user_type == USER_TYPE.SELLER.value and not profile:
            raise PayoutInputError("Seller profile is required before payouts")
        if profile and (profile.is_suspended or profile.payout_hold):
            raise PayoutInputError("Seller payouts are currently on hold")
        if profile and (profile.kyc_status != "verified" or profile.fund_account_status != "validated" or not profile.payout_ready):
            raise PayoutInputError("Seller KYC, fund account validation, and payout readiness are required")

        try:
            amount = Decimal(str(validated_data.get("amount")))
        except (InvalidOperation, TypeError, ValueError):
            raise PayoutInputError("amount must be numeric")

        if amount <= 0:
            raise PayoutInputError("amount must be greater than zero")

        seller_balance = SellerBalance.query.filter_by(seller_id=seller.id).with_for_update().first()
        if not seller_balance:
            raise PayoutInputError("Seller balance is not available for payout")
        available_for_payout = Decimal(str(seller_balance.available_for_payout or 0))
        if amount > available_for_payout:
            raise PayoutInputError("amount exceeds available payout balance")

        validated_data["uuid"] = validated_data.get("uuid") or f"payout::{uuid.uuid4()}"
        validated_data["seller_id"] = seller.id
        validated_data["amount"] = amount
        validated_data["status"] = "pending"
        validated_data["payout_method"] = "manual"
        validated_data["batch_id"] = None
        validated_data["failure_reason"] = None
        validated_data["seller_balance"] = seller_balance
        return validated_data

    @session_rollback(db)
    def create(self, validated_data=None):
        validated_data = dict(validated_data or self.data)
        validated_data = self.validate_create_data(validated_data)
        seller_balance = validated_data.pop("seller_balance")

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
        db.session.flush()

        seller_balance.available_for_payout = Decimal(str(seller_balance.available_for_payout or 0)) - Decimal(
            str(payout.amount)
        )
        seller_balance.pending_payout = Decimal(str(seller_balance.pending_payout or 0)) + Decimal(
            str(payout.amount)
        )

        db.session.commit()
        return payout

    @session_rollback(db)
    def cancel_payout(self, payout_uuid, actor):
        payout = self.get_payout_by_uuid_for_update(payout_uuid)
        is_admin = str(actor.user_type).lower() == USER_TYPE.ADMIN.value
        if not is_admin and payout.seller_id != actor.id:
            raise PayoutInputError("You do not own this payout")
        if payout.status not in {"pending", "failed"}:
            raise PayoutInputError("Only pending or failed payouts can be cancelled")

        balance = SellerBalance.query.filter_by(seller_id=payout.seller_id).with_for_update().first()
        if not balance:
            raise PayoutInputError("Seller balance not found")
        balance.available_for_payout = Decimal(str(balance.available_for_payout or 0)) + Decimal(
            str(payout.amount)
        )
        balance.pending_payout = max(
            Decimal("0"),
            Decimal(str(balance.pending_payout or 0)) - Decimal(str(payout.amount)),
        )
        self.transition_payout(payout, "cancelled", failure_reason="Cancelled by user")
        db.session.commit()
        return payout

    @session_rollback(db)
    def process_batch(self, batch_id, payout_updates):
        if not batch_id:
            raise PayoutInputError("batch_id is required")
        if not isinstance(payout_updates, list) or not payout_updates:
            raise PayoutInputError("payout_updates must be a non-empty list")

        processed_payouts = []
        for update in payout_updates:
            payout_uuid = update.get("payout_uuid")
            next_status = update.get("status")
            if not payout_uuid or not next_status:
                raise PayoutInputError("Each payout update requires payout_uuid and status")

            payout = self.get_payout_by_uuid_for_update(payout_uuid)
            if payout.batch_id and payout.batch_id != batch_id:
                raise PayoutInputError("Payout already belongs to a different batch")

            payout.batch_id = batch_id
            self.transition_payout(payout, "processing")
            if next_status == "failed":
                self.transition_payout(payout, "failed", failure_reason=update.get("failure_reason"))
            elif next_status == "paid":
                self.transition_payout(payout, "paid")
                balance = SellerBalance.query.filter_by(seller_id=payout.seller_id).with_for_update().first()
                if not balance:
                    raise PayoutInputError("Seller balance not found")
                balance.pending_payout = max(
                    Decimal("0"),
                    Decimal(str(balance.pending_payout or 0)) - Decimal(str(payout.amount)),
                )
            else:
                raise PayoutInputError("Batch processing only supports paid or failed final states")

            processed_payouts.append(payout)

        db.session.commit()
        return processed_payouts

    @session_rollback(db)
    def retry_payout(self, payout_uuid):
        payout = self.get_payout_by_uuid(payout_uuid)
        if payout.status != "failed":
            raise PayoutInputError("Only failed payouts can be retried")

        payout = self.transition_payout(payout, "processing")
        payout.failure_reason = None
        db.session.commit()
        return payout

    def reconciliation_summary(self):
        failed_payouts = SellerPayout.query.filter_by(status="failed").all()
        open_payouts = SellerPayout.query.filter(SellerPayout.status.in_(["pending", "processing"])).all()
        paid_payouts = SellerPayout.query.filter_by(status="paid").all()
        return {
            "failed_payouts": [self.serialize_payout(payout) for payout in failed_payouts],
            "open_payouts": [self.serialize_payout(payout) for payout in open_payouts],
            "paid_payouts": [self.serialize_payout(payout) for payout in paid_payouts],
            "counts": {
                "failed_payouts": len(failed_payouts),
                "open_payouts": len(open_payouts),
                "paid_payouts": len(paid_payouts),
            },
        }

    def serialize_payout(self, payout):
        return self._serialize_payout(payout)

    def seller_summary(self, seller_id):
        balance = SellerBalance.query.filter_by(seller_id=seller_id).first()
        profile = SellerProfile.query.filter_by(user_id=seller_id).first()
        payouts = self.list_payouts(seller_id=seller_id)
        return {
            "available_for_payout": str(balance.available_for_payout if balance else 0),
            "pending_payout": str(balance.pending_payout if balance else 0),
            "currency": balance.currency if balance else "INR",
            "payout_ready": bool(profile and profile.payout_ready and not profile.payout_hold),
            "payout_hold": bool(profile and profile.payout_hold),
            "payouts": [self.serialize_payout(payout) for payout in payouts],
        }

    def admin_summary(self):
        available = SellerBalance.query.with_entities(
            func.coalesce(func.sum(SellerBalance.available_for_payout), 0)
        ).scalar() or 0
        pending = SellerBalance.query.with_entities(
            func.coalesce(func.sum(SellerBalance.pending_payout), 0)
        ).scalar() or 0
        return {
            "available_for_payout": str(available),
            "pending_payout": str(pending),
            "currency": "INR",
            "payout_ready": False,
            "payout_hold": False,
            "payouts": [self.serialize_payout(payout) for payout in self.list_payouts()],
        }
