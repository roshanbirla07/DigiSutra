import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from serializers.productSerializers import ProductSerializer, ProductInputError
from v1.routers.routes import v1


class ProductPublishTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(v1)
        self.context = self.app.app_context()
        self.context.push()
        self.product = SimpleNamespace(id=9, uuid="product::1", owner_id=7, owner=SimpleNamespace(uuid="seller::1"), is_public=False, is_active=False)

    def tearDown(self):
        self.context.pop()

    def test_publish_requires_verified_asset(self):
        with patch.object(ProductSerializer, "_get_owned_product", return_value=self.product), patch.object(ProductSerializer, "validate_owner"), patch("serializers.productSerializers.ProductAsset") as assets, patch("serializers.productSerializers.db") as database:
            assets.query.filter_by.return_value.first.return_value = None
            with self.assertRaises(ProductInputError):
                ProductSerializer().publish(self.product.uuid)
            self.assertFalse(self.product.is_public)
            database.session.commit.assert_not_called()

    def test_publish_verifies_owner_readiness_and_commits_visibility(self):
        with patch.object(ProductSerializer, "_get_owned_product", return_value=self.product), patch.object(ProductSerializer, "validate_owner") as validate, patch("serializers.productSerializers.ProductAsset") as assets, patch("serializers.productSerializers.db") as database:
            assets.query.filter_by.return_value.first.return_value = SimpleNamespace(asset_status="verified")
            ProductSerializer().publish(self.product.uuid)
            validate.assert_called_once_with({"owner_uuid": "seller::1"})
            assets.query.filter_by.assert_called_once_with(product_id=9, asset_status="verified")
            self.assertTrue(self.product.is_public)
            self.assertTrue(self.product.is_active)
            database.session.commit.assert_called_once()

    def test_another_seller_cannot_publish_product(self):
        with patch("serializers.productSerializers.g", new=SimpleNamespace(user=SimpleNamespace(id=8, user_type="seller"))), patch.object(ProductSerializer, "get_by_uuid", return_value=self.product), patch("serializers.productSerializers.db") as database:
            with self.assertRaises(ProductInputError):
                ProductSerializer().publish(self.product.uuid)
            database.session.commit.assert_not_called()

    def test_customer_and_anonymous_cannot_publish(self):
        client = self.app.test_client()
        self.assertEqual(client.post("/v1/products/product::1/publish/").status_code, 401)
        with patch("utils.auth.verify_access_token", return_value=(SimpleNamespace(user_type="customer"), {})):
            self.assertEqual(client.post("/v1/products/product::1/publish/", headers={"Authorization": "Bearer test"}).status_code, 403)

    def test_suspended_or_unverified_owner_cannot_publish(self):
        with patch.object(ProductSerializer, "_get_owned_product", return_value=self.product), patch.object(ProductSerializer, "validate_owner", side_effect=ProductInputError("Seller KYC required")), patch("serializers.productSerializers.db") as database:
            with self.assertRaises(ProductInputError):
                ProductSerializer().publish(self.product.uuid)
            self.assertFalse(self.product.is_public)
            database.session.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
