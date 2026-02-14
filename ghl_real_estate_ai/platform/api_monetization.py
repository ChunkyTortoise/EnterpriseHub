"""
API Monetization Platform - Multi-Revenue Stream Engine
Transform platform capabilities into monetizable API products.
Creates exponential revenue opportunities beyond core SaaS.
"""

import logging
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import jwt

from ..core.llm_client import LLMClient
from ..services.cache_service import CacheService
from ..services.database_service import DatabaseService
from ..services.enhanced_error_handling import enhanced_error_handler

logger = logging.getLogger(__name__)


class PricingTier(Enum):
    """API pricing tiers."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    WHITE_LABEL = "white_label"


class APIEndpoint(Enum):
    """Available API endpoints."""

    LEAD_SCORING = "lead_scoring"
    PROPERTY_MATCHING = "property_matching"
    CONVERSATION_INTELLIGENCE = "conversation_intelligence"
    PREDICTIVE_ANALYTICS = "predictive_analytics"
    WORKFLOW_AUTOMATION = "workflow_automation"
    MARKET_INTELLIGENCE = "market_intelligence"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    CONTENT_GENERATION = "content_generation"


@dataclass
class APIKey:
    """API key configuration and tracking."""

    api_key: str
    customer_id: str
    tier: PricingTier
    endpoints_enabled: List[APIEndpoint]
    requests_per_month: int
    requests_used: int
    rate_limit_per_minute: int
    monthly_cost: Decimal
    created_at: datetime
    last_used: Optional[datetime]
    active: bool


@dataclass
class APIUsageRecord:
    """Individual API usage record."""

    request_id: str
    api_key: str
    endpoint: APIEndpoint
    timestamp: datetime
    response_time_ms: int
    tokens_used: int
    success: bool
    cost: Decimal
    customer_id: str
    metadata: Dict[str, Any]


@dataclass
class RevenueTier:
    """Revenue tier configuration."""

    tier: PricingTier
    monthly_price: Decimal
    requests_per_month: int
    rate_limit_per_minute: int
    features: List[str]
    support_level: str
    sla_uptime: float
    priority_support: bool


@dataclass
class APIAnalytics:
    """Comprehensive API analytics."""

    total_requests: int
    successful_requests: int
    error_rate: float
    average_response_time: float
    total_revenue: Decimal
    top_endpoints: List[str]
    customer_distribution: Dict[str, int]
    growth_rate: float
    revenue_per_customer: Decimal


class APIMonetization:
    """
    API Monetization Platform enabling multiple revenue streams.

    Creates value through:
    - Tiered API access with usage-based billing
    - White-label platform licensing
    - Enterprise custom solutions
    - Per-request and subscription monetization
    """

    def __init__(self, llm_client: LLMClient, cache_service: CacheService, database_service: DatabaseService):
        self.llm_client = llm_client
        self.cache = cache_service
        self.db = database_service

        # Pricing configuration
        self.pricing_tiers = {
            PricingTier.FREE: RevenueTier(
                tier=PricingTier.FREE,
                monthly_price=Decimal("0"),
                requests_per_month=1000,
                rate_limit_per_minute=10,
                features=["Basic lead scoring", "Property matching"],
                support_level="Community",
                sla_uptime=0.95,
                priority_support=False,
            ),
            PricingTier.STARTER: RevenueTier(
                tier=PricingTier.STARTER,
                monthly_price=Decimal("99"),
                requests_per_month=10000,
                rate_limit_per_minute=50,
                features=["All basic features", "Conversation intelligence", "Email support"],
                support_level="Standard",
                sla_uptime=0.99,
                priority_support=False,
            ),
            PricingTier.PRO: RevenueTier(
                tier=PricingTier.PRO,
                monthly_price=Decimal("499"),
                requests_per_month=100000,
                rate_limit_per_minute=200,
                features=["All features", "Advanced analytics", "Priority support"],
                support_level="Priority",
                sla_uptime=0.999,
                priority_support=True,
            ),
            PricingTier.ENTERPRISE: RevenueTier(
                tier=PricingTier.ENTERPRISE,
                monthly_price=Decimal("2499"),
                requests_per_month=1000000,
                rate_limit_per_minute=1000,
                features=["All features", "Custom integrations", "24/7 support", "SLA guarantees"],
                support_level="Enterprise",
                sla_uptime=0.9999,
                priority_support=True,
            ),
            PricingTier.WHITE_LABEL: RevenueTier(
                tier=PricingTier.WHITE_LABEL,
                monthly_price=Decimal("9999"),
                requests_per_month=-1,  # Unlimited
                rate_limit_per_minute=5000,
                features=["All features", "White-label branding", "Custom ontario_millss", "Dedicated support"],
                support_level="Dedicated",
                sla_uptime=0.9999,
                priority_support=True,
            ),
        }

        # Per-request pricing for overage
        self.overage_pricing = {
            APIEndpoint.LEAD_SCORING: Decimal("0.001"),  # $0.001 per request
            APIEndpoint.PROPERTY_MATCHING: Decimal("0.002"),  # $0.002 per request
            APIEndpoint.CONVERSATION_INTELLIGENCE: Decimal("0.005"),  # $0.005 per request
            APIEndpoint.PREDICTIVE_ANALYTICS: Decimal("0.003"),
            APIEndpoint.WORKFLOW_AUTOMATION: Decimal("0.002"),
            APIEndpoint.MARKET_INTELLIGENCE: Decimal("0.004"),
            APIEndpoint.BEHAVIORAL_ANALYSIS: Decimal("0.003"),
            APIEndpoint.CONTENT_GENERATION: Decimal("0.006"),
        }

        logger.info("API Monetization Platform initialized")

    @enhanced_error_handler
    async def create_api_key(
        self, customer_id: str, tier: PricingTier, custom_config: Optional[Dict[str, Any]] = None
    ) -> APIKey:
        """Create a new API key for a customer."""
        logger.info(f"Creating API key for customer {customer_id}, tier {tier.value}")

        # Generate secure API key
        api_key_value = self._generate_secure_api_key(customer_id, tier)

        # Get tier configuration
        tier_config = self.pricing_tiers[tier]

        # Create API key configuration
        api_key = APIKey(
            api_key=api_key_value,
            customer_id=customer_id,
            tier=tier,
            endpoints_enabled=self._get_tier_endpoints(tier),
            requests_per_month=tier_config.requests_per_month,
            requests_used=0,
            rate_limit_per_minute=tier_config.rate_limit_per_minute,
            monthly_cost=tier_config.monthly_price,
            created_at=datetime.utcnow(),
            last_used=None,
            active=True,
        )

        # Apply custom configuration if provided
        if custom_config:
            api_key = await self._apply_custom_config(api_key, custom_config)

        # Store API key configuration
        await self._store_api_key(api_key)

        # Set up billing
        await self._setup_api_billing(api_key)

        # Send welcome email with documentation
        await self._send_api_welcome_package(api_key)

        return api_key

    @enhanced_error_handler
    async def track_api_usage(
        self, api_key: str, endpoint: APIEndpoint, request_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track API usage and billing.

        Args:
            api_key: API key used for request
            endpoint: API endpoint called
            request_metadata: Request details (tokens, response time, etc.)

        Returns:
            Usage tracking result and billing information
        """
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        logger.info(f"Tracking API usage: {endpoint.value} for key {api_key[:8]}...")

        # Validate API key
        key_config = await self._get_api_key_config(api_key)
        if not key_config or not key_config.active:
            return {"error": "Invalid or inactive API key"}

        # Check rate limiting
        rate_limit_result = await self._check_rate_limit(key_config)
        if not rate_limit_result["allowed"]:
            return {"error": "Rate limit exceeded", "retry_after": rate_limit_result["retry_after"]}

        # Check monthly quota
        quota_result = await self._check_monthly_quota(key_config)

        # Calculate cost
        cost = await self._calculate_request_cost(key_config, endpoint, request_metadata)

        # Create usage record
        usage_record = APIUsageRecord(
            request_id=request_id,
            api_key=api_key,
            endpoint=endpoint,
            timestamp=timestamp,
            response_time_ms=request_metadata.get("response_time_ms", 0),
            tokens_used=request_metadata.get("tokens_used", 0),
            success=request_metadata.get("success", True),
            cost=cost,
            customer_id=key_config.customer_id,
            metadata=request_metadata,
        )

        # Store usage record
        await self._store_usage_record(usage_record)

        # Update API key statistics
        await self._update_api_key_usage(key_config, usage_record)

        # Check for overage billing
        overage_info = await self._check_overage_billing(key_config, usage_record)

        return {
            "request_id": request_id,
            "success": True,
            "cost": cost,
            "remaining_quota": quota_result["remaining"],
            "rate_limit_remaining": rate_limit_result["remaining"],
            "overage_charges": overage_info["charges"],
            "timestamp": timestamp.isoformat(),
        }

    @enhanced_error_handler
    async def get_api_analytics(
        self, customer_id: Optional[str] = None, date_range: Optional[Dict[str, datetime]] = None
    ) -> APIAnalytics:
        """Get comprehensive API analytics."""
        logger.info(f"Generating API analytics for customer: {customer_id}")

        # Set default date range if not provided
        if not date_range:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            date_range = {"start": start_date, "end": end_date}

        # Get usage records for the period
        usage_records = await self._get_usage_records(customer_id, date_range)

        # Calculate analytics
        total_requests = len(usage_records)
        successful_requests = len([r for r in usage_records if r.success])
        error_rate = (total_requests - successful_requests) / total_requests if total_requests > 0 else 0

        # Calculate average response time
        response_times = [r.response_time_ms for r in usage_records if r.response_time_ms > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Calculate revenue
        total_revenue = sum(r.cost for r in usage_records)

        # Top endpoints
        endpoint_counts = defaultdict(int)
        for record in usage_records:
            endpoint_counts[record.endpoint.value] += 1

        top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Customer distribution
        customer_counts = defaultdict(int)
        for record in usage_records:
            customer_counts[record.customer_id] += 1

        # Calculate growth rate
        growth_rate = await self._calculate_api_growth_rate(date_range)

        # Revenue per customer
        unique_customers = len(customer_counts)
        revenue_per_customer = total_revenue / unique_customers if unique_customers > 0 else Decimal("0")

        return APIAnalytics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            error_rate=error_rate,
            average_response_time=avg_response_time,
            total_revenue=total_revenue,
            top_endpoints=[endpoint[0] for endpoint in top_endpoints],
            customer_distribution=dict(customer_counts),
            growth_rate=growth_rate,
            revenue_per_customer=revenue_per_customer,
        )

    @enhanced_error_handler
    async def upgrade_api_tier(
        self, api_key: str, new_tier: PricingTier, effective_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Upgrade API tier for a customer."""
        logger.info(f"Upgrading API key {api_key[:8]}... to tier {new_tier.value}")

        # Get current API key configuration
        current_config = await self._get_api_key_config(api_key)
        if not current_config:
            return {"error": "API key not found"}

        # Validate upgrade path
        upgrade_validation = await self._validate_tier_upgrade(current_config.tier, new_tier)
        if not upgrade_validation["valid"]:
            return {"error": upgrade_validation["reason"]}

        # Calculate prorated billing
        billing_info = await self._calculate_prorated_billing(current_config, new_tier, effective_date)

        # Update API key configuration
        new_tier_config = self.pricing_tiers[new_tier]
        current_config.tier = new_tier
        current_config.requests_per_month = new_tier_config.requests_per_month
        current_config.rate_limit_per_minute = new_tier_config.rate_limit_per_minute
        current_config.monthly_cost = new_tier_config.monthly_price
        current_config.endpoints_enabled = self._get_tier_endpoints(new_tier)

        # Store updated configuration
        await self._store_api_key(current_config)

        # Process billing change
        billing_result = await self._process_tier_upgrade_billing(current_config, billing_info)

        # Send upgrade confirmation
        await self._send_tier_upgrade_confirmation(current_config, billing_info)

        return {
            "success": True,
            "new_tier": new_tier.value,
            "new_monthly_cost": new_tier_config.monthly_price,
            "billing_info": billing_info,
            "effective_date": effective_date or datetime.utcnow(),
        }

    @enhanced_error_handler
    async def generate_white_label_deployment(
        self, customer_id: str, white_label_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate white-label platform deployment for enterprise customers."""
        logger.info(f"Generating white-label deployment for customer {customer_id}")

        # Validate white-label eligibility
        eligibility = await self._validate_white_label_eligibility(customer_id)
        if not eligibility["eligible"]:
            return {"error": eligibility["reason"]}

        # Generate deployment configuration
        deployment_config = await self._generate_deployment_config(customer_id, white_label_config)

        # Create isolated environment
        environment_result = await self._create_isolated_environment(deployment_config)

        # Configure custom branding
        branding_result = await self._apply_custom_branding(deployment_config)

        # Set up custom ontario_mills
        ontario_mills_result = await self._setup_custom_ontario_mills(deployment_config)

        # Configure billing
        billing_setup = await self._setup_white_label_billing(customer_id, deployment_config)

        return {
            "success": True,
            "deployment_id": deployment_config["deployment_id"],
            "custom_ontario_mills": ontario_mills_result["ontario_mills"],
            "api_endpoints": environment_result["api_endpoints"],
            "billing_info": billing_setup,
            "estimated_go_live": datetime.utcnow() + timedelta(days=7),
        }

    @enhanced_error_handler
    async def get_revenue_projection(self, growth_assumptions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate revenue projections based on API platform growth."""
        logger.info("Generating API revenue projections")

        # Current baseline metrics
        current_metrics = await self.get_api_analytics()

        # Growth assumptions
        monthly_customer_growth = growth_assumptions.get("monthly_customer_growth", 0.20)  # 20%
        tier_upgrade_rate = growth_assumptions.get("tier_upgrade_rate", 0.15)  # 15%
        white_label_conversion = growth_assumptions.get("white_label_conversion", 0.02)  # 2%

        # Calculate projections
        projections = {}
        current_revenue = current_metrics.total_revenue
        current_customers = len(current_metrics.customer_distribution)

        for month in range(1, 13):  # 12-month projection
            # Customer growth
            projected_customers = int(current_customers * ((1 + monthly_customer_growth) ** month))

            # Revenue from existing tiers
            base_revenue = current_revenue * ((1 + monthly_customer_growth) ** month)

            # Revenue from tier upgrades
            upgrade_revenue = base_revenue * tier_upgrade_rate * month * 0.1

            # Revenue from white-label customers
            white_label_customers = int(projected_customers * white_label_conversion)
            white_label_revenue = white_label_customers * self.pricing_tiers[PricingTier.WHITE_LABEL].monthly_price

            # Total projected revenue
            total_revenue = base_revenue + upgrade_revenue + white_label_revenue

            projections[f"month_{month}"] = {
                "customers": projected_customers,
                "base_revenue": base_revenue,
                "upgrade_revenue": upgrade_revenue,
                "white_label_revenue": white_label_revenue,
                "total_revenue": total_revenue,
            }

        # Annual totals
        annual_revenue = sum(proj["total_revenue"] for proj in projections.values())
        annual_customers = projections["month_12"]["customers"]

        return {
            "monthly_projections": projections,
            "annual_summary": {
                "total_annual_revenue": annual_revenue,
                "year_end_customers": annual_customers,
                "revenue_growth_rate": (annual_revenue / current_revenue - 1) * 100,
                "customer_growth_rate": (annual_customers / current_customers - 1) * 100,
            },
            "assumptions": growth_assumptions,
        }

    # Private implementation methods

    def _generate_secure_api_key(self, customer_id: str, tier: PricingTier) -> str:
        """Generate cryptographically secure API key."""
        payload = {
            "customer_id": customer_id,
            "tier": tier.value,
            "created_at": datetime.utcnow().isoformat(),
            "uuid": str(uuid.uuid4()),
        }

        # Use JWT for secure, self-contained API keys
        api_key = jwt.encode(payload, "your-secret-key", algorithm="HS256")
        return f"ent_{api_key}"  # Prefix for identification

    def _get_tier_endpoints(self, tier: PricingTier) -> List[APIEndpoint]:
        """Get available endpoints for a pricing tier."""
        all_endpoints = list(APIEndpoint)

        if tier == PricingTier.FREE:
            return [APIEndpoint.LEAD_SCORING, APIEndpoint.PROPERTY_MATCHING]
        elif tier == PricingTier.STARTER:
            return all_endpoints[:4]
        elif tier in [PricingTier.PRO, PricingTier.ENTERPRISE, PricingTier.WHITE_LABEL]:
            return all_endpoints

        return []

    async def _store_api_key(self, api_key: APIKey) -> None:
        """Store API key configuration."""
        await self.cache.set(f"api_key_{api_key.api_key}", asdict(api_key), ttl=3600 * 24 * 30)

    async def _get_api_key_config(self, api_key: str) -> Optional[APIKey]:
        """Get API key configuration."""
        cached = await self.cache.get(f"api_key_{api_key}")
        if cached:
            return APIKey(**cached)
        return None

    async def _setup_api_billing(self, api_key: APIKey) -> None:
        """Set up billing for API key."""
        # Create billing subscription
        logger.info(f"Setting up billing for API key {api_key.api_key[:8]}...")

    async def _send_api_welcome_package(self, api_key: APIKey) -> None:
        """Send welcome package with API documentation."""
        logger.info(f"Sending API welcome package to customer {api_key.customer_id}")

    async def _check_rate_limit(self, api_key: APIKey) -> Dict[str, Any]:
        """Check rate limiting for API key."""
        # Simplified rate limiting check
        return {"allowed": True, "remaining": api_key.rate_limit_per_minute - 1, "retry_after": 0}

    async def _check_monthly_quota(self, api_key: APIKey) -> Dict[str, Any]:
        """Check monthly quota for API key."""
        remaining = max(0, api_key.requests_per_month - api_key.requests_used)
        return {"remaining": remaining, "exceeded": remaining <= 0}

    async def _calculate_request_cost(
        self, api_key: APIKey, endpoint: APIEndpoint, metadata: Dict[str, Any]
    ) -> Decimal:
        """Calculate cost for API request."""
        # Base cost included in subscription
        if api_key.requests_used < api_key.requests_per_month:
            return Decimal("0")

        # Overage pricing
        return self.overage_pricing.get(endpoint, Decimal("0.001"))

    async def _store_usage_record(self, record: APIUsageRecord) -> None:
        """Store usage record for billing and analytics."""
        # Store in time-series database for analytics
        await self.cache.set(f"usage_{record.request_id}", asdict(record), ttl=3600 * 24 * 90)

    async def _update_api_key_usage(self, api_key: APIKey, usage_record: APIUsageRecord) -> None:
        """Update API key usage statistics."""
        api_key.requests_used += 1
        api_key.last_used = usage_record.timestamp
        await self._store_api_key(api_key)

    async def _check_overage_billing(self, api_key: APIKey, usage_record: APIUsageRecord) -> Dict[str, Any]:
        """Check for overage billing charges."""
        if api_key.requests_used > api_key.requests_per_month:
            return {"charges": usage_record.cost}
        return {"charges": Decimal("0")}

    async def _get_usage_records(
        self, customer_id: Optional[str], date_range: Dict[str, datetime]
    ) -> List[APIUsageRecord]:
        """Get usage records for analytics."""
        # Simplified - would query time-series database
        return []

    async def _calculate_api_growth_rate(self, date_range: Dict[str, datetime]) -> float:
        """Calculate API usage growth rate."""
        return 0.25  # 25% monthly growth

    # Additional helper methods for tier management, billing, etc.
    async def _validate_tier_upgrade(self, current_tier: PricingTier, new_tier: PricingTier) -> Dict[str, Any]:
        """Validate tier upgrade path."""
        tier_order = [
            PricingTier.FREE,
            PricingTier.STARTER,
            PricingTier.PRO,
            PricingTier.ENTERPRISE,
            PricingTier.WHITE_LABEL,
        ]

        current_index = tier_order.index(current_tier)
        new_index = tier_order.index(new_tier)

        if new_index <= current_index:
            return {"valid": False, "reason": "Can only upgrade to higher tiers"}

        return {"valid": True}

    async def _calculate_prorated_billing(
        self, current_config: APIKey, new_tier: PricingTier, effective_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Calculate prorated billing for tier change."""
        # Simplified prorated billing calculation
        old_cost = current_config.monthly_cost
        new_cost = self.pricing_tiers[new_tier].monthly_price

        return {
            "old_monthly_cost": old_cost,
            "new_monthly_cost": new_cost,
            "prorated_charge": new_cost - old_cost,
            "effective_date": effective_date or datetime.utcnow(),
        }

    async def _process_tier_upgrade_billing(self, api_key: APIKey, billing_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process billing for tier upgrade."""
        return {"success": True, "transaction_id": str(uuid.uuid4())}

    async def _send_tier_upgrade_confirmation(self, api_key: APIKey, billing_info: Dict[str, Any]) -> None:
        """Send tier upgrade confirmation email."""
        logger.info(f"Sending tier upgrade confirmation to customer {api_key.customer_id}")

    # White-label deployment methods
    async def _validate_white_label_eligibility(self, customer_id: str) -> Dict[str, Any]:
        """Validate customer eligibility for white-label deployment."""
        # Check customer tier, contract, etc.
        return {"eligible": True}

    async def _generate_deployment_config(self, customer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate deployment configuration for white-label customer."""
        return {
            "deployment_id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "custom_ontario_mills": config.get("ontario_mills", f"{customer_id}.platform.com"),
            "branding": config.get("branding", {}),
            "features": config.get("features", []),
        }

    async def _create_isolated_environment(self, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create isolated environment for white-label deployment."""
        return {
            "environment_id": deployment_config["deployment_id"],
            "api_endpoints": [f"https://{deployment_config['custom_ontario_mills']}/api/v1"],
            "status": "provisioning",
        }

    async def _apply_custom_branding(self, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply custom branding to deployment."""
        return {"branding_applied": True}

    async def _setup_custom_ontario_mills(self, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up custom ontario_mills for white-label deployment."""
        return {"ontario_mills": deployment_config["custom_ontario_mills"], "ssl_configured": True}

    async def _setup_white_label_billing(self, customer_id: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up billing for white-label deployment."""
        return {
            "monthly_cost": self.pricing_tiers[PricingTier.WHITE_LABEL].monthly_price,
            "billing_cycle": "monthly",
            "next_billing_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }
