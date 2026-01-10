"""
Tests for Intelligent Qualifier Service.

Tests Jorge's 7 qualifying questions framework with adaptive questioning.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List

from ghl_real_estate_ai.services.intelligent_qualifier import (
    IntelligentQualifier,
    QualificationAnalysis,
    AdaptiveQuestion,
    CommunicationStyle,
    QualificationGap
)


class TestIntelligentQualifier:
    """Test suite for intelligent qualifier service."""

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client for testing."""
        client = Mock()
        client.agenerate = AsyncMock()
        return client

    @pytest.fixture
    def qualifier(self, mock_llm_client):
        """Create qualifier instance with mocked LLM."""
        return IntelligentQualifier(
            tenant_id="test_tenant",
            llm_client=mock_llm_client
        )

    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history for testing."""
        return [
            {"role": "user", "content": "I'm looking for a house", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "I'd love to help you find a home!", "timestamp": "2024-01-01T10:01:00"},
            {"role": "user", "content": "My budget is around 400k", "timestamp": "2024-01-01T10:02:00"},
            {"role": "assistant", "content": "Great! What area are you looking in?", "timestamp": "2024-01-01T10:03:00"},
            {"role": "user", "content": "Austin or Round Rock", "timestamp": "2024-01-01T10:04:00"}
        ]

    def test_identify_answered_questions_buyer(self, qualifier):
        """Test identification of answered questions for buyer."""
        extracted_preferences = {
            "budget": 400000,
            "location": ["Austin", "Round Rock"],
            "timeline": "June 2024",
            "bedrooms": 3
        }

        answered = qualifier._identify_answered_questions(extracted_preferences, is_buyer=True)

        assert "budget" in answered
        assert "location" in answered
        assert "timeline" in answered
        assert "requirements" in answered  # bedrooms counts
        assert "financing" not in answered  # not provided
        assert "motivation" not in answered  # not provided
        assert "home_condition" not in answered  # buyer doesn't need this

    def test_identify_answered_questions_seller(self, qualifier):
        """Test identification of answered questions for seller."""
        extracted_preferences = {
            "budget": 500000,  # asking price
            "location": "Austin",
            "home_condition": "excellent"
        }

        answered = qualifier._identify_answered_questions(extracted_preferences, is_buyer=False)

        assert "budget" in answered
        assert "location" in answered
        assert "home_condition" in answered
        assert "timeline" not in answered
        assert "requirements" not in answered
        assert "financing" not in answered
        assert "motivation" not in answered

    def test_detect_communication_style_formal(self, qualifier):
        """Test detection of formal communication style."""
        user_messages = [
            {"content": "I would appreciate your assistance in finding a property"},
            {"content": "Could you please help me understand the market conditions?"},
            {"content": "Thank you for your time and consideration"}
        ]

        style = qualifier._detect_communication_style(user_messages)
        assert style == CommunicationStyle.FORMAL

    def test_detect_communication_style_casual(self, qualifier):
        """Test detection of casual communication style."""
        user_messages = [
            {"content": "Yeah I'm looking for a house"},
            {"content": "That sounds awesome!"},
            {"content": "Cool, send me some info"}
        ]

        style = qualifier._detect_communication_style(user_messages)
        assert style == CommunicationStyle.CASUAL

    def test_detect_communication_style_direct(self, qualifier):
        """Test detection of direct communication style."""
        user_messages = [
            {"content": "Need house"},
            {"content": "Show me listings"},
            {"content": "Budget 300k"}
        ]

        style = qualifier._detect_communication_style(user_messages)
        assert style == CommunicationStyle.DIRECT

    def test_calculate_conversation_momentum_high(self, qualifier):
        """Test high momentum calculation."""
        conversation_history = [
            {"role": "user", "content": "Looking for house"},
            {"role": "assistant", "content": "Great! What's your budget?"},
            {"role": "user", "content": "Around 400k"},
            {"role": "assistant", "content": "Perfect! Where are you looking?"},
            {"role": "user", "content": "Austin area"},
        ]

        momentum = qualifier._calculate_conversation_momentum(conversation_history)
        assert momentum == "high"

    def test_calculate_conversation_momentum_low(self, qualifier):
        """Test low momentum calculation."""
        conversation_history = [
            {"role": "assistant", "content": "How can I help you today?"}
        ]

        momentum = qualifier._calculate_conversation_momentum(conversation_history)
        assert momentum == "low"

    @pytest.mark.asyncio
    async def test_analyze_qualification_gaps_buyer(self, qualifier):
        """Test qualification gap analysis for buyer."""
        extracted_preferences = {
            "budget": 400000,
            "location": "Austin"
        }
        conversation_history = [
            {"role": "user", "content": "I have a 400k budget and want to live in Austin"}
        ]

        analysis = await qualifier.analyze_qualification_gaps(
            extracted_preferences,
            conversation_history,
            is_buyer=True
        )

        assert isinstance(analysis, QualificationAnalysis)
        assert analysis.jorge_methodology_score == 2  # budget + location
        assert len(analysis.answered_questions) == 2
        assert len(analysis.missing_qualifiers) == 4  # timeline, requirements, financing, motivation
        assert analysis.next_priority_question is not None

    @pytest.mark.asyncio
    async def test_analyze_qualification_gaps_seller(self, qualifier):
        """Test qualification gap analysis for seller."""
        extracted_preferences = {
            "location": "Austin",
            "home_condition": "excellent",
            "motivation": "relocating for work"
        }
        conversation_history = [
            {"role": "user", "content": "I need to sell my house in Austin, it's in excellent condition"}
        ]

        analysis = await qualifier.analyze_qualification_gaps(
            extracted_preferences,
            conversation_history,
            is_buyer=False
        )

        assert analysis.jorge_methodology_score == 3  # location + home_condition + motivation
        assert "location" in analysis.answered_questions
        assert "home_condition" in analysis.answered_questions
        assert "motivation" in analysis.answered_questions

    def test_calculate_qualification_confidence(self, qualifier):
        """Test qualification confidence calculation."""
        # No questions answered
        confidence_0 = qualifier._calculate_qualification_confidence([])
        assert confidence_0 == 0.0

        # Half questions answered
        confidence_half = qualifier._calculate_qualification_confidence(
            ["budget", "location", "timeline"]
        )
        assert 0.5 < confidence_half < 0.8

        # All questions answered
        confidence_full = qualifier._calculate_qualification_confidence(
            ["budget", "location", "timeline", "requirements", "financing", "motivation", "home_condition"]
        )
        assert confidence_full == 1.0

    @pytest.mark.asyncio
    async def test_craft_next_question_success(self, qualifier, mock_llm_client):
        """Test successful question crafting with Claude."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = '{"question": "What\'s your timeline for moving?", "reasoning": "Natural follow-up to budget/location", "alternatives": ["When do you want to move?", "Timeline?"]}'
        mock_llm_client.agenerate.return_value = mock_response

        # Create qualification analysis
        analysis = QualificationAnalysis(
            answered_questions=["budget", "location"],
            missing_qualifiers=[
                QualificationGap(
                    question_key="timeline",
                    question_name="Timeline",
                    priority=7,
                    context_relevance=0.8,
                    behavioral_readiness=0.9
                )
            ],
            next_priority_question=QualificationGap(
                question_key="timeline",
                question_name="Timeline",
                priority=7,
                context_relevance=0.8,
                behavioral_readiness=0.9
            ),
            jorge_methodology_score=2,
            confidence_level=0.4,
            communication_style=CommunicationStyle.CASUAL,
            conversation_momentum="high"
        )

        question = await qualifier.craft_next_question(
            analysis,
            {"momentum": "high", "engagement_level": "high"},
            {"budget": 400000, "location": "Austin"},
            is_buyer=True
        )

        assert isinstance(question, AdaptiveQuestion)
        assert question.question == "What's your timeline for moving?"
        assert question.targeting == "timeline"
        assert question.style == "casual"

    @pytest.mark.asyncio
    async def test_craft_next_question_fallback(self, qualifier, mock_llm_client):
        """Test fallback question when Claude fails."""
        # Setup mock to raise exception
        mock_llm_client.agenerate.side_effect = Exception("API Error")

        analysis = QualificationAnalysis(
            answered_questions=["budget"],
            missing_qualifiers=[
                QualificationGap(
                    question_key="location",
                    question_name="Location",
                    priority=8,
                    context_relevance=0.5,
                    behavioral_readiness=0.7
                )
            ],
            next_priority_question=QualificationGap(
                question_key="location",
                question_name="Location",
                priority=8,
                context_relevance=0.5,
                behavioral_readiness=0.7
            ),
            jorge_methodology_score=1,
            confidence_level=0.2,
            communication_style=CommunicationStyle.DIRECT,
            conversation_momentum="medium"
        )

        question = await qualifier.craft_next_question(
            analysis,
            {"momentum": "medium", "engagement_level": "medium"},
            {"budget": 300000},
            is_buyer=True
        )

        assert isinstance(question, AdaptiveQuestion)
        assert question.targeting == "location"
        assert "location" in question.question.lower() or "where" in question.question.lower()

    @pytest.mark.asyncio
    async def test_should_ask_qualifying_question_good_timing(self, qualifier):
        """Test when it's good timing to ask a qualifying question."""
        analysis = QualificationAnalysis(
            answered_questions=["budget"],
            missing_qualifiers=[QualificationGap("location", "Location", 8, 0.8, 0.9)],
            next_priority_question=QualificationGap("location", "Location", 8, 0.8, 0.9),
            jorge_methodology_score=1,
            confidence_level=0.2,
            communication_style=CommunicationStyle.CASUAL,
            conversation_momentum="high"
        )

        recent_messages = [
            {"role": "user", "content": "I'm interested in buying a home"},
            {"role": "assistant", "content": "Great! I'd love to help you"}
        ]

        should_ask, reasoning = await qualifier.should_ask_qualifying_question(
            {"momentum": "high"},
            analysis,
            recent_messages
        )

        assert should_ask is True
        assert "good momentum" in reasoning.lower()

    @pytest.mark.asyncio
    async def test_should_ask_qualifying_question_poor_timing(self, qualifier):
        """Test when timing is poor for qualifying questions."""
        analysis = QualificationAnalysis(
            answered_questions=[],
            missing_qualifiers=[QualificationGap("budget", "Budget", 9, 0.5, 0.5)],
            next_priority_question=QualificationGap("budget", "Budget", 9, 0.5, 0.5),
            jorge_methodology_score=0,
            confidence_level=0.0,
            communication_style=CommunicationStyle.CASUAL,
            conversation_momentum="low"
        )

        recent_messages = [
            {"role": "assistant", "content": "What's your budget?"},
            {"role": "assistant", "content": "Hello again, any updates?"}
        ]

        should_ask, reasoning = await qualifier.should_ask_qualifying_question(
            {"momentum": "low"},
            analysis,
            recent_messages
        )

        assert should_ask is False
        assert "low engagement" in reasoning.lower()

    @pytest.mark.asyncio
    async def test_get_qualification_summary_hot_lead(self, qualifier):
        """Test qualification summary for hot lead."""
        extracted_preferences = {
            "budget": 500000,
            "location": "Austin",
            "timeline": "ASAP",
            "bedrooms": 4,
            "financing": "pre-approved"
        }

        summary = await qualifier.get_qualification_summary(
            extracted_preferences,
            is_buyer=True
        )

        assert summary["qualification_status"]["jorge_score"] >= 3
        assert summary["qualification_status"]["classification"] == "Hot Lead"
        assert summary["qualification_status"]["urgency"] == "Immediate action required"
        assert summary["readiness_for_showing"] is True
        assert "Schedule property showing immediately" in summary["recommendations"]

    @pytest.mark.asyncio
    async def test_get_qualification_summary_cold_lead(self, qualifier):
        """Test qualification summary for cold lead."""
        extracted_preferences = {
            "budget": 300000
        }

        summary = await qualifier.get_qualification_summary(
            extracted_preferences,
            is_buyer=True
        )

        assert summary["qualification_status"]["jorge_score"] == 1
        assert summary["qualification_status"]["classification"] == "Cold Lead"
        assert summary["qualification_status"]["urgency"] == "Add to nurture campaign"
        assert summary["readiness_for_showing"] is False
        assert "Build rapport before additional qualifying" in summary["recommendations"]

    def test_fallback_question_templates(self, qualifier):
        """Test fallback question templates for different styles."""
        gap = QualificationGap("budget", "Budget", 9, 0.8, 0.8)

        # Test formal style
        formal_question = qualifier._get_fallback_question(
            gap, CommunicationStyle.FORMAL, True
        )
        assert "could you" in formal_question.question.lower() or "would you" in formal_question.question.lower()

        # Test direct style
        direct_question = qualifier._get_fallback_question(
            gap, CommunicationStyle.DIRECT, True
        )
        assert len(direct_question.question) < 30  # Should be very short

        # Test casual style
        casual_question = qualifier._get_fallback_question(
            gap, CommunicationStyle.CASUAL, True
        )
        assert "what's" in casual_question.question.lower() or "how" in casual_question.question.lower()