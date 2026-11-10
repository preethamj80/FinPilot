"""Packaging script for FinPilot distribution ZIP."""
from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ZIP_NAME = "FinPilot_Final_College_Project.zip"
ZIP_PATH = BASE_DIR / ZIP_NAME

EXCLUDE_DIRS = {
    ".venv",
    ".git",
    "__pycache__",
    "backups",
    ".pytest_cache",
    ".system_generated",
    ".idea",
    ".vscode",
}

EXCLUDE_FILES = {
    "finance.db",
    "category_model.joblib",
    ZIP_NAME,
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
    ".tmp",
    ".png",
}


def build_distribution_zip() -> Path:
    print(f"Building clean distribution ZIP: {ZIP_PATH} ...")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    included_count = 0
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        # Walk through project root
        for root, dirs, files in os.walk(BASE_DIR):
            rel_root = Path(root).relative_to(BASE_DIR)

            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            # Check if current directory path contains any excluded directory
            parts = rel_root.parts
            if any(p in EXCLUDE_DIRS for p in parts):
                continue

            for f in files:
                if f in EXCLUDE_FILES:
                    continue
                if any(f.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue
                if f.startswith("finance_backup_") or f.endswith(".db"):
                    continue

                full_path = Path(root) / f
                rel_path = full_path.relative_to(BASE_DIR)

                zf.write(full_path, arcname=str(rel_path).replace("\\", "/"))
                included_count += 1

        # Add empty data and models placeholder directories if not present
        zf.writestr("data/.gitkeep", "")
        zf.writestr("models/.gitkeep", "")

    print(f"Package successfully created: {ZIP_PATH} ({os.path.getsize(ZIP_PATH):,} bytes, {included_count} files).")
    return ZIP_PATH


def test_packaged_zip(zip_path: Path) -> bool:
    print("Verifying packaged ZIP in an isolated sandbox...")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        tmp_path = Path(tmp_dir)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_path)

        # 1. Verify required files exist
        required_files = [
            "app.py",
            "database.py",
            "ml_models.py",
            "utils.py",
            "requirements.txt",
            "README.md",
            "src/config.py",
            "src/database.py",
            "src/ml/forecasting.py",
            "src/ml/categorization.py",
            "src/ml/anomaly.py",
            "src/ml/clustering.py",
            "src/services/safespending.py",
            "src/services/simulator.py",
            "src/services/coach.py",
            "src/ui/views/overview_view.py",
            "sample_data/sample_transactions.csv",
        ]
        for rf in required_files:
            if not (tmp_path / rf).exists():
                print(f"FAILED: Missing required file in ZIP: {rf}")
                return False

        # 2. Verify that live finance.db was NOT packaged
        if (tmp_path / "data/finance.db").exists():
            print("FAILED: Live finance.db was accidentally packaged into ZIP!")
            return False

        # 3. Test initializing fresh database in extracted package
        import sqlite3
        fresh_db = tmp_path / "data/finance.db"
        # Import fresh database module pointing to extracted path
        sys_path_entry = str(tmp_path)
        import sys
        sys.path.insert(0, sys_path_entry)
        try:
            import database as pack_db
            pack_db.DB_PATH = fresh_db
            pack_db.init_db()

            if not fresh_db.exists():
                print("FAILED: Packaged app failed to create fresh database on initialization.")
                return False

            conn = sqlite3.connect(fresh_db)
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            conn.close()

            expected_tables = {"transactions", "budgets", "bills", "settings"}
            if not expected_tables.issubset(set(tables)):
                print(f"FAILED: Packaged database missing expected tables: {tables}")
                return False

            print(f"SUCCESS: Packaged application initializes fresh database with tables: {tables}")
        finally:
            if sys_path_entry in sys.path:
                sys.path.remove(sys_path_entry)

    print("All isolation checks PASSED for distribution package.")
    return True


if __name__ == "__main__":
    p = build_distribution_zip()
    ok = test_packaged_zip(p)
    if not ok:
        raise SystemExit(1)
