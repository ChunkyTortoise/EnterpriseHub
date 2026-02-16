"""Tests for auth middleware (mocked Redis/DB)."""

import json
import time
import hashlib

import jwt
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from shared_infra.auth_middleware import AuthContext, AuthMiddleware


@pytest.fixture
def auth_middleware(mock_redis, mock_db_session):
    return AuthMiddleware(
        redis=mock_redis,
        db_session_factory=mock_db_session,
        jwt_secret="test-secret-key",
    )


class TestVerifyApiKey:
    async def test_missing_key_raises_401(self, auth_middleware):
        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.verify_api_key(None)
        assert exc_info.value.status_code == 401

    async def test_valid_key_from_cache(self, auth_middleware, mock_redis):
        hashed = hashlib.sha256(b"test-key-123").hexdigest()
        mock_redis._store[f"apikey:{hashed}"] = json.dumps(
            {"tenant_id": "t1", "scopes": ["read", "write"]}
        )
        ctx = await auth_middleware.verify_api_key("test-key-123")
        assert ctx.tenant_id == "t1"
        assert ctx.auth_method == "api_key"

    async def test_valid_key_from_db(self, auth_middleware, mock_redis):
        ctx = await auth_middleware.verify_api_key("new-key-456")
        assert isinstance(ctx, AuthContext)
        assert ctx.auth_method == "api_key"

    async def test_invalid_key_raises_401(self, auth_middleware, mock_db_session):
        # Make DB return no results
        session = AsyncMock()
        result = MagicMock()
        result.fetchone.return_value = None
        session.execute = AsyncMock(return_value=result)

        class NullSessionFactory:
            def __call__(self):
                return self
            async def __aenter__(self):
                return session
            async def __aexit__(self, *args):
                pass

        auth_middleware.db = NullSessionFactory()
        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.verify_api_key("bad-key")
        assert exc_info.value.status_code == 401


class TestVerifyJwt:
    async def test_missing_credentials_raises_401(self, auth_middleware):
        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.verify_jwt(None)
        assert exc_info.value.status_code == 401

    async def test_valid_jwt(self, auth_middleware):
        token = jwt.encode(
            {"sub": "user1", "tenant_id": "t1", "scopes": ["read"], "exp": int(time.time()) + 3600},
            "test-secret-key",
            algorithm="HS256",
        )

        class Creds:
            credentials = token
            scheme = "Bearer"

        ctx = await auth_middleware.verify_jwt(Creds())
        assert ctx.tenant_id == "t1"
        assert ctx.user_id == "user1"
        assert ctx.auth_method == "jwt"

    async def test_expired_jwt_raises_401(self, auth_middleware):
        token = jwt.encode(
            {"sub": "user1", "tenant_id": "t1", "exp": int(time.time()) - 100},
            "test-secret-key",
            algorithm="HS256",
        )

        class Creds:
            credentials = token
            scheme = "Bearer"

        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.verify_jwt(Creds())
        assert exc_info.value.status_code == 401

    async def test_invalid_jwt_raises_401(self, auth_middleware):
        class Creds:
            credentials = "not.a.valid.jwt"
            scheme = "Bearer"

        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.verify_jwt(Creds())
        assert exc_info.value.status_code == 401

    async def test_no_jwt_secret_raises_500(self, mock_redis, mock_db_session):
        mw = AuthMiddleware(redis=mock_redis, db_session_factory=mock_db_session)

        class Creds:
            credentials = "some.token"
            scheme = "Bearer"

        with pytest.raises(HTTPException) as exc_info:
            await mw.verify_jwt(Creds())
        assert exc_info.value.status_code == 500


class TestRateLimit:
    async def test_within_limit(self, auth_middleware, mock_redis):
        mock_redis._counters.clear()
        await auth_middleware.rate_limit("t1", limit=100)
        # Should not raise

    async def test_exceeds_limit(self, auth_middleware, mock_redis):
        mock_redis._counters["ratelimit:t1"] = 100
        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.rate_limit("t1", limit=100)
        assert exc_info.value.status_code == 429


class TestGetCurrentTenant:
    async def test_api_key_auth(self, auth_middleware, mock_redis):
        hashed = hashlib.sha256(b"my-key").hexdigest()
        mock_redis._store[f"apikey:{hashed}"] = json.dumps(
            {"tenant_id": "t1", "scopes": ["read"]}
        )
        request = MagicMock()
        request.headers = {"X-API-Key": "my-key"}
        ctx = await auth_middleware.get_current_tenant(request)
        assert ctx.tenant_id == "t1"

    async def test_jwt_auth(self, auth_middleware):
        token = jwt.encode(
            {"sub": "u1", "tenant_id": "t2", "scopes": ["read"], "exp": int(time.time()) + 3600},
            "test-secret-key",
            algorithm="HS256",
        )
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {token}"}
        ctx = await auth_middleware.get_current_tenant(request)
        assert ctx.tenant_id == "t2"

    async def test_no_auth_raises_401(self, auth_middleware):
        request = MagicMock()
        request.headers = {}
        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.get_current_tenant(request)
        assert exc_info.value.status_code == 401
