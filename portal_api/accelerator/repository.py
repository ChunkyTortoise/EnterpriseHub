from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .schemas import AuditEvent, EngagementStatus, ProofPack, VerticalProfile


class AcceleratorRepository:
    """In-memory repository with lock-based concurrency safety for demo API usage."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._engagements: dict[str, dict[str, Any]] = {}
        self._reports: dict[str, dict[str, Any]] = {}
        self._audit_events: list[AuditEvent] = []

    def create_or_update_engagement(
        self,
        *,
        engagement_id: str,
        vertical_profile: VerticalProfile,
        client_name: str,
        status: EngagementStatus,
    ) -> None:
        with self._lock:
            now = datetime.now(UTC).isoformat()
            existing = self._engagements.get(engagement_id, {})
            self._engagements[engagement_id] = {
                "engagement_id": engagement_id,
                "vertical_profile": vertical_profile,
                "client_name": client_name or existing.get("client_name", "unknown"),
                "status": status,
                "created_at": existing.get("created_at", now),
                "updated_at": now,
            }

    def get_engagement(self, engagement_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._engagements.get(engagement_id)

    def list_audit_events(self, engagement_id: str) -> list[AuditEvent]:
        with self._lock:
            return [event for event in self._audit_events if event.engagement_id == engagement_id]

    def append_audit_event(self, engagement_id: str, action: str, details: dict[str, Any] | None = None) -> AuditEvent:
        with self._lock:
            event = AuditEvent(id=str(uuid4()), engagement_id=engagement_id, action=action, details=details or {})
            self._audit_events.append(event)
            return event

    def get_report(self, engagement_id: str) -> ProofPack | None:
        with self._lock:
            record = self._reports.get(engagement_id)
            if not record:
                return None
            return record["proof_pack"]

    def save_report_idempotent(
        self, engagement_id: str, payload: dict[str, Any], proof_pack: ProofPack
    ) -> tuple[ProofPack, bool]:
        with self._lock:
            fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
            existing = self._reports.get(engagement_id)
            if existing and existing["fingerprint"] == fingerprint:
                return existing["proof_pack"], True
            self._reports[engagement_id] = {"fingerprint": fingerprint, "proof_pack": proof_pack}
            return proof_pack, False
