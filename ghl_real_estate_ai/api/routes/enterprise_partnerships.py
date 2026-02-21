"""
Enterprise Partnership API Routes

FastAPI routes for Fortune 500 corporate partnership management,
including SSO authentication, volume billing, and analytics.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ghl_real_estate_ai.api.enterprise.auth import (
    EnterpriseAuthService,
    SSOProvider,
    TenantRole,
    enterprise_auth_service,
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.corporate_billing_service import CorporateBillingError, CorporateBillingService
from ghl_real_estate_ai.services.corporate_partnership_service import (
    CorporatePartnershipError,
    CorporatePartnershipService,
)
from ghl_real_estate_ai.services.partnership_analytics import PartnershipAnalyticsError, PartnershipAnalyticsService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/enterprise", tags=["Enterprise Partnerships"])
security = HTTPBearer()


# ===================================================================
# Request/Response Models
# ===================================================================


class CreatePartnershipRequest(BaseModel):
    """Request model for creating corporate partnership."""

    company_name: str = Field(..., description="Company name")
    contact_email: str = Field(..., description="Primary contact email")
    contact_name: Optional[str] = Field(None, description="Contact person name")
    company_size: Optional[str] = Field(None, description="Company size category")
    industry: Optional[str] = Field(None, description="Industry sector")
    headquarters_location: Optional[str] = Field(None, description="HQ location")
    expected_volume: int = Field(..., ge=10, description="Expected annual relocation volume")
    preferred_tier: Optional[str] = Field(None, description="Preferred partnership tier")

    @field_validator("expected_volume")
    @classmethod
    def validate_volume(cls, v):
        if v < 10:
            raise ValueError("Minimum expected volume is 10 relocations per year")
        return v


class BulkRelocationRequest(BaseModel):
    """Request model for bulk employee relocations."""

    relocations: List[Dict[str, Any]] = Field(..., description="List of relocation requests")

    @field_validator("relocations")
    @classmethod
    def validate_relocations(cls, v):
        if len(v) > 100:
            raise ValueError("Maximum 100 relocations per batch")
        if not v:
            raise ValueError("At least one relocation required")
        return v


class CreateTenantRequest(BaseModel):
    """Request model for creating enterprise tenant."""

    company_name: str = Field(..., description="Company name")
    ontario_mills: str = Field(..., description="Company ontario_mills")
    sso_provider: SSOProvider = Field(..., description="SSO provider")
    sso_config: Dict[str, Any] = Field(default_factory=dict, description="SSO configuration")
    partnership_id: Optional[str] = Field(None, description="Associated partnership ID")
    admin_email: Optional[str] = Field(None, description="Admin email")
    max_users: int = Field(1000, ge=1, le=10000, description="Maximum users")
    require_mfa: bool = Field(True, description="Require multi-factor authentication")

    @field_validator("ontario_mills")
    @classmethod
    def validate_ontario_mills(cls, v):
        if "." not in v or " " in v:
            raise ValueError("Invalid ontario_mills format")
        return v.lower()


class CreateContractRequest(BaseModel):
    """Request model for creating enterprise contract."""

    partnership_id: str = Field(..., description="Partnership ID")
    expected_monthly_volume: int = Field(..., ge=10, description="Expected monthly volume")
    contract_term_months: int = Field(..., ge=6, le=60, description="Contract term in months")
    billing_contact_email: str = Field(..., description="Billing contact email")
    payment_terms: str = Field(..., description="Payment terms (NET30, NET15, etc.)")
    billing_frequency: str = Field("monthly", description="Billing frequency")
    auto_renewal: bool = Field(True, description="Auto-renewal enabled")
    custom_rate_per_transaction: Optional[Decimal] = Field(None, description="Custom transaction rate")

    @field_validator("payment_terms")
    @classmethod
    def validate_payment_terms(cls, v):
        valid_terms = ["NET30", "NET15", "NET60", "IMMEDIATE"]
        if v not in valid_terms:
            raise ValueError(f"Payment terms must be one of: {', '.join(valid_terms)}")
        return v


class PartnershipResponse(BaseModel):
    """Response model for partnership data."""

    partnership_id: str
    company_name: str
    tier: str
    status: str
    expected_annual_volume: int
    total_relocations: int
    total_revenue: Decimal
    created_at: datetime
    health_score: Optional[float] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat(), Decimal: lambda v: float(v)})


class AnalyticsResponse(BaseModel):
    """Response model for analytics data."""

    partnership_id: str
    analysis_period: Dict[str, Any]
    core_metrics: Dict[str, Any]
    health_score: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat(), Decimal: lambda v: float(v)})


# ===================================================================
# Service Dependencies
# ===================================================================


def get_partnership_service() -> CorporatePartnershipService:
    """Dependency to get partnership service."""
    return CorporatePartnershipService()


def get_billing_service() -> CorporateBillingService:
    """Dependency to get billing service."""
    return CorporateBillingService()


def get_analytics_service() -> PartnershipAnalyticsService:
    """Dependency to get analytics service."""
    return PartnershipAnalyticsService()


# ===================================================================
# Authentication & SSO Routes
# ===================================================================


@router.post("/tenants", status_code=201)
async def create_enterprise_tenant(
    request: CreateTenantRequest, auth_service: EnterpriseAuthService = Depends(lambda: enterprise_auth_service)
):
    """Create a new enterprise tenant with SSO configuration."""
    try:
        tenant_result = await auth_service.create_enterprise_tenant(request.dict())
        return {
            "success": True,
            "tenant_id": tenant_result["tenant_id"],
            "sso_setup_required": True,
            "next_steps": tenant_result["next_steps"],
        }
    except Exception as e:
        logger.error(f"Failed to create enterprise tenant: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")


@router.get("/auth/sso/login")
async def initiate_sso_login(
    ontario_mills: str = Query(..., description="Company ontario_mills"),
    redirect_uri: str = Query(..., description="Post-login redirect URI"),
    auth_service: EnterpriseAuthService = Depends(lambda: enterprise_auth_service),
):
    """Initiate SSO login flow for enterprise user."""
    # SECURITY FIX: Robustly validate redirect_uri against whitelist
    import os
    from urllib.parse import urlparse

    allowed_ontario_millss = [
        d.strip() for d in os.environ.get("ALLOWED_REDIRECT_DOMAINS", "http://localhost:3000").split(",") if d.strip()
    ]

    # Requirement: redirect_uri MUST be present and have a valid netloc
    parsed_uri = urlparse(redirect_uri)

    if not parsed_uri.netloc:
        logger.warning(f"SSO initiation blocked: Missing netloc in redirect URI {redirect_uri}")
        raise HTTPException(status_code=400, detail="Invalid redirect URI format")

    if parsed_uri.netloc not in [urlparse(d).netloc or d for d in allowed_ontario_millss]:
        logger.warning(f"SSO initiation blocked: Unauthorized netloc {parsed_uri.netloc} for URI {redirect_uri}")
        raise HTTPException(status_code=400, detail="Unauthorized redirect URI")

    try:
        sso_result = await auth_service.initiate_sso_login(ontario_mills, redirect_uri)
        return sso_result
    except Exception as e:
        logger.error(f"SSO initiation failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")


@router.post("/auth/sso/callback")
async def handle_sso_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State parameter"),
    auth_service: EnterpriseAuthService = Depends(lambda: enterprise_auth_service),
):
    """Handle SSO callback and complete authentication."""
    try:
        auth_result = await auth_service.handle_sso_callback(code, state)
        return auth_result
    except Exception as e:
        logger.error(f"SSO callback failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")


@router.get("/auth/me")
async def get_current_user(auth_data: Dict[str, Any] = Depends(enterprise_auth_service.get_current_enterprise_user)):
    """Get current authenticated user information."""
    return {
        "user": auth_data["user"],
        "tenant": {
            "tenant_id": auth_data["tenant"]["tenant_id"],
            "company_name": auth_data["tenant"]["company_name"],
            "tier": auth_data["tenant"].get("tier"),
        },
        "permissions": auth_data["permissions"],
    }


# ===================================================================
# Partnership Management Routes
# ===================================================================


@router.post("/partnerships", status_code=201)
async def create_partnership(
    request: CreatePartnershipRequest,
    partnership_service: CorporatePartnershipService = Depends(get_partnership_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("manage_partnerships")),
):
    """Create a new corporate partnership."""
    try:
        partnership_result = await partnership_service.create_corporate_partnership(request.dict())
        return partnership_result
    except CorporatePartnershipError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Partnership creation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/partnerships/{partnership_id}")
async def get_partnership(
    partnership_id: str = Path(..., description="Partnership ID"),
    partnership_service: CorporatePartnershipService = Depends(get_partnership_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.get_current_enterprise_user),
):
    """Get partnership details."""
    try:
        partnership_data = await partnership_service.get_partnership(partnership_id)
        if not partnership_data:
            raise HTTPException(status_code=404, detail="Partnership not found")

        return PartnershipResponse(**partnership_data)
    except Exception as e:
        logger.error(f"Failed to get partnership {partnership_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/partnerships/{partnership_id}/approve")
async def approve_partnership(
    partnership_id: str = Path(..., description="Partnership ID"),
    account_manager: str = Query(..., description="Account manager email"),
    contract_duration_months: int = Query(12, description="Contract duration in months"),
    partnership_service: CorporatePartnershipService = Depends(get_partnership_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("manage_partnerships")),
):
    """Approve and activate a corporate partnership."""
    try:
        approval_result = await partnership_service.approve_partnership(
            partnership_id, account_manager, contract_duration_months
        )
        return approval_result
    except CorporatePartnershipError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Partnership approval failed for {partnership_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ===================================================================
# Relocation Management Routes
# ===================================================================


@router.post("/partnerships/{partnership_id}/relocations/bulk")
async def process_bulk_relocations(
    partnership_id: str = Path(..., description="Partnership ID"),
    request: BulkRelocationRequest = ...,
    partnership_service: CorporatePartnershipService = Depends(get_partnership_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("manage_relocations")),
):
    """Process bulk employee relocation requests."""
    try:
        batch_result = await partnership_service.process_bulk_relocation_request(partnership_id, request.relocations)
        return batch_result
    except CorporatePartnershipError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Bulk relocation processing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/partnerships/{partnership_id}/relocations/{employee_email}")
async def track_relocation(
    partnership_id: str = Path(..., description="Partnership ID"),
    employee_email: str = Path(..., description="Employee email"),
    partnership_service: CorporatePartnershipService = Depends(get_partnership_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.get_current_enterprise_user),
):
    """Track progress of employee relocation."""
    try:
        tracking_result = await partnership_service.track_relocation_progress(partnership_id, employee_email)
        return tracking_result
    except Exception as e:
        logger.error(f"Relocation tracking failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ===================================================================
# Billing & Contract Routes
# ===================================================================


@router.post("/contracts", status_code=201)
async def create_enterprise_contract(
    request: CreateContractRequest,
    billing_service: CorporateBillingService = Depends(get_billing_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("manage_partnerships")),
):
    """Create enterprise contract with volume pricing."""
    try:
        contract_result = await billing_service.create_enterprise_contract(request.dict())
        return contract_result
    except CorporateBillingError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Contract creation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/contracts/{contract_id}/activate")
async def activate_contract(
    contract_id: str = Path(..., description="Contract ID"),
    billing_service: CorporateBillingService = Depends(get_billing_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("manage_partnerships")),
):
    """Activate enterprise contract and begin billing."""
    try:
        activation_result = await billing_service.activate_enterprise_contract(contract_id)
        return activation_result
    except CorporateBillingError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Contract activation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/contracts/{contract_id}/billing")
async def process_volume_billing(
    contract_id: str = Path(..., description="Contract ID"),
    billing_period_start: datetime = Query(..., description="Billing period start"),
    billing_period_end: datetime = Query(..., description="Billing period end"),
    billing_service: CorporateBillingService = Depends(get_billing_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("manage_partnerships")),
):
    """Process volume-based billing for enterprise contract."""
    try:
        billing_result = await billing_service.process_volume_billing(
            contract_id, billing_period_start, billing_period_end
        )
        return billing_result
    except CorporateBillingError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Volume billing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/contracts/{contract_id}/revenue-sharing")
async def calculate_revenue_sharing(
    contract_id: str = Path(..., description="Contract ID"),
    period_start: datetime = Query(..., description="Revenue period start"),
    period_end: datetime = Query(..., description="Revenue period end"),
    billing_service: CorporateBillingService = Depends(get_billing_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("view_financials")),
):
    """Calculate revenue sharing for corporate partnership."""
    try:
        revenue_sharing = await billing_service.calculate_revenue_sharing(contract_id, period_start, period_end)
        return revenue_sharing
    except CorporateBillingError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Revenue sharing calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/contracts/{contract_id}/billing-report")
async def get_billing_report(
    contract_id: str = Path(..., description="Contract ID"),
    report_period_months: int = Query(12, ge=1, le=24, description="Report period in months"),
    billing_service: CorporateBillingService = Depends(get_billing_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("view_financials")),
):
    """Generate enterprise billing report."""
    try:
        billing_report = await billing_service.generate_enterprise_billing_report(contract_id, report_period_months)
        return billing_report
    except CorporateBillingError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Billing report generation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ===================================================================
# Analytics & Reporting Routes
# ===================================================================


@router.get("/partnerships/{partnership_id}/analytics")
async def get_partnership_analytics(
    partnership_id: str = Path(..., description="Partnership ID"),
    analysis_period_days: int = Query(90, ge=7, le=365, description="Analysis period in days"),
    analytics_service: PartnershipAnalyticsService = Depends(get_analytics_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("view_analytics")),
):
    """Get comprehensive partnership performance analytics."""
    try:
        analytics_result = await analytics_service.analyze_partnership_performance(partnership_id, analysis_period_days)
        return AnalyticsResponse(**analytics_result)
    except PartnershipAnalyticsError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Analytics generation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/partnerships/{partnership_id}/analytics/relocation/{relocation_id}")
async def get_relocation_metrics(
    partnership_id: str = Path(..., description="Partnership ID"),
    relocation_id: str = Path(..., description="Relocation ID"),
    analytics_service: PartnershipAnalyticsService = Depends(get_analytics_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.get_current_enterprise_user),
):
    """Get detailed metrics for specific relocation."""
    try:
        relocation_metrics = await analytics_service.track_relocation_metrics(partnership_id, relocation_id)
        return relocation_metrics
    except PartnershipAnalyticsError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Relocation metrics failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/partnerships/{partnership_id}/revenue-attribution")
async def get_revenue_attribution(
    partnership_id: str = Path(..., description="Partnership ID"),
    attribution_period_months: int = Query(12, ge=1, le=24, description="Attribution period in months"),
    analytics_service: PartnershipAnalyticsService = Depends(get_analytics_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("view_financials")),
):
    """Get revenue attribution analysis for partnership."""
    try:
        attribution_result = await analytics_service.calculate_revenue_attribution(
            partnership_id, attribution_period_months
        )
        return attribution_result
    except PartnershipAnalyticsError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Revenue attribution failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/partnerships/{partnership_id}/forecast")
async def get_partnership_forecast(
    partnership_id: str = Path(..., description="Partnership ID"),
    forecast_months: int = Query(12, ge=3, le=24, description="Forecast horizon in months"),
    analytics_service: PartnershipAnalyticsService = Depends(get_analytics_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("view_analytics")),
):
    """Get predictive forecast for partnership performance."""
    try:
        forecast_result = await analytics_service.generate_partnership_forecast(partnership_id, forecast_months)
        return forecast_result
    except PartnershipAnalyticsError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Partnership forecast failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/partnerships/{partnership_id}/competitive-analysis")
async def get_competitive_analysis(
    partnership_id: str = Path(..., description="Partnership ID"),
    analytics_service: PartnershipAnalyticsService = Depends(get_analytics_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("view_analytics")),
):
    """Get competitive analysis for partnership positioning."""
    try:
        competitive_analysis = await analytics_service.generate_competitive_analysis(partnership_id)
        return competitive_analysis
    except PartnershipAnalyticsError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Competitive analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dashboard/executive")
async def get_executive_dashboard(
    time_period: str = Query("last_quarter", description="Time period for dashboard"),
    analytics_service: PartnershipAnalyticsService = Depends(get_analytics_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_permission("view_analytics")),
):
    """Get executive dashboard with portfolio-wide analytics."""
    try:
        dashboard_result = await analytics_service.generate_executive_dashboard(time_period)
        return dashboard_result
    except PartnershipAnalyticsError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Executive dashboard generation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ===================================================================
# User Management Routes (Admin Only)
# ===================================================================


@router.post("/tenants/{tenant_id}/users")
async def provision_enterprise_user(
    tenant_id: str = Path(..., description="Tenant ID"),
    user_email: str = Query(..., description="User email"),
    user_data: Dict[str, Any] = ...,
    auth_service: EnterpriseAuthService = Depends(lambda: enterprise_auth_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_tenant_role(TenantRole.TENANT_ADMIN)),
):
    """Provision new enterprise user with specific roles."""
    try:
        user_result = await auth_service.provision_enterprise_user(tenant_id, user_email, user_data)
        return {
            "success": True,
            "user_id": user_result["user_id"],
            "roles": user_result["roles"],
            "status": user_result["status"],
        }
    except Exception as e:
        logger.error(f"User provisioning failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")


@router.put("/tenants/{tenant_id}/users/{user_email}/roles")
async def update_user_roles(
    tenant_id: str = Path(..., description="Tenant ID"),
    user_email: str = Path(..., description="User email"),
    new_roles: List[str] = Query(..., description="New user roles"),
    auth_service: EnterpriseAuthService = Depends(lambda: enterprise_auth_service),
    auth_data: Dict[str, Any] = Depends(enterprise_auth_service.require_tenant_role(TenantRole.TENANT_ADMIN)),
):
    """Update enterprise user roles and permissions."""
    try:
        user_result = await auth_service.update_user_roles(tenant_id, user_email, new_roles)
        return {
            "success": True,
            "user_email": user_email,
            "updated_roles": user_result["roles"],
            "updated_permissions": user_result["permissions"],
        }
    except Exception as e:
        logger.error(f"User role update failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")


# ===================================================================
# Health Check Routes
# ===================================================================


@router.get("/health")
async def health_check():
    """Health check endpoint for enterprise services."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "services": {
            "partnership_service": "operational",
            "billing_service": "operational",
            "analytics_service": "operational",
            "auth_service": "operational",
        },
    }


@router.get("/version")
async def get_version():
    """Get enterprise platform version information."""
    return {
        "platform": "Jorge Enterprise Partnership Platform",
        "version": "1.0.0",
        "build": "enterprise-partnerships-v1",
        "api_version": "2025.1",
        "target_revenue": "$500K+ annual enhancement",
    }
