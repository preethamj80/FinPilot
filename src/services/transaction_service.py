"""Transaction management service for search, filtering, and deletion validation."""
from __future__ import annotations

from datetime import date, datetime
import pandas as pd


def filter_transactions(
    df: pd.DataFrame,
    search_query: str = "",
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    category: str | list[str] = "All",
    txn_type: str = "All",
    min_amount: float | None = None,
    max_amount: float | None = None,
) -> pd.DataFrame:
    """Filter a transaction DataFrame using multi-criteria conditions without side effects."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["id", "txn_date", "txn_type", "description", "amount", "category", "notes"])

    result = df.copy()

    # Normalize dates if not already datetime
    if not pd.api.types.is_datetime64_any_dtype(result["txn_date"]):
        result["_dt"] = pd.to_datetime(result["txn_date"], errors="coerce")
    else:
        result["_dt"] = result["txn_date"]

    # 1. Search by description (case-insensitive substring)
    if search_query and search_query.strip():
        q = search_query.strip().lower()
        result = result[result["description"].astype(str).str.lower().str.contains(q, regex=False, na=False)]

    # 2. Date range filter
    if start_date is not None:
        start_ts = pd.to_datetime(start_date)
        result = result[result["_dt"] >= start_ts]

    if end_date is not None:
        end_ts = pd.to_datetime(end_date)
        result = result[result["_dt"] <= end_ts]

    # 3. Transaction type filter
    if txn_type and txn_type != "All":
        result = result[result["txn_type"].str.lower() == txn_type.strip().lower()]

    # 4. Category filter
    if category and category != "All":
        if isinstance(category, (list, tuple, set)):
            if len(category) > 0 and "All" not in category:
                result = result[result["category"].isin(category)]
        else:
            result = result[result["category"] == category]

    # 5. Amount range filter
    if min_amount is not None:
        result = result[result["amount"] >= float(min_amount)]

    if max_amount is not None:
        result = result[result["amount"] <= float(max_amount)]

    # Clean temporary helper column
    if "_dt" in result.columns:
        result = result.drop(columns=["_dt"])

    return result.sort_values(by=["txn_date", "id"], ascending=[False, False])


def get_transaction_by_id(df: pd.DataFrame, txn_id: int) -> dict | None:
    """Safely retrieve a single transaction by ID."""
    if df is None or df.empty:
        return None
    matches = df[df["id"] == int(txn_id)]
    if matches.empty:
        return None
    row = matches.iloc[0]
    return row.to_dict()


def validate_delete_transaction(txn_id: int, df: pd.DataFrame) -> tuple[bool, str]:
    """Validate whether a transaction can be safely deleted."""
    if df is None or df.empty:
        return False, "Transaction list is empty."
    matches = df[df["id"] == int(txn_id)]
    if matches.empty:
        return False, f"Transaction with ID #{txn_id} not found."
    row = matches.iloc[0]
    return True, f"Ready to delete: #{txn_id} ({row['txn_date']} - {row['description']} - ₹{float(row['amount']):,.2f})"
