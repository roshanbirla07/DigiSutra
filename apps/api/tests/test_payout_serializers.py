import os
import sys
import unittest
from flask import Flask
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.payoutSerializers import PayoutInputError, PayoutSerializer


class PayoutSerializerTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

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
        payout.amount = "100.00"
        payout.status = "pending"
        payout.payout_method = "manual"
        payout.batch_id = None
        payout.failure_reason = None
        profile = MagicMock()
        profile.is_suspended = False
        profile.payout_hold = False
        profile.kyc_status = "verified"
        profile.fund_account_status = "validated"
        profile.payout_ready = True

        with patch("serializers.payoutSerializers.User") as user_model, \
                patch("serializers.payoutSerializers.SellerBalance") as seller_balance_model, \
                patch("serializers.payoutSerializers.SellerProfile") as seller_profile_model, \
                patch("serializers.payoutSerializers.SellerPayout") as seller_payout_model, \
                patch("serializers.payoutSerializers.db") as db_mock:
            user_model.query.filter_by.return_value.first.return_value = seller
            seller_profile_model.query.filter_by.return_value.first.return_value = profile
            seller_balance_model.query.filter_by.return_value.with_for_update.return_value.first.return_value = seller_balance
            db_mock.session.add = MagicMock()
            db_mock.session.commit = MagicMock()
            seller_payout_model.return_value = payout

            serializer = PayoutSerializer()
            result = serializer.create({"seller_uuid": seller.uuid, "amount": "100.00"})

            self.assertIsNotNone(result)
            self.assertEqual(seller_balance.available_for_payout, 150)
            self.assertEqual(seller_balance.pending_payout, 100)
            self.assertEqual(payout.status, "pending")
            self.assertEqual(payout.payout_method, "manual")
            db_mock.session.commit.assert_called()

    def test_create_payout_ignores_client_controlled_state(self):
        seller = MagicMock(id=7, uuid="seller::1", username="seller1", user_type="seller")
        seller_balance = MagicMock(available_for_payout=250, pending_payout=0, currency="INR")
        profile = MagicMock(
            is_suspended=False,
            payout_hold=False,
            kyc_status="verified",
            fund_account_status="validated",
            payout_ready=True,
        )
        payout = MagicMock(amount="100.00")

        with patch("serializers.payoutSerializers.User") as user_model, \
                patch("serializers.payoutSerializers.SellerBalance") as seller_balance_model, \
                patch("serializers.payoutSerializers.SellerProfile") as seller_profile_model, \
                patch("serializers.payoutSerializers.SellerPayout", return_value=payout) as payout_model, \
                patch("serializers.payoutSerializers.db") as db_mock:
            user_model.query.filter_by.return_value.first.return_value = seller
            seller_profile_model.query.filter_by.return_value.first.return_value = profile
            seller_balance_model.query.filter_by.return_value.with_for_update.return_value.first.return_value = seller_balance

            PayoutSerializer().create({
                "seller_uuid": seller.uuid,
                "amount": "100.00",
                "status": "paid",
                "payout_method": "bank_transfer",
                "batch_id": "attacker-controlled",
            })

            created = payout_model.call_args.kwargs
            self.assertEqual(created["status"], "pending")
            self.assertEqual(created["payout_method"], "manual")
            self.assertIsNone(created["batch_id"])
            self.assertIsNone(created["processed_at"])

    def test_create_payout_rejects_amount_above_available_balance(self):
        seller = MagicMock()
        seller.id = 7
        seller.uuid = "seller::1"
        seller.user_type = "seller"

        seller_balance = MagicMock()
        seller_balance.available_for_payout = 25
        seller_balance.pending_payout = 0

        with patch("serializers.payoutSerializers.User") as user_model, \
                patch("serializers.payoutSerializers.SellerBalance") as seller_balance_model, \
                patch("serializers.payoutSerializers.SellerProfile") as seller_profile_model:
            user_model.query.filter_by.return_value.first.return_value = seller
            seller_balance_model.query.filter_by.return_value.with_for_update.return_value.first.return_value = seller_balance
            seller_profile_model.query.filter_by.return_value.first.return_value = None

            serializer = PayoutSerializer()
            with self.assertRaises(PayoutInputError):
                serializer.validate_create_data({"seller_uuid": seller.uuid, "amount": "100.00"})

    def test_validate_status_transition_allows_only_supported_moves(self):
        serializer = PayoutSerializer()

        self.assertEqual(serializer.validate_status_transition("pending", "processing"), "processing")
        self.assertEqual(serializer.validate_status_transition("processing", "paid"), "paid")
        self.assertEqual(serializer.validate_status_transition("processing", "failed"), "failed")
        self.assertEqual(serializer.validate_status_transition("failed", "processing"), "processing")

        with self.assertRaises(PayoutInputError):
            serializer.validate_status_transition("pending", "paid")

        with self.assertRaises(PayoutInputError):
            serializer.validate_status_transition("paid", "processing")

    def test_transition_payout_updates_terminal_metadata(self):
        payout = MagicMock()
        payout.status = "processing"
        payout.failure_reason = None
        payout.processed_at = None

        serializer = PayoutSerializer()
        serializer.transition_payout(payout, "paid")
        self.assertEqual(payout.status, "paid")
        self.assertIsNotNone(payout.processed_at)
        self.assertIsNone(payout.failure_reason)

        payout.status = "processing"
        payout.failure_reason = None
        payout.processed_at = None
        serializer.transition_payout(payout, "failed", failure_reason="bank rejected")
        self.assertEqual(payout.status, "failed")
        self.assertEqual(payout.failure_reason, "bank rejected")
        self.assertIsNotNone(payout.processed_at)

    def test_process_batch_transitions_multiple_payouts(self):
        payout_one = MagicMock()
        payout_one.uuid = "payout::1"
        payout_one.status = "pending"
        payout_one.batch_id = None
        payout_one.seller_id = 7
        payout_one.amount = 25
        payout_one.failure_reason = None
        payout_one.processed_at = None

        payout_two = MagicMock()
        payout_two.uuid = "payout::2"
        payout_two.status = "processing"
        payout_two.batch_id = None
        payout_two.seller_id = 8
        payout_two.amount = 10
        payout_two.failure_reason = None
        payout_two.processed_at = None

        balance = MagicMock(pending_payout=25)
        with patch.object(PayoutSerializer, "get_payout_by_uuid_for_update") as get_payout, \
                patch("serializers.payoutSerializers.SellerBalance") as balance_model, \
                patch("serializers.payoutSerializers.db") as db_mock:
            get_payout.side_effect = [payout_one, payout_two]
            balance_model.query.filter_by.return_value.with_for_update.return_value.first.return_value = balance
            db_mock.session.commit = MagicMock()

            serializer = PayoutSerializer()
            result = serializer.process_batch(
                "batch::1",
                [
                    {"payout_uuid": "payout::1", "status": "paid"},
                    {"payout_uuid": "payout::2", "status": "failed", "failure_reason": "bank rejected"},
                ],
            )

            self.assertEqual(len(result), 2)
            self.assertEqual(payout_one.batch_id, "batch::1")
            self.assertEqual(payout_one.status, "paid")
            self.assertEqual(payout_two.batch_id, "batch::1")
            self.assertEqual(payout_two.status, "failed")
            self.assertEqual(payout_two.failure_reason, "bank rejected")
            self.assertEqual(balance.pending_payout, 0)
            db_mock.session.commit.assert_called()

    def test_process_batch_rejects_invalid_final_status(self):
        payout = MagicMock()
        payout.uuid = "payout::1"
        payout.status = "pending"
        payout.batch_id = None

        with patch.object(PayoutSerializer, "get_payout_by_uuid_for_update", return_value=payout):
            serializer = PayoutSerializer()
            with self.assertRaises(PayoutInputError):
                serializer.process_batch("batch::1", [{"payout_uuid": "payout::1", "status": "cancelled"}])

    def test_retry_payout_moves_failed_payout_back_to_processing(self):
        payout = MagicMock()
        payout.uuid = "payout::retry"
        payout.status = "failed"
        payout.failure_reason = "bank rejected"
        payout.processed_at = None

        with patch.object(PayoutSerializer, "get_payout_by_uuid", return_value=payout), \
                patch("serializers.payoutSerializers.db") as db_mock:
            db_mock.session.commit = MagicMock()
            serializer = PayoutSerializer()
            result = serializer.retry_payout("payout::retry")

            self.assertIs(result, payout)
            self.assertEqual(payout.status, "processing")
            self.assertIsNone(payout.failure_reason)
            db_mock.session.commit.assert_called()

    def test_retry_payout_rejects_non_failed_payout(self):
        payout = MagicMock()
        payout.uuid = "payout::retry"
        payout.status = "paid"

        with patch.object(PayoutSerializer, "get_payout_by_uuid", return_value=payout):
            serializer = PayoutSerializer()
            with self.assertRaises(PayoutInputError):
                serializer.retry_payout("payout::retry")

    def test_cancel_payout_restores_reserved_balance(self):
        actor = MagicMock(id=7, user_type="seller")
        payout = MagicMock(seller_id=7, status="pending", amount="100.00")
        balance = MagicMock(available_for_payout=150, pending_payout=100)

        with patch.object(PayoutSerializer, "get_payout_by_uuid_for_update", return_value=payout), \
                patch("serializers.payoutSerializers.SellerBalance") as balance_model, \
                patch("serializers.payoutSerializers.db") as db_mock:
            balance_model.query.filter_by.return_value.with_for_update.return_value.first.return_value = balance
            result = PayoutSerializer().cancel_payout("payout::1", actor)

            self.assertIs(result, payout)
            self.assertEqual(payout.status, "cancelled")
            self.assertEqual(balance.available_for_payout, 250)
            self.assertEqual(balance.pending_payout, 0)
            db_mock.session.commit.assert_called_once()

    def test_cancel_payout_rejects_non_owner(self):
        actor = MagicMock(id=8, user_type="seller")
        payout = MagicMock(seller_id=7, status="pending", amount="100.00")
        with patch.object(PayoutSerializer, "get_payout_by_uuid_for_update", return_value=payout):
            with self.assertRaises(PayoutInputError):
                PayoutSerializer().cancel_payout("payout::1", actor)

    def test_reconciliation_summary_groups_failed_and_open_payouts(self):
        failed = MagicMock()
        failed.uuid = "payout::failed"
        failed.status = "failed"
        failed.seller = MagicMock()
        failed.seller.uuid = "seller::1"
        failed.amount = 25
        failed.failure_reason = "bank rejected"
        failed.processed_at = None
        failed.created_on = None
        failed.modified_on = None

        open_payout = MagicMock()
        open_payout.uuid = "payout::open"
        open_payout.status = "processing"
        open_payout.seller = MagicMock()
        open_payout.seller.uuid = "seller::2"
        open_payout.amount = 10
        open_payout.failure_reason = None
        open_payout.processed_at = None
        open_payout.created_on = None
        open_payout.modified_on = None

        paid = MagicMock()
        paid.uuid = "payout::paid"
        paid.status = "paid"
        paid.seller = MagicMock()
        paid.seller.uuid = "seller::3"
        paid.amount = 15
        paid.failure_reason = None
        paid.processed_at = None
        paid.created_on = None
        paid.modified_on = None

        with patch("serializers.payoutSerializers.SellerPayout") as seller_payout_model:
            seller_payout_model.query.filter_by.return_value.all.side_effect = [[failed], [paid]]
            seller_payout_model.query.filter.return_value.all.return_value = [open_payout]

            serializer = PayoutSerializer()
            summary = serializer.reconciliation_summary()

            self.assertEqual(summary["counts"]["failed_payouts"], 1)
            self.assertEqual(summary["counts"]["open_payouts"], 1)
            self.assertEqual(summary["counts"]["paid_payouts"], 1)


if __name__ == "__main__":
    unittest.main()
