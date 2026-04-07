"""Tests for PromptRegistry service.

Uses an in-memory SQLite database to avoid requiring a running Postgres
instance. The schema mirrors the Alembic migration but uses SQLite-compatible
types (TEXT for UUID, TEXT for JSONB).
"""

from __future__ import annotations

import json

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ghl_real_estate_ai.services.prompt_registry import PromptRegistry

_SCHEMA = """
CREATE TABLE prompt_versions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    model TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT NOT NULL DEFAULT '{}',
    CONSTRAINT uq_prompt_versions_name_version UNIQUE (name, version)
);

CREATE TABLE prompt_usage_log (
    id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL REFERENCES prompt_versions(id),
    request_id TEXT NOT NULL,
    response_quality REAL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        for stmt in _SCHEMA.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                await conn.execute(text(stmt))
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def registry(session_factory):
    return PromptRegistry(session_factory)


@pytest.mark.asyncio
async def test_register_creates_version_1(registry: PromptRegistry):
    pv = await registry.register(
        name="seller_system",
        content="You are Jorge's seller bot.",
        model="claude-sonnet-4-6",
    )
    assert pv.version == 1
    assert pv.name == "seller_system"
    assert pv.content == "You are Jorge's seller bot."
    assert pv.model == "claude-sonnet-4-6"
    assert pv.id  # UUID string


@pytest.mark.asyncio
async def test_register_increments_version(registry: PromptRegistry):
    await registry.register(name="lead_prompt", content="v1 content", model="claude-sonnet-4-6")
    pv2 = await registry.register(name="lead_prompt", content="v2 content", model="claude-sonnet-4-6")
    assert pv2.version == 2
    assert pv2.content == "v2 content"


@pytest.mark.asyncio
async def test_get_current_returns_latest(registry: PromptRegistry):
    await registry.register(name="buyer_prompt", content="old", model="claude-sonnet-4-6")
    await registry.register(name="buyer_prompt", content="new", model="claude-sonnet-4-6")
    current = await registry.get_current("buyer_prompt")
    assert current is not None
    assert current.version == 2
    assert current.content == "new"


@pytest.mark.asyncio
async def test_rollback_to_previous_version(registry: PromptRegistry):
    v1 = await registry.register(name="test_prompt", content="original", model="claude-sonnet-4-6")
    await registry.register(name="test_prompt", content="updated", model="claude-sonnet-4-6")

    rolled = await registry.rollback("test_prompt", to_version=1)
    assert rolled.version == 3  # rollback creates a new version
    assert rolled.content == "original"
    assert rolled.metadata.get("rolled_back_from") == 1

    current = await registry.get_current("test_prompt")
    assert current.version == 3
    assert current.content == "original"


@pytest.mark.asyncio
async def test_log_usage_records_request(registry: PromptRegistry, session_factory):
    pv = await registry.register(name="usage_test", content="content", model="claude-sonnet-4-6")
    await registry.log_usage(version_id=pv.id, request_id="req-123", response_quality=0.92)

    async with session_factory() as session:
        result = await session.execute(
            text("SELECT version_id, request_id, response_quality FROM prompt_usage_log WHERE request_id = :rid"),
            {"rid": "req-123"},
        )
        row = result.mappings().first()
        assert row is not None
        assert row["version_id"] == pv.id
        assert row["request_id"] == "req-123"
        assert abs(row["response_quality"] - 0.92) < 0.001


@pytest.mark.asyncio
async def test_get_current_nonexistent_returns_none(registry: PromptRegistry):
    result = await registry.get_current("does_not_exist")
    assert result is None
