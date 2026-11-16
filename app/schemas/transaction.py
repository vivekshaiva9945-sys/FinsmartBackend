import datetime as dt
import uuid
from typing import Literal
from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    client_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Client-side UUID for idempotency")
    account_id: uuid.UUID | None = None
    amount_minor: int = Field(gt=0, lt=10**13, description="Amount in integer paise (e.g. ₹50.00 = 5000)")
    kind: Literal["DEBIT", "CREDIT"]
    category: str = Field(min_length=1, max_length=50)
    payment_mode: Literal["CASH", "UPI", "CARD", "BANK", "WALLET"] = "UPI"
    description: str = Field(default="", max_length=200)
    occurred_on: dt.date = Field(default_factory=dt.date.today)


class TransactionOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID | None
    client_id: uuid.UUID
    amount_minor: int
    currency: str
    kind: str
    category: str
    payment_mode: str
    description: str
    occurred_on: dt.date
    created_at: dt.datetime


class CategoryBreakdown(BaseModel):
    category: str
    kind: str
    total_minor: int
    count: int
    percentage: float


class MonthlySummaryOut(BaseModel):
    month: str
    income_minor: int
    expense_minor: int
    balance_minor: int
    savings_rate_pct: float
    by_category: list[CategoryBreakdown]

