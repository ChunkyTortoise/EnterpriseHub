"""
GoHighLevel API client.

Handles communication with GHL API for:
- Sending messages (SMS, email)
- Updating contact tags
- Updating custom fields
- Triggering workflows

API Documentation: https://highlevel.stoplight.io/
"""

from typing import Any, Dict, List, Optional

import httpx

from ghl_real_estate_ai.api.schemas.ghl import ActionType, GHLAction, MessageType
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class GHLClient:
    """Client for interacting with GoHighLevel API."""

    def __init__(
        self, api_key: Optional[str] = None, location_id: Optional[str] = None
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
            "Version": "2021-07-28",
        }

    def check_health(self):
        """
        Check if GHL API is accessible.
        Synchronous method for Streamlit.
        """
        if settings.test_mode or self.api_key == "dummy":
            # Mock response object
            class MockResponse:
                status_code = 200
            return MockResponse()
        
        # Simple ping to a lightweight endpoint
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/locations/{self.location_id}",
                    headers=self.headers,
                    timeout=5.0
                )
                return response
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            class ErrorResponse:
                status_code = 500
            return ErrorResponse()

    def get_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent conversations from GHL."""
        if settings.test_mode or self.api_key == "dummy":
            return []
            
        endpoint = f"{self.base_url}/conversations/search"
        params = {"locationId": self.location_id, "limit": limit}
        
        try:
            with httpx.Client() as client:
                response = client.get(endpoint, params=params, headers=self.headers)
                response.raise_for_status()
                return response.json().get("conversations", [])
        except Exception as e:
            logger.error(f"Failed to fetch conversations: {e}")
            return []

    def get_opportunities(self) -> List[Dict[str, Any]]:
        """Fetch opportunities (pipeline) from GHL."""
        if settings.test_mode or self.api_key == "dummy":
            return []
            
        endpoint = f"{self.base_url}/opportunities/search"
        params = {"locationId": self.location_id}
        
        try:
            with httpx.Client() as client:
                response = client.get(endpoint, params=params, headers=self.headers)
                response.raise_for_status()
                return response.json().get("opportunities", [])
        except Exception as e:
            logger.error(f"Failed to fetch opportunities: {e}")
            return []

    async def send_message(
        self, contact_id: str, message: str, channel: MessageType = MessageType.SMS
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
                extra={"contact_id": contact_id, "test_mode": True},
            )
            return {"status": "mocked", "messageId": "mock_msg_123"}

        endpoint = f"{self.base_url}/conversations/messages"

        payload = {
            "type": channel.value,
            "contactId": contact_id,
            "locationId": self.location_id,
            "message": message,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds,
                )
                response.raise_for_status()

                logger.info(
                    f"Sent {channel.value} message to contact {contact_id}",
                    extra={"contact_id": contact_id, "channel": channel.value},
                )

                return response.json()

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to send message to contact {contact_id}: {str(e)}",
                extra={"contact_id": contact_id, "error": str(e)},
            )
            raise

    async def add_tags(self, contact_id: str, tags: List[str]) -> Dict[str, Any]:
        """
        Returns:
            API response dict
        """
        if settings.test_mode:
            logger.info(
                f"[TEST MODE] Would add tags to {contact_id}: {tags}",
                extra={"contact_id": contact_id, "test_mode": True},
            )
            return {"status": "mocked", "tags": tags}

        endpoint = f"{self.base_url}/contacts/{contact_id}"

        payload = {"tags": tags}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds,
                )
                response.raise_for_status()

                logger.info(
                    f"Added tags to contact {contact_id}: {tags}",
                    extra={"contact_id": contact_id, "tags": tags},
                )

                return response.json()

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to add tags to contact {contact_id}: {str(e)}",
                extra={"contact_id": contact_id, "error": str(e)},
            )
            raise

    async def remove_tags(self, contact_id: str, tags: List[str]) -> Dict[str, Any]:
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
            extra={"contact_id": contact_id},
        )

        # For now, log the intent - implement full logic when needed
        logger.info(
            f"Would remove tags from contact {contact_id}: {tags}",
            extra={"contact_id": contact_id, "tags": tags},
        )

        return {"message": "Tag removal logged (not implemented)"}

    async def update_custom_field(
        self, contact_id: str, field_id: str, value: Any
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
                extra={"contact_id": contact_id, "test_mode": True},
            )
            return {"status": "mocked", "field_id": field_id, "value": value}

        endpoint = f"{self.base_url}/contacts/{contact_id}"

        payload = {"customFields": [{"id": field_id, "value": str(value)}]}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds,
                )
                response.raise_for_status()

                logger.info(
                    f"Updated custom field {field_id} for contact {contact_id}",
                    extra={"contact_id": contact_id, "field_id": field_id},
                )

                return response.json()

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to update custom field for contact {contact_id}: {str(e)}",
                extra={"contact_id": contact_id, "error": str(e)},
            )
            raise

    async def trigger_workflow(
        self, contact_id: str, workflow_id: str
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
                extra={"contact_id": contact_id, "test_mode": True},
            )
            return {"status": "mocked", "workflow_id": workflow_id}

        endpoint = f"{self.base_url}/workflows/{workflow_id}/trigger"

        payload = {"contactId": contact_id}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds,
                )
                response.raise_for_status()

                logger.info(
                    f"Triggered workflow {workflow_id} for contact {contact_id}",
                    extra={"contact_id": contact_id, "workflow_id": workflow_id},
                )

                return response.json()

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to trigger workflow for contact {contact_id}: {str(e)}",
                extra={"contact_id": contact_id, "error": str(e)},
            )
            raise

    async def get_available_slots(
        self,
        calendar_id: str,
        start_date: str,
        end_date: str,
        timezone: str = "America/New_York",
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
                extra={"calendar_id": calendar_id, "test_mode": True},
            )
            return [
                {"start_time": f"{start_date}T10:00:00Z"},
                {"start_time": f"{start_date}T14:00:00Z"},
                {"start_time": f"{start_date}T16:00:00Z"},
            ]

        endpoint = f"{self.base_url}/calendars/{calendar_id}/free-slots"

        params = {"startDate": start_date, "endDate": end_date, "timezone": timezone}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    params=params,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds,
                )
                response.raise_for_status()

                data = response.json()
                # GHL usually returns slots in a dict under 'slots' or directly
                slots = data.get("slots", []) if isinstance(data, dict) else []

                return slots

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to fetch calendar slots: {str(e)}",
                extra={"calendar_id": calendar_id, "error": str(e)},
            )
            return []

    async def create_appointment(
        self,
        contact_id: str,
        calendar_id: str,
        start_time: str,
        title: str = "AI Assistant Appointment",
        assigned_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an appointment in GHL calendar.

        Args:
            contact_id: GHL contact ID
            calendar_id: GHL calendar ID
            start_time: ISO format start time
            title: Appointment title
            assigned_user_id: Optional user ID to assign

        Returns:
            API response dict
        """
        if settings.test_mode:
            logger.info(
                f"[TEST MODE] Creating appointment for {contact_id} in calendar {calendar_id} at {start_time}",
                extra={
                    "contact_id": contact_id,
                    "calendar_id": calendar_id,
                    "test_mode": True,
                },
            )
            return {
                "status": "mocked",
                "id": "mock_apt_123",
                "startTime": start_time,
                "contactId": contact_id,
            }

        endpoint = f"{self.base_url}/calendars/events/appointments"

        payload = {
            "calendarId": calendar_id,
            "locationId": self.location_id,
            "contactId": contact_id,
            "startTime": start_time,
            "title": title,
            "appointmentStatus": "confirmed",
        }

        if assigned_user_id:
            payload["assignedUserId"] = assigned_user_id

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds,
                )
                response.raise_for_status()

                logger.info(
                    f"Created appointment for contact {contact_id}",
                    extra={"contact_id": contact_id, "calendar_id": calendar_id},
                )

                return response.json()

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to create appointment: {str(e)}",
                extra={
                    "contact_id": contact_id,
                    "calendar_id": calendar_id,
                    "error": str(e),
                },
            )
            raise

    async def apply_actions(
        self, contact_id: str, actions: List[GHLAction]
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
                if (
                    action.type == ActionType.SEND_MESSAGE
                    and action.message
                    and action.channel
                ):
                    result = await self.send_message(
                        contact_id, action.message, action.channel
                    )
                    results.append(result)

                elif action.type == ActionType.ADD_TAG and action.tag:
                    result = await self.add_tags(contact_id, [action.tag])
                    results.append(result)

                elif action.type == ActionType.REMOVE_TAG and action.tag:
                    result = await self.remove_tags(contact_id, [action.tag])
                    results.append(result)

                elif (
                    action.type == ActionType.UPDATE_CUSTOM_FIELD
                    and action.field
                    and action.value is not None
                ):
                    result = await self.update_custom_field(
                        contact_id, action.field, action.value
                    )
                    results.append(result)

                elif action.type == ActionType.TRIGGER_WORKFLOW and action.workflow_id:
                    result = await self.trigger_workflow(contact_id, action.workflow_id)
                    results.append(result)

            except Exception as e:
                logger.error(
                    f"Failed to apply action {action.type}: {str(e)}",
                    extra={
                        "contact_id": contact_id,
                        "action_type": action.type,
                        "error": str(e),
                    },
                )
                # Continue with other actions even if one fails
                results.append({"error": str(e), "action": action.type})

        return results

    def fetch_dashboard_data(self) -> dict:
        """
        Fetch real-time dashboard data from GHL API.
        
        This method replaces mock data with live CRM data for:
        - Active conversations
        - Pipeline opportunities
        - Revenue metrics
        - Lead activity feed
        
        Returns:
            dict: Dashboard data matching mock_analytics.json structure
        """
        if settings.test_mode or self.api_key == "dummy":
            return {
                "system_health": {
                    "uptime_percentage": 99.9,
                    "avg_response_time_ms": 145,
                    "sms_compliance_rate": 0.98
                },
                "conversations": [],
                "revenue": {"total": 0},
                "is_mock": True
            }

        try:
            logger.info("Fetching live dashboard data from GHL API")
            
            # Fetch conversations (last 50)
            conversations = self.get_conversations(limit=50)
            
            # Fetch opportunities (pipeline)
            opportunities = self.get_opportunities()
            
            # Calculate revenue metrics
            total_pipeline = sum(
                float(opp.get("monetary_value", 0) or 0) 
                for opp in opportunities
            )
            
            won_deals = [
                opp for opp in opportunities 
                if opp.get("status") == "won"
            ]
            total_revenue = sum(
                float(deal.get("monetary_value", 0) or 0) 
                for deal in won_deals
            )
            
            # Calculate conversion rate
            total_leads = len(conversations)
            qualified_leads = len([
                c for c in conversations 
                if c.get("tags") and any(
                    tag in c.get("tags", []) 
                    for tag in ["Hot Lead", "Qualified"]
                )
            ])
            conversion_rate = (
                (qualified_leads / total_leads * 100) 
                if total_leads > 0 else 0
            )
            
            # Build activity feed from recent conversations
            activity_feed = []
            for conv in conversations[:10]:  # Last 10 activities
                contact_name = conv.get("contactName", "Unknown")
                last_message = conv.get("lastMessageBody", "")[:50]
                timestamp = conv.get("lastMessageDate", "")
                
                activity_feed.append({
                    "type": "conversation",
                    "contact": contact_name,
                    "message": last_message,
                    "timestamp": timestamp
                })
            
            # Return structured data
            return {
                "conversations": conversations,
                "opportunities": opportunities,
                "metrics": {
                    "total_pipeline": total_pipeline,
                    "total_revenue": total_revenue,
                    "conversion_rate": conversion_rate,
                    "active_leads": total_leads,
                    "qualified_leads": qualified_leads,
                    "won_deals": len(won_deals)
                },
                "activity_feed": activity_feed,
                "system_health": {
                    "status": "live",
                    "api_connected": True,
                    "last_sync": self._get_current_timestamp()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch dashboard data: {e}")
            # Return minimal structure to prevent crashes
            return {
                "conversations": [],
                "opportunities": [],
                "metrics": {
                    "total_pipeline": 0,
                    "total_revenue": 0,
                    "conversion_rate": 0,
                    "active_leads": 0,
                    "qualified_leads": 0,
                    "won_deals": 0
                },
                "activity_feed": [],
                "system_health": {
                    "status": "error",
                    "api_connected": False,
                    "error": str(e)
                }
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
