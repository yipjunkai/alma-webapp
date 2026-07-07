"""Property-based ("fuzz") tests.

Where the other suites assert behaviour on hand-picked examples, these use
Hypothesis to generate a wide range of adversarial inputs and assert that
*invariants* hold for all of them — the payoff is finding the input you didn't
think to write down. They target the code that parses untrusted input: the
public lead form, resume uploads, and the auth primitives.
"""

import io
import string
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi import UploadFile
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.core.security import create_access_token, decode_access_token, verify_credentials
from app.schemas import LeadCreate
from app.services.storage import ALLOWED_EXTENSIONS, ResumeValidationError, save_resume

VALID_EMAIL = "fuzz@example.com"
SECRET = "unit-test-signing-key-0123456789abcdef"
OTHER_SECRET = "a-different-unit-test-key-0123456789abcdef"

# C0 control range plus DEL — the characters LeadCreate strips from names.
CONTROL_CHARS = [chr(i) for i in range(0x20)] + ["\x7f"]


# --- Lead name sanitisation (schemas.LeadCreate) --------------------------------


@given(raw=st.text(max_size=100))
def test_accepted_names_are_control_free_and_trimmed(raw: str) -> None:
    """Any name LeadCreate accepts is stripped of control chars, trimmed, and bounded.

    Names that collapse to empty are rejected instead (asserted below), so the
    stored value is always something safe to drop into a log line or an email
    header.
    """
    try:
        lead = LeadCreate(first_name=raw, last_name=raw, email=VALID_EMAIL)
    except ValidationError:
        return  # collapsed-to-empty inputs are covered by the rejection test
    for name in (lead.first_name, lead.last_name):
        assert name == name.strip()
        assert all(ord(ch) >= 0x20 and ord(ch) != 0x7F for ch in name)
        assert 1 <= len(name) <= 100


@given(raw=st.text(alphabet=st.sampled_from([*CONTROL_CHARS, " "]), min_size=1, max_size=50))
def test_control_or_whitespace_only_names_are_rejected(raw: str) -> None:
    """A name that is only control characters and/or spaces collapses to '' and 422s."""
    with pytest.raises(ValidationError):
        LeadCreate(first_name=raw, last_name="Doe", email=VALID_EMAIL)


@given(raw=st.text(max_size=100))
def test_name_sanitisation_is_idempotent(raw: str) -> None:
    """Re-submitting an already-cleaned name yields the same value (stable normalisation)."""
    try:
        once = LeadCreate(first_name=raw, last_name="Doe", email=VALID_EMAIL).first_name
    except ValidationError:
        return
    twice = LeadCreate(first_name=once, last_name="Doe", email=VALID_EMAIL).first_name
    assert once == twice


# --- Resume upload storage (services.storage.save_resume) -----------------------


def _upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(io.BytesIO(content), filename=filename)


@settings(deadline=None)  # each example does real filesystem IO
@given(filename=st.text(max_size=300), content=st.binary(max_size=64))
def test_save_resume_is_safe_for_any_filename(filename: str, content: bytes) -> None:
    """No filename can escape the upload dir, leak a partial file, or crash the writer.

    The only exception a caller ever has to handle is ResumeValidationError; on
    success the file lands under an unguessable uuid name inside the upload dir
    and its bytes round-trip exactly.
    """
    with tempfile.TemporaryDirectory() as tmp:
        upload_dir = Path(tmp) / "uploads"  # save_resume creates this; it isn't pre-made
        try:
            stored, original = save_resume(_upload(filename, content), upload_dir)
        except ResumeValidationError:
            # A rejection (bad type, empty, missing/oversize name) leaves nothing behind.
            assert not upload_dir.exists() or list(upload_dir.iterdir()) == []
            return
        target = upload_dir / stored
        assert target.resolve().parent == upload_dir.resolve()  # never writes outside the dir
        assert list(upload_dir.iterdir()) == [target]  # exactly one file, no strays
        uuid.UUID(Path(stored).stem)  # stored under a uuid, not attacker-controlled input
        assert Path(stored).suffix.lower() in ALLOWED_EXTENSIONS
        assert target.read_bytes() == content  # content round-trips byte-for-byte
        assert original == Path(original).name and "/" not in original  # basename only


@settings(deadline=None)
@given(
    stem=st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=40),
    ext=st.sampled_from(sorted(ALLOWED_EXTENSIONS)),
    content=st.binary(min_size=1, max_size=64),
)
def test_allowed_extensions_are_stored(stem: str, ext: str, content: bytes) -> None:
    """Every allowed type with real content is stored and keeps its extension."""
    with tempfile.TemporaryDirectory() as tmp:
        upload_dir = Path(tmp) / "uploads"
        stored, original = save_resume(_upload(stem + ext, content), upload_dir)
        assert Path(stored).suffix == ext
        assert original == stem + ext
        assert (upload_dir / stored).read_bytes() == content


# --- Session tokens & credentials (core.security) -------------------------------


@given(subject=st.text())
def test_token_roundtrips_for_any_subject(subject: str) -> None:
    """A freshly minted token always decodes back to its exact subject."""
    token = create_access_token(subject, SECRET)
    assert decode_access_token(token, SECRET) == subject


@given(token=st.text())
def test_decode_is_total_on_arbitrary_input(token: str) -> None:
    """Decoding attacker-controlled text returns None or a str — never raises."""
    result = decode_access_token(token, SECRET)
    assert result is None or isinstance(result, str)


@given(subject=st.text())
def test_token_signed_with_another_key_is_rejected(subject: str) -> None:
    """A token minted under a different secret never validates (HMAC signature check)."""
    token = create_access_token(subject, SECRET)
    assert decode_access_token(token, OTHER_SECRET) is None


@given(email=st.text(max_size=200), password=st.text(max_size=200))
def test_verify_credentials_matches_only_the_exact_pair(email: str, password: str) -> None:
    """Only the exact (email, password) pair returns True — and no input can crash it.

    Passwords are unvalidated free text, so a lone surrogate (arriving as a JSON
    \\uXXXX escape) must yield a clean False here rather than a 500.
    """
    expected_email = "attorney@example.com"
    expected_password = "correct horse battery staple"
    result = verify_credentials(email, password, expected_email, expected_password)
    assert result == (email == expected_email and password == expected_password)
