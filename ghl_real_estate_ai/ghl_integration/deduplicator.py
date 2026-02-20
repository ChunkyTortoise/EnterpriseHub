"""
Event Deduplicator

Prevents duplicate webhook processing using Redis cache.
24-hour TTL window for event deduplication.
"""

import hashlib
import logging
from typing import Any, Dict, Optional

from ghl_real_estate_ai.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class EventDeduplicator:
    """
    Webhook event deduplicator using Redis.
    
    Strategy:
    - Generate unique key from event content
    - Store in Redis with 24h TTL
    - Skip processing if key exists
    """

    DEDUP_TTL_SECONDS = 86400  # 24 hours

    def __init__(self):
        self.cache = CacheService()

    def generate_key(
        self,
        event_id: Optional[str],
        event_type: str,
        payload: Dict[str, Any]
    ) -> str:
        """
        Generate deduplication key.
        
        Priority:
        1. Explicit event_id from payload
        2. Composite of event type + entity IDs
        3. Hash of payload content
        """
        if event_id:
            return f"ghl:dedup:{event_id}"

        # Try to extract entity IDs
        entity_parts = [event_type]
        
        data = payload.get("data", payload)
        
        # Add contact/opportunity ID if present
        for key in ["id", "contact_id", "opportunity_id", "conversation_id"]:
            if key in data:
                entity_parts.append(str(data[key]))
                break

        # Add timestamp if present (rounded to minute for batch events)
        timestamp = payload.get("timestamp") or data.get("dateAdded")
        if timestamp:
            # Round to nearest minute for batch dedup
            from datetime import datetime
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    entity_parts.append(dt.strftime("%Y%m%d%H%M"))
            except (ValueError, TypeError):
                pass

        if len(entity_parts) > 1:
            return f"ghl:dedup:{':'.join(entity_parts)}"

        # Fallback: hash the payload
        import json
        payload_str = json.dumps(payload, sort_keys=True)
        content_hash = hashlib.md5(payload_str.encode()).hexdigest()
        return f"ghl:dedup:{event_type}:{content_hash}"

    async def is_duplicate(self, key: str) -> bool:
        """Check if event with given key has been processed"""
        try:
            exists = await self.cache.get(key)
            if exists:
                logger.debug(f"Duplicate event detected: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Deduplication check failed: {e}")
            # Allow through on error (fail open)
            return False

    async def mark_processed(self, key: str, metadata: Optional[Dict] = None):
        """Mark event as processed"""
        try:
            value = "1"
            if metadata:
                import json
                value = json.dumps(metadata)
            
            await self.cache.set(key, value, ttl=self.DEDUP_TTL_SECONDS)
        except Exception as e:
            logger.error(f"Failed to mark event as processed: {e}")

    async def get_metadata(self, key: str) -> Optional[Dict]:
        """Get metadata for a processed event"""
        try:
            value = await self.cache.get(key)
            if value and value != "1":
                import json
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get dedup metadata: {e}")
            return None

    async def clear_entry(self, key: str):
        """Clear a deduplication entry (for testing/debugging)"""
        try:
            await self.cache.delete(key)
            logger.info(f"Cleared dedup entry: {key}")
        except Exception as e:
            logger.error(f"Failed to clear dedup entry: {e}")


class FuzzyDeduplicator(EventDeduplicator):
    """
    Fuzzy deduplication for events that may have slight variations.
    Uses content hashing to detect similar events.
    """

    def __init__(self, similarity_threshold: float = 0.95):
        super().__init__()
        self.similarity_threshold = similarity_threshold

    def generate_content_hash(self, payload: Dict[str, Any]) -> str:
        """Generate hash of normalized content"""
        import json
        
        # Normalize payload for hashing
        normalized = self._normalize_payload(payload)
        payload_str = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize payload for comparison"""
        normalized = {}
        
        # Keep only key fields
        data = payload.get("data", payload)
        
        key_fields = [
            "id", "contact_id", "email", "phone", 
            "opportunity_id", "pipeline_id", "stage_id"
        ]
        
        for field in key_fields:
            if field in data:
                normalized[field] = data[field]
        
        # Normalize text content
        for text_field in ["message", "body", "content", "note"]:
            if text_field in data:
                # Lowercase and trim
                text = str(data[text_field]).lower().strip()
                # Remove extra whitespace
                import re
                text = re.sub(r'\s+', ' ', text)
                normalized[text_field] = text
        
        return normalized


# Singleton instance
_deduplicator: Optional[EventDeduplicator] = None


def get_deduplicator() -> EventDeduplicator:
    """Get or create deduplicator singleton"""
    global _deduplicator
    if _deduplicator is None:
        _deduplicator = EventDeduplicator()
    return _deduplicator
