"""Data cleaning, category suggestions, and demo data helpers."""
from __future__ import annotations

from datetime import date, timedelta
import random
import re

import pandas as pd

CATEGORIES = [
    "Food", "Groceries", "Transport", "Shopping", "Rent", "Utilities",
    "Health", "Education", "Entertainment", "Travel", "Personal Care",
    "Subscriptions", "Salary", "Freelance", "Investment", "Other",
]
EXPENSE_CATEGORIES = [c for c in CATEGORIES if c not in {"Salary", "Freelance", "Investment"}]
INCOME_CATEGORIES = ["Salary", "Freelance", "Investment", "Other"]

KEYWORDS = {
    "Food": ["swiggy", "zomato", "restaurant", "cafe", "pizza", "burger", "food", "lunch", "dinner"],
    "Groceries": ["grocery", "supermarket", "vegetables", "milk", "bigbasket", "dmart", "provision"],
    "Transport": ["uber", "ola", "bus", "metro", "petrol", "fuel", "taxi", "auto", "parking"],
    "Shopping": ["amazon", "flipkart", "shopping", "clothes", "shoes", "mall", "myntra"],
    "Rent": ["rent", "landlord", "house rent", "hostel", "pg"],
    "Utilities": ["electricity", "water bill", "internet", "wifi", "mobile recharge", "gas bill", "broadband"],
    "Health": ["pharmacy", "hospital", "doctor", "medicine", "clinic", "medical"],
    "Education": ["college", "course", "book", "tuition", "exam fee", "udemy"],
    "Entertainment": ["movie", "cinema", "netflix", "spotify", "game", "concert"],
    "Travel": ["flight", "hotel", "train", "bus ticket", "trip", "booking.com"],
    "Personal Care": ["salon", "haircut", "grooming", "skin care", "personal care"],
    "Subscriptions": ["subscription", "prime", "icloud", "membership"],
    "Salary": ["salary", "payroll", "monthly pay"],
    "Freelance": ["freelance", "client payment", "project payment"],
    "Investment": ["dividend", "interest", "returns"],
}


def suggest_category(description: str, txn_type: str = "Expense") -> str:
    text = re.sub(r"[^a-z0-9 ]", " ", str(description).lower())
    for category, words in KEYWORDS.items():
        if any(word in text for word in words):
            if txn_type == "Income" and category in INCOME_CATEGORIES:
                return category
            if txn_type == "Expense" and category in EXPENSE_CATEGORIES:
                return category
    return "Other"


def clean_transaction_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Accept common CSV column names and return normalized transactions."""
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["txn_date", "txn_type", "description", "amount", "category", "notes"]), ["The uploaded file is empty."]
    df = frame.copy()
    aliases = {
        "date": "txn_date", "transaction_date": "txn_date", "txn_date": "txn_date",
        "type": "txn_type", "transaction_type": "txn_type", "txn_type": "txn_type",
        "description": "description", "details": "description", "merchant": "description", "narration": "description",
        "amount": "amount", "category": "category", "notes": "notes",
    }
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    rename = {c: aliases[c] for c in df.columns if c in aliases}
    df = df.rename(columns=rename)
    errors: list[str] = []
    required = ["txn_date", "amount", "description"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return pd.DataFrame(), ["Missing required CSV column(s): " + ", ".join(missing) + ". Required: date, amount, description."]

    df["txn_date"] = pd.to_datetime(df["txn_date"], errors="coerce", dayfirst=True).dt.strftime("%Y-%m-%d")
    df["amount"] = pd.to_numeric(df["amount"].astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False).str.strip(), errors="coerce")
    df["description"] = df["description"].fillna("").astype(str).str.strip()
    if "txn_type" not in df.columns:
        df["txn_type"] = "Expense"
    df["txn_type"] = df["txn_type"].fillna("Expense").astype(str).str.strip().str.title()
    df.loc[~df["txn_type"].isin(["Income", "Expense"]), "txn_type"] = "Expense"
    if "category" not in df.columns:
        df["category"] = "Other"
    df["category"] = df["category"].fillna("").astype(str).str.strip()
    df.loc[df["category"] == "", "category"] = df.loc[df["category"] == "", "description"].apply(suggest_category)
    if "notes" not in df.columns:
        df["notes"] = ""
    df["notes"] = df["notes"].fillna("").astype(str)

    invalid = df["txn_date"].isna() | df["amount"].isna() | (df["amount"] <= 0) | (df["description"] == "")
    if invalid.any():
        errors.append(f"Skipped {int(invalid.sum())} invalid row(s): check dates, positive amounts and descriptions.")
    valid = df.loc[~invalid, ["txn_date", "txn_type", "description", "amount", "category", "notes"]].copy()
    valid["amount"] = valid["amount"].astype(float)
    valid = valid.drop_duplicates(subset=["txn_date", "txn_type", "description", "amount"])
    return valid, errors


def make_demo_transactions() -> pd.DataFrame:
    """Generate clearly synthetic transactions spanning 12 months for a demo."""
    rng = random.Random(42)
    today = date.today()
    rows = []
    monthly_salary = 32000.0
    expenses = {
        "Rent": (8500, 0.0), "Food": (2800, 450), "Groceries": (2200, 350),
        "Transport": (1200, 250), "Shopping": (1500, 700), "Utilities": (1100, 180),
        "Entertainment": (900, 350), "Health": (500, 300), "Education": (700, 300),
    }
    for offset in range(11, -1, -1):
        month_start = (today.replace(day=1) - pd.DateOffset(months=offset)).date()
        y, m = month_start.year, month_start.month
        rows.append({"txn_date": date(y, m, min(1, 28)).isoformat(), "txn_type": "Income",
                     "description": "Monthly salary (DEMO DATA)", "amount": monthly_salary,
                     "category": "Salary", "notes": "Synthetic demonstration record"})
        for category, (base, spread) in expenses.items():
            amount = max(100, rng.gauss(base + offset * 8, max(100, spread)))
            day = rng.randint(2, 26)
            try:
                txn_day = date(y, m, min(day, 28))
            except ValueError:
                txn_day = date(y, m, 28)
            rows.append({"txn_date": txn_day.isoformat(), "txn_type": "Expense",
                         "description": f"{category} payment (DEMO DATA)", "amount": round(amount, 2),
                         "category": category, "notes": "Synthetic demonstration record; not real financial data"})
    return pd.DataFrame(rows)
