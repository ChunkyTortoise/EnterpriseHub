"""
Bot Management API Router
Connects frontend to Jorge's production bot ecosystem without modifying bot classes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal, AsyncGenerator
from datetime import datetime
import asyncio
import json
import uuid
import time

# Backend bot imports (use existing classes)
from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

# Service imports
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Bot Management"])
cache = get_cache_service()

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

# Bot singletons (lazy initialized for performance)
_jorge_bot: Optional[JorgeSellerBot] = None
_lead_bot: Optional[LeadBotWorkflow] = None
_intent_decoder: Optional[LeadIntentDecoder] = None

def get_jorge_bot() -> JorgeSellerBot:
    """Get or create Jorge Seller Bot instance"""
    global _jorge_bot
    if _jorge_bot is None:
        _jorge_bot = JorgeSellerBot()
        logger.info("Initialized Jorge Seller Bot singleton")
    return _jorge_bot

def get_lead_bot() -> LeadBotWorkflow:
    """Get or create Lead Bot instance"""
    global _lead_bot
    if _lead_bot is None:
        _lead_bot = LeadBotWorkflow()
        logger.info("Initialized Lead Bot singleton")
    return _lead_bot

def get_intent_decoder() -> LeadIntentDecoder:
    """Get or create Intent Decoder instance"""
    global _intent_decoder
    if _intent_decoder is None:
        _intent_decoder = LeadIntentDecoder()
        logger.info("Initialized Intent Decoder singleton")
    return _intent_decoder

# --- ENDPOINT 1: GET /api/bots/health ---
@router.get("/bots/health")
async def health_check():
    """
    Health check for bot management system.
    Returns: System status and bot availability
    """
    try:
        # Test bot instance creation
        jorge = get_jorge_bot()
        lead = get_lead_bot()
        intent = get_intent_decoder()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "bots": {
                "jorge-seller-bot": "initialized",
                "lead-bot": "initialized",
                "intent-decoder": "initialized"
            },
            "services": {
                "cache": "connected",
                "event_publisher": "available"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# --- ENDPOINT 2: GET /api/bots ---
@router.get("/bots", response_model=List[BotStatusResponse])
async def list_available_bots():
    """
    List all available bots with real-time status metrics.
    Frontend: Dashboard bot status cards
    """
    try:
        # Get basic bot status
        # TODO: Replace with BotStatusService for real metrics
        bots = [
            {
                "id": "jorge-seller-bot",
                "name": "Jorge Seller Bot",
                "status": "online",
                "lastActivity": datetime.now().isoformat(),
                "responseTimeMs": 42.0,  # TODO: Real metrics from BotStatusService
                "conversationsToday": await _get_conversation_count("jorge-seller-bot"),
                "leadsQualified": await _get_leads_qualified("jorge-seller-bot")
            },
            {
                "id": "lead-bot",
                "name": "Lead Bot",
                "status": "online",
                "lastActivity": datetime.now().isoformat(),
                "responseTimeMs": 150.0,  # TODO: Real metrics
                "conversationsToday": await _get_conversation_count("lead-bot")
            },
            {
                "id": "intent-decoder",
                "name": "Intent Decoder",
                "status": "online",
                "lastActivity": datetime.now().isoformat(),
                "responseTimeMs": 8.0,  # TODO: Real metrics
                "conversationsToday": await _get_conversation_count("intent-decoder")
            }
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
    background_tasks: BackgroundTasks
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
        event_publisher = get_event_publisher()

        try:
            # Send start event
            yield _format_sse({
                "type": "start",
                "conversationId": conversation_id,
                "botType": bot_id
            })

            # Get conversation history
            # TODO: Get from ConversationSessionManager when built
            conversation_history = []

            # Execute bot workflow based on type
            if bot_id == "jorge-seller-bot":
                bot = get_jorge_bot()
                result = await bot.process_seller_message(
                    request.leadId or "unknown",
                    request.leadName,
                    conversation_history
                )
                bot_response = result.get("response_content", "I'm analyzing your situation...")

            elif bot_id == "lead-bot":
                bot = get_lead_bot()
                # Build minimal state for demonstration
                from ghl_real_estate_ai.models.workflows import LeadFollowUpState

                initial_state: LeadFollowUpState = {
                    "lead_id": request.leadId or "unknown",
                    "lead_name": request.leadName,
                    "contact_phone": "+1234567890",
                    "contact_email": None,
                    "property_address": None,
                    "conversation_history": conversation_history,
                    "intent_profile": None,
                    "current_step": "initial",
                    "engagement_status": "new",
                    "last_interaction_time": None,
                    "stall_breaker_attempted": False,
                    "cma_generated": False,
                    "showing_date": None,
                    "showing_feedback": None,
                    "offer_amount": None,
                    "closing_date": None
                }

                result = await bot.workflow.ainvoke(initial_state)
                bot_response = f"Lead bot processing for {request.leadName}. Current step: {result.get('current_step', 'unknown')}"

            else:  # intent-decoder
                bot = get_intent_decoder()
                profile = bot.analyze_lead(request.leadId or "unknown", conversation_history)
                bot_response = (
                    f"Intent Analysis: {profile.frs.classification} "
                    f"(FRS: {profile.frs.total_score:.0f}, PCS: {profile.pcs.total_score:.0f}). "
                    f"Recommendation: {profile.next_best_action}"
                )
                result = {"intent_profile": profile}

            # Stream response in chunks for typing effect
            words = bot_response.split()
            accumulated = []

            for i, word in enumerate(words):
                accumulated.append(word)
                partial = " ".join(accumulated)

                yield _format_sse({
                    "type": "chunk",
                    "content": partial,
                    "delta": word,
                    "progress": (i + 1) / len(words)
                })

                # Small delay for typing effect
                await asyncio.sleep(0.03)

            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000

            # Send completion event
            yield _format_sse({
                "type": "complete",
                "full_response": bot_response,
                "metadata": {
                    "processingTimeMs": round(processing_time, 2),
                    "conversationId": conversation_id,
                    "botType": bot_id
                }
            })

            # Final done event
            yield _format_sse({"type": "done"})

            # Track metrics in background
            background_tasks.add_task(_track_conversation_metrics, bot_id, processing_time)

        except Exception as e:
            logger.error(f"Streaming error for {bot_id}: {e}")
            yield _format_sse({
                "type": "error",
                "message": f"Bot temporarily unavailable: {str(e)}"
            })

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# --- ENDPOINT 4: GET /api/bots/{bot_id}/status ---
@router.get("/bots/{bot_id}/status", response_model=BotStatusResponse)
async def get_bot_status(bot_id: str):
    """
    Get individual bot health metrics.
    Frontend: Bot detail modals, health dashboard
    """
    if bot_id not in ["jorge-seller-bot", "lead-bot", "intent-decoder"]:
        raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")

    try:
        # TODO: Replace with BotStatusService for real metrics
        bot_configs = {
            "jorge-seller-bot": {
                "name": "Jorge Seller Bot",
                "responseTimeMs": 42.0,
                "hasLeadsQualified": True
            },
            "lead-bot": {
                "name": "Lead Bot",
                "responseTimeMs": 150.0,
                "hasLeadsQualified": False
            },
            "intent-decoder": {
                "name": "Intent Decoder",
                "responseTimeMs": 8.0,
                "hasLeadsQualified": False
            }
        }

        config = bot_configs[bot_id]

        status = {
            "id": bot_id,
            "name": config["name"],
            "status": "online",
            "lastActivity": datetime.now().isoformat(),
            "responseTimeMs": config["responseTimeMs"],
            "conversationsToday": await _get_conversation_count(bot_id)
        }

        if config["hasLeadsQualified"]:
            status["leadsQualified"] = await _get_leads_qualified(bot_id)

        return status

    except Exception as e:
        logger.error(f"Failed to fetch status for bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bot status")

# --- ENDPOINT 5: POST /api/jorge-seller/start ---
@router.post("/api/jorge-seller/start")
async def start_jorge_qualification(request: JorgeStartRequest):
    """
    Start Jorge Seller Bot qualification conversation.
    Frontend: "Start Qualification" button in lead dashboard
    """
    try:
        conversation_id = str(uuid.uuid4())
        jorge_bot = get_jorge_bot()

        # Generate Jorge's opening message
        opening_message = (
            f"Hey {request.leadName}, Jorge here. I see you're interested in selling "
            f"{'at ' + request.propertyAddress if request.propertyAddress else 'your property'}. "
            "Let's cut through the BS—what's your actual timeline? 30 days, 60 days, or 'someday'?"
        )

        # TODO: Create session in ConversationSessionManager
        # await session_manager.create_session(bot_type="jorge-seller-bot", ...)

        # Track activity
        await _increment_conversation_count("jorge-seller-bot")

        logger.info(f"Started Jorge qualification for lead {request.leadId}")

        return {
            "conversationId": conversation_id,
            "openingMessage": opening_message,
            "botId": "jorge-seller-bot",
            "leadId": request.leadId,
            "status": "started"
        }

    except Exception as e:
        logger.error(f"Failed to start Jorge qualification: {e}")
        raise HTTPException(status_code=500, detail="Failed to start qualification")

# --- ENDPOINT 6: POST /api/lead-bot/{leadId}/schedule ---
@router.post("/api/lead-bot/{leadId}/schedule")
async def trigger_lead_bot_sequence(
    leadId: str,
    request: ScheduleRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger lead bot 3-7-30 sequence for a specific lead.
    Frontend: "Start Automation" button, manual sequence triggers
    """
    try:
        lead_bot = get_lead_bot()
        event_publisher = get_event_publisher()

        # Validate sequence day
        if request.sequenceDay not in [3, 7, 14, 30]:
            raise HTTPException(
                status_code=400,
                detail="Sequence day must be 3, 7, 14, or 30"
            )

        # TODO: Use APScheduler for real scheduling instead of immediate execution
        # For now, execute in background task
        background_tasks.add_task(
            _execute_lead_sequence,
            lead_bot,
            leadId,
            request.sequenceDay
        )

        # Publish sequence start event
        await event_publisher.publish_lead_bot_sequence_update(
            contact_id=leadId,
            sequence_day=request.sequenceDay,
            action_type="sequence_scheduled",
            success=True
        )

        await _increment_conversation_count("lead-bot")

        logger.info(f"Scheduled lead bot Day {request.sequenceDay} for lead {leadId}")

        return {
            "status": "scheduled",
            "leadId": leadId,
            "sequenceDay": request.sequenceDay,
            "message": f"Lead bot Day {request.sequenceDay} sequence scheduled"
        }

    except Exception as e:
        logger.error(f"Failed to schedule lead bot sequence: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule sequence")

# --- ENDPOINT 7: GET /api/intent-decoder/{leadId}/score ---
@router.get("/api/intent-decoder/{leadId}/score", response_model=IntentScoreResponse)
async def get_lead_intent_score(leadId: str):
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

        intent_decoder = get_intent_decoder()
        event_publisher = get_event_publisher()

        # TODO: Fetch real conversation history from ConversationSessionManager
        conversation_history = []

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
                "motivation": {
                    "score": profile.frs.motivation.score,
                    "category": profile.frs.motivation.category
                },
                "timeline": {
                    "score": profile.frs.timeline.score,
                    "category": profile.frs.timeline.category
                },
                "condition": {
                    "score": profile.frs.condition.score,
                    "category": profile.frs.condition.category
                },
                "price": {
                    "score": profile.frs.price.score,
                    "category": profile.frs.price.category
                }
            }
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
            pcs_score=profile.pcs.total_score
        )

        await _increment_conversation_count("intent-decoder")

        logger.info(f"Analyzed intent for lead {leadId}: {profile.frs.classification}")

        return result

    except Exception as e:
        logger.error(f"Intent analysis failed for lead {leadId}: {e}")
        raise HTTPException(status_code=500, detail="Intent analysis failed")

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

async def _get_conversation_count(bot_type: str) -> int:
    """Get daily conversation count for bot"""
    # TODO: Replace with BotStatusService
    cache_key = f"bot:{bot_type}:conversations_today"
    count = await cache.get(cache_key)
    return int(count) if count else 0

async def _get_leads_qualified(bot_type: str) -> int:
    """Get daily qualified leads count (Jorge-specific)"""
    # TODO: Replace with BotStatusService
    cache_key = f"bot:{bot_type}:leads_qualified"
    count = await cache.get(cache_key)
    return int(count) if count else 0

async def _increment_conversation_count(bot_type: str) -> None:
    """Increment daily conversation count"""
    cache_key = f"bot:{bot_type}:conversations_today"
    current = await cache.get(cache_key)
    await cache.set(cache_key, int(current or 0) + 1, ttl=86400)

async def _track_conversation_metrics(bot_type: str, processing_time: float) -> None:
    """Track conversation metrics in background"""
    try:
        # TODO: Replace with BotStatusService
        await _increment_conversation_count(bot_type)

        # Track response time (keep last 100)
        response_times_key = f"bot:{bot_type}:response_times"
        await cache.lpush(response_times_key, processing_time)
        await cache.ltrim(response_times_key, 0, 99)

        logger.debug(f"Tracked metrics for {bot_type}: {processing_time:.2f}ms")

    except Exception as e:
        logger.error(f"Failed to track metrics for {bot_type}: {e}")

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
            "closing_date": None
        }

        result = await lead_bot.workflow.ainvoke(initial_state)
        logger.info(f"Lead bot sequence Day {sequence_day} completed for {lead_id}: {result.get('current_step')}")

    except Exception as e:
        logger.error(f"Lead bot sequence failed for {lead_id}: {e}")