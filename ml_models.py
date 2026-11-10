"""Machine-learning and analytical services for FinPilot finance insights.

Maintains full backward compatibility while delegating to hardened src.ml modules.
"""
from __future__ import annotations

import pandas as pd

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
from utils import CATEGORIES, suggest_category


def forecast_next_month(transactions: pd.DataFrame) -> dict:
    """Evaluates Linear Regression against moving-average and naive baselines on chronological holdout."""
    return evaluate_and_forecast_expenses(transactions)


def generate_recommendations(transactions: pd.DataFrame, budgets: pd.DataFrame, bills: pd.DataFrame) -> list[str]:
    """Generate intelligent financial recommendations based on current spending, budgets, and bills."""
    tips: list[str] = []
    now = pd.Timestamp.today()
    month = now.strftime("%Y-%m")
    if transactions is None or transactions.empty:
        return ["Add a few transactions or load the demo dataset to generate spending guidance."]
    tx = transactions.copy()
    tx["txn_date"] = pd.to_datetime(tx["txn_date"], errors="coerce")
    current = tx[(tx["txn_date"].dt.strftime("%Y-%m") == month) & (tx["txn_type"] == "Expense")]

    if budgets is not None and not budgets.empty:
        month_budgets = budgets[budgets["month"] == month]
        for _, b in month_budgets.iterrows():
            spent = float(current.loc[current["category"] == b["category"], "amount"].sum())
            limit = float(b["limit_amount"])
            if limit > 0 and spent >= limit:
                tips.append(
                    f"{b['category']}: spending is ₹{spent:,.0f}, exceeding your ₹{limit:,.0f} budget. "
                    "Pause non-essential purchases in this category."
                )
            elif limit > 0 and spent >= 0.8 * limit:
                tips.append(
                    f"{b['category']}: {spent / limit:.0%} of the monthly budget is utilized. "
                    "Monitor upcoming planned expenses closely."
                )

    if not current.empty:
        top = current.groupby("category")["amount"].sum().sort_values(ascending=False)
        if len(top) and top.iloc[0] > 0:
            tips.append(
                f"Your largest expense category this month is {top.index[0]} at ₹{top.iloc[0]:,.0f}. "
                "Review its transactions for high-impact saving opportunities."
            )

    if bills is not None and not bills.empty:
        unpaid = bills[bills["paid"] == 0]
        if not unpaid.empty:
            due_total = float(unpaid["amount"].sum())
            tips.append(
                f"You have ₹{due_total:,.0f} in unpaid planned bills this cycle. "
                "Keep this liquidity reserved before committing to discretionary purchases."
            )

    if not tips:
        tips.append("No critical budget alerts active. Continue tracking transactions to refine machine learning insights.")

    return tips[:6]
