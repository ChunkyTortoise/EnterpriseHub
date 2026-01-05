"""
Script to register a new tenant in the GHL Real Estate AI system.
Usage: python scripts/register_tenant.py --location_id LOC123 --anthropic_key sk-ant-... --ghl_key ghl-...
"""
import argparse
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "ghl-real-estate-ai"))

from ghl_real_estate_ai.services.tenant_service import TenantService

async def register_tenant():
    parser = argparse.ArgumentParser(description="Register a new GHL Tenant")
    parser.add_argument("--location_id", required=True, help="GHL Location ID")
    parser.add_argument("--anthropic_key", required=True, help="Anthropic API Key for this tenant")
    parser.add_argument("--ghl_key", required=True, help="GHL API Key (or OAuth access token) for this tenant")
    
    args = parser.parse_args()
    
    tenant_service = TenantService()
    await tenant_service.save_tenant_config(
        location_id=args.location_id,
        anthropic_api_key=args.anthropic_key,
        ghl_api_key=args.ghl_key
    )
    
    print(f"✅ Successfully registered tenant: {args.location_id}")
    print(f"Stored in: data/tenants/{args.location_id}.json")

if __name__ == "__main__":
    asyncio.run(register_tenant())
