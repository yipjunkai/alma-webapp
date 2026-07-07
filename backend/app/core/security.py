"""JWT session tokens and constant-time credential checks."""

import secrets
from datetime import UTC, datetime, timedelta

import jwt

JWT_ALGORITHM = "HS256"
SESSION_COOKIE_NAME = "alma_session"
SESSION_TTL = timedelta(hours=8)


def _encode_utf8(value: str) -> bytes:
    """UTF-8 encode a string for byte comparison.

    ``surrogatepass`` keeps a hostile input containing lone surrogates — which can
    reach us as JSON ``\\uXXXX`` escapes and are never valid credentials — from
    raising ``UnicodeEncodeError``. The comparison stays constant-time and just
    fails to match, so a crafted login gets a clean 401 rather than a 500.
    """
    return value.encode("utf-8", "surrogatepass")


def create_access_token(subject: str, secret_key: str, ttl: timedelta = SESSION_TTL) -> str:
    now = datetime.now(UTC)
    payload = {"sub": subject, "iat": now, "exp": now + ttl}
    # PyJWT's key param union includes an untyped cryptography type; our usage is str.
    return jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)  # pyright: ignore[reportUnknownMemberType]


def decode_access_token(token: str, secret_key: str) -> str | None:
    """Return the token subject, or None if the token is invalid or expired."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])  # pyright: ignore[reportUnknownMemberType]
    except (jwt.PyJWTError, UnicodeError):
        # Invalid/expired, or not UTF-8-encodable (lone surrogates): not a session.
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None


def verify_credentials(
    email: str, password: str, expected_email: str, expected_password: str
) -> bool:
    """Compare submitted credentials against the configured admin user in constant time."""
    email_ok = secrets.compare_digest(_encode_utf8(email), _encode_utf8(expected_email))
    password_ok = secrets.compare_digest(_encode_utf8(password), _encode_utf8(expected_password))
    return bool(email_ok & password_ok)
