"""
FastAPI backend tests for FinPilot.

Uses httpx.TestClient with a temporary SQLite database injected via
monkeypatching src.config.DB_PATH — no writes to data/finance.db.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

# ─── Project root on sys.path ────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.auth.dependencies import get_current_user, AuthenticatedUser


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Give each test its own database and keep all auth writes out of finance.db."""
    import src.config as config
    import src.database as db_module

    db_path = tmp_path / "test_finance.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    db_module.init_db(custom_path=db_path)
    return db_path


@pytest.fixture
def client(temp_db):
    """Return a TestClient wired to a temporary database with authenticated test user."""
    import src.database as db_module

    # Seed transactions for user_id = 0
    db_module.add_transaction("2026-10-01", "Income", "Salary October", 50000.0, "Salary", "", custom_path=temp_db, user_id=0)
    db_module.add_transaction("2026-10-05", "Expense", "Swiggy order", 450.0, "Food", "", custom_path=temp_db, user_id=0)
    db_module.add_transaction("2026-10-10", "Expense", "Electricity bill", 1200.0, "Utilities", "", custom_path=temp_db, user_id=0)
    db_module.add_transaction("2026-10-15", "Expense", "Amazon shopping", 2500.0, "Shopping", "", custom_path=temp_db, user_id=0)
    db_module.add_transaction("2026-11-01", "Income", "Salary November", 50000.0, "Salary", "", custom_path=temp_db, user_id=0)
    db_module.add_transaction("2026-11-05", "Expense", "Uber ride", 300.0, "Transport", "", custom_path=temp_db, user_id=0)

    db_module.save_budget("2026-11", "Food", 5000.0, custom_path=temp_db, user_id=0)
    db_module.save_budget("2026-11", "Shopping", 3000.0, custom_path=temp_db, user_id=0)
    db_module.add_bill("Internet Bill", 999.0, "2026-11-20", "Monthly", "", custom_path=temp_db, user_id=0)

    import backend.dependencies as deps

    def _tx(user_id=0):
        return db_module.get_transactions(custom_path=temp_db, user_id=user_id)

    def _bud(user_id=0, month=None):
        return db_module.get_budgets(month=month, custom_path=temp_db, user_id=user_id)

    def _bills(user_id=0):
        return db_module.get_bills(custom_path=temp_db, user_id=user_id)

    def _settings(user_id=0):
        return db_module.get_settings(custom_path=temp_db)

    deps.get_transactions_df = _tx
    deps.get_budgets_df = _bud
    deps.get_bills_df = _bills
    deps.get_settings_dict = _settings

    from fastapi.testclient import TestClient
    from backend.main import app

    # Default authenticated user for standard functional tests
    test_user = AuthenticatedUser(
        id=0,
        full_name="Test User",
        email="test@finpilot.local",
        csrf_token="test_csrf_token_123",
    )
    app.dependency_overrides[get_current_user] = lambda: test_user

    with TestClient(
        app,
        headers={
            "Origin": "http://localhost:5173",
            "X-CSRF-Token": "test_csrf_token_123",
        },
    ) as c:
        yield c

    app.dependency_overrides.clear()


# ─── Health ───────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"] == "1.0.0"


# ─── Overview ─────────────────────────────────────────────────────────────────

def test_overview_summary(client):
    r = client.get("/api/overview/summary")
    assert r.status_code == 200
    body = r.json()
    assert "spendable" in body
    assert "total_income" in body
    assert "total_expenses" in body
    assert isinstance(body["assumptions"], list)


def test_overview_category_mix(client):
    r = client.get("/api/overview/category-mix")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    if items:
        assert "category" in items[0]
        assert "amount" in items[0]


def test_overview_monthly_trend(client):
    r = client.get("/api/overview/monthly-trend")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    if items:
        assert "month" in items[0]
        assert "income" in items[0]
        assert "expenses" in items[0]


# ─── Transactions ─────────────────────────────────────────────────────────────

def test_list_transactions(client):
    r = client.get("/api/transactions")
    assert r.status_code == 200
    body = r.json()
    assert "data" in body
    assert "total" in body
    assert body["total"] >= 6


def test_create_transaction(client):
    payload = {
        "txn_date": "2026-11-08",
        "txn_type": "Expense",
        "description": "Test coffee purchase",
        "amount": 150.0,
        "category": "Food",
        "notes": "API test",
    }
    r = client.post("/api/transactions", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["description"] == "Test coffee purchase"
    assert body["amount"] == 150.0
    assert "id" in body


def test_update_transaction(client):
    payload = {
        "txn_date": "2026-11-09",
        "txn_type": "Expense",
        "description": "Update test transaction",
        "amount": 200.0,
        "category": "Transport",
        "notes": "",
    }
    r_create = client.post("/api/transactions", json=payload)
    assert r_create.status_code == 201
    txn_id = r_create.json()["id"]

    update_payload = {**payload, "amount": 250.0, "notes": "Updated"}
    r = client.put(f"/api/transactions/{txn_id}", json=update_payload)
    assert r.status_code == 200
    assert r.json()["amount"] == 250.0


def test_delete_transaction(client):
    payload = {
        "txn_date": "2026-11-09",
        "txn_type": "Expense",
        "description": "Delete me",
        "amount": 99.0,
        "category": "Other",
        "notes": "",
    }
    r_create = client.post("/api/transactions", json=payload)
    assert r_create.status_code == 201
    txn_id = r_create.json()["id"]

    r_del = client.delete(f"/api/transactions/{txn_id}")
    assert r_del.status_code == 200
    assert r_del.json()["deleted"] == txn_id

    r_check = client.get("/api/transactions")
    ids = [t["id"] for t in r_check.json()["data"]]
    assert txn_id not in ids


def test_delete_nonexistent_transaction(client):
    r = client.delete("/api/transactions/999999")
    assert r.status_code == 404


def test_predict_category(client):
    r = client.post("/api/transactions/predict-category", json={"description": "Swiggy dinner", "txn_type": "Expense"})
    assert r.status_code == 200
    body = r.json()
    assert "category" in body
    assert "method" in body


# ─── Budgets ─────────────────────────────────────────────────────────────────

def test_list_budgets(client):
    r = client.get("/api/budgets")
    assert r.status_code == 200
    body = r.json()
    assert "budgets" in body
    assert "utilization" in body
    assert "current_month" in body


def test_create_budget(client):
    r = client.post("/api/budgets", json={"month": "2026-11", "category": "Health", "limit_amount": 2000.0})
    assert r.status_code == 201
    body = r.json()
    assert body["category"] == "Health"
    assert body["limit_amount"] == 2000.0


def test_delete_budget(client):
    r_create = client.post("/api/budgets", json={"month": "2026-10", "category": "Education", "limit_amount": 1500.0})
    assert r_create.status_code == 201
    budget_id = r_create.json()["id"]

    r_del = client.delete(f"/api/budgets/{budget_id}")
    assert r_del.status_code == 200


# ─── Bills ────────────────────────────────────────────────────────────────────

def test_list_bills(client):
    r = client.get("/api/bills")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_bill(client):
    r = client.post("/api/bills", json={
        "description": "Netflix Subscription",
        "amount": 499.0,
        "due_date": "2026-11-25",
        "frequency": "Monthly",
        "next_due_date": "",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["description"] == "Netflix Subscription"


# ─── Coach ────────────────────────────────────────────────────────────────────

def test_coach_insights(client):
    r = client.get("/api/coach/insights")
    assert r.status_code == 200
    body = r.json()
    assert "insights" in body
    assert "generated_at" in body
    assert isinstance(body["insights"], list)
    required = {
        "observation", "reason", "action", "impact", "evidence", "period",
        "confidence", "type", "severity", "priority", "recommendation_type",
    }
    assert body["insights"]
    assert all(required <= insight.keys() for insight in body["insights"])


# ─── Simulator ───────────────────────────────────────────────────────────────

def test_simulator_major_purchase(client):
    r = client.post("/api/simulator/major-purchase", json={
        "purchase_amount": 15000.0,
        "category": "Shopping",
        "planned_date": "2026-11-20",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["scenario"] == "major_purchase"
    assert "result" in body


def test_simulator_expense_reduction(client):
    r = client.post("/api/simulator/expense-reduction", json={
        "category": "Food",
        "reduction_pct": 20.0,
        "duration_months": 3,
    })
    assert r.status_code == 200
    assert r.json()["scenario"] == "expense_reduction"


def test_simulator_income_reduction(client):
    r = client.post("/api/simulator/income-reduction", json={"reduction_pct": 10.0, "duration_months": 3})
    assert r.status_code == 200
    assert r.json()["scenario"] == "income_reduction"


def test_simulator_monthly_savings(client):
    r = client.post("/api/simulator/monthly-savings", json={
        "monthly_contribution": 5000.0,
        "duration_months": 12,
        "initial_savings": 0.0,
    })
    assert r.status_code == 200
    assert r.json()["scenario"] == "monthly_savings"


# ─── Insights ─────────────────────────────────────────────────────────────────

def test_forecast(client):
    r = client.get("/api/insights/forecast")
    assert r.status_code == 200
    body = r.json()
    assert "overall" in body
    assert "by_category" in body


def test_anomalies(client):
    r = client.get("/api/insights/anomalies")
    assert r.status_code == 200
    body = r.json()
    assert "anomalies" in body
    assert "total_scanned" in body


def test_patterns(client):
    r = client.get("/api/insights/patterns")
    assert r.status_code == 200
    body = r.json()
    assert "clusters" in body
    assert "summary" in body


def test_categorization_status(client):
    r = client.get("/api/insights/categorization")
    assert r.status_code == 200
    body = r.json()
    assert "model_loaded" in body
    assert "categories" in body


# ─── Settings ─────────────────────────────────────────────────────────────────

def test_get_settings(client):
    r = client.get("/api/settings")
    assert r.status_code == 200
    body = r.json()
    assert "opening_balance" in body
    assert "safety_reserve" in body
    assert "monthly_savings_target" in body


def test_update_settings(client):
    r = client.put("/api/settings", json={
        "opening_balance": 10000.0,
        "safety_reserve": 3000.0,
        "monthly_savings_target": 5000.0,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["opening_balance"] == 10000.0
    assert body["safety_reserve"] == 3000.0


# ─── CSV Export ──────────────────────────────────────────────────────────────

def test_export_csv(client):
    r = client.get("/api/transactions/export-csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    content = r.text
    assert "txn_date" in content


# ─── AUTHENTICATION & MULTI-USER ISOLATION TESTS ─────────────────────────────

def test_unauthenticated_request_rejected(temp_db):
    """Unauthenticated access to protected endpoints must return 401."""
    from fastapi.testclient import TestClient
    from backend.main import app

    # Create client WITHOUT any dependency overrides
    old_overrides = dict(app.dependency_overrides)
    app.dependency_overrides.clear()
    try:
        with TestClient(
            app, headers={"Origin": "http://localhost:5173", "X-CSRF-Token": "test-token"}
        ) as raw_client:
            r = raw_client.get("/api/overview/summary")
            assert r.status_code == 401
            assert "Not authenticated" in r.json()["detail"]

            r_tx = raw_client.get("/api/transactions")
            assert r_tx.status_code == 401
    finally:
        app.dependency_overrides = old_overrides


def test_auth_register_and_login_flow(temp_db):
    """Full lifecycle: register -> receive session cookie -> get /me -> logout."""
    import uuid
    from fastapi.testclient import TestClient
    from backend.main import app
    import src.config as config

    test_email = f"aarav_{uuid.uuid4().hex[:6]}@example.com"
    old_overrides = dict(app.dependency_overrides)
    app.dependency_overrides.clear()
    try:
        with TestClient(
            app, headers={"Origin": "http://localhost:5173", "X-CSRF-Token": "test-token"}
        ) as raw_client:
            # 1. Register new user
            reg_payload = {
                "full_name": "Aarav Sharma",
                "email": test_email,
                "password": "Password123!",
                "confirm_password": "Password123!",
            }
            reg_res = raw_client.post("/api/auth/register", json=reg_payload)
            assert reg_res.status_code == 201
            reg_data = reg_res.json()
            assert reg_data["user"]["email"] == test_email
            assert "csrf_token" in reg_data
            raw_client.headers["X-CSRF-Token"] = reg_data["csrf_token"]

            # 2. Access /api/auth/me with session cookie
            me_res = raw_client.get("/api/auth/me")
            assert me_res.status_code == 200
            assert me_res.json()["email"] == test_email

            # 3. Duplicate registration should fail with 409
            dup_res = raw_client.post("/api/auth/register", json=reg_payload)
            assert dup_res.status_code == 409

            # 4. Logout
            logout_res = raw_client.post("/api/auth/logout")
            assert logout_res.status_code == 200

            # 5. /me should now fail with 401
            me_after = raw_client.get("/api/auth/me")
            assert me_after.status_code == 401

            # 6. Login again
            login_res = raw_client.post("/api/auth/login", json={
                "email": test_email,
                "password": "Password123!",
            })
            assert login_res.status_code == 200
    finally:
        app.dependency_overrides = old_overrides


def test_multi_user_isolation(temp_db):
    """Verify that User A cannot see or mutate User B's transactions or budgets."""
    import uuid
    from fastapi.testclient import TestClient
    from backend.main import app

    email_a = f"alpha_{uuid.uuid4().hex[:6]}@example.com"
    email_b = f"beta_{uuid.uuid4().hex[:6]}@example.com"

    old_overrides = dict(app.dependency_overrides)
    app.dependency_overrides.clear()
    try:
        # Register User A
        with TestClient(
            app, headers={"Origin": "http://localhost:5173", "X-CSRF-Token": "test-token"}
        ) as client_a:
            reg_a = client_a.post("/api/auth/register", json={
                "full_name": "User Alpha",
                "email": email_a,
                "password": "SecurePassword1",
                "confirm_password": "SecurePassword1",
            })
            assert reg_a.status_code == 201
            client_a.headers["X-CSRF-Token"] = reg_a.json()["csrf_token"]

            # User A adds a transaction
            tx_res = client_a.post("/api/transactions", json={
                "txn_date": "2026-11-09",
                "txn_type": "Expense",
                "description": "Alpha Private Secret Purchase",
                "amount": 9999.0,
                "category": "Shopping",
                "notes": "Top secret",
            })
            assert tx_res.status_code == 201
            alpha_tx_id = tx_res.json()["id"]

            # User A lists transactions
            list_a = client_a.get("/api/transactions").json()
            assert any(t["id"] == alpha_tx_id for t in list_a["data"])

        # Register User B in a separate client session
        with TestClient(
            app, headers={"Origin": "http://localhost:5173", "X-CSRF-Token": "test-token"}
        ) as client_b:
            reg_b = client_b.post("/api/auth/register", json={
                "full_name": "User Beta",
                "email": email_b,
                "password": "SecurePassword2",
                "confirm_password": "SecurePassword2",
            })
            assert reg_b.status_code == 201
            client_b.headers["X-CSRF-Token"] = reg_b.json()["csrf_token"]

            # User B lists transactions -> should NOT see Alpha's transaction!
            list_b = client_b.get("/api/transactions").json()
            beta_tx_ids = [t["id"] for t in list_b["data"]]
            assert alpha_tx_id not in beta_tx_ids
            assert list_b["total"] == 0  # Brand new user starts with 0 transactions

            # User B attempts to delete Alpha's transaction by ID -> 404
            del_attempt = client_b.delete(f"/api/transactions/{alpha_tx_id}")
            assert del_attempt.status_code == 404
    finally:
        app.dependency_overrides = old_overrides
