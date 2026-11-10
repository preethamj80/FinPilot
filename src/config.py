"""FinPilot application configuration, design tokens, and domain constants."""
from __future__ import annotations

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "finance.db"
BACKUPS_DIR = BASE_DIR / "backups"
MODELS_DIR = BASE_DIR / "models"

# App Branding & Meta
APP_NAME = "FinPilot"
APP_TAGLINE = "AI-Based Personal Finance Intelligence"
APP_ICON = "💸"

# Brand Design Tokens (Fintech Palette: Navy, Teal, Crisp Light)
COLORS = {
    "primary": "#0D9488",        # Emerald Teal (Brand Accent)
    "primary_dark": "#0F766E",   # Deep Teal
    "primary_light": "#14B8A6",  # Light Teal
    "navy_900": "#0A192F",       # Deep Navy (Primary Dark)
    "navy_800": "#0F172A",       # Slate Navy
    "navy_700": "#1E293B",       # Card Border / Dark Accent
    "bg_main": "#F8FAFC",        # Crisp Off-White / Soft Slate
    "bg_card": "#FFFFFF",        # Pure White Card Background
    "border": "#E2E8F0",         # Subtle Card Border
    "text_primary": "#0F172A",   # High Contrast Dark Slate Text
    "text_secondary": "#64748B", # Muted Gray Text
    "success": "#10B981",        # Positive / Inflow Green
    "danger": "#EF4444",         # Outflow / Warning Red
    "warning": "#F59E0B",        # Alert Amber
    "info": "#3B82F6",           # Blue Accent
}

# Transaction Categories
# Core expense categories — covers all required user-facing categories
EXPENSE_CATEGORIES = [
    "Food & Dining",       # restaurants, takeaway, food delivery
    "Groceries",           # supermarket, fresh produce, household staples
    "Rent & Housing",      # rent, maintenance, home expenses
    "Transportation",      # fuel, cab, metro, bus, auto
    "Utilities",           # electricity, water, internet, gas, mobile recharge
    "Shopping",            # clothing, electronics, online shopping
    "Health & Medical",    # pharmacy, doctor, hospital, clinic
    "Education",           # tuition, courses, books, exam fees
    "Entertainment",       # movies, streaming, concerts, games
    "Travel",              # flights, hotels, trip expenses
    "Personal Care",       # salon, grooming, skincare
    "Insurance",           # health, vehicle, life insurance premiums
    "Subscriptions",       # Netflix, Spotify, software subscriptions
    "Miscellaneous",       # catch-all for uncategorised expenses
    "Other",               # user-defined overflow
]

INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Investment Returns",
    "Business Income",
    "Other Income",
]

# All categories for general use
CATEGORIES = EXPENSE_CATEGORIES + INCOME_CATEGORIES

# Legacy aliases: map old category names → new names (for data migration display only)
# Historical data retains its original labels; these aliases are used by UI/coach for display grouping
CATEGORY_ALIASES = {
    "Food": "Food & Dining",
    "Transport": "Transportation",
    "Rent": "Rent & Housing",
    "Health": "Health & Medical",
    "Investment": "Investment Returns",
}

# Financial Planning Defaults
DEFAULT_OPENING_BALANCE = 0.0
DEFAULT_SAFETY_RESERVE = 2000.0
DEFAULT_MONTHLY_SAVINGS_TARGET = 0.0
DEFAULT_CURRENCY_SYMBOL = "₹"
