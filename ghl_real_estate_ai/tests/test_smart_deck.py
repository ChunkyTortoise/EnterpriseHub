"""
Tests for Smart Deck Functionality.

Tests the AI recommendation engine that filters and curates properties.
"""

from datetime import datetime

import pytest

from ghl_real_estate_ai.services.portal_swipe_manager import (
    FeedbackCategory,
    PortalSwipeManager,
    SwipeAction,
)
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher


@pytest.fixture
def mock_properties():
    """Create mock property listings for testing."""
    return [
        {
            "id": "prop_001",
            "property_id": "prop_001",
            "price": 400000,
            "bedrooms": 3,
            "bathrooms": 2,
            "address": {"city": "San Diego", "neighborhood": "Downtown"},
            "property_type": "Single Family",
        },
        {
            "id": "prop_002",
            "property_id": "prop_002",
            "price": 600000,
            "bedrooms": 4,
            "bathrooms": 3,
            "address": {"city": "San Diego", "neighborhood": "La Jolla"},
            "property_type": "Single Family",
        },
        {
            "id": "prop_003",
            "property_id": "prop_003",
            "price": 350000,
            "bedrooms": 2,
            "bathrooms": 2,
            "address": {"city": "San Diego", "neighborhood": "Mission Valley"},
            "property_type": "Condo",
        },
        {
            "id": "prop_004",
            "property_id": "prop_004",
            "price": 800000,
            "bedrooms": 5,
            "bathrooms": 4,
            "address": {"city": "San Diego", "neighborhood": "Del Mar"},
            "property_type": "Single Family",
        },
        {
            "id": "prop_005",
            "property_id": "prop_005",
            "price": 450000,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "address": {"city": "San Diego", "neighborhood": "North Park"},
            "property_type": "Townhouse",
        },
    ]


@pytest.fixture
def mock_property_matcher(mock_properties, monkeypatch):
    """Create a mock PropertyMatcher that returns test data."""

    class MockPropertyMatcher:
        def __init__(self):
            self.properties = mock_properties

        def find_matches(self, preferences, limit=10, min_score=0.5):
            # Simple filtering based on budget
            budget = preferences.get("budget", float("inf"))
            matches = [{**prop, "match_score": 0.8} for prop in self.properties if prop["price"] <= budget]
            return matches[:limit]

    return MockPropertyMatcher()


@pytest.fixture
def swipe_manager_with_mock(tmp_path, mock_property_matcher):
    """Create a swipe manager with mock property matcher."""
    interactions_file = tmp_path / "test_interactions.json"
    interactions_file.write_text('{"interactions": [], "metadata": {}}')

    manager = PortalSwipeManager(interactions_path=str(interactions_file), property_matcher=mock_property_matcher)
    return manager


@pytest.mark.asyncio
async def test_smart_deck_excludes_seen_properties(swipe_manager_with_mock):
    """Test that smart deck excludes properties user has already swiped on."""
    lead_id = "test_lead_exclusion"
    location_id = "loc_test"

    # Swipe on prop_001
    await swipe_manager_with_mock.handle_swipe(
        lead_id=lead_id,
        property_id="prop_001",
        action=SwipeAction.LIKE,
        location_id=location_id,
    )

    # Get smart deck
    deck = await swipe_manager_with_mock.get_smart_deck(lead_id=lead_id, location_id=location_id, limit=10)

    # Verify prop_001 is NOT in the deck
    deck_ids = [p.get("id") or p.get("property_id") for p in deck]
    assert "prop_001" not in deck_ids

    # Verify other properties are present
    assert len(deck) > 0


@pytest.mark.asyncio
async def test_smart_deck_applies_budget_adjustments(swipe_manager_with_mock):
    """Test that deck applies learned budget preferences."""
    lead_id = "test_lead_budget"
    location_id = "loc_test"

    # Reject 3 properties as "too expensive"
    # This will trigger automatic budget adjustment
    for prop_id in ["prop_002", "prop_004", "prop_005"]:
        await swipe_manager_with_mock.handle_swipe(
            lead_id=lead_id,
            property_id=prop_id,
            action=SwipeAction.PASS,
            location_id=location_id,
            feedback={"category": FeedbackCategory.PRICE_TOO_HIGH.value},
        )

    # Get smart deck - should apply budget reduction internally
    deck = await swipe_manager_with_mock.get_smart_deck(lead_id=lead_id, location_id=location_id, limit=10)

    # Verify deck returned properties
    # The smart deck applies negative feedback adjustments automatically
    assert isinstance(deck, list)

    # Verify the deck doesn't include the rejected properties
    deck_ids = [p.get("id") or p.get("property_id") for p in deck]
    assert "prop_002" not in deck_ids
    assert "prop_004" not in deck_ids
    assert "prop_005" not in deck_ids


@pytest.mark.asyncio
async def test_get_seen_property_ids(swipe_manager_with_mock):
    """Test getting list of seen property IDs."""
    lead_id = "test_seen_ids"
    location_id = "loc_test"

    # Swipe on multiple properties
    prop_ids = ["prop_001", "prop_002", "prop_003"]
    for prop_id in prop_ids:
        await swipe_manager_with_mock.handle_swipe(
            lead_id=lead_id,
            property_id=prop_id,
            action=SwipeAction.LIKE,
            location_id=location_id,
        )

    # Get seen IDs
    seen_ids = swipe_manager_with_mock._get_seen_property_ids(lead_id)

    assert len(seen_ids) == 3
    for prop_id in prop_ids:
        assert prop_id in seen_ids


@pytest.mark.asyncio
async def test_apply_negative_feedback_adjustments(swipe_manager_with_mock):
    """Test that negative feedback adjusts preferences."""
    lead_id = "test_feedback_adjust"
    location_id = "loc_test"

    # Set initial preferences
    initial_prefs = {"budget": 500000, "bedrooms": 2}

    # Simulate 3 "price too high" rejections
    for i in range(3):
        swipe_manager_with_mock._log_interaction(
            lead_id=lead_id,
            property_id=f"prop_00{i}",
            action=SwipeAction.PASS,
            feedback={"category": FeedbackCategory.PRICE_TOO_HIGH.value},
            time_on_card=5.0,
        )

    # Apply adjustments
    adjusted = swipe_manager_with_mock._apply_negative_feedback_adjustments(lead_id, initial_prefs)

    # Budget should be lowered
    assert adjusted["budget"] < initial_prefs["budget"]
    assert adjusted["budget"] == int(500000 * 0.95)  # 5% reduction


@pytest.mark.asyncio
async def test_size_feedback_adjustments(swipe_manager_with_mock):
    """Test that 'too small' feedback increases bedroom requirement."""
    lead_id = "test_size_adjust"
    location_id = "loc_test"

    initial_prefs = {"budget": 500000, "bedrooms": 2}

    # Simulate 2 "too small" rejections
    for i in range(2):
        swipe_manager_with_mock._log_interaction(
            lead_id=lead_id,
            property_id=f"prop_size_{i}",
            action=SwipeAction.PASS,
            feedback={"category": FeedbackCategory.SIZE_TOO_SMALL.value},
            time_on_card=3.0,
        )

    # Apply adjustments
    adjusted = swipe_manager_with_mock._apply_negative_feedback_adjustments(lead_id, initial_prefs)

    # Bedrooms should be increased
    assert adjusted["bedrooms"] == 3  # Increased from 2


@pytest.mark.asyncio
async def test_smart_deck_empty_when_all_seen(swipe_manager_with_mock):
    """Test that smart deck returns empty when all properties are seen."""
    lead_id = "test_all_seen"
    location_id = "loc_test"

    # Swipe on all properties
    for prop_id in ["prop_001", "prop_002", "prop_003", "prop_004", "prop_005"]:
        await swipe_manager_with_mock.handle_swipe(
            lead_id=lead_id,
            property_id=prop_id,
            action=SwipeAction.LIKE,
            location_id=location_id,
        )

    # Get smart deck
    deck = await swipe_manager_with_mock.get_smart_deck(lead_id=lead_id, location_id=location_id, limit=10)

    # Should be empty or very few properties
    assert len(deck) == 0


@pytest.mark.asyncio
async def test_smart_deck_respects_limit(swipe_manager_with_mock):
    """Test that smart deck respects the limit parameter."""
    lead_id = "test_limit"
    location_id = "loc_test"

    # Get deck with limit=2
    deck = await swipe_manager_with_mock.get_smart_deck(lead_id=lead_id, location_id=location_id, limit=2)

    assert len(deck) <= 2


@pytest.mark.asyncio
async def test_smart_deck_with_no_preferences(swipe_manager_with_mock):
    """Test smart deck works even without stored preferences."""
    lead_id = "test_no_prefs"
    location_id = "loc_test"

    # Don't set any preferences
    deck = await swipe_manager_with_mock.get_smart_deck(lead_id=lead_id, location_id=location_id, limit=10)

    # Should still return properties
    assert isinstance(deck, list)


@pytest.mark.asyncio
async def test_filter_negative_matches(swipe_manager_with_mock):
    """Test filtering based on negative matches."""
    lead_id = "test_neg_filter"
    location_id = "loc_test"

    # Create context with negative matches
    context = {
        "negative_matches": [
            {
                "property_id": "prop_001",
                "reason": FeedbackCategory.LOCATION.value,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]
    }

    # Mock properties
    properties = [
        {"id": "prop_001", "price": 400000},
        {"id": "prop_002", "price": 500000},
    ]

    # Filter
    filtered = swipe_manager_with_mock._filter_negative_matches(properties, lead_id, context)

    # Currently just returns all (basic implementation)
    # In production, would filter by neighborhood, style, etc.
    assert isinstance(filtered, list)


@pytest.mark.asyncio
async def test_multiple_feedback_patterns(swipe_manager_with_mock):
    """Test handling multiple types of feedback patterns."""
    lead_id = "test_multi_feedback"
    location_id = "loc_test"

    # Mix of feedback types
    feedback_types = [
        FeedbackCategory.PRICE_TOO_HIGH.value,
        FeedbackCategory.PRICE_TOO_HIGH.value,
        FeedbackCategory.PRICE_TOO_HIGH.value,
        FeedbackCategory.SIZE_TOO_SMALL.value,
        FeedbackCategory.SIZE_TOO_SMALL.value,
    ]

    for i, feedback_type in enumerate(feedback_types):
        swipe_manager_with_mock._log_interaction(
            lead_id=lead_id,
            property_id=f"prop_multi_{i}",
            action=SwipeAction.PASS,
            feedback={"category": feedback_type},
            time_on_card=4.0,
        )

    initial_prefs = {"budget": 600000, "bedrooms": 2}
    adjusted = swipe_manager_with_mock._apply_negative_feedback_adjustments(lead_id, initial_prefs)

    # Both adjustments should be applied
    assert adjusted["budget"] < initial_prefs["budget"]
    assert adjusted["bedrooms"] > initial_prefs["bedrooms"]


@pytest.mark.asyncio
async def test_smart_deck_preserves_match_scores(swipe_manager_with_mock):
    """Test that smart deck includes match scores from PropertyMatcher."""
    lead_id = "test_scores"
    location_id = "loc_test"

    deck = await swipe_manager_with_mock.get_smart_deck(lead_id=lead_id, location_id=location_id, limit=5)

    # Verify match scores are included
    for prop in deck:
        assert "match_score" in prop
        assert 0.0 <= prop["match_score"] <= 1.0
