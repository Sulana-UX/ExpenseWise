from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Transaction
from app.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionType,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get(
    "",
    response_model=List[TransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="List transactions for the authenticated user",
    description="Retrieves transactions owned by current user with optional filtering by type, category, date range, search, and pagination.",
)
def list_transactions(
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search keyword in description or category"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Transaction]:
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if category:
        query = query.filter(Transaction.category == category)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (Transaction.description.ilike(search_pattern)) |
            (Transaction.category.ilike(search_pattern))
        )

    # Order by transaction date descending, then created_at descending
    return (
        query.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transaction",
    description="Records an income or expense transaction strictly bound to the authenticated user.",
)
def create_transaction(
    tx_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    new_tx = Transaction(
        user_id=current_user.id,
        transaction_date=tx_in.transaction_date,
        transaction_type=tx_in.transaction_type,
        amount=tx_in.amount,
        category=tx_in.category.strip(),
        description=tx_in.description.strip() if tx_in.description else None,
        payment_method=tx_in.payment_method.strip(),
    )
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    return new_tx


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single transaction by ID",
    description="Returns transaction details only if owned by the authenticated user (prevents IDOR).",
)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    tx = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or you do not have permission to access it.",
        )
    return tx


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing transaction",
    description="Updates transaction details only if owned by the authenticated user.",
)
def update_transaction(
    transaction_id: int,
    tx_update: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    tx = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or you do not have permission to modify it.",
        )

    # Apply updates for explicitly provided fields
    update_data = tx_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "description" and value is not None:
            setattr(tx, field, value.strip())
        elif isinstance(value, str):
            setattr(tx, field, value.strip())
        else:
            setattr(tx, field, value)

    db.commit()
    db.refresh(tx)
    return tx


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a transaction",
    description="Deletes transaction record only if owned by the authenticated user.",
)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    tx = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or you do not have permission to delete it.",
        )

    db.delete(tx)
    db.commit()
    return {"message": "Transaction deleted successfully", "id": transaction_id}
