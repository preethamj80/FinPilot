"""Settings router — financial configuration and data management."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_current_user, AuthenticatedUser
from backend.auth.user_db import get_user_settings, save_user_settings
from backend.schemas.settings import SettingsIn, SettingsOut, LoadDemoResult, ResetResult
import src.database as db

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsOut)
def get_settings(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Retrieve the current user's financial planning settings."""
    s = get_user_settings(current_user.id)
    return SettingsOut(
        opening_balance=float(s.get("opening_balance", 0.0)),
        safety_reserve=float(s.get("safety_reserve", 2000.0)),
        monthly_savings_target=float(s.get("monthly_savings_target", 0.0)),
    )


@router.put("", response_model=SettingsOut)
def update_settings(
    payload: SettingsIn,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Save updated financial planning settings for current user."""
    save_user_settings(current_user.id, {
        "opening_balance": payload.opening_balance,
        "safety_reserve": payload.safety_reserve,
        "monthly_savings_target": payload.monthly_savings_target,
    })
    return get_settings(current_user)


@router.post("/load-demo", response_model=LoadDemoResult)
def load_demo_data(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Populate the database with realistic demo transactions and budgets for current user."""
    try:
        from utils import make_demo_transactions
        demo_rows = make_demo_transactions()
        if not demo_rows:
            return LoadDemoResult(transactions_added=0, message="Demo data generator returned no rows.")

        rows_tuples = [
            (
                str(r.get("txn_date", "")),
                str(r.get("txn_type", "Expense")),
                str(r.get("description", "")),
                float(r.get("amount", 0)),
                str(r.get("category", "Other")),
                str(r.get("notes", "")),
            )
            for r in demo_rows
            if r.get("txn_date") and r.get("description") and float(r.get("amount", 0)) > 0
        ]

        inserted = db.bulk_add_transactions(rows_tuples, user_id=current_user.id)

        from datetime import date
        current_month = date.today().strftime("%Y-%m")
        default_budgets = [
            ("Food & Dining", 5000.0),
            ("Groceries", 4000.0),
            ("Transportation", 3000.0),
            ("Entertainment", 2000.0),
            ("Shopping", 3000.0),
        ]
        for cat, limit in default_budgets:
            try:
                db.save_budget(month=current_month, category=cat, limit_amount=limit, user_id=current_user.id)
            except Exception:
                pass

        return LoadDemoResult(
            transactions_added=inserted,
            message=f"Demo data loaded: {inserted} transactions added, default budgets set for {current_month}.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load demo data: {exc}")


@router.post("/reset-data", response_model=ResetResult)
def reset_data(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Clear ALL transactions, budgets, and bills for current user. Settings are preserved."""
    try:
        db.clear_all_data(user_id=current_user.id)
        return ResetResult(success=True, message="All your transactions, budgets, and bills have been cleared. Settings preserved.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Reset failed: {exc}")
