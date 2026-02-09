"""
Bulletproof Error Handling Middleware for Jorge Platform
Enhanced with comprehensive error classification, circuit breakers, and resilience patterns.
"""

import asyncio
import time
import traceback
import uuid
from collections import defaultdict
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class CircuitBreaker:
    """Simple circuit breaker implementation for error handling middleware"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_proceed(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class BulletproofErrorHandler(BaseHTTPMiddleware):
    """
    Bulletproof error handling middleware with:
    - Comprehensive error classification
    - Circuit breaker patterns
    - Rate limiting awareness
    - Detailed correlation tracking
    - Intelligent fallback responses
    """

    def __init__(self, app):
        super().__init__(app)
        self.circuit_breakers: Dict[str, CircuitBreaker] = defaultdict(
            lambda: CircuitBreaker(failure_threshold=5, timeout=60)
        )
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.last_error_reset = time.time()

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        correlation_id = self._get_correlation_id(request)
        endpoint_key = f"{request.method}:{request.url.path}"

        # Check circuit breaker
        circuit_breaker = self.circuit_breakers[endpoint_key]
        if not circuit_breaker.can_proceed():
            logger.warning(
                f"Circuit breaker OPEN for {endpoint_key}",
                extra={"correlation_id": correlation_id, "endpoint": endpoint_key, "circuit_state": "OPEN"},
            )
            return await self._circuit_breaker_response(request, correlation_id)

        try:
            # Add correlation ID to request state for downstream usage
            request.state.correlation_id = correlation_id

            response = await call_next(request)
            process_time = time.time() - start_time

            # Record success for circuit breaker
            circuit_breaker.record_success()

            # Log performance metrics
            await self._log_performance_metrics(request, response, process_time, correlation_id)

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # Record failure for circuit breaker
            circuit_breaker.record_failure()

            # Classify and handle the error
            error_info = await self._classify_error(e, request, process_time, correlation_id)

            # Enhanced error logging
            await self._log_error(error_info, request, correlation_id)

            # Return appropriate error response
            return await self._create_error_response(error_info, request, correlation_id)

    def _get_correlation_id(self, request: Request) -> str:
        """Get or create correlation ID for request tracking"""
        return (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or f"jorge_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
        )

    async def _classify_error(
        self, error: Exception, request: Request, process_time: float, correlation_id: str
    ) -> Dict[str, Any]:
        """Classify error for appropriate handling"""

        error_info = {
            "id": f"err_{correlation_id}",
            "correlation_id": correlation_id,
            "timestamp": time.time(),
            "process_time": process_time,
            "endpoint": f"{request.method} {request.url.path}",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
        }

        # Classify by error type
        if isinstance(error, HTTPException):
            error_info.update(
                {
                    "category": "http",
                    "status_code": error.status_code,
                    "severity": "medium" if error.status_code < 500 else "high",
                    "user_message": error.detail,
                    "retryable": error.status_code in [408, 429, 502, 503, 504],
                }
            )
        elif isinstance(error, asyncio.TimeoutError):
            error_info.update(
                {
                    "category": "timeout",
                    "status_code": 408,
                    "severity": "medium",
                    "user_message": "Request timed out. Please try again.",
                    "retryable": True,
                }
            )
        elif isinstance(error, ConnectionError):
            error_info.update(
                {
                    "category": "connection",
                    "status_code": 502,
                    "severity": "high",
                    "user_message": "Service temporarily unavailable. We're working on it.",
                    "retryable": True,
                }
            )
        elif "authentication" in str(error).lower() or "unauthorized" in str(error).lower():
            error_info.update(
                {
                    "category": "auth",
                    "status_code": 401,
                    "severity": "medium",
                    "user_message": "Authentication required. Please sign in again.",
                    "retryable": False,
                }
            )
        elif "permission" in str(error).lower() or "forbidden" in str(error).lower():
            error_info.update(
                {
                    "category": "auth",
                    "status_code": 403,
                    "severity": "medium",
                    "user_message": "You don't have permission for this action.",
                    "retryable": False,
                }
            )
        elif "claude" in str(error).lower() or "anthropic" in str(error).lower():
            error_info.update(
                {
                    "category": "claude_api",
                    "status_code": 502,
                    "severity": "medium",
                    "user_message": "AI service temporarily unavailable. Retrying automatically...",
                    "retryable": True,
                }
            )
        elif "ghl" in str(error).lower() or "gohighlevel" in str(error).lower():
            error_info.update(
                {
                    "category": "ghl_api",
                    "status_code": 502,
                    "severity": "medium",
                    "user_message": "CRM service experiencing issues. Data will be synced when available.",
                    "retryable": True,
                }
            )
        elif "database" in str(error).lower() or "postgres" in str(error).lower():
            error_info.update(
                {
                    "category": "database",
                    "status_code": 503,
                    "severity": "high",
                    "user_message": "Data service temporarily unavailable. Please try again.",
                    "retryable": True,
                }
            )
        else:
            error_info.update(
                {
                    "category": "system",
                    "status_code": 500,
                    "severity": "high",
                    "user_message": "An unexpected error occurred. Our team has been notified.",
                    "retryable": True,
                }
            )

        return error_info

    async def _log_performance_metrics(self, request: Request, response, process_time: float, correlation_id: str):
        """Log performance metrics with different levels based on performance"""

        endpoint = f"{request.method} {request.url.path}"

        if process_time > 10.0:
            logger.error(
                f"EXTREMELY slow request: {endpoint} took {process_time:.2f}s",
                extra={
                    "correlation_id": correlation_id,
                    "endpoint": endpoint,
                    "duration": process_time,
                    "status_code": response.status_code,
                    "performance_tier": "critical",
                },
            )
        elif process_time > 5.0:
            logger.warning(
                f"Very slow request: {endpoint} took {process_time:.2f}s",
                extra={
                    "correlation_id": correlation_id,
                    "endpoint": endpoint,
                    "duration": process_time,
                    "status_code": response.status_code,
                    "performance_tier": "warning",
                },
            )
        elif process_time > 2.0:
            logger.info(
                f"Slow request: {endpoint} took {process_time:.2f}s",
                extra={
                    "correlation_id": correlation_id,
                    "endpoint": endpoint,
                    "duration": process_time,
                    "status_code": response.status_code,
                    "performance_tier": "info",
                },
            )

    async def _log_error(self, error_info: Dict[str, Any], request: Request, correlation_id: str):
        """Enhanced error logging with categorization"""

        # Include request details for debugging
        request_details = {
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "user_agent": request.headers.get("user-agent", ""),
            "client_ip": request.client.host if request.client else "unknown",
            "content_type": request.headers.get("content-type", ""),
        }

        logger_method = {"low": logger.info, "medium": logger.warning, "high": logger.error}.get(
            error_info["severity"], logger.error
        )

        logger_method(
            f"🚨 ERROR [{error_info['category'].upper()}]: {error_info['error_message']}",
            extra={
                **error_info,
                **request_details,
                "jorge_platform": True,  # Tag for filtering
            },
        )

        # Count errors for circuit breaker logic
        endpoint_key = f"{request.method}:{request.url.path}"
        self.error_counts[endpoint_key] += 1

    async def _create_error_response(
        self, error_info: Dict[str, Any], request: Request, correlation_id: str
    ) -> JSONResponse:
        """Create standardized error response with actionable guidance"""

        # Determine if we should expose detailed error info
        is_debug = getattr(request.app, "debug", False)

        response_content = {
            "success": False,
            "error": {
                "code": error_info["error_type"],
                "category": error_info["category"],
                "message": error_info["user_message"],
                "retryable": error_info["retryable"],
                "severity": error_info["severity"],
            },
            "correlation_id": correlation_id,
            "timestamp": error_info["timestamp"],
            "endpoint": error_info["endpoint"],
        }

        # Add debug information in development
        if is_debug:
            response_content["debug"] = {
                "error_id": error_info["id"],
                "original_message": error_info["error_message"],
                "process_time": error_info["process_time"],
                "stack_trace": error_info["stack_trace"],
            }

        # Add actionable guidance based on error category
        guidance = self._get_actionable_guidance(error_info["category"], error_info["retryable"])
        if guidance:
            response_content["guidance"] = guidance

        # Add retry information for retryable errors
        if error_info["retryable"]:
            response_content["retry"] = {
                "recommended": True,
                "suggested_delay_seconds": self._get_retry_delay(error_info["category"]),
                "max_retries": 3,
            }

        return JSONResponse(
            status_code=error_info["status_code"],
            content=response_content,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Error-Category": error_info["category"],
                "X-Error-Retryable": str(error_info["retryable"]).lower(),
            },
        )

    async def _circuit_breaker_response(self, request: Request, correlation_id: str) -> JSONResponse:
        """Return circuit breaker response when service is failing"""

        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "CIRCUIT_BREAKER_OPEN",
                    "category": "system",
                    "message": "Service temporarily unavailable due to high error rate. Please try again later.",
                    "retryable": True,
                    "severity": "high",
                },
                "correlation_id": correlation_id,
                "timestamp": time.time(),
                "endpoint": f"{request.method} {request.url.path}",
                "guidance": {
                    "action": "Wait and retry",
                    "description": "The service is experiencing issues and has been temporarily disabled to prevent cascading failures.",
                    "estimated_recovery_time": "1-2 minutes",
                },
                "retry": {"recommended": True, "suggested_delay_seconds": 60, "max_retries": 3},
            },
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Error-Category": "circuit_breaker",
                "X-Error-Retryable": "true",
                "Retry-After": "60",
            },
        )

    def _get_actionable_guidance(self, category: str, retryable: bool) -> Optional[Dict[str, str]]:
        """Get user-friendly guidance based on error category"""

        guidance_map = {
            "http": {
                "action": "Check your request",
                "description": "The request format may be incorrect. Please verify your data and try again.",
            },
            "timeout": {
                "action": "Retry your request",
                "description": "The request took too long to complete. This is usually temporary.",
            },
            "connection": {
                "action": "Check connectivity",
                "description": "Unable to connect to external services. Please check your internet connection.",
            },
            "auth": {
                "action": "Re-authenticate",
                "description": "Please sign out and sign back in to refresh your authentication.",
            },
            "claude_api": {
                "action": "Wait and retry",
                "description": "AI services are experiencing temporary issues. We'll retry automatically.",
            },
            "ghl_api": {
                "action": "Continue working",
                "description": "CRM sync is temporarily delayed. Your data will be saved and synced when the service recovers.",
            },
            "database": {
                "action": "Try again",
                "description": "Database service is temporarily unavailable. Please try your request again.",
            },
            "system": {
                "action": "Contact support if persistent",
                "description": "An unexpected error occurred. Our team has been automatically notified.",
            },
        }

        return guidance_map.get(category)

    def _get_retry_delay(self, category: str) -> int:
        """Get recommended retry delay based on error category"""

        delay_map = {"timeout": 2, "connection": 5, "claude_api": 3, "ghl_api": 10, "database": 5, "system": 5}

        return delay_map.get(category, 5)


# Convenience function for FastAPI app integration
def create_bulletproof_error_middleware():
    """Create and return the bulletproof error handling middleware"""
    return BulletproofErrorHandler


# Legacy alias for backward compatibility
ErrorHandlerMiddleware = BulletproofErrorHandler
