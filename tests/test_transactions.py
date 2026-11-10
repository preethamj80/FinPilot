"""Unit tests for transaction search, filtering, and deletion validation."""
from __future__ import annotations

import unittest
import pandas as pd
from datetime import date

from src.services.transaction_service import filter_transactions, validate_delete_transaction, get_transaction_by_id


class TestTransactionService(unittest.TestCase):
    def setUp(self):
        self.sample_tx = pd.DataFrame([
            {"id": 1, "txn_date": "2026-11-01", "txn_type": "Income", "description": "Monthly Salary", "amount": 35000.0, "category": "Salary", "notes": ""},
            {"id": 2, "txn_date": "2026-11-02", "txn_type": "Expense", "description": "Swiggy Dinner", "amount": 450.0, "category": "Food", "notes": "Pizza"},
            {"id": 3, "txn_date": "2026-11-03", "txn_type": "Expense", "description": "Supermarket Groceries", "amount": 1800.0, "category": "Groceries", "notes": ""},
            {"id": 4, "txn_date": "2026-11-05", "txn_type": "Expense", "description": "Uber Ride to Airport", "amount": 650.0, "category": "Transport", "notes": ""},
            {"id": 5, "txn_date": "2026-10-25", "txn_type": "Expense", "description": "Amazon Shoes", "amount": 2200.0, "category": "Shopping", "notes": ""},
        ])

    def test_search_by_description(self):
        # Case insensitive substring search
        res = filter_transactions(self.sample_tx, search_query="swiggy")
        self.assertEqual(len(res), 1)
        self.assertEqual(res.iloc[0]["description"], "Swiggy Dinner")

        res_uber = filter_transactions(self.sample_tx, search_query="UBER")
        self.assertEqual(len(res_uber), 1)
        self.assertEqual(res_uber.iloc[0]["id"], 4)

        res_none = filter_transactions(self.sample_tx, search_query="NonExistent")
        self.assertTrue(res_none.empty)

    def test_filter_by_date_range(self):
        res = filter_transactions(self.sample_tx, start_date="2026-11-01", end_date="2026-11-03")
        self.assertEqual(len(res), 3)
        self.assertTrue(all(d >= "2026-11-01" and d <= "2026-11-03" for d in res["txn_date"]))

        res_oct = filter_transactions(self.sample_tx, end_date="2026-10-31")
        self.assertEqual(len(res_oct), 1)
        self.assertEqual(res_oct.iloc[0]["description"], "Amazon Shoes")

    def test_filter_by_txn_type(self):
        income = filter_transactions(self.sample_tx, txn_type="Income")
        self.assertEqual(len(income), 1)
        self.assertEqual(income.iloc[0]["amount"], 35000.0)

        expense = filter_transactions(self.sample_tx, txn_type="Expense")
        self.assertEqual(len(expense), 4)

    def test_filter_by_category(self):
        food = filter_transactions(self.sample_tx, category="Food")
        self.assertEqual(len(food), 1)
        self.assertEqual(food.iloc[0]["id"], 2)

        multi = filter_transactions(self.sample_tx, category=["Food", "Transport"])
        self.assertEqual(len(multi), 2)

    def test_filter_by_amount_range(self):
        filtered = filter_transactions(self.sample_tx, min_amount=1000.0, max_amount=3000.0)
        self.assertEqual(len(filtered), 2)
        self.assertCountEqual(filtered["id"].tolist(), [3, 5])

    def test_validate_delete_transaction(self):
        valid, msg = validate_delete_transaction(2, self.sample_tx)
        self.assertTrue(valid)
        self.assertIn("Ready to delete", msg)
        self.assertIn("Swiggy Dinner", msg)

        invalid, err_msg = validate_delete_transaction(999, self.sample_tx)
        self.assertFalse(invalid)
        self.assertIn("not found", err_msg)


if __name__ == "__main__":
    unittest.main()
