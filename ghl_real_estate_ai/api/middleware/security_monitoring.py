"""
Security Monitoring Middleware for GHL Real Estate AI API

Real-time security monitoring and threat detection for all API endpoints.
Integrates with SecurityComplianceMonitor for comprehensive protection.

Features:
- API request monitoring and threat detection
- Real-time PII exposure prevention
- GHL webhook signature validation
- Rate limiting and abuse detection
- Security incident automation
"""

import time
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass
import hashlib
import hmac

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
import redis.asyncio as redis

from ..services.security_compliance_monitor import (
    get_security_monitor,
    SecurityThreatLevel,
    APIAbuseDetection
)
from ..services.secure_logging_service import get_secure_logger, LogLevel

@dataclass
class SecurityMetrics:
    """Security metrics for request monitoring."""
    request_count: int = 0
    failed_auth_count: int = 0
    rate_limit_violations: int = 0
    pii_exposures: int = 0
    suspicious_requests: int = 0

class SecurityMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for real-time security monitoring and threat detection.

    Monitors all API requests for:
    - Authentication failures
    - Rate limiting violations
    - PII exposure attempts
    - Suspicious request patterns
    - GHL webhook signature validation
    """

    def __init__(self, app, tenant_id: Optional[str] = None):
        super().__init__(app)
        self.tenant_id = tenant_id
        self.logger = get_secure_logger(
            tenant_id=tenant_id,
            component_name="security_middleware"
        )

        # Initialize security components
        self.security_monitor = get_security_monitor(tenant_id)

        # Rate limiting configuration
        self.rate_limits = {
            "/api/auth/login": {"requests": 5, "window": 300},  # 5 requests per 5 minutes
            "/api/ghl/webhook": {"requests": 100, "window": 60},  # 100 webhooks per minute
            "/api/ml/predict": {"requests": 50, "window": 60},   # 50 predictions per minute
            "default": {"requests": 100, "window": 60}           # 100 requests per minute default
        }

        # Suspicious patterns
        self.suspicious_patterns = [
            r"(?i)(script|javascript|<|>|%3c|%3e)",  # XSS attempts
            r"(?i)(union|select|insert|delete|drop)",  # SQL injection
            r"(?i)(\.\.\/|\.\.\\|%2e%2e%2f)",         # Path traversal
            r"(?i)(exec|eval|system|cmd)",             # Command injection
        ]

        # Security metrics
        self.metrics = SecurityMetrics()

        # Redis connection for rate limiting
        self.redis_client = None

    async def dispatch(self, request: Request, call_next) -> Response:
        """Main security monitoring dispatch."""
        start_time = time.time()

        try:
            # Initialize Redis connection if needed
            if not self.redis_client:
                try:
                    self.redis_client = redis.from_url("redis://localhost:6379/0")
                except Exception as e:
                    self.logger.warning(f"Redis connection failed: {e}")

            # Extract client information
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            endpoint = str(request.url.path)

            # Pre-request security checks
            security_check_result = await self._pre_request_security_check(
                request, client_ip, endpoint
            )

            if security_check_result.get("blocked", False):
                return self._create_security_response(
                    status_code=security_check_result["status_code"],
                    message=security_check_result["message"],
                    incident_id=security_check_result.get("incident_id")
                )

            # Process the request
            response = await call_next(request)

            # Post-request security analysis
            await self._post_request_security_check(
                request, response, client_ip, endpoint, start_time
            )

            # Add security headers
            self._add_security_headers(response)

            return response

        except Exception as e:
            self.logger.error(
                "Security middleware error",
                metadata={"error": str(e), "endpoint": endpoint}
            )
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address considering proxies."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def _pre_request_security_check(
        self,
        request: Request,
        client_ip: str,
        endpoint: str
    ) -> Dict[str, Any]:
        """Perform pre-request security checks."""
        # Check if IP is blocked
        if await self._is_ip_blocked(client_ip):
            await self._record_blocked_request(client_ip, endpoint, "blocked_ip")
            return {
                "blocked": True,
                "status_code": HTTP_403_FORBIDDEN,
                "message": "Access denied"
            }

        # Rate limiting check
        rate_limit_result = await self._check_rate_limiting(client_ip, endpoint)
        if rate_limit_result.get("exceeded", False):
            await self._handle_rate_limit_violation(client_ip, endpoint)
            return {
                "blocked": True,
                "status_code": HTTP_429_TOO_MANY_REQUESTS,
                "message": "Rate limit exceeded"
            }

        # Check for suspicious patterns in URL
        if self._contains_suspicious_patterns(str(request.url)):
            incident_id = await self._handle_suspicious_request(
                client_ip, endpoint, "suspicious_url_pattern"
            )
            return {
                "blocked": True,
                "status_code": HTTP_403_FORBIDDEN,
                "message": "Suspicious request pattern detected",
                "incident_id": incident_id
            }

        # GHL webhook signature validation
        if endpoint.startswith("/api/ghl/webhook"):
            webhook_valid = await self._validate_ghl_webhook(request)
            if not webhook_valid:
                incident_id = await self._handle_ghl_webhook_forgery(client_ip)
                return {
                    "blocked": True,
                    "status_code": HTTP_401_UNAUTHORIZED,
                    "message": "Invalid webhook signature",
                    "incident_id": incident_id
                }

        return {"blocked": False}

    async def _post_request_security_check(
        self,
        request: Request,
        response: Response,
        client_ip: str,
        endpoint: str,
        start_time: float
    ) -> None:
        """Perform post-request security analysis."""
        duration = time.time() - start_time

        # Record request metrics
        self.metrics.request_count += 1
        self.security_monitor.record_api_request(client_ip, endpoint, start_time)

        # Check for authentication failures
        if response.status_code == 401:
            await self._handle_authentication_failure(
                request, client_ip, endpoint
            )

        # Monitor response for PII exposure
        if hasattr(response, 'body') and response.body:
            await self._check_response_pii_exposure(response, endpoint)

        # Log successful requests for pattern analysis
        if response.status_code < 400:
            self.logger.info(
                f"API request processed successfully",
                metadata={
                    "endpoint": endpoint,
                    "client_ip": client_ip,
                    "duration_ms": duration * 1000,
                    "status_code": response.status_code
                }
            )

    async def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP address is in the blocked list."""
        if not self.redis_client:
            return False

        try:
            is_blocked = await self.redis_client.sismember("security:blocked_ips", client_ip)
            return bool(is_blocked)
        except Exception as e:
            self.logger.error(f"Error checking blocked IPs: {e}")
            return False

    async def _check_rate_limiting(self, client_ip: str, endpoint: str) -> Dict[str, Any]:
        """Check if request exceeds rate limits."""
        if not self.redis_client:
            return {"exceeded": False}

        try:
            # Get rate limit configuration for endpoint
            rate_config = self.rate_limits.get(endpoint, self.rate_limits["default"])
            window = rate_config["window"]
            max_requests = rate_config["requests"]

            # Create Redis key for this client/endpoint combination
            key = f"rate_limit:{client_ip}:{endpoint}"

            # Get current request count
            current_count = await self.redis_client.get(key)
            current_count = int(current_count) if current_count else 0

            if current_count >= max_requests:
                return {"exceeded": True, "current": current_count, "limit": max_requests}

            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            await pipe.execute()

            return {"exceeded": False, "current": current_count + 1, "limit": max_requests}

        except Exception as e:
            self.logger.error(f"Error checking rate limits: {e}")
            return {"exceeded": False}

    async def _handle_rate_limit_violation(self, client_ip: str, endpoint: str) -> None:
        """Handle rate limit violation."""
        self.metrics.rate_limit_violations += 1

        # Record authentication failure
        self.security_monitor.record_authentication_failure(
            user_id="unknown",
            source_ip=client_ip,
            failure_reason="rate_limit_exceeded",
            endpoint=endpoint
        )

        # Log security event
        self.logger.log_security_event(
            event_type="RATE_LIMIT_VIOLATION",
            details={
                "client_ip": client_ip,
                "endpoint": endpoint,
                "violation_type": "requests_per_minute"
            },
            severity="MEDIUM"
        )

        # Create API abuse detection record
        abuse_detection = APIAbuseDetection(
            client_id=client_ip,
            endpoint=endpoint,
            request_count=self.rate_limits.get(endpoint, self.rate_limits["default"])["requests"],
            time_window_minutes=self.rate_limits.get(endpoint, self.rate_limits["default"])["window"] // 60,
            rate_limit_exceeded=True,
            suspicious_patterns=["high_frequency_requests"],
            timestamp=datetime.now(timezone.utc)
        )

        # Trigger automated response for severe violations
        if self.metrics.rate_limit_violations > 10:  # Multiple violations from same IP
            await self._auto_block_ip(client_ip, "repeated_rate_limit_violations")

    def _contains_suspicious_patterns(self, url: str) -> bool:
        """Check if URL contains suspicious patterns."""
        import re

        for pattern in self.suspicious_patterns:
            if re.search(pattern, url):
                return True
        return False

    async def _handle_suspicious_request(
        self,
        client_ip: str,
        endpoint: str,
        threat_type: str
    ) -> str:
        """Handle suspicious request pattern."""
        self.metrics.suspicious_requests += 1

        # Create security incident
        incident = await self.security_monitor._create_security_incident(
            incident_type="suspicious_request_pattern",
            description=f"Suspicious {threat_type} detected from {client_ip}",
            threat_level=SecurityThreatLevel.MEDIUM,
            source_ip=client_ip,
            affected_data_types=["api_access"],
            mitigation_actions=["request_blocking", "ip_monitoring"]
        )

        return incident.incident_id

    async def _validate_ghl_webhook(self, request: Request) -> bool:
        """Validate GoHighLevel webhook signature."""
        try:
            # Get signature from headers
            signature = request.headers.get("x-ghl-signature")
            if not signature:
                return False

            # Get request body
            body = await request.body()
            if not body:
                return False

            # Validate using security monitor
            return await self.security_monitor.validate_ghl_webhook(
                payload=body.decode(),
                signature=signature,
                source_ip=self._get_client_ip(request)
            )

        except Exception as e:
            self.logger.error(f"Error validating GHL webhook: {e}")
            return False

    async def _handle_ghl_webhook_forgery(self, client_ip: str) -> str:
        """Handle GHL webhook forgery attempt."""
        incident = await self.security_monitor._create_security_incident(
            incident_type="ghl_webhook_forgery",
            description=f"Invalid GHL webhook signature from {client_ip}",
            threat_level=SecurityThreatLevel.HIGH,
            source_ip=client_ip,
            affected_data_types=["webhook_data", "ghl_integration"],
            mitigation_actions=["signature_validation", "source_verification"]
        )

        # Auto-block after multiple forgery attempts
        await self._increment_forgery_count(client_ip)

        return incident.incident_id

    async def _increment_forgery_count(self, client_ip: str) -> None:
        """Track webhook forgery attempts and auto-block if needed."""
        if not self.redis_client:
            return

        try:
            key = f"webhook_forgery:{client_ip}"
            count = await self.redis_client.incr(key)
            await self.redis_client.expire(key, 3600)  # 1 hour window

            if count >= 3:  # 3 forgery attempts in 1 hour
                await self._auto_block_ip(client_ip, "webhook_forgery_attempts")

        except Exception as e:
            self.logger.error(f"Error tracking forgery attempts: {e}")

    async def _handle_authentication_failure(
        self,
        request: Request,
        client_ip: str,
        endpoint: str
    ) -> None:
        """Handle authentication failure."""
        self.metrics.failed_auth_count += 1

        # Extract user information if available
        user_id = "unknown"
        if request.method == "POST":
            try:
                body = await request.body()
                if body:
                    data = json.loads(body.decode())
                    user_id = data.get("username", data.get("email", "unknown"))
            except:
                pass

        # Record the failure
        self.security_monitor.record_authentication_failure(
            user_id=user_id,
            source_ip=client_ip,
            failure_reason="invalid_credentials",
            endpoint=endpoint
        )

        # Track repeated failures
        await self._track_auth_failures(client_ip, user_id)

    async def _track_auth_failures(self, client_ip: str, user_id: str) -> None:
        """Track authentication failures for brute force detection."""
        if not self.redis_client:
            return

        try:
            # Track failures by IP
            ip_key = f"auth_failures:ip:{client_ip}"
            ip_count = await self.redis_client.incr(ip_key)
            await self.redis_client.expire(ip_key, 300)  # 5 minute window

            # Track failures by user
            user_key = f"auth_failures:user:{user_id}"
            user_count = await self.redis_client.incr(user_key)
            await self.redis_client.expire(user_key, 300)  # 5 minute window

            # Trigger brute force detection
            if ip_count >= 10:  # 10 failures from same IP in 5 minutes
                await self.security_monitor._create_security_incident(
                    incident_type="brute_force_attack",
                    description=f"Brute force attack detected from IP: {client_ip}",
                    threat_level=SecurityThreatLevel.HIGH,
                    source_ip=client_ip,
                    affected_data_types=["authentication"],
                    mitigation_actions=["ip_blocking", "rate_limiting"]
                )

                # Auto-block the IP
                await self._auto_block_ip(client_ip, "brute_force_attack")

            elif user_count >= 5:  # 5 failures for same user in 5 minutes
                await self.security_monitor._create_security_incident(
                    incident_type="credential_stuffing",
                    description=f"Credential stuffing attack detected for user: {user_id}",
                    threat_level=SecurityThreatLevel.MEDIUM,
                    user_id=user_id,
                    source_ip=client_ip,
                    affected_data_types=["user_credentials"],
                    mitigation_actions=["account_lockout", "user_notification"]
                )

        except Exception as e:
            self.logger.error(f"Error tracking auth failures: {e}")

    async def _check_response_pii_exposure(
        self,
        response: Response,
        endpoint: str
    ) -> None:
        """Check API response for potential PII exposure."""
        try:
            if hasattr(response, 'body') and response.body:
                response_text = response.body.decode() if isinstance(response.body, bytes) else str(response.body)

                # Use security monitor for PII detection
                pii_result = await self.security_monitor.check_pii_exposure(
                    text=response_text,
                    context={"component": "api_response", "endpoint": endpoint}
                )

                if pii_result.redaction_count > 0:
                    self.metrics.pii_exposures += 1

                    # Create security incident for PII exposure
                    await self.security_monitor._create_security_incident(
                        incident_type="pii_exposure_api_response",
                        description=f"PII detected in API response: {endpoint}",
                        threat_level=SecurityThreatLevel.HIGH,
                        affected_data_types=pii_result.pii_types_found,
                        mitigation_actions=["response_sanitization", "endpoint_review"]
                    )

        except Exception as e:
            self.logger.error(f"Error checking response PII: {e}")

    async def _auto_block_ip(self, client_ip: str, reason: str) -> None:
        """Automatically block IP address."""
        if not self.redis_client:
            return

        try:
            await self.redis_client.sadd("security:blocked_ips", client_ip)

            self.logger.security(
                f"IP address auto-blocked: {client_ip}",
                metadata={
                    "client_ip": client_ip,
                    "reason": reason,
                    "action": "auto_block"
                }
            )

        except Exception as e:
            self.logger.error(f"Error auto-blocking IP: {e}")

    async def _record_blocked_request(
        self,
        client_ip: str,
        endpoint: str,
        reason: str
    ) -> None:
        """Record blocked request for analytics."""
        self.logger.info(
            f"Request blocked from {client_ip}",
            metadata={
                "client_ip": client_ip,
                "endpoint": endpoint,
                "reason": reason,
                "action": "blocked"
            }
        )

    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        # Security headers already added by SecurityHeadersMiddleware
        # Add additional monitoring headers
        response.headers["X-Security-Monitored"] = "true"
        response.headers["X-Request-ID"] = str(time.time())

    def _create_security_response(
        self,
        status_code: int,
        message: str,
        incident_id: Optional[str] = None
    ) -> JSONResponse:
        """Create security-related error response."""
        content = {
            "error": "Security violation",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if incident_id:
            content["incident_id"] = incident_id

        return JSONResponse(
            status_code=status_code,
            content=content,
            headers={"X-Security-Response": "true"}
        )

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get current security metrics."""
        return {
            "total_requests": self.metrics.request_count,
            "failed_authentications": self.metrics.failed_auth_count,
            "rate_limit_violations": self.metrics.rate_limit_violations,
            "pii_exposures": self.metrics.pii_exposures,
            "suspicious_requests": self.metrics.suspicious_requests,
            "monitoring_status": "active"
        }

# Middleware factory function
def create_security_monitoring_middleware(tenant_id: Optional[str] = None):
    """Create security monitoring middleware with tenant configuration."""
    def middleware_factory(app):
        return SecurityMonitoringMiddleware(app, tenant_id=tenant_id)

    return middleware_factory