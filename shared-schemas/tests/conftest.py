"""Shared test fixtures for the shared-schemas test suite."""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


@pytest.fixture
def mock_redis():
    """Mock Redis client with async support."""
    redis = AsyncMock()
    store: dict[str, Any] = {}
    hash_store: dict[str, dict[str, Any]] = defaultdict(dict)
    counters: dict[str, int] = {}

    async def mock_get(key: str) -> Any:
        return store.get(key)

    async def mock_set(key: str, value: Any, *args, **kwargs) -> None:
        store[key] = value

    async def mock_setex(key: str, ttl: int, value: Any) -> None:
        store[key] = value

    async def mock_incr(key: str) -> int:
        counters[key] = counters.get(key, 0) + 1
        return counters[key]

    async def mock_expire(key: str, ttl: int) -> None:
        pass

    async def mock_delete(key: str) -> None:
        store.pop(key, None)
        hash_store.pop(key, None)
        counters.pop(key, None)

    async def mock_ping() -> bool:
        return True

    async def mock_hmget(key: str, *fields: str) -> list:
        h = hash_store.get(key, {})
        return [h.get(f) for f in fields]

    async def mock_hmset(key: str, mapping: dict) -> None:
        hash_store[key].update(mapping)

    async def mock_script_load(script: str) -> str:
        return "mock_sha"

    async def mock_evalsha(sha: str, numkeys: int, *args) -> int:
        # Simple mock: always allow
        return 1

    redis.get = mock_get
    redis.set = mock_set
    redis.setex = mock_setex
    redis.incr = mock_incr
    redis.expire = mock_expire
    redis.delete = mock_delete
    redis.ping = mock_ping
    redis.hmget = mock_hmget
    redis.hmset = mock_hmset
    redis.script_load = mock_script_load
    redis.evalsha = mock_evalsha
    redis._store = store
    redis._counters = counters
    redis._hash_store = hash_store
    return redis


@pytest.fixture
def mock_stripe():
    """Mock Stripe module."""
    mock = MagicMock()
    mock.Customer.create.return_value = {
        "id": "cus_test123",
        "email": "test@example.com",
        "name": "Test Tenant",
    }
    mock.Subscription.create.return_value = {
        "id": "sub_test123",
        "customer": "cus_test123",
        "status": "active",
    }
    mock.billing.MeterEvent.create.return_value = {
        "identifier": "evt_test123",
    }
    mock.checkout.Session.create.return_value = MagicMock(
        url="https://checkout.stripe.com/test_session"
    )
    return mock


@pytest.fixture
def test_tenant_id() -> str:
    return str(uuid4())


@pytest.fixture
def mock_db_session():
    """Mock database session factory."""
    session = AsyncMock()
    row = MagicMock()
    row.tenant_id = uuid4()
    row.scopes = ["read", "write"]
    result = MagicMock()
    result.fetchone.return_value = row
    session.execute = AsyncMock(return_value=result)

    class MockSessionFactory:
        def __call__(self):
            return self

        async def __aenter__(self):
            return session

        async def __aexit__(self, *args):
            pass

    return MockSessionFactory()
