"""Transparent Safe-to-Spend mathematical engine."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any
import pandas as pd


def calculate_safe_to_spend(
    transactions: pd.DataFrame | None,
    budgets: pd.DataFrame | None,
    bills: pd.DataFrame | None,
    settings: dict[str, float] | None = None,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    """Calculate the safe flexible spending amount with complete mathematical transparency.
    
    Guarantees:
    1. Separately accounts for cash in hand vs. monthly budget caps.
    2. Never double-subtracts expenses that are already logged in transactions.
    3. If no category budgets exist, spendable is determined by liquid cash commitments
       (does NOT incorrectly treat budget as 0).
    4. Handles zero income and negative balance safely without throwing division-by-zero errors.
    """
    today = as_of_date or date.today()
    current_month = today.strftime("%Y-%m")
    settings = settings or {}

    opening_balance = float(settings.get("opening_balance", 0.0))
    safety_reserve = float(settings.get("safety_reserve", 2000.0))
    monthly_savings_target = float(settings.get("monthly_savings_target", 0.0))

    # 1. Total historical inflows and outflows
    total_income = 0.0
    total_expenses = 0.0
    month_expenses = pd.DataFrame()

    if transactions is not None and not transactions.empty:
        tx = transactions.copy()
        tx["_amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0.0)
        tx["_dt"] = pd.to_datetime(tx["txn_date"], errors="coerce")

        total_income = float(tx[tx["txn_type"] == "Income"]["_amount"].sum())
        total_expenses = float(tx[tx["txn_type"] == "Expense"]["_amount"].sum())

        # Current month expenses
        tx["_month"] = tx["_dt"].dt.strftime("%Y-%m")
        month_expenses = tx[(tx["_month"] == current_month) & (tx["txn_type"] == "Expense")]

    # 2. Current Liquid Cash Balance
    current_cash = opening_balance + total_income - total_expenses

    # 3. Upcoming Unpaid Bills (within next 30 days)
    upcoming_bills_total = 0.0
    upcoming_bills_list = []
    horizon = today + timedelta(days=30)

    if bills is not None and not bills.empty:
        b_df = bills.copy()
        b_df["_due"] = pd.to_datetime(b_df["due_date"], errors="coerce").dt.date
        b_df["_amt"] = pd.to_numeric(b_df["amount"], errors="coerce").fillna(0.0)

        # Only UNPAID bills due between today and horizon
        unpaid = b_df[(b_df["paid"] == 0) & (b_df["_due"] >= today) & (b_df["_due"] <= horizon)]
        upcoming_bills_total = float(unpaid["_amt"].sum())
        upcoming_bills_list = unpaid[["description", "amount", "due_date"]].to_dict(orient="records")

    # 4. Cash After Fixed Commitments
    uncommitted_cash = current_cash - upcoming_bills_total - safety_reserve - monthly_savings_target

    # 5. Budget Evaluation for Current Month
    has_budgets = False
    total_budget_limit = 0.0
    total_budget_spent = 0.0
    remaining_budget_headroom = 0.0

    if budgets is not None and not budgets.empty:
        m_budgets = budgets[budgets["month"] == current_month]
        if not m_budgets.empty:
            has_budgets = True
            for _, b in m_budgets.iterrows():
                limit = float(b["limit_amount"])
                total_budget_limit += limit
                cat = b["category"]
                spent_in_cat = 0.0
                if not month_expenses.empty:
                    spent_in_cat = float(month_expenses[month_expenses["category"] == cat]["_amount"].sum())
                total_budget_spent += spent_in_cat
                remaining_budget_headroom += max(0.0, limit - spent_in_cat)

    # 6. Determine Effective Spendable Amount
    # If budgets exist, spendable is bounded by both uncommitted cash and remaining budget.
    # If no budgets exist, spendable is bounded strictly by uncommitted cash.
    if has_budgets:
        spendable = min(max(0.0, uncommitted_cash), remaining_budget_headroom)
    else:
        spendable = max(0.0, uncommitted_cash)

    # 7. Time Pacing (Daily & Weekly)
    # Days remaining in current calendar month (minimum 1 to prevent division by zero)
    next_month_first = date(today.year + (today.month == 12), 1 if today.month == 12 else today.month + 1, 1)
    days_left = max(1, (next_month_first - today).days)

    daily_spendable = spendable / days_left
    weekly_spendable = min(spendable, daily_spendable * 7)

    # 8. Compile Explicit Assumptions and Audit Steps
    assumptions = [
        f"Starting opening balance recorded: ₹{opening_balance:,.2f}",
        f"Lifetime income (₹{total_income:,.2f}) minus lifetime expenses (₹{total_expenses:,.2f}) yields ₹{current_cash:,.2f} liquid cash.",
        f"Unpaid upcoming bills (next 30 days): ₹{upcoming_bills_total:,.2f} reserved.",
        f"Safety reserve floor: ₹{safety_reserve:,.2f} protected.",
        f"Monthly savings target: ₹{monthly_savings_target:,.2f} allocated.",
    ]
    if has_budgets:
        assumptions.append(
            f"Monthly category budgets active: ₹{remaining_budget_headroom:,.2f} unspent headroom across budgeted categories."
        )
    else:
        assumptions.append(
            "No monthly category budgets configured for this month. Spending guardrail is constrained only by cash commitments."
        )

    return {
        "current_cash": current_cash,
        "opening_balance": opening_balance,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "upcoming_bills_total": upcoming_bills_total,
        "upcoming_bills_list": upcoming_bills_list,
        "safety_reserve": safety_reserve,
        "monthly_savings_target": monthly_savings_target,
        "uncommitted_cash": uncommitted_cash,
        "has_budgets": has_budgets,
        "total_budget_limit": total_budget_limit,
        "total_budget_spent": total_budget_spent,
        "remaining_budget_headroom": remaining_budget_headroom if has_budgets else None,
        "spendable": spendable,
        "daily_spendable": daily_spendable,
        "weekly_spendable": weekly_spendable,
        "days_left": days_left,
        "as_of_date": today.isoformat(),
        "assumptions": assumptions,
    }
