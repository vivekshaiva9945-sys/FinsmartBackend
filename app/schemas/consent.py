import datetime as dt
import uuid
from typing import Any
from pydantic import BaseModel, Field


class ConsentUpdate(BaseModel):
    purpose: str = Field(min_length=3, max_length=50, example="scheme_eligibility")
    granted: bool


class ConsentOut(BaseModel):
    id: uuid.UUID
    purpose: str
    granted: bool
    at: dt.datetime


class DSARDataExport(BaseModel):
    user: dict[str, Any]
    profile: dict[str, Any] | None
    accounts: list[dict[str, Any]]
    transactions: list[dict[str, Any]]
    budgets: list[dict[str, Any]]
    goals: list[dict[str, Any]]
    consents: list[dict[str, Any]]
    exported_at: dt.datetime

