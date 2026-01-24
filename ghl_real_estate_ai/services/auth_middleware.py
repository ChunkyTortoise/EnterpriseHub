"""
Authentication middleware for FastAPI and Streamlit integration.

Provides authentication decorators, session management, and permission checking.
"""

import streamlit as st
from typing import Optional, Callable, Any
from functools import wraps
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth_service import get_auth_service, User, UserRole
from ghl_real_estate_ai.core.logger import get_logger

logger = get_logger(__name__)

# FastAPI Security
security = HTTPBearer()

class AuthenticationError(Exception):
    """Custom authentication error."""
    pass

class PermissionError(Exception):
    """Custom permission error."""
    pass

# FastAPI Dependencies

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """FastAPI dependency to get current authenticated user."""
    auth_service = get_auth_service()

    try:
        payload = auth_service.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user = await auth_service.get_user_by_id(payload['user_id'])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency requiring admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def get_agent_user(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency requiring agent role or higher."""
    if current_user.role not in [UserRole.ADMIN, UserRole.AGENT]:
        raise HTTPException(status_code=403, detail="Agent access required")
    return current_user

def require_permission(resource: str, action: str):
    """Decorator requiring specific permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (injected by FastAPI)
            current_user = None
            for arg in args + tuple(kwargs.values()):
                if isinstance(arg, User):
                    current_user = arg
                    break

            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            auth_service = get_auth_service()
            if not auth_service.check_permission(current_user.role, resource, action):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {resource}:{action}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Streamlit Authentication

def check_streamlit_auth() -> Optional[User]:
    """Check Streamlit session for authenticated user."""
    if 'authenticated_user' in st.session_state:
        return st.session_state.authenticated_user
    return None

def set_streamlit_auth(user: User):
    """Set authenticated user in Streamlit session."""
    st.session_state.authenticated_user = user
    st.session_state.auth_token = get_auth_service().create_token(user)

def clear_streamlit_auth():
    """Clear authentication from Streamlit session."""
    if 'authenticated_user' in st.session_state:
        del st.session_state.authenticated_user
    if 'auth_token' in st.session_state:
        del st.session_state.auth_token

def require_streamlit_auth() -> User:
    """
    Streamlit decorator requiring authentication.
    Returns current user or stops execution.
    """
    user = check_streamlit_auth()
    if not user:
        st.error("🔒 Authentication required")
        st.stop()
    return user

def require_streamlit_permission(resource: str, action: str) -> User:
    """
    Streamlit decorator requiring specific permission.
    Returns current user or stops execution.
    """
    user = require_streamlit_auth()
    auth_service = get_auth_service()

    if not auth_service.check_permission(user.role, resource, action):
        st.error(f"🚫 Permission denied: {resource}:{action}")
        st.stop()

    return user

def require_streamlit_role(required_role: UserRole) -> User:
    """
    Streamlit decorator requiring specific role.
    Returns current user or stops execution.
    """
    user = require_streamlit_auth()

    # Admin can access everything
    if user.role == UserRole.ADMIN:
        return user

    # Check exact role match
    if user.role != required_role:
        st.error(f"🚫 Access denied: {required_role.value} role required")
        st.stop()

    return user

# Utility functions

def get_user_permissions(user: User) -> dict:
    """Get all permissions for a user."""
    auth_service = get_auth_service()

    resources = ['dashboard', 'leads', 'properties', 'conversations', 'commission', 'performance']
    actions = ['read', 'write', 'delete']

    permissions = {}
    for resource in resources:
        permissions[resource] = {}
        for action in actions:
            permissions[resource][action] = auth_service.check_permission(
                user.role, resource, action
            )

    return permissions

def format_user_role(role: UserRole) -> str:
    """Format user role for display."""
    role_colors = {
        UserRole.ADMIN: "🔴",
        UserRole.AGENT: "🟡",
        UserRole.VIEWER: "🟢"
    }

    return f"{role_colors.get(role, '⚪')} {role.value.title()}"

# Session management

class SessionManager:
    """Manage user sessions and tokens."""

    @staticmethod
    def create_session(user: User) -> dict:
        """Create new session data."""
        auth_service = get_auth_service()
        token = auth_service.create_token(user)

        return {
            'user': user,
            'token': token,
            'permissions': get_user_permissions(user),
            'created_at': st.session_state.get('session_start_time'),
        }

    @staticmethod
    def refresh_token(user: User) -> str:
        """Refresh user token."""
        auth_service = get_auth_service()
        new_token = auth_service.create_token(user)

        if 'auth_token' in st.session_state:
            st.session_state.auth_token = new_token

        return new_token

    @staticmethod
    def is_session_valid() -> bool:
        """Check if current session is valid."""
        if 'auth_token' not in st.session_state:
            return False

        auth_service = get_auth_service()
        payload = auth_service.verify_token(st.session_state.auth_token)

        return payload is not None