import datetime
from sqlalchemy import func

from configuration.db_routing import db


class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(50), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner = db.relationship("User", backref=db.backref("products", lazy="dynamic"))
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="INR")
    category = db.Column(db.String(100))
    image_uri = db.Column(db.String(2048))
    image_alt = db.Column(db.String(255))
    image_provider = db.Column(db.String(50))
    image_key = db.Column(db.String(255))
    image_mime_type = db.Column(db.String(100))
    image_size_bytes = db.Column(db.BigInteger)
    image_width = db.Column(db.Integer)
    image_height = db.Column(db.Integer)
    image_sort_order = db.Column(db.Integer, default=0)
    image_is_primary = db.Column(db.Boolean, nullable=False, default=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_public = db.Column(db.Boolean, nullable=False, default=True)
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    created_by = db.Column(db.String(50))
    modified_by = db.Column(db.String(50))

    __table_args__ = (
        db.Index("product_func_lower_title_idx", func.lower(title)),
        db.Index("product_owner_id_idx", owner_id),
    )


class ProductAsset(db.Model):
    __tablename__ = "product_asset"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(50), unique=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    product = db.relationship("Product", backref=db.backref("assets", lazy="dynamic"))
    storage_provider = db.Column(db.String(50), nullable=False, default="s3")
    bucket_name = db.Column(db.String(255), nullable=False)
    object_key = db.Column(db.String(1024), nullable=False, unique=True)
    original_filename = db.Column(db.String(255))
    content_type = db.Column(db.String(100))
    size_bytes = db.Column(db.BigInteger)
    checksum_sha256 = db.Column(db.String(64))
    cloudfront_url = db.Column(db.String(2048))
    asset_status = db.Column(db.String(30), nullable=False, default="pending_upload")
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    __table_args__ = (
        db.Index("product_asset_uuid_idx", uuid),
        db.Index("product_asset_product_id_idx", product_id),
        db.Index("product_asset_status_idx", asset_status),
        db.Index("product_asset_object_key_idx", object_key),
    )


class ProductAssetDownload(db.Model):
    __tablename__ = "product_asset_download"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(50), unique=True, nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey("product_asset.id"), nullable=False)
    asset = db.relationship("ProductAsset", backref=db.backref("download_events", lazy="dynamic"))
    order_uuid = db.Column(db.String(50))
    downloaded_by = db.Column(db.String(50))
    download_url = db.Column(db.String(2048))
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(100))
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        db.Index("product_asset_download_uuid_idx", uuid),
        db.Index("product_asset_download_asset_id_idx", asset_id),
    )
