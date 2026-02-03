"""
Test suite for Voice AI Handler - Advanced voice AI phone integration system
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from ghl_real_estate_ai.services.voice_ai_handler import (
    VoiceAIHandler,
    VoiceCallContext,
    VoiceResponse,
    CallType,
    CallPriority,
    ConversationStage,
    get_voice_ai_handler
)


@pytest.fixture
def voice_handler():
    """Create voice AI handler instance for testing"""
    return VoiceAIHandler()


@pytest.fixture
def sample_call_context():
    """Create sample call context for testing"""
    return VoiceCallContext(
        call_id="test-call-123",
        phone_number="+19095551234",
        caller_name="John Smith"
    )


@pytest.mark.asyncio
class TestVoiceAIHandler:
    """Test cases for Voice AI Handler"""

    async def test_voice_handler_initialization(self, voice_handler):
        """Test voice handler initializes correctly"""
        assert voice_handler is not None
        assert hasattr(voice_handler, 'llm_client')
        assert hasattr(voice_handler, 'rc_assistant')
        assert hasattr(voice_handler, 'qualification_questions')
        assert len(voice_handler.qualification_questions) == 7

    async def test_handle_incoming_call(self, voice_handler):
        """Test incoming call handling"""
        context = await voice_handler.handle_incoming_call(
            phone_number="+19095551234",
            caller_name="Jane Doe"
        )

        assert context is not None
        assert context.phone_number == "+19095551234"
        assert context.caller_name == "Jane Doe"
        assert context.call_type == CallType.NEW_LEAD
        assert context.conversation_stage == ConversationStage.GREETING
        assert context.call_id in voice_handler.active_calls

    async def test_process_voice_input_greeting_stage(self, voice_handler, sample_call_context):
        """Test voice input processing in greeting stage"""
        # Add call to active calls
        voice_handler.active_calls[sample_call_context.call_id] = sample_call_context

        with patch.object(voice_handler.llm_client, 'agenerate') as mock_agenerate, \
             patch.object(voice_handler.rc_assistant, 'generate_response') as mock_generate:
            mock_agenerate.return_value = Mock(content='{"intents": ["greeting"], "emotion": "neutral", "urgency": "low", "qualification_signals": [], "red_flags": []}')
            mock_generate.return_value = "Hi John! I'm Jorge Martinez, your Inland Empire real estate specialist. How can I help you today?"

            response = await voice_handler.process_voice_input(
                call_id=sample_call_context.call_id,
                speech_text="Hi, I'm looking for a real estate agent",
                audio_confidence=0.9
            )

            assert isinstance(response, VoiceResponse)
            assert "Jorge Martinez" in response.text
            assert response.emotion in ["neutral", "enthusiastic", "professional"]

    async def test_process_voice_input_qualification_stage(self, voice_handler):
        """Test voice input processing during qualification"""
        context = VoiceCallContext(
            call_id="test-qual-123",
            phone_number="+19095551234",
            conversation_stage=ConversationStage.QUALIFICATION
        )
        voice_handler.active_calls[context.call_id] = context

        with patch.object(voice_handler.llm_client, 'agenerate') as mock_agenerate:
            mock_agenerate.return_value = Mock(content="Great! Are you currently working with another real estate agent?")

            response = await voice_handler.process_voice_input(
                call_id=context.call_id,
                speech_text="I work for Amazon and need to find a home near the warehouse",
                audio_confidence=0.85
            )

            assert response is not None
            assert context.employer == "Amazon"

    async def test_qualification_score_calculation(self, voice_handler):
        """Test lead qualification scoring"""
        context = VoiceCallContext(
            call_id="test-score-123",
            phone_number="+19095551234",
            employer="Amazon",
            timeline="30 days",
            budget_range=(600000, 700000)
        )

        # Add some conversation history indicating pre-approval
        context.transcript = [
            {"speaker": "caller", "text": "Yes, I'm pre-approved for financing", "confidence": 0.9},
            {"speaker": "caller", "text": "I need to move in 30 days for my job", "confidence": 0.9}
        ]

        score = await voice_handler._calculate_qualification_score(context)

        assert score > 50  # Should have decent qualification score
        assert isinstance(score, int)
        assert 0 <= score <= 100

    async def test_intent_analysis(self, voice_handler, sample_call_context):
        """Test intent analysis functionality"""
        with patch.object(voice_handler.llm_client, 'agenerate') as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"intents": ["scheduling"], "emotion": "excited", "urgency": "high", "qualification_signals": ["timeline"], "red_flags": []}'
            )

            intent_analysis = await voice_handler._analyze_intent(
                "I need to see houses this weekend",
                sample_call_context
            )

            assert "scheduling" in intent_analysis["intents"]
            assert intent_analysis["urgency"] == "high"

    async def test_routing_decision_high_qualified_lead(self, voice_handler):
        """Test routing decision for high-qualified leads"""
        context = VoiceCallContext(
            call_id="test-route-123",
            phone_number="+19095551234",
            qualification_score=85,  # High score
            employer="Kaiser"
        )

        with patch.object(voice_handler, '_calculate_qualification_score') as mock_score:
            mock_score.return_value = 85

            routing = await voice_handler._make_routing_decision(context, "I'm ready to buy immediately")

            assert routing["should_transfer"] is True
            assert "qualification score" in routing["reason"].lower()

    async def test_routing_decision_transfer_request(self, voice_handler, sample_call_context):
        """Test routing decision for explicit transfer requests"""
        routing = await voice_handler._make_routing_decision(
            sample_call_context,
            "I want to speak to Jorge directly"
        )

        assert routing["should_transfer"] is True
        assert "speak to jorge" in routing["reason"].lower()

    async def test_voice_response_generation(self, voice_handler):
        """Test AI-generated voice response"""
        context = VoiceCallContext(
            call_id="test-response-123",
            phone_number="+19095551234",
            conversation_stage=ConversationStage.DISCOVERY,
            employer="Amazon"
        )

        intent_analysis = {"intents": ["information"], "emotion": "interested", "urgency": "medium"}
        sentiment = {"score": 0.3}

        with patch.object(voice_handler.rc_assistant, 'generate_response') as mock_generate:
            mock_generate.return_value = "That's great! Amazon employees love the Etiwanda area for its proximity to the distribution centers."

            response = await voice_handler._generate_contextual_response(
                context, "Where do most Amazon workers live?", intent_analysis, sentiment
            )

            assert isinstance(response, VoiceResponse)
            assert "Amazon" in response.text or "Etiwanda" in response.text

    async def test_call_completion_analytics(self, voice_handler):
        """Test call completion and analytics generation"""
        context = VoiceCallContext(
            call_id="test-complete-123",
            phone_number="+19095551234",
            qualification_score=75,
            duration_seconds=300,
            should_transfer_to_jorge=True
        )

        voice_handler.active_calls[context.call_id] = context

        with patch.object(voice_handler, '_store_call_record') as mock_store:
            mock_store.return_value = None

            analytics = await voice_handler.handle_call_completion(context.call_id)

            assert analytics["qualification_score"] == 75
            assert analytics["duration"] == 300
            assert analytics["transfer_to_jorge"] is True
            assert analytics["lead_quality"] == "high"

    @pytest.mark.skip(reason="_extract_context_updates method was removed from VoiceAIHandler")
    async def test_context_updates_extraction(self, voice_handler, sample_call_context):
        """Test extraction of context updates from conversation"""
        pass

    async def test_jorge_voice_profile_loading(self, voice_handler):
        """Test Jorge's voice profile configuration"""
        profile = voice_handler.jorge_voice_profile

        assert "Inland Empire specialist" in profile["market_expertise"]["key_phrases"]
        assert any(p.lower() == "logistics and healthcare relocations" for p in profile["market_expertise"]["key_phrases"])
        assert "professional_friendly" in profile["speech_patterns"]["greeting_style"].lower() or "friendly but professional" in profile["speech_patterns"]["greeting_style"].lower()

    async def test_qualification_questions_loading(self, voice_handler):
        """Test qualification questions configuration"""
        questions = voice_handler.qualification_questions

        assert len(questions) >= 6
        assert any("working with another agent" in q["question"].lower() for q in questions)
        assert any("timeline" in q["question"].lower() for q in questions)
        assert any("pre-approved" in q["question"].lower() for q in questions)

    async def test_conversation_stage_progression(self, voice_handler):
        """Test conversation stage progression logic"""
        context = VoiceCallContext(
            call_id="test-stage-123",
            phone_number="+19095551234",
            conversation_stage=ConversationStage.QUALIFICATION
        )

        intent_analysis = {"intents": ["scheduling"], "urgency": "high"}

        # Should progress to scheduling if qualification is good
        context.qualification_score = 70

        next_stage = await voice_handler._determine_next_conversation_stage(
            context, "Can we schedule a meeting?", intent_analysis
        )

        assert next_stage == ConversationStage.SCHEDULING

    async def test_analytics_generation(self, voice_handler):
        """Test call analytics generation"""
        # Add some mock call data
        sample_record = {
            "call_id": "test-123",
            "duration": 240,
            "qualification_data": {"score": 80, "employer": "Amazon"},
            "routing_decision": {"transferred": True}
        }

        with patch.object(voice_handler.cache, 'get') as mock_get:
            mock_get.return_value = [sample_record]

            analytics = await voice_handler.get_call_analytics()

            assert analytics["total_calls"] >= 0
            assert "qualification_distribution" in analytics
            assert "top_industries" in analytics

    async def test_error_handling_invalid_call(self, voice_handler):
        """Test error handling for invalid call ID"""
        response = await voice_handler.process_voice_input(
            call_id="invalid-call-id",
            speech_text="Hello",
            audio_confidence=0.9
        )

        assert "transfer you to Jorge" in response.text
        assert response.emotion == "empathetic"

    async def test_sentiment_analysis(self, voice_handler):
        """Test sentiment analysis functionality"""
        # Test positive sentiment
        positive_sentiment = await voice_handler._analyze_sentiment(
            "I'm so excited about finding a home in Rancho Cucamonga!"
        )
        assert positive_sentiment["score"] > 0

        # Test negative sentiment
        negative_sentiment = await voice_handler._analyze_sentiment(
            "I'm worried about the prices and concerned about the market"
        )
        assert negative_sentiment["score"] < 0

    async def test_singleton_pattern(self):
        """Test singleton pattern implementation"""
        handler1 = get_voice_ai_handler()
        handler2 = get_voice_ai_handler()

        assert handler1 is handler2

    async def test_cache_integration(self, voice_handler, sample_call_context):
        """Test cache integration for conversation state"""
        voice_handler.active_calls[sample_call_context.call_id] = sample_call_context

        with patch.object(voice_handler.cache, 'set') as mock_set:
            await voice_handler._cache_conversation_state(sample_call_context)
            mock_set.assert_called_once()

    async def test_conversation_stage_guidance(self, voice_handler):
        """Test stage-specific conversation guidance"""
        context = VoiceCallContext(
            call_id="test-guidance-123",
            phone_number="+19095551234",
            conversation_stage=ConversationStage.QUALIFICATION
        )

        prompt = await voice_handler._build_jorge_voice_prompt(
            context, "Tell me about the area", {}, {"score": 0.5}
        )

        assert "qualification" in prompt.lower()
        assert "jorge martinez" in prompt.lower()
        assert "inland empire" in prompt.lower()


@pytest.mark.asyncio
class TestVoiceCallContext:
    """Test VoiceCallContext dataclass"""

    def test_context_initialization(self):
        """Test context initialization with defaults"""
        context = VoiceCallContext(
            call_id="test-123",
            phone_number="+19095551234"
        )

        assert context.call_id == "test-123"
        assert context.phone_number == "+19095551234"
        assert context.call_type == CallType.NEW_LEAD
        assert context.conversation_stage == ConversationStage.GREETING
        assert context.neighborhood_preferences == []
        assert context.start_time is not None

    def test_context_with_custom_values(self):
        """Test context with custom values"""
        context = VoiceCallContext(
            call_id="test-456",
            phone_number="+19095551234",
            caller_name="Jane Doe",
            call_type=CallType.EXISTING_CLIENT,
            priority=CallPriority.HIGH,
            employer="Amazon"
        )

        assert context.caller_name == "Jane Doe"
        assert context.call_type == CallType.EXISTING_CLIENT
        assert context.priority == CallPriority.HIGH
        assert context.employer == "Amazon"


@pytest.mark.asyncio
class TestVoiceResponse:
    """Test VoiceResponse dataclass"""

    def test_response_initialization(self):
        """Test response initialization"""
        response = VoiceResponse(
            text="Hello! How can I help you today?",
            emotion="friendly",
            pace="normal"
        )

        assert response.text == "Hello! How can I help you today?"
        assert response.emotion == "friendly"
        assert response.pace == "normal"
        assert response.confidence == 1.0
        assert response.suggested_actions == []

    def test_response_with_actions(self):
        """Test response with suggested actions"""
        response = VoiceResponse(
            text="Let me schedule that for you.",
            suggested_actions=["schedule_appointment", "send_calendar_link"]
        )

        assert len(response.suggested_actions) == 2
        assert "schedule_appointment" in response.suggested_actions


# Integration tests
@pytest.mark.integration
class TestVoiceAIIntegration:
    """Integration tests for Voice AI system"""

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test complete conversation flow"""
        handler = get_voice_ai_handler()

        # Start call
        context = await handler.handle_incoming_call("+19095551234", "Test User")

        with patch.object(handler.llm_client, 'agenerate') as mock_agenerate:
            mock_agenerate.return_value = Mock(content="Hi! I'm Jorge, your Inland Empire specialist.")

            # Process greeting
            response1 = await handler.process_voice_input(
                context.call_id,
                "Hi, I'm looking for a home",
                0.9
            )

            assert "Jorge" in response1.text

            # Process qualification
            response2 = await handler.process_voice_input(
                context.call_id,
                "I work for Amazon and need to buy in 60 days",
                0.9
            )

            assert response2 is not None

            # Complete call
            analytics = await handler.handle_call_completion(context.call_id)
            assert analytics["call_id"] == context.call_id

    @pytest.mark.asyncio
    async def test_high_volume_call_handling(self):
        """Test handling multiple simultaneous calls"""
        handler = get_voice_ai_handler()

        # Create multiple calls
        calls = []
        for i in range(5):
            context = await handler.handle_incoming_call(f"+1909555{i:04d}", f"Caller {i}")
            calls.append(context)

        assert len(handler.active_calls) == 5

        # Process voice for each call
        for context in calls:
            with patch.object(handler.llm_client, 'agenerate') as mock_agenerate:
                mock_agenerate.return_value = Mock(content="Hello!")

                response = await handler.process_voice_input(
                    context.call_id,
                    "Hello",
                    0.9
                )
                assert response is not None

        # Complete all calls
        for context in calls:
            await handler.handle_call_completion(context.call_id)

        assert len(handler.active_calls) == 0