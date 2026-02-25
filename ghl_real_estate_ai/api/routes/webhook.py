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

import os
import random
import re
from datetime import datetime
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel

from ghl_real_estate_ai.api.schemas.billing import UsageRecordRequest
from ghl_real_estate_ai.api.schemas.ghl import (
    ActionType,
    GHLAction,
    GHLTagWebhookEvent,
    GHLWebhookEvent,
    GHLWebhookResponse,
    MessageDirection,
    MessageType,
)
from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.core.llm_client import LLMCircuitOpenError, LLMTimeoutError
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.jorge_config import settings as jorge_settings
from ghl_real_estate_ai.ghl_utils.jorge_rancho_config import rancho_config
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.attribution_analytics import AttributionAnalytics
from ghl_real_estate_ai.services.calendar_scheduler import CalendarScheduler
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.compliance_guard import ComplianceStatus, compliance_guard
from ghl_real_estate_ai.services.dynamic_pricing_optimizer import DynamicPricingOptimizer
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.hitl_gate import HITLGate
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService
from ghl_real_estate_ai.services.jorge.response_pipeline.factory import get_response_pipeline
from ghl_real_estate_ai.services.jorge.response_pipeline.models import ProcessingContext
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.services.lead_source_tracker import LeadSource, LeadSourceTracker
from ghl_real_estate_ai.services.mls_client import MLSClient
from ghl_real_estate_ai.models.lead_scoring import (
    ConditionRealism,
    FinancialReadinessScore,
    LeadIntentProfile,
    MotivationSignals,
    PriceResponsiveness,
    PsychologicalCommitmentScore,
    TimelineCommitment,
)
from ghl_real_estate_ai.services.security_framework import verify_webhook
from ghl_real_estate_ai.services.subscription_manager import SubscriptionManager
from ghl_real_estate_ai.services.tenant_service import TenantService

logger = get_logger(__name__)


def _signals_to_handoff_profile(contact_id: str, signals: dict) -> LeadIntentProfile:
    """Build a minimal LeadIntentProfile for handoff routing from raw intent signals.

    FRS/PCS are set to neutral values — only buyer/seller_intent_confidence matters
    for evaluate_handoff_from_profile() routing logic.
    """
    return LeadIntentProfile(
        lead_id=contact_id,
        frs=FinancialReadinessScore(
            total_score=50.0,
            motivation=MotivationSignals(score=50, category="Mixed Intent"),
            timeline=TimelineCommitment(score=50, category="Flexible"),
            condition=ConditionRealism(score=50, category="Negotiable"),
            price=PriceResponsiveness(score=50, category="Price-Flexible"),
            classification="Warm",
        ),
        pcs=PsychologicalCommitmentScore(
            total_score=50.0,
            response_velocity_score=50,
            message_length_score=50,
            question_depth_score=50,
            objection_handling_score=50,
            call_acceptance_score=50,
        ),
        next_best_action="Continue qualification",
        buyer_intent_confidence=signals.get("buyer_intent_score", 0.0),
        seller_intent_confidence=signals.get("seller_intent_score", 0.0),
        detected_intent_phrases=signals.get("detected_intent_phrases", []),
    )

SMS_MAX_CHARS = 320
router = APIRouter(prefix="/ghl", tags=["ghl"])

# Graceful fallback when Claude API is unavailable (timeout / circuit breaker)
LLM_FALLBACK_MSG = (
    "I'm having a brief connection issue — I'll follow up with you shortly. You can also reach Jorge directly."
)

# Initialize services for internal use and testing
conversation_manager = ConversationManager()
tenant_service = TenantService()
ghl_client_default = GHLClient()
lead_scorer = LeadScorer()
analytics_service = AnalyticsService()
pricing_optimizer = DynamicPricingOptimizer()
calendar_scheduler = CalendarScheduler()
lead_source_tracker = LeadSourceTracker()
attribution_analytics = AttributionAnalytics()
subscription_manager = SubscriptionManager()
handoff_service = JorgeHandoffService(analytics_service=analytics_service)
hitl_gate = HITLGate()
mls_client = MLSClient()

# FastAPI dependency injection - using @lru_cache for singleton behavior


@lru_cache(maxsize=1)
def _get_conversation_manager() -> ConversationManager:
    """Get ConversationManager singleton instance."""
    return conversation_manager


@lru_cache(maxsize=1)
def _get_ghl_client_default() -> GHLClient:
    """Get GHLClient default singleton instance."""
    return ghl_client_default


@lru_cache(maxsize=1)
def _get_lead_scorer() -> LeadScorer:
    """Get LeadScorer singleton instance."""
    return lead_scorer


@lru_cache(maxsize=1)
def _get_tenant_service() -> TenantService:
    """Get TenantService singleton instance."""
    return tenant_service


@lru_cache(maxsize=1)
def _get_analytics_service() -> AnalyticsService:
    """Get AnalyticsService singleton instance."""
    return analytics_service


@lru_cache(maxsize=1)
def _get_pricing_optimizer() -> DynamicPricingOptimizer:
    """Get DynamicPricingOptimizer singleton instance."""
    return pricing_optimizer


@lru_cache(maxsize=1)
def _get_calendar_scheduler() -> CalendarScheduler:
    """Get CalendarScheduler singleton instance."""
    return calendar_scheduler


@lru_cache(maxsize=1)
def _get_lead_source_tracker() -> LeadSourceTracker:
    """Get LeadSourceTracker singleton instance."""
    return lead_source_tracker


@lru_cache(maxsize=1)
def _get_attribution_analytics() -> AttributionAnalytics:
    """Get AttributionAnalytics singleton instance."""
    return attribution_analytics


@lru_cache(maxsize=1)
def _get_subscription_manager() -> SubscriptionManager:
    """Get SubscriptionManager singleton instance."""
    return subscription_manager


@lru_cache(maxsize=1)
def _get_handoff_service() -> JorgeHandoffService:
    """Get JorgeHandoffService singleton instance."""
    return handoff_service


@lru_cache(maxsize=1)
def _get_mls_client() -> MLSClient:
    """Get MLSClient singleton instance."""
    return mls_client


# Safe wrappers for background tasks to prevent silent delivery failures
async def safe_send_message(ghl_client, contact_id: str, message: str, channel=None):
    """Wrapper for send_message that handles errors and tags contact on failure."""
    try:
        await ghl_client.send_message(contact_id, message, channel=channel)
    except Exception as e:
        logger.error(f"Message delivery failed for contact {contact_id}: {e}")
        try:
            await ghl_client.add_tags(contact_id, ["Delivery-Failed"])
        except Exception as tag_error:
            logger.error(f"Failed to add Delivery-Failed tag for {contact_id}: {tag_error}")


async def safe_apply_actions(ghl_client, contact_id: str, actions: list):
    """Wrapper for apply_actions that handles errors and tags contact on failure."""
    try:
        await ghl_client.apply_actions(contact_id, actions)
    except Exception as e:
        logger.error(f"Action application failed for contact {contact_id}: {e}")
        try:
            await ghl_client.add_tags(contact_id, ["Delivery-Failed"])
        except Exception as tag_error:
            logger.error(f"Failed to add Delivery-Failed tag for {contact_id}: {tag_error}")


def _normalize_tags(raw_tags: list[str] | None) -> set[str]:
    """Normalize tags for case-insensitive matching with whitespace safety."""
    normalized: set[str] = set()
    for tag in raw_tags or []:
        if tag is None:
            continue
        value = str(tag).strip().lower()
        if value:
            normalized.add(value)
    return normalized


# Tags that the lead bot itself applies — a contact carrying ONLY these tags
# should still activate lead mode on subsequent turns (passthrough activation).
_LEAD_PASSTHROUGH_TAGS: frozenset[str] = frozenset(
    {"hot-lead", "warm-lead", "cold-lead", "lead-qualified"}
)


def _tag_present(tag: str | None, tags_lower: set[str]) -> bool:
    """Return True when a single tag exists in normalized tag set."""
    if not tag:
        return False
    return tag.strip().lower() in tags_lower


def _compute_mode_flags(
    tags_lower: set[str],
    *,
    should_deactivate: bool,
    seller_mode_enabled: bool,
    buyer_mode_enabled: bool,
    lead_mode_enabled: bool,
    buyer_activation_tag: str,
    lead_activation_tag: str,
) -> dict[str, bool]:
    """Compute bot mode flags in one place to keep routing deterministic."""
    return {
        "seller": (
            ("needs qualifying" in tags_lower or "seller-lead" in tags_lower)
            and seller_mode_enabled
            and not should_deactivate
        ),
        "buyer": _tag_present(buyer_activation_tag, tags_lower) and buyer_mode_enabled and not should_deactivate,
        "lead": (
            _tag_present(lead_activation_tag, tags_lower)
            or (not tags_lower and lead_mode_enabled)
            or (lead_mode_enabled and bool(tags_lower) and tags_lower.issubset(_LEAD_PASSTHROUGH_TAGS))
        ) and lead_mode_enabled and not should_deactivate,
    }


def _select_primary_mode(mode_flags: dict[str, bool]) -> str | None:
    """Deterministic mode priority: seller > buyer > lead."""
    if mode_flags.get("seller"):
        return "seller"
    if mode_flags.get("buyer"):
        return "buyer"
    if mode_flags.get("lead"):
        return "lead"
    return None


def _format_slot_options(options: list[dict]) -> str:
    lines = [f"{opt['label']}) {opt['display']}" for opt in options]
    return "Reply with 1, 2, or 3.\n" + "\n".join(lines)


def _select_slot_from_message(message: str, options: list[dict]) -> dict | None:
    msg = message.lower()
    digits = re.findall(r"\b([1-3])\b", msg)
    if len(digits) == 1:
        for opt in options:
            if opt.get("label") == digits[0]:
                return opt
    for opt in options:
        if opt.get("display", "").lower() in msg:
            return opt
    return None


def _detect_buy_sell_intent(message: str) -> str | None:
    """Detect whether an inbound message signals buyer or seller intent.

    Returns 'buyer', 'seller', or None if intent is unclear.
    Used by the lead mode handler to route T2 responses automatically.
    """
    msg = message.lower()
    seller_signals = {
        "sell", "selling", "list", "listing", "want to sell", "looking to sell",
        "thinking about selling", "put it on the market", "on the market",
        "my home", "my house", "my property", "my condo", "my place",
    }
    buyer_signals = {
        "buy", "buying", "purchase", "purchasing", "looking for", "find a home",
        "looking to buy", "want to buy", "interested in buying", "find a house",
        "searching for", "need a home", "need a house", "want a home", "want a house",
        "first home", "first house", "investment property", "rental property",
    }
    seller_score = sum(1 for s in seller_signals if s in msg)
    buyer_score = sum(1 for s in buyer_signals if s in msg)
    if seller_score > buyer_score:
        return "seller"
    if buyer_score > seller_score:
        return "buyer"
    return None


async def _get_tenant_ghl_client(
    location_id: str, tenant_service: TenantService, ghl_client_default: GHLClient
) -> GHLClient:
    tenant_config = await tenant_service.get_tenant_config(location_id)
    if tenant_config and tenant_config.get("ghl_api_key"):
        return GHLClient(api_key=tenant_config["ghl_api_key"], location_id=location_id)
    return ghl_client_default


@router.post("/tag-webhook", response_model=GHLWebhookResponse)
@verify_webhook("ghl")
async def handle_ghl_tag_webhook(
    request: Request,
    event: GHLTagWebhookEvent,
    background_tasks: BackgroundTasks,
    conversation_manager: ConversationManager = Depends(_get_conversation_manager),
    tenant_service: TenantService = Depends(_get_tenant_service),
    ghl_client_default: GHLClient = Depends(_get_ghl_client_default),
    analytics_service: AnalyticsService = Depends(_get_analytics_service),
):
    """
    Handle tag-added webhook from GoHighLevel.

    Sends initial outreach when the lead activation tag is applied
    and no prior conversation exists.
    """
    contact_id = event.contact_id
    location_id = event.location_id
    tag = event.tag

    # Accept both the configured LEAD_ACTIVATION_TAG and the legacy "needs qualifying"
    # tag so that any in-flight contacts tagged before the migration still get outreach.
    _lead_tag = jorge_settings.LEAD_ACTIVATION_TAG.strip().lower()
    if tag.strip().lower() not in (_lead_tag, "needs qualifying"):
        return GHLWebhookResponse(success=True, message="Tag ignored", actions=[])

    context = await conversation_manager.get_context(contact_id, location_id)
    if context.get("initial_outreach_sent"):
        return GHLWebhookResponse(success=True, message="Initial outreach already sent", actions=[])

    if context.get("conversation_history"):
        return GHLWebhookResponse(success=True, message="Conversation already started", actions=[])

    contact_name = event.contact.first_name if event.contact and event.contact.first_name else "there"
    outreach_template = random.choice(rancho_config.INITIAL_OUTREACH_MESSAGES)
    outreach_message = outreach_template.format(name=contact_name)

    current_ghl_client = await _get_tenant_ghl_client(location_id, tenant_service, ghl_client_default)

    # Send SMS outreach
    background_tasks.add_task(
        safe_send_message,
        current_ghl_client,
        contact_id,
        outreach_message,
        MessageType.SMS,
    )

    # Track analytics
    background_tasks.add_task(
        analytics_service.track_event,
        event_type="initial_outreach_sent",
        location_id=location_id,
        contact_id=contact_id,
        data={"tag": tag},
    )

    # Persist idempotency flag
    context["initial_outreach_sent"] = True
    context["initial_outreach_sent_at"] = datetime.utcnow().isoformat()
    await conversation_manager.memory_service.save_context(contact_id, context, location_id=location_id)

    return GHLWebhookResponse(success=True, message=outreach_message, actions=[])


@router.post("/webhook", response_model=GHLWebhookResponse)
@verify_webhook("ghl")
async def handle_ghl_webhook(
    request: Request,
    event: GHLWebhookEvent,
    background_tasks: BackgroundTasks,
    conversation_manager: ConversationManager = Depends(_get_conversation_manager),
    ghl_client_default: GHLClient = Depends(_get_ghl_client_default),
    tenant_service: TenantService = Depends(_get_tenant_service),
    analytics_service: AnalyticsService = Depends(_get_analytics_service),
    lead_scorer: LeadScorer = Depends(_get_lead_scorer),
    pricing_optimizer: DynamicPricingOptimizer = Depends(_get_pricing_optimizer),
    calendar_scheduler: CalendarScheduler = Depends(_get_calendar_scheduler),
    lead_source_tracker: LeadSourceTracker = Depends(_get_lead_source_tracker),
    attribution_analytics: AttributionAnalytics = Depends(_get_attribution_analytics),
    subscription_manager: SubscriptionManager = Depends(_get_subscription_manager),
    handoff_service: JorgeHandoffService = Depends(_get_handoff_service),
    mls_client: MLSClient = Depends(_get_mls_client),
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
    # Resolve dependencies if they are Depends markers (happens in tests calling __wrapped__)
    if hasattr(conversation_manager, "dependency"):
        conversation_manager = _get_conversation_manager()
    if hasattr(ghl_client_default, "dependency"):
        ghl_client_default = _get_ghl_client_default()
    if hasattr(tenant_service, "dependency"):
        tenant_service = _get_tenant_service()
    if hasattr(analytics_service, "dependency"):
        analytics_service = _get_analytics_service()
    if hasattr(lead_scorer, "dependency"):
        lead_scorer = _get_lead_scorer()
    if hasattr(pricing_optimizer, "dependency"):
        pricing_optimizer = _get_pricing_optimizer()
    if hasattr(calendar_scheduler, "dependency"):
        calendar_scheduler = _get_calendar_scheduler()
    if hasattr(lead_source_tracker, "dependency"):
        lead_source_tracker = _get_lead_source_tracker()
    if hasattr(attribution_analytics, "dependency"):
        attribution_analytics = _get_attribution_analytics()
    if hasattr(subscription_manager, "dependency"):
        subscription_manager = _get_subscription_manager()
    if hasattr(handoff_service, "dependency"):
        handoff_service = _get_handoff_service()
    if hasattr(mls_client, "dependency"):
        mls_client = _get_mls_client()

    # Log raw payload summary for debugging (first 500 chars, no PII in production)
    try:
        raw_body = await request.body()
        logger.debug(
            f"GHL webhook raw payload (first 500 chars): {raw_body[:500]}",
            extra={"endpoint": "/api/ghl/webhook"},
        )
    except Exception:
        pass

    contact_id = event.contact_id
    location_id = event.location_id
    user_message = event.message.body
    tags = (event.contact.tags if event.contact else []) or []

    # If tags are absent (GHL sent native flat format without contact tags),
    # fetch the contact's actual tags from the GHL API so activation checks work.
    if not tags and contact_id:
        try:
            contact_data = await ghl_client_default.get_contact(contact_id)
            # GHL v2 API wraps response as {"contact": {...}, "traceId": "..."}
            contact_obj = (contact_data or {}).get("contact", contact_data or {})
            tags = contact_obj.get("tags", [])
            # Also backfill the contact object so downstream code has a name, phone, etc.
            if event.contact and not event.contact.first_name:
                event.contact.first_name = contact_obj.get("firstName", "")
                event.contact.last_name = contact_obj.get("lastName", "")
                event.contact.phone = contact_obj.get("phone", "")
                event.contact.email = contact_obj.get("email", "")
                event.contact.tags = tags
            logger.info(
                f"Fetched {len(tags)} tag(s) from GHL API for contact {contact_id} (not included in webhook payload)"
            )
        except Exception as _tag_fetch_err:
            logger.warning(
                f"Could not fetch tags for contact {contact_id} from GHL API: {_tag_fetch_err}. "
                "Proceeding with empty tags — GHL workflow filter guarantees activation tag is present."
            )
            # Trust the GHL workflow filter: webhook only fires for tagged contacts.
            # Keep tags empty — lead bot handles unclassified contacts when JORGE_LEAD_MODE=true.
            tags = []

    # Normalize tags for case-insensitive comparisons throughout this request.
    tags_lower = _normalize_tags(tags)

    # INPUT LENGTH GUARD: Cap inbound messages to prevent token abuse
    MAX_INBOUND_LENGTH = 2_000  # No legitimate SMS/chat exceeds this
    if len(user_message) > MAX_INBOUND_LENGTH:
        logger.warning(
            f"Oversized inbound message truncated ({len(user_message)} chars)",
            extra={"original_length": len(user_message), "contact_id": contact_id},
        )
        user_message = user_message[:MAX_INBOUND_LENGTH]

    # LOOPBACK PROTECTION: Ignore outbound messages (sent by bot or agent)
    if event.message.direction == MessageDirection.OUTBOUND:
        logger.info(f"Ignoring outbound message for contact {contact_id}")
        return GHLWebhookResponse(
            success=True,
            message="Ignoring outbound message",
            actions=[],
        )

    # IDEMPOTENCY GUARD: Prevent duplicate bot responses from Render cold-start retries.
    # GHL retries the webhook 3-4x when the first attempt times out (50 s+ cold start).
    # Each retry carries the same contact_id + message body, so we fingerprint on those
    # two fields.  A 90-second TTL covers every realistic retry window while still
    # allowing a contact to send the same text again later (e.g. "yes" twice in one day).
    _idem_key = f"webhook:idem:{contact_id}:{hash(user_message)}"
    try:
        _cache = get_cache_service()
        _already_processing = await _cache.get(_idem_key)
        if _already_processing:
            logger.info(
                "Duplicate webhook suppressed for contact %s (idempotency key hit) — "
                "returning 200 without re-processing",
                contact_id,
            )
            return GHLWebhookResponse(success=True, message="duplicate suppressed", actions=[])
        # Mark this (contact, message) pair as in-flight for 90 seconds
        await _cache.set(_idem_key, "1", ttl=90)
    except Exception as _idem_err:
        # Never let idempotency machinery block a real message — fail open
        logger.warning("Idempotency cache check failed (%s) — proceeding without dedup", _idem_err)

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
    deactivation_tags = settings.deactivation_tags  # e.g., ["AI-Off", "Qualified", "Stop-Bot"]

    should_activate = any(_tag_present(tag, tags_lower) for tag in activation_tags)
    # Seller-mode tags also count as activation when seller mode is enabled.
    if not should_activate and jorge_settings.JORGE_SELLER_MODE:
        should_activate = "needs qualifying" in tags_lower or "seller-lead" in tags_lower
    # Buyer-mode tag also counts as activation when buyer mode is enabled
    if not should_activate and jorge_settings.JORGE_BUYER_MODE:
        should_activate = _tag_present(jorge_settings.BUYER_ACTIVATION_TAG, tags_lower)
    # Lead-mode tag also counts as activation when lead mode is enabled.
    # Unclassified contacts (empty tags) are also handled by lead bot when JORGE_LEAD_MODE=true.
    if not should_activate and jorge_settings.JORGE_LEAD_MODE:
        should_activate = (
            _tag_present(jorge_settings.LEAD_ACTIVATION_TAG, tags_lower)
            or not tags_lower
            or (bool(tags_lower) and tags_lower.issubset(_LEAD_PASSTHROUGH_TAGS))
        )
    should_deactivate = any(_tag_present(tag, tags_lower) for tag in deactivation_tags)

    if not should_activate:
        logger.info(f"AI not triggered for contact {contact_id} - activation tag not present")
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
        logger.info(f"AI deactivated for contact {contact_id} - deactivation tag present")
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

    mode_flags = _compute_mode_flags(
        tags_lower,
        should_deactivate=should_deactivate,
        seller_mode_enabled=jorge_settings.JORGE_SELLER_MODE,
        buyer_mode_enabled=jorge_settings.JORGE_BUYER_MODE,
        lead_mode_enabled=jorge_settings.JORGE_LEAD_MODE,
        buyer_activation_tag=jorge_settings.BUYER_ACTIVATION_TAG,
        lead_activation_tag=jorge_settings.LEAD_ACTIVATION_TAG,
    )
    jorge_seller_mode = mode_flags["seller"]
    jorge_buyer_mode = mode_flags["buyer"]
    jorge_lead_mode = mode_flags["lead"]
    primary_mode = _select_primary_mode(mode_flags)

    logger.info(
        "Webhook routing precheck",
        extra={
            "contact_id": contact_id,
            "location_id": location_id,
            "tags_raw": tags,
            "tags_lower": sorted(tags_lower),
            "activation_tags": activation_tags,
            "deactivation_tags": deactivation_tags,
            "should_activate": should_activate,
            "should_deactivate": should_deactivate,
            "jorge_seller_mode": jorge_seller_mode,
            "jorge_buyer_mode": jorge_buyer_mode,
            "jorge_lead_mode": jorge_lead_mode,
            "primary_mode": primary_mode,
        },
    )

    # Opt-out detection (Jorge spec: "end automation immediately")
    OPT_OUT_PHRASES = [
        "stop",
        "unsubscribe",
        "don't contact",
        "dont contact",
        "remove me",
        "not interested",
        "no more",
        "no more messages",
        "opt out",
        "leave me alone",
        "take me off",
        "no thanks",
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

    # Pending appointment selection flow (slot offer -> confirmation)
    context = await conversation_manager.get_context(contact_id, location_id)
    pending_appointment = context.get("pending_appointment")
    if pending_appointment and pending_appointment.get("status") == "awaiting_selection":
        try:
            from ghl_real_estate_ai.services.calendar_scheduler import AppointmentType, TimeSlot, get_smart_scheduler

            # Initialize GHL client with tenant config if available
            current_ghl_client = await _get_tenant_ghl_client(location_id, tenant_service, ghl_client_default)

            selected = _select_slot_from_message(user_message, pending_appointment.get("options", []))
            if selected:
                start_time = datetime.fromisoformat(selected["start_time"])
                end_time = datetime.fromisoformat(selected["end_time"])
                appointment_type = AppointmentType(selected["appointment_type"])

                time_slot = TimeSlot(
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=int((end_time - start_time).total_seconds() / 60),
                    appointment_type=appointment_type,
                )

                scheduler = get_smart_scheduler(current_ghl_client)
                extracted_data = context.get("seller_preferences", {})
                contact_info = {
                    "contact_id": contact_id,
                    "first_name": event.contact.first_name or "Lead",
                    "last_name": event.contact.last_name,
                    "phone": event.contact.phone,
                    "email": event.contact.email,
                }

                booking_result = await scheduler.book_appointment(
                    contact_id=contact_id,
                    contact_info=contact_info,
                    time_slot=time_slot,
                    lead_score=extracted_data.get("questions_answered", 0),
                    extracted_data=extracted_data,
                )

                if booking_result.success:
                    response_message = (
                        f"Perfect, I have you down for {selected['display']}. You'll get a confirmation text shortly."
                    )

                    background_tasks.add_task(
                        safe_send_message,
                        current_ghl_client,
                        contact_id,
                        response_message,
                        event.message.type,
                    )

                    if booking_result.confirmation_actions:
                        background_tasks.add_task(
                            safe_apply_actions,
                            current_ghl_client,
                            contact_id,
                            booking_result.confirmation_actions,
                        )

                    context["pending_appointment"] = None
                    await conversation_manager.memory_service.save_context(contact_id, context, location_id=location_id)

                    background_tasks.add_task(
                        analytics_service.track_event,
                        event_type="appointment_slot_confirmed",
                        location_id=location_id,
                        contact_id=contact_id,
                        data={"appointment_time": selected["display"]},
                    )

                    return GHLWebhookResponse(
                        success=True,
                        message=response_message,
                        actions=booking_result.confirmation_actions,
                    )

                # Booking failed -> manual fallback
                fallback_message = (
                    "I had trouble booking that time. I'll manually check Jorge's calendar "
                    "and get back to you with options."
                )
                background_tasks.add_task(
                    safe_send_message,
                    current_ghl_client,
                    contact_id,
                    fallback_message,
                    event.message.type,
                )
                background_tasks.add_task(
                    safe_apply_actions,
                    current_ghl_client,
                    contact_id,
                    [GHLAction(type=ActionType.ADD_TAG, tag="Needs-Manual-Scheduling")],
                )

                context["pending_appointment"] = None
                await conversation_manager.memory_service.save_context(contact_id, context, location_id=location_id)

                background_tasks.add_task(
                    analytics_service.track_event,
                    event_type="appointment_slot_escalated_manual",
                    location_id=location_id,
                    contact_id=contact_id,
                    data={"reason": "booking_failed"},
                )

                return GHLWebhookResponse(
                    success=True,
                    message=fallback_message,
                    actions=[GHLAction(type=ActionType.ADD_TAG, tag="Needs-Manual-Scheduling")],
                )

            # No selection parsed: re-offer or escalate
            attempts = int(pending_appointment.get("attempts", 0)) + 1
            pending_appointment["attempts"] = attempts
            context["pending_appointment"] = pending_appointment
            await conversation_manager.memory_service.save_context(contact_id, context, location_id=location_id)

            if attempts <= 2:
                options_message = _format_slot_options(pending_appointment.get("options", []))
                response_message = "Which time works for you?\n" + options_message
                background_tasks.add_task(
                    safe_send_message,
                    current_ghl_client,
                    contact_id,
                    response_message,
                    event.message.type,
                )
                return GHLWebhookResponse(success=True, message=response_message, actions=[])

            fallback_message = "No worries, I'll manually check Jorge's calendar and follow up with options."
            background_tasks.add_task(
                safe_send_message,
                current_ghl_client,
                contact_id,
                fallback_message,
                event.message.type,
            )
            background_tasks.add_task(
                safe_apply_actions,
                current_ghl_client,
                contact_id,
                [GHLAction(type=ActionType.ADD_TAG, tag="Needs-Manual-Scheduling")],
            )
            context["pending_appointment"] = None
            await conversation_manager.memory_service.save_context(contact_id, context, location_id=location_id)

            background_tasks.add_task(
                analytics_service.track_event,
                event_type="appointment_slot_escalated_manual",
                location_id=location_id,
                contact_id=contact_id,
                data={"reason": "no_selection"},
            )

            return GHLWebhookResponse(
                success=True,
                message=fallback_message,
                actions=[GHLAction(type=ActionType.ADD_TAG, tag="Needs-Manual-Scheduling")],
            )
        except Exception as e:
            logger.error(f"Pending appointment handling failed for {contact_id}: {e}", exc_info=True)

    # Step -0.5: Seller has strict priority for needs-qualifying flow.
    if jorge_seller_mode:
        logger.info(f"Jorge seller mode activated for contact {contact_id}")
        current_ghl_client = ghl_client_default
        try:
            # Route to Jorge's seller engine
            from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

            # Get tenant configuration first
            tenant_config = await tenant_service.get_tenant_config(location_id)

            # Initialize GHL client
            if tenant_config and tenant_config.get("ghl_api_key"):
                current_ghl_client = GHLClient(api_key=tenant_config["ghl_api_key"], location_id=location_id)

            # Initialize Jorge's seller engine
            jorge_engine = JorgeSellerEngine(conversation_manager, current_ghl_client, mls_client=mls_client)

            # Snapshot history BEFORE process_seller_response so is_first_message
            # is accurate: the engine calls update_context internally, which means
            # fetching history after would always show a non-empty history on T1.
            seller_history_snapshot = await conversation_manager.get_conversation_history(
                contact_id, location_id=location_id
            )

            # Process seller response
            seller_result = await jorge_engine.process_seller_response(
                contact_id=contact_id, user_message=user_message, location_id=location_id, tenant_config=tenant_config
            )

            # Apply Jorge's seller actions (tags, workflows)
            actions = []
            if seller_result.get("actions"):
                for action_data in seller_result["actions"]:
                    if action_data["type"] == "add_tag":
                        actions.append(GHLAction(type=ActionType.ADD_TAG, tag=action_data["tag"]))
                    elif action_data["type"] == "remove_tag":
                        actions.append(GHLAction(type=ActionType.REMOVE_TAG, tag=action_data["tag"]))
                    elif action_data["type"] == "trigger_workflow":
                        actions.append(
                            GHLAction(type=ActionType.TRIGGER_WORKFLOW, workflow_id=action_data["workflow_id"])
                        )
                    elif action_data["type"] == "update_custom_field":
                        actions.append(
                            GHLAction(
                                type=ActionType.UPDATE_CUSTOM_FIELD,
                                field=action_data["field"],
                                value=action_data["value"],
                            )
                        )

            # Track Jorge seller analytics
            background_tasks.add_task(
                analytics_service.track_event,
                event_type="jorge_seller_interaction",
                location_id=location_id,
                contact_id=contact_id,
                data={
                    "temperature": seller_result["temperature"],
                    "questions_answered": seller_result.get("questions_answered", 0),
                    "message_length": len(seller_result["message"]),
                },
            )

            # Run through response pipeline (AI disclosure + SMS truncation + spam guard)
            final_seller_msg = seller_result["message"]
            pipeline_context = ProcessingContext(
                contact_id=contact_id,
                bot_mode="seller",
                channel="sms",
                user_message=user_message,
                is_first_message=not seller_history_snapshot,
            )
            pipeline = get_response_pipeline()
            processed = await pipeline.process(final_seller_msg, pipeline_context)
            final_seller_msg = processed.message

            # --- BULLETPROOF COMPLIANCE INTERCEPTOR ---
            status, reason, violations = await compliance_guard.audit_message(
                final_seller_msg, contact_context={"contact_id": contact_id, "mode": "seller"}
            )

            if status == ComplianceStatus.BLOCKED:
                logger.warning(f"Compliance BLOCKED message for {contact_id}: {reason}. Violations: {violations}")
                final_seller_msg = "Let's stick to the facts about your property. What price are you looking to get?"
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Compliance-Alert"))

            # --- CROSS-BOT HANDOFF CHECK ---
            if seller_result.get("handoff_signals"):
                handoff = await handoff_service.evaluate_handoff_from_profile(
                    current_bot="seller",
                    contact_id=contact_id,
                    conversation_history=[],
                    intent_profile=_signals_to_handoff_profile(contact_id, seller_result["handoff_signals"]),
                )
                if handoff:
                    handoff_actions = await handoff_service.execute_handoff(
                        handoff, contact_id, location_id=location_id
                    )
                    for ha in handoff_actions:
                        if ha["type"] == "add_tag":
                            actions.append(GHLAction(type=ActionType.ADD_TAG, tag=ha["tag"]))
                        elif ha["type"] == "remove_tag":
                            actions.append(GHLAction(type=ActionType.REMOVE_TAG, tag=ha["tag"]))

            # --- HITL GATE: High-Value Human-in-the-Loop ---
            property_value = seller_result.get("estimated_value") or seller_result.get("property_value")
            if hitl_gate.evaluate(seller_result, property_value):
                draft_msg = (
                    f"DRAFT RESPONSE:\n{seller_result.get('response_content', final_seller_msg)}\n\n"
                    f"FRS={seller_result.get('frs_score', 0):.0f} "
                    f"PCS={seller_result.get('pcs_score', 0):.0f}"
                )
                background_tasks.add_task(
                    current_ghl_client.post_internal_note,
                    contact_id,
                    draft_msg,
                )
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="HITL-Review"))
                seller_result["requires_human_approval"] = True

                logger.info(
                    f"HITL gate activated for seller {contact_id} — SMS suppressed, draft posted",
                    extra={"contact_id": contact_id, "property_value": property_value},
                )

                return GHLWebhookResponse(
                    success=True,
                    message="[HITL] Draft posted for human review",
                    actions=actions,
                )

            logger.info(
                f"Jorge seller processing completed for {contact_id}",
                extra={
                    "contact_id": contact_id,
                    "temperature": seller_result["temperature"],
                    "questions_answered": seller_result.get("questions_answered", 0),
                    "actions_count": len(actions),
                    "compliance_status": status.value,
                },
            )

            # Note: seller engine calls update_context internally (success + error paths)

            # Send the seller response via GHL API (background task)
            background_tasks.add_task(
                safe_send_message,
                current_ghl_client,
                contact_id,
                final_seller_msg,
                event.message.type,
            )

            # Apply tags and actions via GHL API (background task)
            if actions:
                background_tasks.add_task(
                    safe_apply_actions,
                    current_ghl_client,
                    contact_id,
                    actions,
                )

            # Track billing and pricing (Jorge's revenue foundation)
            background_tasks.add_task(
                _calculate_lead_pricing,
                contact_id,
                location_id,
                context,
                pricing_optimizer,
                analytics_service,
            )
            background_tasks.add_task(
                _handle_billing_usage,
                contact_id,
                location_id,
                seller_result.get("questions_answered", 0),
                seller_result.get("seller_data", {}),
                seller_result["temperature"],
                subscription_manager,
                pricing_optimizer,
                analytics_service,
            )

            return GHLWebhookResponse(
                success=True,
                message=final_seller_msg,
                actions=actions,
            )

        except Exception as e:
            logger.error(f"Jorge seller mode processing failed for contact {contact_id}: {str(e)}", exc_info=True)
            # Do not fall through to other bot modes when seller preconditions are met.
            seller_rescue_msg = "What's got you considering selling? And where would you be looking to move?"
            # Route through pipeline so SB 243 [AI-assisted message] footer is appended.
            try:
                rescue_pipeline_context = ProcessingContext(
                    contact_id=contact_id,
                    bot_mode="seller",
                    channel=event.message.type,
                    user_message=user_message,
                )
                rescue_pipeline = get_response_pipeline()
                rescue_processed = await rescue_pipeline.process(seller_rescue_msg, rescue_pipeline_context)
                seller_rescue_msg = rescue_processed.message
            except Exception as pipeline_err:
                logger.error(f"Rescue pipeline failed for contact {contact_id}: {pipeline_err}")
                # Pipeline failed — send message as-is
                pass
            background_tasks.add_task(
                safe_send_message,
                current_ghl_client,
                contact_id,
                seller_rescue_msg,
                event.message.type,
            )
            return GHLWebhookResponse(
                success=True,
                message=seller_rescue_msg,
                actions=[],
            )

    # Step -0.4: Check for Jorge's Buyer Mode (Buyer-Lead tag + JORGE_BUYER_MODE)

    if jorge_buyer_mode:
        logger.info(f"Jorge buyer mode activated for contact {contact_id}")
        try:
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            # Get tenant configuration
            tenant_config = await tenant_service.get_tenant_config(location_id)

            # Initialize GHL client
            current_ghl_client = ghl_client_default
            if tenant_config and tenant_config.get("ghl_api_key"):
                current_ghl_client = GHLClient(api_key=tenant_config["ghl_api_key"], location_id=location_id)

            # Build conversation history from manager
            history = await conversation_manager.get_conversation_history(contact_id, location_id=location_id)
            conversation_history = history if history else [{"role": "user", "content": user_message}]
            # Ensure current message is included
            if not conversation_history or conversation_history[-1].get("content") != user_message:
                conversation_history.append({"role": "user", "content": user_message})

            # Initialize and run buyer bot
            buyer_bot = JorgeBuyerBot()
            buyer_result = await buyer_bot.process_buyer_conversation(
                conversation_id=contact_id,
                user_message=user_message,
                buyer_name=event.contact.first_name or "there",
                conversation_history=conversation_history,
            )

            # Apply buyer bot actions (tags based on temperature)
            actions = []
            buyer_temp = buyer_result.get("buyer_temperature") or "cold"
            # buyer_temperature is never set by the LangGraph workflow, so derive from signals
            _resp_content_lower = buyer_result.get("response_content", "").lower()
            _conv_len = len(conversation_history) if conversation_history else 0
            _scheduling_response = (
                "morning or afternoon" in _resp_content_lower
                or "jorge's team will reach out" in _resp_content_lower
                or "jorge will reach out" in _resp_content_lower
                or "lock in a time" in _resp_content_lower
                or "set up tours" in _resp_content_lower
            )
            if buyer_result.get("is_qualified"):
                buyer_temp = "warm"
            elif _scheduling_response and _conv_len >= 3:
                # All qualification fields gathered — buyer is at least warm
                buyer_temp = "warm"
            # Upgrade cold→hot when buyer is fully committed: pre-approval + hard deadline + scheduling
            _pre_approved = any(
                kw in (user_message or "").lower()
                for kw in ("pre-approved", "pre approved", "preapproved", "approved up to", "approval letter")
            )
            _has_deadline = any(
                kw in " ".join(m.get("content", "") for m in (conversation_history or [])).lower()
                for kw in ("lease", "move in by", "by july", "by august", "by month", "closing date", "our deadline")
            )
            if buyer_temp == "warm" and _pre_approved and _has_deadline and _scheduling_response:
                buyer_temp = "hot"
            temp_tag_map = {"hot": "Hot-Buyer", "warm": "Warm-Buyer", "cold": "Cold-Buyer"}
            if buyer_temp in temp_tag_map:
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag=temp_tag_map[buyer_temp]))
                # Remove stale temperature tags to prevent accumulation (e.g. cold+warm)
                for temp_level, tag in temp_tag_map.items():
                    if temp_level != buyer_temp:
                        actions.append(GHLAction(type=ActionType.REMOVE_TAG, tag=tag))

            if buyer_result.get("is_qualified") or buyer_temp in ("warm", "hot"):
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Buyer-Qualified"))

            # --- BUYER CUSTOM FIELD SYNC ---
            # Write qualifying data to GHL contact record so Jorge can see buyer details
            _budget_range = buyer_result.get("budget_range")
            if _budget_range and settings.custom_field_budget:
                if isinstance(_budget_range, dict):
                    _budget_val = _budget_range.get("budget_max") or _budget_range.get("max", "")
                    if _budget_val:
                        actions.append(GHLAction(type=ActionType.UPDATE_CUSTOM_FIELD, field=settings.custom_field_budget, value=str(_budget_val)))
                elif isinstance(_budget_range, str) and _budget_range:
                    actions.append(GHLAction(type=ActionType.UPDATE_CUSTOM_FIELD, field=settings.custom_field_budget, value=_budget_range))

            _buyer_temp_field = os.getenv("CUSTOM_FIELD_BUYER_TEMPERATURE")
            if _buyer_temp_field and buyer_temp in ("hot", "warm", "cold"):
                actions.append(GHLAction(type=ActionType.UPDATE_CUSTOM_FIELD, field=_buyer_temp_field, value=buyer_temp))

            _pre_approval_field = os.getenv("CUSTOM_FIELD_PRE_APPROVAL_STATUS")
            if _pre_approval_field and _pre_approved:
                actions.append(GHLAction(type=ActionType.UPDATE_CUSTOM_FIELD, field=_pre_approval_field, value="pre-approved"))

            _prefs_field = os.getenv("CUSTOM_FIELD_PROPERTY_PREFERENCES")
            if _prefs_field:
                _prefs = buyer_result.get("property_preferences") or buyer_result.get("extracted_preferences") or {}
                if isinstance(_prefs, dict) and _prefs:
                    _prefs_str = "; ".join(f"{k}: {v}" for k, v in _prefs.items())[:200]
                    actions.append(GHLAction(type=ActionType.UPDATE_CUSTOM_FIELD, field=_prefs_field, value=_prefs_str))

            if buyer_temp == "hot" and jorge_settings.hot_buyer_workflow_id:
                actions.append(
                    GHLAction(type=ActionType.TRIGGER_WORKFLOW, workflow_id=jorge_settings.hot_buyer_workflow_id)
                )
            elif buyer_temp == "warm" and jorge_settings.warm_buyer_workflow_id:
                actions.append(
                    GHLAction(type=ActionType.TRIGGER_WORKFLOW, workflow_id=jorge_settings.warm_buyer_workflow_id)
                )

            # Track buyer analytics
            background_tasks.add_task(
                analytics_service.track_event,
                event_type="jorge_buyer_interaction",
                location_id=location_id,
                contact_id=contact_id,
                data={
                    "buyer_temperature": buyer_temp,
                    "is_qualified": buyer_result.get("is_qualified", False),
                    "financial_readiness": buyer_result.get("financial_readiness_score", 0),
                    "message_length": len(buyer_result.get("response_content", "")),
                },
            )

            # Run through response pipeline (AI disclosure + SMS truncation + spam guard)
            final_buyer_msg = buyer_result.get(
                "response_content", "I'd love to help you find the perfect property. What area are you looking in?"
            )
            pipeline_context = ProcessingContext(
                contact_id=contact_id,
                bot_mode="buyer",
                channel="sms",
                user_message=user_message,
                is_first_message=not history,
            )
            pipeline = get_response_pipeline()
            processed = await pipeline.process(final_buyer_msg, pipeline_context)
            final_buyer_msg = processed.message

            # --- BULLETPROOF COMPLIANCE INTERCEPTOR ---
            status, reason, violations = await compliance_guard.audit_message(
                final_buyer_msg, contact_context={"contact_id": contact_id, "mode": "buyer"}
            )

            if status == ComplianceStatus.BLOCKED:
                logger.warning(f"Compliance BLOCKED buyer message for {contact_id}: {reason}. Violations: {violations}")
                final_buyer_msg = (
                    "I'd love to help you find your next home. What's most important to you in a property?"
                )
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Compliance-Alert"))


            # --- CROSS-BOT HANDOFF CHECK ---
            if buyer_result.get("handoff_signals"):
                handoff = await handoff_service.evaluate_handoff_from_profile(
                    current_bot="buyer",
                    contact_id=contact_id,
                    conversation_history=conversation_history,
                    intent_profile=_signals_to_handoff_profile(contact_id, buyer_result["handoff_signals"]),
                )
                if handoff:
                    handoff_actions = await handoff_service.execute_handoff(
                        handoff, contact_id, location_id=location_id
                    )
                    for ha in handoff_actions:
                        if ha["type"] == "add_tag":
                            actions.append(GHLAction(type=ActionType.ADD_TAG, tag=ha["tag"]))
                        elif ha["type"] == "remove_tag":
                            actions.append(GHLAction(type=ActionType.REMOVE_TAG, tag=ha["tag"]))

            # --- HITL GATE: High-Value Human-in-the-Loop ---
            buyer_property_value = buyer_result.get("estimated_value") or buyer_result.get("property_value")
            if hitl_gate.evaluate(buyer_result, buyer_property_value):
                draft_msg = (
                    f"DRAFT RESPONSE:\n{buyer_result.get('response_content', final_buyer_msg)}\n\n"
                    f"Financial Readiness={buyer_result.get('financial_readiness', 0):.0f} "
                    f"Buying Motivation={buyer_result.get('buying_motivation_score', 0):.0f}"
                )
                background_tasks.add_task(
                    current_ghl_client.post_internal_note,
                    contact_id,
                    draft_msg,
                )
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag="HITL-Review"))
                buyer_result["requires_human_approval"] = True

                logger.info(
                    f"HITL gate activated for buyer {contact_id} — SMS suppressed, draft posted",
                    extra={"contact_id": contact_id, "property_value": buyer_property_value},
                )

                return GHLWebhookResponse(
                    success=True,
                    message="[HITL] Draft posted for human review",
                    actions=actions,
                )

            logger.info(
                f"Jorge buyer processing completed for {contact_id}",
                extra={
                    "contact_id": contact_id,
                    "buyer_temperature": buyer_temp,
                    "is_qualified": buyer_result.get("is_qualified", False),
                    "actions_count": len(actions),
                    "compliance_status": status.value,
                },
            )

            # Persist conversation history so next turn has bot reply context
            await conversation_manager.update_context(
                contact_id=contact_id,
                user_message=user_message,
                ai_response=final_buyer_msg,
                location_id=location_id,
            )

            # Send the buyer response via GHL API (background task)
            background_tasks.add_task(
                safe_send_message,
                current_ghl_client,
                contact_id,
                final_buyer_msg,
                event.message.type,
            )

            # Apply tags and actions via GHL API (background task)
            if actions:
                background_tasks.add_task(
                    safe_apply_actions,
                    current_ghl_client,
                    contact_id,
                    actions,
                )

            # Track billing and pricing (Jorge's revenue foundation)
            background_tasks.add_task(
                _calculate_lead_pricing,
                contact_id,
                location_id,
                context,
                pricing_optimizer,
                analytics_service,
            )
            background_tasks.add_task(
                _handle_billing_usage,
                contact_id,
                location_id,
                int(buyer_result.get("financial_readiness_score", 0) / 14),  # Estimate question count
                buyer_result.get("extracted_preferences", {}),
                buyer_temp,
                subscription_manager,
                pricing_optimizer,
                analytics_service,
            )

            return GHLWebhookResponse(
                success=True,
                message=final_buyer_msg,
                actions=actions,
            )

        except Exception as e:
            logger.error(f"Jorge buyer mode processing failed for contact {contact_id}: {str(e)}", exc_info=True)
            # Do not fall through to lead bot — buyer contact would get wrong personality and scoring.
            try:
                background_tasks.add_task(ghl_client_default.add_tags, contact_id, ["Bot-Fallback-Active"])
            except Exception as tag_error:
                logger.error(f"Failed to add Bot-Fallback-Active tag: {tag_error}")
            buyer_rescue_msg = "Thanks for reaching out! Could you tell me more about what you're looking for in a home?"
            # Route through pipeline so SB 243 [AI-assisted message] footer is appended.
            try:
                rescue_pipeline_context = ProcessingContext(
                    contact_id=contact_id,
                    bot_mode="buyer",
                    channel=event.message.type,
                    user_message=user_message,
                )
                rescue_pipeline = get_response_pipeline()
                rescue_processed = await rescue_pipeline.process(buyer_rescue_msg, rescue_pipeline_context)
                buyer_rescue_msg = rescue_processed.message
            except Exception as pipeline_err:
                logger.error(f"Buyer rescue pipeline failed for contact {contact_id}: {pipeline_err}")
                pass  # Pipeline failed — send message as-is
            background_tasks.add_task(
                safe_send_message,
                current_ghl_client,
                contact_id,
                buyer_rescue_msg,
                event.message.type,
            )
            return GHLWebhookResponse(
                success=True,
                message=buyer_rescue_msg,
                actions=[],
            )

    # Step -0.3: Check for Jorge's Lead Mode (LEAD_ACTIVATION_TAG + JORGE_LEAD_MODE)

    if jorge_lead_mode:
        # Collision guard: if the contact carries the seller tag AND seller mode is live,
        # that means they're already in the seller pipeline — skip lead bot to avoid race.
        # NOTE: with LEAD_ACTIVATION_TAG=lead-bot (distinct from "needs qualifying") this
        # collision should never happen; the guard is a belt-and-suspenders safety net.
        _lead_tag_is_seller_tag = (
            jorge_settings.LEAD_ACTIVATION_TAG.lower() in ("needs qualifying", "seller-lead")
        )
        if jorge_seller_mode and _lead_tag_is_seller_tag and "needs qualifying" in tags_lower:
            logger.warning(
                "Dual-bot collision detected: contact %s has 'Needs Qualifying' tag with both "
                "seller and lead mode active (LEAD_ACTIVATION_TAG overlaps seller tag) — "
                "skipping lead bot. Fix: set LEAD_ACTIVATION_TAG=lead-bot in Render env vars.",
                contact_id,
            )
        else:
            logger.info(f"Jorge lead mode activated for contact {contact_id}")
            try:
                from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow

                # Get tenant configuration
                tenant_config = await tenant_service.get_tenant_config(location_id)

                # Initialize GHL client
                current_ghl_client = ghl_client_default
                if tenant_config and tenant_config.get("ghl_api_key"):
                    current_ghl_client = GHLClient(api_key=tenant_config["ghl_api_key"], location_id=location_id)

                # Build conversation history from manager
                history = await conversation_manager.get_conversation_history(contact_id, location_id=location_id)
                conversation_history = history if history else [{"role": "user", "content": user_message}]
                # Ensure current message is included
                if not conversation_history or conversation_history[-1].get("content") != user_message:
                    conversation_history.append({"role": "user", "content": user_message})

                # Determine sequence_day from first contact timestamp
                lead_ctx = await conversation_manager.get_context(contact_id, location_id)
                first_contact = lead_ctx.get("first_contact_at")
                is_lead_first_message = not first_contact  # True ONLY on genuine T1
                if not first_contact:
                    lead_ctx["first_contact_at"] = datetime.utcnow().isoformat()
                    sequence_day = 0
                else:
                    delta = datetime.utcnow() - datetime.fromisoformat(first_contact)
                    sequence_day = delta.days
                await conversation_manager.memory_service.save_context(contact_id, lead_ctx, location_id=location_id)

                # ── BUY/SELL QUALIFYING LAYER ─────────────────────────────────────
                # T1: On first ever contact, skip the full LangGraph flow and send a
                #     simple "buy or sell?" qualifying question so we can route the
                #     lead to the right specialist bot on the very next reply.
                # T2: On the second message, detect intent and apply routing tags so
                #     the seller or buyer bot takes over from the next turn onward.
                # If intent is still unclear, fall through to the normal lead bot.
                # ──────────────────────────────────────────────────────────────────
                contact_first_name = (
                    event.contact.first_name if event.contact and event.contact.first_name else "there"
                )

                if is_lead_first_message:
                    # T1 — send the qualifying question and return early
                    t1_message = (
                        f"Hey {contact_first_name}! Are you looking to buy or sell "
                        f"in the Rancho Cucamonga area?"
                    )
                    logger.info(
                        "Lead T1 qualifying question sent to %s — bypassing LangGraph", contact_id
                    )
                    background_tasks.add_task(
                        safe_send_message,
                        current_ghl_client,
                        contact_id,
                        t1_message,
                        event.message.type,
                    )
                    await conversation_manager.update_context(
                        contact_id=contact_id,
                        user_message=user_message,
                        ai_response=t1_message,
                        location_id=location_id,
                    )
                    return JSONResponse(
                        status_code=200,
                        content={"status": "ok", "mode": "lead_t1_qualify"},
                    )

                # T2 — detect intent from the contact's reply and route accordingly
                detected_intent = _detect_buy_sell_intent(user_message)
                if detected_intent == "seller":
                    logger.info(
                        "Lead T2 seller intent detected for %s — routing to seller bot", contact_id
                    )
                    routing_actions = [
                        GHLAction(type=ActionType.ADD_TAG, tag="Needs Qualifying"),
                        GHLAction(type=ActionType.REMOVE_TAG, tag=jorge_settings.LEAD_ACTIVATION_TAG),
                    ]
                    t2_message = (
                        f"Got it, {contact_first_name}! What's the address of the property "
                        f"you're thinking about selling?"
                    )
                    background_tasks.add_task(
                        safe_send_message,
                        current_ghl_client,
                        contact_id,
                        t2_message,
                        event.message.type,
                    )
                    background_tasks.add_task(
                        safe_apply_actions,
                        current_ghl_client,
                        contact_id,
                        routing_actions,
                    )
                    await conversation_manager.update_context(
                        contact_id=contact_id,
                        user_message=user_message,
                        ai_response=t2_message,
                        location_id=location_id,
                    )
                    return JSONResponse(
                        status_code=200,
                        content={"status": "ok", "mode": "lead_t2_routed_seller"},
                    )

                if detected_intent == "buyer":
                    logger.info(
                        "Lead T2 buyer intent detected for %s — routing to buyer bot", contact_id
                    )
                    routing_actions = [
                        GHLAction(type=ActionType.ADD_TAG, tag=jorge_settings.BUYER_ACTIVATION_TAG),
                        GHLAction(type=ActionType.REMOVE_TAG, tag=jorge_settings.LEAD_ACTIVATION_TAG),
                    ]
                    t2_message = (
                        f"Perfect, {contact_first_name}! What area or neighborhoods "
                        f"are you looking to buy in?"
                    )
                    background_tasks.add_task(
                        safe_send_message,
                        current_ghl_client,
                        contact_id,
                        t2_message,
                        event.message.type,
                    )
                    background_tasks.add_task(
                        safe_apply_actions,
                        current_ghl_client,
                        contact_id,
                        routing_actions,
                    )
                    await conversation_manager.update_context(
                        contact_id=contact_id,
                        user_message=user_message,
                        ai_response=t2_message,
                        location_id=location_id,
                    )
                    return JSONResponse(
                        status_code=200,
                        content={"status": "ok", "mode": "lead_t2_routed_buyer"},
                    )
                # ── END BUY/SELL QUALIFYING LAYER ────────────────────────────────
                # Intent unclear — fall through to the full LangGraph lead bot

                # Initialize and run lead bot (real-time conversation handler)
                lead_bot = LeadBotWorkflow(ghl_client=current_ghl_client)
                lead_result = await lead_bot.real_time_converse(
                    contact_id=contact_id,
                    user_message=user_message,
                    conversation_history=conversation_history,
                )

                # Extract lead temperature from intent profile classification
                lead_temp = "cold"
                if lead_result.get("intent_profile"):
                    classification = lead_result["intent_profile"].frs.classification
                    if classification == "Hot Lead":
                        lead_temp = "hot"
                    elif classification == "Warm Lead":
                        lead_temp = "warm"

                # Apply lead bot actions (tags based on temperature)
                actions = []
                temp_tag_map = {"hot": "Hot-Lead", "warm": "Warm-Lead", "cold": "Cold-Lead"}
                if lead_temp in temp_tag_map:
                    actions.append(GHLAction(type=ActionType.ADD_TAG, tag=temp_tag_map[lead_temp]))
                    # Remove stale temperature tags to prevent accumulation (e.g. cold+warm)
                    for temp_level, tag in temp_tag_map.items():
                        if temp_level != lead_temp:
                            actions.append(GHLAction(type=ActionType.REMOVE_TAG, tag=tag))

                is_qualified = lead_result.get("engagement_status") == "qualified"
                if is_qualified:
                    actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Lead-Qualified"))

                # --- LEAD CUSTOM FIELD SYNC ---
                # Write lead score so Jorge can filter/sort contacts in GHL
                if settings.custom_field_lead_score:
                    _lead_score_val = lead_result.get("lead_score", 0)
                    actions.append(GHLAction(type=ActionType.UPDATE_CUSTOM_FIELD, field=settings.custom_field_lead_score, value=_lead_score_val))
                # Write nurture sequence day so Jorge can see where in follow-up each lead is
                _seq_day_field = os.getenv("CUSTOM_FIELD_LEAD_SEQUENCE_DAY")
                if _seq_day_field:
                    actions.append(GHLAction(type=ActionType.UPDATE_CUSTOM_FIELD, field=_seq_day_field, value=str(sequence_day)))

                # Check for Jorge handoff signals
                handoff_triggered = False
                handoff_signals = lead_result.get("jorge_handoff_recommended") or lead_result.get(
                    "jorge_handoff_eligible"
                )

                # Track lead analytics
                background_tasks.add_task(
                    analytics_service.track_event,
                    event_type="jorge_lead_interaction",
                    location_id=location_id,
                    contact_id=contact_id,
                    data={
                        "lead_temperature": lead_temp,
                        "is_qualified": is_qualified,
                        "handoff_signals": handoff_signals,
                        "message_length": len(lead_result.get("response_content", "")),
                    },
                )

                # Run through response pipeline (AI disclosure + SMS truncation + spam guard)
                final_lead_msg = lead_result.get(
                    "response_content", "Thanks for reaching out! How can I help you today?"
                )
                pipeline_context = ProcessingContext(
                    contact_id=contact_id,
                    bot_mode="lead",
                    channel="sms",
                    user_message=user_message,
                    is_first_message=is_lead_first_message,
                )
                pipeline = get_response_pipeline()
                processed = await pipeline.process(final_lead_msg, pipeline_context)
                final_lead_msg = processed.message

                # --- BULLETPROOF COMPLIANCE INTERCEPTOR ---
                status, reason, violations = await compliance_guard.audit_message(
                    final_lead_msg, contact_context={"contact_id": contact_id, "mode": "lead"}
                )

                if status == ComplianceStatus.BLOCKED:
                    logger.warning(
                        f"Compliance BLOCKED lead message for {contact_id}: {reason}. Violations: {violations}"
                    )
                    final_lead_msg = "Thanks for reaching out! How can I help you today?"
                    actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Compliance-Alert"))


                # --- CROSS-BOT HANDOFF CHECK ---
                if handoff_signals:
                    actual_intent_signals = JorgeHandoffService.extract_intent_signals(user_message)
                    handoff = await handoff_service.evaluate_handoff_from_profile(
                        current_bot="lead",
                        contact_id=contact_id,
                        conversation_history=conversation_history,
                        intent_profile=_signals_to_handoff_profile(contact_id, actual_intent_signals),
                    )
                    if handoff:
                        handoff_actions = await handoff_service.execute_handoff(
                            handoff, contact_id, location_id=location_id
                        )
                        for ha in handoff_actions:
                            if ha["type"] == "add_tag":
                                actions.append(GHLAction(type=ActionType.ADD_TAG, tag=ha["tag"]))
                            elif ha["type"] == "remove_tag":
                                actions.append(GHLAction(type=ActionType.REMOVE_TAG, tag=ha["tag"]))
                        handoff_triggered = True

                logger.info(
                    f"Jorge lead processing completed for {contact_id}",
                    extra={
                        "contact_id": contact_id,
                        "lead_temperature": lead_temp,
                        "is_qualified": is_qualified,
                        "handoff_triggered": handoff_triggered,
                        "actions_count": len(actions),
                        "compliance_status": status.value,
                        "message_length": len(final_lead_msg),
                    },
                )

                # Persist conversation history so next turn has bot reply context
                await conversation_manager.update_context(
                    contact_id=contact_id,
                    user_message=user_message,
                    ai_response=final_lead_msg,
                    location_id=location_id,
                )

                # Send the lead response via GHL API (background task)
                background_tasks.add_task(
                    safe_send_message,
                    current_ghl_client,
                    contact_id,
                    final_lead_msg,
                    event.message.type,
                )

                # Apply tags and actions via GHL API (background task)
                if actions:
                    background_tasks.add_task(
                        safe_apply_actions,
                        current_ghl_client,
                        contact_id,
                        actions,
                    )

                # Track billing and pricing (Jorge's revenue foundation)
                background_tasks.add_task(
                    _calculate_lead_pricing,
                    contact_id,
                    location_id,
                    context,
                    pricing_optimizer,
                    analytics_service,
                )
                lead_score = lead_result.get("lead_score", 1 if lead_temp in ("hot", "warm") else 0)
                background_tasks.add_task(
                    _handle_billing_usage,
                    contact_id,
                    location_id,
                    lead_score,
                    lead_result.get("extracted_data", {}),
                    lead_temp,
                    subscription_manager,
                    pricing_optimizer,
                    analytics_service,
                )

                return GHLWebhookResponse(
                    success=True,
                    message=final_lead_msg,
                    actions=actions,
                )

            except Exception as e:
                logger.error(f"Jorge lead mode processing failed for contact {contact_id}: {str(e)}", exc_info=True)

                fallback_msg = "Thanks for reaching out! How can I help you today?"

                # Tag contact with Bot-Fallback-Active for monitoring
                try:
                    background_tasks.add_task(ghl_client_default.add_tags, contact_id, ["Bot-Fallback-Active"])
                    # Also send the fallback message via API for reliability
                    background_tasks.add_task(
                        safe_send_message,
                        ghl_client_default,
                        contact_id,
                        fallback_msg,
                        event.message.type,
                    )
                except Exception as tag_error:
                    logger.error(f"Failed to add Bot-Fallback-Active actions: {tag_error}")

                return GHLWebhookResponse(
                    success=True,
                    message=fallback_msg,
                    actions=[GHLAction(type=ActionType.ADD_TAG, tag="Bot-Fallback-Active")],
                )

    # Raw fallback — no bot mode matched
    logger.info(f"No bot mode matched for contact {contact_id}")
    return GHLWebhookResponse(
        success=True,
        message="Thanks for reaching out! How can I help you today?",
        actions=[],
    )


async def prepare_ghl_actions(
    extracted_data: dict,
    lead_score: int,
    event: GHLWebhookEvent,
    source_attribution=None,
    lead_scorer: LeadScorer = Depends(_get_lead_scorer),
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
    percentage_score = lead_scorer.get_percentage_score(lead_score)

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
    classification = lead_scorer.classify(lead_score)

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
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag=f"Location-{loc}"))
        else:
            location_str = str(location)
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag=f"Location-{location}"))

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
                LeadSource.DIRECT,
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
            "source": source_attribution.source.value if source_attribution else "unknown",
        },
    )

    return actions


class InitiateQualificationRequest(BaseModel):
    contact_id: str
    location_id: str


@router.post("/initiate-qualification")
@verify_webhook("ghl")
async def initiate_qualification(
    request: Request,
    body: InitiateQualificationRequest,
    background_tasks: BackgroundTasks,
    ghl_client_default: GHLClient = Depends(_get_ghl_client_default),
):
    """
    Called by GHL workflow when 'Needs Qualifying' tag is applied.
    Sends initial outreach message to start qualification.
    """
    contact_id = body.contact_id
    location_id = body.location_id
    try:
        contact_raw = await ghl_client_default.get_contact(contact_id)
        contact = (contact_raw or {}).get("contact", contact_raw or {})
        first_name = contact.get("firstName", "there")
        tags = contact.get("tags", [])

        if "Buyer-Lead" in tags:
            opening = f"{first_name}, glad you reached out! Still searching for a home in Rancho Cucamonga?"
        elif "Seller-Lead" in tags or "Needs Qualifying" in tags:
            opening = f"{first_name}, thanks for connecting. Still thinking about selling your property?"
        else:
            opening = f"{first_name}, thanks for reaching out! Are you looking to buy or sell in Rancho Cucamonga?"

        # Send the opening message via GHL
        background_tasks.add_task(
            ghl_client_default.send_message,
            contact_id=contact_id,
            message=opening,
            channel=MessageType.SMS,
        )

        logger.info(
            f"Initiate qualification sent for contact {contact_id}",
            extra={"contact_id": contact_id, "location_id": location_id},
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
            detail={"success": False, "message": "Failed to initiate qualification"},
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


async def _calculate_lead_pricing(
    contact_id: str,
    location_id: str,
    context: dict,
    pricing_optimizer: DynamicPricingOptimizer,
    analytics_service: AnalyticsService,
) -> None:
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
            contact_id=contact_id, location_id=location_id, context=context
        )

        logger.info(
            f"Pricing calculated for contact {contact_id}",
            extra={
                "contact_id": contact_id,
                "location_id": location_id,
                "tier": pricing_result.tier,
                "final_price": pricing_result.final_price,
                "expected_roi": pricing_result.expected_roi,
            },
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
                "agent_recommendation": pricing_result.agent_recommendation,
            },
        )

    except Exception as e:
        logger.error(
            f"Failed to calculate pricing for contact {contact_id}",
            extra={"contact_id": contact_id, "location_id": location_id, "error": str(e)},
            exc_info=True,
        )


async def _handle_billing_usage(
    contact_id: str,
    location_id: str,
    lead_score: int,
    extracted_data: dict,
    classification: str,
    subscription_manager: SubscriptionManager,
    pricing_optimizer: DynamicPricingOptimizer,
    analytics_service: AnalyticsService,
) -> None:
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
                    "billing_status": "no_subscription",
                },
            )
            return

        # Calculate lead price using dynamic pricing
        pricing_result = await pricing_optimizer.calculate_lead_price(
            contact_id=contact_id,
            location_id=location_id,
            context={
                "questions_answered": lead_score,
                "extracted_data": extracted_data,
                "classification": classification,
            },
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
                    billing_period_end=active_subscription.current_period_end,
                )

                # Record overage usage with subscription manager
                billing_result = await subscription_manager.bill_usage_overage(
                    subscription_id=active_subscription.id,
                    lead_id=usage_request.lead_id,
                    contact_id=contact_id,
                    lead_price=pricing_result.final_price,
                    tier=classification,
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
                            "jorge_feature": "usage_based_billing",
                        },
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
                            "arr_impact": float(pricing_result.final_price) * 12,  # Annualized impact
                        },
                    )

                else:
                    logger.error(
                        f"Failed to bill overage usage for contact {contact_id}",
                        extra={
                            "contact_id": contact_id,
                            "location_id": location_id,
                            "subscription_id": active_subscription.id,
                            "error": billing_result.get("error"),
                            "recoverable": billing_result.get("recoverable", True),
                        },
                    )

            except Exception as overage_error:
                logger.error(
                    f"Error processing usage overage billing for contact {contact_id}: {overage_error}",
                    extra={
                        "contact_id": contact_id,
                        "location_id": location_id,
                        "subscription_id": active_subscription.id,
                        "error": str(overage_error),
                        "error_type": type(overage_error).__name__,
                    },
                    exc_info=True,
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
                    "billing_status": "within_allowance",
                },
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
                    "estimated_value": float(pricing_result.final_price),
                },
            )

        # Check for usage threshold notifications
        threshold_result = await subscription_manager.handle_usage_threshold(
            location_id=location_id,
            current_usage=current_usage,
            period_usage_allowance=active_subscription.usage_allowance,
        )

        if threshold_result.get("actions_taken"):
            logger.info(
                f"Usage threshold actions triggered for location {location_id}",
                extra={
                    "location_id": location_id,
                    "usage_percentage": threshold_result.get("usage_percentage"),
                    "threshold_level": threshold_result.get("threshold_level"),
                    "actions_taken": threshold_result.get("actions_taken"),
                    "overage_billing_active": threshold_result.get("overage_billing_active"),
                },
            )

            # Track threshold events for customer success
            await analytics_service.track_event(
                event_type="usage_threshold_reached",
                location_id=location_id,
                contact_id=contact_id,
                data=threshold_result,
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
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
