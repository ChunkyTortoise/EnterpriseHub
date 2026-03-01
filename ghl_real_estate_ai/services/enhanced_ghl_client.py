"""
Enhanced Production GoHighLevel Client for Service 6 Lead Recovery & Nurture Engine.

Extends the existing GHL client with enterprise-grade features:
- Advanced contact management and lead tracking
- Pipeline and opportunity management
- Workflow automation and campaign management
- Real-time webhook processing
- Enhanced error handling and retry logic
- Rate limiting and connection pooling
- Comprehensive audit logging
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientTimeout
from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.ghl_webhook_types import (
    GHLAPIResponse,
    GHLCampaignData,
    GHLContactData,
    GHLContactUpdatePayload,
    GHLDashboardMetrics,
    GHLHealthCheckResult,
    GHLOpportunityData,
    GHLSearchParams,
    GHLWebhookPayload,
)
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.circuit_breaker import CircuitBreakerConfig, get_circuit_manager
from ghl_real_estate_ai.services.database_service import DatabaseService, log_communication
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.optimized_cache_service import cached

logger = get_logger(__name__)


class ContactStatus(Enum):
    """GHL contact status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DND = "dnd"  # Do Not Disturb
    UNSUBSCRIBED = "unsubscribed"


class OpportunityStatus(Enum):
    """GHL opportunity status enumeration."""

    OPEN = "open"
    WON = "won"
    LOST = "lost"
    ABANDONED = "abandoned"


class WorkflowStatus(Enum):
    """GHL workflow status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class PipelineStage(Enum):
    """Common pipeline stages."""

    LEAD = "lead"
    QUALIFIED = "qualified"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class GHLConfig(BaseModel):
    """Enhanced GHL client configuration."""

    api_key: str = settings.ghl_api_key
    location_id: str = settings.ghl_location_id
    base_url: str = "https://services.leadconnectorhq.com"
    webhook_base_url: str = settings.webhook_base_url
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_requests_per_minute: int = 300

    @field_validator("api_key", "location_id")
    @classmethod
    def validate_required_fields(cls, v, info: ValidationInfo):
        if not v or v in ["dummy", "your_ghl_api_key_here", "your_location_id_here"]:
            if not settings.test_mode:
                raise ValueError(f"Valid GHL {info.field_name} is required for production")
        return v


class GHLContact(BaseModel):
    """GHL contact model."""

    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}
    source: Optional[str] = None
    status: ContactStatus = ContactStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class GHLOpportunity(BaseModel):
    """GHL opportunity model."""

    id: str
    name: str
    contact_id: str
    pipeline_id: str
    pipeline_stage_id: str
    status: OpportunityStatus
    monetary_value: float = 0.0
    assigned_to: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    close_date: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class GHLWorkflow(BaseModel):
    """GHL workflow model."""

    id: str
    name: str
    status: WorkflowStatus
    trigger_type: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class GHLAPIException(Exception):
    """GHL API specific exception."""

    def __init__(self, message: str, status_code: int = None, error_code: str = None, details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class EnhancedGHLClient(GHLClient):
    """
    Enhanced production GHL client.

    Extends the base GHL client with enterprise features:
    - Advanced contact and opportunity management
    - Workflow automation and campaign tracking
    - Real-time webhook processing
    - Enhanced error handling and retry logic
    - Rate limiting and performance optimization
    """

    def __init__(
        self, config: GHLConfig = None, cache_service: CacheService = None, database_service: DatabaseService = None
    ):
        """Initialize enhanced GHL client."""
        self.config = config or GHLConfig()
        self.cache_service = cache_service or CacheService()
        self.database_service = database_service

        # Initialize base client
        super().__init__(self.config.api_key, self.config.location_id)

        # Override base URL and headers for enhanced functionality
        self.base_url = self.config.base_url
        self.headers.update({"Version": "2021-07-28", "User-Agent": "Service6-Lead-Engine/1.0"})

        # Session and rate limiting
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_semaphore = asyncio.Semaphore(self.config.rate_limit_requests_per_minute)

        # Circuit breaker for fault tolerance
        circuit_manager = get_circuit_manager()
        self.circuit_breaker = circuit_manager.get_or_create_breaker("ghl")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure HTTP session is created."""
        if not self.session:
            timeout = ClientTimeout(total=self.config.timeout)

            self.session = aiohttp.ClientSession(
                timeout=timeout, headers=self.headers, connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
            )

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        use_rate_limit: bool = True,
    ) -> GHLAPIResponse:
        """Make rate-limited HTTP request to GHL API."""
        if settings.test_mode:
            logger.info(f"[TEST MODE] {method} {endpoint}")
            return {"status": "mocked", "test_mode": True}

        await self._ensure_session()

        # Apply rate limiting
        if use_rate_limit:
            async with self._rate_limit_semaphore:
                return await self._execute_request(method, endpoint, data, params)
        else:
            return await self._execute_request(method, endpoint, data, params)

    async def _execute_request(
        self, method: str, endpoint: str, data: Dict[str, Any] = None, params: Dict[str, Any] = None
    ) -> GHLAPIResponse:
        """Execute HTTP request with circuit breaker and retry logic."""

        async def _make_http_request():
            """Internal function to execute the actual HTTP request"""
            url = f"{self.base_url}/{endpoint.lstrip('/')}"

            for attempt in range(self.config.max_retries + 1):
                try:
                    if method.upper() == "GET":
                        async with self.session.get(url, params=params) as response:
                            return await self._handle_response(response)
                    elif method.upper() == "POST":
                        async with self.session.post(url, json=data, params=params) as response:
                            return await self._handle_response(response)
                    elif method.upper() == "PUT":
                        async with self.session.put(url, json=data, params=params) as response:
                            return await self._handle_response(response)
                    elif method.upper() == "DELETE":
                        async with self.session.delete(url, params=params) as response:
                            return await self._handle_response(response)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                except aiohttp.ClientError as e:
                    if attempt < self.config.max_retries:
                        delay = self.config.retry_delay * (2**attempt)
                        logger.warning(f"GHL API request failed, retrying in {delay}s: {e}")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise GHLAPIException(f"Network error after {self.config.max_retries} retries: {e}")

                except Exception as e:
                    logger.error(f"Unexpected error in GHL API request: {e}")
                    raise GHLAPIException(f"Unexpected error: {e}")

        # Execute through circuit breaker
        try:
            return await self.circuit_breaker.call(_make_http_request)
        except Exception as e:
            logger.error(f"GHL request failed through circuit breaker: {e}")
            raise

    async def _handle_response(self, response: aiohttp.ClientResponse) -> GHLAPIResponse:
        """Handle GHL API response."""
        try:
            response_data = await response.json()
        except aiohttp.ContentTypeError:
            response_text = await response.text()
            response_data = {"message": response_text}

        if response.status in [200, 201, 202]:
            return response_data
        elif response.status == 429:
            raise GHLAPIException("Rate limit exceeded", response.status)
        elif response.status in [401, 403]:
            raise GHLAPIException("Authentication failed", response.status)
        elif response.status == 404:
            raise GHLAPIException("Resource not found", response.status)
        else:
            error_msg = response_data.get("message", f"HTTP {response.status}")
            raise GHLAPIException(error_msg, response.status, response_data.get("code"), response_data)

    # ============================================================================
    # Enhanced Contact Management
    # ============================================================================

    @cached(ttl=300, key_prefix="ghl_contact")
    async def get_contact(self, contact_id: str) -> Optional[GHLContact]:
        """Get contact by ID with caching."""
        try:
            response = await self._make_request("GET", f"/contacts/{contact_id}")

            if response and "contact" in response:
                contact_data = response["contact"]
                return GHLContact(
                    id=contact_data["id"],
                    first_name=contact_data.get("firstName"),
                    last_name=contact_data.get("lastName"),
                    name=contact_data.get("name"),
                    email=contact_data.get("email"),
                    phone=contact_data.get("phone"),
                    tags=contact_data.get("tags", []),
                    custom_fields=contact_data.get("customFields", {}),
                    source=contact_data.get("source"),
                    created_at=self._parse_datetime(contact_data.get("dateAdded")),
                    updated_at=self._parse_datetime(contact_data.get("dateUpdated")),
                )
            return None

        except GHLAPIException as e:
            if e.status_code == 404:
                return None
            logger.error(f"Failed to get contact {contact_id}: {e.message}")
            raise

    async def create_contact(self, contact_data: GHLContactData, lead_id: str = None) -> GHLContact:
        """Create new contact in GHL."""
        if settings.test_mode:
            mock_id = f"demo_{int(datetime.utcnow().timestamp())}"
            logger.info(
                "[TEST MODE] Returning mocked contact for create_contact",
                extra={"contact_id": mock_id, "test_mode": True},
            )
            return GHLContact(
                id=mock_id,
                first_name=contact_data.get("first_name"),
                last_name=contact_data.get("last_name"),
                name=contact_data.get("name")
                or f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip(),
                email=contact_data.get("email"),
                phone=contact_data.get("phone"),
                tags=contact_data.get("tags", []),
                custom_fields=contact_data.get("custom_fields", {}),
                source=contact_data.get("source", "Service6-Lead-Engine"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        payload = {
            "locationId": self.config.location_id,
            "firstName": contact_data.get("first_name", ""),
            "lastName": contact_data.get("last_name", ""),
            "name": contact_data.get("name")
            or f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip(),
            "email": contact_data.get("email"),
            "phone": contact_data.get("phone"),
            "source": contact_data.get("source", "Service6-Lead-Engine"),
            "tags": contact_data.get("tags", []),
        }

        # Add custom fields
        if "custom_fields" in contact_data:
            payload["customFields"] = [
                {"id": field_id, "value": value} for field_id, value in contact_data["custom_fields"].items()
            ]

        try:
            response = await self._make_request("POST", "/contacts", data=payload)

            contact_id = response.get("contact", {}).get("id")
            if not contact_id:
                raise GHLAPIException("Contact creation failed: No ID returned")

            # Log to database if available
            if self.database_service and lead_id:
                await log_communication(
                    {
                        "lead_id": lead_id,
                        "channel": "webhook",
                        "direction": "outbound",
                        "content": f"Created GHL contact: {payload['name']}",
                        "status": "sent",
                        "metadata": {"ghl_contact_id": contact_id, "action": "create_contact"},
                    }
                )

            logger.info(f"Created GHL contact {contact_id} for {payload.get('email', payload.get('phone'))}")

            # Return the created contact
            return await self.get_contact(contact_id)

        except Exception as e:
            logger.error(f"Failed to create contact: {e}")
            raise GHLAPIException(f"Contact creation failed: {e}")

    async def update_contact(self, contact_id: str, updates: GHLContactUpdatePayload) -> bool:
        """Update existing contact."""
        payload = {}

        # Map field names
        if "first_name" in updates:
            payload["firstName"] = updates["first_name"]
        if "last_name" in updates:
            payload["lastName"] = updates["last_name"]
        if "email" in updates:
            payload["email"] = updates["email"]
        if "phone" in updates:
            payload["phone"] = updates["phone"]
        if "tags" in updates:
            payload["tags"] = updates["tags"]

        # Handle custom fields — skip entries with empty/None field IDs
        if "custom_fields" in updates:
            custom_fields = []
            for field_id, value in updates["custom_fields"].items():
                if not field_id:
                    logger.warning("Skipping custom field with empty ID during contact update")
                    continue
                custom_fields.append({"id": field_id, "value": value})
            if custom_fields:
                payload["customFields"] = custom_fields

        try:
            await self._make_request("PUT", f"/contacts/{contact_id}", data=payload)

            # Clear cache
            await self.cache_service.delete(f"ghl_contact:{contact_id}")

            logger.info(f"Updated GHL contact {contact_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update contact {contact_id}: {e}")
            return False

    async def search_contacts(self, search_params: GHLSearchParams) -> List[GHLContact]:
        """Search contacts with various criteria."""
        params = {"locationId": self.config.location_id, "limit": search_params.get("limit", 100)}

        # Add search criteria
        if "email" in search_params:
            params["email"] = search_params["email"]
        if "phone" in search_params:
            params["phone"] = search_params["phone"]
        if "query" in search_params:
            params["query"] = search_params["query"]
        if "tags" in search_params:
            params["tags"] = ",".join(search_params["tags"])

        try:
            response = await self._make_request("GET", "/contacts/search", params=params)

            contacts = []
            for contact_data in response.get("contacts", []):
                contacts.append(
                    GHLContact(
                        id=contact_data["id"],
                        first_name=contact_data.get("firstName"),
                        last_name=contact_data.get("lastName"),
                        name=contact_data.get("name"),
                        email=contact_data.get("email"),
                        phone=contact_data.get("phone"),
                        tags=contact_data.get("tags", []),
                        custom_fields=contact_data.get("customFields", {}),
                        source=contact_data.get("source"),
                        created_at=self._parse_datetime(contact_data.get("dateAdded")),
                        updated_at=self._parse_datetime(contact_data.get("dateUpdated")),
                    )
                )

            return contacts

        except Exception as e:
            logger.error(f"Contact search failed: {e}")
            return []

    # ============================================================================
    # Opportunity Management
    # ============================================================================

    async def create_opportunity(self, opportunity_data: GHLOpportunityData) -> str:
        """Create opportunity in GHL pipeline."""
        payload = {
            "locationId": self.config.location_id,
            "name": opportunity_data["name"],
            "contactId": opportunity_data["contact_id"],
            "pipelineId": opportunity_data["pipeline_id"],
            "pipelineStageId": opportunity_data["pipeline_stage_id"],
            "monetaryValue": opportunity_data.get("monetary_value", 0),
            "assignedTo": opportunity_data.get("assigned_to"),
            "source": opportunity_data.get("source", "Service6-Lead-Engine"),
        }

        try:
            response = await self._make_request("POST", "/opportunities", data=payload)

            opportunity_id = response.get("opportunity", {}).get("id")
            if not opportunity_id:
                raise GHLAPIException("Opportunity creation failed: No ID returned")

            logger.info(f"Created opportunity {opportunity_id} for contact {opportunity_data['contact_id']}")
            return opportunity_id

        except Exception as e:
            logger.error(f"Failed to create opportunity: {e}")
            raise GHLAPIException(f"Opportunity creation failed: {e}")

    async def update_opportunity_stage(self, opportunity_id: str, stage_id: str, reason: str = None) -> bool:
        """Update opportunity pipeline stage."""
        payload = {"pipelineStageId": stage_id}

        if reason:
            payload["reason"] = reason

        try:
            await self._make_request("PUT", f"/opportunities/{opportunity_id}", data=payload)

            logger.info(f"Updated opportunity {opportunity_id} to stage {stage_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update opportunity stage: {e}")
            return False

    async def get_opportunities_by_contact(self, contact_id: str) -> List[GHLOpportunity]:
        """Get all opportunities for a contact."""
        params = {"locationId": self.config.location_id, "contactId": contact_id}

        try:
            response = await self._make_request("GET", "/opportunities/search", params=params)

            opportunities = []
            for opp_data in response.get("opportunities", []):
                opportunities.append(
                    GHLOpportunity(
                        id=opp_data["id"],
                        name=opp_data["name"],
                        contact_id=opp_data["contactId"],
                        pipeline_id=opp_data["pipelineId"],
                        pipeline_stage_id=opp_data["pipelineStageId"],
                        status=OpportunityStatus(opp_data.get("status", "open")),
                        monetary_value=float(opp_data.get("monetaryValue", 0)),
                        assigned_to=opp_data.get("assignedTo"),
                        source=opp_data.get("source"),
                        created_at=self._parse_datetime(opp_data.get("dateCreated")),
                        updated_at=self._parse_datetime(opp_data.get("dateUpdated")),
                    )
                )

            return opportunities

        except Exception as e:
            logger.error(f"Failed to get opportunities for contact {contact_id}: {e}")
            return []

    # ============================================================================
    # Calendar Management
    # ============================================================================

    async def get_free_slots(self, calendar_id: str) -> List[Dict[str, Any]]:
        """Get available appointment slots from a GHL calendar.

        Retrieves free slots and filters to 9am-5pm PT window.

        Args:
            calendar_id: GHL calendar ID.

        Returns:
            List of up to 3 slot dicts with keys: start, end, formatted.
        """
        if settings.test_mode:
            logger.info(
                f"[TEST MODE] get_free_slots calendar={calendar_id}",
                extra={"calendar_id": calendar_id, "test_mode": True},
            )
            # Return 3 mock slots within 9am-5pm PT
            base = datetime.utcnow().replace(hour=17, minute=0, second=0, microsecond=0)
            mock_slots = []
            for i, hour in enumerate([9, 11, 14]):
                start = base.replace(hour=hour + 8)  # PT offset (UTC-8)
                end = start + timedelta(minutes=30)
                start_iso = start.strftime("%Y-%m-%dT%H:%M:%SZ")
                end_iso = end.strftime("%Y-%m-%dT%H:%M:%SZ")
                mock_slots.append(
                    {
                        "start": start_iso,
                        "end": end_iso,
                        "formatted": start.strftime("%A, %B %d at %I:%M %p"),
                    }
                )
            return mock_slots

        try:
            now = datetime.utcnow()
            start_date = now.strftime("%Y-%m-%d")
            end_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")

            response = await self._make_request(
                "GET",
                f"/calendars/{calendar_id}/free-slots",
                params={
                    "startDate": start_date,
                    "endDate": end_date,
                    "timezone": "America/Los_Angeles",
                },
            )

            raw_slots = response.get("slots", []) if isinstance(response, dict) else []

            # Filter to 9am-5pm PT and limit to 3 slots
            filtered = []
            for slot in raw_slots:
                start_str = slot.get("startTime") or slot.get("start", "")
                end_str = slot.get("endTime") or slot.get("end", "")
                if not start_str:
                    continue
                try:
                    dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    # Rough PT filter: UTC hour 17-01 maps to 9am-5pm PT (UTC-8)
                    pt_hour = (dt.hour - 8) % 24
                    if 9 <= pt_hour < 17:
                        formatted = dt.strftime("%A, %B %d at %I:%M %p")
                        filtered.append(
                            {
                                "start": start_str,
                                "end": end_str,
                                "formatted": formatted,
                            }
                        )
                except (ValueError, AttributeError):
                    continue

                if len(filtered) >= 3:
                    break

            return filtered

        except Exception as e:
            logger.warning(f"Failed to get free slots for calendar {calendar_id}: {e}")
            return []

    async def create_appointment(
        self,
        calendar_id: str,
        contact_id: str,
        start_time: str,
        end_time: str,
        title: str = "Consultation",
        assigned_user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create an appointment on a GHL calendar.

        Args:
            calendar_id: GHL calendar ID.
            contact_id: GHL contact ID.
            start_time: ISO format start time.
            end_time: ISO format end time.
            title: Appointment title.
            assigned_user_id: Optional GHL user ID to assign the appointment to.

        Returns:
            Appointment dict on success, None on failure.
        """
        if settings.test_mode:
            logger.info(
                f"[TEST MODE] create_appointment calendar={calendar_id} contact={contact_id}",
                extra={
                    "calendar_id": calendar_id,
                    "contact_id": contact_id,
                    "test_mode": True,
                },
            )
            return {
                "id": f"appt_mock_{int(datetime.utcnow().timestamp())}",
                "calendarId": calendar_id,
                "contactId": contact_id,
                "startTime": start_time,
                "endTime": end_time,
                "title": title,
                "status": "confirmed",
            }

        payload: Dict[str, Any] = {
            "calendarId": calendar_id,
            "locationId": self.config.location_id,
            "contactId": contact_id,
            "startTime": start_time,
            "endTime": end_time,
            "title": title,
        }
        if assigned_user_id:
            payload["assignedUserId"] = assigned_user_id

        try:
            response = await self._make_request("POST", "/calendars/events", data=payload)
            logger.info(
                f"Created appointment for contact {contact_id} in calendar {calendar_id}",
                extra={"contact_id": contact_id, "calendar_id": calendar_id},
            )
            return response
        except Exception as e:
            logger.error(
                f"Failed to create appointment for contact {contact_id}: {e}",
                extra={"contact_id": contact_id, "calendar_id": calendar_id, "error": str(e)},
            )
            return None

    # ============================================================================
    # Enhanced Messaging
    # ============================================================================

    async def send_sms_with_tracking(
        self, contact_id: str, message: str, lead_id: str = None, campaign_id: str = None, template_id: str = None
    ) -> GHLAPIResponse:
        """Send SMS with enhanced tracking."""
        try:
            # Use the base class send_message method
            from ghl_real_estate_ai.api.schemas.ghl import MessageType

            result = await self.send_message(contact_id, message, MessageType.SMS)

            # Enhanced logging
            if self.database_service and lead_id:
                await log_communication(
                    {
                        "lead_id": lead_id,
                        "channel": "sms",
                        "direction": "outbound",
                        "content": message,
                        "status": "sent",
                        "campaign_id": campaign_id,
                        "template_id": template_id,
                        "metadata": {
                            "ghl_contact_id": contact_id,
                            "ghl_message_id": result.get("messageId"),
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Enhanced SMS sending failed: {e}")
            raise

    async def send_email_with_tracking(
        self,
        contact_id: str,
        subject: str,
        html_content: str,
        plain_content: str = None,
        lead_id: str = None,
        campaign_id: str = None,
        template_id: str = None,
    ) -> GHLAPIResponse:
        """Send email with enhanced tracking."""
        try:
            # For now, use basic message sending - can be enhanced with dedicated email API
            from ghl_real_estate_ai.api.schemas.ghl import MessageType

            email_content = f"Subject: {subject}\n\n{plain_content or html_content}"
            result = await self.send_message(contact_id, email_content, MessageType.Email)

            # Enhanced logging
            if self.database_service and lead_id:
                await log_communication(
                    {
                        "lead_id": lead_id,
                        "channel": "email",
                        "direction": "outbound",
                        "content": subject,
                        "status": "sent",
                        "campaign_id": campaign_id,
                        "template_id": template_id,
                        "metadata": {
                            "ghl_contact_id": contact_id,
                            "ghl_message_id": result.get("messageId"),
                            "subject": subject,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Enhanced email sending failed: {e}")
            raise

    # ============================================================================
    # Workflow Management
    # ============================================================================

    async def get_workflows(self) -> List[GHLWorkflow]:
        """Get all workflows for the location."""
        params = {"locationId": self.config.location_id}

        try:
            response = await self._make_request("GET", "/workflows", params=params)

            workflows = []
            for workflow_data in response.get("workflows", []):
                workflows.append(
                    GHLWorkflow(
                        id=workflow_data["id"],
                        name=workflow_data["name"],
                        status=WorkflowStatus(workflow_data.get("status", "active")),
                        trigger_type=workflow_data.get("triggerType", "manual"),
                        created_at=self._parse_datetime(workflow_data.get("dateCreated")),
                        updated_at=self._parse_datetime(workflow_data.get("dateUpdated")),
                    )
                )

            return workflows

        except Exception as e:
            logger.error(f"Failed to get workflows: {e}")
            return []

    async def trigger_workflow_with_tracking(
        self, contact_id: str, workflow_id: str, lead_id: str = None
    ) -> GHLAPIResponse:
        """Trigger workflow with enhanced tracking."""
        try:
            result = await self.trigger_workflow(contact_id, workflow_id)

            # Enhanced logging
            if self.database_service and lead_id:
                await log_communication(
                    {
                        "lead_id": lead_id,
                        "channel": "webhook",
                        "direction": "outbound",
                        "content": f"Triggered workflow: {workflow_id}",
                        "status": "sent",
                        "metadata": {
                            "ghl_contact_id": contact_id,
                            "workflow_id": workflow_id,
                            "action": "trigger_workflow",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Enhanced workflow trigger failed: {e}")
            raise

    # ============================================================================
    # Campaign Management
    # ============================================================================

    async def create_campaign(self, campaign_data: GHLCampaignData) -> str:
        """Create a new campaign in GHL."""
        # GHL uses workflows for campaigns - create a workflow
        payload = {
            "locationId": self.config.location_id,
            "name": campaign_data["name"],
            "triggerType": campaign_data.get("trigger_type", "manual"),
            "status": "active",
        }

        try:
            response = await self._make_request("POST", "/workflows", data=payload)

            campaign_id = response.get("workflow", {}).get("id")
            if not campaign_id:
                raise GHLAPIException("Campaign creation failed: No ID returned")

            logger.info(f"Created campaign {campaign_id}: {campaign_data['name']}")
            return campaign_id

        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            raise GHLAPIException(f"Campaign creation failed: {e}")

    async def enroll_contact_in_campaign(self, contact_id: str, campaign_id: str) -> bool:
        """Enroll contact in a campaign (trigger workflow)."""
        try:
            result = await self.trigger_workflow_with_tracking(contact_id, campaign_id)

            logger.info(f"Enrolled contact {contact_id} in campaign {campaign_id}")
            return bool(result)

        except Exception as e:
            logger.error(f"Failed to enroll contact in campaign: {e}")
            return False

    # ============================================================================
    # Webhook Processing
    # ============================================================================

    async def process_webhook(self, webhook_data: GHLWebhookPayload) -> GHLAPIResponse:
        """Process incoming GHL webhook."""
        try:
            webhook_type = webhook_data.get("type")
            webhook_data.get("contactId")
            location_id = webhook_data.get("locationId")

            # Verify location
            if location_id != self.config.location_id:
                logger.warning(f"Webhook for different location: {location_id}")
                return {"status": "ignored", "reason": "different_location"}

            # Process by webhook type
            if webhook_type == "ContactCreate":
                return await self._process_contact_create_webhook(webhook_data)
            elif webhook_type == "ContactUpdate":
                return await self._process_contact_update_webhook(webhook_data)
            elif webhook_type == "InboundMessage":
                return await self._process_inbound_message_webhook(webhook_data)
            elif webhook_type == "OpportunityCreate":
                return await self._process_opportunity_create_webhook(webhook_data)
            elif webhook_type == "OpportunityStageUpdate":
                return await self._process_opportunity_stage_webhook(webhook_data)
            else:
                logger.info(f"Unhandled webhook type: {webhook_type}")
                return {"status": "unhandled", "type": webhook_type}

        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _process_contact_create_webhook(self, webhook_data: GHLWebhookPayload) -> GHLAPIResponse:
        """Process contact creation webhook."""
        contact_id = webhook_data.get("contactId")
        contact_data = webhook_data.get("contact", {})

        # Log the event
        if self.database_service:
            # Try to find or create lead record
            email = contact_data.get("email")
            phone = contact_data.get("phone")

            if email or phone:
                # Create lead record if it doesn't exist
                # This would integrate with the database service
                pass

        logger.info(f"Processed contact creation webhook for {contact_id}")
        return {"status": "processed", "action": "contact_created"}

    async def _process_inbound_message_webhook(self, webhook_data: GHLWebhookPayload) -> GHLAPIResponse:
        """Process inbound message webhook."""
        contact_id = webhook_data.get("contactId")
        message_data = webhook_data.get("message", {})
        message_type = message_data.get("type", "SMS")
        message_body = message_data.get("body", "")

        # Log the inbound message
        if self.database_service:
            await log_communication(
                {
                    "lead_id": None,  # Would need to map contact_id to lead_id
                    "channel": message_type.lower(),
                    "direction": "inbound",
                    "content": message_body,
                    "status": "received",
                    "metadata": {"ghl_contact_id": contact_id, "webhook_data": webhook_data},
                }
            )

        logger.info(f"Processed inbound {message_type} from contact {contact_id}")
        return {"status": "processed", "action": "message_logged"}

    # ============================================================================
    # Analytics & Reporting
    # ============================================================================

    async def get_enhanced_dashboard_data(self) -> GHLDashboardMetrics:
        """Get enhanced dashboard data with Service 6 specific metrics."""
        try:
            # Get base dashboard data
            base_data = self.fetch_dashboard_data()

            # Add enhanced metrics for Service 6
            conversations = base_data.get("conversations", [])
            base_data.get("opportunities", [])

            # Calculate Service 6 specific metrics
            silent_leads = [c for c in conversations if self._is_lead_silent(c)]

            hot_leads = [c for c in conversations if "Hot Lead" in c.get("tags", [])]

            response_metrics = await self._calculate_response_metrics(conversations)

            enhanced_data = {
                **base_data,
                "service6_metrics": {
                    "total_leads": len(conversations),
                    "silent_leads": len(silent_leads),
                    "hot_leads": len(hot_leads),
                    "avg_response_time_minutes": response_metrics["avg_response_time"],
                    "leads_responded_within_60s": response_metrics["within_60s"],
                    "nurture_sequences_active": await self._get_active_sequences_count(),
                    "conversion_rate_this_week": await self._calculate_weekly_conversion_rate(),
                },
                "health_check": await self.health_check(),
            }

            return enhanced_data

        except Exception as e:
            logger.error(f"Failed to get enhanced dashboard data: {e}")
            return {"error": str(e), "status": "failed"}

    def _is_lead_silent(self, conversation: Dict[str, Any]) -> bool:
        """Check if lead has been silent for more than 24 hours."""
        last_message_date = conversation.get("lastMessageDate")
        if not last_message_date:
            return True

        try:
            last_message_time = self._parse_datetime(last_message_date)
            if last_message_time:
                silence_duration = datetime.utcnow() - last_message_time
                return silence_duration > timedelta(hours=24)
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to check lead silence: {e}")
            pass

        return False

    async def _calculate_response_metrics(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate response time metrics."""
        # This would analyze conversation timestamps to calculate real response times
        # For now, return mock data structure
        return {
            "avg_response_time": 45,  # minutes
            "within_60s": 85,  # percentage
            "within_5min": 92,  # percentage
        }

    async def _get_active_sequences_count(self) -> int:
        """Get count of active nurture sequences."""
        try:
            workflows = await self.get_workflows()
            active_workflows = [w for w in workflows if w.status == WorkflowStatus.ACTIVE]
            return len(active_workflows)
        except Exception as e:
            logger.debug(f"Failed to get active sequences count: {e}")
            return 0

    async def _calculate_weekly_conversion_rate(self) -> float:
        """Calculate conversion rate for the current week."""
        # This would analyze opportunities created vs leads in the same period
        # For now, return placeholder
        return 32.5  # percentage

    # ============================================================================
    # Health Check
    # ============================================================================

    async def health_check(self) -> GHLHealthCheckResult:
        """Enhanced health check for GHL connectivity."""
        try:
            if settings.test_mode:
                return {
                    "status": "healthy",
                    "mode": "test",
                    "api_accessible": True,
                    "location_verified": True,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Test basic connectivity
            response = await self._make_request("GET", f"/locations/{self.config.location_id}", use_rate_limit=False)

            location_name = response.get("location", {}).get("name", "Unknown")

            return {
                "status": "healthy",
                "api_accessible": True,
                "location_verified": True,
                "location_name": location_name,
                "rate_limit_remaining": self._rate_limit_semaphore._value,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except GHLAPIException as e:
            return {
                "status": "unhealthy" if e.status_code not in [429] else "rate_limited",
                "api_accessible": e.status_code not in [401, 403],
                "error": e.message,
                "status_code": e.status_code,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "api_accessible": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # ============================================================================
    # Utility Methods
    # ============================================================================

    def _parse_datetime(self, date_string: str) -> Optional[datetime]:
        """Parse GHL date string to datetime."""
        if not date_string:
            return None

        try:
            # Try different formats
            for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue

            # If none work, try ISO format
            return datetime.fromisoformat(date_string.replace("Z", "+00:00"))

        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse date '{date_string}': {str(e)}")
            return None

    # ============================================================================
    # SDR Support Methods
    # ============================================================================

    def _build_ghl_contact(self, contact_data: Dict[str, Any]) -> "GHLContact":
        """Build a GHLContact from a raw API response dict."""
        return GHLContact(
            id=contact_data["id"],
            first_name=contact_data.get("firstName"),
            last_name=contact_data.get("lastName"),
            name=contact_data.get("name"),
            email=contact_data.get("email"),
            phone=contact_data.get("phone"),
            tags=contact_data.get("tags", []),
            custom_fields=contact_data.get("customFields", {}),
            source=contact_data.get("source"),
            created_at=self._parse_datetime(contact_data.get("dateAdded")),
            updated_at=self._parse_datetime(contact_data.get("dateUpdated")),
            last_activity_at=self._parse_datetime(contact_data.get("lastActivityAt")),
        )

    async def get_contacts_by_pipeline_stage(
        self,
        location_id: str,
        stage_id: str,
        limit: int = 50,
    ) -> List["GHLContact"]:
        """Return contacts currently in a specific GHL pipeline stage."""
        if settings.test_mode:
            logger.info(
                f"[TEST MODE] get_contacts_by_pipeline_stage stage={stage_id}",
                extra={"stage_id": stage_id, "test_mode": True},
            )
            return []

        params = {
            "locationId": location_id,
            "pipelineStageId": stage_id,
            "limit": limit,
        }
        try:
            response = await self._make_request("GET", "/contacts/search", params=params)
            return [self._build_ghl_contact(c) for c in response.get("contacts", [])]
        except Exception as exc:
            logger.error(f"get_contacts_by_pipeline_stage stage={stage_id}: {exc}")
            return []

    async def get_contacts_inactive_since(
        self,
        location_id: str,
        since: datetime,
        limit: int = 50,
    ) -> List["GHLContact"]:
        """Return contacts with no activity since *since* (stale leads)."""
        if settings.test_mode:
            logger.info(
                "[TEST MODE] get_contacts_inactive_since",
                extra={"since": since.isoformat(), "test_mode": True},
            )
            return []

        params = {
            "locationId": location_id,
            "lastActivityBefore": since.isoformat(),
            "limit": limit,
        }
        try:
            response = await self._make_request("GET", "/contacts/search", params=params)
            return [self._build_ghl_contact(c) for c in response.get("contacts", [])]
        except Exception as exc:
            logger.error(f"get_contacts_inactive_since: {exc}")
            return []

    async def send_sms(
        self,
        contact_id: str,
        message: str,
        location_id: Optional[str] = None,
    ) -> bool:
        """Send an SMS to a contact. Returns True on success."""
        try:
            await self.send_sms_with_tracking(contact_id=contact_id, message=message)
            return True
        except Exception as exc:
            logger.error(f"send_sms contact={contact_id}: {exc}")
            return False

    async def trigger_workflow(  # type: ignore[override]
        self,
        contact_id: str,
        workflow_id: str,
        location_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Trigger a GHL workflow for a contact, optionally passing event_data.

        Overrides base GHLClient.trigger_workflow to accept SDR-specific
        location_id and event_data parameters (both optional for backward compat).
        """
        if not workflow_id:
            logger.warning("trigger_workflow called with empty workflow_id, skipping")
            return {}

        if settings.test_mode:
            logger.info(
                f"[TEST MODE] trigger_workflow workflow={workflow_id} contact={contact_id}",
                extra={"contact_id": contact_id, "workflow_id": workflow_id, "test_mode": True},
            )
            return {"status": "mocked", "workflow_id": workflow_id}

        payload: Dict[str, Any] = {"contactId": contact_id}
        if event_data:
            payload.update(event_data)

        try:
            response = await self._make_request(
                "POST",
                f"/workflows/{workflow_id}/trigger",
                data=payload,
            )
            logger.info(f"[GHL] Workflow triggered workflow={workflow_id} contact={contact_id}")
            return response or {}
        except Exception as exc:
            logger.error(f"trigger_workflow workflow={workflow_id} contact={contact_id}: {exc}")
            raise


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":

    async def test_enhanced_ghl_client():
        """Test enhanced GHL client functionality."""
        async with EnhancedGHLClient() as ghl:
            try:
                # Test health check
                health = await ghl.health_check()
                print(f"Health: {health['status']}")

                # Test contact search
                contacts = await ghl.search_contacts({"limit": 5})
                print(f"Found {len(contacts)} contacts")

                # Test dashboard data
                dashboard = await ghl.get_enhanced_dashboard_data()
                print(f"Dashboard metrics: {dashboard.get('service6_metrics', {})}")

            except Exception as e:
                print(f"Test failed: {e}")

    # Run test
    asyncio.run(test_enhanced_ghl_client())
