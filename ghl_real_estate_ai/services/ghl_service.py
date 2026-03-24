"""DEPRECATED: GHL Service Wrapper.

This module is deprecated. New code should use GHLClient or EnhancedGHLClient
directly from ghl_real_estate_ai.services.ghl_client.

GHLService is kept as a compatibility shim for 11 existing callers across
churn, analytics, ML, and demo modules. These will be migrated incrementally.
"""

import logging
import warnings
from typing import Any, Dict

from ghl_real_estate_ai.models.ghl_webhook_types import GHLAPIResponse

from .ghl_client import GHLClient

logger = logging.getLogger(__name__)


class GHLService:
    """Deprecated thin wrapper around GHLClient. Use GHLClient directly."""

    def __init__(self, ghl_client: GHLClient = None):
        warnings.warn(
            "GHLService is deprecated. Use GHLClient or EnhancedGHLClient directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.client = ghl_client or GHLClient()

    async def trigger_workflow(
        self, contact_id: str, workflow_id: str, custom_data: Dict[str, Any] = None
    ) -> GHLAPIResponse:
        if custom_data:
            try:
                await self.client.update_custom_fields_batch(contact_id, custom_data)
            except Exception as e:
                logger.error(f"Failed to batch-update custom fields: {e}")
        return await self.client.trigger_workflow(contact_id, workflow_id)

    async def get_contacts(self, **kwargs) -> Dict[str, Any]:
        contacts = await self.client.search_contacts(
            query=kwargs.get("query", ""), limit=kwargs.get("limit", 50)
        )
        return {"contacts": contacts}

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        return await self.client.get_contact(contact_id)

    async def get_conversations(self, **kwargs) -> Dict[str, Any]:
        conversations = await self.client.get_conversations(
            limit=kwargs.get("limit", 20), contact_id=kwargs.get("contact_id")
        )
        return {"conversations": conversations}

    async def health_check(self) -> bool:
        response = await self.client.check_health()
        return response.status_code == 200
