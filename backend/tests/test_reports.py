from decimal import Decimal
from fastapi.testclient import TestClient
from app.models import User


def test_monthly_report_and_savings_rate(auth_client_a: TestClient):
    # Add income 100,000 for October 2026
    auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-01",
            "transaction_type": "income",
            "amount": 100000.00,
            "category": "Salary",
        },
    )
    # Add food expense 25,000
    auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-05",
            "transaction_type": "expense",
            "amount": 25000.00,
            "category": "Food",
        },
    )
    # Add bills expense 15,000
    auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-10",
            "transaction_type": "expense",
            "amount": 15000.00,
            "category": "Bills",
        },
    )

    # Fetch monthly report
    res = auth_client_a.get("/reports/monthly?year=2026&month=10")
    assert res.status_code == 200
    data = res.json()

    assert Decimal(data["total_income"]) == Decimal("100000.00")
    assert Decimal(data["total_expenses"]) == Decimal("40000.00")
    assert Decimal(data["remaining_balance"]) == Decimal("60000.00")
    # Savings rate = (100k - 40k) / 100k * 100 = 60.00%
    assert Decimal(data["savings_rate"]) == Decimal("60.00")

    # Verify category distribution
    cats = data["category_expenses"]
    assert len(cats) == 2
    # Food is 25k/40k = 62.5%
    food_cat = next(c for c in cats if c["category"] == "Food")
    assert Decimal(food_cat["amount"]) == Decimal("25000.00")
    assert Decimal(food_cat["percentage"]) == Decimal("62.50")


def test_zero_income_savings_rate_safety(auth_client_a: TestClient):
    """Ensure zero income does not cause division by zero error."""
    # Add expense only for December 2026
    auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-12-01",
            "transaction_type": "expense",
            "amount": 5000.00,
            "category": "Food",
        },
    )

    res = auth_client_a.get("/reports/monthly?year=2026&month=12")
    assert res.status_code == 200
    data = res.json()
    assert Decimal(data["total_income"]) == Decimal("0.00")
    assert Decimal(data["savings_rate"]) == Decimal("0.00")
    assert Decimal(data["remaining_balance"]) == Decimal("-5000.00")


def test_csv_export_isolated_to_authenticated_user(
    auth_client_a: TestClient,
    auth_client_b: TestClient,
):
    # Add transaction for User A
    auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-01",
            "transaction_type": "expense",
            "amount": 1200.00,
            "category": "Food",
            "description": "User A secret expense",
        },
    )
    # Add transaction for User B
    auth_client_b.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-02",
            "transaction_type": "expense",
            "amount": 9999.00,
            "category": "Healthcare",
            "description": "User B secret record",
        },
    )

    # Export User A CSV
    res_a = auth_client_a.get("/reports/export")
    assert res_a.status_code == 200
    csv_text_a = res_a.text

    assert "User A secret expense" in csv_text_a
    assert "User B secret record" not in csv_text_a  # User B data must NEVER appear!
    assert "Amount (LKR)" in csv_text_a
