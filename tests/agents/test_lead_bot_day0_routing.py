import pytest
pytestmark = pytest.mark.unit

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch


@pytest.fixture
def mock_lead_bot_day0_deps():
    """Patch LeadBotWorkflow dependencies for deterministic day-0 routing tests."""
    mock_sync = MagicMock()
    mock_sync.record_lead_event = AsyncMock()

    ghost_engine = AsyncMock()
    ghost_engine.process_lead_step = AsyncMock(
        return_value={"content": "Thanks for reaching out. I can help with next steps today."}
    )

    event_publisher = MagicMock()
    event_publisher.publish_lead_bot_sequence_update = AsyncMock()

    sequence_service = AsyncMock()
    sequence_service.get_state = AsyncMock(return_value=None)
    sequence_service.save_state = AsyncMock(return_value=True)

    scheduler = AsyncMock()

    with (
        patch.multiple(
            "ghl_real_estate_ai.agents.lead_bot",
            LeadIntentDecoder=Mock,
            CMAGenerator=Mock,
            RetellClient=Mock,
            LyrioClient=Mock,
            get_ghost_followup_engine=Mock(return_value=ghost_engine),
            get_event_publisher=Mock(return_value=event_publisher),
            get_sequence_service=Mock(return_value=sequence_service),
            get_lead_scheduler=Mock(return_value=scheduler),
            sync_service=mock_sync,
        ),
        patch(
            "ghl_real_estate_ai.services.national_market_intelligence.get_national_market_intelligence",
            return_value=MagicMock(),
        ),
    ):
        yield {
            "ghost_engine": ghost_engine,
            "event_publisher": event_publisher,
            "sequence_service": sequence_service,
        }


def _intent_profile(price_category: str = "Neutral", classification: str = "Warm Lead", frs_score: float = 42.0):
    return SimpleNamespace(
        frs=SimpleNamespace(
            price=SimpleNamespace(category=price_category),
            classification=classification,
            total_score=frs_score,
        ),
        pcs=SimpleNamespace(total_score=35.0),
    )


@pytest.mark.asyncio
async def test_determine_path_routes_sequence_day_zero_to_day_0(mock_lead_bot_day0_deps):
    from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow

    bot = LeadBotWorkflow()
    state = {
        "lead_id": "lead_day0_route",
        "conversation_history": [{"role": "user", "content": "Hi there"}],
        "intent_profile": _intent_profile(),
        "sequence_day": 0,
        "sequence_state": {},
        "cma_generated": False,
    }

    result = await bot.determine_path(state)

    assert result["current_step"] == "day_0"
    assert result["engagement_status"] == "responsive"


@pytest.mark.asyncio
async def test_send_day0_advances_persisted_state_to_day3(mock_lead_bot_day0_deps):
    from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
    from ghl_real_estate_ai.services.lead_sequence_state_service import (
        LeadSequenceState,
        SequenceDay,
        SequenceStatus,
    )

    bot = LeadBotWorkflow()
    bot.ghl_client = AsyncMock()
    bot.ghl_client.send_message = AsyncMock(return_value={"status": "sent"})

    sequence_state = LeadSequenceState(
        lead_id="lead_day0_progress",
        current_day=SequenceDay.INITIAL,
        sequence_status=SequenceStatus.PENDING,
        sequence_started_at=datetime.now(timezone.utc),
        engagement_status="new",
    )
    mock_lead_bot_day0_deps["sequence_service"].get_state = AsyncMock(return_value=sequence_state)

    state = {
        "lead_id": "lead_day0_progress",
        "conversation_history": [],
        "intent_profile": _intent_profile(frs_score=58.0),
    }

    result = await bot.send_day_0_initial_contact(state)

    assert result["current_step"] == "day_3"
    assert result["engagement_status"] == "responsive"
    assert sequence_state.current_day == SequenceDay.DAY_3
    assert sequence_state.sequence_status == SequenceStatus.IN_PROGRESS
    mock_lead_bot_day0_deps["sequence_service"].save_state.assert_awaited_once_with(sequence_state)
    bot.ghl_client.send_message.assert_awaited_once()
    mock_lead_bot_day0_deps["event_publisher"].publish_lead_bot_sequence_update.assert_awaited_once()

