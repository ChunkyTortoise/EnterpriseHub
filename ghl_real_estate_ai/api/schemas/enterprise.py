"""
Enterprise API Schemas

Pydantic models for enterprise partnership management, SSO authentication,
volume billing, and analytics. Supporting Fortune 500 integration.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
from ghl_real_estate_ai.api.enterprise.auth import SSOProvider, TenantRole
from ghl_real_estate_ai.models.api_analytics_types import (
    ComplianceMetrics,
    CostMetrics,
    EfficiencyMetrics,
    PartnershipMetrics,
    PricingStructure,
    QualityMetrics,
    RelocationMetrics,
    RevenueMetrics,
    SatisfactionMetrics,
    TierConfig,
    TimelineMetric,
)


# ===================================================================
# Enums
# ===================================================================

class PartnershipStatus(str, Enum):
    """Partnership status options."""
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    RENEWAL_REQUIRED = "renewal_required"


class PartnershipTier(str, Enum):
    """Partnership tier levels for Fortune 500 companies."""
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class RelocationStatus(str, Enum):
    """Employee relocation status tracking."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    PROPERTY_SEARCH = "property_search"
    APPLICATION_SUBMITTED = "application_submitted"
    LEASE_NEGOTIATION = "lease_negotiation"
    MOVE_COORDINATION = "move_coordination"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ContractStatus(str, Enum):
    """Enterprise contract status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class BillingFrequency(str, Enum):
    """Billing frequency options."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class PaymentTerms(str, Enum):
    """Payment terms for enterprise contracts."""
    NET15 = "NET15"
    NET30 = "NET30"
    NET60 = "NET60"
    IMMEDIATE = "IMMEDIATE"


# ===================================================================
# Base Models
# ===================================================================

class TimestampedModel(BaseModel):
    """Base model with timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


# ===================================================================
# Authentication & Tenant Models
# ===================================================================

class TenantConfigurationRequest(BaseModel):
    """Request to create or update tenant configuration."""
    company_name: str = Field(..., min_length=2, max_length=100)
    domain: str = Field(..., pattern=r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}$')
    sso_provider: SSOProvider
    sso_config: Dict[str, Any] = Field(default_factory=dict)
    partnership_id: Optional[str] = None
    admin_email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    allowed_domains: Optional[List[str]] = Field(default_factory=list)
    max_users: int = Field(1000, ge=1, le=10000)
    session_timeout_hours: int = Field(8, ge=1, le=24)
    require_mfa: bool = True
    auto_provision_users: bool = True

    @field_validator('allowed_domains', mode='before')
    @classmethod
    def ensure_domain_in_allowed(cls, v, info: ValidationInfo):
        """Ensure primary domain is in allowed domains list."""
        if v is None:
            v = []
        domain = info.data.get('domain')
        if domain and domain not in v:
            v.append(domain)
        return v


class TenantResponse(BaseModel):
    """Response model for tenant information."""
    tenant_id: str
    company_name: str
    domain: str
    sso_provider: SSOProvider
    partnership_id: Optional[str]
    status: str
    max_users: int
    current_user_count: int = 0
    require_mfa: bool
    auto_provision_users: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserProvisioningRequest(BaseModel):
    """Request to provision enterprise user."""
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    name: str = Field(..., min_length=1, max_length=100)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    roles: List[TenantRole] = Field(default_factory=lambda: [TenantRole.EMPLOYEE])
    mfa_enabled: Optional[bool] = None


class EnterpriseUserResponse(BaseModel):
    """Response model for enterprise user."""
    user_id: str
    tenant_id: str
    email: str
    name: str
    first_name: Optional[str]
    last_name: Optional[str]
    department: Optional[str]
    job_title: Optional[str]
    roles: List[TenantRole]
    permissions: List[str]
    status: str
    last_login: Optional[datetime]
    mfa_enabled: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SSOLoginRequest(BaseModel):
    """Request to initiate SSO login."""
    domain: str = Field(..., description="Company domain for tenant lookup")
    redirect_uri: str = Field(..., description="Post-authentication redirect URI")


class SSOCallbackRequest(BaseModel):
    """Request to handle SSO callback."""
    code: str = Field(..., description="Authorization code from SSO provider")
    state: str = Field(..., description="State parameter for security")


class AuthenticationResponse(BaseModel):
    """Response for successful authentication."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: EnterpriseUserResponse
    tenant_id: str


# ===================================================================
# Partnership Models
# ===================================================================

class PartnershipCreationRequest(BaseModel):
    """Request to create corporate partnership."""
    company_name: str = Field(..., min_length=2, max_length=200)
    contact_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    contact_name: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, description="Small, Medium, Large, Enterprise")
    industry: Optional[str] = Field(None, max_length=100)
    headquarters_location: Optional[str] = Field(None, max_length=100)
    expected_volume: int = Field(..., ge=10, le=10000, description="Expected annual relocation volume")
    preferred_tier: Optional[PartnershipTier] = None

    @field_validator('company_size')
    @classmethod
    def validate_company_size(cls, v):
        if v and v not in ['Small', 'Medium', 'Large', 'Enterprise']:
            raise ValueError('Company size must be Small, Medium, Large, or Enterprise')
        return v


class PartnershipUpdateRequest(BaseModel):
    """Request to update partnership configuration."""
    contact_email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    contact_name: Optional[str] = Field(None, max_length=100)
    expected_volume: Optional[int] = Field(None, ge=10, le=10000)
    tier: Optional[PartnershipTier] = None
    status: Optional[PartnershipStatus] = None


class PartnershipSummary(BaseModel):
    """Summary model for partnership listing."""
    partnership_id: str
    company_name: str
    tier: PartnershipTier
    status: PartnershipStatus
    expected_annual_volume: int
    actual_volume_ytd: int = 0
    total_revenue: Decimal = Field(default=Decimal('0.00'))
    health_score: Optional[float] = None
    created_at: datetime
    last_activity: Optional[datetime] = None

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


class PartnershipDetail(PartnershipSummary):
    """Detailed partnership model."""
    contact_email: str
    contact_name: Optional[str]
    company_size: Optional[str]
    industry: Optional[str]
    headquarters_location: Optional[str]
    tier_config: TierConfig = Field(default_factory=dict)
    pricing_structure: PricingStructure = Field(default_factory=dict)
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    dedicated_account_manager: Optional[str] = None
    enterprise_subscription_id: Optional[str] = None


# ===================================================================
# Relocation Models
# ===================================================================

class RelocationRequest(BaseModel):
    """Individual relocation request."""
    employee_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    employee_name: Optional[str] = Field(None, max_length=100)
    destination_city: str = Field(..., min_length=2, max_length=100)
    destination_state: Optional[str] = Field(None, max_length=50)
    housing_budget: Decimal = Field(..., gt=0, description="Monthly housing budget")
    preferred_housing_type: Optional[str] = Field("any", description="Apartment, house, condo, etc.")
    start_date: datetime = Field(..., description="Desired relocation start date")
    special_requirements: Optional[str] = Field(None, max_length=500)

    @field_validator('housing_budget')
    @classmethod
    def validate_housing_budget(cls, v):
        if v <= 0 or v > Decimal('50000'):
            raise ValueError('Housing budget must be between $1 and $50,000')
        return v


class BulkRelocationRequest(BaseModel):
    """Request for bulk employee relocations."""
    relocations: List[RelocationRequest] = Field(..., min_length=1, max_length=100)
    batch_priority: Optional[str] = Field("normal", description="normal, high, urgent")
    notification_email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')


class RelocationResponse(BaseModel):
    """Response for relocation processing."""
    relocation_id: str
    batch_id: Optional[str] = None
    employee_email: str
    status: RelocationStatus
    estimated_completion_date: Optional[datetime] = None
    estimated_revenue: Decimal
    progress_percentage: int = Field(0, ge=0, le=100)
    created_at: datetime
    last_updated: datetime

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


class RelocationTracking(BaseModel):
    """Detailed relocation tracking information."""
    relocation_id: str
    partnership_id: str
    employee_email: str
    destination: Dict[str, Any]
    timeline_metrics: TimelineMetric
    cost_metrics: CostMetrics
    satisfaction_metrics: SatisfactionMetrics
    efficiency_metrics: EfficiencyMetrics
    compliance_metrics: ComplianceMetrics
    success_indicators: Dict[str, Any]
    real_time_status: Dict[str, Any]
    last_updated: datetime

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


# ===================================================================
# Contract & Billing Models
# ===================================================================

class ContractCreationRequest(BaseModel):
    """Request to create enterprise contract."""
    partnership_id: str
    expected_monthly_volume: int = Field(..., ge=10, le=5000)
    contract_term_months: int = Field(..., ge=6, le=60)
    billing_contact_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    secondary_billing_contact: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    payment_terms: PaymentTerms
    billing_frequency: BillingFrequency = BillingFrequency.MONTHLY
    currency: str = Field("USD", max_length=3)
    auto_renewal: bool = True
    custom_rate_per_transaction: Optional[Decimal] = Field(None, gt=0)
    volume_shortfall_penalty: Optional[Decimal] = Field(Decimal('0.00'), ge=0)
    revenue_share_percentage: Optional[Decimal] = Field(Decimal('0.30'), ge=0, le=1)
    minimum_revenue_guarantee: Optional[Decimal] = Field(Decimal('0.00'), ge=0)

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        valid_currencies = ['USD', 'EUR', 'GBP', 'CAD']
        if v not in valid_currencies:
            raise ValueError(f'Currency must be one of: {", ".join(valid_currencies)}')
        return v


class ContractResponse(BaseModel):
    """Response model for enterprise contract."""
    contract_id: str
    partnership_id: str
    volume_tier: str
    pricing_structure: PricingStructure
    contract_terms: Dict[str, Any]
    billing_contacts: Dict[str, Any]
    volume_commitments: Dict[str, Any]
    revenue_sharing: RevenueMetrics
    status: ContractStatus
    total_billed: Decimal = Field(default=Decimal('0.00'))
    total_volume: int = 0
    last_billing_date: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


class VolumeDiscountTierInfo(BaseModel):
    """Information about volume discount tiers."""
    tier_name: str
    min_monthly_volume: int
    max_monthly_volume: Optional[int]
    discount_percentage: Decimal
    base_rate: Decimal
    setup_fee: Decimal

    model_config = ConfigDict(json_encoders={
            Decimal: lambda v: float(v)})


class BillingPeriodRequest(BaseModel):
    """Request to process billing for a period."""
    billing_period_start: datetime
    billing_period_end: datetime
    include_adjustments: bool = True
    generate_invoice: bool = True


class VolumeBillingResponse(BaseModel):
    """Response for volume billing processing."""
    contract_id: str
    billing_period: str
    volume_summary: Dict[str, Any]
    billing_calculation: Dict[str, Any]
    invoice: Optional[Dict[str, Any]] = None
    payment_result: Dict[str, Any]
    processed_at: datetime

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


class RevenueShareCalculation(BaseModel):
    """Revenue sharing calculation result."""
    contract_id: str
    period_start: datetime
    period_end: datetime
    gross_revenue: RevenueMetrics
    cost_breakdown: CostMetrics
    net_revenue: Decimal
    share_percentage: float
    calculated_share: Decimal
    adjustments_applied: List[Dict[str, Any]]
    final_payout_amount: Decimal
    payout_status: str
    calculated_at: datetime

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


# ===================================================================
# Analytics Models
# ===================================================================

class AnalyticsPeriodRequest(BaseModel):
    """Request for analytics within a specific period."""
    analysis_period_days: int = Field(90, ge=7, le=365)
    include_predictions: bool = True
    include_benchmarks: bool = True


class PerformanceMetrics(BaseModel):
    """Core performance metrics."""
    relocation_metrics: RelocationMetrics
    financial_metrics: RevenueMetrics
    efficiency_metrics: EfficiencyMetrics
    quality_metrics: QualityMetrics

    model_config = ConfigDict(json_encoders={
            Decimal: lambda v: float(v)})


class TrendAnalysis(BaseModel):
    """Performance trend analysis."""
    volume_trend: Dict[str, Any]
    revenue_trend: Dict[str, Any]
    satisfaction_trend: Dict[str, Any]


class BenchmarkComparison(BaseModel):
    """Performance benchmark comparison."""
    tier_benchmark: Dict[str, Any]
    performance_vs_benchmark: Dict[str, Any]


class HealthScoreDetails(BaseModel):
    """Partnership health score breakdown."""
    overall_score: float = Field(..., ge=0, le=100)
    component_scores: Dict[str, float]
    health_status: str
    improvement_priority: str


class PartnershipAnalyticsResponse(BaseModel):
    """Comprehensive partnership analytics response."""
    partnership_id: str
    analysis_period: Dict[str, datetime]
    core_metrics: PerformanceMetrics
    trend_analysis: TrendAnalysis
    benchmark_analysis: BenchmarkComparison
    health_score: HealthScoreDetails
    predictive_insights: List[Dict[str, Any]]
    recommendations: List[str]
    analysis_confidence: float
    generated_at: datetime

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


class RevenueAttributionResponse(BaseModel):
    """Revenue attribution analysis response."""
    partnership_id: str
    attribution_period: Dict[str, datetime]
    direct_revenue_attribution: Dict[str, Any]
    indirect_revenue_attribution: Dict[str, Any]
    revenue_stream_breakdown: Dict[str, Any]
    customer_lifetime_value: Dict[str, Any]
    total_attributed_revenue: Decimal
    revenue_attribution_rate: float
    attribution_confidence: Dict[str, Any]
    calculated_at: datetime

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


class ForecastRequest(BaseModel):
    """Request for partnership forecast."""
    forecast_months: int = Field(12, ge=3, le=24)
    include_scenarios: bool = True
    confidence_level: float = Field(0.85, ge=0.5, le=0.99)


class PartnershipForecast(BaseModel):
    """Partnership forecast response."""
    partnership_id: str
    forecast_horizon_months: int
    historical_data_summary: Dict[str, Any]
    volume_forecast: Dict[str, Any]
    revenue_forecast: Dict[str, Any]
    health_forecast: Dict[str, Any]
    risk_opportunity_analysis: Dict[str, Any]
    forecast_confidence: Dict[str, Any]
    scenario_analysis: Dict[str, Any]
    forecast_assumptions: List[str]
    generated_at: datetime

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


class CompetitiveAnalysisResponse(BaseModel):
    """Competitive analysis response."""
    partnership_id: str
    company_name: str
    industry: str
    competitive_position: Dict[str, Any]
    industry_benchmarks: Dict[str, Any]
    market_opportunity_analysis: Dict[str, Any]
    competitive_advantages: List[Dict[str, Any]]
    threat_analysis: Dict[str, Any]
    strategic_recommendations: List[str]
    competitive_score: float
    analysis_date: datetime

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


class ExecutiveDashboardResponse(BaseModel):
    """Executive dashboard response."""
    dashboard_period: str
    period_range: Dict[str, datetime]
    portfolio_summary: Dict[str, Any]
    portfolio_performance: Dict[str, Any]
    top_performers: List[Dict[str, Any]]
    revenue_analytics: Dict[str, Any]
    volume_analytics: Dict[str, Any]
    health_score_distribution: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    growth_opportunities: List[Dict[str, Any]]
    market_trends_impact: Dict[str, Any]
    kpi_trends: Dict[str, Any]
    generated_at: datetime

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)})


# ===================================================================
# Error Response Models
# ===================================================================

class EnterpriseError(BaseModel):
    """Standardized enterprise error response."""
    error_code: str
    error_message: str
    error_type: str
    partnership_id: Optional[str] = None
    tenant_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat()})


# ===================================================================
# Validation Response Models
# ===================================================================

class ValidationResult(BaseModel):
    """Result of data validation."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class HealthCheckResponse(BaseModel):
    """Health check response for enterprise services."""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    version_info: Optional[Dict[str, str]] = None

    model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.isoformat()})


# ===================================================================
# Configuration Models
# ===================================================================

class EnterpriseConfiguration(BaseModel):
    """Enterprise platform configuration."""
    max_partnerships_per_tenant: int = 50
    max_relocations_per_batch: int = 100
    default_session_timeout_hours: int = 8
    volume_tier_thresholds: Dict[str, int] = Field(default_factory=dict)
    supported_sso_providers: List[SSOProvider] = Field(default_factory=list)
    available_payment_terms: List[PaymentTerms] = Field(default_factory=list)
    default_revenue_share_percentage: Decimal = Decimal('0.30')
    analytics_retention_days: int = 730

    model_config = ConfigDict(json_encoders={
            Decimal: lambda v: float(v)})