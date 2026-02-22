"""
Base workflow class for all Jorge bots.

This module provides a shared base class that deduplicates common service
initialization and monitoring patterns across Lead, Buyer, and Seller bots.

Create BaseBotWorkflow shared base class (Enhanced)
- Reduces 50+ duplicate service initializations across 3 bots
- Provides consistent monitoring, metrics, and event publishing
- Enables easier testing and maintenance
- NEW: Includes monitoring services (PerformanceTracker, BotMetricsCollector, AlertingService, ABTestingService)
- NEW: Includes A/B testing initialization
"""

import logging
from typing import TYPE_CHECKING, Optional

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
    - Performance tracking (PerformanceTracker, BotMetricsCollector)
    - Alerting and monitoring (AlertingService)
    - A/B testing infrastructure (ABTestingService)

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
            enable_ml_analytics: Whether to enable ML analytics ML intelligence
        """
        from ghl_real_estate_ai.config.industry_config import IndustryConfig
        from ghl_real_estate_ai.services.event_publisher import get_event_publisher
        from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
        from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService
        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
        from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker

        # Core configuration
        self.tenant_id = tenant_id
        self.industry_config: IndustryConfig = industry_config or IndustryConfig.default_real_estate()

        # Shared services
        self.event_publisher = get_event_publisher()

        # Monitoring services (singletons — cheap to instantiate)
        self.performance_tracker = PerformanceTracker()
        self.metrics_collector = BotMetricsCollector()
        self.alerting_service = AlertingService()
        self.ab_testing = ABTestingService()

        # Initialize A/B experiments
        self._init_ab_experiments()

        # Optional ML analytics (ML analytics)
        self.ml_analytics = None
        if enable_ml_analytics:
            try:
                from ghl_real_estate_ai.services.ml_analytics_engine import get_ml_analytics_engine

                self.ml_analytics = get_ml_analytics_engine(tenant_id)
                logger.info(f"{self.__class__.__name__}: ML analytics enabled for {tenant_id}")
            except ImportError:
                logger.warning(f"{self.__class__.__name__}: ML analytics requested but dependencies not available")

        logger.info(f"{self.__class__.__name__}: Initialized with tenant_id={tenant_id}")

    def _init_ab_experiments(self) -> None:
        """
        Create default A/B experiments if not already registered.

        This method is shared across all bots and creates the standard
        response tone experiment with three variants: formal, casual, empathetic.

        Subclasses can override this method to add bot-specific experiments.
        """
        try:
            from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService

            self.ab_testing.create_experiment(
                ABTestingService.RESPONSE_TONE_EXPERIMENT,
                ["formal", "casual", "empathetic"],
            )
        except ValueError:
            # Experiment already exists (singleton service shared across bots)
            pass
        except Exception as e:
            logger.warning(f"Failed to initialize A/B experiments: {e}")

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
