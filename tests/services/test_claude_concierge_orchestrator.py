"""
Tests for ClaudeConciergeOrchestrator and supporting classes.

Classes tested:
    ClaudeConciergeOrchestrator - Main orchestrator
    JorgePreferenceEngine       - Preference learning engine
    PatternDetectionEngine      - Decision pattern detection
    JorgeBusinessRules          - Business rule management
    ConciergeResponse           - Response dataclass
    ConciergeMode               - Mode enum
"""

import os
from dataclasses import asdict
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.claude_concierge_orchestrator import (
    ClaudeConciergeOrchestrator,
    ConciergeMode,
    ConciergeResponse,
    IntelligenceScope,
    JorgeBusinessRules,
    JorgePreferenceEngine,
    PatternDetectionEngine,
)
from ghl_real_estate_ai.services.claude_concierge_orchestrator import (
    PlatformContext as BackendPlatformContext,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_claude():
    """Mock ClaudeOrchestrator with process_request returning XML-tagged content."""
    claude = AsyncMock()
    claude.process_request = AsyncMock(
        return_value=MagicMock(
            content="<primary_guidance>Test guidance</primary_guidance>"
            "<urgency_level>low</urgency_level>"
        )
    )
    return claude


@pytest.fixture
def mock_cache():
    """Mock cache service."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


@pytest.fixture
def mock_memory():
    """Mock MemoryService."""
    memory = MagicMock()
    memory.add_memory = AsyncMock()
    memory.search_memories = AsyncMock(return_value=[])
    return memory


@pytest.fixture
def mock_analytics():
    """Mock AnalyticsService."""
    analytics = MagicMock()
    analytics.track_event = AsyncMock()
    return analytics


@pytest.fixture
def mock_ghl_live_data():
    """Mock GHL live data service."""
    ghl = MagicMock()
    ghl.generate_omnipresent_context = AsyncMock(return_value={
        "active_leads": [],
        "bot_statuses": {},
        "user_activity": [],
        "business_metrics": {},
        "active_properties": [],
        "market_conditions": {},
        "priority_actions": [],
        "pending_notifications": [],
        "jorge_preferences": {},
    })
    return ghl


@pytest.fixture
def orchestrator(mock_claude, mock_cache, mock_memory, mock_analytics, mock_ghl_live_data):
    """Create ClaudeConciergeOrchestrator with all dependencies mocked."""
    with patch(
        "ghl_real_estate_ai.services.claude_concierge_orchestrator.get_cache_service",
        return_value=mock_cache,
    ), patch(
        "ghl_real_estate_ai.services.claude_concierge_orchestrator.MemoryService",
        return_value=mock_memory,
    ), patch(
        "ghl_real_estate_ai.services.claude_concierge_orchestrator.AnalyticsService",
        return_value=mock_analytics,
    ), patch(
        "ghl_real_estate_ai.services.claude_concierge_orchestrator.get_ghl_live_data_service",
        return_value=mock_ghl_live_data,
    ):
        orch = ClaudeConciergeOrchestrator(claude_orchestrator=mock_claude)
        return orch


@pytest.fixture
def platform_context():
    """Standard platform context for testing."""
    return BackendPlatformContext(
        current_page="Lead Dashboard",
        user_role="agent",
        session_id="test-session-123",
    )


# ---------------------------------------------------------------------------
# ClaudeConciergeOrchestrator initialization
# ---------------------------------------------------------------------------


class TestOrchestratorInit:
    """Tests for orchestrator initialization."""

    def test_orchestrator_initializes(self, orchestrator):
        """Creates with required state attributes."""
        assert hasattr(orchestrator, "session_contexts")
        assert hasattr(orchestrator, "context_cache")
        assert hasattr(orchestrator, "generated_suggestions")
        assert hasattr(orchestrator, "metrics")
        assert isinstance(orchestrator.session_contexts, dict)
        assert isinstance(orchestrator.context_cache, dict)
        assert isinstance(orchestrator.generated_suggestions, dict)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class TestMetrics:
    """Tests for orchestrator metrics."""

    def test_get_metrics_returns_structure(self, orchestrator):
        """get_metrics returns dict with all required keys."""
        metrics = orchestrator.get_metrics()
        assert "requests_processed" in metrics
        assert "avg_response_time_ms" in metrics
        assert "errors" in metrics
        assert "cache_hit_rate" in metrics
        assert "active_sessions" in metrics
        assert "learning_events" in metrics

    def test_get_metrics_zero_initially(self, orchestrator):
        """All numeric metrics start at 0."""
        metrics = orchestrator.get_metrics()
        assert metrics["requests_processed"] == 0
        assert metrics["avg_response_time_ms"] == 0
        assert metrics["errors"] == 0
        assert metrics["learning_events"] == 0
        assert metrics["cache_hit_rate"] == 0.0


# ---------------------------------------------------------------------------
# Contextual guidance
# ---------------------------------------------------------------------------


class TestContextualGuidance:
    """Tests for generate_contextual_guidance."""

    @pytest.mark.asyncio
    async def test_generate_contextual_guidance_returns_response(self, orchestrator, platform_context):
        """Returns a ConciergeResponse when given mocked claude."""
        response = await orchestrator.generate_contextual_guidance(
            context=platform_context,
            mode=ConciergeMode.PROACTIVE,
            scope=IntelligenceScope.PLATFORM_WIDE,
            use_live_data=False,
        )
        assert isinstance(response, ConciergeResponse)
        assert response.primary_guidance  # non-empty

    @pytest.mark.asyncio
    async def test_fallback_on_claude_error(self, orchestrator, platform_context, mock_claude):
        """When claude.process_request raises, returns ConciergeResponse (not exception)."""
        mock_claude.process_request = AsyncMock(side_effect=RuntimeError("API down"))
        response = await orchestrator.generate_contextual_guidance(
            context=platform_context,
            mode=ConciergeMode.PROACTIVE,
            scope=IntelligenceScope.PLATFORM_WIDE,
            use_live_data=False,
        )
        assert isinstance(response, ConciergeResponse)

    @pytest.mark.asyncio
    async def test_fallback_response_has_guidance(self, orchestrator, platform_context, mock_claude):
        """Fallback response has non-empty primary_guidance."""
        mock_claude.process_request = AsyncMock(side_effect=RuntimeError("API down"))
        response = await orchestrator.generate_contextual_guidance(
            context=platform_context,
            mode=ConciergeMode.PROACTIVE,
            scope=IntelligenceScope.PLATFORM_WIDE,
            use_live_data=False,
        )
        assert response.primary_guidance
        assert len(response.primary_guidance) > 0


# ---------------------------------------------------------------------------
# JorgePreferenceEngine
# ---------------------------------------------------------------------------


class TestJorgePreferenceEngine:
    """Tests for JorgePreferenceEngine."""

    @pytest.mark.asyncio
    async def test_jorge_preference_engine_update_returns_true(self, mock_cache):
        """update_preferences returns True on success."""
        engine = JorgePreferenceEngine(mock_cache)
        result = await engine.update_preferences({
            "pattern_type": "test_pattern",
            "confidence": 0.8,
        })
        assert result is True

    @pytest.mark.asyncio
    async def test_jorge_preference_engine_stores_pattern(self, mock_cache):
        """After update, cache.set was called with the aggregate key."""
        engine = JorgePreferenceEngine(mock_cache)
        await engine.update_preferences({
            "pattern_type": "test_pattern",
            "confidence": 0.8,
        })
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert call_args[0][0] == "jorge_preferences:aggregate"

    @pytest.mark.asyncio
    async def test_jorge_preference_engine_decay_factor(self, mock_cache):
        """Calling update twice applies 0.7/0.3 weighting (not just overwrite)."""
        engine = JorgePreferenceEngine(mock_cache)

        # First call: weight starts at 0 -> 0.7*0 + 0.3*0.8 = 0.24
        await engine.update_preferences({"pattern_type": "test", "confidence": 0.8})
        first_call_data = mock_cache.set.call_args[0][1]

        # Reset mock to track second call, but simulate return of first data
        mock_cache.get = AsyncMock(return_value=first_call_data)
        mock_cache.set.reset_mock()

        # Second call: weight = 0.7*0.24 + 0.3*0.9 = 0.168 + 0.27 = 0.438
        await engine.update_preferences({"pattern_type": "test", "confidence": 0.9})
        second_call_data = mock_cache.set.call_args[0][1]

        # The weight should not simply be the raw confidence
        assert second_call_data["test"]["weight"] != 0.9
        assert second_call_data["test"]["count"] == 2


# ---------------------------------------------------------------------------
# PatternDetectionEngine
# ---------------------------------------------------------------------------


class TestPatternDetectionEngine:
    """Tests for PatternDetectionEngine."""

    @pytest.mark.asyncio
    async def test_pattern_detection_success_outcome(self):
        """Success outcome produces pattern_type ending with '_success'."""
        engine = PatternDetectionEngine()
        pattern = await engine.extract_pattern(
            decision={"type": "lead_routing"},
            outcome={"success": True, "result": "converted"},
        )
        assert pattern is not None
        assert pattern["pattern_type"].endswith("_success")
        assert pattern["pattern_type"] == "lead_routing_success"

    @pytest.mark.asyncio
    async def test_pattern_detection_failure_outcome(self):
        """Failure outcome produces pattern_type ending with '_failure'."""
        engine = PatternDetectionEngine()
        pattern = await engine.extract_pattern(
            decision={"type": "pricing"},
            outcome={"success": False, "reason": "overpriced"},
        )
        assert pattern is not None
        assert pattern["pattern_type"].endswith("_failure")
        assert pattern["pattern_type"] == "pricing_failure"

    @pytest.mark.asyncio
    async def test_pattern_detection_high_severity_weight(self):
        """Failure with severity='high' produces confidence==0.9."""
        engine = PatternDetectionEngine()
        pattern = await engine.extract_pattern(
            decision={"type": "deal"},
            outcome={"success": False, "severity": "high"},
        )
        assert pattern["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_pattern_detection_medium_severity_weight(self):
        """Failure with severity='medium' produces confidence==0.6."""
        engine = PatternDetectionEngine()
        pattern = await engine.extract_pattern(
            decision={"type": "deal"},
            outcome={"success": False, "severity": "medium"},
        )
        assert pattern["confidence"] == 0.6


# ---------------------------------------------------------------------------
# JorgeBusinessRules
# ---------------------------------------------------------------------------


class TestJorgeBusinessRules:
    """Tests for JorgeBusinessRules."""

    def test_business_rules_get_workflow_id_returns_none_without_env(self):
        """get_workflow_id returns None when env var not set."""
        rules = JorgeBusinessRules()
        # Ensure env var is not set
        os.environ.pop("HOT_SELLER_WORKFLOW_ID", None)
        result = rules.get_workflow_id("hot_seller")
        assert result is None

    def test_business_rules_get_workflow_id_reads_env(self, monkeypatch):
        """get_workflow_id reads the corresponding env var."""
        monkeypatch.setenv("HOT_SELLER_WORKFLOW_ID", "wf-12345")
        rules = JorgeBusinessRules()
        result = rules.get_workflow_id("hot_seller")
        assert result == "wf-12345"

    def test_business_rules_get_rule(self):
        """get_rule('commission_rate') returns 0.06."""
        rules = JorgeBusinessRules()
        assert rules.get_rule("commission_rate") == 0.06

    def test_business_rules_get_rule_missing(self):
        """get_rule returns None for unknown rules."""
        rules = JorgeBusinessRules()
        assert rules.get_rule("nonexistent_rule") is None


# ---------------------------------------------------------------------------
# ConciergeMode enum
# ---------------------------------------------------------------------------


class TestConciergeMode:
    """Tests for ConciergeMode enum values."""

    def test_concierge_mode_enum_values(self):
        """ConciergeMode has PROACTIVE, REACTIVE, PRESENTATION, FIELD_WORK, EXECUTIVE."""
        assert ConciergeMode.PROACTIVE.value == "proactive"
        assert ConciergeMode.REACTIVE.value == "reactive"
        assert ConciergeMode.PRESENTATION.value == "presentation"
        assert ConciergeMode.FIELD_WORK.value == "field_work"
        assert ConciergeMode.EXECUTIVE.value == "executive"


# ---------------------------------------------------------------------------
# ConciergeResponse dataclass
# ---------------------------------------------------------------------------


class TestConciergeResponse:
    """Tests for ConciergeResponse dataclass."""

    def test_concierge_response_serializable(self):
        """ConciergeResponse can be serialized via asdict."""
        resp = ConciergeResponse(
            primary_guidance="Test guidance",
            urgency_level="low",
            confidence_score=0.85,
        )
        data = asdict(resp)
        assert data["primary_guidance"] == "Test guidance"
        assert data["urgency_level"] == "low"
        assert data["confidence_score"] == 0.85
        assert isinstance(data["immediate_actions"], list)
