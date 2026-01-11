"""
WebSocket Manager Service for Real-Time Lead Intelligence

Enterprise-grade WebSocket management integrating:
- Real-time ML lead intelligence streaming
- Optimized connection pooling and health monitoring
- Redis-backed caching with <100ms latency
- Parallel ML inference coordination
- Tenant-isolated event broadcasting

Performance Targets:
- WebSocket latency: <100ms (end-to-end)
- Concurrent connections: 100+ per tenant
- ML intelligence polling: 500ms interval
- Cache hit rate: >90%
- Broadcast latency: <50ms for 100 clients

Architecture:
- Extends RealtimeWebSocketHub for connection management
- Integrates with OptimizedMLLeadIntelligenceEngine for <35ms inference
- Uses RealtimeLeadScoringService for <100ms scoring
- Redis caching for performance optimization
- Event-driven architecture for real-time updates
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable
from enum import Enum
from collections import defaultdict

from fastapi import WebSocket
from ghl_real_estate_ai.services.realtime_websocket_hub import (
    RealtimeWebSocketHub,
    WebSocketConnection,
    BroadcastResult,
    get_realtime_websocket_hub
)
from ghl_real_estate_ai.services.optimized_ml_lead_intelligence_engine import (
    OptimizedMLLeadIntelligenceEngine,
    OptimizedLeadIntelligence,
    ProcessingPriority,
    IntelligenceType,
    get_optimized_ml_intelligence_engine
)
from ghl_real_estate_ai.services.realtime_lead_scoring import (
    RealtimeLeadScoringService,
    LeadScore,
    get_lead_scoring_service
)
from ghl_real_estate_ai.services.churn_prediction_service import (
    ChurnPrediction,
    get_churn_prediction_service
)
from ghl_real_estate_ai.services.enhanced_property_matcher_ml import (
    EnhancedPropertyMatch,
    get_enhanced_property_matcher
)
from ghl_real_estate_ai.database.redis_client import redis_client, get_redis_health
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class IntelligenceEventType(Enum):
    """Real-time intelligence event types"""
    LEAD_SCORE_UPDATE = "lead_score_update"
    CHURN_RISK_ALERT = "churn_risk_alert"
    PROPERTY_MATCH_FOUND = "property_match_found"
    BEHAVIORAL_INSIGHT = "behavioral_insight"
    INTELLIGENCE_COMPLETE = "intelligence_complete"
    PERFORMANCE_METRICS = "performance_metrics"
    CONNECTION_STATUS = "connection_status"


class SubscriptionTopic(Enum):
    """WebSocket subscription topics"""
    LEAD_INTELLIGENCE = "lead_intelligence"
    LEAD_SCORING = "lead_scoring"
    CHURN_PREDICTION = "churn_prediction"
    PROPERTY_MATCHING = "property_matching"
    SYSTEM_METRICS = "system_metrics"
    ALL = "all"


@dataclass
class IntelligenceSubscription:
    """Subscription to real-time intelligence updates"""
    subscription_id: str
    tenant_id: str
    connection_id: str
    topics: List[SubscriptionTopic]
    lead_filters: Optional[List[str]] = None  # Specific lead IDs to watch
    created_at: datetime = None
    last_update: datetime = None
    update_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_update is None:
            self.last_update = datetime.now()


@dataclass
class IntelligenceUpdate:
    """Real-time intelligence update event"""
    event_id: str
    event_type: IntelligenceEventType
    tenant_id: str
    lead_id: str
    timestamp: datetime

    # Intelligence data
    lead_score: Optional[LeadScore] = None
    churn_prediction: Optional[ChurnPrediction] = None
    property_matches: Optional[List[EnhancedPropertyMatch]] = None
    intelligence: Optional[OptimizedLeadIntelligence] = None

    # Performance metadata
    processing_time_ms: float = 0.0
    cache_hit: bool = False
    ml_operations: int = 0
    broadcast_latency_ms: float = 0.0


@dataclass
class WebSocketPerformanceMetrics:
    """WebSocket manager performance tracking"""
    total_connections: int = 0
    active_subscriptions: int = 0
    total_updates_sent: int = 0
    total_broadcasts: int = 0
    avg_broadcast_latency_ms: float = 0.0
    avg_ml_processing_ms: float = 0.0
    cache_hit_rate: float = 0.0
    connection_success_rate: float = 1.0

    # Real-time performance indicators
    current_load: float = 0.0  # 0-1
    updates_per_second: float = 0.0
    ml_inference_queue_depth: int = 0
    redis_health: bool = True


class WebSocketManager:
    """
    Real-Time WebSocket Manager for Lead Intelligence Streaming.

    Orchestrates real-time ML intelligence updates through WebSocket connections
    with enterprise-grade performance, caching, and monitoring.

    Key Features:
    - Tenant-isolated connection management
    - Parallel ML inference with <35ms target
    - Redis-backed caching for <10ms cache hits
    - Event-driven intelligence broadcasting
    - Connection health monitoring
    - Performance metrics tracking
    """

    def __init__(
        self,
        websocket_hub: Optional[RealtimeWebSocketHub] = None,
        ml_engine: Optional[OptimizedMLLeadIntelligenceEngine] = None,
        scoring_service: Optional[RealtimeLeadScoringService] = None
    ):
        """
        Initialize WebSocket Manager.

        Args:
            websocket_hub: WebSocket connection hub (uses singleton if None)
            ml_engine: Optimized ML intelligence engine (uses singleton if None)
            scoring_service: Real-time lead scoring service (uses singleton if None)
        """
        # Core services (will be initialized asynchronously)
        self.websocket_hub = websocket_hub
        self.ml_engine = ml_engine
        self.scoring_service = scoring_service
        self.churn_service = None
        self.property_matcher = None

        # Redis client for caching
        self.redis_client = redis_client

        # Subscription management
        self._subscriptions: Dict[str, IntelligenceSubscription] = {}
        self._tenant_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self._lead_subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # Event processing
        self._event_queue = asyncio.Queue(maxsize=5000)
        self._processing_tasks: Set[asyncio.Task] = set()

        # Performance tracking
        self.metrics = WebSocketPerformanceMetrics()
        self._performance_history = []
        self._last_metrics_update = time.time()

        # Configuration
        self.polling_interval = 0.5  # 500ms polling for cache results
        self.max_concurrent_processing = 100
        self.cache_ttl = 300  # 5 minutes
        self.intelligence_batch_size = 25

        # Background workers
        self._workers_started = False
        self._worker_tasks = []

        logger.info("WebSocket Manager initialized")

    async def initialize(self):
        """Initialize WebSocket Manager with dependencies"""
        try:
            # Initialize core services if not provided
            if self.websocket_hub is None:
                self.websocket_hub = get_realtime_websocket_hub()

            if self.ml_engine is None:
                self.ml_engine = await get_optimized_ml_intelligence_engine()

            if self.scoring_service is None:
                self.scoring_service = await get_lead_scoring_service()

            # Initialize supporting services
            self.churn_service = get_churn_prediction_service()
            self.property_matcher = get_enhanced_property_matcher()

            # Initialize Redis connection
            await self.redis_client.initialize()

            # Start background workers
            await self._start_background_workers()

            logger.info("WebSocket Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize WebSocket Manager: {e}")
            raise

    async def subscribe_to_lead_intelligence(
        self,
        websocket: WebSocket,
        tenant_id: str,
        user_id: str,
        topics: Optional[List[SubscriptionTopic]] = None,
        lead_filters: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Subscribe WebSocket connection to real-time lead intelligence updates.

        Args:
            websocket: FastAPI WebSocket instance
            tenant_id: Tenant identifier for isolation
            user_id: User identifier
            topics: List of topics to subscribe to (defaults to ALL)
            lead_filters: Optional list of specific lead IDs to monitor

        Returns:
            Subscription ID if successful, None if failed
        """
        start_time = time.time()

        try:
            # Connect client to WebSocket hub
            connection_id = await self.websocket_hub.connect_client(
                websocket=websocket,
                tenant_id=tenant_id,
                user_id=user_id,
                subscription_topics=[topic.value for topic in (topics or [SubscriptionTopic.ALL])]
            )

            if not connection_id:
                logger.warning(f"Failed to connect WebSocket for tenant {tenant_id}")
                return None

            # Create intelligence subscription
            subscription_id = f"sub_{uuid.uuid4().hex[:12]}"
            if topics is None:
                topics = [SubscriptionTopic.ALL]

            subscription = IntelligenceSubscription(
                subscription_id=subscription_id,
                tenant_id=tenant_id,
                connection_id=connection_id,
                topics=topics,
                lead_filters=lead_filters
            )

            # Store subscription
            self._subscriptions[subscription_id] = subscription
            self._tenant_subscriptions[tenant_id].add(subscription_id)

            # Track lead-specific subscriptions
            if lead_filters:
                for lead_id in lead_filters:
                    self._lead_subscriptions[lead_id].add(subscription_id)

            # Update metrics
            self.metrics.total_connections += 1
            self.metrics.active_subscriptions = len(self._subscriptions)

            connection_time = (time.time() - start_time) * 1000
            logger.info(f"Intelligence subscription created: {subscription_id} "
                       f"(tenant: {tenant_id}, topics: {[t.value for t in topics]}, "
                       f"time: {connection_time:.1f}ms)")

            # Send initial connection confirmation
            await self._send_connection_status(subscription_id, "connected")

            return subscription_id

        except Exception as e:
            logger.error(f"Failed to create intelligence subscription: {e}")
            return None

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from lead intelligence updates.

        Args:
            subscription_id: Subscription identifier

        Returns:
            True if unsubscribed successfully, False otherwise
        """
        try:
            subscription = self._subscriptions.get(subscription_id)
            if not subscription:
                logger.warning(f"Subscription {subscription_id} not found")
                return False

            # Disconnect from WebSocket hub
            await self.websocket_hub.disconnect_client(subscription.connection_id)

            # Remove from subscription tracking
            del self._subscriptions[subscription_id]
            self._tenant_subscriptions[subscription.tenant_id].discard(subscription_id)

            # Remove from lead-specific tracking
            if subscription.lead_filters:
                for lead_id in subscription.lead_filters:
                    self._lead_subscriptions[lead_id].discard(subscription_id)

            # Update metrics
            self.metrics.active_subscriptions = len(self._subscriptions)

            logger.info(f"Intelligence subscription removed: {subscription_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unsubscribe {subscription_id}: {e}")
            return False

    async def broadcast_intelligence_update(
        self,
        tenant_id: str,
        intelligence: OptimizedLeadIntelligence,
        event_type: IntelligenceEventType = IntelligenceEventType.INTELLIGENCE_COMPLETE
    ) -> BroadcastResult:
        """
        Broadcast ML intelligence update to subscribed WebSocket connections.

        Args:
            tenant_id: Tenant identifier
            intelligence: Optimized lead intelligence data
            event_type: Type of intelligence event

        Returns:
            BroadcastResult with delivery metrics
        """
        start_time = time.time()

        try:
            # Create intelligence update event
            update = IntelligenceUpdate(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                event_type=event_type,
                tenant_id=tenant_id,
                lead_id=intelligence.lead_id,
                timestamp=datetime.now(),
                intelligence=intelligence,
                lead_score=intelligence.lead_score,
                churn_prediction=intelligence.churn_prediction,
                property_matches=intelligence.property_matches,
                processing_time_ms=intelligence.processing_time_ms,
                cache_hit=intelligence.cache_hit_rate > 0.5,
                ml_operations=intelligence.parallel_operations
            )

            # Prepare broadcast data
            broadcast_data = self._serialize_intelligence_update(update)

            # Broadcast to tenant connections
            result = await self.websocket_hub.broadcast_to_tenant(
                tenant_id=tenant_id,
                event_data=broadcast_data
            )

            # Update performance metrics
            broadcast_latency = (time.time() - start_time) * 1000
            update.broadcast_latency_ms = broadcast_latency

            self._update_broadcast_metrics(result, broadcast_latency)

            # Cache the update for retrieval
            await self._cache_intelligence_update(update)

            logger.debug(f"Intelligence update broadcasted: {update.event_id} "
                        f"(tenant: {tenant_id}, lead: {intelligence.lead_id}, "
                        f"recipients: {result.connections_successful}/{result.connections_targeted}, "
                        f"latency: {broadcast_latency:.1f}ms)")

            return result

        except Exception as e:
            logger.error(f"Failed to broadcast intelligence update: {e}")
            return BroadcastResult(
                event_type=event_type.value,
                tenant_id=tenant_id,
                connections_targeted=0,
                connections_successful=0,
                connections_failed=1,
                broadcast_time_ms=(time.time() - start_time) * 1000,
                errors=[str(e)]
            )

    async def handle_ml_event(
        self,
        lead_id: str,
        tenant_id: str,
        event_data: Dict[str, Any],
        priority: ProcessingPriority = ProcessingPriority.MEDIUM
    ) -> Optional[OptimizedLeadIntelligence]:
        """
        Process ML event and trigger real-time intelligence updates.

        This is the main entry point for processing lead events with ML inference
        and broadcasting results to WebSocket subscribers.

        Args:
            lead_id: Lead identifier
            tenant_id: Tenant identifier
            event_data: Lead event data for processing
            priority: Processing priority level

        Returns:
            OptimizedLeadIntelligence if successful, None otherwise
        """
        start_time = time.time()

        try:
            # Check cache first for recent intelligence
            cached_intelligence = await self._get_cached_intelligence(lead_id, tenant_id)
            if cached_intelligence and self._is_intelligence_fresh(cached_intelligence):
                logger.debug(f"Using cached intelligence for lead {lead_id}")
                # Still broadcast to update subscribers
                await self.broadcast_intelligence_update(tenant_id, cached_intelligence)
                return cached_intelligence

            # Process with optimized ML engine
            intelligence = await self.ml_engine.process_lead_event_optimized(
                lead_id=lead_id,
                event_data=event_data,
                priority=priority
            )

            # Broadcast to subscribers
            await self.broadcast_intelligence_update(tenant_id, intelligence)

            # Send specific event types for key insights
            await self._broadcast_specific_insights(tenant_id, intelligence)

            # Update performance tracking
            processing_time = (time.time() - start_time) * 1000
            self._update_ml_processing_metrics(processing_time, intelligence)

            logger.info(f"ML event processed for lead {lead_id}: "
                       f"score={intelligence.lead_score.score if intelligence.lead_score else 'N/A'}, "
                       f"processing_time={processing_time:.1f}ms")

            return intelligence

        except Exception as e:
            logger.error(f"Failed to handle ML event for lead {lead_id}: {e}")
            return None

    async def get_connection_health(self) -> Dict[str, Any]:
        """
        Get comprehensive connection health and performance metrics.

        Returns:
            Dictionary with health status, performance metrics, and system state
        """
        try:
            # Get WebSocket hub health
            hub_health = await self.websocket_hub.get_connection_health()

            # Get Redis health
            redis_health = await get_redis_health()

            # Get ML engine optimization metrics
            ml_metrics = await self.ml_engine.get_optimization_metrics()

            # Calculate current performance indicators
            current_load = len(self._subscriptions) / max(
                self.max_concurrent_processing, 1
            )

            # Calculate updates per second
            recent_updates = self._performance_history[-60:] if self._performance_history else []
            updates_per_second = len(recent_updates) / 60 if recent_updates else 0

            return {
                "timestamp": datetime.now().isoformat(),
                "websocket_manager": {
                    "total_connections": self.metrics.total_connections,
                    "active_subscriptions": self.metrics.active_subscriptions,
                    "total_updates_sent": self.metrics.total_updates_sent,
                    "total_broadcasts": self.metrics.total_broadcasts,
                    "avg_broadcast_latency_ms": self.metrics.avg_broadcast_latency_ms,
                    "avg_ml_processing_ms": self.metrics.avg_ml_processing_ms,
                    "cache_hit_rate": self.metrics.cache_hit_rate,
                    "connection_success_rate": self.metrics.connection_success_rate,
                    "current_load": current_load,
                    "updates_per_second": updates_per_second
                },
                "websocket_hub": hub_health,
                "redis": redis_health,
                "ml_engine": ml_metrics,
                "performance_targets": {
                    "websocket_latency_target_ms": 100,
                    "ml_inference_target_ms": 35,
                    "cache_hit_rate_target": 0.90,
                    "broadcast_latency_target_ms": 50
                },
                "performance_status": {
                    "websocket_latency_ok": self.metrics.avg_broadcast_latency_ms < 100,
                    "ml_inference_ok": self.metrics.avg_ml_processing_ms < 40,
                    "cache_performance_ok": self.metrics.cache_hit_rate > 0.80,
                    "overall_healthy": (
                        self.metrics.avg_broadcast_latency_ms < 100 and
                        self.metrics.avg_ml_processing_ms < 40 and
                        redis_health.get("is_healthy", False)
                    )
                }
            }

        except Exception as e:
            logger.error(f"Failed to get connection health: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # Internal helper methods

    async def _start_background_workers(self):
        """Start background worker tasks"""
        if self._workers_started:
            return

        # Event processing worker
        event_worker = asyncio.create_task(self._event_processing_worker())
        self._worker_tasks.append(event_worker)

        # Performance monitoring worker
        metrics_worker = asyncio.create_task(self._performance_monitoring_worker())
        self._worker_tasks.append(metrics_worker)

        # Cache polling worker for real-time updates
        cache_worker = asyncio.create_task(self._cache_polling_worker())
        self._worker_tasks.append(cache_worker)

        # Connection health monitoring
        health_worker = asyncio.create_task(self._connection_health_worker())
        self._worker_tasks.append(health_worker)

        self._workers_started = True
        logger.info("Background workers started")

    async def _event_processing_worker(self):
        """Background worker for processing intelligence events"""
        while True:
            try:
                # Process events from queue
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )

                # Create processing task
                task = asyncio.create_task(self._process_event(event))
                self._processing_tasks.add(task)
                task.add_done_callback(self._processing_tasks.discard)

                # Limit concurrent processing
                if len(self._processing_tasks) >= self.max_concurrent_processing:
                    await asyncio.sleep(0.01)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing worker error: {e}")
                await asyncio.sleep(1)

    async def _performance_monitoring_worker(self):
        """Background worker for performance monitoring"""
        while True:
            try:
                await asyncio.sleep(10)  # Monitor every 10 seconds

                # Update performance metrics
                await self._update_performance_metrics()

                # Log performance warnings
                if self.metrics.avg_broadcast_latency_ms > 100:
                    logger.warning(
                        f"Broadcast latency above target: {self.metrics.avg_broadcast_latency_ms:.1f}ms"
                    )

                if self.metrics.avg_ml_processing_ms > 40:
                    logger.warning(
                        f"ML processing above target: {self.metrics.avg_ml_processing_ms:.1f}ms"
                    )

            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")

    async def _cache_polling_worker(self):
        """Background worker for polling cache results"""
        while True:
            try:
                await asyncio.sleep(self.polling_interval)

                # Poll for cached intelligence updates
                # This could check for updates from other processes/workers
                # and broadcast to relevant subscribers

            except Exception as e:
                logger.error(f"Cache polling worker error: {e}")

    async def _connection_health_worker(self):
        """Background worker for connection health monitoring"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Update Redis health status
                redis_health = await get_redis_health()
                self.metrics.redis_health = redis_health.get("is_healthy", False)

                # Update connection success rate
                total_conn = self.metrics.total_connections
                active_subs = self.metrics.active_subscriptions
                if total_conn > 0:
                    self.metrics.connection_success_rate = active_subs / total_conn

            except Exception as e:
                logger.error(f"Connection health worker error: {e}")

    async def _process_event(self, event: Dict[str, Any]):
        """Process individual intelligence event"""
        try:
            # Extract event details
            lead_id = event.get("lead_id")
            tenant_id = event.get("tenant_id")
            event_data = event.get("data", {})
            priority = ProcessingPriority(event.get("priority", "medium"))

            # Handle ML event
            await self.handle_ml_event(lead_id, tenant_id, event_data, priority)

        except Exception as e:
            logger.error(f"Failed to process event: {e}")

    async def _send_connection_status(
        self,
        subscription_id: str,
        status: str
    ):
        """Send connection status update to subscriber"""
        try:
            subscription = self._subscriptions.get(subscription_id)
            if not subscription:
                return

            status_data = {
                "event_type": IntelligenceEventType.CONNECTION_STATUS.value,
                "subscription_id": subscription_id,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "topics": [t.value for t in subscription.topics]
            }

            await self.websocket_hub.broadcast_to_tenant(
                tenant_id=subscription.tenant_id,
                event_data=status_data
            )

        except Exception as e:
            logger.error(f"Failed to send connection status: {e}")

    def _serialize_intelligence_update(
        self,
        update: IntelligenceUpdate
    ) -> Dict[str, Any]:
        """Serialize intelligence update for WebSocket transmission"""
        data = {
            "event_id": update.event_id,
            "event_type": update.event_type.value,
            "tenant_id": update.tenant_id,
            "lead_id": update.lead_id,
            "timestamp": update.timestamp.isoformat(),
            "processing_time_ms": update.processing_time_ms,
            "cache_hit": update.cache_hit,
            "ml_operations": update.ml_operations,
            "broadcast_latency_ms": update.broadcast_latency_ms
        }

        # Add lead score if available
        if update.lead_score:
            data["lead_score"] = {
                "score": update.lead_score.score,
                "confidence": update.lead_score.confidence.value,
                "tier": update.lead_score.score_tier,
                "inference_time_ms": update.lead_score.inference_time_ms
            }

        # Add churn prediction if available
        if update.churn_prediction:
            data["churn_prediction"] = {
                "churn_probability": update.churn_prediction.churn_probability,
                "risk_level": update.churn_prediction.risk_level.value,
                "days_until_churn": update.churn_prediction.days_until_churn
            }

        # Add property matches if available
        if update.property_matches:
            data["property_matches"] = [
                {
                    "property_id": match.property_id,
                    "match_score": match.match_score,
                    "confidence": match.confidence
                }
                for match in update.property_matches[:3]  # Top 3 matches
            ]

        # Add overall intelligence summary
        if update.intelligence:
            data["intelligence_summary"] = {
                "overall_health_score": update.intelligence.overall_health_score,
                "priority_level": update.intelligence.priority_level.value,
                "confidence_score": update.intelligence.confidence_score
            }

        return data

    async def _cache_intelligence_update(self, update: IntelligenceUpdate):
        """Cache intelligence update for retrieval"""
        try:
            cache_key = f"intelligence_update:{update.tenant_id}:{update.lead_id}:{update.event_id}"
            cache_data = self._serialize_intelligence_update(update)

            await self.redis_client.set(
                key=cache_key,
                value=cache_data,
                ttl=self.cache_ttl
            )

        except Exception as e:
            logger.warning(f"Failed to cache intelligence update: {e}")

    async def _get_cached_intelligence(
        self,
        lead_id: str,
        tenant_id: str
    ) -> Optional[OptimizedLeadIntelligence]:
        """Get cached intelligence for a lead"""
        try:
            cache_key = f"optimized_intelligence:{lead_id}:{tenant_id}"
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                # Deserialize and return
                # Note: This would need proper deserialization logic
                return cached_data

        except Exception as e:
            logger.warning(f"Failed to get cached intelligence: {e}")

        return None

    def _is_intelligence_fresh(
        self,
        intelligence: OptimizedLeadIntelligence,
        max_age_seconds: int = 300
    ) -> bool:
        """Check if cached intelligence is still fresh"""
        age = (datetime.now() - intelligence.timestamp).total_seconds()
        return age < max_age_seconds

    async def _broadcast_specific_insights(
        self,
        tenant_id: str,
        intelligence: OptimizedLeadIntelligence
    ):
        """Broadcast specific insight events based on intelligence"""
        try:
            # Broadcast lead score update if significant
            if intelligence.lead_score and intelligence.lead_score.score > 0.7:
                await self.broadcast_intelligence_update(
                    tenant_id=tenant_id,
                    intelligence=intelligence,
                    event_type=IntelligenceEventType.LEAD_SCORE_UPDATE
                )

            # Broadcast churn risk alert if high risk
            if (intelligence.churn_prediction and
                intelligence.churn_prediction.churn_probability > 0.6):
                await self.broadcast_intelligence_update(
                    tenant_id=tenant_id,
                    intelligence=intelligence,
                    event_type=IntelligenceEventType.CHURN_RISK_ALERT
                )

            # Broadcast property match found if good matches
            if intelligence.property_matches and len(intelligence.property_matches) > 0:
                await self.broadcast_intelligence_update(
                    tenant_id=tenant_id,
                    intelligence=intelligence,
                    event_type=IntelligenceEventType.PROPERTY_MATCH_FOUND
                )

        except Exception as e:
            logger.warning(f"Failed to broadcast specific insights: {e}")

    def _update_broadcast_metrics(
        self,
        result: BroadcastResult,
        latency_ms: float
    ):
        """Update broadcast performance metrics"""
        self.metrics.total_broadcasts += 1
        self.metrics.total_updates_sent += result.connections_successful

        # Update average broadcast latency
        total_broadcasts = self.metrics.total_broadcasts
        current_avg = self.metrics.avg_broadcast_latency_ms

        self.metrics.avg_broadcast_latency_ms = (
            (current_avg * (total_broadcasts - 1) + latency_ms) / total_broadcasts
        )

    def _update_ml_processing_metrics(
        self,
        processing_time_ms: float,
        intelligence: OptimizedLeadIntelligence
    ):
        """Update ML processing performance metrics"""
        # Track processing time
        if self.metrics.total_updates_sent > 0:
            current_avg = self.metrics.avg_ml_processing_ms
            total = self.metrics.total_updates_sent

            self.metrics.avg_ml_processing_ms = (
                (current_avg * total + processing_time_ms) / (total + 1)
            )
        else:
            self.metrics.avg_ml_processing_ms = processing_time_ms

        # Track cache hit rate
        if intelligence.cache_hit_rate > 0:
            current_rate = self.metrics.cache_hit_rate
            total = self.metrics.total_updates_sent

            self.metrics.cache_hit_rate = (
                (current_rate * total + intelligence.cache_hit_rate) / (total + 1)
            )

        # Add to performance history
        self._performance_history.append({
            "timestamp": time.time(),
            "processing_time_ms": processing_time_ms,
            "cache_hit": intelligence.cache_hit_rate > 0.5
        })

        # Keep history limited to last hour
        cutoff_time = time.time() - 3600
        self._performance_history = [
            h for h in self._performance_history
            if h["timestamp"] > cutoff_time
        ]

    async def _update_performance_metrics(self):
        """Update comprehensive performance metrics"""
        try:
            # Calculate current performance indicators
            self.metrics.current_load = len(self._subscriptions) / max(
                self.max_concurrent_processing, 1
            )

            self.metrics.ml_inference_queue_depth = len(self._processing_tasks)

            # Update time-based metrics
            current_time = time.time()
            time_delta = current_time - self._last_metrics_update

            if time_delta > 0:
                recent_updates = [
                    h for h in self._performance_history
                    if h["timestamp"] > self._last_metrics_update
                ]
                self.metrics.updates_per_second = len(recent_updates) / time_delta

            self._last_metrics_update = current_time

        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")


# Global WebSocket Manager instance
_websocket_manager = None


async def get_websocket_manager() -> WebSocketManager:
    """Get singleton WebSocket Manager instance"""
    global _websocket_manager

    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
        await _websocket_manager.initialize()

    return _websocket_manager


# Convenience functions for common operations

async def subscribe_lead_intelligence(
    websocket: WebSocket,
    tenant_id: str,
    user_id: str,
    topics: Optional[List[SubscriptionTopic]] = None,
    lead_filters: Optional[List[str]] = None
) -> Optional[str]:
    """Subscribe to real-time lead intelligence updates"""
    manager = await get_websocket_manager()
    return await manager.subscribe_to_lead_intelligence(
        websocket, tenant_id, user_id, topics, lead_filters
    )


async def broadcast_lead_intelligence(
    tenant_id: str,
    intelligence: OptimizedLeadIntelligence
) -> BroadcastResult:
    """Broadcast lead intelligence update to subscribers"""
    manager = await get_websocket_manager()
    return await manager.broadcast_intelligence_update(tenant_id, intelligence)


async def process_lead_event_realtime(
    lead_id: str,
    tenant_id: str,
    event_data: Dict[str, Any],
    priority: ProcessingPriority = ProcessingPriority.MEDIUM
) -> Optional[OptimizedLeadIntelligence]:
    """Process lead event with real-time ML and broadcasting"""
    manager = await get_websocket_manager()
    return await manager.handle_ml_event(lead_id, tenant_id, event_data, priority)


__all__ = [
    "WebSocketManager",
    "IntelligenceEventType",
    "SubscriptionTopic",
    "IntelligenceSubscription",
    "IntelligenceUpdate",
    "WebSocketPerformanceMetrics",
    "get_websocket_manager",
    "subscribe_lead_intelligence",
    "broadcast_lead_intelligence",
    "process_lead_event_realtime"
]
