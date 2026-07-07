"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import SESSION_COOKIE_NAME, decode_access_token
from app.db import get_db

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_db)]


def get_current_user(
    settings: SettingsDep,
    alma_session: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> str:
    """Resolve the authenticated user's email from the session cookie, or raise 401."""
    if alma_session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    subject = decode_access_token(alma_session, settings.secret_key)
    if subject is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return subject


CurrentUser = Annotated[str, Depends(get_current_user)]
