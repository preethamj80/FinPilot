"""Migration 001 — Create authentication tables (users, sessions, auth_attempts).

Non-destructive: only creates new tables. Existing tables are untouched.
Uses individual execute() calls instead of executescript() to stay within
the caller's transaction context.
"""
from __future__ import annotations
import sqlite3


DDL_STATEMENTS = [
    # Users table
    """CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name     TEXT    NOT NULL,
        email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT    NOT NULL,
        created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        is_active     INTEGER NOT NULL DEFAULT 1
    )""",
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email COLLATE NOCASE)",

    # Sessions table
    """CREATE TABLE IF NOT EXISTS sessions (
        session_id  TEXT    PRIMARY KEY,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        csrf_token  TEXT    NOT NULL,
        created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_seen   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at  TEXT    NOT NULL,
        ip_address  TEXT,
        user_agent  TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_sessions_user    ON sessions(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)",

    # Auth attempts (brute-force tracking)
    """CREATE TABLE IF NOT EXISTS auth_attempts (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier   TEXT    NOT NULL,
        ip_address   TEXT,
        attempted_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        success      INTEGER NOT NULL DEFAULT 0
    )""",
    "CREATE INDEX IF NOT EXISTS idx_auth_attempts_id_time ON auth_attempts(identifier, attempted_at)",

    # Per-user settings
    """CREATE TABLE IF NOT EXISTS user_settings (
        user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        setting_key   TEXT    NOT NULL,
        setting_value TEXT    NOT NULL,
        PRIMARY KEY (user_id, setting_key)
    )""",
]


def up(conn: sqlite3.Connection) -> None:
    for stmt in DDL_STATEMENTS:
        conn.execute(stmt)


def verify(conn: sqlite3.Connection) -> bool:
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    required = {"users", "sessions", "auth_attempts", "user_settings"}
    missing = required - tables
    if missing:
        print(f"  [001] MISSING tables: {missing}")
        return False
    return True
