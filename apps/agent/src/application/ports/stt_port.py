"""Speech-to-Text port interface."""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class TranscriptionResult:
    """Result of speech-to-text transcription.

    Attributes:
        text: Transcribed text.
        language: Detected language code.
        confidence: Confidence score (0.0 to 1.0).
        duration_ms: Audio duration in milliseconds.
    """

    text: str
    language: str | None = None
    confidence: float | None = None
    duration_ms: int | None = None


class STTPort(ABC):
    """Port interface for Speech-to-Text services.

    Implementations should handle audio transcription from various sources.
    """

    @abstractmethod
    async def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> TranscriptionResult:
        """Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes (PCM format).
            sample_rate: Audio sample rate in Hz.

        Returns:
            TranscriptionResult: Transcription result with text and metadata.

        Raises:
            STTError: If transcription fails.
        """
        ...
