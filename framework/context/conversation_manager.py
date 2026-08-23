from multiprocessing import context
from pyexpat.errors import messages
import uuid
from typing import Literal
from datetime import datetime, timezone
from typing import Literal

from framework.context import db
from framework.models.models import Message
from framework.context.db import init_db, session_exists, insert_session, insert_message, fetch_messages


class SessionNotFoundError(KeyError):
    """Raised when an operation references a session_id that doesn't exist."""


class ConversationManager:
    """
    Manages conversation sessions and their messages, in memory.

    Backed by a dict[session_id -> list[Message]]. No persistence yet —
    SQLite wiring comes on Day 4. Keeping this in-memory-only for now means
    conversation logic can be unit-tested without a database in the loop.
    """

    def __init__(self, db_path: str = "data/context.db") -> None:
        self.db_path = db_path
        init_db(self.db_path)

    def create_session(self) -> str:
        """Create a new, empty session and return its id."""
        session_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        insert_session(self.db_path, session_id=session_id, created_at=created_at)
        return session_id

    def add_message(self, session_id: str, role: Literal["user", "assistant", "system"], content: str) -> Message:
        """
        Construct a Message (auto-populating id/timestamp, token_count=0),
        append it to the session's history, and return it.

        Raises SessionNotFoundError if session_id doesn't exist — silently
        auto-creating would hide bugs from stale session_ids later.
        """
        if  not  session_exists(self.db_path, session_id):
            raise SessionNotFoundError(f"No such session: {session_id}")

        message = Message(session_id=session_id, role=role, content=content)
        insert_message(
            self.db_path,
            message_id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp.isoformat(),
            token_count=message.token_count,
        )
        return message

    def get_history(self, session_id: str) -> list[Message]:
        """
        Return the session's messages in insertion order.

        Returns a copy so callers can't mutate internal state directly.
        Raises SessionNotFoundError if session_id doesn't exist.
        """
        if  not  session_exists(self.db_path, session_id):
            raise SessionNotFoundError(f"No such session: {session_id}")

        rows = fetch_messages(self.db_path, session_id)
        return [
        Message(
            id=row[0],
            session_id=row[1],
            role=row[2],
            content=row[3],
            token_count=row[5] if row[5] is not None else 0,
            timestamp=datetime.fromisoformat(row[4]),
        )
        for row in rows
    ]