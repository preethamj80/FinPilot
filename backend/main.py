"""FinPilot FastAPI Backend — main application entry point.

Starts the API server that serves the React frontend (Stage 2+).
Existing Streamlit app (app.py) is completely untouched.
"""
from __future__ import annotations

import sqlite3
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# ── Project root on sys.path so src.* and utils.* resolve correctly ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.routers import auth, overview, transactions, budgets, coach, simulator, insights, settings, budget_optimizer
from backend.auth.csrf import CSRFMiddleware
import src.database as _db

# ── Lifespan: DB init + WAL mode ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    _db.init_db()
    from src.config import DB_PATH
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.close()
    except Exception as exc:
        print(f"[FinPilot] Warning: Could not enable WAL mode — {exc}")
    yield
    # Shutdown (nothing needed)

# ── FastAPI application ──
app = FastAPI(
    title="FinPilot API",
    description=(
        "REST API for FinPilot – AI-Based Personal Finance Management System. "
        "Provides financial data, ML insights, and planning tools for the React frontend."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS – only local dev origins, credentials enabled ──
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Origin validation middleware for state‑changing requests ──
class OriginValidatorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            origin = request.headers.get("origin")
            if not origin or origin not in ALLOWED_ORIGINS:
                return JSONResponse(
                    {"detail": "Invalid origin for state-changing request"},
                    status_code=403,
                )
        return await call_next(request)

app.add_middleware(OriginValidatorMiddleware)
app.add_middleware(CSRFMiddleware)

# ── Health check ──
@app.get("/api/health", tags=["Health"])
def health_check():
    """API health check — verify the server is running."""
    return {"status": "ok", "version": "1.0.0", "app": "FinPilot API"}

# ── Categories endpoint ──
@app.get("/api/categories", tags=["Categories"])
def get_categories():
    """Return the canonical expense and income category lists for UI dropdowns.

    Historical transactions may contain legacy category names; those are preserved as‑is
    in the database. This endpoint returns the current preferred category labels.
    """
    from src.config import EXPENSE_CATEGORIES, INCOME_CATEGORIES, CATEGORIES, CATEGORY_ALIASES
    return {
        "expense": EXPENSE_CATEGORIES,
        "income": INCOME_CATEGORIES,
        "all": CATEGORIES,
        "aliases": CATEGORY_ALIASES,
    }

# ── Mount routers ──
app.include_router(auth.router, prefix="/api")
app.include_router(overview.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(budgets.router, prefix="/api")
app.include_router(coach.router, prefix="/api")
app.include_router(simulator.router, prefix="/api")
app.include_router(insights.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(budget_optimizer.router, prefix="/api")
