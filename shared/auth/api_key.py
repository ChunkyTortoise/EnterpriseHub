"""
API Key Authentication for FastAPI.

This module provides FastAPI dependencies for API key verification
with SHA256 hash comparison and database lookup.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyData(BaseModel):
    """
    Validated API key data returned after successful authentication.

    Attributes:
        key_id: Unique identifier for the API key.
        tenant_id: UUID of the tenant this key belongs to.
        name: Human-readable name for the key.
        scopes: List of permission scopes granted.
        rate_limit_per_minute: Rate limit for this key.
    """

    key_id: str = Field(..., description="Unique identifier for the API key")
    tenant_id: str = Field(..., description="UUID of the tenant")
    name: str = Field(..., description="Human-readable name")
    scopes: list[str] = Field(default_factory=list, description="Permission scopes")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")


@dataclass
class APIKeyDependency:
    """
    FastAPI dependency for API key authentication.

    Provides a reusable dependency that validates API keys against
    a database using prefix + hash matching.

    Attributes:
        required_scopes: List of scopes required to access the endpoint.

    Example:
        @app.get("/protected")
        async def protected_endpoint(
            api_key: APIKeyData = Depends(APIKeyDependency(scopes=["read"]))
        ):
            return {"tenant_id": api_key.tenant_id}
    """

    required_scopes: Optional[list[str]] = None

    async def __call__(self, api_key: Optional[str] = Depends(api_key_header)) -> APIKeyData:
        """
        Validate the API key and return key data.

        Args:
            api_key: The raw API key from the X-API-Key header.

        Returns:
            APIKeyData with validated key information.

        Raises:
            HTTPException: 401 if key is missing, invalid, or lacks required scopes.
        """
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required. Provide X-API-Key header.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # Validate key format (prefix_key format)
        if len(api_key) < 16:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # Extract prefix (first 8 characters)
        prefix = api_key[:8]

        # Hash the key for comparison
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Look up the key in the database
        key_data = await _lookup_api_key(prefix, key_hash)

        if key_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # Check if key is active
        if not key_data.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is disabled.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # Check expiration
        expires_at = key_data.get("expires_at")
        if expires_at and datetime.utcnow() > expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # Check required scopes
        if self.required_scopes:
            key_scopes = set(key_data.get("scopes", []))
            required = set(self.required_scopes)
            if not required.issubset(key_scopes):
                missing = required - key_scopes
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Missing required scopes: {', '.join(missing)}",
                    headers={"WWW-Authenticate": "ApiKey"},
                )

        return APIKeyData(
            key_id=str(key_data["key_id"]),
            tenant_id=str(key_data["tenant_id"]),
            name=key_data["name"],
            scopes=key_data.get("scopes", []),
            rate_limit_per_minute=key_data.get("rate_limit_per_minute", 60),
        )


async def verify_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    required_scopes: Optional[list[str]] = None,
) -> APIKeyData:
    """
    FastAPI dependency for API key verification.

    Validates the X-API-Key header against stored API keys using
    SHA256 hash comparison with prefix-based lookup.

    Args:
        api_key: The raw API key from the request header.
        required_scopes: Optional list of scopes required for access.

    Returns:
        APIKeyData with validated key information.

    Raises:
        HTTPException: 401 Unauthorized for invalid, expired, or insufficient scopes.

    Example:
        @app.get("/users")
        async def list_users(api_key: APIKeyData = Depends(verify_api_key)):
            # api_key.tenant_id contains the authenticated tenant
            return {"tenant": api_key.tenant_id}

        @app.post("/users")
        async def create_user(
            api_key: APIKeyData = Depends(lambda: verify_api_key(required_scopes=["write"]))
        ):
            return {"created": True}
    """
    dependency = APIKeyDependency(required_scopes=required_scopes)
    return await dependency(api_key)


async def _lookup_api_key(prefix: str, key_hash: str) -> Optional[dict]:
    """
    Look up an API key in the database by prefix and hash.

    This is a placeholder implementation. In production, this should
    query the database table storing API keys.

    Args:
        prefix: First 8 characters of the API key.
        key_hash: SHA256 hash of the full API key.

    Returns:
        Dictionary with key data if found and valid, None otherwise.

    Note:
        Implement this function to query your database:

        SELECT key_id, tenant_id, key_hash, name, scopes,
               rate_limit_per_minute, is_active, expires_at
        FROM api_keys
        WHERE prefix = :prefix AND key_hash = :key_hash
    """
    # Placeholder - implement actual database lookup
    # Example implementation:
    # from sqlalchemy import select
    # from shared.database import get_session
    # from shared.models.api_key import APIKey
    #
    # async with get_session() as session:
    #     stmt = select(APIKey).where(
    #         APIKey.prefix == prefix,
    #         APIKey.key_hash == key_hash
    #     )
    #     result = await session.execute(stmt)
    #     key = result.scalar_one_or_none()
    #     if key:
    #         return {
    #             "key_id": key.key_id,
    #             "tenant_id": key.tenant_id,
    #             "name": key.name,
    #             "scopes": key.scopes,
    #             "rate_limit_per_minute": key.rate_limit_per_minute,
    #             "is_active": key.is_active,
    #             "expires_at": key.expires_at,
    #         }
    #     return None

    raise NotImplementedError(
        "API key database lookup not implemented. Implement _lookup_api_key() to query your api_keys table."
    )
