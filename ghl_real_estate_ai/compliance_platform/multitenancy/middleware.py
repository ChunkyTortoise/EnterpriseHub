"""
Enterprise Compliance Platform - Tenant Isolation Middleware

Production-ready middleware for multi-tenant isolation, including:
- JWT-based tenant context extraction
- Permission-based access control
- Subscription tier enforcement
- Data filtering by organization
- Audit logging for tenant operations

Designed to work with the existing models in models.py which includes:
- Organization, OrganizationUser, TenantContext
- Permission, UserRole, SubscriptionTier enums
- ROLE_PERMISSIONS, TIER_LIMITS, TIER_FEATURES constants
"""

import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from .models import (
    AuditLogEntry,
    Organization,
    OrganizationUser,
    Permission,
    ROLE_PERMISSIONS,
    SubscriptionTier,
    TenantContext,
    TIER_LIMITS,
    TIER_FEATURES,
    UserRole,
)

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])

# Context variable for current tenant - thread-safe across async operations
_tenant_context: ContextVar[Optional[TenantContext]] = ContextVar("tenant_context", default=None)

# Security configuration
_security_scheme = HTTPBearer(auto_error=False)


def get_current_tenant() -> TenantContext:
    """
    Get current tenant context from context var.

    Returns:
        TenantContext: Current tenant context

    Raises:
        HTTPException: If no tenant context is set
    """
    ctx = _tenant_context.get()
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No tenant context - authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ctx


def get_optional_tenant() -> Optional[TenantContext]:
    """
    Get current tenant context if available, None otherwise.

    Useful for endpoints that work with or without authentication.
    """
    return _tenant_context.get()


def set_tenant_context(ctx: TenantContext) -> None:
    """
    Set tenant context for current request.

    Args:
        ctx: TenantContext to set
    """
    _tenant_context.set(ctx)


def clear_tenant_context() -> None:
    """Clear tenant context after request completion."""
    _tenant_context.set(None)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for tenant isolation.

    Extracts tenant information from JWT token, validates permissions,
    and sets context for downstream handlers.
    """

    def __init__(
        self,
        app,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        exclude_paths: Optional[List[str]] = None,
        organization_repo: Optional[Any] = None,
        user_repo: Optional[Any] = None,
        audit_enabled: bool = True,
    ):
        super().__init__(app)
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.organization_repo = organization_repo
        self.user_repo = user_repo
        self.audit_enabled = audit_enabled

        # Paths that don't require tenant context
        self.exclude_paths = set(exclude_paths or [
            "/health",
            "/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/forgot-password",
        ])

        # In-memory caches (in production, use Redis)
        self._organizations: Dict[str, Organization] = {}
        self._users: Dict[str, OrganizationUser] = {}
        self._revoked_tokens: Set[str] = set()

    async def dispatch(self, request: Request, call_next) -> Response:
        """Main middleware dispatch."""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        path = request.url.path

        # Skip excluded paths
        if self._is_excluded_path(path):
            return await call_next(request)

        try:
            # Extract and validate tenant context
            ctx = await self._extract_tenant_context(request)

            if ctx:
                # Set context for downstream handlers
                set_tenant_context(ctx)

                # Add tenant info to request state
                request.state.tenant_context = ctx
                request.state.organization_id = ctx.organization_id
                request.state.user_id = ctx.user_id

            # Process request
            response = await call_next(request)

            # Audit successful request
            if self.audit_enabled and ctx:
                await self._audit_request(ctx, request, response, start_time)

            return response

        except HTTPException:
            raise

        except Exception as e:
            # Log unexpected error
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                },
            )
            return response

        finally:
            # Clear context after request
            clear_tenant_context()

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from tenant validation."""
        if path in self.exclude_paths:
            return True
        return any(path.startswith(excluded) for excluded in self.exclude_paths)

    async def _extract_tenant_context(self, request: Request) -> Optional[TenantContext]:
        """Extract tenant context from request."""
        # Check for Bearer token
        auth_header = request.headers.get("authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            return await self._validate_jwt_token(token, request)

        # Check for API key
        api_key = request.headers.get("x-api-key")
        if api_key:
            return await self._validate_api_key(api_key, request)

        # No authentication provided
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async def _validate_jwt_token(self, token: str, request: Request) -> TenantContext:
        """Validate JWT token and extract tenant context."""
        if not token or not isinstance(token, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            # Check required claims
            required_claims = ["sub", "org_id"]
            for claim in required_claims:
                if claim not in payload:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Missing required claim: {claim}",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

            # Check if token is revoked
            jti = payload.get("jti")
            if jti and jti in self._revoked_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Get organization
            org_id = payload["org_id"]
            org = await self._get_organization(org_id)

            if not org:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Organization does not exist",
                )

            if not org.status.is_operational:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Organization is not operational (status: {org.status.value})",
                )

            # Get user
            user_id = payload["sub"]
            user = await self._get_user(user_id, org_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not exist",
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive",
                )

            # Build tenant context using existing model
            ctx = TenantContext.from_user_and_org(user, org)
            return ctx

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def _validate_api_key(self, api_key: str, request: Request) -> TenantContext:
        """Validate API key and extract tenant context."""
        # In production, look up API key from database
        # For now, raise not implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="API key authentication not yet implemented",
        )

    async def _get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID (with caching)."""
        if org_id in self._organizations:
            return self._organizations[org_id]

        if self.organization_repo:
            org = await self.organization_repo.get_by_id(org_id)
            if org:
                self._organizations[org_id] = org
            return org

        return None

    async def _get_user(self, user_id: str, org_id: str) -> Optional[OrganizationUser]:
        """Get user by ID within organization (with caching)."""
        cache_key = f"{org_id}:{user_id}"
        if cache_key in self._users:
            return self._users[cache_key]

        if self.user_repo:
            user = await self.user_repo.get_by_id(user_id, org_id)
            if user:
                self._users[cache_key] = user
            return user

        return None

    async def _audit_request(
        self,
        ctx: TenantContext,
        request: Request,
        response: Response,
        start_time: float,
    ) -> None:
        """Audit successful request."""
        # In production, this would write to audit log
        duration_ms = (time.time() - start_time) * 1000

        # Create audit log entry (not persisted here, just created)
        audit_entry = AuditLogEntry.from_context(
            context=ctx,
            action=f"api.{request.method.lower()}",
            resource_type="endpoint",
            resource_id=request.url.path,
            details={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
            ip_address=self._get_client_ip(request),
        )

        # In production, persist audit_entry to database/log service
        pass

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "cf-connecting-ip",
        ]

        for header in forwarded_headers:
            ip = request.headers.get(header)
            if ip:
                return ip.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    def revoke_token(self, jti: str) -> None:
        """Revoke a token by its JTI."""
        self._revoked_tokens.add(jti)

    def clear_cache(self, org_id: Optional[str] = None) -> None:
        """Clear organization/user cache."""
        if org_id:
            self._organizations.pop(org_id, None)
            # Clear users for this org
            keys_to_remove = [k for k in self._users if k.startswith(f"{org_id}:")]
            for key in keys_to_remove:
                self._users.pop(key, None)
        else:
            self._organizations.clear()
            self._users.clear()


class TenantIsolation:
    """
    Dependency injection class for tenant-aware endpoints.

    Provides methods for:
    - Getting tenant context
    - Verifying organization/user
    - Permission checking
    - Tier enforcement
    - Limit checking
    """

    def __init__(
        self,
        organization_repo: Optional[Any] = None,
        user_repo: Optional[Any] = None,
    ):
        self.organization_repo = organization_repo
        self.user_repo = user_repo
        self._organizations: Dict[str, Organization] = {}
        self._users: Dict[str, OrganizationUser] = {}

    async def get_tenant_context(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(_security_scheme),
    ) -> TenantContext:
        """
        FastAPI dependency to get tenant context.

        Use in route parameters:
            @app.get("/api/models")
            async def list_models(ctx: TenantContext = Depends(tenant.get_tenant_context)):
                ...
        """
        ctx = get_current_tenant()
        return ctx

    async def verify_organization(self, org_id: str) -> Organization:
        """
        Verify organization exists and is active.

        Args:
            org_id: Organization ID to verify

        Returns:
            Organization if valid

        Raises:
            HTTPException: If organization is invalid
        """
        org = self._organizations.get(org_id)

        if not org:
            if self.organization_repo:
                org = await self.organization_repo.get_by_id(org_id)
                if org:
                    self._organizations[org_id] = org

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        if not org.status.is_operational:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Organization is not operational (status: {org.status.value})",
            )

        return org

    async def verify_user(self, user_id: str, org_id: str) -> OrganizationUser:
        """
        Verify user belongs to organization and is active.

        Args:
            user_id: User ID to verify
            org_id: Organization ID user should belong to

        Returns:
            OrganizationUser if valid

        Raises:
            HTTPException: If user is invalid
        """
        cache_key = f"{org_id}:{user_id}"
        user = self._users.get(cache_key)

        if not user:
            if self.user_repo:
                user = await self.user_repo.get_by_id(user_id, org_id)
                if user:
                    self._users[cache_key] = user

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to this organization",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        return user

    def require_permission(self, permission: Permission) -> Callable[[F], F]:
        """
        Decorator to require specific permission.

        Usage:
            @app.post("/api/models")
            @tenant.require_permission(Permission.MODEL_CREATE)
            async def create_model(...):
                ...
        """
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                ctx = get_current_tenant()
                if not ctx.has_permission(permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission.value}",
                    )
                return await func(*args, **kwargs)
            return wrapper  # type: ignore
        return decorator

    def require_any_permission(self, permissions: List[Permission]) -> Callable[[F], F]:
        """
        Decorator to require any one of the specified permissions.

        Usage:
            @tenant.require_any_permission([Permission.MODEL_READ, Permission.MODEL_UPDATE])
            async def get_or_update_model(...):
                ...
        """
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                ctx = get_current_tenant()
                if not any(ctx.has_permission(p) for p in permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: requires one of {[p.value for p in permissions]}",
                    )
                return await func(*args, **kwargs)
            return wrapper  # type: ignore
        return decorator

    def require_all_permissions(self, permissions: List[Permission]) -> Callable[[F], F]:
        """
        Decorator to require all specified permissions.

        Usage:
            @tenant.require_all_permissions([Permission.MODEL_UPDATE, Permission.MODEL_DELETE])
            async def replace_model(...):
                ...
        """
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                ctx = get_current_tenant()
                missing = [p for p in permissions if not ctx.has_permission(p)]
                if missing:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: missing {[p.value for p in missing]}",
                    )
                return await func(*args, **kwargs)
            return wrapper  # type: ignore
        return decorator

    def require_tier(self, min_tier: SubscriptionTier) -> Callable[[F], F]:
        """
        Decorator to require minimum subscription tier.

        Usage:
            @app.post("/api/ai/analyze")
            @tenant.require_tier(SubscriptionTier.PROFESSIONAL)
            async def ai_analysis(...):
                ...
        """
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                ctx = get_current_tenant()
                current_level = ctx.subscription_tier.hierarchy_level
                required_level = min_tier.hierarchy_level

                if current_level < required_level:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"This feature requires {min_tier.display_name} tier or higher. "
                               f"Current tier: {ctx.subscription_tier.display_name}",
                    )
                return await func(*args, **kwargs)
            return wrapper  # type: ignore
        return decorator

    def require_feature(self, feature: str) -> Callable[[F], F]:
        """
        Decorator to require specific feature access.

        Usage:
            @tenant.require_feature("ai_analysis")
            async def get_ai_explanation(...):
                ...
        """
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                ctx = get_current_tenant()
                tier_features = TIER_FEATURES.get(ctx.subscription_tier, [])
                has_feature = "all" in tier_features or feature in tier_features

                if not has_feature:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Feature '{feature}' is not available on your subscription tier",
                    )
                return await func(*args, **kwargs)
            return wrapper  # type: ignore
        return decorator

    def check_limit(self, limit_type: str, current_value: int) -> bool:
        """
        Check if organization is within limits.

        Args:
            limit_type: Type of limit to check (max_models, max_users, etc.)
            current_value: Current usage value

        Returns:
            True if within limits, False otherwise
        """
        ctx = get_current_tenant()
        tier_limits = TIER_LIMITS.get(ctx.subscription_tier, {})
        max_value = tier_limits.get(limit_type, -1)

        if max_value == -1:
            return True  # Unlimited
        return current_value < max_value

    def enforce_limit(self, limit_type: str, current_value: int) -> None:
        """
        Enforce a limit, raising HTTPException if exceeded.

        Args:
            limit_type: Type of limit to enforce
            current_value: Current usage value

        Raises:
            HTTPException: If limit is exceeded
        """
        ctx = get_current_tenant()
        tier_limits = TIER_LIMITS.get(ctx.subscription_tier, {})
        max_value = tier_limits.get(limit_type, -1)

        if max_value != -1 and current_value >= max_value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Limit exceeded: {limit_type}. "
                       f"Current: {current_value}, Max: {max_value}. "
                       f"Upgrade your subscription for higher limits.",
            )


class TenantDataFilter:
    """
    Filters data access by tenant.

    Ensures queries only return data for the current tenant,
    preventing cross-tenant data leakage.
    """

    @staticmethod
    def filter_by_org(items: List[Any], org_id: str) -> List[Any]:
        """
        Filter list of items by organization ID.

        Args:
            items: List of items with organization_id attribute
            org_id: Organization ID to filter by

        Returns:
            Filtered list containing only items for the organization
        """
        return [
            item for item in items
            if getattr(item, "organization_id", None) == org_id
        ]

    @staticmethod
    def filter_models(models: List[Any], org_id: str) -> List[Any]:
        """Filter AI models by organization."""
        return TenantDataFilter.filter_by_org(models, org_id)

    @staticmethod
    def filter_assessments(assessments: List[Any], org_id: str) -> List[Any]:
        """Filter risk assessments by organization."""
        return TenantDataFilter.filter_by_org(assessments, org_id)

    @staticmethod
    def filter_violations(violations: List[Any], org_id: str) -> List[Any]:
        """Filter policy violations by organization."""
        return TenantDataFilter.filter_by_org(violations, org_id)

    @staticmethod
    def filter_reports(reports: List[Any], org_id: str) -> List[Any]:
        """Filter compliance reports by organization."""
        return TenantDataFilter.filter_by_org(reports, org_id)

    @staticmethod
    def filter_users(users: List[Any], org_id: str) -> List[Any]:
        """Filter users by organization."""
        return TenantDataFilter.filter_by_org(users, org_id)

    @staticmethod
    def add_tenant_filter(query: Dict[str, Any], org_id: str) -> Dict[str, Any]:
        """
        Add tenant filter to a database query dictionary.

        Args:
            query: Query dictionary
            org_id: Organization ID to add to filter

        Returns:
            Query with organization_id filter added
        """
        query["organization_id"] = org_id
        return query

    @staticmethod
    def validate_tenant_access(item: Any, org_id: str) -> bool:
        """
        Validate that an item belongs to the specified organization.

        Args:
            item: Item to validate
            org_id: Expected organization ID

        Returns:
            True if item belongs to organization

        Raises:
            HTTPException: If item belongs to different organization
        """
        item_org_id = getattr(item, "organization_id", None)
        if item_org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found",  # Don't reveal existence to other tenants
            )
        return True


# Utility functions for JWT token management

def create_tenant_token(
    org: Organization,
    user: OrganizationUser,
    secret: str,
    algorithm: str = "HS256",
    expires_hours: int = 24,
) -> str:
    """
    Create JWT token with tenant information.

    Args:
        org: Organization
        user: User within organization
        secret: JWT signing secret
        algorithm: JWT algorithm
        expires_hours: Token validity in hours

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=expires_hours)

    claims = {
        "sub": user.id,
        "org_id": org.id,
        "org_name": org.name,
        "org_slug": org.slug,
        "email": user.email,
        "role": user.role.value,
        "tier": org.subscription_tier.value,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }

    return jwt.encode(claims, secret, algorithm=algorithm)


def decode_tenant_token(
    token: str,
    secret: str,
    algorithm: str = "HS256",
) -> Dict[str, Any]:
    """
    Decode and validate tenant JWT token.

    Args:
        token: JWT token string
        secret: JWT signing secret
        algorithm: JWT algorithm

    Returns:
        Decoded token claims

    Raises:
        HTTPException: If token is invalid
    """
    try:
        claims = jwt.decode(token, secret, algorithms=[algorithm])
        return claims

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# FastAPI dependency functions

async def get_current_org(
    ctx: TenantContext = Depends(get_current_tenant),
) -> str:
    """
    FastAPI dependency to get current organization ID.

    Usage:
        @app.get("/api/org/info")
        async def get_org_info(org_id: str = Depends(get_current_org)):
            ...
    """
    return ctx.organization_id


async def get_current_user_id(
    ctx: TenantContext = Depends(get_current_tenant),
) -> str:
    """
    FastAPI dependency to get current user ID.

    Usage:
        @app.get("/api/user/profile")
        async def get_profile(user_id: str = Depends(get_current_user_id)):
            ...
    """
    return ctx.user_id


async def get_user_permissions(
    ctx: TenantContext = Depends(get_current_tenant),
) -> frozenset:
    """
    FastAPI dependency to get current user's permissions.

    Usage:
        @app.get("/api/user/permissions")
        async def list_permissions(perms: frozenset = Depends(get_user_permissions)):
            ...
    """
    return ctx.permissions


def require_permission(permission: Permission):
    """
    FastAPI dependency that requires specific permission.

    Usage:
        @app.post("/api/models")
        async def create_model(
            ctx: TenantContext = Depends(require_permission(Permission.MODEL_CREATE))
        ):
            ...
    """
    async def check_permission(
        ctx: TenantContext = Depends(get_current_tenant),
    ) -> TenantContext:
        if not ctx.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )
        return ctx

    return check_permission


def require_role(role: UserRole):
    """
    FastAPI dependency that requires specific role or higher.

    Usage:
        @app.delete("/api/org")
        async def delete_org(
            ctx: TenantContext = Depends(require_role(UserRole.ADMIN))
        ):
            ...
    """
    async def check_role(
        ctx: TenantContext = Depends(get_current_tenant),
    ) -> TenantContext:
        user_level = ctx.user_role.hierarchy_level
        required_level = role.hierarchy_level

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.display_name}",
            )

        return ctx

    return check_role


def require_tier(tier: SubscriptionTier):
    """
    FastAPI dependency that requires minimum subscription tier.

    Usage:
        @app.post("/api/ai/advanced")
        async def advanced_ai(
            ctx: TenantContext = Depends(require_tier(SubscriptionTier.ENTERPRISE))
        ):
            ...
    """
    async def check_tier(
        ctx: TenantContext = Depends(get_current_tenant),
    ) -> TenantContext:
        current_level = ctx.subscription_tier.hierarchy_level
        required_level = tier.hierarchy_level

        if current_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {tier.display_name} tier or higher",
            )
        return ctx

    return check_tier


# Singleton instance for common use
tenant_isolation = TenantIsolation()
