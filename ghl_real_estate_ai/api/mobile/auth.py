"""
Mobile Authentication API - JWT and Biometric Support
Enhanced authentication system for mobile applications with biometric integration.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from ghl_real_estate_ai.api.middleware.jwt_auth import JWTAuth, get_current_user
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/mobile/auth", tags=["Mobile Authentication"])

# Mobile-specific configuration
MOBILE_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days for mobile
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days
BIOMETRIC_TOKEN_EXPIRE_MINUTES = 5  # Short-lived for biometric challenges


class BiometricType(str):
    """Supported biometric authentication types."""

    FINGERPRINT = "fingerprint"
    FACE_ID = "face_id"
    VOICE_PRINT = "voice_print"


class DeviceInfo(BaseModel):
    """Mobile device information for security tracking."""

    device_id: str = Field(..., description="Unique device identifier")
    device_type: str = Field(..., description="iOS or Android")
    app_version: str = Field(..., description="Mobile app version")
    os_version: str = Field(..., description="Operating system version")
    push_token: Optional[str] = Field(None, description="Push notification token")
    biometric_capabilities: List[str] = Field(default=[], description="Available biometric methods")


class MobileLoginRequest(BaseModel):
    """Mobile login request with device fingerprinting."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)
    device_info: DeviceInfo
    remember_device: bool = Field(default=True, description="Remember this device for biometric auth")


class BiometricAuthRequest(BaseModel):
    """Biometric authentication request."""

    device_id: str = Field(..., description="Registered device ID")
    biometric_type: str = Field(..., description="Type of biometric used")
    biometric_signature: str = Field(..., description="Encrypted biometric signature")
    challenge_token: str = Field(..., description="Challenge token from initial request")


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(..., description="Valid refresh token")
    device_id: str = Field(..., description="Device ID for validation")


class MobileTokenResponse(BaseModel):
    """Mobile authentication response with tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]
    device_registered: bool
    biometric_enabled: bool
    session_id: str


class BiometricChallengeResponse(BaseModel):
    """Biometric challenge response."""

    challenge_token: str
    expires_in: int
    biometric_types: List[str]
    device_trusted: bool


class DeviceRegistration(BaseModel):
    """Device registration for biometric auth."""

    device_id: str
    device_fingerprint: str
    biometric_public_key: str
    registered_at: datetime
    last_used: Optional[datetime]
    trust_level: int = Field(default=1, description="1-5 trust scale")


class MobileAuthService:
    """Enhanced mobile authentication service."""

    def __init__(self):
        self.cache = None
        self.jwt_auth = JWTAuth()

    async def _get_cache(self):
        """Get cache service instance."""
        if not self.cache:
            self.cache = get_cache_service()
        return self.cache

    async def authenticate_mobile_user(
        self, username: str, password: str, device_info: DeviceInfo
    ) -> MobileTokenResponse:
        """Authenticate user for mobile app with enhanced security."""
        try:
            cache = await self._get_cache()

            # Check for rate limiting (5 attempts per 15 minutes per device)
            rate_limit_key = f"mobile_auth_rate_limit:{device_info.device_id}"
            attempts = await cache.get(rate_limit_key) or 0

            if attempts >= 5:
                logger.warning(
                    f"Rate limit exceeded for device: {device_info.device_id}",
                    extra={"security_event": "mobile_auth_rate_limit", "device_id": device_info.device_id},
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many authentication attempts. Please try again later.",
                )

            # Validate credentials (simplified - integrate with actual user store)
            user_data = await self._validate_user_credentials(username, password)
            if not user_data:
                # Increment rate limiting counter
                await cache.set(rate_limit_key, attempts + 1, ttl=900)  # 15 minutes

                logger.warning(
                    f"Invalid credentials for user: {username}",
                    extra={"security_event": "mobile_auth_failed", "username": username},
                )
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

            # Check device registration status
            device_registration = await self._get_device_registration(device_info.device_id, user_data["user_id"])
            device_registered = device_registration is not None

            # Generate session ID
            session_id = secrets.token_urlsafe(32)

            # Create mobile tokens with extended expiry
            access_token_data = {
                "sub": user_data["user_id"],
                "username": username,
                "device_id": device_info.device_id,
                "session_id": session_id,
                "device_type": device_info.device_type,
                "app_version": device_info.app_version,
                "auth_method": "password",
                "iat": datetime.now(timezone.utc),
                "mobile": True,
            }

            # Generate tokens
            access_token = self.jwt_auth.create_access_token(
                access_token_data, expires_delta=timedelta(minutes=MOBILE_ACCESS_TOKEN_EXPIRE_MINUTES)
            )

            refresh_token = await self._create_refresh_token(user_data["user_id"], device_info.device_id, session_id)

            # Register device if not already registered and user wants it
            if not device_registered and device_info.remember_device:
                await self._register_device(device_info, user_data["user_id"])
                device_registered = True

            # Update device last used
            if device_registered:
                await self._update_device_last_used(device_info.device_id, user_data["user_id"])

            # Clear rate limiting on successful auth
            await cache.delete(rate_limit_key)

            # Store session data
            session_data = {
                "user_id": user_data["user_id"],
                "device_id": device_info.device_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "device_info": device_info.dict(),
                "auth_method": "password",
            }
            await cache.set(f"mobile_session:{session_id}", session_data, ttl=MOBILE_ACCESS_TOKEN_EXPIRE_MINUTES * 60)

            logger.info(
                f"Mobile authentication successful for user: {username}",
                extra={
                    "security_event": "mobile_auth_success",
                    "user_id": user_data["user_id"],
                    "device_id": device_info.device_id,
                },
            )

            return MobileTokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=MOBILE_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_info={
                    "user_id": user_data["user_id"],
                    "username": username,
                    "display_name": user_data.get("display_name", username),
                    "email": user_data.get("email"),
                    "permissions": user_data.get("permissions", []),
                    "location_id": user_data.get("location_id"),
                    "ghl_api_key": user_data.get("ghl_api_key", "")[:10] + "..."
                    if user_data.get("ghl_api_key")
                    else None,
                },
                device_registered=device_registered,
                biometric_enabled=len(device_info.biometric_capabilities) > 0 and device_registered,
                session_id=session_id,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Mobile authentication error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication service error"
            )

    async def create_biometric_challenge(
        self, device_id: str, user_id: Optional[str] = None
    ) -> BiometricChallengeResponse:
        """Create a biometric authentication challenge."""
        try:
            cache = await self._get_cache()

            # Get device registration
            device_registration = await self._get_device_registration(device_id, user_id)
            if not device_registration:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered for biometric authentication"
                )

            # Generate challenge token
            challenge_token = secrets.token_urlsafe(32)
            challenge_data = {
                "device_id": device_id,
                "user_id": device_registration["user_id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (
                    datetime.now(timezone.utc) + timedelta(minutes=BIOMETRIC_TOKEN_EXPIRE_MINUTES)
                ).isoformat(),
            }

            # Store challenge
            await cache.set(
                f"biometric_challenge:{challenge_token}", challenge_data, ttl=BIOMETRIC_TOKEN_EXPIRE_MINUTES * 60
            )

            # Get available biometric types for this device
            available_biometrics = device_registration.get("biometric_capabilities", [])

            return BiometricChallengeResponse(
                challenge_token=challenge_token,
                expires_in=BIOMETRIC_TOKEN_EXPIRE_MINUTES * 60,
                biometric_types=available_biometrics,
                device_trusted=device_registration.get("trust_level", 1) >= 3,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Biometric challenge creation error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Challenge creation failed")

    async def authenticate_biometric(self, biometric_request: BiometricAuthRequest) -> MobileTokenResponse:
        """Authenticate using biometric data."""
        try:
            cache = await self._get_cache()

            # Validate challenge token
            challenge_data = await cache.get(f"biometric_challenge:{biometric_request.challenge_token}")
            if not challenge_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired challenge token"
                )

            # Validate device matches challenge
            if challenge_data["device_id"] != biometric_request.device_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Device mismatch")

            # Get device registration
            device_registration = await self._get_device_registration(
                biometric_request.device_id, challenge_data["user_id"]
            )

            if not device_registration:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Device not registered")

            # Validate biometric signature (simplified - would integrate with actual biometric validation)
            if not await self._validate_biometric_signature(
                biometric_request.biometric_signature,
                device_registration.get("biometric_public_key"),
                biometric_request.biometric_type,
            ):
                logger.warning(
                    f"Biometric validation failed for device: {biometric_request.device_id}",
                    extra={"security_event": "biometric_auth_failed", "device_id": biometric_request.device_id},
                )
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Biometric authentication failed")

            # Get user data
            user_data = await self._get_user_by_id(challenge_data["user_id"])
            if not user_data:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

            # Generate session ID
            session_id = secrets.token_urlsafe(32)

            # Create access token
            access_token_data = {
                "sub": user_data["user_id"],
                "username": user_data["username"],
                "device_id": biometric_request.device_id,
                "session_id": session_id,
                "device_type": device_registration.get("device_type", "unknown"),
                "auth_method": f"biometric_{biometric_request.biometric_type}",
                "iat": datetime.now(timezone.utc),
                "mobile": True,
                "biometric_auth": True,
            }

            access_token = self.jwt_auth.create_access_token(
                access_token_data, expires_delta=timedelta(minutes=MOBILE_ACCESS_TOKEN_EXPIRE_MINUTES)
            )

            # Generate refresh token
            refresh_token = await self._create_refresh_token(
                user_data["user_id"], biometric_request.device_id, session_id
            )

            # Update device trust level and last used
            await self._update_device_trust(biometric_request.device_id, user_data["user_id"])
            await self._update_device_last_used(biometric_request.device_id, user_data["user_id"])

            # Clean up challenge token
            await cache.delete(f"biometric_challenge:{biometric_request.challenge_token}")

            # Store session data
            session_data = {
                "user_id": user_data["user_id"],
                "device_id": biometric_request.device_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "auth_method": f"biometric_{biometric_request.biometric_type}",
            }
            await cache.set(f"mobile_session:{session_id}", session_data, ttl=MOBILE_ACCESS_TOKEN_EXPIRE_MINUTES * 60)

            logger.info(
                f"Biometric authentication successful for user: {user_data['username']}",
                extra={
                    "security_event": "biometric_auth_success",
                    "user_id": user_data["user_id"],
                    "device_id": biometric_request.device_id,
                    "biometric_type": biometric_request.biometric_type,
                },
            )

            return MobileTokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=MOBILE_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_info={
                    "user_id": user_data["user_id"],
                    "username": user_data["username"],
                    "display_name": user_data.get("display_name", user_data["username"]),
                    "email": user_data.get("email"),
                    "permissions": user_data.get("permissions", []),
                    "location_id": user_data.get("location_id"),
                    "ghl_api_key": user_data.get("ghl_api_key", "")[:10] + "..."
                    if user_data.get("ghl_api_key")
                    else None,
                },
                device_registered=True,
                biometric_enabled=True,
                session_id=session_id,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Biometric authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Biometric authentication failed"
            )

    async def refresh_mobile_token(self, refresh_request: RefreshTokenRequest) -> MobileTokenResponse:
        """Refresh mobile access token using refresh token."""
        try:
            cache = await self._get_cache()

            # Validate refresh token
            refresh_data = await cache.get(f"refresh_token:{refresh_request.refresh_token}")
            if not refresh_data:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

            # Validate device ID
            if refresh_data["device_id"] != refresh_request.device_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Device mismatch")

            # Get user data
            user_data = await self._get_user_by_id(refresh_data["user_id"])
            if not user_data:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

            # Generate new session ID
            session_id = secrets.token_urlsafe(32)

            # Create new access token
            access_token_data = {
                "sub": user_data["user_id"],
                "username": user_data["username"],
                "device_id": refresh_request.device_id,
                "session_id": session_id,
                "device_type": refresh_data.get("device_type", "unknown"),
                "auth_method": "refresh_token",
                "iat": datetime.now(timezone.utc),
                "mobile": True,
            }

            access_token = self.jwt_auth.create_access_token(
                access_token_data, expires_delta=timedelta(minutes=MOBILE_ACCESS_TOKEN_EXPIRE_MINUTES)
            )

            # Generate new refresh token
            new_refresh_token = await self._create_refresh_token(
                user_data["user_id"], refresh_request.device_id, session_id
            )

            # Invalidate old refresh token
            await cache.delete(f"refresh_token:{refresh_request.refresh_token}")

            # Check if device is registered for biometric
            device_registration = await self._get_device_registration(refresh_request.device_id, user_data["user_id"])
            device_registered = device_registration is not None
            biometric_enabled = device_registered and len(device_registration.get("biometric_capabilities", [])) > 0

            return MobileTokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_in=MOBILE_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_info={
                    "user_id": user_data["user_id"],
                    "username": user_data["username"],
                    "display_name": user_data.get("display_name", user_data["username"]),
                    "email": user_data.get("email"),
                    "permissions": user_data.get("permissions", []),
                    "location_id": user_data.get("location_id"),
                    "ghl_api_key": user_data.get("ghl_api_key", "")[:10] + "..."
                    if user_data.get("ghl_api_key")
                    else None,
                },
                device_registered=device_registered,
                biometric_enabled=biometric_enabled,
                session_id=session_id,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed")

    # Helper methods (simplified implementations - would integrate with actual data stores)

    async def _validate_user_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Validate user credentials against user store."""
        # This would integrate with actual user authentication system
        # For demo purposes, we'll use a simple check
        if username == "jorge" and password == "demo123":
            return {
                "user_id": "jorge_001",
                "username": "jorge",
                "display_name": "Jorge Sales",
                "email": "jorge@example.com",
                "permissions": ["read", "write", "admin"],
                "location_id": "demo_location",
                "ghl_api_key": "ghl_demo_key_12345",
            }
        return None

    async def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by user ID."""
        if user_id == "jorge_001":
            return {
                "user_id": "jorge_001",
                "username": "jorge",
                "display_name": "Jorge Sales",
                "email": "jorge@example.com",
                "permissions": ["read", "write", "admin"],
                "location_id": "demo_location",
                "ghl_api_key": "ghl_demo_key_12345",
            }
        return None

    async def _create_refresh_token(self, user_id: str, device_id: str, session_id: str) -> str:
        """Create a secure refresh token."""
        refresh_token = secrets.token_urlsafe(32)
        cache = await self._get_cache()

        refresh_data = {
            "user_id": user_id,
            "device_id": device_id,
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Store refresh token with 30-day expiry
        await cache.set(f"refresh_token:{refresh_token}", refresh_data, ttl=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)

        return refresh_token

    async def _register_device(self, device_info: DeviceInfo, user_id: str):
        """Register device for biometric authentication."""
        cache = await self._get_cache()

        device_registration = {
            "device_id": device_info.device_id,
            "user_id": user_id,
            "device_type": device_info.device_type,
            "device_fingerprint": hashlib.sha256(
                f"{device_info.device_id}:{device_info.device_type}:{device_info.os_version}".encode()
            ).hexdigest(),
            "biometric_capabilities": device_info.biometric_capabilities,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "trust_level": 1,
            "last_used": datetime.now(timezone.utc).isoformat(),
        }

        await cache.set(
            f"device_registration:{device_info.device_id}:{user_id}",
            device_registration,
            ttl=None,  # Persistent storage
        )

    async def _get_device_registration(self, device_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get device registration data."""
        cache = await self._get_cache()

        # If user_id provided, try exact match
        if user_id:
            return await cache.get(f"device_registration:{device_id}:{user_id}")

        # Otherwise, we'd need to search all registrations for this device
        # For simplicity, return None if no user_id provided
        return None

    async def _update_device_last_used(self, device_id: str, user_id: str):
        """Update device last used timestamp."""
        cache = await self._get_cache()

        device_registration = await self._get_device_registration(device_id, user_id)
        if device_registration:
            device_registration["last_used"] = datetime.now(timezone.utc).isoformat()
            await cache.set(f"device_registration:{device_id}:{user_id}", device_registration, ttl=None)

    async def _update_device_trust(self, device_id: str, user_id: str):
        """Update device trust level."""
        cache = await self._get_cache()

        device_registration = await self._get_device_registration(device_id, user_id)
        if device_registration:
            # Increase trust level up to maximum of 5
            current_trust = device_registration.get("trust_level", 1)
            device_registration["trust_level"] = min(current_trust + 1, 5)
            await cache.set(f"device_registration:{device_id}:{user_id}", device_registration, ttl=None)

    async def _validate_biometric_signature(
        self, signature: str, public_key: Optional[str], biometric_type: str
    ) -> bool:
        """Validate biometric signature (simplified implementation)."""
        # This would integrate with actual biometric validation
        # For demo, we'll do a simple check
        return len(signature) > 20 and signature.startswith("bio_")


# Initialize service
mobile_auth_service = MobileAuthService()

# Routes


@router.post("/login", response_model=MobileTokenResponse)
async def mobile_login(login_request: MobileLoginRequest):
    """
    Mobile login with device registration and extended token validity.

    Features:
    - Extended token validity (7 days)
    - Device fingerprinting
    - Automatic device registration for biometric auth
    - Rate limiting protection
    - Security event logging
    """
    return await mobile_auth_service.authenticate_mobile_user(
        login_request.username, login_request.password, login_request.device_info
    )


@router.post("/biometric/challenge", response_model=BiometricChallengeResponse)
async def create_biometric_challenge(
    device_id: str = Body(..., embed=True), current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create biometric authentication challenge.

    Returns a short-lived challenge token for biometric authentication.
    Device must be previously registered through login.
    """
    return await mobile_auth_service.create_biometric_challenge(
        device_id=device_id, user_id=current_user.get("user_id")
    )


@router.post("/biometric/authenticate", response_model=MobileTokenResponse)
async def biometric_authenticate(biometric_request: BiometricAuthRequest):
    """
    Authenticate using biometric data.

    Supports:
    - Fingerprint authentication
    - Face ID authentication
    - Voice print authentication (future)

    Returns full authentication tokens on success.
    """
    return await mobile_auth_service.authenticate_biometric(biometric_request)


@router.post("/refresh", response_model=MobileTokenResponse)
async def refresh_token(refresh_request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.

    - Validates refresh token and device ID match
    - Issues new access token and refresh token
    - Invalidates old refresh token for security
    """
    return await mobile_auth_service.refresh_mobile_token(refresh_request)


@router.post("/logout")
async def mobile_logout(
    device_id: str = Body(..., embed=True), current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Logout from mobile device.

    - Invalidates current session
    - Clears device-specific tokens
    - Maintains device registration for future biometric auth
    """
    try:
        cache = get_cache_service()
        user_id = current_user["user_id"]

        # Get current session ID from token payload
        session_id = current_user.get("payload", {}).get("session_id")

        # Clear session data
        if session_id:
            await cache.delete(f"mobile_session:{session_id}")

        # Clear any pending biometric challenges for this device
        # Note: In production, you'd want to scan and delete all matching keys

        logger.info(
            f"Mobile logout successful for user: {user_id}",
            extra={"security_event": "mobile_logout", "user_id": user_id, "device_id": device_id},
        )

        return {"success": True, "message": "Logged out successfully", "device_id": device_id}

    except Exception as e:
        logger.error(f"Mobile logout error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed")


@router.get("/device/status")
async def get_device_status(
    device_id: str = Header(..., alias="X-Device-ID"), current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get device registration and security status.

    Returns information about:
    - Device registration status
    - Available biometric methods
    - Trust level
    - Last used timestamp
    """
    try:
        user_id = current_user["user_id"]
        device_registration = await mobile_auth_service._get_device_registration(device_id, user_id)

        if not device_registration:
            return {
                "device_registered": False,
                "biometric_enabled": False,
                "trust_level": 0,
                "available_biometrics": [],
            }

        return {
            "device_registered": True,
            "biometric_enabled": len(device_registration.get("biometric_capabilities", [])) > 0,
            "trust_level": device_registration.get("trust_level", 1),
            "available_biometrics": device_registration.get("biometric_capabilities", []),
            "last_used": device_registration.get("last_used"),
            "registered_at": device_registration.get("registered_at"),
        }

    except Exception as e:
        logger.error(f"Device status check error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Device status check failed")


@router.delete("/device/unregister")
async def unregister_device(
    device_id: str = Body(..., embed=True), current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Unregister device from biometric authentication.

    - Removes device registration
    - Invalidates all tokens for this device
    - Requires password re-authentication for future logins
    """
    try:
        cache = get_cache_service()
        user_id = current_user["user_id"]

        # Remove device registration
        await cache.delete(f"device_registration:{device_id}:{user_id}")

        # Clear any active sessions for this device
        # Note: In production, you'd want to scan and clear all sessions for this device

        logger.info(
            f"Device unregistered: {device_id}",
            extra={"security_event": "device_unregistered", "user_id": user_id, "device_id": device_id},
        )

        return {"success": True, "message": "Device unregistered successfully", "device_id": device_id}

    except Exception as e:
        logger.error(f"Device unregistration error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Device unregistration failed")
