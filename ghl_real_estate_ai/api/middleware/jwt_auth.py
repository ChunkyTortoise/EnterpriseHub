"""
JWT Authentication Middleware
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt
import os

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
    """JWT Authentication handler."""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create a new JWT token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
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
            logger.error("Invalid token format provided", extra={"security_event": "jwt_verification_failed", "error_id": "JWT_001"})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Validate required fields
            if "sub" not in payload:
                logger.error("Token missing required subject field", extra={"security_event": "jwt_verification_failed", "error_id": "JWT_002"})
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token structure",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check if token is expired (additional validation beyond jwt.decode)
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                logger.warning("Expired token presented", extra={"security_event": "jwt_token_expired", "error_id": "JWT_003"})
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            logger.info("JWT token successfully verified", extra={"security_event": "jwt_verification_success", "user_id": payload.get("sub")})
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token presented", extra={"security_event": "jwt_token_expired", "error_id": "JWT_004"})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            logger.error(f"Invalid JWT token: {str(e)}", extra={"security_event": "jwt_verification_failed", "error_id": "JWT_005"})
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
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Note: bcrypt has a 72-byte limit. For security, we truncate long passwords.
        """
        # bcrypt has a 72-byte limit, truncate if needed
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Verify password
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    payload = JWTAuth.verify_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Get full user object from auth service
    from ghl_real_estate_ai.services.auth_service import get_auth_service
    auth_service = get_auth_service()
    
    user = await auth_service.get_user_by_id(int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


# Alias for backward compatibility
require_auth = get_current_user
verify_jwt_token = JWTAuth.verify_token
