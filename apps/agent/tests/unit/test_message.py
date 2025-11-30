"""Unit tests for Message entity."""

from uuid import UUID
from uuid import uuid4

from src.domain.entities.message import Message
from src.domain.entities.message import MessageRole


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_user_role_value(self) -> None:
        """USER role should have value 'user'."""
        assert MessageRole.USER.value == "user"

    def test_assistant_role_value(self) -> None:
        """ASSISTANT role should have value 'assistant'."""
        assert MessageRole.ASSISTANT.value == "assistant"

    def test_system_role_value(self) -> None:
        """SYSTEM role should have value 'system'."""
        assert MessageRole.SYSTEM.value == "system"


class TestMessage:
    """Tests for Message entity."""

    def test_create_message_with_required_fields(self) -> None:
        """Message should be created with required fields."""
        session_id = uuid4()
        message = Message(
            session_id=session_id,
            role=MessageRole.USER,
            content="Hello, AI!",
        )

        assert message.session_id == session_id
        assert message.role == MessageRole.USER
        assert message.content == "Hello, AI!"

    def test_message_id_is_auto_generated(self) -> None:
        """Message ID should be auto-generated as UUID."""
        message = Message(
            session_id=uuid4(),
            role=MessageRole.USER,
            content="Test message",
        )

        assert message.id is not None
        assert isinstance(message.id, UUID)

    def test_message_id_is_unique(self) -> None:
        """Each message should have a unique ID."""
        session_id = uuid4()
        message1 = Message(
            session_id=session_id,
            role=MessageRole.USER,
            content="First message",
        )
        message2 = Message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content="Second message",
        )

        assert message1.id != message2.id

    def test_created_at_is_auto_generated(self) -> None:
        """created_at should be auto-generated on creation."""
        message = Message(
            session_id=uuid4(),
            role=MessageRole.USER,
            content="Test message",
        )

        assert message.created_at is not None

    def test_message_with_user_role(self) -> None:
        """Message should accept USER role."""
        message = Message(
            session_id=uuid4(),
            role=MessageRole.USER,
            content="User message",
        )

        assert message.role == MessageRole.USER

    def test_message_with_assistant_role(self) -> None:
        """Message should accept ASSISTANT role."""
        message = Message(
            session_id=uuid4(),
            role=MessageRole.ASSISTANT,
            content="Assistant response",
        )

        assert message.role == MessageRole.ASSISTANT

    def test_message_with_system_role(self) -> None:
        """Message should accept SYSTEM role."""
        message = Message(
            session_id=uuid4(),
            role=MessageRole.SYSTEM,
            content="System instruction",
        )

        assert message.role == MessageRole.SYSTEM

    def test_message_content_can_be_empty_string(self) -> None:
        """Message content can be an empty string."""
        message = Message(
            session_id=uuid4(),
            role=MessageRole.USER,
            content="",
        )

        assert message.content == ""

    def test_message_session_id_relationship(self) -> None:
        """Multiple messages can belong to the same session."""
        session_id = uuid4()
        messages = [
            Message(session_id=session_id, role=MessageRole.USER, content="Hello"),
            Message(session_id=session_id, role=MessageRole.ASSISTANT, content="Hi!"),
            Message(session_id=session_id, role=MessageRole.USER, content="How are you?"),
        ]

        for message in messages:
            assert message.session_id == session_id
