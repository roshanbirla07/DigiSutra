import os
import sys
import unittest

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


if __name__ == "__main__":
    unittest.main()
