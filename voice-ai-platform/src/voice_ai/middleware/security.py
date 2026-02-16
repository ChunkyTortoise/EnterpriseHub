"""API key authentication middleware.

Validates X-API-Key header against comma-separated keys in API_KEYS env var.
Excludes /health, /ready, /docs, /openapi.json, and /redoc from authentication.
"""

from __future__ import annotations

import logging
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Paths excluded from API key authentication
EXCLUDED_PATHS = frozenset({
    "/health",
    "/ready",
    "/docs",
    "/openapi.json",
    "/redoc",
})


def _get_valid_keys() -> set[str]:
    """Parse valid API keys from the API_KEYS environment variable."""
    raw = os.environ.get("API_KEYS", "")
    if not raw:
        return set()
    return {k.strip() for k in raw.split(",") if k.strip()}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware that validates X-API-Key header on every request.

    Keys are loaded from the API_KEYS env var (comma-separated).
    If API_KEYS is empty/unset, authentication is disabled (dev mode).
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth for excluded paths
        if path in EXCLUDED_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        valid_keys = _get_valid_keys()

        # If no keys configured, skip auth (dev mode)
        if not valid_keys:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning("Missing API key for %s %s", request.method, path)
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorized",
                    "message": "Invalid or missing API key",
                    "code": "AUTH_001",
                },
            )

        if api_key not in valid_keys:
            logger.warning("Invalid API key for %s %s", request.method, path)
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorized",
                    "message": "Invalid or missing API key",
                    "code": "AUTH_001",
                },
            )

        return await call_next(request)
