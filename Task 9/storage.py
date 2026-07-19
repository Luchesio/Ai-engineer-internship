import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "sessions.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id         TEXT PRIMARY KEY,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role       TEXT NOT NULL CHECK (role IN ('human', 'ai')),
                content    TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages (session_id, id);
            """
        )


def ensure_session(session_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (id, created_at) VALUES (?, ?)",
            (session_id, time.time()),
        )


def add_message(session_id: str, role: str, content: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, time.time()),
        )


def get_messages(session_id: str, limit: int | None = None) -> list[dict]:
    query = "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id"
    with _connect() as conn:
        rows = conn.execute(query, (session_id,)).fetchall()
    if limit is not None and limit > 0:
        rows = rows[-limit:]
    return [dict(row) for row in rows]


def list_sessions() -> list[dict]:
    query = """
        SELECT s.id, s.created_at, COUNT(m.id) AS message_count
        FROM sessions s
        LEFT JOIN messages m ON m.session_id = s.id
        GROUP BY s.id
        ORDER BY s.created_at
    """
    with _connect() as conn:
        return [dict(row) for row in conn.execute(query).fetchall()]


def session_exists(session_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return row is not None


def delete_session(session_id: str) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    return cur.rowcount > 0