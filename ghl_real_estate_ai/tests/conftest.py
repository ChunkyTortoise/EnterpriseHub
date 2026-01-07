import os
import pytest

# Set dummy environment variables for testing before any imports that use settings
os.environ["ANTHROPIC_API_KEY"] = "sk-test-key-12345"
os.environ["GHL_API_KEY"] = "ghl-test-key-12345"
os.environ["GHL_LOCATION_ID"] = "test-location-id"
os.environ["ENVIRONMENT"] = "testing"
os.environ["TEST_MODE"] = "true"

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Ensure environment variables are set for all tests."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key-12345")
    monkeypatch.setenv("GHL_API_KEY", "ghl-test-key-12345")
    monkeypatch.setenv("GHL_LOCATION_ID", "test-location-id")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("TEST_MODE", "true")
