#!/usr/bin/env python3
"""
File-backed webhook idempotency storage.

Stores processed webhook event IDs with TTL to suppress duplicate processing.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FileBackedIdempotencyStore:
    """Simple file-backed idempotency store with TTL and atomic writes."""

    def __init__(self, storage_path: str, ttl_seconds: int = 86400):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = max(1, int(ttl_seconds))
        self._lock = Lock()

    def check_and_mark(self, event_id: str, seen_at: Optional[datetime] = None) -> bool:
        """
        Return True when an event is a duplicate, otherwise mark it and return False.
        """

        if not event_id:
            raise ValueError("event_id is required")

        now = seen_at or datetime.now(timezone.utc)

        with self._lock:
            records = self._load_records()
            self._purge_expired(records, now)

            if event_id in records:
                return True

            records[event_id] = {
                "event_id": event_id,
                "seen_at": now.isoformat(),
                "expires_at": (now + timedelta(seconds=self.ttl_seconds)).isoformat(),
                "status": "processed",
            }
            self._atomic_write(records)
            return False

    def _load_records(self) -> Dict[str, Dict[str, str]]:
        if not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
                if isinstance(payload, dict):
                    return payload
        except Exception as exc:
            logger.warning("idempotency_store_load_failed path=%s error=%s", self.storage_path, exc)
        return {}

    def _purge_expired(self, records: Dict[str, Dict[str, str]], now: datetime) -> None:
        expired_ids = []
        for event_id, record in records.items():
            expires_at = record.get("expires_at")
            if not expires_at:
                expired_ids.append(event_id)
                continue

            try:
                expires_dt = datetime.fromisoformat(expires_at)
            except ValueError:
                expired_ids.append(event_id)
                continue

            if expires_dt <= now:
                expired_ids.append(event_id)

        if expired_ids:
            for event_id in expired_ids:
                records.pop(event_id, None)
            self._atomic_write(records)

    def _atomic_write(self, records: Dict[str, Dict[str, str]]) -> None:
        temp_path = self.storage_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2, sort_keys=True)
        temp_path.replace(self.storage_path)
