from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ------------------------------------------------------------------------------
# Authentication & User Schemas
# ------------------------------------------------------------------------------

class UserCreate(BaseModel):
    """Schema for registering a new user."""
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="Valid unique email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters with letters and numbers",
    )
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one numeric digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        return v

    @model_validator(mode="after")
    def verify_passwords_match(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    """Schema for authenticating a user."""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Public user profile (Never exposes password_hash)."""
    id: int
    full_name: str
    email: str
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    """Schema for changing account password."""
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters with letters and numbers",
    )
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one numeric digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        return v

    @model_validator(mode="after")
    def verify_passwords_match(self) -> "PasswordChangeRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("New passwords do not match")
        return self


class EmailChangeRequest(BaseModel):
    """Schema for changing account email address."""
    new_email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ProfileUpdateRequest(BaseModel):
    """Schema for updating user name or avatar URL."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)


class TokenResponse(BaseModel):
    """JWT Access Token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ------------------------------------------------------------------------------
# Transaction Schemas
# ------------------------------------------------------------------------------

TransactionType = Literal["income", "expense"]

DEFAULT_EXPENSE_CATEGORIES = [
    "Food",
    "Transport",
    "Education",
    "Accommodation",
    "Shopping",
    "Healthcare",
    "Bills",
    "Entertainment",
    "Other",
]

DEFAULT_INCOME_CATEGORIES = [
    "Salary",
    "Allowance",
    "Freelancing",
    "Business",
    "Other",
]


class TransactionBase(BaseModel):
    transaction_date: date = Field(default_factory=date.today)
    transaction_type: TransactionType
    amount: Decimal = Field(..., gt=0, decimal_places=2, max_digits=12, description="Amount must be positive")
    category: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    payment_method: str = Field("Cash", min_length=1, max_length=50)


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    pass


class TransactionUpdate(BaseModel):
    """Schema for updating an existing transaction (partial updates allowed)."""
    transaction_date: Optional[date] = None
    transaction_type: Optional[TransactionType] = None
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2, max_digits=12)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    payment_method: Optional[str] = Field(None, min_length=1, max_length=50)


class TransactionResponse(TransactionBase):
    """Schema for returning transaction details."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ------------------------------------------------------------------------------
# Budget Schemas
# ------------------------------------------------------------------------------

class BudgetCreate(BaseModel):
    """Schema for creating or updating a monthly budget."""
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)
    amount: Decimal = Field(..., gt=0, decimal_places=2, max_digits=12)


class BudgetResponse(BaseModel):
    """Schema for returning budget details."""
    id: int
    user_id: int
    year: int
    month: int
    amount: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetStatusResponse(BaseModel):
    """Authoritative budget status calculated by backend."""
    year: int
    month: int
    budget_amount: Decimal
    expense_total: Decimal
    remaining_budget: Decimal
    usage_percentage: Decimal
    status: Literal["normal", "warning", "over_budget"]


# ------------------------------------------------------------------------------
# Dashboard & Report Schemas
# ------------------------------------------------------------------------------

class CategoryExpense(BaseModel):
    category: str
    amount: Decimal
    percentage: Decimal


class MonthlyReportResponse(BaseModel):
    """Monthly financial breakdown and category distributions."""
    year: int
    month: int
    total_income: Decimal
    total_expenses: Decimal
    remaining_balance: Decimal
    savings_rate: Decimal
    category_expenses: List[CategoryExpense]


class DashboardSummaryResponse(BaseModel):
    """Dashboard primary summary card metrics."""
    year: int
    month: int
    monthly_income: Decimal
    monthly_expenses: Decimal
    remaining_balance: Decimal
    savings_rate: Decimal
    budget_status: Optional[BudgetStatusResponse] = None
    recent_transactions: List[TransactionResponse] = []
