"""
Tests for Jorge Performance Tracker Service.

Validates latency tracking, percentile calculations, and SLA compliance.
"""

import time

import pytest

from ghl_real_estate_ai.services.jorge.performance_tracker import (
    PerformanceTracker,
)


class TestPerformanceTracker:
    """Test suite for performance tracking functionality."""

    @pytest.fixture
    def tracker(self):
        """Create a fresh PerformanceTracker instance for each test."""
        PerformanceTracker.reset()
        return PerformanceTracker()

    @pytest.mark.asyncio
    async def test_record_metric_success(self, tracker):
        """Test successful recording of a performance metric."""
        await tracker.track_operation(
            bot_name="lead_bot",
            operation="full_qualification",
            duration_ms=1500,
            success=True,
            cache_hit=False,
        )

        stats = await tracker.get_bot_stats("lead_bot")
        assert stats["count"] == 1
        assert stats["success_count"] == 1
        assert stats["error_count"] == 0

    @pytest.mark.asyncio
    async def test_record_metric_with_tags(self, tracker):
        """Test recording metric with metadata tags."""
        metadata = {"contact_id": "123", "route": "lead_to_buyer"}
        await tracker.track_operation(
            bot_name="buyer_bot",
            operation="process",
            duration_ms=2000,
            success=True,
            cache_hit=True,
            metadata=metadata,
        )

        stats = await tracker.get_bot_stats("buyer_bot")
        assert stats["count"] == 1
        assert stats["cache_hit_count"] == 1
        assert stats["cache_hit_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_get_percentiles_p50(self, tracker):
        """Test P50 percentile calculation."""
        for i in range(10):
            await tracker.track_operation(
                bot_name="lead_bot",
                operation="full_qualification",
                duration_ms=1000 + i * 100,
                success=True,
            )

        p50 = await tracker.get_percentile("lead_bot", 50)
        assert 1400 <= p50 <= 1500

    @pytest.mark.asyncio
    async def test_get_percentiles_p95(self, tracker):
        """Test P95 percentile calculation."""
        for i in range(20):
            await tracker.track_operation(
                bot_name="buyer_bot",
                operation="process",
                duration_ms=1000 + i * 50,
                success=True,
            )

        p95 = await tracker.get_percentile("buyer_bot", 95)
        assert p95 > 1800

    @pytest.mark.asyncio
    async def test_get_percentiles_p99(self, tracker):
        """Test P99 percentile calculation."""
        for i in range(50):
            await tracker.track_operation(
                bot_name="seller_bot",
                operation="full_qualification",
                duration_ms=1000 + i * 20,
                success=True,
            )

        p99 = await tracker.get_percentile("seller_bot", 99)
        assert p99 > 1900

    @pytest.mark.asyncio
    async def test_check_sla_compliance_pass(self, tracker):
        """Test SLA compliance check when metrics are within targets."""
        for _ in range(10):
            await tracker.track_operation(
                bot_name="lead_bot",
                operation="full_qualification",
                duration_ms=400,
                success=True,
            )

        compliance = await tracker.check_sla_compliance()
        lead_bot_compliance = next(
            (c for c in compliance if c["bot_name"] == "lead_bot" and c["operation"] == "full_qualification"), None
        )

        assert lead_bot_compliance is not None
        assert lead_bot_compliance["compliant"] is True
        assert len(lead_bot_compliance["violations"]) == 0

    @pytest.mark.asyncio
    async def test_check_sla_compliance_fail(self, tracker):
        """Test SLA compliance check when metrics exceed targets."""
        for _ in range(10):
            await tracker.track_operation(
                bot_name="lead_bot",
                operation="full_qualification",
                duration_ms=2500,
                success=True,
            )

        compliance = await tracker.check_sla_compliance()
        lead_bot_compliance = next(
            (c for c in compliance if c["bot_name"] == "lead_bot" and c["operation"] == "full_qualification"), None
        )

        assert lead_bot_compliance is not None
        assert lead_bot_compliance["compliant"] is False
        assert len(lead_bot_compliance["violations"]) > 0

    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, tracker):
        """Test getting comprehensive metrics summary."""
        for i in range(10):
            await tracker.track_operation(
                bot_name="lead_bot",
                operation="full_qualification",
                duration_ms=1000 + i * 100,
                success=i < 8,
                cache_hit=i % 2 == 0,
            )

        stats = await tracker.get_bot_stats("lead_bot")
        assert stats["count"] == 10
        assert stats["success_count"] == 8
        assert stats["error_count"] == 2
        assert stats["cache_hit_count"] == 5
        assert stats["success_rate"] == 0.8
        assert stats["cache_hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_get_metrics_by_time_range(self, tracker):
        """Test getting metrics for different time windows."""
        for _ in range(5):
            await tracker.track_operation(
                bot_name="buyer_bot",
                operation="process",
                duration_ms=1500,
                success=True,
            )

        stats_1h = await tracker.get_bot_stats("buyer_bot", window="1h")
        stats_24h = await tracker.get_bot_stats("buyer_bot", window="24h")

        assert stats_1h["count"] == 5
        assert stats_24h["count"] == 5

    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self, tracker):
        """Test that old metrics are filtered out by window."""
        await tracker.track_operation(
            bot_name="lead_bot",
            operation="full_qualification",
            duration_ms=1500,
            success=True,
        )

        with tracker._data_lock:
            for window in tracker._operations["lead_bot"]:
                if tracker._operations["lead_bot"][window]:
                    tracker._operations["lead_bot"][window][0].timestamp = time.time() - 4000

        stats = await tracker.get_bot_stats("lead_bot", window="1h")
        assert stats["count"] == 0

    @pytest.mark.asyncio
    async def test_get_alert_thresholds(self, tracker):
        """Test retrieving SLA alert thresholds."""
        compliance = await tracker.check_sla_compliance()

        for item in compliance:
            assert "p50_target" in item
            assert "p95_target" in item
            assert "p99_target" in item

    @pytest.mark.asyncio
    async def test_export_metrics(self, tracker):
        """Test exporting metrics for all bots."""
        for bot in ["lead_bot", "buyer_bot", "seller_bot"]:
            for _ in range(5):
                await tracker.track_operation(
                    bot_name=bot,
                    operation="process",
                    duration_ms=1500,
                    success=True,
                )

        all_stats = await tracker.get_all_stats()

        assert "lead_bot" in all_stats
        assert "buyer_bot" in all_stats
        assert "seller_bot" in all_stats

        for bot in ["lead_bot", "buyer_bot", "seller_bot"]:
            assert all_stats[bot]["count"] == 5
