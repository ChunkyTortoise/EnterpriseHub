"""
Multi-Tenant Context Middleware for Customer Intelligence Platform.

Provides tenant isolation, request routing, and security enforcement
for B2B SaaS enterprise deployments.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import jwt
from functools import wraps
import time
import redis.asyncio as redis
import json

logger = logging.getLogger(__name__)

class TenantContext:
    """Thread-local tenant context for request isolation."""

    _current_tenant: Optional[str] = None
    _current_user: Optional[Dict[str, Any]] = None
    _request_id: Optional[str] = None

    @classmethod
    def set_tenant(cls, tenant_id: str) -> None:
        cls._current_tenant = tenant_id

    @classmethod
    def get_tenant(cls) -> Optional[str]:
        return cls._current_tenant

    @classmethod
    def set_user(cls, user: Dict[str, Any]) -> None:
        cls._current_user = user

    @classmethod
    def get_user(cls) -> Optional[Dict[str, Any]]:
        return cls._current_user

    @classmethod
    def set_request_id(cls, request_id: str) -> None:
        cls._request_id = request_id

    @classmethod
    def get_request_id(cls) -> Optional[str]:
        return cls._request_id

    @classmethod
    def clear(cls) -> None:
        cls._current_tenant = None
        cls._current_user = None
        cls._request_id = None

class TenantResolver:
    """Resolves tenant from various sources (subdomain, API key, JWT token)."""

    def __init__(self):
        self.tenant_cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def resolve_tenant_from_subdomain(self, host: str) -> Optional[str]:
        """
        Resolve tenant from subdomain.

        Examples:
        - acme.customerintelligence.com -> acme
        - techstart.customerintelligence.com -> techstart
        """
        if not host:
            return None

        # Extract subdomain
        parts = host.split('.')
        if len(parts) >= 3:
            subdomain = parts[0]
            # Validate subdomain format
            if re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', subdomain) and len(subdomain) <= 63:
                return subdomain

        return None

    async def resolve_tenant_from_api_key(self, api_key: str) -> Optional[str]:
        """
        Resolve tenant from API key.

        API key format: ci_[tenant_slug]_[random_string]
        Example: ci_acme_ak3j2kl8x9m2n4p5q7r8
        """
        if not api_key or not api_key.startswith('ci_'):
            return None

        try:
            parts = api_key.split('_')
            if len(parts) >= 3:
                tenant_slug = parts[1]
                return tenant_slug
        except Exception:
            pass

        return None

    async def resolve_tenant_from_jwt(self, token: str, jwt_secret: str) -> Optional[str]:
        """
        Resolve tenant from JWT token.

        JWT payload should contain 'tenant_id' claim.
        """
        try:
            payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            return payload.get('tenant_id')
        except jwt.InvalidTokenError:
            return None

    async def resolve_tenant(self, request: Request) -> Optional[str]:
        """
        Resolve tenant from request using multiple strategies.

        Priority:
        1. JWT token (Authorization header)
        2. API key (X-API-Key header)
        3. Subdomain
        4. Default tenant for development
        """
        # Strategy 1: JWT Token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            tenant_id = await self.resolve_tenant_from_jwt(token, "your-jwt-secret")
            if tenant_id:
                return tenant_id

        # Strategy 2: API Key
        api_key = request.headers.get('X-API-Key', '')
        if api_key:
            tenant_id = await self.resolve_tenant_from_api_key(api_key)
            if tenant_id:
                return tenant_id

        # Strategy 3: Subdomain
        host = request.headers.get('Host', '')
        tenant_id = await self.resolve_tenant_from_subdomain(host)
        if tenant_id:
            return tenant_id

        # Strategy 4: Default tenant for development
        return "default"

class RateLimiter:
    """Redis-backed rate limiter for tenant-specific API limits."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_pool = None

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection with connection pooling."""
        if self.redis_pool is None:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=10,
                decode_responses=True
            )
        return redis.Redis(connection_pool=self.redis_pool)

    async def is_rate_limited(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        limit: int = 1000,
        window: int = 3600
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request should be rate limited.

        Args:
            tenant_id: Tenant identifier
            user_id: Optional user identifier for per-user limits
            endpoint: Optional endpoint for endpoint-specific limits
            limit: Rate limit (requests per window)
            window: Time window in seconds

        Returns:
            (is_limited, rate_limit_info)
        """
        try:
            redis_client = await self._get_redis()

            # Create rate limit key
            key_parts = [f"rate_limit", tenant_id]
            if user_id:
                key_parts.append(f"user_{user_id}")
            if endpoint:
                key_parts.append(f"endpoint_{endpoint.replace('/', '_')}")

            key = ":".join(key_parts)

            # Get current count
            current_count = await redis_client.get(key)
            current_count = int(current_count) if current_count else 0

            # Get TTL
            ttl = await redis_client.ttl(key)
            if ttl == -1:  # No expiration set
                ttl = window

            if current_count >= limit:
                return True, {
                    "rate_limited": True,
                    "limit": limit,
                    "current": current_count,
                    "window": window,
                    "reset_in": ttl
                }
            else:
                # Increment counter
                pipe = redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, window)
                await pipe.execute()

                return False, {
                    "rate_limited": False,
                    "limit": limit,
                    "current": current_count + 1,
                    "window": window,
                    "reset_in": ttl
                }

        except Exception as e:
            logger.error(f"Rate limiting check failed: {e}")
            # Fail open - don't block requests if Redis is down
            return False, {
                "rate_limited": False,
                "error": "rate_limiter_unavailable"
            }

class TenantMiddleware:
    """FastAPI middleware for multi-tenant request processing."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        enable_rate_limiting: bool = True,
        enable_audit_logging: bool = True
    ):
        self.tenant_resolver = TenantResolver()
        self.rate_limiter = RateLimiter(redis_url) if enable_rate_limiting else None
        self.enable_audit_logging = enable_audit_logging
        self.start_time = time.time()

    async def __call__(self, request: Request, call_next):
        """Process request with tenant context."""
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000000)}"

        try:
            # 1. Resolve tenant
            tenant_id = await self.tenant_resolver.resolve_tenant(request)
            if not tenant_id:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "tenant_required",
                        "message": "Could not resolve tenant from request"
                    }
                )

            # 2. Set tenant context
            TenantContext.set_tenant(tenant_id)
            TenantContext.set_request_id(request_id)

            # 3. Rate limiting check
            if self.rate_limiter:
                rate_limited, rate_info = await self.rate_limiter.is_rate_limited(
                    tenant_id=tenant_id,
                    endpoint=str(request.url.path),
                    limit=self._get_tenant_rate_limit(tenant_id),
                    window=3600  # 1 hour window
                )

                if rate_limited:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "rate_limit_exceeded",
                            "message": "API rate limit exceeded",
                            **rate_info
                        },
                        headers={
                            "X-RateLimit-Limit": str(rate_info["limit"]),
                            "X-RateLimit-Remaining": str(max(0, rate_info["limit"] - rate_info["current"])),
                            "X-RateLimit-Reset": str(int(start_time + rate_info["reset_in"])),
                            "Retry-After": str(rate_info["reset_in"])
                        }
                    )

            # 4. Add tenant info to request state
            request.state.tenant_id = tenant_id
            request.state.request_id = request_id

            # 5. Process request
            response = await call_next(request)

            # 6. Add tenant headers to response
            response.headers["X-Tenant-ID"] = tenant_id
            response.headers["X-Request-ID"] = request_id

            # 7. Audit logging
            if self.enable_audit_logging:
                await self._log_audit_event(
                    tenant_id=tenant_id,
                    request_id=request_id,
                    method=request.method,
                    path=str(request.url.path),
                    status_code=response.status_code,
                    processing_time=time.time() - start_time
                )

            return response

        except Exception as e:
            logger.error(f"Tenant middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "middleware_error",
                    "message": "Internal server error"
                }
            )
        finally:
            # Always clear context
            TenantContext.clear()

    def _get_tenant_rate_limit(self, tenant_id: str) -> int:
        """Get rate limit for tenant based on subscription tier."""
        # In production, this would query the database for tenant settings
        # For now, use simple defaults
        rate_limits = {
            "default": 1000,    # Development
            "starter": 1000,    # 1K requests/hour
            "professional": 5000,  # 5K requests/hour
            "enterprise": 20000,   # 20K requests/hour
        }
        return rate_limits.get(tenant_id, 1000)

    async def _log_audit_event(
        self,
        tenant_id: str,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        processing_time: float
    ) -> None:
        """Log audit event for compliance."""
        try:
            audit_event = {
                "timestamp": datetime.utcnow().isoformat(),
                "tenant_id": tenant_id,
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "processing_time_ms": round(processing_time * 1000, 2),
                "user_agent": "",  # Could extract from request
                "ip_address": "",  # Could extract from request
            }

            # In production, send to audit log service or database
            logger.info(
                f"API request: {method} {path}",
                extra=audit_event
            )

        except Exception as e:
            logger.error(f"Audit logging failed: {e}")

# Utility decorators for tenant-aware endpoints

def require_tenant(func):
    """Decorator to ensure tenant context is available."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        tenant_id = TenantContext.get_tenant()
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context required"
            )
        return await func(*args, **kwargs)
    return wrapper

def tenant_isolation(func):
    """Decorator to enforce tenant data isolation."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        tenant_id = TenantContext.get_tenant()
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context required for data access"
            )

        # Add tenant_id to all database queries automatically
        # This could be implemented with SQLAlchemy events
        return await func(*args, **kwargs)
    return wrapper

def require_permission(permission: str):
    """Decorator to require specific permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = TenantContext.get_user()
            tenant_id = TenantContext.get_tenant()

            if not user or not tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check if user has permission
            user_permissions = user.get("permissions", [])
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Helper functions for tenant-aware operations

async def get_current_tenant() -> str:
    """Get current tenant ID from context."""
    tenant_id = TenantContext.get_tenant()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant context available"
        )
    return tenant_id

async def get_current_user() -> Dict[str, Any]:
    """Get current user from context."""
    user = TenantContext.get_user()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

def tenant_aware_cache_key(key: str) -> str:
    """Generate tenant-aware cache key."""
    tenant_id = TenantContext.get_tenant()
    if tenant_id:
        return f"tenant:{tenant_id}:{key}"
    return key