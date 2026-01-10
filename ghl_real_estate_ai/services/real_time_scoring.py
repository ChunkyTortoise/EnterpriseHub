"""
Real-Time Lead Scoring Service with WebSocket Broadcasting
Provides live scoring updates with <100ms latency target
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

from .lead_scorer import LeadScorer
from .feature_engineering import FeatureEngineer
from .memory_service import MemoryService

logger = logging.getLogger(__name__)


@dataclass
class ScoringEvent:
    """Real-time scoring event structure"""
    lead_id: str
    tenant_id: str
    score: float
    confidence: float
    factors: Dict[str, float]
    timestamp: datetime
    latency_ms: float
    event_type: str = "score_update"


class RealTimeScoring:
    """
    Real-time lead scoring engine with WebSocket broadcasting
    Optimized for <100ms scoring latency
    """

    def __init__(self):
        self.scorer = LeadScorer()
        self.feature_engineer = FeatureEngineer()
        self.memory_service = MemoryService()

        # WebSocket connection management
        self.active_connections: Set[WebSocket] = set()
        self.tenant_connections: Dict[str, Set[WebSocket]] = {}

        # Redis for caching and pub/sub
        self.redis_client: Optional[redis.Redis] = None

        # Performance monitoring
        self.scoring_metrics = {
            "total_scores": 0,
            "avg_latency_ms": 0,
            "cache_hit_rate": 0,
            "active_connections": 0
        }

    async def initialize(self) -> None:
        """Initialize Redis connection and background tasks"""
        try:
            self.redis_client = redis.Redis(
                host="localhost",
                port=6379,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            await self.redis_client.ping()
            logger.info("✅ Real-time scoring initialized with Redis")

            # Start background cache warming
            asyncio.create_task(self._warm_feature_cache())

        except Exception as e:
            logger.warning(f"⚠️  Redis unavailable, using in-memory fallback: {e}")
            self.redis_client = None

    async def connect_websocket(self, websocket: WebSocket, tenant_id: str) -> None:
        """Connect new WebSocket client for real-time updates"""
        await websocket.accept()
        self.active_connections.add(websocket)

        if tenant_id not in self.tenant_connections:
            self.tenant_connections[tenant_id] = set()
        self.tenant_connections[tenant_id].add(websocket)

        self.scoring_metrics["active_connections"] = len(self.active_connections)
        logger.info(f"🔌 WebSocket connected for tenant {tenant_id}, total: {len(self.active_connections)}")

    async def disconnect_websocket(self, websocket: WebSocket, tenant_id: str) -> None:
        """Clean up WebSocket connection"""
        self.active_connections.discard(websocket)
        if tenant_id in self.tenant_connections:
            self.tenant_connections[tenant_id].discard(websocket)
            if not self.tenant_connections[tenant_id]:
                del self.tenant_connections[tenant_id]

        self.scoring_metrics["active_connections"] = len(self.active_connections)
        logger.info(f"🔌 WebSocket disconnected for tenant {tenant_id}")

    async def score_lead_realtime(
        self,
        lead_id: str,
        tenant_id: str,
        lead_data: Dict,
        broadcast: bool = True
    ) -> ScoringEvent:
        """
        Score lead with real-time broadcasting
        Target: <100ms total latency including broadcast
        """
        start_time = time.time()

        try:
            # 1. Fast feature extraction (target: 10-15ms)
            features = await self._extract_features_cached(lead_id, lead_data)

            # 2. ML scoring (target: 20-30ms)
            score_result = await self.scorer.score_lead_async(features)

            # 3. Create scoring event
            latency_ms = (time.time() - start_time) * 1000

            scoring_event = ScoringEvent(
                lead_id=lead_id,
                tenant_id=tenant_id,
                score=score_result.score,
                confidence=score_result.confidence,
                factors=score_result.factor_breakdown,
                timestamp=datetime.utcnow(),
                latency_ms=latency_ms
            )

            # 4. Cache result for future use
            if self.redis_client:
                cache_key = f"score:{tenant_id}:{lead_id}"
                await self.redis_client.setex(
                    cache_key,
                    300,  # 5 minute TTL
                    json.dumps(asdict(scoring_event), default=str)
                )

            # 5. Broadcast to connected clients (target: 5-10ms)
            if broadcast:
                asyncio.create_task(self._broadcast_scoring_event(scoring_event))

            # 6. Update performance metrics
            self._update_metrics(latency_ms)

            if latency_ms > 100:
                logger.warning(f"⚠️  Scoring latency exceeded target: {latency_ms:.1f}ms for lead {lead_id}")
            else:
                logger.debug(f"✅ Lead scored in {latency_ms:.1f}ms: {lead_id} = {score_result.score:.1f}")

            return scoring_event

        except Exception as e:
            logger.error(f"❌ Real-time scoring failed for lead {lead_id}: {str(e)}")
            # Return fallback event
            return ScoringEvent(
                lead_id=lead_id,
                tenant_id=tenant_id,
                score=50.0,  # Fallback score
                confidence=0.1,
                factors={"error": 1.0},
                timestamp=datetime.utcnow(),
                latency_ms=(time.time() - start_time) * 1000
            )

    async def _extract_features_cached(self, lead_id: str, lead_data: Dict) -> Dict:
        """Extract features with Redis caching"""
        cache_key = f"features:{lead_id}:v1"

        # Try cache first
        if self.redis_client:
            cached_features = await self.redis_client.get(cache_key)
            if cached_features:
                return json.loads(cached_features)

        # Compute features
        features = await self.feature_engineer.extract_features_async(lead_data)

        # Cache for 10 minutes
        if self.redis_client:
            await self.redis_client.setex(
                cache_key,
                600,
                json.dumps(features, default=str)
            )

        return features

    async def _broadcast_scoring_event(self, event: ScoringEvent) -> None:
        """Broadcast scoring event to tenant WebSocket connections"""
        if event.tenant_id not in self.tenant_connections:
            return

        message = json.dumps(asdict(event), default=str)
        disconnected = []

        for websocket in self.tenant_connections[event.tenant_id]:
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected.append(websocket)
            except Exception as e:
                logger.warning(f"WebSocket send failed: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            await self.disconnect_websocket(ws, event.tenant_id)

    async def _warm_feature_cache(self) -> None:
        """Background task to warm feature cache for active leads"""
        while True:
            try:
                if not self.redis_client:
                    await asyncio.sleep(60)
                    continue

                # Get recently active leads
                active_leads = await self.memory_service.get_active_leads(
                    last_activity_hours=24
                )

                for lead in active_leads[:100]:  # Limit cache warming
                    if not await self.redis_client.exists(f"features:{lead['id']}:v1"):
                        # Pre-compute and cache features for active leads
                        features = await self.feature_engineer.extract_features_async(lead)
                        await self.redis_client.setex(
                            f"features:{lead['id']}:v1",
                            3600,  # 1 hour TTL for warm cache
                            json.dumps(features, default=str)
                        )

                        # Don't overwhelm system
                        await asyncio.sleep(0.1)

                logger.info(f"🔥 Feature cache warmed for {len(active_leads)} leads")
                await asyncio.sleep(300)  # Warm every 5 minutes

            except Exception as e:
                logger.error(f"Cache warming failed: {e}")
                await asyncio.sleep(60)

    def _update_metrics(self, latency_ms: float) -> None:
        """Update performance metrics"""
        self.scoring_metrics["total_scores"] += 1

        # Exponential moving average for latency
        alpha = 0.1
        current_avg = self.scoring_metrics["avg_latency_ms"]
        self.scoring_metrics["avg_latency_ms"] = (
            alpha * latency_ms + (1 - alpha) * current_avg
        )

    async def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        cache_hits = 0
        cache_misses = 0

        if self.redis_client:
            info = await self.redis_client.info("stats")
            cache_hits = info.get("keyspace_hits", 0)
            cache_misses = info.get("keyspace_misses", 0)

        hit_rate = cache_hits / max(cache_hits + cache_misses, 1)

        return {
            **self.scoring_metrics,
            "cache_hit_rate": hit_rate,
            "redis_connected": self.redis_client is not None,
            "tenant_connections": len(self.tenant_connections),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def batch_score_leads(
        self,
        leads: List[Dict],
        tenant_id: str,
        parallel_workers: int = 5
    ) -> List[ScoringEvent]:
        """
        Batch score multiple leads with parallel processing
        Useful for initial scoring or bulk operations
        """
        async def score_single(lead_data):
            return await self.score_lead_realtime(
                lead_data["id"],
                tenant_id,
                lead_data,
                broadcast=False  # Don't spam WebSocket during batch
            )

        # Create semaphore for controlled parallelism
        semaphore = asyncio.Semaphore(parallel_workers)

        async def score_with_semaphore(lead_data):
            async with semaphore:
                return await score_single(lead_data)

        # Execute batch scoring
        tasks = [score_with_semaphore(lead) for lead in leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        successful_results = [
            r for r in results
            if isinstance(r, ScoringEvent)
        ]

        # Broadcast batch completion event
        if successful_results:
            batch_event = {
                "event_type": "batch_complete",
                "tenant_id": tenant_id,
                "leads_scored": len(successful_results),
                "avg_score": sum(r.score for r in successful_results) / len(successful_results),
                "timestamp": datetime.utcnow().isoformat()
            }

            await self._broadcast_to_tenant(tenant_id, batch_event)

        logger.info(f"📊 Batch scored {len(successful_results)}/{len(leads)} leads for tenant {tenant_id}")
        return successful_results

    async def _broadcast_to_tenant(self, tenant_id: str, message: Dict) -> None:
        """Broadcast arbitrary message to tenant connections"""
        if tenant_id not in self.tenant_connections:
            return

        message_json = json.dumps(message, default=str)

        for websocket in self.tenant_connections[tenant_id]:
            try:
                await websocket.send_text(message_json)
            except Exception:
                pass  # Connection cleanup handled elsewhere


# Global instance
real_time_scoring = RealTimeScoring()


# Convenience functions for easy integration
async def score_lead_live(lead_id: str, tenant_id: str, lead_data: Dict) -> ScoringEvent:
    """Score a single lead with real-time broadcast"""
    return await real_time_scoring.score_lead_realtime(lead_id, tenant_id, lead_data)


async def connect_scoring_websocket(websocket: WebSocket, tenant_id: str) -> None:
    """Connect WebSocket for real-time scoring updates"""
    await real_time_scoring.connect_websocket(websocket, tenant_id)


async def get_scoring_performance() -> Dict:
    """Get current scoring performance metrics"""
    return await real_time_scoring.get_performance_metrics()