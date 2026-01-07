"""
CRM API Routes for GHL Real Estate AI.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.crm_service import CRMService

logger = get_logger(__name__)
router = APIRouter(prefix="/crm", tags=["crm"])


class CRMConfigUpdate(BaseModel):
    enabled: bool
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None


@router.get("/{location_id}/config")
async def get_crm_config(location_id: str):
    """Get CRM configuration for a location."""
    service = CRMService(location_id)
    return service.config


@router.post("/{location_id}/config/{platform}")
async def update_crm_config(location_id: str, platform: str, config: CRMConfigUpdate):
    """Update CRM configuration for a platform."""
    service = CRMService(location_id)
    try:
        service.update_config(platform, config.dict(exclude_unset=True))
        return {"message": f"{platform} configuration updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{location_id}/sync/{contact_id}")
async def sync_lead(location_id: str, contact_id: str):
    """Manually trigger lead sync to external CRMs."""
    service = CRMService(location_id)
    # In a real app, we'd fetch contact data from GHL or memory first
    mock_contact_data = {
        "id": contact_id,
        "first_name": "Test",
        "email": "test@example.com",
    }
    results = await service.sync_lead(mock_contact_data)
    return {"contact_id": contact_id, "results": results}
