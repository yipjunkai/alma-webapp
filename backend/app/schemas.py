"""Pydantic request/response schemas — the public API contract."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator

from app.models import LeadState


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
    def _strip_whitespace(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


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
