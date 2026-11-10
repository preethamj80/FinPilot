"""Budgets and Bills router."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_current_user, AuthenticatedUser
from backend.dependencies import get_transactions_df, get_budgets_df, get_bills_df
from backend.schemas.budgets import (
    BudgetIn,
    BudgetOut,
    BudgetUtilizationRow,
    BudgetsResponse,
    BillIn,
    BillOut,
    BillPayResult,
)
import src.database as db
from src.services.budget_service import get_budget_utilization, process_recurring_bill_on_payment

router = APIRouter(tags=["Budgets & Bills"])

# ─── Budgets ─────────────────────────────────────────────────────────────────

@router.get("/budgets", response_model=BudgetsResponse)
def list_budgets(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Return all budgets with real-time utilization for current user."""
    current_month = date.today().strftime("%Y-%m")
    bud_df = get_budgets_df(user_id=current_user.id)
    tx_df = get_transactions_df(user_id=current_user.id)

    utilization_df = get_budget_utilization(bud_df, tx_df, current_month)

    budgets = []
    if not bud_df.empty:
        for _, row in bud_df.iterrows():
            budgets.append(BudgetOut(
                id=int(row["id"]),
                month=str(row["month"]),
                category=str(row["category"]),
                limit_amount=float(row["limit_amount"]),
            ))

    utilization = []
    if not utilization_df.empty:
        for _, row in utilization_df.iterrows():
            utilization.append(BudgetUtilizationRow(
                category=str(row["category"]),
                limit_amount=float(row["limit_amount"]),
                spent=float(row["spent"]),
                remaining=float(row["remaining"]),
                pct_used=float(row["pct_used"]),
                status=str(row["status"]),
            ))

    return BudgetsResponse(
        budgets=budgets,
        utilization=utilization,
        current_month=current_month,
    )


@router.post("/budgets", response_model=BudgetOut, status_code=201)
def create_budget(
    payload: BudgetIn,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Create or update a budget for current user (upsert)."""
    db.save_budget(
        month=payload.month,
        category=payload.category,
        limit_amount=payload.limit_amount,
        user_id=current_user.id,
    )
    bud_df = get_budgets_df(user_id=current_user.id, month=payload.month)
    row = bud_df[(bud_df["month"] == payload.month) & (bud_df["category"] == payload.category)]
    if row.empty:
        raise HTTPException(status_code=500, detail="Budget saved but not found.")
    r = row.iloc[0]
    return BudgetOut(
        id=int(r["id"]),
        month=str(r["month"]),
        category=str(r["category"]),
        limit_amount=float(r["limit_amount"]),
    )


@router.delete("/budgets/{budget_id}", status_code=200)
def delete_budget(
    budget_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete a budget entry by ID for current user."""
    bud_df = get_budgets_df(user_id=current_user.id)
    if bud_df.empty or bud_df[bud_df["id"] == budget_id].empty:
        raise HTTPException(status_code=404, detail=f"Budget #{budget_id} not found.")
    db.delete_budget(budget_id, user_id=current_user.id)
    return {"deleted": budget_id, "message": f"Budget #{budget_id} deleted."}


# ─── Bills ───────────────────────────────────────────────────────────────────

@router.get("/bills", response_model=list[BillOut])
def list_bills(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Return all bills for current user sorted by due date."""
    bills_df = get_bills_df(user_id=current_user.id)
    if bills_df.empty:
        return []
    result = []
    for _, row in bills_df.iterrows():
        result.append(BillOut(
            id=int(row["id"]),
            description=str(row["description"]),
            amount=float(row["amount"]),
            due_date=str(row["due_date"]),
            paid=int(row["paid"]),
            frequency=str(row.get("frequency", "One-time")),
            next_due_date=str(row.get("next_due_date", "")),
        ))
    return result


@router.post("/bills", response_model=BillOut, status_code=201)
def create_bill(
    payload: BillIn,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Add a new bill or recurring bill for current user."""
    new_id = db.add_bill(
        description=payload.description,
        amount=payload.amount,
        due_date=payload.due_date,
        frequency=payload.frequency,
        next_due_date=payload.next_due_date,
        user_id=current_user.id,
    )
    bills_df = get_bills_df(user_id=current_user.id)
    row = bills_df[bills_df["id"] == new_id]
    if row.empty:
        raise HTTPException(status_code=500, detail="Bill created but not found.")
    r = row.iloc[0]
    return BillOut(
        id=int(r["id"]),
        description=str(r["description"]),
        amount=float(r["amount"]),
        due_date=str(r["due_date"]),
        paid=int(r["paid"]),
        frequency=str(r.get("frequency", "One-time")),
        next_due_date=str(r.get("next_due_date", "")),
    )


@router.patch("/bills/{bill_id}/pay", response_model=BillPayResult)
def pay_bill(
    bill_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Mark a bill as paid and auto-schedule next recurring bill for current user."""
    bills_df = get_bills_df(user_id=current_user.id)
    if bills_df.empty or bills_df[bills_df["id"] == bill_id].empty:
        raise HTTPException(status_code=404, detail=f"Bill #{bill_id} not found.")

    db.mark_bill_paid(bill_id, paid=True, user_id=current_user.id)

    bills_df_fresh = get_bills_df(user_id=current_user.id)
    created, msg = process_recurring_bill_on_payment(bill_id, bills_df_fresh, db)

    return BillPayResult(
        success=True,
        message=f"Bill #{bill_id} marked as paid.",
        next_bill_created=created,
        next_bill_message=msg,
    )


@router.delete("/bills/{bill_id}", status_code=200)
def delete_bill(
    bill_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete a bill by ID for current user."""
    bills_df = get_bills_df(user_id=current_user.id)
    if bills_df.empty or bills_df[bills_df["id"] == bill_id].empty:
        raise HTTPException(status_code=404, detail=f"Bill #{bill_id} not found.")
    db.delete_bill(bill_id, user_id=current_user.id)
    return {"deleted": bill_id, "message": f"Bill #{bill_id} deleted."}
