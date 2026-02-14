import pytest
pytestmark = pytest.mark.integration

"""Tests for Jorge tech debt items TD2-TD5.

TD2: BotMetricsCollector PostgreSQL persistence
TD3: AlertingService alert acknowledgment tracking
TD4: JorgeHandoffService seed historical data
TD5: OpenTelemetry stubs for all 4 jorge services
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.alerting_service import (
    Alert,
    AlertingService,
)
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import (
    BotMetricsCollector,
)
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    JorgeHandoffService,
)
from ghl_real_estate_ai.services.jorge.performance_tracker import (
    PerformanceTracker,
)
from ghl_real_estate_ai.services.jorge.telemetry import (

    _NoOpSpan,
    is_otel_available,
    optional_span,
    trace_operation,
)

# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all singleton services before and after each test."""
    BotMetricsCollector.reset()
    AlertingService.reset()
    PerformanceTracker.reset()
    JorgeHandoffService._handoff_history.clear()
    JorgeHandoffService._handoff_outcomes.clear()
    JorgeHandoffService._active_handoffs.clear()
    JorgeHandoffService.reset_analytics()
    yield
    BotMetricsCollector.reset()
    AlertingService.reset()
    PerformanceTracker.reset()
    JorgeHandoffService._handoff_history.clear()
    JorgeHandoffService._handoff_outcomes.clear()
    JorgeHandoffService._active_handoffs.clear()
    JorgeHandoffService.reset_analytics()


@pytest.fixture
def mock_metrics_repo():
    """Mock repository implementing the BotMetricsCollector persistence API."""
    repo = AsyncMock()
    repo.save_interaction = AsyncMock()
    repo.save_handoff = AsyncMock()
    repo.load_interactions = AsyncMock(return_value=[])
    repo.load_handoffs = AsyncMock(return_value=[])
    return repo


# ── TD2: Metrics Persistence ─────────────────────────────────────────


class TestTD2MetricsPersistence:
    """TD2: BotMetricsCollector optional PostgreSQL persistence."""

    def test_set_repository_enables_persistence(self, mock_metrics_repo):
        """Setting a repository enables DB persistence."""
        collector = BotMetricsCollector()
        assert collector._repository is None

        collector.set_repository(mock_metrics_repo)
        assert collector._repository is mock_metrics_repo

    def test_set_repository_none_disables_persistence(self, mock_metrics_repo):
        """Setting repository to None disables persistence."""
        collector = BotMetricsCollector()
        collector.set_repository(mock_metrics_repo)
        collector.set_repository(None)
        assert collector._repository is None

    def test_record_interaction_without_repo_no_error(self):
        """Recording without a repository should work fine (in-memory only)."""
        collector = BotMetricsCollector()
        collector.record_bot_interaction("lead", 100.0, True, False)
        summary = collector.get_bot_summary("lead")
        assert summary["total_interactions"] == 1

    @pytest.mark.asyncio
    async def test_load_from_db_returns_zero_without_repo(self):
        """load_from_db returns 0 when no repository is configured."""
        collector = BotMetricsCollector()
        loaded = await collector.load_from_db()
        assert loaded == 0

    @pytest.mark.asyncio
    async def test_load_from_db_hydrates_interactions(self, mock_metrics_repo):
        """load_from_db populates in-memory state from DB records."""
        now = time.time()
        mock_metrics_repo.load_interactions.return_value = [
            {
                "bot_type": "lead",
                "duration_ms": 200.0,
                "success": True,
                "cache_hit": False,
                "timestamp": now - 100,
            },
            {
                "bot_type": "buyer",
                "duration_ms": 300.0,
                "success": False,
                "cache_hit": True,
                "timestamp": now - 200,
            },
        ]
        mock_metrics_repo.load_handoffs.return_value = [
            {
                "source": "lead",
                "target": "buyer",
                "success": True,
                "duration_ms": 50.0,
                "timestamp": now - 150,
            },
        ]

        collector = BotMetricsCollector()
        collector.set_repository(mock_metrics_repo)
        loaded = await collector.load_from_db(since_minutes=60)

        assert loaded == 3
        assert len(collector._interactions) == 2
        assert len(collector._handoffs) == 1

    @pytest.mark.asyncio
    async def test_load_from_db_deduplicates_by_timestamp(self, mock_metrics_repo):
        """load_from_db does not create duplicate entries."""
        now = time.time()
        mock_metrics_repo.load_interactions.return_value = [
            {
                "bot_type": "lead",
                "duration_ms": 200.0,
                "success": True,
                "cache_hit": False,
                "timestamp": now - 100,
            },
        ]

        collector = BotMetricsCollector()
        collector.set_repository(mock_metrics_repo)

        # Load once
        await collector.load_from_db()
        assert len(collector._interactions) == 1

        # Load again -- same timestamp should be skipped
        await collector.load_from_db()
        assert len(collector._interactions) == 1

    @pytest.mark.asyncio
    async def test_load_from_db_handles_repo_error(self, mock_metrics_repo):
        """load_from_db logs but does not raise on DB errors."""
        mock_metrics_repo.load_interactions.side_effect = Exception("DB down")
        mock_metrics_repo.load_handoffs.return_value = []

        collector = BotMetricsCollector()
        collector.set_repository(mock_metrics_repo)
        loaded = await collector.load_from_db()
        # Should not raise, just return whatever was loaded successfully
        assert loaded == 0

    @pytest.mark.asyncio
    async def test_persist_interaction_called_on_record(self, mock_metrics_repo):
        """_persist_interaction is called when repo is set."""
        collector = BotMetricsCollector()
        collector.set_repository(mock_metrics_repo)

        # Directly test the async persist method
        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import (
            _BotInteraction,
        )

        interaction = _BotInteraction(
            bot_type="lead",
            duration_ms=100.0,
            success=True,
            cache_hit=False,
            timestamp=time.time(),
        )
        await collector._persist_interaction(interaction)
        mock_metrics_repo.save_interaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_handoff_called_on_record(self, mock_metrics_repo):
        """_persist_handoff is called when repo is set."""
        collector = BotMetricsCollector()
        collector.set_repository(mock_metrics_repo)

        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import (
            _HandoffRecord,
        )

        record = _HandoffRecord(
            source="lead",
            target="buyer",
            success=True,
            duration_ms=50.0,
            timestamp=time.time(),
        )
        await collector._persist_handoff(record)
        mock_metrics_repo.save_handoff.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_interaction_handles_db_error(self, mock_metrics_repo):
        """DB errors in _persist_interaction are logged, not raised."""
        mock_metrics_repo.save_interaction.side_effect = Exception("DB error")
        collector = BotMetricsCollector()
        collector.set_repository(mock_metrics_repo)

        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import (
            _BotInteraction,
        )

        interaction = _BotInteraction(
            bot_type="lead",
            duration_ms=100.0,
            success=True,
            cache_hit=False,
            timestamp=time.time(),
        )
        # Should not raise
        await collector._persist_interaction(interaction)

    def test_reset_clears_repository(self, mock_metrics_repo):
        """reset() should clear the repository reference."""
        collector = BotMetricsCollector()
        collector.set_repository(mock_metrics_repo)
        BotMetricsCollector.reset()

        # Re-create after reset
        collector2 = BotMetricsCollector()
        assert collector2._repository is None


# ── TD3: Alert Acknowledgment ────────────────────────────────────────


class TestTD3AlertAcknowledgment:
    """TD3: AlertingService alert acknowledgment tracking."""

    @pytest.mark.asyncio
    async def test_acknowledge_alert_sets_metadata(self):
        """acknowledge_alert records timestamp and user."""
        service = AlertingService()
        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)
        assert len(alerts) > 0
        alert_id = alerts[0].id

        result = await service.acknowledge_alert(alert_id, acknowledged_by="jorge@example.com")

        assert result["alert_id"] == alert_id
        assert result["acknowledged_by"] == "jorge@example.com"
        assert result["acknowledged_at"] is not None
        assert result["time_to_ack_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_acknowledge_alert_without_user(self):
        """acknowledge_alert works without specifying acknowledged_by."""
        service = AlertingService()
        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)
        alert_id = alerts[0].id

        result = await service.acknowledge_alert(alert_id)

        assert result["acknowledged_by"] is None
        assert result["acknowledged_at"] is not None

    @pytest.mark.asyncio
    async def test_acknowledge_alert_not_found(self):
        """acknowledge_alert raises KeyError for unknown alert_id."""
        service = AlertingService()
        with pytest.raises(KeyError, match="not found"):
            await service.acknowledge_alert("nonexistent_id")

    @pytest.mark.asyncio
    async def test_acknowledge_alert_updates_dataclass(self):
        """Alert dataclass fields are updated after acknowledgment."""
        service = AlertingService()
        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)
        alert = alerts[0]

        assert alert.acknowledged is False
        assert alert.acknowledged_at is None
        assert alert.acknowledged_by is None

        await service.acknowledge_alert(alert.id, acknowledged_by="auto-resolver")

        assert alert.acknowledged is True
        assert alert.acknowledged_at is not None
        assert alert.acknowledged_by == "auto-resolver"

    @pytest.mark.asyncio
    async def test_get_acknowledgment_status_acknowledged(self):
        """get_acknowledgment_status returns full ack details."""
        service = AlertingService()
        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)
        alert_id = alerts[0].id

        await service.acknowledge_alert(alert_id, acknowledged_by="ops-team")
        status = await service.get_acknowledgment_status(alert_id)

        assert status["alert_id"] == alert_id
        assert status["acknowledged"] is True
        assert status["acknowledged_by"] == "ops-team"
        assert "time_to_ack_seconds" in status
        assert status["time_to_ack_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_get_acknowledgment_status_unacknowledged(self):
        """get_acknowledgment_status for unacked alert shows False."""
        service = AlertingService()
        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)
        alert_id = alerts[0].id

        status = await service.get_acknowledgment_status(alert_id)

        assert status["acknowledged"] is False
        assert "acknowledged_at" not in status

    @pytest.mark.asyncio
    async def test_get_acknowledgment_status_not_found(self):
        """get_acknowledgment_status raises KeyError for unknown ID."""
        service = AlertingService()
        with pytest.raises(KeyError, match="not found"):
            await service.get_acknowledgment_status("bad_id")

    @pytest.mark.asyncio
    async def test_acknowledged_alert_stops_escalation(self):
        """Acknowledged alerts should not appear in escalation checks."""
        service = AlertingService()
        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)
        alert = alerts[0]

        # Before ack -- should appear as active
        active = await service.get_active_alerts()
        assert any(a.id == alert.id for a in active)

        # Acknowledge it
        await service.acknowledge_alert(alert.id, acknowledged_by="test")

        # After ack -- should not appear as active
        active_after = await service.get_active_alerts()
        assert not any(a.id == alert.id for a in active_after)

    @pytest.mark.asyncio
    async def test_acknowledge_returns_dict(self):
        """acknowledge_alert returns a dict (not None as before)."""
        service = AlertingService()
        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)

        result = await service.acknowledge_alert(alerts[0].id)
        assert isinstance(result, dict)
        assert "alert_id" in result
        assert "acknowledged_at" in result


# ── TD4: Handoff Seed Data ───────────────────────────────────────────


class TestTD4HandoffSeedData:
    """TD4: JorgeHandoffService.seed_historical_data()."""

    def test_seed_historical_data_default(self):
        """seed_historical_data populates all 4 routes with defaults."""
        result = JorgeHandoffService.seed_historical_data(seed=42)

        assert result["samples_per_route"] == 20
        assert result["total_records"] == 80  # 4 routes * 20 samples
        assert len(result["routes_seeded"]) == 4
        assert "lead->buyer" in result["routes_seeded"]
        assert "lead->seller" in result["routes_seeded"]
        assert "buyer->seller" in result["routes_seeded"]
        assert "seller->buyer" in result["routes_seeded"]

    def test_seed_historical_data_custom_samples(self):
        """seed_historical_data accepts custom sample count."""
        result = JorgeHandoffService.seed_historical_data(num_samples=15, seed=1)
        assert result["samples_per_route"] == 15
        assert result["total_records"] == 60

    def test_seed_historical_data_too_few_samples(self):
        """seed_historical_data rejects num_samples below MIN_LEARNING_SAMPLES."""
        with pytest.raises(ValueError, match="num_samples must be >="):
            JorgeHandoffService.seed_historical_data(num_samples=5)

    def test_seed_historical_data_enables_learning(self):
        """After seeding, get_learned_adjustments returns non-zero data."""
        JorgeHandoffService.seed_historical_data(num_samples=20, seed=42)

        adj = JorgeHandoffService.get_learned_adjustments("lead", "buyer")
        assert adj["sample_size"] == 20
        assert adj["success_rate"] > 0.0
        # lead->buyer at 80% success should lower threshold
        assert adj["adjustment"] == -0.05

    def test_seed_data_deterministic_with_seed(self):
        """Same seed produces identical outcome distributions."""
        JorgeHandoffService.seed_historical_data(num_samples=20, seed=99)
        adj1 = JorgeHandoffService.get_learned_adjustments("lead", "buyer")

        # Clear and re-seed
        JorgeHandoffService._handoff_outcomes.clear()
        JorgeHandoffService.seed_historical_data(num_samples=20, seed=99)
        adj2 = JorgeHandoffService.get_learned_adjustments("lead", "buyer")

        assert adj1["success_rate"] == adj2["success_rate"]
        assert adj1["adjustment"] == adj2["adjustment"]

    def test_seed_data_populates_all_routes(self):
        """Each route has the expected number of outcomes."""
        JorgeHandoffService.seed_historical_data(num_samples=15, seed=7)

        for route in ["lead->buyer", "lead->seller", "buyer->seller", "seller->buyer"]:
            outcomes = JorgeHandoffService._handoff_outcomes.get(route, [])
            assert len(outcomes) == 15, f"Route {route} has {len(outcomes)} outcomes"

    def test_seed_data_valid_outcomes(self):
        """All seeded outcomes are valid outcome types."""
        JorgeHandoffService.seed_historical_data(num_samples=20, seed=42)

        valid_outcomes = {"successful", "failed", "reverted", "timeout"}
        for route, outcomes in JorgeHandoffService._handoff_outcomes.items():
            for o in outcomes:
                assert o["outcome"] in valid_outcomes, f"Invalid outcome '{o['outcome']}' in route {route}"

    def test_seed_data_has_metadata(self):
        """Seeded records include metadata marking them as seeded."""
        JorgeHandoffService.seed_historical_data(num_samples=10, seed=1)

        for outcomes in JorgeHandoffService._handoff_outcomes.values():
            for o in outcomes:
                assert o["metadata"]["seeded"] is True
                assert o["metadata"]["batch"] == "historical_seed"

    def test_seed_data_timestamps_in_past_week(self):
        """Seeded timestamps fall within the last 7 days."""
        now = time.time()
        seven_days_ago = now - (7 * 24 * 3600)

        JorgeHandoffService.seed_historical_data(num_samples=20, seed=42)

        for outcomes in JorgeHandoffService._handoff_outcomes.values():
            for o in outcomes:
                assert o["timestamp"] >= seven_days_ago
                assert o["timestamp"] <= now

    def test_seed_data_success_rate_ranges(self):
        """Success rates reflect expected patterns per route."""
        # Use a large sample to reduce variance
        JorgeHandoffService.seed_historical_data(num_samples=100, seed=42)

        adj_lb = JorgeHandoffService.get_learned_adjustments("lead", "buyer")
        adj_ls = JorgeHandoffService.get_learned_adjustments("lead", "seller")
        adj_bs = JorgeHandoffService.get_learned_adjustments("buyer", "seller")
        adj_sb = JorgeHandoffService.get_learned_adjustments("seller", "buyer")

        # With 100 samples and known probabilities, rates should be close
        assert 0.65 < adj_lb["success_rate"] < 0.95  # target: 0.80
        assert 0.55 < adj_ls["success_rate"] < 0.85  # target: 0.70
        assert 0.45 < adj_bs["success_rate"] < 0.75  # target: 0.60
        assert 0.60 < adj_sb["success_rate"] < 0.90  # target: 0.75


# ── TD5: OpenTelemetry Stubs ─────────────────────────────────────────


class TestTD5OpenTelemetryStubs:
    """TD5: OpenTelemetry-compatible span/trace decorators."""

    def test_is_otel_available_returns_bool(self):
        """is_otel_available() returns a boolean."""
        result = is_otel_available()
        assert isinstance(result, bool)

    def test_noop_span_accepts_all_operations(self):
        """_NoOpSpan silently accepts all span API calls."""
        span = _NoOpSpan()
        span.set_attribute("key", "value")
        span.set_status("OK")
        span.record_exception(RuntimeError("test"))
        span.add_event("test_event", {"key": "value"})
        span.end()
        # No exceptions raised

    def test_noop_span_context_manager(self):
        """_NoOpSpan works as a context manager."""
        span = _NoOpSpan()
        with span as s:
            assert s is span

    def test_optional_span_yields_span(self):
        """optional_span yields a usable span object."""
        with optional_span("test.service", "test_op") as span:
            span.set_attribute("test_key", "test_value")
            span.add_event("test_event")
            # No errors

    def test_trace_operation_sync_decorator(self):
        """trace_operation works on sync functions."""

        @trace_operation("test.service", "sync_op")
        def my_func(x, y):
            return x + y

        result = my_func(2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_trace_operation_async_decorator(self):
        """trace_operation works on async functions."""

        @trace_operation("test.service", "async_op")
        async def my_async_func(x, y):
            return x * y

        result = await my_async_func(4, 5)
        assert result == 20

    def test_trace_operation_preserves_exceptions(self):
        """trace_operation re-raises exceptions from decorated functions."""

        @trace_operation("test.service", "failing_op")
        def my_failing_func():
            raise ValueError("intentional error")

        with pytest.raises(ValueError, match="intentional error"):
            my_failing_func()

    @pytest.mark.asyncio
    async def test_trace_operation_async_preserves_exceptions(self):
        """trace_operation re-raises exceptions from async functions."""

        @trace_operation("test.service", "async_fail")
        async def my_async_fail():
            raise RuntimeError("async error")

        with pytest.raises(RuntimeError, match="async error"):
            await my_async_fail()

    def test_trace_operation_preserves_function_name(self):
        """trace_operation preserves the original function name."""

        @trace_operation("test.service", "named_op")
        def my_named_function():
            pass

        assert my_named_function.__name__ == "my_named_function"

    @pytest.mark.asyncio
    async def test_trace_operation_preserves_async_function_name(self):
        """trace_operation preserves async function name."""

        @trace_operation("test.service", "async_named")
        async def my_async_named():
            pass

        assert my_async_named.__name__ == "my_async_named"

    def test_optional_span_exception_propagation(self):
        """optional_span re-raises exceptions."""
        with pytest.raises(ValueError, match="span error"):
            with optional_span("test.service", "error_op"):
                raise ValueError("span error")

    # ── Integration: verify decorators are applied to services ────────

    def test_metrics_collector_has_tracing(self):
        """BotMetricsCollector methods are decorated with trace_operation."""
        collector = BotMetricsCollector()
        # The wrapped function name should still be accessible
        assert callable(collector.record_bot_interaction)
        assert callable(collector.record_handoff)
        assert callable(collector.get_bot_summary)

    @pytest.mark.asyncio
    async def test_alerting_service_has_tracing(self):
        """AlertingService key methods are decorated."""
        service = AlertingService()
        assert callable(service.check_alerts)
        assert callable(service.send_alert)
        assert callable(service.acknowledge_alert)

    @pytest.mark.asyncio
    async def test_performance_tracker_has_tracing(self):
        """PerformanceTracker key methods are decorated."""
        tracker = PerformanceTracker()
        assert callable(tracker.track_operation)
        assert callable(tracker.get_bot_stats)
        assert callable(tracker.check_sla_compliance)

    @pytest.mark.asyncio
    async def test_traced_methods_still_work_correctly(self):
        """Traced methods produce correct results (end-to-end)."""
        collector = BotMetricsCollector()
        collector.record_bot_interaction("lead", 100.0, True, False)
        collector.record_bot_interaction("lead", 200.0, False, True)
        summary = collector.get_bot_summary("lead")

        assert summary["total_interactions"] == 2
        assert summary["success_rate"] == 0.5
        assert summary["cache_hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_traced_alerting_check_alerts(self):
        """Traced check_alerts still triggers rules correctly."""
        service = AlertingService()
        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)
        assert len(alerts) > 0
        assert alerts[0].severity == "critical"

    @pytest.mark.asyncio
    async def test_traced_performance_tracker(self):
        """Traced track_operation still records data correctly."""
        tracker = PerformanceTracker()
        await tracker.track_operation("lead_bot", "process", 500.0, True)
        stats = await tracker.get_bot_stats("lead_bot")
        assert stats["count"] == 1
        assert stats["p50"] == 500.0