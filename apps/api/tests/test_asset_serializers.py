import os
import sys
import datetime
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.assetSerializers import AssetInputError, AssetSerializer, DeliveryTokenError


class AssetAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_serialize_asset_does_not_expose_cloudfront_url(self):
        asset = MagicMock()
        asset.uuid = "asset::1"
        asset.product.uuid = "product::1"
        asset.storage_provider = "s3"
        asset.bucket_name = "bucket"
        asset.object_key = "products/product::1/asset.pdf"
        asset.original_filename = "asset.pdf"
        asset.content_type = "application/pdf"
        asset.size_bytes = 123
        asset.checksum_sha256 = "checksum"
        asset.cloudfront_url = "https://cdn.example.com/asset.pdf"
        asset.asset_status = "verified"
        asset.created_on = None
        asset.modified_on = None

        result = AssetSerializer().serialize_asset(asset)

        self.assertNotIn("cloudfront_url", result)
        self.assertEqual(result["object_key"], "products/product::1/asset.pdf")

    def test_authorize_download_allows_owner_with_granted_access(self):
        asset = MagicMock()
        asset.uuid = "asset::1"
        asset.product_id = 11
        asset.cloudfront_url = "https://cdn.example.com/asset.pdf"
        asset.object_key = "products/product::1/asset.pdf"
        asset.bucket_name = "bucket"
        asset.asset_status = "verified"

        order = MagicMock()
        order.id = 21
        order.uuid = "order::1"
        order.buyer_id = 7
        order.product_id = 11
        order.payment_status = "paid"

        access = MagicMock()
        access.access_status = "granted"
        access.download_count = 2
        access.created_on = datetime.datetime.utcnow()

        user = MagicMock()
        user.id = 7
        user.uuid = "user::buyer"

        with patch("serializers.assetSerializers.g", new=SimpleNamespace(user=user)), \
                patch("serializers.assetSerializers.ProductAsset") as product_asset_model, \
                patch("serializers.assetSerializers.MarketplaceOrder") as marketplace_order_model, \
                patch("serializers.assetSerializers.ProductAccess") as product_access_model, \
                patch("serializers.assetSerializers.db") as db_mock, \
                patch("serializers.assetSerializers.S3AssetGateway") as gateway, \
                patch("serializers.assetSerializers.create_delivery_token", return_value="delivery-token"):
            product_asset_model.query.filter_by.return_value.first.return_value = asset
            marketplace_order_model.query.filter_by.return_value.first.return_value = order
            product_access_model.query.filter_by.return_value.first.return_value = access
            gateway.return_value.create_presigned_get_url.return_value = "https://s3.example.com/protected"
            db_mock.session.commit = MagicMock()

            serializer = AssetSerializer()
            result = serializer.authorize_download("asset::1", {"order_uuid": "order::1"})

            self.assertEqual(result["asset_uuid"], "asset::1")
            self.assertEqual(result["order_uuid"], "order::1")
            self.assertEqual(result["download_url"], "https://s3.example.com/protected")
            self.assertNotEqual(result["download_url"], asset.cloudfront_url)
            self.assertTrue(result["delivery_token"])
            self.assertEqual(result["download_count"], 2)
            gateway.return_value.create_presigned_get_url.assert_called_once_with(
                asset.object_key,
                asset.bucket_name,
                result["delivery_token_ttl_seconds"],
            )
            db_mock.session.commit.assert_not_called()

    def test_authorize_download_rejects_revoked_access(self):
        asset = MagicMock()
        asset.uuid = "asset::1"
        asset.product_id = 11
        asset.cloudfront_url = "https://cdn.example.com/asset.pdf"
        asset.asset_status = "verified"

        order = MagicMock()
        order.id = 21
        order.uuid = "order::1"
        order.buyer_id = 7
        order.product_id = 11
        order.payment_status = "paid"

        access = MagicMock()
        access.access_status = "revoked"
        access.download_count = 2

        user = MagicMock()
        user.id = 7
        user.uuid = "user::buyer"

        with patch("serializers.assetSerializers.g", new=SimpleNamespace(user=user)), \
                patch("serializers.assetSerializers.ProductAsset") as product_asset_model, \
                patch("serializers.assetSerializers.MarketplaceOrder") as marketplace_order_model, \
                patch("serializers.assetSerializers.ProductAccess") as product_access_model:
            product_asset_model.query.filter_by.return_value.first.return_value = asset
            marketplace_order_model.query.filter_by.return_value.first.return_value = order
            product_access_model.query.filter_by.return_value.first.return_value = access

            serializer = AssetSerializer()
            with self.assertRaises(AssetInputError):
                serializer.authorize_download("asset::1", {"order_uuid": "order::1"})

    def test_authorize_download_rejects_expired_access(self):
        asset = MagicMock()
        asset.uuid = "asset::1"
        asset.product_id = 11
        asset.cloudfront_url = "https://cdn.example.com/asset.pdf"
        asset.asset_status = "verified"

        order = MagicMock()
        order.id = 21
        order.uuid = "order::1"
        order.buyer_id = 7
        order.product_id = 11
        order.payment_status = "paid"

        access = MagicMock()
        access.access_status = "granted"
        access.download_count = 1
        access.created_on = datetime.datetime.utcnow() - datetime.timedelta(days=31)

        user = MagicMock()
        user.id = 7
        user.uuid = "user::buyer"

        with patch("serializers.assetSerializers.g", new=SimpleNamespace(user=user)), \
                patch("serializers.assetSerializers.ProductAsset") as product_asset_model, \
                patch("serializers.assetSerializers.MarketplaceOrder") as marketplace_order_model, \
                patch("serializers.assetSerializers.ProductAccess") as product_access_model:
            product_asset_model.query.filter_by.return_value.first.return_value = asset
            marketplace_order_model.query.filter_by.return_value.first.return_value = order
            product_access_model.query.filter_by.return_value.first.return_value = access

            serializer = AssetSerializer()
            with self.assertRaises(AssetInputError):
                serializer.authorize_download("asset::1", {"order_uuid": "order::1"})

    def test_authorize_download_rejects_download_limit(self):
        asset = MagicMock()
        asset.uuid = "asset::1"
        asset.product_id = 11
        asset.cloudfront_url = "https://cdn.example.com/asset.pdf"
        asset.asset_status = "verified"

        order = MagicMock()
        order.id = 21
        order.uuid = "order::1"
        order.buyer_id = 7
        order.product_id = 11
        order.payment_status = "paid"

        access = MagicMock()
        access.access_status = "granted"
        access.download_count = 3
        access.created_on = datetime.datetime.utcnow()

        user = MagicMock()
        user.id = 7
        user.uuid = "user::buyer"

        with patch("serializers.assetSerializers.g", new=SimpleNamespace(user=user)), \
                patch("serializers.assetSerializers.ProductAsset") as product_asset_model, \
                patch("serializers.assetSerializers.MarketplaceOrder") as marketplace_order_model, \
                patch("serializers.assetSerializers.ProductAccess") as product_access_model:
            product_asset_model.query.filter_by.return_value.first.return_value = asset
            marketplace_order_model.query.filter_by.return_value.first.return_value = order
            product_access_model.query.filter_by.return_value.first.return_value = access

            serializer = AssetSerializer()
            with self.assertRaises(AssetInputError):
                serializer.authorize_download("asset::1", {"order_uuid": "order::1"})

    def test_delivery_token_consumption_records_token_once(self):
        asset = MagicMock(uuid="asset::1", cloudfront_url="https://cdn.example.com/asset.pdf", object_key="asset.pdf")
        order = MagicMock(uuid="order::1")
        user = MagicMock(uuid="user::buyer")
        claims = {
            "jti": "delivery::1",
            "sub": "user::buyer",
            "asset_uuid": "asset::1",
            "order_uuid": "order::1",
            "download_url": "https://cdn.example.com/asset.pdf",
        }

        with patch("serializers.assetSerializers.DeliveryTokenUse") as token_use_model, \
                patch("serializers.assetSerializers.db") as db_mock:
            token_use_model.query.filter_by.return_value.first.return_value = None

            AssetSerializer()._consume_delivery_token(claims, user, asset, order)

            token_use_model.assert_called_once_with(
                token_jti="delivery::1",
                user_uuid="user::buyer",
                asset_uuid="asset::1",
                order_uuid="order::1",
            )
            db_mock.session.add.assert_called_once()

    def test_delivery_token_replay_is_rejected(self):
        asset = MagicMock(uuid="asset::1", cloudfront_url="https://cdn.example.com/asset.pdf", object_key="asset.pdf")
        order = MagicMock(uuid="order::1")
        user = MagicMock(uuid="user::buyer")
        claims = {
            "jti": "delivery::1",
            "sub": "user::buyer",
            "asset_uuid": "asset::1",
            "order_uuid": "order::1",
            "download_url": "https://cdn.example.com/asset.pdf",
        }

        with patch("serializers.assetSerializers.DeliveryTokenUse") as token_use_model:
            token_use_model.query.filter_by.return_value.first.return_value = MagicMock()

            with self.assertRaises(DeliveryTokenError):
                AssetSerializer()._consume_delivery_token(claims, user, asset, order)


if __name__ == "__main__":
    unittest.main()
