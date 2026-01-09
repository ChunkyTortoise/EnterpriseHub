"""
Event Collection Layer

Provides convenient methods for collecting behavioral events from
different parts of the application.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import logging

from ..interfaces import BehavioralEvent, EventType, IBehaviorTracker

logger = logging.getLogger(__name__)


class EventCollector:
    """
    High-level interface for collecting behavioral events.

    Provides convenient, domain-specific methods for tracking various
    types of user interactions and system events.

    Usage:
        collector = EventCollector(tracker)
        await collector.track_property_view(lead_id="123", property_id="prop-001")
    """

    def __init__(self, tracker: IBehaviorTracker):
        self.tracker = tracker
        self.stats = {
            "events_collected": 0,
            "collection_errors": 0,
            "events_by_type": {}
        }

    # Property interaction tracking
    async def track_property_view(
        self,
        lead_id: str,
        property_id: str,
        session_id: Optional[str] = None,
        device_type: Optional[str] = None,
        view_duration_seconds: Optional[float] = None,
        page_source: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> str:
        """Track property view event with detailed context"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.PROPERTY_VIEW,
            timestamp=datetime.now(),
            lead_id=lead_id,
            property_id=property_id,
            session_id=session_id,
            device_type=device_type,
            event_data={
                "view_duration_seconds": view_duration_seconds,
                "page_source": page_source,
                "referrer": referrer
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.PROPERTY_VIEW, success)

        return event_id

    async def track_property_swipe(
        self,
        lead_id: str,
        property_id: str,
        swipe_direction: str,  # "left" (dislike) or "right" (like)
        session_id: Optional[str] = None,
        swipe_velocity: Optional[float] = None,
        property_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track property swipe (Tinder-style interaction)"""

        event_id = self._generate_event_id()
        liked = swipe_direction.lower() == "right"

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.PROPERTY_SWIPE,
            timestamp=datetime.now(),
            lead_id=lead_id,
            property_id=property_id,
            session_id=session_id,
            event_data={
                "swipe_direction": swipe_direction,
                "liked": liked,
                "swipe_velocity": swipe_velocity,
                "property_details": property_details
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.PROPERTY_SWIPE, success)

        return event_id

    async def track_property_save(
        self,
        lead_id: str,
        property_id: str,
        save_type: str = "favorite",  # "favorite", "watchlist", "compare"
        session_id: Optional[str] = None
    ) -> str:
        """Track property save/favorite action"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.PROPERTY_SAVE,
            timestamp=datetime.now(),
            lead_id=lead_id,
            property_id=property_id,
            session_id=session_id,
            event_data={
                "save_type": save_type
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.PROPERTY_SAVE, success)

        return event_id

    async def track_property_share(
        self,
        lead_id: str,
        property_id: str,
        share_method: str,  # "email", "sms", "social", "link"
        recipient_info: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Track property sharing action"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.PROPERTY_SHARE,
            timestamp=datetime.now(),
            lead_id=lead_id,
            property_id=property_id,
            session_id=session_id,
            event_data={
                "share_method": share_method,
                "recipient_info": recipient_info
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.PROPERTY_SHARE, success)

        return event_id

    # Booking and tour tracking
    async def track_booking_request(
        self,
        lead_id: str,
        agent_id: str,
        property_id: str,
        requested_time: datetime,
        booking_type: str = "tour",  # "tour", "meeting", "call"
        urgency: str = "medium",
        session_id: Optional[str] = None,
        additional_notes: Optional[str] = None
    ) -> str:
        """Track booking request - returns event_id for outcome recording"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.BOOKING_REQUEST,
            timestamp=datetime.now(),
            lead_id=lead_id,
            agent_id=agent_id,
            property_id=property_id,
            session_id=session_id,
            event_data={
                "requested_time": requested_time.isoformat(),
                "booking_type": booking_type,
                "urgency": urgency,
                "additional_notes": additional_notes
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.BOOKING_REQUEST, success)

        return event_id

    async def track_booking_completed(
        self,
        booking_request_event_id: str,
        lead_id: str,
        agent_id: str,
        property_id: str,
        completed: bool,
        completion_time: Optional[datetime] = None,
        completion_rating: Optional[int] = None,
        feedback: Optional[str] = None
    ) -> str:
        """Track booking completion (outcome)"""

        # Record outcome on original booking request
        await self.tracker.record_outcome(
            event_id=booking_request_event_id,
            outcome="completed" if completed else "cancelled",
            outcome_value=1.0 if completed else 0.0
        )

        # Create completion event
        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.BOOKING_COMPLETED,
            timestamp=datetime.now(),
            lead_id=lead_id,
            agent_id=agent_id,
            property_id=property_id,
            event_data={
                "completed": completed,
                "completion_time": completion_time.isoformat() if completion_time else None,
                "completion_rating": completion_rating,
                "feedback": feedback,
                "original_request_event_id": booking_request_event_id
            },
            outcome="completed" if completed else "cancelled",
            outcome_value=1.0 if completed else 0.0
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.BOOKING_COMPLETED, success)

        return event_id

    async def track_tour_scheduled(
        self,
        lead_id: str,
        agent_id: str,
        property_id: str,
        tour_time: datetime,
        tour_type: str = "in_person",  # "in_person", "virtual"
        session_id: Optional[str] = None
    ) -> str:
        """Track tour scheduling"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.TOUR_SCHEDULED,
            timestamp=datetime.now(),
            lead_id=lead_id,
            agent_id=agent_id,
            property_id=property_id,
            session_id=session_id,
            event_data={
                "tour_time": tour_time.isoformat(),
                "tour_type": tour_type
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.TOUR_SCHEDULED, success)

        return event_id

    async def track_tour_completed(
        self,
        lead_id: str,
        agent_id: str,
        property_id: str,
        completed: bool,
        duration_minutes: Optional[int] = None,
        lead_interest_level: Optional[int] = None,  # 1-10 scale
        notes: Optional[str] = None
    ) -> str:
        """Track tour completion"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.TOUR_COMPLETED,
            timestamp=datetime.now(),
            lead_id=lead_id,
            agent_id=agent_id,
            property_id=property_id,
            event_data={
                "completed": completed,
                "duration_minutes": duration_minutes,
                "lead_interest_level": lead_interest_level,
                "notes": notes
            },
            outcome="completed" if completed else "cancelled",
            outcome_value=lead_interest_level / 10.0 if lead_interest_level else (1.0 if completed else 0.0)
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.TOUR_COMPLETED, success)

        return event_id

    # Agent and lead interaction tracking
    async def track_agent_action(
        self,
        agent_id: str,
        lead_id: Optional[str],
        action_type: str,
        action_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """Track agent action for performance learning"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.AGENT_ACTION,
            timestamp=datetime.now(),
            agent_id=agent_id,
            lead_id=lead_id,
            session_id=session_id,
            event_data={
                "action_type": action_type,
                **action_data
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.AGENT_ACTION, success)

        return event_id

    async def track_lead_interaction(
        self,
        lead_id: str,
        interaction_type: str,
        agent_id: Optional[str] = None,
        interaction_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Track general lead interaction"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.LEAD_INTERACTION,
            timestamp=datetime.now(),
            lead_id=lead_id,
            agent_id=agent_id,
            session_id=session_id,
            event_data={
                "interaction_type": interaction_type,
                **(interaction_data or {})
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.LEAD_INTERACTION, success)

        return event_id

    # Search and filter tracking
    async def track_search_query(
        self,
        lead_id: str,
        search_query: str,
        search_filters: Optional[Dict[str, Any]] = None,
        results_count: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Track search query and results"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.SEARCH_QUERY,
            timestamp=datetime.now(),
            lead_id=lead_id,
            session_id=session_id,
            event_data={
                "search_query": search_query,
                "search_filters": search_filters,
                "results_count": results_count
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.SEARCH_QUERY, success)

        return event_id

    async def track_filter_applied(
        self,
        lead_id: str,
        filter_type: str,
        filter_value: Any,
        previous_results_count: Optional[int] = None,
        new_results_count: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Track filter application"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.FILTER_APPLIED,
            timestamp=datetime.now(),
            lead_id=lead_id,
            session_id=session_id,
            event_data={
                "filter_type": filter_type,
                "filter_value": filter_value,
                "previous_results_count": previous_results_count,
                "new_results_count": new_results_count
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.FILTER_APPLIED, success)

        return event_id

    # Communication tracking
    async def track_email_opened(
        self,
        lead_id: str,
        email_campaign_id: Optional[str] = None,
        email_subject: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> str:
        """Track email open"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.EMAIL_OPENED,
            timestamp=datetime.now(),
            lead_id=lead_id,
            agent_id=agent_id,
            campaign_id=email_campaign_id,
            event_data={
                "email_subject": email_subject
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.EMAIL_OPENED, success)

        return event_id

    async def track_email_clicked(
        self,
        lead_id: str,
        email_campaign_id: Optional[str] = None,
        link_url: Optional[str] = None,
        link_type: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> str:
        """Track email link click"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.EMAIL_CLICKED,
            timestamp=datetime.now(),
            lead_id=lead_id,
            agent_id=agent_id,
            campaign_id=email_campaign_id,
            event_data={
                "link_url": link_url,
                "link_type": link_type
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.EMAIL_CLICKED, success)

        return event_id

    # Session tracking
    async def track_session_start(
        self,
        lead_id: str,
        session_id: str,
        device_type: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> str:
        """Track session start"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.SESSION_START,
            timestamp=datetime.now(),
            lead_id=lead_id,
            session_id=session_id,
            device_type=device_type,
            event_data={
                "user_agent": user_agent,
                "referrer": referrer
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.SESSION_START, success)

        return event_id

    async def track_session_end(
        self,
        lead_id: str,
        session_id: str,
        session_duration_seconds: Optional[float] = None,
        total_page_views: Optional[int] = None,
        total_property_views: Optional[int] = None
    ) -> str:
        """Track session end"""

        event_id = self._generate_event_id()

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.SESSION_END,
            timestamp=datetime.now(),
            lead_id=lead_id,
            session_id=session_id,
            event_data={
                "session_duration_seconds": session_duration_seconds,
                "total_page_views": total_page_views,
                "total_property_views": total_property_views
            }
        )

        success = await self.tracker.track_event(event)
        self._update_stats(EventType.SESSION_END, success)

        return event_id

    # Batch tracking for efficiency
    async def track_events_batch(self, events_data: List[Dict[str, Any]]) -> List[str]:
        """Track multiple events in batch"""

        events = []
        event_ids = []

        for event_data in events_data:
            event_id = self._generate_event_id()
            event_ids.append(event_id)

            event = BehavioralEvent(
                event_id=event_id,
                event_type=EventType(event_data["event_type"]),
                timestamp=datetime.now(),
                lead_id=event_data.get("lead_id"),
                agent_id=event_data.get("agent_id"),
                property_id=event_data.get("property_id"),
                session_id=event_data.get("session_id"),
                device_type=event_data.get("device_type"),
                event_data=event_data.get("event_data", {})
            )
            events.append(event)

        successful_count = await self.tracker.track_events_batch(events)
        self.stats["events_collected"] += successful_count

        if successful_count < len(events):
            self.stats["collection_errors"] += len(events) - successful_count

        return event_ids[:successful_count]

    # Utility methods
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return f"evt_{uuid.uuid4().hex[:12]}"

    def _update_stats(self, event_type: EventType, success: bool):
        """Update collection statistics"""
        if success:
            self.stats["events_collected"] += 1
            event_type_key = event_type.value
            self.stats["events_by_type"][event_type_key] = \
                self.stats["events_by_type"].get(event_type_key, 0) + 1
        else:
            self.stats["collection_errors"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return {
            **self.stats,
            "success_rate": self._calculate_success_rate()
        }

    def _calculate_success_rate(self) -> float:
        """Calculate collection success rate"""
        total = self.stats["events_collected"] + self.stats["collection_errors"]
        if total == 0:
            return 100.0
        return (self.stats["events_collected"] / total) * 100.0


class PropertyInteractionCollector:
    """
    Specialized collector for property-related interactions.

    Provides even more specific methods for property interaction tracking
    with built-in property context enrichment.
    """

    def __init__(self, event_collector: EventCollector, property_service=None):
        self.collector = event_collector
        self.property_service = property_service

    async def track_property_card_interaction(
        self,
        lead_id: str,
        property_id: str,
        interaction_type: str,  # "hover", "click", "expand", "collapse"
        session_id: Optional[str] = None,
        card_position: Optional[int] = None,
        total_cards: Optional[int] = None
    ) -> str:
        """Track property card interaction"""

        # Get property details if service available
        property_details = None
        if self.property_service:
            try:
                property_details = await self.property_service.get_property_by_id(property_id)
            except Exception as e:
                logger.warning(f"Failed to get property details for {property_id}: {e}")

        # Use the basic track_property_view method but manually create event with additional data
        from ..interfaces import BehavioralEvent, EventType
        import uuid

        event_id = f"evt_{uuid.uuid4().hex[:12]}"

        event = BehavioralEvent(
            event_id=event_id,
            event_type=EventType.PROPERTY_VIEW,
            timestamp=datetime.now(),
            lead_id=lead_id,
            property_id=property_id,
            session_id=session_id,
            event_data={
                "interaction_type": interaction_type,
                "card_position": card_position,
                "total_cards": total_cards,
                "property_details": property_details,
                "page_source": "property_card"
            }
        )

        success = await self.collector.tracker.track_event(event)
        self.collector._update_stats(EventType.PROPERTY_VIEW, success)

        return event_id

    async def track_property_comparison(
        self,
        lead_id: str,
        property_ids: List[str],
        session_id: Optional[str] = None
    ) -> str:
        """Track property comparison activity"""

        # Track as general interaction with special type
        return await self.collector.track_lead_interaction(
            lead_id=lead_id,
            interaction_type="property_comparison",
            session_id=session_id,
            interaction_data={
                "compared_properties": property_ids,
                "comparison_count": len(property_ids)
            }
        )

    async def track_property_list_scroll(
        self,
        lead_id: str,
        properties_viewed: List[str],
        scroll_depth_percent: float,
        session_id: Optional[str] = None
    ) -> str:
        """Track property list scrolling behavior"""

        return await self.collector.track_lead_interaction(
            lead_id=lead_id,
            interaction_type="property_list_scroll",
            session_id=session_id,
            interaction_data={
                "properties_viewed": properties_viewed,
                "scroll_depth_percent": scroll_depth_percent,
                "properties_in_view": len(properties_viewed)
            }
        )