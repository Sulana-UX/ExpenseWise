import csv
import io
from datetime import date
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Transaction
from app.schemas import MonthlyReportResponse, CategoryExpense, TransactionType
from app.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports & Export"])


@router.get(
    "/monthly",
    response_model=MonthlyReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get monthly financial report and category breakdown",
    description="Calculates totals and percentage breakdown of expenses per category for the selected month.",
)
def get_monthly_report(
    year: Optional[int] = Query(None, description="Year (default: current year)"),
    month: Optional[int] = Query(None, description="Month 1-12 (default: current month)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MonthlyReportResponse:
    today = date.today()
    target_year = year if year is not None else today.year
    target_month = month if month is not None else today.month

    # Income total
    income_query = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == "income",
        extract("year", Transaction.transaction_date) == target_year,
        extract("month", Transaction.transaction_date) == target_month,
    )
    total_income = Decimal(str(income_query.scalar()))

    # Expense total
    expense_query = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == "expense",
        extract("year", Transaction.transaction_date) == target_year,
        extract("month", Transaction.transaction_date) == target_month,
    )
    total_expenses = Decimal(str(expense_query.scalar()))

    # Balance & Savings Rate
    remaining_balance = total_income - total_expenses
    if total_income > 0:
        savings_rate = round(((total_income - total_expenses) / total_income) * Decimal("100"), 2)
    else:
        savings_rate = Decimal("0.00")

    # Category-wise expenses
    cat_query = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("cat_total"),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            extract("year", Transaction.transaction_date) == target_year,
            extract("month", Transaction.transaction_date) == target_month,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    category_expenses: List[CategoryExpense] = []
    for row in cat_query:
        amt = Decimal(str(row.cat_total))
        pct = (
            round((amt / total_expenses) * Decimal("100"), 2)
            if total_expenses > 0
            else Decimal("0.00")
        )
        category_expenses.append(
            CategoryExpense(
                category=row.category,
                amount=amt,
                percentage=pct,
            )
        )

    return MonthlyReportResponse(
        year=target_year,
        month=target_month,
        total_income=total_income,
        total_expenses=total_expenses,
        remaining_balance=remaining_balance,
        savings_rate=savings_rate,
        category_expenses=category_expenses,
    )


@router.get(
    "/export",
    status_code=status.HTTP_200_OK,
    summary="Export transactions as CSV",
    description="Generates a downloadable CSV containing only the authenticated user's transactions.",
)
def export_transactions_csv(
    start_date: Optional[date] = Query(None, description="Filter start date"),
    end_date: Optional[date] = Query(None, description="Filter end date"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    transactions = query.order_by(Transaction.transaction_date.desc()).all()

    # Generate CSV in-memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write Header row
    writer.writerow([
        "Date",
        "Type",
        "Category",
        "Description",
        "Payment Method",
        "Amount (LKR)",
    ])

    # Write Data rows (Sanitizing CSV formulas to prevent CSV Injection)
    for tx in transactions:
        desc = tx.description or ""
        # Escape leading '=' '+' '-' '@' that could trigger formula execution in spreadsheet tools
        if desc.startswith(("=", "+", "-", "@")):
            desc = f"'{desc}"

        writer.writerow([
            tx.transaction_date.isoformat(),
            tx.transaction_type.capitalize(),
            tx.category,
            desc,
            tx.payment_method,
            f"{tx.amount:.2f}",
        ])

    csv_content = output.getvalue()
    filename = f"ExpenseWise_Transactions_{date.today().isoformat()}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
