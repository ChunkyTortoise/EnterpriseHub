"""Phase 4 end-to-end integration tests — Dental tenant.

Proves the config-driven concierge system adapts correctly for a real
second tenant (SmileBright Dental) loaded from concierge_configs/dental.yaml.

Covers:
  - YAML loading and parsing via ConciergeConfigLoader
  - Domain, agents, and platform features populated correctly
  - System prompt contains dental context, no Jorge bleed-through
  - Pluggable agent registry routes by invoke_pattern
  - Session key isolation between tenants
  - Config caching behaviour
  - Compliance summary includes dental-specific requirements
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.claude_concierge_agent import (
    AgentCapability,
    MultiAgentCoordinator,
    PlatformKnowledgeEngine,
)
from ghl_real_estate_ai.config.concierge_config_loader import (
    ConciergeClientConfig,
    ConciergeConfigLoader,
    get_concierge_config,
)
from ghl_real_estate_ai.services.claude_concierge_orchestrator import (
    ClaudeConciergeOrchestrator,
    ConciergeMode,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_CONFIGS_DIR = _PROJECT_ROOT / "concierge_configs"


@pytest.fixture
def loader() -> ConciergeConfigLoader:
    return ConciergeConfigLoader(configs_dir=_CONFIGS_DIR)


@pytest.fixture
def dental_config(loader) -> ConciergeClientConfig:
    return loader.load("dental")


@pytest.fixture
def jorge_config(loader) -> ConciergeClientConfig:
    return loader.load("jorge")


def _make_orchestrator(config: ConciergeClientConfig) -> ClaudeConciergeOrchestrator:
    with (
        patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.get_cache_service"),
        patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.AnalyticsService"),
        patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.get_ghl_live_data_service"),
        patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.MemoryService"),
        patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.JorgeMemorySystem"),
        patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.JorgeBusinessRules"),
    ):
        return ClaudeConciergeOrchestrator(client_config=config)


# ---------------------------------------------------------------------------
# 1. YAML loads without error
# ---------------------------------------------------------------------------


class TestDentalYamlLoading:
    def test_dental_yaml_loads_without_error(self, loader):
        config = loader.load("dental")
        assert config is not None

    def test_dental_config_domain(self, dental_config):
        assert dental_config.domain == "dental_practice"

    def test_dental_config_has_at_least_two_agents(self, dental_config):
        assert len(dental_config.available_agents) >= 2

    def test_dental_config_client_name(self, dental_config):
        assert dental_config.client_name == "SmileBright Dental"


# ---------------------------------------------------------------------------
# 2. PlatformKnowledgeEngine from dental config
# ---------------------------------------------------------------------------


class TestDentalKnowledgeEngine:
    def test_scheduling_in_platform_features(self, dental_config):
        engine = PlatformKnowledgeEngine.from_config(dental_config)
        assert "scheduling" in engine.platform_features

    def test_agent_registry_has_scheduler(self, dental_config):
        engine = PlatformKnowledgeEngine.from_config(dental_config)
        agent_names_lower = [k.lower() for k in engine.agent_registry]
        assert any("scheduler" in n or "appointment" in n for n in agent_names_lower)

    def test_agent_registry_has_intake(self, dental_config):
        engine = PlatformKnowledgeEngine.from_config(dental_config)
        agent_names_lower = [k.lower() for k in engine.agent_registry]
        assert any("intake" in n for n in agent_names_lower)


# ---------------------------------------------------------------------------
# 3. System prompt — dental content present, Jorge absent
# ---------------------------------------------------------------------------


class TestDentalSystemPrompt:
    def test_prompt_contains_smilebright(self, dental_config):
        orch = _make_orchestrator(dental_config)
        prompt = orch._get_concierge_system_prompt(ConciergeMode.PROACTIVE)
        assert "SmileBright" in prompt

    def test_prompt_does_not_contain_commission(self, dental_config):
        orch = _make_orchestrator(dental_config)
        prompt = orch._get_concierge_system_prompt(ConciergeMode.PROACTIVE)
        assert "6% commission" not in prompt

    def test_prompt_does_not_contain_jorge_salas(self, dental_config):
        orch = _make_orchestrator(dental_config)
        prompt = orch._get_concierge_system_prompt(ConciergeMode.PROACTIVE)
        assert "Jorge Salas" not in prompt

    def test_prompt_contains_dental_business_model(self, dental_config):
        orch = _make_orchestrator(dental_config)
        prompt = orch._get_concierge_system_prompt(ConciergeMode.PROACTIVE)
        assert "Fee-for-service" in prompt or "cleaning" in prompt.lower()


# ---------------------------------------------------------------------------
# 4. Pluggable agent registry — scheduler pattern routing
# ---------------------------------------------------------------------------


class TestDentalAgentRegistry:
    @pytest.mark.asyncio
    async def test_custom_scheduler_agent_invoked_by_pattern(self, dental_config):
        engine = PlatformKnowledgeEngine.from_config(dental_config)
        with patch(
            "ghl_real_estate_ai.agents.claude_concierge_agent.get_enhanced_bot_orchestrator", return_value=MagicMock()
        ):
            coordinator = MultiAgentCoordinator(knowledge_engine=engine)

        mock_fn = AsyncMock(return_value={"agent": "scheduler", "response": "Slot booked!", "confidence": 0.95})
        coordinator.register_agent("scheduler", mock_fn)

        cap = AgentCapability(
            agent_name="Appointment Scheduler Bot",
            agent_type="scheduler",
            capabilities=["slot_finding"],
            current_status="active",
        )
        result = await coordinator._invoke_agent(cap, "Book a cleaning for Tuesday", {})
        mock_fn.assert_called_once()
        assert result["response"] == "Slot booked!"


# ---------------------------------------------------------------------------
# 5. Session key isolation
# ---------------------------------------------------------------------------


class TestDentalSessionIsolation:
    def test_session_key_contains_dental(self, dental_config):
        orch = _make_orchestrator(dental_config)
        key = orch._session_key("dental", "sess-100")
        assert "dental" in key

    def test_dental_and_jorge_session_keys_differ(self, dental_config, jorge_config):
        dental_orch = _make_orchestrator(dental_config)
        jorge_orch = _make_orchestrator(jorge_config)
        dental_key = dental_orch._session_key("dental", "sess-100")
        jorge_key = jorge_orch._session_key("jorge", "sess-100")
        assert dental_key != jorge_key


# ---------------------------------------------------------------------------
# 6. Config caching
# ---------------------------------------------------------------------------


class TestDentalConfigCaching:
    def test_loader_caches_dental_config(self, loader):
        config_1 = loader.load("dental")
        config_2 = loader.load("dental")
        assert config_1 is config_2


# ---------------------------------------------------------------------------
# 7. Compliance summary
# ---------------------------------------------------------------------------


class TestDentalCompliance:
    def test_compliance_summary_contains_hipaa(self, dental_config):
        summary = dental_config.compliance_summary
        assert "HIPAA" in summary

    def test_compliance_summary_contains_dental_board(self, dental_config):
        summary = dental_config.compliance_summary
        assert "Dental Board" in summary
