import datetime
import uuid

from flask import g
from werkzeug.exceptions import HTTPException

from configuration.db_routing import db, session_rollback
from models.product import Product
from models.support import ProductFlag, SupportTicket
from models.user import User
from utils.constants import USER_TYPE


class SupportInputError(HTTPException):
    code = 400
    description = "Support data is invalid"

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


class SupportSerializer(object):
    TICKET_STATUSES = {"open", "in_progress", "resolved", "closed"}
    FLAG_STATUSES = {"open", "reviewing", "resolved", "dismissed"}

    def _current_user(self):
        user = getattr(g, "user", None)
        if not user:
            raise SupportInputError("Authentication required")
        return user

    def _require_admin(self):
        user = self._current_user()
        if user.user_type != USER_TYPE.ADMIN.value:
            raise SupportInputError("Admin access required")
        return user

    def serialize_ticket(self, ticket):
        return {
            "uuid": ticket.uuid,
            "created_by_uuid": ticket.created_by.uuid if ticket.created_by else None,
            "subject": ticket.subject,
            "message": ticket.message,
            "status": ticket.status,
            "resolution": ticket.resolution,
            "resolved_by_uuid": ticket.resolved_by.uuid if ticket.resolved_by else None,
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            "created_on": ticket.created_on.isoformat() if ticket.created_on else None,
            "modified_on": ticket.modified_on.isoformat() if ticket.modified_on else None,
        }

    def serialize_flag(self, flag):
        return {
            "uuid": flag.uuid,
            "product_uuid": flag.product.uuid if flag.product else None,
            "reported_by_uuid": flag.reported_by.uuid if flag.reported_by else None,
            "reason": flag.reason,
            "status": flag.status,
            "created_on": flag.created_on.isoformat() if flag.created_on else None,
            "resolved_on": flag.resolved_on.isoformat() if flag.resolved_on else None,
        }

    def list_tickets(self):
        user = self._current_user()
        if user.user_type == USER_TYPE.ADMIN.value:
            return SupportTicket.query.order_by(SupportTicket.created_on.desc()).all()
        return SupportTicket.query.filter_by(created_by_id=user.id).order_by(SupportTicket.created_on.desc()).all()

    def list_flags(self):
        self._require_admin()
        return ProductFlag.query.order_by(ProductFlag.created_on.desc()).all()

    @session_rollback(db)
    def create_ticket(self, validated_data):
        user = self._current_user()
        subject = str(validated_data.get("subject") or "").strip()
        message = str(validated_data.get("message") or "").strip()
        if not subject:
            raise SupportInputError("subject is required")
        if not message:
            raise SupportInputError("message is required")
        ticket = SupportTicket(
            uuid=f"ticket::{uuid.uuid4()}",
            created_by_id=user.id,
            subject=subject,
            message=message,
            status="open",
        )
        db.session.add(ticket)
        db.session.commit()
        return ticket

    @session_rollback(db)
    def resolve_ticket(self, ticket_uuid, validated_data):
        admin = self._require_admin()
        ticket = SupportTicket.query.filter_by(uuid=ticket_uuid).first()
        if not ticket:
            raise SupportInputError("Support ticket not found")
        status = str(validated_data.get("status") or "resolved").lower()
        if status not in self.TICKET_STATUSES:
            raise SupportInputError("Invalid ticket status")
        resolution = str(validated_data.get("resolution") or "").strip()
        if not resolution:
            raise SupportInputError("resolution is required")
        ticket.status = status
        ticket.resolution = resolution
        ticket.resolved_by_id = admin.id
        ticket.resolved_at = datetime.datetime.utcnow()
        db.session.commit()
        return ticket

    @session_rollback(db)
    def create_product_flag(self, product_uuid, validated_data):
        user = self._current_user()
        product = Product.query.filter_by(uuid=product_uuid).first()
        if not product:
            raise SupportInputError("Product not found")
        reason = str(validated_data.get("reason") or "").strip()
        if not reason:
            raise SupportInputError("reason is required")
        flag = ProductFlag(
            uuid=f"flag::{uuid.uuid4()}",
            product_id=product.id,
            reported_by_id=user.id,
            reason=reason,
            status="open",
        )
        db.session.add(flag)
        db.session.commit()
        return flag

    @session_rollback(db)
    def resolve_product_flag(self, flag_uuid, status):
        self._require_admin()
        flag = ProductFlag.query.filter_by(uuid=flag_uuid).first()
        if not flag:
            raise SupportInputError("Flag not found")
        status = str(status or "").lower()
        if status not in self.FLAG_STATUSES:
            raise SupportInputError("Invalid flag status")
        flag.status = status
        flag.resolved_on = datetime.datetime.utcnow() if status in {"resolved", "dismissed"} else None
        db.session.commit()
        return flag

    @session_rollback(db)
    def set_user_active_state(self, user_uuid, is_active):
        self._require_admin()
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            raise SupportInputError("User not found")
        user.is_active = "true" if is_active else "false"
        db.session.commit()
        return user
