import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from flask import Flask
import jwt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from utils.auth import AuthError, require_auth, verify_delivery_token
from serializers.userSerializers import IndefiniteUserProfileData, UserSerializer


class AuthTests(unittest.TestCase):
    def test_delivery_token_verification_requires_delivery_claims(self):
        with patch("utils.auth._get_public_key", return_value="public-key"), \
                patch("utils.auth.jwt.decode", return_value={"sub": "user::1"}) as decode:
            result = verify_delivery_token("signed-token")

        self.assertEqual(result["sub"], "user::1")
        self.assertEqual(decode.call_args.kwargs["algorithms"], ["EdDSA"])
        self.assertEqual(
            decode.call_args.kwargs["options"]["require"],
            ["jti", "sub", "asset_uuid", "order_uuid", "download_url", "exp", "iat"],
        )

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
