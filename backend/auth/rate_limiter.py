"""Brute-force rate limiter — tracks auth attempts per identifier + IP."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import src.config as config

MAX_ATTEMPTS   = 5          # failed attempts before lockout
WINDOW_MINUTES = 15         # rolling window in minutes
LOCKOUT_MINUTES = 15        # how long the lockout lasts


def _db_path():
    return config.DB_PATH


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _window_start() -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)).isoformat()


def record_attempt(identifier: str, ip_address: str | None, success: bool) -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute(
            "INSERT INTO auth_attempts(identifier, ip_address, attempted_at, success) VALUES (?,?,?,?)",
            (identifier.lower(), ip_address, _now_utc(), 1 if success else 0),
        )


def is_locked_out(identifier: str, ip_address: str | None) -> bool:
    """Return True if this identifier/IP has exceeded failed attempt threshold."""
    cutoff = _window_start()
    with sqlite3.connect(_db_path()) as conn:
        # Count failures by identifier in window
        row = conn.execute(
            "SELECT COUNT(*) FROM auth_attempts WHERE identifier=? AND success=0 AND attempted_at>=?",
            (identifier.lower(), cutoff),
        ).fetchone()
        if row and row[0] >= MAX_ATTEMPTS:
            return True
        # Count failures by IP in window (if IP provided)
        if ip_address:
            row_ip = conn.execute(
                "SELECT COUNT(*) FROM auth_attempts WHERE ip_address=? AND success=0 AND attempted_at>=?",
                (ip_address, cutoff),
            ).fetchone()
            if row_ip and row_ip[0] >= MAX_ATTEMPTS * 2:
                return True
    return False


def cleanup_old_attempts() -> None:
    """Prune attempts older than the window to keep table small."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    with sqlite3.connect(_db_path()) as conn:
        conn.execute("DELETE FROM auth_attempts WHERE attempted_at<?", (cutoff,))
