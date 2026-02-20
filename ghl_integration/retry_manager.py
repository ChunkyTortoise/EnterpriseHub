"""
Webhook Retry Manager & Dead Letter Queue

Manages webhook retry logic with exponential backoff.
Failed webhooks are moved to a dead letter queue after max retries.
"""

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from ghl_real_estate_ai.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class RetryStatus(Enum):
    """Retry status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    DLQ = "dlq"  # Dead letter queue


@dataclass
class RetryEntry:
    """Represents a webhook retry entry"""
    event_id: str
    bot_type: str
    event_type: str
    payload: Dict[str, Any]
    attempt: int
    max_attempts: int
    status: str
    created_at: str
    last_attempt_at: Optional[str] = None
    next_attempt_at: Optional[str] = None
    error_history: List[str] = None
    
    def __post_init__(self):
        if self.error_history is None:
            self.error_history = []


class WebhookRetryManager:
    """
    Manages webhook retry logic and dead letter queue.
    
    Strategy:
    - Immediate: 3 attempts with exponential backoff (1s, 2s, 4s)
    - Delayed: Re-queue to Redis for retry after 1min, 5min, 15min
    - Dead Letter: After all retries exhausted, store for manual review
    
    Redis keys:
    - ghl:webhooks:retry:{event_id} - retry metadata
    - ghl:webhooks:retry:queue - sorted set for scheduled retries (score = timestamp)
    - ghl:webhooks:dlq - dead letter queue (Redis list)
    - ghl:webhooks:processing:{event_id} - in-flight tracking
    """

    # Immediate retry delays (seconds)
    IMMEDIATE_DELAYS = [1, 2, 4]
    
    # Delayed retry delays (minutes)
    DELAYED_DELAYS = [1, 5, 15]
    
    MAX_TOTAL_ATTEMPTS = 6  # 3 immediate + 3 delayed

    def __init__(self):
        self.cache = CacheService()
        self.processing: Set[str] = set()
        self._shutdown = False
        self._retry_worker: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize retry manager and start background worker"""
        self._retry_worker = asyncio.create_task(self._retry_worker_loop())
        logger.info("Retry manager initialized")

    async def shutdown(self):
        """Shutdown retry manager"""
        self._shutdown = True
        if self._retry_worker:
            self._retry_worker.cancel()
            try:
                await self._retry_worker
            except asyncio.CancelledError:
                pass
        logger.info("Retry manager shutdown complete")

    async def schedule_retry(
        self,
        bot_type: str,
        event_type: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
        attempt: int = 0,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Schedule a webhook for retry.
        
        Returns:
            Dict with retry info including scheduled time
        """
        if not event_id:
            import hashlib
            event_id = hashlib.md5(
                json.dumps(payload, sort_keys=True).encode()
            ).hexdigest()

        # Check if already at max attempts
        if attempt >= self.MAX_TOTAL_ATTEMPTS:
            await self._send_to_dlq(event_id, bot_type, event_type, payload, error)
            return {
                "event_id": event_id,
                "status": "dlq",
                "message": "Max retries exceeded, sent to DLQ",
            }

        # Calculate next retry time
        if attempt < len(self.IMMEDIATE_DELAYS):
            # Immediate retry
            delay_seconds = self.IMMEDIATE_DELAYS[attempt]
            next_attempt = datetime.utcnow() + timedelta(seconds=delay_seconds)
        else:
            # Delayed retry
            delay_index = attempt - len(self.IMMEDIATE_DELAYS)
            if delay_index < len(self.DELAYED_DELAYS):
                delay_minutes = self.DELAYED_DELAYS[delay_index]
                next_attempt = datetime.utcnow() + timedelta(minutes=delay_minutes)
            else:
                # Fallback to max delayed retry
                next_attempt = datetime.utcnow() + timedelta(minutes=30)

        # Create retry entry
        entry = RetryEntry(
            event_id=event_id,
            bot_type=bot_type,
            event_type=event_type,
            payload=payload,
            attempt=attempt + 1,
            max_attempts=self.MAX_TOTAL_ATTEMPTS,
            status=RetryStatus.PENDING.value,
            created_at=datetime.utcnow().isoformat(),
            last_attempt_at=datetime.utcnow().isoformat() if attempt > 0 else None,
            next_attempt_at=next_attempt.isoformat(),
            error_history=[error] if error else [],
        )

        # Store retry entry
        await self._store_retry_entry(entry)

        # Add to retry queue (sorted set by timestamp)
        score = next_attempt.timestamp()
        await self._add_to_retry_queue(event_id, score)

        logger.info(
            f"Scheduled retry {entry.attempt}/{entry.max_attempts} "
            f"for {bot_type}/{event_type} at {next_attempt}"
        )

        return {
            "event_id": event_id,
            "status": "scheduled",
            "attempt": entry.attempt,
            "max_attempts": entry.max_attempts,
            "next_attempt_at": entry.next_attempt_at,
        }

    async def record_success(self, event_id: str):
        """Mark a webhook as successfully processed"""
        try:
            # Remove from retry queue and storage
            await self.cache.delete(f"ghl:webhooks:retry:{event_id}")
            await self.cache.zrem("ghl:webhooks:retry:queue", event_id)
            self.processing.discard(event_id)
            logger.debug(f"Retry success recorded for {event_id}")
        except Exception as e:
            logger.error(f"Failed to record success: {e}")

    async def get_dlq_contents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get contents of dead letter queue"""
        try:
            entries = await self.cache.lrange("ghl:webhooks:dlq", 0, limit - 1)
            return [json.loads(e) for e in entries if e]
        except Exception as e:
            logger.error(f"Failed to get DLQ contents: {e}")
            return []

    async def retry_dlq_item(self, event_id: str) -> Dict[str, Any]:
        """Retry a specific DLQ item"""
        try:
            # Find in DLQ
            dlq_contents = await self.get_dlq_contents(limit=1000)
            for item in dlq_contents:
                if item.get("event_id") == event_id:
                    # Remove from DLQ
                    await self.cache.lrem("ghl:webhooks:dlq", 0, json.dumps(item))
                    # Re-schedule with reset attempt count
                    return await self.schedule_retry(
                        bot_type=item["bot_type"],
                        event_type=item["event_type"],
                        payload=item["payload"],
                        event_id=event_id,
                        attempt=0,
                    )
            
            return {"error": "Event not found in DLQ"}

        except Exception as e:
            logger.error(f"Failed to retry DLQ item: {e}")
            return {"error": str(e)}

    async def get_metrics(self) -> Dict[str, Any]:
        """Get retry manager metrics"""
        try:
            retry_queue_size = await self.cache.zcard("ghl:webhooks:retry:queue")
            dlq_size = await self.cache.llen("ghl:webhooks:dlq")
            
            return {
                "retry_queue_size": retry_queue_size,
                "dlq_size": dlq_size,
                "processing_count": len(self.processing),
            }
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {
                "retry_queue_size": 0,
                "dlq_size": 0,
                "processing_count": 0,
                "error": str(e),
            }

    async def _store_retry_entry(self, entry: RetryEntry):
        """Store retry entry in cache"""
        key = f"ghl:webhooks:retry:{entry.event_id}"
        value = json.dumps(asdict(entry))
        # Store with longer TTL (7 days)
        await self.cache.set(key, value, ttl=604800)

    async def _get_retry_entry(self, event_id: str) -> Optional[RetryEntry]:
        """Get retry entry from cache"""
        key = f"ghl:webhooks:retry:{event_id}"
        value = await self.cache.get(key)
        if value:
            data = json.loads(value)
            return RetryEntry(**data)
        return None

    async def _add_to_retry_queue(self, event_id: str, score: float):
        """Add event to retry queue (sorted set)"""
        await self.cache.zadd("ghl:webhooks:retry:queue", {event_id: score})

    async def _get_due_retries(self, limit: int = 10) -> List[str]:
        """Get events that are due for retry"""
        now = datetime.utcnow().timestamp()
        # Get items with score <= now
        return await self.cache.zrangebyscore("ghl:webhooks:retry:queue", 0, now, limit)

    async def _send_to_dlq(
        self,
        event_id: str,
        bot_type: str,
        event_type: str,
        payload: Dict[str, Any],
        final_error: Optional[str],
    ):
        """Send exhausted webhook to dead letter queue"""
        dlq_entry = {
            "event_id": event_id,
            "bot_type": bot_type,
            "event_type": event_type,
            "payload": payload,
            "final_error": final_error,
            "sent_to_dlq_at": datetime.utcnow().isoformat(),
        }
        
        # Add to DLQ (left push for newest first)
        await self.cache.lpush("ghl:webhooks:dlq", json.dumps(dlq_entry))
        
        # Trim DLQ to max 1000 entries
        await self.cache.ltrim("ghl:webhooks:dlq", 0, 999)
        
        # Clean up retry entry
        await self.cache.delete(f"ghl:webhooks:retry:{event_id}")
        await self.cache.zrem("ghl:webhooks:retry:queue", event_id)
        
        logger.warning(
            f"Event {event_id} ({bot_type}/{event_type}) sent to DLQ: {final_error}"
        )

    async def _retry_worker_loop(self):
        """Background worker to process scheduled retries"""
        logger.info("Retry worker started")
        
        while not self._shutdown:
            try:
                # Get due retries
                due_events = await self._get_due_retries(limit=5)
                
                if due_events:
                    logger.info(f"Processing {len(due_events)} due retries")
                    
                    for event_id in due_events:
                        if self._shutdown:
                            break
                        
                        # Skip if already processing
                        if event_id in self.processing:
                            continue
                        
                        self.processing.add(event_id)
                        
                        try:
                            # Get retry entry
                            entry = await self._get_retry_entry(event_id)
                            if not entry:
                                continue
                            
                            # Remove from queue temporarily
                            await self.cache.zrem("ghl:webhooks:retry:queue", event_id)
                            
                            # Attempt retry
                            success = await self._attempt_retry(entry)
                            
                            if success:
                                await self.record_success(event_id)
                            else:
                                # Schedule next retry
                                await self.schedule_retry(
                                    bot_type=entry.bot_type,
                                    event_type=entry.event_type,
                                    payload=entry.payload,
                                    event_id=event_id,
                                    attempt=entry.attempt,
                                    error=f"Retry attempt {entry.attempt} failed",
                                )
                        
                        except Exception as e:
                            logger.error(f"Retry processing error for {event_id}: {e}")
                        
                        finally:
                            self.processing.discard(event_id)
                
                # Wait before next check
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Retry worker error: {e}")
                await asyncio.sleep(10)
        
        logger.info("Retry worker stopped")

    async def _attempt_retry(self, entry: RetryEntry) -> bool:
        """Attempt to retry a webhook. Returns True on success."""
        try:
            # Import handler dynamically
            handler = self._get_handler(entry.bot_type, entry.event_type)
            if not handler:
                logger.error(f"No handler found for {entry.bot_type}/{entry.event_type}")
                return False
            
            # Call handler
            result = await handler(entry.payload)
            
            # Check result
            if isinstance(result, dict):
                return result.get("success", False)
            return True
        
        except Exception as e:
            logger.error(f"Retry attempt failed: {e}")
            return False

    def _get_handler(self, bot_type: str, event_type: str) -> Optional[Callable]:
        """Get handler function for bot type and event type"""
        try:
            # Map to handler module
            if bot_type == "lead":
                from .handlers.lead_handlers import get_handler
            elif bot_type == "seller":
                from .handlers.seller_handlers import get_handler
            elif bot_type == "buyer":
                from .handlers.buyer_handlers import get_handler
            else:
                return None
            
            return get_handler(event_type)
        except Exception as e:
            logger.error(f"Failed to get handler: {e}")
            return None


# Singleton instance
_retry_manager: Optional[WebhookRetryManager] = None


async def get_retry_manager() -> WebhookRetryManager:
    """Get or create retry manager singleton"""
    global _retry_manager
    if _retry_manager is None:
        _retry_manager = WebhookRetryManager()
        await _retry_manager.initialize()
    return _retry_manager
