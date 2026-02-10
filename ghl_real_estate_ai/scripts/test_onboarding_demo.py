import pytest

@pytest.mark.unit
#!/usr/bin/env python3
"""
Demo script to test onboarding 3 sample partners.

This script simulates the interactive onboarding process for testing purposes.
It creates 3 test tenants with dummy API keys.

Usage:
    python scripts/test_onboarding_demo.py
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "ghl-real-estate-ai"))

from ghl_real_estate_ai.services.tenant_service import TenantService

# Sample test partners
TEST_PARTNERS = [
    {
        "partner_name": "Acme Real Estate",
        "location_id": "demo_acme_001",
        "anthropic_api_key": "sk-ant-api03-demo-acme-123456789012345",
        "ghl_api_key": "ghl-demo-key-acme-987654321",
        "ghl_calendar_id": "cal_acme_primary"
    },
    {
        "partner_name": "Sunset Properties",
        "location_id": "demo_sunset_002",
        "anthropic_api_key": "sk-ant-api03-demo-sunset-123456789012345",
        "ghl_api_key": "ghl-demo-key-sunset-987654321",
        "ghl_calendar_id": None  # No calendar for this partner
    },
    {
        "partner_name": "Coastal Realty Group",
        "location_id": "demo_coastal_003",
        "anthropic_api_key": "sk-ant-api03-demo-coastal-123456789012345",
        "ghl_api_key": "ghl-demo-key-coastal-987654321",
        "ghl_calendar_id": "cal_coastal_main"
    }
]


async def onboard_test_partners():
    """Onboard 3 test partners for demo purposes."""
    print("=" * 70)
    print("  GHL Real Estate AI - Demo Onboarding Test")
    print("=" * 70)
    print("\nOnboarding 3 sample partners with test credentials...\n")

    tenant_service = TenantService()
    tenants_dir = Path("data/tenants")

    for idx, partner in enumerate(TEST_PARTNERS, 1):
        print(f"\n[{idx}/3] Onboarding: {partner['partner_name']}")
        print(f"      Location ID: {partner['location_id']}")

        try:
            # Check if already exists
            tenant_file = tenants_dir / f"{partner['location_id']}.json"
            if tenant_file.exists():
                print(f"      ⚠ Already exists, skipping...")
                continue

            # Save tenant config
            await tenant_service.save_tenant_config(
                location_id=partner['location_id'],
                anthropic_api_key=partner['anthropic_api_key'],
                ghl_api_key=partner['ghl_api_key'],
                ghl_calendar_id=partner['ghl_calendar_id']
            )

            print(f"      ✓ Successfully registered")
            print(f"      Saved to: {tenant_file}")

        except Exception as e:
            print(f"      ✗ Failed: {str(e)}")

    print("\n" + "=" * 70)
    print("  Demo Onboarding Complete!")
    print("=" * 70)
    print("\nRegistered Partners:")

    # List all demo partners
    for partner in TEST_PARTNERS:
        tenant_file = tenants_dir / f"{partner['location_id']}.json"
        if tenant_file.exists():
            print(f"  ✓ {partner['partner_name']} ({partner['location_id']})")
        else:
            print(f"  ✗ {partner['partner_name']} (FAILED)")

    print("\nTo test the onboarding tool interactively:")
    print("  python scripts/onboard_partner.py")
    print("\nTo view tenant files:")
    print("  ls -la data/tenants/")
    print("\nTo clean up demo data:")
    print("  rm data/tenants/demo_*")
    print()


async def cleanup_test_partners():
    """Remove test partner files."""
    tenants_dir = Path("data/tenants")

    print("Cleaning up demo partners...")
    count = 0

    for partner in TEST_PARTNERS:
        tenant_file = tenants_dir / f"{partner['location_id']}.json"
        if tenant_file.exists():
            tenant_file.unlink()
            print(f"  ✓ Removed {partner['location_id']}.json")
            count += 1

    print(f"\nRemoved {count} demo tenant(s).")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Demo onboarding test script")
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove demo partners instead of creating them"
    )

    args = parser.parse_args()

    if args.cleanup:
        await cleanup_test_partners()
    else:
        await onboard_test_partners()


if __name__ == "__main__":
    asyncio.run(main())
