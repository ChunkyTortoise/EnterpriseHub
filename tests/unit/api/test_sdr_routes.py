"""Unit tests for SDR API routes with DB integration."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

# Pin Fernet key before model import
os.environ.setdefault(
    "SDR_FERNET_KEY", "thpo83actPznyyusxB0BOogCnJAr5-_TYPMAgxd8NDg="
)

from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ghl_real_estate_ai.models.base import Base
from ghl_real_estate_ai.repositories.sdr_repository import SDRRepository

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NOW = datetime.now(timezone.utc)


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(db_engine):
    factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess


@pytest_asyncio.fixture
async def app(db_engine):
    """Create a FastAPI app with the SDR router, overriding get_db to use test DB."""
    from ghl_real_estate_ai.database.session import get_db

    factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as sess:
            try:
                yield sess
                await sess.commit()
            except Exception:
                await sess.rollback()
                raise

    test_app = FastAPI()

    # Patch module-level service instances to avoid real GHL calls
    with patch("ghl_real_estate_ai.api.routes.sdr.EnhancedGHLClient"), \
         patch("ghl_real_estate_ai.api.routes.sdr._ghl_client"), \
         patch("ghl_real_estate_ai.api.routes.sdr._sequence_engine"), \
         patch("ghl_real_estate_ai.api.routes.sdr._scheduler"), \
         patch("ghl_real_estate_ai.api.routes.sdr._sdr_agent"):

        from ghl_real_estate_ai.api.routes.sdr import router
        test_app.include_router(router)
        test_app.dependency_overrides[get_db] = override_get_db
        yield test_app


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_prospect_returns_data(client: AsyncClient, session: AsyncSession):
    """GET /sdr/prospects/{contact_id} should return prospect data from DB."""
    repo = SDRRepository(session)
    p = await repo.upsert_prospect("c1", "loc1", "manual", "buyer", NOW)
    await repo.create_sequence(p.id, "c1", "loc1", "sms_1", enrolled_at=NOW)
    await session.commit()

    resp = await client.get("/sdr/prospects/c1", params={"location_id": "loc1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["contact_id"] == "c1"
    assert data["source"] == "manual"
    assert data["current_step"] == "sms_1"


@pytest.mark.asyncio
async def test_get_prospect_404_when_missing(client: AsyncClient):
    """GET /sdr/prospects/{contact_id} should 404 for unknown contacts."""
    resp = await client.get("/sdr/prospects/unknown", params={"location_id": "loc1"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_sequence_returns_touches(client: AsyncClient, session: AsyncSession):
    """GET /sdr/sequences/{contact_id} should return sequence + touch list."""
    repo = SDRRepository(session)
    p = await repo.upsert_prospect("c1", "loc1", "manual", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "sms_1", enrolled_at=NOW)
    await repo.record_touch(seq.id, "c1", "sms_1", "sms")
    await session.commit()

    resp = await client.get("/sdr/sequences/c1", params={"location_id": "loc1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_step"] == "sms_1"
    assert len(data["touches"]) == 1
    assert data["touches"][0]["channel"] == "sms"


@pytest.mark.asyncio
async def test_get_sequence_404_when_missing(client: AsyncClient):
    """GET /sdr/sequences/{contact_id} should 404 with no active sequence."""
    resp = await client.get("/sdr/sequences/unknown", params={"location_id": "loc1"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_process_batch_uses_db(client: AsyncClient, session: AsyncSession):
    """POST /sdr/sequences/process-batch should query DB for due sequences."""
    repo = SDRRepository(session)
    p = await repo.upsert_prospect("c1", "loc1", "manual", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "sms_1", enrolled_at=NOW)
    past = NOW - timedelta(hours=1)
    await repo.update_sequence_step(seq.id, "sms_1", next_touch_at=past)
    await session.commit()

    # Patch the sequence engine to avoid real GHL dispatch
    with patch("ghl_real_estate_ai.api.routes.sdr._sequence_engine") as mock_engine:
        mock_engine.advance_sequence = AsyncMock(return_value=AsyncMock(
            current_step="email_1",
        ))
        resp = await client.post("/sdr/sequences/process-batch", params={"batch_size": 10})

    assert resp.status_code == 200
    data = resp.json()
    assert "processed" in data
    assert "duration_ms" in data
