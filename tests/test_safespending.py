"""Unit tests for the Safe-to-Spend calculation engine."""
from __future__ import annotations

import unittest
from datetime import date
import pandas as pd

from src.services.safespending import calculate_safe_to_spend


class TestSafeSpendingEngine(unittest.TestCase):
    def test_standard_safe_to_spend_with_budgets(self):
        # Opening: 10,000, Income: 40,000, Expenses: 15,000 -> Cash = 35,000
        tx = pd.DataFrame([
            {"txn_date": "2026-11-01", "txn_type": "Income", "amount": 40000.0, "category": "Salary"},
            {"txn_date": "2026-11-05", "txn_type": "Expense", "amount": 10000.0, "category": "Rent"},
            {"txn_date": "2026-11-08", "txn_type": "Expense", "amount": 5000.0, "category": "Food"},
        ])
        # Budgets for Nov 2026: Rent=10000 (spent 10000, remaining 0), Food=8000 (spent 5000, remaining 3000)
        # Total remaining budget = 3,000
        budgets = pd.DataFrame([
            {"month": "2026-11", "category": "Rent", "limit_amount": 10000.0},
            {"month": "2026-11", "category": "Food", "limit_amount": 8000.0},
        ])
        # Unpaid bills: 2,000
        bills = pd.DataFrame([
            {"description": "Electricity", "amount": 2000.0, "due_date": "2026-11-20", "paid": 0},
            {"description": "Old Bill", "amount": 1000.0, "due_date": "2026-11-02", "paid": 1},  # Paid, should NOT subtract
        ])
        settings = {
            "opening_balance": 10000.0,
            "safety_reserve": 3000.0,
            "monthly_savings_target": 5000.0,
        }
        # Cash = 10000 + 40000 - 15000 = 35,000
        # Commitments: Unpaid bills (2000) + reserve (3000) + savings (5000) = 10,000
        # Uncommitted cash = 35,000 - 10,000 = 25,000
        # Remaining budget headroom = 3,000
        # Spendable = min(25000, 3000) = 3,000
        res = calculate_safe_to_spend(tx, budgets, bills, settings, as_of_date=date(2026, 11, 10))

        self.assertEqual(res["current_cash"], 35000.0)
        self.assertEqual(res["upcoming_bills_total"], 2000.0)
        self.assertEqual(res["uncommitted_cash"], 25000.0)
        self.assertTrue(res["has_budgets"])
        self.assertEqual(res["remaining_budget_headroom"], 3000.0)
        self.assertEqual(res["spendable"], 3000.0)
        self.assertGreater(res["daily_spendable"], 0.0)
        self.assertGreater(res["weekly_spendable"], 0.0)

    def test_missing_budgets_does_not_zero_spendable(self):
        # When no monthly budget is configured, spendable must NOT be zero.
        # It must be based on uncommitted liquid cash.
        tx = pd.DataFrame([
            {"txn_date": "2026-11-01", "txn_type": "Income", "amount": 20000.0, "category": "Salary"},
            {"txn_date": "2026-11-02", "txn_type": "Expense", "amount": 5000.0, "category": "Food"},
        ])
        empty_budgets = pd.DataFrame()
        bills = pd.DataFrame([
            {"description": "Internet", "amount": 1000.0, "due_date": "2026-11-15", "paid": 0},
        ])
        settings = {
            "opening_balance": 0.0,
            "safety_reserve": 2000.0,
            "monthly_savings_target": 2000.0,
        }
        # Cash = 15,000
        # Commitments = 1,000 (bill) + 2,000 (reserve) + 2,000 (savings) = 5,000
        # Uncommitted cash = 10,000
        # With NO budgets, spendable should be 10,000 (not 0!)
        res = calculate_safe_to_spend(tx, empty_budgets, bills, settings, as_of_date=date(2026, 11, 10))

        self.assertFalse(res["has_budgets"])
        self.assertIsNone(res["remaining_budget_headroom"])
        self.assertEqual(res["uncommitted_cash"], 10000.0)
        self.assertEqual(res["spendable"], 10000.0)

    def test_zero_income_and_negative_balance_handling(self):
        # Opening: 1000, Expenses: 3000 -> Cash = -2000
        tx = pd.DataFrame([
            {"txn_date": "2026-11-01", "txn_type": "Expense", "amount": 3000.0, "category": "Medical"},
        ])
        settings = {"opening_balance": 1000.0, "safety_reserve": 2000.0, "monthly_savings_target": 0.0}
        res = calculate_safe_to_spend(tx, None, None, settings, as_of_date=date(2026, 11, 15))

        self.assertEqual(res["current_cash"], -2000.0)
        self.assertLess(res["uncommitted_cash"], 0.0)
        # Spendable must gracefully floor at 0, not negative or error
        self.assertEqual(res["spendable"], 0.0)
        self.assertEqual(res["daily_spendable"], 0.0)
        self.assertEqual(res["weekly_spendable"], 0.0)

    def test_avoids_double_counting_recorded_expenses(self):
        # User spent 4000 on Groceries already. Budget is 5000.
        # Remaining budget headroom is 1000.
        # The 4000 was already subtracted from Cash.
        # Ensure we do NOT subtract both 5000 budget AND 4000 expense from Cash!
        tx = pd.DataFrame([
            {"txn_date": "2026-11-01", "txn_type": "Income", "amount": 10000.0, "category": "Salary"},
            {"txn_date": "2026-11-05", "txn_type": "Expense", "amount": 4000.0, "category": "Groceries"},
        ])
        budgets = pd.DataFrame([
            {"month": "2026-11", "category": "Groceries", "limit_amount": 5000.0},
        ])
        settings = {"opening_balance": 0.0, "safety_reserve": 0.0, "monthly_savings_target": 0.0}
        # Cash = 6,000
        # Uncommitted cash = 6,000
        # Remaining budget headroom = 5,000 - 4,000 = 1,000
        # Spendable = min(6000, 1000) = 1,000
        res = calculate_safe_to_spend(tx, budgets, None, settings, as_of_date=date(2026, 11, 10))
        self.assertEqual(res["current_cash"], 6000.0)
        self.assertEqual(res["remaining_budget_headroom"], 1000.0)
        self.assertEqual(res["spendable"], 1000.0)


if __name__ == "__main__":
    unittest.main()
