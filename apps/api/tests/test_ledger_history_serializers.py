import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.ledgerSerializers import LedgerSerializer


class BuyerPurchaseHistoryTests(unittest.TestCase):
    def test_list_buyer_purchases_serializes_orders_access_and_refunds(self):
        order = MagicMock()
        order.uuid = "order::1"
        order.buyer = MagicMock()
        order.buyer.uuid = "user::buyer"
        order.buyer.username = "buyer1"
        order.seller = MagicMock()
        order.seller.uuid = "user::seller"
        order.seller.username = "seller1"
        order.product = MagicMock()
        order.product.uuid = "product::1"
        order.product.title = "Template"
        order.gross_amount = "100.00"
        order.platform_fee = "10.00"
        order.tax_amount = "5.00"
        order.net_seller_amount = "85.00"
        order.payment_status = "paid"
        order.delivery_status = "ready"
        order.refund_status = "none"
        order.provider = "razorpay"
        order.provider_order_id = "provider-order"
        order.provider_payment_id = "provider-payment"
        order.created_on = MagicMock()
        order.modified_on = MagicMock()
        order.created_on.isoformat.return_value = "2026-08-05T00:00:00"
        order.modified_on.isoformat.return_value = "2026-08-05T00:00:00"

        access_record = MagicMock()
        access_record.uuid = "access::1"
        access_record.order = order
        access_record.asset = MagicMock()
        access_record.asset.uuid = "asset::1"
        access_record.access_status = "granted"
        access_record.download_count = 2
        access_record.revoked_at = None
        access_record.created_on = MagicMock()
        access_record.modified_on = MagicMock()
        access_record.created_on.isoformat.return_value = "2026-08-05T00:00:00"
        access_record.modified_on.isoformat.return_value = "2026-08-05T00:00:00"
        order.product_access_records.all.return_value = [access_record]
        order.refund_records.all.return_value = []

        with patch.object(LedgerSerializer, "list_orders_for_buyer", return_value=[order]):
            serializer = LedgerSerializer()
            history = serializer.list_buyer_purchases(7)

            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["order"]["uuid"], "order::1")
            self.assertEqual(history[0]["access_records"][0]["asset_uuid"], "asset::1")
            self.assertEqual(history[0]["refunds"], [])


if __name__ == "__main__":
    unittest.main()
