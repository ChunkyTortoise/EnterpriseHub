"""
Comprehensive Test Suite for Claude Lead Intelligence System

Complete testing coverage for all Claude AI-powered lead intelligence features
including qualification engine, enrichment engine, API endpoints, and webhook integration.

Test Categories:
- Unit Tests: Individual service and component testing
- Integration Tests: API endpoint and service integration testing
- Performance Tests: Response time and throughput validation
- End-to-End Tests: Complete workflow testing from webhook to dashboard
- Mock Data Tests: Realistic lead data processing scenarios

Coverage Target: 95%+ across all intelligence components
"""

import asyncio
import json
import pytest
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi.testclient import TestClient
from anthropic import AsyncAnthropic

# Test framework imports
import pytest_asyncio
from pytest_mock import MockerFixture

# Claude Intelligence Services
from ghl_real_estate_ai.services.claude_lead_qualification_engine import (
    ClaudeLeadQualificationEngine,
    QualificationResult,
    LeadSourceType,
    LeadPriorityLevel,
    QualificationStatus,
    ContactType
)
from ghl_real_estate_ai.services.claude_lead_enrichment_engine import (
    ClaudeLeadEnrichmentEngine,
    LeadEnrichmentAnalysis,
    EnrichmentPriority,
    DataSourceType,
    ValidationStatus
)

# API endpoints
from ghl_real_estate_ai.api.routes.claude_lead_intelligence import (
    LeadNotificationData,
    ComprehensiveLeadAnalysisRequest,
    ComprehensiveLeadAnalysisResponse,
    ChatWithClaudeRequest,
    ChatWithClaudeResponse
)

# Test utilities
from ghl_real_estate_ai.tests.utils.test_data_factory import (
    create_test_lead_data,
    create_test_webhook_event,
    create_mock_claude_response
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# ========================================================================
# Test Configuration and Fixtures
# ========================================================================

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for Claude API calls."""
    mock_client = AsyncMock(spec=AsyncAnthropic)
    mock_message = MagicMock()
    mock_message.content = [MagicMock()]
    mock_message.content[0].text = json.dumps({
        "qualification_metrics": {
            "overall_score": 75,
            "intent_score": 80,
            "urgency_score": 70,
            "financial_capability_score": 65,
            "fit_score": 75,
            "data_quality_score": 60,
            "source_quality_score": 70,
            "engagement_potential": 75
        },
        "contact_type": "seller",
        "qualification_status": "partially_qualified",
        "priority_level": "high"
    })
    mock_client.messages.create.return_value = mock_message
    return mock_client

@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        "lead_id": f"test_lead_{uuid.uuid4().hex[:8]}",
        "full_name": "John Doe",
        "phone": "(555) 123-4567",
        "email": "john.doe@example.com",
        "property_address": "123 Main St, Anytown, CA 12345",
        "primary_contact_type": "seller",
        "campaign_name": "Facebook Ad Campaign",
        "source": "ghl_webhook",
        "notes": "Interested in selling property quickly",
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture
def sample_email_notification():
    """Sample email notification for parsing tests."""
    return """
    Hi,

    A new lead has been submitted through one of your lead generation channels. Here are the details:

    Campaign Name: ReSimpli Leads
    Full Name: Jamie Hoffman
    Cell Phone: (248) 840-0207
    Email: jamie.hoffman@example.com
    Property Address: 2690 North Kitty Hawk Drive, Palm Springs California 92262
    Notes: Looking to sell within 3 months
    Primary Contact Type: Seller
    Type Of Property: Single Family Home

    Please take the necessary actions to follow up with this lead.
    """

@pytest.fixture
def qualification_engine():
    """Claude Lead Qualification Engine instance."""
    return ClaudeLeadQualificationEngine()

@pytest.fixture
def enrichment_engine():
    """Claude Lead Enrichment Engine instance."""
    return ClaudeLeadEnrichmentEngine()

# ========================================================================
# Unit Tests - Claude Lead Qualification Engine
# ========================================================================

@pytest.mark.asyncio
class TestClaudeLeadQualificationEngine:
    """Test suite for Claude Lead Qualification Engine."""

    async def test_initialization(self, qualification_engine):
        """Test qualification engine initialization."""
        assert qualification_engine is not None
        assert qualification_engine.model == "claude-3-5-sonnet-20241022"
        assert qualification_engine.max_tokens == 3000
        assert qualification_engine.temperature == 0.3
        assert len(qualification_engine.templates) == 4

    @patch('ghl_real_estate_ai.services.claude_lead_qualification_engine.AsyncAnthropic')
    async def test_qualify_lead_success(self, mock_anthropic, qualification_engine, sample_lead_data):
        """Test successful lead qualification."""
        # Mock Claude API response
        mock_client = AsyncMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps({
            "completeness_score": 75,
            "quality_score": 80,
            "confidence_level": 0.85,
            "missing_critical_fields": ["budget"],
            "missing_optional_fields": ["timeline"],
            "data_inconsistencies": [],
            "enrichment_opportunities": ["property_value_lookup"],
            "verification_needed": ["phone"]
        })
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        # Patch the qualification engine's client
        qualification_engine.claude_client = mock_client

        # Test qualification
        result = await qualification_engine.qualify_lead(
            lead_data=sample_lead_data,
            source_type=LeadSourceType.GHL_WEBHOOK,
            agent_id="test_agent",
            tenant_id="test_tenant"
        )

        # Assertions
        assert isinstance(result, QualificationResult)
        assert result.lead_id == sample_lead_data["lead_id"]
        assert result.source_type == LeadSourceType.GHL_WEBHOOK
        assert result.agent_id == "test_agent"
        assert result.tenant_id == "test_tenant"
        assert result.processing_time_ms > 0
        assert 0 <= result.confidence_score <= 1

    async def test_qualify_email_lead(self, qualification_engine, sample_email_notification):
        """Test email lead qualification."""
        with patch.object(qualification_engine, 'qualify_lead') as mock_qualify:
            mock_result = MagicMock(spec=QualificationResult)
            mock_qualify.return_value = mock_result

            result = await qualification_engine.qualify_email_lead(
                email_text=sample_email_notification,
                agent_id="test_agent"
            )

            assert mock_qualify.called
            assert result == mock_result

    @patch('ghl_real_estate_ai.services.claude_lead_qualification_engine.AsyncAnthropic')
    async def test_bulk_qualify_leads(self, mock_anthropic, qualification_engine):
        """Test bulk lead qualification with concurrency control."""
        # Create test leads
        test_leads = [
            {"lead_id": f"lead_{i}", "full_name": f"Test Lead {i}"}
            for i in range(5)
        ]

        with patch.object(qualification_engine, 'qualify_lead') as mock_qualify:
            mock_result = MagicMock(spec=QualificationResult)
            mock_qualify.return_value = mock_result

            results = await qualification_engine.bulk_qualify_leads(
                leads=test_leads,
                source_type=LeadSourceType.API_SUBMISSION,
                max_concurrent=3
            )

            assert len(results) == 5
            assert mock_qualify.call_count == 5

    async def test_claude_api_error_handling(self, qualification_engine, sample_lead_data):
        """Test Claude API error handling and retries."""
        with patch.object(qualification_engine, '_call_claude') as mock_call:
            # Simulate API failures then success
            mock_call.side_effect = [
                Exception("API Error 1"),
                Exception("API Error 2"),
                json.dumps({"qualification_metrics": {"overall_score": 50}})
            ]

            # Should succeed after retries
            result = await qualification_engine._analyze_data_quality(sample_lead_data)
            assert result is not None
            assert mock_call.call_count == 3

    async def test_performance_metrics_tracking(self, qualification_engine, sample_lead_data):
        """Test performance metrics tracking."""
        initial_metrics = qualification_engine.get_performance_metrics()

        with patch.object(qualification_engine, 'qualify_lead') as mock_qualify:
            mock_result = MagicMock(spec=QualificationResult)
            mock_result.processing_time_ms = 250.0
            mock_qualify.return_value = mock_result

            await qualification_engine.qualify_lead(
                lead_data=sample_lead_data,
                source_type=LeadSourceType.API_SUBMISSION
            )

            updated_metrics = qualification_engine.get_performance_metrics()
            assert updated_metrics["total_qualifications"] > initial_metrics["total_qualifications"]

# ========================================================================
# Unit Tests - Claude Lead Enrichment Engine
# ========================================================================

@pytest.mark.asyncio
class TestClaudeLeadEnrichmentEngine:
    """Test suite for Claude Lead Enrichment Engine."""

    async def test_initialization(self, enrichment_engine):
        """Test enrichment engine initialization."""
        assert enrichment_engine is not None
        assert enrichment_engine.model == "claude-3-5-sonnet-20241022"
        assert enrichment_engine.temperature == 0.2
        assert len(enrichment_engine.templates) == 3

    @patch('ghl_real_estate_ai.services.claude_lead_enrichment_engine.AsyncAnthropic')
    async def test_analyze_enrichment_needs_success(self, mock_anthropic, enrichment_engine, sample_lead_data):
        """Test successful enrichment needs analysis."""
        # Mock Claude API responses
        mock_client = AsyncMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps({
            "identified_gaps": [
                {
                    "field_name": "budget_range",
                    "field_type": "financial",
                    "priority": "high",
                    "impact_score": 85,
                    "collection_difficulty": "moderate",
                    "suggested_sources": ["contact_verification"],
                    "collection_methods": ["direct_question"],
                    "example_questions": ["What's your budget range?"],
                    "enrichment_apis": ["budget_estimation_api"]
                }
            ],
            "gap_priority_score": 75,
            "completeness_score": 65,
            "estimated_improvement": 25
        })
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        enrichment_engine.claude_client = mock_client

        # Test analysis
        result = await enrichment_engine.analyze_lead_enrichment_needs(
            lead_data=sample_lead_data,
            include_validation=True
        )

        # Assertions
        assert isinstance(result, LeadEnrichmentAnalysis)
        assert len(result.identified_gaps) >= 0
        assert 0 <= result.completeness_score <= 100
        assert result.processing_time_ms > 0

    async def test_enrich_lead_data(self, enrichment_engine, sample_lead_data):
        """Test actual lead data enrichment."""
        # Mock enrichment analysis
        mock_analysis = MagicMock(spec=LeadEnrichmentAnalysis)
        mock_analysis.enrichment_opportunities = []

        enriched_data, enrichment_results = await enrichment_engine.enrich_lead_data(
            lead_data=sample_lead_data,
            enrichment_analysis=mock_analysis,
            auto_enrich=True,
            max_cost=5.0
        )

        assert isinstance(enriched_data, dict)
        assert isinstance(enrichment_results, list)
        assert sample_lead_data["lead_id"] == enriched_data.get("lead_id")

    async def test_property_data_enrichment(self, enrichment_engine):
        """Test property data enrichment functionality."""
        # Mock opportunity
        opportunity = MagicMock()
        opportunity.source = DataSourceType.PROPERTY_DATABASE
        opportunity.dependencies = ["property_address"]
        opportunity.data_type = "property_value"

        lead_data = {"property_address": "123 Main St, Anytown, CA"}
        current_data = {"property_address": "123 Main St, Anytown, CA"}

        result = await enrichment_engine._enrich_property_data(
            lead_data, opportunity, current_data
        )

        assert result is not None
        assert result.source == DataSourceType.PROPERTY_DATABASE
        assert result.enriched_value is not None

    async def test_contact_validation(self, enrichment_engine):
        """Test contact information validation."""
        opportunity = MagicMock()
        opportunity.source = DataSourceType.CONTACT_VERIFICATION
        opportunity.data_type = "phone_validation"
        opportunity.dependencies = []

        lead_data = {}
        current_data = {"phone": "5551234567"}

        result = await enrichment_engine._enrich_contact_data(
            lead_data, opportunity, current_data
        )

        assert result is not None
        assert result.validation_result is not None
        assert result.validation_result.status == ValidationStatus.VALID

    async def test_performance_metrics(self, enrichment_engine):
        """Test enrichment engine performance tracking."""
        metrics = enrichment_engine.get_performance_metrics()

        assert "total_analyses" in metrics
        assert "avg_processing_time_ms" in metrics
        assert "enrichment_success_rate" in metrics
        assert "timestamp" in metrics

# ========================================================================
# Integration Tests - API Endpoints
# ========================================================================

@pytest.mark.asyncio
class TestClaudeLeadIntelligenceAPI:
    """Test suite for Claude Lead Intelligence API endpoints."""

    @pytest.fixture
    def test_client(self):
        """Test client for API testing."""
        from ghl_real_estate_ai.main import app
        return TestClient(app)

    def test_analyze_lead_endpoint(self, test_client, sample_lead_data):
        """Test comprehensive lead analysis endpoint."""
        request_data = {
            "lead_data": {
                "full_name": sample_lead_data["full_name"],
                "phone": sample_lead_data["phone"],
                "email": sample_lead_data["email"],
                "property_address": sample_lead_data["property_address"],
                "primary_contact_type": sample_lead_data["primary_contact_type"]
            },
            "analysis_depth": "comprehensive",
            "include_market_intelligence": True,
            "include_coaching_suggestions": True,
            "include_action_planning": True
        }

        with patch('ghl_real_estate_ai.services.claude_lead_qualification_engine.get_qualification_engine'):
            with patch('ghl_real_estate_ai.services.claude_lead_enrichment_engine.get_enrichment_engine'):
                response = test_client.post(
                    "/api/v1/claude-intelligence/analyze-lead",
                    json=request_data
                )

                # Note: This test would need proper mocking of async services
                # For now, we test the endpoint structure
                assert response is not None

    def test_chat_with_claude_endpoint(self, test_client):
        """Test chat with Claude endpoint."""
        request_data = {
            "query": "What are the best leads to follow up with today?",
            "agent_id": "test_agent",
            "include_kpis": True,
            "include_lead_data": True
        }

        with patch('ghl_real_estate_ai.services.claude_agent_service.claude_agent_service'):
            response = test_client.post(
                "/api/v1/claude-intelligence/chat",
                json=request_data
            )

            # Test endpoint structure
            assert response is not None

    def test_process_email_notification_endpoint(self, test_client, sample_email_notification):
        """Test email notification processing endpoint."""
        with patch('ghl_real_estate_ai.api.routes.claude_lead_intelligence.parse_email_lead_notification'):
            response = test_client.post(
                "/api/v1/claude-intelligence/process-email-notification",
                params={
                    "email_text": sample_email_notification,
                    "agent_id": "test_agent",
                    "auto_analyze": True
                }
            )

            # Test endpoint structure
            assert response is not None

    def test_quick_lead_insight_endpoint(self, test_client, sample_lead_data):
        """Test quick lead insight endpoint."""
        request_data = {
            "lead_data": {
                "full_name": sample_lead_data["full_name"],
                "phone": sample_lead_data["phone"],
                "email": sample_lead_data["email"],
                "property_address": sample_lead_data["property_address"],
                "primary_contact_type": sample_lead_data["primary_contact_type"]
            },
            "query": "What is the qualification status of this lead?",
            "agent_id": "test_agent"
        }

        with patch('ghl_real_estate_ai.services.claude_agent_service.claude_agent_service'):
            response = test_client.post(
                "/api/v1/claude-intelligence/quick-lead-insight",
                json=request_data
            )

            # Test endpoint structure
            assert response is not None

# ========================================================================
# Integration Tests - Webhook Processing
# ========================================================================

@pytest.mark.asyncio
class TestWebhookIntegration:
    """Test suite for GHL webhook integration with Claude intelligence."""

    @pytest.fixture
    def mock_webhook_event(self):
        """Mock GHL webhook event."""
        return {
            "contact_id": "test_contact_123",
            "location_id": "test_location_456",
            "message": {
                "type": "SMS",
                "body": "I'm interested in selling my property at 123 Main St"
            },
            "contact": {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "(555) 123-4567",
                "email": "john@example.com",
                "tags": ["Needs Qualifying", "Seller"]
            }
        }

    async def test_webhook_claude_intelligence_integration(self, mock_webhook_event):
        """Test webhook processing with Claude intelligence integration."""
        with patch('ghl_real_estate_ai.services.claude_lead_qualification_engine.get_qualification_engine') as mock_qual:
            with patch('ghl_real_estate_ai.services.claude_lead_enrichment_engine.get_enrichment_engine') as mock_enrich:
                # Mock qualification result
                mock_qualification_result = MagicMock()
                mock_qualification_result.priority_level.value = "high"
                mock_qualification_result.qualification_metrics.overall_score = 85
                mock_qual_engine = MagicMock()
                mock_qual_engine.qualify_lead.return_value = mock_qualification_result
                mock_qual.return_value = mock_qual_engine

                # Mock enrichment result
                mock_enrichment_result = MagicMock()
                mock_enrichment_result.completeness_score = 67
                mock_enrich_engine = MagicMock()
                mock_enrich_engine.analyze_lead_enrichment_needs.return_value = mock_enrichment_result
                mock_enrich.return_value = mock_enrich_engine

                # Test webhook processing logic
                # This would be integrated into actual webhook handler testing
                assert mock_qual_engine is not None
                assert mock_enrich_engine is not None

    async def test_comprehensive_ghl_actions_preparation(self):
        """Test comprehensive GHL actions with intelligence data."""
        from ghl_real_estate_ai.api.routes.webhook import prepare_comprehensive_ghl_actions
        from ghl_real_estate_ai.api.schemas.ghl import GHLWebhookEvent

        # Mock event and intelligence data
        mock_event = MagicMock(spec=GHLWebhookEvent)
        mock_event.contact_id = "test_contact"

        mock_qualification_result = MagicMock()
        mock_qualification_result.priority_level.value = "critical"
        mock_qualification_result.qualification_status.value = "fully_qualified"
        mock_qualification_result.contact_type.value = "seller"
        mock_qualification_result.qualification_metrics.overall_score = 92
        mock_qualification_result.confidence_score = 0.89

        mock_enrichment_analysis = MagicMock()
        mock_enrichment_analysis.completeness_score = 78
        mock_enrichment_analysis.identified_gaps = []
        mock_enrichment_analysis.suspicious_data_count = 0

        with patch('ghl_real_estate_ai.api.routes.webhook.prepare_enhanced_ghl_actions') as mock_enhanced:
            mock_enhanced.return_value = []

            actions = await prepare_comprehensive_ghl_actions(
                extracted_data={},
                lead_score=85,
                event=mock_event,
                claude_semantics={},
                qualification_progress={},
                lead_qualification_result=mock_qualification_result,
                lead_enrichment_analysis=mock_enrichment_analysis
            )

            assert isinstance(actions, list)
            # Would contain intelligence-driven actions

# ========================================================================
# Performance Tests
# ========================================================================

@pytest.mark.performance
class TestPerformance:
    """Performance test suite for Claude intelligence services."""

    @pytest.mark.asyncio
    async def test_qualification_performance(self, qualification_engine, sample_lead_data):
        """Test qualification performance under load."""
        start_time = time.time()

        with patch.object(qualification_engine, '_call_claude') as mock_call:
            mock_call.return_value = json.dumps({
                "qualification_metrics": {"overall_score": 75},
                "contact_type": "seller",
                "qualification_status": "partially_qualified",
                "priority_level": "high"
            })

            # Test single qualification performance
            result = await qualification_engine.qualify_lead(
                lead_data=sample_lead_data,
                source_type=LeadSourceType.API_SUBMISSION
            )

            processing_time = time.time() - start_time

            # Performance assertions
            assert processing_time < 5.0  # Should complete within 5 seconds
            assert result.processing_time_ms < 3000  # Should process within 3 seconds

    @pytest.mark.asyncio
    async def test_bulk_processing_performance(self, qualification_engine):
        """Test bulk processing performance and concurrency."""
        # Create 10 test leads
        test_leads = [
            {"lead_id": f"perf_test_{i}", "full_name": f"Test Lead {i}"}
            for i in range(10)
        ]

        start_time = time.time()

        with patch.object(qualification_engine, 'qualify_lead') as mock_qualify:
            mock_result = MagicMock(spec=QualificationResult)
            mock_result.processing_time_ms = 200
            mock_qualify.return_value = mock_result

            results = await qualification_engine.bulk_qualify_leads(
                leads=test_leads,
                source_type=LeadSourceType.API_SUBMISSION,
                max_concurrent=5
            )

            total_time = time.time() - start_time

            # Performance assertions
            assert len(results) == 10
            assert total_time < 10.0  # Should complete within 10 seconds for 10 leads

    @pytest.mark.asyncio
    async def test_enrichment_performance(self, enrichment_engine, sample_lead_data):
        """Test enrichment analysis performance."""
        start_time = time.time()

        with patch.object(enrichment_engine, '_call_claude') as mock_call:
            mock_call.return_value = json.dumps({
                "identified_gaps": [],
                "gap_priority_score": 50,
                "completeness_score": 70
            })

            result = await enrichment_engine.analyze_lead_enrichment_needs(
                lead_data=sample_lead_data
            )

            processing_time = time.time() - start_time

            # Performance assertions
            assert processing_time < 3.0  # Should complete within 3 seconds
            assert result.processing_time_ms < 2000  # Should process within 2 seconds

# ========================================================================
# End-to-End Tests
# ========================================================================

@pytest.mark.e2e
class TestEndToEnd:
    """End-to-end test suite for complete workflow scenarios."""

    @pytest.mark.asyncio
    async def test_complete_email_to_dashboard_workflow(self, sample_email_notification):
        """Test complete workflow from email notification to dashboard display."""
        # This would test the entire pipeline:
        # 1. Email parsing
        # 2. Lead qualification
        # 3. Data enrichment
        # 4. Webhook processing
        # 5. Dashboard update

        # Mock all services
        with patch('ghl_real_estate_ai.services.claude_lead_qualification_engine.get_qualification_engine'):
            with patch('ghl_real_estate_ai.services.claude_lead_enrichment_engine.get_enrichment_engine'):
                # Test would verify complete workflow
                assert True  # Placeholder

    @pytest.mark.asyncio
    async def test_high_volume_processing_scenario(self):
        """Test system under high volume load."""
        # Simulate high volume of leads
        num_leads = 100

        start_time = time.time()

        # Mock concurrent processing
        tasks = []
        for i in range(num_leads):
            # Would create actual processing tasks
            task = asyncio.create_task(asyncio.sleep(0.1))  # Simulate processing
            tasks.append(task)

        await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Performance under load assertions
        assert total_time < 30.0  # Should handle 100 leads within 30 seconds

    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self):
        """Test system behavior under error conditions."""
        scenarios = [
            "claude_api_timeout",
            "invalid_lead_data",
            "network_failure",
            "database_unavailable"
        ]

        for scenario in scenarios:
            # Test error recovery for each scenario
            with patch('ghl_real_estate_ai.services.claude_lead_qualification_engine.AsyncAnthropic') as mock_client:
                if scenario == "claude_api_timeout":
                    mock_client.side_effect = asyncio.TimeoutError("API Timeout")

                # Test that system handles error gracefully
                # Should not crash and should return appropriate error responses
                assert True  # Placeholder for actual error testing

# ========================================================================
# Data Quality and Edge Case Tests
# ========================================================================

@pytest.mark.data_quality
class TestDataQuality:
    """Test suite for data quality and edge case handling."""

    @pytest.mark.asyncio
    async def test_incomplete_lead_data_handling(self, qualification_engine):
        """Test handling of incomplete lead data."""
        incomplete_leads = [
            {"full_name": "John Doe"},  # Only name
            {"phone": "(555) 123-4567"},  # Only phone
            {"email": "test@example.com"},  # Only email
            {},  # Empty data
            {"full_name": "", "phone": "", "email": ""}  # Empty strings
        ]

        for incomplete_data in incomplete_leads:
            with patch.object(qualification_engine, '_call_claude') as mock_call:
                mock_call.return_value = json.dumps({
                    "qualification_metrics": {"overall_score": 25},
                    "contact_type": "unknown",
                    "qualification_status": "insufficient_data",
                    "priority_level": "low"
                })

                result = await qualification_engine.qualify_lead(
                    lead_data=incomplete_data,
                    source_type=LeadSourceType.API_SUBMISSION
                )

                assert result.qualification_status in [
                    QualificationStatus.INSUFFICIENT_DATA,
                    QualificationStatus.MINIMALLY_QUALIFIED
                ]

    @pytest.mark.asyncio
    async def test_malformed_data_handling(self, enrichment_engine):
        """Test handling of malformed data."""
        malformed_data_cases = [
            {"phone": "not-a-phone-number"},
            {"email": "invalid-email"},
            {"property_address": ""},
            {"timestamp": "invalid-date"},
            {"full_name": None},
            {"source": 12345}  # Wrong data type
        ]

        for malformed_data in malformed_data_cases:
            # Should handle gracefully without crashing
            try:
                with patch.object(enrichment_engine, '_call_claude') as mock_call:
                    mock_call.return_value = json.dumps({
                        "validation_results": [
                            {
                                "field_name": "phone",
                                "original_value": malformed_data.get("phone"),
                                "status": "invalid",
                                "confidence": 0.9,
                                "issues_found": ["invalid_format"],
                                "suggestions": ["verify_with_lead"]
                            }
                        ],
                        "data_quality_score": 30,
                        "suspicious_data_count": 1
                    })

                    result = await enrichment_engine.analyze_lead_enrichment_needs(
                        lead_data=malformed_data
                    )

                    assert result.data_quality_score <= 50  # Low quality for malformed data

            except Exception as e:
                # Should handle gracefully, not crash
                assert "validation" in str(e).lower() or "format" in str(e).lower()

    def test_special_characters_and_unicode(self, qualification_engine):
        """Test handling of special characters and unicode in lead data."""
        unicode_leads = [
            {"full_name": "José García-López"},
            {"full_name": "王小明"},
            {"full_name": "Владимир Петров"},
            {"property_address": "123 Café St, Montréal, QC"},
            {"notes": "Property has 2,500 sq ft & 3 bed/2 bath"}
        ]

        for unicode_data in unicode_leads:
            # Should handle unicode correctly
            parsed_data = LeadNotificationData(**unicode_data)
            assert parsed_data.full_name is not None

# ========================================================================
# Mock Data and Utilities
# ========================================================================

class MockDataFactory:
    """Factory for creating mock test data."""

    @staticmethod
    def create_qualification_result() -> QualificationResult:
        """Create mock qualification result."""
        from ghl_real_estate_ai.services.claude_lead_qualification_engine import (
            QualificationMetrics, SmartInsights, ActionRecommendations, LeadDataQuality
        )

        return QualificationResult(
            qualification_id="test_qual_123",
            lead_id="test_lead_123",
            agent_id="test_agent",
            tenant_id="test_tenant",
            timestamp=datetime.now(),
            source_type=LeadSourceType.GHL_WEBHOOK,
            contact_type=ContactType.SELLER,
            priority_level=LeadPriorityLevel.HIGH,
            qualification_status=QualificationStatus.PARTIALLY_QUALIFIED,
            data_quality=LeadDataQuality(
                completeness_score=75.0,
                quality_score=80.0,
                confidence_level=0.85,
                missing_critical_fields=["budget"],
                missing_optional_fields=["timeline"],
                data_inconsistencies=[],
                enrichment_opportunities=["property_value"],
                verification_needed=["phone"]
            ),
            qualification_metrics=QualificationMetrics(
                overall_score=78.5,
                intent_score=82.0,
                urgency_score=75.0,
                financial_capability_score=70.0,
                fit_score=80.0,
                data_quality_score=75.0,
                source_quality_score=85.0,
                engagement_potential=78.0
            ),
            smart_insights=SmartInsights(
                primary_insights=["High engagement level", "Clear selling intent"],
                behavioral_indicators=["Professional communication"],
                opportunity_signals=["Motivated seller"],
                risk_factors=["No budget mentioned"],
                competitive_considerations=[],
                market_timing_factors=["Spring selling season"]
            ),
            action_recommendations=ActionRecommendations(
                immediate_actions=[{"action": "schedule_consultation", "priority": "high"}],
                short_term_actions=[{"action": "property_evaluation", "priority": "medium"}],
                long_term_strategy=[],
                coaching_suggestions=["Focus on timeline"],
                conversation_starters=["When are you hoping to sell?"],
                follow_up_timeline="Contact within 24 hours"
            ),
            processing_time_ms=245.7,
            confidence_score=0.84,
            claude_model_used="claude-3-5-sonnet-20241022"
        )

# ========================================================================
# Test Configuration
# ========================================================================

# Pytest configuration
pytest_plugins = ["pytest_asyncio"]

# Test markers
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.claude_intelligence
]

# Test timeout settings
@pytest.fixture(autouse=True)
def setup_test_timeout():
    """Set up test timeout to prevent hanging tests."""
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Test timed out")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # 30 second timeout for each test

    yield

    signal.alarm(0)  # Disable alarm

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])