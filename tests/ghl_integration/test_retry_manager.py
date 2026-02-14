"""
Test Retry Manager & Dead Letter Queue
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ghl_integration.retry_manager import (
    WebhookRetryManager,
    RetryStatus,
    RetryEntry,
    get_retry_manager,
)


class TestRetryManager:
    """Test suite for webhook retry manager"""

    @pytest.fixture
    def retry_manager(self, mock_cache_service):
        manager = WebhookRetryManager()
        manager.cache = mock_cache_service
        return manager

    def test_init(self, retry_manager):
        """Test retry manager initialization"""
        assert retry_manager.processing == set()
        assert retry_manager._shutdown is False

    @pytest.mark.asyncio
    async def test_schedule_retry_first_attempt(self, retry_manager, mock_cache_service):
        """Test scheduling first retry attempt"""
        result = await retry_manager.schedule_retry(
            bot_type="lead",
            event_type="contact.create",
            payload={"test": "data"},
            event_id="evt_123",
            attempt=0
        )
        
        assert result["status"] == "scheduled"
        assert result["attempt"] == 1
        assert result["max_attempts"] == 6
        # First immediate retry should be ~1 second delay
        assert "next_attempt_at" in result

    @pytest.mark.asyncio
    async def test_schedule_retry_immediate_delays(self, retry_manager, mock_cache_service):
        """Test immediate retry delays (1s, 2s, 4s)"""
        delays = []
        
        for attempt in range(3):
            result = await retry_manager.schedule_retry(
                bot_type="lead",
                event_type="contact.create",
                payload={"test": "data"},
                event_id=f"evt_{attempt}",
                attempt=attempt
            )
            
            next_time = datetime.fromisoformat(result["next_attempt_at"])
            delay = (next_time - datetime.utcnow()).total_seconds()
            delays.append(round(delay))
        
        assert delays == [1, 2, 4]

    @pytest.mark.asyncio
    async def test_schedule_retry_delayed_delays(self, retry_manager, mock_cache_service):
        """Test delayed retry delays (1min, 5min, 15min)"""
        delays = []
        
        for attempt in range(3, 6):
            result = await retry_manager.schedule_retry(
                bot_type="lead",
                event_type="contact.create",
                payload={"test": "data"},
                event_id=f"evt_{attempt}",
                attempt=attempt
            )
            
            next_time = datetime.fromisoformat(result["next_attempt_at"])
            delay = (next_time - datetime.utcnow()).total_seconds()
            delays.append(round(delay / 60))  # Convert to minutes
        
        assert delays == [1, 5, 15]

    @pytest.mark.asyncio
    async def test_schedule_retry_max_attempts_reached(self, retry_manager, mock_cache_service):
        """Test that max attempts sends to DLQ"""
        result = await retry_manager.schedule_retry(
            bot_type="lead",
            event_type="contact.create",
            payload={"test": "data"},
            event_id="evt_123",
            attempt=6,  # Max attempts
            error="Final failure"
        )
        
        assert result["status"] == "dlq"
        assert "DLQ" in result["message"]
        mock_cache_service.lpush.assert_called()

    @pytest.mark.asyncio
    async def test_schedule_retry_generates_event_id(self, retry_manager, mock_cache_service):
        """Test that event ID is generated if not provided"""
        result = await retry_manager.schedule_retry(
            bot_type="lead",
            event_type="contact.create",
            payload={"test": "data"}
        )
        
        assert "event_id" in result
        assert len(result["event_id"]) == 32  # MD5 hash length

    @pytest.mark.asyncio
    async def test_record_success(self, retry_manager, mock_cache_service):
        """Test recording successful processing"""
        await retry_manager.record_success("evt_123")
        
        mock_cache_service.delete.assert_called_with("ghl:webhooks:retry:evt_123")
        mock_cache_service.zrem.assert_called_with("ghl:webhooks:retry:queue", "evt_123")

    @pytest.mark.asyncio
    async def test_get_dlq_contents(self, retry_manager, mock_cache_service):
        """Test retrieving DLQ contents"""
        dlq_items = [
            json.dumps({"event_id": "evt_1", "error": "failed"}),
            json.dumps({"event_id": "evt_2", "error": "timeout"}),
        ]
        mock_cache_service.lrange.return_value = dlq_items
        
        result = await retry_manager.get_dlq_contents(limit=10)
        
        assert len(result) == 2
        assert result[0]["event_id"] == "evt_1"
        mock_cache_service.lrange.assert_called_with("ghl:webhooks:dlq", 0, 9)

    @pytest.mark.asyncio
    async def test_retry_dlq_item_found(self, retry_manager, mock_cache_service):
        """Test retrying an item from DLQ"""
        dlq_item = json.dumps({
            "event_id": "evt_123",
            "bot_type": "lead",
            "event_type": "contact.create",
            "payload": {"test": "data"}
        })
        mock_cache_service.lrange.return_value = [dlq_item]
        
        result = await retry_manager.retry_dlq_item("evt_123")
        
        assert result["status"] == "scheduled"
        assert result["attempt"] == 1  # Reset to first attempt
        mock_cache_service.lrem.assert_called()

    @pytest.mark.asyncio
    async def test_retry_dlq_item_not_found(self, retry_manager, mock_cache_service):
        """Test retrying an item not in DLQ"""
        mock_cache_service.lrange.return_value = []
        
        result = await retry_manager.retry_dlq_item("evt_999")
        
        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_metrics(self, retry_manager, mock_cache_service):
        """Test getting retry manager metrics"""
        mock_cache_service.zcard.return_value = 5
        mock_cache_service.llen.return_value = 3
        retry_manager.processing = {"evt_1", "evt_2"}
        
        metrics = await retry_manager.get_metrics()
        
        assert metrics["retry_queue_size"] == 5
        assert metrics["dlq_size"] == 3
        assert metrics["processing_count"] == 2

    @pytest.mark.asyncio
    async def test_store_and_get_retry_entry(self, retry_manager, mock_cache_service):
        """Test storing and retrieving retry entry"""
        entry = RetryEntry(
            event_id="evt_123",
            bot_type="lead",
            event_type="contact.create",
            payload={"test": "data"},
            attempt=2,
            max_attempts=6,
            status=RetryStatus.PENDING.value,
            created_at=datetime.utcnow().isoformat()
        )
        
        await retry_manager._store_retry_entry(entry)
        
        mock_cache_service.set.assert_called_once()
        call_args = mock_cache_service.set.call_args
        assert call_args[0][0] == "ghl:webhooks:retry:evt_123"
        assert "test" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_due_retries(self, retry_manager, mock_cache_service):
        """Test getting due retries from queue"""
        mock_cache_service.zrangebyscore.return_value = ["evt_1", "evt_2"]
        
        due = await retry_manager._get_due_retries(limit=5)
        
        assert due == ["evt_1", "evt_2"]
        mock_cache_service.zrangebyscore.assert_called()

    @pytest.mark.asyncio
    async def test_send_to_dlq(self, retry_manager, mock_cache_service):
        """Test sending exhausted webhook to DLQ"""
        await retry_manager._send_to_dlq(
            event_id="evt_123",
            bot_type="lead",
            event_type="contact.create",
            payload={"test": "data"},
            final_error="Max retries exceeded"
        )
        
        mock_cache_service.lpush.assert_called_once()
        mock_cache_service.ltrim.assert_called_once_with("ghl:webhooks:dlq", 0, 999)
        mock_cache_service.delete.assert_called_with("ghl:webhooks:retry:evt_123")
        mock_cache_service.zrem.assert_called_with("ghl:webhooks:retry:queue", "evt_123")

    def test_retry_status_enum(self):
        """Test retry status enumeration values"""
        assert RetryStatus.PENDING.value == "pending"
        assert RetryStatus.PROCESSING.value == "processing"
        assert RetryStatus.SUCCESS.value == "success"
        assert RetryStatus.FAILED.value == "failed"
        assert RetryStatus.DLQ.value == "dlq"


class TestRetryEntry:
    """Test suite for RetryEntry dataclass"""

    def test_entry_creation(self):
        """Test creating retry entry"""
        entry = RetryEntry(
            event_id="evt_123",
            bot_type="lead",
            event_type="contact.create",
            payload={"test": "data"},
            attempt=1,
            max_attempts=6,
            status="pending",
            created_at="2026-02-11T10:00:00Z"
        )
        
        assert entry.event_id == "evt_123"
        assert entry.attempt == 1
        assert entry.error_history == []  # Auto-initialized

    def test_entry_with_error_history(self):
        """Test entry with error history"""
        entry = RetryEntry(
            event_id="evt_123",
            bot_type="lead",
            event_type="contact.create",
            payload={},
            attempt=3,
            max_attempts=6,
            status="failed",
            created_at="2026-02-11T10:00:00Z",
            error_history=["Error 1", "Error 2"]
        )
        
        assert len(entry.error_history) == 2
        assert entry.error_history[0] == "Error 1"
