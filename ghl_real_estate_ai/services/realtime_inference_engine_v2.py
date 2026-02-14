#!/usr/bin/env python3
"""
🚀 Real-Time Inference Engine V2
================================

High-performance real-time lead scoring engine with <100ms response times.

Features:
- Sub-100ms inference with aggressive caching
- Parallel signal processing pipeline
- Market-aware model routing
- Adaptive batch processing
- Real-time A/B testing framework
- Performance monitoring and optimization

Target: 95th percentile under 100ms response time
Architecture: Event-driven pipeline with async processing

Author: Lead Scoring 2.0 Implementation
Date: 2026-01-18
"""

import asyncio
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

# Project imports
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ml.behavioral_signal_processor import BehavioralSignalProcessor
from ghl_real_estate_ai.ml.market_specific_models import MarketSpecificModelRouter
from ghl_real_estate_ai.services.ai_predictive_lead_scoring import LeadScore, PredictiveLeadScorer
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.intelligent_lead_router import IntelligentLeadRouter

logger = get_logger(__name__)


class MarketSegment(Enum):
    """Market segment types for model routing"""

    TECH_HUB = "tech_hub"
    ENERGY_SECTOR = "energy_sector"
    MILITARY_MARKET = "military_market"
    LUXURY_RESIDENTIAL = "luxury_residential"
    FIRST_TIME_BUYERS = "first_time_buyers"
    INVESTMENT_FOCUSED = "investment_focused"
    GENERAL_MARKET = "general_market"


class InferenceMode(Enum):
    """Inference processing modes"""

    REAL_TIME = "real_time"  # <100ms target
    BATCH_FAST = "batch_fast"  # <500ms for 10 leads
    BATCH_BULK = "batch_bulk"  # <5s for 100 leads
    BACKGROUND = "background"  # No time constraint


@dataclass
class InferenceRequest:
    """Structured inference request"""

    lead_id: str
    lead_data: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    market_context: Optional[Dict[str, Any]] = None
    mode: InferenceMode = InferenceMode.REAL_TIME
    ab_test_group: Optional[str] = None
    request_timestamp: float = None

    def __post_init__(self):
        if self.request_timestamp is None:
            self.request_timestamp = time.time()

    def cache_key(self) -> str:
        """Generate cache key for this request"""
        # Create stable hash from lead data and conversation
        content = {
            "lead_id": self.lead_id,
            "lead_data_hash": hashlib.md5(json.dumps(self.lead_data, sort_keys=True, default=str).encode()).hexdigest(),
            "conversation_hash": hashlib.md5(
                json.dumps(self.conversation_history, sort_keys=True, default=str).encode()
            ).hexdigest(),
        }
        return f"inference_v2:{hashlib.md5(json.dumps(content, sort_keys=True).encode()).hexdigest()}"


@dataclass
class InferenceResult:
    """Comprehensive inference result"""

    lead_id: str
    score: float
    confidence: float
    tier: str
    market_segment: MarketSegment
    behavioral_signals: Dict[str, float]
    routing_recommendation: Dict[str, Any]

    # Performance metrics
    inference_time_ms: float
    cache_hit: bool
    model_version: str

    # A/B testing
    ab_test_group: Optional[str] = None
    ab_test_variant: Optional[str] = None

    # Timestamps
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class PerformanceMonitor:
    """Real-time performance monitoring"""

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "inference_times": [],
            "error_count": 0,
            "model_calls": {},
            "last_reset": time.time(),
        }
        self.target_p95_ms = 100

    def record_inference(self, inference_time_ms: float, cache_hit: bool, model_used: str):
        """Record inference performance"""
        self.metrics["total_requests"] += 1
        self.metrics["inference_times"].append(inference_time_ms)

        if cache_hit:
            self.metrics["cache_hits"] += 1

        self.metrics["model_calls"][model_used] = self.metrics["model_calls"].get(model_used, 0) + 1

        # Keep only recent measurements
        if len(self.metrics["inference_times"]) > 1000:
            self.metrics["inference_times"] = self.metrics["inference_times"][-500:]

    def get_p95_latency(self) -> float:
        """Get 95th percentile latency"""
        if not self.metrics["inference_times"]:
            return 0.0
        return np.percentile(self.metrics["inference_times"], 95)

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        if self.metrics["total_requests"] == 0:
            return 0.0
        return self.metrics["cache_hits"] / self.metrics["total_requests"]

    def is_healthy(self) -> bool:
        """Check if performance is healthy"""
        p95 = self.get_p95_latency()
        cache_rate = self.get_cache_hit_rate()
        return p95 < self.target_p95_ms and cache_rate > 0.6


class RealTimeInferenceEngineV2:
    """
    High-performance real-time inference engine for lead scoring.

    Optimized for <100ms response times with intelligent caching,
    parallel processing, and market-aware routing.
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.performance_monitor = PerformanceMonitor()

        # Initialize components
        self.base_scorer = PredictiveLeadScorer()
        self.signal_processor = BehavioralSignalProcessor()
        self.market_router = MarketSpecificModelRouter()
        self.lead_router = IntelligentLeadRouter()

        # Thread pool for CPU-intensive tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # Cache configuration
        self.cache_ttl_realtime = 300  # 5 minutes for real-time
        self.cache_ttl_batch = 1800  # 30 minutes for batch

        # A/B testing groups
        self.ab_groups = ["control", "experimental_v1", "experimental_v2"]

        logger.info("RealTimeInferenceEngineV2 initialized with performance monitoring")

    async def predict(self, request: InferenceRequest) -> InferenceResult:
        """
        Main prediction endpoint with performance optimization.

        Target: <100ms for 95% of real-time requests
        """
        start_time = time.time()

        try:
            # Step 1: Check cache first (target: <5ms)
            cache_key = request.cache_key()

            if request.mode == InferenceMode.REAL_TIME:
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    inference_time_ms = (time.time() - start_time) * 1000
                    self.performance_monitor.record_inference(inference_time_ms, True, "cache")

                    # Update cached result with new metadata
                    cached_result.inference_time_ms = inference_time_ms
                    cached_result.cache_hit = True
                    return cached_result

            # Step 2: Parallel signal processing (target: <30ms)
            signal_task = self._extract_behavioral_signals(request)
            market_task = self._determine_market_segment(request)

            behavioral_signals, market_segment = await asyncio.gather(signal_task, market_task)

            # Step 3: Route to appropriate model (target: <50ms)
            score_result = await self._run_inference(request, behavioral_signals, market_segment)

            # Step 4: Generate routing recommendation (target: <10ms)
            routing_recommendation = await self._generate_routing_recommendation(
                request, score_result, behavioral_signals
            )

            # Step 5: Assemble result
            result = InferenceResult(
                lead_id=request.lead_id,
                score=score_result.score,
                confidence=score_result.confidence,
                tier=score_result.tier,
                market_segment=market_segment,
                behavioral_signals=behavioral_signals,
                routing_recommendation=routing_recommendation,
                inference_time_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
                model_version=self.market_router.get_model_version(market_segment),
                ab_test_group=request.ab_test_group,
            )

            # Step 6: Cache result for future requests
            if request.mode == InferenceMode.REAL_TIME:
                await self._cache_result(cache_key, result)

            # Record performance metrics
            self.performance_monitor.record_inference(result.inference_time_ms, False, market_segment.value)

            return result

        except Exception as e:
            self.performance_monitor.metrics["error_count"] += 1
            logger.error(f"Inference error for lead {request.lead_id}: {e}")

            # Fallback to base scorer
            return await self._fallback_inference(request, start_time)

    async def predict_batch(self, requests: List[InferenceRequest]) -> List[InferenceResult]:
        """
        Batch prediction with automatic mode selection.

        Targets:
        - <500ms for 10 leads (BATCH_FAST)
        - <5s for 100 leads (BATCH_BULK)
        """
        if len(requests) <= 10:
            mode = InferenceMode.BATCH_FAST
        elif len(requests) <= 100:
            mode = InferenceMode.BATCH_BULK
        else:
            mode = InferenceMode.BACKGROUND

        # Update request modes
        for req in requests:
            req.mode = mode

        # Process in parallel with concurrency limits
        concurrency_limit = min(len(requests), 10 if mode == InferenceMode.BATCH_FAST else 5)
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def bounded_predict(request):
            async with semaphore:
                return await self.predict(request)

        results = await asyncio.gather(*[bounded_predict(req) for req in requests])
        return results

    async def _extract_behavioral_signals(self, request: InferenceRequest) -> Dict[str, float]:
        """Extract behavioral signals with performance optimization"""
        try:
            # Use thread pool for CPU-intensive signal processing
            loop = asyncio.get_event_loop()
            signals = await loop.run_in_executor(
                self.thread_pool, self.signal_processor.extract_signals, request.lead_data, request.conversation_history
            )
            return signals
        except Exception as e:
            logger.warning(f"Behavioral signal extraction failed: {e}")
            return {}

    async def _determine_market_segment(self, request: InferenceRequest) -> MarketSegment:
        """Determine market segment for model routing"""
        try:
            # Quick heuristics for market segmentation
            lead_data = request.lead_data

            # Combine lead_data and conversation_history for keyword matching
            searchable_text = str(lead_data).lower()
            if request.conversation_history:
                searchable_text += " " + str(request.conversation_history).lower()

            # Tech hub indicators
            if any(
                keyword in searchable_text
                for keyword in ["apple", "google", "tech", "startup", "engineer", "developer", "software"]
            ):
                return MarketSegment.TECH_HUB

            # Energy sector indicators
            if any(keyword in searchable_text for keyword in ["oil", "gas", "energy", "petroleum", "exxon", "chevron"]):
                return MarketSegment.ENERGY_SECTOR

            # Military market indicators
            if any(
                keyword in searchable_text for keyword in ["military", "army", "navy", "air force", "veteran", "base"]
            ):
                return MarketSegment.MILITARY_MARKET

            # Luxury indicators
            budget = lead_data.get("budget", 0)
            if budget > 1000000:
                return MarketSegment.LUXURY_RESIDENTIAL

            # Investment indicators
            if any(keyword in searchable_text for keyword in ["investment", "roi", "cap rate", "rental", "portfolio"]):
                return MarketSegment.INVESTMENT_FOCUSED

            # First-time buyer indicators
            if any(keyword in searchable_text for keyword in ["first time", "first-time", "new buyer", "fha"]):
                return MarketSegment.FIRST_TIME_BUYERS

            return MarketSegment.GENERAL_MARKET

        except Exception as e:
            logger.warning(f"Market segmentation failed: {e}")
            return MarketSegment.GENERAL_MARKET

    async def _run_inference(
        self, request: InferenceRequest, behavioral_signals: Dict[str, float], market_segment: MarketSegment
    ) -> LeadScore:
        """Run inference using market-specific model"""
        try:
            # Route to market-specific model
            model_result = await self.market_router.predict(request.lead_data, behavioral_signals, market_segment)

            # If market-specific model unavailable, fall back to base scorer
            if model_result is None:
                return self.base_scorer.score_lead(request.lead_id, request.lead_data)

            return model_result

        except Exception as e:
            logger.warning(f"Market-specific inference failed: {e}")
            # Fallback to base scorer
            return self.base_scorer.score_lead(request.lead_id, request.lead_data)

    async def _generate_routing_recommendation(
        self, request: InferenceRequest, score_result: LeadScore, behavioral_signals: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate intelligent routing recommendation"""
        try:
            routing_rec = await self.lead_router.recommend_routing(
                lead_id=request.lead_id,
                lead_score=score_result.score,
                behavioral_signals=behavioral_signals,
                lead_data=request.lead_data,
            )
            return routing_rec
        except Exception as e:
            logger.warning(f"Routing recommendation failed: {e}")
            return {
                "recommended_agent": "auto_assign",
                "priority_level": "medium",
                "suggested_response_time": "24_hours",
            }

    async def _get_cached_result(self, cache_key: str) -> Optional[InferenceResult]:
        """Retrieve cached inference result"""
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return InferenceResult(**cached_data)
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None

    async def _cache_result(self, cache_key: str, result: InferenceResult):
        """Cache inference result"""
        try:
            # Convert to dict for caching
            cache_data = asdict(result)
            # Convert datetime to string for JSON serialization
            cache_data["timestamp"] = result.timestamp.isoformat()

            await self.cache.set(cache_key, cache_data, self.cache_ttl_realtime)
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    async def _fallback_inference(self, request: InferenceRequest, start_time: float) -> InferenceResult:
        """Fallback inference when primary pipeline fails"""
        try:
            # Use base scorer as fallback
            score_result = self.base_scorer.score_lead(request.lead_id, request.lead_data)

            return InferenceResult(
                lead_id=request.lead_id,
                score=score_result.score,
                confidence=0.5,  # Lower confidence for fallback
                tier=score_result.tier,
                market_segment=MarketSegment.GENERAL_MARKET,
                behavioral_signals={},
                routing_recommendation={"recommended_agent": "auto_assign", "priority_level": "medium"},
                inference_time_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
                model_version="fallback_v1",
                ab_test_group=request.ab_test_group,
            )
        except Exception as e:
            logger.error(f"Fallback inference failed: {e}")
            # Return minimal result
            return InferenceResult(
                lead_id=request.lead_id,
                score=50.0,
                confidence=0.3,
                tier="warm",
                market_segment=MarketSegment.GENERAL_MARKET,
                behavioral_signals={},
                routing_recommendation={},
                inference_time_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
                model_version="emergency_fallback",
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            "p95_latency_ms": self.performance_monitor.get_p95_latency(),
            "cache_hit_rate": self.performance_monitor.get_cache_hit_rate(),
            "total_requests": self.performance_monitor.metrics["total_requests"],
            "error_rate": (
                self.performance_monitor.metrics["error_count"]
                / max(self.performance_monitor.metrics["total_requests"], 1)
            ),
            "is_healthy": self.performance_monitor.is_healthy(),
            "model_usage": self.performance_monitor.metrics["model_calls"],
            "target_p95_ms": self.performance_monitor.target_p95_ms,
        }

    async def warm_cache(self, sample_requests: List[InferenceRequest]):
        """Warm the cache with sample requests"""
        logger.info(f"Warming cache with {len(sample_requests)} sample requests")

        # Process sample requests to populate cache
        await self.predict_batch(sample_requests)

        logger.info("Cache warming completed")

    @asynccontextmanager
    async def performance_context(self):
        """Context manager for performance monitoring"""
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"Operation completed in {elapsed:.1f}ms")


# Global instance for import
inference_engine = RealTimeInferenceEngineV2()


# Async function for easy imports
async def predict_lead_score_v2(
    lead_id: str,
    lead_data: Dict[str, Any],
    conversation_history: List[Dict[str, Any]] = None,
    mode: InferenceMode = InferenceMode.REAL_TIME,
) -> InferenceResult:
    """
    Convenience function for single lead scoring.

    Args:
        lead_id: Unique lead identifier
        lead_data: Lead information
        conversation_history: Conversation messages
        mode: Inference mode for optimization

    Returns:
        InferenceResult with comprehensive scoring
    """
    request = InferenceRequest(
        lead_id=lead_id, lead_data=lead_data, conversation_history=conversation_history or [], mode=mode
    )

    return await inference_engine.predict(request)


# Example usage
if __name__ == "__main__":

    async def demo():
        # Create sample request
        request = InferenceRequest(
            lead_id="lead_123",
            lead_data={
                "budget": 500000,
                "location": "Rancho Cucamonga, CA",
                "timeline": "immediate",
                "source": "organic",
                "email_engagement": 0.8,
            },
            conversation_history=[
                {"text": "I'm looking for a tech-friendly home in Rancho Cucamonga"},
                {"text": "Budget is around $500K, need to move ASAP for Apple job"},
            ],
        )

        # Run inference
        engine = RealTimeInferenceEngineV2()
        result = await engine.predict(request)

        print(f"Lead Score: {result.score:.1f}")
        print(f"Market Segment: {result.market_segment.value}")
        print(f"Inference Time: {result.inference_time_ms:.1f}ms")
        print(f"Routing: {result.routing_recommendation}")

        # Performance metrics
        metrics = engine.get_performance_metrics()
        print(f"Performance: P95={metrics['p95_latency_ms']:.1f}ms, Cache Hit Rate={metrics['cache_hit_rate']:.1%}")

    asyncio.run(demo())
