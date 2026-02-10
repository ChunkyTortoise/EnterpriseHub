"""HubSpot CRM adapter -- implements CRMProtocol for HubSpot v3 API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .protocol import CRMContact, CRMProtocol

logger = logging.getLogger(__name__)


class HubSpotError(Exception):
    """Raised when a HubSpot API call fails."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HubSpot API error {status_code}: {detail}")


class HubSpotAdapter(CRMProtocol):
    """CRM adapter for HubSpot v3 API.

    Args:
        api_key: HubSpot private app access token.
        base_url: HubSpot API base URL (override for testing).
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.hubapi.com",
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._http_client = httpx.AsyncClient(timeout=30.0)

    # ------------------------------------------------------------------
    # Field mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _contact_to_properties(contact: CRMContact) -> dict[str, str]:
        """Map CRMContact fields to HubSpot contact properties."""
        props: dict[str, str] = {}
        if contact.first_name:
            props["firstname"] = contact.first_name
        if contact.last_name:
            props["lastname"] = contact.last_name
        if contact.email:
            props["email"] = contact.email
        if contact.phone:
            props["phone"] = contact.phone
        if contact.source:
            props["hs_lead_status"] = contact.source
        return props

    @staticmethod
    def _properties_to_contact(
        hs_id: str, properties: dict[str, Any]
    ) -> CRMContact:
        """Map HubSpot properties dict to a CRMContact."""
        return CRMContact(
            id=hs_id,
            first_name=properties.get("firstname", "") or "",
            last_name=properties.get("lastname", "") or "",
            email=properties.get("email"),
            phone=properties.get("phone"),
            source=properties.get("hs_lead_status", "") or "",
        )

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
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
        resp = await self._http_client.request(
            method, url, headers=self._headers(), json=json_body,
            params=params,
        )
        if resp.status_code == 401:
            raise HubSpotError(401, "Authentication failed")
        if resp.status_code == 404:
            raise HubSpotError(404, "Resource not found")
        if resp.status_code >= 400:
            raise HubSpotError(resp.status_code, resp.text)
        return resp

    # ------------------------------------------------------------------
    # CRMProtocol implementation
    # ------------------------------------------------------------------

    async def create_contact(self, contact: CRMContact) -> CRMContact:
        """Create a new contact in HubSpot."""
        payload = {"properties": self._contact_to_properties(contact)}
        resp = await self._request(
            "POST", "/crm/v3/objects/contacts", json_body=payload
        )
        data = resp.json()
        created = self._properties_to_contact(
            data["id"], data.get("properties", {})
        )
        created.tags = list(contact.tags)
        created.metadata = dict(contact.metadata)
        logger.info("Created HubSpot contact %s", created.id)
        return created

    async def update_contact(
        self, contact_id: str, updates: dict[str, Any]
    ) -> CRMContact:
        """Update an existing HubSpot contact."""
        # Map any CRMContact-level keys to HubSpot property names
        hs_key_map = {
            "first_name": "firstname",
            "last_name": "lastname",
            "email": "email",
            "phone": "phone",
            "source": "hs_lead_status",
        }
        properties: dict[str, Any] = {}
        for key, value in updates.items():
            hs_key = hs_key_map.get(key, key)
            properties[hs_key] = value

        payload = {"properties": properties}
        resp = await self._request(
            "PATCH",
            f"/crm/v3/objects/contacts/{contact_id}",
            json_body=payload,
        )
        data = resp.json()
        return self._properties_to_contact(
            data["id"], data.get("properties", {})
        )

    async def get_contact(self, contact_id: str) -> CRMContact | None:
        """Retrieve a HubSpot contact by ID."""
        try:
            resp = await self._request(
                "GET", f"/crm/v3/objects/contacts/{contact_id}"
            )
        except HubSpotError as exc:
            if exc.status_code == 404:
                return None
            raise
        data = resp.json()
        return self._properties_to_contact(
            data["id"], data.get("properties", {})
        )

    async def search_contacts(
        self, query: str, limit: int = 10
    ) -> list[CRMContact]:
        """Search HubSpot contacts using the search API."""
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "CONTAINS_TOKEN",
                            "value": query,
                        }
                    ]
                }
            ],
            "limit": limit,
        }
        resp = await self._request(
            "POST", "/crm/v3/objects/contacts/search", json_body=payload
        )
        data = resp.json()
        results: list[CRMContact] = []
        for item in data.get("results", []):
            results.append(
                self._properties_to_contact(
                    item["id"], item.get("properties", {})
                )
            )
        return results

    async def sync_lead(
        self, contact: CRMContact, score: int, temperature: str
    ) -> bool:
        """Sync lead data: update contact and apply temperature tag."""
        if not contact.id:
            logger.warning("sync_lead called with no contact id")
            return False
        try:
            await self.update_contact(
                contact.id,
                {
                    "hs_lead_status": temperature,
                    "lead_score": str(score),
                },
            )
            logger.info(
                "Synced lead %s score=%d temp=%s",
                contact.id,
                score,
                temperature,
            )
            return True
        except HubSpotError:
            logger.exception("Failed to sync lead %s", contact.id)
            return False

    # ------------------------------------------------------------------
    # Extended operations (beyond CRMProtocol)
    # ------------------------------------------------------------------

    async def delete_contact(self, contact_id: str) -> bool:
        """Delete a HubSpot contact by ID.

        Returns True on success, False if not found.
        """
        try:
            await self._request(
                "DELETE", f"/crm/v3/objects/contacts/{contact_id}"
            )
            logger.info("Deleted HubSpot contact %s", contact_id)
            return True
        except HubSpotError as exc:
            if exc.status_code == 404:
                logger.warning(
                    "Cannot delete HubSpot contact %s: not found", contact_id
                )
                return False
            raise

    async def list_contacts(
        self,
        limit: int = 10,
        after: str | None = None,
    ) -> tuple[list[CRMContact], str | None]:
        """List HubSpot contacts with cursor-based pagination.

        Args:
            limit: Maximum number of contacts per page (max 100).
            after: Cursor token for the next page.

        Returns:
            Tuple of (contacts, next_cursor). next_cursor is None when
            there are no more pages.
        """
        params: dict[str, Any] = {"limit": min(limit, 100)}
        if after:
            params["after"] = after

        resp = await self._request(
            "GET", "/crm/v3/objects/contacts", params=params
        )
        data = resp.json()
        contacts: list[CRMContact] = []
        for item in data.get("results", []):
            contacts.append(
                self._properties_to_contact(
                    item["id"], item.get("properties", {})
                )
            )
        paging = data.get("paging", {})
        next_cursor = paging.get("next", {}).get("after")
        return contacts, next_cursor
