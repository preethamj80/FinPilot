"""Server-side session management backed by SQLite sessions table."""
from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import src.config as config
from backend.auth.csrf import generate_csrf_token

SESSION_DURATION_DAYS = 7     # sliding window expiry
SESSION_MAX_DAYS      = 30    # absolute maximum

COOKIE_NAME = "finpilot_session"


def _db_path():
    return config.DB_PATH


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expiry(days: int = SESSION_DURATION_DAYS) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def create_session(user_id: int, ip_address: str | None, user_agent: str | None) -> tuple[str, str]:
    """Create a new session. Returns (session_id, csrf_token)."""
    session_id = secrets.token_urlsafe(32)
    csrf_token = generate_csrf_token()
    with sqlite3.connect(_db_path()) as conn:
        conn.execute(
            """INSERT INTO sessions(session_id, user_id, csrf_token, created_at, last_seen, expires_at, ip_address, user_agent)
               VALUES (?,?,?,?,?,?,?,?)""",
            (session_id, user_id, csrf_token, _now_utc(), _now_utc(), _expiry(), ip_address, user_agent),
        )
    return session_id, csrf_token


def get_session(session_id: str) -> dict | None:
    """Look up a session. Returns session dict or None if missing/expired."""
    now = _now_utc()
    with sqlite3.connect(_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id=? AND expires_at>?",
            (session_id, now),
        ).fetchone()
        if not row:
            return None
        # Slide the expiry (but never beyond SESSION_MAX_DAYS from created_at)
        created = datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00"))
        max_expiry = created + timedelta(days=SESSION_MAX_DAYS)
        new_expiry = min(datetime.now(timezone.utc) + timedelta(days=SESSION_DURATION_DAYS), max_expiry)
        conn.execute(
            "UPDATE sessions SET last_seen=?, expires_at=? WHERE session_id=?",
            (_now_utc(), new_expiry.isoformat(), session_id),
        )
        return dict(row)


def destroy_session(session_id: str) -> None:
    """Delete a session (logout)."""
    with sqlite3.connect(_db_path()) as conn:
        conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))


def destroy_all_user_sessions(user_id: int) -> None:
    """Delete all sessions for a user (logout everywhere)."""
    with sqlite3.connect(_db_path()) as conn:
        conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))


def prune_expired_sessions() -> None:
    """Remove expired sessions to keep the table tidy."""
    with sqlite3.connect(_db_path()) as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at<?", (_now_utc(),))
