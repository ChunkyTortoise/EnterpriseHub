import pytest

pytestmark = pytest.mark.integration

"""Tests for Jorge Performance Tracker Service.

Covers operation tracking, percentile calculations, bot stats retrieval,
SLA compliance checking, rolling windows, and the async context manager.
"""

import asyncio
import time

import pytest

from ghl_real_estate_ai.services.jorge.performance_tracker import (
    VALID_BOT_NAMES,
    WINDOWS,
    PerformanceTracker,
)


@pytest.fixture(autouse=True)
def reset_tracker():
    """Reset the PerformanceTracker singleton before and after each test."""
    PerformanceTracker.reset()
    yield
    PerformanceTracker.reset()


class TestPerformanceTracker:
    """Tests for PerformanceTracker."""

    # ── 1. Basic tracking ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_track_operation_valid(self):
        """Tracking a valid operation stores the entry successfully."""
        tracker = PerformanceTracker()

        await tracker.track_operation("lead_bot", "qualify", 150.0, success=True)

        stats = await tracker.get_bot_stats("lead_bot")
        assert stats["count"] == 1
        assert stats["success_count"] == 1
        assert stats["p50"] == 150.0

    # ── 2. Invalid bot name ───────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_track_operation_invalid_bot_raises(self):
        """Tracking with an invalid bot_name raises ValueError."""
        tracker = PerformanceTracker()

        with pytest.raises(ValueError, match="Invalid bot_name"):
            await tracker.track_operation("nonexistent_bot", "process", 100.0)

    # ── 3. Context manager timing ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_track_async_operation_timing(self):
        """The async context manager measures elapsed time automatically."""
        tracker = PerformanceTracker()

        async with tracker.track_async_operation("lead_bot", "process"):
            await asyncio.sleep(0.05)  # ~50ms

        stats = await tracker.get_bot_stats("lead_bot")
        assert stats["count"] == 1
        assert stats["success_count"] == 1
        # Should have recorded at least 40ms (allowing for timing jitter)
        assert stats["p50"] >= 40.0

    # ── 4. Context manager failure ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_track_async_operation_failure(self):
        """When an exception occurs inside the context manager, success=False is recorded."""
        tracker = PerformanceTracker()

        with pytest.raises(RuntimeError, match="simulated failure"):
            async with tracker.track_async_operation("buyer_bot", "process"):
                raise RuntimeError("simulated failure")

        stats = await tracker.get_bot_stats("buyer_bot")
        assert stats["count"] == 1
        assert stats["error_count"] == 1
        assert stats["success_count"] == 0

    # ── 5. Percentile retrieval ───────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_percentile(self):
        """get_percentile returns correct values for known data."""
        tracker = PerformanceTracker()

        # Track 10 operations with durations 100, 200, ..., 1000
        for i in range(1, 11):
            await tracker.track_operation("lead_bot", "qualify", float(i * 100))

        p50 = await tracker.get_percentile("lead_bot", 50)
        p95 = await tracker.get_percentile("lead_bot", 95)

        # p50 of [100..1000] with linear interpolation: ~550
        assert 500.0 <= p50 <= 600.0
        # p95 should be near the high end
        assert p95 >= 900.0

    # ── 6. Bot stats with data ────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_bot_stats_with_data(self):
        """get_bot_stats returns comprehensive stats when data is present."""
        tracker = PerformanceTracker()

        await tracker.track_operation("seller_bot", "process", 200.0, success=True, cache_hit=True)
        await tracker.track_operation("seller_bot", "process", 400.0, success=True, cache_hit=False)
        await tracker.track_operation("seller_bot", "process", 600.0, success=False, cache_hit=False)

        stats = await tracker.get_bot_stats("seller_bot")

        assert stats["count"] == 3
        assert stats["success_count"] == 2
        assert stats["error_count"] == 1
        assert stats["cache_hit_count"] == 1
        assert stats["min"] == 200.0
        assert stats["max"] == 600.0
        assert pytest.approx(stats["mean"], abs=0.1) == 400.0
        assert pytest.approx(stats["success_rate"], abs=0.01) == 2 / 3
        assert pytest.approx(stats["cache_hit_rate"], abs=0.01) == 1 / 3

    # ── 7. Bot stats empty ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_bot_stats_empty(self):
        """get_bot_stats returns zeroed stats when no data has been recorded."""
        tracker = PerformanceTracker()

        stats = await tracker.get_bot_stats("handoff")

        assert stats["count"] == 0
        assert stats["p50"] == 0.0
        assert stats["p95"] == 0.0
        assert stats["p99"] == 0.0
        assert stats["mean"] == 0.0
        assert stats["success_count"] == 0
        assert stats["error_count"] == 0

    # ── 8. All stats ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_all_stats(self):
        """get_all_stats returns a dict keyed by every valid bot name."""
        tracker = PerformanceTracker()

        await tracker.track_operation("lead_bot", "qualify", 100.0)
        await tracker.track_operation("buyer_bot", "process", 200.0)

        all_stats = await tracker.get_all_stats()

        assert set(all_stats.keys()) == set(VALID_BOT_NAMES)
        assert all_stats["lead_bot"]["count"] == 1
        assert all_stats["buyer_bot"]["count"] == 1
        assert all_stats["seller_bot"]["count"] == 0
        assert all_stats["handoff"]["count"] == 0

    # ── 9. SLA compliance violation ───────────────────────────────────

    @pytest.mark.asyncio
    async def test_check_sla_compliance_violation(self):
        """Slow operations cause SLA violations to be reported."""
        tracker = PerformanceTracker()

        # Track very slow operations for lead_bot (well above SLA targets)
        for _ in range(20):
            await tracker.track_operation("lead_bot", "process", 5000.0)

        compliance = await tracker.check_sla_compliance()

        # Find lead_bot compliance entries
        lead_entries = [c for c in compliance if c["bot_name"] == "lead_bot"]
        assert len(lead_entries) > 0

        # At least one should be non-compliant
        has_violation = any(not c["compliant"] for c in lead_entries)
        assert has_violation is True

        # Check that violations list is populated for non-compliant entries
        for entry in lead_entries:
            if not entry["compliant"]:
                assert len(entry["violations"]) > 0

    # ── 10. SLA compliance compliant ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_check_sla_compliance_compliant(self):
        """Fast operations stay within SLA targets."""
        tracker = PerformanceTracker()

        # Track fast operations (well within handoff SLA: p95 < 500ms)
        for _ in range(20):
            await tracker.track_operation("handoff", "execute", 50.0)

        compliance = await tracker.check_sla_compliance()

        handoff_entries = [c for c in compliance if c["bot_name"] == "handoff"]
        assert len(handoff_entries) > 0

        for entry in handoff_entries:
            assert entry["compliant"] is True
            assert entry["violations"] == []

    # ── 11. Rolling window filtering ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_rolling_window_filtering(self):
        """Entries older than the window are excluded from stats."""
        tracker = PerformanceTracker()

        # Manually inject an old entry by directly manipulating internal state
        from ghl_real_estate_ai.services.jorge.performance_tracker import _OperationEntry

        old_entry = _OperationEntry(
            timestamp=time.time() - 7200,  # 2 hours ago (outside 1h window)
            duration_ms=9999.0,
            success=True,
            cache_hit=False,
        )

        with tracker._data_lock:
            for window_name in WINDOWS:
                tracker._operations["lead_bot"][window_name].append(old_entry)

        # Track a recent operation
        await tracker.track_operation("lead_bot", "qualify", 100.0)

        # 1h window should only show the recent entry
        stats_1h = await tracker.get_bot_stats("lead_bot", window="1h")
        assert stats_1h["count"] == 1
        assert stats_1h["p50"] == 100.0

        # 24h window should show both entries
        stats_24h = await tracker.get_bot_stats("lead_bot", window="24h")
        assert stats_24h["count"] == 2

    # ── 12. Percentile interpolation ──────────────────────────────────

    def test_percentile_interpolation(self):
        """The static _percentile method uses linear interpolation correctly."""
        # Known sorted data: [10, 20, 30, 40, 50]
        data = [10.0, 20.0, 30.0, 40.0, 50.0]

        # p0 = first element
        assert PerformanceTracker._percentile(data, 0) == 10.0

        # p100 = last element
        assert PerformanceTracker._percentile(data, 100) == 50.0

        # p50 with 5 elements: rank = 0.5 * 4 = 2.0 -> index 2 -> 30.0
        assert PerformanceTracker._percentile(data, 50) == 30.0

        # p25: rank = 0.25 * 4 = 1.0 -> index 1 -> 20.0
        assert PerformanceTracker._percentile(data, 25) == 20.0

        # p75: rank = 0.75 * 4 = 3.0 -> index 3 -> 40.0
        assert PerformanceTracker._percentile(data, 75) == 40.0

        # p10: rank = 0.10 * 4 = 0.4 -> 10 + 0.4*(20-10) = 14.0
        assert PerformanceTracker._percentile(data, 10) == 14.0

        # Empty data returns 0
        assert PerformanceTracker._percentile([], 50) == 0.0