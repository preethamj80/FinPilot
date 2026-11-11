"""User database operations for authentication."""
from __future__ import annotations

from src.database import get_auth_db_connection


def get_user_by_email(email: str) -> dict | None:
    with get_auth_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email=? COLLATE NOCASE AND is_active=1",
            (email.strip().lower(),),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with get_auth_db_connection() as conn:
        row = conn.execute(
            "SELECT id, full_name, email, created_at, is_active FROM users WHERE id=?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def email_exists(email: str) -> bool:
    with get_auth_db_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE email=? COLLATE NOCASE",
            (email.strip().lower(),),
        ).fetchone()
        return row is not None


def create_user(full_name: str, email: str, password_hash: str) -> int:
    with get_auth_db_connection() as conn:
        cur = conn.execute(
            "INSERT INTO users(full_name, email, password_hash) VALUES (?,?,?)",
            (full_name.strip(), email.strip().lower(), password_hash),
        )
        user_id = cur.lastrowid
        defaults = [
            (user_id, "opening_balance", "0.0"),
            (user_id, "safety_reserve", "2000.0"),
            (user_id, "monthly_savings_target", "0.0"),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO user_settings(user_id, setting_key, setting_value) VALUES (?,?,?)",
            defaults,
        )
        return int(user_id)


def get_user_settings(user_id: int) -> dict[str, float]:
    with get_auth_db_connection() as conn:
        rows = conn.execute(
            "SELECT setting_key, setting_value FROM user_settings WHERE user_id=?",
            (user_id,),
        ).fetchall()
        if rows:
            return {row[0]: float(row[1]) for row in rows}
        rows = conn.execute("SELECT setting_key, setting_value FROM settings").fetchall()
        return {row[0]: float(row[1]) for row in rows}


def save_user_settings(user_id: int, values: dict[str, float]) -> None:
    with get_auth_db_connection() as conn:
        for key, value in values.items():
            conn.execute(
                "INSERT INTO user_settings(user_id, setting_key, setting_value) VALUES (?,?,?) "
                "ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value=excluded.setting_value",
                (user_id, key, str(float(value))),
            )
