"""Unit tests for CSV import validation and duplicate prevention."""
from __future__ import annotations

import unittest
import pandas as pd

from src.services.csv_service import clean_and_validate_csv


class TestCsvImportService(unittest.TestCase):
    def setUp(self):
        self.existing_db_tx = pd.DataFrame([
            {"id": 1, "txn_date": "2026-11-01", "txn_type": "Income", "description": "Monthly Salary", "amount": 35000.0, "category": "Salary", "notes": ""},
            {"id": 2, "txn_date": "2026-11-02", "txn_type": "Expense", "description": "Groceries at supermarket", "amount": 1250.0, "category": "Groceries", "notes": ""},
        ])

    def test_valid_csv_rows(self):
        csv_df = pd.DataFrame([
            {"date": "2026-11-03", "type": "Expense", "description": "Swiggy Dinner", "amount": "450", "category": "Food"},
            {"date": "2026-11-04", "type": "Expense", "description": "Metro Ticket", "amount": "60", "category": "Transport"},
        ])
        res = clean_and_validate_csv(csv_df, self.existing_db_tx)
        self.assertEqual(res["summary"]["valid_count"], 2)
        self.assertEqual(res["summary"]["invalid_count"], 0)
        self.assertEqual(res["summary"]["skipped_file_dup_count"], 0)
        self.assertEqual(res["summary"]["skipped_db_dup_count"], 0)

    def test_in_file_duplicate_detection(self):
        # Two identical rows in the same CSV
        csv_df = pd.DataFrame([
            {"date": "2026-11-05", "type": "Expense", "description": "Coffee with friends", "amount": "250"},
            {"date": "2026-11-05", "type": "Expense", "description": "Coffee with friends", "amount": "250"},
        ])
        res = clean_and_validate_csv(csv_df, self.existing_db_tx)
        self.assertEqual(res["summary"]["valid_count"], 1)
        self.assertEqual(res["summary"]["skipped_file_dup_count"], 1)
        self.assertIn("Duplicate record within uploaded CSV", res["skipped_df"].iloc[0]["rejection_reason"])

    def test_cross_database_duplicate_detection(self):
        # Matches existing row in self.existing_db_tx
        csv_df = pd.DataFrame([
            {"date": "2026-11-01", "type": "Income", "description": "Monthly Salary", "amount": "35000"},
            {"date": "2026-11-06", "type": "Expense", "description": "New Book", "amount": "400"},
        ])
        res = clean_and_validate_csv(csv_df, self.existing_db_tx)
        self.assertEqual(res["summary"]["valid_count"], 1)
        self.assertEqual(res["summary"]["skipped_db_dup_count"], 1)
        self.assertIn("already exists in database", res["skipped_df"].iloc[0]["rejection_reason"])

    def test_invalid_csv_rows(self):
        csv_df = pd.DataFrame([
            {"date": "not-a-date", "type": "Expense", "description": "Bad Date Item", "amount": "100"},
            {"date": "2026-11-07", "type": "Expense", "description": "Negative Amount", "amount": "-500"},
            {"date": "2026-11-08", "type": "Expense", "description": "", "amount": "200"},
            {"date": "2026-11-09", "type": "Expense", "description": "Zero Amount", "amount": "0"},
            {"date": "2026-11-10", "type": "Expense", "description": "Valid Item", "amount": "350"},
        ])
        res = clean_and_validate_csv(csv_df, self.existing_db_tx)
        self.assertEqual(res["summary"]["valid_count"], 1)
        self.assertEqual(res["summary"]["invalid_count"], 4)
        reasons = res["invalid_df"]["rejection_reason"].tolist()
        self.assertTrue(any("Invalid date" in r for r in reasons))
        self.assertTrue(any("Amount must be strictly positive" in r for r in reasons))
        self.assertTrue(any("Description is empty" in r for r in reasons))


if __name__ == "__main__":
    unittest.main()
