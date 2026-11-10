"""Explainable, Data-Driven AI Money Coach Engine for FinPilot.

Analyzes recorded transactions, budgets, bills, and forecast outputs to generate
actionable, structured financial recommendations with explicit mathematical evidence.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any
import pandas as pd

from ml_models import forecast_next_month
from src.services.budget_service import get_budget_utilization


RECOMMENDATION_TYPES = [
    "Overspending Warning",
    "Unnecessary Spending Opportunity",
    "High-Spending Category",
    "Recurring Subscription Audit",
    "Budget Improvement Suggestion",
    "Savings Opportunity",
    "Upcoming Bill Warning",
    "Forecast-Based Expense Warning",
]


def generate_coach_insights(
    transactions: pd.DataFrame | None,
    budgets: pd.DataFrame | None,
    bills: pd.DataFrame | None,
    settings: dict[str, float] | None = None,
    as_of_date: date | None = None,
) -> list[dict[str, Any]]:
    """Generate structured, evidence-backed financial guidance cards.
    
    Each recommendation strictly contains:
    - observation: str
    - why_it_matters: str
    - suggested_action: str
    - estimated_monthly_impact: float (INR)
    - supporting_evidence: str
    - analysis_period: str
    - confidence: str ('High', 'Moderate', 'Data-Limited')
    - rec_type: str
    - severity: str ('danger', 'warning', 'info', 'success')
    """
    today = as_of_date or date.today()
    current_month = today.strftime("%Y-%m")
    settings = settings or {}
    insights: list[dict[str, Any]] = []

    # Handle completely empty data
    if transactions is None or transactions.empty:
        return [{
            "rec_type": "Savings Opportunity",
            "observation": "No transactions have been recorded in your local database yet.",
            "why_it_matters": "The AI Money Coach requires transaction history to discover spending habits and anomalies.",
            "suggested_action": "Add your recent expenses or load the synthetic demo dataset from Settings & Data to activate personal guidance.",
            "estimated_monthly_impact": 0.0,
            "supporting_evidence": "0 transactions stored in local database.",
            "analysis_period": current_month,
            "confidence": "Data-Limited",
            "severity": "info",
        }]

    tx = transactions.copy()
    tx["_amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0.0)
    tx["_dt"] = pd.to_datetime(tx["txn_date"], errors="coerce")
    tx["_month"] = tx["_dt"].dt.strftime("%Y-%m")

    month_tx = tx[tx["_month"] == current_month]
    month_expenses = month_tx[month_tx["txn_type"] == "Expense"]
    month_income = month_tx[month_tx["txn_type"] == "Income"]

    total_month_exp = float(month_expenses["_amount"].sum()) if not month_expenses.empty else 0.0
    total_month_inc = float(month_income["_amount"].sum()) if not month_income.empty else 0.0

    # ---------------- 1. Overspending Warnings ----------------
    if budgets is not None and not budgets.empty:
        budget_util = get_budget_utilization(budgets, tx, current_month)
        for _, b_row in budget_util.iterrows():
            cat = b_row["category"]
            limit = float(b_row["limit_amount"])
            spent = float(b_row["spent"])
            status = b_row["status"]

            if status == "Exceeded":
                over_amt = spent - limit
                insights.append({
                    "rec_type": "Overspending Warning",
                    "observation": f"Category '{cat}' has exceeded its ₹{limit:,.0f} monthly budget by ₹{over_amt:,.2f}.",
                    "why_it_matters": "Overspending directly depletes your safe liquid cash reserve and threatens upcoming commitments.",
                    "suggested_action": f"Freeze non-essential purchases in {cat} for the remainder of {current_month}.",
                    "estimated_monthly_impact": over_amt,
                    "supporting_evidence": f"Actual {current_month} spend: ₹{spent:,.2f} vs. Budget Limit: ₹{limit:,.2f} ({b_row['pct_used']:.1f}% used).",
                    "analysis_period": current_month,
                    "confidence": "High",
                    "severity": "danger",
                })
            elif status == "Warning":
                remaining = limit - spent
                insights.append({
                    "rec_type": "Overspending Warning",
                    "observation": f"Category '{cat}' has consumed {b_row['pct_used']:.0f}% of its budget, with only ₹{remaining:,.2f} remaining.",
                    "why_it_matters": "At the current run-rate, this category is on pace to breach its budget before month-end.",
                    "suggested_action": f"Limit remaining {cat} purchases to an average of ₹{max(1.0, remaining / max(1, (30 - today.day))):,.0f}/day.",
                    "estimated_monthly_impact": remaining * 0.5,
                    "supporting_evidence": f"Spent ₹{spent:,.2f} of ₹{limit:,.2f} limit.",
                    "analysis_period": current_month,
                    "confidence": "High",
                    "severity": "warning",
                })

    # ---------------- 2. High-Spending Category Identification & Category Surge ----------------
    if not month_expenses.empty and total_month_exp > 0:
        cat_sums = month_expenses.groupby("category")["_amount"].sum().sort_values(ascending=False)
        top_cat = cat_sums.index[0]
        top_amt = float(cat_sums.iloc[0])
        top_share = (top_amt / total_month_exp) * 100

        if top_share >= 25 and top_cat not in ["Rent", "Salary"]:
            pot_savings = top_amt * 0.12  # 12% realistic trim
            insights.append({
                "rec_type": "High-Spending Category",
                "observation": f"'{top_cat}' is your largest expense category this month, accounting for {top_share:.1f}% (₹{top_amt:,.2f}) of all spending.",
                "why_it_matters": "Concentrated spending in flexible categories represents your highest-leverage opportunity to increase monthly savings.",
                "suggested_action": f"Audit {top_cat} receipts to identify lower-cost alternatives or reduce frequency by 10–15%.",
                "estimated_monthly_impact": pot_savings,
                "supporting_evidence": f"₹{top_amt:,.2f} out of ₹{total_month_exp:,.2f} total monthly expenses spent on {top_cat}.",
                "analysis_period": current_month,
                "confidence": "High",
                "severity": "info",
            })

    # Check for category spending surge compared to prior complete months
    complete_tx = tx[tx["_month"] < current_month]
    if not complete_tx.empty and not month_expenses.empty:
        comp_expenses = complete_tx[complete_tx["txn_type"] == "Expense"]
        num_prior_months = complete_tx["_month"].nunique()
        if num_prior_months >= 2:
            prior_cat_avg = comp_expenses.groupby("category")["_amount"].sum() / num_prior_months
            curr_cat_sums = month_expenses.groupby("category")["_amount"].sum()
            for cat, curr_val in curr_cat_sums.items():
                if cat in prior_cat_avg.index:
                    prior_val = float(prior_cat_avg[cat])
                    if prior_val >= 800.0 and curr_val > prior_val * 1.25:
                        surge_pct = ((curr_val / prior_val) - 1) * 100
                        surge_diff = curr_val - prior_val
                        insights.append({
                            "rec_type": "Category Surge Warning",
                            "observation": f"Spending in '{cat}' (₹{curr_val:,.2f}) has surged by {surge_pct:.1f}% compared to your prior average of ₹{prior_val:,.2f}.",
                            "why_it_matters": "Sudden spending acceleration in a category often signals lifestyle creep or unmonitored impulse buys.",
                            "suggested_action": f"Review recent {cat} receipts and set an alert if spending crosses ₹{prior_val * 1.1:,.0f}.",
                            "estimated_monthly_impact": surge_diff,
                            "supporting_evidence": f"Prior {num_prior_months}-month average: ₹{prior_val:,.2f}/mo vs. current {current_month} spend: ₹{curr_val:,.2f}.",
                            "analysis_period": f"Current vs. Prior {num_prior_months} Months",
                            "confidence": "High",
                            "severity": "warning",
                        })

    # ---------------- 3. Unnecessary Spending / Frequent Micro-Transactions ----------------
    all_expenses = tx[tx["txn_type"] == "Expense"].copy()
    if not all_expenses.empty:
        # Check Food / Dining / Takeout frequency
        dining_tx = all_expenses[all_expenses["category"].isin(["Food", "Entertainment", "Shopping"])]
        if len(dining_tx) >= 6:
            # Check for frequent small purchases (<= 600 INR)
            micro_tx = dining_tx[dining_tx["_amount"] <= 600.0]
            if len(micro_tx) >= 5:
                micro_total = float(micro_tx["_amount"].sum())
                # Trimming 25% of micro expenses
                trim_savings = micro_total * 0.25
                insights.append({
                    "rec_type": "Unnecessary Spending Opportunity",
                    "observation": f"Identified {len(micro_tx)} frequent micro-transactions (under ₹600) totaling ₹{micro_total:,.2f}.",
                    "why_it_matters": "Frequent small impulse spends (coffee, food delivery snacks, quick buys) accumulate silently into major monthly leakages.",
                    "suggested_action": "Consolidate or reduce food delivery and snack orders by 1–2 times per week.",
                    "estimated_monthly_impact": trim_savings,
                    "supporting_evidence": f"{len(micro_tx)} micro-transactions logged in discretionary categories.",
                    "analysis_period": "Historical & Current",
                    "confidence": "Moderate",
                    "severity": "warning",
                })

    # ---------------- 4. Recurring Subscription Audit ----------------
    # Detect recurring charges by description frequency across distinct months
    if len(all_expenses) >= 4:
        desc_counts = all_expenses.groupby("description").agg(
            month_count=("_month", "nunique"),
            total_spent=("_amount", "sum"),
            avg_amount=("_amount", "mean"),
        )
        recurring_candidates = desc_counts[
            (desc_counts["month_count"] >= 2) &
            (desc_counts["avg_amount"] < 5000.0)
        ]
        if not recurring_candidates.empty:
            total_sub_monthly = float(recurring_candidates["avg_amount"].sum())
            sub_names = ", ".join(list(recurring_candidates.index[:3]))
            insights.append({
                "rec_type": "Recurring Subscription Audit",
                "observation": f"Detected {len(recurring_candidates)} recurring subscriptions worth reviewing ({sub_names}) totaling ~₹{total_sub_monthly:,.2f}/month.",
                "why_it_matters": "Recurring charges auto-renew periodically. Reviewing active services ensures you are only paying for subscriptions you value and actively use.",
                "suggested_action": "Review whether you actively utilize each of these subscriptions, or if any can be paused or canceled to free up monthly cash.",
                "estimated_monthly_impact": total_sub_monthly * 0.4,  # Potential estimated monthly savings
                "supporting_evidence": f"Recurring charges observed across {int(recurring_candidates['month_count'].max())} separate monthly periods.",
                "analysis_period": "Multi-month history",
                "confidence": "Moderate",
                "severity": "info",
            })

    # ---------------- 5. Budget Improvement Suggestions ----------------
    if not month_expenses.empty:
        existing_budget_cats = set()
        if budgets is not None and not budgets.empty:
            m_budgets = budgets[budgets["month"] == current_month]
            existing_budget_cats = set(m_budgets["category"].tolist())

        unbudgeted_spending = month_expenses[~month_expenses["category"].isin(existing_budget_cats)]
        if not unbudgeted_spending.empty:
            top_unbudgeted = unbudgeted_spending.groupby("category")["_amount"].sum().sort_values(ascending=False)
            unb_cat = top_unbudgeted.index[0]
            unb_amt = float(top_unbudgeted.iloc[0])
            if unb_amt >= 1000.0:
                insights.append({
                    "rec_type": "Budget Improvement Suggestion",
                    "observation": f"You spent ₹{unb_amt:,.2f} on '{unb_cat}' this month without a defined category budget limit.",
                    "why_it_matters": "Unbudgeted categories lack spending guardrails, making it easy to overspend without warning.",
                    "suggested_action": f"Set a monthly budget cap for '{unb_cat}' (recommended: ₹{unb_amt * 0.9:,.0f}) in Budgets & Bills.",
                    "estimated_monthly_impact": unb_amt * 0.1,
                    "supporting_evidence": f"₹{unb_amt:,.2f} unbudgeted outflow logged in {unb_cat} for {current_month}.",
                    "analysis_period": current_month,
                    "confidence": "High",
                    "severity": "warning",
                })

    # ---------------- 6. Savings Opportunity (50/30/20 Rule Check) ----------------
    if total_month_inc > 0:
        actual_savings = max(0.0, total_month_inc - total_month_exp)
        actual_savings_rate = (actual_savings / total_month_inc) * 100
        target_savings_rate = 20.0
        target_savings_amt = total_month_inc * (target_savings_rate / 100.0)

        if actual_savings_rate < target_savings_rate:
            savings_gap = target_savings_amt - actual_savings
            insights.append({
                "rec_type": "Savings Opportunity",
                "observation": f"Current savings rate is {actual_savings_rate:.1f}% (₹{actual_savings:,.2f}), below the recommended 20% benchmark (₹{target_savings_amt:,.2f}).",
                "why_it_matters": "Maintaining a 20% monthly savings buffer protects your future goals against unexpected emergencies.",
                "suggested_action": f"Automate a ₹{savings_gap:,.2f}/mo recurring transfer into your savings reserve immediately when income arrives.",
                "estimated_monthly_impact": savings_gap,
                "supporting_evidence": f"Recorded income: ₹{total_month_inc:,.2f} vs. recorded expenses: ₹{total_month_exp:,.2f}.",
                "analysis_period": current_month,
                "confidence": "High",
                "severity": "info",
            })
        else:
            insights.append({
                "rec_type": "Savings Opportunity",
                "observation": f"Healthy savings performance! You have retained {actual_savings_rate:.1f}% (₹{actual_savings:,.2f}) of income this month.",
                "why_it_matters": "You are surpassing standard financial wellness benchmarks.",
                "suggested_action": "Consider allocating surplus funds beyond your safety reserve into liquid investments or fixed deposits.",
                "estimated_monthly_impact": actual_savings,
                "supporting_evidence": f"Net surplus of ₹{actual_savings:,.2f} retained this period.",
                "analysis_period": current_month,
                "confidence": "High",
                "severity": "success",
            })

    # ---------------- 7. Upcoming Bill Warnings ----------------
    if bills is not None and not bills.empty:
        b_df = bills.copy()
        b_df["_due"] = pd.to_datetime(b_df["due_date"], errors="coerce").dt.date
        b_df["_amt"] = pd.to_numeric(b_df["amount"], errors="coerce").fillna(0.0)
        due_soon = b_df[(b_df["paid"] == 0) & (b_df["_due"] >= today) & (b_df["_due"] <= today + timedelta(days=7))]

        if not due_soon.empty:
            due_total = float(due_soon["_amt"].sum())
            bill_names = ", ".join(due_soon["description"].tolist()[:3])
            insights.append({
                "rec_type": "Upcoming Bill Warning",
                "observation": f"You have {len(due_soon)} unpaid bill(s) totaling ₹{due_total:,.2f} due within the next 7 days ({bill_names}).",
                "why_it_matters": "Late payments risk late fees, interest charges, and service interruptions.",
                "suggested_action": "Ensure ₹" + f"{due_total:,.2f}" + " remains reserved in your checking balance before making discretionary purchases.",
                "estimated_monthly_impact": due_total,
                "supporting_evidence": f"{len(due_soon)} bill(s) due between {today} and {today + timedelta(days=7)}.",
                "analysis_period": "Next 7 Days",
                "confidence": "High",
                "severity": "warning",
            })

    # ---------------- 8. Forecast-Based Expense Warning ----------------
    try:
        fc = forecast_next_month(tx)
        if fc.get("status") == "trained" and fc.get("prediction"):
            pred = float(fc["prediction"])
            hist = fc.get("history")
            if hist is not None and not hist.empty:
                hist_avg = float(hist["amount"].mean())
                if pred > hist_avg * 1.10:  # > 10% above historical mean
                    diff = pred - hist_avg
                    insights.append({
                        "rec_type": "Forecast-Based Expense Warning",
                        "observation": f"Statistical forecast projects next month's spending at ₹{pred:,.2f}, which is {((pred/hist_avg)-1)*100:.1f}% higher than your average (₹{hist_avg:,.2f}).",
                        "why_it_matters": "Upward linear trajectory suggests creeping expenditure across several categories.",
                        "suggested_action": "Review recent lifestyle inflation and plan category budget reductions in advance of next month.",
                        "estimated_monthly_impact": diff,
                        "supporting_evidence": f"Historical monthly average: ₹{hist_avg:,.2f} vs. Linear Regression Projection: ₹{pred:,.2f}.",
                        "analysis_period": "Next Month Forecast",
                        "confidence": "Moderate",
                        "severity": "warning",
                    })
    except Exception:
        pass

    return insights
