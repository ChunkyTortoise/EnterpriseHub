"""Standardized error response handlers.

Provides a unified error schema: {error, message, code, request_id}.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def _error_response(status_code: int, error: str, message: str) -> JSONResponse:
    """Build a standardized error response with a unique request_id."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "message": message,
            "code": status_code,
            "request_id": str(uuid.uuid4()),
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions with standardized response."""
    error_map = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "validation_error",
        429: "rate_limit_exceeded",
    }
    error_key = error_map.get(exc.status_code, "error")
    message = str(exc.detail) if exc.detail else f"HTTP {exc.status_code}"
    return _error_response(exc.status_code, error_key, message)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with standardized response."""
    errors = exc.errors()
    message = "; ".join(f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in errors)
    return _error_response(422, "validation_error", message)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions with standardized response."""
    logger.exception("Unhandled exception: %s", exc)
    return _error_response(500, "internal_server_error", "An unexpected error occurred")


def register_error_handlers(app: FastAPI) -> None:
    """Register all standardized error handlers on the app."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
