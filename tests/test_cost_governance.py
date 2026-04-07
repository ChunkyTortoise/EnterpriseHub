"""Tests for CostTracker service.

Uses an in-memory SQLite database to avoid requiring Postgres.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ghl_real_estate_ai.services.cost_governance import CostTracker, calculate_cost

_SCHEMA = """
CREATE TABLE cost_records (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    prompt_version TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.execute(text(_SCHEMA))
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def tracker(session_factory):
    return CostTracker(session_factory)


@pytest.mark.asyncio
async def test_record_stores_cost(tracker: CostTracker, session_factory):
    rec = await tracker.record(
        request_id="req-001",
        agent_name="seller_bot",
        model="claude-sonnet-4-6",
        input_tokens=1000,
        output_tokens=200,
    )
    assert rec.request_id == "req-001"
    assert rec.agent_name == "seller_bot"
    assert rec.cost_usd > 0

    # Verify persisted
    async with session_factory() as session:
        result = await session.execute(
            text("SELECT cost_usd FROM cost_records WHERE request_id = :rid"),
            {"rid": "req-001"},
        )
        row = result.mappings().first()
        assert row is not None
        assert abs(row["cost_usd"] - rec.cost_usd) < 0.0001


@pytest.mark.asyncio
async def test_cost_calculation_haiku():
    # 1M input + 1M output for haiku: $0.80 + $4.00 = $4.80
    cost = calculate_cost("claude-3-5-haiku-20251022", 1_000_000, 1_000_000)
    assert abs(cost - 4.80) < 0.001


@pytest.mark.asyncio
async def test_cost_calculation_sonnet():
    # 1M input + 1M output for sonnet: $3.00 + $15.00 = $18.00
    cost = calculate_cost("claude-sonnet-4-6", 1_000_000, 1_000_000)
    assert abs(cost - 18.00) < 0.001


@pytest.mark.asyncio
async def test_get_summary_by_agent(tracker: CostTracker):
    await tracker.record("r1", "seller_bot", "claude-sonnet-4-6", 500, 100)
    await tracker.record("r2", "seller_bot", "claude-sonnet-4-6", 600, 150)
    await tracker.record("r3", "buyer_bot", "claude-3-5-haiku-20251022", 1000, 200)

    summary = await tracker.get_summary("24h")
    assert summary["total_cost"] > 0
    assert "seller_bot" in summary["by_agent"]
    assert "buyer_bot" in summary["by_agent"]
    assert summary["by_agent"]["seller_bot"]["requests"] == 2
    assert summary["by_agent"]["buyer_bot"]["requests"] == 1
    assert summary["emergency_status"] == "normal"
    assert summary["per_lead_avg"] > 0


@pytest.mark.asyncio
async def test_get_summary_empty_period(tracker: CostTracker):
    summary = await tracker.get_summary("24h")
    assert summary["total_cost"] == 0
    assert summary["by_agent"] == {}
    assert summary["by_model"] == {}
    assert summary["per_lead_avg"] == 0.0
    assert summary["emergency_status"] == "normal"
