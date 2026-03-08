"""Unit tests for SDRAgent DB persistence wiring."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Pin Fernet key before model import
os.environ.setdefault(
    "SDR_FERNET_KEY", "thpo83actPznyyusxB0BOogCnJAr5-_TYPMAgxd8NDg="
)

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ghl_real_estate_ai.models.base import Base
from ghl_real_estate_ai.models.sdr_models import SDRProspect
from ghl_real_estate_ai.repositories.sdr_repository import SDRRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def repo(session: AsyncSession) -> SDRRepository:
    return SDRRepository(session)


def _mock_ghl_client() -> AsyncMock:
    client = AsyncMock()
    client.update_contact = AsyncMock()
    client.trigger_workflow = AsyncMock()
    return client


def _make_agent(ghl_client: Any, repo: SDRRepository) -> Any:
    """Create SDRAgent with mocked heavy dependencies."""
    from ghl_real_estate_ai.agents.sdr.sdr_agent import SDRAgent, SDRBotConfig

    with patch(
        "ghl_real_estate_ai.agents.intent_decoder.LeadIntentDecoder"
    ), patch(
        "ghl_real_estate_ai.agents.sdr.sdr_agent.QualificationGate"
    ) as MockGate:
        # Gate always fails by default (no handoff)
        gate_instance = MockGate.return_value
        gate_instance.evaluate.return_value = MagicMock(
            passed=False, handoff_target=None, frs_score=0.3, pcs_score=0.2,
            intent_profile=MagicMock(),
        )
        agent = SDRAgent(
            ghl_client=ghl_client,
            config=SDRBotConfig(handoff_enabled=True),
            repository=repo,
        )
    return agent


NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enroll_persists_prospect_and_sequence(repo: SDRRepository, session: AsyncSession):
    """run_prospecting_cycle should persist prospect + sequence to DB."""
    ghl = _mock_ghl_client()
    agent = _make_agent(ghl, repo)

    from ghl_real_estate_ai.services.sdr.prospect_sourcer import ProspectProfile, ProspectSource

    prospect = ProspectProfile(
        contact_id="c1",
        location_id="loc1",
        source=ProspectSource.GHL_PIPELINE,
        lead_type="buyer",
        property_address=None,
        days_in_stage=5,
        last_activity=None,
    )
    with patch.object(agent._sourcer, "fetch_prospects", return_value=[prospect]):
        result = await agent.run_prospecting_cycle("loc1")

    assert result.enrolled == 1

    db_prospect = await repo.get_prospect_by_contact("c1", "loc1")
    assert db_prospect is not None
    assert db_prospect.source == "ghl_pipeline"

    seq = await repo.get_active_sequence("c1", "loc1")
    assert seq is not None


@pytest.mark.asyncio
async def test_opt_out_persists_terminal_step(repo: SDRRepository, session: AsyncSession):
    """process_inbound_reply with 'stop texting' should set sequence to opted_out."""
    ghl = _mock_ghl_client()
    agent = _make_agent(ghl, repo)

    # Seed a prospect + sequence
    p = await repo.upsert_prospect("c1", "loc1", "manual", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "sms_1", enrolled_at=NOW)

    result = await agent.process_inbound_reply(
        contact_id="c1",
        message="stop texting me",
        channel="sms",
        location_id="loc1",
    )
    assert result.action_taken == "opt_out"

    await session.refresh(seq)
    assert seq.current_step == "opted_out"


@pytest.mark.asyncio
async def test_objection_persists_log(repo: SDRRepository, session: AsyncSession):
    """process_inbound_reply with an objection should log it to DB."""
    ghl = _mock_ghl_client()
    agent = _make_agent(ghl, repo)

    p = await repo.upsert_prospect("c1", "loc1", "manual", enrolled_at=NOW)
    await repo.create_sequence(p.id, "c1", "loc1", "sms_1", enrolled_at=NOW)

    result = await agent.process_inbound_reply(
        contact_id="c1",
        message="I already have an agent",
        channel="sms",
        location_id="loc1",
    )
    assert result.objection_type == "already_agent"

    logs = await repo.get_objection_logs("c1")
    assert len(logs) == 1
    assert logs[0].objection_type == "already_agent"


@pytest.mark.asyncio
async def test_engagement_reply_increments_count(repo: SDRRepository, session: AsyncSession):
    """Engagement reply should increment reply_count on the sequence."""
    ghl = _mock_ghl_client()
    agent = _make_agent(ghl, repo)

    p = await repo.upsert_prospect("c1", "loc1", "manual", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "sms_1", enrolled_at=NOW)
    # Add a touch so there's something to record the reply on
    await repo.record_touch(seq.id, "c1", "sms_1", "sms")

    # Verify repo can find the sequence before calling agent
    pre_seq = await repo.get_active_sequence("c1", "loc1")
    assert pre_seq is not None, "Sequence should be findable before agent call"
    assert agent._repo is repo, "Agent should use same repo"

    result = await agent.process_inbound_reply(
        contact_id="c1",
        message="Sounds great, I am definitely interested in buying soon",
        channel="sms",
        location_id="loc1",
    )
    assert result.action_taken == "sequence_advanced", f"Expected sequence_advanced, got {result.action_taken}"

    # Expire cached ORM state and re-query after Core UPDATE expression
    session.expire_all()
    updated_seq = await repo.get_active_sequence("c1", "loc1")
    assert updated_seq is not None
    assert updated_seq.reply_count >= 1


@pytest.mark.asyncio
async def test_handoff_persists_qualified_step(repo: SDRRepository, session: AsyncSession):
    """Successful handoff should set sequence to 'qualified' and update scores."""
    ghl = _mock_ghl_client()
    agent = _make_agent(ghl, repo)

    # Make gate pass
    agent._gate = MagicMock()
    agent._gate.evaluate.return_value = MagicMock(
        passed=True,
        handoff_target="buyer_bot",
        frs_score=0.9,
        pcs_score=0.8,
        intent_profile=MagicMock(),
    )

    p = await repo.upsert_prospect("c1", "loc1", "manual", enrolled_at=NOW)
    seq = await repo.create_sequence(p.id, "c1", "loc1", "sms_2", enrolled_at=NOW)
    await repo.record_touch(seq.id, "c1", "sms_2", "sms")

    with patch.object(agent, "_trigger_handoff", return_value=True):
        result = await agent.process_inbound_reply(
            contact_id="c1",
            message="I want to buy a house",
            channel="sms",
            location_id="loc1",
        )

    assert result.action_taken == "gate_passed"
    assert result.handoff_triggered is True

    await session.refresh(seq)
    assert seq.current_step == "qualified"

    await session.refresh(p)
    assert p.frs_score == pytest.approx(0.9)
    assert p.pcs_score == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_agent_works_without_repo():
    """SDRAgent should work with repository=None (backward compatible)."""
    ghl = _mock_ghl_client()
    agent = _make_agent.__wrapped__(ghl, None) if hasattr(_make_agent, '__wrapped__') else None

    from ghl_real_estate_ai.agents.sdr.sdr_agent import SDRAgent, SDRBotConfig

    with patch(
        "ghl_real_estate_ai.agents.intent_decoder.LeadIntentDecoder"
    ), patch(
        "ghl_real_estate_ai.agents.sdr.sdr_agent.QualificationGate"
    ):
        agent = SDRAgent(ghl_client=ghl, config=SDRBotConfig(), repository=None)

    assert agent._repo is None


@pytest.mark.asyncio
async def test_cadence_compute_next_touch_time_fast_replier():
    """Fast replier should get 25% reduction in delay."""
    from ghl_real_estate_ai.services.sdr.cadence_scheduler import CadenceScheduler

    base = 24.0  # hours
    result = CadenceScheduler.compute_next_touch_time(
        base_delay_hours=base,
        reply_count=0,
        last_reply_latency_minutes=10,  # fast
        now=NOW,
    )
    # 24 * 0.75 = 18 hours, clamped to [4, 72]
    expected_delta_hours = 18.0
    actual_delta = (result - NOW).total_seconds() / 3600
    assert actual_delta == pytest.approx(expected_delta_hours, abs=1.0)


@pytest.mark.asyncio
async def test_cadence_compute_avoids_sunday():
    """Next touch should skip Sunday."""
    from ghl_real_estate_ai.services.sdr.cadence_scheduler import CadenceScheduler

    # Pick a Saturday 6 PM UTC → +8h = Sunday 2 AM → should snap to Monday 9 AM
    saturday_evening = datetime(2026, 3, 7, 18, 0, 0, tzinfo=timezone.utc)  # Saturday
    result = CadenceScheduler.compute_next_touch_time(
        base_delay_hours=8.0,
        now=saturday_evening,
    )
    assert result.weekday() != 6  # not Sunday
    assert result.hour >= 9
