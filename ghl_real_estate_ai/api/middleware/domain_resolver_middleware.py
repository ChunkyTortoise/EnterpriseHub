"""
Domain Resolver Middleware - Multi-Tenant Routing
Handles domain-based tenant resolution and routing for white-label deployments
in the $500K ARR platform.
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

import asyncpg
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.utils.async_utils import safe_create_task

logger = get_logger(__name__)


class TenantContext:
    """Tenant context information for request processing."""

    def __init__(self):
        self.agency_id: Optional[str] = None
        self.client_id: Optional[str] = None
        self.deployment_id: Optional[str] = None
        self.brand_config: Dict[str, Any] = {}
        self.feature_flags: Dict[str, bool] = {}
        self.routing_config: Dict[str, Any] = {}
        self.is_white_label: bool = False
        self.primary_domain: bool = True
        self.custom_domain: bool = False


class DomainResolverMiddleware(BaseHTTPMiddleware):
    """
    Middleware for resolving domains to tenant configurations and setting up
    multi-tenant context for white-label deployments.
    """

    def __init__(
        self, app: ASGIApp, db_pool: asyncpg.Pool, cache_service: CacheService, default_agency_id: Optional[str] = None
    ):
        """Initialize domain resolver middleware."""
        super().__init__(app)
        self.db_pool = db_pool
        self.cache = cache_service
        self.default_agency_id = default_agency_id or settings.get("DEFAULT_AGENCY_ID")

        # Configuration
        self.primary_domain = settings.get("PRIMARY_DOMAIN", "app.enterprisehub.com")
        self.enable_subdomain_routing = settings.get("ENABLE_SUBDOMAIN_ROUTING", True)
        self.force_https = settings.get("FORCE_HTTPS", True)

        # Performance settings
        self.cache_ttl = 3600  # 1 hour cache for domain resolution
        self.health_check_paths = {"/health", "/ping", "/.well-known/"}

        logger.info(f"Domain resolver middleware initialized with primary domain: {self.primary_domain}")

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request through domain resolution middleware."""

        start_time = time.time()

        try:
            # Skip domain resolution for health checks and static assets
            if self._should_skip_resolution(request):
                return await call_next(request)

            # Enforce HTTPS if configured
            if self.force_https and not self._is_secure_request(request):
                return self._redirect_to_https(request)

            # Resolve domain to tenant context
            tenant_context = await self._resolve_domain(request)

            # Set tenant context on request
            request.state.tenant = tenant_context

            # Add custom headers for debugging
            if settings.get("DEBUG", False):
                request.state.debug_info = {
                    "agency_id": tenant_context.agency_id,
                    "client_id": tenant_context.client_id,
                    "is_white_label": tenant_context.is_white_label,
                    "domain_resolution_time_ms": round((time.time() - start_time) * 1000, 2),
                }

            # Process request
            response = await call_next(request)

            # Add tenant-specific response headers
            await self._add_tenant_headers(response, tenant_context)

            # Log request for analytics (in background)
            if tenant_context.agency_id:
                await self._log_request_analytics(request, response, tenant_context, start_time)

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Domain resolver middleware error: {e}")

            # Return graceful fallback
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "message": "Failed to resolve domain configuration"},
            )

    async def _resolve_domain(self, request: Request) -> TenantContext:
        """Resolve domain to tenant context."""

        host = request.headers.get("host", "").lower()
        if not host:
            return await self._get_default_context()

        # Remove port if present
        domain_name = host.split(":")[0]

        # Check cache first
        cache_key = f"domain_resolution:{domain_name}"
        cached_context = await self.cache.get(cache_key)

        if cached_context:
            try:
                context_data = json.loads(cached_context)
                return self._dict_to_tenant_context(context_data)
            except Exception as e:
                logger.warning(f"Failed to parse cached domain context: {e}")

        # Resolve from database
        tenant_context = await self._resolve_from_database(domain_name)

        # Cache the result
        if tenant_context.agency_id:
            await self.cache.set(
                cache_key, json.dumps(self._tenant_context_to_dict(tenant_context)), ttl=self.cache_ttl
            )

        return tenant_context

    async def _resolve_from_database(self, domain_name: str) -> TenantContext:
        """Resolve domain from database."""

        try:
            async with self.db_pool.acquire() as conn:
                # Check domain routing cache first
                cached_routing = await conn.fetchrow(
                    """
                    SELECT agency_id, client_id, deployment_id, routing_config,
                           brand_config, feature_flags
                    FROM domain_routing_cache
                    WHERE domain_name = $1 AND expires_at > NOW()
                    """,
                    domain_name,
                )

                if cached_routing:
                    context = TenantContext()
                    context.agency_id = cached_routing["agency_id"]
                    context.client_id = cached_routing["client_id"]
                    context.deployment_id = cached_routing["deployment_id"]
                    context.routing_config = json.loads(cached_routing["routing_config"])
                    context.brand_config = json.loads(cached_routing["brand_config"] or "{}")
                    context.feature_flags = json.loads(cached_routing["feature_flags"] or "{}")
                    context.is_white_label = True
                    context.custom_domain = True
                    return context

                # Check domain configurations
                domain_config = await conn.fetchrow(
                    """
                    SELECT dc.agency_id, dc.client_id, dc.domain_type, dc.status,
                           dep.deployment_id, dep.enabled_modules, dep.module_configurations,
                           dep.rate_limit_requests_per_minute, dep.max_concurrent_users,
                           bc.config_id, bc.brand_name, bc.primary_color, bc.secondary_color,
                           bc.accent_color, bc.primary_font_family, bc.custom_css, bc.feature_flags
                    FROM domain_configurations dc
                    LEFT JOIN deployment_configurations dep ON dc.domain_id = dep.primary_domain_id
                    LEFT JOIN brand_configurations bc ON dep.brand_config_id = bc.config_id
                    WHERE dc.domain_name = $1 AND dc.status = 'active'
                    """,
                    domain_name,
                )

                if domain_config:
                    context = TenantContext()
                    context.agency_id = domain_config["agency_id"]
                    context.client_id = domain_config["client_id"]
                    context.deployment_id = domain_config["deployment_id"]
                    context.is_white_label = True
                    context.custom_domain = True

                    # Set routing configuration
                    context.routing_config = {
                        "modules": json.loads(domain_config["enabled_modules"] or "[]"),
                        "module_config": json.loads(domain_config["module_configurations"] or "{}"),
                        "rate_limit": domain_config["rate_limit_requests_per_minute"] or 1000,
                        "max_users": domain_config["max_concurrent_users"] or 100,
                    }

                    # Set brand configuration
                    if domain_config["config_id"]:
                        context.brand_config = {
                            "brand_name": domain_config["brand_name"],
                            "primary_color": domain_config["primary_color"],
                            "secondary_color": domain_config["secondary_color"],
                            "accent_color": domain_config["accent_color"],
                            "font_family": domain_config["primary_font_family"],
                            "custom_css": domain_config["custom_css"],
                        }

                    # Set feature flags
                    context.feature_flags = json.loads(domain_config["feature_flags"] or "{}")

                    # Update domain routing cache
                    await self._update_domain_routing_cache(domain_name, context)

                    return context

                # Check for subdomain routing
                if self.enable_subdomain_routing and self._is_subdomain_of_primary(domain_name):
                    return await self._resolve_subdomain_routing(domain_name)

                # Fallback to default
                return await self._get_default_context()

        except Exception as e:
            logger.error(f"Failed to resolve domain {domain_name} from database: {e}")
            return await self._get_default_context()

    async def _resolve_subdomain_routing(self, domain_name: str) -> TenantContext:
        """Resolve subdomain-based routing (e.g., agency.app.com or client.agency.app.com)."""

        parts = domain_name.split(".")
        if len(parts) < 3:  # Minimum: subdomain.app.com
            return await self._get_default_context()

        try:
            async with self.db_pool.acquire() as conn:
                if len(parts) == 3:
                    # Format: agency.app.com
                    agency_slug = parts[0]

                    agency_info = await conn.fetchrow(
                        """
                        SELECT agency_id, status
                        FROM agencies
                        WHERE agency_slug = $1 AND status = 'active'
                        """,
                        agency_slug,
                    )

                    if agency_info:
                        context = TenantContext()
                        context.agency_id = agency_info["agency_id"]
                        context.is_white_label = True
                        context.primary_domain = False
                        return context

                elif len(parts) == 4:
                    # Format: client.agency.app.com
                    client_slug = parts[0]
                    agency_slug = parts[1]

                    client_info = await conn.fetchrow(
                        """
                        SELECT ac.client_id, ac.agency_id, a.status
                        FROM agency_clients ac
                        JOIN agencies a ON ac.agency_id = a.agency_id
                        WHERE ac.client_slug = $1 AND a.agency_slug = $2
                        AND ac.is_active = true AND a.status = 'active'
                        """,
                        client_slug,
                        agency_slug,
                    )

                    if client_info:
                        context = TenantContext()
                        context.agency_id = client_info["agency_id"]
                        context.client_id = client_info["client_id"]
                        context.is_white_label = True
                        context.primary_domain = False
                        return context

            return await self._get_default_context()

        except Exception as e:
            logger.error(f"Failed to resolve subdomain routing for {domain_name}: {e}")
            return await self._get_default_context()

    async def _get_default_context(self) -> TenantContext:
        """Get default tenant context."""
        context = TenantContext()

        if self.default_agency_id:
            context.agency_id = self.default_agency_id

        context.is_white_label = False
        context.primary_domain = True
        context.feature_flags = {"advanced_analytics": True, "api_access": True, "custom_integrations": True}

        return context

    async def _update_domain_routing_cache(self, domain_name: str, context: TenantContext) -> None:
        """Update domain routing cache in database."""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO domain_routing_cache (
                        domain_name, agency_id, client_id, deployment_id,
                        routing_config, brand_config, feature_flags,
                        last_updated, expires_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (domain_name) DO UPDATE SET
                        routing_config = EXCLUDED.routing_config,
                        brand_config = EXCLUDED.brand_config,
                        feature_flags = EXCLUDED.feature_flags,
                        last_updated = EXCLUDED.last_updated,
                        expires_at = EXCLUDED.expires_at
                    """,
                    domain_name,
                    context.agency_id,
                    context.client_id,
                    context.deployment_id,
                    json.dumps(context.routing_config),
                    json.dumps(context.brand_config),
                    json.dumps(context.feature_flags),
                    datetime.utcnow(),
                    datetime.utcnow() + timedelta(hours=1),
                )
        except Exception as e:
            logger.warning(f"Failed to update domain routing cache: {e}")

    def _should_skip_resolution(self, request: Request) -> bool:
        """Check if request should skip domain resolution."""
        path = request.url.path.lower()

        # Skip health checks
        if any(path.startswith(health_path) for health_path in self.health_check_paths):
            return True

        # Skip static assets
        if path.startswith("/static/") or path.startswith("/assets/"):
            return True

        # Skip API docs
        if path in ["/docs", "/redoc", "/openapi.json"]:
            return True

        return False

    def _is_secure_request(self, request: Request) -> bool:
        """Check if request is using HTTPS."""
        # Check direct HTTPS
        if request.url.scheme == "https":
            return True

        # Check forwarded headers (for load balancers)
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto and forwarded_proto.lower() == "https":
            return True

        return False

    def _redirect_to_https(self, request: Request) -> RedirectResponse:
        """Redirect HTTP request to HTTPS."""
        https_url = request.url.replace(scheme="https")
        return RedirectResponse(url=str(https_url), status_code=301)

    def _is_subdomain_of_primary(self, domain_name: str) -> bool:
        """Check if domain is a subdomain of the primary domain."""
        return domain_name.endswith(f".{self.primary_domain}")

    async def _add_tenant_headers(self, response: Response, tenant_context: TenantContext) -> None:
        """Add tenant-specific headers to response."""
        if tenant_context.is_white_label:
            response.headers["X-Tenant-Type"] = "white-label"
            if tenant_context.agency_id:
                response.headers["X-Agency-ID"] = tenant_context.agency_id
            if tenant_context.client_id:
                response.headers["X-Client-ID"] = tenant_context.client_id
        else:
            response.headers["X-Tenant-Type"] = "primary"

        # Add security headers for white-label deployments
        if tenant_context.custom_domain:
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    async def _log_request_analytics(
        self, request: Request, response: Response, tenant_context: TenantContext, start_time: float
    ) -> None:
        """Log request analytics for tenant."""
        try:
            # Calculate response time
            response_time = round((time.time() - start_time) * 1000, 2)

            # Prepare analytics data
            analytics_data = {
                "agency_id": tenant_context.agency_id,
                "client_id": tenant_context.client_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "user_agent": request.headers.get("user-agent", ""),
                "ip_address": self._get_client_ip(request),
                "domain": request.headers.get("host", ""),
                "is_white_label": tenant_context.is_white_label,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Log to analytics system (async, non-blocking)
            safe_create_task(self._store_analytics_data(analytics_data))

        except Exception as e:
            logger.warning(f"Failed to log request analytics: {e}")

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check forwarded headers first (for load balancers)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct connection
        return request.client.host if request.client else "unknown"

    async def _store_analytics_data(self, analytics_data: Dict[str, Any]) -> None:
        """Store analytics data in database."""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO platform_analytics (
                        metric_id, agency_id, client_id, metric_type, metric_name,
                        metric_value, metric_unit, time_bucket, granularity,
                        segment_dimensions, source_domain, analytics_metadata
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                    )
                    """,
                    f"req_{uuid.uuid4().hex}",
                    analytics_data["agency_id"],
                    analytics_data["client_id"],
                    "http_request",
                    f"{analytics_data['method']} {analytics_data['path']}",
                    analytics_data["response_time_ms"],
                    "milliseconds",
                    datetime.utcnow().replace(minute=0, second=0, microsecond=0),  # Hourly bucket
                    "hour",
                    json.dumps(
                        {
                            "method": analytics_data["method"],
                            "status_code": analytics_data["status_code"],
                            "user_agent": analytics_data["user_agent"][:100],  # Truncate
                            "ip_address": analytics_data["ip_address"],
                        }
                    ),
                    analytics_data["domain"],
                    json.dumps(analytics_data),
                )
        except Exception as e:
            logger.warning(f"Failed to store analytics data: {e}")

    def _tenant_context_to_dict(self, context: TenantContext) -> Dict[str, Any]:
        """Convert TenantContext to dictionary for caching."""
        return {
            "agency_id": context.agency_id,
            "client_id": context.client_id,
            "deployment_id": context.deployment_id,
            "brand_config": context.brand_config,
            "feature_flags": context.feature_flags,
            "routing_config": context.routing_config,
            "is_white_label": context.is_white_label,
            "primary_domain": context.primary_domain,
            "custom_domain": context.custom_domain,
        }

    def _dict_to_tenant_context(self, data: Dict[str, Any]) -> TenantContext:
        """Convert dictionary to TenantContext."""
        context = TenantContext()
        context.agency_id = data.get("agency_id")
        context.client_id = data.get("client_id")
        context.deployment_id = data.get("deployment_id")
        context.brand_config = data.get("brand_config", {})
        context.feature_flags = data.get("feature_flags", {})
        context.routing_config = data.get("routing_config", {})
        context.is_white_label = data.get("is_white_label", False)
        context.primary_domain = data.get("primary_domain", True)
        context.custom_domain = data.get("custom_domain", False)
        return context


# Utility functions for use in route handlers


def get_tenant_context(request: Request) -> TenantContext:
    """Get tenant context from request state."""
    return getattr(request.state, "tenant", TenantContext())


def require_agency_context(request: Request) -> str:
    """Require agency context and return agency_id."""
    tenant = get_tenant_context(request)
    if not tenant.agency_id:
        raise HTTPException(status_code=403, detail="Agency context required for this operation")
    return tenant.agency_id


def require_client_context(request: Request) -> Tuple[str, str]:
    """Require client context and return (agency_id, client_id)."""
    tenant = get_tenant_context(request)
    if not tenant.agency_id or not tenant.client_id:
        raise HTTPException(status_code=403, detail="Client context required for this operation")
    return tenant.agency_id, tenant.client_id


def has_feature_flag(request: Request, flag_name: str) -> bool:
    """Check if feature flag is enabled for current tenant."""
    tenant = get_tenant_context(request)
    return tenant.feature_flags.get(flag_name, False)


def get_brand_config(request: Request) -> Dict[str, Any]:
    """Get brand configuration for current tenant."""
    tenant = get_tenant_context(request)
    return tenant.brand_config


def is_white_label_request(request: Request) -> bool:
    """Check if request is from a white-label deployment."""
    tenant = get_tenant_context(request)
    return tenant.is_white_label
