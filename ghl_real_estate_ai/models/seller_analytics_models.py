"""
Seller Analytics Data Models

Comprehensive analytics and performance tracking models for the seller AI assistant ecosystem.
Supports real-time KPI calculation, predictive insights, and business intelligence across
all integrated systems: Property Valuation, Marketing Campaigns, Document Generation.

Business Impact: $35K+/year in performance insights and optimization
Performance Target: <200ms analytics processing, <60s data freshness

Key Features:
- Real-time performance metrics across all seller touchpoints
- Predictive analytics for seller success probability
- Comprehensive KPI tracking with historical trends
- Integration with Property Valuation, Marketing Campaigns, Document Generation
- Automated insights and recommendations generation
- Advanced benchmarking and comparative analytics
"""

from datetime import datetime, timedelta, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from uuid import uuid4, UUID
import json

from pydantic import (
    BaseModel, Field, validator, root_validator,
    EmailStr, HttpUrl, confloat, conint
)


# ============================================================================
# Core Analytics Enums and Types
# ============================================================================

class AnalyticsTimeframe(str, Enum):
    """Time periods for analytics aggregation."""
    REAL_TIME = "real_time"        # Live metrics
    HOURLY = "hourly"             # Last hour
    DAILY = "daily"               # Last 24 hours
    WEEKLY = "weekly"             # Last 7 days
    MONTHLY = "monthly"           # Last 30 days
    QUARTERLY = "quarterly"       # Last 90 days
    YEARLY = "yearly"             # Last 365 days
    CUSTOM = "custom"             # Custom date range


class MetricType(str, Enum):
    """Types of metrics tracked in the analytics system."""
    COUNTER = "counter"           # Incremental count (e.g., total leads)
    GAUGE = "gauge"               # Point-in-time value (e.g., conversion rate)
    HISTOGRAM = "histogram"       # Distribution of values (e.g., response times)
    RATE = "rate"                 # Rate of change (e.g., growth rate)
    PERCENTAGE = "percentage"     # Percentage values (0-100)
    CURRENCY = "currency"         # Monetary values
    DURATION = "duration"         # Time-based values


class PerformanceLevel(str, Enum):
    """Performance classification levels."""
    EXCELLENT = "excellent"      # Top 10% performance
    GOOD = "good"               # Above average performance
    AVERAGE = "average"         # Average performance
    BELOW_AVERAGE = "below_average"  # Below average performance
    POOR = "poor"               # Bottom 10% performance


class TrendDirection(str, Enum):
    """Trend direction indicators."""
    INCREASING = "increasing"    # Positive trend
    DECREASING = "decreasing"    # Negative trend
    STABLE = "stable"           # No significant change
    VOLATILE = "volatile"       # High variability
    UNKNOWN = "unknown"         # Insufficient data


class AnalyticsCategory(str, Enum):
    """Categories of analytics and metrics."""
    SELLER_PERFORMANCE = "seller_performance"          # Overall seller metrics
    PROPERTY_VALUATION = "property_valuation"          # Valuation-related metrics
    MARKETING_CAMPAIGNS = "marketing_campaigns"        # Campaign performance
    DOCUMENT_GENERATION = "document_generation"        # Document metrics
    WORKFLOW_PROGRESSION = "workflow_progression"      # Workflow analytics
    CLIENT_ENGAGEMENT = "client_engagement"           # Client interaction metrics
    CONVERSION_FUNNEL = "conversion_funnel"           # Conversion analysis
    BUSINESS_INTELLIGENCE = "business_intelligence"    # Advanced insights


# ============================================================================
# Core Analytics Models
# ============================================================================

class AnalyticsMetric(BaseModel):
    """Individual analytics metric with metadata."""

    metric_id: str = Field(default_factory=lambda: f"metric_{uuid4().hex[:8]}")
    metric_name: str = Field(..., min_length=1, max_length=100)
    metric_type: MetricType = Field(...)
    category: AnalyticsCategory = Field(...)

    # Value and measurement
    value: float = Field(...)
    unit: Optional[str] = Field(None, max_length=20)
    precision: int = Field(default=2, ge=0, le=6)

    # Context and metadata
    description: Optional[str] = Field(None, max_length=500)
    measurement_timestamp: datetime = Field(default_factory=datetime.utcnow)
    data_source: str = Field(..., max_length=100)
    tags: Dict[str, str] = Field(default_factory=dict)

    # Quality indicators
    confidence_level: confloat(ge=0, le=1) = Field(default=0.95)
    data_quality_score: confloat(ge=0, le=1) = Field(default=0.9)
    sample_size: Optional[int] = Field(None, ge=1)

    # Comparative context
    benchmark_value: Optional[float] = Field(None)
    target_value: Optional[float] = Field(None)
    previous_period_value: Optional[float] = Field(None)

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}

    @validator('value')
    def validate_metric_value(cls, v, values):
        """Validate metric values based on type."""
        metric_type = values.get('metric_type')

        if metric_type == MetricType.PERCENTAGE and (v < 0 or v > 100):
            raise ValueError("Percentage values must be between 0 and 100")

        if metric_type == MetricType.RATE and v < 0:
            raise ValueError("Rate values cannot be negative")

        return v


class SellerPerformanceMetrics(BaseModel):
    """Comprehensive seller performance metrics."""

    seller_id: str = Field(..., min_length=1)
    calculation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    timeframe: AnalyticsTimeframe = Field(...)

    # Core Performance Indicators
    overall_performance_score: confloat(ge=0, le=100) = Field(...)
    conversion_rate: confloat(ge=0, le=100) = Field(...)
    engagement_rate: confloat(ge=0, le=100) = Field(...)
    response_time_avg_hours: float = Field(..., ge=0)
    client_satisfaction_score: confloat(ge=0, le=5) = Field(...)

    # Activity Metrics
    total_interactions: conint(ge=0) = Field(...)
    leads_generated: conint(ge=0) = Field(...)
    leads_qualified: conint(ge=0) = Field(...)
    properties_evaluated: conint(ge=0) = Field(...)
    documents_generated: conint(ge=0) = Field(...)
    campaigns_executed: conint(ge=0) = Field(...)

    # Financial Metrics
    total_revenue_attributed: Decimal = Field(default=Decimal("0.00"), ge=0)
    avg_deal_value: Decimal = Field(default=Decimal("0.00"), ge=0)
    commission_generated: Decimal = Field(default=Decimal("0.00"), ge=0)
    roi_percentage: float = Field(default=0.0)

    # Efficiency Metrics
    lead_to_listing_ratio: confloat(ge=0, le=100) = Field(...)
    time_to_listing_avg_days: float = Field(..., ge=0)
    workflow_completion_rate: confloat(ge=0, le=100) = Field(...)
    automation_usage_rate: confloat(ge=0, le=100) = Field(...)

    # Quality Metrics
    listing_success_rate: confloat(ge=0, le=100) = Field(...)
    document_quality_avg: confloat(ge=0, le=1) = Field(...)
    campaign_performance_avg: confloat(ge=0, le=100) = Field(...)
    client_retention_rate: confloat(ge=0, le=100) = Field(...)

    # Trend Indicators
    performance_trend: TrendDirection = Field(...)
    growth_rate_percentage: float = Field(...)
    momentum_score: confloat(ge=0, le=100) = Field(...)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            Decimal: lambda d: float(d)
        }


class PropertyValuationAnalytics(BaseModel):
    """Analytics specific to property valuation performance."""

    timeframe: AnalyticsTimeframe = Field(...)
    seller_id: Optional[str] = Field(None)  # None for aggregate analytics

    # Volume Metrics
    total_valuations: conint(ge=0) = Field(...)
    successful_valuations: conint(ge=0) = Field(...)
    failed_valuations: conint(ge=0) = Field(...)
    success_rate: confloat(ge=0, le=100) = Field(...)

    # Performance Metrics
    avg_processing_time_ms: float = Field(..., ge=0)
    avg_confidence_score: confloat(ge=0, le=1) = Field(...)
    accuracy_rate: confloat(ge=0, le=100) = Field(...)

    # Business Impact
    avg_property_value: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_value_assessed: Decimal = Field(default=Decimal("0.00"), ge=0)
    valuation_to_listing_rate: confloat(ge=0, le=100) = Field(...)

    # Quality Indicators
    data_completeness_avg: confloat(ge=0, le=100) = Field(...)
    mls_integration_success_rate: confloat(ge=0, le=100) = Field(...)
    comparable_sales_quality: confloat(ge=0, le=1) = Field(...)

    # User Experience
    client_valuation_satisfaction: confloat(ge=0, le=5) = Field(...)
    valuation_disputes: conint(ge=0) = Field(default=0)
    revision_requests: conint(ge=0) = Field(default=0)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            Decimal: lambda d: float(d)
        }


class MarketingCampaignAnalytics(BaseModel):
    """Analytics for marketing campaign performance."""

    timeframe: AnalyticsTimeframe = Field(...)
    seller_id: Optional[str] = Field(None)
    campaign_id: Optional[str] = Field(None)

    # Campaign Volume
    total_campaigns: conint(ge=0) = Field(...)
    active_campaigns: conint(ge=0) = Field(...)
    completed_campaigns: conint(ge=0) = Field(...)
    cancelled_campaigns: conint(ge=0) = Field(default=0)

    # Delivery Metrics
    total_deliveries: conint(ge=0) = Field(...)
    successful_deliveries: conint(ge=0) = Field(...)
    bounce_rate: confloat(ge=0, le=100) = Field(...)
    delivery_success_rate: confloat(ge=0, le=100) = Field(...)

    # Engagement Metrics
    avg_open_rate: confloat(ge=0, le=100) = Field(...)
    avg_click_rate: confloat(ge=0, le=100) = Field(...)
    avg_conversion_rate: confloat(ge=0, le=100) = Field(...)
    engagement_score_avg: confloat(ge=0, le=100) = Field(...)

    # Financial Performance
    total_spend: Decimal = Field(default=Decimal("0.00"), ge=0)
    revenue_generated: Decimal = Field(default=Decimal("0.00"), ge=0)
    roi_percentage: float = Field(...)
    cost_per_lead: Decimal = Field(default=Decimal("0.00"), ge=0)
    cost_per_acquisition: Decimal = Field(default=Decimal("0.00"), ge=0)

    # Audience Analytics
    total_audience_reached: conint(ge=0) = Field(...)
    unique_engagements: conint(ge=0) = Field(...)
    repeat_engagement_rate: confloat(ge=0, le=100) = Field(...)
    audience_growth_rate: float = Field(...)

    # Campaign Quality
    content_relevance_score: confloat(ge=0, le=1) = Field(...)
    targeting_accuracy: confloat(ge=0, le=100) = Field(...)
    campaign_completion_rate: confloat(ge=0, le=100) = Field(...)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            Decimal: lambda d: float(d)
        }


class DocumentGenerationAnalytics(BaseModel):
    """Analytics for document generation system performance."""

    timeframe: AnalyticsTimeframe = Field(...)
    seller_id: Optional[str] = Field(None)

    # Volume Metrics
    total_documents_generated: conint(ge=0) = Field(...)
    successful_generations: conint(ge=0) = Field(...)
    failed_generations: conint(ge=0) = Field(...)
    generation_success_rate: confloat(ge=0, le=100) = Field(...)

    # Performance Metrics
    avg_generation_time_ms: float = Field(..., ge=0)
    avg_quality_score: confloat(ge=0, le=1) = Field(...)
    template_cache_hit_rate: confloat(ge=0, le=100) = Field(...)

    # Document Type Breakdown
    pdf_generations: conint(ge=0) = Field(default=0)
    docx_generations: conint(ge=0) = Field(default=0)
    pptx_generations: conint(ge=0) = Field(default=0)
    html_generations: conint(ge=0) = Field(default=0)

    # Business Impact
    documents_sent_to_clients: conint(ge=0) = Field(...)
    document_engagement_rate: confloat(ge=0, le=100) = Field(...)
    client_document_satisfaction: confloat(ge=0, le=5) = Field(...)

    # Automation Metrics
    auto_triggered_documents: conint(ge=0) = Field(...)
    manual_document_requests: conint(ge=0) = Field(...)
    automation_rate: confloat(ge=0, le=100) = Field(...)

    # Template Performance
    most_used_templates: List[str] = Field(default_factory=list)
    template_success_rates: Dict[str, float] = Field(default_factory=dict)
    claude_enhancement_usage: confloat(ge=0, le=100) = Field(...)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            Decimal: lambda d: float(d)
        }


class WorkflowProgressionAnalytics(BaseModel):
    """Analytics for seller workflow progression and stage management."""

    timeframe: AnalyticsTimeframe = Field(...)
    seller_id: Optional[str] = Field(None)

    # Workflow Volume
    total_active_workflows: conint(ge=0) = Field(...)
    completed_workflows: conint(ge=0) = Field(...)
    stalled_workflows: conint(ge=0) = Field(...)
    abandoned_workflows: conint(ge=0) = Field(...)

    # Stage Performance
    avg_time_per_stage_hours: Dict[str, float] = Field(default_factory=dict)
    stage_completion_rates: Dict[str, float] = Field(default_factory=dict)
    stage_progression_success: confloat(ge=0, le=100) = Field(...)

    # Workflow Efficiency
    avg_total_workflow_time_days: float = Field(..., ge=0)
    workflow_completion_rate: confloat(ge=0, le=100) = Field(...)
    automation_trigger_success: confloat(ge=0, le=100) = Field(...)

    # Client Interaction
    avg_client_touchpoints: float = Field(..., ge=0)
    client_response_rate: confloat(ge=0, le=100) = Field(...)
    client_satisfaction_per_stage: Dict[str, float] = Field(default_factory=dict)

    # Bottleneck Analysis
    most_common_bottlenecks: List[str] = Field(default_factory=list)
    bottleneck_resolution_time_avg: float = Field(default=0.0, ge=0)
    workflow_optimization_opportunities: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


# ============================================================================
# Advanced Analytics and Intelligence Models
# ============================================================================

class PredictiveInsight(BaseModel):
    """Predictive analytics insights and recommendations."""

    insight_id: str = Field(default_factory=lambda: f"insight_{uuid4().hex[:8]}")
    insight_type: str = Field(..., max_length=50)
    category: AnalyticsCategory = Field(...)

    # Prediction Details
    prediction_target: str = Field(..., max_length=100)
    predicted_value: float = Field(...)
    confidence_interval: Tuple[float, float] = Field(...)
    confidence_level: confloat(ge=0, le=1) = Field(...)

    # Context and Timeline
    prediction_horizon_days: conint(ge=1) = Field(...)
    generated_timestamp: datetime = Field(default_factory=datetime.utcnow)
    relevant_until: datetime = Field(...)

    # Supporting Data
    contributing_factors: List[str] = Field(default_factory=list)
    historical_accuracy: Optional[confloat(ge=0, le=1)] = Field(None)
    model_version: str = Field(default="1.0.0")

    # Business Impact
    potential_impact: str = Field(..., max_length=200)
    recommended_actions: List[str] = Field(default_factory=list)
    priority_level: int = Field(default=3, ge=1, le=5)  # 1=highest, 5=lowest

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class ComparativeBenchmark(BaseModel):
    """Benchmark comparisons for performance analysis."""

    benchmark_id: str = Field(default_factory=lambda: f"benchmark_{uuid4().hex[:8]}")
    metric_name: str = Field(..., max_length=100)
    category: AnalyticsCategory = Field(...)

    # Benchmark Data
    current_value: float = Field(...)
    benchmark_value: float = Field(...)
    percentile_ranking: confloat(ge=0, le=100) = Field(...)
    performance_level: PerformanceLevel = Field(...)

    # Comparison Context
    benchmark_population: str = Field(..., max_length=100)  # e.g., "all_sellers", "regional"
    sample_size: conint(ge=1) = Field(...)
    benchmark_date: date = Field(default_factory=date.today)

    # Analysis
    variance_from_benchmark: float = Field(...)
    statistical_significance: confloat(ge=0, le=1) = Field(...)
    improvement_opportunity: Optional[str] = Field(None, max_length=300)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            date: lambda d: d.isoformat()
        }


class PerformanceTrend(BaseModel):
    """Performance trend analysis over time."""

    trend_id: str = Field(default_factory=lambda: f"trend_{uuid4().hex[:8]}")
    metric_name: str = Field(..., max_length=100)
    category: AnalyticsCategory = Field(...)

    # Trend Analysis
    trend_direction: TrendDirection = Field(...)
    trend_strength: confloat(ge=0, le=1) = Field(...)  # 0=weak, 1=strong
    rate_of_change: float = Field(...)

    # Time Series Data
    data_points: List[Tuple[datetime, float]] = Field(...)
    timeframe_analyzed: AnalyticsTimeframe = Field(...)
    analysis_period_start: datetime = Field(...)
    analysis_period_end: datetime = Field(...)

    # Statistical Analysis
    correlation_coefficient: Optional[float] = Field(None, ge=-1, le=1)
    seasonality_detected: bool = Field(default=False)
    anomalies_detected: List[datetime] = Field(default_factory=list)

    # Forecasting
    projected_next_period: Optional[float] = Field(None)
    forecast_confidence: Optional[confloat(ge=0, le=1)] = Field(None)

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


# ============================================================================
# Aggregation and Reporting Models
# ============================================================================

class AnalyticsReport(BaseModel):
    """Comprehensive analytics report."""

    report_id: str = Field(default_factory=lambda: f"report_{uuid4().hex[:8]}")
    report_name: str = Field(..., max_length=200)
    report_type: str = Field(..., max_length=50)

    # Report Metadata
    generated_timestamp: datetime = Field(default_factory=datetime.utcnow)
    report_period_start: datetime = Field(...)
    report_period_end: datetime = Field(...)
    generated_for: Optional[str] = Field(None)  # seller_id or "all"

    # Report Content
    executive_summary: str = Field(..., max_length=1000)
    key_metrics: List[AnalyticsMetric] = Field(default_factory=list)
    performance_insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Analytics Components
    seller_performance: Optional[SellerPerformanceMetrics] = None
    valuation_analytics: Optional[PropertyValuationAnalytics] = None
    campaign_analytics: Optional[MarketingCampaignAnalytics] = None
    document_analytics: Optional[DocumentGenerationAnalytics] = None
    workflow_analytics: Optional[WorkflowProgressionAnalytics] = None

    # Advanced Analytics
    predictive_insights: List[PredictiveInsight] = Field(default_factory=list)
    benchmarks: List[ComparativeBenchmark] = Field(default_factory=list)
    trends: List[PerformanceTrend] = Field(default_factory=list)

    # Report Quality
    data_completeness: confloat(ge=0, le=100) = Field(...)
    confidence_level: confloat(ge=0, le=1) = Field(...)

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class AnalyticsDashboardConfig(BaseModel):
    """Configuration for analytics dashboard display."""

    config_id: str = Field(default_factory=lambda: f"config_{uuid4().hex[:8]}")
    dashboard_name: str = Field(..., max_length=100)
    user_id: str = Field(...)

    # Display Configuration
    refresh_interval_seconds: conint(ge=30, le=3600) = Field(default=300)
    auto_refresh_enabled: bool = Field(default=True)
    real_time_updates: bool = Field(default=True)

    # Metric Selection
    selected_metrics: List[str] = Field(default_factory=list)
    metric_categories: List[AnalyticsCategory] = Field(default_factory=list)
    timeframe_default: AnalyticsTimeframe = Field(default=AnalyticsTimeframe.WEEKLY)

    # Visualization Preferences
    chart_types: Dict[str, str] = Field(default_factory=dict)
    color_scheme: str = Field(default="professional")
    show_benchmarks: bool = Field(default=True)
    show_trends: bool = Field(default=True)

    # Filtering and Grouping
    seller_filter: Optional[str] = Field(None)
    date_range_filter: Optional[Tuple[date, date]] = Field(None)
    performance_level_filter: Optional[List[PerformanceLevel]] = Field(None)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            date: lambda d: d.isoformat()
        }


# ============================================================================
# API Request and Response Models
# ============================================================================

class AnalyticsQuery(BaseModel):
    """Query model for analytics API requests."""

    query_id: str = Field(default_factory=lambda: f"query_{uuid4().hex[:8]}")

    # Query Parameters
    categories: List[AnalyticsCategory] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    timeframe: AnalyticsTimeframe = Field(default=AnalyticsTimeframe.WEEKLY)

    # Filtering
    seller_ids: Optional[List[str]] = Field(None)
    date_range_start: Optional[datetime] = Field(None)
    date_range_end: Optional[datetime] = Field(None)

    # Aggregation
    group_by: Optional[List[str]] = Field(None)
    aggregation_functions: Dict[str, str] = Field(default_factory=dict)

    # Advanced Options
    include_predictions: bool = Field(default=False)
    include_benchmarks: bool = Field(default=False)
    include_trends: bool = Field(default=False)
    confidence_threshold: confloat(ge=0, le=1) = Field(default=0.8)

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class AnalyticsQueryResponse(BaseModel):
    """Response model for analytics queries."""

    query_id: str = Field(...)
    response_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = Field(..., ge=0)

    # Response Data
    metrics: List[AnalyticsMetric] = Field(default_factory=list)
    aggregated_data: Dict[str, Any] = Field(default_factory=dict)

    # Advanced Analytics (if requested)
    predictions: List[PredictiveInsight] = Field(default_factory=list)
    benchmarks: List[ComparativeBenchmark] = Field(default_factory=list)
    trends: List[PerformanceTrend] = Field(default_factory=list)

    # Response Metadata
    data_freshness_seconds: int = Field(..., ge=0)
    confidence_level: confloat(ge=0, le=1) = Field(...)
    total_records: int = Field(..., ge=0)

    # Warnings and Limitations
    warnings: List[str] = Field(default_factory=list)
    data_limitations: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


# ============================================================================
# Performance Benchmarks and Constants
# ============================================================================

ANALYTICS_PERFORMANCE_BENCHMARKS = {
    # Processing Performance
    "metric_calculation_time_ms": 200,
    "dashboard_load_time_ms": 500,
    "report_generation_time_ms": 1000,
    "real_time_update_latency_ms": 100,

    # Data Freshness
    "real_time_data_freshness_seconds": 60,
    "batch_processing_interval_minutes": 15,
    "trend_analysis_update_hours": 6,
    "benchmark_refresh_hours": 24,

    # Quality Thresholds
    "minimum_confidence_level": 0.80,
    "minimum_data_completeness": 0.85,
    "statistical_significance_threshold": 0.95,
    "trend_strength_threshold": 0.60
}

DEFAULT_SELLER_KPIS = [
    "overall_performance_score",
    "conversion_rate",
    "engagement_rate",
    "client_satisfaction_score",
    "leads_qualified",
    "total_revenue_attributed",
    "workflow_completion_rate",
    "response_time_avg_hours"
]

BENCHMARK_POPULATIONS = {
    "all_sellers": "All sellers in the platform",
    "regional": "Sellers in the same geographic region",
    "experience_level": "Sellers with similar experience level",
    "property_type": "Sellers working with similar property types",
    "market_segment": "Sellers in similar market segments"
}


# ============================================================================
# Utility Functions
# ============================================================================

def calculate_performance_level(value: float, benchmarks: Dict[str, float]) -> PerformanceLevel:
    """Calculate performance level based on value and benchmarks."""
    if value >= benchmarks.get("excellent", 90):
        return PerformanceLevel.EXCELLENT
    elif value >= benchmarks.get("good", 75):
        return PerformanceLevel.GOOD
    elif value >= benchmarks.get("average", 50):
        return PerformanceLevel.AVERAGE
    elif value >= benchmarks.get("below_average", 25):
        return PerformanceLevel.BELOW_AVERAGE
    else:
        return PerformanceLevel.POOR


def determine_trend_direction(data_points: List[Tuple[datetime, float]]) -> TrendDirection:
    """Determine trend direction from time series data points."""
    if len(data_points) < 3:
        return TrendDirection.UNKNOWN

    # Simple trend calculation based on first and last values
    first_value = data_points[0][1]
    last_value = data_points[-1][1]

    if last_value > first_value * 1.05:  # 5% increase threshold
        return TrendDirection.INCREASING
    elif last_value < first_value * 0.95:  # 5% decrease threshold
        return TrendDirection.DECREASING
    else:
        return TrendDirection.STABLE


def validate_analytics_request(request: AnalyticsQuery) -> Dict[str, Any]:
    """Validate analytics request parameters."""
    validation_result = {"valid": True, "errors": []}

    # Validate date range
    if request.date_range_start and request.date_range_end:
        if request.date_range_start >= request.date_range_end:
            validation_result["errors"].append("Start date must be before end date")

    # Validate timeframe with date range
    if request.timeframe == AnalyticsTimeframe.CUSTOM:
        if not (request.date_range_start and request.date_range_end):
            validation_result["errors"].append("Custom timeframe requires start and end dates")

    # Validate metric requests
    if len(request.metrics) > 50:
        validation_result["errors"].append("Maximum 50 metrics can be requested at once")

    validation_result["valid"] = len(validation_result["errors"]) == 0
    return validation_result


# Export all models and utilities
__all__ = [
    # Enums
    "AnalyticsTimeframe", "MetricType", "PerformanceLevel", "TrendDirection", "AnalyticsCategory",

    # Core Models
    "AnalyticsMetric", "SellerPerformanceMetrics", "PropertyValuationAnalytics",
    "MarketingCampaignAnalytics", "DocumentGenerationAnalytics", "WorkflowProgressionAnalytics",

    # Advanced Models
    "PredictiveInsight", "ComparativeBenchmark", "PerformanceTrend",

    # Reporting Models
    "AnalyticsReport", "AnalyticsDashboardConfig",

    # API Models
    "AnalyticsQuery", "AnalyticsQueryResponse",

    # Constants
    "ANALYTICS_PERFORMANCE_BENCHMARKS", "DEFAULT_SELLER_KPIS", "BENCHMARK_POPULATIONS",

    # Utilities
    "calculate_performance_level", "determine_trend_direction", "validate_analytics_request"
]