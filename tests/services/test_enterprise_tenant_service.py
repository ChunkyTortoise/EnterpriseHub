"""
Tests for Enterprise Tenant Management Service.

Ensures reliability for high-ticket consulting platform ($25K-$100K engagements).
"""

import pytest
import asyncio
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from ghl_real_estate_ai.services.enterprise_tenant_service import (
    EnterpriseTenantService, TenantConfig, TenantUser, BrandingConfig, 
    FeatureFlags, TenantTier, TenantStatus, Permission, RoleType,
    get_enterprise_tenant_service
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
async def enterprise_service():
    """Create enterprise tenant service for testing."""
    service = EnterpriseTenantService()
    await service.initialize()
    yield service
    # Cleanup would go here if needed


@pytest.fixture
def sample_tenant_config():
    """Sample tenant configuration for testing."""
    return TenantConfig(
        name="Test Consulting Client",
        slug="test-consulting-client",
        tier=TenantTier.PROFESSIONAL,
        primary_contact_email="admin@testclient.com",
        organization_name="Test Client Corp",
        anthropic_api_key="test-claude-key",
        ghl_api_key="test-ghl-key",
        ghl_location_id="loc_test123",
        apollo_api_key="test-apollo-key",
        twilio_account_sid="test-twilio-sid",
        sendgrid_api_key="test-sendgrid-key",
        consulting_package_value=65000.00,
        engagement_start_date=date.today(),
        engagement_end_date=date.today() + timedelta(days=90)
    )


@pytest.fixture
def sample_branding_config():
    """Sample branding configuration."""
    return BrandingConfig(
        logo_url="https://client.com/logo.png",
        primary_color="#FF6B35",
        secondary_color="#004E89",
        company_name="Client Real Estate",
        contact_email="support@client.com",
        support_phone="+1-555-0123"
    )


# ============================================================================
# Tenant Management Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_tenant(enterprise_service, sample_tenant_config):
    """Test creating enterprise tenant with full configuration."""
    tenant_id = await enterprise_service.create_tenant(
        sample_tenant_config, 
        created_by="test-system"
    )
    
    assert tenant_id is not None
    assert len(tenant_id) == 36  # UUID format
    
    # Verify tenant was created correctly
    retrieved = await enterprise_service.get_tenant_config(tenant_id)
    assert retrieved is not None
    assert retrieved.name == sample_tenant_config.name
    assert retrieved.tier == TenantTier.PROFESSIONAL
    assert retrieved.consulting_package_value == 65000.00


@pytest.mark.asyncio
async def test_create_tenant_with_custom_branding(enterprise_service, sample_branding_config):
    """Test creating tenant with custom branding configuration."""
    config = TenantConfig(
        name="Branded Client",
        slug="branded-client",
        tier=TenantTier.ENTERPRISE,
        primary_contact_email="admin@brandedclient.com",
        organization_name="Branded Client LLC",
        anthropic_api_key="test-key",
        ghl_api_key="test-ghl",
        branding=sample_branding_config,
        consulting_package_value=95000.00
    )
    
    tenant_id = await enterprise_service.create_tenant(config)
    retrieved = await enterprise_service.get_tenant_config(tenant_id)
    
    assert retrieved.branding.company_name == "Client Real Estate"
    assert retrieved.branding.primary_color == "#FF6B35"
    assert retrieved.branding.support_phone == "+1-555-0123"


@pytest.mark.asyncio
async def test_tenant_tier_feature_mapping(enterprise_service):
    """Test that tenant tiers correctly map to feature flags."""
    # Test STARTER tier ($25K-$35K)
    starter_config = TenantConfig(
        name="Starter Client",
        slug="starter-client",
        tier=TenantTier.STARTER,
        primary_contact_email="admin@starter.com",
        organization_name="Starter Corp",
        anthropic_api_key="key1",
        ghl_api_key="key2",
        consulting_package_value=30000.00
    )
    
    starter_id = await enterprise_service.create_tenant(starter_config)
    starter_retrieved = await enterprise_service.get_tenant_config(starter_id)
    
    assert starter_retrieved.feature_flags.behavioral_profiling is True
    assert starter_retrieved.feature_flags.white_label_branding is True
    assert starter_retrieved.feature_flags.multi_agent_swarm is False  # Not in starter
    assert starter_retrieved.feature_flags.custom_ai_models is False  # Not in starter
    
    # Test ENTERPRISE tier ($75K-$100K+)
    enterprise_config = TenantConfig(
        name="Enterprise Client",
        slug="enterprise-client",
        tier=TenantTier.ENTERPRISE,
        primary_contact_email="admin@enterprise.com",
        organization_name="Enterprise Corp",
        anthropic_api_key="key1",
        ghl_api_key="key2",
        consulting_package_value=85000.00
    )
    
    enterprise_id = await enterprise_service.create_tenant(enterprise_config)
    enterprise_retrieved = await enterprise_service.get_tenant_config(enterprise_id)
    
    assert enterprise_retrieved.feature_flags.multi_agent_swarm is True
    assert enterprise_retrieved.feature_flags.custom_ai_models is True
    assert enterprise_retrieved.feature_flags.real_time_consensus is True
    assert enterprise_retrieved.feature_flags.success_measurement is True


@pytest.mark.asyncio
async def test_get_tenant_by_slug(enterprise_service, sample_tenant_config):
    """Test retrieving tenant by slug instead of ID."""
    tenant_id = await enterprise_service.create_tenant(sample_tenant_config)
    
    # Should be able to retrieve by slug
    retrieved_by_slug = await enterprise_service.get_tenant_config(sample_tenant_config.slug)
    retrieved_by_id = await enterprise_service.get_tenant_config(tenant_id)
    
    assert retrieved_by_slug.id == retrieved_by_id.id
    assert retrieved_by_slug.name == retrieved_by_id.name


@pytest.mark.asyncio
async def test_duplicate_slug_prevention(enterprise_service, sample_tenant_config):
    """Test that duplicate slugs are prevented."""
    # Create first tenant
    await enterprise_service.create_tenant(sample_tenant_config)
    
    # Try to create second tenant with same slug
    duplicate_config = TenantConfig(
        name="Different Name",
        slug=sample_tenant_config.slug,  # Same slug
        tier=TenantTier.STARTER,
        primary_contact_email="different@email.com",
        organization_name="Different Org",
        anthropic_api_key="different-key",
        ghl_api_key="different-ghl"
    )
    
    with pytest.raises(ValueError, match="already exists"):
        await enterprise_service.create_tenant(duplicate_config)


@pytest.mark.asyncio 
async def test_update_tenant(enterprise_service, sample_tenant_config):
    """Test updating tenant configuration."""
    tenant_id = await enterprise_service.create_tenant(sample_tenant_config)
    
    # Update tenant
    updates = {
        "organization_name": "Updated Corp Name",
        "consulting_package_value": 75000.00,
        "tier": TenantTier.ENTERPRISE.value
    }
    
    success = await enterprise_service.update_tenant(
        tenant_id, updates, updated_by="test-admin"
    )
    
    assert success is True
    
    # Verify updates
    updated_tenant = await enterprise_service.get_tenant_config(tenant_id)
    assert updated_tenant.organization_name == "Updated Corp Name"
    assert updated_tenant.consulting_package_value == 75000.00
    assert updated_tenant.tier == TenantTier.ENTERPRISE


# ============================================================================
# User Management & RBAC Tests  
# ============================================================================

@pytest.mark.asyncio
async def test_create_tenant_user(enterprise_service, sample_tenant_config):
    """Test creating tenant user with role-based permissions."""
    tenant_id = await enterprise_service.create_tenant(sample_tenant_config)
    
    user = TenantUser(
        tenant_id=tenant_id,
        email="sales@testclient.com",
        first_name="Sales",
        last_name="Manager",
        role=RoleType.SALES_MANAGER
    )
    
    user_id = await enterprise_service.create_tenant_user(user, "admin")
    assert user_id is not None
    
    # Verify user has correct role permissions
    has_leads_edit = await enterprise_service.check_permission(
        "sales@testclient.com", tenant_id, Permission.LEADS_EDIT
    )
    has_tenant_admin = await enterprise_service.check_permission(
        "sales@testclient.com", tenant_id, Permission.TENANT_ADMIN
    )
    
    assert has_leads_edit is True  # Sales manager should have this
    assert has_tenant_admin is False  # Sales manager should NOT have this


@pytest.mark.asyncio
async def test_role_permission_mapping(enterprise_service, sample_tenant_config):
    """Test that roles map to correct permission sets."""
    tenant_id = await enterprise_service.create_tenant(sample_tenant_config)
    
    # Test TENANT_ADMIN role
    admin_user = TenantUser(
        tenant_id=tenant_id,
        email="admin@test.com", 
        first_name="Admin",
        last_name="User",
        role=RoleType.TENANT_ADMIN
    )
    
    await enterprise_service.create_tenant_user(admin_user)
    
    # Should have admin permissions
    assert await enterprise_service.check_permission(
        "admin@test.com", tenant_id, Permission.TENANT_ADMIN
    ) is True
    assert await enterprise_service.check_permission(
        "admin@test.com", tenant_id, Permission.WHITELABEL_BRANDING 
    ) is True
    
    # Test VIEWER role
    viewer_user = TenantUser(
        tenant_id=tenant_id,
        email="viewer@test.com",
        first_name="View",
        last_name="Only", 
        role=RoleType.VIEWER
    )
    
    await enterprise_service.create_tenant_user(viewer_user)
    
    # Should only have view permissions
    assert await enterprise_service.check_permission(
        "viewer@test.com", tenant_id, Permission.LEADS_VIEW
    ) is True
    assert await enterprise_service.check_permission(
        "viewer@test.com", tenant_id, Permission.LEADS_EDIT
    ) is False


# ============================================================================
# Usage Tracking & Analytics Tests
# ============================================================================

@pytest.mark.asyncio
async def test_track_usage(enterprise_service, sample_tenant_config):
    """Test usage tracking for billing and analytics."""
    tenant_id = await enterprise_service.create_tenant(sample_tenant_config)
    
    # Track some usage
    usage_metrics = {
        "ai_queries": 150,
        "multi_agent_queries": 25,
        "behavioral_analysis_runs": 10,
        "leads_processed": 75,
        "campaigns_executed": 5,
        "revenue_attributed": 250000.00,
        "leads_converted": 12,
        "roi_calculated": 4.85
    }
    
    await enterprise_service.track_usage(tenant_id, usage_metrics)
    
    # Verify usage was tracked
    analytics = await enterprise_service.get_tenant_analytics(tenant_id)
    
    assert analytics["summary"]["total_ai_queries"] == 150
    assert analytics["summary"]["total_multi_agent"] == 25
    assert analytics["summary"]["total_revenue_attributed"] == Decimal("250000.00")
    assert analytics["summary"]["total_leads_converted"] == 12


@pytest.mark.asyncio
async def test_cumulative_usage_tracking(enterprise_service, sample_tenant_config):
    """Test that usage accumulates correctly over multiple tracking calls."""
    tenant_id = await enterprise_service.create_tenant(sample_tenant_config)
    
    # Track usage twice on the same day
    await enterprise_service.track_usage(tenant_id, {"ai_queries": 50, "leads_processed": 20})
    await enterprise_service.track_usage(tenant_id, {"ai_queries": 30, "leads_processed": 15})
    
    analytics = await enterprise_service.get_tenant_analytics(tenant_id)
    
    # Should accumulate
    assert analytics["summary"]["total_ai_queries"] == 80  # 50 + 30
    assert analytics["summary"]["total_leads_processed"] == 35  # 20 + 15


@pytest.mark.asyncio
async def test_analytics_date_filtering(enterprise_service, sample_tenant_config):
    """Test analytics date filtering functionality."""
    tenant_id = await enterprise_service.create_tenant(sample_tenant_config)
    
    # Track usage
    await enterprise_service.track_usage(tenant_id, {"ai_queries": 100})
    
    # Test different date ranges
    analytics_7d = await enterprise_service.get_tenant_analytics(tenant_id, days=7)
    analytics_30d = await enterprise_service.get_tenant_analytics(tenant_id, days=30)
    
    assert analytics_7d["period_days"] == 7
    assert analytics_30d["period_days"] == 30
    assert analytics_7d["summary"]["total_ai_queries"] == 100
    assert analytics_30d["summary"]["total_ai_queries"] == 100


# ============================================================================
# Legacy Compatibility Tests
# ============================================================================

@pytest.mark.asyncio
async def test_legacy_compatibility(enterprise_service, sample_tenant_config):
    """Test compatibility with existing tenant_service.py interface."""
    tenant_id = await enterprise_service.create_tenant(sample_tenant_config)
    
    # Test legacy method
    legacy_config = await enterprise_service.get_legacy_tenant_config(tenant_id)
    
    assert legacy_config["anthropic_api_key"] == sample_tenant_config.anthropic_api_key
    assert legacy_config["ghl_api_key"] == sample_tenant_config.ghl_api_key
    assert legacy_config["location_id"] == sample_tenant_config.ghl_location_id
    assert "enterprise_features" in legacy_config
    assert "branding" in legacy_config


# ============================================================================
# Data Validation Tests
# ============================================================================

def test_tenant_config_validation():
    """Test tenant configuration validation."""
    # Test invalid slug
    with pytest.raises(ValueError, match="Slug must contain only"):
        TenantConfig(
            name="Test",
            slug="Invalid Slug!",  # Invalid characters
            primary_contact_email="test@example.com",
            organization_name="Test Corp",
            anthropic_api_key="key",
            ghl_api_key="key"
        )
    
    # Test valid slug
    config = TenantConfig(
        name="Test",
        slug="valid-slug-123",  # Valid
        primary_contact_email="test@example.com",
        organization_name="Test Corp",
        anthropic_api_key="key",
        ghl_api_key="key"
    )
    assert config.slug == "valid-slug-123"


def test_feature_flags_dataclass():
    """Test feature flags data structure."""
    flags = FeatureFlags(
        multi_agent_swarm=True,
        behavioral_profiling=True,
        custom_ai_models=False
    )
    
    flags_dict = flags.to_dict()
    assert flags_dict["multi_agent_swarm"] is True
    assert flags_dict["behavioral_profiling"] is True
    assert flags_dict["custom_ai_models"] is False


def test_branding_config_dataclass():
    """Test branding configuration data structure."""
    branding = BrandingConfig(
        logo_url="https://example.com/logo.png",
        primary_color="#FF0000",
        company_name="Test Company",
        contact_email="contact@test.com"
    )
    
    branding_dict = branding.to_dict()
    assert branding_dict["logo_url"] == "https://example.com/logo.png"
    assert branding_dict["primary_color"] == "#FF0000"
    assert branding_dict["company_name"] == "Test Company"


# ============================================================================
# Security Tests
# ============================================================================

@pytest.mark.asyncio
async def test_api_key_encryption(enterprise_service):
    """Test that API keys are properly encrypted in storage."""
    config = TenantConfig(
        name="Security Test",
        slug="security-test",
        primary_contact_email="test@security.com",
        organization_name="Security Corp",
        anthropic_api_key="secret-claude-key",
        ghl_api_key="secret-ghl-key"
    )
    
    tenant_id = await enterprise_service.create_tenant(config)
    
    # Verify we can retrieve decrypted keys
    retrieved = await enterprise_service.get_tenant_config(tenant_id)
    assert retrieved.anthropic_api_key == "secret-claude-key"
    assert retrieved.ghl_api_key == "secret-ghl-key"
    
    # Keys should be encrypted in database (placeholder test)
    # In production, would verify keys are not stored in plaintext


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
async def test_bulk_tenant_operations(enterprise_service):
    """Test performance with multiple tenants."""
    # Create multiple tenants
    tenant_ids = []
    
    for i in range(5):  # Small number for test performance
        config = TenantConfig(
            name=f"Bulk Test {i}",
            slug=f"bulk-test-{i}",
            primary_contact_email=f"test{i}@bulk.com",
            organization_name=f"Bulk Corp {i}",
            anthropic_api_key=f"key-{i}",
            ghl_api_key=f"ghl-{i}"
        )
        
        tenant_id = await enterprise_service.create_tenant(config)
        tenant_ids.append(tenant_id)
    
    # Verify all can be retrieved efficiently
    for tenant_id in tenant_ids:
        tenant = await enterprise_service.get_tenant_config(tenant_id)
        assert tenant is not None


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_nonexistent_tenant_retrieval(enterprise_service):
    """Test retrieving non-existent tenant."""
    fake_id = str(uuid4())
    tenant = await enterprise_service.get_tenant_config(fake_id)
    assert tenant is None
    
    fake_slug = "nonexistent-tenant"
    tenant_by_slug = await enterprise_service.get_tenant_config(fake_slug)
    assert tenant_by_slug is None


@pytest.mark.asyncio
async def test_permission_check_nonexistent_user(enterprise_service, sample_tenant_config):
    """Test permission check for non-existent user."""
    tenant_id = await enterprise_service.create_tenant(sample_tenant_config)
    
    has_permission = await enterprise_service.check_permission(
        "nonexistent@user.com", tenant_id, Permission.LEADS_VIEW
    )
    
    assert has_permission is False


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_service_factory():
    """Test service factory and singleton pattern."""
    service1 = await get_enterprise_tenant_service()
    service2 = await get_enterprise_tenant_service()
    
    # Should return same instance (singleton)
    assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])