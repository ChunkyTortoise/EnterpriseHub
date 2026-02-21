"""Pydantic models for buyer persona classification.

Maps to the database schema defined in:
    alembic/versions/2026_02_10_008_add_buyer_personas_table.py

Table: buyer_personas
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


class ConversationTurnDict(TypedDict, total=False):
    """TypedDict for conversation turn in persona input."""

    role: str
    content: str
    timestamp: Optional[str]


class LeadDataDict(TypedDict, total=False):
    """TypedDict for lead data in persona input."""

    lead_id: str
    email: Optional[str]
    phone: Optional[str]
    source: Optional[str]
    tags: List[str]


class BuyerPersonaType(str, Enum):
    """Buyer persona types for classification."""

    FIRST_TIME = "first_time"
    UPSIZER = "upsizer"
    DOWNSIZER = "downsizer"
    INVESTOR = "investor"
    RELOCATOR = "relocator"
    LUXURY = "luxury"
    UNKNOWN = "unknown"


class BuyerPersonaDB(BaseModel):
    """Row from the buyer_personas table."""

    id: Optional[int] = None
    lead_id: str = Field(..., description="Lead/contact ID from GHL")
    persona_type: BuyerPersonaType = Field(..., description="Classified buyer persona")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    detected_signals: List[str] = Field(default_factory=list, description="Detected keyword signals")
    behavioral_signals: Dict[str, float] = Field(default_factory=dict, description="Behavioral signal scores")
    conversation_turns: int = Field(default=0, description="Number of conversation turns analyzed")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BuyerPersonaClassification(BaseModel):
    """Result of buyer persona classification."""

    persona_type: BuyerPersonaType
    confidence: float
    detected_signals: List[str]
    behavioral_signals: Dict[str, float]
    primary_indicators: List[str]
    secondary_indicators: List[str]


class BuyerPersonaInsights(BaseModel):
    """Communication recommendations per persona."""

    tone: str
    content_focus: str
    urgency_level: str
    key_messages: List[str]
    recommended_questions: List[str]


class BuyerPersonaUpdateRequest(BaseModel):
    """Request to update buyer persona with new conversation data."""

    lead_id: str
    conversation_history: List[ConversationTurnDict]
    lead_data: Optional[LeadDataDict] = None


class BuyerPersonaUpdateResponse(BaseModel):
    """Response from buyer persona update."""

    lead_id: str
    persona_type: BuyerPersonaType
    confidence: float
    detected_signals: List[str]
    previous_persona: Optional[BuyerPersonaType] = None
    persona_changed: bool = False
