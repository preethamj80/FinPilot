"""Expense forecasting with chronological validation and uncertainty estimation."""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error


def _monthly_expenses(transactions: pd.DataFrame) -> pd.DataFrame:
    """Aggregate expense transactions by calendar month."""
    if transactions is None or transactions.empty:
        return pd.DataFrame(columns=["month", "amount"])
    df = transactions[transactions["txn_type"] == "Expense"].copy()
    if df.empty:
        return pd.DataFrame(columns=["month", "amount"])
    df["month"] = pd.to_datetime(df["txn_date"], errors="coerce").dt.to_period("M").astype(str)
    df = df.dropna(subset=["month"])
    grouped = df.groupby("month", as_index=False)["amount"].sum()
    return grouped.sort_values("month").reset_index(drop=True)


def evaluate_and_forecast_expenses(transactions: pd.DataFrame) -> dict:
    """Evaluate Linear Regression, 3-Month Moving Average, and Naive Baseline using

    chronological holdout validation without data leakage. Computes MAE, RMSE,
    and returns next-month point prediction with 80% and 95% uncertainty intervals.
    """
    monthly = _monthly_expenses(transactions)
    if monthly.empty:
        return {
            "status": "no_data",
            "prediction": 0.0,
            "best_model": "None",
            "model": "None",
            "message": "Add or import expense transactions to generate an expense forecast.",
            "history": monthly,
            "metrics": None,
            "model_comparisons": [],
            "interval_80": (0.0, 0.0),
            "interval_95": (0.0, 0.0),
            "std_error": 0.0,
            "uncertainty_note": "No historical transactions available.",
        }

    n_months = len(monthly)
    y = monthly["amount"].astype(float).values
    x = np.arange(n_months).reshape(-1, 1)

    # If fewer than 3 months, statistical forecasting is unreliable
    if n_months < 3:
        recent_avg = float(monthly["amount"].mean())
        return {
            "status": "limited_data",
            "prediction": round(recent_avg, 2),
            "best_model": "Recent Historical Average",
            "model": "Recent Historical Average",
            "message": f"Only {n_months} month(s) of expense history available. Using simple historical average until at least 3 months are recorded.",
            "history": monthly,
            "metrics": None,
            "model_comparisons": [],
            "interval_80": (round(max(0.0, recent_avg * 0.85), 2), round(recent_avg * 1.15, 2)),
            "interval_95": (round(max(0.0, recent_avg * 0.70), 2), round(recent_avg * 1.30, 2)),
            "std_error": round(recent_avg * 0.15, 2),
            "uncertainty_note": "Wide heuristic uncertainty due to small sample size (<3 months).",
        }

    # Chronological validation
    # Hold out the most recent months (up to 3, leaving at least 3 for training)
    holdout_size = 1 if n_months < 5 else (2 if n_months < 7 else 3)
    train_size = n_months - holdout_size

    y_train = y[:train_size]
    x_train = x[:train_size]
    y_test = y[train_size:]
    x_test = x[train_size:]

    # 1. Linear Regression (trained strictly on chronological training window)
    lr_train = LinearRegression().fit(x_train, y_train)
    lr_holdout_preds = np.maximum(0.0, lr_train.predict(x_test))
    lr_mae = float(mean_absolute_error(y_test, lr_holdout_preds))
    lr_rmse = float(np.sqrt(mean_squared_error(y_test, lr_holdout_preds)))

    # 2. 3-Month Moving Average (expanding rolling step-by-step on holdout)
    ma_holdout_preds = []
    # For each holdout point, use the preceding up to 3 actual months
    for i in range(train_size, n_months):
        window = y[max(0, i - 3):i]
        ma_holdout_preds.append(float(np.mean(window)))
    ma_holdout_preds = np.array(ma_holdout_preds)
    ma_mae = float(mean_absolute_error(y_test, ma_holdout_preds))
    ma_rmse = float(np.sqrt(mean_squared_error(y_test, ma_holdout_preds)))

    # 3. Naive Baseline (Last Month Actual: y_t = y_{t-1})
    naive_holdout_preds = []
    for i in range(train_size, n_months):
        naive_holdout_preds.append(float(y[i - 1]))
    naive_holdout_preds = np.array(naive_holdout_preds)
    naive_mae = float(mean_absolute_error(y_test, naive_holdout_preds))
    naive_rmse = float(np.sqrt(mean_squared_error(y_test, naive_holdout_preds)))

    # Compute final full-dataset forecast for each candidate model
    # Full Linear Regression
    lr_full = LinearRegression().fit(x, y)
    lr_next_pred = max(0.0, float(lr_full.predict([[n_months]])[0]))

    # Full 3-Month Moving Average
    ma_next_pred = max(0.0, float(np.mean(y[-min(3, n_months):])))

    # Full Naive Baseline
    naive_next_pred = max(0.0, float(y[-1]))

    comparisons = [
        {
            "model": "Linear Regression",
            "mae": round(lr_mae, 2),
            "rmse": round(lr_rmse, 2),
            "next_pred": round(lr_next_pred, 2),
            "description": "Fits overall linear spending trajectory over chronological month indices.",
        },
        {
            "model": "3-Month Moving Average",
            "mae": round(ma_mae, 2),
            "rmse": round(ma_rmse, 2),
            "next_pred": round(ma_next_pred, 2),
            "description": "Smooths short-term fluctuations by averaging the 3 most recent months.",
        },
        {
            "model": "Naive Baseline (Last Month)",
            "mae": round(naive_mae, 2),
            "rmse": round(naive_rmse, 2),
            "next_pred": round(naive_next_pred, 2),
            "description": "Simple reference baseline assuming next month matches the current month exactly.",
        },
    ]

    # Select best model based on holdout MAE
    comparisons.sort(key=lambda m: m["mae"])
    for idx, comp in enumerate(comparisons):
        comp["is_best"] = (idx == 0)

    best_candidate = comparisons[0]
    best_model_name = best_candidate["model"]
    point_prediction = best_candidate["next_pred"]

    # Compute prediction uncertainty intervals
    # Residual analysis on the full history
    if best_model_name == "Linear Regression":
        fitted = np.maximum(0.0, lr_full.predict(x))
        residuals = y - fitted
        dof = max(1, n_months - 2)
        s_e = float(np.sqrt(np.sum(residuals ** 2) / dof))
        # Standard error of forecast at x* = n_months
        x_mean = float(np.mean(x))
        x_ss = float(np.sum((x - x_mean) ** 2))
        se_factor = math.sqrt(1.0 + (1.0 / n_months) + (((n_months - x_mean) ** 2) / max(1e-5, x_ss)))
        se_forecast = s_e * se_factor
    else:
        # For moving average / naive baseline
        residuals = []
        for i in range(1, n_months):
            if best_model_name == "3-Month Moving Average":
                win = y[max(0, i - 3):i]
                pred_i = float(np.mean(win))
            else:
                pred_i = float(y[i - 1])
            residuals.append(y[i] - pred_i)
        residuals = np.array(residuals)
        dof = max(1, len(residuals) - 1)
        s_e = float(np.sqrt(np.sum(residuals ** 2) / dof)) if len(residuals) > 0 else 0.0
        se_forecast = s_e * math.sqrt(1.0 + (1.0 / min(3, n_months)))

    # 80% interval (z = 1.282) and 95% interval (z = 1.960)
    margin_80 = 1.282 * se_forecast
    margin_95 = 1.960 * se_forecast

    lower_80 = round(max(0.0, point_prediction - margin_80), 2)
    upper_80 = round(point_prediction + margin_80, 2)
    lower_95 = round(max(0.0, point_prediction - margin_95), 2)
    upper_95 = round(point_prediction + margin_95, 2)

    # Attach fitted line to history frame
    history_df = monthly.copy()
    history_df["fitted"] = lr_full.predict(x)

    uncertainty_note = (
        f"Based on {holdout_size}-month chronological holdout evaluation, {best_model_name} achieved the lowest error "
        f"(MAE: ₹{best_candidate['mae']:,.2f}, RMSE: ₹{best_candidate['rmse']:,.2f}). "
        f"The 95% statistical prediction interval estimates next month's total spend between ₹{lower_95:,.2f} and ₹{upper_95:,.2f} "
        f"(accounting for residual variance around future observations)."
    )

    return {
        "status": "trained",
        "prediction": round(point_prediction, 2),
        "best_model": best_model_name,
        "model": best_model_name,
        "metrics": {"mae": best_candidate["mae"], "rmse": best_candidate["rmse"]},
        "model_comparisons": comparisons,
        "history": history_df,
        "interval_80": (lower_80, upper_80),
        "interval_95": (lower_95, upper_95),
        "std_error": round(se_forecast, 2),
        "holdout_size": holdout_size,
        "message": f"Evaluated against chronological holdout ({holdout_size} months). {best_model_name} selected as best predictor.",
        "uncertainty_note": uncertainty_note,
    }


def forecast_by_category(transactions: pd.DataFrame) -> pd.DataFrame:
    """Generate category-level next-month expense forecasts with method indications

    and uncertainty ranges.
    """
    if transactions is None or transactions.empty:
        return pd.DataFrame(columns=["category", "predicted_amount", "method", "interval_80", "historical_avg"])

    df = transactions[transactions["txn_type"] == "Expense"].copy()
    if df.empty:
        return pd.DataFrame(columns=["category", "predicted_amount", "method", "interval_80", "historical_avg"])

    df["month"] = pd.to_datetime(df["txn_date"], errors="coerce").dt.to_period("M").astype(str)
    df = df.dropna(subset=["month"])
    grouped = df.groupby(["month", "category"], as_index=False)["amount"].sum()

    out = []
    for category, part in grouped.groupby("category"):
        part = part.sort_values("month").reset_index(drop=True)
        n = len(part)
        y = part["amount"].values
        hist_avg = float(np.mean(y))

        if n >= 4:
            # Compare Linear Regression vs 3-month Moving Average on last month holdout
            x_all = np.arange(n).reshape(-1, 1)
            lr_model = LinearRegression().fit(x_all[:-1], y[:-1])
            lr_test_err = abs(y[-1] - lr_model.predict([[n - 1]])[0])

            ma_test_pred = float(np.mean(y[-4:-1]))
            ma_test_err = abs(y[-1] - ma_test_pred)

            if lr_test_err < ma_test_err:
                full_lr = LinearRegression().fit(x_all, y)
                pred = max(0.0, float(full_lr.predict([[n]])[0]))
                method = "Linear Regression"
                res = y - full_lr.predict(x_all)
                se = float(np.std(res))
            else:
                pred = max(0.0, float(np.mean(y[-3:])))
                method = "3-Month Moving Avg"
                res = [y[i] - np.mean(y[max(0, i - 3):i]) for i in range(1, n)]
                se = float(np.std(res)) if res else pred * 0.15

            interval_80 = (round(max(0.0, pred - 1.282 * se), 2), round(pred + 1.282 * se, 2))
        elif n >= 2:
            pred = max(0.0, float(np.mean(y[-min(3, n):])))
            method = "Recent Average (Limited History)"
            se = float(np.std(y)) if len(y) > 1 else pred * 0.20
            interval_80 = (round(max(0.0, pred - 1.282 * se), 2), round(pred + 1.282 * se, 2))
        else:
            pred = float(y[0])
            method = "Single Month (Insufficient History)"
            interval_80 = (round(max(0.0, pred * 0.8), 2), round(pred * 1.2, 2))

        out.append({
            "category": category,
            "predicted_amount": round(pred, 2),
            "historical_avg": round(hist_avg, 2),
            "method": method,
            "interval_80": f"₹{interval_80[0]:,.0f} – ₹{interval_80[1]:,.0f}",
            "raw_interval": interval_80,
        })

    result_df = pd.DataFrame(out)
    if not result_df.empty:
        result_df = result_df.sort_values("predicted_amount", ascending=False).reset_index(drop=True)
    return result_df
