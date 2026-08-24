import pytest

from framework.context.conversation_manager import (
    ConversationManager,
    SessionNotFoundError,
)
from framework.models.models import Message


def test_create_session_returns_unique_id():
    manager = ConversationManager()
    session_id_1 = manager.create_session()
    session_id_2 = manager.create_session()

    assert isinstance(session_id_1, str) and session_id_1
    assert session_id_1 != session_id_2


def test_add_and_get_history_in_order():
    manager = ConversationManager()
    session_id = manager.create_session()

    manager.add_message(session_id, "user", "Hello")
    manager.add_message(session_id, "assistant", "Hi there")
    manager.add_message(session_id, "user", "How are you?")

    history = manager.get_history(session_id)

    assert len(history) == 3
    assert [m.content for m in history] == ["Hello", "Hi there", "How are you?"]
    assert [m.role for m in history] == ["user", "assistant", "user"]


def test_message_fields_auto_populated():
    manager = ConversationManager()
    session_id = manager.create_session()

    message = manager.add_message(session_id, "user", "Hello")

    assert message.id
    assert message.session_id == session_id
    assert message.timestamp is not None
    assert message.token_count == 0


def test_get_history_returns_copy_not_live_reference():
    manager = ConversationManager()
    session_id = manager.create_session()
    manager.add_message(session_id, "user", "Hello")

    history = manager.get_history(session_id)
    history.append("tampering with internal state")

    assert len(manager.get_history(session_id)) == 1


def test_add_message_unknown_session_raises():
    manager = ConversationManager()
    with pytest.raises(SessionNotFoundError):
        manager.add_message("nonexistent-id", "user", "Hello")


def test_get_history_unknown_session_raises():
    manager = ConversationManager()
    with pytest.raises(SessionNotFoundError):
        manager.get_history("nonexistent-id")


# Example usage OF the Message class and token counting
def test_token_count_is_computed_on_creation():
    message = Message(session_id="s1", role="user", content="Hello, world!")
    assert message.token_count == 4  # matches ground truth from tokenCount tests