"""Brute-force rate limiter — tracks auth attempts per identifier + IP."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.database import get_auth_db_connection

MAX_ATTEMPTS = 5          # failed attempts before lockout
WINDOW_MINUTES = 15       # rolling window in minutes
LOCKOUT_MINUTES = 15      # how long the lockout lasts


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _window_start() -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)).isoformat()


def record_attempt(identifier: str, ip_address: str | None, success: bool) -> None:
    with get_auth_db_connection() as conn:
        conn.execute(
            "INSERT INTO auth_attempts(identifier, ip_address, attempted_at, success) VALUES (?,?,?,?)",
            (identifier.lower(), ip_address, _now_utc(), 1 if success else 0),
        )


def is_locked_out(identifier: str, ip_address: str | None) -> bool:
    """Return True if this identifier/IP has exceeded failed attempt threshold."""
    cutoff = _window_start()
    with get_auth_db_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM auth_attempts WHERE identifier=? AND success=0 AND attempted_at>=?",
            (identifier.lower(), cutoff),
        ).fetchone()
        if row and row[0] >= MAX_ATTEMPTS:
            return True
        if ip_address:
            row_ip = conn.execute(
                "SELECT COUNT(*) FROM auth_attempts WHERE ip_address=? AND success=0 AND attempted_at>=?",
                (ip_address, cutoff),
            ).fetchone()
            if row_ip and row_ip[0] >= MAX_ATTEMPTS * 2:
                return True
    return False


def cleanup_old_attempts() -> None:
    """Prune attempts older than the window to keep the table tidy."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    with get_auth_db_connection() as conn:
        conn.execute("DELETE FROM auth_attempts WHERE attempted_at<?", (cutoff,))
