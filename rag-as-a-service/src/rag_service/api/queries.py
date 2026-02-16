"""Query API — RAG query with answer + sources, SSE streaming."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/query", tags=["queries"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    collection_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=50)
    expand: bool = True
    expansion_method: str = "multi_query"


class SourceInfo(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]
    query: str
    latency_ms: int
    metadata: dict = Field(default_factory=dict)


@router.post("", response_model=QueryResponse)
async def query_rag(request: Request, body: QueryRequest):
    """Execute a RAG query and return answer with sources."""
    tenant_id = request.state.tenant_id
    tier = getattr(request.state, "tenant_tier", "starter")

    # Check query quota
    usage_tracker = request.app.state.usage_tracker
    within_quota = await usage_tracker.check_quota(tenant_id, tier, "queries")
    if not within_quota:
        raise HTTPException(status_code=429, detail="Query limit exceeded for your tier")

    # PII scan the query
    pii_detector = getattr(request.app.state, "pii_detector", None)
    query_text = body.query
    if pii_detector:
        scan = pii_detector.scan(query_text)
        if scan.has_pii:
            query_text = scan.redacted_text

    # Execute RAG pipeline
    rag_engine = request.app.state.rag_engine
    result = await rag_engine.query(
        query_text=query_text,
        collection_id=body.collection_id,
        top_k=body.top_k,
        expand=body.expand,
        expansion_method=body.expansion_method,
    )

    # Track usage
    await usage_tracker.increment_queries(tenant_id)

    # Report to Stripe
    billing = getattr(request.app.state, "billing_service", None)
    if billing:
        await billing.report_query_usage(tenant_id)

    # Audit log
    audit_logger = getattr(request.app.state, "audit_logger", None)
    if audit_logger:
        await audit_logger.log(
            tenant_id=tenant_id,
            action="query.execute",
            resource_type="query",
            metadata={
                "query_length": len(body.query),
                "sources_count": len(result.sources),
                "latency_ms": result.latency_ms,
            },
        )

    return QueryResponse(
        answer=result.answer,
        sources=[
            SourceInfo(
                chunk_id=s.chunk_id,
                document_id=s.document_id,
                content=s.content,
                score=s.score,
                metadata=s.metadata,
            )
            for s in result.sources
        ],
        query=result.query,
        latency_ms=result.latency_ms,
        metadata=result.metadata,
    )


@router.post("/stream")
async def query_stream(request: Request, body: QueryRequest):
    """Stream RAG query response via SSE."""
    tenant_id = request.state.tenant_id
    tier = getattr(request.state, "tenant_tier", "starter")

    # Check quota
    usage_tracker = request.app.state.usage_tracker
    within_quota = await usage_tracker.check_quota(tenant_id, tier, "queries")
    if not within_quota:
        raise HTTPException(status_code=429, detail="Query limit exceeded for your tier")

    rag_engine = request.app.state.rag_engine

    async def event_generator():
        async for token in rag_engine.query_stream(
            query_text=body.query,
            collection_id=body.collection_id,
            top_k=body.top_k,
        ):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    # Track usage
    await usage_tracker.increment_queries(tenant_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
