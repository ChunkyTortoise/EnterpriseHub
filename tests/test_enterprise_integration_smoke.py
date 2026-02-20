import pytest

pytestmark = pytest.mark.integration

import importlib
import os

import httpx
import pytest

BASE_URL = os.getenv("ENTERPRISE_API_BASE_URL") or os.getenv("BACKEND_URL")


@pytest.fixture
def mocker(monkeypatch):
    class SimpleMocker:
        def patch(self, target, new=None, **kwargs):
            parts = target.split(".")
            module = None
            module_index = None
            for i in range(len(parts), 0, -1):
                module_path = ".".join(parts[:i])
                try:
                    module = importlib.import_module(module_path)
                    module_index = i
                    break
                except ModuleNotFoundError:
                    continue

            if module is None or module_index is None:
                raise ModuleNotFoundError(f"Could not import module for target: {target}")

            obj = module
            attr_chain = parts[module_index:]
            for attr in attr_chain[:-1]:
                obj = getattr(obj, attr)
            monkeypatch.setattr(obj, attr_chain[-1], new)
            return new

    return SimpleMocker()


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
