"""Pydantic V2 schemas for transaction endpoints."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class TransactionIn(BaseModel):
    txn_date: str = Field(..., description="Transaction date as YYYY-MM-DD")
    txn_type: str = Field(..., description="'Income' or 'Expense'")
    description: str = Field(..., min_length=1, max_length=500)
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    notes: str = Field(default="")

    @field_validator("txn_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("Income", "Expense"):
            raise ValueError("txn_type must be 'Income' or 'Expense'")
        return v

    @field_validator("txn_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("txn_date must be in YYYY-MM-DD format")
        return v


class TransactionOut(BaseModel):
    id: int
    txn_date: str
    txn_type: str
    description: str
    amount: float
    category: str
    notes: str


class TransactionUpdate(BaseModel):
    txn_date: str
    txn_type: str
    description: str
    amount: float = Field(..., gt=0)
    category: str
    notes: str = Field(default="")

    @field_validator("txn_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("Income", "Expense"):
            raise ValueError("txn_type must be 'Income' or 'Expense'")
        return v


class PredictCategoryIn(BaseModel):
    description: str
    txn_type: str = "Expense"


class PredictCategoryOut(BaseModel):
    category: str
    method: str
    confidence: Optional[float] = None


class ConfirmImportIn(BaseModel):
    rows: list[dict[str, Any]]


class CSVImportSummary(BaseModel):
    total_rows: int
    valid_count: int
    skipped_file_dup_count: int
    skipped_db_dup_count: int
    invalid_count: int
    error: Optional[str] = None
    preview: list[dict[str, Any]] = []
    invalid_preview: list[dict[str, Any]] = []
