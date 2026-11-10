"""Reusable UI component library for FinPilot's Fintech Design System."""
from __future__ import annotations

from typing import Any
import plotly.graph_objects as go
import streamlit as st

from src.ui.styles import PALETTE


def format_currency(val: float | int) -> str:
    """Format numeric values cleanly as INR currency."""
    try:
        f_val = float(val)
        if abs(f_val) >= 100000:
            return f"₹{f_val:,.0f}"
        return f"₹{f_val:,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"


def page_header(title: str, subtitle: str = "", badge: str | None = None) -> None:
    """Render a modern fintech page header with optional pill badge."""
    badge_html = f'<span class="fintech-hero-pill" style="margin-left: 0.75rem;">{badge}</span>' if badge else ""
    st.markdown(
        f"""
        <div style="margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center;">
                <h1 style="margin: 0;">{title}</h1>
                {badge_html}
            </div>
            {f'<p style="color: {PALETTE["text_secondary"]}; font-size: 0.95rem; margin-top: 0.35rem; margin-bottom: 0;">{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero_banner(title: str, subtitle: str, pill_text: str = "FINANCIAL CO-PILOT") -> None:
    """Render an executive gradient banner for top-level summaries."""
    st.markdown(
        f"""
        <div class="fintech-hero">
            <span class="fintech-hero-pill">{pill_text}</span>
            <h2>{title}</h2>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_header() -> None:
    """Render the sidebar brand block."""
    st.markdown(
        f"""
        <div class="sidebar-brand">
            <div class="sidebar-brand-name">
                <span style="color: {PALETTE['teal_accent']};">💸</span> FinPilot
            </div>
            <div class="sidebar-tagline">Intelligent Personal Finance</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_coach_card(rec: dict[str, Any]) -> None:
    """Render a structured, evidence-backed AI Money Coach diagnostic card."""
    severity = rec.get("severity", "info")
    sev_class = f"coach-card-{severity}"
    sev_icon = "🚨" if severity == "danger" else "⚠️" if severity == "warning" else "💡" if severity == "info" else "✅"
    pill_class = f"pill-{severity}"

    st.markdown(
        f"""
        <div class="coach-card {sev_class}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.15rem;">{sev_icon}</span>
                    <span style="font-weight: 700; font-size: 1.05rem; color: {PALETTE['text_primary']};">{rec['rec_type']}</span>
                </div>
                <span class="pill-badge {pill_class}">Confidence: {rec.get('confidence', 'Moderate')}</span>
            </div>
            <div style="margin-bottom: 0.5rem; font-size: 0.95rem; line-height: 1.5; color: {PALETTE['text_primary']};">
                <strong>Observation:</strong> {rec['observation']}
            </div>
            <div style="margin-bottom: 0.5rem; font-size: 0.9rem; color: {PALETTE['text_secondary']}; line-height: 1.45;">
                <strong>Why it matters:</strong> {rec['why_it_matters']}
            </div>
            <div style="margin-bottom: 0.85rem; font-size: 0.92rem; color: {PALETTE['teal_primary']}; font-weight: 600;">
                🎯 <strong>Suggested Action:</strong> {rec['suggested_action']}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 0.65rem; border-top: 1px solid {PALETTE['border']}; font-size: 0.82rem; color: {PALETTE['text_secondary']};">
                <span>📊 <strong>Evidence:</strong> {rec['supporting_evidence']}</span>
                <span style="font-weight: 700; color: {PALETTE['text_primary']}; font-size: 0.9rem;">
                    Est. Monthly Impact: {format_currency(rec.get('estimated_monthly_impact', 0.0))}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(title: str, description: str, icon: str = "📂") -> None:
    """Render a clean placeholder when data is missing."""
    st.markdown(
        f"""
        <div class="fintech-card" style="text-align: center; padding: 2.5rem 1.5rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">{icon}</div>
            <h3 style="color: {PALETTE['text_primary']}; margin-bottom: 0.35rem;">{title}</h3>
            <p style="color: {PALETTE['text_secondary']}; font-size: 0.92rem; max-width: 460px; margin: 0 auto;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plotly_fintech_theme(fig: go.Figure) -> go.Figure:
    """Apply a standardized, clean light fintech theme to any Plotly chart."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=PALETTE["bg_card"],
        plot_bgcolor=PALETTE["bg_card"],
        font=dict(
            family="Inter, sans-serif",
            color=PALETTE["text_primary"],
            size=12,
        ),
        margin=dict(l=15, r=15, t=40, b=15),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text="",
        ),
        colorway=[
            PALETTE["teal_primary"],
            "#3B82F6",  # Blue
            "#F59E0B",  # Amber
            "#EC4899",  # Pink
            "#8B5CF6",  # Purple
            "#10B981",  # Emerald
            "#F97316",  # Orange
            "#6366F1",  # Indigo
        ],
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor=PALETTE["border"],
        tickfont=dict(color=PALETTE["text_secondary"]),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor=PALETTE["border"],
        tickfont=dict(color=PALETTE["text_secondary"]),
    )
    return fig
