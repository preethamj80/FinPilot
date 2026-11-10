"""Pydantic V2 schemas for overview endpoints."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class BillSummary(BaseModel):
    description: str
    amount: float
    due_date: str


class OverviewSummaryResponse(BaseModel):
    current_cash: float
    opening_balance: float
    total_income: float
    total_expenses: float
    upcoming_bills_total: float
    upcoming_bills_list: list[dict[str, Any]]
    safety_reserve: float
    monthly_savings_target: float
    uncommitted_cash: float
    has_budgets: bool
    total_budget_limit: float
    total_budget_spent: float
    remaining_budget_headroom: Optional[float]
    spendable: float
    daily_spendable: float
    weekly_spendable: float
    days_left: int
    as_of_date: str
    assumptions: list[str]
    current_month_income: Optional[float] = 0.0
    current_month_expenses: Optional[float] = 0.0
    current_month: Optional[str] = None


class CategoryMixItem(BaseModel):
    category: str
    amount: float


class MonthlyTrendItem(BaseModel):
    month: str
    income: float
    expenses: float
    net: float
