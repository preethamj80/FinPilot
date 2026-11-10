"""Migration 002 — Add user_id column to transactions, budgets, bills.

Non-destructive: uses ALTER TABLE ADD COLUMN only.
Existing rows get user_id = 0 (legacy account) by default.
"""
from __future__ import annotations
import sqlite3


def up(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    # Helper: check if column exists before adding
    def has_column(table: str, col: str) -> bool:
        cols = [r[1] for r in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
        return col in cols

    if not has_column("transactions", "user_id"):
        conn.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER DEFAULT 0")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_user ON transactions(user_id)")

    if not has_column("budgets", "user_id"):
        conn.execute("ALTER TABLE budgets ADD COLUMN user_id INTEGER DEFAULT 0")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id)")

    if not has_column("bills", "user_id"):
        conn.execute("ALTER TABLE bills ADD COLUMN user_id INTEGER DEFAULT 0")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_bills_user ON bills(user_id)")


def verify(conn: sqlite3.Connection) -> bool:
    cursor = conn.cursor()
    for table in ("transactions", "budgets", "bills"):
        cols = [r[1] for r in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
        if "user_id" not in cols:
            print(f"  [002] MISSING user_id on {table}")
            return False
    return True
