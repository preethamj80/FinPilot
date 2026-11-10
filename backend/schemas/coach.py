"""Pydantic response schemas for the AI Money Coach API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class CoachInsight(BaseModel):
    """Stable API shape for a data-backed coach recommendation."""

    recommendation_type: str
    priority: Literal["High", "Medium", "Low"]
    observation: str
    reason: str
    action: str
    impact: float
    evidence: str
    period: str
    confidence: str
    type: Literal["rule", "ml"]
    severity: Literal["danger", "warning", "info", "success"]


class CoachResponse(BaseModel):
    insights: list[CoachInsight]
    generated_at: str
