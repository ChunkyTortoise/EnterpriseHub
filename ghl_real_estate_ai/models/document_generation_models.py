"""
Document Generation Models for Real Estate AI Platform

This module provides comprehensive data models for automated document generation
including professional reports, proposals, market analysis, and listing presentations.

Business Impact: $40K+/year in document automation and professional presentation
Performance Target: <2s generation time, professional template quality
Integration: Property valuations, marketing campaigns, seller workflow automation

Key Features:
- Multi-format support (PDF, DOCX, PPTX, HTML)
- Real estate specialized templates
- Dynamic content generation with Claude AI
- Professional branding and design
- Automated data integration from property valuations and campaigns
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
import json

from pydantic import BaseModel, Field, validator, root_validator


# ============================================================================
# Enums and Constants
# ============================================================================

class DocumentType(str, Enum):
    """Document type enumeration for different output formats."""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    HTML = "html"
    EXCEL = "xlsx"


class DocumentCategory(str, Enum):
    """Document category for real estate specialization."""
    SELLER_PROPOSAL = "seller_proposal"
    MARKET_ANALYSIS = "market_analysis"
    PROPERTY_SHOWCASE = "property_showcase"
    LISTING_PRESENTATION = "listing_presentation"
    PERFORMANCE_REPORT = "performance_report"
    CONTRACT_TEMPLATE = "contract_template"
    MARKETING_MATERIALS = "marketing_materials"
    COMPARATIVE_ANALYSIS = "comparative_analysis"


class DocumentStatus(str, Enum):
    """Document generation status tracking."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class TemplateStyle(str, Enum):
    """Template style options for professional branding."""
    EXECUTIVE = "executive"
    MODERN = "modern"
    CLASSIC = "classic"
    LUXURY = "luxury"
    MINIMALIST = "minimalist"


class ContentSource(str, Enum):
    """Source of content data for document generation."""
    PROPERTY_VALUATION = "property_valuation"
    MARKETING_CAMPAIGN = "marketing_campaign"
    SELLER_WORKFLOW = "seller_workflow"
    MANUAL_INPUT = "manual_input"
    CLAUDE_GENERATED = "claude_generated"


# Performance benchmarks for document generation
DOCUMENT_PERFORMANCE_BENCHMARKS = {
    'pdf_generation_target_ms': 2000,       # Target: <2s for PDF
    'docx_generation_target_ms': 1500,      # Target: <1.5s for DOCX
    'pptx_generation_target_ms': 3000,      # Target: <3s for PPTX
    'template_processing_target_ms': 500,    # Target: <500ms for template processing
    'content_enhancement_target_ms': 800,    # Target: <800ms for Claude enhancement
    'document_quality_score_min': 0.95,     # Minimum quality score
    'template_reuse_rate_target': 0.80,     # Target: 80% template reuse
    'generation_success_rate_target': 0.99  # Target: 99% success rate
}


# ============================================================================
# Core Document Models
# ============================================================================

class DocumentTemplate(BaseModel):
    """Document template configuration with real estate specialization."""

    template_id: str = Field(default_factory=lambda: f"tmpl_{uuid4().hex[:8]}")
    template_name: str = Field(..., min_length=1, max_length=100)
    template_category: DocumentCategory = Field(...)
    document_type: DocumentType = Field(...)
    template_style: TemplateStyle = Field(default=TemplateStyle.MODERN)

    # Template structure and content
    template_version: str = Field(default="1.0")
    template_description: str = Field(default="")
    template_file_path: Optional[str] = Field(None, description="Path to template file")
    template_content: Dict[str, Any] = Field(default_factory=dict)

    # Real estate specialization
    property_types: List[str] = Field(default_factory=list)
    market_segments: List[str] = Field(default_factory=list)
    target_audience: List[str] = Field(default_factory=list)

    # Content placeholders and variables
    content_placeholders: Dict[str, str] = Field(default_factory=dict)
    required_data_sources: List[ContentSource] = Field(default_factory=list)
    optional_data_sources: List[ContentSource] = Field(default_factory=list)

    # Template configuration
    supports_branding: bool = Field(default=True)
    allows_customization: bool = Field(default=True)
    requires_approval: bool = Field(default=False)

    # Metadata
    created_date: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(...)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = Field(default=0, ge=0)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentContent(BaseModel):
    """Document content structure for dynamic generation."""

    content_id: str = Field(default_factory=lambda: f"content_{uuid4().hex[:8]}")
    content_type: str = Field(..., description="Type of content (text, image, table, chart)")
    content_title: Optional[str] = Field(None)

    # Content data
    content_data: Dict[str, Any] = Field(default_factory=dict)
    content_source: ContentSource = Field(...)
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw source data")

    # Formatting and styling
    formatting_options: Dict[str, Any] = Field(default_factory=dict)
    position_config: Dict[str, Any] = Field(default_factory=dict)

    # Claude AI enhancement
    claude_enhanced: bool = Field(default=False)
    enhancement_prompt: Optional[str] = Field(None)
    enhancement_suggestions: List[str] = Field(default_factory=list)

    # Validation and quality
    content_validated: bool = Field(default=False)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    validation_notes: List[str] = Field(default_factory=list)


class DocumentGenerationRequest(BaseModel):
    """Request for document generation with comprehensive configuration."""

    # Request identification
    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex[:8]}")
    document_name: str = Field(..., min_length=1, max_length=200)
    document_category: DocumentCategory = Field(...)
    document_type: DocumentType = Field(...)

    # Template and styling
    template_id: Optional[str] = Field(None)
    template_style: TemplateStyle = Field(default=TemplateStyle.MODERN)
    custom_branding: Dict[str, Any] = Field(default_factory=dict)

    # Data sources and content
    property_valuation_id: Optional[str] = Field(None)
    marketing_campaign_id: Optional[str] = Field(None)
    seller_workflow_data: Optional[Dict[str, Any]] = Field(None)
    custom_content: Dict[str, Any] = Field(default_factory=dict)

    # Generation options
    include_claude_enhancement: bool = Field(default=True)
    claude_enhancement_prompt: Optional[str] = Field(None)
    content_personalization: Dict[str, Any] = Field(default_factory=dict)

    # Output configuration
    output_quality: str = Field(default="high", regex="^(draft|standard|high|premium)$")
    include_analytics: bool = Field(default=True)
    watermark_enabled: bool = Field(default=False)

    # Delivery and sharing
    delivery_options: Dict[str, Any] = Field(default_factory=dict)
    sharing_permissions: Dict[str, Any] = Field(default_factory=dict)
    expiration_date: Optional[datetime] = Field(None)

    # Request metadata
    requested_by: str = Field(...)
    requested_date: datetime = Field(default_factory=datetime.utcnow)
    priority: str = Field(default="normal", regex="^(low|normal|high|urgent)$")

    @validator('expiration_date')
    def validate_expiration_date(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError("Expiration date must be in the future")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentGenerationResponse(BaseModel):
    """Response from document generation with comprehensive metadata."""

    # Response identification
    request_id: str = Field(...)
    document_id: str = Field(default_factory=lambda: f"doc_{uuid4().hex[:8]}")

    # Generation results
    success: bool = Field(...)
    document_status: DocumentStatus = Field(...)
    document_name: str = Field(...)
    document_type: DocumentType = Field(...)

    # File information
    file_path: Optional[str] = Field(None)
    file_size_bytes: Optional[int] = Field(None, ge=0)
    download_url: Optional[str] = Field(None)
    preview_url: Optional[str] = Field(None)

    # Generation metrics
    generation_time_ms: float = Field(..., ge=0)
    content_sources_used: List[ContentSource] = Field(default_factory=list)
    claude_enhancement_applied: bool = Field(default=False)
    template_utilized: Optional[str] = Field(None)

    # Quality and validation
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    validation_passed: bool = Field(default=True)
    validation_notes: List[str] = Field(default_factory=list)

    # Content summary
    page_count: Optional[int] = Field(None, ge=1)
    content_sections: List[str] = Field(default_factory=list)
    data_sources_integrated: List[str] = Field(default_factory=list)

    # Enhancement and optimization
    claude_suggestions: List[str] = Field(default_factory=list)
    optimization_applied: List[str] = Field(default_factory=list)
    performance_notes: List[str] = Field(default_factory=list)

    # Error handling
    error_message: Optional[str] = Field(None)
    error_code: Optional[str] = Field(None)
    retry_suggested: bool = Field(default=False)

    # Metadata
    generated_date: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(...)
    expires_at: Optional[datetime] = Field(None)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Specialized Real Estate Document Models
# ============================================================================

class SellerProposalData(BaseModel):
    """Data structure for seller proposal generation."""

    # Seller information
    seller_name: str = Field(...)
    seller_contact: Dict[str, Any] = Field(default_factory=dict)
    property_address: str = Field(...)

    # Property valuation data
    estimated_value: Decimal = Field(..., ge=0)
    valuation_confidence: float = Field(..., ge=0.0, le=1.0)
    comparable_sales: List[Dict[str, Any]] = Field(default_factory=list)
    market_analysis: Dict[str, Any] = Field(default_factory=dict)

    # Marketing strategy
    marketing_plan: Dict[str, Any] = Field(default_factory=dict)
    pricing_strategy: Dict[str, Any] = Field(default_factory=dict)
    timeline_projections: Dict[str, Any] = Field(default_factory=dict)

    # Agent and company information
    agent_information: Dict[str, Any] = Field(default_factory=dict)
    company_branding: Dict[str, Any] = Field(default_factory=dict)
    success_metrics: Dict[str, Any] = Field(default_factory=dict)

    # Additional services
    included_services: List[str] = Field(default_factory=list)
    optional_services: List[str] = Field(default_factory=list)
    service_pricing: Dict[str, Decimal] = Field(default_factory=dict)


class MarketAnalysisData(BaseModel):
    """Data structure for market analysis report generation."""

    # Market scope
    analysis_area: str = Field(...)
    property_type_focus: List[str] = Field(default_factory=list)
    price_range: Dict[str, Decimal] = Field(default_factory=dict)
    analysis_period: Dict[str, datetime] = Field(default_factory=dict)

    # Market metrics
    median_sale_price: Decimal = Field(..., ge=0)
    price_trend_percentage: float = Field(...)
    days_on_market: int = Field(..., ge=0)
    inventory_levels: Dict[str, int] = Field(default_factory=dict)

    # Comparative analysis
    comparable_sales: List[Dict[str, Any]] = Field(default_factory=list)
    competitive_listings: List[Dict[str, Any]] = Field(default_factory=list)
    market_positioning: Dict[str, Any] = Field(default_factory=dict)

    # Market predictions
    forecast_data: Dict[str, Any] = Field(default_factory=dict)
    risk_factors: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)

    # Data sources and credibility
    data_sources: List[str] = Field(default_factory=list)
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    analyst_notes: List[str] = Field(default_factory=list)


class PropertyShowcaseData(BaseModel):
    """Data structure for property showcase presentation."""

    # Property details
    property_address: str = Field(...)
    property_description: str = Field(...)
    property_features: Dict[str, Any] = Field(default_factory=dict)
    property_specifications: Dict[str, Any] = Field(default_factory=dict)

    # Visual assets
    property_images: List[Dict[str, str]] = Field(default_factory=list)
    virtual_tour_url: Optional[str] = Field(None)
    floor_plan_urls: List[str] = Field(default_factory=list)
    video_tour_url: Optional[str] = Field(None)

    # Pricing and value proposition
    listing_price: Decimal = Field(..., ge=0)
    price_justification: Dict[str, Any] = Field(default_factory=dict)
    value_highlights: List[str] = Field(default_factory=list)
    unique_selling_points: List[str] = Field(default_factory=list)

    # Neighborhood and location
    neighborhood_highlights: List[str] = Field(default_factory=list)
    local_amenities: List[Dict[str, Any]] = Field(default_factory=list)
    school_information: Dict[str, Any] = Field(default_factory=dict)
    transportation_access: List[str] = Field(default_factory=list)

    # Investment and lifestyle appeal
    investment_potential: Dict[str, Any] = Field(default_factory=dict)
    lifestyle_benefits: List[str] = Field(default_factory=list)
    target_buyer_profiles: List[str] = Field(default_factory=list)


class PerformanceReportData(BaseModel):
    """Data structure for performance and analytics reports."""

    # Report scope and period
    report_title: str = Field(...)
    report_period: Dict[str, datetime] = Field(default_factory=dict)
    report_scope: List[str] = Field(default_factory=list)

    # Key performance indicators
    key_metrics: Dict[str, Union[int, float, Decimal]] = Field(default_factory=dict)
    performance_trends: Dict[str, List[float]] = Field(default_factory=dict)
    benchmark_comparisons: Dict[str, Dict[str, float]] = Field(default_factory=dict)

    # Campaign performance (if applicable)
    campaign_results: List[Dict[str, Any]] = Field(default_factory=list)
    engagement_metrics: Dict[str, float] = Field(default_factory=dict)
    conversion_analytics: Dict[str, Any] = Field(default_factory=dict)

    # Business insights
    success_stories: List[Dict[str, Any]] = Field(default_factory=list)
    improvement_areas: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)

    # Visual data representation
    charts_config: List[Dict[str, Any]] = Field(default_factory=list)
    tables_data: List[Dict[str, Any]] = Field(default_factory=list)
    infographic_elements: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# Document Processing and Enhancement Models
# ============================================================================

class ClaudeDocumentEnhancement(BaseModel):
    """Claude AI enhancement configuration for document generation."""

    enhancement_id: str = Field(default_factory=lambda: f"enh_{uuid4().hex[:8]}")
    enhancement_type: str = Field(..., description="Type of enhancement (content, style, structure)")

    # Enhancement prompt and context
    base_prompt: str = Field(..., min_length=10)
    context_data: Dict[str, Any] = Field(default_factory=dict)
    enhancement_goals: List[str] = Field(default_factory=list)

    # Content focus areas
    focus_sections: List[str] = Field(default_factory=list)
    enhancement_priorities: List[str] = Field(default_factory=list)
    style_preferences: Dict[str, Any] = Field(default_factory=dict)

    # Output requirements
    tone_and_voice: str = Field(default="professional")
    target_audience: str = Field(default="real_estate_clients")
    content_length_preference: str = Field(default="comprehensive")

    # Enhancement results
    enhancement_applied: bool = Field(default=False)
    original_content_length: Optional[int] = Field(None, ge=0)
    enhanced_content_length: Optional[int] = Field(None, ge=0)
    improvement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    enhancement_suggestions: List[str] = Field(default_factory=list)

    # Processing metadata
    processing_time_ms: float = Field(default=0.0, ge=0)
    claude_model_used: str = Field(default="claude-3-sonnet")
    enhancement_date: datetime = Field(default_factory=datetime.utcnow)


class DocumentQualityValidation(BaseModel):
    """Document quality validation and scoring model."""

    validation_id: str = Field(default_factory=lambda: f"val_{uuid4().hex[:8]}")
    document_id: str = Field(...)

    # Quality scoring
    overall_quality_score: float = Field(..., ge=0.0, le=1.0)
    content_quality_score: float = Field(..., ge=0.0, le=1.0)
    design_quality_score: float = Field(..., ge=0.0, le=1.0)
    data_accuracy_score: float = Field(..., ge=0.0, le=1.0)

    # Validation criteria
    content_completeness: bool = Field(default=False)
    data_accuracy_verified: bool = Field(default=False)
    formatting_consistent: bool = Field(default=False)
    branding_compliant: bool = Field(default=False)

    # Quality metrics
    spelling_errors_count: int = Field(default=0, ge=0)
    grammar_errors_count: int = Field(default=0, ge=0)
    formatting_issues_count: int = Field(default=0, ge=0)
    data_inconsistencies_count: int = Field(default=0, ge=0)

    # Validation results
    validation_passed: bool = Field(...)
    critical_issues: List[str] = Field(default_factory=list)
    recommended_fixes: List[str] = Field(default_factory=list)

    # Validation metadata
    validation_date: datetime = Field(default_factory=datetime.utcnow)
    validated_by: str = Field(default="automated_system")
    validation_notes: List[str] = Field(default_factory=list)


class DocumentDeliveryConfiguration(BaseModel):
    """Configuration for document delivery and sharing."""

    delivery_id: str = Field(default_factory=lambda: f"del_{uuid4().hex[:8]}")
    document_id: str = Field(...)

    # Delivery methods
    email_delivery: Dict[str, Any] = Field(default_factory=dict)
    portal_access: Dict[str, Any] = Field(default_factory=dict)
    direct_download: Dict[str, Any] = Field(default_factory=dict)

    # Access control
    access_permissions: Dict[str, List[str]] = Field(default_factory=dict)
    password_protection: Optional[str] = Field(None)
    expiration_settings: Dict[str, Any] = Field(default_factory=dict)

    # Tracking and analytics
    delivery_tracking: bool = Field(default=True)
    view_analytics: bool = Field(default=True)
    download_tracking: bool = Field(default=True)

    # Notification settings
    delivery_notifications: List[str] = Field(default_factory=list)
    access_notifications: bool = Field(default=False)
    expiration_warnings: bool = Field(default=True)

    # Delivery status
    delivery_status: str = Field(default="pending")
    delivery_attempts: int = Field(default=0, ge=0)
    last_delivery_attempt: Optional[datetime] = Field(None)
    successful_delivery: bool = Field(default=False)


# ============================================================================
# Analytics and Performance Models
# ============================================================================

class DocumentGenerationMetrics(BaseModel):
    """Comprehensive metrics for document generation performance."""

    metrics_id: str = Field(default_factory=lambda: f"metrics_{uuid4().hex[:8]}")
    measurement_period: Dict[str, datetime] = Field(default_factory=dict)

    # Generation performance
    total_documents_generated: int = Field(default=0, ge=0)
    successful_generations: int = Field(default=0, ge=0)
    failed_generations: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    # Performance timing
    avg_generation_time_ms: float = Field(default=0.0, ge=0)
    median_generation_time_ms: float = Field(default=0.0, ge=0)
    p95_generation_time_ms: float = Field(default=0.0, ge=0)
    fastest_generation_ms: float = Field(default=0.0, ge=0)
    slowest_generation_ms: float = Field(default=0.0, ge=0)

    # Document type breakdown
    documents_by_type: Dict[DocumentType, int] = Field(default_factory=dict)
    documents_by_category: Dict[DocumentCategory, int] = Field(default_factory=dict)
    documents_by_template: Dict[str, int] = Field(default_factory=dict)

    # Quality metrics
    avg_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_distribution: Dict[str, int] = Field(default_factory=dict)
    claude_enhancement_usage: float = Field(default=0.0, ge=0.0, le=1.0)

    # Business impact
    estimated_time_saved_hours: float = Field(default=0.0, ge=0)
    estimated_cost_savings: Decimal = Field(default=Decimal("0"), ge=0)
    client_satisfaction_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # System health
    error_rates: Dict[str, float] = Field(default_factory=dict)
    resource_utilization: Dict[str, float] = Field(default_factory=dict)
    template_cache_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    # Reporting metadata
    metrics_generated_date: datetime = Field(default_factory=datetime.utcnow)
    metrics_generated_by: str = Field(default="automated_system")


class DocumentUsageAnalytics(BaseModel):
    """Analytics for document usage and engagement."""

    analytics_id: str = Field(default_factory=lambda: f"analytics_{uuid4().hex[:8]}")
    document_id: str = Field(...)

    # Usage statistics
    total_views: int = Field(default=0, ge=0)
    total_downloads: int = Field(default=0, ge=0)
    unique_viewers: int = Field(default=0, ge=0)
    avg_view_duration_seconds: float = Field(default=0.0, ge=0)

    # Engagement metrics
    engagement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    bounce_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    # User feedback
    user_ratings: List[float] = Field(default_factory=list)
    avg_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    feedback_comments: List[str] = Field(default_factory=list)

    # Conversion tracking
    leads_generated: int = Field(default=0, ge=0)
    conversions_attributed: int = Field(default=0, ge=0)
    conversion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    revenue_attributed: Decimal = Field(default=Decimal("0"), ge=0)

    # Geographic and demographic insights
    viewer_locations: Dict[str, int] = Field(default_factory=dict)
    viewer_demographics: Dict[str, Any] = Field(default_factory=dict)
    device_usage: Dict[str, int] = Field(default_factory=dict)

    # Analytics metadata
    analytics_updated: datetime = Field(default_factory=datetime.utcnow)
    analytics_version: str = Field(default="1.0")


# ============================================================================
# Integration Models
# ============================================================================

class PropertyValuationIntegration(BaseModel):
    """Integration model for property valuation data in documents."""

    valuation_id: str = Field(...)
    property_data: Dict[str, Any] = Field(default_factory=dict)
    valuation_results: Dict[str, Any] = Field(default_factory=dict)
    comparative_analysis: Dict[str, Any] = Field(default_factory=dict)
    market_insights: Dict[str, Any] = Field(default_factory=dict)

    # Integration metadata
    integration_date: datetime = Field(default_factory=datetime.utcnow)
    data_freshness: timedelta = Field(default=timedelta(hours=24))
    integration_source: str = Field(default="property_valuation_engine")


class MarketingCampaignIntegration(BaseModel):
    """Integration model for marketing campaign data in documents."""

    campaign_id: str = Field(...)
    campaign_data: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    audience_insights: Dict[str, Any] = Field(default_factory=dict)
    content_assets: List[Dict[str, Any]] = Field(default_factory=list)

    # Integration metadata
    integration_date: datetime = Field(default_factory=datetime.utcnow)
    data_freshness: timedelta = Field(default=timedelta(hours=1))
    integration_source: str = Field(default="marketing_campaign_engine")


class SellerWorkflowIntegration(BaseModel):
    """Integration model for seller workflow data in documents."""

    seller_id: str = Field(...)
    workflow_stage: str = Field(...)
    interaction_history: List[Dict[str, Any]] = Field(default_factory=list)
    engagement_metrics: Dict[str, Any] = Field(default_factory=dict)
    progress_summary: Dict[str, Any] = Field(default_factory=dict)

    # Integration metadata
    integration_date: datetime = Field(default_factory=datetime.utcnow)
    data_freshness: timedelta = Field(default=timedelta(minutes=30))
    integration_source: str = Field(default="seller_claude_integration_engine")


# ============================================================================
# Bulk Processing and Automation Models
# ============================================================================

class BulkDocumentRequest(BaseModel):
    """Request for bulk document generation with template automation."""

    bulk_request_id: str = Field(default_factory=lambda: f"bulk_{uuid4().hex[:8]}")
    request_name: str = Field(..., min_length=1)

    # Bulk processing configuration
    document_requests: List[DocumentGenerationRequest] = Field(..., min_items=1)
    processing_priority: str = Field(default="normal")
    batch_size: int = Field(default=10, ge=1, le=50)

    # Quality and consistency settings
    consistent_styling: bool = Field(default=True)
    quality_validation: bool = Field(default=True)
    claude_enhancement_batch: bool = Field(default=True)

    # Progress tracking
    completion_notification: bool = Field(default=True)
    progress_updates: bool = Field(default=True)

    # Request metadata
    requested_by: str = Field(...)
    requested_date: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion: Optional[datetime] = Field(None)


class BulkDocumentResponse(BaseModel):
    """Response for bulk document generation processing."""

    bulk_request_id: str = Field(...)

    # Processing summary
    total_requests: int = Field(..., ge=0)
    successful_generations: int = Field(default=0, ge=0)
    failed_generations: int = Field(default=0, ge=0)
    in_progress: int = Field(default=0, ge=0)

    # Individual results
    document_results: List[DocumentGenerationResponse] = Field(default_factory=list)

    # Bulk processing metrics
    total_processing_time_ms: float = Field(default=0.0, ge=0)
    avg_document_time_ms: float = Field(default=0.0, ge=0)
    processing_efficiency: float = Field(default=0.0, ge=0.0, le=1.0)

    # Quality summary
    overall_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    consistency_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Status and completion
    processing_status: str = Field(default="completed")
    completion_date: Optional[datetime] = Field(None)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Model Validation and Utilities
# ============================================================================

def validate_document_request(request: DocumentGenerationRequest) -> Dict[str, Any]:
    """Validate document generation request for completeness and feasibility."""
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'suggestions': []
    }

    # Check required data sources
    if request.document_category == DocumentCategory.SELLER_PROPOSAL:
        if not request.property_valuation_id and not request.custom_content:
            validation_results['errors'].append("Seller proposal requires property valuation or custom content")
            validation_results['valid'] = False

    if request.document_category == DocumentCategory.PERFORMANCE_REPORT:
        if not request.marketing_campaign_id and not request.seller_workflow_data:
            validation_results['errors'].append("Performance report requires campaign or workflow data")
            validation_results['valid'] = False

    # Check template compatibility
    if request.template_id and request.document_type == DocumentType.PPTX:
        if request.document_category not in [DocumentCategory.PROPERTY_SHOWCASE, DocumentCategory.LISTING_PRESENTATION]:
            validation_results['warnings'].append("PPTX format recommended for showcase presentations")

    # Performance suggestions
    if request.include_claude_enhancement and not request.claude_enhancement_prompt:
        validation_results['suggestions'].append("Custom enhancement prompt can improve content quality")

    return validation_results


def calculate_estimated_generation_time(request: DocumentGenerationRequest) -> float:
    """Calculate estimated generation time based on document complexity."""
    base_times = {
        DocumentType.PDF: 1000,
        DocumentType.DOCX: 800,
        DocumentType.PPTX: 2000,
        DocumentType.HTML: 500,
        DocumentType.EXCEL: 1200
    }

    base_time = base_times.get(request.document_type, 1000)

    # Adjust for complexity factors
    if request.include_claude_enhancement:
        base_time += 500

    if request.property_valuation_id and request.marketing_campaign_id:
        base_time += 300  # Data integration overhead

    if request.output_quality == "premium":
        base_time *= 1.5

    return base_time


def get_recommended_templates(document_category: DocumentCategory, property_type: Optional[str] = None) -> List[str]:
    """Get recommended templates for specific document categories and property types."""
    template_recommendations = {
        DocumentCategory.SELLER_PROPOSAL: {
            'luxury': ['luxury_seller_proposal', 'executive_proposal'],
            'standard': ['modern_seller_proposal', 'classic_proposal'],
            'commercial': ['commercial_proposal', 'investment_proposal']
        },
        DocumentCategory.MARKET_ANALYSIS: {
            'residential': ['residential_market_analysis', 'neighborhood_report'],
            'commercial': ['commercial_market_analysis', 'investment_analysis']
        },
        DocumentCategory.PROPERTY_SHOWCASE: {
            'luxury': ['luxury_showcase', 'premium_presentation'],
            'standard': ['modern_showcase', 'classic_presentation']
        }
    }

    category_templates = template_recommendations.get(document_category, {})
    return category_templates.get(property_type or 'standard', ['default_template'])


# Export all models for use in other modules
__all__ = [
    # Enums
    'DocumentType', 'DocumentCategory', 'DocumentStatus', 'TemplateStyle', 'ContentSource',

    # Core Models
    'DocumentTemplate', 'DocumentContent', 'DocumentGenerationRequest', 'DocumentGenerationResponse',

    # Specialized Models
    'SellerProposalData', 'MarketAnalysisData', 'PropertyShowcaseData', 'PerformanceReportData',

    # Enhancement Models
    'ClaudeDocumentEnhancement', 'DocumentQualityValidation', 'DocumentDeliveryConfiguration',

    # Analytics Models
    'DocumentGenerationMetrics', 'DocumentUsageAnalytics',

    # Integration Models
    'PropertyValuationIntegration', 'MarketingCampaignIntegration', 'SellerWorkflowIntegration',

    # Bulk Processing Models
    'BulkDocumentRequest', 'BulkDocumentResponse',

    # Constants
    'DOCUMENT_PERFORMANCE_BENCHMARKS',

    # Utilities
    'validate_document_request', 'calculate_estimated_generation_time', 'get_recommended_templates'
]