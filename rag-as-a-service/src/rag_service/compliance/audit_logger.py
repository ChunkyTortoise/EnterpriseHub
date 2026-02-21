"""Audit logger — structured audit trail for all operations."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Single audit log entry."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    user_id: str | None = None
    action: str = ""  # document.upload, document.delete, query.execute, auth.login, etc.
    resource_type: str = ""  # document, collection, query, api_key
    resource_id: str | None = None
    metadata: dict = field(default_factory=dict)
    ip_address: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditLogger:
    """Record audit trail for all tenant operations."""

    def __init__(self, db_session=None):
        self.db = db_session
        self._buffer: list[AuditEntry] = []

    async def log(
        self,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        user_id: str | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditEntry:
        """Record an audit event."""
        entry = AuditEntry(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {},
            ip_address=ip_address,
        )

        # Persist to database if available
        if self.db:
            await self._persist(entry)
        else:
            self._buffer.append(entry)

        logger.info(
            "AUDIT: tenant=%s action=%s resource=%s/%s",
            tenant_id,
            action,
            resource_type,
            resource_id,
        )

        return entry

    async def _persist(self, entry: AuditEntry) -> None:
        """Write audit entry to database."""
        if self.db:
            await self.db.execute(
                """
                INSERT INTO shared.audit_logs
                    (id, tenant_id, user_id, action, resource_type, resource_id,
                     metadata_json, ip_address, created_at)
                VALUES (:id, :tenant_id, :user_id, :action, :resource_type,
                        :resource_id, :metadata, :ip_address, :timestamp)
                """,
                {
                    "id": entry.id,
                    "tenant_id": entry.tenant_id,
                    "user_id": entry.user_id,
                    "action": entry.action,
                    "resource_type": entry.resource_type,
                    "resource_id": entry.resource_id,
                    "metadata": entry.metadata,
                    "ip_address": entry.ip_address,
                    "timestamp": entry.timestamp,
                },
            )

    async def query_logs(
        self,
        tenant_id: str,
        action: str | None = None,
        resource_type: str | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Query audit logs for a tenant."""
        # Return from buffer if no DB
        if not self.db:
            results = [e for e in self._buffer if e.tenant_id == tenant_id]
            if action:
                results = [e for e in results if e.action == action]
            if resource_type:
                results = [e for e in results if e.resource_type == resource_type]
            return results[:limit]

        return []

    def get_buffered_entries(self) -> list[AuditEntry]:
        """Get all buffered entries (for testing)."""
        return list(self._buffer)

    def clear_buffer(self) -> None:
        """Clear the in-memory buffer."""
        self._buffer.clear()
