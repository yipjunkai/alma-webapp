"""Application settings loaded from environment variables (and backend/.env)."""

import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Placeholder/weak values that must never be accepted as a real signing key.
_INSECURE_SECRETS = {"", "dev-secret-change-me", "changeme", "secret"}
_MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/alma.db"
    # No usable signing key is ever committed: when SECRET_KEY is unset the app
    # generates a strong ephemeral key per process, so repo contents can't forge
    # sessions. Set SECRET_KEY in the environment to keep sessions valid across
    # restarts — required in production (see the validator below).
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(_MIN_SECRET_LENGTH))
    admin_email: str = "attorney@example.com"
    admin_password: str = "changeme"
    attorney_email: str = "attorney@example.com"
    email_from: str = "Alma <onboarding@resend.dev>"
    resend_api_key: str = ""
    upload_dir: Path = Path("./data/uploads")
    frontend_origin: str = "http://localhost:3000"

    @field_validator("secret_key")
    @classmethod
    def _reject_insecure_secret(cls, value: str) -> str:
        """Reject an explicitly-configured weak key (the generated default is always strong)."""
        if value in _INSECURE_SECRETS or len(value) < _MIN_SECRET_LENGTH:
            raise ValueError(
                f"SECRET_KEY must be at least {_MIN_SECRET_LENGTH} characters and not a "
                "placeholder. Generate one with: "
                'python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
