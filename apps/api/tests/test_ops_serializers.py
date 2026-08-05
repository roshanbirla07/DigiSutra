import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.opsSerializers import OpsSerializer


class OpsSerializerTests(unittest.TestCase):
    def test_summary_returns_risk_buckets(self):
        with patch("serializers.opsSerializers.MarketplaceOrder") as orders, \
                patch("serializers.opsSerializers.RefundRecord") as refunds, \
                patch("serializers.opsSerializers.SellerPayout") as payouts:
            orders.query.filter_by.return_value.all.return_value = []
            refunds.query.filter.return_value.all.return_value = []
            payouts.query.filter.return_value.all.return_value = []

            serializer = OpsSerializer()
            summary = serializer.summary()

            self.assertEqual(summary["counts"]["failed_payments"], 0)
            self.assertEqual(summary["counts"]["stuck_refunds"], 0)
            self.assertEqual(summary["counts"]["open_payouts"], 0)


if __name__ == "__main__":
    unittest.main()
