"""Migration runner — backup → verify → migrate → verify → rollback on failure.

Usage (from project root):
    .venv_backend\\Scripts\\python.exe backend/migrations/run_migrations.py
"""
from __future__ import annotations

import importlib
import logging
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Project root on sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import DB_PATH, BACKUPS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("migration")


def _backup(db_path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUPS_DIR / f"finance_backup_PRE_AUTH_{ts}.db"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db_path, dest)
    log.info(f"Backup created: {dest}")
    return dest


def _integrity_check(conn: sqlite3.Connection) -> bool:
    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        log.error(f"Integrity check FAILED: {result}")
        return False
    log.info("Integrity check: ok")
    return True


def _row_counts(conn: sqlite3.Connection) -> dict:
    counts = {}
    for table in ("transactions", "budgets", "bills", "settings"):
        try:
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except Exception:
            counts[table] = "N/A"
    return counts


def run():
    if not DB_PATH.exists():
        log.error(f"Database not found: {DB_PATH}")
        sys.exit(1)

    log.info(f"Database: {DB_PATH}")

    # 1. Backup first
    backup_path = _backup(DB_PATH)

    # 2. Open connection
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # 3. Integrity check
    if not _integrity_check(conn):
        conn.close()
        log.error("Aborting migration due to integrity check failure.")
        sys.exit(1)

    # 4. Row counts before migration
    before = _row_counts(conn)
    log.info(f"Row counts before: {before}")

    # 5. Load migration modules
    _mig_dir = Path(__file__).parent
    migration_files = [
        ("001_add_auth_tables",     "backend.migrations.001_add_auth_tables"),
        ("002_add_user_id_columns", "backend.migrations.002_add_user_id_columns"),
        ("003_create_legacy_user",  "backend.migrations.003_create_legacy_user"),
    ]

    for name, module_path in migration_files:
        log.info(f"Running migration: {name}")
        try:
            mod = importlib.import_module(module_path)
            # Use a fresh connection with autocommit off for each migration
            # executescript() in 001 issues implicit COMMITs, so we verify after
            mod.up(conn)
            conn.commit()
            if not mod.verify(conn):
                raise RuntimeError(f"Verification failed for {name}")
            log.info(f"  {name}: SUCCESS ✓")
        except Exception as exc:
            try:
                conn.rollback()
            except Exception:
                pass
            conn.close()
            log.error(f"  {name}: FAILED — {exc}")
            log.error(f"Database unchanged. Backup available at: {backup_path}")
            sys.exit(1)

    # 6. Row counts after — existing data must be preserved
    after = _row_counts(conn)
    log.info(f"Row counts after:  {after}")

    for table in ("transactions", "budgets", "bills"):
        b = before.get(table, "N/A")
        a = after.get(table, "N/A")
        if b != a:
            conn.close()
            log.error(f"Row count MISMATCH for '{table}': was {b}, now {a}")
            log.error(f"Restore from backup: {backup_path}")
            sys.exit(1)

    conn.close()
    log.info("=" * 50)
    log.info("All migrations completed successfully.")
    log.info(f"Backup retained at: {backup_path}")
    log.info("=" * 50)


if __name__ == "__main__":
    run()
