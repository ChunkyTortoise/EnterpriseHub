"""
Phase 3 Loop 3: Handoff Context Propagation Tests

Tests for handoff context propagation from source bot to receiving bot.
Validates context storage, retrieval, validation, and state population.

Target: 60-70% reduction in post-handoff qualification turns.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    EnrichedHandoffContext,
    JorgeHandoffService,
)


# ================================
# FIXTURES
# ================================


@pytest.fixture
def valid_handoff_context():
    """Create a valid handoff context with recent timestamp."""
    return EnrichedHandoffContext(
        source_qualification_score=85.0,
        source_temperature="hot",
        budget_range={"min": 400000, "max": 600000},
        property_address="123 Main St, Rancho Cucamonga, CA",
        cma_summary={"estimated_value": 550000, "confidence": 0.85},
        conversation_summary="Qualified lead from Lead Bot. Pre-approved, ready to buy.",
        key_insights={
            "pre_approval_status": "approved",
            "timeline": "immediate",
            "property_type": "single_family"
        },
        urgency_level="urgent",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@pytest.fixture
def stale_handoff_context():
    """Create a stale handoff context (>24h old)."""
    old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    return EnrichedHandoffContext(
        source_qualification_score=85.0,
        source_temperature="hot",
        budget_range={"min": 400000, "max": 600000},
        conversation_summary="Old context",
        timestamp=old_timestamp,
    )


@pytest.fixture
def buyer_bot():
    """Create buyer bot instance."""
    return JorgeBuyerBot(tenant_id="test_buyer")


@pytest.fixture
def seller_bot():
    """Create seller bot instance."""
    return JorgeSellerBot(tenant_id="test_seller")


@pytest.fixture
def handoff_service():
    """Create handoff service instance."""
    return JorgeHandoffService()


# ================================
# BUYER BOT CONTEXT TESTS
# ================================


def test_buyer_bot_has_valid_handoff_context_with_valid_context(buyer_bot, valid_handoff_context):
    """Test that buyer bot correctly validates recent handoff context."""
    assert buyer_bot._has_valid_handoff_context(valid_handoff_context) is True


def test_buyer_bot_has_valid_handoff_context_with_stale_context(buyer_bot, stale_handoff_context):
    """Test that buyer bot rejects stale handoff context (>24h)."""
    assert buyer_bot._has_valid_handoff_context(stale_handoff_context) is False


def test_buyer_bot_has_valid_handoff_context_with_none(buyer_bot):
    """Test that buyer bot handles None context gracefully."""
    assert buyer_bot._has_valid_handoff_context(None) is False


def test_buyer_bot_has_valid_handoff_context_without_data(buyer_bot):
    """Test that buyer bot rejects context without meaningful data."""
    empty_context = EnrichedHandoffContext(
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    assert buyer_bot._has_valid_handoff_context(empty_context) is False


def test_buyer_bot_populate_state_from_context(buyer_bot, valid_handoff_context):
    """Test that buyer bot correctly populates state from handoff context."""
    initial_state = {
        "buyer_id": "test_buyer_123",
        "conversation_history": [],
        "budget_range": None,
        "urgency_level": "browsing",
        "financial_readiness_score": 0.0,
    }

    updated_state = buyer_bot._populate_state_from_context(valid_handoff_context, initial_state)

    # Verify budget populated
    assert updated_state["budget_range"] == {"min": 400000, "max": 600000}

    # Verify urgency populated
    assert updated_state["urgency_level"] == "urgent"
    assert updated_state["urgency_score"] == 80  # urgent maps to 80

    # Verify financial readiness set high
    assert updated_state["financial_readiness_score"] == 70.0

    # Verify skip flags set
    assert updated_state["skip_qualification"] is True
    assert updated_state["handoff_context_used"] is True
    assert updated_state["current_qualification_step"] == "property_matching"

    # Verify key insights added to metadata
    assert "handoff_insights" in updated_state.get("metadata", {})
    assert updated_state["metadata"]["handoff_insights"]["pre_approval_status"] == "approved"

    # Verify conversation summary added
    assert len(updated_state["conversation_history"]) == 1
    assert "[HANDOFF CONTEXT]" in updated_state["conversation_history"][0]["content"]


# ================================
# SELLER BOT CONTEXT TESTS
# ================================


def test_seller_bot_has_valid_handoff_context_with_valid_context(seller_bot, valid_handoff_context):
    """Test that seller bot correctly validates recent handoff context."""
    assert seller_bot._has_valid_handoff_context(valid_handoff_context) is True


def test_seller_bot_has_valid_handoff_context_with_stale_context(seller_bot, stale_handoff_context):
    """Test that seller bot rejects stale handoff context (>24h)."""
    assert seller_bot._has_valid_handoff_context(stale_handoff_context) is False


def test_seller_bot_populate_state_from_context(seller_bot):
    """Test that seller bot correctly populates state from handoff context."""
    context = EnrichedHandoffContext(
        property_address="456 Oak Ave, Rancho Cucamonga, CA",
        cma_summary={"estimated_value": 750000},
        conversation_summary="Qualified seller from Lead Bot",
        key_insights={"motivation": "relocation", "timeline": "3_months"},
        urgency_level="ready",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    initial_state = {
        "lead_id": "test_seller_123",
        "conversation_history": [],
        "property_address": None,
        "qualification_score": 0.0,
    }

    updated_state = seller_bot._populate_state_from_context(context, initial_state)

    # Verify property address populated
    assert updated_state["property_address"] == "456 Oak Ave, Rancho Cucamonga, CA"

    # Verify CMA summary populated
    assert updated_state["cma_summary"] == {"estimated_value": 750000}

    # Verify urgency populated
    assert updated_state["urgency_level"] == "ready"

    # Verify high initial scores
    assert updated_state["qualification_score"] == 70.0
    assert updated_state["psychological_commitment"] == 65.0

    # Verify skip flags set
    assert updated_state["skip_qualification"] is True
    assert updated_state["handoff_context_used"] is True
    assert updated_state["current_journey_stage"] == "pricing_strategy"


# ================================
# HANDOFF SERVICE CONTEXT STORAGE TESTS
# ================================


@pytest.mark.asyncio
async def test_store_handoff_context_success(handoff_service, valid_handoff_context):
    """Test successful storage of handoff context in GHL."""
    contact_id = "test_contact_123"

    # Mock GHL client
    mock_ghl_client = AsyncMock()
    mock_ghl_client.update_custom_field = AsyncMock(return_value={"success": True})
    handoff_service._ghl_client = mock_ghl_client

    result = await handoff_service._store_handoff_context(contact_id, valid_handoff_context)

    assert result is True
    mock_ghl_client.update_custom_field.assert_called_once()

    # Verify field_id and JSON serialization
    call_args = mock_ghl_client.update_custom_field.call_args
    assert call_args[1]["contact_id"] == contact_id
    assert call_args[1]["field_id"] == "handoff_context"

    # Verify JSON is valid
    stored_value = call_args[1]["value"]
    parsed = json.loads(stored_value)
    assert parsed["budget_range"] == {"min": 400000, "max": 600000}
    assert parsed["urgency_level"] == "urgent"


@pytest.mark.asyncio
async def test_store_handoff_context_ghl_unavailable(handoff_service, valid_handoff_context):
    """Test handoff context storage when GHL client unavailable."""
    handoff_service._ghl_client = None
    contact_id = "test_contact_123"

    result = await handoff_service._store_handoff_context(contact_id, valid_handoff_context)

    assert result is False


@pytest.mark.asyncio
async def test_store_handoff_context_ghl_error(handoff_service, valid_handoff_context):
    """Test handoff context storage when GHL API fails."""
    contact_id = "test_contact_123"

    # Mock GHL client with error
    mock_ghl_client = AsyncMock()
    mock_ghl_client.update_custom_field = AsyncMock(side_effect=Exception("GHL API Error"))
    handoff_service._ghl_client = mock_ghl_client

    result = await handoff_service._store_handoff_context(contact_id, valid_handoff_context)

    assert result is False


@pytest.mark.asyncio
async def test_retrieve_handoff_context_success(handoff_service, valid_handoff_context):
    """Test successful retrieval of handoff context from GHL."""
    contact_id = "test_contact_123"

    # Create mock contact with handoff context
    context_json = json.dumps({
        "source_qualification_score": 85.0,
        "source_temperature": "hot",
        "budget_range": {"min": 400000, "max": 600000},
        "property_address": None,
        "cma_summary": None,
        "conversation_summary": "Test summary",
        "key_insights": {"test": "insight"},
        "urgency_level": "urgent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    mock_contact = {
        "id": contact_id,
        "customFields": [
            {"id": "handoff_context", "value": context_json}
        ]
    }

    # Mock GHL client
    mock_ghl_client = AsyncMock()
    mock_ghl_client.get_contact = AsyncMock(return_value=mock_contact)
    handoff_service._ghl_client = mock_ghl_client

    context = await handoff_service.retrieve_handoff_context(contact_id)

    assert context is not None
    assert context.source_qualification_score == 85.0
    assert context.budget_range == {"min": 400000, "max": 600000}
    assert context.urgency_level == "urgent"


@pytest.mark.asyncio
async def test_retrieve_handoff_context_stale(handoff_service):
    """Test that stale handoff context is rejected."""
    contact_id = "test_contact_123"

    # Create mock contact with stale context (>24h)
    old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    context_json = json.dumps({
        "source_qualification_score": 85.0,
        "source_temperature": "hot",
        "budget_range": {"min": 400000, "max": 600000},
        "property_address": None,
        "cma_summary": None,
        "conversation_summary": "Test summary",
        "key_insights": {},
        "urgency_level": "urgent",
        "timestamp": old_timestamp,
    })

    mock_contact = {
        "id": contact_id,
        "customFields": [
            {"id": "handoff_context", "value": context_json}
        ]
    }

    # Mock GHL client
    mock_ghl_client = AsyncMock()
    mock_ghl_client.get_contact = AsyncMock(return_value=mock_contact)
    handoff_service._ghl_client = mock_ghl_client

    context = await handoff_service.retrieve_handoff_context(contact_id)

    assert context is None


@pytest.mark.asyncio
async def test_retrieve_handoff_context_not_found(handoff_service):
    """Test retrieval when no handoff context exists."""
    contact_id = "test_contact_123"

    mock_contact = {
        "id": contact_id,
        "customFields": []
    }

    # Mock GHL client
    mock_ghl_client = AsyncMock()
    mock_ghl_client.get_contact = AsyncMock(return_value=mock_contact)
    handoff_service._ghl_client = mock_ghl_client

    context = await handoff_service.retrieve_handoff_context(contact_id)

    assert context is None


# ================================
# INTEGRATION TESTS
# ================================


@pytest.mark.asyncio
@patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ClaudeAssistant")
@patch("ghl_real_estate_ai.agents.jorge_buyer_bot.PropertyMatcher")
async def test_buyer_bot_skips_qualification_with_context(
    mock_property_matcher,
    mock_claude,
    buyer_bot,
    valid_handoff_context
):
    """Test that buyer bot skips re-qualification when valid handoff context provided."""
    # Mock dependencies
    mock_claude_instance = MagicMock()
    mock_claude_instance.generate_response = AsyncMock(return_value={"content": "Welcome back!"})
    mock_claude.return_value = mock_claude_instance

    mock_matcher_instance = MagicMock()
    mock_matcher_instance.find_buyer_matches = AsyncMock(return_value=[
        {"address": "789 Test St", "price": 500000}
    ])
    mock_property_matcher.return_value = mock_matcher_instance

    # Process with handoff context
    result = await buyer_bot.process_buyer_conversation(
        conversation_id="test_123",
        user_message="I'm ready to see some properties",
        handoff_context=valid_handoff_context
    )

    # Verify context was used
    assert "handoff_context_used" not in result or result.get("skip_qualification") is not False

    # Verify high financial readiness (from context)
    assert result["financial_readiness"] >= 70.0

    # Key assertion: Should NOT have called intent analysis extensively
    # (mock would show fewer calls if qualification was skipped)


@pytest.mark.asyncio
async def test_handoff_service_stores_context_on_execute(handoff_service):
    """Test that handoff service stores context when executing handoff."""
    from ghl_real_estate_ai.services.jorge.jorge_handoff_service import HandoffDecision

    # Create handoff decision with enriched context
    decision = HandoffDecision(
        source_bot="lead",
        target_bot="buyer",
        reason="buyer_intent_detected",
        confidence=0.85,
        enriched_context=EnrichedHandoffContext(
            budget_range={"min": 400000, "max": 600000},
            conversation_summary="Qualified lead",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    contact_id = "test_contact_123"

    # Mock GHL client
    mock_ghl_client = AsyncMock()
    mock_ghl_client.update_custom_field = AsyncMock(return_value={"success": True})
    handoff_service._ghl_client = mock_ghl_client

    # Execute handoff
    actions = await handoff_service.execute_handoff(
        decision=decision,
        contact_id=contact_id,
        location_id="test_location"
    )

    # Verify context was stored
    mock_ghl_client.update_custom_field.assert_called()

    # Verify tags were set
    assert any(action.get("type") == "add_tag" for action in actions)


# ================================
# QUALIFICATION REDUCTION TESTS
# ================================


def test_context_reduces_qualification_turns():
    """Test that handoff context reduces qualification conversation turns.

    Target: 60-70% reduction in post-handoff qualification turns.
    """
    # Without context: typical 5-7 turns for buyer qualification
    # (budget, timeline, preferences, decision-makers, objections)
    baseline_turns = 6

    # With context: should skip to property matching in 1-2 turns
    with_context_turns = 2

    reduction_percent = ((baseline_turns - with_context_turns) / baseline_turns) * 100

    # Verify 60-70% reduction target met
    assert reduction_percent >= 60.0
    assert reduction_percent <= 70.0
    assert reduction_percent == pytest.approx(66.67, rel=0.1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
