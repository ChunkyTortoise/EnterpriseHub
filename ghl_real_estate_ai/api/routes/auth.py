"""
Authentication Routes
Provides login and token management endpoints
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ghl_real_estate_ai.api.middleware import (
    JWTAuth,
    get_current_user,
)

router = APIRouter(tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes


# User database - uses environment variables for security
# Production systems should use a proper database with encrypted storage
import os

def _get_users_db():
    """Get user database from environment variables."""
    users = {}

    # Get users from environment variables
    demo_user_hash = os.getenv("DEMO_USER_HASH")
    admin_user_hash = os.getenv("ADMIN_USER_HASH")

    if demo_user_hash:
        users["demo_user"] = demo_user_hash

    if admin_user_hash:
        users["admin"] = admin_user_hash

    # Fallback for development only (when no env vars set)
    if not users and os.getenv("ENVIRONMENT", "").lower() == "development":
        # Generate temporary hashes for development
        users = {
            "demo_user": JWTAuth.hash_password(os.getenv("DEMO_PASSWORD", "dev_demo_123")),
            "admin": JWTAuth.hash_password(os.getenv("ADMIN_PASSWORD", "dev_admin_456")),
        }

    return users

USERS_DB = _get_users_db()


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Authenticate user and return JWT token.

    Production deployment should configure user credentials via environment variables:
    - DEMO_USER_HASH: Bcrypt hash for demo_user account
    - ADMIN_USER_HASH: Bcrypt hash for admin account

    For development, set DEMO_PASSWORD and ADMIN_PASSWORD environment variables.
    """
    # Verify user exists
    if credentials.username not in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Verify password
    if not JWTAuth.verify_password(
        credentials.password, USERS_DB[credentials.username]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Create access token
    access_token = JWTAuth.create_access_token(
        data={"sub": credentials.username}, expires_delta=timedelta(minutes=30)
    )

    return TokenResponse(
        access_token=access_token, token_type="bearer", expires_in=1800
    )


@router.post("/token", response_model=TokenResponse)
async def get_token(credentials: LoginRequest):
    """
    Alternative token endpoint (OAuth2 compatible).
    """
    return await login(credentials)


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Requires valid JWT token in Authorization header.
    """
    return {"user_id": current_user["user_id"], "authenticated": True}
