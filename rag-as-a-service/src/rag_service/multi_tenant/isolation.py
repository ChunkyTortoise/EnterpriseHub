"""Tenant isolation middleware — extract tenant from API key and set schema."""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from rag_service.multi_tenant.tenant_router import TenantRouter

logger = logging.getLogger(__name__)

# Paths that don't require tenant context
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class TenantMiddleware(BaseHTTPMiddleware):
    """Extract tenant from API key header and inject into request state."""

    def __init__(self, app, tenant_router: TenantRouter):
        super().__init__(app)
        self.tenant_router = tenant_router

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request, resolve tenant, set schema in request state."""
        # Skip tenant resolution for public paths
        path = request.url.path
        if path in PUBLIC_PATHS or path.startswith("/api/v1/auth"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing X-API-Key header")

        tenant_info = await self.tenant_router.resolve_tenant(api_key)
        if not tenant_info:
            raise HTTPException(status_code=401, detail="Invalid API key or suspended tenant")

        # Inject tenant context into request state
        request.state.tenant_id = tenant_info["tenant_id"]
        request.state.tenant_schema = tenant_info["schema_name"]
        request.state.tenant_tier = tenant_info["tier"]
        request.state.tenant_scopes = tenant_info["scopes"]

        response = await call_next(request)
        return response
