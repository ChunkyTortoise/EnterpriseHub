"""
GHL Service Wrapper - Interface for Churn Prediction System
"""

import logging
from typing import Dict, Any
from .ghl_client import GHLClient

logger = logging.getLogger(__name__)

class GHLService:
    """
    Wrapper for GHLClient to provide the specific interface expected by the churn system.
    """
    def __init__(self, ghl_client: GHLClient = None):
        self.client = ghl_client or GHLClient()

    async def trigger_workflow(self, contact_id: str, workflow_id: str, custom_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Trigger a workflow for a contact in GHL.
        
        Args:
            contact_id: GHL contact ID
            workflow_id: GHL workflow ID to trigger
            custom_data: Optional data to pass to the workflow (mapped to custom fields if possible)
            
        Returns:
            API response dict
        """
        logger.info(f"Triggering GHL workflow {workflow_id} for contact {contact_id}")
        
        # If custom_data is provided, we might want to update custom fields first
        if custom_data:
            for field_id, value in custom_data.items():
                try:
                    await self.client.update_custom_field(contact_id, field_id, value)
                except Exception as e:
                    logger.error(f"Failed to update custom field {field_id}: {e}")

        return await self.client.trigger_workflow(contact_id, workflow_id)

    async def get_contacts(self, **kwargs) -> Dict[str, Any]:
        """Fetch contacts from GHL."""
        # Use search_contacts since GHLClient has that
        contacts = await self.client.search_contacts(
            query=kwargs.get("query", ""),
            limit=kwargs.get("limit", 50)
        )
        return {"contacts": contacts}

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Fetch a single contact from GHL."""
        return await self.client.get_contact(contact_id)

    async def get_conversations(self, **kwargs) -> Dict[str, Any]:
        """Fetch conversations from GHL."""
        conversations = await self.client.get_conversations(
            limit=kwargs.get("limit", 20),
            contact_id=kwargs.get("contact_id")
        )
        return {"conversations": conversations}

    async def health_check(self) -> bool:
        """
        Check if the service is healthy.
        """
        response = self.client.check_health()
        return response.status_code == 200
