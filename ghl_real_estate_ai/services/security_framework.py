"""
Production Security Framework for Service 6 Lead Recovery & Nurture Engine.

Implements enterprise-grade security controls:
- Authentication & Authorization
- Rate limiting with Redis backend
- Input validation & sanitization
- Webhook signature verification
- CORS configuration
- Security headers
- Audit logging
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union

import jwt
import redis.asyncio as aioredis
from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class SecurityLevel(Enum):
    """Security levels for different endpoints."""

    PUBLIC = "public"  # No authentication required
    AUTHENTICATED = "authenticated"  # Valid JWT required
    ADMIN = "admin"  # Admin role required
    SYSTEM = "system"  # System-level authentication


class RateLimitType(Enum):
    """Rate limiting types."""

    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_ENDPOINT = "per_endpoint"
    GLOBAL = "global"


class SecurityConfig(BaseModel):
    """Security configuration settings."""

    # JWT Configuration
    jwt_secret_key: str = settings.jwt_secret_key
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Rate Limiting
    default_rate_limit: int = 100  # requests per minute
    burst_rate_limit: int = 200  # max burst requests
    rate_limit_window: int = 60  # seconds

    # API Keys
    webhook_signing_secrets: Dict[str, str] = {
        "ghl": settings.ghl_webhook_secret,
        "apollo": settings.apollo_webhook_secret,
        "twilio": settings.twilio_webhook_secret,
        "sendgrid": settings.sendgrid_webhook_secret,
        "vapi": settings.vapi_webhook_secret,
        "retell": settings.retell_webhook_secret,
    }

    # CORS Settings
    cors_origins: List[str] = [
        "https://app.gohighlevel.com",
        "https://*.gohighlevel.com",
        "http://localhost:3000",
        "http://localhost:8501",  # Streamlit default
    ]

    # Security Headers
    security_headers: Dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    }


class SecurityFramework:
    """
    Production security framework for Service 6.

    Provides enterprise-grade security controls with Redis-backed
    rate limiting, JWT authentication, and comprehensive audit logging.
    """

    def __init__(self, redis_url: str = None):
        """Initialize security framework."""
        self.config = SecurityConfig()
        self.redis_url = redis_url or settings.redis_url
        self._redis_pool = None
        self.security_bearer = HTTPBearer(auto_error=False)

    async def _get_redis(self) -> aioredis.Redis:
        """Get Redis connection with connection pooling."""
        if not self._redis_pool:
            self._redis_pool = aioredis.ConnectionPool.from_url(
                self.redis_url, max_connections=20, retry_on_timeout=True
            )
        return aioredis.Redis(connection_pool=self._redis_pool)

    async def close_redis(self):
        """Close Redis connection pool."""
        if self._redis_pool:
            await self._redis_pool.disconnect()

    # ============================================================================
    # Authentication & Authorization
    # ============================================================================

    def generate_jwt_token(self, user_id: str, role: str = "user", additional_claims: Dict[str, Any] = None) -> str:
        """Generate JWT token with expiry."""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "role": role,
            "iat": now,
            "exp": now + timedelta(hours=self.config.jwt_expiry_hours),
            "iss": "service6-lead-engine",
            "aud": "service6-api",
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)

        logger.info(f"Generated JWT token for user {user_id} with role {role}")
        return token

    async def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return claims."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
                audience="service6-api",
                issuer="service6-lead-engine",
            )

            # Additional validation
            if payload.get("exp", 0) < time.time():
                raise HTTPException(status_code=401, detail="Token expired")

            logger.debug(f"Validated JWT token for user {payload.get('sub')}")
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")

    async def authenticate_request(
        self, request: Request, required_level: SecurityLevel = SecurityLevel.AUTHENTICATED
    ) -> Dict[str, Any]:
        """Authenticate request based on security level."""

        if required_level == SecurityLevel.PUBLIC:
            return {"user_id": "anonymous", "role": "public"}

        # Extract token from Authorization header
        credentials: HTTPAuthorizationCredentials = await self.security_bearer(request)

        if not credentials:
            raise HTTPException(status_code=401, detail="Authorization header required")

        token_payload = await self.validate_jwt_token(credentials.credentials)

        # Check role authorization
        user_role = token_payload.get("role", "user")

        if required_level == SecurityLevel.ADMIN and user_role not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        if required_level == SecurityLevel.SYSTEM and user_role != "system":
            raise HTTPException(status_code=403, detail="System access required")

        # Log successful authentication
        await self._audit_log(
            event="authentication_success",
            user_id=token_payload.get("sub"),
            details={"role": user_role, "endpoint": str(request.url.path), "method": request.method},
            request=request,
        )

        return token_payload

    # ============================================================================
    # Rate Limiting
    # ============================================================================

    async def check_rate_limit(
        self, request: Request, limit: int = None, window: int = None, limit_type: RateLimitType = RateLimitType.PER_IP
    ) -> bool:
        """
        Check rate limit with Redis backend.

        Returns True if request is within limits, False if rate limited.
        """
        redis = await self._get_redis()

        # Use provided limits or defaults
        limit = limit or self.config.default_rate_limit
        window = window or self.config.rate_limit_window

        # Generate rate limit key
        if limit_type == RateLimitType.PER_IP:
            key_suffix = self._get_client_ip(request)
        elif limit_type == RateLimitType.PER_USER:
            # Extract from JWT if available
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    token_payload = await self.validate_jwt_token(auth_header[7:])
                    key_suffix = token_payload.get("sub", "anonymous")
                except:
                    key_suffix = self._get_client_ip(request)
            else:
                key_suffix = self._get_client_ip(request)
        elif limit_type == RateLimitType.PER_ENDPOINT:
            key_suffix = f"{request.method}:{request.url.path}"
        else:  # GLOBAL
            key_suffix = "global"

        rate_limit_key = f"rate_limit:{limit_type.value}:{key_suffix}"

        # Sliding window rate limiting
        now = time.time()
        window_start = now - window

        # Remove expired entries and count current requests
        pipe = redis.pipeline()
        pipe.zremrangebyscore(rate_limit_key, 0, window_start)
        pipe.zcard(rate_limit_key)
        pipe.zadd(rate_limit_key, {str(now): now})
        pipe.expire(rate_limit_key, window)

        results = await pipe.execute()
        current_count = results[1]

        if current_count >= limit:
            # Log rate limit exceeded
            await self._audit_log(
                event="rate_limit_exceeded",
                user_id=key_suffix,
                details={
                    "limit": limit,
                    "window": window,
                    "current_count": current_count,
                    "limit_type": limit_type.value,
                },
                request=request,
            )

            logger.warning(f"Rate limit exceeded for {key_suffix}: {current_count}/{limit}")
            return False

        return True

    async def rate_limit_middleware(
        self, request: Request, limit: int = None, limit_type: RateLimitType = RateLimitType.PER_IP
    ):
        """Rate limiting middleware that raises HTTPException if exceeded."""
        if not await self.check_rate_limit(request, limit=limit, limit_type=limit_type):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(self.config.rate_limit_window)},
            )

    # ============================================================================
    # Webhook Signature Verification
    # ============================================================================

    async def verify_webhook_signature(self, request: Request, provider: str, signature_header: str = None) -> bool:
        """
        Verify webhook signature from external providers.

        Supports GHL, Apollo, Twilio, and SendGrid signature formats.
        """
        body = await request.body()

        if provider == "ghl":
            return self._verify_ghl_signature(request, body)
        elif provider == "apollo":
            return self._verify_apollo_signature(request, body)
        elif provider == "twilio":
            return self._verify_twilio_signature(request, body)
        elif provider == "sendgrid":
            return self._verify_sendgrid_signature(request, body)
        elif provider == "vapi":
            return self._verify_vapi_signature(request, body)
        else:
            logger.error(f"Unknown webhook provider: {provider}")
            return False

    def _verify_vapi_signature(self, request: Request, body: bytes) -> bool:
        """
        Verify Vapi.ai webhook signature.
        Vapi uses x-vapi-secret header for authentication.
        """
        provided_secret = request.headers.get("x-vapi-secret")
        if not provided_secret:
            logger.error("Vapi webhook secret missing")
            return False

        configured_secret = self.config.webhook_signing_secrets.get("vapi")
        if not configured_secret:
            logger.error("Vapi webhook secret not configured")
            # In development, we might want to allow if secret is not set,
            # but for production hardening we must require it.
            return settings.environment == "development"

        return hmac.compare_digest(provided_secret, configured_secret)

    def _verify_ghl_signature(self, request: Request, body: bytes) -> bool:
        """Verify GoHighLevel webhook signature."""
        signature = request.headers.get("X-GHL-Signature")
        if not signature:
            logger.error(
                "GHL webhook signature missing - potential unauthorized access attempt",
                extra={"client_ip": self._get_client_ip(request), "error_id": "WEBHOOK_SIGNATURE_MISSING"},
            )
            # SECURITY FIX: Raise exception instead of returning False to prevent bypass
            raise HTTPException(status_code=401, detail="Webhook signature required")

        secret = self.config.webhook_signing_secrets.get("ghl")
        if not secret:
            logger.error(
                "CRITICAL: GHL webhook secret not configured in production",
                extra={
                    "error_id": "WEBHOOK_SECRET_MISSING",
                    "environment": getattr(settings, "environment", "unknown"),
                },
            )
            # SECURITY FIX: Configuration errors should prevent execution
            raise HTTPException(status_code=500, detail="Webhook authentication not configured")

        try:
            expected_signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

            # SECURITY FIX: Use constant-time comparison
            is_valid = hmac.compare_digest(signature, expected_signature)

            # Fallback: GHL Custom Webhook actions send a static shared
            # secret (not a per-request HMAC).  Accept the raw secret as
            # a valid signature so both Marketplace HMAC webhooks and
            # workflow Custom Webhook actions are supported.
            if not is_valid:
                is_valid = hmac.compare_digest(signature, secret)

            if not is_valid:
                logger.warning(
                    "GHL webhook signature verification failed",
                    extra={
                        "client_ip": self._get_client_ip(request),
                        "error_id": "WEBHOOK_SIGNATURE_INVALID",
                        "signature_provided": signature[:10] + "..." if len(signature) > 10 else signature,
                    },
                )

            return is_valid

        except Exception as e:
            logger.error(
                f"Webhook signature verification error: {type(e).__name__}: {e}",
                extra={"error_id": "WEBHOOK_SIGNATURE_ERROR", "client_ip": self._get_client_ip(request)},
                exc_info=True,
            )
            # SECURITY FIX: Unexpected errors should reject the webhook
            raise HTTPException(status_code=500, detail="Webhook verification failed")

    def _verify_apollo_signature(self, request: Request, body: bytes) -> bool:
        """Verify Apollo.io webhook signature."""
        signature = request.headers.get("X-Apollo-Signature")
        if not signature:
            return False

        secret = self.config.webhook_signing_secrets.get("apollo")
        if not secret:
            logger.error("Apollo webhook secret not configured")
            return False

        expected_signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        return hmac.compare_digest(signature, f"sha256={expected_signature}")

    def _verify_twilio_signature(self, request: Request, body: bytes) -> bool:
        """Verify Twilio webhook signature."""
        signature = request.headers.get("X-Twilio-Signature")
        if not signature:
            return False

        # Twilio signature verification requires URL + form parameters
        url = str(request.url)
        auth_token = self.config.webhook_signing_secrets.get("twilio")

        if not auth_token:
            logger.error("Twilio auth token not configured")
            return False

        # Parse form data for Twilio format
        form_data = {}
        if request.headers.get("Content-Type") == "application/x-www-form-urlencoded":
            # This is simplified - in production, use proper form parsing
            form_data = dict(x.split("=", 1) for x in body.decode().split("&"))

        # Build string to sign (URL + sorted parameters)
        sorted_params = sorted(form_data.items())
        data_string = url + "".join(f"{k}{v}" for k, v in sorted_params)

        expected_signature = hmac.new(auth_token.encode(), data_string.encode(), hashlib.sha1).digest()

        import base64

        expected_signature_b64 = base64.b64encode(expected_signature).decode()

        return hmac.compare_digest(signature, expected_signature_b64)

    def _verify_sendgrid_signature(self, request: Request, body: bytes) -> bool:
        """Verify SendGrid webhook signature."""
        signature = request.headers.get("X-Twilio-Email-Event-Webhook-Signature")
        timestamp = request.headers.get("X-Twilio-Email-Event-Webhook-Timestamp")

        if not signature or not timestamp:
            return False

        public_key = self.config.webhook_signing_secrets.get("sendgrid")
        if not public_key:
            logger.error("SendGrid public key not configured")
            return False

        # SendGrid uses ECDSA verification - simplified here
        # In production, implement full ECDSA verification with cryptography library
        payload = timestamp.encode() + body

        # For demo purposes, using HMAC (replace with ECDSA in production)
        expected_signature = hmac.new(public_key.encode(), payload, hashlib.sha256).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    # ============================================================================
    # Input Validation & Sanitization
    # ============================================================================

    def sanitize_input(self, data: Union[str, Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """Sanitize input data to prevent injection attacks."""
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        else:
            return data

    def _sanitize_string(self, value: str) -> str:
        """Sanitize string input."""
        # Remove null bytes
        value = value.replace("\x00", "")

        # Limit length
        if len(value) > 10000:
            value = value[:10000]

        # Basic HTML entity encoding for dangerous characters
        dangerous_chars = {"<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;", "&": "&amp;"}

        for char, entity in dangerous_chars.items():
            value = value.replace(char, entity)

        return value

    def validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format."""
        import re

        # Basic phone validation - enhance as needed
        pattern = r"^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$"
        return bool(re.match(pattern, phone))

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    # ============================================================================
    # Security Headers & CORS
    # ============================================================================

    def add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        for header, value in self.config.security_headers.items():
            response.headers[header] = value
        return response

    def is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is allowed for CORS."""
        import fnmatch

        for allowed_origin in self.config.cors_origins:
            if fnmatch.fnmatch(origin, allowed_origin):
                return True
        return False

    # ============================================================================
    # Audit Logging
    # ============================================================================

    async def _audit_log(
        self, event: str, user_id: str = None, details: Dict[str, Any] = None, request: Request = None
    ):
        """Log security events for audit trail."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "user_id": user_id or "anonymous",
            "details": details or {},
            "metadata": {
                "source_ip": self._get_client_ip(request) if request else None,
                "user_agent": request.headers.get("User-Agent") if request else None,
                "request_id": getattr(request.state, "request_id", None) if request else None,
            },
        }

        # Log to file and/or external audit system
        logger.info(f"AUDIT: {json.dumps(audit_entry)}")

        # Store in Redis for real-time monitoring
        try:
            redis = await self._get_redis()
            await redis.lpush("audit_log", json.dumps(audit_entry))
            await redis.ltrim("audit_log", 0, 10000)  # Keep last 10k entries
        except Exception as e:
            logger.error(f"Failed to store audit log in Redis: {e}")

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client
        return getattr(request.client, "host", "unknown")


# ============================================================================
# Security Decorators
# ============================================================================


def require_auth(security_level: SecurityLevel = SecurityLevel.AUTHENTICATED, rate_limit: int = None):
    """Decorator for endpoint authentication and rate limiting."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break

            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            # Initialize security framework
            security = SecurityFramework()

            try:
                # Check rate limiting
                if rate_limit:
                    await security.rate_limit_middleware(request, limit=rate_limit)

                # Authenticate request
                auth_context = await security.authenticate_request(request, security_level)

                # Add auth context to request state
                request.state.auth = auth_context

                # Call original function
                return await func(*args, **kwargs)

            finally:
                await security.close_redis()

        return wrapper

    return decorator


def verify_webhook(provider: str):
    """Decorator for webhook signature verification."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                for val in kwargs.values():
                    if isinstance(val, Request):
                        request = val
                        break

            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            # Verify webhook signature
            security = SecurityFramework()

            try:
                if not await security.verify_webhook_signature(request, provider):
                    raise HTTPException(status_code=401, detail="Invalid webhook signature")

                # Log successful webhook verification
                await security._audit_log(event="webhook_verified", details={"provider": provider}, request=request)

                return await func(*args, **kwargs)

            finally:
                await security.close_redis()

        return wrapper

    return decorator


# ============================================================================
# Security Middleware Classes
# ============================================================================


class SecurityMiddleware:
    """FastAPI middleware for security controls."""

    def __init__(self, app):
        self.app = app
        self.security = SecurityFramework()

    async def __call__(self, scope, receive, send):
        """Process request through security controls."""
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Add security headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))

                    # Add security headers
                    for header, value in self.security.config.security_headers.items():
                        headers[header.encode()] = value.encode()

                    message["headers"] = list(headers.items())

                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test_security_framework():
        """Test security framework functionality."""
        security = SecurityFramework()

        # Test JWT token generation and validation
        token = security.generate_jwt_token("user123", "admin")
        print(f"Generated token: {token[:50]}...")

        try:
            payload = await security.validate_jwt_token(token)
            print(f"Token validation successful: {payload}")
        except Exception as e:
            print(f"Token validation failed: {e}")

        await security.close_redis()

    # Run test
    asyncio.run(test_security_framework())
