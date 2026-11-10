"""Overview router — financial summary, category mix, and monthly trend."""
from __future__ import annotations

from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, Query

from backend.auth.dependencies import get_current_user, AuthenticatedUser
from backend.dependencies import (
    get_transactions_df,
    get_budgets_df,
    get_bills_df,
    get_settings_dict,
)
from backend.schemas.overview import (
    OverviewSummaryResponse,
    CategoryMixItem,
    MonthlyTrendItem,
)
from src.services.safespending import calculate_safe_to_spend

router = APIRouter(prefix="/overview", tags=["Overview"])


@router.get("/summary", response_model=OverviewSummaryResponse)
def get_overview_summary(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Return the full Safe-to-Spend calculation and financial summary."""
    tx_df = get_transactions_df(user_id=current_user.id)
    bud_df = get_budgets_df(user_id=current_user.id)
    bill_df = get_bills_df(user_id=current_user.id)
    settings = get_settings_dict(user_id=current_user.id)

    result = calculate_safe_to_spend(
        transactions=tx_df if not tx_df.empty else None,
        budgets=bud_df if not bud_df.empty else None,
        bills=bill_df if not bill_df.empty else None,
        settings=settings,
    )

    current_month = date.today().strftime("%Y-%m")
    m_inc = 0.0
    m_exp = 0.0
    if not tx_df.empty:
        tx = tx_df.copy()
        tx["_month"] = pd.to_datetime(tx["txn_date"], errors="coerce").dt.strftime("%Y-%m")
        tx["_amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0.0)
        m_inc = float(tx[(tx["_month"] == current_month) & (tx["txn_type"] == "Income")]["_amount"].sum())
        m_exp = float(tx[(tx["_month"] == current_month) & (tx["txn_type"] == "Expense")]["_amount"].sum())

    result["current_month_income"] = m_inc
    result["current_month_expenses"] = m_exp
    result["current_month"] = current_month
    return OverviewSummaryResponse(**result)


@router.get("/category-mix", response_model=list[CategoryMixItem])
def get_category_mix(
    month: str = Query(default=None, description="YYYY-MM filter, 'current', or omit for all time"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Return expense totals grouped by category."""
    tx = get_transactions_df(user_id=current_user.id)
    if tx.empty:
        return []

    expenses = tx[tx["txn_type"] == "Expense"].copy()

    if month == "current":
        month = date.today().strftime("%Y-%m")

    if month and month.lower() != "all":
        expenses["_month"] = pd.to_datetime(expenses["txn_date"], errors="coerce").dt.strftime("%Y-%m")
        expenses = expenses[expenses["_month"] == month]

    if expenses.empty:
        return []

    grouped = (
        expenses.groupby("category")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "amount"})
        .sort_values("amount", ascending=False)
    )
    return [CategoryMixItem(category=row["category"], amount=float(row["amount"])) for _, row in grouped.iterrows()]


@router.get("/monthly-trend", response_model=list[MonthlyTrendItem])
def get_monthly_trend(
    last_months: int = Query(default=12, ge=1, le=60),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Return monthly income, expenses, and net for the last N months."""
    tx = get_transactions_df(user_id=current_user.id)
    if tx.empty:
        return []

    tx["_month"] = pd.to_datetime(tx["txn_date"], errors="coerce").dt.strftime("%Y-%m")
    tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0.0)

    grouped = tx.groupby(["_month", "txn_type"])["amount"].sum().unstack(fill_value=0.0).reset_index()
    grouped.columns.name = None

    if "Income" not in grouped.columns:
        grouped["Income"] = 0.0
    if "Expense" not in grouped.columns:
        grouped["Expense"] = 0.0

    grouped = grouped.sort_values("_month").tail(last_months)
    grouped["net"] = grouped["Income"] - grouped["Expense"]

    result = []
    for _, row in grouped.iterrows():
        result.append(MonthlyTrendItem(
            month=str(row["_month"]),
            income=float(row["Income"]),
            expenses=float(row["Expense"]),
            net=float(row["net"]),
        ))
    return result
