"""Regression tests for the bcrypt 72-byte password guard in jwt_auth.

REQ-W4-3 / audit D P1-6: ``JWTAuth.hash_password`` must reject passwords
longer than bcrypt's 72-byte limit with HTTP 422 instead of silently
truncating, matching the behavior in ``enhanced_auth.py``. The length check
is measured in UTF-8 bytes, not characters.
"""

import pytest
from fastapi import HTTPException, status

from ghl_real_estate_ai.api.middleware.jwt_auth import JWTAuth


def test_hash_password_accepts_exactly_72_bytes():
    """A 72-byte password is at the limit and must hash without error."""
    password = "a" * 72
    assert len(password.encode("utf-8")) == 72

    hashed = JWTAuth.hash_password(password)

    assert isinstance(hashed, str)
    assert hashed != password


def test_hash_password_rejects_over_72_bytes_with_422():
    """A 73-byte password must raise 422, not be truncated and hashed."""
    password = "a" * 73
    assert len(password.encode("utf-8")) == 73

    with pytest.raises(HTTPException) as excinfo:
        JWTAuth.hash_password(password)

    assert excinfo.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "not exceed 72 characters" in excinfo.value.detail


def test_hash_password_counts_utf8_bytes_not_characters():
    """Multibyte chars count toward the byte budget (37 * 2 = 74 bytes)."""
    password = "é" * 37
    assert len(password) == 37
    assert len(password.encode("utf-8")) == 74

    with pytest.raises(HTTPException) as excinfo:
        JWTAuth.hash_password(password)

    assert excinfo.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
