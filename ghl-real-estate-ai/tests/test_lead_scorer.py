"""
Unit tests for lead scorer service.

Tests the lead qualification scoring algorithm using various scenarios.
"""
import pytest
from services.lead_scorer import LeadScorer


class TestLeadScorer:
    """Test suite for LeadScorer class."""

    @pytest.fixture
    def scorer(self):
        """Create a LeadScorer instance for testing."""
        return LeadScorer()

    def test_calculate_hot_lead_score(self, scorer):
        """Test that a highly qualified lead gets a hot score (70+)."""
        # Arrange: Create context for ideal buyer
        context = {
            "extracted_preferences": {
                "budget": 400000,
                "timeline": "ASAP",
                "location": "Austin",
                "bedrooms": 3,
                "financing": "pre-approved",
                "must_haves": ["pool", "good schools"]
            },
            "conversation_history": [
                {"role": "user", "content": "Looking for a house"},
                {"role": "assistant", "content": "Great! Tell me more"},
                {"role": "user", "content": "Budget is $400k"},
                {"role": "assistant", "content": "Perfect"},
                {"role": "user", "content": "Need to move ASAP"},
                {"role": "assistant", "content": "I can help"},
                {"role": "user", "content": "I'm pre-approved"},
                {"role": "assistant", "content": "Excellent"}
            ]
        }

        # Act
        score = scorer.calculate(context)

        # Assert: Should be 70+
        assert score >= 70, f"Expected hot lead score (70+), got {score}"
        assert score == 100, f"Perfect lead should score 100, got {score}"

    def test_calculate_warm_lead_score(self, scorer):
        """Test that a moderately qualified lead gets a warm score (40-69)."""
        # Arrange: Lead with some info but not all
        context = {
            "extracted_preferences": {
                "budget": 350000,
                "location": "Austin",
                "bedrooms": 2
            },
            "conversation_history": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello"},
                {"role": "user", "content": "Looking for a home"},
                {"role": "assistant", "content": "Great"}
            ]
        }

        # Act
        score = scorer.calculate(context)

        # Assert: Should be 40-69
        assert 40 <= score < 70, f"Expected warm lead score (40-69), got {score}"

    def test_calculate_cold_lead_score(self, scorer):
        """Test that an unqualified lead gets a cold score (0-39)."""
        # Arrange: Minimal information
        context = {
            "extracted_preferences": {},
            "conversation_history": [
                {"role": "user", "content": "Just browsing"},
                {"role": "assistant", "content": "No problem"}
            ]
        }

        # Act
        score = scorer.calculate(context)

        # Assert: Should be < 40
        assert score < 40, f"Expected cold lead score (<40), got {score}"
        assert score == 0, f"No info should score 0, got {score}"

    def test_budget_scoring(self, scorer):
        """Test that budget alone adds 30 points."""
        # Arrange
        context = {
            "extracted_preferences": {"budget": 500000},
            "conversation_history": []
        }

        # Act
        score = scorer.calculate(context)

        # Assert
        assert score == 30, f"Budget alone should score 30, got {score}"

    def test_preapproved_financing_bonus(self, scorer):
        """Test that pre-approved financing adds 15 bonus points."""
        # Arrange
        context = {
            "extracted_preferences": {
                "budget": 400000,
                "financing": "pre-approved"
            },
            "conversation_history": []
        }

        # Act
        score = scorer.calculate(context)

        # Assert
        assert score == 45, f"Budget + pre-approval should score 45 (30+15), got {score}"

    def test_urgent_timeline_bonus(self, scorer):
        """Test that urgent timeline adds 25 + 10 bonus points."""
        # Arrange
        context = {
            "extracted_preferences": {
                "timeline": "ASAP"
            },
            "conversation_history": []
        }

        # Act
        score = scorer.calculate(context)

        # Assert
        assert score == 35, f"Urgent timeline should score 35 (25+10), got {score}"

    def test_non_urgent_timeline(self, scorer):
        """Test that non-urgent timeline adds only 25 points."""
        # Arrange
        context = {
            "extracted_preferences": {
                "timeline": "Maybe next year"
            },
            "conversation_history": []
        }

        # Act
        score = scorer.calculate(context)

        # Assert
        assert score == 25, f"Non-urgent timeline should score 25, got {score}"

    def test_location_scoring(self, scorer):
        """Test that location adds 15 points."""
        # Arrange
        context = {
            "extracted_preferences": {
                "location": "Austin"
            },
            "conversation_history": []
        }

        # Act
        score = scorer.calculate(context)

        # Assert
        assert score == 15, f"Location should score 15, got {score}"

    def test_specific_requirements_scoring(self, scorer):
        """Test that specific requirements add 10 points."""
        # Arrange
        context = {
            "extracted_preferences": {
                "bedrooms": 3,
                "must_haves": ["pool", "good schools"]
            },
            "conversation_history": []
        }

        # Act
        score = scorer.calculate(context)

        # Assert
        assert score == 10, f"Requirements should score 10, got {score}"

    def test_high_engagement_bonus(self, scorer):
        """Test that >3 back-and-forth exchanges add 10 points."""
        # Arrange
        context = {
            "extracted_preferences": {},
            "conversation_history": [
                {"role": "user", "content": "1"},
                {"role": "assistant", "content": "1"},
                {"role": "user", "content": "2"},
                {"role": "assistant", "content": "2"},
                {"role": "user", "content": "3"},
                {"role": "assistant", "content": "3"},
                {"role": "user", "content": "4"},
                {"role": "assistant", "content": "4"}
            ]
        }

        # Act
        score = scorer.calculate(context)

        # Assert
        assert score == 10, f"High engagement should score 10, got {score}"

    def test_score_capped_at_100(self, scorer):
        """Test that score never exceeds 100."""
        # Arrange: Theoretical maximum score scenario
        context = {
            "extracted_preferences": {
                "budget": 500000,
                "financing": "cash",  # 30 + 15
                "timeline": "immediately",  # 25 + 10
                "location": "Austin",  # 15
                "bedrooms": 3,  # 10
                "must_haves": ["pool"]
            },
            "conversation_history": [{"role": "user"}] * 10  # 10
        }

        # Act
        score = scorer.calculate(context)

        # Assert
        assert score <= 100, f"Score should be capped at 100, got {score}"
        assert score == 100, f"Maximum scenario should score 100, got {score}"

    def test_classify_hot_lead(self, scorer):
        """Test lead classification for hot leads."""
        assert scorer.classify(85) == "hot"
        assert scorer.classify(70) == "hot"

    def test_classify_warm_lead(self, scorer):
        """Test lead classification for warm leads."""
        assert scorer.classify(50) == "warm"
        assert scorer.classify(40) == "warm"
        assert scorer.classify(69) == "warm"

    def test_classify_cold_lead(self, scorer):
        """Test lead classification for cold leads."""
        assert scorer.classify(0) == "cold"
        assert scorer.classify(20) == "cold"
        assert scorer.classify(39) == "cold"

    def test_is_urgent_timeline_keywords(self, scorer):
        """Test urgent timeline detection with various keywords."""
        assert scorer._is_urgent_timeline("ASAP") is True
        assert scorer._is_urgent_timeline("Need to move immediately") is True
        assert scorer._is_urgent_timeline("This month") is True
        assert scorer._is_urgent_timeline("Next week") is True
        assert scorer._is_urgent_timeline("Right away") is True

    def test_is_not_urgent_timeline(self, scorer):
        """Test non-urgent timeline detection."""
        assert scorer._is_urgent_timeline("Maybe next year") is False
        assert scorer._is_urgent_timeline("Just browsing") is False
        assert scorer._is_urgent_timeline("Thinking about it") is False
        assert scorer._is_urgent_timeline("") is False

    def test_get_recommended_actions_hot_lead(self, scorer):
        """Test recommended actions for hot leads."""
        actions = scorer.get_recommended_actions(85)
        assert len(actions) > 0
        assert any("Hot Lead" in action for action in actions)
        assert any("24-48 hours" in action for action in actions)

    def test_get_recommended_actions_warm_lead(self, scorer):
        """Test recommended actions for warm leads."""
        actions = scorer.get_recommended_actions(50)
        assert len(actions) > 0
        assert any("Warm Lead" in action for action in actions)
        assert any("24 hours" in action for action in actions)

    def test_get_recommended_actions_cold_lead(self, scorer):
        """Test recommended actions for cold leads."""
        actions = scorer.get_recommended_actions(20)
        assert len(actions) > 0
        assert any("Cold Lead" in action for action in actions)
        assert any("nurture" in action for action in actions)

    def test_calculate_with_reasoning(self, scorer):
        """Test detailed scoring with reasoning."""
        # Arrange
        context = {
            "extracted_preferences": {
                "budget": 400000,
                "location": "Austin",
                "timeline": "June 2025",
                "financing": "pre-approved"
            },
            "conversation_history": []
        }

        # Act
        result = scorer.calculate_with_reasoning(context)

        # Assert
        assert "score" in result
        assert "classification" in result
        assert "reasoning" in result
        assert "recommended_actions" in result
        assert result["score"] > 0
        assert len(result["recommended_actions"]) > 0
        assert "Budget confirmed" in result["reasoning"]
