"""Unit tests for resume validation and safe storage (no app/DB needed)."""

import io
import uuid
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.services.storage import MAX_RESUME_BYTES, ResumeValidationError, save_resume

PDF = b"%PDF-1.4 test %%EOF"


def _upload(filename: str, content: bytes = PDF) -> UploadFile:
    return UploadFile(io.BytesIO(content), filename=filename)


def test_stores_under_uuid_name_and_keeps_original(tmp_path: Path) -> None:
    stored, original = save_resume(_upload("resume.pdf"), tmp_path)
    assert original == "resume.pdf"
    assert stored.endswith(".pdf")
    uuid.UUID(Path(stored).stem)  # stored stem is a uuid, not the user's name
    assert (tmp_path / stored).read_bytes() == PDF


def test_path_traversal_filename_is_neutralised(tmp_path: Path) -> None:
    stored, original = save_resume(_upload("../../../etc/passwd.pdf"), tmp_path)
    # Directory components are stripped from both the stored and original names,
    # and nothing is written outside the upload dir.
    assert original == "passwd.pdf"
    assert Path(stored).parent == Path(".")
    assert list(tmp_path.iterdir()) == [tmp_path / stored]


def test_unicode_filename_is_preserved(tmp_path: Path) -> None:
    _, original = save_resume(_upload("résumé café.pdf"), tmp_path)
    assert original == "résumé café.pdf"


def test_rejects_disallowed_extension(tmp_path: Path) -> None:
    with pytest.raises(ResumeValidationError):
        save_resume(_upload("malware.exe", b"MZ"), tmp_path)


def test_rejects_missing_filename(tmp_path: Path) -> None:
    with pytest.raises(ResumeValidationError):
        save_resume(_upload("", PDF), tmp_path)


def test_rejects_too_long_filename(tmp_path: Path) -> None:
    with pytest.raises(ResumeValidationError):
        save_resume(_upload("a" * 300 + ".pdf"), tmp_path)


def test_rejects_empty_file(tmp_path: Path) -> None:
    with pytest.raises(ResumeValidationError):
        save_resume(_upload("empty.pdf", b""), tmp_path)


def test_rejects_oversize_file_and_cleans_up(tmp_path: Path) -> None:
    with pytest.raises(ResumeValidationError):
        save_resume(_upload("big.pdf", b"x" * (MAX_RESUME_BYTES + 1)), tmp_path)
    # No partial file is left behind after the streamed size check trips.
    assert list(tmp_path.iterdir()) == []
