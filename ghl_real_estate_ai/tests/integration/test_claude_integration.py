"""
Claude Services Integration Tests

Comprehensive integration tests for all Claude services to validate
end-to-end functionality, coordination, and performance.

Created: January 2026
Author: Enterprise Development Team
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

# Import Claude services
from ghl_real_estate_ai.services.claude_agent_orchestrator import (
    ClaudeAgentOrchestrator,
    AgentRole,
    TaskPriority
)
from ghl_real_estate_ai.services.claude_enterprise_intelligence import (
    ClaudeEnterpriseIntelligence
)
from ghl_real_estate_ai.services.claude_business_intelligence_automation import (
    ClaudeBusinessIntelligenceAutomation
)
from ghl_real_estate_ai.services.claude_api_integration import (
    ClaudeAPIIntegration
)
from ghl_real_estate_ai.services.claude_management_orchestration import (
    ClaudeManagementOrchestration,
    ServiceLifecycleState
)

@pytest.fixture(scope="session")
async def claude_services():
    """Initialize Claude services for testing."""
    services = {
        'orchestrator': ClaudeAgentOrchestrator(),
        'intelligence': ClaudeEnterpriseIntelligence(),
        'business': ClaudeBusinessIntelligenceAutomation(),
        'api': ClaudeAPIIntegration(),
        'management': ClaudeManagementOrchestration()
    }

    # Initialize all services
    for service in services.values():
        if hasattr(service, 'initialize'):
            await service.initialize()

    yield services

    # Cleanup
    for service in services.values():
        if hasattr(service, 'shutdown'):
            await service.shutdown()

@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        "lead_id": str(uuid.uuid4()),
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
        "budget": 500000,
        "location": "Austin, TX",
        "property_type": "single_family",
        "bedrooms": 3,
        "bathrooms": 2,
        "square_footage": 2000,
        "timeline": "3_months",
        "source": "website_form"
    }

@pytest.fixture
def sample_workflow_request():
    """Sample workflow request for testing coordination."""
    return {
        "workflow_type": "lead_processing",
        "priority": "high",
        "data": {
            "lead_id": str(uuid.uuid4()),
            "actions": ["score_lead", "match_properties", "generate_insights"]
        },
        "requirements": {
            "response_time_target": 5000,  # 5 seconds
            "accuracy_threshold": 0.95
        }
    }

class TestClaudeServicesIntegration:
    """Integration tests for Claude services."""

    @pytest.mark.asyncio
    async def test_services_initialization(self, claude_services):
        """Test that all Claude services initialize correctly."""
        # Verify all services are available
        assert 'orchestrator' in claude_services
        assert 'intelligence' in claude_services
        assert 'business' in claude_services
        assert 'api' in claude_services
        assert 'management' in claude_services

        # Verify services have expected attributes
        orchestrator = claude_services['orchestrator']
        assert hasattr(orchestrator, 'submit_task')
        assert hasattr(orchestrator, 'coordinate_agents')

        intelligence = claude_services['intelligence']
        assert hasattr(intelligence, 'analyze_system_health')
        assert hasattr(intelligence, 'optimize_system_performance')

        business = claude_services['business']
        assert hasattr(business, 'generate_executive_report')
        assert hasattr(business, 'generate_real_time_insights')

    @pytest.mark.asyncio
    async def test_agent_task_submission(self, claude_services, sample_lead_data):
        """Test submitting and processing agent tasks."""
        orchestrator = claude_services['orchestrator']

        # Submit a lead scoring task
        task_id = await orchestrator.submit_task(
            task_type="lead_scoring",
            description="Score incoming lead for quality and fit",
            context={"lead_data": sample_lead_data},
            agent_role=AgentRole.BUSINESS_INTELLIGENCE,
            priority=TaskPriority.HIGH
        )

        assert task_id is not None
        assert len(task_id) > 0

        # Check task status
        status = await orchestrator.get_task_status(task_id)
        assert status in ["pending", "processing", "completed"]

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self, claude_services, sample_lead_data):
        """Test coordination between multiple agents."""
        orchestrator = claude_services['orchestrator']

        # Submit multiple related tasks
        task_list = [
            {
                "task_type": "lead_scoring",
                "description": "Score lead quality",
                "context": {"lead_data": sample_lead_data},
                "agent_role": AgentRole.BUSINESS_INTELLIGENCE,
                "priority": TaskPriority.HIGH
            },
            {
                "task_type": "property_matching",
                "description": "Find matching properties",
                "context": {"lead_data": sample_lead_data},
                "agent_role": AgentRole.DATA_SCIENTIST,
                "priority": TaskPriority.NORMAL
            },
            {
                "task_type": "risk_assessment",
                "description": "Assess lead risk factors",
                "context": {"lead_data": sample_lead_data},
                "agent_role": AgentRole.SECURITY_ANALYST,
                "priority": TaskPriority.NORMAL
            }
        ]

        # Coordinate agent tasks
        coordination_result = await orchestrator.coordinate_agents(
            task_list,
            coordination_strategy="parallel_with_synthesis"
        )

        assert coordination_result is not None
        assert "coordination_id" in coordination_result
        assert "status" in coordination_result
        assert coordination_result["status"] in ["initiated", "processing", "completed"]

    @pytest.mark.asyncio
    async def test_enterprise_intelligence_analysis(self, claude_services):
        """Test enterprise intelligence analysis capabilities."""
        intelligence = claude_services['intelligence']

        # Perform system health analysis
        analysis = await intelligence.analyze_system_health()

        assert analysis is not None
        assert hasattr(analysis, 'system_metrics')
        assert hasattr(analysis, 'performance_analysis')
        assert hasattr(analysis, 'recommendations')

        # Verify analysis structure
        assert isinstance(analysis.system_metrics, dict)
        assert len(analysis.recommendations) >= 0

    @pytest.mark.asyncio
    async def test_performance_optimization(self, claude_services):
        """Test performance optimization capabilities."""
        intelligence = claude_services['intelligence']

        # Trigger performance optimization
        optimization = await intelligence.optimize_system_performance()

        assert optimization is not None
        assert hasattr(optimization, 'optimizations')
        assert hasattr(optimization, 'expected_improvements')
        assert isinstance(optimization.optimizations, list)

    @pytest.mark.asyncio
    async def test_business_intelligence_reporting(self, claude_services):
        """Test business intelligence report generation."""
        business = claude_services['business']

        # Generate executive report
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        report = await business.generate_executive_report(start_date, end_date)

        assert report is not None
        assert hasattr(report, 'report_id')
        assert hasattr(report, 'executive_summary')
        assert hasattr(report, 'key_metrics')
        assert hasattr(report, 'recommendations')

        # Verify report content
        assert len(report.report_id) > 0
        assert isinstance(report.key_metrics, dict)

    @pytest.mark.asyncio
    async def test_real_time_insights_generation(self, claude_services):
        """Test real-time business insights generation."""
        business = claude_services['business']

        # Generate real-time insights
        insights = await business.generate_real_time_insights()

        assert insights is not None
        assert isinstance(insights, list)

        # Verify insight structure if any insights exist
        if insights:
            for insight in insights:
                assert hasattr(insight, 'insight_type')
                assert hasattr(insight, 'content')
                assert hasattr(insight, 'confidence')
                assert hasattr(insight, 'timestamp')

    @pytest.mark.asyncio
    async def test_management_orchestration_workflow(self, claude_services, sample_workflow_request):
        """Test end-to-end workflow orchestration."""
        management = claude_services['management']

        # Coordinate intelligent workflow
        workflow_result = await management.coordinate_intelligent_workflow(
            sample_workflow_request
        )

        assert workflow_result is not None
        assert "workflow_id" in workflow_result
        assert "status" in workflow_result
        assert workflow_result["status"] == "coordinated"

        # Verify workflow components
        assert "analysis" in workflow_result
        assert "coordination_time" in workflow_result

    @pytest.mark.asyncio
    async def test_system_status_monitoring(self, claude_services):
        """Test system status monitoring and health checks."""
        management = claude_services['management']

        # Get system status
        status = await management.get_system_status()

        assert status is not None
        assert hasattr(status, 'overall_state')
        assert hasattr(status, 'services')
        assert hasattr(status, 'active_tasks')
        assert hasattr(status, 'resource_utilization')

        # Verify status structure
        assert isinstance(status.active_tasks, int)
        assert isinstance(status.resource_utilization, dict)

    @pytest.mark.asyncio
    async def test_service_scaling_coordination(self, claude_services):
        """Test service scaling coordination."""
        management = claude_services['management']

        # Trigger system performance optimization
        optimization = await management.optimize_system_performance()

        assert optimization is not None
        assert "optimization_id" in optimization
        assert "optimizations_applied" in optimization
        assert "performance_improvement" in optimization

        # Verify optimization structure
        assert isinstance(optimization["optimizations_applied"], list)

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, claude_services):
        """Test error handling and recovery capabilities."""
        orchestrator = claude_services['orchestrator']

        # Submit a task with invalid data to test error handling
        try:
            task_id = await orchestrator.submit_task(
                task_type="invalid_task_type",
                description="This should trigger error handling",
                context={"invalid": "data"},
                agent_role=AgentRole.BUSINESS_INTELLIGENCE,
                priority=TaskPriority.LOW
            )

            # Even with invalid data, should return a task ID (graceful handling)
            assert task_id is not None

        except Exception as e:
            # If exception is raised, it should be handled gracefully
            assert isinstance(e, (ValueError, TypeError))

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, claude_services, sample_lead_data):
        """Test performance benchmarks for Claude services."""
        orchestrator = claude_services['orchestrator']
        intelligence = claude_services['intelligence']

        # Measure agent task submission performance
        start_time = datetime.utcnow()
        task_id = await orchestrator.submit_task(
            task_type="performance_test",
            description="Performance benchmark test",
            context={"lead_data": sample_lead_data},
            agent_role=AgentRole.PERFORMANCE_ENGINEER,
            priority=TaskPriority.HIGH
        )
        submission_time = (datetime.utcnow() - start_time).total_seconds()

        assert submission_time < 1.0  # Should complete in under 1 second

        # Measure intelligence analysis performance
        start_time = datetime.utcnow()
        analysis = await intelligence.analyze_system_health()
        analysis_time = (datetime.utcnow() - start_time).total_seconds()

        assert analysis_time < 5.0  # Should complete in under 5 seconds

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, claude_services, sample_lead_data):
        """Test concurrent operations across Claude services."""
        orchestrator = claude_services['orchestrator']
        intelligence = claude_services['intelligence']
        business = claude_services['business']

        # Run multiple operations concurrently
        tasks = [
            orchestrator.submit_task(
                task_type=f"concurrent_test_{i}",
                description=f"Concurrent task {i}",
                context={"data": sample_lead_data, "task_id": i},
                agent_role=AgentRole.BUSINESS_INTELLIGENCE,
                priority=TaskPriority.NORMAL
            ) for i in range(5)
        ]

        # Add intelligence and business operations
        tasks.append(intelligence.analyze_system_health())
        tasks.append(business.generate_real_time_insights())

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all tasks completed (may include exceptions for graceful handling)
        assert len(results) == 7

        # Count successful operations
        successful_operations = sum(1 for result in results if not isinstance(result, Exception))
        assert successful_operations >= 5  # At least 5 operations should succeed

class TestClaudeServiceCoordination:
    """Test inter-service coordination and communication."""

    @pytest.mark.asyncio
    async def test_orchestrator_intelligence_coordination(self, claude_services, sample_lead_data):
        """Test coordination between orchestrator and intelligence services."""
        orchestrator = claude_services['orchestrator']
        intelligence = claude_services['intelligence']

        # Submit analysis task through orchestrator
        task_id = await orchestrator.submit_task(
            task_type="system_analysis",
            description="Analyze system for optimization opportunities",
            context={"trigger": "manual_request"},
            agent_role=AgentRole.SYSTEM_ARCHITECT,
            priority=TaskPriority.HIGH
        )

        # Run intelligence analysis
        analysis = await intelligence.analyze_system_health()

        # Both should complete successfully
        assert task_id is not None
        assert analysis is not None

    @pytest.mark.asyncio
    async def test_intelligence_business_integration(self, claude_services):
        """Test integration between intelligence and business services."""
        intelligence = claude_services['intelligence']
        business = claude_services['business']

        # Get intelligence analysis
        analysis = await intelligence.analyze_system_health()

        # Generate business insights
        insights = await business.generate_real_time_insights()

        # Both services should produce results
        assert analysis is not None
        assert insights is not None

    @pytest.mark.asyncio
    async def test_end_to_end_lead_processing(self, claude_services, sample_lead_data):
        """Test complete end-to-end lead processing workflow."""
        orchestrator = claude_services['orchestrator']
        intelligence = claude_services['intelligence']
        business = claude_services['business']
        management = claude_services['management']

        # Step 1: Submit lead for processing
        lead_task_id = await orchestrator.submit_task(
            task_type="lead_processing",
            description="Complete lead processing workflow",
            context={"lead_data": sample_lead_data},
            agent_role=AgentRole.BUSINESS_INTELLIGENCE,
            priority=TaskPriority.HIGH
        )

        # Step 2: Analyze system performance for this workflow
        performance_analysis = await intelligence.analyze_system_health()

        # Step 3: Generate business insights about the lead
        business_insights = await business.generate_real_time_insights()

        # Step 4: Coordinate through management
        workflow_request = {
            "workflow_type": "lead_analysis_complete",
            "lead_id": sample_lead_data["lead_id"],
            "task_id": lead_task_id,
            "analysis_results": "performance_analyzed",
            "business_insights": len(business_insights) if business_insights else 0
        }

        coordination_result = await management.coordinate_intelligent_workflow(workflow_request)

        # Verify end-to-end completion
        assert lead_task_id is not None
        assert performance_analysis is not None
        assert coordination_result is not None
        assert coordination_result["status"] == "coordinated"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])