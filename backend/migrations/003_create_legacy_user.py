"""Migration 003 — Create the legacy system account (user_id = 0).

Existing rows in transactions/budgets/bills already default to user_id = 0.
This migration records the legacy account in the users table so foreign key
integrity is maintained. The legacy account cannot log in (is_active = 0).
"""
from __future__ import annotations
import sqlite3


LEGACY_USER_ID   = 0
LEGACY_EMAIL     = "legacy@finpilot.local"
LEGACY_FULL_NAME = "Legacy Data (Streamlit)"


def up(conn: sqlite3.Connection) -> None:
    # SQLite AUTOINCREMENT starts at 1; we insert with explicit id=0
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?", (LEGACY_EMAIL,)
    ).fetchone()
    if existing:
        return  # Idempotent: already created

    conn.execute("""
        INSERT INTO users (id, full_name, email, password_hash, is_active)
        VALUES (0, ?, ?, '__LEGACY_NO_LOGIN__', 0)
    """, (LEGACY_FULL_NAME, LEGACY_EMAIL))

    # Seed default user_settings for legacy user (mirrors global settings table)
    legacy_settings = [
        (0, "opening_balance",        "0.0"),
        (0, "safety_reserve",         "2000.0"),
        (0, "monthly_savings_target", "0.0"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO user_settings(user_id, setting_key, setting_value) VALUES (?,?,?)",
        legacy_settings,
    )


def verify(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT id, is_active FROM users WHERE email = ?", (LEGACY_EMAIL,)
    ).fetchone()
    if not row:
        print("  [003] Legacy user not found")
        return False
    if row[1] != 0:
        print("  [003] Legacy user is_active should be 0")
        return False
    return True
