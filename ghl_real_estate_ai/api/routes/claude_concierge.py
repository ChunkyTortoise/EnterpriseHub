"""
Claude Concierge API Routes - Track 2 Omnipresent Intelligence
Provides RESTful API endpoints for the enhanced Claude Concierge system.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional, AsyncGenerator
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio

from ghl_real_estate_ai.services.claude_concierge_orchestrator import (
    ClaudeConciergeOrchestrator,
    get_claude_concierge_orchestrator,
    PlatformContext,
    ConciergeResponse,
    ConciergeMode,
    IntelligenceScope
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.api.auth import get_current_user
from ghl_real_estate_ai.api.models import User

logger = get_logger(__name__)
router = APIRouter(prefix="/api/claude-concierge", tags=["claude-concierge"])

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PlatformContextRequest(BaseModel):
    """Request model for platform context."""
    current_page: str
    user_role: str = "agent"
    session_id: str
    location_context: Dict[str, Any] = Field(default_factory=dict)

    # Business Intelligence
    active_leads: List[Dict[str, Any]] = Field(default_factory=list)
    bot_statuses: Dict[str, Any] = Field(default_factory=dict)
    user_activity: List[Dict[str, Any]] = Field(default_factory=list)
    business_metrics: Dict[str, Any] = Field(default_factory=dict)
    active_properties: List[Dict[str, Any]] = Field(default_factory=list)

    # Real-time Context
    market_conditions: Dict[str, Any] = Field(default_factory=dict)
    priority_actions: List[Dict[str, Any]] = Field(default_factory=list)
    pending_notifications: List[Dict[str, Any]] = Field(default_factory=list)

    # Jorge-specific Context
    jorge_preferences: Dict[str, Any] = Field(default_factory=dict)
    deal_pipeline_state: Dict[str, Any] = Field(default_factory=dict)
    commission_opportunities: List[Dict[str, Any]] = Field(default_factory=list)

    # Technical Context
    device_type: str = "desktop"
    connection_quality: str = "good"
    offline_capabilities: bool = False


class LiveGuidanceRequest(BaseModel):
    """Simplified request model for live guidance using real GHL data."""
    current_page: str
    user_role: str = "agent"
    session_id: Optional[str] = None
    mode: str = "proactive"
    scope: Optional[str] = None


class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    message: str = Field(..., max_length=1000, description="User message")
    conversation_id: Optional[str] = None
    platform_context: PlatformContextRequest
    mode: str = "reactive"  # proactive, reactive, presentation, field_work, executive
    streaming: bool = True

class CoachingRequest(BaseModel):
    """Request model for real-time coaching."""
    conversation_id: str
    current_situation: Dict[str, Any]
    urgency: str = "medium"  # low, medium, high, urgent
    platform_context: PlatformContextRequest

class BotHandoffRequest(BaseModel):
    """Request model for bot orchestration."""
    conversation_id: str
    target_bot: str  # jorge-seller, lead-bot, intent-decoder
    reason: str
    urgency: str = "scheduled"  # immediate, scheduled, background
    platform_context: PlatformContextRequest

class FieldAssistanceRequest(BaseModel):
    """Request model for mobile field assistance."""
    location_data: Dict[str, Any]
    platform_context: PlatformContextRequest

class PresentationSupportRequest(BaseModel):
    """Request model for client presentation support."""
    client_profile: Dict[str, Any]
    presentation_context: Dict[str, Any]
    platform_context: PlatformContextRequest

class LearningRequest(BaseModel):
    """Request model for learning from decisions."""
    decision: Dict[str, Any]
    outcome: Dict[str, Any]
    platform_context: PlatformContextRequest

class ConciergeResponseModel(BaseModel):
    """Response model for concierge responses."""
    primary_guidance: str
    urgency_level: str
    confidence_score: float

    immediate_actions: List[Dict[str, Any]]
    background_tasks: List[Dict[str, Any]]
    follow_up_reminders: List[Dict[str, Any]]

    page_specific_tips: List[str]
    bot_coordination_suggestions: List[Dict[str, Any]]
    revenue_optimization_ideas: List[Dict[str, Any]]

    risk_alerts: List[Dict[str, Any]]
    opportunity_highlights: List[Dict[str, Any]]
    learning_insights: List[Dict[str, Any]]

    response_time_ms: int
    data_sources_used: List[str]
    generated_at: datetime

class StreamChunk(BaseModel):
    """Model for streaming response chunks."""
    type: str  # 'content', 'metadata', 'complete'
    data: Any

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_concierge_orchestrator() -> ClaudeConciergeOrchestrator:
    """Get the Claude Concierge Orchestrator instance."""
    return get_claude_concierge_orchestrator()

def convert_platform_context(request: PlatformContextRequest) -> PlatformContext:
    """Convert request model to internal PlatformContext."""
    return PlatformContext(
        current_page=request.current_page,
        user_role=request.user_role,
        session_id=request.session_id,
        location_context=request.location_context,
        active_leads=request.active_leads,
        bot_statuses=request.bot_statuses,
        user_activity=request.user_activity,
        business_metrics=request.business_metrics,
        active_properties=request.active_properties,
        market_conditions=request.market_conditions,
        priority_actions=request.priority_actions,
        pending_notifications=request.pending_notifications,
        jorge_preferences=request.jorge_preferences,
        deal_pipeline_state=request.deal_pipeline_state,
        commission_opportunities=request.commission_opportunities,
        device_type=request.device_type,
        connection_quality=request.connection_quality,
        offline_capabilities=request.offline_capabilities
    )

def convert_concierge_response(response: ConciergeResponse) -> ConciergeResponseModel:
    """Convert internal response to API model."""
    return ConciergeResponseModel(
        primary_guidance=response.primary_guidance,
        urgency_level=response.urgency_level,
        confidence_score=response.confidence_score,
        immediate_actions=response.immediate_actions,
        background_tasks=response.background_tasks,
        follow_up_reminders=response.follow_up_reminders,
        page_specific_tips=response.page_specific_tips,
        bot_coordination_suggestions=response.bot_coordination_suggestions,
        revenue_optimization_ideas=response.revenue_optimization_ideas,
        risk_alerts=response.risk_alerts,
        opportunity_highlights=response.opportunity_highlights,
        learning_insights=response.learning_insights,
        response_time_ms=response.response_time_ms,
        data_sources_used=response.data_sources_used,
        generated_at=response.generated_at
    )

# ============================================================================
# CORE OMNIPRESENT INTELLIGENCE ENDPOINTS
# ============================================================================

@router.post("/contextual-guidance", response_model=ConciergeResponseModel)
async def generate_contextual_guidance(
    request: PlatformContextRequest,
    mode: str = "proactive",
    scope: Optional[str] = None,
    orchestrator: ClaudeConciergeOrchestrator = Depends(get_concierge_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """
    Generate intelligent contextual guidance based on current platform state.
    This is the main entry point for Track 2 omnipresent intelligence.
    """
    try:
        # Convert request to internal models
        platform_context = convert_platform_context(request)
        concierge_mode = ConciergeMode(mode)
        intelligence_scope = IntelligenceScope(scope) if scope else None

        # Generate contextual guidance
        response = await orchestrator.generate_contextual_guidance(
            context=platform_context,
            mode=concierge_mode,
            scope=intelligence_scope
        )

        # Convert and return response
        return convert_concierge_response(response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating contextual guidance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error generating guidance")


@router.post("/live-guidance", response_model=ConciergeResponseModel)
async def generate_live_guidance(
    request: LiveGuidanceRequest,
    orchestrator: ClaudeConciergeOrchestrator = Depends(get_concierge_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """
    Generate intelligent guidance using real-time GHL data.
    Track 3: Simplified endpoint that automatically connects to live business data.
    """
    try:
        # Convert mode and scope
        concierge_mode = ConciergeMode(request.mode)
        intelligence_scope = IntelligenceScope(request.scope) if request.scope else None

        # Generate guidance with live data
        response = await orchestrator.generate_live_guidance(
            current_page=request.current_page,
            mode=concierge_mode,
            user_role=request.user_role,
            session_id=request.session_id
        )

        # Convert to API response
        return ConciergeResponseModel(
            primary_guidance=response.primary_guidance,
            immediate_actions=response.immediate_actions,
            risk_alerts=response.risk_alerts,
            revenue_opportunities=response.revenue_opportunities,
            coaching_insights=response.coaching_insights,
            bot_coordination=response.bot_coordination,
            mobile_assistance=response.mobile_assistance,
            presentation_mode=response.presentation_mode,
            confidence_score=response.confidence_score,
            response_time_ms=response.response_time_ms,
            mode=response.mode.value,
            scope=response.scope.value
        )

    except Exception as e:
        logger.error(f"Error generating live guidance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error generating live guidance")


@router.post("/chat")
async def chat_with_concierge(
    request: ChatRequest,
    orchestrator: ClaudeConciergeOrchestrator = Depends(get_concierge_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """
    Interactive chat with the omnipresent concierge.
    Supports both streaming and non-streaming responses.
    """
    try:
        platform_context = convert_platform_context(request.platform_context)
        concierge_mode = ConciergeMode(request.mode)

        if request.streaming:
            # Return true streaming response
            async def generate_stream() -> AsyncGenerator[str, None]:
                try:
                    # Use real streaming from orchestrator
                    async for chunk in orchestrator.generate_contextual_guidance_stream(
                        context=platform_context,
                        mode=concierge_mode,
                        scope=IntelligenceScope.WORKFLOW
                    ):
                        chunk_data = StreamChunk(
                            type="content",
                            data={"content": chunk}
                        )
                        yield f"data: {json.dumps(chunk_data.dict())}\n\n"

                    # Signal completion
                    complete_chunk = StreamChunk(type="complete", data={})
                    yield f"data: {json.dumps(complete_chunk.dict())}\n\n"

                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    error_chunk = StreamChunk(
                        type="error",
                        data={"error": str(e)}
                    )
                    yield f"data: {json.dumps(error_chunk.dict())}\n\n"

            return StreamingResponse(
                generate_stream(),
                media_type="text/stream-events",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable nginx buffering
                }
            )
        else:
            # Return complete response
            response = await orchestrator.generate_contextual_guidance(
                context=platform_context,
                mode=concierge_mode,
                scope=IntelligenceScope.WORKFLOW
            )
            return convert_concierge_response(response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid chat parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error in chat with concierge: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in chat")

@router.post("/real-time-coaching", response_model=ConciergeResponseModel)
async def provide_real_time_coaching(
    request: CoachingRequest,
    orchestrator: ClaudeConciergeOrchestrator = Depends(get_concierge_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """
    Provide real-time coaching and guidance for specific situations.
    Used for immediate decision support and tactical guidance.
    """
    try:
        platform_context = convert_platform_context(request.platform_context)

        response = await orchestrator.provide_real_time_coaching(
            current_situation=request.current_situation,
            context=platform_context,
            urgency=request.urgency
        )

        return convert_concierge_response(response)

    except Exception as e:
        logger.error(f"Error providing real-time coaching: {e}")
        raise HTTPException(status_code=500, detail="Internal server error providing coaching")

@router.post("/bot-coordination", response_model=ConciergeResponseModel)
async def coordinate_bot_ecosystem(
    request: BotHandoffRequest,
    orchestrator: ClaudeConciergeOrchestrator = Depends(get_concierge_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """
    Coordinate the bot ecosystem for optimal outcomes.
    Provides bot orchestration recommendations and workflow optimization.
    """
    try:
        platform_context = convert_platform_context(request.platform_context)

        response = await orchestrator.coordinate_bot_ecosystem(
            context=platform_context,
            desired_outcome=f"Handoff to {request.target_bot}: {request.reason}"
        )

        return convert_concierge_response(response)

    except Exception as e:
        logger.error(f"Error coordinating bot ecosystem: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in bot coordination")

@router.post("/field-assistance", response_model=ConciergeResponseModel)
async def generate_mobile_field_assistance(
    request: FieldAssistanceRequest,
    orchestrator: ClaudeConciergeOrchestrator = Depends(get_concierge_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """
    Generate mobile-specific field assistance for property visits and client meetings.
    Optimized for mobile field work with offline capabilities.
    """
    try:
        platform_context = convert_platform_context(request.platform_context)

        response = await orchestrator.generate_mobile_field_assistance(
            location_data=request.location_data,
            context=platform_context
        )

        return convert_concierge_response(response)

    except Exception as e:
        logger.error(f"Error generating field assistance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in field assistance")

@router.post("/presentation-support", response_model=ConciergeResponseModel)
async def provide_client_presentation_support(
    request: PresentationSupportRequest,
    orchestrator: ClaudeConciergeOrchestrator = Depends(get_concierge_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """
    Provide intelligent support for client presentations with talking points and strategies.
    Client-safe mode ensures no sensitive internal information is exposed.
    """
    try:
        platform_context = convert_platform_context(request.platform_context)

        response = await orchestrator.provide_client_presentation_support(
            client_profile=request.client_profile,
            presentation_context=request.presentation_context,
            context=platform_context
        )

        return convert_concierge_response(response)

    except Exception as e:
        logger.error(f"Error providing presentation support: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in presentation support")

# ============================================================================
# JORGE MEMORY & LEARNING SYSTEM ENDPOINTS
# ============================================================================

@router.post("/learn-decision")
async def learn_from_user_decision(
    request: LearningRequest,
    background_tasks: BackgroundTasks,
    orchestrator: ClaudeConciergeOrchestrator = Depends(get_concierge_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """
    Learn from Jorge's decisions to improve future recommendations.
    This is a key part of the adaptive intelligence system.
    """
    try:
        platform_context = convert_platform_context(request.platform_context)

        # Process learning in background for performance
        background_tasks.add_task(
            orchestrator.learn_from_user_decision,
            platform_context,
            request.decision,
            request.outcome
        )

        return {"status": "learning_queued", "message": "Decision learning queued for processing"}

    except Exception as e:
        logger.error(f"Error queuing decision learning: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in learning system")

@router.post("/predict-preference")
async def predict_jorge_preference(
    situation: Dict[str, Any],
    request: PlatformContextRequest,
    orchestrator: ClaudeConciergeOrchestrator = Depends(get_concierge_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """
    Predict what Jorge would prefer in a given situation based on learned patterns.
    """
    try:
        platform_context = convert_platform_context(request)

        prediction = await orchestrator.predict_jorge_preference(
            situation=situation,
            context=platform_context
        )

        return {
            "prediction": prediction,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error predicting preference: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in preference prediction")

# ============================================================================
# PLATFORM INTEGRATION ENDPOINTS
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for the concierge service."""
    try:
        orchestrator = get_claude_concierge_orchestrator()
        # Basic health check - could be enhanced with more detailed checks

        return {
            "status": "healthy",
            "service": "claude_concierge_omnipresent",
            "version": "track_2",
            "timestamp": datetime.now().isoformat(),
            "features": {
                "contextual_guidance": True,
                "real_time_coaching": True,
                "bot_coordination": True,
                "field_assistance": True,
                "presentation_support": True,
                "jorge_memory_learning": True,
                "omnipresent_monitoring": True
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@router.get("/capabilities")
async def get_capabilities():
    """Get available capabilities and configuration."""
    return {
        "concierge_modes": [mode.value for mode in ConciergeMode],
        "intelligence_scopes": [scope.value for scope in IntelligenceScope],
        "supported_bots": ["jorge-seller", "lead-bot", "intent-decoder"],
        "coaching_types": [
            "response_optimization",
            "timing_adjustment",
            "strategy_pivot",
            "objection_handling",
            "temperature_escalation"
        ],
        "urgency_levels": ["low", "medium", "high", "urgent"],
        "device_types": ["desktop", "mobile", "tablet"],
        "connection_qualities": ["excellent", "good", "poor"],
        "user_roles": ["agent", "executive", "client"],
        "max_message_length": 1000,
        "streaming_enabled": True
    }

@router.get("/metrics")
async def get_orchestrator_metrics(
    orchestrator: ClaudeConciergeOrchestrator = Depends(get_concierge_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for the concierge orchestrator."""
    try:
        # This would need to be implemented in the orchestrator
        metrics = {
            "requests_processed": 0,
            "avg_response_time_ms": 0,
            "errors": 0,
            "cache_hit_rate": 0.0,
            "active_sessions": 0,
            "learning_events": 0,
            "timestamp": datetime.now().isoformat()
        }

        return metrics

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error getting metrics")

@router.post("/reset-session")
async def reset_concierge_session(
    session_id: str,
    orchestrator: ClaudeConciergeOrchestrator = Depends(get_concierge_orchestrator),
    current_user: User = Depends(get_current_user)
):
    """Reset a concierge session for debugging or user request."""
    try:
        # Clear session context and caches
        orchestrator.session_contexts.pop(session_id, None)

        return {
            "status": "session_reset",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error resetting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error resetting session")

# ============================================================================
# WEBSOCKET ENDPOINTS FOR REAL-TIME FEATURES
# ============================================================================

@router.websocket("/ws/{session_id}")
async def websocket_concierge(websocket, session_id: str):
    """
    WebSocket endpoint for real-time concierge communication.
    Supports omnipresent monitoring and live coaching.
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established for session {session_id}")

    try:
        orchestrator = get_claude_concierge_orchestrator()

        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})

            elif message_type == "context_update":
                # Handle real-time context updates
                platform_context_data = data.get("platform_context")
                if platform_context_data:
                    # Process context update
                    await websocket.send_json({
                        "type": "context_acknowledged",
                        "timestamp": datetime.now().isoformat()
                    })

            elif message_type == "request_guidance":
                # Handle real-time guidance requests
                try:
                    platform_context_data = data.get("platform_context")
                    mode = data.get("mode", "proactive")

                    if platform_context_data:
                        # Convert to internal model (simplified for WebSocket)
                        platform_context = PlatformContext(**platform_context_data)

                        response = await orchestrator.generate_contextual_guidance(
                            context=platform_context,
                            mode=ConciergeMode(mode)
                        )

                        await websocket.send_json({
                            "type": "guidance_response",
                            "data": {
                                "primary_guidance": response.primary_guidance,
                                "urgency_level": response.urgency_level,
                                "confidence_score": response.confidence_score,
                                "immediate_actions": response.immediate_actions
                            },
                            "timestamp": datetime.now().isoformat()
                        })

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error processing guidance request: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    })

    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        await websocket.close(code=1000)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}")
    return HTTPException(status_code=400, detail=str(exc))

@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled error in concierge API: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")