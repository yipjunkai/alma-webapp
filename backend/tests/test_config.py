"""Unit tests for the SECRET_KEY hardening in Settings."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_rejects_placeholder_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, secret_key="dev-secret-change-me")


def test_rejects_short_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, secret_key="too-short")


def test_accepts_strong_explicit_secret() -> None:
    settings = Settings(_env_file=None, secret_key="k" * 32)
    assert settings.secret_key == "k" * 32


def test_ephemeral_default_is_strong_and_unique(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    first = Settings(_env_file=None)
    second = Settings(_env_file=None)
    assert len(first.secret_key) >= 32
    # Each process/instance gets an independent random key — nothing to forge from.
    assert first.secret_key != second.secret_key
