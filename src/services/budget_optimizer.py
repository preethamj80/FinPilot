'''Budget Optimizer service.

Provides generation of budget recommendations based on past transaction history.
All calculations are performed on actual user data; no synthetic values are created.
''' 
from __future__ import annotations

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

# Define essential categories – these are typically non‑negotiable expenses.
ESSENTIAL_CATEGORIES = {
    "Rent", "Rent & Housing", "Mortgage", "Utilities", "Insurance", "Tax",
    "Healthcare", "Health & Medical",
}

def _prepare_monthly_data(transactions: pd.DataFrame, months: int) -> pd.DataFrame:
    """Return a DataFrame limited to the most recent *months* full months.
    The DataFrame will have a '_month' column (YYYY-MM) and numeric '_amount'.
    """
    tx = transactions.copy()
    tx["_amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0.0)
    tx["_date"] = pd.to_datetime(tx["txn_date"], errors="coerce")
    tx["_month"] = tx["_date"].dt.strftime("%Y-%m")
    # Determine the most recent full month (ignore current incomplete month)
    current_month = datetime.today().strftime("%Y-%m")
    historical = tx[tx["_month"] < current_month]
    if historical.empty:
        return pd.DataFrame()
    recent_months = sorted(historical["_month"].unique())[-months:]
    return historical[historical["_month"].isin(recent_months)]

def generate_budget_recommendations(
    transactions: pd.DataFrame | None,
    budgets: pd.DataFrame | None,
    bills: pd.DataFrame | None,
    months_history: int = 3,
    savings_target: float | None = None,
    locked_limits: dict[str, float] | None = None,
    budget_month: str | None = None,
) -> List[Dict[str, Any]]:
    """Generate a list of recommendation dicts.

    Each dict matches the BudgetRecommendation schema.
    """
    if transactions is None or transactions.empty:
        # No data – cannot generate real recommendations.
        raise ValueError("Insufficient transaction history to generate budget recommendations.")

    # Prepare recent months transaction data.
    recent_tx = _prepare_monthly_data(transactions, months_history)
    if recent_tx.empty:
        raise ValueError("Not enough completed months of transaction data.")

    # Aggregate income and expenses per month.
    income_tx = recent_tx[recent_tx["txn_type"] == "Income"]
    expense_tx = recent_tx[recent_tx["txn_type"] == "Expense"]
    # Average monthly income.
    avg_income = float(income_tx.groupby("_month")['_amount'].sum().mean()) if not income_tx.empty else 0.0
    # Average spend per category.
    cat_spend = expense_tx.groupby(["_month", "category"])['_amount'].sum().reset_index()
    avg_cat_spend = cat_spend.groupby('category')['_amount'].mean().to_dict()

    # Determine essential spend total.
    essential_spend = sum(v for k, v in avg_cat_spend.items() if k in ESSENTIAL_CATEGORIES)
    discretionary_spend = sum(v for k, v in avg_cat_spend.items() if k not in ESSENTIAL_CATEGORIES)

    # Determine target savings.
    if savings_target is None:
        # Fallback to a modest 10% of income if not configured.
        savings_target = avg_income * 0.10

    if savings_target < 0:
        raise ValueError("Savings target must be zero or greater.")
    if savings_target > avg_income:
        raise ValueError("Savings target cannot exceed the average monthly income in your history.")

    # Reduce flexible spending only when historical outgoings exceed income
    # remaining after the requested savings target.
    required_reduction = max(
        0.0,
        essential_spend + discretionary_spend - (avg_income - savings_target),
    )
    # If reduction is zero, we are already under target.

    # Build recommendations per category.
    recommendations: List[Dict[str, Any]] = []
    locked_limits = locked_limits or {}
    confidence = "High" if recent_tx["_month"].nunique() >= 5 else "Moderate"
    for category, avg_spend in avg_cat_spend.items():
        current_limit = None
        if budgets is not None and not budgets.empty:
            # Find existing budget limit for the latest month in budgets table.
            latest_month = budget_month or budgets["month"].max()
            row = budgets[(budgets["month"] == latest_month) & (budgets["category"] == category)]
            if not row.empty:
                current_limit = float(row.iloc[0]["limit_amount"])
        # Determine recommended limit.
        if category in locked_limits:
            recommended = float(locked_limits[category])
            reason = f"Category locked at ₹{recommended:,.2f}; the optimizer preserves this limit."
        elif category in ESSENTIAL_CATEGORIES:
            # Keep essential limits unchanged; just note they are essential.
            recommended = current_limit if current_limit is not None else avg_spend
            reason = "Essential expense – keep current allocation."
        else:
            # Proportionally reduce based on required_reduction.
            proportion = avg_spend / discretionary_spend if discretionary_spend > 0 else 0
            reduction = required_reduction * proportion
            recommended = max(0.0, avg_spend - reduction)
            reason = f"Potential savings of {reduction:,.0f} by trimming discretionary spend in {category}."
        impact = max(0.0, avg_spend - recommended)
        recommendations.append({
            "category": category,
            "current_limit": current_limit,
            "recommended_limit": round(recommended, 2),
            "reason": reason,
            "impact_estimate": round(impact, 2),
            "confidence": confidence,
            "locked": category in locked_limits,
        })
    # Sort by impact descending.
    recommendations.sort(key=lambda r: r["impact_estimate"], reverse=True)
    return recommendations
