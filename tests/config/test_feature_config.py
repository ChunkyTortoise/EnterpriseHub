"""
Tests for Feature Configuration Module

Validates:
- Default configuration values
- Environment variable loading
- Feature flag toggling
- Config-to-JorgeFeatureConfig bridge function
- Edge cases in boolean parsing
"""

import os
from unittest.mock import patch

import pytest

from ghl_real_estate_ai.config.feature_config import (

    AgentMeshConfig,
    FeatureConfig,
    MCPConfig,
    ProgressiveSkillsConfig,
    _env_bool,
    feature_config_to_jorge_kwargs,
    load_feature_config_from_env,
)

# ─── _env_bool helper ───────────────────────────────────────────────


class TestEnvBool:
    """Tests for the _env_bool helper that parses boolean env vars."""

    def test_true_values(self):
        for val in ("true", "True", "TRUE", "1", "yes", "YES"):
            with patch.dict(os.environ, {"TEST_FLAG": val}):
                assert _env_bool("TEST_FLAG") is True

    def test_false_values(self):
        for val in ("false", "False", "FALSE", "0", "no", "NO"):
            with patch.dict(os.environ, {"TEST_FLAG": val}):
                assert _env_bool("TEST_FLAG") is False

    def test_missing_var_returns_default(self):
        env = os.environ.copy()
        env.pop("NONEXISTENT_FLAG", None)
        with patch.dict(os.environ, env, clear=True):
            assert _env_bool("NONEXISTENT_FLAG") is False
            assert _env_bool("NONEXISTENT_FLAG", default=True) is True

    def test_empty_string_returns_default(self):
        with patch.dict(os.environ, {"TEST_FLAG": ""}):
            assert _env_bool("TEST_FLAG") is False
            assert _env_bool("TEST_FLAG", default=True) is True

    def test_unrecognized_value_returns_default(self):
        with patch.dict(os.environ, {"TEST_FLAG": "maybe"}):
            assert _env_bool("TEST_FLAG") is False
            assert _env_bool("TEST_FLAG", default=True) is True


# ─── Default configurations ─────────────────────────────────────────


class TestDefaultConfigs:
    """All features should be disabled by default for backward compatibility."""

    def test_progressive_skills_defaults(self):
        config = ProgressiveSkillsConfig()
        assert config.enabled is False
        assert config.model == "claude-sonnet-4"
        assert config.skills_path == "skills/"
        assert config.cache_ttl == 3600
        assert config.max_discovery_tokens == 103
        assert config.max_execution_tokens == 169

    def test_agent_mesh_defaults(self):
        config = AgentMeshConfig()
        assert config.enabled is False
        assert config.max_agents == 10
        assert config.routing_strategy == "capability_based"
        assert config.max_cost_per_task == 5.0
        assert config.task_timeout == 30
        assert config.enable_auto_scaling is False

    def test_mcp_defaults(self):
        config = MCPConfig()
        assert config.enabled is False
        assert config.config_path == "mcp_config.json"
        assert config.request_timeout == 10
        assert config.max_retries == 3
        assert config.enable_crm_sync is True
        assert config.enable_mls_lookup is True

    def test_feature_config_defaults(self):
        config = FeatureConfig()
        assert config.progressive_skills.enabled is False
        assert config.agent_mesh.enabled is False
        assert config.mcp.enabled is False
        assert config.enable_adaptive_questioning is False
        assert config.enable_track3_intelligence is True
        assert config.enable_bot_intelligence is True


# ─── Environment variable loading ───────────────────────────────────


class TestLoadFromEnv:
    """Tests for load_feature_config_from_env()."""

    def test_all_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            config = load_feature_config_from_env()
            assert config.progressive_skills.enabled is False
            assert config.agent_mesh.enabled is False
            assert config.mcp.enabled is False

    def test_enable_progressive_skills(self):
        env = {"ENABLE_PROGRESSIVE_SKILLS": "true"}
        with patch.dict(os.environ, env, clear=True):
            config = load_feature_config_from_env()
            assert config.progressive_skills.enabled is True
            assert config.agent_mesh.enabled is False
            assert config.mcp.enabled is False

    def test_enable_agent_mesh(self):
        env = {"ENABLE_AGENT_MESH": "true"}
        with patch.dict(os.environ, env, clear=True):
            config = load_feature_config_from_env()
            assert config.agent_mesh.enabled is True

    def test_enable_mcp_integration(self):
        env = {"ENABLE_MCP_INTEGRATION": "true"}
        with patch.dict(os.environ, env, clear=True):
            config = load_feature_config_from_env()
            assert config.mcp.enabled is True

    def test_enable_all_features(self):
        env = {
            "ENABLE_PROGRESSIVE_SKILLS": "true",
            "ENABLE_AGENT_MESH": "true",
            "ENABLE_MCP_INTEGRATION": "true",
            "ENABLE_ADAPTIVE_QUESTIONING": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_feature_config_from_env()
            assert config.progressive_skills.enabled is True
            assert config.agent_mesh.enabled is True
            assert config.mcp.enabled is True
            assert config.enable_adaptive_questioning is True

    def test_custom_progressive_skills_settings(self):
        env = {
            "ENABLE_PROGRESSIVE_SKILLS": "true",
            "PROGRESSIVE_SKILLS_MODEL": "claude-opus-4",
            "PROGRESSIVE_SKILLS_PATH": "/custom/skills/",
            "PROGRESSIVE_SKILLS_CACHE_TTL": "7200",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_feature_config_from_env()
            assert config.progressive_skills.enabled is True
            assert config.progressive_skills.model == "claude-opus-4"
            assert config.progressive_skills.skills_path == "/custom/skills/"
            assert config.progressive_skills.cache_ttl == 7200

    def test_custom_agent_mesh_settings(self):
        env = {
            "ENABLE_AGENT_MESH": "true",
            "AGENT_MESH_MAX_AGENTS": "20",
            "AGENT_MESH_ROUTING_STRATEGY": "cost_aware",
            "AGENT_MESH_MAX_COST": "10.0",
            "AGENT_MESH_TASK_TIMEOUT": "60",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_feature_config_from_env()
            assert config.agent_mesh.enabled is True
            assert config.agent_mesh.max_agents == 20
            assert config.agent_mesh.routing_strategy == "cost_aware"
            assert config.agent_mesh.max_cost_per_task == 10.0
            assert config.agent_mesh.task_timeout == 60

    def test_custom_mcp_settings(self):
        env = {
            "ENABLE_MCP_INTEGRATION": "true",
            "MCP_CONFIG_PATH": "/etc/mcp/config.json",
            "MCP_REQUEST_TIMEOUT": "30",
            "MCP_MAX_RETRIES": "5",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_feature_config_from_env()
            assert config.mcp.enabled is True
            assert config.mcp.config_path == "/etc/mcp/config.json"
            assert config.mcp.request_timeout == 30
            assert config.mcp.max_retries == 5

    def test_track3_intelligence_defaults_true(self):
        with patch.dict(os.environ, {}, clear=True):
            config = load_feature_config_from_env()
            assert config.enable_track3_intelligence is True

    def test_track3_intelligence_can_be_disabled(self):
        env = {"ENABLE_TRACK3_INTELLIGENCE": "false"}
        with patch.dict(os.environ, env, clear=True):
            config = load_feature_config_from_env()
            assert config.enable_track3_intelligence is False


# ─── Bridge function ────────────────────────────────────────────────


class TestFeatureConfigBridge:
    """Tests for feature_config_to_jorge_kwargs() bridge."""

    def test_all_disabled(self):
        config = FeatureConfig()
        kwargs = feature_config_to_jorge_kwargs(config)

        assert kwargs["enable_progressive_skills"] is False
        assert kwargs["enable_agent_mesh"] is False
        assert kwargs["enable_mcp_integration"] is False
        assert kwargs["enable_adaptive_questioning"] is False
        assert kwargs["enable_track3_intelligence"] is True
        assert kwargs["enable_bot_intelligence"] is True

    def test_all_enabled(self):
        config = FeatureConfig(
            progressive_skills=ProgressiveSkillsConfig(enabled=True),
            agent_mesh=AgentMeshConfig(enabled=True),
            mcp=MCPConfig(enabled=True),
            enable_adaptive_questioning=True,
        )
        kwargs = feature_config_to_jorge_kwargs(config)

        assert kwargs["enable_progressive_skills"] is True
        assert kwargs["enable_agent_mesh"] is True
        assert kwargs["enable_mcp_integration"] is True
        assert kwargs["enable_adaptive_questioning"] is True

    def test_max_concurrent_tasks_maps_from_mesh_max_agents(self):
        config = FeatureConfig(
            agent_mesh=AgentMeshConfig(max_agents=25),
        )
        kwargs = feature_config_to_jorge_kwargs(config)
        assert kwargs["max_concurrent_tasks"] == 25

    def test_kwargs_compatible_with_jorge_feature_config(self):
        """Verify bridge output can construct a JorgeFeatureConfig."""
        from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeFeatureConfig

        config = FeatureConfig(
            progressive_skills=ProgressiveSkillsConfig(enabled=True),
            agent_mesh=AgentMeshConfig(enabled=True, max_agents=8),
        )
        kwargs = feature_config_to_jorge_kwargs(config)

        jorge_config = JorgeFeatureConfig(**kwargs)
        assert jorge_config.enable_progressive_skills is True
        assert jorge_config.enable_agent_mesh is True
        assert jorge_config.max_concurrent_tasks == 8
        assert jorge_config.enable_mcp_integration is False


# ─── Round-trip test ────────────────────────────────────────────────


class TestRoundTrip:
    """End-to-end: env vars -> FeatureConfig -> JorgeFeatureConfig kwargs."""

    def test_env_to_jorge_config_round_trip(self):
        env = {
            "ENABLE_PROGRESSIVE_SKILLS": "true",
            "ENABLE_AGENT_MESH": "true",
            "ENABLE_MCP_INTEGRATION": "false",
            "AGENT_MESH_MAX_AGENTS": "15",
            "PROGRESSIVE_SKILLS_MODEL": "claude-opus-4",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_feature_config_from_env()
            kwargs = feature_config_to_jorge_kwargs(config)

            assert kwargs["enable_progressive_skills"] is True
            assert kwargs["enable_agent_mesh"] is True
            assert kwargs["enable_mcp_integration"] is False
            assert kwargs["max_concurrent_tasks"] == 15