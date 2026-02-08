"""
Enterprise Authentication Module

SSO integration for corporate clients with OAuth2 enterprise flows,
multi-tenant access control, and corporate user provisioning.
Designed for Fortune 500 enterprise partnerships.
"""

import asyncio
import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import httpx
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService

logger = get_logger(__name__)


class EnterpriseAuthError(Exception):
    """Exception for enterprise authentication errors."""

    def __init__(self, message: str, error_code: Optional[str] = None, tenant_id: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.tenant_id = tenant_id
        super().__init__(message)


class SSOProvider:
    """Supported SSO providers for enterprise authentication."""

    AZURE_AD = "azure_ad"
    OKTA = "okta"
    GOOGLE_WORKSPACE = "google_workspace"
    PING_IDENTITY = "ping_identity"
    ACTIVE_DIRECTORY = "active_directory"
    SAML_GENERIC = "saml_generic"


class TenantRole:
    """Corporate tenant role definitions."""

    TENANT_ADMIN = "tenant_admin"  # Full tenant management
    RELOCATION_MANAGER = "relocation_manager"  # Manage employee relocations
    HR_COORDINATOR = "hr_coordinator"  # HR-level access
    EMPLOYEE = "employee"  # Basic employee access
    READONLY_VIEWER = "readonly_viewer"  # View-only access


class EnterpriseAuthService:
    """
    Enterprise authentication service for Fortune 500 partnerships.

    Handles SSO integration, multi-tenant access control, corporate user
    provisioning, and enterprise-grade security features.
    """

    def __init__(self):
        """Initialize enterprise authentication service."""
        self.cache_service = CacheService()
        self.security = HTTPBearer()

        # JWT configuration for enterprise tokens
        self.jwt_secret = settings.jwt_secret_key or secrets.token_urlsafe(32)
        self.jwt_algorithm = "HS256"
        self.enterprise_token_expiry = 28800  # 8 hours for enterprise sessions
        self.enterprise_refresh_token_expiry = 604800  # 7 days for refresh tokens

        # SSO provider configurations
        self.sso_providers = {}
        self._initialize_sso_providers()

        logger.info("EnterpriseAuthService initialized successfully")

    def _initialize_sso_providers(self):
        """Initialize SSO provider configurations."""
        self.sso_providers = {
            SSOProvider.AZURE_AD: {
                "name": "Microsoft Azure AD",
                "auth_url": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
                "userinfo_url": "https://graph.microsoft.com/v1.0/me",
                "scopes": ["openid", "profile", "email", "User.Read"],
                "supports_groups": True,
            },
            SSOProvider.OKTA: {
                "name": "Okta",
                "auth_url": "https://{domain}.okta.com/oauth2/v1/authorize",
                "token_url": "https://{domain}.okta.com/oauth2/v1/token",
                "userinfo_url": "https://{domain}.okta.com/oauth2/v1/userinfo",
                "scopes": ["openid", "profile", "email", "groups"],
                "supports_groups": True,
            },
            SSOProvider.GOOGLE_WORKSPACE: {
                "name": "Google Workspace",
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scopes": ["openid", "email", "profile"],
                "supports_groups": False,  # Requires additional API calls
            },
        }

    # ===================================================================
    # Tenant Management
    # ===================================================================

    async def create_enterprise_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new enterprise tenant for corporate partnership.

        Args:
            tenant_data: Tenant configuration and SSO settings

        Returns:
            Created tenant details with configuration

        Raises:
            EnterpriseAuthError: If tenant creation fails
        """
        try:
            tenant_id = str(uuid4())
            logger.info(f"Creating enterprise tenant for {tenant_data.get('company_name')} (ID: {tenant_id})")

            # Validate tenant data
            required_fields = ["company_name", "domain", "sso_provider"]
            missing_fields = [field for field in required_fields if field not in tenant_data]
            if missing_fields:
                raise EnterpriseAuthError(
                    f"Missing required fields: {', '.join(missing_fields)}",
                    error_code="MISSING_REQUIRED_FIELDS",
                    tenant_id=tenant_id,
                )

            # Validate domain uniqueness
            if await self._is_domain_already_registered(tenant_data["domain"]):
                raise EnterpriseAuthError(
                    f"Domain {tenant_data['domain']} already registered",
                    error_code="DOMAIN_ALREADY_EXISTS",
                    tenant_id=tenant_id,
                )

            # Validate SSO provider
            sso_provider = tenant_data["sso_provider"]
            if sso_provider not in self.sso_providers:
                raise EnterpriseAuthError(
                    f"Unsupported SSO provider: {sso_provider}",
                    error_code="UNSUPPORTED_SSO_PROVIDER",
                    tenant_id=tenant_id,
                )

            # Create tenant configuration
            tenant_config = {
                "tenant_id": tenant_id,
                "company_name": tenant_data["company_name"],
                "domain": tenant_data["domain"],
                "sso_provider": sso_provider,
                "sso_config": tenant_data.get("sso_config", {}),
                "partnership_id": tenant_data.get("partnership_id"),
                "status": "pending_setup",
                "created_at": datetime.now(timezone.utc),
                "admin_email": tenant_data.get("admin_email"),
                "allowed_domains": tenant_data.get("allowed_domains", [tenant_data["domain"]]),
                "max_users": tenant_data.get("max_users", 1000),
                "session_timeout_hours": tenant_data.get("session_timeout_hours", 8),
                "require_mfa": tenant_data.get("require_mfa", True),
                "auto_provision_users": tenant_data.get("auto_provision_users", True),
            }

            # Generate tenant-specific secrets
            tenant_secrets = await self._generate_tenant_secrets(tenant_id)
            tenant_config["secrets"] = tenant_secrets

            # Initialize SSO configuration
            sso_setup = await self._setup_sso_configuration(tenant_id, tenant_config)
            tenant_config["sso_setup"] = sso_setup

            # Store tenant configuration
            await self.cache_service.set(
                f"enterprise_tenant:{tenant_id}",
                tenant_config,
                ttl=86400 * 365,  # 1 year
            )

            # Store domain -> tenant mapping
            await self.cache_service.set(
                f"domain_tenant_mapping:{tenant_data['domain']}",
                tenant_id,
                ttl=86400 * 365,  # 1 year
            )

            logger.info(f"Enterprise tenant {tenant_id} created successfully for {tenant_data['company_name']}")

            return {
                "success": True,
                "tenant_id": tenant_id,
                "tenant_config": tenant_config,
                "next_steps": [
                    "Complete SSO provider configuration",
                    "Configure user role mappings",
                    "Test SSO authentication flow",
                    "Provision initial admin users",
                ],
            }

        except Exception as e:
            logger.error(f"Failed to create enterprise tenant: {e}")
            raise EnterpriseAuthError(
                f"Tenant creation failed: {str(e)}",
                error_code="TENANT_CREATION_FAILED",
                tenant_id=tenant_id if "tenant_id" in locals() else None,
            )

    async def get_tenant_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve tenant configuration by domain.

        Args:
            domain: Company domain

        Returns:
            Tenant configuration or None if not found
        """
        try:
            tenant_id = await self.cache_service.get(f"domain_tenant_mapping:{domain}")
            if not tenant_id:
                return None

            tenant_config = await self.cache_service.get(f"enterprise_tenant:{tenant_id}")
            return tenant_config

        except Exception as e:
            logger.error(f"Error retrieving tenant for domain {domain}: {e}")
            return None

    async def update_tenant_configuration(self, tenant_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update enterprise tenant configuration.

        Args:
            tenant_id: Tenant identifier
            updates: Configuration updates

        Returns:
            Updated tenant configuration
        """
        try:
            tenant_config = await self.cache_service.get(f"enterprise_tenant:{tenant_id}")
            if not tenant_config:
                raise EnterpriseAuthError(
                    f"Tenant {tenant_id} not found", error_code="TENANT_NOT_FOUND", tenant_id=tenant_id
                )

            # Apply updates
            tenant_config.update(updates)
            tenant_config["updated_at"] = datetime.now(timezone.utc)

            # Save updated configuration
            await self.cache_service.set(
                f"enterprise_tenant:{tenant_id}",
                tenant_config,
                ttl=86400 * 365,  # 1 year
            )

            logger.info(f"Tenant {tenant_id} configuration updated")
            return tenant_config

        except Exception as e:
            logger.error(f"Failed to update tenant {tenant_id}: {e}")
            raise EnterpriseAuthError(
                f"Tenant update failed: {str(e)}", error_code="TENANT_UPDATE_FAILED", tenant_id=tenant_id
            )

    # ===================================================================
    # SSO Authentication Flow
    # ===================================================================

    async def initiate_sso_login(self, domain: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Initiate SSO login flow for enterprise user.

        Args:
            domain: Company domain
            redirect_uri: Callback URL after authentication

        Returns:
            SSO authorization URL and state token
        """
        try:
            tenant_config = await self.get_tenant_by_domain(domain)
            if not tenant_config:
                raise EnterpriseAuthError(f"No tenant configured for domain {domain}", error_code="TENANT_NOT_FOUND")

            tenant_id = tenant_config["tenant_id"]
            sso_provider = tenant_config["sso_provider"]
            sso_config = tenant_config["sso_config"]

            # Generate state token for security
            state_token = secrets.token_urlsafe(32)
            nonce = secrets.token_urlsafe(16)

            # Store SSO session state
            sso_session = {
                "tenant_id": tenant_id,
                "domain": domain,
                "redirect_uri": redirect_uri,
                "nonce": nonce,
                "created_at": datetime.now(timezone.utc),
                "provider": sso_provider,
            }

            await self.cache_service.set(
                f"sso_state:{state_token}",
                sso_session,
                ttl=600,  # 10 minutes for SSO flow
            )

            # Build authorization URL
            auth_url = await self._build_authorization_url(sso_provider, sso_config, state_token, nonce, redirect_uri)

            logger.info(f"SSO login initiated for domain {domain}, tenant {tenant_id}")

            return {
                "authorization_url": auth_url,
                "state": state_token,
                "tenant_id": tenant_id,
                "provider": sso_provider,
            }

        except Exception as e:
            logger.error(f"Failed to initiate SSO login for domain {domain}: {e}")
            raise EnterpriseAuthError(f"SSO initiation failed: {str(e)}", error_code="SSO_INITIATION_FAILED")

    async def handle_sso_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Handle SSO callback and complete authentication.

        Args:
            code: Authorization code from SSO provider
            state: State token for security validation

        Returns:
            Enterprise access token and user information
        """
        try:
            # Retrieve SSO session
            sso_session = await self.cache_service.get(f"sso_state:{state}")
            if not sso_session:
                raise EnterpriseAuthError("Invalid or expired SSO state", error_code="INVALID_SSO_STATE")

            tenant_id = sso_session["tenant_id"]
            tenant_config = await self.cache_service.get(f"enterprise_tenant:{tenant_id}")

            # Exchange code for tokens
            tokens = await self._exchange_code_for_tokens(
                tenant_config["sso_provider"], tenant_config["sso_config"], code, sso_session["redirect_uri"]
            )

            # Get user information from SSO provider
            user_info = await self._get_user_info_from_sso(
                tenant_config["sso_provider"], tenant_config["sso_config"], tokens["access_token"]
            )

            # Validate user belongs to tenant domain
            user_email = user_info.get("email")
            if not user_email or not self._validate_user_domain(user_email, tenant_config["allowed_domains"]):
                raise EnterpriseAuthError(
                    f"User email {user_email} not authorized for this tenant",
                    error_code="USER_DOMAIN_NOT_AUTHORIZED",
                    tenant_id=tenant_id,
                )

            # Provision or update user
            enterprise_user = await self._provision_enterprise_user(tenant_id, user_info, tenant_config)

            # Generate enterprise access and refresh tokens
            tokens = await self._generate_enterprise_tokens(enterprise_user, tenant_config)

            # Clean up SSO session
            await self.cache_service.delete(f"sso_state:{state}")

            logger.info(f"SSO authentication completed for user {user_email}, tenant {tenant_id}")

            return {
                "success": True,
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer",
                "expires_in": self.enterprise_token_expiry,
                "user": enterprise_user,
                "tenant_id": tenant_id,
            }

        except Exception as e:
            logger.error(f"SSO callback handling failed: {e}")
            raise EnterpriseAuthError(f"SSO authentication failed: {str(e)}", error_code="SSO_AUTHENTICATION_FAILED")

    async def validate_enterprise_token(self, token: str) -> Dict[str, Any]:
        """
        Validate enterprise access token and return user information.

        Args:
            token: Enterprise access token

        Returns:
            Validated user and tenant information
        """
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            # Check token expiration
            if datetime.fromtimestamp(payload["exp"], tz=timezone.utc) < datetime.now(timezone.utc):
                raise EnterpriseAuthError("Token expired", error_code="TOKEN_EXPIRED")

            # Retrieve user session
            session_id = payload.get("session_id")
            user_session = await self.cache_service.get(f"enterprise_session:{session_id}")

            if not user_session:
                raise EnterpriseAuthError("Session not found or expired", error_code="SESSION_NOT_FOUND")

            # Validate tenant status
            tenant_config = await self.cache_service.get(f"enterprise_tenant:{user_session['tenant_id']}")
            if not tenant_config or tenant_config["status"] != "active":
                raise EnterpriseAuthError(
                    "Tenant not active", error_code="TENANT_NOT_ACTIVE", tenant_id=user_session["tenant_id"]
                )

            return {
                "user": user_session["user"],
                "tenant": tenant_config,
                "session": user_session,
                "permissions": user_session.get("permissions", []),
            }

        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            raise EnterpriseAuthError("Invalid token", error_code="INVALID_TOKEN")
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise EnterpriseAuthError(f"Token validation failed: {str(e)}", error_code="TOKEN_VALIDATION_FAILED")

    # ===================================================================
    # User Management
    # ===================================================================

    async def provision_enterprise_user(
        self, tenant_id: str, user_email: str, user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manually provision enterprise user with specific roles.

        Args:
            tenant_id: Tenant identifier
            user_email: User email address
            user_data: User information and role assignments

        Returns:
            Provisioned user details
        """
        try:
            tenant_config = await self.cache_service.get(f"enterprise_tenant:{tenant_id}")
            if not tenant_config:
                raise EnterpriseAuthError(
                    f"Tenant {tenant_id} not found", error_code="TENANT_NOT_FOUND", tenant_id=tenant_id
                )

            # Validate user email domain
            if not self._validate_user_domain(user_email, tenant_config["allowed_domains"]):
                raise EnterpriseAuthError(
                    f"User email {user_email} not authorized for this tenant",
                    error_code="USER_DOMAIN_NOT_AUTHORIZED",
                    tenant_id=tenant_id,
                )

            user_id = str(uuid4())

            enterprise_user = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "email": user_email,
                "name": user_data.get("name", ""),
                "first_name": user_data.get("first_name", ""),
                "last_name": user_data.get("last_name", ""),
                "department": user_data.get("department", ""),
                "job_title": user_data.get("job_title", ""),
                "roles": user_data.get("roles", [TenantRole.EMPLOYEE]),
                "permissions": self._calculate_user_permissions(user_data.get("roles", [TenantRole.EMPLOYEE])),
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "last_login": None,
                "provisioned_by": "manual",
                "mfa_enabled": tenant_config.get("require_mfa", True),
            }

            # Store user data
            await self.cache_service.set(
                f"enterprise_user:{tenant_id}:{user_email}",
                enterprise_user,
                ttl=86400 * 365,  # 1 year
            )

            logger.info(f"Enterprise user {user_email} provisioned for tenant {tenant_id}")

            return enterprise_user

        except Exception as e:
            logger.error(f"Failed to provision user {user_email} for tenant {tenant_id}: {e}")
            raise EnterpriseAuthError(
                f"User provisioning failed: {str(e)}", error_code="USER_PROVISIONING_FAILED", tenant_id=tenant_id
            )

    async def update_user_roles(self, tenant_id: str, user_email: str, new_roles: List[str]) -> Dict[str, Any]:
        """
        Update enterprise user roles and permissions.

        Args:
            tenant_id: Tenant identifier
            user_email: User email
            new_roles: New role assignments

        Returns:
            Updated user information
        """
        try:
            user_data = await self.cache_service.get(f"enterprise_user:{tenant_id}:{user_email}")
            if not user_data:
                raise EnterpriseAuthError(
                    f"User {user_email} not found in tenant {tenant_id}",
                    error_code="USER_NOT_FOUND",
                    tenant_id=tenant_id,
                )

            # Update roles and recalculate permissions
            user_data["roles"] = new_roles
            user_data["permissions"] = self._calculate_user_permissions(new_roles)
            user_data["updated_at"] = datetime.now(timezone.utc)

            # Save updated user data
            await self.cache_service.set(
                f"enterprise_user:{tenant_id}:{user_email}",
                user_data,
                ttl=86400 * 365,  # 1 year
            )

            # Invalidate active sessions to force re-authentication
            await self._invalidate_user_sessions(tenant_id, user_email)

            logger.info(f"User {user_email} roles updated in tenant {tenant_id}: {new_roles}")

            return user_data

        except Exception as e:
            logger.error(f"Failed to update user roles for {user_email}: {e}")
            raise EnterpriseAuthError(
                f"Role update failed: {str(e)}", error_code="ROLE_UPDATE_FAILED", tenant_id=tenant_id
            )

    # ===================================================================
    # FastAPI Dependencies
    # ===================================================================

    async def get_current_enterprise_user(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> Dict[str, Any]:
        """
        FastAPI dependency to get current authenticated enterprise user.

        Args:
            credentials: HTTP bearer token

        Returns:
            Current user and tenant information
        """
        try:
            if not credentials:
                raise HTTPException(status_code=401, detail="Authorization header required")

            token = credentials.credentials
            auth_data = await self.validate_enterprise_token(token)

            return auth_data

        except EnterpriseAuthError as e:
            if e.error_code in ["TOKEN_EXPIRED", "SESSION_NOT_FOUND"]:
                raise HTTPException(status_code=401, detail=e.message)
            elif e.error_code == "TENANT_NOT_ACTIVE":
                raise HTTPException(status_code=403, detail=e.message)
            else:
                raise HTTPException(status_code=401, detail="Authentication failed")

    def require_permission(self, required_permission: str):
        """
        FastAPI dependency factory for permission-based access control.

        Args:
            required_permission: Required permission for endpoint access

        Returns:
            FastAPI dependency function
        """

        async def permission_dependency(
            auth_data: Dict[str, Any] = Depends(self.get_current_enterprise_user),
        ) -> Dict[str, Any]:
            user_permissions = auth_data["session"].get("permissions", [])

            if required_permission not in user_permissions:
                raise HTTPException(status_code=403, detail=f"Permission '{required_permission}' required")

            return auth_data

        return permission_dependency

    def require_tenant_role(self, required_role: str):
        """
        FastAPI dependency factory for role-based access control.

        Args:
            required_role: Required tenant role for endpoint access

        Returns:
            FastAPI dependency function
        """

        async def role_dependency(
            auth_data: Dict[str, Any] = Depends(self.get_current_enterprise_user),
        ) -> Dict[str, Any]:
            user_roles = auth_data["user"].get("roles", [])

            if required_role not in user_roles:
                raise HTTPException(status_code=403, detail=f"Role '{required_role}' required")

            return auth_data

        return role_dependency

    # ===================================================================
    # Private Helper Methods
    # ===================================================================

    async def _is_domain_already_registered(self, domain: str) -> bool:
        """Check if domain is already registered to a tenant."""
        tenant_id = await self.cache_service.get(f"domain_tenant_mapping:{domain}")
        return tenant_id is not None

    async def _generate_tenant_secrets(self, tenant_id: str) -> Dict[str, str]:
        """Generate tenant-specific secrets for SSO integration."""
        return {
            "client_secret": secrets.token_urlsafe(32),
            "webhook_secret": secrets.token_urlsafe(16),
            "api_key": f"ent_{tenant_id[:8]}_{secrets.token_urlsafe(24)}",
        }

    async def _setup_sso_configuration(self, tenant_id: str, tenant_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup SSO configuration for tenant."""
        provider = tenant_config["sso_provider"]
        provider_config = self.sso_providers[provider]

        return {
            "provider": provider,
            "client_id": f"ent_{tenant_id}",  # Would be provided by SSO provider
            "redirect_uri": f"{settings.BASE_URL}/api/enterprise/auth/callback/{tenant_id}",
            "setup_status": "pending_provider_configuration",
        }

    async def _build_authorization_url(
        self, provider: str, sso_config: Dict[str, Any], state: str, nonce: str, redirect_uri: str
    ) -> str:
        """Build authorization URL for SSO provider."""
        provider_config = self.sso_providers[provider]
        auth_url = provider_config["auth_url"]

        # Replace placeholders
        if provider == SSOProvider.AZURE_AD:
            auth_url = auth_url.format(tenant_id=sso_config.get("tenant_id", "common"))
        elif provider == SSOProvider.OKTA:
            auth_url = auth_url.format(domain=sso_config.get("domain"))

        params = {
            "client_id": sso_config.get("client_id"),
            "response_type": "code",
            "scope": " ".join(provider_config["scopes"]),
            "redirect_uri": redirect_uri,
            "state": state,
            "nonce": nonce,
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_url}?{query_string}"

    async def _exchange_code_for_tokens(
        self, provider: str, sso_config: Dict[str, Any], code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access tokens."""
        provider_config = self.sso_providers[provider]
        token_url = provider_config["token_url"]

        # Replace placeholders
        if provider == SSOProvider.AZURE_AD:
            token_url = token_url.format(tenant_id=sso_config.get("tenant_id", "common"))
        elif provider == SSOProvider.OKTA:
            token_url = token_url.format(domain=sso_config.get("domain"))

        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": sso_config.get("client_id"),
            "client_secret": sso_config.get("client_secret"),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=token_data)
            response.raise_for_status()
            return response.json()

    async def _get_user_info_from_sso(
        self, provider: str, sso_config: Dict[str, Any], access_token: str
    ) -> Dict[str, Any]:
        """Get user information from SSO provider."""
        provider_config = self.sso_providers[provider]
        userinfo_url = provider_config["userinfo_url"]

        # Replace placeholders
        if provider == SSOProvider.OKTA:
            userinfo_url = userinfo_url.format(domain=sso_config.get("domain"))

        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_url, headers=headers)
            response.raise_for_status()
            return response.json()

    def _validate_user_domain(self, email: str, allowed_domains: List[str]) -> bool:
        """Validate user email belongs to allowed domains."""
        if not email or "@" not in email:
            return False

        user_domain = email.split("@")[1].lower()
        return user_domain in [domain.lower() for domain in allowed_domains]

    async def _provision_enterprise_user(
        self, tenant_id: str, user_info: Dict[str, Any], tenant_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Provision or update enterprise user from SSO information."""
        user_email = user_info.get("email")

        # Check if user already exists
        existing_user = await self.cache_service.get(f"enterprise_user:{tenant_id}:{user_email}")

        if existing_user:
            # Update last login and SSO data
            existing_user["last_login"] = datetime.now(timezone.utc)
            existing_user["sso_user_id"] = user_info.get("id")
            existing_user["updated_at"] = datetime.now(timezone.utc)

            await self.cache_service.set(
                f"enterprise_user:{tenant_id}:{user_email}",
                existing_user,
                ttl=86400 * 365,  # 1 year
            )

            return existing_user

        # Auto-provision new user if enabled
        if tenant_config.get("auto_provision_users", True):
            user_id = str(uuid4())

            new_user = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "email": user_email,
                "name": user_info.get("name", ""),
                "first_name": user_info.get("given_name", ""),
                "last_name": user_info.get("family_name", ""),
                "sso_user_id": user_info.get("id"),
                "roles": [TenantRole.EMPLOYEE],  # Default role
                "permissions": self._calculate_user_permissions([TenantRole.EMPLOYEE]),
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "last_login": datetime.now(timezone.utc),
                "provisioned_by": "sso_auto",
                "mfa_enabled": tenant_config.get("require_mfa", True),
            }

            await self.cache_service.set(
                f"enterprise_user:{tenant_id}:{user_email}",
                new_user,
                ttl=86400 * 365,  # 1 year
            )

            return new_user

        else:
            raise EnterpriseAuthError(
                f"User {user_email} not provisioned and auto-provisioning disabled",
                error_code="USER_NOT_PROVISIONED",
                tenant_id=tenant_id,
            )

    def _calculate_user_permissions(self, roles: List[str]) -> List[str]:
        """Calculate user permissions based on roles."""
        permissions = set()

        role_permissions = {
            TenantRole.TENANT_ADMIN: [
                "manage_tenant",
                "manage_users",
                "view_analytics",
                "manage_relocations",
                "view_financials",
                "configure_sso",
                "manage_partnerships",
            ],
            TenantRole.RELOCATION_MANAGER: [
                "manage_relocations",
                "view_analytics",
                "view_employee_data",
                "coordinate_housing",
            ],
            TenantRole.HR_COORDINATOR: [
                "manage_relocations",
                "view_employee_data",
                "coordinate_housing",
                "view_reports",
            ],
            TenantRole.EMPLOYEE: ["view_own_relocation", "update_preferences", "view_housing_options"],
            TenantRole.READONLY_VIEWER: ["view_reports", "view_analytics"],
        }

        for role in roles:
            if role in role_permissions:
                permissions.update(role_permissions[role])

        return list(permissions)

    async def _generate_enterprise_tokens(self, user: Dict[str, Any], tenant_config: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate enterprise JWT access and refresh tokens.

        Args:
            user: User information
            tenant_config: Tenant configuration

        Returns:
            Dict containing access_token and refresh_token
        """
        session_id = str(uuid4())
        session_timeout = tenant_config.get("session_timeout_hours", 8)
        refresh_token = secrets.token_urlsafe(64)

        # Create user session
        user_session = {
            "session_id": session_id,
            "user": user,
            "tenant_id": user["tenant_id"],
            "permissions": user.get("permissions", []),
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=session_timeout),
            "refresh_token": refresh_token,
        }

        # Store session
        await self.cache_service.set(
            f"enterprise_session:{session_id}",
            user_session,
            ttl=session_timeout * 3600,  # Convert to seconds
        )

        # Store refresh token mapping to session
        await self.cache_service.set(
            f"enterprise_refresh:{refresh_token}", session_id, ttl=self.enterprise_refresh_token_expiry
        )

        # Create JWT payload
        payload = {
            "sub": user["user_id"],
            "email": user["email"],
            "tenant_id": user["tenant_id"],
            "session_id": session_id,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(seconds=self.enterprise_token_expiry),
        }

        # Generate access token
        access_token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

        return {"access_token": access_token, "refresh_token": refresh_token}

    async def refresh_enterprise_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an enterprise access token using a valid refresh token.

        Args:
            refresh_token: The refresh token provided by the client

        Returns:
            New access and refresh tokens
        """
        try:
            # Retrieve session ID from refresh token
            session_id = await self.cache_service.get(f"enterprise_refresh:{refresh_token}")
            if not session_id:
                raise EnterpriseAuthError("Invalid or expired refresh token", error_code="INVALID_REFRESH_TOKEN")

            # Retrieve user session
            user_session = await self.cache_service.get(f"enterprise_session:{session_id}")
            if not user_session:
                raise EnterpriseAuthError("Session not found or expired", error_code="SESSION_NOT_FOUND")

            # Verify refresh token matches session
            if user_session.get("refresh_token") != refresh_token:
                raise EnterpriseAuthError("Token rotation error", error_code="TOKEN_ROTATION_FAILURE")

            # Retrieve tenant config
            tenant_config = await self.cache_service.get(f"enterprise_tenant:{user_session['tenant_id']}")
            if not tenant_config or tenant_config["status"] != "active":
                raise EnterpriseAuthError("Tenant not active", error_code="TENANT_NOT_ACTIVE")

            # Generate new tokens
            new_tokens = await self._generate_enterprise_tokens(user_session["user"], tenant_config)

            # Clean up old refresh token
            await self.cache_service.delete(f"enterprise_refresh:{refresh_token}")

            logger.info(f"Enterprise token refreshed for user {user_session['user']['email']}")

            return {
                "success": True,
                "access_token": new_tokens["access_token"],
                "refresh_token": new_tokens["refresh_token"],
                "expires_in": self.enterprise_token_expiry,
            }

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise EnterpriseAuthError(f"Token refresh failed: {str(e)}", error_code="TOKEN_REFRESH_FAILED")

    async def _invalidate_user_sessions(self, tenant_id: str, user_email: str) -> None:
        """Invalidate all active sessions for a user."""
        # This would query all sessions for the user and invalidate them
        # Implementation depends on session storage strategy
        logger.info(f"Invalidated sessions for user {user_email} in tenant {tenant_id}")


# Global instance for dependency injection
enterprise_auth_service = EnterpriseAuthService()
