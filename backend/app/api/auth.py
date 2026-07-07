"""Authentication endpoints: login / logout / me."""

from fastapi import APIRouter, HTTPException, Response

from app.api.deps import CurrentUser, SettingsDep
from app.core.security import (
    SESSION_COOKIE_NAME,
    SESSION_TTL,
    create_access_token,
    verify_credentials,
)
from app.schemas import LoginRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, response: Response, settings: SettingsDep) -> UserOut:
    if not verify_credentials(
        payload.email, payload.password, settings.admin_email, settings.admin_password
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(settings.admin_email, settings.secret_key)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
        httponly=True,
        samesite="lax",
    )
    return UserOut(email=settings.admin_email)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


@router.get("/me")
def me(user: CurrentUser) -> UserOut:
    return UserOut(email=user)
