"""Reconcile UUID and external identifier column widths."""
from alembic import op
import sqlalchemy as sa


revision = "005_reconcile_identifier_widths"
down_revision = "004_seller_kyc_onboarding"
branch_labels = None
depends_on = None


IDENTIFIER_COLUMNS = {
    "user": ("uuid",),
    "product": ("uuid",),
    "product_asset": ("uuid",),
    "product_asset_download": ("uuid", "order_uuid"),
    "marketplace_order": ("uuid", "provider_order_id", "provider_payment_id"),
    "seller_payout": ("uuid", "batch_id"),
    "refund_record": ("uuid", "provider_refund_id"),
    "invoice_record": ("uuid",),
    "product_access": ("uuid", "asset_id"),
    "delivery_token_use": ("token_jti", "user_uuid", "asset_uuid", "order_uuid"),
    "seller_applications": ("uuid", "provider_account_id"),
    "seller_profiles": ("uuid", "provider_account_id"),
}


def upgrade():
    for table_name, column_names in IDENTIFIER_COLUMNS.items():
        for column_name in column_names:
            op.alter_column(
                table_name,
                column_name,
                existing_type=sa.String(length=50),
                type_=sa.String(length=100),
                existing_nullable=True,
            )


def downgrade():
    # Unsafe downgrade: provider IDs and UUID-like values may already exceed
    # 50 characters. Restore from a pre-migration backup if a rollback is
    # required.
    raise RuntimeError(
        "Downgrading 005_reconcile_identifier_widths can truncate identifier data."
    )
