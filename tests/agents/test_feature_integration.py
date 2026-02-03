"""
Stream C: Feature Integration Tests

Comprehensive tests for the 3 optional features in the Jorge Seller Bot:
1. Progressive Skills Manager - Token reduction & fallback
2. Agent Mesh Coordinator - Parallel execution & cost-aware routing
3. MCP Integration - Service calls & circuit breaker fallback

Also validates no regression when all features are disabled.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from ghl_real_estate_ai.agents.jorge_seller_bot import (
    JorgeSellerBot,
    JorgeFeatureConfig,
    QualificationResult,
)
from ghl_real_estate_ai.config.feature_config import (
    ProgressiveSkillsConfig,
    AgentMeshConfig,
    MCPConfig,
    FeatureConfig,
    load_feature_config_from_env,
    feature_config_to_jorge_kwargs,
)


# ======================================================================
# Shared Fixtures
# ======================================================================


@pytest.fixture
def mock_core_dependencies():
    """Patch core dependencies (intent decoder, claude, event publisher, ML engine)."""
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


@pytest.fixture
def disabled_config():
    """Config with all 3 optional features disabled."""
    return JorgeFeatureConfig(
        enable_progressive_skills=False,
        enable_agent_mesh=False,
        enable_mcp_integration=False,
        enable_adaptive_questioning=False,
        enable_track3_intelligence=False,
        enable_bot_intelligence=False,
    )


@pytest.fixture
def sample_lead_data():
    """Realistic seller lead data for integration tests."""
    return {
        "lead_id": "test_seller_001",
        "lead_name": "Maria Garcia",
        "last_message": "I need to sell my house in 60 days",
        "interaction_count": 3,
        "lead_source": "zillow",
        "property_address": "1234 Victoria Ave, Rancho Cucamonga, CA 91730",
        "seller_temperature": "warm",
        "frs_score": 65,
        "pcs_score": 55,
        "email": "maria@example.com",
        "phone": "+19095551234",
    }


# ======================================================================
# 1. Progressive Skills Integration Tests
# ======================================================================


class TestProgressiveSkillsIntegration:
    """Progressive Skills: toggle, fallback, and token savings measurement."""

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.PROGRESSIVE_SKILLS_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.ProgressiveSkillsManager")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_token_tracker")
    def test_toggle_enabled(self, mock_tracker, mock_skills, mock_core_dependencies):
        """Skills manager is instantiated when flag is on and deps are present."""
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

    def test_toggle_disabled(self, mock_core_dependencies, disabled_config):
        """Skills manager is None when flag is off."""
        bot = JorgeSellerBot(config=disabled_config)
        assert bot.skills_manager is None
        assert bot.token_tracker is None

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.PROGRESSIVE_SKILLS_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.ProgressiveSkillsManager")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_token_tracker")
    @pytest.mark.asyncio
    async def test_fallback_when_skill_fails(
        self, mock_tracker, mock_skills_cls, mock_core_dependencies, sample_lead_data
    ):
        """When skills_manager is None, _execute_progressive_qualification falls back
        to traditional qualification via _execute_traditional_qualification."""
        mock_skills_cls.return_value = MagicMock()
        mock_tracker.return_value = MagicMock()

        config = JorgeFeatureConfig(
            enable_progressive_skills=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        # Force skills_manager to None to trigger fallback path
        bot.skills_manager = None

        # Mock the claude assistant for traditional fallback
        bot.claude.analyze_with_context = AsyncMock(
            return_value={"content": "Traditional qualification result"}
        )

        result = await bot._execute_progressive_qualification(sample_lead_data)

        # Fallback path produces a traditional result
        assert result is not None
        assert result["qualification_method"] == "traditional"
        assert result["tokens_used"] == 853  # Baseline (no reduction)

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.PROGRESSIVE_SKILLS_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.ProgressiveSkillsManager")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_token_tracker")
    @pytest.mark.asyncio
    async def test_token_savings_measurement(
        self, mock_tracker, mock_skills_cls, mock_core_dependencies, sample_lead_data
    ):
        """Token savings are tracked in workflow_stats after progressive qualification."""
        mock_skills_instance = MagicMock()
        mock_skills_instance.discover_skills = AsyncMock(
            return_value={
                "skills": ["jorge_stall_breaker"],
                "confidence": 0.85,
                "reasoning": "Stall pattern detected",
                "detected_pattern": "stalling",
            }
        )
        mock_skills_instance.execute_skill = AsyncMock(
            return_value={
                "skill_used": "jorge_stall_breaker",
                "response_content": "Jorge's response",
                "confidence": 0.85,
                "tokens_estimated": 169,
                "execution_successful": True,
            }
        )
        mock_skills_cls.return_value = mock_skills_instance

        mock_tracker_instance = MagicMock()
        mock_tracker_instance.record_usage = AsyncMock()
        mock_tracker.return_value = mock_tracker_instance

        config = JorgeFeatureConfig(
            enable_progressive_skills=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        initial_savings = bot.workflow_stats["token_savings"]
        initial_usage = bot.workflow_stats["progressive_skills_usage"]

        result = await bot._execute_progressive_qualification(sample_lead_data)

        # Verify token savings were recorded
        assert bot.workflow_stats["progressive_skills_usage"] == initial_usage + 1
        assert bot.workflow_stats["token_savings"] > initial_savings

        # Verify the result contains expected fields
        assert result["qualification_method"] == "progressive_skills"
        assert result["tokens_used"] < 853  # Less than baseline
        assert result["token_reduction"] > 0  # Positive reduction percentage

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.PROGRESSIVE_SKILLS_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.ProgressiveSkillsManager")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_token_tracker")
    @pytest.mark.asyncio
    async def test_token_tracker_records_usage(
        self, mock_tracker, mock_skills_cls, mock_core_dependencies, sample_lead_data
    ):
        """Token tracker receives a record_usage call after progressive execution."""
        mock_skills_instance = MagicMock()
        mock_skills_instance.discover_skills = AsyncMock(
            return_value={
                "skills": ["jorge_confrontational"],
                "confidence": 0.9,
                "reasoning": "Qualified lead",
                "detected_pattern": "confrontational",
            }
        )
        mock_skills_instance.execute_skill = AsyncMock(
            return_value={
                "skill_used": "jorge_confrontational",
                "response_content": "Are we selling or just chatting?",
                "confidence": 0.9,
                "tokens_estimated": 150,
                "execution_successful": True,
            }
        )
        mock_skills_cls.return_value = mock_skills_instance

        mock_tracker_instance = MagicMock()
        mock_tracker_instance.record_usage = AsyncMock()
        mock_tracker.return_value = mock_tracker_instance

        config = JorgeFeatureConfig(
            enable_progressive_skills=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        await bot._execute_progressive_qualification(sample_lead_data)

        mock_tracker_instance.record_usage.assert_called_once()
        call_kwargs = mock_tracker_instance.record_usage.call_args
        assert call_kwargs is not None


# ======================================================================
# 2. Agent Mesh Coordinator Integration Tests
# ======================================================================


class TestAgentMeshIntegration:
    """Agent Mesh: parallel execution, cost-aware routing, health check, fallback."""

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.AGENT_MESH_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mesh_coordinator")
    def test_toggle_enabled(self, mock_coordinator, mock_core_dependencies):
        """Mesh coordinator is instantiated when flag is on."""
        mock_coordinator.return_value = MagicMock()

        config = JorgeFeatureConfig(
            enable_agent_mesh=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert bot.mesh_coordinator is not None

    def test_toggle_disabled(self, mock_core_dependencies, disabled_config):
        """Mesh coordinator is None when flag is off."""
        bot = JorgeSellerBot(config=disabled_config)
        assert bot.mesh_coordinator is None

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.AGENT_MESH_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mesh_coordinator")
    @pytest.mark.asyncio
    async def test_mesh_task_creation(
        self, mock_coordinator_fn, mock_core_dependencies, sample_lead_data
    ):
        """Mesh coordinator creates a task and increments orchestration count."""
        mock_coordinator = MagicMock()
        mock_coordinator.submit_task = AsyncMock(return_value="task_abc_123")
        mock_coordinator_fn.return_value = mock_coordinator

        config = JorgeFeatureConfig(
            enable_agent_mesh=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        task_id = await bot._create_mesh_qualification_task(sample_lead_data)

        assert task_id == "task_abc_123"
        assert bot.workflow_stats["mesh_orchestrations"] == 1
        mock_coordinator.submit_task.assert_called_once()

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.AGENT_MESH_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mesh_coordinator")
    @pytest.mark.asyncio
    async def test_mesh_fallback_when_unavailable(
        self, mock_coordinator_fn, mock_core_dependencies, sample_lead_data
    ):
        """When mesh coordinator is None, _create_mesh_qualification_task returns None."""
        config = JorgeFeatureConfig(
            enable_agent_mesh=False,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        task_id = await bot._create_mesh_qualification_task(sample_lead_data)
        assert task_id is None
        assert bot.workflow_stats["mesh_orchestrations"] == 0

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.AGENT_MESH_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mesh_coordinator")
    @pytest.mark.asyncio
    async def test_orchestrate_supporting_tasks(
        self, mock_coordinator_fn, mock_core_dependencies, sample_lead_data
    ):
        """Orchestrate supporting tasks (property valuation) when address is provided."""
        mock_coordinator = MagicMock()
        mock_coordinator.submit_task = AsyncMock(return_value="valuation_task_456")
        mock_coordinator_fn.return_value = mock_coordinator

        config = JorgeFeatureConfig(
            enable_agent_mesh=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        orchestrated = await bot._orchestrate_supporting_tasks(
            sample_lead_data,
            {"qualification_score": 75},
            "parent_task_123",
        )

        assert len(orchestrated) > 0
        assert "valuation_task_456" in orchestrated

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.AGENT_MESH_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mesh_coordinator")
    @pytest.mark.asyncio
    async def test_orchestration_error_returns_empty(
        self, mock_coordinator_fn, mock_core_dependencies, sample_lead_data
    ):
        """If orchestration throws, empty list is returned gracefully."""
        mock_coordinator = MagicMock()
        mock_coordinator.submit_task = AsyncMock(
            side_effect=Exception("Mesh network error")
        )
        mock_coordinator_fn.return_value = mock_coordinator

        config = JorgeFeatureConfig(
            enable_agent_mesh=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        orchestrated = await bot._orchestrate_supporting_tasks(
            sample_lead_data,
            {"qualification_score": 75},
            "parent_task_123",
        )

        # Graceful fallback: returns whatever tasks were created before error
        assert isinstance(orchestrated, list)

    @pytest.mark.asyncio
    async def test_health_check_mesh_disabled(
        self, mock_core_dependencies, disabled_config
    ):
        """Health check reports mesh as disabled when flag is off."""
        bot = JorgeSellerBot(config=disabled_config)
        health = await bot.health_check()
        assert health["agent_mesh"] == "disabled"


# ======================================================================
# 3. MCP Integration Tests
# ======================================================================


class TestMCPIntegration:
    """MCP: service call, circuit breaker, fallback to direct integration."""

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.MCP_INTEGRATION_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mcp_client")
    def test_toggle_enabled(self, mock_mcp, mock_core_dependencies):
        """MCP client is instantiated when flag is on."""
        mock_mcp.return_value = MagicMock()

        config = JorgeFeatureConfig(
            enable_mcp_integration=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert bot.mcp_client is not None

    def test_toggle_disabled(self, mock_core_dependencies, disabled_config):
        """MCP client is None when flag is off."""
        bot = JorgeSellerBot(config=disabled_config)
        assert bot.mcp_client is None

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.MCP_INTEGRATION_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mcp_client")
    @pytest.mark.asyncio
    async def test_mcp_enrichment_success(
        self, mock_mcp_fn, mock_core_dependencies, sample_lead_data
    ):
        """Successful MCP enrichment returns CRM and property data."""
        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock(
            side_effect=[
                # CRM search result
                {
                    "contacts": [
                        {
                            "id": "contact_789",
                            "name": "Maria Garcia",
                            "email": "maria@example.com",
                        }
                    ]
                },
                # MLS property search result
                {
                    "properties": [
                        {"address": "1234 Victoria Ave", "price": 750000},
                        {"address": "1236 Victoria Ave", "price": 720000},
                    ]
                },
            ]
        )
        mock_mcp_fn.return_value = mock_mcp

        config = JorgeFeatureConfig(
            enable_mcp_integration=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        result = await bot._enrich_with_mcp_data(sample_lead_data, {})

        assert result["mcp_enrichment_applied"] is True
        assert result["mcp_calls"] == 2
        assert result["mcp_enrichment"]["is_return_lead"] is True
        assert len(result["mcp_enrichment"]["local_market_data"]) == 2
        assert bot.workflow_stats["mcp_calls"] == 2

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.MCP_INTEGRATION_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mcp_client")
    @pytest.mark.asyncio
    async def test_mcp_circuit_breaker_fallback(
        self, mock_mcp_fn, mock_core_dependencies, sample_lead_data
    ):
        """When MCP call fails, enrichment gracefully degrades."""
        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock(
            side_effect=Exception("MCP server connection refused")
        )
        mock_mcp_fn.return_value = mock_mcp

        config = JorgeFeatureConfig(
            enable_mcp_integration=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        result = await bot._enrich_with_mcp_data(sample_lead_data, {})

        # Enrichment still returns a result, not a crash
        assert result["mcp_enrichment_applied"] is True
        assert "enrichment_error" in result["mcp_enrichment"]

    @pytest.mark.asyncio
    async def test_mcp_enrichment_skipped_when_disabled(
        self, mock_core_dependencies, disabled_config
    ):
        """When MCP is disabled, enrichment returns False with no calls."""
        bot = JorgeSellerBot(config=disabled_config)
        result = await bot._enrich_with_mcp_data({}, {})

        assert result["mcp_enrichment_applied"] is False
        assert bot.workflow_stats["mcp_calls"] == 0

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.MCP_INTEGRATION_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mcp_client")
    @pytest.mark.asyncio
    async def test_crm_sync_via_mcp(
        self, mock_mcp_fn, mock_core_dependencies, sample_lead_data
    ):
        """CRM sync writes qualification data through MCP protocol."""
        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock(return_value={"success": True})
        mock_mcp_fn.return_value = mock_mcp

        config = JorgeFeatureConfig(
            enable_mcp_integration=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        await bot._sync_to_crm_via_mcp(
            sample_lead_data,
            {"qualification_score": 82, "temperature": "hot"},
        )

        mock_mcp.call_tool.assert_called_once()
        call_args = mock_mcp.call_tool.call_args
        assert call_args[0][0] == "ghl-crm"
        assert call_args[0][1] == "update_contact"

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.MCP_INTEGRATION_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mcp_client")
    @pytest.mark.asyncio
    async def test_crm_sync_failure_is_silent(
        self, mock_mcp_fn, mock_core_dependencies, sample_lead_data
    ):
        """CRM sync failures do not propagate up."""
        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock(
            side_effect=Exception("CRM timeout")
        )
        mock_mcp_fn.return_value = mock_mcp

        config = JorgeFeatureConfig(
            enable_mcp_integration=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        # Should not raise
        await bot._sync_to_crm_via_mcp(
            sample_lead_data,
            {"qualification_score": 82, "temperature": "hot"},
        )

    @pytest.mark.asyncio
    async def test_health_check_mcp_disabled(
        self, mock_core_dependencies, disabled_config
    ):
        """Health check reports MCP as disabled when flag is off."""
        bot = JorgeSellerBot(config=disabled_config)
        health = await bot.health_check()
        assert health["mcp_integration"] == "disabled"

    @patch(
        "ghl_real_estate_ai.agents.jorge_seller_bot.MCP_INTEGRATION_AVAILABLE",
        True,
    )
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mcp_client")
    @pytest.mark.asyncio
    async def test_shutdown_disconnects_mcp(
        self, mock_mcp_fn, mock_core_dependencies
    ):
        """Bot shutdown calls disconnect_all on MCP client."""
        mock_mcp = MagicMock()
        mock_mcp.disconnect_all = AsyncMock()
        mock_mcp_fn.return_value = mock_mcp

        config = JorgeFeatureConfig(
            enable_mcp_integration=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        await bot.shutdown()

        mock_mcp.disconnect_all.assert_called_once()


# ======================================================================
# 4. Regression & No-Break Tests
# ======================================================================


class TestNoRegression:
    """Verify all existing functionality works with features disabled."""

    def test_bot_creates_with_defaults(self, mock_core_dependencies):
        """Bot initializes with default config (all optional features off)."""
        bot = JorgeSellerBot()
        assert bot.config.enable_progressive_skills is False
        assert bot.config.enable_agent_mesh is False
        assert bot.config.enable_mcp_integration is False
        assert bot.workflow is not None

    def test_workflow_stats_initialized(self, mock_core_dependencies, disabled_config):
        """Workflow stats contain all expected counters."""
        bot = JorgeSellerBot(config=disabled_config)
        expected_keys = [
            "total_interactions",
            "progressive_skills_usage",
            "mesh_orchestrations",
            "mcp_calls",
            "adaptive_question_selections",
            "token_savings",
        ]
        for key in expected_keys:
            assert key in bot.workflow_stats
            assert bot.workflow_stats[key] == 0

    def test_factory_standard_jorge(self, mock_core_dependencies):
        """Standard factory method creates a working bot."""
        bot = JorgeSellerBot.create_standard_jorge()
        assert bot.skills_manager is None
        assert bot.mesh_coordinator is None
        assert bot.mcp_client is None

    @pytest.mark.asyncio
    async def test_health_check_all_disabled(
        self, mock_core_dependencies, disabled_config
    ):
        """Health check reports healthy when all optional features are off."""
        bot = JorgeSellerBot(config=disabled_config)
        health = await bot.health_check()
        assert health["jorge_bot"] == "healthy"
        assert health["overall_status"] == "healthy"
        assert health["progressive_skills"] == "disabled"
        assert health["agent_mesh"] == "disabled"
        assert health["mcp_integration"] == "disabled"

    @pytest.mark.asyncio
    async def test_performance_metrics_all_disabled(
        self, mock_core_dependencies, disabled_config
    ):
        """Performance metrics return base stats when no optional features are on."""
        bot = JorgeSellerBot(config=disabled_config)
        metrics = await bot.get_performance_metrics()
        assert "workflow_statistics" in metrics
        assert "features_enabled" in metrics
        assert metrics["features_enabled"]["progressive_skills"] is False
        assert metrics["features_enabled"]["agent_mesh"] is False
        assert metrics["features_enabled"]["mcp_integration"] is False

    @pytest.mark.asyncio
    async def test_traditional_qualification_fallback(
        self, mock_core_dependencies, disabled_config
    ):
        """Traditional qualification runs when progressive skills are off."""
        bot = JorgeSellerBot(config=disabled_config)
        bot.claude.analyze_with_context = AsyncMock(
            return_value={"content": "Qualification result"}
        )

        lead_data = {"lead_name": "Test", "property_address": "123 Main St"}
        result = await bot._execute_traditional_qualification(lead_data)

        assert result["qualification_method"] == "traditional"
        assert result["tokens_used"] == 853  # Baseline tokens
        bot.claude.analyze_with_context.assert_called_once()


# ======================================================================
# 5. Feature Config Module Tests
# ======================================================================


class TestFeatureConfigModule:
    """Tests for the centralized feature config module."""

    def test_default_config_all_disabled(self):
        """Default FeatureConfig has all features disabled."""
        cfg = FeatureConfig()
        assert cfg.progressive_skills.enabled is False
        assert cfg.agent_mesh.enabled is False
        assert cfg.mcp.enabled is False

    def test_progressive_skills_config_defaults(self):
        """ProgressiveSkillsConfig has expected defaults."""
        cfg = ProgressiveSkillsConfig()
        assert cfg.enabled is False
        assert cfg.model == "claude-sonnet-4"
        assert cfg.cache_ttl == 3600
        assert cfg.fallback_to_full is True
        assert cfg.enabled_skills == "all"
        assert cfg.max_discovery_tokens == 103
        assert cfg.max_execution_tokens == 169

    def test_agent_mesh_config_defaults(self):
        """AgentMeshConfig has expected defaults."""
        cfg = AgentMeshConfig()
        assert cfg.enabled is False
        assert cfg.max_agents == 10
        assert cfg.routing_strategy == "capability_based"
        assert cfg.load_balance is True
        assert cfg.health_check_interval == 30

    def test_mcp_config_defaults(self):
        """MCPConfig has expected defaults."""
        cfg = MCPConfig()
        assert cfg.enabled is False
        assert cfg.protocol_version == "2024-11-05"
        assert cfg.request_timeout == 10
        assert cfg.max_retries == 3

    def test_load_from_env_defaults(self):
        """load_feature_config_from_env returns disabled defaults with no env vars."""
        with patch.dict("os.environ", {}, clear=True):
            cfg = load_feature_config_from_env()
            assert cfg.progressive_skills.enabled is False
            assert cfg.agent_mesh.enabled is False
            assert cfg.mcp.enabled is False

    def test_load_from_env_enabled(self):
        """Environment variables correctly enable features."""
        env = {
            "ENABLE_PROGRESSIVE_SKILLS": "true",
            "ENABLE_AGENT_MESH": "1",
            "ENABLE_MCP_INTEGRATION": "yes",
            "PROGRESSIVE_SKILLS_CACHE_TTL": "7200",
            "AGENT_MESH_MAX_AGENTS": "20",
            "MCP_REQUEST_TIMEOUT": "15",
            "MCP_PROTOCOL_VERSION": "2025-01-01",
            "AGENT_MESH_HEALTH_CHECK_INTERVAL": "60",
            "PROGRESSIVE_SKILLS_FALLBACK_TO_FULL": "false",
            "PROGRESSIVE_SKILLS_ENABLED_SKILLS": "stall_breaker,confrontational",
        }
        with patch.dict("os.environ", env, clear=True):
            cfg = load_feature_config_from_env()
            assert cfg.progressive_skills.enabled is True
            assert cfg.progressive_skills.cache_ttl == 7200
            assert cfg.progressive_skills.fallback_to_full is False
            assert cfg.progressive_skills.enabled_skills == "stall_breaker,confrontational"
            assert cfg.agent_mesh.enabled is True
            assert cfg.agent_mesh.max_agents == 20
            assert cfg.agent_mesh.health_check_interval == 60
            assert cfg.mcp.enabled is True
            assert cfg.mcp.request_timeout == 15
            assert cfg.mcp.protocol_version == "2025-01-01"

    def test_feature_config_to_jorge_kwargs(self):
        """Bridge function produces correct kwargs for JorgeFeatureConfig."""
        cfg = FeatureConfig(
            progressive_skills=ProgressiveSkillsConfig(enabled=True),
            agent_mesh=AgentMeshConfig(enabled=True, max_agents=15),
            mcp=MCPConfig(enabled=True),
        )
        kwargs = feature_config_to_jorge_kwargs(cfg)
        assert kwargs["enable_progressive_skills"] is True
        assert kwargs["enable_agent_mesh"] is True
        assert kwargs["enable_mcp_integration"] is True
        assert kwargs["max_concurrent_tasks"] == 15

    def test_end_to_end_env_to_bot(self, mock_core_dependencies):
        """Full path: env vars -> FeatureConfig -> JorgeFeatureConfig -> bot."""
        with patch(
            "ghl_real_estate_ai.agents.jorge_seller_bot.PROGRESSIVE_SKILLS_AVAILABLE",
            False,
        ), patch(
            "ghl_real_estate_ai.agents.jorge_seller_bot.AGENT_MESH_AVAILABLE",
            False,
        ), patch(
            "ghl_real_estate_ai.agents.jorge_seller_bot.MCP_INTEGRATION_AVAILABLE",
            False,
        ):
            env = {
                "ENABLE_PROGRESSIVE_SKILLS": "true",
                "ENABLE_AGENT_MESH": "true",
                "ENABLE_MCP_INTEGRATION": "true",
            }
            with patch.dict("os.environ", env, clear=True):
                feature_cfg = load_feature_config_from_env()
                kwargs = feature_config_to_jorge_kwargs(feature_cfg)
                jorge_cfg = JorgeFeatureConfig(**kwargs)
                bot = JorgeSellerBot(config=jorge_cfg)

                # Config reflects requested state
                assert bot.config.enable_progressive_skills is True
                assert bot.config.enable_agent_mesh is True
                assert bot.config.enable_mcp_integration is True

                # Services are None because deps are not available
                assert bot.skills_manager is None
                assert bot.mesh_coordinator is None
                assert bot.mcp_client is None


# ======================================================================
# 6. Combined Feature Interaction Tests
# ======================================================================


class TestCombinedFeatures:
    """Test interactions between multiple features enabled simultaneously."""

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
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.ProgressiveSkillsManager")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_token_tracker")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mesh_coordinator")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mcp_client")
    @pytest.mark.asyncio
    async def test_all_features_performance_metrics(
        self,
        mock_mcp,
        mock_mesh,
        mock_tracker,
        mock_skills,
        mock_core_dependencies,
    ):
        """All enabled features appear in performance metrics."""
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

        metrics = await bot.get_performance_metrics()

        assert metrics["features_enabled"]["progressive_skills"] is True
        assert metrics["features_enabled"]["agent_mesh"] is True
        assert metrics["features_enabled"]["mcp_integration"] is True

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
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.ProgressiveSkillsManager")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_token_tracker")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mesh_coordinator")
    @patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_mcp_client")
    @pytest.mark.asyncio
    async def test_full_health_check_all_enabled(
        self,
        mock_mcp_fn,
        mock_mesh,
        mock_tracker,
        mock_skills,
        mock_core_dependencies,
    ):
        """Health check covers all enabled features."""
        mock_skills.return_value = MagicMock()
        mock_tracker.return_value = MagicMock()
        mock_mesh.return_value = MagicMock()

        mock_mcp = MagicMock()
        mock_mcp.health_check = AsyncMock(
            return_value={"status": "healthy", "ghl-crm": "healthy"}
        )
        mock_mcp_fn.return_value = mock_mcp

        config = JorgeFeatureConfig(
            enable_progressive_skills=True,
            enable_agent_mesh=True,
            enable_mcp_integration=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)

        health = await bot.health_check()
        assert health["progressive_skills"] == "healthy"
        assert health["agent_mesh"] == "healthy"
        assert health["mcp_integration"]["status"] == "healthy"
        assert health["overall_status"] == "healthy"
