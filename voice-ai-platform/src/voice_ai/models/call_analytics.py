"""Analytics aggregation models (Pydantic, not SQLAlchemy — computed from Call data)."""

from datetime import datetime

from pydantic import BaseModel, Field


class CallMetrics(BaseModel):
    """Aggregated call metrics for a time period."""

    total_calls: int = 0
    completed_calls: int = 0
    failed_calls: int = 0
    avg_duration_seconds: float = 0.0
    total_duration_minutes: float = 0.0
    avg_lead_score: float | None = None
    appointments_booked: int = 0
    pii_incidents: int = 0


class SentimentSummary(BaseModel):
    """Sentiment distribution across calls."""

    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0
    avg_sentiment: float = 0.0


class CostBreakdown(BaseModel):
    """Cost breakdown by component."""

    stt_total: float = 0.0
    tts_total: float = 0.0
    llm_total: float = 0.0
    telephony_total: float = 0.0
    total_cost: float = 0.0
    total_revenue: float = 0.0
    gross_margin: float = 0.0


class CallAnalyticsResponse(BaseModel):
    """Full analytics response."""

    period: str
    start_date: datetime
    end_date: datetime
    metrics: CallMetrics = Field(default_factory=CallMetrics)
    sentiment: SentimentSummary = Field(default_factory=SentimentSummary)
    costs: CostBreakdown = Field(default_factory=CostBreakdown)
    calls_by_bot_type: dict[str, int] = Field(default_factory=dict)
    calls_by_direction: dict[str, int] = Field(default_factory=dict)
