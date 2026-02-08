"""
API Key Authentication Middleware
"""

import hashlib
import hmac
import os
import secrets
from typing import Optional

from fastapi import Header, HTTPException, status

# Store API keys in environment or database
# Format: location_id -> hashed_api_key
API_KEYS_DB = {}  # In production, use a database


class APIKeyAuth:
    """API Key authentication handler."""

    @staticmethod
    def generate_api_key() -> str:
        """Generate a new API key."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def verify_api_key(api_key: str, location_id: str) -> bool:
        """Verify an API key against stored hash.

        Uses constant-time comparison to prevent timing attacks.
        """
        if location_id not in API_KEYS_DB:
            return False

        hashed = APIKeyAuth.hash_api_key(api_key)
        stored_hash = API_KEYS_DB[location_id]

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(hashed, stored_hash)


async def verify_api_key(x_api_key: Optional[str] = Header(None), x_location_id: Optional[str] = Header(None)):
    """Dependency to verify API key."""
    if not x_api_key or not x_location_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key and location ID required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not APIKeyAuth.verify_api_key(x_api_key, x_location_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")

    return {"location_id": x_location_id}
