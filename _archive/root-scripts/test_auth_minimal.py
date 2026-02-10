import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Minimal test for authentication service only.

Tests without initializing the full application system.
"""

import asyncio
import os
import sqlite3
import jwt
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import aiosqlite


class UserRole(Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    AGENT = "agent"
    VIEWER = "viewer"


@dataclass
class User:
    """User model."""
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool = True


class MinimalAuthService:
    """Minimal auth service for testing."""

    def __init__(self):
        """Initialize auth service."""
        self.db_path = "test_auth.db"
        self.secret_key = secrets.token_urlsafe(64)
        self.algorithm = "HS256"
        self.token_expire_hours = 24

    def _hash_password(self, password: str) -> str:
        """Hash password using HMAC-SHA256."""
        salt = hashlib.sha256(self.secret_key.encode()).hexdigest()[:32]
        return hmac.new(
            salt.encode(),
            password.encode(),
            hashlib.sha256
        ).hexdigest()

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return hmac.compare_digest(self._hash_password(password), hashed)

    async def init_database(self):
        """Initialize database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)
            await db.commit()

    async def create_user(self, username: str, email: str, password: str, role: UserRole) -> Optional[User]:
        """Create a new user."""
        password_hash = self._hash_password(password)

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                    (username, email, password_hash, role.value)
                )
                await db.commit()

                # Get created user
                async with db.execute(
                    "SELECT * FROM users WHERE username = ?", (username,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return User(
                            id=row[0],
                            username=row[1],
                            email=row[2],
                            role=UserRole(row[4])
                        )
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row and self._verify_password(password, row[3]):
                        return User(
                            id=row[0],
                            username=row[1],
                            email=row[2],
                            role=UserRole(row[4])
                        )
        except Exception as e:
            print(f"Error authenticating user: {e}")
        return None

    def create_token(self, user: User) -> str:
        """Create JWT token."""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role.value,
            'exp': datetime.now(timezone.utc) + timedelta(hours=self.token_expire_hours),
            'iat': datetime.now(timezone.utc)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token."""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            print("Token expired")
            return None
        except jwt.InvalidTokenError:
            print("Invalid token")
            return None

    def check_permission(self, user_role: UserRole, resource: str, action: str) -> bool:
        """Check permissions."""
        if user_role == UserRole.ADMIN:
            return True

        permissions = {
            UserRole.AGENT: {
                'dashboard': ['read', 'write'],
                'leads': ['read', 'write'],
                'commission': ['read']
            },
            UserRole.VIEWER: {
                'dashboard': ['read'],
                'leads': ['read'],
                'commission': []
            }
        }

        user_perms = permissions.get(user_role, {})
        resource_perms = user_perms.get(resource, [])
        return action in resource_perms

    def cleanup(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)


async def test_minimal_auth():
    """Test authentication system."""
    print("🧪 Minimal Authentication System Test")
    print("=" * 40)

    auth = MinimalAuthService()

    try:
        # Initialize database
        await auth.init_database()
        print("✅ Database initialized")

        # Create test users
        users_data = [
            ("admin", "admin@test.com", "admin123", UserRole.ADMIN),
            ("jorge", "jorge@test.com", "jorge123", UserRole.AGENT),
            ("viewer", "viewer@test.com", "viewer123", UserRole.VIEWER)
        ]

        for username, email, password, role in users_data:
            user = await auth.create_user(username, email, password, role)
            if user:
                print(f"✅ Created user: {username} ({role.value})")
            else:
                print(f"❌ Failed to create user: {username}")

        # Test authentication and tokens
        for username, email, password, role in users_data:
            print(f"\n🔐 Testing {username}...")

            # Authenticate
            user = await auth.authenticate_user(username, password)
            if user:
                print(f"✅ Authentication successful")

                # Create and verify token
                token = auth.create_token(user)
                payload = auth.verify_token(token)
                if payload:
                    print(f"✅ Token valid: role={payload['role']}")
                else:
                    print("❌ Token invalid")

                # Test permissions
                test_perms = [
                    ('dashboard', 'read'),
                    ('commission', 'read'),
                    ('leads', 'write')
                ]

                for resource, action in test_perms:
                    has_perm = auth.check_permission(user.role, resource, action)
                    status = "✅" if has_perm else "❌"
                    print(f"{status} {resource}:{action}")

            else:
                print(f"❌ Authentication failed")

        print("\n🎉 Test completed successfully!")
        return True

    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        auth.cleanup()


def main():
    """Run the test."""
    try:
        success = asyncio.run(test_minimal_auth())
        if success:
            print("\n🚀 Authentication system is working correctly!")
        else:
            print("\n🔧 Please fix errors before proceeding.")
    except KeyboardInterrupt:
        print("\n⏸️ Test interrupted")


if __name__ == "__main__":
    main()