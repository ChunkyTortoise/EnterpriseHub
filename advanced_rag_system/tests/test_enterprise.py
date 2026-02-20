"""Tests for enterprise features: auth, multi-tenancy, and usage metering."""
import os
import sys

# Ensure src directory is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from enterprise.auth import APIKeyAuth, JWTAuth
from enterprise.multi_tenant import TenantDocumentStore, TenantIsolationError
from enterprise.usage_metering import UsageMetering, UsageRecord
from fastapi import HTTPException

# -- API Key Auth -----------------------------------------------------------

class TestAPIKeyAuth:
    def test_api_key_auth_valid(self):
        auth = APIKeyAuth(allowed_keys=frozenset({"my-key"}))
        tenant = auth.validate("my-key")
        assert tenant == "tenant:my-key"

    def test_api_key_auth_invalid(self):
        auth = APIKeyAuth(allowed_keys=frozenset({"my-key"}))
        with pytest.raises(HTTPException) as exc_info:
            auth.validate("wrong-key")
        assert exc_info.value.status_code == 401

    def test_api_key_auth_missing(self):
        auth = APIKeyAuth(allowed_keys=frozenset({"my-key"}))
        with pytest.raises(HTTPException) as exc_info:
            auth.validate(None)
        assert exc_info.value.status_code == 401


# -- JWT Auth ---------------------------------------------------------------

class TestJWTAuth:
    def test_jwt_auth_skip_if_unavailable(self):
        """If python-jose is not installed, JWTAuth raises 501."""
        try:
            from jose import jwt as jose_jwt
            # jose IS installed -- test with a valid token
            secret = "test-secret"
            token = jose_jwt.encode({"sub": "tenant-abc"}, secret, algorithm="HS256")
            auth = JWTAuth(secret=secret)
            tenant = auth.validate(token)
            assert tenant == "tenant-abc"
        except ImportError:
            # jose NOT installed -- should raise 501
            auth = JWTAuth()
            with pytest.raises(HTTPException) as exc_info:
                auth.validate("some-token")
            assert exc_info.value.status_code == 501

    def test_jwt_auth_missing_token(self):
        auth = JWTAuth()
        try:
            from jose import jwt as jose_jwt
            with pytest.raises(HTTPException) as exc_info:
                auth.validate(None)
            assert exc_info.value.status_code == 401
        except ImportError:
            pytest.skip("python-jose not installed")

    def test_jwt_auth_invalid_token(self):
        try:
            from jose import jwt as jose_jwt
        except ImportError:
            pytest.skip("python-jose not installed")
        auth = JWTAuth(secret="real-secret")
        with pytest.raises(HTTPException) as exc_info:
            auth.validate("not.a.valid.token")
        assert exc_info.value.status_code == 401


# -- Multi-Tenant Document Store --------------------------------------------

class TestTenantDocumentStore:
    def test_multi_tenant_add_and_get(self):
        store = TenantDocumentStore()
        store.add_document("t1", "doc1", "Hello world")
        assert store.get_document("t1", "doc1") == "Hello world"

    def test_multi_tenant_isolation(self):
        store = TenantDocumentStore()
        store.add_document("t1", "doc1", "Secret data")
        # Tenant t2 should not see t1's document
        result = store.get_document("t2", "doc1")
        assert result is None  # doc1 is not in t2's namespace

    def test_multi_tenant_isolation_raw(self):
        """Verify the document exists but is owned by a different tenant."""
        store = TenantDocumentStore()
        store.add_document("t1", "doc1", "Secret data")
        raw = store._get_raw("doc1")
        assert raw is not None
        assert raw.tenant_id == "t1"

    def test_multi_tenant_list(self):
        store = TenantDocumentStore()
        store.add_document("t1", "doc1", "A")
        store.add_document("t1", "doc2", "B")
        store.add_document("t2", "doc3", "C")
        assert sorted(store.list_documents("t1")) == ["doc1", "doc2"]
        assert store.list_documents("t2") == ["doc3"]
        assert store.list_documents("t3") == []

    def test_multi_tenant_delete(self):
        store = TenantDocumentStore()
        store.add_document("t1", "doc1", "Data")
        assert store.delete_document("t1", "doc1") is True
        assert store.delete_document("t1", "doc1") is False  # Already deleted
        assert store.get_document("t1", "doc1") is None


# -- Usage Metering ---------------------------------------------------------

class TestUsageMetering:
    def test_usage_record_query(self):
        meter = UsageMetering()
        meter.record_query("t1", token_count=150)
        meter.record_query("t1", token_count=200)
        usage = meter.get_usage("t1")
        assert usage.query_count == 2
        assert usage.total_tokens == 350
        assert usage.last_query_at is not None

    def test_usage_get_unregistered(self):
        meter = UsageMetering()
        usage = meter.get_usage("unknown-tenant")
        assert usage.tenant_id == "unknown-tenant"
        assert usage.query_count == 0
        assert usage.total_tokens == 0
        assert usage.last_query_at is None

    def test_usage_reset(self):
        meter = UsageMetering()
        meter.record_query("t1", token_count=500)
        meter.reset_usage("t1")
        usage = meter.get_usage("t1")
        assert usage.query_count == 0
        assert usage.total_tokens == 0

    def test_usage_negative_tokens_clamped(self):
        meter = UsageMetering()
        meter.record_query("t1", token_count=-100)
        usage = meter.get_usage("t1")
        assert usage.total_tokens == 0  # max(0, -100) = 0
