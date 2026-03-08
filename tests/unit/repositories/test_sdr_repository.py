"""Unit tests for SDRRepository using in-memory SQLite."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Pin a stable Fernet key so encrypt/decrypt round-trips succeed across refreshes.
os.environ.setdefault("SDR_FERNET_KEY", "thpo83actPznyyusxB0BOogCnJAr5-_TYPMAgxd8NDg=")

from ghl_real_estate_ai.models.base import Base
from ghl_real_estate_ai.models.sdr_models import (
    SDRObjectionLog,
    SDROutreachSequence,
    SDROutreachTouch,
    SDRProspect,
)
from ghl_real_estate_ai.repositories.sdr_repository import SDRRepository

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def session():
    """Yield an AsyncSession backed by an in-memory SQLite database."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as sess:
        yield sess

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def repo(session: AsyncSession) -> SDRRepository:
    return SDRRepository(session)


NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Prospect tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_prospect_creates_new(repo: SDRRepository, session: AsyncSession):
    p = await repo.upsert_prospect("c1", "loc1", "ghl_pipeline", "buyer", NOW)
    assert p.id is not None
    assert p.contact_id == "c1"
    assert p.location_id == "loc1"
    assert p.source == "ghl_pipeline"
    assert p.lead_type == "buyer"


@pytest.mark.asyncio
async def test_upsert_prospect_idempotent(repo: SDRRepository, session: AsyncSession):
    p1 = await repo.upsert_prospect("c1", "loc1", "ghl_pipeline", "buyer", NOW)
    p2 = await repo.upsert_prospect("c1", "loc1", "manual", "seller", NOW)
    assert p1.id == p2.id
    # Source updated on re-enroll
    assert p2.source == "manual"


@pytest.mark.asyncio
async def test_get_prospect_by_contact_returns_none_when_missing(repo: SDRRepository):
    result = await repo.get_prospect_by_contact("nonexistent", "loc1")
    assert result is None


@pytest.mark.asyncio
async def test_update_scores_sets_values(repo: SDRRepository, session: AsyncSession):
    p = await repo.upsert_prospect("c1", "loc1", "ghl_pipeline", enrolled_at=NOW)
    await repo.update_scores(p.id, frs_score=0.85, pcs_score=0.72)
    await session.refresh(p)
    assert p.frs_score == pytest.approx(0.85)
    assert p.pcs_score == pytest.approx(0.72)
    assert p.last_scored_at is not None


# ---------------------------------------------------------------------------
# Sequence tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_sequence_and_get_active(repo: SDRRepository, session: AsyncSession):
    p = await repo.upsert_prospect("c1", "loc1", "ghl_pipeline", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "intro_sms", enrolled_at=NOW)
    assert seq.id is not None
    assert seq.current_step == "intro_sms"

    active = await repo.get_active_sequence("c1", "loc1")
    assert active is not None
    assert active.id == seq.id


@pytest.mark.asyncio
async def test_get_active_sequence_returns_none_for_terminal_step(repo: SDRRepository, session: AsyncSession):
    p = await repo.upsert_prospect("c1", "loc1", "ghl_pipeline", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "qualified", enrolled_at=NOW)
    active = await repo.get_active_sequence("c1", "loc1")
    assert active is None


@pytest.mark.asyncio
async def test_update_sequence_step(repo: SDRRepository, session: AsyncSession):
    p = await repo.upsert_prospect("c1", "loc1", "ghl_pipeline", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "intro_sms", enrolled_at=NOW)
    next_touch = NOW + timedelta(hours=24)
    await repo.update_sequence_step(seq.id, "follow_up_1", next_touch_at=next_touch)
    await session.refresh(seq)
    assert seq.current_step == "follow_up_1"
    assert seq.next_touch_at is not None


@pytest.mark.asyncio
async def test_increment_reply_count(repo: SDRRepository, session: AsyncSession):
    p = await repo.upsert_prospect("c1", "loc1", "ghl_pipeline", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "intro_sms", enrolled_at=NOW)
    assert seq.reply_count == 0
    await repo.increment_reply_count(seq.id)
    await session.refresh(seq)
    assert seq.reply_count == 1


@pytest.mark.asyncio
async def test_get_due_sequences_filters_by_cutoff(repo: SDRRepository, session: AsyncSession):
    p = await repo.upsert_prospect("c1", "loc1", "ghl_pipeline", enrolled_at=NOW)
    past = NOW - timedelta(hours=1)
    future = NOW + timedelta(hours=24)

    seq_due = await repo.create_sequence(p.id, "c1", "loc1", "intro_sms", enrolled_at=NOW)
    await repo.update_sequence_step(seq_due.id, "intro_sms", next_touch_at=past)

    p2 = await repo.upsert_prospect("c2", "loc1", "ghl_pipeline", enrolled_at=NOW)
    seq_future = await repo.create_sequence(p2.id, "c2", "loc1", "intro_sms", enrolled_at=NOW)
    await repo.update_sequence_step(seq_future.id, "intro_sms", next_touch_at=future)

    due = await repo.get_due_sequences(cutoff=NOW)
    ids = [s.id for s in due]
    assert seq_due.id in ids
    assert seq_future.id not in ids


# ---------------------------------------------------------------------------
# Touch tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_touch_creates_row(repo: SDRRepository, session: AsyncSession):
    p = await repo.upsert_prospect("c1", "loc1", "ghl_pipeline", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "intro_sms", enrolled_at=NOW)
    touch = await repo.record_touch(seq.id, "c1", "intro_sms", "sms", "Hey there!")
    assert touch.id is not None
    assert touch.channel == "sms"
    assert touch.sent_at is not None


@pytest.mark.asyncio
async def test_record_reply_updates_touch(repo: SDRRepository, session: AsyncSession):
    p = await repo.upsert_prospect("c1", "loc1", "ghl_pipeline", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "intro_sms", enrolled_at=NOW)
    touch = await repo.record_touch(seq.id, "c1", "intro_sms", "sms")
    replied = NOW + timedelta(minutes=5)
    await repo.record_reply(touch.id, "Sounds good!", replied)
    await session.refresh(touch)
    assert touch.replied_at is not None
    assert touch.reply_body == "Sounds good!"


@pytest.mark.asyncio
async def test_get_touches_for_sequence(repo: SDRRepository, session: AsyncSession):
    p = await repo.upsert_prospect("c1", "loc1", "ghl_pipeline", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "intro_sms", enrolled_at=NOW)
    await repo.record_touch(seq.id, "c1", "intro_sms", "sms")
    await repo.record_touch(seq.id, "c1", "follow_up_1", "email")
    touches = await repo.get_touches_for_sequence(seq.id)
    assert len(touches) == 2


# ---------------------------------------------------------------------------
# Objection tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_log_objection_and_retrieve(repo: SDRRepository, session: AsyncSession):
    obj = await repo.log_objection("c1", "pricing", "Too expensive", "market_data_rebuttal")
    assert obj.id is not None
    assert obj.objection_type == "pricing"

    logs = await repo.get_objection_logs("c1")
    assert len(logs) == 1
    assert logs[0].id == obj.id


# ---------------------------------------------------------------------------
# Aggregation tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_enrolled_respects_since(repo: SDRRepository, session: AsyncSession):
    old = NOW - timedelta(days=30)
    recent = NOW - timedelta(hours=1)

    await repo.upsert_prospect("c_old", "loc1", "ghl_pipeline", enrolled_at=old)
    await repo.upsert_prospect("c_new", "loc1", "ghl_pipeline", enrolled_at=recent)

    since = NOW - timedelta(days=1)
    count = await repo.count_enrolled("loc1", since)
    assert count == 1  # only the recent one


@pytest.mark.asyncio
async def test_objection_distribution_aggregates_correctly(repo: SDRRepository, session: AsyncSession):
    await repo.log_objection("c1", "pricing", "Too expensive")
    await repo.log_objection("c2", "pricing", "Way too much")
    await repo.log_objection("c3", "timing", "Not now")

    since = NOW - timedelta(hours=1)
    dist = await repo.objection_distribution(None, since)
    assert dist.get("pricing", 0) == 2
    assert dist.get("timing", 0) == 1
