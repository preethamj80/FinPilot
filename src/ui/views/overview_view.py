"""Overview Dashboard view for FinPilot."""
from __future__ import annotations

from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import database as db
from ml_models import generate_recommendations
from src.services.budget_service import get_budget_utilization
from src.services.safespending import calculate_safe_to_spend
from src.ui.components import format_currency, hero_banner, page_header, plotly_fintech_theme, empty_state
from src.ui.styles import PALETTE


def render_overview_view(tx: pd.DataFrame) -> None:
    """Render the redesigned Executive Fintech Overview Dashboard."""
    today = date.today()
    month_name = today.strftime("%B %Y")
    current_month_str = today.strftime("%Y-%m")

    budgets = db.get_budgets()
    bills = db.get_bills()
    settings = db.get_settings()

    spend = calculate_safe_to_spend(tx, budgets, bills, settings, as_of_date=today)

    # Top Hero Banner
    hero_banner(
        title=f"Welcome to your Financial Co-Pilot · {month_name}",
        subtitle=f"You have {format_currency(spend['current_cash'])} in total liquid cash. Your safe spending allowance is {format_currency(spend['daily_spendable'])}/day.",
        pill_text="PERSONAL BANKING OVERVIEW",
    )

    # 4 Key Financial Summary Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Available Balance",
        format_currency(spend["current_cash"]),
        help="Opening balance + lifetime income - lifetime expenses",
    )
    c2.metric(
        "Total Income Recorded",
        format_currency(spend["total_income"]),
        delta="Inflows",
        delta_color="normal",
    )
    c3.metric(
        "Total Expenses Recorded",
        format_currency(spend["total_expenses"]),
        delta="-Outflows",
        delta_color="inverse",
    )
    c4.metric(
        "Safe-to-Spend Today",
        format_currency(spend["daily_spendable"]),
        delta=f"{spend['days_left']} days left in month",
        delta_color="off",
    )

    st.write("")

    # Two column layout: Spending Guardrail on Left, Practical Money Moves on Right
    left_col, right_col = st.columns([1.35, 1])

    with left_col:
        st.subheader("🧭 Spending Guardrail & Commitments")
        st.markdown(
            f"""
            <div style="background-color: {PALETTE['bg_card']}; border: 1px solid {PALETTE['border']}; border-radius: 12px; padding: 1.15rem 1.35rem; margin-bottom: 1rem;">
                <div style="color: {PALETTE['text_secondary']}; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Flexible Spending Ceiling</div>
                <div style="font-size: 1.75rem; font-weight: 800; color: {PALETTE['teal_primary']}; margin: 0.2rem 0;">
                    {format_currency(spend['spendable'])}
                </div>
                <div style="color: {PALETTE['text_secondary']}; font-size: 0.85rem;">
                    Approx. <strong>{format_currency(spend['daily_spendable'])}</strong> per day · <strong>{format_currency(spend['weekly_spendable'])}</strong> for the next 7 days
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        commitments_df = pd.DataFrame({
            "Commitment Type": ["Upcoming Unpaid Bills", "Minimum Safety Reserve", "Monthly Savings Target"],
            "Protected Amount": [
                spend["upcoming_bills_total"],
                spend["safety_reserve"],
                spend["monthly_savings_target"],
            ],
        })
        st.dataframe(
            commitments_df,
            hide_index=True,
            use_container_width=True,
            column_config={"Protected Amount": st.column_config.NumberColumn(format="₹%.2f")},
        )

        if not spend["has_budgets"]:
            st.info("💡 No category budgets set for this month. Safe-to-spend is currently bounded strictly by cash commitments. Add budgets in Budgets & Bills for tighter control.")

        if spend["current_cash"] < 0:
            st.warning("⚠️ Total recorded expenses exceed recorded income plus starting balance. Review your entries.")

        with st.expander("🔍 Calculation Breakdown & Assumptions"):
            for asm in spend.get("assumptions", []):
                st.markdown(f"- {asm}")

    with right_col:
        st.subheader("✨ Practical Money Moves")
        recommendations = generate_recommendations(tx, budgets, bills)
        for tip in recommendations:
            st.markdown(
                f"""
                <div style="background-color: {PALETTE['bg_card']}; border: 1px solid {PALETTE['border']}; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.55rem; font-size: 0.88rem; color: {PALETTE['text_primary']};">
                    {tip}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # Visualizations Section
    st.subheader("📊 Financial Trajectory & Expense Mix")
    chart_a, chart_b = st.columns(2)

    if not tx.empty:
        exp = tx[tx["txn_type"] == "Expense"].copy()
        inc = tx[tx["txn_type"] == "Income"].copy()

        with chart_a:
            if not exp.empty:
                cat_df = exp.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
                fig_pie = px.pie(
                    cat_df,
                    names="category",
                    values="amount",
                    hole=0.6,
                    title="Expense Breakdown by Category",
                )
                st.plotly_chart(plotly_fintech_theme(fig_pie), use_container_width=True)
            else:
                empty_state("No Expenses", "Record an expense to see your category mix.")

        with chart_b:
            if not exp.empty:
                exp_monthly = exp.copy()
                exp_monthly["month"] = pd.to_datetime(exp_monthly["txn_date"]).dt.to_period("M").astype(str)
                trend_exp = exp_monthly.groupby("month", as_index=False)["amount"].sum()
                trend_exp["Type"] = "Expenses"

                fig_trend = px.line(
                    trend_exp,
                    x="month",
                    y="amount",
                    markers=True,
                    title="Monthly Spending Trend",
                    labels={"amount": "Amount (₹)", "month": "Month"},
                )
                st.plotly_chart(plotly_fintech_theme(fig_trend), use_container_width=True)
            else:
                empty_state("No Trend Data", "Add multiple months of records to see your spending trend.")
    else:
        empty_state("Your Dashboard is Ready", "Add your first transaction or load clearly labelled demo records from Settings & Data.")
