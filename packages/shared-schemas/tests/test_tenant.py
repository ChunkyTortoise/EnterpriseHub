"""Tests for tenant schemas."""

import pytest

from shared_schemas.tenant import TenantConfig, TenantLimits, TenantTier


class TestTenantTier:
    def test_all_tiers_exist(self):
        assert set(TenantTier) == {TenantTier.FREE, TenantTier.STARTER, TenantTier.PRO, TenantTier.ENTERPRISE}

    def test_tier_is_str_enum(self):
        assert TenantTier.FREE == "FREE"
        assert isinstance(TenantTier.PRO, str)


class TestTenantLimits:
    def test_default_limits(self):
        limits = TenantLimits()
        assert limits.max_users == 1
        assert limits.max_queries_per_day == 100
        assert limits.max_storage_gb == 1.0
        assert limits.max_api_keys == 1

    def test_custom_limits(self):
        limits = TenantLimits(max_users=50, max_queries_per_day=5000, max_storage_gb=200.0, max_api_keys=20)
        assert limits.max_users == 50
        assert limits.max_storage_gb == 200.0

    def test_limits_are_frozen(self):
        limits = TenantLimits()
        with pytest.raises(Exception):
            limits.max_users = 99


class TestTenantConfig:
    def test_creates_with_defaults(self):
        config = TenantConfig(name="Acme Corp")
        assert config.name == "Acme Corp"
        assert config.tier == TenantTier.FREE
        assert config.limits is not None
        assert config.limits.max_users == 1
        assert config.metadata == {}

    def test_auto_sets_limits_from_tier(self):
        config = TenantConfig(name="Pro Tenant", tier=TenantTier.PRO)
        assert config.limits.max_users == 25
        assert config.limits.max_queries_per_day == 10_000

    def test_enterprise_tier_limits(self):
        config = TenantConfig(name="Big Corp", tier=TenantTier.ENTERPRISE)
        assert config.limits.max_users == 999_999

    def test_custom_limits_override_tier_defaults(self):
        custom = TenantLimits(max_users=3, max_queries_per_day=50, max_storage_gb=0.5, max_api_keys=1)
        config = TenantConfig(name="Custom", tier=TenantTier.PRO, limits=custom)
        assert config.limits.max_users == 3

    def test_uuid_id_generated(self):
        c1 = TenantConfig(name="A")
        c2 = TenantConfig(name="B")
        assert c1.id != c2.id
        assert len(c1.id) == 36

    def test_serialization_roundtrip(self):
        config = TenantConfig(name="Test", tier=TenantTier.STARTER)
        data = config.model_dump()
        restored = TenantConfig(**data)
        assert restored.name == config.name
        assert restored.tier == config.tier
        assert restored.limits == config.limits

    def test_metadata_field(self):
        config = TenantConfig(name="Meta", metadata={"region": "us-west-2"})
        assert config.metadata["region"] == "us-west-2"
