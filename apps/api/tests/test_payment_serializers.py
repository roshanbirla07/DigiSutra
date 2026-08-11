import os
import sys
import hashlib
import hmac
import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.paymentSerializers import PaymentInputError, PaymentSerializer
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
        with patch("services.razorpay_gateway.RAZORPAY_TEST_KEY_SECRET", "secret_key"):
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
        with patch("services.razorpay_gateway.RAZORPAY_TEST_KEY_SECRET", "secret_key"):
            gateway = RazorpayGateway()

            self.assertFalse(
                gateway.verify_checkout_signature(
                    "order_test_123",
                    "pay_test_456",
                    "bad_signature",
                )
            )


class PaymentWebhookIdempotencyTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_process_webhook_event_rejects_replayed_paid_order_event(self):
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
                patch("serializers.paymentSerializers.PaymentWebhookEvent") as webhook_event, \
                patch("serializers.paymentSerializers.db") as db_mock, \
                patch.object(PaymentSerializer, "_grant_access_if_needed") as grant_access, \
                patch.object(RazorpayGateway, "verify_webhook_signature") as verify_signature:
            marketplace_order.query.filter_by.return_value.first.return_value = order
            webhook_event.query.filter_by.return_value.first.side_effect = [None, MagicMock()]
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
            with self.assertRaises(PaymentInputError):
                serializer.process_webhook_event(payload, b"{}")

            self.assertIs(first, order)
            grant_access.assert_not_called()
            self.assertEqual(verify_signature.call_count, 2)
            db_mock.session.commit.assert_called_once()

    def test_refund_processed_webhook_finalizes_order_access_and_balance(self):
        order = MagicMock()
        order.id = 1
        order.uuid = "order::abc"
        order.provider_payment_id = "pay_razorpay_123"
        order.payment_status = "paid"
        order.delivery_status = "ready"
        order.refund_status = "approved"
        order.seller_id = 10
        order.product.currency = "INR"
        access_record = MagicMock()
        order.product_access_records.all.return_value = [access_record]

        refund = MagicMock()
        refund.status = "approved"
        refund.amount = "25.00"

        seller_balance = MagicMock()
        seller_balance.pending_payout = 10
        seller_balance.available_for_payout = 100
        seller_balance.currency = "INR"

        with patch("serializers.paymentSerializers.MarketplaceOrder") as marketplace_order, \
                patch("serializers.paymentSerializers.RefundRecord") as refund_record, \
                patch("serializers.paymentSerializers.PaymentWebhookEvent") as webhook_event, \
                patch("serializers.paymentSerializers.SellerBalance") as seller_balance_model, \
                patch("serializers.paymentSerializers.db") as db_mock, \
                patch.object(RazorpayGateway, "verify_webhook_signature", return_value=True):
            marketplace_order.query.filter_by.return_value.first.return_value = order
            refund_record.query.filter_by.return_value.first.return_value = refund
            webhook_event.query.filter_by.return_value.first.return_value = None
            seller_balance_model.query.filter_by.return_value.first.return_value = seller_balance

            payload = {
                "event": "refund.processed",
                "payload": {
                    "refund": {
                        "entity": {
                            "id": "rfnd_123",
                            "payment_id": "pay_razorpay_123",
                            "status": "processed",
                        }
                    }
                },
                "x_razorpay_signature": "valid_signature",
            }

            result = PaymentSerializer().process_webhook_event(payload, b"{}")

            self.assertIs(result, order)
            self.assertEqual(refund.provider_refund_id, "rfnd_123")
            self.assertEqual(refund.provider_status, "processed")
            self.assertEqual(refund.status, "processed")
            self.assertEqual(order.payment_status, "refunded")
            self.assertEqual(order.delivery_status, "revoked")
            self.assertEqual(order.refund_status, "processed")
            self.assertEqual(access_record.access_status, "revoked")
            self.assertEqual(seller_balance.pending_payout, 0)
            self.assertEqual(seller_balance.available_for_payout, 85)
            self.assertTrue(db_mock.session.commit.called)


class LedgerRefundTransitionTests(unittest.TestCase):
    def test_create_refund_processed_updates_order_and_access(self):
        order = MagicMock()
        order.id = 1
        order.uuid = "order::abc"
        order.payment_status = "paid"
        order.delivery_status = "ready"
        order.refund_status = "none"
        order.gross_amount = "100.00"
        order.net_seller_amount = "85.00"
        order.seller = MagicMock()
        order.seller.id = 10
        order.seller.uuid = "user::seller"
        order.product = MagicMock()
        order.product.currency = "INR"
        access_record = MagicMock()
        order.product_access_records.all.return_value = [access_record]

        with patch("serializers.ledgerSerializers.MarketplaceOrder") as marketplace_order, \
                patch("serializers.ledgerSerializers.RefundRecord") as refund_record, \
                patch("serializers.ledgerSerializers.SellerBalance") as seller_balance_model, \
                patch("serializers.ledgerSerializers.db") as db_mock:
            marketplace_order.query.filter_by.return_value.first.return_value = order
            refund_record.query.filter_by.return_value.first.return_value = None
            seller_balance = MagicMock()
            seller_balance.pending_payout = 85
            seller_balance.available_for_payout = 10
            seller_balance.currency = "INR"
            seller_balance_model.query.filter_by.return_value.first.return_value = seller_balance
            db_mock.session.add = MagicMock()
            db_mock.session.commit = MagicMock()

            from serializers.ledgerSerializers import LedgerSerializer

            ledger = LedgerSerializer()
            result = ledger.create_refund("order::abc", {"status": "processed", "amount": "25.00"})

            self.assertIsNotNone(result)
            self.assertEqual(order.payment_status, "refunded")
            self.assertEqual(order.delivery_status, "revoked")
            self.assertEqual(order.refund_status, "processed")
            self.assertEqual(access_record.access_status, "revoked")
            self.assertEqual(seller_balance.pending_payout, 60)
            self.assertEqual(seller_balance.available_for_payout, 10)
            self.assertTrue(db_mock.session.commit.called)

    def test_create_razorpay_refund_waits_for_provider_processed_status(self):
        order = MagicMock()
        order.id = 1
        order.uuid = "order::abc"
        order.provider = "razorpay"
        order.provider_payment_id = "pay_razorpay_123"
        order.payment_status = "paid"
        order.delivery_status = "ready"
        order.refund_status = "none"
        order.gross_amount = "100.00"
        order.net_seller_amount = "85.00"
        order.seller = MagicMock()
        order.seller.id = 10
        order.product = MagicMock()
        order.product.currency = "INR"
        order.product_access_records.all.return_value = []

        with patch("serializers.ledgerSerializers.MarketplaceOrder") as marketplace_order, \
                patch("serializers.ledgerSerializers.RefundRecord") as refund_record, \
                patch("serializers.ledgerSerializers.db") as db_mock, \
                patch("serializers.ledgerSerializers.RazorpayGateway") as gateway:
            marketplace_order.query.filter_by.return_value.first.return_value = order
            refund_record.query.filter_by.return_value.first.return_value = None
            gateway.return_value.create_refund.return_value = {
                "id": "rfnd_123",
                "status": "pending",
            }
            db_mock.session.add = MagicMock()
            db_mock.session.commit = MagicMock()

            from serializers.ledgerSerializers import LedgerSerializer

            ledger = LedgerSerializer()
            result = ledger.create_refund("order::abc", {"status": "processed", "amount": "25.00"})

            self.assertEqual(result.status, "approved")
            self.assertIsNone(result.resolved_on)
            self.assertEqual(result.provider_refund_id, "rfnd_123")
            self.assertEqual(result.provider_status, "pending")
            self.assertEqual(order.payment_status, "paid")
            self.assertEqual(order.delivery_status, "ready")
            self.assertEqual(order.refund_status, "approved")
            gateway.return_value.create_refund.assert_called_once()
            self.assertTrue(db_mock.session.commit.called)

    def test_create_refund_rejects_invalid_status(self):
        from serializers.ledgerSerializers import LedgerSerializer, LedgerInputError

        ledger = LedgerSerializer()
        with self.assertRaises(LedgerInputError):
            ledger._validate_order_state("pending", "pending", "bogus")


if __name__ == "__main__":
    unittest.main()
