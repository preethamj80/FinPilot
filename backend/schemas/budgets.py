"""Pydantic V2 schemas for budget and bill endpoints."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class BudgetIn(BaseModel):
    month: str = Field(..., description="Budget month as YYYY-MM")
    category: str
    limit_amount: float = Field(..., ge=0)


class BudgetOut(BaseModel):
    id: int
    month: str
    category: str
    limit_amount: float


class BudgetUtilizationRow(BaseModel):
    category: str
    limit_amount: float
    spent: float
    remaining: float
    pct_used: float
    status: str


class BudgetsResponse(BaseModel):
    budgets: list[BudgetOut]
    utilization: list[BudgetUtilizationRow]
    current_month: str


class BillIn(BaseModel):
    description: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    due_date: str = Field(..., description="YYYY-MM-DD")
    frequency: str = Field(default="One-time")
    next_due_date: str = Field(default="")


class BillOut(BaseModel):
    id: int
    description: str
    amount: float
    due_date: str
    paid: int
    frequency: str
    next_due_date: str


class BillPayResult(BaseModel):
    success: bool
    message: str
    next_bill_created: bool
    next_bill_message: str
