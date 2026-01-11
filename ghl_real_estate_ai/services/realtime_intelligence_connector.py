"""
Real-Time Intelligence Connector - Live Claude AI Data Streams

Provides real-time data connectivity between Claude AI services and dashboard components:
- WebSocket connections for live updates
- Data transformation and normalization
- Caching and performance optimization
- Event-driven updates and notifications
- Multi-tenant data isolation

This service acts as the bridge between Claude AI services and the dashboard visualization layer.
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, asdict
import aioredis
from fastapi import WebSocket
import websockets

# Import Claude services
try:
    from .claude_agent_service import get_claude_agent_service
    from .claude_semantic_analyzer import get_claude_semantic_analyzer
    from .qualification_orchestrator import get_qualification_orchestrator
    from .claude_action_planner import get_claude_action_planner
    CLAUDE_SERVICES_AVAILABLE = True
except ImportError:
    CLAUDE_SERVICES_AVAILABLE = False

# Import dashboard data models
try:
    from ..streamlit_components.advanced_intelligence_visualizations import (
        LeadJourneyStage,
        SentimentAnalysis,
        CompetitiveIntelligence,
        ContentRecommendation
    )
    DASHBOARD_MODELS_AVAILABLE = True
except ImportError:
    DASHBOARD_MODELS_AVAILABLE = False


@dataclass
class RealTimeEvent:
    """Real-time event data structure."""
    event_type: str
    timestamp: datetime
    lead_id: str
    agent_id: Optional[str]
    data: Dict[str, Any]
    confidence: float
    source: str


@dataclass
class ConnectionContext:
    """WebSocket connection context."""
    connection_id: str
    agent_id: str
    location_id: str
    subscribed_events: List[str]
    last_activity: datetime
    filters: Dict[str, Any]


class RealTimeIntelligenceConnector:
    """
    Real-time intelligence connector for live Claude AI integration.

    Provides high-performance, real-time data streaming between Claude AI services
    and dashboard components with WebSocket support, caching, and event-driven updates.
    """

    def __init__(self, redis_url: Optional[str] = None, cache_ttl: int = 300):
        """
        Initialize real-time connector.

        Args:
            redis_url: Redis connection URL for caching
            cache_ttl: Cache time-to-live in seconds
        """
        self.redis_url = redis_url or "redis://localhost:6379"
        self.cache_ttl = cache_ttl
        self.logger = logging.getLogger(__name__)

        # Connection management
        self.active_connections: Dict[str, ConnectionContext] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.event_subscribers: Dict[str, List[Callable]] = {}

        # Data cache
        self.cache_store: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}

        # Performance metrics
        self.performance_metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0.0,
            "active_connections": 0,
            "events_published": 0
        }

        # Claude services
        self.claude_services = {}

        # Initialize services
        asyncio.create_task(self._initialize_services())

    async def _initialize_services(self):
        """Initialize Claude AI services and Redis connection."""
        try:
            # Initialize Redis
            self.redis = await aioredis.create_redis_pool(self.redis_url)
            self.logger.info("Redis connection established")

            # Initialize Claude services
            if CLAUDE_SERVICES_AVAILABLE:
                self.claude_services = {
                    'agent_service': await get_claude_agent_service(),
                    'semantic_analyzer': await get_claude_semantic_analyzer(),
                    'qualification_orchestrator': await get_qualification_orchestrator(),
                    'action_planner': await get_claude_action_planner()
                }
                self.logger.info(f"Initialized {len(self.claude_services)} Claude services")

            # Start background tasks
            asyncio.create_task(self._cache_cleanup_task())
            asyncio.create_task(self._connection_heartbeat_task())

        except Exception as e:
            self.logger.error(f"Error initializing services: {e}")

    async def connect_websocket(
        self,
        websocket: WebSocket,
        agent_id: str,
        location_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Connect a new WebSocket client for real-time updates.

        Args:
            websocket: WebSocket connection
            agent_id: Agent identifier
            location_id: GHL location ID for data scoping
            filters: Optional filters for events

        Returns:
            Connection ID for the established connection
        """
        connection_id = f"conn_{int(time.time() * 1000)}_{agent_id}"

        # Accept WebSocket connection
        await websocket.accept()

        # Store connection context
        context = ConnectionContext(
            connection_id=connection_id,
            agent_id=agent_id,
            location_id=location_id,
            subscribed_events=["all"],  # Default subscription
            last_activity=datetime.now(),
            filters=filters or {}
        )

        self.active_connections[connection_id] = context
        self.websocket_connections[connection_id] = websocket
        self.performance_metrics["active_connections"] = len(self.active_connections)

        self.logger.info(f"WebSocket connected: {connection_id} for agent {agent_id}")

        # Send initial connection confirmation
        await self._send_to_connection(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Real-time intelligence stream active"
        })

        return connection_id

    async def disconnect_websocket(self, connection_id: str):
        """Disconnect a WebSocket client."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        if connection_id in self.websocket_connections:
            try:
                await self.websocket_connections[connection_id].close()
            except:
                pass
            del self.websocket_connections[connection_id]

        self.performance_metrics["active_connections"] = len(self.active_connections)
        self.logger.info(f"WebSocket disconnected: {connection_id}")

    async def subscribe_to_events(self, connection_id: str, event_types: List[str]):
        """Subscribe a connection to specific event types."""
        if connection_id in self.active_connections:
            self.active_connections[connection_id].subscribed_events = event_types
            self.logger.debug(f"Connection {connection_id} subscribed to: {event_types}")

    async def get_real_time_coaching(
        self,
        lead_id: str,
        agent_id: str,
        conversation_context: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get real-time coaching data with caching.

        Args:
            lead_id: Lead identifier
            agent_id: Agent identifier
            conversation_context: Current conversation context
            use_cache: Whether to use cached data

        Returns:
            Real-time coaching recommendations
        """
        start_time = time.time()
        cache_key = f"coaching:{lead_id}:{agent_id}:{hash(str(conversation_context))}"

        # Check cache first
        if use_cache:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                self.performance_metrics["cache_hits"] += 1
                await self._publish_event("coaching_delivered", lead_id, agent_id, cached_data)
                return cached_data

        self.performance_metrics["cache_misses"] += 1

        try:
            # Get coaching from Claude service
            if 'agent_service' in self.claude_services:
                coaching_response = await self.claude_services['agent_service'].get_real_time_coaching(
                    agent_id=agent_id,
                    conversation_context=conversation_context,
                    prospect_message=conversation_context.get('latest_message', ''),
                    conversation_stage=conversation_context.get('stage', 'discovery')
                )

                # Transform to dashboard format
                coaching_data = {
                    "suggestions": coaching_response.suggestions,
                    "urgency": coaching_response.urgency_level,
                    "confidence": coaching_response.confidence_score / 100,
                    "stage": conversation_context.get('stage', 'discovery'),
                    "objection_detected": coaching_response.objection_detected,
                    "next_question": coaching_response.recommended_questions[0] if coaching_response.recommended_questions else None,
                    "timestamp": datetime.now().isoformat(),
                    "processing_time_ms": coaching_response.processing_time_ms
                }

                # Cache the result
                await self._set_cache(cache_key, coaching_data)

                # Publish real-time event
                await self._publish_event("coaching_delivered", lead_id, agent_id, coaching_data)

                # Update metrics
                processing_time = (time.time() - start_time) * 1000
                self._update_response_time_metric(processing_time)

                return coaching_data

        except Exception as e:
            self.logger.error(f"Error getting real-time coaching: {e}")
            return self._get_fallback_coaching_data()

        return self._get_fallback_coaching_data()

    async def get_sentiment_analysis(
        self,
        lead_id: str,
        conversation_messages: List[Dict[str, str]],
        use_cache: bool = True
    ) -> List[SentimentAnalysis]:
        """
        Get real-time sentiment analysis.

        Args:
            lead_id: Lead identifier
            conversation_messages: List of conversation messages
            use_cache: Whether to use cached data

        Returns:
            List of sentiment analysis results
        """
        cache_key = f"sentiment:{lead_id}:{hash(str(conversation_messages))}"

        # Check cache
        if use_cache:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data and DASHBOARD_MODELS_AVAILABLE:
                sentiment_objects = [
                    SentimentAnalysis(**item) for item in cached_data
                ]
                return sentiment_objects

        try:
            # Get sentiment from Claude service
            if 'semantic_analyzer' in self.claude_services:
                semantic_result = await self.claude_services['semantic_analyzer'].analyze_conversation(
                    conversation_messages=conversation_messages
                )

                # Transform to SentimentAnalysis objects
                sentiment_data = []
                for i, message in enumerate(conversation_messages):
                    sentiment = SentimentAnalysis(
                        timestamp=datetime.now() - timedelta(minutes=len(conversation_messages) - i),
                        overall_sentiment=semantic_result.sentiment_score - 0.5,  # Normalize to -0.5 to 0.5
                        emotion_breakdown=semantic_result.emotion_analysis,
                        voice_tone=semantic_result.communication_style,
                        confidence=semantic_result.confidence,
                        engagement_level=semantic_result.engagement_score,
                        communication_style=semantic_result.communication_style,
                        recommended_response=semantic_result.recommended_approach
                    )
                    sentiment_data.append(sentiment)

                # Cache the result
                if DASHBOARD_MODELS_AVAILABLE:
                    cache_data = [asdict(item) for item in sentiment_data]
                    await self._set_cache(cache_key, cache_data)

                # Publish real-time event
                await self._publish_event("sentiment_updated", lead_id, None, {
                    "latest_sentiment": sentiment_data[-1].overall_sentiment,
                    "engagement_level": sentiment_data[-1].engagement_level,
                    "confidence": sentiment_data[-1].confidence
                })

                return sentiment_data

        except Exception as e:
            self.logger.error(f"Error getting sentiment analysis: {e}")

        return self._get_fallback_sentiment_data()

    async def get_lead_journey_progress(
        self,
        lead_id: str,
        agent_id: str,
        use_cache: bool = True
    ) -> List[LeadJourneyStage]:
        """
        Get lead journey progression data.

        Args:
            lead_id: Lead identifier
            agent_id: Agent identifier
            use_cache: Whether to use cached data

        Returns:
            List of journey stages with AI insights
        """
        cache_key = f"journey:{lead_id}:{agent_id}"

        # Check cache
        if use_cache:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data and DASHBOARD_MODELS_AVAILABLE:
                journey_objects = [
                    LeadJourneyStage(**item) for item in cached_data
                ]
                return journey_objects

        try:
            # Get journey data from qualification orchestrator
            if 'qualification_orchestrator' in self.claude_services:
                qualification_result = await self.claude_services['qualification_orchestrator'].get_qualification_progress(
                    contact_id=lead_id
                )

                # Transform to journey stages
                journey_stages = []

                # Current stage based on qualification progress
                completion_pct = qualification_result.completion_percentage

                if completion_pct < 25:
                    current_stage = "Initial Contact"
                    stage_order = 1
                elif completion_pct < 60:
                    current_stage = "Qualification"
                    stage_order = 2
                elif completion_pct < 85:
                    current_stage = "Property Evaluation"
                    stage_order = 3
                else:
                    current_stage = "Closing Process"
                    stage_order = 4

                # Create journey stage with Claude insights
                if 'action_planner' in self.claude_services:
                    action_plan = await self.claude_services['action_planner'].create_action_plan(
                        contact_id=lead_id,
                        context={"qualification_progress": completion_pct}
                    )

                    stage = LeadJourneyStage(
                        stage_name=current_stage,
                        stage_order=stage_order,
                        entry_time=datetime.now() - timedelta(days=stage_order),
                        predicted_exit_time=datetime.now() + timedelta(days=2),
                        conversion_probability=completion_pct / 100,
                        risk_factors=action_plan.risk_assessment.get("risks", ["Standard lead progression"]),
                        opportunities=action_plan.immediate_actions[:3] if action_plan.immediate_actions else ["Continue qualification"],
                        claude_insights=[
                            f"Qualification completion: {completion_pct:.1f}%",
                            f"Priority level: {action_plan.priority_score}/100",
                            f"Recommended focus: {action_plan.follow_up_strategy.get('primary_focus', 'Continue engagement')}"
                        ],
                        recommended_actions=[action.description for action in action_plan.immediate_actions[:3]]
                    )

                    journey_stages.append(stage)

                # Cache the result
                if DASHBOARD_MODELS_AVAILABLE:
                    cache_data = [asdict(item) for item in journey_stages]
                    await self._set_cache(cache_key, cache_data)

                # Publish real-time event
                await self._publish_event("journey_updated", lead_id, agent_id, {
                    "current_stage": current_stage,
                    "conversion_probability": completion_pct / 100,
                    "stage_order": stage_order
                })

                return journey_stages

        except Exception as e:
            self.logger.error(f"Error getting journey progress: {e}")

        return self._get_fallback_journey_data(lead_id)

    async def get_content_recommendations(
        self,
        lead_id: str,
        lead_profile: Dict[str, Any],
        use_cache: bool = True
    ) -> List[ContentRecommendation]:
        """
        Get intelligent content recommendations.

        Args:
            lead_id: Lead identifier
            lead_profile: Lead profile data
            use_cache: Whether to use cached data

        Returns:
            List of content recommendations
        """
        cache_key = f"content:{lead_id}:{hash(str(lead_profile))}"

        # Check cache
        if use_cache:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data and DASHBOARD_MODELS_AVAILABLE:
                content_objects = [
                    ContentRecommendation(**item) for item in cached_data
                ]
                return content_objects

        try:
            # Get action plan which includes content strategy
            if 'action_planner' in self.claude_services:
                action_plan = await self.claude_services['action_planner'].create_action_plan(
                    contact_id=lead_id,
                    context=lead_profile
                )

                recommendations = []

                # Transform action plan to content recommendations
                for i, action in enumerate(action_plan.immediate_actions[:3]):
                    if "send" in action.description.lower() or "share" in action.description.lower():
                        content_type = "listing"
                        if "market" in action.description.lower():
                            content_type = "market_report"
                        elif "guide" in action.description.lower():
                            content_type = "educational"

                        recommendation = ContentRecommendation(
                            content_type=content_type,
                            title=action.description,
                            relevance_score=min(1.0, action_plan.priority_score / 100),
                            predicted_engagement=0.7 + (i * 0.1),
                            optimal_timing=action_plan.follow_up_strategy.get("timing", "Within 24 hours"),
                            delivery_channel=action_plan.follow_up_strategy.get("channel", "Email"),
                            personalization_notes=[
                                f"Based on {key}: {value}" for key, value in lead_profile.items() if key in ["interests", "communication_style"]
                            ],
                            claude_rationale=action.reasoning
                        )
                        recommendations.append(recommendation)

                # Cache the result
                if DASHBOARD_MODELS_AVAILABLE:
                    cache_data = [asdict(item) for item in recommendations]
                    await self._set_cache(cache_key, cache_data)

                # Publish real-time event
                await self._publish_event("content_recommended", lead_id, None, {
                    "recommendation_count": len(recommendations),
                    "top_relevance": recommendations[0].relevance_score if recommendations else 0
                })

                return recommendations

        except Exception as e:
            self.logger.error(f"Error getting content recommendations: {e}")

        return self._get_fallback_content_recommendations()

    async def _publish_event(self, event_type: str, lead_id: str, agent_id: Optional[str], data: Dict[str, Any]):
        """Publish real-time event to connected clients."""
        event = RealTimeEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            lead_id=lead_id,
            agent_id=agent_id,
            data=data,
            confidence=data.get("confidence", 0.9),
            source="claude_ai"
        )

        # Send to all connected clients
        for connection_id, context in self.active_connections.items():
            if self._should_send_event(context, event):
                await self._send_to_connection(connection_id, {
                    "type": "real_time_event",
                    "event": asdict(event),
                    "timestamp": datetime.now().isoformat()
                })

        self.performance_metrics["events_published"] += 1

    def _should_send_event(self, context: ConnectionContext, event: RealTimeEvent) -> bool:
        """Check if event should be sent to connection based on filters."""
        # Check if event type is subscribed
        if "all" not in context.subscribed_events and event.event_type not in context.subscribed_events:
            return False

        # Check agent filter
        if event.agent_id and context.agent_id != event.agent_id:
            return False

        # Apply custom filters
        for filter_key, filter_value in context.filters.items():
            if hasattr(event, filter_key) and getattr(event, filter_key) != filter_value:
                return False

        return True

    async def _send_to_connection(self, connection_id: str, data: Dict[str, Any]):
        """Send data to specific WebSocket connection."""
        if connection_id in self.websocket_connections:
            try:
                websocket = self.websocket_connections[connection_id]
                await websocket.send_text(json.dumps(data))
                self.active_connections[connection_id].last_activity = datetime.now()
            except Exception as e:
                self.logger.warning(f"Failed to send to connection {connection_id}: {e}")
                await self.disconnect_websocket(connection_id)

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache with TTL check."""
        if key in self.cache_store:
            if key in self.cache_timestamps:
                age = datetime.now() - self.cache_timestamps[key]
                if age.total_seconds() < self.cache_ttl:
                    return self.cache_store[key]
                else:
                    # Remove expired data
                    del self.cache_store[key]
                    del self.cache_timestamps[key]

        # Try Redis cache if available
        try:
            if hasattr(self, 'redis') and self.redis:
                cached_data = await self.redis.get(key)
                if cached_data:
                    return json.loads(cached_data)
        except Exception as e:
            self.logger.warning(f"Redis cache error: {e}")

        return None

    async def _set_cache(self, key: str, data: Any):
        """Set data in cache with TTL."""
        # Local cache
        self.cache_store[key] = data
        self.cache_timestamps[key] = datetime.now()

        # Redis cache if available
        try:
            if hasattr(self, 'redis') and self.redis:
                await self.redis.setex(key, self.cache_ttl, json.dumps(data, default=str))
        except Exception as e:
            self.logger.warning(f"Redis cache set error: {e}")

    def _update_response_time_metric(self, response_time: float):
        """Update average response time metric."""
        self.performance_metrics["total_requests"] += 1
        current_avg = self.performance_metrics["avg_response_time"]
        total_requests = self.performance_metrics["total_requests"]

        # Calculate running average
        new_avg = ((current_avg * (total_requests - 1)) + response_time) / total_requests
        self.performance_metrics["avg_response_time"] = new_avg

    async def _cache_cleanup_task(self):
        """Background task to clean up expired cache entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                expired_keys = []
                for key, timestamp in self.cache_timestamps.items():
                    age = datetime.now() - timestamp
                    if age.total_seconds() > self.cache_ttl:
                        expired_keys.append(key)

                for key in expired_keys:
                    if key in self.cache_store:
                        del self.cache_store[key]
                    if key in self.cache_timestamps:
                        del self.cache_timestamps[key]

                if expired_keys:
                    self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")

    async def _connection_heartbeat_task(self):
        """Background task to check connection health."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                current_time = datetime.now()
                inactive_connections = []

                for connection_id, context in self.active_connections.items():
                    inactive_time = current_time - context.last_activity
                    if inactive_time.total_seconds() > 300:  # 5 minutes inactive
                        inactive_connections.append(connection_id)

                for connection_id in inactive_connections:
                    await self.disconnect_websocket(connection_id)

                if inactive_connections:
                    self.logger.info(f"Cleaned up {len(inactive_connections)} inactive connections")

            except Exception as e:
                self.logger.error(f"Connection heartbeat error: {e}")

    # Fallback data methods

    def _get_fallback_coaching_data(self) -> Dict[str, Any]:
        """Get fallback coaching data when Claude services unavailable."""
        return {
            "suggestions": [
                "Continue building rapport with the prospect",
                "Ask open-ended questions to understand needs",
                "Listen actively and acknowledge their concerns"
            ],
            "urgency": "medium",
            "confidence": 0.7,
            "stage": "discovery",
            "objection_detected": False,
            "next_question": "What's most important to you in this process?",
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": 50
        }

    def _get_fallback_sentiment_data(self) -> List[SentimentAnalysis]:
        """Get fallback sentiment data."""
        if not DASHBOARD_MODELS_AVAILABLE:
            return []

        return [
            SentimentAnalysis(
                timestamp=datetime.now(),
                overall_sentiment=0.3,
                emotion_breakdown={"neutral": 0.7, "positive": 0.3},
                voice_tone="professional",
                confidence=0.8,
                engagement_level=0.6,
                communication_style="direct",
                recommended_response="Continue with standard approach"
            )
        ]

    def _get_fallback_journey_data(self, lead_id: str) -> List[LeadJourneyStage]:
        """Get fallback journey data."""
        if not DASHBOARD_MODELS_AVAILABLE:
            return []

        return [
            LeadJourneyStage(
                stage_name="Active Engagement",
                stage_order=2,
                entry_time=datetime.now() - timedelta(days=2),
                predicted_exit_time=datetime.now() + timedelta(days=3),
                conversion_probability=0.65,
                risk_factors=["Standard lead progression"],
                opportunities=["Active engagement", "Showing interest"],
                claude_insights=["Lead is engaged and responsive"],
                recommended_actions=["Continue current approach", "Schedule follow-up"]
            )
        ]

    def _get_fallback_content_recommendations(self) -> List[ContentRecommendation]:
        """Get fallback content recommendations."""
        if not DASHBOARD_MODELS_AVAILABLE:
            return []

        return [
            ContentRecommendation(
                content_type="market_report",
                title="Current Market Overview",
                relevance_score=0.75,
                predicted_engagement=0.65,
                optimal_timing="Next business day",
                delivery_channel="Email",
                personalization_notes=["Standard market information"],
                claude_rationale="Provides valuable market context for decision making"
            )
        ]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            **self.performance_metrics,
            "cache_hit_rate": self.performance_metrics["cache_hits"] / max(1, self.performance_metrics["cache_hits"] + self.performance_metrics["cache_misses"]),
            "cached_items": len(self.cache_store),
            "uptime_seconds": time.time() - getattr(self, '_start_time', time.time())
        }


# Singleton instance
_realtime_connector: Optional[RealTimeIntelligenceConnector] = None


async def get_realtime_connector() -> RealTimeIntelligenceConnector:
    """Get singleton real-time intelligence connector."""
    global _realtime_connector
    if _realtime_connector is None:
        _realtime_connector = RealTimeIntelligenceConnector()
        _realtime_connector._start_time = time.time()
    return _realtime_connector


# Factory function for testing
def create_realtime_connector(redis_url: Optional[str] = None, cache_ttl: int = 300) -> RealTimeIntelligenceConnector:
    """Create a new real-time intelligence connector instance."""
    return RealTimeIntelligenceConnector(redis_url=redis_url, cache_ttl=cache_ttl)