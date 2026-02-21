"""API key and JWT authentication for enterprise tier."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPBearer

# Try jose for JWT, fall back gracefully if not installed
try:
    from jose import JWTError
    from jose import jwt as jose_jwt

    _JWT_AVAILABLE = True
except ImportError:
    _JWT_AVAILABLE = False

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer = HTTPBearer(auto_error=False)

# Default allowed keys -- in production, load from env/database
_DEFAULT_ALLOWED_KEYS: frozenset[str] = frozenset(
    k.strip() for k in os.getenv("ENTERPRISE_API_KEYS", "test-key-1,test-key-2").split(",") if k.strip()
)
_JWT_SECRET = os.getenv("JWT_SECRET", "enterprise-dev-secret-change-in-prod")
_JWT_ALGORITHM = "HS256"


class APIKeyAuth:
    """Validate API keys from X-API-Key header."""

    def __init__(self, allowed_keys: Optional[frozenset[str]] = None) -> None:
        self.allowed_keys = allowed_keys or _DEFAULT_ALLOWED_KEYS

    def validate(self, api_key: Optional[str]) -> str:
        """Return tenant_id derived from valid API key, else raise 401."""
        if not api_key or api_key not in self.allowed_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        # Tenant ID is the API key itself (in prod, map key -> tenant_id in DB)
        return f"tenant:{api_key}"


class JWTAuth:
    """Validate Bearer JWT tokens."""

    def __init__(self, secret: Optional[str] = None, algorithm: str = _JWT_ALGORITHM) -> None:
        self.secret = secret or _JWT_SECRET
        self.algorithm = algorithm

    def validate(self, token: Optional[str]) -> str:
        """Return tenant_id from JWT sub claim, else raise 401."""
        if not _JWT_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="python-jose not installed -- JWT auth unavailable",
            )
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
        try:
            payload = jose_jwt.decode(token, self.secret, algorithms=[self.algorithm])
            tenant_id: Optional[str] = payload.get("sub")
            if not tenant_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing sub claim")
            return tenant_id
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
            ) from exc


_api_key_auth = APIKeyAuth()
_jwt_auth = JWTAuth()


async def get_current_tenant(request: Request) -> str:
    """FastAPI dependency -- try API key first, then JWT Bearer token."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return _api_key_auth.validate(api_key)

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return _jwt_auth.validate(auth_header[7:])

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide X-API-Key header or Bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )
