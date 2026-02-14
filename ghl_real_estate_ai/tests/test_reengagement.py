"""
Test suite for Re-engagement Engine.

Tests:
1. Trigger detection at 24h, 48h, 72h intervals
2. Message template selection based on time elapsed
3. SMS compliance (all messages <160 characters)
4. Integration with GHL client for sending
5. Silent lead detection from memory
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set dummy env vars for Pydantic Settings validation
os.environ["ANTHROPIC_API_KEY"] = "sk-test-key"
os.environ["GHL_API_KEY"] = "ghl-test-key"
os.environ["GHL_LOCATION_ID"] = "loc-test-123"

import sys

sys.path.append(os.path.join(os.getcwd(), "ghl-real-estate-ai"))

from ghl_real_estate_ai.prompts.reengagement_templates import REENGAGEMENT_TEMPLATES
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.reengagement_engine import ReengagementEngine, ReengagementTrigger


@pytest.mark.asyncio
async def test_trigger_detection_24h():
    """Test that engine detects silent leads after 24 hours."""
    print("🧪 Testing 24h trigger detection...")

    engine = ReengagementEngine()

    # Create test contact with last interaction 25 hours ago
    test_contact_id = "test_24h_silent"
    last_interaction = datetime.utcnow() - timedelta(hours=25)

    context = {
        "contact_id": test_contact_id,
        "last_interaction_at": last_interaction.isoformat(),
        "conversation_history": [
            {"role": "user", "content": "Looking to buy a house", "timestamp": last_interaction.isoformat()}
        ],
        "extracted_preferences": {"goal": "buy"},
    }

    # Should trigger 24h re-engagement
    trigger = await engine.detect_trigger(context)

    assert trigger is not None, "Should detect 24h trigger"
    assert trigger == ReengagementTrigger.HOURS_24, f"Expected 24h trigger, got {trigger}"
    print("✅ 24h trigger detected correctly")


@pytest.mark.asyncio
async def test_trigger_detection_48h():
    """Test that engine detects silent leads after 48 hours."""
    print("🧪 Testing 48h trigger detection...")

    engine = ReengagementEngine()

    # Create test contact with last interaction 49 hours ago
    test_contact_id = "test_48h_silent"
    last_interaction = datetime.utcnow() - timedelta(hours=49)

    context = {
        "contact_id": test_contact_id,
        "last_interaction_at": last_interaction.isoformat(),
        "conversation_history": [
            {"role": "user", "content": "Thinking about selling", "timestamp": last_interaction.isoformat()}
        ],
        "extracted_preferences": {"goal": "sell"},
    }

    # Should trigger 48h re-engagement
    trigger = await engine.detect_trigger(context)

    assert trigger is not None, "Should detect 48h trigger"
    assert trigger == ReengagementTrigger.HOURS_48, f"Expected 48h trigger, got {trigger}"
    print("✅ 48h trigger detected correctly")


@pytest.mark.asyncio
async def test_trigger_detection_72h():
    """Test that engine detects silent leads after 72 hours."""
    print("🧪 Testing 72h trigger detection...")

    engine = ReengagementEngine()

    # Create test contact with last interaction 73 hours ago
    test_contact_id = "test_72h_silent"
    last_interaction = datetime.utcnow() - timedelta(hours=73)

    context = {
        "contact_id": test_contact_id,
        "last_interaction_at": last_interaction.isoformat(),
        "conversation_history": [
            {"role": "user", "content": "Just browsing", "timestamp": last_interaction.isoformat()}
        ],
        "extracted_preferences": {},
    }

    # Should trigger 72h re-engagement
    trigger = await engine.detect_trigger(context)

    assert trigger is not None, "Should detect 72h trigger"
    assert trigger == ReengagementTrigger.HOURS_72, f"Expected 72h trigger, got {trigger}"
    print("✅ 72h trigger detected correctly")


@pytest.mark.asyncio
async def test_no_trigger_for_recent_interactions():
    """Test that engine does NOT trigger for recent interactions."""
    print("🧪 Testing no trigger for recent interactions...")

    engine = ReengagementEngine()

    # Create test contact with last interaction 12 hours ago
    test_contact_id = "test_recent"
    last_interaction = datetime.utcnow() - timedelta(hours=12)

    context = {
        "contact_id": test_contact_id,
        "last_interaction_at": last_interaction.isoformat(),
        "conversation_history": [
            {"role": "user", "content": "Looking to buy", "timestamp": last_interaction.isoformat()}
        ],
    }

    # Should NOT trigger
    trigger = await engine.detect_trigger(context)

    assert trigger is None, f"Should not trigger for recent interactions, got {trigger}"
    print("✅ No trigger for recent interactions")


@pytest.mark.asyncio
async def test_message_template_selection():
    """Test that correct template is selected for each trigger."""
    print("🧪 Testing message template selection...")

    engine = ReengagementEngine()

    # Test 24h template
    msg_24h = engine.get_message_for_trigger(ReengagementTrigger.HOURS_24, contact_name="Sarah", action="buy")
    assert "still a priority" in msg_24h.lower() or "still interested" in msg_24h.lower(), (
        "24h message should ask about priority"
    )
    print(f"  24h message: {msg_24h}")

    # Test 48h template
    msg_48h = engine.get_message_for_trigger(ReengagementTrigger.HOURS_48, contact_name="Mike", action="sell")
    assert "close your file" in msg_48h.lower() or "still looking" in msg_48h.lower(), (
        "48h message should mention closing file"
    )
    print(f"  48h message: {msg_48h}")

    # Test 72h template
    msg_72h = engine.get_message_for_trigger(ReengagementTrigger.HOURS_72, contact_name="Lisa", action="buy")
    assert "last chance" in msg_72h.lower() or "move on" in msg_72h.lower(), "72h message should be final/direct"
    print(f"  72h message: {msg_72h}")

    print("✅ Template selection working correctly")


@pytest.mark.asyncio
async def test_sms_character_limit_compliance():
    """Test that ALL templates are under 160 characters (SMS limit)."""
    print("🧪 Testing SMS character limit compliance...")

    engine = ReengagementEngine()

    test_cases = [
        (ReengagementTrigger.HOURS_24, "Sarah", "buy"),
        (ReengagementTrigger.HOURS_24, "Christopher", "sell"),
        (ReengagementTrigger.HOURS_48, "Mike", "buy"),
        (ReengagementTrigger.HOURS_48, "Alexandria", "sell"),
        (ReengagementTrigger.HOURS_72, "Lisa", "buy"),
        (ReengagementTrigger.HOURS_72, "Maximilian", "sell"),
    ]

    for trigger, name, action in test_cases:
        message = engine.get_message_for_trigger(trigger, name, action)
        char_count = len(message)

        assert char_count <= 160, f"Message exceeds 160 chars: {char_count} chars\nMessage: {message}"

        print(f"  ✅ {trigger.value} ({name}, {action}): {char_count} chars")

    print("✅ All messages under 160 characters")


@pytest.mark.asyncio
async def test_integration_with_ghl_client():
    """Test that re-engagement engine integrates with GHL client to send SMS."""
    print("🧪 Testing GHL client integration...")

    # Mock GHL client
    mock_ghl_client = AsyncMock()
    mock_ghl_client.send_message.return_value = {"status": "sent", "messageId": "msg_123"}

    engine = ReengagementEngine(ghl_client=mock_ghl_client)

    # Create silent lead context
    context = {
        "contact_id": "test_integration",
        "last_interaction_at": (datetime.utcnow() - timedelta(hours=25)).isoformat(),
        "conversation_history": [
            {
                "role": "user",
                "content": "Looking to buy",
                "timestamp": (datetime.utcnow() - timedelta(hours=25)).isoformat(),
            }
        ],
        "extracted_preferences": {"goal": "buy"},
    }

    # Send re-engagement message
    result = await engine.send_reengagement_message(contact_id="test_integration", contact_name="John", context=context)

    assert result is not None, "Should return send result"
    assert result["status"] == "sent", "Message should be sent"

    # Verify GHL client was called
    mock_ghl_client.send_message.assert_called_once()
    call_args = mock_ghl_client.send_message.call_args

    assert call_args.kwargs["contact_id"] == "test_integration"
    assert len(call_args.kwargs["message"]) <= 160, "Message should be SMS-compliant"

    print("✅ GHL client integration working")


@pytest.mark.asyncio
async def test_silent_lead_detection_from_memory():
    """Test that engine can scan memory service for silent leads."""
    print("🧪 Testing silent lead detection from memory...")

    # Create test memory files
    memory_dir = Path("data/memory")
    memory_dir.mkdir(parents=True, exist_ok=True)

    # Create silent lead (48h old)
    silent_contact_id = "silent_lead_001"
    silent_context = {
        "contact_id": silent_contact_id,
        "last_interaction_at": (datetime.utcnow() - timedelta(hours=49)).isoformat(),
        "conversation_history": [
            {
                "role": "user",
                "content": "Interested in buying",
                "timestamp": (datetime.utcnow() - timedelta(hours=49)).isoformat(),
            }
        ],
        "extracted_preferences": {"goal": "buy"},
    }

    with open(memory_dir / f"{silent_contact_id}.json", "w") as f:
        json.dump(silent_context, f)

    # Create active lead (2h old)
    active_contact_id = "active_lead_001"
    active_context = {
        "contact_id": active_contact_id,
        "last_interaction_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "conversation_history": [
            {
                "role": "user",
                "content": "What's available?",
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            }
        ],
    }

    with open(memory_dir / f"{active_contact_id}.json", "w") as f:
        json.dump(active_context, f)

    # Scan for silent leads
    engine = ReengagementEngine()
    silent_leads = await engine.scan_for_silent_leads()

    assert len(silent_leads) > 0, "Should detect at least one silent lead"

    silent_ids = [lead["contact_id"] for lead in silent_leads]
    assert silent_contact_id in silent_ids, f"Should detect {silent_contact_id}"
    assert active_contact_id not in silent_ids, f"Should NOT flag active lead {active_contact_id}"

    print(f"✅ Detected {len(silent_leads)} silent leads correctly")

    # Cleanup
    (memory_dir / f"{silent_contact_id}.json").unlink()
    (memory_dir / f"{active_contact_id}.json").unlink()


@pytest.mark.asyncio
async def test_prevents_duplicate_reengagement():
    """Test that engine doesn't re-send same trigger level multiple times."""
    print("🧪 Testing duplicate prevention...")

    engine = ReengagementEngine()

    # Context with last re-engagement sent 24h message already
    context = {
        "contact_id": "test_duplicate",
        "last_interaction_at": (datetime.utcnow() - timedelta(hours=25)).isoformat(),
        "last_reengagement_trigger": "24h",
        "last_reengagement_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "conversation_history": [
            {
                "role": "user",
                "content": "Looking to buy",
                "timestamp": (datetime.utcnow() - timedelta(hours=25)).isoformat(),
            }
        ],
    }

    # Should NOT trigger again for 24h
    trigger = await engine.detect_trigger(context)

    # Should be None because 24h was already sent
    assert trigger is None, f"Should not re-trigger 24h, got {trigger}"

    print("✅ Duplicate prevention working")


if __name__ == "__main__":

    async def run_all_tests():
        print("=" * 80)
        print("Re-engagement Engine Test Suite")
        print("=" * 80)

        try:
            await test_trigger_detection_24h()
            await test_trigger_detection_48h()
            await test_trigger_detection_72h()
            await test_no_trigger_for_recent_interactions()
            await test_message_template_selection()
            await test_sms_character_limit_compliance()
            await test_integration_with_ghl_client()
            await test_silent_lead_detection_from_memory()
            await test_prevents_duplicate_reengagement()

            print("\n" + "=" * 80)
            print("✅ ALL TESTS PASSED")
            print("=" * 80)
        except AssertionError as e:
            print("\n" + "=" * 80)
            print(f"❌ TEST FAILED: {e}")
            print("=" * 80)
            raise

    asyncio.run(run_all_tests())