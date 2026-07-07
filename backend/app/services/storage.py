"""Resume upload validation and storage."""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_RESUME_BYTES = 5 * 1024 * 1024  # 5 MB
_CHUNK_SIZE = 1024 * 1024


def save_resume(upload: UploadFile, upload_dir: Path) -> tuple[str, str]:
    """Validate and persist an uploaded resume.

    Returns ``(stored_name, original_name)``. Raises ``HTTPException(422)`` with a
    helpful message when the file type is not allowed or the file is too large.
    The file is streamed to disk in chunks so oversized uploads never sit in memory.
    """
    original_name = Path(upload.filename or "").name.strip()
    if not original_name:
        raise HTTPException(status_code=422, detail="A resume file with a filename is required.")

    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported resume file type {extension or original_name!r}. "
                f"Allowed types: {allowed}."
            ),
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
                    raise HTTPException(
                        status_code=422,
                        detail="Resume file is too large. The maximum allowed size is 5 MB.",
                    )
                out.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    return stored_name, original_name
