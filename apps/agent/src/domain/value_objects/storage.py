"""Storage-related value objects.

These value objects represent immutable data structures for S3/object storage
operations.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ObjectInfo:
    """Information about a stored object.

    Attributes:
        bucket: S3 bucket name.
        key: Object key (path) in the bucket.
        size_bytes: Size of the object in bytes.
        last_modified: Timestamp of the last modification.
        content_type: MIME type of the object.
        etag: Entity tag for the object (MD5 hash).
    """

    bucket: str
    key: str
    size_bytes: int
    last_modified: datetime | None = None
    content_type: str | None = None
    etag: str | None = None
