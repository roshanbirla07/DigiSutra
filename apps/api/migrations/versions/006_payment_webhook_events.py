"""Add payment webhook replay tracking."""
from alembic import op
import sqlalchemy as sa


revision = "006_payment_webhook_events"
down_revision = "005_reconcile_identifier_widths"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "payment_webhook_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=100), nullable=False, unique=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("event_key", sa.String(length=100), nullable=False, unique=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("provider_entity_id", sa.String(length=100)),
        sa.Column("received_on", sa.DateTime(), nullable=False),
        sa.Column("processed_on", sa.DateTime()),
    )
    op.create_index("payment_webhook_event_key_idx", "payment_webhook_event", ["event_key"])
    op.create_index("payment_webhook_event_type_idx", "payment_webhook_event", ["event_type"])


def downgrade():
    op.drop_index("payment_webhook_event_type_idx", table_name="payment_webhook_event")
    op.drop_index("payment_webhook_event_key_idx", table_name="payment_webhook_event")
    op.drop_table("payment_webhook_event")
