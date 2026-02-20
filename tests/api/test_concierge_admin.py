"""
Tests for Concierge Admin API endpoints.

Endpoints tested:
    GET    /admin/concierge/tenants                           - List cached tenants
    GET    /admin/concierge/tenants/{tenant_id}               - Full tenant config
    POST   /admin/concierge/tenants/{tenant_id}/reload        - Hot-reload config
    DELETE /admin/concierge/sessions/{tenant_id}/{session_id} - Delete session
"""

import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ghl_real_estate_ai.config.concierge_config_loader import (
    AgentDef,
    ConciergeClientConfig,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(tenant_id: str = "jorge", domain: str = "real_estate") -> ConciergeClientConfig:
    return ConciergeClientConfig(
        tenant_id=tenant_id,
        domain=domain,
        client_name="Jorge Salas",
        business_model="6% commission",
        market_context="Rancho Cucamonga, CA",
        client_style="Direct and results-focused",
        available_agents=[
            AgentDef(
                name="Seller Bot",
                agent_type="seller_qualification",
                capabilities=["real_time_questioning"],
                invoke_pattern="seller",
            ),
            AgentDef(
                name="Buyer Bot",
                agent_type="buyer_qualification",
                capabilities=["property_matching"],
                invoke_pattern="buyer",
            ),
        ],
        platform_features={"lead_management": ["Seller Bot", "Buyer Bot"]},
        compliance_requirements=["DRE licensing", "Fair Housing"],
    )


@contextlib.contextmanager
def _patched_client(cache_dict=None, cache_service=None, loader_overrides=None):
    """Yield (TestClient, mock_loader, mock_cache) with patches active for the
    full duration of the context so requests hit mocked objects."""
    mock_loader = MagicMock()
    mock_loader._cache = cache_dict if cache_dict is not None else {}
    if loader_overrides:
        for attr, val in loader_overrides.items():
            setattr(mock_loader, attr, val)

    mock_cache = cache_service or AsyncMock()
    if not hasattr(mock_cache.delete, '_mock_name'):
        mock_cache.delete = AsyncMock(return_value=True)

    with (
        patch("ghl_real_estate_ai.api.routes.concierge_admin._loader", mock_loader),
        patch("ghl_real_estate_ai.api.routes.concierge_admin.get_cache_service", return_value=mock_cache),
    ):
        from ghl_real_estate_ai.api.routes.concierge_admin import router

        app = FastAPI()
        app.include_router(router, prefix="/admin/concierge")
        client = TestClient(app, raise_server_exceptions=False)
        yield client, mock_loader, mock_cache


# ---------------------------------------------------------------------------
# GET /tenants -- list all cached tenants
# ---------------------------------------------------------------------------

class TestListTenants:
    def test_list_empty(self):
        with _patched_client(cache_dict={}) as (client, _, _):
            resp = client.get("/admin/concierge/tenants")
            assert resp.status_code == 200
            assert resp.json() == []

    def test_list_single_tenant(self):
        cfg = _make_config("jorge")
        with _patched_client(cache_dict={"jorge": cfg}) as (client, _, _):
            resp = client.get("/admin/concierge/tenants")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["tenant_id"] == "jorge"
            assert data[0]["domain"] == "real_estate"
            assert data[0]["client_name"] == "Jorge Salas"
            assert data[0]["agent_count"] == 2

    def test_list_multiple_tenants(self):
        cache = {
            "jorge": _make_config("jorge", "real_estate"),
            "dental": _make_config("dental", "dental"),
        }
        with _patched_client(cache_dict=cache) as (client, _, _):
            resp = client.get("/admin/concierge/tenants")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
            tenant_ids = {t["tenant_id"] for t in data}
            assert tenant_ids == {"jorge", "dental"}


# ---------------------------------------------------------------------------
# GET /tenants/{tenant_id} -- full config
# ---------------------------------------------------------------------------

class TestGetTenant:
    def test_get_existing_tenant(self):
        cfg = _make_config("jorge")
        with _patched_client(cache_dict={"jorge": cfg}) as (client, _, _):
            resp = client.get("/admin/concierge/tenants/jorge")
            assert resp.status_code == 200
            data = resp.json()
            assert data["tenant_id"] == "jorge"
            assert data["domain"] == "real_estate"
            assert data["client_name"] == "Jorge Salas"
            assert data["business_model"] == "6% commission"
            assert data["market_context"] == "Rancho Cucamonga, CA"
            assert data["client_style"] == "Direct and results-focused"
            assert data["agent_count"] == 2
            assert len(data["agents"]) == 2
            assert data["agents"][0]["name"] == "Seller Bot"
            assert data["agents"][0]["agent_type"] == "seller_qualification"
            assert data["agents"][0]["invoke_pattern"] == "seller"
            assert data["compliance_requirements"] == ["DRE licensing", "Fair Housing"]
            assert data["platform_features"] == {"lead_management": ["Seller Bot", "Buyer Bot"]}

    def test_get_unknown_tenant_returns_404(self):
        with _patched_client(cache_dict={}) as (client, _, _):
            resp = client.get("/admin/concierge/tenants/unknown")
            assert resp.status_code == 404
            assert "unknown" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /tenants/{tenant_id}/reload -- hot-reload
# ---------------------------------------------------------------------------

class TestReloadTenant:
    def test_reload_success(self):
        cfg = _make_config("jorge")
        with _patched_client(
            cache_dict={"jorge": cfg},
            loader_overrides={"reload": MagicMock()},
        ) as (client, loader, _):
            resp = client.post("/admin/concierge/tenants/jorge/reload")
            assert resp.status_code == 200
            data = resp.json()
            assert data["tenant_id"] == "jorge"
            assert data["status"] == "reloaded"
            assert data["domain"] == "real_estate"
            assert data["agent_count"] == 2
            loader.reload.assert_called_once_with("jorge")

    def test_reload_missing_config_returns_404(self):
        with _patched_client(
            cache_dict={},
            loader_overrides={
                "reload": MagicMock(side_effect=FileNotFoundError("Config not found: jorge.yaml")),
            },
        ) as (client, _, _):
            resp = client.post("/admin/concierge/tenants/jorge/reload")
            assert resp.status_code == 404
            assert "jorge.yaml" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# DELETE /sessions/{tenant_id}/{session_id} -- delete session
# ---------------------------------------------------------------------------

class TestDeleteSession:
    def test_delete_existing_session(self):
        mock_cache = AsyncMock()
        mock_cache.delete = AsyncMock(return_value=True)
        with _patched_client(cache_service=mock_cache) as (client, _, cache):
            resp = client.delete("/admin/concierge/sessions/jorge/sess-abc-123")
            assert resp.status_code == 200
            data = resp.json()
            assert data["tenant_id"] == "jorge"
            assert data["session_id"] == "sess-abc-123"
            assert data["deleted"] is True
            cache.delete.assert_called_once_with("concierge:jorge:session:sess-abc-123")

    def test_delete_nonexistent_session(self):
        mock_cache = AsyncMock()
        mock_cache.delete = AsyncMock(return_value=False)
        with _patched_client(cache_service=mock_cache) as (client, _, cache):
            resp = client.delete("/admin/concierge/sessions/jorge/nonexistent")
            assert resp.status_code == 200
            data = resp.json()
            assert data["deleted"] is False
            cache.delete.assert_called_once_with("concierge:jorge:session:nonexistent")


# ---------------------------------------------------------------------------
# Response shape validation
# ---------------------------------------------------------------------------

class TestResponseShapes:
    def test_tenant_summary_shape(self):
        cfg = _make_config("jorge")
        with _patched_client(cache_dict={"jorge": cfg}) as (client, _, _):
            resp = client.get("/admin/concierge/tenants")
            data = resp.json()[0]
            assert set(data.keys()) == {"tenant_id", "domain", "client_name", "agent_count"}

    def test_tenant_detail_shape(self):
        cfg = _make_config("jorge")
        with _patched_client(cache_dict={"jorge": cfg}) as (client, _, _):
            resp = client.get("/admin/concierge/tenants/jorge")
            data = resp.json()
            expected_keys = {
                "tenant_id", "domain", "client_name", "business_model",
                "market_context", "client_style", "agent_count", "agents",
                "compliance_requirements", "platform_features",
            }
            assert set(data.keys()) == expected_keys

    def test_agent_info_shape(self):
        cfg = _make_config("jorge")
        with _patched_client(cache_dict={"jorge": cfg}) as (client, _, _):
            resp = client.get("/admin/concierge/tenants/jorge")
            agent = resp.json()["agents"][0]
            assert set(agent.keys()) == {"name", "agent_type", "invoke_pattern"}
