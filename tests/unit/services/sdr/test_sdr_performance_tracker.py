"""Tests for SDRPerformanceTracker."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.services.sdr.performance_tracker import SDRPerformanceTracker

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.count_enrolled = AsyncMock(return_value=100)
    repo.count_touches_sent = AsyncMock(return_value=50)
    repo.count_replies = AsyncMock(return_value=10)
    repo.count_by_step = AsyncMock(return_value={"sms_1": 40, "email_1": 30, "qualified": 5, "booked": 2})
    repo.objection_distribution = AsyncMock(return_value={"timing": 3, "price": 2, "already_agent": 1})
    return repo


@pytest.mark.asyncio
async def test_get_stats_returns_sdr_stats_response(mock_repo):
    tracker = SDRPerformanceTracker(mock_repo)
    stats = await tracker.get_stats()
    assert stats.enrolled == 100
    assert stats.touches_sent == 50
    assert stats.replies_received == 10
    assert stats.qualified_leads == 5
    assert stats.appointments_booked == 2
    assert stats.objections_handled == 6
    assert stats.window == "30d"


@pytest.mark.asyncio
async def test_get_stats_reply_rate_calculation(mock_repo):
    mock_repo.count_touches_sent = AsyncMock(return_value=10)
    mock_repo.count_replies = AsyncMock(return_value=3)
    tracker = SDRPerformanceTracker(mock_repo)
    stats = await tracker.get_stats()
    assert stats.reply_rate == 0.3


@pytest.mark.asyncio
async def test_get_stats_zero_touches_no_division_error(mock_repo):
    mock_repo.count_touches_sent = AsyncMock(return_value=0)
    mock_repo.count_replies = AsyncMock(return_value=0)
    tracker = SDRPerformanceTracker(mock_repo)
    stats = await tracker.get_stats()
    assert stats.reply_rate == 0.0


@pytest.mark.asyncio
async def test_get_sequence_funnel_returns_ordered_steps(mock_repo):
    mock_repo.count_by_step = AsyncMock(return_value={})
    tracker = SDRPerformanceTracker(mock_repo)
    funnel = await tracker.get_sequence_funnel()
    steps = [item["step"] for item in funnel]
    assert steps[0] == "enrolled"
    assert steps[-1] == "opted_out"
    assert "sms_1" in steps
    assert "qualified" in steps
    assert len(steps) == 13


@pytest.mark.asyncio
async def test_get_objection_analytics_rates_sum_to_one(mock_repo):
    tracker = SDRPerformanceTracker(mock_repo)
    result = await tracker.get_objection_analytics()
    rates = result["rates"]
    assert result["total"] == 6
    assert abs(sum(rates.values()) - 1.0) < 0.01
