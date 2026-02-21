"""
Shared Pydantic Base Models for Multi-Tenant Infrastructure.

This module provides foundational models used across all EnterpriseHub products
for tenant isolation, API key management, and usage tracking.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class TenantBase(BaseModel):
    """
    Base model for all tenant-scoped entities.

    Provides common fields for multi-tenant data isolation including
    tenant identification and audit timestamps.

    Attributes:
        tenant_id: UUID identifying the tenant this record belongs to.
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last modified.

    Example:
        class User(TenantBase):
            email: str
            name: str
    """

    tenant_id: UUID = Field(..., description="Unique identifier for the tenant this record belongs to")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the record was created")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when the record was last modified"
    )

    def touch(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.utcnow()


class APIKeyBase(BaseModel):
    """
    Model for API key management and authentication.

    Stores API key information for tenant authentication including
    the hashed key value, metadata, and access controls.

    Attributes:
        key_id: Unique identifier for this API key.
        tenant_id: UUID of the tenant this key belongs to.
        key_hash: SHA256 hash of the actual API key (never store raw key).
        prefix: First 8 characters of the key for identification purposes.
        name: Human-readable name for the API key.
        scopes: List of permission scopes granted to this key.
        rate_limit_per_minute: Maximum requests per minute allowed.
        is_active: Whether this key is currently active.
        expires_at: Optional expiration timestamp for the key.

    Example:
        key = APIKeyBase(
            key_id=uuid4(),
            tenant_id=tenant_uuid,
            key_hash=hashlib.sha256(api_key.encode()).hexdigest(),
            prefix=api_key[:8],
            name="Production API Key",
            scopes=["read", "write"],
            rate_limit_per_minute=100
        )
    """

    key_id: UUID = Field(default_factory=uuid4, description="Unique identifier for this API key")
    tenant_id: UUID = Field(..., description="UUID of the tenant this key belongs to")
    key_hash: str = Field(..., min_length=64, max_length=64, description="SHA256 hash of the actual API key")
    prefix: str = Field(..., min_length=8, max_length=8, description="First 8 characters of the key for identification")
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable name for the API key")
    scopes: list[str] = Field(default_factory=list, description="List of permission scopes granted to this key")
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000, description="Maximum requests per minute allowed")
    is_active: bool = Field(default=True, description="Whether this key is currently active")
    expires_at: Optional[datetime] = Field(default=None, description="Optional expiration timestamp for the key")

    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def has_scope(self, scope: str) -> bool:
        """Check if the key has a specific permission scope."""
        return scope in self.scopes

    def verify_hash(self, key_value: str) -> bool:
        """
        Verify a raw key value against the stored hash.

        Args:
            key_value: The raw API key to verify.

        Returns:
            True if the key matches the stored hash.
        """
        import hashlib

        return hashlib.sha256(key_value.encode()).hexdigest() == self.key_hash


class UsageRecord(BaseModel):
    """
    Model for tracking resource usage per tenant.

    Records usage events for billing, rate limiting, and analytics
    across all EnterpriseHub products.

    Attributes:
        tenant_id: UUID of the tenant consuming resources.
        resource_type: Type of resource being consumed (e.g., "api_calls", "storage_gb").
        quantity: Amount of the resource consumed.
        timestamp: When the usage occurred.
        metadata: Additional context about the usage event.

    Example:
        record = UsageRecord(
            tenant_id=tenant_uuid,
            resource_type="api_calls",
            quantity=1,
            metadata={"endpoint": "/v1/chat", "model": "claude-3"}
        )
    """

    tenant_id: UUID = Field(..., description="UUID of the tenant consuming resources")
    resource_type: str = Field(..., min_length=1, max_length=100, description="Type of resource being consumed")
    quantity: float = Field(..., ge=0, description="Amount of the resource consumed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the usage occurred")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context about the usage event")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )
