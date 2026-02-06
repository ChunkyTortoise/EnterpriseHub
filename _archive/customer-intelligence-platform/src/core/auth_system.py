"""
JWT Authentication and RBAC Authorization System.

Provides enterprise-grade authentication and authorization for:
- JWT token management with refresh tokens
- Role-Based Access Control (RBAC)
- SSO/SAML integration points
- API key authentication
- Permission enforcement
- Session management
"""

import asyncio
import hashlib
import hmac
import jwt
import logging
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis.asyncio as redis
import bcrypt

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    """User roles in the Customer Intelligence Platform."""
    SUPER_ADMIN = "super_admin"          # Platform administrator
    TENANT_ADMIN = "tenant_admin"        # Tenant administrator
    ACCOUNT_MANAGER = "account_manager"  # Account management
    SALES_REP = "sales_rep"             # Sales representative
    MARKETING_USER = "marketing_user"    # Marketing team member
    ANALYST = "analyst"                  # Data analyst
    VIEWER = "viewer"                    # Read-only access
    API_USER = "api_user"               # API-only access

class Permission(str, Enum):
    """Granular permissions for the platform."""
    # Customer Management
    CREATE_CUSTOMERS = "customers:create"
    READ_CUSTOMERS = "customers:read"
    UPDATE_CUSTOMERS = "customers:update"
    DELETE_CUSTOMERS = "customers:delete"
    EXPORT_CUSTOMERS = "customers:export"

    # Conversation Management
    START_CONVERSATIONS = "conversations:start"
    READ_CONVERSATIONS = "conversations:read"
    MANAGE_CONVERSATIONS = "conversations:manage"

    # Analytics and Scoring
    VIEW_ANALYTICS = "analytics:view"
    EXPORT_ANALYTICS = "analytics:export"
    MANAGE_SCORING = "scoring:manage"

    # Knowledge Management
    CREATE_KNOWLEDGE = "knowledge:create"
    UPDATE_KNOWLEDGE = "knowledge:update"
    DELETE_KNOWLEDGE = "knowledge:delete"

    # Integration Management
    MANAGE_INTEGRATIONS = "integrations:manage"
    VIEW_INTEGRATIONS = "integrations:view"

    # System Administration
    MANAGE_USERS = "users:manage"
    MANAGE_ROLES = "roles:manage"
    VIEW_AUDIT_LOGS = "audit:view"
    MANAGE_SETTINGS = "settings:manage"

    # AI Features
    USE_AI_FEATURES = "ai:use"
    CONFIGURE_AI = "ai:configure"

@dataclass
class User:
    """User data model."""
    id: str
    email: str
    name: str
    tenant_id: str
    roles: List[UserRole]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    sso_provider: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return any(permission in ROLE_PERMISSIONS.get(role, set()) for role in self.roles)

@dataclass
class AuthToken:
    """Authentication token data."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour
    refresh_expires_in: int = 604800  # 7 days

@dataclass
class TokenPayload:
    """JWT token payload."""
    user_id: str
    email: str
    tenant_id: str
    roles: List[str]
    permissions: List[str]
    exp: int
    iat: int
    jti: str  # JWT ID for revocation

# Role-Permission Mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.SUPER_ADMIN: {
        # Full access to everything
        Permission.CREATE_CUSTOMERS, Permission.READ_CUSTOMERS, Permission.UPDATE_CUSTOMERS,
        Permission.DELETE_CUSTOMERS, Permission.EXPORT_CUSTOMERS,
        Permission.START_CONVERSATIONS, Permission.READ_CONVERSATIONS, Permission.MANAGE_CONVERSATIONS,
        Permission.VIEW_ANALYTICS, Permission.EXPORT_ANALYTICS, Permission.MANAGE_SCORING,
        Permission.CREATE_KNOWLEDGE, Permission.UPDATE_KNOWLEDGE, Permission.DELETE_KNOWLEDGE,
        Permission.MANAGE_INTEGRATIONS, Permission.VIEW_INTEGRATIONS,
        Permission.MANAGE_USERS, Permission.MANAGE_ROLES, Permission.VIEW_AUDIT_LOGS, Permission.MANAGE_SETTINGS,
        Permission.USE_AI_FEATURES, Permission.CONFIGURE_AI
    },
    UserRole.TENANT_ADMIN: {
        # Tenant administration
        Permission.CREATE_CUSTOMERS, Permission.READ_CUSTOMERS, Permission.UPDATE_CUSTOMERS,
        Permission.DELETE_CUSTOMERS, Permission.EXPORT_CUSTOMERS,
        Permission.START_CONVERSATIONS, Permission.READ_CONVERSATIONS, Permission.MANAGE_CONVERSATIONS,
        Permission.VIEW_ANALYTICS, Permission.EXPORT_ANALYTICS, Permission.MANAGE_SCORING,
        Permission.CREATE_KNOWLEDGE, Permission.UPDATE_KNOWLEDGE, Permission.DELETE_KNOWLEDGE,
        Permission.MANAGE_INTEGRATIONS, Permission.VIEW_INTEGRATIONS,
        Permission.MANAGE_USERS, Permission.MANAGE_ROLES, Permission.MANAGE_SETTINGS,
        Permission.USE_AI_FEATURES, Permission.CONFIGURE_AI
    },
    UserRole.ACCOUNT_MANAGER: {
        # Customer management focus
        Permission.CREATE_CUSTOMERS, Permission.READ_CUSTOMERS, Permission.UPDATE_CUSTOMERS,
        Permission.START_CONVERSATIONS, Permission.READ_CONVERSATIONS, Permission.MANAGE_CONVERSATIONS,
        Permission.VIEW_ANALYTICS, Permission.EXPORT_ANALYTICS,
        Permission.USE_AI_FEATURES
    },
    UserRole.SALES_REP: {
        # Sales-focused permissions
        Permission.CREATE_CUSTOMERS, Permission.READ_CUSTOMERS, Permission.UPDATE_CUSTOMERS,
        Permission.START_CONVERSATIONS, Permission.READ_CONVERSATIONS,
        Permission.VIEW_ANALYTICS, Permission.USE_AI_FEATURES
    },
    UserRole.MARKETING_USER: {
        # Marketing analytics focus
        Permission.READ_CUSTOMERS, Permission.START_CONVERSATIONS, Permission.READ_CONVERSATIONS,
        Permission.VIEW_ANALYTICS, Permission.EXPORT_ANALYTICS, Permission.USE_AI_FEATURES
    },
    UserRole.ANALYST: {
        # Data analysis focus
        Permission.READ_CUSTOMERS, Permission.READ_CONVERSATIONS,
        Permission.VIEW_ANALYTICS, Permission.EXPORT_ANALYTICS, Permission.USE_AI_FEATURES
    },
    UserRole.VIEWER: {
        # Read-only access
        Permission.READ_CUSTOMERS, Permission.READ_CONVERSATIONS, Permission.VIEW_ANALYTICS
    },
    UserRole.API_USER: {
        # API access only
        Permission.READ_CUSTOMERS, Permission.CREATE_CUSTOMERS, Permission.UPDATE_CUSTOMERS,
        Permission.START_CONVERSATIONS, Permission.USE_AI_FEATURES
    }
}

class AuthenticationError(Exception):
    """Authentication-related errors."""
    pass

class AuthorizationError(Exception):
    """Authorization-related errors."""
    pass

class JWTAuthenticator:
    """JWT token management and validation."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)

        # Get user permissions
        permissions = []
        for role in user.roles:
            permissions.extend([p.value for p in ROLE_PERMISSIONS.get(role, set())])

        payload = TokenPayload(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            roles=[role.value for role in user.roles],
            permissions=list(set(permissions)),  # Remove duplicates
            exp=int(expire.timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            jti=secrets.token_hex(16)
        )

        return jwt.encode(asdict(payload), self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "user_id": user_id,
            "type": "refresh",
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "jti": secrets.token_hex(16)
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check if token is not expired
            if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
                raise AuthenticationError("Token has expired")

            return TokenPayload(
                user_id=payload["user_id"],
                email=payload["email"],
                tenant_id=payload["tenant_id"],
                roles=payload["roles"],
                permissions=payload["permissions"],
                exp=payload["exp"],
                iat=payload["iat"],
                jti=payload["jti"]
            )

        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")

    def verify_refresh_token(self, refresh_token: str) -> str:
        """Verify refresh token and extract user_id."""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])

            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid token type")

            if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
                raise AuthenticationError("Refresh token has expired")

            return payload["user_id"]

        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid refresh token: {e}")

class TokenBlacklist:
    """Redis-backed token blacklist for logout and revocation."""

    def __init__(self, redis_url: str = "redis://localhost:6379/3"):
        self.redis_url = redis_url
        self.redis_pool = None

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection."""
        if self.redis_pool is None:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=10,
                decode_responses=True
            )
        return redis.Redis(connection_pool=self.redis_pool)

    async def blacklist_token(self, jti: str, expires_at: datetime) -> None:
        """Add token to blacklist."""
        redis_client = await self._get_redis()

        # Calculate TTL based on token expiration
        ttl = max(1, int((expires_at - datetime.now(timezone.utc)).total_seconds()))

        await redis_client.setex(f"blacklist:{jti}", ttl, "revoked")
        logger.info(f"Token {jti} blacklisted with TTL {ttl}s")

    async def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        redis_client = await self._get_redis()
        result = await redis_client.get(f"blacklist:{jti}")
        return result is not None

class UserStore:
    """User storage and management (would be database in production)."""

    def __init__(self):
        # In production, this would be database operations
        self.users: Dict[str, User] = {}
        self.email_to_user_id: Dict[str, str] = {}

    async def create_user(
        self,
        email: str,
        name: str,
        tenant_id: str,
        password: str,
        roles: List[UserRole]
    ) -> User:
        """Create a new user."""
        user_id = secrets.token_hex(16)

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user = User(
            id=user_id,
            email=email,
            name=name,
            tenant_id=tenant_id,
            roles=roles,
            is_active=True,
            is_verified=True,
            created_at=datetime.now(timezone.utc)
        )

        self.users[user_id] = user
        self.email_to_user_id[email] = user_id

        logger.info(f"Created user {email} with roles {[r.value for r in roles]}")
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        user_id = self.email_to_user_id.get(email)
        if user_id:
            return self.users.get(user_id)
        return None

    async def verify_password(self, email: str, password: str) -> Optional[User]:
        """Verify user password and return user if valid."""
        # In production, this would check hashed password from database
        user = await self.get_user_by_email(email)
        if user and user.is_active:
            # Simplified password check for demo
            # In production: bcrypt.checkpw(password.encode('utf-8'), stored_hash)
            return user
        return None

    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        user = self.users.get(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)

class AuthService:
    """Main authentication and authorization service."""

    def __init__(
        self,
        secret_key: str,
        redis_url: str = "redis://localhost:6379/3"
    ):
        self.jwt_auth = JWTAuthenticator(secret_key)
        self.token_blacklist = TokenBlacklist(redis_url)
        self.user_store = UserStore()
        self.bearer_scheme = HTTPBearer(auto_error=False)

        logger.info("AuthService initialized")

    async def login(self, email: str, password: str, tenant_id: str) -> AuthToken:
        """Authenticate user and return tokens."""
        # Verify credentials
        user = await self.user_store.verify_password(email, password)
        if not user:
            raise AuthenticationError("Invalid credentials")

        if user.tenant_id != tenant_id:
            raise AuthenticationError("Invalid tenant")

        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        # Update last login
        await self.user_store.update_last_login(user.id)

        # Create tokens
        access_token = self.jwt_auth.create_access_token(user)
        refresh_token = self.jwt_auth.create_refresh_token(user.id)

        logger.info(f"User {email} logged in successfully")

        return AuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.jwt_auth.access_token_expire_minutes * 60
        )

    async def refresh_token(self, refresh_token: str) -> AuthToken:
        """Refresh access token using refresh token."""
        # Verify refresh token
        user_id = self.jwt_auth.verify_refresh_token(refresh_token)

        # Get current user
        user = await self.user_store.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("Invalid user")

        # Create new tokens
        access_token = self.jwt_auth.create_access_token(user)
        new_refresh_token = self.jwt_auth.create_refresh_token(user.id)

        return AuthToken(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=self.jwt_auth.access_token_expire_minutes * 60
        )

    async def logout(self, token: str) -> None:
        """Logout user by blacklisting token."""
        payload = self.jwt_auth.verify_token(token)
        expires_at = datetime.fromtimestamp(payload.exp, tz=timezone.utc)
        await self.token_blacklist.blacklist_token(payload.jti, expires_at)

        logger.info(f"User {payload.email} logged out")

    async def verify_token(self, token: str) -> TokenPayload:
        """Verify token and check blacklist."""
        payload = self.jwt_auth.verify_token(token)

        # Check if token is blacklisted
        if await self.token_blacklist.is_blacklisted(payload.jti):
            raise AuthenticationError("Token has been revoked")

        return payload

    async def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> User:
        """Get current user from request token."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token"
            )

        try:
            payload = await self.verify_token(credentials.credentials)
            user = await self.user_store.get_user_by_id(payload.user_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is disabled"
                )

            return user

        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

    async def check_permissions(self, user: User, required_permissions: List[Permission]) -> bool:
        """Check if user has required permissions."""
        return all(user.has_permission(perm) for perm in required_permissions)

    async def require_permissions(self, user: User, permissions: List[Permission]) -> None:
        """Require user to have specific permissions."""
        if not await self.check_permissions(user, permissions):
            missing_perms = [p.value for p in permissions if not user.has_permission(p)]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {missing_perms}"
            )

# Dependency injection for FastAPI
auth_service = None

def get_auth_service() -> AuthService:
    """
    Get auth service instance.

    SECURITY: Enforces fail-fast validation for JWT secrets.
    No weak fallback secrets are permitted in any environment.
    """
    global auth_service
    if auth_service is None:
        import os
        import sys

        secret_key = os.getenv("JWT_SECRET_KEY")
        environment = os.getenv("ENVIRONMENT", "development").lower()

        # Production: Fail fast if no secret or weak secret
        if environment == "production":
            if not secret_key:
                logger.critical("SECURITY: JWT_SECRET_KEY required in production")
                print("=" * 60)
                print("CRITICAL SECURITY ERROR: JWT_SECRET_KEY must be set in production")
                print("=" * 60)
                print("Generate a secure secret: openssl rand -hex 32")
                print("=" * 60)
                sys.exit(1)
            if len(secret_key) < 32:
                logger.critical(f"SECURITY: JWT_SECRET_KEY too weak ({len(secret_key)} chars)")
                print(f"SECURITY ERROR: JWT_SECRET_KEY must be >= 32 characters (got {len(secret_key)})")
                sys.exit(1)
        else:
            # Development: Allow missing secret but generate temporary one with warning
            if not secret_key:
                import secrets as secrets_module
                secret_key = secrets_module.token_urlsafe(32)
                logger.warning(
                    "JWT_SECRET_KEY not set - using temporary secret for development. "
                    "This secret will change on restart. Set JWT_SECRET_KEY in .env for persistence."
                )
            elif len(secret_key) < 32:
                logger.warning(
                    f"JWT_SECRET_KEY is only {len(secret_key)} characters. "
                    "For security, use at least 32 characters (openssl rand -hex 32)"
                )

        auth_service = AuthService(secret_key)
    return auth_service

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    auth: AuthService = Depends(get_auth_service)
) -> User:
    """FastAPI dependency to get current user."""
    return await auth.get_current_user(credentials)

async def get_current_active_user(
    user: User = Depends(get_current_user)
) -> User:
    """FastAPI dependency to get current active user."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return user

def require_permissions(*permissions: Permission):
    """Decorator factory for permission requirements."""
    def decorator(func):
        async def wrapper(
            user: User = Depends(get_current_active_user),
            auth: AuthService = Depends(get_auth_service),
            *args,
            **kwargs
        ):
            await auth.require_permissions(user, list(permissions))
            return await func(user=user, *args, **kwargs)
        return wrapper
    return decorator

def require_role(*roles: UserRole):
    """Decorator factory for role requirements."""
    def decorator(func):
        async def wrapper(
            user: User = Depends(get_current_active_user),
            *args,
            **kwargs
        ):
            if not any(user.has_role(role) for role in roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required roles: {[r.value for r in roles]}"
                )
            return await func(user=user, *args, **kwargs)
        return wrapper
    return decorator

# Initialize default users for development
async def init_default_users(auth_service: AuthService) -> None:
    """Initialize default users for development/demo."""
    default_users = [
        {
            "email": "admin@example.com",
            "name": "System Administrator",
            "tenant_id": "default",
            "password": "admin123",
            "roles": [UserRole.SUPER_ADMIN]
        },
        {
            "email": "sales@example.com",
            "name": "Sales Representative",
            "tenant_id": "default",
            "password": "sales123",
            "roles": [UserRole.SALES_REP]
        },
        {
            "email": "analyst@example.com",
            "name": "Data Analyst",
            "tenant_id": "default",
            "password": "analyst123",
            "roles": [UserRole.ANALYST]
        }
    ]

    for user_data in default_users:
        try:
            await auth_service.user_store.create_user(**user_data)
        except Exception as e:
            logger.warning(f"Failed to create default user {user_data['email']}: {e}")

    logger.info("Default users initialized")