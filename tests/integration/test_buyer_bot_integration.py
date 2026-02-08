"""
Integration tests for Jorge's Buyer Bot Ecosystem
Tests end-to-end workflows, orchestrator integration, and real-time events.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.agents.enhanced_bot_orchestrator import ConversationSession, EnhancedBotOrchestrator
from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
from ghl_real_estate_ai.services.sms_compliance_service import OptOutReason, SMSComplianceService


class TestBuyerBotOrchestrator:
    """Test buyer bot integration with enhanced orchestrator."""

    @pytest.fixture
    def mock_conversation_session(self):
        """Mock conversation session for testing."""
        return ConversationSession(
            session_id="test_session_123",
            lead_id="buyer_lead_456",
            lead_name="John Buyer",
            conversation_history=[
                {"role": "user", "content": "I'm looking to buy a 3-bedroom house"},
                {"role": "assistant", "content": "Great! What's your budget and timeline?"},
                {"role": "user", "content": "Pre-approved for $400k, need to move in 2 months"},
            ],
            active_bots=[],
            session_start=datetime.now(),
            last_interaction=datetime.now(),
            intent_profile=None,
            orchestration_state={},
        )

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mocked dependencies."""
        with patch.multiple(
            "ghl_real_estate_ai.agents.enhanced_bot_orchestrator",
            get_event_publisher=Mock,
            get_adaptive_jorge_bot=Mock,
            get_predictive_lead_bot=Mock,
            get_realtime_intent_decoder=Mock,
        ):
            return EnhancedBotOrchestrator()

    @pytest.mark.asyncio
    async def test_orchestrator_buyer_conversation_flow(self, orchestrator, mock_conversation_session):
        """Test complete buyer conversation flow through orchestrator."""
        with patch("ghl_real_estate_ai.agents.enhanced_bot_orchestrator.JorgeBuyerBot") as mock_buyer_bot_class:
            # Mock buyer bot instance and workflow result
            mock_buyer_bot = AsyncMock()
            mock_buyer_bot_class.return_value = mock_buyer_bot

            mock_workflow_result = {
                "buyer_id": "buyer_lead_456",
                "intent_profile": Mock(buyer_temperature="warm", financial_readiness=75.0, urgency_score=65.0),
                "response_content": "Based on your timeline and budget, I have 3 properties to show you.",
                "is_qualified": True,
                "current_qualification_step": "property_search",
                "matched_properties": [{"id": "prop1"}, {"id": "prop2"}, {"id": "prop3"}],
                "next_action": "schedule_property_tour",
                "financial_readiness_score": 75.0,
                "buying_motivation_score": 65.0,
                "buyer_temperature": "warm",
            }

            mock_buyer_bot.process_buyer_conversation.return_value = mock_workflow_result

            # Mock event publisher
            orchestrator.event_publisher.publish_buyer_qualification_progress = AsyncMock()

            # Execute buyer conversation orchestration
            result = await orchestrator._orchestrate_buyer_conversation(
                session=mock_conversation_session, message="I'm ready to see some properties", intent_update=None
            )

            # Verify buyer bot was created with correct tenant
            mock_buyer_bot_class.assert_called_once_with(tenant_id="buyer_lead_456")

            # Verify buyer bot process was called correctly
            mock_buyer_bot.process_buyer_conversation.assert_called_once_with(
                buyer_id="buyer_lead_456",
                buyer_name="John Buyer",
                conversation_history=mock_conversation_session.conversation_history,
            )

            # Verify qualification progress event was published
            orchestrator.event_publisher.publish_buyer_qualification_progress.assert_called_once()

            # Verify result structure
            assert result["bot_type"] == "jorge_buyer"
            assert result["enhancement_level"] == "qualified_buyer_bot"
            assert result["buyer_temperature"] == "warm"
            assert result["financial_readiness_score"] == 75.0
            assert result["properties_matched"] == 3
            assert result["qualification_status"] == "qualified"
            assert "Based on your timeline" in result["message"]

    @pytest.mark.asyncio
    async def test_orchestrator_buyer_conversation_error_handling(self, orchestrator, mock_conversation_session):
        """Test error handling in buyer conversation orchestration."""
        with patch("ghl_real_estate_ai.agents.enhanced_bot_orchestrator.JorgeBuyerBot") as mock_buyer_bot_class:
            # Mock buyer bot to raise exception
            mock_buyer_bot = AsyncMock()
            mock_buyer_bot_class.return_value = mock_buyer_bot
            mock_buyer_bot.process_buyer_conversation.side_effect = Exception("Workflow error")

            result = await orchestrator._orchestrate_buyer_conversation(
                session=mock_conversation_session, message="Test message", intent_update=None
            )

            # Verify error handling
            assert result["bot_type"] == "jorge_buyer_error"
            assert result["enhancement_level"] == "error_fallback"
            assert "technical difficulties" in result["message"]
            assert "error" in result


class TestBuyerBotWorkflowIntegration:
    """Test buyer bot workflow integration with real dependencies."""

    @pytest.mark.asyncio
    async def test_buyer_qualification_workflow_hot_lead(self):
        """Test complete workflow for hot buyer lead."""
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            get_event_publisher=Mock(return_value=AsyncMock()),
            get_ml_analytics_engine=Mock(return_value=Mock()),
        ):
            mock_event_publisher = AsyncMock()

            buyer_bot = JorgeBuyerBot(enable_bot_intelligence=False)
            buyer_bot.event_publisher = mock_event_publisher

            # Mock the LangGraph workflow to return hot buyer result
            hot_result = {
                "buyer_id": "hot_buyer_789",
                "buyer_temperature": "hot",
                "financial_readiness_score": 85.0,
                "buying_motivation_score": 80.0,
                "matched_properties": [
                    {"id": "prop1", "price": 350000, "bedrooms": 3, "score": 95},
                    {"id": "prop2", "price": 380000, "bedrooms": 3, "score": 90},
                ],
                "response_content": "Perfect! I found 2 properties matching your needs.",
                "next_action": "schedule_property_tour",
            }
            buyer_bot.workflow = Mock()
            buyer_bot.workflow.ainvoke = AsyncMock(return_value=hot_result)

            conversation_history = [
                {"role": "user", "content": "Pre-approved for $400k, looking for 3br house"},
                {"role": "user", "content": "Need to move this month, ready to make offer"},
            ]

            result = await buyer_bot.process_buyer_conversation(
                buyer_id="hot_buyer_789", buyer_name="Sarah Johnson", conversation_history=conversation_history
            )

            # Verify hot buyer classification and response
            assert result["is_qualified"] == True
            assert result["buyer_temperature"] == "hot"
            assert result["financial_readiness_score"] == 85.0
            assert result["buying_motivation_score"] == 80.0
            assert len(result["matched_properties"]) == 2

            # Verify events were published
            mock_event_publisher.publish_buyer_qualification_complete.assert_called_once()
            call_kwargs = mock_event_publisher.publish_buyer_qualification_complete.call_args[1]
            assert call_kwargs["contact_id"] == "hot_buyer_789"
            assert call_kwargs["qualification_status"] == "qualified"
            assert call_kwargs["final_score"] == 82.5  # (85 + 80) / 2

    @pytest.mark.asyncio
    async def test_buyer_qualification_workflow_cold_lead(self):
        """Test complete workflow for cold buyer lead."""
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            get_event_publisher=Mock(return_value=AsyncMock()),
            get_ml_analytics_engine=Mock(return_value=Mock()),
        ):
            mock_event_publisher = AsyncMock()

            buyer_bot = JorgeBuyerBot(enable_bot_intelligence=False)
            buyer_bot.event_publisher = mock_event_publisher

            # Mock the LangGraph workflow to return cold buyer result
            cold_result = {
                "buyer_id": "cold_buyer_101",
                "buyer_temperature": "cold",
                "financial_readiness_score": 25.0,
                "buying_motivation_score": 20.0,
                "matched_properties": [],
                "response_content": "I understand you're exploring options.",
                "next_action": "nurture",
            }
            buyer_bot.workflow = Mock()
            buyer_bot.workflow.ainvoke = AsyncMock(return_value=cold_result)

            conversation_history = [
                {"role": "user", "content": "Just browsing, not sure if I want to buy"},
                {"role": "user", "content": "Maybe someday when prices come down"},
            ]

            result = await buyer_bot.process_buyer_conversation(
                buyer_id="cold_buyer_101", buyer_name="Bob Wilson", conversation_history=conversation_history
            )

            # Verify cold buyer classification
            assert result["is_qualified"] == False
            assert result["buyer_temperature"] == "cold"
            assert result["financial_readiness_score"] == 25.0
            assert result["buying_motivation_score"] == 20.0

            # Verify qualification complete event with "needs_nurturing" status
            mock_event_publisher.publish_buyer_qualification_complete.assert_called_with(
                contact_id="cold_buyer_101",
                qualification_status="needs_nurturing",
                final_score=22.5,  # (25 + 20) / 2
                properties_matched=0,
            )


class TestSMSComplianceIntegration:
    """Test SMS compliance integration with buyer bot workflows."""

    @pytest.fixture
    def sms_compliance_service(self):
        """Create SMS compliance service with mocked dependencies."""
        with patch.multiple(
            "ghl_real_estate_ai.services.sms_compliance_service", get_cache_service=Mock, get_event_publisher=Mock
        ):
            return SMSComplianceService()

    @pytest.mark.asyncio
    async def test_sms_validation_before_buyer_message(self, sms_compliance_service):
        """Test SMS validation before sending buyer qualification messages."""
        phone_number = "+15551234567"

        # Mock allowed send (async methods need AsyncMock)
        with (
            patch.object(sms_compliance_service, "_is_opted_out", new_callable=AsyncMock, return_value=False),
            patch.object(sms_compliance_service, "_get_daily_sms_count", new_callable=AsyncMock, return_value=1),
            patch.object(sms_compliance_service, "_get_monthly_sms_count", new_callable=AsyncMock, return_value=10),
            patch.object(sms_compliance_service, "_get_last_sent_timestamp", new_callable=AsyncMock, return_value=None),
        ):
            validation = await sms_compliance_service.validate_sms_send(
                phone_number=phone_number, message_content="Your property matches are ready for review."
            )

            assert validation.allowed == True
            assert validation.daily_count == 1
            assert validation.monthly_count == 10

    @pytest.mark.asyncio
    async def test_sms_opt_out_during_buyer_conversation(self, sms_compliance_service):
        """Test opt-out processing during active buyer conversation."""
        phone_number = "+15551234567"

        with (
            patch.object(sms_compliance_service, "_store_opt_out_audit", new_callable=AsyncMock),
            patch.object(sms_compliance_service.cache, "set", new_callable=AsyncMock),
            patch.object(
                sms_compliance_service.event_publisher, "publish_sms_opt_out_processed", new_callable=AsyncMock
            ),
            patch.object(
                sms_compliance_service.event_publisher, "publish_sms_compliance_event", new_callable=AsyncMock
            ),
        ):
            # Process STOP message
            result = await sms_compliance_service.process_incoming_sms(
                phone_number=phone_number,
                message_content="STOP sending me property updates",
                location_id="jorge_location",
            )

            assert result["action"] == "opt_out_processed"
            assert result["method"] == "stop_keyword"
            assert "STOP" in result["keywords_detected"]

            # Verify events were published
            sms_compliance_service.event_publisher.publish_sms_opt_out_processed.assert_called_once()
            sms_compliance_service.event_publisher.publish_sms_compliance_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_sms_frequency_limit_integration(self, sms_compliance_service):
        """Test SMS frequency limits integration with buyer messaging."""
        phone_number = "+15551234567"

        # Mock daily limit exceeded
        with (
            patch.object(sms_compliance_service, "_is_opted_out", return_value=False),
            patch.object(sms_compliance_service, "_get_daily_sms_count", return_value=3),
            patch.object(sms_compliance_service, "_get_monthly_sms_count", return_value=15),
            patch.object(
                sms_compliance_service.event_publisher, "publish_sms_frequency_limit_hit", new_callable=AsyncMock
            ),
        ):
            validation = await sms_compliance_service.validate_sms_send(
                phone_number=phone_number, message_content="Another property update"
            )

            assert validation.allowed == False
            assert validation.reason == "daily_limit_exceeded"
            assert validation.daily_count == 3

            # Verify frequency limit event was published
            sms_compliance_service.event_publisher.publish_sms_frequency_limit_hit.assert_called_once_with(
                phone_number=phone_number, limit_type="daily", current_count=3, limit_value=3, location_id=None
            )


class TestRealTimeEventIntegration:
    """Test real-time event integration across buyer bot ecosystem."""

    @pytest.mark.asyncio
    async def test_buyer_qualification_events_flow(self):
        """Test complete buyer qualification events flow."""
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            get_event_publisher=Mock(return_value=AsyncMock()),
            get_ml_analytics_engine=Mock(return_value=Mock()),
        ):
            mock_event_publisher = AsyncMock()

            buyer_bot = JorgeBuyerBot(enable_bot_intelligence=False)
            buyer_bot.event_publisher = mock_event_publisher

            # Mock the LangGraph workflow to return warm buyer result
            warm_result = {
                "buyer_id": "test_buyer",
                "buyer_temperature": "warm",
                "financial_readiness_score": 70.0,
                "buying_motivation_score": 65.0,
                "matched_properties": [{"id": "prop1"}],
                "response_content": "Great match!",
                "next_action": "schedule_tour",
            }
            buyer_bot.workflow = Mock()
            buyer_bot.workflow.ainvoke = AsyncMock(return_value=warm_result)

            # Process conversation
            await buyer_bot.process_buyer_conversation(
                buyer_id="test_buyer",
                buyer_name="Test Buyer",
                conversation_history=[{"role": "user", "content": "Looking to buy"}],
            )

            # Verify event publishing sequence
            mock_event_publisher.publish_buyer_qualification_complete.assert_called_once()

            # Verify event data
            call_args = mock_event_publisher.publish_buyer_qualification_complete.call_args
            assert call_args[1]["contact_id"] == "test_buyer"
            assert call_args[1]["qualification_status"] == "qualified"
            assert call_args[1]["final_score"] == 67.5  # (70 + 65) / 2

    @pytest.mark.asyncio
    async def test_property_match_events_integration(self):
        """Test property match events integration."""
        with patch("ghl_real_estate_ai.services.event_publisher.get_event_publisher") as mock_get_publisher:
            mock_event_publisher = AsyncMock()
            mock_get_publisher.return_value = mock_event_publisher

            buyer_bot = JorgeBuyerBot()
            buyer_bot.event_publisher = mock_event_publisher
            buyer_bot.property_matcher = AsyncMock()

            # Mock property matches
            mock_properties = [{"id": "prop1", "score": 95}, {"id": "prop2", "score": 88}]
            buyer_bot.property_matcher.find_matches.return_value = mock_properties

            # Test property matching
            state = {
                "buyer_id": "test_buyer",
                "property_preferences": {"bedrooms": 3},
                "budget_range": {"min": 300000, "max": 400000},
            }

            result = await buyer_bot.match_properties(state)

            # Verify property match event was published
            mock_event_publisher.publish_property_match_update.assert_called_once_with(
                contact_id="test_buyer", properties_matched=2, match_criteria={"bedrooms": 3}
            )

            assert len(result["matched_properties"]) == 2
            assert result["next_action"] == "respond"


@pytest.mark.integration
class TestEndToEndBuyerBotFlow:
    """End-to-end integration tests for complete buyer bot workflows."""

    @pytest.mark.asyncio
    async def test_complete_buyer_journey_integration(self):
        """Test complete buyer journey from initial contact to qualified lead."""
        # This would test with real dependencies in integration environment
        # Including real Redis, event publishing, property matching, etc.
        pass

    @pytest.mark.asyncio
    async def test_buyer_to_seller_handoff_integration(self):
        """Test buyer bot to seller bot handoff for qualified leads."""
        # This would test cross-bot communication and handoffs
        pass

    @pytest.mark.asyncio
    async def test_sms_compliance_with_real_webhooks(self):
        """Test SMS compliance with real webhook endpoints."""
        # This would test the FastAPI webhook endpoints with real requests
        pass
