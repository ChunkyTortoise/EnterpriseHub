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
from api.schemas.ghl import (
    GHLWebhookEvent,
    GHLWebhookResponse,
    GHLAction,
    ActionType,
    MessageType
)
from core.conversation_manager import ConversationManager
from services.ghl_client import GHLClient
from services.lead_scorer import LeadScorer
from ghl_utils.config import settings
from ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ghl", tags=["ghl"])

# Initialize dependencies (singletons)
conversation_manager = ConversationManager()
ghl_client = GHLClient()
lead_scorer = LeadScorer()


@router.post("/webhook", response_model=GHLWebhookResponse)
async def handle_ghl_webhook(
    event: GHLWebhookEvent,
    background_tasks: BackgroundTasks
):
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
    user_message = event.message.body

    logger.info(
        f"Received webhook for contact {contact_id}",
        extra={
            "contact_id": contact_id,
            "message_type": event.message.type,
            "message_preview": user_message[:100]
        }
    )

    try:
        # Step 0: Check if bot should be active for this contact
        contact_tags = event.contact.tags
        is_active = any(tag in contact_tags for tag in settings.activation_tags)
        is_explicitly_disabled = any(tag in contact_tags for tag in settings.deactivation_tags)

        # Determine contact type (default to Seller if 'Hit List' is present)
        is_buyer = True
        contact_type = event.contact.custom_fields.get("primary_contact_type") or \
                      event.contact.custom_fields.get("Primary Contact Type")
        
        if contact_type == "Seller" or "Hit List" in contact_tags:
            is_buyer = False

        # Check contact type if required
        if settings.required_contact_type:
            if contact_type != settings.required_contact_type and "Hit List" not in contact_tags:
                logger.info(
                    f"Bot ignored contact {contact_id}: wrong type {contact_type}",
                    extra={"contact_id": contact_id, "type": contact_type}
                )
                return GHLWebhookResponse(
                    success=False,
                    message=f"Bot only handles {settings.required_contact_type} contacts.",
                    actions=[]
                )

        if not is_active or is_explicitly_disabled:
            logger.info(
                f"Bot inactive for contact {contact_id}",
                extra={"contact_id": contact_id, "tags": contact_tags}
            )
            return GHLWebhookResponse(
                success=False,
                message="Bot is currently inactive for this contact.",
                actions=[]
            )

        # Step 1: Get conversation context
        context = await conversation_manager.get_context(contact_id)

        # Step 2: Generate AI response
        ai_response = await conversation_manager.generate_response(
            user_message=user_message,
            contact_info={
                "first_name": event.contact.first_name,
                "last_name": event.contact.last_name,
                "phone": event.contact.phone,
                "email": event.contact.email
            },
            context=context,
            is_buyer=is_buyer
        )

        # Step 3: Update conversation context
        await conversation_manager.update_context(
            contact_id=contact_id,
            user_message=user_message,
            ai_response=ai_response.message,
            extracted_data=ai_response.extracted_data
        )

        # Step 4: Prepare GHL actions based on extracted data and lead score
        actions = await prepare_ghl_actions(
            extracted_data=ai_response.extracted_data,
            lead_score=ai_response.lead_score,
            event=event
        )

        # Step 5: Send response and apply actions in background
        # (Don't block webhook response waiting for GHL API calls)
        background_tasks.add_task(
            ghl_client.send_message,
            contact_id=contact_id,
            message=ai_response.message,
            channel=event.message.type
        )

        background_tasks.add_task(
            ghl_client.apply_actions,
            contact_id=contact_id,
            actions=actions
        )

        logger.info(
            f"Successfully processed webhook for contact {contact_id}",
            extra={
                "contact_id": contact_id,
                "lead_score": ai_response.lead_score,
                "actions_count": len(actions)
            }
        )

        # Return immediate response to GHL
        return GHLWebhookResponse(
            success=True,
            message=ai_response.message,
            actions=actions
        )

    except Exception as e:
        logger.error(
            f"Error processing webhook for contact {contact_id}: {str(e)}",
            extra={
                "contact_id": contact_id,
                "error": str(e)
            },
            exc_info=True
        )

        # Return error response (but don't fail the webhook)
        return GHLWebhookResponse(
            success=False,
            message="Sorry, I'm experiencing a technical issue. A team member will follow up with you shortly!",
            actions=[],
            error=str(e)
        )


async def prepare_ghl_actions(
    extracted_data: dict,
    lead_score: int,
    event: GHLWebhookEvent
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
        # TODO: Trigger workflow to notify agent via SMS
        # actions.append(GHLAction(
        #     type=ActionType.TRIGGER_WORKFLOW,
        #     workflow_id="notify_agent_hot_lead"
        # ))

    elif classification == "warm":
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Warm-Lead"))
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="AI-Engaged"))

    else:
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Cold-Lead"))

    # Tag based on budget
    budget = extracted_data.get("budget")
    if budget:
        if budget < 300000:
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Budget-Under-300k"))
        elif budget < 500000:
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Budget-300k-500k"))
        else:
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Budget-Over-500k"))

    # Tag based on location
    location = extracted_data.get("location")
    if location:
        if isinstance(location, list):
            for loc in location:
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag=f"Location-{loc}"))
        else:
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag=f"Location-{location}"))

    # Tag based on timeline urgency
    timeline = extracted_data.get("timeline", "")
    if timeline and lead_scorer._is_urgent_timeline(timeline):
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Timeline-Urgent"))

    # Update custom field with lead score
    # Note: Replace "lead_score_field_id" with actual GHL custom field ID
    # actions.append(GHLAction(
    #     type=ActionType.UPDATE_CUSTOM_FIELD,
    #     field="lead_score_field_id",
    #     value=lead_score
    # ))

    logger.info(
        f"Prepared {len(actions)} actions for contact {event.contact_id}",
        extra={
            "contact_id": event.contact_id,
            "actions": [a.type for a in actions]
        }
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
        "environment": settings.environment
    }
