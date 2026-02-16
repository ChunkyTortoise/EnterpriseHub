"""GHL CRM sync — push call results and update contact tags."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GHLSyncService:
    """Syncs voice call outcomes to GoHighLevel CRM.

    After each call, pushes:
    - Call summary (duration, bot type, outcome)
    - Lead temperature tag (Hot/Warm/Cold based on score)
    - Appointment booking if triggered during call
    - Contact note with transcript summary
    """

    api_key: str
    location_id: str
    base_url: str = "https://services.leadconnectorhq.com"

    def _get_temperature_tag(self, lead_score: float | None) -> str:
        """Map lead score to temperature tag."""
        if lead_score is None:
            return "Unknown-Lead"
        if lead_score >= 80:
            return "Hot-Lead"
        if lead_score >= 40:
            return "Warm-Lead"
        return "Cold-Lead"

    async def sync_call_result(
        self,
        contact_id: str,
        call_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Push call results to GHL contact.

        Args:
            contact_id: GHL contact ID.
            call_data: Dict with duration, bot_type, lead_score, sentiment, etc.

        Returns:
            Dict with sync results.
        """
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28",
        }

        # Update contact tags
        tag = self._get_temperature_tag(call_data.get("lead_score"))
        tags_to_add = [tag, f"voice-{call_data.get('bot_type', 'lead')}"]

        async with httpx.AsyncClient() as client:
            # Add tags
            await client.post(
                f"{self.base_url}/contacts/{contact_id}/tags",
                headers=headers,
                json={"tags": tags_to_add},
            )

            # Add call note
            note_text = (
                f"Voice AI Call Summary\n"
                f"Duration: {call_data.get('duration_seconds', 0):.0f}s\n"
                f"Bot: {call_data.get('bot_type', 'lead')}\n"
                f"Lead Score: {call_data.get('lead_score', 'N/A')}\n"
                f"Sentiment: {call_data.get('sentiment', 'N/A')}\n"
                f"Appointment: {'Yes' if call_data.get('appointment_booked') else 'No'}"
            )
            await client.post(
                f"{self.base_url}/contacts/{contact_id}/notes",
                headers=headers,
                json={"body": note_text},
            )

        logger.info("GHL sync complete for contact %s (tag=%s)", contact_id, tag)
        return {"contact_id": contact_id, "tags_added": tags_to_add, "note_added": True}

    async def create_contact(
        self, phone: str, name: str | None = None, email: str | None = None
    ) -> str:
        """Create a new GHL contact from an inbound call."""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28",
        }

        payload: dict[str, Any] = {
            "phone": phone,
            "locationId": self.location_id,
            "source": "Voice AI Platform",
        }
        if name:
            payload["name"] = name
        if email:
            payload["email"] = email

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/contacts",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        contact_id = data.get("contact", {}).get("id", "")
        logger.info("GHL contact created: %s", contact_id)
        return contact_id
