"""Domain value objects - Immutable objects with no identity."""

from src.domain.value_objects.egress import EgressConfig
from src.domain.value_objects.egress import EgressInfo
from src.domain.value_objects.egress import EgressStatus
from src.domain.value_objects.storage import ObjectInfo

__all__ = [
    "EgressConfig",
    "EgressInfo",
    "EgressStatus",
    "ObjectInfo",
]
