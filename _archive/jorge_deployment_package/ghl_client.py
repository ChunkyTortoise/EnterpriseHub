#!/usr/bin/env python3
"""
Standalone GHL Client for Jorge's Bot System

This is a self-contained GoHighLevel API client with all the methods
needed for Jorge's lead and seller bots.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GHLClient:
    """
    Standalone GoHighLevel API client for Jorge's bot system.

    Provides all necessary methods for:
    - Contact management
    - Conversation handling
    - Tag management
    - Custom field updates
    - Workflow triggering
    - Calendar appointments
    """

    def __init__(self, access_token: Optional[str] = None):
        """Initialize GHL client with access token"""

        self.access_token = access_token or os.getenv("GHL_ACCESS_TOKEN")
        self.base_url = "https://services.leadconnectorhq.com"

        if not self.access_token:
            raise ValueError("GHL_ACCESS_TOKEN is required")

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        self.logger = logging.getLogger(__name__)

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get contact information from GHL"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/contacts/{contact_id}",
                    headers=self.headers
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.error(f"Failed to get contact {contact_id}: {response.status_code}")
                    return {}

        except Exception as e:
            self.logger.error(f"Error getting contact {contact_id}: {e}")
            return {}

    async def update_contact(self, contact_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update contact information in GHL"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/contacts/{contact_id}",
                    headers=self.headers,
                    json=data
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.error(f"Failed to update contact {contact_id}: {response.status_code}")
                    return {}

        except Exception as e:
            self.logger.error(f"Error updating contact {contact_id}: {e}")
            return {}

    async def add_tag(self, contact_id: str, tag: str) -> bool:
        """Add tag to contact"""

        try:
            data = {"tags": [tag]}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/contacts/{contact_id}/tags",
                    headers=self.headers,
                    json=data
                )

                success = response.status_code in [200, 201]
                if not success:
                    self.logger.error(f"Failed to add tag {tag} to contact {contact_id}: {response.status_code}")

                return success

        except Exception as e:
            self.logger.error(f"Error adding tag {tag} to contact {contact_id}: {e}")
            return False

    async def remove_tag(self, contact_id: str, tag: str) -> bool:
        """Remove tag from contact"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/contacts/{contact_id}/tags/{tag}",
                    headers=self.headers
                )

                success = response.status_code in [200, 204]
                if not success:
                    self.logger.error(f"Failed to remove tag {tag} from contact {contact_id}: {response.status_code}")

                return success

        except Exception as e:
            self.logger.error(f"Error removing tag {tag} from contact {contact_id}: {e}")
            return False

    async def update_custom_field(self, contact_id: str, field_id: str, value: str) -> bool:
        """Update custom field for contact"""

        try:
            data = {
                "customFields": [
                    {
                        "id": field_id,
                        "value": value
                    }
                ]
            }

            result = await self.update_contact(contact_id, data)
            return bool(result)

        except Exception as e:
            self.logger.error(f"Error updating custom field {field_id} for contact {contact_id}: {e}")
            return False

    async def send_message(self, contact_id: str, message: str, message_type: str = "SMS") -> Dict[str, Any]:
        """Send message to contact via GHL"""

        try:
            data = {
                "contactId": contact_id,
                "message": message,
                "type": message_type
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/conversations/messages",
                    headers=self.headers,
                    json=data
                )

                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    self.logger.error(f"Failed to send message to contact {contact_id}: {response.status_code}")
                    return {}

        except Exception as e:
            self.logger.error(f"Error sending message to contact {contact_id}: {e}")
            return {}

    async def trigger_workflow(self, contact_id: str, workflow_id: str) -> Dict[str, Any]:
        """Trigger workflow for contact"""

        try:
            data = {
                "contactId": contact_id,
                "workflowId": workflow_id
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/workflows/{workflow_id}/subscribe",
                    headers=self.headers,
                    json=data
                )

                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    self.logger.error(f"Failed to trigger workflow {workflow_id} for contact {contact_id}: {response.status_code}")
                    return {}

        except Exception as e:
            self.logger.error(f"Error triggering workflow {workflow_id} for contact {contact_id}: {e}")
            return {}

    async def create_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create calendar appointment in GHL"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/calendars/events",
                    headers=self.headers,
                    json=appointment_data
                )

                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    self.logger.error(f"Failed to create appointment: {response.status_code}")
                    return {}

        except Exception as e:
            self.logger.error(f"Error creating appointment: {e}")
            return {}

    async def get_conversations(self, contact_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for contact"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/conversations",
                    headers=self.headers,
                    params={"contactId": contact_id}
                )

                if response.status_code == 200:
                    return response.json().get("conversations", [])
                else:
                    self.logger.error(f"Failed to get conversations for contact {contact_id}: {response.status_code}")
                    return []

        except Exception as e:
            self.logger.error(f"Error getting conversations for contact {contact_id}: {e}")
            return []

    async def apply_actions(self, contact_id: str, actions: List[Dict[str, Any]]) -> bool:
        """Apply multiple actions to a contact"""

        success = True

        for action in actions:
            try:
                action_type = action.get("type")

                if action_type == "add_tag":
                    result = await self.add_tag(contact_id, action["tag"])

                elif action_type == "remove_tag":
                    result = await self.remove_tag(contact_id, action["tag"])

                elif action_type == "update_custom_field":
                    result = await self.update_custom_field(
                        contact_id, action["field"], action["value"]
                    )

                elif action_type == "trigger_workflow":
                    result = await self.trigger_workflow(
                        contact_id, action["workflow_id"]
                    )

                elif action_type == "send_message":
                    result = await self.send_message(
                        contact_id, action["message"]
                    )

                else:
                    self.logger.warning(f"Unknown action type: {action_type}")
                    result = False

                if not result:
                    success = False

            except Exception as e:
                self.logger.error(f"Error applying action {action}: {e}")
                success = False

        return success

    def check_health(self) -> httpx.Response:
        """Check GHL API health (synchronous for health checks)"""

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/locations",
                    headers=self.headers,
                    timeout=5.0
                )
                return response

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            # Return a mock response for health check failure
            class MockResponse:
                status_code = 500
            return MockResponse()


# Factory function for easy instantiation
def create_ghl_client(access_token: Optional[str] = None) -> GHLClient:
    """Create and configure GHL client"""
    return GHLClient(access_token=access_token)