"""
Multi-Tenant Organization Management Module

Provides enterprise-grade multi-tenancy support for the compliance platform:
- Organization and tenant management
- Role-based access control (RBAC) with fine-grained permissions
- Subscription tier management with feature gating
- Audit logging for compliance and security
- Tenant context isolation for request processing
- FastAPI middleware for automatic tenant isolation

Architecture:
- Organizations (tenants) contain users with specific roles
- Permissions are role-based with explicit mappings
- Subscription tiers control feature access and resource limits
- All operations are scoped to tenant context via middleware
"""

from .models import (
    # Enums
    SubscriptionTier,
    OrganizationStatus,
    UserRole,
    Permission,
    # Core Models
    Organization,
    OrganizationUser,
    TenantContext,
    AuditLogEntry,
    TenantAuditLog,  # Alias for AuditLogEntry
    # Supporting Models
    FeatureFlag,
    UsageMetrics,
    InviteToken,
    APIKey,
    # Constants
    ROLE_PERMISSIONS,
    TIER_LIMITS,
    TIER_FEATURES,
    # Helper Functions
    get_permissions_for_role,
    get_tier_limits,
    get_tier_features,
    check_permission_hierarchy,
    generate_organization_slug,
)

from .middleware import (
    # Context management
    clear_tenant_context,
    get_current_tenant,
    get_optional_tenant,
    set_tenant_context,
    # Middleware classes
    TenantMiddleware,
    TenantIsolation,
    TenantDataFilter,
    # Token utilities
    create_tenant_token,
    decode_tenant_token,
    # FastAPI dependencies
    get_current_org,
    get_current_user_id,
    get_user_permissions,
    require_permission,
    require_role,
    require_tier,
    # Singleton
    tenant_isolation,
)

__version__ = "1.0.0"
__all__ = [
    # Enums
    "SubscriptionTier",
    "OrganizationStatus",
    "UserRole",
    "Permission",
    # Core Models
    "Organization",
    "OrganizationUser",
    "TenantContext",
    "AuditLogEntry",
    "TenantAuditLog",
    # Supporting Models
    "FeatureFlag",
    "UsageMetrics",
    "InviteToken",
    "APIKey",
    # Constants
    "ROLE_PERMISSIONS",
    "TIER_LIMITS",
    "TIER_FEATURES",
    # Helper Functions
    "get_permissions_for_role",
    "get_tier_limits",
    "get_tier_features",
    "check_permission_hierarchy",
    "generate_organization_slug",
    # Context management
    "clear_tenant_context",
    "get_current_tenant",
    "get_optional_tenant",
    "set_tenant_context",
    # Middleware classes
    "TenantMiddleware",
    "TenantIsolation",
    "TenantDataFilter",
    # Token utilities
    "create_tenant_token",
    "decode_tenant_token",
    # FastAPI dependencies
    "get_current_org",
    "get_current_user_id",
    "get_user_permissions",
    "require_permission",
    "require_role",
    "require_tier",
    # Singleton
    "tenant_isolation",
]
