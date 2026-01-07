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

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from ghl_real_estate_ai.api.schemas.ghl import (
    ActionType,
    GHLAction,
    GHLWebhookEvent,
    GHLWebhookResponse,
    MessageType,
)
from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
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


@router.post("/webhook", response_model=GHLWebhookResponse)
async def handle_ghl_webhook(event: GHLWebhookEvent, background_tasks: BackgroundTasks):
    """
    Handle incoming webhook from GoHighLevel.

    This endpoint receives messages from GHL, processes them with AI,
    and returns a response along with actions to perform (tags, workflows).

    Args:
        event: GHL webhook event payload
        background_tasks: FastAPI background tasks for async operations

    Returns:
        GHLWebhookResponse with AI message and actions

    Raises:
        HTTPException: If webhook processing fails
    """
    contact_id = event.contact_id
    location_id = event.location_id
    user_message = event.message.body
    tags = event.contact.tags or []

    logger.info(
        f"Received webhook for contact {contact_id} in location {location_id}",
        extra={
            "contact_id": contact_id,
            "location_id": location_id,
            "message_type": event.message.type,
            "message_preview": user_message[:100],
            "tags": tags,
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

        # Step 2: Generate AI response
        ai_response = await conversation_manager.generate_response(
            user_message=user_message,
            contact_info={
                "first_name": event.contact.first_name,
                "last_name": event.contact.last_name,
                "phone": event.contact.phone,
                "email": event.contact.email,
            },
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

        # Step 3: Update conversation context
        await conversation_manager.update_context(
            contact_id=contact_id,
            user_message=user_message,
            ai_response=ai_response.message,
            extracted_data=ai_response.extracted_data,
            location_id=location_id,
        )

        # Step 4: Prepare GHL actions based on extracted data and lead score
        actions = await prepare_ghl_actions(
            extracted_data=ai_response.extracted_data,
            lead_score=ai_response.lead_score,
            event=event,
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
