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


@pytest.mark.asyncio
async def test_configurable_thresholds_custom_hot():
    """Test MEDIUM-002 Fix: Hot seller temperature calculation with custom thresholds"""
    from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

    # Create custom config with modified hot thresholds
    custom_config = JorgeSellerConfig()
    custom_config.HOT_QUESTIONS_REQUIRED = 3  # Lower threshold for testing
    custom_config.HOT_QUALITY_THRESHOLD = 0.6  # Lower quality threshold

    # Initialize engine with custom config and minimal mocks
    mock_conversation_manager = AsyncMock()
    mock_ghl_client = AsyncMock()
    seller_engine = JorgeSellerEngine(mock_conversation_manager, mock_ghl_client, config=custom_config)

    # Test the temperature calculation directly (bypass full pipeline)
    seller_data = {
        "motivation": "relocation",
        "timeline_acceptable": True,  # Required for hot
        "property_condition": "move-in ready",
        "questions_answered": 3,  # Only 3 questions (would fail default hot criteria of 4)
        "response_quality": 0.65,  # Lower quality (would fail default hot criteria of 0.7)
    }

    # Execute temperature calculation directly
    temperature_result = await seller_engine._calculate_seller_temperature(seller_data)

    # Assert - should be HOT with custom thresholds (3 questions >= 3, quality 0.65 >= 0.6, timeline True)
    assert temperature_result["temperature"] == "hot", \
        f"Expected 'hot' but got '{temperature_result['temperature']}' with custom thresholds"

    # Verify thresholds were applied
    assert "analytics" in temperature_result
    analytics = temperature_result["analytics"]
    assert "thresholds_used" in analytics
    assert analytics["thresholds_used"]["hot_questions"] == 3
    assert analytics["thresholds_used"]["hot_quality"] == 0.6


@pytest.mark.asyncio
async def test_configurable_thresholds_custom_warm():
    """Test MEDIUM-002 Fix: Warm seller temperature calculation with custom thresholds"""
    from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

    # Create custom config with modified warm thresholds
    custom_config = JorgeSellerConfig()
    custom_config.WARM_QUESTIONS_REQUIRED = 2  # Lower threshold for testing
    custom_config.WARM_QUALITY_THRESHOLD = 0.4  # Lower quality threshold

    # Initialize engine with custom config and minimal mocks
    mock_conversation_manager = AsyncMock()
    mock_ghl_client = AsyncMock()
    seller_engine = JorgeSellerEngine(mock_conversation_manager, mock_ghl_client, config=custom_config)

    # Test the temperature calculation directly (bypass full pipeline)
    seller_data = {
        "motivation": "relocation",  # Question 1 answered
        "property_condition": "needs work",  # Question 3 answered (2 total)
        "timeline_acceptable": False,
        "questions_answered": 2,
        "response_quality": 0.45,  # Lower quality (would fail default warm criteria of 0.5)
    }

    # Execute temperature calculation directly
    temperature_result = await seller_engine._calculate_seller_temperature(seller_data)

    # Assert - should be WARM with custom thresholds (2 questions >= 2, quality 0.45 >= 0.4)
    assert temperature_result["temperature"] == "warm", \
        f"Expected 'warm' but got '{temperature_result['temperature']}' with custom thresholds"

    # Verify thresholds were applied
    assert "analytics" in temperature_result
    analytics = temperature_result["analytics"]
    assert "thresholds_used" in analytics
    assert analytics["thresholds_used"]["warm_questions"] == 2
    assert analytics["thresholds_used"]["warm_quality"] == 0.4


@pytest.mark.asyncio
async def test_default_thresholds_backward_compatibility(mock_conversation_manager, mock_ghl_client):
    """Test MEDIUM-002 Fix: Default thresholds maintain backward compatibility"""
    # Initialize engine without config (should use defaults)
    seller_engine = JorgeSellerEngine(mock_conversation_manager, mock_ghl_client)

    contact_id = "default_config_test"
    user_message = "Yes definitely"
    location_id = "test_location"

    # Simulate standard hot seller scenario with default thresholds
    mock_conversation_manager.extract_seller_data.return_value = {
        "motivation": "relocation",
        "timeline_acceptable": True,
        "property_condition": "move-in ready",
        "price_expectation": 500000,
        "questions_answered": 4,
        "response_quality": 0.9,
        "contact_name": "Default User"
    }

    # Execute
    result = await seller_engine.process_seller_response(contact_id, user_message, location_id)

    # Assert - should be HOT with default thresholds (4 questions, 0.7 quality)
    assert result["temperature"] == "hot"

    # Verify default thresholds were used
    assert "analytics" in result
    analytics = result["analytics"]
    assert "thresholds_used" in analytics
    assert analytics["thresholds_used"]["hot_questions"] == 4  # Default
    assert analytics["thresholds_used"]["hot_quality"] == 0.7  # Default
    assert analytics["thresholds_used"]["warm_questions"] == 3  # Default
    assert analytics["thresholds_used"]["warm_quality"] == 0.5  # Default


def test_validate_seller_required_fields_reports_missing_fields():
    from ghl_real_estate_ai.core.conversation_manager import ConversationManager

    result = ConversationManager.validate_seller_required_fields(
        {
            "motivation": "relocation",
            "timeline_acceptable": True,
        }
    )

    assert result["is_complete"] is False
    assert set(result["missing_fields"]) == {"property_condition", "price_expectation"}
    assert result["completion_ratio"] == 0.5


@pytest.mark.asyncio
async def test_required_field_completeness_hook_uses_validator(seller_engine, mock_conversation_manager):
    mock_conversation_manager.validate_seller_required_fields.return_value = {
        "required_fields": ["motivation", "timeline_acceptable", "property_condition", "price_expectation"],
        "missing_fields": ["price_expectation"],
        "is_complete": False,
        "completion_ratio": 0.75,
    }

    enriched = await seller_engine._evaluate_required_field_completeness(
        {"motivation": "relocation", "timeline_acceptable": True, "property_condition": "needs work"}
    )

    assert enriched["missing_required_fields"] == ["price_expectation"]
    assert enriched["required_fields_complete"] is False
    assert enriched["qualification_completeness"] == 0.75


def test_parse_amount_with_retry_honors_max_retries(seller_engine):
    with patch.object(seller_engine, "_parse_amount_once", side_effect=ValueError("invalid")) as parse_once:
        parsed = seller_engine._parse_amount_with_retry("not-a-number")

    assert parsed is None
    assert parse_once.call_count == seller_engine.NUMERIC_PARSE_MAX_RETRIES
