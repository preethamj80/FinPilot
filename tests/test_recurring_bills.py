"""Unit and integration tests for recurring bills and idempotency."""
from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
import pandas as pd

from src.database import init_db, add_bill, get_bills, mark_bill_paid
import src.database as db_module
from src.services.budget_service import compute_next_due_date, process_recurring_bill_on_payment, sync_all_recurring_bills


class TestRecurringBills(unittest.TestCase):
    def setUp(self):
        # Create a temporary SQLite database for test isolation
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_db_path = Path(self.temp_dir.name) / "test_finance.db"
        init_db(self.temp_db_path)

    def tearDown(self):
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_compute_next_due_date(self):
        # Weekly (+7 days)
        self.assertEqual(compute_next_due_date("2026-11-01", "Weekly"), "2026-11-08")
        # Monthly (+1 calendar month)
        self.assertEqual(compute_next_due_date("2026-11-01", "Monthly"), "2026-12-01")
        # Yearly (+1 year)
        self.assertEqual(compute_next_due_date("2026-11-01", "Yearly"), "2027-11-01")
        # One-time returns empty string
        self.assertEqual(compute_next_due_date("2026-11-01", "One-time"), "")

    def test_recurring_monthly_bill_payment_creates_next_bill(self):
        # Add monthly bill
        bill_id = add_bill(
            description="Broadband Internet",
            amount=999.0,
            due_date="2026-11-15",
            frequency="Monthly",
            custom_path=self.temp_db_path,
        )
        bills_before = get_bills(self.temp_db_path)
        self.assertEqual(len(bills_before), 1)

        # Mark paid
        mark_bill_paid(bill_id, True, self.temp_db_path)
        bills_df = get_bills(self.temp_db_path)

        # Trigger recurring generation
        created, msg = process_recurring_bill_on_payment(bill_id, bills_df, db_module, self.temp_db_path)
        self.assertTrue(created)
        self.assertIn("2026-12-15", msg)

        # Verify new upcoming bill exists
        bills_after = get_bills(self.temp_db_path)
        self.assertEqual(len(bills_after), 2)
        new_bill = bills_after[bills_after["due_date"] == "2026-12-15"].iloc[0]
        self.assertEqual(new_bill["description"], "Broadband Internet")
        self.assertEqual(new_bill["paid"], 0)
        self.assertEqual(new_bill["frequency"], "Monthly")

    def test_idempotency_prevents_duplicate_recurring_bills(self):
        # Add weekly gym membership
        bill_id = add_bill(
            description="Weekly Personal Training",
            amount=500.0,
            due_date="2026-11-01",
            frequency="Weekly",
            custom_path=self.temp_db_path,
        )
        mark_bill_paid(bill_id, True, self.temp_db_path)

        # Run recurring generation first time
        bills_df = get_bills(self.temp_db_path)
        created1, _ = process_recurring_bill_on_payment(bill_id, bills_df, db_module, self.temp_db_path)
        self.assertTrue(created1)

        # Run recurring generation a SECOND time (e.g. page refresh)
        bills_df2 = get_bills(self.temp_db_path)
        created2, msg2 = process_recurring_bill_on_payment(bill_id, bills_df2, db_module, self.temp_db_path)
        self.assertFalse(created2)
        self.assertIn("already exists", msg2)

        # Run recurring generation a THIRD time via sync_all_recurring_bills
        logs = sync_all_recurring_bills(db_module, self.temp_db_path)
        self.assertEqual(len(logs), 0)

        # Ensure total bills count remains exactly 2 (the paid one and the single next one)
        total_bills = get_bills(self.temp_db_path)
        self.assertEqual(len(total_bills), 2)

    def test_one_time_bills_do_not_generate_recurring(self):
        bill_id = add_bill(
            description="One-time Dentist Visit",
            amount=1500.0,
            due_date="2026-11-10",
            frequency="One-time",
            custom_path=self.temp_db_path,
        )
        mark_bill_paid(bill_id, True, self.temp_db_path)
        bills_df = get_bills(self.temp_db_path)
        created, msg = process_recurring_bill_on_payment(bill_id, bills_df, db_module, self.temp_db_path)
        self.assertFalse(created)
        self.assertIn("One-time bill", msg)
        self.assertEqual(len(get_bills(self.temp_db_path)), 1)


if __name__ == "__main__":
    unittest.main()
