"""
Lead pipeline schemas for demo ingestion and status responses.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class LeadPipelineIngestRequest(BaseModel):
    """Request model for demo lead ingestion."""
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    source: str = Field(default="demo_form")
    lead_type: Optional[str] = Field(default="buyer")
    initial_message: Optional[str] = Field(default="")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "first_name": "Alex",
            "last_name": "Reed",
            "email": "alex@example.com",
            "phone": "+19095551234",
            "source": "demo_form",
            "lead_type": "seller",
            "initial_message": "Considering selling in 2 months, what is my home worth?"
        }
    })


class LeadPipelineStatus(BaseModel):
    """Status response for pipeline processing."""
    success: bool
    contact_id: str
    location_id: str
    lead_score: int = 0
    classification: str = "cold"
    appointment_status: Optional[str] = None
    message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
