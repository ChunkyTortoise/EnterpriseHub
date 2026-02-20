"""
Tests for Portal Swipe Manager.

Tests the "Tinder-style" swipe logic for the branded client portal.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ghl_real_estate_ai.services.portal_swipe_manager import (
    FeedbackCategory,
    PortalSwipeManager,
    SwipeAction,
)


@pytest.fixture
def temp_interactions_file(tmp_path):
    """Create a temporary interactions file for testing."""
    interactions_file = tmp_path / "test_interactions.json"
    interactions_file.write_text(
        json.dumps(
            {
                "interactions": [],
                "metadata": {
                    "schema_version": "1.0",
                    "created_at": datetime.utcnow().isoformat(),
                },
            }
        )
    )
    return str(interactions_file)


@pytest.fixture
def mock_ghl_client():
    """Mock GHL client to avoid real API calls in tests."""
    from unittest.mock import AsyncMock, Mock
    mock = Mock()
    mock.add_tags = AsyncMock(return_value={"status": "success"})
    return mock


@pytest.fixture
def swipe_manager(temp_interactions_file, mock_ghl_client):
    """Create a PortalSwipeManager instance for testing."""
    manager = PortalSwipeManager(interactions_path=temp_interactions_file)
    manager.ghl_client = mock_ghl_client
    return manager


@pytest.mark.asyncio
async def test_handle_like_basic(swipe_manager):
    """Test basic like functionality."""
    result = await swipe_manager.handle_swipe(
        lead_id="test_lead_123",
        property_id="mls_001",
        action=SwipeAction.LIKE,
        location_id="loc_test",
        time_on_card=12.5,
    )

    assert result["status"] == "logged"
    assert result["trigger_sms"] == False
    assert result["high_intent"] == False
    assert len(swipe_manager.interactions) == 1

    # Verify interaction was logged
    interaction = swipe_manager.interactions[0]
    assert interaction["lead_id"] == "test_lead_123"
    assert interaction["property_id"] == "mls_001"
    assert interaction["action"] == "like"
    assert interaction["meta_data"]["time_on_card"] == 12.5


@pytest.mark.asyncio
async def test_high_intent_detection(swipe_manager):
    """Test that high-intent behavior is detected (3+ likes in 10 minutes)."""
    lead_id = "test_lead_high_intent"
    location_id = "loc_test"

    # Simulate 3 quick likes
    results = []
    for i in range(3):
        result = await swipe_manager.handle_swipe(
            lead_id=lead_id,
            property_id=f"mls_00{i}",
            action=SwipeAction.LIKE,
            location_id=location_id,
        )
        results.append(result)

    # First two likes should not trigger high intent
    assert results[0]["high_intent"] == False
    assert results[1]["high_intent"] == False

    # Third like should trigger high intent (3+ likes total)
    assert results[2]["high_intent"] == True
    assert results[2]["trigger_sms"] == True
    assert "High intent detected" in results[2]["message"]

    # Verify all likes were logged
    assert len(swipe_manager.interactions) == 3


@pytest.mark.asyncio
async def test_handle_pass_basic(swipe_manager):
    """Test basic pass functionality without feedback."""
    result = await swipe_manager.handle_swipe(
        lead_id="test_lead_456",
        property_id="mls_002",
        action=SwipeAction.PASS,
        location_id="loc_test",
        time_on_card=5.2,
    )

    assert result["status"] == "preference_updated"
    assert len(swipe_manager.interactions) == 1

    # Verify interaction was logged
    interaction = swipe_manager.interactions[0]
    assert interaction["lead_id"] == "test_lead_456"
    assert interaction["property_id"] == "mls_002"
    assert interaction["action"] == "pass"


@pytest.mark.asyncio
async def test_pass_with_price_feedback(swipe_manager):
    """Test pass with 'price too high' feedback."""
    feedback = {
        "category": FeedbackCategory.PRICE_TOO_HIGH.value,
        "text": "Way over my budget",
    }

    result = await swipe_manager.handle_swipe(
        lead_id="test_lead_789",
        property_id="mls_003",
        action=SwipeAction.PASS,
        location_id="loc_test",
        feedback=feedback,
    )

    assert result["status"] == "preference_updated"

    # Verify feedback was logged
    interaction = swipe_manager.interactions[0]
    assert interaction["meta_data"]["feedback_category"] == "price_too_high"
    assert interaction["meta_data"]["feedback_text"] == "Way over my budget"


@pytest.mark.asyncio
async def test_pass_with_location_feedback(swipe_manager):
    """Test pass with location feedback."""
    feedback = {
        "category": FeedbackCategory.LOCATION.value,
        "text": "Too far from work",
    }

    result = await swipe_manager.handle_swipe(
        lead_id="test_lead_location",
        property_id="mls_004",
        action=SwipeAction.PASS,
        location_id="loc_test",
        feedback=feedback,
    )

    assert result["status"] == "preference_updated"
    interaction = swipe_manager.interactions[0]
    assert interaction["meta_data"]["feedback_category"] == "location"


@pytest.mark.asyncio
async def test_get_lead_stats(swipe_manager):
    """Test getting statistics for a lead."""
    lead_id = "test_lead_stats"
    location_id = "loc_test"

    # Create some interactions
    await swipe_manager.handle_swipe(
        lead_id=lead_id,
        property_id="mls_010",
        action=SwipeAction.LIKE,
        location_id=location_id,
    )

    await swipe_manager.handle_swipe(
        lead_id=lead_id,
        property_id="mls_011",
        action=SwipeAction.LIKE,
        location_id=location_id,
    )

    await swipe_manager.handle_swipe(
        lead_id=lead_id,
        property_id="mls_012",
        action=SwipeAction.PASS,
        location_id=location_id,
        feedback={"category": FeedbackCategory.PRICE_TOO_HIGH.value},
    )

    # Get stats
    stats = swipe_manager.get_lead_stats(lead_id)

    assert stats["lead_id"] == lead_id
    assert stats["total_interactions"] == 3
    assert stats["likes"] == 2
    assert stats["passes"] == 1
    assert stats["like_rate"] == pytest.approx(0.666, rel=0.01)
    assert stats["pass_reasons"]["price_too_high"] == 1
    assert stats["recent_likes_10min"] == 2


@pytest.mark.asyncio
async def test_count_recent_likes(swipe_manager):
    """Test counting recent likes."""
    lead_id = "test_lead_recent"
    location_id = "loc_test"

    # Add 2 likes
    for i in range(2):
        await swipe_manager.handle_swipe(
            lead_id=lead_id,
            property_id=f"mls_recent_{i}",
            action=SwipeAction.LIKE,
            location_id=location_id,
        )

    count = swipe_manager._count_recent_likes(lead_id, minutes=10)
    assert count == 2


def test_log_interaction_structure(swipe_manager):
    """Test that logged interactions have the correct structure."""
    swipe_manager._log_interaction(
        lead_id="test_lead",
        property_id="mls_123",
        action=SwipeAction.LIKE,
        feedback=None,
        time_on_card=10.5,
    )

    interaction = swipe_manager.interactions[0]

    # Check required fields
    assert "interaction_id" in interaction
    assert "lead_id" in interaction
    assert "property_id" in interaction
    assert "action" in interaction
    assert "timestamp" in interaction
    assert "meta_data" in interaction

    # Check UUID format
    assert len(interaction["interaction_id"]) == 36  # UUID4 format

    # Check timestamp is ISO format
    datetime.fromisoformat(interaction["timestamp"].replace("Z", "+00:00"))


def test_feedback_categories_enum():
    """Test that feedback categories are properly defined."""
    categories = [
        FeedbackCategory.PRICE_TOO_HIGH,
        FeedbackCategory.PRICE_TOO_LOW,
        FeedbackCategory.LOCATION,
        FeedbackCategory.STYLE,
        FeedbackCategory.SIZE_TOO_SMALL,
        FeedbackCategory.SIZE_TOO_LARGE,
        FeedbackCategory.OTHER,
    ]

    assert len(categories) == 7
    assert FeedbackCategory.PRICE_TOO_HIGH.value == "price_too_high"
    assert FeedbackCategory.LOCATION.value == "location"


@pytest.mark.asyncio
async def test_multiple_leads_isolation(swipe_manager):
    """Test that statistics are properly isolated between leads."""
    location_id = "loc_test"

    # Lead 1: 2 likes
    await swipe_manager.handle_swipe(
        lead_id="lead_1",
        property_id="mls_a",
        action=SwipeAction.LIKE,
        location_id=location_id,
    )
    await swipe_manager.handle_swipe(
        lead_id="lead_1",
        property_id="mls_b",
        action=SwipeAction.LIKE,
        location_id=location_id,
    )

    # Lead 2: 1 like, 1 pass
    await swipe_manager.handle_swipe(
        lead_id="lead_2",
        property_id="mls_c",
        action=SwipeAction.LIKE,
        location_id=location_id,
    )
    await swipe_manager.handle_swipe(
        lead_id="lead_2",
        property_id="mls_d",
        action=SwipeAction.PASS,
        location_id=location_id,
    )

    # Check stats are isolated
    stats_1 = swipe_manager.get_lead_stats("lead_1")
    stats_2 = swipe_manager.get_lead_stats("lead_2")

    assert stats_1["total_interactions"] == 2
    assert stats_1["likes"] == 2
    assert stats_1["passes"] == 0

    assert stats_2["total_interactions"] == 2
    assert stats_2["likes"] == 1
    assert stats_2["passes"] == 1


@pytest.mark.asyncio
async def test_interaction_persistence(temp_interactions_file):
    """Test that interactions are persisted to file."""
    manager1 = PortalSwipeManager(interactions_path=temp_interactions_file)

    # Add an interaction
    await manager1.handle_swipe(
        lead_id="test_persist",
        property_id="mls_persist",
        action=SwipeAction.LIKE,
        location_id="loc_test",
    )

    # Create a new manager instance (simulating restart)
    manager2 = PortalSwipeManager(interactions_path=temp_interactions_file)

    # Verify interaction was loaded
    assert len(manager2.interactions) == 1
    assert manager2.interactions[0]["lead_id"] == "test_persist"
    assert manager2.interactions[0]["property_id"] == "mls_persist"


@pytest.mark.asyncio
async def test_time_on_card_tracking(swipe_manager):
    """Test that time spent on card is properly tracked."""
    await swipe_manager.handle_swipe(
        lead_id="test_time",
        property_id="mls_time",
        action=SwipeAction.LIKE,
        location_id="loc_test",
        time_on_card=25.7,
    )

    interaction = swipe_manager.interactions[0]
    assert interaction["meta_data"]["time_on_card"] == 25.7


@pytest.mark.asyncio
async def test_swipe_action_enum():
    """Test SwipeAction enum values."""
    assert SwipeAction.LIKE.value == "like"
    assert SwipeAction.PASS.value == "pass"

    # Test creating from string
    assert SwipeAction("like") == SwipeAction.LIKE
    assert SwipeAction("pass") == SwipeAction.PASS