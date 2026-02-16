"""Auth API — API key creation and management."""

from __future__ import annotations

import hashlib
import secrets
import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class APIKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    scopes: list[str] = Field(default=["read", "write"])


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    full_key: str  # Only returned on creation
    scopes: list[str]
    created_at: str = ""


class APIKeyListResponse(BaseModel):
    keys: list[APIKeyResponse]


@router.post("/keys", response_model=APIKeyResponse, status_code=201)
async def create_api_key(request: Request, body: APIKeyCreateRequest):
    """Create a new API key for the current tenant."""
    # Generate secure API key
    raw_key = f"rag_{secrets.token_urlsafe(32)}"
    key_prefix = raw_key[:12]
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    key_id = str(uuid.uuid4())

    # Audit log
    audit_logger = getattr(request.app.state, "audit_logger", None)
    if audit_logger:
        tenant_id = getattr(request.state, "tenant_id", "system")
        await audit_logger.log(
            tenant_id=tenant_id,
            action="auth.create_key",
            resource_type="api_key",
            resource_id=key_id,
            metadata={"name": body.name, "scopes": body.scopes},
        )

    return APIKeyResponse(
        id=key_id,
        name=body.name,
        key_prefix=key_prefix,
        full_key=raw_key,
        scopes=body.scopes,
    )


@router.get("/keys", response_model=APIKeyListResponse)
async def list_api_keys(request: Request):
    """List API keys for the current tenant (prefix only, not full keys)."""
    return APIKeyListResponse(keys=[])
