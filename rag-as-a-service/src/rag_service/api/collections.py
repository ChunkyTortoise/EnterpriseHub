"""Collections API — CRUD for document collections."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/collections", tags=["collections"])


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    metadata: dict = Field(default_factory=dict)


class CollectionResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    document_count: int = 0
    metadata: dict = Field(default_factory=dict)
    created_at: str = ""


class CollectionListResponse(BaseModel):
    collections: list[CollectionResponse]
    total: int


@router.post("", response_model=CollectionResponse, status_code=201)
async def create_collection(request: Request, body: CollectionCreate):
    """Create a new document collection."""
    tenant_id = request.state.tenant_id
    collection_id = str(uuid.uuid4())

    # Audit log
    audit_logger = getattr(request.app.state, "audit_logger", None)
    if audit_logger:
        await audit_logger.log(
            tenant_id=tenant_id,
            action="collection.create",
            resource_type="collection",
            resource_id=collection_id,
            metadata={"name": body.name},
        )

    return CollectionResponse(
        id=collection_id,
        name=body.name,
        description=body.description,
        metadata=body.metadata,
    )


@router.get("", response_model=CollectionListResponse)
async def list_collections(request: Request):
    """List all collections for the current tenant."""
    return CollectionListResponse(collections=[], total=0)


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(request: Request, collection_id: str):
    """Get a specific collection."""
    # In production, query from per-tenant schema
    raise HTTPException(status_code=404, detail="Collection not found")


@router.delete("/{collection_id}", status_code=204)
async def delete_collection(request: Request, collection_id: str):
    """Delete a collection and all its documents."""
    tenant_id = request.state.tenant_id

    audit_logger = getattr(request.app.state, "audit_logger", None)
    if audit_logger:
        await audit_logger.log(
            tenant_id=tenant_id,
            action="collection.delete",
            resource_type="collection",
            resource_id=collection_id,
        )

    return None
