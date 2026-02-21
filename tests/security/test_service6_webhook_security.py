import pytest

pytestmark = pytest.mark.integration

#!/usr/bin/env python3
"""
Service 6 Webhook Security Validation Tests
==========================================

Comprehensive security testing for Service 6's webhook endpoints:

Critical Security Scenarios:
1. Webhook signature validation (GHL, Twilio, SendGrid, Apollo)
2. Replay attack prevention with timestamp validation
3. Rate limiting and DDoS protection
4. Input validation and injection prevention
5. Authentication and authorization checks
6. Data encryption and PII protection

Attack Vectors Tested:
- Invalid/malicious signatures
- Replay attacks with old timestamps
- Rate limiting bypass attempts
- SQL injection in webhook payloads
- XSS attempts in form data
- Oversized payloads (DoS attempts)
- Malformed JSON/data corruption

Compliance Requirements:
- OWASP webhook security guidelines
- PCI DSS data protection standards
- GDPR privacy requirements
- SOX audit trail requirements
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import security components
try:
    # Import webhook processing
    from ghl_real_estate_ai.api.routes.webhooks import (
        process_apollo_webhook,
        process_ghl_webhook,
        process_sendgrid_webhook,
        process_twilio_webhook,
    )

    from ghl_real_estate_ai.services.security_framework import InputValidator, RateLimiter, WebhookSignatureValidator

    # Import test utilities
    from tests.mocks.external_services import MockSignatureValidator, MockWebhookPayloads
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestWebhookSignatureValidation:
    """Test webhook signature validation for all providers"""

    @pytest.fixture
    def signature_validator(self):
        """Create signature validator with test secrets"""
        validator = WebhookSignatureValidator()

        # Mock secrets (in production these would be from secure storage)
        validator.ghl_secret = "test_ghl_secret_key_12345"
        validator.twilio_auth_token = "test_twilio_auth_token_67890"
        validator.sendgrid_webhook_secret = "test_sendgrid_secret_abcdef"
        validator.apollo_secret = "test_apollo_secret_ghijkl"

        return validator

    def test_ghl_webhook_valid_signature(self, signature_validator):
        """Test GHL webhook with valid signature"""
        # Arrange
        payload = json.dumps(MockWebhookPayloads.ghl_lead_webhook())
        timestamp = str(int(time.time()))

        # Create valid signature
        signature_string = timestamp + payload
        expected_signature = hmac.new(
            signature_validator.ghl_secret.encode(), signature_string.encode(), hashlib.sha256
        ).hexdigest()

        # Act
        is_valid = signature_validator.validate_ghl_signature(payload, expected_signature, timestamp)

        # Assert
        assert is_valid is True

    def test_ghl_webhook_invalid_signature(self, signature_validator):
        """Test GHL webhook with invalid signature"""
        # Arrange
        payload = json.dumps(MockWebhookPayloads.ghl_lead_webhook())
        timestamp = str(int(time.time()))
        invalid_signature = "invalid_signature_hash"

        # Act
        is_valid = signature_validator.validate_ghl_signature(payload, invalid_signature, timestamp)

        # Assert
        assert is_valid is False

    def test_ghl_webhook_tampered_payload(self, signature_validator):
        """Test GHL webhook with tampered payload"""
        # Arrange
        original_payload = MockWebhookPayloads.ghl_lead_webhook()
        original_json = json.dumps(original_payload)
        timestamp = str(int(time.time()))

        # Create signature for original payload
        signature_string = timestamp + original_json
        valid_signature = hmac.new(
            signature_validator.ghl_secret.encode(), signature_string.encode(), hashlib.sha256
        ).hexdigest()

        # Tamper with payload
        tampered_payload = original_payload.copy()
        tampered_payload["data"]["email"] = "hacker@malicious.com"
        tampered_json = json.dumps(tampered_payload)

        # Act - Use original signature with tampered payload
        is_valid = signature_validator.validate_ghl_signature(tampered_json, valid_signature, timestamp)

        # Assert
        assert is_valid is False

    def test_twilio_webhook_signature_validation(self, signature_validator):
        """Test Twilio webhook signature validation"""
        # Arrange
        url = "https://enterprisehub.ai/webhooks/twilio"
        params = MockWebhookPayloads.twilio_voice_webhook()

        # Create Twilio-style signature
        sorted_params = "".join([f"{k}{v}" for k, v in sorted(params.items())])
        signature_string = url + sorted_params

        expected_signature = base64.b64encode(
            hmac.new(signature_validator.twilio_auth_token.encode(), signature_string.encode(), hashlib.sha1).digest()
        ).decode()

        # Act
        is_valid = signature_validator.validate_twilio_signature(params, expected_signature, url)

        # Assert
        assert is_valid is True

    def test_sendgrid_webhook_signature_validation(self, signature_validator):
        """Test SendGrid webhook signature validation"""
        # Arrange
        payload = json.dumps(MockWebhookPayloads.sendgrid_event_webhook())
        timestamp = str(int(time.time()))

        # Create SendGrid-style signature
        signature_payload = timestamp + payload
        expected_signature = base64.b64encode(
            hmac.new(
                signature_validator.sendgrid_webhook_secret.encode(), signature_payload.encode(), hashlib.sha256
            ).digest()
        ).decode()

        # Act
        is_valid = signature_validator.validate_sendgrid_signature(payload, expected_signature, timestamp)

        # Assert
        assert is_valid is True


class TestReplayAttackPrevention:
    """Test replay attack prevention mechanisms"""

    @pytest.fixture
    def replay_validator(self):
        """Create replay attack validator"""
        validator = WebhookSignatureValidator()
        validator.replay_window_seconds = 300  # 5 minute window
        validator.processed_webhooks = set()  # Track processed webhooks
        return validator

    def test_reject_old_timestamp(self, replay_validator):
        """Test rejection of webhooks with old timestamps"""
        # Arrange - Create webhook with old timestamp (10 minutes ago)
        old_timestamp = str(int(time.time()) - 600)
        payload = json.dumps(MockWebhookPayloads.ghl_lead_webhook())

        # Act
        is_valid_time = replay_validator.validate_timestamp(old_timestamp, max_age_seconds=300)

        # Assert
        assert is_valid_time is False

    def test_reject_future_timestamp(self, replay_validator):
        """Test rejection of webhooks with future timestamps"""
        # Arrange - Create webhook with future timestamp (10 minutes from now)
        future_timestamp = str(int(time.time()) + 600)
        payload = json.dumps(MockWebhookPayloads.ghl_lead_webhook())

        # Act
        is_valid_time = replay_validator.validate_timestamp(future_timestamp, max_age_seconds=300)

        # Assert
        assert is_valid_time is False

    def test_prevent_duplicate_webhook_processing(self, replay_validator):
        """Test prevention of duplicate webhook processing"""
        # Arrange
        webhook_id = "unique_webhook_123"
        payload = json.dumps(MockWebhookPayloads.ghl_lead_webhook())

        # Act - Process webhook first time
        first_result = replay_validator.mark_webhook_processed(webhook_id)

        # Act - Attempt to process same webhook again
        second_result = replay_validator.is_webhook_processed(webhook_id)

        # Assert
        assert first_result is True  # First processing should succeed
        assert second_result is True  # Should be marked as already processed

    def test_webhook_nonce_validation(self, replay_validator):
        """Test webhook nonce validation for replay prevention"""
        # Arrange
        nonce1 = "nonce_12345_unique"
        nonce2 = "nonce_67890_different"
        nonce_duplicate = "nonce_12345_unique"  # Same as nonce1

        # Act
        result1 = replay_validator.validate_nonce(nonce1)
        result2 = replay_validator.validate_nonce(nonce2)
        result_duplicate = replay_validator.validate_nonce(nonce_duplicate)

        # Assert
        assert result1 is True  # First use of nonce1
        assert result2 is True  # First use of nonce2
        assert result_duplicate is False  # Duplicate nonce1


class TestRateLimitingAndDDoSProtection:
    """Test rate limiting and DDoS protection"""

    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter for testing"""
        limiter = RateLimiter()
        limiter.configure(
            {
                "requests_per_minute": 100,
                "requests_per_hour": 1000,
                "burst_allowance": 20,
                "ip_whitelist": ["127.0.0.1", "10.0.0.0/8"],
                "ip_blacklist": ["192.168.1.100"],
            }
        )
        return limiter

    @pytest.mark.asyncio
    async def test_rate_limiting_normal_traffic(self, rate_limiter):
        """Test rate limiting with normal traffic patterns"""
        client_ip = "203.0.113.1"  # Test IP

        # Simulate normal traffic (10 requests over 1 minute)
        allowed_count = 0

        for i in range(10):
            is_allowed = await rate_limiter.check_rate_limit(client_ip, endpoint="ghl_webhook")
            if is_allowed:
                allowed_count += 1

        # Assert - All normal requests should be allowed
        assert allowed_count == 10

    @pytest.mark.asyncio
    async def test_rate_limiting_burst_protection(self, rate_limiter):
        """Test rate limiting with burst traffic"""
        client_ip = "203.0.113.2"

        # Simulate burst traffic (50 requests rapidly)
        allowed_count = 0
        blocked_count = 0

        for i in range(50):
            is_allowed = await rate_limiter.check_rate_limit(client_ip, endpoint="ghl_webhook")
            if is_allowed:
                allowed_count += 1
            else:
                blocked_count += 1

        # Assert - Should allow burst allowance then start blocking
        assert allowed_count <= rate_limiter.burst_allowance + 5  # Some tolerance
        assert blocked_count > 0  # Should block some requests

    @pytest.mark.asyncio
    async def test_ip_whitelist_bypass(self, rate_limiter):
        """Test IP whitelist bypasses rate limiting"""
        whitelisted_ip = "127.0.0.1"  # From whitelist

        # Simulate high traffic from whitelisted IP
        allowed_count = 0

        for i in range(150):  # More than normal rate limit
            is_allowed = await rate_limiter.check_rate_limit(whitelisted_ip, endpoint="ghl_webhook")
            if is_allowed:
                allowed_count += 1

        # Assert - Whitelisted IP should bypass rate limits
        assert allowed_count == 150

    @pytest.mark.asyncio
    async def test_ip_blacklist_blocking(self, rate_limiter):
        """Test IP blacklist blocks all traffic"""
        blacklisted_ip = "192.168.1.100"  # From blacklist

        # Attempt request from blacklisted IP
        is_allowed = await rate_limiter.check_rate_limit(blacklisted_ip, endpoint="ghl_webhook")

        # Assert - Blacklisted IP should be blocked
        assert is_allowed is False

    @pytest.mark.asyncio
    async def test_ddos_pattern_detection(self, rate_limiter):
        """Test DDoS pattern detection and mitigation"""
        # Simulate distributed attack from multiple IPs
        attack_ips = [f"198.51.100.{i}" for i in range(1, 21)]  # 20 attacking IPs

        total_blocked = 0

        # Simulate coordinated attack
        for round_num in range(10):  # 10 rounds
            for ip in attack_ips:
                # Each IP tries 10 requests per round
                for request in range(10):
                    is_allowed = await rate_limiter.check_rate_limit(ip, "ghl_webhook")
                    if not is_allowed:
                        total_blocked += 1

        # Assert - Should detect and block DDoS pattern
        total_requests = 10 * 20 * 10  # rounds * IPs * requests_per_round
        block_ratio = total_blocked / total_requests

        assert block_ratio > 0.5, f"Should block >50% of DDoS traffic, blocked {block_ratio:.2%}"


class TestInputValidationAndSanitization:
    """Test input validation and injection prevention"""

    @pytest.fixture
    def input_validator(self):
        """Create input validator for testing"""
        validator = InputValidator()
        validator.configure_validation_rules(
            {
                "max_payload_size": 1024 * 1024,  # 1MB
                "max_string_length": 1000,
                "allowed_content_types": ["application/json"],
                "require_ssl": True,
                "validate_schemas": True,
            }
        )
        return validator

    def test_sql_injection_prevention(self, input_validator):
        """Test SQL injection prevention in webhook payloads"""
        # Arrange - Malicious payload with SQL injection
        malicious_payload = {
            "email": "'; DROP TABLE leads; SELECT * FROM users WHERE ''='",
            "first_name": "Robert'; DELETE FROM communications; --",
            "custom_field": "test' UNION SELECT password FROM admin_users --",
        }

        # Act
        is_safe, cleaned_payload = input_validator.sanitize_payload(malicious_payload)

        # Assert
        assert is_safe is True  # Should clean the payload
        assert "DROP TABLE" not in cleaned_payload["email"]
        assert "DELETE FROM" not in cleaned_payload["first_name"]
        assert "UNION SELECT" not in cleaned_payload["custom_field"]

    def test_xss_prevention(self, input_validator):
        """Test XSS prevention in webhook data"""
        # Arrange - Malicious payload with XSS
        xss_payload = {
            "first_name": "<script>alert('xss')</script>John",
            "last_name": "Smith<img src=x onerror=alert('xss')>",
            "notes": "<iframe src='javascript:alert(\"xss\")'></iframe>Interested buyer",
        }

        # Act
        is_safe, cleaned_payload = input_validator.sanitize_payload(xss_payload)

        # Assert
        assert is_safe is True
        assert "<script>" not in cleaned_payload["first_name"]
        assert "<img src=x" not in cleaned_payload["last_name"]
        assert "<iframe" not in cleaned_payload["notes"]
        assert "John" in cleaned_payload["first_name"]  # Legitimate content preserved

    def test_oversized_payload_rejection(self, input_validator):
        """Test rejection of oversized payloads"""
        # Arrange - Create oversized payload
        oversized_data = "x" * (2 * 1024 * 1024)  # 2MB (larger than 1MB limit)
        oversized_payload = {"email": "test@example.com", "malicious_field": oversized_data}

        # Act
        is_valid = input_validator.validate_payload_size(json.dumps(oversized_payload))

        # Assert
        assert is_valid is False  # Should reject oversized payload

    def test_malformed_json_handling(self, input_validator):
        """Test handling of malformed JSON"""
        # Arrange - Malformed JSON payloads
        malformed_payloads = [
            '{"email": "test@example.com",}',  # Trailing comma
            '{"email": "test@example.com" "name": "John"}',  # Missing comma
            '{"email": "test@example.com", "name":}',  # Incomplete value
            '{email: "test@example.com"}',  # Unquoted key
            '{"email": "test@example.com"',  # Missing closing brace
        ]

        # Act & Assert
        for malformed_json in malformed_payloads:
            is_valid = input_validator.validate_json_format(malformed_json)
            assert is_valid is False, f"Should reject malformed JSON: {malformed_json[:50]}"

    def test_content_type_validation(self, input_validator):
        """Test content type validation"""
        # Arrange - Test various content types
        valid_content_type = "application/json"
        invalid_content_types = ["text/html", "application/xml", "text/plain", "application/x-www-form-urlencoded"]

        # Act & Assert - Valid content type
        assert input_validator.validate_content_type(valid_content_type) is True

        # Act & Assert - Invalid content types
        for content_type in invalid_content_types:
            is_valid = input_validator.validate_content_type(content_type)
            assert is_valid is False, f"Should reject content type: {content_type}"


class TestDataEncryptionAndPIIProtection:
    """Test data encryption and PII protection"""

    @pytest.fixture
    def encryption_handler(self):
        """Create encryption handler for testing"""
        from ghl_real_estate_ai.services.security_framework import EncryptionHandler

        handler = EncryptionHandler()
        handler.configure(
            {
                "encryption_key": "test_encryption_key_32_chars_long!",
                "pii_fields": ["email", "phone", "ssn", "credit_card"],
                "encrypt_at_rest": True,
                "encrypt_in_transit": True,
            }
        )
        return handler

    def test_pii_field_encryption(self, encryption_handler):
        """Test PII field encryption"""
        # Arrange
        sensitive_data = {
            "lead_id": "LEAD_001",  # Not PII
            "email": "sensitive@example.com",  # PII
            "phone": "+15551234567",  # PII
            "first_name": "John",  # Not PII in this config
            "ssn": "123-45-6789",  # PII
        }

        # Act
        encrypted_data = encryption_handler.encrypt_pii_fields(sensitive_data)

        # Assert
        assert encrypted_data["lead_id"] == sensitive_data["lead_id"]  # Not encrypted
        assert encrypted_data["first_name"] == sensitive_data["first_name"]  # Not encrypted

        # PII fields should be encrypted
        assert encrypted_data["email"] != sensitive_data["email"]
        assert encrypted_data["phone"] != sensitive_data["phone"]
        assert encrypted_data["ssn"] != sensitive_data["ssn"]

        # Verify encryption is reversible
        decrypted_data = encryption_handler.decrypt_pii_fields(encrypted_data)
        assert decrypted_data["email"] == sensitive_data["email"]
        assert decrypted_data["phone"] == sensitive_data["phone"]

    def test_pii_masking_for_logs(self, encryption_handler):
        """Test PII masking for logging purposes"""
        # Arrange
        log_data = {
            "timestamp": "2026-01-17T10:30:00Z",
            "action": "webhook_received",
            "email": "user@example.com",
            "phone": "+15551234567",
            "ip_address": "203.0.113.1",
        }

        # Act
        masked_data = encryption_handler.mask_pii_for_logging(log_data)

        # Assert
        assert masked_data["timestamp"] == log_data["timestamp"]  # Not PII
        assert masked_data["action"] == log_data["action"]  # Not PII
        assert masked_data["ip_address"] == log_data["ip_address"]  # Not PII (in this test)

        # PII should be masked
        assert "*" in masked_data["email"]  # e.g., "us***@example.com"
        assert "*" in masked_data["phone"]  # e.g., "+155512****7"
        assert "user@example.com" not in str(masked_data)  # Original not present

    def test_gdpr_data_deletion(self, encryption_handler):
        """Test GDPR-compliant data deletion"""
        # Arrange
        lead_data = {
            "lead_id": "GDPR_DELETE_001",
            "email": "gdpr@example.com",
            "phone": "+15551234567",
            "marketing_consent": False,
            "data_retention_days": 30,
        }

        # Act - GDPR deletion request
        deletion_result = encryption_handler.gdpr_delete_data(lead_data["lead_id"], reason="user_requested_deletion")

        # Assert
        assert deletion_result["success"] is True
        assert deletion_result["deletion_timestamp"] is not None
        assert deletion_result["data_categories_deleted"] == ["personal_data", "communication_history"]
        assert deletion_result["retention_period_remaining"] == 0


class TestAuthenticationAndAuthorization:
    """Test authentication and authorization for webhook endpoints"""

    @pytest.fixture
    def auth_handler(self):
        """Create authentication handler"""
        from ghl_real_estate_ai.services.security_framework import AuthHandler

        handler = AuthHandler()
        handler.configure(
            {
                "require_api_key": True,
                "require_webhook_signature": True,
                "api_key_header": "X-API-Key",
                "rate_limit_by_api_key": True,
            }
        )
        return handler

    @pytest.mark.asyncio
    async def test_api_key_authentication(self, auth_handler):
        """Test API key authentication"""
        # Arrange
        valid_api_key = "enterprise_hub_api_key_12345"
        invalid_api_key = "invalid_key"

        # Mock request headers
        valid_headers = {"X-API-Key": valid_api_key}
        invalid_headers = {"X-API-Key": invalid_api_key}
        missing_headers = {}

        # Act & Assert - Valid API key
        is_valid = await auth_handler.validate_api_key(valid_headers)
        assert is_valid is True

        # Act & Assert - Invalid API key
        is_valid = await auth_handler.validate_api_key(invalid_headers)
        assert is_valid is False

        # Act & Assert - Missing API key
        is_valid = await auth_handler.validate_api_key(missing_headers)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_webhook_source_authorization(self, auth_handler):
        """Test webhook source authorization"""
        # Arrange - Known webhook sources
        authorized_sources = ["webhook.gohighlevel.com", "webhooks.twilio.com", "webhook.sendgrid.com", "api.apollo.io"]

        unauthorized_sources = ["malicious.com", "fake-webhook.com", "not-ghl.com"]

        # Act & Assert - Authorized sources
        for source in authorized_sources:
            is_authorized = auth_handler.validate_webhook_source(source)
            assert is_authorized is True, f"Should authorize {source}"

        # Act & Assert - Unauthorized sources
        for source in unauthorized_sources:
            is_authorized = auth_handler.validate_webhook_source(source)
            assert is_authorized is False, f"Should not authorize {source}"

    @pytest.mark.asyncio
    async def test_permission_based_access_control(self, auth_handler):
        """Test permission-based access control"""
        # Arrange - Different API key permissions
        permissions = {
            "read_only_key": ["read_leads", "read_analytics"],
            "webhook_key": ["write_leads", "create_communications"],
            "admin_key": ["read_leads", "write_leads", "delete_leads", "admin_access"],
        }

        # Act & Assert - Read-only key permissions
        can_read = auth_handler.check_permission("read_only_key", "read_leads")
        can_write = auth_handler.check_permission("read_only_key", "write_leads")
        assert can_read is True
        assert can_write is False

        # Act & Assert - Webhook key permissions
        can_write = auth_handler.check_permission("webhook_key", "write_leads")
        can_delete = auth_handler.check_permission("webhook_key", "delete_leads")
        assert can_write is True
        assert can_delete is False

        # Act & Assert - Admin key permissions
        can_admin = auth_handler.check_permission("admin_key", "admin_access")
        can_delete = auth_handler.check_permission("admin_key", "delete_leads")
        assert can_admin is True
        assert can_delete is True


class TestComplianceAndAuditTrail:
    """Test compliance requirements and audit trail"""

    @pytest.fixture
    def audit_logger(self):
        """Create audit logger for compliance testing"""
        from ghl_real_estate_ai.services.security_framework import AuditLogger

        logger = AuditLogger()
        logger.configure(
            {
                "log_all_webhook_events": True,
                "include_request_headers": True,
                "include_response_data": False,  # Privacy
                "retention_days": 2555,  # 7 years for SOX compliance
                "encrypt_audit_logs": True,
            }
        )
        return logger

    @pytest.mark.asyncio
    async def test_audit_trail_creation(self, audit_logger):
        """Test audit trail creation for webhook processing"""
        # Arrange
        webhook_event = {
            "source": "ghl",
            "event_type": "lead_created",
            "lead_id": "AUDIT_LEAD_001",
            "timestamp": datetime.now().isoformat(),
            "client_ip": "203.0.113.1",
            "user_agent": "GHL-Webhook/1.0",
        }

        # Act
        audit_entry = await audit_logger.log_webhook_event(
            event_type="webhook_processed", source="ghl", event_data=webhook_event, result="success"
        )

        # Assert
        assert audit_entry["event_id"] is not None
        assert audit_entry["timestamp"] is not None
        assert audit_entry["source"] == "ghl"
        assert audit_entry["result"] == "success"
        assert "client_ip" in audit_entry
        assert "user_agent" in audit_entry

    @pytest.mark.asyncio
    async def test_security_incident_logging(self, audit_logger):
        """Test security incident logging"""
        # Arrange
        security_incident = {
            "incident_type": "invalid_signature",
            "source_ip": "198.51.100.42",
            "attempted_payload": '{"malicious": "data"}',
            "timestamp": datetime.now().isoformat(),
            "severity": "medium",
        }

        # Act
        incident_log = await audit_logger.log_security_incident(
            incident_type=security_incident["incident_type"], details=security_incident, severity="medium"
        )

        # Assert
        assert incident_log["incident_id"] is not None
        assert incident_log["severity"] == "medium"
        assert incident_log["incident_type"] == "invalid_signature"
        assert incident_log["investigation_required"] is True

    def test_pci_dss_compliance_validation(self, audit_logger):
        """Test PCI DSS compliance for payment data"""
        # Arrange - Mock payment data in webhook
        payment_webhook = {
            "customer_id": "CUST_001",
            "payment_token": "tok_secure_12345",  # Tokenized, not raw card data
            "amount": 150000,  # $1,500 in cents
            "currency": "USD",
            "card_last_four": "4242",  # Only last 4 digits
        }

        # Act - Validate PCI compliance
        compliance_check = audit_logger.validate_pci_compliance(payment_webhook)

        # Assert
        assert compliance_check["compliant"] is True
        assert compliance_check["issues"] == []
        assert "card_number" not in payment_webhook  # Full card number not present
        assert "cvv" not in payment_webhook  # CVV not stored
        assert "payment_token" in payment_webhook  # Using tokenization

    def test_sox_audit_requirements(self, audit_logger):
        """Test SOX audit requirements for financial data"""
        # Arrange
        financial_transaction = {
            "transaction_id": "TXN_001",
            "lead_id": "LEAD_001",
            "commission_amount": 15000,  # $150 commission
            "transaction_date": "2026-01-17",
            "agent_id": "AGENT_001",
            "approval_chain": ["manager_001", "director_001"],
        }

        # Act
        sox_audit_entry = audit_logger.create_sox_audit_entry(
            transaction_type="commission_calculation",
            transaction_data=financial_transaction,
            approval_chain=financial_transaction["approval_chain"],
        )

        # Assert
        assert sox_audit_entry["audit_id"] is not None
        assert sox_audit_entry["transaction_id"] == "TXN_001"
        assert len(sox_audit_entry["approval_chain"]) == 2
        assert sox_audit_entry["financial_impact"] == 15000
        assert sox_audit_entry["retention_required_until"] is not None  # 7 years


# Test configuration and fixtures
pytest_plugins = ["pytest_asyncio"]


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=ghl_real_estate_ai.services.security_framework",
            "--cov=ghl_real_estate_ai.api.routes.webhooks",
            "--cov-report=html",
            "--cov-report=term-missing",
        ]
    )
