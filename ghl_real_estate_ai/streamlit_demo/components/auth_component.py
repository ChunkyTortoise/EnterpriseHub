"""
Streamlit Authentication Components.

Provides login forms, user menus, and authentication UI elements.
"""

import asyncio
from typing import Optional

import streamlit as st

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.auth_middleware import (
    check_streamlit_auth,
    clear_streamlit_auth,
    format_user_role,
    get_user_permissions,
    require_streamlit_permission,
    set_streamlit_auth,
)
from ghl_real_estate_ai.services.auth_service import User, UserRole, get_auth_service

logger = get_logger(__name__)


def check_authentication() -> Optional[User]:
    """Check if user is authenticated in current session."""
    return check_streamlit_auth()


async def _authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with credentials."""
    auth_service = get_auth_service()
    return await auth_service.authenticate_user(username, password)


def render_login_form():
    """Render the login form."""
    st.markdown(
        """
    <div style="max-width: 400px; margin: 0 auto; padding: 2rem;">
        <div style="background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🔐 Login")

    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if not username or not password:
                st.error("❌ Please enter both username and password")
                return

            try:
                # Run authentication in async context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                user = loop.run_until_complete(_authenticate_user(username, password))
                loop.close()

                if user:
                    set_streamlit_auth(user)
                    st.success(f"✅ Welcome back, {user.username}!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

            except Exception as e:
                logger.error(f"Login error: {e}")
                st.error("❌ Login failed. Please try again.")

    # Demo credentials info
    with st.expander("Demo Credentials"):
        st.markdown("""
        **Admin Access:**
        - Username: `admin`
        - Password: `admin123`

        **Agent Access:**
        - Username: `jorge`
        - Password: `jorge123`

        **Viewer Access:**
        - Username: `viewer`
        - Password: `viewer123`
        """)

    st.markdown("</div></div>", unsafe_allow_html=True)


def render_user_menu(user: User):
    """Render user menu in sidebar."""
    with st.sidebar:
        st.markdown("---")

        # User info
        st.markdown(f"""
        **👤 {user.username}**
        {format_user_role(user.role)}
        📧 {user.email}
        """)

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            clear_streamlit_auth()
            st.rerun()

        # Show permissions
        with st.expander("🔐 Permissions"):
            permissions = get_user_permissions(user)
            for resource, actions in permissions.items():
                st.write(f"**{resource.title()}:**")
                perms = []
                if actions.get("read"):
                    perms.append("👀 Read")
                if actions.get("write"):
                    perms.append("✏️ Write")
                if actions.get("delete"):
                    perms.append("🗑️ Delete")
                st.write(" • ".join(perms) if perms else "❌ No access")


def require_permission(user: User, resource: str, action: str) -> bool:
    """Check permission and show error if denied."""
    try:
        require_streamlit_permission(resource, action)
        return True
    except:
        return False


def create_user_management_interface():
    """Create user management interface for admins."""
    current_user = check_streamlit_auth()

    if not current_user or current_user.role != UserRole.ADMIN:
        st.error("🚫 Admin access required")
        return

    st.markdown("#### 👥 User Management")

    # Create new user
    with st.expander("➕ Create New User"):
        with st.form("create_user_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", [role.value for role in UserRole])

            if st.form_submit_button("Create User"):
                if new_username and new_email and new_password:
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        auth_service = get_auth_service()
                        user = loop.run_until_complete(
                            auth_service.create_user(new_username, new_email, new_password, UserRole(new_role))
                        )
                        loop.close()

                        if user:
                            st.success(f"✅ User {new_username} created successfully")
                        else:
                            st.error("❌ User creation failed (may already exist)")

                    except Exception as e:
                        logger.error(f"User creation error: {e}")
                        st.error(f"❌ Error creating user: {e}")
                else:
                    st.error("❌ Please fill in all fields")

    # Initialize default users
    if st.button("🔄 Initialize Default Users"):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            auth_service = get_auth_service()
            loop.run_until_complete(auth_service.initialize_default_users())
            loop.close()

            st.success("✅ Default users initialized")

        except Exception as e:
            logger.error(f"Default user initialization error: {e}")
            st.error(f"❌ Error initializing users: {e}")


def render_access_denied(resource: str, action: str):
    """Render access denied message."""
    st.error(f"""
    🚫 **Access Denied**

    You don't have permission to {action} {resource}.

    Please contact an administrator if you need access.
    """)


def render_authentication_status():
    """Render current authentication status."""
    user = check_streamlit_auth()

    if user:
        st.success(f"🟢 Authenticated as {user.username} ({user.role.value})")
        return user
    else:
        st.warning("🟡 Not authenticated")
        return None


# Authentication decorators for Streamlit functions


def auth_required(func):
    """Decorator requiring authentication for Streamlit functions."""

    def wrapper(*args, **kwargs):
        user = check_streamlit_auth()
        if not user:
            st.error("🔒 Authentication required")
            render_login_form()
            st.stop()
        return func(user, *args, **kwargs)

    return wrapper


def permission_required(resource: str, action: str):
    """Decorator requiring specific permission for Streamlit functions."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            user = require_streamlit_permission(resource, action)
            return func(user, *args, **kwargs)

        return wrapper

    return decorator


def admin_required(func):
    """Decorator requiring admin role for Streamlit functions."""

    def wrapper(*args, **kwargs):
        user = check_streamlit_auth()
        if not user or user.role != UserRole.ADMIN:
            render_access_denied("admin functions", "access")
            st.stop()
        return func(user, *args, **kwargs)

    return wrapper
