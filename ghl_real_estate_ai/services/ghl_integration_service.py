"""
GHL Integration Service (V2)
Bridges V2 Agents with GoHighLevel for lead retrieval and campaign triggering.
"""

import logging
from typing import List, Dict, Any, Optional
from .ghl_client import GHLClient

logger = logging.getLogger(__name__)

class GHLIntegrationService:
    def __init__(self, ghl_client: Optional[GHLClient] = None):
        self.client = ghl_client or GHLClient()

    async def get_mock_leads(self) -> List[Dict[str, Any]]:
        """Return a list of mock leads for demonstration purposes."""
        return [
            {
                "id": "contact_001",
                "first_name": "John",
                "last_name": "Investor",
                "email": "john@example.com",
                "phone": "+155501001",
                "preferences": ["luxury", "multifamily", "austin"],
                "budget": 2000000,
                "tags": ["Investor", "Hot Lead"]
            },
            {
                "id": "contact_002",
                "first_name": "Jane",
                "last_name": "Flipper",
                "email": "jane@example.com",
                "phone": "+155501002",
                "preferences": ["distressed", "single-family", "san-antonio"],
                "budget": 500000,
                "tags": ["Flipper"]
            },
            {
                "id": "contact_003",
                "first_name": "Bob",
                "last_name": "Builder",
                "email": "bob@example.com",
                "phone": "+155501003",
                "preferences": ["land", "development", "houston"],
                "budget": 5000000,
                "tags": ["Developer"]
            },
            {
                "id": "contact_004",
                "first_name": "Sarah",
                "last_name": "FirstHome",
                "email": "sarah@example.com",
                "phone": "+155501004",
                "preferences": ["residential", "modern", "austin"],
                "budget": 450000,
                "tags": ["First Time Buyer"]
            }
        ]

    async def get_active_leads(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch active leads from GHL (falls back to mock if API fails)."""
        try:
            contacts = await self.client.search_contacts(limit=limit)
            if not contacts:
                return await self.get_mock_leads()
            return contacts
        except Exception as e:
            logger.error(f"Error fetching GHL contacts: {e}")
            return await self.get_mock_leads()

    async def trigger_marketing_campaign(self, contact_id: str, campaign_data: Dict[str, Any]) -> bool:
        """Trigger a GHL workflow or send a message with marketing copy."""
        logger.info(f"Triggering GHL campaign for {contact_id}")
        
        message = campaign_data.get("sms_copy") or campaign_data.get("email_body")
        if not message:
            return False
            
        try:
            # In a real scenario, we might trigger a specific workflow
            # await self.client.trigger_workflow(contact_id, "marketing_automation_id")
            # For this demo, we'll just log the message sending
            await self.client.send_message(contact_id, message)
            return True
        except Exception as e:
            logger.error(f"Failed to send GHL campaign: {e}")
            return False

ghl_integration_service = GHLIntegrationService()
