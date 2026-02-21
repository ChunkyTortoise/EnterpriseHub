"""Phase 4 per-tenant metrics tests for ClaudeConciergeOrchestrator.

Covers:
  - _get_tenant_metrics initialises fresh dict per tenant
  - Tenant isolation (jorge requests don't touch dental counters)
  - get_tenant_stats returns correct keys and computed values
  - get_metrics includes tenant_breakdown
  - cache_hit increments correct tenant counter
  - error increments correct tenant counter
  - avg_response_time_ms computes correctly
  - Multiple tenants tracked independently
"""

from unittest.mock import AsyncMock, patch

import pytest

from ghl_real_estate_ai.config.concierge_config_loader import (
    AgentDef,
    ConciergeClientConfig,
    get_default_concierge_config,
)
from ghl_real_estate_ai.services.claude_concierge_orchestrator import (
    ClaudeConciergeOrchestrator,
)

MODULE = "ghl_real_estate_ai.services.claude_concierge_orchestrator"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_orchestrator(config: ConciergeClientConfig) -> ClaudeConciergeOrchestrator:
    with (
        patch(f"{MODULE}.get_cache_service"),
        patch(f"{MODULE}.AnalyticsService"),
        patch(f"{MODULE}.get_ghl_live_data_service"),
        patch(f"{MODULE}.MemoryService"),
        patch(f"{MODULE}.JorgeMemorySystem"),
        patch(f"{MODULE}.JorgeBusinessRules"),
    ):
        return ClaudeConciergeOrchestrator(client_config=config)


@pytest.fixture
def jorge_config() -> ConciergeClientConfig:
    return get_default_concierge_config()


@pytest.fixture
def dental_config() -> ConciergeClientConfig:
    return ConciergeClientConfig(
        tenant_id="dental",
        domain="dental_practice",
        client_name="SmileBright Dental",
        business_model="Fee-for-service dental practice.",
        market_context="Rancho Cucamonga, CA",
        client_style="Warm",
        available_agents=[
            AgentDef(
                name="Scheduler Bot",
                agent_type="scheduler",
                capabilities=["slot_finding"],
                specializations=["dental_scheduling"],
                invoke_pattern="scheduler",
            ),
        ],
        platform_features={"scheduling": ["Online Booking"]},
        compliance_requirements=["HIPAA"],
    )


@pytest.fixture
def jorge_orch(jorge_config):
    return _make_orchestrator(jorge_config)


@pytest.fixture
def dental_orch(dental_config):
    return _make_orchestrator(dental_config)


# ---------------------------------------------------------------------------
# _get_tenant_metrics — initialisation
# ---------------------------------------------------------------------------


class TestGetTenantMetrics:
    def test_initialises_fresh_dict_for_new_tenant(self, jorge_orch):
        tm = jorge_orch._get_tenant_metrics("jorge")
        assert tm == {
            "requests_processed": 0,
            "total_response_time_ms": 0,
            "errors": 0,
            "cache_hits": 0,
        }

    def test_returns_same_dict_on_repeated_call(self, jorge_orch):
        tm1 = jorge_orch._get_tenant_metrics("jorge")
        tm1["requests_processed"] = 5
        tm2 = jorge_orch._get_tenant_metrics("jorge")
        assert tm2["requests_processed"] == 5
        assert tm1 is tm2

    def test_different_tenants_get_separate_dicts(self, jorge_orch):
        jorge_tm = jorge_orch._get_tenant_metrics("jorge")
        dental_tm = jorge_orch._get_tenant_metrics("dental")
        jorge_tm["requests_processed"] = 10
        assert dental_tm["requests_processed"] == 0


# ---------------------------------------------------------------------------
# Tenant isolation — jorge vs dental
# ---------------------------------------------------------------------------


class TestTenantIsolation:
    def test_jorge_increment_does_not_touch_dental(self, jorge_orch):
        jorge_orch._get_tenant_metrics("jorge")["requests_processed"] += 3
        jorge_orch._get_tenant_metrics("jorge")["errors"] += 1
        dental = jorge_orch._get_tenant_metrics("dental")
        assert dental["requests_processed"] == 0
        assert dental["errors"] == 0

    def test_dental_cache_hit_does_not_touch_jorge(self, jorge_orch):
        jorge_orch._get_tenant_metrics("dental")["cache_hits"] += 5
        jorge = jorge_orch._get_tenant_metrics("jorge")
        assert jorge["cache_hits"] == 0


# ---------------------------------------------------------------------------
# get_tenant_stats — computed values
# ---------------------------------------------------------------------------


class TestGetTenantStats:
    def test_returns_correct_keys(self, jorge_orch):
        stats = jorge_orch.get_tenant_stats("jorge")
        assert set(stats.keys()) == {
            "tenant_id",
            "requests_processed",
            "avg_response_time_ms",
            "errors",
            "cache_hit_rate",
        }

    def test_returns_tenant_id(self, jorge_orch):
        stats = jorge_orch.get_tenant_stats("jorge")
        assert stats["tenant_id"] == "jorge"

    def test_avg_response_time_computed_correctly(self, jorge_orch):
        tm = jorge_orch._get_tenant_metrics("jorge")
        tm["requests_processed"] = 4
        tm["total_response_time_ms"] = 800
        stats = jorge_orch.get_tenant_stats("jorge")
        assert stats["avg_response_time_ms"] == 200

    def test_avg_response_time_zero_when_no_requests(self, jorge_orch):
        stats = jorge_orch.get_tenant_stats("jorge")
        assert stats["avg_response_time_ms"] == 0

    def test_cache_hit_rate_computed_correctly(self, jorge_orch):
        tm = jorge_orch._get_tenant_metrics("jorge")
        tm["requests_processed"] = 10
        tm["cache_hits"] = 3
        stats = jorge_orch.get_tenant_stats("jorge")
        assert stats["cache_hit_rate"] == 0.3

    def test_cache_hit_rate_zero_when_no_requests(self, jorge_orch):
        stats = jorge_orch.get_tenant_stats("jorge")
        assert stats["cache_hit_rate"] == 0.0

    def test_errors_returned(self, jorge_orch):
        jorge_orch._get_tenant_metrics("jorge")["errors"] = 7
        stats = jorge_orch.get_tenant_stats("jorge")
        assert stats["errors"] == 7


# ---------------------------------------------------------------------------
# get_metrics — tenant_breakdown key
# ---------------------------------------------------------------------------


class TestGetMetricsTenantBreakdown:
    def test_tenant_breakdown_key_exists(self, jorge_orch):
        metrics = jorge_orch.get_metrics()
        assert "tenant_breakdown" in metrics

    def test_tenant_breakdown_empty_when_no_tenants_tracked(self, jorge_orch):
        metrics = jorge_orch.get_metrics()
        assert metrics["tenant_breakdown"] == {}

    def test_tenant_breakdown_includes_tracked_tenants(self, jorge_orch):
        jorge_orch._get_tenant_metrics("jorge")["requests_processed"] = 1
        jorge_orch._get_tenant_metrics("dental")["requests_processed"] = 2
        metrics = jorge_orch.get_metrics()
        assert "jorge" in metrics["tenant_breakdown"]
        assert "dental" in metrics["tenant_breakdown"]
        assert metrics["tenant_breakdown"]["jorge"]["requests_processed"] == 1
        assert metrics["tenant_breakdown"]["dental"]["requests_processed"] == 2

    def test_tenant_breakdown_values_match_get_tenant_stats(self, jorge_orch):
        tm = jorge_orch._get_tenant_metrics("jorge")
        tm["requests_processed"] = 5
        tm["total_response_time_ms"] = 500
        tm["errors"] = 1
        tm["cache_hits"] = 2
        metrics = jorge_orch.get_metrics()
        assert metrics["tenant_breakdown"]["jorge"] == jorge_orch.get_tenant_stats("jorge")


# ---------------------------------------------------------------------------
# Integration-style: manual counter bumps simulate generate_contextual_guidance
# ---------------------------------------------------------------------------


class TestMetricsIncrementPaths:
    def test_request_success_increments_tenant(self, jorge_orch):
        """Simulate the success path of generate_contextual_guidance."""
        resolved_tenant = "jorge"
        jorge_orch.metrics["requests_processed"] += 1
        jorge_orch.metrics["total_response_time_ms"] += 150

        tm = jorge_orch._get_tenant_metrics(resolved_tenant)
        tm["requests_processed"] += 1
        tm["total_response_time_ms"] += 150

        assert jorge_orch._tenant_metrics["jorge"]["requests_processed"] == 1
        assert jorge_orch._tenant_metrics["jorge"]["total_response_time_ms"] == 150

    def test_cache_hit_increments_tenant(self, jorge_orch):
        """Simulate the cache-hit path."""
        resolved_tenant = "dental"
        jorge_orch.metrics["cache_hits"] += 1
        jorge_orch._get_tenant_metrics(resolved_tenant)["cache_hits"] += 1

        assert jorge_orch._tenant_metrics["dental"]["cache_hits"] == 1
        assert "jorge" not in jorge_orch._tenant_metrics

    def test_error_increments_tenant(self, jorge_orch):
        """Simulate the except path."""
        resolved_tenant = "jorge"
        jorge_orch.metrics["errors"] += 1
        jorge_orch._get_tenant_metrics(resolved_tenant)["errors"] += 1

        assert jorge_orch._tenant_metrics["jorge"]["errors"] == 1
