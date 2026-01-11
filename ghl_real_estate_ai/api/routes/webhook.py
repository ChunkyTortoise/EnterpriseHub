"""
GHL Webhook Handler.

Processes incoming messages from GoHighLevel and returns AI-generated responses.

Flow:
1. Receive webhook from GHL
2. Extract message and contact info
3. Get conversation context
4. Generate AI response
5. Update conversation state
6. Calculate lead score
7. Prepare GHL actions (tags, custom fields)
8. Send response back to GHL
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Request, Header
import hmac
import hashlib
import os
from datetime import datetime

from ghl_real_estate_ai.api.schemas.ghl import (
    ActionType,
    GHLAction,
    GHLWebhookEvent,
    GHLWebhookResponse,
    MessageType,
)
from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.core.service_registry import ServiceRegistry
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.business_metrics_service import (
    BusinessMetricsService,
    BusinessMetric,
    MetricType,
    ConversionStage,
    create_business_metrics_service
)
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.services.tenant_service import TenantService

logger = get_logger(__name__)
router = APIRouter(prefix="/ghl", tags=["ghl"])

# Initialize dependencies (singletons)
conversation_manager = ConversationManager()
ghl_client_default = GHLClient()
lead_scorer = LeadScorer()
tenant_service = TenantService()
analytics_service = AnalyticsService()

# Initialize business metrics service for comprehensive tracking
business_metrics_service = None

# Initialize Claude-enhanced service registry (Phase 3 Enhancement)
service_registry = ServiceRegistry(demo_mode=False)

# Initialize AI-Powered Coaching Engine (Week 8B Integration)
from ghl_real_estate_ai.services.ai_powered_coaching_engine import (
    get_coaching_engine,
    initialize_coaching_engine
)
from ghl_real_estate_ai.services.claude_conversation_analyzer import (
    ConversationData
)

# Global coaching engine instance
coaching_engine = None


async def initialize_business_metrics_service():
    """Initialize the business metrics service for webhook tracking."""
    global business_metrics_service
    if not business_metrics_service:
        try:
            business_metrics_service = await create_business_metrics_service(
                redis_url=settings.redis_url,
                postgres_url=settings.database_url
            )
            logger.info("Business metrics service initialized for webhook tracking")
        except Exception as e:
            logger.error(f"Failed to initialize business metrics service: {e}")
            business_metrics_service = None


async def initialize_coaching_engine_for_webhook():
    """Initialize the AI-Powered Coaching Engine for webhook processing."""
    global coaching_engine
    if not coaching_engine:
        try:
            coaching_engine = await initialize_coaching_engine()
            logger.info("AI-Powered Coaching Engine initialized for webhook processing")
        except Exception as e:
            logger.error(f"Failed to initialize coaching engine: {e}")
            coaching_engine = None


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    """
    Verify GoHighLevel webhook signature.

    Args:
        raw_body: Raw request body bytes
        signature: X-GHL-Signature header value

    Returns:
        bool: True if signature is valid
    """
    webhook_secret = os.getenv("GHL_WEBHOOK_SECRET")
    if not webhook_secret:
        # Log security warning but don't fail in development
        environment = os.getenv("ENVIRONMENT", "").lower()
        if environment == "production":
            logger.error("GHL_WEBHOOK_SECRET not configured in production!")
            return False
        else:
            logger.warning("GHL_WEBHOOK_SECRET not configured - webhook signature verification disabled")
            return True

    if not signature:
        return False

    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]

    # Compute HMAC signature
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    # Secure comparison
    return hmac.compare_digest(expected_signature, signature)


@router.post("/webhook", response_model=GHLWebhookResponse)
async def handle_ghl_webhook(
    event: GHLWebhookEvent,
    background_tasks: BackgroundTasks,
    request: Request,
    x_ghl_signature: str = Header(None, alias="X-GHL-Signature")
):
    """
    Handle incoming webhook from GoHighLevel.

    This endpoint receives messages from GHL, processes them with AI,
    and returns a response along with actions to perform (tags, workflows).

    Args:
        event: GHL webhook event payload
        background_tasks: FastAPI background tasks for async operations
        request: FastAPI request object for signature verification
        x_ghl_signature: GHL webhook signature header

    Returns:
        GHLWebhookResponse with AI message and actions

    Raises:
        HTTPException: If webhook processing fails or signature invalid
    """
    # Verify webhook signature for security
    raw_body = await request.body()
    if not verify_webhook_signature(raw_body, x_ghl_signature):
        logger.error(
            f"Invalid webhook signature from GHL for location {event.location_id}",
            extra={"contact_id": event.contact_id, "signature_provided": bool(x_ghl_signature)}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    contact_id = event.contact_id
    location_id = event.location_id
    user_message = event.message.body
    tags = event.contact.tags or []

    # Initialize business metrics service if not already done
    if not business_metrics_service:
        await initialize_business_metrics_service()

    # Initialize AI-Powered Coaching Engine if not already done (Week 8B)
    if not coaching_engine:
        await initialize_coaching_engine_for_webhook()

    # Start business metrics tracking for this webhook
    webhook_tracking_id = None
    if business_metrics_service:
        webhook_tracking_id = await business_metrics_service.track_webhook_start(
            location_id=location_id,
            contact_id=contact_id,
            webhook_type=event.message.type
        )

    logger.info(
        f"Received webhook for contact {contact_id} in location {location_id}",
        extra={
            "contact_id": contact_id,
            "location_id": location_id,
            "message_type": event.message.type,
            "message_preview": user_message[:100],
            "tags": tags,
            "webhook_tracking_id": webhook_tracking_id,
        },
    )

    # Track incoming message
    background_tasks.add_task(
        analytics_service.track_event,
        event_type="message_received",
        location_id=location_id,
        contact_id=contact_id,
        data={"message_type": event.message.type, "message_length": len(user_message)},
    )

    # Step -1: Check AI Activation/Deactivation Tags (Jorge's Requirement)
    # AI only runs if activation tag is present AND no deactivation tag is present
    activation_tags = settings.activation_tags  # e.g., ["Needs Qualifying", "Hit List"]
    deactivation_tags = (
        settings.deactivation_tags
    )  # e.g., ["AI-Off", "Qualified", "Stop-Bot"]

    should_activate = any(tag in tags for tag in activation_tags)
    should_deactivate = any(tag in tags for tag in deactivation_tags)

    if not should_activate:
        logger.info(
            f"AI not triggered for contact {contact_id} - activation tag not present"
        )
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="ai_not_triggered",
            location_id=location_id,
            contact_id=contact_id,
            data={"reason": "activation_tag_missing"},
        )
        return GHLWebhookResponse(
            success=True,
            message="AI not triggered (activation tag missing)",
            actions=[],
        )

    if should_deactivate:
        logger.info(
            f"AI deactivated for contact {contact_id} - deactivation tag present"
        )
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="ai_not_triggered",
            location_id=location_id,
            contact_id=contact_id,
            data={"reason": "deactivation_tag_present"},
        )
        return GHLWebhookResponse(
            success=True,
            message="AI deactivated (deactivation tag present)",
            actions=[],
        )

    try:
        # Step 0: Get tenant configuration
        tenant_config = await tenant_service.get_tenant_config(location_id)

        # Step 0.1: Initialize GHL client (tenant-specific or default)
        current_ghl_client = ghl_client_default
        if tenant_config and tenant_config.get("ghl_api_key"):
            current_ghl_client = GHLClient(
                api_key=tenant_config["ghl_api_key"], location_id=location_id
            )

        # Step 1: Get conversation context
        context = await conversation_manager.get_context(
            contact_id, location_id=location_id
        )

        # Step 1.5: Claude Semantic Analysis (Phase 3 Enhancement)
        conversation_messages = []
        if context and context.get("messages"):
            # Build conversation history for Claude analysis
            for msg in context["messages"][-10:]:  # Last 10 messages for context
                conversation_messages.append({
                    "role": "user" if msg.get("from_contact", False) else "assistant",
                    "content": msg.get("text", ""),
                    "timestamp": msg.get("timestamp", "")
                })

        # Add current message
        conversation_messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })

        # Perform Claude semantic analysis
        claude_semantics = {}
        try:
            claude_semantics = await service_registry.analyze_lead_semantics(conversation_messages)
            logger.info(f"Claude semantic analysis completed for contact {contact_id}")
        except Exception as e:
            logger.warning(f"Claude semantic analysis failed: {e}")

        # Step 1.6: Qualification Orchestrator Integration (Phase 3 Enhancement)
        qualification_progress = {}
        try:
            # Check if qualification flow exists or start new one
            contact_name = f"{event.contact.first_name or ''} {event.contact.last_name or ''}".strip()
            if not contact_name:
                contact_name = f"Contact {contact_id}"

            # Try to find existing qualification flow
            orchestrator = service_registry.qualification_orchestrator
            if orchestrator:
                # Process the response in existing flow or start new one
                qualification_progress = await service_registry.process_qualification_response(
                    flow_id=f"qual_{contact_id}_active",  # Try active flow
                    user_message=user_message
                )

                # If no active flow found, start new one
                if qualification_progress.get("error"):
                    new_flow = await service_registry.start_intelligent_qualification(
                        contact_id=contact_id,
                        contact_name=contact_name,
                        initial_message=user_message,
                        source=tags[0] if tags else "ghl_webhook"
                    )
                    qualification_progress = new_flow

        except Exception as e:
            logger.warning(f"Qualification orchestration failed: {e}")

        # Step 2: Enhanced AI Response Generation (with Claude insights)
        enhanced_contact_info = {
            "first_name": event.contact.first_name,
            "last_name": event.contact.last_name,
            "phone": event.contact.phone,
            "email": event.contact.email,
            # Add Claude insights
            "claude_intent": claude_semantics.get("intent_analysis", {}),
            "semantic_preferences": claude_semantics.get("semantic_preferences", {}),
            "urgency_score": claude_semantics.get("urgency_score", 50),
            "qualification_progress": qualification_progress.get("completion_percentage", 0)
        }

        ai_response = await conversation_manager.generate_response(
            user_message=user_message,
            contact_info=enhanced_contact_info,
            context=context,
            tenant_config=tenant_config,
            ghl_client=current_ghl_client,
        )

        # Track AI response generation
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="message_sent",
            location_id=location_id,
            contact_id=contact_id,
            data={
                "message_length": len(ai_response.message),
                "lead_score": ai_response.lead_score,
            },
        )

        # Track lead scoring
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="lead_scored",
            location_id=location_id,
            contact_id=contact_id,
            data={
                "score": ai_response.lead_score,
                "classification": lead_scorer.classify(ai_response.lead_score),
            },
        )

        # Step 2.5: AI-Powered Coaching Analysis (Week 8B Integration)
        coaching_analysis = None
        coaching_alert = None
        if coaching_engine:
            try:
                # Create conversation data for coaching analysis
                coaching_conversation_data = ConversationData(
                    conversation_id=f"ghl_{contact_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    agent_id=location_id,  # Use location_id as agent identifier
                    tenant_id=location_id,  # Use location_id as tenant identifier
                    lead_id=contact_id,
                    messages=conversation_messages,
                    start_time=datetime.now(),
                    context={
                        "source": "ghl_webhook",
                        "lead_score": ai_response.lead_score,
                        "claude_semantics": claude_semantics,
                        "qualification_progress": qualification_progress,
                        "contact_tags": tags
                    }
                )

                # Analyze conversation for real-time coaching
                coaching_analysis, coaching_alert = await coaching_engine.analyze_and_coach_real_time(
                    coaching_conversation_data
                )

                logger.info(
                    f"Real-time coaching analysis completed for contact {contact_id}: "
                    f"quality_score={coaching_analysis.overall_quality_score:.1f}, "
                    f"coaching_alert={'generated' if coaching_alert else 'none'}"
                )

                # Track coaching analytics
                background_tasks.add_task(
                    analytics_service.track_event,
                    event_type="coaching_analysis",
                    location_id=location_id,
                    contact_id=contact_id,
                    data={
                        "quality_score": coaching_analysis.overall_quality_score,
                        "conversation_effectiveness": coaching_analysis.conversation_effectiveness,
                        "coaching_opportunities": len(coaching_analysis.coaching_insights.coaching_opportunities),
                        "coaching_alert_generated": bool(coaching_alert),
                        "processing_time_ms": coaching_analysis.processing_time_ms
                    },
                )

            except Exception as e:
                logger.error(f"Real-time coaching analysis failed for contact {contact_id}: {e}")
                coaching_analysis = None
                coaching_alert = None

        # Step 3: Update conversation context
        await conversation_manager.update_context(
            contact_id=contact_id,
            user_message=user_message,
            ai_response=ai_response.message,
            extracted_data=ai_response.extracted_data,
            location_id=location_id,
        )

        # Step 4: Enhanced GHL Actions with Claude Intelligence (Phase 3 Enhancement)
        actions = await prepare_enhanced_ghl_actions(
            extracted_data=ai_response.extracted_data,
            lead_score=ai_response.lead_score,
            event=event,
            claude_semantics=claude_semantics,
            qualification_progress=qualification_progress,
        )

        # Step 5: Send response and apply actions in background
        background_tasks.add_task(
            current_ghl_client.send_message,
            contact_id=contact_id,
            message=ai_response.message,
            channel=event.message.type,
        )

        background_tasks.add_task(
            current_ghl_client.apply_actions, contact_id=contact_id, actions=actions
        )

        # Complete business metrics tracking for successful webhook
        if business_metrics_service and webhook_tracking_id:
            # Track contact enrichment data
            enrichment_data = {
                "lead_score": ai_response.lead_score,
                "extracted_preferences": len(ai_response.extracted_data),
                "claude_insights": bool(claude_semantics),
                "qualification_progress": qualification_progress.get("completion_percentage", 0)
            }

            processing_time = await business_metrics_service.track_webhook_completion(
                tracking_id=webhook_tracking_id,
                location_id=location_id,
                contact_id=contact_id,
                success=True,
                webhook_type=event.message.type,
                enrichment_data=enrichment_data
            )

            # Track lead creation/update in conversion pipeline
            await business_metrics_service.track_conversion_stage(
                contact_id=contact_id,
                location_id=location_id,
                stage=ConversionStage.LEAD_CREATED,
                ai_score=ai_response.lead_score,
                metadata={
                    "message_type": event.message.type,
                    "claude_enhanced": bool(claude_semantics),
                    "processing_time_ms": processing_time
                }
            )

            logger.info(
                f"Business metrics tracked: webhook completed in {processing_time:.1f}ms, "
                f"lead score {ai_response.lead_score}"
            )

        logger.info(
            f"Successfully processed webhook for contact {contact_id}",
            extra={
                "contact_id": contact_id,
                "lead_score": ai_response.lead_score,
                "actions_count": len(actions),
            },
        )

        # Return immediate response to GHL
        return GHLWebhookResponse(
            success=True, message=ai_response.message, actions=actions
        )

    except Exception as e:
        # Track failed webhook in business metrics
        if business_metrics_service and webhook_tracking_id:
            try:
                await business_metrics_service.track_webhook_completion(
                    tracking_id=webhook_tracking_id,
                    location_id=location_id,
                    contact_id=contact_id,
                    success=False,
                    error_message=str(e),
                    webhook_type=getattr(event, 'message', {}).get('type', 'unknown')
                )
            except Exception as metrics_error:
                logger.error(f"Failed to track webhook failure in metrics: {metrics_error}")

        logger.error(
            f"Error processing webhook for contact {contact_id}: {str(e)}",
            extra={"contact_id": contact_id, "error": str(e)},
            exc_info=True,
        )

        # Return error response (but don't fail the webhook)
        return GHLWebhookResponse(
            success=False,
            message="Sorry, I'm experiencing a technical issue. A team member will follow up with you shortly!",
            actions=[],
            error=str(e),
        )


async def prepare_ghl_actions(
    extracted_data: dict, lead_score: int, event: GHLWebhookEvent
) -> list[GHLAction]:
    """
    Prepare GHL actions based on extracted data and lead score.

    Args:
        extracted_data: Extracted preferences from conversation
        lead_score: Calculated lead score (0-100)
        event: Original webhook event

    Returns:
        List of GHLAction objects to apply
    """
    actions = []

    # Tag based on lead score
    classification = lead_scorer.classify(lead_score)

    if classification == "hot":
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Hot-Lead"))
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="AI-Qualified"))

        # Trigger workflow to notify agent via SMS if configured
        if settings.notify_agent_workflow_id:
            actions.append(
                GHLAction(
                    type=ActionType.TRIGGER_WORKFLOW,
                    workflow_id=settings.notify_agent_workflow_id,
                )
            )

    elif classification == "warm":
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Warm-Lead"))
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="AI-Engaged"))

    else:
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Cold-Lead"))

    # Update Lead Score Custom Field if configured
    if settings.custom_field_lead_score:
        actions.append(
            GHLAction(
                type=ActionType.UPDATE_CUSTOM_FIELD,
                field=settings.custom_field_lead_score,
                value=lead_score,
            )
        )

    # Tag based on budget
    budget = extracted_data.get("budget")
    if budget:
        if budget < 300000:
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Budget-Under-300k"))
        elif budget < 500000:
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Budget-300k-500k"))
        else:
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Budget-Over-500k"))

        # Update Budget Custom Field if configured
        if settings.custom_field_budget:
            actions.append(
                GHLAction(
                    type=ActionType.UPDATE_CUSTOM_FIELD,
                    field=settings.custom_field_budget,
                    value=budget,
                )
            )

    # Tag based on location
    location = extracted_data.get("location")
    if location:
        location_str = ""
        if isinstance(location, list):
            location_str = ", ".join(location)
            for loc in location:
                actions.append(
                    GHLAction(type=ActionType.ADD_TAG, tag=f"Location-{loc}")
                )
        else:
            location_str = str(location)
            actions.append(
                GHLAction(type=ActionType.ADD_TAG, tag=f"Location-{location}")
            )

        # Update Location Custom Field if configured
        if settings.custom_field_location:
            actions.append(
                GHLAction(
                    type=ActionType.UPDATE_CUSTOM_FIELD,
                    field=settings.custom_field_location,
                    value=location_str,
                )
            )

    # Tag based on timeline urgency
    timeline = extracted_data.get("timeline", "")
    if timeline:
        if lead_scorer._is_urgent_timeline(timeline):
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Timeline-Urgent"))

        # Update Timeline Custom Field if configured
        if settings.custom_field_timeline:
            actions.append(
                GHLAction(
                    type=ActionType.UPDATE_CUSTOM_FIELD,
                    field=settings.custom_field_timeline,
                    value=timeline,
                )
            )

    logger.info(
        f"Prepared {len(actions)} actions for contact {event.contact_id}",
        extra={"contact_id": event.contact_id, "actions": [a.type for a in actions]},
    )

    return actions


async def prepare_enhanced_ghl_actions(
    extracted_data: dict,
    lead_score: int,
    event: GHLWebhookEvent,
    claude_semantics: dict,
    qualification_progress: dict
) -> list[GHLAction]:
    """
    Enhanced GHL actions preparation with Claude intelligence (Phase 3).

    Args:
        extracted_data: Extracted preferences from conversation
        lead_score: Calculated lead score (0-100)
        event: Original webhook event
        claude_semantics: Claude semantic analysis results
        qualification_progress: Qualification orchestrator progress

    Returns:
        List of GHLAction objects to apply with Claude-enhanced intelligence
    """
    actions = []

    # Start with base actions from original function
    base_actions = await prepare_ghl_actions(extracted_data, lead_score, event)
    actions.extend(base_actions)

    # Claude-Enhanced Actions (Phase 3 Enhancement)

    # 1. Semantic Intent-Based Tagging
    intent_analysis = claude_semantics.get("intent_analysis", {})
    intent_confidence = intent_analysis.get("confidence", 0)

    if intent_confidence > 70:
        intent_type = intent_analysis.get("intent", "")
        if intent_type == "high_purchase_intent":
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Claude-High-Intent"))
        elif intent_type == "browsing_interest":
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Claude-Browsing"))
        elif intent_type == "urgent_timeline":
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Claude-Urgent"))

    # 2. Qualification Progress-Based Actions
    completion_percentage = qualification_progress.get("completion_percentage", 0)

    if completion_percentage >= 80:
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Claude-Qualified"))
        # Trigger high-priority workflow for qualified leads
        if settings.notify_agent_workflow_id:
            actions.append(
                GHLAction(
                    type=ActionType.TRIGGER_WORKFLOW,
                    workflow_id=settings.notify_agent_workflow_id,
                )
            )
    elif completion_percentage >= 50:
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Claude-Qualifying"))
    elif completion_percentage >= 20:
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Claude-Discovery"))

    # 3. Semantic Preferences-Based Custom Fields
    semantic_preferences = claude_semantics.get("semantic_preferences", {})

    # Budget insights from Claude
    if semantic_preferences.get("budget_mentioned"):
        budget_confidence = semantic_preferences.get("budget_confidence", 0)
        if budget_confidence > 60 and settings.custom_field_budget:
            actions.append(
                GHLAction(
                    type=ActionType.UPDATE_CUSTOM_FIELD,
                    field=settings.custom_field_budget,
                    value=semantic_preferences.get("budget_range", "Mentioned but unspecified"),
                )
            )

    # Timeline urgency from Claude
    urgency_score = claude_semantics.get("urgency_score", 50)
    if urgency_score > 75:
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Claude-Urgent-Timeline"))
        if settings.custom_field_timeline:
            actions.append(
                GHLAction(
                    type=ActionType.UPDATE_CUSTOM_FIELD,
                    field=settings.custom_field_timeline,
                    value=f"High urgency (Claude score: {urgency_score})",
                )
            )

    # 4. Conversation Quality and Engagement Scoring
    engagement_level = qualification_progress.get("metrics", {}).get("engagement_level", 50)

    if engagement_level > 80:
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Claude-Highly-Engaged"))
    elif engagement_level < 30:
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Claude-Low-Engagement"))

    # 5. Next Best Action Recommendations
    agent_recommendations = qualification_progress.get("recommendations", [])

    for recommendation in agent_recommendations:
        if recommendation.get("action") == "schedule_showing":
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Ready-For-Showing"))
        elif recommendation.get("action") == "assess_urgency":
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Assess-Timeline"))

    # 6. Claude Confidence-Based Quality Scores
    overall_confidence = claude_semantics.get("confidence", 50)

    if settings.custom_field_lead_score:
        # Enhanced lead score combining traditional score with Claude confidence
        enhanced_score = int((lead_score * 0.7) + (overall_confidence * 0.3))
        actions.append(
            GHLAction(
                type=ActionType.UPDATE_CUSTOM_FIELD,
                field=settings.custom_field_lead_score,
                value=enhanced_score,
            )
        )

    # 7. Semantic Location Intelligence
    location_preferences = semantic_preferences.get("locations", [])
    if location_preferences:
        for location in location_preferences[:3]:  # Top 3 locations
            clean_location = str(location).replace(" ", "-").replace(",", "")
            actions.append(
                GHLAction(type=ActionType.ADD_TAG, tag=f"Claude-Location-{clean_location}")
            )

    logger.info(
        f"Enhanced GHL actions prepared for contact {event.contact_id}",
        extra={
            "contact_id": event.contact_id,
            "base_actions_count": len(base_actions),
            "claude_actions_count": len(actions) - len(base_actions),
            "qualification_completion": completion_percentage,
            "claude_confidence": overall_confidence,
        },
    )

    return actions


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Railway deployment.

    Returns:
        Dict with status and version info
    """
    return {
        "status": "healthy",
        "service": "ghl-real-estate-ai",
        "version": settings.version,
        "environment": settings.environment,
    }
