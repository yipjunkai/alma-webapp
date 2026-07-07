"""SQLAlchemy ORM models."""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class LeadState(enum.StrEnum):
    PENDING = "PENDING"
    REACHED_OUT = "REACHED_OUT"


def utcnow() -> datetime:
    return datetime.now(UTC)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    state: Mapped[LeadState] = mapped_column(
        Enum(LeadState, name="lead_state"), nullable=False, default=LeadState.PENDING
    )
    resume_stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    resume_original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    @property
    def resume_filename(self) -> str:
        """Original upload filename, exposed under the public API field name."""
        return self.resume_original_name
