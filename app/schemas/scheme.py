import datetime as dt
from typing import Any, Literal
from pydantic import BaseModel, Field


class SchemeOut(BaseModel):
    code: str
    title_en: str
    title_kn: str | None
    title_hi: str | None
    agency: str
    category: str
    summary: str
    benefits: str
    source_url: str
    documents_required: list[str]
    application_steps: list[str]
    last_verified_at: dt.date | None


class SchemeEvaluationResult(SchemeOut):
    eligible: bool
    reasons: list[str]
    matched_conditions: int
    total_conditions: int


class ProfileEvaluationRequest(BaseModel):
    age: int | None = Field(default=None, ge=0, le=120)
    gender: str | None = None
    state: str = Field(default="Karnataka")
    district: str | None = None
    is_student: bool | None = None
    annual_family_income: int | None = Field(default=None, ge=0, description="Rupees per year (e.g. 200000)")
    social_category: Literal["GEN", "OBC", "SC", "ST", "EWS"] | None = None
    has_bank_account: bool | None = None
    has_disability: bool | None = None
    ration_card_type: Literal["BPL", "APL", "AAY", "None"] | None = None

