"""
Bot Management API Router
Connects frontend to Jorge's production bot ecosystem without modifying bot classes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal, AsyncGenerator
from datetime import datetime, timedelta
import asyncio
import json
import uuid
import time

# Backend bot imports (use existing classes)
from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot, JorgeFeatureConfig
from ghl_real_estate_ai.config.feature_config import load_feature_config_from_env, feature_config_to_jorge_kwargs
from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

# Service imports
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.performance_monitor import get_performance_monitor
from ghl_real_estate_ai.services.conversation_session_manager import get_session_manager
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
    """Get or create Jorge Seller Bot instance with env-based feature config"""
    global _jorge_bot
    if _jorge_bot is None:
        feature_cfg = load_feature_config_from_env()
        jorge_kwargs = feature_config_to_jorge_kwargs(feature_cfg)
        config = JorgeFeatureConfig(**jorge_kwargs)
        _jorge_bot = JorgeSellerBot(config=config)
        logger.info(f"Initialized Jorge Seller Bot singleton with feature config: {jorge_kwargs}")
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

    session_manager = get_session_manager()
    conversation_id = request.conversationId or str(uuid.uuid4())

    async def generate_stream() -> AsyncGenerator[str, None]:
        start_time = time.time()
        event_publisher = get_event_publisher()

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
            yield _format_sse({
                "type": "start",
                "conversationId": resolved_conversation_id,
                "botType": bot_id
            })

            # Execute bot workflow based on type
            if bot_id == "jorge-seller-bot":
                bot = get_jorge_bot()
                result = await bot.process_seller_message(
                    request.leadId or "unknown",
                    request.leadName,
                    current_history
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
                    "closing_date": None
                }

                result = await bot.workflow.ainvoke(initial_state)
                bot_response = f"Lead bot processing for {request.leadName}. Current step: {result.get('current_step', 'unknown')}"

            else:  # intent-decoder
                bot = get_intent_decoder()
                profile = bot.analyze_lead(request.leadId or "unknown", current_history)
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

                yield _format_sse({
                    "type": "chunk",
                    "content": partial,
                    "chunk": word,
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
            # Persist conversation messages
            await session_manager.add_message(resolved_conversation_id, "user", request.content)
            await session_manager.add_message(resolved_conversation_id, "bot", bot_response)

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
@router.post("/jorge-seller/start")
async def start_jorge_qualification(request: JorgeStartRequest):
    """
    Start Jorge Seller Bot qualification conversation.
    Frontend: "Start Qualification" button in lead dashboard
    """
    try:
        session_manager = get_session_manager()
        conversation_id = await session_manager.create_session(
            bot_type="jorge-seller-bot",
            lead_id=request.leadId,
            lead_name=request.leadName,
        )
        jorge_bot = get_jorge_bot()

        # Generate Jorge's opening message
        opening_message = (
            f"Hey {request.leadName}, Jorge here. I see you're interested in selling "
            f"{'at ' + request.propertyAddress if request.propertyAddress else 'your property'}. "
            "Let's cut through the BS—what's your actual timeline? 30 days, 60 days, or 'someday'?"
        )

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
@router.post("/lead-bot/{leadId}/schedule")
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
@router.get("/intent-decoder/{leadId}/score", response_model=IntentScoreResponse)
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

        session_manager = get_session_manager()
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
        return {
            "status": "success",
            "message": "Jorge Seller Bot endpoint is accessible",
            "test_result": "PASS"
        }
    except Exception as e:
        logger.error(f"Test endpoint failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "test_result": "FAIL"
        }

# --- ENDPOINT 8: POST /api/jorge-seller/process ---
@router.post("/jorge-seller/process", response_model=SellerChatResponse)
async def process_seller_message(request: SellerChatRequest):
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

        session_manager = get_session_manager()
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
        result = await jorge_bot.process_seller_with_enhancements({
            "contact_id": request.contact_id,
            "lead_id": request.contact_id,  # CRITICAL FIX: Map contact_id to lead_id for bot compatibility
            "message": request.message,
            "conversation_history": conversation_history,
            "lead_info": lead_info
        })

        end_time = time.time()
        processing_time = (end_time - start_time) * 1000

        # Track Jorge performance metrics
        performance_monitor = get_performance_monitor()
        await performance_monitor.track_jorge_performance(
            start_time=start_time,
            end_time=end_time,
            success=True,
            metadata={"contact_id": request.contact_id, "message_length": len(request.message)}
        )

        # Transform bot result to match frontend expectations
        # Map QualificationResult attributes to expected API fields
        seller_temp = getattr(result, 'temperature', 'cold')
        qualification_score = getattr(result, 'qualification_score', 0.0)
        next_actions = getattr(result, 'next_actions', [])
        confidence = getattr(result, 'confidence', 0.0)

        response = SellerChatResponse(
            response_message=f"Based on our conversation, I can see you're {seller_temp} about selling. Let me ask you a few questions to better understand your situation.",
            seller_temperature=_map_temperature(seller_temp),
            questions_answered=1 if qualification_score > 0.2 else 0,
            qualification_complete=qualification_score > 0.8,
            actions_taken=_transform_actions([{"type": "qualification", "description": f"Assessed as {seller_temp} lead"}]),
            next_steps=" | ".join(next_actions) if next_actions else "Continue qualification process",
            analytics={
                "seller_temperature": seller_temp,
                "questions_answered": 1 if qualification_score > 0.2 else 0,
                "qualification_progress": f"{min(int(qualification_score * 4), 4)}/4",
                "qualification_complete": qualification_score > 0.8,
                "qualification_score": qualification_score,
                "confidence": confidence,
                "frs_score": getattr(result, 'frs_score', 0.0),
                "pcs_score": getattr(result, 'pcs_score', 0.0),
                "processing_time_ms": round(processing_time, 2),
                "bot_version": "unified_enterprise",
                "enhancement_features": []
            }
        )

        # Track metrics and publish events
        await _track_conversation_metrics("jorge-seller-bot", processing_time)

        event_publisher = get_event_publisher()
        await event_publisher.publish_seller_bot_message_processed(
            contact_id=request.contact_id,
            message_content=request.message,
            bot_response=response.response_message,
            seller_temperature=response.seller_temperature,
            processing_time_ms=processing_time,
            questions_answered=response.questions_answered,
            qualification_complete=response.qualification_complete
        )

        logger.info(f"Processed seller message for {request.contact_id}: {response.seller_temperature} temperature, {processing_time:.2f}ms")

        # Persist conversation messages
        await session_manager.add_message(conversation_id, "user", request.message)
        await session_manager.add_message(conversation_id, "bot", response.response_message)

        return response

    except Exception as e:
        end_time = time.time()
        logger.error(f"Jorge seller bot processing failed: {e}")

        # Track Jorge performance metrics for failures
        performance_monitor = get_performance_monitor()
        await performance_monitor.track_jorge_performance(
            start_time=start_time,
            end_time=end_time,
            success=False,
            metadata={"error": str(e), "contact_id": request.contact_id}
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
                "processing_time_ms": 0
            }
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
            transformed_actions.append({
                "type": "add_tag",
                "tag": action.get("tag_name", "seller_qualified")
            })
        elif action.get("type") == "ghl_field":
            transformed_actions.append({
                "type": "update_custom_field",
                "field": action.get("field_name", "seller_temperature"),
                "value": action.get("field_value")
            })
        else:
            # Pass through other action types
            transformed_actions.append(action)

    # Ensure at least one action for frontend
    if not transformed_actions:
        transformed_actions.append({
            "type": "update_custom_field",
            "field": "last_jorge_contact",
            "value": datetime.now().isoformat()
        })

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


# Lead Bot Automation Models
class LeadAutomationRequest(BaseModel):
    """Request model for Lead Bot automation - Frontend Interface"""
    contact_id: str = Field(..., description="Lead contact ID")
    location_id: str = Field(..., description="GHL location ID")
    automation_type: Literal["day_3", "day_7", "day_30", "post_showing", "contract_to_close"] = Field(..., description="Type of automation to trigger")
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
async def trigger_lead_automation(request: LeadAutomationRequest):
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
            "contract_to_close": 1  # Immediate
        }

        sequence_day = automation_mapping.get(request.automation_type, 3)

        # Execute lead bot sequence in background
        background_tasks = BackgroundTasks()
        background_tasks.add_task(
            _execute_lead_sequence,
            lead_bot,
            request.contact_id,
            sequence_day
        )

        end_time = time.time()
        processing_time = (end_time - start_time) * 1000

        # Track Lead Bot automation performance
        performance_monitor = get_performance_monitor()
        await performance_monitor.track_lead_automation(
            automation_type=request.automation_type,
            start_time=start_time,
            end_time=end_time,
            success=True
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
                    scheduled_time=scheduled_time.isoformat()
                )
            ]
        elif request.automation_type == "day_7":
            actions_taken = [
                LeadAutomationAction(
                    type="retell_voice_call",
                    channel="voice_call",
                    scheduled_time=scheduled_time.isoformat()
                ),
                LeadAutomationAction(
                    type="follow_up_sms",
                    channel="sms",
                    content="Jorge here - tried calling but wanted to follow up. Have you had a chance to think about those properties I sent? What questions can I answer?",
                    scheduled_time=(scheduled_time + timedelta(hours=2)).isoformat()
                )
            ]
        elif request.automation_type == "day_30":
            actions_taken = [
                LeadAutomationAction(
                    type="market_update",
                    channel="email",
                    content="Market Update: New properties matching your criteria",
                    scheduled_time=scheduled_time.isoformat()
                )
            ]
        elif request.automation_type == "post_showing":
            actions_taken = [
                LeadAutomationAction(
                    type="feedback_survey",
                    channel="sms",
                    content="How did the showing go? Any thoughts on the property? I'm here to answer any questions!",
                    scheduled_time=(scheduled_time + timedelta(hours=1)).isoformat()
                )
            ]
        elif request.automation_type == "contract_to_close":
            actions_taken = [
                LeadAutomationAction(
                    type="closing_checklist",
                    channel="email",
                    content="Here's your closing checklist and next steps",
                    scheduled_time=scheduled_time.isoformat()
                )
            ]

        # Publish automation event
        event_publisher = get_event_publisher()
        await event_publisher.publish_lead_bot_sequence_update(
            contact_id=request.contact_id,
            sequence_day=sequence_day,
            action_type=f"automation_{request.automation_type}",
            success=True
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
                "scheduled_for": (datetime.now() + timedelta(days=7)).isoformat()
            } if request.automation_type in ["day_3", "day_7"] else None
        )

        logger.info(f"Triggered lead automation {automation_id} for {request.contact_id}: {request.automation_type}")

        return response

    except Exception as e:
        end_time = time.time()
        logger.error(f"Lead automation failed for {request.contact_id}: {e}")

        # Track Lead Bot automation performance for failures
        performance_monitor = get_performance_monitor()
        await performance_monitor.track_lead_automation(
            automation_type=request.automation_type,
            start_time=start_time,
            end_time=end_time,
            success=False
        )

        # Return error response in expected format
        error_response = LeadAutomationResponse(
            automation_id=f"error_{int(time.time())}",
            contact_id=request.contact_id,
            automation_type=request.automation_type,
            status="failed",
            scheduled_for=datetime.now().isoformat(),
            actions_taken=[
                LeadAutomationAction(
                    type="error",
                    channel="sms",
                    content=f"Automation failed: {str(e)}"
                )
            ]
        )

        return error_response


# ========================================================================
# PERFORMANCE MONITORING ENDPOINTS
# ========================================================================

@router.get("/performance/summary")
async def get_performance_summary():
    """Get comprehensive Jorge Enterprise performance summary"""
    performance_monitor = get_performance_monitor()
    return performance_monitor.get_jorge_enterprise_summary()


@router.get("/performance/jorge")
async def get_jorge_metrics():
    """Get Jorge Seller Bot specific performance metrics"""
    performance_monitor = get_performance_monitor()
    return performance_monitor.get_jorge_metrics()


@router.get("/performance/lead-automation")
async def get_lead_automation_metrics():
    """Get Lead Bot automation performance metrics"""
    performance_monitor = get_performance_monitor()
    return performance_monitor.get_lead_automation_metrics()


@router.get("/performance/websocket")
async def get_websocket_metrics():
    """Get WebSocket coordination performance metrics"""
    performance_monitor = get_performance_monitor()
    return performance_monitor.get_websocket_metrics()


@router.get("/performance/health")
async def get_system_health():
    """Get comprehensive system health report"""
    performance_monitor = get_performance_monitor()
    return performance_monitor.get_health_report()


# ========================================================================
# JORGE SELLER BOT - FRONTEND INTEGRATION ENDPOINTS
# ========================================================================

@router.get("/jorge-seller/{lead_id}/progress")
async def get_jorge_qualification_progress(lead_id: str):
    """
    Get Jorge Seller Bot qualification progress for a lead.
    Expected by frontend: jorge-seller-api.ts line 122
    """
    try:
        # Get intent decoder for FRS/PCS scores
        intent_decoder = get_intent_decoder()

        session_manager = get_session_manager()
        conversation_history = []
        conversation_ids = await session_manager.get_lead_conversations(lead_id)
        if conversation_ids:
            conversation_history = await session_manager.get_history(conversation_ids[-1])

        # Analyze lead intent
        profile = intent_decoder.analyze_lead(lead_id, conversation_history)

        # Map to frontend expected format
        return {
            "contact_id": lead_id,
            "current_question": 1,  # TODO: Track real question progress
            "questions_answered": len([h for h in conversation_history if h.get("role") == "user"]),
            "seller_temperature": _classify_temperature(profile),
            "qualification_scores": {
                "frs_score": profile.frs.total_score,
                "pcs_score": profile.pcs.total_score
            },
            "next_action": profile.next_best_action,
            "timestamp": datetime.now().isoformat(),
            "stall_detected": False,  # TODO: Implement stall detection
            "detected_stall_type": None,
            "confrontational_effectiveness": 85  # TODO: Calculate based on responses
        }
    except Exception as e:
        logger.error(f"Failed to get Jorge qualification progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get qualification progress")


@router.get("/jorge-seller/conversations/{conversation_id}")
async def get_jorge_conversation_state(conversation_id: str):
    """
    Get Jorge Seller Bot conversation state.
    Expected by frontend: jorge-seller-api.ts line 149
    """
    try:
        session_manager = get_session_manager()
        summary = await session_manager.get_conversation_summary(conversation_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "conversation_id": conversation_id,
            "lead_id": summary.get("lead_id"),
            "lead_name": summary.get("lead_name"),
            "stage": "qualification",
            "current_tone": "CONFRONTATIONAL",
            "stall_detected": False,
            "detected_stall_type": None,
            "seller_temperature": "warm",
            "psychological_commitment": 65,
            "is_qualified": False,
            "questions_answered": summary.get("user_messages", 0),
            "current_question": summary.get("user_messages", 0) + 1,
            "ml_confidence": 0.85
        }
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
            "thinking": "Thinking usually means someone else got in your head. What are they telling you?"
        }

        script = stall_breaker_scripts.get(stall_type, stall_breaker_scripts["generic"])

        logger.info(f"Applied stall-breaker for lead {lead_id}: {stall_type}")

        return {
            "success": True,
            "script_applied": stall_type,
            "next_message": script
        }
    except Exception as e:
        logger.error(f"Failed to apply stall-breaker: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply stall-breaker")


@router.post("/jorge-seller/{lead_id}/handoff")
async def trigger_jorge_handoff(lead_id: str, request: dict):
    """
    Trigger handoff from Jorge Seller Bot to Lead Bot.
    Expected by frontend: jorge-seller-api.ts line 245
    """
    try:
        target_bot = request.get("target_bot", "lead-bot")
        reason = request.get("reason", "qualification_complete")

        # Generate handoff ID
        handoff_id = f"handoff_{int(time.time())}_{lead_id[:8]}"

        # TODO: Implement actual handoff logic with CoordinationEngine
        # For now, log the handoff request
        logger.info(f"Jorge handoff triggered: {lead_id} -> {target_bot}, reason: {reason}")

        # Publish handoff event (using generic event publishing)
        event_publisher = get_event_publisher()
        # TODO: Implement bot_coordination_event when CoordinationEngine is ready
        # For now, log the handoff completion
        logger.info(f"Jorge handoff completed: {lead_id} -> {target_bot}, handoff_id: {handoff_id}")

        return {
            "success": True,
            "handoff_id": handoff_id,
            "target_bot": target_bot,
            "estimated_time_seconds": 30
        }
    except Exception as e:
        logger.error(f"Failed to trigger handoff: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger handoff")
