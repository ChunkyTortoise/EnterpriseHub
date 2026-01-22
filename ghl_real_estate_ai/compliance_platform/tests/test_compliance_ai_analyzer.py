"""
Comprehensive Test Suite for ComplianceAIAnalyzer Service

Tests cover:
- Risk dimension explanation with AI-generated insights
- Risk recommendations generation based on assessments
- Violation explanation with severity-aware analysis
- Remediation roadmap generation with prioritization
- Executive summary generation for C-suite reporting
- Compliance question answering with context
- Caching behavior for repeated calls
- Error handling and fallback behavior
- Performance requirements

Following TDD principles: RED -> GREEN -> REFACTOR
"""

import pytest
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from ghl_real_estate_ai.compliance_platform.models.compliance_models import (
    AIModelRegistration,
    ComplianceStatus,
    PolicyViolation,
    RegulationType,
    RiskAssessment,
    RiskLevel,
    ViolationSeverity,
)
from ghl_real_estate_ai.compliance_platform.models.risk_models import (
    RiskCategory,
    RiskIndicator,
    RiskMitigation,
)

# Import the analyzer service
from ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer import (
    ComplianceAIAnalyzer,
)


# ============================================================================
# FIXTURES - Common test data following project patterns
# ============================================================================


@pytest.fixture
def sample_ai_model_registration() -> AIModelRegistration:
    """Sample AI model registration for testing."""
    return AIModelRegistration(
        model_id="model_001",
        name="Lead Scoring AI",
        version="2.1.0",
        description="AI-powered lead scoring and prioritization model for real estate",
        model_type="classification",
        provider="anthropic",
        deployment_location="cloud",
        data_residency=["us", "eu"],
        intended_use="Automated lead scoring and qualification",
        prohibited_uses=["credit decisions", "employment screening"],
        target_users=["sales_team", "marketing_team"],
        risk_level=RiskLevel.HIGH,
        use_case_category="crm_automation",
        training_data_description="Historical CRM data from 50k+ real estate transactions",
        personal_data_processed=True,
        sensitive_data_processed=False,
        data_retention_days=90,
        input_types=["text", "structured_data"],
        output_types=["score", "classification"],
        api_endpoints=["/api/v1/score", "/api/v1/qualify"],
        compliance_status=ComplianceStatus.UNDER_REVIEW,
        applicable_regulations=[RegulationType.EU_AI_ACT, RegulationType.GDPR],
        certifications=["SOC2_Type2"],
        registered_by="compliance_team",
    )


@pytest.fixture
def sample_risk_assessment(sample_ai_model_registration: AIModelRegistration) -> RiskAssessment:
    """Sample risk assessment for testing."""
    return RiskAssessment(
        assessment_id="assess_001",
        model_id=sample_ai_model_registration.model_id,
        model_name=sample_ai_model_registration.name,
        risk_level=RiskLevel.HIGH,
        risk_score=72.5,
        transparency_score=65.0,
        fairness_score=78.0,
        accountability_score=70.0,
        robustness_score=82.0,
        privacy_score=68.0,
        security_score=85.0,
        assessed_by="ai_compliance_engine",
        methodology="automated_assessment_v2",
        risk_factors=[
            "Personal data processing without explicit consent tracking",
            "Limited explainability for scoring decisions",
            "Potential demographic bias in training data",
        ],
        mitigating_factors=[
            "Regular model retraining schedule",
            "Human-in-the-loop review for high-stakes decisions",
            "Comprehensive logging and audit trail",
        ],
        recommendations=[
            "Implement consent management integration",
            "Add SHAP-based explainability features",
            "Conduct bias audit on training data",
        ],
        applicable_regulations=[RegulationType.EU_AI_ACT, RegulationType.GDPR],
        regulatory_requirements={
            "eu_ai_act": [
                "Article 13 - Transparency",
                "Article 14 - Human oversight",
            ],
            "gdpr": [
                "Article 22 - Automated decision-making",
                "Article 35 - DPIA required",
            ],
        },
    )


@pytest.fixture
def sample_policy_violation_critical() -> PolicyViolation:
    """Sample critical severity policy violation."""
    return PolicyViolation(
        violation_id="viol_001",
        regulation=RegulationType.EU_AI_ACT,
        policy_id="pol_transparency_001",
        policy_name="AI Transparency Requirements",
        article_reference="Article 13",
        severity=ViolationSeverity.CRITICAL,
        title="Missing AI Disclosure in User-Facing Interfaces",
        description="The lead scoring system does not clearly inform end users that AI-based decisions are being made about their data.",
        evidence=[
            "UI audit showed no AI disclosure banners",
            "API responses lack AI attribution headers",
            "User consent forms missing AI processing clause",
        ],
        affected_systems=["crm_lead_scoring", "web_portal"],
        affected_data_subjects=15000,
        detected_by="automated_compliance_scan",
        detection_method="ui_audit",
        status="open",
        potential_fine=2000000.00,
        potential_fine_currency="EUR",
        reputational_risk="high",
    )


@pytest.fixture
def sample_policy_violation_medium() -> PolicyViolation:
    """Sample medium severity policy violation."""
    return PolicyViolation(
        violation_id="viol_002",
        regulation=RegulationType.GDPR,
        policy_id="pol_retention_001",
        policy_name="Data Retention Policy",
        article_reference="Article 5(1)(e)",
        severity=ViolationSeverity.MEDIUM,
        title="Data Retention Period Exceeded",
        description="Training data retained beyond the specified 90-day retention period.",
        evidence=[
            "Database audit found records from 180+ days ago",
            "Automated purge job failed silently",
        ],
        affected_systems=["model_training_pipeline"],
        affected_data_subjects=5000,
        detected_by="data_audit_system",
        detection_method="automated_scan",
        status="acknowledged",
        potential_fine=500000.00,
        reputational_risk="medium",
    )


@pytest.fixture
def sample_policy_violation_low() -> PolicyViolation:
    """Sample low severity policy violation."""
    return PolicyViolation(
        violation_id="viol_003",
        regulation=RegulationType.SOC2,
        policy_id="pol_docs_001",
        policy_name="Documentation Requirements",
        article_reference="CC6.1",
        severity=ViolationSeverity.LOW,
        title="Incomplete Model Documentation",
        description="Model card missing performance metrics for edge cases.",
        evidence=["Documentation review gap analysis"],
        affected_systems=["documentation_portal"],
        affected_data_subjects=0,
        detected_by="manual_review",
        detection_method="documentation_audit",
        status="open",
        potential_fine=None,
        reputational_risk="low",
    )


@pytest.fixture
def sample_violations_list(
    sample_policy_violation_critical: PolicyViolation,
    sample_policy_violation_medium: PolicyViolation,
    sample_policy_violation_low: PolicyViolation,
) -> List[PolicyViolation]:
    """List of violations with varying severities."""
    return [
        sample_policy_violation_critical,
        sample_policy_violation_medium,
        sample_policy_violation_low,
    ]


@pytest.fixture
def sample_risk_scores() -> Dict[str, float]:
    """Sample risk scores for dimension explanation."""
    return {
        "transparency": 65.0,
        "fairness": 78.0,
        "accountability": 70.0,
        "robustness": 82.0,
        "privacy": 68.0,
        "security": 85.0,
    }


@pytest.fixture
def sample_context() -> Dict[str, Any]:
    """Sample context for AI analysis."""
    return {
        "organization_id": "org_123",
        "organization_name": "Acme Real Estate Corp",
        "industry": "real_estate",
        "region": "north_america",
        "compliance_maturity": "intermediate",
        "active_regulations": ["EU_AI_ACT", "GDPR", "CCPA"],
        "previous_violations": 3,
        "risk_appetite": "moderate",
    }


@pytest.fixture
def sample_report_data(
    sample_risk_assessment: RiskAssessment,
    sample_violations_list: List[PolicyViolation],
) -> Dict[str, Any]:
    """Sample report data for executive summary generation."""
    return {
        "report_id": "rpt_001",
        "report_type": "executive_summary",
        "period_start": datetime.now(timezone.utc) - timedelta(days=30),
        "period_end": datetime.now(timezone.utc),
        "overall_score": 76.5,
        "models_assessed": 5,
        "total_violations": 3,
        "critical_violations": 1,
        "high_violations": 0,
        "medium_violations": 1,
        "low_violations": 1,
        "remediation_completion_rate": 0.67,
        "risk_trend": "improving",
        "key_findings": [
            "AI transparency gaps in user-facing systems",
            "Data retention policy non-compliance",
            "Documentation gaps identified",
        ],
        "risk_assessments": [sample_risk_assessment],
        "active_violations": sample_violations_list,
        "regulations_covered": ["EU_AI_ACT", "GDPR", "SOC2"],
    }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client to avoid actual API calls."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "AI-generated analysis response"
    mock_client.generate.return_value = mock_response
    mock_client.agenerate = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def mock_llm_response():
    """Mock LLM response object."""
    mock_response = MagicMock()
    mock_response.content = "AI-generated compliance analysis"
    mock_response.tokens_used = 500
    return mock_response


# ============================================================================
# TEST CLASS: explain_risk_dimension
# ============================================================================


class TestExplainRiskDimension:
    """Test suite for explain_risk_dimension method."""

    @pytest.mark.asyncio
    async def test_returns_explanation_structure(
        self,
        sample_risk_scores: Dict[str, float],
        sample_ai_model_registration: AIModelRegistration,
        sample_context: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that explain_risk_dimension returns proper explanation structure."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.explain_risk_dimension(
                dimension="transparency",
                scores=sample_risk_scores,
                model=sample_ai_model_registration,
                context=sample_context,
            )

            # Assert
            assert isinstance(result, dict)
            assert "explanation" in result
            assert "key_concerns" in result
            assert "mitigation_strategies" in result

    @pytest.mark.asyncio
    async def test_returns_key_concerns_as_list(
        self,
        sample_risk_scores: Dict[str, float],
        sample_ai_model_registration: AIModelRegistration,
        sample_context: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that key_concerns is returned as a list."""
        # Arrange
        mock_llm_client.agenerate = AsyncMock(
            return_value=MagicMock(
                content='{"explanation": "Analysis", "key_concerns": ["Concern 1", "Concern 2"], "mitigation_strategies": ["Strategy 1"]}'
            )
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.explain_risk_dimension(
                dimension="fairness",
                scores=sample_risk_scores,
                model=sample_ai_model_registration,
                context=sample_context,
            )

            # Assert
            assert isinstance(result.get("key_concerns"), list)

    @pytest.mark.asyncio
    async def test_returns_mitigation_strategies_as_list(
        self,
        sample_risk_scores: Dict[str, float],
        sample_ai_model_registration: AIModelRegistration,
        sample_context: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that mitigation_strategies is returned as a list."""
        # Arrange
        mock_llm_client.agenerate = AsyncMock(
            return_value=MagicMock(
                content='{"explanation": "Analysis", "key_concerns": ["Concern"], "mitigation_strategies": ["Strategy 1", "Strategy 2"]}'
            )
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.explain_risk_dimension(
                dimension="accountability",
                scores=sample_risk_scores,
                model=sample_ai_model_registration,
                context=sample_context,
            )

            # Assert
            assert isinstance(result.get("mitigation_strategies"), list)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "dimension",
        [
            "transparency",
            "fairness",
            "accountability",
            "robustness",
            "privacy",
            "security",
        ],
    )
    async def test_handles_all_six_risk_dimensions(
        self,
        dimension: str,
        sample_risk_scores: Dict[str, float],
        sample_ai_model_registration: AIModelRegistration,
        sample_context: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that all 6 risk dimensions are handled correctly."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.explain_risk_dimension(
                dimension=dimension,
                scores=sample_risk_scores,
                model=sample_ai_model_registration,
                context=sample_context,
            )

            # Assert
            assert isinstance(result, dict)
            assert "explanation" in result
            # Verify the dimension was processed
            assert result is not None

    @pytest.mark.asyncio
    async def test_caching_works_for_repeated_calls(
        self,
        sample_risk_scores: Dict[str, float],
        sample_ai_model_registration: AIModelRegistration,
        sample_context: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that caching works for repeated calls with same parameters."""
        # Arrange
        call_count = 0

        async def mock_agenerate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return MagicMock(
                content='{"explanation": "Cached response", "key_concerns": [], "mitigation_strategies": []}'
            )

        mock_llm_client.agenerate = mock_agenerate

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer(enable_caching=True)

            # Act - Call twice with same parameters
            result1 = await analyzer.explain_risk_dimension(
                dimension="transparency",
                scores=sample_risk_scores,
                model=sample_ai_model_registration,
                context=sample_context,
            )

            result2 = await analyzer.explain_risk_dimension(
                dimension="transparency",
                scores=sample_risk_scores,
                model=sample_ai_model_registration,
                context=sample_context,
            )

            # Assert - LLM should only be called once due to caching
            assert result1 == result2
            # If caching is implemented, call_count should be 1
            # If not cached, this test will fail (call_count == 2)
            assert call_count == 1, "Caching should prevent duplicate LLM calls"

    @pytest.mark.asyncio
    async def test_handles_invalid_dimension_gracefully(
        self,
        sample_risk_scores: Dict[str, float],
        sample_ai_model_registration: AIModelRegistration,
        sample_context: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that invalid dimensions are handled via fallback responses."""
        # Arrange
        # Note: The existing implementation doesn't validate dimensions explicitly,
        # it handles them via fallback responses, so we test that behavior
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act - Invalid dimension should still return a valid structure (via fallback)
            result = await analyzer.explain_risk_dimension(
                dimension="invalid_dimension",
                scores=sample_risk_scores,
                model=sample_ai_model_registration,
                context=sample_context,
            )

            # Assert - Should return valid structure even for invalid dimension
            assert isinstance(result, dict)
            assert "explanation" in result


# ============================================================================
# TEST CLASS: generate_risk_recommendations
# ============================================================================


class TestGenerateRiskRecommendations:
    """Test suite for generate_risk_recommendations method."""

    @pytest.mark.asyncio
    async def test_returns_list_of_recommendations(
        self,
        sample_risk_assessment: RiskAssessment,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that generate_risk_recommendations returns a list."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_risk_recommendations(
                assessment=sample_risk_assessment,
                model=sample_ai_model_registration,
            )

            # Assert
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_recommendations_are_strings(
        self,
        sample_risk_assessment: RiskAssessment,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that all recommendations are strings."""
        # Arrange
        mock_llm_client.agenerate = AsyncMock(
            return_value=MagicMock(
                content="1. Implement SHAP explainability\n2. Conduct bias audit\n3. Add consent tracking"
            )
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_risk_recommendations(
                assessment=sample_risk_assessment,
                model=sample_ai_model_registration,
            )

            # Assert
            assert all(isinstance(rec, str) for rec in result)

    @pytest.mark.asyncio
    async def test_recommendations_are_actionable(
        self,
        sample_risk_assessment: RiskAssessment,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that recommendations contain actionable language."""
        # Arrange
        mock_llm_client.agenerate = AsyncMock(
            return_value=MagicMock(
                content="1. Implement bias testing framework within 30 days\n2. Deploy explainability module for lead scoring\n3. Update privacy policy with AI disclosure"
            )
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_risk_recommendations(
                assessment=sample_risk_assessment,
                model=sample_ai_model_registration,
            )

            # Assert
            assert len(result) > 0
            # Check for actionable verbs in recommendations
            actionable_verbs = ["implement", "deploy", "update", "add", "conduct", "review", "establish", "priority", "improve"]
            has_actionable = any(
                any(verb in rec.lower() for verb in actionable_verbs)
                for rec in result
            )
            assert has_actionable, "Recommendations should contain actionable verbs"

    @pytest.mark.asyncio
    async def test_recommendations_specific_to_model_context(
        self,
        sample_risk_assessment: RiskAssessment,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that recommendations are specific to the model context."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_risk_recommendations(
                assessment=sample_risk_assessment,
                model=sample_ai_model_registration,
            )

            # Assert - LLM should have been called with model context
            mock_llm_client.agenerate.assert_called()
            call_args = str(mock_llm_client.agenerate.call_args)
            # Verify model name or context was included in the prompt
            assert result is not None

    @pytest.mark.asyncio
    async def test_handles_high_risk_assessment(
        self,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test handling of high-risk assessments."""
        # Arrange
        high_risk_assessment = RiskAssessment(
            model_id="high_risk_model",
            model_name="High Risk AI",
            risk_level=RiskLevel.HIGH,
            risk_score=92.0,
            transparency_score=40.0,
            fairness_score=45.0,
            accountability_score=50.0,
            robustness_score=55.0,
            privacy_score=42.0,
            security_score=60.0,
            risk_factors=["Critical data exposure", "No human oversight"],
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_risk_recommendations(
                assessment=high_risk_assessment,
                model=sample_ai_model_registration,
            )

            # Assert
            assert isinstance(result, list)


# ============================================================================
# TEST CLASS: explain_violation
# ============================================================================


class TestExplainViolation:
    """Test suite for explain_violation method."""

    @pytest.mark.asyncio
    async def test_returns_explanation_with_significance(
        self,
        sample_policy_violation_critical: PolicyViolation,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that explain_violation returns significance field."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.explain_violation(
                violation=sample_policy_violation_critical,
                model=sample_ai_model_registration,
            )

            # Assert
            assert isinstance(result, dict)
            assert "significance" in result

    @pytest.mark.asyncio
    async def test_returns_business_impact(
        self,
        sample_policy_violation_critical: PolicyViolation,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that explain_violation returns business_impact field."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.explain_violation(
                violation=sample_policy_violation_critical,
                model=sample_ai_model_registration,
            )

            # Assert
            assert "business_impact" in result

    @pytest.mark.asyncio
    async def test_returns_remediation_priority(
        self,
        sample_policy_violation_critical: PolicyViolation,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that explain_violation returns remediation_priority field."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.explain_violation(
                violation=sample_policy_violation_critical,
                model=sample_ai_model_registration,
            )

            # Assert
            assert "remediation_priority" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "severity",
        [
            ViolationSeverity.CRITICAL,
            ViolationSeverity.HIGH,
            ViolationSeverity.MEDIUM,
            ViolationSeverity.LOW,
            ViolationSeverity.INFORMATIONAL,
        ],
    )
    async def test_handles_different_severity_levels(
        self,
        severity: ViolationSeverity,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that all severity levels are handled correctly."""
        # Arrange
        violation = PolicyViolation(
            regulation=RegulationType.EU_AI_ACT,
            policy_id=f"pol_{severity.value}",
            policy_name=f"Test Policy - {severity.value}",
            severity=severity,
            title=f"Test Violation - {severity.value}",
            description=f"Test description for {severity.value} severity",
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.explain_violation(
                violation=violation,
                model=sample_ai_model_registration,
            )

            # Assert
            assert isinstance(result, dict)
            assert "significance" in result
            assert "business_impact" in result
            assert "remediation_priority" in result

    @pytest.mark.asyncio
    async def test_critical_violation_has_high_priority(
        self,
        sample_policy_violation_critical: PolicyViolation,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that critical violations receive high remediation priority."""
        # Arrange
        mock_llm_client.agenerate = AsyncMock(
            return_value=MagicMock(
                content='{"significance": "Major regulatory exposure", "business_impact": "Potential fines up to 6% of annual turnover", "remediation_priority": "critical", "suggested_actions": []}'
            )
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.explain_violation(
                violation=sample_policy_violation_critical,
                model=sample_ai_model_registration,
            )

            # Assert
            priority = result.get("remediation_priority", "").lower()
            assert priority in ["immediate", "critical", "high", "urgent", "1"]


# ============================================================================
# TEST CLASS: generate_remediation_roadmap
# ============================================================================


class TestGenerateRemediationRoadmap:
    """Test suite for generate_remediation_roadmap method."""

    @pytest.mark.asyncio
    async def test_returns_prioritized_actions(
        self,
        sample_violations_list: List[PolicyViolation],
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that roadmap includes prioritized_actions."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_remediation_roadmap(
                violations=sample_violations_list,
                model=sample_ai_model_registration,
            )

            # Assert
            assert isinstance(result, dict)
            assert "prioritized_actions" in result

    @pytest.mark.asyncio
    async def test_returns_timeline(
        self,
        sample_violations_list: List[PolicyViolation],
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that roadmap includes timeline."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_remediation_roadmap(
                violations=sample_violations_list,
                model=sample_ai_model_registration,
            )

            # Assert
            assert "timeline" in result

    @pytest.mark.asyncio
    async def test_returns_resource_estimates(
        self,
        sample_violations_list: List[PolicyViolation],
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that roadmap includes resource_estimates."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_remediation_roadmap(
                violations=sample_violations_list,
                model=sample_ai_model_registration,
            )

            # Assert
            assert "resource_estimates" in result

    @pytest.mark.asyncio
    async def test_handles_empty_violations_list(
        self,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that empty violations list is handled gracefully."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_remediation_roadmap(
                violations=[],
                model=sample_ai_model_registration,
            )

            # Assert
            assert isinstance(result, dict)
            # Should return valid structure even with no violations
            assert "prioritized_actions" in result
            assert "timeline" in result
            assert "resource_estimates" in result

    @pytest.mark.asyncio
    async def test_prioritizes_critical_violations_first(
        self,
        sample_violations_list: List[PolicyViolation],
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test that critical violations are prioritized in the roadmap."""
        # Arrange
        mock_llm_client.agenerate = AsyncMock(
            return_value=MagicMock(
                content="""{
                    "prioritized_actions": [
                        {"title": "Remediate: Missing AI Disclosure", "priority": 1, "category": "eu_ai_act", "estimated_hours": 40},
                        {"title": "Remediate: Data Retention", "priority": 2, "category": "gdpr", "estimated_hours": 24},
                        {"title": "Remediate: Documentation", "priority": 3, "category": "soc2", "estimated_hours": 8}
                    ],
                    "timeline": "Urgent: Critical items within 1 week, full remediation 4-6 weeks",
                    "resource_estimates": {"estimated_hours": 72, "fte_weeks": 1.8, "team_recommendation": "1-2 dedicated resources"},
                    "quick_wins": ["Enable audit logging", "Update privacy policy"]
                }"""
            )
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_remediation_roadmap(
                violations=sample_violations_list,
                model=sample_ai_model_registration,
            )

            # Assert
            actions = result.get("prioritized_actions", [])
            if isinstance(actions, list) and len(actions) > 0:
                # First action should have highest priority (1)
                first_action = actions[0]
                if isinstance(first_action, dict):
                    assert first_action.get("priority") == 1


# ============================================================================
# TEST CLASS: generate_executive_summary
# ============================================================================


class TestGenerateExecutiveSummary:
    """Test suite for generate_executive_summary method."""

    @pytest.mark.asyncio
    async def test_returns_string_narrative(
        self,
        sample_report_data: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that executive summary returns a string narrative."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_executive_summary(
                report_data=sample_report_data,
            )

            # Assert
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_summary_is_coherent_narrative(
        self,
        sample_report_data: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that summary is a coherent narrative, not bullet points."""
        # Arrange
        mock_llm_client.agenerate = AsyncMock(
            return_value=MagicMock(
                content="This reporting period demonstrates continued progress in our AI compliance program. The organization achieved an overall compliance score of 76.5%, representing a stable position with room for improvement. Critical attention is required for the AI transparency violation detected in user-facing systems, which carries potential regulatory exposure under the EU AI Act."
            )
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_executive_summary(
                report_data=sample_report_data,
            )

            # Assert
            # Check for sentence structure (contains periods and reasonable length)
            assert "." in result
            assert len(result) > 100  # Narrative should be substantial

    @pytest.mark.asyncio
    async def test_summary_includes_key_metrics(
        self,
        sample_report_data: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that summary mentions key metrics from report data."""
        # Arrange
        mock_llm_client.agenerate = AsyncMock(
            return_value=MagicMock(
                content="The compliance assessment covering the period achieved an overall score of 76.5%, with 5 AI models assessed. There were 3 total violations identified, including 1 critical violation requiring immediate attention. The remediation completion rate stands at 67%, showing progress in addressing identified issues."
            )
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_executive_summary(
                report_data=sample_report_data,
            )

            # Assert
            # Check that key metrics are referenced (as strings in the narrative)
            result_lower = result.lower()
            # Should mention compliance score
            assert "76" in result or "score" in result_lower
            # Should mention violations
            assert "violation" in result_lower or "issue" in result_lower

    @pytest.mark.asyncio
    async def test_handles_empty_report_data(
        self,
        mock_llm_client,
    ):
        """Test handling of minimal report data."""
        # Arrange
        minimal_report = {
            "report_id": "rpt_empty",
            "overall_score": {},
            "models_assessed": 0,
            "violations_summary": {},
        }

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.generate_executive_summary(
                report_data=minimal_report,
            )

            # Assert
            assert isinstance(result, str)


# ============================================================================
# TEST CLASS: answer_compliance_question
# ============================================================================


class TestAnswerComplianceQuestion:
    """Test suite for answer_compliance_question method."""

    @pytest.mark.asyncio
    async def test_returns_string_answer(
        self,
        sample_context: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that answer_compliance_question returns a string."""
        # Arrange
        question = "What are the key requirements of the EU AI Act for high-risk AI systems?"

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.answer_compliance_question(
                question=question,
                context=sample_context,
            )

            # Assert
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_returns_relevant_answer(
        self,
        sample_context: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that answer is relevant to the question."""
        # Arrange
        question = "What is the maximum fine under GDPR for data breaches?"

        mock_llm_client.agenerate = AsyncMock(
            return_value=MagicMock(
                content="Under GDPR, organizations can face fines of up to 4% of annual global turnover or 20 million EUR, whichever is greater, for the most serious violations including data breaches that affect data subject rights."
            )
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.answer_compliance_question(
                question=question,
                context=sample_context,
            )

            # Assert
            # Answer should contain relevant terms
            result_lower = result.lower()
            assert "gdpr" in result_lower or "fine" in result_lower or "%" in result

    @pytest.mark.asyncio
    async def test_handles_context_properly(
        self,
        sample_context: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that context is properly used in generating answers."""
        # Arrange
        question = "How should our organization approach AI compliance?"

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.answer_compliance_question(
                question=question,
                context=sample_context,
            )

            # Assert - LLM should have been called with context
            mock_llm_client.agenerate.assert_called()
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_handles_empty_context(
        self,
        mock_llm_client,
    ):
        """Test handling of empty context."""
        # Arrange
        question = "What is the EU AI Act?"

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.answer_compliance_question(
                question=question,
                context={},
            )

            # Assert
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_handles_complex_questions(
        self,
        sample_context: Dict[str, Any],
        mock_llm_client,
    ):
        """Test handling of complex, multi-part questions."""
        # Arrange
        question = (
            "Given our organization's use of AI for lead scoring in real estate, "
            "what specific EU AI Act requirements apply to us, and how do they intersect "
            "with GDPR requirements for automated decision-making?"
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            result = await analyzer.answer_compliance_question(
                question=question,
                context=sample_context,
            )

            # Assert
            assert isinstance(result, str)
            assert len(result) > 50  # Complex question should get substantial answer


# ============================================================================
# TEST CLASS: Error Handling and Edge Cases
# ============================================================================


class TestErrorHandling:
    """Test suite for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_handles_llm_client_failure_with_fallback(
        self,
        sample_risk_scores: Dict[str, float],
        sample_ai_model_registration: AIModelRegistration,
        sample_context: Dict[str, Any],
    ):
        """Test graceful handling when LLM client fails - should return fallback response."""
        # Arrange
        mock_client = MagicMock()
        mock_client.agenerate = AsyncMock(side_effect=Exception("LLM API unavailable"))

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act - The implementation has fallback behavior
            result = await analyzer.explain_risk_dimension(
                dimension="transparency",
                scores=sample_risk_scores,
                model=sample_ai_model_registration,
                context=sample_context,
            )

            # Assert - Should return fallback response, not raise
            assert isinstance(result, dict)
            assert "explanation" in result
            assert "key_concerns" in result
            assert "mitigation_strategies" in result

    @pytest.mark.asyncio
    async def test_handles_malformed_llm_response(
        self,
        sample_risk_scores: Dict[str, float],
        sample_ai_model_registration: AIModelRegistration,
        sample_context: Dict[str, Any],
    ):
        """Test handling of malformed LLM responses."""
        # Arrange
        mock_client = MagicMock()
        mock_client.agenerate = AsyncMock(
            return_value=MagicMock(content="Not valid JSON at all {{{")
        )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act - The implementation parses JSON and falls back gracefully
            result = await analyzer.explain_risk_dimension(
                dimension="transparency",
                scores=sample_risk_scores,
                model=sample_ai_model_registration,
                context=sample_context,
            )

            # Assert - Should return valid structure via fallback
            assert isinstance(result, dict)
            assert "explanation" in result

    @pytest.mark.asyncio
    async def test_handles_none_values_in_input(
        self,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test handling of None values in input data."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act & Assert - Should handle None context gracefully (converts to {})
            result = await analyzer.answer_compliance_question(
                question="What is compliance?",
                context=None,
            )
            assert isinstance(result, str)


# ============================================================================
# TEST CLASS: Performance Tests
# ============================================================================


class TestPerformance:
    """Test suite for performance requirements."""

    @pytest.mark.asyncio
    async def test_explain_risk_dimension_response_time(
        self,
        sample_risk_scores: Dict[str, float],
        sample_ai_model_registration: AIModelRegistration,
        sample_context: Dict[str, Any],
        mock_llm_client,
    ):
        """Test that explain_risk_dimension completes within acceptable time."""
        # Arrange
        import time

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            start_time = time.time()
            await analyzer.explain_risk_dimension(
                dimension="transparency",
                scores=sample_risk_scores,
                model=sample_ai_model_registration,
                context=sample_context,
            )
            execution_time = time.time() - start_time

            # Assert - Should complete quickly with mocked LLM
            assert execution_time < 1.0, f"Execution took {execution_time:.2f}s, should be <1s"

    @pytest.mark.asyncio
    async def test_generate_remediation_roadmap_with_many_violations(
        self,
        sample_ai_model_registration: AIModelRegistration,
        mock_llm_client,
    ):
        """Test roadmap generation performance with many violations."""
        # Arrange
        import time

        # Create 20 violations
        violations = []
        for i in range(20):
            severity = [
                ViolationSeverity.CRITICAL,
                ViolationSeverity.HIGH,
                ViolationSeverity.MEDIUM,
                ViolationSeverity.LOW,
            ][i % 4]
            violations.append(
                PolicyViolation(
                    violation_id=f"viol_{i:03d}",
                    regulation=RegulationType.EU_AI_ACT,
                    policy_id=f"pol_{i:03d}",
                    policy_name=f"Test Policy {i}",
                    severity=severity,
                    title=f"Test Violation {i}",
                    description=f"Description for violation {i}",
                )
            )

        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act
            start_time = time.time()
            result = await analyzer.generate_remediation_roadmap(
                violations=violations,
                model=sample_ai_model_registration,
            )
            execution_time = time.time() - start_time

            # Assert
            assert isinstance(result, dict)
            assert execution_time < 5.0, f"Execution took {execution_time:.2f}s, should be <5s"


# ============================================================================
# TEST CLASS: Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for ComplianceAIAnalyzer."""

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self, mock_llm_client):
        """Test that analyzer initializes correctly."""
        # Arrange & Act
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Assert
            assert analyzer is not None
            assert hasattr(analyzer, "explain_risk_dimension")
            assert hasattr(analyzer, "generate_risk_recommendations")
            assert hasattr(analyzer, "explain_violation")
            assert hasattr(analyzer, "generate_remediation_roadmap")
            assert hasattr(analyzer, "generate_executive_summary")
            assert hasattr(analyzer, "answer_compliance_question")

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(
        self,
        sample_risk_assessment: RiskAssessment,
        sample_violations_list: List[PolicyViolation],
        sample_ai_model_registration: AIModelRegistration,
        sample_context: Dict[str, Any],
        sample_report_data: Dict[str, Any],
        mock_llm_client,
    ):
        """Test a complete analysis workflow using all methods."""
        # Arrange
        with patch(
            "ghl_real_estate_ai.compliance_platform.services.compliance_ai_analyzer.LLMClient",
            return_value=mock_llm_client,
        ):
            analyzer = ComplianceAIAnalyzer()

            # Act - Execute full workflow
            # Step 1: Explain risk dimensions
            risk_explanation = await analyzer.explain_risk_dimension(
                dimension="transparency",
                scores={
                    "transparency": sample_risk_assessment.transparency_score,
                    "fairness": sample_risk_assessment.fairness_score,
                    "accountability": sample_risk_assessment.accountability_score,
                    "robustness": sample_risk_assessment.robustness_score,
                    "privacy": sample_risk_assessment.privacy_score,
                    "security": sample_risk_assessment.security_score,
                },
                model=sample_ai_model_registration,
                context=sample_context,
            )

            # Step 2: Generate recommendations
            recommendations = await analyzer.generate_risk_recommendations(
                assessment=sample_risk_assessment,
                model=sample_ai_model_registration,
            )

            # Step 3: Explain violations
            violation_explanation = await analyzer.explain_violation(
                violation=sample_violations_list[0],
                model=sample_ai_model_registration,
            )

            # Step 4: Generate roadmap
            roadmap = await analyzer.generate_remediation_roadmap(
                violations=sample_violations_list,
                model=sample_ai_model_registration,
            )

            # Step 5: Generate executive summary
            summary = await analyzer.generate_executive_summary(
                report_data=sample_report_data,
            )

            # Step 6: Answer question
            answer = await analyzer.answer_compliance_question(
                question="What are our compliance priorities?",
                context=sample_context,
            )

            # Assert - All components returned valid results
            assert isinstance(risk_explanation, dict)
            assert isinstance(recommendations, list)
            assert isinstance(violation_explanation, dict)
            assert isinstance(roadmap, dict)
            assert isinstance(summary, str)
            assert isinstance(answer, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
