import os
import sys
import unittest
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from configuration.db_routing import db
from controllers.user import GoogleLink, GoogleLogin
from models.user import User
from services.google_identity import GoogleIdentityError, sign_in_with_google, verify_google_credential


class GoogleSignInTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        db.init_app(self.app)
        self.app.add_url_rule("/google/login/", view_func=GoogleLogin.as_view("google_login"))
        self.app.add_url_rule("/google/link/", view_func=GoogleLink.as_view("google_link"))
        self.context = self.app.app_context()
        self.context.push()
        User.__table__.create(db.engine)
        self.identity = {"sub": "google-123", "email": "buyer@example.com", "first_name": "Buyer", "last_name": "One"}

    def tearDown(self):
        db.session.remove()
        User.__table__.drop(db.engine)
        self.context.pop()

    def test_rejects_unverified_and_wrong_audience_tokens(self):
        with patch("services.google_identity.GOOGLE_CLIENT_ID", "client-id"), \
                patch("services.google_identity.id_token.verify_oauth2_token", return_value={"sub": "123", "email": "x@example.com", "email_verified": False}) as verifier:
            with self.assertRaises(GoogleIdentityError):
                verify_google_credential("credential")
            self.assertEqual(verifier.call_args.args[2], "client-id")
        with patch("services.google_identity.GOOGLE_CLIENT_ID", "client-id"), \
                patch("services.google_identity.id_token.verify_oauth2_token", side_effect=ValueError("wrong audience")):
            with self.assertRaises(GoogleIdentityError):
                verify_google_credential("credential")

    def test_new_customer_and_existing_email_not_automatically_linked(self):
        user = sign_in_with_google(self.identity)
        self.assertEqual(user.user_type, "customer")
        self.assertEqual(sign_in_with_google(self.identity).id, user.id)
        with self.assertRaisesRegex(GoogleIdentityError, "link Google"):
            sign_in_with_google({**self.identity, "sub": "another-google-id"})
        self.assertEqual(User.query.count(), 1)

    def test_password_account_can_link_and_then_sign_in_without_role_change(self):
        admin = User(uuid="user::admin", username="admin", password="hash", email="buyer@example.com", first_name="Admin", user_type="admin")
        db.session.add(admin)
        db.session.commit()
        with patch("controllers.user.verify_google_credential", return_value=self.identity), \
                patch("utils.auth.verify_access_token", return_value=(admin, {})):
            response = self.app.test_client().post("/google/link/", json={"credential": "valid"}, headers={"Authorization": "Bearer existing-token"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sign_in_with_google(self.identity).id, admin.id)
        self.assertEqual(admin.user_type, "admin")

    def test_google_login_returns_regular_session(self):
        with patch("controllers.user.verify_google_credential", return_value=self.identity), \
                patch("controllers.user.create_access_token", return_value="signed"):
            response = self.app.test_client().post("/google/login/", json={"credential": "valid"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["token"], "signed")
        self.assertTrue(response.json["google_linked"])
        self.assertEqual(response.json["user_type"], "customer")


if __name__ == "__main__":
    unittest.main()
