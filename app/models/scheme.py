from datetime import date
from typing import Any
from sqlalchemy import ARRAY, Date, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Scheme(Base):
    __tablename__ = "schemes"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    title_en: Mapped[str] = mapped_column(String, nullable=False)
    title_kn: Mapped[str | None] = mapped_column(String, nullable=True)
    title_hi: Mapped[str | None] = mapped_column(String, nullable=True)
    agency: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, default="Welfare", nullable=False)
    summary: Mapped[str] = mapped_column(String, nullable=False)
    benefits: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    documents_required: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    application_steps: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    last_verified_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    rule: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
