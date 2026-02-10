from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
from pathlib import Path
import sys
from unittest.mock import AsyncMock

import pytest


def _load_tenant_bootstrap_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "tenant_bootstrap.py"
    spec = importlib.util.spec_from_file_location("tenant_bootstrap", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_validate_request_rejects_missing_email_workflow_for_sms_and_email():
    module = _load_tenant_bootstrap_module()
    request = module.BootstrapRequest(
        tenant_name="Acme Realty",
        location_id="loc_abc123",
        anthropic_key="sk-ant-validsuffix123",
        ghl_key="ghlkey12345",
        calendar_id=None,
        confirmation_strategy="sms_and_email",
        confirmation_email_workflow_id=None,
        checklist_path=Path("docs/tenant_onboarding/loc_abc123_checklist.md"),
        dry_run=True,
        force=False,
    )

    with pytest.raises(ValueError, match="confirmation_email_workflow_id"):
        module.validate_request(request)


def test_build_checklist_contains_expected_items():
    module = _load_tenant_bootstrap_module()
    request = module.BootstrapRequest(
        tenant_name="Acme Realty",
        location_id="loc_abc123",
        anthropic_key="sk-ant-validsuffix123",
        ghl_key="ghlkey12345",
        calendar_id="cal_primary",
        confirmation_strategy="sms_only",
        confirmation_email_workflow_id=None,
        checklist_path=Path("docs/tenant_onboarding/loc_abc123_checklist.md"),
        dry_run=True,
        force=False,
    )

    checklist = module.build_checklist_markdown(request, datetime.now(UTC))
    assert "Tenant: Acme Realty" in checklist
    assert "Location ID: loc_abc123" in checklist
    assert "seller_consultation" in checklist
    assert "Run webhook smoke tests for seller and buyer flows." in checklist


@pytest.mark.asyncio
async def test_run_dry_run_writes_checklist(tmp_path: Path):
    module = _load_tenant_bootstrap_module()
    checklist_path = tmp_path / "loc_abc123_checklist.md"

    request = module.BootstrapRequest(
        tenant_name="Acme Realty",
        location_id="loc_abc123",
        anthropic_key="sk-ant-validsuffix123",
        ghl_key="ghlkey12345",
        calendar_id=None,
        confirmation_strategy="sms_only",
        confirmation_email_workflow_id=None,
        checklist_path=checklist_path,
        dry_run=True,
        force=False,
    )

    exit_code = await module.run(request)

    assert exit_code == 0
    assert checklist_path.exists()
    assert "Validation Evidence" in checklist_path.read_text(encoding="utf-8")


def test_parse_args_applies_default_checklist_path():
    module = _load_tenant_bootstrap_module()
    request = module.parse_args(
        [
            "--tenant-name",
            "Acme Realty",
            "--location-id",
            "loc_abc123",
            "--anthropic-key",
            "sk-ant-validsuffix123",
            "--ghl-key",
            "ghlkey12345",
        ]
    )

    assert request.checklist_path == Path("docs/tenant_onboarding/loc_abc123_checklist.md")
    assert request.force is False
    assert request.dry_run is False


@pytest.mark.asyncio
async def test_run_non_dry_run_handles_idempotent_registration(tmp_path: Path, capsys):
    module = _load_tenant_bootstrap_module()
    checklist_path = tmp_path / "loc_abc123_checklist.md"
    module._save_tenant_config = AsyncMock(return_value="unchanged")

    request = module.BootstrapRequest(
        tenant_name="Acme Realty",
        location_id="loc_abc123",
        anthropic_key="sk-ant-validsuffix123",
        ghl_key="ghlkey12345",
        calendar_id=None,
        confirmation_strategy="sms_only",
        confirmation_email_workflow_id=None,
        checklist_path=checklist_path,
        dry_run=False,
        force=False,
    )

    exit_code = await module.run(request)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert checklist_path.exists()
    assert "unchanged" in output
