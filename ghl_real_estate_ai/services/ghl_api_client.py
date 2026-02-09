"""
GoHighLevel API Client
Official GHL API integration with OAuth2, rate limiting, and error handling
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GHLRateLimiter:
    """Rate limiter for GHL API (100 requests per minute)"""

    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded (async)"""
        now = time.time()
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]

        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request)
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
                self.requests = []

        self.requests.append(now)


class GHLAPIClient:
    """
    GoHighLevel API Client (Async)

    Features:
    - OAuth2 authentication
    - Automatic token refresh
    - Rate limiting (100 req/min)
    - Async HTTP with httpx
    - Comprehensive error handling
    """

    BASE_URL = "https://rest.gohighlevel.com/v1"
    AUTH_URL = "https://marketplace.gohighlevel.com/oauth/authorize"
    TOKEN_URL = "https://marketplace.gohighlevel.com/oauth/token"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        location_id: Optional[str] = None,
    ):
        """
        Initialize GHL API Client
        """
        self.client_id = client_id or os.getenv("GHL_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GHL_CLIENT_SECRET")
        self.access_token = access_token or os.getenv("GHL_ACCESS_TOKEN")
        self.refresh_token = refresh_token or os.getenv("GHL_REFRESH_TOKEN")
        self.location_id = location_id or os.getenv("GHL_LOCATION_ID")

        self.token_expires_at: Optional[datetime] = None
        self.rate_limiter = GHLRateLimiter()

        # Configure httpx client with connection pooling
        self.client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5),
            timeout=httpx.Timeout(10.0),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def close(self):
        """Close the underlying HTTP client."""
        await self.client.aclose()

    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """
        Get OAuth2 authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "contacts.readonly contacts.write opportunities.readonly opportunities.write "
            "calendars.readonly calendars.write conversations.readonly conversations.write",
        }
        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTH_URL}?{query_string}"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token (async)
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }

        response = await self.client.post(self.TOKEN_URL, data=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token")

        # Calculate expiration
        expires_in = token_data.get("expires_in", 3600)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        logger.info("Successfully obtained access token")
        return token_data

    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh access token using refresh token (async)
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        response = await self.client.post(self.TOKEN_URL, data=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        if "refresh_token" in token_data:
            self.refresh_token = token_data["refresh_token"]

        expires_in = token_data.get("expires_in", 3600)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        logger.info("Successfully refreshed access token")
        return token_data

    async def _ensure_token_valid(self):
        """Ensure access token is valid, refresh if needed (async)"""
        if not self.access_token:
            raise ValueError("No access token available. Call exchange_code_for_token() first.")

        # Refresh if token expires in less than 5 minutes
        if self.token_expires_at and datetime.now() > self.token_expires_at - timedelta(minutes=5):
            logger.info("Token expiring soon, refreshing...")
            await self.refresh_access_token()

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make authenticated API request (async)
        """
        await self._ensure_token_valid()
        await self.rate_limiter.wait_if_needed()

        url = f"{self.BASE_URL}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"

        # Add location ID if required and not in URL
        if self.location_id and "locationId" not in endpoint:
            params = kwargs.get("params", {})
            params["locationId"] = self.location_id
            kwargs["params"] = params

        response = await self.client.request(method, url, headers=headers, **kwargs)

        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"GHL API Error: {e.response.status_code} - {e.response.text}")
            raise

    # CONTACTS API

    async def get_contacts(self, limit: int = 100, skip: int = 0, query: str = None) -> Dict[str, Any]:
        """Get contacts from GHL (async)"""
        params = {"limit": limit, "skip": skip}
        if query:
            params["query"] = query

        return await self._make_request("GET", "/contacts/", params=params)

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get single contact by ID (async)"""
        return await self._make_request("GET", f"/contacts/{contact_id}")

    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new contact (async)"""
        return await self._make_request("POST", "/contacts/", json=contact_data)

    async def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing contact (async)"""
        return await self._make_request("PUT", f"/contacts/{contact_id}", json=contact_data)

    async def delete_contact(self, contact_id: str) -> Dict[str, Any]:
        """Delete contact (async)"""
        return await self._make_request("DELETE", f"/contacts/{contact_id}")

    async def add_contact_tag(self, contact_id: str, tag: str) -> Dict[str, Any]:
        """Add tag (async)"""
        return await self._make_request("POST", f"/contacts/{contact_id}/tags", json={"tags": [tag]})

    async def remove_contact_tag(self, contact_id: str, tag: str) -> Dict[str, Any]:
        """Remove tag (async)"""
        return await self._make_request("DELETE", f"/contacts/{contact_id}/tags", json={"tags": [tag]})

    # OPPORTUNITIES API

    async def get_opportunities(self, pipeline_id: str = None, limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Get opportunities (async)"""
        params = {"limit": limit, "skip": skip}
        if pipeline_id:
            params["pipelineId"] = pipeline_id

        return await self._make_request("GET", "/opportunities/", params=params)

    async def get_opportunity(self, opportunity_id: str) -> Dict[str, Any]:
        """Get single opportunity (async)"""
        return await self._make_request("GET", f"/opportunities/{opportunity_id}")

    async def create_opportunity(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create opportunity (async)"""
        return await self._make_request("POST", "/opportunities/", json=opportunity_data)

    async def update_opportunity(self, opportunity_id: str, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update opportunity (async)"""
        return await self._make_request("PUT", f"/opportunities/{opportunity_id}", json=opportunity_data)

    async def delete_opportunity(self, opportunity_id: str) -> Dict[str, Any]:
        """Delete opportunity (async)"""
        return await self._make_request("DELETE", f"/opportunities/{opportunity_id}")

    # CONVERSATIONS API

    async def get_conversations(self, contact_id: str = None) -> Dict[str, Any]:
        """Get conversations (async)"""
        params = {}
        if contact_id:
            params["contactId"] = contact_id

        return await self._make_request("GET", "/conversations/", params=params)

    async def get_messages(self, conversation_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get messages (async)"""
        params = {"limit": limit}
        return await self._make_request("GET", f"/conversations/{conversation_id}/messages", params=params)

    async def send_sms(self, contact_id: str, message: str, from_number: str = None) -> Dict[str, Any]:
        """Send SMS (async)"""
        data = {"contactId": contact_id, "message": message, "type": "SMS"}
        if from_number:
            data["from"] = from_number

        return await self._make_request("POST", "/conversations/messages", json=data)

    async def send_email(self, contact_id: str, subject: str, body: str, from_email: str = None) -> Dict[str, Any]:
        """Send email (async)"""
        data = {
            "contactId": contact_id,
            "subject": subject,
            "message": body,
            "type": "Email",
        }
        if from_email:
            data["from"] = from_email

        return await self._make_request("POST", "/conversations/messages", json=data)

    # CALENDARS API

    async def get_calendars(self) -> Dict[str, Any]:
        """Get calendars (async)"""
        return await self._make_request("GET", "/calendars/")

    async def get_appointments(
        self, calendar_id: str, start_time: datetime = None, end_time: datetime = None
    ) -> Dict[str, Any]:
        """Get appointments (async)"""
        params = {"calendarId": calendar_id}
        if start_time:
            params["startTime"] = start_time.isoformat()
        if end_time:
            params["endTime"] = end_time.isoformat()

        return await self._make_request("GET", "/appointments/", params=params)

    async def create_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create appointment (async)"""
        return await self._make_request("POST", "/appointments/", json=appointment_data)

    async def update_appointment(self, appointment_id: str, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update appointment (async)"""
        return await self._make_request("PUT", f"/appointments/{appointment_id}", json=appointment_data)

    async def delete_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Delete appointment (async)"""
        return await self._make_request("DELETE", f"/appointments/{appointment_id}")

    # WEBHOOKS API

    async def create_webhook(self, url: str, events: List[str]) -> Dict[str, Any]:
        """Create webhook (async)"""
        data = {"url": url, "events": events}
        return await self._make_request("POST", "/webhooks/", json=data)

    async def get_webhooks(self) -> Dict[str, Any]:
        """Get webhooks (async)"""
        return await self._make_request("GET", "/webhooks/")

    async def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete webhook (async)"""
        return await self._make_request("DELETE", f"/webhooks/{webhook_id}")


if __name__ == "__main__":
    print("🔗 GHL API Client (Async) usage requires an event loop")
