"""
Integration Tests for Claude Component Enhancements

Tests for the comprehensive Claude AI integration across Streamlit components:
- ClaudeComponentMixin functionality
- PropertyValuationDashboard Claude integration
- BusinessIntelligenceDashboard Claude integration
- Voice webhook handler integration
- Sub-25ms performance optimizer

Performance Validation:
- Real-time coaching: < 25ms target
- Semantic analysis: < 100ms target
- Objection handling: < 15ms target

Author: EnterpriseHub Development Team
Created: January 10, 2026
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any


# ============================================================================
# ClaudeComponentMixin Tests
# ============================================================================

class TestClaudeComponentMixin:
    """Tests for the ClaudeComponentMixin."""

    @pytest.fixture
    def mixin_instance(self):
        """Create a test mixin instance."""
        from ghl_real_estate_ai.streamlit_components.claude_component_mixin import (
            ClaudeComponentMixin
        )
        return ClaudeComponentMixin(
            enable_claude_caching=True,
            cache_ttl_seconds=60,
            enable_performance_monitoring=True,
            demo_mode=True
        )

    def test_mixin_initialization(self, mixin_instance):
        """Test that mixin initializes correctly."""
        assert mixin_instance._claude_caching_enabled is True
        assert mixin_instance._claude_cache_ttl == 60
        assert mixin_instance._performance_monitoring is True
        assert mixin_instance._claude_demo_mode is True
        assert mixin_instance._service_status is not None

    def test_cache_key_generation(self, mixin_instance):
        """Test cache key generation."""
        from ghl_real_estate_ai.streamlit_components.claude_component_mixin import (
            ClaudeOperationType
        )

        key1 = mixin_instance._generate_cache_key(
            ClaudeOperationType.REAL_TIME_COACHING,
            "agent1", "hello", "discovery"
        )
        key2 = mixin_instance._generate_cache_key(
            ClaudeOperationType.REAL_TIME_COACHING,
            "agent1", "hello", "discovery"
        )
        key3 = mixin_instance._generate_cache_key(
            ClaudeOperationType.REAL_TIME_COACHING,
            "agent2", "hello", "discovery"
        )

        # Same inputs should produce same key
        assert key1 == key2
        # Different inputs should produce different key
        assert key1 != key3

    def test_cache_response_storage(self, mixin_instance):
        """Test caching responses."""
        from ghl_real_estate_ai.streamlit_components.claude_component_mixin import (
            ClaudeOperationType
        )

        cache_key = "test_key_123"
        test_response = {"suggestions": ["test"], "confidence": 0.9}

        mixin_instance._cache_response(
            cache_key,
            test_response,
            ClaudeOperationType.REAL_TIME_COACHING
        )

        cached = mixin_instance._get_cached_response(cache_key)
        assert cached is not None
        assert cached["suggestions"] == ["test"]

    def test_cache_expiration(self, mixin_instance):
        """Test cache entry expiration."""
        from ghl_real_estate_ai.streamlit_components.claude_component_mixin import (
            ClaudeOperationType
        )

        cache_key = "expire_test_key"
        test_response = {"data": "test"}

        # Cache with very short TTL
        mixin_instance._cache_response(
            cache_key,
            test_response,
            ClaudeOperationType.SEMANTIC_ANALYSIS,
            ttl_override=0  # Immediate expiration
        )

        # Should not be retrievable after expiration
        time.sleep(0.1)
        cached = mixin_instance._get_cached_response(cache_key)
        assert cached is None

    def test_demo_mode_coaching_response(self, mixin_instance):
        """Test demo mode coaching response generation."""
        response = mixin_instance._get_demo_coaching_response("test message")

        assert "suggestions" in response
        assert "recommended_response" in response
        assert "demo_mode" in response
        assert response["demo_mode"] is True
        assert len(response["suggestions"]) > 0

    def test_demo_mode_semantic_analysis(self, mixin_instance):
        """Test demo mode semantic analysis response."""
        response = mixin_instance._get_demo_semantic_analysis()

        assert "intent_analysis" in response
        assert "semantic_preferences" in response
        assert "qualification_assessment" in response
        assert "demo_mode" in response

    def test_fallback_responses(self, mixin_instance):
        """Test fallback response generation."""
        coaching_fallback = mixin_instance._get_fallback_coaching_response()
        assert "fallback_mode" in coaching_fallback
        assert coaching_fallback["fallback_mode"] is True

        semantic_fallback = mixin_instance._get_fallback_semantic_analysis()
        assert "fallback_mode" in semantic_fallback
        assert semantic_fallback["fallback_mode"] is True

    def test_performance_metrics_recording(self, mixin_instance):
        """Test performance metrics recording."""
        from ghl_real_estate_ai.streamlit_components.claude_component_mixin import (
            ClaudeOperationType,
            ClaudeOperationMetrics
        )

        metrics = mixin_instance._start_operation(ClaudeOperationType.REAL_TIME_COACHING)
        time.sleep(0.01)  # Simulate some processing
        metrics.complete(success=True, cached=False)

        mixin_instance._complete_operation(metrics)

        stats = mixin_instance.get_claude_performance_stats(
            ClaudeOperationType.REAL_TIME_COACHING
        )

        assert stats is not None
        assert "total_operations" in stats

    def test_status_indicator(self, mixin_instance):
        """Test status indicator generation."""
        status = mixin_instance.get_claude_status_indicator()
        assert status is not None
        assert "Claude AI" in status


# ============================================================================
# Voice Webhook Handler Tests
# ============================================================================

class TestVoiceWebhookHandler:
    """Tests for the voice webhook integration handler."""

    @pytest.fixture
    def voice_event_payload(self):
        """Create a test voice event payload."""
        return {
            "event_type": "call_started",
            "provider": "custom",
            "call_id": "test_call_123",
            "agent_id": "agent_456",
            "contact_id": "contact_789",
            "location_id": "loc_001",
            "call_direction": "inbound"
        }

    def test_voice_event_model_validation(self, voice_event_payload):
        """Test voice event model validation."""
        from ghl_real_estate_ai.api.routes.voice.voice_webhook_handler import (
            VoiceCallEventModel,
            VoiceEventType
        )

        event = VoiceCallEventModel(**voice_event_payload)

        assert event.call_id == "test_call_123"
        assert event.agent_id == "agent_456"
        assert event.event_type == VoiceEventType.CALL_STARTED

    def test_transcription_segment_model(self):
        """Test transcription segment model."""
        from ghl_real_estate_ai.api.routes.voice.voice_webhook_handler import (
            TranscriptionSegmentModel,
            SpeakerType
        )

        segment = TranscriptionSegmentModel(
            text="I'm interested in looking at homes",
            speaker=SpeakerType.PROSPECT,
            timestamp=10.5,
            confidence=0.95,
            is_final=True
        )

        assert segment.text == "I'm interested in looking at homes"
        assert segment.speaker == SpeakerType.PROSPECT
        assert segment.confidence == 0.95

    def test_coaching_response_model(self):
        """Test voice coaching response model."""
        from ghl_real_estate_ai.api.routes.voice.voice_webhook_handler import (
            VoiceCoachingResponseModel
        )

        response = VoiceCoachingResponseModel(
            coaching_suggestions=[
                {"type": "opening", "message": "Test suggestion", "priority": "high"}
            ],
            objection_detected=True,
            objection_type="price_concern",
            recommended_responses=["Test response"],
            urgency_level="high"
        )

        assert len(response.coaching_suggestions) == 1
        assert response.objection_detected is True
        assert response.urgency_level == "high"


# ============================================================================
# Sub-25ms Performance Optimizer Tests
# ============================================================================

class TestSub25msOptimizer:
    """Tests for the sub-25ms coaching optimizer."""

    @pytest.fixture
    def optimizer(self):
        """Create a test optimizer instance."""
        from ghl_real_estate_ai.services.claude_performance_optimizer import (
            Sub25msCoachingOptimizer
        )
        return Sub25msCoachingOptimizer()

    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initializes correctly."""
        assert optimizer.target_latency_ms == 25.0
        assert len(optimizer.precomputed_responses) > 0
        assert optimizer.total_requests == 0

    def test_prewarm_cache(self, optimizer):
        """Test cache pre-warming."""
        # Should have precomputed responses for common objections
        assert len(optimizer.precomputed_responses) >= len(optimizer.COMMON_OBJECTIONS)

        # Check coaching templates are cached
        for stage in optimizer.COACHING_TEMPLATES.keys():
            key = f"stage:{stage}"
            assert key in optimizer.precomputed_responses

    def test_objection_key_generation(self, optimizer):
        """Test objection key generation."""
        # Similar objections should produce same key
        key1 = optimizer._generate_objection_key("too expensive")
        key2 = optimizer._generate_objection_key("it's too expensive for me")
        assert key1 == key2  # Both should be "objection:expensive"

        # Different objection types should produce different keys
        key3 = optimizer._generate_objection_key("need to think about it")
        assert key1 != key3

    def test_instant_coaching_latency(self, optimizer):
        """Test that instant coaching meets sub-25ms target."""
        messages = [
            "That's too expensive for my budget",
            "I need to think about it",
            "Hello, I'm interested in homes"
        ]

        for message in messages:
            response, latency_ms = optimizer.get_instant_coaching(message, "discovery")

            # Should be well under 25ms for cached responses
            assert latency_ms < 25.0, f"Latency {latency_ms}ms exceeds 25ms target for: {message}"
            assert "suggestions" in response

    def test_objection_classification(self, optimizer):
        """Test objection classification."""
        assert optimizer._classify_objection("too expensive") == "price_concern"
        assert optimizer._classify_objection("need to think about it") == "decision_delay"
        assert optimizer._classify_objection("I'm too busy right now") == "timing"
        assert optimizer._classify_objection("working with another agent") == "competition"

    def test_coaching_response_structure(self, optimizer):
        """Test coaching response structure."""
        response, _ = optimizer.get_instant_coaching("I'm interested in a 3-bedroom home", "discovery")

        assert "suggestions" in response
        assert isinstance(response["suggestions"], list)
        assert len(response["suggestions"]) > 0

    def test_performance_stats(self, optimizer):
        """Test performance statistics collection."""
        # Make some requests
        for i in range(10):
            optimizer.get_instant_coaching(f"test message {i}", "discovery")

        stats = optimizer.get_performance_stats()

        assert stats["total_requests"] == 10
        assert "avg_latency_ms" in stats
        assert "target_compliance_rate" in stats
        assert stats["avg_latency_ms"] < 25.0  # Should be well under target

    def test_cache_enhanced_response(self, optimizer):
        """Test caching enhanced responses."""
        message = "unique test message for caching"
        enhanced_response = {
            "suggestions": ["Enhanced suggestion 1", "Enhanced suggestion 2"],
            "confidence": 0.95
        }

        # Cache the response
        optimizer.cache_enhanced_response(message, enhanced_response)

        # Retrieve from cache
        cache_key = optimizer._generate_message_key(message)
        assert cache_key in optimizer.hot_cache
        assert optimizer.hot_cache[cache_key]["cached"] is True


# ============================================================================
# Integration Tests
# ============================================================================

class TestClaudeIntegration:
    """Integration tests for Claude component enhancements."""

    @pytest.mark.asyncio
    async def test_mixin_real_time_coaching_demo(self):
        """Test real-time coaching in demo mode."""
        from ghl_real_estate_ai.streamlit_components.claude_component_mixin import (
            ClaudeComponentMixin
        )

        mixin = ClaudeComponentMixin(demo_mode=True)

        response = await mixin.get_real_time_coaching(
            agent_id="test_agent",
            conversation_context={"test": True},
            prospect_message="I'm looking for a 3-bedroom home",
            conversation_stage="discovery"
        )

        assert response is not None
        assert "suggestions" in response
        assert "demo_mode" in response

    @pytest.mark.asyncio
    async def test_mixin_semantic_analysis_demo(self):
        """Test semantic analysis in demo mode."""
        from ghl_real_estate_ai.streamlit_components.claude_component_mixin import (
            ClaudeComponentMixin
        )

        mixin = ClaudeComponentMixin(demo_mode=True)

        messages = [
            {"speaker": "prospect", "content": "I'm looking for a home under $500k"},
            {"speaker": "agent", "content": "Great! What areas interest you?"}
        ]

        response = await mixin.analyze_lead_semantics(
            conversation_messages=messages,
            include_preferences=True,
            include_qualification=True
        )

        assert response is not None
        assert "intent_analysis" in response
        assert "semantic_preferences" in response

    @pytest.mark.asyncio
    async def test_mixin_executive_summary_demo(self):
        """Test executive summary generation in demo mode."""
        from ghl_real_estate_ai.streamlit_components.claude_component_mixin import (
            ClaudeComponentMixin
        )

        mixin = ClaudeComponentMixin(demo_mode=True)

        data = {
            "revenue": 500000,
            "leads": 150,
            "conversion_rate": 12.5
        }

        response = await mixin.generate_executive_summary(
            data=data,
            context="business_intelligence",
            tone="professional"
        )

        assert response is not None
        assert "summary" in response
        assert "key_insights" in response

    def test_instant_coaching_performance_target(self):
        """Test that instant coaching consistently meets performance targets."""
        from ghl_real_estate_ai.services.claude_performance_optimizer import (
            get_sub25ms_optimizer
        )

        optimizer = get_sub25ms_optimizer()

        # Run 100 requests and check performance
        total_requests = 100
        target_met = 0
        latencies = []

        messages = [
            "too expensive",
            "need to think about it",
            "not the right time",
            "just looking",
            "interested in a home",
            "what's your commission?",
            "can you show me some properties?",
            "I'm working with another agent",
            "maybe next month",
            "send me more info"
        ]

        for i in range(total_requests):
            message = messages[i % len(messages)]
            response, latency_ms = optimizer.get_instant_coaching(message, "discovery")
            latencies.append(latency_ms)
            if latency_ms <= 25.0:
                target_met += 1

        # Should meet target at least 95% of the time
        target_compliance = target_met / total_requests
        avg_latency = sum(latencies) / len(latencies)

        assert target_compliance >= 0.95, f"Target compliance {target_compliance:.1%} below 95%"
        assert avg_latency < 25.0, f"Average latency {avg_latency:.1f}ms exceeds 25ms"


# ============================================================================
# Performance Benchmark Tests
# ============================================================================

class TestPerformanceBenchmarks:
    """Performance benchmark tests for Claude enhancements."""

    def test_sub25ms_target_under_load(self):
        """Test sub-25ms target under simulated load."""
        from ghl_real_estate_ai.services.claude_performance_optimizer import (
            Sub25msCoachingOptimizer
        )

        optimizer = Sub25msCoachingOptimizer()

        # Simulate 1000 requests
        latencies = []
        for i in range(1000):
            _, latency = optimizer.get_instant_coaching(
                f"test message variation {i % 50}",
                "discovery"
            )
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        max_latency = max(latencies)

        print(f"\nPerformance Results:")
        print(f"  Average latency: {avg_latency:.2f}ms")
        print(f"  P95 latency: {p95_latency:.2f}ms")
        print(f"  Max latency: {max_latency:.2f}ms")

        assert avg_latency < 10.0, f"Avg latency {avg_latency}ms too high"
        assert p95_latency < 25.0, f"P95 latency {p95_latency}ms exceeds target"

    def test_cache_efficiency(self):
        """Test cache efficiency under repeated queries."""
        from ghl_real_estate_ai.streamlit_components.claude_component_mixin import (
            ClaudeComponentMixin,
            ClaudeOperationType
        )

        mixin = ClaudeComponentMixin(demo_mode=True)

        # Cache a response
        cache_key = "benchmark_test_key"
        test_response = {"test": "data"}
        mixin._cache_response(cache_key, test_response, ClaudeOperationType.REAL_TIME_COACHING)

        # Measure cache retrieval time
        retrieval_times = []
        for _ in range(1000):
            start = time.time()
            _ = mixin._get_cached_response(cache_key)
            retrieval_times.append((time.time() - start) * 1000)

        avg_retrieval = sum(retrieval_times) / len(retrieval_times)
        print(f"\nCache Retrieval Performance:")
        print(f"  Average retrieval time: {avg_retrieval:.3f}ms")

        # Cache retrieval should be sub-millisecond
        assert avg_retrieval < 1.0, f"Cache retrieval {avg_retrieval}ms too slow"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
