"""Tests for tenant schemas."""

import pytest
from uuid import UUID
from pydantic import ValidationError

from shared_schemas.tenant import (
    TenantBase,
    TenantCreate,
    TenantLimits,
    TenantResponse,
    TenantStatus,
    TenantTier,
    TIER_LIMITS,
)


class TestTenantStatus:
    def test_enum_values(self):
        assert TenantStatus.ACTIVE == "active"
        assert TenantStatus.SUSPENDED == "suspended"
        assert TenantStatus.TRIAL == "trial"


class TestTenantTier:
    def test_enum_values(self):
        assert TenantTier.FREE == "free"
        assert TenantTier.STARTER == "starter"
        assert TenantTier.PRO == "pro"
        assert TenantTier.ENTERPRISE == "enterprise"


class TestTenantLimits:
    def test_defaults(self):
        limits = TenantLimits()
        assert limits.max_users == 5
        assert limits.max_queries_per_day == 1000
        assert limits.storage_gb == 1.0

    def test_frozen(self):
        limits = TenantLimits()
        with pytest.raises(ValidationError):
            limits.max_users = 10

    def test_negative_users_rejected(self):
        with pytest.raises(ValidationError):
            TenantLimits(max_users=0)

    def test_tier_limits_defined(self):
        for tier in TenantTier:
            assert tier in TIER_LIMITS


class TestTenantBase:
    def test_create_with_defaults(self):
        t = TenantBase(name="Acme Corp", slug="acme-corp")
        assert isinstance(t.id, UUID)
        assert t.status == TenantStatus.TRIAL
        assert t.tier == TenantTier.FREE
        assert t.stripe_customer_id is None

    def test_slug_validation_valid(self):
        t = TenantBase(name="Test", slug="my-slug-123")
        assert t.slug == "my-slug-123"

    def test_slug_validation_rejects_uppercase(self):
        with pytest.raises(ValidationError):
            TenantBase(name="Test", slug="MySlug")

    def test_slug_validation_rejects_spaces(self):
        with pytest.raises(ValidationError):
            TenantBase(name="Test", slug="my slug")

    def test_limits_property(self):
        t = TenantBase(name="Test", slug="test", tier=TenantTier.PRO)
        assert t.limits.max_users == 25
        assert t.limits.max_queries_per_day == 50000

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            TenantBase(name="", slug="test")


class TestTenantCreate:
    def test_valid_create(self):
        tc = TenantCreate(name="Acme", slug="acme", email="admin@acme.com")
        assert tc.plan == TenantTier.FREE
        assert tc.email == "admin@acme.com"

    def test_email_normalized(self):
        tc = TenantCreate(name="Acme", slug="acme", email="  Admin@ACME.COM  ")
        assert tc.email == "admin@acme.com"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            TenantCreate(name="Acme", slug="acme", email="not-an-email")

    def test_email_without_dot_rejected(self):
        with pytest.raises(ValidationError):
            TenantCreate(name="Acme", slug="acme", email="user@localhost")


class TestTenantResponse:
    def test_includes_usage(self):
        tr = TenantResponse(
            name="Test",
            slug="test",
            usage_this_period={"rag_queries": 150},
        )
        assert tr.usage_this_period["rag_queries"] == 150

    def test_includes_limits_info(self):
        limits = TenantLimits(max_users=10)
        tr = TenantResponse(name="Test", slug="test", limits_info=limits)
        assert tr.limits_info.max_users == 10
