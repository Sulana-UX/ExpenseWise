from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Budget, Transaction
from app.schemas import BudgetCreate, BudgetResponse, BudgetStatusResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get(
    "",
    response_model=List[BudgetResponse],
    status_code=status.HTTP_200_OK,
    summary="List all budgets for current user",
)
def list_budgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Budget]:
    return (
        db.query(Budget)
        .filter(Budget.user_id == current_user.id)
        .order_by(Budget.year.desc(), Budget.month.desc())
        .all()
    )


@router.post(
    "",
    response_model=BudgetResponse,
    status_code=status.HTTP_200_OK,
    summary="Set or update monthly spending budget",
    description="Creates or updates the overall spending budget for a specified month and year.",
)
def set_or_update_budget(
    budget_in: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Budget:
    # Check if budget already exists for this user, year, and month
    budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.year == budget_in.year,
            Budget.month == budget_in.month,
        )
        .first()
    )

    if budget:
        budget.amount = budget_in.amount
    else:
        budget = Budget(
            user_id=current_user.id,
            year=budget_in.year,
            month=budget_in.month,
            amount=budget_in.amount,
        )
        db.add(budget)

    db.commit()
    db.refresh(budget)
    return budget


@router.get(
    "/status",
    response_model=BudgetStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get monthly budget utilization and warning status",
    description="Calculates total expenses against the monthly budget and provides normal/warning/over_budget alerts.",
)
def get_budget_status(
    year: Optional[int] = Query(None, description="Year (default: current year)"),
    month: Optional[int] = Query(None, description="Month 1-12 (default: current month)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetStatusResponse:
    today = date.today()
    target_year = year if year is not None else today.year
    target_month = month if month is not None else today.month

    # Retrieve user's configured budget
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

    # Authoritative calculation of expenses in the specified month
    expense_sum_query = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == "expense",
        extract("year", Transaction.transaction_date) == target_year,
        extract("month", Transaction.transaction_date) == target_month,
    )
    expense_total = Decimal(str(expense_sum_query.scalar()))

    remaining_budget = budget_amount - expense_total
    if budget_amount > 0:
        usage_percentage = round((expense_total / budget_amount) * Decimal("100"), 2)
    else:
        usage_percentage = Decimal("0.00")

    # Determine alert status
    if budget_amount == 0:
        alert_status = "normal"
    elif usage_percentage > 100:
        alert_status = "over_budget"
    elif usage_percentage >= 80:
        alert_status = "warning"
    else:
        alert_status = "normal"

    return BudgetStatusResponse(
        year=target_year,
        month=target_month,
        budget_amount=budget_amount,
        expense_total=expense_total,
        remaining_budget=remaining_budget,
        usage_percentage=usage_percentage,
        status=alert_status,
    )
