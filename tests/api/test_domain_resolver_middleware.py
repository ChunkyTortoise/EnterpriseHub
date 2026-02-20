import pytest

pytestmark = pytest.mark.integration

"""
Tests for Domain Resolver Middleware
Validates multi-tenant routing and domain resolution functionality
for the white-label platform.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from starlette.responses import Response

from ghl_real_estate_ai.api.middleware.domain_resolver_middleware import (
    DomainResolverMiddleware,
    TenantContext,
    get_brand_config,
    get_tenant_context,
    has_feature_flag,
    is_white_label_request,
    require_agency_context,
    require_client_context,
)
from ghl_real_estate_ai.services.cache_service import CacheService


@pytest.fixture
async def mock_db_pool():
    """Mock database pool."""
    pool = AsyncMock(spec=asyncpg.Pool)
    return pool


@pytest.fixture
async def mock_cache_service():
    """Mock cache service."""
    cache = AsyncMock(spec=CacheService)
    cache.get.return_value = None  # Default to cache miss
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


@pytest.fixture
def sample_tenant_context():
    """Sample tenant context for testing."""
    context = TenantContext()
    context.agency_id = "agency_001"
    context.client_id = "client_001"
    context.deployment_id = "deployment_001"
    context.is_white_label = True
    context.custom_domain = True
    context.brand_config = {"brand_name": "Test Agency", "primary_color": "#6D28D9", "secondary_color": "#4C1D95"}
    context.feature_flags = {"advanced_analytics": True, "api_access": True, "custom_integrations": False}
    context.routing_config = {"modules": ["leads", "analytics"], "rate_limit": 1000, "max_users": 100}
    return context


@pytest.fixture
def app_with_middleware(mock_db_pool, mock_cache_service):
    """Create FastAPI app with domain resolver middleware."""
    app = FastAPI()

    # Add middleware
    middleware = DomainResolverMiddleware(
        app=app, db_pool=mock_db_pool, cache_service=mock_cache_service, default_agency_id="default_agency"
    )

    app.add_middleware(DomainResolverMiddleware, db_pool=mock_db_pool, cache_service=mock_cache_service)

    # Add test routes
    @app.get("/test")
    async def test_route(request: Request):
        tenant = get_tenant_context(request)
        return {
            "agency_id": tenant.agency_id,
            "client_id": tenant.client_id,
            "is_white_label": tenant.is_white_label,
            "brand_config": tenant.brand_config,
            "feature_flags": tenant.feature_flags,
        }

    @app.get("/agency-required")
    async def agency_required_route(request: Request):
        agency_id = require_agency_context(request)
        return {"agency_id": agency_id}

    @app.get("/client-required")
    async def client_required_route(request: Request):
        agency_id, client_id = require_client_context(request)
        return {"agency_id": agency_id, "client_id": client_id}

    @app.get("/feature-check")
    async def feature_check_route(request: Request):
        has_analytics = has_feature_flag(request, "advanced_analytics")
        has_custom = has_feature_flag(request, "custom_integrations")
        return {"has_analytics": has_analytics, "has_custom": has_custom}

    return app, middleware


class TestDomainResolverMiddleware:
    """Test suite for domain resolver middleware."""

    async def test_middleware_initialization(self, mock_db_pool, mock_cache_service):
        """Test middleware initialization."""
        middleware = DomainResolverMiddleware(
            app=MagicMock(), db_pool=mock_db_pool, cache_service=mock_cache_service, default_agency_id="default_agency"
        )

        assert middleware.db_pool == mock_db_pool
        assert middleware.cache == mock_cache_service
        assert middleware.default_agency_id == "default_agency"
        assert middleware.primary_domain == "app.enterprisehub.com"
        assert middleware.enable_subdomain_routing is True

    async def test_resolve_custom_domain_from_cache(self, mock_cache_service, sample_tenant_context):
        """Test domain resolution from cache."""
        app, middleware = app_with_middleware(mock_db_pool=MagicMock(), mock_cache_service=mock_cache_service)

        # Mock cache hit
        cached_data = json.dumps(
            {
                "agency_id": "agency_001",
                "client_id": "client_001",
                "deployment_id": "deployment_001",
                "brand_config": {"brand_name": "Test Agency"},
                "feature_flags": {"advanced_analytics": True},
                "routing_config": {"modules": ["leads"]},
                "is_white_label": True,
                "primary_domain": False,
                "custom_domain": True,
            }
        )
        mock_cache_service.get.return_value = cached_data

        # Mock request
        request = MagicMock()
        request.headers = {"host": "custom.example.com"}

        context = await middleware._resolve_domain(request)

        assert context.agency_id == "agency_001"
        assert context.client_id == "client_001"
        assert context.is_white_label is True
        assert context.custom_domain is True
        mock_cache_service.get.assert_called_once_with("domain_resolution:custom.example.com")

    async def test_resolve_custom_domain_from_database(self, mock_db_pool, mock_cache_service):
        """Test domain resolution from database when cache miss."""
        app, middleware = app_with_middleware(mock_db_pool=mock_db_pool, mock_cache_service=mock_cache_service)

        # Mock cache miss
        mock_cache_service.get.return_value = None

        # Mock database response
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock

        # Mock domain routing cache hit
        cached_routing = {
            "agency_id": "agency_001",
            "client_id": "client_001",
            "deployment_id": "deployment_001",
            "routing_config": '{"modules": ["leads", "analytics"]}',
            "brand_config": '{"brand_name": "Test Agency", "primary_color": "#6D28D9"}',
            "feature_flags": '{"advanced_analytics": true}',
        }
        conn_mock.fetchrow.return_value = cached_routing

        # Mock request
        request = MagicMock()
        request.headers = {"host": "custom.example.com"}

        context = await middleware._resolve_domain(request)

        assert context.agency_id == "agency_001"
        assert context.client_id == "client_001"
        assert context.is_white_label is True
        assert context.custom_domain is True
        assert context.brand_config["brand_name"] == "Test Agency"
        assert context.feature_flags["advanced_analytics"] is True

    async def test_resolve_subdomain_agency_level(self, mock_db_pool, mock_cache_service):
        """Test subdomain resolution for agency-level domain."""
        app, middleware = app_with_middleware(mock_db_pool=mock_db_pool, mock_cache_service=mock_cache_service)

        # Mock cache miss
        mock_cache_service.get.return_value = None

        # Mock database responses
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock

        # No domain configuration found, but agency exists via subdomain
        conn_mock.fetchrow.side_effect = [
            None,  # No domain routing cache
            None,  # No domain configuration
            {"agency_id": "agency_001", "status": "active"},  # Agency exists
        ]

        # Mock request with agency subdomain
        request = MagicMock()
        request.headers = {"host": "test-agency.app.enterprisehub.com"}

        context = await middleware._resolve_domain(request)

        assert context.agency_id == "agency_001"
        assert context.client_id is None
        assert context.is_white_label is True
        assert context.primary_domain is False

    async def test_resolve_subdomain_client_level(self, mock_db_pool, mock_cache_service):
        """Test subdomain resolution for client-level domain."""
        app, middleware = app_with_middleware(mock_db_pool=mock_db_pool, mock_cache_service=mock_cache_service)

        # Mock cache miss
        mock_cache_service.get.return_value = None

        # Mock database responses
        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock

        # No domain configuration found, but client exists via subdomain
        conn_mock.fetchrow.side_effect = [
            None,  # No domain routing cache
            None,  # No domain configuration
            {"client_id": "client_001", "agency_id": "agency_001", "status": "active"},  # Client exists
        ]

        # Mock request with client subdomain
        request = MagicMock()
        request.headers = {"host": "test-client.test-agency.app.enterprisehub.com"}

        context = await middleware._resolve_domain(request)

        assert context.agency_id == "agency_001"
        assert context.client_id == "client_001"
        assert context.is_white_label is True
        assert context.primary_domain is False

    async def test_resolve_default_context(self, mock_db_pool, mock_cache_service):
        """Test fallback to default context."""
        app, middleware = app_with_middleware(mock_db_pool=mock_db_pool, mock_cache_service=mock_cache_service)

        # Mock cache miss and no database matches
        mock_cache_service.get.return_value = None

        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock
        conn_mock.fetchrow.return_value = None

        # Mock request with unknown domain
        request = MagicMock()
        request.headers = {"host": "unknown.example.com"}

        context = await middleware._resolve_domain(request)

        assert context.agency_id == "default_agency"  # Uses default from middleware
        assert context.is_white_label is False
        assert context.primary_domain is True

    async def test_should_skip_resolution(self):
        """Test request path skipping logic."""
        app, middleware = app_with_middleware(mock_db_pool=MagicMock(), mock_cache_service=MagicMock())

        # Health check paths should be skipped
        health_request = MagicMock()
        health_request.url.path.lower.return_value = "/health"
        assert middleware._should_skip_resolution(health_request) is True

        # Static assets should be skipped
        static_request = MagicMock()
        static_request.url.path.lower.return_value = "/static/css/style.css"
        assert middleware._should_skip_resolution(static_request) is True

        # API docs should be skipped
        docs_request = MagicMock()
        docs_request.url.path.lower.return_value = "/docs"
        assert middleware._should_skip_resolution(docs_request) is True

        # Regular API paths should not be skipped
        api_request = MagicMock()
        api_request.url.path.lower.return_value = "/api/v1/leads"
        assert middleware._should_skip_resolution(api_request) is False

    async def test_https_enforcement(self):
        """Test HTTPS enforcement."""
        app, middleware = app_with_middleware(mock_db_pool=MagicMock(), mock_cache_service=MagicMock())
        middleware.force_https = True

        # HTTP request should be detected as insecure
        http_request = MagicMock()
        http_request.url.scheme = "http"
        http_request.headers = {}
        assert middleware._is_secure_request(http_request) is False

        # HTTPS request should be detected as secure
        https_request = MagicMock()
        https_request.url.scheme = "https"
        assert middleware._is_secure_request(https_request) is True

        # Request with X-Forwarded-Proto header should be detected as secure
        forwarded_request = MagicMock()
        forwarded_request.url.scheme = "http"
        forwarded_request.headers = {"x-forwarded-proto": "https"}
        assert middleware._is_secure_request(forwarded_request) is True

    async def test_https_redirect(self):
        """Test HTTPS redirect response."""
        app, middleware = app_with_middleware(mock_db_pool=MagicMock(), mock_cache_service=MagicMock())

        request = MagicMock()
        request.url.replace.return_value = "https://example.com/path"

        response = middleware._redirect_to_https(request)

        assert response.status_code == 301
        request.url.replace.assert_called_once_with(scheme="https")

    async def test_subdomain_detection(self):
        """Test subdomain detection logic."""
        app, middleware = app_with_middleware(mock_db_pool=MagicMock(), mock_cache_service=MagicMock())

        # Subdomain of primary should be detected
        assert middleware._is_subdomain_of_primary("agency.app.enterprisehub.com") is True
        assert middleware._is_subdomain_of_primary("client.agency.app.enterprisehub.com") is True

        # Non-subdomains should not be detected
        assert middleware._is_subdomain_of_primary("example.com") is False
        assert middleware._is_subdomain_of_primary("app.example.com") is False

    async def test_client_ip_extraction(self):
        """Test client IP address extraction."""
        app, middleware = app_with_middleware(mock_db_pool=MagicMock(), mock_cache_service=MagicMock())

        # Test X-Forwarded-For header
        forwarded_request = MagicMock()
        forwarded_request.headers = {"x-forwarded-for": "192.168.1.1, 10.0.0.1"}
        forwarded_request.client = None
        assert middleware._get_client_ip(forwarded_request) == "192.168.1.1"

        # Test X-Real-IP header
        real_ip_request = MagicMock()
        real_ip_request.headers = {"x-real-ip": "203.0.113.1"}
        real_ip_request.client = None
        assert middleware._get_client_ip(real_ip_request) == "203.0.113.1"

        # Test direct connection
        direct_request = MagicMock()
        direct_request.headers = {}
        direct_request.client.host = "198.51.100.1"
        assert middleware._get_client_ip(direct_request) == "198.51.100.1"

        # Test fallback when no client info available
        no_client_request = MagicMock()
        no_client_request.headers = {}
        no_client_request.client = None
        assert middleware._get_client_ip(no_client_request) == "unknown"

    async def test_tenant_context_serialization(self):
        """Test tenant context serialization/deserialization."""
        app, middleware = app_with_middleware(mock_db_pool=MagicMock(), mock_cache_service=MagicMock())

        original_context = TenantContext()
        original_context.agency_id = "agency_001"
        original_context.client_id = "client_001"
        original_context.is_white_label = True
        original_context.brand_config = {"brand_name": "Test"}
        original_context.feature_flags = {"analytics": True}

        # Test serialization
        serialized = middleware._tenant_context_to_dict(original_context)
        assert serialized["agency_id"] == "agency_001"
        assert serialized["is_white_label"] is True

        # Test deserialization
        deserialized = middleware._dict_to_tenant_context(serialized)
        assert deserialized.agency_id == original_context.agency_id
        assert deserialized.client_id == original_context.client_id
        assert deserialized.is_white_label == original_context.is_white_label
        assert deserialized.brand_config == original_context.brand_config
        assert deserialized.feature_flags == original_context.feature_flags

    async def test_domain_routing_cache_update(self, mock_db_pool, mock_cache_service):
        """Test domain routing cache update."""
        app, middleware = app_with_middleware(mock_db_pool=mock_db_pool, mock_cache_service=mock_cache_service)

        conn_mock = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = conn_mock
        conn_mock.execute = AsyncMock()

        context = TenantContext()
        context.agency_id = "agency_001"
        context.deployment_id = "deployment_001"
        context.routing_config = {"modules": ["leads"]}
        context.brand_config = {"brand_name": "Test"}
        context.feature_flags = {"analytics": True}

        await middleware._update_domain_routing_cache("example.com", context)

        # Verify database insert/update was called
        conn_mock.execute.assert_called_once()
        call_args = conn_mock.execute.call_args
        assert "INSERT INTO domain_routing_cache" in call_args[0][0]
        assert "ON CONFLICT (domain_name) DO UPDATE" in call_args[0][0]


class TestUtilityFunctions:
    """Test utility functions for route handlers."""

    def test_get_tenant_context(self):
        """Test getting tenant context from request."""
        request = MagicMock()
        request.state.tenant = TenantContext()
        request.state.tenant.agency_id = "test_agency"

        context = get_tenant_context(request)
        assert context.agency_id == "test_agency"

    def test_get_tenant_context_missing(self):
        """Test getting tenant context when missing from request."""
        request = MagicMock()
        del request.state.tenant  # Remove tenant attribute

        context = get_tenant_context(request)
        assert isinstance(context, TenantContext)
        assert context.agency_id is None

    def test_require_agency_context_success(self):
        """Test requiring agency context when available."""
        request = MagicMock()
        request.state.tenant = TenantContext()
        request.state.tenant.agency_id = "test_agency"

        agency_id = require_agency_context(request)
        assert agency_id == "test_agency"

    def test_require_agency_context_missing(self):
        """Test requiring agency context when missing."""
        request = MagicMock()
        request.state.tenant = TenantContext()
        request.state.tenant.agency_id = None

        with pytest.raises(HTTPException) as exc_info:
            require_agency_context(request)

        assert exc_info.value.status_code == 403
        assert "Agency context required" in str(exc_info.value.detail)

    def test_require_client_context_success(self):
        """Test requiring client context when available."""
        request = MagicMock()
        request.state.tenant = TenantContext()
        request.state.tenant.agency_id = "test_agency"
        request.state.tenant.client_id = "test_client"

        agency_id, client_id = require_client_context(request)
        assert agency_id == "test_agency"
        assert client_id == "test_client"

    def test_require_client_context_missing(self):
        """Test requiring client context when missing."""
        request = MagicMock()
        request.state.tenant = TenantContext()
        request.state.tenant.agency_id = "test_agency"
        request.state.tenant.client_id = None

        with pytest.raises(HTTPException) as exc_info:
            require_client_context(request)

        assert exc_info.value.status_code == 403
        assert "Client context required" in str(exc_info.value.detail)

    def test_has_feature_flag(self):
        """Test feature flag checking."""
        request = MagicMock()
        request.state.tenant = TenantContext()
        request.state.tenant.feature_flags = {"advanced_analytics": True, "custom_integrations": False}

        assert has_feature_flag(request, "advanced_analytics") is True
        assert has_feature_flag(request, "custom_integrations") is False
        assert has_feature_flag(request, "nonexistent_flag") is False

    def test_get_brand_config(self):
        """Test getting brand configuration."""
        request = MagicMock()
        request.state.tenant = TenantContext()
        request.state.tenant.brand_config = {"brand_name": "Test Agency", "primary_color": "#6D28D9"}

        brand_config = get_brand_config(request)
        assert brand_config["brand_name"] == "Test Agency"
        assert brand_config["primary_color"] == "#6D28D9"

    def test_is_white_label_request(self):
        """Test white-label request detection."""
        # White-label request
        white_label_request = MagicMock()
        white_label_request.state.tenant = TenantContext()
        white_label_request.state.tenant.is_white_label = True

        assert is_white_label_request(white_label_request) is True

        # Non-white-label request
        regular_request = MagicMock()
        regular_request.state.tenant = TenantContext()
        regular_request.state.tenant.is_white_label = False

        assert is_white_label_request(regular_request) is False


if __name__ == "__main__":
    pytest.main([__file__])