"""
Tests for Jorge Handoff Outcome Publisher

Verifies that handoff outcomes are correctly published to GHL as tags
and custom fields, with proper rate limiting and batch processing.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.outcome_publisher import (
    OutcomePublisher,
    OutcomeUpdate,
)


@pytest.fixture
def mock_ghl_client():
    """Mock GHL client with tag and custom field methods."""
    client = MagicMock()
    client.add_tags = AsyncMock(return_value={"status": "success"})
    client.update_custom_fields_batch = AsyncMock(return_value={"status": "success"})
    return client


@pytest.fixture
def publisher(mock_ghl_client):
    """Create outcome publisher instance."""
    return OutcomePublisher(ghl_client=mock_ghl_client)


class TestOutcomeTagFormat:
    """Test outcome tag formatting."""

    def test_format_outcome_tag_success(self):
        """Test successful handoff tag format."""
        tag = OutcomePublisher._format_outcome_tag("lead", "buyer", "successful")
        assert tag == "Handoff-Lead-to-Buyer-Successful"

    def test_format_outcome_tag_failed(self):
        """Test failed handoff tag format."""
        tag = OutcomePublisher._format_outcome_tag("buyer", "seller", "failed")
        assert tag == "Handoff-Buyer-to-Seller-Failed"

    def test_format_outcome_tag_timeout(self):
        """Test timeout handoff tag format."""
        tag = OutcomePublisher._format_outcome_tag("seller", "lead", "timeout")
        assert tag == "Handoff-Seller-to-Lead-Timeout"

    def test_format_outcome_tag_reverted(self):
        """Test reverted handoff tag format."""
        tag = OutcomePublisher._format_outcome_tag("lead", "seller", "reverted")
        assert tag == "Handoff-Lead-to-Seller-Reverted"


class TestPublishHandoffOutcome:
    """Test outcome publishing."""

    @pytest.mark.asyncio
    async def test_publish_immediate_success(self, publisher, mock_ghl_client):
        """Test immediate outcome publication."""
        result = await publisher.publish_handoff_outcome(
            contact_id="test_contact_1",
            source_bot="lead",
            target_bot="buyer",
            outcome="successful",
            confidence=0.85,
            immediate=True,
        )

        assert result is True
        mock_ghl_client.add_tags.assert_called_once_with(
            "test_contact_1", ["Handoff-Lead-to-Buyer-Successful"]
        )

        expected_fields = {
            "handoff_source": "lead",
            "handoff_target": "buyer",
            "handoff_outcome": "successful",
            "handoff_confidence": "0.85",
        }

        # Check that custom fields were updated
        call_args = mock_ghl_client.update_custom_fields_batch.call_args
        assert call_args[0][0] == "test_contact_1"
        fields = call_args[0][1]
        for key, value in expected_fields.items():
            assert fields[key] == value
        assert "handoff_timestamp" in fields

    @pytest.mark.asyncio
    async def test_publish_queued(self, publisher, mock_ghl_client):
        """Test queued outcome publication."""
        result = await publisher.publish_handoff_outcome(
            contact_id="test_contact_2",
            source_bot="buyer",
            target_bot="seller",
            outcome="failed",
            confidence=0.65,
            immediate=False,
        )

        assert result is True
        assert len(publisher._pending_updates) == 1
        assert publisher._pending_updates[0].contact_id == "test_contact_2"
        assert publisher._pending_updates[0].source_bot == "buyer"
        assert publisher._pending_updates[0].target_bot == "seller"
        assert publisher._pending_updates[0].outcome == "failed"

        # Should not call GHL client yet
        mock_ghl_client.add_tags.assert_not_called()
        mock_ghl_client.update_custom_fields_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_invalid_contact_id(self, publisher, mock_ghl_client):
        """Test publication with missing contact ID."""
        result = await publisher.publish_handoff_outcome(
            contact_id="",
            source_bot="lead",
            target_bot="buyer",
            outcome="successful",
            confidence=0.8,
            immediate=True,
        )

        assert result is False
        mock_ghl_client.add_tags.assert_not_called()
        mock_ghl_client.update_custom_fields_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_invalid_outcome(self, publisher, mock_ghl_client):
        """Test publication with invalid outcome."""
        result = await publisher.publish_handoff_outcome(
            contact_id="test_contact_3",
            source_bot="lead",
            target_bot="buyer",
            outcome="invalid_outcome",
            confidence=0.8,
            immediate=True,
        )

        assert result is False
        mock_ghl_client.add_tags.assert_not_called()
        mock_ghl_client.update_custom_fields_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_ghl_error_handling(self, publisher, mock_ghl_client):
        """Test error handling when GHL API fails."""
        mock_ghl_client.add_tags.side_effect = Exception("GHL API error")

        result = await publisher.publish_handoff_outcome(
            contact_id="test_contact_4",
            source_bot="lead",
            target_bot="buyer",
            outcome="successful",
            confidence=0.8,
            immediate=True,
        )

        assert result is False


class TestBatchProcessing:
    """Test batch processing functionality."""

    @pytest.mark.asyncio
    async def test_batch_processor_start_stop(self, publisher):
        """Test starting and stopping batch processor."""
        publisher.start_batch_processor()
        assert publisher._is_running is True
        assert publisher._batch_task is not None

        await publisher.stop_batch_processor()
        assert publisher._is_running is False

    @pytest.mark.asyncio
    async def test_batch_processing_respects_rate_limit(self, publisher, mock_ghl_client):
        """Test that batch processing respects rate limits."""
        # Queue 250 updates (exceeds 200/min limit)
        for i in range(250):
            await publisher.publish_handoff_outcome(
                contact_id=f"contact_{i}",
                source_bot="lead",
                target_bot="buyer",
                outcome="successful",
                confidence=0.8,
                immediate=False,
            )

        assert len(publisher._pending_updates) == 250

        # Process batch
        await publisher._process_batch()

        # Should only process up to MAX_WRITES_PER_MINUTE
        remaining = len(publisher._pending_updates)
        processed = 250 - remaining

        assert processed <= publisher.MAX_WRITES_PER_MINUTE
        assert mock_ghl_client.add_tags.call_count == processed
        assert mock_ghl_client.update_custom_fields_batch.call_count == processed

    @pytest.mark.asyncio
    async def test_batch_processing_tracks_write_timestamps(self, publisher, mock_ghl_client):
        """Test that write timestamps are tracked for rate limiting."""
        # Queue 10 updates
        for i in range(10):
            await publisher.publish_handoff_outcome(
                contact_id=f"contact_{i}",
                source_bot="lead",
                target_bot="buyer",
                outcome="successful",
                confidence=0.8,
                immediate=False,
            )

        await publisher._process_batch()

        # Should have 10 write timestamps
        assert len(publisher._write_timestamps) == 10

    @pytest.mark.asyncio
    async def test_batch_processing_cleans_old_timestamps(self, publisher, mock_ghl_client):
        """Test that old write timestamps are cleaned up."""
        # Add old timestamps (> 60 seconds ago)
        old_time = time.time() - 70
        publisher._write_timestamps = [old_time, old_time, old_time]

        # Queue and process a new update
        await publisher.publish_handoff_outcome(
            contact_id="contact_new",
            source_bot="lead",
            target_bot="buyer",
            outcome="successful",
            confidence=0.8,
            immediate=False,
        )

        await publisher._process_batch()

        # Old timestamps should be removed
        recent_timestamps = [
            ts for ts in publisher._write_timestamps if time.time() - ts < 60
        ]
        assert len(recent_timestamps) == 1

    @pytest.mark.asyncio
    async def test_empty_batch_processing(self, publisher, mock_ghl_client):
        """Test processing empty batch."""
        await publisher._process_batch()

        # Should not call GHL client
        mock_ghl_client.add_tags.assert_not_called()
        mock_ghl_client.update_custom_fields_batch.assert_not_called()


class TestPublisherStats:
    """Test publisher statistics."""

    @pytest.mark.asyncio
    async def test_get_stats_empty(self, publisher):
        """Test stats with no pending updates or writes."""
        stats = publisher.get_stats()

        assert stats["pending_updates"] == 0
        assert stats["writes_last_minute"] == 0
        assert stats["rate_limit_capacity"] == publisher.MAX_WRITES_PER_MINUTE

    @pytest.mark.asyncio
    async def test_get_stats_with_pending(self, publisher):
        """Test stats with pending updates."""
        # Queue 5 updates
        for i in range(5):
            await publisher.publish_handoff_outcome(
                contact_id=f"contact_{i}",
                source_bot="lead",
                target_bot="buyer",
                outcome="successful",
                confidence=0.8,
                immediate=False,
            )

        stats = publisher.get_stats()
        assert stats["pending_updates"] == 5

    @pytest.mark.asyncio
    async def test_get_stats_with_recent_writes(self, publisher):
        """Test stats with recent writes."""
        # Simulate 10 recent writes
        now = time.time()
        publisher._write_timestamps = [now - i for i in range(10)]

        stats = publisher.get_stats()
        assert stats["writes_last_minute"] == 10
        assert (
            stats["rate_limit_capacity"]
            == publisher.MAX_WRITES_PER_MINUTE - 10
        )


class TestOutcomeUpdate:
    """Test OutcomeUpdate dataclass."""

    def test_outcome_update_creation(self):
        """Test creating OutcomeUpdate."""
        update = OutcomeUpdate(
            contact_id="test_contact",
            source_bot="lead",
            target_bot="buyer",
            outcome="successful",
            confidence=0.85,
            timestamp=time.time(),
        )

        assert update.contact_id == "test_contact"
        assert update.source_bot == "lead"
        assert update.target_bot == "buyer"
        assert update.outcome == "successful"
        assert update.confidence == 0.85
        assert update.timestamp > 0
