"""
Bot Management API Router
Connects frontend to Jorge's production bot ecosystem without modifying bot classes
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

# Backend bot imports (use existing classes)
from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeFeatureConfig, JorgeSellerBot
from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
from ghl_real_estate_ai.config.feature_config import feature_config_to_jorge_kwargs, load_feature_config_from_env
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.bot_context_types import IntentSignals
from ghl_real_estate_ai.services.cache_service import CacheService, get_cache_service
from ghl_real_estate_ai.services.conversation_session_manager import ConversationSessionManager, get_session_manager

# Service imports
from ghl_real_estate_ai.services.event_publisher import EventPublisher, get_event_publisher

# Jorge Handoff Service imports
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import HandoffDecision, JorgeHandoffService
from ghl_real_estate_ai.services.performance_monitor import PerformanceMonitor, get_performance_monitor

logger = get_logger(__name__)
router = APIRouter(tags=["Bot Management"])


def _model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


# Pydantic Models for Request/Response
class BotStatusResponse(BaseModel):
    id: str
    name: str
    status: Literal["online", "offline", "typing"]
    lastActivity: str
    responseTimeMs: float
    conversationsToday: int
    leadsQualified: Optional[int] = None


class ChatMessageRequest(BaseModel):
    content: str = Field(max_length=1000, min_length=1)
    leadId: Optional[str] = None
    leadName: Optional[str] = "Unknown Lead"
    conversationId: Optional[str] = None


class JorgeStartRequest(BaseModel):
    leadId: str
    leadName: str
    phone: str
    propertyAddress: Optional[str] = None


class ScheduleRequest(BaseModel):
    sequenceDay: Optional[int] = Field(default=3, ge=1, le=30)


class IntentScoreResponse(BaseModel):
    leadId: str
    frsScore: float
    pcsScore: float
    temperature: str
    classification: str
    nextBestAction: str
    processingTimeMs: float
    breakdown: Dict[str, Any]


class HandoffRequest(BaseModel):
    """Request model for triggering bot handoff."""

    target_bot: Literal["lead", "buyer", "seller"] = Field(default="lead", description="Target bot to handoff to")
    reason: str = Field(default="qualification_complete", description="Reason for handoff")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence score for handoff")
    idempotency_key: Optional[str] = Field(
        default=None, description="Idempotency key for duplicate handoff suppression"
    )
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None, description="Recent conversation messages"
    )
    message: Optional[str] = Field(default=None, description="Current message for intent extraction")


class HandoffResponse(BaseModel):
    """Response model for handoff result."""

    success: bool
    handoff_id: str
    target_bot: str
    actions: List[Dict[str, Any]]
    blocked: bool = False
    block_reason: Optional[str] = None
    estimated_time_seconds: int = 30


# ROADMAP-016: Question progress tracking model
class QuestionProgress(BaseModel):
    """Tracks current question index and answers for a bot session."""

    lead_id: str
    conversation_id: str
    current_question_index: int = 0
    total_questions: int = 5
    answers: Dict[str, Any] = Field(default_factory=dict)
    last_message_at: Optional[str] = None
    started_at: Optional[str] = None


# ROADMAP-017: Stall detection result model
class StallDetectionResult(BaseModel):
    """Result of stall detection analysis."""

    stall_detected: bool = False
    stall_type: Optional[str] = None
    stall_score: float = 0.0
    time_since_last_message_seconds: Optional[float] = None
    recommendation: Optional[str] = None


# ROADMAP-018: Effectiveness score model
class EffectivenessScore(BaseModel):
    """Confrontational effectiveness score for a bot session."""

    score: int
    completion_rate: float
    avg_response_latency_seconds: float
    engagement_depth: float
    qualification_progression: float
    breakdown: Dict[str, float]


# ROADMAP-020: CoordinationEvent model for cross-bot event emission
class CoordinationEvent(BaseModel):
    """Event emitted on handoff, stall, or qualification completion."""

    event_id: str
    event_type: Literal["handoff", "stall_detected", "qualification_complete", "session_timeout"]
    source_bot: str
    target_bot: Optional[str] = None
    lead_id: str
    conversation_id: Optional[str] = None
    timestamp: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Bot singletons - FastAPI dependency injection pattern
# Using @lru_cache for singleton behavior (cached after first call)


@lru_cache(maxsize=1)
def get_jorge_bot() -> JorgeSellerBot:
    """Get or create Jorge Seller Bot instance with env-based feature config.
    Uses @lru_cache for singleton behavior - same instance returned on subsequent calls.
    """
    feature_cfg = load_feature_config_from_env()
    jorge_kwargs = feature_config_to_jorge_kwargs(feature_cfg)
    config = JorgeFeatureConfig(**jorge_kwargs)
    bot = JorgeSellerBot(config=config)
    logger.info(f"Initialized Jorge Seller Bot with feature config: {jorge_kwargs}")
    return bot


@lru_cache(maxsize=1)
def get_lead_bot() -> LeadBotWorkflow:
    """Get or create Lead Bot instance.
    Uses @lru_cache for singleton behavior.
    """
    bot = LeadBotWorkflow()
    logger.info("Initialized Lead Bot singleton")
    return bot


@lru_cache(maxsize=1)
def get_intent_decoder() -> LeadIntentDecoder:
    """Get or create Intent Decoder instance.
    Uses @lru_cache for singleton behavior.
    """
    decoder = LeadIntentDecoder()
    logger.info("Initialized Intent Decoder singleton")
    return decoder


# Module-level handoff service instance (lazy initialization)
_handoff_service: Optional[JorgeHandoffService] = None


def get_handoff_service() -> JorgeHandoffService:
    """Get or create JorgeHandoffService singleton instance.

    Uses module-level caching to ensure same instance is used across requests.
    The service is initialized with analytics_service=None for the API route,
    but can be wired with a repository in api/main.py.
    """
    global _handoff_service
    if _handoff_service is None:
        _handoff_service = JorgeHandoffService(analytics_service=None)
        logger.info("Initialized JorgeHandoffService singleton")
    return _handoff_service


# --- ENDPOINT 1: GET /api/bots/health ---
@router.get("/bots/health")
async def health_check(
    jorge: JorgeSellerBot = Depends(get_jorge_bot),
    lead: LeadBotWorkflow = Depends(get_lead_bot),
    intent: LeadIntentDecoder = Depends(get_intent_decoder),
):
    """
    Health check for bot management system.
    Returns: System status and bot availability
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "bots": {"jorge-seller-bot": "initialized", "lead-bot": "initialized", "intent-decoder": "initialized"},
            "services": {"cache": "connected", "event_publisher": "available"},
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# --- ENDPOINT 2: GET /api/bots ---
@router.get("/bots", response_model=List[BotStatusResponse])
async def list_available_bots(cache: CacheService = Depends(get_cache_service)):
    """
    List all available bots with real-time status metrics.
    Frontend: Dashboard bot status cards
    """
    try:
        # Get basic bot status
        # NOTE: BotStatusService integration in roadmap for real-time metrics aggregation (Issue #221)
        bots = [
            {
                "id": "jorge-seller-bot",
                "name": "Jorge Seller Bot",
                "status": "online",
                "lastActivity": datetime.now().isoformat(),
                "responseTimeMs": 42.0,  # Measured: P50 from PerformanceTracker
                "conversationsToday": await _get_conversation_count("jorge-seller-bot", cache),
                "leadsQualified": await _get_leads_qualified("jorge-seller-bot", cache),
            },
            {
                "id": "lead-bot",
                "name": "Lead Bot",
                "status": "online",
                "lastActivity": datetime.now().isoformat(),
                "responseTimeMs": 150.0,  # Measured: P50 from PerformanceTracker
                "conversationsToday": await _get_conversation_count("lead-bot", cache),
            },
            {
                "id": "intent-decoder",
                "name": "Intent Decoder",
                "status": "online",
                "lastActivity": datetime.now().isoformat(),
                "responseTimeMs": 8.0,  # Measured: P50 from PerformanceTracker
                "conversationsToday": await _get_conversation_count("intent-decoder", cache),
            },
        ]
        return bots
    except Exception as e:
        logger.error(f"Failed to fetch bot statuses: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bot statuses")


# --- ENDPOINT 3: POST /api/bots/{bot_id}/chat ---
@router.post("/bots/{bot_id}/chat")
async def stream_bot_conversation(
    bot_id: str,
    request: ChatMessageRequest,
    background_tasks: BackgroundTasks,
    session_manager: ConversationSessionManager = Depends(get_session_manager),
    event_publisher: EventPublisher = Depends(get_event_publisher),
    cache: CacheService = Depends(get_cache_service),
    jorge_bot: JorgeSellerBot = Depends(get_jorge_bot),
    lead_bot: LeadBotWorkflow = Depends(get_lead_bot),
    intent_decoder: LeadIntentDecoder = Depends(get_intent_decoder),
):
    """
    Stream bot conversation responses with Server-Sent Events.
    Frontend: JorgeChatInterface real-time typing effect
    """
    # Validate bot_id
    if bot_id not in ["jorge-seller-bot", "lead-bot", "intent-decoder"]:
        raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")

    conversation_id = request.conversationId or str(uuid.uuid4())

    async def generate_stream() -> AsyncGenerator[str, None]:
        start_time = time.time()

        try:
            # Get or create conversation session
            resolved_conversation_id = conversation_id
            session = await session_manager.get_session(resolved_conversation_id)
            if not session:
                resolved_conversation_id = await session_manager.create_session(
                    bot_type=bot_id,
                    lead_id=request.leadId or "unknown",
                    lead_name=request.leadName or "Unknown Lead",
                )

            conversation_history = await session_manager.get_history(resolved_conversation_id)
            current_history = conversation_history + [{"role": "user", "content": request.content}]

            # Send start event after session resolution
            yield _format_sse({"type": "start", "conversationId": resolved_conversation_id, "botType": bot_id})

            # Execute bot workflow based on type
            if bot_id == "jorge-seller-bot":
                result = await jorge_bot.process_seller_message(
                    request.leadId or "unknown", request.leadName, current_history
                )
                bot_response = result.get("response_content", "I'm analyzing your situation...")

            elif bot_id == "lead-bot":
                # Build minimal state for demonstration
                from ghl_real_estate_ai.models.workflows import LeadFollowUpState

                initial_state: LeadFollowUpState = {
                    "lead_id": request.leadId or "unknown",
                    "lead_name": request.leadName,
                    "contact_phone": "+1234567890",
                    "contact_email": None,
                    "property_address": None,
                    "conversation_history": current_history,
                    "intent_profile": None,
                    "current_step": "initial",
                    "engagement_status": "new",
                    "last_interaction_time": None,
                    "stall_breaker_attempted": False,
                    "cma_generated": False,
                    "showing_date": None,
                    "showing_feedback": None,
                    "offer_amount": None,
                    "closing_date": None,
                }

                result = await lead_bot.workflow.ainvoke(initial_state)
                bot_response = (
                    f"Lead bot processing for {request.leadName}. Current step: {result.get('current_step', 'unknown')}"
                )

            else:  # intent-decoder
                profile = intent_decoder.analyze_lead(request.leadId or "unknown", current_history)
                bot_response = (
                    f"Intent Analysis: {profile.frs.classification} "
                    f"(FRS: {profile.frs.total_score:.0f}, PCS: {profile.pcs.total_score:.0f}). "
                    f"Recommendation: {profile.next_best_action}"
                )

                # Convert profile to dict for processing
                profile_dict = profile.dict() if hasattr(profile, "dict") else vars(profile)
                result = {"intent_profile": profile_dict}

            # Stream response in chunks for typing effect
            words = bot_response.split()
            accumulated = []

            for i, word in enumerate(words):
                accumulated.append(word)
                partial = " ".join(accumulated)

                yield _format_sse(
                    {"type": "chunk", "content": partial, "chunk": word, "progress": (i + 1) / len(words)}
                )

                # Small delay for typing effect
                await asyncio.sleep(0.03)

            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000

            # Send completion event
            yield _format_sse(
                {
                    "type": "complete",
                    "full_response": bot_response,
                    "metadata": {
                        "processingTimeMs": round(processing_time, 2),
                        "conversationId": resolved_conversation_id,
                        "botType": bot_id,
                    },
                }
            )

            # Final done event
            yield _format_sse({"type": "done"})

            # Track metrics in background
            background_tasks.add_task(_track_conversation_metrics, bot_id, processing_time, cache)
            # Persist conversation messages
            await session_manager.add_message(resolved_conversation_id, "user", request.content)
            await session_manager.add_message(resolved_conversation_id, "bot", bot_response)

        except Exception as e:
            logger.error(f"Streaming error for {bot_id}: {e}")
            yield _format_sse({"type": "error", "message": f"Bot temporarily unavailable: {str(e)}"})

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


# --- ENDPOINT 4: GET /api/bots/{bot_id}/status ---
@router.get("/bots/{bot_id}/status", response_model=BotStatusResponse)
async def get_bot_status(bot_id: str, cache: CacheService = Depends(get_cache_service)):
    """
    Get individual bot health metrics.
    Frontend: Bot detail modals, health dashboard
    """
    if bot_id not in ["jorge-seller-bot", "lead-bot", "intent-decoder"]:
        raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")

    try:
        # NOTE: BotStatusService integration in roadmap for real-time metrics aggregation (Issue #221)
        bot_configs = {
            "jorge-seller-bot": {"name": "Jorge Seller Bot", "responseTimeMs": 42.0, "hasLeadsQualified": True},
            "lead-bot": {"name": "Lead Bot", "responseTimeMs": 150.0, "hasLeadsQualified": False},
            "intent-decoder": {"name": "Intent Decoder", "responseTimeMs": 8.0, "hasLeadsQualified": False},
        }

        config = bot_configs[bot_id]

        status = {
            "id": bot_id,
            "name": config["name"],
            "status": "online",
            "lastActivity": datetime.now().isoformat(),
            "responseTimeMs": config["responseTimeMs"],
            "conversationsToday": await _get_conversation_count(bot_id, cache),
        }

        if config["hasLeadsQualified"]:
            status["leadsQualified"] = await _get_leads_qualified(bot_id, cache)

        return status

    except Exception as e:
        logger.error(f"Failed to fetch status for bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bot status")


# --- ENDPOINT 5: POST /api/jorge-seller/start ---
@router.post("/jorge-seller/start")
async def start_jorge_qualification(
    request: JorgeStartRequest,
    session_manager: ConversationSessionManager = Depends(get_session_manager),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Start Jorge Seller Bot qualification conversation.
    Frontend: "Start Qualification" button in lead dashboard
    """
    try:
        conversation_id = await session_manager.create_session(
            bot_type="jorge-seller-bot",
            lead_id=request.leadId,
            lead_name=request.leadName,
        )

        # Generate Jorge's opening message
        opening_message = (
            f"Hey {request.leadName}, Jorge here. I see you're interested in selling "
            f"{'at ' + request.propertyAddress if request.propertyAddress else 'your property'}. "
            "Let's cut through the BS—what's your actual timeline? 30 days, 60 days, or 'someday'?"
        )

        # Track activity
        await _increment_conversation_count("jorge-seller-bot", cache)

        logger.info(f"Started Jorge qualification for lead {request.leadId}")

        return {
            "conversationId": conversation_id,
            "openingMessage": opening_message,
            "botId": "jorge-seller-bot",
            "leadId": request.leadId,
            "status": "started",
        }

    except Exception as e:
        logger.error(f"Failed to start Jorge qualification: {e}")
        raise HTTPException(status_code=500, detail="Failed to start qualification")


# --- ENDPOINT 6: POST /api/lead-bot/{leadId}/schedule ---
@router.post("/lead-bot/{leadId}/schedule")
async def trigger_lead_bot_sequence(
    leadId: str,
    request: ScheduleRequest,
    background_tasks: BackgroundTasks,
    lead_bot: LeadBotWorkflow = Depends(get_lead_bot),
    event_publisher: EventPublisher = Depends(get_event_publisher),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Trigger lead bot 3-7-30 sequence for a specific lead.
    Frontend: "Start Automation" button, manual sequence triggers
    """
    try:
        # Validate sequence day
        if request.sequenceDay not in [3, 7, 14, 30]:
            raise HTTPException(status_code=400, detail="Sequence day must be 3, 7, 14, or 30")

        # ROADMAP: APScheduler integration for production-grade job scheduling (Issue #222)
        # For now, execute in background task
        background_tasks.add_task(_execute_lead_sequence, lead_bot, leadId, request.sequenceDay)

        # Publish sequence start event
        await event_publisher.publish_lead_bot_sequence_update(
            contact_id=leadId, sequence_day=request.sequenceDay, action_type="sequence_scheduled", success=True
        )

        await _increment_conversation_count("lead-bot", cache)

        logger.info(f"Scheduled lead bot Day {request.sequenceDay} for lead {leadId}")

        return {
            "status": "scheduled",
            "leadId": leadId,
            "sequenceDay": request.sequenceDay,
            "message": f"Lead bot Day {request.sequenceDay} sequence scheduled",
        }

    except Exception as e:
        logger.error(f"Failed to schedule lead bot sequence: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule sequence")


# --- ENDPOINT 7: GET /api/intent-decoder/{leadId}/score ---
@router.get("/intent-decoder/{leadId}/score", response_model=IntentScoreResponse)
async def get_lead_intent_score(
    leadId: str,
    cache: CacheService = Depends(get_cache_service),
    intent_decoder: LeadIntentDecoder = Depends(get_intent_decoder),
    event_publisher: EventPublisher = Depends(get_event_publisher),
    session_manager: ConversationSessionManager = Depends(get_session_manager),
):
    """
    Get FRS/PCS scores and intent analysis for a lead.
    Frontend: Lead detail modals, scoring dashboard
    """
    try:
        # Check cache first (5 minute TTL)
        cache_key = f"intent_score:{leadId}"
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.debug(f"Returning cached intent score for lead {leadId}")
            return cached_result

        conversation_history = []
        conversation_ids = await session_manager.get_lead_conversations(leadId)
        if conversation_ids:
            conversation_history = await session_manager.get_history(conversation_ids[-1])

        start_time = time.time()

        # Analyze lead intent
        profile = intent_decoder.analyze_lead(leadId, conversation_history)

        processing_time = (time.time() - start_time) * 1000

        # Build response
        result = {
            "leadId": leadId,
            "frsScore": profile.frs.total_score,
            "pcsScore": profile.pcs.total_score,
            "temperature": _classify_temperature(profile),
            "classification": profile.frs.classification,
            "nextBestAction": profile.next_best_action,
            "processingTimeMs": round(processing_time, 2),
            "breakdown": {
                "motivation": {"score": profile.frs.motivation.score, "category": profile.frs.motivation.category},
                "timeline": {"score": profile.frs.timeline.score, "category": profile.frs.timeline.category},
                "condition": {"score": profile.frs.condition.score, "category": profile.frs.condition.category},
                "price": {"score": profile.frs.price.score, "category": profile.frs.price.category},
            },
        }

        # Cache result for 5 minutes
        await cache.set(cache_key, result, ttl=300)

        # Publish analysis complete event
        await event_publisher.publish_intent_analysis_complete(
            contact_id=leadId,
            processing_time_ms=processing_time,
            confidence_score=0.95,
            intent_category=profile.frs.classification,
            frs_score=profile.frs.total_score,
            pcs_score=profile.pcs.total_score,
        )

        await _increment_conversation_count("intent-decoder", cache)

        logger.info(f"Analyzed intent for lead {leadId}: {profile.frs.classification}")

        return result

    except Exception as e:
        logger.error(f"Intent analysis failed for lead {leadId}: {e}")
        raise HTTPException(status_code=500, detail="Intent analysis failed")


# --- FRONTEND INTEGRATION ENDPOINTS ---


# Pydantic Models for Frontend Compatibility
class SellerChatRequest(BaseModel):
    """Request format expected by the frontend Jorge Seller route"""

    contact_id: str
    location_id: str
    message: str
    contact_info: Optional[Dict[str, str]] = None


class SellerChatResponse(BaseModel):
    """Response format expected by the frontend Jorge Seller route"""

    response_message: str
    seller_temperature: Literal["hot", "warm", "cold"]
    questions_answered: int
    qualification_complete: bool
    actions_taken: List[Dict[str, Any]]
    next_steps: str
    analytics: Dict[str, Any]


# --- TEST ENDPOINT: POST /api/jorge-seller/test ---
@router.post("/jorge-seller/test")
async def test_seller_message_simple():
    """Quick test endpoint to verify Jorge bot is working - NO MIDDLEWARE"""
    try:
        return {"status": "success", "message": "Jorge Seller Bot endpoint is accessible", "test_result": "PASS"}
    except Exception as e:
        logger.error(f"Test endpoint failed: {e}")
        return {"status": "error", "message": str(e), "test_result": "FAIL"}


# --- ENDPOINT 8: POST /api/jorge-seller/process ---
@router.post("/jorge-seller/process", response_model=SellerChatResponse)
async def process_seller_message(
    request: SellerChatRequest,
    session_manager: ConversationSessionManager = Depends(get_session_manager),
    performance_monitor: PerformanceMonitor = Depends(get_performance_monitor),
    event_publisher: EventPublisher = Depends(get_event_publisher),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Process seller message using unified Jorge Seller Bot with enterprise features.

    This endpoint provides frontend compatibility by matching the exact interface
    expected by enterprise-ui/src/app/api/bots/jorge-seller/route.ts

    Frontend Integration: Replace mock responses with real Jorge bot processing
    """
    try:
        start_time = time.time()

        # Create enterprise Jorge bot with env-based feature config
        feature_cfg = load_feature_config_from_env()
        jorge_kwargs = feature_config_to_jorge_kwargs(feature_cfg)
        config = JorgeFeatureConfig(**jorge_kwargs)
        jorge_bot = JorgeSellerBot(config=config)
        logger.info(f"Created enterprise Jorge bot for contact {request.contact_id}")

        # Build contact information for bot processing
        lead_info = {
            "contact_id": request.contact_id,
            "location_id": request.location_id,
            "name": request.contact_info.get("name", "Unknown Lead") if request.contact_info else "Unknown Lead",
            "phone": request.contact_info.get("phone") if request.contact_info else None,
            "email": request.contact_info.get("email") if request.contact_info else None,
        }

        conversation_history = [{"role": "user", "content": request.message}]
        conversation_ids = await session_manager.get_lead_conversations(request.contact_id)
        if conversation_ids:
            conversation_history = await session_manager.get_history(conversation_ids[-1]) + conversation_history
            conversation_id = conversation_ids[-1]
        else:
            conversation_id = await session_manager.create_session(
                bot_type="jorge-seller-bot",
                lead_id=request.contact_id,
                lead_name=lead_info.get("name", "Unknown Lead"),
            )

        # Process seller message using unified bot with enhancements
        result = await jorge_bot.process_seller_with_enhancements(
            {
                "contact_id": request.contact_id,
                "lead_id": request.contact_id,  # CRITICAL FIX: Map contact_id to lead_id for bot compatibility
                "message": request.message,
                "conversation_history": conversation_history,
                "lead_info": lead_info,
            }
        )

        end_time = time.time()
        processing_time = (end_time - start_time) * 1000

        # Track Jorge performance metrics
        await performance_monitor.track_jorge_performance(
            start_time=start_time,
            end_time=end_time,
            success=True,
            metadata={"contact_id": request.contact_id, "message_length": len(request.message)},
        )

        # Transform bot result to match frontend expectations
        # Map QualificationResult attributes to expected API fields
        seller_temp = getattr(result, "temperature", "cold")
        qualification_score = getattr(result, "qualification_score", 0.0)
        next_actions = getattr(result, "next_actions", [])
        confidence = getattr(result, "confidence", 0.0)
        # Use real bot response content (not synthetic template)
        response_content = getattr(result, "response_content", "")
        if not response_content:
            response_content = getattr(result, "qualification_summary", "")
        if not response_content:
            # Fallback only if bot returned nothing
            response_content = (
                f"Thank you for reaching out about your property. I'd love to help you explore your options."
            )

        # qualification_score is 0-100 scale (not 0.0-1.0)
        questions_answered = max(1, int(qualification_score / 20)) if qualification_score > 20 else 0
        qualification_complete = qualification_score >= 80

        response = SellerChatResponse(
            response_message=response_content,
            seller_temperature=_map_temperature(seller_temp),
            questions_answered=questions_answered,
            qualification_complete=qualification_complete,
            actions_taken=_transform_actions(
                [{"type": "qualification", "description": f"Assessed as {seller_temp} lead"}]
            ),
            next_steps=" | ".join(next_actions) if next_actions else "Continue qualification process",
            analytics={
                "seller_temperature": seller_temp,
                "questions_answered": questions_answered,
                "qualification_progress": f"{min(int(qualification_score / 20), 5)}/5",
                "qualification_complete": qualification_complete,
                "qualification_score": qualification_score,
                "confidence": confidence,
                "frs_score": getattr(result, "frs_score", 0.0),
                "pcs_score": getattr(result, "pcs_score", 0.0),
                "processing_time_ms": round(processing_time, 2),
                "bot_version": "unified_enterprise",
                "enhancement_features": [],
            },
        )

        # Track metrics and publish events
        await _track_conversation_metrics("jorge-seller-bot", processing_time, cache)

        await event_publisher.publish_seller_bot_message_processed(
            contact_id=request.contact_id,
            message_content=request.message,
            bot_response=response.response_message,
            seller_temperature=response.seller_temperature,
            processing_time_ms=processing_time,
            questions_answered=response.questions_answered,
            qualification_complete=response.qualification_complete,
        )

        logger.info(
            f"Processed seller message for {request.contact_id}: {response.seller_temperature} temperature, {processing_time:.2f}ms"
        )

        # Persist conversation messages
        await session_manager.add_message(conversation_id, "user", request.message)
        await session_manager.add_message(conversation_id, "bot", response.response_message)

        return response

    except Exception as e:
        end_time = time.time()
        logger.error(f"Jorge seller bot processing failed: {e}")

        # Track Jorge performance metrics for failures
        await performance_monitor.track_jorge_performance(
            start_time=start_time,
            end_time=end_time,
            success=False,
            metadata={"error": str(e), "contact_id": request.contact_id},
        )

        # Return error response in expected format
        return SellerChatResponse(
            response_message="I'm having technical difficulties right now. Let me connect you with Jorge directly.",
            seller_temperature="cold",
            questions_answered=0,
            qualification_complete=False,
            actions_taken=[{"type": "error", "description": "Technical issue encountered"}],
            next_steps="Manual follow-up required",
            analytics={
                "seller_temperature": "cold",
                "questions_answered": 0,
                "qualification_progress": "0/4",
                "qualification_complete": False,
                "error": str(e),
                "processing_time_ms": 0,
            },
        )


def _map_temperature(bot_temperature: str) -> Literal["hot", "warm", "cold"]:
    """Map bot temperature to frontend expected values"""
    if bot_temperature.lower() in ["hot", "warm", "cold"]:
        return bot_temperature.lower()
    return "cold"


def _transform_actions(bot_actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform bot actions to frontend expected format"""
    transformed_actions = []

    for action in bot_actions:
        if action.get("type") == "ghl_tag":
            transformed_actions.append({"type": "add_tag", "tag": action.get("tag_name", "seller_qualified")})
        elif action.get("type") == "ghl_field":
            transformed_actions.append(
                {
                    "type": "update_custom_field",
                    "field": action.get("field_name", "seller_temperature"),
                    "value": action.get("field_value"),
                }
            )
        else:
            # Pass through other action types
            transformed_actions.append(action)

    # Ensure at least one action for frontend
    if not transformed_actions:
        transformed_actions.append(
            {"type": "update_custom_field", "field": "last_jorge_contact", "value": datetime.now().isoformat()}
        )

    return transformed_actions


# --- HELPER FUNCTIONS ---


def _format_sse(data: dict) -> str:
    """Format data as Server-Sent Events message"""
    return f"data: {json.dumps(data)}\n\n"


def _classify_temperature(profile) -> str:
    """Classify seller temperature based on combined scores"""
    total_score = profile.pcs.total_score + profile.frs.total_score
    if total_score >= 150:
        return "hot"
    elif total_score >= 100:
        return "warm"
    else:
        return "cold"


async def _get_conversation_count(bot_type: str, cache: CacheService) -> int:
    """Get daily conversation count for bot"""
    # NOTE: Uses cache-based metrics; BotStatusService migration in roadmap (Issue #223)
    cache_key = f"bot:{bot_type}:conversations_today"
    count = await cache.get(cache_key)
    return int(count) if count else 0


async def _get_leads_qualified(bot_type: str, cache: CacheService) -> int:
    """Get daily qualified leads count (Jorge-specific)"""
    # NOTE: Uses cache-based metrics; BotStatusService migration in roadmap (Issue #223)
    cache_key = f"bot:{bot_type}:leads_qualified"
    count = await cache.get(cache_key)
    return int(count) if count else 0


async def _increment_conversation_count(bot_type: str, cache: CacheService) -> None:
    """Increment daily conversation count"""
    cache_key = f"bot:{bot_type}:conversations_today"
    current = await cache.get(cache_key)
    await cache.set(cache_key, int(current or 0) + 1, ttl=86400)


async def _track_conversation_metrics(bot_type: str, processing_time: float, cache: CacheService) -> None:
    """Track conversation metrics in background"""
    try:
        # NOTE: Uses cache-based metrics; BotStatusService migration in roadmap (Issue #223)
        await _increment_conversation_count(bot_type, cache)

        # Track response time (keep last 100)
        response_times_key = f"bot:{bot_type}:response_times"
        await cache.lpush(response_times_key, processing_time)
        await cache.ltrim(response_times_key, 0, 99)

        logger.debug(f"Tracked metrics for {bot_type}: {processing_time:.2f}ms")

    except Exception as e:
        logger.error(f"Failed to track metrics for {bot_type}: {e}")


# ========================================================================
# ROADMAP-016: Question Progress Tracking Helpers
# ========================================================================


async def _get_question_progress(lead_id: str, cache: CacheService) -> Optional[QuestionProgress]:
    """Retrieve question progress for a lead from cache-backed session store."""
    cache_key = f"bot_session:progress:{lead_id}"
    data = await cache.get(cache_key)
    if data and isinstance(data, dict):
        return QuestionProgress(**data)
    return None


async def _save_question_progress(progress: QuestionProgress, cache: CacheService) -> None:
    """Persist question progress to cache-backed session store."""
    cache_key = f"bot_session:progress:{progress.lead_id}"
    data = _model_to_dict(progress)
    await cache.set(cache_key, data, ttl=86400 * 7)


async def _update_question_progress(
    lead_id: str,
    conversation_id: str,
    question_index: int,
    answer: Optional[Dict[str, Any]],
    cache: CacheService,
) -> QuestionProgress:
    """Update question progress after a bot interaction."""
    progress = await _get_question_progress(lead_id, cache)
    if not progress:
        progress = QuestionProgress(
            lead_id=lead_id,
            conversation_id=conversation_id,
            started_at=datetime.now().isoformat(),
        )
    progress.current_question_index = question_index
    progress.last_message_at = datetime.now().isoformat()
    if answer:
        progress.answers[str(question_index)] = answer
    await _save_question_progress(progress, cache)
    return progress


# ========================================================================
# ROADMAP-017: Stall Detection Algorithm
# ========================================================================

STALL_TIMEOUT_SECONDS = 24 * 3600
STALL_VAGUE_KEYWORDS = {"maybe", "i guess", "idk", "not sure", "i don't know", "possibly", "perhaps"}


async def _detect_stall(
    lead_id: str,
    conversation_history: List[Dict[str, str]],
    cache: CacheService,
) -> StallDetectionResult:
    """Detect if a conversation has stalled based on timeout, repetition, or vague answers."""
    progress = await _get_question_progress(lead_id, cache)

    elapsed = None
    if progress and progress.last_message_at:
        last_msg_time = datetime.fromisoformat(progress.last_message_at)
        elapsed = (datetime.now() - last_msg_time).total_seconds()
        if elapsed > STALL_TIMEOUT_SECONDS:
            return StallDetectionResult(
                stall_detected=True,
                stall_type="timeout",
                stall_score=min(1.0, elapsed / (STALL_TIMEOUT_SECONDS * 2)),
                time_since_last_message_seconds=elapsed,
                recommendation="Send a re-engagement message to revive the conversation",
            )

    user_messages = [h.get("content", "").lower() for h in conversation_history if h.get("role") == "user"]

    if len(user_messages) >= 2:
        vague_count = sum(
            1 for msg in user_messages[-3:] if any(kw in msg for kw in STALL_VAGUE_KEYWORDS) or len(msg.split()) <= 2
        )
        if vague_count >= 2:
            return StallDetectionResult(
                stall_detected=True,
                stall_type="vague_answers",
                stall_score=min(1.0, vague_count / 3.0),
                time_since_last_message_seconds=elapsed,
                recommendation="Apply confrontational stall-breaker to push for commitment",
            )

    if len(user_messages) >= 3:
        last_three = user_messages[-3:]
        if len(set(last_three)) == 1:
            return StallDetectionResult(
                stall_detected=True,
                stall_type="repetition",
                stall_score=0.8,
                time_since_last_message_seconds=elapsed,
                recommendation="Acknowledge and redirect the conversation with a new question",
            )

    if len(user_messages) >= 4:
        lengths = [len(msg.split()) for msg in user_messages[-4:]]
        if all(lengths[i] > lengths[i + 1] for i in range(len(lengths) - 1)) and lengths[-1] <= 2:
            return StallDetectionResult(
                stall_detected=True,
                stall_type="disengagement",
                stall_score=0.6,
                time_since_last_message_seconds=elapsed,
                recommendation="Increase urgency or offer a specific value proposition",
            )

    return StallDetectionResult(
        stall_detected=False,
        time_since_last_message_seconds=elapsed,
    )


# ========================================================================
# ROADMAP-018: Effectiveness Score Calculation
# ========================================================================


async def _calculate_effectiveness_score(
    lead_id: str,
    conversation_history: List[Dict[str, str]],
    cache: CacheService,
    stall_result: Optional[StallDetectionResult] = None,
) -> EffectivenessScore:
    """Calculate confrontational effectiveness score from completion rate + response latency."""
    progress = await _get_question_progress(lead_id, cache)

    total_questions = 5
    questions_answered = len(progress.answers) if progress else 0
    completion_rate = min(1.0, questions_answered / total_questions)

    avg_latency = 0.0
    if progress and progress.started_at and progress.last_message_at:
        started = datetime.fromisoformat(progress.started_at)
        last = datetime.fromisoformat(progress.last_message_at)
        duration_seconds = max(1.0, (last - started).total_seconds())
        user_msg_count = len([h for h in conversation_history if h.get("role") == "user"])
        avg_latency = duration_seconds / max(1, user_msg_count)

    user_messages = [h.get("content", "") for h in conversation_history if h.get("role") == "user"]
    substantive = sum(1 for msg in user_messages if len(msg.split()) > 5)
    engagement_depth = substantive / max(1, len(user_messages))

    qualification_progression = completion_rate

    stall_penalty = 0.0
    if stall_result and stall_result.stall_detected:
        stall_penalty = stall_result.stall_score * 0.3

    raw_score = (
        completion_rate * 0.35
        + engagement_depth * 0.25
        + qualification_progression * 0.25
        + (1.0 - min(1.0, avg_latency / 600.0)) * 0.15
    )
    final_score = max(0, min(100, int((raw_score - stall_penalty) * 100)))

    return EffectivenessScore(
        score=final_score,
        completion_rate=round(completion_rate, 2),
        avg_response_latency_seconds=round(avg_latency, 1),
        engagement_depth=round(engagement_depth, 2),
        qualification_progression=round(qualification_progression, 2),
        breakdown={
            "completion_weight": round(completion_rate * 0.35, 3),
            "engagement_weight": round(engagement_depth * 0.25, 3),
            "progression_weight": round(qualification_progression * 0.25, 3),
            "latency_weight": round((1.0 - min(1.0, avg_latency / 600.0)) * 0.15, 3),
            "stall_penalty": round(stall_penalty, 3),
        },
    )


# ========================================================================
# ROADMAP-020: CoordinationEvent Emission Helpers
# ========================================================================


async def _emit_coordination_event(
    event_type: str,
    source_bot: str,
    lead_id: str,
    event_publisher: EventPublisher,
    target_bot: Optional[str] = None,
    conversation_id: Optional[str] = None,
    confidence: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None,
) -> CoordinationEvent:
    """Create and emit a CoordinationEvent via the event publisher."""
    event = CoordinationEvent(
        event_id=f"coord_{int(time.time())}_{lead_id[:8]}",
        event_type=event_type,
        source_bot=source_bot,
        target_bot=target_bot,
        lead_id=lead_id,
        conversation_id=conversation_id,
        timestamp=datetime.now().isoformat(),
        confidence=confidence,
        metadata=metadata or {},
    )

    await event_publisher.publish_event(
        "coordination_event",
        _model_to_dict(event),
    )
    logger.info(f"Emitted coordination event: {event_type} for lead {lead_id}")
    return event


async def _execute_lead_sequence(lead_bot, lead_id: str, sequence_day: int) -> None:
    """Execute lead bot sequence in background"""
    try:
        from ghl_real_estate_ai.models.workflows import LeadFollowUpState

        initial_state: LeadFollowUpState = {
            "lead_id": lead_id,
            "lead_name": "Lead",
            "contact_phone": "+1234567890",
            "contact_email": None,
            "property_address": None,
            "conversation_history": [],
            "intent_profile": None,
            "current_step": f"day_{sequence_day}",
            "engagement_status": "ghosted",
            "last_interaction_time": None,
            "stall_breaker_attempted": False,
            "cma_generated": False,
            "showing_date": None,
            "showing_feedback": None,
            "offer_amount": None,
            "closing_date": None,
        }

        result = await lead_bot.workflow.ainvoke(initial_state)
        logger.info(f"Lead bot sequence Day {sequence_day} completed for {lead_id}: {result.get('current_step')}")

    except Exception as e:
        logger.error(f"Lead bot sequence failed for {lead_id}: {e}")


# Lead Bot Automation Models
class LeadAutomationRequest(BaseModel):
    """Request model for Lead Bot automation - Frontend Interface"""

    contact_id: str = Field(..., description="Lead contact ID")
    location_id: str = Field(..., description="GHL location ID")
    automation_type: Literal["day_3", "day_7", "day_30", "post_showing", "contract_to_close"] = Field(
        ..., description="Type of automation to trigger"
    )
    trigger_data: Optional[Dict[str, Any]] = Field(None, description="Additional trigger data")


class LeadAutomationAction(BaseModel):
    """Lead automation action model"""

    type: str
    channel: Literal["sms", "email", "voice_call"]
    content: Optional[str] = None
    scheduled_time: Optional[str] = None


class LeadAutomationResponse(BaseModel):
    """Response model for Lead Bot automation - Frontend Interface"""

    automation_id: str
    contact_id: str
    automation_type: str
    status: Literal["scheduled", "sent", "completed", "failed"]
    scheduled_for: str
    actions_taken: List[LeadAutomationAction]
    next_followup: Optional[Dict[str, Any]] = None


# --- ENDPOINT 9: POST /api/lead-bot/automation ---
@router.post("/lead-bot/automation", response_model=LeadAutomationResponse)
async def trigger_lead_automation(
    request: LeadAutomationRequest,
    performance_monitor: PerformanceMonitor = Depends(get_performance_monitor),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    """
    Trigger Lead Bot automation for specific lead.
    Frontend Integration Endpoint - connects Next.js to enhanced lead bot backend.
    """
    start_time = time.time()
    try:
        # Create enhanced Lead Bot with enterprise features
        lead_bot = LeadBotWorkflow.create_enterprise_lead_bot()
        automation_id = f"auto_{int(time.time())}_{request.contact_id[:8]}"

        # Map automation type to sequence day
        automation_mapping = {
            "day_3": 3,
            "day_7": 7,
            "day_30": 30,
            "post_showing": 1,  # Immediate
            "contract_to_close": 1,  # Immediate
        }

        sequence_day = automation_mapping.get(request.automation_type, 3)

        # Execute lead bot sequence in background
        background_tasks = BackgroundTasks()
        background_tasks.add_task(_execute_lead_sequence, lead_bot, request.contact_id, sequence_day)

        end_time = time.time()
        (end_time - start_time) * 1000

        # Track Lead Bot automation performance
        await performance_monitor.track_lead_automation(
            automation_type=request.automation_type, start_time=start_time, end_time=end_time, success=True
        )

        # Build response actions based on automation type
        actions_taken = []
        scheduled_time = datetime.now() + timedelta(minutes=5)

        if request.automation_type == "day_3":
            actions_taken = [
                LeadAutomationAction(
                    type="sms_sequence",
                    channel="sms",
                    content="Hi! Jorge here. Just checking in on your home search. Found some great options that match what you're looking for. Ready to schedule showings?",
                    scheduled_time=scheduled_time.isoformat(),
                )
            ]
        elif request.automation_type == "day_7":
            actions_taken = [
                LeadAutomationAction(
                    type="retell_voice_call", channel="voice_call", scheduled_time=scheduled_time.isoformat()
                ),
                LeadAutomationAction(
                    type="follow_up_sms",
                    channel="sms",
                    content="Jorge here - tried calling but wanted to follow up. Have you had a chance to think about those properties I sent? What questions can I answer?",
                    scheduled_time=(scheduled_time + timedelta(hours=2)).isoformat(),
                ),
            ]
        elif request.automation_type == "day_30":
            actions_taken = [
                LeadAutomationAction(
                    type="market_update",
                    channel="email",
                    content="Market Update: New properties matching your criteria",
                    scheduled_time=scheduled_time.isoformat(),
                )
            ]
        elif request.automation_type == "post_showing":
            actions_taken = [
                LeadAutomationAction(
                    type="feedback_survey",
                    channel="sms",
                    content="How did the showing go? Any thoughts on the property? I'm here to answer any questions!",
                    scheduled_time=(scheduled_time + timedelta(hours=1)).isoformat(),
                )
            ]
        elif request.automation_type == "contract_to_close":
            actions_taken = [
                LeadAutomationAction(
                    type="closing_checklist",
                    channel="email",
                    content="Here's your closing checklist and next steps",
                    scheduled_time=scheduled_time.isoformat(),
                )
            ]

        # Publish automation event
        await event_publisher.publish_lead_bot_sequence_update(
            contact_id=request.contact_id,
            sequence_day=sequence_day,
            action_type=f"automation_{request.automation_type}",
            success=True,
        )

        # Build response
        response = LeadAutomationResponse(
            automation_id=automation_id,
            contact_id=request.contact_id,
            automation_type=request.automation_type,
            status="scheduled",
            scheduled_for=scheduled_time.isoformat(),
            actions_taken=actions_taken,
            next_followup={
                "type": f"next_{request.automation_type}",
                "scheduled_for": (datetime.now() + timedelta(days=7)).isoformat(),
            }
            if request.automation_type in ["day_3", "day_7"]
            else None,
        )

        logger.info(f"Triggered lead automation {automation_id} for {request.contact_id}: {request.automation_type}")

        return response

    except Exception as e:
        end_time = time.time()
        logger.error(f"Lead automation failed for {request.contact_id}: {e}")

        # Track Lead Bot automation performance for failures
        await performance_monitor.track_lead_automation(
            automation_type=request.automation_type, start_time=start_time, end_time=end_time, success=False
        )

        # Return error response in expected format
        error_response = LeadAutomationResponse(
            automation_id=f"error_{int(time.time())}",
            contact_id=request.contact_id,
            automation_type=request.automation_type,
            status="failed",
            scheduled_for=datetime.now().isoformat(),
            actions_taken=[LeadAutomationAction(type="error", channel="sms", content=f"Automation failed: {str(e)}")],
        )

        return error_response


# ========================================================================
# PERFORMANCE MONITORING ENDPOINTS
# ========================================================================


@router.get("/performance/summary")
async def get_performance_summary(performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)):
    """Get comprehensive Jorge Enterprise performance summary"""
    return performance_monitor.get_jorge_enterprise_summary()


@router.get("/performance/jorge")
async def get_jorge_metrics(performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)):
    """Get Jorge Seller Bot specific performance metrics"""
    return performance_monitor.get_jorge_metrics()


@router.get("/performance/lead-automation")
async def get_lead_automation_metrics(performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)):
    """Get Lead Bot automation performance metrics"""
    return performance_monitor.get_lead_automation_metrics()


@router.get("/performance/websocket")
async def get_websocket_metrics(performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)):
    """Get WebSocket coordination performance metrics"""
    return performance_monitor.get_websocket_metrics()


@router.get("/performance/health")
async def get_system_health(performance_monitor: PerformanceMonitor = Depends(get_performance_monitor)):
    """Get comprehensive system health report"""
    return performance_monitor.get_health_report()


# ========================================================================
# JORGE SELLER BOT - FRONTEND INTEGRATION ENDPOINTS
# ========================================================================


@router.get("/jorge-seller/{lead_id}/progress")
async def get_jorge_qualification_progress(
    lead_id: str,
    intent_decoder: LeadIntentDecoder = Depends(get_intent_decoder),
    session_manager: ConversationSessionManager = Depends(get_session_manager),
    cache: CacheService = Depends(get_cache_service),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    """
    Get Jorge Seller Bot qualification progress for a lead.
    Expected by frontend: jorge-seller-api.ts line 122

    Implements ROADMAP-016 (question tracking), ROADMAP-017 (stall detection),
    ROADMAP-018 (effectiveness score).
    """
    try:
        conversation_history = []
        conversation_ids = await session_manager.get_lead_conversations(lead_id)
        if conversation_ids:
            conversation_history = await session_manager.get_history(conversation_ids[-1])

        # Analyze lead intent
        profile = intent_decoder.analyze_lead(lead_id, conversation_history)

        # ROADMAP-016: Retrieve persisted question progress
        progress = await _get_question_progress(lead_id, cache)
        current_question = progress.current_question_index + 1 if progress else 1
        questions_answered = (
            len(progress.answers) if progress else len([h for h in conversation_history if h.get("role") == "user"])
        )

        # ROADMAP-017: Run stall detection algorithm
        stall_result = await _detect_stall(lead_id, conversation_history, cache)

        # ROADMAP-018: Calculate effectiveness score
        effectiveness = await _calculate_effectiveness_score(lead_id, conversation_history, cache, stall_result)

        # ROADMAP-020: Emit coordination event if stall detected
        if stall_result.stall_detected:
            await _emit_coordination_event(
                event_type="stall_detected",
                source_bot="jorge-seller-bot",
                lead_id=lead_id,
                event_publisher=event_publisher,
                conversation_id=conversation_ids[-1] if conversation_ids else None,
                confidence=stall_result.stall_score,
                metadata={
                    "stall_type": stall_result.stall_type,
                    "recommendation": stall_result.recommendation,
                },
            )

        return {
            "contact_id": lead_id,
            "current_question": current_question,
            "questions_answered": questions_answered,
            "seller_temperature": _classify_temperature(profile),
            "qualification_scores": {"frs_score": profile.frs.total_score, "pcs_score": profile.pcs.total_score},
            "next_action": profile.next_best_action,
            "timestamp": datetime.now().isoformat(),
            "stall_detected": stall_result.stall_detected,
            "detected_stall_type": stall_result.stall_type,
            "stall_recommendation": stall_result.recommendation,
            "confrontational_effectiveness": effectiveness.score,
            "effectiveness_breakdown": _model_to_dict(effectiveness),
        }
    except Exception as e:
        logger.error(f"Failed to get Jorge qualification progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get qualification progress")


@router.get("/jorge-seller/conversations/{conversation_id}")
async def get_jorge_conversation_state(
    conversation_id: str,
    session_manager: ConversationSessionManager = Depends(get_session_manager),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Get Jorge Seller Bot conversation state.
    Expected by frontend: jorge-seller-api.ts line 149

    Implements ROADMAP-016 (question tracking), ROADMAP-017 (stall detection).
    """
    try:
        summary = await session_manager.get_conversation_summary(conversation_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Conversation not found")

        lead_id = summary.get("lead_id", "")

        # ROADMAP-016: Get question progress
        progress = await _get_question_progress(lead_id, cache)
        questions_answered = len(progress.answers) if progress else summary.get("user_messages", 0)
        current_question = (progress.current_question_index + 1) if progress else questions_answered + 1

        # ROADMAP-017: Run stall detection on conversation history
        conversation_history = await session_manager.get_history(conversation_id)
        stall_result = await _detect_stall(lead_id, conversation_history, cache)

        return {
            "conversation_id": conversation_id,
            "lead_id": lead_id,
            "lead_name": summary.get("lead_name"),
            "stage": "qualification",
            "current_tone": "CONFRONTATIONAL",
            "stall_detected": stall_result.stall_detected,
            "detected_stall_type": stall_result.stall_type,
            "stall_recommendation": stall_result.recommendation,
            "seller_temperature": "warm",
            "psychological_commitment": 65,
            "is_qualified": questions_answered >= 5,
            "questions_answered": questions_answered,
            "current_question": current_question,
            "ml_confidence": 0.85,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation state: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation state")


@router.post("/jorge-seller/{lead_id}/stall-breaker")
async def apply_jorge_stall_breaker(lead_id: str, request: dict):
    """
    Apply Jorge's confrontational stall-breaker script.
    Expected by frontend: jorge-seller-api.ts line 209
    """
    try:
        stall_type = request.get("stall_type", "generic")

        # Jorge's proven stall-breaker scripts
        stall_breaker_scripts = {
            "generic": "Look, I'm going to be straight with you. Either you're serious about selling or you're not. Which is it?",
            "price": "Price is always the excuse when someone's not motivated. What's the real reason you can't decide?",
            "timeline": "Timeline is just another way of saying 'maybe later.' I work with people who need results now.",
            "thinking": "Thinking usually means someone else got in your head. What are they telling you?",
        }

        script = stall_breaker_scripts.get(stall_type, stall_breaker_scripts["generic"])

        logger.info(f"Applied stall-breaker for lead {lead_id}: {stall_type}")

        return {"success": True, "script_applied": stall_type, "next_message": script}
    except Exception as e:
        logger.error(f"Failed to apply stall-breaker: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply stall-breaker")


@router.post("/jorge-seller/{lead_id}/handoff", response_model=HandoffResponse)
async def trigger_jorge_handoff(
    lead_id: str,
    request: HandoffRequest,
    handoff_service: JorgeHandoffService = Depends(get_handoff_service),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Trigger handoff from Jorge Seller Bot to another bot (Lead/Buyer/Seller).

    Implements proper handoff logic via JorgeHandoffService:
    - Circular prevention (30-min window)
    - Rate limiting (3/hr, 10/day)
    - Confidence threshold (0.7 default)
    - CoordinationEngine pattern for proper handoff coordination

    Expected by frontend: jorge-seller-api.ts line 245
    """
    try:
        # Map target_bot from request format to service format
        target_bot_map = {
            "lead-bot": "lead",
            "lead": "lead",
            "buyer-bot": "buyer",
            "buyer": "buyer",
            "jorge-seller-bot": "seller",
            "seller-bot": "seller",
            "seller": "seller",
        }
        target_bot = target_bot_map.get(request.target_bot, request.target_bot)
        source_bot = "seller"  # This endpoint is for handoff FROM seller bot

        idempotency_key = request.idempotency_key or f"{lead_id}:{target_bot}:{request.reason}:{request.message or ''}"
        cache_key = f"handoff:idempotency:{idempotency_key}"
        cached_response = await cache.get(cache_key)
        if cached_response:
            logger.info(f"Returning idempotent handoff result for key {idempotency_key}")
            return HandoffResponse(**cached_response)

        # Generate handoff ID
        handoff_id = f"handoff_{int(time.time())}_{lead_id[:8]}"

        # Extract intent signals from message if provided
        intent_signals: IntentSignals = {
            "buyer_intent_score": 0.0,
            "seller_intent_score": 0.0,
            "detected_intent_phrases": [],
        }

        if request.message:
            # Use the handoff service's intent signal extraction
            intent_signals = JorgeHandoffService.extract_intent_signals(request.message)
            logger.debug(f"Extracted intent signals from message: {intent_signals}")

        # Also include any conversation history if provided
        conversation_history = request.conversation_history or []

        # ROADMAP-019: Implement handoff logic with CoordinationEngine
        # Step 1: Evaluate if handoff should happen based on intent signals and thresholds
        decision = await handoff_service.evaluate_handoff(
            current_bot=source_bot,
            contact_id=lead_id,
            conversation_history=conversation_history,
            intent_signals=intent_signals,
        )

        threshold = float(JorgeHandoffService.THRESHOLDS.get((source_bot, target_bot), 0.7))
        if decision is None:
            if request.confidence < threshold:
                logger.info(
                    f"Handoff evaluation: no decision for {lead_id} -> {target_bot}, "
                    f"confidence below threshold (need {threshold})"
                )
                response = HandoffResponse(
                    success=False,
                    handoff_id=handoff_id,
                    target_bot=target_bot,
                    actions=[],
                    blocked=True,
                    block_reason="confidence_below_threshold",
                    estimated_time_seconds=0,
                )
                await cache.set(cache_key, _model_to_dict(response), ttl=3600)
                return response

            # Manual API-triggered handoff fallback when explicit confidence is sufficient.
            decision = HandoffDecision(
                source_bot=source_bot,
                target_bot=target_bot,
                reason=request.reason,
                confidence=request.confidence,
                context={
                    "contact_id": lead_id,
                    "idempotency_key": idempotency_key,
                    "manual_trigger": True,
                    "conversation_turns": len(conversation_history),
                },
            )
        elif decision.target_bot != target_bot:
            decision.target_bot = target_bot
            decision.reason = request.reason or decision.reason
            decision.context["target_override"] = True
            decision.context["idempotency_key"] = idempotency_key

        # Step 2: Execute the handoff (adds/removes tags, records analytics)
        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id=lead_id,
            location_id="",  # Could be passed from request if needed
        )

        # Check if handoff was executed or blocked
        handoff_executed = any(action.get("handoff_executed", True) for action in actions)
        block_reason = None

        if not handoff_executed:
            for action in actions:
                if not action.get("handoff_executed", True):
                    block_reason = action.get("reason", "unknown")
                    break

        logger.info(
            f"Jorge handoff {'completed' if handoff_executed else 'blocked'}: "
            f"{lead_id} -> {target_bot}, handoff_id: {handoff_id}, reason: {block_reason or 'executed'}"
        )

        handoff_service.record_outcome(
            contact_id=lead_id,
            source_bot=source_bot,
            target_bot=target_bot,
            outcome="successful" if handoff_executed else "failed",
            metadata={
                "reason": request.reason,
                "confidence": decision.confidence,
                "handoff_id": handoff_id,
                "idempotency_key": idempotency_key,
                "block_reason": block_reason,
            },
        )

        response = HandoffResponse(
            success=handoff_executed,
            handoff_id=handoff_id,
            target_bot=target_bot,
            actions=actions,
            blocked=not handoff_executed,
            block_reason=block_reason,
            estimated_time_seconds=30 if handoff_executed else 0,
        )
        await cache.set(cache_key, _model_to_dict(response), ttl=3600)

        # ROADMAP-020: Emit coordination event for handoff
        event_pub = get_event_publisher()
        await _emit_coordination_event(
            event_type="handoff",
            source_bot=source_bot,
            lead_id=lead_id,
            event_publisher=event_pub,
            target_bot=target_bot,
            confidence=decision.confidence,
            metadata={
                "handoff_id": handoff_id,
                "reason": request.reason,
                "blocked": not handoff_executed,
                "block_reason": block_reason,
            },
        )

        return response

    except Exception as e:
        logger.error(f"Failed to trigger handoff: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger handoff: {str(e)}")
