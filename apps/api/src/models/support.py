import datetime

from configuration.db_routing import db


class SupportTicket(db.Model):
    __tablename__ = "support_ticket"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(100), unique=True, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_by = db.relationship("User", foreign_keys=[created_by_id], backref=db.backref("support_tickets", lazy="dynamic"))
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="open")
    resolution = db.Column(db.Text)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    resolved_by = db.relationship("User", foreign_keys=[resolved_by_id], backref=db.backref("resolved_support_tickets", lazy="dynamic"))
    resolved_at = db.Column(db.DateTime)
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ProductFlag(db.Model):
    __tablename__ = "product_flag"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(100), unique=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    product = db.relationship("Product", backref=db.backref("flags", lazy="dynamic"))
    reported_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reported_by = db.relationship("User", foreign_keys=[reported_by_id], backref=db.backref("product_flags", lazy="dynamic"))
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="open")
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    resolved_on = db.Column(db.DateTime)
