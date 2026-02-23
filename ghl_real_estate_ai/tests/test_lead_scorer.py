"""
Unit tests for lead scorer service.

Tests the lead qualification scoring algorithm using Jorge's Question Count methodology.
"""

import pytest

from ghl_real_estate_ai.services.lead_scorer import LeadScorer


class TestLeadScorer:
    """Test suite for LeadScorer class using Question Count scoring."""

    @pytest.fixture
    def scorer(self):
        """Create a LeadScorer instance for testing."""
        return LeadScorer()

    async def test_calculate_hot_lead_score(self, scorer):
        """Test that 3+ questions answered results in a hot score."""
        context = {"extracted_preferences": {"budget": 400000, "location": "Rancho Cucamonga", "timeline": "ASAP"}}
        score = await scorer.calculate(context)
        assert score == 3
        assert scorer.classify(score) == "hot"

    async def test_calculate_warm_lead_score(self, scorer):
        """Test that 2 questions answered results in a warm score."""
        context = {"extracted_preferences": {"budget": 350000, "location": "Rancho Cucamonga"}}
        score = await scorer.calculate(context)
        assert score == 2
        assert scorer.classify(score) == "warm"

    async def test_calculate_cold_lead_score(self, scorer):
        """Test that 0-1 questions answered results in a cold score."""
        # 1 question
        context = {"extracted_preferences": {"budget": 500000}}
        score = await scorer.calculate(context)
        assert score == 1
        assert scorer.classify(score) == "cold"

        # 0 questions
        context = {"extracted_preferences": {}}
        score = await scorer.calculate(context)
        assert score == 0
        assert scorer.classify(score) == "cold"

    async def test_property_requirements_scoring(self, scorer):
        """Test that property requirements (beds/baths/must_haves) count as 1 question."""
        context = {"extracted_preferences": {"bedrooms": 3, "bathrooms": 2, "must_haves": ["pool"]}}
        # Multiple property requirements still only count as ONE qualifying category (Question 4)
        score = await scorer.calculate(context)
        assert score == 1

    async def test_full_qualification_score(self, scorer):
        """Test that all 7 questions answered results in a score of 7."""
        context = {
            "extracted_preferences": {
                "budget": 500000,
                "location": "Rancho Cucamonga",
                "timeline": "ASAP",
                "bedrooms": 3,
                "financing": "pre-approved",
                "motivation": "relocating",
                "home_condition": "excellent",
            }
        }
        score = await scorer.calculate(context)
        assert score == 7
        assert scorer.classify(score) == "hot"

    def test_classify_thresholds(self, scorer):
        """Test classification at boundary thresholds."""
        assert scorer.classify(3) == "hot"
        assert scorer.classify(2) == "warm"
        assert scorer.classify(1) == "cold"
        assert scorer.classify(0) == "cold"
        assert scorer.classify(7) == "hot"

    def test_get_recommended_actions(self, scorer):
        """Test recommended actions for each classification."""
        # Hot
        actions = scorer.get_recommended_actions(3)
        assert any("Hot Lead" in action for action in actions)

        # Warm
        actions = scorer.get_recommended_actions(2)
        assert any("Warm Lead" in action for action in actions)

        # Cold
        actions = scorer.get_recommended_actions(1)
        assert any("Cold Lead" in action for action in actions)

    async def test_calculate_with_reasoning(self, scorer):
        """Test reasoning breakdown for partial qualification."""
        context = {"extracted_preferences": {"budget": 400000, "location": "Rancho Cucamonga"}}
        result = await scorer.calculate_with_reasoning(context)
        assert result["score"] == 2
        assert "Budget: $400,000" in result["reasoning"]
        assert "Location: Rancho Cucamonga" in result["reasoning"]
        assert result["classification"] == "warm"
