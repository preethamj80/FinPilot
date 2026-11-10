"""Authenticated endpoints for generation and approval of budget plans."""
from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.auth.dependencies import AuthenticatedUser, get_current_user
from backend.auth.user_db import get_user_settings
from backend.dependencies import get_bills_df, get_budgets_df, get_transactions_df
from backend.schemas.budget_optimizer import (
    BillCommitment,
    BudgetRecommendation,
    HistoryItem,
    HistoryResponse,
    LockRequest,
    OptimizationActionRequest,
    OptimizeRequest,
    OptimizeResponse,
)
import src.database as db
from src.services.budget_optimizer import generate_budget_recommendations


router = APIRouter(prefix="/budget", tags=["AI Budget Optimizer"])


def _response(item: dict) -> OptimizeResponse:
    return OptimizeResponse(
        optimization_id=int(item["id"]),
        month=str(item["month"]),
        recommendations=[BudgetRecommendation(**row) for row in item.get("recommendations", [])],
        generated_at=str(item["generated_at"]),
        status=item.get("status", "pending"),
        savings_target=item.get("savings_target"),
        unpaid_bills=[BillCommitment(**bill) for bill in item.get("unpaid_bills", [])],
    )


@router.post("/optimize", response_model=OptimizeResponse, status_code=201)
def optimize_budget(
    payload: OptimizeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Generate a real-data proposal. This endpoint never writes budgets."""
    target_month = date.today().strftime("%Y-%m")
    transactions = get_transactions_df(user_id=current_user.id)
    budgets = get_budgets_df(user_id=current_user.id, month=target_month)
    bills = get_bills_df(user_id=current_user.id)
    locks = db.get_category_locks(target_month, current_user.id)
    savings_target = payload.savings_target
    if savings_target is None:
        configured_target = get_user_settings(current_user.id).get("monthly_savings_target", 0.0)
        if configured_target > 0:
            savings_target = configured_target

    try:
        recommendations_raw = generate_budget_recommendations(
            transactions=transactions if not transactions.empty else None,
            budgets=budgets if not budgets.empty else None,
            bills=bills if not bills.empty else None,
            months_history=payload.months_history,
            savings_target=savings_target,
            locked_limits=locks,
            budget_month=target_month,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Show only actual, unpaid bills due this month. These are surfaced as
    # commitments for the user to review; historical bill transactions are not
    # added again to category spend, avoiding double-counting.
    unpaid_bills: list[dict] = []
    if bills is not None and not bills.empty:
        for _, bill in bills.iterrows():
            due_date = str(bill.get("due_date", ""))
            if int(bill.get("paid", 0) or 0) == 0 and due_date[:7] == target_month:
                unpaid_bills.append({
                    "description": str(bill.get("description", "Bill")),
                    "amount": float(bill.get("amount", 0) or 0),
                    "due_date": due_date,
                })

    recommendations = [BudgetRecommendation(**item).model_dump() for item in recommendations_raw]
    data = {
        "recommendations": recommendations,
        "status": "pending",
        "savings_target": savings_target,
        "months_history": payload.months_history,
        "unpaid_bills": unpaid_bills,
    }
    optimization_id = db.save_budget_optimization(current_user.id, target_month, data)
    saved = db.get_budget_optimization(optimization_id, current_user.id)
    return _response(saved)


@router.get("/history", response_model=HistoryResponse)
def get_budget_history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    items = db.list_budget_optimizations(current_user.id, limit=limit)
    return HistoryResponse(
        history=[HistoryItem(**_response(item).model_dump()) for item in items]
    )


@router.patch("/lock")
def set_budget_category_lock(
    payload: LockRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    db.set_category_lock(
        month=payload.month,
        category=payload.category.strip(),
        locked_limit=payload.locked_limit,
        user_id=current_user.id,
    )
    return {
        "month": payload.month,
        "category": payload.category.strip(),
        "locked": payload.locked_limit is not None,
        "locked_limit": payload.locked_limit,
    }


@router.post("/approve")
def approve_budget(
    payload: OptimizationActionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    status, _item = db.approve_budget_optimization(payload.optimization_id, current_user.id)
    if status == "not_found":
        raise HTTPException(status_code=404, detail="Optimization not found.")
    if status == "not_pending":
        raise HTTPException(status_code=409, detail="Only a pending optimization can be approved.")
    return {"optimization_id": payload.optimization_id, "status": "approved"}


@router.post("/undo")
def undo_budget(
    payload: OptimizationActionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    status, _item = db.undo_budget_optimization(payload.optimization_id, current_user.id)
    if status == "not_found":
        raise HTTPException(status_code=404, detail="Optimization not found.")
    if status == "not_approved":
        raise HTTPException(status_code=409, detail="Only an approved optimization can be undone.")
    if status == "budgets_changed":
        raise HTTPException(
            status_code=409,
            detail="Budgets changed after approval. Restore or review them manually before undoing this optimization.",
        )
    return {"optimization_id": payload.optimization_id, "status": "undone"}
