"""Integration tests for abandonment recovery system.

Tests the full flow: detection → orchestration → recovery.
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.abandonment_detector import (
    AbandonmentDetector,
    AbandonmentStage,
)
from ghl_real_estate_ai.services.jorge.recovery_orchestrator import (
    RecoveryOrchestrator,
)


@pytest.mark.asyncio
class TestAbandonmentRecoveryFlow:
    """Test end-to-end abandonment recovery flow."""

    async def test_full_recovery_flow(self):
        """Test complete flow from detection to recovery."""
        # Mock dependencies
        mock_ghl_client = AsyncMock()
        mock_db_pool = AsyncMock()

        # Mock database query to return abandoned contact
        current_time = time.time()
        last_contact = current_time - (4 * 24 * 3600)  # 4 days ago

        mock_db_pool.fetch.return_value = [
            {
                "contact_id": "c123",
                "location_id": "loc123",
                "bot_type": "lead",
                "last_contact_timestamp": last_contact,
                "current_stage": "24h",
                "recovery_attempt_count": 0,
                "metadata": {
                    "name": "John Doe",
                    "interest_area": "Rancho Cucamonga",
                },
            }
        ]

        # Initialize services
        detector = AbandonmentDetector(
            ghl_client=mock_ghl_client, db_pool=mock_db_pool
        )
        orchestrator = RecoveryOrchestrator(ghl_client=mock_ghl_client)

        # Step 1: Detect abandoned contacts
        abandoned_contacts = await detector.detect_abandoned_contacts("loc123")
        assert len(abandoned_contacts) == 1
        assert abandoned_contacts[0].current_stage == AbandonmentStage.DAY_3

        # Step 2: Orchestrate recovery
        summary = await orchestrator.orchestrate_recovery(abandoned_contacts)
        assert summary["successful"] == 1
        assert summary["by_stage"]["3d"] == 1

        # Step 3: Verify message sent
        mock_ghl_client.send_message.assert_called_once()

        # Step 4: Mark recovery attempted
        await detector.mark_recovery_attempted("c123", AbandonmentStage.DAY_3)
        mock_db_pool.execute.assert_called()

    async def test_multi_stage_recovery_progression(self):
        """Test recovery progression across multiple stages."""
        mock_ghl_client = AsyncMock()
        mock_db_pool = AsyncMock()

        detector = AbandonmentDetector(
            ghl_client=mock_ghl_client, db_pool=mock_db_pool
        )
        orchestrator = RecoveryOrchestrator(ghl_client=mock_ghl_client)

        current_time = time.time()

        # Simulate progression: Day 3 → Day 7 → Day 14
        stages = [
            (4 * 24 * 3600, AbandonmentStage.DAY_3),
            (8 * 24 * 3600, AbandonmentStage.DAY_7),
            (15 * 24 * 3600, AbandonmentStage.DAY_14),
        ]

        for silence_sec, expected_stage in stages:
            last_contact = current_time - silence_sec

            mock_db_pool.fetch.return_value = [
                {
                    "contact_id": "c123",
                    "location_id": "loc123",
                    "bot_type": "lead",
                    "last_contact_timestamp": last_contact,
                    "current_stage": "24h",
                    "recovery_attempt_count": 0,
                    "metadata": {"name": "John"},
                }
            ]

            # Detect
            contacts = await detector.detect_abandoned_contacts("loc123")
            assert len(contacts) == 1
            assert contacts[0].current_stage == expected_stage

            # Recover
            summary = await orchestrator.orchestrate_recovery(contacts)
            assert summary["successful"] == 1

    async def test_recovery_skip_already_attempted(self):
        """Test that recovery is skipped if already attempted at current stage."""
        mock_ghl_client = AsyncMock()
        mock_db_pool = AsyncMock()

        current_time = time.time()
        last_contact = current_time - (4 * 24 * 3600)  # 4 days

        # Contact already recovered at Day 3 stage
        mock_db_pool.fetch.return_value = [
            {
                "contact_id": "c123",
                "location_id": "loc123",
                "bot_type": "lead",
                "last_contact_timestamp": last_contact,
                "current_stage": "3d",  # Already at Day 3
                "recovery_attempt_count": 1,
                "metadata": {"name": "John"},
            }
        ]

        detector = AbandonmentDetector(
            ghl_client=mock_ghl_client, db_pool=mock_db_pool
        )

        # Detect - should return empty because still at same stage
        contacts = await detector.detect_abandoned_contacts("loc123")
        assert len(contacts) == 0  # Not eligible for recovery yet

    async def test_re_engagement_clears_abandonment(self):
        """Test that re-engagement clears abandonment tracking."""
        mock_db_pool = AsyncMock()

        detector = AbandonmentDetector(ghl_client=None, db_pool=mock_db_pool)

        # Clear abandonment
        await detector.clear_abandonment("c123")

        # Verify DELETE was called
        mock_db_pool.execute.assert_called_once()
        call_args = mock_db_pool.execute.call_args[0]
        assert "DELETE FROM abandonment_events" in call_args[0]


@pytest.mark.asyncio
class TestBackgroundTaskIntegration:
    """Test background task integration."""

    @patch("ghl_real_estate_ai.services.jorge.abandonment_detector.get_abandonment_detector")
    @patch("ghl_real_estate_ai.services.jorge.recovery_orchestrator.get_recovery_orchestrator")
    async def test_background_task_one_iteration(
        self, mock_get_orchestrator, mock_get_detector
    ):
        """Test one iteration of background task loop."""
        # Mock detector and orchestrator
        mock_detector = AsyncMock()
        mock_orchestrator = AsyncMock()
        mock_get_detector.return_value = mock_detector
        mock_get_orchestrator.return_value = mock_orchestrator

        # Mock detection returns one contact
        from ghl_real_estate_ai.services.jorge.abandonment_detector import (
            AbandonedContact,
            AbandonmentStage,
        )

        mock_detector.detect_abandoned_contacts.return_value = [
            AbandonedContact(
                contact_id="c123",
                location_id="loc123",
                bot_type="lead",
                last_contact_timestamp=time.time() - (4 * 24 * 3600),
                silence_duration_hours=96.0,
                current_stage=AbandonmentStage.DAY_3,
                recovery_attempt_count=0,
                contact_metadata={},
            )
        ]

        mock_orchestrator.orchestrate_recovery.return_value = {
            "successful": 1,
            "total_attempted": 1,
            "contacts_processed": [
                {"contact_id": "c123", "stage": "3d", "status": "success"}
            ],
        }

        # Import and run one iteration
        from ghl_real_estate_ai.services.jorge.abandonment_background_task import (
            start_abandonment_background_task,
            stop_abandonment_background_task,
        )

        # Start task (will run in background)
        started = await start_abandonment_background_task(
            ghl_client=AsyncMock(),
            db_pool=AsyncMock(),
            interval_seconds=0.1,  # Short interval for testing
        )
        assert started is True

        # Let it run one iteration
        await asyncio.sleep(0.2)

        # Stop task
        await stop_abandonment_background_task()

        # Verify detector was called
        mock_detector.detect_abandoned_contacts.assert_called()
