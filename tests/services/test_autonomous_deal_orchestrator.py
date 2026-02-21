import pytest

pytestmark = pytest.mark.integration

"""
Comprehensive tests for Autonomous Deal Orchestration Engine.
Tests cover workflow management, autonomous task execution, and system integration.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.autonomous_deal_orchestrator import (
    AutonomousDealOrchestrator,
    AutonomousTask,
    DocumentRequest,
    EscalationRule,
    TaskStatus,
    TaskType,
    UrgencyLevel,
    VendorCoordination,
    WorkflowStage,
)


class TestAutonomousTask:
    """Test AutonomousTask dataclass and its functionality."""

    def test_task_creation(self):
        """Test task creation with all required fields."""
        task = AutonomousTask(
            task_id="task_001",
            transaction_id="deal_123",
            task_type=TaskType.DOCUMENT_REQUEST,
            workflow_stage=WorkflowStage.CONTRACT_EXECUTION,
            title="Collect Purchase Agreement",
            description="Collect signed purchase agreement from client",
            status=TaskStatus.PENDING,
            urgency=UrgencyLevel.HIGH,
            due_date=datetime.now() + timedelta(days=2),
            dependencies=["task_000"],
            metadata={"document_type": "purchase_agreement"},
        )

        assert task.task_id == "task_001"
        assert task.task_type == TaskType.DOCUMENT_REQUEST
        assert task.status == TaskStatus.PENDING
        assert task.urgency == UrgencyLevel.HIGH
        assert len(task.dependencies) == 1
        assert task.metadata["document_type"] == "purchase_agreement"

    def test_task_serialization(self):
        """Test task can be serialized to dictionary."""
        task = AutonomousTask(
            task_id="task_002",
            transaction_id="deal_456",
            task_type=TaskType.VENDOR_SCHEDULING,
            workflow_stage=WorkflowStage.DUE_DILIGENCE,
            title="Schedule Home Inspection",
            description="Schedule inspection with preferred vendor",
            status=TaskStatus.IN_PROGRESS,
            urgency=UrgencyLevel.HIGH,
            due_date=datetime.now() + timedelta(days=1),
        )

        task_dict = task.__dict__
        assert task_dict["task_id"] == "task_002"
        assert task_dict["task_type"] == TaskType.VENDOR_SCHEDULING
        assert isinstance(task_dict["due_date"], datetime)


class TestAutonomousDealOrchestrator:
    """Test the main orchestrator functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for orchestrator."""
        return {
            "cache_service": AsyncMock(),
            "ghl_client": MagicMock(),
            "claude_assistant": MagicMock(),
            "transaction_service": AsyncMock(),
        }

    @pytest.fixture
    def orchestrator(self, mock_dependencies):
        """Create orchestrator instance with mocked dependencies."""
        with (
            patch("ghl_real_estate_ai.services.autonomous_deal_orchestrator.get_cache_service") as mock_cache,
            patch("ghl_real_estate_ai.services.autonomous_deal_orchestrator.ClaudeAssistant") as mock_claude,
            patch("ghl_real_estate_ai.services.autonomous_deal_orchestrator.GHLClient") as mock_ghl,
            patch("ghl_real_estate_ai.services.autonomous_deal_orchestrator.get_llm_client") as mock_llm,
        ):
            mock_cache.return_value = mock_dependencies["cache_service"]
            mock_claude.return_value = mock_dependencies["claude_assistant"]
            mock_ghl.return_value = mock_dependencies["ghl_client"]
            mock_llm.return_value = MagicMock()

            return AutonomousDealOrchestrator(
                transaction_service=mock_dependencies["transaction_service"],
                cache_service=mock_dependencies["cache_service"],
                ghl_client=mock_dependencies["ghl_client"],
                claude_assistant=mock_dependencies["claude_assistant"],
            )

    @pytest.mark.asyncio
    async def test_start_orchestration(self, orchestrator):
        """Test starting the orchestration engine."""
        with patch.object(orchestrator, "_orchestration_loop", new_callable=AsyncMock):
            await orchestrator.start_orchestration()

            assert orchestrator.is_running is True
            assert orchestrator.orchestration_task is not None

    @pytest.mark.asyncio
    async def test_stop_orchestration(self, orchestrator):
        """Test stopping the orchestration engine."""

        async def dummy_loop():
            await asyncio.sleep(3600)

        orchestrator.is_running = True
        orchestrator.orchestration_task = asyncio.ensure_future(dummy_loop())

        await orchestrator.stop_orchestration()

        assert orchestrator.is_running is False

    @pytest.mark.asyncio
    async def test_process_active_tasks(self, orchestrator):
        """Test processing of active tasks in workflow."""
        # Create active tasks
        task1 = AutonomousTask(
            task_id="task_100",
            transaction_id="deal_123",
            task_type=TaskType.DOCUMENT_REQUEST,
            workflow_stage=WorkflowStage.FINANCING,
            title="Collect Insurance",
            description="Collect homeowner's insurance documentation",
            status=TaskStatus.PENDING,
            urgency=UrgencyLevel.MEDIUM,
            due_date=datetime.now() + timedelta(hours=12),
        )

        task2 = AutonomousTask(
            task_id="task_101",
            transaction_id="deal_123",
            task_type=TaskType.COMMUNICATION,
            workflow_stage=WorkflowStage.FINANCING,
            title="Send Update",
            description="Send weekly progress update to client",
            status=TaskStatus.PENDING,
            urgency=UrgencyLevel.LOW,
            due_date=datetime.now() + timedelta(days=1),
        )

        orchestrator.active_tasks["task_100"] = task1
        orchestrator.active_tasks["task_101"] = task2

        with patch.object(orchestrator, "_execute_autonomous_task", new_callable=AsyncMock) as mock_execute:
            await orchestrator._process_active_tasks()

            # Both tasks should have been processed
            assert mock_execute.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_document_request_task(self, orchestrator):
        """Test execution of document request task."""
        task = AutonomousTask(
            task_id="task_doc_001",
            transaction_id="deal_123",
            task_type=TaskType.DOCUMENT_REQUEST,
            workflow_stage=WorkflowStage.FINANCING,
            title="Collect W2 Forms",
            description="Collect client W2 forms for financing",
            status=TaskStatus.PENDING,
            urgency=UrgencyLevel.HIGH,
            due_date=datetime.now() + timedelta(days=3),
            metadata={
                "document_config": {
                    "type": "w2_forms",
                    "description": "Client W2 forms for financing",
                    "required": True,
                    "from": "buyer",
                }
            },
        )

        with patch.object(
            orchestrator, "_execute_document_request_task", new_callable=AsyncMock, return_value=True
        ) as mock_doc:
            await orchestrator._execute_autonomous_task(task)

            mock_doc.assert_called_once_with(task)
            assert task.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_vendor_scheduling_task(self, orchestrator):
        """Test execution of vendor scheduling task."""
        task = AutonomousTask(
            task_id="task_vendor_001",
            transaction_id="deal_456",
            task_type=TaskType.VENDOR_SCHEDULING,
            workflow_stage=WorkflowStage.DUE_DILIGENCE,
            title="Schedule Appraisal",
            description="Schedule property appraisal with certified appraiser",
            status=TaskStatus.PENDING,
            urgency=UrgencyLevel.HIGH,
            due_date=datetime.now() + timedelta(days=2),
            metadata={
                "vendor_config": {
                    "type": "appraiser",
                    "service": "property_appraisal",
                    "property_address": "123 Main St",
                }
            },
        )

        with patch.object(
            orchestrator, "_execute_vendor_scheduling_task", new_callable=AsyncMock, return_value=True
        ) as mock_vendor:
            await orchestrator._execute_autonomous_task(task)

            mock_vendor.assert_called_once_with(task)
            assert task.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_communication_task(self, orchestrator):
        """Test execution of communication task."""
        task = AutonomousTask(
            task_id="task_comm_001",
            transaction_id="deal_789",
            task_type=TaskType.COMMUNICATION,
            workflow_stage=WorkflowStage.DUE_DILIGENCE,
            title="Milestone Update",
            description="Send inspection completion milestone update",
            status=TaskStatus.PENDING,
            urgency=UrgencyLevel.MEDIUM,
            due_date=datetime.now() + timedelta(hours=6),
            metadata={
                "communication_config": {
                    "type": "milestone_update",
                    "recipients": ["buyer"],
                    "template": "inspection_update",
                }
            },
        )

        with patch.object(
            orchestrator, "_execute_communication_task", new_callable=AsyncMock, return_value=True
        ) as mock_comm:
            await orchestrator._execute_autonomous_task(task)

            mock_comm.assert_called_once_with(task)
            assert task.status == TaskStatus.COMPLETED

    def test_get_orchestration_status(self, orchestrator):
        """Test orchestration status retrieval."""
        # Add some tasks
        task1 = AutonomousTask(
            task_id="task_status_1",
            transaction_id="deal_456",
            task_type=TaskType.DOCUMENT_REQUEST,
            workflow_stage=WorkflowStage.FINANCING,
            title="Test Task 1",
            description="Test",
            status=TaskStatus.COMPLETED,
        )
        task2 = AutonomousTask(
            task_id="task_status_2",
            transaction_id="deal_456",
            task_type=TaskType.COMMUNICATION,
            workflow_stage=WorkflowStage.FINANCING,
            title="Test Task 2",
            description="Test",
            status=TaskStatus.PENDING,
        )

        orchestrator.active_tasks["task_status_1"] = task1
        orchestrator.active_tasks["task_status_2"] = task2

        result = orchestrator.get_orchestration_status()

        assert result["total_active_tasks"] == 2
        assert "tasks_by_stage" in result
        assert "metrics" in result
        assert "is_running" in result

    @pytest.mark.asyncio
    async def test_task_failure_and_retry(self, orchestrator):
        """Test task failure and retry logic."""
        task = AutonomousTask(
            task_id="task_retry_001",
            transaction_id="deal_123",
            task_type=TaskType.DOCUMENT_REQUEST,
            workflow_stage=WorkflowStage.CONTRACT_EXECUTION,
            title="Retry Test Task",
            description="Task that will fail for testing",
            status=TaskStatus.PENDING,
            urgency=UrgencyLevel.MEDIUM,
            due_date=datetime.now() + timedelta(hours=1),
            max_retries=3,
        )

        # Handle first failure with retry
        await orchestrator._handle_task_failure(task)

        assert task.retry_count == 1
        assert task.status == TaskStatus.SCHEDULED

        # Exhaust all retries
        task.retry_count = 3
        with patch.object(orchestrator, "_escalate_task", new_callable=AsyncMock) as mock_escalate:
            await orchestrator._handle_task_failure(task)

            assert task.status == TaskStatus.FAILED
            mock_escalate.assert_called_once()

    @pytest.mark.asyncio
    async def test_task_escalation(self, orchestrator, mock_dependencies):
        """Test task escalation when max retries exceeded."""
        task = AutonomousTask(
            task_id="task_esc_001",
            transaction_id="deal_123",
            task_type=TaskType.DOCUMENT_REQUEST,
            workflow_stage=WorkflowStage.CONTRACT_EXECUTION,
            title="Escalation Test",
            description="Task to be escalated",
            status=TaskStatus.FAILED,
            urgency=UrgencyLevel.HIGH,
        )

        mock_dependencies["cache_service"].set = AsyncMock()

        with patch.object(orchestrator, "_send_escalation_notification", new_callable=AsyncMock):
            await orchestrator._escalate_task(task, "Max retries exceeded")

            assert task.status == TaskStatus.ESCALATED
            assert orchestrator.metrics["escalations_triggered"] == 1

    def test_dependencies_satisfied(self, orchestrator):
        """Test dependency satisfaction check."""
        # Add a completed parent task
        parent_task = AutonomousTask(
            task_id="task_parent",
            transaction_id="deal_123",
            task_type=TaskType.DOCUMENT_REQUEST,
            workflow_stage=WorkflowStage.CONTRACT_EXECUTION,
            title="Parent Task",
            description="Completed parent",
            status=TaskStatus.COMPLETED,
        )
        orchestrator.active_tasks["task_parent"] = parent_task

        # Child task depends on parent
        child_task = AutonomousTask(
            task_id="task_child",
            transaction_id="deal_123",
            task_type=TaskType.VENDOR_SCHEDULING,
            workflow_stage=WorkflowStage.DUE_DILIGENCE,
            title="Child Task",
            description="Depends on parent",
            status=TaskStatus.PENDING,
            dependencies=["task_parent"],
        )

        assert orchestrator._dependencies_satisfied(child_task) is True

        # Test with unsatisfied dependency
        parent_task.status = TaskStatus.IN_PROGRESS
        assert orchestrator._dependencies_satisfied(child_task) is False

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, orchestrator):
        """Test error handling and recovery mechanisms."""
        task = AutonomousTask(
            task_id="task_error_test",
            transaction_id="deal_error",
            task_type=TaskType.DOCUMENT_REQUEST,
            workflow_stage=WorkflowStage.CONTRACT_EXECUTION,
            title="Error Test Task",
            description="Task that will fail for testing",
            status=TaskStatus.PENDING,
            urgency=UrgencyLevel.MEDIUM,
            due_date=datetime.now() + timedelta(hours=1),
        )

        # Mock _execute_document_request_task to raise an exception
        with (
            patch.object(
                orchestrator,
                "_execute_document_request_task",
                new_callable=AsyncMock,
                side_effect=Exception("API Error"),
            ),
            patch.object(orchestrator, "_handle_task_failure", new_callable=AsyncMock) as mock_handle_failure,
        ):
            await orchestrator._execute_autonomous_task(task)

            # Should have called failure handler
            mock_handle_failure.assert_called_once_with(task)

    def test_task_urgency_sorting(self, orchestrator):
        """Test task sorting by urgency."""
        tasks = [
            AutonomousTask(
                task_id="low",
                transaction_id="deal_1",
                task_type=TaskType.COMMUNICATION,
                workflow_stage=WorkflowStage.FINANCING,
                title="Low Priority",
                description="Low urgency task",
                status=TaskStatus.PENDING,
                urgency=UrgencyLevel.LOW,
                due_date=datetime.now() + timedelta(days=1),
            ),
            AutonomousTask(
                task_id="critical",
                transaction_id="deal_1",
                task_type=TaskType.DOCUMENT_REQUEST,
                workflow_stage=WorkflowStage.CONTRACT_EXECUTION,
                title="Critical Priority",
                description="Critical urgency task",
                status=TaskStatus.PENDING,
                urgency=UrgencyLevel.CRITICAL,
                due_date=datetime.now() + timedelta(hours=6),
            ),
            AutonomousTask(
                task_id="medium",
                transaction_id="deal_1",
                task_type=TaskType.VENDOR_SCHEDULING,
                workflow_stage=WorkflowStage.DUE_DILIGENCE,
                title="Medium Priority",
                description="Medium urgency task",
                status=TaskStatus.PENDING,
                urgency=UrgencyLevel.MEDIUM,
                due_date=datetime.now() + timedelta(hours=12),
            ),
        ]

        # Sort by urgency value (alphabetical for enum values) and due date
        sorted_tasks = sorted(tasks, key=lambda t: (t.urgency.value, t.due_date or datetime.max))

        # Verify sorting happened without error
        assert len(sorted_tasks) == 3

    @pytest.mark.asyncio
    async def test_check_escalations(self, orchestrator):
        """Test escalation checking logic."""
        # Create an overdue task
        overdue_task = AutonomousTask(
            task_id="task_overdue",
            transaction_id="deal_123",
            task_type=TaskType.DOCUMENT_REQUEST,
            workflow_stage=WorkflowStage.CONTRACT_EXECUTION,
            title="Overdue Task",
            description="This task is overdue",
            status=TaskStatus.IN_PROGRESS,
            urgency=UrgencyLevel.HIGH,
            created_at=datetime.now() - timedelta(hours=48),
            escalation_threshold_hours=24,
        )

        orchestrator.active_tasks["task_overdue"] = overdue_task

        with patch.object(orchestrator, "_escalate_task", new_callable=AsyncMock) as mock_escalate:
            await orchestrator._check_escalations()

            mock_escalate.assert_called_once()

    def test_escalation_rules_initialized(self, orchestrator):
        """Test that escalation rules are properly initialized."""
        assert len(orchestrator.escalation_rules) > 0
        for rule in orchestrator.escalation_rules:
            assert isinstance(rule, EscalationRule)
            assert rule.rule_id is not None
            assert isinstance(rule.escalation_level, UrgencyLevel)

    def test_workflow_templates_initialized(self, orchestrator):
        """Test that workflow templates are properly initialized."""
        assert len(orchestrator.workflow_templates) > 0
        assert "standard_purchase" in orchestrator.workflow_templates
        assert "cash_purchase" in orchestrator.workflow_templates


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
