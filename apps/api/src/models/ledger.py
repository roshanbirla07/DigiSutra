import datetime

from configuration.db_routing import db


class MarketplaceOrder(db.Model):
    __tablename__ = "marketplace_order"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(100), unique=True, nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    buyer = db.relationship(
        "User",
        foreign_keys=[buyer_id],
        backref=db.backref("marketplace_orders", lazy="dynamic"),
    )
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    product = db.relationship("Product", backref=db.backref("marketplace_orders", lazy="dynamic"))
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    seller = db.relationship("User", foreign_keys=[seller_id], backref=db.backref("sold_marketplace_orders", lazy="dynamic"))
    gross_amount = db.Column(db.Numeric(10, 2), nullable=False)
    platform_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    net_seller_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_status = db.Column(db.String(30), nullable=False, default="pending")
    delivery_status = db.Column(db.String(30), nullable=False, default="pending")
    refund_status = db.Column(db.String(30), nullable=False, default="none")
    provider = db.Column(db.String(50))
    provider_order_id = db.Column(db.String(100), unique=True)
    provider_payment_id = db.Column(db.String(100), unique=True)
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_by = db.Column(db.String(50))
    modified_by = db.Column(db.String(50))

    __table_args__ = (
        db.Index("marketplace_order_uuid_idx", uuid),
        db.Index("marketplace_order_buyer_id_idx", buyer_id),
        db.Index("marketplace_order_seller_id_idx", seller_id),
        db.Index("marketplace_order_product_id_idx", product_id),
        db.Index("marketplace_order_payment_status_idx", payment_status),
    )


class SellerBalance(db.Model):
    __tablename__ = "seller_balance"

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    seller = db.relationship("User", backref=db.backref("seller_balance", uselist=False))
    available_for_payout = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    pending_payout = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    currency = db.Column(db.String(10), nullable=False, default="INR")
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (db.Index("seller_balance_seller_id_idx", seller_id),)


class SellerPayout(db.Model):
    __tablename__ = "seller_payout"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(100), unique=True, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    seller = db.relationship("User", backref=db.backref("seller_payouts", lazy="dynamic"))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pending")
    payout_method = db.Column(db.String(50), nullable=False, default="manual")
    batch_id = db.Column(db.String(100))
    failure_reason = db.Column(db.Text)
    processed_at = db.Column(db.DateTime)
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        db.Index("seller_payout_uuid_idx", uuid),
        db.Index("seller_payout_seller_id_idx", seller_id),
        db.Index("seller_payout_status_idx", status),
    )


class RefundRecord(db.Model):
    __tablename__ = "refund_record"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(100), unique=True, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("marketplace_order.id"), nullable=False)
    order = db.relationship("MarketplaceOrder", backref=db.backref("refund_records", lazy="dynamic"))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="requested")
    reason = db.Column(db.Text)
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    resolved_on = db.Column(db.DateTime)
    provider_refund_id = db.Column(db.String(100), unique=True)
    provider_status = db.Column(db.String(50))
    failure_reason = db.Column(db.Text)

    __table_args__ = (
        db.Index("refund_record_uuid_idx", uuid),
        db.Index("refund_record_order_id_idx", order_id),
        db.Index("refund_record_status_idx", status),
    )


class InvoiceRecord(db.Model):
    __tablename__ = "invoice_record"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(100), unique=True, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("marketplace_order.id"), nullable=False, unique=True)
    order = db.relationship("MarketplaceOrder", backref=db.backref("invoice", uselist=False))
    invoice_number = db.Column(db.String(80), unique=True, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="issued")
    currency = db.Column(db.String(10), nullable=False, default="INR")
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    issued_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ProductAccess(db.Model):
    __tablename__ = "product_access"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(100), unique=True, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("marketplace_order.id"), nullable=False)
    order = db.relationship("MarketplaceOrder", backref=db.backref("product_access_records", lazy="dynamic"))
    asset_id = db.Column(db.String(100))
    access_status = db.Column(db.String(30), nullable=False, default="granted")
    download_count = db.Column(db.Integer, nullable=False, default=0)
    revoked_at = db.Column(db.DateTime)
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        db.Index("product_access_uuid_idx", uuid),
        db.Index("product_access_order_id_idx", order_id),
        db.Index("product_access_status_idx", access_status),
    )


class DeliveryTokenUse(db.Model):
    __tablename__ = "delivery_token_use"

    id = db.Column(db.Integer, primary_key=True)
    token_jti = db.Column(db.String(100), unique=True, nullable=False)
    user_uuid = db.Column(db.String(100), nullable=False)
    asset_uuid = db.Column(db.String(100), nullable=False)
    order_uuid = db.Column(db.String(100), nullable=False)
    consumed_on = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index("delivery_token_use_asset_uuid_idx", asset_uuid),
        db.Index("delivery_token_use_order_uuid_idx", order_uuid),
    )
