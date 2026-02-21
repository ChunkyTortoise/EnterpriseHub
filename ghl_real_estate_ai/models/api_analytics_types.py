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
# Enterprise Billing & Contract
# =============================================================================


class ContractTermsData(TypedDict, total=False):
    """Enterprise contract terms."""

    start_date: str
    end_date: str
    auto_renewal: bool
    payment_terms: str
    billing_frequency: str
    currency: str
    special_conditions: list[str]


class BillingContactData(TypedDict, total=False):
    """Billing contact information."""

    primary_email: str
    secondary_email: str
    name: str
    phone: str
    department: str


class VolumeCommitmentData(TypedDict, total=False):
    """Volume commitment details."""

    minimum_monthly: int
    maximum_monthly: int
    shortfall_penalty: float
    current_usage: int
    compliance_rate: float


class VolumeSummary(TypedDict, total=False):
    """Volume billing summary."""

    total_volume: int
    billable_volume: int
    volume_tier: str
    discount_applied: float
    period: str


class BillingCalculation(TypedDict, total=False):
    """Billing calculation breakdown."""

    subtotal: float
    discounts: float
    taxes: float
    total_amount: float
    currency: str
    line_items: list[dict[str, Any]]


class InvoiceData(TypedDict, total=False):
    """Invoice details."""

    invoice_id: str
    amount: float
    status: str
    due_date: str
    issued_date: str
    line_items: list[dict[str, Any]]


class PaymentResult(TypedDict, total=False):
    """Payment processing result."""

    payment_id: str
    status: str
    amount: float
    method: str
    processed_at: str
    transaction_id: str


class AdjustmentItem(TypedDict, total=False):
    """Billing/revenue adjustment."""

    adjustment_type: str
    amount: float
    reason: str
    applied_at: str
    approved_by: str


class DestinationData(TypedDict, total=False):
    """Relocation destination details."""

    city: str
    state: str
    zip_code: str
    neighborhood: str
    housing_type: str


class StatusIndicators(TypedDict, total=False):
    """Status indicator data."""

    status: str
    last_updated: str
    progress_percentage: float
    milestones_completed: int
    blockers: list[str]


# =============================================================================
# Dashboard Portfolio
# =============================================================================


class PortfolioSummaryData(TypedDict, total=False):
    """Partnership portfolio summary."""

    total_partnerships: int
    active_partnerships: int
    total_revenue: float
    avg_health_score: float
    growth_rate: float
    top_tier_count: int


class PartnerPerformer(TypedDict, total=False):
    """Top-performing partner data."""

    partnership_id: str
    company_name: str
    revenue: float
    health_score: float
    volume: int
    growth_rate: float


class GrowthOpportunity(TypedDict, total=False):
    """Growth opportunity data."""

    opportunity_type: str
    description: str
    potential_revenue: float
    confidence: float
    timeline: str
    required_actions: list[str]


class JorgeCommissionData(TypedDict, total=False):
    """Jorge's commission calculation."""

    rate: float
    pipeline_value: float
    commission_amount: float
    monthly_target: float
    progress_percentage: float


class BotMetricData(TypedDict, total=False):
    """Bot performance metric."""

    bot_type: str
    display_name: str
    current_status: str
    avg_response_time_ms: float
    success_rate: float
    total_conversations: int
    satisfaction_score: float


class CoordinationMetricsData(TypedDict, total=False):
    """Bot coordination metrics."""

    handoff_success_rate: float
    avg_handoff_time_ms: float
    coordination_events: int
    context_preservation_rate: float
    multi_bot_conversations: int


class PerformanceAlertData(TypedDict, total=False):
    """Performance alert."""

    bot_type: str
    alert_type: str
    severity: str
    message: str
    timestamp: str


# =============================================================================
# Competitive Intelligence Response
# =============================================================================


class CompetitorDataPoint(TypedDict, total=False):
    """Competitor data point."""

    data_id: str
    data_source: str
    data_type: str
    collected_at: str
    confidence_score: float
    summary: str


class CollectionSummaryData(TypedDict, total=False):
    """Data collection summary."""

    total_data_points: int
    data_sources_used: int
    collection_time_range: str
    most_recent_collection: str


class ThreatDataItem(TypedDict, total=False):
    """Competitive threat item."""

    threat_id: str
    competitor_id: str
    threat_type: str
    threat_level: str
    description: str
    potential_impact: str
    confidence_level: float
    recommended_response: str
    response_urgency: str
    evidence_count: int


class RiskSummaryData(TypedDict, total=False):
    """Risk assessment summary."""

    total_threats: int
    high_priority_threats: int
    overall_risk_level: str
    immediate_action_required: int
    threat_categories: list[str]


class ResponseStrategy(TypedDict, total=False):
    """Competitive response strategy."""

    strategy: str
    description: str
    timeline: str
    cost_impact: str
    effectiveness: str


class CompetitiveLandscape(TypedDict, total=False):
    """Competitive landscape analysis."""

    total_competitors: int
    market_concentration: str
    pricing_pressure: str
    differentiation_opportunities: list[str]
    threat_level: str
    competitive_advantages: list[str]


class CollectionMetricsData(TypedDict, total=False):
    """Collection performance metrics."""

    data_points_collected_24h: int
    collection_success_rate: float
    active_collectors: int
    monitored_competitors: int
    average_collection_time_ms: float
    collection_errors_24h: int
    data_sources_active: int


class ProcessingMetricsData(TypedDict, total=False):
    """Processing performance metrics."""

    average_processing_time: float
    processing_queue_length: int
    processed_items_24h: int
    processing_errors_24h: int
    ai_enrichment_rate: float
    batch_processing_efficiency: float


class UptimeStatsData(TypedDict, total=False):
    """Uptime statistics."""

    system_uptime_hours: float
    monitoring_uptime_percent: float
    api_availability_percent: float
    last_restart: str
    scheduled_maintenance: str


# =============================================================================
# Module & Integration
# =============================================================================


class ModuleMetricsData(TypedDict, total=False):
    """Module-specific metrics."""

    status: str
    total_processed: int
    success_rate: float
    avg_processing_time_ms: float
    error_count: int


class ActionItemData(TypedDict, total=False):
    """Action item data."""

    action_id: str
    title: str
    priority: str
    status: str
    due_date: str
    assigned_to: str


class ErrorRecord(TypedDict, total=False):
    """Error record."""

    error_id: str
    error_type: str
    message: str
    timestamp: str
    severity: str
    resolved: bool


class CompetitiveAdvantageItem(TypedDict, total=False):
    """Competitive advantage item."""

    advantage_type: str
    description: str
    impact_score: float
    sustainability: str


# =============================================================================
# BI Report & Insight
# =============================================================================


class BIReportSection(TypedDict, total=False):
    """BI report section."""

    section_id: str
    title: str
    content: str
    data: dict[str, Any]
    visualizations: list[dict[str, Any]]


class InsightData(TypedDict, total=False):
    """Business intelligence insight."""

    insight_type: str
    title: str
    description: str
    confidence: float
    impact_score: float
    recommended_actions: list[str]
    data_points: list[dict[str, Any]]


class RecommendationData(TypedDict, total=False):
    """Business recommendation."""

    title: str
    description: str
    priority: str
    impact: str
    timeline: str
    resources_required: list[str]


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
    # Enterprise Billing & Contract
    "ContractTermsData",
    "BillingContactData",
    "VolumeCommitmentData",
    "VolumeSummary",
    "BillingCalculation",
    "InvoiceData",
    "PaymentResult",
    "AdjustmentItem",
    "DestinationData",
    "StatusIndicators",
    # Dashboard Portfolio
    "PortfolioSummaryData",
    "PartnerPerformer",
    "GrowthOpportunity",
    "JorgeCommissionData",
    "BotMetricData",
    "CoordinationMetricsData",
    "PerformanceAlertData",
    # Competitive Intelligence Response
    "CompetitorDataPoint",
    "CollectionSummaryData",
    "ThreatDataItem",
    "RiskSummaryData",
    "ResponseStrategy",
    "CompetitiveLandscape",
    "CollectionMetricsData",
    "ProcessingMetricsData",
    "UptimeStatsData",
    # Module & Integration
    "ModuleMetricsData",
    "ActionItemData",
    "ErrorRecord",
    "CompetitiveAdvantageItem",
    # BI Report & Insight
    "BIReportSection",
    "InsightData",
    "RecommendationData",
]
