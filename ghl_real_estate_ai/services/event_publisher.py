"""
Real-Time Event Publisher for Jorge's Real Estate AI Dashboard.

Publishes events when data changes occur to enable real-time dashboard updates.
Integrates with existing services to detect data changes and broadcast them
via the WebSocket system to connected clients.

Features:
- Automatic event detection from data service operations
- Intelligent event aggregation and batching
- Performance monitoring and metrics
- Integration with caching layer for efficiency
- Event filtering and role-based distribution
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.auth_service import UserRole
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.websocket_server import EventType, RealTimeEvent, get_websocket_manager

logger = get_logger(__name__)


@dataclass
class EventMetrics:
    """Event publishing metrics."""

    total_events_published: int = 0
    events_by_type: Dict[str, int] = None
    last_event_time: Optional[datetime] = None
    average_processing_time_ms: float = 0.0
    failed_publishes: int = 0

    def __post_init__(self):
        if self.events_by_type is None:
            self.events_by_type = {}


class EventPublisher:
    """
    Real-Time Event Publisher Service.

    Monitors data changes and publishes real-time events to connected
    WebSocket clients. Provides intelligent batching, filtering, and
    performance optimization.
    """

    def __init__(self):
        self.websocket_manager = get_websocket_manager()
        self.cache_service = get_cache_service()
        self.metrics = EventMetrics()

        # 🚀 ENHANCED EVENT BATCHING CONFIGURATION (Phase 8+ Optimization)
        self.batch_interval = 0.01  # 10ms micro-batching (vs 500ms previous)
        self.max_batch_size = 50  # Increased capacity for enterprise throughput
        self._event_batch = []
        self._batch_timer = None

        # 🎯 PRIORITY LANES FOR <10MS LATENCY TARGET
        self.critical_bypass = True  # Critical events skip batching entirely

        # 📊 ENHANCED PERFORMANCE TRACKING
        self._processing_times = []
        self._latency_measurements = []
        self._events_under_10ms = 0
        self._total_events_processed = 0

        logger.info("Event Publisher initialized")

    async def start(self):
        """Start the event publisher service."""
        await self.websocket_manager.start_services()
        logger.info("Event Publisher started")

    async def stop(self):
        """Stop the event publisher service."""
        if self._batch_timer:
            self._batch_timer.cancel()
        await self.websocket_manager.stop_services()
        logger.info("Event Publisher stopped")

    async def publish_lead_update(
        self,
        lead_id: str,
        lead_data: Dict[str, Any],
        action: str = "updated",
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish lead update event.

        Args:
            lead_id: Lead identifier
            lead_data: Lead data that was updated
            action: Type of action (created, updated, qualified, etc.)
            user_id: User who triggered the update (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.LEAD_UPDATE,
            data={
                "lead_id": lead_id,
                "action": action,
                "lead_data": lead_data,
                "updated_fields": list(lead_data.keys()),
                "summary": f"Lead {action}: {lead_data.get('name', 'Unknown')}",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if action in ["created", "qualified", "hot"] else "normal",
        )

        await self._publish_event(event)
        logger.info(f"Published lead update event: {lead_id} ({action})")

    async def publish_conversation_update(
        self,
        conversation_id: str,
        lead_id: str,
        stage: str,
        message: Optional[str] = None,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish conversation stage update event.

        Args:
            conversation_id: Conversation identifier
            lead_id: Associated lead ID
            stage: New conversation stage (Q1, Q2, Q3, Q4, etc.)
            message: Latest message content (optional)
            user_id: User associated with conversation (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.CONVERSATION_UPDATE,
            data={
                "conversation_id": conversation_id,
                "lead_id": lead_id,
                "stage": stage,
                "message_preview": message[:100] + "..." if message and len(message) > 100 else message,
                "stage_progression": self._get_stage_progression(stage),
                "summary": f"Conversation moved to {stage}",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if stage in ["Q4", "hot", "ready"] else "normal",
        )

        await self._publish_event(event)
        logger.info(f"Published conversation update: {conversation_id} -> {stage}")

    def _get_stage_progression(self, stage: str) -> Dict[str, Any]:
        """Get conversation stage progression information."""
        stage_map = {
            "Q1": {"progress": 25, "next": "Q2", "description": "Initial Qualification"},
            "Q2": {"progress": 50, "next": "Q3", "description": "Budgeting & Timeline"},
            "Q3": {"progress": 75, "next": "Q4", "description": "Property Search"},
            "Q4": {"progress": 90, "next": "closing", "description": "Ready to Sell"},
            "closing": {"progress": 100, "next": None, "description": "Deal Closing"},
        }

        return stage_map.get(stage, {"progress": 0, "next": None, "description": "Unknown"})

    async def publish_commission_update(
        self,
        deal_id: str,
        commission_amount: float,
        pipeline_status: str,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish commission pipeline update event.

        Args:
            deal_id: Deal identifier
            commission_amount: Commission amount
            pipeline_status: Pipeline status (potential, confirmed, paid)
            user_id: User associated with deal (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.COMMISSION_UPDATE,
            data={
                "deal_id": deal_id,
                "commission_amount": commission_amount,
                "pipeline_status": pipeline_status,
                "formatted_amount": f"${commission_amount:,.2f}",
                "impact": "positive" if commission_amount > 0 else "neutral",
                "summary": f"Commission {pipeline_status}: ${commission_amount:,.2f}",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if commission_amount > 10000 else "normal",
        )

        await self._publish_event(event)
        logger.info(f"Published commission update: {deal_id} - ${commission_amount:,.2f} ({pipeline_status})")

    async def publish_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "info",
        details: Optional[Dict[str, Any]] = None,
        target_roles: Optional[List[UserRole]] = None,
        **kwargs,
    ):
        """
        Publish system alert event.

        Args:
            alert_type: Type of alert (performance, error, maintenance, etc.)
            message: Alert message
            severity: Alert severity (info, warning, error, critical)
            details: Additional alert details (optional)
            target_roles: Specific roles to target (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.SYSTEM_ALERT,
            data={
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "details": details or {},
                "action_required": severity in ["error", "critical"],
                "summary": f"{severity.upper()}: {message}",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            priority="critical" if severity == "critical" else "high" if severity == "error" else "normal",
        )

        # Target specific roles if specified
        if target_roles:
            await self.websocket_manager.broadcast_event(event, target_roles=set(target_roles))
        else:
            await self._publish_event(event)

        logger.info(f"Published system alert: {alert_type} ({severity}) - {message}")

    async def publish_performance_update(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: str = "",
        comparison: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        **kwargs,
    ):
        """
        Publish performance metric update event.

        Args:
            metric_name: Name of the metric
            metric_value: Current metric value
            metric_unit: Unit of measurement (optional)
            comparison: Comparison data (previous value, trend, etc.) (optional)
            user_id: User associated with metric (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.PERFORMANCE_UPDATE,
            data={
                "metric_name": metric_name,
                "metric_value": metric_value,
                "metric_unit": metric_unit,
                "formatted_value": f"{metric_value:.2f}{metric_unit}",
                "comparison": comparison or {},
                "trend": self._calculate_trend(comparison) if comparison else "neutral",
                "summary": f"{metric_name}: {metric_value:.2f}{metric_unit}",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            priority="low",
        )

        await self._publish_event(event)
        logger.debug(f"Published performance update: {metric_name} = {metric_value}{metric_unit}")

    def _calculate_trend(self, comparison: Dict[str, Any]) -> str:
        """Calculate trend direction from comparison data."""
        if "previous_value" in comparison and "current_value" in comparison:
            prev = comparison["previous_value"]
            curr = comparison["current_value"]

            if curr > prev * 1.05:  # 5% increase threshold
                return "up"
            elif curr < prev * 0.95:  # 5% decrease threshold
                return "down"

        return "stable"

    async def publish_dashboard_refresh(
        self,
        component: str,
        data: Dict[str, Any],
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish dashboard component refresh event.

        Args:
            component: Dashboard component to refresh
            data: Updated component data
            user_id: User requesting refresh (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.DASHBOARD_REFRESH,
            data={
                "component": component,
                "data": data,
                "cache_key": f"dashboard:{component}:{location_id or 'global'}",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "summary": f"Dashboard component refreshed: {component}",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="normal",
        )

        await self._publish_event(event)
        logger.debug(f"Published dashboard refresh: {component}")

    async def publish_user_activity(
        self,
        action: str,
        user_id: int,
        details: Optional[Dict[str, Any]] = None,
        target_roles: Optional[List[UserRole]] = None,
        **kwargs,
    ):
        """
        Publish user activity event.

        Args:
            action: Activity action (login, logout, view_dashboard, etc.)
            user_id: User ID performing action
            details: Additional activity details (optional)
            target_roles: Specific roles to notify (optional, defaults to admin only)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.USER_ACTIVITY,
            data={
                "action": action,
                "user_id": user_id,
                "details": details or {},
                "session_info": await self._get_session_info(user_id),
                "summary": f"User activity: {action}",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            priority="low",
        )

        # Default to admin-only notifications for user activity
        target_roles = target_roles or [UserRole.ADMIN]
        await self.websocket_manager.broadcast_event(event, target_roles=set(target_roles))
        logger.debug(f"Published user activity: {action} (user {user_id})")

    async def _get_session_info(self, user_id: int) -> Dict[str, Any]:
        """Get session information for user activity events."""
        # This could be enhanced to include more session details
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "user_id": user_id}

    async def publish_property_alert(
        self,
        alert_id: str,
        lead_id: str,
        property_id: str,
        match_score: float,
        alert_type: str,
        property_data: Dict[str, Any],
        match_reasoning: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish property alert event for real-time property matching.

        Args:
            alert_id: Unique alert identifier
            lead_id: Lead who should receive the alert
            property_id: Property that matched
            match_score: Match score (0-100)
            alert_type: Type of alert (new_match, price_drop, market_opportunity)
            property_data: Property details for the alert
            match_reasoning: Detailed matching reasoning (optional)
            user_id: User associated with lead (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        # Extract key property details for quick access
        property_address = property_data.get("address", "Unknown Address")
        property_price = property_data.get("price", 0)
        property_bedrooms = property_data.get("bedrooms", 0)
        property_bathrooms = property_data.get("bathrooms", 0)
        property_sqft = property_data.get("sqft", 0)

        # Determine priority based on match score and alert type
        priority = "high" if match_score >= 85 or alert_type == "price_drop" else "normal"
        if alert_type in ["market_opportunity", "back_on_market"] and match_score >= 90:
            priority = "critical"

        event = RealTimeEvent(
            event_type=EventType.PROPERTY_ALERT,
            data={
                "alert_id": alert_id,
                "lead_id": lead_id,
                "property_id": property_id,
                "match_score": round(match_score, 2),
                "alert_type": alert_type,
                # Property summary for quick display
                "property_summary": {
                    "address": property_address,
                    "price": property_price,
                    "formatted_price": f"${property_price:,.0f}" if property_price else "Price on request",
                    "bedrooms": property_bedrooms,
                    "bathrooms": property_bathrooms,
                    "sqft": property_sqft,
                    "formatted_sqft": f"{property_sqft:,} sq ft" if property_sqft else "Size not listed",
                },
                # Full property data for detailed view
                "property_data": property_data,
                "match_reasoning": match_reasoning or {},
                # Alert metadata
                "alert_priority": priority,
                "requires_action": match_score >= 90,
                "expires_at": (datetime.now(timezone.utc).timestamp() + 86400),  # 24 hours from now
                # Human-readable summary
                "summary": f"New {alert_type.replace('_', ' ').title()}: {property_address} ({match_score:.0f}% match)",
                "notification_text": f"Found a {match_score:.0f}% match! {property_address} - ${property_price:,.0f}"
                if property_price
                else f"Found a {match_score:.0f}% match! {property_address}",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority=priority,
        )

        await self._publish_event(event)
        logger.info(
            f"Published property alert: {alert_type} for lead {lead_id} - {property_address} ({match_score:.1f}% match)"
        )

    # Jorge Bot Ecosystem Event Publishers

    async def publish_bot_status_update(
        self,
        bot_type: str,
        contact_id: str,
        status: str,
        current_step: Optional[str] = None,
        processing_time_ms: Optional[float] = None,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish bot status update event.

        Args:
            bot_type: Type of bot (jorge-seller, lead-bot, intent-decoder)
            contact_id: Contact/lead identifier
            status: Bot status (active, idle, processing, completed, error)
            current_step: Current processing step (optional)
            processing_time_ms: Processing time in milliseconds (optional)
            user_id: User associated with bot operation (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.BOT_STATUS_UPDATE,
            data={
                "bot_type": bot_type,
                "contact_id": contact_id,
                "status": status,
                "current_step": current_step,
                "processing_time_ms": processing_time_ms,
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "summary": f"{bot_type.replace('-', ' ').title()} bot {status}",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if status == "error" else "normal",
        )

        await self._publish_event(event)
        logger.info(f"Published bot status: {bot_type} - {status} (contact: {contact_id})")

    async def publish_jorge_qualification_progress(
        self,
        contact_id: str,
        current_question: int,
        questions_answered: int,
        seller_temperature: str,
        qualification_scores: Optional[Dict[str, float]] = None,
        next_action: Optional[str] = None,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish Jorge seller bot qualification progress event.

        Args:
            contact_id: Contact/lead identifier
            current_question: Current question number (1-4)
            questions_answered: Total questions answered so far
            seller_temperature: Seller temperature (hot, warm, cold)
            qualification_scores: FRS/PCS scores (optional)
            next_action: Next recommended action (optional)
            user_id: User associated with qualification (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        progress_percentage = min(100, (questions_answered / 4) * 100)

        event = RealTimeEvent(
            event_type=EventType.JORGE_QUALIFICATION_PROGRESS,
            data={
                "contact_id": contact_id,
                "current_question": current_question,
                "questions_answered": questions_answered,
                "total_questions": 4,  # Jorge's 4 core questions
                "progress_percentage": round(progress_percentage, 1),
                "seller_temperature": seller_temperature,
                "qualification_scores": qualification_scores or {},
                "next_action": next_action,
                "qualification_stage": f"Q{current_question}" if current_question <= 4 else "Complete",
                "summary": f"Jorge qualification {progress_percentage:.0f}% complete - {seller_temperature} seller",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if seller_temperature == "hot" else "normal",
        )

        await self._publish_event(event)
        logger.info(
            f"Published Jorge qualification progress: {progress_percentage:.0f}% ({seller_temperature} - contact: {contact_id})"
        )

    async def publish_lead_bot_sequence_update(
        self,
        contact_id: str,
        sequence_day: int,
        action_type: str,
        success: bool,
        next_action_date: Optional[str] = None,
        message_sent: Optional[str] = None,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish lead bot 3-7-30 sequence progress event.

        Args:
            contact_id: Contact/lead identifier
            sequence_day: Day in sequence (3, 7, 30)
            action_type: Type of action (analysis_started, message_sent, call_scheduled, etc.)
            success: Whether the action was successful
            next_action_date: Next scheduled action date (optional)
            message_sent: Message content preview (optional)
            user_id: User associated with sequence (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.LEAD_BOT_SEQUENCE_UPDATE,
            data={
                "contact_id": contact_id,
                "sequence_day": sequence_day,
                "action_type": action_type,
                "success": success,
                "next_action_date": next_action_date,
                "message_preview": message_sent[:100] + "..."
                if message_sent and len(message_sent) > 100
                else message_sent,
                "sequence_progress": self._calculate_sequence_progress(sequence_day),
                "summary": f"Day {sequence_day} sequence {action_type} - {'Success' if success else 'Failed'}",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if not success else "normal",
        )

        await self._publish_event(event)
        logger.info(
            f"Published lead bot sequence: Day {sequence_day} {action_type} ({'success' if success else 'failed'} - contact: {contact_id})"
        )

    async def publish_intent_analysis_complete(
        self,
        contact_id: str,
        processing_time_ms: float,
        confidence_score: float,
        intent_category: str,
        frs_score: Optional[float] = None,
        pcs_score: Optional[float] = None,
        recommendations: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish intent decoder analysis completion event.

        Args:
            contact_id: Contact/lead identifier
            processing_time_ms: Analysis processing time in milliseconds
            confidence_score: Analysis confidence score (0-1)
            intent_category: Categorized intent result
            frs_score: Financial Readiness Score (optional)
            pcs_score: Psychological Commitment Score (optional)
            recommendations: Analysis recommendations (optional)
            user_id: User associated with analysis (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.INTENT_ANALYSIS_COMPLETE,
            data={
                "contact_id": contact_id,
                "processing_time_ms": round(processing_time_ms, 2),
                "confidence_score": round(confidence_score, 3),
                "intent_category": intent_category,
                "frs_score": round(frs_score, 1) if frs_score else None,
                "pcs_score": round(pcs_score, 1) if pcs_score else None,
                "recommendations": recommendations or [],
                "performance_tier": "excellent"
                if processing_time_ms < 50
                else "good"
                if processing_time_ms < 100
                else "acceptable",
                "summary": f"Intent analysis complete - {intent_category} ({confidence_score:.1%} confidence)",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="normal",
        )

        await self._publish_event(event)
        logger.info(
            f"Published intent analysis: {intent_category} ({confidence_score:.1%} - {processing_time_ms:.1f}ms - contact: {contact_id})"
        )

    async def publish_bot_handoff_request(
        self,
        handoff_id: str,
        from_bot: str,
        to_bot: str,
        contact_id: str,
        handoff_reason: str = "qualification_ready",
        context_transfer: Dict[str, Any] = None,
        urgency: str = "normal",
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish bot handoff coordination event.

        Args:
            handoff_id: Unique handoff identifier
            from_bot: Source bot identifier
            to_bot: Target bot identifier
            contact_id: Contact/lead identifier
            handoff_reason: Reason for handoff
            context_transfer: Context data being transferred
            urgency: Handoff urgency (immediate, normal, low)
            user_id: User associated with handoff (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        if context_transfer is None:
            context_transfer = {}

        RealTimeEvent(
            event_type=EventType.BOT_HANDOFF_REQUEST,
            data={
                "handoff_id": handoff_id,
                "from_bot": from_bot,
                "to_bot": to_bot,
                "contact_id": contact_id,
                "handoff_reason": handoff_reason,
                "context_transfer": context_transfer,
                "urgency": urgency,
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if urgency == "immediate" else "normal",
        )

    async def publish_system_health_update(
        self,
        component: str,
        status: str,
        response_time_ms: float,
        error_message: Optional[str] = None,
        additional_metrics: Optional[Dict[str, Any]] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish system component health update event.

        Args:
            component: Component name (redis, ghl_api, claude_api, database, jorge_bots)
            status: Component status (healthy, degraded, down, recovering)
            response_time_ms: Component response time in milliseconds
            error_message: Error message if status is down/degraded (optional)
            additional_metrics: Additional component metrics (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.SYSTEM_HEALTH_UPDATE,
            data={
                "component": component,
                "status": status,
                "response_time_ms": round(response_time_ms, 2),
                "error_message": error_message,
                "health_score": self._calculate_health_score(status, response_time_ms),
                "metrics": additional_metrics or {},
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "summary": f"{component.replace('_', ' ').title()}: {status} ({response_time_ms:.0f}ms)",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            priority="critical" if status == "down" else "high" if status == "degraded" else "low",
        )

        await self._publish_event(event)
        logger.info(f"Published system health: {component} - {status} ({response_time_ms:.1f}ms)")

    # === BUYER BOT EVENT PUBLISHERS ===

    async def publish_buyer_intent_analysis(
        self,
        contact_id: str,
        buyer_temperature: str,
        financial_readiness: float,
        urgency_score: float,
        confidence_level: float,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """Publish buyer intent analysis results."""
        event = RealTimeEvent(
            event_type=EventType.BUYER_INTENT_ANALYSIS,
            data={
                "contact_id": contact_id,
                "buyer_temperature": buyer_temperature,
                "financial_readiness_score": financial_readiness,
                "urgency_score": urgency_score,
                "confidence_level": confidence_level,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if buyer_temperature in ["hot", "warm"] else "normal",
        )

        await self._publish_event(event)
        logger.info(f"Published buyer intent analysis: {buyer_temperature} (contact: {contact_id})")

    async def publish_buyer_qualification_progress(
        self,
        contact_id: str,
        current_step: str,
        financial_readiness_score: float,
        motivation_score: float,
        qualification_status: str,
        properties_matched: int = 0,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """Publish buyer qualification progress (mirrors jorge_qualification_progress)."""
        event = RealTimeEvent(
            event_type=EventType.BUYER_QUALIFICATION_PROGRESS,
            data={
                "contact_id": contact_id,
                "current_step": current_step,
                "financial_readiness_score": financial_readiness_score,
                "motivation_score": motivation_score,
                "qualification_status": qualification_status,
                "properties_matched": properties_matched,
                "overall_score": (financial_readiness_score + motivation_score) / 2,
                "progress_timestamp": datetime.now(timezone.utc).isoformat(),
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if qualification_status == "qualified" else "normal",
        )

        await self._publish_event(event)
        logger.info(
            f"Published buyer qualification progress: {qualification_status} ({current_step} - contact: {contact_id})"
        )

    async def publish_buyer_qualification_complete(
        self,
        contact_id: str,
        qualification_status: str,
        final_score: float,
        properties_matched: int,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """Publish buyer qualification completion."""
        event = RealTimeEvent(
            event_type=EventType.BUYER_QUALIFICATION_COMPLETE,
            data={
                "contact_id": contact_id,
                "qualification_status": qualification_status,
                "final_score": final_score,
                "properties_matched": properties_matched,
                "completion_timestamp": datetime.now(timezone.utc).isoformat(),
                "next_action": "property_search" if qualification_status == "qualified" else "nurture",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if qualification_status == "qualified" else "normal",
        )

        await self._publish_event(event)
        logger.info(
            f"Published buyer qualification complete: {qualification_status} (score: {final_score} - contact: {contact_id})"
        )

    async def publish_buyer_follow_up_scheduled(
        self,
        contact_id: str,
        action_type: str,
        scheduled_hours: int,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """Publish buyer follow-up scheduling."""
        event = RealTimeEvent(
            event_type=EventType.BUYER_FOLLOW_UP_SCHEDULED,
            data={
                "contact_id": contact_id,
                "action_type": action_type,
                "scheduled_hours": scheduled_hours,
                "scheduled_for": (datetime.now(timezone.utc) + timedelta(hours=scheduled_hours)).isoformat(),
                "schedule_timestamp": datetime.now(timezone.utc).isoformat(),
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="normal",
        )

        await self._publish_event(event)
        logger.info(f"Published buyer follow-up scheduled: {action_type} in {scheduled_hours}h (contact: {contact_id})")

    async def publish_property_match_update(
        self,
        contact_id: str,
        properties_matched: int,
        match_criteria: Dict[str, Any],
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """Publish property matching results."""
        event = RealTimeEvent(
            event_type=EventType.PROPERTY_MATCH_UPDATE,
            data={
                "contact_id": contact_id,
                "properties_matched": properties_matched,
                "match_criteria": match_criteria,
                "match_timestamp": datetime.now(timezone.utc).isoformat(),
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if properties_matched > 0 else "normal",
        )

        await self._publish_event(event)
        logger.info(f"Published property match update: {properties_matched} matches (contact: {contact_id})")

    # === SMS COMPLIANCE EVENT PUBLISHERS ===

    async def publish_sms_compliance_event(
        self,
        phone_number: str,
        event_type: str,
        reason: str,
        additional_data: Optional[Dict] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """Publish SMS compliance events for audit trail."""
        event = RealTimeEvent(
            event_type=EventType.SMS_COMPLIANCE,
            data={
                "phone_number_suffix": phone_number[-4:] if phone_number else "****",  # Only last 4 digits for privacy
                "compliance_event_type": event_type,
                "reason": reason,
                "additional_data": additional_data or {},
                "compliance_timestamp": datetime.now(timezone.utc).isoformat(),
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            priority="critical",  # Compliance events are always critical
        )

        await self._publish_event(event)
        logger.info(
            f"Published SMS compliance event: {event_type} - {reason} (phone: ***{phone_number[-4:] if phone_number else '****'})"
        )

    async def publish_sms_opt_out_processed(
        self,
        phone_number: str,
        opt_out_method: str,
        message_content: Optional[str] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """Publish SMS opt-out processing confirmation."""
        event = RealTimeEvent(
            event_type=EventType.SMS_OPT_OUT_PROCESSED,
            data={
                "phone_number_suffix": phone_number[-4:] if phone_number else "****",
                "opt_out_method": opt_out_method,
                "message_content": message_content[:100] + "..."
                if message_content and len(message_content) > 100
                else message_content,
                "processed_timestamp": datetime.now(timezone.utc).isoformat(),
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            priority="high",
        )

        await self._publish_event(event)
        logger.info(
            f"Published SMS opt-out processed: {opt_out_method} (phone: ***{phone_number[-4:] if phone_number else '****'})"
        )

    async def publish_sms_frequency_limit_hit(
        self,
        phone_number: str,
        limit_type: str,
        current_count: int,
        limit_value: int,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """Publish SMS frequency limit violations."""
        event = RealTimeEvent(
            event_type=EventType.SMS_FREQUENCY_LIMIT_HIT,
            data={
                "phone_number_suffix": phone_number[-4:] if phone_number else "****",
                "limit_type": limit_type,
                "current_count": current_count,
                "limit_value": limit_value,
                "limit_hit_timestamp": datetime.now(timezone.utc).isoformat(),
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            priority="high",
        )

        await self._publish_event(event)
        logger.info(
            f"Published SMS frequency limit hit: {limit_type} {current_count}/{limit_value} (phone: ***{phone_number[-4:] if phone_number else '****'})"
        )

    # === AI CONCIERGE EVENT PUBLISHERS ===

    async def publish_proactive_insight(
        self,
        insight_id: str,
        contact_id: str,
        insight_type: str,
        confidence_score: float,
        title: str,
        description: str,
        suggested_actions: List[str],
        priority_level: str = "normal",
        context_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish proactive conversation insight event.

        Args:
            insight_id: Unique insight identifier
            contact_id: Contact/lead identifier
            insight_type: Type of insight (opportunity, risk, coaching, strategy)
            confidence_score: AI confidence in the insight (0-1)
            title: Brief insight title
            description: Detailed insight description
            suggested_actions: List of suggested actions
            priority_level: Insight priority (low, normal, high, critical)
            context_data: Additional insight context (optional)
            user_id: User associated with insight (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.PROACTIVE_INSIGHT,
            data={
                "insight_id": insight_id,
                "contact_id": contact_id,
                "insight_type": insight_type,
                "confidence_score": round(confidence_score, 3),
                "title": title,
                "description": description,
                "suggested_actions": suggested_actions,
                "priority_level": priority_level,
                "context_data": context_data or {},
                "requires_action": priority_level in ["high", "critical"],
                "expires_at": (datetime.now(timezone.utc).timestamp() + 3600),  # 1 hour expiry
                "summary": f"AI Insight: {title} ({confidence_score:.1%} confidence)",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="critical" if priority_level == "critical" else "high" if priority_level == "high" else "normal",
        )

        await self._publish_event(event)
        logger.info(
            f"Published proactive insight: {insight_type} - {title} ({confidence_score:.1%} confidence - contact: {contact_id})"
        )

    async def publish_strategy_recommendation(
        self,
        recommendation_id: str,
        contact_id: str,
        strategy_type: str,
        recommendation_text: str = "",
        reasoning: str = "",
        confidence_score: float = 0.0,
        expected_impact: str = "medium",
        implementation_steps: List[str] = None,
        urgency: str = "normal",
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish AI strategy recommendation event.

        Args:
            recommendation_id: Unique recommendation identifier
            contact_id: Contact/lead identifier
            strategy_type: Type of strategy (negotiation, timing, communication)
            recommendation_text: Core recommendation
            reasoning: AI reasoning for the recommendation
            confidence_score: AI confidence in recommendation (0-1)
            expected_impact: Expected impact description
            implementation_steps: Step-by-step implementation guide
            urgency: Recommendation urgency (low, normal, high, immediate)
            user_id: User associated with recommendation (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        if implementation_steps is None:
            implementation_steps = []

        event = RealTimeEvent(
            event_type=EventType.STRATEGY_RECOMMENDATION,
            data={
                "recommendation_id": recommendation_id,
                "contact_id": contact_id,
                "strategy_type": strategy_type,
                "recommendation_text": recommendation_text,
                "reasoning": reasoning,
                "confidence_score": round(confidence_score, 3),
                "expected_impact": expected_impact,
                "implementation_steps": implementation_steps,
                "urgency": urgency,
                "requires_immediate_action": urgency == "immediate",
                "estimated_implementation_time": len(implementation_steps) * 5,  # 5 min per step estimate
                "summary": f"Strategy: {strategy_type.title()} ({confidence_score:.1%} confidence)",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="critical" if urgency == "immediate" else "high" if urgency == "high" else "normal",
        )

        await self._publish_event(event)
        logger.info(
            f"Published strategy recommendation: {strategy_type} - {urgency} urgency ({confidence_score:.1%} confidence - contact: {contact_id})"
        )

    async def publish_coaching_opportunity(
        self,
        opportunity_id: str,
        contact_id: str,
        coaching_area: str,
        opportunity_description: str,
        suggested_approach: str,
        learning_objectives: List[str],
        difficulty_level: str,
        estimated_time_minutes: int,
        resources: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish AI coaching opportunity event.

        Args:
            opportunity_id: Unique opportunity identifier
            contact_id: Contact/lead identifier
            coaching_area: Area for coaching (objection_handling, negotiation, follow_up)
            opportunity_description: Description of the coaching opportunity
            suggested_approach: Suggested coaching approach
            learning_objectives: List of learning objectives
            difficulty_level: Difficulty (beginner, intermediate, advanced)
            estimated_time_minutes: Estimated coaching time in minutes
            resources: Optional learning resources list
            user_id: User associated with coaching (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        # Calculate priority based on difficulty and objectives
        priority = "high" if difficulty_level == "advanced" and len(learning_objectives) >= 3 else "normal"

        event = RealTimeEvent(
            event_type=EventType.COACHING_OPPORTUNITY,
            data={
                "opportunity_id": opportunity_id,
                "contact_id": contact_id,
                "coaching_area": coaching_area,
                "opportunity_description": opportunity_description,
                "suggested_approach": suggested_approach,
                "learning_objectives": learning_objectives,
                "difficulty_level": difficulty_level,
                "estimated_time_minutes": estimated_time_minutes,
                "resources": resources or [],
                "skill_development_focus": coaching_area.replace("_", " ").title(),
                "completion_tracking_enabled": True,
                "summary": f"Coaching: {coaching_area.replace('_', ' ').title()} ({difficulty_level}, {estimated_time_minutes}min)",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority=priority,
        )

        await self._publish_event(event)
        logger.info(
            f"Published coaching opportunity: {coaching_area} - {difficulty_level} level ({estimated_time_minutes}min - contact: {contact_id})"
        )

    async def publish_ai_concierge_status_update(
        self,
        concierge_id: str,
        status: str,
        active_insights: int,
        monitoring_contacts: int,
        processing_time_ms: float,
        performance_metrics: Optional[Dict[str, Any]] = None,
        location_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Publish AI Concierge service status update.

        Args:
            concierge_id: Concierge service identifier
            status: Service status (active, idle, processing, error)
            active_insights: Number of active insights
            monitoring_contacts: Number of contacts being monitored
            processing_time_ms: Average processing time in milliseconds
            performance_metrics: Additional performance data (optional)
            location_id: Location/tenant ID (optional)
            **kwargs: Additional event data
        """
        event = RealTimeEvent(
            event_type=EventType.AI_CONCIERGE_STATUS,
            data={
                "concierge_id": concierge_id,
                "status": status,
                "active_insights": active_insights,
                "monitoring_contacts": monitoring_contacts,
                "processing_time_ms": round(processing_time_ms, 2),
                "performance_metrics": performance_metrics or {},
                "efficiency_score": self._calculate_concierge_efficiency(processing_time_ms, active_insights),
                "status_timestamp": datetime.now(timezone.utc).isoformat(),
                "summary": f"AI Concierge: {status} - {active_insights} insights, {monitoring_contacts} contacts",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            priority="high" if status == "error" else "low",
        )

        await self._publish_event(event)
        logger.info(
            f"Published AI Concierge status: {status} - {active_insights} insights, {monitoring_contacts} contacts"
        )

    def _calculate_concierge_efficiency(self, processing_time_ms: float, active_insights: int) -> float:
        """Calculate AI Concierge efficiency score."""
        # Target: <2000ms processing time, efficient insight generation
        time_score = max(0, 1.0 - (processing_time_ms - 1000) / 3000) if processing_time_ms > 1000 else 1.0
        insight_score = min(1.0, active_insights / 10)  # Optimal around 10 insights

        return round((time_score * 0.7) + (insight_score * 0.3), 2)

    def _calculate_sequence_progress(self, sequence_day: int) -> Dict[str, Any]:
        """Calculate lead bot sequence progress information."""
        progress_map = {
            3: {"progress": 33, "next_day": 7, "description": "Day 3 Follow-up"},
            7: {"progress": 67, "next_day": 30, "description": "Day 7 Call"},
            30: {"progress": 100, "next_day": None, "description": "Day 30 Final Touch"},
        }

        return progress_map.get(sequence_day, {"progress": 0, "next_day": None, "description": "Unknown"})

    def _calculate_health_score(self, status: str, response_time_ms: float) -> float:
        """Calculate component health score based on status and response time."""
        status_scores = {"healthy": 1.0, "degraded": 0.6, "recovering": 0.4, "down": 0.0}

        base_score = status_scores.get(status, 0.5)

        # Adjust based on response time
        if response_time_ms < 100:
            time_modifier = 1.0
        elif response_time_ms < 500:
            time_modifier = 0.8
        elif response_time_ms < 1000:
            time_modifier = 0.6
        else:
            time_modifier = 0.4

        return round(base_score * time_modifier, 2)

    async def _publish_event(self, event: RealTimeEvent):
        """
        OPTIMIZED event publishing with <10ms latency target.

        Phase 8+ Enhancement:
        - Micro-batching (10ms max vs 500ms previous)
        - Priority bypass for critical events (<1ms)
        - Real-time latency tracking and alerting
        - Performance compliance monitoring

        Args:
            event: Event to publish
        """
        start_time = time.perf_counter()  # High precision timing

        try:
            # Add processing timestamp for latency tracking
            event.data["_processing_start"] = start_time

            # 🚀 CRITICAL EVENT BYPASS (<1ms target)
            if self.critical_bypass and (
                event.priority == "critical" or event.event_type in {EventType.SYSTEM_ALERT, EventType.SMS_COMPLIANCE}
            ):
                # Immediate processing - no batching
                await self.websocket_manager.publish_event(event)
                await self._track_event_latency(event, start_time, 1, target_ms=1.0)
                return

            # 🎯 MICRO-BATCHING WITH PRIORITY ROUTING
            self._event_batch.append(event)

            # Enhanced batch processing criteria
            should_process_immediately = (
                len(self._event_batch) >= self.max_batch_size
                or event.priority == "high"
                or (time.perf_counter() - start_time) > self.batch_interval
            )

            if should_process_immediately:
                await self._process_event_batch_optimized()
            else:
                # Schedule micro-batch processing if not already scheduled
                if self._batch_timer is None:
                    self._batch_timer = asyncio.create_task(self._schedule_micro_batch_processing())

            # 📊 ENHANCED PERFORMANCE TRACKING
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            self._processing_times.append(processing_time_ms)

            # Keep only recent processing times (last 1000 for better statistics)
            if len(self._processing_times) > 1000:
                self._processing_times = self._processing_times[-1000:]

            # Update enhanced metrics
            self.metrics.average_processing_time_ms = sum(self._processing_times) / len(self._processing_times)
            self.metrics.total_events_published += 1
            self.metrics.last_event_time = datetime.now(timezone.utc)
            self._total_events_processed += 1

            # Track 10ms compliance
            if processing_time_ms < 10:
                self._events_under_10ms += 1

            # Alert on high latency
            if processing_time_ms > 15:  # 15ms warning threshold
                logger.warning(
                    f"⚠️ High event latency: {processing_time_ms:.2f}ms for {event.event_type.value} (target: <10ms)"
                )

            # Track events by type
            event_type_name = event.event_type.value
            self.metrics.events_by_type[event_type_name] = self.metrics.events_by_type.get(event_type_name, 0) + 1

        except Exception as e:
            logger.error(f"Error publishing event {event.event_type.value}: {e}")
            self.metrics.failed_publishes += 1

    async def _schedule_batch_processing(self):
        """Schedule batch processing after interval."""
        try:
            await asyncio.sleep(self.batch_interval)
            await self._process_event_batch()
        except asyncio.CancelledError:
            pass
        finally:
            self._batch_timer = None

    async def _schedule_micro_batch_processing(self):
        """OPTIMIZED: Schedule micro-batch processing with 10ms maximum delay."""
        try:
            await asyncio.sleep(self.batch_interval)  # 10ms micro-batch interval
            await self._process_event_batch_optimized()
        except asyncio.CancelledError:
            pass
        finally:
            self._batch_timer = None

    async def _process_event_batch(self):
        """Process the current batch of events."""
        if not self._event_batch:
            return

        # Cancel existing timer
        if self._batch_timer:
            self._batch_timer.cancel()
            self._batch_timer = None

        # Process events
        batch = self._event_batch.copy()
        self._event_batch.clear()

        # Group events by priority for processing order
        critical_events = [e for e in batch if e.priority == "critical"]
        high_events = [e for e in batch if e.priority == "high"]
        normal_events = [e for e in batch if e.priority in ["normal", "low"]]

        # Process critical events first
        for event in critical_events:
            await self.websocket_manager.publish_event(event)

        # Process high priority events
        for event in high_events:
            await self.websocket_manager.publish_event(event)

        # Batch process normal priority events
        if normal_events:
            # For normal events, we can potentially aggregate similar events
            aggregated_events = self._aggregate_similar_events(normal_events)
            for event in aggregated_events:
                await self.websocket_manager.publish_event(event)

        logger.debug(
            f"Processed event batch: {len(batch)} events ({len(critical_events)} critical, {len(high_events)} high, {len(normal_events)} normal)"
        )

    async def _process_event_batch_optimized(self):
        """OPTIMIZED: Process event batch with priority lanes and concurrent publishing."""
        if not self._event_batch:
            return

        # Cancel existing timer
        if self._batch_timer:
            self._batch_timer.cancel()
            self._batch_timer = None

        # Process events
        batch = self._event_batch.copy()
        self._event_batch.clear()

        processing_start = time.perf_counter()

        # 🎯 PRIORITY LANE PROCESSING
        critical_events = [e for e in batch if e.priority == "critical"]
        high_events = [e for e in batch if e.priority == "high"]
        normal_events = [e for e in batch if e.priority in ["normal", "low"]]

        # Process critical events first (should be rare due to bypass)
        for event in critical_events:
            await self.websocket_manager.publish_event(event)

        # Concurrent processing for high and normal priority events
        if high_events:
            await asyncio.gather(*[self.websocket_manager.publish_event(event) for event in high_events])

        # Apply intelligent aggregation for normal events to reduce volume
        if normal_events:
            aggregated_events = self._aggregate_similar_events_optimized(normal_events)
            await asyncio.gather(*[self.websocket_manager.publish_event(event) for event in aggregated_events])

        # Track latency for all events in batch
        for event in batch:
            await self._track_event_latency(event, processing_start, len(batch), target_ms=10.0)

        logger.debug(
            f"📊 Optimized batch processed: {len(batch)} events "
            f"({len(critical_events)} critical, {len(high_events)} high, {len(normal_events)} normal)"
        )

    def _aggregate_similar_events_optimized(self, events: List[RealTimeEvent]) -> List[RealTimeEvent]:
        """
        ENHANCED: Intelligent event aggregation to reduce WebSocket message volume.

        Args:
            events: List of events to potentially aggregate

        Returns:
            List of events (with intelligent aggregation applied)
        """
        if len(events) <= 1:
            return events

        # Group events by aggregation key
        aggregable_groups = {}
        standalone_events = []

        for event in events:
            # Events that can be aggregated to reduce volume
            if event.event_type in {
                EventType.DASHBOARD_REFRESH,
                EventType.PERFORMANCE_UPDATE,
                EventType.AI_CONCIERGE_STATUS,
            }:
                key = f"{event.event_type.value}_{event.user_id}_{event.location_id}"

                if key not in aggregable_groups:
                    aggregable_groups[key] = []
                aggregable_groups[key].append(event)
            else:
                standalone_events.append(event)

        # Create aggregated events for groups with multiple events
        result_events = standalone_events.copy()

        for group_events in aggregable_groups.values():
            if len(group_events) > 1:
                # Create aggregated event
                base_event = group_events[0]
                aggregated_event = RealTimeEvent(
                    event_type=base_event.event_type,
                    data={
                        "aggregated_events": len(group_events),
                        "time_span_ms": (
                            max(e.timestamp for e in group_events) - min(e.timestamp for e in group_events)
                        ).total_seconds()
                        * 1000,
                        "combined_data": [e.data for e in group_events],
                    },
                    timestamp=max(e.timestamp for e in group_events),
                    user_id=base_event.user_id,
                    location_id=base_event.location_id,
                    priority=base_event.priority,
                )
                result_events.append(aggregated_event)
            else:
                result_events.extend(group_events)

        return result_events

    async def _track_event_latency(
        self, event: RealTimeEvent, processing_start: float, batch_size: int, target_ms: float
    ):
        """Track individual event latency for performance optimization."""
        processing_end = time.perf_counter()
        event_start = event.data.get("_processing_start", processing_start)

        # Calculate end-to-end latency
        latency_ms = (processing_end - event_start) * 1000
        target_met = latency_ms <= target_ms

        # Store measurement
        measurement = {
            "event_type": event.event_type.value,
            "priority": event.priority,
            "latency_ms": latency_ms,
            "target_met": target_met,
            "batch_size": batch_size,
            "timestamp": datetime.now(timezone.utc),
        }

        self._latency_measurements.append(measurement)

        # Keep only recent measurements (last 1000)
        if len(self._latency_measurements) > 1000:
            self._latency_measurements = self._latency_measurements[-1000:]

        # Alert on target miss
        if not target_met:
            logger.warning(
                f"⚠️ Latency target missed: {latency_ms:.2f}ms (target: {target_ms}ms) "
                f"for {event.event_type.value} [batch_size: {batch_size}]"
            )

        # Clean up processing timestamp
        if "_processing_start" in event.data:
            del event.data["_processing_start"]

    def _aggregate_similar_events(self, events: List[RealTimeEvent]) -> List[RealTimeEvent]:
        """
        Legacy method - maintained for backward compatibility.
        Use _aggregate_similar_events_optimized for enhanced performance.
        """
        return self._aggregate_similar_events_optimized(events)

    async def create_decorator(self, event_type: EventType, **event_kwargs):
        """
        Create a decorator for automatically publishing events from function calls.

        Args:
            event_type: Type of event to publish
            **event_kwargs: Additional event data

        Returns:
            Decorator function
        """

        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # Call original function
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

                # Extract event data from function result or arguments
                event_data = {
                    "function": func.__name__,
                    "result": result if isinstance(result, dict) else {"value": result},
                    **event_kwargs,
                }

                # Create and publish event
                event = RealTimeEvent(
                    event_type=event_type, data=event_data, timestamp=datetime.now(timezone.utc), priority="normal"
                )

                await self._publish_event(event)
                return result

            return wrapper

        return decorator

    def get_metrics(self) -> Dict[str, Any]:
        """Get enhanced event publishing metrics with optimization tracking."""
        base_metrics = {
            "total_events_published": self.metrics.total_events_published,
            "events_by_type": self.metrics.events_by_type,
            "last_event_time": self.metrics.last_event_time.isoformat() if self.metrics.last_event_time else None,
            "average_processing_time_ms": round(self.metrics.average_processing_time_ms, 3),
            "failed_publishes": self.metrics.failed_publishes,
            "batch_queue_size": len(self._event_batch),
            "websocket_metrics": self.websocket_manager.get_metrics(),
        }

        # 📊 ENHANCED OPTIMIZATION METRICS
        if self._total_events_processed > 0:
            compliance_10ms = (self._events_under_10ms / self._total_events_processed) * 100

            optimization_metrics = {
                "optimization_status": "enabled",
                "micro_batch_interval_ms": self.batch_interval * 1000,
                "events_under_10ms_count": self._events_under_10ms,
                "total_events_processed": self._total_events_processed,
                "latency_compliance_10ms_percentage": round(compliance_10ms, 2),
                "target_achievement": "✅ ACHIEVED" if compliance_10ms >= 95 else "🎯 IN PROGRESS",
            }

            # Recent latency statistics
            if self._latency_measurements:
                recent_latencies = [m["latency_ms"] for m in self._latency_measurements[-100:]]
                optimization_metrics.update(
                    {
                        "recent_avg_latency_ms": round(sum(recent_latencies) / len(recent_latencies), 3),
                        "recent_max_latency_ms": round(max(recent_latencies), 3),
                        "recent_min_latency_ms": round(min(recent_latencies), 3),
                    }
                )

                # Calculate percentiles
                sorted_latencies = sorted(recent_latencies)
                optimization_metrics.update(
                    {
                        "p95_latency_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.95)], 3),
                        "p99_latency_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.99)], 3),
                    }
                )

            base_metrics["optimization_metrics"] = optimization_metrics

        return base_metrics

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for optimization monitoring."""
        if self._total_events_processed == 0:
            return {"status": "no_data", "message": "No events processed yet - performance data unavailable"}

        compliance_10ms = (self._events_under_10ms / self._total_events_processed) * 100

        return {
            "status": "optimized",
            "optimization_level": "micro_batching_enabled",
            "performance_grade": self._get_performance_grade(compliance_10ms),
            "target_compliance_10ms": round(compliance_10ms, 1),
            "total_events_processed": self._total_events_processed,
            "average_processing_time_ms": round(self.metrics.average_processing_time_ms, 3),
            "batch_configuration": {
                "interval_ms": self.batch_interval * 1000,
                "max_batch_size": self.max_batch_size,
                "critical_bypass_enabled": self.critical_bypass,
            },
        }

    def _get_performance_grade(self, compliance_percentage: float) -> str:
        """Get performance grade based on 10ms compliance."""
        if compliance_percentage >= 99:
            return "A+ (Exceptional)"
        elif compliance_percentage >= 95:
            return "A (Excellent - Target Achieved)"
        elif compliance_percentage >= 90:
            return "B+ (Very Good)"
        elif compliance_percentage >= 80:
            return "B (Good)"
        elif compliance_percentage >= 70:
            return "C+ (Acceptable)"
        else:
            return "C (Needs Optimization)"

    async def publish_seller_bot_message_processed(
        self,
        contact_id: str,
        message_content: str,
        bot_response: str,
        seller_temperature: str,
        processing_time_ms: float,
        questions_answered: int,
        qualification_complete: bool,
        **kwargs,
    ):
        """Publish event after Jorge Seller Bot processes a message."""
        event = RealTimeEvent(
            event_type=EventType.BOT_STATUS_UPDATE,  # Use existing type or create new
            data={
                "contact_id": contact_id,
                "message_preview": message_content[:50],
                "bot_response_preview": bot_response[:50],
                "seller_temperature": seller_temperature,
                "processing_time_ms": round(processing_time_ms, 2),
                "questions_answered": questions_answered,
                "qualification_complete": qualification_complete,
                "summary": f"Jorge processed message: {seller_temperature} (Q: {questions_answered})",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            priority="normal",
        )
        await self._publish_event(event)

    # ============================================================================
    # Phase 2.1: Behavioral Prediction Event Publishers
    # ============================================================================

    async def publish_behavioral_prediction(
        self,
        lead_id: str,
        location_id: str,
        behavior_category: str = "moderate",
        churn_risk_score: float = 0.0,
        engagement_score: float = 0.5,
        next_actions: List[Dict[str, Any]] = None,
        prediction_latency_ms: float = 0.0,
        user_id: Optional[int] = None,
        **kwargs,
    ):
        """
        Publish behavioral prediction completion event.

        Real-time notification when new behavioral prediction is available.
        """
        if next_actions is None:
            next_actions = []

        event = RealTimeEvent(
            event_type=EventType.BEHAVIORAL_PREDICTION_COMPLETE,
            data={
                "lead_id": lead_id,
                "behavior_category": behavior_category,
                "churn_risk_score": round(churn_risk_score, 2),
                "engagement_score_7d": round(engagement_score, 2),
                "next_actions": next_actions[:3],  # Top 3 actions
                "prediction_latency_ms": round(prediction_latency_ms, 2),
                "performance_grade": self._calculate_performance_grade(prediction_latency_ms),
                "urgency_level": "high" if churn_risk_score > 70 else "normal",
                "summary": f"Behavioral prediction: {behavior_category} (churn risk: {churn_risk_score:.0f}%)",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if churn_risk_score > 70 else "normal",
        )

        await self._publish_event(event)
        logger.info(
            f"Published behavioral prediction: {lead_id} ({behavior_category}, {churn_risk_score:.0f}% churn risk)"
        )

    async def publish_churn_risk_alert(
        self,
        lead_id: str,
        location_id: str,
        churn_risk_score: float,
        risk_factors: List[str],
        prevention_strategies: List[str],
        urgency: str = "high",
        user_id: Optional[int] = None,
        **kwargs,
    ):
        """
        Publish high churn risk alert for immediate action.

        Critical priority for leads at risk of churning.
        """
        event = RealTimeEvent(
            event_type=EventType.CHURN_RISK_ALERT,
            data={
                "lead_id": lead_id,
                "churn_risk_score": round(churn_risk_score, 2),
                "risk_factors": risk_factors,
                "prevention_strategies": prevention_strategies[:5],  # Top 5 strategies
                "urgency": urgency,
                "requires_immediate_action": churn_risk_score > 80,
                "escalation_level": self._calculate_churn_escalation_level(churn_risk_score),
                "time_sensitive": True,
                "summary": f"Churn Risk Alert: {churn_risk_score:.0f}% - {len(risk_factors)} factors identified",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            user_id=user_id,
            priority="critical" if churn_risk_score > 80 else "high",
        )

        await self._publish_event(event)
        logger.warning(f"Churn risk alert: {lead_id} ({churn_risk_score:.0f}%) - {len(risk_factors)} risk factors")

    async def publish_behavior_category_change(
        self,
        lead_id: str,
        location_id: str,
        previous_category: str,
        new_category: str,
        change_reason: str,
        confidence: float,
        user_id: Optional[int] = None,
        **kwargs,
    ):
        """
        Publish behavior category change notification.

        Alerts when lead behavior significantly changes categories.
        """
        # Determine if this is a positive or negative change
        positive_changes = [
            ("dormant", "low_engagement"),
            ("low_engagement", "moderately_engaged"),
            ("moderately_engaged", "highly_engaged"),
            ("churning", "low_engagement"),
            ("churning", "moderately_engaged"),
        ]

        change_type = "improvement" if (previous_category, new_category) in positive_changes else "decline"

        event = RealTimeEvent(
            event_type=EventType.BEHAVIOR_CATEGORY_CHANGE,
            data={
                "lead_id": lead_id,
                "previous_category": previous_category,
                "new_category": new_category,
                "change_reason": change_reason,
                "change_type": change_type,
                "confidence": round(confidence, 4),
                "significant_change": confidence > 0.8,
                "requires_action": change_type == "decline",
                "summary": f"Behavior change: {previous_category} → {new_category} ({change_type})",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            user_id=user_id,
            priority="high" if change_type == "decline" else "normal",
        )

        await self._publish_event(event)
        logger.info(f"Behavior category change: {lead_id} ({previous_category} → {new_category}) - {change_type}")

    async def publish_engagement_trend_change(
        self,
        lead_id: str,
        location_id: str,
        trend_direction: str,
        velocity: float,
        current_score: float,
        projected_score: float,
        time_window_hours: int,
        user_id: Optional[int] = None,
        **kwargs,
    ):
        """
        Publish engagement trend change notification.

        Alerts when lead engagement patterns shift significantly.
        """
        event = RealTimeEvent(
            event_type=EventType.ENGAGEMENT_TREND_CHANGE,
            data={
                "lead_id": lead_id,
                "trend_direction": trend_direction,
                "velocity": round(velocity, 3),
                "current_engagement_score": round(current_score, 2),
                "projected_engagement_score": round(projected_score, 2),
                "time_window_hours": time_window_hours,
                "trend_strength": self._calculate_trend_strength(velocity),
                "significant_change": abs(velocity) > 0.5,
                "needs_intervention": trend_direction == "decreasing" and velocity < -0.3,
                "summary": f"Engagement trend: {trend_direction} ({current_score:.0f}% → {projected_score:.0f}%)",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            user_id=user_id,
            priority="high" if trend_direction == "decreasing" else "normal",
        )

        await self._publish_event(event)
        logger.info(f"Engagement trend change: {lead_id} ({trend_direction}, velocity: {velocity:.2f})")

    async def publish_optimal_contact_window(
        self,
        lead_id: str,
        location_id: str,
        contact_window: Dict[str, Any],
        contact_channel: str,
        probability_success: float,
        user_id: Optional[int] = None,
        **kwargs,
    ):
        """
        Publish optimal contact window recommendation.

        Notifies when optimal contact timing is identified.
        """
        event = RealTimeEvent(
            event_type=EventType.OPTIMAL_CONTACT_WINDOW,
            data={
                "lead_id": lead_id,
                "contact_window": contact_window,
                "recommended_channel": contact_channel,
                "success_probability": round(probability_success, 4),
                "window_start": contact_window.get("start"),
                "window_end": contact_window.get("end"),
                "timezone": contact_window.get("timezone", "America/Chicago"),
                "confidence_level": contact_window.get("confidence", 0.7),
                "time_sensitive": probability_success > 0.8,
                "summary": f"Optimal contact: {contact_window.get('start')}-{contact_window.get('end')} via {contact_channel} ({probability_success:.1%} success)",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            user_id=user_id,
            priority="high" if probability_success > 0.8 else "normal",
        )

        await self._publish_event(event)
        logger.info(f"Optimal contact window: {lead_id} ({contact_channel}, {probability_success:.1%} success)")

    async def publish_behavioral_feedback_recorded(
        self,
        lead_id: str,
        location_id: str,
        feedback_type: str,
        prediction_accuracy: float,
        model_version: str = "v1.0",
        user_id: Optional[int] = None,
        **kwargs,
    ):
        """
        Publish feedback recording event for learning loop.

        Confirms when prediction feedback has been recorded for model improvement.
        """
        event = RealTimeEvent(
            event_type=EventType.BEHAVIORAL_FEEDBACK_RECORDED,
            data={
                "lead_id": lead_id,
                "feedback_type": feedback_type,
                "prediction_accuracy": round(prediction_accuracy, 4),
                "model_version": model_version,
                "accuracy_grade": self._calculate_accuracy_grade(prediction_accuracy),
                "learning_value": "high" if prediction_accuracy < 0.7 else "medium",
                "contributes_to_improvement": prediction_accuracy != 1.0,  # Perfect predictions don't teach much
                "summary": f"Feedback recorded: {feedback_type} ({prediction_accuracy:.1%} accuracy)",
                **kwargs,
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            user_id=user_id,
            priority="low",  # Feedback is informational, not urgent
        )

        await self._publish_event(event)
        logger.debug(f"Behavioral feedback recorded: {lead_id} ({feedback_type}, {prediction_accuracy:.1%} accuracy)")

    # ============================================================================
    # Phase 2.2: Advanced Property Matching Events
    # ============================================================================

    async def publish_property_match_generated(
        self,
        lead_id: str,
        location_id: str,
        property_id: str,
        match_score: float,
        behavioral_fit: float,
        engagement_prediction: float,
        rank: int,
        presentation_strategy: str,
        reasoning: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Publish property match generation event with behavioral enhancement.

        Args:
            lead_id: Lead identifier
            location_id: Location identifier for tenant scoping
            property_id: Matched property identifier
            match_score: Overall match score (0.0-1.0)
            behavioral_fit: Behavioral fit score (0.0-100.0)
            engagement_prediction: Predicted engagement probability (0.0-1.0)
            rank: Match rank in results (1-based)
            presentation_strategy: Optimal presentation strategy
            reasoning: Behavioral reasoning for match
            user_id: Optional user identifier
        """
        try:
            match_quality_grade = self._calculate_match_quality_grade(match_score, behavioral_fit)

            event = RealTimeEvent(
                event_type=EventType.PROPERTY_MATCH_GENERATED,
                data={
                    "lead_id": lead_id,
                    "property_id": property_id,
                    "match_score": round(match_score, 3),
                    "behavioral_fit": round(behavioral_fit, 1),
                    "engagement_prediction": round(engagement_prediction, 3),
                    "rank": rank,
                    "presentation_strategy": presentation_strategy,
                    "reasoning": reasoning,
                    "quality_grade": match_quality_grade,
                    "is_top_match": rank <= 3,
                    "high_confidence": match_score >= 0.8 and behavioral_fit >= 75.0,
                    "recommended_action": "schedule_showing" if engagement_prediction > 0.7 else "send_info",
                    "match_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                timestamp=datetime.now(timezone.utc),
                location_id=location_id,
                user_id=user_id,
                priority="high" if rank <= 3 else "normal",
            )

            await self._publish_event(event)
            logger.debug(
                f"Property match generated: {property_id} for {lead_id} (rank #{rank}, {match_score:.1%} score)"
            )

        except Exception as e:
            logger.error(f"Failed to publish property match generated event: {e}")

    async def publish_property_inventory_update(
        self,
        location_id: str,
        property_ids: List[str],
        update_type: str,
        affected_leads: List[str],
        inventory_change: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Publish property inventory update event.

        Args:
            location_id: Location identifier for tenant scoping
            property_ids: List of property identifiers affected
            update_type: Type of update (new_listings, price_change, status_change)
            affected_leads: List of lead IDs that may be interested
            inventory_change: Description of the change
            user_id: Optional user identifier
        """
        try:
            event = RealTimeEvent(
                event_type=EventType.PROPERTY_INVENTORY_UPDATE,
                data={
                    "property_ids": property_ids,
                    "property_count": len(property_ids),
                    "update_type": update_type,
                    "affected_leads": affected_leads,
                    "affected_lead_count": len(affected_leads),
                    "inventory_change": inventory_change,
                    "requires_reanalysis": update_type in ["new_listings", "price_change"],
                    "priority_update": len(affected_leads) > 10,
                    "update_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                timestamp=datetime.now(timezone.utc),
                location_id=location_id,
                user_id=user_id,
                priority="high" if len(affected_leads) > 10 else "normal",
            )

            await self._publish_event(event)
            logger.debug(
                f"Property inventory update: {len(property_ids)} properties, {len(affected_leads)} leads affected"
            )

        except Exception as e:
            logger.error(f"Failed to publish property inventory update event: {e}")

    async def publish_behavioral_match_improvement(
        self,
        lead_id: str,
        location_id: str,
        improvement_type: str,
        old_score: float,
        new_score: float,
        behavioral_factors: Dict[str, Any],
        recommendations: List[str],
        user_id: Optional[str] = None,
    ) -> None:
        """
        Publish behavioral match improvement event.

        Args:
            lead_id: Lead identifier
            location_id: Location identifier for tenant scoping
            improvement_type: Type of improvement (accuracy, relevance, engagement)
            old_score: Previous match score
            new_score: Improved match score
            behavioral_factors: Behavioral factors contributing to improvement
            recommendations: Action recommendations
            user_id: Optional user identifier
        """
        try:
            improvement_magnitude = new_score - old_score

            event = RealTimeEvent(
                event_type=EventType.BEHAVIORAL_MATCH_IMPROVEMENT,
                data={
                    "lead_id": lead_id,
                    "improvement_type": improvement_type,
                    "old_score": round(old_score, 3),
                    "new_score": round(new_score, 3),
                    "improvement_magnitude": round(improvement_magnitude, 3),
                    "improvement_percentage": round((improvement_magnitude / max(old_score, 0.01)) * 100, 1),
                    "behavioral_factors": behavioral_factors,
                    "recommendations": recommendations,
                    "significant_improvement": improvement_magnitude >= 0.2,
                    "suggested_actions": recommendations[:3],  # Top 3 recommendations
                    "improvement_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                timestamp=datetime.now(timezone.utc),
                location_id=location_id,
                user_id=user_id,
                priority="high" if improvement_magnitude >= 0.3 else "normal",
            )

            await self._publish_event(event)
            logger.debug(f"Behavioral match improvement: {lead_id} ({improvement_type}, +{improvement_magnitude:.1%})")

        except Exception as e:
            logger.error(f"Failed to publish behavioral match improvement event: {e}")

    # ============================================================================
    # Phase 2.3: Conversation Intelligence Events
    # ============================================================================

    async def publish_objection_detected(
        self,
        lead_id: str,
        location_id: str,
        objection_type: str,
        severity: str,
        confidence: float,
        context: str,
        suggested_responses: List[str],
        user_id: Optional[str] = None,
    ) -> None:
        """
        Publish objection detection event.

        Args:
            lead_id: Lead identifier
            location_id: Location identifier for tenant scoping
            objection_type: Type of objection detected
            severity: Objection severity (low, medium, high)
            confidence: Detection confidence (0.0-1.0)
            context: Context where objection was detected
            suggested_responses: List of suggested response strategies
            user_id: Optional user identifier
        """
        try:
            severity_priority = self._determine_objection_priority(severity, confidence)

            event = RealTimeEvent(
                event_type=EventType.OBJECTION_DETECTED,
                data={
                    "lead_id": lead_id,
                    "objection_type": objection_type,
                    "severity": severity,
                    "confidence": round(confidence, 3),
                    "context": context,
                    "suggested_responses": suggested_responses,
                    "requires_immediate_action": severity in ["high", "critical"],
                    "response_urgency": "immediate" if severity == "high" else "within_24h",
                    "objection_category": self._categorize_objection(objection_type),
                    "coaching_opportunity": severity in ["medium", "high"],
                    "detection_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                timestamp=datetime.now(timezone.utc),
                location_id=location_id,
                user_id=user_id,
                priority=severity_priority,
            )

            await self._publish_event(event)
            logger.debug(f"Objection detected: {objection_type} for {lead_id} ({severity} severity)")

        except Exception as e:
            logger.error(f"Failed to publish objection detected event: {e}")

    async def publish_sentiment_warning(
        self,
        lead_id: str,
        location_id: str,
        current_sentiment: float,
        trend: str,
        risk_level: str,
        recommendations: List[str],
        user_id: Optional[str] = None,
    ) -> None:
        """
        Publish sentiment warning event.

        Args:
            lead_id: Lead identifier
            location_id: Location identifier for tenant scoping
            current_sentiment: Current sentiment score (-1.0 to 1.0)
            trend: Sentiment trend (improving, declining, stable)
            risk_level: Risk level (low, medium, high)
            recommendations: List of recommended actions
            user_id: Optional user identifier
        """
        try:
            event = RealTimeEvent(
                event_type=EventType.SENTIMENT_WARNING,
                data={
                    "lead_id": lead_id,
                    "current_sentiment": round(current_sentiment, 3),
                    "sentiment_level": self._classify_sentiment_level(current_sentiment),
                    "trend": trend,
                    "risk_level": risk_level,
                    "recommendations": recommendations,
                    "requires_intervention": risk_level == "high",
                    "suggested_timeline": "immediate" if risk_level == "high" else "within_24h",
                    "escalation_needed": current_sentiment <= -0.5 and trend == "declining",
                    "recovery_potential": current_sentiment > -0.3,
                    "warning_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                timestamp=datetime.now(timezone.utc),
                location_id=location_id,
                user_id=user_id,
                priority="critical" if risk_level == "high" else "high",
            )

            await self._publish_event(event)
            logger.debug(f"Sentiment warning: {lead_id} (sentiment: {current_sentiment:.2f}, {risk_level} risk)")

        except Exception as e:
            logger.error(f"Failed to publish sentiment warning event: {e}")

    async def publish_conversation_insight_generated(
        self,
        lead_id: str,
        location_id: str,
        insight_type: str,
        insight_summary: str,
        confidence: float,
        action_items: List[str],
        processing_time_ms: float,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Publish conversation insight generation event.

        Args:
            lead_id: Lead identifier
            location_id: Location identifier for tenant scoping
            insight_type: Type of insight generated
            insight_summary: Summary of the insight
            confidence: Insight confidence (0.0-1.0)
            action_items: List of actionable items
            processing_time_ms: Processing time in milliseconds
            user_id: Optional user identifier
        """
        try:
            performance_grade = self._calculate_performance_grade(processing_time_ms)

            event = RealTimeEvent(
                event_type=EventType.CONVERSATION_INSIGHT_GENERATED,
                data={
                    "lead_id": lead_id,
                    "insight_type": insight_type,
                    "insight_summary": insight_summary,
                    "confidence": round(confidence, 3),
                    "action_items": action_items,
                    "processing_time_ms": round(processing_time_ms, 1),
                    "performance_grade": performance_grade,
                    "high_confidence": confidence >= 0.8,
                    "actionable_items_count": len(action_items),
                    "requires_follow_up": len(action_items) > 0,
                    "insight_priority": "high" if confidence >= 0.8 else "normal",
                    "insight_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                timestamp=datetime.now(timezone.utc),
                location_id=location_id,
                user_id=user_id,
                priority="high" if confidence >= 0.8 else "normal",
            )

            await self._publish_event(event)
            logger.debug(f"Conversation insight: {insight_type} for {lead_id} ({confidence:.1%} confidence)")

        except Exception as e:
            logger.error(f"Failed to publish conversation insight event: {e}")

    # ============================================================================
    # Phase 2.4: Preference Learning Events
    # ============================================================================

    async def publish_preference_learning_complete(
        self,
        client_id: str,
        location_id: str,
        learning_source: str,
        signals_processed: int,
        learning_latency_ms: float,
        preferences_updated: List[str],
        profile_completeness: float,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Publish preference learning completion event.

        Args:
            client_id: Client identifier
            location_id: Location identifier for tenant scoping
            learning_source: Source of learning (conversation, property_view, behavioral)
            signals_processed: Number of preference signals processed
            learning_latency_ms: Learning processing time in milliseconds
            preferences_updated: List of preference names that were updated
            profile_completeness: Updated profile completeness score (0.0-1.0)
            user_id: Optional user identifier
        """
        try:
            performance_grade = self._calculate_performance_grade(learning_latency_ms)

            event = RealTimeEvent(
                event_type=EventType.PREFERENCE_LEARNING_COMPLETE,
                data={
                    "client_id": client_id,
                    "learning_source": learning_source,
                    "signals_processed": signals_processed,
                    "learning_latency_ms": round(learning_latency_ms, 1),
                    "performance_grade": performance_grade,
                    "preferences_updated": preferences_updated,
                    "preferences_updated_count": len(preferences_updated),
                    "profile_completeness": round(profile_completeness, 3),
                    "profile_completeness_percentage": round(profile_completeness * 100, 1),
                    "significant_learning": signals_processed >= 5,
                    "high_completeness": profile_completeness >= 0.8,
                    "learning_efficiency": round(len(preferences_updated) / max(signals_processed, 1), 2),
                    "learning_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                timestamp=datetime.now(timezone.utc),
                location_id=location_id,
                user_id=user_id,
                priority="normal",
            )

            await self._publish_event(event)
            logger.debug(f"Preference learning: {client_id} from {learning_source} ({signals_processed} signals)")

        except Exception as e:
            logger.error(f"Failed to publish preference learning complete event: {e}")

    async def publish_preference_drift_detected(
        self,
        client_id: str,
        location_id: str,
        preference_name: str,
        drift_magnitude: float,
        old_value: Any,
        new_value: Any,
        drift_direction: str,
        confidence: float,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Publish preference drift detection event.

        Args:
            client_id: Client identifier
            location_id: Location identifier for tenant scoping
            preference_name: Name of the preference that drifted
            drift_magnitude: Magnitude of the drift (0.0-1.0)
            old_value: Previous preference value
            new_value: New preference value
            drift_direction: Direction of drift (increasing, decreasing, changing)
            confidence: Drift detection confidence (0.0-1.0)
            user_id: Optional user identifier
        """
        try:
            drift_significance = self._calculate_drift_significance(drift_magnitude, confidence)

            event = RealTimeEvent(
                event_type=EventType.PREFERENCE_DRIFT_DETECTED,
                data={
                    "client_id": client_id,
                    "preference_name": preference_name,
                    "drift_magnitude": round(drift_magnitude, 3),
                    "old_value": str(old_value),
                    "new_value": str(new_value),
                    "drift_direction": drift_direction,
                    "confidence": round(confidence, 3),
                    "drift_significance": drift_significance,
                    "requires_reanalysis": drift_significance in ["high", "critical"],
                    "preference_category": self._categorize_preference_name(preference_name),
                    "impact_level": "high" if preference_name in ["budget", "location", "bedrooms"] else "medium",
                    "adaptation_needed": drift_magnitude >= 0.3,
                    "drift_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                timestamp=datetime.now(timezone.utc),
                location_id=location_id,
                user_id=user_id,
                priority="high" if drift_magnitude >= 0.5 else "normal",
            )

            await self._publish_event(event)
            logger.debug(f"Preference drift: {preference_name} for {client_id} (magnitude: {drift_magnitude:.2f})")

        except Exception as e:
            logger.error(f"Failed to publish preference drift event: {e}")

    async def publish_preference_profile_updated(
        self,
        client_id: str,
        location_id: str,
        update_type: str,
        updated_preferences: List[str],
        profile_completeness: float,
        confidence_improvement: float,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Publish preference profile update event.

        Args:
            client_id: Client identifier
            location_id: Location identifier for tenant scoping
            update_type: Type of update (learning, drift_adaptation, manual_correction)
            updated_preferences: List of preference names that were updated
            profile_completeness: Current profile completeness score (0.0-1.0)
            confidence_improvement: Overall confidence improvement
            user_id: Optional user identifier
        """
        try:
            event = RealTimeEvent(
                event_type=EventType.PREFERENCE_PROFILE_UPDATED,
                data={
                    "client_id": client_id,
                    "update_type": update_type,
                    "updated_preferences": updated_preferences,
                    "updated_preferences_count": len(updated_preferences),
                    "profile_completeness": round(profile_completeness, 3),
                    "profile_completeness_percentage": round(profile_completeness * 100, 1),
                    "confidence_improvement": round(confidence_improvement, 3),
                    "significant_update": len(updated_preferences) >= 3,
                    "high_completeness": profile_completeness >= 0.8,
                    "profile_ready_for_matching": profile_completeness >= 0.6,
                    "confidence_increased": confidence_improvement > 0,
                    "update_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                timestamp=datetime.now(timezone.utc),
                location_id=location_id,
                user_id=user_id,
                priority="normal",
            )

            await self._publish_event(event)
            logger.debug(f"Preference profile updated: {client_id} ({len(updated_preferences)} preferences)")

        except Exception as e:
            logger.error(f"Failed to publish preference profile updated event: {e}")

    # ============================================================================
    # Helper Methods for Phase 2 Intelligence Layer Events
    # ============================================================================

    def _calculate_match_quality_grade(self, match_score: float, behavioral_fit: float) -> str:
        """Calculate match quality grade from scores."""
        combined_score = (match_score + (behavioral_fit / 100.0)) / 2
        if combined_score >= 0.9:
            return "A+ (Exceptional)"
        elif combined_score >= 0.8:
            return "A (Excellent)"
        elif combined_score >= 0.7:
            return "B (Good)"
        elif combined_score >= 0.6:
            return "C (Fair)"
        else:
            return "D (Poor)"

    def _determine_objection_priority(self, severity: str, confidence: float) -> str:
        """Determine objection event priority."""
        if severity == "high" and confidence >= 0.8:
            return "critical"
        elif severity == "high" or (severity == "medium" and confidence >= 0.9):
            return "high"
        elif severity == "medium":
            return "normal"
        else:
            return "low"

    def _categorize_objection(self, objection_type: str) -> str:
        """Categorize objection type for reporting."""
        financial_objections = ["pricing", "financial", "budget"]
        process_objections = ["timing", "process", "commitment"]
        trust_objections = ["trust", "competition"]

        if objection_type in financial_objections:
            return "financial"
        elif objection_type in process_objections:
            return "process"
        elif objection_type in trust_objections:
            return "trust"
        else:
            return "property"

    def _classify_sentiment_level(self, sentiment: float) -> str:
        """Classify sentiment score into levels."""
        if sentiment >= 0.6:
            return "very_positive"
        elif sentiment >= 0.2:
            return "positive"
        elif sentiment >= -0.2:
            return "neutral"
        elif sentiment >= -0.6:
            return "negative"
        else:
            return "very_negative"

    def _calculate_drift_significance(self, magnitude: float, confidence: float) -> str:
        """Calculate preference drift significance."""
        weighted_drift = magnitude * confidence
        if weighted_drift >= 0.7:
            return "critical"
        elif weighted_drift >= 0.5:
            return "high"
        elif weighted_drift >= 0.3:
            return "medium"
        else:
            return "low"

    def _categorize_preference_name(self, preference_name: str) -> str:
        """Categorize preference by importance."""
        core_prefs = ["budget", "location", "bedrooms", "bathrooms"]
        important_prefs = ["property_type", "urgency", "timeline"]

        if any(core in preference_name.lower() for core in core_prefs):
            return "core"
        elif any(imp in preference_name.lower() for imp in important_prefs):
            return "important"
        else:
            return "lifestyle"

    # ============================================================================
    # Helper Methods for Behavioral Events
    # ============================================================================

    def _calculate_performance_grade(self, latency_ms: float) -> str:
        """Calculate performance grade based on prediction latency."""
        if latency_ms <= 25:
            return "A+ (Excellent)"
        elif latency_ms <= 50:
            return "A (Good)"
        elif latency_ms <= 100:
            return "B (Acceptable)"
        elif latency_ms <= 200:
            return "C (Slow)"
        else:
            return "D (Poor)"

    def _calculate_churn_escalation_level(self, churn_risk_score: float) -> str:
        """Calculate churn risk escalation level."""
        if churn_risk_score >= 90:
            return "critical"
        elif churn_risk_score >= 80:
            return "urgent"
        elif churn_risk_score >= 70:
            return "high"
        elif churn_risk_score >= 50:
            return "moderate"
        else:
            return "low"

    def _calculate_trend_strength(self, velocity: float) -> str:
        """Calculate trend strength from velocity."""
        abs_velocity = abs(velocity)
        if abs_velocity >= 1.0:
            return "very_strong"
        elif abs_velocity >= 0.5:
            return "strong"
        elif abs_velocity >= 0.2:
            return "moderate"
        else:
            return "weak"

    def _calculate_accuracy_grade(self, accuracy: float) -> str:
        """Calculate accuracy grade for feedback."""
        if accuracy >= 0.9:
            return "A (Excellent)"
        elif accuracy >= 0.8:
            return "B (Good)"
        elif accuracy >= 0.7:
            return "C (Fair)"
        elif accuracy >= 0.5:
            return "D (Poor)"
        else:
            return "F (Failed)"


@lru_cache(maxsize=1)
def get_event_publisher() -> EventPublisher:
    """Get singleton event publisher instance."""
    return EventPublisher()


# Convenience functions for common event publishing
async def publish_lead_update(lead_id: str, lead_data: Dict[str, Any], action: str = "updated", **kwargs):
    """Convenience function to publish lead update."""
    publisher = get_event_publisher()
    await publisher.publish_lead_update(lead_id, lead_data, action, **kwargs)


async def publish_conversation_update(conversation_id: str, lead_id: str, stage: str, **kwargs):
    """Convenience function to publish conversation update."""
    publisher = get_event_publisher()
    await publisher.publish_conversation_update(conversation_id, lead_id, stage, **kwargs)


async def publish_commission_update(deal_id: str, commission_amount: float, pipeline_status: str, **kwargs):
    """Convenience function to publish commission update."""
    publisher = get_event_publisher()
    await publisher.publish_commission_update(deal_id, commission_amount, pipeline_status, **kwargs)


async def publish_system_alert(alert_type: str, message: str, severity: str = "info", **kwargs):
    """Convenience function to publish system alert."""
    publisher = get_event_publisher()
    await publisher.publish_system_alert(alert_type, message, severity, **kwargs)


async def publish_performance_update(metric_name: str, metric_value: float, **kwargs):
    """Convenience function to publish performance update."""
    publisher = get_event_publisher()
    await publisher.publish_performance_update(metric_name, metric_value, **kwargs)


async def publish_dashboard_refresh(component: str, data: Dict[str, Any], **kwargs):
    """Convenience function to publish dashboard refresh."""
    publisher = get_event_publisher()
    await publisher.publish_dashboard_refresh(component, data, **kwargs)


async def publish_property_alert(
    alert_id: str,
    lead_id: str,
    property_id: str,
    match_score: float,
    alert_type: str,
    property_data: Dict[str, Any],
    **kwargs,
):
    """Convenience function to publish property alert."""
    publisher = get_event_publisher()
    await publisher.publish_property_alert(
        alert_id, lead_id, property_id, match_score, alert_type, property_data, **kwargs
    )


# Jorge Bot Ecosystem Convenience Functions


async def publish_bot_status_update(bot_type: str, contact_id: str, status: str, **kwargs):
    """Convenience function to publish bot status update."""
    publisher = get_event_publisher()
    await publisher.publish_bot_status_update(bot_type, contact_id, status, **kwargs)


async def publish_jorge_qualification_progress(
    contact_id: str, current_question: int, questions_answered: int, seller_temperature: str, **kwargs
):
    """Convenience function to publish Jorge qualification progress."""
    publisher = get_event_publisher()
    await publisher.publish_jorge_qualification_progress(
        contact_id, current_question, questions_answered, seller_temperature, **kwargs
    )


async def publish_lead_bot_sequence_update(
    contact_id: str, sequence_day: int, action_type: str, success: bool, **kwargs
):
    """Convenience function to publish lead bot sequence update."""
    publisher = get_event_publisher()
    await publisher.publish_lead_bot_sequence_update(contact_id, sequence_day, action_type, success, **kwargs)


async def publish_intent_analysis_complete(
    contact_id: str, processing_time_ms: float, confidence_score: float, intent_category: str, **kwargs
):
    """Convenience function to publish intent analysis completion."""
    publisher = get_event_publisher()
    await publisher.publish_intent_analysis_complete(
        contact_id, processing_time_ms, confidence_score, intent_category, **kwargs
    )


async def publish_bot_handoff_request(
    handoff_id: str,
    from_bot: str,
    to_bot: str,
    contact_id: str,
    handoff_reason: str,
    context_transfer: Dict[str, Any],
    **kwargs,
):
    """Convenience function to publish bot handoff request."""
    publisher = get_event_publisher()
    await publisher.publish_bot_handoff_request(
        handoff_id, from_bot, to_bot, contact_id, handoff_reason, context_transfer, **kwargs
    )


async def publish_system_health_update(component: str, status: str, response_time_ms: float, **kwargs):
    """Convenience function to publish system health update."""
    publisher = get_event_publisher()
    await publisher.publish_system_health_update(component, status, response_time_ms, **kwargs)


async def publish_seller_bot_message_processed(
    contact_id: str,
    message_content: str,
    bot_response: str,
    seller_temperature: str,
    processing_time_ms: float,
    questions_answered: int,
    qualification_complete: bool,
    **kwargs,
):
    """Convenience function to publish seller bot message processed."""
    publisher = get_event_publisher()
    await publisher.publish_seller_bot_message_processed(
        contact_id,
        message_content,
        bot_response,
        seller_temperature,
        processing_time_ms,
        questions_answered,
        qualification_complete,
        **kwargs,
    )


# AI Concierge Convenience Functions


async def publish_proactive_insight(
    insight_id: str,
    contact_id: str,
    insight_type: str,
    confidence_score: float,
    title: str,
    description: str,
    suggested_actions: List[str],
    **kwargs,
):
    """Convenience function to publish proactive insight."""
    publisher = get_event_publisher()
    await publisher.publish_proactive_insight(
        insight_id, contact_id, insight_type, confidence_score, title, description, suggested_actions, **kwargs
    )


async def publish_strategy_recommendation(
    recommendation_id: str,
    contact_id: str,
    strategy_type: str,
    recommendation_text: str,
    reasoning: str,
    confidence_score: float,
    expected_impact: str,
    implementation_steps: List[str],
    **kwargs,
):
    """Convenience function to publish strategy recommendation."""
    publisher = get_event_publisher()
    await publisher.publish_strategy_recommendation(
        recommendation_id,
        contact_id,
        strategy_type,
        recommendation_text,
        reasoning,
        confidence_score,
        expected_impact,
        implementation_steps,
        **kwargs,
    )


async def publish_coaching_opportunity(
    opportunity_id: str,
    contact_id: str,
    coaching_area: str,
    opportunity_description: str,
    suggested_approach: str,
    learning_objectives: List[str],
    difficulty_level: str,
    estimated_time_minutes: int,
    **kwargs,
):
    """Convenience function to publish coaching opportunity."""
    publisher = get_event_publisher()
    await publisher.publish_coaching_opportunity(
        opportunity_id,
        contact_id,
        coaching_area,
        opportunity_description,
        suggested_approach,
        learning_objectives,
        difficulty_level,
        estimated_time_minutes,
        **kwargs,
    )


async def publish_ai_concierge_status_update(
    concierge_id: str, status: str, active_insights: int, monitoring_contacts: int, processing_time_ms: float, **kwargs
):
    """Convenience function to publish AI Concierge status update."""
    publisher = get_event_publisher()
    await publisher.publish_ai_concierge_status_update(
        concierge_id, status, active_insights, monitoring_contacts, processing_time_ms, **kwargs
    )


# ============================================================================
# Phase 2.1: Behavioral Prediction Convenience Functions
# ============================================================================


async def publish_behavioral_prediction_complete(
    lead_id: str,
    location_id: str,
    behavior_category: str,
    churn_risk_score: float,
    engagement_score: float,
    next_actions: List[Dict[str, Any]],
    prediction_latency_ms: float,
    **kwargs,
):
    """Convenience function to publish behavioral prediction completion."""
    publisher = get_event_publisher()
    await publisher.publish_behavioral_prediction_complete(
        lead_id,
        location_id,
        behavior_category,
        churn_risk_score,
        engagement_score,
        next_actions,
        prediction_latency_ms,
        **kwargs,
    )


async def publish_churn_risk_alert(
    lead_id: str,
    location_id: str,
    churn_risk_score: float,
    risk_factors: List[str],
    prevention_strategies: List[str],
    urgency: str = "high",
    **kwargs,
):
    """Convenience function to publish churn risk alert."""
    publisher = get_event_publisher()
    await publisher.publish_churn_risk_alert(
        lead_id, location_id, churn_risk_score, risk_factors, prevention_strategies, urgency, **kwargs
    )


async def publish_behavior_category_change(
    lead_id: str,
    location_id: str,
    previous_category: str,
    new_category: str,
    change_reason: str,
    confidence: float,
    **kwargs,
):
    """Convenience function to publish behavior category change."""
    publisher = get_event_publisher()
    await publisher.publish_behavior_category_change(
        lead_id, location_id, previous_category, new_category, change_reason, confidence, **kwargs
    )


async def publish_engagement_trend_change(
    lead_id: str,
    location_id: str,
    trend_direction: str,
    velocity: float,
    current_score: float,
    projected_score: float,
    time_window_hours: int,
    **kwargs,
):
    """Convenience function to publish engagement trend change."""
    publisher = get_event_publisher()
    await publisher.publish_engagement_trend_change(
        lead_id, location_id, trend_direction, velocity, current_score, projected_score, time_window_hours, **kwargs
    )


async def publish_optimal_contact_window(
    lead_id: str,
    location_id: str,
    contact_window: Dict[str, Any],
    contact_channel: str,
    probability_success: float,
    **kwargs,
):
    """Convenience function to publish optimal contact window."""
    publisher = get_event_publisher()
    await publisher.publish_optimal_contact_window(
        lead_id, location_id, contact_window, contact_channel, probability_success, **kwargs
    )


async def publish_behavioral_feedback_recorded(
    lead_id: str,
    location_id: str,
    feedback_type: str,
    prediction_accuracy: float,
    model_version: str = "v1.0",
    **kwargs,
):
    """Convenience function to publish behavioral feedback recording."""
    publisher = get_event_publisher()
    await publisher.publish_behavioral_feedback_recorded(
        lead_id, location_id, feedback_type, prediction_accuracy, model_version, **kwargs
    )


# ============================================================================
# Phase 2 Intelligence Layer Convenience Functions
# ============================================================================


async def publish_property_match_generated(
    lead_id: str,
    location_id: str,
    property_id: str,
    match_score: float,
    behavioral_fit: float,
    engagement_prediction: float,
    rank: int,
    presentation_strategy: str,
    reasoning: str,
    **kwargs,
):
    """Convenience function to publish property match generation."""
    publisher = get_event_publisher()
    await publisher.publish_property_match_generated(
        lead_id,
        location_id,
        property_id,
        match_score,
        behavioral_fit,
        engagement_prediction,
        rank,
        presentation_strategy,
        reasoning,
        **kwargs,
    )


async def publish_property_inventory_update(
    location_id: str,
    property_ids: List[str],
    update_type: str,
    affected_leads: List[str],
    inventory_change: str,
    **kwargs,
):
    """Convenience function to publish property inventory update."""
    publisher = get_event_publisher()
    await publisher.publish_property_inventory_update(
        location_id, property_ids, update_type, affected_leads, inventory_change, **kwargs
    )


async def publish_behavioral_match_improvement(
    lead_id: str,
    location_id: str,
    improvement_type: str,
    old_score: float,
    new_score: float,
    behavioral_factors: Dict[str, Any],
    recommendations: List[str],
    **kwargs,
):
    """Convenience function to publish behavioral match improvement."""
    publisher = get_event_publisher()
    await publisher.publish_behavioral_match_improvement(
        lead_id, location_id, improvement_type, old_score, new_score, behavioral_factors, recommendations, **kwargs
    )


async def publish_objection_detected(
    lead_id: str,
    location_id: str,
    objection_type: str,
    severity: str,
    confidence: float,
    context: str,
    suggested_responses: List[str],
    **kwargs,
):
    """Convenience function to publish objection detection."""
    publisher = get_event_publisher()
    await publisher.publish_objection_detected(
        lead_id, location_id, objection_type, severity, confidence, context, suggested_responses, **kwargs
    )


async def publish_sentiment_warning(
    lead_id: str,
    location_id: str,
    current_sentiment: float,
    trend: str,
    risk_level: str,
    recommendations: List[str],
    **kwargs,
):
    """Convenience function to publish sentiment warning."""
    publisher = get_event_publisher()
    await publisher.publish_sentiment_warning(
        lead_id, location_id, current_sentiment, trend, risk_level, recommendations, **kwargs
    )


async def publish_conversation_insight_generated(
    lead_id: str,
    location_id: str,
    insight_type: str,
    insight_summary: str,
    confidence: float,
    action_items: List[str],
    processing_time_ms: float,
    **kwargs,
):
    """Convenience function to publish conversation insight generation."""
    publisher = get_event_publisher()
    await publisher.publish_conversation_insight_generated(
        lead_id, location_id, insight_type, insight_summary, confidence, action_items, processing_time_ms, **kwargs
    )


async def publish_preference_learning_complete(
    client_id: str,
    location_id: str,
    learning_source: str,
    signals_processed: int,
    learning_latency_ms: float,
    preferences_updated: List[str],
    profile_completeness: float,
    **kwargs,
):
    """Convenience function to publish preference learning completion."""
    publisher = get_event_publisher()
    await publisher.publish_preference_learning_complete(
        client_id,
        location_id,
        learning_source,
        signals_processed,
        learning_latency_ms,
        preferences_updated,
        profile_completeness,
        **kwargs,
    )


async def publish_preference_drift_detected(
    client_id: str,
    location_id: str,
    preference_name: str,
    drift_magnitude: float,
    old_value: Any,
    new_value: Any,
    drift_direction: str,
    confidence: float,
    **kwargs,
):
    """Convenience function to publish preference drift detection."""
    publisher = get_event_publisher()
    await publisher.publish_preference_drift_detected(
        client_id,
        location_id,
        preference_name,
        drift_magnitude,
        old_value,
        new_value,
        drift_direction,
        confidence,
        **kwargs,
    )


async def publish_preference_profile_updated(
    client_id: str,
    location_id: str,
    update_type: str,
    updated_preferences: List[str],
    profile_completeness: float,
    confidence_improvement: float,
    **kwargs,
):
    """Convenience function to publish preference profile update."""
    publisher = get_event_publisher()
    await publisher.publish_preference_profile_updated(
        client_id, location_id, update_type, updated_preferences, profile_completeness, confidence_improvement, **kwargs
    )
