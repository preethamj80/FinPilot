"""Transaction categorization using TF-IDF + Random Forest with model persistence,

cross-validation evaluation, and explainable keyword fallback.
"""
from __future__ import annotations

import datetime
import hashlib
import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline

from src.config import MODELS_DIR
from utils import suggest_category

_IN_MEMORY_MODEL_CACHE: dict[str, Any] = {}
MODEL_PATH = MODELS_DIR / "category_model.joblib"


def _persist_models_locally() -> bool:
    """Avoid writing models trained on hosted user records to Render's disk."""
    return os.getenv("FINPILOT_ENV", "development").lower() != "production"


def _compute_dataset_hash(df: pd.DataFrame) -> str:
    """Compute MD5 hash of training data to detect changes."""
    content = "|".join(
        f"{str(d)}:{str(c)}"
        for d, c in zip(df["description"].astype(str), df["category"].astype(str))
    )
    return hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()


def check_training_eligibility(transactions: pd.DataFrame, txn_type: str = "Expense") -> tuple[bool, str, pd.DataFrame]:
    """Check if there is sufficient and balanced data to train the ML categorizer."""
    if transactions is None or transactions.empty:
        return False, "No transactions available for training.", pd.DataFrame()

    df = transactions[transactions["txn_type"] == txn_type].copy()
    df = df.dropna(subset=["description", "category"])
    df["description"] = df["description"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df = df[df["description"].str.len() > 1]

    if len(df) < 25:
        return (
            False,
            f"Insufficient training volume: {len(df)} labelled records found (at least 25 required for Random Forest).",
            df,
        )

    n_cats = df["category"].nunique()
    if n_cats < 2:
        return (
            False,
            f"Insufficient class diversity: Only {n_cats} category found (at least 2 distinct categories required).",
            df,
        )

    return True, f"Eligible for training: {len(df)} records across {n_cats} categories.", df


def train_or_load_categorizer(
    transactions: pd.DataFrame,
    txn_type: str = "Expense",
    force_retrain: bool = False,
) -> dict[str, Any]:
    """Load cached/persisted model if available and unchanged; otherwise train,

    evaluate with cross-validation, persist to disk, and return evaluation diagnostics.
    """
    global _IN_MEMORY_MODEL_CACHE

    eligible, reason, train_df = check_training_eligibility(transactions, txn_type)
    if not eligible:
        return {
            "status": "insufficient_data",
            "message": reason,
            "pipeline": None,
            "metrics": None,
            "per_class_metrics": [],
            "top_confusions": [],
            "class_distribution": {},
            "record_count": len(train_df),
        }

    dataset_hash = _compute_dataset_hash(train_df)

    # 1. Check in-memory cache
    if not force_retrain and _IN_MEMORY_MODEL_CACHE.get("hash") == dataset_hash:
        return _IN_MEMORY_MODEL_CACHE["data"]

    # 2. Check disk persistence in local mode only. Hosted models are trained
    # per request from that user's data and remain in memory for this process.
    if _persist_models_locally() and not force_retrain and MODEL_PATH.exists():
        try:
            persisted = joblib.load(MODEL_PATH)
            if persisted.get("dataset_hash") == dataset_hash:
                _IN_MEMORY_MODEL_CACHE["hash"] = dataset_hash
                _IN_MEMORY_MODEL_CACHE["data"] = persisted
                return persisted
        except Exception:
            # Corrupt file or version mismatch; proceed to retrain
            pass

    # 3. Train fresh model and evaluate
    X = train_df["description"].astype(str)
    y = train_df["category"].astype(str)

    # Class distribution analysis
    counts = y.value_counts()
    class_distribution = {cat: {"count": int(cnt), "percentage": round((cnt / len(y)) * 100, 1)} for cat, cnt in counts.items()}

    # Pipeline definition
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=3000, sublinear_tf=True)),
        ("rf", RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")),
    ])

    # Model Evaluation (Holdout or Cross-Validation without leakage)
    min_class_count = counts.min()
    can_stratify = min_class_count >= 2

    metrics: dict[str, float] = {}
    top_confusions: list[dict[str, Any]] = []
    per_class_metrics: list[dict[str, Any]] = []

    try:
        if can_stratify and len(train_df) >= 30:
            # 80/20 Stratified train/test holdout for unbiased performance evaluation
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.20, random_state=42, stratify=y
            )
            eval_pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=3000, sublinear_tf=True)),
                ("rf", RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")),
            ])
            eval_pipeline.fit(X_train, y_train)
            y_pred = eval_pipeline.predict(X_test)

            metrics = {
                "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
                "precision": round(float(precision_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
                "recall": round(float(recall_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
                "f1": round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
                "eval_samples": len(y_test),
                "eval_method": "Stratified 80/20 Holdout",
            }

            # Per-class metrics
            report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            for cls_name, vals in report.items():
                if isinstance(vals, dict) and cls_name not in {"macro avg", "weighted avg"}:
                    per_class_metrics.append({
                        "category": cls_name,
                        "precision": round(vals["precision"], 2),
                        "recall": round(vals["recall"], 2),
                        "f1": round(vals["f1-score"], 2),
                        "support": int(vals["support"]),
                    })

            # Confusion Matrix Analysis
            unique_labels = sorted(list(set(y_test) | set(y_pred)))
            cm = confusion_matrix(y_test, y_pred, labels=unique_labels)
            for i, true_lbl in enumerate(unique_labels):
                for j, pred_lbl in enumerate(unique_labels):
                    if i != j and cm[i][j] > 0:
                        top_confusions.append({
                            "actual": true_lbl,
                            "predicted": pred_lbl,
                            "count": int(cm[i][j]),
                        })
            top_confusions.sort(key=lambda x: x["count"], reverse=True)
        else:
            # Fallback evaluation on smaller dataset
            pipeline.fit(X, y)
            y_pred = pipeline.predict(X)
            metrics = {
                "accuracy": round(float(accuracy_score(y, y_pred)), 4),
                "precision": round(float(precision_score(y, y_pred, average="weighted", zero_division=0)), 4),
                "recall": round(float(recall_score(y, y_pred, average="weighted", zero_division=0)), 4),
                "f1": round(float(f1_score(y, y_pred, average="weighted", zero_division=0)), 4),
                "eval_samples": len(y),
                "eval_method": "In-sample (Dataset too small or rare classes with single record)",
            }
    except Exception as e:
        metrics = {"error": str(e), "accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    # Fit full pipeline on all training records for deployment
    pipeline.fit(X, y)

    result_data = {
        "status": "trained",
        "message": f"Random Forest ({len(train_df)} records, {len(counts)} categories) trained and evaluated.",
        "pipeline": pipeline,
        "classes": list(pipeline.classes_),
        "metrics": metrics,
        "per_class_metrics": per_class_metrics,
        "top_confusions": top_confusions[:5],
        "class_distribution": class_distribution,
        "record_count": len(train_df),
        "dataset_hash": dataset_hash,
        "trained_at": datetime.datetime.now().isoformat(),
    }

    # Persist locally for development, but never write a user-trained model to
    # the hosted service's ephemeral filesystem.
    if _persist_models_locally():
        try:
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            joblib.dump(result_data, MODEL_PATH)
        except Exception:
            pass

    # Update in-memory cache
    _IN_MEMORY_MODEL_CACHE["hash"] = dataset_hash
    _IN_MEMORY_MODEL_CACHE["data"] = result_data

    return result_data


def predict_category(
    description: str,
    txn_type: str = "Expense",
    transactions: pd.DataFrame | None = None,
) -> tuple[str, str, float]:
    """Predict category with confidence score. Falls back to explainable keyword rules

    if confidence is low, transaction type is Income, or data is insufficient.
    Returns: (predicted_category, explanation, confidence)
    """
    if txn_type != "Expense" or not str(description).strip():
        kw_cat = suggest_category(description, txn_type)
        return kw_cat, "Deterministic keyword rule (Income / Non-expense)", 1.0

    if transactions is None or transactions.empty:
        kw_cat = suggest_category(description, txn_type)
        return kw_cat, "Keyword fallback (No transaction history available)", 0.50

    model_info = train_or_load_categorizer(transactions, txn_type)
    if model_info["status"] != "trained" or model_info["pipeline"] is None:
        kw_cat = suggest_category(description, txn_type)
        return kw_cat, f"Keyword fallback ({model_info['message']})", 0.60

    try:
        pipeline: Pipeline = model_info["pipeline"]
        clean_desc = [str(description).strip()]
        probs = pipeline.predict_proba(clean_desc)[0]
        max_idx = int(np.argmax(probs))
        confidence = float(probs[max_idx])
        predicted_class = str(pipeline.classes_[max_idx])

        # If model is uncertain (< 0.35 confidence), check keyword suggestion
        if confidence < 0.35:
            kw_cat = suggest_category(description, txn_type)
            if kw_cat != "Other":
                return (
                    kw_cat,
                    f"Keyword rule chosen (Model confidence was low: {confidence:.1%} for {predicted_class})",
                    confidence,
                )

        f1_str = f", F1: {model_info['metrics'].get('f1', 0):.2f}" if model_info.get("metrics") else ""
        return (
            predicted_class,
            f"Random Forest (Confidence: {confidence:.0%}{f1_str})",
            round(confidence, 2),
        )
    except Exception:
        kw_cat = suggest_category(description, txn_type)
        return kw_cat, "Keyword fallback (Model inference exception)", 0.50


def category_prediction(
    description: str,
    txn_type: str,
    transactions: pd.DataFrame,
) -> tuple[str, str]:
    """Backward-compatible wrapper returning (category, explanation)."""
    cat, explanation, _ = predict_category(description, txn_type, transactions)
    return cat, explanation
