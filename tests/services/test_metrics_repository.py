import pytest

pytestmark = pytest.mark.integration

"""Tests for JorgeMetricsRepository.

Validates all CRUD methods with mocked asyncpg pool to ensure correct
SQL queries and error handling without requiring a live database.
"""

import json
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.repositories.jorge_metrics_repository import (
    JorgeMetricsRepository,
)


@pytest.fixture
def mock_pool():
    """Create a mock asyncpg pool."""
    pool = AsyncMock()
    return pool


@pytest.fixture
def repo(mock_pool):
    """Create a repository with a pre-injected mock pool."""
    r = JorgeMetricsRepository(dsn="postgresql://test:test@localhost/test")
    r._pool = mock_pool
    return r


# ── save_interaction ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_interaction_calls_execute(repo, mock_pool):
    await repo.save_interaction("lead", 450.0, True, True, 1000.0)
    mock_pool.execute.assert_awaited_once()
    args = mock_pool.execute.call_args
    assert "jorge_bot_interactions" in args[0][0]
    assert args[0][1] == "lead"
    assert args[0][2] == 450.0
    assert args[0][3] is True
    assert args[0][4] is True
    assert args[0][5] == 1000.0


@pytest.mark.asyncio
async def test_save_interaction_with_metadata(repo, mock_pool):
    meta = {"source": "test"}
    await repo.save_interaction("buyer", 200.0, False, False, 1000.0, metadata=meta)
    args = mock_pool.execute.call_args
    assert json.loads(args[0][6]) == meta


@pytest.mark.asyncio
async def test_save_interaction_db_failure_logs_warning(repo, mock_pool, caplog):
    mock_pool.execute.side_effect = Exception("connection lost")
    await repo.save_interaction("lead", 100.0, True, False, 1000.0)
    assert "Failed to save interaction" in caplog.text


# ── load_interactions ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_interactions_returns_dicts(repo, mock_pool):
    mock_pool.fetch.return_value = [
        {
            "bot_type": "lead",
            "duration_ms": 300.0,
            "success": True,
            "cache_hit": False,
            "timestamp": 1000.0,
            "metadata": None,
        }
    ]
    result = await repo.load_interactions(900.0)
    assert len(result) == 1
    assert result[0]["bot_type"] == "lead"
    assert result[0]["duration_ms"] == 300.0


@pytest.mark.asyncio
async def test_load_interactions_db_failure_returns_empty(repo, mock_pool):
    mock_pool.fetch.side_effect = Exception("timeout")
    result = await repo.load_interactions(0.0)
    assert result == []


# ── save_handoff ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_handoff_calls_execute(repo, mock_pool):
    await repo.save_handoff("lead", "buyer", True, 120.0, 1000.0)
    mock_pool.execute.assert_awaited_once()
    args = mock_pool.execute.call_args
    assert "jorge_handoff_events" in args[0][0]
    assert args[0][1] == "lead"
    assert args[0][2] == "buyer"


# ── load_handoffs ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_handoffs_returns_dicts(repo, mock_pool):
    mock_pool.fetch.return_value = [
        {
            "source_bot": "lead",
            "target_bot": "buyer",
            "success": True,
            "duration_ms": 120.0,
            "timestamp": 1000.0,
        }
    ]
    result = await repo.load_handoffs(900.0)
    assert len(result) == 1
    assert result[0]["source"] == "lead"
    assert result[0]["target"] == "buyer"


# ── save_alert ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_alert_calls_execute(repo, mock_pool):
    await repo.save_alert(
        rule_name="high_error_rate",
        severity="critical",
        message="Error rate 6%",
        triggered_at=1000.0,
        performance_stats={"error_rate": 0.06},
        channels_sent=["email"],
    )
    mock_pool.execute.assert_awaited_once()
    args = mock_pool.execute.call_args
    assert "jorge_alerts" in args[0][0]


# ── load_alerts ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_alerts_returns_dicts(repo, mock_pool):
    mock_pool.fetch.return_value = [
        {
            "id": 1,
            "rule_name": "sla_violation",
            "severity": "critical",
            "message": "test",
            "triggered_at": 1000.0,
            "performance_stats": None,
            "channels_sent": None,
            "acknowledged": False,
            "acknowledged_at": None,
            "acknowledged_by": None,
        }
    ]
    result = await repo.load_alerts(limit=10)
    assert len(result) == 1
    assert result[0]["rule_name"] == "sla_violation"


# ── acknowledge_alert_db ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_acknowledge_alert_db_success(repo, mock_pool):
    mock_pool.fetchrow.return_value = {
        "id": 42,
        "acknowledged": True,
        "acknowledged_at": 1001.0,
        "acknowledged_by": "admin",
    }
    result = await repo.acknowledge_alert_db(42, "admin")
    assert result["alert_id"] == 42
    assert result["acknowledged"] is True


@pytest.mark.asyncio
async def test_acknowledge_alert_db_not_found(repo, mock_pool):
    mock_pool.fetchrow.return_value = None
    result = await repo.acknowledge_alert_db(999, "admin")
    assert result == {}


# ── save_handoff_outcome ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_handoff_outcome_calls_execute(repo, mock_pool):
    await repo.save_handoff_outcome(
        contact_id="c001",
        source_bot="lead",
        target_bot="buyer",
        outcome="successful",
        timestamp=1000.0,
        metadata={"seeded": True},
    )
    mock_pool.execute.assert_awaited_once()
    args = mock_pool.execute.call_args
    assert "jorge_handoff_outcomes" in args[0][0]
    assert args[0][1] == "c001"
    assert args[0][4] == "successful"


@pytest.mark.asyncio
async def test_save_handoff_outcome_db_failure(repo, mock_pool, caplog):
    mock_pool.execute.side_effect = Exception("disk full")
    await repo.save_handoff_outcome("c001", "lead", "buyer", "failed", 1000.0)
    assert "Failed to save handoff outcome" in caplog.text


# ── load_handoff_outcomes ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_handoff_outcomes_no_filters(repo, mock_pool):
    mock_pool.fetch.return_value = [
        {
            "contact_id": "c001",
            "source_bot": "lead",
            "target_bot": "buyer",
            "outcome": "successful",
            "timestamp": 1000.0,
            "metadata": None,
        }
    ]
    result = await repo.load_handoff_outcomes(900.0)
    assert len(result) == 1
    assert result[0]["contact_id"] == "c001"


@pytest.mark.asyncio
async def test_load_handoff_outcomes_with_filters(repo, mock_pool):
    mock_pool.fetch.return_value = []
    result = await repo.load_handoff_outcomes(900.0, source_bot="lead", target_bot="buyer")
    assert result == []
    call_args = mock_pool.fetch.call_args
    sql = call_args[0][0]
    assert "source_bot" in sql
    assert "target_bot" in sql


@pytest.mark.asyncio
async def test_load_handoff_outcomes_db_failure(repo, mock_pool):
    mock_pool.fetch.side_effect = Exception("timeout")
    result = await repo.load_handoff_outcomes(0.0)
    assert result == []


# ── Pool creation ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_pool_lazy_creation():
    repo = JorgeMetricsRepository(dsn="postgresql://test:test@localhost/test")
    assert repo._pool is None
    mock_asyncpg = MagicMock()
    mock_asyncpg.create_pool = AsyncMock(return_value=MagicMock())
    with patch.dict("sys.modules", {"asyncpg": mock_asyncpg}):
        pool = await repo._get_pool()
        assert pool is not None
        mock_asyncpg.create_pool.assert_awaited_once()


# ── close ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_close_pool(repo, mock_pool):
    await repo.close()
    mock_pool.close.assert_awaited_once()
    assert repo._pool is None