"""S3 Storage adapter implementation.

This adapter implements the StoragePort interface using aioboto3
for asynchronous S3 operations. Supports both AWS S3 and MinIO.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC
from typing import Any

import aioboto3
import structlog
from botocore.config import Config
from botocore.exceptions import ClientError

from src.application.ports.storage_port import StorageError
from src.application.ports.storage_port import StoragePort
from src.config.settings import Settings
from src.domain.value_objects import ObjectInfo

logger = structlog.get_logger()


class S3StorageAdapter(StoragePort):
    """S3-compatible storage adapter using aioboto3.

    Supports both AWS S3 and MinIO (via endpoint_url configuration).
    Uses async context managers for proper resource management.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the adapter with settings.

        Args:
            settings: Application settings containing S3 configuration.
        """
        self._settings = settings
        self._session = aioboto3.Session()
        self._config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},  # Required for MinIO
        )

    @asynccontextmanager
    async def _get_client(self) -> AsyncIterator[Any]:
        """Get an S3 client context manager.

        Yields:
            Async S3 client for operations.
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._settings.s3_endpoint_url,
            aws_access_key_id=self._settings.s3_access_key,
            aws_secret_access_key=self._settings.s3_secret_key.get_secret_value(),
            region_name=self._settings.s3_region,
            config=self._config,
        ) as client:
            yield client

    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiry_seconds: int = 3600,
    ) -> str:
        """Generate a presigned URL for downloading an object.

        Args:
            bucket: S3 bucket name.
            key: Object key (path) in the bucket.
            expiry_seconds: URL expiration time in seconds.

        Returns:
            Presigned URL for the object.

        Raises:
            StorageError: If URL generation fails.
        """
        try:
            async with self._get_client() as client:
                url: str = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=expiry_seconds,
                )

                logger.debug(
                    "presigned_url_generated",
                    bucket=bucket,
                    key=key,
                    expiry_seconds=expiry_seconds,
                )

                return url

        except ClientError as e:
            logger.error(
                "presigned_url_generation_failed",
                bucket=bucket,
                key=key,
                error=str(e),
            )
            raise StorageError(f"Failed to generate presigned URL: {e}") from e

    async def object_exists(
        self,
        bucket: str,
        key: str,
    ) -> bool:
        """Check if an object exists in the bucket.

        Args:
            bucket: S3 bucket name.
            key: Object key (path) in the bucket.

        Returns:
            True if the object exists, False otherwise.

        Raises:
            StorageError: If the check fails.
        """
        try:
            async with self._get_client() as client:
                await client.head_object(Bucket=bucket, Key=key)
                return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                return False

            logger.error(
                "object_exists_check_failed",
                bucket=bucket,
                key=key,
                error=str(e),
            )
            raise StorageError(f"Failed to check object existence: {e}") from e

    async def list_objects(
        self,
        bucket: str,
        prefix: str,
        max_keys: int = 1000,
    ) -> list[ObjectInfo]:
        """List objects in a bucket with a given prefix.

        Args:
            bucket: S3 bucket name.
            prefix: Key prefix to filter objects.
            max_keys: Maximum number of keys to return.

        Returns:
            List of ObjectInfo for matching objects.

        Raises:
            StorageError: If listing fails.
        """
        try:
            async with self._get_client() as client:
                response = await client.list_objects_v2(
                    Bucket=bucket,
                    Prefix=prefix,
                    MaxKeys=max_keys,
                )

                objects = []
                for obj in response.get("Contents", []):
                    # Ensure last_modified is timezone-aware
                    last_modified = obj["LastModified"]
                    if last_modified.tzinfo is None:
                        last_modified = last_modified.replace(tzinfo=UTC)

                    objects.append(
                        ObjectInfo(
                            bucket=bucket,
                            key=obj["Key"],
                            size_bytes=obj["Size"],
                            last_modified=last_modified,
                            etag=obj.get("ETag", "").strip('"'),
                        )
                    )

                logger.debug(
                    "objects_listed",
                    bucket=bucket,
                    prefix=prefix,
                    count=len(objects),
                )

                return objects

        except ClientError as e:
            logger.error(
                "list_objects_failed",
                bucket=bucket,
                prefix=prefix,
                error=str(e),
            )
            raise StorageError(f"Failed to list objects: {e}") from e

    async def delete_object(
        self,
        bucket: str,
        key: str,
    ) -> None:
        """Delete an object from the bucket.

        Args:
            bucket: S3 bucket name.
            key: Object key (path) to delete.

        Raises:
            StorageError: If deletion fails.
        """
        try:
            async with self._get_client() as client:
                await client.delete_object(Bucket=bucket, Key=key)

                logger.info(
                    "object_deleted",
                    bucket=bucket,
                    key=key,
                )

        except ClientError as e:
            logger.error(
                "delete_object_failed",
                bucket=bucket,
                key=key,
                error=str(e),
            )
            raise StorageError(f"Failed to delete object: {e}") from e

    async def get_object_info(
        self,
        bucket: str,
        key: str,
    ) -> ObjectInfo | None:
        """Get metadata for a specific object.

        Args:
            bucket: S3 bucket name.
            key: Object key (path) in the bucket.

        Returns:
            ObjectInfo if object exists, None otherwise.

        Raises:
            StorageError: If the operation fails.
        """
        try:
            async with self._get_client() as client:
                response = await client.head_object(Bucket=bucket, Key=key)

                # Ensure last_modified is timezone-aware
                last_modified = response["LastModified"]
                if last_modified.tzinfo is None:
                    last_modified = last_modified.replace(tzinfo=UTC)

                return ObjectInfo(
                    bucket=bucket,
                    key=key,
                    size_bytes=response["ContentLength"],
                    last_modified=last_modified,
                    etag=response.get("ETag", "").strip('"'),
                    content_type=response.get("ContentType"),
                )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                return None

            logger.error(
                "get_object_info_failed",
                bucket=bucket,
                key=key,
                error=str(e),
            )
            raise StorageError(f"Failed to get object info: {e}") from e

    async def ensure_bucket_exists(self, bucket: str) -> None:
        """Ensure a bucket exists, creating it if necessary.

        Args:
            bucket: S3 bucket name.

        Raises:
            StorageError: If bucket creation fails.
        """
        try:
            async with self._get_client() as client:
                try:
                    await client.head_bucket(Bucket=bucket)
                    logger.debug("bucket_exists", bucket=bucket)
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")
                    if error_code in ("404", "NoSuchBucket"):
                        # Create the bucket
                        create_config = {}
                        if self._settings.s3_region != "us-east-1":
                            create_config["CreateBucketConfiguration"] = {
                                "LocationConstraint": self._settings.s3_region
                            }

                        await client.create_bucket(Bucket=bucket, **create_config)
                        logger.info("bucket_created", bucket=bucket)
                    else:
                        raise

        except ClientError as e:
            logger.error(
                "ensure_bucket_failed",
                bucket=bucket,
                error=str(e),
            )
            raise StorageError(f"Failed to ensure bucket exists: {e}") from e
