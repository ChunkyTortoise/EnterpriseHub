#!/usr/bin/env python3
"""
Enhanced Authentication Middleware - Critical Security Fixes
Addresses authentication vulnerabilities identified in security audit.

SECURITY FIXES:
1. No weak fallback secrets in production
2. Rate limiting on authentication attempts
3. Proper password length handling with user notification
4. Comprehensive security logging
5. Token blacklist for logout functionality
"""

import secrets
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import bcrypt
import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class AuthenticationError(Exception):
    """Authentication-specific error"""

    def __init__(self, message: str, error_id: str = None, status_code: int = 401):
        super().__init__(message)
        self.error_id = error_id or f"AUTH_ERROR_{uuid.uuid4().hex[:8].upper()}"
        self.status_code = status_code


class RateLimitError(Exception):
    """Rate limiting error"""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class EnhancedJWTAuth:
    """Enhanced JWT authentication with comprehensive security controls."""

    def __init__(self):
        self.secret_key = self._get_secure_secret_key()
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

        # Rate limiting configuration
        self.max_login_attempts = 5
        self.login_window_minutes = 15
        self.lockout_duration_minutes = 30

        # Redis for rate limiting and token blacklist
        self.redis_url = getattr(settings, "redis_url", "redis://localhost:6379")
        self._redis_pool = None

    def _get_secure_secret_key(self) -> str:
        """Get JWT secret key with strict production validation."""
        secret_key = getattr(settings, "jwt_secret_key", None)

        if not secret_key:
            if getattr(settings, "environment", "development") == "production":
                error_id = f"JWT_SECRET_MISSING_{uuid.uuid4().hex[:8].upper()}"
                logger.critical(
                    "CRITICAL_SECURITY_ERROR: JWT secret key not configured in production",
                    extra={
                        "error_id": error_id,
                        "environment": settings.environment,
                        "startup_time": datetime.utcnow().isoformat(),
                    },
                )
                raise ValueError(f"JWT_SECRET_KEY environment variable is required in production. Error ID: {error_id}")

            # Generate cryptographically secure key for development
            secret_key = secrets.token_urlsafe(64)
            logger.warning(
                "AUTH_WARNING: Generated temporary JWT secret for development",
                extra={
                    "environment": getattr(settings, "environment", "development"),
                    "key_length": len(secret_key),
                    "generated_at": datetime.utcnow().isoformat(),
                },
            )

        # Validate secret key strength
        if len(secret_key) < 32:
            error_id = f"WEAK_JWT_SECRET_{uuid.uuid4().hex[:8].upper()}"
            logger.error(
                "SECURITY_ERROR: JWT secret key too short (minimum 32 characters)",
                extra={"error_id": error_id, "key_length": len(secret_key), "minimum_length": 32},
            )
            raise ValueError(f"JWT secret key must be at least 32 characters. Error ID: {error_id}")

        return secret_key

    async def _get_redis(self) -> aioredis.Redis:
        """Get Redis connection for rate limiting and token blacklist."""
        if not self._redis_pool:
            try:
                self._redis_pool = aioredis.ConnectionPool.from_url(
                    self.redis_url, max_connections=20, retry_on_timeout=True
                )
            except Exception as e:
                logger.error(
                    f"REDIS_CONNECTION_FAILED: Could not connect to Redis",
                    extra={"redis_url": self.redis_url, "error": str(e)},
                )
                raise

        return aioredis.Redis(connection_pool=self._redis_pool)

    async def check_rate_limit(self, identifier: str, request: Request) -> None:
        """
        Check authentication rate limiting.

        Args:
            identifier: User identifier (email, IP, etc.)
            request: FastAPI request object

        Raises:
            RateLimitError: If rate limit exceeded
        """
        redis = await self._get_redis()

        # Create rate limit key
        rate_limit_key = f"auth_rate_limit:{identifier}"
        current_time = int(time.time())
        window_start = current_time - (self.login_window_minutes * 60)

        try:
            # Remove expired attempts
            await redis.zremrangebyscore(rate_limit_key, 0, window_start)

            # Count current attempts
            attempt_count = await redis.zcard(rate_limit_key)

            if attempt_count >= self.max_login_attempts:
                # Check if lockout period has expired
                latest_attempt = await redis.zrevrange(rate_limit_key, 0, 0, withscores=True)
                if latest_attempt:
                    last_attempt_time = latest_attempt[0][1]
                    lockout_until = last_attempt_time + (self.lockout_duration_minutes * 60)

                    if current_time < lockout_until:
                        remaining_lockout = int(lockout_until - current_time)

                        logger.warning(
                            f"AUTH_RATE_LIMITED: Authentication attempts exceeded",
                            extra={
                                "identifier": identifier,
                                "attempt_count": attempt_count,
                                "max_attempts": self.max_login_attempts,
                                "lockout_remaining_seconds": remaining_lockout,
                                "client_ip": self._get_client_ip(request),
                            },
                        )

                        raise RateLimitError(
                            f"Too many authentication attempts. Please try again in {remaining_lockout} seconds.",
                            retry_after=remaining_lockout,
                        )

            # Record this attempt
            await redis.zadd(rate_limit_key, {str(uuid.uuid4()): current_time})
            await redis.expire(rate_limit_key, self.login_window_minutes * 60)

        except RateLimitError:
            raise
        except Exception as e:
            logger.error(
                f"RATE_LIMIT_CHECK_ERROR: Error checking rate limit", extra={"identifier": identifier, "error": str(e)}
            )
            # Don't block authentication if rate limiting fails
            pass

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a new JWT access token with enhanced security."""
        to_encode = data.copy()

        # Add security claims
        now = datetime.utcnow()
        expire = now + (expires_delta or timedelta(minutes=self.access_token_expire_minutes))

        to_encode.update(
            {
                "exp": expire,
                "iat": now,
                "nbf": now,  # Not before
                "iss": "enterprisehub-api",  # Issuer
                "aud": "enterprisehub-client",  # Audience
                "jti": uuid.uuid4().hex,  # JWT ID for blacklisting
                "token_type": "access",
            }
        )

        # Validate required claims
        if "sub" not in to_encode:
            raise ValueError("Subject (sub) claim is required")

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        logger.info(
            f"ACCESS_TOKEN_CREATED: Created access token",
            extra={"user_id": to_encode.get("sub"), "expires_at": expire.isoformat(), "token_id": to_encode.get("jti")},
        )

        return encoded_jwt

    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token for token renewal."""
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "nbf": now,
            "iss": "enterprisehub-api",
            "aud": "enterprisehub-client",
            "jti": uuid.uuid4().hex,
            "token_type": "refresh",
        }

        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        logger.info(
            f"REFRESH_TOKEN_CREATED: Created refresh token",
            extra={"user_id": user_id, "expires_at": expire.isoformat(), "token_id": payload.get("jti")},
        )

        return encoded_jwt

    async def verify_token(self, token: str, request: Request = None) -> Dict[str, Any]:
        """
        Verify and decode JWT token with comprehensive validation.

        Args:
            token: JWT token to verify
            request: FastAPI request (for logging)

        Returns:
            Token payload if valid

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience="enterprisehub-client",
                issuer="enterprisehub-api",
            )

            # Additional validation
            token_id = payload.get("jti")
            if not token_id:
                raise AuthenticationError("Token missing unique identifier", error_id="TOKEN_MISSING_JTI")

            # Check if token is blacklisted
            if await self._is_token_blacklisted(token_id):
                logger.warning(
                    f"BLACKLISTED_TOKEN_USED: Attempt to use blacklisted token",
                    extra={
                        "token_id": token_id,
                        "user_id": payload.get("sub"),
                        "client_ip": self._get_client_ip(request) if request else None,
                    },
                )
                raise AuthenticationError("Token has been revoked", error_id="TOKEN_BLACKLISTED", status_code=401)

            # Validate token type
            expected_type = "access"
            actual_type = payload.get("token_type")
            if actual_type != expected_type:
                raise AuthenticationError(
                    f"Invalid token type: expected {expected_type}, got {actual_type}", error_id="INVALID_TOKEN_TYPE"
                )

            # Validate required claims
            required_claims = ["sub", "exp", "iat"]
            missing_claims = [claim for claim in required_claims if claim not in payload]
            if missing_claims:
                raise AuthenticationError(
                    f"Token missing required claims: {missing_claims}", error_id="TOKEN_MISSING_CLAIMS"
                )

            logger.debug(
                f"TOKEN_VERIFIED: Successfully verified token",
                extra={
                    "user_id": payload.get("sub"),
                    "token_id": token_id,
                    "expires_at": datetime.fromtimestamp(payload.get("exp")).isoformat(),
                },
            )

            return payload

        except JWTError as e:
            error_type = type(e).__name__

            if "expired" in str(e).lower():
                error_id = "TOKEN_EXPIRED"
                message = "Token has expired"
            elif "signature" in str(e).lower():
                error_id = "TOKEN_INVALID_SIGNATURE"
                message = "Invalid token signature"
            else:
                error_id = "TOKEN_INVALID"
                message = f"Invalid token: {str(e)}"

            logger.warning(
                f"TOKEN_VERIFICATION_FAILED: {message}",
                extra={
                    "error_id": error_id,
                    "jwt_error_type": error_type,
                    "client_ip": self._get_client_ip(request) if request else None,
                },
            )

            raise AuthenticationError(message, error_id=error_id)

        except Exception as e:
            error_id = f"TOKEN_VERIFICATION_ERROR_{uuid.uuid4().hex[:8].upper()}"
            logger.error(
                f"TOKEN_VERIFICATION_ERROR: Unexpected error verifying token",
                extra={"error_id": error_id, "error_type": type(e).__name__, "error_message": str(e)},
                exc_info=True,
            )
            raise AuthenticationError(f"Token verification failed: {str(e)}", error_id=error_id)

    async def _is_token_blacklisted(self, token_id: str) -> bool:
        """Check if token is blacklisted."""
        try:
            redis = await self._get_redis()
            result = await redis.exists(f"blacklist_token:{token_id}")
            return bool(result)
        except Exception as e:
            logger.error(
                f"BLACKLIST_CHECK_ERROR: Error checking token blacklist", extra={"token_id": token_id, "error": str(e)}
            )
            # If blacklist check fails, allow token (fail open)
            return False

    async def blacklist_token(self, token_id: str, expires_at: datetime) -> None:
        """Add token to blacklist."""
        try:
            redis = await self._get_redis()

            # Calculate TTL (time until token naturally expires)
            ttl_seconds = int((expires_at - datetime.utcnow()).total_seconds())
            if ttl_seconds > 0:
                await redis.setex(f"blacklist_token:{token_id}", ttl_seconds, "1")

                logger.info(
                    f"TOKEN_BLACKLISTED: Token added to blacklist",
                    extra={"token_id": token_id, "ttl_seconds": ttl_seconds},
                )
        except Exception as e:
            logger.error(
                f"TOKEN_BLACKLIST_ERROR: Error blacklisting token", extra={"token_id": token_id, "error": str(e)}
            )

    def hash_password(self, password: str) -> str:
        """
        Hash password with proper length handling and user notification.

        SECURITY FIX: Notify user if password is truncated.
        """
        if len(password) > 72:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password must not exceed 72 characters"
            )

        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)  # Increased from default 10
        hashed = bcrypt.hashpw(password_bytes, salt)

        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password with proper length handling."""
        if len(plain_password) > 72:
            plain_password = plain_password[:72]

        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")

        return bcrypt.checkpw(password_bytes, hashed_bytes)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct client
        return getattr(request.client, "host", "unknown") if request.client else "unknown"


# Initialize enhanced auth
enhanced_auth = EnhancedJWTAuth()
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Enhanced dependency to get current authenticated user.

    SECURITY FIXES:
    1. Rate limiting on token validation
    2. Comprehensive logging
    3. Proper error handling
    """
    token = credentials.credentials

    # Basic rate limiting on token validation (prevent token brute force)
    client_ip = enhanced_auth._get_client_ip(request)
    try:
        await enhanced_auth.check_rate_limit(f"token_validation:{client_ip}", request)
    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for token validation: {e}",
            headers={"Retry-After": str(e.retry_after)},
        )

    try:
        payload = await enhanced_auth.verify_token(token, request)

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Token missing user identifier", error_id="TOKEN_MISSING_USER_ID")

        return {"user_id": user_id, "payload": payload, "token_id": payload.get("jti")}

    except AuthenticationError as e:
        raise HTTPException(
            status_code=e.status_code, detail=f"Authentication failed: {e}", headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_optional(
    request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Dict[str, Any]:
    """
    Optional authentication dependency for demo-safe endpoints.
    In non-production environments, missing credentials fall back to a demo user.
    """
    if credentials is None:
        if getattr(settings, "environment", "development") != "production":
            return {"user_id": "demo-user", "payload": {"role": "demo", "scope": "demo"}, "token_id": "demo"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await get_current_user(request, credentials)


# Export enhanced authentication
__all__ = [
    "EnhancedJWTAuth",
    "enhanced_auth",
    "get_current_user",
    "get_current_user_optional",
    "AuthenticationError",
    "RateLimitError",
]
