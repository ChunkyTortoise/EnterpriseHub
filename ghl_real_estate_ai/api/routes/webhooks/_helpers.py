"""Shared helpers for GHL webhook route handlers.

Extracted from webhook.py to support decomposition into domain-specific
route modules. Contains:
- Dependency injection factories (lru_cache singletons)
- Safe message/action wrappers
- Tag normalization and mode flag computation
- Intent detection (buy/sell, negative sentiment, rejected offers)
- Slot selection for calendar booking
"""

import re
from functools import lru_cache
from typing import Any, Optional

from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.attribution_analytics import AttributionAnalytics
from ghl_real_estate_ai.services.calendar_scheduler import CalendarScheduler
from ghl_real_estate_ai.services.dynamic_pricing_optimizer import DynamicPricingOptimizer
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.hitl_gate import HITLGate
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.services.lead_source_tracker import LeadSourceTracker
from ghl_real_estate_ai.services.mls_client import MLSClient
from ghl_real_estate_ai.services.subscription_manager import SubscriptionManager
from ghl_real_estate_ai.services.tenant_service import TenantService

logger = get_logger(__name__)

SMS_MAX_CHARS = 320

LLM_FALLBACK_MSG = (
    "I'm having a brief connection issue — I'll follow up with you shortly. You can also reach Jorge directly."
)


# ── Dependency injection factories ──────────────────────────────────────


@lru_cache(maxsize=1)
def get_conversation_manager() -> ConversationManager:
    return ConversationManager()


@lru_cache(maxsize=1)
def get_ghl_client_default() -> GHLClient:
    return GHLClient()


@lru_cache(maxsize=1)
def get_lead_scorer() -> LeadScorer:
    return LeadScorer()


@lru_cache(maxsize=1)
def get_tenant_service() -> TenantService:
    return TenantService()


@lru_cache(maxsize=1)
def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


@lru_cache(maxsize=1)
def get_pricing_optimizer() -> DynamicPricingOptimizer:
    return DynamicPricingOptimizer()


@lru_cache(maxsize=1)
def get_calendar_scheduler() -> CalendarScheduler:
    return CalendarScheduler()


@lru_cache(maxsize=1)
def get_lead_source_tracker() -> LeadSourceTracker:
    return LeadSourceTracker()


@lru_cache(maxsize=1)
def get_attribution_analytics() -> AttributionAnalytics:
    return AttributionAnalytics()


@lru_cache(maxsize=1)
def get_subscription_manager() -> SubscriptionManager:
    return SubscriptionManager()


@lru_cache(maxsize=1)
def get_handoff_service() -> JorgeHandoffService:
    return JorgeHandoffService(analytics_service=get_analytics_service())


@lru_cache(maxsize=1)
def get_hitl_gate() -> HITLGate:
    return HITLGate()


@lru_cache(maxsize=1)
def get_mls_client() -> MLSClient:
    return MLSClient()


# ── Safe wrappers ───────────────────────────────────────────────────────


async def safe_send_message(ghl_client: GHLClient, contact_id: str, message: str, channel: Any = None) -> None:
    """Send a message via GHL, logging errors instead of raising."""
    try:
        await ghl_client.send_message(contact_id, message, channel=channel)
    except Exception as e:
        logger.error(f"Message delivery failed for contact {contact_id}: {e}")


async def safe_apply_actions(ghl_client: GHLClient, contact_id: str, actions: list) -> None:
    """Apply GHL actions (tags, fields), logging errors instead of raising."""
    try:
        for action in actions:
            if hasattr(action, "type"):
                await ghl_client.apply_action(contact_id, action)
    except Exception as e:
        logger.error(f"Action application failed for contact {contact_id}: {e}")


async def get_tenant_ghl_client(
    location_id: str, tenant_service: TenantService, ghl_client_default: GHLClient
) -> GHLClient:
    """Get a tenant-specific GHL client, falling back to the default."""
    tenant_config = await tenant_service.get_tenant_config(location_id)
    if tenant_config and tenant_config.get("ghl_api_key"):
        return GHLClient(api_key=tenant_config["ghl_api_key"], location_id=location_id)
    return ghl_client_default


# ── Tag normalization + mode flags ──────────────────────────────────────

# Tags that bots apply — contacts with ONLY these should still activate
_LEAD_PASSTHROUGH_TAGS: frozenset[str] = frozenset({"hot-lead", "warm-lead", "cold-lead", "lead-qualified"})
_SELLER_PASSTHROUGH_TAGS: frozenset[str] = frozenset({"hot-seller", "warm-seller", "cold-seller", "seller-qualified"})


def normalize_tags(raw_tags: list[str] | None) -> set[str]:
    """Normalize tags for case-insensitive matching with whitespace safety."""
    normalized: set[str] = set()
    for tag in raw_tags or []:
        if tag is None:
            continue
        value = str(tag).strip().lower()
        if value:
            normalized.add(value)
    return normalized


def tag_present(tag: str | None, tags_lower: set[str]) -> bool:
    """Return True when a single tag exists in normalized tag set."""
    if not tag:
        return False
    return tag.strip().lower() in tags_lower


def compute_mode_flags(
    tags_lower: set[str],
    *,
    should_deactivate: bool,
    seller_mode_enabled: bool,
    buyer_mode_enabled: bool,
    lead_mode_enabled: bool,
    buyer_activation_tag: str,
    lead_activation_tag: str,
) -> dict[str, bool]:
    """Compute bot mode flags. Mutually exclusive: seller > buyer > lead."""
    buyer_tag_present = tag_present(buyer_activation_tag, tags_lower)
    seller_active = (
        ("needs qualifying" in tags_lower or "seller-lead" in tags_lower)
        and seller_mode_enabled
        and not should_deactivate
        and not buyer_tag_present
    )
    buyer_active = buyer_tag_present and buyer_mode_enabled and not should_deactivate
    lead_active = (
        (
            (tag_present(lead_activation_tag, tags_lower) and not seller_active and not buyer_active)
            or (not tags_lower and lead_mode_enabled)
            or (lead_mode_enabled and bool(tags_lower) and tags_lower.issubset(_LEAD_PASSTHROUGH_TAGS))
        )
        and lead_mode_enabled
        and not should_deactivate
    )
    return {"seller": seller_active, "buyer": buyer_active, "lead": lead_active}


def select_primary_mode(mode_flags: dict[str, bool]) -> Optional[str]:
    """Deterministic mode priority: seller > buyer > lead."""
    if mode_flags.get("seller"):
        return "seller"
    if mode_flags.get("buyer"):
        return "buyer"
    if mode_flags.get("lead"):
        return "lead"
    return None


# ── Intent detection ────────────────────────────────────────────────────

_SELLER_SIGNALS = frozenset(
    {
        "sell",
        "selling",
        "list",
        "listing",
        "want to sell",
        "looking to sell",
        "thinking about selling",
        "put it on the market",
        "on the market",
        "my home",
        "my house",
        "my property",
        "my condo",
        "my place",
    }
)

_BUYER_SIGNALS = frozenset(
    {
        "buy",
        "buying",
        "purchase",
        "purchasing",
        "looking for",
        "find a home",
        "looking to buy",
        "want to buy",
        "interested in buying",
        "find a house",
        "searching for",
        "need a home",
        "need a house",
        "want a home",
        "want a house",
        "first home",
        "first house",
        "investment property",
        "rental property",
    }
)

_NEGATIVE_KEYWORDS = frozenset(
    {
        "angry",
        "frustrated",
        "disappointed",
        "furious",
        "upset",
        "scam",
        "rip off",
        "waste of time",
        "terrible",
        "awful",
        "horrible",
        "ridiculous",
        "unacceptable",
        "this is bs",
        "this is b.s",
        "forget it",
        "never mind",
        "stop contacting",
    }
)

_REJECTED_OFFER_KEYWORDS = frozenset(
    {
        "rejected",
        "won't accept",
        "not accepting",
        "turned down",
        "declined the offer",
        "offer was rejected",
        "offer rejected",
        "no deal",
        "not interested in the offer",
        "below asking",
        "too low",
        "lowball",
        "insulting offer",
    }
)


def detect_buy_sell_intent(message: str) -> Optional[str]:
    """Detect buyer or seller intent from message text."""
    msg = message.lower()
    seller_score = sum(1 for s in _SELLER_SIGNALS if s in msg)
    buyer_score = sum(1 for s in _BUYER_SIGNALS if s in msg)
    if seller_score > buyer_score:
        return "seller"
    if buyer_score > seller_score:
        return "buyer"
    return None


def detect_negative_sentiment(message: str) -> bool:
    """Lightweight negative-sentiment detection for CC workflow routing."""
    return any(kw in message.lower() for kw in _NEGATIVE_KEYWORDS)


def detect_rejected_offer(message: str) -> bool:
    """Detect rejected offer signals for CC workflow routing."""
    return any(kw in message.lower() for kw in _REJECTED_OFFER_KEYWORDS)


# ── Calendar slot helpers ───────────────────────────────────────────────


def format_slot_options(options: list[dict]) -> str:
    """Format calendar slot options for SMS display."""
    lines = [f"{opt['label']}) {opt['display']}" for opt in options]
    return "Reply with 1, 2, or 3.\n" + "\n".join(lines)


def select_slot_from_message(message: str, options: list[dict]) -> Optional[dict]:
    """Select a calendar slot from user message (digit or text match)."""
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
