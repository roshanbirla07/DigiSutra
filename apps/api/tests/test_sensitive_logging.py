import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from v1.routers.routes import v1


class SensitiveLoggingTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(v1)
        self.client = app.test_client()

    def test_login_failure_does_not_log_or_return_password(self):
        marker = "synthetic-password-marker"
        with patch("controllers.user.UserSerializer") as serializer, \
                patch("controllers.user.logging.error") as logger:
            serializer.return_value.login_with_token.side_effect = ValueError(marker)
            response = self.client.post("/v1/users/login/", json={"username": "buyer", "password": marker})
        self.assertEqual(response.status_code, 400)
        logger.assert_called_once()
        self.assertNotIn(marker, str(logger.call_args_list))
        self.assertNotIn(marker, response.get_data(as_text=True))

    def test_payment_failure_does_not_log_or_return_signature(self):
        marker = "synthetic-signature-marker"
        user = SimpleNamespace(uuid="user::1", user_type="customer")
        with patch("utils.auth.verify_access_token", return_value=(user, {})), \
                patch("controllers.payment.PaymentSerializer") as serializer, \
                patch("controllers.payment.logging.error") as logger:
            serializer.return_value.confirm_checkout_payment.side_effect = ValueError(marker)
            response = self.client.post("/v1/payments/confirm/", json={
                "razorpay_payment_id": "pay_1",
                "razorpay_order_id": "order_1", "razorpay_signature": marker,
            }, headers={"Authorization": "Bearer access-token"})
        self.assertEqual(response.status_code, 400)
        logger.assert_called_once()
        self.assertNotIn(marker, str(logger.call_args_list))
        self.assertNotIn(marker, response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
