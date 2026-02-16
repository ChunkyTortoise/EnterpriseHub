"""Tests for auth schemas."""

import pytest
from uuid import uuid4
from pydantic import ValidationError

from shared_schemas.auth import APIKeySchema, JWTClaims, JWTPayload, Permission


class TestPermission:
    def test_enum_values(self):
        assert Permission.READ == "read"
        assert Permission.WRITE == "write"
        assert Permission.ADMIN == "admin"
        assert Permission.BILLING == "billing"


class TestAPIKeySchema:
    def test_valid_key(self):
        key = APIKeySchema(
            id=uuid4(),
            tenant_id=uuid4(),
            key_prefix="sk_live_",
            hashed_key="abc123hash",
            name="Production Key",
        )
        assert key.is_active is True
        assert key.rate_limit == 100
        assert key.scopes == ["read", "write"]

    def test_prefix_length_validated(self):
        with pytest.raises(ValidationError):
            APIKeySchema(
                id=uuid4(),
                tenant_id=uuid4(),
                key_prefix="short",
                hashed_key="hash",
                name="Bad Key",
            )

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            APIKeySchema(
                id=uuid4(),
                tenant_id=uuid4(),
                key_prefix="sk_live_",
                hashed_key="hash",
                name="",
            )

    def test_custom_scopes(self):
        key = APIKeySchema(
            id=uuid4(),
            tenant_id=uuid4(),
            key_prefix="sk_test_",
            hashed_key="hash",
            name="Read-Only Key",
            scopes=["read"],
            rate_limit=10,
        )
        assert key.scopes == ["read"]
        assert key.rate_limit == 10


class TestJWTPayload:
    def test_valid_payload(self):
        p = JWTPayload(sub="user123", tenant_id="tenant456", scopes=["read"], exp=9999999999)
        assert p.sub == "user123"

    def test_default_scopes(self):
        p = JWTPayload(sub="user123", tenant_id="t1", exp=9999999999)
        assert p.scopes == ["read"]


class TestJWTClaims:
    def test_valid_claims(self):
        c = JWTClaims(
            sub="user123",
            tenant_id="tenant456",
            permissions=[Permission.READ, Permission.WRITE],
            exp=9999999999,
            iat=1000000000,
            iss="shared-schemas",
        )
        assert Permission.ADMIN not in c.permissions

    def test_default_permissions(self):
        c = JWTClaims(sub="user123", tenant_id="t1", exp=9999999999)
        assert c.permissions == [Permission.READ]
        assert c.iat is None
        assert c.iss is None
