"""Tests for abandonment detection service."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.services.jorge.abandonment_detector import (
    AbandonedContact,
    AbandonmentDetector,
    AbandonmentStage,
    STAGE_THRESHOLDS,
)


@pytest.fixture
def mock_ghl_client():
    """Mock GHL client."""
    client = AsyncMock()
    client.send_message = AsyncMock()
    return client


@pytest.fixture
def mock_db_pool():
    """Mock database pool."""
    pool = AsyncMock()
    pool.fetch = AsyncMock()
    pool.execute = AsyncMock()
    return pool


@pytest.fixture
def detector(mock_ghl_client, mock_db_pool):
    """Create detector with mocked dependencies."""
    return AbandonmentDetector(ghl_client=mock_ghl_client, db_pool=mock_db_pool)


class TestAbandonmentStageDetection:
    """Test abandonment stage determination."""

    def test_determine_stage_24h(self, detector):
        """Test 24h stage detection."""
        # 25 hours = 90000 seconds
        stage = detector._determine_stage(25 * 3600)
        assert stage == AbandonmentStage.HOUR_24

    def test_determine_stage_3d(self, detector):
        """Test 3-day stage detection."""
        # 4 days = 345600 seconds
        stage = detector._determine_stage(4 * 24 * 3600)
        assert stage == AbandonmentStage.DAY_3

    def test_determine_stage_7d(self, detector):
        """Test 7-day stage detection."""
        # 8 days
        stage = detector._determine_stage(8 * 24 * 3600)
        assert stage == AbandonmentStage.DAY_7

    def test_determine_stage_14d(self, detector):
        """Test 14-day stage detection."""
        # 15 days
        stage = detector._determine_stage(15 * 24 * 3600)
        assert stage == AbandonmentStage.DAY_14

    def test_determine_stage_30d(self, detector):
        """Test 30-day stage detection."""
        # 35 days
        stage = detector._determine_stage(35 * 24 * 3600)
        assert stage == AbandonmentStage.DAY_30


class TestRecoveryEligibility:
    """Test recovery attempt eligibility logic."""

    def test_should_attempt_recovery_never_attempted(self, detector):
        """Test recovery eligible when never attempted."""
        assert detector._should_attempt_recovery(
            AbandonmentStage.DAY_3, None
        ) is True

    def test_should_attempt_recovery_stage_advancement(self, detector):
        """Test recovery eligible when stage advances."""
        # Last recovered at 3d, now at 7d
        assert detector._should_attempt_recovery(
            AbandonmentStage.DAY_7, AbandonmentStage.DAY_3
        ) is True

    def test_should_not_attempt_recovery_same_stage(self, detector):
        """Test recovery not eligible at same stage."""
        # Last recovered at 7d, still at 7d
        assert detector._should_attempt_recovery(
            AbandonmentStage.DAY_7, AbandonmentStage.DAY_7
        ) is False

    def test_should_not_attempt_recovery_earlier_stage(self, detector):
        """Test recovery not eligible at earlier stage (edge case)."""
        # Last recovered at 14d, somehow at 7d (shouldn't happen but test logic)
        assert detector._should_attempt_recovery(
            AbandonmentStage.DAY_7, AbandonmentStage.DAY_14
        ) is False


@pytest.mark.asyncio
class TestAbandonmentDetection:
    """Test abandonment detection from database."""

    async def test_detect_abandoned_contacts_no_client(self):
        """Test detection without GHL client returns empty list."""
        detector = AbandonmentDetector(ghl_client=None, db_pool=None)
        contacts = await detector.detect_abandoned_contacts("loc123")
        assert contacts == []

    async def test_detect_abandoned_contacts_no_pool(self, mock_ghl_client):
        """Test detection without DB pool returns empty list."""
        detector = AbandonmentDetector(ghl_client=mock_ghl_client, db_pool=None)
        contacts = await detector.detect_abandoned_contacts("loc123")
        assert contacts == []

    async def test_detect_abandoned_contacts_empty_result(
        self, detector, mock_db_pool
    ):
        """Test detection with no abandoned contacts."""
        mock_db_pool.fetch.return_value = []

        contacts = await detector.detect_abandoned_contacts("loc123")
        assert contacts == []
        mock_db_pool.fetch.assert_called_once()

    async def test_detect_abandoned_contacts_with_results(
        self, detector, mock_db_pool
    ):
        """Test detection with abandoned contacts."""
        current_time = time.time()
        last_contact = current_time - (5 * 24 * 3600)  # 5 days ago

        mock_db_pool.fetch.return_value = [
            {
                "contact_id": "contact123",
                "location_id": "loc123",
                "bot_type": "lead",
                "last_contact_timestamp": last_contact,
                "current_stage": "24h",
                "recovery_attempt_count": 0,
                "metadata": {"name": "John Doe"},
            }
        ]

        contacts = await detector.detect_abandoned_contacts("loc123")

        assert len(contacts) == 1
        contact = contacts[0]
        assert contact.contact_id == "contact123"
        assert contact.current_stage == AbandonmentStage.DAY_3
        assert contact.recovery_attempt_count == 0
        assert contact.silence_duration_days > 4.9


@pytest.mark.asyncio
class TestRecordAbandonment:
    """Test recording abandonment events."""

    async def test_record_abandonment_no_pool(self, mock_ghl_client):
        """Test recording without DB pool logs warning."""
        detector = AbandonmentDetector(ghl_client=mock_ghl_client, db_pool=None)
        # Should not raise, just log
        await detector.record_abandonment(
            contact_id="c123",
            location_id="loc123",
            bot_type="lead",
            last_contact_timestamp=time.time(),
        )

    async def test_record_abandonment_success(self, detector, mock_db_pool):
        """Test successful abandonment recording."""
        current_time = time.time()

        await detector.record_abandonment(
            contact_id="c123",
            location_id="loc123",
            bot_type="lead",
            last_contact_timestamp=current_time,
            metadata={"name": "John"},
        )

        mock_db_pool.execute.assert_called_once()
        call_args = mock_db_pool.execute.call_args[0]
        assert "INSERT INTO abandonment_events" in call_args[0]
        assert call_args[1] == "c123"
        assert call_args[2] == "loc123"


@pytest.mark.asyncio
class TestMarkRecoveryAttempt:
    """Test marking recovery attempts."""

    async def test_mark_recovery_attempted_success(self, detector, mock_db_pool):
        """Test successful recovery attempt marking."""
        await detector.mark_recovery_attempted("c123", AbandonmentStage.DAY_3)

        mock_db_pool.execute.assert_called_once()
        call_args = mock_db_pool.execute.call_args[0]
        assert "UPDATE abandonment_events" in call_args[0]
        assert call_args[1] == "c123"
        assert call_args[2] == "3d"


@pytest.mark.asyncio
class TestClearAbandonment:
    """Test clearing abandonment tracking."""

    async def test_clear_abandonment_success(self, detector, mock_db_pool):
        """Test successful abandonment clearing."""
        await detector.clear_abandonment("c123")

        mock_db_pool.execute.assert_called_once()
        call_args = mock_db_pool.execute.call_args[0]
        assert "DELETE FROM abandonment_events" in call_args[0]
        assert call_args[1] == "c123"


class TestAbandonedContactModel:
    """Test AbandonedContact data model."""

    def test_abandoned_contact_properties(self):
        """Test AbandonedContact computed properties."""
        contact = AbandonedContact(
            contact_id="c123",
            location_id="loc123",
            bot_type="lead",
            last_contact_timestamp=time.time() - (48 * 3600),
            silence_duration_hours=48.0,
            current_stage=AbandonmentStage.DAY_3,
            recovery_attempt_count=1,
            contact_metadata={"name": "John"},
        )

        assert contact.silence_duration_days == 2.0

    def test_abandoned_contact_to_dict(self):
        """Test AbandonedContact serialization."""
        current_time = time.time()
        contact = AbandonedContact(
            contact_id="c123",
            location_id="loc123",
            bot_type="lead",
            last_contact_timestamp=current_time,
            silence_duration_hours=72.0,
            current_stage=AbandonmentStage.DAY_3,
            recovery_attempt_count=1,
            contact_metadata={"name": "John"},
        )

        data = contact.to_dict()
        assert data["contact_id"] == "c123"
        assert data["current_stage"] == "3d"
        assert data["silence_duration_days"] == 3.0
        assert "last_contact_date" in data
