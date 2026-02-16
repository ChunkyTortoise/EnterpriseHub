"""Tenant router — map request to tenant schema via API key."""

from __future__ import annotations

import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class TenantRouter:
    """Resolve API key to tenant_id and schema name."""

    def __init__(self, redis=None, db_session_factory=None):
        self.redis = redis
        self.db = db_session_factory

    async def resolve_tenant(self, api_key: str) -> dict | None:
        """Resolve an API key to tenant information.

        Returns:
            Dict with tenant_id, schema_name, tier, scopes or None.
        """
        hashed = hashlib.sha256(api_key.encode()).hexdigest()

        # Check cache
        if self.redis:
            cached = await self.redis.get(f"tenant_route:{hashed}")
            if cached:
                return json.loads(cached)

        # Query database
        if self.db:
            async with self.db() as session:
                result = await session.execute(
                    """
                    SELECT k.tenant_id, k.scopes, t.slug, t.tier, t.status
                    FROM shared.api_keys k
                    JOIN shared.tenants t ON k.tenant_id = t.id
                    WHERE k.hashed_key = :hashed AND k.is_active = true
                    """,
                    {"hashed": hashed},
                )
                row = result.fetchone()
                if not row:
                    return None

                if row.status == "suspended":
                    return None

                tenant_info = {
                    "tenant_id": str(row.tenant_id),
                    "schema_name": f"tenant_{row.slug}",
                    "tier": row.tier,
                    "scopes": row.scopes,
                }

                # Cache for 5 minutes
                if self.redis:
                    await self.redis.setex(
                        f"tenant_route:{hashed}", 300, json.dumps(tenant_info)
                    )

                return tenant_info

        return None

    async def invalidate_cache(self, api_key: str) -> None:
        """Remove cached tenant route for an API key."""
        if self.redis:
            hashed = hashlib.sha256(api_key.encode()).hexdigest()
            await self.redis.delete(f"tenant_route:{hashed}")
