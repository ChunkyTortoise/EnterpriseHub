"""
Event Bus Integration for Real-Time Lead Intelligence

Orchestrates parallel ML processing and WebSocket broadcasting with event-driven architecture.
Connects optimized ML engines to the WebSocket Manager for real-time lead intelligence streaming.

Key Features:
- Parallel ML inference coordination (Lead Score + Churn + Property Matches)
- Event-driven architecture with async queue processing
- Redis-backed caching with 500ms polling interval
- WebSocket Manager integration for real-time broadcasting
- Performance monitoring and health checks
- Multi-tenant event isolation

Performance Targets:
- Event processing: <100ms end-to-end
- ML coordination: <40ms (leverages OptimizedMLLeadIntelligenceEngine's <35ms target)
- Cache polling: 500ms interval
- WebSocket broadcast: <50ms latency
- Queue processing: 5000+ events/second capacity

Architecture:
- Integrates with OptimizedMLLeadIntelligenceEngine for <35ms inference
- Uses RealtimeLeadScoringService for <100ms scoring
- Connects to WebSocketManager for real-time broadcasting
- Redis caching for performance optimization
- Event queue for async processing coordination
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable, Tuple
from enum import Enum
from collections import defaultdict, deque

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
    ChurnRiskLevel,
    get_churn_prediction_service
)
from ghl_real_estate_ai.services.enhanced_property_matcher_ml import (
    EnhancedPropertyMatch,
    get_enhanced_property_matcher
)
try:
    from ghl_real_estate_ai.services.websocket_manager import (
        WebSocketManager,
        IntelligenceEventType,
        get_websocket_manager
    )
except ImportError:
    # WebSocket Manager may not be available in all environments
    WebSocketManager = None
    IntelligenceEventType = None
    get_websocket_manager = None
from ghl_real_estate_ai.database.redis_client import redis_client, get_redis_health
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class EventType(Enum):
    """Event types for ML processing coordination"""
    LEAD_CREATED = "lead_created"
    LEAD_UPDATED = "lead_updated"
    INTERACTION_RECORDED = "interaction_recorded"
    PROPERTY_VIEWED = "property_viewed"
    SCORE_REFRESH_REQUESTED = "score_refresh_requested"
    CHURN_CHECK_REQUESTED = "churn_check_requested"
    SYSTEM_HEALTH_CHECK = "system_health_check"


class EventPriority(Enum):
    """Event processing priority levels"""
    CRITICAL = 1  # <20ms target
    HIGH = 2      # <40ms target
    MEDIUM = 3    # <100ms target
    LOW = 4       # <200ms target


@dataclass
class MLEvent:
    """ML processing event with metadata"""
    event_id: str
    event_type: EventType
    tenant_id: str
    lead_id: str
    event_data: Dict[str, Any]
    priority: EventPriority
    timestamp: datetime

    # Processing metadata
    processing_started: Optional[datetime] = None
    processing_completed: Optional[datetime] = None
    processing_time_ms: float = 0.0

    # ML processing flags
    requires_scoring: bool = True
    requires_churn_prediction: bool = True
    requires_property_matching: bool = True

    # Result tracking
    intelligence_result: Optional[OptimizedLeadIntelligence] = None
    broadcast_result: Optional[Dict[str, Any]] = None

    # Error handling
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None


@dataclass
class EventBusMetrics:
    """Event bus performance tracking"""
    total_events_processed: int = 0
    successful_events: int = 0
    failed_events: int = 0
    avg_processing_time_ms: float = 0.0
    avg_ml_coordination_ms: float = 0.0
    avg_broadcast_latency_ms: float = 0.0

    # Queue metrics
    current_queue_depth: int = 0
    max_queue_depth: int = 0
    events_per_second: float = 0.0

    # Performance distribution
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0

    # Cache performance
    cache_hit_rate: float = 0.0
    cache_polling_interval_ms: float = 500.0

    # Health indicators
    is_healthy: bool = True
    redis_healthy: bool = True
    websocket_healthy: bool = True
    ml_engine_healthy: bool = True

    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class EventBus:
    """
    Event Bus Integration for Real-Time Lead Intelligence.

    Orchestrates parallel ML processing and coordinates with WebSocket Manager
    for real-time intelligence broadcasting.

    Key Features:
    - Parallel ML inference coordination
    - Event-driven async queue processing
    - Redis-backed caching with 500ms polling
    - WebSocket broadcasting integration
    - Performance monitoring and health checks
    - Multi-tenant event isolation
    """

    def __init__(
        self,
        ml_engine: Optional[OptimizedMLLeadIntelligenceEngine] = None,
        websocket_manager: Optional[WebSocketManager] = None,
        scoring_service: Optional[RealtimeLeadScoringService] = None
    ):
        """
        Initialize Event Bus.

        Args:
            ml_engine: Optimized ML intelligence engine (uses singleton if None)
            websocket_manager: WebSocket manager (uses singleton if None)
            scoring_service: Real-time lead scoring service (uses singleton if None)
        """
        # Core services (initialized asynchronously)
        self.ml_engine = ml_engine
        self.websocket_manager = websocket_manager
        self.scoring_service = scoring_service
        self.churn_service = None
        self.property_matcher = None

        # Redis client for caching
        self.redis_client = redis_client

        # Event processing infrastructure
        self._event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=5000)
        self._processing_tasks: Set[asyncio.Task] = set()
        self._active_events: Dict[str, MLEvent] = {}

        # Cache polling infrastructure
        self._cache_poll_interval = 0.5  # 500ms polling interval
        self._cached_results: Dict[str, OptimizedLeadIntelligence] = {}
        self._cache_subscribers: Dict[str, Set[str]] = defaultdict(set)  # lead_id -> event_ids

        # Performance tracking
        self.metrics = EventBusMetrics()
        self._performance_history = deque(maxlen=10000)
        self._last_metrics_update = time.time()

        # Event handlers registry
        self._event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)

        # Configuration
        self.max_concurrent_processing = 100
        self.processing_timeout = 30  # seconds
        self.cache_ttl = 300  # 5 minutes
        self.polling_interval = 0.5  # 500ms for cache polling

        # Background workers
        self._workers_started = False
        self._worker_tasks: List[asyncio.Task] = []

        # Health monitoring
        self._last_health_check = time.time()
        self._health_check_interval = 30  # seconds

        logger.info("Event Bus initialized")

    async def initialize(self):
        """Initialize Event Bus with all dependencies"""
        try:
            # Initialize core services if not provided
            if self.ml_engine is None:
                self.ml_engine = await get_optimized_ml_intelligence_engine()

            if self.websocket_manager is None:
                self.websocket_manager = await get_websocket_manager()

            if self.scoring_service is None:
                self.scoring_service = await get_lead_scoring_service()

            # Initialize supporting services
            self.churn_service = get_churn_prediction_service()
            self.property_matcher = get_enhanced_property_matcher()

            # Initialize Redis connection
            await self.redis_client.initialize()

            # Start background workers
            await self._start_background_workers()

            # Register default event handlers
            self._register_default_handlers()

            logger.info("Event Bus initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Event Bus: {e}")
            raise

    async def publish_event(
        self,
        event_type: EventType,
        tenant_id: str,
        lead_id: str,
        event_data: Dict[str, Any],
        priority: EventPriority = EventPriority.MEDIUM
    ) -> str:
        """
        Publish event to the bus for async processing.

        Args:
            event_type: Type of event
            tenant_id: Tenant identifier for isolation
            lead_id: Lead identifier
            event_data: Event payload data
            priority: Processing priority level

        Returns:
            Event ID for tracking
        """
        event_id = f"evt_{uuid.uuid4().hex[:12]}"

        try:
            # Create ML event
            event = MLEvent(
                event_id=event_id,
                event_type=event_type,
                tenant_id=tenant_id,
                lead_id=lead_id,
                event_data=event_data,
                priority=priority,
                timestamp=datetime.now()
            )

            # Determine ML processing requirements based on event type
            self._configure_ml_requirements(event)

            # Add to priority queue (lower priority value = higher priority)
            await self._event_queue.put((priority.value, time.time(), event))

            # Track active event
            self._active_events[event_id] = event

            # Update metrics
            self.metrics.current_queue_depth = self._event_queue.qsize()
            self.metrics.max_queue_depth = max(
                self.metrics.max_queue_depth,
                self.metrics.current_queue_depth
            )

            logger.debug(f"Event published: {event_id} (type: {event_type.value}, "
                        f"priority: {priority.value}, lead: {lead_id})")

            return event_id

        except asyncio.QueueFull:
            logger.error(f"Event queue full, rejecting event for lead {lead_id}")
            raise RuntimeError("Event queue is full, please retry")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise

    async def process_lead_event(
        self,
        lead_id: str,
        tenant_id: str,
        event_data: Dict[str, Any],
        priority: ProcessingPriority = ProcessingPriority.MEDIUM,
        broadcast: bool = True
    ) -> Optional[OptimizedLeadIntelligence]:
        """
        Process lead event with parallel ML inference and optional broadcasting.

        This is the main entry point for synchronous event processing.

        Args:
            lead_id: Lead identifier
            tenant_id: Tenant identifier
            event_data: Lead event data
            priority: Processing priority level
            broadcast: Whether to broadcast to WebSocket subscribers

        Returns:
            OptimizedLeadIntelligence if successful, None otherwise
        """
        start_time = time.time()

        try:
            # Check cache first
            cached_intelligence = await self._get_cached_intelligence(lead_id, tenant_id)
            if cached_intelligence and self._is_intelligence_fresh(cached_intelligence):
                logger.debug(f"Using cached intelligence for lead {lead_id}")

                if broadcast:
                    await self._broadcast_intelligence(tenant_id, cached_intelligence)

                self.metrics.cache_hit_rate = self._update_cache_hit_rate(True)
                return cached_intelligence

            self.metrics.cache_hit_rate = self._update_cache_hit_rate(False)

            # Process with optimized ML engine (parallel ML inference)
            intelligence = await self.ml_engine.process_lead_event_optimized(
                lead_id=lead_id,
                event_data=event_data,
                priority=priority
            )

            # Cache the result
            await self._cache_intelligence(lead_id, tenant_id, intelligence)

            # Broadcast to WebSocket subscribers if requested
            if broadcast:
                await self._broadcast_intelligence(tenant_id, intelligence)

            # Update performance metrics
            processing_time = (time.time() - start_time) * 1000
            await self._update_processing_metrics(processing_time, intelligence)

            # Track successful processing
            self.metrics.successful_events += 1
            self.metrics.total_events_processed += 1

            logger.info(f"Lead event processed: {lead_id} (processing_time: {processing_time:.1f}ms, "
                       f"score: {intelligence.lead_score.score if intelligence.lead_score else 'N/A'})")

            return intelligence

        except Exception as e:
            logger.error(f"Failed to process lead event for {lead_id}: {e}")
            self.metrics.failed_events += 1
            self.metrics.total_events_processed += 1
            return None

    async def subscribe_to_ml_events(
        self,
        event_types: List[EventType],
        handler: Callable[[MLEvent, OptimizedLeadIntelligence], None]
    ):
        """
        Subscribe to ML event results with custom handler.

        Args:
            event_types: List of event types to subscribe to
            handler: Async callback function to handle events
        """
        for event_type in event_types:
            self._event_handlers[event_type].append(handler)

        logger.info(f"Subscribed to ML events: {[et.value for et in event_types]}")

    async def publish_intelligence_update(
        self,
        tenant_id: str,
        intelligence_data: OptimizedLeadIntelligence,
        event_type: IntelligenceEventType = IntelligenceEventType.INTELLIGENCE_COMPLETE
    ):
        """
        Publish intelligence update to WebSocket Manager for broadcasting.

        Args:
            tenant_id: Tenant identifier
            intelligence_data: Optimized lead intelligence data
            event_type: Type of intelligence event
        """
        start_time = time.time()

        try:
            # Broadcast through WebSocket Manager
            result = await self.websocket_manager.broadcast_intelligence_update(
                tenant_id=tenant_id,
                intelligence=intelligence_data,
                event_type=event_type
            )

            # Update broadcast metrics
            broadcast_latency = (time.time() - start_time) * 1000
            self._update_broadcast_metrics(broadcast_latency)

            logger.debug(f"Intelligence update published: {intelligence_data.lead_id} "
                        f"(broadcast_latency: {broadcast_latency:.1f}ms, "
                        f"recipients: {result.connections_successful}/{result.connections_targeted})")

        except Exception as e:
            logger.error(f"Failed to publish intelligence update: {e}")
            raise

    async def get_event_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get processing status for a specific event.

        Args:
            event_id: Event identifier

        Returns:
            Event status dictionary or None if not found
        """
        event = self._active_events.get(event_id)
        if not event:
            # Check if it's been cached/completed
            return await self._get_completed_event_status(event_id)

        return {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "tenant_id": event.tenant_id,
            "lead_id": event.lead_id,
            "priority": event.priority.value,
            "timestamp": event.timestamp.isoformat(),
            "processing_started": event.processing_started.isoformat() if event.processing_started else None,
            "processing_completed": event.processing_completed.isoformat() if event.processing_completed else None,
            "processing_time_ms": event.processing_time_ms,
            "status": "processing" if event.processing_started and not event.processing_completed else "queued",
            "retry_count": event.retry_count,
            "last_error": event.last_error
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive event bus performance metrics.

        Returns:
            Performance metrics dictionary
        """
        try:
            # Calculate recent performance statistics
            recent_history = list(self._performance_history)[-100:]

            if recent_history:
                processing_times = [h['processing_time_ms'] for h in recent_history]
                import numpy as np

                self.metrics.p50_latency_ms = np.percentile(processing_times, 50)
                self.metrics.p95_latency_ms = np.percentile(processing_times, 95)
                self.metrics.p99_latency_ms = np.percentile(processing_times, 99)

            # Get Redis health
            redis_health = await get_redis_health()
            self.metrics.redis_healthy = redis_health.get("is_healthy", False)

            # Get WebSocket Manager health
            ws_health = await self.websocket_manager.get_connection_health()
            self.metrics.websocket_healthy = ws_health.get("performance_status", {}).get("overall_healthy", False)

            # Get ML Engine metrics
            ml_metrics = await self.ml_engine.get_optimization_metrics()
            self.metrics.ml_engine_healthy = ml_metrics.get("optimization_status", {}).get("target_achievement", False)

            # Overall health status
            self.metrics.is_healthy = (
                self.metrics.redis_healthy and
                self.metrics.websocket_healthy and
                self.metrics.ml_engine_healthy and
                self.metrics.avg_processing_time_ms < 100
            )

            # Calculate events per second
            current_time = time.time()
            time_delta = current_time - self._last_metrics_update
            if time_delta > 0:
                recent_events = [
                    h for h in self._performance_history
                    if h['timestamp'] > self._last_metrics_update
                ]
                self.metrics.events_per_second = len(recent_events) / time_delta

            self._last_metrics_update = current_time
            self.metrics.last_updated = datetime.now()

            return {
                **asdict(self.metrics),
                "performance_targets": {
                    "event_processing_target_ms": 100,
                    "ml_coordination_target_ms": 40,
                    "cache_polling_interval_ms": 500,
                    "broadcast_latency_target_ms": 50,
                    "queue_capacity": 5000
                },
                "performance_status": {
                    "processing_time_ok": self.metrics.avg_processing_time_ms < 100,
                    "ml_coordination_ok": self.metrics.avg_ml_coordination_ms < 40,
                    "broadcast_latency_ok": self.metrics.avg_broadcast_latency_ms < 50,
                    "queue_healthy": self.metrics.current_queue_depth < 4500,
                    "overall_healthy": self.metrics.is_healthy
                }
            }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # Internal helper methods

    def _configure_ml_requirements(self, event: MLEvent):
        """Configure ML processing requirements based on event type"""
        event_type = event.event_type

        # All events require scoring by default
        event.requires_scoring = True

        # Configure based on event type
        if event_type == EventType.LEAD_CREATED:
            event.requires_churn_prediction = True
            event.requires_property_matching = True
        elif event_type == EventType.LEAD_UPDATED:
            event.requires_churn_prediction = True
            event.requires_property_matching = False
        elif event_type == EventType.INTERACTION_RECORDED:
            event.requires_churn_prediction = True
            event.requires_property_matching = False
        elif event_type == EventType.PROPERTY_VIEWED:
            event.requires_churn_prediction = False
            event.requires_property_matching = True
        elif event_type == EventType.SCORE_REFRESH_REQUESTED:
            event.requires_churn_prediction = False
            event.requires_property_matching = False
        elif event_type == EventType.CHURN_CHECK_REQUESTED:
            event.requires_churn_prediction = True
            event.requires_property_matching = False

    async def _get_cached_intelligence(
        self,
        lead_id: str,
        tenant_id: str
    ) -> Optional[OptimizedLeadIntelligence]:
        """Get cached intelligence from Redis"""
        try:
            cache_key = f"intelligence:{tenant_id}:{lead_id}"
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                # Check in-memory cache first
                if lead_id in self._cached_results:
                    return self._cached_results[lead_id]

                # TODO: Deserialize from Redis
                # For now, return None and let it be regenerated
                return None

        except Exception as e:
            logger.warning(f"Failed to get cached intelligence: {e}")

        return None

    async def _cache_intelligence(
        self,
        lead_id: str,
        tenant_id: str,
        intelligence: OptimizedLeadIntelligence
    ):
        """Cache intelligence in Redis and in-memory"""
        try:
            # Store in in-memory cache
            self._cached_results[lead_id] = intelligence

            # Store in Redis
            cache_key = f"intelligence:{tenant_id}:{lead_id}"
            cache_data = {
                "lead_id": lead_id,
                "tenant_id": tenant_id,
                "timestamp": intelligence.timestamp.isoformat(),
                "processing_time_ms": intelligence.processing_time_ms,
                "cache_hit_rate": intelligence.cache_hit_rate,
                # Add serialized intelligence data as needed
            }

            await self.redis_client.set(
                key=cache_key,
                value=cache_data,
                ttl=self.cache_ttl
            )

        except Exception as e:
            logger.warning(f"Failed to cache intelligence: {e}")

    def _is_intelligence_fresh(
        self,
        intelligence: OptimizedLeadIntelligence,
        max_age_seconds: int = 300
    ) -> bool:
        """Check if cached intelligence is still fresh"""
        age = (datetime.now() - intelligence.timestamp).total_seconds()
        return age < max_age_seconds

    async def _broadcast_intelligence(
        self,
        tenant_id: str,
        intelligence: OptimizedLeadIntelligence
    ):
        """Broadcast intelligence through WebSocket Manager"""
        try:
            await self.websocket_manager.broadcast_intelligence_update(
                tenant_id=tenant_id,
                intelligence=intelligence
            )
        except Exception as e:
            logger.error(f"Failed to broadcast intelligence: {e}")

    def _update_cache_hit_rate(self, is_hit: bool) -> float:
        """Update cache hit rate metric"""
        total_events = self.metrics.total_events_processed or 1
        current_hits = self.metrics.cache_hit_rate * total_events

        if is_hit:
            current_hits += 1

        return current_hits / (total_events + 1)

    async def _update_processing_metrics(
        self,
        processing_time_ms: float,
        intelligence: OptimizedLeadIntelligence
    ):
        """Update processing performance metrics"""
        # Update average processing time
        total = self.metrics.total_events_processed or 1
        current_avg = self.metrics.avg_processing_time_ms

        self.metrics.avg_processing_time_ms = (
            (current_avg * (total - 1) + processing_time_ms) / total
        )

        # Update ML coordination time
        self.metrics.avg_ml_coordination_ms = (
            (self.metrics.avg_ml_coordination_ms * (total - 1) + intelligence.processing_time_ms) / total
        )

        # Add to performance history
        self._performance_history.append({
            "timestamp": time.time(),
            "processing_time_ms": processing_time_ms,
            "ml_coordination_ms": intelligence.processing_time_ms,
            "cache_hit": intelligence.cache_hit_rate > 0.5
        })

    def _update_broadcast_metrics(self, broadcast_latency_ms: float):
        """Update broadcast performance metrics"""
        total = self.metrics.total_events_processed or 1
        current_avg = self.metrics.avg_broadcast_latency_ms

        self.metrics.avg_broadcast_latency_ms = (
            (current_avg * (total - 1) + broadcast_latency_ms) / total
        )

    def _register_default_handlers(self):
        """Register default event handlers"""
        # Default handler logs event completion
        async def log_event_completion(event: MLEvent, intelligence: OptimizedLeadIntelligence):
            logger.info(f"Event completed: {event.event_id} (lead: {event.lead_id}, "
                       f"processing_time: {event.processing_time_ms:.1f}ms)")

        # Register for all event types
        for event_type in EventType:
            self._event_handlers[event_type].append(log_event_completion)

    async def _start_background_workers(self):
        """Start background worker tasks"""
        if self._workers_started:
            return

        # Event processing worker
        event_worker = asyncio.create_task(self._event_processing_worker())
        self._worker_tasks.append(event_worker)

        # Cache polling worker
        cache_worker = asyncio.create_task(self._cache_polling_worker())
        self._worker_tasks.append(cache_worker)

        # Performance monitoring worker
        metrics_worker = asyncio.create_task(self._performance_monitoring_worker())
        self._worker_tasks.append(metrics_worker)

        # Health check worker
        health_worker = asyncio.create_task(self._health_check_worker())
        self._worker_tasks.append(health_worker)

        self._workers_started = True
        logger.info("Event Bus background workers started")

    async def _event_processing_worker(self):
        """Background worker for processing events from queue"""
        while True:
            try:
                # Get event from priority queue (with timeout)
                priority, timestamp, event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )

                # Create processing task
                task = asyncio.create_task(self._process_event(event))
                self._processing_tasks.add(task)
                task.add_done_callback(self._processing_tasks.discard)

                # Update queue depth
                self.metrics.current_queue_depth = self._event_queue.qsize()

                # Limit concurrent processing
                if len(self._processing_tasks) >= self.max_concurrent_processing:
                    await asyncio.sleep(0.01)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing worker error: {e}")
                await asyncio.sleep(1)

    async def _process_event(self, event: MLEvent):
        """Process individual ML event"""
        event.processing_started = datetime.now()
        start_time = time.time()

        try:
            # Map event priority to processing priority
            processing_priority = self._map_event_priority(event.priority)

            # Process lead event with ML engine
            intelligence = await self.process_lead_event(
                lead_id=event.lead_id,
                tenant_id=event.tenant_id,
                event_data=event.event_data,
                priority=processing_priority,
                broadcast=True
            )

            # Update event with results
            event.intelligence_result = intelligence
            event.processing_completed = datetime.now()
            event.processing_time_ms = (time.time() - start_time) * 1000

            # Call registered event handlers
            await self._notify_event_handlers(event, intelligence)

            # Remove from active events
            self._active_events.pop(event.event_id, None)

        except Exception as e:
            logger.error(f"Failed to process event {event.event_id}: {e}")
            event.last_error = str(e)
            event.retry_count += 1

            # Retry if not exceeded max retries
            if event.retry_count < event.max_retries:
                await self._event_queue.put((event.priority.value, time.time(), event))
            else:
                logger.error(f"Event {event.event_id} failed after {event.max_retries} retries")
                self._active_events.pop(event.event_id, None)

    async def _cache_polling_worker(self):
        """Background worker for polling cache results"""
        while True:
            try:
                await asyncio.sleep(self.polling_interval)

                # Poll for cached intelligence updates
                # This checks for updates from other processes/workers
                # and notifies subscribers

                for lead_id, subscriber_event_ids in list(self._cache_subscribers.items()):
                    if not subscriber_event_ids:
                        continue

                    # Check cache for updates
                    # (Implementation would check Redis for new intelligence)

            except Exception as e:
                logger.error(f"Cache polling worker error: {e}")

    async def _performance_monitoring_worker(self):
        """Background worker for performance monitoring"""
        while True:
            try:
                await asyncio.sleep(10)  # Monitor every 10 seconds

                # Update comprehensive metrics
                await self.get_performance_metrics()

                # Log performance warnings
                if self.metrics.avg_processing_time_ms > 100:
                    logger.warning(
                        f"Processing time above target: {self.metrics.avg_processing_time_ms:.1f}ms"
                    )

                if self.metrics.current_queue_depth > 4000:
                    logger.warning(
                        f"Queue depth high: {self.metrics.current_queue_depth}/5000"
                    )

            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")

    async def _health_check_worker(self):
        """Background worker for system health checks"""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)

                # Check component health
                redis_health = await get_redis_health()
                self.metrics.redis_healthy = redis_health.get("is_healthy", False)

                # Update overall health status
                self.metrics.is_healthy = (
                    self.metrics.redis_healthy and
                    self.metrics.websocket_healthy and
                    self.metrics.ml_engine_healthy
                )

                if not self.metrics.is_healthy:
                    logger.warning(
                        f"Event Bus health degraded: "
                        f"Redis={self.metrics.redis_healthy}, "
                        f"WebSocket={self.metrics.websocket_healthy}, "
                        f"ML Engine={self.metrics.ml_engine_healthy}"
                    )

            except Exception as e:
                logger.error(f"Health check worker error: {e}")

    def _map_event_priority(self, event_priority: EventPriority) -> ProcessingPriority:
        """Map event priority to ML processing priority"""
        mapping = {
            EventPriority.CRITICAL: ProcessingPriority.CRITICAL,
            EventPriority.HIGH: ProcessingPriority.HIGH,
            EventPriority.MEDIUM: ProcessingPriority.MEDIUM,
            EventPriority.LOW: ProcessingPriority.LOW
        }
        return mapping.get(event_priority, ProcessingPriority.MEDIUM)

    async def _notify_event_handlers(self, event: MLEvent, intelligence: OptimizedLeadIntelligence):
        """Notify all registered event handlers"""
        handlers = self._event_handlers.get(event.event_type, [])

        for handler in handlers:
            try:
                await handler(event, intelligence)
            except Exception as e:
                logger.error(f"Event handler error for {event.event_id}: {e}")

    async def _get_completed_event_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get status for completed event from cache"""
        try:
            cache_key = f"event_status:{event_id}"
            cached_status = await self.redis_client.get(cache_key)

            if cached_status:
                return cached_status

        except Exception as e:
            logger.warning(f"Failed to get completed event status: {e}")

        return None


# Global Event Bus instance
_event_bus = None


async def get_event_bus() -> EventBus:
    """Get singleton Event Bus instance"""
    global _event_bus

    if _event_bus is None:
        _event_bus = EventBus()
        await _event_bus.initialize()

    return _event_bus


# Convenience functions for common operations

async def publish_lead_event(
    event_type: EventType,
    tenant_id: str,
    lead_id: str,
    event_data: Dict[str, Any],
    priority: EventPriority = EventPriority.MEDIUM
) -> str:
    """Publish lead event to Event Bus"""
    bus = await get_event_bus()
    return await bus.publish_event(event_type, tenant_id, lead_id, event_data, priority)


async def process_lead_intelligence(
    lead_id: str,
    tenant_id: str,
    event_data: Dict[str, Any],
    priority: ProcessingPriority = ProcessingPriority.MEDIUM
) -> Optional[OptimizedLeadIntelligence]:
    """Process lead intelligence with ML coordination and broadcasting"""
    bus = await get_event_bus()
    return await bus.process_lead_event(lead_id, tenant_id, event_data, priority)


async def subscribe_to_intelligence_events(
    event_types: List[EventType],
    handler: Callable[[MLEvent, OptimizedLeadIntelligence], None]
):
    """Subscribe to intelligence event results"""
    bus = await get_event_bus()
    await bus.subscribe_to_ml_events(event_types, handler)


__all__ = [
    "EventBus",
    "EventType",
    "EventPriority",
    "MLEvent",
    "EventBusMetrics",
    "get_event_bus",
    "publish_lead_event",
    "process_lead_intelligence",
    "subscribe_to_intelligence_events"
]
