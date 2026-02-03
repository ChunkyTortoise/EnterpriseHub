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

from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from pydantic import BaseModel

from ghl_real_estate_ai.api.schemas.ghl import (
    ActionType,
    GHLAction,
    GHLWebhookEvent,
    GHLWebhookResponse,
    MessageType,
    MessageDirection,
)
from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.attribution_analytics import AttributionAnalytics
from ghl_real_estate_ai.services.calendar_scheduler import CalendarScheduler
from ghl_real_estate_ai.services.dynamic_pricing_optimizer import DynamicPricingOptimizer
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.services.lead_source_tracker import LeadSourceTracker, LeadSource
from ghl_real_estate_ai.services.security_framework import verify_webhook
from ghl_real_estate_ai.services.tenant_service import TenantService
from ghl_real_estate_ai.services.subscription_manager import SubscriptionManager
from ghl_real_estate_ai.services.compliance_guard import compliance_guard, ComplianceStatus
from ghl_real_estate_ai.api.schemas.billing import UsageRecordRequest

logger = get_logger(__name__)
router = APIRouter(prefix="/ghl", tags=["ghl"])

# Initialize dependencies (singletons)
conversation_manager = ConversationManager()
ghl_client_default = GHLClient()
# Lazy singleton — defer initialization until first request
_lead_scorer = None


def _get_lead_scorer():
    global _lead_scorer
    if _lead_scorer is None:
        _lead_scorer = LeadScorer()
    return _lead_scorer
tenant_service = TenantService()
analytics_service = AnalyticsService()
pricing_optimizer = DynamicPricingOptimizer()
calendar_scheduler = CalendarScheduler()
lead_source_tracker = LeadSourceTracker()
attribution_analytics = AttributionAnalytics()
subscription_manager = SubscriptionManager()


@router.post("/webhook", response_model=GHLWebhookResponse)
@verify_webhook("ghl")
async def handle_ghl_webhook(request: Request, event: GHLWebhookEvent, background_tasks: BackgroundTasks):
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

    # LOOPBACK PROTECTION: Ignore outbound messages (sent by bot or agent)
    if event.message.direction == MessageDirection.OUTBOUND:
        logger.info(f"Ignoring outbound message for contact {contact_id}")
        return GHLWebhookResponse(
            success=True,
            message="Ignoring outbound message",
            actions=[],
        )

    # SECURITY FIX: Remove PII from logs (contact_id, message content)
    logger.info(
        f"Received webhook for location {location_id}",
        extra={
            "location_id": location_id,
            "message_type": event.message.type,
            "message_length": len(user_message),
            "has_contact_id": bool(contact_id),
            "tags_count": len(tags) if tags else 0,
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

    # Opt-out detection (Jorge spec: "end automation immediately")
    OPT_OUT_PHRASES = [
        "stop", "unsubscribe", "don't contact", "dont contact",
        "remove me", "not interested", "no more", "opt out",
        "leave me alone", "take me off", "no thanks"
    ]
    msg_lower = user_message.lower().strip()
    if any(phrase in msg_lower for phrase in OPT_OUT_PHRASES):
        logger.info(f"Opt-out detected for contact {contact_id}")
        opt_out_msg = "No problem at all, reach out whenever you're ready"
        background_tasks.add_task(
            ghl_client_default.send_message,
            contact_id=contact_id,
            message=opt_out_msg,
            channel=event.message.type,
        )
        background_tasks.add_task(ghl_client_default.add_tags, contact_id, ["AI-Off"])
        return GHLWebhookResponse(
            success=True,
            message=opt_out_msg,
            actions=[GHLAction(type=ActionType.ADD_TAG, tag="AI-Off")],
        )

    # Step -0.5: Check for Jorge's Seller Mode (Needs Qualifying tag + JORGE_SELLER_MODE)
    from ghl_real_estate_ai.ghl_utils.jorge_config import settings as jorge_settings

    jorge_seller_mode = (
        "Needs Qualifying" in tags and
        jorge_settings.JORGE_SELLER_MODE and
        not should_deactivate
    )

    if jorge_seller_mode:
        logger.info(f"Jorge seller mode activated for contact {contact_id}")
        try:
            # Route to Jorge's seller engine
            from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

            # Get tenant configuration first
            tenant_config = await tenant_service.get_tenant_config(location_id)

            # Initialize GHL client
            current_ghl_client = ghl_client_default
            if tenant_config and tenant_config.get("ghl_api_key"):
                current_ghl_client = GHLClient(
                    api_key=tenant_config["ghl_api_key"], location_id=location_id
                )

            # Initialize Jorge's seller engine
            jorge_engine = JorgeSellerEngine(conversation_manager, current_ghl_client)

            # Process seller response
            seller_result = await jorge_engine.process_seller_response(
                contact_id=contact_id,
                user_message=user_message,
                location_id=location_id,
                tenant_config=tenant_config
            )

            # Apply Jorge's seller actions (tags, workflows)
            actions = []
            if seller_result.get("actions"):
                for action_data in seller_result["actions"]:
                    if action_data["type"] == "add_tag":
                        actions.append(GHLAction(
                            type=ActionType.ADD_TAG,
                            tag=action_data["tag"]
                        ))
                    elif action_data["type"] == "remove_tag":
                        actions.append(GHLAction(
                            type=ActionType.REMOVE_TAG,
                            tag=action_data["tag"]
                        ))
                    elif action_data["type"] == "trigger_workflow":
                        actions.append(GHLAction(
                            type=ActionType.TRIGGER_WORKFLOW,
                            workflow_id=action_data["workflow_id"]
                        ))
                    elif action_data["type"] == "update_custom_field":
                        actions.append(GHLAction(
                            type=ActionType.UPDATE_CUSTOM_FIELD,
                            field_id=action_data["field"],
                            value=action_data["value"]
                        ))

            # Track Jorge seller analytics
            background_tasks.add_task(
                analytics_service.track_event,
                event_type="jorge_seller_interaction",
                location_id=location_id,
                contact_id=contact_id,
                data={
                    "temperature": seller_result["temperature"],
                    "questions_answered": seller_result.get("questions_answered", 0),
                    "message_length": len(seller_result["message"])
                }
            )

            # --- BULLETPROOF COMPLIANCE INTERCEPTOR ---
            final_seller_msg = seller_result["message"]
            status, reason, violations = await compliance_guard.audit_message(
                final_seller_msg, 
                contact_context={"contact_id": contact_id, "mode": "seller"}
            )
            
            if status == ComplianceStatus.BLOCKED:
                logger.warning(f"Compliance BLOCKED message for {contact_id}: {reason}. Violations: {violations}")
                final_seller_msg = "Let's stick to the facts about your property. What price are you looking to get?"
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Compliance-Alert"))

            logger.info(
                f"Jorge seller processing completed for {contact_id}",
                extra={
                    "contact_id": contact_id,
                    "temperature": seller_result["temperature"],
                    "questions_answered": seller_result.get("questions_answered", 0),
                    "actions_count": len(actions),
                    "compliance_status": status.value
                }
            )

            # Send the seller response via GHL API (background task)
            background_tasks.add_task(
                current_ghl_client.send_message,
                contact_id=contact_id,
                message=final_seller_msg,
                channel=event.message.type,
            )

            # Apply tags and actions via GHL API (background task)
            if actions:
                background_tasks.add_task(
                    current_ghl_client.apply_actions,
                    contact_id=contact_id,
                    actions=actions,
                )

            return GHLWebhookResponse(
                success=True,
                message=final_seller_msg,
                actions=actions,
            )

        except Exception as e:
            logger.error(f"Jorge seller mode processing failed: {str(e)}", exc_info=True)
            # Fall back to normal processing if Jorge mode fails

    try:
        # Step 0: Get tenant configuration
        tenant_config = await tenant_service.get_tenant_config(location_id)

        # Step 0.1: Initialize GHL client (tenant-specific or default)
        current_ghl_client = ghl_client_default
        if tenant_config and tenant_config.get("ghl_api_key"):
            current_ghl_client = GHLClient(
                api_key=tenant_config["ghl_api_key"], location_id=location_id
            )

        # Step 0.2: Analyze and track lead source attribution
        source_attribution = None
        try:
            # Analyze lead source attribution
            contact_data = {
                "custom_fields": event.contact.custom_fields,
                "first_name": event.contact.first_name,
                "last_name": event.contact.last_name,
                "phone": event.contact.phone,
                "email": event.contact.email,
                "tags": event.contact.tags
            }

            # Extract webhook metadata for source analysis
            webhook_metadata = {
                "location_id": location_id,
                "contact_id": contact_id,
                "message_type": event.message.type.value,
                "timestamp": datetime.utcnow().isoformat()
            }

            source_attribution = await lead_source_tracker.analyze_lead_source(
                contact_data, webhook_metadata
            )

            # Update GHL custom fields with source attribution in background
            background_tasks.add_task(
                lead_source_tracker.update_ghl_custom_fields,
                contact_id,
                source_attribution,
                current_ghl_client
            )

            # Track source performance event
            background_tasks.add_task(
                lead_source_tracker.track_source_performance,
                source_attribution.source,
                "lead_interaction",
                {
                    "contact_id": contact_id,
                    "location_id": location_id,
                    "message_type": event.message.type.value,
                    "quality_score": source_attribution.quality_score,
                    "confidence": source_attribution.confidence_score
                }
            )

            # Track daily attribution metrics
            background_tasks.add_task(
                attribution_analytics.track_daily_metrics,
                source_attribution.source,
                1,  # 1 lead interaction
                0.0,  # No revenue at interaction stage
                0.0  # Cost tracked separately by marketing spend
            )

            logger.info(
                f"Source attribution completed for contact {contact_id}",
                extra={
                    "contact_id": contact_id,
                    "detected_source": source_attribution.source.value,
                    "confidence": source_attribution.confidence_score,
                    "quality_score": source_attribution.quality_score
                }
            )

        except Exception as e:
            logger.error(f"Source attribution failed for contact {contact_id}: {e}", exc_info=True)
            # Continue processing even if attribution fails

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

        # Track lead scoring with source attribution
        lead_scored_data = {
            "score": ai_response.lead_score,
            "classification": _get_lead_scorer().classify(ai_response.lead_score),
        }

        # Add source attribution context if available
        if source_attribution:
            lead_scored_data.update({
                "source": source_attribution.source.value,
                "source_quality": source_attribution.source_quality.value,
                "confidence": source_attribution.confidence_score,
                "utm_source": source_attribution.utm_source,
                "utm_campaign": source_attribution.utm_campaign,
                "medium": source_attribution.medium
            })

        background_tasks.add_task(
            analytics_service.track_event,
            event_type="lead_scored",
            location_id=location_id,
            contact_id=contact_id,
            data=lead_scored_data,
        )

        # Track source-specific lead scoring for attribution analytics
        if source_attribution:
            background_tasks.add_task(
                lead_source_tracker.track_source_performance,
                source_attribution.source,
                "lead_scored",
                {
                    "score": ai_response.lead_score,
                    "classification": _get_lead_scorer().classify(ai_response.lead_score),
                    "contact_id": contact_id,
                    "location_id": location_id
                }
            )
        
        # Calculate dynamic pricing for this lead (background task)
        background_tasks.add_task(
            _calculate_lead_pricing,
            contact_id=contact_id,
            location_id=location_id,
            context={
                "questions_answered": ai_response.lead_score,
                "message_content": user_message,
                "extracted_data": ai_response.extracted_data,
                "classification": _get_lead_scorer().classify(ai_response.lead_score)
            }
        )

        # Step 2.5: Handle Billing Usage Tracking (Jorge's $240K ARR Foundation)
        background_tasks.add_task(
            _handle_billing_usage,
            contact_id=contact_id,
            location_id=location_id,
            lead_score=ai_response.lead_score,
            extracted_data=ai_response.extracted_data,
            classification=_get_lead_scorer().classify(ai_response.lead_score)
        )

        # Step 3: Update conversation context
        await conversation_manager.update_context(
            contact_id=contact_id,
            user_message=user_message,
            ai_response=ai_response.message,
            extracted_data=ai_response.extracted_data,
            location_id=location_id,
        )

        # Step 3.5: Handle Smart Appointment Scheduling (Jorge's Requirement)
        appointment_booking_attempted = False
        appointment_message_addition = ""
        appointment_actions = []

        if settings.appointment_auto_booking_enabled and ai_response.lead_score >= 5:
            try:
                # Check if we should attempt appointment booking
                booking_attempted, booking_message, booking_actions = await calendar_scheduler.handle_appointment_request(
                    contact_id=contact_id,
                    contact_info={
                        "contact_id": contact_id,
                        "first_name": event.contact.first_name,
                        "last_name": event.contact.last_name,
                        "phone": event.contact.phone,
                        "email": event.contact.email,
                    },
                    lead_score=ai_response.lead_score,
                    extracted_data=ai_response.extracted_data,
                    message_content=user_message
                )

                if booking_attempted:
                    appointment_booking_attempted = True
                    appointment_message_addition = f"\n\n{booking_message}"
                    appointment_actions = booking_actions

                    # Track appointment booking event
                    background_tasks.add_task(
                        analytics_service.track_event,
                        event_type="appointment_booking_attempted",
                        location_id=location_id,
                        contact_id=contact_id,
                        data={
                            "lead_score": ai_response.lead_score,
                            "booking_success": booking_message and "scheduled" in booking_message.lower(),
                            "appointment_actions": len(booking_actions),
                            "40_percent_faster_target": True  # Jorge's conversion goal
                        }
                    )

                    logger.info(
                        f"Smart appointment scheduling triggered for {contact_id}",
                        extra={
                            "contact_id": contact_id,
                            "lead_score": ai_response.lead_score,
                            "booking_attempted": booking_attempted,
                            "actions_count": len(booking_actions),
                            "jorge_feature": "smart_appointment_scheduling"
                        }
                    )

            except Exception as e:
                logger.error(
                    f"Smart appointment scheduling failed for {contact_id}: {str(e)}",
                    extra={
                        "contact_id": contact_id,
                        "lead_score": ai_response.lead_score,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "security_event": "appointment_scheduling_failure"
                    },
                    exc_info=True
                )
                # Don't fail the webhook - continue with normal processing

        # Step 4: Prepare GHL actions based on extracted data and lead score
        actions = await prepare_ghl_actions(
            extracted_data=ai_response.extracted_data,
            lead_score=ai_response.lead_score,
            event=event,
            source_attribution=source_attribution,
        )

        # Add appointment actions to the main actions list
        if appointment_actions:
            actions.extend(appointment_actions)

        # Step 5: Send response and apply actions in background
        # Combine AI response with appointment message if booking was attempted
        final_message = ai_response.message + appointment_message_addition

        # --- BULLETPROOF COMPLIANCE INTERCEPTOR ---
        compliance_status, reason, violations = await compliance_guard.audit_message(
            final_message, 
            contact_context={"contact_id": contact_id, "lead_score": ai_response.lead_score}
        )
        
        if compliance_status == ComplianceStatus.BLOCKED:
            logger.warning(f"Compliance BLOCKED standard message for {contact_id}: {reason}")
            final_message = "I'm looking forward to helping you find the right home. What's your top priority in a neighborhood?"
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Compliance-Alert"))

        background_tasks.add_task(
            current_ghl_client.send_message,
            contact_id=contact_id,
            message=final_message,
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
                "appointment_booking_attempted": appointment_booking_attempted,
            },
        )

        # Return immediate response to GHL
        return GHLWebhookResponse(
            success=True, message=final_message, actions=actions
        )

    except Exception as e:
        # SECURITY FIX: Remove PII from error logs and responses
        import uuid
        error_id = str(uuid.uuid4())

        logger.error(
            f"Webhook processing error - location: {location_id}",
            extra={
                "error_id": error_id,
                "location_id": location_id,
                "error_type": type(e).__name__,
                "has_contact_id": bool(contact_id),
                "error_message": str(e)
            },
            exc_info=True,
        )

        # Best-effort: send a human-sounding fallback so the contact isn't left on read
        if contact_id:
            fallback_msg = "Hey, give me just a moment — I want to make sure I get you the right info. I'll circle back shortly!"
            try:
                background_tasks.add_task(
                    ghl_client_default.send_message,
                    contact_id=contact_id,
                    message=fallback_msg,
                    channel=event.message.type if event and event.message else "SMS",
                )
            except Exception:
                logger.warning(f"Failed to send fallback message for {contact_id}")

        # SECURITY FIX: Return minimal error to GHL (no PII, trackable error ID)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Processing error — fallback message sent to contact",
                "error_id": error_id,
                "retry_allowed": True
            }
        )


async def prepare_ghl_actions(
    extracted_data: dict,
    lead_score: int,
    event: GHLWebhookEvent,
    source_attribution=None
) -> list[GHLAction]:
    """
    Prepare GHL actions based on extracted data and lead score.

    Args:
        extracted_data: Extracted preferences from conversation
        lead_score: Calculated lead score (0-7, question count)
        event: Original webhook event
        source_attribution: Lead source attribution data

    Returns:
        List of GHLAction objects to apply
    """
    actions = []

    # Convert question count to percentage for Jorge's auto-deactivation logic
    percentage_score = _get_lead_scorer().get_percentage_score(lead_score)

    # Jorge's Auto-Deactivation Logic: If score >= 70%, deactivate AI and hand off
    if percentage_score >= settings.auto_deactivate_threshold:
        logger.info(
            f"Auto-deactivating AI for contact {event.contact_id} - "
            f"score {percentage_score}% (questions: {lead_score}) >= threshold {settings.auto_deactivate_threshold}%"
        )

        # Remove activation tag to stop AI
        actions.append(GHLAction(type=ActionType.REMOVE_TAG, tag="Needs Qualifying"))

        # Add qualified tag to indicate handoff
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="AI-Qualified"))
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Ready-For-Agent"))

        # Trigger agent notification workflow if configured
        if settings.notify_agent_workflow_id:
            actions.append(
                GHLAction(
                    type=ActionType.TRIGGER_WORKFLOW,
                    workflow_id=settings.notify_agent_workflow_id,
                )
            )

    # Standard lead classification based on question count
    classification = _get_lead_scorer().classify(lead_score)

    if classification == "hot":
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Hot-Lead"))

        # If not auto-deactivated, add standard hot lead tag
        if percentage_score < settings.auto_deactivate_threshold:
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="AI-Qualified"))

        # Trigger workflow to notify agent via SMS if configured (and not auto-deactivated)
        if settings.notify_agent_workflow_id and percentage_score < settings.auto_deactivate_threshold:
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
        # Convert budget to numeric if it's a string like "$400k" or "400,000"
        try:
            if isinstance(budget, str):
                # Simple cleanup: remove $, comma, and handle 'k'
                clean_budget = budget.lower().replace("$", "").replace(",", "").replace(" ", "")
                if "k" in clean_budget:
                    budget_val = float(clean_budget.replace("k", "")) * 1000
                elif "m" in clean_budget:
                    budget_val = float(clean_budget.replace("m", "")) * 1000000
                else:
                    budget_val = float(clean_budget)
            else:
                budget_val = float(budget)

            if budget_val < 300000:
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Budget-Under-300k"))
            elif budget_val < 500000:
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Budget-300k-500k"))
            else:
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Budget-Over-500k"))
        except (ValueError, TypeError):
            logger.warning(f"Could not parse budget value: {budget}")

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
        if _get_lead_scorer()._is_urgent_timeline(timeline):
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

    # Source-based tagging and attribution (Jorge's source tracking requirement)
    if source_attribution:
        try:
            # Add primary source tag
            source_tag = f"Source-{source_attribution.source.value.replace('_', '-').title()}"
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag=source_tag))

            # Add source quality tag
            quality_tag = f"Source-Quality-{source_attribution.source_quality.value.title()}"
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag=quality_tag))

            # Add high-confidence attribution tag if confidence > 80%
            if source_attribution.confidence_score > 0.8:
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="High-Confidence-Source"))

            # Priority tagging for premium sources
            premium_sources = [
                LeadSource.AGENT_REFERRAL,
                LeadSource.CLIENT_REFERRAL,
                LeadSource.ZILLOW,
                LeadSource.REALTOR_COM,
                LeadSource.DIRECT
            ]

            if source_attribution.source in premium_sources:
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Premium-Source"))

                # Higher priority for premium sources with good quality
                if source_attribution.quality_score >= 8.0:
                    actions.append(GHLAction(type=ActionType.ADD_TAG, tag="VIP-Lead"))

            # Campaign-specific tagging
            if source_attribution.utm_campaign:
                campaign_tag = f"Campaign-{source_attribution.utm_campaign[:20]}"  # Limit length
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag=campaign_tag))

            # Medium-specific tagging for paid sources
            if source_attribution.medium in ["cpc", "paid"]:
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Paid-Source"))
            elif source_attribution.medium == "organic":
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Organic-Source"))

            logger.debug(f"Added source attribution tags for {source_attribution.source.value}")

        except Exception as e:
            logger.error(f"Error adding source attribution tags: {e}", exc_info=True)

    logger.info(
        f"Prepared {len(actions)} actions for contact {event.contact_id}",
        extra={
            "contact_id": event.contact_id,
            "actions": [a.type.value for a in actions],
            "source": source_attribution.source.value if source_attribution else "unknown"
        },
    )

    return actions


class InitiateQualificationRequest(BaseModel):
    contact_id: str
    location_id: str


@router.post("/initiate-qualification")
@verify_webhook("ghl")
async def initiate_qualification(request: Request, body: InitiateQualificationRequest, background_tasks: BackgroundTasks):
    """
    Called by GHL workflow when 'Needs Qualifying' tag is applied.
    Sends initial outreach message to start qualification.
    """
    contact_id = body.contact_id
    location_id = body.location_id
    try:
        contact = await ghl_client_default.get_contact(contact_id)
        first_name = contact.get("firstName", "there")

        opening = f"Hey {first_name}, saw your property inquiry. Are you still thinking about selling?"

        # Send the opening message via GHL
        background_tasks.add_task(
            ghl_client_default.send_message,
            contact_id=contact_id,
            message=opening,
            channel=MessageType.SMS,
        )

        logger.info(
            f"Initiate qualification sent for contact {contact_id}",
            extra={"contact_id": contact_id, "location_id": location_id}
        )

        return GHLWebhookResponse(
            success=True,
            message=opening,
            actions=[],
        )
    except Exception as e:
        logger.error(f"Initiate qualification failed for contact {contact_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to initiate qualification"}
        )


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


async def _calculate_lead_pricing(contact_id: str, location_id: str, context: dict) -> None:
    """
    Background task to calculate dynamic pricing for a lead
    
    Args:
        contact_id: GHL contact ID
        location_id: GHL location ID  
        context: Conversation context and lead data
    """
    try:
        # Calculate pricing using the dynamic pricing optimizer
        pricing_result = await pricing_optimizer.calculate_lead_price(
            contact_id=contact_id,
            location_id=location_id,
            context=context
        )
        
        logger.info(
            f"Pricing calculated for contact {contact_id}",
            extra={
                "contact_id": contact_id,
                "location_id": location_id,
                "tier": pricing_result.tier,
                "final_price": pricing_result.final_price,
                "expected_roi": pricing_result.expected_roi
            }
        )
        
        # Track pricing calculation event
        await analytics_service.track_event(
            event_type="pricing_calculated",
            location_id=location_id,
            contact_id=contact_id,
            data={
                "tier": pricing_result.tier,
                "final_price": pricing_result.final_price,
                "base_price": pricing_result.base_price,
                "multiplier": pricing_result.multiplier,
                "conversion_probability": pricing_result.conversion_probability,
                "expected_roi": pricing_result.expected_roi,
                "jorge_score": pricing_result.jorge_score,
                "agent_recommendation": pricing_result.agent_recommendation
            }
        )

    except Exception as e:
        logger.error(
            f"Failed to calculate pricing for contact {contact_id}",
            extra={
                "contact_id": contact_id,
                "location_id": location_id,
                "error": str(e)
            },
            exc_info=True
        )


async def _handle_billing_usage(contact_id: str, location_id: str, lead_score: int,
                              extracted_data: dict, classification: str) -> None:
    """
    Background task to handle billing usage tracking for lead processing.

    Implements Jorge's $240K ARR foundation by tracking subscription usage
    and recording billable events for overage calculation.

    Args:
        contact_id: GHL contact ID
        location_id: GHL location ID
        lead_score: AI-generated lead score (0-7)
        extracted_data: Extracted lead preferences and data
        classification: Lead classification (hot/warm/cold)
    """
    try:
        # Get active subscription for this location
        active_subscription = await subscription_manager.get_active_subscription(location_id)

        if not active_subscription:
            logger.info(
                f"No active subscription found for location {location_id} - skipping usage billing",
                extra={
                    "contact_id": contact_id,
                    "location_id": location_id,
                    "classification": classification,
                    "billing_status": "no_subscription"
                }
            )
            return

        # Calculate lead price using dynamic pricing
        pricing_result = await pricing_optimizer.calculate_lead_price(
            contact_id=contact_id,
            location_id=location_id,
            context={
                "questions_answered": lead_score,
                "extracted_data": extracted_data,
                "classification": classification
            }
        )

        # Check if this lead exceeds the subscription allowance
        current_usage = active_subscription.usage_current + 1  # Including this lead

        if current_usage > active_subscription.usage_allowance:
            # This is an overage lead - bill usage to Stripe
            try:
                # Create usage record request
                usage_request = UsageRecordRequest(
                    subscription_id=active_subscription.id,
                    lead_id=f"lead_{contact_id}_{datetime.now().isoformat()}",
                    contact_id=contact_id,
                    amount=pricing_result.final_price,
                    tier=classification,
                    pricing_multiplier=pricing_result.multiplier,
                    billing_period_start=active_subscription.current_period_start,
                    billing_period_end=active_subscription.current_period_end
                )

                # Record overage usage with subscription manager
                billing_result = await subscription_manager.bill_usage_overage(
                    subscription_id=active_subscription.id,
                    lead_id=usage_request.lead_id,
                    contact_id=contact_id,
                    lead_price=pricing_result.final_price,
                    tier=classification
                )

                if billing_result["success"]:
                    logger.info(
                        f"Successfully billed overage usage for contact {contact_id}",
                        extra={
                            "contact_id": contact_id,
                            "location_id": location_id,
                            "subscription_id": active_subscription.id,
                            "amount_billed": float(pricing_result.final_price),
                            "tier": classification,
                            "overage_lead_number": current_usage - active_subscription.usage_allowance,
                            "stripe_usage_record_id": billing_result.get("stripe_usage_record_id"),
                            "billing_period": billing_result.get("billing_period"),
                            "jorge_feature": "usage_based_billing"
                        }
                    )

                    # Track overage billing event
                    await analytics_service.track_event(
                        event_type="usage_overage_billed",
                        location_id=location_id,
                        contact_id=contact_id,
                        data={
                            "subscription_id": active_subscription.id,
                            "amount": float(pricing_result.final_price),
                            "tier": classification,
                            "lead_score": lead_score,
                            "overage_number": current_usage - active_subscription.usage_allowance,
                            "subscription_tier": active_subscription.tier.value,
                            "expected_roi": pricing_result.expected_roi,
                            "arr_impact": float(pricing_result.final_price) * 12  # Annualized impact
                        }
                    )

                else:
                    logger.error(
                        f"Failed to bill overage usage for contact {contact_id}",
                        extra={
                            "contact_id": contact_id,
                            "location_id": location_id,
                            "subscription_id": active_subscription.id,
                            "error": billing_result.get("error"),
                            "recoverable": billing_result.get("recoverable", True)
                        }
                    )

            except Exception as overage_error:
                logger.error(
                    f"Error processing usage overage billing for contact {contact_id}: {overage_error}",
                    extra={
                        "contact_id": contact_id,
                        "location_id": location_id,
                        "subscription_id": active_subscription.id,
                        "error": str(overage_error),
                        "error_type": type(overage_error).__name__
                    },
                    exc_info=True
                )

        else:
            # Within allowance - just track usage
            logger.info(
                f"Lead processing within subscription allowance for contact {contact_id}",
                extra={
                    "contact_id": contact_id,
                    "location_id": location_id,
                    "subscription_id": active_subscription.id,
                    "current_usage": current_usage,
                    "usage_allowance": active_subscription.usage_allowance,
                    "usage_percentage": round((current_usage / active_subscription.usage_allowance) * 100, 2),
                    "tier": classification,
                    "estimated_value": float(pricing_result.final_price),
                    "billing_status": "within_allowance"
                }
            )

            # Track usage within allowance for analytics
            await analytics_service.track_event(
                event_type="usage_within_allowance",
                location_id=location_id,
                contact_id=contact_id,
                data={
                    "subscription_id": active_subscription.id,
                    "current_usage": current_usage,
                    "usage_allowance": active_subscription.usage_allowance,
                    "tier": classification,
                    "lead_score": lead_score,
                    "estimated_value": float(pricing_result.final_price)
                }
            )

        # Check for usage threshold notifications
        threshold_result = await subscription_manager.handle_usage_threshold(
            location_id=location_id,
            current_usage=current_usage,
            period_usage_allowance=active_subscription.usage_allowance
        )

        if threshold_result.get("actions_taken"):
            logger.info(
                f"Usage threshold actions triggered for location {location_id}",
                extra={
                    "location_id": location_id,
                    "usage_percentage": threshold_result.get("usage_percentage"),
                    "threshold_level": threshold_result.get("threshold_level"),
                    "actions_taken": threshold_result.get("actions_taken"),
                    "overage_billing_active": threshold_result.get("overage_billing_active")
                }
            )

            # Track threshold events for customer success
            await analytics_service.track_event(
                event_type="usage_threshold_reached",
                location_id=location_id,
                contact_id=contact_id,
                data=threshold_result
            )

    except Exception as e:
        logger.error(
            f"Failed to process billing usage for contact {contact_id}",
            extra={
                "contact_id": contact_id,
                "location_id": location_id,
                "classification": classification,
                "lead_score": lead_score,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
