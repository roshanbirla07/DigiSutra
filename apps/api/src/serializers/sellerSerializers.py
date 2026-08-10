import datetime
import re
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
    STATUSES = {
        "draft",
        "submitted",
        "under_review",
        "kyc_pending",
        "kyc_in_review",
        "kyc_verified",
        "kyc_failed",
        "needs_information",
        "approved",
        "rejected",
        "withdrawn",
        "suspended",
    }
    KYC_STATUSES = {"not_started", "pending", "in_review", "verified", "failed", "needs_information"}
    PROVIDER_STATUSES = {"not_started", "created", "under_review", "activated", "needs_clarification", "suspended"}
    FUND_ACCOUNT_STATUSES = {"not_started", "pending", "validated", "failed"}
    BUSINESS_TYPES = {"individual", "proprietorship", "partnership", "llp", "private_limited", "public_limited", "trust", "ngo", "society"}
    EDITABLE_FIELDS = {
        "store_name",
        "store_description",
        "category",
        "product_types",
        "website_url",
        "portfolio_url",
        "legal_name",
        "business_type",
        "business_address",
        "pan_number",
        "gstin",
        "country",
        "phone_number",
        "bank_account_holder_name",
        "bank_account_last4",
        "bank_ifsc",
        "kyc_document_type",
        "kyc_document_reference",
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
            "business_type": application.business_type,
            "business_address": application.business_address,
            "pan_number": application.pan_number,
            "gstin": application.gstin,
            "country": application.country,
            "phone_number": application.phone_number,
            "bank_account_holder_name": application.bank_account_holder_name,
            "bank_account_last4": application.bank_account_last4,
            "bank_ifsc": application.bank_ifsc,
            "kyc_document_type": application.kyc_document_type,
            "kyc_document_reference": application.kyc_document_reference,
            "kyc_status": application.kyc_status,
            "kyc_review_note": application.kyc_review_note,
            "kyc_reviewed_on": application.kyc_reviewed_on.isoformat() if application.kyc_reviewed_on else None,
            "provider": application.provider,
            "provider_account_id": application.provider_account_id,
            "provider_account_status": application.provider_account_status,
            "fund_account_status": application.fund_account_status,
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
            "legal_name": profile.legal_name,
            "business_type": profile.business_type,
            "country": profile.country,
            "kyc_status": profile.kyc_status,
            "provider": profile.provider,
            "provider_account_id": profile.provider_account_id,
            "provider_account_status": profile.provider_account_status,
            "fund_account_status": profile.fund_account_status,
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
                if field in {"pan_number", "gstin", "bank_ifsc"} and value:
                    value = str(value).upper()
                values[field] = value

        if require_submit:
            required = {
                "store_name": "Store name is required",
                "store_description": "Store description is required",
                "category": "Category is required",
                "product_types": "Product types are required",
                "legal_name": "Legal name is required",
                "business_type": "Business type is required",
                "business_address": "Business address is required",
                "pan_number": "PAN is required",
                "country": "Country is required",
                "phone_number": "Phone number is required",
                "bank_account_holder_name": "Bank account holder name is required",
                "bank_account_last4": "Bank account last 4 digits are required",
                "bank_ifsc": "Bank IFSC is required",
                "kyc_document_type": "KYC document type is required",
                "kyc_document_reference": "KYC document reference is required",
            }
            for field, message in required.items():
                if not str(values.get(field) or "").strip():
                    raise SellerApplicationInputError(message)
            business_type = str(values.get("business_type") or "").strip().lower()
            if business_type not in cls.BUSINESS_TYPES:
                raise SellerApplicationInputError("Invalid business type")
            pan_number = str(values.get("pan_number") or "")
            if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan_number):
                raise SellerApplicationInputError("PAN format is invalid")
            gstin = str(values.get("gstin") or "")
            if gstin and not re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$", gstin):
                raise SellerApplicationInputError("GSTIN format is invalid")
            bank_last4 = str(values.get("bank_account_last4") or "")
            if not re.match(r"^[0-9]{4}$", bank_last4):
                raise SellerApplicationInputError("Bank account last 4 digits are invalid")
            bank_ifsc = str(values.get("bank_ifsc") or "")
            if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", bank_ifsc):
                raise SellerApplicationInputError("Bank IFSC format is invalid")
            if values.get("terms_accepted") is not True:
                raise SellerApplicationInputError("Seller terms must be accepted")

        if "store_name" in values and len(str(values["store_name"] or "")) > 120:
            raise SellerApplicationInputError("Store name is too long")
        return values

    @staticmethod
    def _normalize_review_payload(payload):
        payload = payload or {}
        return {
            "note": str(payload.get("note") or "").strip() or None,
            "provider": str(payload.get("provider") or "manual").strip().lower() or "manual",
            "provider_account_id": str(payload.get("provider_account_id") or "").strip() or None,
            "provider_account_status": str(payload.get("provider_account_status") or "").strip().lower() or None,
            "fund_account_status": str(payload.get("fund_account_status") or "").strip().lower() or None,
        }

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
        if application and application.status not in {"draft", "needs_information", "kyc_failed", "rejected"}:
            raise SellerApplicationInputError("This application cannot be edited in its current state")
        values = cls._validate_fields(payload)
        if not application:
            application = SellerApplication(
                uuid=f"seller-application::{uuid.uuid4()}",
                user_id=user.id,
                status="draft",
                kyc_status="not_started",
                provider="manual",
                provider_account_status="not_started",
                fund_account_status="not_started",
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
                kyc_status="not_started",
                provider="manual",
                provider_account_status="not_started",
                fund_account_status="not_started",
            )
            db.session.add(application)
        if application.status not in {"draft", "needs_information", "kyc_failed", "rejected"}:
            raise SellerApplicationInputError("This application cannot be submitted in its current state")
        values = cls._validate_fields(payload, require_submit=False)
        for field, value in values.items():
            setattr(application, field, value)
        cls._validate_fields({field: getattr(application, field) for field in cls.EDITABLE_FIELDS}, require_submit=True)
        application.status = "kyc_pending"
        application.kyc_status = "pending"
        application.provider = application.provider or "manual"
        application.provider_account_status = application.provider_account_status or "not_started"
        application.fund_account_status = application.fund_account_status or "pending"
        application.submitted_on = datetime.datetime.utcnow()
        application.review_note = None
        application.kyc_review_note = None
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def withdraw(cls, application_uuid):
        application = cls._get_owned(application_uuid)
        if application.status not in {"submitted", "under_review", "kyc_pending", "kyc_in_review", "needs_information"}:
            raise SellerApplicationInputError("This application cannot be withdrawn in its current state")
        application.status = "withdrawn"
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def request_information(cls, application_uuid, note):
        admin = cls._require_admin()
        application = cls._get_owned(application_uuid)
        if application.status not in {"submitted", "under_review", "kyc_pending", "kyc_in_review", "kyc_failed"}:
            raise SellerApplicationInputError("This application is not awaiting review")
        note = str(note or "").strip()
        if not note:
            raise SellerApplicationInputError("A request for information is required")
        application.status = "needs_information"
        application.kyc_status = "needs_information"
        application.reviewer_id = admin.id
        application.review_note = note
        application.kyc_review_note = note
        application.reviewed_on = datetime.datetime.utcnow()
        application.kyc_reviewed_on = application.reviewed_on
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def reject(cls, application_uuid, note):
        admin = cls._require_admin()
        application = cls._get_owned(application_uuid)
        if application.status not in {"submitted", "under_review", "kyc_pending", "kyc_in_review", "kyc_failed", "needs_information"}:
            raise SellerApplicationInputError("This application is not awaiting review")
        note = str(note or "").strip()
        if not note:
            raise SellerApplicationInputError("A rejection reason is required")
        application.status = "rejected"
        application.kyc_status = "failed"
        application.reviewer_id = admin.id
        application.review_note = note
        application.kyc_review_note = note
        application.reviewed_on = datetime.datetime.utcnow()
        application.kyc_reviewed_on = application.reviewed_on
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def start_kyc_review(cls, application_uuid, payload=None):
        admin = cls._require_admin()
        application = cls._get_owned(application_uuid)
        if application.status not in {"kyc_pending", "submitted", "under_review"}:
            raise SellerApplicationInputError("This application is not ready for KYC review")
        review = cls._normalize_review_payload(payload)
        application.status = "kyc_in_review"
        application.kyc_status = "in_review"
        application.reviewer_id = admin.id
        application.review_note = review["note"] or application.review_note
        application.kyc_review_note = review["note"] or application.kyc_review_note
        application.provider = review["provider"]
        application.provider_account_id = review["provider_account_id"] or application.provider_account_id
        application.provider_account_status = review["provider_account_status"] or "under_review"
        application.fund_account_status = review["fund_account_status"] or application.fund_account_status or "pending"
        application.reviewed_on = datetime.datetime.utcnow()
        application.kyc_reviewed_on = application.reviewed_on
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def verify_kyc(cls, application_uuid, payload=None):
        admin = cls._require_admin()
        application = cls._get_owned(application_uuid)
        if application.status not in {"kyc_pending", "kyc_in_review", "kyc_failed"}:
            raise SellerApplicationInputError("This application is not ready for KYC verification")
        review = cls._normalize_review_payload(payload)
        provider_status = review["provider_account_status"] or application.provider_account_status or "activated"
        fund_status = review["fund_account_status"] or application.fund_account_status or "validated"
        if provider_status not in cls.PROVIDER_STATUSES:
            raise SellerApplicationInputError("Invalid provider account status")
        if fund_status not in cls.FUND_ACCOUNT_STATUSES:
            raise SellerApplicationInputError("Invalid fund account status")
        if provider_status not in {"activated", "created"}:
            raise SellerApplicationInputError("Provider account must be created or activated before KYC verification")
        if fund_status != "validated":
            raise SellerApplicationInputError("Fund account must be validated before KYC verification")
        application.status = "kyc_verified"
        application.kyc_status = "verified"
        application.reviewer_id = admin.id
        application.review_note = review["note"] or application.review_note
        application.kyc_review_note = review["note"] or application.kyc_review_note
        application.provider = review["provider"]
        application.provider_account_id = review["provider_account_id"] or application.provider_account_id
        application.provider_account_status = provider_status
        application.fund_account_status = fund_status
        application.reviewed_on = datetime.datetime.utcnow()
        application.kyc_reviewed_on = application.reviewed_on
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def fail_kyc(cls, application_uuid, payload=None):
        admin = cls._require_admin()
        application = cls._get_owned(application_uuid)
        if application.status not in {"kyc_pending", "kyc_in_review", "kyc_failed"}:
            raise SellerApplicationInputError("This application is not in KYC review")
        review = cls._normalize_review_payload(payload)
        if not review["note"]:
            raise SellerApplicationInputError("A KYC failure reason is required")
        application.status = "kyc_failed"
        application.kyc_status = "failed"
        application.reviewer_id = admin.id
        application.review_note = review["note"]
        application.kyc_review_note = review["note"]
        application.provider = review["provider"]
        application.provider_account_id = review["provider_account_id"] or application.provider_account_id
        application.provider_account_status = review["provider_account_status"] or application.provider_account_status or "needs_clarification"
        application.fund_account_status = review["fund_account_status"] or application.fund_account_status or "failed"
        application.reviewed_on = datetime.datetime.utcnow()
        application.kyc_reviewed_on = application.reviewed_on
        db.session.commit()
        return application

    @classmethod
    @session_rollback(db)
    def approve(cls, application_uuid, note=None):
        admin = cls._require_admin()
        application = cls._get_owned(application_uuid)
        if application.status != "kyc_verified" or application.kyc_status != "verified":
            raise SellerApplicationInputError("KYC must be verified before seller approval")
        if application.fund_account_status != "validated":
            raise SellerApplicationInputError("Fund account must be validated before seller approval")
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
                legal_name=application.legal_name,
                business_type=application.business_type,
                country=application.country,
                kyc_status=application.kyc_status,
                provider=application.provider,
                provider_account_id=application.provider_account_id,
                provider_account_status=application.provider_account_status,
                fund_account_status=application.fund_account_status,
                payout_ready=True,
            )
            db.session.add(profile)
        else:
            profile.legal_name = application.legal_name
            profile.business_type = application.business_type
            profile.country = application.country
            profile.kyc_status = application.kyc_status
            profile.provider = application.provider
            profile.provider_account_id = application.provider_account_id
            profile.provider_account_status = application.provider_account_status
            profile.fund_account_status = application.fund_account_status
            profile.payout_ready = True
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

    @classmethod
    @session_rollback(db)
    def set_payout_readiness(cls, user_uuid, ready):
        cls._require_admin()
        from models.user import User
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user or user.user_type != USER_TYPE.SELLER.value:
            raise SellerApplicationInputError("Active seller not found")
        profile = SellerProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            raise SellerApplicationInputError("Seller profile not found")
        if ready and (profile.kyc_status != "verified" or profile.fund_account_status != "validated"):
            raise SellerApplicationInputError("KYC and fund account validation are required for payout readiness")
        profile.payout_ready = bool(ready)
        db.session.commit()
        return profile
