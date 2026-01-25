"""
Comprehensive tests for Jorge Buyer Bot Implementation
Tests JorgeBuyerBot, BuyerIntentDecoder, and buyer-specific workflows.
Follows proven testing patterns from seller bot tests.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
from ghl_real_estate_ai.agents.buyer_intent_decoder import BuyerIntentDecoder
from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState
from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile

class TestJorgeBuyerBot:
    """Test suite for JorgeBuyerBot implementation."""

    @pytest.fixture
    def mock_buyer_state(self):
        """Create mock buyer state for testing."""
        return {
            "buyer_id": "test_buyer_123",
            "buyer_name": "John Doe",
            "target_areas": None,
            "conversation_history": [
                {"role": "user", "content": "Looking for a 3br house under $400k"},
                {"role": "assistant", "content": "I can help you find that. What's your timeline?"},
                {"role": "user", "content": "Need to move in 3 months, pre-approved for $380k"}
            ],
            "intent_profile": None,
            "budget_range": None,
            "financing_status": "unknown",
            "urgency_level": "browsing",
            "property_preferences": None,
            "current_qualification_step": "budget",
            "objection_detected": False,
            "detected_objection_type": None,
            "next_action": "qualify",
            "response_content": "",
            "financial_readiness_score": 0.0,
            "buying_motivation_score": 0.0,
            "is_qualified": False,
            "current_journey_stage": "discovery",
            "properties_viewed_count": 0,
            "last_action_timestamp": None
        }

    @pytest.fixture
    def mock_buyer_intent_profile(self):
        """Create mock buyer intent profile for testing."""
        return BuyerIntentProfile(
            financial_readiness=75.0,
            budget_clarity=80.0,
            financing_status_score=85.0,
            urgency_score=65.0,
            timeline_pressure=70.0,
            consequence_awareness=60.0,
            preference_clarity=70.0,
            market_realism=75.0,
            decision_authority=80.0,
            buyer_temperature="warm",
            confidence_level=85.0,
            conversation_turns=3,
            key_insights={
                "has_specific_timeline": True,
                "mentions_financing": True,
                "has_clear_preferences": True,
                "shows_urgency": True,
                "decision_maker_identified": True
            },
            next_qualification_step="preferences"
        )

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch.multiple(
            'ghl_real_estate_ai.agents.jorge_buyer_bot',
            BuyerIntentDecoder=AsyncMock,
            ClaudeAssistant=AsyncMock,
            get_event_publisher=Mock,
            PropertyMatcher=AsyncMock,
            get_ml_analytics_engine=Mock
        ) as mocks:
            yield mocks

    @pytest.mark.asyncio
    async def test_buyer_bot_initialization(self, mock_dependencies):
        """Test buyer bot initializes correctly with all dependencies."""
        buyer_bot = JorgeBuyerBot(tenant_id="test_tenant")

        assert buyer_bot.intent_decoder is not None
        assert buyer_bot.claude is not None
        assert buyer_bot.event_publisher is not None
        assert buyer_bot.property_matcher is not None
        assert buyer_bot.ml_analytics is not None
        assert buyer_bot.workflow is not None

    @pytest.mark.asyncio
    async def test_analyze_buyer_intent(self, mock_dependencies, mock_buyer_state, mock_buyer_intent_profile):
        """Test buyer intent analysis workflow node."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.intent_decoder.analyze_buyer = AsyncMock(return_value=mock_buyer_intent_profile)
        buyer_bot.event_publisher.publish_buyer_intent_analysis = AsyncMock()

        result = await buyer_bot.analyze_buyer_intent(mock_buyer_state)

        # Verify intent decoder was called correctly
        buyer_bot.intent_decoder.analyze_buyer.assert_called_once_with(
            mock_buyer_state["buyer_id"],
            mock_buyer_state["conversation_history"]
        )

        # Verify event was published
        buyer_bot.event_publisher.publish_buyer_intent_analysis.assert_called_once()

        # Verify result structure
        assert result["intent_profile"] == mock_buyer_intent_profile
        assert result["financial_readiness_score"] == 75.0
        assert result["buying_motivation_score"] == 65.0
        assert result["current_qualification_step"] == "preferences"
        assert result["buyer_temperature"] == "warm"

    @pytest.mark.asyncio
    async def test_assess_financial_readiness(self, mock_dependencies, mock_buyer_state, mock_buyer_intent_profile):
        """Test financial readiness assessment workflow node."""
        buyer_bot = JorgeBuyerBot()
        mock_buyer_state["intent_profile"] = mock_buyer_intent_profile

        result = await buyer_bot.assess_financial_readiness(mock_buyer_state)

        # Verify financing status classification
        assert result["financing_status"] == "pre_approved"  # Score 85 >= 75
        assert result["financial_readiness_score"] == 75.0

    @pytest.mark.asyncio
    async def test_qualify_property_needs(self, mock_dependencies, mock_buyer_state, mock_buyer_intent_profile):
        """Test property needs qualification workflow node."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot._extract_property_preferences = AsyncMock(return_value={
            "bedrooms": 3,
            "features": ["garage"]
        })
        mock_buyer_state["intent_profile"] = mock_buyer_intent_profile

        result = await buyer_bot.qualify_property_needs(mock_buyer_state)

        # Verify urgency level classification
        assert result["urgency_level"] == "3_months"  # Score 65 >= 50
        assert result["property_preferences"]["bedrooms"] == 3
        assert result["preference_clarity_score"] == 70.0

    @pytest.mark.asyncio
    async def test_match_properties(self, mock_dependencies, mock_buyer_state):
        """Test property matching workflow node."""
        buyer_bot = JorgeBuyerBot()
        mock_properties = [
            {"id": "prop1", "price": 350000, "bedrooms": 3},
            {"id": "prop2", "price": 375000, "bedrooms": 3}
        ]
        buyer_bot.property_matcher.find_matches = AsyncMock(return_value=mock_properties)
        buyer_bot.event_publisher.publish_property_match_update = AsyncMock()

        # Set up qualified buyer state
        mock_buyer_state["property_preferences"] = {"bedrooms": 3}
        mock_buyer_state["budget_range"] = {"min": 700000, "max": 400000}

        result = await buyer_bot.match_properties(mock_buyer_state)

        # Verify property matcher was called correctly
        buyer_bot.property_matcher.find_matches.assert_called_once_with(
            buyer_preferences={"bedrooms": 3},
            budget_range={"min": 700000, "max": 400000},
            max_results=5
        )

        # Verify event was published
        buyer_bot.event_publisher.publish_property_match_update.assert_called_once()

        # Verify result
        assert len(result["matched_properties"]) == 2
        assert result["properties_viewed_count"] == 2
        assert result["next_action"] == "respond"

    @pytest.mark.asyncio
    async def test_match_properties_no_matches(self, mock_dependencies, mock_buyer_state):
        """Test property matching when no properties match."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.property_matcher.find_matches = AsyncMock(return_value=[])
        buyer_bot.event_publisher.publish_property_match_update = AsyncMock()

        mock_buyer_state["property_preferences"] = {"bedrooms": 5}
        mock_buyer_state["budget_range"] = {"min": 200000, "max": 250000}

        result = await buyer_bot.match_properties(mock_buyer_state)

        assert len(result["matched_properties"]) == 0
        assert result["properties_viewed_count"] == 0
        assert result["next_action"] == "educate_market"

    @pytest.mark.asyncio
    async def test_generate_buyer_response(self, mock_dependencies, mock_buyer_state, mock_buyer_intent_profile):
        """Test buyer response generation workflow node."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.claude.generate_response = AsyncMock(return_value={
            "content": "Based on your budget and timeline, I have 3 great properties to show you."
        })

        mock_buyer_state["intent_profile"] = mock_buyer_intent_profile
        mock_buyer_state["matched_properties"] = [{"id": "prop1"}, {"id": "prop2"}]
        mock_buyer_state["financial_readiness_score"] = 75.0

        result = await buyer_bot.generate_buyer_response(mock_buyer_state)

        # Verify Claude was called
        buyer_bot.claude.generate_response.assert_called_once()

        # Verify response structure
        assert "Based on your budget" in result["response_content"]
        assert result["response_tone"] == "consultative"
        assert result["next_action"] == "send_response"

    @pytest.mark.asyncio
    async def test_schedule_next_action(self, mock_dependencies, mock_buyer_state):
        """Test next action scheduling workflow node."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot._schedule_follow_up = AsyncMock()

        # Test qualified buyer (score >= 75)
        mock_buyer_state["financial_readiness_score"] = 80.0

        result = await buyer_bot.schedule_next_action(mock_buyer_state)

        # Verify scheduling was called correctly
        buyer_bot._schedule_follow_up.assert_called_once_with(
            mock_buyer_state["buyer_id"],
            "schedule_property_tour",
            2  # Hot leads get 2 hour follow-up
        )

        assert result["next_action"] == "schedule_property_tour"
        assert result["follow_up_scheduled"] == True
        assert result["follow_up_hours"] == 2

    @pytest.mark.asyncio
    async def test_route_buyer_action(self, mock_dependencies, mock_buyer_state):
        """Test buyer action routing logic."""
        buyer_bot = JorgeBuyerBot()

        # Test qualified buyer with respond action
        mock_buyer_state["next_action"] = "respond"
        mock_buyer_state["financial_readiness_score"] = 60.0
        route = buyer_bot._route_buyer_action(mock_buyer_state)
        assert route == "respond"

        # Test qualified buyer for scheduling
        mock_buyer_state["next_action"] = "qualify_more"
        mock_buyer_state["financial_readiness_score"] = 40.0
        route = buyer_bot._route_buyer_action(mock_buyer_state)
        assert route == "schedule"

        # Test unqualified buyer (end conversation)
        mock_buyer_state["financial_readiness_score"] = 20.0
        route = buyer_bot._route_buyer_action(mock_buyer_state)
        assert route == "end"

    @pytest.mark.asyncio
    async def test_extract_budget_range(self, mock_dependencies):
        """Test budget range extraction from conversation."""
        buyer_bot = JorgeBuyerBot()

        # Test with range
        conversation = [
            {"role": "user", "content": "Looking for something between $300,000 and $450,000"}
        ]
        budget = await buyer_bot._extract_budget_range(conversation)
        assert budget == {"min": 700000, "max": 450000}

        # Test with single amount
        conversation = [
            {"role": "user", "content": "My max budget is $350,000"}
        ]
        budget = await buyer_bot._extract_budget_range(conversation)
        assert budget["max"] == 350000
        assert budget["min"] == int(350000 * 0.8)

        # Test with no amounts
        conversation = [
            {"role": "user", "content": "Looking for a house"}
        ]
        budget = await buyer_bot._extract_budget_range(conversation)
        assert budget is None

    @pytest.mark.asyncio
    async def test_extract_property_preferences(self, mock_dependencies):
        """Test property preferences extraction from conversation."""
        buyer_bot = JorgeBuyerBot()

        conversation = [
            {"role": "user", "content": "Need a 3 bedroom, 2 bathroom house with a garage and pool"}
        ]

        preferences = await buyer_bot._extract_property_preferences(conversation)

        assert preferences["bedrooms"] == 3
        assert preferences["bathrooms"] == 2
        assert "garage" in preferences["features"]
        assert "pool" in preferences["features"]

    @pytest.mark.asyncio
    async def test_process_buyer_conversation_end_to_end(self, mock_dependencies, mock_buyer_intent_profile):
        """Test complete buyer conversation processing workflow."""
        buyer_bot = JorgeBuyerBot()

        # Mock workflow execution
        mock_workflow_result = {
            "buyer_id": "test_buyer_123",
            "intent_profile": mock_buyer_intent_profile,
            "financial_readiness_score": 75.0,
            "buying_motivation_score": 65.0,
            "is_qualified": True,
            "response_content": "Great! Let me show you some properties.",
            "matched_properties": [{"id": "prop1"}, {"id": "prop2"}],
            "current_qualification_step": "property_search",
            "next_action": "respond"
        }

        buyer_bot.workflow.ainvoke = AsyncMock(return_value=mock_workflow_result)
        buyer_bot.event_publisher.publish_buyer_qualification_complete = AsyncMock()

        conversation_history = [
            {"role": "user", "content": "Looking for a 3br house under $400k"},
            {"role": "user", "content": "Pre-approved for $380k, need to move in 3 months"}
        ]

        result = await buyer_bot.process_buyer_conversation(
            buyer_id="test_buyer_123",
            buyer_name="John Doe",
            conversation_history=conversation_history
        )

        # Verify workflow was invoked
        buyer_bot.workflow.ainvoke.assert_called_once()

        # Verify final qualification event was published
        buyer_bot.event_publisher.publish_buyer_qualification_complete.assert_called_once_with(
            contact_id="test_buyer_123",
            qualification_status="qualified",
            final_score=70.0,  # (75 + 65) / 2
            properties_matched=2
        )

        # Verify result structure
        assert result["is_qualified"] == True
        assert result["buyer_id"] == "test_buyer_123"
        assert len(result["matched_properties"]) == 2

    @pytest.mark.asyncio
    async def test_process_buyer_conversation_error_handling(self, mock_dependencies):
        """Test buyer conversation processing with errors."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.workflow.ainvoke = AsyncMock(side_effect=Exception("Workflow error"))

        result = await buyer_bot.process_buyer_conversation(
            buyer_id="test_buyer_123",
            buyer_name="John Doe",
            conversation_history=[]
        )

        # Verify error handling
        assert "error" in result
        assert result["qualification_status"] == "error"
        assert "technical difficulties" in result["response_content"]


class TestBuyerIntentDecoder:
    """Test suite for BuyerIntentDecoder implementation."""

    @pytest.fixture
    def buyer_intent_decoder(self):
        return BuyerIntentDecoder()

    @pytest.fixture
    def qualified_buyer_conversation(self):
        return [
            {"role": "user", "content": "I'm pre-approved for $400k and need to move by March"},
            {"role": "user", "content": "Looking for 3 bedrooms, 2 bathrooms with a garage"},
            {"role": "user", "content": "My wife and I are ready to make a decision this week"}
        ]

    @pytest.fixture
    def unqualified_buyer_conversation(self):
        return [
            {"role": "user", "content": "Just browsing, not sure if I want to buy"},
            {"role": "user", "content": "Maybe someday when prices come down"},
            {"role": "user", "content": "I'll need to talk to my parents about financing"}
        ]

    def test_score_financial_readiness(self, buyer_intent_decoder):
        """Test financial readiness scoring logic."""
        # High readiness text
        high_text = "pre-approved for $400k cash buyer down payment ready"
        score = buyer_intent_decoder._score_financial_readiness(high_text)
        assert score >= 70

        # Medium readiness text
        medium_text = "working with lender getting pre-approved"
        score = buyer_intent_decoder._score_financial_readiness(medium_text)
        assert 40 <= score < 70

        # Low readiness text
        low_text = "not sure about financing need to talk to bank"
        score = buyer_intent_decoder._score_financial_readiness(low_text)
        assert score < 50

    def test_score_budget_clarity(self, buyer_intent_decoder):
        """Test budget clarity scoring logic."""
        # Clear budget text
        clear_text = "my budget is $350,000 max price can afford $400k"
        score = buyer_intent_decoder._score_budget_clarity(clear_text)
        assert score >= 60

        # Vague budget text
        vague_text = "not sure depends on what's available flexible"
        score = buyer_intent_decoder._score_budget_clarity(vague_text)
        assert score < 40

    def test_score_urgency(self, buyer_intent_decoder):
        """Test urgency scoring logic."""
        # High urgency text
        urgent_text = "need to move this month lease ending must buy urgent"
        score = buyer_intent_decoder._score_urgency(urgent_text)
        assert score >= 60

        # Low urgency text
        casual_text = "just looking browsing might buy someday eventually"
        score = buyer_intent_decoder._score_urgency(casual_text)
        assert score < 40

    def test_score_preference_clarity(self, buyer_intent_decoder):
        """Test preference clarity scoring logic."""
        # Specific preferences
        specific_text = "need 3 bedroom 2 bathroom garage pool good schools location"
        score = buyer_intent_decoder._score_preference_clarity(specific_text)
        assert score >= 60

        # Vague preferences
        vague_text = "open to anything flexible whatever available"
        score = buyer_intent_decoder._score_preference_clarity(vague_text)
        assert score < 40

    def test_score_decision_authority(self, buyer_intent_decoder):
        """Test decision authority scoring logic."""
        # Full authority
        authority_text = "I decide my choice my decision I'm buying"
        score = buyer_intent_decoder._score_decision_authority(authority_text)
        assert score >= 60

        # Limited authority
        limited_text = "need approval have to ask my wife decides not my decision"
        score = buyer_intent_decoder._score_decision_authority(limited_text)
        assert score < 50

    def test_classify_buyer_temperature(self, buyer_intent_decoder):
        """Test buyer temperature classification logic."""
        assert buyer_intent_decoder._classify_buyer_temperature(85) == "hot"
        assert buyer_intent_decoder._classify_buyer_temperature(70) == "warm"
        assert buyer_intent_decoder._classify_buyer_temperature(50) == "lukewarm"
        assert buyer_intent_decoder._classify_buyer_temperature(30) == "cold"
        assert buyer_intent_decoder._classify_buyer_temperature(15) == "ice_cold"

    def test_determine_next_qualification_step(self, buyer_intent_decoder):
        """Test next qualification step logic."""
        # Low financial score -> budget
        step = buyer_intent_decoder._determine_next_qualification_step(40, 70, 70, 70)
        assert step == "budget"

        # Low urgency -> timeline
        step = buyer_intent_decoder._determine_next_qualification_step(60, 40, 70, 70)
        assert step == "timeline"

        # Low preferences -> preferences
        step = buyer_intent_decoder._determine_next_qualification_step(60, 60, 40, 70)
        assert step == "preferences"

        # Low authority -> decision_makers
        step = buyer_intent_decoder._determine_next_qualification_step(60, 60, 60, 40)
        assert step == "decision_makers"

        # All high -> property_search
        step = buyer_intent_decoder._determine_next_qualification_step(70, 70, 70, 70)
        assert step == "property_search"

    def test_analyze_qualified_buyer(self, buyer_intent_decoder, qualified_buyer_conversation):
        """Test analysis of qualified buyer conversation."""
        profile = buyer_intent_decoder.analyze_buyer("buyer_123", qualified_buyer_conversation)

        assert profile.buyer_temperature in ["hot", "warm"]
        assert profile.financial_readiness >= 60
        assert profile.urgency_score >= 50
        assert profile.preference_clarity >= 60
        assert profile.decision_authority >= 50

    def test_analyze_unqualified_buyer(self, buyer_intent_decoder, unqualified_buyer_conversation):
        """Test analysis of unqualified buyer conversation."""
        profile = buyer_intent_decoder.analyze_buyer("buyer_456", unqualified_buyer_conversation)

        assert profile.buyer_temperature in ["cold", "ice_cold"]
        assert profile.financial_readiness < 50
        assert profile.urgency_score < 50

    def test_extract_key_insights(self, buyer_intent_decoder):
        """Test key insights extraction."""
        text = "pre-approved for loan need 3 bedroom ready to decide by march"
        insights = buyer_intent_decoder._extract_key_insights(text)

        assert insights["mentions_financing"] == True
        assert insights["has_clear_preferences"] == True  # Has "bedroom"
        assert insights["decision_maker_identified"] == True  # Has "ready to decide"

    def test_create_default_profile(self, buyer_intent_decoder):
        """Test default profile creation for error cases."""
        profile = buyer_intent_decoder._create_default_profile("error_buyer")

        assert profile.buyer_temperature == "cold"
        assert profile.financial_readiness == 25.0
        assert profile.confidence_level == 10.0
        assert profile.next_qualification_step == "budget"


@pytest.mark.integration
class TestBuyerBotIntegration:
    """Integration tests for buyer bot with real dependencies."""

    @pytest.mark.asyncio
    async def test_buyer_workflow_integration(self):
        """Test buyer workflow with mock dependencies but real flow."""
        # This would test with real Redis, database connections, etc.
        # Implementation depends on test environment setup
        pass

    @pytest.mark.asyncio
    async def test_orchestrator_integration(self):
        """Test buyer bot integration with enhanced orchestrator."""
        # This would test the orchestrator calling the buyer bot
        pass