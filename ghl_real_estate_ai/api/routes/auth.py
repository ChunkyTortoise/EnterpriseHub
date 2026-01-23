"""
Authentication Routes
Provides login and token management endpoints
"""

import os
from datetime import timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv

from ghl_real_estate_ai.api.middleware import (
    JWTAuth,
    get_current_user,
)

load_dotenv()
logger = logging.getLogger(__name__)

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


# Load credentials from environment variables
DEMO_USER_HASH = os.getenv("AUTH_DEMO_USER_HASH")
ADMIN_USER_HASH = os.getenv("AUTH_ADMIN_USER_HASH")

if not DEMO_USER_HASH or not ADMIN_USER_HASH:
    logger.warning("⚠️ using default hardcoded credentials for demo/admin. Set AUTH_DEMO_USER_HASH and AUTH_ADMIN_USER_HASH in .env for production.")

USERS_DB = {
    "demo_user": DEMO_USER_HASH or "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVLXhKvNe",  # nosemgrep: generic.secrets.security.detected-bcrypt-hash.detected-bcrypt-hash
    "admin": ADMIN_USER_HASH or "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # nosemgrep: generic.secrets.security.detected-bcrypt-hash.detected-bcrypt-hash
}


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Authenticate user and return JWT token.

    Default demo credentials:
    - username: demo_user, password: demo_password
    - username: admin, password: admin_password
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
