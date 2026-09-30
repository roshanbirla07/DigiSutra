import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from flask import Flask
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import jwt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from utils.auth import AuthError, create_access_token, create_delivery_token, require_auth, verify_access_token, verify_delivery_token
from serializers.userSerializers import IndefiniteUserProfileData, UserSerializer


class AuthTests(unittest.TestCase):
    def test_delivery_token_verification_requires_delivery_claims(self):
        with patch("utils.auth._get_public_key", return_value="public-key"), \
                patch("utils.auth.jwt.decode", return_value={"sub": "user::1", "purpose": "delivery"}) as decode:
            result = verify_delivery_token("signed-token")

        self.assertEqual(result["sub"], "user::1")
        self.assertEqual(decode.call_args.kwargs["algorithms"], ["EdDSA"])
        self.assertEqual(
            decode.call_args.kwargs["options"]["require"],
            ["jti", "sub", "asset_uuid", "order_uuid", "download_url", "exp", "iat", "iss", "aud", "purpose"],
        )

    def test_signed_tokens_cannot_cross_authentication_boundaries(self):
        private_key = Ed25519PrivateKey.generate()
        private_pem = private_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        public_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        user = MagicMock(uuid="user::1", username="buyer", user_type="customer", is_active=True)
        with patch("utils.auth._get_private_key", return_value=private_pem), \
                patch("utils.auth._get_public_key", return_value=public_pem), \
                patch("utils.auth.User") as model:
            model.query.filter_by.return_value.first.return_value = user
            access = create_access_token(user)
            delivery = create_delivery_token(user.uuid, "asset::1", "order::1", "https://example.com/file")
            self.assertEqual(verify_access_token(access)[0], user)
            self.assertEqual(verify_delivery_token(delivery)["sub"], user.uuid)
            with self.assertRaises(jwt.PyJWTError):
                verify_access_token(delivery)
            with self.assertRaises(AuthError):
                verify_delivery_token(access)

    def test_delivery_token_verification_normalizes_expired_tokens(self):
        with patch("utils.auth._get_public_key", return_value="public-key"), \
                patch("utils.auth.jwt.decode", side_effect=jwt.ExpiredSignatureError("expired")):
            with self.assertRaises(AuthError):
                verify_delivery_token("expired-token")

    def test_require_auth_rejects_missing_bearer_token(self):
        app = Flask(__name__)

        @app.route("/protected")
        @require_auth(roles=["admin"], methods=["GET"])
        def protected():
            return {"ok": True}

        response = app.test_client().get("/protected")

        self.assertEqual(response.status_code, 401)

    def test_require_auth_rejects_disallowed_role(self):
        app = Flask(__name__)
        user = MagicMock(user_type="customer")

        @app.route("/protected")
        @require_auth(roles=["admin"], methods=["GET"])
        def protected():
            return {"ok": True}

        with patch("utils.auth.verify_access_token", return_value=(user, {})):
            response = app.test_client().get(
                "/protected", headers={"Authorization": "Bearer signed-token"}
            )

        self.assertEqual(response.status_code, 403)

    def test_login_rejects_inactive_user(self):
        inactive_user = MagicMock(is_active=False)

        with patch("serializers.userSerializers.User") as user_model, \
                patch("serializers.userSerializers.check_password_hash", return_value=True):
            user_model.query.filter.return_value.first.return_value = inactive_user

            with self.assertRaises(IndefiniteUserProfileData):
                UserSerializer({"username": "inactive", "password": "password"}).login()

    def test_user_creation_ignores_privileged_user_type(self):
        serializer = UserSerializer()

        prepared = serializer.prepare_create_data({
            "first_name": "New",
            "last_name": "Admin",
            "email": "new@example.com",
            "password": "password",
            "user_type": "admin",
        })

        self.assertEqual(prepared["user_type"], "customer")


if __name__ == "__main__":
    unittest.main()
