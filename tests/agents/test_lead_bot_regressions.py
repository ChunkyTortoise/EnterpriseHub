"""Targeted regressions for LeadBotWorkflow Jorge stabilization fixes."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow

pytestmark = pytest.mark.asyncio


def _build_minimal_lead_bot() -> LeadBotWorkflow:
    """Create a minimally configured LeadBotWorkflow instance for node-level tests."""
    bot = object.__new__(LeadBotWorkflow)

    bot.config = SimpleNamespace(
        jorge_handoff_enabled=True,
        enable_bot_intelligence=False,
        enable_behavioral_optimization=False,
        enable_predictive_analytics=False,
        enable_track3_intelligence=False,
    )
    bot.intelligence_middleware = None

    bot.event_publisher = MagicMock()
    bot.event_publisher.publish_bot_status_update = AsyncMock()
    bot.event_publisher.publish_lead_bot_sequence_update = AsyncMock()

    bot.ghost_engine = MagicMock()
    bot.ghost_engine.process_lead_step = AsyncMock(return_value={"content": "Follow-up message", "logic": "test"})

    bot.sequence_service = MagicMock()
    bot.sequence_service.mark_action_completed = AsyncMock()
    bot.sequence_service.advance_to_next_day = AsyncMock()
    bot.sequence_service.complete_sequence = AsyncMock()

    bot.scheduler = MagicMock()
    bot.scheduler.schedule_next_action = AsyncMock()

    bot.ghl_client = MagicMock()
    bot.ghl_client.send_message = AsyncMock()

    bot.retell_client = MagicMock()
    bot.retell_client.create_call = AsyncMock(return_value={"call_id": "retell_123"})

    bot.sendgrid_client = None

    return bot


def _lead_state_with_alias_only() -> dict:
    """State with lead_* fields only (no contact_* aliases)."""
    return {
        "lead_id": "lead_123",
        "lead_name": "Jordan Lead",
        "conversation_history": [{"role": "user", "content": "Checking in"}],
        "intent_profile": SimpleNamespace(frs=SimpleNamespace(total_score=68)),
        "lead_phone": "+15555550123",
        "lead_email": "lead@example.com",
        "property_address": "123 Main St",
    }


async def test_check_handoff_signals_records_event_without_name_error():
    """Regression: check_handoff_signals should not raise NameError and must record handoff event."""
    bot = _build_minimal_lead_bot()

    mock_sync_service = MagicMock()
    mock_sync_service.record_lead_event = AsyncMock()

    with patch(
        "ghl_real_estate_ai.services.jorge.jorge_handoff_service.JorgeHandoffService.extract_intent_signals",
        return_value={"buyer_intent_score": 0.91, "seller_intent_score": 0.04},
    ), patch("ghl_real_estate_ai.agents.lead_bot.sync_service", new=mock_sync_service):
        result = await LeadBotWorkflow.check_handoff_signals(
            bot,
            {"lead_id": "lead_123", "user_message": "I am pre-approved and ready to buy now"},
        )

    assert result["handoff_required"] is True
    assert result["handoff_target"] == "buyer-bot"
    bot.event_publisher.publish_bot_status_update.assert_awaited_once()
    mock_sync_service.record_lead_event.assert_awaited_once()


async def test_sequence_day_nodes_accept_lead_phone_email_aliases_only():
    """Regression: Day 3/7/14/30 nodes should work when only lead_* keys are present."""
    bot = _build_minimal_lead_bot()
    state = _lead_state_with_alias_only()

    day3 = await LeadBotWorkflow.send_day_3_sms(bot, state)
    assert day3["current_step"] == "day_7_call"

    day7 = await LeadBotWorkflow.initiate_day_7_call(bot, state)
    await asyncio.sleep(0)
    assert day7["current_step"] == "day_14_email"
    assert bot.retell_client.create_call.await_args.kwargs["to_number"] == state["lead_phone"]

    day14 = await LeadBotWorkflow.send_day_14_email(bot, state)
    assert day14["current_step"] == "day_30_nudge"

    day30 = await LeadBotWorkflow.send_day_30_nudge(bot, state)
    assert day30["current_step"] == "nurture"


async def test_enhanced_graph_includes_handoff_check_and_short_circuit_edge():
    """Regression: enhanced graph should include handoff node and short-circuit route to END."""
    bot = object.__new__(LeadBotWorkflow)
    bot.config = SimpleNamespace(
        enable_bot_intelligence=False,
        enable_behavioral_optimization=False,
        enable_predictive_analytics=False,
        enable_track3_intelligence=False,
    )
    bot.intelligence_middleware = None

    compiled_graph = LeadBotWorkflow._build_enhanced_graph(bot)
    graph = compiled_graph.get_graph()

    assert "check_handoff_signals" in graph.nodes

    edges = {(edge.source, edge.target) for edge in graph.edges}
    assert ("analyze_intent", "check_handoff_signals") in edges
    assert ("check_handoff_signals", "__end__") in edges
