"""Unit tests for JorgeMetricsRepository.

All database calls are mocked via unittest.mock.AsyncMock so that
tests run without a live PostgreSQL instance.  Each test method
verifies a single CRUD operation on the repository.
"""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.repositories.jorge_metrics_repository import (
    JorgeMetricsRepository,
)

# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def mock_pool():
    """Return an AsyncMock that behaves like an asyncpg pool."""
    pool = AsyncMock()
    pool.execute = AsyncMock(return_value=None)
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchrow = AsyncMock(return_value=None)
    pool.close = AsyncMock()
    return pool


@pytest.fixture
def repo(mock_pool):
    """Return a JorgeMetricsRepository with a pre-injected mock pool."""
    r = JorgeMetricsRepository(dsn="postgresql://test:test@localhost/test")
    r._pool = mock_pool
    return r


# ── Interaction Tests ─────────────────────────────────────────────────


class TestSaveInteraction:
    """Tests for save_interaction."""

    @pytest.mark.asyncio
    async def test_save_interaction_calls_execute(self, repo, mock_pool):
        """save_interaction should INSERT a row into jorge_bot_interactions."""
        ts = time.time()
        await repo.save_interaction("lead", 450.0, True, True, ts)

        mock_pool.execute.assert_awaited_once()
        call_args = mock_pool.execute.call_args
        sql = call_args[0][0]
        assert "INSERT INTO jorge_bot_interactions" in sql
        assert call_args[0][1] == "lead"
        assert call_args[0][2] == 450.0
        assert call_args[0][3] is True
        assert call_args[0][4] is True
        assert call_args[0][5] == ts

    @pytest.mark.asyncio
    async def test_save_interaction_with_metadata(self, repo, mock_pool):
        """save_interaction should JSON-serialize metadata when provided."""
        ts = time.time()
        meta = {"model": "claude-3", "tokens": 150}
        await repo.save_interaction("buyer", 200.0, True, False, ts, metadata=meta)

        call_args = mock_pool.execute.call_args
        assert call_args[0][6] == json.dumps(meta)

    @pytest.mark.asyncio
    async def test_save_interaction_db_failure_logged(self, repo, mock_pool):
        """save_interaction should log but not raise on DB failure."""
        mock_pool.execute.side_effect = Exception("connection refused")
        # Should not raise
        await repo.save_interaction("lead", 100.0, True, False, time.time())


class TestLoadInteractions:
    """Tests for load_interactions."""

    @pytest.mark.asyncio
    async def test_load_interactions_returns_rows(self, repo, mock_pool):
        """load_interactions should return parsed dicts from DB rows."""
        mock_pool.fetch.return_value = [
            {
                "bot_type": "lead",
                "duration_ms": 450.0,
                "success": True,
                "cache_hit": True,
                "timestamp": 1000.0,
                "metadata": None,
            }
        ]
        result = await repo.load_interactions(since_timestamp=900.0)
        assert len(result) == 1
        assert result[0]["bot_type"] == "lead"
        assert result[0]["duration_ms"] == 450.0
        assert result[0]["timestamp"] == 1000.0

    @pytest.mark.asyncio
    async def test_load_interactions_empty(self, repo, mock_pool):
        """load_interactions should return empty list when no rows match."""
        mock_pool.fetch.return_value = []
        result = await repo.load_interactions(since_timestamp=time.time())
        assert result == []

    @pytest.mark.asyncio
    async def test_load_interactions_db_failure(self, repo, mock_pool):
        """load_interactions should return empty list on DB failure."""
        mock_pool.fetch.side_effect = Exception("timeout")
        result = await repo.load_interactions(since_timestamp=0.0)
        assert result == []


# ── Handoff Tests ─────────────────────────────────────────────────────


class TestSaveHandoff:
    """Tests for save_handoff."""

    @pytest.mark.asyncio
    async def test_save_handoff_calls_execute(self, repo, mock_pool):
        """save_handoff should INSERT a row into jorge_handoff_events."""
        ts = time.time()
        await repo.save_handoff("lead", "buyer", True, 120.0, ts)

        mock_pool.execute.assert_awaited_once()
        call_args = mock_pool.execute.call_args
        sql = call_args[0][0]
        assert "INSERT INTO jorge_handoff_events" in sql
        assert call_args[0][1] == "lead"
        assert call_args[0][2] == "buyer"

    @pytest.mark.asyncio
    async def test_save_handoff_db_failure_logged(self, repo, mock_pool):
        """save_handoff should not raise on DB failure."""
        mock_pool.execute.side_effect = Exception("connection refused")
        await repo.save_handoff("lead", "buyer", True, 100.0, time.time())


class TestLoadHandoffs:
    """Tests for load_handoffs."""

    @pytest.mark.asyncio
    async def test_load_handoffs_returns_rows(self, repo, mock_pool):
        """load_handoffs should return parsed dicts from DB rows."""
        mock_pool.fetch.return_value = [
            {
                "source_bot": "lead",
                "target_bot": "buyer",
                "success": True,
                "duration_ms": 120.0,
                "timestamp": 1000.0,
            }
        ]
        result = await repo.load_handoffs(since_timestamp=900.0)
        assert len(result) == 1
        assert result[0]["source"] == "lead"
        assert result[0]["target"] == "buyer"

    @pytest.mark.asyncio
    async def test_load_handoffs_db_failure(self, repo, mock_pool):
        """load_handoffs should return empty list on DB failure."""
        mock_pool.fetch.side_effect = Exception("timeout")
        result = await repo.load_handoffs(since_timestamp=0.0)
        assert result == []


# ── Performance Operations Tests ──────────────────────────────────────


class TestSavePerformanceOperation:
    """Tests for save_performance_operation."""

    @pytest.mark.asyncio
    async def test_save_perf_op_calls_execute(self, repo, mock_pool):
        """save_performance_operation should INSERT a row."""
        ts = time.time()
        await repo.save_performance_operation(
            bot_name="lead_bot",
            operation="qualify",
            duration_ms=1500.0,
            success=True,
            cache_hit=False,
            metadata={"key": "val"},
            timestamp=ts,
        )

        mock_pool.execute.assert_awaited_once()
        call_args = mock_pool.execute.call_args
        sql = call_args[0][0]
        assert "INSERT INTO jorge_performance_operations" in sql
        assert call_args[0][1] == "lead_bot"
        assert call_args[0][2] == "qualify"

    @pytest.mark.asyncio
    async def test_save_perf_op_default_timestamp(self, repo, mock_pool):
        """save_performance_operation should use current time when timestamp is None."""
        before = time.time()
        await repo.save_performance_operation(
            bot_name="buyer_bot",
            operation="process",
            duration_ms=200.0,
            success=True,
            cache_hit=True,
        )
        after = time.time()

        call_args = mock_pool.execute.call_args
        ts_arg = call_args[0][7]  # timestamp is the 7th positional arg
        assert before <= ts_arg <= after

    @pytest.mark.asyncio
    async def test_save_perf_op_db_failure(self, repo, mock_pool):
        """save_performance_operation should not raise on DB failure."""
        mock_pool.execute.side_effect = Exception("disk full")
        await repo.save_performance_operation(
            "lead_bot", "qualify", 1000.0, True, False,
        )


class TestLoadPerformanceOperations:
    """Tests for load_performance_operations."""

    @pytest.mark.asyncio
    async def test_load_perf_ops_returns_rows(self, repo, mock_pool):
        """load_performance_operations should return parsed dicts."""
        mock_pool.fetch.return_value = [
            {
                "bot_name": "lead_bot",
                "operation": "qualify",
                "duration_ms": 1500.0,
                "success": True,
                "cache_hit": False,
                "metadata": json.dumps({"key": "val"}),
                "timestamp": 1000.0,
            }
        ]
        result = await repo.load_performance_operations(since_timestamp=900.0)
        assert len(result) == 1
        assert result[0]["bot_name"] == "lead_bot"
        assert result[0]["metadata"] == {"key": "val"}

    @pytest.mark.asyncio
    async def test_load_perf_ops_db_failure(self, repo, mock_pool):
        """load_performance_operations should return empty list on failure."""
        mock_pool.fetch.side_effect = Exception("timeout")
        result = await repo.load_performance_operations(since_timestamp=0.0)
        assert result == []


# ── Alert Tests ───────────────────────────────────────────────────────


class TestSaveAlert:
    """Tests for save_alert."""

    @pytest.mark.asyncio
    async def test_save_alert_calls_execute(self, repo, mock_pool):
        """save_alert should INSERT a row into jorge_alerts."""
        ts = time.time()
        await repo.save_alert(
            rule_name="sla_violation",
            severity="critical",
            message="P95 exceeded target",
            triggered_at=ts,
            performance_stats={"p95": 2500},
            channels_sent=["slack", "email"],
        )

        mock_pool.execute.assert_awaited_once()
        call_args = mock_pool.execute.call_args
        sql = call_args[0][0]
        assert "INSERT INTO jorge_alerts" in sql
        assert call_args[0][1] == "sla_violation"

    @pytest.mark.asyncio
    async def test_save_alert_db_failure(self, repo, mock_pool):
        """save_alert should not raise on DB failure."""
        mock_pool.execute.side_effect = Exception("connection refused")
        await repo.save_alert("test", "warning", "msg", time.time())


class TestLoadAlerts:
    """Tests for load_alerts."""

    @pytest.mark.asyncio
    async def test_load_alerts_returns_rows(self, repo, mock_pool):
        """load_alerts should return parsed alert dicts."""
        mock_pool.fetch.return_value = [
            {
                "id": 1,
                "rule_name": "sla_violation",
                "severity": "critical",
                "message": "P95 exceeded",
                "triggered_at": 1000.0,
                "performance_stats": json.dumps({"p95": 2500}),
                "channels_sent": json.dumps(["slack"]),
                "acknowledged": False,
                "acknowledged_at": None,
                "acknowledged_by": None,
            }
        ]
        result = await repo.load_alerts(limit=10)
        assert len(result) == 1
        assert result[0]["rule_name"] == "sla_violation"
        assert result[0]["performance_stats"] == {"p95": 2500}
        assert result[0]["channels_sent"] == ["slack"]

    @pytest.mark.asyncio
    async def test_load_alerts_db_failure(self, repo, mock_pool):
        """load_alerts should return empty list on failure."""
        mock_pool.fetch.side_effect = Exception("timeout")
        result = await repo.load_alerts()
        assert result == []


class TestAcknowledgeAlertDB:
    """Tests for acknowledge_alert_db."""

    @pytest.mark.asyncio
    async def test_acknowledge_returns_result(self, repo, mock_pool):
        """acknowledge_alert_db should return acknowledgment details."""
        mock_pool.fetchrow.return_value = {
            "id": 42,
            "acknowledged": True,
            "acknowledged_at": 1000.0,
            "acknowledged_by": "admin@test.com",
        }
        result = await repo.acknowledge_alert_db(42, "admin@test.com")
        assert result["alert_id"] == 42
        assert result["acknowledged"] is True
        assert result["acknowledged_by"] == "admin@test.com"

    @pytest.mark.asyncio
    async def test_acknowledge_not_found(self, repo, mock_pool):
        """acknowledge_alert_db should return empty dict when alert not found."""
        mock_pool.fetchrow.return_value = None
        result = await repo.acknowledge_alert_db(999, "admin")
        assert result == {}

    @pytest.mark.asyncio
    async def test_acknowledge_db_failure(self, repo, mock_pool):
        """acknowledge_alert_db should return empty dict on DB failure."""
        mock_pool.fetchrow.side_effect = Exception("timeout")
        result = await repo.acknowledge_alert_db(1, "admin")
        assert result == {}


# ── Alert Rule Tests ──────────────────────────────────────────────────


class TestSaveAlertRule:
    """Tests for save_alert_rule."""

    @pytest.mark.asyncio
    async def test_save_alert_rule_upsert(self, repo, mock_pool):
        """save_alert_rule should execute an UPSERT (ON CONFLICT UPDATE)."""
        await repo.save_alert_rule(
            name="sla_violation",
            condition_config={"metric": "p95", "threshold": 2000},
            severity="critical",
            cooldown_seconds=300,
            channels=["email", "slack"],
            description="P95 latency exceeds SLA target",
        )

        mock_pool.execute.assert_awaited_once()
        call_args = mock_pool.execute.call_args
        sql = call_args[0][0]
        assert "INSERT INTO jorge_alert_rules" in sql
        assert "ON CONFLICT" in sql

    @pytest.mark.asyncio
    async def test_save_alert_rule_db_failure(self, repo, mock_pool):
        """save_alert_rule should not raise on failure."""
        mock_pool.execute.side_effect = Exception("connection refused")
        await repo.save_alert_rule("test", {}, "warning", 300, [])


class TestLoadAlertRules:
    """Tests for load_alert_rules."""

    @pytest.mark.asyncio
    async def test_load_alert_rules_returns_active(self, repo, mock_pool):
        """load_alert_rules should return only active rules."""
        mock_pool.fetch.return_value = [
            {
                "id": 1,
                "name": "sla_violation",
                "condition_config": json.dumps({"metric": "p95"}),
                "severity": "critical",
                "cooldown_seconds": 300,
                "channels": json.dumps(["email", "slack"]),
                "description": "P95 exceeds target",
                "active": True,
            }
        ]
        result = await repo.load_alert_rules()
        assert len(result) == 1
        assert result[0]["name"] == "sla_violation"
        assert result[0]["channels"] == ["email", "slack"]

    @pytest.mark.asyncio
    async def test_load_alert_rules_db_failure(self, repo, mock_pool):
        """load_alert_rules should return empty list on failure."""
        mock_pool.fetch.side_effect = Exception("timeout")
        result = await repo.load_alert_rules()
        assert result == []


class TestToggleAlertRule:
    """Tests for toggle_alert_rule."""

    @pytest.mark.asyncio
    async def test_toggle_rule_enable(self, repo, mock_pool):
        """toggle_alert_rule should UPDATE the active flag to True."""
        await repo.toggle_alert_rule("sla_violation", True)

        mock_pool.execute.assert_awaited_once()
        call_args = mock_pool.execute.call_args
        assert call_args[0][1] is True
        assert call_args[0][2] == "sla_violation"

    @pytest.mark.asyncio
    async def test_toggle_rule_disable(self, repo, mock_pool):
        """toggle_alert_rule should UPDATE the active flag to False."""
        await repo.toggle_alert_rule("sla_violation", False)

        call_args = mock_pool.execute.call_args
        assert call_args[0][1] is False

    @pytest.mark.asyncio
    async def test_toggle_rule_db_failure(self, repo, mock_pool):
        """toggle_alert_rule should not raise on failure."""
        mock_pool.execute.side_effect = Exception("timeout")
        await repo.toggle_alert_rule("test", True)


# ── Pool / Connection Tests ───────────────────────────────────────────


class TestPoolManagement:
    """Tests for lazy pool creation and cleanup."""

    @pytest.mark.asyncio
    async def test_close_pool(self, repo, mock_pool):
        """close() should close the connection pool."""
        await repo.close()
        mock_pool.close.assert_awaited_once()
        assert repo._pool is None

    @pytest.mark.asyncio
    async def test_close_when_no_pool(self):
        """close() should be safe when pool was never created."""
        repo = JorgeMetricsRepository(dsn="postgresql://test:test@localhost/test")
        await repo.close()  # Should not raise