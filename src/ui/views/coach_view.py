"""AI Money Coach view for FinPilot."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import database as db
from src.services.coach import generate_coach_insights
from src.ui.components import empty_state, format_currency, page_header, render_coach_card


def render_coach_view(tx: pd.DataFrame) -> None:
    """Render the explainable AI Money Coach interface with structured diagnostic cards."""
    page_header(
        "AI Money Coach",
        "Personalized financial guidance, spending anomalies, and potential savings opportunities backed by your local records.",
        badge="LOCAL INTELLIGENCE",
    )

    budgets = db.get_budgets()
    bills = db.get_bills()
    settings = db.get_settings()

    insights = generate_coach_insights(tx, budgets, bills, settings)

    # Top Health Summary Metrics
    tot_impact = sum(r["estimated_monthly_impact"] for r in insights if r["severity"] in ["danger", "warning", "info"])
    danger_count = sum(1 for r in insights if r["severity"] == "danger")
    warning_count = sum(1 for r in insights if r["severity"] == "warning")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Active Diagnostics", len(insights))
    s2.metric("Critical Overruns", danger_count, delta="Immediate action", delta_color="inverse")
    s3.metric("Attention Areas", warning_count, delta="Monitor", delta_color="off")
    s4.metric("Potential Est. Savings", format_currency(tot_impact), delta="Monthly value", delta_color="normal")

    st.divider()

    # Filter selector
    filter_type = st.selectbox(
        "FILTER DIAGNOSTICS BY TOPIC",
        [
            "All Recommendations",
            "Critical Warnings & Overruns",
            "Potential Savings & High-Spend Categories",
            "Subscriptions Worth Reviewing & Upcoming Bills",
        ],
    )

    filtered_insights = []
    for r in insights:
        if filter_type == "Critical Warnings & Overruns":
            if r["severity"] == "danger" or "Warning" in r["rec_type"]:
                filtered_insights.append(r)
        elif filter_type == "Potential Savings & High-Spend Categories":
            if "Savings" in r["rec_type"] or "Opportunity" in r["rec_type"] or "Category" in r["rec_type"]:
                filtered_insights.append(r)
        elif filter_type == "Subscriptions Worth Reviewing & Upcoming Bills":
            if "Subscription" in r["rec_type"] or "Bill" in r["rec_type"]:
                filtered_insights.append(r)
        else:
            filtered_insights.append(r)

    if not filtered_insights:
        empty_state("No Recommendations Match Filter", "Select 'All Recommendations' or record more transactions to discover additional insights.", icon="🔍")
    else:
        for rec in filtered_insights:
            render_coach_card(rec)

    st.caption("ℹ️ **Methodology Note:** All recommendations are computed from actual database records and deterministic financial benchmarks. Savings amounts represent potential estimates based on behavioral adjustments, not guaranteed returns. No personal financial information leaves this computer.")
