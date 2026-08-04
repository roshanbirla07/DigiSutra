import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.payoutSerializers import PayoutInputError, PayoutSerializer


class PayoutSerializerTests(unittest.TestCase):
    def test_create_payout_reduces_available_balance(self):
        seller = MagicMock()
        seller.id = 7
        seller.uuid = "seller::1"
        seller.username = "seller1"
        seller.user_type = "seller"

        seller_balance = MagicMock()
        seller_balance.available_for_payout = 250
        seller_balance.pending_payout = 0
        seller_balance.currency = "INR"
        payout = MagicMock()
        payout.seller = seller

        with patch("serializers.payoutSerializers.User") as user_model, \
                patch("serializers.payoutSerializers.SellerBalance") as seller_balance_model, \
                patch("serializers.payoutSerializers.SellerPayout") as seller_payout_model, \
                patch("serializers.payoutSerializers.db") as db_mock:
            user_model.query.filter_by.return_value.first.return_value = seller
            seller_balance_model.query.filter_by.return_value.first.return_value = seller_balance
            db_mock.session.add = MagicMock()
            db_mock.session.commit = MagicMock()
            seller_payout_model.return_value = payout

            serializer = PayoutSerializer()
            result = serializer.create({"seller_uuid": seller.uuid, "amount": "100.00"})

            self.assertIsNotNone(result)
            self.assertEqual(seller_balance.available_for_payout, 150)
            db_mock.session.commit.assert_called()

    def test_create_payout_rejects_amount_above_available_balance(self):
        seller = MagicMock()
        seller.id = 7
        seller.uuid = "seller::1"
        seller.user_type = "seller"

        seller_balance = MagicMock()
        seller_balance.available_for_payout = 25
        seller_balance.pending_payout = 0

        with patch("serializers.payoutSerializers.User") as user_model, \
                patch("serializers.payoutSerializers.SellerBalance") as seller_balance_model:
            user_model.query.filter_by.return_value.first.return_value = seller
            seller_balance_model.query.filter_by.return_value.first.return_value = seller_balance

            serializer = PayoutSerializer()
            with self.assertRaises(PayoutInputError):
                serializer.validate_create_data({"seller_uuid": seller.uuid, "amount": "100.00"})


if __name__ == "__main__":
    unittest.main()
