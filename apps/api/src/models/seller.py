import datetime

from configuration.db_routing import db


class SellerApplication(db.Model):
    __tablename__ = "seller_applications"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    status = db.Column(db.String(30), nullable=False, default="draft")
    store_name = db.Column(db.String(120), nullable=True)
    store_description = db.Column(db.String(5000), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    product_types = db.Column(db.String(1000), nullable=True)
    website_url = db.Column(db.String(2048), nullable=True)
    portfolio_url = db.Column(db.String(2048), nullable=True)
    legal_name = db.Column(db.String(120), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(30), nullable=True)
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
    uuid = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    store_name = db.Column(db.String(120), nullable=False)
    store_description = db.Column(db.String(5000), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    website_url = db.Column(db.String(2048), nullable=True)
    portfolio_url = db.Column(db.String(2048), nullable=True)
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
