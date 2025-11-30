"""Application ports - Interfaces for external dependencies.

Ports define the contract that adapters must implement.
This enables dependency inversion and testability.
"""

from src.application.ports.egress_port import EgressConfig
from src.application.ports.egress_port import EgressInfo
from src.application.ports.egress_port import EgressPort
from src.application.ports.egress_port import EgressStatus
from src.application.ports.llm_port import LLMPort
from src.application.ports.recording_repository_port import RecordingRepositoryPort
from src.application.ports.session_repository_port import SessionRepositoryPort
from src.application.ports.storage_port import StorageObject
from src.application.ports.storage_port import StoragePort
from src.application.ports.stt_port import STTPort
from src.application.ports.tts_port import TTSPort

__all__ = [
    "EgressConfig",
    "EgressInfo",
    "EgressPort",
    "EgressStatus",
    "LLMPort",
    "RecordingRepositoryPort",
    "STTPort",
    "SessionRepositoryPort",
    "StorageObject",
    "StoragePort",
    "TTSPort",
]
