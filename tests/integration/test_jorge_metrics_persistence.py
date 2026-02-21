import pytest

pytestmark = pytest.mark.integration

"""Integration tests for Jorge metrics persistence.

Verifies the full flow from service layer through to repository calls:
- BotMetricsCollector wired with repository persists interactions/handoffs
- PerformanceTracker set_repository + _persist_operation flow
- AlertingService persistence round-trip for alerts

Uses mocked repository to avoid needing a live database, but tests the
complete wiring from services through to repository method invocations.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.repositories.jorge_metrics_repository import (
    JorgeMetricsRepository,
)
from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker


@pytest.fixture(autouse=True)
def reset_all():
    """Reset all singleton services before and after each test."""
    PerformanceTracker.reset()
    BotMetricsCollector.reset()
    AlertingService.reset()
    yield
    PerformanceTracker.reset()
    BotMetricsCollector.reset()
    AlertingService.reset()


@pytest.fixture
def mock_repo():
    """Return a mock repository with all async methods stubbed."""
    repo = AsyncMock(spec=JorgeMetricsRepository)
    repo.save_interaction = AsyncMock()
    repo.save_handoff = AsyncMock()
    repo.save_performance_operation = AsyncMock()
    repo.save_alert = AsyncMock()
    repo.load_interactions = AsyncMock(return_value=[])
    repo.load_handoffs = AsyncMock(return_value=[])
    repo.load_performance_operations = AsyncMock(return_value=[])
    repo.load_alerts = AsyncMock(return_value=[])
    repo.load_alert_rules = AsyncMock(return_value=[])
    repo.acknowledge_alert_db = AsyncMock(return_value={})
    return repo


# ── BotMetricsCollector Persistence ───────────────────────────────────


class TestBotMetricsCollectorPersistence:
    """Tests that BotMetricsCollector correctly calls repository methods."""

    def test_set_repository_wires_repo(self, mock_repo):
        """set_repository should store the repository reference."""
        collector = BotMetricsCollector()
        collector.set_repository(mock_repo)
        assert collector._repository is mock_repo

    def test_set_repository_none_disables(self):
        """set_repository(None) should disable persistence."""
        collector = BotMetricsCollector()
        collector.set_repository(None)
        assert collector._repository is None

    @pytest.mark.asyncio
    async def test_record_interaction_persists(self, mock_repo):
        """record_bot_interaction should fire-and-forget to repository."""
        collector = BotMetricsCollector()
        collector.set_repository(mock_repo)

        # record_bot_interaction is sync but triggers async persist internally
        collector.record_bot_interaction("lead", duration_ms=450.0, success=True, cache_hit=True)

        # Give the event loop a tick to run the fire-and-forget coroutine
        await asyncio.sleep(0.05)

        mock_repo.save_interaction.assert_awaited_once()
        call_kwargs = mock_repo.save_interaction.call_args[1]
        assert call_kwargs["bot_type"] == "lead"
        assert call_kwargs["duration_ms"] == 450.0
        assert call_kwargs["success"] is True
        assert call_kwargs["cache_hit"] is True

    @pytest.mark.asyncio
    async def test_record_handoff_persists(self, mock_repo):
        """record_handoff should fire-and-forget to repository."""
        collector = BotMetricsCollector()
        collector.set_repository(mock_repo)

        collector.record_handoff("lead", "buyer", success=True, duration_ms=120.0)

        await asyncio.sleep(0.05)

        mock_repo.save_handoff.assert_awaited_once()
        call_kwargs = mock_repo.save_handoff.call_args[1]
        assert call_kwargs["source"] == "lead"
        assert call_kwargs["target"] == "buyer"
        assert call_kwargs["success"] is True
        assert call_kwargs["duration_ms"] == 120.0

    @pytest.mark.asyncio
    async def test_interaction_persist_failure_doesnt_block(self, mock_repo):
        """DB failures in persist should not block the caller."""
        mock_repo.save_interaction.side_effect = Exception("connection lost")
        collector = BotMetricsCollector()
        collector.set_repository(mock_repo)

        # Should not raise
        collector.record_bot_interaction("buyer", duration_ms=200.0, success=True)
        await asyncio.sleep(0.05)

        # Interaction should still be in memory
        summary = collector.get_bot_summary("buyer")
        assert summary["total_interactions"] == 1

    @pytest.mark.asyncio
    async def test_load_from_db_hydrates_memory(self, mock_repo):
        """load_from_db should hydrate in-memory state from repository."""
        mock_repo.load_interactions.return_value = [
            {
                "bot_type": "seller",
                "duration_ms": 300.0,
                "success": True,
                "cache_hit": False,
                "timestamp": time.time() - 100,
            }
        ]
        mock_repo.load_handoffs.return_value = [
            {
                "source": "lead",
                "target": "seller",
                "success": True,
                "duration_ms": 80.0,
                "timestamp": time.time() - 100,
            }
        ]

        collector = BotMetricsCollector()
        collector.set_repository(mock_repo)

        loaded = await collector.load_from_db(since_minutes=60)
        assert loaded == 2

        summary = collector.get_bot_summary("seller")
        assert summary["total_interactions"] == 1


# ── PerformanceTracker Persistence ────────────────────────────────────


class TestPerformanceTrackerPersistence:
    """Tests that PerformanceTracker correctly calls repository methods."""

    def test_set_repository_wires_repo(self, mock_repo):
        """set_repository should store the repository reference."""
        tracker = PerformanceTracker()
        tracker.set_repository(mock_repo)
        assert tracker._repository is mock_repo

    def test_set_repository_none_disables(self):
        """set_repository(None) should disable persistence."""
        tracker = PerformanceTracker()
        tracker.set_repository(None)
        assert tracker._repository is None

    @pytest.mark.asyncio
    async def test_track_operation_persists(self, mock_repo):
        """track_operation should fire-and-forget to repository."""
        tracker = PerformanceTracker()
        tracker.set_repository(mock_repo)

        await tracker.track_operation("lead_bot", "qualify", 1500.0, True, False)

        # Give fire-and-forget a tick
        await asyncio.sleep(0.05)

        mock_repo.save_performance_operation.assert_awaited_once()
        call_kwargs = mock_repo.save_performance_operation.call_args[1]
        assert call_kwargs["bot_name"] == "lead_bot"
        assert call_kwargs["operation"] == "qualify"
        assert call_kwargs["duration_ms"] == 1500.0

    @pytest.mark.asyncio
    async def test_track_operation_persist_failure_doesnt_block(self, mock_repo):
        """DB failures should not block PerformanceTracker operations."""
        mock_repo.save_performance_operation.side_effect = Exception("timeout")
        tracker = PerformanceTracker()
        tracker.set_repository(mock_repo)

        # Should not raise
        await tracker.track_operation("lead_bot", "process", 500.0, True)
        await asyncio.sleep(0.05)

        # In-memory tracking should still work
        stats = await tracker.get_bot_stats("lead_bot")
        assert stats["count"] == 1

    @pytest.mark.asyncio
    async def test_track_without_repo_skips_persist(self):
        """track_operation without a repository should skip persistence."""
        tracker = PerformanceTracker()
        # No set_repository call

        # Should work purely in-memory
        await tracker.track_operation("buyer_bot", "process", 300.0, True)
        stats = await tracker.get_bot_stats("buyer_bot")
        assert stats["count"] == 1


# ── AlertingService Persistence ───────────────────────────────────────


class TestAlertingServicePersistence:
    """Tests that AlertingService correctly calls repository methods."""

    def test_set_repository_wires_repo(self, mock_repo):
        """set_repository should store the repository reference."""
        service = AlertingService()
        service.set_repository(mock_repo)
        assert service._repository is mock_repo

    def test_set_repository_none_disables(self):
        """set_repository(None) should disable persistence."""
        service = AlertingService()
        service.set_repository(None)
        assert service._repository is None

    @pytest.mark.asyncio
    async def test_check_alerts_persists_triggered(self, mock_repo):
        """check_alerts should persist triggered alerts to repository."""
        service = AlertingService()
        service.set_repository(mock_repo)

        # Trigger the high_error_rate rule (error_rate > 0.05)
        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)

        await asyncio.sleep(0.05)

        assert len(alerts) >= 1
        # Verify at least one save_alert call was made
        assert mock_repo.save_alert.await_count >= 1

    @pytest.mark.asyncio
    async def test_alert_persist_failure_doesnt_block(self, mock_repo):
        """DB failures in alert persist should not block alerting."""
        mock_repo.save_alert.side_effect = Exception("disk full")
        service = AlertingService()
        service.set_repository(mock_repo)

        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)

        # Alerts should still be stored in-memory
        assert len(alerts) >= 1
        history = await service.get_alert_history()
        assert len(history) >= 1

    @pytest.mark.asyncio
    async def test_enable_disable_rule(self):
        """enable_rule and disable_rule should toggle rule availability."""
        service = AlertingService()

        rules_before = await service.list_rules()
        rule_names = {r.name for r in rules_before}
        assert "high_error_rate" in rule_names

        await service.disable_rule("high_error_rate")

        # Disabled rule should not trigger
        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)
        triggered_names = {a.rule_name for a in alerts}
        assert "high_error_rate" not in triggered_names

        await service.enable_rule("high_error_rate")

        # Re-enabled rule should trigger
        # Need to clear cooldown first
        service._last_fired.pop("high_error_rate", None)
        alerts = await service.check_alerts(stats)
        triggered_names = {a.rule_name for a in alerts}
        assert "high_error_rate" in triggered_names


# ── Cross-Service Persistence Flow ────────────────────────────────────


class TestCrossServicePersistenceFlow:
    """Tests the full persistence flow across multiple services."""

    @pytest.mark.asyncio
    async def test_collector_to_alerting_persistence_flow(self, mock_repo):
        """Verify collector feeds alerting, and both persist to repository."""
        collector = BotMetricsCollector()
        collector.set_repository(mock_repo)

        alerting = AlertingService()
        alerting.set_repository(mock_repo)

        # Record enough failed interactions to trigger error alert
        for _ in range(20):
            collector.record_bot_interaction("lead", duration_ms=100.0, success=False)

        await asyncio.sleep(0.05)

        # Feed aggregated metrics into alerting
        collector.feed_to_alerting(alerting)

        # Check alerts with the recorded metrics
        metrics = alerting.get_recorded_metrics()
        alerts = await alerting.check_alerts(metrics)

        await asyncio.sleep(0.05)

        # Interactions should have been persisted
        assert mock_repo.save_interaction.await_count == 20

        # At least one alert should have been triggered and persisted
        assert mock_repo.save_alert.await_count >= 1

    @pytest.mark.asyncio
    async def test_tracker_persist_flow(self, mock_repo):
        """Verify PerformanceTracker persists operations to repository."""
        tracker = PerformanceTracker()
        tracker.set_repository(mock_repo)

        # Track multiple operations
        for i in range(5):
            await tracker.track_operation("lead_bot", "qualify", 1000.0 + i * 100, True)

        await asyncio.sleep(0.05)

        # All 5 operations should be persisted
        assert mock_repo.save_performance_operation.await_count == 5

        # In-memory stats should also be available
        stats = await tracker.get_bot_stats("lead_bot")
        assert stats["count"] == 5
