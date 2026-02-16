"""Tests for auth schemas."""

from datetime import datetime, timedelta

import pytest
from shared_schemas.auth import APIKeyConfig, JWTClaims, Permission


class TestPermission:
    def test_all_permissions(self):
        assert set(Permission) == {Permission.READ, Permission.WRITE, Permission.ADMIN, Permission.BILLING}

    def test_permission_is_str(self):
        assert Permission.READ == "READ"


class TestJWTClaims:
    def test_valid_claims(self):
        future = datetime.utcnow() + timedelta(hours=1)
        claims = JWTClaims(sub="user-1", tenant_id="t-1", permissions=[Permission.READ], exp=future)
        assert claims.sub == "user-1"
        assert claims.tenant_id == "t-1"
        assert Permission.READ in claims.permissions

    def test_expired_token_rejected(self):
        past = datetime.utcnow() - timedelta(hours=1)
        with pytest.raises(ValueError, match="future"):
            JWTClaims(sub="user-1", tenant_id="t-1", exp=past)

    def test_default_permissions_empty(self):
        future = datetime.utcnow() + timedelta(hours=1)
        claims = JWTClaims(sub="user-1", tenant_id="t-1", exp=future)
        assert claims.permissions == []

    def test_iat_optional(self):
        future = datetime.utcnow() + timedelta(hours=1)
        claims = JWTClaims(sub="u", tenant_id="t", exp=future)
        assert claims.iat is None

    def test_iat_set(self):
        now = datetime.utcnow()
        future = now + timedelta(hours=1)
        claims = JWTClaims(sub="u", tenant_id="t", exp=future, iat=now)
        assert claims.iat == now

    def test_multiple_permissions(self):
        future = datetime.utcnow() + timedelta(hours=1)
        claims = JWTClaims(
            sub="admin",
            tenant_id="t-1",
            permissions=[Permission.READ, Permission.WRITE, Permission.ADMIN],
            exp=future,
        )
        assert len(claims.permissions) == 3


class TestAPIKeyConfig:
    def test_create_api_key(self):
        key = APIKeyConfig(key_id="k-1", tenant_id="t-1", name="Production Key")
        assert key.is_active is True
        assert key.permissions == []
        assert key.expires_at is None

    def test_api_key_with_permissions(self):
        key = APIKeyConfig(
            key_id="k-2",
            tenant_id="t-1",
            name="Read-Only",
            permissions=[Permission.READ],
        )
        assert key.permissions == [Permission.READ]

    def test_inactive_key(self):
        key = APIKeyConfig(key_id="k-3", tenant_id="t-1", name="Revoked", is_active=False)
        assert key.is_active is False

    def test_key_with_expiry(self):
        exp = datetime.utcnow() + timedelta(days=90)
        key = APIKeyConfig(key_id="k-4", tenant_id="t-1", name="Temp", expires_at=exp)
        assert key.expires_at == exp
