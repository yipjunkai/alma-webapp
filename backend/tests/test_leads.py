import uuid

from conftest import MINIMAL_PDF, CapturingEmailService, submit_lead
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db import get_sessionmaker
from app.models import Lead


def test_create_lead_happy_path(client: TestClient, email_service: CapturingEmailService) -> None:
    response = submit_lead(client)
    assert response.status_code == 201
    body = response.json()

    assert uuid.UUID(body["id"])
    assert body["first_name"] == "Jane"
    assert body["last_name"] == "Doe"
    assert body["email"] == "jane.doe@example.com"
    assert body["state"] == "PENDING"
    assert body["resume_filename"] == "resume.pdf"
    assert body["created_at"].endswith("Z")
    assert body["updated_at"].endswith("Z")

    # Row persisted.
    session = get_sessionmaker()()
    try:
        lead = session.get(Lead, body["id"])
        assert lead is not None
        stored_name = lead.resume_stored_name
    finally:
        session.close()

    # Resume file written to the upload dir under its stored (uuid) name.
    stored_path = get_settings().upload_dir / stored_name
    assert stored_path.read_bytes() == MINIMAL_PDF

    # Exactly two emails captured (prospect confirmation + attorney notification).
    assert len(email_service.sent) == 2


def test_create_lead_trims_names(client: TestClient) -> None:
    response = submit_lead(client, first_name="  Ada  ", last_name="  Lovelace ")
    assert response.status_code == 201
    body = response.json()
    assert body["first_name"] == "Ada"
    assert body["last_name"] == "Lovelace"


def test_create_lead_invalid_email(client: TestClient) -> None:
    response = submit_lead(client, email="not-an-email")
    assert response.status_code == 422


def test_create_lead_blank_first_name(client: TestClient) -> None:
    response = submit_lead(client, first_name="   ")
    assert response.status_code == 422


def test_create_lead_name_too_long(client: TestClient) -> None:
    response = submit_lead(client, first_name="x" * 101)
    assert response.status_code == 422


def test_create_lead_missing_fields(client: TestClient) -> None:
    response = client.post("/api/leads", data={"first_name": "Jane"})
    assert response.status_code == 422


def test_create_lead_disallowed_extension(client: TestClient) -> None:
    response = submit_lead(client, filename="malware.exe", content=b"MZ")
    assert response.status_code == 422
    detail = response.json()["detail"]
    # File errors share the field-scoped 422 shape used for the text fields.
    assert any(part["loc"][-1] == "resume" for part in detail)
    assert any(".pdf" in part["msg"] for part in detail)


def test_create_lead_file_too_large(client: TestClient) -> None:
    oversized = b"x" * (5 * 1024 * 1024 + 1)
    response = submit_lead(client, content=oversized)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(part["loc"][-1] == "resume" for part in detail)
    assert any("5 MB" in part["msg"] for part in detail)


def test_create_lead_empty_file(client: TestClient) -> None:
    response = submit_lead(client, content=b"")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(part["loc"][-1] == "resume" for part in detail)
    assert any("empty" in part["msg"].lower() for part in detail)


def test_create_lead_strips_control_characters_from_names(client: TestClient) -> None:
    response = submit_lead(client, first_name="Ev\r\nil", last_name="Do\te")
    assert response.status_code == 201
    body = response.json()
    assert body["first_name"] == "Evil"
    assert body["last_name"] == "Doe"


def test_list_leads_requires_auth(client: TestClient) -> None:
    response = client.get("/api/leads")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_list_leads_sorted_created_at_desc(auth_client: TestClient) -> None:
    emails = [f"lead{i}@example.com" for i in range(3)]
    for email in emails:
        assert submit_lead(auth_client, email=email).status_code == 201

    response = auth_client.get("/api/leads")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert [item["email"] for item in body["items"]] == list(reversed(emails))
    created = [item["created_at"] for item in body["items"]]
    assert created == sorted(created, reverse=True)


def test_list_leads_state_filter(auth_client: TestClient) -> None:
    pending_id = submit_lead(auth_client, email="pending@example.com").json()["id"]
    reached_id = submit_lead(auth_client, email="reached@example.com").json()["id"]
    patch = auth_client.patch(f"/api/leads/{reached_id}", json={"state": "REACHED_OUT"})
    assert patch.status_code == 200

    pending = auth_client.get("/api/leads", params={"state": "PENDING"}).json()
    assert pending["total"] == 1
    assert [item["id"] for item in pending["items"]] == [pending_id]

    reached = auth_client.get("/api/leads", params={"state": "REACHED_OUT"}).json()
    assert reached["total"] == 1
    assert [item["id"] for item in reached["items"]] == [reached_id]


def test_patch_requires_auth(client: TestClient) -> None:
    lead_id = submit_lead(client).json()["id"]
    response = client.patch(f"/api/leads/{lead_id}", json={"state": "REACHED_OUT"})
    assert response.status_code == 401


def test_patch_pending_to_reached_out(auth_client: TestClient) -> None:
    lead_id = submit_lead(auth_client).json()["id"]
    response = auth_client.patch(f"/api/leads/{lead_id}", json={"state": "REACHED_OUT"})
    assert response.status_code == 200
    assert response.json()["state"] == "REACHED_OUT"


def test_patch_same_state_is_idempotent(auth_client: TestClient) -> None:
    lead_id = submit_lead(auth_client).json()["id"]
    first = auth_client.patch(f"/api/leads/{lead_id}", json={"state": "REACHED_OUT"})
    second = auth_client.patch(f"/api/leads/{lead_id}", json={"state": "REACHED_OUT"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["state"] == "REACHED_OUT"

    # PENDING -> PENDING is also an idempotent no-op.
    pending_id = submit_lead(auth_client, email="still.pending@example.com").json()["id"]
    noop = auth_client.patch(f"/api/leads/{pending_id}", json={"state": "PENDING"})
    assert noop.status_code == 200
    assert noop.json()["state"] == "PENDING"


def test_patch_reached_out_to_pending_conflict(auth_client: TestClient) -> None:
    lead_id = submit_lead(auth_client).json()["id"]
    reached = auth_client.patch(f"/api/leads/{lead_id}", json={"state": "REACHED_OUT"})
    assert reached.status_code == 200
    response = auth_client.patch(f"/api/leads/{lead_id}", json={"state": "PENDING"})
    assert response.status_code == 409


def test_patch_unknown_id_returns_404(auth_client: TestClient) -> None:
    response = auth_client.patch(f"/api/leads/{uuid.uuid4()}", json={"state": "REACHED_OUT"})
    assert response.status_code == 404


def test_patch_invalid_state_value(auth_client: TestClient) -> None:
    lead_id = submit_lead(auth_client).json()["id"]
    response = auth_client.patch(f"/api/leads/{lead_id}", json={"state": "ARCHIVED"})
    assert response.status_code == 422


def test_resume_requires_auth(client: TestClient) -> None:
    lead_id = submit_lead(client).json()["id"]
    response = client.get(f"/api/leads/{lead_id}/resume")
    assert response.status_code == 401


def test_resume_download_streams_original_filename(auth_client: TestClient) -> None:
    content = b"%PDF-1.4 resume bytes %%EOF"
    lead_id = submit_lead(auth_client, filename="jane resume.pdf", content=content).json()["id"]
    response = auth_client.get(f"/api/leads/{lead_id}/resume")
    assert response.status_code == 200
    assert response.content == content
    disposition = response.headers["content-disposition"]
    assert "attachment" in disposition
    assert "jane resume.pdf" in disposition or "jane%20resume.pdf" in disposition


def test_resume_unknown_lead_returns_404(auth_client: TestClient) -> None:
    response = auth_client.get(f"/api/leads/{uuid.uuid4()}/resume")
    assert response.status_code == 404


def test_resume_missing_file_returns_404(auth_client: TestClient) -> None:
    # The row exists but the stored file was lost — download must 404, not 500.
    lead_id = submit_lead(auth_client).json()["id"]
    for stored in get_settings().upload_dir.iterdir():
        stored.unlink()
    response = auth_client.get(f"/api/leads/{lead_id}/resume")
    assert response.status_code == 404


def test_request_over_hard_body_limit_returns_413(client: TestClient) -> None:
    # The coarse body-size guard rejects >10 MB before the multipart parse.
    huge = b"x" * (10 * 1024 * 1024 + 1)
    response = submit_lead(client, content=huge)
    assert response.status_code == 413
