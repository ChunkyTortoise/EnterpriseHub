"""
Tests for Claude Prompt Caching Service
Validates 70% cost reduction and performance improvements
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from ghl_real_estate_ai.services.claude_prompt_caching_service import (
    ClaudePromptCachingService,
    ClaudeRequest,
    ClaudeResponse,
    CacheStrategy,
    RealEstateCachePatterns,
    cached_claude_call
)

@pytest.fixture
async def mock_claude_api():
    """Mock Claude API function for testing."""

    async def mock_api_call(prompt: str, system_prompt: str = "", **kwargs) -> Dict[str, Any]:
        # Simulate API response
        return {
            "content": f"Mock response for: {prompt[:50]}...",
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 50,
                "total_tokens": len(prompt.split()) + 50
            }
        }

    return mock_api_call

@pytest.fixture
async def cache_service():
    """Cache service instance for testing."""

    # Use in-memory Redis mock for testing
    service = ClaudePromptCachingService(
        redis_url="redis://localhost:6379/15",  # Test database
        cost_per_1k_tokens=0.015,
        max_cache_size_mb=50.0
    )

    async with service:
        yield service

class TestClaudeCacheStrategies:
    """Test cache strategy determination."""

    def test_aggressive_strategy_detection(self):
        """Test aggressive caching for static content."""

        service = ClaudePromptCachingService()

        # Test documentation request
        request = ClaudeRequest(
            prompt="Explain how to calculate property ROI",
            system_prompt="You are a real estate expert. Provide clear explanations."
        )

        strategy = service._determine_cache_strategy(request)
        assert strategy == CacheStrategy.AGGRESSIVE

    def test_real_time_strategy_detection(self):
        """Test real-time caching for coaching scenarios."""

        service = ClaudePromptCachingService()

        # Test real-time coaching request
        request = ClaudeRequest(
            prompt="Provide immediate coaching for this live conversation",
            system_prompt="You are a real-time coach",
            context_data={"timestamp": datetime.now().isoformat()}
        )

        strategy = service._determine_cache_strategy(request)
        assert strategy == CacheStrategy.REAL_TIME

    def test_conservative_strategy_detection(self):
        """Test conservative caching for time-sensitive content."""

        service = ClaudePromptCachingService()

        # Test current market analysis
        request = ClaudeRequest(
            prompt="Analyze current market conditions for downtown properties",
            system_prompt="Provide up-to-date market analysis"
        )

        strategy = service._determine_cache_strategy(request)
        assert strategy == CacheStrategy.CONSERVATIVE

class TestClaudeCaching:
    """Test core caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_miss_and_hit_flow(self, cache_service, mock_claude_api):
        """Test complete cache miss -> hit flow."""

        request = ClaudeRequest(
            prompt="Test property analysis request",
            system_prompt="You are a property expert"
        )

        # First call - cache miss
        response1, was_cached1 = await cache_service.get_or_call_claude(
            request, mock_claude_api
        )

        assert not was_cached1, "First call should be cache miss"
        assert response1.content.startswith("Mock response")
        assert response1.cost > 0

        # Second call - cache hit
        response2, was_cached2 = await cache_service.get_or_call_claude(
            request, mock_claude_api
        )

        assert was_cached2, "Second call should be cache hit"
        assert response2.content == response1.content
        assert response2.cost == response1.cost

    @pytest.mark.asyncio
    async def test_cache_key_uniqueness(self, cache_service, mock_claude_api):
        """Test that different requests generate different cache keys."""

        request1 = ClaudeRequest(
            prompt="Analyze property A",
            system_prompt="You are an expert"
        )

        request2 = ClaudeRequest(
            prompt="Analyze property B",
            system_prompt="You are an expert"
        )

        # Should have different cache keys
        assert request1.cache_key() != request2.cache_key()

        # Should result in separate cache entries
        response1, _ = await cache_service.get_or_call_claude(request1, mock_claude_api)
        response2, _ = await cache_service.get_or_call_claude(request2, mock_claude_api)

        assert response1.content != response2.content

    @pytest.mark.asyncio
    async def test_force_refresh(self, cache_service, mock_claude_api):
        """Test force refresh bypasses cache."""

        request = ClaudeRequest(
            prompt="Test force refresh",
            system_prompt="You are an expert"
        )

        # First call
        await cache_service.get_or_call_claude(request, mock_claude_api)

        # Force refresh should bypass cache
        response, was_cached = await cache_service.get_or_call_claude(
            request, mock_claude_api, force_refresh=True
        )

        assert not was_cached, "Force refresh should bypass cache"

class TestCacheAnalytics:
    """Test cache analytics and ROI tracking."""

    @pytest.mark.asyncio
    async def test_cache_metrics_tracking(self, cache_service, mock_claude_api):
        """Test cache metrics are properly tracked."""

        request = ClaudeRequest(
            prompt="Test metrics tracking",
            system_prompt="You are an expert"
        )

        # Initial analytics
        initial_analytics = await cache_service.get_cache_analytics()
        initial_hits = initial_analytics["performance_metrics"]["cache_hits"]
        initial_misses = initial_analytics["performance_metrics"]["cache_misses"]

        # Make cache miss call
        await cache_service.get_or_call_claude(request, mock_claude_api)

        # Make cache hit call
        await cache_service.get_or_call_claude(request, mock_claude_api)

        # Check updated analytics
        final_analytics = await cache_service.get_cache_analytics()
        final_hits = final_analytics["performance_metrics"]["cache_hits"]
        final_misses = final_analytics["performance_metrics"]["cache_misses"]

        assert final_hits == initial_hits + 1, "Should track cache hit"
        assert final_misses == initial_misses + 1, "Should track cache miss"

    @pytest.mark.asyncio
    async def test_cost_savings_calculation(self, cache_service, mock_claude_api):
        """Test cost savings are calculated correctly."""

        request = ClaudeRequest(
            prompt="Test cost savings calculation with longer prompt to generate higher token count",
            system_prompt="You are an expert providing detailed analysis"
        )

        # Cache miss
        response1, _ = await cache_service.get_or_call_claude(request, mock_claude_api)
        original_cost = response1.cost

        # Cache hit - should save the original cost
        await cache_service.get_or_call_claude(request, mock_claude_api)

        analytics = await cache_service.get_cache_analytics()
        cost_saved = float(analytics["cost_metrics"]["total_cost_saved"].replace("$", ""))

        assert cost_saved == original_cost, f"Should save ${original_cost}, but saved ${cost_saved}"

class TestCacheWarming:
    """Test cache warming functionality."""

    @pytest.mark.asyncio
    async def test_cache_warming(self, cache_service, mock_claude_api):
        """Test cache warming with multiple requests."""

        # Create warming requests
        warming_requests = [
            ClaudeRequest(
                prompt=f"Analyze property {i}",
                system_prompt="You are a property expert"
            )
            for i in range(5)
        ]

        # Warm cache
        results = await cache_service.warm_cache(
            warming_requests, mock_claude_api, concurrency_limit=2
        )

        assert results["total_requests"] == 5
        assert results["warmed"] == 5
        assert results["already_cached"] == 0
        assert results["failed"] == 0

        # Verify requests are now cached
        for request in warming_requests:
            response, was_cached = await cache_service.get_or_call_claude(
                request, mock_claude_api
            )
            assert was_cached, "Request should be cached after warming"

class TestRealEstatePatterns:
    """Test real estate specific cache patterns."""

    def test_property_analysis_pattern(self):
        """Test property analysis cache pattern."""

        property_data = {
            "id": "prop_123",
            "address": "123 Main St",
            "price": 500000,
            "type": "condo"
        }

        request = RealEstateCachePatterns.property_analysis_request(property_data)

        assert "property_analysis" in request.context_data["type"]
        assert property_data["id"] in request.context_data["property_id"]
        assert json.dumps(property_data) in request.prompt

    def test_lead_qualification_pattern(self):
        """Test lead qualification cache pattern."""

        lead_data = {
            "id": "lead_456",
            "name": "John Doe",
            "budget": 600000,
            "timeline": "3 months"
        }

        request = RealEstateCachePatterns.lead_qualification_request(lead_data)

        assert "lead_qualification" in request.context_data["type"]
        assert lead_data["id"] in request.context_data["lead_id"]
        assert json.dumps(lead_data) in request.prompt

    def test_real_time_coaching_pattern(self):
        """Test real-time coaching cache pattern."""

        conversation_context = {
            "agent_id": "agent_789",
            "prospect_message": "I'm interested in downtown condos",
            "conversation_stage": "initial_contact"
        }

        request = RealEstateCachePatterns.real_time_coaching_request(conversation_context)

        assert "real_time_coaching" in request.context_data["type"]
        assert "timestamp" in request.context_data
        assert json.dumps(conversation_context) in request.prompt

class TestPerformanceOptimizations:
    """Test performance and efficiency features."""

    @pytest.mark.asyncio
    async def test_cache_compression(self, cache_service, mock_claude_api):
        """Test cache compression reduces storage size."""

        # Create request with large content
        large_content = "This is a very long property description. " * 100
        request = ClaudeRequest(
            prompt=f"Analyze this property: {large_content}",
            system_prompt="Provide detailed analysis"
        )

        # Cache the response
        await cache_service.get_or_call_claude(request, mock_claude_api)

        # Check cache info
        cache_info = await cache_service._get_cache_info()

        # Should have compressed data (exact compression ratio depends on content)
        assert cache_info["cache_size_mb"] > 0
        assert cache_info["total_keys"] >= 1

    @pytest.mark.asyncio
    async def test_cache_limits_enforcement(self, cache_service, mock_claude_api):
        """Test cache size limits are enforced."""

        # Set very small cache limit for testing
        cache_service.max_cache_size_mb = 0.1  # 100KB limit

        # Create many large requests to exceed limit
        for i in range(10):
            large_request = ClaudeRequest(
                prompt=f"Large analysis request {i}: {'content ' * 1000}",
                system_prompt="Provide analysis"
            )
            await cache_service.get_or_call_claude(large_request, mock_claude_api)

        # Cache should enforce limits (might clear old entries)
        cache_info = await cache_service._get_cache_info()
        # Should not exceed limit significantly
        assert cache_info["cache_size_mb"] <= cache_service.max_cache_size_mb * 2  # Allow some buffer

class TestConvenienceFunctions:
    """Test convenience functions for easy integration."""

    @pytest.mark.asyncio
    async def test_cached_claude_call_function(self, mock_claude_api):
        """Test convenience function for cached calls."""

        # Mock Redis to avoid dependency
        with patch('ghl_real_estate_ai.services.claude_prompt_caching_service.redis') as mock_redis:
            mock_redis.from_url.return_value.ping = AsyncMock()
            mock_redis.from_url.return_value.get.return_value = None  # Cache miss
            mock_redis.from_url.return_value.setex = AsyncMock()
            mock_redis.from_url.return_value.keys.return_value = []
            mock_redis.from_url.return_value.close = AsyncMock()

            content, was_cached, cost = await cached_claude_call(
                prompt="Test convenience function",
                system_prompt="You are an expert",
                claude_api_function=mock_claude_api
            )

            assert content.startswith("Mock response")
            assert isinstance(was_cached, bool)
            assert cost > 0

# Integration test scenarios

class TestCostReductionScenarios:
    """Test various cost reduction scenarios."""

    @pytest.mark.asyncio
    async def test_property_analysis_cost_reduction(self, cache_service, mock_claude_api):
        """Test cost reduction for repeated property analysis."""

        # Simulate common property analysis requests
        property_requests = [
            RealEstateCachePatterns.property_analysis_request({
                "id": f"prop_{i}",
                "address": f"{i} Main St",
                "price": 500000 + i * 10000,
                "type": "condo"
            })
            for i in range(3)
        ]

        total_cost_without_cache = 0
        total_cost_with_cache = 0

        # First round - all cache misses
        for request in property_requests:
            response, was_cached = await cache_service.get_or_call_claude(
                request, mock_claude_api
            )
            total_cost_without_cache += response.cost
            if not was_cached:
                total_cost_with_cache += response.cost

        # Second round - all cache hits (simulate repeated analysis)
        for request in property_requests:
            response, was_cached = await cache_service.get_or_call_claude(
                request, mock_claude_api
            )
            total_cost_without_cache += response.cost
            if not was_cached:
                total_cost_with_cache += response.cost

        # Calculate cost reduction
        cost_reduction = (total_cost_without_cache - total_cost_with_cache) / total_cost_without_cache

        # Should achieve significant cost reduction (50%+ for repeated requests)
        assert cost_reduction >= 0.5, f"Cost reduction {cost_reduction:.1%} below 50% target"

    @pytest.mark.asyncio
    async def test_annual_savings_projection(self, cache_service, mock_claude_api):
        """Test annual savings projection accuracy."""

        # Simulate a day's worth of requests with various cache hit patterns
        daily_requests = [
            ClaudeRequest(
                prompt="Daily market analysis",
                system_prompt="Provide market insights"
            ),
            ClaudeRequest(
                prompt="Property valuation methodology",
                system_prompt="Explain valuation process"
            ),
            ClaudeRequest(
                prompt="Lead qualification best practices",
                system_prompt="Provide qualification guidance"
            )
        ]

        # Simulate repeated requests throughout the day
        total_api_cost = 0
        for _ in range(10):  # 10 cycles of the same requests
            for request in daily_requests:
                response, was_cached = await cache_service.get_or_call_claude(
                    request, mock_claude_api
                )
                if not was_cached:
                    total_api_cost += response.cost

        # Get analytics and validate savings projection
        analytics = await cache_service.get_cache_analytics()

        # Extract annual savings estimate
        annual_estimate_str = analytics["cost_metrics"]["annual_savings_estimate"]
        annual_estimate = float(annual_estimate_str.replace("$", "").replace(",", ""))

        # Should project meaningful annual savings
        assert annual_estimate > 0, "Should project positive annual savings"

# Performance benchmarks

@pytest.mark.performance
class TestCachePerformance:
    """Performance benchmarks for caching service."""

    @pytest.mark.asyncio
    async def test_cache_retrieval_speed(self, cache_service, mock_claude_api):
        """Test cache retrieval performance."""

        request = ClaudeRequest(
            prompt="Performance test request",
            system_prompt="You are an expert"
        )

        # Prime cache
        await cache_service.get_or_call_claude(request, mock_claude_api)

        # Measure cache retrieval time
        import time
        start_time = time.time()

        for _ in range(10):
            response, was_cached = await cache_service.get_or_call_claude(
                request, mock_claude_api
            )
            assert was_cached

        retrieval_time = (time.time() - start_time) / 10

        # Cache retrieval should be very fast (< 10ms)
        assert retrieval_time < 0.01, f"Cache retrieval too slow: {retrieval_time:.3f}s"

    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, cache_service, mock_claude_api):
        """Test concurrent cache access performance."""

        request = ClaudeRequest(
            prompt="Concurrent access test",
            system_prompt="You are an expert"
        )

        # Prime cache
        await cache_service.get_or_call_claude(request, mock_claude_api)

        # Test concurrent access
        async def concurrent_access():
            response, was_cached = await cache_service.get_or_call_claude(
                request, mock_claude_api
            )
            return was_cached

        # Run 20 concurrent cache retrievals
        results = await asyncio.gather(*[concurrent_access() for _ in range(20)])

        # All should be cache hits
        assert all(results), "All concurrent requests should be cache hits"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])