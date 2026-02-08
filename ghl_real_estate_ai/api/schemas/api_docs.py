"""API documentation response schemas for OpenAPI spec enhancement.

Provides Pydantic models used as response_model annotations on key demo
routes to produce rich Swagger/ReDoc documentation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ── Leads ───────────────────────────────────────────────────────────────


class LeadSummary(BaseModel):
    """A single lead summary for demo display."""

    id: str = Field(..., description="Unique lead identifier", json_schema_extra={"example": "lead_001"})
    first_name: str = Field(..., description="Lead first name", json_schema_extra={"example": "Maria"})
    last_name: str = Field(..., description="Lead last name", json_schema_extra={"example": "Garcia"})
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    source: str = Field(..., description="Lead source channel", json_schema_extra={"example": "Zillow"})
    score: int = Field(..., ge=0, le=100, description="AI qualification score (0-100)")
    temperature: str = Field(
        ...,
        description="Lead temperature tag",
        json_schema_extra={"example": "Hot-Lead"},
    )
    stage: str = Field(..., description="Pipeline stage", json_schema_extra={"example": "Qualified"})
    city: str = Field(default="Rancho Cucamonga", description="Target city")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    last_activity: str = Field(..., description="ISO 8601 last activity timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "lead_001",
                "first_name": "Maria",
                "last_name": "Garcia",
                "email": "maria.garcia@example.com",
                "phone": "+19095551234",
                "source": "Zillow",
                "score": 85,
                "temperature": "Hot-Lead",
                "stage": "Qualified",
                "city": "Rancho Cucamonga",
                "created_at": "2026-01-15T10:30:00",
                "last_activity": "2026-02-07T14:22:00",
            }
        }
    )


class LeadListResponse(BaseModel):
    """Response for GET /demo/leads."""

    leads: List[LeadSummary] = Field(..., description="List of demo leads")
    total: int = Field(..., ge=0, description="Total number of leads returned")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "leads": [
                    {
                        "id": "lead_001",
                        "first_name": "Maria",
                        "last_name": "Garcia",
                        "email": "maria.garcia@example.com",
                        "phone": "+19095551234",
                        "source": "Zillow",
                        "score": 85,
                        "temperature": "Hot-Lead",
                        "stage": "Qualified",
                        "city": "Rancho Cucamonga",
                        "created_at": "2026-01-15T10:30:00",
                        "last_activity": "2026-02-07T14:22:00",
                    }
                ],
                "total": 1,
            }
        }
    )


# ── Pipeline ────────────────────────────────────────────────────────────


class StageMetrics(BaseModel):
    """Metrics for a single pipeline stage."""

    count: int = Field(..., ge=0, description="Number of leads in this stage")
    avg_score: float = Field(..., description="Average lead score in this stage")
    avg_days_in_stage: float = Field(..., ge=0.0, description="Average days spent in this stage")


class PipelineSummary(BaseModel):
    """Aggregated pipeline summary statistics."""

    total_leads: int = Field(..., ge=0, description="Total leads across all stages")
    conversion_rate: float = Field(..., ge=0.0, le=1.0, description="Overall conversion rate")
    avg_days_to_close: float = Field(..., ge=0.0, description="Average days to close")
    pipeline_value: int = Field(..., ge=0, description="Total estimated pipeline value in USD")
    temperature_distribution: Dict[str, int] = Field(..., description="Count of leads per temperature tag")


class PipelineResponse(BaseModel):
    """Response for GET /demo/pipeline."""

    snapshot_at: str = Field(..., description="ISO 8601 snapshot timestamp")
    stages: Dict[str, StageMetrics] = Field(..., description="Per-stage metrics")
    summary: PipelineSummary = Field(..., description="Aggregated pipeline summary")


# ── Health ──────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Response for GET /demo/health."""

    status: str = Field(
        ...,
        description="Overall system health: healthy, degraded, or critical",
        json_schema_extra={"example": "healthy"},
    )
    active_bots: int = Field(..., ge=0, description="Number of active bot instances")
    uptime_pct: float = Field(..., ge=0.0, le=100.0, description="System uptime percentage")
    version: str = Field(..., description="API version string", json_schema_extra={"example": "5.0.1"})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "active_bots": 4,
                "uptime_pct": 99.87,
                "version": "5.0.1",
            }
        }
    )


# ── Bot Status ──────────────────────────────────────────────────────────


class BotStatusItem(BaseModel):
    """Status of a single bot instance."""

    name: str = Field(..., description="Bot display name")
    type: str = Field(..., description="Bot type: lead, buyer, or seller")
    status: str = Field(..., description="Current status: active, idle, or error")
    uptime_hours: float = Field(..., ge=0.0, description="Hours since last restart")
    conversations_today: int = Field(..., ge=0, description="Conversations handled today")


class BotStatusResponse(BaseModel):
    """Response for GET /demo/bots."""

    bots: List[BotStatusItem] = Field(..., description="List of active bot instances")
    total_conversations_today: int = Field(..., ge=0, description="Total conversations across all bots")


# ── OpenAPI Tag Metadata ────────────────────────────────────────────────

OPENAPI_TAGS = [
    {
        "name": "leads",
        "description": "Lead management -- create, score, and qualify real estate leads.",
    },
    {
        "name": "pipeline",
        "description": "Pipeline analytics -- stage progression, conversion tracking, and forecasting.",
    },
    {
        "name": "bots",
        "description": "Bot management -- Jorge Lead, Buyer, and Seller bot orchestration.",
    },
    {
        "name": "analytics",
        "description": "Business intelligence -- dashboards, KPIs, and performance metrics.",
    },
    {
        "name": "health",
        "description": "System health -- uptime, latency, and error rate monitoring.",
    },
    {
        "name": "Demo",
        "description": "Demo endpoints -- hardcoded sample data for zero-config API exploration.",
    },
]
