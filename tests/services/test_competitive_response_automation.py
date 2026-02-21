import pytest

pytestmark = pytest.mark.integration

"""
Comprehensive Tests for Competitive Response Automation Engine

Tests cover:
1. Response rule registration and validation
2. Threat assessment processing and triggering
3. Multi-channel response execution (GHL, Email, SMS)
4. Approval workflows and human oversight
5. Performance tracking and ROI measurement
6. Budget controls and spending limits
7. Error handling and recovery
8. Audit logging and compliance
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.competitive_data_pipeline import (
    CompetitorDataPoint,
    DataSource,
    ThreatAssessment,
    ThreatLevel,
)
from ghl_real_estate_ai.services.competitive_response_automation import (
    ApprovalLevel,
    CompetitiveResponseEngine,
    EmailMarketingExecutor,
    ExecutionChannel,
    GHLCRMExecutor,
    ResponseExecution,
    ResponseRule,
    ResponseStatus,
    ResponseType,
    get_competitive_response_engine,
)


class TestCompetitiveResponseEngine:
    """Test suite for competitive response automation engine"""

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_cache.delete.return_value = True
        return mock_cache

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client"""
        mock_llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = "Response analysis completed successfully"
        mock_llm.generate.return_value = mock_response
        return mock_llm

    @pytest.fixture
    def response_engine(self, mock_cache_service, mock_llm_client):
        """Create response engine with mocked dependencies"""
        engine = CompetitiveResponseEngine()
        engine.cache = mock_cache_service
        engine.llm_client = mock_llm_client
        return engine

    @pytest.fixture
    def sample_threat_assessment(self):
        """Sample threat assessment for testing"""
        return ThreatAssessment(
            threat_id="threat_001",
            competitor_id="comp_001",
            threat_level=ThreatLevel.HIGH,
            threat_type="aggressive_pricing",
            threat_description="Competitor reduced prices by 15%",
            potential_impact="May trigger price competition",
            timeline="immediate",
            recommended_response="Review pricing strategy",
            response_urgency="high",
            confidence_level=0.9,
        )

    @pytest.fixture
    def sample_response_rule(self):
        """Sample response rule for testing"""
        return ResponseRule(
            rule_name="Pricing Response Rule",
            description="Respond to aggressive pricing threats",
            trigger_conditions=[
                {"field": "threat_type", "operator": "equals", "value": "aggressive_pricing"},
                {"field": "price_reduction", "operator": "greater_than", "value": 0.10},
            ],
            threat_level_threshold=ThreatLevel.MEDIUM,
            response_type=ResponseType.PRICING_ADJUSTMENT,
            response_actions=[
                {"type": "price_analysis", "analyze_competitive_position": True, "recommend_pricing_strategy": True}
            ],
            execution_channels=[ExecutionChannel.GHL_CRM],
            approval_level=ApprovalLevel.SUPERVISOR,
            max_budget=Decimal("1000"),
        )

    @pytest.mark.asyncio
    async def test_engine_initialization(self, response_engine):
        """Test response engine initialization"""
        await response_engine.initialize()

        # Verify executors are registered
        assert ExecutionChannel.GHL_CRM in response_engine.executors
        assert ExecutionChannel.EMAIL_MARKETING in response_engine.executors

        # Verify executors are correct type
        assert isinstance(response_engine.executors[ExecutionChannel.GHL_CRM], GHLCRMExecutor)
        assert isinstance(response_engine.executors[ExecutionChannel.EMAIL_MARKETING], EmailMarketingExecutor)

    @pytest.mark.asyncio
    async def test_response_rule_registration(self, response_engine, sample_response_rule):
        """Test registration of response rules"""
        rule_id = await response_engine.register_response_rule(sample_response_rule)

        assert rule_id == sample_response_rule.rule_id
        assert rule_id in response_engine.response_rules
        assert response_engine.response_rules[rule_id] == sample_response_rule

        # Verify rule is cached
        response_engine.cache.set.assert_called()

    @pytest.mark.asyncio
    async def test_response_rule_validation(self, response_engine):
        """Test response rule validation"""
        # Valid rule
        valid_rule = ResponseRule(
            rule_name="Valid Rule",
            description="Valid test rule",
            trigger_conditions=[{"field": "test", "operator": "equals", "value": "value"}],
            response_actions=[{"type": "test_action"}],
            max_budget=Decimal("100"),
        )

        is_valid = await response_engine._validate_response_rule(valid_rule)
        assert is_valid is True

        # Invalid rule - no name
        invalid_rule = ResponseRule(
            rule_name="",
            description="Invalid rule",
            trigger_conditions=[{"field": "test", "operator": "equals", "value": "value"}],
            response_actions=[{"type": "test_action"}],
            max_budget=Decimal("100"),
        )

        is_valid = await response_engine._validate_response_rule(invalid_rule)
        assert is_valid is False

        # Invalid rule - no budget
        invalid_rule_budget = ResponseRule(
            rule_name="Invalid Budget Rule",
            description="Invalid rule",
            trigger_conditions=[{"field": "test", "operator": "equals", "value": "value"}],
            response_actions=[{"type": "test_action"}],
            max_budget=Decimal("0"),
        )

        is_valid = await response_engine._validate_response_rule(invalid_rule_budget)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_threat_assessment_processing(self, response_engine, sample_response_rule, sample_threat_assessment):
        """Test processing of threat assessments"""
        # Register rule first
        await response_engine.register_response_rule(sample_response_rule)

        # Add evidence with trigger data
        evidence = CompetitorDataPoint(
            competitor_id="comp_001",
            data_source=DataSource.PRICE_MONITORING,
            data_type="pricing",
            raw_data={"price_reduction": 0.15},  # 15% reduction
            confidence_score=0.9,
        )
        sample_threat_assessment.evidence = [evidence]

        # Process threat assessment
        executions = await response_engine.process_threat_assessment(sample_threat_assessment)

        assert len(executions) > 0
        execution = executions[0]
        assert execution.threat_id == sample_threat_assessment.threat_id
        assert execution.rule_id == sample_response_rule.rule_id

    @pytest.mark.asyncio
    async def test_trigger_condition_evaluation(self, response_engine, sample_threat_assessment):
        """Test trigger condition evaluation logic"""
        # Test equals condition
        conditions = [{"field": "threat_type", "operator": "equals", "value": "aggressive_pricing"}]
        result = await response_engine._evaluate_trigger_conditions(conditions, sample_threat_assessment)
        assert result is True

        # Test greater_than condition with evidence data
        evidence = CompetitorDataPoint(
            competitor_id="comp_001",
            data_source=DataSource.PRICE_MONITORING,
            data_type="pricing",
            raw_data={"price_reduction": 0.15},
            confidence_score=0.9,
        )
        sample_threat_assessment.evidence = [evidence]

        conditions = [{"field": "price_reduction", "operator": "greater_than", "value": 0.10}]
        result = await response_engine._evaluate_trigger_conditions(conditions, sample_threat_assessment)
        assert result is True

        # Test false condition
        conditions = [{"field": "threat_type", "operator": "equals", "value": "market_expansion"}]
        result = await response_engine._evaluate_trigger_conditions(conditions, sample_threat_assessment)
        assert result is False

    @pytest.mark.asyncio
    async def test_automatic_response_execution(self, response_engine):
        """Test automatic response execution without approval"""
        # Create automatic rule
        auto_rule = ResponseRule(
            rule_name="Auto Response Rule",
            description="Automatic response test",
            trigger_conditions=[{"field": "threat_type", "operator": "equals", "value": "aggressive_pricing"}],
            response_type=ResponseType.DEFENSIVE_MESSAGING,
            response_actions=[{"type": "add_tags", "tags": ["competitive_threat"], "target_leads": ["lead_001"]}],
            execution_channels=[ExecutionChannel.GHL_CRM],
            approval_level=ApprovalLevel.AUTOMATIC,
            max_budget=Decimal("100"),
        )

        await response_engine.register_response_rule(auto_rule)

        # Create threat that matches rule
        threat = ThreatAssessment(
            threat_id="threat_auto",
            competitor_id="comp_001",
            threat_level=ThreatLevel.HIGH,
            threat_type="aggressive_pricing",
            threat_description="Test threat",
            confidence_level=0.9,
        )

        # Process threat
        executions = await response_engine.process_threat_assessment(threat)

        assert len(executions) > 0
        execution = executions[0]
        assert execution.status in [ResponseStatus.IN_PROGRESS, ResponseStatus.COMPLETED]

    @pytest.mark.asyncio
    async def test_approval_workflow(self, response_engine):
        """Test approval workflow for high-level responses"""
        # Create rule requiring supervisor approval
        approval_rule = ResponseRule(
            rule_name="Approval Required Rule",
            description="Rule requiring approval",
            trigger_conditions=[{"field": "threat_type", "operator": "equals", "value": "market_expansion"}],
            response_type=ResponseType.MARKETING_CAMPAIGN,
            response_actions=[{"type": "trigger_campaign", "campaign_id": "defensive", "budget": 500}],
            execution_channels=[ExecutionChannel.EMAIL_MARKETING],
            approval_level=ApprovalLevel.SUPERVISOR,
            max_budget=Decimal("1000"),
        )

        await response_engine.register_response_rule(approval_rule)

        # Create threat
        threat = ThreatAssessment(
            threat_id="threat_approval",
            competitor_id="comp_001",
            threat_level=ThreatLevel.HIGH,
            threat_type="market_expansion",
            threat_description="Competitor expanding",
            confidence_level=0.9,
        )

        # Process threat
        executions = await response_engine.process_threat_assessment(threat)

        assert len(executions) > 0
        execution = executions[0]
        assert execution.status == ResponseStatus.PENDING
        assert execution.approval_level == ApprovalLevel.SUPERVISOR

        # Test approval process
        approval_success = await response_engine.approve_response_execution(
            execution.execution_id, approved_by="supervisor_001", approval_notes="Approved for competitive defense"
        )

        assert approval_success is True
        assert execution.status in [ResponseStatus.APPROVED, ResponseStatus.IN_PROGRESS, ResponseStatus.COMPLETED]
        assert execution.approved_by == "supervisor_001"

    @pytest.mark.asyncio
    async def test_budget_constraints(self, response_engine):
        """Test budget constraint enforcement"""
        # Create rule with small budget
        budget_rule = ResponseRule(
            rule_name="Budget Constrained Rule",
            description="Rule with budget limit",
            trigger_conditions=[{"field": "threat_type", "operator": "equals", "value": "aggressive_pricing"}],
            response_type=ResponseType.MARKETING_CAMPAIGN,
            response_actions=[{"type": "expensive_action", "cost": 1000}],
            execution_channels=[ExecutionChannel.EMAIL_MARKETING],
            max_budget=Decimal("500"),  # Budget limit
            total_cost=Decimal("500"),  # Already at limit
        )

        await response_engine.register_response_rule(budget_rule)

        # Create threat
        threat = ThreatAssessment(
            threat_id="threat_budget",
            competitor_id="comp_001",
            threat_level=ThreatLevel.HIGH,
            threat_type="aggressive_pricing",
            threat_description="Budget test threat",
            confidence_level=0.9,
        )

        # Should trigger rule but not execute due to budget
        executions = await response_engine.process_threat_assessment(threat)

        # Should not create execution due to budget constraint
        budget_exceeded_executions = [e for e in executions if e.rule_id == budget_rule.rule_id]
        assert len(budget_exceeded_executions) == 0

    @pytest.mark.asyncio
    async def test_execution_rate_limiting(self, response_engine):
        """Test execution rate limiting per rule"""
        # Create rule with low daily limit
        rate_limited_rule = ResponseRule(
            rule_name="Rate Limited Rule",
            description="Rule with execution limits",
            trigger_conditions=[{"field": "threat_type", "operator": "equals", "value": "test_threat"}],
            response_type=ResponseType.CUSTOMER_OUTREACH,
            response_actions=[{"type": "send_message"}],
            max_executions_per_day=2,  # Only 2 per day
            max_budget=Decimal("1000"),
        )

        await response_engine.register_response_rule(rate_limited_rule)

        # Create multiple threats
        threats = [
            ThreatAssessment(
                threat_id=f"threat_rate_{i}",
                competitor_id="comp_001",
                threat_level=ThreatLevel.MEDIUM,
                threat_type="test_threat",
                threat_description=f"Rate test threat {i}",
                confidence_level=0.8,
            )
            for i in range(5)  # Try to trigger 5 times
        ]

        executed_count = 0
        for threat in threats:
            executions = await response_engine.process_threat_assessment(threat)
            rate_limited_executions = [e for e in executions if e.rule_id == rate_limited_rule.rule_id]
            executed_count += len(rate_limited_executions)

        # Should only execute 2 times due to rate limiting
        assert executed_count <= 2

    @pytest.mark.asyncio
    async def test_cooldown_period_enforcement(self, response_engine):
        """Test cooldown period between executions"""
        # Create rule with cooldown period
        cooldown_rule = ResponseRule(
            rule_name="Cooldown Rule",
            description="Rule with cooldown period",
            trigger_conditions=[{"field": "threat_type", "operator": "equals", "value": "cooldown_test"}],
            response_type=ResponseType.DEFENSIVE_MESSAGING,
            response_actions=[{"type": "send_message"}],
            cooldown_hours=24,  # 24 hour cooldown
            max_budget=Decimal("1000"),
        )

        await response_engine.register_response_rule(cooldown_rule)

        # Add a recent execution to history to simulate cooldown
        recent_execution = ResponseExecution(
            rule_id=cooldown_rule.rule_id,
            threat_id="threat_prev",
            status=ResponseStatus.COMPLETED,
            completed_at=datetime.now() - timedelta(hours=12),  # 12 hours ago
        )
        response_engine.execution_history.append(recent_execution)

        # Create new threat
        threat = ThreatAssessment(
            threat_id="threat_cooldown",
            competitor_id="comp_001",
            threat_level=ThreatLevel.MEDIUM,
            threat_type="cooldown_test",
            threat_description="Cooldown test threat",
            confidence_level=0.8,
        )

        # Should not execute due to cooldown
        executions = await response_engine.process_threat_assessment(threat)
        cooldown_executions = [e for e in executions if e.rule_id == cooldown_rule.rule_id]

        assert len(cooldown_executions) == 0


class TestGHLCRMExecutor:
    """Test suite for GHL CRM executor"""

    @pytest.fixture
    def ghl_executor(self):
        """Create GHL CRM executor"""
        return GHLCRMExecutor()

    @pytest.fixture
    def sample_execution(self):
        """Sample execution for testing"""
        return ResponseExecution(
            execution_id="exec_test",
            rule_id="rule_test",
            threat_id="threat_test",
            response_type=ResponseType.CUSTOMER_OUTREACH,
        )

    @pytest.mark.asyncio
    async def test_tag_addition_execution(self, ghl_executor, sample_execution):
        """Test GHL tag addition execution"""
        action = {
            "type": "add_tags",
            "target_leads": ["lead_001", "lead_002", "lead_003"],
            "tags": ["competitive_threat", "high_priority"],
        }

        result = await ghl_executor.execute_action(action, sample_execution)

        assert result["success"] is True
        assert result["leads_updated"] == 3
        assert result["tags_added"] == ["competitive_threat", "high_priority"]
        assert result["cost"] == 0  # Tags should be free

    @pytest.mark.asyncio
    async def test_campaign_trigger_execution(self, ghl_executor, sample_execution):
        """Test GHL campaign trigger execution"""
        action = {
            "type": "trigger_campaign",
            "campaign_id": "defensive_campaign_001",
            "target_audience": "at_risk_leads",
            "estimated_reach": 150,
            "cost": 75,
        }

        result = await ghl_executor.execute_action(action, sample_execution)

        assert result["success"] is True
        assert result["campaign_id"] == "defensive_campaign_001"
        assert result["target_audience"] == "at_risk_leads"
        assert result["estimated_reach"] == 150
        assert result["cost"] == Decimal("75")

    @pytest.mark.asyncio
    async def test_opportunity_creation_execution(self, ghl_executor, sample_execution):
        """Test GHL opportunity creation execution"""
        action = {
            "type": "create_opportunity",
            "opportunity_data": {"name": "Competitive Response Opportunity", "value": 5000, "stage": "qualification"},
        }

        result = await ghl_executor.execute_action(action, sample_execution)

        assert result["success"] is True
        assert "opportunity_id" in result
        assert result["opportunity_value"] == 5000
        assert result["cost"] == 0

    @pytest.mark.asyncio
    async def test_unknown_action_handling(self, ghl_executor, sample_execution):
        """Test handling of unknown action types"""
        action = {"type": "unknown_action", "some_parameter": "test_value"}

        result = await ghl_executor.execute_action(action, sample_execution)

        assert result["success"] is False
        assert "Unknown action type" in result["error"]


class TestEmailMarketingExecutor:
    """Test suite for email marketing executor"""

    @pytest.fixture
    def email_executor(self):
        """Create email marketing executor"""
        return EmailMarketingExecutor()

    @pytest.fixture
    def sample_execution(self):
        """Sample execution for testing"""
        return ResponseExecution(
            execution_id="exec_email_test",
            rule_id="rule_email_test",
            threat_id="threat_email_test",
            response_type=ResponseType.MARKETING_CAMPAIGN,
        )

    @pytest.mark.asyncio
    async def test_competitive_alert_email(self, email_executor, sample_execution):
        """Test competitive alert email execution"""
        action = {
            "type": "send_competitive_alert",
            "recipients": ["user1@example.com", "user2@example.com", "user3@example.com"],
            "alert_content": "Competitor price reduction detected - immediate action required",
        }

        result = await email_executor.execute_action(action, sample_execution)

        assert result["success"] is True
        assert result["recipients_count"] == 3
        assert result["delivery_rate"] == 0.95
        assert result["cost"] == Decimal("0.06")  # 3 emails * $0.02

    @pytest.mark.asyncio
    async def test_value_proposition_email(self, email_executor, sample_execution):
        """Test value proposition email execution"""
        action = {
            "type": "value_proposition_email",
            "target_segment": "high_value_leads",
            "template_id": "value_prop_template_001",
        }

        result = await email_executor.execute_action(action, sample_execution)

        assert result["success"] is True
        assert result["target_segment"] == "high_value_leads"
        assert result["template_id"] == "value_prop_template_001"
        assert result["estimated_open_rate"] == 0.28
        assert result["cost"] == Decimal("25.00")


class TestPerformanceMetrics:
    """Test suite for performance metrics and tracking"""

    @pytest.fixture
    def response_engine(self):
        """Create response engine for testing"""
        engine = CompetitiveResponseEngine()
        engine.cache = AsyncMock()
        engine.cache.get.return_value = None
        engine.cache.set.return_value = True
        engine.llm_client = AsyncMock()
        return engine

    @pytest.fixture
    def response_engine_with_history(self):
        """Create response engine with execution history"""
        engine = CompetitiveResponseEngine()

        # Add sample execution history
        for i in range(10):
            execution = ResponseExecution(
                execution_id=f"exec_{i:03d}",
                rule_id=f"rule_{i % 3:03d}",
                threat_id=f"threat_{i:03d}",
                response_type=list(ResponseType)[i % len(ResponseType)],
                status=ResponseStatus.COMPLETED if i % 4 != 3 else ResponseStatus.FAILED,
                cost=Decimal(str(50 + i * 25)),
                execution_duration_ms=1000 + i * 200,
                created_at=datetime.now() - timedelta(hours=i),
            )
            engine.execution_history.append(execution)

        return engine

    @pytest.mark.asyncio
    async def test_performance_metrics_calculation(self, response_engine_with_history):
        """Test performance metrics calculation"""
        metrics = await response_engine_with_history.get_response_performance_metrics()

        # Check overview metrics
        assert "overview" in metrics
        overview = metrics["overview"]

        assert overview["total_responses_executed"] == 10
        assert overview["successful_responses"] == 8  # 8 completed, 2 failed
        assert overview["success_rate"] == 0.8
        assert overview["avg_response_time_ms"] > 0
        assert overview["total_cost"] > 0

        # Check response type breakdown
        assert "response_types" in metrics
        assert len(metrics["response_types"]) > 0

        # Check channel performance
        assert "channel_performance" in metrics

        # Check recent performance
        assert "recent_performance" in metrics
        recent = metrics["recent_performance"]
        assert "executions_24h" in recent
        assert "success_rate_24h" in recent

        # Check cost breakdown
        assert "cost_breakdown" in metrics
        cost_breakdown = metrics["cost_breakdown"]
        assert "total_cost" in cost_breakdown
        assert "by_response_type" in cost_breakdown

        # Check ROI metrics
        assert "roi_metrics" in metrics
        roi = metrics["roi_metrics"]
        assert "total_investment" in roi
        assert "estimated_roi" in roi

    @pytest.mark.asyncio
    async def test_roi_calculation(self, response_engine_with_history):
        """Test ROI calculation accuracy"""
        roi_metrics = await response_engine_with_history._calculate_roi_metrics()

        total_cost = float(sum(e.cost for e in response_engine_with_history.execution_history))
        assert roi_metrics["total_investment"] == total_cost

        # ROI should be positive
        assert roi_metrics["estimated_roi"] > 0
        assert roi_metrics["estimated_revenue_protected"] > total_cost

        # Cost per response should be reasonable
        assert roi_metrics["cost_per_response"] > 0
        assert roi_metrics["average_response_value"] > 0

    def test_singleton_pattern(self):
        """Test singleton pattern for response engine"""
        engine1 = get_competitive_response_engine()
        engine2 = get_competitive_response_engine()

        assert engine1 is engine2

    @pytest.mark.asyncio
    async def test_audit_logging(self, response_engine):
        """Test audit logging functionality"""
        # Create and register rule
        rule = ResponseRule(
            rule_name="Audit Test Rule",
            description="Rule for testing audit logging",
            trigger_conditions=[{"field": "test", "operator": "equals", "value": "audit"}],
            response_type=ResponseType.DEFENSIVE_MESSAGING,
            response_actions=[{"type": "test_action"}],
            approval_level=ApprovalLevel.AUTOMATIC,
            max_budget=Decimal("100"),
        )

        await response_engine.register_response_rule(rule)

        # Create threat and execution
        threat = ThreatAssessment(
            threat_id="threat_audit",
            competitor_id="comp_001",
            threat_level=ThreatLevel.MEDIUM,
            threat_type="test",
            threat_description="Audit test threat",
            confidence_level=0.8,
        )

        # Add evidence with trigger data
        from ghl_real_estate_ai.services.competitive_data_pipeline import CompetitorDataPoint, DataSource

        evidence = CompetitorDataPoint(
            competitor_id="comp_001",
            data_source=DataSource.WEB_SCRAPING,
            data_type="test",
            raw_data={"test": "audit"},
            confidence_score=0.8,
        )
        threat.evidence = [evidence]

        # Process threat
        executions = await response_engine.process_threat_assessment(threat)

        if executions:
            execution = executions[0]

            # Verify audit log entries
            assert len(execution.audit_log) > 0

            # Should have creation entry
            creation_entries = [log for log in execution.audit_log if log["action"] == "created"]
            assert len(creation_entries) > 0

            creation_entry = creation_entries[0]
            assert creation_entry["rule_id"] == rule.rule_id
            assert creation_entry["threat_id"] == threat.threat_id
            assert "timestamp" in creation_entry

    @pytest.mark.asyncio
    async def test_error_handling_in_execution(self, response_engine):
        """Test error handling during response execution"""
        # Create rule that will cause execution error
        error_rule = ResponseRule(
            rule_name="Error Test Rule",
            description="Rule that will cause execution error",
            trigger_conditions=[{"field": "test", "operator": "equals", "value": "error"}],
            response_type=ResponseType.PRICING_ADJUSTMENT,
            response_actions=[{"type": "invalid_action", "invalid_param": "test"}],
            approval_level=ApprovalLevel.AUTOMATIC,
            max_budget=Decimal("100"),
        )

        await response_engine.register_response_rule(error_rule)

        # Create threat
        threat = ThreatAssessment(
            threat_id="threat_error",
            competitor_id="comp_001",
            threat_level=ThreatLevel.MEDIUM,
            threat_type="test",
            threat_description="Error test threat",
            confidence_level=0.8,
        )

        # Add evidence
        from ghl_real_estate_ai.services.competitive_data_pipeline import CompetitorDataPoint, DataSource

        evidence = CompetitorDataPoint(
            competitor_id="comp_001",
            data_source=DataSource.WEB_SCRAPING,
            data_type="test",
            raw_data={"test": "error"},
            confidence_score=0.8,
        )
        threat.evidence = [evidence]

        # Process threat - should not raise exception
        executions = await response_engine.process_threat_assessment(threat)

        # Should still create execution but mark as failed
        if executions:
            execution = executions[0]
            # Execution should be completed or failed, not crash the system
            assert execution.status in [ResponseStatus.COMPLETED, ResponseStatus.FAILED]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
