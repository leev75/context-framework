"""
SQLite-backed persistence for the context framework.

Backed by the stdlib `sqlite3` module — no ORM. Tables are created
idempotently so `init_db()` can be called repeatedly (including once per
`ConversationManager` instantiation) without error.
"""

from email.mime import message
import os
import sqlite3
from typing import Optional


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    role TEXT,
    content TEXT,
    timestamp TEXT,
    token_count INTEGER
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
"""


def _connect(db_path: str) -> sqlite3.Connection:
    """Open a connection to the SQLite database at `db_path`."""
    return sqlite3.connect(db_path)


def init_db(db_path: str = "data/context.db") -> None:
    """
    Create the `data/` directory (if missing) and the sessions/messages
    tables (if they don't already exist). Idempotent.
    """
    directory = os.path.dirname(db_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)
        conn.commit()
    conn.close()


def session_exists(db_path: str, session_id: str) -> bool:
    """Return True if a session with `session_id` exists."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    conn.close()
    return row is not None


def insert_session(db_path: str, *, session_id: str, created_at: str) -> None:
    """Insert a new session row."""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO sessions (id, created_at) VALUES (?, ?)",
            (session_id, created_at),
        )
        conn.commit()
    conn.close()


def insert_message(
    db_path: str,
    *,
    message_id: str,
    session_id: str,
    role: str,
    content: str,
    timestamp: str,
    token_count: Optional[int],
) -> None:
    """Insert a new message row for the given session."""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO messages (id, session_id, role, content, timestamp, token_count)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (message_id, session_id, role, content, timestamp, token_count),
        )
        conn.commit()
    conn.close()


def fetch_messages(db_path: str, session_id: str) -> list[tuple]:
    """
    Return the session's messages in insertion order.

    Each row is a 6-tuple:
        (id, session_id, role, content, timestamp, token_count)
    Ordered by the implicit rowid (insertion order).
    """
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, session_id, role, content, timestamp, token_count"
            " FROM messages WHERE session_id = ? ORDER BY rowid",
            (session_id,),
        ).fetchall()
    conn.close()
    return rows