import datetime
import hashlib
import hmac
from urllib.parse import quote

from configuration.variables import (
    AWS_ACCESS_KEY_ID,
    AWS_CLOUDFRONT_DOMAIN,
    AWS_REGION,
    AWS_S3_BUCKET_NAME,
    AWS_S3_PRESIGN_EXPIRES_IN,
    AWS_S3_GET_PRESIGN_EXPIRES_IN,
    AWS_SECRET_ACCESS_KEY,
)


class S3AssetGatewayError(Exception):
    pass


class S3AssetGateway(object):
    def _require_config(self):
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not AWS_S3_BUCKET_NAME:
            raise S3AssetGatewayError("AWS S3 configuration is incomplete")

    @staticmethod
    def _sign(key, message):
        return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()

    def _signing_key(self, date_stamp):
        k_date = self._sign(("AWS4" + AWS_SECRET_ACCESS_KEY).encode("utf-8"), date_stamp)
        k_region = hmac.new(k_date, AWS_REGION.encode("utf-8"), hashlib.sha256).digest()
        k_service = hmac.new(k_region, b"s3", hashlib.sha256).digest()
        return hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()

    def create_presigned_put_url(self, object_key, content_type="application/octet-stream", expires_in=None):
        self._require_config()
        expires_in = int(expires_in or AWS_S3_PRESIGN_EXPIRES_IN)
        now = datetime.datetime.utcnow()
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        host = f"{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com"
        canonical_uri = f"/{quote(object_key, safe='/')}"
        canonical_querystring = ""
        canonical_headers = (
            f"host:{host}\n"
            f"x-amz-content-sha256:UNSIGNED-PAYLOAD\n"
            f"x-amz-date:{amz_date}\n"
        )
        signed_headers = "host;x-amz-content-sha256;x-amz-date"
        canonical_request = "\n".join(
            [
                "PUT",
                canonical_uri,
                canonical_querystring,
                canonical_headers,
                signed_headers,
                "UNSIGNED-PAYLOAD",
            ]
        )
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{AWS_REGION}/s3/aws4_request"
        string_to_sign = "\n".join(
            [
                algorithm,
                amz_date,
                credential_scope,
                hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
            ]
        )
        signing_key = self._signing_key(date_stamp)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        query = (
            f"X-Amz-Algorithm={algorithm}"
            f"&X-Amz-Credential={quote(AWS_ACCESS_KEY_ID + '/' + credential_scope, safe='')}"
            f"&X-Amz-Date={amz_date}"
            f"&X-Amz-Expires={expires_in}"
            f"&X-Amz-SignedHeaders={signed_headers}"
            f"&X-Amz-Signature={signature}"
        )
        return {
            "upload_url": f"https://{host}{canonical_uri}?{query}",
            "method": "PUT",
            "headers": {
                "Content-Type": content_type,
                "x-amz-content-sha256": "UNSIGNED-PAYLOAD",
                "x-amz-date": amz_date,
            },
            "bucket_name": AWS_S3_BUCKET_NAME,
            "object_key": object_key,
            "expires_in": expires_in,
        }

    def cloudfront_url_for(self, object_key):
        if AWS_CLOUDFRONT_DOMAIN:
            return f"https://{AWS_CLOUDFRONT_DOMAIN.rstrip('/')}/{object_key.lstrip('/')}"
        return f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{object_key.lstrip('/')}"

    def _client(self):
        self._require_config()
        try:
            import boto3
        except ImportError as exc:
            raise S3AssetGatewayError("boto3 is required for protected asset delivery") from exc
        return boto3.client("s3", region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    def create_presigned_get_url(self, object_key, bucket_name=None, expires_in=None):
        try:
            return self._client().generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name or AWS_S3_BUCKET_NAME, "Key": object_key},
                ExpiresIn=int(expires_in or AWS_S3_GET_PRESIGN_EXPIRES_IN),
            )
        except Exception as exc:
            raise S3AssetGatewayError(f"Unable to create protected asset URL: {exc}") from exc

    def head_object(self, object_key, bucket_name=None):
        try:
            return self._client().head_object(Bucket=bucket_name or AWS_S3_BUCKET_NAME, Key=object_key)
        except Exception as exc:
            raise S3AssetGatewayError(f"Unable to verify uploaded asset: {exc}") from exc
