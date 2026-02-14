"""
White-Label Platform API Schemas
Pydantic models for white-label agency and ontario_mills management APIs
supporting the $500K ARR platform foundation.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator

# ===================================================================
# ENUM TYPES
# ===================================================================


class AgencyStatus(str, Enum):
    """Agency status values."""

    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class AgencyTier(str, Enum):
    """Agency tier values."""

    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Ontario MillsType(str, Enum):
    """Ontario Mills configuration types."""

    AGENCY = "agency"
    CLIENT = "client"
    CUSTOM = "custom"


class VerificationMethod(str, Enum):
    """Ontario Mills verification methods."""

    DNS = "dns"
    FILE = "file"
    EMAIL = "email"


class SSLProvider(str, Enum):
    """SSL certificate providers."""

    LETSENCRYPT = "letsencrypt"
    CLOUDFLARE = "cloudflare"
    AWS_ACM = "aws_acm"
    CUSTOM = "custom"


class DNSProvider(str, Enum):
    """DNS service providers."""

    CLOUDFLARE = "cloudflare"
    ROUTE53 = "route53"
    GOOGLE_CLOUD_DNS = "google_cloud_dns"
    AZURE_DNS = "azure_dns"


class AssetType(str, Enum):
    """Brand asset types."""

    LOGO = "logo"
    FAVICON = "favicon"
    BANNER = "banner"
    BACKGROUND = "background"
    FONT = "font"
    CSS = "css"
    IMAGE = "image"
    DOCUMENT = "document"


class ProcessingStatus(str, Enum):
    """Asset processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ===================================================================
# AGENCY MANAGEMENT SCHEMAS
# ===================================================================


class AgencyCreateRequest(BaseModel):
    """Request schema for creating an agency."""

    agency_name: str = Field(..., min_length=1, max_length=500)
    agency_slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    contact_email: EmailStr
    contract_value: Decimal = Field(..., gt=0, description="Annual contract value in USD")
    platform_fee_rate: Decimal = Field(0.20, ge=0, le=1, description="Platform fee as decimal (e.g., 0.20 for 20%)")
    tier: AgencyTier = AgencyTier.PROFESSIONAL
    contract_start_date: datetime
    contract_end_date: datetime
    auto_renewal: bool = True
    max_clients: int = Field(50, gt=0, le=1000)
    max_custom_ontario_millss: int = Field(10, gt=0, le=100)
    metadata: Dict[str, Any] = {}

    @field_validator("contract_end_date")
    @classmethod
    def validate_contract_dates(cls, v, info: ValidationInfo):
        if "contract_start_date" in info.data and v <= info.data["contract_start_date"]:
            raise ValueError("Contract end date must be after start date")
        return v

    @field_validator("agency_slug")
    @classmethod
    def validate_agency_slug(cls, v):
        if len(v) < 3:
            raise ValueError("Agency slug must be at least 3 characters")
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Agency slug cannot start or end with hyphen")
        return v


class AgencyUpdateRequest(BaseModel):
    """Request schema for updating an agency."""

    agency_name: Optional[str] = Field(None, min_length=1, max_length=500)
    contact_email: Optional[EmailStr] = None
    status: Optional[AgencyStatus] = None
    tier: Optional[AgencyTier] = None
    contract_end_date: Optional[datetime] = None
    auto_renewal: Optional[bool] = None
    max_clients: Optional[int] = Field(None, gt=0, le=1000)
    max_custom_ontario_millss: Optional[int] = Field(None, gt=0, le=100)
    metadata: Optional[Dict[str, Any]] = None


class AgencyResponse(BaseModel):
    """Response schema for agency information."""

    agency_id: str
    agency_name: str
    agency_slug: str
    contact_email: str
    contract_value: Decimal
    platform_fee_rate: Decimal
    status: AgencyStatus
    tier: AgencyTier

    contract_start_date: datetime
    contract_end_date: datetime
    auto_renewal: bool

    max_clients: int
    max_custom_ontario_millss: int

    onboarding_completed: bool
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AgencyStatsResponse(BaseModel):
    """Response schema for agency statistics."""

    agency_id: str
    agency_name: str
    client_count: int
    active_ontario_millss: int
    total_assets: int
    monthly_revenue: Decimal
    platform_fees: Decimal
    contract_status: str  # active, expiring, expired


# ===================================================================
# CLIENT MANAGEMENT SCHEMAS
# ===================================================================


class ClientCreateRequest(BaseModel):
    """Request schema for creating a client."""

    client_name: str = Field(..., min_length=1, max_length=500)
    client_slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    client_type: str = Field("real_estate", pattern=r"^(Union[real_estate, mortgage]|Union[insurance, general])$")
    monthly_fee: Decimal = Field(..., gt=0, description="Monthly fee in USD")
    monthly_volume_limit: int = Field(1000, gt=0, le=100000)

    # GHL Integration (optional)
    ghl_location_id: Optional[str] = None
    ghl_access_token: Optional[str] = None
    ghl_refresh_token: Optional[str] = None

    client_metadata: Dict[str, Any] = {}

    @field_validator("client_slug")
    @classmethod
    def validate_client_slug(cls, v):
        if len(v) < 3:
            raise ValueError("Client slug must be at least 3 characters")
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Client slug cannot start or end with hyphen")
        return v


class ClientUpdateRequest(BaseModel):
    """Request schema for updating a client."""

    client_name: Optional[str] = Field(None, min_length=1, max_length=500)
    client_type: Optional[str] = Field(None, pattern=r"^(Union[real_estate, mortgage]|Union[insurance, general])$")
    is_active: Optional[bool] = None
    monthly_fee: Optional[Decimal] = Field(None, gt=0)
    monthly_volume_limit: Optional[int] = Field(None, gt=0, le=100000)
    client_metadata: Optional[Dict[str, Any]] = None


class ClientResponse(BaseModel):
    """Response schema for client information."""

    client_id: str
    agency_id: str
    client_name: str
    client_slug: str
    client_type: str

    ghl_location_id: Optional[str]

    is_active: bool
    monthly_fee: Decimal
    monthly_volume_limit: int
    current_monthly_volume: int

    billing_status: str
    last_billing_date: Optional[datetime]
    next_billing_date: Optional[datetime]

    client_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# ===================================================================
# DOMAIN CONFIGURATION SCHEMAS
# ===================================================================


class DNSRecordSchema(BaseModel):
    """DNS record schema."""

    name: str = Field(..., min_length=1)
    type: str = Field(..., pattern=r"^(Union[A, AAAA]|Union[CNAME, TXT]|MX)$")
    value: str = Field(..., min_length=1)
    ttl: int = Field(300, gt=0, le=86400)
    priority: Optional[int] = Field(None, ge=0)


class Ontario MillsCreateRequest(BaseModel):
    """Request schema for creating a ontario_mills configuration."""

    ontario_mills_name: str = Field(..., min_length=4, max_length=255)
    ontario_mills_type: Ontario MillsType
    client_id: Optional[str] = None

    # DNS Configuration
    dns_provider: Optional[DNSProvider] = None

    # SSL Configuration
    ssl_enabled: bool = True
    ssl_provider: SSLProvider = SSLProvider.LETSENCRYPT
    ssl_auto_renew: bool = True

    # CDN Configuration
    cdn_enabled: bool = False
    cdn_provider: Optional[str] = None

    # Verification
    verification_method: VerificationMethod = VerificationMethod.DNS

    # Health Check
    health_check_url: Optional[str] = None

    configuration_metadata: Dict[str, Any] = {}

    @field_validator("ontario_mills_name")
    @classmethod
    def validate_ontario_mills_name(cls, v):
        import re

        ontario_mills_regex = re.compile(
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
        )
        if not ontario_mills_regex.match(v):
            raise ValueError("Invalid ontario_mills name format")
        return v.lower()

    @field_validator("client_id")
    @classmethod
    def validate_client_ontario_mills_type(cls, v, info: ValidationInfo):
        if "ontario_mills_type" in info.data:
            if info.data["ontario_mills_type"] == Ontario MillsType.CLIENT and not v:
                raise ValueError("Client ID required for client ontario_mills type")
            if info.data["ontario_mills_type"] == Ontario MillsType.AGENCY and v:
                raise ValueError("Client ID should not be provided for agency ontario_mills type")
        return v


class Ontario MillsUpdateRequest(BaseModel):
    """Request schema for updating a ontario_mills configuration."""

    ssl_enabled: Optional[bool] = None
    ssl_auto_renew: Optional[bool] = None
    cdn_enabled: Optional[bool] = None
    cdn_provider: Optional[str] = None
    health_check_url: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(Union[pending, active]|Union[error, disabled])$")
    configuration_metadata: Optional[Dict[str, Any]] = None


class Ontario MillsResponse(BaseModel):
    """Response schema for ontario_mills configuration."""

    ontario_mills_id: str
    agency_id: str
    client_id: Optional[str]

    ontario_mills_name: str
    subontario_mills: Optional[str]
    ontario_mills_type: Ontario MillsType

    # DNS Configuration
    dns_provider: Optional[DNSProvider]
    dns_zone_id: Optional[str]
    dns_records: List[DNSRecordSchema]

    # SSL Configuration
    ssl_enabled: bool
    ssl_provider: SSLProvider
    ssl_cert_status: str
    ssl_cert_expires_at: Optional[datetime]
    ssl_auto_renew: bool

    # CDN Configuration
    cdn_enabled: bool
    cdn_provider: Optional[str]
    cdn_distribution_id: Optional[str]
    cdn_endpoint: Optional[str]

    # Verification
    verification_token: str
    verification_status: str
    verification_method: VerificationMethod
    verified_at: Optional[datetime]

    # Status
    status: str
    health_check_url: Optional[str]
    last_health_check: Optional[datetime]
    health_status: str

    configuration_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class Ontario MillsHealthCheckResponse(BaseModel):
    """Response schema for ontario_mills health check."""

    ontario_mills_name: str
    overall_status: str
    checks: Dict[str, Dict[str, Any]]
    failed_checks: Optional[List[str]]
    timestamp: str


class DNSRecordsUpdateRequest(BaseModel):
    """Request schema for updating DNS records."""

    records: List[DNSRecordSchema] = Field(..., min_length=1, max_length=50)
    auto_configure: bool = True


# ===================================================================
# BRAND ASSET SCHEMAS
# ===================================================================


class AssetVariantSchema(BaseModel):
    """Asset variant schema."""

    variant_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    storage_path: str = ""
    storage_url: str = ""
    cdn_url: str = ""


class AssetUploadRequest(BaseModel):
    """Request schema for asset upload (multipart form data)."""

    asset_type: AssetType
    asset_name: str = Field(..., min_length=1, max_length=500)
    client_id: Optional[str] = None
    usage_context: Optional[str] = Field(None, max_length=100)
    auto_process: bool = True


class AssetResponse(BaseModel):
    """Response schema for brand asset."""

    asset_id: str
    agency_id: str
    client_id: Optional[str]

    asset_type: AssetType
    asset_name: str
    file_name: str
    file_extension: str
    mime_type: str

    storage_provider: str
    storage_bucket: Optional[str]
    storage_path: str
    storage_url: str
    cdn_url: Optional[str]
    cdn_cache_control: str

    file_size_bytes: int
    image_width: Optional[int]
    image_height: Optional[int]
    file_hash: Optional[str]

    processing_status: ProcessingStatus
    processed_variants: Dict[str, AssetVariantSchema]
    processing_error: Optional[str]

    is_active: bool
    usage_context: Optional[str]
    display_order: int

    optimized_size_bytes: Optional[int]
    optimization_ratio: Optional[float]
    webp_variant_url: Optional[str]
    avif_variant_url: Optional[str]

    asset_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AssetListResponse(BaseModel):
    """Response schema for asset list."""

    assets: List[AssetResponse]
    total_count: int
    total_size_bytes: int


class StorageOptimizationResponse(BaseModel):
    """Response schema for storage cost optimization analysis."""

    total_assets: int
    total_storage_bytes: int
    potential_savings_bytes: int
    storage_cost_estimate: Dict[str, float]
    recommendations: List[Dict[str, Any]]


# ===================================================================
# BRAND CONFIGURATION SCHEMAS
# ===================================================================


class BrandConfigCreateRequest(BaseModel):
    """Request schema for creating brand configuration."""

    brand_name: str = Field(..., min_length=1, max_length=500)
    client_id: Optional[str] = None

    # Asset IDs
    primary_logo_asset_id: Optional[str] = None
    secondary_logo_asset_id: Optional[str] = None
    favicon_asset_id: Optional[str] = None

    # Color palette (hex colors)
    primary_color: str = Field("#6D28D9", pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field("#4C1D95", pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str = Field("#10B981", pattern=r"^#[0-9A-Fa-f]{6}$")
    text_color: str = Field("#1F2937", pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: str = Field("#F9FAFB", pattern=r"^#[0-9A-Fa-f]{6}$")
    error_color: str = Field("#DC2626", pattern=r"^#[0-9A-Fa-f]{6}$")
    success_color: str = Field("#059669", pattern=r"^#[0-9A-Fa-f]{6}$")
    warning_color: str = Field("#D97706", pattern=r"^#[0-9A-Fa-f]{6}$")

    # Typography
    primary_font_family: str = Field("Inter, sans-serif", max_length=255)
    secondary_font_family: str = Field("system-ui", max_length=255)
    font_scale: Decimal = Field(Decimal("1.00"), ge=Decimal("0.5"), le=Decimal("2.0"))

    # Layout settings
    border_radius: str = Field("8px", max_length=10)
    box_shadow: str = Field("0 4px 6px rgba(0, 0, 0, 0.1)", max_length=255)
    animation_duration: str = Field("0.3s", max_length=10)
    container_max_width: str = Field("1200px", max_length=10)

    # Custom CSS
    custom_css: Optional[str] = Field(None, max_length=50000)
    css_variables: Dict[str, str] = {}

    # Feature toggles
    feature_flags: Dict[str, bool] = {}
    navigation_structure: List[Dict[str, Any]] = []
    footer_configuration: Dict[str, Any] = {}

    # SEO settings
    meta_title_template: Optional[str] = Field(None, max_length=255)
    meta_description_template: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = None
    og_image_asset_id: Optional[str] = None

    is_default: bool = False
    configuration_notes: Optional[str] = None
    brand_metadata: Dict[str, Any] = {}


class BrandConfigUpdateRequest(BaseModel):
    """Request schema for updating brand configuration."""

    brand_name: Optional[str] = Field(None, min_length=1, max_length=500)

    # Asset IDs
    primary_logo_asset_id: Optional[str] = None
    secondary_logo_asset_id: Optional[str] = None
    favicon_asset_id: Optional[str] = None

    # Color palette
    primary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    text_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

    # Typography
    primary_font_family: Optional[str] = Field(None, max_length=255)
    font_scale: Optional[Decimal] = Field(None, ge=Decimal("0.5"), le=Decimal("2.0"))

    # Custom CSS
    custom_css: Optional[str] = Field(None, max_length=50000)

    # Feature toggles
    feature_flags: Optional[Dict[str, bool]] = None

    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    brand_metadata: Optional[Dict[str, Any]] = None


class BrandConfigResponse(BaseModel):
    """Response schema for brand configuration."""

    config_id: str
    agency_id: str
    client_id: Optional[str]

    brand_name: str
    primary_logo_asset_id: Optional[str]
    secondary_logo_asset_id: Optional[str]
    favicon_asset_id: Optional[str]

    # Color palette
    primary_color: str
    secondary_color: str
    accent_color: str
    text_color: str
    background_color: str
    error_color: str
    success_color: str
    warning_color: str

    # Typography
    primary_font_family: str
    secondary_font_family: str
    font_scale: Decimal

    # Layout settings
    border_radius: str
    box_shadow: str
    animation_duration: str
    container_max_width: str

    # Custom CSS
    custom_css: Optional[str]
    css_variables: Dict[str, str]

    # Feature toggles
    feature_flags: Dict[str, bool]
    navigation_structure: List[Dict[str, Any]]
    footer_configuration: Dict[str, Any]

    # SEO settings
    meta_title_template: Optional[str]
    meta_description_template: Optional[str]
    meta_keywords: Optional[str]
    og_image_asset_id: Optional[str]

    is_active: bool
    is_default: bool
    version: str

    configuration_notes: Optional[str]
    brand_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# ===================================================================
# DEPLOYMENT CONFIGURATION SCHEMAS
# ===================================================================


class DeploymentCreateRequest(BaseModel):
    """Request schema for creating deployment configuration."""

    client_id: Optional[str] = None
    primary_ontario_mills_id: str
    brand_config_id: Optional[str] = None

    enabled_modules: List[str] = Field(default_factory=lambda: ["leads", "analytics", "messaging"])
    module_configurations: Dict[str, Any] = {}

    # Performance settings
    cache_ttl_seconds: int = Field(3600, gt=0, le=86400)
    rate_limit_requests_per_minute: int = Field(1000, gt=0, le=10000)
    max_concurrent_users: int = Field(100, gt=0, le=10000)

    # Security settings
    csrf_protection: bool = True
    cors_origins: List[str] = []
    api_key_required: bool = False
    ip_whitelist: List[str] = []

    # Monitoring
    analytics_enabled: bool = True
    error_tracking_enabled: bool = True
    performance_monitoring: bool = True

    deployment_notes: Optional[str] = None
    deployment_metadata: Dict[str, Any] = {}


class DeploymentUpdateRequest(BaseModel):
    """Request schema for updating deployment configuration."""

    enabled_modules: Optional[List[str]] = None
    module_configurations: Optional[Dict[str, Any]] = None
    cache_ttl_seconds: Optional[int] = Field(None, gt=0, le=86400)
    rate_limit_requests_per_minute: Optional[int] = Field(None, gt=0, le=10000)
    max_concurrent_users: Optional[int] = Field(None, gt=0, le=10000)

    csrf_protection: Optional[bool] = None
    cors_origins: Optional[List[str]] = None
    api_key_required: Optional[bool] = None

    analytics_enabled: Optional[bool] = None
    error_tracking_enabled: Optional[bool] = None
    performance_monitoring: Optional[bool] = None

    deployment_status: Optional[str] = Field(
        None, pattern=r"^(Union[pending, deploying]|Union[active, error]|disabled)$"
    )
    deployment_notes: Optional[str] = None
    deployment_metadata: Optional[Dict[str, Any]] = None


class DeploymentResponse(BaseModel):
    """Response schema for deployment configuration."""

    deployment_id: str
    agency_id: str
    client_id: Optional[str]

    primary_ontario_mills_id: str
    additional_ontario_mills_ids: List[str]
    brand_config_id: Optional[str]

    app_version: str
    deployment_environment: str

    enabled_modules: List[str]
    module_configurations: Dict[str, Any]

    cache_ttl_seconds: int
    rate_limit_requests_per_minute: int
    max_concurrent_users: int

    csrf_protection: bool
    cors_origins: List[str]
    api_key_required: bool
    ip_whitelist: List[str]

    analytics_enabled: bool
    error_tracking_enabled: bool
    performance_monitoring: bool

    deployment_status: str
    last_deployment_at: Optional[datetime]
    deployment_health: str

    deployment_notes: Optional[str]
    deployment_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# ===================================================================
# ANALYTICS AND REPORTING SCHEMAS
# ===================================================================


class PlatformAnalyticsResponse(BaseModel):
    """Response schema for platform analytics."""

    metric_id: str
    agency_id: str
    client_id: Optional[str]
    metric_type: str
    metric_name: str
    metric_value: Decimal
    metric_unit: Optional[str]
    time_bucket: datetime
    granularity: str
    segment_dimensions: Dict[str, Any]
    source_ontario_mills: Optional[str]
    analytics_metadata: Dict[str, Any]
    recorded_at: datetime


class AnalyticsQueryRequest(BaseModel):
    """Request schema for analytics queries."""

    agency_id: Optional[str] = None
    client_id: Optional[str] = None
    metric_types: List[str] = []
    start_date: datetime
    end_date: datetime
    granularity: str = Field("hour", pattern=r"^(Union[minute, hour]|Union[day, week]|month)$")
    group_by: List[str] = []
    filters: Dict[str, Any] = {}


class AnalyticsSummaryResponse(BaseModel):
    """Response schema for analytics summary."""

    total_requests: int
    unique_visitors: int
    avg_response_time_ms: float
    error_rate: float
    top_pages: List[Dict[str, Any]]
    traffic_by_hour: List[Dict[str, Any]]
    geographic_distribution: Dict[str, int]


# ===================================================================
# COMMON RESPONSE SCHEMAS
# ===================================================================


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Standard success response schema."""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: List[Any]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


# ===================================================================
# VALIDATION HELPERS
# ===================================================================


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = Field(1, gt=0)
    page_size: int = Field(20, gt=0, le=100)


class SortParams(BaseModel):
    """Sorting query parameters."""

    sort_by: str = "created_at"
    sort_order: str = Field("desc", pattern=r"^(Union[asc, desc])$")


class FilterParams(BaseModel):
    """Common filter parameters."""

    search: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
