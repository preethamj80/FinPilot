"""Phase 6 QA Edge Cases and Mathematical Validation Tests for FinPilot.

Validates financial calculation boundary conditions, zero-division resilience,
month transitions, negative cash balances, simulator stress cases, and database reload safety.
"""
from __future__ import annotations

import datetime
from datetime import date
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

import database as db_root
import src.database as db_src
from src.services.budget_service import (
    compute_next_due_date,
    get_budget_utilization,
    process_recurring_bill_on_payment,
)
from src.services.coach import generate_coach_insights
from src.services.csv_service import clean_and_validate_csv
from src.services.safespending import calculate_safe_to_spend
from src.services.simulator import (
    simulate_expense_reduction,
    simulate_income_reduction,
    simulate_major_purchase,
    simulate_monthly_savings,
)
from src.services.transaction_service import filter_transactions


class TestFinancialMathAndBoundaryConditions(unittest.TestCase):
    """Rigorous tests for core financial math formulas."""

    def test_liquid_cash_balance_formula(self):
        # Balance = Opening Balance + Total Inflow - Total Outflow
        tx = pd.DataFrame([
            {"txn_date": "2026-11-01", "txn_type": "Income", "amount": 50000.0, "category": "Salary", "description": "Pay"},
            {"txn_date": "2026-11-02", "txn_type": "Expense", "amount": 12000.0, "category": "Rent", "description": "Rent"},
            {"txn_date": "2026-11-03", "txn_type": "Expense", "amount": 3500.0, "category": "Food", "description": "Groceries"},
        ])
        settings = {"opening_balance": 15000.0, "safety_reserve": 2000.0, "monthly_savings_target": 5000.0}
        res = calculate_safe_to_spend(tx, None, None, settings, as_of_date=date(2026, 11, 10))

        # Expected: 15,000 + 50,000 - 15,500 = 49,500
        self.assertEqual(res["total_income"], 50000.0)
        self.assertEqual(res["total_expenses"], 15500.0)
        self.assertEqual(res["current_cash"], 49500.0)

        # Uncommitted = current_cash - upcoming_bills - safety_reserve - savings_target
        # 49,500 - 0 - 2,000 - 5,000 = 42,500
        self.assertEqual(res["uncommitted_cash"], 42500.0)
        self.assertEqual(res["spendable"], 42500.0)

    def test_zero_days_left_and_month_transition_boundary(self):
        # On the last day of a 30-day month (e.g. 2026-11-30)
        # days_left must equal 1 (not 0) to avoid division by zero
        tx = pd.DataFrame([
            {"txn_date": "2026-11-01", "txn_type": "Income", "amount": 30000.0, "category": "Salary", "description": "Pay"},
        ])
        res_last_day = calculate_safe_to_spend(tx, None, None, {"safety_reserve": 0.0}, as_of_date=date(2026, 11, 30))
        self.assertEqual(res_last_day["days_left"], 1)
        self.assertEqual(res_last_day["daily_spendable"], 30000.0)
        self.assertEqual(res_last_day["weekly_spendable"], 30000.0)

        # Crossing December 31 to January 1
        res_dec_end = calculate_safe_to_spend(tx, None, None, {"safety_reserve": 0.0}, as_of_date=date(2026, 12, 31))
        self.assertEqual(res_dec_end["days_left"], 1)

    def test_negative_cash_balance_handling(self):
        # User spent more than they have
        tx = pd.DataFrame([
            {"txn_date": "2026-11-01", "txn_type": "Income", "amount": 10000.0, "category": "Salary", "description": "Pay"},
            {"txn_date": "2026-11-02", "txn_type": "Expense", "amount": 25000.0, "category": "Rent", "description": "Rent"},
        ])
        res = calculate_safe_to_spend(tx, None, None, {"opening_balance": 0.0, "safety_reserve": 2000.0}, as_of_date=date(2026, 11, 5))
        self.assertEqual(res["current_cash"], -15000.0)
        self.assertEqual(res["spendable"], 0.0)
        self.assertEqual(res["daily_spendable"], 0.0)
        self.assertEqual(res["weekly_spendable"], 0.0)

    def test_budget_utilization_warning_and_exceeded_thresholds(self):
        budgets = pd.DataFrame([
            {"id": 1, "month": "2026-11", "category": "Food", "limit_amount": 5000.0},
            {"id": 2, "month": "2026-11", "category": "Transport", "limit_amount": 3000.0},
            {"id": 3, "month": "2026-11", "category": "Shopping", "limit_amount": 2000.0},
        ])
        tx = pd.DataFrame([
            {"txn_date": "2026-11-02", "txn_type": "Expense", "amount": 2000.0, "category": "Food"},         # 40% -> On Track
            {"txn_date": "2026-11-03", "txn_type": "Expense", "amount": 2500.0, "category": "Transport"},    # 83.3% -> Warning
            {"txn_date": "2026-11-04", "txn_type": "Expense", "amount": 2400.0, "category": "Shopping"},     # 120% -> Exceeded
        ])
        util = get_budget_utilization(budgets, tx, "2026-11")

        food_row = util[util["category"] == "Food"].iloc[0]
        self.assertEqual(food_row["status"], "On Track")
        self.assertEqual(food_row["remaining"], 3000.0)

        trans_row = util[util["category"] == "Transport"].iloc[0]
        self.assertEqual(trans_row["status"], "Warning")

        shop_row = util[util["category"] == "Shopping"].iloc[0]
        self.assertEqual(shop_row["status"], "Exceeded")
        self.assertEqual(shop_row["remaining"], 0.0)  # Headroom cannot be negative


class TestSimulatorScenariosStress(unittest.TestCase):
    """Stress tests for all four What-If simulator scenarios."""

    def test_scenario_a_major_purchase_causing_deficit(self):
        tx = pd.DataFrame([
            {"txn_date": "2026-11-01", "txn_type": "Income", "amount": 40000.0, "category": "Salary", "description": "Salary"},
            {"txn_date": "2026-11-02", "txn_type": "Expense", "amount": 20000.0, "category": "Rent", "description": "Rent"},
        ])
        # Cash available: 20,000. Purchase of 50,000 laptop
        res = simulate_major_purchase(
            purchase_amount=50000.0,
            category="Shopping",
            planned_date="2026-11-15",
            transactions=tx,
            budgets=None,
            bills=None,
            settings={"safety_reserve": 2000.0},
            as_of_date=date(2026, 11, 10),
        )
        self.assertEqual(res["baseline_cash"], 20000.0)
        self.assertEqual(res["simulated_cash"], -30000.0)
        self.assertEqual(res["status"], "Deficit (Cannot Afford)")
        self.assertEqual(res["status_color"], "danger")

    def test_scenario_b_expense_reduction_boundary(self):
        tx = pd.DataFrame([
            {"txn_date": "2026-09-05", "txn_type": "Expense", "amount": 6000.0, "category": "Food"},
            {"txn_date": "2026-10-05", "txn_type": "Expense", "amount": 4000.0, "category": "Food"},
        ])
        # 2 complete months: avg Food = 5,000/mo. Reduce by 20% for 6 months
        res = simulate_expense_reduction(
            category="Food",
            reduction_pct=20.0,
            duration_months=6,
            transactions=tx,
            budgets=None,
            as_of_date=date(2026, 11, 10),
        )
        self.assertEqual(res["monthly_baseline"], 5000.0)
        self.assertEqual(res["monthly_savings"], 1000.0)
        self.assertEqual(res["cumulative_savings"], 6000.0)

    def test_scenario_c_income_reduction_deficit(self):
        tx = pd.DataFrame([
            {"txn_date": "2026-09-01", "txn_type": "Income", "amount": 50000.0, "category": "Salary"},
            {"txn_date": "2026-09-02", "txn_type": "Expense", "amount": 40000.0, "category": "Rent"},
        ])
        # Income drops by 30% (from 50,000 to 35,000), but expenses are 40,000 -> Deficit of 5,000/mo
        res = simulate_income_reduction(
            reduction_type="percentage",
            reduction_value=30.0,
            duration_months=3,
            transactions=tx,
            settings=None,
            as_of_date=date(2026, 10, 15),
        )
        self.assertEqual(res["revised_income"], 35000.0)
        self.assertEqual(res["revised_net_cashflow"], -5000.0)
        self.assertFalse(res["is_sustainable"])
        self.assertEqual(res["status_color"], "danger")

    def test_scenario_d_monthly_savings_timeline(self):
        res = simulate_monthly_savings(
            monthly_contribution=3000.0,
            duration_months=12,
            transactions=None,
            budgets=None,
            bills=None,
            settings={"opening_balance": 10000.0},
            initial_savings=5000.0,
            as_of_date=date(2026, 11, 1),
        )
        self.assertEqual(res["total_contributions"], 36000.0)
        self.assertEqual(res["projected_savings_pool"], 41000.0)
        self.assertEqual(len(res["timeline"]), 12)
        self.assertEqual(res["timeline"][-1]["accumulated_savings"], 41000.0)


class TestDatabaseReloadAndIsolation(unittest.TestCase):
    """Test database persistence across connection resets using temporary database files."""

    def test_database_insert_update_delete_persistence(self):
        fd, temp_db = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            db_src.init_db(temp_db)

            # 1. Add transaction
            t_id = db_src.add_transaction("2026-11-01", "Expense", "Initial Test", 500.0, "Food", "Notes", custom_path=temp_db)
            self.assertGreater(t_id, 0)

            # Verify in fresh query
            tx1 = db_src.get_transactions(temp_db)
            self.assertEqual(len(tx1), 1)
            self.assertEqual(tx1.iloc[0]["description"], "Initial Test")

            # 2. Update transaction
            db_src.update_transaction(t_id, "2026-11-02", "Expense", "Updated Test", 750.0, "Groceries", "Updated Notes", custom_path=temp_db)
            tx2 = db_src.get_transactions(temp_db)
            self.assertEqual(tx2.iloc[0]["description"], "Updated Test")
            self.assertEqual(tx2.iloc[0]["amount"], 750.0)
            self.assertEqual(tx2.iloc[0]["category"], "Groceries")

            # 3. Delete transaction
            db_src.delete_transaction(t_id, custom_path=temp_db)
            tx3 = db_src.get_transactions(temp_db)
            self.assertTrue(tx3.empty)
        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)


if __name__ == "__main__":
    unittest.main()
