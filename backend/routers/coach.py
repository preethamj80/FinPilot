"""AI Money Coach router."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

from backend.auth.dependencies import get_current_user, AuthenticatedUser
from backend.dependencies import get_transactions_df, get_budgets_df, get_bills_df, get_settings_dict
from backend.schemas.coach import CoachInsight, CoachResponse
from src.services.coach import generate_coach_insights

router = APIRouter(prefix="/coach", tags=["AI Money Coach"])


@router.get("/insights", response_model=CoachResponse)
def get_coach_insights(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Generate evidence-based financial recommendations for current user."""
    tx_df = get_transactions_df(user_id=current_user.id)
    bud_df = get_budgets_df(user_id=current_user.id)
    bill_df = get_bills_df(user_id=current_user.id)
    settings = get_settings_dict(user_id=current_user.id)

    insights_raw = generate_coach_insights(
        transactions=tx_df if not tx_df.empty else None,
        budgets=bud_df if not bud_df.empty else None,
        bills=bill_df if not bill_df.empty else None,
        settings=settings,
    )

    insights = []
    for item in insights_raw:
        severity = item.get("severity")
        if severity not in {"danger", "warning", "info", "success"}:
            severity = "info"

        priority = item.get("priority")
        if priority not in {"High", "Medium", "Low"}:
            priority = {
                "danger": "High",
                "warning": "Medium",
                "info": "Low",
                "success": "Low",
            }[severity]

        try:
            impact = float(item.get("estimated_monthly_impact") or 0.0)
        except (TypeError, ValueError):
            impact = 0.0

        insights.append(CoachInsight(
            recommendation_type=item.get("rec_type") or "Financial Guidance",
            priority=priority,
            observation=item.get("observation") or "Review your recent financial activity.",
            reason=item.get("why_it_matters") or "This recommendation is based on your recorded financial activity.",
            action=item.get("suggested_action") or "Review the supporting evidence and adjust your plan if needed.",
            impact=impact,
            evidence=item.get("supporting_evidence") or "No supporting transaction details were available.",
            period=item.get("analysis_period") or datetime.now().strftime("%Y-%m"),
            confidence=item.get("confidence") or "Data-Limited",
            type=item.get("type") if item.get("type") in {"rule", "ml"} else "rule",
            severity=severity,
        ))

    return CoachResponse(
        insights=insights,
        generated_at=datetime.now().isoformat(),
    )
