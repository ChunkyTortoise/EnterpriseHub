"""
Enhanced Input Validation and SQL Injection Protection Middleware

Features:
- SQL injection detection and prevention
- XSS protection for user-generated content
- Parameter validation and sanitization
- Request size limiting
- Malicious payload detection
- Security event logging
"""

import re
import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, ValidationError
import html
import bleach
from urllib.parse import unquote

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class SecurityValidator:
    """Advanced security validation for input sanitization."""

    def __init__(self):
        # SQL injection patterns (case-insensitive)
        self.sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(\b(script|javascript|vbscript)\b)",
            r"(--|/\*|\*/|;|'|\"|<|>)",
            r"(\b(or|and)\s+\d+=\d+)",
            r"(\b(or|and)\s+'[^']*'\s*=\s*'[^']*')",
            r"(\bxp_\w+)",
            r"(\bsp_\w+)",
            r"(\bsys\w+)",
            r"(\binformation_schema\b)",
            r"(\bmaster\.\w+)",
            r"(\bwaitfor\s+delay\b)",
            r"(\bconvert\s*\(\s*int\b)",
            r"(\bcast\s*\(\b)",
            r"(\bunion\s+(all\s+)?select\b)",
            r"(\bdeclare\s+@\w+)",
            r"(\bexec\s*\(\s*@\w+\s*\))",
        ]

        # XSS patterns
        self.xss_patterns = [
            r"<\s*script[^>]*>.*?</\s*script\s*>",
            r"<\s*img[^>]*\s+src\s*=\s*[\"']?\s*javascript:",
            r"<\s*iframe[^>]*>.*?</\s*iframe\s*>",
            r"<\s*object[^>]*>.*?</\s*object\s*>",
            r"<\s*embed[^>]*>",
            r"<\s*link[^>]*>",
            r"<\s*meta[^>]*>",
            r"on\w+\s*=\s*[\"'][^\"']*[\"']",
            r"javascript\s*:",
            r"vbscript\s*:",
            r"data\s*:\s*text/html",
        ]

        # Path traversal patterns
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"~\w*/",
            r"file://",
            r"/etc/passwd",
            r"/proc/",
            r"c:\\",
            r"c:/",
        ]

        # Compile patterns for performance
        self.compiled_sql_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
        self.compiled_xss_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
        self.compiled_path_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.path_traversal_patterns]

    def validate_sql_injection(self, value: str) -> tuple[bool, Optional[str]]:
        """Check for SQL injection patterns."""
        if not value or not isinstance(value, str):
            return True, None

        # Decode URL encoding
        decoded_value = unquote(value)

        for pattern in self.compiled_sql_patterns:
            if pattern.search(decoded_value):
                return False, f"SQL injection pattern detected: {pattern.pattern[:50]}"

        return True, None

    def validate_xss(self, value: str) -> tuple[bool, Optional[str]]:
        """Check for XSS patterns."""
        if not value or not isinstance(value, str):
            return True, None

        # Decode URL encoding and HTML entities
        decoded_value = html.unescape(unquote(value))

        for pattern in self.compiled_xss_patterns:
            if pattern.search(decoded_value):
                return False, f"XSS pattern detected: {pattern.pattern[:50]}"

        return True, None

    def validate_path_traversal(self, value: str) -> tuple[bool, Optional[str]]:
        """Check for path traversal patterns."""
        if not value or not isinstance(value, str):
            return True, None

        decoded_value = unquote(value)

        for pattern in self.compiled_path_patterns:
            if pattern.search(decoded_value):
                return False, f"Path traversal pattern detected: {pattern.pattern[:50]}"

        return True, None

    def sanitize_string(self, value: str, allow_html: bool = False) -> str:
        """Sanitize string input."""
        if not value or not isinstance(value, str):
            return value

        # HTML entity decode first
        value = html.unescape(value)

        if allow_html:
            # Allow safe HTML tags
            allowed_tags = ['b', 'i', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li']
            allowed_attributes = {}
            value = bleach.clean(value, tags=allowed_tags, attributes=allowed_attributes)
        else:
            # Strip all HTML
            value = bleach.clean(value, tags=[], attributes={}, strip=True)

        # Additional sanitization
        value = value.strip()

        return value


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Enhanced input validation middleware with security features."""

    def __init__(
        self,
        app,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        validate_json: bool = True,
        validate_query_params: bool = True,
        validate_form_data: bool = True,
        enable_sanitization: bool = True,
    ):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.validate_json = validate_json
        self.validate_query_params = validate_query_params
        self.validate_form_data = validate_form_data
        self.enable_sanitization = enable_sanitization
        self.validator = SecurityValidator()

    async def _validate_request_size(self, request: Request) -> None:
        """Check request size limits."""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            logger.warning(
                f"Request size exceeds limit: {content_length} bytes",
                extra={
                    "security_event": "request_size_exceeded",
                    "content_length": content_length,
                    "max_allowed": self.max_request_size,
                    "ip_address": self._get_client_ip(request),
                    "event_id": "VAL_001"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request entity too large"
            )

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP for logging."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.client.host if request.client else "unknown"

    def _validate_value(self, value: Any, param_name: str, request: Request) -> Any:
        """Validate a single value for security issues."""
        if not isinstance(value, str):
            return value

        # Check for SQL injection
        is_valid, reason = self.validator.validate_sql_injection(value)
        if not is_valid:
            logger.warning(
                f"SQL injection attempt detected in parameter '{param_name}'",
                extra={
                    "security_event": "sql_injection_attempt",
                    "parameter": param_name,
                    "value": value[:100],  # Truncate for safety
                    "reason": reason,
                    "ip_address": self._get_client_ip(request),
                    "path": request.url.path,
                    "event_id": "VAL_002"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input in parameter '{param_name}': {reason}"
            )

        # Check for XSS
        is_valid, reason = self.validator.validate_xss(value)
        if not is_valid:
            logger.warning(
                f"XSS attempt detected in parameter '{param_name}'",
                extra={
                    "security_event": "xss_attempt",
                    "parameter": param_name,
                    "value": value[:100],
                    "reason": reason,
                    "ip_address": self._get_client_ip(request),
                    "path": request.url.path,
                    "event_id": "VAL_003"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input in parameter '{param_name}': {reason}"
            )

        # Check for path traversal
        is_valid, reason = self.validator.validate_path_traversal(value)
        if not is_valid:
            logger.warning(
                f"Path traversal attempt detected in parameter '{param_name}'",
                extra={
                    "security_event": "path_traversal_attempt",
                    "parameter": param_name,
                    "value": value[:100],
                    "reason": reason,
                    "ip_address": self._get_client_ip(request),
                    "path": request.url.path,
                    "event_id": "VAL_004"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input in parameter '{param_name}': {reason}"
            )

        # Sanitize if enabled
        if self.enable_sanitization:
            value = self.validator.sanitize_string(value)

        return value

    def _validate_dict_recursive(self, data: Dict[str, Any], request: Request, prefix: str = "") -> Dict[str, Any]:
        """Recursively validate dictionary data."""
        validated_data = {}
        for key, value in data.items():
            param_name = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                validated_data[key] = self._validate_dict_recursive(value, request, param_name)
            elif isinstance(value, list):
                validated_data[key] = [
                    self._validate_value(item, f"{param_name}[{i}]", request) if isinstance(item, str)
                    else (self._validate_dict_recursive(item, request, f"{param_name}[{i}]") if isinstance(item, dict) else item)
                    for i, item in enumerate(value)
                ]
            else:
                validated_data[key] = self._validate_value(value, param_name, request)

        return validated_data

    async def _validate_query_parameters(self, request: Request) -> None:
        """Validate URL query parameters."""
        if not self.validate_query_params:
            return

        for param_name, param_value in request.query_params.items():
            self._validate_value(param_value, param_name, request)

    async def _validate_json_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """Validate JSON request body."""
        if not self.validate_json:
            return None

        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return None

        try:
            # Read body
            body = await request.body()
            if not body:
                return None

            # Parse JSON
            try:
                json_data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Invalid JSON in request body",
                    extra={
                        "security_event": "invalid_json",
                        "error": str(e),
                        "ip_address": self._get_client_ip(request),
                        "event_id": "VAL_005"
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON in request body"
                )

            # Validate JSON data
            if isinstance(json_data, dict):
                return self._validate_dict_recursive(json_data, request)
            else:
                return json_data

        except Exception as e:
            logger.error(
                f"Error validating JSON body: {str(e)}",
                extra={
                    "security_event": "json_validation_error",
                    "error": str(e),
                    "ip_address": self._get_client_ip(request),
                    "event_id": "VAL_006"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error processing request body"
            )

    def _is_business_critical_endpoint(self, path: str) -> bool:
        """Check if endpoint is business-critical and needs extra protection."""
        critical_patterns = [
            "/api/jorge",
            "/api/revenue",
            "/api/commission",
            "/api/analytics",
            "/api/bi",
            "/api/admin"
        ]
        return any(path.startswith(pattern) for pattern in critical_patterns)

    async def dispatch(self, request: Request, call_next):
        """Process request with comprehensive input validation."""
        try:
            # Check request size
            await self._validate_request_size(request)

            # Skip validation for certain endpoints
            skip_paths = ["/health", "/ping", "/docs", "/redoc", "/openapi.json"]
            if request.url.path in skip_paths:
                return await call_next(request)

            # Enhanced validation for business-critical endpoints
            if self._is_business_critical_endpoint(request.url.path):
                logger.info(
                    f"Enhanced validation for critical endpoint",
                    extra={
                        "security_event": "critical_endpoint_access",
                        "path": request.url.path,
                        "method": request.method,
                        "ip_address": self._get_client_ip(request),
                        "event_id": "VAL_007"
                    }
                )

            # Validate query parameters
            await self._validate_query_parameters(request)

            # Validate JSON body (if applicable)
            validated_json = await self._validate_json_body(request)

            # Store validated data in request state for use by endpoints
            if validated_json is not None:
                if hasattr(request, 'state'):
                    request.state.validated_json = validated_json

            # Process request
            response = await call_next(request)

            # Add validation headers
            response.headers["X-Input-Validation"] = "applied"

            return response

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in input validation: {str(e)}",
                extra={
                    "security_event": "validation_error",
                    "error": str(e),
                    "path": request.url.path,
                    "ip_address": self._get_client_ip(request),
                    "event_id": "VAL_008"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal validation error"
            )


# Utility functions for endpoint-specific validation

def validate_jorge_commission_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Special validation for Jorge's commission-related endpoints."""
    if not isinstance(data, dict):
        raise ValueError("Commission data must be a dictionary")

    # Validate commission percentage
    if "commission_percentage" in data:
        commission = data["commission_percentage"]
        if not isinstance(commission, (int, float)) or commission < 0 or commission > 100:
            raise ValueError("Commission percentage must be between 0 and 100")

    # Validate deal amounts
    for field in ["deal_amount", "commission_amount", "estimated_value"]:
        if field in data:
            value = data[field]
            if not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"{field} must be a non-negative number")

    return data


def validate_lead_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Special validation for lead-related data."""
    if not isinstance(data, dict):
        raise ValueError("Lead data must be a dictionary")

    # Validate email format
    if "email" in data:
        email = data["email"]
        if not isinstance(email, str) or "@" not in email:
            raise ValueError("Invalid email format")

    # Validate phone number
    if "phone" in data:
        phone = data["phone"]
        if not isinstance(phone, str) or len(phone.strip()) < 10:
            raise ValueError("Invalid phone number")

    return data