from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class Interaction(BaseModel):
    contact_id: str
    property_id: str
    action: Literal["like", "pass"]
    location_id: Optional[str] = None
    time_on_card: Optional[float] = None
    feedback: Optional[Dict[str, Any]] = None


class RootResponse(BaseModel):
    message: str
    docs: str
    health: str
    reset: str
    state: str
    state_details: str
    environment: str


class HealthResponse(BaseModel):
    status: str
    service: str


class ResetResponse(BaseModel):
    status: str
    reset: Dict[str, int]


class StateSnapshot(BaseModel):
    inventory_leads: int
    inventory_properties: int
    inventory_interactions: int
    ghl_actions: int
    appointments: int


class StateResponse(BaseModel):
    status: str
    state: StateSnapshot


class PropertyCard(BaseModel):
    id: str
    address: str
    price: int
    beds: int
    baths: int


class DeckResponse(BaseModel):
    deck: list[PropertyCard]


class SwipeResponse(BaseModel):
    status: str
    high_intent: bool
    trigger_sms: bool
    adjustments: list[str]


class InventoryInteractionSnapshot(BaseModel):
    lead_id: str
    property_id: str
    action: str
    feedback: Dict[str, Any]
    time_on_card: Optional[float] = None
    timestamp: str


class InventoryDetailedState(BaseModel):
    lead_count: int
    property_count: int
    interaction_count: int
    recent_interactions: list[InventoryInteractionSnapshot]


class GHLDetailedState(BaseModel):
    action_count: int
    recent_actions: list[Dict[str, Any]]


class AppointmentBookingSnapshot(BaseModel):
    contact_id: str
    slot_time: str
    property_address: str


class AppointmentDetailedState(BaseModel):
    booking_count: int
    recent_bookings: list[AppointmentBookingSnapshot]


class DetailedStateSnapshot(BaseModel):
    inventory: InventoryDetailedState
    ghl: GHLDetailedState
    appointment: AppointmentDetailedState


class DetailedStateResponse(BaseModel):
    status: str
    details: DetailedStateSnapshot


class VapiToolResult(BaseModel):
    toolCallId: Optional[str] = None
    result: str


class VapiToolFunctionPayload(BaseModel):
    arguments: Dict[str, Any] | str = Field(default_factory=dict)


class VapiToolCallPayload(BaseModel):
    id: Optional[str] = None
    function: VapiToolFunctionPayload = Field(default_factory=VapiToolFunctionPayload)


class VapiToolPayload(BaseModel):
    toolCall: VapiToolCallPayload = Field(default_factory=VapiToolCallPayload)


class VapiToolResponse(BaseModel):
    results: list[VapiToolResult]


class GHLSyncResponse(BaseModel):
    status: str
    synced_count: int


class GHLField(BaseModel):
    id: str
    name: str
    type: str


class GHLFieldsResponse(BaseModel):
    fields: list[GHLField]


class GHLFieldsUnavailableResponse(BaseModel):
    message: str
