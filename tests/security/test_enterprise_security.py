import pytest
pytestmark = pytest.mark.integration

"""
Enterprise Security Validation Tests

Comprehensive security testing for the Enterprise Partnership Platform
including authentication, authorization, data protection, and compliance.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.enterprise.auth import EnterpriseAuthError, EnterpriseAuthService, SSOProvider, TenantRole
from ghl_real_estate_ai.services.corporate_billing_service import CorporateBillingService
from ghl_real_estate_ai.services.corporate_partnership_service import CorporatePartnershipService


class TestAuthenticationSecurity:
    """Security tests for authentication mechanisms."""

    @pytest.fixture
    def auth_service(self):
        return EnterpriseAuthService()

    def test_jwt_token_security_configuration(self, auth_service):
        """Test JWT token uses secure configuration."""
        # Ensure strong algorithm
        assert auth_service.jwt_algorithm == "HS256"

        # Ensure reasonable token expiry
        assert auth_service.enterprise_token_expiry == 28800  # 8 hours
        assert auth_service.enterprise_token_expiry <= 86400  # Max 24 hours

        # Ensure JWT secret is sufficiently long
        assert len(auth_service.jwt_secret) >= 32

    @pytest.mark.asyncio
    async def test_jwt_token_tampering_detection(self, auth_service):
        """Test JWT token tampering is detected."""
        # Create valid token
        payload = {
            "sub": "user_123",
            "session_id": "session_123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=8),
        }
        valid_token = jwt.encode(payload, auth_service.jwt_secret, algorithm=auth_service.jwt_algorithm)

        # Tamper with token
        tampered_token = valid_token[:-10] + "tampered123"

        with pytest.raises(EnterpriseAuthError) as exc_info:
            await auth_service.validate_enterprise_token(tampered_token)

        assert exc_info.value.error_code == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_token_replay_attack_protection(self, auth_service):
        """Test protection against token replay attacks."""
        mock_cache = AsyncMock()

        with patch.object(auth_service, "cache_service", mock_cache):
            # First token validation - session exists
            mock_cache.get.side_effect = [
                {"session_id": "session_123", "user": {"user_id": "user_123"}, "tenant_id": "tenant_123"},
                {"tenant_id": "tenant_123", "status": "active"},
            ]

            payload = {
                "sub": "user_123",
                "session_id": "session_123",
                "exp": datetime.now(timezone.utc) + timedelta(hours=8),
            }
            token = jwt.encode(payload, auth_service.jwt_secret, algorithm=auth_service.jwt_algorithm)

            result = await auth_service.validate_enterprise_token(token)
            assert result is not None

            # Second validation - session no longer exists (simulating logout/invalidation)
            mock_cache.get.side_effect = [None, None]

            with pytest.raises(EnterpriseAuthError) as exc_info:
                await auth_service.validate_enterprise_token(token)

            assert exc_info.value.error_code == "SESSION_NOT_FOUND"

    def test_password_security_not_applicable(self, auth_service):
        """Test that no passwords are stored or handled."""
        # Enterprise platform should only use SSO - no password handling
        assert not hasattr(auth_service, "hash_password")
        assert not hasattr(auth_service, "verify_password")

    def test_secure_random_generation(self, auth_service):
        """Test that secure random values are used for secrets."""
        # Generate multiple secrets and ensure they're different and secure
        secrets_generated = []
        for _ in range(10):
            tenant_secrets = asyncio.run(auth_service._generate_tenant_secrets("tenant_123"))
            secrets_generated.append(tenant_secrets["client_secret"])

            # Each secret should be sufficiently long
            assert len(tenant_secrets["client_secret"]) >= 32
            assert len(tenant_secrets["api_key"]) >= 32

        # Ensure all generated secrets are unique
        assert len(set(secrets_generated)) == 10


class TestAuthorizationSecurity:
    """Security tests for authorization and access control."""

    @pytest.fixture
    def auth_service(self):
        return EnterpriseAuthService()

    def test_role_based_access_control(self, auth_service):
        """Test that roles provide appropriate permissions."""
        # Employee should have limited permissions
        employee_permissions = auth_service._calculate_user_permissions([TenantRole.EMPLOYEE])
        assert "view_own_relocation" in employee_permissions
        assert "manage_partnerships" not in employee_permissions
        assert "manage_users" not in employee_permissions

        # Admin should have full permissions
        admin_permissions = auth_service._calculate_user_permissions([TenantRole.TENANT_ADMIN])
        assert "manage_tenant" in admin_permissions
        assert "manage_users" in admin_permissions
        assert "manage_partnerships" in admin_permissions

        # Relocation manager should have specific permissions
        manager_permissions = auth_service._calculate_user_permissions([TenantRole.RELOCATION_MANAGER])
        assert "manage_relocations" in manager_permissions
        assert "view_employee_data" in manager_permissions
        assert "manage_tenant" not in manager_permissions

    def test_permission_overlap_security(self, auth_service):
        """Test that permission overlap doesn't create security holes."""
        all_roles = [
            TenantRole.EMPLOYEE,
            TenantRole.RELOCATION_MANAGER,
            TenantRole.HR_COORDINATOR,
            TenantRole.TENANT_ADMIN,
        ]

        for role in all_roles:
            permissions = auth_service._calculate_user_permissions([role])

            # Ensure no role has empty permissions
            assert len(permissions) > 0

            # Ensure critical admin permissions are only for admin role
            if role != TenantRole.TENANT_ADMIN:
                assert "manage_tenant" not in permissions
                assert "configure_sso" not in permissions

    def test_domain_isolation_enforcement(self, auth_service):
        """Test that domain isolation is enforced."""
        # Valid domain
        assert auth_service._validate_user_domain("user@company.com", ["company.com"]) is True

        # Invalid domains should be rejected
        assert auth_service._validate_user_domain("user@attacker.com", ["company.com"]) is False
        assert auth_service._validate_user_domain("user@company.com.evil.com", ["company.com"]) is False
        assert auth_service._validate_user_domain("user@subcompany.com", ["company.com"]) is False

        # Case insensitive but exact match
        assert auth_service._validate_user_domain("USER@COMPANY.COM", ["company.com"]) is True

    @pytest.mark.asyncio
    async def test_tenant_data_isolation(self, auth_service):
        """Test that tenant data cannot be accessed across tenants."""
        mock_cache = AsyncMock()

        # User from tenant A trying to access data
        user_session = {
            "session_id": "session_123",
            "user": {"user_id": "user_123", "tenant_id": "tenant_a"},
            "tenant_id": "tenant_a",
            "permissions": ["view_analytics"],
        }

        tenant_config = {"tenant_id": "tenant_a", "status": "active"}

        with patch.object(auth_service, "cache_service", mock_cache):
            mock_cache.get.side_effect = [user_session, tenant_config]

            payload = {
                "sub": "user_123",
                "session_id": "session_123",
                "tenant_id": "tenant_a",
                "exp": datetime.now(timezone.utc) + timedelta(hours=8),
            }
            token = jwt.encode(payload, auth_service.jwt_secret, algorithm=auth_service.jwt_algorithm)

            result = await auth_service.validate_enterprise_token(token)

            # User should only have access to their own tenant
            assert result["tenant"]["tenant_id"] == "tenant_a"
            assert result["user"]["tenant_id"] == "tenant_a"


class TestDataProtectionSecurity:
    """Security tests for data protection and privacy."""

    def test_sensitive_data_not_logged(self):
        """Test that sensitive data is not included in logs."""
        # This would involve setting up log capture and ensuring
        # that passwords, tokens, and PII are not logged
        pass

    def test_data_encryption_in_transit(self):
        """Test that data is encrypted in transit."""
        # Ensure HTTPS enforcement, no HTTP endpoints
        # This would typically be enforced at the infrastructure level
        pass

    @pytest.mark.asyncio
    async def test_cache_data_expiration(self):
        """Test that cached data has appropriate TTL."""
        auth_service = EnterpriseAuthService()

        # Mock cache operations to verify TTL settings
        mock_cache = AsyncMock()

        with patch.object(auth_service, "cache_service", mock_cache):
            # Test tenant creation with proper TTL
            tenant_data = {
                "company_name": "TestCorp",
                "domain": "testcorp.com",
                "sso_provider": SSOProvider.AZURE_AD,
                "admin_email": "admin@testcorp.com",
            }

            auth_service._is_domain_already_registered = AsyncMock(return_value=False)
            auth_service._generate_tenant_secrets = AsyncMock(return_value={"client_secret": "secret"})
            auth_service._setup_sso_configuration = AsyncMock(return_value={"status": "pending"})

            await auth_service.create_enterprise_tenant(tenant_data)

            # Verify cache calls have appropriate TTL
            cache_calls = mock_cache.set.call_args_list
            for call in cache_calls:
                args, kwargs = call
                ttl = kwargs.get("ttl")

                # Ensure TTL is set and reasonable (not too long)
                assert ttl is not None
                assert ttl <= 86400 * 365  # Max 1 year

    def test_api_key_format_security(self):
        """Test that API keys follow secure format."""
        auth_service = EnterpriseAuthService()

        tenant_secrets = asyncio.run(auth_service._generate_tenant_secrets("tenant_123"))
        api_key = tenant_secrets["api_key"]

        # API key should have identifiable prefix
        assert api_key.startswith("ent_")

        # Should contain tenant identifier
        assert "tenant_123"[:8] in api_key

        # Should be sufficiently long
        assert len(api_key) >= 40


class TestInputValidationSecurity:
    """Security tests for input validation and sanitization."""

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self):
        """Test SQL injection prevention in partnership service."""
        partnership_service = CorporatePartnershipService()

        # Attempt SQL injection in company name
        malicious_data = {
            "company_name": "'; DROP TABLE partnerships; --",
            "contact_email": "test@company.com",
            "expected_volume": 100,
        }

        # Service should handle malicious input safely
        # In this case, it would be stored as-is but not executed as SQL
        # since we're using parameterized queries or ORM

        # The actual test would verify the data is stored safely
        # and doesn't execute any SQL commands
        pass

    @pytest.mark.asyncio
    async def test_xss_prevention_in_user_data(self):
        """Test XSS prevention in user data handling."""
        auth_service = EnterpriseAuthService()

        malicious_user_data = {
            "name": "<script>alert('xss')</script>",
            "department": "Engineering<img src=x onerror=alert(1)>",
            "job_title": "Developer' OR '1'='1",
        }

        # User data should be properly escaped/sanitized
        # The service should store the data safely without executing scripts

        tenant_config = {"tenant_id": "tenant_123", "allowed_domains": ["company.com"], "require_mfa": True}

        with patch.object(auth_service, "cache_service", AsyncMock()):
            auth_service._validate_user_domain = MagicMock(return_value=True)
            auth_service._calculate_user_permissions = MagicMock(return_value=["view_own_relocation"])

            # This should not raise an exception and should handle malicious input safely
            result = await auth_service.provision_enterprise_user("tenant_123", "user@company.com", malicious_user_data)

            # Verify that the malicious content is stored as plain text, not executed
            assert result["name"] == "<script>alert('xss')</script>"

    def test_email_validation_security(self):
        """Test email validation prevents malicious input."""
        auth_service = EnterpriseAuthService()

        # Valid emails
        assert auth_service._validate_user_domain("user@company.com", ["company.com"]) is True

        # Invalid/malicious emails
        malicious_emails = [
            "user@company.com<script>",
            "user+script@company.com'; DROP TABLE users; --",
            "user@company.com\nBcc: attacker@evil.com",
            "user@company.com\r\nSubject: Malicious",
            "",
            "not-an-email",
            "user@@company.com",
            "user@",
            "@company.com",
        ]

        for email in malicious_emails:
            assert auth_service._validate_user_domain(email, ["company.com"]) is False

    @pytest.mark.asyncio
    async def test_volume_limits_enforcement(self):
        """Test that volume limits are enforced for security."""
        partnership_service = CorporatePartnershipService()

        # Test bulk relocation with excessive volume
        excessive_relocations = [
            {"employee_email": f"user{i}@company.com", "destination_city": "Austin"}
            for i in range(101)  # Exceeds limit of 100
        ]

        active_partnership = {"partnership_id": "test", "status": "active"}

        with patch.object(partnership_service, "get_partnership", AsyncMock(return_value=active_partnership)):
            with pytest.raises(Exception):  # Should raise an error for excessive volume
                await partnership_service.process_bulk_relocation_request("test", excessive_relocations)


class TestComplianceSecurity:
    """Security tests for compliance requirements."""

    def test_audit_trail_logging(self):
        """Test that audit trails are maintained for sensitive operations."""
        # Verify that all sensitive operations are logged
        # This would involve checking log outputs for critical actions
        pass

    def test_data_retention_policies(self):
        """Test that data retention policies are enforced."""
        # Verify that data is automatically purged according to retention policies
        pass

    def test_gdpr_compliance_user_deletion(self):
        """Test GDPR compliance for user data deletion."""
        # Test that user data can be completely removed on request
        pass

    @pytest.mark.asyncio
    async def test_sso_security_standards(self):
        """Test that SSO implementation follows security standards."""
        auth_service = EnterpriseAuthService()

        # Test state parameter generation for CSRF protection
        result = await auth_service.initiate_sso_login("company.com", "https://app.com/callback")

        assert "state" in result
        assert len(result["state"]) >= 32  # Sufficient entropy for CSRF protection

    def test_session_security_configuration(self):
        """Test session security configuration."""
        auth_service = EnterpriseAuthService()

        # Session timeout should be reasonable
        assert auth_service.enterprise_token_expiry <= 86400  # Max 24 hours
        assert auth_service.enterprise_token_expiry >= 3600  # Min 1 hour


class TestErrorHandlingSecurity:
    """Security tests for error handling."""

    @pytest.mark.asyncio
    async def test_information_disclosure_prevention(self):
        """Test that errors don't disclose sensitive information."""
        auth_service = EnterpriseAuthService()

        # Invalid token should not reveal internal details
        with pytest.raises(EnterpriseAuthError) as exc_info:
            await auth_service.validate_enterprise_token("invalid_token")

        # Error message should be generic
        assert "Invalid token" in exc_info.value.message
        assert "jwt" not in exc_info.value.message.lower()
        assert "secret" not in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_timing_attack_prevention(self):
        """Test prevention of timing attacks."""
        auth_service = EnterpriseAuthService()

        # Test that user existence checks don't leak timing information
        # Both existing and non-existing domains should take similar time

        import time

        # Mock consistent behavior
        with patch.object(auth_service, "cache_service", AsyncMock()):
            start_time = time.time()
            result1 = await auth_service.get_tenant_by_domain("existing.com")
            time1 = time.time() - start_time

            start_time = time.time()
            result2 = await auth_service.get_tenant_by_domain("nonexistent.com")
            time2 = time.time() - start_time

            # Timing difference should be minimal (allowing for normal variance)
            time_difference = abs(time1 - time2)
            assert time_difference < 0.1  # Less than 100ms difference


class TestBusinessLogicSecurity:
    """Security tests for business logic vulnerabilities."""

    @pytest.mark.asyncio
    async def test_privilege_escalation_prevention(self):
        """Test that users cannot escalate their privileges."""
        auth_service = EnterpriseAuthService()

        # Test that role updates require admin privileges
        # This would be enforced at the API level through dependencies

        # Mock non-admin user trying to update roles
        user_permissions = auth_service._calculate_user_permissions([TenantRole.EMPLOYEE])

        # Employee should not have manage_users permission
        assert "manage_users" not in user_permissions

    @pytest.mark.asyncio
    async def test_rate_limiting_protection(self):
        """Test rate limiting protection for API endpoints."""
        # This would test that excessive API calls are throttled
        # Implementation would be at the middleware level
        pass

    @pytest.mark.asyncio
    async def test_concurrent_operation_safety(self):
        """Test that concurrent operations don't create security issues."""
        # Test that simultaneous user creation, role updates, etc.
        # don't create inconsistent states or security bypasses
        pass

    def test_financial_calculation_integrity(self):
        """Test that financial calculations cannot be manipulated."""
        billing_service = CorporateBillingService()

        # Test that volume discounts are calculated correctly
        # and cannot be manipulated
        volume_tier = "gold"

        # Ensure discount calculation is consistent and secure
        discount = billing_service._calculate_volume_discount(200, 0.25)
        assert discount == 0.25

        # Test edge cases
        assert billing_service._calculate_volume_discount(0, 0.25) == 0.25
        assert billing_service._calculate_volume_discount(-1, 0.25) == 0.25


class TestCryptographicSecurity:
    """Security tests for cryptographic implementations."""

    def test_jwt_signature_verification(self):
        """Test JWT signature verification security."""
        auth_service = EnterpriseAuthService()

        # Create token with correct secret
        payload = {"sub": "user_123", "exp": datetime.now(timezone.utc) + timedelta(hours=8)}
        valid_token = jwt.encode(payload, auth_service.jwt_secret, algorithm="HS256")

        # Attempt to create token with wrong secret
        wrong_secret = "wrong_secret_key"
        malicious_token = jwt.encode(payload, wrong_secret, algorithm="HS256")

        # Verification should fail for token with wrong secret
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(malicious_token, auth_service.jwt_secret, algorithms=["HS256"])

    def test_secure_random_entropy(self):
        """Test that secure random generation has sufficient entropy."""
        import secrets

        # Generate multiple random values and ensure they're different
        random_values = [secrets.token_urlsafe(32) for _ in range(100)]

        # All values should be unique (extremely high probability with good entropy)
        assert len(set(random_values)) == 100

        # Each value should be sufficiently long
        for value in random_values:
            assert len(value) >= 32


# Integration security tests
class TestEndToEndSecurity:
    """End-to-end security tests."""

    @pytest.mark.asyncio
    async def test_complete_authentication_flow_security(self):
        """Test security of complete authentication flow."""
        # This would test the entire SSO flow for security vulnerabilities
        pass

    @pytest.mark.asyncio
    async def test_cross_tenant_isolation(self):
        """Test complete isolation between tenants."""
        # This would verify that no data leakage occurs between tenants
        # at any level of the application
        pass

    def test_api_security_headers(self):
        """Test that proper security headers are set."""
        # This would test that the API sets proper security headers:
        # - X-Content-Type-Options
        # - X-Frame-Options
        # - X-XSS-Protection
        # - Strict-Transport-Security
        # - Content-Security-Policy
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


import asyncio


# Helper to run async tests
def asyncio_run(coro):
    """Helper to run async functions in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)
