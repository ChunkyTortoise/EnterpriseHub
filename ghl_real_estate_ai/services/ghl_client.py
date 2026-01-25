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
        """
        Fetch recent conversations from GHL.
        
        CRITICAL SECURITY FIX: No longer silently returns empty list on API failures.
        Silent failures can hide important system issues and compromise monitoring.
        
        Args:
            limit: Maximum number of conversations to fetch
            
        Returns:
            List of conversation dictionaries
            
        Raises:
            ValueError: If limit is invalid
            httpx.HTTPError: If API request fails
            ConnectionError: If GHL API is unreachable
        """
        if limit <= 0:
            error_msg = f"Invalid conversation limit: {limit}. Must be positive integer."
            logger.error(error_msg, extra={"security_event": "fetch_conversations_failed", "error_id": "GHL_005"})
            raise ValueError(error_msg)
            
        if settings.test_mode or self.api_key == "dummy":
            logger.info(f"[TEST MODE] Would fetch {limit} conversations", extra={"test_mode": True})
            return []
            
        endpoint = f"{self.base_url}/conversations/search"
        params = {"locationId": self.location_id, "limit": limit}
        
        try:
            with httpx.Client() as client:
                response = client.get(endpoint, params=params, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                conversations = data.get("conversations", [])
                
                logger.info(
                    f"Successfully fetched {len(conversations)} conversations",
                    extra={"security_event": "fetch_conversations_success", "count": len(conversations)}
                )
                
                return conversations
                
        except httpx.TimeoutException as e:
            error_msg = f"Timeout fetching conversations after 30s: {str(e)}"
            logger.error(
                error_msg,
                extra={"security_event": "fetch_conversations_timeout", "error_id": "GHL_006", "limit": limit}
            )
            raise ConnectionError(error_msg) from e
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code} error fetching conversations: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "security_event": "fetch_conversations_http_error", 
                    "error_id": "GHL_007",
                    "status_code": e.response.status_code,
                    "limit": limit
                }
            )
            raise
            
        except Exception as e:
            error_msg = f"Unexpected error fetching conversations: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "security_event": "fetch_conversations_critical_failure",
                    "error_id": "GHL_008", 
                    "limit": limit,
                    "error_type": type(e).__name__
                }
            )
            raise

    def get_opportunities(self) -> List[Dict[str, Any]]:
        """
        Fetch opportunities (pipeline) from GHL.
        
        CRITICAL SECURITY FIX: No longer silently returns empty list on API failures.
        Silent failures can hide revenue pipeline issues and compromise business monitoring.
        
        Returns:
            List of opportunity dictionaries
            
        Raises:
            httpx.HTTPError: If API request fails
            ConnectionError: If GHL API is unreachable
        """
        if settings.test_mode or self.api_key == "dummy":
            logger.info("[TEST MODE] Would fetch opportunities", extra={"test_mode": True})
            return []
            
        endpoint = f"{self.base_url}/opportunities/search"
        params = {"locationId": self.location_id}
        
        try:
            with httpx.Client() as client:
                response = client.get(endpoint, params=params, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                opportunities = data.get("opportunities", [])
                
                # Calculate revenue for logging
                total_pipeline = sum(
                    float(opp.get("monetary_value", 0) or 0) for opp in opportunities
                )
                
                logger.info(
                    f"Successfully fetched {len(opportunities)} opportunities, total pipeline: ${total_pipeline:,.2f}",
                    extra={
                        "security_event": "fetch_opportunities_success", 
                        "count": len(opportunities),
                        "pipeline_value": total_pipeline
                    }
                )
                
                return opportunities
                
        except httpx.TimeoutException as e:
            error_msg = f"Timeout fetching opportunities after 30s: {str(e)}"
            logger.error(
                error_msg,
                extra={"security_event": "fetch_opportunities_timeout", "error_id": "GHL_009"}
            )
            raise ConnectionError(error_msg) from e
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code} error fetching opportunities: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "security_event": "fetch_opportunities_http_error", 
                    "error_id": "GHL_010",
                    "status_code": e.response.status_code
                }
            )
            raise
            
        except Exception as e:
            error_msg = f"Unexpected error fetching opportunities: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "security_event": "fetch_opportunities_critical_failure",
                    "error_id": "GHL_011",
                    "error_type": type(e).__name__
                }
            )
            raise

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

        CRITICAL SECURITY FIX: This method now properly removes tags instead of just logging.
        Silent failures in tag removal can bypass security policies.

        Args:
            contact_id: GHL contact ID
            tags: List of tag names to remove

        Returns:
            API response dict

        Raises:
            ValueError: If contact_id or tags are invalid
            httpx.HTTPError: If API request fails
        """
        if not contact_id:
            error_msg = "Contact ID is required for tag removal"
            logger.error(error_msg, extra={"security_event": "tag_removal_failed", "error_id": "GHL_001"})
            raise ValueError(error_msg)
            
        if not tags or not isinstance(tags, list):
            error_msg = f"Valid tags list is required for removal from contact {contact_id}"
            logger.error(error_msg, extra={"contact_id": contact_id, "security_event": "tag_removal_failed", "error_id": "GHL_002"})
            raise ValueError(error_msg)

        if settings.test_mode:
            logger.info(
                f"[TEST MODE] Would remove tags from contact {contact_id}: {tags}",
                extra={"contact_id": contact_id, "tags": tags, "test_mode": True},
            )
            return {"status": "mocked", "removed_tags": tags}

        try:
            # Step 1: Fetch current contact data to get existing tags
            contact_endpoint = f"{self.base_url}/contacts/{contact_id}"
            
            async with httpx.AsyncClient() as client:
                # Get current contact data
                response = await client.get(
                    contact_endpoint,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds,
                )
                response.raise_for_status()
                
                contact_data = response.json()
                current_tags = contact_data.get("tags", [])
                
                # Step 2: Remove specified tags from current tags
                if not current_tags:
                    logger.warning(
                        f"Contact {contact_id} has no tags to remove",
                        extra={"contact_id": contact_id, "requested_tags": tags}
                    )
                    return {"message": "No tags to remove", "current_tags": []}
                
                # Remove the specified tags (case-insensitive)
                tags_to_remove_lower = [tag.lower() for tag in tags]
                updated_tags = [tag for tag in current_tags if tag.lower() not in tags_to_remove_lower]
                
                # Step 3: Update contact with new tags list
                payload = {"tags": updated_tags}
                
                update_response = await client.put(
                    contact_endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds,
                )
                update_response.raise_for_status()

                # Log successful removal with security context
                removed_tags = [tag for tag in current_tags if tag.lower() in tags_to_remove_lower]
                logger.info(
                    f"Successfully removed tags from contact {contact_id}: {removed_tags}",
                    extra={
                        "contact_id": contact_id, 
                        "removed_tags": removed_tags,
                        "remaining_tags": updated_tags,
                        "security_event": "tag_removal_success"
                    },
                )

                return {
                    "status": "success",
                    "removed_tags": removed_tags,
                    "remaining_tags": updated_tags,
                    "contact_id": contact_id
                }

        except httpx.HTTPError as e:
            error_msg = f"Failed to remove tags from contact {contact_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "contact_id": contact_id, 
                    "error": str(e),
                    "security_event": "tag_removal_failed",
                    "error_id": "GHL_003",
                    "requested_tags": tags
                },
            )
            raise
        except Exception as e:
            error_msg = f"Unexpected error removing tags from contact {contact_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "contact_id": contact_id,
                    "error": str(e),
                    "security_event": "tag_removal_critical_failure", 
                    "error_id": "GHL_004",
                    "requested_tags": tags
                },
            )
            raise

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
        
        CRITICAL SECURITY FIX: Enhanced error handling and escalation for critical failures.
        Some action failures should stop processing entirely to prevent inconsistent state.

        Args:
            contact_id: GHL contact ID
            actions: List of GHLAction objects

        Returns:
            List of API response dicts

        Raises:
            ValueError: If contact_id or actions are invalid
            RuntimeError: If critical security-related actions fail
        """
        if not contact_id:
            error_msg = "Contact ID is required for action application"
            logger.error(error_msg, extra={"security_event": "apply_actions_failed", "error_id": "GHL_012"})
            raise ValueError(error_msg)
            
        if not actions:
            error_msg = "Actions list cannot be empty"
            logger.error(error_msg, extra={"contact_id": contact_id, "security_event": "apply_actions_failed", "error_id": "GHL_013"})
            raise ValueError(error_msg)

        results = []
        critical_failures = []
        
        logger.info(
            f"Starting to apply {len(actions)} actions to contact {contact_id}",
            extra={"contact_id": contact_id, "action_count": len(actions)}
        )

        for i, action in enumerate(actions):
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
                    # Tag removal is CRITICAL for security policies - must not fail silently
                    try:
                        result = await self.remove_tags(contact_id, [action.tag])
                        results.append(result)
                    except Exception as e:
                        critical_failures.append({
                            "action": action.type,
                            "error": str(e),
                            "action_index": i,
                            "tag": action.tag
                        })
                        logger.error(
                            f"CRITICAL: Tag removal failed for contact {contact_id}, tag: {action.tag}",
                            extra={
                                "contact_id": contact_id,
                                "action_type": action.type,
                                "error": str(e),
                                "security_event": "critical_tag_removal_failure",
                                "error_id": "GHL_014",
                                "tag": action.tag
                            }
                        )
                        raise RuntimeError(f"Critical security action failed: {action.type}") from e

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

                else:
                    # Invalid action configuration
                    error_msg = f"Invalid action configuration: {action.type}"
                    logger.warning(
                        error_msg,
                        extra={
                            "contact_id": contact_id,
                            "action_type": action.type,
                            "action_index": i
                        }
                    )
                    results.append({"error": error_msg, "action": action.type})

            except RuntimeError:
                # Critical failures should stop processing immediately
                raise
                
            except Exception as e:
                error_msg = f"Failed to apply action {action.type}: {str(e)}"
                logger.error(
                    error_msg,
                    extra={
                        "contact_id": contact_id,
                        "action_type": action.type,
                        "error": str(e),
                        "action_index": i,
                        "security_event": "action_application_failure",
                        "error_id": "GHL_015"
                    },
                )
                
                # For non-critical actions, log error and continue
                results.append({
                    "error": str(e), 
                    "action": action.type,
                    "action_index": i,
                    "status": "failed"
                })

        # Log final summary
        successful_actions = len([r for r in results if "error" not in r])
        failed_actions = len(results) - successful_actions
        
        logger.info(
            f"Action application complete: {successful_actions} successful, {failed_actions} failed",
            extra={
                "contact_id": contact_id,
                "successful_count": successful_actions,
                "failed_count": failed_actions,
                "critical_failures": len(critical_failures)
            }
        )

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
            # CRITICAL SECURITY FIX: Dashboard failures should not be silently masked
            error_msg = f"CRITICAL: Dashboard data fetch failed - this indicates serious system problems: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "security_event": "dashboard_fetch_critical_failure",
                    "error_id": "GHL_016",
                    "error_type": type(e).__name__,
                    "api_key_status": "configured" if self.api_key else "missing"
                }
            )
            # Dashboard failures indicate critical system problems - don't hide them
            raise RuntimeError(error_msg) from e
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    async def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get contact information by ID from GHL.

        Args:
            contact_id: GHL contact ID

        Returns:
            Contact data dict or None if not found

        Raises:
            httpx.HTTPError: If API request fails
        """
        if not contact_id:
            logger.error("Contact ID is required")
            return None

        if settings.test_mode or self.api_key == "dummy":
            logger.info(f"[TEST MODE] Would fetch contact {contact_id}", extra={"test_mode": True})
            return {
                "id": contact_id,
                "firstName": "Test",
                "lastName": "Contact",
                "email": f"test-{contact_id}@example.com",
                "phone": "+15551234567",
                "tags": [],
                "customFields": {}
            }

        endpoint = f"{self.base_url}/contacts/{contact_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    headers=self.headers,
                    timeout=settings.webhook_timeout_seconds,
                )
                response.raise_for_status()

                contact_data = response.json()

                logger.info(
                    f"Successfully fetched contact {contact_id}",
                    extra={"contact_id": contact_id}
                )

                return contact_data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Contact {contact_id} not found in GHL")
                return None
            else:
                logger.error(f"HTTP {e.response.status_code} error fetching contact {contact_id}: {str(e)}")
                raise

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch contact {contact_id}: {str(e)}")
            raise

    async def search_contacts(self, query: str = "", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search contacts in GHL.

        Args:
            query: Search query (name, email, phone)
            limit: Maximum number of results

        Returns:
            List of contact dictionaries

        Raises:
            httpx.HTTPError: If API request fails
        """
        if settings.test_mode or self.api_key == "dummy":
            logger.info(f"[TEST MODE] Would search contacts with query '{query}'", extra={"test_mode": True})
            return []

        endpoint = f"{self.base_url}/contacts/search"
        params = {"locationId": self.location_id, "limit": limit}

        if query:
            params["query"] = query

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
                contacts = data.get("contacts", [])

                logger.info(f"Found {len(contacts)} contacts matching query '{query}'")
                return contacts

        except httpx.HTTPError as e:
            logger.error(f"Failed to search contacts with query '{query}': {str(e)}")
            raise
