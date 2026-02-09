"""SLA compliance tests for all bot operations.

Validates that the PerformanceTracker correctly detects compliance/violations
for each bot at the SLA targets defined in SLA_CONFIG.
"""

import random

import pytest

from ghl_real_estate_ai.services.jorge.performance_tracker import (

@pytest.mark.unit
    SLA_CONFIG,
    PerformanceTracker,
)


@pytest.fixture(autouse=True)
def _reset_tracker():
    PerformanceTracker.reset()
    yield
    PerformanceTracker.reset()


def _generate_compliant_latencies(mu: float, sigma: float, n: int = 200, seed: int = 42) -> list:
    """Generate latencies that are well within SLA targets."""
    rng = random.Random(seed)
    return [max(1.0, rng.lognormvariate(mu, sigma)) for _ in range(n)]


class TestSLACompliance:
    """Validate SLA compliance checking for each bot (spec: 5 tests)."""

    @pytest.mark.asyncio
    async def test_lead_bot_p95_under_2000ms(self):
        """Lead Bot P95 latency stays under the 1500ms SLA target."""
        tracker = PerformanceTracker()
        # mu=5.0, sigma=0.6 → median ~148ms, P95 ~340ms — well under 1500ms
        for lat in _generate_compliant_latencies(5.0, 0.6):
            await tracker.track_operation("lead_bot", "process", lat)

        stats = await tracker.get_bot_stats("lead_bot")
        target = SLA_CONFIG["lead_bot"]["process"]["p95_target"]
        assert stats["p95"] < target, f"Lead P95 {stats['p95']:.0f}ms >= {target}ms"

    @pytest.mark.asyncio
    async def test_buyer_bot_p95_under_2500ms(self):
        """Buyer Bot P95 latency stays under the 1800ms SLA target."""
        tracker = PerformanceTracker()
        for lat in _generate_compliant_latencies(5.3, 0.6):
            await tracker.track_operation("buyer_bot", "process", lat)

        stats = await tracker.get_bot_stats("buyer_bot")
        target = SLA_CONFIG["buyer_bot"]["process"]["p95_target"]
        assert stats["p95"] < target, f"Buyer P95 {stats['p95']:.0f}ms >= {target}ms"

    @pytest.mark.asyncio
    async def test_seller_bot_p95_under_2500ms(self):
        """Seller Bot P95 latency stays under the 1800ms SLA target."""
        tracker = PerformanceTracker()
        for lat in _generate_compliant_latencies(5.3, 0.6):
            await tracker.track_operation("seller_bot", "process", lat)

        stats = await tracker.get_bot_stats("seller_bot")
        target = SLA_CONFIG["seller_bot"]["process"]["p95_target"]
        assert stats["p95"] < target, f"Seller P95 {stats['p95']:.0f}ms >= {target}ms"

    @pytest.mark.asyncio
    async def test_handoff_p95_under_500ms(self):
        """Handoff P95 latency stays under the 500ms SLA target."""
        tracker = PerformanceTracker()
        for lat in _generate_compliant_latencies(3.7, 0.5):
            await tracker.track_operation("handoff", "execute", lat)

        stats = await tracker.get_bot_stats("handoff")
        target = SLA_CONFIG["handoff"]["execute"]["p95_target"]
        assert stats["p95"] < target, f"Handoff P95 {stats['p95']:.0f}ms >= {target}ms"

    @pytest.mark.asyncio
    async def test_cache_hit_rate_above_70_percent(self):
        """Tracker records cache hits and the rate exceeds 70%."""
        tracker = PerformanceTracker()
        rng = random.Random(42)

        # Record 200 operations: 80% cache hits
        for _ in range(200):
            cache_hit = rng.random() < 0.80
            await tracker.track_operation("lead_bot", "process", rng.uniform(5, 50), cache_hit=cache_hit)

        stats = await tracker.get_bot_stats("lead_bot")
        assert stats["cache_hit_rate"] > 0.70, f"Cache hit rate {stats['cache_hit_rate']:.2%} <= 70%"