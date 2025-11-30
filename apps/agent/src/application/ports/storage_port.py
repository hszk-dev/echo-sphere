"""Storage port interface for S3/object storage operations."""

from abc import ABC
from abc import abstractmethod

from src.domain.value_objects import ObjectInfo


class StorageError(Exception):
    """Base exception for storage operations."""

    pass


class ObjectNotFoundError(StorageError):
    """Raised when an object is not found."""

    pass


class StoragePort(ABC):
    """Port interface for object storage operations.

    Implementations handle S3/MinIO storage operations.
    """

    @abstractmethod
    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiry_seconds: int = 3600,
    ) -> str:
        """Generate a presigned URL for accessing an object.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.
            expiry_seconds: URL expiry time in seconds.

        Returns:
            Presigned URL for the object.

        Raises:
            StorageError: If URL generation fails.
        """
        ...

    @abstractmethod
    async def get_object_info(self, bucket: str, key: str) -> ObjectInfo | None:
        """Get information about a stored object.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.

        Returns:
            Object information if found, None otherwise.

        Raises:
            StorageError: If the lookup fails.
        """
        ...

    @abstractmethod
    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.

        Returns:
            True if object exists, False otherwise.

        Raises:
            StorageError: If the check fails.
        """
        ...

    @abstractmethod
    async def delete_object(self, bucket: str, key: str) -> None:
        """Delete an object from storage.

        Args:
            bucket: S3 bucket name.
            key: Object key/path.

        Raises:
            StorageError: If deletion fails.
        """
        ...

    @abstractmethod
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
        ...
