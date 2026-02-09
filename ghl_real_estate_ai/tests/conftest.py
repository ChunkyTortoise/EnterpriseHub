# Global test configuration
import os
import sys

# Set required env vars before any imports to prevent import-time ValueErrors
_test_env_defaults = {
    "JWT_SECRET_KEY": "test-jwt-secret-key-for-testing-only-minimum-32-chars",
    "STRIPE_SECRET_KEY": "sk_test_fake_key_for_testing",
    "STRIPE_WEBHOOK_SECRET": "whsec_test_fake_secret",
}
for _k, _v in _test_env_defaults.items():
    if _k not in os.environ:
        os.environ[_k] = _v

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest


@pytest.fixture(scope="session", autouse=True)
def force_austin_market():
    """Force Austin market for property matcher tests to ensure consistent test data."""
    original = os.environ.get("JORGE_MARKET")
    os.environ["JORGE_MARKET"] = "austin"
    yield
    if original:
        os.environ["JORGE_MARKET"] = original
    else:
        os.environ.pop("JORGE_MARKET", None)
