"""Lead business logic: create, list, and state transitions."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lead, LeadState


class LeadNotFoundError(Exception):
    """No lead exists with the given id."""


class InvalidTransitionError(Exception):
    """The requested state transition is not allowed."""


def create_lead(
    db: Session,
    *,
    first_name: str,
    last_name: str,
    email: str,
    resume_stored_name: str,
    resume_original_name: str,
) -> Lead:
    lead = Lead(
        first_name=first_name,
        last_name=last_name,
        email=email,
        state=LeadState.PENDING,
        resume_stored_name=resume_stored_name,
        resume_original_name=resume_original_name,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def find_recent_by_email(db: Session, email: str, window_seconds: int) -> Lead | None:
    """Return the most recent lead for ``email`` if created within the window.

    Makes the public create endpoint idempotent for accidental duplicate
    submissions. The window check runs in Python to avoid SQLite naive/aware
    datetime comparison quirks.
    """
    if window_seconds <= 0:
        return None
    stmt = select(Lead).where(Lead.email == email).order_by(Lead.created_at.desc()).limit(1)
    lead = db.scalars(stmt).first()
    if lead is None:
        return None
    created = lead.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    if datetime.now(UTC) - created <= timedelta(seconds=window_seconds):
        return lead
    return None


def list_leads(db: Session, state: LeadState | None = None) -> tuple[list[Lead], int]:
    query = select(Lead).order_by(Lead.created_at.desc(), Lead.id)
    if state is not None:
        query = query.where(Lead.state == state)
    leads = list(db.scalars(query).all())
    return leads, len(leads)


def get_lead(db: Session, lead_id: str) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise LeadNotFoundError(lead_id)
    return lead


def transition_lead(db: Session, lead_id: str, new_state: LeadState) -> Lead:
    """Apply a state transition.

    PENDING -> REACHED_OUT is allowed; a no-op transition to the current state is
    idempotent; anything else raises ``InvalidTransitionError``.
    """
    lead = get_lead(db, lead_id)
    if lead.state == new_state:
        return lead
    if lead.state is LeadState.PENDING and new_state is LeadState.REACHED_OUT:
        lead.state = new_state
        db.commit()
        db.refresh(lead)
        return lead
    raise InvalidTransitionError(
        f"Cannot transition lead from {lead.state.value} to {new_state.value}."
    )
