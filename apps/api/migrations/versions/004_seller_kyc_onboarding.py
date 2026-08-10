"""Add seller KYC and provider onboarding state."""
from alembic import op
import sqlalchemy as sa


revision = "004_seller_kyc_onboarding"
down_revision = "003_invoices_and_config"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("seller_applications", sa.Column("business_type", sa.String(length=50)))
    op.add_column("seller_applications", sa.Column("business_address", sa.String(length=500)))
    op.add_column("seller_applications", sa.Column("pan_number", sa.String(length=10)))
    op.add_column("seller_applications", sa.Column("gstin", sa.String(length=15)))
    op.add_column("seller_applications", sa.Column("bank_account_holder_name", sa.String(length=120)))
    op.add_column("seller_applications", sa.Column("bank_account_last4", sa.String(length=4)))
    op.add_column("seller_applications", sa.Column("bank_ifsc", sa.String(length=11)))
    op.add_column("seller_applications", sa.Column("kyc_document_type", sa.String(length=50)))
    op.add_column("seller_applications", sa.Column("kyc_document_reference", sa.String(length=500)))
    op.add_column(
        "seller_applications",
        sa.Column("kyc_status", sa.String(length=30), nullable=False, server_default="not_started"),
    )
    op.add_column("seller_applications", sa.Column("kyc_review_note", sa.String(length=5000)))
    op.add_column("seller_applications", sa.Column("kyc_reviewed_on", sa.DateTime()))
    op.add_column(
        "seller_applications",
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="manual"),
    )
    op.add_column("seller_applications", sa.Column("provider_account_id", sa.String(length=100)))
    op.add_column(
        "seller_applications",
        sa.Column("provider_account_status", sa.String(length=30), server_default="not_started"),
    )
    op.add_column(
        "seller_applications",
        sa.Column("fund_account_status", sa.String(length=30), server_default="not_started"),
    )
    op.create_index("seller_application_kyc_status_idx", "seller_applications", ["kyc_status"])

    op.add_column("seller_profiles", sa.Column("legal_name", sa.String(length=120)))
    op.add_column("seller_profiles", sa.Column("business_type", sa.String(length=50)))
    op.add_column("seller_profiles", sa.Column("country", sa.String(length=100)))
    op.add_column(
        "seller_profiles",
        sa.Column("kyc_status", sa.String(length=30), nullable=False, server_default="verified"),
    )
    op.add_column(
        "seller_profiles",
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="manual"),
    )
    op.add_column("seller_profiles", sa.Column("provider_account_id", sa.String(length=100)))
    op.add_column(
        "seller_profiles",
        sa.Column("provider_account_status", sa.String(length=30), server_default="activated"),
    )
    op.add_column(
        "seller_profiles",
        sa.Column("fund_account_status", sa.String(length=30), server_default="validated"),
    )
    op.create_index("seller_profile_kyc_status_idx", "seller_profiles", ["kyc_status"])


def downgrade():
    op.drop_index("seller_profile_kyc_status_idx", table_name="seller_profiles")
    op.drop_column("seller_profiles", "fund_account_status")
    op.drop_column("seller_profiles", "provider_account_status")
    op.drop_column("seller_profiles", "provider_account_id")
    op.drop_column("seller_profiles", "provider")
    op.drop_column("seller_profiles", "kyc_status")
    op.drop_column("seller_profiles", "country")
    op.drop_column("seller_profiles", "business_type")
    op.drop_column("seller_profiles", "legal_name")

    op.drop_index("seller_application_kyc_status_idx", table_name="seller_applications")
    op.drop_column("seller_applications", "fund_account_status")
    op.drop_column("seller_applications", "provider_account_status")
    op.drop_column("seller_applications", "provider_account_id")
    op.drop_column("seller_applications", "provider")
    op.drop_column("seller_applications", "kyc_reviewed_on")
    op.drop_column("seller_applications", "kyc_review_note")
    op.drop_column("seller_applications", "kyc_status")
    op.drop_column("seller_applications", "kyc_document_reference")
    op.drop_column("seller_applications", "kyc_document_type")
    op.drop_column("seller_applications", "bank_ifsc")
    op.drop_column("seller_applications", "bank_account_last4")
    op.drop_column("seller_applications", "bank_account_holder_name")
    op.drop_column("seller_applications", "gstin")
    op.drop_column("seller_applications", "pan_number")
    op.drop_column("seller_applications", "business_address")
    op.drop_column("seller_applications", "business_type")
