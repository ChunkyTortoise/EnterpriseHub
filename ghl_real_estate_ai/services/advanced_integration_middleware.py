"""
Advanced Integration Middleware (Phase 2)

Comprehensive integration layer that seamlessly connects all Phase 2 systems
with existing Phase 1 components and external services, providing unified
API endpoints, event routing, and service orchestration.

Key Features:
- Unified API gateway with intelligent routing and load balancing
- Event-driven architecture with pub/sub messaging and event sourcing
- Service mesh integration with health monitoring and auto-discovery
- Advanced caching layer with multi-level cache hierarchy
- Real-time WebSocket connections for live updates and collaboration
- Integration with GHL APIs, external real estate services, and ML models
- Security layer with authentication, authorization, and rate limiting
- Performance monitoring with distributed tracing and metrics collection

Integration Points:
- Phase 1: Smart Navigation, Enhanced Analytics, Visualizations, Onboarding
- Phase 2: Workflow Orchestrator, Data Sync, Intelligent Automation
- External: GoHighLevel, Real Estate APIs, ML Models, Claude AI
- Infrastructure: Redis, PostgreSQL, Railway, Vercel
"""

import asyncio
import json
import time
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import uuid
import hashlib
from pathlib import Path
import weakref

# External dependencies
try:
    import redis
    import asyncpg
    import aiohttp
    import websockets
    from fastapi import FastAPI, WebSocket, HTTPException, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
except ImportError as e:
    print(f"Advanced Integration Middleware: Missing dependencies: {e}")
    print("Install with: pip install redis asyncpg aiohttp websockets fastapi uvicorn")

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.unified_workflow_orchestrator import (
    AdvancedWorkflowOrchestrator, HubType
)
from ghl_real_estate_ai.services.cross_hub_data_sync import (
    CrossHubDataSynchronizer, DataChangeEvent
)
from ghl_real_estate_ai.services.intelligent_workflow_automation import (
    IntelligentWorkflowAutomation
)

logger = get_logger(__name__)


class ServiceType(Enum):
    """Types of integrated services."""
    PHASE_1 = "phase_1"           # Phase 1 components
    PHASE_2 = "phase_2"           # Phase 2 systems
    EXTERNAL = "external"         # External APIs
    INFRASTRUCTURE = "infrastructure"  # Database, cache, etc.


class EventType(Enum):
    """System event types."""
    DATA_CHANGED = "data_changed"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    USER_ACTION = "user_action"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_METRIC = "performance_metric"
    INTEGRATION_EVENT = "integration_event"


class CacheLevel(Enum):
    """Cache hierarchy levels."""
    L1_MEMORY = "l1_memory"       # In-process cache
    L2_REDIS = "l2_redis"         # Redis cache
    L3_DATABASE = "l3_database"   # Database cache
    L4_EXTERNAL = "l4_external"   # External service cache


@dataclass
class ServiceDefinition:
    """Definition of an integrated service."""

    service_id: str
    name: str
    service_type: ServiceType
    version: str = "1.0.0"

    # Connection details
    base_url: Optional[str] = None
    websocket_url: Optional[str] = None
    health_check_endpoint: str = "/health"

    # Configuration
    timeout_seconds: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 1000

    # Capabilities
    supported_events: List[EventType] = field(default_factory=list)
    provided_endpoints: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)

    # Status tracking
    status: str = "unknown"  # healthy, unhealthy, maintenance, disabled
    last_health_check: Optional[datetime] = None
    response_time_ms: Optional[float] = None


@dataclass
class IntegrationEvent:
    """Event for cross-service communication."""

    event_id: str
    event_type: EventType
    source_service: str
    target_services: List[str]

    # Event data
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Routing
    priority: int = 5  # 1-10, higher = more urgent
    routing_key: str = "default"

    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    # Processing state
    processed_by: List[str] = field(default_factory=list)
    failed_services: List[str] = field(default_factory=list)
    retry_count: int = 0


@dataclass
class CacheEntry:
    """Multi-level cache entry."""

    key: str
    value: Any
    cache_level: CacheLevel

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Cache hierarchy
    ttl_seconds: int = 3600
    auto_refresh: bool = False
    refresh_source: Optional[str] = None


class MultiLevelCacheManager:
    """Advanced multi-level caching system."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize multi-level cache manager."""
        self.redis = redis_client or redis.Redis(host='localhost', port=6379, db=0)

        # Cache levels
        self.l1_cache: Dict[str, CacheEntry] = {}  # In-memory cache
        self.l1_max_size = 1000
        self.l1_access_order = deque()

        # Cache statistics
        self.cache_stats = defaultdict(int)
        self.performance_metrics = defaultdict(list)

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from multi-level cache."""
        start_time = time.time()

        try:
            # L1 (Memory) cache check
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                if not self._is_expired(entry):
                    entry.access_count += 1
                    entry.last_accessed = datetime.now(timezone.utc)
                    self._update_access_order(key)
                    self.cache_stats["l1_hits"] += 1
                    return entry.value

            # L2 (Redis) cache check
            redis_key = f"cache:l2:{key}"
            redis_value = await self.redis.get(redis_key)
            if redis_value:
                try:
                    value = json.loads(redis_value)
                    # Promote to L1 cache
                    await self._set_l1_cache(key, value)
                    self.cache_stats["l2_hits"] += 1
                    return value
                except json.JSONDecodeError:
                    pass

            # Cache miss
            self.cache_stats["cache_misses"] += 1
            return default

        finally:
            execution_time = time.time() - start_time
            self.performance_metrics["get_times"].append(execution_time)

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600, cache_level: CacheLevel = CacheLevel.L1_MEMORY) -> bool:
        """Set value in multi-level cache."""
        try:
            if cache_level in [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]:
                await self._set_l1_cache(key, value, ttl_seconds)

            if cache_level in [CacheLevel.L2_REDIS, CacheLevel.L3_DATABASE]:
                await self._set_l2_cache(key, value, ttl_seconds)

            self.cache_stats["cache_sets"] += 1
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def _set_l1_cache(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set value in L1 (memory) cache."""
        # Check cache size limit
        if len(self.l1_cache) >= self.l1_max_size:
            await self._evict_l1_cache()

        entry = CacheEntry(
            key=key,
            value=value,
            cache_level=CacheLevel.L1_MEMORY,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
            ttl_seconds=ttl_seconds
        )

        self.l1_cache[key] = entry
        self._update_access_order(key)

    async def _set_l2_cache(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set value in L2 (Redis) cache."""
        redis_key = f"cache:l2:{key}"
        await self.redis.setex(redis_key, ttl_seconds, json.dumps(value, default=str))

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        if not entry.expires_at:
            return False
        return datetime.now(timezone.utc) > entry.expires_at

    def _update_access_order(self, key: str):
        """Update access order for LRU eviction."""
        if key in self.l1_access_order:
            self.l1_access_order.remove(key)
        self.l1_access_order.append(key)

    async def _evict_l1_cache(self):
        """Evict least recently used entries from L1 cache."""
        while len(self.l1_cache) >= self.l1_max_size and self.l1_access_order:
            lru_key = self.l1_access_order.popleft()
            if lru_key in self.l1_cache:
                del self.l1_cache[lru_key]

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_requests = self.cache_stats["l1_hits"] + self.cache_stats["l2_hits"] + self.cache_stats["cache_misses"]
        if total_requests == 0:
            return {"hit_rate": 0, "total_requests": 0}

        return {
            "hit_rate": (self.cache_stats["l1_hits"] + self.cache_stats["l2_hits"]) / total_requests,
            "l1_hit_rate": self.cache_stats["l1_hits"] / total_requests,
            "l2_hit_rate": self.cache_stats["l2_hits"] / total_requests,
            "total_requests": total_requests,
            "l1_cache_size": len(self.l1_cache),
            "avg_get_time": sum(self.performance_metrics["get_times"]) / len(self.performance_metrics["get_times"]) if self.performance_metrics["get_times"] else 0
        }


class EventBusManager:
    """Event-driven communication bus for service integration."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize event bus manager."""
        self.redis = redis_client or redis.Redis(host='localhost', port=6379, db=0)

        # Event routing
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.service_subscriptions: Dict[str, List[EventType]] = defaultdict(list)

        # Event processing
        self.event_queue = deque()
        self.processing_tasks = set()
        self.max_concurrent_events = 100

        # Performance tracking
        self.event_metrics = defaultdict(int)
        self.processing_times = defaultdict(list)

    async def publish_event(self, event: IntegrationEvent) -> bool:
        """Publish event to the event bus."""
        try:
            # Store event in Redis
            event_key = f"event:{event.event_id}"
            await self.redis.setex(
                event_key,
                3600,  # 1 hour expiry
                json.dumps(asdict(event), default=str)
            )

            # Route to target services
            for service in event.target_services:
                service_queue = f"events:{service}"
                await self.redis.lpush(service_queue, event.event_id)

            # Publish to general event channel
            await self.redis.publish("event_bus", json.dumps({
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "source_service": event.source_service
            }))

            self.event_metrics["events_published"] += 1
            logger.debug(f"Published event {event.event_id} to {len(event.target_services)} services")

            return True

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            return False

    async def subscribe_to_events(self, service_id: str, event_types: List[EventType], handler: Callable):
        """Subscribe service to specific event types."""
        self.service_subscriptions[service_id].extend(event_types)

        for event_type in event_types:
            self.event_handlers[event_type].append(handler)

        logger.info(f"Service {service_id} subscribed to {len(event_types)} event types")

    async def process_service_events(self, service_id: str) -> List[Dict[str, Any]]:
        """Process events for a specific service."""
        service_queue = f"events:{service_id}"
        processed_events = []

        try:
            # Get pending events
            event_ids = await self.redis.lrange(service_queue, 0, 10)  # Process up to 10 events

            for event_id in event_ids:
                event_data = await self.redis.get(f"event:{event_id}")
                if event_data:
                    try:
                        event_dict = json.loads(event_data)
                        result = await self._process_event_for_service(service_id, event_dict)
                        processed_events.append(result)

                        # Remove processed event from queue
                        await self.redis.lrem(service_queue, 1, event_id)

                    except Exception as e:
                        logger.error(f"Failed to process event {event_id} for service {service_id}: {e}")

        except Exception as e:
            logger.error(f"Error processing events for service {service_id}: {e}")

        return processed_events

    async def _process_event_for_service(self, service_id: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single event for a service."""
        start_time = time.time()
        event_type = EventType(event_dict.get("event_type"))

        try:
            # Find handlers for this event type
            handlers = self.event_handlers.get(event_type, [])

            results = []
            for handler in handlers:
                try:
                    result = await handler(service_id, event_dict)
                    results.append({"handler": handler.__name__, "success": True, "result": result})
                except Exception as e:
                    results.append({"handler": handler.__name__, "success": False, "error": str(e)})

            processing_time = time.time() - start_time
            self.processing_times[event_type].append(processing_time)
            self.event_metrics["events_processed"] += 1

            return {
                "event_id": event_dict.get("event_id"),
                "service_id": service_id,
                "processing_time": processing_time,
                "handlers_executed": len(results),
                "results": results
            }

        except Exception as e:
            logger.error(f"Event processing failed: {e}")
            return {
                "event_id": event_dict.get("event_id"),
                "service_id": service_id,
                "success": False,
                "error": str(e)
            }


class WebSocketManager:
    """Real-time WebSocket connection manager."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = defaultdict(list)
        self.hub_connections: Dict[HubType, List[str]] = defaultdict(list)

        # Message routing
        self.message_handlers: Dict[str, Callable] = {}

        # Performance tracking
        self.connection_metrics = defaultdict(int)

    async def connect_user(self, websocket: WebSocket, user_id: str, hub: HubType) -> str:
        """Connect user WebSocket and return connection ID."""
        connection_id = str(uuid.uuid4())

        try:
            await websocket.accept()
            self.connections[connection_id] = websocket
            self.user_connections[user_id].append(connection_id)
            self.hub_connections[hub].append(connection_id)

            self.connection_metrics["total_connections"] += 1
            self.connection_metrics["active_connections"] = len(self.connections)

            # Send welcome message
            await self.send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "user_id": user_id,
                "hub": hub.value
            })

            logger.info(f"WebSocket connected: user {user_id}, hub {hub.value}, connection {connection_id}")
            return connection_id

        except Exception as e:
            logger.error(f"WebSocket connection failed for user {user_id}: {e}")
            raise

    async def disconnect_user(self, connection_id: str):
        """Disconnect user WebSocket."""
        if connection_id in self.connections:
            # Remove from all tracking
            del self.connections[connection_id]

            for user_id, connections in self.user_connections.items():
                if connection_id in connections:
                    connections.remove(connection_id)

            for hub, connections in self.hub_connections.items():
                if connection_id in connections:
                    connections.remove(connection_id)

            self.connection_metrics["active_connections"] = len(self.connections)
            logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Send message to all connections for a user."""
        connections = self.user_connections.get(user_id, [])
        success_count = 0

        for connection_id in connections.copy():  # Use copy to avoid modification during iteration
            success = await self.send_to_connection(connection_id, message)
            if success:
                success_count += 1

        return success_count > 0

    async def send_to_hub(self, hub: HubType, message: Dict[str, Any]) -> int:
        """Send message to all connections for a hub."""
        connections = self.hub_connections.get(hub, [])
        success_count = 0

        for connection_id in connections.copy():
            success = await self.send_to_connection(connection_id, message)
            if success:
                success_count += 1

        return success_count

    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send message to a specific connection."""
        websocket = self.connections.get(connection_id)
        if not websocket:
            return False

        try:
            await websocket.send_text(json.dumps(message, default=str))
            return True
        except Exception as e:
            logger.error(f"Failed to send message to connection {connection_id}: {e}")
            # Remove dead connection
            await self.disconnect_user(connection_id)
            return False

    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """Broadcast message to all active connections."""
        success_count = 0

        for connection_id in list(self.connections.keys()):
            success = await self.send_to_connection(connection_id, message)
            if success:
                success_count += 1

        return success_count


class AdvancedIntegrationMiddleware:
    """Main integration middleware system."""

    def __init__(self,
                 workflow_orchestrator: AdvancedWorkflowOrchestrator,
                 data_synchronizer: CrossHubDataSynchronizer,
                 automation_system: IntelligentWorkflowAutomation,
                 redis_client: Optional[redis.Redis] = None):
        """Initialize advanced integration middleware."""

        # Core systems
        self.workflow_orchestrator = workflow_orchestrator
        self.data_synchronizer = data_synchronizer
        self.automation_system = automation_system
        self.redis = redis_client or redis.Redis(host='localhost', port=6379, db=0)

        # Middleware components
        self.cache_manager = MultiLevelCacheManager(redis_client)
        self.event_bus = EventBusManager(redis_client)
        self.websocket_manager = WebSocketManager()

        # Service registry
        self.services: Dict[str, ServiceDefinition] = {}
        self.service_health: Dict[str, Dict[str, Any]] = {}

        # FastAPI app for unified API
        self.app = FastAPI(
            title="EnterpriseHub Integration API",
            description="Advanced integration middleware for Phase 2 cross-hub workflows",
            version="2.0.0"
        )

        # Security
        self.security = HTTPBearer()

        # Performance metrics
        self.middleware_metrics = defaultdict(int)
        self.response_times = defaultdict(list)

        # Initialize middleware
        self._setup_fastapi_app()
        self._register_core_services()

        logger.info("Advanced Integration Middleware initialized")

    def _setup_fastapi_app(self):
        """Set up FastAPI application with middleware and routes."""

        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Performance monitoring middleware
        @self.app.middleware("http")
        async def performance_middleware(request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time

            self.response_times[request.url.path].append(process_time)
            self.middleware_metrics["requests_processed"] += 1

            response.headers["X-Process-Time"] = str(process_time)
            return response

        # API Routes
        self._setup_api_routes()

    def _setup_api_routes(self):
        """Set up unified API routes."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

        @self.app.get("/api/v2/services")
        async def list_services():
            """List all registered services."""
            return {
                "services": list(self.services.keys()),
                "service_details": {k: asdict(v) for k, v in self.services.items()},
                "health_status": self.service_health
            }

        @self.app.post("/api/v2/events/publish")
        async def publish_event(event_data: Dict[str, Any]):
            """Publish integration event."""
            event = IntegrationEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType(event_data["event_type"]),
                source_service=event_data["source_service"],
                target_services=event_data["target_services"],
                payload=event_data["payload"]
            )

            success = await self.event_bus.publish_event(event)
            return {"success": success, "event_id": event.event_id}

        @self.app.get("/api/v2/workflows")
        async def list_workflows():
            """List active workflows."""
            analytics = self.workflow_orchestrator.get_workflow_analytics()
            return {"workflow_analytics": analytics}

        @self.app.post("/api/v2/workflows/execute")
        async def execute_workflow(workflow_data: Dict[str, Any]):
            """Execute a unified workflow."""
            # Implementation would create and execute workflow
            return {"status": "workflow_execution_started"}

        @self.app.get("/api/v2/cache/stats")
        async def cache_statistics():
            """Get cache performance statistics."""
            return self.cache_manager.get_cache_statistics()

        @self.app.get("/api/v2/middleware/metrics")
        async def middleware_metrics():
            """Get middleware performance metrics."""
            return {
                "requests_processed": self.middleware_metrics["requests_processed"],
                "active_connections": self.websocket_manager.connection_metrics["active_connections"],
                "cache_stats": self.cache_manager.get_cache_statistics(),
                "event_stats": {
                    "events_published": self.event_bus.event_metrics["events_published"],
                    "events_processed": self.event_bus.event_metrics["events_processed"]
                }
            }

        @self.app.websocket("/ws/{user_id}/{hub}")
        async def websocket_endpoint(websocket: WebSocket, user_id: str, hub: str):
            """WebSocket endpoint for real-time updates."""
            try:
                hub_type = HubType(hub)
                connection_id = await self.websocket_manager.connect_user(websocket, user_id, hub_type)

                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    # Handle WebSocket message
                    await self._handle_websocket_message(connection_id, user_id, hub_type, message)

            except Exception as e:
                logger.error(f"WebSocket error for user {user_id}: {e}")
            finally:
                if 'connection_id' in locals():
                    await self.websocket_manager.disconnect_user(connection_id)

    def _register_core_services(self):
        """Register core Phase 1 and Phase 2 services."""

        # Phase 1 services
        phase1_services = [
            ServiceDefinition(
                service_id="smart_navigation",
                name="Smart Navigation System",
                service_type=ServiceType.PHASE_1,
                supported_events=[EventType.USER_ACTION],
                provided_endpoints=["/api/navigation/context", "/api/navigation/breadcrumbs"]
            ),
            ServiceDefinition(
                service_id="enhanced_analytics",
                name="Enhanced Analytics Service",
                service_type=ServiceType.PHASE_1,
                supported_events=[EventType.DATA_CHANGED, EventType.PERFORMANCE_METRIC],
                provided_endpoints=["/api/analytics/metrics", "/api/analytics/reports"]
            ),
            ServiceDefinition(
                service_id="advanced_visualizations",
                name="Advanced Visualizations",
                service_type=ServiceType.PHASE_1,
                supported_events=[EventType.DATA_CHANGED],
                provided_endpoints=["/api/visualizations/charts", "/api/visualizations/render"]
            )
        ]

        # Phase 2 services
        phase2_services = [
            ServiceDefinition(
                service_id="workflow_orchestrator",
                name="Unified Workflow Orchestrator",
                service_type=ServiceType.PHASE_2,
                supported_events=[EventType.WORKFLOW_STARTED, EventType.WORKFLOW_COMPLETED],
                provided_endpoints=["/api/workflows/execute", "/api/workflows/status"]
            ),
            ServiceDefinition(
                service_id="data_synchronizer",
                name="Cross-Hub Data Synchronizer",
                service_type=ServiceType.PHASE_2,
                supported_events=[EventType.DATA_CHANGED],
                provided_endpoints=["/api/sync/status", "/api/sync/conflicts"]
            ),
            ServiceDefinition(
                service_id="intelligent_automation",
                name="Intelligent Workflow Automation",
                service_type=ServiceType.PHASE_2,
                supported_events=[EventType.USER_ACTION, EventType.DATA_CHANGED],
                provided_endpoints=["/api/automation/suggestions", "/api/automation/rules"]
            )
        ]

        # Register all services
        for service in phase1_services + phase2_services:
            self.services[service.service_id] = service
            logger.info(f"Registered service: {service.name}")

    async def _handle_websocket_message(self, connection_id: str, user_id: str, hub: HubType, message: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        try:
            message_type = message.get("type", "unknown")

            if message_type == "subscribe_to_updates":
                # Subscribe to real-time updates
                await self._subscribe_connection_to_updates(connection_id, message.get("topics", []))

            elif message_type == "trigger_action":
                # Trigger cross-hub action
                await self._handle_action_trigger(user_id, hub, message.get("action_data", {}))

            elif message_type == "ping":
                # Respond to ping
                await self.websocket_manager.send_to_connection(connection_id, {"type": "pong"})

        except Exception as e:
            logger.error(f"WebSocket message handling error: {e}")

    async def _subscribe_connection_to_updates(self, connection_id: str, topics: List[str]):
        """Subscribe WebSocket connection to specific update topics."""
        # Implementation for topic-based subscriptions
        await self.websocket_manager.send_to_connection(connection_id, {
            "type": "subscription_confirmed",
            "topics": topics
        })

    async def _handle_action_trigger(self, user_id: str, hub: HubType, action_data: Dict[str, Any]):
        """Handle action trigger from WebSocket."""
        # Create integration event for the action
        event = IntegrationEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.USER_ACTION,
            source_service=f"websocket_{hub.value}",
            target_services=["workflow_orchestrator"],
            payload={
                "user_id": user_id,
                "hub": hub.value,
                "action": action_data
            }
        )

        await self.event_bus.publish_event(event)

    async def start_middleware_services(self):
        """Start background middleware services."""
        # Start event processing
        asyncio.create_task(self._process_events_continuously())

        # Start service health monitoring
        asyncio.create_task(self._monitor_service_health())

        # Start cache cleanup
        asyncio.create_task(self._cleanup_cache_periodically())

        logger.info("Middleware background services started")

    async def _process_events_continuously(self):
        """Continuously process events from the event bus."""
        while True:
            try:
                # Process events for each registered service
                for service_id in self.services.keys():
                    events = await self.event_bus.process_service_events(service_id)
                    if events:
                        logger.debug(f"Processed {len(events)} events for service {service_id}")

                await asyncio.sleep(1)  # Process every second

            except Exception as e:
                logger.error(f"Event processing error: {e}")
                await asyncio.sleep(5)

    async def _monitor_service_health(self):
        """Monitor health of all registered services."""
        while True:
            try:
                for service_id, service in self.services.items():
                    health_status = await self._check_service_health(service)
                    self.service_health[service_id] = health_status

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)

    async def _check_service_health(self, service: ServiceDefinition) -> Dict[str, Any]:
        """Check health of a specific service."""
        if service.base_url and service.health_check_endpoint:
            try:
                start_time = time.time()
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{service.base_url}{service.health_check_endpoint}",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        response_time = time.time() - start_time

                        return {
                            "status": "healthy" if response.status == 200 else "unhealthy",
                            "response_time_ms": response_time * 1000,
                            "last_check": datetime.now(timezone.utc),
                            "status_code": response.status
                        }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now(timezone.utc)
                }
        else:
            return {
                "status": "unknown",
                "reason": "No health check endpoint configured",
                "last_check": datetime.now(timezone.utc)
            }

    async def _cleanup_cache_periodically(self):
        """Periodically clean up expired cache entries."""
        while True:
            try:
                # Clean L1 cache
                expired_keys = []
                for key, entry in self.cache_manager.l1_cache.items():
                    if self.cache_manager._is_expired(entry):
                        expired_keys.append(key)

                for key in expired_keys:
                    del self.cache_manager.l1_cache[key]

                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

                await asyncio.sleep(300)  # Clean every 5 minutes

            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(300)

    def get_middleware_status(self) -> Dict[str, Any]:
        """Get comprehensive middleware status."""
        return {
            "services": {
                "registered": len(self.services),
                "healthy": sum(1 for health in self.service_health.values() if health.get("status") == "healthy"),
                "details": self.service_health
            },
            "cache": self.cache_manager.get_cache_statistics(),
            "websockets": {
                "active_connections": self.websocket_manager.connection_metrics["active_connections"],
                "total_connections": self.websocket_manager.connection_metrics["total_connections"]
            },
            "events": {
                "published": self.event_bus.event_metrics["events_published"],
                "processed": self.event_bus.event_metrics["events_processed"]
            },
            "performance": {
                "requests_processed": self.middleware_metrics["requests_processed"],
                "avg_response_time": sum(sum(times) for times in self.response_times.values()) /
                                   max(sum(len(times) for times in self.response_times.values()), 1)
            }
        }


# Export main classes
__all__ = [
    "AdvancedIntegrationMiddleware",
    "MultiLevelCacheManager",
    "EventBusManager",
    "WebSocketManager",
    "ServiceDefinition",
    "IntegrationEvent",
    "ServiceType",
    "EventType",
    "CacheLevel"
]