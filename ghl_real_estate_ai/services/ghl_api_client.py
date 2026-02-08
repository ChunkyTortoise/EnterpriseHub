"""
GoHighLevel API Client
Official GHL API integration with OAuth2, rate limiting, and error handling
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class GHLRateLimiter:
    """Rate limiter for GHL API (100 requests per minute)"""

    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]

        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request)
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                self.requests = []

        self.requests.append(now)


class GHLAPIClient:
    """
    GoHighLevel API Client

    Features:
    - OAuth2 authentication
    - Automatic token refresh
    - Rate limiting (100 req/min)
    - Retry logic with exponential backoff
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

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            access_token: Access token (if already obtained)
            refresh_token: Refresh token for token renewal
            location_id: GHL location (sub-account) ID
        """
        self.client_id = client_id or os.getenv("GHL_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GHL_CLIENT_SECRET")
        self.access_token = access_token or os.getenv("GHL_ACCESS_TOKEN")
        self.refresh_token = refresh_token or os.getenv("GHL_REFRESH_TOKEN")
        self.location_id = location_id or os.getenv("GHL_LOCATION_ID")

        self.token_expires_at: Optional[datetime] = None
        self.rate_limiter = GHLRateLimiter()

        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """
        Get OAuth2 authorization URL

        Args:
            redirect_uri: Redirect URI after authorization
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL
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

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from OAuth2 callback
            redirect_uri: Same redirect URI used in authorization

        Returns:
            Token response with access_token, refresh_token, expires_in
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }

        response = self.session.post(self.TOKEN_URL, data=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token")

        # Calculate expiration
        expires_in = token_data.get("expires_in", 3600)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        logger.info("Successfully obtained access token")
        return token_data

    def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh access token using refresh token

        Returns:
            New token response
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        response = self.session.post(self.TOKEN_URL, data=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        if "refresh_token" in token_data:
            self.refresh_token = token_data["refresh_token"]

        expires_in = token_data.get("expires_in", 3600)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        logger.info("Successfully refreshed access token")
        return token_data

    def _ensure_token_valid(self):
        """Ensure access token is valid, refresh if needed"""
        if not self.access_token:
            raise ValueError("No access token available. Call exchange_code_for_token() first.")

        # Refresh if token expires in less than 5 minutes
        if self.token_expires_at and datetime.now() > self.token_expires_at - timedelta(minutes=5):
            logger.info("Token expiring soon, refreshing...")
            self.refresh_access_token()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make authenticated API request

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests

        Returns:
            JSON response
        """
        self._ensure_token_valid()
        self.rate_limiter.wait_if_needed()

        url = f"{self.BASE_URL}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"

        # Add location ID if required and not in URL
        if self.location_id and "locationId" not in endpoint:
            params = kwargs.get("params", {})
            params["locationId"] = self.location_id
            kwargs["params"] = params

        response = self.session.request(method, url, headers=headers, **kwargs)

        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"GHL API Error: {e.response.status_code} - {e.response.text}")
            raise

    # ============================================================================
    # CONTACTS API
    # ============================================================================

    def get_contacts(self, limit: int = 100, skip: int = 0, query: str = None) -> Dict[str, Any]:
        """
        Get contacts from GHL

        Args:
            limit: Number of contacts to return (max 100)
            skip: Number of contacts to skip
            query: Search query

        Returns:
            Contacts response
        """
        params = {"limit": limit, "skip": skip}
        if query:
            params["query"] = query

        return self._make_request("GET", "/contacts/", params=params)

    def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get single contact by ID"""
        return self._make_request("GET", f"/contacts/{contact_id}")

    def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new contact

        Args:
            contact_data: Contact information (firstName, lastName, email, phone, etc.)

        Returns:
            Created contact
        """
        return self._make_request("POST", "/contacts/", json=contact_data)

    def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing contact"""
        return self._make_request("PUT", f"/contacts/{contact_id}", json=contact_data)

    def delete_contact(self, contact_id: str) -> Dict[str, Any]:
        """Delete contact"""
        return self._make_request("DELETE", f"/contacts/{contact_id}")

    def add_contact_tag(self, contact_id: str, tag: str) -> Dict[str, Any]:
        """Add tag to contact"""
        return self._make_request("POST", f"/contacts/{contact_id}/tags", json={"tags": [tag]})

    def remove_contact_tag(self, contact_id: str, tag: str) -> Dict[str, Any]:
        """Remove tag from contact"""
        return self._make_request("DELETE", f"/contacts/{contact_id}/tags", json={"tags": [tag]})

    # ============================================================================
    # OPPORTUNITIES (PIPELINES) API
    # ============================================================================

    def get_opportunities(self, pipeline_id: str = None, limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Get opportunities (deals)"""
        params = {"limit": limit, "skip": skip}
        if pipeline_id:
            params["pipelineId"] = pipeline_id

        return self._make_request("GET", "/opportunities/", params=params)

    def get_opportunity(self, opportunity_id: str) -> Dict[str, Any]:
        """Get single opportunity by ID"""
        return self._make_request("GET", f"/opportunities/{opportunity_id}")

    def create_opportunity(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new opportunity"""
        return self._make_request("POST", "/opportunities/", json=opportunity_data)

    def update_opportunity(self, opportunity_id: str, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update opportunity"""
        return self._make_request("PUT", f"/opportunities/{opportunity_id}", json=opportunity_data)

    def delete_opportunity(self, opportunity_id: str) -> Dict[str, Any]:
        """Delete opportunity"""
        return self._make_request("DELETE", f"/opportunities/{opportunity_id}")

    # ============================================================================
    # CONVERSATIONS API
    # ============================================================================

    def get_conversations(self, contact_id: str = None) -> Dict[str, Any]:
        """Get conversations"""
        params = {}
        if contact_id:
            params["contactId"] = contact_id

        return self._make_request("GET", "/conversations/", params=params)

    def get_messages(self, conversation_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get messages in a conversation"""
        params = {"limit": limit}
        return self._make_request("GET", f"/conversations/{conversation_id}/messages", params=params)

    def send_sms(self, contact_id: str, message: str, from_number: str = None) -> Dict[str, Any]:
        """
        Send SMS message to contact

        Args:
            contact_id: Contact ID
            message: Message text
            from_number: Sending phone number (optional)

        Returns:
            Message response
        """
        data = {"contactId": contact_id, "message": message, "type": "SMS"}
        if from_number:
            data["from"] = from_number

        return self._make_request("POST", "/conversations/messages", json=data)

    def send_email(self, contact_id: str, subject: str, body: str, from_email: str = None) -> Dict[str, Any]:
        """
        Send email to contact

        Args:
            contact_id: Contact ID
            subject: Email subject
            body: Email body (HTML or plain text)
            from_email: Sending email address (optional)

        Returns:
            Message response
        """
        data = {
            "contactId": contact_id,
            "subject": subject,
            "message": body,
            "type": "Email",
        }
        if from_email:
            data["from"] = from_email

        return self._make_request("POST", "/conversations/messages", json=data)

    # ============================================================================
    # CALENDARS API
    # ============================================================================

    def get_calendars(self) -> Dict[str, Any]:
        """Get all calendars"""
        return self._make_request("GET", "/calendars/")

    def get_appointments(
        self, calendar_id: str, start_time: datetime = None, end_time: datetime = None
    ) -> Dict[str, Any]:
        """Get appointments from calendar"""
        params = {"calendarId": calendar_id}
        if start_time:
            params["startTime"] = start_time.isoformat()
        if end_time:
            params["endTime"] = end_time.isoformat()

        return self._make_request("GET", "/appointments/", params=params)

    def create_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create appointment

        Args:
            appointment_data: Appointment details (calendarId, contactId, startTime, etc.)

        Returns:
            Created appointment
        """
        return self._make_request("POST", "/appointments/", json=appointment_data)

    def update_appointment(self, appointment_id: str, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update appointment"""
        return self._make_request("PUT", f"/appointments/{appointment_id}", json=appointment_data)

    def delete_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Delete appointment"""
        return self._make_request("DELETE", f"/appointments/{appointment_id}")

    # ============================================================================
    # WEBHOOKS API
    # ============================================================================

    def create_webhook(self, url: str, events: List[str]) -> Dict[str, Any]:
        """
        Create webhook subscription

        Args:
            url: Webhook URL to receive events
            events: List of events to subscribe to

        Returns:
            Webhook configuration
        """
        data = {"url": url, "events": events}
        return self._make_request("POST", "/webhooks/", json=data)

    def get_webhooks(self) -> Dict[str, Any]:
        """Get all webhook subscriptions"""
        return self._make_request("GET", "/webhooks/")

    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete webhook subscription"""
        return self._make_request("DELETE", f"/webhooks/{webhook_id}")


# ============================================================================
# DEMO & TESTING
# ============================================================================

if __name__ == "__main__":
    print("🔗 GHL API Client Demo\n")

    # Initialize client (uses environment variables)
    client = GHLAPIClient()

    print("✅ Client initialized")
    print(f"   Base URL: {client.BASE_URL}")
    print(f"   Has token: {bool(client.access_token)}")
    print(f"   Rate limit: {client.rate_limiter.max_requests} req/{client.rate_limiter.time_window}s")

    print("\n📋 Available Methods:")
    print("\n   Contacts:")
    print("   • get_contacts() - List contacts")
    print("   • get_contact(id) - Get single contact")
    print("   • create_contact(data) - Create contact")
    print("   • update_contact(id, data) - Update contact")
    print("   • add_contact_tag(id, tag) - Add tag")

    print("\n   Opportunities:")
    print("   • get_opportunities() - List deals")
    print("   • create_opportunity(data) - Create deal")
    print("   • update_opportunity(id, data) - Update deal")

    print("\n   Conversations:")
    print("   • get_conversations() - List conversations")
    print("   • send_sms(contact_id, message) - Send SMS")
    print("   • send_email(contact_id, subject, body) - Send email")

    print("\n   Calendars:")
    print("   • get_calendars() - List calendars")
    print("   • get_appointments(calendar_id) - List appointments")
    print("   • create_appointment(data) - Create appointment")

    print("\n   Webhooks:")
    print("   • create_webhook(url, events) - Subscribe to events")
    print("   • get_webhooks() - List webhooks")

    print("\n💡 Usage Example:")
    print(
        """
    # Initialize client
    client = GHLAPIClient(
        client_id="your_client_id",
        client_secret="your_secret",
        access_token="your_token",
        location_id="your_location_id"
    )
    
    # Get contacts
    contacts = client.get_contacts(limit=10)
    
    # Create contact
    new_contact = client.create_contact({
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com",
        "phone": "+1234567890"
    })
    
    # Send SMS
    client.send_sms(new_contact["id"], "Welcome to our service!")
    """
    )

    print("\n⚠️  Setup Required:")
    print("   Set environment variables:")
    print("   • GHL_CLIENT_ID")
    print("   • GHL_CLIENT_SECRET")
    print("   • GHL_ACCESS_TOKEN (or use OAuth flow)")
    print("   • GHL_LOCATION_ID")
