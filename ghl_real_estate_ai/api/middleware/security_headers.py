"""
Enhanced Security Headers Middleware with OWASP Compliance

Features:
- Comprehensive OWASP security headers
- Environment-specific CSP policies
- Request ID tracking for security auditing
- Security event logging
- Production-ready security configuration
"""

import os
import uuid
from datetime import datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enhanced security headers middleware with OWASP compliance."""

    def __init__(
        self,
        app,
        environment: str = None,
        enable_csp: bool = True,
        enable_hsts: bool = True,
        enable_request_id: bool = True,
    ):
        super().__init__(app)
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.enable_csp = enable_csp
        self.enable_hsts = enable_hsts
        self.enable_request_id = enable_request_id

        # CSP policies by environment
        self.csp_policies = {
            "development": self._get_development_csp(),
            "staging": self._get_staging_csp(),
            "production": self._get_production_csp(),
        }

    def _get_development_csp(self) -> str:
        """Development-friendly CSP policy."""
        return (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss: http://localhost:* https://localhost:*; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'"
        )

    def _get_staging_csp(self) -> str:
        """Staging environment CSP policy."""
        return (
            "default-src 'self'; "
            "script-src 'self' 'nonce-{nonce}' "
            "https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'nonce-{nonce}' "
            "https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https:; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests"
        )

    def _get_production_csp(self) -> str:
        """Production-ready strict CSP policy.

        Uses nonce-based script/style allowlisting with strict-dynamic.
        'unsafe-inline' is kept as a fallback for browsers that don't support nonces,
        but strict-dynamic takes precedence in modern browsers (CSP Level 3).
        """
        return (
            "default-src 'self'; "
            "script-src 'self' 'strict-dynamic' 'nonce-{nonce}'; "
            "style-src 'self' 'nonce-{nonce}'; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https:; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests; "
            "block-all-mixed-content"
        )

    def _generate_csp_nonce(self) -> str:
        """Generate cryptographically secure nonce for CSP."""
        return uuid.uuid4().hex[:16]

    def _get_security_headers(self, request: Request) -> dict:
        """Get comprehensive security headers."""
        headers = {}

        # Core security headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        headers["X-XSS-Protection"] = "0"  # Modern browsers prefer CSP over XSS filter
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # HSTS for HTTPS
        if self.enable_hsts and (request.url.scheme == "https" or self.environment == "production"):
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubOntario Millss; preload"

        # Content Security Policy
        if self.enable_csp:
            csp_policy = self.csp_policies.get(self.environment, self.csp_policies["production"])

            # Add nonce for inline scripts/styles in staging and production
            if self.environment in ("staging", "production"):
                nonce = self._generate_csp_nonce()
                csp_policy = csp_policy.format(nonce=nonce)
                headers["X-CSP-Nonce"] = nonce

            headers["Content-Security-Policy"] = csp_policy

        # Additional security headers
        headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        headers["Cross-Origin-Opener-Policy"] = "same-origin"
        headers["Cross-Origin-Resource-Policy"] = "cross-origin"

        # Server information disclosure prevention
        headers["Server"] = "Jorge-AI-Platform"
        headers["X-Powered-By"] = "Jorge-AI"

        return headers

    def _add_request_id(self, request: Request, response) -> str:
        """Add unique request ID for security auditing."""
        request_id = str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id

        # Store request ID in request state for logging
        if hasattr(request, "state"):
            request.state.request_id = request_id

        return request_id

    def _log_security_event(self, request: Request, request_id: str):
        """Log security-relevant request information."""
        client_ip = self._get_client_ip(request)

        logger.info(
            "Security headers applied",
            extra={
                "security_event": "headers_applied",
                "request_id": request_id,
                "ip_address": client_ip,
                "user_agent": request.headers.get("User-Agent", ""),
                "path": request.url.path,
                "method": request.method,
                "environment": self.environment,
                "timestamp": datetime.utcnow().isoformat(),
                "event_id": "SEC_001",
            },
        )

    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP address."""
        # Check forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _detect_suspicious_headers(self, request: Request) -> bool:
        """Detect potentially malicious request headers."""
        suspicious_patterns = [
            "script",
            "javascript:",
            "vbscript:",
            "onload=",
            "onerror=",
            "<script",
            "</script",
            "<?php",
            "<?xml",
        ]

        for header_name, header_value in request.headers.items():
            header_value_lower = header_value.lower()
            for pattern in suspicious_patterns:
                if pattern in header_value_lower:
                    logger.warning(
                        f"Suspicious header detected: {header_name}",
                        extra={
                            "security_event": "suspicious_header",
                            "header_name": header_name,
                            "header_value": header_value[:100],  # Truncate for safety
                            "ip_address": self._get_client_ip(request),
                            "event_id": "SEC_002",
                        },
                    )
                    return True
        return False

    async def dispatch(self, request: Request, call_next):
        """Apply comprehensive security headers and monitoring."""
        # Detect suspicious headers
        if self._detect_suspicious_headers(request):
            # Continue processing but log the event
            pass

        # Process the request
        response = await call_next(request)

        # Apply security headers
        security_headers = self._get_security_headers(request)
        for name, value in security_headers.items():
            response.headers[name] = value

        # Add request ID tracking
        if self.enable_request_id:
            request_id = self._add_request_id(request, response)

            # Log security event (sampling for performance)
            import random

            if random.random() < 0.01:  # Log 1% of requests for monitoring
                self._log_security_event(request, request_id)

        return response


# Additional security utilities


def generate_secure_token() -> str:
    """Generate a cryptographically secure token."""
    return uuid.uuid4().hex


def validate_content_type(content_type: str) -> bool:
    """Validate that content type is safe."""
    allowed_types = [
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
        "text/plain",
        "application/octet-stream",
    ]
    return any(content_type.startswith(allowed) for allowed in allowed_types)
