"""FastAPI authentication middleware — API key and JWT support."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import jwt
from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER = HTTPBearer(auto_error=False)

API_KEY_CACHE_TTL = 300  # 5 minutes


@dataclass
class AuthContext:
    """Authentication context extracted from request."""

    tenant_id: str
    scopes: list[str] = field(default_factory=lambda: ["read"])
    user_id: str | None = None
    auth_method: str = "api_key"  # "api_key" or "jwt"


class AuthMiddleware:
    """FastAPI dependency for API key and JWT authentication."""

    def __init__(
        self,
        redis: aioredis.Redis,
        db_session_factory: Callable,
        jwt_secret: str = "",
        jwt_algorithm: str = "HS256",
    ):
        self.redis = redis
        self.db = db_session_factory
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm

    async def verify_api_key(
        self, api_key: str | None = Security(API_KEY_HEADER)
    ) -> AuthContext:
        """Verify an API key from X-API-Key header."""
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")

        hashed = hashlib.sha256(api_key.encode()).hexdigest()

        # Check Redis cache first
        cached = await self.redis.get(f"apikey:{hashed}")
        if cached:
            data = json.loads(cached)
            return AuthContext(
                tenant_id=data["tenant_id"],
                scopes=data.get("scopes", ["read"]),
                auth_method="api_key",
            )

        # Fallback: query database
        async with self.db() as session:
            result = await session.execute(
                "SELECT tenant_id, scopes FROM api_keys WHERE hashed_key = :h AND is_active = true",
                {"h": hashed},
            )
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="Invalid API key")

            payload = {"tenant_id": str(row.tenant_id), "scopes": row.scopes}
            await self.redis.setex(f"apikey:{hashed}", API_KEY_CACHE_TTL, json.dumps(payload))

            return AuthContext(
                tenant_id=str(row.tenant_id),
                scopes=row.scopes,
                auth_method="api_key",
            )

    async def verify_jwt(
        self, credentials: HTTPAuthorizationCredentials | None = Security(BEARER)
    ) -> AuthContext:
        """Verify a JWT Bearer token."""
        if not credentials:
            raise HTTPException(status_code=401, detail="Missing authorization header")

        if not self.jwt_secret:
            raise HTTPException(status_code=500, detail="JWT authentication not configured")

        try:
            payload = jwt.decode(
                credentials.credentials,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

        return AuthContext(
            tenant_id=payload.get("tenant_id", ""),
            scopes=payload.get("scopes", ["read"]),
            user_id=payload.get("sub"),
            auth_method="jwt",
        )

    async def rate_limit(self, tenant_id: str, limit: int = 100) -> None:
        """Check per-tenant rate limit using simple counter."""
        key = f"ratelimit:{tenant_id}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 60)
        if current > limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

    async def get_current_tenant(self, request: Request) -> AuthContext:
        """FastAPI dependency: authenticate via API key or JWT.

        Tries API key first, then falls back to JWT.
        """
        api_key = request.headers.get("X-API-Key")
        auth_header = request.headers.get("Authorization")

        if api_key:
            ctx = await self.verify_api_key(api_key)
        elif auth_header and auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")

            class Creds:
                credentials = token
                scheme = "Bearer"

            ctx = await self.verify_jwt(Creds())  # type: ignore[arg-type]
        else:
            raise HTTPException(status_code=401, detail="No authentication provided")

        await self.rate_limit(ctx.tenant_id)
        return ctx
