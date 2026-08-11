"""Create core marketplace schema.

Revision ID: 000_core_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa


revision = "000_core_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=50)),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50)),
        sa.Column("phone_number", sa.String(length=13)),
        sa.Column("uuid", sa.String(length=100), nullable=False, unique=True),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("modified_on", sa.DateTime()),
        sa.Column("changed_by", sa.String(length=50)),
        sa.Column("is_active", sa.String(length=15)),
        sa.Column("user_type", sa.String(length=50)),
    )
    op.create_index("user_func_lower_email_idx", "user", [sa.text("lower(email)")])
    op.create_index("user_func_lower_username_idx", "user", [sa.text("lower(username)")])

    op.create_table(
        "sellers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id")),
    )

    op.create_table(
        "product",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=100), nullable=False, unique=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="INR"),
        sa.Column("category", sa.String(length=100)),
        sa.Column("image_uri", sa.String(length=2048)),
        sa.Column("image_alt", sa.String(length=255)),
        sa.Column("image_provider", sa.String(length=50)),
        sa.Column("image_key", sa.String(length=255)),
        sa.Column("image_mime_type", sa.String(length=100)),
        sa.Column("image_size_bytes", sa.BigInteger()),
        sa.Column("image_width", sa.Integer()),
        sa.Column("image_height", sa.Integer()),
        sa.Column("image_sort_order", sa.Integer(), server_default="0"),
        sa.Column("image_is_primary", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("modified_on", sa.DateTime()),
        sa.Column("created_by", sa.String(length=50)),
        sa.Column("modified_by", sa.String(length=50)),
    )
    op.create_index("product_func_lower_title_idx", "product", [sa.text("lower(title)")])
    op.create_index("product_owner_id_idx", "product", ["owner_id"])

    op.create_table(
        "product_asset",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=100), nullable=False, unique=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("product.id"), nullable=False),
        sa.Column("storage_provider", sa.String(length=50), nullable=False, server_default="s3"),
        sa.Column("bucket_name", sa.String(length=255), nullable=False),
        sa.Column("object_key", sa.String(length=1024), nullable=False, unique=True),
        sa.Column("original_filename", sa.String(length=255)),
        sa.Column("content_type", sa.String(length=100)),
        sa.Column("size_bytes", sa.BigInteger()),
        sa.Column("checksum_sha256", sa.String(length=64)),
        sa.Column("cloudfront_url", sa.String(length=2048)),
        sa.Column("asset_status", sa.String(length=30), nullable=False, server_default="pending_upload"),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("modified_on", sa.DateTime()),
    )
    op.create_index("product_asset_uuid_idx", "product_asset", ["uuid"])
    op.create_index("product_asset_product_id_idx", "product_asset", ["product_id"])
    op.create_index("product_asset_status_idx", "product_asset", ["asset_status"])
    op.create_index("product_asset_object_key_idx", "product_asset", ["object_key"])

    op.create_table(
        "marketplace_order",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=100), nullable=False, unique=True),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("product.id"), nullable=False),
        sa.Column("seller_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("gross_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("platform_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("net_seller_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("delivery_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("refund_status", sa.String(length=30), nullable=False, server_default="none"),
        sa.Column("provider", sa.String(length=50)),
        sa.Column("provider_order_id", sa.String(length=100), unique=True),
        sa.Column("provider_payment_id", sa.String(length=100), unique=True),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("modified_on", sa.DateTime()),
        sa.Column("created_by", sa.String(length=50)),
        sa.Column("modified_by", sa.String(length=50)),
    )
    op.create_index("marketplace_order_uuid_idx", "marketplace_order", ["uuid"])
    op.create_index("marketplace_order_buyer_id_idx", "marketplace_order", ["buyer_id"])
    op.create_index("marketplace_order_seller_id_idx", "marketplace_order", ["seller_id"])
    op.create_index("marketplace_order_product_id_idx", "marketplace_order", ["product_id"])
    op.create_index("marketplace_order_payment_status_idx", "marketplace_order", ["payment_status"])

    op.create_table(
        "product_asset_download",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=100), nullable=False, unique=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("product_asset.id"), nullable=False),
        sa.Column("order_uuid", sa.String(length=100)),
        sa.Column("downloaded_by", sa.String(length=50)),
        sa.Column("download_url", sa.String(length=2048)),
        sa.Column("user_agent", sa.String(length=500)),
        sa.Column("ip_address", sa.String(length=100)),
        sa.Column("created_on", sa.DateTime()),
    )
    op.create_index("product_asset_download_uuid_idx", "product_asset_download", ["uuid"])
    op.create_index("product_asset_download_asset_id_idx", "product_asset_download", ["asset_id"])

    op.create_table(
        "seller_balance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seller_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, unique=True),
        sa.Column("available_for_payout", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("pending_payout", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="INR"),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("modified_on", sa.DateTime()),
    )
    op.create_index("seller_balance_seller_id_idx", "seller_balance", ["seller_id"])

    op.create_table(
        "seller_payout",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=100), nullable=False, unique=True),
        sa.Column("seller_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("payout_method", sa.String(length=50), nullable=False, server_default="manual"),
        sa.Column("batch_id", sa.String(length=100)),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("processed_at", sa.DateTime()),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("modified_on", sa.DateTime()),
    )
    op.create_index("seller_payout_uuid_idx", "seller_payout", ["uuid"])
    op.create_index("seller_payout_seller_id_idx", "seller_payout", ["seller_id"])
    op.create_index("seller_payout_status_idx", "seller_payout", ["status"])

    op.create_table(
        "refund_record",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=100), nullable=False, unique=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("marketplace_order.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="requested"),
        sa.Column("reason", sa.Text()),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("modified_on", sa.DateTime()),
        sa.Column("resolved_on", sa.DateTime()),
    )
    op.create_index("refund_record_uuid_idx", "refund_record", ["uuid"])
    op.create_index("refund_record_order_id_idx", "refund_record", ["order_id"])
    op.create_index("refund_record_status_idx", "refund_record", ["status"])

    op.create_table(
        "product_access",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=100), nullable=False, unique=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("marketplace_order.id"), nullable=False),
        sa.Column("asset_id", sa.String(length=100)),
        sa.Column("access_status", sa.String(length=30), nullable=False, server_default="granted"),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revoked_at", sa.DateTime()),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("modified_on", sa.DateTime()),
    )
    op.create_index("product_access_uuid_idx", "product_access", ["uuid"])
    op.create_index("product_access_order_id_idx", "product_access", ["order_id"])
    op.create_index("product_access_status_idx", "product_access", ["access_status"])

    op.create_table(
        "delivery_token_use",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token_jti", sa.String(length=100), nullable=False, unique=True),
        sa.Column("user_uuid", sa.String(length=100), nullable=False),
        sa.Column("asset_uuid", sa.String(length=100), nullable=False),
        sa.Column("order_uuid", sa.String(length=100), nullable=False),
        sa.Column("consumed_on", sa.DateTime(), nullable=False),
    )
    op.create_index("delivery_token_use_asset_uuid_idx", "delivery_token_use", ["asset_uuid"])
    op.create_index("delivery_token_use_order_uuid_idx", "delivery_token_use", ["order_uuid"])

    op.create_table(
        "support_ticket",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=100), nullable=False, unique=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("resolution", sa.Text()),
        sa.Column("resolved_by_id", sa.Integer(), sa.ForeignKey("user.id")),
        sa.Column("resolved_at", sa.DateTime()),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("modified_on", sa.DateTime()),
    )

    op.create_table(
        "product_flag",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=100), nullable=False, unique=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("product.id"), nullable=False),
        sa.Column("reported_by_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("resolved_on", sa.DateTime()),
    )


def downgrade():
    op.drop_table("product_flag")
    op.drop_table("support_ticket")
    op.drop_index("delivery_token_use_order_uuid_idx", table_name="delivery_token_use")
    op.drop_index("delivery_token_use_asset_uuid_idx", table_name="delivery_token_use")
    op.drop_table("delivery_token_use")
    op.drop_index("product_access_status_idx", table_name="product_access")
    op.drop_index("product_access_order_id_idx", table_name="product_access")
    op.drop_index("product_access_uuid_idx", table_name="product_access")
    op.drop_table("product_access")
    op.drop_index("refund_record_status_idx", table_name="refund_record")
    op.drop_index("refund_record_order_id_idx", table_name="refund_record")
    op.drop_index("refund_record_uuid_idx", table_name="refund_record")
    op.drop_table("refund_record")
    op.drop_index("seller_payout_status_idx", table_name="seller_payout")
    op.drop_index("seller_payout_seller_id_idx", table_name="seller_payout")
    op.drop_index("seller_payout_uuid_idx", table_name="seller_payout")
    op.drop_table("seller_payout")
    op.drop_index("seller_balance_seller_id_idx", table_name="seller_balance")
    op.drop_table("seller_balance")
    op.drop_index("product_asset_download_asset_id_idx", table_name="product_asset_download")
    op.drop_index("product_asset_download_uuid_idx", table_name="product_asset_download")
    op.drop_table("product_asset_download")
    op.drop_index("marketplace_order_payment_status_idx", table_name="marketplace_order")
    op.drop_index("marketplace_order_product_id_idx", table_name="marketplace_order")
    op.drop_index("marketplace_order_seller_id_idx", table_name="marketplace_order")
    op.drop_index("marketplace_order_buyer_id_idx", table_name="marketplace_order")
    op.drop_index("marketplace_order_uuid_idx", table_name="marketplace_order")
    op.drop_table("marketplace_order")
    op.drop_index("product_asset_object_key_idx", table_name="product_asset")
    op.drop_index("product_asset_status_idx", table_name="product_asset")
    op.drop_index("product_asset_product_id_idx", table_name="product_asset")
    op.drop_index("product_asset_uuid_idx", table_name="product_asset")
    op.drop_table("product_asset")
    op.drop_index("product_owner_id_idx", table_name="product")
    op.drop_index("product_func_lower_title_idx", table_name="product")
    op.drop_table("product")
    op.drop_table("sellers")
    op.drop_index("user_func_lower_username_idx", table_name="user")
    op.drop_index("user_func_lower_email_idx", table_name="user")
    op.drop_table("user")
