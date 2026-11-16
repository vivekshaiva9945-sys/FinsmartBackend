import datetime as dt
import uuid
from typing import Literal
from pydantic import BaseModel, Field


class BudgetCreate(BaseModel):
    category: str = Field(min_length=1, max_length=50)
    limit_minor: int = Field(gt=0, description="Monthly limit in paise")
    period: Literal["MONTHLY", "SEMESTER", "YEARLY"] = "MONTHLY"


class BudgetOut(BaseModel):
    id: uuid.UUID
    category: str
    limit_minor: int
    period: str
    created_at: dt.datetime


class BudgetStatusOut(BaseModel):
    category: str
    limit_minor: int
    spent_minor: int
    remaining_minor: int
    percent: int
    level: Literal["ok", "warning", "over"]
    period: str

