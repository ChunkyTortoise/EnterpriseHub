"""
Tests for HIGH-001: Semantic Response Quality Assessment

Tests that response quality is based on semantic meaning, not just length.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine


@pytest.fixture
def mock_conversation_manager():
    manager = AsyncMock()
    manager.get_context.return_value = {"seller_preferences": {}, "conversation_history": []}
    manager.extract_seller_data.return_value = {}
    return manager


@pytest.fixture
def mock_ghl_client():
    return AsyncMock()


@pytest.fixture
def seller_engine(mock_conversation_manager, mock_ghl_client):
    return JorgeSellerEngine(mock_conversation_manager, mock_ghl_client)


@pytest.mark.asyncio
async def test_good_short_answer_high_quality(seller_engine):
    """Test that a good short answer (e.g., 'yes') gets high quality score"""
    # Short but definitive answer
    quality = await seller_engine._assess_response_quality_semantic("yes")

    # Should be high quality despite being short
    assert quality > 0.7, f"Expected quality > 0.7 for definitive 'yes', got {quality}"


@pytest.mark.asyncio
async def test_bad_long_answer_low_quality(seller_engine):
    """Test that a long but vague answer gets low quality score"""
    # Long but evasive/vague answer
    vague_long_message = (
        "I'm not really sure about all this, maybe I might be interested "
        "in selling but I don't know, it depends on a lot of things, I guess "
        "we'll see what happens, who knows really"
    )

    quality = await seller_engine._assess_response_quality_semantic(vague_long_message)

    # Should be low quality despite being long
    assert quality < 0.5, f"Expected quality < 0.5 for vague long answer, got {quality}"


@pytest.mark.asyncio
async def test_specific_answer_high_quality(seller_engine):
    """Test that specific, informative answers get high quality"""
    specific_message = "$450,000"

    quality = await seller_engine._assess_response_quality_semantic(specific_message)

    # Should be high quality - specific price
    assert quality > 0.8, f"Expected quality > 0.8 for specific price, got {quality}"


@pytest.mark.asyncio
async def test_vague_short_answer_low_quality(seller_engine):
    """Test that vague short answers get low quality"""
    vague_message = "idk maybe"

    quality = await seller_engine._assess_response_quality_semantic(vague_message)

    # Should be low quality - vague and non-committal
    assert quality < 0.5, f"Expected quality < 0.5 for 'idk maybe', got {quality}"


@pytest.mark.asyncio
async def test_informative_answer_high_quality(seller_engine):
    """Test that informative answers get high quality regardless of length"""
    informative_message = "I'm relocating to Austin for work in 6 weeks"

    quality = await seller_engine._assess_response_quality_semantic(informative_message)

    # Should be high quality - specific and informative
    assert quality > 0.7, f"Expected quality > 0.7 for informative answer, got {quality}"


@pytest.mark.asyncio
async def test_unclear_rambling_low_quality(seller_engine):
    """Test that unclear rambling gets low quality"""
    rambling_message = "well you know things are kind of complicated right now and stuff"

    quality = await seller_engine._assess_response_quality_semantic(rambling_message)

    # Should be low quality - unclear and non-specific
    assert quality < 0.6, f"Expected quality < 0.6 for rambling, got {quality}"


@pytest.mark.asyncio
async def test_timeline_specific_high_quality(seller_engine):
    """Test that timeline-specific answers get high quality"""
    timeline_message = "30 days works fine"

    quality = await seller_engine._assess_response_quality_semantic(timeline_message)

    # Should be high quality - directly addresses timeline question
    assert quality > 0.8, f"Expected quality > 0.8 for timeline answer, got {quality}"


@pytest.mark.asyncio
async def test_condition_specific_high_quality(seller_engine):
    """Test that condition-specific answers get high quality"""
    condition_message = "move-in ready, just painted"

    quality = await seller_engine._assess_response_quality_semantic(condition_message)

    # Should be high quality - specific condition details
    assert quality > 0.7, f"Expected quality > 0.7 for condition answer, got {quality}"


@pytest.mark.asyncio
async def test_integration_with_extraction(seller_engine, mock_conversation_manager):
    """Test that semantic quality assessment integrates with extraction"""
    contact_id = "test_contact"
    location_id = "test_location"

    # Good short answer
    user_message = "yes"

    # Mock extraction to return minimal data
    mock_conversation_manager.extract_seller_data.return_value = {"timeline_acceptable": True, "questions_answered": 1}

    # Process the response
    result = await seller_engine.process_seller_response(
        contact_id=contact_id, user_message=user_message, location_id=location_id
    )

    # Check that response quality is properly assessed
    seller_data = result.get("seller_data", {})
    quality = seller_data.get("response_quality", 0.0)

    # Should have high quality for definitive "yes"
    assert quality > 0.7, f"Expected quality > 0.7 for 'yes', got {quality}"


@pytest.mark.asyncio
async def test_fallback_on_api_failure(seller_engine, mock_conversation_manager):
    """Test that if Claude API fails, we fall back to heuristic assessment"""
    # This will be tested by mocking the LLM client to raise an exception
    # For now, just ensure the method exists and has error handling

    # Test with a normal message
    quality = await seller_engine._assess_response_quality_semantic("test message")

    # Should return a valid quality score even if Claude fails
    assert 0.0 <= quality <= 1.0, f"Quality score should be 0-1, got {quality}"
