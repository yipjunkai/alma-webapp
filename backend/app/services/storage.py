"""Resume upload validation and storage."""

import uuid
from pathlib import Path

from fastapi import UploadFile

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_RESUME_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_FILENAME_LENGTH = 255  # matches the resume_original_name column
_CHUNK_SIZE = 1024 * 1024


class ResumeValidationError(Exception):
    """An uploaded resume failed validation (missing name, bad type, empty, or too large).

    The endpoint maps this to a 422 scoped to the ``resume`` field, so all
    validation failures on POST /leads share one response shape.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def save_resume(upload: UploadFile, upload_dir: Path) -> tuple[str, str]:
    """Validate and persist an uploaded resume, streaming it to disk in chunks.

    Returns ``(stored_name, original_name)``. Raises ``ResumeValidationError`` when
    the file is missing a name, has a disallowed type, is empty, or exceeds 5 MB.
    Streaming keeps oversized uploads from sitting in memory.
    """
    original_name = Path(upload.filename or "").name.strip()
    if not original_name:
        raise ResumeValidationError("A resume file with a filename is required.")
    if len(original_name) > MAX_FILENAME_LENGTH:
        raise ResumeValidationError(
            f"Resume filename is too long (maximum {MAX_FILENAME_LENGTH} characters)."
        )

    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ResumeValidationError(
            f"Unsupported resume file type {extension or original_name!r}. "
            f"Allowed types: {allowed}."
        )

    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4()}{extension}"
    destination = upload_dir / stored_name

    bytes_written = 0
    try:
        with destination.open("wb") as out:
            while chunk := upload.file.read(_CHUNK_SIZE):
                bytes_written += len(chunk)
                if bytes_written > MAX_RESUME_BYTES:
                    raise ResumeValidationError(
                        "Resume file is too large. The maximum allowed size is 5 MB."
                    )
                out.write(chunk)
        if bytes_written == 0:
            raise ResumeValidationError("Resume file is empty.")
    except ResumeValidationError:
        destination.unlink(missing_ok=True)
        raise
    return stored_name, original_name


def delete_resume(stored_name: str, upload_dir: Path) -> None:
    """Best-effort removal of a stored resume (used to avoid orphans on later failure)."""
    (upload_dir / stored_name).unlink(missing_ok=True)
