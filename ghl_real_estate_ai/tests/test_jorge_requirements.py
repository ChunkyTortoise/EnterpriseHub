"""
Unit tests for Jorge's specific requirements.

Tests the question-count based lead scoring system.
"""

import pytest

from ghl_real_estate_ai.services.lead_scorer import LeadScorer



class TestJorgeLeadScoring:
    """Test Jorge's lead scoring requirements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = LeadScorer()

    @pytest.mark.asyncio
    async def test_cold_lead_zero_questions(self):
        """Test that 0 questions answered = cold lead."""
        context = {"extracted_preferences": {}, "conversation_history": []}

        score = await self.scorer.calculate(context)
        classification = self.scorer.classify(score)

        assert score == 0, "Should have 0 questions answered"
        assert classification == "cold", "0 questions should be classified as cold"

    @pytest.mark.asyncio
    async def test_cold_lead_one_question(self):
        """Test that 1 question answered = cold lead."""
        context = {"extracted_preferences": {"budget": "700000"}, "conversation_history": []}

        score = await self.scorer.calculate(context)
        classification = self.scorer.classify(score)

        assert score == 1, "Should have 1 question answered"
        assert classification == "cold", "1 question should be classified as cold"

    @pytest.mark.asyncio
    async def test_warm_lead_two_questions(self):
        """Test that 2 questions answered = warm lead."""
        context = {
            "extracted_preferences": {"budget": "700000", "location": "Rancho Cucamonga, CA"},
            "conversation_history": [],
        }

        score = await self.scorer.calculate(context)
        classification = self.scorer.classify(score)

        assert score == 2, "Should have 2 questions answered"
        assert classification == "warm", "2 questions should be classified as warm"

    @pytest.mark.asyncio
    async def test_hot_lead_three_questions(self):
        """Test that 3 questions answered = hot lead."""
        context = {
            "extracted_preferences": {"budget": "700000", "location": "Rancho Cucamonga, CA", "timeline": "3 months"},
            "conversation_history": [],
        }

        score = await self.scorer.calculate(context)
        classification = self.scorer.classify(score)

        assert score == 3, "Should have 3 questions answered"
        assert classification == "hot", "3 questions should be classified as hot"

    @pytest.mark.asyncio
    async def test_hot_lead_four_questions(self):
        """Test that 4+ questions answered = hot lead."""
        context = {
            "extracted_preferences": {
                "budget": "700000",
                "location": "Rancho Cucamonga, CA",
                "timeline": "3 months",
                "bedrooms": 3,
            },
            "conversation_history": [],
        }

        score = await self.scorer.calculate(context)
        classification = self.scorer.classify(score)

        assert score == 4, "Should have 4 questions answered"
        assert classification == "hot", "4 questions should be classified as hot"

    @pytest.mark.asyncio
    async def test_all_seven_questions(self):
        """Test that all 7 questions can be counted."""
        context = {
            "extracted_preferences": {
                "budget": "700000",
                "location": "Rancho Cucamonga, CA",
                "timeline": "3 months",
                "bedrooms": 3,
                "financing": "pre-approved",
                "motivation": "relocating for job",
                "home_condition": "excellent",
            },
            "conversation_history": [],
        }

        score = await self.scorer.calculate(context)
        classification = self.scorer.classify(score)

        assert score == 7, "Should have all 7 questions answered"
        assert classification == "hot", "7 questions should be classified as hot"

    @pytest.mark.asyncio
    async def test_property_requirements_bedrooms_only(self):
        """Test that bedrooms alone counts as property requirement."""
        context = {"extracted_preferences": {"bedrooms": 3}}

        score = await self.scorer.calculate(context)
        assert score == 1, "Bedrooms should count as 1 question"

    @pytest.mark.asyncio
    async def test_property_requirements_bathrooms_only(self):
        """Test that bathrooms alone counts as property requirement."""
        context = {"extracted_preferences": {"bathrooms": 2}}

        score = await self.scorer.calculate(context)
        assert score == 1, "Bathrooms should count as 1 question"

    @pytest.mark.asyncio
    async def test_property_requirements_must_haves_only(self):
        """Test that must_haves alone counts as property requirement."""
        context = {"extracted_preferences": {"must_haves": "pool, garage"}}

        score = await self.scorer.calculate(context)
        assert score == 1, "Must-haves should count as 1 question"

    @pytest.mark.asyncio
    async def test_property_requirements_combined_counts_once(self):
        """Test that beds + baths + must-haves only counts as 1 question."""
        context = {"extracted_preferences": {"bedrooms": 3, "bathrooms": 2, "must_haves": "pool"}}

        score = await self.scorer.calculate(context)
        assert score == 1, "Combined property requirements should count as 1 question"

    @pytest.mark.asyncio
    async def test_calculate_with_reasoning_includes_question_count(self):
        """Test that calculate_with_reasoning includes question count."""
        context = {
            "extracted_preferences": {"budget": "700000", "location": "Rancho Cucamonga, CA", "timeline": "3 months"}
        }

        result = await self.scorer.calculate_with_reasoning(context)

        assert result["score"] == 3
        assert result["questions_answered"] == 3
        assert result["classification"] == "hot"
        assert "Budget" in result["reasoning"]
        assert "Location" in result["reasoning"]
        assert "Timeline" in result["reasoning"]

    @pytest.mark.asyncio
    async def test_no_questions_answered_reasoning(self):
        """Test reasoning when no questions are answered."""
        context = {"extracted_preferences": {}}

        result = await self.scorer.calculate_with_reasoning(context)

        assert result["score"] == 0
        assert result["classification"] == "cold"
        assert result["reasoning"] == "No qualifying questions answered yet"

    def test_recommended_actions_hot_lead(self):
        """Test that hot leads get immediate action recommendations."""
        actions = self.scorer.get_recommended_actions(3)

        assert len(actions) > 0
        assert any("Hot Lead" in action for action in actions)
        assert any("immediately" in action.lower() or "24-48" in action for action in actions)

    def test_recommended_actions_warm_lead(self):
        """Test that warm leads get follow-up recommendations."""
        actions = self.scorer.get_recommended_actions(2)

        assert len(actions) > 0
        assert any("Warm Lead" in action for action in actions)

    def test_recommended_actions_cold_lead(self):
        """Test that cold leads get nurture recommendations."""
        actions = self.scorer.get_recommended_actions(1)

        assert len(actions) > 0
        assert any("Cold Lead" in action for action in actions)
        assert any("nurture" in action.lower() for action in actions)


class TestJorgePhase3:
    """Tests for Phase 3: Qualifying Questions Enhancement."""

    @pytest.fixture
    def manager(self):
        from ghl_real_estate_ai.core.conversation_manager import ConversationManager

        return ConversationManager()

    def test_wholesale_detection(self, manager):
        """Test detection of wholesale intent."""
        assert manager.detect_intent_pathway("I need to sell as-is for cash") == "wholesale"
        assert manager.detect_intent_pathway("looking for a quick cash offer") == "wholesale"
        assert manager.detect_intent_pathway("don't want to fix anything, just sell fast") == "wholesale"

    def test_listing_detection(self, manager):
        """Test detection of listing intent."""
        assert manager.detect_intent_pathway("I want to get the best price for my home") == "listing"
        assert manager.detect_intent_pathway("What's my house worth on the market?") == "listing"
        assert manager.detect_intent_pathway("I want top dollar") == "listing"

    def test_unknown_detection(self, manager):
        """Test unknown intent."""
        assert manager.detect_intent_pathway("I'm thinking about selling") == "unknown"
        assert manager.detect_intent_pathway("How is the market today?") == "unknown"


class TestJorgeScenarios:
    """Test real-world scenarios matching Jorge's use cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = LeadScorer()

    @pytest.mark.asyncio
    async def test_seller_with_home_condition(self):
        """Test seller scenario with home condition question."""
        context = {
            "extracted_preferences": {
                "budget": "400000",  # Selling price
                "location": "Central RC Rancho Cucamonga",
                "timeline": "ASAP",
                "home_condition": "needs repairs",  # Seller-specific
            }
        }

        score = await self.scorer.calculate(context)
        assert score == 4, "Should count home_condition question"
        assert self.scorer.classify(score) == "hot"

    @pytest.mark.asyncio
    async def test_buyer_without_home_condition(self):
        """Test buyer scenario (no home condition)."""
        context = {
            "extracted_preferences": {
                "budget": "400000",
                "location": "Central RC Rancho Cucamonga",
                "timeline": "3-6 months",
                "bedrooms": 3,
                "financing": "pre-approved",
            }
        }

        score = await self.scorer.calculate(context)
        assert score == 5, "Should count 5 questions (no home_condition for buyer)"
        assert self.scorer.classify(score) == "hot"

    @pytest.mark.asyncio
    async def test_engaged_lead_with_motivation(self):
        """Test lead who shares motivation."""
        context = {
            "extracted_preferences": {
                "location": "Rancho Cucamonga",
                "timeline": "soon",
                "motivation": "relocating for new job",
            }
        }

        score = await self.scorer.calculate(context)
        assert score == 3, "Should count motivation question"
        assert self.scorer.classify(score) == "hot"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])