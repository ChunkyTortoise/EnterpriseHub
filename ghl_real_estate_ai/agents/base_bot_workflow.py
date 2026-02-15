"""
Base workflow class for all Jorge bots.

This module provides a shared base class that deduplicates common service
initialization and monitoring patterns across Lead, Buyer, and Seller bots.

Task #18: Create BaseBotWorkflow shared base class
- Reduces 50+ duplicate service initializations across 3 bots
- Provides consistent monitoring, metrics, and event publishing
- Enables easier testing and maintenance
"""

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ghl_real_estate_ai.config.industry_config import IndustryConfig

logger = logging.getLogger(__name__)


class BaseBotWorkflow:
    """
    Shared base class for all Jorge bot workflows.

    Provides common functionality:
    - Industry configuration management
    - Event publishing
    - ML analytics engine (optional)
    - Performance tracking foundation
    - Metrics collection hooks

    Subclasses:
    - LeadBotWorkflow (lead_bot.py)
    - JorgeBuyerBot (jorge_buyer_bot.py)
    - JorgeSellerBot (jorge_seller_bot.py)
    """

    def __init__(
        self,
        tenant_id: str,
        industry_config: Optional["IndustryConfig"] = None,
        enable_ml_analytics: bool = False,
    ):
        """
        Initialize shared bot workflow components.

        Args:
            tenant_id: Unique identifier for this bot instance
            industry_config: Industry-specific configuration (defaults to real estate)
            enable_ml_analytics: Whether to enable Track 3.1 ML intelligence
        """
        from ghl_real_estate_ai.config.industry_config import IndustryConfig
        from ghl_real_estate_ai.services.event_publisher import get_event_publisher

        # Core configuration
        self.tenant_id = tenant_id
        self.industry_config: IndustryConfig = industry_config or IndustryConfig.default_real_estate()

        # Shared services
        self.event_publisher = get_event_publisher()

        # Optional ML analytics (Track 3.1)
        self.ml_analytics = None
        if enable_ml_analytics:
            try:
                from ghl_real_estate_ai.services.ml_analytics_engine import get_ml_analytics_engine
                self.ml_analytics = get_ml_analytics_engine(tenant_id)
                logger.info(f"{self.__class__.__name__}: ML analytics enabled for {tenant_id}")
            except ImportError:
                logger.warning(
                    f"{self.__class__.__name__}: ML analytics requested but dependencies not available"
                )

        logger.info(f"{self.__class__.__name__}: Initialized with tenant_id={tenant_id}")

    def publish_event(self, event_type: str, data: dict) -> None:
        """
        Publish an event to the event bus.

        Args:
            event_type: Type of event (e.g., "lead.qualified", "handoff.initiated")
            data: Event payload data
        """
        try:
            self.event_publisher.publish(
                event_type=event_type,
                data={**data, "tenant_id": self.tenant_id},
            )
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}", exc_info=True)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"tenant_id={self.tenant_id!r}, "
            f"ml_analytics={'enabled' if self.ml_analytics else 'disabled'}"
            f")"
        )
