"""Deterministic What-If Financial Simulator Engine for FinPilot.

Supports four comprehensive financial decision scenarios:
- Scenario A: Major Purchase Impact
- Scenario B: Expense Reduction
- Scenario C: Income Reduction
- Scenario D: Monthly Savings Simulation
"""
from __future__ import annotations

from datetime import date
from typing import Any
import pandas as pd

from src.services.safespending import calculate_safe_to_spend


def _get_complete_months_data(transactions: pd.DataFrame, current_month: str) -> pd.DataFrame:
    """Filter transactions to complete historical calendar months (excluding current in-progress month)."""
    if transactions is None or transactions.empty:
        return pd.DataFrame()
    tx = transactions.copy()
    tx["_month"] = pd.to_datetime(tx["txn_date"], errors="coerce").dt.strftime("%Y-%m")
    return tx[tx["_month"] < current_month]


def simulate_major_purchase(
    purchase_amount: float,
    category: str,
    planned_date: str | date | None,
    transactions: pd.DataFrame | None,
    budgets: pd.DataFrame | None,
    bills: pd.DataFrame | None,
    settings: dict[str, float] | None,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    """Simulate the financial impact of a major one-time expenditure.
    
    Returns side-by-side baseline vs simulated balances, budget impacts, and affordability verdict.
    """
    today = as_of_date or date.today()
    current_month = today.strftime("%Y-%m")
    purchase_amount = max(0.0, float(purchase_amount))

    # 1. Baseline financial position
    base = calculate_safe_to_spend(transactions, budgets, bills, settings, as_of_date=today)
    base_cash = base["current_cash"]
    base_spendable = base["spendable"]
    base_uncommitted = base["uncommitted_cash"]

    # 2. Simulated position
    sim_cash = base_cash - purchase_amount
    sim_uncommitted = base_uncommitted - purchase_amount
    can_afford_from_cash = sim_cash >= 0
    can_afford_from_uncommitted = sim_uncommitted >= 0
    can_afford_from_safe_spend = purchase_amount <= base_spendable

    # 3. Category budget impact
    cat_limit = None
    cat_spent_mtd = 0.0
    cat_budget_exists = False
    new_cat_spent = purchase_amount
    remaining_cat_budget = None
    budget_overrun = 0.0

    if transactions is not None and not transactions.empty:
        tx = transactions.copy()
        tx["_month"] = pd.to_datetime(tx["txn_date"], errors="coerce").dt.strftime("%Y-%m")
        m_expenses = tx[(tx["_month"] == current_month) & (tx["txn_type"] == "Expense") & (tx["category"] == category)]
        cat_spent_mtd = float(m_expenses["amount"].sum())
        new_cat_spent = cat_spent_mtd + purchase_amount

    if budgets is not None and not budgets.empty:
        b_match = budgets[(budgets["month"] == current_month) & (budgets["category"] == category)]
        if not b_match.empty:
            cat_budget_exists = True
            cat_limit = float(b_match.iloc[0]["limit_amount"])
            remaining_cat_budget = max(0.0, cat_limit - new_cat_spent)
            if new_cat_spent > cat_limit:
                budget_overrun = new_cat_spent - cat_limit

    # 4. Projected month-end cash
    # Baseline projected: cash minus upcoming unpaid bills due this month
    unpaid_bills = base["upcoming_bills_total"]
    proj_month_end_base = base_cash - unpaid_bills
    proj_month_end_sim = sim_cash - unpaid_bills

    # 5. Affordability status & recommendation
    if not can_afford_from_cash:
        status = "Deficit (Cannot Afford)"
        status_color = "danger"
        verdict = f"This purchase exceeds your liquid cash balance by ₹{abs(sim_cash):,.2f}. It cannot be accommodated without incurring debt or overdraft."
    elif not can_afford_from_uncommitted:
        status = "Caution (Dips into Commitments)"
        status_color = "warning"
        verdict = f"You have enough cash in hand, but this purchase cuts into your safety reserve (₹{base['safety_reserve']:,.2f}) or upcoming bills (₹{unpaid_bills:,.2f}) by ₹{abs(sim_uncommitted):,.2f}."
    elif not can_afford_from_safe_spend and base["has_budgets"]:
        status = "Tight (Exceeds Monthly Budget)"
        status_color = "warning"
        verdict = f"Affordable from cash reserves, but exceeds your current safe flexible spending allowance (₹{base_spendable:,.2f}) by ₹{purchase_amount - base_spendable:,.2f}."
    else:
        status = "Comfortable (Within Safe Limits)"
        status_color = "success"
        verdict = f"This purchase is fully within your safe spending capacity. ₹{sim_cash:,.2f} liquid cash will remain."

    assumptions = [
        f"Baseline available liquid cash: ₹{base_cash:,.2f}",
        f"Simulated purchase amount: ₹{purchase_amount:,.2f} in category '{category}'",
        f"Upcoming unpaid bills: ₹{unpaid_bills:,.2f} (protected from spending)",
        f"Safety reserve requirement: ₹{base['safety_reserve']:,.2f}",
        "Assumes no other unrecorded emergency expenses occur before month end.",
    ]

    return {
        "scenario": "Major Purchase Impact",
        "purchase_amount": purchase_amount,
        "category": category,
        "planned_date": str(planned_date or today),
        "baseline_cash": base_cash,
        "simulated_cash": sim_cash,
        "cash_impact": -purchase_amount,
        "baseline_uncommitted": base_uncommitted,
        "simulated_uncommitted": sim_uncommitted,
        "baseline_safe_to_spend": base_spendable,
        "cat_spent_mtd": cat_spent_mtd,
        "new_cat_spent": new_cat_spent,
        "cat_limit": cat_limit,
        "cat_budget_exists": cat_budget_exists,
        "remaining_cat_budget": remaining_cat_budget,
        "budget_overrun": budget_overrun,
        "proj_month_end_base": proj_month_end_base,
        "proj_month_end_sim": proj_month_end_sim,
        "status": status,
        "status_color": status_color,
        "verdict": verdict,
        "assumptions": assumptions,
    }


def simulate_expense_reduction(
    category: str,
    reduction_pct: float,
    duration_months: int,
    transactions: pd.DataFrame | None,
    budgets: pd.DataFrame | None,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    """Simulate reducing spending in a specific category using actual historical baselines."""
    today = as_of_date or date.today()
    current_month = today.strftime("%Y-%m")
    reduction_pct = max(0.0, min(100.0, float(reduction_pct)))
    duration_months = max(1, int(duration_months))

    # Determine baseline monthly spending for this category from complete historical months
    complete_tx = _get_complete_months_data(transactions, current_month)
    history_note = ""
    monthly_baseline = 0.0

    if not complete_tx.empty:
        cat_complete = complete_tx[(complete_tx["txn_type"] == "Expense") & (complete_tx["category"] == category)]
        num_complete_months = complete_tx["_month"].nunique()
        if num_complete_months > 0:
            monthly_baseline = float(cat_complete["amount"].sum()) / num_complete_months
            history_note = f"Based on {num_complete_months} complete historical month(s) average."

    # If no complete historical months, fallback to current month-to-date or budget
    if monthly_baseline <= 0:
        if transactions is not None and not transactions.empty:
            tx = transactions.copy()
            cat_tx = tx[(tx["txn_type"] == "Expense") & (tx["category"] == category)]
            if not cat_tx.empty:
                monthly_baseline = float(cat_tx["amount"].mean())
                history_note = "Based on available transaction records (limited complete monthly history)."

    if monthly_baseline <= 0 and budgets is not None and not budgets.empty:
        b_match = budgets[budgets["category"] == category]
        if not b_match.empty:
            monthly_baseline = float(b_match["limit_amount"].mean())
            history_note = "Based on configured category budget limit."

    if monthly_baseline <= 0:
        history_note = "No historical spending or budget found for this category. Baseline set to ₹0.00."

    monthly_savings = monthly_baseline * (reduction_pct / 100.0)
    revised_monthly = monthly_baseline - monthly_savings
    cumulative_savings = monthly_savings * duration_months
    three_month_savings = monthly_savings * 3

    # Budget impact
    curr_budget_limit = None
    if budgets is not None and not budgets.empty:
        curr_b = budgets[(budgets["month"] == current_month) & (budgets["category"] == category)]
        if not curr_b.empty:
            curr_budget_limit = float(curr_b.iloc[0]["limit_amount"])

    assumptions = [
        f"Category: {category}",
        f"Baseline monthly spending: ₹{monthly_baseline:,.2f} ({history_note})",
        f"Target reduction: {reduction_pct:.1f}% for {duration_months} month(s)",
        "Assumes spending cuts are sustained evenly across the simulation window.",
    ]

    return {
        "scenario": "Expense Reduction",
        "category": category,
        "reduction_pct": reduction_pct,
        "duration_months": duration_months,
        "monthly_baseline": monthly_baseline,
        "revised_monthly": revised_monthly,
        "monthly_savings": monthly_savings,
        "cumulative_savings": cumulative_savings,
        "three_month_savings": three_month_savings,
        "curr_budget_limit": curr_budget_limit,
        "history_note": history_note,
        "assumptions": assumptions,
    }


def simulate_income_reduction(
    reduction_type: str,  # "percentage" or "fixed"
    reduction_value: float,
    duration_months: int,
    transactions: pd.DataFrame | None,
    settings: dict[str, float] | None,
    bills: pd.DataFrame | None = None,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    """Simulate a fixed or percentage reduction in income over a specified duration."""
    today = as_of_date or date.today()
    current_month = today.strftime("%Y-%m")
    duration_months = max(1, int(duration_months))
    reduction_value = max(0.0, float(reduction_value))

    # Determine baseline monthly income
    complete_tx = _get_complete_months_data(transactions, current_month)
    baseline_income = 0.0
    baseline_expenses = 0.0
    num_complete = complete_tx["_month"].nunique() if not complete_tx.empty else 0

    if num_complete > 0:
        income_tx = complete_tx[complete_tx["txn_type"] == "Income"]
        expense_tx = complete_tx[complete_tx["txn_type"] == "Expense"]
        baseline_income = float(income_tx["amount"].sum()) / num_complete
        baseline_expenses = float(expense_tx["amount"].sum()) / num_complete
    elif transactions is not None and not transactions.empty:
        # Fallback to overall monthly sums
        inc = transactions[transactions["txn_type"] == "Income"]
        exp = transactions[transactions["txn_type"] == "Expense"]
        baseline_income = float(inc["amount"].sum()) if not inc.empty else 0.0
        baseline_expenses = float(exp["amount"].sum()) if not exp.empty else 0.0

    # Calculate monthly reduction amount
    if reduction_type == "percentage":
        pct = min(100.0, reduction_value)
        monthly_reduction = baseline_income * (pct / 100.0)
    else:
        monthly_reduction = min(reduction_value, baseline_income)

    revised_income = max(0.0, baseline_income - monthly_reduction)
    baseline_net_cashflow = baseline_income - baseline_expenses
    revised_net_cashflow = revised_income - baseline_expenses
    monthly_cashflow_diff = -monthly_reduction
    cumulative_income_loss = monthly_reduction * duration_months

    # Cash position impact
    base = calculate_safe_to_spend(transactions, None, bills, settings, as_of_date=today)
    starting_cash = base["current_cash"]
    projected_remaining_balance = starting_cash + (revised_net_cashflow * duration_months)

    is_sustainable = revised_net_cashflow >= 0
    if is_sustainable:
        verdict = f"Your revised income (₹{revised_income:,.2f}) still covers average expenses (₹{baseline_expenses:,.2f}). Surplus: +₹{revised_net_cashflow:,.2f}/mo."
        status_color = "success"
    else:
        deficit = abs(revised_net_cashflow)
        verdict = f"Deficit Warning: Your revised income falls short of average expenses by ₹{deficit:,.2f} every month. Cash balance will drain."
        status_color = "danger"

    assumptions = [
        f"Baseline monthly income: ₹{baseline_income:,.2f}",
        f"Baseline monthly expenses: ₹{baseline_expenses:,.2f}",
        f"Income reduction: {reduction_value:,.1f}{'%' if reduction_type == 'percentage' else ' ₹'} per month for {duration_months} month(s)",
        f"Total simulated income loss: ₹{cumulative_income_loss:,.2f}",
    ]

    return {
        "scenario": "Income Reduction",
        "reduction_type": reduction_type,
        "reduction_value": reduction_value,
        "duration_months": duration_months,
        "baseline_income": baseline_income,
        "revised_income": revised_income,
        "monthly_reduction": monthly_reduction,
        "baseline_expenses": baseline_expenses,
        "baseline_net_cashflow": baseline_net_cashflow,
        "revised_net_cashflow": revised_net_cashflow,
        "monthly_cashflow_diff": monthly_cashflow_diff,
        "cumulative_income_loss": cumulative_income_loss,
        "starting_cash": starting_cash,
        "projected_remaining_balance": projected_remaining_balance,
        "is_sustainable": is_sustainable,
        "status_color": status_color,
        "verdict": verdict,
        "assumptions": assumptions,
    }


def simulate_monthly_savings(
    monthly_contribution: float,
    duration_months: int,
    transactions: pd.DataFrame | None,
    budgets: pd.DataFrame | None,
    bills: pd.DataFrame | None,
    settings: dict[str, float] | None,
    initial_savings: float = 0.0,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    """Simulate systematic monthly savings contributions without treating them as an expense or wealth loss."""
    today = as_of_date or date.today()
    monthly_contribution = max(0.0, float(monthly_contribution))
    duration_months = max(1, int(duration_months))
    initial_savings = max(0.0, float(initial_savings))

    base = calculate_safe_to_spend(transactions, budgets, bills, settings, as_of_date=today)
    base_spendable = base["spendable"]
    base_uncommitted = base["uncommitted_cash"]
    base_cash = base["current_cash"]

    total_contributions = monthly_contribution * duration_months
    projected_savings_pool = initial_savings + total_contributions

    # Impact on liquid spending capacity
    can_afford = base_uncommitted >= monthly_contribution
    revised_spendable = max(0.0, base_spendable - monthly_contribution)

    timeline = []
    accum = initial_savings
    for m in range(1, duration_months + 1):
        accum += monthly_contribution
        timeline.append({
            "month": f"Month +{m}",
            "contribution": monthly_contribution,
            "accumulated_savings": accum,
        })

    if can_afford:
        verdict = f"Saving ₹{monthly_contribution:,.2f}/mo is sustainable. In {duration_months} months, you will accumulate ₹{projected_savings_pool:,.2f} in protected savings."
        status_color = "success"
    else:
        verdict = f"Your current uncommitted cash (₹{base_uncommitted:,.2f}) is lower than the planned ₹{monthly_contribution:,.2f}/mo contribution. Dips into commitments."
        status_color = "warning"

    assumptions = [
        f"Monthly savings contribution: ₹{monthly_contribution:,.2f}",
        f"Duration: {duration_months} months",
        "Savings transfers do not reduce total personal net worth; they shift money from liquid spendable to protected savings.",
        f"Baseline spendable allowance before savings: ₹{base_spendable:,.2f}",
        f"Revised spendable allowance after savings: ₹{revised_spendable:,.2f}",
    ]

    return {
        "scenario": "Monthly Savings Simulation",
        "monthly_contribution": monthly_contribution,
        "duration_months": duration_months,
        "initial_savings": initial_savings,
        "total_contributions": total_contributions,
        "projected_savings_pool": projected_savings_pool,
        "base_spendable": base_spendable,
        "revised_spendable": revised_spendable,
        "base_uncommitted": base_uncommitted,
        "can_afford": can_afford,
        "status_color": status_color,
        "verdict": verdict,
        "timeline": timeline,
        "assumptions": assumptions,
    }
