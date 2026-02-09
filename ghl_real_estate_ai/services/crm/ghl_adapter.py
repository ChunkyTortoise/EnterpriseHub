"""GHL CRM adapter -- implements CRMProtocol for GoHighLevel v2 API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .protocol import CRMContact, CRMProtocol

logger = logging.getLogger(__name__)


class GHLError(Exception):
    """Raised when a GHL API call fails."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"GHL API error {status_code}: {detail}")


class GHLAdapter(CRMProtocol):
    """CRM adapter for GoHighLevel v2 API.

    Args:
        api_key: GHL API bearer token.
        location_id: GHL location ID for contact scoping.
        base_url: GHL API base URL (override for testing).
    """

    def __init__(
        self,
        api_key: str,
        location_id: str,
        base_url: str = "https://services.leadconnectorhq.com",
    ) -> None:
        self._api_key = api_key
        self._location_id = location_id
        self._base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Field mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _contact_to_ghl(contact: CRMContact, location_id: str) -> dict[str, Any]:
        """Map CRMContact fields to GHL contact payload."""
        payload: dict[str, Any] = {"locationId": location_id}
        if contact.first_name:
            payload["firstName"] = contact.first_name
        if contact.last_name:
            payload["lastName"] = contact.last_name
        if contact.email:
            payload["email"] = contact.email
        if contact.phone:
            payload["phone"] = contact.phone
        if contact.tags:
            payload["tags"] = list(contact.tags)
        if contact.source:
            payload["source"] = contact.source
        return payload

    @staticmethod
    def _ghl_to_contact(data: dict[str, Any]) -> CRMContact:
        """Map GHL API response to CRMContact."""
        return CRMContact(
            id=data.get("id", ""),
            first_name=data.get("firstName", "") or "",
            last_name=data.get("lastName", "") or "",
            email=data.get("email"),
            phone=data.get("phone"),
            source=data.get("source", "") or "",
            tags=data.get("tags", []),
            metadata={
                k: v
                for k, v in data.items()
                if k
                not in {
                    "id",
                    "firstName",
                    "lastName",
                    "email",
                    "phone",
                    "source",
                    "tags",
                }
            },
        )

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    @property
    def _headers(self) -> dict[str, str]:
        """Authorization and version headers for GHL v2 API."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Version": "2021-07-28",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute an HTTP request and raise on failure."""
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                url,
                headers=self._headers,
                json=json_body,
                params=params,
            )
        if resp.status_code == 401:
            raise GHLError(401, "Authentication failed")
        if resp.status_code == 404:
            raise GHLError(404, "Resource not found")
        if resp.status_code >= 400:
            raise GHLError(resp.status_code, resp.text)
        return resp

    # ------------------------------------------------------------------
    # CRMProtocol implementation
    # ------------------------------------------------------------------

    async def create_contact(self, contact: CRMContact) -> CRMContact:
        """Create a new contact in GHL."""
        payload = self._contact_to_ghl(contact, self._location_id)
        resp = await self._request("POST", "/contacts/", json_body=payload)
        data = resp.json().get("contact", resp.json())
        created = self._ghl_to_contact(data)
        logger.info("Created GHL contact %s", created.id)
        return created

    async def update_contact(
        self, contact_id: str, updates: dict[str, Any]
    ) -> CRMContact:
        """Update an existing GHL contact."""
        ghl_key_map = {
            "first_name": "firstName",
            "last_name": "lastName",
            "email": "email",
            "phone": "phone",
            "source": "source",
            "tags": "tags",
        }
        payload: dict[str, Any] = {}
        for key, value in updates.items():
            ghl_key = ghl_key_map.get(key, key)
            payload[ghl_key] = value

        resp = await self._request(
            "PUT", f"/contacts/{contact_id}", json_body=payload
        )
        data = resp.json().get("contact", resp.json())
        return self._ghl_to_contact(data)

    async def get_contact(self, contact_id: str) -> CRMContact | None:
        """Retrieve a GHL contact by ID."""
        try:
            resp = await self._request("GET", f"/contacts/{contact_id}")
        except GHLError as exc:
            if exc.status_code == 404:
                return None
            raise
        data = resp.json().get("contact", resp.json())
        return self._ghl_to_contact(data)

    async def search_contacts(
        self, query: str, limit: int = 10
    ) -> list[CRMContact]:
        """Search GHL contacts by query string."""
        params = {
            "locationId": self._location_id,
            "query": query,
            "limit": limit,
        }
        resp = await self._request("GET", "/contacts/search", params=params)
        data = resp.json()
        results: list[CRMContact] = []
        for item in data.get("contacts", []):
            results.append(self._ghl_to_contact(item))
        return results

    async def sync_lead(
        self, contact: CRMContact, score: int, temperature: str
    ) -> bool:
        """Sync lead data: update contact and apply temperature tag."""
        if not contact.id:
            logger.warning("sync_lead called with no contact id")
            return False
        try:
            existing_tags = list(contact.tags)
            # Remove old temperature tags before adding the new one
            temp_tags = {"Hot-Lead", "Warm-Lead", "Cold-Lead"}
            clean_tags = [t for t in existing_tags if t not in temp_tags]
            clean_tags.append(temperature)

            await self.update_contact(
                contact.id,
                {"tags": clean_tags, "lead_score": str(score)},
            )
            logger.info(
                "Synced lead %s score=%d temp=%s",
                contact.id,
                score,
                temperature,
            )
            return True
        except GHLError:
            logger.exception("Failed to sync lead %s", contact.id)
            return False
