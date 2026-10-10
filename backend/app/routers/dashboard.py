from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Transaction, Budget
from app.schemas import DashboardSummaryResponse, BudgetStatusResponse, TransactionResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get comprehensive dashboard metrics",
    description="Returns monthly income, expenses, remaining balance, savings rate, budget utilization, and recent transactions.",
)
def get_dashboard_summary(
    year: Optional[int] = Query(None, description="Year (default: current year)"),
    month: Optional[int] = Query(None, description="Month 1-12 (default: current month)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    today = date.today()
    target_year = year if year is not None else today.year
    target_month = month if month is not None else today.month

    # Aggregate monthly income
    income_query = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == "income",
        extract("year", Transaction.transaction_date) == target_year,
        extract("month", Transaction.transaction_date) == target_month,
    )
    monthly_income = Decimal(str(income_query.scalar()))

    # Aggregate monthly expenses
    expense_query = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == "expense",
        extract("year", Transaction.transaction_date) == target_year,
        extract("month", Transaction.transaction_date) == target_month,
    )
    monthly_expenses = Decimal(str(expense_query.scalar()))

    # Calculate balance & savings rate
    remaining_balance = monthly_income - monthly_expenses
    if monthly_income > 0:
        savings_rate = round(((monthly_income - monthly_expenses) / monthly_income) * Decimal("100"), 2)
    else:
        savings_rate = Decimal("0.00")

    # Retrieve Budget status
    budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.year == target_year,
            Budget.month == target_month,
        )
        .first()
    )
    budget_amount = Decimal(str(budget.amount)) if budget else Decimal("0.00")
    remaining_budget = budget_amount - monthly_expenses
    usage_pct = (
        round((monthly_expenses / budget_amount) * Decimal("100"), 2)
        if budget_amount > 0
        else Decimal("0.00")
    )
    if budget_amount == 0:
        b_status = "normal"
    elif usage_pct > 100:
        b_status = "over_budget"
    elif usage_pct >= 80:
        b_status = "warning"
    else:
        b_status = "normal"

    budget_status = BudgetStatusResponse(
        year=target_year,
        month=target_month,
        budget_amount=budget_amount,
        expense_total=monthly_expenses,
        remaining_budget=remaining_budget,
        usage_percentage=usage_pct,
        status=b_status,
    )

    # 5 most recent transactions
    recent_txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .limit(5)
        .all()
    )

    return DashboardSummaryResponse(
        year=target_year,
        month=target_month,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        remaining_balance=remaining_balance,
        savings_rate=savings_rate,
        budget_status=budget_status,
        recent_transactions=[TransactionResponse.model_validate(t) for t in recent_txs],
    )
