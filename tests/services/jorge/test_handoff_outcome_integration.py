"""
Integration tests for handoff service with outcome publisher.

Verifies that handoff outcomes are correctly recorded and published to GHL.
"""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    JorgeHandoffService,
)
from ghl_real_estate_ai.services.jorge.outcome_publisher import OutcomePublisher


@pytest.fixture
def mock_ghl_client():
    """Mock GHL client for outcome publisher."""
    client = MagicMock()
    client.add_tags = AsyncMock(return_value={"status": "success"})
    client.update_custom_fields_batch = AsyncMock(return_value={"status": "success"})
    return client


@pytest.fixture
def mock_repository():
    """Mock repository for outcome persistence."""
    repo = MagicMock()
    repo.save_handoff_outcome = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def outcome_publisher(mock_ghl_client):
    """Create outcome publisher instance."""
    return OutcomePublisher(ghl_client=mock_ghl_client)


@pytest.fixture
def handoff_service(mock_repository, outcome_publisher):
    """Create handoff service with outcome publisher configured."""
    service = JorgeHandoffService()
    service.set_repository(mock_repository)
    service.set_outcome_publisher(outcome_publisher)
    return service


class TestHandoffServiceWithOutcomePublisher:
    """Test handoff service integration with outcome publisher."""

    def test_set_outcome_publisher(self, handoff_service, outcome_publisher):
        """Test setting outcome publisher on service."""
        assert handoff_service._outcome_publisher is outcome_publisher

    @pytest.mark.asyncio
    async def test_record_outcome_publishes_to_ghl(self, handoff_service, mock_ghl_client, mock_repository):
        """Test that recording outcome publishes to GHL via outcome publisher."""
        handoff_service.record_outcome(
            contact_id="test_contact_1",
            source_bot="lead",
            target_bot="buyer",
            outcome="successful",
            metadata={"confidence": 0.85},
        )

        # Give async tasks time to execute, then flush
        import asyncio

        await asyncio.sleep(0.1)
        await handoff_service._outcome_publisher._flush_all_pending()

        # Verify GHL calls were made
        mock_ghl_client.add_tags.assert_called()
        assert mock_ghl_client.add_tags.call_args[0][0] == "test_contact_1"
        assert "Handoff-Lead-to-Buyer-Successful" in mock_ghl_client.add_tags.call_args[0][1]

        mock_ghl_client.update_custom_fields_batch.assert_called()
        fields = mock_ghl_client.update_custom_fields_batch.call_args[0][1]
        assert fields["handoff_source"] == "lead"
        assert fields["handoff_target"] == "buyer"
        assert fields["handoff_outcome"] == "successful"
        assert fields["handoff_confidence"] == "0.85"

    @pytest.mark.asyncio
    async def test_record_outcome_persists_to_db(self, handoff_service, mock_repository):
        """Test that recording outcome persists to database."""
        handoff_service.record_outcome(
            contact_id="test_contact_2",
            source_bot="buyer",
            target_bot="seller",
            outcome="failed",
            metadata={"reason": "low_confidence"},
        )

        # Give async tasks time to execute
        import asyncio

        await asyncio.sleep(0.1)

        # Verify DB call was made
        mock_repository.save_handoff_outcome.assert_called_once()
        call_args = mock_repository.save_handoff_outcome.call_args
        assert call_args[1]["contact_id"] == "test_contact_2"
        assert call_args[1]["source_bot"] == "buyer"
        assert call_args[1]["target_bot"] == "seller"
        assert call_args[1]["outcome"] == "failed"

    @pytest.mark.asyncio
    async def test_classmethod_record_with_publisher(self, mock_ghl_client, outcome_publisher):
        """Test classmethod record_handoff_outcome with explicit publisher."""
        JorgeHandoffService.record_handoff_outcome(
            contact_id="test_contact_3",
            source_bot="seller",
            target_bot="buyer",
            outcome="timeout",
            metadata={"confidence": 0.72},
            _outcome_publisher=outcome_publisher,
        )

        # Process pending updates
        import asyncio

        await asyncio.sleep(0.1)
        await outcome_publisher._flush_all_pending()

        # Verify GHL calls
        mock_ghl_client.add_tags.assert_called()
        assert "Handoff-Seller-to-Buyer-Timeout" in mock_ghl_client.add_tags.call_args[0][1]

    def test_record_outcome_invalid_outcome(self, handoff_service, mock_ghl_client):
        """Test recording invalid outcome does not publish."""
        handoff_service.record_outcome(
            contact_id="test_contact_4",
            source_bot="lead",
            target_bot="buyer",
            outcome="invalid_outcome",
        )

        # Should not call GHL client
        mock_ghl_client.add_tags.assert_not_called()
        mock_ghl_client.update_custom_fields_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_record_outcome_ghl_failure_fallback(self, handoff_service, mock_ghl_client, mock_repository):
        """Test that DB write still succeeds if GHL publish fails."""
        mock_ghl_client.add_tags.side_effect = Exception("GHL API error")

        handoff_service.record_outcome(
            contact_id="test_contact_5",
            source_bot="lead",
            target_bot="buyer",
            outcome="successful",
            metadata={"confidence": 0.9},
        )

        # Process and verify GHL was attempted but failed
        await handoff_service._outcome_publisher._process_batch()

        # DB write should still succeed
        import asyncio

        await asyncio.sleep(0.1)
        mock_repository.save_handoff_outcome.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_outcomes_batched(self, handoff_service, mock_ghl_client):
        """Test that multiple outcomes are batched correctly."""
        # Record 5 outcomes
        for i in range(5):
            handoff_service.record_outcome(
                contact_id=f"test_contact_{i}",
                source_bot="lead",
                target_bot="buyer",
                outcome="successful",
                metadata={"confidence": 0.8},
            )

        # Process batch
        import asyncio

        await asyncio.sleep(0.1)
        await handoff_service._outcome_publisher._flush_all_pending()

        # Should have made 5 tag calls and 5 custom field calls
        assert mock_ghl_client.add_tags.call_count == 5
        assert mock_ghl_client.update_custom_fields_batch.call_count == 5

    def test_record_outcome_without_metadata(self, handoff_service, mock_ghl_client):
        """Test recording outcome without metadata."""
        handoff_service.record_outcome(
            contact_id="test_contact_6",
            source_bot="buyer",
            target_bot="seller",
            outcome="reverted",
        )

        # Should still add to in-memory outcomes
        pair_key = "buyer->seller"
        assert pair_key in JorgeHandoffService._handoff_outcomes
        outcomes = JorgeHandoffService._handoff_outcomes[pair_key]
        assert any(o["contact_id"] == "test_contact_6" for o in outcomes)


class TestOutcomePublisherLifecycle:
    """Test outcome publisher lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_stop_batch_processor(self, outcome_publisher):
        """Test starting and stopping batch processor."""
        outcome_publisher.start_batch_processor()
        assert outcome_publisher._is_running is True

        await outcome_publisher.stop_batch_processor()
        assert outcome_publisher._is_running is False

    @pytest.mark.asyncio
    async def test_stop_flushes_pending_updates(self, outcome_publisher, mock_ghl_client):
        """Test that stopping batch processor flushes pending updates."""
        # Queue updates
        for i in range(3):
            await outcome_publisher.publish_handoff_outcome(
                contact_id=f"contact_{i}",
                source_bot="lead",
                target_bot="buyer",
                outcome="successful",
                confidence=0.8,
            )

        assert len(outcome_publisher._pending_updates) == 3

        # Stop should flush
        await outcome_publisher.stop_batch_processor()

        # All should be processed
        assert len(outcome_publisher._pending_updates) == 0
        assert mock_ghl_client.add_tags.call_count == 3
        assert mock_ghl_client.update_custom_fields_batch.call_count == 3
