"""Authenticated budget optimizer API tests using isolated SQLite databases."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import uuid

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.config as config
import src.database as database
from backend.main import app

ORIGIN = "http://localhost:5173"


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    path = tmp_path / "optimizer_test.db"
    monkeypatch.setattr(config, "DB_PATH", path)
    database.init_db(custom_path=path)
    return path


@pytest.fixture
def client(isolated_db):
    with TestClient(app, headers={"Origin": ORIGIN}) as test_client:
        yield test_client


def register(client: TestClient, label: str) -> tuple[int, str]:
    email = f"{label}_{uuid.uuid4().hex}@example.test"
    response = client.post("/api/auth/register", json={
        "full_name": f"Optimizer {label}",
        "email": email,
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
    })
    assert response.status_code == 201, response.text
    data = response.json()
    csrf = data["csrf_token"]
    client.headers["X-CSRF-Token"] = csrf
    return data["user"]["id"], csrf


def add_optimizer_history(user_id: int, target_month: str | None = None) -> None:
    today = date.today()
    month_index = today.year * 12 + today.month - 1
    for months_ago in (1, 2, 3):
        index = month_index - months_ago
        year, month_zero = divmod(index, 12)
        month = f"{year:04d}-{month_zero + 1:02d}"
        database.add_transaction(f"{month}-05", "Income", "Salary", 10000, "Salary", user_id=user_id)
        database.add_transaction(f"{month}-08", "Expense", "Rent", 4000, "Rent & Housing", user_id=user_id)
        database.add_transaction(f"{month}-12", "Expense", "Groceries", 5000, "Food & Dining", user_id=user_id)
        database.add_transaction(f"{month}-18", "Expense", "Shopping", 1000, "Shopping", user_id=user_id)

    month = target_month or today.strftime("%Y-%m")
    database.save_budget(month, "Food & Dining", 4700, user_id=user_id)
    database.save_budget(month, "Rent & Housing", 4500, user_id=user_id)
    database.add_bill("Electricity", 850, f"{month}-25", user_id=user_id)


def optimize(client: TestClient, savings_target: float = 2000):
    response = client.post("/api/budget/optimize", json={
        "months_history": 3,
        "savings_target": savings_target,
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_optimizer_uses_real_data_and_does_not_apply_before_approval(client):
    user_id, _csrf = register(client, "proposal")
    add_optimizer_history(user_id)
    month = date.today().strftime("%Y-%m")
    before = database.get_budgets(month=month, user_id=user_id).set_index("category")["limit_amount"].to_dict()

    proposal = optimize(client)
    by_category = {row["category"]: row for row in proposal["recommendations"]}
    assert proposal["status"] == "pending"
    assert by_category["Food & Dining"]["recommended_limit"] == pytest.approx(3333.33)
    assert by_category["Rent & Housing"]["recommended_limit"] == 4500
    assert proposal["unpaid_bills"] == [{
        "description": "Electricity",
        "amount": 850.0,
        "due_date": f"{month}-25",
    }]
    after = database.get_budgets(month=month, user_id=user_id).set_index("category")["limit_amount"].to_dict()
    assert after == before

    history = client.get("/api/budget/history")
    assert history.status_code == 200
    assert history.json()["history"][0]["optimization_id"] == proposal["optimization_id"]


def test_category_lock_is_applied_to_recommendation_and_can_be_removed(client):
    user_id, csrf = register(client, "locks")
    add_optimizer_history(user_id)
    month = date.today().strftime("%Y-%m")

    locked = client.patch("/api/budget/lock", json={
        "month": month,
        "category": "Food & Dining",
        "locked_limit": 3500,
    }, headers={"X-CSRF-Token": csrf})
    assert locked.status_code == 200
    proposal = optimize(client)
    food = next(item for item in proposal["recommendations"] if item["category"] == "Food & Dining")
    assert food["locked"] is True
    assert food["recommended_limit"] == 3500

    unlocked = client.patch("/api/budget/lock", json={
        "month": month,
        "category": "Food & Dining",
        "locked_limit": None,
    }, headers={"X-CSRF-Token": csrf})
    assert unlocked.status_code == 200
    refreshed = optimize(client)
    food = next(item for item in refreshed["recommendations"] if item["category"] == "Food & Dining")
    assert food["locked"] is False
    assert food["recommended_limit"] == pytest.approx(3333.33)


def test_approval_applies_budgets_and_undo_restores_previous_values(client):
    user_id, _csrf = register(client, "approval")
    add_optimizer_history(user_id)
    month = date.today().strftime("%Y-%m")
    proposal = optimize(client)

    # New categories are created only by approval; existing limits are snapshotted.
    before = database.get_budgets(month=month, user_id=user_id).set_index("category")["limit_amount"].to_dict()
    assert "Shopping" not in before
    approved = client.post("/api/budget/approve", json={"optimization_id": proposal["optimization_id"]})
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    after = database.get_budgets(month=month, user_id=user_id).set_index("category")["limit_amount"].to_dict()
    assert after["Food & Dining"] == pytest.approx(3333.33)
    assert "Shopping" in after

    undo = client.post("/api/budget/undo", json={"optimization_id": proposal["optimization_id"]})
    assert undo.status_code == 200, undo.text
    assert undo.json()["status"] == "undone"
    restored = database.get_budgets(month=month, user_id=user_id).set_index("category")["limit_amount"].to_dict()
    assert restored == before

    repeated = client.post("/api/budget/approve", json={"optimization_id": proposal["optimization_id"]})
    assert repeated.status_code == 409


def test_optimizer_history_and_actions_are_isolated_between_users(client):
    user_a, _csrf_a = register(client, "user_a")
    add_optimizer_history(user_a)
    proposal_a = optimize(client)
    user_a_client = client

    # Separate client keeps user B's cookie independent while sharing the isolated DB.
    with TestClient(app, headers={"Origin": ORIGIN}) as client_b:
        user_b, _csrf_b = register(client_b, "user_b")
        add_optimizer_history(user_b)
        assert client_b.get("/api/budget/history").json()["history"] == []
        forbidden = client_b.post("/api/budget/approve", json={"optimization_id": proposal_a["optimization_id"]})
        assert forbidden.status_code == 404

        month = date.today().strftime("%Y-%m")
        client_b.patch("/api/budget/lock", json={
            "month": month,
            "category": "Food & Dining",
            "locked_limit": 3300,
        })
        user_a_locks = database.get_category_locks(month, user_a)
        user_b_locks = database.get_category_locks(month, user_b)
        assert "Food & Dining" not in user_a_locks
        assert user_b_locks["Food & Dining"] == 3300

    assert user_a_client.get("/api/budget/history").json()["history"][0]["optimization_id"] == proposal_a["optimization_id"]


def test_optimizer_rejects_unachievable_savings_target(client):
    user_id, _csrf = register(client, "target")
    add_optimizer_history(user_id)
    response = client.post("/api/budget/optimize", json={
        "months_history": 3,
        "savings_target": 25000,
    })
    assert response.status_code == 422
    assert "cannot exceed" in response.json()["detail"]
