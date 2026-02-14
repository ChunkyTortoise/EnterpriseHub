"""
Security Integration Tests - Fixed Version
Tests security middleware without TestClient compatibility issues
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest

# Test security modules directly without TestClient
from ghl_real_estate_ai.api.middleware import APIKeyAuth, JWTAuth, RateLimitMiddleware, SecurityHeadersMiddleware
from ghl_real_estate_ai.api.middleware.rate_limiter import RateLimiter


class TestJWTAuthentication:
    """Test JWT authentication functionality."""

    def test_jwt_create_token(self):
        """Test JWT token creation."""
        token = JWTAuth.create_access_token(data={"sub": "test_user"})

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

    def test_jwt_verify_token_valid(self):
        """Test JWT token verification with valid token."""
        token = JWTAuth.create_access_token(data={"sub": "test_user"})
        payload = JWTAuth.verify_token(token)

        assert payload is not None
        assert payload["sub"] == "test_user"

    def test_jwt_verify_token_invalid(self):
        """Test JWT token verification with invalid token."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            JWTAuth.verify_token("invalid_token")

        assert exc_info.value.status_code == 401

    def test_jwt_hash_password(self):
        """Test password hashing."""
        password = "test_password"
        hashed = JWTAuth.hash_password(password)

        assert hashed != password
        assert len(hashed) > 20

    def test_jwt_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password"
        hashed = JWTAuth.hash_password(password)

        assert JWTAuth.verify_password(password, hashed)

    def test_jwt_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password"
        hashed = JWTAuth.hash_password(password)

        assert not JWTAuth.verify_password("wrong_password", hashed)


class TestAPIKeyAuthentication:
    """Test API key authentication functionality."""

    def test_generate_api_key(self):
        """Test API key generation."""
        api_key = APIKeyAuth.generate_api_key()

        assert api_key is not None
        assert isinstance(api_key, str)
        assert len(api_key) > 20

    def test_hash_api_key(self):
        """Test API key hashing."""
        api_key = "test_api_key_12345"
        hashed = APIKeyAuth.hash_api_key(api_key)

        assert hashed != api_key
        assert len(hashed) == 64  # SHA256 hex length

    def test_api_key_hash_consistent(self):
        """Test that hashing same key gives same result."""
        api_key = "test_api_key_12345"
        hash1 = APIKeyAuth.hash_api_key(api_key)
        hash2 = APIKeyAuth.hash_api_key(api_key)

        assert hash1 == hash2


class TestRateLimiter:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_first_request(self):
        """Test that rate limiter allows first request."""
        limiter = RateLimiter(requests_per_minute=60)

        result = await limiter.is_allowed("test_key")
        allowed = result[0] if isinstance(result, tuple) else result
        assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limiter_burst_limit(self):
        """Test rate limiter burst capacity."""
        limiter = RateLimiter(requests_per_minute=60, burst=5)

        # Should allow burst number of requests
        for i in range(5):
            result = await limiter.is_allowed("test_key")
            allowed = result[0] if isinstance(result, tuple) else result
            assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limiter_exceeds_burst(self):
        """Test rate limiter when exceeding burst."""
        limiter = RateLimiter(requests_per_minute=60, burst=3)

        # Use up burst
        for i in range(3):
            await limiter.is_allowed("test_key")

        # Next request should be denied
        result = await limiter.is_allowed("test_key")
        allowed = result[0] if isinstance(result, tuple) else result
        assert allowed is False

    @pytest.mark.asyncio
    async def test_rate_limiter_different_keys(self):
        """Test rate limiter with different keys."""
        limiter = RateLimiter(requests_per_minute=60, burst=3)

        # Different keys should have independent limits
        result1 = await limiter.is_allowed("key1")
        result2 = await limiter.is_allowed("key2")
        allowed1 = result1[0] if isinstance(result1, tuple) else result1
        allowed2 = result2[0] if isinstance(result2, tuple) else result2

        assert allowed1 is True
        assert allowed2 is True


class TestSecurityHeaders:
    """Test security headers middleware."""

    def test_security_headers_middleware_exists(self):
        """Test that SecurityHeadersMiddleware can be instantiated."""
        from starlette.middleware.base import BaseHTTPMiddleware

        assert issubclass(SecurityHeadersMiddleware, BaseHTTPMiddleware)

    @pytest.mark.asyncio
    async def test_security_headers_applied(self):
        """Test that security headers are applied to response."""
        from starlette.requests import Request
        from starlette.responses import Response

        # Create mock request with realistic headers
        mock_request = Mock(spec=Request)
        mock_request.headers = {"user-agent": "TestAgent", "host": "localhost"}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_response = Response()

        # Create middleware instance
        middleware = SecurityHeadersMiddleware(app=Mock())

        # Mock call_next to return our response
        async def mock_call_next(request):
            return mock_response

        # Call dispatch
        result = await middleware.dispatch(mock_request, mock_call_next)

        # Check headers were added
        assert "X-Content-Type-Options" in result.headers
        assert "X-Frame-Options" in result.headers
        assert "X-XSS-Protection" in result.headers
        # HSTS only added for HTTPS requests, skip for mock HTTP
        assert "Content-Security-Policy" in result.headers
        assert "Referrer-Policy" in result.headers


class TestSecurityIntegration:
    """Integration tests for security features."""

    def test_all_security_components_importable(self):
        """Test that all security components can be imported."""
        from ghl_real_estate_ai.api.middleware import (
            APIKeyAuth,
            JWTAuth,
            SecurityHeadersMiddleware,
            get_current_user,
            verify_api_key,
        )

        assert JWTAuth is not None
        assert get_current_user is not None
        assert APIKeyAuth is not None
        assert verify_api_key is not None
        assert RateLimitMiddleware is not None
        assert SecurityHeadersMiddleware is not None

    def test_jwt_workflow(self):
        """Test complete JWT workflow."""
        # Create token
        token = JWTAuth.create_access_token(data={"sub": "test_user", "role": "admin"})

        # Verify token
        payload = JWTAuth.verify_token(token)

        assert payload["sub"] == "test_user"
        assert payload["role"] == "admin"

    def test_api_key_workflow(self):
        """Test complete API key workflow."""
        # Generate key
        api_key = APIKeyAuth.generate_api_key()

        # Hash it
        hashed = APIKeyAuth.hash_api_key(api_key)

        # Verify hash is different
        assert api_key != hashed
        assert len(hashed) == 64


class TestEnvironmentConfiguration:
    """Test environment configuration for security."""

    def test_jwt_secret_key_configured(self):
        """Test JWT secret key configuration."""
        from ghl_real_estate_ai.api.middleware.jwt_auth import SECRET_KEY

        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0

    def test_jwt_algorithm_configured(self):
        """Test JWT algorithm configuration."""
        from ghl_real_estate_ai.api.middleware.jwt_auth import ALGORITHM

        assert ALGORITHM == "HS256"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])