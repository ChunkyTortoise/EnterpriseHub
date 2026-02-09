"""
Behavioral Trigger Detection API Routes

Exposes behavioral analysis capabilities for negotiation pattern detection,
hedging/commitment scoring, and Voss technique recommendations.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.behavioral_trigger_detector import (
    get_behavioral_detector,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/behavioral",
    tags=["Behavioral Trigger Detection"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class AnalyzeMessageRequest(BaseModel):
    message: str = Field(..., description="Message text to analyze")
    contact_id: str = Field(..., description="Contact identifier")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        None, description="Prior conversation turns for context"
    )
    response_latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")


class TriggerResponse(BaseModel):
    type: str
    confidence: float
    description: str
    recommended_action: str


class BehavioralAnalysisResponse(BaseModel):
    composite_score: float
    drift_direction: str
    hedging_score: float
    urgency_score: float
    commitment_score: float
    recommended_technique: Optional[str]
    latency_factor: float
    triggers: List[TriggerResponse]
    trigger_count: int


class BatchAnalyzeRequest(BaseModel):
    messages: List[AnalyzeMessageRequest] = Field(..., min_length=1, max_length=100)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/analyze", response_model=BehavioralAnalysisResponse)
async def analyze_message(request: AnalyzeMessageRequest):
    """Analyze a single message for behavioral triggers and negotiation signals."""
    try:
        detector = get_behavioral_detector()
        result = await detector.analyze_message(
            message=request.message,
            contact_id=request.contact_id,
            conversation_history=request.conversation_history,
            response_latency_ms=request.response_latency_ms,
        )
        return BehavioralAnalysisResponse(
            composite_score=result.composite_score,
            drift_direction=result.drift_direction,
            hedging_score=result.hedging_score,
            urgency_score=result.urgency_score,
            commitment_score=result.commitment_score,
            recommended_technique=result.recommended_technique,
            latency_factor=result.latency_factor,
            triggers=[
                TriggerResponse(
                    type=t.type.value,
                    confidence=t.confidence,
                    description=t.description,
                    recommended_action=t.recommended_action,
                )
                for t in result.triggers
            ],
            trigger_count=len(result.triggers),
        )
    except Exception as e:
        logger.error("Behavioral analysis failed for %s: %s", request.contact_id, e)
        raise HTTPException(500, f"Behavioral analysis error: {e}")


@router.post("/analyze/batch")
async def analyze_messages_batch(request: BatchAnalyzeRequest):
    """Analyze multiple messages for behavioral triggers."""
    try:
        detector = get_behavioral_detector()
        results = []
        for msg in request.messages:
            result = await detector.analyze_message(
                message=msg.message,
                contact_id=msg.contact_id,
                conversation_history=msg.conversation_history,
                response_latency_ms=msg.response_latency_ms,
            )
            results.append(
                {
                    "contact_id": msg.contact_id,
                    "composite_score": result.composite_score,
                    "drift_direction": result.drift_direction,
                    "hedging_score": result.hedging_score,
                    "commitment_score": result.commitment_score,
                    "recommended_technique": result.recommended_technique,
                    "trigger_count": len(result.triggers),
                }
            )
        return {"results": results, "total": len(results)}
    except Exception as e:
        logger.error("Batch behavioral analysis failed: %s", e)
        raise HTTPException(500, f"Batch analysis error: {e}")


@router.get("/health")
async def behavioral_health():
    """Health check for the behavioral trigger detector."""
    try:
        detector = get_behavioral_detector()
        return {
            "status": "healthy",
            "service": "behavioral_trigger_detector",
            "pattern_categories": 6,
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
