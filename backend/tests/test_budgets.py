from decimal import Decimal
from fastapi.testclient import TestClient
from app.models import User


def test_set_and_get_monthly_budget(auth_client_a: TestClient):
    # Set Budget for 2026-10
    response = auth_client_a.post(
        "/budgets",
        json={
            "year": 2026,
            "month": 10,
            "amount": 50000.00,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == "50000.00"
    assert data["year"] == 2026
    assert data["month"] == 10

    # Retrieve all budgets
    res_list = auth_client_a.get("/budgets")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1


def test_budget_warning_and_overbudget_alerts(auth_client_a: TestClient):
    # Set budget of 10,000 for 2026-10
    auth_client_a.post(
        "/budgets",
        json={
            "year": 2026,
            "month": 10,
            "amount": 10000.00,
        },
    )

    # 1. Normal state: Spend 5,000 (50%)
    auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-05",
            "transaction_type": "expense",
            "amount": 5000.00,
            "category": "Food",
        },
    )
    status_1 = auth_client_a.get("/budgets/status?year=2026&month=10").json()
    assert status_1["status"] == "normal"
    assert Decimal(status_1["usage_percentage"]) == Decimal("50.00")

    # 2. Warning state: Spend another 3,500 (total 8,500 = 85%)
    auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-06",
            "transaction_type": "expense",
            "amount": 3500.00,
            "category": "Transport",
        },
    )
    status_2 = auth_client_a.get("/budgets/status?year=2026&month=10").json()
    assert status_2["status"] == "warning"
    assert Decimal(status_2["usage_percentage"]) == Decimal("85.00")

    # 3. Over-budget state: Spend another 2,000 (total 10,500 = 105%)
    auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-07",
            "transaction_type": "expense",
            "amount": 2000.00,
            "category": "Shopping",
        },
    )
    status_3 = auth_client_a.get("/budgets/status?year=2026&month=10").json()
    assert status_3["status"] == "over_budget"
    assert Decimal(status_3["usage_percentage"]) == Decimal("105.00")
    assert Decimal(status_3["remaining_budget"]) == Decimal("-500.00")


def test_income_does_not_count_towards_budget_usage(auth_client_a: TestClient):
    """Ensure income transactions do not erroneously alter expense calculations."""
    # Set budget of 20,000
    auth_client_a.post(
        "/budgets",
        json={"year": 2026, "month": 11, "amount": 20000.00},
    )
    # Add large income of 150,000
    auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-11-01",
            "transaction_type": "income",
            "amount": 150000.00,
            "category": "Salary",
        },
    )
    # Check status: expenses should still be 0.00
    status_data = auth_client_a.get("/budgets/status?year=2026&month=11").json()
    assert Decimal(status_data["expense_total"]) == Decimal("0.00")
    assert Decimal(status_data["remaining_budget"]) == Decimal("20000.00")
    assert status_data["status"] == "normal"
