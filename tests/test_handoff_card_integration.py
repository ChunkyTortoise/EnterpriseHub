"""Integration tests for handoff card generation in JorgeHandoffService

Tests auto-generation of warm handoff cards during handoff execution.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    EnrichedHandoffContext,
    HandoffDecision,
    JorgeHandoffService,
)


@pytest.fixture
def handoff_service():
    """Create a JorgeHandoffService instance for testing."""
    service = JorgeHandoffService()
    service.reset_analytics()  # Clean state
    # Disable handoff router for tests (avoids performance tracker validation)
    service._handoff_router = None
    return service


@pytest.fixture
def sample_handoff_decision():
    """Sample HandoffDecision with enriched context."""
    enriched_context = EnrichedHandoffContext(
        source_qualification_score=85.0,
        source_temperature="hot",
        budget_range={"min": 500000, "max": 700000},
        property_address=None,
        cma_summary=None,
        conversation_summary="Highly qualified buyer, pre-approved, ready to move.",
        key_insights={
            "pre_approval": True,
            "down_payment_ready": True,
            "timeline": "immediate",
        },
        urgency_level="immediate",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    return HandoffDecision(
        source_bot="lead",
        target_bot="buyer",
        reason="buyer_intent_detected",
        confidence=0.87,
        context={
            "contact_id": "test_contact_123",
            "detected_phrases": ["I want to buy", "pre-approved"],
            "conversation_turns": 5,
        },
        enriched_context=enriched_context,
    )


class TestHandoffCardIntegration:
    """Test integration of card generation with handoff service."""

    @pytest.mark.asyncio
    async def test_execute_handoff_generates_card(self, handoff_service, sample_handoff_decision):
        """Test that execute_handoff auto-generates a card on successful handoff."""
        contact_id = "test_contact_123"
        location_id = "test_location_456"

        # Mock GHL client to avoid actual API calls
        with patch.object(handoff_service, "_ghl_client", None):
            # Mock analytics service
            handoff_service.analytics_service = AsyncMock()

            # Execute handoff
            actions = await handoff_service.execute_handoff(
                decision=sample_handoff_decision,
                contact_id=contact_id,
                location_id=location_id,
            )

        # Verify actions include card generation
        assert isinstance(actions, list)
        assert len(actions) > 0

        # Find card generation action
        card_action = next(
            (a for a in actions if a.get("type") == "handoff_card_generated"),
            None,
        )

        assert card_action is not None, "Card generation action not found in actions"

        # Verify card metadata
        card_metadata = card_action.get("card_metadata")
        assert card_metadata is not None
        assert "size_bytes" in card_metadata
        assert "generation_time_ms" in card_metadata
        assert "timestamp" in card_metadata
        assert card_metadata["contact_id"] == contact_id
        assert card_metadata["handoff_route"] == "lead->buyer"

        # Verify size is reasonable (PDF should be a few KB)
        assert card_metadata["size_bytes"] > 1000  # At least 1KB
        assert card_metadata["size_bytes"] < 100000  # Less than 100KB

        # Verify generation time is acceptable
        assert card_metadata["generation_time_ms"] < 2000  # < 2 seconds

    @pytest.mark.asyncio
    async def test_card_generation_with_ghl_contact_data(self, handoff_service, sample_handoff_decision):
        """Test that card generation uses GHL contact data when available."""
        contact_id = "test_contact_123"

        # Mock GHL client with contact data
        mock_ghl_client = AsyncMock()
        mock_ghl_client.get_contact.return_value = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
        }
        handoff_service._ghl_client = mock_ghl_client
        handoff_service.analytics_service = AsyncMock()

        # Execute handoff
        actions = await handoff_service.execute_handoff(
            decision=sample_handoff_decision,
            contact_id=contact_id,
            location_id="test_location",
        )

        # Verify GHL client was called to fetch contact
        mock_ghl_client.get_contact.assert_called_once_with(contact_id)

        # Verify card was generated
        card_action = next(
            (a for a in actions if a.get("type") == "handoff_card_generated"),
            None,
        )
        assert card_action is not None

    @pytest.mark.asyncio
    async def test_card_generation_handles_missing_ghl_data(self, handoff_service, sample_handoff_decision):
        """Test that card generation works even if GHL data fetch fails."""
        contact_id = "test_contact_123"

        # Mock GHL client that fails to fetch contact
        mock_ghl_client = AsyncMock()
        mock_ghl_client.get_contact.side_effect = Exception("GHL API error")
        handoff_service._ghl_client = mock_ghl_client
        handoff_service.analytics_service = AsyncMock()

        # Execute handoff
        actions = await handoff_service.execute_handoff(
            decision=sample_handoff_decision,
            contact_id=contact_id,
            location_id="test_location",
        )

        # Verify card was still generated despite GHL error
        card_action = next(
            (a for a in actions if a.get("type") == "handoff_card_generated"),
            None,
        )
        assert card_action is not None

    @pytest.mark.asyncio
    async def test_card_generation_failure_does_not_block_handoff(self, handoff_service, sample_handoff_decision):
        """Test that handoff succeeds even if card generation fails."""
        contact_id = "test_contact_123"

        # Mock card generator to fail
        with patch(
            "ghl_real_estate_ai.services.handoff_card_generator.generate_card",
            side_effect=Exception("Card generation failed"),
        ):
            handoff_service._ghl_client = None
            handoff_service.analytics_service = AsyncMock()

            # Execute handoff
            actions = await handoff_service.execute_handoff(
                decision=sample_handoff_decision,
                contact_id=contact_id,
                location_id="test_location",
            )

        # Verify handoff still executed (tags were added)
        assert len(actions) > 0
        tag_actions = [a for a in actions if a.get("type") in ("add_tag", "remove_tag")]
        assert len(tag_actions) > 0

        # Card action may be absent or have no metadata
        card_action = next(
            (a for a in actions if a.get("type") == "handoff_card_generated"),
            None,
        )
        # Card action should not be present if generation failed
        assert card_action is None

    @pytest.mark.asyncio
    async def test_card_metadata_format(self, handoff_service, sample_handoff_decision):
        """Test that card metadata has the correct structure."""
        contact_id = "test_contact_123"

        handoff_service._ghl_client = None
        handoff_service.analytics_service = AsyncMock()

        actions = await handoff_service.execute_handoff(
            decision=sample_handoff_decision,
            contact_id=contact_id,
            location_id="test_location",
        )

        card_action = next(
            (a for a in actions if a.get("type") == "handoff_card_generated"),
            None,
        )

        assert card_action is not None
        metadata = card_action["card_metadata"]

        # Verify required metadata fields
        required_fields = [
            "size_bytes",
            "generation_time_ms",
            "timestamp",
            "contact_id",
            "handoff_route",
        ]
        for field in required_fields:
            assert field in metadata, f"Missing required field: {field}"

        # Verify types
        assert isinstance(metadata["size_bytes"], int)
        assert isinstance(metadata["generation_time_ms"], (int, float))
        assert isinstance(metadata["timestamp"], (int, float))
        assert isinstance(metadata["contact_id"], str)
        assert isinstance(metadata["handoff_route"], str)


class TestCardGenerationPerformance:
    """Test performance aspects of card generation integration."""

    @pytest.mark.asyncio
    async def test_card_generation_does_not_slow_handoff(self, handoff_service, sample_handoff_decision):
        """Test that card generation doesn't significantly slow handoff execution."""
        import time

        contact_id = "test_contact_123"

        handoff_service._ghl_client = None
        handoff_service.analytics_service = AsyncMock()

        # Execute handoff and measure time
        start = time.time()
        actions = await handoff_service.execute_handoff(
            decision=sample_handoff_decision,
            contact_id=contact_id,
            location_id="test_location",
        )
        elapsed = time.time() - start

        # Handoff with card generation should complete in reasonable time
        # Target: <3s for handoff + card generation
        assert elapsed < 3.0, f"Handoff took {elapsed:.2f}s (target: <3s)"

        # Verify card was generated
        card_action = next(
            (a for a in actions if a.get("type") == "handoff_card_generated"),
            None,
        )
        assert card_action is not None


class TestCardGenerationWithDifferentBots:
    """Test card generation for different bot handoff scenarios."""

    @pytest.mark.asyncio
    async def test_lead_to_seller_handoff_card(self, handoff_service):
        """Test card generation for lead→seller handoff."""
        enriched_context = EnrichedHandoffContext(
            source_qualification_score=80.0,
            source_temperature="warm",
            budget_range=None,
            property_address="123 Main St, Rancho Cucamonga, CA 91730",
            cma_summary={"estimated_value": 650000},
            conversation_summary="Seller interested in listing property.",
            key_insights={"motivation": "relocation", "timeline": "immediate"},
            urgency_level="immediate",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        decision = HandoffDecision(
            source_bot="lead",
            target_bot="seller",
            reason="seller_intent_detected",
            confidence=0.82,
            context={},
            enriched_context=enriched_context,
        )

        handoff_service._ghl_client = None
        handoff_service.analytics_service = AsyncMock()

        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id="seller_contact_123",
            location_id="test_location",
        )

        card_action = next(
            (a for a in actions if a.get("type") == "handoff_card_generated"),
            None,
        )

        assert card_action is not None
        assert card_action["card_metadata"]["handoff_route"] == "lead->seller"

    @pytest.mark.asyncio
    async def test_buyer_to_seller_handoff_card(self, handoff_service):
        """Test card generation for buyer→seller handoff."""
        enriched_context = EnrichedHandoffContext(
            source_qualification_score=75.0,
            source_temperature="warm",
            budget_range={"min": 400000, "max": 500000},
            property_address="456 Oak Ave, Rancho Cucamonga, CA 91730",
            cma_summary={"estimated_value": 475000},
            conversation_summary="Buyer needs to sell current home first.",
            key_insights={"sell_first": True, "contingent_offer": True},
            urgency_level="3_months",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        decision = HandoffDecision(
            source_bot="buyer",
            target_bot="seller",
            reason="seller_intent_detected",
            confidence=0.78,
            context={},
            enriched_context=enriched_context,
        )

        handoff_service._ghl_client = None
        handoff_service.analytics_service = AsyncMock()

        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id="buyer_seller_123",
            location_id="test_location",
        )

        card_action = next(
            (a for a in actions if a.get("type") == "handoff_card_generated"),
            None,
        )

        assert card_action is not None
        assert card_action["card_metadata"]["handoff_route"] == "buyer->seller"
