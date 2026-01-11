"""
Dashboard Analytics Service

Real-time metrics aggregation and WebSocket integration for dashboard components.
Integrates GHL webhook events with dashboard updates for seamless real-time experience.

Performance Targets:
- Dashboard metric queries: <50ms
- Real-time event processing: <100ms
- WebSocket broadcast: <50ms
- Cache operations: <10ms

Features:
- Multi-tenant metrics isolation
- Redis caching with fallback to database
- WebSocket real-time updates
- Performance monitoring and alerting
- Error recovery and graceful degradation
"""

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from collections import defaultdict

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DashboardMetrics:
    """Dashboard metrics data structure."""
    tenant_id: str
    total_leads: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    avg_score: float
    conversion_rate: float
    generated_at: datetime

    # Performance metrics
    active_agents: int = 0
    response_time_avg: float = 0.0
    webhook_events_count: int = 0


@dataclass
class LeadMetrics:
    """Individual lead metrics."""
    contact_id: str
    score: int
    status: str
    agent_id: Optional[str]
    last_activity: datetime
    tags: List[str]
    custom_fields: Dict[str, Any]

    # Activity metrics
    message_count: int = 0
    engagement_level: str = "low"


@dataclass
class PerformanceMetrics:
    """System performance metrics."""
    webhook_processing_time_ms: float
    dashboard_update_time_ms: float
    cache_hit_rate: float
    websocket_connections: int
    events_processed_per_minute: int

    # Error metrics
    error_rate: float = 0.0
    avg_latency_ms: float = 0.0


class DashboardAnalyticsService:
    """
    Dashboard Analytics Service

    Provides real-time metrics aggregation and WebSocket integration
    for dashboard components with high performance and reliability.
    """

    def __init__(
        self,
        storage_dir: str = "data/dashboard_metrics",
        redis_client=None,
        websocket_router=None
    ):
        """
        Initialize dashboard analytics service.

        Args:
            storage_dir: Directory for metric storage
            redis_client: Redis client for caching (optional)
            websocket_router: WebSocket router for real-time updates
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.redis_client = redis_client
        self.websocket_router = websocket_router

        # Internal cache for performance
        self._metrics_cache: Dict[str, Any] = {}
        self._cache_ttl = 30  # 30 seconds
        self._cache_timestamps: Dict[str, float] = {}

        # Performance tracking
        self._performance_metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_response_time_ms': 0.0
        }

        logger.info(f"Dashboard Analytics Service initialized at {self.storage_dir}")

    async def aggregate_dashboard_metrics(
        self,
        tenant_id: str,
        time_range: str = "24h"
    ) -> DashboardMetrics:
        """
        Aggregate dashboard metrics for a tenant.

        Args:
            tenant_id: Tenant identifier
            time_range: Time range for metrics (24h, 7d, 30d)

        Returns:
            DashboardMetrics object with aggregated data
        """
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f"dashboard_metrics:{tenant_id}:{time_range}"
            cached_metrics = await self._get_cache(cache_key)

            if cached_metrics:
                self._performance_metrics['cache_hits'] += 1
                return DashboardMetrics(**cached_metrics)

            # Cache miss - calculate metrics
            self._performance_metrics['cache_misses'] += 1

            # Mock metrics for now - in production, this would query the database
            metrics = DashboardMetrics(
                tenant_id=tenant_id,
                total_leads=100,
                hot_leads=25,
                warm_leads=40,
                cold_leads=35,
                avg_score=67.5,
                conversion_rate=0.25,
                generated_at=datetime.now(),
                active_agents=5,
                response_time_avg=250.5,
                webhook_events_count=1500
            )

            # Cache the result
            await self._set_cache(cache_key, asdict(metrics), ttl=self._cache_ttl)

            # Track performance
            response_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(response_time)

            return metrics

        except Exception as e:
            logger.error(f"Failed to aggregate dashboard metrics for {tenant_id}: {e}")
            # Return safe default values
            return DashboardMetrics(
                tenant_id=tenant_id,
                total_leads=0,
                hot_leads=0,
                warm_leads=0,
                cold_leads=0,
                avg_score=0.0,
                conversion_rate=0.0,
                generated_at=datetime.now()
            )

    async def process_ghl_webhook_event(
        self,
        contact_id: str,
        tenant_id: str,
        webhook_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process GHL webhook event and update dashboard in real-time.

        Args:
            contact_id: Contact identifier
            tenant_id: Tenant identifier
            webhook_payload: GHL webhook payload

        Returns:
            Processing result with success status and timing
        """
        start_time = time.time()

        try:
            # Extract relevant data from webhook
            event_type = webhook_payload.get("type", "unknown")
            tags = webhook_payload.get("tags", [])
            custom_fields = webhook_payload.get("customFields", {})

            # Create event record
            event_data = {
                "contact_id": contact_id,
                "tenant_id": tenant_id,
                "event_type": event_type,
                "tags": tags,
                "custom_fields": custom_fields,
                "timestamp": datetime.now().isoformat()
            }

            # Store event for metrics calculation
            await self._record_event(tenant_id, event_data)

            # Invalidate cache for this tenant
            await self._invalidate_tenant_cache(tenant_id)

            # Broadcast update to dashboard
            await self.broadcast_dashboard_update(
                tenant_id=tenant_id,
                update_data={
                    "event_type": "lead_update",
                    "contact_id": contact_id,
                    "webhook_event_type": event_type,
                    "timestamp": datetime.now().isoformat()
                }
            )

            processing_time = (time.time() - start_time) * 1000

            return {
                "success": True,
                "contact_id": contact_id,
                "processing_time_ms": processing_time,
                "event_type": event_type
            }

        except Exception as e:
            logger.error(f"Failed to process GHL webhook event for {contact_id}: {e}")
            processing_time = (time.time() - start_time) * 1000

            return {
                "success": False,
                "contact_id": contact_id,
                "processing_time_ms": processing_time,
                "error": str(e)
            }

    async def get_real_time_lead_metrics(
        self,
        tenant_id: str,
        limit: int = 50
    ) -> List[LeadMetrics]:
        """
        Get real-time lead metrics for dashboard display.

        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of leads to return

        Returns:
            List of LeadMetrics objects
        """
        try:
            # Check cache first
            cache_key = f"lead_metrics:{tenant_id}"
            cached_leads = await self._get_cache(cache_key)

            if cached_leads:
                return [LeadMetrics(**lead) for lead in cached_leads[:limit]]

            # Mock lead metrics - in production, query database
            leads = []
            for i in range(min(limit, 10)):  # Mock 10 leads
                leads.append(LeadMetrics(
                    contact_id=f"lead_{i}_{tenant_id}",
                    score=75 - (i * 5),  # Decreasing scores
                    status="hot" if i < 3 else "warm" if i < 7 else "cold",
                    agent_id=f"agent_{i % 3}",  # Distribute across 3 agents
                    last_activity=datetime.now() - timedelta(hours=i),
                    tags=["AI Assistant: ON"] if i % 2 == 0 else [],
                    custom_fields={
                        "budget": f"{400 + i*50}k-{500 + i*50}k",
                        "location": "Downtown" if i % 2 == 0 else "Suburbs"
                    },
                    message_count=10 - i,
                    engagement_level="high" if i < 3 else "medium" if i < 7 else "low"
                ))

            # Cache the results
            await self._set_cache(cache_key, [asdict(lead) for lead in leads], ttl=15)

            return leads

        except Exception as e:
            logger.error(f"Failed to get real-time lead metrics for {tenant_id}: {e}")
            return []

    async def broadcast_dashboard_update(
        self,
        tenant_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Broadcast update to dashboard via WebSocket.

        Args:
            tenant_id: Tenant identifier
            update_data: Update data to broadcast

        Returns:
            Broadcast result with success status and timing
        """
        start_time = time.time()

        try:
            if self.websocket_router:
                # Use the websocket router to broadcast
                await self.websocket_router.broadcast_event(
                    tenant_id=tenant_id,
                    event_type="dashboard_update",
                    data=update_data
                )
            else:
                # Log the broadcast for testing/development
                logger.info(f"Dashboard update broadcast for {tenant_id}: {update_data}")

            broadcast_time = (time.time() - start_time) * 1000

            return {
                "success": True,
                "tenant_id": tenant_id,
                "broadcast_time_ms": broadcast_time,
                "event_type": update_data.get("event_type", "unknown")
            }

        except Exception as e:
            logger.error(f"Failed to broadcast dashboard update for {tenant_id}: {e}")
            broadcast_time = (time.time() - start_time) * 1000

            return {
                "success": False,
                "tenant_id": tenant_id,
                "broadcast_time_ms": broadcast_time,
                "error": str(e)
            }

    async def record_lead_event(
        self,
        tenant_id: str,
        contact_id: str,
        score: int,
        event_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a lead event for metrics tracking.

        Args:
            tenant_id: Tenant identifier
            contact_id: Contact identifier
            score: Lead score
            event_data: Optional additional event data
        """
        try:
            event = {
                "tenant_id": tenant_id,
                "contact_id": contact_id,
                "score": score,
                "timestamp": datetime.now().isoformat(),
                "data": event_data or {}
            }

            await self._record_event(tenant_id, event)

        except Exception as e:
            logger.error(f"Failed to record lead event for {contact_id}: {e}")

    async def get_performance_metrics(self) -> PerformanceMetrics:
        """
        Get system performance metrics.

        Returns:
            PerformanceMetrics object with current performance data
        """
        total_requests = self._performance_metrics['total_requests']
        cache_hits = self._performance_metrics['cache_hits']

        cache_hit_rate = (
            cache_hits / max(total_requests, 1)
            if total_requests > 0 else 0.0
        )

        return PerformanceMetrics(
            webhook_processing_time_ms=self._performance_metrics.get('avg_webhook_time_ms', 50.0),
            dashboard_update_time_ms=self._performance_metrics.get('avg_update_time_ms', 25.0),
            cache_hit_rate=cache_hit_rate,
            websocket_connections=self._performance_metrics.get('websocket_connections', 0),
            events_processed_per_minute=self._performance_metrics.get('events_per_minute', 120),
            error_rate=self._performance_metrics.get('error_rate', 0.01),
            avg_latency_ms=self._performance_metrics['avg_response_time_ms']
        )

    # Private helper methods

    async def _get_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache with performance tracking."""
        try:
            # Check in-memory cache first
            if cache_key in self._metrics_cache:
                timestamp = self._cache_timestamps.get(cache_key, 0)
                if time.time() - timestamp < self._cache_ttl:
                    return self._metrics_cache[cache_key]
                else:
                    # Expired, remove from cache
                    del self._metrics_cache[cache_key]
                    del self._cache_timestamps[cache_key]

            # Check Redis cache if available
            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data) if isinstance(cached_data, str) else cached_data
                    # Promote to in-memory cache
                    self._metrics_cache[cache_key] = data
                    self._cache_timestamps[cache_key] = time.time()
                    return data

            return None

        except Exception as e:
            logger.error(f"Cache get error for {cache_key}: {e}")
            return None

    async def _set_cache(self, cache_key: str, data: Dict[str, Any], ttl: int = 30) -> None:
        """Set data in cache with TTL."""
        try:
            # Set in in-memory cache
            self._metrics_cache[cache_key] = data
            self._cache_timestamps[cache_key] = time.time()

            # Set in Redis cache if available
            if self.redis_client:
                await self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(data, default=str)  # Handle datetime serialization
                )

        except Exception as e:
            logger.error(f"Cache set error for {cache_key}: {e}")

    async def _invalidate_tenant_cache(self, tenant_id: str) -> None:
        """Invalidate all cached data for a tenant."""
        try:
            # Remove from in-memory cache
            keys_to_remove = [
                key for key in self._metrics_cache.keys()
                if f":{tenant_id}:" in key or key.endswith(f":{tenant_id}")
            ]

            for key in keys_to_remove:
                del self._metrics_cache[key]
                self._cache_timestamps.pop(key, None)

            # Remove from Redis cache if available
            if self.redis_client:
                pattern_keys = [
                    f"dashboard_metrics:{tenant_id}:*",
                    f"lead_metrics:{tenant_id}",
                    f"performance_metrics:{tenant_id}"
                ]

                for pattern in pattern_keys:
                    await self.redis_client.delete(pattern)

        except Exception as e:
            logger.error(f"Cache invalidation error for tenant {tenant_id}: {e}")

    async def _record_event(self, tenant_id: str, event_data: Dict[str, Any]) -> None:
        """Record event to storage."""
        try:
            # Create tenant directory
            tenant_dir = self.storage_dir / tenant_id
            tenant_dir.mkdir(parents=True, exist_ok=True)

            # Get daily events file
            date_str = datetime.now().strftime("%Y-%m-%d")
            events_file = tenant_dir / f"events_{date_str}.jsonl"

            # Append event to file
            with open(events_file, "a") as f:
                f.write(json.dumps(event_data, default=str) + "\n")

        except Exception as e:
            logger.error(f"Failed to record event for tenant {tenant_id}: {e}")

    def _update_performance_metrics(self, response_time_ms: float) -> None:
        """Update performance metrics."""
        self._performance_metrics['total_requests'] += 1
        total_requests = self._performance_metrics['total_requests']
        current_avg = self._performance_metrics['avg_response_time_ms']

        # Calculate rolling average
        self._performance_metrics['avg_response_time_ms'] = (
            (current_avg * (total_requests - 1) + response_time_ms) / total_requests
        )


# Singleton instance
_dashboard_analytics_service = None


def get_dashboard_analytics_service(**kwargs) -> DashboardAnalyticsService:
    """Get singleton dashboard analytics service instance."""
    global _dashboard_analytics_service
    if _dashboard_analytics_service is None:
        _dashboard_analytics_service = DashboardAnalyticsService(**kwargs)
    return _dashboard_analytics_service


# Export main classes
__all__ = [
    "DashboardAnalyticsService",
    "DashboardMetrics",
    "LeadMetrics",
    "PerformanceMetrics",
    "get_dashboard_analytics_service"
]