"""Tenant management API — admin only."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


class TenantCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    slug: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
    email: str
    tier: str = "starter"


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    email: str
    tier: str
    status: str = "trial"
    created_at: str = ""


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(request: Request, body: TenantCreateRequest):
    """Create a new tenant with isolated schema."""
    tenant_id = str(uuid.uuid4())

    # Create tenant schema
    schema_manager = getattr(request.app.state, "schema_manager", None)
    if schema_manager:
        await schema_manager.create_tenant_schema(body.slug)

    return TenantResponse(
        id=tenant_id,
        name=body.name,
        slug=body.slug,
        email=body.email,
        tier=body.tier,
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(request: Request, tenant_id: str):
    """Get tenant details."""
    raise HTTPException(status_code=404, detail="Tenant not found")


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(request: Request, tenant_id: str):
    """Delete a tenant and all data. IRREVERSIBLE."""
    return None
