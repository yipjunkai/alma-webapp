"""Pydantic request/response schemas — the public API contract."""

import re
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator

from app.models import LeadState

# C0/C7 control characters (incl. CR/LF/TAB) — stripped from names so they can't
# forge multi-line email subjects or inject into log lines.
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


class HealthOut(BaseModel):
    status: str = "ok"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    email: str


class LeadCreate(BaseModel):
    """Fields submitted by the public lead form (multipart/form-data)."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def _clean_name(cls, value: object) -> object:
        # Strip control characters, then trim; a name that was only control
        # chars/whitespace collapses to "" and fails the min_length check.
        return _CONTROL_CHARS.sub("", value).strip() if isinstance(value, str) else value


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str
    email: str
    state: LeadState
    resume_filename: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _serialize_utc(self, value: datetime) -> str:
        """SQLite returns naive datetimes; all stored timestamps are UTC."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class LeadListOut(BaseModel):
    items: list[LeadOut]
    total: int


class LeadStateUpdate(BaseModel):
    state: LeadState
