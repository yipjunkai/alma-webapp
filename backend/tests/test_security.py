"""Unit tests for JWT session tokens and credential checks (no app/DB needed)."""

from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_access_token,
    verify_credentials,
)

SECRET = "unit-test-secret-key-abcdefghijklmnop"  # >= 32 chars
OTHER_SECRET = "a-different-secret-key-0123456789abcd"


def test_token_round_trip_returns_subject() -> None:
    token = create_access_token("attorney@example.com", SECRET)
    assert decode_access_token(token, SECRET) == "attorney@example.com"


def test_expired_token_is_rejected() -> None:
    token = create_access_token("x@y.z", SECRET, ttl=timedelta(seconds=-1))
    assert decode_access_token(token, SECRET) is None


def test_token_signed_with_a_different_key_is_rejected() -> None:
    token = create_access_token("x@y.z", SECRET)
    assert decode_access_token(token, OTHER_SECRET) is None


def test_tampered_token_is_rejected() -> None:
    token = create_access_token("x@y.z", SECRET)
    tampered = token[:-3] + ("bbb" if token.endswith("aaa") else "aaa")
    assert decode_access_token(tampered, SECRET) is None


def test_garbage_token_is_rejected() -> None:
    assert decode_access_token("not-a-jwt", SECRET) is None


def test_verify_credentials_accepts_exact_match() -> None:
    assert verify_credentials("a@b.co", "pw", "a@b.co", "pw") is True


def test_verify_credentials_rejects_wrong_password() -> None:
    assert verify_credentials("a@b.co", "nope", "a@b.co", "pw") is False


def test_verify_credentials_rejects_wrong_email() -> None:
    assert verify_credentials("x@b.co", "pw", "a@b.co", "pw") is False
