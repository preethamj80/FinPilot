"""Request and response models for the real-data budget optimizer."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class BudgetRecommendation(BaseModel):
    category: str
    current_limit: Optional[float] = None
    recommended_limit: float
    reason: str
    impact_estimate: float
    confidence: Literal["High", "Moderate", "Low"]
    locked: bool = False


class BillCommitment(BaseModel):
    description: str
    amount: float
    due_date: str


class OptimizeRequest(BaseModel):
    months_history: int = Field(3, ge=3, le=6)
    savings_target: Optional[float] = Field(default=None, ge=0)


class OptimizeResponse(BaseModel):
    optimization_id: int
    month: str
    recommendations: list[BudgetRecommendation]
    generated_at: str
    status: Literal["pending", "approved", "undone"] = "pending"
    savings_target: Optional[float] = None
    unpaid_bills: list[BillCommitment] = Field(default_factory=list)


class LockRequest(BaseModel):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    category: str = Field(min_length=1, max_length=100)
    locked_limit: Optional[float] = Field(default=None, ge=0)


class OptimizationActionRequest(BaseModel):
    optimization_id: int = Field(gt=0)


class HistoryItem(OptimizeResponse):
    pass


class HistoryResponse(BaseModel):
    history: list[HistoryItem]
