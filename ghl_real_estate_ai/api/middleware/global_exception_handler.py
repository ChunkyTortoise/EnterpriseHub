"""
Comprehensive Global Exception Handler for Jorge's Real Estate AI Platform.

Provides consistent error responses, proper HTTP status codes, and structured
error logging to eliminate 500 errors and enhance user experience.

Features:
- Structured error responses with consistent schema
- Proper HTTP status codes for different error types
- User-friendly error messages with actionable guidance
- Comprehensive logging with correlation tracking
- Development vs production error detail levels
- Integration with Jorge's business logic validation
- WebSocket error handling support
"""

import asyncio
import time
import traceback
import uuid
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

try:
    from ghl_real_estate_ai.services.error_monitoring_service import ErrorCategory, get_error_monitoring_service
except ImportError:
    # Fallback if monitoring service is not available
    def get_error_monitoring_service():
        return None

    class ErrorCategory:
        VALIDATION = "validation"
        AUTHENTICATION = "authentication"
        AUTHORIZATION = "authorization"
        BUSINESS_LOGIC = "business_logic"
        EXTERNAL_API = "external_api"
        DATABASE = "database"
        NETWORK = "network"
        SYSTEM = "system"
        WEBSOCKET = "websocket"
        PERFORMANCE = "performance"


logger = get_logger(__name__)


class JorgeErrorResponse:
    """Standardized error response structure for Jorge's platform."""

    def __init__(
        self,
        error_type: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        retryable: bool = False,
        guidance: Optional[str] = None,
    ):
        self.error_type = error_type
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.correlation_id = correlation_id or self._generate_correlation_id()
        self.retryable = retryable
        self.guidance = guidance
        self.timestamp = time.time()

    def _generate_correlation_id(self) -> str:
        """Generate correlation ID for error tracking."""
        return f"jorge_err_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"

    def to_dict(self, include_debug: bool = False) -> Dict[str, Any]:
        """Convert to dictionary response."""
        response = {
            "success": False,
            "error": {"type": self.error_type, "message": self.message, "retryable": self.retryable},
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
        }

        if self.guidance:
            response["guidance"] = self.guidance

        if self.retryable:
            response["retry"] = {
                "recommended": True,
                "suggested_delay_seconds": self._get_retry_delay(),
                "max_retries": 3,
            }

        if include_debug and self.details:
            response["debug"] = self.details

        return response

    def _get_retry_delay(self) -> int:
        """Get retry delay based on error type."""
        delay_map = {"timeout": 2, "external_service": 5, "database": 3, "rate_limit": 60, "temporary": 5}
        return delay_map.get(self.error_type, 5)


class GlobalExceptionHandler:
    """Comprehensive global exception handler for Jorge's platform."""

    def __init__(self):
        self.error_patterns = self._load_error_patterns()
        try:
            self.monitoring_service = get_error_monitoring_service()
        except Exception:
            self.monitoring_service = None
            logger.warning("Error monitoring service not available - continuing without monitoring")

    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load Jorge-specific error patterns and responses."""
        return {
            # Business Logic Errors
            "commission_validation": {
                "status_code": 400,
                "message": "Commission rate validation failed",
                "guidance": "Commission must be between 5% and 8% for Jorge's listings",
                "retryable": False,
            },
            "property_qualification": {
                "status_code": 400,
                "message": "Property does not meet Jorge's criteria",
                "guidance": "Properties must be residential, $100K-$2M range, in supported markets",
                "retryable": False,
            },
            "lead_scoring_error": {
                "status_code": 400,
                "message": "Lead scoring validation failed",
                "guidance": "Check lead data completeness and contact information",
                "retryable": True,
            },
            # External Service Errors
            "ghl_api_error": {
                "status_code": 502,
                "message": "GoHighLevel service temporarily unavailable",
                "guidance": "CRM operations will retry automatically",
                "retryable": True,
            },
            "claude_api_error": {
                "status_code": 502,
                "message": "AI assistant service temporarily unavailable",
                "guidance": "AI features will be restored shortly",
                "retryable": True,
            },
            "retell_api_error": {
                "status_code": 502,
                "message": "Voice calling service unavailable",
                "guidance": "Voice features temporarily disabled",
                "retryable": True,
            },
            # Database and Performance
            "database_timeout": {
                "status_code": 503,
                "message": "Database operation timed out",
                "guidance": "Please try your request again",
                "retryable": True,
            },
            "cache_miss": {
                "status_code": 202,
                "message": "Data is being processed",
                "guidance": "Results will be available shortly",
                "retryable": True,
            },
            # Authentication and Authorization
            "auth_token_expired": {
                "status_code": 401,
                "message": "Authentication token has expired",
                "guidance": "Please sign in again to continue",
                "retryable": False,
            },
            "insufficient_permissions": {
                "status_code": 403,
                "message": "Insufficient permissions for this action",
                "guidance": "Contact your administrator for access",
                "retryable": False,
            },
            # WebSocket Specific
            "websocket_connection_failed": {
                "status_code": 503,
                "message": "Real-time connection failed",
                "guidance": "Refreshing page may restore real-time features",
                "retryable": True,
            },
            "websocket_message_invalid": {
                "status_code": 400,
                "message": "Invalid real-time message format",
                "guidance": "Check message structure and try again",
                "retryable": False,
            },
        }

    async def handle_validation_error(
        self, request: Request, exc: Union[RequestValidationError, ValidationError]
    ) -> JorgeErrorResponse:
        """Handle Pydantic validation errors with user-friendly messages."""

        correlation_id = self._get_correlation_id(request)

        # Extract field-specific validation errors
        field_errors = []
        for error in exc.errors():
            loc = " -> ".join([str(l) for l in error["loc"]])
            msg = error["msg"]
            field_errors.append(f"{loc}: {msg}")

        # Check for Jorge-specific validation patterns
        error_msg = str(exc)
        jorge_context = self._get_jorge_validation_context(error_msg, field_errors)

        error_response = JorgeErrorResponse(
            error_type="validation_error",
            message=jorge_context.get("message", "Invalid request data"),
            status_code=422,
            details={"field_errors": field_errors, "validation_type": jorge_context.get("type", "general")},
            correlation_id=correlation_id,
            retryable=False,
            guidance=jorge_context.get("guidance"),
        )

        # Record error in monitoring system
        await self._record_error_event(
            request=request, error_response=error_response, category=ErrorCategory.VALIDATION, exception=exc
        )

        return error_response

    def _get_jorge_validation_context(self, error_msg: str, field_errors: list) -> Dict[str, str]:
        """Get Jorge-specific validation context and guidance."""

        error_msg_lower = error_msg.lower()

        # Commission validation
        if any("commission" in field.lower() for field in field_errors):
            return {
                "type": "commission",
                "message": "Commission rate is invalid",
                "guidance": "Jorge's commission rate must be between 5% and 8%. Standard rate is 6%.",
            }

        # Phone number validation
        if any("phone" in field.lower() for field in field_errors):
            return {
                "type": "contact",
                "message": "Phone number format is invalid",
                "guidance": "Please provide a valid 10-digit US phone number (e.g., 555-123-4567)",
            }

        # Email validation
        if any("email" in field.lower() for field in field_errors):
            return {
                "type": "contact",
                "message": "Email address format is invalid",
                "guidance": "Please provide a valid email address (e.g., contact@example.com)",
            }

        # Price/value validation
        if any("price" in field.lower() or "value" in field.lower() for field in field_errors):
            return {
                "type": "property",
                "message": "Property value is outside acceptable range",
                "guidance": "Jorge handles properties between $100,000 and $2,000,000",
            }

        # Date validation
        if any("date" in field.lower() or "time" in field.lower() for field in field_errors):
            return {
                "type": "datetime",
                "message": "Date/time format is invalid",
                "guidance": "Please provide dates in ISO format (YYYY-MM-DD) or Unix timestamp",
            }

        return {
            "type": "general",
            "message": "Request data validation failed",
            "guidance": "Please check the highlighted fields and correct any errors",
        }

    async def handle_http_exception(
        self, request: Request, exc: Union[HTTPException, StarletteHTTPException]
    ) -> JorgeErrorResponse:
        """Handle HTTP exceptions with Jorge context."""

        correlation_id = self._get_correlation_id(request)

        # Classify the HTTP error
        error_context = self._classify_http_error(exc.status_code, str(exc.detail))

        error_response = JorgeErrorResponse(
            error_type=error_context["type"],
            message=error_context["message"],
            status_code=exc.status_code,
            details={"original_detail": str(exc.detail)},
            correlation_id=correlation_id,
            retryable=error_context["retryable"],
            guidance=error_context.get("guidance"),
        )

        # Record error in monitoring system
        await self._record_error_event(
            request=request,
            error_response=error_response,
            category=self._map_http_status_to_category(exc.status_code),
            exception=exc,
        )

        return error_response

    async def handle_system_exception(self, request: Request, exc: Exception) -> JorgeErrorResponse:
        """Handle unexpected system exceptions."""

        correlation_id = self._get_correlation_id(request)
        exc_str = str(exc)
        exc_type = type(exc).__name__

        # Classify system errors by pattern
        error_context = self._classify_system_error(exc_type, exc_str)

        # Log the full error for debugging
        logger.error(
            f"🚨 System Exception: {exc_type}",
            extra={
                "correlation_id": correlation_id,
                "endpoint": f"{request.method} {request.url.path}",
                "error_type": exc_type,
                "error_message": exc_str,
                "stack_trace": traceback.format_exc(),
                "jorge_platform": True,
            },
        )

        error_response = JorgeErrorResponse(
            error_type=error_context["type"],
            message=error_context["message"],
            status_code=error_context["status_code"],
            details={
                "exception_type": exc_type,
                "stack_trace": traceback.format_exc() if settings.environment == "development" else None,
            },
            correlation_id=correlation_id,
            retryable=error_context["retryable"],
            guidance=error_context.get("guidance"),
        )

        # Record error in monitoring system
        await self._record_error_event(
            request=request, error_response=error_response, category=self._map_exception_to_category(exc), exception=exc
        )

        return error_response

    def _classify_http_error(self, status_code: int, detail: str) -> Dict[str, Any]:
        """Classify HTTP errors for Jorge context."""

        detail_lower = detail.lower()

        # 400 Bad Request patterns
        if status_code == 400:
            if "commission" in detail_lower:
                return self.error_patterns["commission_validation"]
            elif "property" in detail_lower:
                return self.error_patterns["property_qualification"]
            elif "lead" in detail_lower:
                return self.error_patterns["lead_scoring_error"]
            else:
                return {
                    "type": "bad_request",
                    "message": "Invalid request format",
                    "retryable": False,
                    "guidance": "Please check your request data and try again",
                }

        # 401 Unauthorized
        elif status_code == 401:
            if "expired" in detail_lower:
                return self.error_patterns["auth_token_expired"]
            else:
                return {
                    "type": "authentication_required",
                    "message": "Authentication required",
                    "retryable": False,
                    "guidance": "Please sign in to access this feature",
                }

        # 403 Forbidden
        elif status_code == 403:
            return self.error_patterns["insufficient_permissions"]

        # 404 Not Found
        elif status_code == 404:
            return {
                "type": "resource_not_found",
                "message": "Requested resource was not found",
                "retryable": False,
                "guidance": "Please check the resource ID and try again",
            }

        # 429 Rate Limited
        elif status_code == 429:
            return {
                "type": "rate_limit",
                "message": "Too many requests",
                "retryable": True,
                "guidance": "Please wait a moment before trying again",
            }

        # 5xx Server Errors
        elif status_code >= 500:
            return {
                "type": "server_error",
                "message": "Server encountered an error",
                "retryable": True,
                "guidance": "Please try again in a few moments",
            }

        else:
            return {"type": "unknown_http_error", "message": detail, "retryable": False}

    def _classify_system_error(self, exc_type: str, exc_str: str) -> Dict[str, Any]:
        """Classify system errors by type and message."""

        exc_str_lower = exc_str.lower()

        # Database errors
        if (
            "database" in exc_str_lower
            or "postgres" in exc_str_lower
            or "connection" in exc_str_lower
            and "database" in exc_str_lower
        ):
            return {
                "type": "database_error",
                "message": "Database service temporarily unavailable",
                "status_code": 503,
                "retryable": True,
                "guidance": "Please try your request again",
            }

        # Timeout errors
        elif exc_type in ["TimeoutError", "asyncio.TimeoutError"] or "timeout" in exc_str_lower:
            return {
                "type": "timeout",
                "message": "Request timed out",
                "status_code": 408,
                "retryable": True,
                "guidance": "The operation took too long. Please try again.",
            }

        # External API errors
        elif "claude" in exc_str_lower or "anthropic" in exc_str_lower:
            return self.error_patterns["claude_api_error"]

        elif "ghl" in exc_str_lower or "gohighlevel" in exc_str_lower:
            return self.error_patterns["ghl_api_error"]

        elif "retell" in exc_str_lower:
            return self.error_patterns["retell_api_error"]

        # Memory/Resource errors
        elif exc_type in ["MemoryError", "ResourceWarning"]:
            return {
                "type": "resource_exhausted",
                "message": "System resources temporarily unavailable",
                "status_code": 503,
                "retryable": True,
                "guidance": "Please try again in a few moments",
            }

        # WebSocket errors
        elif "websocket" in exc_str_lower:
            if "connection" in exc_str_lower:
                return self.error_patterns["websocket_connection_failed"]
            else:
                return self.error_patterns["websocket_message_invalid"]

        # Network errors
        elif exc_type in ["ConnectionError", "NetworkError"] or "network" in exc_str_lower:
            return {
                "type": "network_error",
                "message": "Network connection failed",
                "status_code": 502,
                "retryable": True,
                "guidance": "Please check your connection and try again",
            }

        # Default system error
        else:
            return {
                "type": "system_error",
                "message": "An unexpected error occurred",
                "status_code": 500,
                "retryable": True,
                "guidance": "Our team has been notified. Please try again.",
            }

    def _get_correlation_id(self, request: Request) -> str:
        """Extract or generate correlation ID for the request."""
        return (
            getattr(request.state, "correlation_id", None)
            or request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or f"jorge_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
        )

    async def _record_error_event(
        self,
        request: Request,
        error_response: JorgeErrorResponse,
        category: ErrorCategory,
        exception: Optional[Exception] = None,
    ):
        """Record error event in monitoring system."""

        try:
            if self.monitoring_service:
                # Extract user information if available
                user_id = getattr(request.state, "user_id", None)
                session_id = getattr(request.state, "session_id", None)

                # Record the error event
                await self.monitoring_service.record_error(
                    error_id=error_response.correlation_id,
                    correlation_id=error_response.correlation_id,
                    endpoint=f"{request.method} {request.url.path}",
                    error_type=error_response.error_type,
                    category=category,
                    message=error_response.message,
                    context=error_response.details,
                    user_id=user_id,
                    session_id=session_id,
                    user_agent=request.headers.get("user-agent"),
                    ip_address=request.client.host if request.client else None,
                    stack_trace=traceback.format_exc() if exception else None,
                )

        except Exception as monitoring_error:
            # Don't let monitoring errors affect the main error handling
            logger.warning(
                f"Failed to record error event: {monitoring_error}", extra={"error_id": error_response.correlation_id}
            )

    def _map_http_status_to_category(self, status_code: int) -> ErrorCategory:
        """Map HTTP status code to error category."""

        if status_code == 400:
            return ErrorCategory.VALIDATION
        elif status_code == 401:
            return ErrorCategory.AUTHENTICATION
        elif status_code == 403:
            return ErrorCategory.AUTHORIZATION
        elif status_code == 422:
            return ErrorCategory.VALIDATION
        elif 500 <= status_code <= 599:
            return ErrorCategory.SYSTEM
        else:
            return ErrorCategory.SYSTEM

    def _map_exception_to_category(self, exception: Exception) -> ErrorCategory:
        """Map exception type to error category."""

        exc_str = str(exception).lower()
        exc_type = type(exception).__name__

        if "validation" in exc_str or exc_type in ["ValidationError", "ValueError"]:
            return ErrorCategory.VALIDATION
        elif "auth" in exc_str or "unauthorized" in exc_str:
            return ErrorCategory.AUTHENTICATION
        elif "permission" in exc_str or "forbidden" in exc_str:
            return ErrorCategory.AUTHORIZATION
        elif "claude" in exc_str or "anthropic" in exc_str:
            return ErrorCategory.EXTERNAL_API
        elif "ghl" in exc_str or "gohighlevel" in exc_str:
            return ErrorCategory.EXTERNAL_API
        elif "database" in exc_str or "postgres" in exc_str:
            return ErrorCategory.DATABASE
        elif "timeout" in exc_str or exc_type in ["TimeoutError"]:
            return ErrorCategory.PERFORMANCE
        elif "websocket" in exc_str:
            return ErrorCategory.WEBSOCKET
        elif "network" in exc_str or "connection" in exc_str:
            return ErrorCategory.NETWORK
        elif "commission" in exc_str or "property" in exc_str or "lead" in exc_str:
            return ErrorCategory.BUSINESS_LOGIC
        else:
            return ErrorCategory.SYSTEM


# Global instance
_global_exception_handler = GlobalExceptionHandler()


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """FastAPI validation exception handler."""
    error_response = await _global_exception_handler.handle_validation_error(request, exc)
    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict(include_debug=settings.environment == "development"),
        headers={"X-Correlation-ID": error_response.correlation_id, "X-Error-Type": error_response.error_type},
    )


async def http_exception_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]) -> JSONResponse:
    """FastAPI HTTP exception handler."""
    error_response = await _global_exception_handler.handle_http_exception(request, exc)
    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict(include_debug=settings.environment == "development"),
        headers={"X-Correlation-ID": error_response.correlation_id, "X-Error-Type": error_response.error_type},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI general exception handler."""
    error_response = await _global_exception_handler.handle_system_exception(request, exc)
    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict(include_debug=settings.environment == "development"),
        headers={"X-Correlation-ID": error_response.correlation_id, "X-Error-Type": error_response.error_type},
    )


def setup_global_exception_handlers(app):
    """Set up all global exception handlers for the FastAPI app."""

    # Validation errors (422)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # HTTP exceptions (4xx, 5xx)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # General exceptions (500)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("✅ Global exception handlers configured for Jorge's platform")
