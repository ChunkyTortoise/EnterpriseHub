"""
Tests for ClaudeConciergeAgent and related classes.

Classes tested:
    ClaudeConciergeAgent   - Main concierge agent
    UserIntent             - User intent enum
    PlatformContext        - Platform context enum
    UserSession            - Session tracking dataclass
    AgentCapability        - Agent capability dataclass
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.agents.claude_concierge_agent import (
    ClaudeConciergeAgent,
    UserIntent,
    PlatformContext,
    UserSession,
    AgentCapability,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def agent():
    """Create ClaudeConciergeAgent with external services mocked."""
    with patch("ghl_real_estate_ai.agents.claude_concierge_agent.get_enhanced_bot_orchestrator"):
        with patch("ghl_real_estate_ai.agents.claude_concierge_agent.ClaudeAssistant"):
            with patch("ghl_real_estate_ai.agents.claude_concierge_agent.get_event_publisher"):
                return ClaudeConciergeAgent()


@pytest.fixture
def sample_session():
    """Create a sample UserSession for testing."""
    return UserSession(
        user_id="test-user-1",
        session_start=datetime.now(),
        last_activity=datetime.now(),
        current_context=PlatformContext.DASHBOARD,
        detected_intent=UserIntent.EXPLORING,
    )


# ---------------------------------------------------------------------------
# ClaudeConciergeAgent initialization
# ---------------------------------------------------------------------------


class TestAgentInitialization:
    """Tests for ClaudeConciergeAgent creation and defaults."""

    def test_agent_initializes(self, agent):
        """Agent creates successfully with default attributes."""
        assert agent is not None
        assert hasattr(agent, "performance_metrics")
        assert hasattr(agent, "knowledge_engine")
        assert hasattr(agent, "context_engine")
        assert hasattr(agent, "multi_agent_coordinator")
        assert hasattr(agent, "proactive_assistant")

    def test_performance_metrics_initial_values(self, agent):
        """Performance metrics start with expected keys and zero values."""
        metrics = agent.performance_metrics
        assert "interactions_handled" in metrics
        assert "recommendations_generated" in metrics
        assert "agent_coordinations" in metrics
        assert "user_satisfaction_score" in metrics
        assert "proactive_assists" in metrics
        assert metrics["interactions_handled"] == 0
        assert metrics["recommendations_generated"] == 0


# ---------------------------------------------------------------------------
# Agent status
# ---------------------------------------------------------------------------


class TestAgentStatus:
    """Tests for agent status retrieval."""

    @pytest.mark.asyncio
    async def test_get_status_has_performance_metrics(self, agent):
        """get_concierge_status returns dict with 'performance_metrics' key."""
        status = await agent.get_concierge_status()
        assert isinstance(status, dict)
        assert "performance_metrics" in status


# ---------------------------------------------------------------------------
# PlatformContext enum
# ---------------------------------------------------------------------------


class TestPlatformContext:
    """Tests for PlatformContext enum values."""

    def test_platform_context_enum_values(self):
        """PlatformContext has expected enum members."""
        assert PlatformContext.DASHBOARD.value == "dashboard"
        assert PlatformContext.LEAD_MANAGEMENT.value == "lead_management"
        assert PlatformContext.PROPERTY_ANALYSIS.value == "property_analysis"
        assert PlatformContext.BOT_MANAGEMENT.value == "bot_management"
        assert PlatformContext.REPORTS.value == "reports"
        assert PlatformContext.SETTINGS.value == "settings"
        assert PlatformContext.INTEGRATIONS.value == "integrations"
        assert PlatformContext.MOBILE.value == "mobile"


# ---------------------------------------------------------------------------
# UserIntent enum
# ---------------------------------------------------------------------------


class TestUserIntent:
    """Tests for UserIntent enum values."""

    def test_user_intent_enum_values(self):
        """UserIntent has expected enum members."""
        assert UserIntent.EXPLORING.value == "exploring"
        assert UserIntent.WORKING.value == "working"
        assert UserIntent.TROUBLESHOOTING.value == "troubleshooting"
        assert UserIntent.ANALYZING.value == "analyzing"
        assert UserIntent.CONFIGURING.value == "configuring"
        assert UserIntent.LEARNING.value == "learning"


# ---------------------------------------------------------------------------
# Context detection
# ---------------------------------------------------------------------------


class TestContextDetection:
    """Tests for context and intent detection via ContextAwarenessEngine."""

    def test_detect_context_dashboard(self, agent):
        """Dashboard page activity maps to DASHBOARD context."""
        ctx = agent.context_engine._detect_context({"page": "dashboard", "action": "view"})
        assert ctx == PlatformContext.DASHBOARD

    def test_detect_context_lead_management(self, agent):
        """Lead page activity maps to LEAD_MANAGEMENT context."""
        ctx = agent.context_engine._detect_context({"page": "lead-management", "action": "view"})
        assert ctx == PlatformContext.LEAD_MANAGEMENT

    def test_detect_intent_working(self, agent):
        """Working-related action maps to WORKING intent."""
        intent = agent.context_engine._detect_intent({"action": "edit", "duration": 120})
        assert intent == UserIntent.WORKING

    def test_detect_intent_exploring(self, agent):
        """Short duration browse maps to EXPLORING intent."""
        intent = agent.context_engine._detect_intent({"action": "browse", "duration": 10})
        assert intent == UserIntent.EXPLORING


# ---------------------------------------------------------------------------
# UserSession
# ---------------------------------------------------------------------------


class TestUserSession:
    """Tests for UserSession dataclass."""

    def test_user_session_activity_tracking(self, sample_session):
        """Activity history can be appended and accumulates entries."""
        sample_session.activity_history.append({"action": "click", "timestamp": datetime.now()})
        sample_session.activity_history.append({"action": "navigate", "timestamp": datetime.now()})
        assert len(sample_session.activity_history) == 2

    def test_user_session_defaults(self, sample_session):
        """Session has correct default values."""
        assert sample_session.competency_level == "intermediate"
        assert isinstance(sample_session.activity_history, list)
        assert isinstance(sample_session.frustration_indicators, list)
        assert isinstance(sample_session.preferences, dict)


# ---------------------------------------------------------------------------
# AgentCapability
# ---------------------------------------------------------------------------


class TestAgentCapability:
    """Tests for AgentCapability dataclass."""

    def test_agent_capability_has_required_fields(self):
        """AgentCapability dataclass has agent_name and capabilities."""
        cap = AgentCapability(
            agent_name="Test Agent",
            agent_type="test",
            capabilities=["cap1", "cap2"],
            current_status="active",
        )
        assert cap.agent_name == "Test Agent"
        assert "cap1" in cap.capabilities
        assert cap.performance_score == 1.0  # default

    def test_agent_capability_optional_fields(self):
        """AgentCapability optional fields have correct defaults."""
        cap = AgentCapability(
            agent_name="Test Agent",
            agent_type="test",
            capabilities=[],
            current_status="active",
        )
        assert cap.last_used is None
        assert cap.specializations == []
