import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.sellerSerializers import SellerApplicationInputError, SellerApplicationSerializer


class SellerOnboardingValidationTests(unittest.TestCase):
    def valid_payload(self):
        return {
            "store_name": "Study Notes",
            "store_description": "Digital study guides",
            "category": "Education",
            "product_types": "PDFs",
            "legal_name": "Study Notes Ltd",
            "business_type": "private_limited",
            "business_address": "12 Market Road, Mumbai",
            "pan_number": "ABCDE1234F",
            "gstin": "27ABCDE1234F1Z5",
            "country": "India",
            "phone_number": "9999999999",
            "bank_account_holder_name": "Study Notes Ltd",
            "bank_account_last4": "1234",
            "bank_ifsc": "HDFC0123456",
            "kyc_document_type": "company_pan",
            "kyc_document_reference": "s3://private-kyc/study-notes/pan.pdf",
            "terms_accepted": True,
        }

    def test_submit_requires_terms(self):
        payload = self.valid_payload()
        payload["terms_accepted"] = False

        with self.assertRaisesRegex(SellerApplicationInputError, "terms"):
            SellerApplicationSerializer._validate_fields(payload, require_submit=True)

    def test_submit_requires_business_fields(self):
        with self.assertRaisesRegex(SellerApplicationInputError, "Store name"):
            SellerApplicationSerializer._validate_fields({"terms_accepted": True}, require_submit=True)

    def test_status_set_contains_only_supported_workflow_states(self):
        self.assertEqual(
            SellerApplicationSerializer.STATUSES,
            {
                "draft",
                "submitted",
                "under_review",
                "kyc_pending",
                "kyc_in_review",
                "kyc_verified",
                "kyc_failed",
                "needs_information",
                "approved",
                "rejected",
                "withdrawn",
                "suspended",
            },
        )

    def test_submit_accepts_complete_kyc_payload(self):
        values = SellerApplicationSerializer._validate_fields(self.valid_payload(), require_submit=True)

        self.assertEqual(values["pan_number"], "ABCDE1234F")
        self.assertEqual(values["bank_ifsc"], "HDFC0123456")

    def test_submit_accepts_core_fields_without_supporting_details(self):
        payload = self.valid_payload()
        for field in (
            "store_description", "product_types", "business_address", "country",
            "phone_number", "gstin", "kyc_document_type", "kyc_document_reference",
        ):
            payload.pop(field)

        values = SellerApplicationSerializer._validate_fields(payload, require_submit=True)

        self.assertEqual(values, payload)

    def test_submit_rejects_invalid_pan(self):
        payload = self.valid_payload()
        payload["pan_number"] = "bad-pan"

        with self.assertRaisesRegex(SellerApplicationInputError, "PAN"):
            SellerApplicationSerializer._validate_fields(payload, require_submit=True)

    def test_submit_rejects_invalid_ifsc(self):
        payload = self.valid_payload()
        payload["bank_ifsc"] = "BAD123"

        with self.assertRaisesRegex(SellerApplicationInputError, "IFSC"):
            SellerApplicationSerializer._validate_fields(payload, require_submit=True)

    def test_upi_submission_requires_enabled_onboarding_and_valid_address(self):
        payload = self.valid_payload()
        for field in SellerApplicationSerializer.BANK_FIELDS:
            payload.pop(field)
        payload.update(payout_destination="upi", upi_id="demo@bank")

        with self.assertRaisesRegex(SellerApplicationInputError, "UPI payouts are unavailable"):
            SellerApplicationSerializer._validate_fields(payload, require_submit=True)

        with patch("serializers.sellerSerializers.ENABLE_SELLER_UPI_ONBOARDING", True):
            self.assertEqual(
                SellerApplicationSerializer._validate_fields(payload, require_submit=True)["upi_id"],
                "demo@bank",
            )
            payload["upi_id"] = "invalid"
            with self.assertRaisesRegex(SellerApplicationInputError, "valid UPI ID"):
                SellerApplicationSerializer._validate_fields(payload, require_submit=True)

    @patch("serializers.sellerSerializers.ENABLE_SELLER_UPI_ONBOARDING", True)
    def test_changing_destination_clears_old_details_and_resets_verification(self):
        serializer = SellerApplicationSerializer
        application = SimpleNamespace(
            payout_destination="bank_account", upi_id=None, fund_account_status="validated",
            bank_account_holder_name="Example", bank_account_last4="1234", bank_ifsc="HDFC0123456",
        )
        serializer._apply_application_fields(application, {"payout_destination": "upi", "upi_id": "demo@bank"})
        self.assertEqual(application.upi_id, "demo@bank")
        self.assertTrue(all(getattr(application, field) is None for field in serializer.BANK_FIELDS))
        self.assertEqual(application.fund_account_status, "not_started")

        serializer._apply_application_fields(application, {"payout_destination": "bank_account", "bank_account_last4": "5678"})
        self.assertIsNone(application.upi_id)
        self.assertEqual(application.bank_account_last4, "5678")

    @patch("serializers.sellerSerializers.ENABLE_SELLER_UPI_ONBOARDING", True)
    def test_admin_must_record_upi_holder_name_verification(self):
        serializer = SellerApplicationSerializer
        application = SimpleNamespace(status="kyc_in_review", payout_destination="upi", upi_id="demo@bank")
        with patch.object(serializer, "_require_admin"), patch.object(serializer, "_get_owned", return_value=application):
            with self.assertRaisesRegex(SellerApplicationInputError, "holder-name verification"):
                serializer.verify_kyc.__wrapped__(serializer, "application::1", {"verified_upi_id": "demo@bank"})
            with self.assertRaisesRegex(SellerApplicationInputError, "current payout destination"):
                serializer.verify_kyc.__wrapped__(serializer, "application::1", {
                    "verified_upi_id": "old@bank", "note": "Matched the holder name",
                })
        self.assertEqual(application.status, "kyc_in_review")


if __name__ == "__main__":
    unittest.main()

class SellerApplicationSummaryTests(unittest.TestCase):
    def test_summary_omits_sensitive_kyc_and_bank_fields(self):
        from unittest.mock import MagicMock
        application = MagicMock()
        application.uuid = "application::1"
        application.applicant = None
        application.status = "submitted"
        application.store_name = "Example store"
        application.category = "Guides"
        application.kyc_status = "pending"
        application.fund_account_status = "pending"
        application.provider = "manual"
        application.submitted_on = None
        application.created_on = None
        summary = SellerApplicationSerializer.serialize_application_summary(application)
        self.assertEqual(summary["store_name"], "Example store")
        for field in ("pan_number", "gstin", "business_address", "phone_number", "bank_ifsc", "kyc_document_reference", "provider_account_id", "upi_id"):
            self.assertNotIn(field, summary)
