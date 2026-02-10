"""
Comprehensive Tests for Enhanced Workflow Automation System

Tests cover:
- Enhanced workflow engine functionality
- Intelligent trigger evaluation
- Behavioral pattern matching
- Industry-specific workflow templates
- CRM integration capabilities
- Analytics and performance monitoring
- A/B testing functionality
- Workflow optimization
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from enhanced_workflow_engine import (
    EnhancedWorkflowEngine, TriggerCondition, ActionType, WorkflowPriority,
    WorkflowStage, IndustryVertical, TriggerRule, EnhancedWorkflowAction,
    BehaviorPatternMatcher, IntelligentTriggerEngine, ContextualResponseGenerator,
    WorkflowTemplateEngine, CRMIntegrationManager
)
from workflow_analytics_service import (
    WorkflowAnalyticsService, MetricType, TimeWindow, WorkflowMetric,
    WorkflowAnalyticsCollector, WorkflowPerformanceAnalyzer, ABTestingManager
)
from ..core.ai_orchestrator import AIInsight, AnalysisType, AdvancedAIOrchestrator

@pytest.mark.integration


@pytest.fixture
def mock_ai_orchestrator():
    """Mock AI orchestrator for testing."""
    orchestrator = MagicMock(spec=AdvancedAIOrchestrator)
    orchestrator.process_customer_interaction = AsyncMock(return_value={
        "customer_id": "test_customer",
        "analysis_results": [
            {
                "insight_id": "insight_1",
                "type": "sentiment_analysis",
                "confidence": 0.85,
                "data": {"overall_sentiment": 0.7},
                "reasoning": "Positive sentiment detected"
            }
        ],
        "workflow_actions": [],
        "journey_stage": "initial_contact",
        "processing_timestamp": datetime.utcnow().isoformat()
    })
    return orchestrator


@pytest.fixture
def behavior_pattern_matcher():
    """Create behavior pattern matcher for testing."""
    return BehaviorPatternMatcher()


@pytest.fixture
def trigger_engine():
    """Create intelligent trigger engine for testing."""
    return IntelligentTriggerEngine()


@pytest.fixture
def response_generator(mock_ai_orchestrator):
    """Create contextual response generator for testing."""
    return ContextualResponseGenerator(mock_ai_orchestrator)


@pytest.fixture
def template_engine():
    """Create workflow template engine for testing."""
    return WorkflowTemplateEngine()


@pytest.fixture
def crm_manager():
    """Create CRM integration manager for testing."""
    return CRMIntegrationManager()


@pytest.fixture
def enhanced_workflow_engine(mock_ai_orchestrator):
    """Create enhanced workflow engine for testing."""
    return EnhancedWorkflowEngine(mock_ai_orchestrator)


@pytest.fixture
def analytics_service():
    """Create workflow analytics service for testing."""
    return WorkflowAnalyticsService()


class TestBehaviorPatternMatcher:
    """Test behavioral pattern matching functionality."""
    
    @pytest.mark.asyncio
    async def test_high_intent_buyer_pattern(self, behavior_pattern_matcher):
        """Test high intent buyer pattern detection."""
        customer_data = {
            "page_views": 15,
            "pricing_page_visits": 5,
            "demo_requests": 2
        }
        
        patterns = await behavior_pattern_matcher.match_patterns(customer_data)
        
        # Should detect high intent buyer pattern
        high_intent_patterns = [p for p in patterns if p["pattern"] == "high_intent_buyer"]
        assert len(high_intent_patterns) == 1
        assert high_intent_patterns[0]["confidence"] >= 0.8
    
    @pytest.mark.asyncio
    async def test_at_risk_customer_pattern(self, behavior_pattern_matcher):
        """Test at-risk customer pattern detection."""
        customer_data = {
            "support_tickets": 4,
            "negative_sentiment_score": 0.8,
            "engagement_decrease": 0.5
        }
        
        patterns = await behavior_pattern_matcher.match_patterns(customer_data)
        
        # Should detect at-risk customer pattern
        at_risk_patterns = [p for p in patterns if p["pattern"] == "at_risk_customer"]
        assert len(at_risk_patterns) == 1
        assert at_risk_patterns[0]["confidence"] >= 0.75
    
    @pytest.mark.asyncio
    async def test_no_patterns_for_insufficient_data(self, behavior_pattern_matcher):
        """Test that no patterns are detected with insufficient data."""
        customer_data = {
            "page_views": 2,
            "pricing_page_visits": 0,
            "demo_requests": 0
        }
        
        patterns = await behavior_pattern_matcher.match_patterns(customer_data)
        
        # Should not detect any patterns with low confidence
        assert len(patterns) == 0


class TestIntelligentTriggerEngine:
    """Test intelligent trigger evaluation."""
    
    @pytest.fixture
    def sample_insights(self):
        """Create sample AI insights for testing."""
        return [
            AIInsight(
                insight_id="insight_1",
                analysis_type=AnalysisType.SENTIMENT_ANALYSIS,
                confidence=0.9,
                data={"overall_sentiment": 0.8},
                reasoning="High positive sentiment",
                timestamp=datetime.utcnow(),
                source="test"
            ),
            AIInsight(
                insight_id="insight_2",
                analysis_type=AnalysisType.CHURN_PREDICTION,
                confidence=0.85,
                data={"churn_probability": 0.7},
                reasoning="High churn risk detected",
                timestamp=datetime.utcnow(),
                source="test"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_sentiment_trigger_evaluation(self, trigger_engine, sample_insights):
        """Test sentiment-based trigger evaluation."""
        trigger_rule = TriggerRule(
            condition=TriggerCondition.SENTIMENT_THRESHOLD,
            operator=">=",
            threshold=0.6,
            confidence_required=0.8
        )
        
        customer_context = {}
        triggered_rules = await trigger_engine.evaluate_triggers(
            "customer_123", sample_insights, customer_context, [trigger_rule]
        )
        
        assert len(triggered_rules) == 1
        assert triggered_rules[0][0] == trigger_rule
        assert triggered_rules[0][1] >= 0.8
    
    @pytest.mark.asyncio
    async def test_churn_risk_trigger_evaluation(self, trigger_engine, sample_insights):
        """Test churn risk trigger evaluation."""
        trigger_rule = TriggerRule(
            condition=TriggerCondition.CHURN_RISK_LEVEL,
            operator=">=",
            threshold=0.6,
            confidence_required=0.7
        )
        
        customer_context = {}
        triggered_rules = await trigger_engine.evaluate_triggers(
            "customer_123", sample_insights, customer_context, [trigger_rule]
        )
        
        assert len(triggered_rules) == 1
        assert triggered_rules[0][1] >= 0.7
    
    @pytest.mark.asyncio
    async def test_engagement_score_trigger(self, trigger_engine):
        """Test engagement score trigger evaluation."""
        trigger_rule = TriggerRule(
            condition=TriggerCondition.ENGAGEMENT_SCORE,
            operator="<=",
            threshold=0.3,
            confidence_required=0.7
        )
        
        customer_context = {"engagement_score": 0.2}
        insights = []
        
        triggered_rules = await trigger_engine.evaluate_triggers(
            "customer_123", insights, customer_context, [trigger_rule]
        )
        
        assert len(triggered_rules) == 1


class TestContextualResponseGenerator:
    """Test contextual AI response generation."""
    
    @pytest.fixture
    def sample_customer_context(self):
        """Sample customer context for testing."""
        return {
            "name": "John Doe",
            "company": "Tech Corp",
            "industry": "Technology",
            "status": "qualified"
        }
    
    @pytest.fixture
    def sample_insights(self):
        """Sample insights for testing."""
        return [
            AIInsight(
                insight_id="insight_1",
                analysis_type=AnalysisType.SENTIMENT_ANALYSIS,
                confidence=0.9,
                data={"overall_sentiment": 0.7},
                reasoning="Positive sentiment",
                timestamp=datetime.utcnow(),
                source="test"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_email_content_generation(self, response_generator, sample_customer_context, sample_insights):
        """Test email content generation."""
        result = await response_generator.generate_contextual_response(
            ActionType.SEND_EMAIL,
            sample_customer_context,
            sample_insights
        )
        
        assert "subject" in result
        assert "tone" in result
        assert "template_variables" in result
        assert result["template_variables"]["customer_name"] == "John Doe"
        assert result["template_variables"]["company_name"] == "Tech Corp"
    
    @pytest.mark.asyncio
    async def test_proposal_content_generation(self, response_generator, sample_customer_context, sample_insights):
        """Test proposal content generation."""
        result = await response_generator.generate_contextual_response(
            ActionType.GENERATE_PROPOSAL,
            sample_customer_context,
            sample_insights
        )
        
        assert result["proposal_type"] == "custom"
        assert "sections" in result
        assert "personalization_level" in result


class TestWorkflowTemplateEngine:
    """Test workflow template functionality."""
    
    def test_get_real_estate_template(self, template_engine):
        """Test retrieving real estate workflow template."""
        template = template_engine.get_template(IndustryVertical.REAL_ESTATE)
        
        assert template is not None
        assert template.industry == IndustryVertical.REAL_ESTATE
        assert template.name == "Real Estate Lead Nurturing"
        assert len(template.default_actions) > 0
        assert WorkflowStage.INITIAL_CONTACT in template.stages
    
    def test_get_saas_template(self, template_engine):
        """Test retrieving SaaS B2B workflow template."""
        template = template_engine.get_template(IndustryVertical.SAAS_B2B)
        
        assert template is not None
        assert template.industry == IndustryVertical.SAAS_B2B
        assert template.name == "SaaS B2B Sales Automation"
        assert len(template.default_actions) > 0
        assert WorkflowStage.ONBOARDING in template.stages
    
    def test_customize_template(self, template_engine):
        """Test template customization."""
        customizations = {
            "personalization_fields": ["custom_field1", "custom_field2"],
            "additional_actions": [],
            "trigger_rules": {
                "custom_trigger": [
                    TriggerRule(
                        condition=TriggerCondition.ENGAGEMENT_SCORE,
                        operator=">=",
                        threshold=0.8,
                        confidence_required=0.7
                    )
                ]
            }
        }
        
        customized = template_engine.customize_template(
            IndustryVertical.REAL_ESTATE,
            customizations
        )
        
        assert "custom_field1" in customized.personalization_fields
        assert "custom_field2" in customized.personalization_fields
        assert "custom_trigger" in customized.trigger_rules


class TestCRMIntegrationManager:
    """Test CRM integration functionality."""
    
    @pytest.mark.asyncio
    async def test_update_crm_record(self, crm_manager):
        """Test updating CRM record."""
        result = await crm_manager.execute_crm_action(
            "salesforce",
            ActionType.UPDATE_CRM,
            "customer_123",
            {"status": "qualified", "score": 85}
        )
        
        assert result["status"] == "success"
        assert result["crm"] == "salesforce"
        assert result["customer_id"] == "customer_123"
        assert "updated_fields" in result
    
    @pytest.mark.asyncio
    async def test_create_crm_task(self, crm_manager):
        """Test creating CRM task."""
        result = await crm_manager.execute_crm_action(
            "hubspot",
            ActionType.CREATE_TASK,
            "customer_123",
            {"task": "Follow up call", "priority": "high"}
        )
        
        assert result["status"] == "success"
        assert result["crm"] == "hubspot"
        assert result["customer_id"] == "customer_123"
        assert "task_id" in result
    
    @pytest.mark.asyncio
    async def test_update_lead_score(self, crm_manager):
        """Test updating lead score in CRM."""
        result = await crm_manager.execute_crm_action(
            "pipedrive",
            ActionType.UPDATE_LEAD_SCORE,
            "customer_123",
            {"score": 92, "score_type": "lead_scoring"}
        )
        
        assert result["status"] == "success"
        assert result["new_score"] == 92
        assert result["score_type"] == "lead_scoring"
    
    @pytest.mark.asyncio
    async def test_unsupported_crm(self, crm_manager):
        """Test error handling for unsupported CRM."""
        with pytest.raises(ValueError, match="Unsupported CRM"):
            await crm_manager.execute_crm_action(
                "unknown_crm",
                ActionType.UPDATE_CRM,
                "customer_123",
                {}
            )


class TestEnhancedWorkflowEngine:
    """Test enhanced workflow engine functionality."""
    
    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history for testing."""
        return [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "speaker": "customer",
                "content": "I'm interested in your premium package"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "speaker": "assistant",
                "content": "Great! Let me tell you about our premium features"
            }
        ]
    
    @pytest.fixture
    def sample_customer_context(self):
        """Sample customer context for testing."""
        return {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "company": "Example Corp",
            "industry": "Technology",
            "status": "qualified",
            "engagement_score": 0.8,
            "interaction_count": 3
        }
    
    @pytest.mark.asyncio
    async def test_process_customer_workflow(
        self, enhanced_workflow_engine, sample_conversation_history, sample_customer_context
    ):
        """Test processing customer workflow."""
        result = await enhanced_workflow_engine.process_customer_workflow(
            "customer_123",
            sample_conversation_history,
            sample_customer_context,
            industry=IndustryVertical.SAAS_B2B
        )
        
        assert result["customer_id"] == "customer_123"
        assert "ai_insights" in result
        assert "workflow_actions" in result
        assert "template_used" in result
        assert result["template_used"] is not None
    
    @pytest.mark.asyncio
    async def test_workflow_action_execution(self, enhanced_workflow_engine):
        """Test workflow action execution."""
        action = EnhancedWorkflowAction(
            action_id="test_action",
            action_type=ActionType.SEND_EMAIL,
            priority=WorkflowPriority.MEDIUM,
            stage=WorkflowStage.INITIAL_CONTACT,
            payload={"template": "welcome", "subject": "Welcome!"},
            trigger_rules=[]
        )
        
        insights = []
        customer_context = {"email": "test@example.com"}
        
        result = await enhanced_workflow_engine._execute_workflow_action(
            "customer_123", action, insights, customer_context
        )
        
        assert result["action_id"] == "test_action"
        assert result["status"] == "completed"
        assert action.executed is True
    
    @pytest.mark.asyncio
    async def test_workflow_engine_start_stop(self, enhanced_workflow_engine):
        """Test starting and stopping workflow engine."""
        await enhanced_workflow_engine.start()
        assert enhanced_workflow_engine.running is True
        assert len(enhanced_workflow_engine.executor_tasks) > 0
        
        await enhanced_workflow_engine.stop()
        assert enhanced_workflow_engine.running is False
        assert len(enhanced_workflow_engine.executor_tasks) == 0
    
    def test_workflow_engine_stats(self, enhanced_workflow_engine):
        """Test workflow engine statistics."""
        stats = enhanced_workflow_engine.get_workflow_stats()
        
        assert "running" in stats
        assert "active_workflows" in stats
        assert "queue_sizes" in stats
        assert "templates_available" in stats
        assert "supported_industries" in stats
        assert "supported_crms" in stats


class TestWorkflowAnalyticsService:
    """Test workflow analytics functionality."""
    
    @pytest.mark.asyncio
    async def test_record_workflow_event(self, analytics_service):
        """Test recording workflow events."""
        await analytics_service.record_workflow_event(
            "workflow_started",
            "workflow_123",
            "customer_456",
            1.0,
            {"template": "saas_b2b_v1"}
        )
        
        # Verify event was recorded (would check database in real implementation)
        assert len(analytics_service.collector.metrics_buffer) > 0
    
    @pytest.mark.asyncio
    async def test_analytics_service_start_stop(self, analytics_service):
        """Test starting and stopping analytics service."""
        await analytics_service.start()
        assert analytics_service.running is True
        assert len(analytics_service.background_tasks) > 0
        
        await analytics_service.stop()
        assert analytics_service.running is False
        assert len(analytics_service.background_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, analytics_service):
        """Test getting dashboard data."""
        # Add some test metrics
        await analytics_service.collector.record_metric(
            "workflow_123",
            "customer_456",
            MetricType.CONVERSION_RATE,
            0.15
        )
        
        dashboard_data = await analytics_service.get_dashboard_data()
        
        assert "timestamp" in dashboard_data
        assert "performance_summary" in dashboard_data
        assert "real_time_metrics" in dashboard_data
        assert "active_ab_tests" in dashboard_data


class TestWorkflowAnalyticsCollector:
    """Test workflow analytics collection."""
    
    @pytest.fixture
    def analytics_collector(self):
        """Create analytics collector for testing."""
        return WorkflowAnalyticsCollector()
    
    @pytest.mark.asyncio
    async def test_record_metric(self, analytics_collector):
        """Test recording individual metrics."""
        await analytics_collector.record_metric(
            "workflow_123",
            "customer_456",
            MetricType.CONVERSION_RATE,
            0.25,
            {"campaign": "test"},
            IndustryVertical.SAAS_B2B,
            WorkflowStage.PROPOSAL,
            ActionType.SEND_EMAIL
        )
        
        assert len(analytics_collector.metrics_buffer) == 1
        
        metric = analytics_collector.metrics_buffer[0]
        assert metric.workflow_id == "workflow_123"
        assert metric.customer_id == "customer_456"
        assert metric.metric_type == MetricType.CONVERSION_RATE
        assert metric.value == 0.25
        assert metric.industry == IndustryVertical.SAAS_B2B
    
    def test_get_recent_metrics(self, analytics_collector):
        """Test retrieving recent metrics."""
        # Add test metric to recent metrics directly
        from datetime import datetime
        from ..services.workflow_analytics_service import WorkflowMetric
        
        test_metric = WorkflowMetric(
            metric_id="metric_1",
            workflow_id="workflow_123",
            customer_id="customer_456",
            metric_type=MetricType.ENGAGEMENT_RATE,
            value=0.8,
            timestamp=datetime.utcnow(),
            metadata={}
        )
        
        analytics_collector.recent_metrics["engagement_rate_workflow_123"].append(test_metric)
        
        recent_metrics = analytics_collector.get_recent_metrics(
            MetricType.ENGAGEMENT_RATE,
            "workflow_123",
            time_window_hours=1
        )
        
        assert len(recent_metrics) == 1
        assert recent_metrics[0].value == 0.8


class TestABTestingManager:
    """Test A/B testing functionality."""
    
    @pytest.fixture
    def ab_testing_manager(self):
        """Create A/B testing manager for testing."""
        from ..services.workflow_analytics_service import WorkflowAnalyticsCollector
        collector = WorkflowAnalyticsCollector()
        return ABTestingManager(collector)
    
    @pytest.mark.asyncio
    async def test_create_ab_test(self, ab_testing_manager):
        """Test creating A/B test."""
        test_id = await ab_testing_manager.create_ab_test(
            "Email Subject Test",
            "control_subject",
            ["variant_a", "variant_b"]
        )
        
        assert test_id in ab_testing_manager.active_tests
        
        test = ab_testing_manager.active_tests[test_id]
        assert test.test_name == "Email Subject Test"
        assert test.control_variant == "control_subject"
        assert test.test_variants == ["variant_a", "variant_b"]
        assert test.status == "running"
    
    def test_assign_variant(self, ab_testing_manager):
        """Test variant assignment."""
        # Create test first
        test_id = "test_123"
        from ..services.workflow_analytics_service import ABTestResult
        
        test = ABTestResult(
            test_id=test_id,
            test_name="Test",
            start_date=datetime.utcnow(),
            end_date=None,
            status="running",
            control_variant="control",
            test_variants=["variant_a"],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            sample_sizes={},
            conversion_rates={},
            confidence_intervals={},
            statistical_significance=None,
            winner=None,
            revenue_impact={},
            customer_impact={},
            recommendations=[]
        )
        
        ab_testing_manager.active_tests[test_id] = test
        
        # Test variant assignment (should be consistent for same customer)
        variant1 = ab_testing_manager.assign_variant(test_id, "customer_123")
        variant2 = ab_testing_manager.assign_variant(test_id, "customer_123")
        
        assert variant1 == variant2  # Should be consistent
        assert variant1 in ["control", "variant_a"]
    
    @pytest.mark.asyncio
    async def test_record_test_conversion(self, ab_testing_manager):
        """Test recording test conversions."""
        # Create and add test
        test_id = "test_456"
        from ..services.workflow_analytics_service import ABTestResult
        
        test = ABTestResult(
            test_id=test_id,
            test_name="Conversion Test",
            start_date=datetime.utcnow(),
            end_date=None,
            status="running",
            control_variant="control",
            test_variants=["variant_a"],
            traffic_allocation={"control": 0.5, "variant_a": 0.5},
            sample_sizes={},
            conversion_rates={},
            confidence_intervals={},
            statistical_significance=None,
            winner=None,
            revenue_impact={},
            customer_impact={},
            recommendations=[]
        )
        
        ab_testing_manager.active_tests[test_id] = test
        
        # Record conversion
        await ab_testing_manager.record_test_conversion(
            test_id, "control", "customer_123", True, 100.0
        )
        
        assert test.sample_sizes["control"] == 1
        assert test.conversion_rates["control"] == 1.0
        assert test.revenue_impact["control"] == 100.0


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_high_churn_risk_workflow_scenario(self, enhanced_workflow_engine):
        """Test complete workflow for high churn risk customer."""
        
        # Setup high churn risk scenario
        conversation_history = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "speaker": "customer",
                "content": "I'm having issues with your service and considering alternatives"
            }
        ]
        
        customer_context = {
            "name": "At Risk Customer",
            "email": "atrisk@example.com",
            "support_tickets": 5,
            "negative_sentiment_score": 0.8,
            "engagement_decrease": 0.6,
            "churn_probability": 0.75
        }
        
        # Mock AI orchestrator to return high churn risk
        enhanced_workflow_engine.ai_orchestrator.process_customer_interaction.return_value = {
            "customer_id": "churn_risk_customer",
            "analysis_results": [
                {
                    "insight_id": "churn_insight",
                    "type": "churn_prediction",
                    "confidence": 0.9,
                    "data": {"churn_probability": 0.75, "retention_strategies": ["discount", "call"]},
                    "reasoning": "High churn risk based on recent behavior"
                }
            ],
            "workflow_actions": [],
            "journey_stage": "retention"
        }
        
        # Process workflow
        result = await enhanced_workflow_engine.process_customer_workflow(
            "churn_risk_customer",
            conversation_history,
            customer_context
        )
        
        # Verify churn prevention actions were generated
        assert len(result["workflow_actions"]) > 0
        
        # Check for retention-focused actions
        retention_actions = [
            action for action in result["workflow_actions"]
            if "retention" in action.get("action_type", "").lower() or
               action.get("stage") == "retention"
        ]
        assert len(retention_actions) > 0
    
    @pytest.mark.asyncio
    async def test_high_intent_buyer_workflow_scenario(self, enhanced_workflow_engine):
        """Test complete workflow for high intent buyer."""
        
        conversation_history = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "speaker": "customer", 
                "content": "I'd like to see pricing for your enterprise package"
            }
        ]
        
        customer_context = {
            "name": "High Intent Buyer",
            "email": "buyer@enterprise.com",
            "page_views": 20,
            "pricing_page_visits": 8,
            "demo_requests": 2,
            "engagement_score": 0.9
        }
        
        # Mock AI orchestrator to return high purchase intent
        enhanced_workflow_engine.ai_orchestrator.process_customer_interaction.return_value = {
            "customer_id": "high_intent_buyer",
            "analysis_results": [
                {
                    "insight_id": "intent_insight",
                    "type": "intent_classification",
                    "confidence": 0.95,
                    "data": {"primary_intent": "purchase_intent", "intent_confidence": 0.9},
                    "reasoning": "Strong purchase signals detected"
                }
            ],
            "workflow_actions": [],
            "journey_stage": "proposal"
        }
        
        # Process workflow
        result = await enhanced_workflow_engine.process_customer_workflow(
            "high_intent_buyer",
            conversation_history,
            customer_context
        )
        
        # Verify high-priority sales actions were generated
        assert len(result["workflow_actions"]) > 0
        
        # Check for high-priority actions
        high_priority_actions = [
            action for action in result["workflow_actions"]
            if action.get("priority") in ["critical", "high"]
        ]
        assert len(high_priority_actions) > 0
    
    @pytest.mark.asyncio
    async def test_industry_specific_template_application(self, enhanced_workflow_engine):
        """Test industry-specific template application."""
        
        conversation_history = [{"content": "Looking for real estate services"}]
        customer_context = {"industry": "real_estate"}
        
        # Process with real estate industry
        result = await enhanced_workflow_engine.process_customer_workflow(
            "real_estate_customer",
            conversation_history, 
            customer_context,
            industry=IndustryVertical.REAL_ESTATE
        )
        
        # Verify real estate template was used
        assert result["template_used"] == "real_estate_v1"
        
        # Process with SaaS industry
        result_saas = await enhanced_workflow_engine.process_customer_workflow(
            "saas_customer",
            conversation_history,
            customer_context,
            industry=IndustryVertical.SAAS_B2B
        )
        
        # Verify different template was used
        assert result_saas["template_used"] == "saas_b2b_v1"
        assert result_saas["template_used"] != result["template_used"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main(["-v", __file__])