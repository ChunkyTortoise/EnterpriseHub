#!/usr/bin/env python3
"""
🔐 Authentication Integration Component - JWT & RBAC for Streamlit
=================================================================

Secure authentication integration for Streamlit applications connecting
to the customer intelligence platform. Provides JWT token validation,
role-based access control, and enterprise security features.

Features:
- JWT token validation and parsing
- Role-based access control (RBAC)
- Tenant-aware authentication
- Session management
- Security middleware
- Audit logging integration

Author: Claude Code Authentication
Created: January 2026
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import jwt
import requests
import streamlit as st


class UserRole(str, Enum):
    """User roles matching backend auth system."""

    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    ACCOUNT_MANAGER = "account_manager"
    SALES_REP = "sales_rep"
    MARKETING_USER = "marketing_user"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_USER = "api_user"


class Permission(str, Enum):
    """Permissions matching backend auth system."""

    # Customer Management
    CREATE_CUSTOMERS = "customers:create"
    READ_CUSTOMERS = "customers:read"
    UPDATE_CUSTOMERS = "customers:update"
    DELETE_CUSTOMERS = "customers:delete"
    EXPORT_CUSTOMERS = "customers:export"

    # Analytics
    VIEW_ANALYTICS = "analytics:view"
    EXPORT_ANALYTICS = "analytics:export"
    MANAGE_SCORING = "scoring:manage"

    # System Administration
    MANAGE_USERS = "users:manage"
    MANAGE_ROLES = "roles:manage"
    VIEW_AUDIT_LOGS = "audit:view"
    MANAGE_SETTINGS = "settings:manage"


@dataclass
class AuthenticatedUser:
    """Authenticated user data."""

    user_id: str
    email: str
    name: str
    tenant_id: str
    roles: List[UserRole]
    permissions: List[Permission]
    is_active: bool
    last_login: Optional[datetime] = None
    session_expires: Optional[datetime] = None

    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role."""
        return role in self.roles

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions

    def has_any_role(self, roles: List[UserRole]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions."""
        return all(permission in self.permissions for permission in permissions)


class AuthenticationError(Exception):
    """Authentication related errors."""

    pass


class AuthorizationError(Exception):
    """Authorization related errors."""

    pass


class StreamlitAuthenticator:
    """JWT Authentication for Streamlit applications."""

    def __init__(
        self,
        secret_key: str = None,
        api_base_url: str = None,
        token_header_name: str = "Authorization",
        session_timeout_minutes: int = 60,
    ):
        """
        Initialize authenticator.

        Args:
            secret_key: JWT secret key for token validation
            api_base_url: Base URL for authentication API
            token_header_name: Header name for token transmission
            session_timeout_minutes: Session timeout in minutes
        """
        self.secret_key = secret_key or st.secrets.get("JWT_SECRET_KEY", "development-secret-key")
        self.api_base_url = api_base_url or st.secrets.get("AUTH_API_URL", "http://localhost:8000")
        self.token_header_name = token_header_name
        self.session_timeout = timedelta(minutes=session_timeout_minutes)

        # Initialize session state
        if "auth_state" not in st.session_state:
            st.session_state.auth_state = {
                "authenticated": False,
                "user": None,
                "token": None,
                "refresh_token": None,
                "login_time": None,
                "last_activity": None,
            }

    def render_login_form(self, container=None) -> bool:
        """
        Render login form and handle authentication.

        Returns:
            bool: True if login successful, False otherwise
        """
        if container is None:
            container = st

        with container.container():
            st.markdown(
                """
            <style>
            .login-container {
                max-width: 400px;
                margin: 2rem auto;
                padding: 2rem;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                border: 1px solid #E2E8F0;
            }
            
            .login-title {
                text-align: center;
                color: #2D3748;
                margin-bottom: 2rem;
                font-weight: 600;
            }
            
            .login-subtitle {
                text-align: center;
                color: #4A5568;
                margin-bottom: 1.5rem;
                font-size: 0.9rem;
            }
            
            .demo-credentials {
                background: #F7FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 1rem;
                margin: 1rem 0;
                font-family: monospace;
                font-size: 0.9rem;
            }
            </style>
            """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="login-container">', unsafe_allow_html=True)

            st.markdown('<h2 class="login-title">🔐 Customer Intelligence Platform</h2>', unsafe_allow_html=True)
            st.markdown('<p class="login-subtitle">Secure Authentication Required</p>', unsafe_allow_html=True)

            with st.form("login_form", clear_on_submit=False):
                email = st.text_input(
                    "📧 Email Address", placeholder="user@company.com", help="Enter your registered email address"
                )

                password = st.text_input("🔑 Password", type="password", help="Enter your password")

                col1, col2 = st.columns(2)

                with col1:
                    tenant_id = st.selectbox(
                        "🏢 Tenant", ["demo", "enterprise", "trial"], help="Select your organization tenant"
                    )

                with col2:
                    remember_me = st.checkbox("Remember me", value=False)

                login_submitted = st.form_submit_button("🚀 Sign In", use_container_width=True)

                if login_submitted:
                    try:
                        if self._authenticate_user(email, password, tenant_id, remember_me):
                            st.success("✅ Authentication successful! Redirecting...")
                            time.sleep(1)
                            st.rerun()
                            return True
                        else:
                            st.error("❌ Invalid credentials. Please try again.")
                    except AuthenticationError as e:
                        st.error(f"❌ Authentication failed: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")

            # Demo credentials info
            with st.expander("🔍 Demo Credentials", expanded=False):
                st.markdown(
                    """
                <div class="demo-credentials">
                <strong>Super Admin:</strong><br>
                Email: admin@demo.com<br>
                Password: admin123<br>
                Tenant: demo<br><br>
                
                <strong>Analyst:</strong><br>
                Email: analyst@demo.com<br>
                Password: analyst123<br>
                Tenant: demo<br><br>
                
                <strong>Viewer:</strong><br>
                Email: viewer@enterprise.com<br>
                Password: viewer123<br>
                Tenant: enterprise
                </div>
                """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

            return False

    def _authenticate_user(self, email: str, password: str, tenant_id: str, remember_me: bool = False) -> bool:
        """
        Authenticate user with backend service.

        Args:
            email: User email
            password: User password
            tenant_id: Tenant identifier
            remember_me: Extended session flag

        Returns:
            bool: True if authentication successful
        """
        try:
            # For demo purposes, we'll use mock authentication
            # In production, this would make API call to auth service

            # Mock user database with role assignments
            mock_users = {
                ("admin@demo.com", "admin123", "demo"): {
                    "user_id": "user_001",
                    "name": "System Administrator",
                    "roles": [UserRole.SUPER_ADMIN],
                    "permissions": [p for p in Permission],  # All permissions
                },
                ("analyst@demo.com", "analyst123", "demo"): {
                    "user_id": "user_002",
                    "name": "Data Analyst",
                    "roles": [UserRole.ANALYST],
                    "permissions": [Permission.VIEW_ANALYTICS, Permission.READ_CUSTOMERS, Permission.EXPORT_ANALYTICS],
                },
                ("viewer@enterprise.com", "viewer123", "enterprise"): {
                    "user_id": "user_003",
                    "name": "Enterprise Viewer",
                    "roles": [UserRole.VIEWER],
                    "permissions": [Permission.VIEW_ANALYTICS, Permission.READ_CUSTOMERS],
                },
                ("manager@demo.com", "manager123", "demo"): {
                    "user_id": "user_004",
                    "name": "Account Manager",
                    "roles": [UserRole.ACCOUNT_MANAGER, UserRole.SALES_REP],
                    "permissions": [
                        Permission.READ_CUSTOMERS,
                        Permission.UPDATE_CUSTOMERS,
                        Permission.CREATE_CUSTOMERS,
                        Permission.VIEW_ANALYTICS,
                    ],
                },
            }

            user_key = (email.lower(), password, tenant_id.lower())
            user_data = mock_users.get(user_key)

            if not user_data:
                raise AuthenticationError("Invalid credentials")

            # Create authenticated user
            authenticated_user = AuthenticatedUser(
                user_id=user_data["user_id"],
                email=email,
                name=user_data["name"],
                tenant_id=tenant_id,
                roles=user_data["roles"],
                permissions=user_data["permissions"],
                is_active=True,
                last_login=datetime.now(timezone.utc),
                session_expires=datetime.now(timezone.utc)
                + (timedelta(days=30) if remember_me else self.session_timeout),
            )

            # Generate JWT token (mock)
            token_payload = {
                "user_id": authenticated_user.user_id,
                "email": authenticated_user.email,
                "tenant_id": authenticated_user.tenant_id,
                "roles": [r.value for r in authenticated_user.roles],
                "permissions": [p.value for p in authenticated_user.permissions],
                "exp": int(authenticated_user.session_expires.timestamp()),
                "iat": int(datetime.now(timezone.utc).timestamp()),
            }

            # Create token (in production, this would be done by auth service)
            token = jwt.encode(token_payload, self.secret_key, algorithm="HS256")

            # Store in session state
            st.session_state.auth_state.update(
                {
                    "authenticated": True,
                    "user": authenticated_user,
                    "token": token,
                    "refresh_token": f"refresh_{authenticated_user.user_id}_{int(time.time())}",
                    "login_time": datetime.now(timezone.utc),
                    "last_activity": datetime.now(timezone.utc),
                }
            )

            # Also store in legacy format for compatibility
            st.session_state.authenticated = True
            st.session_state.user = {
                "email": authenticated_user.email,
                "name": authenticated_user.name,
                "roles": [r.value for r in authenticated_user.roles],
                "permissions": [p.value for p in authenticated_user.permissions],
            }
            st.session_state.tenant_id = authenticated_user.tenant_id

            self._log_authentication_event("login_success", authenticated_user)

            return True

        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Token validation failed: {e}")
        except requests.RequestException as e:
            raise AuthenticationError(f"Authentication service unavailable: {e}")
        except Exception as e:
            raise AuthenticationError(f"Authentication error: {e}")

    def get_current_user(self) -> Optional[AuthenticatedUser]:
        """Get currently authenticated user."""
        auth_state = st.session_state.auth_state

        if not auth_state.get("authenticated", False):
            return None

        user = auth_state.get("user")
        if not user:
            return None

        # Check session expiration
        if user.session_expires and datetime.now(timezone.utc) > user.session_expires:
            self.logout()
            return None

        # Update last activity
        auth_state["last_activity"] = datetime.now(timezone.utc)

        return user

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self.get_current_user() is not None

    def require_authentication(self) -> AuthenticatedUser:
        """
        Require authentication, show login form if not authenticated.

        Returns:
            AuthenticatedUser: Current authenticated user

        Raises:
            SystemExit: If user not authenticated (stops execution)
        """
        user = self.get_current_user()

        if not user:
            st.warning("🔐 Authentication required to access this application.")
            self.render_login_form()
            st.stop()

        return user

    def require_role(self, required_roles: List[UserRole]) -> AuthenticatedUser:
        """
        Require specific roles, show error if not authorized.

        Args:
            required_roles: List of required roles

        Returns:
            AuthenticatedUser: Current authenticated user

        Raises:
            SystemExit: If user doesn't have required roles
        """
        user = self.require_authentication()

        if not user.has_any_role(required_roles):
            role_names = [r.value.replace("_", " ").title() for r in required_roles]
            st.error(f"🚫 Access denied. Required roles: {', '.join(role_names)}")
            st.info(f"Your roles: {', '.join(r.value.replace('_', ' ').title() for r in user.roles)}")
            st.stop()

        return user

    def require_permission(self, required_permissions: List[Permission]) -> AuthenticatedUser:
        """
        Require specific permissions, show error if not authorized.

        Args:
            required_permissions: List of required permissions

        Returns:
            AuthenticatedUser: Current authenticated user

        Raises:
            SystemExit: If user doesn't have required permissions
        """
        user = self.require_authentication()

        if not user.has_all_permissions(required_permissions):
            missing_perms = [p.value for p in required_permissions if not user.has_permission(p)]
            st.error(f"🚫 Access denied. Missing permissions: {', '.join(missing_perms)}")
            st.info(f"Your permissions: {len(user.permissions)} granted")
            st.stop()

        return user

    def logout(self):
        """Log out current user."""
        user = st.session_state.auth_state.get("user")
        if user:
            self._log_authentication_event("logout", user)

        # Clear auth state
        st.session_state.auth_state = {
            "authenticated": False,
            "user": None,
            "token": None,
            "refresh_token": None,
            "login_time": None,
            "last_activity": None,
        }

        # Clear legacy state
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.tenant_id = None

        st.success("✅ Successfully logged out")
        st.rerun()

    def render_user_info(self, container=None):
        """
        Render current user information widget.

        Args:
            container: Streamlit container to render in
        """
        if container is None:
            container = st

        user = self.get_current_user()
        if not user:
            return

        with container.container():
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"""
                **👤 {user.name}**  
                📧 {user.email}  
                🏢 {user.tenant_id}
                """)

            with col2:
                # Role badge
                primary_role = user.roles[0] if user.roles else UserRole.VIEWER
                role_display = primary_role.value.replace("_", " ").title()

                st.markdown(
                    f"""
                <div style="background-color: #E6FFFA; color: #234E52; padding: 0.5rem; 
                           border-radius: 8px; text-align: center; font-weight: 600;">
                    🎭 {role_display}
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col3:
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()

    def render_session_info(self, container=None):
        """
        Render session information.

        Args:
            container: Streamlit container to render in
        """
        if container is None:
            container = st

        auth_state = st.session_state.auth_state
        user = auth_state.get("user")

        if not user:
            return

        with container.expander("📊 Session Information"):
            col1, col2 = st.columns(2)

            with col1:
                login_time = auth_state.get("login_time")
                if login_time:
                    st.write(f"**Login Time:** {login_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")

                last_activity = auth_state.get("last_activity")
                if last_activity:
                    st.write(f"**Last Activity:** {last_activity.strftime('%Y-%m-%d %H:%M:%S UTC')}")

            with col2:
                if user.session_expires:
                    st.write(f"**Session Expires:** {user.session_expires.strftime('%Y-%m-%d %H:%M:%S UTC')}")

                time_remaining = user.session_expires - datetime.now(timezone.utc)
                hours_remaining = int(time_remaining.total_seconds() // 3600)
                st.write(f"**Time Remaining:** {hours_remaining} hours")

            # Permissions summary
            st.write(f"**Permissions:** {len(user.permissions)} granted")

            # Token info (masked)
            token = auth_state.get("token", "")
            if token:
                masked_token = token[:10] + "..." + token[-10:] if len(token) > 20 else "***"
                st.code(f"Token: {masked_token}")

    def _validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token.

        Args:
            token: JWT token to validate

        Returns:
            Dict: Token payload if valid

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.now(timezone.utc).timestamp() > exp:
                raise AuthenticationError("Token has expired")

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")

    def _log_authentication_event(self, event_type: str, user: AuthenticatedUser):
        """Log authentication events for audit trail."""
        # In production, this would send to centralized logging system
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user_id": user.user_id,
            "email": user.email,
            "tenant_id": user.tenant_id,
            "ip_address": "127.0.0.1",  # Would get real IP in production
            "user_agent": "Streamlit App",  # Would get real user agent
        }

        # Store in session for demo purposes
        if "auth_events" not in st.session_state:
            st.session_state.auth_events = []

        st.session_state.auth_events.append(event)

        # Keep only last 100 events
        if len(st.session_state.auth_events) > 100:
            st.session_state.auth_events = st.session_state.auth_events[-100:]


def create_auth_middleware():
    """Create authentication middleware instance."""
    return StreamlitAuthenticator()


def require_authentication() -> AuthenticatedUser:
    """Convenient function to require authentication."""
    auth = create_auth_middleware()
    return auth.require_authentication()


def require_role(*roles: UserRole) -> AuthenticatedUser:
    """Convenient function to require specific roles."""
    auth = create_auth_middleware()
    return auth.require_role(list(roles))


def require_permission(*permissions: Permission) -> AuthenticatedUser:
    """Convenient function to require specific permissions."""
    auth = create_auth_middleware()
    return auth.require_permission(list(permissions))


def get_current_user() -> Optional[AuthenticatedUser]:
    """Get current authenticated user."""
    auth = create_auth_middleware()
    return auth.get_current_user()


# Demo authentication component
def demo_auth_component():
    """Demo authentication component for testing."""
    st.title("🔐 Authentication Demo")

    auth = create_auth_middleware()

    if not auth.is_authenticated():
        st.info("Please log in to continue")
        auth.render_login_form()
    else:
        user = auth.get_current_user()

        st.success("✅ Successfully authenticated!")

        # User info
        auth.render_user_info()

        # Role and permission checks
        st.subheader("🎭 Access Control Demo")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Your Roles:**")
            for role in user.roles:
                st.write(f"- {role.value.replace('_', ' ').title()}")

        with col2:
            st.write("**Your Permissions:**")
            for perm in user.permissions[:10]:  # Show first 10
                st.write(f"- {perm.value}")

            if len(user.permissions) > 10:
                st.write(f"... and {len(user.permissions) - 10} more")

        # Test access controls
        st.subheader("🚦 Access Control Tests")

        if st.button("Test Admin Access"):
            try:
                auth.require_role([UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN])
                st.success("✅ Admin access granted!")
            except:
                st.error("❌ Admin access denied")

        if st.button("Test Analytics Permission"):
            try:
                auth.require_permission([Permission.VIEW_ANALYTICS])
                st.success("✅ Analytics access granted!")
            except:
                st.error("❌ Analytics access denied")

        # Session info
        auth.render_session_info()

        # Authentication events
        if "auth_events" in st.session_state and st.session_state.auth_events:
            with st.expander("📋 Recent Authentication Events"):
                for event in st.session_state.auth_events[-5:]:
                    st.json(event)


if __name__ == "__main__":
    st.set_page_config(page_title="Authentication Demo", page_icon="🔐", layout="wide")

    demo_auth_component()
