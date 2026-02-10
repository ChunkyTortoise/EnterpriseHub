import pytest

@pytest.mark.integration
"""
Test Authentication Helper

Provides test-safe JWT token generation for Socket.IO scale tests
and integration tests without using hardcoded demo tokens.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt


def generate_test_jwt(
    user_id: str = "test_user",
    email: str = "test@example.com",
    tenant_id: str = "test_tenant",
    roles: list = None,
    expiry_hours: int = 8,
) -> str:
    """
    Generate a valid JWT token for testing purposes.

    Args:
        user_id: User identifier
        email: User email
        tenant_id: Tenant identifier
        roles: List of user roles
        expiry_hours: Token expiration in hours

    Returns:
        Encoded JWT token string
    """
    if roles is None:
        roles = ["tenant_admin"]

    # Use test JWT secret (should match settings.jwt_secret_key in tests)
    jwt_secret = os.getenv("TEST_JWT_SECRET", "test_secret_key_for_scale_testing_only")

    session_id = f"test_session_{secrets.token_urlsafe(8)}"

    payload = {
        "sub": user_id,
        "email": email,
        "tenant_id": tenant_id,
        "session_id": session_id,
        "roles": roles,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
    }

    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    return token


def get_demo_bypass_token() -> str:
    """
    Get demo token only if ENABLE_DEMO_BYPASS is explicitly set.

    Returns:
        Demo token if bypass enabled, otherwise raises error

    Raises:
        RuntimeError: If demo bypass is not enabled
    """
    if os.getenv("ENABLE_DEMO_BYPASS", "false").lower() == "true":
        return "demo_token"
    else:
        raise RuntimeError("Demo token bypass not enabled. Set ENABLE_DEMO_BYPASS=true or use generate_test_jwt()")
