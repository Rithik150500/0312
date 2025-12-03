"""
S3/MinIO Storage Client

Handles uploading and retrieving files from object storage.
"""
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config
import io
from typing import Optional
import logging
from PIL import Image

from ..config import settings

logger = logging.getLogger(__name__)


class S3Client:
    """Client for S3/MinIO object storage."""

    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        self.bucket = settings.S3_BUCKET
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
            logger.info(f"Bucket '{self.bucket}' exists")
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                logger.info(f"Created bucket '{self.bucket}'")
            except ClientError as e:
                logger.error(f"Failed to create bucket: {e}")
                raise

    def upload_file(self, file_path: str, object_name: str) -> str:
        """
        Upload a file to S3.

        Args:
            file_path: Local path to file
            object_name: S3 object name (path in bucket)

        Returns:
            S3 path (object_name)
        """
        try:
            self.client.upload_file(file_path, self.bucket, object_name)
            logger.info(f"Uploaded {file_path} to s3://{self.bucket}/{object_name}")
            return object_name
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    def upload_image(self, image: Image.Image, object_name: str, format: str = 'PNG') -> str:
        """
        Upload a PIL Image to S3.

        Args:
            image: PIL Image object
            object_name: S3 object name
            format: Image format (PNG, JPEG, etc.)

        Returns:
            S3 path (object_name)
        """
        try:
            # Convert image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format=format)
            buffer.seek(0)

            # Upload
            self.client.upload_fileobj(
                buffer,
                self.bucket,
                object_name,
                ExtraArgs={'ContentType': f'image/{format.lower()}'}
            )

            logger.info(f"Uploaded image to s3://{self.bucket}/{object_name}")
            return object_name

        except ClientError as e:
            logger.error(f"Failed to upload image: {e}")
            raise

    def upload_bytes(self, data: bytes, object_name: str, content_type: str = 'application/octet-stream') -> str:
        """
        Upload bytes data to S3.

        Args:
            data: Bytes data
            object_name: S3 object name
            content_type: MIME type

        Returns:
            S3 path (object_name)
        """
        try:
            buffer = io.BytesIO(data)
            self.client.upload_fileobj(
                buffer,
                self.bucket,
                object_name,
                ExtraArgs={'ContentType': content_type}
            )

            logger.info(f"Uploaded bytes to s3://{self.bucket}/{object_name}")
            return object_name

        except ClientError as e:
            logger.error(f"Failed to upload bytes: {e}")
            raise

    def download_file(self, object_name: str, file_path: str):
        """
        Download a file from S3.

        Args:
            object_name: S3 object name
            file_path: Local path to save file
        """
        try:
            self.client.download_file(self.bucket, object_name, file_path)
            logger.info(f"Downloaded s3://{self.bucket}/{object_name} to {file_path}")
        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            raise

    def get_file_bytes(self, object_name: str) -> bytes:
        """
        Get file contents as bytes.

        Args:
            object_name: S3 object name

        Returns:
            File contents as bytes
        """
        try:
            buffer = io.BytesIO()
            self.client.download_fileobj(self.bucket, object_name, buffer)
            buffer.seek(0)
            return buffer.read()
        except ClientError as e:
            logger.error(f"Failed to get file bytes: {e}")
            raise

    def file_exists(self, object_name: str) -> bool:
        """
        Check if a file exists in S3.

        Args:
            object_name: S3 object name

        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=object_name)
            return True
        except ClientError:
            return False

    def delete_file(self, object_name: str):
        """
        Delete a file from S3.

        Args:
            object_name: S3 object name
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_name)
            logger.info(f"Deleted s3://{self.bucket}/{object_name}")
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            raise

    def get_presigned_url(self, object_name: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for an object.

        Args:
            object_name: S3 object name
            expiration: URL expiration time in seconds

        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': object_name},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
