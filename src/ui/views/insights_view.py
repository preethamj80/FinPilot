"""AI Insights and Machine Learning analytics view for FinPilot.

Features chronologically validated forecasting, TF-IDF + Random Forest categorization,
multi-feature statistical anomaly audit, and behavioral K-Means clustering with fallbacks.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.ml.anomaly import detect_multi_feature_anomalies
from src.ml.categorization import (
    predict_category,
    train_or_load_categorizer,
)
from src.ml.clustering import (
    analyze_category_volatility,
    analyze_essential_vs_discretionary,
    cluster_monthly_spending_advanced,
)
from src.ml.forecasting import (
    evaluate_and_forecast_expenses,
    forecast_by_category,
)
from src.ui.components import empty_state, format_currency, page_header, plotly_fintech_theme
from src.ui.styles import PALETTE


def render_insights_view(tx: pd.DataFrame) -> None:
    """Render the AI Insights and Machine Learning analytics page."""
    page_header(
        "AI Insights & Machine Learning",
        "Chronologically validated time-series forecasting, TF-IDF + Random Forest categorization, multi-feature anomaly audit, and behavioral K-Means clustering.",
        badge="SCIKIT-LEARN & STATS",
    )

    if tx is None or tx.empty:
        empty_state(
            "No Transaction Data Available",
            "Add transactions or load synthetic demo data from Settings & Data to train local machine learning models.",
            icon="🧠",
        )
        return

    tab_forecast, tab_cat, tab_anomaly, tab_patterns = st.tabs([
        "🔮 Expense Forecasting & Baselines",
        "🧠 Categorization Engine & Evaluation",
        "🚩 Multi-Feature Anomaly Audit",
        "🧩 Spending Pattern Archetypes",
    ])

    # =========================================================================
    # TAB 1: EXPENSE FORECASTING & BASELINE COMPARISON
    # =========================================================================
    with tab_forecast:
        st.markdown("### 🔮 Next-Month Expense Forecasting")
        st.markdown(
            "FinPilot evaluates candidate models on a **chronological holdout window** with zero data leakage. "
            "The model with the lowest holdout Mean Absolute Error (MAE) is selected as the primary forecaster."
        )

        fc = evaluate_and_forecast_expenses(tx)

        if fc["status"] == "no_data":
            st.info(fc["message"])
        elif fc["status"] == "limited_data":
            st.warning(fc["message"])
            st.metric("Recent Monthly Average", format_currency(fc["prediction"]))
        else:
            # Metrics Row
            m_col1, m_col2, m_col3, m_col4 = st.columns([1.2, 1.1, 1.1, 1.4])
            m_col1.metric("Projected Total Spend", format_currency(fc["prediction"]), delta="Next Month", delta_color="off")
            m_col2.metric("80% Expected Range", f"₹{fc['interval_80'][0]:,.0f} – ₹{fc['interval_80'][1]:,.0f}", help="80% prediction interval based on historical residual variance")
            m_col3.metric("95% Expected Range", f"₹{fc['interval_95'][0]:,.0f} – ₹{fc['interval_95'][1]:,.0f}", help="95% prediction interval (standard error: ₹" + f"{fc['std_error']:,.2f})")
            m_col4.metric("Selected Best Model", fc["best_model"], delta=f"Holdout MAE: ₹{fc['metrics']['mae']:,.0f}", delta_color="normal")

            st.caption(f"ℹ️ **Uncertainty Analysis:** {fc['uncertainty_note']}")

            # Model Evaluation & Baseline Comparison Card
            st.markdown("#### 📊 Chronological Model Evaluation vs. Baselines")
            comp_rows = []
            for m in fc.get("model_comparisons", []):
                comp_rows.append({
                    "Model / Baseline": m["model"],
                    "Holdout MAE (₹)": m["mae"],
                    "Holdout RMSE (₹)": m["rmse"],
                    "Next Month Forecast (₹)": m["next_pred"],
                    "Evaluation Status": "⭐ Selected Best Model" if m.get("is_best") else "Baseline Candidate",
                    "Methodology": m["description"],
                })

            st.dataframe(
                pd.DataFrame(comp_rows),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Holdout MAE (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Holdout RMSE (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Next Month Forecast (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                },
            )

            # Interactive Plotly Time Series Chart
            history = fc.get("history", pd.DataFrame()).copy()
            if not history.empty:
                fig = go.Figure()

                # Historical Actual Spend
                fig.add_trace(go.Scatter(
                    x=history["month"],
                    y=history["amount"],
                    mode="lines+markers",
                    name="Actual Spend",
                    line=dict(color=PALETTE["navy_900"], width=2.5),
                    marker=dict(size=7),
                ))

                # Fitted Linear Trend
                if "fitted" in history.columns:
                    fig.add_trace(go.Scatter(
                        x=history["month"],
                        y=history["fitted"],
                        mode="lines",
                        name="Linear Trend Fit",
                        line=dict(color="#94A3B8", width=1.8, dash="dot"),
                    ))

                # Next-Month Point Forecast
                next_label = "Next Month"
                fig.add_trace(go.Scatter(
                    x=[next_label],
                    y=[fc["prediction"]],
                    mode="markers+text",
                    name=f"Forecast ({fc['best_model']})",
                    text=[format_currency(fc["prediction"])],
                    textposition="top center",
                    marker=dict(size=13, symbol="diamond", color=PALETTE["teal_primary"]),
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=[fc["interval_95"][1] - fc["prediction"]],
                        arrayminus=[fc["prediction"] - fc["interval_95"][0]],
                        color=PALETTE["teal_primary"],
                        thickness=2,
                        width=8,
                    ),
                ))

                fig.update_layout(
                    title="Historical Monthly Spend, Model Fit & Next-Month Prediction with 95% Error Band",
                    xaxis_title="Month",
                    yaxis_title="Total Spend (₹)",
                )
                st.plotly_chart(plotly_fintech_theme(fig), use_container_width=True)

            # Category-wise forecasts
            st.markdown("#### 🏷️ Category-Level Next-Month Projections")
            cat_fc = forecast_by_category(tx)
            if not cat_fc.empty:
                st.dataframe(
                    cat_fc[["category", "predicted_amount", "historical_avg", "interval_80", "method"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "category": "Category",
                        "predicted_amount": st.column_config.NumberColumn("Estimated Spend", format="₹%.2f"),
                        "historical_avg": st.column_config.NumberColumn("Historical Monthly Avg", format="₹%.2f"),
                        "interval_80": "80% Expected Range",
                        "method": "Forecasting Methodology",
                    },
                )

    # =========================================================================
    # TAB 2: TRANSACTION CATEGORIZATION ENGINE & EVALUATION
    # =========================================================================
    with tab_cat:
        st.markdown("### 🧠 Transaction Categorization Engine")
        st.markdown(
            "FinPilot uses a hybrid classification pipeline: a **TF-IDF (1-2 gram) + Random Forest Classifier** "
            "trained on user-labelled transactions, with a fast, deterministic **keyword fallback** for unlabelled or low-confidence inputs."
        )

        cat_info = train_or_load_categorizer(tx)

        if cat_info["status"] == "insufficient_data":
            st.info(f"ℹ️ {cat_info['message']}")
            st.caption("When your dataset grows to at least 25 labelled records across 2 or more categories, Random Forest will automatically train and persist.")
        else:
            # Metrics summary
            metrics = cat_info.get("metrics", {})
            st.success(f"✅ **Random Forest Pipeline Active** — {cat_info['record_count']} labelled records trained and persisted to disk (`models/category_model.joblib`).")

            c_col1, c_col2, c_col3, c_col4, c_col5 = st.columns(5)
            c_col1.metric("Holdout Accuracy", f"{metrics.get('accuracy', 0.0):.1%}")
            c_col2.metric("Weighted Precision", f"{metrics.get('precision', 0.0):.1%}")
            c_col3.metric("Weighted Recall", f"{metrics.get('recall', 0.0):.1%}")
            c_col4.metric("Weighted F1 Score", f"{metrics.get('f1', 0.0):.2f}")
            c_col5.metric("Evaluation Method", metrics.get("eval_method", "Holdout")[:16] + "...")

            # Diagnostics Expander
            with st.expander("🔍 Model Evaluation Diagnostics (Per-Class Metrics & Confusion Analysis)"):
                per_class = cat_info.get("per_class_metrics", [])
                if per_class:
                    st.markdown("**Per-Category Classification Performance**")
                    st.dataframe(pd.DataFrame(per_class), use_container_width=True, hide_index=True)

                top_confusions = cat_info.get("top_confusions", [])
                if top_confusions:
                    st.markdown("**Common Confusion Pairs (Actual vs. Predicted)**")
                    st.dataframe(pd.DataFrame(top_confusions), use_container_width=True, hide_index=True)
                else:
                    st.caption("No misclassifications detected on the evaluation holdout.")

                dist = cat_info.get("class_distribution", {})
                if dist:
                    st.markdown("**Training Class Distribution**")
                    dist_rows = [{"Category": k, "Sample Count": v["count"], "Share (%)": f"{v['percentage']}%"} for k, v in dist.items()]
                    st.dataframe(pd.DataFrame(dist_rows), use_container_width=True, hide_index=True)

            # Interactive Real-Time Prediction Sandbox
            st.markdown("#### 🧪 Test Categorization in Real Time")
            st.caption("Type any transaction description to inspect model prediction, confidence score, and decision source.")

            test_col1, test_col2 = st.columns([3, 1])
            test_input = test_col1.text_input("Enter transaction description:", value="Swiggy dinner delivery", placeholder="e.g. Swiggy food delivery, Uber cab, Netflix monthly")
            test_type = test_col2.selectbox("Type:", ["Expense", "Income"])

            if test_input:
                pred_cat, explanation, conf = predict_category(test_input, test_type, tx)
                res_box = st.container()
                with res_box:
                    st.markdown(
                        f"""
                        <div class="fintech-card" style="margin-top: 0.5rem; padding: 1.25rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <div>
                                    <span style="font-size: 0.85rem; color: {PALETTE['text_secondary']};">Predicted Category:</span>
                                    <div style="font-size: 1.35rem; font-weight: 700; color: {PALETTE['teal_primary']};">🏷️ {pred_cat}</div>
                                </div>
                                <div style="text-align: right;">
                                    <span style="font-size: 0.85rem; color: {PALETTE['text_secondary']};">Confidence:</span>
                                    <div style="font-size: 1.25rem; font-weight: 700; color: {PALETTE['text_primary']};">{conf:.0%}</div>
                                </div>
                            </div>
                            <div style="font-size: 0.88rem; color: {PALETTE['text_secondary']};">
                                <strong>Decision Source:</strong> {explanation}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # =========================================================================
    # TAB 3: MULTI-FEATURE ANOMALY AUDIT
    # =========================================================================
    with tab_anomaly:
        st.markdown("### 🚩 Multi-Feature Anomaly Audit")

        # Ethical Framing Notice
        st.markdown(
            f"""
            <div class="fintech-card" style="background: #F8FAFC; border-left: 4px solid {PALETTE['teal_primary']}; padding: 1rem 1.25rem; margin-bottom: 1.25rem;">
                <div style="font-weight: 700; color: {PALETTE['text_primary']}; margin-bottom: 0.25rem;">
                    🛡️ Statistical Audit Notice
                </div>
                <div style="font-size: 0.9rem; color: {PALETTE['text_secondary']}; line-height: 1.45;">
                    This screening engine identifies transactions exhibiting statistical spending variations (unusually high amounts, vendor spikes, or daily velocity bursts) to assist your personal budget review. 
                    <strong>Flagged items represent statistical outliers, not confirmed fraud or unauthorized charges.</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        anomaly_data = detect_multi_feature_anomalies(tx)
        anomalies_df = anomaly_data.get("anomalies", pd.DataFrame())

        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Screened Transactions", anomaly_data.get("total_screened", 0))
        col_s2.metric("Flagged Outliers", anomaly_data.get("flagged_count", 0))
        col_s3.metric("Screening Signals", "4 Dimensions", help="Category Robust Z-Score, Merchant Median Ratio, Daily Frequency Velocity, and Multivariate Isolation Forest")

        if anomalies_df.empty:
            st.success("✅ No unusual outlier transactions flagged across category, merchant, frequency, or multivariate screening.")
        else:
            st.markdown(f"**Identified {len(anomalies_df)} transaction(s) exhibiting notable statistical deviations:**")

            display_cols = ["txn_date", "description", "category", "amount", "severity", "signal_type", "anomaly_reason"]
            avail_cols = [c for c in display_cols if c in anomalies_df.columns]

            st.dataframe(
                anomalies_df[avail_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "txn_date": "Date",
                    "description": "Description",
                    "category": "Category",
                    "amount": st.column_config.NumberColumn("Amount", format="₹%.2f"),
                    "severity": "Severity Level",
                    "signal_type": "Signal Dimension",
                    "anomaly_reason": "Audit Explanation",
                },
            )

    # =========================================================================
    # TAB 4: SPENDING PATTERN ARCHETYPES & VOLATILITY
    # =========================================================================
    with tab_patterns:
        st.markdown("### 🧩 Spending Pattern Archetypes & Volatility Analysis")

        pattern_res = cluster_monthly_spending_advanced(tx)

        if pattern_res["status"] == "clustered":
            st.success(f"✅ **K-Means Clustering Active:** {pattern_res['message']}")

            # Archetype summary cards
            archetypes = pattern_res.get("archetypes", [])
            if archetypes:
                cols = st.columns(len(archetypes))
                for idx, arch in enumerate(archetypes):
                    with cols[idx]:
                        st.markdown(
                            f"""
                            <div class="fintech-card" style="padding: 1.25rem; height: 100%;">
                                <div style="font-size: 0.85rem; font-weight: 700; color: {PALETTE['teal_primary']}; margin-bottom: 0.25rem;">
                                    ARCHETYPE {arch['cluster_id'] + 1}
                                </div>
                                <div style="font-size: 1.15rem; font-weight: 700; color: {PALETTE['text_primary']}; margin-bottom: 0.5rem;">
                                    {arch['archetype']}
                                </div>
                                <div style="font-size: 1.35rem; font-weight: 800; color: {PALETTE['navy_900']}; margin-bottom: 0.35rem;">
                                    {format_currency(arch['average_total'])}
                                </div>
                                <div style="font-size: 0.85rem; color: {PALETTE['text_secondary']}; margin-bottom: 0.5rem;">
                                    Discretionary Share: <strong>{arch['discretionary_share']}%</strong> ({arch['month_count']} months)
                                </div>
                                <div style="font-size: 0.85rem; color: {PALETTE['text_secondary']}; border-top: 1px solid {PALETTE['border']}; padding-top: 0.5rem;">
                                    {arch['description']}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            # Scatter Plot
            clusters_df = pattern_res.get("clusters", pd.DataFrame())
            if not clusters_df.empty:
                st.markdown("#### 📈 Monthly Archetype Distribution")
                fig_cluster = px.scatter(
                    clusters_df,
                    x="month",
                    y="total_spend",
                    color="archetype",
                    size="total_spend",
                    title="Monthly Spending Profiles Grouped by K-Means Archetype",
                    labels={"month": "Month", "total_spend": "Total Spend (₹)", "archetype": "Spending Archetype"},
                )
                st.plotly_chart(plotly_fintech_theme(fig_cluster), use_container_width=True)

        elif pattern_res["status"] == "insufficient_history":
            st.info(f"ℹ️ **Statistical Integrity Notice:** {pattern_res['message']}")

        # Universal Fallbacks: Essential vs Discretionary & Category Volatility
        st.markdown("#### ⚖️ Needs vs. Wants (Essential vs. Discretionary Spending Ratio)")
        ess_res = pattern_res.get("essential_vs_discretionary", {})
        if ess_res.get("status") == "computed":
            e_col1, e_col2, e_col3 = st.columns(3)
            e_col1.metric("Total Tracked Spending", format_currency(ess_res["total"]))
            e_col2.metric("Essential Needs", format_currency(ess_res["essential"]), delta=f"{ess_res['essential_pct']}% of total", delta_color="off")
            e_col3.metric("Discretionary Wants", format_currency(ess_res["discretionary"]), delta=f"{ess_res['discretionary_pct']}% of total", delta_color="off")

            st.caption("Benchmark Guideline (50/30/20 Rule): ~50% Essential Needs, ~30% Discretionary Wants, and ~20% Savings.")

        st.markdown("#### 📊 Category Volatility & Stability Analysis")
        st.caption("Evaluates the Coefficient of Variation ($CV = \\sigma / \\mu$) across months to differentiate fixed recurring commitments from volatile discretionary spending.")
        vol_df = pattern_res.get("category_volatility", pd.DataFrame())
        if not vol_df.empty:
            st.dataframe(
                vol_df[["category", "monthly_avg", "std_dev", "cv", "stability_class"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "category": "Category",
                    "monthly_avg": st.column_config.NumberColumn("Monthly Average", format="₹%.2f"),
                    "std_dev": st.column_config.NumberColumn("Std Deviation", format="₹%.2f"),
                    "cv": st.column_config.NumberColumn("Volatility (CV)", format="%.2f"),
                    "stability_class": "Stability Classification",
                },
            )
