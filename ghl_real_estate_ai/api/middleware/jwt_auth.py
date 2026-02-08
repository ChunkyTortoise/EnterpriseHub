"""
JWT Authentication Middleware
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# Configuration - CRITICAL SECURITY FIX
# No weak fallback secrets allowed - this was a major security vulnerability
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    # CRITICAL: Never allow weak fallback secrets in any environment
    error_msg = "JWT_SECRET_KEY environment variable must be set for security. No fallback allowed."
    print(f"SECURITY ERROR: {error_msg}")
    raise ValueError(error_msg)
# Security configuration - enforce strong settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security validation for JWT secret
if len(SECRET_KEY) < 32:
    error_msg = f"JWT_SECRET_KEY must be at least 32 characters for security. Current length: {len(SECRET_KEY)}"
    print(f"SECURITY ERROR: {error_msg}")
    raise ValueError(error_msg)

security = HTTPBearer()


class JWTAuth:
    """Enhanced JWT Authentication handler with token rotation and security features."""

    @staticmethod
    def create_access_token(
        data: dict, expires_delta: Optional[timedelta] = None, include_refresh_token: bool = False
    ) -> Union[str, tuple[str, str]]:
        """
        Create a new JWT token with enhanced security.

        Args:
            data: Token payload data
            expires_delta: Custom expiration time
            include_refresh_token: Whether to return refresh token as well

        Returns:
            Access token string, or tuple of (access_token, refresh_token)
        """
        # Add security metadata
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

        # Enhanced payload with security features
        to_encode.update(
            {
                "exp": expire,
                "iat": now,  # Issued at time
                "nbf": now,  # Not before time
                "jti": uuid.uuid4().hex[:16],  # JWT ID for revocation tracking
                "token_type": "access",
            }
        )

        access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        if include_refresh_token:
            # Create refresh token with longer expiration
            refresh_data = {
                "sub": data.get("sub"),
                "exp": now + timedelta(days=7),  # 7 days for refresh
                "iat": now,
                "jti": uuid.uuid4().hex[:16],
                "token_type": "refresh",
            }
            refresh_token = jwt.encode(refresh_data, SECRET_KEY, algorithm=ALGORITHM)
            return access_token, refresh_token

        return access_token

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create a dedicated refresh token."""
        now = datetime.now(timezone.utc)
        refresh_data = {
            "sub": user_id,
            "exp": now + timedelta(days=7),
            "iat": now,
            "jti": uuid.uuid4().hex[:16],
            "token_type": "refresh",
        }
        return jwt.encode(refresh_data, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """
        Create new access token from valid refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token

        Raises:
            HTTPException: If refresh token is invalid or expired
        """
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

            # Validate token type
            if payload.get("token_type") != "refresh":
                logger.error(
                    "Invalid token type for refresh",
                    extra={"security_event": "invalid_refresh_token_type", "error_id": "JWT_006"},
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token type",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Create new access token
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")

            new_access_token = JWTAuth.create_access_token({"sub": user_id})

            logger.info(
                "Access token refreshed successfully",
                extra={"security_event": "token_refreshed", "user_id": user_id, "event_id": "JWT_007"},
            )

            return new_access_token

        except jwt.ExpiredSignatureError:
            logger.warning(
                "Expired refresh token used", extra={"security_event": "expired_refresh_token", "error_id": "JWT_008"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            logger.error(
                f"Invalid refresh token: {str(e)}",
                extra={"security_event": "invalid_refresh_token", "error_id": "JWT_009"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verify and decode JWT token.

        CRITICAL SECURITY FIX: Enhanced validation and security logging.

        Args:
            token: JWT token string to verify

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid, expired, or malformed
        """
        if not token or not isinstance(token, str):
            logger.error(
                "Invalid token format provided",
                extra={"security_event": "jwt_verification_failed", "error_id": "JWT_001"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Validate required fields
            if "sub" not in payload:
                logger.error(
                    "Token missing required subject field",
                    extra={"security_event": "jwt_verification_failed", "error_id": "JWT_002"},
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token structure",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Check if token is expired (additional validation beyond jwt.decode)
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                logger.warning(
                    "Expired token presented", extra={"security_event": "jwt_token_expired", "error_id": "JWT_003"}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            logger.info(
                "JWT token successfully verified",
                extra={"security_event": "jwt_verification_success", "user_id": payload.get("sub")},
            )
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning(
                "Expired JWT token presented", extra={"security_event": "jwt_token_expired", "error_id": "JWT_004"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            logger.error(
                f"Invalid JWT token: {str(e)}",
                extra={"security_event": "jwt_verification_failed", "error_id": "JWT_005"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.

        Note: bcrypt has a 72-byte limit. For security, we truncate long passwords.
        """
        # bcrypt has a 72-byte limit, truncate if needed
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.

        Note: bcrypt has a 72-byte limit. For security, we truncate long passwords.
        """
        # bcrypt has a 72-byte limit, truncate if needed
        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        # Verify password
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    payload = JWTAuth.verify_token(token)

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # Get full user object from auth service
    from ghl_real_estate_ai.services.auth_service import get_auth_service

    auth_service = get_auth_service()

    user = await auth_service.get_user_by_id(int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


# Alias for backward compatibility
require_auth = get_current_user
verify_jwt_token = JWTAuth.verify_token
