import datetime as dt
import uuid
from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_minor: int = Field(gt=0, description="Target savings amount in paise")
    target_date: dt.date | None = None
    category: str = Field(default="General", max_length=50)


class GoalContribute(BaseModel):
    amount_minor: int = Field(gt=0, description="Deposit contribution in paise")


class GoalOut(BaseModel):
    id: uuid.UUID
    name: str
    target_minor: int
    saved_minor: int
    remaining_minor: int
    percent: int
    target_date: dt.date | None
    category: str
    is_completed: bool
    monthly_recommended_minor: int | None
    created_at: dt.datetime

