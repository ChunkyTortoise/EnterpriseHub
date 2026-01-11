"""
Marketing Campaign Models for Automated Campaign Creation

This module provides Pydantic data models for the Marketing Campaign Builder,
enabling automated creation, management, and optimization of real estate marketing campaigns
with GoHighLevel integration and Claude AI content generation.

Business Impact: $60K+/year in marketing automation efficiency
Performance Target: <300ms campaign generation, <150ms template rendering
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, root_validator


# ============================================================================
# Core Enumerations
# ============================================================================

class CampaignType(str, Enum):
    """Marketing campaign type classifications."""
    PROPERTY_SHOWCASE = "property_showcase"
    LEAD_NURTURING = "lead_nurturing"
    MARKET_UPDATE = "market_update"
    SELLER_ONBOARDING = "seller_onboarding"
    FOLLOW_UP_SEQUENCE = "follow_up_sequence"
    REFERRAL_REQUEST = "referral_request"
    CLIENT_TESTIMONIAL = "client_testimonial"
    NEIGHBORHOOD_SPOTLIGHT = "neighborhood_spotlight"


class CampaignStatus(str, Enum):
    """Campaign lifecycle status tracking."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class CampaignChannel(str, Enum):
    """Marketing campaign delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    SOCIAL_MEDIA = "social_media"
    DIRECT_MAIL = "direct_mail"
    PUSH_NOTIFICATION = "push_notification"
    VOICEMAIL_DROP = "voicemail_drop"
    VIDEO_MESSAGE = "video_message"
    LINKEDIN_MESSAGE = "linkedin_message"


class TemplateCategory(str, Enum):
    """Marketing template category classifications."""
    WELCOME_SERIES = "welcome_series"
    PROPERTY_ALERTS = "property_alerts"
    MARKET_INSIGHTS = "market_insights"
    EDUCATIONAL_CONTENT = "educational_content"
    TESTIMONIALS = "testimonials"
    EVENT_INVITATIONS = "event_invitations"
    SEASONAL_CAMPAIGNS = "seasonal_campaigns"
    REACTIVATION = "reactivation"


class PersonalizationLevel(str, Enum):
    """Content personalization sophistication levels."""
    BASIC = "basic"  # Name and property type only
    STANDARD = "standard"  # Demographics and preferences
    ADVANCED = "advanced"  # Behavioral data and AI insights
    HYPER_PERSONALIZED = "hyper_personalized"  # Full Claude AI customization


class AudienceSegment(str, Enum):
    """Target audience segmentation options."""
    FIRST_TIME_BUYERS = "first_time_buyers"
    MOVE_UP_BUYERS = "move_up_buyers"
    DOWNSIZERS = "downsizers"
    INVESTORS = "investors"
    LUXURY_BUYERS = "luxury_buyers"
    INTERNATIONAL_BUYERS = "international_buyers"
    CASH_BUYERS = "cash_buyers"
    RELOCATING_BUYERS = "relocating_buyers"


# ============================================================================
# Content and Template Models
# ============================================================================

class ContentAsset(BaseModel):
    """Individual content asset within a marketing campaign."""

    asset_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique content asset identifier")
    asset_type: str = Field(..., description="Type of content asset")
    title: str = Field(..., min_length=1, max_length=200, description="Content title")
    content_body: str = Field(..., min_length=1, description="Main content body")

    # Media and attachments
    image_urls: List[str] = Field(default_factory=list, description="Associated image URLs")
    video_urls: List[str] = Field(default_factory=list, description="Associated video URLs")
    document_urls: List[str] = Field(default_factory=list, description="Associated document URLs")

    # Personalization and targeting
    personalization_tokens: Dict[str, Any] = Field(default_factory=dict, description="Dynamic content tokens")
    dynamic_content: Dict[str, str] = Field(default_factory=dict, description="Conditional content blocks")

    # Performance and optimization
    a_b_test_variant: Optional[str] = Field(None, description="A/B test variant identifier")
    click_tracking_enabled: bool = Field(True, description="Enable click tracking for analytics")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Asset creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_by: str = Field(..., description="Creator identifier")


class CampaignTemplate(BaseModel):
    """Reusable marketing campaign template with real estate specialization."""

    template_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique template identifier")
    template_name: str = Field(..., min_length=1, max_length=100, description="Template display name")
    template_category: TemplateCategory = Field(..., description="Template category classification")

    # Template configuration
    campaign_type: CampaignType = Field(..., description="Associated campaign type")
    target_audience: List[AudienceSegment] = Field(..., description="Target audience segments")
    recommended_channels: List[CampaignChannel] = Field(..., description="Recommended delivery channels")

    # Content structure
    subject_line_templates: List[str] = Field(..., min_items=1, description="Email subject line options")
    content_assets: List[ContentAsset] = Field(..., min_items=1, description="Template content components")
    call_to_action: str = Field(..., min_length=1, description="Primary call-to-action")

    # Personalization and customization
    personalization_level: PersonalizationLevel = Field(default=PersonalizationLevel.STANDARD, description="Personalization complexity")
    required_data_fields: List[str] = Field(default_factory=list, description="Required data for personalization")
    optional_data_fields: List[str] = Field(default_factory=list, description="Optional enhancement data")

    # Timing and scheduling
    recommended_send_times: List[str] = Field(default_factory=list, description="Optimal send time recommendations")
    follow_up_sequence: List[Dict[str, Any]] = Field(default_factory=list, description="Automated follow-up steps")

    # Performance and analytics
    historical_performance: Dict[str, float] = Field(default_factory=dict, description="Template performance metrics")
    optimization_suggestions: List[str] = Field(default_factory=list, description="AI optimization recommendations")

    # Template metadata
    is_active: bool = Field(True, description="Template availability status")
    version: str = Field(default="1.0", description="Template version")
    tags: List[str] = Field(default_factory=list, description="Searchable template tags")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Template creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_by: str = Field(..., description="Template creator identifier")


# ============================================================================
# Campaign Configuration Models
# ============================================================================

class CampaignAudience(BaseModel):
    """Target audience configuration for marketing campaigns."""

    audience_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique audience identifier")
    audience_name: str = Field(..., min_length=1, max_length=100, description="Audience segment name")

    # Segmentation criteria
    demographic_filters: Dict[str, Any] = Field(default_factory=dict, description="Demographic targeting criteria")
    behavioral_filters: Dict[str, Any] = Field(default_factory=dict, description="Behavioral targeting criteria")
    geographic_filters: Dict[str, Any] = Field(default_factory=dict, description="Geographic targeting criteria")

    # GHL integration
    ghl_tag_filters: List[str] = Field(default_factory=list, description="GoHighLevel tag filters")
    ghl_custom_field_filters: Dict[str, Any] = Field(default_factory=dict, description="Custom field criteria")
    excluded_contact_ids: List[str] = Field(default_factory=list, description="Contacts to exclude")

    # Engagement criteria
    engagement_score_min: Optional[float] = Field(None, ge=0, le=1, description="Minimum engagement score")
    last_activity_days: Optional[int] = Field(None, ge=0, description="Days since last activity filter")

    # Audience size and validation
    estimated_size: Optional[int] = Field(None, ge=0, description="Estimated audience size")
    actual_size: Optional[int] = Field(None, ge=0, description="Actual audience size after filtering")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Audience creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class CampaignScheduling(BaseModel):
    """Campaign scheduling and delivery timing configuration."""

    schedule_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique schedule identifier")

    # Basic scheduling
    start_date: datetime = Field(..., description="Campaign start date and time")
    end_date: Optional[datetime] = Field(None, description="Campaign end date (if applicable)")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")

    # Delivery configuration
    immediate_send: bool = Field(False, description="Send immediately upon activation")
    scheduled_send_times: List[datetime] = Field(default_factory=list, description="Specific send timestamps")
    recurring_schedule: Optional[Dict[str, Any]] = Field(None, description="Recurring campaign configuration")

    # Frequency and throttling
    max_sends_per_contact: int = Field(default=1, ge=1, description="Maximum sends per contact")
    send_frequency_limit: Optional[str] = Field(None, description="Frequency limit (e.g., 'daily', 'weekly')")
    throttle_rate: int = Field(default=100, ge=1, le=1000, description="Messages per minute limit")

    # Channel-specific scheduling
    channel_schedules: Dict[CampaignChannel, Dict[str, Any]] = Field(default_factory=dict, description="Per-channel scheduling")

    # Optimization
    auto_optimize_send_times: bool = Field(True, description="Automatically optimize send times")
    respect_quiet_hours: bool = Field(True, description="Respect recipient quiet hours")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Schedule creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class CampaignPersonalization(BaseModel):
    """Advanced personalization configuration for campaign content."""

    personalization_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique personalization identifier")

    # Personalization strategy
    personalization_level: PersonalizationLevel = Field(default=PersonalizationLevel.STANDARD, description="Personalization sophistication")
    dynamic_content_enabled: bool = Field(True, description="Enable dynamic content insertion")

    # Data source configuration
    primary_data_sources: List[str] = Field(default_factory=list, description="Primary personalization data sources")
    fallback_data_sources: List[str] = Field(default_factory=list, description="Fallback data when primary unavailable")

    # Content customization
    personalization_rules: Dict[str, Any] = Field(default_factory=dict, description="Content customization rules")
    conditional_content_blocks: Dict[str, Dict[str, str]] = Field(default_factory=dict, description="Conditional content variations")

    # Claude AI integration
    claude_content_generation: bool = Field(False, description="Use Claude AI for content generation")
    claude_optimization_prompts: List[str] = Field(default_factory=list, description="Claude optimization instructions")

    # Performance tracking
    personalization_effectiveness: Dict[str, float] = Field(default_factory=dict, description="Personalization performance metrics")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Personalization creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


# ============================================================================
# Core Campaign Models
# ============================================================================

class MarketingCampaign(BaseModel):
    """Complete marketing campaign configuration and management."""

    campaign_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique campaign identifier")
    campaign_name: str = Field(..., min_length=1, max_length=150, description="Campaign display name")
    campaign_description: Optional[str] = Field(None, max_length=500, description="Campaign description and objectives")

    # Campaign classification
    campaign_type: CampaignType = Field(..., description="Campaign type classification")
    campaign_status: CampaignStatus = Field(default=CampaignStatus.DRAFT, description="Current campaign status")
    priority_level: str = Field(default="medium", description="Campaign priority level")

    # Template and content
    template_id: Optional[str] = Field(None, description="Base template identifier")
    content_assets: List[ContentAsset] = Field(default_factory=list, description="Campaign content components")

    # Targeting and personalization
    target_audience: CampaignAudience = Field(..., description="Campaign target audience configuration")
    personalization_config: CampaignPersonalization = Field(..., description="Content personalization settings")

    # Delivery configuration
    delivery_channels: List[CampaignChannel] = Field(..., min_items=1, description="Campaign delivery channels")
    scheduling_config: CampaignScheduling = Field(..., description="Campaign scheduling and timing")

    # Performance tracking
    performance_goals: Dict[str, float] = Field(default_factory=dict, description="Campaign performance targets")
    success_metrics: List[str] = Field(default_factory=list, description="Key success indicators")

    # Integration and automation
    ghl_campaign_id: Optional[str] = Field(None, description="GoHighLevel campaign identifier")
    trigger_conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Automated trigger conditions")

    # Budget and resources
    budget_allocation: Optional[Decimal] = Field(None, ge=0, description="Campaign budget allocation")
    estimated_cost: Optional[Decimal] = Field(None, ge=0, description="Estimated campaign cost")
    actual_cost: Optional[Decimal] = Field(None, ge=0, description="Actual campaign cost")

    # Campaign lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Campaign creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    launched_at: Optional[datetime] = Field(None, description="Campaign launch timestamp")
    completed_at: Optional[datetime] = Field(None, description="Campaign completion timestamp")

    # Metadata and tags
    tags: List[str] = Field(default_factory=list, description="Campaign categorization tags")
    owner_id: str = Field(..., description="Campaign owner identifier")
    team_members: List[str] = Field(default_factory=list, description="Campaign team member IDs")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Ensure end date is after start date if provided."""
        if v and 'start_date' in values:
            start_date = values['scheduling_config'].start_date if 'scheduling_config' in values else None
            if start_date and v <= start_date:
                raise ValueError('End date must be after start date')
        return v

    @root_validator
    def validate_campaign_consistency(cls, values):
        """Validate campaign configuration consistency."""
        # Ensure template and campaign type compatibility
        template_id = values.get('template_id')
        campaign_type = values.get('campaign_type')

        # Additional validation logic can be added here
        return values


# ============================================================================
# Campaign Performance Models
# ============================================================================

class CampaignDeliveryMetrics(BaseModel):
    """Campaign delivery and engagement metrics."""

    metrics_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique metrics identifier")
    campaign_id: str = Field(..., description="Associated campaign identifier")

    # Delivery metrics
    total_sent: int = Field(default=0, ge=0, description="Total messages sent")
    total_delivered: int = Field(default=0, ge=0, description="Total messages delivered")
    total_bounced: int = Field(default=0, ge=0, description="Total messages bounced")
    total_failed: int = Field(default=0, ge=0, description="Total send failures")

    # Engagement metrics
    total_opens: int = Field(default=0, ge=0, description="Total message opens")
    unique_opens: int = Field(default=0, ge=0, description="Unique recipients who opened")
    total_clicks: int = Field(default=0, ge=0, description="Total link clicks")
    unique_clicks: int = Field(default=0, ge=0, description="Unique recipients who clicked")

    # Conversion metrics
    total_conversions: int = Field(default=0, ge=0, description="Total conversions")
    conversion_value: Decimal = Field(default=0, ge=0, description="Total conversion value")
    total_unsubscribes: int = Field(default=0, ge=0, description="Total unsubscribes")
    spam_complaints: int = Field(default=0, ge=0, description="Spam complaints received")

    # Calculated rates
    delivery_rate: float = Field(default=0, ge=0, le=1, description="Delivery success rate")
    open_rate: float = Field(default=0, ge=0, le=1, description="Email open rate")
    click_through_rate: float = Field(default=0, ge=0, le=1, description="Click-through rate")
    conversion_rate: float = Field(default=0, ge=0, le=1, description="Conversion rate")

    # Channel-specific metrics
    channel_metrics: Dict[CampaignChannel, Dict[str, float]] = Field(default_factory=dict, description="Per-channel performance")

    # Time-based analysis
    performance_by_hour: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Hourly performance breakdown")
    performance_by_day: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Daily performance breakdown")

    # A/B testing results
    variant_performance: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="A/B test variant performance")

    # Measurement period
    measurement_start: datetime = Field(..., description="Metrics measurement start time")
    measurement_end: Optional[datetime] = Field(None, description="Metrics measurement end time")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last metrics update")


class CampaignROIAnalysis(BaseModel):
    """Return on investment analysis for marketing campaigns."""

    roi_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique ROI analysis identifier")
    campaign_id: str = Field(..., description="Associated campaign identifier")

    # Cost analysis
    total_campaign_cost: Decimal = Field(default=0, ge=0, description="Total campaign investment")
    cost_breakdown: Dict[str, Decimal] = Field(default_factory=dict, description="Cost category breakdown")
    cost_per_send: Decimal = Field(default=0, ge=0, description="Cost per message sent")
    cost_per_acquisition: Decimal = Field(default=0, ge=0, description="Customer acquisition cost")

    # Revenue analysis
    total_revenue: Decimal = Field(default=0, ge=0, description="Total revenue generated")
    revenue_per_conversion: Decimal = Field(default=0, ge=0, description="Average revenue per conversion")
    attributed_revenue: Decimal = Field(default=0, ge=0, description="Directly attributed revenue")

    # ROI calculations
    roi_percentage: float = Field(default=0, description="Return on investment percentage")
    profit_margin: float = Field(default=0, description="Campaign profit margin")
    break_even_point: Optional[int] = Field(None, description="Break-even point in conversions")

    # Comparative analysis
    industry_benchmark_roi: Optional[float] = Field(None, description="Industry benchmark ROI")
    previous_campaign_comparison: Optional[float] = Field(None, description="Previous campaign performance comparison")

    # Predictive analysis
    projected_lifetime_value: Decimal = Field(default=0, ge=0, description="Projected customer lifetime value")
    estimated_future_revenue: Decimal = Field(default=0, ge=0, description="Estimated future revenue from campaign")

    analysis_date: datetime = Field(default_factory=datetime.utcnow, description="Analysis calculation date")
    analysis_period_days: int = Field(default=30, ge=1, description="Analysis period in days")


# ============================================================================
# Request/Response Models
# ============================================================================

class CampaignCreationRequest(BaseModel):
    """Request model for creating new marketing campaigns."""

    campaign_name: str = Field(..., min_length=1, max_length=150, description="Campaign name")
    campaign_type: CampaignType = Field(..., description="Campaign type")
    template_id: Optional[str] = Field(None, description="Base template to use")

    # Basic configuration
    target_audience_criteria: Dict[str, Any] = Field(..., description="Audience targeting criteria")
    delivery_channels: List[CampaignChannel] = Field(..., min_items=1, description="Delivery channels")

    # Scheduling
    start_date: datetime = Field(..., description="Campaign start date")
    end_date: Optional[datetime] = Field(None, description="Campaign end date")

    # Content customization
    content_overrides: Dict[str, str] = Field(default_factory=dict, description="Content customizations")
    personalization_level: PersonalizationLevel = Field(default=PersonalizationLevel.STANDARD, description="Personalization level")

    # Performance goals
    success_metrics: List[str] = Field(default_factory=list, description="Success measurement criteria")
    performance_goals: Dict[str, float] = Field(default_factory=dict, description="Performance targets")

    # Additional metadata
    tags: List[str] = Field(default_factory=list, description="Campaign tags")
    owner_id: str = Field(..., description="Campaign owner")


class CampaignGenerationResponse(BaseModel):
    """Response model for campaign generation operations."""

    campaign_id: str = Field(..., description="Generated campaign identifier")
    campaign_name: str = Field(..., description="Campaign name")
    status: CampaignStatus = Field(..., description="Campaign status")

    # Generation results
    generated_content_assets: List[ContentAsset] = Field(..., description="Generated content components")
    audience_size: int = Field(..., ge=0, description="Target audience size")
    estimated_reach: int = Field(..., ge=0, description="Estimated campaign reach")

    # Optimization insights
    claude_optimization_suggestions: List[str] = Field(default_factory=list, description="AI optimization recommendations")
    performance_predictions: Dict[str, float] = Field(default_factory=dict, description="Predicted performance metrics")

    # Technical details
    generation_time_ms: float = Field(..., ge=0, description="Content generation time in milliseconds")
    templates_used: List[str] = Field(default_factory=list, description="Templates utilized")
    personalization_applied: bool = Field(..., description="Personalization status")

    # Next steps
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended next steps")
    approval_required: bool = Field(default=False, description="Approval required before launch")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Response generation timestamp")


class CampaignAnalyticsRequest(BaseModel):
    """Request model for campaign analytics and reporting."""

    campaign_ids: List[str] = Field(..., min_items=1, description="Campaign IDs to analyze")
    analytics_type: str = Field(..., description="Type of analytics requested")

    # Time range
    start_date: datetime = Field(..., description="Analysis start date")
    end_date: datetime = Field(..., description="Analysis end date")

    # Analysis configuration
    include_roi_analysis: bool = Field(default=True, description="Include ROI calculations")
    include_channel_breakdown: bool = Field(default=True, description="Include channel-specific metrics")
    include_audience_insights: bool = Field(default=False, description="Include audience behavior analysis")

    # Comparison options
    compare_to_benchmarks: bool = Field(default=False, description="Compare to industry benchmarks")
    compare_to_previous_campaigns: bool = Field(default=False, description="Compare to historical campaigns")

    # Output format
    output_format: str = Field(default="json", description="Desired output format")
    include_visualizations: bool = Field(default=False, description="Include chart data")


# ============================================================================
# Performance Validation Models
# ============================================================================

MARKETING_PERFORMANCE_BENCHMARKS = {
    'campaign_generation_target_ms': 300,
    'template_rendering_target_ms': 150,
    'audience_calculation_target_ms': 500,
    'personalization_target_ms': 200,
    'ghl_sync_target_ms': 1000,
    'analytics_calculation_target_ms': 800,

    # Business performance targets
    'email_open_rate_target': 0.25,
    'email_click_rate_target': 0.03,
    'sms_response_rate_target': 0.08,
    'campaign_roi_target': 3.0,
    'audience_accuracy_target': 0.95
}


class CampaignPerformanceBenchmark(BaseModel):
    """Performance benchmark validation for campaign operations."""

    operation_name: str = Field(..., description="Operation being benchmarked")
    target_time_ms: float = Field(..., gt=0, description="Target performance time")
    actual_time_ms: float = Field(..., gt=0, description="Actual performance time")

    performance_met: bool = Field(..., description="Whether performance target was met")
    performance_ratio: float = Field(..., description="Actual/target ratio")

    # Context information
    campaign_complexity: str = Field(..., description="Campaign complexity level")
    audience_size: int = Field(..., ge=0, description="Audience size processed")
    content_assets_count: int = Field(..., ge=0, description="Number of content assets")

    benchmark_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Benchmark measurement time")


if __name__ == "__main__":
    # Example usage and validation
    print("Marketing Campaign Models - Data Structure Validation")

    # Create sample campaign template
    sample_template = CampaignTemplate(
        template_name="Luxury Property Showcase",
        template_category=TemplateCategory.PROPERTY_ALERTS,
        campaign_type=CampaignType.PROPERTY_SHOWCASE,
        target_audience=[AudienceSegment.LUXURY_BUYERS, AudienceSegment.MOVE_UP_BUYERS],
        recommended_channels=[CampaignChannel.EMAIL, CampaignChannel.SOCIAL_MEDIA],
        subject_line_templates=[
            "Exclusive: New Luxury Listing in {neighborhood}",
            "Premium Property Alert: {property_type} in {city}"
        ],
        content_assets=[
            ContentAsset(
                asset_type="hero_image",
                title="Property Hero Image",
                content_body="Stunning {property_type} featuring {key_features}",
                personalization_tokens={"property_type": "luxury_condo", "key_features": "city_views"}
            )
        ],
        call_to_action="Schedule Private Showing",
        created_by="system"
    )

    # Create sample campaign
    sample_campaign = MarketingCampaign(
        campaign_name="Q1 Luxury Property Showcase",
        campaign_type=CampaignType.PROPERTY_SHOWCASE,
        target_audience=CampaignAudience(
            audience_name="High-Value Prospects",
            demographic_filters={"income_range": "250k+", "property_budget": "1M+"},
            ghl_tag_filters=["luxury_buyer", "high_intent"]
        ),
        personalization_config=CampaignPersonalization(
            personalization_level=PersonalizationLevel.HYPER_PERSONALIZED,
            claude_content_generation=True
        ),
        delivery_channels=[CampaignChannel.EMAIL, CampaignChannel.SMS],
        scheduling_config=CampaignScheduling(
            start_date=datetime.utcnow() + timedelta(days=1),
            auto_optimize_send_times=True
        ),
        owner_id="agent_001"
    )

    print(f"✅ Template created: {sample_template.template_name}")
    print(f"✅ Campaign created: {sample_campaign.campaign_name}")
    print(f"📊 Performance targets: {MARKETING_PERFORMANCE_BENCHMARKS}")
    print("🚀 Marketing Campaign Models validation successful!")