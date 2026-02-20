"""
Feature Integration Tests - Progressive Skills, Agent Mesh, MCP Integration

Tests centralized feature configuration and optional feature enablement
for the Jorge Seller Bot. All features are disabled by default;
these tests verify correct behavior when selectively enabled.

Mocking strategy: Patch at module-level import sites within jorge_seller_bot
to avoid requiring actual service dependencies.
"""

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest

from ghl_real_estate_ai.config.feature_config import (
    AgentMeshConfig,
    FeatureConfig,
    MCPConfig,
    ProgressiveSkillsConfig,
    feature_config_to_jorge_kwargs,
    load_feature_config_from_env,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_jorge_deps():
    """Mock all external dependencies required by JorgeSellerBot.__init__."""
    with patch.multiple(
        "ghl_real_estate_ai.agents.jorge_seller_bot",
        LeadIntentDecoder=MagicMock,
        ClaudeAssistant=MagicMock,
        get_event_publisher=MagicMock,
        get_ml_analytics_engine=MagicMock,
    ):
        yield


@pytest.fixture
def sample_lead_data():
    """Standard lead data dict used across feature tests."""
    return {
        "lead_id": "test_lead_001",
        "lead_name": "Jane Smith",
        "last_message": "I'm thinking about selling my property",
        "lead_source": "website",
        "property_address": "123 Victoria Ave, Rancho Cucamonga, CA 91730",
        "email": "jane@example.com",
        "phone": "909-555-1234",
        "interaction_count": 2,
        "seller_temperature": "warm",
        "frs_score": 60,
        "pcs_score": 55,
        "stall_count": 0,
    }


# ===========================================================================
# 1. Config loads from environment variables
# ===========================================================================


class TestFeatureConfig:
    def test_feature_config_loads_from_env(self):
        """Env vars produce a FeatureConfig with all features enabled."""
        env = {
            "ENABLE_PROGRESSIVE_SKILLS": "true",
            "PROGRESSIVE_SKILLS_MODEL": "claude-opus-4",
            "PROGRESSIVE_SKILLS_CACHE_TTL": "7200",
            "ENABLE_AGENT_MESH": "true",
            "AGENT_MESH_MAX_AGENTS": "20",
            "AGENT_MESH_ROUTING_STRATEGY": "round_robin",
            "AGENT_MESH_MAX_COST": "10.0",
            "ENABLE_MCP_INTEGRATION": "true",
            "MCP_CONFIG_PATH": "/etc/mcp/config.json",
            "MCP_REQUEST_TIMEOUT": "15",
            "ENABLE_ADAPTIVE_QUESTIONING": "true",
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = load_feature_config_from_env()

        assert cfg.progressive_skills.enabled is True
        assert cfg.progressive_skills.model == "claude-opus-4"
        assert cfg.progressive_skills.cache_ttl == 7200
        assert cfg.agent_mesh.enabled is True
        assert cfg.agent_mesh.max_agents == 20
        assert cfg.agent_mesh.routing_strategy == "round_robin"
        assert cfg.agent_mesh.max_cost_per_task == 10.0
        assert cfg.mcp.enabled is True
        assert cfg.mcp.config_path == "/etc/mcp/config.json"
        assert cfg.mcp.request_timeout == 15
        assert cfg.enable_adaptive_questioning is True

    def test_feature_config_defaults_all_disabled(self):
        """Without env vars, all optional features are disabled (backward compat)."""
        env_keys = [
            "ENABLE_PROGRESSIVE_SKILLS",
            "ENABLE_AGENT_MESH",
            "ENABLE_MCP_INTEGRATION",
            "ENABLE_ADAPTIVE_QUESTIONING",
        ]
        cleaned = {k: "" for k in env_keys}
        with patch.dict(os.environ, cleaned, clear=False):
            # Clear any existing values
            for k in env_keys:
                os.environ.pop(k, None)
            cfg = load_feature_config_from_env()

        assert cfg.progressive_skills.enabled is False
        assert cfg.agent_mesh.enabled is False
        assert cfg.mcp.enabled is False
        assert cfg.enable_adaptive_questioning is False
        # Track 3.1 and bot intelligence default to True
        assert cfg.enable_track3_intelligence is True
        assert cfg.enable_bot_intelligence is True

    def test_feature_config_to_jorge_kwargs(self):
        """Bridge function produces valid JorgeFeatureConfig kwargs."""
        cfg = FeatureConfig(
            progressive_skills=ProgressiveSkillsConfig(enabled=True),
            agent_mesh=AgentMeshConfig(enabled=True, max_agents=15),
            mcp=MCPConfig(enabled=True),
            enable_adaptive_questioning=True,
        )
        kwargs = feature_config_to_jorge_kwargs(cfg)

        assert kwargs["enable_progressive_skills"] is True
        assert kwargs["enable_agent_mesh"] is True
        assert kwargs["enable_mcp_integration"] is True
        assert kwargs["enable_adaptive_questioning"] is True
        assert kwargs["max_concurrent_tasks"] == 15


# ===========================================================================
# 2. Progressive Skills Integration
# ===========================================================================


class TestProgressiveSkills:
    @pytest.mark.asyncio
    async def test_progressive_skills_initialization(self, mock_jorge_deps):
        """Skills manager and token tracker initialize when feature enabled."""
        mock_skills_mgr = MagicMock()
        mock_token_tracker = MagicMock()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            PROGRESSIVE_SKILLS_AVAILABLE=True,
            ProgressiveSkillsManager=MagicMock(return_value=mock_skills_mgr),
            get_token_tracker=MagicMock(return_value=mock_token_tracker),
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import (
                JorgeFeatureConfig,
                JorgeSellerBot,
            )

            config = JorgeFeatureConfig(enable_progressive_skills=True)
            bot = JorgeSellerBot(config=config)

            assert bot.skills_manager is mock_skills_mgr
            assert bot.token_tracker is mock_token_tracker

    @pytest.mark.asyncio
    async def test_progressive_skills_qualification_path(self, mock_jorge_deps, sample_lead_data):
        """Discovery → execution flow works and tracks token reduction."""
        mock_skills_mgr = MagicMock()
        mock_skills_mgr.discover_skills = AsyncMock(
            return_value={
                "skills": ["seller_qualification_v2"],
                "confidence": 0.85,
            }
        )
        mock_skills_mgr.execute_skill = AsyncMock(
            return_value={
                "response_content": "Qualified warm seller",
                "tokens_estimated": 169,
            }
        )

        mock_token_tracker = MagicMock()
        mock_token_tracker.record_usage = AsyncMock()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            PROGRESSIVE_SKILLS_AVAILABLE=True,
            ProgressiveSkillsManager=MagicMock(return_value=mock_skills_mgr),
            get_token_tracker=MagicMock(return_value=mock_token_tracker),
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import (
                JorgeFeatureConfig,
                JorgeSellerBot,
            )

            config = JorgeFeatureConfig(enable_progressive_skills=True)
            bot = JorgeSellerBot(config=config)

            result = await bot._execute_progressive_qualification(sample_lead_data)

            assert result["qualification_method"] == "progressive_skills"
            assert result["skill_used"] == "seller_qualification_v2"
            assert result["confidence"] == 0.85
            assert result["tokens_used"] == 103 + 169  # discovery + execution
            assert result["token_reduction"] > 60  # >60% reduction from 853 baseline
            mock_skills_mgr.discover_skills.assert_awaited_once()
            mock_skills_mgr.execute_skill.assert_awaited_once()
            mock_token_tracker.record_usage.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_progressive_skills_fallback(self, mock_jorge_deps, sample_lead_data):
        """Falls back to traditional qualification when dependencies unavailable."""
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            PROGRESSIVE_SKILLS_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import (
                JorgeFeatureConfig,
                JorgeSellerBot,
            )

            config = JorgeFeatureConfig(enable_progressive_skills=True)
            bot = JorgeSellerBot(config=config)

            # skills_manager should be None (dependency not available)
            assert bot.skills_manager is None

            # _execute_progressive_qualification should fall back to traditional
            bot.claude.analyze_with_context = AsyncMock(return_value={"content": "Traditional qualification"})
            result = await bot._execute_progressive_qualification(sample_lead_data)

            assert result["qualification_method"] == "traditional"
            assert result["tokens_used"] == 853  # baseline


# ===========================================================================
# 3. Agent Mesh Integration
# ===========================================================================


class TestAgentMesh:
    @pytest.mark.asyncio
    async def test_agent_mesh_task_creation(self, mock_jorge_deps, sample_lead_data):
        """Mesh coordinator creates and submits qualification tasks."""
        mock_coordinator = MagicMock()
        mock_coordinator.submit_task = AsyncMock(return_value="mesh-task-001")

        mock_agent_task = MagicMock()
        mock_task_priority = MagicMock()
        mock_task_priority.HIGH = "HIGH"
        mock_task_priority.NORMAL = "NORMAL"
        mock_agent_capability = MagicMock()
        mock_agent_capability.LEAD_QUALIFICATION = "LEAD_QUALIFICATION"
        mock_agent_capability.CONVERSATION_ANALYSIS = "CONVERSATION_ANALYSIS"
        mock_agent_capability.MARKET_INTELLIGENCE = "MARKET_INTELLIGENCE"

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            AGENT_MESH_AVAILABLE=True,
            get_mesh_coordinator=MagicMock(return_value=mock_coordinator),
            AgentTask=mock_agent_task,
            TaskPriority=mock_task_priority,
            AgentCapability=mock_agent_capability,
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import (
                JorgeFeatureConfig,
                JorgeSellerBot,
            )

            config = JorgeFeatureConfig(enable_agent_mesh=True)
            bot = JorgeSellerBot(config=config)

            assert bot.mesh_coordinator is mock_coordinator

            task_id = await bot._create_mesh_qualification_task(sample_lead_data)

            assert task_id == "mesh-task-001"
            mock_coordinator.submit_task.assert_awaited_once()
            assert bot.workflow_stats["mesh_orchestrations"] == 1


# ===========================================================================
# 4. MCP Integration
# ===========================================================================


class TestMCPIntegration:
    @pytest.mark.asyncio
    async def test_mcp_enrichment_calls_tools(self, mock_jorge_deps, sample_lead_data):
        """MCP client calls CRM search and property data tools."""
        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock(
            side_effect=[
                # First call: CRM search_contacts
                {"contacts": [{"id": "crm-001", "name": "Jane Smith"}]},
                # Second call: MLS search_properties
                {"properties": [{"address": "124 Victoria Ave", "price": 750000}]},
            ]
        )

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            MCP_INTEGRATION_AVAILABLE=True,
            get_mcp_client=MagicMock(return_value=mock_mcp),
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import (
                JorgeFeatureConfig,
                JorgeSellerBot,
            )

            config = JorgeFeatureConfig(enable_mcp_integration=True)
            bot = JorgeSellerBot(config=config)

            result = await bot._enrich_with_mcp_data(sample_lead_data, {"qualification_score": 75})

            assert result["mcp_enrichment_applied"] is True
            assert result["mcp_calls"] == 2
            assert result["mcp_enrichment"]["is_return_lead"] is True
            assert len(result["mcp_enrichment"]["local_market_data"]) == 1
            assert mock_mcp.call_tool.await_count == 2


# ===========================================================================
# 5. Full Enhanced Workflow
# ===========================================================================


class TestFullEnhancedWorkflow:
    @pytest.mark.asyncio
    async def test_full_enhanced_workflow(self, mock_jorge_deps, sample_lead_data):
        """All features orchestrated in process_seller_with_enhancements."""
        # --- Progressive Skills mocks ---
        mock_skills_mgr = MagicMock()
        mock_skills_mgr.discover_skills = AsyncMock(
            return_value={
                "skills": ["seller_qualification_v2"],
                "confidence": 0.82,
            }
        )
        mock_skills_mgr.execute_skill = AsyncMock(
            return_value={
                "response_content": "Qualified warm seller via progressive",
                "tokens_estimated": 169,
            }
        )
        mock_token_tracker = MagicMock()
        mock_token_tracker.record_usage = AsyncMock()

        # --- Agent Mesh mocks ---
        mock_coordinator = MagicMock()
        mock_coordinator.submit_task = AsyncMock(return_value="mesh-full-001")

        mock_agent_task = MagicMock()
        mock_task_priority = MagicMock()
        mock_task_priority.HIGH = "HIGH"
        mock_task_priority.NORMAL = "NORMAL"
        mock_agent_capability = MagicMock()
        mock_agent_capability.LEAD_QUALIFICATION = "LEAD_QUALIFICATION"
        mock_agent_capability.CONVERSATION_ANALYSIS = "CONVERSATION_ANALYSIS"
        mock_agent_capability.MARKET_INTELLIGENCE = "MARKET_INTELLIGENCE"

        # --- MCP mocks ---
        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock(
            side_effect=[
                # CRM search
                {"contacts": [{"id": "crm-full-001", "name": "Jane Smith"}]},
                # MLS search
                {"properties": [{"address": "124 Victoria Ave", "price": 750000}]},
                # CRM update (sync_to_crm_via_mcp)
                {"success": True},
            ]
        )

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            PROGRESSIVE_SKILLS_AVAILABLE=True,
            ProgressiveSkillsManager=MagicMock(return_value=mock_skills_mgr),
            get_token_tracker=MagicMock(return_value=mock_token_tracker),
            AGENT_MESH_AVAILABLE=True,
            get_mesh_coordinator=MagicMock(return_value=mock_coordinator),
            AgentTask=mock_agent_task,
            TaskPriority=mock_task_priority,
            AgentCapability=mock_agent_capability,
            MCP_INTEGRATION_AVAILABLE=True,
            get_mcp_client=MagicMock(return_value=mock_mcp),
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import (
                JorgeFeatureConfig,
                JorgeSellerBot,
                QualificationResult,
            )

            config = JorgeFeatureConfig(
                enable_progressive_skills=True,
                enable_agent_mesh=True,
                enable_mcp_integration=True,
            )
            bot = JorgeSellerBot(config=config)

            result = await bot.process_seller_with_enhancements(sample_lead_data)

            # Verify result type and structure
            assert isinstance(result, QualificationResult)
            assert result.lead_id == "test_lead_001"

            # Progressive skills applied
            assert result.progressive_skills_applied is True
            assert result.tokens_used == 103 + 169

            # Mesh task created
            assert result.mesh_task_id == "mesh-full-001"

            # MCP enrichment applied
            assert result.mcp_enrichment_applied is True

            # Timeline captured all phases
            assert "qualification_complete" in result.timeline_ms
            assert "mesh_task_created" in result.timeline_ms
            assert "mcp_enrichment_complete" in result.timeline_ms