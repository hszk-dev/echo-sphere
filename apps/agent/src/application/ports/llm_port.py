"""LLM (Large Language Model) port interface."""

from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dataclasses import field


@dataclass
class Message:
    """A message in a conversation.

    Attributes:
        role: Message role (system, user, assistant).
        content: Message content.
    """

    role: str
    content: str


@dataclass
class LLMResponse:
    """Response from LLM.

    Attributes:
        content: Generated text content.
        finish_reason: Reason for completion (stop, length, etc.).
        usage: Token usage statistics.
    """

    content: str
    finish_reason: str | None = None
    usage: dict[str, int] = field(default_factory=dict)


class LLMPort(ABC):
    """Port interface for Large Language Model services.

    Implementations should handle text generation from conversation context.
    """

    @abstractmethod
    async def generate(self, messages: list[Message]) -> LLMResponse:
        """Generate a response from the conversation.

        Args:
            messages: List of conversation messages.

        Returns:
            LLMResponse: Generated response with content and metadata.

        Raises:
            LLMError: If generation fails.
        """
        ...

    @abstractmethod
    async def generate_stream(self, messages: list[Message]) -> AsyncIterator[str]:
        """Generate a streaming response from the conversation.

        Args:
            messages: List of conversation messages.

        Yields:
            str: Chunks of generated text.

        Raises:
            LLMError: If generation fails.
        """
        ...
