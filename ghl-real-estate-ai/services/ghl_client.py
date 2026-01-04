"""
GoHighLevel API client.

Handles communication with GHL API for:
- Sending messages (SMS, email)
- Updating contact tags
- Updating custom fields
- Triggering workflows

API Documentation: https://highlevel.stoplight.io/
"""
import httpx
from typing import List, Dict, Any, Optional
from api.schemas.ghl import MessageType, GHLAction, ActionType
from ghl_utils.config import settings
from ghl_utils.logger import get_logger

logger = get_logger(__name__)


class GHLClient:
    """Client for interacting with GoHighLevel API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        location_id: Optional[str] = None
    ):
        """
        Initialize GHL API client.

        Args:
            api_key: GHL API key (defaults to settings)
            location_id: GHL location ID (defaults to settings)
        """
        self.api_key = api_key or settings.ghl_api_key
        self.location_id = location_id or settings.ghl_location_id
        self.base_url = "https://services.leadconnectorhq.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }

    async def send_message(
        self,
        contact_id: str,
        message: str,
        channel: MessageType = MessageType.SMS
    ) -> Dict[str, Any]:
        """
        Send a message to a contact via SMS or email.

        Args:
            contact_id: GHL contact ID
            message: Message content
            channel: Communication channel (SMS, Email, Live_Chat)

        Returns:
            API response dict

        Raises:
            httpx.HTTPError: If API request fails
        """
        if settings.test_mode:
            logger.info(
                f"[TEST MODE] Would send {channel.value} message to {contact_id}: {message}",
                extra={"contact_id": contact_id, "test_mode": True}
            )
            return {"status": "mocked", "messageId": "mock_msg_123"}

        endpoint = f"{self.base_url}/conversations/messages"

        payload = {
            "type": channel.value,
            "contactId": contact_id,
            "locationId": self.location_id,
            "message": message
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds
                )
                response.raise_for_status()

                logger.info(
                    f"Sent {channel.value} message to contact {contact_id}",
                    extra={"contact_id": contact_id, "channel": channel.value}
                )

                return response.json()

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to send message to contact {contact_id}: {str(e)}",
                extra={"contact_id": contact_id, "error": str(e)}
            )
            raise

    async def add_tags(
        self,
        contact_id: str,
        tags: List[str]
    ) -> Dict[str, Any]:
        """
        Returns:
            API response dict
        """
        if settings.test_mode:
            logger.info(
                f"[TEST MODE] Would add tags to {contact_id}: {tags}",
                extra={"contact_id": contact_id, "test_mode": True}
            )
            return {"status": "mocked", "tags": tags}

        endpoint = f"{self.base_url}/contacts/{contact_id}"

        payload = {
            "tags": tags
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds
                )
                response.raise_for_status()

                logger.info(
                    f"Added tags to contact {contact_id}: {tags}",
                    extra={"contact_id": contact_id, "tags": tags}
                )

                return response.json()

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to add tags to contact {contact_id}: {str(e)}",
                extra={"contact_id": contact_id, "error": str(e)}
            )
            raise

    async def remove_tags(
        self,
        contact_id: str,
        tags: List[str]
    ) -> Dict[str, Any]:
        """
        Remove tags from a contact.

        Args:
            contact_id: GHL contact ID
            tags: List of tag names to remove

        Returns:
            API response dict
        """
        # GHL API doesn't have a dedicated remove tags endpoint
        # We need to fetch current tags, remove specified ones, and update
        logger.warning(
            "Tag removal requires fetching current tags first",
            extra={"contact_id": contact_id}
        )

        # For now, log the intent - implement full logic when needed
        logger.info(
            f"Would remove tags from contact {contact_id}: {tags}",
            extra={"contact_id": contact_id, "tags": tags}
        )

        return {"message": "Tag removal logged (not implemented)"}

    async def update_custom_field(
        self,
        contact_id: str,
        field_id: str,
        value: Any
    ) -> Dict[str, Any]:
        """
        Update a custom field on a contact.

        Args:
            contact_id: GHL contact ID
            field_id: Custom field ID
            value: New value for the field

        Returns:
            API response dict
        """
        if settings.test_mode:
            logger.info(
                f"[TEST MODE] Would update custom field {field_id} for {contact_id} to {value}",
                extra={"contact_id": contact_id, "test_mode": True}
            )
            return {"status": "mocked", "field_id": field_id, "value": value}

        endpoint = f"{self.base_url}/contacts/{contact_id}"

        payload = {
            "customFields": [
                {
                    "id": field_id,
                    "value": str(value)
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds
                )
                response.raise_for_status()

                logger.info(
                    f"Updated custom field {field_id} for contact {contact_id}",
                    extra={"contact_id": contact_id, "field_id": field_id}
                )

                return response.json()

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to update custom field for contact {contact_id}: {str(e)}",
                extra={"contact_id": contact_id, "error": str(e)}
            )
            raise

    async def trigger_workflow(
        self,
        contact_id: str,
        workflow_id: str
    ) -> Dict[str, Any]:
        """
        Trigger a workflow for a contact.

        Args:
            contact_id: GHL contact ID
            workflow_id: GHL workflow ID to trigger

        Returns:
            API response dict
        """
        if settings.test_mode:
            logger.info(
                f"[TEST MODE] Would trigger workflow {workflow_id} for {contact_id}",
                extra={"contact_id": contact_id, "test_mode": True}
            )
            return {"status": "mocked", "workflow_id": workflow_id}

        endpoint = f"{self.base_url}/workflows/{workflow_id}/trigger"

        payload = {
            "contactId": contact_id
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds
                )
                response.raise_for_status()

                logger.info(
                    f"Triggered workflow {workflow_id} for contact {contact_id}",
                    extra={"contact_id": contact_id, "workflow_id": workflow_id}
                )

                return response.json()

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to trigger workflow for contact {contact_id}: {str(e)}",
                extra={"contact_id": contact_id, "error": str(e)}
            )
            raise

    async def get_available_slots(
        self,
        calendar_id: str,
        start_date: str,
        end_date: str,
        timezone: str = "America/New_York"
    ) -> List[Dict[str, Any]]:
        """
        Fetch available time slots from GHL calendar.
        
        Args:
            calendar_id: GHL calendar ID
            start_date: ISO format date or timestamp
            end_date: ISO format date or timestamp
            timezone: Timezone for slots
            
        Returns:
            List of available slots
        """
        if settings.test_mode:
            logger.info(
                f"[TEST MODE] Fetching slots for calendar {calendar_id} from {start_date} to {end_date}",
                extra={"calendar_id": calendar_id, "test_mode": True}
            )
            return [
                {"start_time": f"{start_date}T10:00:00Z"},
                {"start_time": f"{start_date}T14:00:00Z"},
                {"start_time": f"{start_date}T16:00:00Z"}
            ]

        endpoint = f"{self.base_url}/calendars/{calendar_id}/free-slots"
        
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "timezone": timezone
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    params=params,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds
                )
                response.raise_for_status()
                
                data = response.json()
                # GHL usually returns slots in a dict under 'slots' or directly
                slots = data.get("slots", []) if isinstance(data, dict) else []
                
                return slots

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to fetch calendar slots: {str(e)}",
                extra={"calendar_id": calendar_id, "error": str(e)}
            )
            return []

    async def apply_actions(
        self,
        contact_id: str,
        actions: List[GHLAction]
    ) -> List[Dict[str, Any]]:
        """
        Apply multiple actions to a contact.

        Args:
            contact_id: GHL contact ID
            actions: List of GHLAction objects

        Returns:
            List of API response dicts
        """
        results = []

        for action in actions:
            try:
                if action.type == ActionType.SEND_MESSAGE and action.message and action.channel:
                    result = await self.send_message(
                        contact_id,
                        action.message,
                        action.channel
                    )
                    results.append(result)

                elif action.type == ActionType.ADD_TAG and action.tag:
                    result = await self.add_tags(contact_id, [action.tag])
                    results.append(result)

                elif action.type == ActionType.REMOVE_TAG and action.tag:
                    result = await self.remove_tags(contact_id, [action.tag])
                    results.append(result)

                elif action.type == ActionType.UPDATE_CUSTOM_FIELD and action.field and action.value is not None:
                    result = await self.update_custom_field(
                        contact_id,
                        action.field,
                        action.value
                    )
                    results.append(result)

                elif action.type == ActionType.TRIGGER_WORKFLOW and action.workflow_id:
                    result = await self.trigger_workflow(
                        contact_id,
                        action.workflow_id
                    )
                    results.append(result)

            except Exception as e:
                logger.error(
                    f"Failed to apply action {action.type}: {str(e)}",
                    extra={"contact_id": contact_id, "action_type": action.type, "error": str(e)}
                )
                # Continue with other actions even if one fails
                results.append({"error": str(e), "action": action.type})

        return results
