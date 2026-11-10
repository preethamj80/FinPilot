"""Unit tests for the explainable AI Money Coach engine."""
from __future__ import annotations

import unittest
from datetime import date
import pandas as pd

from src.services.coach import generate_coach_insights


class TestCoachEngine(unittest.TestCase):
    def setUp(self):
        self.as_of = date(2026, 11, 10)

    def test_empty_database_handling(self):
        empty_tx = pd.DataFrame()
        insights = generate_coach_insights(empty_tx, None, None, as_of_date=self.as_of)
        self.assertEqual(len(insights), 1)
        self.assertEqual(insights[0]["confidence"], "Data-Limited")
        self.assertEqual(insights[0]["estimated_monthly_impact"], 0.0)
        self.assertIn("No transactions", insights[0]["observation"])

    def test_overspending_detection(self):
        # Spent 6,000 on Food in Nov 2026 against a 5,000 budget
        tx = pd.DataFrame([
            {"txn_date": "2026-11-02", "txn_type": "Expense", "amount": 6000.0, "category": "Food", "description": "Restaurants"},
        ])
        budgets = pd.DataFrame([
            {"month": "2026-11", "category": "Food", "limit_amount": 5000.0},
        ])
        insights = generate_coach_insights(tx, budgets, None, as_of_date=self.as_of)
        overspending_recs = [r for r in insights if r["rec_type"] == "Overspending Warning"]
        self.assertTrue(len(overspending_recs) >= 1)
        rec = overspending_recs[0]
        self.assertEqual(rec["severity"], "danger")
        self.assertEqual(rec["estimated_monthly_impact"], 1000.0)
        self.assertIn("exceeded its ₹5,000", rec["observation"])
        self.assertIn("₹6,000.00", rec["supporting_evidence"])

    def test_category_spending_increase_detection(self):
        # 2 complete months with 1,000/mo in Shopping. Current month has 2,500 (+150% surge!)
        rows = [
            {"txn_date": "2026-09-10", "txn_type": "Expense", "amount": 1000.0, "category": "Shopping", "description": "Clothes"},
            {"txn_date": "2026-10-10", "txn_type": "Expense", "amount": 1000.0, "category": "Shopping", "description": "Shoes"},
            {"txn_date": "2026-11-05", "txn_type": "Expense", "amount": 2500.0, "category": "Shopping", "description": "Winter Jacket"},
            {"txn_date": "2026-11-01", "txn_type": "Income", "amount": 25000.0, "category": "Salary", "description": "Salary"},
        ]
        tx = pd.DataFrame(rows)
        insights = generate_coach_insights(tx, None, None, as_of_date=self.as_of)
        surge_recs = [r for r in insights if r["rec_type"] == "Category Surge Warning"]
        self.assertEqual(len(surge_recs), 1)
        rec = surge_recs[0]
        self.assertIn("Shopping", rec["observation"])
        self.assertEqual(rec["estimated_monthly_impact"], 1500.0)
        self.assertEqual(rec["severity"], "warning")

    def test_upcoming_bill_recommendation(self):
        # Bill due in 3 days (Nov 13, 2026)
        bills = pd.DataFrame([
            {"description": "Electricity Bill", "amount": 2500.0, "due_date": "2026-11-13", "paid": 0},
            {"description": "Rent Next Month", "amount": 10000.0, "due_date": "2026-12-01", "paid": 0},  # > 7 days away
        ])
        tx = pd.DataFrame([
            {"txn_date": "2026-11-01", "txn_type": "Income", "amount": 30000.0, "category": "Salary", "description": "Pay"},
        ])
        insights = generate_coach_insights(tx, None, bills, as_of_date=self.as_of)
        bill_recs = [r for r in insights if r["rec_type"] == "Upcoming Bill Warning"]
        self.assertEqual(len(bill_recs), 1)
        rec = bill_recs[0]
        self.assertEqual(rec["estimated_monthly_impact"], 2500.0)
        self.assertIn("Electricity Bill", rec["observation"])

    def test_recurring_transaction_evidence(self):
        # 12 transactions with repeated "Netflix" description across different months
        rows = []
        for m in ["2026-08", "2026-09", "2026-10", "2026-11"]:
            rows.append({"txn_date": f"{m}-05", "txn_type": "Expense", "amount": 650.0, "category": "Subscriptions", "description": "Netflix Subscription"})
            rows.append({"txn_date": f"{m}-01", "txn_type": "Income", "amount": 30000.0, "category": "Salary", "description": "Salary"})
            rows.append({"txn_date": f"{m}-15", "txn_type": "Expense", "amount": 2000.0, "category": "Food", "description": "Dining"})
        tx = pd.DataFrame(rows)
        insights = generate_coach_insights(tx, None, None, as_of_date=self.as_of)
        sub_recs = [r for r in insights if r["rec_type"] == "Recurring Subscription Audit"]
        self.assertEqual(len(sub_recs), 1)
        rec = sub_recs[0]
        self.assertIn("Netflix Subscription", rec["observation"])
        self.assertGreater(rec["estimated_monthly_impact"], 0.0)

    def test_correct_savings_calculation_and_no_fabricated_figures(self):
        # Income = 40,000, Expenses = 36,000. Savings = 4,000 (10%).
        # Recommended 20% = 8,000. Gap = 4,000.
        tx = pd.DataFrame([
            {"txn_date": "2026-11-01", "txn_type": "Income", "amount": 40000.0, "category": "Salary", "description": "Salary"},
            {"txn_date": "2026-11-05", "txn_type": "Expense", "amount": 36000.0, "category": "Rent", "description": "House Rent"},
        ])
        insights = generate_coach_insights(tx, None, None, as_of_date=self.as_of)
        savings_recs = [r for r in insights if r["rec_type"] == "Savings Opportunity"]
        self.assertEqual(len(savings_recs), 1)
        rec = savings_recs[0]
        self.assertEqual(rec["estimated_monthly_impact"], 4000.0)
        self.assertIn("10.0%", rec["observation"])
        self.assertIn("₹40,000.00", rec["supporting_evidence"])
        self.assertIn("₹36,000.00", rec["supporting_evidence"])


if __name__ == "__main__":
    unittest.main()
