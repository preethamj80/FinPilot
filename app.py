"""FinPilot — AI-Based Personal Finance Management System.

Entrypoint router connecting the Fintech Design System and modular views.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

import database as db
from src.ui.components import render_sidebar_header
from src.ui.styles import apply_fintech_theme
from src.ui.views.budgets_view import render_budgets_view
from src.ui.views.coach_view import render_coach_view
from src.ui.views.insights_view import render_insights_view
from src.ui.views.overview_view import render_overview_view
from src.ui.views.settings_view import render_settings_view
from src.ui.views.simulator_view import render_simulator_view
from src.ui.views.transactions_view import render_transactions_view

# Initialize Streamlit application
st.set_page_config(
    page_title="FinPilot | Intelligent Personal Finance",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database schema and migrations
db.init_db()

# Apply Global Fintech CSS Theme
apply_fintech_theme()

# Navigation definition
NAV_PAGES = [
    "Overview",
    "Transactions",
    "Budgets & Bills",
    "AI Money Coach",
    "What-If Simulator",
    "AI Insights",
    "Settings & Data",
]

# Sidebar Navigation
with st.sidebar:
    render_sidebar_header()
    page = st.radio("NAVIGATE", NAV_PAGES, label_visibility="collapsed")
    st.divider()
    st.markdown(
        """
        <div style="font-size: 0.8rem; color: #94A3B8; line-height: 1.4;">
            <strong>Local-First Architecture</strong><br>
            All financial records are encrypted and stored in your private local SQLite database. No external APIs used.
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_data() -> pd.DataFrame:
    """Fetch and normalize transaction records from the local database."""
    tx = db.get_transactions()
    if not tx.empty:
        tx["txn_date"] = pd.to_datetime(tx["txn_date"], errors="coerce")
        tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0.0)
    return tx


# Retrieve current transactions
transactions = get_data()

# Route to active view
if page == "Overview":
    render_overview_view(transactions)
elif page == "Transactions":
    render_transactions_view(transactions)
elif page == "Budgets & Bills":
    render_budgets_view(transactions)
elif page == "AI Money Coach":
    render_coach_view(transactions)
elif page == "What-If Simulator":
    render_simulator_view(transactions)
elif page == "AI Insights":
    render_insights_view(transactions)
elif page == "Settings & Data":
    render_settings_view(transactions)

# App Footer
st.markdown(
    """
    <div style="text-align: center; color: #94A3B8; font-size: 0.78rem; margin-top: 3.5rem; padding-top: 1rem; border-top: 1px solid #E2E8F0;">
        FinPilot · AI-Based Personal Finance Management System · Academic Prototype · Predictions and recommendations are informational.
    </div>
    """,
    unsafe_allow_html=True,
)
