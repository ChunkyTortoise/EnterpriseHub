"""Shared fixtures and stubs for API route tests."""

import sys
from unittest.mock import MagicMock

# Stub optional heavy dependencies that may not be installed in test env.
# These are imported transitively when the FastAPI app loads all route modules.
for _mod_name in ("speech_recognition", "bleach"):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = MagicMock()


import pytest


@pytest.fixture(autouse=True)
def _bypass_rate_limiter_for_api_tests():
    """Bypass rate limiter for all API tests to prevent cross-test pollution.

    The in-memory rate limiter accumulates state across tests, causing false
    rate-limit blocks when many TestClient requests run in a single session.
    """
    from unittest.mock import patch

    async def _always_allow(*args, **kwargs):
        return (True, None)

    with patch(
        "ghl_real_estate_ai.api.middleware.rate_limiter.EnhancedRateLimiter.is_allowed",
        new=_always_allow,
    ):
        yield
