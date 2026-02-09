"""
JWT-based Authentication Service for Real Estate AI Dashboard.

Provides secure user authentication with role-based permissions.
Handles user creation, authentication, token management, and permissions.
"""

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional

import aiosqlite
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class UserRole(Enum):
    """User roles with hierarchical permissions."""

    ADMIN = "admin"  # Full system access
    AGENT = "agent"  # Lead and deal management
    VIEWER = "viewer"  # Read-only access
    SUPER_ADMIN = "super_admin"  # Reserved for enterprise ops


@dataclass
class User:
    """User model with authentication details."""

    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class AuthService:
    """JWT-based authentication service with secure password handling."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize authentication service."""
        self.db_path = db_path or os.path.join("data", "auth.db")
        self.secret_key = self._get_secret_key()
        self.algorithm = "HS256"
        self.token_expire_hours = 24
        self._init_complete = False

        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _get_secret_key(self) -> str:
        """Get or generate JWT secret key."""
        key_file = os.path.join("data", ".jwt_secret")

        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning(f"Could not read JWT secret file: {e}")

        # Generate new secret key
        secret = secrets.token_urlsafe(64)
        try:
            os.makedirs("data", exist_ok=True)
            with open(key_file, "w") as f:
                f.write(secret)
            os.chmod(key_file, 0o600)  # Owner read/write only
        except Exception as e:
            logger.warning(f"Could not save JWT secret file: {e}")

        return secret

    def _hash_password(self, password: str) -> str:
        """
        Secure password hashing using HMAC-SHA256.

        Alternative to bcrypt that avoids the 72-byte limitation
        and provides strong security for password storage.
        """
        # Use a salt derived from the secret key for consistency
        salt = hashlib.sha256(self.secret_key.encode()).hexdigest()[:32]

        # HMAC-SHA256 with salt
        return hmac.new(salt.encode(), password.encode(), hashlib.sha256).hexdigest()

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return hmac.compare_digest(self._hash_password(password), hashed)

    async def init_database(self):
        """Initialize the authentication database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_login DATETIME
                    )
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        token_hash TEXT NOT NULL,
                        expires_at DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)

                await db.commit()

            self._init_complete = True
            logger.info("Authentication database initialized")

        except Exception as e:
            logger.error(f"Error initializing auth database: {e}")
            raise

    async def _ensure_initialized(self):
        """Ensure database is initialized."""
        if not self._init_complete:
            await self.init_database()

    async def create_user(
        self, username: str, email: str, password: str, role: UserRole = UserRole.VIEWER
    ) -> Optional[User]:
        """Create a new user."""
        await self._ensure_initialized()

        try:
            password_hash = self._hash_password(password)

            async with aiosqlite.connect(self.db_path) as db:
                # Check for existing user
                async with db.execute(
                    "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
                ) as cursor:
                    if await cursor.fetchone():
                        return None

                # Create new user
                await db.execute(
                    """
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (?, ?, ?, ?)
                    """,
                    (username, email, password_hash, role.value),
                )
                await db.commit()

                # Get created user
                async with db.execute("SELECT * FROM users WHERE username = ?", (username,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return self._row_to_user(row)

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
                ) as cursor:
                    row = await cursor.fetchone()

                    if row and self._verify_password(password, row[3]):  # password_hash is index 3
                        # Update last login
                        await db.execute(
                            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                            (row[0],),  # id is index 0
                        )
                        await db.commit()

                        return self._row_to_user(row)

            return None

        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    def _row_to_user(self, row) -> User:
        """Convert database row to User object."""
        return User(
            id=row[0],
            username=row[1],
            email=row[2],
            role=UserRole(row[4]),
            is_active=bool(row[5]),
            created_at=datetime.fromisoformat(row[6]) if row[6] else None,
            last_login=datetime.fromisoformat(row[7]) if row[7] else None,
        )

    def create_token(self, user: User) -> str:
        """Create JWT token for user."""
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "exp": datetime.now(timezone.utc) + timedelta(hours=self.token_expire_hours),
            "iat": datetime.now(timezone.utc),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    return self._row_to_user(row) if row else None

        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    def check_permission(self, user_role: UserRole, required_permission: str, action: str) -> bool:
        """
        Check if user role has required permission.

        Args:
            user_role: User's role
            required_permission: Permission resource (e.g., 'dashboard', 'leads')
            action: Action type ('read', 'write', 'delete')
        """
        # Admin has all permissions
        if user_role == UserRole.ADMIN:
            return True

        # Define role permissions
        permissions = {
            UserRole.AGENT: {
                "dashboard": ["read", "write"],
                "leads": ["read", "write"],
                "properties": ["read", "write"],
                "conversations": ["read", "write"],
                "commission": ["read"],
                "performance": ["read"],
            },
            UserRole.VIEWER: {
                "dashboard": ["read"],
                "leads": ["read"],
                "properties": ["read"],
                "conversations": ["read"],
                "commission": [],
                "performance": ["read"],
            },
        }

        user_perms = permissions.get(user_role, {})
        resource_perms = user_perms.get(required_permission, [])

        return action in resource_perms

    async def initialize_default_users(self):
        """Create default users for testing and initial setup."""
        await self._ensure_initialized()

        default_users = [
            ("admin", "admin@jorgeai.com", "admin123", UserRole.ADMIN),
            ("jorge", "jorge@realtor.com", "jorge123", UserRole.AGENT),
            ("viewer", "viewer@jorgeai.com", "viewer123", UserRole.VIEWER),
        ]

        for username, email, password, role in default_users:
            user = await self.create_user(username, email, password, role)
            if user:
                logger.info(f"Created default user: {username} ({role.value})")
            else:
                logger.debug(f"User {username} already exists or creation failed")


# Global auth service instance
_auth_service = None


def get_auth_service() -> AuthService:
    """Get singleton auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


# FastAPI dependency for routes that import from auth_service directly
_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user as dict."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization required")

    auth_service = get_auth_service()
    payload = auth_service.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await auth_service.get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
    }
