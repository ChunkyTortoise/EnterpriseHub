"""Usage tracker — Redis-backed per-tenant query and storage counting."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# Tier limits
TIER_LIMITS = {
    "starter": {"queries_per_month": 5_000, "storage_mb": 1_000, "documents": 500},
    "pro": {"queries_per_month": 50_000, "storage_mb": 10_000, "documents": 5_000},
    "business": {"queries_per_month": 500_000, "storage_mb": 100_000, "documents": 999_999},
}


@dataclass
class UsageStats:
    """Current usage statistics for a tenant."""
    tenant_id: str
    queries_this_month: int = 0
    storage_bytes: int = 0
    documents: int = 0
    queries_limit: int = 0
    storage_limit_mb: int = 0
    documents_limit: int = 0
    overage_queries: int = 0


class UsageTracker:
    """Track tenant usage via Redis INCR with per-period keys."""

    def __init__(self, redis=None):
        self.redis = redis
        # In-memory fallback for testing
        self._counters: dict[str, int] = {}

    def _period_key(self) -> str:
        """Get the current billing period key (YYYY-MM)."""
        return datetime.now(timezone.utc).strftime("%Y-%m")

    async def increment_queries(self, tenant_id: str, count: int = 1) -> int:
        """Increment query count for the current period."""
        period = self._period_key()
        key = f"usage:{tenant_id}:queries:{period}"

        if self.redis:
            new_val = await self.redis.incrby(key, count)
            # Expire after 90 days (retain for billing reconciliation)
            await self.redis.expire(key, 90 * 86400)
            return new_val

        self._counters[key] = self._counters.get(key, 0) + count
        return self._counters[key]

    async def increment_storage(self, tenant_id: str, bytes_added: int) -> int:
        """Track storage usage in bytes."""
        key = f"usage:{tenant_id}:storage_bytes"

        if self.redis:
            return await self.redis.incrby(key, bytes_added)

        self._counters[key] = self._counters.get(key, 0) + bytes_added
        return self._counters[key]

    async def decrement_storage(self, tenant_id: str, bytes_removed: int) -> int:
        """Reduce storage count when documents are deleted."""
        key = f"usage:{tenant_id}:storage_bytes"

        if self.redis:
            return await self.redis.decrby(key, bytes_removed)

        self._counters[key] = max(0, self._counters.get(key, 0) - bytes_removed)
        return self._counters[key]

    async def increment_documents(self, tenant_id: str, count: int = 1) -> int:
        """Track document count."""
        key = f"usage:{tenant_id}:documents"

        if self.redis:
            return await self.redis.incrby(key, count)

        self._counters[key] = self._counters.get(key, 0) + count
        return self._counters[key]

    async def decrement_documents(self, tenant_id: str, count: int = 1) -> int:
        """Reduce document count."""
        key = f"usage:{tenant_id}:documents"

        if self.redis:
            return await self.redis.decrby(key, count)

        self._counters[key] = max(0, self._counters.get(key, 0) - count)
        return self._counters[key]

    async def get_usage(self, tenant_id: str, tier: str = "starter") -> UsageStats:
        """Get current usage stats for a tenant."""
        period = self._period_key()
        queries_key = f"usage:{tenant_id}:queries:{period}"
        storage_key = f"usage:{tenant_id}:storage_bytes"
        docs_key = f"usage:{tenant_id}:documents"

        if self.redis:
            queries = int(await self.redis.get(queries_key) or 0)
            storage = int(await self.redis.get(storage_key) or 0)
            docs = int(await self.redis.get(docs_key) or 0)
        else:
            queries = self._counters.get(queries_key, 0)
            storage = self._counters.get(storage_key, 0)
            docs = self._counters.get(docs_key, 0)

        limits = TIER_LIMITS.get(tier, TIER_LIMITS["starter"])
        overage = max(0, queries - limits["queries_per_month"])

        return UsageStats(
            tenant_id=tenant_id,
            queries_this_month=queries,
            storage_bytes=storage,
            documents=docs,
            queries_limit=limits["queries_per_month"],
            storage_limit_mb=limits["storage_mb"],
            documents_limit=limits["documents"],
            overage_queries=overage,
        )

    async def check_quota(self, tenant_id: str, tier: str, resource: str) -> bool:
        """Check if a tenant is within their quota for a resource."""
        usage = await self.get_usage(tenant_id, tier)
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["starter"])

        if resource == "queries":
            return usage.queries_this_month < limits["queries_per_month"]
        elif resource == "storage":
            return usage.storage_bytes < limits["storage_mb"] * 1024 * 1024
        elif resource == "documents":
            return usage.documents < limits["documents"]

        return True
