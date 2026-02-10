"""
TypedDict definitions for GHL API data structures and webhook payloads.

Provides type safety for GHL API responses and internal data structures
without runtime overhead. Follow the pattern from seller_bot_state.py.
"""

from __future__ import annotations

from typing import Any, TypedDict

# ============================================================================
# GHL API Response Types
# ============================================================================


class GHLAPIResponse(TypedDict, total=False):
    """Standard GHL API response structure."""

    success: bool
    data: dict[str, Any]
    error: str
    status_code: int
    details: dict[str, Any]


# ============================================================================
# Contact Data Types
# ============================================================================


class GHLCustomField(TypedDict, total=False):
    """Custom field structure for GHL contacts."""

    id: str
    value: str


class GHLContactData(TypedDict, total=False):
    """Contact data structure from GHL API.

    Includes both camelCase (GHL API format) and snake_case (internal format)
    field variants since both are used across the codebase.
    """

    # Common fields
    id: str
    name: str
    email: str
    phone: str
    tags: list[str]
    source: str
    status: str
    locationId: str

    # GHL API format (camelCase)
    contactId: str
    firstName: str
    lastName: str
    customFields: list[GHLCustomField] | dict[str, Any]
    dateAdded: str
    dateUpdated: str
    dateOfBirth: str
    address1: str
    city: str
    state: str
    postalCode: str
    country: str
    companyName: str
    website: str

    # Internal format (snake_case) used by EnhancedGHLClient
    first_name: str
    last_name: str
    custom_fields: dict[str, Any]

    # Extended fields used by GHLIntegrationService mock data
    preferences: list[str]
    budget: int | float


class GHLSearchParams(TypedDict, total=False):
    """Parameters for searching GHL contacts."""

    locationId: str
    query: str
    email: str
    phone: str
    tags: list[str]
    limit: int
    skip: int


class GHLContactUpdatePayload(TypedDict, total=False):
    """Payload for updating GHL contact.

    Includes both camelCase and snake_case variants for compatibility.
    """

    # GHL API format (camelCase)
    firstName: str
    lastName: str
    name: str
    email: str
    phone: str
    tags: list[str]
    customFields: list[GHLCustomField]
    source: str
    address1: str
    city: str
    state: str
    postalCode: str

    # Internal format (snake_case) used by EnhancedGHLClient.update_contact
    first_name: str
    last_name: str
    custom_fields: dict[str, Any]


# ============================================================================
# Webhook Payload Types
# ============================================================================


class GHLWebhookMessage(TypedDict, total=False):
    """Message data from GHL webhook."""

    type: str
    body: str
    direction: str
    messageId: str
    timestamp: str
    contentType: str
    attachments: list[dict[str, Any]]


class GHLWebhookPayload(TypedDict, total=False):
    """Raw webhook payload from GHL (before Pydantic validation)."""

    type: str
    contactId: str
    locationId: str
    message: GHLWebhookMessage
    contact: GHLContactData
    tag: str
    conversationId: str


# ============================================================================
# Opportunity/Pipeline Types
# ============================================================================


class GHLOpportunityData(TypedDict, total=False):
    """Opportunity (deal) data structure.

    Includes both camelCase and snake_case variants for compatibility.
    """

    id: str
    name: str
    status: str
    source: str
    notes: str
    locationId: str

    # GHL API format (camelCase)
    contactId: str
    pipelineId: str
    pipelineStageId: str
    monetaryValue: float
    assignedTo: str
    dateCreated: str
    dateUpdated: str
    closeDate: str

    # Internal format (snake_case) used by EnhancedGHLClient
    contact_id: str
    pipeline_id: str
    pipeline_stage_id: str
    monetary_value: float
    assigned_to: str


class GHLPipelineStage(TypedDict, total=False):
    """Pipeline stage data."""

    id: str
    name: str
    position: int


class GHLPipeline(TypedDict, total=False):
    """Pipeline data."""

    id: str
    name: str
    stages: list[GHLPipelineStage]


# ============================================================================
# Calendar/Appointment Types
# ============================================================================


class GHLCalendarSlot(TypedDict, total=False):
    """Available calendar slot."""

    start_time: str
    end_time: str
    calendar_id: str
    available: bool


class GHLAppointmentData(TypedDict, total=False):
    """Appointment data structure."""

    id: str
    calendarId: str
    contactId: str
    locationId: str
    title: str
    startTime: str
    endTime: str
    status: str
    appointmentType: str
    notes: str
    assignedUserId: str


# ============================================================================
# Conversation Context Types
# ============================================================================


class ConversationMessage(TypedDict, total=False):
    """Single conversation message."""

    role: str
    content: str
    timestamp: str


class ConversationContext(TypedDict, total=False):
    """Conversation context stored in memory service."""

    conversation_history: list[ConversationMessage]
    extracted_preferences: dict[str, Any]
    seller_preferences: dict[str, Any]
    initial_outreach_sent: bool
    initial_outreach_sent_at: str
    lead_metadata: dict[str, Any]
    last_interaction_at: str
    created_at: str
    conversation_stage: str
    last_lead_score: int
    predictive_score: dict[str, Any]
    is_returning_lead: bool
    hours_since_last_interaction: float
    seller_temperature: str
    pending_appointment: dict[str, Any]


# ============================================================================
# Workflow/Campaign Types
# ============================================================================


class GHLWorkflowData(TypedDict, total=False):
    """Workflow data structure."""

    id: str
    name: str
    status: str
    triggerType: str
    dateCreated: str
    dateUpdated: str


class GHLCampaignData(TypedDict, total=False):
    """Campaign data structure."""

    id: str
    name: str
    status: str
    type: str
    startDate: str
    endDate: str

    # Internal format (snake_case) used by EnhancedGHLClient.create_campaign
    trigger_type: str


# ============================================================================
# Analytics/Metrics Types
# ============================================================================


class GHLDashboardMetrics(TypedDict, total=False):
    """Dashboard metrics from GHL."""

    total_leads: int
    silent_leads: int
    hot_leads: int
    avg_response_time_minutes: float
    leads_responded_within_60s: int
    nurture_sequences_active: int
    conversion_rate_this_week: float


class GHLHealthCheckResult(TypedDict, total=False):
    """Health check result."""

    status: str
    mode: str
    api_accessible: bool
    location_verified: bool
    location_name: str
    rate_limit_remaining: int
    timestamp: str
    error: str
    status_code: int


# ============================================================================
# Custom Objects Types
# ============================================================================


class GHLCustomObjectData(TypedDict, total=False):
    """Custom object data (e.g., Property AI Profile)."""

    id: str
    locationId: str
    objectType: str
    data: dict[str, Any]
    createdAt: str
    updatedAt: str
