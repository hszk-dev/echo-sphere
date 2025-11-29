"""Text-to-Speech port interface."""

from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class AudioChunk:
    """A chunk of synthesized audio.

    Attributes:
        data: Raw audio bytes.
        sample_rate: Audio sample rate in Hz.
        duration_ms: Chunk duration in milliseconds.
    """

    data: bytes
    sample_rate: int = 24000
    duration_ms: int | None = None


class TTSPort(ABC):
    """Port interface for Text-to-Speech services.

    Implementations should handle text-to-audio synthesis.
    """

    @abstractmethod
    async def synthesize(self, text: str, voice_id: str | None = None) -> bytes:
        """Synthesize text to audio.

        Args:
            text: Text to synthesize.
            voice_id: Optional voice identifier.

        Returns:
            bytes: Complete audio data.

        Raises:
            TTSError: If synthesis fails.
        """
        ...

    @abstractmethod
    async def synthesize_stream(
        self, text: str, voice_id: str | None = None
    ) -> AsyncIterator[AudioChunk]:
        """Synthesize text to streaming audio.

        Args:
            text: Text to synthesize.
            voice_id: Optional voice identifier.

        Yields:
            AudioChunk: Chunks of synthesized audio.

        Raises:
            TTSError: If synthesis fails.
        """
        ...
