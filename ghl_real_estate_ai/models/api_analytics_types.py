"""
TypedDict definitions for API analytics, dashboard data, and enterprise configurations.

Provides strongly-typed dictionary structures for:
- Analytics metrics and performance data
- Dashboard widgets and visualization data
- Enterprise configuration and settings
- Intelligence insights and predictions
- Competitive intelligence data
- Revenue and financial metrics

Usage:
    from ghl_real_estate_ai.models.api_analytics_types import AnalyticsMetrics, DashboardWidget
    
    metrics: AnalyticsMetrics = {
        "total_leads": 150,
        "qualified_leads": 45,
        "conversion_rate": 0.30,
        "avg_response_time_ms": 85.5,
        "revenue_pipeline": 1250000.0,
        "period": "7d"
    }

Author: Claude Code Agent - Feature Enhancement
Date: 2026-02-09
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from typing_extensions import NotRequired

# =============================================================================
# Analytics & Performance Metrics
# =============================================================================


class AnalyticsMetrics(TypedDict, total=False):
    """Core analytics metrics for business intelligence."""
    
    total_leads: int
    qualified_leads: int
    conversion_rate: float
    avg_response_time_ms: float
    revenue_pipeline: float
    period: str
    hot_leads: int
    warm_leads: int
    cold_leads: int
    appointments_scheduled: int
    deals_closed: int
    avg_deal_size: float


class PerformanceMetrics(TypedDict, total=False):
    """System and component performance metrics."""
    
    processing_time_ms: int
    cache_hit_rate: float
    error_rate: float
    uptime_percentage: float
    throughput_per_second: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float


class KPIMetrics(TypedDict, total=False):
    """Key Performance Indicator metrics."""
    
    metric_name: str
    current_value: float
    target_value: float
    previous_value: float
    change_percentage: float
    trend: str  # "up", "down", "stable"
    status: str  # "on_track", "at_risk", "critical"


# =============================================================================
# Dashboard & Visualization
# =============================================================================


class DashboardWidget(TypedDict, total=False):
    """Dashboard widget configuration and data."""
    
    widget_id: str
    widget_type: str  # "chart", "table", "metric", "map", "timeline"
    title: str
    data: dict[str, Any]
    position: dict[str, int]  # x, y, width, height
    refresh_interval_seconds: int
    filters: dict[str, Any]


class ChartData(TypedDict, total=False):
    """Chart visualization data structure."""
    
    chart_type: str  # "line", "bar", "pie", "scatter", "area"
    labels: list[str]
    datasets: list[dict[str, Any]]
    options: dict[str, Any]
    title: str
    x_axis_label: str
    y_axis_label: str


class TimeSeriesData(TypedDict, total=False):
    """Time series data point."""
    
    timestamp: str  # ISO format
    value: float
    label: str
    metadata: dict[str, Any]


# =============================================================================
# Enterprise Configuration
# =============================================================================


class EnterpriseConfig(TypedDict, total=False):
    """Enterprise platform configuration."""
    
    location_id: str
    tenant_id: str
    features: list[str]
    tier: str  # "silver", "gold", "platinum"
    settings: dict[str, Any]
    rate_limits: dict[str, int]
    enabled_modules: list[str]


class TierConfig(TypedDict, total=False):
    """Partnership tier configuration."""
    
    tier_name: str
    max_users: int
    max_relocations_per_month: int
    support_level: str
    features: list[str]
    pricing_model: str


class PricingStructure(TypedDict, total=False):
    """Pricing structure for enterprise contracts."""
    
    base_rate: float
    volume_discounts: dict[str, float]
    revenue_share_percentage: float
    setup_fee: float
    minimum_monthly_commitment: float
    payment_terms: str


# =============================================================================
# Intelligence & Insights
# =============================================================================


class ConversationInsights(TypedDict, total=False):
    """Conversation intelligence analysis data."""
    
    engagement_score: float
    sentiment_score: float
    key_topics: list[str]
    buying_signals: list[str]
    concern_indicators: list[str]
    recommended_next_actions: list[str]
    qualification_score: int


class PreferenceData(TypedDict, total=False):
    """Client preference learning data."""
    
    preference_type: str
    confidence: float
    source: str
    last_updated: str  # ISO format
    supporting_evidence: list[str]
    conflicts: list[str]


class MatchingWeights(TypedDict, total=False):
    """Behavioral matching weight configuration."""
    
    feature_weight: float
    location_weight: float
    price_weight: float
    urgency_weight: float
    lifestyle_weight: float
    adjusted_priorities: dict[str, float]


# =============================================================================
# Competitive Intelligence
# =============================================================================


class CompetitiveIntelligenceData(TypedDict, total=False):
    """Competitive intelligence analysis data."""
    
    competitor_name: str
    market_share: float
    listings_count: int
    avg_price: float
    strengths: list[str]
    weaknesses: list[str]
    threat_level: str
    last_updated: str


class MarketTrendData(TypedDict, total=False):
    """Market trend analysis data."""
    
    trend_name: str
    trend_direction: str  # "up", "down", "stable"
    confidence: float
    impact_score: float
    time_horizon: str
    supporting_factors: list[str]


# =============================================================================
# Revenue & Financial
# =============================================================================


class RevenueMetrics(TypedDict, total=False):
    """Revenue and financial metrics."""
    
    total_revenue: float
    jorge_commission: float
    commission_rate: float
    avg_transaction_value: float
    revenue_growth_rate: float
    projected_revenue: float


class RevenueAttribution(TypedDict, total=False):
    """Revenue attribution analysis."""
    
    direct_revenue: float
    indirect_revenue: float
    attributed_to: dict[str, float]
    confidence_score: float
    attribution_model: str


class CostMetrics(TypedDict, total=False):
    """Cost and expense metrics."""
    
    total_cost: float
    cost_per_lead: float
    cost_per_acquisition: float
    operational_costs: float
    marketing_costs: float
    roi: float


# =============================================================================
# Forecasting & Predictions
# =============================================================================


class ForecastData(TypedDict, total=False):
    """Forecasting and prediction data."""
    
    forecast_period: str
    predicted_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    confidence_level: float
    methodology: str
    factors_considered: list[str]


class PredictiveInsight(TypedDict, total=False):
    """Predictive analytics insight."""
    
    insight_type: str
    prediction: Any
    confidence: float
    impact_score: float
    time_horizon: str
    recommended_actions: list[dict[str, Any]]
    risk_factors: list[str]


# =============================================================================
# System Health & Monitoring
# =============================================================================


class SystemHealthData(TypedDict, total=False):
    """System health monitoring data."""
    
    overall_status: str  # "healthy", "degraded", "critical"
    component_statuses: dict[str, str]
    active_alerts: list[str]
    last_check: str
    uptime_percentage: float


class AlertConfig(TypedDict, total=False):
    """Alert configuration and rules."""
    
    alert_name: str
    condition: str
    threshold: float
    severity: str  # "info", "warning", "critical"
    notification_channels: list[str]
    cooldown_seconds: int


# =============================================================================
# Relocation & Partnership
# =============================================================================


class RelocationMetrics(TypedDict, total=False):
    """Employee relocation tracking metrics."""
    
    total_relocations: int
    in_progress: int
    completed: int
    avg_completion_days: float
    satisfaction_score: float
    cost_efficiency_score: float


class PartnershipMetrics(TypedDict, total=False):
    """Partnership performance metrics."""
    
    partnership_id: str
    volume_ytd: int
    revenue_ytd: float
    health_score: float
    sla_compliance_rate: float
    satisfaction_rating: float


# =============================================================================
# Timeline & Journey
# =============================================================================


class TimelineMetric(TypedDict, total=False):
    """Timeline milestone metric."""
    
    milestone_name: str
    target_date: str
    actual_date: NotRequired[str]
    status: str  # "pending", "in_progress", "completed", "delayed"
    delay_days: NotRequired[int]


class JourneyStageData(TypedDict, total=False):
    """Customer journey stage data."""
    
    stage_name: str
    entry_date: str
    duration_days: int
    completion_percentage: float
    next_actions: list[str]
    blockers: list[str]


# =============================================================================
# Quality & Compliance
# =============================================================================


class QualityMetrics(TypedDict, total=False):
    """Data and service quality metrics."""
    
    data_completeness: float
    data_accuracy: float
    data_freshness_hours: float
    validation_errors: int
    confidence_score: float


class ComplianceMetrics(TypedDict, total=False):
    """Compliance and regulatory metrics."""
    
    compliance_status: str
    violations: int
    audit_trail_complete: bool
    last_audit_date: str
    remediation_required: list[str]


# =============================================================================
# Efficiency & Operational
# =============================================================================


class EfficiencyMetrics(TypedDict, total=False):
    """Operational efficiency metrics."""
    
    automation_rate: float
    manual_intervention_rate: float
    avg_processing_time_seconds: float
    throughput: int
    resource_utilization: float


class SatisfactionMetrics(TypedDict, total=False):
    """Satisfaction and experience metrics."""
    
    nps_score: float
    satisfaction_rating: float
    feedback_sentiment: str
    issues_reported: int
    issues_resolved: int
    resolution_time_hours: float


# =============================================================================
# Context & Metadata
# =============================================================================


class AnalysisContext(TypedDict, total=False):
    """Analysis context and metadata."""
    
    analysis_id: str
    analysis_type: str
    start_date: str
    end_date: str
    location_id: str
    tenant_id: str
    generated_by: str
    confidence: float


class DataQuality(TypedDict, total=False):
    """Data quality assessment."""
    
    completeness_percentage: float
    accuracy_score: float
    timeliness_score: float
    consistency_score: float
    issues: list[str]


# =============================================================================
# Benchmark & Comparison
# =============================================================================


class BenchmarkData(TypedDict, total=False):
    """Benchmark comparison data."""
    
    metric_name: str
    current_value: float
    benchmark_value: float
    percentile_rank: float
    peer_average: float
    top_performers_average: float


class ComparisonData(TypedDict, total=False):
    """Period-over-period comparison data."""
    
    current_period_value: float
    previous_period_value: float
    change_absolute: float
    change_percentage: float
    trend: str
    significance: str


# =============================================================================
# Export all types
# =============================================================================

__all__ = [
    # Analytics & Performance
    "AnalyticsMetrics",
    "PerformanceMetrics",
    "KPIMetrics",
    # Dashboard & Visualization
    "DashboardWidget",
    "ChartData",
    "TimeSeriesData",
    # Enterprise Configuration
    "EnterpriseConfig",
    "TierConfig",
    "PricingStructure",
    # Intelligence & Insights
    "ConversationInsights",
    "PreferenceData",
    "MatchingWeights",
    # Competitive Intelligence
    "CompetitiveIntelligenceData",
    "MarketTrendData",
    # Revenue & Financial
    "RevenueMetrics",
    "RevenueAttribution",
    "CostMetrics",
    # Forecasting & Predictions
    "ForecastData",
    "PredictiveInsight",
    # System Health & Monitoring
    "SystemHealthData",
    "AlertConfig",
    # Relocation & Partnership
    "RelocationMetrics",
    "PartnershipMetrics",
    # Timeline & Journey
    "TimelineMetric",
    "JourneyStageData",
    # Quality & Compliance
    "QualityMetrics",
    "ComplianceMetrics",
    # Efficiency & Operational
    "EfficiencyMetrics",
    "SatisfactionMetrics",
    # Context & Metadata
    "AnalysisContext",
    "DataQuality",
    # Benchmark & Comparison
    "BenchmarkData",
    "ComparisonData",
]
