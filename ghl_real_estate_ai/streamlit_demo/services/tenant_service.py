"""
Tenant Service for GHL Real Estate AI.

Manages multi-tenancy by storing and retrieving API keys per GHL Location.
Ensures each team is charged on their own account.
"""
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class TenantService:
    """
    Service for managing tenant-specific credentials.
    """

    def __init__(self):
        """Initialize tenant service with file storage."""
        self.tenants_dir = Path("data/tenants")
        self.tenants_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Tenant service initialized with storage at {self.tenants_dir}")

    def _get_file_path(self, location_id: str) -> Path:
        """Get file path for a location's tenant info."""
        return self.tenants_dir / f"{location_id}.json"

    async def get_tenant_config(self, location_id: str) -> Dict[str, Any]:
        """
        Retrieve configuration for a tenant.
        Fallbacks: Specific File -> Default Settings -> Agency Master Key.
        """
        file_path = self._get_file_path(location_id)
        
        # 1. Check for specific tenant file
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read tenant file for {location_id}: {e}")
        
        # 2. Fallback to default credentials from settings if this is the primary account
        if location_id == settings.ghl_location_id:
            return {
                "location_id": settings.ghl_location_id,
                "anthropic_api_key": settings.anthropic_api_key,
                "ghl_api_key": settings.ghl_api_key
            }
            
        # 3. Fallback to Agency Master Key (Jorge's Requirement)
        if settings.ghl_agency_api_key:
            logger.info(f"Using Agency Master Key for location {location_id}")
            return {
                "location_id": location_id,
                "anthropic_api_key": settings.anthropic_api_key,
                "ghl_api_key": settings.ghl_agency_api_key,
                "is_agency_scoped": True
            }
            
        return {}

    async def save_tenant_config(
        self,
        location_id: str,
        anthropic_api_key: str,
        ghl_api_key: str,
        ghl_calendar_id: Optional[str] = None
    ) -> None:
        """Save/Update configuration for a specific tenant (sub-account)."""
        config = {
            "location_id": location_id,
            "anthropic_api_key": anthropic_api_key,
            "ghl_api_key": ghl_api_key,
            "ghl_calendar_id": ghl_calendar_id,
            "updated_at": datetime.utcnow().isoformat()
        }

        file_path = self._get_file_path(location_id)
        with open(file_path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved tenant config for {location_id}")

    async def save_agency_config(self, agency_id: str, api_key: str) -> None:
        """Save master agency credentials."""
        config = {
            "agency_id": agency_id,
            "agency_api_key": api_key,
            "updated_at": datetime.utcnow().isoformat()
        }
        file_path = self.tenants_dir / "agency_master.json"
        with open(file_path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved Agency Master config for {agency_id}")

    async def is_tenant_active(self, location_id: str) -> bool:
        """Check if a tenant has active configuration (including agency fallback)."""
        if location_id == settings.ghl_location_id:
            return True
        if self._get_file_path(location_id).exists():
            return True
        return settings.ghl_agency_api_key is not None
