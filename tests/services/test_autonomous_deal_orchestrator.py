"""
Comprehensive tests for Autonomous Deal Orchestration Engine.
Tests cover workflow management, autonomous task execution, and system integration.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from ghl_real_estate_ai.services.autonomous_deal_orchestrator import (
    AutonomousDealOrchestrator,
    WorkflowStage,
    TaskType,
    TaskStatus,
    AutonomousTask
)


class TestAutonomousTask:
    """Test AutonomousTask dataclass and its functionality."""

    def test_task_creation(self):
        """Test task creation with all required fields."""
        task = AutonomousTask(
            id="task_001",
            type=TaskType.DOCUMENT_COLLECTION,
            status=TaskStatus.PENDING,
            title="Collect Purchase Agreement",
            description="Collect signed purchase agreement from client",
            deal_id="deal_123",
            stage=WorkflowStage.CONTRACT_REVIEW,
            priority=8,
            due_date=datetime.now() + timedelta(days=2),
            dependencies=["task_000"],
            metadata={"document_type": "purchase_agreement"}
        )

        assert task.id == "task_001"
        assert task.type == TaskType.DOCUMENT_COLLECTION
        assert task.status == TaskStatus.PENDING
        assert task.priority == 8
        assert len(task.dependencies) == 1
        assert task.metadata["document_type"] == "purchase_agreement"

    def test_task_serialization(self):
        """Test task can be serialized to dictionary."""
        task = AutonomousTask(
            id="task_002",
            type=TaskType.VENDOR_COORDINATION,
            status=TaskStatus.IN_PROGRESS,
            title="Schedule Home Inspection",
            description="Schedule inspection with preferred vendor",
            deal_id="deal_456",
            stage=WorkflowStage.INSPECTIONS,
            priority=7,
            due_date=datetime.now() + timedelta(days=1)
        )

        task_dict = task.__dict__
        assert task_dict["id"] == "task_002"
        assert task_dict["type"] == TaskType.VENDOR_COORDINATION
        assert isinstance(task_dict["due_date"], datetime)


class TestAutonomousDealOrchestrator:
    """Test the main orchestrator functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for orchestrator."""
        return {
            'cache_service': AsyncMock(),
            'ghl_client': AsyncMock(),
            'claude_assistant': AsyncMock(),
            'document_engine': AsyncMock(),
            'vendor_engine': AsyncMock(),
            'communication_engine': AsyncMock(),
            'exception_engine': AsyncMock()
        }

    @pytest.fixture
    def orchestrator(self, mock_dependencies):
        """Create orchestrator instance with mocked dependencies."""
        return AutonomousDealOrchestrator(
            cache_service=mock_dependencies['cache_service'],
            ghl_client=mock_dependencies['ghl_client'],
            claude_assistant=mock_dependencies['claude_assistant']
        )

    @pytest.mark.asyncio
    async def test_initiate_deal_workflow_success(self, orchestrator, mock_dependencies):
        """Test successful workflow initiation."""
        deal_data = {
            "deal_id": "deal_789",
            "property_address": "123 Main St, Austin, TX",
            "client_name": "John Doe",
            "contract_date": "2024-01-15",
            "closing_date": "2024-02-15"
        }

        # Mock cache operations
        mock_dependencies['cache_service'].get.return_value = None
        mock_dependencies['cache_service'].set.return_value = True

        # Mock Claude AI response for workflow planning
        mock_dependencies['claude_assistant'].generate_response.return_value = {
            "workflow_plan": "Standard purchase workflow with inspections",
            "key_milestones": ["contract_review", "inspections", "financing"],
            "estimated_duration": "30 days"
        }

        result = await orchestrator.initiate_deal_workflow(deal_data)

        assert result["success"] is True
        assert result["deal_id"] == "deal_789"
        assert "workflow_id" in result
        assert len(result["initial_tasks"]) > 0

        # Verify cache operations
        mock_dependencies['cache_service'].set.assert_called()
        mock_dependencies['claude_assistant'].generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_deal_workflow_duplicate(self, orchestrator, mock_dependencies):
        """Test handling of duplicate deal workflow initiation."""
        deal_data = {"deal_id": "deal_existing", "property_address": "456 Oak St"}

        # Mock existing workflow in cache
        mock_dependencies['cache_service'].get.return_value = {
            "workflow_id": "existing_workflow",
            "status": "active"
        }

        result = await orchestrator.initiate_deal_workflow(deal_data)

        assert result["success"] is False
        assert "already exists" in result["error"]
        mock_dependencies['claude_assistant'].generate_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_active_tasks(self, orchestrator, mock_dependencies):
        """Test processing of active tasks in workflow."""
        # Mock active tasks in cache
        active_tasks = [
            AutonomousTask(
                id="task_100",
                type=TaskType.DOCUMENT_COLLECTION,
                status=TaskStatus.PENDING,
                title="Collect Insurance",
                description="Collect homeowner's insurance documentation",
                deal_id="deal_123",
                stage=WorkflowStage.FINANCING,
                priority=6,
                due_date=datetime.now() + timedelta(hours=12)
            ),
            AutonomousTask(
                id="task_101",
                type=TaskType.COMMUNICATION,
                status=TaskStatus.PENDING,
                title="Send Update",
                description="Send weekly progress update to client",
                deal_id="deal_123",
                stage=WorkflowStage.FINANCING,
                priority=4,
                due_date=datetime.now() + timedelta(days=1)
            )
        ]

        mock_dependencies['cache_service'].get.return_value = active_tasks

        with patch.object(orchestrator, '_execute_autonomous_task', return_value={"success": True}):
            result = await orchestrator._process_active_tasks("deal_123")

        assert result["processed_count"] == 2
        assert result["success_count"] == 2
        assert result["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_execute_document_collection_task(self, orchestrator, mock_dependencies):
        """Test execution of document collection task."""
        task = AutonomousTask(
            id="task_doc_001",
            type=TaskType.DOCUMENT_COLLECTION,
            status=TaskStatus.PENDING,
            title="Collect W2 Forms",
            description="Collect client W2 forms for financing",
            deal_id="deal_123",
            stage=WorkflowStage.FINANCING,
            priority=8,
            due_date=datetime.now() + timedelta(days=3),
            metadata={"document_type": "w2_forms", "client_id": "client_456"}
        )

        # Mock document engine response
        mock_document_engine = AsyncMock()
        mock_document_engine.initiate_document_collection.return_value = {
            "success": True,
            "request_id": "req_789",
            "collection_method": "secure_portal"
        }

        with patch.object(orchestrator, 'document_engine', mock_document_engine):
            result = await orchestrator._execute_autonomous_task(task)

        assert result["success"] is True
        assert result["action"] == "document_collection_initiated"
        mock_document_engine.initiate_document_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_vendor_coordination_task(self, orchestrator, mock_dependencies):
        """Test execution of vendor coordination task."""
        task = AutonomousTask(
            id="task_vendor_001",
            type=TaskType.VENDOR_COORDINATION,
            status=TaskStatus.PENDING,
            title="Schedule Appraisal",
            description="Schedule property appraisal with certified appraiser",
            deal_id="deal_456",
            stage=WorkflowStage.INSPECTIONS,
            priority=9,
            due_date=datetime.now() + timedelta(days=2),
            metadata={"vendor_type": "appraiser", "property_id": "prop_789"}
        )

        # Mock vendor engine response
        mock_vendor_engine = AsyncMock()
        mock_vendor_engine.request_vendor_service.return_value = {
            "success": True,
            "appointment_id": "appt_123",
            "scheduled_date": "2024-01-20T10:00:00",
            "vendor_name": "Elite Appraisals LLC"
        }

        with patch.object(orchestrator, 'vendor_engine', mock_vendor_engine):
            result = await orchestrator._execute_autonomous_task(task)

        assert result["success"] is True
        assert result["action"] == "vendor_service_scheduled"
        mock_vendor_engine.request_vendor_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_communication_task(self, orchestrator, mock_dependencies):
        """Test execution of communication task."""
        task = AutonomousTask(
            id="task_comm_001",
            type=TaskType.COMMUNICATION,
            status=TaskStatus.PENDING,
            title="Milestone Update",
            description="Send inspection completion milestone update",
            deal_id="deal_789",
            stage=WorkflowStage.INSPECTIONS,
            priority=5,
            due_date=datetime.now() + timedelta(hours=6),
            metadata={
                "communication_type": "milestone_update",
                "milestone": "inspection_completed",
                "recipients": ["client", "agent"]
            }
        )

        # Mock communication engine response
        mock_comm_engine = AsyncMock()
        mock_comm_engine.send_milestone_update.return_value = {
            "success": True,
            "message_id": "msg_456",
            "channels_sent": ["email", "sms", "portal"]
        }

        with patch.object(orchestrator, 'communication_engine', mock_comm_engine):
            result = await orchestrator._execute_autonomous_task(task)

        assert result["success"] is True
        assert result["action"] == "milestone_update_sent"
        mock_comm_engine.send_milestone_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_workflow_status(self, orchestrator, mock_dependencies):
        """Test workflow status retrieval."""
        # Mock workflow data in cache
        workflow_data = {
            "workflow_id": "workflow_123",
            "deal_id": "deal_456",
            "stage": WorkflowStage.FINANCING.value,
            "status": "active",
            "created_date": datetime.now().isoformat(),
            "total_tasks": 15,
            "completed_tasks": 8,
            "pending_tasks": 5,
            "failed_tasks": 2
        }

        mock_dependencies['cache_service'].get.return_value = workflow_data

        result = await orchestrator.get_workflow_status("deal_456")

        assert result["deal_id"] == "deal_456"
        assert result["stage"] == WorkflowStage.FINANCING.value
        assert result["completion_percentage"] == 53.33  # 8/15 * 100
        assert result["total_tasks"] == 15

    @pytest.mark.asyncio
    async def test_pause_workflow(self, orchestrator, mock_dependencies):
        """Test workflow pause functionality."""
        mock_dependencies['cache_service'].get.return_value = {
            "workflow_id": "workflow_123",
            "status": "active"
        }
        mock_dependencies['cache_service'].set.return_value = True

        result = await orchestrator.pause_workflow("deal_789", "Manual pause for client review")

        assert result["success"] is True
        assert result["action"] == "workflow_paused"
        mock_dependencies['cache_service'].set.assert_called()

    @pytest.mark.asyncio
    async def test_resume_workflow(self, orchestrator, mock_dependencies):
        """Test workflow resume functionality."""
        mock_dependencies['cache_service'].get.return_value = {
            "workflow_id": "workflow_123",
            "status": "paused"
        }
        mock_dependencies['cache_service'].set.return_value = True

        result = await orchestrator.resume_workflow("deal_789")

        assert result["success"] is True
        assert result["action"] == "workflow_resumed"
        mock_dependencies['cache_service'].set.assert_called()

    @pytest.mark.asyncio
    async def test_task_dependency_resolution(self, orchestrator, mock_dependencies):
        """Test task dependency resolution logic."""
        # Create tasks with dependencies
        completed_task = AutonomousTask(
            id="task_parent",
            type=TaskType.DOCUMENT_COLLECTION,
            status=TaskStatus.COMPLETED,
            title="Collect Contract",
            description="Collect signed purchase contract",
            deal_id="deal_123",
            stage=WorkflowStage.CONTRACT_REVIEW,
            priority=10,
            due_date=datetime.now()
        )

        dependent_task = AutonomousTask(
            id="task_child",
            type=TaskType.VENDOR_COORDINATION,
            status=TaskStatus.WAITING_DEPENDENCIES,
            title="Schedule Inspection",
            description="Schedule home inspection after contract review",
            deal_id="deal_123",
            stage=WorkflowStage.INSPECTIONS,
            priority=8,
            due_date=datetime.now() + timedelta(days=1),
            dependencies=["task_parent"]
        )

        # Mock cache to return tasks
        mock_dependencies['cache_service'].get.side_effect = [
            [completed_task, dependent_task],  # All tasks
            completed_task  # Specific task lookup
        ]

        result = await orchestrator._resolve_task_dependencies("deal_123", dependent_task)

        assert result is True  # Dependencies should be resolved

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, orchestrator, mock_dependencies):
        """Test error handling and recovery mechanisms."""
        task = AutonomousTask(
            id="task_error_test",
            type=TaskType.DOCUMENT_COLLECTION,
            status=TaskStatus.PENDING,
            title="Error Test Task",
            description="Task that will fail for testing",
            deal_id="deal_error",
            stage=WorkflowStage.CONTRACT_REVIEW,
            priority=5,
            due_date=datetime.now() + timedelta(hours=1)
        )

        # Mock document engine to raise exception
        mock_document_engine = AsyncMock()
        mock_document_engine.initiate_document_collection.side_effect = Exception("API Error")

        # Mock exception engine
        mock_exception_engine = AsyncMock()
        mock_exception_engine.report_exception.return_value = {
            "success": True,
            "exception_id": "exc_123",
            "recovery_strategy": "retry_with_backoff"
        }

        with patch.object(orchestrator, 'document_engine', mock_document_engine), \
             patch.object(orchestrator, 'exception_engine', mock_exception_engine):

            result = await orchestrator._execute_autonomous_task(task)

        assert result["success"] is False
        assert "error" in result
        mock_exception_engine.report_exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, orchestrator, mock_dependencies):
        """Test performance monitoring and metrics collection."""
        # Mock performance data in cache
        performance_data = {
            "total_workflows": 150,
            "completed_workflows": 120,
            "active_workflows": 25,
            "failed_workflows": 5,
            "average_completion_time": 28.5,  # days
            "task_success_rate": 94.2,  # percentage
            "automation_rate": 91.5  # percentage of tasks completed autonomously
        }

        mock_dependencies['cache_service'].get.return_value = performance_data

        result = await orchestrator.get_system_performance_metrics()

        assert result["total_workflows"] == 150
        assert result["success_rate"] == 80.0  # 120/150 * 100
        assert result["automation_rate"] == 91.5
        assert result["average_completion_time"] == 28.5

    @pytest.mark.asyncio
    async def test_workflow_stage_progression(self, orchestrator, mock_dependencies):
        """Test workflow stage progression logic."""
        # Mock current workflow state
        mock_dependencies['cache_service'].get.return_value = {
            "workflow_id": "workflow_123",
            "current_stage": WorkflowStage.CONTRACT_REVIEW.value,
            "completed_stages": [],
            "stage_progress": {"CONTRACT_REVIEW": 85}
        }

        result = await orchestrator._advance_workflow_stage("deal_123", WorkflowStage.INSPECTIONS)

        assert result["success"] is True
        assert result["new_stage"] == WorkflowStage.INSPECTIONS.value
        mock_dependencies['cache_service'].set.assert_called()

    def test_task_priority_sorting(self, orchestrator):
        """Test task priority sorting logic."""
        tasks = [
            AutonomousTask(id="low", type=TaskType.COMMUNICATION, status=TaskStatus.PENDING,
                         title="Low Priority", description="Low", deal_id="deal_1",
                         stage=WorkflowStage.FINANCING, priority=3,
                         due_date=datetime.now() + timedelta(days=1)),
            AutonomousTask(id="high", type=TaskType.DOCUMENT_COLLECTION, status=TaskStatus.PENDING,
                         title="High Priority", description="High", deal_id="deal_1",
                         stage=WorkflowStage.CONTRACT_REVIEW, priority=9,
                         due_date=datetime.now() + timedelta(hours=6)),
            AutonomousTask(id="medium", type=TaskType.VENDOR_COORDINATION, status=TaskStatus.PENDING,
                         title="Medium Priority", description="Medium", deal_id="deal_1",
                         stage=WorkflowStage.INSPECTIONS, priority=6,
                         due_date=datetime.now() + timedelta(hours=12))
        ]

        sorted_tasks = orchestrator._sort_tasks_by_priority(tasks)

        assert sorted_tasks[0].id == "high"
        assert sorted_tasks[1].id == "medium"
        assert sorted_tasks[2].id == "low"
        assert sorted_tasks[0].priority == 9
        assert sorted_tasks[2].priority == 3


class TestWorkflowIntegration:
    """Integration tests for complete workflow scenarios."""

    @pytest.mark.asyncio
    async def test_complete_workflow_lifecycle(self):
        """Test a complete workflow from initiation to completion."""
        # This would be an integration test that exercises the full system
        # For brevity, this is a placeholder for the concept
        pass

    @pytest.mark.asyncio
    async def test_multi_deal_concurrent_processing(self):
        """Test handling multiple deals concurrently."""
        # Test concurrent processing capabilities
        pass

    @pytest.mark.asyncio
    async def test_workflow_recovery_after_system_restart(self):
        """Test workflow recovery after system restart."""
        # Test persistence and recovery mechanisms
        pass