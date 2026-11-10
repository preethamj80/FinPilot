"""Transactions management view for FinPilot."""
from __future__ import annotations

from datetime import date
import io
import pandas as pd
import streamlit as st

import database as db
from ml_models import category_prediction
from src.config import CATEGORIES, EXPENSE_CATEGORIES, INCOME_CATEGORIES
from src.services.csv_service import clean_and_validate_csv
from src.services.transaction_service import filter_transactions
from src.ui.components import empty_state, format_currency, page_header
from utils import suggest_category


def render_transactions_view(tx: pd.DataFrame) -> None:
    """Render the Transactions view with search, filtering, CSV tools, and safe edit/delete."""
    page_header("Transactions", "Record, categorize, and audit all inflows and outflows in your local database.")

    left, right = st.columns([1.1, 1])

    with left:
        st.subheader("Add a Transaction")
        with st.form("add_txn_form", clear_on_submit=True):
            txn_type = st.selectbox("Transaction Type", ["Expense", "Income"])
            txn_date = st.date_input("Date", value=date.today())
            description = st.text_input("Description", placeholder="e.g. Swiggy dinner, Monthly salary, Uber")
            amount = st.number_input("Amount (₹)", min_value=1.0, value=250.0, step=50.0)

            options = EXPENSE_CATEGORIES if txn_type == "Expense" else INCOME_CATEGORIES
            cat_options = ["Auto-detect"] + options + ["Other"]
            category = st.selectbox("Category", cat_options)
            notes = st.text_input("Notes (optional)", placeholder="e.g. Work reimbursement, split with friend")

            submitted = st.form_submit_button("Save Transaction", use_container_width=True, type="primary")

        if submitted:
            if not description.strip():
                st.error("Please enter a description.")
            else:
                if category == "Auto-detect":
                    predicted, source = category_prediction(description, txn_type, tx)
                    if txn_type == "Expense" and predicted not in EXPENSE_CATEGORIES:
                        predicted = suggest_category(description, txn_type)
                    if txn_type == "Income" and predicted not in INCOME_CATEGORIES:
                        predicted = suggest_category(description, txn_type)
                    category = predicted
                    st.toast(f"Category detected: {category} ({source})")

                db.add_transaction(txn_date.isoformat(), txn_type, description, amount, category, notes)
                st.success(f"Saved {txn_type.lower()} of {format_currency(amount)} under {category}.")
                st.rerun()

    with right:
        st.subheader("Import & Export Records")
        st.markdown("Upload a CSV with **date, amount, description**. Optional columns: type, category, notes.")
        uploaded = st.file_uploader("Upload Transaction CSV", type=["csv"], key="csv_upload")

        if uploaded is not None:
            csv_result = clean_and_validate_csv(uploaded, existing_transactions=tx)
            summary = csv_result["summary"]
            if summary.get("error"):
                st.error(summary["error"])
            else:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Rows", summary["total_rows"])
                m2.metric("Valid Rows", summary["valid_count"])
                m3.metric("Skipped Dups", summary["skipped_file_dup_count"] + summary["skipped_db_dup_count"])
                m4.metric("Invalid Rows", summary["invalid_count"])

                if not csv_result["valid_df"].empty:
                    st.write("Preview of Valid Transactions")
                    st.dataframe(csv_result["valid_df"].head(5), use_container_width=True, hide_index=True)
                    if st.button(f"Import {summary['valid_count']} Valid Records", use_container_width=True, type="primary"):
                        rows = [tuple(r) for r in csv_result["valid_df"][["txn_date", "txn_type", "description", "amount", "category", "notes"]].itertuples(index=False, name=None)]
                        count = db.bulk_add_transactions(rows)
                        st.success(f"Successfully imported {count} transaction(s).")
                        st.rerun()

                if not csv_result["skipped_df"].empty:
                    with st.expander(f"⚠️ Skipped Duplicates ({len(csv_result['skipped_df'])} rows)"):
                        st.caption("Rows below were skipped to prevent duplicate records in your database:")
                        disp_skipped = csv_result["skipped_df"].copy()
                        cols_to_show = [c for c in ["row_num", "rejection_reason", "txn_date", "description", "amount"] if c in disp_skipped.columns]
                        st.dataframe(disp_skipped[cols_to_show], use_container_width=True, hide_index=True)

                if not csv_result["invalid_df"].empty:
                    with st.expander(f"❌ Invalid / Malformed Rows ({len(csv_result['invalid_df'])} rows)"):
                        st.caption("Rows below have formatting issues (e.g. invalid date, negative/zero amount, empty description):")
                        disp_invalid = csv_result["invalid_df"].copy()
                        cols_to_show = [c for c in ["row_num", "rejection_reason", "date", "description", "amount"] if c in disp_invalid.columns]
                        st.dataframe(disp_invalid[cols_to_show], use_container_width=True, hide_index=True)

        st.download_button(
            "Download CSV Template",
            data="date,type,description,amount,category,notes\n2026-11-01,Expense,Example grocery purchase,450,Groceries,Sample row\n",
            file_name="finpilot_transactions_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()

    # Transaction History Section
    st.subheader("Your Transaction History")
    if tx.empty:
        empty_state("No Transactions Recorded", "Add a transaction using the form above or import from CSV.")
    else:
        # Search & Filters
        f1, f2, f3 = st.columns([2, 1, 1.2])
        search_kw = f1.text_input("🔍 Search description", placeholder="Search by merchant or keyword...")
        type_filter = f2.selectbox("Filter Type", ["All", "Expense", "Income"])
        cat_filter = f3.selectbox("Filter Category", ["All"] + CATEGORIES)

        with st.expander("More Filters (Date Range & Amount)"):
            af1, af2, af3, af4 = st.columns(4)
            min_date = tx["txn_date"].min().date() if not tx.empty else date.today()
            max_date = tx["txn_date"].max().date() if not tx.empty else date.today()
            start_d = af1.date_input("From Date", value=min_date)
            end_d = af2.date_input("To Date", value=max_date)
            min_val = float(tx["amount"].min()) if not tx.empty else 0.0
            max_val = float(tx["amount"].max()) if not tx.empty else 10000.0
            filter_min_amt = af3.number_input("Min Amount (₹)", min_value=0.0, value=0.0, step=100.0)
            filter_max_amt = af4.number_input("Max Amount (₹)", min_value=0.0, value=max(max_val, 1000.0), step=500.0)

        filtered_tx = filter_transactions(
            tx,
            search_query=search_kw,
            start_date=start_d,
            end_date=end_d,
            category=cat_filter,
            txn_type=type_filter,
            min_amount=filter_min_amt if filter_min_amt > 0 else None,
            max_amount=filter_max_amt if filter_max_amt < max(max_val, 1000.0) else None,
        )

        st.caption(f"Showing **{len(filtered_tx)}** of **{len(tx)}** total transactions")

        display_df = filtered_tx.copy()
        display_df["txn_date"] = display_df["txn_date"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "txn_date": st.column_config.TextColumn("Date"),
                "txn_type": st.column_config.TextColumn("Type"),
                "description": st.column_config.TextColumn("Description"),
                "category": st.column_config.TextColumn("Category"),
                "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%.2f"),
                "notes": st.column_config.TextColumn("Notes"),
            },
        )

        # Edit and Delete Controls
        st.write("")
        options = {f"#{int(r.id)} · {r.txn_date} · {r.description} · {format_currency(r.amount)}": int(r.id) for r in tx.itertuples()}
        chosen = st.selectbox("Select a Transaction to Edit or Delete", list(options.keys()))
        txn_id = options[chosen]
        row = tx.loc[tx["id"] == txn_id].iloc[0]

        edit_col, delete_col = st.columns(2)

        with edit_col:
            with st.expander("✏️ Edit Selected Transaction"):
                with st.form("edit_form"):
                    edit_date = st.date_input("Date", value=row["txn_date"].date(), key="ed_date")
                    edit_type = st.selectbox("Type", ["Expense", "Income"], index=0 if row["txn_type"] == "Expense" else 1, key="ed_type")
                    edit_desc = st.text_input("Description", value=row["description"], key="ed_desc")
                    edit_amount = st.number_input("Amount (₹)", min_value=1.0, value=float(row["amount"]), key="ed_amt")
                    edit_cat = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(row["category"]) if row["category"] in CATEGORIES else CATEGORIES.index("Other"), key="ed_cat")
                    edit_notes = st.text_input("Notes", value=row["notes"] or "", key="ed_notes")
                    save_btn = st.form_submit_button("Update Transaction", type="primary")

                if save_btn:
                    db.update_transaction(txn_id, edit_date.isoformat(), edit_type, edit_desc, edit_amount, edit_cat, edit_notes)
                    st.success("Transaction updated successfully.")
                    st.rerun()

        with delete_col:
            with st.expander("🗑️ Delete Selected Transaction"):
                st.warning(f"Are you sure you want to permanently delete transaction #{txn_id} ({row['description']} - {format_currency(row['amount'])})?")
                confirm_del = st.checkbox(f"Yes, permanently delete #{txn_id}", key=f"del_confirm_{txn_id}")
                if st.button("Delete Transaction", type="secondary", disabled=not confirm_del):
                    db.delete_transaction(txn_id)
                    st.success("Transaction deleted.")
                    st.rerun()

        # CSV Export
        csv_bytes = tx.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Export All Transactions (CSV)",
            data=csv_bytes,
            file_name="finpilot_transactions_export.csv",
            mime="text/csv",
        )
