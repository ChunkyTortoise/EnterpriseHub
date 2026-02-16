"""Document management API — upload, list, delete documents."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    chunk_count: int
    collection_id: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: str = ""


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    collection_id: str | None = None,
):
    """Upload a document for processing and indexing."""
    tenant_id = request.state.tenant_id

    # Check quota
    usage_tracker = request.app.state.usage_tracker
    tier = getattr(request.state, "tenant_tier", "starter")
    within_quota = await usage_tracker.check_quota(tenant_id, tier, "documents")
    if not within_quota:
        raise HTTPException(status_code=429, detail="Document limit exceeded for your tier")

    # Read file content
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "unnamed"

    # Process document
    processor = request.app.state.document_processor
    try:
        processed = processor.process(content, filename, content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # PII scan if enabled
    pii_detector = getattr(request.app.state, "pii_detector", None)
    if pii_detector:
        scan_result = pii_detector.scan(processed.raw_text)
        if scan_result.has_pii:
            # Store redacted version
            processed = processor.process(
                scan_result.redacted_text.encode("utf-8"), filename, "text/plain"
            )

    doc_id = str(uuid.uuid4())

    # Track usage
    await usage_tracker.increment_documents(tenant_id)
    await usage_tracker.increment_storage(tenant_id, len(content))

    # Audit log
    audit_logger = getattr(request.app.state, "audit_logger", None)
    if audit_logger:
        await audit_logger.log(
            tenant_id=tenant_id,
            action="document.upload",
            resource_type="document",
            resource_id=doc_id,
            metadata={"filename": filename, "size": len(content), "chunks": len(processed.chunks)},
        )

    return DocumentResponse(
        id=doc_id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(content),
        chunk_count=len(processed.chunks),
        collection_id=collection_id,
        metadata=processed.metadata,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(request: Request, collection_id: str | None = None, limit: int = 50):
    """List documents for the current tenant."""
    # In production, query from per-tenant schema
    return DocumentListResponse(documents=[], total=0)


@router.delete("/{document_id}", status_code=204)
async def delete_document(request: Request, document_id: str):
    """Delete a document and its chunks."""
    tenant_id = request.state.tenant_id

    # Track usage reduction
    usage_tracker = request.app.state.usage_tracker
    await usage_tracker.decrement_documents(tenant_id)

    # Audit log
    audit_logger = getattr(request.app.state, "audit_logger", None)
    if audit_logger:
        await audit_logger.log(
            tenant_id=tenant_id,
            action="document.delete",
            resource_type="document",
            resource_id=document_id,
        )

    return None
