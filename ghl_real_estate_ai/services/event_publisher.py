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
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import json

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.websocket_server import get_websocket_manager, RealTimeEvent, EventType
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.auth_service import UserRole

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
        
        # Event batching configuration
        self.batch_interval = 0.5  # seconds
        self.max_batch_size = 10
        self._event_batch = []
        self._batch_timer = None
        
        # Performance tracking
        self._processing_times = []
        
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
        location_id: Optional[str] = None
    ):
        """
        Publish lead update event.
        
        Args:
            lead_id: Lead identifier
            lead_data: Lead data that was updated
            action: Type of action (created, updated, qualified, etc.)
            user_id: User who triggered the update (optional)
            location_id: Location/tenant ID (optional)
        """
        event = RealTimeEvent(
            event_type=EventType.LEAD_UPDATE,
            data={
                "lead_id": lead_id,
                "action": action,
                "lead_data": lead_data,
                "updated_fields": list(lead_data.keys()),
                "summary": f"Lead {action}: {lead_data.get('name', 'Unknown')}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if action in ["created", "qualified", "hot"] else "normal"
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
        location_id: Optional[str] = None
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
        """
        event = RealTimeEvent(
            event_type=EventType.CONVERSATION_UPDATE,
            data={
                "conversation_id": conversation_id,
                "lead_id": lead_id,
                "stage": stage,
                "message_preview": message[:100] + "..." if message and len(message) > 100 else message,
                "stage_progression": self._get_stage_progression(stage),
                "summary": f"Conversation moved to {stage}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if stage in ["Q4", "hot", "ready"] else "normal"
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
            "closing": {"progress": 100, "next": None, "description": "Deal Closing"}
        }
        
        return stage_map.get(stage, {"progress": 0, "next": None, "description": "Unknown"})

    async def publish_commission_update(
        self,
        deal_id: str,
        commission_amount: float,
        pipeline_status: str,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None
    ):
        """
        Publish commission pipeline update event.
        
        Args:
            deal_id: Deal identifier
            commission_amount: Commission amount
            pipeline_status: Pipeline status (potential, confirmed, paid)
            user_id: User associated with deal (optional)
            location_id: Location/tenant ID (optional)
        """
        event = RealTimeEvent(
            event_type=EventType.COMMISSION_UPDATE,
            data={
                "deal_id": deal_id,
                "commission_amount": commission_amount,
                "pipeline_status": pipeline_status,
                "formatted_amount": f"${commission_amount:,.2f}",
                "impact": "positive" if commission_amount > 0 else "neutral",
                "summary": f"Commission {pipeline_status}: ${commission_amount:,.2f}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if commission_amount > 10000 else "normal"
        )
        
        await self._publish_event(event)
        logger.info(f"Published commission update: {deal_id} - ${commission_amount:,.2f} ({pipeline_status})")

    async def publish_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "info",
        details: Optional[Dict[str, Any]] = None,
        target_roles: Optional[List[UserRole]] = None
    ):
        """
        Publish system alert event.
        
        Args:
            alert_type: Type of alert (performance, error, maintenance, etc.)
            message: Alert message
            severity: Alert severity (info, warning, error, critical)
            details: Additional alert details (optional)
            target_roles: Specific roles to target (optional)
        """
        event = RealTimeEvent(
            event_type=EventType.SYSTEM_ALERT,
            data={
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "details": details or {},
                "action_required": severity in ["error", "critical"],
                "summary": f"{severity.upper()}: {message}"
            },
            timestamp=datetime.now(timezone.utc),
            priority="critical" if severity == "critical" else "high" if severity == "error" else "normal"
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
        user_id: Optional[int] = None
    ):
        """
        Publish performance metric update event.
        
        Args:
            metric_name: Name of the metric
            metric_value: Current metric value
            metric_unit: Unit of measurement (optional)
            comparison: Comparison data (previous value, trend, etc.) (optional)
            user_id: User associated with metric (optional)
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
                "summary": f"{metric_name}: {metric_value:.2f}{metric_unit}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            priority="low"
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
        location_id: Optional[str] = None
    ):
        """
        Publish dashboard component refresh event.
        
        Args:
            component: Dashboard component to refresh
            data: Updated component data
            user_id: User requesting refresh (optional)
            location_id: Location/tenant ID (optional)
        """
        event = RealTimeEvent(
            event_type=EventType.DASHBOARD_REFRESH,
            data={
                "component": component,
                "data": data,
                "cache_key": f"dashboard:{component}:{location_id or 'global'}",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "summary": f"Dashboard component refreshed: {component}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="normal"
        )
        
        await self._publish_event(event)
        logger.debug(f"Published dashboard refresh: {component}")

    async def publish_user_activity(
        self,
        action: str,
        user_id: int,
        details: Optional[Dict[str, Any]] = None,
        target_roles: Optional[List[UserRole]] = None
    ):
        """
        Publish user activity event.
        
        Args:
            action: Activity action (login, logout, view_dashboard, etc.)
            user_id: User ID performing action
            details: Additional activity details (optional)
            target_roles: Specific roles to notify (optional, defaults to admin only)
        """
        event = RealTimeEvent(
            event_type=EventType.USER_ACTIVITY,
            data={
                "action": action,
                "user_id": user_id,
                "details": details or {},
                "session_info": await self._get_session_info(user_id),
                "summary": f"User activity: {action}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            priority="low"
        )
        
        # Default to admin-only notifications for user activity
        target_roles = target_roles or [UserRole.ADMIN]
        await self.websocket_manager.broadcast_event(event, target_roles=set(target_roles))
        logger.debug(f"Published user activity: {action} (user {user_id})")

    async def _get_session_info(self, user_id: int) -> Dict[str, Any]:
        """Get session information for user activity events."""
        # This could be enhanced to include more session details
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id
        }

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
        location_id: Optional[str] = None
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
        """
        # Extract key property details for quick access
        property_address = property_data.get('address', 'Unknown Address')
        property_price = property_data.get('price', 0)
        property_bedrooms = property_data.get('bedrooms', 0)
        property_bathrooms = property_data.get('bathrooms', 0)
        property_sqft = property_data.get('sqft', 0)

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
                    "formatted_sqft": f"{property_sqft:,} sq ft" if property_sqft else "Size not listed"
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
                "notification_text": f"Found a {match_score:.0f}% match! {property_address} - ${property_price:,.0f}" if property_price else f"Found a {match_score:.0f}% match! {property_address}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority=priority
        )

        await self._publish_event(event)
        logger.info(f"Published property alert: {alert_type} for lead {lead_id} - {property_address} ({match_score:.1f}% match)")

    # Jorge Bot Ecosystem Event Publishers

    async def publish_bot_status_update(
        self,
        bot_type: str,
        contact_id: str,
        status: str,
        current_step: Optional[str] = None,
        processing_time_ms: Optional[float] = None,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None
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
                "summary": f"{bot_type.replace('-', ' ').title()} bot {status}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if status == "error" else "normal"
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
        location_id: Optional[str] = None
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
                "summary": f"Jorge qualification {progress_percentage:.0f}% complete - {seller_temperature} seller"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if seller_temperature == "hot" else "normal"
        )

        await self._publish_event(event)
        logger.info(f"Published Jorge qualification progress: {progress_percentage:.0f}% ({seller_temperature} - contact: {contact_id})")

    async def publish_lead_bot_sequence_update(
        self,
        contact_id: str,
        sequence_day: int,
        action_type: str,
        success: bool,
        next_action_date: Optional[str] = None,
        message_sent: Optional[str] = None,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None
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
        """
        event = RealTimeEvent(
            event_type=EventType.LEAD_BOT_SEQUENCE_UPDATE,
            data={
                "contact_id": contact_id,
                "sequence_day": sequence_day,
                "action_type": action_type,
                "success": success,
                "next_action_date": next_action_date,
                "message_preview": message_sent[:100] + "..." if message_sent and len(message_sent) > 100 else message_sent,
                "sequence_progress": self._calculate_sequence_progress(sequence_day),
                "summary": f"Day {sequence_day} sequence {action_type} - {'Success' if success else 'Failed'}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if not success else "normal"
        )

        await self._publish_event(event)
        logger.info(f"Published lead bot sequence: Day {sequence_day} {action_type} ({'success' if success else 'failed'} - contact: {contact_id})")

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
        location_id: Optional[str] = None
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
                "performance_tier": "excellent" if processing_time_ms < 50 else "good" if processing_time_ms < 100 else "acceptable",
                "summary": f"Intent analysis complete - {intent_category} ({confidence_score:.1%} confidence)"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="normal"
        )

        await self._publish_event(event)
        logger.info(f"Published intent analysis: {intent_category} ({confidence_score:.1%} - {processing_time_ms:.1f}ms - contact: {contact_id})")

    async def publish_bot_handoff_request(
        self,
        handoff_id: str,
        from_bot: str,
        to_bot: str,
        contact_id: str,
        handoff_reason: str,
        context_transfer: Dict[str, Any],
        urgency: str = "normal",
        user_id: Optional[int] = None,
        location_id: Optional[str] = None
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
        """
        event = RealTimeEvent(
            event_type=EventType.BOT_HANDOFF_REQUEST,
            data={
                "handoff_id": handoff_id,
                "from_bot": from_bot,
                "to_bot": to_bot,
                "contact_id": contact_id,
                "handoff_reason": handoff_reason,
                "context_summary": {
                    "conversation_length": len(context_transfer.get("conversation_history", [])),
                    "qualification_scores": context_transfer.get("qualification_scores", {}),
                    "lead_temperature": context_transfer.get("lead_temperature", "unknown")
                },
                "urgency": urgency,
                "context_size_kb": round(len(str(context_transfer)) / 1024, 2),
                "summary": f"Handoff request: {from_bot} → {to_bot} ({handoff_reason})"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if urgency == "immediate" else "normal"
        )

        await self._publish_event(event)
        logger.info(f"Published bot handoff request: {from_bot} → {to_bot} (ID: {handoff_id}, contact: {contact_id})")

    async def publish_system_health_update(
        self,
        component: str,
        status: str,
        response_time_ms: float,
        error_message: Optional[str] = None,
        additional_metrics: Optional[Dict[str, Any]] = None,
        location_id: Optional[str] = None
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
                "summary": f"{component.replace('_', ' ').title()}: {status} ({response_time_ms:.0f}ms)"
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            priority="critical" if status == "down" else "high" if status == "degraded" else "low"
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
        location_id: Optional[str] = None
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
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if buyer_temperature in ["hot", "warm"] else "normal"
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
        location_id: Optional[str] = None
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
                "progress_timestamp": datetime.now(timezone.utc).isoformat()
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if qualification_status == "qualified" else "normal"
        )

        await self._publish_event(event)
        logger.info(f"Published buyer qualification progress: {qualification_status} ({current_step} - contact: {contact_id})")

    async def publish_buyer_qualification_complete(
        self,
        contact_id: str,
        qualification_status: str,
        final_score: float,
        properties_matched: int,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None
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
                "next_action": "property_search" if qualification_status == "qualified" else "nurture"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if qualification_status == "qualified" else "normal"
        )

        await self._publish_event(event)
        logger.info(f"Published buyer qualification complete: {qualification_status} (score: {final_score} - contact: {contact_id})")

    async def publish_buyer_follow_up_scheduled(
        self,
        contact_id: str,
        action_type: str,
        scheduled_hours: int,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None
    ):
        """Publish buyer follow-up scheduling."""
        event = RealTimeEvent(
            event_type=EventType.BUYER_FOLLOW_UP_SCHEDULED,
            data={
                "contact_id": contact_id,
                "action_type": action_type,
                "scheduled_hours": scheduled_hours,
                "scheduled_for": (datetime.now(timezone.utc) + timedelta(hours=scheduled_hours)).isoformat(),
                "schedule_timestamp": datetime.now(timezone.utc).isoformat()
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="normal"
        )

        await self._publish_event(event)
        logger.info(f"Published buyer follow-up scheduled: {action_type} in {scheduled_hours}h (contact: {contact_id})")

    async def publish_property_match_update(
        self,
        contact_id: str,
        properties_matched: int,
        match_criteria: Dict[str, Any],
        user_id: Optional[int] = None,
        location_id: Optional[str] = None
    ):
        """Publish property matching results."""
        event = RealTimeEvent(
            event_type=EventType.PROPERTY_MATCH_UPDATE,
            data={
                "contact_id": contact_id,
                "properties_matched": properties_matched,
                "match_criteria": match_criteria,
                "match_timestamp": datetime.now(timezone.utc).isoformat()
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if properties_matched > 0 else "normal"
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
        location_id: Optional[str] = None
    ):
        """Publish SMS compliance events for audit trail."""
        event = RealTimeEvent(
            event_type=EventType.SMS_COMPLIANCE,
            data={
                "phone_number_suffix": phone_number[-4:] if phone_number else "****",  # Only last 4 digits for privacy
                "compliance_event_type": event_type,
                "reason": reason,
                "additional_data": additional_data or {},
                "compliance_timestamp": datetime.now(timezone.utc).isoformat()
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            priority="critical"  # Compliance events are always critical
        )

        await self._publish_event(event)
        logger.info(f"Published SMS compliance event: {event_type} - {reason} (phone: ***{phone_number[-4:] if phone_number else '****'})")

    async def publish_sms_opt_out_processed(
        self,
        phone_number: str,
        opt_out_method: str,
        message_content: Optional[str] = None,
        location_id: Optional[str] = None
    ):
        """Publish SMS opt-out processing confirmation."""
        event = RealTimeEvent(
            event_type=EventType.SMS_OPT_OUT_PROCESSED,
            data={
                "phone_number_suffix": phone_number[-4:] if phone_number else "****",
                "opt_out_method": opt_out_method,
                "message_content": message_content[:100] + "..." if message_content and len(message_content) > 100 else message_content,
                "processed_timestamp": datetime.now(timezone.utc).isoformat()
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            priority="high"
        )

        await self._publish_event(event)
        logger.info(f"Published SMS opt-out processed: {opt_out_method} (phone: ***{phone_number[-4:] if phone_number else '****'})")

    async def publish_sms_frequency_limit_hit(
        self,
        phone_number: str,
        limit_type: str,
        current_count: int,
        limit_value: int,
        location_id: Optional[str] = None
    ):
        """Publish SMS frequency limit violations."""
        event = RealTimeEvent(
            event_type=EventType.SMS_FREQUENCY_LIMIT_HIT,
            data={
                "phone_number_suffix": phone_number[-4:] if phone_number else "****",
                "limit_type": limit_type,
                "current_count": current_count,
                "limit_value": limit_value,
                "limit_hit_timestamp": datetime.now(timezone.utc).isoformat()
            },
            timestamp=datetime.now(timezone.utc),
            location_id=location_id,
            priority="high"
        )

        await self._publish_event(event)
        logger.info(f"Published SMS frequency limit hit: {limit_type} {current_count}/{limit_value} (phone: ***{phone_number[-4:] if phone_number else '****'})")

    def _calculate_sequence_progress(self, sequence_day: int) -> Dict[str, Any]:
        """Calculate lead bot sequence progress information."""
        progress_map = {
            3: {"progress": 33, "next_day": 7, "description": "Day 3 Follow-up"},
            7: {"progress": 67, "next_day": 30, "description": "Day 7 Call"},
            30: {"progress": 100, "next_day": None, "description": "Day 30 Final Touch"}
        }

        return progress_map.get(sequence_day, {"progress": 0, "next_day": None, "description": "Unknown"})

    def _calculate_health_score(self, status: str, response_time_ms: float) -> float:
        """Calculate component health score based on status and response time."""
        status_scores = {
            "healthy": 1.0,
            "degraded": 0.6,
            "recovering": 0.4,
            "down": 0.0
        }

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
        Publish event with performance tracking and batching.
        
        Args:
            event: Event to publish
        """
        start_time = time.time()
        
        try:
            # Add to batch
            self._event_batch.append(event)
            
            # Check if batch should be processed immediately
            should_process_immediately = (
                len(self._event_batch) >= self.max_batch_size or
                event.priority == "critical" or
                (event.priority == "high" and len(self._event_batch) >= 3)
            )
            
            if should_process_immediately:
                await self._process_event_batch()
            else:
                # Schedule batch processing if not already scheduled
                if self._batch_timer is None:
                    self._batch_timer = asyncio.create_task(self._schedule_batch_processing())
            
            # Update metrics
            processing_time = (time.time() - start_time) * 1000  # ms
            self._processing_times.append(processing_time)
            
            # Keep only recent processing times (last 100)
            if len(self._processing_times) > 100:
                self._processing_times = self._processing_times[-100:]
                
            self.metrics.average_processing_time_ms = sum(self._processing_times) / len(self._processing_times)
            self.metrics.total_events_published += 1
            self.metrics.last_event_time = datetime.now(timezone.utc)
            
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
        
        logger.debug(f"Processed event batch: {len(batch)} events ({len(critical_events)} critical, {len(high_events)} high, {len(normal_events)} normal)")

    def _aggregate_similar_events(self, events: List[RealTimeEvent]) -> List[RealTimeEvent]:
        """
        Aggregate similar events to reduce WebSocket message volume.
        
        Args:
            events: List of events to potentially aggregate
            
        Returns:
            List of events (some potentially aggregated)
        """
        # For now, return events as-is
        # In the future, we could aggregate multiple dashboard_refresh events
        # for the same component, or multiple performance_updates for the same metric
        return events

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
                    **event_kwargs
                }
                
                # Create and publish event
                event = RealTimeEvent(
                    event_type=event_type,
                    data=event_data,
                    timestamp=datetime.now(timezone.utc),
                    priority="normal"
                )
                
                await self._publish_event(event)
                return result
                
            return wrapper
        return decorator

    def get_metrics(self) -> Dict[str, Any]:
        """Get event publishing metrics."""
        return {
            "total_events_published": self.metrics.total_events_published,
            "events_by_type": self.metrics.events_by_type,
            "last_event_time": self.metrics.last_event_time.isoformat() if self.metrics.last_event_time else None,
            "average_processing_time_ms": round(self.metrics.average_processing_time_ms, 3),
            "failed_publishes": self.metrics.failed_publishes,
            "batch_queue_size": len(self._event_batch),
            "websocket_metrics": self.websocket_manager.get_metrics()
        }

# Global event publisher instance
_event_publisher = None

def get_event_publisher() -> EventPublisher:
    """Get singleton event publisher instance."""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher

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

async def publish_property_alert(alert_id: str, lead_id: str, property_id: str, match_score: float,
                                alert_type: str, property_data: Dict[str, Any], **kwargs):
    """Convenience function to publish property alert."""
    publisher = get_event_publisher()
    await publisher.publish_property_alert(alert_id, lead_id, property_id, match_score,
                                         alert_type, property_data, **kwargs)

# Jorge Bot Ecosystem Convenience Functions

async def publish_bot_status_update(bot_type: str, contact_id: str, status: str, **kwargs):
    """Convenience function to publish bot status update."""
    publisher = get_event_publisher()
    await publisher.publish_bot_status_update(bot_type, contact_id, status, **kwargs)

async def publish_jorge_qualification_progress(contact_id: str, current_question: int,
                                             questions_answered: int, seller_temperature: str, **kwargs):
    """Convenience function to publish Jorge qualification progress."""
    publisher = get_event_publisher()
    await publisher.publish_jorge_qualification_progress(contact_id, current_question,
                                                       questions_answered, seller_temperature, **kwargs)

async def publish_lead_bot_sequence_update(contact_id: str, sequence_day: int,
                                         action_type: str, success: bool, **kwargs):
    """Convenience function to publish lead bot sequence update."""
    publisher = get_event_publisher()
    await publisher.publish_lead_bot_sequence_update(contact_id, sequence_day, action_type, success, **kwargs)

async def publish_intent_analysis_complete(contact_id: str, processing_time_ms: float,
                                         confidence_score: float, intent_category: str, **kwargs):
    """Convenience function to publish intent analysis completion."""
    publisher = get_event_publisher()
    await publisher.publish_intent_analysis_complete(contact_id, processing_time_ms,
                                                   confidence_score, intent_category, **kwargs)

async def publish_bot_handoff_request(handoff_id: str, from_bot: str, to_bot: str,
                                    contact_id: str, handoff_reason: str, context_transfer: Dict[str, Any], **kwargs):
    """Convenience function to publish bot handoff request."""
    publisher = get_event_publisher()
    await publisher.publish_bot_handoff_request(handoff_id, from_bot, to_bot, contact_id,
                                              handoff_reason, context_transfer, **kwargs)

async def publish_system_health_update(component: str, status: str, response_time_ms: float, **kwargs):
    """Convenience function to publish system health update."""
    publisher = get_event_publisher()
    await publisher.publish_system_health_update(component, status, response_time_ms, **kwargs)