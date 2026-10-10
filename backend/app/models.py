from datetime import datetime, timezone, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now() -> datetime:
    """Helper to return current UTC datetime."""
    return datetime.now(timezone.utc)


class User(Base):
    """User database model representing registered application accounts."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships (cascade delete removes transactions & budgets when user is deleted)
    transactions = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    budgets = relationship(
        "Budget",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class Transaction(Base):
    """Financial transaction model (income and expense records)."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_date = Column(Date, nullable=False, default=date.today, index=True)
    transaction_type = Column(String(20), nullable=False)  # 'income' or 'expense'
    amount = Column(Numeric(12, 2), nullable=False)  # Fixed 2-decimal precision
    category = Column(String(50), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    payment_method = Column(String(50), nullable=False, default="Cash")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_user_type", "user_id", "transaction_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} user_id={self.user_id} "
            f"type={self.transaction_type} amount={self.amount}>"
        )


class Budget(Base):
    """Monthly spending budget model per user."""

    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="budgets")

    __table_args__ = (
        UniqueConstraint("user_id", "year", "month", name="uq_user_year_month_budget"),
        Index("ix_budgets_user_year_month", "user_id", "year", "month"),
    )

    def __repr__(self) -> str:
        return (
            f"<Budget id={self.id} user_id={self.user_id} "
            f"year={self.year} month={self.month} amount={self.amount}>"
        )
