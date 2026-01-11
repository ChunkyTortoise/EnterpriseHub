"""
Comprehensive tests for Security Compliance Monitoring System

Tests cover:
- Security incident detection and response
- Compliance validation (CCPA/GDPR/Fair Housing)
- ML model bias detection
- API security monitoring
- PII exposure prevention
- GHL webhook security validation
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd

from ghl_real_estate_ai.services.security_compliance_monitor import (
    SecurityComplianceMonitor,
    SecurityIncident,
    ComplianceViolation,
    BiasDetectionResult,
    APIAbuseDetection,
    SecurityThreatLevel,
    ComplianceStandard,
    BiasType,
    get_security_monitor
)
from ghl_real_estate_ai.services.secure_logging_service import (
    SecureLogger,
    PIIDetectionResult
)
from ghl_real_estate_ai.api.middleware.security_monitoring import (
    SecurityMonitoringMiddleware,
    SecurityMetrics
)


class TestSecurityComplianceMonitor:
    """Test SecurityComplianceMonitor service."""

    @pytest.fixture
    async def security_monitor(self):
        """Create test security monitor instance."""
        monitor = SecurityComplianceMonitor(tenant_id="test_tenant")
        yield monitor
        await monitor.stop_monitoring()

    @pytest.fixture
    def sample_ml_predictions(self):
        """Sample ML predictions for bias testing."""
        return {
            "lead_scoring_model": [
                {"prediction": 0.8, "race": "white", "gender": "male", "protected_attribute": "majority"},
                {"prediction": 0.6, "race": "black", "gender": "female", "protected_attribute": "minority"},
                {"prediction": 0.7, "race": "hispanic", "gender": "male", "protected_attribute": "minority"},
                {"prediction": 0.9, "race": "white", "gender": "female", "protected_attribute": "majority"},
                {"prediction": 0.5, "race": "black", "gender": "male", "protected_attribute": "minority"},
            ]
        }

    @pytest.mark.asyncio
    async def test_security_monitor_initialization(self, security_monitor):
        """Test security monitor initializes correctly."""
        assert security_monitor.tenant_id == "test_tenant"
        assert security_monitor.is_monitoring is False
        assert len(security_monitor.active_incidents) == 0
        assert len(security_monitor.compliance_violations) == 0

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, security_monitor):
        """Test starting and stopping security monitoring."""
        # Start monitoring
        await security_monitor.start_monitoring()
        assert security_monitor.is_monitoring is True
        assert security_monitor.monitoring_task is not None

        # Stop monitoring
        await security_monitor.stop_monitoring()
        assert security_monitor.is_monitoring is False

    @pytest.mark.asyncio
    async def test_create_security_incident(self, security_monitor):
        """Test security incident creation."""
        incident = await security_monitor._create_security_incident(
            incident_type="test_incident",
            description="Test security incident",
            threat_level=SecurityThreatLevel.HIGH,
            source_ip="192.168.1.100",
            user_id="test_user",
            affected_data_types=["test_data"],
            mitigation_actions=["test_action"]
        )

        assert incident.incident_type == "test_incident"
        assert incident.threat_level == SecurityThreatLevel.HIGH
        assert incident.source_ip == "192.168.1.100"
        assert incident.user_id == "test_user"
        assert "test_data" in incident.affected_data_types
        assert "test_action" in incident.mitigation_actions
        assert not incident.resolved

        # Check incident is tracked
        assert incident.incident_id in security_monitor.active_incidents

    @pytest.mark.asyncio
    async def test_pii_exposure_detection(self, security_monitor):
        """Test PII exposure detection."""
        test_text = "Customer John Doe (john.doe@example.com, 555-123-4567) at 123 Main Street"

        result = await security_monitor.check_pii_exposure(
            text=test_text,
            context={"component": "test_api"}
        )

        assert isinstance(result, PIIDetectionResult)
        assert result.redaction_count > 0
        assert "email" in result.pii_types_found
        assert "phone" in result.pii_types_found

    @pytest.mark.asyncio
    async def test_ml_bias_detection(self, security_monitor, sample_ml_predictions):
        """Test ML model bias detection."""
        # Mock the prediction data retrieval
        with patch.object(security_monitor, '_get_recent_ml_predictions', return_value=sample_ml_predictions):
            # Run bias detection
            await security_monitor._detect_ml_bias()

            # Check if bias violations were created
            bias_violations = [
                v for v in security_monitor.compliance_violations.values()
                if v.violation_type == "algorithmic_bias"
            ]

            # Should detect bias in the sample data
            assert len(bias_violations) > 0

            for violation in bias_violations:
                assert violation.standard == ComplianceStandard.FAIR_HOUSING
                assert "bias" in violation.description.lower()

    def test_demographic_parity_check(self, security_monitor):
        """Test demographic parity bias calculation."""
        # Create test DataFrame
        data = {
            "protected_attribute": ["majority", "majority", "minority", "minority", "majority"],
            "prediction": [0.9, 0.8, 0.5, 0.6, 0.85]
        }
        df = pd.DataFrame(data)

        result = security_monitor._check_demographic_parity("test_model", df)

        assert isinstance(result, BiasDetectionResult)
        assert result.model_name == "test_model"
        assert result.bias_type == BiasType.DEMOGRAPHIC_PARITY
        assert result.bias_score > 0  # Should detect bias in this unbalanced data

    def test_disparate_impact_check(self, security_monitor):
        """Test disparate impact bias calculation."""
        # Create test DataFrame with racial bias
        data = {
            "race": ["white", "white", "black", "black", "white"],
            "prediction": [1, 1, 0, 0, 1]  # Clear bias against black applicants
        }
        df = pd.DataFrame(data)

        result = security_monitor._check_disparate_impact("test_model", df)

        assert isinstance(result, BiasDetectionResult)
        assert result.model_name == "test_model"
        assert result.bias_type == BiasType.DISPARATE_IMPACT
        assert result.is_biased is True  # Should detect significant bias

    @pytest.mark.asyncio
    async def test_ghl_webhook_validation(self, security_monitor):
        """Test GHL webhook signature validation."""
        # Mock the signature calculation
        with patch.object(security_monitor, '_calculate_ghl_signature') as mock_calc:
            mock_calc.return_value = "valid_signature"

            # Test valid signature
            result = await security_monitor.validate_ghl_webhook(
                payload="test_payload",
                signature="valid_signature",
                source_ip="192.168.1.1"
            )
            assert result is True

            # Test invalid signature
            result = await security_monitor.validate_ghl_webhook(
                payload="test_payload",
                signature="invalid_signature",
                source_ip="192.168.1.1"
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_compliance_violation_creation(self, security_monitor):
        """Test compliance violation tracking."""
        # Create a bias result that should trigger violation
        bias_result = BiasDetectionResult(
            model_name="test_model",
            bias_type=BiasType.DEMOGRAPHIC_PARITY,
            bias_score=0.15,  # Above threshold
            threshold=0.05,
            is_biased=True,
            protected_attributes=["race"],
            affected_groups=["minority_group"],
            recommendations=["retrain_model"],
            timestamp=datetime.now(timezone.utc)
        )

        await security_monitor._handle_ml_bias_detection(bias_result)

        # Check violation was created
        violations = [
            v for v in security_monitor.compliance_violations.values()
            if v.standard == ComplianceStandard.FAIR_HOUSING
        ]

        assert len(violations) == 1
        violation = violations[0]
        assert violation.violation_type == "algorithmic_bias"
        assert violation.severity == "HIGH"
        assert "retrain_model" in violation.remediation_actions

    @pytest.mark.asyncio
    async def test_incident_response_automation(self, security_monitor):
        """Test automated incident response."""
        # Create critical incident that should trigger automation
        incident = await security_monitor._create_security_incident(
            incident_type="brute_force_attack",
            description="Multiple login failures from same IP",
            threat_level=SecurityThreatLevel.CRITICAL,
            source_ip="192.168.1.100",
            affected_data_types=["authentication"],
            mitigation_actions=["ip_blocking"]
        )

        # Verify incident was created and is critical
        assert incident.threat_level == SecurityThreatLevel.CRITICAL
        assert incident.incident_type == "brute_force_attack"

        # Automated response should have been triggered (mocked in actual implementation)
        # In real implementation, this would add IP to Redis blocklist

    @pytest.mark.asyncio
    async def test_data_retention_compliance(self, security_monitor):
        """Test data retention compliance checking."""
        # Mock database connection for testing
        with patch('sqlalchemy.create_engine') as mock_engine:
            mock_conn = Mock()
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
            mock_conn.execute.return_value = []

            # Run data retention check
            await security_monitor._check_data_retention()

            # Verify database was queried for retention compliance
            mock_conn.execute.assert_called()

    @pytest.mark.asyncio
    async def test_license_compliance_monitoring(self, security_monitor):
        """Test real estate license compliance monitoring."""
        # Mock database with expired license
        with patch('sqlalchemy.create_engine') as mock_engine:
            mock_conn = Mock()
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

            # Mock expired license data
            expired_license = Mock()
            expired_license.agent_id = "agent_123"
            expired_license.license_number = "DRE12345678"
            expired_license.license_state = "CA"
            expired_license.expiration_date = datetime.now() - timedelta(days=30)

            mock_conn.execute.return_value = [expired_license]

            # Run license compliance check
            await security_monitor._check_license_compliance()

            # Verify compliance violation was created
            license_violations = [
                v for v in security_monitor.compliance_violations.values()
                if v.violation_type == "expired_license"
            ]

            assert len(license_violations) == 1
            violation = license_violations[0]
            assert violation.standard == ComplianceStandard.NAR_CODE
            assert "agent_123" in violation.description

    @pytest.mark.asyncio
    async def test_dashboard_data_retrieval(self, security_monitor):
        """Test security dashboard data generation."""
        # Create some test incidents and violations
        await security_monitor._create_security_incident(
            incident_type="test_incident_1",
            description="Test incident 1",
            threat_level=SecurityThreatLevel.CRITICAL,
        )

        await security_monitor._create_security_incident(
            incident_type="test_incident_2",
            description="Test incident 2",
            threat_level=SecurityThreatLevel.MEDIUM,
        )

        dashboard_data = await security_monitor.get_security_dashboard_data()

        assert dashboard_data["active_incidents"] == 2
        assert dashboard_data["critical_incidents"] == 1
        assert dashboard_data["compliance_violations"] == 0  # None created in this test
        assert dashboard_data["monitoring_status"] == "inactive"  # Not started
        assert "last_check" in dashboard_data


class TestSecurityMonitoringMiddleware:
    """Test SecurityMonitoringMiddleware."""

    @pytest.fixture
    def mock_app(self):
        """Mock ASGI application."""
        async def app(scope, receive, send):
            response = {
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"application/json"]],
            }
            await send(response)
            await send({"type": "http.response.body", "body": b'{"success": true}'})

        return app

    @pytest.fixture
    def security_middleware(self, mock_app):
        """Create security monitoring middleware."""
        return SecurityMonitoringMiddleware(mock_app, tenant_id="test_tenant")

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock()
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {"user-agent": "test-agent"}
        request.client.host = "192.168.1.1"
        return request

    def test_get_client_ip(self, security_middleware, mock_request):
        """Test client IP extraction."""
        # Test direct IP
        ip = security_middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"

        # Test X-Forwarded-For header
        mock_request.headers = {"x-forwarded-for": "10.0.0.1, 192.168.1.1"}
        ip = security_middleware._get_client_ip(mock_request)
        assert ip == "10.0.0.1"

        # Test X-Real-IP header
        mock_request.headers = {"x-real-ip": "10.0.0.2"}
        ip = security_middleware._get_client_ip(mock_request)
        assert ip == "10.0.0.2"

    def test_suspicious_pattern_detection(self, security_middleware):
        """Test suspicious URL pattern detection."""
        # Test XSS pattern
        assert security_middleware._contains_suspicious_patterns("/api/test?param=<script>") is True

        # Test SQL injection pattern
        assert security_middleware._contains_suspicious_patterns("/api/test?param=union select") is True

        # Test path traversal
        assert security_middleware._contains_suspicious_patterns("/api/../../../etc/passwd") is True

        # Test safe URL
        assert security_middleware._contains_suspicious_patterns("/api/leads?status=active") is False

    @pytest.mark.asyncio
    async def test_rate_limiting_check(self, security_middleware):
        """Test rate limiting functionality."""
        # Mock Redis client
        security_middleware.redis_client = AsyncMock()

        # Test first request (under limit)
        security_middleware.redis_client.get.return_value = "0"
        security_middleware.redis_client.pipeline.return_value.execute.return_value = [1, True]

        result = await security_middleware._check_rate_limiting("192.168.1.1", "/api/test")
        assert result["exceeded"] is False

        # Test request over limit
        security_middleware.redis_client.get.return_value = "150"  # Over default limit of 100

        result = await security_middleware._check_rate_limiting("192.168.1.1", "/api/test")
        assert result["exceeded"] is True

    @pytest.mark.asyncio
    async def test_authentication_failure_tracking(self, security_middleware, mock_request):
        """Test authentication failure tracking."""
        # Mock Redis client
        security_middleware.redis_client = AsyncMock()
        security_middleware.redis_client.incr.return_value = 5  # 5 failures

        # Mock request with auth failure
        mock_request.method = "POST"
        mock_request.body = AsyncMock(return_value=b'{"username": "testuser", "password": "wrong"}')

        await security_middleware._handle_authentication_failure(
            mock_request, "192.168.1.1", "/api/auth/login"
        )

        # Verify failure was recorded
        assert security_middleware.security_monitor.record_authentication_failure.called

    @pytest.mark.asyncio
    async def test_pii_response_monitoring(self, security_middleware):
        """Test PII exposure monitoring in API responses."""
        # Mock response with PII
        mock_response = Mock()
        mock_response.body = b'{"user": {"email": "test@example.com", "phone": "555-123-4567"}}'

        # Mock PII detection
        with patch.object(security_middleware.security_monitor, 'check_pii_exposure') as mock_check:
            pii_result = PIIDetectionResult(
                original_length=100,
                sanitized_length=80,
                pii_types_found=["email", "phone"],
                redaction_count=2,
                severity_level="HIGH",
                processing_time_ms=5.0
            )
            mock_check.return_value = pii_result

            await security_middleware._check_response_pii_exposure(mock_response, "/api/users")

            # Verify PII check was called
            mock_check.assert_called_once()

    def test_security_metrics_tracking(self, security_middleware):
        """Test security metrics collection."""
        # Initial metrics
        metrics = security_middleware.get_security_metrics()
        assert metrics["total_requests"] == 0
        assert metrics["failed_authentications"] == 0

        # Update metrics
        security_middleware.metrics.request_count = 100
        security_middleware.metrics.failed_auth_count = 5
        security_middleware.metrics.rate_limit_violations = 3

        metrics = security_middleware.get_security_metrics()
        assert metrics["total_requests"] == 100
        assert metrics["failed_authentications"] == 5
        assert metrics["rate_limit_violations"] == 3

    @pytest.mark.asyncio
    async def test_ghl_webhook_middleware_validation(self, security_middleware):
        """Test GHL webhook validation in middleware."""
        # Mock request with GHL webhook
        mock_request = Mock()
        mock_request.url.path = "/api/ghl/webhook"
        mock_request.headers = {"x-ghl-signature": "test_signature"}
        mock_request.body = AsyncMock(return_value=b'{"event": "contact.created"}')

        # Mock validation
        with patch.object(security_middleware.security_monitor, 'validate_ghl_webhook') as mock_validate:
            mock_validate.return_value = True

            result = await security_middleware._validate_ghl_webhook(mock_request)
            assert result is True

            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_ip_blocking_functionality(self, security_middleware):
        """Test IP blocking functionality."""
        # Mock Redis client
        security_middleware.redis_client = AsyncMock()

        # Test IP not blocked
        security_middleware.redis_client.sismember.return_value = False
        is_blocked = await security_middleware._is_ip_blocked("192.168.1.1")
        assert is_blocked is False

        # Test IP is blocked
        security_middleware.redis_client.sismember.return_value = True
        is_blocked = await security_middleware._is_ip_blocked("192.168.1.1")
        assert is_blocked is True

        # Test auto-blocking
        await security_middleware._auto_block_ip("192.168.1.100", "brute_force")
        security_middleware.redis_client.sadd.assert_called_with("security:blocked_ips", "192.168.1.100")

    def test_security_response_creation(self, security_middleware):
        """Test security violation response creation."""
        response = security_middleware._create_security_response(
            status_code=403,
            message="Access denied",
            incident_id="inc_123"
        )

        assert response.status_code == 403
        assert "Access denied" in str(response.body)
        assert "inc_123" in str(response.body)
        assert response.headers["X-Security-Response"] == "true"


class TestSecurityIntegration:
    """Integration tests for complete security system."""

    @pytest.mark.asyncio
    async def test_end_to_end_security_incident_flow(self):
        """Test complete security incident detection and response flow."""
        # Create security monitor
        monitor = SecurityComplianceMonitor(tenant_id="integration_test")

        try:
            # Simulate brute force attack detection
            for i in range(15):  # Simulate 15 failed login attempts
                monitor.record_authentication_failure(
                    user_id=f"user_{i % 3}",  # 3 different users
                    source_ip="192.168.1.100",
                    failure_reason="invalid_credentials",
                    endpoint="/api/auth/login"
                )

            # Start monitoring to trigger detection
            await monitor.start_monitoring()

            # Wait for monitoring loop to process
            await asyncio.sleep(0.1)

            # Check if incidents were created
            brute_force_incidents = [
                incident for incident in monitor.active_incidents.values()
                if incident.incident_type == "brute_force_attack"
            ]

            # Should have detected brute force attack
            assert len(brute_force_incidents) > 0

            incident = brute_force_incidents[0]
            assert incident.threat_level == SecurityThreatLevel.HIGH
            assert "192.168.1.100" in incident.description

        finally:
            await monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_compliance_monitoring_integration(self):
        """Test integration between security monitoring and compliance tracking."""
        monitor = SecurityComplianceMonitor(tenant_id="compliance_test")

        try:
            # Simulate ML bias detection that triggers compliance violation
            bias_result = BiasDetectionResult(
                model_name="property_matching_model",
                bias_type=BiasType.DEMOGRAPHIC_PARITY,
                bias_score=0.20,  # Significant bias
                threshold=0.05,
                is_biased=True,
                protected_attributes=["race", "gender"],
                affected_groups=["minority_applicants"],
                recommendations=["retrain_with_balanced_data", "apply_fairness_constraints"],
                timestamp=datetime.now(timezone.utc)
            )

            # Handle bias detection
            await monitor._handle_ml_bias_detection(bias_result)

            # Check compliance violation was created
            fair_housing_violations = [
                v for v in monitor.compliance_violations.values()
                if v.standard == ComplianceStandard.FAIR_HOUSING
            ]

            assert len(fair_housing_violations) == 1
            violation = fair_housing_violations[0]
            assert violation.violation_type == "algorithmic_bias"
            assert "retrain_with_balanced_data" in violation.remediation_actions

        finally:
            await monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_real_estate_specific_compliance(self):
        """Test real estate industry specific compliance features."""
        monitor = SecurityComplianceMonitor(tenant_id="real_estate_test")

        # Test license pattern recognition
        ca_license = "DRE12345678"
        assert monitor.license_patterns['CA'].match(ca_license[:8])  # Match first 8 digits

        # Test protected characteristics detection
        assert "race" in monitor.protected_characteristics
        assert "familial_status" in monitor.protected_characteristics

        # Test sensitive property field recognition
        assert "credit_score" in monitor.sensitive_property_fields
        assert "income_verification" in monitor.sensitive_property_fields


# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])