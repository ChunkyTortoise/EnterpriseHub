from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

"""Unit tests for the HealthDashboard component.

Tests health status calculation, demo mode data generation, summary
generation, and edge cases.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.streamlit_demo.components.health_dashboard import (
    EndpointHealth,
    HealthDashboard,
    _generate_demo_endpoints,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def dashboard() -> HealthDashboard:
    """Create a HealthDashboard with no trackers (demo mode)."""
    return HealthDashboard()


@pytest.fixture
def mock_tracker() -> MagicMock:
    """Create a mock PerformanceTracker that returns realistic stats."""
    tracker = MagicMock()

    async def _get_bot_stats(bot_name: str, window: str = "1h") -> dict:
        base = {
            "p50": 150.0,
            "p95": 400.0,
            "p99": 700.0,
            "mean": 180.0,
            "min": 50.0,
            "max": 900.0,
            "count": 100,
            "success_count": 98,
            "error_count": 2,
            "cache_hit_count": 40,
            "cache_hit_rate": 0.4,
            "success_rate": 0.98,
        }
        return base

    tracker.get_bot_stats = AsyncMock(side_effect=_get_bot_stats)
    return tracker


# ============================================================================
# Test: Health Status Calculation
# ============================================================================


class TestHealthStatusCalculation:
    """Tests for _calculate_health_status static method."""

    def test_healthy_status(self, dashboard: HealthDashboard):
        """Low error rate and low P95 should return 'healthy'."""
        assert dashboard._calculate_health_status(0.005, 500.0) == "healthy"

    def test_degraded_from_error_rate(self, dashboard: HealthDashboard):
        """Error rate at 1% boundary should return 'degraded'."""
        assert dashboard._calculate_health_status(0.01, 500.0) == "degraded"

    def test_degraded_from_p95(self, dashboard: HealthDashboard):
        """P95 at 1000ms boundary should return 'degraded'."""
        assert dashboard._calculate_health_status(0.005, 1000.0) == "degraded"

    def test_critical_from_error_rate(self, dashboard: HealthDashboard):
        """Error rate >= 5% should return 'critical'."""
        assert dashboard._calculate_health_status(0.05, 500.0) == "critical"

    def test_critical_from_p95(self, dashboard: HealthDashboard):
        """P95 >= 2500ms should return 'critical'."""
        assert dashboard._calculate_health_status(0.001, 2500.0) == "critical"

    def test_both_critical(self, dashboard: HealthDashboard):
        """Both metrics in critical range should return 'critical'."""
        assert dashboard._calculate_health_status(0.10, 5000.0) == "critical"

    def test_zero_values(self, dashboard: HealthDashboard):
        """Zero error rate and zero P95 should return 'healthy'."""
        assert dashboard._calculate_health_status(0.0, 0.0) == "healthy"


# ============================================================================
# Test: Demo Mode Data
# ============================================================================


class TestDemoModeData:
    """Tests for demo data generation."""

    def test_demo_endpoints_count(self):
        """Demo mode should generate exactly 4 endpoints."""
        endpoints = _generate_demo_endpoints()
        assert len(endpoints) == 4

    def test_demo_endpoints_have_names(self):
        """Each demo endpoint should have a non-empty name."""
        endpoints = _generate_demo_endpoints()
        for ep in endpoints:
            assert ep.name, f"Endpoint has empty name: {ep}"

    def test_demo_endpoints_all_healthy(self):
        """Demo endpoints should all be healthy."""
        endpoints = _generate_demo_endpoints()
        for ep in endpoints:
            assert ep.status == "healthy", f"{ep.name} is {ep.status}, expected healthy"

    def test_demo_endpoints_have_request_counts(self):
        """Demo endpoints should have positive request counts."""
        endpoints = _generate_demo_endpoints()
        for ep in endpoints:
            assert ep.request_count > 0, f"{ep.name} has zero requests"


# ============================================================================
# Test: Summary Generation
# ============================================================================


class TestSummaryGeneration:
    """Tests for get_health_summary method."""

    def test_summary_keys(self, dashboard: HealthDashboard):
        """Summary should contain all required keys."""
        summary = dashboard.get_health_summary()
        required_keys = {
            "overall_status",
            "active_bots",
            "uptime_pct",
            "total_requests_1h",
            "avg_error_rate_1h",
            "endpoints",
        }
        assert required_keys.issubset(summary.keys())

    def test_summary_overall_status_is_valid(self, dashboard: HealthDashboard):
        """Overall status should be one of the three valid statuses."""
        summary = dashboard.get_health_summary()
        assert summary["overall_status"] in ("healthy", "degraded", "critical")

    def test_summary_active_bots_positive(self, dashboard: HealthDashboard):
        """Demo mode should report active bots."""
        summary = dashboard.get_health_summary()
        assert summary["active_bots"] > 0

    def test_summary_uptime_in_range(self, dashboard: HealthDashboard):
        """Uptime percentage should be between 0 and 100."""
        summary = dashboard.get_health_summary()
        assert 0.0 <= summary["uptime_pct"] <= 100.0

    def test_summary_endpoints_match_demo_count(self, dashboard: HealthDashboard):
        """Demo summary should have the same number of endpoints as demo data."""
        summary = dashboard.get_health_summary()
        assert len(summary["endpoints"]) == 4

    def test_endpoint_dict_keys(self, dashboard: HealthDashboard):
        """Each endpoint dict in summary should have the expected keys."""
        summary = dashboard.get_health_summary()
        expected_keys = {
            "name",
            "p50_ms",
            "p95_ms",
            "p99_ms",
            "error_rate_1h",
            "error_rate_24h",
            "request_count",
            "status",
        }
        for ep in summary["endpoints"]:
            assert expected_keys.issubset(ep.keys()), f"Missing keys in endpoint: {ep['name']}"


# ============================================================================
# Test: Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge case handling."""

    def test_no_trackers_uses_demo(self):
        """Dashboard with no trackers should use demo data."""
        dash = HealthDashboard(performance_tracker=None, metrics_collector=None)
        summary = dash.get_health_summary()
        assert summary["overall_status"] in ("healthy", "degraded")
        assert len(summary["endpoints"]) >= 1

    def test_endpoint_health_defaults(self):
        """EndpointHealth dataclass defaults should be safe."""
        ep = EndpointHealth(name="test")
        assert ep.p50_ms == 0.0
        assert ep.p95_ms == 0.0
        assert ep.p99_ms == 0.0
        assert ep.error_rate_1h == 0.0
        assert ep.request_count == 0
        assert ep.status == "healthy"

    def test_total_requests_sum(self, dashboard: HealthDashboard):
        """Total requests should equal sum of endpoint requests."""
        summary = dashboard.get_health_summary()
        expected_total = sum(ep["request_count"] for ep in summary["endpoints"])
        assert summary["total_requests_1h"] == expected_total
