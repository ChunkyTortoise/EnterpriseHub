"""
Tenant Service for GHL Real Estate AI.

Manages multi-tenancy by storing and retrieving API keys per GHL Location.
Ensures each team is charged on their own account.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional

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
        SECURITY: NO LONGER exposes primary account keys via webhook access.
        """
        file_path = self._get_file_path(location_id)

        # 1. Check for specific tenant file (explicit registration required)
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    config = json.load(f)
                    logger.info(
                        f"Loaded tenant config for location {location_id}",
                        extra={
                            "has_api_keys": "anthropic_api_key" in config,
                            "is_registered": True
                        }
                    )
                    return config
            except json.JSONDecodeError as e:
                logger.error(
                    f"Tenant config file corrupted for {location_id}: {e}",
                    extra={"error_id": "TENANT_CONFIG_CORRUPT"}
                )
                raise ValueError(f"Invalid tenant configuration for {location_id}")
            except Exception as e:
                logger.error(
                    f"Failed to read tenant config for {location_id}: {e}",
                    extra={"error_id": "TENANT_CONFIG_READ_ERROR"}
                )
                raise ValueError(f"Cannot load tenant configuration")

        # SECURITY FIX: Never fall back to primary account credentials via webhook
        # This prevents attackers from using Jorge's location_id to steal his API keys
        # If this is truly Jorge's primary location calling via webhook, it should
        # have an explicit tenant config file created during setup

        logger.warning(
            f"No tenant config found for location {location_id} - rejecting request",
            extra={
                "error_id": "TENANT_NOT_REGISTERED",
                "location_id": location_id,
                "primary_location": settings.ghl_location_id
            }
        )

        # SECURITY: Return empty config instead of exposing credentials
        # This forces explicit tenant registration for all sub-accounts
        return {}

    async def save_tenant_config(
        self,
        location_id: str,
        anthropic_api_key: str,
        ghl_api_key: str,
        ghl_calendar_id: Optional[str] = None,
    ) -> None:
        """Save/Update configuration for a specific tenant (sub-account)."""
        config = {
            "location_id": location_id,
            "anthropic_api_key": anthropic_api_key,
            "ghl_api_key": ghl_api_key,
            "ghl_calendar_id": ghl_calendar_id,
            "updated_at": datetime.now(UTC).isoformat(),
        }

        file_path = self._get_file_path(location_id)
        with open(file_path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved tenant config for {location_id}")

    async def register_tenant_config(
        self,
        location_id: str,
        anthropic_api_key: str,
        ghl_api_key: str,
        ghl_calendar_id: Optional[str] = None,
        *,
        overwrite: bool = False,
    ) -> Literal["created", "updated", "unchanged"]:
        """
        Register tenant config with duplicate-safe idempotency guard.

        Returns:
            "created" when a new config is written,
            "updated" when an existing config is replaced with overwrite=True,
            "unchanged" when the same config is already present.
        Raises:
            ValueError when a conflicting config exists and overwrite=False.
        """
        file_path = self._get_file_path(location_id)
        requested = {
            "location_id": location_id,
            "anthropic_api_key": anthropic_api_key,
            "ghl_api_key": ghl_api_key,
            "ghl_calendar_id": ghl_calendar_id,
        }

        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    existing = json.load(f)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid tenant configuration for {location_id}") from exc

            existing_core = {
                "location_id": existing.get("location_id"),
                "anthropic_api_key": existing.get("anthropic_api_key"),
                "ghl_api_key": existing.get("ghl_api_key"),
                "ghl_calendar_id": existing.get("ghl_calendar_id"),
            }
            if existing_core == requested:
                logger.info(f"Tenant config already registered for {location_id}; no changes applied")
                return "unchanged"

            if not overwrite:
                raise ValueError(
                    f"tenant config already exists for {location_id}. Use --force to overwrite."
                )

            await self.save_tenant_config(
                location_id=location_id,
                anthropic_api_key=anthropic_api_key,
                ghl_api_key=ghl_api_key,
                ghl_calendar_id=ghl_calendar_id,
            )
            return "updated"

        await self.save_tenant_config(
            location_id=location_id,
            anthropic_api_key=anthropic_api_key,
            ghl_api_key=ghl_api_key,
            ghl_calendar_id=ghl_calendar_id,
        )
        return "created"

    async def save_agency_config(self, agency_id: str, api_key: str) -> None:
        """Save master agency credentials."""
        config = {
            "agency_id": agency_id,
            "agency_api_key": api_key,
            "updated_at": datetime.now(UTC).isoformat(),
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
