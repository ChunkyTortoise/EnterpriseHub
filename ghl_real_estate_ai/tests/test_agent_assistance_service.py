"""
Tests for Agent Assistance Service.

Tests conversation suggestions, objection handling, and performance coaching.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ghl_real_estate_ai.services.agent_assistance_service import (
    AgentAssistanceService,
    ConversationStage,
    ConversationMomentum,
    ObjectionType,
    ConversationSuggestion,
    ObjectionResponse,
    AgentGuidance
)


class TestAgentAssistanceService:
    """Test suite for agent assistance service."""

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client for testing."""
        client = Mock()
        client.agenerate = AsyncMock()

        # Mock Claude response
        mock_response = Mock()
        mock_response.content = "This is a great opportunity to help them find their perfect home!"
        client.agenerate.return_value = mock_response

        return client

    @pytest.fixture
    def agent_service(self, mock_llm_client):
        """Create agent assistance service with mocked LLM."""
        return AgentAssistanceService(
            tenant_id="test_tenant",
            llm_client=mock_llm_client
        )

    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history for testing."""
        return [
            {"role": "user", "content": "I'm looking to buy a house", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "I'd love to help you find a home!", "timestamp": "2024-01-01T10:01:00"},
            {"role": "user", "content": "My budget is around 400k", "timestamp": "2024-01-01T10:05:00"},
            {"role": "assistant", "content": "Great! What area are you looking in?", "timestamp": "2024-01-01T10:06:00"},
            {"role": "user", "content": "Austin or Round Rock area", "timestamp": "2024-01-01T10:10:00"},
        ]

    @pytest.fixture
    def sample_extracted_preferences(self):
        """Sample extracted preferences."""
        return {
            "budget": 400000,
            "location": ["Austin", "Round Rock"],
            "bedrooms": 3,
            "timeline": "next 3 months"
        }

    def test_identify_conversation_stage_initial_contact(self, agent_service):
        """Test identification of initial contact stage."""
        conversation_history = []
        extracted_preferences = {}
        lead_score = 0

        stage = agent_service._identify_conversation_stage(
            conversation_history, extracted_preferences, lead_score
        )

        assert stage == ConversationStage.INITIAL_CONTACT

    def test_identify_conversation_stage_qualifying(self, agent_service):
        """Test identification of qualifying stage."""
        conversation_history = [
            {"role": "user", "content": "I'm looking for a house"},
            {"role": "assistant", "content": "What's your budget?"}
        ]
        extracted_preferences = {"budget": 400000}
        lead_score = 1

        stage = agent_service._identify_conversation_stage(
            conversation_history, extracted_preferences, lead_score
        )

        assert stage == ConversationStage.QUALIFYING

    def test_identify_conversation_stage_presenting(self, agent_service):
        """Test identification of presenting stage."""
        conversation_history = [
            {"role": "user", "content": "My budget is 400k and I want Austin area"},
            {"role": "assistant", "content": "Perfect! I have some great properties"}
        ]
        extracted_preferences = {"budget": 400000, "location": "Austin"}
        lead_score = 3  # Hot lead

        stage = agent_service._identify_conversation_stage(
            conversation_history, extracted_preferences, lead_score
        )

        assert stage == ConversationStage.PRESENTING

    def test_identify_conversation_stage_closing(self, agent_service):
        """Test identification of closing stage."""
        conversation_history = [
            {"role": "user", "content": "I'd love to see this property. Can we schedule a showing?"},
        ]
        extracted_preferences = {"budget": 400000, "location": "Austin", "bedrooms": 3}
        lead_score = 4  # Hot lead with appointment request

        stage = agent_service._identify_conversation_stage(
            conversation_history, extracted_preferences, lead_score
        )

        assert stage == ConversationStage.CLOSING

    def test_assess_conversation_momentum_high(self, agent_service):
        """Test assessment of high conversation momentum."""
        conversation_history = [
            {"role": "user", "content": "I'm very interested! When can we see some properties? This is exactly what I've been looking for!", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "Great! I can show you several options", "timestamp": "2024-01-01T10:01:00"},
            {"role": "user", "content": "Perfect! What about this weekend? I love the photos you sent", "timestamp": "2024-01-01T10:05:00"}
        ]

        momentum = agent_service._assess_conversation_momentum(conversation_history)

        assert momentum == ConversationMomentum.HIGH

    def test_assess_conversation_momentum_medium(self, agent_service):
        """Test assessment of medium conversation momentum."""
        conversation_history = [
            {"role": "user", "content": "Ok, that works", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "What about location?", "timestamp": "2024-01-01T10:01:00"},
            {"role": "user", "content": "Austin area is fine", "timestamp": "2024-01-01T10:05:00"}
        ]

        momentum = agent_service._assess_conversation_momentum(conversation_history)

        assert momentum == ConversationMomentum.MEDIUM

    def test_assess_conversation_momentum_low(self, agent_service):
        """Test assessment of low conversation momentum."""
        conversation_history = [
            {"role": "user", "content": "ok", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "What's your budget?", "timestamp": "2024-01-01T10:01:00"},
            {"role": "user", "content": "not sure", "timestamp": "2024-01-01T10:05:00"}
        ]

        momentum = agent_service._assess_conversation_momentum(conversation_history)

        assert momentum == ConversationMomentum.LOW

    def test_assess_conversation_momentum_stalled(self, agent_service):
        """Test assessment of stalled conversation momentum."""
        conversation_history = [
            {"role": "user", "content": "Looking for house", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "What's your budget?", "timestamp": "2024-01-01T10:01:00"}
            # No user response
        ]

        momentum = agent_service._assess_conversation_momentum(conversation_history)

        assert momentum in [ConversationMomentum.STALLED, ConversationMomentum.LOW]

    @pytest.mark.asyncio
    async def test_get_initial_contact_suggestions(self, agent_service):
        """Test getting suggestions for initial contact."""
        extracted_preferences = {}
        momentum = ConversationMomentum.MEDIUM

        suggestions = await agent_service._get_initial_contact_suggestions(
            extracted_preferences, momentum
        )

        assert len(suggestions) > 0
        assert any(s.suggestion_type == "rapport_building" for s in suggestions)
        assert any(s.priority == "high" for s in suggestions)

    @pytest.mark.asyncio
    async def test_get_qualifying_suggestions(self, agent_service):
        """Test getting suggestions for qualifying stage."""
        extracted_preferences = {"budget": 400000}  # Missing location and timeline
        lead_score = 1

        suggestions = await agent_service._get_qualifying_suggestions(
            extracted_preferences, lead_score
        )

        assert len(suggestions) > 0
        assert any(s.suggestion_type == "qualifying_question" for s in suggestions)
        # Should ask about location since it's missing
        assert any("location" in s.message.lower() for s in suggestions)

    @pytest.mark.asyncio
    async def test_get_presenting_suggestions(self, agent_service):
        """Test getting suggestions for presenting stage."""
        extracted_preferences = {"budget": 400000, "location": "Austin"}
        lead_score = 3

        suggestions = await agent_service._get_presenting_suggestions(
            extracted_preferences, lead_score
        )

        assert len(suggestions) > 0
        assert any(s.suggestion_type == "property_presentation" for s in suggestions)
        assert any("properties" in s.message.lower() for s in suggestions)

    @pytest.mark.asyncio
    async def test_get_closing_suggestions_high_momentum(self, agent_service):
        """Test getting closing suggestions with high momentum."""
        extracted_preferences = {"budget": 400000, "location": "Austin"}
        momentum = ConversationMomentum.HIGH

        suggestions = await agent_service._get_closing_suggestions(
            extracted_preferences, momentum
        )

        assert len(suggestions) > 0
        assert any(s.suggestion_type == "appointment_close" for s in suggestions)
        assert any("schedule" in s.message.lower() or "see" in s.message.lower() for s in suggestions)

    @pytest.mark.asyncio
    async def test_get_closing_suggestions_low_momentum(self, agent_service):
        """Test getting closing suggestions with low momentum."""
        extracted_preferences = {"budget": 400000, "location": "Austin"}
        momentum = ConversationMomentum.LOW

        suggestions = await agent_service._get_closing_suggestions(
            extracted_preferences, momentum
        )

        assert len(suggestions) > 0
        assert any(s.suggestion_type == "soft_close" for s in suggestions)
        # Should be softer approach for low momentum
        assert any("call" in s.message.lower() or "discuss" in s.message.lower() for s in suggestions)

    @pytest.mark.asyncio
    async def test_prepare_objection_responses(self, agent_service):
        """Test preparation of objection responses."""
        conversation_history = [
            {"role": "user", "content": "That seems expensive for what it is"}
        ]
        extracted_preferences = {"budget": 400000}
        conversation_stage = ConversationStage.OBJECTION_HANDLING

        objection_responses = await agent_service._prepare_objection_responses(
            conversation_history, extracted_preferences, conversation_stage
        )

        assert len(objection_responses) > 0
        assert any(obj.objection_type == ObjectionType.PRICE for obj in objection_responses)
        assert any(obj.objection_type == ObjectionType.AUTHORITY for obj in objection_responses)

        price_response = next((obj for obj in objection_responses if obj.objection_type == ObjectionType.PRICE), None)
        assert price_response is not None
        assert len(price_response.follow_up_questions) > 0
        assert len(price_response.alternative_approaches) > 0

    @pytest.mark.asyncio
    async def test_generate_performance_insights_slow_response(self, agent_service):
        """Test performance insights for slow response times."""
        conversation_history = [
            {"role": "user", "content": "Looking for house", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "What's your budget?", "timestamp": "2024-01-01T12:00:00"},  # 2 hour delay
            {"role": "user", "content": "400k", "timestamp": "2024-01-01T12:30:00"},
            {"role": "assistant", "content": "Great", "timestamp": "2024-01-01T14:00:00"}  # 1.5 hour delay
        ]

        insights = await agent_service._generate_performance_insights(
            "test_contact", conversation_history, 2, ConversationStage.QUALIFYING
        )

        assert len(insights) > 0
        response_time_insight = next((i for i in insights if i.area == "response_time"), None)
        assert response_time_insight is not None
        assert response_time_insight.impact_level == "high"

    @pytest.mark.asyncio
    async def test_generate_performance_insights_low_questions(self, agent_service):
        """Test performance insights for low question ratio."""
        conversation_history = [
            {"role": "assistant", "content": "I can help you find a house", "timestamp": "2024-01-01T10:00:00"},
            {"role": "user", "content": "Great", "timestamp": "2024-01-01T10:01:00"},
            {"role": "assistant", "content": "Here are some properties", "timestamp": "2024-01-01T10:02:00"},  # No question
            {"role": "user", "content": "Ok", "timestamp": "2024-01-01T10:03:00"},
            {"role": "assistant", "content": "This one is nice", "timestamp": "2024-01-01T10:04:00"}  # No question
        ]

        insights = await agent_service._generate_performance_insights(
            "test_contact", conversation_history, 1, ConversationStage.QUALIFYING
        )

        assert len(insights) > 0
        questioning_insight = next((i for i in insights if i.area == "questioning_technique"), None)
        assert questioning_insight is not None
        assert questioning_insight.impact_level == "high"

    def test_calculate_response_times(self, agent_service):
        """Test calculation of response times."""
        conversation_history = [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T10:05:00"},  # 5 minutes
            {"role": "user", "content": "Budget 400k", "timestamp": "2024-01-01T10:10:00"},
            {"role": "assistant", "content": "Perfect!", "timestamp": "2024-01-01T10:25:00"},  # 15 minutes
        ]

        response_times = agent_service._calculate_response_times(conversation_history)

        assert len(response_times) == 2
        assert response_times[0] == 5.0  # 5 minutes
        assert response_times[1] == 15.0  # 15 minutes

    def test_determine_next_best_actions_initial_contact(self, agent_service):
        """Test determining next best actions for initial contact."""
        actions = agent_service._determine_next_best_actions(
            ConversationStage.INITIAL_CONTACT,
            ConversationMomentum.MEDIUM,
            0,
            {}
        )

        assert len(actions) > 0
        assert any("rapport" in action.lower() for action in actions)
        assert any("motivation" in action.lower() for action in actions)

    def test_determine_next_best_actions_qualifying(self, agent_service):
        """Test determining next best actions for qualifying stage."""
        extracted_preferences = {"budget": 400000}  # Missing location and timeline

        actions = agent_service._determine_next_best_actions(
            ConversationStage.QUALIFYING,
            ConversationMomentum.MEDIUM,
            1,
            extracted_preferences
        )

        assert len(actions) > 0
        assert any("location" in action.lower() and "timeline" in action.lower() for action in actions)

    def test_determine_next_best_actions_high_momentum(self, agent_service):
        """Test next best actions with high momentum."""
        actions = agent_service._determine_next_best_actions(
            ConversationStage.PRESENTING,
            ConversationMomentum.HIGH,
            3,
            {"budget": 400000, "location": "Austin"}
        )

        assert len(actions) > 0
        assert actions[0].startswith("PRIORITY:")

    def test_determine_next_best_actions_stalled(self, agent_service):
        """Test next best actions for stalled conversation."""
        actions = agent_service._determine_next_best_actions(
            ConversationStage.QUALIFYING,
            ConversationMomentum.STALLED,
            1,
            {}
        )

        assert len(actions) > 0
        assert any("reactivate" in action.lower() for action in actions)

    @pytest.mark.asyncio
    async def test_develop_progression_strategy_cold_lead(self, agent_service):
        """Test developing progression strategy for cold lead."""
        strategy = await agent_service._develop_progression_strategy(
            {"budget": 300000},
            1,  # Cold lead
            ConversationStage.QUALIFYING,
            ConversationMomentum.MEDIUM,
            None
        )

        assert strategy["current_stage"] == "qualifying"
        assert strategy["lead_score"] == 1
        assert len(strategy["progression_plan"]) > 0
        assert any("rapport" in step.lower() for step in strategy["progression_plan"])
        assert any("qualifying" in step.lower() for step in strategy["progression_plan"])

    @pytest.mark.asyncio
    async def test_develop_progression_strategy_hot_lead(self, agent_service):
        """Test developing progression strategy for hot lead."""
        strategy = await agent_service._develop_progression_strategy(
            {"budget": 400000, "location": "Austin", "timeline": "ASAP"},
            4,  # Hot lead
            ConversationStage.CLOSING,
            ConversationMomentum.HIGH,
            None
        )

        assert strategy["current_stage"] == "closing"
        assert strategy["lead_score"] == 4
        assert len(strategy["progression_plan"]) > 0
        assert any("viewing" in step.lower() or "schedule" in step.lower() for step in strategy["progression_plan"])

    def test_calculate_confidence_score_high_momentum(self, agent_service):
        """Test confidence score calculation with high momentum."""
        suggestions = [
            ConversationSuggestion("test", "high", "test message", "test reason", 0.9, "immediate", [])
        ]

        confidence = agent_service._calculate_confidence_score(
            suggestions,
            ConversationMomentum.HIGH,
            3  # Hot lead
        )

        assert confidence > 0.8

    def test_calculate_confidence_score_low_momentum(self, agent_service):
        """Test confidence score calculation with low momentum."""
        suggestions = [
            ConversationSuggestion("test", "low", "test message", "test reason", 0.5, "later", [])
        ]

        confidence = agent_service._calculate_confidence_score(
            suggestions,
            ConversationMomentum.LOW,
            1  # Cold lead
        )

        assert confidence < 0.7

    @pytest.mark.asyncio
    async def test_generate_conversation_assistance_complete(
        self,
        agent_service,
        sample_conversation_history,
        sample_extracted_preferences
    ):
        """Test complete conversation assistance generation."""
        guidance = await agent_service.generate_conversation_assistance(
            contact_id="test_contact",
            conversation_history=sample_conversation_history,
            extracted_preferences=sample_extracted_preferences,
            lead_score=3,
            behavioral_context=None
        )

        assert isinstance(guidance, AgentGuidance)
        assert len(guidance.conversation_suggestions) > 0
        assert len(guidance.objection_responses) > 0
        assert len(guidance.next_best_actions) > 0
        assert guidance.confidence_score > 0.0
        assert isinstance(guidance.conversation_momentum, ConversationMomentum)

        # Check that suggestions are relevant
        for suggestion in guidance.conversation_suggestions:
            assert suggestion.message != ""
            assert suggestion.reasoning != ""
            assert suggestion.confidence > 0.0

    @pytest.mark.asyncio
    async def test_fallback_agent_guidance(self, agent_service):
        """Test fallback guidance when main process fails."""
        guidance = await agent_service._fallback_agent_guidance()

        assert isinstance(guidance, AgentGuidance)
        assert len(guidance.conversation_suggestions) > 0
        assert guidance.conversation_suggestions[0].suggestion_type == "general"
        assert guidance.confidence_score == 0.5
        assert len(guidance.next_best_actions) > 0

    @pytest.mark.asyncio
    async def test_track_conversation_outcome(self, agent_service):
        """Test tracking conversation outcomes."""
        guidance = AgentGuidance(
            conversation_suggestions=[],
            objection_responses=[],
            performance_insights=[],
            lead_progression_strategy={},
            next_best_actions=[],
            conversation_momentum=ConversationMomentum.MEDIUM,
            confidence_score=0.8
        )

        await agent_service.track_conversation_outcome(
            contact_id="test_contact",
            guidance_used=guidance,
            actual_response="Thanks for reaching out! What can I help you with?",
            outcome_metrics={"engagement_score": 0.7, "progression": True}
        )

        # Verify tracking was recorded
        performance_key = f"{agent_service.tenant_id}:test_contact"
        assert performance_key in agent_service.performance_data
        assert len(agent_service.performance_data[performance_key]) == 1

    @pytest.mark.asyncio
    async def test_get_agent_performance_summary(self, agent_service):
        """Test getting agent performance summary."""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        summary = await agent_service.get_agent_performance_summary(
            agent_id="test_agent",
            date_range=(start_date, end_date)
        )

        assert "agent_id" in summary
        assert "conversations_assisted" in summary
        assert "average_response_time_minutes" in summary
        assert "top_performing_strategies" in summary
        assert "improvement_opportunities" in summary
        assert isinstance(summary["top_performing_strategies"], list)
        assert isinstance(summary["improvement_opportunities"], list)