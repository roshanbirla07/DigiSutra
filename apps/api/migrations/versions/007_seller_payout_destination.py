"""Add an optional UPI destination for seller applications."""
from alembic import op
import sqlalchemy as sa


revision = "007_seller_payout_destination"
down_revision = "006_payment_webhook_events"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("seller_applications", sa.Column(
        "payout_destination", sa.String(length=12), nullable=False, server_default="bank_account",
    ))
    op.add_column("seller_applications", sa.Column("upi_id", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("seller_applications", "upi_id")
    op.drop_column("seller_applications", "payout_destination")
