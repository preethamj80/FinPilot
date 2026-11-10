"""What-If Simulator router — four financial scenario endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_current_user, AuthenticatedUser
from backend.dependencies import get_transactions_df, get_budgets_df, get_bills_df, get_settings_dict
from backend.schemas.simulator import (
    MajorPurchaseIn,
    ExpenseReductionIn,
    IncomeReductionIn,
    MonthlySavingsIn,
    SimulatorResult,
)
from src.services.simulator import (
    simulate_major_purchase,
    simulate_expense_reduction,
    simulate_income_reduction,
    simulate_monthly_savings,
)

router = APIRouter(prefix="/simulator", tags=["What-If Simulator"])


def _load_data(user_id: int):
    tx = get_transactions_df(user_id=user_id)
    bud = get_budgets_df(user_id=user_id)
    bill = get_bills_df(user_id=user_id)
    settings = get_settings_dict(user_id=user_id)
    return (
        tx if not tx.empty else None,
        bud if not bud.empty else None,
        bill if not bill.empty else None,
        settings,
    )


@router.post("/major-purchase", response_model=SimulatorResult)
def sim_major_purchase(
    payload: MajorPurchaseIn,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Simulate the impact of a major one-time purchase on financial health."""
    tx, bud, bill, settings = _load_data(current_user.id)
    try:
        result = simulate_major_purchase(
            purchase_amount=payload.purchase_amount,
            category=payload.category,
            planned_date=payload.planned_date,
            transactions=tx,
            budgets=bud,
            bills=bill,
            settings=settings,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return SimulatorResult(scenario="major_purchase", result=result)


@router.post("/expense-reduction", response_model=SimulatorResult)
def sim_expense_reduction(
    payload: ExpenseReductionIn,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Simulate reducing spending in a specific category by a given percentage."""
    tx, bud, bill, settings = _load_data(current_user.id)
    try:
        result = simulate_expense_reduction(
            category=payload.category,
            reduction_pct=payload.reduction_pct,
            duration_months=payload.duration_months,
            transactions=tx,
            budgets=bud,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return SimulatorResult(scenario="expense_reduction", result=result)


@router.post("/income-reduction", response_model=SimulatorResult)
def sim_income_reduction(
    payload: IncomeReductionIn,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Simulate a reduction in monthly income and its impact on spending capacity."""
    tx, bud, bill, settings = _load_data(current_user.id)
    try:
        result = simulate_income_reduction(
            reduction_type="percentage",
            reduction_value=payload.reduction_pct,
            duration_months=payload.duration_months,
            transactions=tx,
            settings=settings,
            bills=bill,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return SimulatorResult(scenario="income_reduction", result=result)


@router.post("/monthly-savings", response_model=SimulatorResult)
def sim_monthly_savings(
    payload: MonthlySavingsIn,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Project corpus growth given a monthly savings contribution over N months."""
    tx, bud, bill, settings = _load_data(current_user.id)
    try:
        result = simulate_monthly_savings(
            monthly_contribution=payload.monthly_contribution,
            duration_months=payload.duration_months,
            initial_savings=payload.initial_savings,
            transactions=tx,
            budgets=bud,
            bills=bill,
            settings=settings,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return SimulatorResult(scenario="monthly_savings", result=result)
