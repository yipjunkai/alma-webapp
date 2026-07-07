"""JWT session tokens and constant-time credential checks."""

import secrets
from datetime import UTC, datetime, timedelta

import jwt

JWT_ALGORITHM = "HS256"
SESSION_COOKIE_NAME = "alma_session"
SESSION_TTL = timedelta(hours=8)


def create_access_token(subject: str, secret_key: str, ttl: timedelta = SESSION_TTL) -> str:
    now = datetime.now(UTC)
    payload = {"sub": subject, "iat": now, "exp": now + ttl}
    # PyJWT's key param union includes an untyped cryptography type; our usage is str.
    return jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)  # pyright: ignore[reportUnknownMemberType]


def decode_access_token(token: str, secret_key: str) -> str | None:
    """Return the token subject, or None if the token is invalid or expired."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])  # pyright: ignore[reportUnknownMemberType]
    except jwt.PyJWTError:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None


def verify_credentials(
    email: str, password: str, expected_email: str, expected_password: str
) -> bool:
    """Compare submitted credentials against the configured admin user in constant time."""
    email_ok = secrets.compare_digest(email.encode(), expected_email.encode())
    password_ok = secrets.compare_digest(password.encode(), expected_password.encode())
    return bool(email_ok & password_ok)
