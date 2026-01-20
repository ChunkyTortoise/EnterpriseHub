"""
Redis-backed Conversation Context Manager.

Replaces in-memory context storage with persistent Redis storage
for horizontal scaling and data persistence.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import redis.asyncio as redis
from contextlib import asynccontextmanager
import os

logger = logging.getLogger(__name__)

class RedisConversationContext:
    """Redis-backed conversation context storage with TTL and compression."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 7 * 24 * 3600,  # 7 days default TTL
        max_history_length: int = 50,
        tenant_id: Optional[str] = None
    ):
        """
        Initialize Redis conversation context manager.

        Args:
            redis_url: Redis connection URL (defaults to env var)
            default_ttl: Default TTL for conversation contexts in seconds
            max_history_length: Maximum conversation history length
            tenant_id: Tenant ID for multi-tenant isolation
        """
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL", "redis://localhost:6379/1"
        )
        self.default_ttl = default_ttl
        self.max_history_length = max_history_length
        self.tenant_id = tenant_id or "default"
        self.redis_pool = None
        logger.info(f"Initialized RedisConversationContext for tenant {self.tenant_id}")

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection with connection pooling."""
        if self.redis_pool is None:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                decode_responses=True
            )
        return redis.Redis(connection_pool=self.redis_pool)

    def _get_context_key(self, customer_id: str, department_id: Optional[str] = None) -> str:
        """Generate Redis key for conversation context with tenant isolation."""
        base_key = f"conversation_context:{self.tenant_id}"
        context_key = f"{department_id}:{customer_id}" if department_id else customer_id
        return f"{base_key}:{context_key}"

    def _get_analytics_key(self) -> str:
        """Generate Redis key for conversation analytics."""
        return f"conversation_analytics:{self.tenant_id}"

    async def get_context(
        self,
        customer_id: str,
        department_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve conversation context from Redis.

        Args:
            customer_id: Unique customer identifier
            department_id: Optional department ID for context isolation

        Returns:
            Conversation context dict with history and extracted data
        """
        try:
            redis_client = await self._get_redis()
            context_key = self._get_context_key(customer_id, department_id)

            # Try to get existing context
            context_json = await redis_client.get(context_key)

            if context_json:
                context = json.loads(context_json)

                # Update last accessed timestamp
                context["last_accessed_at"] = datetime.utcnow().isoformat()

                # Check for session gap (Smart Resume)
                last_interaction = context.get("last_interaction_at")
                if last_interaction:
                    last_dt = datetime.fromisoformat(last_interaction)
                    hours_since = (datetime.utcnow() - last_dt).total_seconds() / 3600

                    if hours_since > 24:  # 24 hour window for returning customers
                        context["is_returning_customer"] = True
                        context["hours_since_last_interaction"] = hours_since
                        logger.info(f"Returning customer detected for {customer_id} ({hours_since:.1f} hours since last interaction)")

                # Refresh TTL
                await redis_client.expire(context_key, self.default_ttl)

                return context
            else:
                # Create new context
                new_context = {
                    "customer_id": customer_id,
                    "department_id": department_id,
                    "tenant_id": self.tenant_id,
                    "conversation_history": [],
                    "extracted_preferences": {},
                    "created_at": datetime.utcnow().isoformat(),
                    "last_interaction_at": None,
                    "last_accessed_at": datetime.utcnow().isoformat(),
                    "engagement_score": 0,
                    "session_count": 1,
                    "total_messages": 0
                }

                # Store in Redis with TTL
                await redis_client.setex(
                    context_key,
                    self.default_ttl,
                    json.dumps(new_context)
                )

                # Update analytics
                await self._update_analytics("context_created")

                logger.info(f"Created new context for customer {customer_id}")
                return new_context

        except Exception as e:
            logger.error(f"Failed to retrieve context for {customer_id}: {e}")
            # Return minimal fallback context
            return {
                "customer_id": customer_id,
                "department_id": department_id,
                "conversation_history": [],
                "extracted_preferences": {},
                "created_at": datetime.utcnow().isoformat(),
                "last_interaction_at": None,
                "engagement_score": 0,
                "error": "redis_unavailable"
            }

    async def update_context(
        self,
        customer_id: str,
        user_message: str,
        ai_response: str,
        extracted_data: Optional[Dict[str, Any]] = None,
        department_id: Optional[str] = None,
        engagement_score: Optional[int] = None
    ) -> None:
        """
        Update conversation context in Redis with new messages and data.

        Args:
            customer_id: Unique customer identifier
            user_message: User's message
            ai_response: AI's response
            extracted_data: Newly extracted data from conversation
            department_id: Optional department ID for context isolation
            engagement_score: Optional engagement score
        """
        try:
            redis_client = await self._get_redis()
            context = await self.get_context(customer_id, department_id)

            # Add messages to history with message IDs for deduplication
            message_id = f"{customer_id}_{int(datetime.utcnow().timestamp() * 1000)}"

            new_messages = [
                {
                    "id": f"{message_id}_user",
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "id": f"{message_id}_assistant",
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]

            # Append new messages and trim if necessary
            context["conversation_history"].extend(new_messages)
            if len(context["conversation_history"]) > self.max_history_length:
                # Keep most recent messages
                context["conversation_history"] = context["conversation_history"][-self.max_history_length:]

            # Update interaction tracking
            context["last_interaction_at"] = datetime.utcnow().isoformat()
            context["last_accessed_at"] = datetime.utcnow().isoformat()
            context["total_messages"] = context.get("total_messages", 0) + 2

            # Merge extracted data (new data overrides old)
            if extracted_data:
                context["extracted_preferences"].update(extracted_data)

            # Update engagement score
            if engagement_score is not None:
                context["engagement_score"] = engagement_score

            # Remove returning customer flag after acknowledged
            if context.get("is_returning_customer"):
                context["is_returning_customer"] = False

            # Store updated context in Redis
            context_key = self._get_context_key(customer_id, department_id)
            await redis_client.setex(
                context_key,
                self.default_ttl,
                json.dumps(context)
            )

            # Update analytics
            await self._update_analytics("message_exchanged", {
                "customer_id": customer_id,
                "department_id": department_id,
                "message_count": 2,
                "has_extracted_data": bool(extracted_data)
            })

            logger.info(
                f"Updated context for customer {customer_id}",
                extra={
                    "customer_id": customer_id,
                    "history_length": len(context["conversation_history"]),
                    "total_messages": context["total_messages"],
                    "preferences": context["extracted_preferences"]
                }
            )

        except Exception as e:
            logger.error(f"Failed to update context for {customer_id}: {e}")

    async def _update_analytics(
        self,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update conversation analytics in Redis."""
        try:
            redis_client = await self._get_redis()
            analytics_key = self._get_analytics_key()

            # Get current analytics
            analytics_json = await redis_client.get(analytics_key)
            analytics = json.loads(analytics_json) if analytics_json else {
                "total_contexts": 0,
                "total_messages": 0,
                "active_conversations": 0,
                "last_updated": datetime.utcnow().isoformat()
            }

            # Update based on event type
            if event_type == "context_created":
                analytics["total_contexts"] += 1
                analytics["active_conversations"] += 1
            elif event_type == "message_exchanged":
                analytics["total_messages"] += event_data.get("message_count", 0)

            analytics["last_updated"] = datetime.utcnow().isoformat()

            # Store updated analytics
            await redis_client.setex(analytics_key, 24 * 3600, json.dumps(analytics))

        except Exception as e:
            logger.warning(f"Failed to update analytics: {e}")

    async def get_customer_contexts(
        self,
        customer_ids: List[str],
        department_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Bulk retrieve multiple customer contexts efficiently.

        Args:
            customer_ids: List of customer IDs
            department_id: Optional department filter

        Returns:
            Dict mapping customer_id to context
        """
        try:
            redis_client = await self._get_redis()

            # Build all keys
            keys = [self._get_context_key(cid, department_id) for cid in customer_ids]

            # Bulk get
            contexts_json = await redis_client.mget(keys)

            result = {}
            for i, context_json in enumerate(contexts_json):
                customer_id = customer_ids[i]
                if context_json:
                    result[customer_id] = json.loads(context_json)

            return result

        except Exception as e:
            logger.error(f"Failed to bulk retrieve contexts: {e}")
            return {}

    async def delete_context(
        self,
        customer_id: str,
        department_id: Optional[str] = None
    ) -> bool:
        """
        Delete conversation context from Redis.

        Args:
            customer_id: Unique customer identifier
            department_id: Optional department ID

        Returns:
            True if context was deleted, False otherwise
        """
        try:
            redis_client = await self._get_redis()
            context_key = self._get_context_key(customer_id, department_id)

            deleted = await redis_client.delete(context_key)

            if deleted:
                await self._update_analytics("context_deleted")
                logger.info(f"Deleted context for customer {customer_id}")

            return bool(deleted)

        except Exception as e:
            logger.error(f"Failed to delete context for {customer_id}: {e}")
            return False

    async def cleanup_expired_contexts(self, max_age_days: int = 30) -> int:
        """
        Cleanup old conversation contexts beyond max age.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of contexts cleaned up
        """
        try:
            redis_client = await self._get_redis()
            pattern = f"conversation_context:{self.tenant_id}:*"

            cursor = 0
            cleaned_count = 0
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

            while True:
                cursor, keys = await redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )

                for key in keys:
                    context_json = await redis_client.get(key)
                    if context_json:
                        context = json.loads(context_json)
                        created_at = datetime.fromisoformat(context.get("created_at", ""))

                        if created_at < cutoff_date:
                            await redis_client.delete(key)
                            cleaned_count += 1

                if cursor == 0:
                    break

            logger.info(f"Cleaned up {cleaned_count} expired contexts")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired contexts: {e}")
            return 0

    async def get_analytics(self) -> Dict[str, Any]:
        """Get conversation analytics for the tenant."""
        try:
            redis_client = await self._get_redis()
            analytics_key = self._get_analytics_key()

            analytics_json = await redis_client.get(analytics_key)
            if analytics_json:
                return json.loads(analytics_json)
            else:
                return {
                    "total_contexts": 0,
                    "total_messages": 0,
                    "active_conversations": 0,
                    "last_updated": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Check Redis connection health."""
        try:
            redis_client = await self._get_redis()

            # Test basic operations
            test_key = f"health_check:{self.tenant_id}"
            await redis_client.setex(test_key, 10, "test")
            result = await redis_client.get(test_key)
            await redis_client.delete(test_key)

            if result == "test":
                return {
                    "status": "healthy",
                    "redis_connection": "ok",
                    "tenant_id": self.tenant_id
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Redis test failed"
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def close(self) -> None:
        """Close Redis connection pool."""
        if self.redis_pool:
            await self.redis_pool.disconnect()
            logger.info("Redis connection pool closed")

    @asynccontextmanager
    async def context_lock(self, customer_id: str, department_id: Optional[str] = None):
        """
        Context manager for distributed locking to prevent race conditions.

        Useful for concurrent updates to the same conversation context.
        """
        redis_client = await self._get_redis()
        lock_key = f"lock:{self._get_context_key(customer_id, department_id)}"
        lock_timeout = 5  # 5 second timeout

        # Try to acquire lock
        acquired = await redis_client.set(lock_key, "locked", ex=lock_timeout, nx=True)

        if not acquired:
            raise RuntimeError(f"Could not acquire lock for context {customer_id}")

        try:
            yield
        finally:
            # Release lock
            await redis_client.delete(lock_key)