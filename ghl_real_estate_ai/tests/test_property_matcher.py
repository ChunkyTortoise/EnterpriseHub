"""
Tests for Property Matcher Service
"""

from pathlib import Path

import pytest

from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
from ghl_real_estate_ai.services.property_matching_strategy import BasicFilteringStrategy


def test_load_listings():
    """Test that listings are loaded correctly."""
    matcher = PropertyMatcher()
    assert len(matcher.listings) > 0
    # Accept either Rancho Cucamonga (prop_) or Rancho Cucamonga (rc_) prefixes
    assert matcher.listings[0]["id"].startswith(("prop_", "rc_"))


def test_find_matches_budget():
    """Test matching by budget."""
    matcher = PropertyMatcher()
    # Use higher budget to work with both Rancho Cucamonga and Rancho Cucamonga markets
    matches = matcher.find_matches({"budget": 700000}, limit=1)
    assert len(matches) >= 1
    assert matches[0]["price"] <= 700000


def test_find_matches_location():
    """Test matching by location - uses neighborhood from first listing."""
    matcher = PropertyMatcher()
    # Get the first listing's neighborhood dynamically
    first_listing = matcher.listings[0]
    addr = first_listing.get("address", {})
    if isinstance(addr, dict):
        neighborhood = addr.get("neighborhood", "")
    else:
        neighborhood = first_listing.get("neighborhood", "")

    if neighborhood:
        matches = matcher.find_matches({"location": neighborhood}, limit=1)
        assert len(matches) >= 1
    else:
        # Skip if no neighborhood available
        pytest.skip("No neighborhood available in test data")


def test_calculate_match_score():
    """Test score calculation logic using strategy pattern."""
    strategy = BasicFilteringStrategy()
    prop = {
        "price": 400000,
        "address": {"city": "Rancho Cucamonga", "neighborhood": "Circle C"},
        "bedrooms": 3,
        "property_type": "Single Family",
    }

    # Perfect match
    prefs = {"budget": 400000, "location": "Circle C", "bedrooms": 3, "property_type": "Single Family"}
    score = strategy._calculate_basic_score(prop, prefs)
    assert score > 0.5  # Should be a good match


def test_format_match_for_sms():
    """Test SMS formatting."""
    matcher = PropertyMatcher()
    prop = matcher.listings[0]
    formatted = matcher.format_match_for_sms(prop)
    assert "$" in formatted
    # Check for either format (legacy or sample data)
    assert "Check it out:" in formatted or "/" in formatted
    assert len(formatted) < 200  # Reasonable SMS length
