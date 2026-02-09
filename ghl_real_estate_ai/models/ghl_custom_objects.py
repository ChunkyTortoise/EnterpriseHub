"""
GHL Custom Objects Models - Section 4 of 2026 Strategic Roadmap
Defines the structure for AI-enriched property profiles in GHL.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PropertyAIProfile(BaseModel):
    """
    Custom Object: "Property_AI_Profile"
    Used to sync EnterpriseHub intelligence back to GHL.
    """

    mls_id: str = Field(..., description="Unique MLS identifier")
    address: str
    ai_market_heat: float = Field(..., ge=0, le=100, description="Proprietary heat index")
    digital_twin_url: Optional[str] = None
    cma_pdf_url: Optional[str] = None
    zillow_zestimate: float
    ai_valuation: float
    valuation_confidence: float = Field(..., ge=0, le=100)
    last_updated: datetime = Field(default_factory=datetime.now)

    # Associations (Mocked for GHL logic)
    related_contacts: List[str] = []  # List of Contact IDs
    active_offers: int = 0


class GHLSyncStatus(BaseModel):
    object_id: str
    status: str  # synced, pending, failed
    timestamp: datetime = Field(default_factory=datetime.now)
    fields_updated: List[str]
