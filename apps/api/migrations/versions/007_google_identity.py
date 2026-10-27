"""Store the stable Google identity for linked accounts."""
from alembic import op
import sqlalchemy as sa


revision = "007_google_identity"
down_revision = "006_payment_webhook_events"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("google_sub", sa.String(length=255), nullable=True))
    op.create_index("user_google_sub_idx", "user", ["google_sub"], unique=True)


def downgrade():
    op.drop_index("user_google_sub_idx", table_name="user")
    op.drop_column("user", "google_sub")
