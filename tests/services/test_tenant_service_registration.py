from __future__ import annotations

import json
from pathlib import Path

import pytest

from ghl_real_estate_ai.services.tenant_service import TenantService


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_service(tmp_path: Path) -> TenantService:
    service = TenantService()
    service.tenants_dir = tmp_path / "tenants"
    service.tenants_dir.mkdir(parents=True, exist_ok=True)
    return service


@pytest.mark.asyncio
async def test_register_tenant_config_creates_new_config(tmp_path: Path):
    service = _build_service(tmp_path)

    result = await service.register_tenant_config(
        location_id="loc_create",
        anthropic_api_key="sk-ant-create-123456",
        ghl_api_key="eyJcreate-token-123456",
        ghl_calendar_id="cal_create",
    )

    assert result == "created"
    saved = _read_json(service._get_file_path("loc_create"))
    assert saved["location_id"] == "loc_create"
    assert saved["ghl_calendar_id"] == "cal_create"


@pytest.mark.asyncio
async def test_register_tenant_config_is_idempotent_for_identical_payload(tmp_path: Path):
    service = _build_service(tmp_path)

    await service.save_tenant_config(
        location_id="loc_same",
        anthropic_api_key="sk-ant-same-123456",
        ghl_api_key="eyJsame-token-123456",
        ghl_calendar_id="cal_same",
    )
    file_path = service._get_file_path("loc_same")
    before = _read_json(file_path)

    result = await service.register_tenant_config(
        location_id="loc_same",
        anthropic_api_key="sk-ant-same-123456",
        ghl_api_key="eyJsame-token-123456",
        ghl_calendar_id="cal_same",
    )

    assert result == "unchanged"
    assert _read_json(file_path) == before


@pytest.mark.asyncio
async def test_register_tenant_config_rejects_conflicting_duplicate_without_overwrite(tmp_path: Path):
    service = _build_service(tmp_path)

    await service.save_tenant_config(
        location_id="loc_conflict",
        anthropic_api_key="sk-ant-original-123456",
        ghl_api_key="eyJoriginal-token-123456",
        ghl_calendar_id="cal_original",
    )

    with pytest.raises(ValueError, match="Use --force to overwrite"):
        await service.register_tenant_config(
            location_id="loc_conflict",
            anthropic_api_key="sk-ant-new-123456",
            ghl_api_key="eyJnew-token-123456",
            ghl_calendar_id="cal_new",
        )


@pytest.mark.asyncio
async def test_register_tenant_config_overwrites_when_enabled(tmp_path: Path):
    service = _build_service(tmp_path)

    await service.save_tenant_config(
        location_id="loc_overwrite",
        anthropic_api_key="sk-ant-old-123456",
        ghl_api_key="eyJold-token-123456",
        ghl_calendar_id="cal_old",
    )

    result = await service.register_tenant_config(
        location_id="loc_overwrite",
        anthropic_api_key="sk-ant-new-123456",
        ghl_api_key="eyJnew-token-123456",
        ghl_calendar_id="cal_new",
        overwrite=True,
    )

    assert result == "updated"
    saved = _read_json(service._get_file_path("loc_overwrite"))
    assert saved["anthropic_api_key"] == "sk-ant-new-123456"
    assert saved["ghl_api_key"] == "eyJnew-token-123456"
    assert saved["ghl_calendar_id"] == "cal_new"
