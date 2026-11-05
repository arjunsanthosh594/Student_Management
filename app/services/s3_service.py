"""
app/services/s3_service.py — Amazon S3 operations using Boto3
"""
import boto3
import botocore
from flask import current_app
from typing import Optional


class S3Service:
    """Wrapper for Amazon S3 operations.

    On EC2, boto3 automatically uses the instance IAM Role when
    AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are NOT set.
    For local dev, set them in .env.
    """

    def __init__(self):
        self._client = None
        self._bucket = None

    def _get_client(self):
        if self._client is None:
            key_id = current_app.config.get("AWS_ACCESS_KEY_ID", "")
            secret = current_app.config.get("AWS_SECRET_ACCESS_KEY", "")
            region = current_app.config.get("AWS_REGION", "us-east-1")

            if key_id and secret:
                self._client = boto3.client(
                    "s3",
                    region_name=region,
                    aws_access_key_id=key_id,
                    aws_secret_access_key=secret,
                )
            else:
                # Uses IAM Role on EC2 or env vars set by the OS
                self._client = boto3.client("s3", region_name=region)
        return self._client

    def _get_bucket(self) -> str:
        if self._bucket is None:
            self._bucket = current_app.config.get("S3_BUCKET_NAME", "")
        return self._bucket

    def is_configured(self) -> bool:
        """Return True if an S3 bucket name is provided."""
        return bool(self._get_bucket())

    def upload_file(self, file_obj, object_key: str, content_type: str = "image/jpeg") -> bool:
        """Upload a file-like object to S3. Returns True on success."""
        try:
            self._get_client().upload_fileobj(
                file_obj,
                self._get_bucket(),
                object_key,
                ExtraArgs={"ContentType": content_type},
            )
            return True
        except botocore.exceptions.ClientError as e:
            current_app.logger.error(f"S3 upload error: {e}")
            return False

    def delete_file(self, object_key: str) -> bool:
        """Delete an object from S3. Returns True on success."""
        try:
            self._get_client().delete_object(Bucket=self._get_bucket(), Key=object_key)
            return True
        except botocore.exceptions.ClientError as e:
            current_app.logger.error(f"S3 delete error: {e}")
            return False

    def get_presigned_url(self, object_key: str, expiry: int = 3600) -> Optional[str]:
        """Generate a presigned URL valid for `expiry` seconds."""
        try:
            url = self._get_client().generate_presigned_url(
                "get_object",
                Params={"Bucket": self._get_bucket(), "Key": object_key},
                ExpiresIn=expiry,
            )
            return url
        except botocore.exceptions.ClientError as e:
            current_app.logger.error(f"S3 presigned URL error: {e}")
            return None
