"""
GoHighLevel (GHL) API service for Real Estate AI.

Handles all interactions with GHL API including:
- Sending messages to contacts
- Managing contact tags
- Retrieving conversation history
- Notifying agents

Authentication uses GHL API key and location ID from environment variables.
"""
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.config import settings


class GHLService:
    """
    Service for interacting with GoHighLevel API.

    Provides methods for messaging, tagging, and conversation management.
    """

    def __init__(self):
        """Initialize GHL service with API credentials."""
        self.api_key = settings.ghl_api_key
        self.location_id = settings.ghl_location_id
        self.base_url = "https://rest.gohighlevel.com/v1"

        # HTTP client with timeout and retry configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.webhook_timeout_seconds),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

    async def send_message(self, contact_id: str, message: str, message_type: str = "SMS") -> Dict[str, Any]:
        """
        Send message to contact via GHL.

        Args:
            contact_id: GHL contact ID
            message: Message content to send
            message_type: Type of message ("SMS", "Email", "Chat")

        Returns:
            Message send result from GHL API

        Raises:
            httpx.HTTPError: If API request fails
        """
        endpoint = f"{self.base_url}/conversations/messages"

        payload = {
            "type": message_type.lower(),
            "contactId": contact_id,
            "message": message,
            "locationId": self.location_id
        }

        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()

            return {
                "success": True,
                "message_id": response.json().get("id"),
                "sent_at": datetime.now().isoformat()
            }

        except httpx.HTTPError as e:
            print(f"Error sending message to {contact_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "contact_id": contact_id
            }

    async def add_tag(self, contact_id: str, tag: str) -> bool:
        """
        Add tag to contact.

        Args:
            contact_id: GHL contact ID
            tag: Tag to add

        Returns:
            True if tag was added successfully
        """
        endpoint = f"{self.base_url}/contacts/{contact_id}/tags"

        payload = {
            "tags": [tag]
        }

        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()
            return True

        except httpx.HTTPError as e:
            print(f"Error adding tag '{tag}' to {contact_id}: {str(e)}")
            return False

    async def remove_tag(self, contact_id: str, tag: str) -> bool:
        """
        Remove tag from contact.

        Args:
            contact_id: GHL contact ID
            tag: Tag to remove

        Returns:
            True if tag was removed successfully
        """
        endpoint = f"{self.base_url}/contacts/{contact_id}/tags"

        payload = {
            "tags": [tag]
        }

        try:
            response = await self.client.delete(endpoint, json=payload)
            response.raise_for_status()
            return True

        except httpx.HTTPError as e:
            print(f"Error removing tag '{tag}' from {contact_id}: {str(e)}")
            return False

    async def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get contact information from GHL.

        Args:
            contact_id: GHL contact ID

        Returns:
            Contact data or None if not found
        """
        endpoint = f"{self.base_url}/contacts/{contact_id}"

        try:
            response = await self.client.get(endpoint)
            response.raise_for_status()
            return response.json().get("contact")

        except httpx.HTTPError as e:
            print(f"Error getting contact {contact_id}: {str(e)}")
            return None

    async def get_conversation_history(self, contact_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent conversation history for contact.

        Args:
            contact_id: GHL contact ID
            limit: Maximum number of messages to retrieve

        Returns:
            List of messages in chronological order
        """
        endpoint = f"{self.base_url}/conversations/search"

        params = {
            "contactId": contact_id,
            "locationId": self.location_id,
            "limit": limit
        }

        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()

            conversations = response.json().get("conversations", [])
            if not conversations:
                return []

            # Get messages from the most recent conversation
            conversation_id = conversations[0].get("id")
            return await self.get_conversation_messages(conversation_id, limit)

        except httpx.HTTPError as e:
            print(f"Error getting conversation history for {contact_id}: {str(e)}")
            return []

    async def get_conversation_messages(self, conversation_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get messages from a specific conversation.

        Args:
            conversation_id: GHL conversation ID
            limit: Maximum number of messages

        Returns:
            List of messages with metadata
        """
        endpoint = f"{self.base_url}/conversations/{conversation_id}/messages"

        params = {
            "limit": limit
        }

        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()

            messages = response.json().get("messages", [])

            # Format messages for easier processing
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": msg.get("id"),
                    "body": msg.get("body", ""),
                    "direction": msg.get("direction"),  # "inbound" or "outbound"
                    "type": msg.get("type"),  # "SMS", "Email", etc.
                    "timestamp": msg.get("dateAdded"),
                    "contact_id": msg.get("contactId")
                })

            # Sort by timestamp (oldest first for conversation flow)
            formatted_messages.sort(key=lambda x: x.get("timestamp", ""))

            return formatted_messages

        except httpx.HTTPError as e:
            print(f"Error getting messages for conversation {conversation_id}: {str(e)}")
            return []

    async def notify_agent(self, contact_id: str, message: str) -> bool:
        """
        Send notification to agent about qualified lead.

        Args:
            contact_id: GHL contact ID
            message: Notification message

        Returns:
            True if notification was sent successfully
        """
        # Get contact info for agent notification
        contact = await self.get_contact(contact_id)
        if not contact:
            return False

        contact_name = contact.get("firstName", "Unknown") + " " + contact.get("lastName", "")
        contact_phone = contact.get("phone", "No phone")

        notification_text = f"""
🔥 HOT LEAD QUALIFIED!

Contact: {contact_name}
Phone: {contact_phone}
Contact ID: {contact_id}

{message}

Action Required: Follow up immediately!
        """.strip()

        # Send notification via SMS to default agent
        # In production, this should use agent's phone number from settings
        agent_phone = settings.default_agent_phone

        try:
            # Use GHL to send SMS notification to agent
            # This assumes agent has a contact record in GHL
            # Alternative: Use external SMS service (Twilio, etc.)

            # For now, log the notification (in production, implement SMS)
            print(f"AGENT NOTIFICATION: {notification_text}")

            # TODO: Implement actual SMS notification to agent
            # await self.send_sms_to_agent(agent_phone, notification_text)

            return True

        except Exception as e:
            print(f"Error notifying agent about {contact_id}: {str(e)}")
            return False

    async def update_contact_custom_field(self, contact_id: str, field_name: str, value: str) -> bool:
        """
        Update custom field on contact.

        Args:
            contact_id: GHL contact ID
            field_name: Custom field name (e.g., "lead_score", "ai_qualification_status")
            value: Field value

        Returns:
            True if field was updated successfully
        """
        endpoint = f"{self.base_url}/contacts/{contact_id}"

        payload = {
            "customFields": [
                {
                    "key": field_name,
                    "field_value": value
                }
            ]
        }

        try:
            response = await self.client.put(endpoint, json=payload)
            response.raise_for_status()
            return True

        except httpx.HTTPError as e:
            print(f"Error updating custom field '{field_name}' for {contact_id}: {str(e)}")
            return False

    async def create_opportunity(self, contact_id: str, pipeline_id: str, stage_id: str, value: Optional[int] = None) -> Optional[str]:
        """
        Create opportunity in GHL pipeline for qualified lead.

        Args:
            contact_id: GHL contact ID
            pipeline_id: GHL pipeline ID
            stage_id: Pipeline stage ID
            value: Optional opportunity value

        Returns:
            Opportunity ID if created successfully, None otherwise
        """
        endpoint = f"{self.base_url}/pipelines/{pipeline_id}/opportunities"

        payload = {
            "title": "AI Qualified Lead",
            "contactId": contact_id,
            "stageId": stage_id,
            "status": "open"
        }

        if value:
            payload["value"] = value

        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()

            opportunity = response.json().get("opportunity", {})
            return opportunity.get("id")

        except httpx.HTTPError as e:
            print(f"Error creating opportunity for {contact_id}: {str(e)}")
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def __del__(self):
        """Cleanup on deletion."""
        # Note: This may not always be called, prefer explicit close()
        try:
            asyncio.create_task(self.close())
        except RuntimeError:
            pass  # Event loop may already be closed