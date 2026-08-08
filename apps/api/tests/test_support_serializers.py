import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.supportSerializers import SupportInputError, SupportSerializer


class SupportSerializerTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_create_ticket_records_authenticated_user(self):
        user = MagicMock()
        user.id = 7
        user.uuid = "user::buyer"
        user.user_type = "customer"

        with patch("serializers.supportSerializers.g", new=SimpleNamespace(user=user)), \
                patch("serializers.supportSerializers.SupportTicket") as ticket_model, \
                patch("serializers.supportSerializers.db") as db_mock:
            ticket = MagicMock()
            ticket.uuid = "ticket::1"
            ticket.created_by = user
            ticket.subject = "Help"
            ticket.message = "Need assistance"
            ticket.status = "open"
            ticket.resolution = None
            ticket.resolved_by = None
            ticket.resolved_at = None
            ticket.created_on = MagicMock()
            ticket.modified_on = MagicMock()
            db_mock.session.add = MagicMock()
            db_mock.session.commit = MagicMock()
            ticket_model.return_value = ticket

            serializer = SupportSerializer()
            result = serializer.create_ticket({"subject": "Help", "message": "Need assistance"})

            self.assertIs(result, ticket)
            ticket_model.assert_called_once()
            self.assertEqual(ticket_model.call_args.kwargs["created_by_id"], user.id)
            db_mock.session.commit.assert_called()

    def test_admin_can_suspend_user(self):
        admin = MagicMock()
        admin.id = 1
        admin.user_type = "admin"

        target = MagicMock()
        target.uuid = "user::suspended"
        target.is_active = "true"

        with patch("serializers.supportSerializers.g", new=SimpleNamespace(user=admin)), \
                patch("serializers.supportSerializers.User") as user_model, \
                patch("serializers.supportSerializers.db") as db_mock:
            user_model.query.filter_by.return_value.first.return_value = target
            db_mock.session.commit = MagicMock()

            serializer = SupportSerializer()
            result = serializer.set_user_active_state("user::suspended", False)

            self.assertIs(result, target)
            self.assertEqual(target.is_active, "false")
            db_mock.session.commit.assert_called()

    def test_non_admin_cannot_suspend_user(self):
        user = MagicMock()
        user.id = 2
        user.user_type = "seller"

        with patch("serializers.supportSerializers.g", new=SimpleNamespace(user=user)):
            serializer = SupportSerializer()
            with self.assertRaises(SupportInputError):
                serializer.set_user_active_state("user::suspended", False)


if __name__ == "__main__":
    unittest.main()
