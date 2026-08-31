import os
import sys
import unittest
from decimal import Decimal
from unittest.mock import patch

from flask import Flask, g

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from configuration.db_routing import db
from models.ledger import SellerBalance
from models.product import Product
from models.user import User
from serializers.ledgerSerializers import LedgerInputError, LedgerSerializer


class OrderIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

        self.buyer = User(
            uuid="user::buyer",
            username="buyer",
            password="hash",
            email="buyer@example.com",
            first_name="Buyer",
            user_type="customer",
            is_active="true",
        )
        self.seller = User(
            uuid="user::seller",
            username="seller",
            password="hash",
            email="seller@example.com",
            first_name="Seller",
            user_type="seller",
            is_active="true",
        )
        db.session.add_all([self.buyer, self.seller])
        db.session.flush()
        self.product = Product(
            uuid="product::premium",
            owner_id=self.seller.id,
            title="Premium guide",
            price=Decimal("1000.00"),
            currency="INR",
            is_active=True,
            is_public=True,
        )
        db.session.add(self.product)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_order_uses_server_price_fee_owner_and_initial_state(self):
        with self.app.test_request_context("/v1/ledger/orders/"):
            g.user = self.buyer
            with patch("serializers.ledgerSerializers.PLATFORM_FEE_PERCENT", "10"):
                order = LedgerSerializer({
                    "product_uuid": self.product.uuid,
                    "buyer_uuid": "user::attacker-selected-buyer",
                    "seller_uuid": "user::attacker-selected-seller",
                    "gross_amount": "1.00",
                    "platform_fee": "0.00",
                    "payment_status": "paid",
                    "delivery_status": "ready",
                    "provider_payment_id": "fake-payment",
                }).create()

        self.assertEqual(order.buyer_id, self.buyer.id)
        self.assertEqual(order.seller_id, self.seller.id)
        self.assertEqual(order.gross_amount, Decimal("1000.00"))
        self.assertEqual(order.platform_fee, Decimal("100.00"))
        self.assertEqual(order.net_seller_amount, Decimal("900.00"))
        self.assertEqual(order.payment_status, "pending")
        self.assertEqual(order.delivery_status, "pending")
        self.assertIsNone(order.provider_payment_id)
        self.assertIsNone(SellerBalance.query.filter_by(seller_id=self.seller.id).first())

    def test_order_rejects_non_positive_product_price(self):
        self.product.price = Decimal("0.00")
        db.session.commit()
        with self.app.test_request_context("/v1/ledger/orders/"):
            g.user = self.buyer
            with self.assertRaises(LedgerInputError):
                LedgerSerializer({"product_uuid": self.product.uuid}).create()


if __name__ == "__main__":
    unittest.main()
