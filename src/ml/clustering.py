"""Spending pattern analysis and K-Means clustering with data sufficiency checks

and essential vs. discretionary behavioral fallbacks.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.config import EXPENSE_CATEGORIES

ESSENTIAL_CATEGORIES = {"Rent", "Groceries", "Utilities", "Health", "Education", "Transport"}
DISCRETIONARY_CATEGORIES = {"Food", "Shopping", "Entertainment", "Travel", "Personal Care", "Subscriptions", "Other"}


def analyze_essential_vs_discretionary(transactions: pd.DataFrame) -> dict:
    """Breakdown spending into Essential (Needs) vs Discretionary (Wants)."""
    if transactions is None or transactions.empty:
        return {"status": "no_data", "total": 0.0, "essential": 0.0, "discretionary": 0.0}

    df = transactions[transactions["txn_type"] == "Expense"].copy()
    if df.empty:
        return {"status": "no_data", "total": 0.0, "essential": 0.0, "discretionary": 0.0}

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["is_essential"] = df["category"].isin(ESSENTIAL_CATEGORIES)

    total = float(df["amount"].sum())
    essential = float(df[df["is_essential"]]["amount"].sum())
    discretionary = float(df[~df["is_essential"]]["amount"].sum())

    essential_pct = round((essential / total) * 100, 1) if total > 0 else 0.0
    discretionary_pct = round((discretionary / total) * 100, 1) if total > 0 else 0.0

    # Monthly breakdown
    df["month"] = pd.to_datetime(df["txn_date"], errors="coerce").dt.to_period("M").astype(str)
    monthly_breakdown = []
    for month, group in df.groupby("month"):
        m_total = float(group["amount"].sum())
        m_ess = float(group[group["is_essential"]]["amount"].sum())
        m_disc = float(group[~group["is_essential"]]["amount"].sum())
        monthly_breakdown.append({
            "month": month,
            "total": round(m_total, 2),
            "essential": round(m_ess, 2),
            "discretionary": round(m_disc, 2),
            "essential_pct": round((m_ess / m_total) * 100, 1) if m_total > 0 else 0.0,
            "discretionary_pct": round((m_disc / m_total) * 100, 1) if m_total > 0 else 0.0,
        })

    return {
        "status": "computed",
        "total": round(total, 2),
        "essential": round(essential, 2),
        "discretionary": round(discretionary, 2),
        "essential_pct": essential_pct,
        "discretionary_pct": discretionary_pct,
        "monthly_history": pd.DataFrame(monthly_breakdown).sort_values("month", ascending=False) if monthly_breakdown else pd.DataFrame(),
    }


def analyze_category_volatility(transactions: pd.DataFrame) -> pd.DataFrame:
    """Analyze Coefficient of Variation (CV = sigma / mu) per category across months

    to classify spending stability (Fixed vs Moderate vs Volatile).
    """
    if transactions is None or transactions.empty:
        return pd.DataFrame(columns=["category", "monthly_avg", "std_dev", "cv", "stability_class"])

    df = transactions[transactions["txn_type"] == "Expense"].copy()
    if df.empty:
        return pd.DataFrame(columns=["category", "monthly_avg", "std_dev", "cv", "stability_class"])

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["month"] = pd.to_datetime(df["txn_date"], errors="coerce").dt.to_period("M").astype(str)
    monthly = df.groupby(["month", "category"])["amount"].sum().unstack(fill_value=0.0)

    rows = []
    for cat in monthly.columns:
        series = monthly[cat]
        avg = float(series.mean())
        std = float(series.std(ddof=1)) if len(series) > 1 else 0.0
        cv = (std / avg) if avg > 0 else 0.0

        if cv < 0.15:
            stability = "Fixed / Highly Predictable"
        elif cv <= 0.40:
            stability = "Moderate Variance"
        else:
            stability = "Volatile / Spike-Prone"

        rows.append({
            "category": cat,
            "monthly_avg": round(avg, 2),
            "std_dev": round(std, 2),
            "cv": round(cv, 2),
            "stability_class": stability,
            "is_essential": cat in ESSENTIAL_CATEGORIES,
        })

    res_df = pd.DataFrame(rows)
    if not res_df.empty:
        res_df = res_df.sort_values("monthly_avg", ascending=False).reset_index(drop=True)
    return res_df


def cluster_monthly_spending_advanced(transactions: pd.DataFrame) -> dict:
    """Perform K-Means clustering on monthly category spending profiles when sufficient

    historical data (>= 6 months) is available. Otherwise, provides statistically
    sound fallbacks (Needs vs Wants ratio and category volatility analysis).
    """
    ess_disc = analyze_essential_vs_discretionary(transactions)
    volatility = analyze_category_volatility(transactions)

    if transactions is None or transactions.empty:
        return {
            "status": "no_data",
            "message": "No transaction data available for spending pattern analysis.",
            "clusters": pd.DataFrame(),
            "archetypes": [],
            "essential_vs_discretionary": ess_disc,
            "category_volatility": volatility,
            "n_months": 0,
            "k": 0,
        }

    df = transactions[transactions["txn_type"] == "Expense"].copy()
    if df.empty:
        return {
            "status": "no_data",
            "message": "Add expenses to discover monthly spending patterns.",
            "clusters": pd.DataFrame(),
            "archetypes": [],
            "essential_vs_discretionary": ess_disc,
            "category_volatility": volatility,
            "n_months": 0,
            "k": 0,
        }

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["month"] = pd.to_datetime(df["txn_date"], errors="coerce").dt.to_period("M").astype(str)
    pivot = df.pivot_table(index="month", columns="category", values="amount", aggfunc="sum", fill_value=0.0)
    n_months = len(pivot)

    # Statistical sufficiency check: K-Means requires at least 6 distinct calendar months
    if n_months < 6:
        reason = (
            f"K-Means clustering deferred: {n_months} calendar month(s) recorded. At least 6 distinct months "
            f"are required to detect recurring behavioral spending archetypes without overfitting small datasets."
        )
        return {
            "status": "insufficient_history",
            "message": reason,
            "clusters": pd.DataFrame(),
            "archetypes": [],
            "essential_vs_discretionary": ess_disc,
            "category_volatility": volatility,
            "n_months": n_months,
            "k": 0,
        }

    # Adequate data: choose K <= n_months / 2
    k = 2 if n_months < 9 else 3

    # Normalize spending vectors with StandardScaler so large expenses don't dominate
    scaler = StandardScaler()
    scaled_matrix = scaler.fit_transform(pivot.values)

    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(scaled_matrix)

    result = pivot.copy()
    result["total_spend"] = pivot.sum(axis=1)
    result["cluster"] = labels

    # Compute discretionary percentage per month
    disc_cols = [c for c in pivot.columns if c in DISCRETIONARY_CATEGORIES]
    result["discretionary_spend"] = pivot[disc_cols].sum(axis=1) if disc_cols else 0.0
    result["discretionary_pct"] = (result["discretionary_spend"] / result["total_spend"]) * 100

    # Sort clusters by average total spending to assign intuitive archetypes
    cluster_means = result.groupby("cluster")["total_spend"].mean().sort_values()
    archetype_map = {}
    archetypes_summary = []

    for rank, (c_id, mean_amt) in enumerate(cluster_means.items()):
        c_rows = result[result["cluster"] == c_id]
        mean_disc_pct = float(c_rows["discretionary_pct"].mean())
        if rank == 0:
            name = "Low-Spend / High-Savings Month"
            desc = "Below-average overall spending; tight budget discipline and minimal discretionary outlays."
        elif rank == len(cluster_means) - 1:
            name = "Peak Discretionary Month"
            desc = "Higher total outlays driven by elevated dining, shopping, travel, or seasonal commitments."
        else:
            name = "Balanced Routine Month"
            desc = "Predictable monthly cash flow matching standard recurring lifestyle obligations."

        archetype_map[c_id] = name
        archetypes_summary.append({
            "cluster_id": int(c_id),
            "archetype": name,
            "average_total": round(float(mean_amt), 2),
            "discretionary_share": round(mean_disc_pct, 1),
            "month_count": len(c_rows),
            "description": desc,
        })

    result["pattern"] = result["cluster"].map(archetype_map)
    result["archetype"] = result["pattern"]

    return {
        "status": "clustered",
        "message": f"K-Means grouped {n_months} monthly cycles into {k} spending archetypes using standardized category vectors.",
        "clusters": result.reset_index(),
        "archetypes": archetypes_summary,
        "essential_vs_discretionary": ess_disc,
        "category_volatility": volatility,
        "n_months": n_months,
        "k": k,
    }


def cluster_monthly_spending(transactions: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Backward-compatible wrapper returning (clusters_df, message)."""
    res = cluster_monthly_spending_advanced(transactions)
    if res["status"] != "clustered" or res["clusters"].empty:
        return pd.DataFrame(), res["message"]
    return res["clusters"], res["message"]
