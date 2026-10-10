from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User, Transaction


def test_create_income_and_expense_transaction(auth_client_a: TestClient, test_user_a: User):
    # Create Income
    res_income = auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-01",
            "transaction_type": "income",
            "amount": 75000.00,
            "category": "Salary",
            "description": "Monthly October Salary",
            "payment_method": "Bank Transfer",
        },
    )
    assert res_income.status_code == 201
    income_data = res_income.json()
    assert income_data["amount"] == "75000.00"
    assert income_data["user_id"] == test_user_a.id

    # Create Expense
    res_expense = auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-02",
            "transaction_type": "expense",
            "amount": 4500.50,
            "category": "Food",
            "description": "Grocery shopping",
            "payment_method": "Cash",
        },
    )
    assert res_expense.status_code == 201
    expense_data = res_expense.json()
    assert expense_data["amount"] == "4500.50"


def test_reject_negative_or_zero_amount(auth_client_a: TestClient):
    # Zero amount
    res_zero = auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-01",
            "transaction_type": "expense",
            "amount": 0,
            "category": "Food",
        },
    )
    assert res_zero.status_code == 422

    # Negative amount
    res_neg = auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-01",
            "transaction_type": "expense",
            "amount": -500.00,
            "category": "Food",
        },
    )
    assert res_neg.status_code == 422


def test_list_and_filter_transactions(auth_client_a: TestClient):
    # Add food and transport expenses
    auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-01",
            "transaction_type": "expense",
            "amount": 2000.00,
            "category": "Food",
            "description": "Lunch with friends",
        },
    )
    auth_client_a.post(
        "/transactions",
        json={
            "transaction_date": "2026-10-02",
            "transaction_type": "expense",
            "amount": 1500.00,
            "category": "Transport",
            "description": "Bus fare and taxi",
        },
    )

    # Filter by category Food
    res_food = auth_client_a.get("/transactions?category=Food")
    assert res_food.status_code == 200
    assert len(res_food.json()) == 1
    assert res_food.json()[0]["category"] == "Food"

    # Search keyword
    res_search = auth_client_a.get("/transactions?search=taxi")
    assert res_search.status_code == 200
    assert len(res_search.json()) == 1
    assert "taxi" in res_search.json()[0]["description"].lower()


# ==============================================================================
# IDOR & Broken Access Control Security Tests (Crucial!)
# ==============================================================================

def test_idor_user_a_cannot_read_user_b_transaction(
    auth_client_a: TestClient,
    auth_client_b: TestClient,
    test_user_b: User,
    db_session: Session,
):
    """Ensure User A cannot read User B's private transaction (mitigating IDOR)."""
    # Create transaction for User B
    tx_b = Transaction(
        user_id=test_user_b.id,
        transaction_date=date(2026, 10, 5),
        transaction_type="expense",
        amount=Decimal("12000.00"),
        category="Healthcare",
        description="Confidential medical expense",
        payment_method="Card",
    )
    db_session.add(tx_b)
    db_session.commit()
    db_session.refresh(tx_b)

    # User B can view their own transaction
    res_b = auth_client_b.get(f"/transactions/{tx_b.id}")
    assert res_b.status_code == 200
    assert res_b.json()["id"] == tx_b.id

    # User A tries to view User B's transaction -> MUST BE REJECTED (404)
    res_a = auth_client_a.get(f"/transactions/{tx_b.id}")
    assert res_a.status_code == 404
    assert "permission" in res_a.json()["detail"].lower() or "not found" in res_a.json()["detail"].lower()


def test_idor_user_a_cannot_update_user_b_transaction(
    auth_client_a: TestClient,
    test_user_b: User,
    db_session: Session,
):
    """Ensure User A cannot tamper with User B's transaction."""
    tx_b = Transaction(
        user_id=test_user_b.id,
        transaction_date=date(2026, 10, 5),
        transaction_type="expense",
        amount=Decimal("5000.00"),
        category="Shopping",
        payment_method="Cash",
    )
    db_session.add(tx_b)
    db_session.commit()

    # User A attempts to edit User B's transaction amount
    res_tamper = auth_client_a.put(
        f"/transactions/{tx_b.id}",
        json={"amount": 1.00},
    )
    assert res_tamper.status_code == 404

    # Verify amount remained unchanged in database
    db_session.refresh(tx_b)
    assert tx_b.amount == Decimal("5000.00")


def test_idor_user_a_cannot_delete_user_b_transaction(
    auth_client_a: TestClient,
    test_user_b: User,
    db_session: Session,
):
    """Ensure User A cannot delete User B's transaction."""
    tx_b = Transaction(
        user_id=test_user_b.id,
        transaction_date=date(2026, 10, 5),
        transaction_type="income",
        amount=Decimal("50000.00"),
        category="Salary",
        payment_method="Bank Transfer",
    )
    db_session.add(tx_b)
    db_session.commit()

    # User A attempts to delete User B's transaction
    res_del = auth_client_a.delete(f"/transactions/{tx_b.id}")
    assert res_del.status_code == 404

    # Verify transaction still exists in DB
    existing_tx = db_session.query(Transaction).filter(Transaction.id == tx_b.id).first()
    assert existing_tx is not None
