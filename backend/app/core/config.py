"""Application settings loaded from environment variables (and backend/.env)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/alma.db"
    secret_key: str = "dev-secret-change-me"
    admin_email: str = "attorney@example.com"
    admin_password: str = "changeme"
    attorney_email: str = "attorney@example.com"
    email_from: str = "Alma <onboarding@resend.dev>"
    resend_api_key: str = ""
    upload_dir: Path = Path("./data/uploads")


@lru_cache
def get_settings() -> Settings:
    return Settings()
