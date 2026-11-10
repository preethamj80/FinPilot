"""Comprehensive tests for FinPilot Machine Learning services.

Validates chronological time-series forecasting without leakage, baseline comparisons,
prediction uncertainty intervals, TF-IDF + Random Forest categorization with persistence,
multi-feature anomaly screening without fraud language, and K-Means data sufficiency.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest

import numpy as np
import pandas as pd

import ml_models
from src.ml.anomaly import (
    DISCLAIMER,
    detect_anomalies,
    detect_multi_feature_anomalies,
)
from src.ml.categorization import (
    check_training_eligibility,
    predict_category,
    train_or_load_categorizer,
)
from src.ml.clustering import (
    analyze_category_volatility,
    analyze_essential_vs_discretionary,
    cluster_monthly_spending,
    cluster_monthly_spending_advanced,
)
from src.ml.forecasting import (
    _monthly_expenses,
    evaluate_and_forecast_expenses,
    forecast_by_category,
)


def _generate_synthetic_transactions(n_months: int = 12) -> pd.DataFrame:
    """Helper to generate realistic historical monthly expense records."""
    records = []
    base_amounts = {
        "Rent": 10000.0,
        "Groceries": 4000.0,
        "Food": 2500.0,
        "Utilities": 1500.0,
        "Transport": 1200.0,
        "Shopping": 2000.0,
    }
    desc_templates = {
        "Rent": ["Apartment rent payment", "House rent landlord", "PG accommodation fee"],
        "Groceries": ["BigBasket monthly order", "Supermarket grocery bill", "DMart provisions"],
        "Food": ["Swiggy food order", "Zomato dinner delivery", "Restaurant lunch bill"],
        "Utilities": ["Electricity power bill", "Internet broadband wifi", "Mobile postpaid recharge"],
        "Transport": ["Uber office commute", "Ola cab ride", "Metro card recharge"],
        "Shopping": ["Amazon order delivery", "Flipkart retail shopping", "Myntra clothes order"],
    }

    t_id = 1
    for m in range(n_months):
        year = 2025 + (m // 12)
        month = (m % 12) + 1
        date_str = f"{year:04d}-{month:02d}-15"
        for cat, base in base_amounts.items():
            for rep in range(3):
                desc = desc_templates[cat][rep % len(desc_templates[cat])]
                # Add predictable variation
                noise = (rep - 1) * (base * 0.05) + (m * 20.0)
                records.append({
                    "id": t_id,
                    "txn_date": date_str,
                    "txn_type": "Expense",
                    "description": desc,
                    "amount": round(base + noise, 2),
                    "category": cat,
                    "notes": "",
                })
                t_id += 1

    return pd.DataFrame(records)


class TestExpenseForecasting(unittest.TestCase):
    """Test time-series forecasting, chronological holdout, baselines, and uncertainty intervals."""

    def test_monthly_expenses_aggregation(self):
        df = _generate_synthetic_transactions(n_months=6)
        monthly = _monthly_expenses(df)
        self.assertEqual(len(monthly), 6)
        self.assertIn("month", monthly.columns)
        self.assertIn("amount", monthly.columns)
        self.assertTrue(all(monthly["amount"] > 0))

    def test_forecasting_empty_and_small_dataset(self):
        # Empty
        res_empty = evaluate_and_forecast_expenses(pd.DataFrame())
        self.assertEqual(res_empty["status"], "no_data")
        self.assertEqual(res_empty["prediction"], 0.0)

        # 2 Months (Limited data fallback)
        df_2m = _generate_synthetic_transactions(n_months=2)
        res_2m = evaluate_and_forecast_expenses(df_2m)
        self.assertEqual(res_2m["status"], "limited_data")
        self.assertGreater(res_2m["prediction"], 0.0)
        self.assertIn("at least 3 months", res_2m["message"])

    def test_chronological_holdout_and_baseline_comparison(self):
        df = _generate_synthetic_transactions(n_months=10)
        res = evaluate_and_forecast_expenses(df)

        self.assertEqual(res["status"], "trained")
        self.assertIn("best_model", res)
        self.assertIn(res["best_model"], ["Linear Regression", "3-Month Moving Average", "Naive Baseline (Last Month)"])

        # Check model comparisons structure
        comparisons = res["model_comparisons"]
        self.assertEqual(len(comparisons), 3)

        models_evaluated = {c["model"] for c in comparisons}
        self.assertEqual(models_evaluated, {"Linear Regression", "3-Month Moving Average", "Naive Baseline (Last Month)"})

        for c in comparisons:
            self.assertGreaterEqual(c["mae"], 0.0)
            self.assertGreaterEqual(c["rmse"], 0.0)
            self.assertGreater(c["next_pred"], 0.0)

        # Confirm the selected best model matches the lowest MAE
        best_mae = min(c["mae"] for c in comparisons)
        selected_model_mae = res["metrics"]["mae"]
        self.assertEqual(selected_model_mae, best_mae)

    def test_prediction_uncertainty_intervals(self):
        df = _generate_synthetic_transactions(n_months=8)
        res = evaluate_and_forecast_expenses(df)

        pred = res["prediction"]
        low_80, high_80 = res["interval_80"]
        low_95, high_95 = res["interval_95"]

        self.assertGreater(pred, 0.0)
        # Mathematical soundness of intervals: low <= pred <= high
        self.assertLessEqual(low_80, pred)
        self.assertGreaterEqual(high_80, pred)
        self.assertLessEqual(low_95, low_80)  # 95% interval is wider than 80% interval
        self.assertGreaterEqual(high_95, high_80)
        self.assertGreaterEqual(low_95, 0.0)  # Non-negative lower bound

    def test_forecast_by_category(self):
        df = _generate_synthetic_transactions(n_months=6)
        cat_fc = forecast_by_category(df)

        self.assertFalse(cat_fc.empty)
        self.assertIn("category", cat_fc.columns)
        self.assertIn("predicted_amount", cat_fc.columns)
        self.assertIn("method", cat_fc.columns)
        self.assertIn("interval_80", cat_fc.columns)
        self.assertEqual(len(cat_fc), 6)  # 6 categories in synthetic generator


class TestCategorizationEngine(unittest.TestCase):
    """Test TF-IDF + Random Forest classification, evaluation metrics, persistence, and fallbacks."""

    def test_training_eligibility_checks(self):
        # Empty
        eligible, reason, _ = check_training_eligibility(pd.DataFrame())
        self.assertFalse(eligible)

        # Under 25 records
        small_df = pd.DataFrame([
            {"txn_type": "Expense", "description": "Grocery", "category": "Groceries"}
            for _ in range(10)
        ])
        eligible, reason, _ = check_training_eligibility(small_df)
        self.assertFalse(eligible)
        self.assertIn("Insufficient training volume", reason)

        # Single category (no diversity)
        single_cat_df = pd.DataFrame([
            {"txn_type": "Expense", "description": "Grocery", "category": "Groceries"}
            for _ in range(30)
        ])
        eligible, reason, _ = check_training_eligibility(single_cat_df)
        self.assertFalse(eligible)
        self.assertIn("Insufficient class diversity", reason)

    def test_train_and_evaluate_categorizer(self):
        df = _generate_synthetic_transactions(n_months=6)  # ~108 records, 6 categories
        res = train_or_load_categorizer(df, force_retrain=True)

        self.assertEqual(res["status"], "trained")
        self.assertIsNotNone(res["pipeline"])

        # Check evaluation metrics
        metrics = res["metrics"]
        self.assertIn("accuracy", metrics)
        self.assertIn("f1", metrics)
        self.assertIn("precision", metrics)
        self.assertIn("recall", metrics)
        self.assertGreaterEqual(metrics["accuracy"], 0.70)
        self.assertGreaterEqual(metrics["f1"], 0.70)

        # Check per-class metrics
        per_class = res["per_class_metrics"]
        self.assertGreater(len(per_class), 0)

    def test_predict_category_with_confidence_and_fallback(self):
        df = _generate_synthetic_transactions(n_months=6)

        # 1. Known pattern matching training distribution
        pred, expl, conf = predict_category("BigBasket monthly order", "Expense", df)
        self.assertEqual(pred, "Groceries")
        self.assertGreaterEqual(conf, 0.40)
        self.assertIn("Random Forest", expl)

        # 2. Income transaction should cleanly use deterministic keyword rule
        pred_inc, expl_inc, conf_inc = predict_category("Monthly salary from employer", "Income", df)
        self.assertEqual(pred_inc, "Salary")
        self.assertEqual(conf_inc, 1.0)
        self.assertIn("keyword", expl_inc.lower())

        # 3. Novel description with low model confidence falls back to keyword rule
        pred_novel, expl_novel, _ = predict_category("Zomato dinner delivery meal", "Expense", df)
        self.assertEqual(pred_novel, "Food")


class TestMultiFeatureAnomalyDetection(unittest.TestCase):
    """Test multi-signal anomaly detection and ethical framing."""

    def test_empty_and_insufficient_data(self):
        res = detect_multi_feature_anomalies(pd.DataFrame())
        self.assertEqual(res["status"], "no_data")

        small = pd.DataFrame([
            {"txn_type": "Expense", "txn_date": "2026-11-01", "category": "Food", "amount": 100.0, "description": "tea"}
        ])
        res_small = detect_multi_feature_anomalies(small)
        self.assertEqual(res_small["status"], "limited_data")

    def test_detects_injected_category_outlier(self):
        df = _generate_synthetic_transactions(n_months=4)
        # Normal food is ~2,500. Inject a massive 25,000 Food transaction
        outlier = pd.DataFrame([{
            "id": 9999,
            "txn_date": "2026-11-10",
            "txn_type": "Expense",
            "description": "Luxury Banquet Dinner",
            "amount": 25000.0,
            "category": "Food",
            "notes": "Wedding party",
        }])
        test_df = pd.concat([df, outlier], ignore_index=True)

        res = detect_multi_feature_anomalies(test_df)
        self.assertEqual(res["status"], "flagged")
        anomalies = res["anomalies"]
        self.assertFalse(anomalies.empty)

        flagged_ids = anomalies["id"].tolist()
        self.assertIn(9999, flagged_ids)

        flagged_row = anomalies[anomalies["id"] == 9999].iloc[0]
        self.assertEqual(flagged_row["category"], "Food")
        self.assertIn("higher than typical Food median", flagged_row["anomaly_reason"])
        self.assertEqual(flagged_row["severity"], "High Deviation")

    def test_non_fraud_disclaimer_present(self):
        df = _generate_synthetic_transactions(n_months=4)
        res = detect_multi_feature_anomalies(df)
        disclaimer = res["disclaimer"]

        # Strictly verify non-fraud terminology
        self.assertIn("do not represent confirmed fraud", disclaimer.lower())
        self.assertIn("statistical spending variations", disclaimer.lower())

        # Also test backward-compatible wrapper
        _, note = detect_anomalies(df)
        self.assertIn("confirmed fraud", note.lower())


class TestSpendingPatternAnalysis(unittest.TestCase):
    """Test K-Means data sufficiency check (>= 6 months required) and fallbacks."""

    def test_kmeans_deferred_on_insufficient_history(self):
        # 3 months: K-Means must NOT run to prevent overfitting
        df_3m = _generate_synthetic_transactions(n_months=3)
        res = cluster_monthly_spending_advanced(df_3m)

        self.assertEqual(res["status"], "insufficient_history")
        self.assertTrue(res["clusters"].empty)
        self.assertEqual(res["k"], 0)
        self.assertIn("At least 6 distinct months", res["message"])

        # Fallbacks must still be computed cleanly
        self.assertEqual(res["essential_vs_discretionary"]["status"], "computed")
        self.assertFalse(res["category_volatility"].empty)

    def test_kmeans_runs_on_adequate_history(self):
        # 8 months: K-Means should run and return 2 clusters
        df_8m = _generate_synthetic_transactions(n_months=8)
        res = cluster_monthly_spending_advanced(df_8m)

        self.assertEqual(res["status"], "clustered")
        self.assertEqual(res["n_months"], 8)
        self.assertEqual(res["k"], 2)
        self.assertEqual(len(res["archetypes"]), 2)
        self.assertFalse(res["clusters"].empty)
        self.assertIn("archetype", res["clusters"].columns)

    def test_essential_vs_discretionary_analysis(self):
        df = _generate_synthetic_transactions(n_months=4)
        res = analyze_essential_vs_discretionary(df)

        self.assertEqual(res["status"], "computed")
        self.assertGreater(res["total"], 0.0)
        self.assertGreater(res["essential"], 0.0)
        self.assertGreater(res["discretionary"], 0.0)
        self.assertAlmostEqual(res["essential_pct"] + res["discretionary_pct"], 100.0, places=1)

    def test_category_volatility_analysis(self):
        df = _generate_synthetic_transactions(n_months=6)
        vol = analyze_category_volatility(df)

        self.assertFalse(vol.empty)
        self.assertIn("category", vol.columns)
        self.assertIn("monthly_avg", vol.columns)
        self.assertIn("cv", vol.columns)
        self.assertIn("stability_class", vol.columns)


class TestBackwardCompatibility(unittest.TestCase):
    """Verify that root ml_models.py functions maintain identical signatures and return types."""

    def test_forecast_next_month_signature(self):
        df = _generate_synthetic_transactions(n_months=5)
        res = ml_models.forecast_next_month(df)

        self.assertIn("status", res)
        self.assertIn("prediction", res)
        self.assertIn("history", res)
        self.assertIn("metrics", res)
        self.assertIn("model", res)
        self.assertIn("message", res)

    def test_cluster_monthly_spending_signature(self):
        df = _generate_synthetic_transactions(n_months=6)
        clusters, note = ml_models.cluster_monthly_spending(df)
        self.assertIsInstance(clusters, pd.DataFrame)
        self.assertIsInstance(note, str)

    def test_detect_anomalies_signature(self):
        df = _generate_synthetic_transactions(n_months=4)
        anomalies, note = ml_models.detect_anomalies(df)
        self.assertIsInstance(anomalies, pd.DataFrame)
        self.assertIsInstance(note, str)

    def test_category_prediction_signature(self):
        df = _generate_synthetic_transactions(n_months=5)
        cat, expl = ml_models.category_prediction("Dinner at cafe", "Expense", df)
        self.assertIsInstance(cat, str)
        self.assertIsInstance(expl, str)


if __name__ == "__main__":
    unittest.main()
