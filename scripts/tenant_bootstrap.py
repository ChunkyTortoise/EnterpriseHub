#!/usr/bin/env python3
"""Tenant bootstrap automation for Jorge multi-subaccount onboarding."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import re
import sys


ANTHROPIC_KEY_PATTERN = re.compile(r"^sk-ant-[A-Za-z0-9_-]{8,}$")


@dataclass(frozen=True)
class BootstrapRequest:
    tenant_name: str
    location_id: str
    anthropic_key: str
    ghl_key: str
    calendar_id: str | None
    confirmation_strategy: str
    confirmation_email_workflow_id: str | None
    checklist_path: Path
    dry_run: bool
    force: bool


def _validate_non_empty(value: str, field_name: str, minimum: int = 1) -> str:
    cleaned = value.strip()
    if len(cleaned) < minimum:
        raise ValueError(f"{field_name} must be at least {minimum} characters")
    return cleaned


def validate_request(request: BootstrapRequest) -> None:
    _validate_non_empty(request.tenant_name, "tenant_name", minimum=3)
    _validate_non_empty(request.location_id, "location_id", minimum=5)

    if not ANTHROPIC_KEY_PATTERN.match(request.anthropic_key.strip()):
        raise ValueError("anthropic_key must start with 'sk-ant-' and include a valid suffix")

    if len(request.ghl_key.strip()) < 10:
        raise ValueError("ghl_key must be at least 10 characters")

    if request.confirmation_strategy not in {"sms_only", "sms_and_email"}:
        raise ValueError("confirmation_strategy must be sms_only or sms_and_email")

    if request.confirmation_strategy == "sms_and_email" and not request.confirmation_email_workflow_id:
        raise ValueError("confirmation_email_workflow_id is required when confirmation_strategy=sms_and_email")


def build_checklist_markdown(request: BootstrapRequest, created_at: datetime) -> str:
    calendar_display = request.calendar_id or "Not configured"
    workflow_display = request.confirmation_email_workflow_id or "Not configured"

    return f"""# Tenant Bootstrap Checklist

Created: {created_at.isoformat()}
Tenant: {request.tenant_name}
Location ID: {request.location_id}

## Provisioning Snapshot

- Confirmation strategy: `{request.confirmation_strategy}`
- Calendar ID: `{calendar_display}`
- Email workflow ID: `{workflow_display}`
- Tenant config path: `data/tenants/{request.location_id}.json`

## Required Execution Steps

1. Verify tenant credentials are valid in staging by sending a manual API request to GHL.
2. Configure the tenant webhook endpoint and secret in GHL.
3. Confirm activation tags include `Needs Qualifying` and `Buyer-Lead` as needed.
4. Confirm deactivation tags include `AI-Off`, `Do Not Contact`, and `Stop-Bot`.
5. Validate custom field mappings for seller temperature, timeline, asking price, and qualification complete.
6. Validate seller appointment type is configured as `seller_consultation` with 30-minute duration.
7. Validate appointment confirmation behavior matches `{request.confirmation_strategy}`.
8. Run webhook smoke tests for seller and buyer flows.
9. Run opt-out test (`STOP`) and confirm DNC behavior.
10. Record go-live decision and owner sign-off.

## Validation Evidence (Fill During Onboarding)

- Webhook smoke test result:
- Seller HOT booking test result:
- Buyer routing test result:
- Opt-out compliance test result:
- Owner sign-off:
"""


async def _save_tenant_config(request: BootstrapRequest) -> str:
    from ghl_real_estate_ai.services.tenant_service import TenantService

    tenant_service = TenantService()
    return await tenant_service.register_tenant_config(
        location_id=request.location_id,
        anthropic_api_key=request.anthropic_key,
        ghl_api_key=request.ghl_key,
        ghl_calendar_id=request.calendar_id,
        overwrite=request.force,
    )


def parse_args(argv: list[str]) -> BootstrapRequest:
    parser = argparse.ArgumentParser(description="Bootstrap a new Jorge tenant/subaccount")
    parser.add_argument("--tenant-name", required=True, help="Display name for the tenant")
    parser.add_argument("--location-id", required=True, help="GHL location/subaccount ID")
    parser.add_argument("--anthropic-key", required=True, help="Tenant Anthropic key")
    parser.add_argument("--ghl-key", required=True, help="Tenant GHL API key or OAuth token")
    parser.add_argument("--calendar-id", help="Optional GHL calendar ID")
    parser.add_argument(
        "--confirmation-strategy",
        choices=["sms_only", "sms_and_email"],
        default="sms_only",
        help="Appointment confirmation mode",
    )
    parser.add_argument(
        "--confirmation-email-workflow-id",
        help="Required when confirmation strategy is sms_and_email",
    )
    parser.add_argument(
        "--checklist-out",
        help="Checklist output path (defaults to docs/tenant_onboarding/<location_id>_checklist.md)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate and generate checklist only")
    parser.add_argument("--force", action="store_true", help="Allow overwrite when tenant already exists")

    args = parser.parse_args(argv)
    checklist_path = Path(args.checklist_out) if args.checklist_out else Path("docs/tenant_onboarding") / f"{args.location_id}_checklist.md"

    return BootstrapRequest(
        tenant_name=args.tenant_name,
        location_id=args.location_id,
        anthropic_key=args.anthropic_key,
        ghl_key=args.ghl_key,
        calendar_id=args.calendar_id,
        confirmation_strategy=args.confirmation_strategy,
        confirmation_email_workflow_id=args.confirmation_email_workflow_id,
        checklist_path=checklist_path,
        dry_run=args.dry_run,
        force=args.force,
    )


def _tenant_file_path(location_id: str) -> Path:
    return Path("data/tenants") / f"{location_id}.json"


async def run(request: BootstrapRequest) -> int:
    validate_request(request)

    created_at = datetime.now(UTC)
    request.checklist_path.parent.mkdir(parents=True, exist_ok=True)
    request.checklist_path.write_text(build_checklist_markdown(request, created_at), encoding="utf-8")

    if request.dry_run:
        print(f"Dry run complete. Checklist created at: {request.checklist_path}")
        return 0

    registration_result = await _save_tenant_config(request)
    tenant_file = _tenant_file_path(request.location_id)

    if registration_result == "unchanged":
        print(f"Tenant bootstrap unchanged for {request.location_id} (already registered)")
    else:
        print(f"Tenant bootstrap complete for {request.location_id} ({registration_result})")
    print(f"Tenant config: {tenant_file}")
    print(f"Checklist: {request.checklist_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    try:
        request = parse_args(argv)
        return asyncio.run(run(request))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Cancelled", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
