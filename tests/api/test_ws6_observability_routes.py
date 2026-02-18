"""Route-level tests for WS-6 observability payload exposure."""

from unittest.mock import AsyncMock, patch

import pytest

from ghl_real_estate_ai.api.routes.ai_concierge import get_concierge_performance
from ghl_real_estate_ai.api.routes.analytics import get_jorge_ws6_observability
from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def reset_singletons():
    BotMetricsCollector.reset()
    PerformanceTracker.reset()
    ABTestingService.reset()
    yield
    BotMetricsCollector.reset()
    PerformanceTracker.reset()
    ABTestingService.reset()


async def test_analytics_ws6_route_returns_observability_payload():
    payload = await get_jorge_ws6_observability(
        window="1h",
        include_recent_events=False,
        current_user={"user_id": "test_user"},
    )

    assert payload["available"] is True
    assert payload["version"] == "ws6.v1"
    assert "dashboard" in payload
    assert "event_schemas" in payload


async def test_concierge_performance_includes_ws6_payload():
    with patch(
        "ghl_real_estate_ai.api.routes.ai_concierge.proactive_intelligence.get_performance_metrics",
        new=AsyncMock(return_value={"performance_status": "good"}),
    ):
        response = await get_concierge_performance(current_user={"user_id": "test_user"})

    assert "jorge_ws6" in response
    assert response["jorge_ws6"]["version"] == "ws6.v1"
    assert "dashboard" in response["jorge_ws6"]
