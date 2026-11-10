"""Robust CSV import service with duplicate detection and row-level validation."""
from __future__ import annotations

import io
from typing import Any
import pandas as pd

from src.config import CATEGORIES, EXPENSE_CATEGORIES, INCOME_CATEGORIES
from utils import suggest_category


def parse_date_robust(raw_val: Any) -> pd.Timestamp | None:
    """Parse various date formats robustly without swapping year-first months and days."""
    if pd.isna(raw_val):
        return None
    val_str = str(raw_val).strip()
    if not val_str:
        return None
    # 1. Try ISO YYYY-MM-DD
    try:
        return pd.to_datetime(val_str, format="%Y-%m-%d")
    except Exception:
        pass
    # 2. Try ISO8601
    try:
        return pd.to_datetime(val_str, format="ISO8601")
    except Exception:
        pass
    # 3. Try mixed format with dayfirst=True for DD-MM-YYYY or DD/MM/YYYY
    try:
        return pd.to_datetime(val_str, format="mixed", dayfirst=True)
    except Exception:
        pass
    # 4. Fallback
    try:
        res = pd.to_datetime(val_str, errors="coerce")
        return None if pd.isna(res) else res
    except Exception:
        return None


def clean_and_validate_csv(
    file_or_df: Any,
    existing_transactions: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Parse, validate, and audit transaction records from an uploaded CSV.
    
    Returns a dictionary with:
    - valid_df: Cleaned transactions ready for insertion.
    - skipped_df: Duplicates within the file or existing in the database.
    - invalid_df: Malformed rows with error descriptions.
    - summary: Statistics on rows processed.
    """
    # 1. Ingest into DataFrame
    if isinstance(file_or_df, pd.DataFrame):
        df = file_or_df.copy()
    else:
        try:
            if hasattr(file_or_df, "read"):
                # Handle Streamlit UploadedFile or BytesIO
                df = pd.read_csv(file_or_df)
            else:
                df = pd.read_csv(str(file_or_df))
        except Exception as exc:
            return {
                "valid_df": pd.DataFrame(),
                "skipped_df": pd.DataFrame(),
                "invalid_df": pd.DataFrame(),
                "summary": {
                    "total_rows": 0,
                    "valid_count": 0,
                    "skipped_file_dup_count": 0,
                    "skipped_db_dup_count": 0,
                    "invalid_count": 0,
                    "error": f"Failed to parse CSV file: {exc}",
                },
            }

    if df.empty:
        return {
            "valid_df": pd.DataFrame(),
            "skipped_df": pd.DataFrame(),
            "invalid_df": pd.DataFrame(),
            "summary": {
                "total_rows": 0,
                "valid_count": 0,
                "skipped_file_dup_count": 0,
                "skipped_db_dup_count": 0,
                "invalid_count": 0,
                "error": "The uploaded CSV file contains no data rows.",
            },
        }

    # Normalize column names
    aliases = {
        "date": "txn_date", "transaction_date": "txn_date", "txn_date": "txn_date",
        "type": "txn_type", "transaction_type": "txn_type", "txn_type": "txn_type",
        "description": "description", "details": "description", "merchant": "description", "narration": "description",
        "amount": "amount", "value": "amount",
        "category": "category",
        "notes": "notes", "memo": "notes", "remarks": "notes",
    }
    cleaned_cols = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    rename_map = {orig: aliases[norm] for orig, norm in zip(df.columns, cleaned_cols) if norm in aliases}
    df = df.rename(columns=rename_map)

    required_cols = ["txn_date", "amount", "description"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return {
            "valid_df": pd.DataFrame(),
            "skipped_df": pd.DataFrame(),
            "invalid_df": pd.DataFrame(),
            "summary": {
                "total_rows": len(df),
                "valid_count": 0,
                "skipped_file_dup_count": 0,
                "skipped_db_dup_count": 0,
                "invalid_count": len(df),
                "error": f"Missing required CSV column(s): {', '.join(missing)}. File must include: date, amount, description.",
            },
        }

    valid_rows = []
    skipped_rows = []
    invalid_rows = []

    # Build lookup set for existing database records: (date, type, description_lower, amount_2dec)
    existing_keys: set[tuple[str, str, str, float]] = set()
    if existing_transactions is not None and not existing_transactions.empty:
        for r in existing_transactions.itertuples():
            try:
                d_str = pd.to_datetime(r.txn_date).strftime("%Y-%m-%d")
                t_str = str(r.txn_type).strip().title()
                desc_str = str(r.description).strip().lower()
                amt_val = round(float(r.amount), 2)
                existing_keys.add((d_str, t_str, desc_str, amt_val))
            except Exception:
                continue

    # Seen keys within the current uploaded batch
    seen_in_batch: set[tuple[str, str, str, float]] = set()

    for idx, raw_row in df.iterrows():
        row_num = idx + 2  # 1-based index accounting for CSV header
        raw_dict = raw_row.to_dict()

        # 1. Validate Date
        raw_date = raw_row.get("txn_date")
        parsed_date = parse_date_robust(raw_date)
        if parsed_date is None or pd.isna(parsed_date):
            raw_dict["row_num"] = row_num
            raw_dict["rejection_reason"] = f"Invalid date format: '{raw_date}'"
            invalid_rows.append(raw_dict)
            continue
        norm_date = parsed_date.strftime("%Y-%m-%d")

        # 2. Validate Amount
        raw_amt = raw_row.get("amount")
        try:
            cleaned_amt_str = (
                str(raw_amt)
                .replace(",", "")
                .replace("₹", "")
                .replace("$", "")
                .strip()
            )
            amt = float(cleaned_amt_str)
            if amt <= 0 or pd.isna(amt):
                raw_dict["row_num"] = row_num
                raw_dict["rejection_reason"] = f"Amount must be strictly positive (found: '{raw_amt}')"
                invalid_rows.append(raw_dict)
                continue
            amt = round(amt, 2)
        except (ValueError, TypeError):
            raw_dict["row_num"] = row_num
            raw_dict["rejection_reason"] = f"Unparseable numeric amount: '{raw_amt}'"
            invalid_rows.append(raw_dict)
            continue

        # 3. Validate Description
        raw_desc = str(raw_row.get("description", "")).strip()
        if not raw_desc or raw_desc.lower() == "nan":
            raw_dict["row_num"] = row_num
            raw_dict["rejection_reason"] = "Description is empty"
            invalid_rows.append(raw_dict)
            continue

        # 4. Normalize Transaction Type
        raw_type = str(raw_row.get("txn_type", "Expense")).strip().title()
        if raw_type not in ["Income", "Expense"]:
            raw_type = "Expense"

        # 5. Normalize Category
        raw_cat = str(raw_row.get("category", "")).strip()
        if not raw_cat or raw_cat.lower() == "nan":
            raw_cat = suggest_category(raw_desc, raw_type)
        else:
            raw_cat = raw_cat.title()
            if raw_cat not in CATEGORIES:
                # If custom or close match
                raw_cat = raw_cat if raw_cat else suggest_category(raw_desc, raw_type)

        # 6. Notes
        raw_notes = str(raw_row.get("notes", "")).strip()
        if raw_notes.lower() == "nan":
            raw_notes = ""

        # Duplicate key: exact combination of date, type, description (case-insensitive), and amount
        dup_key = (norm_date, raw_type, raw_desc.lower(), amt)

        # 7. Check In-File Duplicate
        if dup_key in seen_in_batch:
            raw_dict["row_num"] = row_num
            raw_dict["rejection_reason"] = "Duplicate record within uploaded CSV file"
            skipped_rows.append(raw_dict)
            continue

        # 8. Check Database Duplicate
        if dup_key in existing_keys:
            raw_dict["row_num"] = row_num
            raw_dict["rejection_reason"] = f"Exact duplicate already exists in database ({norm_date} · {raw_type} · ₹{amt:,.2f})"
            skipped_rows.append(raw_dict)
            continue

        # Mark as seen in this batch
        seen_in_batch.add(dup_key)

        valid_rows.append({
            "txn_date": norm_date,
            "txn_type": raw_type,
            "description": raw_desc,
            "amount": amt,
            "category": raw_cat,
            "notes": raw_notes,
        })

    valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=["txn_date", "txn_type", "description", "amount", "category", "notes"])
    skipped_df = pd.DataFrame(skipped_rows) if skipped_rows else pd.DataFrame()
    invalid_df = pd.DataFrame(invalid_rows) if invalid_rows else pd.DataFrame()

    file_dups = sum(1 for r in skipped_rows if "within uploaded CSV" in r.get("rejection_reason", ""))
    db_dups = sum(1 for r in skipped_rows if "already exists in database" in r.get("rejection_reason", ""))

    return {
        "valid_df": valid_df,
        "skipped_df": skipped_df,
        "invalid_df": invalid_df,
        "summary": {
            "total_rows": len(df),
            "valid_count": len(valid_rows),
            "skipped_file_dup_count": file_dups,
            "skipped_db_dup_count": db_dups,
            "invalid_count": len(invalid_rows),
            "error": None,
        },
    }
