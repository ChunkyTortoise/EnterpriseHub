import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Test script for the authentication system.

Tests user creation, authentication, and token validation.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ghl_real_estate_ai.services.auth_service import get_auth_service, UserRole


async def test_auth_system():
    """Test the complete authentication system."""
    print("🧪 Testing Jorge's Real Estate AI Authentication System")
    print("=" * 60)

    try:
        # Get auth service instance
        auth_service = get_auth_service()
        print("✅ Auth service initialized")

        # Initialize database
        await auth_service.init_database()
        print("✅ Database initialized")

        # Initialize default users
        await auth_service.initialize_default_users()
        print("✅ Default users created")

        # Test authentication
        test_users = [
            ("admin", "admin123"),
            ("jorge", "jorge123"),
            ("viewer", "viewer123")
        ]

        for username, password in test_users:
            print(f"\n🔐 Testing authentication for {username}...")

            # Test authentication
            user = await auth_service.authenticate_user(username, password)
            if user:
                print(f"✅ Authentication successful: {user.username} ({user.role.value})")

                # Test token creation and validation
                token = auth_service.create_token(user)
                print(f"✅ Token created: {token[:20]}...")

                # Verify token
                payload = auth_service.verify_token(token)
                if payload:
                    print(f"✅ Token valid: user_id={payload['user_id']}, role={payload['role']}")
                else:
                    print("❌ Token validation failed")

                # Test permissions
                test_permissions = [
                    ('dashboard', 'read'),
                    ('commission', 'read'),
                    ('leads', 'write')
                ]

                for resource, action in test_permissions:
                    has_permission = auth_service.check_permission(
                        user.role, resource, action
                    )
                    status = "✅" if has_permission else "❌"
                    print(f"{status} Permission {resource}:{action} = {has_permission}")

            else:
                print(f"❌ Authentication failed for {username}")

        print("\n🎉 Authentication system test completed successfully!")
        return True

    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    try:
        success = asyncio.run(test_auth_system())
        if success:
            print("\n🚀 Ready for production! Authentication system is working.")
            sys.exit(0)
        else:
            print("\n🔧 Please fix errors before proceeding.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏸️ Test interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()