"""API versioning utilities.

Provides helpers to mount legacy and versioned routes while emitting
standard deprecation headers on legacy paths.
"""
from __future__ import annotations

from fastapi import Depends, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Iterable, Optional

DEFAULT_SUNSET_DATE = "2026-12-31"


def add_deprecation_headers(response: Response) -> None:
    """Attach deprecation headers to legacy responses."""
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = DEFAULT_SUNSET_DATE
    response.headers["Link"] = '</api/v1>; rel="alternate"'


def _normalize_deps(deps: Optional[Iterable]) -> list:
    if not deps:
        return []
    return list(deps)


def include_versioned_router(
    app,
    router,
    *,
    legacy_prefix: str,
    version_prefix: str,
    dependencies: Optional[Iterable] = None,
    legacy_dependencies: Optional[Iterable] = None,
    version_dependencies: Optional[Iterable] = None,
    **kwargs,
) -> None:
    """Include a router under both legacy and versioned prefixes."""
    base_deps = _normalize_deps(dependencies)
    version_deps = _normalize_deps(version_dependencies) or base_deps
    legacy_deps = _normalize_deps(legacy_dependencies) or base_deps
    legacy_deps = legacy_deps + [Depends(add_deprecation_headers)]

    app.include_router(router, prefix=version_prefix, dependencies=version_deps, **kwargs)
    app.include_router(router, prefix=legacy_prefix, dependencies=legacy_deps, **kwargs)


class ApiVersionRewriteMiddleware:
    """Rewrite /api/v1 paths to legacy /api paths for routing compatibility."""

    def __init__(self, app, version_prefix: str = "/api/v1", legacy_prefix: str = "/api") -> None:
        self.app = app
        self.version_prefix = version_prefix.rstrip("/")
        self.legacy_prefix = legacy_prefix.rstrip("/")

    async def __call__(self, scope, receive, send):
        if scope["type"] in {"http", "websocket"}:
            path = scope.get("path", "")
            if path == self.version_prefix or path.startswith(self.version_prefix + "/"):
                new_path = self.legacy_prefix + path[len(self.version_prefix):]
                new_scope = dict(scope)
                new_scope["path"] = new_path
                new_scope["raw_path"] = new_path.encode()
                return await self.app(new_scope, receive, send)
        return await self.app(scope, receive, send)


class LegacyDeprecationMiddleware(BaseHTTPMiddleware):
    """Attach deprecation headers to legacy /api responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/api") and not path.startswith("/api/v1"):
            add_deprecation_headers(response)
        return response
