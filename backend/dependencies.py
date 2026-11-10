"""FinPilot FastAPI — shared dependencies and per-user DataFrame loaders."""
from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import src.database as db
from backend.auth.user_db import get_user_settings, save_user_settings as _save_us


def get_transactions_df(user_id: int = 0) -> pd.DataFrame:
    """Load all transactions for a specific user."""
    return db.get_transactions(user_id=user_id)


def get_budgets_df(user_id: int = 0, month: str | None = None) -> pd.DataFrame:
    """Load budgets for a specific user."""
    return db.get_budgets(month=month, user_id=user_id)


def get_bills_df(user_id: int = 0) -> pd.DataFrame:
    """Load all bills for a specific user."""
    return db.get_bills(user_id=user_id)


def get_settings_dict(user_id: int = 0) -> dict[str, float]:
    """Load application settings for a specific user."""
    return get_user_settings(user_id)
