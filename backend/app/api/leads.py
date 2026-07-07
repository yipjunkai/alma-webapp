"""Lead endpoints: public intake plus attorney-only management."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from pydantic import ValidationError

from app.api.deps import CurrentUser, SessionDep, SettingsDep
from app.models import Lead, LeadState
from app.schemas import LeadCreate, LeadListOut, LeadOut, LeadStateUpdate
from app.services import leads as leads_service
from app.services import storage
from app.services.email import EmailServiceDep, compose_lead_emails, send_email_messages
from app.services.leads import InvalidTransitionError, LeadNotFoundError

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut, status_code=201)
def create_lead(
    first_name: Annotated[str, Form()],
    last_name: Annotated[str, Form()],
    email: Annotated[str, Form()],
    resume: Annotated[UploadFile, File()],
    background_tasks: BackgroundTasks,
    db: SessionDep,
    settings: SettingsDep,
    email_service: EmailServiceDep,
) -> Lead:
    try:
        data = LeadCreate(first_name=first_name, last_name=last_name, email=email)
    except ValidationError as exc:
        errors = [{**error, "loc": ("body", *error["loc"])} for error in exc.errors()]
        raise RequestValidationError(errors) from exc

    # Idempotency: a rapid duplicate (double-click / retry) with the same email
    # returns the original lead — no second file stored, no duplicate emails.
    #
    # Known trade-offs (acceptable at intake volume): this is check-then-create,
    # not atomic, with no unique constraint behind it — two truly concurrent
    # identical submits could both pass (SQLite's single writer makes that
    # unlikely). And a deliberate re-submit within the window (e.g. correcting a
    # wrong resume) returns the original lead and silently drops the new file.
    existing = leads_service.find_recent_by_email(
        db, data.email, settings.lead_dedupe_window_seconds
    )
    if existing is not None:
        return existing

    # Surface resume validation as a field-scoped 422, matching the pydantic shape
    # above so every 422 from this endpoint has one contract the client can map.
    try:
        stored_name, original_name = storage.save_resume(resume, settings.upload_dir)
    except storage.ResumeValidationError as exc:
        raise RequestValidationError(
            [{"type": "value_error", "loc": ("body", "resume"), "msg": exc.message, "input": None}]
        ) from exc

    try:
        lead = leads_service.create_lead(
            db,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            resume_stored_name=stored_name,
            resume_original_name=original_name,
        )
    except Exception:
        # Don't leave the just-written upload orphaned if persistence fails.
        storage.delete_resume(stored_name, settings.upload_dir)
        raise

    admin_leads_url = f"{settings.frontend_origin}/admin/leads"
    messages = compose_lead_emails(
        lead, attorney_email=settings.attorney_email, admin_leads_url=admin_leads_url
    )
    background_tasks.add_task(send_email_messages, email_service, messages)
    return lead


@router.get("", response_model=LeadListOut)
def list_leads(
    db: SessionDep,
    _user: CurrentUser,
    state: LeadState | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LeadListOut:
    leads, total = leads_service.list_leads(db, state=state, limit=limit, offset=offset)
    return LeadListOut(items=[LeadOut.model_validate(lead) for lead in leads], total=total)


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead_state(
    lead_id: str, payload: LeadStateUpdate, db: SessionDep, _user: CurrentUser
) -> Lead:
    try:
        return leads_service.transition_lead(db, lead_id, payload.state)
    except LeadNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Lead not found") from exc
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{lead_id}/resume")
def download_resume(
    lead_id: str, db: SessionDep, settings: SettingsDep, _user: CurrentUser
) -> FileResponse:
    try:
        lead = leads_service.get_lead(db, lead_id)
    except LeadNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Lead not found") from exc
    file_path = settings.upload_dir / lead.resume_stored_name
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Resume file not found")
    return FileResponse(file_path, filename=lead.resume_original_name)
