"""Salesforce CRM adapter -- implements CRMProtocol for Salesforce REST API."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from .protocol import CRMContact, CRMProtocol

logger = logging.getLogger(__name__)


class SalesforceError(Exception):
    """Raised when a Salesforce API call fails."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Salesforce API error {status_code}: {detail}")


class SalesforceAdapter(CRMProtocol):
    """CRM adapter for Salesforce REST API.

    Uses OAuth 2.0 client_credentials flow for authentication.

    Args:
        client_id: Salesforce Connected App client ID.
        client_secret: Salesforce Connected App client secret.
        instance_url: Salesforce instance URL (e.g. https://na1.salesforce.com).
        base_url: Override for the token endpoint base (testing).
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        instance_url: str,
        base_url: str | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._instance_url = instance_url.rstrip("/")
        self._base_url = (base_url or instance_url).rstrip("/")
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0
        self._http_client = httpx.AsyncClient(timeout=30.0)

    # ------------------------------------------------------------------
    # OAuth 2.0 authentication
    # ------------------------------------------------------------------

    async def _authenticate(self) -> str:
        """Obtain or refresh an OAuth 2.0 access token.

        Uses client_credentials grant type. Caches the token until expiry.
        """
        if self._access_token and time.monotonic() < self._token_expires_at:
            return self._access_token

        url = f"{self._base_url}/services/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        resp = await self._http_client.post(url, data=payload)

        if resp.status_code != 200:
            raise SalesforceError(resp.status_code, "Authentication failed")

        data = resp.json()
        self._access_token = data["access_token"]
        # Default token lifetime: 2 hours minus 5-minute buffer
        expires_in = int(data.get("expires_in", 7200)) - 300
        self._token_expires_at = time.monotonic() + expires_in
        return self._access_token

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def _headers(self) -> dict[str, str]:
        token = await self._authenticate()
        return {
            "Authorization": f"Bearer {token}",
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
        """Execute an HTTP request against Salesforce REST API."""
        url = f"{self._base_url}/services/data/v59.0{path}"
        headers = await self._headers()
        resp = await self._http_client.request(
            method, url, headers=headers, json=json_body, params=params,
        )
        if resp.status_code == 401:
            # Token may have expired — clear cache and re-raise
            self._access_token = None
            self._token_expires_at = 0.0
            raise SalesforceError(401, "Authentication failed")
        if resp.status_code == 404:
            raise SalesforceError(404, "Resource not found")
        if resp.status_code == 429:
            raise SalesforceError(429, "Rate limit exceeded")
        if resp.status_code >= 400:
            raise SalesforceError(resp.status_code, resp.text)
        return resp

    # ------------------------------------------------------------------
    # Field mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _contact_to_salesforce(contact: CRMContact) -> dict[str, str]:
        """Map CRMContact fields to Salesforce Contact/Lead fields."""
        fields: dict[str, str] = {}
        if contact.first_name:
            fields["FirstName"] = contact.first_name
        if contact.last_name:
            fields["LastName"] = contact.last_name
        if contact.email:
            fields["Email"] = contact.email
        if contact.phone:
            fields["Phone"] = contact.phone
        if contact.source:
            fields["LeadSource"] = contact.source
        return fields

    @staticmethod
    def _salesforce_to_contact(sf_id: str, record: dict[str, Any]) -> CRMContact:
        """Map Salesforce record to CRMContact."""
        return CRMContact(
            id=sf_id,
            first_name=record.get("FirstName", "") or "",
            last_name=record.get("LastName", "") or "",
            email=record.get("Email"),
            phone=record.get("Phone"),
            source=record.get("LeadSource", "") or "",
        )

    # ------------------------------------------------------------------
    # CRMProtocol implementation
    # ------------------------------------------------------------------

    async def create_contact(self, contact: CRMContact) -> CRMContact:
        """Create a new contact in Salesforce."""
        payload = self._contact_to_salesforce(contact)
        resp = await self._request(
            "POST", "/sobjects/Contact", json_body=payload,
        )
        data = resp.json()
        sf_id = data.get("id", "")
        created = CRMContact(
            id=sf_id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            email=contact.email,
            phone=contact.phone,
            source=contact.source,
            tags=list(contact.tags),
            metadata=dict(contact.metadata),
        )
        logger.info("Created Salesforce contact %s", sf_id)
        return created

    async def update_contact(
        self, contact_id: str, updates: dict[str, Any]
    ) -> CRMContact:
        """Update an existing Salesforce contact."""
        sf_key_map = {
            "first_name": "FirstName",
            "last_name": "LastName",
            "email": "Email",
            "phone": "Phone",
            "source": "LeadSource",
        }
        payload: dict[str, Any] = {}
        for key, value in updates.items():
            sf_key = sf_key_map.get(key, key)
            payload[sf_key] = value

        await self._request(
            "PATCH", f"/sobjects/Contact/{contact_id}", json_body=payload,
        )
        # Salesforce PATCH returns 204 — fetch updated record
        resp = await self._request("GET", f"/sobjects/Contact/{contact_id}")
        data = resp.json()
        return self._salesforce_to_contact(data.get("Id", contact_id), data)

    async def get_contact(self, contact_id: str) -> CRMContact | None:
        """Retrieve a Salesforce contact by ID."""
        try:
            resp = await self._request(
                "GET", f"/sobjects/Contact/{contact_id}",
            )
        except SalesforceError as exc:
            if exc.status_code == 404:
                return None
            raise
        data = resp.json()
        return self._salesforce_to_contact(data.get("Id", contact_id), data)

    async def search_contacts(
        self, query: str, limit: int = 10,
    ) -> list[CRMContact]:
        """Search Salesforce contacts using SOSL."""
        sosl = (
            f"FIND {{{query}}} IN ALL FIELDS "
            f"RETURNING Contact(Id, FirstName, LastName, Email, Phone, LeadSource) "
            f"LIMIT {limit}"
        )
        resp = await self._request("GET", "/search/", params={"q": sosl})
        data = resp.json()
        results: list[CRMContact] = []
        for record in data.get("searchRecords", []):
            results.append(
                self._salesforce_to_contact(record["Id"], record)
            )
        return results

    async def sync_lead(
        self, contact: CRMContact, score: int, temperature: str,
    ) -> bool:
        """Sync lead data with temperature scoring."""
        if not contact.id:
            logger.warning("sync_lead called with no contact id")
            return False
        try:
            await self.update_contact(
                contact.id,
                {
                    "LeadSource": temperature,
                    "lead_score__c": str(score),
                },
            )
            logger.info(
                "Synced lead %s score=%d temp=%s",
                contact.id,
                score,
                temperature,
            )
            return True
        except SalesforceError:
            logger.exception("Failed to sync lead %s", contact.id)
            return False
