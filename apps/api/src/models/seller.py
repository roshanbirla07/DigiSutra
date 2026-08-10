import datetime

from configuration.db_routing import db


class SellerApplication(db.Model):
    __tablename__ = "seller_applications"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    status = db.Column(db.String(30), nullable=False, default="draft")
    store_name = db.Column(db.String(120), nullable=True)
    store_description = db.Column(db.String(5000), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    product_types = db.Column(db.String(1000), nullable=True)
    website_url = db.Column(db.String(2048), nullable=True)
    portfolio_url = db.Column(db.String(2048), nullable=True)
    legal_name = db.Column(db.String(120), nullable=True)
    business_type = db.Column(db.String(50), nullable=True)
    business_address = db.Column(db.String(500), nullable=True)
    pan_number = db.Column(db.String(10), nullable=True)
    gstin = db.Column(db.String(15), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(30), nullable=True)
    bank_account_holder_name = db.Column(db.String(120), nullable=True)
    bank_account_last4 = db.Column(db.String(4), nullable=True)
    bank_ifsc = db.Column(db.String(11), nullable=True)
    kyc_document_type = db.Column(db.String(50), nullable=True)
    kyc_document_reference = db.Column(db.String(500), nullable=True)
    kyc_status = db.Column(db.String(30), nullable=False, default="not_started")
    kyc_review_note = db.Column(db.String(5000), nullable=True)
    kyc_reviewed_on = db.Column(db.DateTime, nullable=True)
    provider = db.Column(db.String(50), nullable=False, default="manual")
    provider_account_id = db.Column(db.String(100), nullable=True)
    provider_account_status = db.Column(db.String(30), nullable=True)
    fund_account_status = db.Column(db.String(30), nullable=True)
    terms_accepted = db.Column(db.Boolean, nullable=False, default=False)
    submitted_on = db.Column(db.DateTime, nullable=True)
    reviewed_on = db.Column(db.DateTime, nullable=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    review_note = db.Column(db.String(5000), nullable=True)
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    applicant = db.relationship("User", foreign_keys=[user_id], backref=db.backref("seller_application", uselist=False))
    reviewer = db.relationship("User", foreign_keys=[reviewer_id])


class SellerProfile(db.Model):
    __tablename__ = "seller_profiles"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    store_name = db.Column(db.String(120), nullable=False)
    store_description = db.Column(db.String(5000), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    website_url = db.Column(db.String(2048), nullable=True)
    portfolio_url = db.Column(db.String(2048), nullable=True)
    legal_name = db.Column(db.String(120), nullable=True)
    business_type = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    kyc_status = db.Column(db.String(30), nullable=False, default="verified")
    provider = db.Column(db.String(50), nullable=False, default="manual")
    provider_account_id = db.Column(db.String(100), nullable=True)
    provider_account_status = db.Column(db.String(30), nullable=True)
    fund_account_status = db.Column(db.String(30), nullable=True)
    payout_ready = db.Column(db.Boolean, nullable=False, default=False)
    payout_hold = db.Column(db.Boolean, nullable=False, default=False)
    is_suspended = db.Column(db.Boolean, nullable=False, default=False)
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    user = db.relationship("User", backref=db.backref("seller_profile", uselist=False))
