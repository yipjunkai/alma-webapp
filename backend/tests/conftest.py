"""Shared pytest fixtures: isolated settings/db/uploads and captured emails."""

import io
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db import Base, get_engine, get_sessionmaker
from app.main import create_app
from app.services.email import EmailMessage, get_email_service

ADMIN_EMAIL = "attorney@test.com"
ADMIN_PASSWORD = "test-password"
ATTORNEY_EMAIL = "notify@test.com"

MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"%%EOF\n"
)


class CapturingEmailService:
    """Test double that records sent emails; set ``fail=True`` to simulate failures."""

    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []
        self.fail = False

    def send(self, message: EmailMessage) -> None:
        if self.fail:
            raise RuntimeError("simulated email failure")
        self.sent.append(message)


def _clear_caches() -> None:
    get_sessionmaker.cache_clear()
    get_engine.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def email_service() -> CapturingEmailService:
    return CapturingEmailService()


@pytest.fixture
def app(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, email_service: CapturingEmailService
) -> Iterator[FastAPI]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-0123456789abcdef-0123456789abcdef")
    monkeypatch.setenv("ADMIN_EMAIL", ADMIN_EMAIL)
    monkeypatch.setenv("ADMIN_PASSWORD", ADMIN_PASSWORD)
    monkeypatch.setenv("ATTORNEY_EMAIL", ATTORNEY_EMAIL)
    monkeypatch.setenv("RESEND_API_KEY", "")
    _clear_caches()
    application = create_app()
    Base.metadata.create_all(get_engine())
    application.dependency_overrides[get_email_service] = lambda: email_service
    yield application
    get_engine().dispose()
    _clear_caches()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200
    return client


def submit_lead(
    client: TestClient,
    first_name: str = "Jane",
    last_name: str = "Doe",
    email: str = "jane.doe@example.com",
    filename: str = "resume.pdf",
    content: bytes = MINIMAL_PDF,
) -> httpx.Response:
    """POST a lead through the public multipart form endpoint."""
    return client.post(
        "/api/leads",
        data={"first_name": first_name, "last_name": last_name, "email": email},
        files={"resume": (filename, io.BytesIO(content), "application/pdf")},
    )
