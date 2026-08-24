"""
Tests proving ConversationManager persists sessions and messages to SQLite
across process/instance boundaries — the Day 4 "done when" criterion.

Uses a dedicated test database, separate from real dev data (data/context.db)
and separate from Day 2's in-memory-focused test file.
"""

import pytest
from pathlib import Path


from framework.context.conversation_manager import ConversationManager, SessionNotFoundError
from framework.budget.tokenCount import count_tokens


TEST_DB_PATH = "data/test_context.db"


@pytest.fixture(scope="module", autouse=True)
def clean_test_db():
    """
    Delete any leftover test DB before this file's tests run, so a full
    test run always starts from a clean slate. Not deleted between
    individual tests within this file — they're expected to coexist in
    the same file (multiple sessions, distinguished by UUID).
    """
    db_file = Path(TEST_DB_PATH)
    if db_file.exists():
        db_file.unlink()
    yield


def test_history_persists_across_new_manager_instance():
    """
    The core persistence proof: two separate ConversationManager objects,
    no shared memory between them, connected only by db_path. If manager_b
    can read what manager_a wrote, storage is doing the actual remembering
    — not Python object state.
    """
    manager_a = ConversationManager(db_path=TEST_DB_PATH)
    session_id = manager_a.create_session()
    manager_a.add_message(session_id, "user", "Hello")
    manager_a.add_message(session_id, "assistant", "Hi there")

    manager_b = ConversationManager(db_path=TEST_DB_PATH)
    history = manager_b.get_history(session_id)

    assert len(history) == 2
    assert history[0].role == "user"
    assert history[0].content == "Hello"
    assert history[1].role == "assistant"
    assert history[1].content == "Hi there"


def test_message_fields_round_trip_correctly():
    """
    Beyond just 'the messages are there' — checks that each field survives
    the datetime -> isoformat string -> datetime round trip intact, and
    that token_count (defaulting to 0) isn't silently dropped or corrupted
    on the way through SQLite and back.
    """
    manager = ConversationManager(db_path=TEST_DB_PATH)
    session_id = manager.create_session()
    original = manager.add_message(session_id, "user", "Check my fields")

    reloaded_manager = ConversationManager(db_path=TEST_DB_PATH)
    history = reloaded_manager.get_history(session_id)
    reloaded = history[0]

    assert reloaded.id == original.id
    assert reloaded.session_id == original.session_id
    assert reloaded.role == original.role
    assert reloaded.content == original.content
    assert reloaded.timestamp == original.timestamp
    assert reloaded.token_count == original.token_count


def test_missing_session_raises_across_new_instance():
    """
    SessionNotFoundError must still fire correctly even when the check is
    now a database lookup (session_exists) instead of a dict membership
    test — same public contract, different mechanism underneath.
    """
    manager = ConversationManager(db_path=TEST_DB_PATH)
    with pytest.raises(SessionNotFoundError):
        manager.get_history("nonexistent-id")


def test_add_message_to_missing_session_raises():
    """
    Mirror of the above, but for add_message — both read and write paths
    need to independently enforce the same 'session must exist' rule.
    """
    manager = ConversationManager(db_path=TEST_DB_PATH)
    with pytest.raises(SessionNotFoundError):
        manager.add_message("nonexistent-id", "user", "should fail")


def test_history_order_is_preserved():
    """
    fetch_messages orders by rowid (insertion order). This confirms that
    ordering guarantee survives the tuple -> Message reconstruction in
    get_history, not just that all messages are present.
    """
    manager = ConversationManager(db_path=TEST_DB_PATH)
    session_id = manager.create_session()
    manager.add_message(session_id, "user", "first")
    manager.add_message(session_id, "assistant", "second")
    manager.add_message(session_id, "user", "third")

    reloaded_manager = ConversationManager(db_path=TEST_DB_PATH)
    history = reloaded_manager.get_history(session_id)

    assert [m.content for m in history] == ["first", "second", "third"]