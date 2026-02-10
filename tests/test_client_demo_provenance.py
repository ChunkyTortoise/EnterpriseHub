import os
import pytest

from ghl_real_estate_ai.services import client_demo_service as demo_module


class DummyService:
    def __init__(self, *args, **kwargs):
        pass


@pytest.mark.asyncio
async def test_demo_session_has_provenance(monkeypatch):
    monkeypatch.setenv("DEMO_DATA_SOURCE", "synthetic")

    monkeypatch.setattr(demo_module, "CacheService", DummyService)
    monkeypatch.setattr(demo_module, "ROICalculatorService", DummyService)
    monkeypatch.setattr(demo_module, "ClaudeAssistant", DummyService)
    monkeypatch.setattr(demo_module, "MLAnalyticsEngine", DummyService)
    monkeypatch.setattr(demo_module, "GHLService", DummyService)

    service = demo_module.ClientDemoService()

    async def _noop_store(_):
        return None

    monkeypatch.setattr(service, "_store_demo_environment", _noop_store)

    demo_env = await service.create_demo_session(demo_module.DemoScenario.MID_MARKET)
    assert demo_env.data_source == "synthetic"
    assert demo_env.data_provenance["demo_mode"] is True
    assert "roi_assumptions" in demo_env.__dict__
