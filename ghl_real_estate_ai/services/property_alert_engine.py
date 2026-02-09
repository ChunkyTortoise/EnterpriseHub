"""
Real-Time Property Alert Engine for Jorge's Real Estate AI Platform.

Central orchestrator for intelligent property alerts that:
- Manages alert subscriptions and preferences per lead
- Integrates with Enhanced Property Matcher for continuous scoring
- Handles intelligent de-duplication and batching
- Publishes alerts through existing WebSocket and notification infrastructure
- Tracks delivery and engagement metrics

Features:
- Background property scoring pipeline integration
- Multi-tenant alert preference management
- Smart de-duplication based on property similarity
- Rate limiting and alert fatigue prevention
- Real-time WebSocket delivery
- Comprehensive engagement analytics
"""

import asyncio
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.matching_models import MatchingContext, PropertyMatch
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.enhanced_property_matcher import EnhancedPropertyMatcher
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)


class AlertType(Enum):
    """Types of property alerts that can be generated."""

    NEW_MATCH = "new_match"
    PRICE_DROP = "price_drop"
    BACK_ON_MARKET = "back_on_market"
    MARKET_OPPORTUNITY = "market_opportunity"
    STATUS_CHANGE = "status_change"


class AlertPriority(Enum):
    """Priority levels for property alerts."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AlertPreferences:
    """Lead's property alert preferences and criteria."""

    lead_id: str
    tenant_id: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    min_bathrooms: Optional[float] = None
    max_bathrooms: Optional[float] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None
    preferred_neighborhoods: List[str] = None
    max_commute_minutes: Optional[int] = None
    work_location: Optional[str] = None
    school_districts: List[str] = None
    property_types: List[str] = None
    must_have_features: List[str] = None
    exclude_features: List[str] = None
    alert_threshold_score: float = 75.0
    max_alerts_per_day: int = 5
    alert_frequency: str = "immediate"
    active: bool = True

    def __post_init__(self):
        if self.preferred_neighborhoods is None:
            self.preferred_neighborhoods = []
        if self.school_districts is None:
            self.school_districts = []
        if self.property_types is None:
            self.property_types = []
        if self.must_have_features is None:
            self.must_have_features = []
        if self.exclude_features is None:
            self.exclude_features = []


@dataclass
class PropertyAlert:
    """Generated property alert ready for delivery."""

    id: str
    lead_id: str
    tenant_id: str
    property_id: str
    alert_type: AlertType
    alert_priority: AlertPriority
    alert_title: str
    alert_message: str
    alert_summary: str
    match_score: float
    match_reasoning: Dict[str, Any]
    property_data: Dict[str, Any]
    processing_time_ms: int
    created_at: datetime
    scheduled_for: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for JSON serialization."""
        return {
            **asdict(self),
            "alert_type": self.alert_type.value,
            "alert_priority": self.alert_priority.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
        }


class PropertyAlertEngine:
    """
    Central engine for real-time property alert generation and delivery.

    Coordinates between:
    - Property matching algorithms (EnhancedPropertyMatcher)
    - Alert preference management
    - De-duplication and rate limiting
    - WebSocket event publishing
    - Delivery tracking and analytics
    """

    def __init__(self):
        # Core services
        self.property_matcher = EnhancedPropertyMatcher(enable_ml=True)
        self.event_publisher = get_event_publisher()
        self.cache_service = get_cache_service()

        # Alert configuration
        self.dedup_threshold_hours = 24  # De-duplicate similar alerts within 24 hours
        self.similarity_threshold = 0.8  # 80% similarity to consider properties similar
        self.max_queue_size = 1000  # Maximum alerts in processing queue

        # Performance tracking
        self.metrics = {
            "alerts_generated": 0,
            "alerts_deduplicated": 0,
            "alerts_rate_limited": 0,
            "alerts_sent": 0,
            "processing_errors": 0,
            "average_processing_time_ms": 0.0,
        }

        # Alert queue for batching and scheduling
        self.alert_queue = asyncio.Queue()
        self.processing_queue_task = None

        logger.info("PropertyAlertEngine initialized successfully")

    async def start_processing_queue(self):
        """Start background task for processing alert queue."""
        if self.processing_queue_task is None:
            self.processing_queue_task = asyncio.create_task(self._process_alert_queue())
            logger.info("PropertyAlertEngine queue processing started")

    async def stop_processing_queue(self):
        """Stop background queue processing."""
        if self.processing_queue_task:
            self.processing_queue_task.cancel()
            self.processing_queue_task = None
            logger.info("PropertyAlertEngine queue processing stopped")

    async def evaluate_property_for_alerts(
        self, property_data: Dict[str, Any], alert_type: AlertType = AlertType.NEW_MATCH
    ) -> List[PropertyAlert]:
        """
        Evaluate a property against all active alert preferences.

        Args:
            property_data: Property information to evaluate
            alert_type: Type of alert being generated

        Returns:
            List of generated alerts ready for delivery
        """
        start_time = time.time()
        generated_alerts = []

        try:
            # Get all active alert preferences (would normally be from database)
            active_preferences = await self._get_active_alert_preferences()

            logger.info(
                f"Evaluating property {property_data.get('id')} against {len(active_preferences)} alert preferences"
            )

            for preferences in active_preferences:
                # Check rate limiting first
                if not await self._check_rate_limits(preferences.lead_id, preferences.tenant_id):
                    self.metrics["alerts_rate_limited"] += 1
                    continue

                # Generate matching context from preferences
                matching_context = self._preferences_to_matching_context(preferences)

                # Score property using enhanced matcher
                property_matches = self.property_matcher.find_enhanced_matches(
                    matching_context.to_dict(), min_score=preferences.alert_threshold_score / 100.0, limit=1
                )

                # Check if property meets threshold
                if property_matches and len(property_matches) > 0:
                    match = property_matches[0]

                    if match.overall_score * 100 >= preferences.alert_threshold_score:
                        # Check for duplicates
                        if not await self._is_duplicate_alert(preferences.lead_id, property_data["id"], alert_type):
                            # Generate alert
                            alert = await self._create_property_alert(
                                preferences=preferences, property_data=property_data, match=match, alert_type=alert_type
                            )

                            generated_alerts.append(alert)
                            self.metrics["alerts_generated"] += 1
                        else:
                            self.metrics["alerts_deduplicated"] += 1
                            logger.debug(
                                f"Duplicate alert detected for lead {preferences.lead_id}, property {property_data.get('id')}"
                            )

            # Add alerts to processing queue
            for alert in generated_alerts:
                await self._queue_alert_for_delivery(alert)

            processing_time = (time.time() - start_time) * 1000
            self.metrics["average_processing_time_ms"] = (
                self.metrics["average_processing_time_ms"] * 0.9 + processing_time * 0.1
            )

            logger.info(
                f"Generated {len(generated_alerts)} alerts for property {property_data.get('id')} in {processing_time:.2f}ms"
            )
            return generated_alerts

        except Exception as e:
            logger.error(f"Error evaluating property for alerts: {e}", exc_info=True)
            self.metrics["processing_errors"] += 1
            return []

    async def create_alert_preferences(
        self, lead_id: str, tenant_id: str, preferences: Dict[str, Any]
    ) -> AlertPreferences:
        """
        Create or update alert preferences for a lead.

        Args:
            lead_id: Lead identifier
            tenant_id: Tenant identifier
            preferences: Alert preference configuration

        Returns:
            Created AlertPreferences object
        """
        alert_prefs = AlertPreferences(lead_id=lead_id, tenant_id=tenant_id, **preferences)

        # Cache preferences for quick access
        cache_key = f"alert_prefs:{tenant_id}:{lead_id}"
        await self.cache_service.set(cache_key, asdict(alert_prefs), ttl=600)  # 10 minute cache

        logger.info(f"Created alert preferences for lead {lead_id} in tenant {tenant_id}")
        return alert_prefs

    async def get_alert_preferences(self, lead_id: str, tenant_id: str) -> Optional[AlertPreferences]:
        """
        Get alert preferences for a lead.

        Args:
            lead_id: Lead identifier
            tenant_id: Tenant identifier

        Returns:
            AlertPreferences if found, None otherwise
        """
        cache_key = f"alert_prefs:{tenant_id}:{lead_id}"

        # Try cache first
        cached_prefs = await self.cache_service.get(cache_key)
        if cached_prefs:
            return AlertPreferences(**cached_prefs)

        # In production, this would query the database
        # For now, return None
        return None

    async def disable_alert_preferences(self, lead_id: str, tenant_id: str) -> bool:
        """
        Disable alert preferences for a lead.

        Args:
            lead_id: Lead identifier
            tenant_id: Tenant identifier

        Returns:
            True if successfully disabled
        """
        preferences = await self.get_alert_preferences(lead_id, tenant_id)
        if preferences:
            preferences.active = False

            cache_key = f"alert_prefs:{tenant_id}:{lead_id}"
            await self.cache_service.set(cache_key, asdict(preferences), ttl=600)

            logger.info(f"Disabled alert preferences for lead {lead_id} in tenant {tenant_id}")
            return True

        return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the alert engine."""
        queue_size = self.alert_queue.qsize() if self.alert_queue else 0

        return {
            **self.metrics,
            "queue_size": queue_size,
            "queue_processing_active": self.processing_queue_task is not None,
            "dedup_threshold_hours": self.dedup_threshold_hours,
            "similarity_threshold": self.similarity_threshold,
        }

    # Private helper methods

    async def _get_active_alert_preferences(self) -> List[AlertPreferences]:
        """Get all active alert preferences. In production, this queries the database."""
        # For now, return sample preferences for testing
        # In production: SELECT * FROM lead_alert_preferences WHERE active = true
        return [
            AlertPreferences(
                lead_id="sample_lead_1",
                tenant_id="tenant_1",
                min_price=300000,
                max_price=600000,
                min_bedrooms=2,
                max_bedrooms=4,
                preferred_neighborhoods=["Downtown", "Midtown"],
                alert_threshold_score=75.0,
                max_alerts_per_day=5,
            )
        ]

    async def _check_rate_limits(self, lead_id: str, tenant_id: str) -> bool:
        """Check if lead has exceeded daily alert limits."""
        cache_key = f"alert_count:{tenant_id}:{lead_id}:today"
        today_count = await self.cache_service.get(cache_key) or 0

        # Get preferences to check limit
        preferences = await self.get_alert_preferences(lead_id, tenant_id)
        max_daily = preferences.max_alerts_per_day if preferences else 5

        return today_count < max_daily

    def _preferences_to_matching_context(self, preferences: AlertPreferences) -> MatchingContext:
        """Convert AlertPreferences to MatchingContext for property matching."""
        context_dict = {
            "budget": {"min": preferences.min_price, "max": preferences.max_price},
            "bedrooms": preferences.min_bedrooms,
            "bathrooms": preferences.min_bathrooms,
            "location": preferences.preferred_neighborhoods[0] if preferences.preferred_neighborhoods else None,
            "property_type": preferences.property_types[0] if preferences.property_types else None,
            "min_sqft": preferences.min_sqft,
            "max_sqft": preferences.max_sqft,
        }

        return MatchingContext(**{k: v for k, v in context_dict.items() if v is not None})

    async def _is_duplicate_alert(self, lead_id: str, property_id: str, alert_type: AlertType) -> bool:
        """Check if similar alert was recently sent to avoid spam."""
        cache_key = f"alert_history:{lead_id}:{property_id}:{alert_type.value}"
        recent_alert = await self.cache_service.get(cache_key)

        return recent_alert is not None

    async def _create_property_alert(
        self, preferences: AlertPreferences, property_data: Dict[str, Any], match: PropertyMatch, alert_type: AlertType
    ) -> PropertyAlert:
        """Create a PropertyAlert from matching results."""

        # Determine priority based on match score
        if match.overall_score >= 0.95:
            priority = AlertPriority.URGENT
        elif match.overall_score >= 0.85:
            priority = AlertPriority.HIGH
        elif match.overall_score >= 0.75:
            priority = AlertPriority.NORMAL
        else:
            priority = AlertPriority.LOW

        # Generate alert content
        alert_title = self._generate_alert_title(property_data, match, alert_type)
        alert_message = self._generate_alert_message(property_data, match, alert_type)
        alert_summary = (
            f"New {property_data.get('property_type', 'property')} match: {match.overall_score:.0%} compatibility"
        )

        alert = PropertyAlert(
            id=f"alert_{int(time.time() * 1000)}_{preferences.lead_id}",
            lead_id=preferences.lead_id,
            tenant_id=preferences.tenant_id,
            property_id=property_data["id"],
            alert_type=alert_type,
            alert_priority=priority,
            alert_title=alert_title,
            alert_message=alert_message,
            alert_summary=alert_summary,
            match_score=match.overall_score * 100,
            match_reasoning=match.reasoning.to_dict() if hasattr(match, "reasoning") and match.reasoning else {},
            property_data=property_data,
            processing_time_ms=0,  # Will be updated
            created_at=datetime.now(timezone.utc),
        )

        return alert

    def _generate_alert_title(self, property_data: Dict[str, Any], match: PropertyMatch, alert_type: AlertType) -> str:
        """Generate human-readable alert title."""
        property_type = property_data.get("property_type", "Property")
        bedrooms = property_data.get("bedrooms", "N/A")
        price = property_data.get("price", 0)
        location = property_data.get("city", "Unknown")

        price_str = f"${price:,.0f}" if isinstance(price, (int, float)) else str(price)

        if alert_type == AlertType.NEW_MATCH:
            return f"Perfect Match: {bedrooms}BR {property_type} in {location} - {price_str}"
        elif alert_type == AlertType.PRICE_DROP:
            return f"Price Drop Alert: {property_type} in {location} now {price_str}"
        else:
            return f"Property Alert: {property_type} in {location} - {price_str}"

    def _generate_alert_message(
        self, property_data: Dict[str, Any], match: PropertyMatch, alert_type: AlertType
    ) -> str:
        """Generate detailed alert message."""
        score_pct = match.overall_score * 100

        message = f"🏠 **{score_pct:.0f}% Match Found!**\n\n"
        message += f"📍 **Location**: {property_data.get('address', 'Address not available')}\n"
        message += f"💰 **Price**: ${property_data.get('price', 0):,.0f}\n"
        message += f"🏡 **Details**: {property_data.get('bedrooms', 'N/A')} bed, {property_data.get('bathrooms', 'N/A')} bath\n"
        message += f"📐 **Size**: {property_data.get('sqft', 'N/A')} sq ft\n\n"

        if alert_type == AlertType.NEW_MATCH:
            message += "✨ This property matches your criteria perfectly! View details and schedule a showing today."
        elif alert_type == AlertType.PRICE_DROP:
            message += "📉 Great news! The price on this property just dropped and it still matches your preferences."

        return message

    async def _queue_alert_for_delivery(self, alert: PropertyAlert):
        """Add alert to delivery queue with scheduling logic."""
        preferences = await self.get_alert_preferences(alert.lead_id, alert.tenant_id)

        if preferences and preferences.alert_frequency == "immediate":
            alert.scheduled_for = datetime.now(timezone.utc)
        elif preferences and preferences.alert_frequency == "daily_digest":
            # Schedule for next day at 9 AM
            tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
            alert.scheduled_for = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            # Default to immediate
            alert.scheduled_for = datetime.now(timezone.utc)

        await self.alert_queue.put(alert)
        logger.debug(f"Queued alert {alert.id} for delivery at {alert.scheduled_for}")

    async def _process_alert_queue(self):
        """Background task to process queued alerts for delivery."""
        logger.info("Alert queue processing started")

        while True:
            try:
                # Get next alert from queue
                alert = await self.alert_queue.get()

                # Check if it's time to send
                if alert.scheduled_for and datetime.now(timezone.utc) < alert.scheduled_for:
                    # Put back in queue and wait
                    await self.alert_queue.put(alert)
                    await asyncio.sleep(60)  # Check again in 1 minute
                    continue

                # Send alert via WebSocket
                await self._deliver_alert_via_websocket(alert)

                # Update metrics
                self.metrics["alerts_sent"] += 1

                # Cache alert to prevent duplicates
                cache_key = f"alert_history:{alert.lead_id}:{alert.property_id}:{alert.alert_type.value}"
                await self.cache_service.set(cache_key, alert.id, ttl=self.dedup_threshold_hours * 3600)

                # Update daily count for rate limiting
                count_key = f"alert_count:{alert.tenant_id}:{alert.lead_id}:today"
                current_count = await self.cache_service.get(count_key) or 0
                await self.cache_service.set(count_key, current_count + 1, ttl=86400)  # 24 hours

                logger.info(f"Successfully delivered alert {alert.id} to lead {alert.lead_id}")

            except asyncio.CancelledError:
                logger.info("Alert queue processing cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing alert queue: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying

    async def _deliver_alert_via_websocket(self, alert: PropertyAlert):
        """Deliver alert through WebSocket system with Jorge-specific event structure."""
        # Use the Jorge-specific property alert publisher with frontend-expected structure
        await self.event_publisher.publish_property_alert(
            alert_id=alert.id,
            contact_id=alert.lead_id,  # Map lead_id → contact_id for frontend
            location_id=alert.tenant_id,
            property_id=alert.property_id,
            match_score=alert.match_score,
            alert_type=alert.alert_type.value,
            property_data={
                "address": alert.property_data.get("address", "Unknown Address"),
                "price": alert.property_data.get("price", 0),
                "beds": alert.property_data.get("bedrooms", 0),
                "baths": alert.property_data.get("bathrooms", 0),
                "sqft": alert.property_data.get("sqft", 0),
                "listing_date": alert.property_data.get("listing_date"),
                "match_reasons": alert.match_reasoning.get("primary_factors", []) if alert.match_reasoning else [],
            },
            match_reasoning=alert.match_reasoning,
        )

        logger.debug(f"Published Jorge property alert event for alert {alert.id} (contact: {alert.lead_id})")


# Global singleton instance
_property_alert_engine = None


def get_property_alert_engine() -> PropertyAlertEngine:
    """Get singleton PropertyAlertEngine instance."""
    global _property_alert_engine
    if _property_alert_engine is None:
        _property_alert_engine = PropertyAlertEngine()
    return _property_alert_engine


# Convenience functions for common operations
async def create_property_alert_preferences(
    lead_id: str, tenant_id: str, preferences: Dict[str, Any]
) -> AlertPreferences:
    """Convenience function to create alert preferences."""
    engine = get_property_alert_engine()
    return await engine.create_alert_preferences(lead_id, tenant_id, preferences)


async def evaluate_property_for_alerts(
    property_data: Dict[str, Any], alert_type: str = "new_match"
) -> List[PropertyAlert]:
    """Convenience function to evaluate property for alerts."""
    engine = get_property_alert_engine()
    alert_type_enum = AlertType(alert_type) if isinstance(alert_type, str) else alert_type
    return await engine.evaluate_property_for_alerts(property_data, alert_type_enum)


async def get_property_alert_metrics() -> Dict[str, Any]:
    """Convenience function to get alert engine metrics."""
    engine = get_property_alert_engine()
    return engine.get_metrics()
