"""
Enterprise Tenant Management Service for High-Ticket Consulting Platform.

Provides database-backed multi-tenancy with enterprise features:
- Custom branding and white-label configuration
- Role-based access controls (RBAC)
- Tenant-specific feature flags and pricing tiers
- Usage analytics and billing integration
- Enterprise security and compliance

Replaces simple file-based tenant_service.py with production-grade multi-tenancy
for $25K-$100K consulting engagements.
"""

import asyncio
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional, Set

import asyncpg
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.database_service import DatabaseService, get_database

logger = get_logger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================


class TenantTier(Enum):
    """Tenant pricing tiers for consulting packages."""

    STARTER = "starter"  # $25K-$35K packages
    PROFESSIONAL = "professional"  # $50K-$75K packages
    ENTERPRISE = "enterprise"  # $75K-$100K+ packages
    CUSTOM = "custom"  # Custom consulting engagements


class TenantStatus(Enum):
    """Tenant status lifecycle."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    MIGRATING = "migrating"


class Permission(Enum):
    """RBAC permissions for enterprise tenants."""

    # AI & Intelligence Features
    AI_MULTI_AGENT_SWARM = "ai.multi_agent_swarm"
    AI_BEHAVIORAL_PROFILING = "ai.behavioral_profiling"
    AI_PREDICTIVE_ANALYTICS = "ai.predictive_analytics"
    AI_CUSTOM_MODELS = "ai.custom_models"

    # Platform Management
    TENANT_ADMIN = "tenant.admin"
    TENANT_CONFIG = "tenant.config"
    TENANT_BRANDING = "tenant.branding"
    TENANT_USERS = "tenant.users"

    # Data & Analytics
    DATA_EXPORT = "data.export"
    DATA_ANALYTICS = "data.analytics"
    DATA_API_ACCESS = "data.api_access"

    # Lead Management
    LEADS_VIEW = "leads.view"
    LEADS_EDIT = "leads.edit"
    LEADS_EXPORT = "leads.export"
    LEADS_ADVANCED_SCORING = "leads.advanced_scoring"

    # Campaign & Automation
    CAMPAIGNS_CREATE = "campaigns.create"
    CAMPAIGNS_EDIT = "campaigns.edit"
    CAMPAIGNS_ADVANCED = "campaigns.advanced"

    # White-Label Features
    WHITELABEL_BRANDING = "whitelabel.branding"
    WHITELABEL_DOMAIN = "whitelabel.domain"
    WHITELABEL_SUBDOMAIN = "whitelabel.subdomain"


class RoleType(Enum):
    """Pre-defined role types with permission sets."""

    SUPER_ADMIN = "super_admin"  # Full platform access
    TENANT_ADMIN = "tenant_admin"  # Full tenant access
    SALES_MANAGER = "sales_manager"  # Sales & lead management
    AGENT = "agent"  # Basic lead interaction
    ANALYST = "analyst"  # Data & reporting
    VIEWER = "viewer"  # Read-only access


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class BrandingConfig:
    """Tenant branding configuration for white-label deployments."""

    logo_url: Optional[str] = None
    primary_color: str = "#6D28D9"
    secondary_color: str = "#4C1D95"
    accent_color: str = "#10B981"
    company_name: str = "Real Estate AI"
    favicon_url: Optional[str] = None
    custom_css: Optional[str] = None
    footer_text: Optional[str] = None
    contact_email: Optional[str] = None
    support_phone: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeatureFlags:
    """Feature flags for tenant-specific capabilities."""

    # AI Features (tied to consulting tier)
    multi_agent_swarm: bool = False
    behavioral_profiling: bool = False
    predictive_analytics: bool = False
    custom_ai_models: bool = False
    real_time_consensus: bool = False

    # Platform Features
    white_label_branding: bool = False
    custom_domain: bool = False
    api_access: bool = False
    advanced_reporting: bool = False

    # Integration Features
    ghl_premium_features: bool = False
    apollo_enrichment: bool = False
    twilio_premium: bool = False
    sendgrid_premium: bool = False

    # Consulting Features
    consultant_collaboration: bool = False
    roi_attribution: bool = False
    success_measurement: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TenantConfig(BaseModel):
    """Complete tenant configuration for enterprise deployments."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str  # URL-friendly identifier
    status: TenantStatus = TenantStatus.ACTIVE
    tier: TenantTier = TenantTier.STARTER

    # Contact & Organization
    primary_contact_email: str
    organization_name: str
    billing_contact: Optional[str] = None

    # API Keys & Integrations
    anthropic_api_key: str
    ghl_api_key: str
    ghl_location_id: Optional[str] = None
    ghl_calendar_id: Optional[str] = None

    # Additional service keys
    apollo_api_key: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    sendgrid_api_key: Optional[str] = None

    # Configuration
    branding: BrandingConfig = Field(default_factory=BrandingConfig)
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)
    custom_config: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # Consulting engagement tracking
    engagement_start_date: Optional[datetime] = None
    engagement_end_date: Optional[datetime] = None
    consulting_package_value: Optional[float] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        """Ensure slug is URL-friendly."""
        import re

        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v

    model_config = ConfigDict(use_enum_values=True)


class TenantUser(BaseModel):
    """Tenant user with RBAC permissions."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    email: str
    first_name: str
    last_name: str
    role: RoleType = RoleType.VIEWER
    permissions: Set[Permission] = Field(default_factory=set)
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


# ============================================================================
# Enterprise Tenant Service
# ============================================================================


class EnterpriseTenantService:
    """
    Enterprise-grade tenant management service for high-ticket consulting platform.

    Features:
    - Database-backed tenant configuration with PostgreSQL
    - White-label branding and custom domain support
    - Role-based access controls (RBAC) with granular permissions
    - Tier-based feature flags ($25K/$50K/$100K consulting packages)
    - Usage tracking and billing integration
    - Enterprise security and audit logging
    - Real-time tenant analytics and monitoring
    """

    def __init__(self):
        """Initialize enterprise tenant service."""
        self.db: Optional[DatabaseService] = None
        self._initialized = False

        # Pre-defined role permission mappings
        self.role_permissions = {
            RoleType.SUPER_ADMIN: set(Permission),  # All permissions
            RoleType.TENANT_ADMIN: {
                Permission.TENANT_ADMIN,
                Permission.TENANT_CONFIG,
                Permission.TENANT_BRANDING,
                Permission.TENANT_USERS,
                Permission.DATA_EXPORT,
                Permission.DATA_ANALYTICS,
                Permission.LEADS_VIEW,
                Permission.LEADS_EDIT,
                Permission.LEADS_EXPORT,
                Permission.CAMPAIGNS_CREATE,
                Permission.CAMPAIGNS_EDIT,
                Permission.WHITELABEL_BRANDING,
                Permission.WHITELABEL_SUBDOMAIN,
            },
            RoleType.SALES_MANAGER: {
                Permission.LEADS_VIEW,
                Permission.LEADS_EDIT,
                Permission.LEADS_ADVANCED_SCORING,
                Permission.CAMPAIGNS_CREATE,
                Permission.CAMPAIGNS_EDIT,
                Permission.DATA_ANALYTICS,
            },
            RoleType.AGENT: {Permission.LEADS_VIEW, Permission.LEADS_EDIT},
            RoleType.ANALYST: {Permission.LEADS_VIEW, Permission.DATA_ANALYTICS, Permission.DATA_EXPORT},
            RoleType.VIEWER: {Permission.LEADS_VIEW},
        }

        # Tier-based feature mappings for consulting packages
        self.tier_features = {
            TenantTier.STARTER: FeatureFlags(
                # $25K-$35K: Basic AI + white-label
                behavioral_profiling=True,
                white_label_branding=True,
                ghl_premium_features=True,
                apollo_enrichment=True,
            ),
            TenantTier.PROFESSIONAL: FeatureFlags(
                # $50K-$75K: Multi-agent + advanced analytics
                multi_agent_swarm=True,
                behavioral_profiling=True,
                predictive_analytics=True,
                white_label_branding=True,
                custom_domain=True,
                api_access=True,
                advanced_reporting=True,
                ghl_premium_features=True,
                apollo_enrichment=True,
                twilio_premium=True,
                sendgrid_premium=True,
                consultant_collaboration=True,
                roi_attribution=True,
            ),
            TenantTier.ENTERPRISE: FeatureFlags(
                # $75K-$100K+: Full platform + custom AI
                multi_agent_swarm=True,
                behavioral_profiling=True,
                predictive_analytics=True,
                custom_ai_models=True,
                real_time_consensus=True,
                white_label_branding=True,
                custom_domain=True,
                api_access=True,
                advanced_reporting=True,
                ghl_premium_features=True,
                apollo_enrichment=True,
                twilio_premium=True,
                sendgrid_premium=True,
                consultant_collaboration=True,
                roi_attribution=True,
                success_measurement=True,
            ),
            TenantTier.CUSTOM: FeatureFlags(
                **{feature.name.lower(): True for feature in FeatureFlags.__dataclass_fields__.values()}
            ),
        }

    async def initialize(self) -> None:
        """Initialize enterprise tenant service with database setup."""
        if self._initialized:
            return

        try:
            self.db = await get_database()
            await self._create_tenant_tables()
            self._initialized = True
            logger.info("Enterprise tenant service initialized with database backend")

        except Exception as e:
            logger.error(f"Failed to initialize enterprise tenant service: {e}")
            raise

    async def _create_tenant_tables(self) -> None:
        """Create tenant management tables."""
        async with self.db.get_connection() as conn:
            # Tenants table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(200) NOT NULL,
                    slug VARCHAR(100) UNIQUE NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    tier VARCHAR(20) NOT NULL DEFAULT 'starter',
                    
                    -- Contact & Organization
                    primary_contact_email VARCHAR(255) NOT NULL,
                    organization_name VARCHAR(200) NOT NULL,
                    billing_contact VARCHAR(255),
                    
                    -- API Keys & Integrations (encrypted)
                    anthropic_api_key_encrypted TEXT NOT NULL,
                    ghl_api_key_encrypted TEXT NOT NULL,
                    ghl_location_id VARCHAR(100),
                    ghl_calendar_id VARCHAR(100),
                    apollo_api_key_encrypted TEXT,
                    twilio_account_sid_encrypted TEXT,
                    twilio_auth_token_encrypted TEXT,
                    sendgrid_api_key_encrypted TEXT,
                    
                    -- Configuration (JSONB)
                    branding_config JSONB DEFAULT '{}',
                    feature_flags JSONB DEFAULT '{}',
                    custom_config JSONB DEFAULT '{}',
                    
                    -- Metadata
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    created_by VARCHAR(100),
                    updated_by VARCHAR(100),
                    
                    -- Consulting engagement tracking
                    engagement_start_date DATE,
                    engagement_end_date DATE,
                    consulting_package_value DECIMAL(10,2),
                    
                    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'suspended', 'trial', 'migrating')),
                    CONSTRAINT valid_tier CHECK (tier IN ('starter', 'professional', 'enterprise', 'custom'))
                )
            """)

            # Tenant users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tenant_users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    email VARCHAR(255) NOT NULL,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
                    permissions TEXT[] DEFAULT '{}',
                    is_active BOOLEAN DEFAULT true,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    created_by VARCHAR(100),
                    
                    UNIQUE(tenant_id, email),
                    CONSTRAINT valid_role CHECK (role IN ('super_admin', 'tenant_admin', 'sales_manager', 'agent', 'analyst', 'viewer'))
                )
            """)

            # Tenant usage tracking
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tenant_usage (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    date DATE NOT NULL,
                    
                    -- AI Usage Metrics
                    ai_queries_count INTEGER DEFAULT 0,
                    multi_agent_queries INTEGER DEFAULT 0,
                    behavioral_analysis_runs INTEGER DEFAULT 0,
                    predictive_models_executed INTEGER DEFAULT 0,
                    
                    -- Platform Usage
                    api_calls_count INTEGER DEFAULT 0,
                    leads_processed INTEGER DEFAULT 0,
                    campaigns_executed INTEGER DEFAULT 0,
                    reports_generated INTEGER DEFAULT 0,
                    
                    -- Business Metrics
                    revenue_attributed DECIMAL(10,2) DEFAULT 0.00,
                    leads_converted INTEGER DEFAULT 0,
                    roi_calculated DECIMAL(8,4) DEFAULT 0.00,
                    
                    created_at TIMESTAMP DEFAULT NOW(),
                    
                    UNIQUE(tenant_id, date)
                )
            """)

            # Audit log for enterprise compliance
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tenant_audit_log (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
                    user_email VARCHAR(255),
                    action VARCHAR(100) NOT NULL,
                    resource_type VARCHAR(50),
                    resource_id VARCHAR(100),
                    details JSONB DEFAULT '{}',
                    ip_address INET,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    
                    -- Index for performance
                    INDEX idx_audit_tenant_date ON tenant_audit_log(tenant_id, created_at DESC),
                    INDEX idx_audit_action ON tenant_audit_log(action, created_at DESC)
                )
            """)

            # Create indexes for performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tenants_tier ON tenants(tier)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tenant_users_tenant_id ON tenant_users(tenant_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tenant_users_email ON tenant_users(email)")
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tenant_usage_tenant_date ON tenant_usage(tenant_id, date)"
            )

            logger.info("Created enterprise tenant management tables")

    # ============================================================================
    # Tenant Management
    # ============================================================================

    async def create_tenant(self, config: TenantConfig, created_by: str = None) -> str:
        """Create a new enterprise tenant with full configuration."""
        if not self._initialized:
            await self.initialize()

        try:
            async with self.db.transaction() as conn:
                # Set tier-based features
                if config.tier in self.tier_features:
                    config.feature_flags = self.tier_features[config.tier]

                tenant_id = str(uuid.uuid4())

                await conn.execute(
                    """
                    INSERT INTO tenants (
                        id, name, slug, status, tier,
                        primary_contact_email, organization_name, billing_contact,
                        anthropic_api_key_encrypted, ghl_api_key_encrypted,
                        ghl_location_id, ghl_calendar_id,
                        apollo_api_key_encrypted, twilio_account_sid_encrypted,
                        twilio_auth_token_encrypted, sendgrid_api_key_encrypted,
                        branding_config, feature_flags, custom_config,
                        created_by, engagement_start_date, engagement_end_date,
                        consulting_package_value
                    )
                    VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
                        $17, $18, $19, $20, $21, $22, $23
                    )
                """,
                    tenant_id,
                    config.name,
                    config.slug,
                    config.status.value,
                    config.tier.value,
                    config.primary_contact_email,
                    config.organization_name,
                    config.billing_contact,
                    self._encrypt_key(config.anthropic_api_key),
                    self._encrypt_key(config.ghl_api_key),
                    config.ghl_location_id,
                    config.ghl_calendar_id,
                    self._encrypt_key(config.apollo_api_key) if config.apollo_api_key else None,
                    self._encrypt_key(config.twilio_account_sid) if config.twilio_account_sid else None,
                    self._encrypt_key(config.twilio_auth_token) if config.twilio_auth_token else None,
                    self._encrypt_key(config.sendgrid_api_key) if config.sendgrid_api_key else None,
                    json.dumps(config.branding.to_dict()),
                    json.dumps(config.feature_flags.to_dict()),
                    json.dumps(config.custom_config),
                    created_by,
                    config.engagement_start_date,
                    config.engagement_end_date,
                    config.consulting_package_value,
                )

                # Create default admin user
                admin_user = TenantUser(
                    tenant_id=tenant_id,
                    email=config.primary_contact_email,
                    first_name="Admin",
                    last_name="User",
                    role=RoleType.TENANT_ADMIN,
                    created_by=created_by,
                )

                await self._create_tenant_user(conn, admin_user)

                await self._audit_log(
                    conn, tenant_id, created_by, "TENANT_CREATED", "tenant", tenant_id, {"tier": config.tier.value}
                )

                logger.info(f"Created enterprise tenant {tenant_id} for {config.organization_name}")
                return tenant_id

        except asyncpg.UniqueViolationError:
            raise ValueError(f"Tenant with slug '{config.slug}' already exists")
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            raise

    async def get_tenant_config(self, tenant_identifier: str) -> Optional[TenantConfig]:
        """Get tenant configuration by ID or slug."""
        if not self._initialized:
            await self.initialize()

        async with self.db.get_connection() as conn:
            # Try by ID first, then by slug
            where_clause = "id = $1" if self._is_uuid(tenant_identifier) else "slug = $1"

            row = await conn.fetchrow(
                f"""
                SELECT * FROM tenants WHERE {where_clause}
            """,
                tenant_identifier,
            )

            if not row:
                return None

            tenant_data = dict(row)

            return TenantConfig(
                id=str(tenant_data["id"]),
                name=tenant_data["name"],
                slug=tenant_data["slug"],
                status=TenantStatus(tenant_data["status"]),
                tier=TenantTier(tenant_data["tier"]),
                primary_contact_email=tenant_data["primary_contact_email"],
                organization_name=tenant_data["organization_name"],
                billing_contact=tenant_data["billing_contact"],
                anthropic_api_key=self._decrypt_key(tenant_data["anthropic_api_key_encrypted"]),
                ghl_api_key=self._decrypt_key(tenant_data["ghl_api_key_encrypted"]),
                ghl_location_id=tenant_data["ghl_location_id"],
                ghl_calendar_id=tenant_data["ghl_calendar_id"],
                apollo_api_key=self._decrypt_key(tenant_data["apollo_api_key_encrypted"])
                if tenant_data["apollo_api_key_encrypted"]
                else None,
                twilio_account_sid=self._decrypt_key(tenant_data["twilio_account_sid_encrypted"])
                if tenant_data["twilio_account_sid_encrypted"]
                else None,
                twilio_auth_token=self._decrypt_key(tenant_data["twilio_auth_token_encrypted"])
                if tenant_data["twilio_auth_token_encrypted"]
                else None,
                sendgrid_api_key=self._decrypt_key(tenant_data["sendgrid_api_key_encrypted"])
                if tenant_data["sendgrid_api_key_encrypted"]
                else None,
                branding=BrandingConfig(**tenant_data["branding_config"]),
                feature_flags=FeatureFlags(**tenant_data["feature_flags"]),
                custom_config=tenant_data["custom_config"],
                created_at=tenant_data["created_at"],
                updated_at=tenant_data["updated_at"],
                created_by=tenant_data["created_by"],
                updated_by=tenant_data["updated_by"],
                engagement_start_date=tenant_data["engagement_start_date"],
                engagement_end_date=tenant_data["engagement_end_date"],
                consulting_package_value=float(tenant_data["consulting_package_value"])
                if tenant_data["consulting_package_value"]
                else None,
            )

    async def update_tenant(self, tenant_id: str, updates: Dict[str, Any], updated_by: str = None) -> bool:
        """Update tenant configuration with audit logging."""
        if not self._initialized:
            await self.initialize()

        try:
            async with self.db.transaction() as conn:
                # Build dynamic update query
                set_clauses = ["updated_at = NOW()"]
                values = []
                param_count = 1

                for field, value in updates.items():
                    if field.endswith("_api_key") or field.endswith("_auth_token") or field.endswith("_account_sid"):
                        # Encrypt sensitive data
                        set_clauses.append(f"{field}_encrypted = ${param_count}")
                        values.append(self._encrypt_key(value))
                    elif field in ["branding", "feature_flags", "custom_config"]:
                        # JSON fields
                        set_clauses.append(f"{field}_config = ${param_count}")
                        if hasattr(value, "to_dict"):
                            values.append(json.dumps(value.to_dict()))
                        else:
                            values.append(json.dumps(value))
                    else:
                        set_clauses.append(f"{field} = ${param_count}")
                        values.append(value)
                    param_count += 1

                if updated_by:
                    set_clauses.append(f"updated_by = ${param_count}")
                    values.append(updated_by)
                    param_count += 1

                values.append(tenant_id)

                query = f"""
                    UPDATE tenants 
                    SET {", ".join(set_clauses)}
                    WHERE id = ${param_count}
                """

                result = await conn.execute(query, *values)
                rows_affected = int(result.split()[-1])

                if rows_affected > 0:
                    await self._audit_log(
                        conn,
                        tenant_id,
                        updated_by,
                        "TENANT_UPDATED",
                        "tenant",
                        tenant_id,
                        {"fields": list(updates.keys())},
                    )
                    logger.info(f"Updated tenant {tenant_id} with fields: {list(updates.keys())}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to update tenant {tenant_id}: {e}")
            raise

    # ============================================================================
    # User Management & RBAC
    # ============================================================================

    async def create_tenant_user(self, user: TenantUser, created_by: str = None) -> str:
        """Create a tenant user with role-based permissions."""
        if not self._initialized:
            await self.initialize()

        async with self.db.transaction() as conn:
            return await self._create_tenant_user(conn, user, created_by)

    async def _create_tenant_user(self, conn, user: TenantUser, created_by: str = None) -> str:
        """Internal method to create tenant user."""
        # Set role-based permissions
        if user.role in self.role_permissions:
            user.permissions = self.role_permissions[user.role]

        user_id = str(uuid.uuid4())

        await conn.execute(
            """
            INSERT INTO tenant_users (
                id, tenant_id, email, first_name, last_name, 
                role, permissions, is_active, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            user_id,
            user.tenant_id,
            user.email,
            user.first_name,
            user.last_name,
            user.role.value,
            [perm.value for perm in user.permissions],
            user.is_active,
            created_by or user.created_by,
        )

        await self._audit_log(
            conn,
            user.tenant_id,
            created_by,
            "USER_CREATED",
            "user",
            user_id,
            {"email": user.email, "role": user.role.value},
        )

        logger.info(f"Created tenant user {user.email} for tenant {user.tenant_id}")
        return user_id

    async def check_permission(self, user_email: str, tenant_id: str, permission: Permission) -> bool:
        """Check if user has specific permission within tenant."""
        if not self._initialized:
            await self.initialize()

        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT permissions, is_active FROM tenant_users 
                WHERE tenant_id = $1 AND email = $2
            """,
                tenant_id,
                user_email,
            )

            if not row or not row["is_active"]:
                return False

            user_permissions = {Permission(perm) for perm in row["permissions"]}
            return permission in user_permissions

    # ============================================================================
    # Usage Tracking & Analytics
    # ============================================================================

    async def track_usage(self, tenant_id: str, metrics: Dict[str, Any]) -> None:
        """Track tenant usage for billing and analytics."""
        if not self._initialized:
            await self.initialize()

        today = datetime.utcnow().date()

        async with self.db.transaction() as conn:
            # Insert or update usage metrics
            await conn.execute(
                """
                INSERT INTO tenant_usage (
                    tenant_id, date, ai_queries_count, multi_agent_queries,
                    behavioral_analysis_runs, predictive_models_executed,
                    api_calls_count, leads_processed, campaigns_executed,
                    reports_generated, revenue_attributed, leads_converted, roi_calculated
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (tenant_id, date)
                DO UPDATE SET
                    ai_queries_count = tenant_usage.ai_queries_count + EXCLUDED.ai_queries_count,
                    multi_agent_queries = tenant_usage.multi_agent_queries + EXCLUDED.multi_agent_queries,
                    behavioral_analysis_runs = tenant_usage.behavioral_analysis_runs + EXCLUDED.behavioral_analysis_runs,
                    predictive_models_executed = tenant_usage.predictive_models_executed + EXCLUDED.predictive_models_executed,
                    api_calls_count = tenant_usage.api_calls_count + EXCLUDED.api_calls_count,
                    leads_processed = tenant_usage.leads_processed + EXCLUDED.leads_processed,
                    campaigns_executed = tenant_usage.campaigns_executed + EXCLUDED.campaigns_executed,
                    reports_generated = tenant_usage.reports_generated + EXCLUDED.reports_generated,
                    revenue_attributed = tenant_usage.revenue_attributed + EXCLUDED.revenue_attributed,
                    leads_converted = tenant_usage.leads_converted + EXCLUDED.leads_converted,
                    roi_calculated = GREATEST(tenant_usage.roi_calculated, EXCLUDED.roi_calculated)
            """,
                tenant_id,
                today,
                metrics.get("ai_queries", 0),
                metrics.get("multi_agent_queries", 0),
                metrics.get("behavioral_analysis_runs", 0),
                metrics.get("predictive_models_executed", 0),
                metrics.get("api_calls", 0),
                metrics.get("leads_processed", 0),
                metrics.get("campaigns_executed", 0),
                metrics.get("reports_generated", 0),
                metrics.get("revenue_attributed", 0.0),
                metrics.get("leads_converted", 0),
                metrics.get("roi_calculated", 0.0),
            )

    async def get_tenant_analytics(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive tenant analytics for the consulting dashboard."""
        if not self._initialized:
            await self.initialize()

        start_date = datetime.utcnow().date() - timedelta(days=days)

        async with self.db.get_connection() as conn:
            # Get usage summary
            usage_summary = await conn.fetchrow(
                """
                SELECT
                    SUM(ai_queries_count) as total_ai_queries,
                    SUM(multi_agent_queries) as total_multi_agent,
                    SUM(behavioral_analysis_runs) as total_behavioral_analysis,
                    SUM(leads_processed) as total_leads_processed,
                    SUM(campaigns_executed) as total_campaigns,
                    SUM(revenue_attributed) as total_revenue_attributed,
                    SUM(leads_converted) as total_leads_converted,
                    AVG(roi_calculated) as avg_roi
                FROM tenant_usage
                WHERE tenant_id = $1 AND date >= $2
            """,
                tenant_id,
                start_date,
            )

            # Get daily trends
            daily_usage = await conn.fetch(
                """
                SELECT date, ai_queries_count, leads_processed, revenue_attributed
                FROM tenant_usage
                WHERE tenant_id = $1 AND date >= $2
                ORDER BY date
            """,
                tenant_id,
                start_date,
            )

            # Get tenant info
            tenant_info = await conn.fetchrow(
                """
                SELECT tier, consulting_package_value, engagement_start_date
                FROM tenants
                WHERE id = $1
            """,
                tenant_id,
            )

            return {
                "summary": dict(usage_summary) if usage_summary else {},
                "daily_trends": [dict(row) for row in daily_usage],
                "tenant_info": dict(tenant_info) if tenant_info else {},
                "period_days": days,
            }

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _encrypt_key(self, key: str) -> str:
        """Encrypt API keys for storage (placeholder - implement with proper encryption)."""
        if not key:
            return key
        # TODO: Implement proper encryption with a key management service
        # For now, using simple base64 encoding as placeholder
        import base64

        return base64.b64encode(key.encode()).decode()

    def _decrypt_key(self, encrypted_key: str) -> str:
        """Decrypt API keys (placeholder - implement with proper decryption)."""
        if not encrypted_key:
            return encrypted_key
        # TODO: Implement proper decryption
        import base64

        return base64.b64decode(encrypted_key.encode()).decode()

    def _is_uuid(self, value: str) -> bool:
        """Check if string is a valid UUID."""
        try:
            uuid.UUID(value)
            return True
        except (ValueError, TypeError):
            return False

    async def _audit_log(
        self,
        conn,
        tenant_id: str,
        user_email: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Dict[str, Any] = None,
    ):
        """Log audit event for enterprise compliance."""
        await conn.execute(
            """
            INSERT INTO tenant_audit_log (
                tenant_id, user_email, action, resource_type, 
                resource_id, details
            )
            VALUES ($1, $2, $3, $4, $5, $6)
        """,
            tenant_id,
            user_email,
            action,
            resource_type,
            resource_id,
            json.dumps(details or {}),
        )

    # ============================================================================
    # Compatibility with Legacy System
    # ============================================================================

    async def get_legacy_tenant_config(self, location_id: str) -> Dict[str, Any]:
        """Compatibility method for existing tenant_service.py interface."""
        tenant_config = await self.get_tenant_config(location_id)

        if tenant_config:
            return {
                "location_id": tenant_config.ghl_location_id or location_id,
                "anthropic_api_key": tenant_config.anthropic_api_key,
                "ghl_api_key": tenant_config.ghl_api_key,
                "ghl_calendar_id": tenant_config.ghl_calendar_id,
                "enterprise_features": tenant_config.feature_flags.to_dict(),
                "branding": tenant_config.branding.to_dict(),
            }

        # Fallback to legacy logic
        if location_id == settings.ghl_location_id:
            return {
                "location_id": settings.ghl_location_id,
                "anthropic_api_key": settings.anthropic_api_key,
                "ghl_api_key": settings.ghl_api_key,
            }

        if settings.ghl_agency_api_key:
            return {
                "location_id": location_id,
                "anthropic_api_key": settings.anthropic_api_key,
                "ghl_api_key": settings.ghl_agency_api_key,
                "is_agency_scoped": True,
            }

        return {}


# ============================================================================
# Service Factory & Singleton
# ============================================================================


class EnterpriseTenantManager:
    """Singleton manager for enterprise tenant service."""

    _instance = None
    _service = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_service(self) -> EnterpriseTenantService:
        """Get enterprise tenant service instance."""
        if self._service is None:
            self._service = EnterpriseTenantService()
            await self._service.initialize()
        return self._service


# Global enterprise tenant manager
tenant_manager = EnterpriseTenantManager()


async def get_enterprise_tenant_service() -> EnterpriseTenantService:
    """Get enterprise tenant service instance."""
    return await tenant_manager.get_service()


# ============================================================================
# Example Usage & Migration
# ============================================================================


async def migrate_from_legacy_tenants():
    """Migrate existing file-based tenants to enterprise database system."""
    from pathlib import Path

    from ghl_real_estate_ai.services.tenant_service import TenantService as LegacyTenantService

    enterprise_service = await get_enterprise_tenant_service()
    legacy_service = LegacyTenantService()

    # Find all existing tenant files
    tenants_dir = Path("data/tenants")
    if tenants_dir.exists():
        for tenant_file in tenants_dir.glob("*.json"):
            try:
                location_id = tenant_file.stem
                legacy_config = await legacy_service.get_tenant_config(location_id)

                if legacy_config:
                    # Create enterprise tenant config
                    enterprise_config = TenantConfig(
                        name=f"Tenant {location_id}",
                        slug=f"tenant-{location_id}",
                        tier=TenantTier.STARTER,  # Default to starter
                        primary_contact_email=legacy_config.get("email", "admin@example.com"),
                        organization_name=f"Organization {location_id}",
                        anthropic_api_key=legacy_config["anthropic_api_key"],
                        ghl_api_key=legacy_config["ghl_api_key"],
                        ghl_location_id=legacy_config["location_id"],
                        ghl_calendar_id=legacy_config.get("ghl_calendar_id"),
                    )

                    await enterprise_service.create_tenant(enterprise_config, "migration-script")
                    logger.info(f"Migrated tenant {location_id} to enterprise system")

            except Exception as e:
                logger.error(f"Failed to migrate tenant {location_id}: {e}")


if __name__ == "__main__":

    async def test_enterprise_tenant_service():
        """Test enterprise tenant service functionality."""
        service = await get_enterprise_tenant_service()

        # Test tenant creation
        config = TenantConfig(
            name="Acme Real Estate",
            slug="acme-real-estate",
            tier=TenantTier.PROFESSIONAL,
            primary_contact_email="admin@acme.com",
            organization_name="Acme Real Estate Corp",
            anthropic_api_key="test-key",
            ghl_api_key="test-ghl-key",
            consulting_package_value=65000.00,
        )

        tenant_id = await service.create_tenant(config, "test-system")
        print(f"Created tenant: {tenant_id}")

        # Test retrieval
        retrieved = await service.get_tenant_config(tenant_id)
        print(f"Retrieved tenant: {retrieved.organization_name}")

        # Test usage tracking
        await service.track_usage(tenant_id, {"ai_queries": 50, "leads_processed": 25, "revenue_attributed": 150000.00})

        # Test analytics
        analytics = await service.get_tenant_analytics(tenant_id)
        print(f"Analytics: {analytics}")

    # Run test
    asyncio.run(test_enterprise_tenant_service())
