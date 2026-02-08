"""
Vapi Voice Intelligence API Routes

Exposes voice call processing, transcript analysis, and voice-to-qualification
pipeline via REST and webhook endpoints.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.vapi_voice_integration import (
    TranscriptSegment,
    get_voice_intelligence,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/voice-intelligence",
    tags=["Voice Intelligence"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class TranscriptSegmentInput(BaseModel):
    role: str = Field(..., description="Speaker role: agent, customer, system")
    text: str = Field(..., description="Segment text")
    timestamp_ms: float = Field(0.0, description="Timestamp in milliseconds")
    confidence: float = Field(1.0, description="Transcription confidence")


class AnalyzeTranscriptRequest(BaseModel):
    contact_id: str = Field(..., description="Contact identifier")
    call_id: str = Field(..., description="Call identifier")
    transcript_segments: List[TranscriptSegmentInput] = Field(..., min_length=1, description="Transcript segments")
    call_duration_seconds: float = Field(0.0, description="Call duration")


class TranscriptAnalysisResponse(BaseModel):
    contact_id: str
    call_id: str
    composite_score: float
    hedging_score: float
    commitment_score: float
    urgency_score: float
    drift_direction: str
    recommended_technique: Optional[str]
    lead_temperature: str
    is_qualified: bool
    qualification_signals: Dict[str, Any]
    total_segments: int
    customer_segments: int
    avg_customer_response_length: float
    processing_latency_ms: float


class CallEventResponse(BaseModel):
    success: bool
    event_type: str
    call_id: str
    message: str
    analysis: Optional[Dict[str, Any]] = None
    actions: List[Dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/webhook")
async def process_vapi_webhook(request: Request) -> CallEventResponse:
    """Process a Vapi.ai webhook event (call started, ended, transcript, etc.)."""
    try:
        event_data = await request.json()
        intelligence = get_voice_intelligence()
        result = await intelligence.process_call_event(event_data)

        analysis_dict = None
        if result.analysis:
            a = result.analysis
            analysis_dict = {
                "composite_score": a.composite_score,
                "lead_temperature": a.lead_temperature,
                "is_qualified": a.is_qualified,
                "qualification_signals": a.qualification_signals,
                "drift_direction": a.drift_direction,
                "recommended_technique": a.recommended_technique,
                "processing_latency_ms": a.processing_latency_ms,
            }

        return CallEventResponse(
            success=result.success,
            event_type=result.event_type,
            call_id=result.call_id,
            message=result.message,
            analysis=analysis_dict,
            actions=result.actions,
        )
    except Exception as e:
        logger.error("Vapi webhook processing failed: %s", e)
        raise HTTPException(500, f"Voice intelligence error: {e}")


@router.post("/analyze-transcript", response_model=TranscriptAnalysisResponse)
async def analyze_transcript(request: AnalyzeTranscriptRequest):
    """Analyze a completed call transcript for qualification signals."""
    try:
        intelligence = get_voice_intelligence()
        segments = [
            TranscriptSegment(
                role=s.role,
                text=s.text,
                timestamp_ms=s.timestamp_ms,
                confidence=s.confidence,
            )
            for s in request.transcript_segments
        ]

        result = await intelligence.analyze_transcript(
            contact_id=request.contact_id,
            call_id=request.call_id,
            transcript_segments=segments,
            call_duration_seconds=request.call_duration_seconds,
        )

        return TranscriptAnalysisResponse(
            contact_id=result.contact_id,
            call_id=result.call_id,
            composite_score=result.composite_score,
            hedging_score=result.hedging_score,
            commitment_score=result.commitment_score,
            urgency_score=result.urgency_score,
            drift_direction=result.drift_direction,
            recommended_technique=result.recommended_technique,
            lead_temperature=result.lead_temperature,
            is_qualified=result.is_qualified,
            qualification_signals=result.qualification_signals,
            total_segments=result.total_segments,
            customer_segments=result.customer_segments,
            avg_customer_response_length=result.avg_customer_response_length,
            processing_latency_ms=result.processing_latency_ms,
        )
    except Exception as e:
        logger.error("Transcript analysis failed: %s", e)
        raise HTTPException(500, f"Transcript analysis error: {e}")


@router.get("/health")
async def voice_intelligence_health():
    """Health check for the voice intelligence service."""
    try:
        intelligence = get_voice_intelligence()
        return {
            "status": "healthy",
            "service": "vapi_voice_intelligence",
            "active_calls": len(intelligence._active_calls),
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
