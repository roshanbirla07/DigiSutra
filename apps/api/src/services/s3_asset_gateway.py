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
        if not AWS_REGION or not AWS_S3_BUCKET_NAME:
            raise S3AssetGatewayError("AWS S3 configuration is incomplete")

    def create_presigned_put_url(self, object_key, content_type="application/octet-stream", expires_in=None):
        expires_in = int(expires_in or AWS_S3_PRESIGN_EXPIRES_IN)
        try:
            upload_url = self._client().generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": AWS_S3_BUCKET_NAME,
                    "Key": object_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
        except Exception as exc:
            raise S3AssetGatewayError(f"Unable to create asset upload URL: {exc}") from exc
        return {
            "upload_url": upload_url,
            "method": "PUT",
            "headers": {"Content-Type": content_type},
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
        client_options = {"region_name": AWS_REGION}
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            client_options.update(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            )
        return boto3.client("s3", **client_options)

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
