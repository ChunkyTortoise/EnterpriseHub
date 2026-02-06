"""
Authentication API routes for Customer Intelligence Platform.

Provides JWT authentication endpoints for enterprise SSO integration.
"""

from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
import logging

from ...core.auth_system import (
    AuthService, AuthToken, User, UserRole, Permission,
    get_auth_service, get_current_user, get_current_active_user,
    require_permissions, require_role, init_default_users,
    AuthenticationError
)
from ...core.tenant_middleware import TenantContext, get_current_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models for API
class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]

class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str

class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    name: str
    tenant_id: str
    roles: List[str]
    permissions: List[str]
    is_active: bool
    is_verified: bool
    last_login_at: str = None

class CreateUserRequest(BaseModel):
    """Create user request model."""
    email: EmailStr
    name: str
    password: str
    roles: List[str]

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return JWT tokens.

    Supports:
    - Email/password authentication
    - Multi-tenant isolation
    - JWT token generation with permissions
    """
    try:
        # Get tenant from context (set by TenantMiddleware)
        tenant_id = TenantContext.get_tenant() or "default"

        # Authenticate user
        auth_token = await auth_service.login(
            email=request.email,
            password=request.password,
            tenant_id=tenant_id
        )

        # Get user details for response
        user = await auth_service.user_store.get_user_by_email(request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User not found after authentication"
            )

        # Build user permissions list
        permissions = []
        for role in user.roles:
            from ...core.auth_system import ROLE_PERMISSIONS
            permissions.extend([p.value for p in ROLE_PERMISSIONS.get(role, set())])

        user_data = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "tenant_id": user.tenant_id,
            "roles": [role.value for role in user.roles],
            "permissions": list(set(permissions)),  # Remove duplicates
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
        }

        logger.info(
            f"User {request.email} authenticated successfully",
            extra={"tenant_id": tenant_id, "user_id": user.id}
        )

        return LoginResponse(
            access_token=auth_token.access_token,
            refresh_token=auth_token.refresh_token,
            token_type=auth_token.token_type,
            expires_in=auth_token.expires_in,
            user=user_data
        )

    except AuthenticationError as e:
        logger.warning(f"Authentication failed for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.

    Provides seamless token renewal for long-running sessions.
    """
    try:
        auth_token = await auth_service.refresh_token(request.refresh_token)

        logger.info("Token refreshed successfully")

        return TokenResponse(
            access_token=auth_token.access_token,
            refresh_token=auth_token.refresh_token,
            token_type=auth_token.token_type,
            expires_in=auth_token.expires_in
        )

    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
    request: Request = None
):
    """
    Logout user by revoking current token.

    Adds token to blacklist for immediate revocation.
    """
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            await auth_service.logout(token)

        logger.info(f"User {user.email} logged out")

    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Don't return error for logout - it's not critical

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.

    Returns user profile, roles, and permissions for frontend apps.
    """
    # Build user permissions list
    permissions = []
    for role in user.roles:
        from ...core.auth_system import ROLE_PERMISSIONS
        permissions.extend([p.value for p in ROLE_PERMISSIONS.get(role, set())])

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        tenant_id=user.tenant_id,
        roles=[role.value for role in user.roles],
        permissions=list(set(permissions)),
        is_active=user.is_active,
        is_verified=user.is_verified,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None
    )

@router.post(
    "/users",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions(Permission.MANAGE_USERS))]
)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Create a new user (admin only).

    Requires MANAGE_USERS permission.
    """
    try:
        # Convert string roles to UserRole enums
        roles = [UserRole(role) for role in request.roles]

        # Create user
        user = await auth_service.user_store.create_user(
            email=request.email,
            name=request.name,
            tenant_id=current_user.tenant_id,  # Same tenant as creator
            password=request.password,
            roles=roles
        )

        # Build permissions list
        permissions = []
        for role in user.roles:
            from ...core.auth_system import ROLE_PERMISSIONS
            permissions.extend([p.value for p in ROLE_PERMISSIONS.get(role, set())])

        logger.info(f"User {request.email} created by {current_user.email}")

        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            tenant_id=user.tenant_id,
            roles=[role.value for role in user.roles],
            permissions=list(set(permissions)),
            is_active=user.is_active,
            is_verified=user.is_verified
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {e}"
        )
    except Exception as e:
        logger.error(f"User creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )

@router.get("/permissions")
async def list_permissions(
    user: User = Depends(get_current_active_user)
):
    """
    List all available permissions and roles.

    Useful for admin interfaces and permission management.
    """
    return {
        "roles": [
            {
                "name": role.value,
                "description": role.value.replace("_", " ").title(),
                "permissions": [p.value for p in perms]
            }
            for role, perms in ROLE_PERMISSIONS.items()
        ],
        "permissions": [
            {
                "name": perm.value,
                "description": perm.value.replace("_", " ").replace(":", ": ").title()
            }
            for perm in Permission
        ]
    }

@router.get("/health")
async def auth_health_check():
    """
    Authentication service health check.

    Validates JWT configuration and token blacklist connectivity.
    """
    try:
        auth_service = get_auth_service()

        # Test JWT functionality
        test_user = User(
            id="test",
            email="test@example.com",
            name="Test User",
            tenant_id="test",
            roles=[UserRole.VIEWER],
            is_active=True,
            is_verified=True,
            created_at=datetime.now()
        )

        # Test token creation and verification
        test_token = auth_service.jwt_auth.create_access_token(test_user)
        payload = auth_service.jwt_auth.verify_token(test_token)

        # Test Redis connectivity
        try:
            await auth_service.token_blacklist.is_blacklisted("test_jti")
            redis_status = "connected"
        except Exception:
            redis_status = "disconnected"

        return {
            "status": "healthy",
            "jwt": "operational",
            "redis_blacklist": redis_status,
            "default_users": len(auth_service.user_store.users)
        }

    except Exception as e:
        logger.error(f"Auth health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Authentication service unhealthy: {e}"
        )

# SSO Integration Placeholder Endpoints
# These would be implemented for specific SSO providers

@router.get("/sso/providers")
async def list_sso_providers():
    """List available SSO providers."""
    return {
        "providers": [
            {
                "name": "google",
                "display_name": "Google Workspace",
                "enabled": False,
                "authorization_url": "/auth/sso/google"
            },
            {
                "name": "microsoft",
                "display_name": "Microsoft Azure AD",
                "enabled": False,
                "authorization_url": "/auth/sso/microsoft"
            },
            {
                "name": "saml",
                "display_name": "SAML 2.0",
                "enabled": False,
                "authorization_url": "/auth/sso/saml"
            }
        ]
    }

@router.get("/sso/{provider}")
async def sso_redirect(provider: str):
    """
    SSO provider redirect endpoint.

    In production, this would redirect to the SSO provider's
    authorization endpoint.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"SSO provider '{provider}' not yet implemented"
    )

@router.post("/sso/{provider}/callback")
async def sso_callback(provider: str):
    """
    SSO provider callback endpoint.

    In production, this would handle the SSO provider's
    authorization response and create local user sessions.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"SSO callback for '{provider}' not yet implemented"
    )

# Initialize authentication on startup
@router.on_event("startup")
async def startup_event():
    """Initialize authentication system on startup."""
    try:
        auth_service = get_auth_service()
        await init_default_users(auth_service)
        logger.info("Authentication system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize authentication: {e}")

# Import ROLE_PERMISSIONS for reference
from ...core.auth_system import ROLE_PERMISSIONS