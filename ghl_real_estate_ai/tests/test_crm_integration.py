"""
Tests for CRM Integration Features (Phase 3)
"""

import os

import pytest

from ghl_real_estate_ai.services.crm_service import CRMService

# Set dummy env vars for test mode
os.environ["ENVIRONMENT"] = "development"


@pytest.mark.asyncio
async def test_crm_config_update():
    """Test updating CRM configuration."""
    service = CRMService("test_location_crm")

    # Update Salesforce config
    service.update_config("salesforce", {"enabled": True, "api_key": "sf_key_123"})
    assert service.config["salesforce"]["enabled"] is True
    assert service.config["salesforce"]["api_key"] == "sf_key_123"

    # Update HubSpot config
    service.update_config("hubspot", {"enabled": True, "api_key": "hs_key_456"})
    assert service.config["hubspot"]["enabled"] is True
    assert service.config["hubspot"]["api_key"] == "hs_key_456"


@pytest.mark.asyncio
async def test_crm_sync_lead():
    """Test lead synchronization to enabled CRMs."""
    service = CRMService("test_location_crm_sync")
    service.update_config("salesforce", {"enabled": True})
    service.update_config("hubspot", {"enabled": True})

    contact_data = {"id": "contact_123", "first_name": "Test"}
    results = await service.sync_lead(contact_data)

    assert "salesforce" in results
    assert "hubspot" in results
    assert results["salesforce"]["status"] == "success"
    assert results["hubspot"]["status"] == "success"