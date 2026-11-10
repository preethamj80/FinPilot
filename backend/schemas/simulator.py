"""Pydantic V2 schemas for What-If Simulator endpoints."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class MajorPurchaseIn(BaseModel):
    purchase_amount: float = Field(..., gt=0)
    category: str = Field(default="Shopping")
    planned_date: Optional[str] = None


class ExpenseReductionIn(BaseModel):
    category: str
    reduction_pct: float = Field(..., ge=0, le=100,
                                 description="Percentage to cut from that category spending")
    duration_months: int = Field(default=6, ge=1, le=120)


class IncomeReductionIn(BaseModel):
    reduction_pct: float = Field(..., ge=0, le=100,
                                 description="Percentage income reduction to simulate")
    duration_months: int = Field(default=6, ge=1, le=120)


class MonthlySavingsIn(BaseModel):
    monthly_contribution: float = Field(..., ge=0,
                                        description="Monthly savings amount in ₹")
    duration_months: int = Field(default=12, ge=1, le=120)
    initial_savings: float = Field(default=0.0, ge=0)


class SimulatorResult(BaseModel):
    scenario: str
    result: dict[str, Any]
