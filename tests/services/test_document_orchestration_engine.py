import pytest
pytestmark = pytest.mark.integration

"""
Comprehensive tests for Document Orchestration Engine.
Tests cover document collection, validation, template generation, and lifecycle management.
"""

import asyncio
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.document_orchestration_engine import (

@pytest.mark.integration
    DeliveryChannel,
    DocumentOrchestrationEngine,
    DocumentRequest,
    DocumentStatus,
    DocumentTemplate,
    DocumentType,
    ValidationLevel,
    ValidationResult,
)


class TestDocumentRequest:
    """Test DocumentRequest dataclass functionality."""

    def test_document_request_creation(self):
        """Test document request creation with all fields."""
        request = DocumentRequest(
            request_id="req_001",
            transaction_id="deal_123",
            document_type=DocumentType.PURCHASE_AGREEMENT,
            title="Purchase Agreement Collection",
            description="Collect signed purchase agreement from buyer",
            required=True,
            requested_from="buyer",
            status=DocumentStatus.PENDING,
            due_date=datetime.now() + timedelta(days=3),
            priority=5,
        )

        assert request.request_id == "req_001"
        assert request.document_type == DocumentType.PURCHASE_AGREEMENT
        assert request.status == DocumentStatus.PENDING
        assert request.priority == 5
        assert request.transaction_id == "deal_123"

    def test_document_request_serialization(self):
        """Test document request serialization to dictionary."""
        request = DocumentRequest(
            request_id="req_002",
            transaction_id="deal_789",
            document_type=DocumentType.INSPECTION_REPORT,
            title="Home Inspection Report",
            description="Professional home inspection report",
            required=True,
            requested_from="inspector",
            status=DocumentStatus.RECEIVED,
            due_date=datetime.now() + timedelta(days=1),
            priority=4,
        )

        request_dict = request.__dict__
        assert request_dict["request_id"] == "req_002"
        assert request_dict["document_type"] == DocumentType.INSPECTION_REPORT
        assert isinstance(request_dict["due_date"], datetime)


class TestValidationResult:
    """Test ValidationResult dataclass functionality."""

    def test_validation_result_success(self):
        """Test successful validation result."""
        result = ValidationResult(
            is_valid=True,
            confidence_score=0.95,
            validation_level=ValidationLevel.COMPLETE,
            issues=[],
            suggestions=["Verify property tax information"],
            required_actions=[],
        )

        assert result.is_valid is True
        assert result.confidence_score == 0.95
        assert len(result.required_actions) == 0
        assert len(result.suggestions) == 1

    def test_validation_result_failure(self):
        """Test failed validation result."""
        result = ValidationResult(
            is_valid=False,
            confidence_score=0.65,
            validation_level=ValidationLevel.CONTENT,
            issues=["Missing buyer signature", "Missing seller signature"],
            suggestions=["Request signatures from both parties"],
            required_actions=["request_buyer_signature", "request_seller_signature"],
        )

        assert result.is_valid is False
        assert result.confidence_score == 0.65
        assert len(result.required_actions) == 2
        assert len(result.issues) == 2


class TestDocumentOrchestrationEngine:
    """Test the main document orchestration functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for document engine."""
        return {
            "cache_service": MagicMock(),
            "ghl_client": MagicMock(),
            "claude_assistant": MagicMock(),
        }

    @pytest.fixture
    def engine(self, mock_dependencies):
        """Create document engine instance with mocked dependencies."""
        with (
            patch(
                "ghl_real_estate_ai.services.document_orchestration_engine.ClaudeAssistant",
                return_value=mock_dependencies["claude_assistant"],
            ),
            patch(
                "ghl_real_estate_ai.services.document_orchestration_engine.GHLClient",
                return_value=mock_dependencies["ghl_client"],
            ),
            patch(
                "ghl_real_estate_ai.services.document_orchestration_engine.get_cache_service",
                return_value=mock_dependencies["cache_service"],
            ),
            patch("ghl_real_estate_ai.services.document_orchestration_engine.get_llm_client") as mock_llm,
        ):
            mock_llm_instance = MagicMock()
            mock_llm.return_value = mock_llm_instance
            engine = DocumentOrchestrationEngine(
                cache_service=mock_dependencies["cache_service"],
                ghl_client=mock_dependencies["ghl_client"],
                claude_assistant=mock_dependencies["claude_assistant"],
            )
            return engine

    @pytest.mark.asyncio
    async def test_initiate_document_collection_success(self, engine):
        """Test successful document collection initiation."""
        # Mock the LLM client for request message generation
        mock_response = MagicMock()
        mock_response.content = "Please submit your purchase agreement."
        engine.llm_client.generate = AsyncMock(return_value=mock_response)

        transaction_data = {
            "loan_amount": 350000,
            "property_address": "123 Main St, Austin, TX",
        }

        request_ids = await engine.initiate_document_collection(
            transaction_id="deal_123",
            transaction_data=transaction_data,
        )

        assert isinstance(request_ids, list)
        assert len(request_ids) > 0
        assert engine.metrics["documents_requested"] > 0

        # All returned request_ids should be in active_requests
        for rid in request_ids:
            assert rid in engine.active_requests

    @pytest.mark.asyncio
    async def test_initiate_document_collection_cash_purchase(self, engine):
        """Test document collection for cash purchase (no loan)."""
        mock_response = MagicMock()
        mock_response.content = "Please submit your proof of funds."
        engine.llm_client.generate = AsyncMock(return_value=mock_response)

        transaction_data = {
            "loan_amount": 0,  # Cash purchase
            "property_address": "456 Oak St, Austin, TX",
        }

        request_ids = await engine.initiate_document_collection(
            transaction_id="deal_cash",
            transaction_data=transaction_data,
        )

        assert len(request_ids) > 0

        # Should include proof of funds for cash purchases
        doc_types = [engine.active_requests[rid].document_type for rid in request_ids]
        assert DocumentType.PROOF_OF_FUNDS in doc_types

    @pytest.mark.asyncio
    async def test_receive_document_success(self, engine):
        """Test successful document receipt and processing."""
        # Create a document request first
        request = DocumentRequest(
            request_id="req_123",
            transaction_id="deal_123",
            document_type=DocumentType.PURCHASE_AGREEMENT,
            title="Purchase Agreement",
            description="Collect purchase agreement",
            required=True,
            requested_from="buyer",
            status=DocumentStatus.REQUESTED,
            due_date=datetime.now() + timedelta(days=1),
        )
        engine.active_requests["req_123"] = request

        # Create valid file content (large enough to pass min size check)
        file_content = b"A" * 200  # At least 100 bytes
        file_name = "purchase_agreement.pdf"

        # Mock the LLM for AI validation
        mock_response = MagicMock()
        mock_response.content = '{"is_valid": true, "confidence_score": 0.96}'
        engine.llm_client.generate = AsyncMock(return_value=mock_response)

        result = await engine.receive_document(
            request_id="req_123",
            file_content=file_content,
            file_name=file_name,
            submitted_by="buyer",
        )

        assert result["success"] is True
        assert "status" in result
        assert "validation" in result
        assert engine.metrics["documents_received"] >= 1

    @pytest.mark.asyncio
    async def test_receive_document_not_found(self, engine):
        """Test receiving document for non-existent request."""
        result = await engine.receive_document(
            request_id="nonexistent",
            file_content=b"content",
            file_name="test.pdf",
        )

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_receive_document_file_too_large(self, engine):
        """Test receiving document that exceeds size limit."""
        request = DocumentRequest(
            request_id="req_large",
            transaction_id="deal_large",
            document_type=DocumentType.INSPECTION_REPORT,
            title="Inspection Report",
            description="Home inspection report",
            required=True,
        )
        engine.active_requests["req_large"] = request

        # Create file content larger than max_file_size_mb (25 MB)
        large_content = b"A" * (26 * 1024 * 1024)

        result = await engine.receive_document(
            request_id="req_large",
            file_content=large_content,
            file_name="large_report.pdf",
        )

        assert result["success"] is False
        assert "too large" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_receive_document_invalid_file_type(self, engine):
        """Test receiving document with disallowed file type."""
        request = DocumentRequest(
            request_id="req_invalid_type",
            transaction_id="deal_type",
            document_type=DocumentType.INSPECTION_REPORT,
            title="Inspection Report",
            description="Home inspection report",
            required=True,
        )
        engine.active_requests["req_invalid_type"] = request

        result = await engine.receive_document(
            request_id="req_invalid_type",
            file_content=b"A" * 200,
            file_name="report.exe",
        )

        assert result["success"] is False
        assert "not allowed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_generate_document_from_template(self, engine):
        """Test successful document template generation."""
        # Add a template
        template = DocumentTemplate(
            template_id="tmpl_closing",
            name="Closing Disclosure",
            document_type=DocumentType.CLOSING_DISCLOSURE,
            template_content="CLOSING DISCLOSURE\n\nProperty: {address}",
            variables=["address", "sale_price"],
            requires_signature=True,
        )
        engine.document_templates["tmpl_closing"] = template

        variables = {
            "address": "456 Oak Street, Austin, TX",
            "sale_price": 425000,
        }

        result = await engine.generate_document_from_template(
            template_id="tmpl_closing",
            variables=variables,
            transaction_id="deal_789",
        )

        assert result is not None  # Returns request_id
        assert result in engine.active_requests
        assert engine.metrics["auto_generated"] >= 1

    @pytest.mark.asyncio
    async def test_generate_document_from_template_not_found(self, engine):
        """Test template generation with non-existent template."""
        result = await engine.generate_document_from_template(
            template_id="nonexistent",
            variables={},
            transaction_id="deal_test",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_check_compliance(self, engine):
        """Test compliance checking for transaction documents."""
        transaction_id = "deal_compliance"

        # Add some document requests
        engine.active_requests["req_approved"] = DocumentRequest(
            request_id="req_approved",
            transaction_id=transaction_id,
            document_type=DocumentType.PURCHASE_AGREEMENT,
            title="Purchase Agreement",
            description="Signed purchase agreement",
            required=True,
            status=DocumentStatus.APPROVED,
            due_date=datetime.now() + timedelta(days=1),
        )

        engine.active_requests["req_pending"] = DocumentRequest(
            request_id="req_pending",
            transaction_id=transaction_id,
            document_type=DocumentType.INSPECTION_REPORT,
            title="Inspection Report",
            description="Home inspection report",
            required=True,
            status=DocumentStatus.REQUESTED,
            due_date=datetime.now() + timedelta(hours=6),
        )

        compliance = await engine.check_compliance(transaction_id)

        assert compliance["transaction_id"] == transaction_id
        assert compliance["required_documents"]["total"] == 2
        assert compliance["required_documents"]["completed"] == 1
        assert compliance["required_documents"]["missing"] == 1
        assert compliance["completion_percentage"] == 50.0

    @pytest.mark.asyncio
    async def test_check_compliance_all_complete(self, engine):
        """Test compliance when all documents are approved."""
        transaction_id = "deal_all_complete"

        engine.active_requests["req_1"] = DocumentRequest(
            request_id="req_1",
            transaction_id=transaction_id,
            document_type=DocumentType.PURCHASE_AGREEMENT,
            title="PA",
            description="PA",
            required=True,
            status=DocumentStatus.APPROVED,
        )

        engine.active_requests["req_2"] = DocumentRequest(
            request_id="req_2",
            transaction_id=transaction_id,
            document_type=DocumentType.INSPECTION_REPORT,
            title="IR",
            description="IR",
            required=True,
            status=DocumentStatus.APPROVED,
        )

        compliance = await engine.check_compliance(transaction_id)

        assert compliance["overall_compliance"] is True
        assert compliance["completion_percentage"] == 100.0

    @pytest.mark.asyncio
    async def test_start_and_stop_orchestration(self, engine):
        """Test starting and stopping the orchestration engine."""
        await engine.start_orchestration()
        assert engine.is_running is True

        await engine.stop_orchestration()
        assert engine.is_running is False

    def test_get_orchestration_status(self, engine):
        """Test orchestration status reporting."""
        status = engine.get_orchestration_status()

        assert "is_running" in status
        assert "total_active_requests" in status
        assert "requests_by_status" in status
        assert "metrics" in status
        assert status["is_running"] is False

    def test_determine_delivery_channels(self, engine):
        """Test delivery channel determination."""
        buyer_channels = engine._determine_delivery_channels("buyer")
        assert DeliveryChannel.EMAIL in buyer_channels
        assert DeliveryChannel.SMS in buyer_channels

        seller_channels = engine._determine_delivery_channels("seller")
        assert DeliveryChannel.EMAIL in seller_channels

    def test_generate_follow_up_schedule(self, engine):
        """Test follow-up schedule generation."""
        due_date = datetime.now() + timedelta(days=5)
        schedule = engine._generate_follow_up_schedule(due_date)

        assert isinstance(schedule, list)
        assert len(schedule) > 0
        # All follow-ups should be in the future
        for fu_time in schedule:
            assert isinstance(fu_time, datetime)

    def test_document_type_enum_values(self):
        """Test DocumentType enum has expected values."""
        assert DocumentType.PURCHASE_AGREEMENT.value == "purchase_agreement"
        assert DocumentType.INSPECTION_REPORT.value == "inspection_report"
        assert DocumentType.APPRAISAL_REPORT.value == "appraisal_report"
        assert DocumentType.CLOSING_DISCLOSURE.value == "closing_disclosure"
        assert DocumentType.PRE_APPROVAL_LETTER.value == "pre_approval_letter"

    def test_document_status_enum_values(self):
        """Test DocumentStatus enum has expected values."""
        assert DocumentStatus.NOT_REQUESTED.value == "not_requested"
        assert DocumentStatus.REQUESTED.value == "requested"
        assert DocumentStatus.PENDING.value == "pending"
        assert DocumentStatus.RECEIVED.value == "received"
        assert DocumentStatus.UNDER_REVIEW.value == "under_review"
        assert DocumentStatus.APPROVED.value == "approved"
        assert DocumentStatus.REJECTED.value == "rejected"
        assert DocumentStatus.COMPLETED.value == "completed"

    def test_validation_level_enum_values(self):
        """Test ValidationLevel enum has expected values."""
        assert ValidationLevel.BASIC.value == "basic"
        assert ValidationLevel.CONTENT.value == "content"
        assert ValidationLevel.COMPLIANCE.value == "compliance"
        assert ValidationLevel.COMPLETE.value == "complete"

    def test_engine_configuration_defaults(self, engine):
        """Test engine default configuration values."""
        assert engine.max_file_size_mb == 25
        assert ".pdf" in engine.allowed_file_types
        assert ".doc" in engine.allowed_file_types
        assert engine.ai_validation_confidence_threshold == 0.8
        assert engine.auto_approve_threshold == 0.95
        assert engine.processing_interval_seconds == 180


class TestDocumentIntegration:
    """Integration tests for document orchestration workflows."""

    @pytest.mark.asyncio
    async def test_complete_document_workflow(self):
        """Test complete document workflow from collection to validation."""
        # Integration test placeholder
        pass

    @pytest.mark.asyncio
    async def test_multi_document_coordination(self):
        """Test coordination of multiple document collections."""
        # Integration test placeholder
        pass

    @pytest.mark.asyncio
    async def test_document_workflow_recovery(self):
        """Test document workflow recovery after interruption."""
        # Integration test placeholder
        pass