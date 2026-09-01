import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from serializers.productSerializers import ProductInputError, ProductSerializer


class ProductPreviewTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.context = self.app.app_context()
        self.context.push()
        self.user = SimpleNamespace(id=7, user_type="seller")
        self.product = SimpleNamespace(
            id=11,
            uuid="product::1",
            owner_id=7,
            title="Premium guide",
            image_uri=None,
            image_alt=None,
            image_provider=None,
            image_key=None,
            image_mime_type=None,
            image_size_bytes=None,
        )

    def tearDown(self):
        self.context.pop()

    def test_preview_target_uses_a_separate_preview_key(self):
        gateway = MagicMock()
        gateway.create_presigned_put_url.return_value = {"upload_url": "https://signed.example/put"}
        with patch("serializers.productSerializers.g", new=SimpleNamespace(user=self.user)), \
                patch.object(ProductSerializer, "get_by_uuid", return_value=self.product), \
                patch("serializers.productSerializers.db") as db_mock:
            serializer = ProductSerializer()
            serializer.gateway = gateway
            product, signed = serializer.create_preview_upload_target("product::1", {
                "original_filename": "cover.webp",
                "content_type": "image/webp",
                "size_bytes": 1024,
            })

        self.assertIs(product, self.product)
        self.assertTrue(product.image_key.startswith("previews/product::1/"))
        self.assertEqual(product.image_mime_type, "image/webp")
        self.assertEqual(signed["upload_url"], "https://signed.example/put")
        db_mock.session.commit.assert_called_once()

    def test_preview_target_rejects_non_image_content(self):
        with patch("serializers.productSerializers.g", new=SimpleNamespace(user=self.user)), \
                patch.object(ProductSerializer, "get_by_uuid", return_value=self.product):
            serializer = ProductSerializer()
            with self.assertRaises(ProductInputError):
                serializer.create_preview_upload_target("product::1", {
                    "original_filename": "payload.svg",
                    "content_type": "image/svg+xml",
                    "size_bytes": 1024,
                })

    def test_preview_completion_verifies_s3_metadata(self):
        self.product.image_provider = "s3"
        self.product.image_key = "previews/product::1/cover.webp"
        self.product.image_mime_type = "image/webp"
        self.product.image_size_bytes = 1024
        gateway = MagicMock()
        gateway.head_object.return_value = {"ContentLength": 1024, "ContentType": "image/webp"}
        with patch("serializers.productSerializers.g", new=SimpleNamespace(user=self.user)), \
                patch.object(ProductSerializer, "get_by_uuid", return_value=self.product), \
                patch("serializers.productSerializers.db") as db_mock:
            serializer = ProductSerializer()
            serializer.gateway = gateway
            product = serializer.complete_preview_upload("product::1", {"size_bytes": 1024})

        self.assertIs(product, self.product)
        gateway.head_object.assert_called_once_with(self.product.image_key)
        db_mock.session.commit.assert_called_once()

    def test_preview_url_is_short_lived_and_requires_no_purchase(self):
        self.product.image_key = "previews/product::1/cover.webp"
        gateway = MagicMock()
        gateway.create_presigned_get_url.return_value = "https://signed.example/get"
        serializer = ProductSerializer()
        serializer.gateway = gateway

        self.assertEqual(serializer.preview_url(self.product), "https://signed.example/get")
        gateway.create_presigned_get_url.assert_called_once_with(self.product.image_key)


if __name__ == "__main__":
    unittest.main()
