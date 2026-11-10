"""Transactions router — CRUD, CSV import/export, category prediction."""
from __future__ import annotations

import io
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse

from backend.auth.dependencies import get_current_user, AuthenticatedUser
from backend.dependencies import get_transactions_df
from backend.schemas.transactions import (
    TransactionIn,
    TransactionOut,
    TransactionUpdate,
    PredictCategoryIn,
    PredictCategoryOut,
    ConfirmImportIn,
    CSVImportSummary,
)
import src.database as db
from src.services.transaction_service import filter_transactions
from src.services.csv_service import clean_and_validate_csv

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _row_to_out(row: dict) -> TransactionOut:
    return TransactionOut(
        id=int(row["id"]),
        txn_date=str(row["txn_date"]),
        txn_type=str(row["txn_type"]),
        description=str(row["description"]),
        amount=float(row["amount"]),
        category=str(row["category"]),
        notes=str(row.get("notes", "")),
    )


@router.get("", response_model=dict)
def list_transactions(
    search: str = Query(default=""),
    txn_type: str = Query(default="All"),
    category: str = Query(default="All"),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    min_amount: Optional[float] = Query(default=None),
    max_amount: Optional[float] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """List transactions with optional filtering, pagination for current user."""
    df = get_transactions_df(user_id=current_user.id)
    if df.empty:
        return {"data": [], "total": 0, "limit": limit, "offset": offset}

    filtered = filter_transactions(
        df,
        search_query=search,
        start_date=start_date,
        end_date=end_date,
        category=category,
        txn_type=txn_type,
        min_amount=min_amount,
        max_amount=max_amount,
    )

    total = len(filtered)
    page = filtered.iloc[offset: offset + limit]
    data = [_row_to_out(r).model_dump() for r in page.to_dict(orient="records")]
    return {"data": data, "total": total, "limit": limit, "offset": offset}


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(
    payload: TransactionIn,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Add a new transaction for current user."""
    new_id = db.add_transaction(
        txn_date=payload.txn_date,
        txn_type=payload.txn_type,
        description=payload.description,
        amount=payload.amount,
        category=payload.category,
        notes=payload.notes,
        user_id=current_user.id,
    )
    df = get_transactions_df(user_id=current_user.id)
    row = df[df["id"] == new_id]
    if row.empty:
        raise HTTPException(status_code=500, detail="Transaction created but not found.")
    return _row_to_out(row.iloc[0].to_dict())


@router.put("/{txn_id}", response_model=TransactionOut)
def update_transaction(
    txn_id: int,
    payload: TransactionUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Update an existing transaction by ID for current user."""
    df = get_transactions_df(user_id=current_user.id)
    if df.empty or df[df["id"] == txn_id].empty:
        raise HTTPException(status_code=404, detail=f"Transaction #{txn_id} not found.")

    db.update_transaction(
        txn_id=txn_id,
        txn_date=payload.txn_date,
        txn_type=payload.txn_type,
        description=payload.description,
        amount=payload.amount,
        category=payload.category,
        notes=payload.notes,
        user_id=current_user.id,
    )
    df2 = get_transactions_df(user_id=current_user.id)
    row = df2[df2["id"] == txn_id]
    if row.empty:
        raise HTTPException(status_code=500, detail="Transaction updated but not found.")
    return _row_to_out(row.iloc[0].to_dict())


@router.delete("/{txn_id}", status_code=200)
def delete_transaction(
    txn_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete a transaction by ID for current user."""
    df = get_transactions_df(user_id=current_user.id)
    if df.empty or df[df["id"] == txn_id].empty:
        raise HTTPException(status_code=404, detail=f"Transaction #{txn_id} not found.")
    db.delete_transaction(txn_id, user_id=current_user.id)
    return {"deleted": txn_id, "message": f"Transaction #{txn_id} deleted."}


@router.post("/predict-category", response_model=PredictCategoryOut)
def predict_category_endpoint(
    payload: PredictCategoryIn,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Predict the category for a transaction description using ML + keyword fallback."""
    tx_df = get_transactions_df(user_id=current_user.id)
    try:
        from src.ml.categorization import predict_category
        cat, method, confidence = predict_category(
            description=payload.description,
            txn_type=payload.txn_type,
            transactions=tx_df if not tx_df.empty else None,
        )
        return PredictCategoryOut(
            category=cat,
            method=method,
            confidence=confidence,
        )
    except Exception:
        from utils import suggest_category
        fallback = suggest_category(payload.description, payload.txn_type)
        return PredictCategoryOut(category=fallback, method="keyword_fallback", confidence=None)


@router.post("/import-csv", response_model=CSVImportSummary)
async def import_csv(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Upload a CSV file, validate rows, and return a preview for current user."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    contents = await file.read()
    file_obj = io.BytesIO(contents)

    existing = get_transactions_df(user_id=current_user.id)
    result = clean_and_validate_csv(file_obj, existing_transactions=existing if not existing.empty else None)

    summary = result["summary"]
    valid_df: pd.DataFrame = result["valid_df"]
    invalid_df: pd.DataFrame = result["invalid_df"]

    preview = valid_df.head(10).to_dict(orient="records") if not valid_df.empty else []
    invalid_preview = invalid_df.head(5).to_dict(orient="records") if not invalid_df.empty else []

    return CSVImportSummary(
        total_rows=summary["total_rows"],
        valid_count=summary["valid_count"],
        skipped_file_dup_count=summary["skipped_file_dup_count"],
        skipped_db_dup_count=summary["skipped_db_dup_count"],
        invalid_count=summary["invalid_count"],
        error=summary.get("error"),
        preview=preview,
        invalid_preview=invalid_preview,
    )


@router.post("/confirm-import", status_code=200)
def confirm_import(
    payload: ConfirmImportIn,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Bulk-insert pre-validated CSV rows into the database for current user."""
    if not payload.rows:
        return {"inserted": 0, "message": "No rows to import."}

    rows_tuples = []
    for r in payload.rows:
        try:
            rows_tuples.append((
                str(r["txn_date"]),
                str(r["txn_type"]),
                str(r["description"]),
                float(r["amount"]),
                str(r["category"]),
                str(r.get("notes", "")),
            ))
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"Invalid row data: {exc}")

    inserted = db.bulk_add_transactions(rows_tuples, user_id=current_user.id)
    return {"inserted": inserted, "message": f"Successfully imported {inserted} transactions."}


@router.get("/export-csv")
def export_csv(
    search: str = Query(default=""),
    txn_type: str = Query(default="All"),
    category: str = Query(default="All"),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Export filtered transactions as a downloadable CSV for current user."""
    df = get_transactions_df(user_id=current_user.id)
    if df.empty:
        filtered = pd.DataFrame(columns=["id", "txn_date", "txn_type", "description", "amount", "category", "notes"])
    else:
        filtered = filter_transactions(
            df,
            search_query=search,
            txn_type=txn_type,
            category=category,
            start_date=start_date,
            end_date=end_date,
        )

    output = io.StringIO()
    cols = ["id", "txn_date", "txn_type", "description", "amount", "category", "notes"]
    for c in cols:
        if c not in filtered.columns:
            filtered[c] = ""
    filtered[cols].to_csv(output, index=False)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=finpilot_transactions.csv"},
    )
