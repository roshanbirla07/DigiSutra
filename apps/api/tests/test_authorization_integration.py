import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from utils.auth import AuthError
from v1.routers.routes import v1


class AuthorizationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(v1)
        self.client = self.app.test_client()

    def test_protected_collection_requires_authentication(self):
        response = self.client.get("/v1/users/")

        self.assertEqual(response.status_code, 401)

    def test_all_protected_route_groups_require_authentication(self):
        protected_routes = [
            ("GET", "/v1/users/"),
            ("POST", "/v1/products/"),
            ("POST", "/v1/assets/upload-target/"),
            ("POST", "/v1/assets/asset::1/deliver/"),
            ("POST", "/v1/assets/asset::1/downloads/"),
            ("GET", "/v1/ledger/orders/"),
            ("GET", "/v1/ledger/purchases/"),
            ("GET", "/v1/ledger/orders/order::1/"),
            ("POST", "/v1/payments/orders/"),
            ("POST", "/v1/payments/confirm/"),
            ("GET", "/v1/payouts/"),
            ("POST", "/v1/payouts/"),
            ("POST", "/v1/payouts/batch/"),
            ("POST", "/v1/payouts/payout::1/retry/"),
            ("GET", "/v1/payouts/reconciliation-summary/"),
            ("GET", "/v1/dashboard/summary/"),
            ("GET", "/v1/ops/reconciliation-summary/"),
            ("GET", "/v1/support/tickets/"),
            ("POST", "/v1/support/tickets/"),
            ("POST", "/v1/support/tickets/ticket::1/resolve/"),
            ("POST", "/v1/moderation/products/product::1/flags/"),
            ("POST", "/v1/moderation/product-flags/flag::1/resolve/"),
            ("POST", "/v1/moderation/users/user::1/suspend/"),
            ("POST", "/v1/moderation/users/user::1/activate/"),
        ]

        for method, path in protected_routes:
            response = self.client.open(path, method=method)
            self.assertEqual(response.status_code, 401, f"{method} {path}")

    def test_protected_collection_rejects_non_admin(self):
        customer = SimpleNamespace(user_type="customer")

        with patch("utils.auth.verify_access_token", return_value=(customer, {})):
            response = self.client.get(
                "/v1/users/",
                headers={"Authorization": "Bearer customer-token"},
            )

        self.assertEqual(response.status_code, 403)

    def test_public_signup_cannot_assign_privileged_role(self):
        created_user = SimpleNamespace(uuid="user::customer")
        serializer = MagicMock()
        serializer.create.return_value = created_user

        with patch("controllers.user.UserSerializer", return_value=serializer) as serializer_factory:
            response = self.client.post(
                "/v1/users/",
                json={
                    "firstname": "New",
                    "lastname": "Seller",
                    "email": "new@example.com",
                    "password": "password",
                    "user_type": "admin",
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(serializer_factory.call_args.args[0]["user_type"], "customer")

    def test_download_log_passes_verified_claims_to_serializer(self):
        buyer = SimpleNamespace(uuid="user::buyer", user_type="customer")
        claims = {
            "jti": "delivery::1",
            "sub": buyer.uuid,
            "asset_uuid": "asset::1",
            "order_uuid": "order::1",
            "download_url": "https://cdn.example.com/asset.pdf",
            "iat": 1,
            "exp": 9999999999,
        }
        download = object()

        serializer = MagicMock()
        serializer.log_download.return_value = download
        serializer.serialize_download.return_value = {"uuid": "download::1"}

        with patch("utils.auth.verify_access_token", return_value=(buyer, {})), \
                patch("controllers.asset.verify_delivery_token", return_value=claims), \
                patch("controllers.asset.AssetSerializer", return_value=serializer):
            response = self.client.post(
                "/v1/assets/asset::1/downloads/",
                json={
                    "order_uuid": "attacker-supplied-order",
                    "download_url": "https://attacker.example/file",
                },
                headers={
                    "Authorization": "Bearer buyer-token",
                    "X-Asset-Delivery-Token": "delivery-token",
                },
            )

        self.assertEqual(response.status_code, 201)
        logged_payload = serializer.log_download.call_args.args[1]
        self.assertEqual(logged_payload["_delivery_claims"], claims)

    def test_invalid_delivery_token_returns_401(self):
        buyer = SimpleNamespace(uuid="user::buyer", user_type="customer")

        with patch("utils.auth.verify_access_token", return_value=(buyer, {})), \
                patch("controllers.asset.verify_delivery_token", side_effect=AuthError("invalid token")):
            response = self.client.post(
                "/v1/assets/asset::1/downloads/",
                json={},
                headers={
                    "Authorization": "Bearer buyer-token",
                    "X-Asset-Delivery-Token": "invalid-token",
                },
            )

        self.assertEqual(response.status_code, 401)

if __name__ == "__main__":
    unittest.main()
