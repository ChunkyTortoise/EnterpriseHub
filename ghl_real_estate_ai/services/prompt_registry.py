"""Prompt version registry with DB-backed storage.

Tracks prompt content, model, and version history. Supports rollback
and usage logging for prompt performance analysis.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass
class PromptVersion:
    id: str
    name: str
    version: int
    content: str
    model: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class PromptRegistry:
    """DB-backed prompt version registry."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_current(self, name: str) -> PromptVersion | None:
        """Get latest version of a named prompt."""
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    "SELECT id, name, version, content, model, created_at, metadata "
                    "FROM prompt_versions "
                    "WHERE name = :name "
                    "ORDER BY version DESC LIMIT 1"
                ),
                {"name": name},
            )
            row = result.mappings().first()
            if row is None:
                return None
            return self._row_to_version(row)

    async def register(
        self,
        name: str,
        content: str,
        model: str,
        metadata: dict[str, Any] | None = None,
    ) -> PromptVersion:
        """Register a new version (auto-increments version number)."""
        async with self._session_factory() as session:
            # Get current max version
            result = await session.execute(
                text("SELECT COALESCE(MAX(version), 0) AS max_v FROM prompt_versions WHERE name = :name"),
                {"name": name},
            )
            max_version = result.scalar_one()
            new_version = max_version + 1
            new_id = str(uuid.uuid4())

            await session.execute(
                text(
                    "INSERT INTO prompt_versions (id, name, version, content, model, metadata) "
                    "VALUES (:id, :name, :version, :content, :model, :metadata)"
                ),
                {
                    "id": new_id,
                    "name": name,
                    "version": new_version,
                    "content": content,
                    "model": model,
                    "metadata": _json_dumps(metadata or {}),
                },
            )
            await session.commit()

            return PromptVersion(
                id=new_id,
                name=name,
                version=new_version,
                content=content,
                model=model,
                created_at=datetime.now(UTC),
                metadata=metadata or {},
            )

    async def rollback(self, name: str, to_version: int) -> PromptVersion:
        """Create a new version with the content of a previous version."""
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    "SELECT id, name, version, content, model, created_at, metadata "
                    "FROM prompt_versions "
                    "WHERE name = :name AND version = :version"
                ),
                {"name": name, "version": to_version},
            )
            row = result.mappings().first()
            if row is None:
                raise ValueError(f"Prompt '{name}' version {to_version} not found")

        # Deserialize metadata (TEXT in SQLite, JSONB in Postgres)
        raw_meta = row["metadata"]
        if isinstance(raw_meta, str):
            import json

            raw_meta = json.loads(raw_meta) if raw_meta else {}

        # Register a new version with the old content
        return await self.register(
            name=name,
            content=row["content"],
            model=row["model"],
            metadata={**(raw_meta or {}), "rolled_back_from": to_version},
        )

    async def log_usage(
        self,
        version_id: str,
        request_id: str,
        response_quality: float | None = None,
    ) -> None:
        """Log that a prompt version was used in a request."""
        async with self._session_factory() as session:
            await session.execute(
                text(
                    "INSERT INTO prompt_usage_log (id, version_id, request_id, response_quality) "
                    "VALUES (:id, :version_id, :request_id, :response_quality)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "version_id": version_id,
                    "request_id": request_id,
                    "response_quality": response_quality,
                },
            )
            await session.commit()

    @staticmethod
    def _row_to_version(row) -> PromptVersion:
        raw_meta = row["metadata"]
        if isinstance(raw_meta, str):
            import json

            raw_meta = json.loads(raw_meta) if raw_meta else {}
        return PromptVersion(
            id=str(row["id"]),
            name=row["name"],
            version=row["version"],
            content=row["content"],
            model=row["model"],
            created_at=row["created_at"],
            metadata=raw_meta or {},
        )


def _json_dumps(obj: dict) -> str:
    import json

    return json.dumps(obj)
