from conftest import ATTORNEY_EMAIL, CapturingEmailService, submit_lead
from fastapi.testclient import TestClient


def test_lead_submission_sends_prospect_and_attorney_emails(
    client: TestClient, email_service: CapturingEmailService
) -> None:
    response = submit_lead(client, first_name="Sam", email="prospect@example.com")
    assert response.status_code == 201

    assert len(email_service.sent) == 2
    by_recipient = {message.to: message for message in email_service.sent}
    assert set(by_recipient) == {"prospect@example.com", ATTORNEY_EMAIL}

    prospect = by_recipient["prospect@example.com"]
    assert "received" in prospect.subject.lower()
    assert "Sam" in prospect.text

    attorney = by_recipient[ATTORNEY_EMAIL]
    assert "new lead" in attorney.subject.lower()
    assert "prospect@example.com" in attorney.text
    assert "resume.pdf" in attorney.text
    assert "http://localhost:3000/admin/leads" in attorney.text


def test_email_failure_does_not_fail_request(
    client: TestClient, email_service: CapturingEmailService
) -> None:
    email_service.fail = True
    response = submit_lead(client, email="unlucky@example.com")
    assert response.status_code == 201
    assert email_service.sent == []

    # The lead was still persisted despite the email failure.
    body = response.json()
    assert body["email"] == "unlucky@example.com"
    assert body["state"] == "PENDING"
