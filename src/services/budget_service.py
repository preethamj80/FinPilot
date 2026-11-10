"""Budget and recurring bills service for FinPilot."""
from __future__ import annotations

from datetime import date
from typing import Any
import pandas as pd


VALID_FREQUENCIES = ["One-time", "Weekly", "Monthly", "Yearly"]


def compute_next_due_date(current_due_date: str, frequency: str) -> str:
    """Calculate the next chronological due date based on recurring frequency."""
    if frequency not in ["Weekly", "Monthly", "Yearly"]:
        return ""
    try:
        dt = pd.to_datetime(current_due_date).date()
        if frequency == "Weekly":
            return (dt + pd.Timedelta(days=7)).isoformat()
        elif frequency == "Monthly":
            # Add exactly one calendar month using DateOffset
            next_month = (pd.Timestamp(dt) + pd.DateOffset(months=1)).date()
            return next_month.isoformat()
        elif frequency == "Yearly":
            next_year = (pd.Timestamp(dt) + pd.DateOffset(years=1)).date()
            return next_year.isoformat()
    except Exception:
        return ""
    return ""


def process_recurring_bill_on_payment(
    bill_id: int,
    bills_df: pd.DataFrame,
    db_module: Any,
    custom_path: Any = None,
) -> tuple[bool, str]:
    """When a recurring bill is marked paid, idempotently spawn its next upcoming bill.
    
    Returns (created: bool, message: str).
    """
    if bills_df is None or bills_df.empty:
        return False, "Bills table is empty."

    match = bills_df[bills_df["id"] == int(bill_id)]
    if match.empty:
        return False, f"Bill #{bill_id} not found."

    bill = match.iloc[0]
    frequency = str(bill.get("frequency", "One-time")).strip().title()

    if frequency not in ["Weekly", "Monthly", "Yearly"]:
        # One-time bill; no next bill needs to be created
        return False, "One-time bill; no recurring schedule."

    curr_due = str(bill["due_date"])
    next_due = compute_next_due_date(curr_due, frequency)
    if not next_due:
        return False, f"Could not calculate next due date for {curr_due} with frequency {frequency}."

    desc = str(bill["description"]).strip()
    amount = float(bill["amount"])
    u_id = int(bill.get("user_id", 0))

    # Idempotency check: check if a bill with identical description, due_date and user_id already exists
    with db_module.get_connection(custom_path) as conn:
        existing = conn.execute(
            "SELECT id FROM bills WHERE description=? AND due_date=? AND user_id=?",
            (desc, next_due, u_id),
        ).fetchall()
        if existing:
            # Already generated, avoid duplicates
            conn.execute("UPDATE bills SET next_due_date=? WHERE id=?", (next_due, int(bill_id)))
            return False, f"Next {frequency.lower()} bill for '{desc}' on {next_due} already exists (idempotent; skipped duplicate)."

        # Insert new upcoming bill
        cur = conn.execute(
            """INSERT INTO bills(description, amount, due_date, paid, frequency, next_due_date, user_id)
               VALUES (?, ?, ?, 0, ?, '', ?)""",
            (desc, amount, next_due, frequency, u_id),
        )
        new_id = int(cur.lastrowid)

        # Update current bill's pointer
        conn.execute("UPDATE bills SET next_due_date=? WHERE id=?", (next_due, int(bill_id)))

    return True, f"Created next {frequency.lower()} bill #{new_id} for '{desc}' due on {next_due}."


def sync_all_recurring_bills(
    db_module: Any,
    custom_path: Any = None,
) -> list[str]:
    """Scan all paid recurring bills and ensure upcoming instances exist idempotently."""
    bills_df = db_module.get_bills(custom_path)
    if bills_df.empty:
        return []

    logs = []
    # Find paid recurring bills
    paid_recurring = bills_df[
        (bills_df["paid"] == 1) &
        (bills_df["frequency"].isin(["Weekly", "Monthly", "Yearly"]))
    ]

    for _, row in paid_recurring.iterrows():
        created, msg = process_recurring_bill_on_payment(row["id"], bills_df, db_module, custom_path)
        if created:
            logs.append(msg)

    return logs


def get_budget_utilization(
    budgets_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    current_month: str,
) -> pd.DataFrame:
    """Calculate budget limits, actual expenditures, and remaining headroom for a month."""
    if budgets_df is None or budgets_df.empty:
        return pd.DataFrame(columns=["category", "limit_amount", "spent", "remaining", "pct_used", "status"])

    month_budgets = budgets_df[budgets_df["month"] == current_month].copy()
    if month_budgets.empty:
        return pd.DataFrame(columns=["category", "limit_amount", "spent", "remaining", "pct_used", "status"])

    month_expenses = pd.DataFrame()
    if transactions_df is not None and not transactions_df.empty:
        tx = transactions_df.copy()
        tx["_m"] = pd.to_datetime(tx["txn_date"], errors="coerce").dt.strftime("%Y-%m")
        month_expenses = tx[(tx["_m"] == current_month) & (tx["txn_type"] == "Expense")]

    rows = []
    for _, b in month_budgets.iterrows():
        cat = b["category"]
        limit = float(b["limit_amount"])
        spent = 0.0
        if not month_expenses.empty:
            spent = float(month_expenses[month_expenses["category"] == cat]["amount"].sum())

        remaining = max(0.0, limit - spent)
        pct = (spent / limit) * 100 if limit > 0 else 0.0

        if limit > 0 and spent > limit:
            status = "Exceeded"
        elif limit > 0 and spent >= 0.8 * limit:
            status = "Warning"
        else:
            status = "On Track"

        rows.append({
            "category": cat,
            "limit_amount": limit,
            "spent": spent,
            "remaining": remaining,
            "pct_used": pct,
            "status": status,
        })

    return pd.DataFrame(rows).sort_values("pct_used", ascending=False)
