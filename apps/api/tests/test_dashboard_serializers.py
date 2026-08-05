import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.dashboardSerializers import DashboardSerializer


class DashboardSerializerTests(unittest.TestCase):
    def test_seller_summary_returns_aggregates(self):
        with patch("serializers.dashboardSerializers.MarketplaceOrder") as orders, \
                patch("serializers.dashboardSerializers.RefundRecord") as refunds, \
                patch("serializers.dashboardSerializers.SellerBalance") as balances, \
                patch("serializers.dashboardSerializers.Product") as products, \
                patch("serializers.dashboardSerializers.SellerPayout") as payouts:
            orders.query.filter_by.return_value.count.side_effect = [2, 1, 1]
            orders.query.filter_by.return_value.with_entities.return_value.scalar.return_value = 100
            refunds.query.join.return_value.filter.return_value.with_entities.return_value.scalar.return_value = 15
            refunds.query.join.return_value.filter.return_value.count.return_value = 1
            balances.query.filter_by.return_value.first.return_value = None
            products.query.filter_by.return_value.count.return_value = 3
            payouts.query.filter_by.return_value.count.return_value = 1
            payouts.query.filter_by.return_value.with_entities.return_value.scalar.return_value = 20

            serializer = DashboardSerializer()
            summary = serializer.seller_summary(7)

            self.assertEqual(summary["orders_count"], 2)
            self.assertEqual(summary["products_count"], 3)


if __name__ == "__main__":
    unittest.main()
