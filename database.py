"""SQLite persistence for the AI Personal Finance Management System."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "finance.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                txn_date TEXT NOT NULL,
                txn_type TEXT NOT NULL CHECK(txn_type IN ('Income', 'Expense')),
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                category TEXT NOT NULL,
                limit_amount REAL NOT NULL CHECK(limit_amount >= 0),
                UNIQUE(month, category)
            );
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                due_date TEXT NOT NULL,
                paid INTEGER NOT NULL DEFAULT 0,
                frequency TEXT NOT NULL DEFAULT 'One-time',
                next_due_date TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            );
            """
        )
        # Non-destructive migration for bills: ensure frequency and next_due_date exist
        cols = [r[1] for r in conn.execute("PRAGMA table_info(bills)").fetchall()]
        if "frequency" not in cols:
            conn.execute("ALTER TABLE bills ADD COLUMN frequency TEXT NOT NULL DEFAULT 'One-time'")
        if "next_due_date" not in cols:
            conn.execute("ALTER TABLE bills ADD COLUMN next_due_date TEXT DEFAULT ''")

        defaults = {
            "opening_balance": "0",
            "safety_reserve": "2000",
            "monthly_savings_target": "0",
        }
        for key, value in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(setting_key, setting_value) VALUES (?, ?)",
                (key, value),
            )


def add_transaction(txn_date: str, txn_type: str, description: str, amount: float,
                    category: str, notes: str = "") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO transactions(txn_date, txn_type, description, amount, category, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (txn_date, txn_type, description.strip(), float(amount), category, notes.strip()),
        )
        return int(cur.lastrowid)


def get_transactions() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT id, txn_date, txn_type, description, amount, category, notes FROM transactions ORDER BY txn_date DESC, id DESC",
            conn,
        )


def update_transaction(txn_id: int, txn_date: str, txn_type: str, description: str,
                       amount: float, category: str, notes: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            """UPDATE transactions SET txn_date=?, txn_type=?, description=?, amount=?, category=?, notes=?
               WHERE id=?""",
            (txn_date, txn_type, description.strip(), float(amount), category, notes.strip(), int(txn_id)),
        )


def delete_transaction(txn_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE id=?", (int(txn_id),))


def bulk_add_transactions(rows: list[tuple[str, str, str, float, str, str]]) -> int:
    if not rows:
        return 0
    with get_connection() as conn:
        before = conn.total_changes
        conn.executemany(
            """INSERT INTO transactions(txn_date, txn_type, description, amount, category, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            rows,
        )
        return conn.total_changes - before


def save_budget(month: str, category: str, limit_amount: float) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO budgets(month, category, limit_amount) VALUES (?, ?, ?)
               ON CONFLICT(month, category) DO UPDATE SET limit_amount=excluded.limit_amount""",
            (month, category, float(limit_amount)),
        )


def get_budgets(month: str | None = None) -> pd.DataFrame:
    query = "SELECT id, month, category, limit_amount FROM budgets"
    params: tuple[Any, ...] = ()
    if month:
        query += " WHERE month=?"
        params = (month,)
    query += " ORDER BY month DESC, category"
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def delete_budget(budget_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM budgets WHERE id=?", (int(budget_id),))


def add_bill(description: str, amount: float, due_date: str,
             frequency: str = "One-time", next_due_date: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO bills(description, amount, due_date, paid, frequency, next_due_date) VALUES (?, ?, ?, 0, ?, ?)",
            (description.strip(), float(amount), due_date, frequency, next_due_date),
        )


def get_bills() -> pd.DataFrame:
    with get_connection() as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(bills)").fetchall()]
        if "frequency" in cols and "next_due_date" in cols:
            query = "SELECT id, description, amount, due_date, paid, frequency, next_due_date FROM bills ORDER BY due_date"
        else:
            query = "SELECT id, description, amount, due_date, paid, 'One-time' AS frequency, '' AS next_due_date FROM bills ORDER BY due_date"
        return pd.read_sql_query(query, conn)


def mark_bill_paid(bill_id: int, paid: bool) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE bills SET paid=? WHERE id=?", (1 if paid else 0, int(bill_id)))


def delete_bill(bill_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM bills WHERE id=?", (int(bill_id),))


def get_settings() -> dict[str, float]:
    with get_connection() as conn:
        rows = conn.execute("SELECT setting_key, setting_value FROM settings").fetchall()
    return {row["setting_key"]: float(row["setting_value"]) for row in rows}


def save_settings(values: dict[str, float]) -> None:
    with get_connection() as conn:
        for key, value in values.items():
            conn.execute(
                "INSERT INTO settings(setting_key, setting_value) VALUES (?, ?) "
                "ON CONFLICT(setting_key) DO UPDATE SET setting_value=excluded.setting_value",
                (key, str(float(value))),
            )


def clear_all_data() -> None:
    with get_connection() as conn:
        conn.executescript("DELETE FROM transactions; DELETE FROM budgets; DELETE FROM bills;")
