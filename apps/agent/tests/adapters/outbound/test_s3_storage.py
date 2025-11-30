"""Unit tests for S3StorageAdapter."""

from datetime import UTC
from datetime import datetime
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from src.adapters.outbound.s3_storage import S3StorageAdapter
from src.application.ports.storage_port import StorageError
from src.config.settings import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    settings = MagicMock(spec=Settings)
    settings.s3_endpoint_url = "http://localhost:9000"
    settings.s3_access_key = "test-access-key"
    settings.s3_secret_key = MagicMock()
    settings.s3_secret_key.get_secret_value.return_value = "test-secret-key"
    settings.s3_region = "us-east-1"
    return settings


@pytest.fixture
def adapter(mock_settings: Settings) -> S3StorageAdapter:
    """Create S3StorageAdapter instance for testing."""
    return S3StorageAdapter(mock_settings)


class TestGeneratePresignedUrl:
    """Tests for generate_presigned_url method."""

    async def test_generates_url_successfully(self, adapter: S3StorageAdapter) -> None:
        """Should generate a presigned URL for an object."""
        expected_url = "https://localhost:9000/bucket/key?signature=abc123"

        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_presigned_url.return_value = expected_url
            mock_get_client.return_value.__aenter__.return_value = mock_client

            url = await adapter.generate_presigned_url(
                bucket="test-bucket",
                key="path/to/file.m3u8",
                expiry_seconds=3600,
            )

            assert url == expected_url
            mock_client.generate_presigned_url.assert_called_once_with(
                "get_object",
                Params={"Bucket": "test-bucket", "Key": "path/to/file.m3u8"},
                ExpiresIn=3600,
            )

    async def test_raises_storage_error_on_client_error(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should raise StorageError when client fails."""
        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_presigned_url.side_effect = ClientError(
                {"Error": {"Code": "500", "Message": "Internal error"}},
                "generate_presigned_url",
            )
            mock_get_client.return_value.__aenter__.return_value = mock_client

            with pytest.raises(StorageError, match="Failed to generate presigned URL"):
                await adapter.generate_presigned_url(
                    bucket="test-bucket",
                    key="path/to/file.m3u8",
                )


class TestObjectExists:
    """Tests for object_exists method."""

    async def test_returns_true_when_object_exists(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should return True when object exists."""
        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.head_object.return_value = {"ContentLength": 1024}
            mock_get_client.return_value.__aenter__.return_value = mock_client

            exists = await adapter.object_exists(
                bucket="test-bucket",
                key="existing/file.txt",
            )

            assert exists is True
            mock_client.head_object.assert_called_once_with(
                Bucket="test-bucket",
                Key="existing/file.txt",
            )

    async def test_returns_false_when_object_not_found(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should return False when object does not exist."""
        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.head_object.side_effect = ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}},
                "head_object",
            )
            mock_get_client.return_value.__aenter__.return_value = mock_client

            exists = await adapter.object_exists(
                bucket="test-bucket",
                key="missing/file.txt",
            )

            assert exists is False

    async def test_raises_storage_error_on_other_errors(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should raise StorageError for non-404 errors."""
        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.head_object.side_effect = ClientError(
                {"Error": {"Code": "500", "Message": "Server error"}},
                "head_object",
            )
            mock_get_client.return_value.__aenter__.return_value = mock_client

            with pytest.raises(StorageError, match="Failed to check object existence"):
                await adapter.object_exists(
                    bucket="test-bucket",
                    key="file.txt",
                )


class TestListObjects:
    """Tests for list_objects method."""

    async def test_lists_objects_successfully(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should list objects with the given prefix."""
        now = datetime.now(tz=UTC)
        mock_response = {
            "Contents": [
                {
                    "Key": "prefix/file1.txt",
                    "Size": 1024,
                    "LastModified": now,
                    "ETag": '"etag1"',
                },
                {
                    "Key": "prefix/file2.txt",
                    "Size": 2048,
                    "LastModified": now,
                    "ETag": '"etag2"',
                },
            ]
        }

        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.list_objects_v2.return_value = mock_response
            mock_get_client.return_value.__aenter__.return_value = mock_client

            objects = await adapter.list_objects(
                bucket="test-bucket",
                prefix="prefix/",
                max_keys=100,
            )

            assert len(objects) == 2
            assert objects[0].bucket == "test-bucket"
            assert objects[0].key == "prefix/file1.txt"
            assert objects[0].size_bytes == 1024
            assert objects[0].etag == "etag1"
            assert objects[1].bucket == "test-bucket"
            assert objects[1].key == "prefix/file2.txt"
            assert objects[1].size_bytes == 2048

    async def test_returns_empty_list_when_no_objects(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should return empty list when no objects match prefix."""
        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.list_objects_v2.return_value = {}
            mock_get_client.return_value.__aenter__.return_value = mock_client

            objects = await adapter.list_objects(
                bucket="test-bucket",
                prefix="nonexistent/",
            )

            assert objects == []


class TestDeleteObject:
    """Tests for delete_object method."""

    async def test_deletes_object_successfully(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should delete object without error."""
        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.delete_object.return_value = {}
            mock_get_client.return_value.__aenter__.return_value = mock_client

            # Should not raise
            await adapter.delete_object(
                bucket="test-bucket",
                key="file/to/delete.txt",
            )

            mock_client.delete_object.assert_called_once_with(
                Bucket="test-bucket",
                Key="file/to/delete.txt",
            )

    async def test_raises_storage_error_on_failure(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should raise StorageError when deletion fails."""
        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.delete_object.side_effect = ClientError(
                {"Error": {"Code": "500", "Message": "Error"}},
                "delete_object",
            )
            mock_get_client.return_value.__aenter__.return_value = mock_client

            with pytest.raises(StorageError, match="Failed to delete object"):
                await adapter.delete_object(
                    bucket="test-bucket",
                    key="file.txt",
                )


class TestGetObjectInfo:
    """Tests for get_object_info method."""

    async def test_gets_object_info_successfully(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should return ObjectInfo for existing object."""
        now = datetime.now(tz=UTC)
        mock_response = {
            "ContentLength": 4096,
            "LastModified": now,
            "ETag": '"abc123"',
            "ContentType": "application/octet-stream",
        }

        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.head_object.return_value = mock_response
            mock_get_client.return_value.__aenter__.return_value = mock_client

            info = await adapter.get_object_info(
                bucket="test-bucket",
                key="path/to/file.bin",
            )

            assert info is not None
            assert info.bucket == "test-bucket"
            assert info.key == "path/to/file.bin"
            assert info.size_bytes == 4096
            assert info.etag == "abc123"
            assert info.content_type == "application/octet-stream"

    async def test_returns_none_when_object_not_found(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should return None when object does not exist."""
        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.head_object.side_effect = ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}},
                "head_object",
            )
            mock_get_client.return_value.__aenter__.return_value = mock_client

            info = await adapter.get_object_info(
                bucket="test-bucket",
                key="missing/file.txt",
            )

            assert info is None


class TestEnsureBucketExists:
    """Tests for ensure_bucket_exists method."""

    async def test_does_nothing_when_bucket_exists(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should not create bucket if it already exists."""
        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.head_bucket.return_value = {}
            mock_get_client.return_value.__aenter__.return_value = mock_client

            await adapter.ensure_bucket_exists("existing-bucket")

            mock_client.head_bucket.assert_called_once_with(Bucket="existing-bucket")
            mock_client.create_bucket.assert_not_called()

    async def test_creates_bucket_when_not_exists(
        self, adapter: S3StorageAdapter
    ) -> None:
        """Should create bucket if it does not exist."""
        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.head_bucket.side_effect = ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}},
                "head_bucket",
            )
            mock_client.create_bucket.return_value = {}
            mock_get_client.return_value.__aenter__.return_value = mock_client

            await adapter.ensure_bucket_exists("new-bucket")

            mock_client.create_bucket.assert_called_once_with(Bucket="new-bucket")
