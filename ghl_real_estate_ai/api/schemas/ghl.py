"""
GoHighLevel webhook schemas.

Defines Pydantic models for incoming GHL webhooks and outgoing responses.
Based on GHL API documentation: https://highlevel.stoplight.io/
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MessageType(str, Enum):
    """Supported message types from GHL."""

    SMS = "SMS"
    EMAIL = "Email"
    LIVE_CHAT = "Live_Chat"
    WHATSAPP = "WhatsApp"


class MessageDirection(str, Enum):
    """Message direction (inbound vs outbound)."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class GHLMessage(BaseModel):
    """Message payload from GHL webhook."""

    type: MessageType
    body: str
    direction: MessageDirection
    timestamp: Optional[datetime] = None


class GHLContact(BaseModel):
    """Contact information from GHL."""

    id: Optional[str] = Field(None, alias="contactId")
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    phone: Optional[str] = None
    email: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict, alias="customFields")


class GHLWebhookEvent(BaseModel):
    """
    Incoming webhook event from GoHighLevel.

    This is the top-level schema for all inbound messages.

    Supports both GHL's native flat format and our custom nested format:
    - Native flat: {"contactId": "...", "messageType": "TYPE_SMS", "body": "...", "direction": "inbound"}
    - Custom nested: {"contactId": "...", "message": {"type": "SMS", "body": "...", "direction": "inbound"}}
    """

    type: str  # "InboundMessage", "OutboundMessage", etc.
    contact_id: str = Field(..., alias="contactId")
    location_id: str = Field(..., alias="locationId")
    message: GHLMessage
    contact: Optional[GHLContact] = None

    model_config = ConfigDict(populate_by_name=True)  # Allow both snake_case and camelCase

    @model_validator(mode="before")
    @classmethod
    def handle_ghl_native_format(cls, data: Any) -> Any:
        """
        Accept GHL's native flat webhook format in addition to our custom nested format.

        GHL's native InboundMessage webhook sends a flat payload:
          { "contactId": "...", "locationId": "...", "messageType": "TYPE_SMS",
            "body": "Hello", "direction": "inbound", ... }

        Our custom workflow template sends the nested format:
          { "contactId": "...", "locationId": "...",
            "message": {"type": "SMS", "body": "Hello", "direction": "inbound"},
            "contact": {"contactId": "...", "tags": [...]} }

        This validator converts the flat format to nested so Pydantic validation passes.
        """
        if not isinstance(data, dict):
            return data

        # Convert flat format to nested if the "message" key is absent
        if "message" not in data:
            raw_type = str(data.get("messageType", data.get("type", "SMS")))
            # GHL sends "TYPE_SMS" -> normalise to "SMS"
            if raw_type.upper().startswith("TYPE_"):
                raw_type = raw_type[5:]
            _type_map = {
                "SMS": "SMS",
                "EMAIL": "Email",
                "LIVE_CHAT": "Live_Chat",
                "CHAT": "Live_Chat",
                "WHATSAPP": "WhatsApp",
            }
            msg_type = _type_map.get(raw_type.upper(), "SMS")
            data["message"] = {
                "type": msg_type,
                "body": data.get("body", ""),
                "direction": data.get("direction", "inbound"),
            }

        # Ensure a contact object always exists (even if minimal)
        # so handler code can safely access event.contact.tags
        if "contact" not in data or data["contact"] is None:
            data["contact"] = {
                "contactId": data.get("contactId", ""),
                "firstName": data.get("contactName", ""),
                # Propagate top-level tags (present in some GHL webhook formats)
                # so the handler doesn't have to do a separate API fetch just to
                # discover the contact's tags.
                "tags": data.get("tags", []),
            }

        return data


class GHLTagWebhookEvent(BaseModel):
    """
    Tag-added webhook event from GoHighLevel.

    Used to trigger proactive outreach when "Needs Qualifying" is applied.
    """

    type: str  # "ContactTagAdded" or similar
    contact_id: str = Field(..., alias="contactId")
    location_id: str = Field(..., alias="locationId")
    tag: str
    contact: GHLContact

    model_config = ConfigDict(populate_by_name=True)


class ActionType(str, Enum):
    """Actions that can be triggered in GHL."""

    SEND_MESSAGE = "send_message"
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"
    UPDATE_CUSTOM_FIELD = "update_custom_field"
    TRIGGER_WORKFLOW = "trigger_workflow"
    CREATE_TASK = "create_task"
    CREATE_APPOINTMENT = "create_appointment"
    UPDATE_APPOINTMENT = "update_appointment"


class GHLAction(BaseModel):
    """Action to be executed in GHL."""

    type: ActionType
    tag: Optional[str] = None  # For add_tag/remove_tag
    field: Optional[str] = None  # For update_custom_field
    value: Optional[Any] = None  # For update_custom_field
    workflow_id: Optional[str] = None  # For trigger_workflow
    message: Optional[str] = None  # For send_message
    channel: Optional[MessageType] = None  # For send_message

    # Appointment-specific fields
    calendar_id: Optional[str] = None  # For create_appointment
    appointment_id: Optional[str] = None  # For update_appointment
    start_time: Optional[str] = None  # ISO format datetime
    end_time: Optional[str] = None  # ISO format datetime
    appointment_title: Optional[str] = None
    appointment_type: Optional[str] = None  # buyer_consultation, listing_appointment, etc.
    assigned_user_id: Optional[str] = None  # Jorge's user ID


class GHLWebhookResponse(BaseModel):
    """
    Response sent back to GHL after processing webhook.

    This schema defines what we return to GHL, including the AI response
    and any actions to trigger (tags, custom fields, workflows).
    """

    success: bool
    message: str  # AI-generated response
    actions: List[GHLAction] = Field(default_factory=list)


class AppointmentStatus(str, Enum):
    """Appointment status values for GHL calendar."""

    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "noShow"


class GHLCalendarEvent(BaseModel):
    """Calendar event from GHL API."""

    id: Optional[str] = None
    title: str
    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")
    calendar_id: str = Field(..., alias="calendarId")
    location_id: str = Field(..., alias="locationId")
    contact_id: Optional[str] = Field(None, alias="contactId")
    assigned_user_id: Optional[str] = Field(None, alias="assignedUserId")
    status: AppointmentStatus = AppointmentStatus.CONFIRMED
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class GHLTimeSlot(BaseModel):
    """Available time slot from GHL calendar API."""

    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")
    available: bool = True
    calendar_id: str = Field(..., alias="calendarId")

    model_config = ConfigDict(populate_by_name=True)


class CreateAppointmentRequest(BaseModel):
    """Request schema for creating appointments in GHL."""

    calendar_id: str = Field(..., alias="calendarId")
    location_id: str = Field(..., alias="locationId")
    contact_id: str = Field(..., alias="contactId")
    start_time: str = Field(..., alias="startTime")  # ISO format
    end_time: Optional[str] = Field(None, alias="endTime")  # ISO format
    title: str
    status: AppointmentStatus = AppointmentStatus.CONFIRMED
    assigned_user_id: Optional[str] = Field(None, alias="assignedUserId")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class AppointmentBookingEvent(BaseModel):
    """Event data for appointment booking analytics."""

    contact_id: str
    appointment_type: str  # buyer_consultation, listing_appointment, etc.
    booking_method: str  # auto_booked, manual_scheduled, fallback
    lead_score: int
    appointment_time: datetime
    timezone: str = "America/Los_Angeles"
    confirmation_sent: bool = False
    booking_duration_seconds: Optional[int] = None  # Time to book from qualification

    model_config = ConfigDict(arbitrary_types_allowed=True)
    error: Optional[str] = None


class ConversationContext(BaseModel):
    """Internal conversation context (stored in database)."""

    contact_id: str
    location_id: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    extracted_preferences: Dict[str, Any] = Field(default_factory=dict)
    lead_score: int = 0
    last_interaction: Optional[datetime] = None
    qualified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Backward compatibility aliases
ContactData = GHLContact
MessageData = GHLMessage
