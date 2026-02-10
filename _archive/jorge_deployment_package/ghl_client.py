#!/usr/bin/env python3
"""
Standalone GHL Client for Jorge's Bot System

This is a self-contained GoHighLevel API client with all the methods
needed for Jorge's lead and seller bots.
"""

import asyncio
import logging
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
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

    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self, access_token: Optional[str] = None, timeout_seconds: float = 10.0):
        """Initialize GHL client with access token."""

        self.access_token = access_token or os.getenv("GHL_ACCESS_TOKEN")
        self.base_url = "https://services.leadconnectorhq.com"
        self.timeout = httpx.Timeout(timeout_seconds, connect=5.0)
        self.max_retries = 3

        if not self.access_token:
            raise ValueError("GHL_ACCESS_TOKEN is required")

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.logger = logging.getLogger(__name__)

    async def _request(
        self,
        method: str,
        endpoint: str,
        operation: str,
        json_payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[httpx.Response]:
        url = f"{self.base_url}{endpoint}"
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        json=json_payload,
                        params=params,
                    )

                self.logger.info(
                    "ghl_request operation=%s method=%s status_code=%s attempt=%s",
                    operation,
                    method,
                    response.status_code,
                    attempt,
                )

                if (
                    response.status_code in self.RETRYABLE_STATUS_CODES
                    and attempt < self.max_retries
                ):
                    backoff_seconds = (2 ** (attempt - 1)) + random.uniform(0, 0.25)
                    await asyncio.sleep(backoff_seconds)
                    continue

                return response

            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                self.logger.warning(
                    "ghl_request_retry operation=%s method=%s attempt=%s error=%s",
                    operation,
                    method,
                    attempt,
                    exc,
                )
                if attempt < self.max_retries:
                    backoff_seconds = (2 ** (attempt - 1)) + random.uniform(0, 0.25)
                    await asyncio.sleep(backoff_seconds)
                    continue

        if last_error:
            self.logger.error(
                "ghl_request_failed operation=%s method=%s error=%s",
                operation,
                method,
                last_error,
            )
        return None

    @staticmethod
    def _safe_json(response: Optional[httpx.Response]) -> Dict[str, Any]:
        if not response:
            return {}
        try:
            return response.json()
        except Exception:
            return {}

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get contact information from GHL."""

        response = await self._request(
            "GET",
            f"/contacts/{contact_id}",
            operation="get_contact",
        )
        if response and response.status_code == 200:
            return self._safe_json(response)

        status = response.status_code if response else "none"
        self.logger.error("Failed to get contact %s status=%s", contact_id, status)
        return {}

    async def update_contact(self, contact_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update contact information in GHL."""

        response = await self._request(
            "PUT",
            f"/contacts/{contact_id}",
            operation="update_contact",
            json_payload=data,
        )
        if response and response.status_code in (200, 201):
            return self._safe_json(response)

        status = response.status_code if response else "none"
        self.logger.error("Failed to update contact %s status=%s", contact_id, status)
        return {}

    async def add_tag(self, contact_id: str, tag: str) -> bool:
        """Add tag to contact."""

        response = await self._request(
            "POST",
            f"/contacts/{contact_id}/tags",
            operation="add_tag",
            json_payload={"tags": [tag]},
        )
        if response and response.status_code in (200, 201):
            return True

        status = response.status_code if response else "none"
        self.logger.error("Failed to add tag %s to contact %s status=%s", tag, contact_id, status)
        return False

    async def remove_tag(self, contact_id: str, tag: str) -> bool:
        """Remove tag from contact."""

        response = await self._request(
            "DELETE",
            f"/contacts/{contact_id}/tags/{tag}",
            operation="remove_tag",
        )
        if response and response.status_code in (200, 204):
            return True

        status = response.status_code if response else "none"
        self.logger.error("Failed to remove tag %s from contact %s status=%s", tag, contact_id, status)
        return False

    async def update_custom_field(self, contact_id: str, field_id: str, value: str) -> bool:
        """Update one custom field for contact."""

        return await self.update_contact_custom_fields(contact_id, {field_id: value})

    async def send_message(
        self,
        contact_id: str,
        message: str,
        message_type: str = "SMS",
    ) -> Dict[str, Any]:
        """Send message to contact via GHL."""

        response = await self._request(
            "POST",
            "/conversations/messages",
            operation="send_message",
            json_payload={
                "contactId": contact_id,
                "message": message,
                "type": message_type,
            },
        )
        if response and response.status_code in (200, 201):
            return self._safe_json(response)

        status = response.status_code if response else "none"
        self.logger.error("Failed to send message to contact %s status=%s", contact_id, status)
        return {}

    async def send_sms(self, phone: str, message: str) -> bool:
        """Send SMS via phone number using GHL messaging endpoint."""

        if not phone or not message:
            self.logger.error("send_sms rejected: phone and message are required")
            return False

        response = await self._request(
            "POST",
            "/conversations/messages",
            operation="send_sms",
            json_payload={
                "phone": phone,
                "message": message,
                "type": "SMS",
            },
        )
        if response and response.status_code in (200, 201):
            return True

        status = response.status_code if response else "none"
        self.logger.error("Failed to send SMS to %s status=%s", phone, status)
        return False

    async def update_contact_custom_fields(self, contact_id: str, updates: Dict[str, Any]) -> bool:
        """Update multiple contact custom fields in one call."""

        if not isinstance(updates, dict) or not updates:
            self.logger.error("update_contact_custom_fields rejected: updates must be a non-empty dict")
            return False

        custom_fields: List[Dict[str, Any]] = []
        for field_id, value in updates.items():
            if not isinstance(field_id, str) or not field_id.strip():
                self.logger.error("update_contact_custom_fields rejected: invalid field id %r", field_id)
                return False
            custom_fields.append({"id": field_id, "value": value})

        response = await self._request(
            "PUT",
            f"/contacts/{contact_id}",
            operation="update_contact_custom_fields",
            json_payload={"customFields": custom_fields},
        )
        if response and response.status_code in (200, 201):
            return True

        status = response.status_code if response else "none"
        self.logger.error(
            "Failed to update custom fields for contact %s status=%s",
            contact_id,
            status,
        )
        return False

    async def add_contact_tags(self, contact_id: str, tags: List[str]) -> bool:
        """Add multiple tags to a contact."""

        if not isinstance(tags, list) or not tags:
            self.logger.error("add_contact_tags rejected: tags must be a non-empty list")
            return False

        success = True
        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                self.logger.error("add_contact_tags rejected: invalid tag %r", tag)
                return False
            tag_success = await self.add_tag(contact_id, tag)
            success = success and tag_success

        return success

    async def trigger_workflow(self, contact_id: str, workflow_id: str) -> Dict[str, Any]:
        """Trigger workflow for contact."""

        response = await self._request(
            "POST",
            f"/workflows/{workflow_id}/subscribe",
            operation="trigger_workflow",
            json_payload={"contactId": contact_id, "workflowId": workflow_id},
        )
        if response and response.status_code in (200, 201):
            return self._safe_json(response)

        status = response.status_code if response else "none"
        self.logger.error(
            "Failed to trigger workflow %s for contact %s status=%s",
            workflow_id,
            contact_id,
            status,
        )
        return {}

    async def create_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create calendar appointment in GHL."""

        response = await self._request(
            "POST",
            "/calendars/events",
            operation="create_appointment",
            json_payload=appointment_data,
        )
        if response and response.status_code in (200, 201):
            return self._safe_json(response)

        status = response.status_code if response else "none"
        self.logger.error("Failed to create appointment status=%s", status)
        return {}

    async def get_conversations(self, contact_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for contact."""

        response = await self._request(
            "GET",
            "/conversations",
            operation="get_conversations",
            params={"contactId": contact_id},
        )
        if response and response.status_code == 200:
            return self._safe_json(response).get("conversations", [])

        status = response.status_code if response else "none"
        self.logger.error("Failed to get conversations for contact %s status=%s", contact_id, status)
        return []

    async def apply_actions(self, contact_id: str, actions: List[Dict[str, Any]]) -> bool:
        """Apply multiple actions to a contact."""

        success = True
        for action in actions:
            try:
                action_type = action.get("type")

                if action_type == "add_tag":
                    result = await self.add_tag(contact_id, action["tag"])
                elif action_type == "remove_tag":
                    result = await self.remove_tag(contact_id, action["tag"])
                elif action_type == "update_custom_field":
                    result = await self.update_custom_field(contact_id, action["field"], action["value"])
                elif action_type == "trigger_workflow":
                    result = bool(await self.trigger_workflow(contact_id, action["workflow_id"]))
                elif action_type == "send_message":
                    result = bool(await self.send_message(contact_id, action["message"]))
                else:
                    self.logger.warning("Unknown action type: %s", action_type)
                    result = False

                if not result:
                    success = False

            except Exception as exc:
                self.logger.error("Error applying action %s: %s", action, exc)
                success = False

        return success

    def check_health(self) -> httpx.Response:
        """Check GHL API health (synchronous for health checks)."""

        try:
            with httpx.Client(timeout=5.0) as client:
                return client.get(f"{self.base_url}/locations", headers=self.headers)
        except Exception as exc:
            self.logger.error("Health check failed: %s", exc)

            class MockResponse:
                status_code = 500

            return MockResponse()


# Factory function for easy instantiation
def create_ghl_client(access_token: Optional[str] = None) -> GHLClient:
    """Create and configure GHL client."""
    return GHLClient(access_token=access_token)
