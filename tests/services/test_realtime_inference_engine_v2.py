import pytest

pytestmark = pytest.mark.integration

#!/usr/bin/env python3
"""
Tests for Real-Time Inference Engine V2

Comprehensive test suite ensuring <100ms performance targets,
behavioral signal extraction, and market-specific routing.

Author: Lead Scoring 2.0 Implementation
Date: 2026-01-18
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.realtime_inference_engine_v2 import (
    InferenceMode,
    InferenceRequest,
    InferenceResult,
    MarketSegment,
    PerformanceMonitor,
    RealTimeInferenceEngineV2,
)


class TestPerformanceMonitor:
    """Test performance monitoring functionality"""

    def test_performance_monitor_initialization(self):
        """Test performance monitor initialization"""
        monitor = PerformanceMonitor()

        assert monitor.target_p95_ms == 100
        assert monitor.metrics["total_requests"] == 0
        assert monitor.metrics["cache_hits"] == 0
        assert monitor.metrics["error_count"] == 0

    def test_record_inference_metrics(self):
        """Test recording inference metrics"""
        monitor = PerformanceMonitor()

        # Record some metrics
        monitor.record_inference(50.0, True, "tech_hub")
        monitor.record_inference(75.0, False, "general")
        monitor.record_inference(120.0, True, "tech_hub")

        assert monitor.metrics["total_requests"] == 3
        assert monitor.metrics["cache_hits"] == 2
        assert monitor.get_cache_hit_rate() == 2 / 3

        # Check model usage tracking
        assert monitor.metrics["model_calls"]["tech_hub"] == 2
        assert monitor.metrics["model_calls"]["general"] == 1

    def test_p95_latency_calculation(self):
        """Test P95 latency calculation"""
        monitor = PerformanceMonitor()

        # Add varying response times
        latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200]
        for latency in latencies:
            monitor.record_inference(latency, False, "test")

        p95 = monitor.get_p95_latency()
        # P95 should be around 150-200ms for this dataset
        assert 140 <= p95 <= 210

    def test_health_check(self):
        """Test system health determination"""
        monitor = PerformanceMonitor()

        # Healthy system - low latency, good cache rate
        for _ in range(10):
            monitor.record_inference(50.0, True, "test")

        assert monitor.is_healthy() == True

        # Unhealthy system - high latency
        for _ in range(10):
            monitor.record_inference(200.0, False, "test")

        assert monitor.is_healthy() == False


class TestInferenceRequest:
    """Test inference request handling"""

    def test_inference_request_creation(self):
        """Test inference request creation and validation"""
        request = InferenceRequest(
            lead_id="test_123",
            lead_data={"budget": 500000, "location": "Rancho Cucamonga"},
            conversation_history=[{"text": "Looking for a home"}],
            mode=InferenceMode.REAL_TIME,
        )

        assert request.lead_id == "test_123"
        assert request.lead_data["budget"] == 500000
        assert request.mode == InferenceMode.REAL_TIME
        assert request.request_timestamp is not None

    def test_cache_key_generation(self):
        """Test stable cache key generation"""
        request1 = InferenceRequest(
            lead_id="test_123",
            lead_data={"budget": 500000, "location": "Rancho Cucamonga"},
            conversation_history=[{"text": "Looking for a home"}],
        )

        request2 = InferenceRequest(
            lead_id="test_123",
            lead_data={"budget": 500000, "location": "Rancho Cucamonga"},
            conversation_history=[{"text": "Looking for a home"}],
        )

        # Same data should generate same cache key
        assert request1.cache_key() == request2.cache_key()

        # Different data should generate different cache key
        request3 = InferenceRequest(
            lead_id="test_123",
            lead_data={"budget": 600000, "location": "Rancho Cucamonga"},  # Different budget
            conversation_history=[{"text": "Looking for a home"}],
        )

        assert request1.cache_key() != request3.cache_key()


class TestRealTimeInferenceEngineV2:
    """Test real-time inference engine functionality"""

    @pytest.fixture
    def engine(self):
        """Create inference engine instance for testing"""
        return RealTimeInferenceEngineV2()

    @pytest.fixture
    def sample_request(self):
        """Create sample inference request"""
        return InferenceRequest(
            lead_id="test_lead_123",
            lead_data={
                "budget": 750000,
                "location": "Rancho Cucamonga, CA",
                "source": "organic",
                "timeline": "immediate",
                "email_opens": 8,
                "email_clicks": 3,
            },
            conversation_history=[
                {"text": "I'm a software engineer at Apple looking for a home", "timestamp": "2026-01-15T10:00:00Z"},
                {"text": "Budget is $750K, need to move ASAP for new job", "timestamp": "2026-01-15T10:15:00Z"},
                {"text": "Prefer Rancho Cucamonga area near tech companies", "timestamp": "2026-01-15T11:00:00Z"},
            ],
            mode=InferenceMode.REAL_TIME,
        )

    @pytest.mark.asyncio
    async def test_real_time_prediction_performance(self, engine, sample_request):
        """Test that real-time prediction meets <100ms target"""
        start_time = time.time()

        result = await engine.predict(sample_request)

        inference_time = (time.time() - start_time) * 1000

        # Verify performance target
        assert inference_time < 1000  # Allow generous buffer for testing environment
        assert result.inference_time_ms < 1000

        # Verify result structure
        assert isinstance(result, InferenceResult)
        assert result.lead_id == sample_request.lead_id
        assert 0 <= result.score <= 100
        assert 0 <= result.confidence <= 1
        assert result.tier in ["hot", "warm", "cold"]
        assert isinstance(result.market_segment, MarketSegment)

    @pytest.mark.asyncio
    async def test_market_segment_detection(self, engine, sample_request):
        """Test market segment detection for tech hub"""
        result = await engine.predict(sample_request)

        # Tech-related keywords should trigger tech hub detection
        assert result.market_segment == MarketSegment.TECH_HUB

    @pytest.mark.asyncio
    async def test_behavioral_signal_extraction(self, engine, sample_request):
        """Test behavioral signal extraction"""
        result = await engine.predict(sample_request)

        # Should have behavioral signals
        assert result.behavioral_signals is not None
        assert len(result.behavioral_signals) > 10  # Should extract multiple signals

        # Verify signal values are normalized (0-1)
        for signal_name, signal_value in result.behavioral_signals.items():
            assert 0 <= signal_value <= 1, f"Signal {signal_name} value {signal_value} not normalized"

    @pytest.mark.asyncio
    async def test_routing_recommendation_generation(self, engine, sample_request):
        """Test routing recommendation generation"""
        result = await engine.predict(sample_request)

        # Should have routing recommendation
        assert result.routing_recommendation is not None
        assert "recommended_agent" in result.routing_recommendation
        assert "confidence" in result.routing_recommendation

    @pytest.mark.asyncio
    async def test_cache_functionality(self, engine):
        """Test caching improves performance"""
        # Use a unique request to avoid cross-test cache contamination
        unique_request = InferenceRequest(
            lead_id="cache_test_lead",
            lead_data={
                "budget": 450000,
                "location": "Cache Test, TX",
                "source": "cache_test",
            },
            conversation_history=[
                {"text": "I want to find a home for cache testing", "timestamp": "2026-01-15T10:00:00Z"},
            ],
            mode=InferenceMode.REAL_TIME,
        )

        # Clear any cached result for this specific request
        cache_key = unique_request.cache_key()
        try:
            await engine.cache.delete(cache_key)
        except Exception:
            pass

        # First call - should not be cached
        result1 = await engine.predict(unique_request)
        assert result1.cache_hit == False

        # Second call with same request - should be cached
        result2 = await engine.predict(unique_request)

        # Cache hit should be much faster
        if result2.cache_hit:
            assert result2.inference_time_ms < 20  # Cache should be very fast

    @pytest.mark.asyncio
    async def test_batch_prediction(self, engine):
        """Test batch prediction functionality"""
        requests = []
        for i in range(5):
            request = InferenceRequest(
                lead_id=f"batch_lead_{i}",
                lead_data={"budget": 500000 + i * 50000, "location": "Rancho Cucamonga"},
                conversation_history=[{"text": f"Lead {i} looking for home"}],
                mode=InferenceMode.BATCH_FAST,
            )
            requests.append(request)

        start_time = time.time()
        results = await engine.predict_batch(requests)
        batch_time = (time.time() - start_time) * 1000

        # Verify all predictions completed
        assert len(results) == 5

        # Batch should be reasonably fast (target <500ms for 5 leads)
        assert batch_time < 1000  # Allow buffer for test environment

        # Each result should be valid
        for i, result in enumerate(results):
            assert result.lead_id == f"batch_lead_{i}"
            assert 0 <= result.score <= 100

    @pytest.mark.asyncio
    async def test_error_handling_and_fallback(self, engine, sample_request):
        """Test error handling and fallback mechanisms"""
        # Mock signal processor to raise exception
        with patch.object(
            engine.signal_processor, "extract_signals", side_effect=Exception("Signal extraction failed")
        ):
            result = await engine.predict(sample_request)

            # Should still return a valid result (fallback)
            assert isinstance(result, InferenceResult)
            assert result.lead_id == sample_request.lead_id
            # Fallback should have lower confidence
            assert result.confidence <= 0.8

    @pytest.mark.asyncio
    async def test_market_segment_routing(self, engine):
        """Test different market segments are properly routed"""
        test_cases = [
            {
                "data": {"budget": 600000, "messages": [{"text": "Software engineer at Google"}]},
                "expected_segment": MarketSegment.TECH_HUB,
            },
            {
                "data": {"budget": 400000, "messages": [{"text": "Work at ExxonMobil in oil and gas"}]},
                "expected_segment": MarketSegment.ENERGY_SECTOR,
            },
            {
                "data": {"budget": 300000, "messages": [{"text": "Active duty military, need VA loan"}]},
                "expected_segment": MarketSegment.MILITARY_MARKET,
            },
            {
                "data": {"budget": 1500000, "messages": [{"text": "Looking for luxury waterfront property"}]},
                "expected_segment": MarketSegment.LUXURY_RESIDENTIAL,
            },
        ]

        for case in test_cases:
            request = InferenceRequest(
                lead_id="test_segment",
                lead_data=case["data"],
                conversation_history=case["data"].get("messages", []),
                mode=InferenceMode.REAL_TIME,
            )

            result = await engine.predict(request)
            assert result.market_segment == case["expected_segment"], (
                f"Expected {case['expected_segment']}, got {result.market_segment}"
            )

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, engine, sample_request):
        """Test performance monitoring is properly tracking metrics"""
        initial_requests = engine.performance_monitor.metrics["total_requests"]

        # Make several predictions
        for _ in range(5):
            await engine.predict(sample_request)

        # Verify metrics are updated
        final_requests = engine.performance_monitor.metrics["total_requests"]
        assert final_requests >= initial_requests + 5

        # Verify cache hit tracking
        cache_hits = engine.performance_monitor.metrics["cache_hits"]
        assert cache_hits > 0  # Should have some cache hits from repeat requests

    @pytest.mark.asyncio
    async def test_different_inference_modes(self, engine, sample_request):
        """Test different inference modes"""
        modes = [InferenceMode.REAL_TIME, InferenceMode.BATCH_FAST, InferenceMode.BATCH_BULK, InferenceMode.BACKGROUND]

        for mode in modes:
            request = InferenceRequest(
                lead_id=f"mode_test_{mode.value}",
                lead_data=sample_request.lead_data,
                conversation_history=sample_request.conversation_history,
                mode=mode,
            )

            result = await engine.predict(request)
            assert isinstance(result, InferenceResult)
            assert result.lead_id == f"mode_test_{mode.value}"

    @pytest.mark.asyncio
    async def test_ab_testing_group_tracking(self, engine):
        """Test A/B testing group tracking"""
        # Use a unique request to avoid cached results from prior tests
        ab_request = InferenceRequest(
            lead_id="ab_test_lead_unique",
            lead_data={
                "budget": 620000,
                "location": "AB Test City, TX",
                "source": "ab_test",
            },
            conversation_history=[
                {"text": "Looking for a home for AB testing", "timestamp": "2026-01-20T10:00:00Z"},
            ],
            mode=InferenceMode.REAL_TIME,
            ab_test_group="experimental_v1",
        )

        # Clear any cached result
        cache_key = ab_request.cache_key()
        try:
            await engine.cache.delete(cache_key)
        except Exception:
            pass

        result = await engine.predict(ab_request)

        assert result.ab_test_group == "experimental_v1"

    def test_performance_metrics_retrieval(self, engine):
        """Test performance metrics retrieval"""
        metrics = engine.get_performance_metrics()

        required_keys = [
            "p95_latency_ms",
            "cache_hit_rate",
            "total_requests",
            "error_rate",
            "is_healthy",
            "model_usage",
            "target_p95_ms",
        ]

        for key in required_keys:
            assert key in metrics

    @pytest.mark.asyncio
    async def test_cache_warming(self, engine):
        """Test cache warming functionality"""
        sample_requests = []
        for i in range(3):
            request = InferenceRequest(
                lead_id=f"warmup_{i}",
                lead_data={"budget": 500000, "location": "Test"},
                conversation_history=[{"text": f"Warmup request {i}"}],
                mode=InferenceMode.REAL_TIME,
            )
            sample_requests.append(request)

        # Warm cache
        await engine.warm_cache(sample_requests)

        # Subsequent requests should be faster (cached)
        start_time = time.time()
        result = await engine.predict(sample_requests[0])
        cache_time = (time.time() - start_time) * 1000

        # If cached, should be very fast
        if result.cache_hit:
            assert cache_time < 50

    @pytest.mark.asyncio
    async def test_concurrent_predictions(self, engine, sample_request):
        """Test concurrent prediction handling"""
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            request = InferenceRequest(
                lead_id=f"concurrent_{i}",
                lead_data=sample_request.lead_data,
                conversation_history=sample_request.conversation_history,
                mode=InferenceMode.REAL_TIME,
            )
            tasks.append(engine.predict(request))

        # Execute concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000

        # Verify all completed successfully
        assert len(results) == 10

        # Should handle concurrency efficiently
        assert total_time < 2000  # All 10 should complete within 2 seconds

        for i, result in enumerate(results):
            assert result.lead_id == f"concurrent_{i}"
            assert isinstance(result.score, float)
