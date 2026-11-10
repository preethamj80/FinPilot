"""ML Insights router — forecasting, anomaly detection, categorization, spending patterns."""
from __future__ import annotations

import math
import numpy as np
from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_current_user, AuthenticatedUser
from backend.dependencies import get_transactions_df
from backend.schemas.insights import (
    ForecastResponse,
    AnomalyResponse,
    PatternResponse,
    CategorizationStatus,
)
from backend.schemas.transactions import PredictCategoryIn, PredictCategoryOut
from src.ml.forecasting import evaluate_and_forecast_expenses, forecast_by_category
from src.ml.anomaly import detect_multi_feature_anomalies
from src.ml.clustering import cluster_monthly_spending_advanced

router = APIRouter(prefix="/insights", tags=["ML Insights"])


@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Return next-month expense forecast for current user."""
    tx = get_transactions_df(user_id=current_user.id)
    tx_or_none = tx if not tx.empty else None

    if tx_or_none is None:
        return ForecastResponse(
            overall={"status": "no_data", "message": "No transactions available."},
            by_category=[],
        )

    try:
        overall = evaluate_and_forecast_expenses(tx_or_none)
        if "interval_80" in overall and isinstance(overall["interval_80"], tuple):
            overall["interval_80"] = list(overall["interval_80"])
        if "interval_95" in overall and isinstance(overall["interval_95"], tuple):
            overall["interval_95"] = list(overall["interval_95"])
        if "history" in overall and hasattr(overall["history"], "to_dict"):
            overall["history"] = overall["history"].to_dict(orient="records")

        by_cat = forecast_by_category(tx_or_none)
        if hasattr(by_cat, "to_dict"):
            by_cat = by_cat.to_dict(orient="records")
        elif not isinstance(by_cat, list):
            by_cat = []

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Forecast error: {exc}")

    return ForecastResponse(overall=overall, by_category=by_cat)


@router.get("/anomalies", response_model=AnomalyResponse)
def get_anomalies(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Detect statistically unusual transactions for current user."""
    tx = get_transactions_df(user_id=current_user.id)
    tx_or_none = tx if not tx.empty else None

    try:
        result = detect_multi_feature_anomalies(tx_or_none)
        anomalies_df = result.get("anomalies")
        if anomalies_df is None or (hasattr(anomalies_df, "empty") and anomalies_df.empty):
            return AnomalyResponse(
                anomalies=[],
                total_scanned=result.get("total_screened", 0),
                anomaly_count=0,
            )
        records = []
        for r in anomalies_df.to_dict(orient="records"):
            clean = {}
            for k, v in r.items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    clean[k] = None
                elif isinstance(v, np.integer):
                    clean[k] = int(v)
                elif isinstance(v, np.floating):
                    clean[k] = float(v)
                else:
                    clean[k] = v
            records.append(clean)

        return AnomalyResponse(
            anomalies=records,
            total_scanned=result.get("total_screened", len(tx)),
            anomaly_count=len(records),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Anomaly detection error: {exc}")


@router.get("/patterns", response_model=PatternResponse)
def get_patterns(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Cluster monthly spending patterns using K-Means for current user."""
    tx = get_transactions_df(user_id=current_user.id)
    tx_or_none = tx if not tx.empty else None

    try:
        result = cluster_monthly_spending_advanced(tx_or_none)
        clusters = result.get("clusters", [])
        if hasattr(clusters, "to_dict"):
            clusters = clusters.to_dict(orient="records")
        elif not isinstance(clusters, list):
            clusters = []

        summary = str(result.get("summary", result.get("message", "Pattern analysis complete.")))
        return PatternResponse(clusters=clusters, summary=summary)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pattern analysis error: {exc}")


@router.get("/categorization", response_model=CategorizationStatus)
def get_categorization_status(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Return the current state of the ML transaction categorizer."""
    tx = get_transactions_df(user_id=current_user.id)

    try:
        from src.ml.categorization import train_or_load_categorizer
        if tx.empty:
            raise ValueError("No transactions to train on")
        result = train_or_load_categorizer(tx)
        return CategorizationStatus(
            model_loaded=result.get("status") == "trained",
            training_samples=result.get("record_count", 0),
            model_type=result.get("model_type", "TF-IDF + RandomForest"),
            categories=list(result.get("class_distribution", {}).keys()),
        )
    except Exception:
        from src.config import CATEGORIES
        return CategorizationStatus(
            model_loaded=False,
            training_samples=0,
            model_type="keyword_fallback",
            categories=CATEGORIES,
        )


@router.post("/categorization/test", response_model=PredictCategoryOut)
def test_categorization(
    payload: PredictCategoryIn,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Test-predict a category for a description string."""
    tx = get_transactions_df(user_id=current_user.id)
    try:
        from src.ml.categorization import predict_category
        cat, method, confidence = predict_category(
            description=payload.description,
            txn_type=payload.txn_type,
            transactions=tx if not tx.empty else None,
        )
        return PredictCategoryOut(
            category=cat,
            method=method,
            confidence=confidence,
        )
    except Exception:
        from utils import suggest_category
        return PredictCategoryOut(
            category=suggest_category(payload.description, payload.txn_type),
            method="keyword_fallback",
            confidence=None,
        )
