"""FastAPI JWT authentication middleware."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt
from pydantic import BaseModel

from shared_schemas.auth import Permission


class AuthContext(BaseModel):
    """Resolved authentication context for a request."""

    tenant_id: str
    user_id: str
    permissions: list[Permission]

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions


class JWTAuthBackend:
    """Decodes and validates JWT tokens."""

    def __init__(self, secret_key: str, algorithm: str = "HS256") -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm

    def decode(self, token: str) -> dict[str, Any]:
        """Decode a JWT token. Raises HTTPException on failure."""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except JWTError as exc:
            raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc

        exp = payload.get("exp")
        if exp is not None and datetime.utcfromtimestamp(exp) <= datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token expired")

        return payload

    def extract_auth_context(self, payload: dict[str, Any]) -> AuthContext:
        """Build AuthContext from decoded JWT payload."""
        permissions = [Permission(p) for p in payload.get("permissions", [])]
        return AuthContext(
            tenant_id=payload.get("tenant_id", ""),
            user_id=payload.get("sub", ""),
            permissions=permissions,
        )


_backend: JWTAuthBackend | None = None


def configure_auth(secret_key: str, algorithm: str = "HS256") -> None:
    """Configure the global JWT auth backend."""
    global _backend
    _backend = JWTAuthBackend(secret_key, algorithm)


def _get_backend() -> JWTAuthBackend:
    if _backend is None:
        raise RuntimeError("Auth not configured. Call configure_auth() at startup.")
    return _backend


def _extract_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return auth_header[7:]


async def get_auth_context(request: Request) -> AuthContext:
    """FastAPI dependency that extracts and validates JWT auth."""
    backend = _get_backend()
    token = _extract_token(request)
    payload = backend.decode(token)
    return backend.extract_auth_context(payload)


def require_auth(permissions: list[Permission] | None = None):
    """Factory that returns a FastAPI dependency requiring specific permissions."""

    async def _dependency(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if permissions:
            for perm in permissions:
                if not ctx.has_permission(perm):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Missing required permission: {perm.value}",
                    )
        return ctx

    return Depends(_dependency)


def require_permission(permission: Permission):
    """Shorthand: require a single permission."""
    return require_auth([permission])
