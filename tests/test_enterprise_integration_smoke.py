import os

import httpx
import pytest


BASE_URL = os.getenv("ENTERPRISE_API_BASE_URL") or os.getenv("BACKEND_URL")


@pytest.mark.integration
def test_agent_status_endpoint_available():
    if not BASE_URL:
        pytest.skip("ENTERPRISE_API_BASE_URL or BACKEND_URL not set")

    response = httpx.get(f"{BASE_URL}/api/agents/status", timeout=10)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "name" in data[0]
        assert "status" in data[0]
        assert "last_run_ts" in data[0]


@pytest.mark.integration
def test_jorge_seller_test_endpoint():
    if not BASE_URL:
        pytest.skip("ENTERPRISE_API_BASE_URL or BACKEND_URL not set")

    response = httpx.post(f"{BASE_URL}/api/jorge-seller/test", timeout=10)
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("test_result") == "PASS"


@pytest.mark.integration
def test_lead_bot_health_endpoint():
    if not BASE_URL:
        pytest.skip("ENTERPRISE_API_BASE_URL or BACKEND_URL not set")

    response = httpx.get(f"{BASE_URL}/api/bots/health", timeout=10)
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "healthy"


@pytest.mark.integration
def test_concierge_health_endpoint():
    if not BASE_URL:
        pytest.skip("ENTERPRISE_API_BASE_URL or BACKEND_URL not set")

    response = httpx.get(f"{BASE_URL}/api/claude-concierge/insights", timeout=10)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
