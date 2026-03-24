"""Shared helpers for GHL webhook route handlers.

Extracted from webhook.py to support decomposition into domain-specific
route modules. Contains:
- Dependency injection factories (lru_cache singletons)
- Safe message/action wrappers
- Intent detection utilities
- Mode flag computation
"""

from functools import lru_cache
from typing import Any

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
    "I'm having a brief connection issue — I'll follow up with you shortly. "
    "You can also reach Jorge directly."
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


async def safe_send_message(
    ghl_client: GHLClient, contact_id: str, message: str, channel: Any = None
) -> None:
    """Send a message via GHL, logging errors instead of raising."""
    try:
        await ghl_client.send_message(contact_id, message, channel=channel)
    except Exception as e:
        logger.error(f"Message delivery failed for contact {contact_id}: {e}")


async def safe_apply_actions(
    ghl_client: GHLClient, contact_id: str, actions: list
) -> None:
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
