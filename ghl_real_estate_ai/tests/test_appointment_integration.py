"""
Tests for Appointment Scheduling Integration (Phase 2)
"""

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set dummy env vars
os.environ["ANTHROPIC_API_KEY"] = "sk-test-key"
os.environ["GHL_API_KEY"] = "ghl-test-key"
os.environ["GHL_LOCATION_ID"] = "loc-test-123"

from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.services.ghl_client import GHLClient



async def test_slot_fetching_for_hot_lead():
    """Test that available slots are fetched when lead score is high."""
    cm = ConversationManager()

    # Mock LLM and RAG
    cm.llm_client.agenerate = AsyncMock(return_value=MagicMock(content="I can book that for you."))
    cm.rag_engine.search = MagicMock(return_value=[])

    # Mock GHL Client
    mock_ghl = AsyncMock(spec=GHLClient)
    mock_ghl.get_available_slots.return_value = [
        {"start_time": "2026-01-05T10:00:00Z"},
        {"start_time": "2026-01-05T14:00:00Z"},
    ]

    # Hot lead context (high score)
    context = {
        "conversation_history": [
            {"role": "user", "content": "I want to buy a house"},
            {"role": "assistant", "content": "Great, what is your budget?"},
            {"role": "user", "content": "400k"},
            {"role": "assistant", "content": "And where?"},
            {"role": "user", "content": "Austin"},
        ],
        "extracted_preferences": {"budget": 400000, "location": "Austin", "timeline": "ASAP"},
        "created_at": datetime.utcnow().isoformat(),
    }

    # Generate response
    response = await cm.generate_response(
        user_message="I'm ready to talk to someone.",
        contact_info={"first_name": "Test", "id": "contact_123"},
        context=context,
        ghl_client=mock_ghl,
        tenant_config={"ghl_calendar_id": "cal_123"},
    )

    # Verify get_available_slots was called
    mock_ghl.get_available_slots.assert_called_once()
    assert "10:00 AM" in cm.llm_client.agenerate.call_args.kwargs["system_prompt"]


async def test_appointment_booking_on_slot_selection():
    """Test that an appointment is created when a slot is selected."""
    cm = ConversationManager()

    # Mock extraction to simulate slot selection
    cm.extract_data = AsyncMock(return_value={"selected_slot": "Monday at 10am"})

    # Mock LLM and RAG
    cm.llm_client.agenerate = AsyncMock(return_value=MagicMock(content="Confirmed for Monday!"))
    cm.rag_engine.search = MagicMock(return_value=[])

    # Mock GHL Client
    mock_ghl = AsyncMock(spec=GHLClient)
    mock_ghl.get_available_slots.return_value = [{"start_time": "2026-01-05T10:00:00Z"}]
    mock_ghl.create_appointment = AsyncMock(return_value={"id": "apt_123"})

    context = {"conversation_history": [], "extracted_preferences": {}, "created_at": datetime.utcnow().isoformat()}

    # Generate response
    await cm.generate_response(
        user_message="Monday at 10am works for me.",
        contact_info={"first_name": "Test", "id": "contact_123"},
        context=context,
        ghl_client=mock_ghl,
        tenant_config={"ghl_calendar_id": "cal_123"},
    )

    # Verify create_appointment was called
    mock_ghl.create_appointment.assert_called_once_with(
        contact_id="contact_123", calendar_id="cal_123", start_time="2026-01-05T10:00:00Z", title="AI Booking: Test"
    )