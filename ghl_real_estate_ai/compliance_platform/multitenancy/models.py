"""
Multi-Tenant Organization Models

Enterprise-grade data structures for multi-tenant compliance platform supporting:
- Organization (tenant) management with subscription tiers
- User management with RBAC permissions
- Tenant context for request isolation
- Comprehensive audit logging
- Feature flags and usage metrics

Follows patterns from:
- ghl_real_estate_ai/security/rbac.py (RBAC patterns)
- ghl_real_estate_ai/compliance_platform/models/compliance_models.py (Pydantic patterns)
"""

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4
import re
import secrets
import hashlib

from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    field_validator,
    model_validator,
    ConfigDict,
)


# =============================================================================
# Enums
# =============================================================================


class SubscriptionTier(str, Enum):
    """Subscription tier levels with increasing capabilities"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

    @property
    def display_name(self) -> str:
        """Human-readable tier name"""
        return self.value.title()

    @property
    def is_paid(self) -> bool:
        """Check if this is a paid tier"""
        return self != SubscriptionTier.FREE

    @property
    def hierarchy_level(self) -> int:
        """Numeric level for tier comparison"""
        levels = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.STARTER: 1,
            SubscriptionTier.PROFESSIONAL: 2,
            SubscriptionTier.ENTERPRISE: 3,
        }
        return levels.get(self, 0)


class OrganizationStatus(str, Enum):
    """Organization lifecycle status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"
    PENDING_ACTIVATION = "pending_activation"

    @property
    def is_operational(self) -> bool:
        """Check if organization can perform normal operations"""
        return self in (OrganizationStatus.ACTIVE, OrganizationStatus.TRIAL)

    @property
    def allows_api_access(self) -> bool:
        """Check if API access is allowed in this status"""
        return self in (OrganizationStatus.ACTIVE, OrganizationStatus.TRIAL)


class UserRole(str, Enum):
    """User roles within an organization"""
    OWNER = "owner"
    ADMIN = "admin"
    COMPLIANCE_OFFICER = "compliance_officer"
    ANALYST = "analyst"
    VIEWER = "viewer"

    @property
    def display_name(self) -> str:
        """Human-readable role name"""
        return self.value.replace("_", " ").title()

    @property
    def hierarchy_level(self) -> int:
        """Hierarchy level for permission inheritance (higher = more privileged)"""
        levels = {
            UserRole.OWNER: 100,
            UserRole.ADMIN: 80,
            UserRole.COMPLIANCE_OFFICER: 60,
            UserRole.ANALYST: 40,
            UserRole.VIEWER: 20,
        }
        return levels.get(self, 0)


class Permission(str, Enum):
    """Fine-grained permissions for compliance platform operations"""

    # Model permissions
    MODEL_CREATE = "model:create"
    MODEL_READ = "model:read"
    MODEL_UPDATE = "model:update"
    MODEL_DELETE = "model:delete"

    # Assessment permissions
    ASSESSMENT_CREATE = "assessment:create"
    ASSESSMENT_READ = "assessment:read"

    # Violation permissions
    VIOLATION_READ = "violation:read"
    VIOLATION_ACKNOWLEDGE = "violation:acknowledge"
    VIOLATION_RESOLVE = "violation:resolve"

    # Report permissions
    REPORT_CREATE = "report:create"
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"

    # Admin permissions
    USER_MANAGE = "user:manage"
    SETTINGS_MANAGE = "settings:manage"
    BILLING_MANAGE = "billing:manage"
    AUDIT_READ = "audit:read"

    @property
    def resource(self) -> str:
        """Extract resource from permission (e.g., 'model' from 'model:create')"""
        return self.value.split(":")[0]

    @property
    def action(self) -> str:
        """Extract action from permission (e.g., 'create' from 'model:create')"""
        return self.value.split(":")[1]

    @classmethod
    def get_by_resource(cls, resource: str) -> List["Permission"]:
        """Get all permissions for a resource type"""
        return [p for p in cls if p.resource == resource]


# =============================================================================
# Permission Constants
# =============================================================================


# Role -> Permissions mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.OWNER: set(Permission),  # All permissions
    UserRole.ADMIN: {
        # Model permissions
        Permission.MODEL_CREATE,
        Permission.MODEL_READ,
        Permission.MODEL_UPDATE,
        Permission.MODEL_DELETE,
        # Assessment permissions
        Permission.ASSESSMENT_CREATE,
        Permission.ASSESSMENT_READ,
        # Violation permissions
        Permission.VIOLATION_READ,
        Permission.VIOLATION_ACKNOWLEDGE,
        Permission.VIOLATION_RESOLVE,
        # Report permissions
        Permission.REPORT_CREATE,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        # Admin permissions (except billing)
        Permission.USER_MANAGE,
        Permission.SETTINGS_MANAGE,
        Permission.AUDIT_READ,
    },
    UserRole.COMPLIANCE_OFFICER: {
        # Model permissions (no delete)
        Permission.MODEL_CREATE,
        Permission.MODEL_READ,
        Permission.MODEL_UPDATE,
        # Assessment permissions
        Permission.ASSESSMENT_CREATE,
        Permission.ASSESSMENT_READ,
        # Violation permissions (full)
        Permission.VIOLATION_READ,
        Permission.VIOLATION_ACKNOWLEDGE,
        Permission.VIOLATION_RESOLVE,
        # Report permissions
        Permission.REPORT_CREATE,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        # Audit access
        Permission.AUDIT_READ,
    },
    UserRole.ANALYST: {
        # Model permissions (read-only)
        Permission.MODEL_READ,
        # Assessment permissions (create + read)
        Permission.ASSESSMENT_CREATE,
        Permission.ASSESSMENT_READ,
        # Violation permissions (read + acknowledge)
        Permission.VIOLATION_READ,
        Permission.VIOLATION_ACKNOWLEDGE,
        # Report permissions (read only)
        Permission.REPORT_READ,
    },
    UserRole.VIEWER: {
        # Read-only permissions
        Permission.MODEL_READ,
        Permission.ASSESSMENT_READ,
        Permission.VIOLATION_READ,
        Permission.REPORT_READ,
    },
}


# =============================================================================
# Tier Configuration
# =============================================================================


# Subscription tier limits
TIER_LIMITS: Dict[SubscriptionTier, Dict[str, Any]] = {
    SubscriptionTier.FREE: {
        "max_models": 3,
        "max_users": 2,
        "max_assessments": 50,
        "features": ["basic_assessment"],
    },
    SubscriptionTier.STARTER: {
        "max_models": 10,
        "max_users": 5,
        "max_assessments": 200,
        "features": ["basic_assessment", "reports"],
    },
    SubscriptionTier.PROFESSIONAL: {
        "max_models": 50,
        "max_users": 20,
        "max_assessments": 1000,
        "features": ["basic_assessment", "reports", "ai_analysis", "webhooks"],
    },
    SubscriptionTier.ENTERPRISE: {
        "max_models": -1,  # Unlimited
        "max_users": -1,   # Unlimited
        "max_assessments": -1,  # Unlimited
        "features": ["all"],
    },
}


# Tier feature flags (expanded feature list)
TIER_FEATURES: Dict[SubscriptionTier, List[str]] = {
    SubscriptionTier.FREE: [
        "basic_assessment",
        "manual_model_registration",
        "basic_reports",
    ],
    SubscriptionTier.STARTER: [
        "basic_assessment",
        "manual_model_registration",
        "basic_reports",
        "detailed_reports",
        "email_notifications",
        "basic_api_access",
    ],
    SubscriptionTier.PROFESSIONAL: [
        "basic_assessment",
        "manual_model_registration",
        "basic_reports",
        "detailed_reports",
        "email_notifications",
        "basic_api_access",
        "ai_analysis",
        "custom_policies",
        "scheduled_reports",
        "webhooks",
        "slack_integration",
        "bulk_operations",
        "audit_log_export",
    ],
    SubscriptionTier.ENTERPRISE: [
        "all",  # Special marker for all features
        "sso_saml",
        "sso_oidc",
        "custom_branding",
        "dedicated_support",
        "custom_integrations",
        "advanced_analytics",
        "multi_region",
        "compliance_dashboard",
        "executive_reports",
        "priority_support",
        "custom_data_retention",
        "api_rate_limit_increase",
    ],
}


# =============================================================================
# Core Models
# =============================================================================


class Organization(BaseModel):
    """
    Tenant organization representing a customer account.

    Organizations are the top-level isolation boundary for multi-tenancy.
    All resources (models, assessments, users) are scoped to an organization.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    # Identity
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=50)
    domain: Optional[str] = Field(default=None, description="Primary domain for SSO")

    # Status
    status: OrganizationStatus = Field(default=OrganizationStatus.TRIAL)
    subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Configuration
    settings: Dict[str, Any] = Field(default_factory=dict)

    # Limits based on tier (can be overridden)
    max_models: int = Field(default=5)
    max_users: int = Field(default=3)
    max_assessments_per_month: int = Field(default=100)
    features_enabled: List[str] = Field(default_factory=list)

    # Branding (for white-label - Enterprise tier)
    logo_url: Optional[str] = Field(default=None)
    primary_color: Optional[str] = Field(default=None)
    custom_domain: Optional[str] = Field(default=None)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format - must be URL-safe"""
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", v):
            raise ValueError(
                "Slug must start and end with alphanumeric and contain only "
                "lowercase letters, numbers, and hyphens"
            )
        # Reserved slugs
        reserved = {"admin", "api", "www", "app", "dashboard", "login", "signup"}
        if v in reserved:
            raise ValueError(f"Slug '{v}' is reserved")
        return v

    @model_validator(mode="after")
    def apply_tier_defaults(self) -> "Organization":
        """Apply default limits and features based on subscription tier"""
        tier_limits = TIER_LIMITS.get(self.subscription_tier, {})
        tier_features = TIER_FEATURES.get(self.subscription_tier, [])

        # Apply limits if using defaults
        if self.max_models == 5:
            self.max_models = tier_limits.get("max_models", 5)
        if self.max_users == 3:
            self.max_users = tier_limits.get("max_users", 3)
        if self.max_assessments_per_month == 100:
            self.max_assessments_per_month = tier_limits.get("max_assessments", 100)

        # Apply features if not explicitly set
        if not self.features_enabled:
            self.features_enabled = tier_features.copy()

        return self

    def has_feature(self, feature: str) -> bool:
        """Check if organization has access to a feature"""
        if "all" in self.features_enabled:
            return True
        return feature in self.features_enabled

    def is_limit_reached(self, resource: str, current_count: int) -> bool:
        """Check if resource limit is reached (-1 means unlimited)"""
        limit_map = {
            "models": self.max_models,
            "users": self.max_users,
            "assessments": self.max_assessments_per_month,
        }
        max_value = limit_map.get(resource, -1)
        if max_value == -1:
            return False
        return current_count >= max_value

    def get_limit(self, resource: str) -> int:
        """Get limit for a specific resource"""
        limit_map = {
            "models": self.max_models,
            "users": self.max_users,
            "assessments": self.max_assessments_per_month,
        }
        return limit_map.get(resource, 0)

    def to_public_dict(self) -> Dict[str, Any]:
        """Return public-safe organization info (no internal data)"""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "status": self.status.value,
            "subscription_tier": self.subscription_tier.value,
            "features_enabled": self.features_enabled,
            "branding": {
                "logo_url": self.logo_url,
                "primary_color": self.primary_color,
            },
        }


class OrganizationUser(BaseModel):
    """
    User within an organization with role-based permissions.

    Users belong to exactly one organization and have a single role
    that determines their permissions within that organization.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    # Identity
    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)

    # Role and status
    role: UserRole
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = Field(default=None)

    # Security
    mfa_enabled: bool = Field(default=False)

    # Notification preferences
    email_notifications: bool = Field(default=True)
    slack_notifications: bool = Field(default=False)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower()

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        if not self.is_active:
            return False
        role_perms = ROLE_PERMISSIONS.get(self.role, set())
        return permission in role_perms

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions"""
        return all(self.has_permission(p) for p in permissions)

    def get_permissions(self) -> Set[Permission]:
        """Get all permissions for this user's role"""
        if not self.is_active:
            return set()
        return ROLE_PERMISSIONS.get(self.role, set())

    def can_manage_role(self, target_role: UserRole) -> bool:
        """Check if this user can manage users with the target role"""
        if not self.is_active:
            return False
        # Users can only manage roles below their hierarchy level
        return self.role.hierarchy_level > target_role.hierarchy_level

    def to_public_dict(self) -> Dict[str, Any]:
        """Return public-safe user info"""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role.value,
            "is_active": self.is_active,
            "mfa_enabled": self.mfa_enabled,
        }


class TenantContext(BaseModel):
    """
    Current tenant context for request processing.

    Passed through the request lifecycle to ensure all operations
    are properly scoped to the current tenant and user.
    """

    model_config = ConfigDict(frozen=True)  # Immutable once created

    # Organization context
    organization_id: str
    organization_name: str
    subscription_tier: SubscriptionTier

    # User context
    user_id: str
    user_role: UserRole
    permissions: frozenset[Permission]

    @classmethod
    def from_user_and_org(
        cls,
        user: OrganizationUser,
        org: Organization,
    ) -> "TenantContext":
        """Create context from user and organization"""
        return cls(
            organization_id=org.id,
            organization_name=org.name,
            subscription_tier=org.subscription_tier,
            user_id=user.id,
            user_role=user.role,
            permissions=frozenset(user.get_permissions()),
        )

    def has_permission(self, permission: Permission) -> bool:
        """Check if context has a permission"""
        return permission in self.permissions

    def require_permission(self, permission: Permission) -> None:
        """Raise exception if permission is missing"""
        if not self.has_permission(permission):
            raise PermissionError(
                f"Permission '{permission.value}' required for this operation"
            )


class AuditLogEntry(BaseModel):
    """
    Tenant-scoped audit log entry for compliance and security tracking.

    All significant operations are logged with full context for
    compliance reporting and security forensics.
    """

    # Identity
    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str

    # Actor
    user_id: str

    # Action
    action: str = Field(..., description="Action performed (e.g., 'model.create')")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: str = Field(..., description="ID of affected resource")

    # Timestamp
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Details
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = Field(default=None)

    @classmethod
    def from_context(
        cls,
        context: TenantContext,
        action: str,
        resource_type: str,
        resource_id: str,
        **kwargs: Any,
    ) -> "AuditLogEntry":
        """Create audit log entry from tenant context"""
        return cls(
            organization_id=context.organization_id,
            user_id=context.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs,
        )

    def to_compliance_format(self) -> Dict[str, Any]:
        """Format for compliance reporting"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "organization_id": self.organization_id,
            "actor": {
                "user_id": self.user_id,
                "ip_address": self.ip_address,
            },
            "action": {
                "type": self.action,
                "resource_type": self.resource_type,
                "resource_id": self.resource_id,
            },
            "details": self.details,
        }


# =============================================================================
# Supporting Models
# =============================================================================


class FeatureFlag(BaseModel):
    """Feature flag for organization-level feature control"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str
    feature_key: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    is_enabled: bool = Field(default=False)

    # Override settings
    enabled_by: Optional[str] = Field(default=None)
    enabled_at: Optional[datetime] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    reason: Optional[str] = Field(default=None)

    @property
    def is_active(self) -> bool:
        """Check if feature flag is currently active"""
        if not self.is_enabled:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True


class UsageMetrics(BaseModel):
    """Usage metrics for an organization's billing period"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str

    # Billing period
    period_start: datetime
    period_end: datetime

    # Resource counts
    models_count: int = Field(default=0, ge=0)
    users_count: int = Field(default=0, ge=0)
    assessments_count: int = Field(default=0, ge=0)
    reports_exported: int = Field(default=0, ge=0)
    api_calls: int = Field(default=0, ge=0)

    # Computed
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def check_limit(self, resource: str, tier: SubscriptionTier) -> Dict[str, Any]:
        """Check if a resource limit is reached"""
        limits = TIER_LIMITS.get(tier, {})
        max_value = limits.get(f"max_{resource}", -1)

        count_map = {
            "models": self.models_count,
            "users": self.users_count,
            "assessments": self.assessments_count,
        }
        current = count_map.get(resource, 0)

        return {
            "resource": resource,
            "current": current,
            "limit": max_value,
            "is_unlimited": max_value == -1,
            "is_reached": max_value != -1 and current >= max_value,
            "remaining": max_value - current if max_value != -1 else None,
            "percentage_used": (
                (current / max_value * 100) if max_value > 0 else 0
            ),
        }


class InviteToken(BaseModel):
    """Invitation token for adding users to an organization"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str
    token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    # Invite details
    email: EmailStr
    role: UserRole
    invited_by: str
    invited_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Expiry
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7)
    )

    # Status
    is_used: bool = Field(default=False)
    used_at: Optional[datetime] = Field(default=None)
    used_by_user_id: Optional[str] = Field(default=None)

    @property
    def is_valid(self) -> bool:
        """Check if invite is still valid"""
        if self.is_used:
            return False
        if datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    @property
    def days_until_expiry(self) -> int:
        """Days until invite expires"""
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)


class APIKey(BaseModel):
    """API key for programmatic access to organization resources"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str
    created_by: str

    # Key details
    name: str = Field(..., min_length=1, max_length=100)
    key_prefix: str = Field(default="")
    key_hash: str = Field(default="")
    last_four: str = Field(default="")

    # Permissions (subset of user permissions)
    permissions: Set[Permission] = Field(default_factory=set)

    # Rate limiting
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_per_day: int = Field(default=10000)

    # Lifecycle
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(default=None)
    last_used_at: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)

    # Usage tracking
    total_requests: int = Field(default=0, ge=0)

    @classmethod
    def generate_key(cls) -> tuple[str, str, str, str]:
        """
        Generate a new API key and return (full_key, key_prefix, key_hash, last_four).
        The full key should only be shown once at creation time.
        """
        full_key = f"cp_{secrets.token_urlsafe(32)}"
        key_prefix = full_key[:10]
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        last_four = full_key[-4:]

        return full_key, key_prefix, key_hash, last_four

    @property
    def is_valid(self) -> bool:
        """Check if API key is currently valid"""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def has_permission(self, permission: Permission) -> bool:
        """Check if API key has a specific permission"""
        if not self.is_valid:
            return False
        return permission in self.permissions

    @property
    def display_key(self) -> str:
        """Masked key for display (e.g., 'cp_abc...xyz1')"""
        return f"{self.key_prefix}...{self.last_four}"


# =============================================================================
# Helper Functions
# =============================================================================


def get_permissions_for_role(role: UserRole) -> Set[Permission]:
    """Get all permissions for a given role"""
    return ROLE_PERMISSIONS.get(role, set())


def get_tier_limits(tier: SubscriptionTier) -> Dict[str, Any]:
    """Get limits for a subscription tier"""
    return TIER_LIMITS.get(tier, {})


def get_tier_features(tier: SubscriptionTier) -> List[str]:
    """Get features for a subscription tier"""
    return TIER_FEATURES.get(tier, [])


def check_permission_hierarchy(
    actor_role: UserRole,
    target_role: UserRole,
) -> bool:
    """Check if actor can manage target based on role hierarchy"""
    return actor_role.hierarchy_level > target_role.hierarchy_level


def generate_organization_slug(name: str) -> str:
    """Generate a URL-friendly slug from organization name"""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    slug = slug.strip("-")
    if len(slug) > 50:
        slug = slug[:50].rstrip("-")
    return slug


# =============================================================================
# Aliases for compatibility
# =============================================================================

# Alias for backward compatibility with middleware module
TenantAuditLog = AuditLogEntry
