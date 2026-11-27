import os
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from configuration.db_routing import db
from controllers.user import GoogleLogin
from models.user import User
from utils.auth import AuthError
from utils.google_auth import google_client_id, google_user, verify_google_token


class GoogleAuthTests(unittest.TestCase):
    def test_client_id_configuration_name(self):
        with patch("utils.google_auth.variables.CLIENT_ID", "configured-client", create=True):
            self.assertEqual(google_client_id(), "configured-client")

    @classmethod
    def setUpClass(cls):
        cls.key = generate_private_key(public_exponent=65537, key_size=2048)

    def test_token_checks_signature_audience_issuer_expiry_and_verified_email(self):
        claims = dict(sub="123456", email="buyer@gmail.com", email_verified=True,
                      iss="https://accounts.google.com", aud="client-id",
                      iat=int(time.time()), exp=int(time.time()) + 300)
        cases = [{}, {"aud": "other-client"}, {"iss": "https://attacker.example"},
                 {"exp": int(time.time()) - 1}, {"email_verified": False}, {"sub": ""}]
        with patch("utils.google_auth.google_client_id", return_value="client-id"), \
                patch("utils.google_auth.google_keys.get_signing_key_from_jwt",
                      return_value=SimpleNamespace(key=self.key.public_key())):
            for changes in cases:
                token = jwt.encode({**claims, **changes}, self.key, algorithm="RS256")
                with self.subTest(changes=changes):
                    if changes:
                        with self.assertRaises(AuthError):
                            verify_google_token(token)
                    else:
                        self.assertEqual(verify_google_token(token)["sub"], "123456")
            other_key = generate_private_key(public_exponent=65537, key_size=2048)
            with self.assertRaises(AuthError):
                verify_google_token(jwt.encode(claims, other_key, algorithm="RS256"))
            with self.assertRaises(AuthError):
                verify_google_token(jwt.encode({k: v for k, v in claims.items() if k != "exp"},
                                              self.key, algorithm="RS256"))

    def test_create_returning_inactive_and_existing_password_accounts(self):
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.init_app(app)
        claims = {"sub": "123456", "email": "buyer@gmail.com", "given_name": "Buyer"}
        with app.app_context():
            User.__table__.create(db.engine)
            user = google_user(claims)
            self.assertEqual(user.user_type, "customer")
            self.assertEqual(google_user({**claims, "email": "changed@gmail.com"}).id, user.id)
            self.assertEqual(User.query.count(), 1)
            user.is_active = "false"
            db.session.commit()
            with self.assertRaises(AuthError):
                google_user(claims)
            with self.assertRaises(AuthError):
                google_user({**claims, "sub": "987654"})

    def test_endpoint_configuration_input_and_session_response(self):
        app = Flask(__name__)
        app.add_url_rule("/google", view_func=GoogleLogin.as_view("google"))
        client = app.test_client()
        with patch("controllers.user.google_client_id", return_value=""):
            self.assertEqual(client.get("/google").json, {"client_id": ""})
            self.assertEqual(client.post("/google", json={}).status_code, 503)
        with patch("controllers.user.google_client_id", return_value="client-id"):
            for data in [{}, [], {"credential": 42}]:
                self.assertEqual(client.post("/google", json=data).status_code, 400)
            with patch("controllers.user.verify_google_token", side_effect=AuthError("Invalid credential")):
                self.assertEqual(client.post("/google", json={"credential": "invalid"}).status_code, 401)
            user = SimpleNamespace(uuid="google::123", username="buyer", email="buyer@gmail.com",
                                   first_name="Buyer", last_name="", phone_number=None,
                                   user_type="customer", is_active="true", created_on=None, modified_on=None)
            with patch("controllers.user.verify_google_token", return_value={}), \
                    patch("controllers.user.google_user", return_value=user), \
                    patch("controllers.user.create_access_token", return_value="app-token"):
                response = client.post("/google", json={"credential": "google-token"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json["token"], "app-token")
                self.assertEqual(response.json["uuid"], "google::123")
