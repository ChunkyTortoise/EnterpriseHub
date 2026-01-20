"""
Jorge's Advanced Analytics Models
Data structures for business intelligence and forecasting
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field, validator

from ghl_real_estate_ai.services.enhanced_smart_lead_scorer import LeadPriority


class ForecastHorizon(Enum):
    """Forecast time horizons."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class MetricCategory(Enum):
    """Categories of performance metrics."""
    REVENUE = "revenue"
    CONVERSION = "conversion"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    MARKET = "market"
    GEOGRAPHIC = "geographic"


class FunnelStage(Enum):
    """Conversion funnel stages."""
    NEW_LEAD = "new_lead"
    QUALIFIED = "qualified"
    APPOINTMENT = "appointment"
    SHOWING = "showing"
    OFFER = "offer"
    UNDER_CONTRACT = "under_contract"
    CLOSED = "closed"


class MarketTemperature(Enum):
    """Market condition indicators."""
    HOT = "hot"
    WARM = "warm"
    COOL = "cool"
    COLD = "cold"


class CompetitivePressure(Enum):
    """Competitive pressure levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RevenueForecast(BaseModel):
    """Revenue forecasting model."""
    forecasted_revenue: float
    confidence_lower: float
    confidence_upper: float
    confidence_level: float = Field(..., ge=0.5, le=0.99)

    forecast_horizon_days: int
    predicted_conversions: int
    avg_deal_value: float

    # Model performance
    model_accuracy: float = Field(..., ge=0.0, le=1.0)
    historical_mape: float = Field(..., description="Mean Absolute Percentage Error")

    # Business context
    key_assumptions: List[str]
    risk_factors: List[str]
    market_conditions: MarketTemperature

    # Metadata
    model_version: str
    generated_at: datetime = Field(default_factory=datetime.now)
    forecast_date: date


class FunnelMetrics(BaseModel):
    """Metrics for a single funnel stage."""
    stage: FunnelStage
    lead_count: int
    conversion_rate: float = Field(..., ge=0.0, le=1.0)
    avg_time_in_stage_days: float
    drop_off_count: int
    drop_off_percentage: float


class DropOffAnalysis(BaseModel):
    """Analysis of funnel drop-off points."""
    from_stage: FunnelStage
    to_stage: FunnelStage
    drop_off_count: int
    drop_off_rate: float
    primary_reasons: List[str]
    improvement_opportunities: List[str]


class FunnelAnalysis(BaseModel):
    """Complete conversion funnel analysis."""
    time_period_days: int
    stages: List[FunnelMetrics]
    conversion_rates: Dict[str, float]  # stage_to_stage rates
    drop_off_points: List[DropOffAnalysis]

    # Performance insights
    bottleneck_stage: FunnelStage
    optimization_opportunities: List[str]
    overall_conversion_rate: float
    avg_lead_to_close_days: float

    # Improvement potential
    improvement_potential_percent: float
    recommended_actions: List[str]

    analysis_date: datetime = Field(default_factory=datetime.now)


class LeadQualityMetrics(BaseModel):
    """Lead scoring quality and accuracy metrics."""
    total_leads_scored: int
    avg_lead_score: float
    score_distribution: Dict[str, int]  # score_range -> count

    # Accuracy metrics
    prediction_accuracy: float
    calibration_score: float
    false_positive_rate: float
    false_negative_rate: float

    # Confidence analysis
    avg_confidence: float
    high_confidence_accuracy: float
    low_confidence_accuracy: float


class CalibrationBucket(BaseModel):
    """Calibration analysis bucket."""
    predicted_probability_range: str  # "0.8-1.0"
    predicted_avg: float
    actual_conversion_rate: float
    lead_count: int
    calibration_error: float


class LeadQualityTrend(BaseModel):
    """Trend analysis of lead quality metrics."""
    time_series_data: List[Dict[str, Any]]  # [{date, accuracy, score_distribution, etc}]
    trend_direction: str  # "improving", "stable", "declining"
    trend_rate: float  # percentage change per day

    # Current state
    current_accuracy: float
    target_accuracy: float
    accuracy_gap: float

    # Calibration analysis
    calibration_curve: List[CalibrationBucket]
    overall_calibration_error: float

    # Quality by source
    quality_by_source: Dict[str, LeadQualityMetrics]
    best_performing_source: str
    worst_performing_source: str

    analysis_period_days: int
    generated_at: datetime = Field(default_factory=datetime.now)


class MarketTimingMetrics(BaseModel):
    """Market timing and conditions."""
    market_area: str = "Rancho Cucamonga"

    # Supply metrics
    active_inventory: int
    new_listings_count: int
    inventory_months: float

    # Demand metrics
    buyer_demand_index: float  # 0-100 composite score
    showing_activity: int
    offer_activity: int

    # Pricing metrics
    median_list_price: float
    median_sale_price: float
    price_velocity_percent: float  # rate of change
    avg_days_on_market: int

    # Timing intelligence
    market_temperature: MarketTemperature
    best_action: str  # "buy_now", "wait", "sell_now"
    confidence_score: float

    analysis_date: date


class MarketTimingInsight(BaseModel):
    """Market timing intelligence and recommendations."""
    current_conditions: MarketTimingMetrics
    historical_trends: List[MarketTimingMetrics]

    # Recommendations
    buyer_recommendations: List[str]
    seller_recommendations: List[str]
    investor_recommendations: List[str]

    # Timing predictions
    predicted_peak_season: str
    predicted_inventory_change: str
    price_movement_forecast: str

    # Context
    seasonal_factors: List[str]
    economic_indicators: Dict[str, float]

    generated_at: datetime = Field(default_factory=datetime.now)


class GeographicMetrics(BaseModel):
    """Performance metrics by geographic area."""
    zip_code: str
    neighborhood: str
    city: str = "Rancho Cucamonga"

    # Lead metrics
    total_leads: int
    qualified_leads: int
    avg_lead_score: float

    # Conversion metrics
    total_conversions: int
    conversion_rate: float
    avg_deal_value: float
    total_revenue: float

    # Market metrics
    median_property_price: float
    price_appreciation_3m: float
    inventory_level: int

    # Performance indicators
    market_share_estimate: float
    competitive_pressure: CompetitivePressure
    growth_potential: float  # 0-100 score


class GeographicAnalysis(BaseModel):
    """Complete geographic performance analysis."""
    total_areas_analyzed: int
    geographic_metrics: List[GeographicMetrics]

    # Top performers
    best_performing_zip: str
    worst_performing_zip: str
    highest_revenue_zip: str
    most_competitive_zip: str

    # Opportunities
    expansion_opportunities: List[str]
    underperforming_areas: List[str]
    market_gaps: List[str]

    # Summary statistics
    avg_conversion_rate: float
    total_market_revenue: float
    geographic_concentration: float  # how spread out the business is

    analysis_date: datetime = Field(default_factory=datetime.now)


class SourceROI(BaseModel):
    """ROI analysis for a lead source."""
    source_name: str
    campaign_id: Optional[str] = None

    # Costs
    acquisition_cost: float
    operational_cost: float
    total_cost: float

    # Revenue
    total_revenue: float
    attributed_conversions: int
    avg_deal_value: float

    # ROI metrics
    roi_percentage: float
    ltv_cac_ratio: float
    payback_period_days: int

    # Quality metrics
    avg_lead_score: float
    conversion_rate: float
    cost_per_conversion: float

    # Time period
    measurement_period_days: int
    last_updated: datetime = Field(default_factory=datetime.now)


class CompetitiveIntel(BaseModel):
    """Competitive intelligence analysis."""
    market_area: str = "Rancho Cucamonga"

    # Market share
    estimated_market_share: float
    competitor_count: int
    market_concentration: float  # how concentrated the market is

    # Activity metrics
    competitor_listing_velocity: float
    competitive_pricing_pressure: float
    avg_competitor_days_on_market: int

    # Intelligence
    top_competitors: List[str]
    competitive_advantages: List[str]
    competitive_threats: List[str]
    differentiation_opportunities: List[str]

    # Recommendations
    competitive_strategy_recommendations: List[str]
    pricing_recommendations: str
    positioning_recommendations: str

    analysis_date: datetime = Field(default_factory=datetime.now)


class PerformanceGoal(BaseModel):
    """Performance goal tracking."""
    goal_name: str
    goal_category: MetricCategory
    metric_name: str
    target_value: float
    current_value: float

    # Timeline
    goal_period: str  # "monthly", "quarterly", "yearly"
    start_date: date
    target_date: date

    # Progress
    completion_percentage: float
    on_track: bool
    forecast_completion_date: Optional[date] = None

    # Context
    assigned_to: str
    priority: str  # "high", "medium", "low"

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PerformanceSummary(BaseModel):
    """Executive summary of all performance metrics."""
    summary_period_days: int

    # Key metrics
    total_revenue: float
    total_conversions: int
    avg_conversion_rate: float
    lead_scoring_accuracy: float

    # Trends
    revenue_trend: str  # "up", "down", "stable"
    conversion_trend: str
    quality_trend: str

    # Goals progress
    goals_on_track: int
    goals_behind: int
    goals_ahead: int

    # Alerts
    performance_alerts: List[str]
    improvement_opportunities: List[str]

    # Forecasts
    revenue_forecast_30d: float
    conversion_forecast_30d: int

    generated_at: datetime = Field(default_factory=datetime.now)


class ExecutiveSummary(BaseModel):
    """Top-level executive dashboard summary."""
    revenue_forecast: RevenueForecast
    funnel_analysis: FunnelAnalysis
    lead_quality_summary: LeadQualityMetrics
    market_timing: MarketTimingInsight
    geographic_summary: GeographicAnalysis
    source_roi_summary: List[SourceROI]
    competitive_intel: CompetitiveIntel
    performance_summary: PerformanceSummary

    # Executive insights
    key_insights: List[str]
    action_items: List[str]
    risk_factors: List[str]
    opportunities: List[str]

    # Dashboard metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    refresh_frequency_minutes: int = 5
    cache_expires_at: datetime = Field(default_factory=lambda: datetime.now().replace(minute=datetime.now().minute + 5))


# Time series data models
class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series."""
    timestamp: datetime
    value: float
    metadata: Optional[Dict[str, Any]] = None


class TimeSeriesAnalysis(BaseModel):
    """Time series analysis results."""
    data_points: List[TimeSeriesDataPoint]
    trend: str  # "increasing", "decreasing", "stable", "volatile"
    seasonality_detected: bool
    anomalies: List[datetime]
    forecast_next_period: float
    confidence_interval: Tuple[float, float]


# Analytics request/response models
class AnalyticsRequest(BaseModel):
    """Request for analytics data."""
    time_window_days: int = 30
    include_forecasts: bool = True
    include_geographic: bool = True
    include_competitive: bool = False
    segment_filters: Optional[Dict[str, Any]] = None


class AnalyticsResponse(BaseModel):
    """Response from analytics service."""
    executive_summary: ExecutiveSummary
    processing_time_ms: int
    cache_hit: bool = False
    generated_at: datetime = Field(default_factory=datetime.now)


# Export all models
__all__ = [
    'ForecastHorizon', 'MetricCategory', 'FunnelStage', 'MarketTemperature', 'CompetitivePressure',
    'RevenueForecast', 'FunnelMetrics', 'DropOffAnalysis', 'FunnelAnalysis',
    'LeadQualityMetrics', 'CalibrationBucket', 'LeadQualityTrend',
    'MarketTimingMetrics', 'MarketTimingInsight', 'GeographicMetrics', 'GeographicAnalysis',
    'SourceROI', 'CompetitiveIntel', 'PerformanceGoal', 'PerformanceSummary',
    'ExecutiveSummary', 'TimeSeriesDataPoint', 'TimeSeriesAnalysis',
    'AnalyticsRequest', 'AnalyticsResponse'
]