"""Per-tenant usage tracking: query counts and token consumption."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class UsageRecord:
    tenant_id: str
    query_count: int = 0
    total_tokens: int = 0
    last_query_at: Optional[datetime] = None


class UsageMetering:
    """
    In-memory usage tracker -- records query count and token usage per tenant.
    Thread-safe.
    """

    def __init__(self) -> None:
        self._records: dict[str, UsageRecord] = {}
        self._lock = threading.Lock()

    def record_query(self, tenant_id: str, token_count: int = 0) -> None:
        with self._lock:
            rec = self._records.setdefault(tenant_id, UsageRecord(tenant_id=tenant_id))
            rec.query_count += 1
            rec.total_tokens += max(0, token_count)
            rec.last_query_at = datetime.now(tz=timezone.utc)

    def get_usage(self, tenant_id: str) -> UsageRecord:
        with self._lock:
            return self._records.get(tenant_id, UsageRecord(tenant_id=tenant_id))

    def get_all_usage(self) -> list[UsageRecord]:
        with self._lock:
            return list(self._records.values())

    def reset_usage(self, tenant_id: str) -> None:
        with self._lock:
            self._records[tenant_id] = UsageRecord(tenant_id=tenant_id)
