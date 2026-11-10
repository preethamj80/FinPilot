"""Settings and Data Management view for FinPilot."""
from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
import streamlit as st

import database as db
from src.ui.components import format_currency, page_header
from utils import make_demo_transactions


def render_settings_view(tx: pd.DataFrame) -> None:
    """Render the Settings & Data Management page."""
    page_header(
        "Settings & Data Management",
        "Configure baseline financial planning assumptions, download database backups, or load synthetic demonstration records.",
        badge="CONFIGURATION",
    )

    settings = db.get_settings()

    # Financial Assumptions Form
    st.subheader("Financial Planning Assumptions")
    with st.form("settings_form"):
        opening = st.number_input(
            "Current Starting Balance (₹)",
            min_value=0.0,
            value=float(settings.get("opening_balance", 0.0)),
            step=500.0,
            help="Your bank checking/cash balance when you began using FinPilot.",
        )
        reserve = st.number_input(
            "Minimum Safety Reserve Floor (₹)",
            min_value=0.0,
            value=float(settings.get("safety_reserve", 2000.0)),
            step=500.0,
            help="Minimum emergency cushion to protect from discretionary spending.",
        )
        savings = st.number_input(
            "Monthly Savings Target (₹)",
            min_value=0.0,
            value=float(settings.get("monthly_savings_target", 0.0)),
            step=500.0,
            help="Monthly income earmarked for long-term savings goals.",
        )
        save_btn = st.form_submit_button("Save Planning Assumptions", type="primary")

    if save_btn:
        db.save_settings({"opening_balance": opening, "safety_reserve": reserve, "monthly_savings_target": savings})
        st.success("Planning assumptions updated. Safe-to-Spend has been recalculated.")
        st.rerun()

    st.divider()

    # Demo Data Loader
    st.subheader("Synthetic Demonstration Data")
    st.caption("Generate 12 months of realistic, clearly-labeled synthetic records for presentations and evaluations.")

    if st.button("Load 12 Months of Synthetic Demo Records", type="secondary", use_container_width=True):
        demo = make_demo_transactions()
        rows = [tuple(r) for r in demo[["txn_date", "txn_type", "description", "amount", "category", "notes"]].itertuples(index=False, name=None)]
        added = db.bulk_add_transactions(rows)

        # Set default budgets and bills if missing
        curr_m = date.today().strftime("%Y-%m")
        if db.get_budgets(curr_m).empty:
            for cat, lim in [("Food", 3500.0), ("Groceries", 2800.0), ("Transport", 1600.0), ("Shopping", 1800.0), ("Entertainment", 1200.0)]:
                db.save_budget(curr_m, cat, lim)

        if db.get_bills().empty:
            db.add_bill("Electricity Bill (DEMO)", 1100.0, (date.today() + timedelta(days=8)).isoformat(), frequency="Monthly")
            db.add_bill("Internet Broadband (DEMO)", 800.0, (date.today() + timedelta(days=12)).isoformat(), frequency="Monthly")

        st.success(f"Loaded {added} synthetic demonstration transactions with example monthly budgets and recurring bills.")
        st.rerun()

    # Database Export Backup
    if not tx.empty:
        st.write("")
        csv_bytes = tx.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Transaction Database Backup (CSV)",
            data=csv_bytes,
            file_name=f"finpilot_backup_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()

    # Reset / Clear Data
    st.subheader("Database Maintenance & Reset")
    st.warning("Clearing local finance data removes all recorded transactions, category budgets, and upcoming bills. Planning assumptions will be retained.")

    confirm = st.checkbox("I understand this will permanently delete all records from this computer's local database.")
    if st.button("Delete All Finance Records", disabled=not confirm, type="secondary"):
        db.clear_all_data()
        st.success("Local records cleared successfully.")
        st.rerun()
