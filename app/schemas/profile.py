import datetime as dt
import uuid
from typing import Literal
from pydantic import BaseModel, Field


class UserProfileIn(BaseModel):
    age: int | None = Field(default=None, ge=0, le=120)
    gender: Literal["male", "female", "other", "prefer_not_to_say"] | None = "prefer_not_to_say"
    state: str = Field(default="Karnataka", max_length=50)
    district: str | None = Field(default=None, max_length=50)
    is_student: bool = True
    academic_year: str | None = Field(default=None, max_length=20)
    department: str | None = Field(default=None, max_length=50)
    annual_family_income_minor: int = Field(default=0, ge=0, description="Annual income in paise")
    social_category: Literal["GEN", "OBC", "SC", "ST", "EWS"] = "GEN"
    has_bank_account: bool = True
    has_disability: bool = False
    ration_card_type: Literal["BPL", "APL", "AAY", "None"] = "None"


class UserProfileOut(UserProfileIn):
    id: uuid.UUID
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    updated_at: dt.datetime

