import pytest
pytestmark = pytest.mark.integration

"""
Comprehensive tests for Exception Escalation Engine.
Tests cover exception detection, classification, resolution strategies, and escalation workflows.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

@pytest.mark.integration

try:
    from ghl_real_estate_ai.services.exception_escalation_engine import (
        EscalationLevel,
        ExceptionEscalationEngine,
        ExceptionRecord,
        ExceptionType,
        ResolutionStatus,
        ResolutionStrategy,
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestExceptionRecord:
    """Test ExceptionRecord dataclass functionality."""

    def test_exception_record_creation(self):
        """Test exception record creation with all fields."""
        record = ExceptionRecord(
            id="exc_001",
            deal_id="deal_123",
            exception_type=ExceptionType.BUSINESS_LOGIC_ERROR,
            severity="high",
            title="Financing Qualification Issue",
            description="Client's debt-to-income ratio exceeds lender requirements",
            source_component="financing_verification",
            detected_at=datetime.now(),
            escalation_level=EscalationLevel.AGENT_REVIEW,
            resolution_status=ResolutionStatus.IN_PROGRESS,
            metadata={
                "lender_requirements": {"max_dti": 0.43},
                "client_current": {"dti": 0.48},
                "suggested_solutions": ["increase_down_payment", "find_alternative_lender"],
            },
            context_data={"property_value": 450000, "loan_amount": 360000, "client_income": 85000},
        )

        assert record.id == "exc_001"
        assert record.exception_type == ExceptionType.BUSINESS_LOGIC_ERROR
        assert record.severity == "high"
        assert record.escalation_level == EscalationLevel.AGENT_REVIEW
        assert record.metadata["client_current"]["dti"] == 0.48

    def test_exception_record_serialization(self):
        """Test exception record serialization."""
        record = ExceptionRecord(
            id="exc_002",
            deal_id="deal_456",
            exception_type=ExceptionType.EXTERNAL_SERVICE_ERROR,
            severity="medium",
            title="Appraisal Service Timeout",
            description="Appraisal ordering service is not responding",
            source_component="vendor_coordination",
            detected_at=datetime.now(),
            escalation_level=EscalationLevel.SYSTEM_RECOVERY,
            resolution_status=ResolutionStatus.PENDING,
        )

        record_dict = record.__dict__
        assert record_dict["id"] == "exc_002"
        assert record_dict["exception_type"] == ExceptionType.EXTERNAL_SERVICE_ERROR
        assert isinstance(record_dict["detected_at"], datetime)


class TestResolutionStrategy:
    """Test ResolutionStrategy dataclass functionality."""

    def test_resolution_strategy_creation(self):
        """Test resolution strategy creation."""
        strategy = ResolutionStrategy(
            id="strategy_001",
            name="Document Re-collection Strategy",
            description="Automated strategy for re-collecting failed document uploads",
            exception_types=[ExceptionType.DOCUMENT_PROCESSING_ERROR],
            automated_steps=["retry_document_upload", "validate_file_format", "notify_client_if_failed"],
            escalation_triggers=["max_retries_exceeded", "client_non_responsive_24h"],
            success_criteria=["document_successfully_processed", "validation_passed"],
            estimated_resolution_time=timedelta(hours=2),
            success_rate=0.87,
            metadata={
                "max_retry_attempts": 3,
                "supported_formats": ["pdf", "jpg", "png"],
                "fallback_method": "manual_collection",
            },
        )

        assert strategy.id == "strategy_001"
        assert len(strategy.automated_steps) == 3
        assert ExceptionType.DOCUMENT_PROCESSING_ERROR in strategy.exception_types
        assert strategy.success_rate == 0.87
        assert strategy.estimated_resolution_time == timedelta(hours=2)


class TestExceptionEscalationEngine:
    """Test the main exception escalation functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for exception engine."""
        return {
            "cache_service": AsyncMock(),
            "ghl_service": AsyncMock(),
            "claude_service": AsyncMock(),
            "notification_service": AsyncMock(),
            "recovery_service": AsyncMock(),
        }

    @pytest.fixture
    def engine(self, mock_dependencies):
        """Create exception engine instance with mocked dependencies."""
        return ExceptionEscalationEngine(
            cache_service=mock_dependencies["cache_service"],
            ghl_service=mock_dependencies["ghl_service"],
            claude_service=mock_dependencies["claude_service"],
        )

    @pytest.mark.asyncio
    async def test_report_exception_success(self, engine, mock_dependencies):
        """Test successful exception reporting and initial processing."""
        exception_data = {
            "deal_id": "deal_123",
            "component": "document_orchestration",
            "error_type": "document_validation_failed",
            "error_message": "Purchase agreement missing required signatures",
            "severity": "high",
            "context": {
                "document_id": "doc_456",
                "validation_errors": ["buyer_signature_missing", "date_incomplete"],
                "attempted_at": "2024-01-20T14:30:00",
            },
            "auto_recovery_attempted": False,
        }

        # Mock AI classification
        mock_dependencies["claude_service"].generate_response.return_value = {
            "classification_result": {
                "exception_type": "business_logic_error",
                "severity_confirmation": "high",
                "escalation_recommendation": "agent_review",
                "resolution_strategy": "document_re_collection",
                "estimated_impact": "moderate_delay",
                "urgency_score": 0.75,
            }
        }

        # Mock strategy lookup
        mock_strategy = ResolutionStrategy(
            id="strategy_doc_recollection",
            name="Document Re-collection",
            description="Re-collect missing signatures",
            exception_types=[ExceptionType.DOCUMENT_PROCESSING_ERROR],
            automated_steps=["send_signature_request", "set_reminder"],
            escalation_triggers=["no_response_48h"],
            success_criteria=["signatures_received"],
            estimated_resolution_time=timedelta(hours=24),
            success_rate=0.82,
        )

        with patch.object(engine, "_get_resolution_strategy", return_value=mock_strategy):
            result = await engine.report_exception(exception_data)

        assert result["success"] is True
        assert result["exception_id"] is not None
        assert result["escalation_level"] == "agent_review"
        assert result["resolution_strategy_id"] == "strategy_doc_recollection"
        assert result["estimated_resolution_time"] == "24 hours"

        # Verify classification and storage
        mock_dependencies["claude_service"].generate_response.assert_called_once()
        mock_dependencies["cache_service"].set.assert_called()

    @pytest.mark.asyncio
    async def test_escalate_to_human_success(self, engine, mock_dependencies):
        """Test successful escalation to human intervention."""
        escalation_data = {
            "exception_id": "exc_escalate_test",
            "current_level": "system_recovery",
            "escalation_reason": "automated_resolution_failed_multiple_attempts",
            "urgency": "high",
            "additional_context": {
                "attempts_made": 3,
                "last_attempt_error": "External service still unavailable",
                "business_impact": "Closing scheduled in 2 days",
            },
        }

        # Mock existing exception
        mock_exception = ExceptionRecord(
            id="exc_escalate_test",
            deal_id="deal_urgent",
            exception_type=ExceptionType.EXTERNAL_SERVICE_ERROR,
            severity="high",
            title="Title Company API Unavailable",
            description="Cannot access title search results",
            source_component="vendor_coordination",
            detected_at=datetime.now() - timedelta(hours=4),
            escalation_level=EscalationLevel.SYSTEM_RECOVERY,
            resolution_status=ResolutionStatus.FAILED_AUTO_RECOVERY,
        )

        mock_dependencies["cache_service"].get.return_value = mock_exception

        # Mock human escalation workflow
        mock_dependencies["ghl_service"].create_urgent_task.return_value = {
            "success": True,
            "task_id": "task_urgent_123",
            "assigned_to": "senior_agent_mike",
            "priority": "high",
        }

        mock_dependencies["notification_service"].send_escalation_alert.return_value = {
            "success": True,
            "alert_id": "alert_456",
            "recipients_notified": ["manager", "senior_agent"],
        }

        result = await engine.escalate_to_human(escalation_data)

        assert result["success"] is True
        assert result["escalation_level"] == "human_intervention"
        assert result["task_created"] is True
        assert result["notifications_sent"] is True
        assert result["assigned_to"] == "senior_agent_mike"

        # Verify escalation actions
        mock_dependencies["ghl_service"].create_urgent_task.assert_called_once()
        mock_dependencies["notification_service"].send_escalation_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_resolution_strategy_success(self, engine, mock_dependencies):
        """Test successful execution of resolution strategy."""
        strategy_execution_data = {
            "exception_id": "exc_strategy_test",
            "strategy_id": "strategy_vendor_retry",
            "execution_context": {
                "vendor_id": "vendor_123",
                "service_type": "appraisal",
                "original_request_time": "2024-01-20T10:00:00",
            },
        }

        # Mock resolution strategy
        mock_strategy = ResolutionStrategy(
            id="strategy_vendor_retry",
            name="Vendor Service Retry",
            description="Retry vendor service with escalated priority",
            exception_types=[ExceptionType.EXTERNAL_SERVICE_ERROR],
            automated_steps=["check_vendor_status", "retry_with_priority", "find_alternative_vendor_if_failed"],
            escalation_triggers=["all_vendors_unavailable"],
            success_criteria=["service_request_accepted"],
            estimated_resolution_time=timedelta(hours=1),
            success_rate=0.78,
        )

        mock_dependencies["cache_service"].get.return_value = mock_strategy

        # Mock strategy execution steps
        execution_results = [
            {"step": "check_vendor_status", "result": "available", "success": True},
            {"step": "retry_with_priority", "result": "request_accepted", "success": True},
        ]

        with patch.object(engine, "_execute_strategy_step", side_effect=execution_results):
            result = await engine._execute_resolution_strategy(strategy_execution_data)

        assert result["success"] is True
        assert result["steps_executed"] == 2
        assert result["strategy_completed"] is True
        assert result["resolution_achieved"] is True

    @pytest.mark.asyncio
    async def test_ai_exception_classification(self, engine, mock_dependencies):
        """Test AI-powered exception classification and analysis."""
        exception_details = {
            "error_message": "Connection timeout: Unable to reach lender API endpoint",
            "stack_trace": "requests.exceptions.ConnectTimeout at line 142",
            "component": "financing_verification",
            "timestamp": "2024-01-20T15:45:00",
            "request_data": {"loan_application_id": "loan_789", "verification_type": "income"},
            "system_state": {"api_health": "degraded", "retry_count": 3},
        }

        # Mock comprehensive AI analysis
        mock_dependencies["claude_service"].generate_response.return_value = {
            "classification_analysis": {
                "primary_type": "external_service_error",
                "secondary_types": ["network_connectivity", "api_timeout"],
                "severity_assessment": {
                    "level": "medium",
                    "justification": "Service degradation but alternative paths available",
                    "business_impact": "potential_delay",
                },
                "root_cause_analysis": {
                    "likely_cause": "lender_api_overload",
                    "contributing_factors": ["peak_traffic_time", "api_rate_limiting"],
                    "confidence": 0.82,
                },
                "resolution_recommendations": [
                    {
                        "strategy": "retry_with_exponential_backoff",
                        "probability_success": 0.75,
                        "estimated_time": "15_minutes",
                    },
                    {
                        "strategy": "use_alternative_lender_api",
                        "probability_success": 0.90,
                        "estimated_time": "30_minutes",
                    },
                ],
                "escalation_criteria": {
                    "escalate_if": ["retry_fails_3_times", "alternative_api_also_fails"],
                    "escalate_to": "agent_review",
                    "urgency_factors": ["closing_proximity", "client_expectations"],
                },
            }
        }

        result = await engine._classify_exception_with_ai(exception_details)

        assert result["primary_type"] == "external_service_error"
        assert result["severity_assessment"]["level"] == "medium"
        assert result["root_cause_analysis"]["confidence"] == 0.82
        assert len(result["resolution_recommendations"]) == 2
        assert result["resolution_recommendations"][0]["strategy"] == "retry_with_exponential_backoff"

    @pytest.mark.asyncio
    async def test_exception_pattern_detection(self, engine, mock_dependencies):
        """Test detection of exception patterns and trends."""
        pattern_analysis_request = {
            "time_window": "last_7_days",
            "deal_ids": ["deal_001", "deal_002", "deal_003"],
            "component_filter": None,  # Analyze all components
        }

        # Mock historical exception data
        mock_exceptions = [
            {
                "deal_id": "deal_001",
                "exception_type": "external_service_error",
                "component": "vendor_coordination",
                "timestamp": "2024-01-15T10:30:00",
                "resolved": True,
                "resolution_time": 45,  # minutes
            },
            {
                "deal_id": "deal_002",
                "exception_type": "external_service_error",
                "component": "vendor_coordination",
                "timestamp": "2024-01-16T14:20:00",
                "resolved": True,
                "resolution_time": 60,
            },
            {
                "deal_id": "deal_003",
                "exception_type": "document_processing_error",
                "component": "document_orchestration",
                "timestamp": "2024-01-17T09:15:00",
                "resolved": False,
                "escalated_to_human": True,
            },
        ]

        mock_dependencies["cache_service"].get.return_value = mock_exceptions

        # Mock AI pattern analysis
        mock_dependencies["claude_service"].generate_response.return_value = {
            "pattern_analysis": {
                "detected_patterns": [
                    {
                        "pattern": "recurring_vendor_api_timeouts",
                        "frequency": "2_per_day_last_3_days",
                        "confidence": 0.88,
                        "suggested_action": "implement_vendor_circuit_breaker",
                    }
                ],
                "trend_analysis": {
                    "exception_rate_trend": "increasing",
                    "resolution_time_trend": "stable",
                    "escalation_rate_trend": "concerning_increase",
                },
                "recommendations": [
                    "implement_proactive_vendor_health_monitoring",
                    "create_vendor_backup_strategies",
                    "enhance_auto_recovery_capabilities",
                ],
            }
        }

        result = await engine.analyze_exception_patterns(pattern_analysis_request)

        assert len(result["detected_patterns"]) == 1
        assert result["detected_patterns"][0]["pattern"] == "recurring_vendor_api_timeouts"
        assert result["trend_analysis"]["escalation_rate_trend"] == "concerning_increase"
        assert "implement_proactive_vendor_health_monitoring" in result["recommendations"]

    @pytest.mark.asyncio
    async def test_recovery_workflow_execution(self, engine, mock_dependencies):
        """Test automated recovery workflow execution."""
        recovery_request = {
            "exception_id": "exc_recovery_test",
            "recovery_type": "service_restoration",
            "target_component": "document_orchestration",
            "recovery_parameters": {"restart_services": True, "clear_cache": True, "validate_connections": True},
        }

        # Mock recovery service responses
        recovery_steps = [
            {"action": "stop_service", "result": "success", "duration": 5},
            {"action": "clear_cache", "result": "success", "duration": 10},
            {"action": "validate_connections", "result": "success", "duration": 15},
            {"action": "restart_service", "result": "success", "duration": 20},
            {"action": "health_check", "result": "healthy", "duration": 10},
        ]

        mock_dependencies["recovery_service"].execute_recovery_workflow.return_value = {
            "success": True,
            "total_duration": 60,  # seconds
            "steps_completed": 5,
            "service_status": "healthy",
            "recovery_details": recovery_steps,
        }

        result = await engine.execute_recovery_workflow(recovery_request)

        assert result["success"] is True
        assert result["recovery_completed"] is True
        assert result["service_status"] == "healthy"
        assert result["total_duration"] == 60

        # Verify recovery execution
        mock_dependencies["recovery_service"].execute_recovery_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_exception_metrics_tracking(self, engine, mock_dependencies):
        """Test exception metrics and performance tracking."""
        metrics_request = {
            "time_period": "last_30_days",
            "group_by": ["exception_type", "component", "severity"],
            "include_trends": True,
        }

        # Mock metrics data
        mock_metrics = {
            "total_exceptions": 156,
            "exceptions_by_type": {
                "external_service_error": 78,
                "document_processing_error": 45,
                "business_logic_error": 23,
                "system_error": 10,
            },
            "exceptions_by_component": {
                "vendor_coordination": 68,
                "document_orchestration": 52,
                "financing_verification": 24,
                "communication_engine": 12,
            },
            "resolution_metrics": {
                "auto_resolved": 124,
                "escalated_to_human": 32,
                "average_resolution_time": 45,  # minutes
                "success_rate": 79.5,  # percentage
            },
            "trends": {
                "exception_rate_change": "+12%",
                "resolution_time_change": "-8%",
                "escalation_rate_change": "+15%",
            },
        }

        mock_dependencies["cache_service"].get.return_value = mock_metrics

        result = await engine.get_exception_metrics(metrics_request)

        assert result["total_exceptions"] == 156
        assert result["exceptions_by_type"]["external_service_error"] == 78
        assert result["resolution_metrics"]["success_rate"] == 79.5
        assert result["trends"]["resolution_time_change"] == "-8%"

    @pytest.mark.asyncio
    async def test_proactive_exception_prevention(self, engine, mock_dependencies):
        """Test proactive exception prevention mechanisms."""
        prevention_analysis = {
            "deal_id": "deal_prevention_test",
            "upcoming_milestones": ["appraisal_due", "financing_deadline"],
            "risk_factors": {
                "vendor_availability": "limited",
                "financing_complexity": "high",
                "timeline_pressure": "moderate",
            },
            "historical_patterns": {
                "similar_deals_exception_rate": 0.35,
                "common_failure_points": ["vendor_scheduling", "document_delays"],
            },
        }

        # Mock AI risk assessment
        mock_dependencies["claude_service"].generate_response.return_value = {
            "risk_assessment": {
                "overall_risk_score": 0.72,
                "high_risk_areas": [
                    {
                        "area": "vendor_scheduling",
                        "risk_score": 0.85,
                        "prevention_actions": ["book_backup_vendors", "extend_scheduling_window"],
                    },
                    {
                        "area": "financing_timeline",
                        "risk_score": 0.68,
                        "prevention_actions": ["expedite_document_collection", "lender_communication"],
                    },
                ],
                "recommended_preventive_measures": [
                    "implement_vendor_contingency_plan",
                    "accelerate_document_workflow",
                    "increase_communication_frequency",
                ],
            }
        }

        result = await engine.analyze_exception_prevention_opportunities(prevention_analysis)

        assert result["overall_risk_score"] == 0.72
        assert len(result["high_risk_areas"]) == 2
        assert result["high_risk_areas"][0]["area"] == "vendor_scheduling"
        assert "implement_vendor_contingency_plan" in result["recommended_preventive_measures"]

    def test_severity_calculation(self, engine):
        """Test exception severity calculation logic."""
        # High severity: Business impact + time pressure
        high_severity_context = {
            "business_impact": "closing_at_risk",
            "days_to_closing": 1,
            "client_expectations": "high",
            "financial_impact": 5000,
        }

        severity = engine._calculate_exception_severity(ExceptionType.BUSINESS_LOGIC_ERROR, high_severity_context)
        assert severity == "high"

        # Low severity: Minor issue with time buffer
        low_severity_context = {
            "business_impact": "minor_delay",
            "days_to_closing": 15,
            "client_expectations": "flexible",
            "financial_impact": 0,
        }

        severity = engine._calculate_exception_severity(ExceptionType.SYSTEM_ERROR, low_severity_context)
        assert severity == "low"

    def test_escalation_threshold_logic(self, engine):
        """Test escalation threshold decision logic."""
        # Should escalate: Multiple failures + time pressure
        escalation_context = {
            "retry_count": 3,
            "time_since_first_attempt": 120,  # minutes
            "business_criticality": "high",
            "auto_recovery_success_rate": 0.2,
        }

        should_escalate = engine._should_escalate_to_human(escalation_context)
        assert should_escalate is True

        # Should not escalate: Recent issue with good recovery rate
        no_escalation_context = {
            "retry_count": 1,
            "time_since_first_attempt": 5,
            "business_criticality": "low",
            "auto_recovery_success_rate": 0.9,
        }

        should_escalate = engine._should_escalate_to_human(no_escalation_context)
        assert should_escalate is False


class TestExceptionIntegration:
    """Integration tests for exception escalation workflows."""

    @pytest.mark.asyncio
    async def test_complete_exception_lifecycle(self):
        """Test complete exception lifecycle from detection to resolution."""
        # Integration test placeholder
        pass

    @pytest.mark.asyncio
    async def test_multi_exception_coordination(self):
        """Test coordination of multiple related exceptions."""
        # Integration test placeholder
        pass

    @pytest.mark.asyncio
    async def test_exception_recovery_under_load(self):
        """Test exception handling under high load conditions."""
        # Integration test placeholder
        pass