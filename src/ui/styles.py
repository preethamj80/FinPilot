"""Fintech Design System & CSS Styling for FinPilot.

Inspired by modern personal banking and financial SaaS applications (Stripe, Revolut, Mercury).
Features a clean light palette with deep navy navigation, emerald teal accents, and crisp white cards.
"""
from __future__ import annotations

# Design Tokens
PALETTE = {
    "navy_dark": "#0A192F",       # Primary Navy (Sidebar / Dark Accent)
    "navy_medium": "#0F2742",     # Secondary Navy
    "teal_primary": "#0D9488",    # Primary Teal
    "teal_accent": "#14B8A6",     # Accent Teal
    "bg_page": "#F5F8FC",         # Light Clean App Background
    "bg_card": "#FFFFFF",         # Pure White Card
    "text_primary": "#172B4D",    # Deep Navy-Slate Primary Text
    "text_secondary": "#64748B",  # Muted Slate Secondary Text
    "text_light": "#94A3B8",      # Subtle Tertiary Text
    "border": "#E2E8F0",          # Crisp Container Border
    "border_focus": "#0D9488",    # Teal Focus Border
    "success": "#16A34A",         # Positive Green
    "success_bg": "#DCFCE7",      # Subtle Green Pill
    "warning": "#D97706",         # Warning Amber
    "warning_bg": "#FEF3C7",      # Subtle Amber Pill
    "danger": "#DC2626",          # Critical Red
    "danger_bg": "#FEE2E2",       # Subtle Red Pill
    "info": "#2563EB",            # Informational Blue
    "info_bg": "#DBEAFE",         # Subtle Blue Pill
}

FINTECH_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

    /* Global Document & Typography */
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: {PALETTE['text_primary']};
        background-color: {PALETTE['bg_page']};
    }}

    .stApp {{
        background-color: {PALETTE['bg_page']};
        color: {PALETTE['text_primary']};
    }}

    /* Main Container Padding & Spacing */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3.5rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
        max-width: 1380px;
    }}

    /* Headings */
    h1, h2, h3, h4 {{
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
        font-weight: 700 !important;
        color: {PALETTE['text_primary']} !important;
        letter-spacing: -0.025em;
    }}

    h1 {{ font-size: 1.85rem !important; margin-bottom: 0.25rem !important; }}
    h2 {{ font-size: 1.45rem !important; margin-top: 1.25rem !important; }}
    h3 {{ font-size: 1.15rem !important; }}

    /* Sidebar Navigation (Deep Navy Aesthetic) */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {PALETTE['navy_dark']} 0%, {PALETTE['navy_medium']} 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }}

    [data-testid="stSidebar"] * {{
        color: #E2E8F0 !important;
    }}

    [data-testid="stSidebar"] hr {{
        border-color: rgba(255, 255, 255, 0.12) !important;
    }}

    /* Sidebar Brand Box */
    .sidebar-brand {{
        padding: 0.75rem 0.25rem 1.25rem 0.25rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 1.25rem;
    }}
    .sidebar-brand-name {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.45rem;
        font-weight: 800;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        letter-spacing: -0.03em;
    }}
    .sidebar-tagline {{
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: {PALETTE['teal_accent']} !important;
        font-weight: 600;
        margin-top: 2px;
    }}

    /* Sidebar Radio / Navigation Items */
    [data-testid="stSidebar"] div[role="radiogroup"] > label {{
        padding: 0.55rem 0.85rem;
        border-radius: 8px;
        margin-bottom: 4px;
        transition: all 0.15s ease-in-out;
        border: 1px solid transparent;
        cursor: pointer;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
        background-color: rgba(255, 255, 255, 0.06);
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {{
        background: rgba(13, 148, 136, 0.18) !important;
        border: 1px solid rgba(20, 184, 166, 0.35) !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] * {{
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }}

    /* Crisp White Fintech Cards */
    .fintech-card {{
        background-color: {PALETTE['bg_card']};
        border: 1px solid {PALETTE['border']};
        border-radius: 12px;
        padding: 1.25rem 1.4rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 1px 2px rgba(15, 23, 42, 0.02);
        margin-bottom: 1rem;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }}
    .fintech-card:hover {{
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.07);
    }}

    /* Header Banner / Welcome Hero */
    .fintech-hero {{
        background: linear-gradient(135deg, {PALETTE['navy_dark']} 0%, #102A45 70%, #133E4F 100%);
        border-radius: 16px;
        padding: 1.6rem 2rem;
        color: #FFFFFF !important;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(20, 184, 166, 0.2);
        box-shadow: 0 8px 24px rgba(10, 25, 47, 0.12);
    }}
    .fintech-hero h2 {{
        color: #FFFFFF !important;
        margin: 0.25rem 0 0.4rem 0 !important;
        font-size: 1.55rem !important;
    }}
    .fintech-hero p {{
        color: #CBD5E1 !important;
        margin: 0;
        font-size: 0.92rem;
    }}
    .fintech-hero-pill {{
        display: inline-block;
        background: rgba(13, 148, 136, 0.25);
        color: {PALETTE['teal_accent']} !important;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 0.2rem 0.65rem;
        border-radius: 9999px;
        border: 1px solid rgba(20, 184, 166, 0.4);
    }}

    /* Metrics Components */
    div[data-testid="stMetric"] {{
        background-color: {PALETTE['bg_card']};
        border: 1px solid {PALETTE['border']};
        border-radius: 12px;
        padding: 1rem 1.25rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }}
    div[data-testid="stMetricLabel"] {{
        color: {PALETTE['text_secondary']} !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    div[data-testid="stMetricValue"] {{
        color: {PALETTE['text_primary']} !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.65rem !important;
        font-weight: 700 !important;
    }}

    /* Form Containers */
    div[data-testid="stForm"] {{
        background-color: {PALETTE['bg_card']};
        border: 1px solid {PALETTE['border']};
        border-radius: 14px;
        padding: 1.4rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }}

    /* Primary & Secondary Buttons */
    .stButton>button, .stDownloadButton>button {{
        border-radius: 9px;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 0.5rem 1.1rem;
        transition: all 0.15s ease-in-out;
    }}
    .stButton>button[kind="primary"] {{
        background-color: {PALETTE['teal_primary']} !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 2px 6px rgba(13, 148, 136, 0.25);
    }}
    .stButton>button[kind="primary"]:hover {{
        background-color: #0F766E !important;
        box-shadow: 0 4px 12px rgba(13, 148, 136, 0.35);
    }}
    .stButton>button[kind="secondary"] {{
        background-color: #FFFFFF !important;
        color: {PALETTE['text_primary']} !important;
        border: 1px solid {PALETTE['border']} !important;
    }}
    .stButton>button[kind="secondary"]:hover {{
        background-color: #F8FAFC !important;
        border-color: #CBD5E1 !important;
    }}

    /* Status Badges & Pills */
    .pill-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.2rem 0.65rem;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .pill-success {{ background-color: {PALETTE['success_bg']}; color: {PALETTE['success']}; border: 1px solid #BBF7D0; }}
    .pill-danger  {{ background-color: {PALETTE['danger_bg']};  color: {PALETTE['danger']};  border: 1px solid #FECACA; }}
    .pill-warning {{ background-color: {PALETTE['warning_bg']}; color: {PALETTE['warning']}; border: 1px solid #FDE68A; }}
    .pill-info    {{ background-color: {PALETTE['info_bg']};    color: {PALETTE['info']};    border: 1px solid #BFDBFE; }}

    /* AI Money Coach Diagnostic Card */
    .coach-card {{
        background-color: {PALETTE['bg_card']};
        border: 1px solid {PALETTE['border']};
        border-left: 4px solid {PALETTE['teal_primary']};
        border-radius: 12px;
        padding: 1.25rem 1.4rem;
        margin-bottom: 1.15rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .coach-card:hover {{
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
    }}
    .coach-card-danger {{ border-left-color: {PALETTE['danger']}; }}
    .coach-card-warning {{ border-left-color: {PALETTE['warning']}; }}
    .coach-card-info {{ border-left-color: {PALETTE['info']}; }}
    .coach-card-success {{ border-left-color: {PALETTE['success']}; }}

    /* DataTables & DataFrames */
    [data-testid="stDataFrame"] {{
        background-color: {PALETTE['bg_card']};
        border-radius: 10px;
        border: 1px solid {PALETTE['border']};
    }}

    /* Expanders */
    div[data-testid="stExpander"] {{
        background-color: {PALETTE['bg_card']};
        border: 1px solid {PALETTE['border']};
        border-radius: 10px;
        margin-bottom: 0.85rem;
    }}

    /* Alerts */
    div[data-testid="stAlert"] {{
        border-radius: 10px;
        border: 1px solid rgba(0, 0, 0, 0.05);
    }}

    /* Subtle Dividers */
    hr {{
        border-color: {PALETTE['border']} !important;
        margin: 1.75rem 0 !important;
    }}
</style>
"""


def apply_fintech_theme() -> None:
    """Inject the global Fintech CSS design tokens into the Streamlit app."""
    import streamlit as st
    st.markdown(FINTECH_CSS, unsafe_allow_html=True)
