import uuid

import pytest
from fastapi.testclient import TestClient
from backend.main import app
import src.config as config
import src.database as database


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Use a fresh SQLite database for each CSRF/security integration test."""
    db_path = tmp_path / "csrf_test.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    database.init_db(custom_path=db_path)
    with TestClient(app, headers={"Origin": "http://localhost:5173"}) as test_client:
        yield test_client

# Helper to create a user and login, returning session cookie and csrf token
def register_and_login(client: TestClient, email: str, password: str, full_name: str = "Test User"):
    # Register (no CSRF needed)
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        headers={"origin": "http://localhost:5173"},
    )
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    data = resp.json()
    csrf_token = data.get("csrf_token")
    client.headers["X-CSRF-Token"] = csrf_token
    # Login (also returns CSRF token again, but we keep the one from register)
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
        headers={"origin": "http://localhost:5173"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    # Session cookie is stored in client.cookies automatically
    return csrf_token


def test_logout_successful_csrf_and_origin(client):
    csrf = register_and_login(client, f"csrf_{uuid.uuid4().hex}@example.com", "StrongPass123!")
    response = client.post(
        "/api/auth/logout",
        headers={
            "origin": "http://localhost:5173",
            "x-csrf-token": csrf,
        },
    )
    assert response.status_code == 200
    assert response.json().get("message") == "You have been signed out successfully."


def test_logout_invalid_origin(client):
    csrf = register_and_login(client, f"origin_{uuid.uuid4().hex}@example.com", "StrongPass123!")
    response = client.post(
        "/api/auth/logout",
        headers={
            "origin": "http://malicious.com",
            "x-csrf-token": csrf,
        },
    )
    assert response.status_code == 403
    assert "Invalid origin" in response.json().get("detail", "")


def test_logout_missing_csrf_token(client):
    register_and_login(client, f"missing_{uuid.uuid4().hex}@example.com", "StrongPass123!")
    client.headers.pop("X-CSRF-Token", None)
    response = client.post(
        "/api/auth/logout",
        headers={"origin": "http://localhost:5173"},
    )
    assert response.status_code == 403
    assert "Missing CSRF token" in response.json().get("detail", "")


def test_logout_invalid_csrf_token(client):
    csrf = register_and_login(client, f"invalid_{uuid.uuid4().hex}@example.com", "StrongPass123!")
    response = client.post(
        "/api/auth/logout",
        headers={
            "origin": "http://localhost:5173",
            "x-csrf-token": csrf + "tampered",
        },
    )
    assert response.status_code == 403
    assert "Invalid CSRF token" in response.json().get("detail", "")


def test_authenticated_coach_returns_complete_real_insights(client):
    email = f"coach_{uuid.uuid4().hex}@example.com"
    csrf = register_and_login(client, email, "StrongPass123!")
    user = client.get("/api/auth/me")
    assert user.status_code == 200

    # Create actual user transactions through the API; the coach must analyze these,
    # not substitute test recommendations.
    from datetime import date
    today = date.today().isoformat()
    for payload in (
        {"txn_date": today, "txn_type": "Income", "description": "Salary", "amount": 40000, "category": "Salary"},
        {"txn_date": today, "txn_type": "Expense", "description": "Rent", "amount": 36000, "category": "Rent"},
    ):
        created = client.post(
            "/api/transactions",
            json=payload,
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf},
        )
        assert created.status_code == 201, created.text

    response = client.get("/api/coach/insights")
    assert response.status_code == 200, response.text
    insights = response.json()["insights"]
    assert insights
    required = {
        "observation", "reason", "action", "impact", "evidence", "period",
        "confidence", "type", "severity", "priority", "recommendation_type",
    }
    assert all(required <= insight.keys() for insight in insights)
    assert any("40,000" in insight["evidence"] for insight in insights)


def test_authenticated_coach_handles_empty_transaction_history(client):
    email = f"empty_coach_{uuid.uuid4().hex}@example.com"
    register_and_login(client, email, "StrongPass123!")

    response = client.get("/api/coach/insights")
    assert response.status_code == 200, response.text
    insights = response.json()["insights"]
    assert len(insights) == 1
    assert insights[0]["confidence"] == "Data-Limited"
    assert insights[0]["observation"]
