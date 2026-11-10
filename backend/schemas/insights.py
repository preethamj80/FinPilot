"""Pydantic V2 schemas for ML Insights endpoints."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class ForecastResponse(BaseModel):
    overall: dict[str, Any]
    by_category: list[dict[str, Any]]


class AnomalyRecord(BaseModel):
    id: int
    txn_date: str
    description: str
    amount: float
    category: str
    anomaly_score: Optional[float] = None
    flags: Optional[list[str]] = None


class AnomalyResponse(BaseModel):
    anomalies: list[dict[str, Any]]
    total_scanned: int
    anomaly_count: int


class PatternResponse(BaseModel):
    clusters: list[dict[str, Any]]
    summary: str


class CategorizationStatus(BaseModel):
    model_loaded: bool
    training_samples: int
    model_type: str
    categories: list[str]
