"""Email composition and delivery services."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC
from typing import Annotated, Protocol

import resend
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.models import Lead

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str


class EmailService(Protocol):
    def send(self, message: EmailMessage) -> None: ...


class ConsoleEmailService:
    """Logs emails instead of sending them (used when RESEND_API_KEY is unset)."""

    def __init__(self, sender: str) -> None:
        self.sender = sender

    def send(self, message: EmailMessage) -> None:
        logger.info(
            "Console email (not sent)\nFrom: %s\nTo: %s\nSubject: %s\n\n%s",
            self.sender,
            message.to,
            message.subject,
            message.text,
        )


class ResendEmailService:
    """Sends emails through the Resend API."""

    def __init__(self, api_key: str, sender: str) -> None:
        self.api_key = api_key
        self.sender = sender

    def send(self, message: EmailMessage) -> None:
        resend.api_key = self.api_key
        resend.Emails.send(
            {
                "from": self.sender,
                "to": [message.to],
                "subject": message.subject,
                "text": message.text,
            }
        )


def get_email_service(settings: Annotated[Settings, Depends(get_settings)]) -> EmailService:
    """Pick the delivery backend based on configuration (tests override this dependency)."""
    if settings.resend_api_key:
        return ResendEmailService(api_key=settings.resend_api_key, sender=settings.email_from)
    return ConsoleEmailService(sender=settings.email_from)


EmailServiceDep = Annotated[EmailService, Depends(get_email_service)]


def compose_lead_emails(
    lead: Lead, attorney_email: str, admin_leads_url: str
) -> tuple[EmailMessage, EmailMessage]:
    """Build the prospect confirmation and the attorney notification for a new lead."""
    # SQLite returns naive datetimes; stored timestamps are UTC — label them so.
    created = lead.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    submitted = created.astimezone(UTC).strftime("%b %d, %Y %H:%M UTC")
    prospect = EmailMessage(
        to=lead.email,
        subject="We received your information - Alma",
        text=(
            f"Hi {lead.first_name},\n\n"
            "Thanks for reaching out to Alma. We received your information and your resume "
            f"({lead.resume_original_name}).\n\n"
            "An attorney will review your submission and follow up with you soon.\n\n"
            "- The Alma Team"
        ),
    )
    attorney = EmailMessage(
        to=attorney_email,
        subject=f"New lead: {lead.first_name} {lead.last_name}",
        text=(
            "A new lead was submitted.\n\n"
            f"Name: {lead.first_name} {lead.last_name}\n"
            f"Email: {lead.email}\n"
            f"Resume: {lead.resume_original_name}\n"
            f"State: {lead.state.value}\n"
            f"Submitted: {submitted}\n\n"
            f"Review leads: {admin_leads_url}"
        ),
    )
    return prospect, attorney


def send_email_messages(service: EmailService, messages: Sequence[EmailMessage]) -> None:
    """Send messages, logging (never raising) on failure — email must not break requests."""
    for message in messages:
        try:
            service.send(message)
        except Exception:
            logger.exception("Failed to send email to %s (subject=%r)", message.to, message.subject)
