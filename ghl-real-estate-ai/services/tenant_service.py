"""
Tenant Service for GHL Real Estate AI.

Manages multi-tenancy by storing and retrieving API keys per GHL Location.
Ensures each team is charged on their own account.
"""
import json
from typing import Dict, Any, Optional
from pathlib import Path

from ghl_utils.config import settings
from ghl_utils.logger import get_logger

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

        Args:
            location_id: GHL location ID

        Returns:
            Tenant configuration dict (keys: anthropic_api_key, ghl_api_key)
        """
        file_path = self._get_file_path(location_id)
        
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read tenant file for {location_id}: {e}")
        
        # Fallback to default credentials from settings if this is the primary account
        if location_id == settings.ghl_location_id:
            return {
                "location_id": settings.ghl_location_id,
                "anthropic_api_key": settings.anthropic_api_key,
                "ghl_api_key": settings.ghl_api_key
            }
            
        return {}

    async def save_tenant_config(
        self, 
        location_id: str, 
        anthropic_api_key: str, 
        ghl_api_key: str
    ) -> None:
        """
        Save/Update configuration for a tenant.

        Args:
            location_id: GHL location ID
            anthropic_api_key: Their Anthropic API key
            ghl_api_key: Their GHL API key
        """
        config = {
            "location_id": location_id,
            "anthropic_api_key": anthropic_api_key,
            "ghl_api_key": ghl_api_key
        }
        
        file_path = self._get_file_path(location_id)
        try:
            with open(file_path, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved tenant config for {location_id}")
        except Exception as e:
            logger.error(f"Failed to save tenant file for {location_id}: {e}")

    async def is_tenant_active(self, location_id: str) -> bool:
        """Check if a tenant has active configuration."""
        if location_id == settings.ghl_location_id:
            return True
        return self._get_file_path(location_id).exists()
