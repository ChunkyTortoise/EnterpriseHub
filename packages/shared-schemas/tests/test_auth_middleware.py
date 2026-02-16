"""Tests for auth middleware."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from jose import jwt

from shared_infra.auth_middleware import AuthContext, JWTAuthBackend, configure_auth, get_auth_context
from shared_schemas.auth import Permission


@pytest.fixture
def secret():
    return "test-secret-key-for-jwt"


@pytest.fixture
def backend(secret):
    return JWTAuthBackend(secret)


@pytest.fixture
def valid_token(secret):
    payload = {
        "sub": "user-1",
        "tenant_id": "t-1",
        "permissions": ["READ", "WRITE"],
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def expired_token(secret):
    payload = {
        "sub": "user-1",
        "tenant_id": "t-1",
        "permissions": ["READ"],
        "exp": datetime.utcnow() - timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


class TestJWTAuthBackend:
    def test_decode_valid_token(self, backend, valid_token):
        payload = backend.decode(valid_token)
        assert payload["sub"] == "user-1"
        assert payload["tenant_id"] == "t-1"

    def test_decode_expired_token_raises(self, backend, expired_token):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            backend.decode(expired_token)
        assert exc_info.value.status_code == 401

    def test_decode_invalid_token_raises(self, backend):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            backend.decode("not-a-real-token")
        assert exc_info.value.status_code == 401

    def test_extract_auth_context(self, backend, valid_token):
        payload = backend.decode(valid_token)
        ctx = backend.extract_auth_context(payload)
        assert ctx.tenant_id == "t-1"
        assert ctx.user_id == "user-1"
        assert Permission.READ in ctx.permissions
        assert Permission.WRITE in ctx.permissions


class TestAuthContext:
    def test_has_permission(self):
        ctx = AuthContext(tenant_id="t-1", user_id="u-1", permissions=[Permission.READ])
        assert ctx.has_permission(Permission.READ) is True
        assert ctx.has_permission(Permission.ADMIN) is False

    def test_empty_permissions(self):
        ctx = AuthContext(tenant_id="t-1", user_id="u-1", permissions=[])
        assert ctx.has_permission(Permission.READ) is False


class TestGetAuthContext:
    @pytest.mark.asyncio
    async def test_missing_bearer_raises(self):
        from fastapi import HTTPException

        configure_auth("secret")
        request = MagicMock()
        request.headers = {"Authorization": "Basic abc"}
        with pytest.raises(HTTPException) as exc_info:
            await get_auth_context(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_no_auth_header_raises(self):
        from fastapi import HTTPException

        configure_auth("secret")
        request = MagicMock()
        request.headers = {}
        with pytest.raises(HTTPException) as exc_info:
            await get_auth_context(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_bearer_returns_context(self, secret, valid_token):
        configure_auth(secret)
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {valid_token}"}
        ctx = await get_auth_context(request)
        assert ctx.tenant_id == "t-1"
        assert ctx.user_id == "user-1"
