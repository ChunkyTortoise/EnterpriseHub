"""Phase 3 multi-tenant tests for the Claude Concierge system.

Covers:
  3.1 Config-driven knowledge engine (YAML → PlatformKnowledgeEngine)
  3.2 Domain-agnostic system prompt (no hardcoded "Rancho Cucamonga" etc.)
  3.3 Multi-tenant Redis session isolation (different key prefixes, no bleed)
  3.4 Pluggable agent registry (register_agent + capability routing)
  3.5 Client config package (jorge.yaml + _template.yaml exist and parse)
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from ghl_real_estate_ai.agents.claude_concierge_agent import (
    AgentCapability,
    MultiAgentCoordinator,
    PlatformKnowledgeEngine,
)
from ghl_real_estate_ai.config.concierge_config_loader import (
    AgentDef,
    ConciergeClientConfig,
    ConciergeConfigLoader,
    get_default_concierge_config,
)
from ghl_real_estate_ai.services.claude_concierge_orchestrator import (
    ConciergeMode,
    ClaudeConciergeOrchestrator,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dental_config() -> ConciergeClientConfig:
    return ConciergeClientConfig(
        tenant_id="dental",
        domain="dental_practice",
        client_name="SmileBright Dental",
        business_model="Fee-for-service dental practice. Revenue from cleanings ($150), fillings ($300), and crowns ($1,200).",
        market_context="Rancho Cucamonga, CA — suburban dental market. 3 competitors within 2 miles.",
        client_style="Warm, reassuring, and patient-focused. Avoid jargon.",
        available_agents=[
            AgentDef(
                name="Appointment Scheduler Bot",
                agent_type="scheduler",
                capabilities=["slot_finding", "sms_reminder"],
                specializations=["dental_scheduling"],
                invoke_pattern="scheduler",
            ),
            AgentDef(
                name="Patient Intake Bot",
                agent_type="intake",
                capabilities=["form_collection", "insurance_verify"],
                specializations=["new_patient_onboarding"],
                invoke_pattern="intake",
            ),
        ],
        platform_features={
            "scheduling": ["Online Booking", "SMS Reminders", "Cancellation Management"],
            "intake": ["Digital Forms", "Insurance Verification"],
        },
        compliance_requirements=["HIPAA patient privacy", "California Dental Board licensing"],
    )


@pytest.fixture
def jorge_config() -> ConciergeClientConfig:
    return get_default_concierge_config()


# ---------------------------------------------------------------------------
# 3.1 Config-Driven Knowledge Engine
# ---------------------------------------------------------------------------

class TestConfigDrivenKnowledgeEngine:
    def test_from_config_populates_features(self, dental_config):
        engine = PlatformKnowledgeEngine(client_config=dental_config)
        assert "scheduling" in engine.platform_features
        assert "Online Booking" in engine.platform_features["scheduling"]["features"]

    def test_from_config_populates_agent_registry(self, dental_config):
        engine = PlatformKnowledgeEngine(client_config=dental_config)
        assert len(engine.agent_registry) == 2
        # Keys are slugified agent names
        assert any("scheduler" in k or "appointment" in k for k in engine.agent_registry)

    def test_agent_registry_capabilities_preserved(self, dental_config):
        engine = PlatformKnowledgeEngine(client_config=dental_config)
        agents = list(engine.agent_registry.values())
        capability_sets = [set(a.capabilities) for a in agents]
        assert {"slot_finding", "sms_reminder"} in capability_sets

    def test_no_config_falls_back_to_jorge_hardcoded(self):
        engine = PlatformKnowledgeEngine()
        # Jorge's hardcoded features include lead_management
        assert "lead_management" in engine.platform_features

    def test_from_config_classmethod(self, dental_config):
        engine = PlatformKnowledgeEngine.from_config(dental_config)
        assert engine.platform_features is not None
        assert len(engine.agent_registry) > 0

    def test_jorge_and_dental_engines_are_independent(self, dental_config, jorge_config):
        dental_engine = PlatformKnowledgeEngine(client_config=dental_config)
        jorge_engine = PlatformKnowledgeEngine(client_config=jorge_config)
        assert set(dental_engine.platform_features.keys()) != set(jorge_engine.platform_features.keys())


# ---------------------------------------------------------------------------
# 3.2 Domain-Agnostic System Prompt
# ---------------------------------------------------------------------------

class TestDomainAgnosticSystemPrompt:
    def _make_orchestrator(self, config: ConciergeClientConfig) -> ClaudeConciergeOrchestrator:
        with patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.get_cache_service"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.AnalyticsService"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.get_ghl_live_data_service"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.MemoryService"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.JorgeMemorySystem"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.JorgeBusinessRules"):
            orch = ClaudeConciergeOrchestrator(client_config=config)
        return orch

    def test_dental_prompt_contains_client_name(self, dental_config):
        orch = self._make_orchestrator(dental_config)
        prompt = orch._get_concierge_system_prompt(ConciergeMode.PROACTIVE)
        assert "SmileBright Dental" in prompt

    def test_dental_prompt_contains_business_model(self, dental_config):
        orch = self._make_orchestrator(dental_config)
        prompt = orch._get_concierge_system_prompt(ConciergeMode.PROACTIVE)
        assert "cleanings" in prompt or "Fee-for-service" in prompt

    def test_dental_prompt_no_jorge_hardcoded_strings(self, dental_config):
        orch = self._make_orchestrator(dental_config)
        prompt = orch._get_concierge_system_prompt(ConciergeMode.REACTIVE)
        assert "6% commission" not in prompt
        assert "Rancho Cucamonga" not in prompt or "dental" in prompt.lower()

    def test_jorge_prompt_contains_business_model(self, jorge_config):
        orch = self._make_orchestrator(jorge_config)
        prompt = orch._get_concierge_system_prompt(ConciergeMode.PROACTIVE)
        assert "6% commission" in prompt or "residential" in prompt.lower()

    def test_jorge_prompt_contains_agents(self, jorge_config):
        orch = self._make_orchestrator(jorge_config)
        prompt = orch._get_concierge_system_prompt(ConciergeMode.PROACTIVE)
        assert "Bot" in prompt or "Agent" in prompt

    def test_mode_specific_section_appended(self, dental_config):
        orch = self._make_orchestrator(dental_config)
        proactive_prompt = orch._get_concierge_system_prompt(ConciergeMode.PROACTIVE)
        executive_prompt = orch._get_concierge_system_prompt(ConciergeMode.EXECUTIVE)
        assert proactive_prompt != executive_prompt


# ---------------------------------------------------------------------------
# 3.3 Multi-Tenant Session Management — Redis Key Isolation
# ---------------------------------------------------------------------------

class TestMultiTenantSessionIsolation:
    def _make_orchestrator_with_mock_cache(self, config: ConciergeClientConfig):
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        with patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.get_cache_service", return_value=mock_cache), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.AnalyticsService"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.get_ghl_live_data_service"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.MemoryService"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.JorgeMemorySystem"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.JorgeBusinessRules"):
            orch = ClaudeConciergeOrchestrator(client_config=config)
            orch.cache = mock_cache
        return orch, mock_cache

    def test_session_key_includes_tenant_id(self, jorge_config):
        orch, _ = self._make_orchestrator_with_mock_cache(jorge_config)
        key = orch._session_key("jorge", "sess-123")
        assert "jorge" in key
        assert "sess-123" in key

    def test_suggestion_key_includes_tenant_id(self, jorge_config):
        orch, _ = self._make_orchestrator_with_mock_cache(jorge_config)
        key = orch._suggestion_key("dental", "sugg-abc")
        assert "dental" in key
        assert "sugg-abc" in key

    def test_jorge_and_dental_session_keys_differ(self, jorge_config):
        orch, _ = self._make_orchestrator_with_mock_cache(jorge_config)
        jorge_key = orch._session_key("jorge", "sess-1")
        dental_key = orch._session_key("dental", "sess-1")
        assert jorge_key != dental_key

    @pytest.mark.asyncio
    async def test_store_suggestion_writes_to_redis(self, jorge_config):
        orch, mock_cache = self._make_orchestrator_with_mock_cache(jorge_config)
        await orch.store_suggestion("sugg-1", {"type": "optimization", "title": "Test"}, tenant_id="jorge")
        mock_cache.set.assert_called_once()
        call_key = mock_cache.set.call_args[0][0]
        assert "jorge" in call_key
        assert "sugg-1" in call_key

    @pytest.mark.asyncio
    async def test_get_suggestion_reads_from_redis(self, jorge_config):
        orch, mock_cache = self._make_orchestrator_with_mock_cache(jorge_config)
        mock_cache.get = AsyncMock(return_value=json.dumps({"type": "optimization", "title": "Test"}))
        result = await orch.get_suggestion("sugg-1", tenant_id="jorge")
        assert result is not None
        assert result["type"] == "optimization"

    @pytest.mark.asyncio
    async def test_tenant_isolation_no_bleed(self, jorge_config):
        """Suggestion stored for jorge tenant must not appear under dental tenant."""
        orch, mock_cache = self._make_orchestrator_with_mock_cache(jorge_config)

        jorge_data = json.dumps({"type": "jorge_specific", "title": "Seller Lead"})
        dental_data = None  # dental tenant has no such suggestion

        async def side_effect(key):
            if "jorge" in key:
                return jorge_data
            return dental_data

        mock_cache.get = AsyncMock(side_effect=side_effect)

        jorge_result = await orch.get_suggestion("sugg-1", tenant_id="jorge")
        dental_result = await orch.get_suggestion("sugg-1", tenant_id="dental")

        assert jorge_result is not None
        assert dental_result is None

    @pytest.mark.asyncio
    async def test_get_session_history_falls_back_to_dict_on_miss(self, jorge_config):
        orch, mock_cache = self._make_orchestrator_with_mock_cache(jorge_config)
        mock_cache.get = AsyncMock(return_value=None)
        orch.session_contexts["sess-99"] = [{"page": "dashboard"}]
        history = await orch._get_session_history("jorge", "sess-99")
        assert history == [{"page": "dashboard"}]

    @pytest.mark.asyncio
    async def test_update_session_context_writes_to_redis(self, jorge_config):
        orch, mock_cache = self._make_orchestrator_with_mock_cache(jorge_config)
        mock_cache.get = AsyncMock(return_value=None)

        mock_ctx = MagicMock()
        mock_ctx.current_page = "leads"

        mock_resp = MagicMock()
        mock_resp.primary_guidance = "Focus on hot leads"
        mock_resp.urgency_level = "high"
        mock_resp.immediate_actions = []

        await orch._update_session_context("jorge", "sess-1", mock_ctx, mock_resp)
        mock_cache.set.assert_called_once()
        call_key = mock_cache.set.call_args[0][0]
        assert "jorge" in call_key


# ---------------------------------------------------------------------------
# 3.4 Pluggable Agent Registry
# ---------------------------------------------------------------------------

class TestPluggableAgentRegistry:
    def _make_coordinator(self) -> MultiAgentCoordinator:
        engine = PlatformKnowledgeEngine()
        with patch("ghl_real_estate_ai.agents.claude_concierge_agent.get_enhanced_bot_orchestrator", return_value=MagicMock()):
            return MultiAgentCoordinator(knowledge_engine=engine)

    def test_coordinator_has_built_in_registry(self):
        coordinator = self._make_coordinator()
        assert len(coordinator._agent_registry) > 0

    def test_built_in_seller_pattern_exists(self):
        coordinator = self._make_coordinator()
        patterns = [p for p, _ in coordinator._agent_registry]
        assert "seller" in patterns

    def test_built_in_buyer_pattern_exists(self):
        coordinator = self._make_coordinator()
        patterns = [p for p, _ in coordinator._agent_registry]
        assert "buyer" in patterns

    def test_register_agent_prepends_to_custom_registry(self):
        coordinator = self._make_coordinator()
        dummy_fn = AsyncMock()
        coordinator.register_agent("scheduler", dummy_fn)
        assert coordinator._custom_registry[0] == ("scheduler", dummy_fn)

    @pytest.mark.asyncio
    async def test_custom_agent_invoked_by_pattern(self):
        coordinator = self._make_coordinator()
        custom_fn = AsyncMock(return_value={"agent": "scheduler", "response": "Booked!", "confidence": 0.9})
        coordinator.register_agent("scheduler", custom_fn)

        cap = AgentCapability(
            agent_name="Appointment Scheduler Bot",
            agent_type="scheduler",
            capabilities=["slot_finding"],
            current_status="active",
        )
        result = await coordinator._invoke_agent(cap, "Book an appointment", {})
        custom_fn.assert_called_once()
        assert result["response"] == "Booked!"

    @pytest.mark.asyncio
    async def test_custom_agent_takes_priority_over_built_in(self):
        """Custom 'seller' pattern should override built-in seller routing."""
        coordinator = self._make_coordinator()
        custom_seller_fn = AsyncMock(return_value={"agent": "custom_seller", "response": "Custom!", "confidence": 1.0})
        coordinator.register_agent("seller", custom_seller_fn)

        cap = AgentCapability(
            agent_name="Custom Seller Bot",
            agent_type="seller_qualification",
            capabilities=["custom_cap"],
            current_status="active",
        )
        result = await coordinator._invoke_agent(cap, "Qualify this seller", {})
        custom_seller_fn.assert_called_once()
        assert result["agent"] == "custom_seller"

    @pytest.mark.asyncio
    async def test_unknown_agent_falls_through_to_generic(self):
        coordinator = self._make_coordinator()
        cap = AgentCapability(
            agent_name="Unknown Exotic Bot XYZ",
            agent_type="exotic",
            capabilities=["unknown"],
            current_status="active",
        )
        with patch.object(coordinator, "_invoke_claude_generic_agent", new_callable=AsyncMock) as mock_generic:
            mock_generic.return_value = {"agent": "claude_generic", "response": "fallback", "confidence": 0.7}
            result = await coordinator._invoke_agent(cap, "Do something exotic", {})
        mock_generic.assert_called_once()


# ---------------------------------------------------------------------------
# 3.5 Config Package — YAML Files Present and Parseable
# ---------------------------------------------------------------------------

class TestClientConfigPackage:
    _project_root = Path(__file__).parent.parent.parent
    _configs_dir = _project_root / "concierge_configs"

    def test_jorge_yaml_exists(self):
        assert (self._configs_dir / "jorge.yaml").exists()

    def test_template_yaml_exists(self):
        assert (self._configs_dir / "_template.yaml").exists()

    def test_jorge_yaml_valid(self):
        with open(self._configs_dir / "jorge.yaml") as f:
            raw = yaml.safe_load(f)
        assert raw["domain"] == "real_estate"
        assert "business_model" in raw
        assert "agents" in raw
        assert len(raw["agents"]) > 0

    def test_jorge_yaml_agents_have_required_fields(self):
        with open(self._configs_dir / "jorge.yaml") as f:
            raw = yaml.safe_load(f)
        for agent in raw["agents"]:
            assert "name" in agent
            assert "agent_type" in agent
            assert "invoke_pattern" in agent

    def test_loader_loads_jorge_yaml(self):
        loader = ConciergeConfigLoader(configs_dir=self._configs_dir)
        config = loader.load("jorge")
        assert config.tenant_id == "jorge"
        assert config.domain == "real_estate"
        assert len(config.available_agents) > 0

    def test_loader_raises_for_unknown_tenant(self):
        loader = ConciergeConfigLoader(configs_dir=self._configs_dir)
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent_tenant_xyz")

    def test_loader_caches_config(self):
        loader = ConciergeConfigLoader(configs_dir=self._configs_dir)
        config_1 = loader.load("jorge")
        config_2 = loader.load("jorge")
        assert config_1 is config_2

    def test_reload_clears_cache(self):
        loader = ConciergeConfigLoader(configs_dir=self._configs_dir)
        config_1 = loader.load("jorge")
        loader.reload("jorge")
        config_2 = loader.load("jorge")
        # Different object after reload
        assert config_1 is not config_2

    def test_hardcoded_fallback_when_yaml_missing(self):
        loader = ConciergeConfigLoader(configs_dir=Path("/tmp/nonexistent_dir_xyz"))
        config = loader.get_default()
        assert config.tenant_id == "jorge"
        assert "commission" in config.business_model.lower()

    def test_dental_config_fixture_parses_correctly(self, dental_config):
        assert dental_config.domain == "dental_practice"
        assert len(dental_config.available_agents) == 2
        assert dental_config.available_agents[0].invoke_pattern == "scheduler"

    def test_config_agent_summary_property(self, dental_config):
        summary = dental_config.agent_summary
        assert "Scheduler" in summary or "scheduler" in summary.lower()

    def test_config_compliance_summary_property(self, dental_config):
        summary = dental_config.compliance_summary
        assert "HIPAA" in summary


# ---------------------------------------------------------------------------
# Loose-end fixes: tenant-scoped cache key, tenant_id threading
# ---------------------------------------------------------------------------

class TestTenantScopedCacheKey:
    def _make_orchestrator(self, config: ConciergeClientConfig) -> ClaudeConciergeOrchestrator:
        with patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.get_cache_service"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.AnalyticsService"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.get_ghl_live_data_service"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.MemoryService"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.JorgeMemorySystem"), \
             patch("ghl_real_estate_ai.services.claude_concierge_orchestrator.JorgeBusinessRules"):
            orch = ClaudeConciergeOrchestrator(client_config=config)
        return orch

    def test_cache_key_includes_tenant_id(self, jorge_config):
        from ghl_real_estate_ai.services.claude_concierge_orchestrator import IntelligenceScope, PlatformContext
        orch = self._make_orchestrator(jorge_config)
        ctx = PlatformContext(current_page="leads", user_role="agent", bot_statuses={})
        key = orch._generate_context_cache_key(ctx, ConciergeMode.PROACTIVE, IntelligenceScope.WORKFLOW, "jorge")
        assert "jorge" in key
        assert "concierge:" in key

    def test_cache_keys_differ_by_tenant(self, jorge_config):
        from ghl_real_estate_ai.services.claude_concierge_orchestrator import IntelligenceScope, PlatformContext
        orch = self._make_orchestrator(jorge_config)
        ctx = PlatformContext(current_page="leads", user_role="agent", bot_statuses={})
        jorge_key = orch._generate_context_cache_key(ctx, ConciergeMode.PROACTIVE, IntelligenceScope.WORKFLOW, "jorge")
        dental_key = orch._generate_context_cache_key(ctx, ConciergeMode.PROACTIVE, IntelligenceScope.WORKFLOW, "dental")
        assert jorge_key != dental_key

    def test_cache_key_defaults_to_config_tenant(self, dental_config):
        from ghl_real_estate_ai.services.claude_concierge_orchestrator import IntelligenceScope, PlatformContext
        orch = self._make_orchestrator(dental_config)
        ctx = PlatformContext(current_page="leads", user_role="agent", bot_statuses={})
        key = orch._generate_context_cache_key(ctx, ConciergeMode.PROACTIVE, IntelligenceScope.WORKFLOW)
        assert "dental" in key  # uses default_config.tenant_id

    @pytest.mark.asyncio
    async def test_apply_suggestion_uses_tenant_id(self, jorge_config):
        orch = self._make_orchestrator(jorge_config)
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        orch.cache = mock_cache

        result = await orch.apply_suggestion("nonexistent-123", tenant_id="dental")
        # Should attempt Redis lookup with dental tenant key
        mock_cache.get.assert_called_once()
        call_key = mock_cache.get.call_args[0][0]
        assert "dental" in call_key
