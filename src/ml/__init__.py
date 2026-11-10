"""FinPilot machine learning and statistical modeling package."""
from __future__ import annotations

from src.ml.anomaly import detect_anomalies, detect_multi_feature_anomalies
from src.ml.categorization import (
    category_prediction,
    check_training_eligibility,
    predict_category,
    train_or_load_categorizer,
)
from src.ml.clustering import (
    analyze_category_volatility,
    analyze_essential_vs_discretionary,
    cluster_monthly_spending,
    cluster_monthly_spending_advanced,
)
from src.ml.forecasting import (
    evaluate_and_forecast_expenses,
    forecast_by_category,
)

__all__ = [
    "evaluate_and_forecast_expenses",
    "forecast_by_category",
    "train_or_load_categorizer",
    "predict_category",
    "category_prediction",
    "check_training_eligibility",
    "detect_multi_feature_anomalies",
    "detect_anomalies",
    "cluster_monthly_spending_advanced",
    "cluster_monthly_spending",
    "analyze_essential_vs_discretionary",
    "analyze_category_volatility",
]
