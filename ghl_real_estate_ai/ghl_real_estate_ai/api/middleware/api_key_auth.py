"""
API Key Authentication Middleware
"""

from fastapi import Header, HTTPException, status
from typing import Optional
import os
import hashlib
import secrets

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
        """Verify an API key against stored hash."""
        if location_id not in API_KEYS_DB:
            return False
        
        hashed = APIKeyAuth.hash_api_key(api_key)
        return hashed == API_KEYS_DB[location_id]


async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    x_location_id: Optional[str] = Header(None)
):
    """Dependency to verify API key."""
    if not x_api_key or not x_location_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key and location ID required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if not APIKeyAuth.verify_api_key(x_api_key, x_location_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return {"location_id": x_location_id}
