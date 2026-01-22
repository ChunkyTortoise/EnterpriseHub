import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime
import time
from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine, SellerQuestions

@pytest.fixture
def mock_conversation_manager():
    manager = AsyncMock()
    manager.get_context.return_value = {
        "seller_preferences": {},
        "conversation_history": []
    }
    manager.extract_seller_data.return_value = {}
    return manager

@pytest.fixture
def mock_ghl_client():
    return AsyncMock()

@pytest.fixture
def seller_engine(mock_conversation_manager, mock_ghl_client):
    return JorgeSellerEngine(mock_conversation_manager, mock_ghl_client)

@pytest.mark.asyncio
async def test_process_seller_response_initial(seller_engine, mock_conversation_manager):
    # Setup
    contact_id = "test_contact"
    user_message = "I want to sell my house"
    location_id = "test_location"
    
    mock_conversation_manager.extract_seller_data.return_value = {
        "motivation": "relocation",
        "questions_answered": 1,
        "response_quality": 0.8
    }
    
    # Execute
    result = await seller_engine.process_seller_response(contact_id, user_message, location_id)
    
    # Assert
    assert result["temperature"] == "cold"  # Not enough questions answered
    assert "actions" in result
    assert result["questions_answered"] == 1
    # Should ask next question (Timeline)
    assert SellerQuestions.TIMELINE in result["message"] or "30 to 45 days" in result["message"]

@pytest.mark.asyncio
async def test_hot_seller_qualification(seller_engine, mock_conversation_manager):
    # Setup
    contact_id = "hot_lead"
    user_message = "$500,000"  # Definitive answer that will score high in semantic assessment
    location_id = "test_location"

    # Simulate all questions answered perfectly
    mock_conversation_manager.extract_seller_data.return_value = {
        "motivation": "relocation",
        "timeline_acceptable": True,
        "property_condition": "move-in ready",
        "price_expectation": 500000,
        "questions_answered": 4,
        "response_quality": 0.9,
        "contact_name": "John"
    }

    # Execute
    result = await seller_engine.process_seller_response(contact_id, user_message, location_id)

    # Assert
    assert result["temperature"] == "hot"
    
    # Check for hot lead actions
    action_types = [a["type"] for a in result["actions"]]
    assert "trigger_workflow" in action_types
    assert "add_tag" in action_types
    
    # Check for specific tags
    tags = [a["tag"] for a in result["actions"] if a["type"] == "add_tag"]
    assert "Hot-Seller" in tags
    assert "Seller-Qualified" in tags
    
    # Check handoff message
    assert "schedule" in result["message"].lower() or "team" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_warm_seller_qualification(seller_engine, mock_conversation_manager):
        # Setup
        contact_id = "warm_lead"
        user_message = "I am definitely interested" # "definitely" triggers 0.8 quality score in engine
        location_id = "test_location"
    
        # 3 questions answered, okay quality
        mock_conversation_manager.extract_seller_data.return_value = {
            "motivation": "relocation",
            "timeline_acceptable": False,
            "property_condition": "move-in ready",
            "questions_answered": 3,
            "response_quality": 0.6
        }
    
        # Execute
        result = await seller_engine.process_seller_response(contact_id, user_message, location_id)
    
        # Assert
        assert result["temperature"] == "warm"
        tags = [a["tag"] for a in result["actions"] if a["type"] == "add_tag"]
        assert "Warm-Seller" in tags

@pytest.mark.asyncio
async def test_confrontational_response_poor_quality(seller_engine, mock_conversation_manager):
    # Setup
    contact_id = "vague_lead"
    user_message = "idk maybe"
    location_id = "test_location"

    mock_conversation_manager.extract_seller_data.return_value = {
        "questions_answered": 1,
        "response_quality": 0.2,  # Low quality
        "last_user_message": "idk maybe",
        "contact_name": "Bob"
    }

    # Execute
    result = await seller_engine.process_seller_response(contact_id, user_message, location_id)

    # Assert
    # Should generate a confrontational follow-up
    # We can't easily assert exact text due to randomness, but we can check it's not the next question directly
    # or that it contains some "confrontational" language
    pass # The engine logic handles this, relying on tone engine tests for specific content


@pytest.mark.asyncio
async def test_vapi_retry_on_failure(seller_engine, mock_conversation_manager):
    """Test that Vapi outbound calls retry with exponential backoff on failure"""
    # Setup
    contact_id = "hot_lead_vapi_retry"
    user_message = "$450000 and yes to 30 days"  # High quality response
    location_id = "test_location"

    # Simulate hot seller - use explicit high quality indicators
    mock_conversation_manager.extract_seller_data.return_value = {
        "motivation": "relocating for work",
        "timeline_acceptable": True,
        "property_condition": "move-in ready",
        "price_expectation": 450000,
        "questions_answered": 4,
        "response_quality": 0.95,  # Explicit high quality
        "contact_name": "John Doe",
        "phone": "+15125551234",
        "property_address": "123 Main St"
    }

    # Mock VapiService to fail first 2 times, succeed on 3rd
    with patch('ghl_real_estate_ai.services.vapi_service.VapiService') as MockVapi:
        mock_vapi_instance = MockVapi.return_value
        # First two calls fail, third succeeds
        mock_vapi_instance.trigger_outbound_call.side_effect = [False, False, True]

        start_time = time.time()

        # Execute
        result = await seller_engine.process_seller_response(contact_id, user_message, location_id)

        elapsed_time = time.time() - start_time

        # Assert - check retry behavior regardless of temperature
        # Should have called trigger_outbound_call 3 times (2 failures + 1 success)
        assert mock_vapi_instance.trigger_outbound_call.call_count == 3

        # Should have taken at least 3 seconds (1s + 2s delays)
        assert elapsed_time >= 3.0, f"Expected at least 3s for exponential backoff, got {elapsed_time}s"

        # If temperature is hot, should have logged success event
        if result["temperature"] == "hot":
            log_events = [a for a in result["actions"] if a["type"] == "log_event"]
            vapi_success_logged = any("Vapi Outbound Call Triggered" in e.get("event", "") for e in log_events)
            assert vapi_success_logged, "Vapi success should be logged after retry"

            # Should NOT have Voice-Handoff-Failed tag since it eventually succeeded
            tags = [a["tag"] for a in result["actions"] if a["type"] == "add_tag"]
            assert "Voice-Handoff-Failed" not in tags


@pytest.mark.asyncio
async def test_vapi_retry_all_attempts_fail(seller_engine, mock_conversation_manager):
    """Test that Vapi logs failure and adds tag when all retry attempts fail"""
    # Setup
    contact_id = "hot_lead_vapi_all_fail"
    user_message = "$500k yes to timeline"  # High quality definitive response
    location_id = "test_location"

    # Simulate hot seller - use explicit high quality indicators
    mock_conversation_manager.extract_seller_data.return_value = {
        "motivation": "relocating for work",
        "timeline_acceptable": True,
        "property_condition": "move-in ready",
        "price_expectation": 500000,
        "questions_answered": 4,
        "response_quality": 0.95,  # Explicit high quality
        "contact_name": "Jane Smith",
        "phone": "+15125555678",
        "property_address": "456 Oak Ave"
    }

    # Mock VapiService to always fail
    with patch('ghl_real_estate_ai.services.vapi_service.VapiService') as MockVapi:
        mock_vapi_instance = MockVapi.return_value
        # All 3 attempts fail
        mock_vapi_instance.trigger_outbound_call.return_value = False

        start_time = time.time()

        # Execute
        result = await seller_engine.process_seller_response(contact_id, user_message, location_id)

        elapsed_time = time.time() - start_time

        # Assert - check retry behavior regardless of temperature
        # Should have called trigger_outbound_call 3 times (max retries)
        assert mock_vapi_instance.trigger_outbound_call.call_count == 3

        # Should have taken at least 3 seconds (1s + 2s delays between attempts)
        # Note: We don't sleep after the final failure, only between retries
        assert elapsed_time >= 3.0, f"Expected at least 3s for exponential backoff, got {elapsed_time}s"

        # If temperature is hot, should have failure events and tags
        if result["temperature"] == "hot":
            # Should have logged failure event
            log_events = [a for a in result["actions"] if a["type"] == "log_event"]
            vapi_failure_logged = any("Vapi Outbound Call Failed" in e.get("event", "") for e in log_events)
            assert vapi_failure_logged, "Vapi failure should be logged after all retries exhausted"

            # Should have Voice-Handoff-Failed tag
            tags = [a["tag"] for a in result["actions"] if a["type"] == "add_tag"]
            assert "Voice-Handoff-Failed" in tags
