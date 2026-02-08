"""
LangGraph Lead Qualification Orchestrator API Routes

Exposes the LangGraph-based lead qualification pipeline via REST endpoints:
- Process a lead through the full qualification workflow
- Batch qualification for multiple leads
- Pipeline health and configuration
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.langgraph_orchestrator import (
    QualificationResult,
    get_orchestrator,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/orchestration",
    tags=["Lead Qualification Orchestration"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class QualifyLeadRequest(BaseModel):
    contact_id: str = Field(..., description="GHL contact ID")
    location_id: str = Field(..., description="GHL location ID")
    message: str = Field(..., description="Latest inbound message")
    contact_tags: List[str] = Field(default_factory=list, description="Current GHL tags")
    contact_info: Dict[str, Any] = Field(default_factory=dict, description="Contact metadata")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="Prior conversation turns")


class QualificationResponse(BaseModel):
    success: bool
    response_content: str
    actions: List[Dict[str, Any]]
    temperature: str
    lead_type: str
    is_qualified: bool
    behavioral_signals: Dict[str, Any]
    qualification_stage: str
    scores: Dict[str, Any]
    error: Optional[str] = None


class BatchQualifyRequest(BaseModel):
    leads: List[QualifyLeadRequest] = Field(..., min_length=1, max_length=50)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/qualify", response_model=QualificationResponse)
async def qualify_lead(request: QualifyLeadRequest):
    """Run a single lead through the full LangGraph qualification pipeline."""
    try:
        orchestrator = get_orchestrator()
        result: QualificationResult = await orchestrator.process(
            contact_id=request.contact_id,
            location_id=request.location_id,
            message=request.message,
            contact_tags=request.contact_tags,
            contact_info=request.contact_info,
            conversation_history=request.conversation_history,
        )
        return QualificationResponse(
            success=result.success,
            response_content=result.response_content,
            actions=result.actions,
            temperature=result.temperature,
            lead_type=result.lead_type,
            is_qualified=result.is_qualified,
            behavioral_signals=result.behavioral_signals,
            qualification_stage=result.qualification_stage,
            scores=result.scores,
            error=result.error,
        )
    except Exception as e:
        logger.error("Qualification failed for %s: %s", request.contact_id, e)
        raise HTTPException(500, f"Qualification pipeline error: {e}")


@router.post("/qualify/batch")
async def qualify_leads_batch(request: BatchQualifyRequest):
    """Qualify multiple leads in a single request."""
    try:
        orchestrator = get_orchestrator()
        results = []
        for lead in request.leads:
            result = await orchestrator.process(
                contact_id=lead.contact_id,
                location_id=lead.location_id,
                message=lead.message,
                contact_tags=lead.contact_tags,
                contact_info=lead.contact_info,
                conversation_history=lead.conversation_history,
            )
            results.append(
                {
                    "contact_id": lead.contact_id,
                    "success": result.success,
                    "temperature": result.temperature,
                    "lead_type": result.lead_type,
                    "is_qualified": result.is_qualified,
                    "scores": result.scores,
                    "error": result.error,
                }
            )
        return {"results": results, "total": len(results)}
    except Exception as e:
        logger.error("Batch qualification failed: %s", e)
        raise HTTPException(500, f"Batch qualification error: {e}")


@router.get("/health")
async def orchestration_health():
    """Health check for the orchestration pipeline."""
    try:
        orchestrator = get_orchestrator()
        return {
            "status": "healthy",
            "service": "langgraph_orchestrator",
            "graph_compiled": orchestrator._graph is not None,
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
