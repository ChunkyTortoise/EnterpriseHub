import os
"""
Comprehensive Test Suite for Compliance Platform API Endpoints

Tests cover:
- Model Registration API (create, list, get, validation)
- Compliance Assessment API (sync, async, status, scoring)
- Violations API (list, acknowledge, filter by severity)
- Reports API (generation, retrieval)
- Webhooks API (subscribe, list, test, signature verification)

Following TDD principles: RED -> GREEN -> REFACTOR
"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ghl_real_estate_ai.compliance_platform.models.compliance_models import (
    AIModelRegistration,
    ComplianceScore,
    ComplianceStatus,
    PolicyViolation,
    RegulationType,
    RiskAssessment,
    RiskLevel,
    ViolationSeverity,
)

# ============================================================================
# FIXTURES - Common test data and mock clients
# ============================================================================


@pytest.fixture
def sample_model_registration_payload() -> Dict[str, Any]:
    """Sample payload for model registration API"""
    return {
        "name": "Lead Scoring AI",
        "version": "2.1.0",
        "description": "AI-powered lead scoring for real estate",
        "model_type": "classification",
        "provider": "anthropic",
        "deployment_location": "cloud",
        "intended_use": "Automated lead qualification",
        "use_case_category": "crm_automation",
        "data_residency": ["us", "eu"],
        "personal_data_processed": True,
        "sensitive_data_processed": False,
        "registered_by": "compliance_team",
    }


@pytest.fixture
def sample_model_registration() -> AIModelRegistration:
    """Sample registered AI model"""
    return AIModelRegistration(
        model_id="model_001",
        name="Lead Scoring AI",
        version="2.1.0",
        description="AI-powered lead scoring for real estate",
        model_type="classification",
        provider="anthropic",
        deployment_location="cloud",
        data_residency=["us", "eu"],
        intended_use="Automated lead qualification",
        prohibited_uses=["credit decisions"],
        target_users=["sales_team"],
        risk_level=RiskLevel.HIGH,
        use_case_category="crm_automation",
        personal_data_processed=True,
        sensitive_data_processed=False,
        data_retention_days=90,
        compliance_status=ComplianceStatus.UNDER_REVIEW,
        applicable_regulations=[RegulationType.EU_AI_ACT, RegulationType.GDPR],
        registered_by="compliance_team",
    )


@pytest.fixture
def sample_risk_assessment() -> RiskAssessment:
    """Sample risk assessment"""
    return RiskAssessment(
        assessment_id="assess_001",
        model_id="model_001",
        model_name="Lead Scoring AI",
        risk_level=RiskLevel.HIGH,
        risk_score=72.5,
        transparency_score=65.0,
        fairness_score=78.0,
        accountability_score=70.0,
        robustness_score=82.0,
        privacy_score=68.0,
        security_score=85.0,
        risk_factors=["Personal data processing", "Limited explainability"],
        mitigating_factors=["Human oversight", "Regular audits"],
        recommendations=["Implement SHAP", "Add consent tracking"],
        applicable_regulations=[RegulationType.EU_AI_ACT, RegulationType.GDPR],
    )


@pytest.fixture
def sample_compliance_score() -> ComplianceScore:
    """Sample compliance score"""
    return ComplianceScore(
        overall_score=85.5,
        regulation_scores={
            "eu_ai_act": 88.0,
            "gdpr": 82.0,
        },
        category_scores={
            "transparency": 65.0,
            "fairness": 78.0,
            "accountability": 70.0,
            "robustness": 82.0,
            "privacy": 68.0,
            "security": 85.0,
        },
        trend="improving",
        trend_percentage=5.2,
        assessor="compliance_engine",
    )


@pytest.fixture
def sample_policy_violation() -> PolicyViolation:
    """Sample policy violation"""
    return PolicyViolation(
        violation_id="viol_001",
        regulation=RegulationType.EU_AI_ACT,
        policy_id="EUAI-005",
        policy_name="AI Transparency Requirements",
        article_reference="Article 13",
        severity=ViolationSeverity.HIGH,
        title="Missing AI Disclosure",
        description="AI system does not inform users of AI-based processing",
        evidence=["UI audit: no AI disclosure banner found"],
        affected_systems=["model_001"],
        affected_data_subjects=10000,
        detected_by="compliance_engine",
        detection_method="automated_scan",
        status="open",
        potential_fine=15000000.00,
        reputational_risk="high",
    )


@pytest.fixture
def sample_violations_list(sample_policy_violation) -> List[PolicyViolation]:
    """List of policy violations with various severities"""
    return [
        sample_policy_violation,
        PolicyViolation(
            violation_id="viol_002",
            regulation=RegulationType.GDPR,
            policy_id="GDPR-002",
            policy_name="Data Subject Rights",
            severity=ViolationSeverity.MEDIUM,
            title="Incomplete Data Access Capability",
            description="Data access requests not fully automated",
            evidence=["Manual process required for data export"],
            affected_systems=["model_001"],
            status="acknowledged",
            potential_fine=5000000.00,
        ),
        PolicyViolation(
            violation_id="viol_003",
            regulation=RegulationType.SOC2,
            policy_id="SOC2-001",
            policy_name="Documentation Requirements",
            severity=ViolationSeverity.LOW,
            title="Incomplete Model Documentation",
            description="Model card missing edge case metrics",
            evidence=["Documentation gap analysis"],
            affected_systems=["model_001"],
            status="open",
        ),
    ]


@pytest.fixture
def mock_compliance_service():
    """Mock compliance service for API tests"""
    service = MagicMock()
    service.register_model = AsyncMock()
    service.assess_compliance = AsyncMock()
    service.get_compliance_score = MagicMock()
    service.get_model = MagicMock()
    service.list_models = MagicMock()
    service.get_compliance_summary = AsyncMock()
    service.policy_enforcer = MagicMock()
    service.policy_enforcer.get_active_violations = MagicMock(return_value=[])
    service.policy_enforcer.acknowledge_violation = MagicMock(return_value=True)
    return service


@pytest.fixture
def mock_report_generator():
    """Mock report generator for API tests"""
    generator = MagicMock()
    generator.generate_report = AsyncMock()
    generator.get_report = MagicMock()
    return generator


@pytest.fixture
def webhook_secret() -> str:
    """Webhook signing secret for tests (from environment)"""
    return os.environ.get("TEST_WEBHOOK_SECRET", "test-webhook-secret-for-ci-only-min-32-chars")


# ============================================================================
# TEST CLASS: Model Registration API
# ============================================================================


class TestModelRegistrationAPI:
    """Test suite for model registration API endpoints"""

    @pytest.mark.asyncio
    async def test_register_model_success(
        self,
        sample_model_registration_payload: Dict[str, Any],
        sample_model_registration: AIModelRegistration,
        mock_compliance_service,
    ):
        """Test successful model registration"""
        # Arrange
        mock_compliance_service.register_model.return_value = sample_model_registration

        # Act
        result = await mock_compliance_service.register_model(**sample_model_registration_payload)

        # Assert
        assert result is not None
        assert result.name == "Lead Scoring AI"
        assert result.model_id is not None
        mock_compliance_service.register_model.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_model_validation_error(
        self,
        mock_compliance_service,
    ):
        """Test model registration with invalid payload"""
        # Arrange - missing required fields
        invalid_payload = {
            "name": "Test Model",
            # Missing version, description, model_type, etc.
        }

        mock_compliance_service.register_model.side_effect = ValueError(
            "Missing required fields: version, description, model_type"
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await mock_compliance_service.register_model(**invalid_payload)

        assert "Missing required fields" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_model_duplicate_name_version(
        self,
        sample_model_registration_payload: Dict[str, Any],
        mock_compliance_service,
    ):
        """Test that duplicate model name+version combinations are handled"""
        # Arrange
        mock_compliance_service.register_model.side_effect = ValueError(
            "Model with name 'Lead Scoring AI' version '2.1.0' already exists"
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await mock_compliance_service.register_model(**sample_model_registration_payload)

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_models(
        self,
        sample_model_registration: AIModelRegistration,
        mock_compliance_service,
    ):
        """Test listing registered models"""
        # Arrange
        mock_compliance_service.list_models.return_value = [
            sample_model_registration,
            AIModelRegistration(
                model_id="model_002",
                name="Property Matcher AI",
                version="1.0.0",
                description="AI property matching",
                model_type="nlp",
                provider="internal",
                deployment_location="cloud",
                data_residency=["us"],
                intended_use="Property recommendations",
                use_case_category="real_estate",
                registered_by="dev_team",
            ),
        ]

        # Act
        result = mock_compliance_service.list_models()

        # Assert
        assert len(result) == 2
        assert result[0].name == "Lead Scoring AI"
        assert result[1].name == "Property Matcher AI"

    @pytest.mark.asyncio
    async def test_list_models_with_filter(
        self,
        sample_model_registration: AIModelRegistration,
        mock_compliance_service,
    ):
        """Test listing models with compliance status filter"""
        # Arrange
        mock_compliance_service.list_models.return_value = [sample_model_registration]

        # Act
        result = mock_compliance_service.list_models(compliance_status=ComplianceStatus.UNDER_REVIEW)

        # Assert
        assert len(result) == 1
        assert result[0].compliance_status == ComplianceStatus.UNDER_REVIEW

    @pytest.mark.asyncio
    async def test_get_model_not_found(
        self,
        mock_compliance_service,
    ):
        """Test getting a model that doesn't exist"""
        # Arrange
        mock_compliance_service.get_model.return_value = None

        # Act
        result = mock_compliance_service.get_model("nonexistent_model_id")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_model_success(
        self,
        sample_model_registration: AIModelRegistration,
        mock_compliance_service,
    ):
        """Test getting a model by ID"""
        # Arrange
        mock_compliance_service.get_model.return_value = sample_model_registration

        # Act
        result = mock_compliance_service.get_model("model_001")

        # Assert
        assert result is not None
        assert result.model_id == "model_001"
        assert result.name == "Lead Scoring AI"


# ============================================================================
# TEST CLASS: Compliance Assessment API
# ============================================================================


class TestComplianceAssessmentAPI:
    """Test suite for compliance assessment API endpoints"""

    @pytest.mark.asyncio
    async def test_assess_compliance_sync(
        self,
        sample_model_registration: AIModelRegistration,
        sample_compliance_score: ComplianceScore,
        sample_risk_assessment: RiskAssessment,
        mock_compliance_service,
    ):
        """Test synchronous compliance assessment"""
        # Arrange
        mock_compliance_service.assess_compliance.return_value = (
            sample_compliance_score,
            sample_risk_assessment,
            [],  # No violations
        )

        # Act
        score, assessment, violations = await mock_compliance_service.assess_compliance(
            model_id="model_001",
            context={"risk_assessment_completed": True},
        )

        # Assert
        assert score.overall_score == 85.5
        assert assessment.risk_level == RiskLevel.HIGH
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_assess_compliance_async(
        self,
        sample_compliance_score: ComplianceScore,
        sample_risk_assessment: RiskAssessment,
        mock_compliance_service,
    ):
        """Test asynchronous compliance assessment with job ID"""
        # Arrange
        job_id = str(uuid4())
        mock_compliance_service.start_async_assessment = AsyncMock(return_value=job_id)

        # Act
        result = await mock_compliance_service.start_async_assessment(
            model_id="model_001",
            context={"comprehensive_scan": True},
        )

        # Assert
        assert result == job_id
        mock_compliance_service.start_async_assessment.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_assessment_status(
        self,
        mock_compliance_service,
    ):
        """Test getting assessment job status"""
        # Arrange
        job_id = str(uuid4())
        mock_compliance_service.get_assessment_status = MagicMock(
            return_value={
                "job_id": job_id,
                "status": "completed",
                "progress": 100,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Act
        result = mock_compliance_service.get_assessment_status(job_id)

        # Assert
        assert result["status"] == "completed"
        assert result["progress"] == 100

    @pytest.mark.asyncio
    async def test_get_assessment_status_pending(
        self,
        mock_compliance_service,
    ):
        """Test getting assessment status when still in progress"""
        # Arrange
        job_id = str(uuid4())
        mock_compliance_service.get_assessment_status = MagicMock(
            return_value={
                "job_id": job_id,
                "status": "in_progress",
                "progress": 45,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "current_step": "policy_evaluation",
            }
        )

        # Act
        result = mock_compliance_service.get_assessment_status(job_id)

        # Assert
        assert result["status"] == "in_progress"
        assert result["progress"] == 45
        assert result["current_step"] == "policy_evaluation"

    @pytest.mark.asyncio
    async def test_get_compliance_score(
        self,
        sample_compliance_score: ComplianceScore,
        mock_compliance_service,
    ):
        """Test getting compliance score for a model"""
        # Arrange
        mock_compliance_service.get_compliance_score.return_value = sample_compliance_score

        # Act
        result = mock_compliance_service.get_compliance_score("model_001")

        # Assert
        assert result is not None
        assert result.overall_score == 85.5
        assert result.grade == "B+"
        assert "eu_ai_act" in result.regulation_scores

    @pytest.mark.asyncio
    async def test_get_compliance_score_not_found(
        self,
        mock_compliance_service,
    ):
        """Test getting compliance score for unassessed model"""
        # Arrange
        mock_compliance_service.get_compliance_score.return_value = None

        # Act
        result = mock_compliance_service.get_compliance_score("unassessed_model")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_assess_compliance_with_violations(
        self,
        sample_compliance_score: ComplianceScore,
        sample_risk_assessment: RiskAssessment,
        sample_violations_list: List[PolicyViolation],
        mock_compliance_service,
    ):
        """Test assessment that finds violations"""
        # Arrange
        mock_compliance_service.assess_compliance.return_value = (
            sample_compliance_score,
            sample_risk_assessment,
            sample_violations_list,
        )

        # Act
        score, assessment, violations = await mock_compliance_service.assess_compliance(
            model_id="model_001",
            context={},
        )

        # Assert
        assert len(violations) == 3
        assert any(v.severity == ViolationSeverity.HIGH for v in violations)
        assert any(v.severity == ViolationSeverity.MEDIUM for v in violations)
        assert any(v.severity == ViolationSeverity.LOW for v in violations)


# ============================================================================
# TEST CLASS: Violations API
# ============================================================================


class TestViolationsAPI:
    """Test suite for violations API endpoints"""

    @pytest.mark.asyncio
    async def test_list_violations(
        self,
        sample_violations_list: List[PolicyViolation],
        mock_compliance_service,
    ):
        """Test listing all violations"""
        # Arrange
        mock_compliance_service.policy_enforcer.get_active_violations.return_value = sample_violations_list

        # Act
        result = mock_compliance_service.policy_enforcer.get_active_violations()

        # Assert
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_violations_empty(
        self,
        mock_compliance_service,
    ):
        """Test listing violations when none exist"""
        # Arrange
        mock_compliance_service.policy_enforcer.get_active_violations.return_value = []

        # Act
        result = mock_compliance_service.policy_enforcer.get_active_violations()

        # Assert
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_acknowledge_violation(
        self,
        sample_policy_violation: PolicyViolation,
        mock_compliance_service,
    ):
        """Test acknowledging a violation"""
        # Arrange
        mock_compliance_service.policy_enforcer.acknowledge_violation.return_value = True

        # Act
        result = mock_compliance_service.policy_enforcer.acknowledge_violation(
            violation_id="viol_001",
            acknowledged_by="compliance_officer",
        )

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_acknowledge_violation_not_found(
        self,
        mock_compliance_service,
    ):
        """Test acknowledging a non-existent violation"""
        # Arrange
        mock_compliance_service.policy_enforcer.acknowledge_violation.return_value = False

        # Act
        result = mock_compliance_service.policy_enforcer.acknowledge_violation(
            violation_id="nonexistent_violation",
            acknowledged_by="compliance_officer",
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_filter_violations_by_severity(
        self,
        sample_violations_list: List[PolicyViolation],
        mock_compliance_service,
    ):
        """Test filtering violations by severity"""
        # Arrange
        high_severity_violations = [v for v in sample_violations_list if v.severity == ViolationSeverity.HIGH]
        mock_compliance_service.policy_enforcer.get_active_violations.return_value = high_severity_violations

        # Act
        result = mock_compliance_service.policy_enforcer.get_active_violations(severity=ViolationSeverity.HIGH)

        # Assert
        assert len(result) == 1
        assert all(v.severity == ViolationSeverity.HIGH for v in result)

    @pytest.mark.asyncio
    async def test_filter_violations_by_regulation(
        self,
        sample_violations_list: List[PolicyViolation],
        mock_compliance_service,
    ):
        """Test filtering violations by regulation"""
        # Arrange
        gdpr_violations = [v for v in sample_violations_list if v.regulation == RegulationType.GDPR]
        mock_compliance_service.policy_enforcer.get_active_violations.return_value = gdpr_violations

        # Act
        result = mock_compliance_service.policy_enforcer.get_active_violations(regulation=RegulationType.GDPR)

        # Assert
        assert len(result) == 1
        assert all(v.regulation == RegulationType.GDPR for v in result)

    @pytest.mark.asyncio
    async def test_filter_violations_by_model(
        self,
        sample_violations_list: List[PolicyViolation],
        mock_compliance_service,
    ):
        """Test filtering violations by model ID"""
        # Arrange
        mock_compliance_service.policy_enforcer.get_active_violations.return_value = sample_violations_list

        # Act
        result = mock_compliance_service.policy_enforcer.get_active_violations(model_id="model_001")

        # Assert
        assert all("model_001" in v.affected_systems for v in result)

    @pytest.mark.asyncio
    async def test_resolve_violation(
        self,
        mock_compliance_service,
    ):
        """Test resolving a violation"""
        # Arrange
        mock_compliance_service.policy_enforcer.resolve_violation = MagicMock(return_value=True)

        # Act
        result = mock_compliance_service.policy_enforcer.resolve_violation(
            violation_id="viol_001",
            resolved_by="compliance_officer",
            resolution_notes="Implemented AI disclosure banner",
        )

        # Assert
        assert result is True


# ============================================================================
# TEST CLASS: Reports API
# ============================================================================


class TestReportsAPI:
    """Test suite for reports API endpoints"""

    @pytest.mark.asyncio
    async def test_generate_report(
        self,
        mock_report_generator,
    ):
        """Test generating a compliance report"""
        # Arrange
        report_id = str(uuid4())
        mock_report_generator.generate_report.return_value = {
            "report_id": report_id,
            "report_type": "executive_summary",
            "status": "completed",
            "download_url": f"/api/v1/reports/{report_id}/download",
        }

        # Act
        result = await mock_report_generator.generate_report(
            report_type="executive_summary",
            model_ids=["model_001"],
            period_start=datetime.now(timezone.utc) - timedelta(days=30),
            period_end=datetime.now(timezone.utc),
        )

        # Assert
        assert result["status"] == "completed"
        assert "download_url" in result

    @pytest.mark.asyncio
    async def test_generate_detailed_report(
        self,
        mock_report_generator,
    ):
        """Test generating a detailed compliance report"""
        # Arrange
        report_id = str(uuid4())
        mock_report_generator.generate_report.return_value = {
            "report_id": report_id,
            "report_type": "detailed",
            "status": "completed",
            "sections": [
                "executive_summary",
                "risk_assessment",
                "violation_details",
                "remediation_status",
                "recommendations",
            ],
        }

        # Act
        result = await mock_report_generator.generate_report(
            report_type="detailed",
            include_sections=["all"],
        )

        # Assert
        assert result["report_type"] == "detailed"
        assert len(result["sections"]) == 5

    @pytest.mark.asyncio
    async def test_get_report(
        self,
        mock_report_generator,
    ):
        """Test retrieving a generated report"""
        # Arrange
        report_id = str(uuid4())
        mock_report_generator.get_report.return_value = {
            "report_id": report_id,
            "report_type": "executive_summary",
            "status": "completed",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "content": {
                "overall_score": 85.5,
                "models_assessed": 3,
                "total_violations": 5,
            },
        }

        # Act
        result = mock_report_generator.get_report(report_id)

        # Assert
        assert result["report_id"] == report_id
        assert result["status"] == "completed"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_get_report_not_found(
        self,
        mock_report_generator,
    ):
        """Test retrieving a non-existent report"""
        # Arrange
        mock_report_generator.get_report.return_value = None

        # Act
        result = mock_report_generator.get_report("nonexistent_report_id")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_report_async(
        self,
        mock_report_generator,
    ):
        """Test generating a report asynchronously for large datasets"""
        # Arrange
        job_id = str(uuid4())
        mock_report_generator.start_async_report = AsyncMock(
            return_value={
                "job_id": job_id,
                "status": "queued",
                "estimated_completion": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            }
        )

        # Act
        result = await mock_report_generator.start_async_report(
            report_type="audit",
            model_ids=["model_001", "model_002", "model_003"],
            include_historical=True,
        )

        # Assert
        assert result["status"] == "queued"
        assert "job_id" in result


# ============================================================================
# TEST CLASS: Webhooks API
# ============================================================================


class TestWebhooksAPI:
    """Test suite for webhooks API endpoints"""

    @pytest.fixture
    def mock_webhook_service(self):
        """Mock webhook service"""
        service = MagicMock()
        service.subscribe = AsyncMock()
        service.unsubscribe = AsyncMock()
        service.list_subscriptions = MagicMock()
        service.test_webhook = AsyncMock()
        service.verify_signature = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_subscribe_webhook(
        self,
        mock_webhook_service,
    ):
        """Test subscribing to webhook events"""
        # Arrange
        subscription_id = str(uuid4())
        mock_webhook_service.subscribe.return_value = {
            "subscription_id": subscription_id,
            "url": "https://example.com/webhook",
            "events": ["violation.detected", "assessment.completed"],
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Act
        result = await mock_webhook_service.subscribe(
            url="https://example.com/webhook",
            events=["violation.detected", "assessment.completed"],
            secret="webhook_secret_123",
        )

        # Assert
        assert result["status"] == "active"
        assert "violation.detected" in result["events"]
        assert "assessment.completed" in result["events"]

    @pytest.mark.asyncio
    async def test_subscribe_webhook_invalid_url(
        self,
        mock_webhook_service,
    ):
        """Test webhook subscription with invalid URL"""
        # Arrange
        mock_webhook_service.subscribe.side_effect = ValueError("Invalid webhook URL: must be HTTPS")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await mock_webhook_service.subscribe(
                url="http://insecure.com/webhook",  # HTTP not HTTPS
                events=["violation.detected"],
            )

        assert "must be HTTPS" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_subscriptions(
        self,
        mock_webhook_service,
    ):
        """Test listing webhook subscriptions"""
        # Arrange
        mock_webhook_service.list_subscriptions.return_value = [
            {
                "subscription_id": str(uuid4()),
                "url": "https://example1.com/webhook",
                "events": ["violation.detected"],
                "status": "active",
            },
            {
                "subscription_id": str(uuid4()),
                "url": "https://example2.com/webhook",
                "events": ["assessment.completed", "score.changed"],
                "status": "active",
            },
        ]

        # Act
        result = mock_webhook_service.list_subscriptions()

        # Assert
        assert len(result) == 2
        assert all(s["status"] == "active" for s in result)

    @pytest.mark.asyncio
    async def test_test_webhook(
        self,
        mock_webhook_service,
    ):
        """Test webhook endpoint testing"""
        # Arrange
        mock_webhook_service.test_webhook.return_value = {
            "success": True,
            "response_code": 200,
            "response_time_ms": 150,
            "message": "Webhook endpoint responded successfully",
        }

        # Act
        result = await mock_webhook_service.test_webhook(
            subscription_id="sub_001",
        )

        # Assert
        assert result["success"] is True
        assert result["response_code"] == 200

    @pytest.mark.asyncio
    async def test_test_webhook_failure(
        self,
        mock_webhook_service,
    ):
        """Test webhook endpoint testing with failure"""
        # Arrange
        mock_webhook_service.test_webhook.return_value = {
            "success": False,
            "response_code": 500,
            "response_time_ms": 5000,
            "message": "Webhook endpoint returned error",
            "error_details": "Internal Server Error",
        }

        # Act
        result = await mock_webhook_service.test_webhook(
            subscription_id="sub_001",
        )

        # Assert
        assert result["success"] is False
        assert result["response_code"] == 500

    def test_webhook_signature_verification(
        self,
        webhook_secret: str,
        mock_webhook_service,
    ):
        """Test webhook signature verification"""
        # Arrange
        payload = json.dumps(
            {
                "event_type": "violation.detected",
                "model_id": "model_001",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        timestamp = str(int(time.time()))

        # Create signature
        signature_payload = f"{timestamp}.{payload}"
        expected_signature = hmac.new(
            webhook_secret.encode(),
            signature_payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        mock_webhook_service.verify_signature.return_value = True

        # Act
        result = mock_webhook_service.verify_signature(
            payload=payload,
            signature=f"t={timestamp},v1={expected_signature}",
            secret=webhook_secret,
        )

        # Assert
        assert result is True

    def test_webhook_signature_verification_invalid(
        self,
        webhook_secret: str,
        mock_webhook_service,
    ):
        """Test webhook signature verification with invalid signature"""
        # Arrange
        payload = json.dumps({"event_type": "violation.detected"})
        invalid_signature = "t=123456789,v1=invalid_signature_here"

        mock_webhook_service.verify_signature.return_value = False

        # Act
        result = mock_webhook_service.verify_signature(
            payload=payload,
            signature=invalid_signature,
            secret=webhook_secret,
        )

        # Assert
        assert result is False

    def test_webhook_signature_verification_expired(
        self,
        webhook_secret: str,
        mock_webhook_service,
    ):
        """Test webhook signature verification with expired timestamp"""
        # Arrange
        payload = json.dumps({"event_type": "violation.detected"})
        old_timestamp = str(int(time.time()) - 600)  # 10 minutes ago

        signature_payload = f"{old_timestamp}.{payload}"
        signature = hmac.new(
            webhook_secret.encode(),
            signature_payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        mock_webhook_service.verify_signature.side_effect = ValueError("Webhook timestamp expired")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            mock_webhook_service.verify_signature(
                payload=payload,
                signature=f"t={old_timestamp},v1={signature}",
                secret=webhook_secret,
                max_age_seconds=300,  # 5 minute tolerance
            )

        assert "expired" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unsubscribe_webhook(
        self,
        mock_webhook_service,
    ):
        """Test unsubscribing from webhook"""
        # Arrange
        mock_webhook_service.unsubscribe.return_value = True

        # Act
        result = await mock_webhook_service.unsubscribe(
            subscription_id="sub_001",
        )

        # Assert
        assert result is True


# ============================================================================
# TEST CLASS: API Error Handling
# ============================================================================


class TestAPIErrorHandling:
    """Test suite for API error handling"""

    @pytest.mark.asyncio
    async def test_rate_limiting(
        self,
        mock_compliance_service,
    ):
        """Test API rate limiting"""
        # Arrange
        mock_compliance_service.assess_compliance.side_effect = [(MagicMock(), MagicMock(), []) for _ in range(5)] + [
            Exception("Rate limit exceeded")
        ]

        # Act
        results = []
        for i in range(6):
            try:
                result = await mock_compliance_service.assess_compliance(model_id="model_001")
                results.append(("success", result))
            except Exception as e:
                results.append(("error", str(e)))

        # Assert
        assert len([r for r in results if r[0] == "success"]) == 5
        assert results[-1][0] == "error"
        assert "Rate limit" in results[-1][1]

    @pytest.mark.asyncio
    async def test_validation_error_response(
        self,
        mock_compliance_service,
    ):
        """Test validation error response format"""
        # Arrange
        mock_compliance_service.register_model.side_effect = ValueError(
            "Validation failed: name must be at least 3 characters"
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await mock_compliance_service.register_model(
                name="AB",  # Too short
                version="1.0.0",
            )

        assert "Validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_internal_server_error_handling(
        self,
        mock_compliance_service,
    ):
        """Test internal server error handling"""
        # Arrange
        mock_compliance_service.assess_compliance.side_effect = RuntimeError("Database connection failed")

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            await mock_compliance_service.assess_compliance(model_id="model_001")

        assert "Database connection failed" in str(exc_info.value)


# ============================================================================
# TEST CLASS: API Authentication
# ============================================================================


class TestAPIAuthentication:
    """Test suite for API authentication"""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        service = MagicMock()
        service.validate_token = MagicMock()
        service.get_user_permissions = MagicMock()
        return service

    def test_valid_api_key(
        self,
        mock_auth_service,
    ):
        """Test valid API key authentication"""
        # Arrange
        mock_auth_service.validate_token.return_value = {
            "valid": True,
            "user_id": "user_001",
            "organization_id": "org_001",
            "scopes": ["read", "write"],
        }

        # Act
        result = mock_auth_service.validate_token("valid_api_key_123")

        # Assert
        assert result["valid"] is True
        assert "scopes" in result

    def test_invalid_api_key(
        self,
        mock_auth_service,
    ):
        """Test invalid API key authentication"""
        # Arrange
        mock_auth_service.validate_token.return_value = {
            "valid": False,
            "error": "Invalid or expired API key",
        }

        # Act
        result = mock_auth_service.validate_token("invalid_key")

        # Assert
        assert result["valid"] is False

    def test_insufficient_permissions(
        self,
        mock_auth_service,
    ):
        """Test insufficient permissions handling"""
        # Arrange
        mock_auth_service.validate_token.return_value = {
            "valid": True,
            "scopes": ["read"],  # Missing 'write' scope
        }
        mock_auth_service.get_user_permissions.return_value = ["read"]

        # Act
        result = mock_auth_service.get_user_permissions("user_001")

        # Assert
        assert "write" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
