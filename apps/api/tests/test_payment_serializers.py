import os
import sys
import hashlib
import hmac
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.paymentSerializers import PaymentSerializer
from services.razorpay_gateway import RazorpayGateway


class FakeQueryResult:
    def __init__(self, value):
        self._value = value

    def first(self):
        return self._value


class FakeQuery:
    def __init__(self, value):
        self._value = value

    def filter_by(self, **kwargs):
        return FakeQueryResult(self._value)


class PaymentGatewayTests(unittest.TestCase):
    def test_verify_checkout_signature_matches_expected_hmac(self):
        with patch("services.razorpay_gateway.RAZORPAY_KEY_SECRET", "secret_key"):
            gateway = RazorpayGateway()
            order_id = "order_test_123"
            payment_id = "pay_test_456"
            signature = hmac.new(
                b"secret_key",
                f"{order_id}|{payment_id}".encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            self.assertTrue(gateway.verify_checkout_signature(order_id, payment_id, signature))

    def test_verify_checkout_signature_rejects_tampered_signature(self):
        with patch("services.razorpay_gateway.RAZORPAY_KEY_SECRET", "secret_key"):
            gateway = RazorpayGateway()

            self.assertFalse(
                gateway.verify_checkout_signature(
                    "order_test_123",
                    "pay_test_456",
                    "bad_signature",
                )
            )


class PaymentWebhookIdempotencyTests(unittest.TestCase):
    def test_process_webhook_event_is_idempotent_for_paid_order(self):
        order = MagicMock()
        order.id = 1
        order.uuid = "order::abc"
        order.provider_order_id = "order_razorpay_123"
        order.provider_payment_id = "pay_razorpay_123"
        order.payment_status = "paid"
        order.delivery_status = "ready"
        order.provider = "razorpay"
        order.seller_id = 10
        order.seller.uuid = "user::seller"
        order.buyer.uuid = "user::buyer"
        order.product.uuid = "product::1"
        order.product.currency = "INR"
        order.product_access_records.all.return_value = []

        with patch("serializers.paymentSerializers.MarketplaceOrder") as marketplace_order, \
                patch("serializers.paymentSerializers.db") as db_mock, \
                patch.object(PaymentSerializer, "_grant_access_if_needed") as grant_access, \
                patch.object(RazorpayGateway, "verify_webhook_signature") as verify_signature:
            marketplace_order.query.filter_by.return_value.first.return_value = order
            verify_signature.return_value = True
            db_mock.session.commit = MagicMock()

            serializer = PaymentSerializer()
            payload = {
                "event": "payment.captured",
                "payload": {
                    "payment": {
                        "entity": {
                            "order_id": "order_razorpay_123",
                            "id": "pay_razorpay_123",
                        }
                    }
                },
                "x_razorpay_signature": "valid_signature",
            }

            first = serializer.process_webhook_event(payload, b"{}")
            second = serializer.process_webhook_event(payload, b"{}")

            self.assertIs(first, order)
            self.assertIs(second, order)
            grant_access.assert_not_called()
            self.assertEqual(verify_signature.call_count, 2)
            db_mock.session.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
