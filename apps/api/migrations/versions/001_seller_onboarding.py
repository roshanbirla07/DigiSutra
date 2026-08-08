"""Add seller application and profile tables.

Revision ID: 001_seller_onboarding
Revises:
"""
from alembic import op
import sqlalchemy as sa


revision = "001_seller_onboarding"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "seller_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=50), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, unique=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("store_name", sa.String(length=120)),
        sa.Column("store_description", sa.String(length=5000)),
        sa.Column("category", sa.String(length=100)),
        sa.Column("product_types", sa.String(length=1000)),
        sa.Column("website_url", sa.String(length=2048)),
        sa.Column("portfolio_url", sa.String(length=2048)),
        sa.Column("legal_name", sa.String(length=120)),
        sa.Column("country", sa.String(length=100)),
        sa.Column("phone_number", sa.String(length=30)),
        sa.Column("terms_accepted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("submitted_on", sa.DateTime()),
        sa.Column("reviewed_on", sa.DateTime()),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("user.id")),
        sa.Column("review_note", sa.String(length=5000)),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("modified_on", sa.DateTime()),
    )
    op.create_index("seller_application_status_idx", "seller_applications", ["status"])
    op.create_index("seller_application_user_id_idx", "seller_applications", ["user_id"])
    op.create_table(
        "seller_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=50), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, unique=True),
        sa.Column("store_name", sa.String(length=120), nullable=False),
        sa.Column("store_description", sa.String(length=5000)),
        sa.Column("category", sa.String(length=100)),
        sa.Column("website_url", sa.String(length=2048)),
        sa.Column("portfolio_url", sa.String(length=2048)),
        sa.Column("payout_ready", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_suspended", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_on", sa.DateTime()),
        sa.Column("modified_on", sa.DateTime()),
    )


def downgrade():
    op.drop_table("seller_profiles")
    op.drop_index("seller_application_user_id_idx", table_name="seller_applications")
    op.drop_index("seller_application_status_idx", table_name="seller_applications")
    op.drop_table("seller_applications")
