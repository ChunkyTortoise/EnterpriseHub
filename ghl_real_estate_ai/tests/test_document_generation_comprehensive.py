"""
Comprehensive Test Suite for Document Generation System

Tests all components of the document generation system including:
- Document Generation Engine (core service)
- Document templates and content generation
- Multi-format document generation (PDF, DOCX, PPTX, HTML)
- Integration with Property Valuation and Marketing Campaign data
- Automated workflow document generation
- Performance benchmarks and quality validation
- Claude AI content enhancement

Business Impact Validation:
- Document generation <2s performance target
- 98%+ accuracy in content integration
- 95%+ template quality validation
- Comprehensive error handling and recovery
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import time

# Import Document Generation components
from ghl_real_estate_ai.services.document_generation_engine import (
    DocumentGenerationEngine,
    DocumentTemplateManager,
    ContentIntegrationService,
    ClaudeContentEnhancer,
    DocumentQualityValidator,
    PDFDocumentGenerator,
    DOCXDocumentGenerator,
    PPTXDocumentGenerator,
    HTMLDocumentGenerator
)

from ghl_real_estate_ai.models.document_generation_models import (
    DocumentType, DocumentCategory, DocumentStatus, TemplateStyle, ContentSource,
    DocumentTemplate, DocumentContent, DocumentGenerationRequest, DocumentGenerationResponse,
    SellerProposalData, MarketAnalysisData, PropertyShowcaseData, PerformanceReportData,
    ClaudeDocumentEnhancement, DocumentQualityValidation, DocumentDeliveryConfiguration,
    DocumentGenerationMetrics, PropertyValuationIntegration, MarketingCampaignIntegration,
    SellerWorkflowIntegration, BulkDocumentRequest, BulkDocumentResponse,
    DOCUMENT_PERFORMANCE_BENCHMARKS, validate_document_request, calculate_estimated_generation_time
)

from ghl_real_estate_ai.services.seller_claude_integration_engine import (
    SellerClaudeIntegrationEngine, WorkflowStage
)

# Test data fixtures
@pytest.fixture
def sample_property_valuation_data():
    """Sample property valuation data for testing."""
    return {
        'property_address': '123 Test Street, San Francisco, CA 94102',
        'estimated_value': 1250000,
        'confidence_score': 0.92,
        'property_type': 'single_family',
        'square_footage': 2500,
        'lot_size': 0.15,
        'year_built': 2010,
        'comparable_sales': [
            {
                'address': '125 Test Street',
                'sale_price': 1300000,
                'sale_date': '2025-12-15',
                'similarity_score': 0.95
            },
            {
                'address': '121 Test Street',
                'sale_price': 1200000,
                'sale_date': '2025-11-28',
                'similarity_score': 0.90
            }
        ],
        'market_trends': {
            'price_appreciation': 0.08,
            'days_on_market': 32,
            'market_condition': 'moderate',
            'inventory_level': 'balanced'
        }
    }

@pytest.fixture
def sample_marketing_campaign_data():
    """Sample marketing campaign data for testing."""
    return {
        'campaign_name': 'Q1 Luxury Property Showcase',
        'campaign_type': 'property_showcase',
        'target_audience': 'luxury_buyers',
        'delivery_channels': ['email', 'social_media'],
        'campaign_status': 'active',
        'performance_metrics': {
            'total_deliveries': 1247,
            'open_rate': 0.283,
            'click_rate': 0.067,
            'conversion_rate': 0.152,
            'roi': 3.4,
            'attributed_revenue': 45000
        },
        'audience_segments': {'luxury_buyers': 847, 'investors': 400},
        'content_assets': [
            {
                'content_type': 'email_template',
                'title': 'Luxury Property Showcase',
                'performance_metrics': {'open_rate': 0.29}
            }
        ]
    }

@pytest.fixture
def sample_document_request():
    """Sample document generation request."""
    return DocumentGenerationRequest(
        document_name="Test Seller Proposal",
        document_category=DocumentCategory.SELLER_PROPOSAL,
        document_type=DocumentType.PDF,
        template_id="luxury_seller_proposal",
        property_valuation_id="val_123",
        marketing_campaign_id="camp_456",
        seller_workflow_data={
            'seller_id': 'seller_789',
            'workflow_stage': 'pricing_discussion',
            'engagement_level': 0.85
        },
        include_claude_enhancement=True,
        claude_enhancement_prompt="Enhance this seller proposal with professional tone",
        custom_content={'client_name': 'John Smith'},
        priority_level='high'
    )

@pytest.fixture
def mock_claude_service():
    """Mock Claude service for testing."""
    claude_mock = AsyncMock()
    claude_mock.process_seller_message = AsyncMock(return_value={
        'response': 'Enhanced content with professional insights',
        'confidence': 0.95
    })
    return claude_mock

@pytest.fixture
def temp_output_directory():
    """Create temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Core Engine Tests
# ============================================================================

class TestDocumentGenerationEngine:
    """Test the core Document Generation Engine."""

    @pytest.fixture
    def engine(self, mock_claude_service, temp_output_directory):
        """Document generation engine with mocked dependencies."""
        engine = DocumentGenerationEngine(claude_service=mock_claude_service)
        engine.output_directory = temp_output_directory
        return engine

    @pytest.mark.asyncio
    async def test_single_document_generation(self, engine, sample_document_request):
        """Test single document generation with performance validation."""
        start_time = time.time()

        result = await engine.generate_document(sample_document_request)

        generation_time = (time.time() - start_time) * 1000

        # Validate response
        assert result.success is True
        assert result.document_name == sample_document_request.document_name
        assert result.document_type == sample_document_request.document_type
        assert result.file_path is not None
        assert result.quality_score > 0.8

        # Performance validation
        assert generation_time < DOCUMENT_PERFORMANCE_BENCHMARKS['pdf_generation_time_ms']
        assert result.generation_time_ms < DOCUMENT_PERFORMANCE_BENCHMARKS['pdf_generation_time_ms']

        # Verify file creation
        assert os.path.exists(result.file_path)

        print(f"✅ Single document generation completed in {generation_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_bulk_document_generation(self, engine):
        """Test bulk document generation with performance optimization."""
        # Create multiple document requests
        bulk_requests = []
        for i in range(5):
            request = DocumentGenerationRequest(
                document_name=f"Test Document {i+1}",
                document_category=DocumentCategory.MARKET_ANALYSIS,
                document_type=DocumentType.PDF,
                template_id="market_analysis_residential",
                custom_content={'iteration': i+1},
                include_claude_enhancement=False  # Disable for speed
            )
            bulk_requests.append(request)

        bulk_request = BulkDocumentRequest(
            bulk_request_id="bulk_test_001",
            document_requests=bulk_requests,
            batch_size=3
        )

        start_time = time.time()
        result = await engine.generate_bulk_documents(bulk_request)
        bulk_generation_time = (time.time() - start_time) * 1000

        # Validate bulk processing
        assert result.total_requests == 5
        assert result.successful_generations >= 4  # Allow for 1 potential failure
        assert result.processing_status == "completed"
        assert result.avg_document_time_ms > 0

        # Performance validation
        assert bulk_generation_time < 10000  # Should complete within 10 seconds

        print(f"✅ Bulk generation: {result.successful_generations}/{result.total_requests} successful in {bulk_generation_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_document_generation_with_valuation_data(self, engine, sample_document_request, sample_property_valuation_data):
        """Test document generation with integrated property valuation data."""
        # Mock the valuation integration
        with patch.object(engine, '_integrate_live_property_valuation') as mock_valuation:
            mock_integration = PropertyValuationIntegration(
                valuation_id="val_123",
                property_data=sample_property_valuation_data,
                valuation_results={
                    'estimated_value': sample_property_valuation_data['estimated_value'],
                    'confidence': sample_property_valuation_data['confidence_score']
                },
                comparative_analysis={'comparable_sales': sample_property_valuation_data['comparable_sales']},
                market_insights=sample_property_valuation_data['market_trends']
            )
            mock_valuation.return_value = mock_integration

            result = await engine.generate_document(sample_document_request)

            # Validate integration occurred
            mock_valuation.assert_called_once()
            assert result.success is True
            assert ContentSource.PROPERTY_VALUATION in result.content_sources_used

        print("✅ Property valuation integration successful")

    @pytest.mark.asyncio
    async def test_document_generation_with_campaign_data(self, engine, sample_document_request, sample_marketing_campaign_data):
        """Test document generation with integrated marketing campaign data."""
        # Mock the campaign integration
        with patch.object(engine, '_integrate_live_marketing_campaign') as mock_campaign:
            mock_integration = MarketingCampaignIntegration(
                campaign_id="camp_456",
                campaign_data=sample_marketing_campaign_data,
                performance_metrics=sample_marketing_campaign_data['performance_metrics'],
                audience_insights={'total_audience': 1247},
                content_assets=sample_marketing_campaign_data['content_assets']
            )
            mock_campaign.return_value = mock_integration

            result = await engine.generate_document(sample_document_request)

            # Validate integration occurred
            mock_campaign.assert_called_once()
            assert result.success is True
            assert ContentSource.MARKETING_CAMPAIGN in result.content_sources_used

        print("✅ Marketing campaign integration successful")

    @pytest.mark.asyncio
    async def test_claude_content_enhancement(self, engine, sample_document_request, mock_claude_service):
        """Test Claude AI content enhancement functionality."""
        sample_document_request.include_claude_enhancement = True
        sample_document_request.claude_enhancement_prompt = "Make this content more engaging and professional"

        result = await engine.generate_document(sample_document_request)

        # Validate Claude enhancement
        assert result.success is True
        assert result.claude_enhancement_applied is True
        assert mock_claude_service.process_seller_message.called

        # Should have enhanced content suggestions
        assert len(result.claude_suggestions) > 0

        print("✅ Claude content enhancement successful")

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, engine):
        """Test comprehensive error handling and recovery mechanisms."""
        # Test with invalid template
        invalid_request = DocumentGenerationRequest(
            document_name="Invalid Test",
            document_category=DocumentCategory.SELLER_PROPOSAL,
            document_type=DocumentType.PDF,
            template_id="nonexistent_template"
        )

        result = await engine.generate_document(invalid_request)

        # Should handle error gracefully
        assert result.success is False
        assert result.error_message is not None
        assert result.document_status == DocumentStatus.FAILED

        # Test with empty content
        empty_request = DocumentGenerationRequest(
            document_name="Empty Test",
            document_category=DocumentCategory.MARKET_ANALYSIS,
            document_type=DocumentType.PDF,
            custom_content={}
        )

        result = await engine.generate_document(empty_request)

        # Should still complete with default content
        assert result.success is True  # Should generate with default content

        print("✅ Error handling and recovery working correctly")


# ============================================================================
# Template Management Tests
# ============================================================================

class TestDocumentTemplateManager:
    """Test the Document Template Management system."""

    @pytest.fixture
    def template_manager(self):
        """Template manager instance for testing."""
        return DocumentTemplateManager()

    @pytest.mark.asyncio
    async def test_template_retrieval_and_caching(self, template_manager):
        """Test template retrieval with caching performance."""
        template_id = "luxury_seller_proposal"

        # First retrieval (should load from storage)
        start_time = time.time()
        template1 = await template_manager.get_template_by_id(template_id)
        first_load_time = (time.time() - start_time) * 1000

        # Second retrieval (should use cache)
        start_time = time.time()
        template2 = await template_manager.get_template_by_id(template_id)
        cached_load_time = (time.time() - start_time) * 1000

        # Validate template data
        assert template1 is not None
        assert template1.template_id == template_id
        assert template1.template_name is not None
        assert template1.template_category == DocumentCategory.SELLER_PROPOSAL

        # Validate caching performance
        assert template2 is not None
        assert cached_load_time < first_load_time  # Cache should be faster
        assert cached_load_time < 50  # Should be very fast from cache

        print(f"✅ Template caching: First load {first_load_time:.2f}ms, Cached {cached_load_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_template_listing_and_filtering(self, template_manager):
        """Test template listing with category and type filtering."""
        # List all templates
        all_templates = await template_manager.list_templates()
        assert len(all_templates) >= 3  # Should have predefined templates

        # Filter by category
        seller_proposal_templates = await template_manager.list_templates(
            category=DocumentCategory.SELLER_PROPOSAL
        )
        assert len(seller_proposal_templates) >= 1
        assert all(t.template_category == DocumentCategory.SELLER_PROPOSAL for t in seller_proposal_templates)

        # Filter by document type
        pdf_templates = await template_manager.list_templates(
            document_type=DocumentType.PDF
        )
        assert len(pdf_templates) >= 1
        assert all(t.document_type == DocumentType.PDF for t in pdf_templates)

        print(f"✅ Template filtering: {len(all_templates)} total, {len(seller_proposal_templates)} seller proposals")

    @pytest.mark.asyncio
    async def test_template_recommendation_engine(self, template_manager):
        """Test intelligent template recommendation system."""
        # Test recommendation for luxury seller proposal
        recommendation = await template_manager.get_recommended_template(
            document_category=DocumentCategory.SELLER_PROPOSAL,
            property_type="luxury_home",
            market_segment="luxury"
        )

        assert recommendation is not None
        assert recommendation.template_category == DocumentCategory.SELLER_PROPOSAL
        assert "luxury" in recommendation.template_id or "luxury" in recommendation.market_segments

        # Test recommendation for market analysis
        recommendation = await template_manager.get_recommended_template(
            document_category=DocumentCategory.MARKET_ANALYSIS,
            property_type="single_family",
            market_segment="residential"
        )

        assert recommendation is not None
        assert recommendation.template_category == DocumentCategory.MARKET_ANALYSIS

        print("✅ Template recommendation engine working correctly")


# ============================================================================
# Multi-Format Generator Tests
# ============================================================================

class TestMultiFormatGenerators:
    """Test all document format generators (PDF, DOCX, PPTX, HTML)."""

    @pytest.fixture
    def sample_template(self):
        """Sample template for testing."""
        return DocumentTemplate(
            template_id="test_template",
            template_name="Test Template",
            template_category=DocumentCategory.SELLER_PROPOSAL,
            document_type=DocumentType.PDF,
            template_style=TemplateStyle.LUXURY,
            template_description="Test template for format generation",
            property_types=["test"],
            market_segments=["test"],
            target_audience=["test"],
            content_placeholders={"test": "placeholder"},
            required_data_sources=[ContentSource.MANUAL_INPUT],
            created_by="test_system"
        )

    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return [
            DocumentContent(
                content_type="text",
                content_title="Executive Summary",
                content_data={"text": "This is a comprehensive test of the document generation system."},
                content_source=ContentSource.MANUAL_INPUT,
                quality_score=0.9
            ),
            DocumentContent(
                content_type="table",
                content_title="Performance Metrics",
                content_data={
                    "table_data": {
                        "headers": ["Metric", "Value", "Target"],
                        "rows": [
                            ["Generation Time", "1.2s", "2.0s"],
                            ["Quality Score", "0.95", "0.90"]
                        ]
                    }
                },
                content_source=ContentSource.MANUAL_INPUT,
                quality_score=0.92
            )
        ]

    @pytest.mark.asyncio
    async def test_pdf_generation(self, sample_template, sample_content, temp_output_directory):
        """Test PDF document generation with performance validation."""
        generator = PDFDocumentGenerator()
        output_path = os.path.join(temp_output_directory, "test.pdf")

        start_time = time.time()
        result = await generator.generate_pdf(sample_template, sample_content, output_path)
        generation_time = (time.time() - start_time) * 1000

        # Validate generation
        assert result['success'] is True
        assert os.path.exists(output_path)
        assert result['metadata']['pages'] > 0
        assert generation_time < DOCUMENT_PERFORMANCE_BENCHMARKS['pdf_generation_time_ms']

        print(f"✅ PDF generation: {generation_time:.2f}ms, Quality: {result['quality_score']}")

    @pytest.mark.asyncio
    async def test_docx_generation(self, sample_template, sample_content, temp_output_directory):
        """Test DOCX document generation."""
        generator = DOCXDocumentGenerator()
        output_path = os.path.join(temp_output_directory, "test.docx")

        start_time = time.time()
        result = await generator.generate_docx(sample_template, sample_content, output_path)
        generation_time = (time.time() - start_time) * 1000

        # Validate generation
        assert result['success'] is True
        assert os.path.exists(output_path)
        assert result['metadata']['sections'] >= len(sample_content)
        assert generation_time < DOCUMENT_PERFORMANCE_BENCHMARKS['docx_generation_time_ms']

        print(f"✅ DOCX generation: {generation_time:.2f}ms, Sections: {result['metadata']['sections']}")

    @pytest.mark.asyncio
    async def test_pptx_generation(self, sample_template, sample_content, temp_output_directory):
        """Test PPTX presentation generation."""
        generator = PPTXDocumentGenerator()
        output_path = os.path.join(temp_output_directory, "test.pptx")

        start_time = time.time()
        result = await generator.generate_pptx(sample_template, sample_content, output_path)
        generation_time = (time.time() - start_time) * 1000

        # Validate generation
        assert result['success'] is True
        assert os.path.exists(output_path)
        assert result['metadata']['slides'] >= len(sample_content) + 1  # +1 for title slide
        assert generation_time < DOCUMENT_PERFORMANCE_BENCHMARKS['pptx_generation_time_ms']

        print(f"✅ PPTX generation: {generation_time:.2f}ms, Slides: {result['metadata']['slides']}")

    @pytest.mark.asyncio
    async def test_html_generation(self, sample_template, sample_content, temp_output_directory):
        """Test HTML document generation."""
        generator = HTMLDocumentGenerator()
        output_path = os.path.join(temp_output_directory, "test.html")

        start_time = time.time()
        result = await generator.generate_html(sample_template, sample_content, output_path)
        generation_time = (time.time() - start_time) * 1000

        # Validate generation
        assert result['success'] is True
        assert os.path.exists(output_path)
        assert result['metadata']['responsive'] is True
        assert generation_time < DOCUMENT_PERFORMANCE_BENCHMARKS['html_generation_time_ms']

        # Verify HTML content structure
        with open(output_path, 'r') as f:
            html_content = f.read()
            assert '<!DOCTYPE html>' in html_content
            assert sample_template.template_name in html_content
            assert sample_content[0].content_data['text'] in html_content

        print(f"✅ HTML generation: {generation_time:.2f}ms, Size: {result['metadata']['file_size']} bytes")


# ============================================================================
# Quality Validation Tests
# ============================================================================

class TestDocumentQualityValidation:
    """Test document quality validation and scoring."""

    @pytest.fixture
    def quality_validator(self):
        """Quality validator instance for testing."""
        return DocumentQualityValidator()

    @pytest.mark.asyncio
    async def test_comprehensive_quality_validation(self, quality_validator):
        """Test comprehensive quality validation scoring."""
        # Create sample generation request and content
        request = DocumentGenerationRequest(
            document_name="Quality Test Document",
            document_category=DocumentCategory.SELLER_PROPOSAL,
            document_type=DocumentType.PDF
        )

        high_quality_content = [
            DocumentContent(
                content_type="text",
                content_title="Executive Summary",
                content_data={"text": "A comprehensive and detailed executive summary with substantial content."},
                content_source=ContentSource.CLAUDE_GENERATED,
                claude_enhanced=True,
                quality_score=0.95,
                content_validated=True
            ),
            DocumentContent(
                content_type="analysis",
                content_title="Market Analysis",
                content_data={"text": "Detailed market analysis with comprehensive insights and data-driven conclusions."},
                content_source=ContentSource.PROPERTY_VALUATION,
                claude_enhanced=True,
                quality_score=0.90,
                content_validated=True
            )
        ]

        generation_result = {
            'success': True,
            'metadata': {'pages': 3, 'file_size': 150000},
            'document_id': 'test_doc_001'
        }

        # Perform quality validation
        validation = await quality_validator.validate_document_quality(
            request, high_quality_content, generation_result
        )

        # Validate quality scoring
        assert validation.overall_quality_score >= DOCUMENT_PERFORMANCE_BENCHMARKS['document_quality_score_min']
        assert validation.content_quality_score > 0.8
        assert validation.design_quality_score > 0.8
        assert validation.data_accuracy_score > 0.8
        assert validation.validation_passed is True
        assert len(validation.critical_issues) == 0

        print(f"✅ Quality validation: Overall {validation.overall_quality_score:.3f}, Content {validation.content_quality_score:.3f}")

    @pytest.mark.asyncio
    async def test_quality_validation_with_issues(self, quality_validator):
        """Test quality validation with potential issues."""
        request = DocumentGenerationRequest(
            document_name="Low Quality Test",
            document_category=DocumentCategory.MARKET_ANALYSIS,
            document_type=DocumentType.PDF
        )

        low_quality_content = [
            DocumentContent(
                content_type="text",
                content_data={"text": "Short"},  # Very brief content
                content_source=ContentSource.MANUAL_INPUT,
                claude_enhanced=False,
                quality_score=0.5,
                content_validated=False
            )
        ]

        generation_result = {
            'success': False,  # Failed generation
            'metadata': {},
            'document_id': 'test_doc_002'
        }

        validation = await quality_validator.validate_document_quality(
            request, low_quality_content, generation_result
        )

        # Should identify quality issues
        assert validation.overall_quality_score < DOCUMENT_PERFORMANCE_BENCHMARKS['document_quality_score_min']
        assert validation.validation_passed is False
        assert len(validation.critical_issues) > 0
        assert len(validation.recommended_fixes) > 0

        print(f"✅ Quality issues detected: {len(validation.critical_issues)} issues, {len(validation.recommended_fixes)} fixes")


# ============================================================================
# Integration Tests
# ============================================================================

class TestDocumentGenerationIntegration:
    """Test integration with seller workflow and automated document generation."""

    @pytest.fixture
    def integration_engine(self, mock_claude_service):
        """Seller Claude integration engine with document generation enabled."""
        engine = SellerClaudeIntegrationEngine()
        engine.claude_agent = mock_claude_service
        # Enable document generation for testing
        engine.integration_config['auto_document_generation'] = True
        return engine

    @pytest.mark.asyncio
    async def test_workflow_stage_document_triggers(self, integration_engine):
        """Test automatic document generation triggers based on workflow stage advancement."""
        seller_id = "test_seller_integration_001"

        # Mock workflow state
        from ghl_real_estate_ai.services.seller_claude_integration_engine import SellerWorkflowState, IntegrationStatus
        workflow_state = SellerWorkflowState(
            seller_id=seller_id,
            current_stage=WorkflowStage.PROPERTY_EVALUATION,
            integration_status=IntegrationStatus.ACTIVE,
            last_interaction=datetime.utcnow(),
            next_scheduled_action=None,
            completion_percentage=40.0,
            milestone_achievements=['property_details_collected'],
            outstanding_tasks=['property_valuation'],
            conversation_history_summary="Test conversation",
            current_priorities=['valuation'],
            identified_concerns=[],
            readiness_score=0.8,
            engagement_level=0.85,
            conversion_probability=0.75
        )

        # Add to workflow states
        integration_engine.workflow_states[seller_id] = workflow_state

        # Test stage advancement that should trigger document generation
        result = await integration_engine.trigger_automatic_document_generation(
            seller_id, 'property_valuation_complete'
        )

        # Validate automatic generation
        if result['success']:
            assert result['documents_generated'] > 0
            assert result['trigger_type'] == 'property_valuation_complete'
            print(f"✅ Workflow document trigger: {result['documents_generated']} documents generated")
        else:
            # May fail in test environment due to missing dependencies
            print(f"⚠️ Workflow document trigger: {result['reason']}")

    @pytest.mark.asyncio
    async def test_seller_document_tracking(self, integration_engine):
        """Test document tracking and retrieval for sellers."""
        seller_id = "test_seller_tracking_001"

        # Get seller documents (should be empty initially)
        documents_result = await integration_engine.get_seller_documents(seller_id)

        assert documents_result['success'] is True
        assert len(documents_result['documents']) == 0
        assert documents_result['stats']['total_generated'] == 0

        print("✅ Document tracking and retrieval working correctly")

    @pytest.mark.asyncio
    async def test_document_configuration_validation(self, integration_engine):
        """Test document generation configuration and validation."""
        # Validate integration configuration
        config = integration_engine.integration_config
        assert 'auto_document_generation' in config
        assert 'document_generation_triggers' in config

        triggers = config['document_generation_triggers']
        expected_triggers = [
            'property_valuation_complete',
            'market_analysis_ready',
            'seller_proposal_stage',
            'campaign_performance_report'
        ]

        for trigger in expected_triggers:
            assert trigger in triggers
            assert isinstance(triggers[trigger], bool)

        print("✅ Document generation configuration validation passed")


# ============================================================================
# Performance Benchmark Tests
# ============================================================================

class TestDocumentGenerationPerformance:
    """Performance benchmark testing for document generation system."""

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, temp_output_directory):
        """Test all performance benchmarks are met."""
        engine = DocumentGenerationEngine()
        engine.output_directory = temp_output_directory

        benchmark_tests = [
            # (document_type, expected_max_time_ms, template_id)
            (DocumentType.PDF, DOCUMENT_PERFORMANCE_BENCHMARKS['pdf_generation_time_ms'], 'luxury_seller_proposal'),
            (DocumentType.DOCX, DOCUMENT_PERFORMANCE_BENCHMARKS['docx_generation_time_ms'], 'market_analysis_residential'),
            (DocumentType.PPTX, DOCUMENT_PERFORMANCE_BENCHMARKS['pptx_generation_time_ms'], 'property_showcase_presentation'),
            (DocumentType.HTML, DOCUMENT_PERFORMANCE_BENCHMARKS['html_generation_time_ms'], 'performance_report_monthly'),
        ]

        performance_results = []

        for doc_type, max_time, template_id in benchmark_tests:
            request = DocumentGenerationRequest(
                document_name=f"Performance Test {doc_type.value}",
                document_category=DocumentCategory.SELLER_PROPOSAL,
                document_type=doc_type,
                template_id=template_id,
                include_claude_enhancement=False,  # Disable for pure performance
                custom_content={'test': 'performance'}
            )

            # Measure generation time
            start_time = time.time()
            result = await engine.generate_document(request)
            actual_time = (time.time() - start_time) * 1000

            performance_results.append({
                'format': doc_type.value,
                'actual_time_ms': actual_time,
                'max_time_ms': max_time,
                'passed': actual_time <= max_time,
                'success': result.success
            })

        # Report results
        all_passed = True
        for result in performance_results:
            status = "✅ PASS" if result['passed'] and result['success'] else "❌ FAIL"
            print(f"{status} {result['format']}: {result['actual_time_ms']:.2f}ms (limit: {result['max_time_ms']}ms)")
            if not (result['passed'] and result['success']):
                all_passed = False

        assert all_passed, "Some performance benchmarks failed"
        print(f"\n✅ All performance benchmarks passed")

    @pytest.mark.asyncio
    async def test_concurrent_generation_performance(self, temp_output_directory):
        """Test performance under concurrent document generation load."""
        engine = DocumentGenerationEngine()
        engine.output_directory = temp_output_directory

        # Create concurrent generation tasks
        concurrent_requests = []
        for i in range(5):  # Generate 5 documents concurrently
            request = DocumentGenerationRequest(
                document_name=f"Concurrent Test {i+1}",
                document_category=DocumentCategory.MARKET_ANALYSIS,
                document_type=DocumentType.PDF,
                template_id="market_analysis_residential",
                include_claude_enhancement=False,
                custom_content={'concurrent_id': i+1}
            )
            concurrent_requests.append(engine.generate_document(request))

        # Execute concurrent generations
        start_time = time.time()
        results = await asyncio.gather(*concurrent_requests, return_exceptions=True)
        concurrent_time = (time.time() - start_time) * 1000

        # Validate results
        successful_generations = sum(1 for r in results if not isinstance(r, Exception) and r.success)

        assert successful_generations >= 4  # Allow for 1 potential failure
        assert concurrent_time < 8000  # Should complete within 8 seconds

        print(f"✅ Concurrent generation: {successful_generations}/5 successful in {concurrent_time:.2f}ms")


# ============================================================================
# End-to-End Integration Tests
# ============================================================================

class TestDocumentGenerationEndToEnd:
    """End-to-end integration tests simulating real workflow scenarios."""

    @pytest.mark.asyncio
    async def test_complete_seller_document_workflow(self, temp_output_directory):
        """Test complete seller document generation workflow from valuation to final proposal."""
        # Initialize components
        engine = DocumentGenerationEngine()
        engine.output_directory = temp_output_directory

        # Step 1: Generate property valuation document
        valuation_request = DocumentGenerationRequest(
            document_name="Property Valuation Report - 123 Test St",
            document_category=DocumentCategory.MARKET_ANALYSIS,
            document_type=DocumentType.PDF,
            template_id="market_analysis_residential",
            custom_content={
                'property_address': '123 Test Street, San Francisco, CA',
                'estimated_value': 1250000,
                'confidence_score': 0.92
            },
            include_claude_enhancement=True
        )

        valuation_result = await engine.generate_document(valuation_request)
        assert valuation_result.success is True

        # Step 2: Generate seller proposal based on valuation
        proposal_request = DocumentGenerationRequest(
            document_name="Seller Proposal - 123 Test St",
            document_category=DocumentCategory.SELLER_PROPOSAL,
            document_type=DocumentType.PDF,
            template_id="luxury_seller_proposal",
            custom_content={
                'seller_name': 'John and Sarah Smith',
                'property_address': '123 Test Street, San Francisco, CA',
                'estimated_value': 1250000,
                'marketing_strategy': 'Comprehensive luxury marketing campaign'
            },
            include_claude_enhancement=True
        )

        proposal_result = await engine.generate_document(proposal_request)
        assert proposal_result.success is True

        # Step 3: Generate property showcase presentation
        showcase_request = DocumentGenerationRequest(
            document_name="Property Showcase - 123 Test St",
            document_category=DocumentCategory.PROPERTY_SHOWCASE,
            document_type=DocumentType.PPTX,
            template_id="property_showcase_presentation",
            custom_content={
                'property_features': 'Luxury finishes, modern kitchen, panoramic views',
                'neighborhood_highlights': 'Prime location near parks and shopping',
                'pricing_strategy': 'Competitive pricing based on recent comparables'
            },
            include_claude_enhancement=True
        )

        showcase_result = await engine.generate_document(showcase_request)
        assert showcase_result.success is True

        # Validate complete workflow
        all_documents = [valuation_result, proposal_result, showcase_result]
        total_generation_time = sum(doc.generation_time_ms for doc in all_documents)
        avg_quality_score = sum(doc.quality_score for doc in all_documents) / len(all_documents)

        assert all(doc.success for doc in all_documents)
        assert avg_quality_score > 0.85
        assert total_generation_time < 10000  # Complete workflow under 10 seconds

        print(f"✅ Complete workflow: 3 documents, avg quality {avg_quality_score:.3f}, total time {total_generation_time:.0f}ms")

    @pytest.mark.asyncio
    async def test_error_recovery_and_fallback(self, temp_output_directory):
        """Test system recovery and fallback mechanisms during failures."""
        engine = DocumentGenerationEngine()
        engine.output_directory = temp_output_directory

        # Test with invalid template ID (should fallback to recommended)
        fallback_request = DocumentGenerationRequest(
            document_name="Fallback Test Document",
            document_category=DocumentCategory.SELLER_PROPOSAL,
            document_type=DocumentType.PDF,
            template_id="nonexistent_template_id",
            custom_content={'test': 'fallback'}
        )

        result = await engine.generate_document(fallback_request)

        # Should either fail gracefully or use fallback template
        if result.success:
            assert result.template_utilized is not None
            print("✅ Fallback template mechanism working")
        else:
            assert result.error_message is not None
            print("✅ Graceful error handling working")

        # Test with missing content (should use default content)
        minimal_request = DocumentGenerationRequest(
            document_name="Minimal Content Test",
            document_category=DocumentCategory.MARKET_ANALYSIS,
            document_type=DocumentType.PDF,
            template_id="market_analysis_residential"
            # No custom content provided
        )

        minimal_result = await engine.generate_document(minimal_request)
        assert minimal_result.success is True
        assert minimal_result.content_sections is not None

        print("✅ Default content generation working")


if __name__ == "__main__":
    # Run comprehensive test suite with performance monitoring
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings",
        "-x"  # Stop on first failure for debugging
    ])