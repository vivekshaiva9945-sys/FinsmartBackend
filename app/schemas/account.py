import datetime as dt
import uuid
from typing import Literal
from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, example="Canara Bank Student Account")
    account_type: Literal["BANK", "CASH", "WALLET", "SAVINGS"] = "BANK"
    initial_balance_minor: int = Field(default=0, ge=0, description="Initial balance in paise")


class AccountOut(BaseModel):
    id: uuid.UUID
    name: str
    account_type: str
    balance_minor: int
    currency: str
    is_active: bool
    created_at: dt.datetime

