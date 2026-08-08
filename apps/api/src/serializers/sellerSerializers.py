import datetime
import uuid

from flask import g
from werkzeug.exceptions import HTTPException

from configuration.db_routing import db, session_rollback
from models.seller import SellerApplication, SellerProfile
from utils.constants import USER_TYPE


class SellerApplicationInputError(HTTPException):
    code = 400
    description = "Seller application data is invalid"

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


class SellerApplicationSerializer(object):
    STATUSES = {"draft", "submitted", "under_review", "needs_information", "approved", "rejected", "withdrawn"}
    EDITABLE_FIELDS = {
        "store_name",
        "store_description",
        "category",
        "product_types",
        "website_url",
        "portfolio_url",
        "legal_name",
        "country",
        "phone_number",
        "terms_accepted",
    }

    @staticmethod
    def _user():
        user = getattr(g, "user", None)
        if not user:
            raise SellerApplicationInputError("Authentication required")
        return user

    @classmethod
    def _serialize_user(cls, user):
        return {
            "uuid": user.uuid,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

    @classmethod
    def serialize_application(cls, application):
        return {
            "uuid": application.uuid,
            "status": application.status,
            "applicant": cls._serialize_user(application.applicant) if application.applicant else None,
            "store_name": application.store_name,
            "store_description": application.store_description,
            "category": application.category,
            "product_types": application.product_types,
            "website_url": application.website_url,
            "portfolio_url": application.portfolio_url,
            "legal_name": application.legal_name,
            "country": application.country,
            "phone_number": application.phone_number,
            "terms_accepted": application.terms_accepted,
            "submitted_on": application.submitted_on.isoformat() if application.submitted_on else None,
            "reviewed_on": application.reviewed_on.isoformat() if application.reviewed_on else None,
            "reviewer_uuid": application.reviewer.uuid if application.reviewer else None,
            "review_note": application.review_note,
            "created_on": application.created_on.isoformat() if application.created_on else None,
            "modified_on": application.modified_on.isoformat() if application.modified_on else None,
        }

    @staticmethod
    def serialize_profile(profile):
        return {
            "uuid": profile.uuid,
            "user_uuid": profile.user.uuid if profile.user else None,
            "store_name": profile.store_name,
            "store_description": profile.store_description,
            "category": profile.category,
            "website_url": profile.website_url,
            "portfolio_url": profile.portfolio_url,
            "payout_ready": profile.payout_ready,
            "payout_hold": profile.payout_hold,
            "is_suspended": profile.is_suspended,
            "created_on": profile.created_on.isoformat() if profile.created_on else None,
            "modified_on": profile.modified_on.isoformat() if profile.modified_on else None,
        }

    @classmethod
    def _validate_fields(cls, payload, require_submit=False):
        values = {}
        for field in cls.EDITABLE_FIELDS:
            if field in payload:
                value = payload[field]
                if isinstance(value, str):
                    value = value.strip()
                values[field] = value

        if require_submit:
            required = {
                "store_name": "Store name is required",
                "store_description": "Store description is required",
                "category": "Category is required",
                "product_types": "Product types are required",
                "legal_name": "Legal name is required",
                "country": "Country is required",
                "phone_number": "Phone number is required",
            }
            for field, message in required.items():
                if not str(values.get(field) or "").strip():
                    raise SellerApplicationInputError(message)
            if values.get("terms_accepted") is not True:
                raise SellerApplicationInputError("Seller terms must be accepted")

        if "store_name" in values and len(str(values["store_name"] or "")) > 120:
            raise SellerApplicationInputError("Store name is too long")
        return values

    @classmethod
    def _get_owned(cls, application_uuid=None):
        user = cls._user()
        query = SellerApplication.query
        if application_uuid:
            application = query.filter_by(uuid=application_uuid).first()
            if not application:
                raise SellerApplicationInputError("Seller application not found")
            if application.user_id != user.id and user.user_type != USER_TYPE.ADMIN.value:
                raise SellerApplicationInputError("You do not have access to this application")
            return application
        return query.filter_by(user_id=user.id).first()

    @classmethod
    def get_my_application(cls):
        return cls._get_owned()

    @classmethod
    def list_applications(cls, status=None):
        cls._require_admin()
        query = SellerApplication.query.order_by(SellerApplication.created_on.desc())
        if status:
            normalized = str(status).lower()
            if normalized not in cls.STATUSES:
                raise SellerApplicationInputError("Invalid application status")
            query = query.filter_by(status=normalized)
        return query.all()

    @classmethod
    def _require_admin(cls):
        user = cls._user()
        if user.user_type != USER_TYPE.ADMIN.value:
            raise SellerApplicationInputError("Admin access required")
        return user

    @classmethod
    @session_rollback(db)
    def save_draft(cls, payload):
        user = cls._user()
        if user.user_type != USER_TYPE.CUSTOMER.value:
            raise SellerApplicationInputError("Only customers can apply to become sellers")
        application = cls._get_owned()
        if application and application.status not in {"draft", "needs_information", "rejected"}:
            raise SellerApplicationInputError("This application cannot be edited in its current state")
        values = cls._validate_fields(payload)
        if not application:
            application = SellerApplication(
                uuid=f"seller-application::{uuid.uuid4()}",
                user_id=user.id,
                status="draft",
            )
            db.session.add(application)
        for field, value in values.items():
            setattr(application, field, value)
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def submit(cls, payload):
        user = cls._user()
        if user.user_type != USER_TYPE.CUSTOMER.value:
            raise SellerApplicationInputError("Only customers can apply to become sellers")
        application = cls._get_owned()
        if not application:
            application = SellerApplication(
                uuid=f"seller-application::{uuid.uuid4()}",
                user_id=user.id,
                status="draft",
            )
            db.session.add(application)
        if application.status not in {"draft", "needs_information", "rejected"}:
            raise SellerApplicationInputError("This application cannot be submitted in its current state")
        values = cls._validate_fields(payload, require_submit=False)
        for field, value in values.items():
            setattr(application, field, value)
        cls._validate_fields({field: getattr(application, field) for field in cls.EDITABLE_FIELDS}, require_submit=True)
        application.status = "submitted"
        application.submitted_on = datetime.datetime.utcnow()
        application.review_note = None
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def withdraw(cls, application_uuid):
        application = cls._get_owned(application_uuid)
        if application.status not in {"submitted", "under_review", "needs_information"}:
            raise SellerApplicationInputError("This application cannot be withdrawn in its current state")
        application.status = "withdrawn"
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def request_information(cls, application_uuid, note):
        admin = cls._require_admin()
        application = cls._get_owned(application_uuid)
        if application.status not in {"submitted", "under_review"}:
            raise SellerApplicationInputError("This application is not awaiting review")
        note = str(note or "").strip()
        if not note:
            raise SellerApplicationInputError("A request for information is required")
        application.status = "needs_information"
        application.reviewer_id = admin.id
        application.review_note = note
        application.reviewed_on = datetime.datetime.utcnow()
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def reject(cls, application_uuid, note):
        admin = cls._require_admin()
        application = cls._get_owned(application_uuid)
        if application.status not in {"submitted", "under_review", "needs_information"}:
            raise SellerApplicationInputError("This application is not awaiting review")
        note = str(note or "").strip()
        if not note:
            raise SellerApplicationInputError("A rejection reason is required")
        application.status = "rejected"
        application.reviewer_id = admin.id
        application.review_note = note
        application.reviewed_on = datetime.datetime.utcnow()
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def approve(cls, application_uuid, note=None):
        admin = cls._require_admin()
        application = cls._get_owned(application_uuid)
        if application.status not in {"submitted", "under_review", "needs_information"}:
            raise SellerApplicationInputError("This application is not awaiting approval")
        user = application.applicant
        if not user or user.user_type != USER_TYPE.CUSTOMER.value:
            raise SellerApplicationInputError("Only customer accounts can be promoted")
        application.status = "approved"
        application.reviewer_id = admin.id
        application.review_note = str(note or "").strip() or None
        application.reviewed_on = datetime.datetime.utcnow()
        user.user_type = USER_TYPE.SELLER.value
        profile = SellerProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = SellerProfile(
                uuid=f"seller-profile::{uuid.uuid4()}",
                user_id=user.id,
                store_name=application.store_name,
                store_description=application.store_description,
                category=application.category,
                website_url=application.website_url,
                portfolio_url=application.portfolio_url,
            )
            db.session.add(profile)
        db.session.commit()
        return application, profile

    @classmethod
    @session_rollback(db)
    def set_suspension(cls, user_uuid, suspended, note=None):
        admin = cls._require_admin()
        from models.user import User
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user or user.user_type != USER_TYPE.SELLER.value:
            raise SellerApplicationInputError("Active seller not found")
        profile = SellerProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            raise SellerApplicationInputError("Seller profile not found")
        profile.is_suspended = bool(suspended)
        profile.payout_hold = bool(suspended)
        application = SellerApplication.query.filter_by(user_id=user.id).first()
        if application:
            application.review_note = str(note or "").strip() or application.review_note
            application.reviewer_id = admin.id
            application.reviewed_on = datetime.datetime.utcnow()
        db.session.commit()
        return profile
