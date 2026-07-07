"""Unit tests for the SECRET_KEY hardening in Settings."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _settings(**overrides: str) -> Settings:
    """Build Settings while ignoring any real .env file, so the test is hermetic.

    pydantic-settings accepts the documented ``_env_file`` init arg but omits it
    from its typed signature, hence the scoped ignore.
    """
    return Settings(_env_file=None, **overrides)  # pyright: ignore[reportCallIssue]


def test_rejects_placeholder_secret() -> None:
    with pytest.raises(ValidationError):
        _settings(secret_key="dev-secret-change-me")


def test_rejects_short_secret() -> None:
    with pytest.raises(ValidationError):
        _settings(secret_key="too-short")


def test_accepts_strong_explicit_secret() -> None:
    settings = _settings(secret_key="k" * 32)
    assert settings.secret_key == "k" * 32


def test_ephemeral_default_is_strong_and_unique(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    first = _settings()
    second = _settings()
    assert len(first.secret_key) >= 32
    # Each instance gets an independent random key — nothing to forge from.
    assert first.secret_key != second.secret_key
