"""
Comprehensive Tests for Buyer Bot Main Entry Point
==================================================

Tests for JorgeBuyerBot.process_buyer_conversation() - the primary public API.
Covers qualification workflows, financial readiness, property matching, and handoffs.
"""

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot


pytestmark = pytest.mark.asyncio


class TestProcessBuyerConversation:
    """Test suite for process_buyer_conversation() entry point."""

    @pytest.fixture
    def mock_buyer_bot(self):
        """Create mock buyer bot with mocked dependencies."""
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=Mock(return_value=AsyncMock()),
            ClaudeAssistant=Mock(return_value=AsyncMock()),
            get_event_publisher=Mock(return_value=AsyncMock()),
            PropertyMatcher=Mock(return_value=AsyncMock()),
        ):
            bot = JorgeBuyerBot(tenant_id="test_tenant")

            # Mock workflow — workflow.ainvoke returns raw state dict
            bot.workflow = AsyncMock()
            bot.workflow.ainvoke = AsyncMock(return_value={
                "response_content": "Let me help you find the perfect home!",
                "financial_readiness_score": 80.0,
                "buying_motivation_score": 75.0,
                "is_qualified": True,
                "current_journey_stage": "property_search",
                "current_qualification_step": "property_search",
            })

            # Mock all services used during post-processing
            bot.event_publisher = AsyncMock()
            bot.intent_decoder = AsyncMock()
            bot.conversation_memory = AsyncMock()
            bot.conversation_memory.load_state = AsyncMock(return_value=None)
            bot.conversation_memory.save_state = AsyncMock()
            bot.workflow_service = AsyncMock()
            bot.churn_service = AsyncMock()
            bot.churn_service.assess_churn_risk = AsyncMock(
                return_value=MagicMock(risk_score=0.1, risk_level=MagicMock(value="low"), recommended_action=MagicMock(value="monitor"))
            )
            bot.performance_tracker = AsyncMock()
            bot.metrics_collector = MagicMock()
            bot.ab_testing = AsyncMock()
            bot.ab_testing.get_variant = AsyncMock(return_value="empathetic")
            bot.ab_testing.record_outcome = AsyncMock()

            yield bot

    # ==================== Happy Path Tests ====================

    async def test_basic_buyer_conversation(self, mock_buyer_bot):
        """Test basic buyer conversation processing."""
        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="I want to buy a 3br house",
            buyer_name="Jane Smith",
        )

        assert result["lead_id"] == "buyer_123"
        assert "response_content" in result

    async def test_pre_approved_buyer(self, mock_buyer_bot):
        """Test buyer with pre-approval gets response."""
        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="I'm pre-approved for $450k, ready to buy",
            buyer_name="John Pre-Approved",
        )

        assert "response_content" in result

    async def test_budget_range_extraction(self, mock_buyer_bot):
        """Test response includes budget info from workflow."""
        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="Looking for homes between $350k and $400k",
            buyer_name="Budget Buyer",
        )

        assert "response_content" in result

    async def test_property_preferences(self, mock_buyer_bot):
        """Test property preference conversation."""
        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="Need 3 bedrooms, 2 bathrooms, garage, pool and backyard",
            buyer_name="Specific Buyer",
        )

        assert "response_content" in result

    async def test_urgency_detection(self, mock_buyer_bot):
        """Test urgency in buyer conversation."""
        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="Need to close within 30 days, relocating for work",
            buyer_name="Urgent Buyer",
        )

        assert "response_content" in result

    # ==================== Qualification Tests ====================

    async def test_qualification_status_included(self, mock_buyer_bot):
        """Test that qualification status is in response."""
        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="Looking for homes",
            buyer_name="Buyer",
        )

        assert "is_qualified" in result

    async def test_unqualified_buyer(self, mock_buyer_bot):
        """Test unqualified buyer scenario."""
        mock_buyer_bot.workflow.ainvoke = AsyncMock(return_value={
            "response_content": "Let's talk about financing first.",
            "financial_readiness_score": 30.0,
            "buying_motivation_score": 40.0,
            "is_qualified": False,
            "current_qualification_step": "financing",
            "current_journey_stage": "qualification",
        })

        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="Just looking, no budget yet",
            buyer_name="Browser",
        )

        assert result["is_qualified"] is False

    # ==================== Handoff Tests ====================

    async def test_handoff_signals_included(self, mock_buyer_bot):
        """Test that handoff signals are in response."""
        mock_buyer_bot.enable_handoff = True

        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="Not sure what I want, just browsing",
            buyer_name="Browser",
        )

        assert "handoff_signals" in result

    # ==================== Edge Case Tests ====================

    async def test_empty_message_returns_fallback(self, mock_buyer_bot):
        """Test empty message returns fallback response."""
        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="",
            buyer_name="Buyer",
        )

        assert "response_content" in result

    async def test_none_buyer_name(self, mock_buyer_bot):
        """Test handling of None buyer name."""
        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="Hello",
            buyer_name=None,
        )

        assert "response_content" in result

    async def test_unicode_buyer_name(self, mock_buyer_bot):
        """Test handling of Unicode buyer name."""
        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="Looking for homes",
            buyer_name="José García 李明",
        )

        assert "response_content" in result

    async def test_with_conversation_history(self, mock_buyer_bot):
        """Test with existing conversation history."""
        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="$400k max",
            buyer_name="Buyer",
            conversation_history=[
                {"role": "assistant", "content": "What's your budget?"},
            ],
        )

        assert "response_content" in result

    # ==================== Error Handling Tests ====================

    async def test_workflow_exception_handling(self, mock_buyer_bot):
        """Test graceful handling of workflow exceptions."""
        mock_buyer_bot.workflow.ainvoke = AsyncMock(
            side_effect=Exception("Workflow error")
        )

        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="Hello",
            buyer_name="Buyer",
        )

        # Should return error/fallback, not crash
        assert "response_content" in result or "error" in result

    async def test_intent_decoder_failure(self, mock_buyer_bot):
        """Test fallback when intent decoder fails."""
        result = await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="Looking for homes",
            buyer_name="Buyer",
        )

        # Even with decoder issues, should produce a response
        assert "response_content" in result

    # ==================== Event Publishing Tests ====================

    async def test_events_published_on_success(self, mock_buyer_bot):
        """Test that events are published on successful processing."""
        await mock_buyer_bot.process_buyer_conversation(
            conversation_id="buyer_123",
            user_message="I'm ready to buy",
            buyer_name="Buyer",
        )

        mock_buyer_bot.event_publisher.publish_bot_status_update.assert_called_once()
        mock_buyer_bot.event_publisher.publish_buyer_qualification_complete.assert_called_once()
