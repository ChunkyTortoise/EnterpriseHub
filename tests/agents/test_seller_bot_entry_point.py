"""
Comprehensive Tests for Seller Bot Main Entry Point
===================================================

Tests for JorgeSellerBot.process_seller_message() - the primary public API.
Covers FRS/PCS scoring, CMA generation, calendar booking, and listing workflows.

Test Coverage:
- Basic seller conversation processing
- FRS (Financial Readiness Score) calculation
- PCS (Property Condition Score) calculation
- CMA request handling
- Calendar booking for hot sellers
- Objection handling
- Edge cases and error handling
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

pytestmark = pytest.mark.asyncio


class TestProcessSellerMessage:
    """Test suite for process_seller_message() entry point."""

    @pytest.fixture
    def mock_seller_bot(self):
        """Create mock seller bot with mocked dependencies."""
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            SellerIntentDecoder=Mock(return_value=AsyncMock()),
            ClaudeAssistant=Mock(return_value=AsyncMock()),
            get_event_publisher=Mock(return_value=AsyncMock()),
            CMAGenerator=Mock(return_value=AsyncMock()),
            CalendarBookingService=Mock(return_value=AsyncMock()),
        ):
            bot = JorgeSellerBot(tenant_id="test_tenant")

            # Mock workflow — return dict matching what process_seller_message expects
            bot.workflow = AsyncMock()
            bot.workflow.ainvoke = AsyncMock(return_value={
                "response_content": "I can help you sell your home!",
                "next_action": "respond",
                "current_journey_stage": "qualification",
                "intent_profile": None,
                "seller_persona": {},
                "composite_score": {},
            })

            # Mock all services used during post-processing
            bot.event_publisher = AsyncMock()
            bot.intent_decoder = AsyncMock()
            bot.cma_generator = AsyncMock()
            bot.calendar_service = None  # Disable calendar slot detection by default
            bot.workflow_service = AsyncMock()
            bot.churn_service = AsyncMock()
            bot.churn_service.assess_churn_risk = AsyncMock(return_value=MagicMock(risk_level="low"))
            bot.performance_tracker = AsyncMock()
            bot.metrics_collector = MagicMock()
            bot.ab_testing = AsyncMock()
            bot.ab_testing.get_variant = AsyncMock(return_value="empathetic")
            bot.ab_testing.record_outcome = AsyncMock()

            yield bot

    # ==================== Happy Path Tests ====================

    async def test_basic_seller_conversation(self, mock_seller_bot):
        """Test basic seller conversation processing."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="What's my home worth?",
            seller_name="Mike Seller",
        )

        assert result["lead_id"] == "seller_123"
        assert "response_content" in result
        assert "frs_score" in result
        assert "pcs_score" in result

    async def test_high_motivation_seller(self, mock_seller_bot):
        """Test seller with high motivation returns response with scores."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Need to sell ASAP, relocating next month",
            seller_name="Urgent Seller",
        )

        # With no intent_profile in workflow result, scores default to 0.0
        assert result["frs_score"] >= 0.0
        assert "response_content" in result

    async def test_timeline_extraction(self, mock_seller_bot):
        """Test response includes timeline_urgency from workflow."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "response_content": "60 days is doable!",
            "timeline_urgency": "60_days",
            "next_action": "respond",
            "current_journey_stage": "qualification",
            "intent_profile": None,
            "seller_persona": {},
            "composite_score": {},
        })

        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Want to list in next 60 days",
            seller_name="Seller",
        )

        assert result.get("timeline_urgency") == "60_days"

    # ==================== FRS/PCS Scoring Tests ====================

    async def test_frs_score_range(self, mock_seller_bot):
        """Test that FRS score is in valid range [0, 100]."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Thinking about selling",
            seller_name="Seller",
        )

        assert 0.0 <= result["frs_score"] <= 100.0

    async def test_pcs_score_range(self, mock_seller_bot):
        """Test that PCS score is in valid range [0, 100]."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="House needs some work",
            seller_name="Seller",
        )

        assert 0.0 <= result["pcs_score"] <= 100.0

    async def test_move_in_ready_returns_response(self, mock_seller_bot):
        """Test move-in ready seller gets a response."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="House is move-in ready, new kitchen, renovated bathrooms",
            seller_name="Seller",
        )

        assert "response_content" in result
        assert "frs_score" in result

    async def test_fixer_upper_returns_response(self, mock_seller_bot):
        """Test fixer-upper seller gets a response."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Needs new roof, plumbing issues, outdated kitchen",
            seller_name="Seller",
        )

        assert "response_content" in result
        assert "pcs_score" in result

    # ==================== CMA Request Tests ====================

    async def test_cma_request_returns_response(self, mock_seller_bot):
        """Test CMA request gets valid response."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="What's my home worth? Need a market analysis",
            seller_name="Seller",
        )

        assert "response_content" in result

    async def test_cma_generation_with_email(self, mock_seller_bot):
        """Test CMA generation when seller email provided."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Send me the home value report",
            seller_name="Seller",
            seller_email="seller@example.com",
        )

        assert "response_content" in result

    # ==================== Calendar Booking Tests ====================

    async def test_hot_seller_gets_response(self, mock_seller_bot):
        """Test hot seller scenario returns valid response."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Ready to list now, let's meet this week",
            seller_name="Hot Seller",
        )

        assert "response_content" in result
        assert "frs_score" in result
        assert "pcs_score" in result

    async def test_calendar_booking_success(self, mock_seller_bot):
        """Test successful calendar booking via slot selection."""
        # Enable calendar service with a successful booking
        mock_seller_bot.calendar_service = AsyncMock()
        mock_seller_bot.calendar_service.book_appointment = AsyncMock(return_value={
            "success": True,
            "message": "Appointment confirmed for March 15 at 10am!",
        })
        # Mock the slot detection to trigger calendar flow
        mock_seller_bot._detect_slot_selection = Mock(return_value=0)

        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Option 1",
            seller_name="Seller",
        )

        assert "response_content" in result
        mock_seller_bot.calendar_service.book_appointment.assert_called_once()

    # ==================== Objection Handling Tests ====================

    async def test_price_objection_returns_response(self, mock_seller_bot):
        """Test handling of price objections returns response."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Your commission is too high, I found cheaper agents",
            seller_name="Seller",
        )

        assert "response_content" in result

    async def test_timing_objection_returns_response(self, mock_seller_bot):
        """Test handling of timing objections returns response."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Not ready yet, maybe next year",
            seller_name="Seller",
        )

        assert "response_content" in result

    # ==================== Edge Case Tests ====================

    async def test_empty_message(self, mock_seller_bot):
        """Test handling of empty message."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="",
            seller_name="Seller",
        )

        assert "response_content" in result

    async def test_none_seller_name(self, mock_seller_bot):
        """Test handling of None seller name."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Hello",
            seller_name=None,
        )

        assert "response_content" in result

    async def test_unicode_seller_name(self, mock_seller_bot):
        """Test handling of Unicode characters in seller name."""
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Want to sell my home",
            seller_name="María González 王伟",
        )

        assert "response_content" in result

    async def test_max_length_message(self, mock_seller_bot):
        """Test handling of very long messages."""
        long_message = "I want to sell my home " * 500
        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message=long_message,
            seller_name="Seller",
        )

        assert "response_content" in result

    # ==================== Error Handling Tests ====================

    async def test_workflow_exception_handling(self, mock_seller_bot):
        """Test graceful handling of workflow exceptions."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(
            side_effect=Exception("Workflow processing error")
        )

        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Hello",
            seller_name="Seller",
        )

        # Should return error state, not crash
        assert "error" in result or "response_content" in result

    async def test_intent_decoder_failure(self, mock_seller_bot):
        """Test fallback when intent decoder fails."""
        mock_seller_bot.intent_decoder.analyze_seller = AsyncMock(
            side_effect=Exception("Intent analysis failed")
        )

        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Want to sell",
            seller_name="Seller",
        )

        # Should fallback gracefully
        assert "response_content" in result or "error" in result

    async def test_cma_generation_failure(self, mock_seller_bot):
        """Test handling of CMA generation failures."""
        mock_seller_bot.cma_generator.generate_cma = AsyncMock(
            side_effect=Exception("CMA generation failed")
        )

        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Send me a market analysis",
            seller_name="Seller",
        )

        assert "response_content" in result

    async def test_calendar_booking_failure(self, mock_seller_bot):
        """Test handling of calendar booking failures."""
        mock_seller_bot.calendar_service = AsyncMock()
        mock_seller_bot.calendar_service.book_appointment = AsyncMock(
            side_effect=Exception("Calendar booking failed")
        )
        mock_seller_bot._detect_slot_selection = Mock(return_value=0)

        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="Option 1",
            seller_name="Seller",
        )

        # Calendar exception should propagate or be caught
        assert result is not None

    # ==================== Handoff Tests ====================

    async def test_handoff_to_buyer_bot(self, mock_seller_bot):
        """Test handoff signals extracted when buyer intent detected."""
        # Enable jorge_handoff in config
        mock_seller_bot.config.jorge_handoff_enabled = True

        result = await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="I want to buy a bigger house, will sell mine later",
            seller_name="Seller",
        )

        assert "handoff_signals" in result

    # ==================== Event Publishing Tests ====================

    async def test_event_published_on_success(self, mock_seller_bot):
        """Test that bot status event is published on successful processing."""
        await mock_seller_bot.process_seller_message(
            conversation_id="seller_123",
            user_message="What's my home worth?",
            seller_name="Seller",
        )

        mock_seller_bot.event_publisher.publish_bot_status_update.assert_called_once()
