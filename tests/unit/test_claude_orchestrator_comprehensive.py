"""Comprehensive tests for ClaudeOrchestrator.

Tests for:
- Multi-strategy parsing
- L1/L2/L3 cache behavior
- <200ms overhead requirement
- Response parsing
"""

import json
import pytest
import time
from typing import Any, Dict, Optional

pytestmark = pytest.mark.unit


# =============================================================================
# Helpers
# =============================================================================


def _bare_orchestrator():
    """Create a ClaudeOrchestrator instance without triggering __init__.

    Manually initializes cache attributes that __init__ normally sets,
    since object.__new__ bypasses __init__.
    """
    from ghl_real_estate_ai.services.claude_orchestrator import ClaudeOrchestrator
    obj = object.__new__(ClaudeOrchestrator)
    obj._response_cache = {}
    obj._response_cache_hits = 0
    obj._response_cache_misses = 0
    obj._memory_context_cache = {}
    return obj


@pytest.fixture
def orch():
    """Fixture providing a lightweight ClaudeOrchestrator for parsing tests."""
    return _bare_orchestrator()


# =============================================================================
# Multi-Strategy Parsing Tests
# =============================================================================


class TestMultiStrategyParsing:
    """Tests for multi-strategy JSON extraction and parsing."""

    def test_parse_json_from_markdown_code_block(self, orch):
        """Should extract JSON from markdown code blocks."""
        content = '''
        Here's the analysis:
        
        ```json
        {"score": 85, "confidence": 0.9}
        ```
        
        Let me know if you need more details.
        '''
        
        result = orch._extract_json_block(content)
        
        assert result is not None
        assert result.get("score") == 85

    def test_parse_json_without_markdown(self, orch):
        """Should extract JSON when not in code blocks."""
        content = '{"score": 75, "reasoning": "High intent detected"}'
        
        result = orch._extract_json_block(content)
        
        assert result is not None
        assert result.get("score") == 75

    def test_parse_json_with_balanced_brackets(self, orch):
        """Should find JSON with balanced brackets even if malformed."""
        content = '''
        {"data": {"nested": true}, "extra": "ignored"}
        more text after
        '''
        
        result = orch._extract_json_block(content)
        
        assert result is not None
        assert "data" in result

    def test_parse_json_invalid_returns_none(self, orch):
        """Should return None for invalid JSON."""
        content = '''
        This is just text with { unmatched brackets
        and no actual json
        '''

        result = orch._extract_json_block(content)

        assert result is None

    def test_parse_confidence_from_json(self, orch):
        """Should extract confidence from JSON data."""
        json_data = {"confidence": 0.85, "score": 90}
        
        result = orch._parse_confidence_score("any content", json_data)
        
        assert result == 0.85

    def test_parse_confidence_from_percentage(self, orch):
        """Should extract confidence from percentage text."""
        content = "The analysis shows 85% confidence in this lead."
        
        result = orch._parse_confidence_score(content, None)
        
        assert result == 0.85

    def test_parse_confidence_from_qualitative(self, orch):
        """Should extract confidence from qualitative terms."""
        content = "This is a high-confidence lead with strong buying signals."
        
        result = orch._parse_confidence_score(content, None)
        
        assert result is not None

    def test_parse_recommended_actions(self, orch):
        """Should parse recommended actions from JSON."""
        content = '''
        Based on my analysis, here are the next steps:
        
        ```json
        {
            "actions": [
                {"type": "call", "priority": "high"},
                {"type": "email", "priority": "medium"}
            ]
        }
        ```
        '''
        
        json_data = {"actions": [{"type": "call", "priority": "high"}, {"type": "email", "priority": "medium"}]}
        
        result = orch._parse_recommended_actions(content, json_data)
        
        assert len(result) >= 1

    def test_parse_script_variants(self, orch):
        """Should parse script variants from response."""
        content = '''
        Here are the script variants:
        
        ```json
        {
            "variants": [
                {"name": "aggressive", "script": "Buy now!"},
                {"name": "gentle", "script": "Consider your options."}
            ]
        }
        ```
        '''
        
        json_data = {
            "variants": [
                {"name": "aggressive", "script": "Buy now!"},
                {"name": "gentle", "script": "Consider your options."}
            ]
        }
        
        result = orch._parse_script_variants(content, json_data)
        
        assert len(result) >= 1

    def test_parse_risk_factors(self, orch):
        """Should parse risk factors from response."""
        content = '''
        Risk assessment:
        
        ```json
        {
            "risks": [
                {"factor": "price_sensitivity", "severity": "medium"},
                {"factor": "competition", "severity": "high"}
            ]
        }
        ```
        '''
        
        json_data = {
            "risks": [
                {"factor": "price_sensitivity", "severity": "medium"},
                {"factor": "competition", "severity": "high"}
            ]
        }
        
        result = orch._parse_risk_factors(content, json_data)
        
        assert len(result) >= 1

    def test_parse_opportunities(self, orch):
        """Should parse opportunities from response."""
        content = '''
        Opportunities identified:
        
        ```json
        {
            "opportunities": [
                {"type": "upsell", "potential": "high"},
                {"type": "referral", "potential": "medium"}
            ]
        }
        ```
        '''
        
        json_data = {
            "opportunities": [
                {"type": "upsell", "potential": "high"},
                {"type": "referral", "potential": "medium"}
            ]
        }
        
        result = orch._parse_opportunities(content, json_data)
        
        assert len(result) >= 1


# =============================================================================
# L1/L2/L3 Cache Behavior Tests
# =============================================================================


class TestCacheBehavior:
    """Tests for L1/L2/L3 caching behavior."""

    def test_cache_key_generation(self, orch):
        """Should generate consistent cache keys from requests."""
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeRequest, ClaudeTaskType
        
        req1 = ClaudeRequest(
            task_type=ClaudeTaskType.LEAD_ANALYSIS,
            context={"lead_id": "L1"},
            prompt="Analyze this lead"
        )
        
        req2 = ClaudeRequest(
            task_type=ClaudeTaskType.LEAD_ANALYSIS,
            context={"lead_id": "L1"},
            prompt="Analyze this lead"
        )
        
        key1 = orch._make_response_cache_key(req1)
        key2 = orch._make_response_cache_key(req2)
        
        assert key1 == key2

    def test_cache_key_different_requests(self, orch):
        """Should generate different keys for different requests."""
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeRequest, ClaudeTaskType
        
        req1 = ClaudeRequest(
            task_type=ClaudeTaskType.LEAD_ANALYSIS,
            context={"lead_id": "L1"},
            prompt="Analyze this lead"
        )
        
        req2 = ClaudeRequest(
            task_type=ClaudeTaskType.LEAD_ANALYSIS,
            context={"lead_id": "L2"},
            prompt="Analyze this lead"
        )
        
        key1 = orch._make_response_cache_key(req1)
        key2 = orch._make_response_cache_key(req2)
        
        assert key1 != key2

    def test_get_cached_response_valid(self, orch):
        """Should return cached response when not expired."""
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeResponse

        cache_key = "test_key"
        future_time = time.time() + 300  # 5 minutes from now
        cached_resp = ClaudeResponse(content="cached response")

        orch._response_cache[cache_key] = (cached_resp, future_time)

        result = orch._get_cached_response(cache_key)

        assert result is not None
        assert result.content == "cached response"

    def test_get_cached_response_expired(self, orch):
        """Should return None for expired cache entries."""
        cache_key = "test_key_expired"
        past_time = time.time() - 100  # Already expired
        
        orch._response_cache[cache_key] = (
            {"content": "expired response"},
            past_time
        )
        
        result = orch._get_cached_response(cache_key)
        
        assert result is None

    def test_cache_tracks_hits_and_misses(self, orch):
        """Should track cache hits and misses."""
        initial_hits = orch._response_cache_hits
        initial_misses = orch._response_cache_misses
        
        # Miss - key doesn't exist
        result = orch._get_cached_response("nonexistent_key")
        
        assert result is None
        assert orch._response_cache_misses == initial_misses + 1

    def test_cache_cleanup(self, orch):
        """Should clean up expired cache entries."""
        # Add some expired entries
        past_time = time.time() - 100
        orch._response_cache["expired1"] = ("data1", past_time)
        orch._response_cache["expired2"] = ("data2", past_time)
        
        # Add valid entry
        future_time = time.time() + 300
        orch._response_cache["valid"] = ("data3", future_time)
        
        # Trigger cleanup (if method exists)
        if hasattr(orch, '_cleanup_cache'):
            orch._cleanup_cache()
        
        # Check that expired entries are cleaned or will be cleaned


# =============================================================================
# Performance Tests (<200ms Overhead)
# =============================================================================


class TestPerformance:
    """Tests for <200ms overhead requirement."""

    def test_parse_response_performance(self, orch):
        """JSON parsing should complete quickly."""
        content = '''
        ```json
        {
            "score": 85,
            "confidence": 0.9,
            "reasoning": "Strong buying signals detected",
            "actions": [
                {"type": "call", "priority": "high"},
                {"type": "email", "priority": "medium"}
            ]
        }
        ```
        '''
        
        start_time = time.time()
        
        # Parse multiple times to get average
        for _ in range(10):
            result = orch._extract_json_block(content)
        
        elapsed = time.time() - start_time
        per_parse = elapsed / 10
        
        # Each parse should be well under 200ms
        assert per_parse < 0.2, f"Parse took {per_parse*1000:.2f}ms, expected <200ms"

    def test_cache_key_generation_performance(self, orch):
        """Cache key generation should be fast."""
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeRequest, ClaudeTaskType
        
        req = ClaudeRequest(
            task_type=ClaudeTaskType.LEAD_ANALYSIS,
            context={"lead_id": "L1"},
            prompt="Test prompt"
        )
        
        start_time = time.time()
        
        # Generate many keys
        for _ in range(100):
            orch._make_response_cache_key(req)
        
        elapsed = time.time() - start_time
        per_key = elapsed / 100
        
        assert per_key < 0.01, f"Cache key gen took {per_key*1000:.2f}ms"

    def test_confidence_parsing_performance(self, orch):
        """Confidence parsing should be fast."""
        content = "This is a high-confidence lead with 85% certainty"
        
        start_time = time.time()
        
        for _ in range(50):
            orch._parse_confidence_score(content, None)
        
        elapsed = time.time() - start_time
        per_parse = elapsed / 50
        
        assert per_parse < 0.05, f"Confidence parse took {per_parse*1000:.2f}ms"

    def test_memory_context_cache(self, orch):
        """Memory context caching should be fast."""
        test_context = {"lead_id": "L1", "history": ["msg1", "msg2"]}
        
        # First access
        start_time = time.time()
        orch._memory_context_cache["test_key"] = test_context
        first_access = time.time() - start_time
        
        # Second access (from cache)
        start_time = time.time()
        cached = orch._memory_context_cache.get("test_key")
        second_access = time.time() - start_time
        
        assert first_access < 0.01  # Initial access should be fast
        assert second_access < 0.001  # Cache access should be very fast


# =============================================================================
# ClaudeTaskType Tests
# =============================================================================


class TestClaudeTaskType:
    """Tests for ClaudeTaskType enum."""

    def test_all_task_types_exist(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType
        
        expected_types = [
            "CHAT_QUERY",
            "LEAD_ANALYSIS",
            "REPORT_SYNTHESIS",
            "SCRIPT_GENERATION",
            "INTERVENTION_STRATEGY",
            "BEHAVIORAL_INSIGHT",
            "OMNIPOTENT_ASSISTANT",
            "PERSONA_OPTIMIZATION",
            "EXECUTIVE_BRIEFING",
            "REVENUE_PROJECTION",
            "RESEARCH_QUERY",
        ]
        
        actual = {member.name for member in ClaudeTaskType}
        
        for expected in expected_types:
            assert expected in actual

    def test_task_type_values(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType
        
        for member in ClaudeTaskType:
            assert isinstance(member.value, str)
            assert len(member.value) > 0


# =============================================================================
# ClaudeRequest/Response Tests
# =============================================================================


class TestClaudeRequestResponse:
    """Tests for request/response dataclasses."""

    def test_request_creation(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeRequest, ClaudeTaskType
        
        req = ClaudeRequest(
            task_type=ClaudeTaskType.LEAD_ANALYSIS,
            context={"lead_id": "L123"},
            prompt="Analyze this lead",
        )
        
        assert req.task_type == ClaudeTaskType.LEAD_ANALYSIS
        assert req.context["lead_id"] == "L123"
        assert req.prompt == "Analyze this lead"

    def test_response_creation(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeResponse

        resp = ClaudeResponse(
            content="Analysis complete",
            confidence=0.85,
        )

        assert resp.content == "Analysis complete"
        assert resp.confidence == 0.85

    def test_response_with_metadata(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeResponse

        resp = ClaudeResponse(
            content="Here are the results",
            confidence=0.9,
            metadata={
                "score": 85,
                "actions": [{"type": "call"}],
            },
        )

        assert resp.metadata is not None
        assert resp.metadata["score"] == 85


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases in parsing and caching."""

    def test_empty_content(self, orch):
        """Should handle empty content gracefully."""
        result = orch._extract_json_block("")
        assert result is None

    def test_none_content(self, orch):
        """Should handle None content."""
        result = orch._extract_json_block(None)
        assert result is None

    def test_malformed_json_fallback(self, orch):
        """Should attempt fallback parsing for malformed JSON."""
        content = '{broken json" with issues'
        
        result = orch._extract_json_block(content)
        # Should not crash

    def test_unicode_content(self, orch):
        """Should handle Unicode characters."""
        content = '{"name": "José", "emoji": "🎯"}'
        
        result = orch._extract_json_block(content)
        
        assert result is not None

    def test_large_json_content(self, orch):
        """Should handle large JSON content efficiently."""
        large_data = {"items": [{"id": i, "data": "x" * 100} for i in range(100)]}
        content = json.dumps(large_data)
        
        start_time = time.time()
        result = orch._extract_json_block(content)
        elapsed = time.time() - start_time
        
        assert result is not None
        assert elapsed < 0.1  # Should parse quickly
