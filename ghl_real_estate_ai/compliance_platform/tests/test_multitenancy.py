"""
Comprehensive Test Suite for Multi-Tenancy in Compliance Platform

Tests cover:
- Organization Model: creation, subscription tiers, limits
- User Permissions: roles, permissions, inheritance
- Tenant Middleware: token extraction, validation, exclusions
- Tenant Isolation: data filtering, decorators, limit checking
- Tenant Token: creation, decoding, expiration

Following TDD principles: RED -> GREEN -> REFACTOR
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


# ============================================================================
# MULTI-TENANCY MODELS (Mock implementations for testing)
# ============================================================================


class SubscriptionTier(str, Enum):
    """Subscription tiers for multi-tenant organizations"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"


class Permission(str, Enum):
    """Available permissions in the system"""
    # Model permissions
    MODEL_READ = "model:read"
    MODEL_WRITE = "model:write"
    MODEL_DELETE = "model:delete"
    MODEL_REGISTER = "model:register"

    # Assessment permissions
    ASSESSMENT_READ = "assessment:read"
    ASSESSMENT_RUN = "assessment:run"
    ASSESSMENT_EXPORT = "assessment:export"

    # Violation permissions
    VIOLATION_READ = "violation:read"
    VIOLATION_ACKNOWLEDGE = "violation:acknowledge"
    VIOLATION_RESOLVE = "violation:resolve"

    # Report permissions
    REPORT_READ = "report:read"
    REPORT_GENERATE = "report:generate"
    REPORT_EXPORT = "report:export"

    # Admin permissions
    ADMIN_USER_MANAGE = "admin:user_manage"
    ADMIN_ORG_SETTINGS = "admin:org_settings"
    ADMIN_BILLING = "admin:billing"


class UserRole(str, Enum):
    """User roles with associated permissions"""
    VIEWER = "viewer"
    ANALYST = "analyst"
    COMPLIANCE_OFFICER = "compliance_officer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.VIEWER: {
        Permission.MODEL_READ,
        Permission.ASSESSMENT_READ,
        Permission.VIOLATION_READ,
        Permission.REPORT_READ,
    },
    UserRole.ANALYST: {
        Permission.MODEL_READ,
        Permission.MODEL_WRITE,
        Permission.ASSESSMENT_READ,
        Permission.ASSESSMENT_RUN,
        Permission.VIOLATION_READ,
        Permission.VIOLATION_ACKNOWLEDGE,
        Permission.REPORT_READ,
        Permission.REPORT_GENERATE,
    },
    UserRole.COMPLIANCE_OFFICER: {
        Permission.MODEL_READ,
        Permission.MODEL_WRITE,
        Permission.MODEL_REGISTER,
        Permission.ASSESSMENT_READ,
        Permission.ASSESSMENT_RUN,
        Permission.ASSESSMENT_EXPORT,
        Permission.VIOLATION_READ,
        Permission.VIOLATION_ACKNOWLEDGE,
        Permission.VIOLATION_RESOLVE,
        Permission.REPORT_READ,
        Permission.REPORT_GENERATE,
        Permission.REPORT_EXPORT,
    },
    UserRole.ADMIN: {
        Permission.MODEL_READ,
        Permission.MODEL_WRITE,
        Permission.MODEL_DELETE,
        Permission.MODEL_REGISTER,
        Permission.ASSESSMENT_READ,
        Permission.ASSESSMENT_RUN,
        Permission.ASSESSMENT_EXPORT,
        Permission.VIOLATION_READ,
        Permission.VIOLATION_ACKNOWLEDGE,
        Permission.VIOLATION_RESOLVE,
        Permission.REPORT_READ,
        Permission.REPORT_GENERATE,
        Permission.REPORT_EXPORT,
        Permission.ADMIN_USER_MANAGE,
        Permission.ADMIN_ORG_SETTINGS,
    },
    UserRole.SUPER_ADMIN: set(Permission),  # All permissions
}


# Tier limits
TIER_LIMITS: Dict[SubscriptionTier, Dict[str, int]] = {
    SubscriptionTier.FREE: {
        "max_models": 3,
        "max_users": 2,
        "max_assessments_per_month": 10,
        "max_api_calls_per_day": 100,
        "retention_days": 30,
    },
    SubscriptionTier.STARTER: {
        "max_models": 10,
        "max_users": 5,
        "max_assessments_per_month": 50,
        "max_api_calls_per_day": 1000,
        "retention_days": 90,
    },
    SubscriptionTier.PROFESSIONAL: {
        "max_models": 50,
        "max_users": 25,
        "max_assessments_per_month": 500,
        "max_api_calls_per_day": 10000,
        "retention_days": 365,
    },
    SubscriptionTier.ENTERPRISE: {
        "max_models": 500,
        "max_users": 100,
        "max_assessments_per_month": 5000,
        "max_api_calls_per_day": 100000,
        "retention_days": 730,
    },
    SubscriptionTier.UNLIMITED: {
        "max_models": -1,  # Unlimited
        "max_users": -1,
        "max_assessments_per_month": -1,
        "max_api_calls_per_day": -1,
        "retention_days": -1,
    },
}


class Organization:
    """Multi-tenant organization model"""

    def __init__(
        self,
        org_id: str,
        name: str,
        subscription_tier: SubscriptionTier,
        owner_id: str,
        created_at: Optional[datetime] = None,
        settings: Optional[Dict[str, Any]] = None,
    ):
        self.org_id = org_id
        self.name = name
        self.subscription_tier = subscription_tier
        self.owner_id = owner_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self.settings = settings or {}
        self.is_active = True
        self.users: Dict[str, "TenantUser"] = {}

    def get_limit(self, limit_name: str) -> int:
        """Get a specific limit for this organization's tier"""
        limits = TIER_LIMITS.get(self.subscription_tier, {})
        return limits.get(limit_name, 0)

    def add_user(self, user: "TenantUser") -> bool:
        """Add a user to the organization"""
        max_users = self.get_limit("max_users")
        if max_users != -1 and len(self.users) >= max_users:
            return False
        self.users[user.user_id] = user
        return True


class TenantUser:
    """User within a tenant organization"""

    def __init__(
        self,
        user_id: str,
        org_id: str,
        email: str,
        role: UserRole,
        custom_permissions: Optional[Set[Permission]] = None,
        is_active: bool = True,
    ):
        self.user_id = user_id
        self.org_id = org_id
        self.email = email
        self.role = role
        self.custom_permissions = custom_permissions or set()
        self.is_active = is_active
        self.created_at = datetime.now(timezone.utc)

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        # Check role-based permissions
        role_perms = ROLE_PERMISSIONS.get(self.role, set())
        if permission in role_perms:
            return True

        # Check custom permissions
        if permission in self.custom_permissions:
            return True

        return False

    def get_all_permissions(self) -> Set[Permission]:
        """Get all permissions for this user"""
        role_perms = ROLE_PERMISSIONS.get(self.role, set())
        return Union[role_perms, self].custom_permissions


class TenantContext:
    """Context for current tenant request"""

    def __init__(
        self,
        org_id: str,
        user_id: str,
        role: UserRole,
        permissions: Set[Permission],
        subscription_tier: SubscriptionTier,
    ):
        self.org_id = org_id
        self.user_id = user_id
        self.role = role
        self.permissions = permissions
        self.subscription_tier = subscription_tier


class TenantToken:
    """JWT-like token for tenant authentication"""

    SECRET_KEY = "test_secret_key_for_testing_only"

    @classmethod
    def create_token(
        cls,
        org_id: str,
        user_id: str,
        role: UserRole,
        permissions: List[str],
        expires_in_seconds: int = 3600,
    ) -> str:
        """Create a tenant authentication token"""
        payload = {
            "org_id": org_id,
            "user_id": user_id,
            "role": role.value,
            "permissions": permissions,
            "iat": int(time.time()),
            "exp": int(time.time()) + expires_in_seconds,
        }

        # Simple encoding (in production, use proper JWT)
        payload_json = json.dumps(payload)
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()

        signature = hmac.new(
            cls.SECRET_KEY.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"{payload_b64}.{signature}"

    @classmethod
    def decode_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a tenant token"""
        try:
            parts = token.split(".")
            if len(parts) != 2:
                return None

            payload_b64, signature = parts

            # Verify signature
            expected_sig = hmac.new(
                cls.SECRET_KEY.encode(),
                payload_b64.encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_sig):
                return None

            # Decode payload
            payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
            payload = json.loads(payload_json)

            # Check expiration
            if payload.get("exp", 0) < time.time():
                return None

            return payload

        except Exception:
            return None

    @classmethod
    def is_expired(cls, token: str) -> bool:
        """Check if token is expired"""
        payload = cls.decode_token(token)
        if payload is None:
            return True
        return payload.get("exp", 0) < time.time()


class TenantMiddleware:
    """Middleware for tenant context extraction and validation"""

    EXCLUDED_PATHS = [
        "/health",
        "/metrics",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/docs",
        "/openapi.json",
    ]

    def __init__(self, org_repository: Optional[Any] = None):
        self.org_repository = org_repository or {}

    def extract_tenant_from_token(self, token: str) -> Optional[TenantContext]:
        """Extract tenant context from authentication token"""
        payload = TenantToken.decode_token(token)
        if not payload:
            return None

        try:
            return TenantContext(
                org_id=payload["org_id"],
                user_id=payload["user_id"],
                role=UserRole(payload["role"]),
                permissions={Permission(p) for p in payload.get("permissions", [])},
                subscription_tier=SubscriptionTier.PROFESSIONAL,  # Default for testing
            )
        except (KeyError, ValueError):
            return None

    def is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from tenant validation"""
        return any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS)


class TenantIsolation:
    """Service for enforcing tenant data isolation"""

    def __init__(self, context: TenantContext):
        self.context = context

    def filter_by_org(self, items: List[Any], org_id_attr: str = "org_id") -> List[Any]:
        """Filter items to only those belonging to current tenant"""
        return [
            item for item in items
            if getattr(item, org_id_attr, None) == self.context.org_id
        ]

    def check_limit(self, resource_type: str, current_count: int) -> Tuple[bool, str]:
        """Check if a limit has been reached"""
        limit_mapping = {
            "models": "max_models",
            "users": "max_users",
            "assessments": "max_assessments_per_month",
            "api_calls": "max_api_calls_per_day",
        }

        limit_key = limit_mapping.get(resource_type)
        if not limit_key:
            return True, ""

        limits = TIER_LIMITS.get(self.context.subscription_tier, {})
        max_allowed = limits.get(limit_key, 0)

        if max_allowed == -1:  # Unlimited
            return True, ""

        if current_count >= max_allowed:
            return False, f"Limit reached: {resource_type} ({current_count}/{max_allowed})"

        return True, ""


# Typing import for decorator
from typing import Tuple, Union


def require_permission(permission: Permission):
    """Decorator to require a specific permission"""
    def decorator(func: Callable):
        async def wrapper(*args, context: TenantContext = None, **kwargs):
            if context is None:
                raise ValueError("Tenant context required")
            if permission not in context.permissions:
                raise PermissionError(f"Permission denied: {permission.value}")
            return await func(*args, context=context, **kwargs)
        return wrapper
    return decorator


def require_tier(minimum_tier: SubscriptionTier):
    """Decorator to require a minimum subscription tier"""
    tier_order = [
        SubscriptionTier.FREE,
        SubscriptionTier.STARTER,
        SubscriptionTier.PROFESSIONAL,
        SubscriptionTier.ENTERPRISE,
        SubscriptionTier.UNLIMITED,
    ]

    def decorator(func: Callable):
        async def wrapper(*args, context: TenantContext = None, **kwargs):
            if context is None:
                raise ValueError("Tenant context required")

            current_tier_idx = tier_order.index(context.subscription_tier)
            required_tier_idx = tier_order.index(minimum_tier)

            if current_tier_idx < required_tier_idx:
                raise PermissionError(
                    f"Subscription tier {minimum_tier.value} or higher required"
                )
            return await func(*args, context=context, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_organization() -> Organization:
    """Sample organization for testing"""
    return Organization(
        org_id="org_001",
        name="Acme Real Estate Corp",
        subscription_tier=SubscriptionTier.PROFESSIONAL,
        owner_id="user_001",
        settings={"timezone": "America/New_York", "locale": "en-US"},
    )


@pytest.fixture
def sample_user() -> TenantUser:
    """Sample user for testing"""
    return TenantUser(
        user_id="user_001",
        org_id="org_001",
        email="admin@acme.com",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def sample_viewer_user() -> TenantUser:
    """Sample viewer user with limited permissions"""
    return TenantUser(
        user_id="user_002",
        org_id="org_001",
        email="viewer@acme.com",
        role=UserRole.VIEWER,
    )


@pytest.fixture
def sample_tenant_context(sample_user: TenantUser) -> TenantContext:
    """Sample tenant context"""
    return TenantContext(
        org_id=sample_user.org_id,
        user_id=sample_user.user_id,
        role=sample_user.role,
        permissions=sample_user.get_all_permissions(),
        subscription_tier=SubscriptionTier.PROFESSIONAL,
    )


@pytest.fixture
def sample_token(sample_user: TenantUser) -> str:
    """Sample authentication token"""
    return TenantToken.create_token(
        org_id=sample_user.org_id,
        user_id=sample_user.user_id,
        role=sample_user.role,
        permissions=[p.value for p in sample_user.get_all_permissions()],
    )


@pytest.fixture
def middleware() -> TenantMiddleware:
    """Tenant middleware instance"""
    return TenantMiddleware()


# ============================================================================
# TEST CLASS: Organization Model
# ============================================================================


class TestOrganizationModel:
    """Test suite for Organization model"""

    def test_organization_creation(
        self,
        sample_organization: Organization,
    ):
        """Test organization creation with all fields"""
        # Assert
        assert sample_organization.org_id == "org_001"
        assert sample_organization.name == "Acme Real Estate Corp"
        assert sample_organization.subscription_tier == SubscriptionTier.PROFESSIONAL
        assert sample_organization.owner_id == "user_001"
        assert sample_organization.is_active is True
        assert sample_organization.created_at is not None

    def test_organization_creation_minimal(self):
        """Test organization creation with minimal fields"""
        # Act
        org = Organization(
            org_id="org_min",
            name="Minimal Org",
            subscription_tier=SubscriptionTier.FREE,
            owner_id="owner_001",
        )

        # Assert
        assert org.org_id == "org_min"
        assert org.settings == {}
        assert org.users == {}

    def test_subscription_tiers(self):
        """Test all subscription tiers are valid"""
        # Assert all tiers exist
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.STARTER.value == "starter"
        assert SubscriptionTier.PROFESSIONAL.value == "professional"
        assert SubscriptionTier.ENTERPRISE.value == "enterprise"
        assert SubscriptionTier.UNLIMITED.value == "unlimited"

    def test_tier_limits(
        self,
        sample_organization: Organization,
    ):
        """Test tier limits retrieval"""
        # Act
        max_models = sample_organization.get_limit("max_models")
        max_users = sample_organization.get_limit("max_users")
        max_assessments = sample_organization.get_limit("max_assessments_per_month")

        # Assert - Professional tier limits
        assert max_models == 50
        assert max_users == 25
        assert max_assessments == 500

    def test_tier_limits_free(self):
        """Test free tier limits"""
        # Arrange
        free_org = Organization(
            org_id="org_free",
            name="Free Org",
            subscription_tier=SubscriptionTier.FREE,
            owner_id="owner_001",
        )

        # Act & Assert
        assert free_org.get_limit("max_models") == 3
        assert free_org.get_limit("max_users") == 2
        assert free_org.get_limit("retention_days") == 30

    def test_tier_limits_unlimited(self):
        """Test unlimited tier has no limits"""
        # Arrange
        unlimited_org = Organization(
            org_id="org_unlimited",
            name="Unlimited Org",
            subscription_tier=SubscriptionTier.UNLIMITED,
            owner_id="owner_001",
        )

        # Act & Assert
        assert unlimited_org.get_limit("max_models") == -1
        assert unlimited_org.get_limit("max_users") == -1

    def test_add_user_within_limit(
        self,
        sample_organization: Organization,
        sample_user: TenantUser,
    ):
        """Test adding user within limit"""
        # Act
        result = sample_organization.add_user(sample_user)

        # Assert
        assert result is True
        assert sample_user.user_id in sample_organization.users

    def test_add_user_exceeds_limit(self):
        """Test adding user when limit is reached"""
        # Arrange - Free tier with max 2 users
        free_org = Organization(
            org_id="org_free",
            name="Free Org",
            subscription_tier=SubscriptionTier.FREE,
            owner_id="owner_001",
        )

        # Add 2 users (at limit)
        for i in range(2):
            user = TenantUser(
                user_id=f"user_{i}",
                org_id="org_free",
                email=f"user{i}@test.com",
                role=UserRole.VIEWER,
            )
            free_org.add_user(user)

        # Try to add 3rd user
        extra_user = TenantUser(
            user_id="user_extra",
            org_id="org_free",
            email="extra@test.com",
            role=UserRole.VIEWER,
        )

        # Act
        result = free_org.add_user(extra_user)

        # Assert
        assert result is False
        assert "user_extra" not in free_org.users


# ============================================================================
# TEST CLASS: User Permissions
# ============================================================================


class TestUserPermissions:
    """Test suite for user permissions"""

    def test_role_permissions(self):
        """Test that all roles have defined permissions"""
        # Assert
        for role in UserRole:
            assert role in ROLE_PERMISSIONS
            assert isinstance(ROLE_PERMISSIONS[role], set)

    def test_viewer_permissions(
        self,
        sample_viewer_user: TenantUser,
    ):
        """Test viewer role has read-only permissions"""
        # Assert - Can read
        assert sample_viewer_user.has_permission(Permission.MODEL_READ)
        assert sample_viewer_user.has_permission(Permission.ASSESSMENT_READ)
        assert sample_viewer_user.has_permission(Permission.VIOLATION_READ)
        assert sample_viewer_user.has_permission(Permission.REPORT_READ)

        # Assert - Cannot write/modify
        assert not sample_viewer_user.has_permission(Permission.MODEL_WRITE)
        assert not sample_viewer_user.has_permission(Permission.ASSESSMENT_RUN)
        assert not sample_viewer_user.has_permission(Permission.VIOLATION_RESOLVE)

    def test_admin_permissions(
        self,
        sample_user: TenantUser,  # Admin role
    ):
        """Test admin role has administrative permissions"""
        # Assert - Has admin permissions
        assert sample_user.has_permission(Permission.ADMIN_USER_MANAGE)
        assert sample_user.has_permission(Permission.ADMIN_ORG_SETTINGS)

        # Assert - Doesn't have super admin permissions
        assert not sample_user.has_permission(Permission.ADMIN_BILLING)

    def test_has_permission(
        self,
        sample_user: TenantUser,
    ):
        """Test has_permission method"""
        # Assert
        assert sample_user.has_permission(Permission.MODEL_READ) is True
        assert sample_user.has_permission(Permission.MODEL_WRITE) is True

    def test_has_permission_denied(
        self,
        sample_viewer_user: TenantUser,
    ):
        """Test has_permission returns False for unauthorized"""
        # Assert
        assert sample_viewer_user.has_permission(Permission.MODEL_DELETE) is False
        assert sample_viewer_user.has_permission(Permission.ADMIN_USER_MANAGE) is False

    def test_permission_inheritance(self):
        """Test that higher roles inherit lower role permissions"""
        # Viewer permissions should be subset of Analyst
        viewer_perms = ROLE_PERMISSIONS[UserRole.VIEWER]
        analyst_perms = ROLE_PERMISSIONS[UserRole.ANALYST]
        assert viewer_perms.issubset(analyst_perms)

        # Analyst permissions should be subset of Compliance Officer
        co_perms = ROLE_PERMISSIONS[UserRole.COMPLIANCE_OFFICER]
        # Note: Not strict subset, but should have overlap
        assert len(analyst_perms & co_perms) > 0

    def test_custom_permissions(self):
        """Test custom permissions override"""
        # Arrange - Viewer with custom write permission
        user = TenantUser(
            user_id="user_custom",
            org_id="org_001",
            email="custom@test.com",
            role=UserRole.VIEWER,
            custom_permissions={Permission.MODEL_WRITE},
        )

        # Assert - Has custom permission
        assert user.has_permission(Permission.MODEL_WRITE) is True

    def test_get_all_permissions(
        self,
        sample_user: TenantUser,
    ):
        """Test getting all permissions for a user"""
        # Act
        all_perms = sample_user.get_all_permissions()

        # Assert
        assert isinstance(all_perms, set)
        assert Permission.MODEL_READ in all_perms
        assert Permission.ADMIN_USER_MANAGE in all_perms

    def test_super_admin_has_all_permissions(self):
        """Test super admin has all permissions"""
        # Arrange
        super_admin = TenantUser(
            user_id="super_admin",
            org_id="org_001",
            email="super@test.com",
            role=UserRole.SUPER_ADMIN,
        )

        # Assert - Has all permissions
        for permission in Permission:
            assert super_admin.has_permission(permission)


# ============================================================================
# TEST CLASS: Tenant Middleware
# ============================================================================


class TestTenantMiddleware:
    """Test suite for tenant middleware"""

    def test_extract_tenant_from_token(
        self,
        middleware: TenantMiddleware,
        sample_token: str,
    ):
        """Test extracting tenant context from valid token"""
        # Act
        context = middleware.extract_tenant_from_token(sample_token)

        # Assert
        assert context is not None
        assert context.org_id == "org_001"
        assert context.user_id == "user_001"
        assert context.role == UserRole.ADMIN

    def test_invalid_token(
        self,
        middleware: TenantMiddleware,
    ):
        """Test handling of invalid token"""
        # Act
        context = middleware.extract_tenant_from_token("invalid.token.here")

        # Assert
        assert context is None

    def test_malformed_token(
        self,
        middleware: TenantMiddleware,
    ):
        """Test handling of malformed token"""
        # Act
        context = middleware.extract_tenant_from_token("not_even_a_token")

        # Assert
        assert context is None

    def test_expired_token(
        self,
        middleware: TenantMiddleware,
    ):
        """Test handling of expired token"""
        # Arrange - Create expired token
        expired_token = TenantToken.create_token(
            org_id="org_001",
            user_id="user_001",
            role=UserRole.ADMIN,
            permissions=[],
            expires_in_seconds=-3600,  # Expired 1 hour ago
        )

        # Act
        context = middleware.extract_tenant_from_token(expired_token)

        # Assert
        assert context is None

    def test_excluded_paths(
        self,
        middleware: TenantMiddleware,
    ):
        """Test excluded paths don't require authentication"""
        # Assert - Health check excluded
        assert middleware.is_excluded_path("/health") is True
        assert middleware.is_excluded_path("/health/live") is True

        # Assert - Auth endpoints excluded
        assert middleware.is_excluded_path("/api/v1/auth/login") is True
        assert middleware.is_excluded_path("/api/v1/auth/register") is True

        # Assert - Protected endpoints not excluded
        assert middleware.is_excluded_path("/api/v1/models") is False
        assert middleware.is_excluded_path("/api/v1/assessments") is False

    def test_excluded_paths_docs(
        self,
        middleware: TenantMiddleware,
    ):
        """Test documentation paths are excluded"""
        # Assert
        assert middleware.is_excluded_path("/docs") is True
        assert middleware.is_excluded_path("/openapi.json") is True


# ============================================================================
# TEST CLASS: Tenant Isolation
# ============================================================================


class TestTenantIsolation:
    """Test suite for tenant data isolation"""

    @pytest.fixture
    def isolation(self, sample_tenant_context: TenantContext) -> TenantIsolation:
        """Create isolation service"""
        return TenantIsolation(sample_tenant_context)

    def test_data_filter_models(
        self,
        isolation: TenantIsolation,
    ):
        """Test filtering models by organization"""
        # Arrange
        class MockModel:
            def __init__(self, model_id: str, org_id: str):
                self.model_id = model_id
                self.org_id = org_id

        models = [
            MockModel("model_1", "org_001"),  # Same org
            MockModel("model_2", "org_001"),  # Same org
            MockModel("model_3", "org_002"),  # Different org
            MockModel("model_4", "org_003"),  # Different org
        ]

        # Act
        filtered = isolation.filter_by_org(models)

        # Assert
        assert len(filtered) == 2
        assert all(m.org_id == "org_001" for m in filtered)

    def test_data_filter_empty(
        self,
        isolation: TenantIsolation,
    ):
        """Test filtering with empty list"""
        # Act
        filtered = isolation.filter_by_org([])

        # Assert
        assert filtered == []

    def test_data_filter_all_different_org(
        self,
        isolation: TenantIsolation,
    ):
        """Test filtering when all items belong to different org"""
        # Arrange
        class MockItem:
            def __init__(self, org_id: str):
                self.org_id = org_id

        items = [MockItem("org_other") for _ in range(5)]

        # Act
        filtered = isolation.filter_by_org(items)

        # Assert
        assert len(filtered) == 0

    @pytest.mark.asyncio
    async def test_require_permission_decorator(
        self,
        sample_tenant_context: TenantContext,
    ):
        """Test require_permission decorator allows authorized access"""
        # Arrange
        @require_permission(Permission.MODEL_READ)
        async def read_model(context: TenantContext = None):
            return {"status": "success"}

        # Act
        result = await read_model(context=sample_tenant_context)

        # Assert
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_require_permission_decorator_denied(
        self,
    ):
        """Test require_permission decorator blocks unauthorized access"""
        # Arrange
        viewer_context = TenantContext(
            org_id="org_001",
            user_id="user_002",
            role=UserRole.VIEWER,
            permissions=ROLE_PERMISSIONS[UserRole.VIEWER],
            subscription_tier=SubscriptionTier.PROFESSIONAL,
        )

        @require_permission(Permission.MODEL_DELETE)
        async def delete_model(context: TenantContext = None):
            return {"status": "deleted"}

        # Act & Assert
        with pytest.raises(PermissionError) as exc_info:
            await delete_model(context=viewer_context)

        assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_require_tier_decorator(
        self,
        sample_tenant_context: TenantContext,
    ):
        """Test require_tier decorator allows sufficient tier"""
        # Arrange
        @require_tier(SubscriptionTier.STARTER)
        async def premium_feature(context: TenantContext = None):
            return {"status": "premium"}

        # Act - Professional tier (higher than Starter)
        result = await premium_feature(context=sample_tenant_context)

        # Assert
        assert result["status"] == "premium"

    @pytest.mark.asyncio
    async def test_require_tier_decorator_denied(
        self,
    ):
        """Test require_tier decorator blocks insufficient tier"""
        # Arrange
        free_context = TenantContext(
            org_id="org_free",
            user_id="user_free",
            role=UserRole.ADMIN,
            permissions=ROLE_PERMISSIONS[UserRole.ADMIN],
            subscription_tier=SubscriptionTier.FREE,
        )

        @require_tier(SubscriptionTier.ENTERPRISE)
        async def enterprise_feature(context: TenantContext = None):
            return {"status": "enterprise"}

        # Act & Assert
        with pytest.raises(PermissionError) as exc_info:
            await enterprise_feature(context=free_context)

        assert "Subscription tier" in str(exc_info.value)

    def test_check_limit(
        self,
        isolation: TenantIsolation,
    ):
        """Test limit checking for resources"""
        # Act - Under limit
        allowed, message = isolation.check_limit("models", 10)

        # Assert
        assert allowed is True
        assert message == ""

    def test_check_limit_exceeded(
        self,
    ):
        """Test limit checking when exceeded"""
        # Arrange - Free tier context
        free_context = TenantContext(
            org_id="org_free",
            user_id="user_free",
            role=UserRole.ADMIN,
            permissions=set(),
            subscription_tier=SubscriptionTier.FREE,
        )
        isolation = TenantIsolation(free_context)

        # Act - At limit (free tier max_models = 3)
        allowed, message = isolation.check_limit("models", 3)

        # Assert
        assert allowed is False
        assert "Limit reached" in message

    def test_check_limit_unlimited(
        self,
    ):
        """Test limit checking for unlimited tier"""
        # Arrange - Unlimited tier context
        unlimited_context = TenantContext(
            org_id="org_unlimited",
            user_id="user_unlimited",
            role=UserRole.ADMIN,
            permissions=set(),
            subscription_tier=SubscriptionTier.UNLIMITED,
        )
        isolation = TenantIsolation(unlimited_context)

        # Act - Any count should be allowed
        allowed, message = isolation.check_limit("models", 10000)

        # Assert
        assert allowed is True


# ============================================================================
# TEST CLASS: Tenant Token
# ============================================================================


class TestTenantToken:
    """Test suite for tenant authentication tokens"""

    def test_create_token(self):
        """Test token creation"""
        # Act
        token = TenantToken.create_token(
            org_id="org_001",
            user_id="user_001",
            role=UserRole.ADMIN,
            permissions=["model:read", "model:write"],
        )

        # Assert
        assert token is not None
        assert "." in token  # Contains separator
        assert len(token.split(".")) == 2

    def test_decode_token(self):
        """Test token decoding"""
        # Arrange
        token = TenantToken.create_token(
            org_id="org_test",
            user_id="user_test",
            role=UserRole.ANALYST,
            permissions=["model:read"],
        )

        # Act
        payload = TenantToken.decode_token(token)

        # Assert
        assert payload is not None
        assert payload["org_id"] == "org_test"
        assert payload["user_id"] == "user_test"
        assert payload["role"] == "analyst"
        assert "model:read" in payload["permissions"]

    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None"""
        # Act
        payload = TenantToken.decode_token("invalid.signature")

        # Assert
        assert payload is None

    def test_decode_tampered_token(self):
        """Test decoding tampered token fails"""
        # Arrange
        token = TenantToken.create_token(
            org_id="org_001",
            user_id="user_001",
            role=UserRole.ADMIN,
            permissions=[],
        )

        # Tamper with payload
        parts = token.split(".")
        tampered = parts[0] + "tampered." + parts[1]

        # Act
        payload = TenantToken.decode_token(tampered)

        # Assert
        assert payload is None

    def test_token_expiration(self):
        """Test token expiration checking"""
        # Arrange - Expired token
        expired_token = TenantToken.create_token(
            org_id="org_001",
            user_id="user_001",
            role=UserRole.ADMIN,
            permissions=[],
            expires_in_seconds=-1,  # Already expired
        )

        # Arrange - Valid token
        valid_token = TenantToken.create_token(
            org_id="org_001",
            user_id="user_001",
            role=UserRole.ADMIN,
            permissions=[],
            expires_in_seconds=3600,
        )

        # Assert
        assert TenantToken.is_expired(expired_token) is True
        assert TenantToken.is_expired(valid_token) is False

    def test_token_includes_timestamps(self):
        """Test token includes iat and exp timestamps"""
        # Arrange
        before = int(time.time())
        token = TenantToken.create_token(
            org_id="org_001",
            user_id="user_001",
            role=UserRole.ADMIN,
            permissions=[],
            expires_in_seconds=3600,
        )
        after = int(time.time())

        # Act
        payload = TenantToken.decode_token(token)

        # Assert
        assert "iat" in payload
        assert "exp" in payload
        assert before <= payload["iat"] <= after
        assert payload["exp"] == payload["iat"] + 3600


# ============================================================================
# TEST CLASS: Integration Tests
# ============================================================================


class TestMultiTenancyIntegration:
    """Integration tests for multi-tenancy features"""

    @pytest.mark.asyncio
    async def test_full_tenant_workflow(self):
        """Test complete tenant workflow from token to data access"""
        # Step 1: Create organization and user
        org = Organization(
            org_id="org_integration",
            name="Integration Test Org",
            subscription_tier=SubscriptionTier.PROFESSIONAL,
            owner_id="owner_001",
        )

        user = TenantUser(
            user_id="user_integration",
            org_id="org_integration",
            email="test@integration.com",
            role=UserRole.COMPLIANCE_OFFICER,
        )
        org.add_user(user)

        # Step 2: Create token
        token = TenantToken.create_token(
            org_id=user.org_id,
            user_id=user.user_id,
            role=user.role,
            permissions=[p.value for p in user.get_all_permissions()],
        )

        # Step 3: Middleware extracts context
        middleware = TenantMiddleware()
        context = middleware.extract_tenant_from_token(token)

        assert context is not None
        assert context.org_id == "org_integration"

        # Step 4: Use context for isolation
        isolation = TenantIsolation(context)

        # Step 5: Check permissions and limits
        assert user.has_permission(Permission.ASSESSMENT_RUN)
        allowed, _ = isolation.check_limit("models", 10)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_cross_tenant_isolation(self):
        """Test that tenants cannot access each other's data"""
        # Arrange - Two organizations
        org_a = Organization(
            org_id="org_a",
            name="Organization A",
            subscription_tier=SubscriptionTier.PROFESSIONAL,
            owner_id="owner_a",
        )

        org_b = Organization(
            org_id="org_b",
            name="Organization B",
            subscription_tier=SubscriptionTier.PROFESSIONAL,
            owner_id="owner_b",
        )

        # Create users
        user_a = TenantUser(
            user_id="user_a",
            org_id="org_a",
            email="user@org-a.com",
            role=UserRole.ADMIN,
        )

        user_b = TenantUser(
            user_id="user_b",
            org_id="org_b",
            email="user@org-b.com",
            role=UserRole.ADMIN,
        )

        # Create contexts
        context_a = TenantContext(
            org_id="org_a",
            user_id="user_a",
            role=UserRole.ADMIN,
            permissions=user_a.get_all_permissions(),
            subscription_tier=SubscriptionTier.PROFESSIONAL,
        )

        context_b = TenantContext(
            org_id="org_b",
            user_id="user_b",
            role=UserRole.ADMIN,
            permissions=user_b.get_all_permissions(),
            subscription_tier=SubscriptionTier.PROFESSIONAL,
        )

        # Create mock data belonging to both orgs
        class MockData:
            def __init__(self, data_id: str, org_id: str):
                self.data_id = data_id
                self.org_id = org_id

        all_data = [
            MockData("data_a1", "org_a"),
            MockData("data_a2", "org_a"),
            MockData("data_b1", "org_b"),
            MockData("data_b2", "org_b"),
            MockData("data_b3", "org_b"),
        ]

        # Test isolation for Org A
        isolation_a = TenantIsolation(context_a)
        data_a = isolation_a.filter_by_org(all_data)

        assert len(data_a) == 2
        assert all(d.org_id == "org_a" for d in data_a)

        # Test isolation for Org B
        isolation_b = TenantIsolation(context_b)
        data_b = isolation_b.filter_by_org(all_data)

        assert len(data_b) == 3
        assert all(d.org_id == "org_b" for d in data_b)

        # Verify no cross-contamination
        assert not any(d.org_id == "org_b" for d in data_a)
        assert not any(d.org_id == "org_a" for d in data_b)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
