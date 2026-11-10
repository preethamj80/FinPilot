"""Pydantic V2 schemas for settings endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SettingsIn(BaseModel):
    opening_balance: float = Field(..., ge=0)
    safety_reserve: float = Field(..., ge=0)
    monthly_savings_target: float = Field(..., ge=0)


class SettingsOut(BaseModel):
    opening_balance: float
    safety_reserve: float
    monthly_savings_target: float


class LoadDemoResult(BaseModel):
    transactions_added: int
    message: str


class ResetResult(BaseModel):
    success: bool
    message: str
