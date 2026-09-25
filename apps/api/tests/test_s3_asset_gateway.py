import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from services.s3_asset_gateway import S3AssetGateway, S3AssetGatewayError


class S3AssetGatewayTests(unittest.TestCase):
    @patch("services.s3_asset_gateway.AWS_S3_BUCKET_NAME", "digisutra-assets")
    @patch("services.s3_asset_gateway.AWS_REGION", "ap-south-1")
    def test_create_presigned_put_url_uses_boto3_signer(self):
        client = MagicMock()
        client.generate_presigned_url.return_value = "https://signed.example/upload"

        with patch.object(S3AssetGateway, "_client", return_value=client):
            result = S3AssetGateway().create_presigned_put_url(
                "products/seller/file name.zip",
                "application/zip",
                600,
            )

        client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": "digisutra-assets",
                "Key": "products/seller/file name.zip",
                "ContentType": "application/zip",
            },
            ExpiresIn=600,
        )
        self.assertEqual(result["upload_url"], "https://signed.example/upload")
        self.assertEqual(result["headers"], {"Content-Type": "application/zip"})

    @patch("services.s3_asset_gateway.AWS_S3_BUCKET_NAME", "digisutra-assets")
    @patch("services.s3_asset_gateway.AWS_REGION", "ap-south-1")
    def test_create_presigned_put_url_wraps_provider_errors(self):
        client = MagicMock()
        client.generate_presigned_url.side_effect = RuntimeError("credentials unavailable")

        with patch.object(S3AssetGateway, "_client", return_value=client):
            with self.assertRaisesRegex(S3AssetGatewayError, "Unable to create asset upload URL"):
                S3AssetGateway().create_presigned_put_url("products/file.zip")

    @patch("services.s3_asset_gateway.AWS_S3_BUCKET_NAME", "digisutra-assets")
    @patch("services.s3_asset_gateway.AWS_REGION", "ap-south-1")
    @patch("services.s3_asset_gateway.AWS_ACCESS_KEY_ID", "")
    @patch("services.s3_asset_gateway.AWS_SECRET_ACCESS_KEY", "")
    def test_client_uses_regional_sigv4_virtual_host_and_role_credentials(self):
        with patch("boto3.client") as client:
            S3AssetGateway()._client()

        options = client.call_args.kwargs
        self.assertEqual(client.call_args.args, ("s3",))
        self.assertEqual(options["region_name"], "ap-south-1")
        self.assertEqual(options["endpoint_url"], "https://s3.ap-south-1.amazonaws.com")
        self.assertEqual(options["config"].signature_version, "s3v4")
        self.assertEqual(options["config"].s3["addressing_style"], "virtual")
        self.assertNotIn("aws_access_key_id", options)
        self.assertNotIn("aws_secret_access_key", options)

    @patch("services.s3_asset_gateway.AWS_S3_BUCKET_NAME", "")
    def test_client_requires_bucket_configuration(self):
        with self.assertRaisesRegex(S3AssetGatewayError, "configuration is incomplete"):
            S3AssetGateway()._client()


if __name__ == "__main__":
    unittest.main()
