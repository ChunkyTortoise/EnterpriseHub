"""
Redis Key Namespace Convention Helper.

This module provides utilities for building and parsing Redis keys
following a consistent namespace pattern across all EnterpriseHub products.

Key Pattern:
    {product}:{tenant_id}:{resource}:{key}

Examples:
    - jorge:tenant-abc123:lead:temp_score
    - contra:tenant-xyz789:project:cache:proj_001
    - certification:tenant-def456:user:progress:user_123

This namespace pattern ensures:
    1. Product isolation - keys are grouped by product
    2. Tenant isolation - multi-tenant data separation
    3. Resource grouping - logical grouping of related keys
    4. Easy scanning - SCAN commands can target specific namespaces
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class RedisKey:
    """
    Immutable representation of a Redis key with namespace components.
    
    Attributes:
        product: Product identifier (e.g., "jorge", "contra", "certification").
        tenant_id: UUID of the tenant.
        resource: Resource type (e.g., "lead", "project", "user").
        key: Specific key identifier.
    """
    
    product: str
    tenant_id: str
    resource: str
    key: str
    
    def __str__(self) -> str:
        """Convert to Redis key string format."""
        return f"{self.product}:{self.tenant_id}:{self.resource}:{self.key}"
    
    @property
    def product_prefix(self) -> str:
        """Get the product-level prefix for scanning."""
        return f"{self.product}:*"
    
    @property
    def tenant_prefix(self) -> str:
        """Get the tenant-level prefix for scanning."""
        return f"{self.product}:{self.tenant_id}:*"
    
    @property
    def resource_prefix(self) -> str:
        """Get the resource-level prefix for scanning."""
        return f"{self.product}:{self.tenant_id}:{self.resource}:*"


def build_key(
    product: str,
    tenant_id: str | UUID,
    resource: str,
    key: str,
) -> str:
    """
    Build a Redis key following the namespace convention.
    
    Args:
        product: Product identifier (e.g., "jorge", "contra").
        tenant_id: UUID of the tenant (string or UUID object).
        resource: Resource type (e.g., "lead", "project", "cache").
        key: Specific key identifier.
        
    Returns:
        Formatted Redis key string.
        
    Example:
        >>> build_key("jorge", "tenant-abc", "lead", "temp_score")
        'jorge:tenant-abc:lead:temp_score'
        
        >>> build_key("contra", UUID("12345678-1234-5678-1234-567812345678"), "project", "cache:proj_001")
        'contra:12345678-1234-5678-1234-567812345678:project:cache:proj_001'
    """
    # Convert UUID to string if needed
    tenant_str = str(tenant_id) if isinstance(tenant_id, UUID) else tenant_id
    
    # Validate components (no colons allowed in individual parts)
    if ":" in product:
        raise ValueError(f"Product '{product}' contains invalid colon separator")
    if ":" in tenant_str:
        # Allow colons in tenant_id for flexibility (some systems use composite IDs)
        pass
    if ":" in resource:
        raise ValueError(f"Resource '{resource}' contains invalid colon separator")
    
    return f"{product}:{tenant_str}:{resource}:{key}"


def parse_key(key: str) -> RedisKey:
    """
    Parse a Redis key string into its namespace components.
    
    Args:
        key: Redis key string to parse.
        
    Returns:
        RedisKey with extracted components.
        
    Raises:
        ValueError: If key doesn't match the expected format.
        
    Example:
        >>> parse_key("jorge:tenant-abc:lead:temp_score")
        RedisKey(product='jorge', tenant_id='tenant-abc', resource='lead', key='temp_score')
        
        >>> parse_key("contra:tenant-xyz:project:cache:proj_001")
        RedisKey(product='contra', tenant_id='tenant-xyz', resource='project', key='cache:proj_001')
    """
    parts = key.split(":", 3)  # Split into at most 4 parts
    
    if len(parts) < 4:
        raise ValueError(
            f"Invalid key format: '{key}'. "
            f"Expected format: {{product}}:{{tenant_id}}:{{resource}}:{{key}}"
        )
    
    return RedisKey(
        product=parts[0],
        tenant_id=parts[1],
        resource=parts[2],
        key=parts[3],
    )


def build_scan_pattern(
    product: Optional[str] = None,
    tenant_id: Optional[str | UUID] = None,
    resource: Optional[str] = None,
) -> str:
    """
    Build a SCAN pattern for matching Redis keys.
    
    Useful for finding all keys matching specific criteria.
    
    Args:
        product: Optional product filter.
        tenant_id: Optional tenant filter.
        resource: Optional resource filter.
        
    Returns:
        SCAN pattern string with wildcards for unspecified parts.
        
    Example:
        >>> build_scan_pattern(product="jorge")
        'jorge:*'
        
        >>> build_scan_pattern(product="jorge", tenant_id="tenant-abc")
        'jorge:tenant-abc:*'
        
        >>> build_scan_pattern(product="jorge", tenant_id="tenant-abc", resource="lead")
        'jorge:tenant-abc:lead:*'
    """
    if product is None:
        return "*"
    
    if tenant_id is None:
        return f"{product}:*"
    
    tenant_str = str(tenant_id) if isinstance(tenant_id, UUID) else tenant_id
    
    if resource is None:
        return f"{product}:{tenant_str}:*"
    
    return f"{product}:{tenant_str}:{resource}:*"


def build_ttl_key(
    product: str,
    tenant_id: str | UUID,
    resource: str,
    key: str,
    ttl_seconds: int,
) -> tuple[str, int]:
    """
    Build a Redis key with TTL metadata.
    
    Convenience function that returns both the key and TTL for
    use with Redis SETEX command.
    
    Args:
        product: Product identifier.
        tenant_id: UUID of the tenant.
        resource: Resource type.
        key: Specific key identifier.
        ttl_seconds: Time-to-live in seconds.
        
    Returns:
        Tuple of (key, ttl_seconds) for use with Redis.
        
    Example:
        >>> key, ttl = build_ttl_key("jorge", "tenant-abc", "cache", "temp", 3600)
        >>> await redis.setex(key, ttl, "value")
    """
    return build_key(product, tenant_id, resource, key), ttl_seconds


# Predefined product identifiers for consistency
PRODUCT_JORGE = "jorge"  # Real estate AI bots
PRODUCT_CONTRA = "contra"  # Contractor marketplace
PRODUCT_CERTIFICATION = "certification"  # Certification platform
PRODUCT_ANALYTICS = "analytics"  # Analytics service
PRODUCT_BILLING = "billing"  # Billing service


# Common resource types
RESOURCE_CACHE = "cache"
RESOURCE_SESSION = "session"
RESOURCE_RATE_LIMIT = "ratelimit"
RESOURCE_LOCK = "lock"
RESOURCE_QUEUE = "queue"
RESOURCE_COUNTER = "counter"
