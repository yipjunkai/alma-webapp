"""Seed the database with sample leads.

Run from backend/ after migrations:

    uv run alembic upgrade head
    uv run python -m app.seed
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.db import get_sessionmaker
from app.models import Lead, LeadState

TINY_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"%%EOF\n"
)

SAMPLE_LEADS = [
    ("Sofia", "Martinez", "sofia.martinez@example.com", LeadState.PENDING),
    ("Liam", "Chen", "liam.chen@example.com", LeadState.PENDING),
    ("Priya", "Patel", "priya.patel@example.com", LeadState.PENDING),
    ("Noah", "Johnson", "noah.johnson@example.com", LeadState.REACHED_OUT),
    ("Amara", "Okafor", "amara.okafor@example.com", LeadState.REACHED_OUT),
]


def seed() -> None:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    session = get_sessionmaker()()
    try:
        try:
            existing = session.scalar(select(func.count()).select_from(Lead)) or 0
        except OperationalError:
            print("Database schema missing. Run 'uv run alembic upgrade head' first.")
            raise SystemExit(1) from None
        if existing:
            print(f"Leads already present ({existing}); nothing to do.")
            return
        now = datetime.now(UTC)
        for index, (first_name, last_name, email, state) in enumerate(SAMPLE_LEADS):
            stored_name = f"{uuid.uuid4()}.pdf"
            (settings.upload_dir / stored_name).write_bytes(TINY_PDF)
            created = now - timedelta(hours=6 * index + 1)
            session.add(
                Lead(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    state=state,
                    resume_stored_name=stored_name,
                    resume_original_name=f"{first_name.lower()}_{last_name.lower()}_resume.pdf",
                    created_at=created,
                    updated_at=created,
                )
            )
        session.commit()
        pending = sum(1 for lead in SAMPLE_LEADS if lead[3] is LeadState.PENDING)
        reached = len(SAMPLE_LEADS) - pending
        print(f"Seeded {len(SAMPLE_LEADS)} leads ({pending} PENDING, {reached} REACHED_OUT).")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
