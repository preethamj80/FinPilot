"""Unit tests for What-If Financial Simulator Engine."""
from __future__ import annotations

import unittest
from datetime import date
import pandas as pd

from src.services.simulator import (
    simulate_major_purchase,
    simulate_expense_reduction,
    simulate_income_reduction,
    simulate_monthly_savings,
)


class TestSimulatorEngine(unittest.TestCase):
    def setUp(self):
        # Controlled dataset:
        # 3 complete months: Aug, Sep, Oct 2026. Current month: Nov 2026.
        # Income: 35,000/mo. Expenses: Food=4000/mo, Rent=10000/mo, Groceries=3000/mo.
        rows = []
        for m_str in ["2026-08", "2026-09", "2026-10"]:
            rows.append({"txn_date": f"{m_str}-01", "txn_type": "Income", "description": "Salary", "amount": 35000.0, "category": "Salary"})
            rows.append({"txn_date": f"{m_str}-03", "txn_type": "Expense", "description": "Rent", "amount": 10000.0, "category": "Rent"})
            rows.append({"txn_date": f"{m_str}-05", "txn_type": "Expense", "description": "Food", "amount": 4000.0, "category": "Food"})
            rows.append({"txn_date": f"{m_str}-10", "txn_type": "Expense", "description": "Groceries", "amount": 3000.0, "category": "Groceries"})

        # Current month (Nov 2026) entries
        rows.append({"txn_date": "2026-11-01", "txn_type": "Income", "description": "Salary", "amount": 35000.0, "category": "Salary"})
        rows.append({"txn_date": "2026-11-02", "txn_type": "Expense", "description": "Rent", "amount": 10000.0, "category": "Rent"})
        rows.append({"txn_date": "2026-11-04", "txn_type": "Expense", "description": "Food", "amount": 1500.0, "category": "Food"})

        self.transactions = pd.DataFrame(rows)

        self.budgets = pd.DataFrame([
            {"month": "2026-11", "category": "Food", "limit_amount": 5000.0},
            {"month": "2026-11", "category": "Shopping", "limit_amount": 8000.0},
        ])

        self.bills = pd.DataFrame([
            {"description": "Electricity Bill", "amount": 1500.0, "due_date": "2026-11-20", "paid": 0},
            {"description": "Past Internet Bill", "amount": 800.0, "due_date": "2026-11-02", "paid": 1},  # Paid, do not count
        ])

        self.settings = {
            "opening_balance": 5000.0,
            "safety_reserve": 2000.0,
            "monthly_savings_target": 3000.0,
        }
        self.as_of = date(2026, 11, 10)

    def test_major_purchase_reduces_balance_correctly(self):
        # Baseline cash = 5000 (opening) + 140000 (total income 4 mos) - 62500 (total expenses) = 82,500
        res = simulate_major_purchase(
            purchase_amount=10000.0,
            category="Shopping",
            planned_date="2026-11-15",
            transactions=self.transactions,
            budgets=self.budgets,
            bills=self.bills,
            settings=self.settings,
            as_of_date=self.as_of,
        )
        self.assertEqual(res["baseline_cash"], 82500.0)
        self.assertEqual(res["simulated_cash"], 72500.0)
        self.assertEqual(res["cash_impact"], -10000.0)
        # Check that unpaid bill (1500) is deducted from month-end projection without double counting
        self.assertEqual(res["proj_month_end_base"], 82500.0 - 1500.0)
        self.assertEqual(res["proj_month_end_sim"], 72500.0 - 1500.0)

    def test_major_purchase_exceeds_available_cash(self):
        # Purchase amount of 100,000 exceeds liquid cash (82,500)
        res = simulate_major_purchase(
            purchase_amount=100000.0,
            category="Shopping",
            planned_date="2026-11-15",
            transactions=self.transactions,
            budgets=self.budgets,
            bills=self.bills,
            settings=self.settings,
            as_of_date=self.as_of,
        )
        self.assertLess(res["simulated_cash"], 0.0)
        self.assertEqual(res["simulated_cash"], -17500.0)
        self.assertEqual(res["status_color"], "danger")
        self.assertIn("Deficit", res["status"])

    def test_expense_reduction_calculates_correct_savings(self):
        # In complete months (Aug, Sep, Oct), Food was exactly 4,000/mo.
        # 20% reduction = 800/mo savings.
        res = simulate_expense_reduction(
            category="Food",
            reduction_pct=20.0,
            duration_months=3,
            transactions=self.transactions,
            budgets=self.budgets,
            as_of_date=self.as_of,
        )
        self.assertEqual(res["monthly_baseline"], 4000.0)
        self.assertEqual(res["monthly_savings"], 800.0)
        self.assertEqual(res["revised_monthly"], 3200.0)
        self.assertEqual(res["cumulative_savings"], 2400.0)
        self.assertEqual(res["three_month_savings"], 2400.0)

    def test_income_reduction_calculates_correct_cashflow_change(self):
        # Average income in complete months = 35,000/mo.
        # Average expenses = 17,000/mo.
        # Fixed reduction of ₹5,000 for 4 months.
        res = simulate_income_reduction(
            reduction_type="fixed",
            reduction_value=5000.0,
            duration_months=4,
            transactions=self.transactions,
            settings=self.settings,
            bills=self.bills,
            as_of_date=self.as_of,
        )
        self.assertEqual(res["baseline_income"], 35000.0)
        self.assertEqual(res["revised_income"], 30000.0)
        self.assertEqual(res["monthly_reduction"], 5000.0)
        self.assertEqual(res["cumulative_income_loss"], 20000.0)
        self.assertEqual(res["monthly_cashflow_diff"], -5000.0)
        self.assertTrue(res["is_sustainable"])

    def test_monthly_savings_simulation(self):
        # Monthly savings contribution of 5000 for 6 months
        res = simulate_monthly_savings(
            monthly_contribution=5000.0,
            duration_months=6,
            transactions=self.transactions,
            budgets=self.budgets,
            bills=self.bills,
            settings=self.settings,
            initial_savings=10000.0,
            as_of_date=self.as_of,
        )
        self.assertEqual(res["total_contributions"], 30000.0)
        self.assertEqual(res["projected_savings_pool"], 40000.0)
        self.assertEqual(len(res["timeline"]), 6)
        self.assertEqual(res["timeline"][-1]["accumulated_savings"], 40000.0)
        self.assertTrue(res["can_afford"])

    def test_missing_historical_expense_data(self):
        # If no complete history exists, simulator falls back safely without NaN or error
        empty_tx = pd.DataFrame(columns=["txn_date", "txn_type", "description", "amount", "category"])
        res = simulate_expense_reduction(
            category="Health",
            reduction_pct=15.0,
            duration_months=3,
            transactions=empty_tx,
            budgets=None,
            as_of_date=self.as_of,
        )
        self.assertEqual(res["monthly_baseline"], 0.0)
        self.assertEqual(res["monthly_savings"], 0.0)
        self.assertIn("No historical spending", res["history_note"])

    def test_no_double_counting_unpaid_bills(self):
        # Unpaid bill (1500) vs paid bill (800)
        res = simulate_major_purchase(
            purchase_amount=5000.0,
            category="Food",
            planned_date="2026-11-12",
            transactions=self.transactions,
            budgets=self.budgets,
            bills=self.bills,
            settings=self.settings,
            as_of_date=self.as_of,
        )
        # proj_month_end_base must only subtract 1500 (unpaid), NOT 2300 (total bills)
        self.assertEqual(res["proj_month_end_base"], res["baseline_cash"] - 1500.0)


if __name__ == "__main__":
    unittest.main()
