import uuid
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        CheckConstraint("role IN ('student', 'faculty', 'college_admin', 'admin')", name="chk_user_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="student", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint("age >= 0 AND age <= 120", name="chk_profile_age"),
        CheckConstraint("gender IN ('male', 'female', 'other', 'prefer_not_to_say')", name="chk_profile_gender"),
        CheckConstraint("social_category IN ('GEN', 'OBC', 'SC', 'ST', 'EWS')", name="chk_profile_social_cat"),
        CheckConstraint("ration_card_type IN ('BPL', 'APL', 'AAY', 'None')", name="chk_profile_ration_card"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String, default="Karnataka", nullable=False)
    district: Mapped[str | None] = mapped_column(String, nullable=True)
    is_student: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    academic_year: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    annual_family_income_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    social_category: Mapped[str] = mapped_column(String, default="GEN", nullable=False)
    has_bank_account: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_disability: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ration_card_type: Mapped[str] = mapped_column(String, default="None", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
