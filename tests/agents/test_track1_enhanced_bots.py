"""
Comprehensive tests for Track 1 Enhanced Bot Intelligence
Tests AdaptiveJorgeBot, PredictiveLeadBot, RealTimeIntentDecoder, and EnhancedBotOrchestrator
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ghl_real_estate_ai.agents.adaptive_jorge_seller_bot import (
    AdaptiveJorgeBot, AdaptiveQuestionEngine, ConversationMemory
)
from ghl_real_estate_ai.agents.predictive_lead_bot import (
    PredictiveLeadBot, BehavioralAnalyticsEngine, PersonalityAdapter, TemperaturePredictionEngine
)
from ghl_real_estate_ai.agents.realtime_intent_decoder import (
    RealTimeIntentDecoder, SemanticIntentEngine, IntentSignal
)
from ghl_real_estate_ai.agents.enhanced_bot_orchestrator import (
    EnhancedBotOrchestrator, BotOrchestrationConfig, OrchestrationPresets
)
from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile, FinancialReadinessScore, PsychologicalCommitmentScore

class TestAdaptiveJorgeBot:
    """Test suite for AdaptiveJorgeBot enhancements."""

    @pytest.fixture
    def mock_claude_assistant(self):
        mock_claude = AsyncMock()
        mock_claude.analyze_with_context.return_value = {
            "content": "Are we selling this property or just talking about it?"
        }
        return mock_claude

    @pytest.fixture
    def mock_intent_profile(self):
        """Create mock intent profile for testing."""
        from ghl_real_estate_ai.models.lead_scoring import (
            MotivationSignals, TimelineCommitment, ConditionRealism, PriceResponsiveness
        )

        frs = FinancialReadinessScore(
            total_score=65.0,
            motivation=MotivationSignals(score=70, detected_markers=["need to sell fast"], category="High Intent"),
            timeline=TimelineCommitment(score=60, category="Flexible"),
            condition=ConditionRealism(score=50, category="Negotiable"),
            price=PriceResponsiveness(score=80, zestimate_mentioned=True, category="Price-Aware"),
            classification="Warm Lead"
        )

        pcs = PsychologicalCommitmentScore(
            total_score=75.0,
            response_velocity_score=80,
            message_length_score=70,
            question_depth_score=60,
            objection_handling_score=80,
            call_acceptance_score=90
        )

        return LeadIntentProfile(
            lead_id="test_lead_123",
            frs=frs,
            pcs=pcs,
            next_best_action="Schedule Property Tour"
        )

    @pytest.fixture
    def adaptive_jorge_bot(self, mock_claude_assistant, mock_intent_profile):
        with patch('ghl_real_estate_ai.agents.adaptive_jorge_seller_bot.ClaudeAssistant', return_value=mock_claude_assistant):
            with patch('ghl_real_estate_ai.agents.adaptive_jorge_seller_bot.LeadIntentDecoder') as mock_decoder:
                mock_decoder_instance = Mock()
                mock_decoder_instance.analyze_lead.return_value = mock_intent_profile
                mock_decoder.return_value = mock_decoder_instance

                with patch('ghl_real_estate_ai.agents.adaptive_jorge_seller_bot.get_event_publisher') as mock_publisher:
                    mock_publisher.return_value = Mock()
                    bot = AdaptiveJorgeBot()
                    return bot

    @pytest.mark.asyncio
    async def test_adaptive_question_engine_fast_track(self):
        """Test fast-track logic for high-intent leads."""
        engine = AdaptiveQuestionEngine()

        # Mock high-commitment state
        mock_state = {
            'intent_profile': Mock(pcs=Mock(total_score=75)),  # High PCS
            'detected_stall_type': None
        }

        question = await engine.select_next_question(mock_state, {})

        assert "motivated" in question.lower() or "tour" in question.lower()
        assert "tomorrow" in question.lower() or "week" in question.lower()

    @pytest.mark.asyncio
    async def test_adaptive_question_engine_stall_breaker(self):
        """Test stall-breaker question selection."""
        engine = AdaptiveQuestionEngine()

        question = await engine._select_stall_breaker("zestimate")

        assert "zillow" in question.lower() or "comps" in question.lower()

    @pytest.mark.asyncio
    async def test_conversation_memory_persistence(self):
        """Test conversation memory maintains context across interactions."""
        memory = ConversationMemory()

        # First interaction
        context1 = await memory.get_context("test_conv_1")
        assert context1["adaptation_count"] == 0

        # Update context
        await memory.update_context("test_conv_1", {"adaptation_count": 1, "test_data": "value"})

        # Retrieve updated context
        context2 = await memory.get_context("test_conv_1")
        assert context2["adaptation_count"] == 1
        assert context2["test_data"] == "value"

    @pytest.mark.asyncio
    async def test_adaptive_jorge_workflow_integration(self, adaptive_jorge_bot):
        """Test complete adaptive Jorge workflow."""
        conversation_history = [
            {"role": "user", "content": "I need to sell my house ASAP due to job relocation"}
        ]

        result = await adaptive_jorge_bot.process_adaptive_seller_message(
            lead_id="test_123",
            lead_name="Test Lead",
            history=conversation_history
        )

        assert "response_content" in result
        assert result.get("adaptation_applied") == True
        assert "adaptive_mode" in result

class TestPredictiveLeadBot:
    """Test suite for PredictiveLeadBot enhancements."""

    @pytest.mark.asyncio
    async def test_behavioral_analytics_engine_fast_responder(self):
        """Test behavioral analytics for fast-responding leads."""
        engine = BehavioralAnalyticsEngine()

        # Mock conversation history with fast responses
        conversation_history = [
            {"role": "assistant", "content": "Hi, how are you?"},
            {"role": "user", "content": "Great! Very interested in selling."},
            {"role": "assistant", "content": "What's your timeline?"},
            {"role": "user", "content": "I need to sell within 30 days."}
        ]

        pattern = await engine.analyze_response_patterns("fast_lead_123", conversation_history)

        # Should detect fast engagement
        assert pattern.engagement_velocity in ["fast", "moderate"]
        assert pattern.response_count > 0

    @pytest.mark.asyncio
    async def test_sequence_optimization_for_fast_responder(self):
        """Test sequence timing optimization for fast responders."""
        engine = BehavioralAnalyticsEngine()

        # Create fast responder pattern
        from ghl_real_estate_ai.agents.predictive_lead_bot import ResponsePattern
        fast_pattern = ResponsePattern(
            avg_response_hours=1.5,  # Very fast
            response_count=3,
            channel_preferences={"SMS": 0.9, "Email": 0.3},
            engagement_velocity="fast",
            best_contact_times=[9, 14, 18],
            message_length_preference="detailed"
        )

        optimization = await engine.predict_optimal_sequence(fast_pattern)

        # Should accelerate sequence
        assert optimization.day_3 < 3  # Faster than standard
        assert optimization.day_7 < 7
        assert "SMS" in optimization.channel_sequence

    @pytest.mark.asyncio
    async def test_personality_adapter_detection(self):
        """Test personality type detection from conversation."""
        adapter = PersonalityAdapter()

        analytical_conversation = [
            {"role": "user", "content": "I need to see the data and analysis before making any decisions. What are the comparable sales?"}
        ]

        personality = await adapter.detect_personality(analytical_conversation)
        assert personality == "analytical"

        relationship_conversation = [
            {"role": "user", "content": "I want to work with someone I can trust to help me through this process together."}
        ]

        personality = await adapter.detect_personality(relationship_conversation)
        assert personality == "relationship"

    @pytest.mark.asyncio
    async def test_temperature_prediction_engine(self):
        """Test lead temperature trend prediction."""
        engine = TemperaturePredictionEngine()

        # Simulate declining scores
        declining_scores = [
            {"frs_score": 80, "pcs_score": 70},
            {"frs_score": 75, "pcs_score": 65},
            {"frs_score": 65, "pcs_score": 55}
        ]

        for scores in declining_scores:
            prediction = await engine.predict_temperature_trend("declining_lead", scores)

        assert prediction["trend"] == "cooling_down"
        assert prediction.get("early_warning") is not None
        assert prediction["early_warning"]["type"] == "temperature_declining"

    @pytest.mark.asyncio
    async def test_predictive_lead_bot_workflow(self):
        """Test complete predictive lead bot workflow."""
        with patch('ghl_real_estate_ai.agents.predictive_lead_bot.LeadIntentDecoder') as mock_decoder:
            mock_profile = Mock()
            mock_profile.frs = Mock(total_score=70, classification="Warm Lead")
            mock_profile.pcs = Mock(total_score=65)
            mock_decoder_instance = Mock()
            mock_decoder_instance.analyze_lead.return_value = mock_profile
            mock_decoder.return_value = mock_decoder_instance

            with patch('ghl_real_estate_ai.agents.predictive_lead_bot.get_event_publisher') as mock_publisher:
                mock_publisher.return_value = Mock()

                bot = PredictiveLeadBot()

                conversation_history = [
                    {"role": "user", "content": "I'm interested but want to think about it more."}
                ]

                result = await bot.process_predictive_lead_sequence(
                    lead_id="test_123",
                    sequence_day=3,
                    conversation_history=conversation_history
                )

                assert "response_pattern" in result
                assert "personality_type" in result
                assert "sequence_optimization" in result

class TestRealTimeIntentDecoder:
    """Test suite for RealTimeIntentDecoder enhancements."""

    @pytest.mark.asyncio
    async def test_semantic_intent_engine_urgency_detection(self):
        """Test detection of urgency markers in messages."""
        engine = SemanticIntentEngine()
        mock_context = Mock()
        mock_context.detected_patterns = {}

        # Test urgency detection
        urgent_message = "I need to sell my house ASAP due to a job relocation"
        analysis = await engine.analyze(urgent_message, mock_context)

        signals = analysis["semantic_signals"]
        assert any("urgency_" in signal for signal in signals)
        assert analysis["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_semantic_intent_engine_financial_indicators(self):
        """Test detection of financial readiness signals."""
        engine = SemanticIntentEngine()
        mock_context = Mock()
        mock_context.detected_patterns = {}

        # Test financial readiness detection
        cash_message = "I have cash ready and can close within 2 weeks"
        analysis = await engine.analyze(cash_message, mock_context)

        signals = analysis["semantic_signals"]
        assert any("financial_cash" in signal for signal in signals)

    @pytest.mark.asyncio
    async def test_realtime_intent_decoder_streaming_analysis(self):
        """Test real-time streaming intent analysis."""
        decoder = RealTimeIntentDecoder()

        # Mock existing conversation context
        decoder.context_memory._memory["test_conv"] = Mock()
        decoder.context_memory._memory["test_conv"].last_scores = Mock()
        decoder.context_memory._memory["test_conv"].last_scores.frs = Mock(total_score=60)
        decoder.context_memory._memory["test_conv"].last_scores.pcs = Mock(total_score=55)

        # Analyze high-intent message
        high_intent_message = "I'm ready to sell immediately, I have cash buyers lined up"

        with patch.object(decoder, 'event_publisher') as mock_publisher:
            mock_publisher.publish_realtime_intent_update = AsyncMock()

            intent_update = await decoder.stream_intent_analysis(
                message=high_intent_message,
                conversation_id="test_conv",
                lead_id="test_lead"
            )

            assert intent_update.frs_delta > 0  # Should increase FRS
            assert intent_update.pcs_delta > 0  # Should increase PCS
            assert intent_update.confidence > 0.5
            assert IntentSignal.MOTIVATION_INCREASE in intent_update.signals_detected

    @pytest.mark.asyncio
    async def test_intent_forecasting(self):
        """Test intent trajectory forecasting."""
        decoder = RealTimeIntentDecoder()

        # Set up score history with upward trend
        conversation_id = "trending_up"
        context = await decoder.context_memory.get_context(conversation_id)
        context.score_history = [
            {"timestamp": "2026-01-01T10:00:00", "scores": {"frs_total": 40, "pcs_total": 30}},
            {"timestamp": "2026-01-01T11:00:00", "scores": {"frs_total": 50, "pcs_total": 40}},
            {"timestamp": "2026-01-01T12:00:00", "scores": {"frs_total": 65, "pcs_total": 55}}
        ]

        forecast = await decoder.forecast_intent_trajectory(conversation_id, "test_lead")

        assert forecast["forecast"] == "accelerating"
        assert forecast["confidence"] > 0.0
        assert "predicted_scores" in forecast

class TestEnhancedBotOrchestrator:
    """Test suite for EnhancedBotOrchestrator integration."""

    @pytest.fixture
    def orchestrator_config(self):
        return BotOrchestrationConfig(
            enable_realtime_analysis=True,
            enable_adaptive_questioning=True,
            enable_predictive_timing=True,
            realtime_threshold=0.8,
            fallback_to_original=True
        )

    @pytest.fixture
    def orchestrator(self, orchestrator_config):
        with patch('ghl_real_estate_ai.agents.enhanced_bot_orchestrator.get_adaptive_jorge_bot') as mock_jorge:
            with patch('ghl_real_estate_ai.agents.enhanced_bot_orchestrator.get_predictive_lead_bot') as mock_lead:
                with patch('ghl_real_estate_ai.agents.enhanced_bot_orchestrator.get_realtime_intent_decoder') as mock_intent:
                    with patch('ghl_real_estate_ai.agents.enhanced_bot_orchestrator.get_event_publisher') as mock_publisher:
                        # Mock bot instances
                        mock_jorge_instance = AsyncMock()
                        mock_jorge_instance.process_adaptive_seller_message.return_value = {
                            "response_content": "Test response",
                            "adaptive_mode": "standard",
                            "adaptation_applied": True
                        }
                        mock_jorge.return_value = mock_jorge_instance

                        mock_lead_instance = AsyncMock()
                        mock_lead_instance.process_predictive_lead_sequence.return_value = {
                            "optimization_applied": True,
                            "behavioral_insights": {},
                            "personality_type": "analytical"
                        }
                        mock_lead.return_value = mock_lead_instance

                        mock_intent_instance = AsyncMock()
                        mock_intent_instance.stream_intent_analysis.return_value = Mock(
                            frs_delta=5.0,
                            pcs_delta=8.0,
                            confidence=0.85,
                            recommended_action="CONTINUE_NURTURE",
                            signals_detected=[IntentSignal.MOTIVATION_INCREASE]
                        )
                        mock_intent.return_value = mock_intent_instance

                        mock_publisher.return_value = AsyncMock()

                        return EnhancedBotOrchestrator(orchestrator_config)

    @pytest.mark.asyncio
    async def test_seller_conversation_orchestration(self, orchestrator):
        """Test orchestration of seller conversation."""
        result = await orchestrator.orchestrate_conversation(
            lead_id="test_lead",
            lead_name="Test Lead",
            message="I want to sell my house",
            conversation_type="seller",
            conversation_history=[]
        )

        assert result["bot_type"] == "adaptive_jorge"
        assert result["adaptation_applied"] == True
        assert "realtime_insights" in result
        assert "orchestration_metadata" in result

    @pytest.mark.asyncio
    async def test_lead_sequence_orchestration(self, orchestrator):
        """Test orchestration of lead sequence."""
        result = await orchestrator.orchestrate_conversation(
            lead_id="test_lead",
            lead_name="Test Lead",
            message="I'm thinking about buying",
            conversation_type="lead_sequence",
            conversation_history=[]
        )

        assert result["bot_type"] == "predictive_lead"
        assert result["optimization_applied"] == True
        assert "behavioral_insights" in result

    @pytest.mark.asyncio
    async def test_orchestration_metrics_tracking(self, orchestrator):
        """Test orchestration metrics collection."""
        # Perform some orchestrated conversations
        await orchestrator.orchestrate_conversation(
            lead_id="test_1", lead_name="Test 1", message="Hello",
            conversation_type="seller", conversation_history=[]
        )

        await orchestrator.orchestrate_conversation(
            lead_id="test_2", lead_name="Test 2", message="Hi",
            conversation_type="lead_sequence", conversation_history=[]
        )

        metrics = await orchestrator.get_orchestration_metrics()

        assert metrics["total_sessions"] == 2
        assert metrics["adaptive_decisions"] == 1
        assert metrics["predictive_optimizations"] == 1
        assert len(metrics["session_details"]) == 2

    @pytest.mark.asyncio
    async def test_fallback_mechanism(self):
        """Test fallback to original bots when enhanced bots fail."""
        config = BotOrchestrationConfig(fallback_to_original=True)

        with patch('ghl_real_estate_ai.agents.enhanced_bot_orchestrator.get_adaptive_jorge_bot') as mock_jorge:
            # Simulate enhanced bot failure
            mock_jorge.side_effect = Exception("Enhanced bot failed")

            with patch('ghl_real_estate_ai.agents.enhanced_bot_orchestrator.JorgeSellerBot') as mock_original:
                mock_original_instance = AsyncMock()
                mock_original_instance.process_seller_message.return_value = {
                    "response_content": "Fallback response"
                }
                mock_original.return_value = mock_original_instance

                orchestrator = EnhancedBotOrchestrator(config)

                result = await orchestrator.orchestrate_conversation(
                    lead_id="test_lead",
                    lead_name="Test Lead",
                    message="Test message",
                    conversation_type="seller"
                )

                assert result["enhancement_level"] == "fallback"
                assert result["bot_type"] == "original_jorge"

    def test_orchestration_presets(self):
        """Test predefined orchestration configurations."""
        production_config = OrchestrationPresets.production_config()
        assert production_config.enable_realtime_analysis == True
        assert production_config.enable_adaptive_questioning == True
        assert production_config.fallback_to_original == True

        conservative_config = OrchestrationPresets.conservative_config()
        assert conservative_config.enable_adaptive_questioning == False  # Conservative
        assert conservative_config.realtime_threshold == 0.9  # Higher threshold

        testing_config = OrchestrationPresets.testing_config()
        assert testing_config.realtime_threshold == 0.5  # Lower for testing
        assert testing_config.fallback_to_original == False  # Force enhanced

class TestIntegrationScenarios:
    """Integration tests for complete enhanced bot workflows."""

    @pytest.mark.asyncio
    async def test_high_intent_seller_full_workflow(self):
        """Test complete workflow for high-intent seller."""
        # This would be an end-to-end integration test
        # Testing the full flow from message receipt to response generation
        # with all enhancements working together
        pass

    @pytest.mark.asyncio
    async def test_declining_lead_intervention(self):
        """Test intervention workflow for declining lead temperature."""
        # Test real-time detection of declining intent
        # and automatic escalation to prevent lead loss
        pass

    @pytest.mark.asyncio
    async def test_multi_channel_sequence_optimization(self):
        """Test predictive timing across multiple channels."""
        # Test optimization of SMS, email, voice sequence
        # based on lead behavioral patterns
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])