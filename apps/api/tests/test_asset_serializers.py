import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.assetSerializers import AssetInputError, AssetSerializer


class AssetAuthorizationTests(unittest.TestCase):
    def test_authorize_download_allows_owner_with_granted_access(self):
        asset = MagicMock()
        asset.uuid = "asset::1"
        asset.product_id = 11
        asset.cloudfront_url = "https://cdn.example.com/asset.pdf"

        order = MagicMock()
        order.id = 21
        order.uuid = "order::1"
        order.buyer_id = 7
        order.product_id = 11

        access = MagicMock()
        access.access_status = "granted"
        access.download_count = 2

        user = MagicMock()
        user.id = 7
        user.uuid = "user::buyer"

        with patch("serializers.assetSerializers.g") as g_mock, \
                patch("serializers.assetSerializers.ProductAsset") as product_asset_model, \
                patch("serializers.assetSerializers.MarketplaceOrder") as marketplace_order_model, \
                patch("serializers.assetSerializers.ProductAccess") as product_access_model, \
                patch("serializers.assetSerializers.db") as db_mock:
            g_mock.user = user
            product_asset_model.query.filter_by.return_value.first.return_value = asset
            marketplace_order_model.query.filter_by.return_value.first.return_value = order
            product_access_model.query.filter_by.return_value.first.return_value = access
            db_mock.session.commit = MagicMock()

            serializer = AssetSerializer()
            result = serializer.authorize_download("asset::1", {"order_uuid": "order::1"})

            self.assertEqual(result["asset_uuid"], "asset::1")
            self.assertEqual(result["order_uuid"], "order::1")
            self.assertEqual(result["download_url"], asset.cloudfront_url)
            self.assertEqual(result["download_count"], 3)
            db_mock.session.commit.assert_called()

    def test_authorize_download_rejects_revoked_access(self):
        asset = MagicMock()
        asset.uuid = "asset::1"
        asset.product_id = 11
        asset.cloudfront_url = "https://cdn.example.com/asset.pdf"

        order = MagicMock()
        order.id = 21
        order.uuid = "order::1"
        order.buyer_id = 7
        order.product_id = 11

        access = MagicMock()
        access.access_status = "revoked"
        access.download_count = 2

        user = MagicMock()
        user.id = 7
        user.uuid = "user::buyer"

        with patch("serializers.assetSerializers.g") as g_mock, \
                patch("serializers.assetSerializers.ProductAsset") as product_asset_model, \
                patch("serializers.assetSerializers.MarketplaceOrder") as marketplace_order_model, \
                patch("serializers.assetSerializers.ProductAccess") as product_access_model:
            g_mock.user = user
            product_asset_model.query.filter_by.return_value.first.return_value = asset
            marketplace_order_model.query.filter_by.return_value.first.return_value = order
            product_access_model.query.filter_by.return_value.first.return_value = access

            serializer = AssetSerializer()
            with self.assertRaises(AssetInputError):
                serializer.authorize_download("asset::1", {"order_uuid": "order::1"})


if __name__ == "__main__":
    unittest.main()
