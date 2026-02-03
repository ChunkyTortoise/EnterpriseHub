"""
Tests for Jorge Seller Bot Feature Flag Integration

Validates that optional features (Progressive Skills, Agent Mesh, MCP)
initialize correctly when enabled/disabled, degrade gracefully when
dependencies are unavailable, and track usage statistics properly.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import logging

from ghl_real_estate_ai.agents.jorge_seller_bot import (
    JorgeSellerBot,
    JorgeFeatureConfig,
)


# ─── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def all_features_disabled():
    return JorgeFeatureConfig(
        enable_progressive_skills=False,
        enable_agent_mesh=False,
        enable_mcp_integration=False,
        enable_adaptive_questioning=False,
        enable_track3_intelligence=False,
        enable_bot_intelligence=False,
    )


@pytest.fixture
def all_features_enabled():
    return JorgeFeatureConfig(
        enable_progressive_skills=True,
        enable_agent_mesh=True,
        enable_mcp_integration=True,
        enable_adaptive_questioning=True,
        enable_track3_intelligence=False,  # Avoid ML engine dependency in tests
        enable_bot_intelligence=False,  # Avoid middleware dependency in tests
    )


@pytest.fixture
def mock_dependencies():
    """Patch all external service constructors to return mocks."""
    with patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.LeadIntentDecoder"
    ) as mock_intent, patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.ClaudeAssistant"
    ) as mock_claude, patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.get_event_publisher"
    ) as mock_events:
        mock_intent.return_value = MagicMock()
        mock_claude.return_value = MagicMock()
        mock_events.return_value = MagicMock()
        yield {
            "intent_decoder": mock_intent,
            "claude": mock_claude,
            "event_publisher": mock_events,
        }


# ─── Default initialization ─────────────────────────────────────────


class TestDefaultInitialization:
    """Seller bot should work with all optional features disabled."""

    def test_creates_with_default_config(self, mock_dependencies):
        bot = JorgeSellerBot()
        assert bot.config is not None
        assert bot.config.enable_progressive_skills is False
        assert bot.config.enable_agent_mesh is False
        assert bot.config.enable_mcp_integration is False

    def test_optional_services_none_when_disabled(
        self, mock_dependencies, all_features_disabled
    ):
        bot = JorgeSellerBot(config=all_features_disabled)
        assert bot.skills_manager is None
        assert bot.token_tracker is None
        assert bot.mesh_coordinator is None
        assert bot.mcp_client is None
        assert bot.conversation_memory is None
        assert bot.question_engine is None

    def test_workflow_stats_initialized(self, mock_dependencies, all_features_disabled):
        bot = JorgeSellerBot(config=all_features_disabled)
        assert bot.workflow_stats["total_interactions"] == 0
        assert bot.workflow_stats["progressive_skills_usage"] == 0
        assert bot.workflow_stats["mesh_orchestrations"] == 0
        assert bot.workflow_stats["mcp_calls"] == 0


# ─── Progressive Skills feature flag ────────────────────────────────


class TestProgressiveSkillsFlag:
    """Progressive Skills Manager should init only when flag AND deps available."""

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.PROGRESSIVE_SKILLS_AVAILABLE",
        True,
    )
    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.ProgressiveSkillsManager"
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_token_tracker")
    def test_initializes_when_enabled_and_available(
        self, mock_tracker, mock_skills, mock_dependencies
    ):
        mock_skills.return_value = MagicMock()
        mock_tracker.return_value = MagicMock()

        config = JorgeFeatureConfig(
            enable_progressive_skills=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        assert bot.skills_manager is not None
        assert bot.token_tracker is not None
        mock_skills.assert_called_once()
        mock_tracker.assert_called_once()

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.PROGRESSIVE_SKILLS_AVAILABLE",
        False,
    )
    def test_degrades_gracefully_when_unavailable(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_progressive_skills=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        # Bot creates successfully but service is None
        assert bot.skills_manager is None
        assert bot.token_tracker is None
        # Config still reflects the request
        assert bot.config.enable_progressive_skills is True

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.PROGRESSIVE_SKILLS_AVAILABLE",
        True,
    )
    def test_not_initialized_when_disabled(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_progressive_skills=False,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert bot.skills_manager is None
        assert bot.token_tracker is None


# ─── Agent Mesh feature flag ────────────────────────────────────────


class TestAgentMeshFlag:
    """Agent Mesh Coordinator should init only when flag AND deps available."""

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.AGENT_MESH_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mesh_coordinator")
    def test_initializes_when_enabled_and_available(
        self, mock_coordinator, mock_dependencies
    ):
        mock_coordinator.return_value = MagicMock()

        config = JorgeFeatureConfig(
            enable_agent_mesh=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        assert bot.mesh_coordinator is not None
        mock_coordinator.assert_called_once()

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.AGENT_MESH_AVAILABLE",
        False,
    )
    def test_degrades_gracefully_when_unavailable(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_agent_mesh=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        # Bot creates successfully but service is None
        assert bot.mesh_coordinator is None
        # Config still reflects the request
        assert bot.config.enable_agent_mesh is True

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.AGENT_MESH_AVAILABLE",
        True,
    )
    def test_not_initialized_when_disabled(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_agent_mesh=False,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert bot.mesh_coordinator is None


# ─── MCP Integration feature flag ───────────────────────────────────


class TestMCPIntegrationFlag:
    """MCP Client should init only when flag AND deps available."""

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.MCP_INTEGRATION_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mcp_client")
    def test_initializes_when_enabled_and_available(
        self, mock_mcp, mock_dependencies
    ):
        mock_mcp.return_value = MagicMock()

        config = JorgeFeatureConfig(
            enable_mcp_integration=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        assert bot.mcp_client is not None
        mock_mcp.assert_called_once()

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.MCP_INTEGRATION_AVAILABLE",
        False,
    )
    def test_degrades_gracefully_when_unavailable(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_mcp_integration=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        # Bot creates successfully but service is None
        assert bot.mcp_client is None
        # Config still reflects the request
        assert bot.config.enable_mcp_integration is True

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.MCP_INTEGRATION_AVAILABLE",
        True,
    )
    def test_not_initialized_when_disabled(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_mcp_integration=False,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert bot.mcp_client is None


# ─── Adaptive Questioning feature flag ──────────────────────────────


class TestAdaptiveQuestioningFlag:
    """Adaptive questioning components should init only when enabled."""

    def test_initializes_when_enabled(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_adaptive_questioning=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert bot.conversation_memory is not None
        assert bot.question_engine is not None

    def test_not_initialized_when_disabled(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_adaptive_questioning=False,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert bot.conversation_memory is None
        assert bot.question_engine is None


# ─── Combined feature flags ─────────────────────────────────────────


class TestCombinedFeatureFlags:
    """Test multiple features enabled simultaneously."""

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.PROGRESSIVE_SKILLS_AVAILABLE",
        True,
    )
    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.AGENT_MESH_AVAILABLE",
        True,
    )
    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.MCP_INTEGRATION_AVAILABLE",
        True,
    )
    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.ProgressiveSkillsManager"
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_token_tracker")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mesh_coordinator")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mcp_client")
    def test_all_three_features_initialize(
        self,
        mock_mcp,
        mock_mesh,
        mock_tracker,
        mock_skills,
        mock_dependencies,
    ):
        mock_skills.return_value = MagicMock()
        mock_tracker.return_value = MagicMock()
        mock_mesh.return_value = MagicMock()
        mock_mcp.return_value = MagicMock()

        config = JorgeFeatureConfig(
            enable_progressive_skills=True,
            enable_agent_mesh=True,
            enable_mcp_integration=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        assert bot.skills_manager is not None
        assert bot.mesh_coordinator is not None
        assert bot.mcp_client is not None

    def test_selective_enabling(self, mock_dependencies):
        """Only progressive skills enabled, others stay off."""
        with patch(
            "ghl_real_estate_ai.agents.jorge_seller_bot.PROGRESSIVE_SKILLS_AVAILABLE",
            True,
        ), patch(
            "ghl_real_estate_ai.agents.jorge_seller_bot.ProgressiveSkillsManager"
        ) as mock_skills, patch(
            "ghl_real_estate_ai.agents.jorge_seller_bot.get_token_tracker"
        ) as mock_tracker:
            mock_skills.return_value = MagicMock()
            mock_tracker.return_value = MagicMock()

            config = JorgeFeatureConfig(
                enable_progressive_skills=True,
                enable_agent_mesh=False,
                enable_mcp_integration=False,
                enable_track3_intelligence=False,
                enable_bot_intelligence=False,
            )
            bot = JorgeSellerBot(config=config)

            assert bot.skills_manager is not None
            assert bot.mesh_coordinator is None
            assert bot.mcp_client is None


# ─── Workflow graph selection ────────────────────────────────────────


class TestWorkflowGraphSelection:
    """Bot should build the appropriate workflow graph based on features."""

    def test_standard_graph_when_adaptive_disabled(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_adaptive_questioning=False,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert bot.workflow is not None

    def test_adaptive_graph_when_adaptive_enabled(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_adaptive_questioning=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert bot.workflow is not None
        assert bot.question_engine is not None


# ─── JorgeFeatureConfig dataclass ────────────────────────────────────


class TestJorgeFeatureConfigDataclass:
    """Test the JorgeFeatureConfig dataclass itself."""

    def test_default_temperature_thresholds(self):
        config = JorgeFeatureConfig()
        assert config.temperature_thresholds == {"hot": 75, "warm": 50, "lukewarm": 25}

    def test_custom_temperature_thresholds(self):
        config = JorgeFeatureConfig(temperature_thresholds={"hot": 80, "warm": 60, "lukewarm": 30})
        assert config.temperature_thresholds["hot"] == 80

    def test_performance_defaults(self):
        config = JorgeFeatureConfig()
        assert config.max_concurrent_tasks == 5
        assert config.sla_response_time == 15
        assert config.cost_per_token == 0.000015

    def test_jorge_specific_defaults(self):
        config = JorgeFeatureConfig()
        assert config.commission_rate == 0.06
        assert config.friendly_approach_enabled is True

    def test_custom_tenant_id(self, mock_dependencies):
        bot = JorgeSellerBot(tenant_id="custom_seller")
        assert bot.tenant_id == "custom_seller"


# ─── Environment-to-bot integration ─────────────────────────────────


class TestEnvToBotIntegration:
    """End-to-end: env vars -> FeatureConfig -> JorgeFeatureConfig -> Bot."""

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.PROGRESSIVE_SKILLS_AVAILABLE",
        True,
    )
    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.ProgressiveSkillsManager"
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_token_tracker")
    def test_env_enables_progressive_skills_in_bot(
        self, mock_tracker, mock_skills, mock_dependencies
    ):
        """Simulate the production flow: env -> config -> bot init."""
        from ghl_real_estate_ai.config.feature_config import (
            load_feature_config_from_env,
            feature_config_to_jorge_kwargs,
        )

        mock_skills.return_value = MagicMock()
        mock_tracker.return_value = MagicMock()

        env = {"ENABLE_PROGRESSIVE_SKILLS": "true"}
        with patch.dict("os.environ", env, clear=True):
            feature_config = load_feature_config_from_env()
            kwargs = feature_config_to_jorge_kwargs(feature_config)
            jorge_config = JorgeFeatureConfig(**kwargs)
            bot = JorgeSellerBot(config=jorge_config)

            assert bot.skills_manager is not None
            assert bot.config.enable_progressive_skills is True
