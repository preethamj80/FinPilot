"""Database access layer and schema management for FinPilot."""
from __future__ import annotations

import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import pandas as pd

import src.config as config
from src.config import DEFAULT_OPENING_BALANCE, DEFAULT_SAFETY_RESERVE, DEFAULT_MONTHLY_SAVINGS_TARGET


def get_connection(custom_path: Path | str | None = None) -> sqlite3.Connection:
    """Create and return a configured SQLite connection with foreign keys enabled."""
    target_path = Path(custom_path) if custom_path else Path(config.DB_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db_connection(custom_path: Path | str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager that ensures the SQLite connection is committed and closed cleanly."""
    conn = get_connection(custom_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(custom_path: Path | str | None = None) -> None:
    """Initialize database tables and run non-destructive schema migrations."""
    with get_db_connection(custom_path) as conn:
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
                user_id INTEGER DEFAULT 0,
                UNIQUE(user_id, month, category)
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
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                csrf_token TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT
            );
            CREATE TABLE IF NOT EXISTS auth_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                ip_address TEXT,
                attempted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                success INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                setting_key TEXT NOT NULL,
                setting_value TEXT NOT NULL,
                PRIMARY KEY (user_id, setting_key)
            );
            CREATE TABLE IF NOT EXISTS budget_opt_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                month TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                data_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS category_locks (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                month TEXT NOT NULL,
                category TEXT NOT NULL,
                locked_limit REAL,
                PRIMARY KEY (user_id, month, category)
            );
            """
        )

        cursor = conn.cursor()
        # Ensure user_id column on transactions, budgets, bills
        for tbl in ("transactions", "budgets", "bills"):
            t_cols = [r[1] for r in cursor.execute(f"PRAGMA table_info({tbl})").fetchall()]
            if "user_id" not in t_cols:
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN user_id INTEGER DEFAULT 0")

        # Non-destructive migration for bills: ensure frequency and next_due_date columns exist
        cols = [r[1] for r in cursor.execute("PRAGMA table_info(bills)").fetchall()]
        if "frequency" not in cols:
            conn.execute("ALTER TABLE bills ADD COLUMN frequency TEXT NOT NULL DEFAULT 'One-time'")
        if "next_due_date" not in cols:
            conn.execute("ALTER TABLE bills ADD COLUMN next_due_date TEXT DEFAULT ''")

        # Indexes for query performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(txn_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_type ON transactions(txn_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_category ON transactions(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_budgets_month ON budgets(month)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_bills_due ON bills(due_date)")

        # Default settings
        defaults = {
            "opening_balance": str(DEFAULT_OPENING_BALANCE),
            "safety_reserve": str(DEFAULT_SAFETY_RESERVE),
            "monthly_savings_target": str(DEFAULT_MONTHLY_SAVINGS_TARGET),
        }
        for key, value in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(setting_key, setting_value) VALUES (?, ?)",
                (key, value),
            )


# ---------------- Transactions ----------------

def add_transaction(txn_date: str, txn_type: str, description: str, amount: float,
                    category: str, notes: str = "", custom_path: Path | str | None = None,
                    user_id: int = 0) -> int:
    with get_db_connection(custom_path) as conn:
        cur = conn.execute(
            """INSERT INTO transactions(txn_date, txn_type, description, amount, category, notes, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (txn_date, txn_type, description.strip(), float(amount), category, notes.strip(), user_id),
        )
        return int(cur.lastrowid)


def get_transactions(custom_path: Path | str | None = None, user_id: int = 0) -> pd.DataFrame:
    with get_db_connection(custom_path) as conn:
        return pd.read_sql_query(
            "SELECT id, txn_date, txn_type, description, amount, category, notes FROM transactions WHERE user_id=? ORDER BY txn_date DESC, id DESC",
            conn, params=(user_id,),
        )


def update_transaction(txn_id: int, txn_date: str, txn_type: str, description: str,
                       amount: float, category: str, notes: str = "",
                       custom_path: Path | str | None = None, user_id: int = 0) -> None:
    with get_db_connection(custom_path) as conn:
        conn.execute(
            """UPDATE transactions SET txn_date=?, txn_type=?, description=?, amount=?, category=?, notes=?
               WHERE id=? AND user_id=?""",
            (txn_date, txn_type, description.strip(), float(amount), category, notes.strip(), int(txn_id), user_id),
        )


def delete_transaction(txn_id: int, custom_path: Path | str | None = None, user_id: int = 0) -> None:
    with get_db_connection(custom_path) as conn:
        conn.execute("DELETE FROM transactions WHERE id=? AND user_id=?", (int(txn_id), user_id))


def bulk_add_transactions(rows: list[tuple[str, str, str, float, str, str]],
                          custom_path: Path | str | None = None, user_id: int = 0) -> int:
    if not rows:
        return 0
    with get_db_connection(custom_path) as conn:
        before = conn.total_changes
        # rows is (txn_date, txn_type, description, amount, category, notes)
        rows_with_user = [(*r, user_id) for r in rows]
        conn.executemany(
            """INSERT INTO transactions(txn_date, txn_type, description, amount, category, notes, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            rows_with_user,
        )
        return conn.total_changes - before


# ---------------- Budgets ----------------

def save_budget(month: str, category: str, limit_amount: float,
                custom_path: Path | str | None = None, user_id: int = 0) -> None:
    with get_db_connection(custom_path) as conn:
        conn.execute(
            """INSERT INTO budgets(month, category, limit_amount, user_id) VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, month, category) DO UPDATE SET limit_amount=excluded.limit_amount""",
            (month, category, float(limit_amount), user_id),
        )


def get_budgets(month: str | None = None, custom_path: Path | str | None = None, user_id: int = 0) -> pd.DataFrame:
    query = "SELECT id, month, category, limit_amount FROM budgets WHERE user_id=?"
    params: list[Any] = [user_id]
    if month:
        query += " AND month=?"
        params.append(month)
    query += " ORDER BY month DESC, category"
    with get_db_connection(custom_path) as conn:
        return pd.read_sql_query(query, conn, params=tuple(params))


def delete_budget(budget_id: int, custom_path: Path | str | None = None, user_id: int = 0) -> None:
    with get_db_connection(custom_path) as conn:
        conn.execute("DELETE FROM budgets WHERE id=? AND user_id=?", (int(budget_id), user_id))


# ---------------- Bills & Recurring Bills ----------------

def add_bill(description: str, amount: float, due_date: str,
             frequency: str = "One-time", next_due_date: str = "",
             custom_path: Path | str | None = None, user_id: int = 0) -> int:
    with get_db_connection(custom_path) as conn:
        cur = conn.execute(
            """INSERT INTO bills(description, amount, due_date, paid, frequency, next_due_date, user_id)
               VALUES (?, ?, ?, 0, ?, ?, ?)""",
            (description.strip(), float(amount), due_date, frequency, next_due_date, user_id),
        )
        return int(cur.lastrowid)


def get_bills(custom_path: Path | str | None = None, user_id: int = 0) -> pd.DataFrame:
    with get_db_connection(custom_path) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(bills)").fetchall()]
        if "frequency" in cols and "next_due_date" in cols:
            query = "SELECT id, description, amount, due_date, paid, frequency, next_due_date FROM bills WHERE user_id=? ORDER BY due_date"
        else:
            query = "SELECT id, description, amount, due_date, paid, 'One-time' AS frequency, '' AS next_due_date FROM bills WHERE user_id=? ORDER BY due_date"
        return pd.read_sql_query(query, conn, params=(user_id,))


def mark_bill_paid(bill_id: int, paid: bool, custom_path: Path | str | None = None, user_id: int = 0) -> None:
    with get_db_connection(custom_path) as conn:
        conn.execute("UPDATE bills SET paid=? WHERE id=? AND user_id=?", (1 if paid else 0, int(bill_id), user_id))


def update_bill_next_due(bill_id: int, next_due_date: str, custom_path: Path | str | None = None, user_id: int = 0) -> None:
    with get_db_connection(custom_path) as conn:
        conn.execute("UPDATE bills SET next_due_date=? WHERE id=? AND user_id=?", (next_due_date, int(bill_id), user_id))


def delete_bill(bill_id: int, custom_path: Path | str | None = None, user_id: int = 0) -> None:
    with get_db_connection(custom_path) as conn:
        conn.execute("DELETE FROM bills WHERE id=? AND user_id=?", (int(bill_id), user_id))


# ---------------- Settings ----------------

def get_settings(custom_path: Path | str | None = None) -> dict[str, float]:
    with get_db_connection(custom_path) as conn:
        rows = conn.execute("SELECT setting_key, setting_value FROM settings").fetchall()
    return {row["setting_key"]: float(row["setting_value"]) for row in rows}


def save_settings(values: dict[str, float], custom_path: Path | str | None = None) -> None:
    with get_db_connection(custom_path) as conn:
        for key, value in values.items():
            conn.execute(
                "INSERT INTO settings(setting_key, setting_value) VALUES (?, ?) "
                "ON CONFLICT(setting_key) DO UPDATE SET setting_value=excluded.setting_value",
                (key, str(float(value))),
            )


def clear_all_data(custom_path: Path | str | None = None, user_id: int = 0) -> None:
    with get_db_connection(custom_path) as conn:
        conn.execute("DELETE FROM transactions WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM budgets WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM bills WHERE user_id=?", (user_id,))


# ---------------- Budget optimizer state ----------------

def get_category_locks(month: str, user_id: int,
                       custom_path: Path | str | None = None) -> dict[str, float]:
    with get_db_connection(custom_path) as conn:
        rows = conn.execute(
            "SELECT category, locked_limit FROM category_locks WHERE user_id=? AND month=?",
            (user_id, month),
        ).fetchall()
    return {str(row["category"]): float(row["locked_limit"]) for row in rows}


def set_category_lock(month: str, category: str, locked_limit: float | None,
                      user_id: int, custom_path: Path | str | None = None) -> None:
    with get_db_connection(custom_path) as conn:
        if locked_limit is None:
            conn.execute(
                "DELETE FROM category_locks WHERE user_id=? AND month=? AND category=?",
                (user_id, month, category),
            )
        else:
            conn.execute(
                "INSERT INTO category_locks(user_id, month, category, locked_limit) VALUES (?,?,?,?) "
                "ON CONFLICT(user_id, month, category) DO UPDATE SET locked_limit=excluded.locked_limit",
                (user_id, month, category, float(locked_limit)),
            )


def save_budget_optimization(user_id: int, month: str, data: dict[str, Any],
                             custom_path: Path | str | None = None) -> int:
    with get_db_connection(custom_path) as conn:
        cur = conn.execute(
            "INSERT INTO budget_opt_history(user_id, month, data_json) VALUES (?,?,?)",
            (user_id, month, json.dumps(data, ensure_ascii=False)),
        )
        return int(cur.lastrowid)


def _decode_budget_optimization(row: sqlite3.Row) -> dict[str, Any]:
    item = json.loads(row["data_json"])
    item.update({
        "id": int(row["id"]),
        "month": str(row["month"]),
        "generated_at": str(row["created_at"]),
    })
    return item


def get_budget_optimization(optimization_id: int, user_id: int,
                            custom_path: Path | str | None = None) -> dict[str, Any] | None:
    with get_db_connection(custom_path) as conn:
        row = conn.execute(
            "SELECT id, month, created_at, data_json FROM budget_opt_history WHERE id=? AND user_id=?",
            (optimization_id, user_id),
        ).fetchone()
    return _decode_budget_optimization(row) if row else None


def list_budget_optimizations(user_id: int, limit: int = 20,
                              custom_path: Path | str | None = None) -> list[dict[str, Any]]:
    with get_db_connection(custom_path) as conn:
        rows = conn.execute(
            "SELECT id, month, created_at, data_json FROM budget_opt_history "
            "WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, max(1, min(int(limit), 100))),
        ).fetchall()
    return [_decode_budget_optimization(row) for row in rows]


def approve_budget_optimization(optimization_id: int, user_id: int,
                                custom_path: Path | str | None = None) -> tuple[str, dict[str, Any] | None]:
    """Atomically snapshot current values and apply a pending optimization."""
    with get_db_connection(custom_path) as conn:
        row = conn.execute(
            "SELECT id, month, created_at, data_json FROM budget_opt_history WHERE id=? AND user_id=?",
            (optimization_id, user_id),
        ).fetchone()
        if not row:
            return "not_found", None
        data = json.loads(row["data_json"])
        if data.get("status") != "pending":
            return "not_pending", _decode_budget_optimization(row)

        previous: dict[str, float | None] = {}
        for recommendation in data.get("recommendations", []):
            category = recommendation["category"]
            existing = conn.execute(
                "SELECT limit_amount FROM budgets WHERE user_id=? AND month=? AND category=?",
                (user_id, row["month"], category),
            ).fetchone()
            previous[category] = float(existing["limit_amount"]) if existing else None

        for recommendation in data.get("recommendations", []):
            conn.execute(
                "INSERT INTO budgets(month, category, limit_amount, user_id) VALUES (?,?,?,?) "
                "ON CONFLICT(user_id, month, category) DO UPDATE SET limit_amount=excluded.limit_amount",
                (row["month"], recommendation["category"],
                 float(recommendation["recommended_limit"]), user_id),
            )

        from datetime import datetime, timezone
        data["previous_budgets"] = previous
        data["status"] = "approved"
        data["approved_at"] = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE budget_opt_history SET data_json=? WHERE id=? AND user_id=?",
            (json.dumps(data, ensure_ascii=False), optimization_id, user_id),
        )
        result = dict(data)
        result.update({"id": int(row["id"]), "month": str(row["month"]), "generated_at": str(row["created_at"])})
        return "approved", result


def undo_budget_optimization(optimization_id: int, user_id: int,
                              custom_path: Path | str | None = None) -> tuple[str, dict[str, Any] | None]:
    """Restore the exact budget values captured by approval, atomically."""
    with get_db_connection(custom_path) as conn:
        row = conn.execute(
            "SELECT id, month, created_at, data_json FROM budget_opt_history WHERE id=? AND user_id=?",
            (optimization_id, user_id),
        ).fetchone()
        if not row:
            return "not_found", None
        data = json.loads(row["data_json"])
        if data.get("status") != "approved":
            return "not_approved", _decode_budget_optimization(row)

        previous = data.get("previous_budgets", {})
        for recommendation in data.get("recommendations", []):
            category = recommendation["category"]
            current = conn.execute(
                "SELECT limit_amount FROM budgets WHERE user_id=? AND month=? AND category=?",
                (user_id, row["month"], category),
            ).fetchone()
            if current is None or abs(float(current["limit_amount"]) - float(recommendation["recommended_limit"])) > 1e-6:
                return "budgets_changed", _decode_budget_optimization(row)

        for category, old_limit in previous.items():
            if old_limit is None:
                conn.execute(
                    "DELETE FROM budgets WHERE user_id=? AND month=? AND category=?",
                    (user_id, row["month"], category),
                )
            else:
                conn.execute(
                    "UPDATE budgets SET limit_amount=? WHERE user_id=? AND month=? AND category=?",
                    (float(old_limit), user_id, row["month"], category),
                )

        from datetime import datetime, timezone
        data["status"] = "undone"
        data["undone_at"] = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE budget_opt_history SET data_json=? WHERE id=? AND user_id=?",
            (json.dumps(data, ensure_ascii=False), optimization_id, user_id),
        )
        result = dict(data)
        result.update({"id": int(row["id"]), "month": str(row["month"]), "generated_at": str(row["created_at"])})
        return "undone", result
