"""
Comprehensive tests for Document Orchestration Engine.
Tests cover document collection, validation, template generation, and lifecycle management.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any
import base64

from ghl_real_estate_ai.services.document_orchestration_engine import (
    DocumentOrchestrationEngine,
    DocumentType,
    DocumentStatus,
    DocumentRequest,
    ValidationResult
)


class TestDocumentRequest:
    """Test DocumentRequest dataclass functionality."""

    def test_document_request_creation(self):
        """Test document request creation with all fields."""
        request = DocumentRequest(
            id="req_001",
            document_type=DocumentType.PURCHASE_AGREEMENT,
            status=DocumentStatus.PENDING,
            deal_id="deal_123",
            client_id="client_456",
            title="Purchase Agreement Collection",
            description="Collect signed purchase agreement from buyer",
            due_date=datetime.now() + timedelta(days=3),
            priority=9,
            collection_method="secure_portal",
            metadata={"property_address": "123 Main St", "contract_date": "2024-01-15"}
        )

        assert request.id == "req_001"
        assert request.document_type == DocumentType.PURCHASE_AGREEMENT
        assert request.status == DocumentStatus.PENDING
        assert request.priority == 9
        assert request.metadata["property_address"] == "123 Main St"

    def test_document_request_serialization(self):
        """Test document request serialization to dictionary."""
        request = DocumentRequest(
            id="req_002",
            document_type=DocumentType.INSPECTION_REPORT,
            status=DocumentStatus.RECEIVED,
            deal_id="deal_789",
            client_id="client_101",
            title="Home Inspection Report",
            description="Professional home inspection report",
            due_date=datetime.now() + timedelta(days=1),
            priority=8,
            collection_method="vendor_upload"
        )

        request_dict = request.__dict__
        assert request_dict["id"] == "req_002"
        assert request_dict["document_type"] == DocumentType.INSPECTION_REPORT
        assert isinstance(request_dict["due_date"], datetime)


class TestValidationResult:
    """Test ValidationResult dataclass functionality."""

    def test_validation_result_success(self):
        """Test successful validation result."""
        result = ValidationResult(
            is_valid=True,
            confidence_score=0.95,
            validation_details={
                "format_check": "passed",
                "content_analysis": "complete",
                "signature_verification": "valid"
            },
            ai_analysis="Document appears complete and properly executed",
            required_actions=[]
        )

        assert result.is_valid is True
        assert result.confidence_score == 0.95
        assert len(result.required_actions) == 0
        assert "complete" in result.ai_analysis

    def test_validation_result_failure(self):
        """Test failed validation result."""
        result = ValidationResult(
            is_valid=False,
            confidence_score=0.65,
            validation_details={
                "format_check": "failed",
                "missing_signatures": ["buyer", "seller"]
            },
            ai_analysis="Document is missing required signatures",
            required_actions=["request_buyer_signature", "request_seller_signature"]
        )

        assert result.is_valid is False
        assert result.confidence_score == 0.65
        assert len(result.required_actions) == 2
        assert "missing" in result.ai_analysis


class TestDocumentOrchestrationEngine:
    """Test the main document orchestration functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for document engine."""
        return {
            'cache_service': AsyncMock(),
            'ghl_client': AsyncMock(),
            'claude_assistant': AsyncMock(),
            'file_storage': AsyncMock(),
            'notification_service': AsyncMock()
        }

    @pytest.fixture
    def engine(self, mock_dependencies):
        """Create document engine instance with mocked dependencies."""
        return DocumentOrchestrationEngine(
            cache_service=mock_dependencies['cache_service'],
            ghl_client=mock_dependencies['ghl_client'],
            claude_assistant=mock_dependencies['claude_assistant']
        )

    @pytest.mark.asyncio
    async def test_initiate_document_collection_success(self, engine, mock_dependencies):
        """Test successful document collection initiation."""
        collection_data = {
            "deal_id": "deal_123",
            "client_id": "client_456",
            "document_type": "purchase_agreement",
            "priority": 9,
            "due_date": "2024-01-20T00:00:00",
            "collection_method": "secure_portal"
        }

        # Mock cache operations
        mock_dependencies['cache_service'].set.return_value = True
        mock_dependencies['cache_service'].get.return_value = None

        # Mock GHL portal creation
        mock_dependencies['ghl_client'].create_document_portal.return_value = {
            "success": True,
            "portal_url": "https://secure.example.com/upload/xyz123",
            "portal_id": "portal_789"
        }

        result = await engine.initiate_document_collection(collection_data)

        assert result["success"] is True
        assert result["request_id"] is not None
        assert result["collection_method"] == "secure_portal"
        assert "portal_url" in result

        # Verify service calls
        mock_dependencies['ghl_client'].create_document_portal.assert_called_once()
        mock_dependencies['cache_service'].set.assert_called()

    @pytest.mark.asyncio
    async def test_initiate_document_collection_duplicate(self, engine, mock_dependencies):
        """Test handling of duplicate document collection request."""
        collection_data = {
            "deal_id": "deal_existing",
            "document_type": "purchase_agreement"
        }

        # Mock existing request in cache
        mock_dependencies['cache_service'].get.return_value = {
            "request_id": "req_existing",
            "status": DocumentStatus.PENDING.value
        }

        result = await engine.initiate_document_collection(collection_data)

        assert result["success"] is False
        assert "already exists" in result["error"]
        mock_dependencies['ghl_client'].create_document_portal.assert_not_called()

    @pytest.mark.asyncio
    async def test_receive_document_success(self, engine, mock_dependencies):
        """Test successful document receipt and processing."""
        document_data = {
            "request_id": "req_123",
            "file_content": base64.b64encode(b"mock PDF content").decode(),
            "file_name": "purchase_agreement.pdf",
            "file_size": 1024,
            "upload_timestamp": datetime.now().isoformat()
        }

        # Mock existing request
        mock_request = DocumentRequest(
            id="req_123",
            document_type=DocumentType.PURCHASE_AGREEMENT,
            status=DocumentStatus.PENDING,
            deal_id="deal_123",
            client_id="client_456",
            title="Purchase Agreement",
            description="Collect purchase agreement",
            due_date=datetime.now() + timedelta(days=1),
            priority=9,
            collection_method="secure_portal"
        )

        mock_dependencies['cache_service'].get.return_value = mock_request

        # Mock file storage
        mock_dependencies['file_storage'].store_document.return_value = {
            "success": True,
            "file_id": "file_789",
            "storage_path": "/documents/deal_123/purchase_agreement.pdf"
        }

        # Mock AI validation
        with patch.object(engine, '_perform_ai_validation', return_value=ValidationResult(
            is_valid=True,
            confidence_score=0.92,
            validation_details={"format_check": "passed"},
            ai_analysis="Document appears complete and properly executed",
            required_actions=[]
        )):
            result = await engine.receive_document(document_data)

        assert result["success"] is True
        assert result["status"] == DocumentStatus.VALIDATED.value
        assert result["file_id"] == "file_789"

        # Verify storage and validation calls
        mock_dependencies['file_storage'].store_document.assert_called_once()
        mock_dependencies['cache_service'].set.assert_called()

    @pytest.mark.asyncio
    async def test_receive_document_validation_failure(self, engine, mock_dependencies):
        """Test document receipt with validation failure."""
        document_data = {
            "request_id": "req_456",
            "file_content": base64.b64encode(b"invalid content").decode(),
            "file_name": "incomplete.pdf",
            "file_size": 512
        }

        # Mock existing request
        mock_request = DocumentRequest(
            id="req_456",
            document_type=DocumentType.INSPECTION_REPORT,
            status=DocumentStatus.PENDING,
            deal_id="deal_456",
            client_id="client_789",
            title="Inspection Report",
            description="Home inspection report",
            due_date=datetime.now() + timedelta(hours=12),
            priority=8
        )

        mock_dependencies['cache_service'].get.return_value = mock_request
        mock_dependencies['file_storage'].store_document.return_value = {
            "success": True,
            "file_id": "file_invalid",
            "storage_path": "/documents/deal_456/incomplete.pdf"
        }

        # Mock AI validation failure
        with patch.object(engine, '_perform_ai_validation', return_value=ValidationResult(
            is_valid=False,
            confidence_score=0.45,
            validation_details={"missing_sections": ["structural_assessment"]},
            ai_analysis="Document appears incomplete - missing structural assessment section",
            required_actions=["request_complete_report"]
        )):
            result = await engine.receive_document(document_data)

        assert result["success"] is True  # Receipt successful
        assert result["status"] == DocumentStatus.VALIDATION_FAILED.value
        assert len(result["required_actions"]) == 1
        assert "incomplete" in result["validation_message"]

    @pytest.mark.asyncio
    async def test_generate_document_template_success(self, engine, mock_dependencies):
        """Test successful document template generation."""
        template_data = {
            "document_type": "closing_disclosure",
            "deal_id": "deal_789",
            "property_data": {
                "address": "456 Oak Street, Austin, TX",
                "sale_price": 425000,
                "loan_amount": 340000
            },
            "client_data": {
                "buyer_name": "Jane Smith",
                "email": "jane@example.com"
            }
        }

        # Mock Claude AI template generation
        mock_dependencies['claude_assistant'].generate_response.return_value = {
            "template_content": "CLOSING DISCLOSURE\n\nProperty: 456 Oak Street...",
            "fillable_fields": ["buyer_signature", "date_signed"],
            "template_version": "v2.1"
        }

        # Mock template storage
        mock_dependencies['file_storage'].store_template.return_value = {
            "success": True,
            "template_id": "tmpl_123",
            "template_url": "https://docs.example.com/templates/tmpl_123"
        }

        result = await engine.generate_document_template(template_data)

        assert result["success"] is True
        assert result["template_id"] == "tmpl_123"
        assert "template_url" in result
        assert len(result["fillable_fields"]) == 2

        # Verify AI and storage calls
        mock_dependencies['claude_assistant'].generate_response.assert_called_once()
        mock_dependencies['file_storage'].store_template.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_validation_comprehensive(self, engine, mock_dependencies):
        """Test comprehensive AI document validation."""
        document_content = "PURCHASE AGREEMENT\n\nBuyer: John Doe\nSeller: Jane Smith..."
        document_type = DocumentType.PURCHASE_AGREEMENT

        # Mock Claude AI validation response
        mock_dependencies['claude_assistant'].generate_response.return_value = {
            "validation_analysis": {
                "is_valid": True,
                "confidence_score": 0.88,
                "completeness_check": {
                    "required_fields_present": True,
                    "signatures_present": True,
                    "dates_valid": True
                },
                "content_analysis": {
                    "contract_terms_clear": True,
                    "legal_compliance": "appears_compliant",
                    "potential_issues": []
                },
                "recommendations": [
                    "Verify property tax information",
                    "Confirm closing date with all parties"
                ]
            }
        }

        result = await engine._perform_ai_validation(document_content, document_type)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.confidence_score == 0.88
        assert len(result.required_actions) > 0  # Should have recommendations
        assert "appears_compliant" in result.ai_analysis

        mock_dependencies['claude_assistant'].generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_collection_status(self, engine, mock_dependencies):
        """Test document collection status retrieval."""
        deal_id = "deal_123"

        # Mock multiple document requests
        mock_requests = [
            DocumentRequest(
                id="req_001",
                document_type=DocumentType.PURCHASE_AGREEMENT,
                status=DocumentStatus.VALIDATED,
                deal_id=deal_id,
                client_id="client_456",
                title="Purchase Agreement",
                description="Signed purchase agreement",
                due_date=datetime.now() + timedelta(days=1),
                priority=9
            ),
            DocumentRequest(
                id="req_002",
                document_type=DocumentType.INSPECTION_REPORT,
                status=DocumentStatus.PENDING,
                deal_id=deal_id,
                client_id="client_456",
                title="Inspection Report",
                description="Home inspection report",
                due_date=datetime.now() + timedelta(hours=6),
                priority=8
            )
        ]

        mock_dependencies['cache_service'].get.return_value = mock_requests

        result = await engine.get_collection_status(deal_id)

        assert result["deal_id"] == deal_id
        assert result["total_requests"] == 2
        assert result["completed_requests"] == 1
        assert result["pending_requests"] == 1
        assert result["completion_percentage"] == 50.0

    @pytest.mark.asyncio
    async def test_send_reminder_notifications(self, engine, mock_dependencies):
        """Test sending reminder notifications for overdue documents."""
        # Mock overdue requests
        overdue_request = DocumentRequest(
            id="req_overdue",
            document_type=DocumentType.FINANCIAL_STATEMENT,
            status=DocumentStatus.PENDING,
            deal_id="deal_123",
            client_id="client_456",
            title="Financial Statement",
            description="Bank statements and W2 forms",
            due_date=datetime.now() - timedelta(hours=2),  # Overdue
            priority=7,
            collection_method="email"
        )

        mock_dependencies['cache_service'].get.return_value = [overdue_request]

        # Mock notification service
        mock_dependencies['notification_service'].send_reminder.return_value = {
            "success": True,
            "channels_sent": ["email", "sms"],
            "message_id": "msg_789"
        }

        result = await engine.send_reminder_notifications("deal_123")

        assert result["reminders_sent"] == 1
        assert result["success"] is True
        mock_dependencies['notification_service'].send_reminder.assert_called_once()

    @pytest.mark.asyncio
    async def test_document_lifecycle_tracking(self, engine, mock_dependencies):
        """Test complete document lifecycle tracking."""
        request_id = "req_lifecycle_test"

        # Mock lifecycle events
        lifecycle_events = [
            {
                "event": "collection_initiated",
                "timestamp": datetime.now() - timedelta(days=2),
                "details": {"collection_method": "secure_portal"}
            },
            {
                "event": "document_received",
                "timestamp": datetime.now() - timedelta(days=1),
                "details": {"file_name": "contract.pdf", "file_size": 2048}
            },
            {
                "event": "validation_completed",
                "timestamp": datetime.now() - timedelta(hours=2),
                "details": {"validation_result": "passed", "confidence": 0.91}
            }
        ]

        mock_dependencies['cache_service'].get.return_value = lifecycle_events

        result = await engine.get_document_lifecycle(request_id)

        assert len(result["lifecycle_events"]) == 3
        assert result["current_status"] == "validation_completed"
        assert result["lifecycle_events"][0]["event"] == "collection_initiated"

    @pytest.mark.asyncio
    async def test_bulk_document_processing(self, engine, mock_dependencies):
        """Test bulk document processing capabilities."""
        deal_ids = ["deal_001", "deal_002", "deal_003"]

        # Mock bulk processing response
        mock_dependencies['cache_service'].get.side_effect = [
            [  # deal_001 requests
                DocumentRequest(id="req_001", document_type=DocumentType.PURCHASE_AGREEMENT,
                              status=DocumentStatus.VALIDATED, deal_id="deal_001",
                              client_id="client_001", title="Purchase Agreement",
                              description="PA", due_date=datetime.now() + timedelta(days=1),
                              priority=9)
            ],
            [  # deal_002 requests
                DocumentRequest(id="req_002", document_type=DocumentType.INSPECTION_REPORT,
                              status=DocumentStatus.PENDING, deal_id="deal_002",
                              client_id="client_002", title="Inspection Report",
                              description="IR", due_date=datetime.now() + timedelta(hours=6),
                              priority=8)
            ],
            [  # deal_003 requests
                DocumentRequest(id="req_003", document_type=DocumentType.APPRAISAL_REPORT,
                              status=DocumentStatus.VALIDATION_FAILED, deal_id="deal_003",
                              client_id="client_003", title="Appraisal Report",
                              description="AR", due_date=datetime.now() + timedelta(hours=12),
                              priority=7)
            ]
        ]

        result = await engine.get_bulk_collection_status(deal_ids)

        assert len(result["deals"]) == 3
        assert result["summary"]["total_deals"] == 3
        assert result["summary"]["total_requests"] == 3
        assert result["summary"]["completed_requests"] == 1

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, engine, mock_dependencies):
        """Test error handling and recovery mechanisms."""
        collection_data = {
            "deal_id": "deal_error_test",
            "document_type": "purchase_agreement"
        }

        # Mock service failure
        mock_dependencies['ghl_client'].create_document_portal.side_effect = Exception("API Error")

        # Should handle gracefully and return error
        result = await engine.initiate_document_collection(collection_data)

        assert result["success"] is False
        assert "error" in result
        assert "API Error" in str(result["error"])

    @pytest.mark.asyncio
    async def test_document_security_validation(self, engine, mock_dependencies):
        """Test document security and compliance validation."""
        document_content = "CONFIDENTIAL PURCHASE AGREEMENT..."

        # Mock security analysis
        mock_dependencies['claude_assistant'].generate_response.return_value = {
            "security_analysis": {
                "contains_pii": True,
                "sensitive_fields": ["ssn", "account_number"],
                "security_score": 0.85,
                "compliance_check": "passed",
                "recommendations": ["encrypt_at_rest", "audit_access"]
            }
        }

        result = await engine._validate_document_security(document_content)

        assert result["contains_pii"] is True
        assert len(result["sensitive_fields"]) == 2
        assert result["security_score"] == 0.85
        assert "encrypt_at_rest" in result["recommendations"]

    def test_document_type_validation(self, engine):
        """Test document type validation logic."""
        # Test valid document types
        assert engine._is_valid_document_type("purchase_agreement") is True
        assert engine._is_valid_document_type("inspection_report") is True
        assert engine._is_valid_document_type("invalid_type") is False

    def test_collection_priority_calculation(self, engine):
        """Test document collection priority calculation."""
        # High priority: Purchase agreement near closing
        high_priority = engine._calculate_collection_priority(
            document_type=DocumentType.PURCHASE_AGREEMENT,
            days_until_closing=3,
            deal_value=500000
        )

        # Low priority: Optional document with long timeline
        low_priority = engine._calculate_collection_priority(
            document_type=DocumentType.WARRANTY_DEED,
            days_until_closing=30,
            deal_value=200000
        )

        assert high_priority > low_priority
        assert high_priority >= 8  # Should be high priority
        assert low_priority <= 5   # Should be lower priority


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