"""Add provider reconciliation fields to refunds."""
from alembic import op
import sqlalchemy as sa


revision = "002_refund_provider_fields"
down_revision = "001_seller_onboarding"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("refund_record", sa.Column("provider_refund_id", sa.String(length=100), unique=True))
    op.add_column("refund_record", sa.Column("provider_status", sa.String(length=50)))
    op.add_column("refund_record", sa.Column("failure_reason", sa.Text()))


def downgrade():
    op.drop_column("refund_record", "failure_reason")
    op.drop_column("refund_record", "provider_status")
    op.drop_column("refund_record", "provider_refund_id")
