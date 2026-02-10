import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Test script to validate GHL MCP Server installation.

Run this to verify:
1. Dependencies are installed
2. Environment variables are configured
3. GHL API is accessible
4. MCP server tools are working
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from ghl_real_estate_ai.ghl_utils.config import settings


def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")

    required_modules = {
        "httpx": "httpx",
        "pydantic": "pydantic",
        "pydantic_settings": "pydantic-settings"
    }

    missing = []
    for module_name, package_name in required_modules.items():
        try:
            __import__(module_name)
            print(f"✓ {package_name} installed")
        except ImportError:
            print(f"✗ {package_name} missing")
            missing.append(package_name)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False

    print("✓ All dependencies installed\n")
    return True


def check_environment():
    """Check if environment variables are configured"""
    print("Checking environment variables...")

    required_vars = {
        "ANTHROPIC_API_KEY": settings.anthropic_api_key,
        "GHL_API_KEY": settings.ghl_api_key,
        "GHL_LOCATION_ID": settings.ghl_location_id
    }

    missing = []
    for var_name, var_value in required_vars.items():
        if not var_value or var_value == "dummy":
            print(f"✗ {var_name} not set")
            missing.append(var_name)
        else:
            masked_value = var_value[:8] + "..." if len(var_value) > 8 else "***"
            print(f"✓ {var_name} = {masked_value}")

    if missing:
        print(f"\nMissing environment variables: {', '.join(missing)}")
        print("Add them to .env file in project root")
        return False

    print("✓ All environment variables configured\n")
    return True


async def check_ghl_api():
    """Check if GHL API is accessible"""
    print("Checking GHL API access...")

    try:
        from ghl_real_estate_ai.services.ghl_client import GHLClient

        client = GHLClient()
        response = client.check_health()

        if response.status_code == 200:
            print("✓ GHL API accessible")
            print(f"✓ Location ID: {settings.ghl_location_id}\n")
            return True
        else:
            print(f"✗ GHL API returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ GHL API check failed: {str(e)}\n")
        return False


async def test_mcp_tools():
    """Test MCP server tools"""
    print("Testing MCP server tools...")

    try:
        # Import server module
        from server import GHLMCPServer

        server = GHLMCPServer()

        # Test contact search (should work even in test mode)
        print("  Testing search_ghl_contacts...")
        results = await server.search_ghl_contacts(limit=5)
        print(f"  ✓ search_ghl_contacts returned {len(results)} results")

        # Test contact creation (test mode)
        print("  Testing create_ghl_contact...")
        contact = await server.create_ghl_contact(
            name="Test Contact - MCP Validation",
            email="test@example.com",
            tags=["Test"]
        )
        print(f"  ✓ create_ghl_contact returned ID: {contact.get('id')}")

        # Test lead score update (test mode)
        print("  Testing update_lead_score...")
        score_result = await server.update_lead_score(
            contact_id="test_123",
            score=75.0,
            factors={"test": True},
            notes="MCP installation test"
        )
        print(f"  ✓ update_lead_score completed: {score_result.get('id', 'success')}")

        print("✓ All MCP tools functioning correctly\n")
        return True

    except Exception as e:
        print(f"✗ MCP tools test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Print test summary"""
    print("=" * 50)
    print("INSTALLATION TEST SUMMARY")
    print("=" * 50)

    all_passed = all(results.values())

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 50)

    if all_passed:
        print("✓ GHL MCP Server installation complete!")
        print("\nNext steps:")
        print("1. Start using natural language GHL operations")
        print("2. Try: 'Create contact named John Smith with email john@example.com'")
        print("3. Try: 'Update lead score for contact abc123 to 85'")
        print("4. See README.md for full documentation")
    else:
        print("✗ Installation incomplete. Fix errors above and retry.")

    print("=" * 50)


async def main():
    """Run all installation tests"""
    print("=" * 50)
    print("GHL MCP SERVER INSTALLATION TEST")
    print("=" * 50)
    print()

    results = {
        "Dependencies": check_dependencies(),
        "Environment": check_environment(),
        "GHL API": await check_ghl_api(),
        "MCP Tools": await test_mcp_tools()
    }

    print_summary(results)

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
