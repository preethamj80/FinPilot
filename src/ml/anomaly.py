"""Multi-feature anomaly screening for unusual financial transactions.

Considers amount magnitude, category z-scores, merchant history, and transaction velocity.
Explicitly framed as statistical audit flags, never as proven fraud.
"""
from __future__ import annotations

import re
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

DISCLAIMER = (
    "Anomaly screening identifies statistical spending variations and outliers to assist your budget audit. "
    "Flags indicate deviation from typical historical patterns and do not represent confirmed fraud or unauthorized charges."
)


def _clean_merchant_name(desc: str) -> str:
    """Extract core merchant name from transaction description."""
    cleaned = re.sub(r"\(.*?\)", "", str(desc)).strip()
    words = cleaned.split()
    return " ".join(words[:3]) if words else "Unknown"


def detect_multi_feature_anomalies(transactions: pd.DataFrame) -> dict:
    """Detect unusual transactions using category robust z-scores, merchant-level deviations,

    daily frequency spikes, and multi-feature Isolation Forest screening.
    """
    if transactions is None or transactions.empty:
        return {
            "status": "no_data",
            "message": "No transactions available for anomaly screening.",
            "anomalies": pd.DataFrame(),
            "disclaimer": DISCLAIMER,
            "total_screened": 0,
            "flagged_count": 0,
        }

    df = transactions[transactions["txn_type"] == "Expense"].copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount", "txn_date", "category"])
    df = df[df["amount"] > 0]

    if len(df) < 10:
        return {
            "status": "limited_data",
            "message": f"At least 10 expense transactions are needed for anomaly screening (currently {len(df)}).",
            "anomalies": pd.DataFrame(),
            "disclaimer": DISCLAIMER,
            "total_screened": len(df),
            "flagged_count": 0,
        }

    # Pre-calculate category statistics (Robust Median and MAD)
    cat_stats: dict[str, dict[str, float]] = {}
    for cat, group in df.groupby("category"):
        amounts = group["amount"].values
        med = float(np.median(amounts))
        mad = float(np.median(np.abs(amounts - med)))
        iqr_std = max(1.0, 1.4826 * mad)
        cat_stats[cat] = {
            "median": med,
            "mad": mad,
            "scale": iqr_std,
            "count": len(amounts),
        }

    # Pre-calculate merchant statistics
    df["merchant"] = df["description"].apply(_clean_merchant_name)
    merchant_stats: dict[str, dict[str, float]] = {}
    for merch, group in df.groupby("merchant"):
        if len(group) >= 3:
            merchant_stats[merch] = {
                "median": float(np.median(group["amount"].values)),
                "count": len(group),
            }

    # Pre-calculate daily frequency per category
    day_freq = df.groupby(["txn_date", "category"])["amount"].agg(["count", "sum"]).reset_index()
    mean_freq = float(day_freq["count"].mean())
    std_freq = float(day_freq["count"].std()) if len(day_freq) > 1 else 0.0
    freq_threshold = max(4, int(mean_freq + 2.5 * std_freq))

    day_freq_map = {
        (row["txn_date"], row["category"]): (int(row["count"]), float(row["sum"]))
        for _, row in day_freq.iterrows()
    }

    # Compute features for each transaction
    flagged_records: list[dict] = []
    seen_ids = set()

    # Feature matrix for Isolation Forest
    feature_rows = []
    index_map = []

    for idx, row in df.iterrows():
        amt = float(row["amount"])
        cat = str(row["category"])
        merch = str(row["merchant"])
        dt = str(row["txn_date"])
        t_id = row.get("id", idx)

        # 1. Category-level robust z-score and ratio
        c_stat = cat_stats.get(cat, {"median": amt, "scale": 1.0, "count": 1})
        c_median = c_stat["median"]
        c_scale = c_stat["scale"]
        c_z = (amt - c_median) / c_scale
        c_ratio = amt / max(1.0, c_median)

        # 2. Daily velocity
        freq_count, day_total = day_freq_map.get((dt, cat), (1, amt))

        # 3. Merchant ratio
        m_stat = merchant_stats.get(merch)
        m_ratio = (amt / m_stat["median"]) if m_stat else 1.0

        feature_rows.append([
            np.log1p(amt),
            max(-3.0, min(10.0, c_z)),
            min(10.0, c_ratio),
            freq_count,
        ])
        index_map.append(idx)

        # Rule Signal A: High Category Spend Deviation (z-score >= 2.3 and ratio >= 1.5)
        if c_stat["count"] >= 5 and c_z >= 2.3 and c_ratio >= 1.5:
            severity = "High Deviation" if (c_z >= 3.0 or c_ratio >= 2.5) else "Moderate Deviation"
            reason = (
                f"Amount ₹{amt:,.0f} is {c_ratio:.1f}× higher than typical {cat} median "
                f"(₹{c_median:,.0f}, z-score: +{c_z:.1f})"
            )
            flagged_records.append({
                **row.to_dict(),
                "anomaly_reason": reason,
                "severity": severity,
                "signal_type": "Category Outlier",
                "z_score": round(c_z, 2),
                "ratio_to_median": round(c_ratio, 2),
            })
            seen_ids.add(t_id)

        # Rule Signal B: Merchant-Level Spike
        elif m_stat and m_stat["count"] >= 3 and m_ratio >= 2.5 and amt >= 500:
            if t_id not in seen_ids:
                reason = (
                    f"Unusual spend at '{merch}': ₹{amt:,.0f} is {m_ratio:.1f}× higher than "
                    f"your typical median of ₹{m_stat['median']:,.0f} at this vendor"
                )
                flagged_records.append({
                    **row.to_dict(),
                    "anomaly_reason": reason,
                    "severity": "Merchant Outlier",
                    "signal_type": "Merchant Outlier",
                    "z_score": round(c_z, 2),
                    "ratio_to_median": round(m_ratio, 2),
                })
                seen_ids.add(t_id)

        # Rule Signal C: Daily Frequency Burst (significantly exceeds dataset typical velocity)
        elif freq_count >= freq_threshold and amt > c_median:
            if t_id not in seen_ids:
                reason = (
                    f"Spending velocity spike: {freq_count} transactions recorded in {cat} on {dt} "
                    f"(Day total: ₹{day_total:,.0f})"
                )
                flagged_records.append({
                    **row.to_dict(),
                    "anomaly_reason": reason,
                    "severity": "Frequency Spike",
                    "signal_type": "Velocity Spike",
                    "z_score": round(c_z, 2),
                    "ratio_to_median": round(c_ratio, 2),
                })
                seen_ids.add(t_id)

    # Optional Multi-Feature Isolation Forest to catch subtle joint outliers
    if len(df) >= 20 and len(feature_rows) >= 20:
        try:
            X_features = np.array(feature_rows)
            iso = IsolationForest(contamination=0.03, random_state=42)
            iso_preds = iso.fit_predict(X_features)
            for i, pred in enumerate(iso_preds):
                if pred == -1:
                    orig_idx = index_map[i]
                    orig_row = df.loc[orig_idx]
                    t_id = orig_row.get("id", orig_idx)
                    if t_id not in seen_ids and orig_row["amount"] > np.median(df["amount"]):
                        c_z = feature_rows[i][1]
                        c_ratio = feature_rows[i][2]
                        flagged_records.append({
                            **orig_row.to_dict(),
                            "anomaly_reason": f"Multivariate outlier: Unusual joint amount-frequency profile (z-score: +{c_z:.1f})",
                            "severity": "Multivariate Pattern",
                            "signal_type": "Isolation Forest",
                            "z_score": round(float(c_z), 2),
                            "ratio_to_median": round(float(c_ratio), 2),
                        })
                        seen_ids.add(t_id)
        except Exception:
            pass

    if not flagged_records:
        return {
            "status": "clean",
            "message": "No unusual transactions flagged across category, merchant, frequency, and multivariate screening.",
            "anomalies": pd.DataFrame(),
            "disclaimer": DISCLAIMER,
            "total_screened": len(df),
            "flagged_count": 0,
        }

    res_df = pd.DataFrame(flagged_records)
    res_df = res_df.sort_values(by=["z_score", "amount"], ascending=[False, False]).reset_index(drop=True)

    return {
        "status": "flagged",
        "message": f"Identified {len(res_df)} transaction(s) exhibiting notable statistical deviations for review.",
        "anomalies": res_df,
        "disclaimer": DISCLAIMER,
        "total_screened": len(df),
        "flagged_count": len(res_df),
    }


def detect_anomalies(transactions: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Backward-compatible wrapper returning (anomalies_df, note)."""
    result = detect_multi_feature_anomalies(transactions)
    if result["anomalies"].empty:
        return pd.DataFrame(), result["message"] + " " + result["disclaimer"]
    note = f"{result['message']} {result['disclaimer']}"
    return result["anomalies"], note
