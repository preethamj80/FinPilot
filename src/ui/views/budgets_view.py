"""Budgets and bills management view for FinPilot."""
from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
import streamlit as st

import database as db
from src.config import EXPENSE_CATEGORIES
from src.services.budget_service import (
    get_budget_utilization,
    process_recurring_bill_on_payment,
    sync_all_recurring_bills,
)
from src.ui.components import empty_state, format_currency, page_header
from src.ui.styles import PALETTE


def render_budgets_view(tx: pd.DataFrame) -> None:
    """Render the Budgets & Bills view."""
    page_header("Budgets & Bills", "Set monthly spending guardrails, track upcoming commitments, and manage recurring payments.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Set a Category Budget")
        with st.form("budget_form"):
            bmonth = st.date_input("Budget Month", value=date.today(), key="b_month").strftime("%Y-%m")
            bcategory = st.selectbox("Category", EXPENSE_CATEGORIES)
            blimit = st.number_input("Monthly Limit (₹)", min_value=0.0, value=3000.0, step=250.0)
            save_b = st.form_submit_button("Save Category Budget", type="primary", use_container_width=True)

        if save_b:
            db.save_budget(bmonth, bcategory, blimit)
            st.success(f"Saved {bcategory} budget limit of {format_currency(blimit)} for {bmonth}.")
            st.rerun()

    with col2:
        st.subheader("Add an Upcoming Bill or Subscription")
        with st.form("bill_form"):
            bdesc = st.text_input("Bill Name", placeholder="e.g. Electricity, Netflix, House Rent")
            bamount = st.number_input("Expected Amount (₹)", min_value=1.0, value=1000.0, step=100.0)
            bdue = st.date_input("Due Date", value=date.today() + timedelta(days=7))
            bfreq = st.selectbox("Frequency", ["One-time", "Weekly", "Monthly", "Yearly"], index=0)
            save_bill = st.form_submit_button("Add Bill Commitment", type="primary", use_container_width=True)

        if save_bill:
            if bdesc.strip():
                db.add_bill(bdesc, bamount, bdue.isoformat(), frequency=bfreq)
                st.success(f"Added {bfreq.lower()} commitment '{bdesc}' for {format_currency(bamount)}.")
                st.rerun()
            else:
                st.error("Please enter a bill name.")

    st.divider()

    # Budget Usage Cards
    current_month = date.today().strftime("%Y-%m")
    st.subheader(f"Monthly Budget Utilization ({date.today().strftime('%B %Y')})")

    budgets_df = db.get_budgets(current_month)
    if budgets_df.empty:
        empty_state("No Budgets for This Month", "Set your first category budget above to monitor spending limits and overruns.", icon="🎯")
    else:
        utilization = get_budget_utilization(budgets_df, tx, current_month)
        for _, b in utilization.iterrows():
            cat = b["category"]
            limit = float(b["limit_amount"])
            spent = float(b["spent"])
            rem = float(b["remaining"])
            pct = float(b["pct_used"]) / 100.0
            status = b["status"]

            badge_color = PALETTE["success"] if status == "On Track" else PALETTE["warning"] if status == "Warning" else PALETTE["danger"]

            st.markdown(
                f"""
                <div style="background-color: {PALETTE['bg_card']}; border: 1px solid {PALETTE['border']}; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <span style="font-weight: 700; font-size: 1rem; color: {PALETTE['text_primary']};">{cat}</span>
                        <span style="font-size: 0.85rem; font-weight: 600; color: {badge_color};">
                            {status} ({pct:.0%})
                        </span>
                    </div>
                    <div style="font-size: 0.9rem; color: {PALETTE['text_secondary']}; margin-bottom: 0.45rem;">
                        Spent <strong>{format_currency(spent)}</strong> of <strong>{format_currency(limit)}</strong> · {format_currency(rem)} remaining
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(min(1.0, max(0.0, pct)))

        # Budget Removal Management
        all_budgets = db.get_budgets()
        if not all_budgets.empty:
            with st.expander("Manage / Remove Saved Budgets"):
                b_map = {f"#{int(r.id)} · {r.month} · {r.category} ({format_currency(r.limit_amount)})": int(r.id) for r in all_budgets.itertuples()}
                sel_b = st.selectbox("Select Budget to Remove", list(b_map.keys()))
                if st.button("Delete Selected Budget", type="secondary"):
                    db.delete_budget(b_map[sel_b])
                    st.success("Budget removed.")
                    st.rerun()

    st.divider()

    # Upcoming Bills and Recurring Subscriptions Section
    st.subheader("Upcoming Bills & Recurring Subscriptions")

    sync_all_recurring_bills(db)
    bills = db.get_bills()

    if bills.empty:
        empty_state("No Upcoming Commitments", "Add rent, utilities, subscriptions, or credit card bills above to reserve cash for them.", icon="📅")
    else:
        for r in bills.itertuples():
            c1, c2, c3, c4, c5 = st.columns([2.5, 1.2, 1.3, 1.2, 1.1])
            c1.write(f"**{r.description}**")
            c2.write(format_currency(r.amount))
            c3.write(str(r.due_date))

            freq = getattr(r, "frequency", "One-time")
            c4.caption(f"🔄 {freq}" if freq != "One-time" else "Once")

            paid = c5.checkbox("Paid", value=bool(r.paid), key=f"bill_paid_{r.id}")
            if paid != bool(r.paid):
                db.mark_bill_paid(r.id, paid)
                if paid and freq != "One-time":
                    created, msg = process_recurring_bill_on_payment(r.id, bills, db)
                    if created:
                        st.toast(msg)
                st.rerun()

        bill_map = {f"#{int(r.id)} · {r.description} · {format_currency(r.amount)}": int(r.id) for r in bills.itertuples()}
        rem_b = st.selectbox("Select Bill to Delete", list(bill_map.keys()))
        if st.button("Delete Selected Bill", type="secondary"):
            db.delete_bill(bill_map[rem_b])
            st.success("Bill removed.")
            st.rerun()
