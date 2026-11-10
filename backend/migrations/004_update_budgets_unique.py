"""Migration 004 — Update budgets table unique constraint to (user_id, month, category).

Ensures each user can have their own independent budgets for each month and category.
"""
from __future__ import annotations
import sqlite3


def up(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            limit_amount REAL NOT NULL CHECK(limit_amount >= 0),
            user_id INTEGER DEFAULT 0,
            UNIQUE(user_id, month, category)
        )
    """)
    conn.execute("""
        INSERT INTO budgets_new (id, month, category, limit_amount, user_id)
        SELECT id, month, category, limit_amount, COALESCE(user_id, 0) FROM budgets
    """)
    conn.execute("DROP TABLE budgets")
    conn.execute("ALTER TABLE budgets_new RENAME TO budgets")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_budgets_month ON budgets(month)")
    conn.execute("PRAGMA foreign_keys = ON")


def verify(conn: sqlite3.Connection) -> bool:
    count = conn.execute("SELECT COUNT(*) FROM budgets").fetchone()[0]
    schema = conn.execute("SELECT sql FROM sqlite_master WHERE name='budgets'").fetchone()[0]
    return count >= 5 and "user_id, month, category" in schema
