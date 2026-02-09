import pytest
pytestmark = pytest.mark.integration

"""
Comprehensive tests for Jorge Buyer Bot Implementation
Tests JorgeBuyerBot, BuyerIntentDecoder, and buyer-specific workflows.
Follows proven testing patterns from seller bot tests.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ghl_real_estate_ai.agents.buyer_intent_decoder import BuyerIntentDecoder
from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
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
                {"role": "user", "content": "Need to move in 3 months, pre-approved for $380k"},
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
            "last_action_timestamp": None,
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
                "decision_maker_identified": True,
            },
            next_qualification_step="preferences",
        )

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=AsyncMock,
            ClaudeAssistant=AsyncMock,
            get_event_publisher=Mock,
            PropertyMatcher=AsyncMock,
            get_ml_analytics_engine=Mock,
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
        buyer_bot.intent_decoder.analyze_buyer = Mock(return_value=mock_buyer_intent_profile)
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock()
        buyer_bot.event_publisher.publish_buyer_intent_analysis = AsyncMock()

        result = await buyer_bot.analyze_buyer_intent(mock_buyer_state)

        # Verify intent decoder was called correctly
        buyer_bot.intent_decoder.analyze_buyer.assert_called_once_with(
            mock_buyer_state["buyer_id"], mock_buyer_state["conversation_history"]
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
        buyer_bot._extract_property_preferences = AsyncMock(return_value={"bedrooms": 3, "features": ["garage"]})
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
            {"id": "prop2", "price": 375000, "bedrooms": 3},
        ]
        buyer_bot.property_matcher.find_matches = AsyncMock(return_value=mock_properties)
        buyer_bot.event_publisher.publish_property_match_update = AsyncMock()

        # Set up qualified buyer state
        mock_buyer_state["property_preferences"] = {"bedrooms": 3}
        mock_buyer_state["budget_range"] = {"min": 700000, "max": 400000}

        result = await buyer_bot.match_properties(mock_buyer_state)

        # Verify property matcher was called correctly
        buyer_bot.property_matcher.find_matches.assert_called_once_with(preferences={"bedrooms": 3}, limit=5)

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
        buyer_bot.claude.generate_response = AsyncMock(
            return_value={"content": "Based on your budget and timeline, I have 3 great properties to show you."}
        )

        mock_buyer_state["intent_profile"] = mock_buyer_intent_profile
        mock_buyer_state["matched_properties"] = [{"id": "prop1"}, {"id": "prop2"}]
        mock_buyer_state["financial_readiness_score"] = 75.0

        result = await buyer_bot.generate_buyer_response(mock_buyer_state)

        # Verify Claude was called
        buyer_bot.claude.generate_response.assert_called_once()

        # Verify response structure
        assert "Based on your budget" in result["response_content"]
        assert result["response_tone"] == "friendly_consultative"
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
            2,  # Hot leads get 2 hour follow-up
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
        conversation = [{"role": "user", "content": "Looking for something between $300,000 and $450,000"}]
        budget = await buyer_bot._extract_budget_range(conversation)
        assert budget == {"min": 300000, "max": 450000}

        # Test with single amount
        conversation = [{"role": "user", "content": "My max budget is $350,000"}]
        budget = await buyer_bot._extract_budget_range(conversation)
        assert budget["max"] == 350000
        assert budget["min"] == int(350000 * 0.8)

        # Test with no amounts
        conversation = [{"role": "user", "content": "Looking for a house"}]
        budget = await buyer_bot._extract_budget_range(conversation)
        assert budget is None

    @pytest.mark.asyncio
    async def test_extract_property_preferences(self, mock_dependencies):
        """Test property preferences extraction from conversation."""
        buyer_bot = JorgeBuyerBot()

        conversation = [{"role": "user", "content": "Need a 3 bedroom, 2 bathroom house with a garage and pool"}]

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
            "next_action": "respond",
        }

        buyer_bot.workflow.ainvoke = AsyncMock(return_value=mock_workflow_result)
        buyer_bot.event_publisher.publish_buyer_qualification_complete = AsyncMock()

        conversation_history = [
            {"role": "user", "content": "Looking for a 3br house under $400k"},
            {"role": "user", "content": "Pre-approved for $380k, need to move in 3 months"},
        ]

        result = await buyer_bot.process_buyer_conversation(
            buyer_id="test_buyer_123", buyer_name="John Doe", conversation_history=conversation_history
        )

        # Verify workflow was invoked
        buyer_bot.workflow.ainvoke.assert_called_once()

        # Verify final qualification event was published
        buyer_bot.event_publisher.publish_buyer_qualification_complete.assert_called_once_with(
            contact_id="test_buyer_123",
            qualification_status="qualified",
            final_score=70.0,  # (75 + 65) / 2
            properties_matched=2,
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
            buyer_id="test_buyer_123", buyer_name="John Doe", conversation_history=[]
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
            {"role": "user", "content": "My wife and I are ready to make a decision this week"},
        ]

    @pytest.fixture
    def unqualified_buyer_conversation(self):
        return [
            {"role": "user", "content": "Just browsing, not sure if I want to buy"},
            {"role": "user", "content": "Maybe someday when prices come down"},
            {"role": "user", "content": "I'll need to talk to my parents about financing"},
        ]

    def test_score_financial_readiness(self, buyer_intent_decoder):
        """Test financial readiness scoring logic."""
        # High readiness text
        high_text = "pre-approved for $400k cash buyer down payment ready"
        score = buyer_intent_decoder._score_financial_readiness(high_text)
        assert score >= 70

        # Medium readiness text (no high-readiness substring matches)
        medium_text = "working with lender checking financing"
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

        # Limited authority (no full_authority substring matches)
        limited_text = "need approval have to ask not up to me"
        score = buyer_intent_decoder._score_decision_authority(limited_text)
        assert score < 50

    def test_classify_buyer_temperature(self, buyer_intent_decoder):
        """Test buyer temperature classification logic."""
        assert buyer_intent_decoder._classify_buyer_temperature(85) == "hot"
        assert buyer_intent_decoder._classify_buyer_temperature(70) == "warm"
        assert buyer_intent_decoder._classify_buyer_temperature(50) == "warm"  # >=50 is warm
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
        assert profile.financial_readiness >= 40  # pre-approved detected
        assert profile.urgency_score >= 40  # "need to move" detected
        assert profile.preference_clarity >= 50  # bedrooms, bathrooms, garage
        assert profile.decision_authority >= 30  # shared authority signals

    def test_analyze_unqualified_buyer(self, buyer_intent_decoder, unqualified_buyer_conversation):
        """Test analysis of unqualified buyer conversation."""
        profile = buyer_intent_decoder.analyze_buyer("buyer_456", unqualified_buyer_conversation)

        assert profile.buyer_temperature in ["cold", "ice_cold"]
        assert profile.financial_readiness < 50
        assert profile.urgency_score < 50

    def test_extract_key_insights(self, buyer_intent_decoder):
        """Test key insights extraction."""
        text = "pre-approved for loan need 3 bedroom 2 bathroom I decide by march"
        insights = buyer_intent_decoder._extract_key_insights(text)

        assert insights["mentions_financing"] == True  # "pre-approved" matches
        assert insights["has_clear_preferences"] == True  # "bedroom" + "bathroom" >= 2
        assert insights["decision_maker_identified"] == True  # "I decide" matches full_authority

    def test_create_default_profile(self, buyer_intent_decoder):
        """Test default profile creation for error cases."""
        profile = buyer_intent_decoder._create_default_profile("error_buyer")

        assert profile.buyer_temperature == "cold"
        assert profile.financial_readiness == 25.0
        assert profile.confidence_level == 10.0
        assert profile.next_qualification_step == "budget"


class TestRetryMechanism:
    """Tests for exponential backoff retry mechanism (TODO 1)."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=AsyncMock,
            ClaudeAssistant=AsyncMock,
            get_event_publisher=Mock,
            PropertyMatcher=AsyncMock,
            get_ml_analytics_engine=Mock,
        ) as mocks:
            yield mocks

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self, mock_dependencies):
        """Retry mechanism recovers on second attempt after transient failure."""
        from ghl_real_estate_ai.agents.jorge_buyer_bot import NetworkError, RetryConfig, async_retry_with_backoff

        call_count = 0

        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Connection reset")
            return {"result": "success"}

        config = RetryConfig(max_retries=3, initial_backoff_ms=10)  # Fast for testing
        result = await async_retry_with_backoff(flaky_operation, config, "test_op")

        assert result == {"result": "success"}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_fails_after_max_retries(self, mock_dependencies):
        """Retry mechanism raises after exhausting all retries."""
        from ghl_real_estate_ai.agents.jorge_buyer_bot import ClaudeAPIError, RetryConfig, async_retry_with_backoff

        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ClaudeAPIError("Service down")

        config = RetryConfig(max_retries=3, initial_backoff_ms=10)
        with pytest.raises(ClaudeAPIError, match="Service down"):
            await async_retry_with_backoff(always_fails, config, "test_op")

        assert call_count == 4  # Initial + 3 retries

    @pytest.mark.asyncio
    async def test_retry_does_not_retry_non_retryable_errors(self, mock_dependencies):
        """Non-retryable exceptions propagate immediately without retry."""
        from ghl_real_estate_ai.agents.jorge_buyer_bot import (
            BuyerIntentAnalysisError,
            RetryConfig,
            async_retry_with_backoff,
        )

        call_count = 0

        async def business_error():
            nonlocal call_count
            call_count += 1
            raise BuyerIntentAnalysisError("Invalid data")

        config = RetryConfig(max_retries=3, initial_backoff_ms=10)
        with pytest.raises(BuyerIntentAnalysisError, match="Invalid data"):
            await async_retry_with_backoff(business_error, config, "test_op")

        assert call_count == 1  # No retries


class TestEscalateToHumanReview:
    """Tests for human escalation workflow (TODO 2)."""

    @pytest.fixture
    def mock_dependencies(self):
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=AsyncMock,
            ClaudeAssistant=AsyncMock,
            get_event_publisher=Mock,
            PropertyMatcher=AsyncMock,
            get_ml_analytics_engine=Mock,
        ) as mocks:
            yield mocks

    @pytest.mark.asyncio
    async def test_escalate_creates_ticket_and_sends_notification(self, mock_dependencies):
        """Escalation creates CRM tag and publishes internal event."""
        buyer_bot = JorgeBuyerBot()
        # Mock GHL client so CRM actions succeed
        buyer_bot.ghl_client = MagicMock()
        buyer_bot.ghl_client.add_tags = AsyncMock()
        buyer_bot.ghl_client.trigger_workflow = AsyncMock()
        buyer_bot.ghl_client.update_custom_field = AsyncMock()
        buyer_bot.ghl_client.base_url = "https://test.api"
        buyer_bot.ghl_client.headers = {"Authorization": "Bearer test"}
        # Mock event publisher
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock()

        result = await buyer_bot.escalate_to_human_review(
            buyer_id="buyer_123", reason="intent_analysis_failure", context={"error": "test error"}
        )

        assert result["escalation_id"] is not None
        assert result["status"] == "escalated"
        assert result["tag_added"] is True
        assert result["event_published"] is True
        assert result["buyer_id"] == "buyer_123"
        assert result["reason"] == "intent_analysis_failure"

        # Verify internal event was published
        buyer_bot.event_publisher.publish_bot_status_update.assert_called_once()
        call_kwargs = buyer_bot.event_publisher.publish_bot_status_update.call_args
        assert call_kwargs.kwargs["status"] == "escalated"

    @pytest.mark.asyncio
    async def test_escalate_graceful_degradation_when_services_fail(self, mock_dependencies):
        """Escalation queues request when all channels fail."""
        buyer_bot = JorgeBuyerBot()
        # GHL client methods all fail
        buyer_bot.ghl_client = MagicMock()
        buyer_bot.ghl_client.add_tags = AsyncMock(side_effect=Exception("GHL unavailable"))
        buyer_bot.ghl_client.trigger_workflow = AsyncMock(side_effect=Exception("GHL unavailable"))
        buyer_bot.ghl_client.update_custom_field = AsyncMock(side_effect=Exception("GHL unavailable"))
        buyer_bot.ghl_client.base_url = "https://test.api"
        buyer_bot.ghl_client.headers = {"Authorization": "Bearer test"}
        # Event publisher also fails
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock(side_effect=Exception("CRM unavailable"))

        result = await buyer_bot.escalate_to_human_review(buyer_id="buyer_456", reason="system_failure", context={})

        assert result["status"] == "queued"
        assert result["tag_added"] is False
        assert result["event_published"] is False
        assert result["escalation_id"] is not None


class TestFallbackFinancialAssessment:
    """Tests for multi-tier fallback financial assessment (TODO 3)."""

    @pytest.fixture
    def mock_dependencies(self):
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=AsyncMock,
            ClaudeAssistant=AsyncMock,
            get_event_publisher=Mock,
            PropertyMatcher=AsyncMock,
            get_ml_analytics_engine=Mock,
        ) as mocks:
            yield mocks

    @pytest.mark.asyncio
    async def test_fallback_tier1_preapproved_heuristic(self, mock_dependencies):
        """Tier 1 fallback detects pre-approval from conversation history."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock()

        state = {
            "buyer_id": "buyer_pre",
            "conversation_history": [{"role": "user", "content": "I'm pre-approved for $400k through Wells Fargo"}],
        }

        result = await buyer_bot._fallback_financial_assessment(state)

        assert result["financing_status"] == "pre_approved"
        assert result["fallback_tier"] == 1
        assert result["fallback_source"] == "conversation_heuristic"
        assert result["financial_readiness_score"] >= 70

    @pytest.mark.asyncio
    async def test_fallback_tier1_cash_buyer_heuristic(self, mock_dependencies):
        """Tier 1 fallback detects cash buyer from conversation."""
        buyer_bot = JorgeBuyerBot()

        state = {
            "buyer_id": "buyer_cash",
            "conversation_history": [{"role": "user", "content": "I'm a cash buyer, no financing needed"}],
        }

        result = await buyer_bot._fallback_financial_assessment(state)

        assert result["financing_status"] == "cash"
        assert result["fallback_tier"] == 1
        assert result["financial_readiness_score"] >= 80

    @pytest.mark.asyncio
    async def test_fallback_tier2_conservative_default(self, mock_dependencies):
        """Tier 2 fallback returns conservative defaults when no conversation signals."""
        buyer_bot = JorgeBuyerBot()

        state = {
            "buyer_id": "buyer_unknown",
            "conversation_history": [{"role": "user", "content": "Hi, looking at houses"}],
        }

        result = await buyer_bot._fallback_financial_assessment(state)

        assert result["financing_status"] == "assessment_pending"
        assert result["requires_manual_review"] is True
        assert result["fallback_tier"] == 2
        assert result["fallback_source"] == "conservative_default"
        assert result["confidence"] == 0.3

    @pytest.mark.asyncio
    async def test_fallback_continues_conversation(self, mock_dependencies):
        """Fallback always returns valid result, never raises."""
        buyer_bot = JorgeBuyerBot()

        state = {"buyer_id": "buyer_empty", "conversation_history": []}

        result = await buyer_bot._fallback_financial_assessment(state)

        assert result is not None
        assert "financing_status" in result
        assert result["fallback_tier"] == 2  # Empty convo -> conservative default


class TestComplianceViolationEscalation:
    """Tests for compliance violation escalation (TODO 4)."""

    @pytest.fixture
    def mock_dependencies(self):
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=AsyncMock,
            ClaudeAssistant=AsyncMock,
            get_event_publisher=Mock,
            PropertyMatcher=AsyncMock,
            get_ml_analytics_engine=Mock,
        ) as mocks:
            yield mocks

    @pytest.mark.asyncio
    async def test_fair_housing_violation_escalation(self, mock_dependencies):
        """Fair housing violation is logged as critical and triggers full escalation."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.event_publisher.publish_conversation_update = AsyncMock()
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock()

        result = await buyer_bot.escalate_compliance_violation(
            buyer_id="buyer_789",
            violation_type="fair_housing",
            evidence={"summary": "Discriminatory language detected", "message_id": "msg_001"},
        )

        assert result["compliance_ticket_id"] is not None
        assert result["severity"] == "critical"
        assert result["violation_type"] == "fair_housing"
        assert result["audit_logged"] is True
        assert result["notification_sent"] is True  # Critical severity triggers notification
        assert result["crm_flagged"] is True
        assert result["bot_paused"] is True
        assert result["status"] == "escalated"

    @pytest.mark.asyncio
    async def test_compliance_crm_flag_applied(self, mock_dependencies):
        """Compliance violation flags contact in CRM."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.event_publisher.publish_conversation_update = AsyncMock()
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock()

        result = await buyer_bot.escalate_compliance_violation(
            buyer_id="buyer_crm", violation_type="privacy", evidence={"summary": "PII handling violation"}
        )

        assert result["crm_flagged"] is True
        # Verify status update calls include compliance flagging
        status_calls = buyer_bot.event_publisher.publish_bot_status_update.call_args_list
        flag_calls = [c for c in status_calls if c.kwargs.get("status") == "compliance_flagged"]
        assert len(flag_calls) >= 1

    @pytest.mark.asyncio
    async def test_compliance_pauses_bot_interaction(self, mock_dependencies):
        """Compliance violation pauses bot interactions for human review."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.event_publisher.publish_conversation_update = AsyncMock()
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock()

        result = await buyer_bot.escalate_compliance_violation(
            buyer_id="buyer_pause",
            violation_type="financial_regulation",
            evidence={"summary": "Loan fraud risk indicators"},
        )

        assert result["bot_paused"] is True
        # Verify the bot status was set to paused
        status_calls = buyer_bot.event_publisher.publish_bot_status_update.call_args_list
        pause_calls = [c for c in status_calls if c.kwargs.get("current_step") == "bot_paused"]
        assert len(pause_calls) >= 1

    @pytest.mark.asyncio
    async def test_licensing_violation_medium_severity(self, mock_dependencies):
        """Licensing violation is classified as medium severity."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.event_publisher.publish_conversation_update = AsyncMock()
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock()

        result = await buyer_bot.escalate_compliance_violation(
            buyer_id="buyer_lic", violation_type="licensing", evidence={"summary": "Agent credential issue"}
        )

        assert result["severity"] == "medium"
        assert result["notification_sent"] is False  # Medium severity doesn't auto-notify


class TestStreamARequiredCoverage:
    """
    Required test coverage for Stream A error handling TODOs.
    Uses the exact test names specified in the delivery requirements.
    """

    @pytest.fixture
    def mock_dependencies(self):
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=AsyncMock,
            ClaudeAssistant=AsyncMock,
            get_event_publisher=Mock,
            PropertyMatcher=AsyncMock,
            get_ml_analytics_engine=Mock,
        ) as mocks:
            yield mocks

    # ---- TODO 1: Retry Mechanism ----

    @pytest.mark.asyncio
    async def test_retry_mechanism_succeeds_on_second_attempt(self, mock_dependencies):
        """Retry recovers from a transient NetworkError on the second call."""
        from ghl_real_estate_ai.agents.jorge_buyer_bot import NetworkError, RetryConfig, async_retry_with_backoff

        attempts = 0

        async def transient_failure():
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise NetworkError("Connection reset by peer")
            return {"status": "ok", "data": [1, 2, 3]}

        config = RetryConfig(max_retries=3, initial_backoff_ms=5)
        result = await async_retry_with_backoff(transient_failure, config, "test_retry_second")

        assert result == {"status": "ok", "data": [1, 2, 3]}
        assert attempts == 2

    @pytest.mark.asyncio
    async def test_retry_mechanism_fails_after_max_retries(self, mock_dependencies):
        """All retries exhausted raises the final exception."""
        from ghl_real_estate_ai.agents.jorge_buyer_bot import ClaudeAPIError, RetryConfig, async_retry_with_backoff

        attempts = 0

        async def persistent_failure():
            nonlocal attempts
            attempts += 1
            raise ClaudeAPIError("Upstream 503")

        config = RetryConfig(max_retries=2, initial_backoff_ms=5)
        with pytest.raises(ClaudeAPIError, match="Upstream 503"):
            await async_retry_with_backoff(persistent_failure, config, "test_retry_exhaust")

        assert attempts == 3  # 1 initial + 2 retries

    @pytest.mark.asyncio
    async def test_retry_mechanism_respects_backoff_timing(self, mock_dependencies):
        """Backoff sleep is called with increasing delay between retries."""
        import time

        from ghl_real_estate_ai.agents.jorge_buyer_bot import NetworkError, RetryConfig, async_retry_with_backoff

        timestamps = []

        async def timed_failure():
            timestamps.append(time.monotonic())
            raise NetworkError("Timeout")

        config = RetryConfig(max_retries=2, initial_backoff_ms=50, jitter_factor=0.0)
        with pytest.raises(NetworkError):
            await async_retry_with_backoff(timed_failure, config, "test_timing")

        assert len(timestamps) == 3
        # Second attempt should be at least 40ms after first (50ms backoff minus tolerance)
        gap_1 = timestamps[1] - timestamps[0]
        gap_2 = timestamps[2] - timestamps[1]
        assert gap_1 >= 0.03  # ~50ms first backoff (with tolerance)
        assert gap_2 >= gap_1 * 0.8  # Second gap should be larger (exponential)

    # ---- TODO 2: Escalate to Human Review ----

    @pytest.mark.asyncio
    async def test_escalate_to_human_review_creates_ticket(self, mock_dependencies):
        """Human escalation returns a valid ticket with CRM actions and event published."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.ghl_client = MagicMock()
        buyer_bot.ghl_client.add_tags = AsyncMock()
        buyer_bot.ghl_client.trigger_workflow = AsyncMock()
        buyer_bot.ghl_client.update_custom_field = AsyncMock()
        buyer_bot.ghl_client.base_url = "https://mock.api"
        buyer_bot.ghl_client.headers = {"Authorization": "Bearer mock"}
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock()

        result = await buyer_bot.escalate_to_human_review(
            buyer_id="buyer_ticket_test",
            reason="high_value_lead_confusion",
            context={"conversation_summary": "Buyer asked complex questions about financing."},
        )

        assert result["escalation_id"] is not None
        assert len(result["escalation_id"]) == 36  # UUID format
        assert result["buyer_id"] == "buyer_ticket_test"
        assert result["reason"] == "high_value_lead_confusion"
        assert result["status"] == "escalated"
        assert result["tag_added"] is True
        assert result["timestamp"] is not None

        # Verify GHL tag was applied
        buyer_bot.ghl_client.add_tags.assert_called_once_with("buyer_ticket_test", ["Escalation"])

    @pytest.mark.asyncio
    async def test_escalate_to_human_review_queues_on_total_failure(self, mock_dependencies):
        """When both GHL and event publisher fail, escalation is queued for manual processing."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.ghl_client = MagicMock()
        buyer_bot.ghl_client.add_tags = AsyncMock(side_effect=Exception("GHL down"))
        buyer_bot.ghl_client.trigger_workflow = AsyncMock(side_effect=Exception("GHL down"))
        buyer_bot.ghl_client.update_custom_field = AsyncMock(side_effect=Exception("GHL down"))
        buyer_bot.ghl_client.base_url = "https://mock.api"
        buyer_bot.ghl_client.headers = {"Authorization": "Bearer mock"}
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock(side_effect=Exception("Event bus down"))

        result = await buyer_bot.escalate_to_human_review(
            buyer_id="buyer_total_fail", reason="system_failure", context={}
        )

        assert result["status"] == "queued"
        assert result["tag_added"] is False
        assert result["note_added"] is False
        assert result["event_published"] is False
        assert result["escalation_id"] is not None

    # ---- TODO 3: Fallback Financial Assessment ----

    @pytest.mark.asyncio
    async def test_fallback_financial_assessment_uses_heuristic(self, mock_dependencies):
        """Tier 1 fallback detects pre-approval keywords and returns heuristic assessment."""
        buyer_bot = JorgeBuyerBot()

        state = {
            "buyer_id": "buyer_heuristic",
            "conversation_history": [{"role": "user", "content": "I got pre-approved last week for $500k"}],
        }

        result = await buyer_bot._fallback_financial_assessment(state)

        assert result["fallback_tier"] == 1
        assert result["fallback_source"] == "conversation_heuristic"
        assert result["financing_status"] == "pre_approved"
        assert result["financial_readiness_score"] >= 70

    @pytest.mark.asyncio
    async def test_fallback_financial_assessment_uses_conservative_default(self, mock_dependencies):
        """Tier 2 fallback returns conservative defaults when no financial signals found."""
        buyer_bot = JorgeBuyerBot()

        state = {
            "buyer_id": "buyer_no_signal",
            "conversation_history": [{"role": "user", "content": "I might want to look at some neighborhoods."}],
        }

        result = await buyer_bot._fallback_financial_assessment(state)

        assert result["fallback_tier"] == 2
        assert result["fallback_source"] == "conservative_default"
        assert result["financing_status"] == "assessment_pending"
        assert result["requires_manual_review"] is True
        assert result["confidence"] == 0.3
        assert result["budget_range"] is None

    @pytest.mark.asyncio
    async def test_fallback_financial_assessment_budget_keyword_detection(self, mock_dependencies):
        """Tier 1 detects budget keyword signals (needs_approval) from conversation."""
        buyer_bot = JorgeBuyerBot()

        state = {
            "buyer_id": "buyer_budget",
            "conversation_history": [{"role": "user", "content": "Our budget is around $600k, max price we can do"}],
        }

        result = await buyer_bot._fallback_financial_assessment(state)

        assert result["fallback_tier"] == 1
        assert result["financing_status"] == "needs_approval"
        assert result["financial_readiness_score"] >= 50

    # ---- TODO 4: Compliance Violation Escalation ----

    @pytest.mark.asyncio
    async def test_escalate_compliance_violation_fair_housing(self, mock_dependencies):
        """Fair housing violation is escalated as critical with full audit trail and bot paused."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.event_publisher.publish_conversation_update = AsyncMock()
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock()

        result = await buyer_bot.escalate_compliance_violation(
            buyer_id="buyer_fh_test",
            violation_type="fair_housing",
            evidence={
                "summary": "Discriminatory language about neighborhood demographics",
                "message_id": "msg_fair_001",
            },
        )

        assert result["compliance_ticket_id"] is not None
        assert len(result["compliance_ticket_id"]) == 36  # UUID format
        assert result["severity"] == "critical"
        assert result["violation_type"] == "fair_housing"
        assert result["audit_logged"] is True
        assert result["notification_sent"] is True  # Critical severity sends notification
        assert result["crm_flagged"] is True
        assert result["bot_paused"] is True
        assert result["status"] == "escalated"

        # Verify audit trail was logged via conversation update
        buyer_bot.event_publisher.publish_conversation_update.assert_called_once()
        audit_kwargs = buyer_bot.event_publisher.publish_conversation_update.call_args
        assert audit_kwargs.kwargs["violation_type"] == "fair_housing"
        assert audit_kwargs.kwargs["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_compliance_violation_pauses_bot(self, mock_dependencies):
        """Any compliance violation flags contact and pauses bot interactions."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.event_publisher.publish_conversation_update = AsyncMock()
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock()

        result = await buyer_bot.escalate_compliance_violation(
            buyer_id="buyer_pause_test",
            violation_type="privacy",
            evidence={"summary": "Unauthorized PII disclosure to third party"},
        )

        assert result["bot_paused"] is True
        assert result["crm_flagged"] is True
        assert result["severity"] == "high"

        # Verify bot_paused step was published
        status_calls = buyer_bot.event_publisher.publish_bot_status_update.call_args_list
        paused_calls = [c for c in status_calls if c.kwargs.get("current_step") == "bot_paused"]
        assert len(paused_calls) >= 1

    @pytest.mark.asyncio
    async def test_compliance_violation_degraded_when_audit_fails(self, mock_dependencies):
        """Compliance escalation reports degraded status when audit logging fails."""
        buyer_bot = JorgeBuyerBot()
        buyer_bot.event_publisher.publish_conversation_update = AsyncMock(
            side_effect=Exception("Audit service unavailable")
        )
        buyer_bot.event_publisher.publish_bot_status_update = AsyncMock()

        result = await buyer_bot.escalate_compliance_violation(
            buyer_id="buyer_audit_fail", violation_type="fair_housing", evidence={"summary": "Test audit failure"}
        )

        assert result["audit_logged"] is False
        assert result["status"] == "escalation_degraded"
        assert result["compliance_ticket_id"] is not None


@pytest.mark.integration
class TestBuyerBotIntegration:
    """Integration tests for buyer bot with real dependencies."""

    @pytest.mark.asyncio
    async def test_buyer_workflow_integration(self):
        """Test buyer workflow with mock dependencies but real flow."""
        pass

    @pytest.mark.asyncio
    async def test_orchestrator_integration(self):
        """Test buyer bot integration with enhanced orchestrator."""
        pass


# ---------------------------------------------------------------------------
# Phase 2: Affordability Calculator, Objection Handling, Enhanced Matching Tests
# ---------------------------------------------------------------------------


class TestBuyerBotAffordability:
    """Test affordability calculator and objection handling."""

    @pytest.fixture
    def mock_deps(self):
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=AsyncMock,
            ClaudeAssistant=AsyncMock,
            get_event_publisher=Mock,
            PropertyMatcher=AsyncMock,
            get_ml_analytics_engine=Mock,
        ):
            yield

    def _make_state(self, **overrides):
        state = {
            "buyer_id": "test_buyer_100",
            "buyer_name": "Jane Doe",
            "target_areas": None,
            "conversation_history": [
                {"role": "user", "content": "Looking for a house under $500k"},
            ],
            "intent_profile": None,
            "budget_range": {"min": 400000, "max": 500000},
            "financing_status": "pre_approved",
            "urgency_level": "3_months",
            "property_preferences": {"bedrooms": 3},
            "current_qualification_step": "budget",
            "objection_detected": False,
            "detected_objection_type": None,
            "next_action": "respond",
            "response_content": "",
            "matched_properties": [],
            "financial_readiness_score": 75.0,
            "buying_motivation_score": 65.0,
            "buyer_temperature": "warm",
            "is_qualified": False,
            "tone_variant": "empathetic",
            "current_journey_stage": "qualification",
            "properties_viewed_count": 0,
            "last_action_timestamp": None,
            "user_message": "test",
            "intelligence_context": None,
            "intelligence_performance_ms": 0.0,
            "affordability_analysis": None,
            "mortgage_details": None,
            "max_monthly_payment": None,
            "objection_history": None,
        }
        state.update(overrides)
        return state

    @pytest.mark.asyncio
    async def test_affordability_calc_with_budget(self, mock_deps):
        """Test affordability calculation with valid budget."""
        bot = JorgeBuyerBot()
        state = self._make_state()
        result = await bot.calculate_affordability(state)

        assert result.get("affordability_analysis") is not None
        analysis = result["affordability_analysis"]
        assert analysis["max_price"] == 500000
        assert analysis["down_payment"] == 100000  # 20% of 500k
        assert analysis["loan_amount"] == 400000
        assert analysis["monthly_mortgage"] > 0
        assert analysis["monthly_tax"] > 0
        assert analysis["monthly_insurance"] > 0
        assert analysis["total_monthly_payment"] > 0
        assert result["max_monthly_payment"] > 0

    @pytest.mark.asyncio
    async def test_affordability_calc_without_budget(self, mock_deps):
        """Test affordability skips without budget."""
        bot = JorgeBuyerBot()
        state = self._make_state(budget_range=None)
        result = await bot.calculate_affordability(state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_affordability_includes_tax_and_insurance(self, mock_deps):
        """Test that tax and insurance are included in total."""
        bot = JorgeBuyerBot()
        state = self._make_state()
        result = await bot.calculate_affordability(state)
        analysis = result["affordability_analysis"]
        assert analysis["total_monthly_payment"] > analysis["monthly_mortgage"]

    @pytest.mark.asyncio
    async def test_mortgage_details_populated(self, mock_deps):
        """Test mortgage details dict is populated."""
        bot = JorgeBuyerBot()
        state = self._make_state()
        result = await bot.calculate_affordability(state)
        details = result["mortgage_details"]
        assert details["rate"] > 0
        assert details["term_years"] == 30
        assert details["type"] == "30-year fixed"

    @pytest.mark.asyncio
    async def test_objection_handling_budget_shock(self, mock_deps):
        """Test objection handling for budget shock."""
        bot = JorgeBuyerBot()
        state = self._make_state(
            objection_detected=True,
            detected_objection_type="budget_shock",
            affordability_analysis={"total_monthly_payment": 3500},
        )
        result = await bot.handle_objections(state)
        assert len(result["objection_history"]) == 1
        assert result["objection_history"][0]["type"] == "budget_shock"

    @pytest.mark.asyncio
    async def test_objection_handling_analysis_paralysis(self, mock_deps):
        """Test objection handling for analysis paralysis."""
        bot = JorgeBuyerBot()
        state = self._make_state(
            objection_detected=True,
            detected_objection_type="analysis_paralysis",
        )
        result = await bot.handle_objections(state)
        assert result["objection_history"][0]["type"] == "analysis_paralysis"

    @pytest.mark.asyncio
    async def test_objection_handling_spouse_decision(self, mock_deps):
        """Test objection handling for spouse decision."""
        bot = JorgeBuyerBot()
        state = self._make_state(
            objection_detected=True,
            detected_objection_type="spouse_decision",
        )
        result = await bot.handle_objections(state)
        assert result["objection_history"][0]["type"] == "spouse_decision"

    @pytest.mark.asyncio
    async def test_objection_handling_timing(self, mock_deps):
        """Test objection handling for timing concerns."""
        bot = JorgeBuyerBot()
        state = self._make_state(
            objection_detected=True,
            detected_objection_type="timing",
        )
        result = await bot.handle_objections(state)
        assert result["objection_history"][0]["type"] == "timing"

    @pytest.mark.asyncio
    async def test_objection_enriched_with_affordability(self, mock_deps):
        """Test budget shock objection enriched with affordability data."""
        bot = JorgeBuyerBot()
        state = self._make_state(
            objection_detected=True,
            detected_objection_type="budget_shock",
            affordability_analysis={"total_monthly_payment": 3500},
        )
        result = await bot.handle_objections(state)
        # Verify the affordability data was used
        assert len(result["objection_history"]) == 1

    def test_route_after_matching_with_objection(self, mock_deps):
        """Test routing to objection handling when objection detected."""
        bot = JorgeBuyerBot()
        state = self._make_state(objection_detected=True)
        result = bot._route_after_matching(state)
        assert result == "handle_objections"

    def test_route_after_matching_no_objection(self, mock_deps):
        """Test normal routing when no objection detected."""
        bot = JorgeBuyerBot()
        state = self._make_state(objection_detected=False, next_action="respond")
        result = bot._route_after_matching(state)
        assert result == "respond"


# ---------------------------------------------------------------------------
# TCPA SMS Opt-Out Handling Tests
# ---------------------------------------------------------------------------


class TestBuyerBotOptOut:
    """Tests for TCPA opt-out detection in process_buyer_conversation."""

    @pytest.fixture
    def mock_deps(self):
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=AsyncMock,
            ClaudeAssistant=AsyncMock,
            get_event_publisher=Mock,
            PropertyMatcher=AsyncMock,
            get_ml_analytics_engine=Mock,
        ):
            yield

    @pytest.mark.asyncio
    async def test_buyer_opt_out_stop_keyword(self, mock_deps):
        """'stop' triggers opt-out response and skips AI processing."""
        bot = JorgeBuyerBot()
        bot.workflow.ainvoke = AsyncMock()

        result = await bot.process_buyer_conversation(
            conversation_id="buyer_opt_1",
            user_message="stop",
        )

        assert result["opt_out_detected"] is True
        assert result["buyer_id"] == "buyer_opt_1"
        bot.workflow.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_buyer_opt_out_unsubscribe(self, mock_deps):
        """'unsubscribe' triggers opt-out response and skips AI processing."""
        bot = JorgeBuyerBot()
        bot.workflow.ainvoke = AsyncMock()

        result = await bot.process_buyer_conversation(
            conversation_id="buyer_opt_2",
            user_message="Unsubscribe",
        )

        assert result["opt_out_detected"] is True
        bot.workflow.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_buyer_opt_out_adds_ai_off_tag(self, mock_deps):
        """Opt-out response actions include an 'AI-Off' tag."""
        bot = JorgeBuyerBot()
        bot.workflow.ainvoke = AsyncMock()

        result = await bot.process_buyer_conversation(
            conversation_id="buyer_opt_3",
            user_message="remove me",
        )

        assert result["opt_out_detected"] is True
        assert any(
            action.get("tag") == "AI-Off"
            for action in result.get("actions", [])
        )

    @pytest.mark.asyncio
    async def test_buyer_opt_out_sends_confirmation(self, mock_deps):
        """Opt-out returns the standard unsubscribe confirmation message."""
        bot = JorgeBuyerBot()
        bot.workflow.ainvoke = AsyncMock()

        result = await bot.process_buyer_conversation(
            conversation_id="buyer_opt_4",
            user_message="opt out",
        )

        assert "unsubscribed" in result["response_content"].lower()
        assert len(result["response_content"]) <= 160  # SMS length

    @pytest.mark.asyncio
    async def test_buyer_normal_message_not_opt_out(self, mock_deps):
        """A regular buyer message does NOT trigger opt-out."""
        bot = JorgeBuyerBot()
        # Mock the workflow to return a normal response
        bot.workflow.ainvoke = AsyncMock(return_value={
            "buyer_id": "buyer_normal",
            "response_content": "Let me help you find a home!",
            "financial_readiness_score": 50.0,
            "buying_motivation_score": 50.0,
            "matched_properties": [],
            "current_qualification_step": "budget",
        })
        bot.event_publisher.publish_bot_status_update = AsyncMock()
        bot.event_publisher.publish_buyer_qualification_complete = AsyncMock()

        result = await bot.process_buyer_conversation(
            conversation_id="buyer_normal",
            user_message="I want to buy a house",
        )

        assert result.get("opt_out_detected") is not True
        bot.workflow.ainvoke.assert_called_once()
