"""
Tests for Property Matcher Service
"""

from pathlib import Path

import pytest

from ghl_real_estate_ai.services.property_matcher import PropertyMatcher


def test_load_listings():
    """Test that listings are loaded correctly."""
    matcher = PropertyMatcher()
    assert len(matcher.listings) > 0
    assert matcher.listings[0]["id"].startswith("prop_")


def test_find_matches_budget():
    """Test matching by budget."""
    matcher = PropertyMatcher()
    # Find something affordable
    matches = matcher.find_matches({"budget": 350000}, limit=1)
    assert len(matches) == 1
    assert matches[0]["price"] <= 350000


def test_find_matches_location():
    """Test matching by location."""
    matcher = PropertyMatcher()
    # Find something in Avery Ranch
    matches = matcher.find_matches({"location": "Avery Ranch"}, limit=1)
    assert len(matches) == 1
    assert matches[0]["address"]["neighborhood"] == "Avery Ranch"


def test_calculate_match_score():
    """Test score calculation logic."""
    matcher = PropertyMatcher()
    prop = {
        "price": 400000,
        "address": {"city": "Austin", "neighborhood": "Circle C"},
        "bedrooms": 3,
        "property_type": "Single Family",
    }

    # Perfect match
    prefs = {"budget": 400000, "location": "Circle C", "bedrooms": 3, "property_type": "Single Family"}
    score = matcher._calculate_match_score(prop, prefs)
    assert score == pytest.approx(1.0)

    # Partial match
    prefs = {
        "budget": 300000,  # Too expensive
        "location": "Circle C",
        "bedrooms": 3,
        "property_type": "Single Family",
    }
    score = matcher._calculate_match_score(prop, prefs)
    assert score < 1.0
    assert score > 0.5


def test_format_match_for_sms():
    """Test SMS formatting."""
    matcher = PropertyMatcher()
    prop = matcher.listings[0]
    formatted = matcher.format_match_for_sms(prop)
    assert "$" in formatted
    assert "Check it out:" in formatted
    assert len(formatted) < 160
