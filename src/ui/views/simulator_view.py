"""What-If Financial Simulator view for FinPilot."""
from __future__ import annotations

from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import database as db
from src.config import EXPENSE_CATEGORIES
from src.services.simulator import (
    simulate_expense_reduction,
    simulate_income_reduction,
    simulate_major_purchase,
    simulate_monthly_savings,
)
from src.ui.components import format_currency, page_header, plotly_fintech_theme
from src.ui.styles import PALETTE


def render_simulator_view(tx: pd.DataFrame) -> None:
    """Render the What-If Financial Simulator with side-by-side comparisons and scenario modeling."""
    page_header(
        "What-If Financial Simulator",
        "Model the financial consequences of major purchases, category cutbacks, income shocks, or savings goals before committing real money.",
        badge="SCENARIO MODELING",
    )

    budgets = db.get_budgets()
    bills = db.get_bills()
    settings = db.get_settings()

    scenario = st.radio(
        "SELECT SIMULATION SCENARIO",
        [
            "Scenario A: Major Purchase Impact",
            "Scenario B: Category Expense Reduction",
            "Scenario C: Income Reduction Shock",
            "Scenario D: Monthly Savings Accelerator",
        ],
        horizontal=True,
    )

    st.divider()

    # ---------------- Scenario A: Major Purchase Impact ----------------
    if scenario == "Scenario A: Major Purchase Impact":
        st.subheader("🛍️ Scenario A: Major Purchase Impact")
        st.caption("Evaluate whether you can safely afford a planned expenditure (e.g. laptop, furniture, vacation) without jeopardizing upcoming commitments.")

        c1, c2, c3 = st.columns([1.5, 1.2, 1.2])
        p_amount = c1.number_input("Purchase Amount (₹)", min_value=100.0, value=15000.0, step=1000.0)
        p_category = c2.selectbox("Category", EXPENSE_CATEGORIES, index=EXPENSE_CATEGORIES.index("Shopping") if "Shopping" in EXPENSE_CATEGORIES else 0)
        p_date = c3.date_input("Planned Purchase Date", value=date.today())

        sim = simulate_major_purchase(p_amount, p_category, p_date, tx, budgets, bills, settings)

        # Verdict Alert Banner
        if sim["status_color"] == "success":
            st.success(f"**{sim['status']}:** {sim['verdict']}")
        elif sim["status_color"] == "warning":
            st.warning(f"**{sim['status']}:** {sim['verdict']}")
        else:
            st.error(f"**{sim['status']}:** {sim['verdict']}")

        # 4 Key Comparison Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Available Liquid Cash", format_currency(sim["simulated_cash"]), delta=format_currency(sim["cash_impact"]), delta_color="normal")
        m2.metric("Month-End Proj. Cash", format_currency(sim["proj_month_end_sim"]), delta=format_currency(sim["cash_impact"]), delta_color="normal")
        m3.metric(f"{p_category} MTD Spend", format_currency(sim["new_cat_spent"]), delta=f"+{format_currency(p_amount)}", delta_color="inverse")
        if sim["cat_budget_exists"]:
            m4.metric(f"{p_category} Budget Headroom", format_currency(sim["remaining_cat_budget"]), delta=f"-{format_currency(p_amount)}", delta_color="inverse")
        else:
            m4.metric(f"{p_category} Budget", "No limit set", help="No budget ceiling set for this category in Budgets & Bills")

        # Side-by-side Chart
        comp_df = pd.DataFrame({
            "Metric": ["Liquid Cash", "Month-End Projected", f"{p_category} Spend"],
            "Current Baseline": [sim["baseline_cash"], sim["proj_month_end_base"], sim["cat_spent_mtd"]],
            "After Purchase": [sim["simulated_cash"], sim["proj_month_end_sim"], sim["new_cat_spent"]],
        })
        fig = go.Figure(data=[
            go.Bar(name="Current Baseline", x=comp_df["Metric"], y=comp_df["Current Baseline"], marker_color="#0D9488"),
            go.Bar(name="After Purchase", x=comp_df["Metric"], y=comp_df["After Purchase"], marker_color="#3B82F6" if sim["simulated_cash"] >= 0 else "#DC2626"),
        ])
        fig.update_layout(barmode="group", title="Baseline vs. Post-Purchase Comparison (₹)")
        st.plotly_chart(plotly_fintech_theme(fig), use_container_width=True)

        with st.expander("🔍 Simulation Math & Explicit Assumptions"):
            for asm in sim["assumptions"]:
                st.markdown(f"- {asm}")

    # ---------------- Scenario B: Category Expense Reduction ----------------
    elif scenario == "Scenario B: Category Expense Reduction":
        st.subheader("✂️ Scenario B: Category Expense Reduction")
        st.caption("Model the financial benefit of trimming spending in a flexible category over a chosen time horizon.")

        c1, c2, c3 = st.columns(3)
        red_cat = c1.selectbox("Expense Category", EXPENSE_CATEGORIES, index=EXPENSE_CATEGORIES.index("Food") if "Food" in EXPENSE_CATEGORIES else 0)
        red_pct = c2.slider("Reduction Target (%)", min_value=5, max_value=50, value=15, step=5)
        red_duration = c3.selectbox("Simulation Duration", [1, 3, 6, 12], index=1, format_func=lambda d: f"{d} Month(s)")

        sim_b = simulate_expense_reduction(red_cat, float(red_pct), red_duration, tx, budgets)

        st.info(f"💡 **Baseline Insight:** {sim_b['history_note']}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Historical Monthly Spend", format_currency(sim_b["monthly_baseline"]))
        m2.metric("Revised Monthly Spend", format_currency(sim_b["revised_monthly"]), delta=f"-{format_currency(sim_b['monthly_savings'])}/mo", delta_color="normal")
        m3.metric("Estimated Monthly Savings", format_currency(sim_b["monthly_savings"]))
        m4.metric(f"{red_duration}-Month Cumulative", format_currency(sim_b["cumulative_savings"]))

        # Timeline Bar Chart
        months_arr = [f"Month {i}" for i in range(1, red_duration + 1)]
        cum_arr = [sim_b["monthly_savings"] * i for i in range(1, red_duration + 1)]
        fig_b = px.bar(
            x=months_arr,
            y=cum_arr,
            labels={"x": "Timeline", "y": "Potential Cumulative Savings (₹)"},
            title=f"Projected Potential Savings from {red_pct}% Cut in {red_cat}",
        )
        st.plotly_chart(plotly_fintech_theme(fig_b), use_container_width=True)

        with st.expander("🔍 Simulation Math & Explicit Assumptions"):
            for asm in sim_b["assumptions"]:
                st.markdown(f"- {asm}")

    # ---------------- Scenario C: Income Reduction Shock ----------------
    elif scenario == "Scenario C: Income Reduction Shock":
        st.subheader("📉 Scenario C: Income Reduction Shock")
        st.caption("Stress-test how your cash flow holds up if earnings drop due to reduced hours, freelancing variance, or pay cuts.")

        c1, c2, c3 = st.columns(3)
        mode = c1.radio("Reduction Type", ["Percentage (%)", "Fixed Amount (₹)"], horizontal=True)
        type_key = "percentage" if "Percentage" in mode else "fixed"
        val = c2.number_input("Reduction Value", min_value=1.0, value=20.0 if type_key == "percentage" else 5000.0, step=5.0 if type_key == "percentage" else 1000.0)
        dur = c3.selectbox("Duration of Shock", [1, 2, 3, 6, 12], index=2, format_func=lambda d: f"{d} Month(s)")

        sim_c = simulate_income_reduction(type_key, val, dur, tx, settings, bills)

        if sim_c["status_color"] == "success":
            st.success(sim_c["verdict"])
        else:
            st.error(sim_c["verdict"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Baseline Monthly Income", format_currency(sim_c["baseline_income"]))
        m2.metric("Revised Monthly Income", format_currency(sim_c["revised_income"]), delta=f"-{format_currency(sim_c['monthly_reduction'])}", delta_color="inverse")
        m3.metric("Net Monthly Cash Flow", format_currency(sim_c["revised_net_cashflow"]), delta=format_currency(sim_c["monthly_cashflow_diff"]), delta_color="inverse")
        m4.metric(f"Total {dur}-Month Income Loss", format_currency(sim_c["cumulative_income_loss"]))

        cf_df = pd.DataFrame({
            "Scenario": ["Baseline Trajectory", "Simulated Shock"],
            "Monthly Inflow": [sim_c["baseline_income"], sim_c["revised_income"]],
            "Monthly Expenses": [sim_c["baseline_expenses"], sim_c["baseline_expenses"]],
            "Net Surplus / Deficit": [sim_c["baseline_net_cashflow"], sim_c["revised_net_cashflow"]],
        })
        fig_c = px.bar(
            cf_df,
            x="Scenario",
            y=["Monthly Inflow", "Monthly Expenses"],
            barmode="group",
            title="Monthly Cash Inflow vs. Essential Outflow Under Shock (₹)",
        )
        st.plotly_chart(plotly_fintech_theme(fig_c), use_container_width=True)

        with st.expander("🔍 Simulation Math & Explicit Assumptions"):
            for asm in sim_c["assumptions"]:
                st.markdown(f"- {asm}")

    # ---------------- Scenario D: Monthly Savings Accelerator ----------------
    elif scenario == "Scenario D: Monthly Savings Accelerator":
        st.subheader("🌱 Scenario D: Monthly Savings Accelerator")
        st.caption("Plan a systematic monthly savings transfer and project your protected wealth growth over time.")

        c1, c2, c3 = st.columns(3)
        contrib = c1.number_input("Monthly Savings Contribution (₹)", min_value=250.0, value=3000.0, step=500.0)
        s_dur = c2.selectbox("Savings Horizon", [3, 6, 12, 24, 36], index=2, format_func=lambda d: f"{d} Month(s)")
        init_sav = c3.number_input("Starting Protected Reserve (₹)", min_value=0.0, value=float(settings.get("safety_reserve", 2000.0)), step=1000.0)

        sim_d = simulate_monthly_savings(contrib, s_dur, tx, budgets, bills, settings, initial_savings=init_sav)

        if sim_d["status_color"] == "success":
            st.success(sim_d["verdict"])
        else:
            st.warning(sim_d["verdict"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Monthly Allocation", format_currency(sim_d["monthly_contribution"]))
        m2.metric(f"Total Saved ({s_dur} Mos)", format_currency(sim_d["total_contributions"]))
        m3.metric("Projected Total Reserve", format_currency(sim_d["projected_savings_pool"]))
        m4.metric("Revised Safe-to-Spend", format_currency(sim_d["revised_spendable"]), delta=f"-{format_currency(sim_d['monthly_contribution'])}", delta_color="normal")

        t_df = pd.DataFrame(sim_d["timeline"])
        fig_d = px.line(
            t_df,
            x="month",
            y="accumulated_savings",
            markers=True,
            title="Projected Protected Wealth Growth Over Time (₹)",
            labels={"month": "Timeline", "accumulated_savings": "Accumulated Savings (₹)"},
        )
        st.plotly_chart(plotly_fintech_theme(fig_d), use_container_width=True)

        with st.expander("🔍 Simulation Math & Explicit Assumptions"):
            for asm in sim_d["assumptions"]:
                st.markdown(f"- {asm}")
