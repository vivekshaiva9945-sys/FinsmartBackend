import datetime as dt
import uuid
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Minimum 8 characters")
    full_name: str = Field(min_length=2, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)
    role: str = Field(default="student", pattern="^(student|faculty|college_admin|admin)$")
    consent_data_processing: bool = Field(description="Explicit consent for processing financial records (DPDP Act 2023)")
    honeypot: str | None = Field(default=None, description="Spam bot trap - must remain empty")


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    honeypot: str | None = Field(default=None, description="Spam bot trap - must remain empty")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str
    full_name: str
    email: str


class UserOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    full_name: str
    phone_number: str | None
    role: str
    is_active: bool
    created_at: dt.datetime

