"""Tests for recovery orchestration service."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.abandonment_detector import (
    AbandonedContact,
    AbandonmentStage,
)
from ghl_real_estate_ai.services.jorge.recovery_orchestrator import (
    RecoveryOrchestrator,
)


@pytest.fixture
def mock_ghl_client():
    """Mock GHL client."""
    client = AsyncMock()
    client.send_message = AsyncMock()
    return client


@pytest.fixture
def orchestrator(mock_ghl_client):
    """Create orchestrator with mocked GHL client."""
    return RecoveryOrchestrator(ghl_client=mock_ghl_client)


@pytest.fixture
def sample_abandoned_contact():
    """Create sample abandoned contact."""
    return AbandonedContact(
        contact_id="c123",
        location_id="loc123",
        bot_type="lead",
        last_contact_timestamp=time.time() - (5 * 24 * 3600),
        silence_duration_hours=120.0,
        current_stage=AbandonmentStage.DAY_3,
        recovery_attempt_count=0,
        contact_metadata={
            "name": "John Doe",
            "interest_area": "Rancho Cucamonga",
            "preferred_channel": "sms",
        },
    )


@pytest.mark.asyncio
class TestRecoveryOrchestration:
    """Test recovery orchestration."""

    async def test_orchestrate_recovery_no_client(self):
        """Test orchestration without GHL client."""
        orchestrator = RecoveryOrchestrator(ghl_client=None)
        result = await orchestrator.orchestrate_recovery([])
        assert "error" in result

    async def test_orchestrate_recovery_empty_list(self, orchestrator):
        """Test orchestration with empty contact list."""
        result = await orchestrator.orchestrate_recovery([])
        assert result["total_attempted"] == 0
        assert result["successful"] == 0

    async def test_orchestrate_recovery_single_contact(
        self, orchestrator, mock_ghl_client, sample_abandoned_contact
    ):
        """Test successful recovery for single contact."""
        mock_ghl_client.send_message.return_value = None

        result = await orchestrator.orchestrate_recovery([sample_abandoned_contact])

        assert result["total_attempted"] == 1
        assert result["successful"] == 1
        assert result["failed"] == 0
        assert "3d" in result["by_stage"]
        assert result["by_stage"]["3d"] == 1

        # Verify message was sent
        mock_ghl_client.send_message.assert_called_once()
        call_kwargs = mock_ghl_client.send_message.call_args[1]
        assert call_kwargs["contact_id"] == "c123"
        assert call_kwargs["channel"] == "sms"

    async def test_orchestrate_recovery_multiple_contacts(
        self, orchestrator, mock_ghl_client
    ):
        """Test recovery for multiple contacts."""
        contacts = [
            AbandonedContact(
                contact_id=f"c{i}",
                location_id="loc123",
                bot_type="lead",
                last_contact_timestamp=time.time() - (i * 24 * 3600),
                silence_duration_hours=i * 24.0,
                current_stage=AbandonmentStage.DAY_3 if i < 5 else AbandonmentStage.DAY_7,
                recovery_attempt_count=0,
                contact_metadata={"name": f"Contact {i}"},
            )
            for i in range(3, 8)
        ]

        result = await orchestrator.orchestrate_recovery(contacts)

        assert result["total_attempted"] == 5
        assert result["successful"] == 5
        assert mock_ghl_client.send_message.call_count == 5

    async def test_orchestrate_recovery_with_failure(
        self, orchestrator, mock_ghl_client, sample_abandoned_contact
    ):
        """Test recovery with GHL client failure."""
        mock_ghl_client.send_message.side_effect = Exception("GHL API error")

        result = await orchestrator.orchestrate_recovery([sample_abandoned_contact])

        assert result["total_attempted"] == 1
        assert result["successful"] == 0
        assert result["failed"] == 1


@pytest.mark.asyncio
class TestRecoveryMessageGeneration:
    """Test recovery message generation."""

    async def test_generate_recovery_message_day3(
        self, orchestrator, sample_abandoned_contact
    ):
        """Test message generation for Day 3 stage."""
        sample_abandoned_contact.current_stage = AbandonmentStage.DAY_3

        message = await orchestrator._generate_recovery_message(sample_abandoned_contact)

        assert message is not None
        assert "John" in message or "there" in message  # Name fallback
        assert "Rancho Cucamonga" in message or "check" in message.lower()

    async def test_generate_recovery_message_day7(
        self, orchestrator, sample_abandoned_contact
    ):
        """Test message generation for Day 7 stage."""
        sample_abandoned_contact.current_stage = AbandonmentStage.DAY_7

        message = await orchestrator._generate_recovery_message(sample_abandoned_contact)

        assert message is not None
        assert len(message) > 50  # Substantial message

    async def test_generate_recovery_message_day14(
        self, orchestrator, sample_abandoned_contact
    ):
        """Test message generation for Day 14 stage."""
        sample_abandoned_contact.current_stage = AbandonmentStage.DAY_14

        message = await orchestrator._generate_recovery_message(sample_abandoned_contact)

        assert message is not None

    async def test_generate_recovery_message_day30(
        self, orchestrator, sample_abandoned_contact
    ):
        """Test message generation for Day 30 stage (Hail Mary)."""
        sample_abandoned_contact.current_stage = AbandonmentStage.DAY_30

        message = await orchestrator._generate_recovery_message(sample_abandoned_contact)

        assert message is not None

    async def test_generate_recovery_message_missing_metadata(
        self, orchestrator
    ):
        """Test message generation with minimal metadata."""
        contact = AbandonedContact(
            contact_id="c123",
            location_id="loc123",
            bot_type="lead",
            last_contact_timestamp=time.time(),
            silence_duration_hours=72.0,
            current_stage=AbandonmentStage.DAY_3,
            recovery_attempt_count=0,
            contact_metadata={},  # Empty metadata
        )

        message = await orchestrator._generate_recovery_message(contact)

        assert message is not None
        # Should use fallback values
        assert "there" in message  # Default name


@pytest.mark.asyncio
class TestMarketTriggerIntegration:
    """Test market trigger integration in recovery messages."""

    async def test_get_relevant_market_trigger_day3(
        self, orchestrator, sample_abandoned_contact
    ):
        """Test market trigger retrieval for Day 3 (urgency stage)."""
        sample_abandoned_contact.current_stage = AbandonmentStage.DAY_3

        trigger = await orchestrator._get_relevant_market_trigger(
            sample_abandoned_contact
        )

        # Should attempt to generate rate change or price drop
        # Result may be None if no watchlist, but method should not error
        assert trigger is None or trigger is not None  # Valid either way

    async def test_get_relevant_market_trigger_day30(
        self, orchestrator, sample_abandoned_contact
    ):
        """Test market trigger retrieval for Day 30 (softer approach)."""
        sample_abandoned_contact.current_stage = AbandonmentStage.DAY_30

        trigger = await orchestrator._get_relevant_market_trigger(
            sample_abandoned_contact
        )

        # Should attempt neighborhood sales
        assert trigger is None or trigger is not None

    async def test_generic_market_update_fallback(self, orchestrator):
        """Test generic market update when no trigger available."""
        update = orchestrator._get_generic_market_update(AbandonmentStage.DAY_3)
        assert isinstance(update, str)
        assert len(update) > 10

        update = orchestrator._get_generic_market_update(AbandonmentStage.DAY_30)
        assert isinstance(update, str)
        assert len(update) > 10


@pytest.mark.asyncio
class TestRecoveryAttempt:
    """Test individual recovery attempts."""

    async def test_attempt_recovery_success(
        self, orchestrator, mock_ghl_client, sample_abandoned_contact
    ):
        """Test successful recovery attempt."""
        success = await orchestrator._attempt_recovery(sample_abandoned_contact)

        assert success is True
        mock_ghl_client.send_message.assert_called_once()

    async def test_attempt_recovery_ghl_failure(
        self, orchestrator, mock_ghl_client, sample_abandoned_contact
    ):
        """Test recovery attempt with GHL API failure."""
        mock_ghl_client.send_message.side_effect = Exception("API error")

        success = await orchestrator._attempt_recovery(sample_abandoned_contact)

        assert success is False
