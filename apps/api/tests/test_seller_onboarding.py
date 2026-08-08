import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.sellerSerializers import SellerApplicationInputError, SellerApplicationSerializer


class SellerOnboardingValidationTests(unittest.TestCase):
    def test_submit_requires_terms(self):
        payload = {
            "store_name": "Study Notes",
            "store_description": "Digital study guides",
            "category": "Education",
            "product_types": "PDFs",
            "legal_name": "Study Notes Ltd",
            "country": "India",
            "phone_number": "9999999999",
            "terms_accepted": False,
        }

        with self.assertRaisesRegex(SellerApplicationInputError, "terms"):
            SellerApplicationSerializer._validate_fields(payload, require_submit=True)

    def test_submit_requires_business_fields(self):
        with self.assertRaisesRegex(SellerApplicationInputError, "Store name"):
            SellerApplicationSerializer._validate_fields({"terms_accepted": True}, require_submit=True)

    def test_status_set_contains_only_supported_workflow_states(self):
        self.assertEqual(
            SellerApplicationSerializer.STATUSES,
            {"draft", "submitted", "under_review", "needs_information", "approved", "rejected", "withdrawn"},
        )


if __name__ == "__main__":
    unittest.main()
