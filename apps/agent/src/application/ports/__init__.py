"""Application ports - Interfaces for external dependencies.

Ports define the contract that adapters must implement.
This enables dependency inversion and testability.
"""

from src.application.ports.llm_port import LLMPort
from src.application.ports.session_repository_port import SessionRepositoryPort
from src.application.ports.stt_port import STTPort
from src.application.ports.tts_port import TTSPort

__all__ = ["LLMPort", "STTPort", "SessionRepositoryPort", "TTSPort"]
