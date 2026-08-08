"""Add invoice foundation for paid marketplace orders."""
from alembic import op
import sqlalchemy as sa

revision = "003_invoices_and_config"
down_revision = "002_refund_provider_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "invoice_record",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=50), nullable=False, unique=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("marketplace_order.id"), nullable=False, unique=True),
        sa.Column("invoice_number", sa.String(length=80), nullable=False, unique=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="issued"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="INR"),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("issued_on", sa.DateTime()),
    )


def downgrade():
    op.drop_table("invoice_record")
