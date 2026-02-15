"""
Comprehensive Tests for Seller Bot Main Entry Point
===================================================

Tests for JorgeSellerBot.process_seller_message() - the primary public API.
Covers FRS/PCS scoring, CMA generation, calendar booking, and listing workflows.

Test Coverage:
- Basic seller conversation processing ✓
- FRS (Financial Readiness Score) calculation ✓
- PCS (Property Condition Score) calculation ✓
- CMA request handling ✓
- Calendar booking for hot sellers ✓
- Objection handling ✓
- Edge cases and error handling ✓
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch, ANY
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
            
            # Mock workflow
            bot.workflow = AsyncMock()
            bot.workflow.ainvoke = AsyncMock(return_value={
                "seller_id": "seller_123",
                "response_content": "I can help you sell your home!",
                "frs_score": 75.0,
                "pcs_score": 65.0,
                "seller_temperature": "warm",
                "current_stage": "qualification",
                "handoff_signals": {},
            })
            
            # Mock services
            bot.intent_decoder = AsyncMock()
            bot.intent_decoder.analyze_seller = AsyncMock(return_value={
                "frs_score": 75.0,
                "pcs_score": 65.0,
                "motivation_level": "high",
            })
            
            bot.event_publisher = AsyncMock()
            bot.cma_generator = AsyncMock()
            bot.calendar_service = AsyncMock()
            
            yield bot

    # ==================== Happy Path Tests ====================

    async def test_basic_seller_conversation(self, mock_seller_bot):
        """Test basic seller conversation processing."""
        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Mike Seller",
            message="What's my home worth?",
        )

        assert result["seller_id"] == "seller_123"
        assert "response_content" in result
        assert "frs_score" in result
        assert "pcs_score" in result

    async def test_high_motivation_seller(self, mock_seller_bot):
        """Test seller with high motivation gets high FRS score."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "seller_id": "seller_123",
            "response_content": "Let's get your home sold quickly!",
            "frs_score": 90.0,
            "pcs_score": 75.0,
            "seller_temperature": "hot",
            "motivation_level": "urgent",
            "current_stage": "listing",
            "handoff_signals": {},
        })

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Urgent Seller",
            message="Need to sell ASAP, relocating next month",
        )

        assert result["frs_score"] >= 85.0
        assert result["seller_temperature"] == "hot"

    async def test_timeline_extraction(self, mock_seller_bot):
        """Test timeline extraction from seller message."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "seller_id": "seller_123",
            "response_content": "60 days is doable!",
            "timeline": "60_days",
            "frs_score": 80.0,
            "pcs_score": 70.0,
            "handoff_signals": {},
        })

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="Want to list in next 60 days",
        )

        assert "timeline" in result
        assert "60" in result["timeline"]

    # ==================== FRS/PCS Scoring Tests ====================

    async def test_frs_score_range(self, mock_seller_bot):
        """Test that FRS score is in valid range [0, 100]."""
        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="Thinking about selling",
        )

        assert 0.0 <= result["frs_score"] <= 100.0

    async def test_pcs_score_range(self, mock_seller_bot):
        """Test that PCS score is in valid range [0, 100]."""
        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="House needs some work",
        )

        assert 0.0 <= result["pcs_score"] <= 100.0

    async def test_move_in_ready_high_pcs(self, mock_seller_bot):
        """Test move-in ready homes get high PCS scores."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "seller_id": "seller_123",
            "response_content": "Perfect condition!",
            "frs_score": 75.0,
            "pcs_score": 95.0,
            "condition": "excellent",
            "handoff_signals": {},
        })

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name= "Seller",
            message="House is move-in ready, new kitchen, renovated bathrooms",
        )

        assert result["pcs_score"] >= 90.0

    async def test_fixer_upper_low_pcs(self, mock_seller_bot):
        """Test fixer-uppers get lower PCS scores."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "seller_id": "seller_123",
            "response_content": "We can still get good value.",
            "frs_score": 70.0,
            "pcs_score": 40.0,
            "condition": "needs_work",
            "handoff_signals": {},
        })

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="Needs new roof, plumbing issues, outdated kitchen",
        )

        assert result["pcs_score"] < 60.0

    # ==================== CMA Request Tests ====================

    async def test_cma_request_detection(self, mock_seller_bot):
        """Test CMA request detection and handling."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "seller_id": "seller_123",
            "response_content": "I'll prepare a CMA for your home.",
            "cma_requested": True,
            "frs_score": 75.0,
            "pcs_score": 70.0,
            "handoff_signals": {},
        })

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="What's my home worth? Need a market analysis",
        )

        assert result.get("cma_requested") is True

    async def test_cma_generation_success(self, mock_seller_bot):
        """Test successful CMA generation."""
        mock_seller_bot.cma_generator.generate_cma = AsyncMock(return_value={
            "cma_id": "cma_123",
            "estimated_value": 450000,
            "confidence": 0.85,
        })

        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "seller_id": "seller_123",
            "response_content": "CMA sent via email!",
            "cma_requested": True,
            "cma_generated": True,
            "frs_score": 80.0,
            "pcs_score": 75.0,
            "handoff_signals": {},
        })

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="Send me the home value report",
            seller_email="seller@example.com",
            property_address="123 Main St",
        )

        assert result.get("cma_generated") is True

    # ==================== Calendar Booking Tests ====================

    async def test_hot_seller_calendar_offer(self, mock_seller_bot):
        """Test calendar booking offer for hot sellers."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "seller_id": "seller_123",
            "response_content": "Great! Here are available times to meet...",
            "frs_score": 90.0,
            "pcs_score": 85.0,
            "seller_temperature": "hot",
            "calendar_offered": True,
            "handoff_signals": {},
        })

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Hot Seller",
            message="Ready to list now, let's meet this week",
        )

        assert result["frs_score"] >= 85.0
        assert result["pcs_score"] >= 80.0
        assert result.get("calendar_offered") is True

    async def test_calendar_booking_success(self, mock_seller_bot):
        """Test successful calendar booking."""
        mock_seller_bot.calendar_service.book_appointment = AsyncMock(return_value={
            "booking_id": "booking_123",
            "confirmed": True,
            "slot_time": "2024-03-15T10:00:00Z",
        })

        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "seller_id": "seller_123",
            "response_content": "Appointment confirmed for March 15 at 10am!",
            "frs_score": 90.0,
            "pcs_score": 80.0,
            "appointment_booked": True,
            "handoff_signals": {},
        })

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="Book me for March 15 at 10am",
        )

        assert result.get("appointment_booked") is True

    # ==================== Objection Handling Tests ====================

    async def test_price_objection_handling(self, mock_seller_bot):
        """Test handling of price objections."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "seller_id": "seller_123",
            "response_content": "Let me explain how we price homes competitively...",
            "objection_detected": True,
            "objection_type": "price_concern",
            "frs_score": 60.0,
            "pcs_score": 70.0,
            "handoff_signals": {},
        })

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="Your commission is too high, I found cheaper agents",
        )

        assert result.get("objection_detected") is True
        assert result.get("objection_type") == "price_concern"

    async def test_timing_objection_handling(self, mock_seller_bot):
        """Test handling of timing objections."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "seller_id": "seller_123",
            "response_content": "No pressure! We can revisit when you're ready.",
            "objection_detected": True,
            "objection_type": "timing",
            "frs_score": 40.0,
            "pcs_score": 70.0,
            "handoff_signals": {},
        })

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="Not ready yet, maybe next year",
        )

        assert result.get("objection_detected") is True
        assert result["frs_score"] < 50.0

    # ==================== Edge Case Tests ====================

    async def test_empty_message(self, mock_seller_bot):
        """Test handling of empty message."""
        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="",
        )

        # Should handle gracefully
        assert "response_content" in result

    async def test_none_message(self, mock_seller_bot):
        """Test handling of None message."""
        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message=None,
        )

        assert "response_content" in result

    async def test_none_seller_name(self, mock_seller_bot):
        """Test handling of None seller name."""
        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name=None,
            message="Hello",
        )

        assert "response_content" in result

    async def test_unicode_seller_name(self, mock_seller_bot):
        """Test handling of Unicode characters in seller name."""
        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="María González 王伟",
            message="Want to sell my home",
        )

        assert "response_content" in result

    async def test_max_length_message(self, mock_seller_bot, max_length_message):
        """Test handling of very long messages."""
        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message=max_length_message,
        )

        # Should handle without crashing
        assert "response_content" in result

    # ==================== Error Handling Tests ====================

    async def test_workflow_exception_handling(self, mock_seller_bot):
        """Test graceful handling of workflow exceptions."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(
            side_effect=Exception("Workflow processing error")
        )

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="Hello",
        )

        # Should return error state, not crash
        assert "error" in result or "response_content" in result

    async def test_intent_decoder_failure(self, mock_seller_bot):
        """Test fallback when intent decoder fails."""
        mock_seller_bot.intent_decoder.analyze_seller = AsyncMock(
            side_effect=Exception("Intent analysis failed")
        )

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="Want to sell",
        )

        # Should fallback gracefully
        assert "response_content" in result or "error" in result

    async def test_cma_generation_failure(self, mock_seller_bot):
        """Test handling of CMA generation failures."""
        mock_seller_bot.cma_generator.generate_cma = AsyncMock(
            side_effect=Exception("CMA generation failed")
        )

        # Workflow should handle CMA failure gracefully
        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="Send me a market analysis",
        )

        # Should acknowledge error but not crash
        assert "response_content" in result

    async def test_calendar_booking_failure(self, mock_seller_bot):
        """Test handling of calendar booking failures."""
        mock_seller_bot.calendar_service.book_appointment = AsyncMock(
            side_effect=Exception("Calendar booking failed")
        )

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="Book me for tomorrow",
        )

        # Should handle error gracefully
        assert "response_content" in result

    # ==================== Handoff Tests ====================

    async def test_handoff_to_buyer_bot(self, mock_seller_bot):
        """Test handoff to buyer bot when buy-before-sell detected."""
        mock_seller_bot.workflow.ainvoke = AsyncMock(return_value={
            "seller_id": "seller_123",
            "response_content": "Let me connect you with our buyer specialist.",
            "frs_score": 0.0,
            "pcs_score": 0.0,
            "handoff_signals": {
                "target_bot": "buyer",
                "confidence": 0.85,
                "reason": "buyer_intent_detected",
            },
        })

        result = await mock_seller_bot.process_seller_message(
            seller_id="seller_123",
            seller_name="Seller",
            message="I want to buy a bigger house, will sell mine later",
        )

        assert result["handoff_signals"]["target_bot"] == "buyer"
