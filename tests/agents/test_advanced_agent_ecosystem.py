"""
Comprehensive tests for Advanced Agent Ecosystem
Tests ClaudeConciergeAgent, PropertyIntelligenceAgent, and CustomerJourneyOrchestrator
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ghl_real_estate_ai.agents.claude_concierge_agent import (
    ClaudeConciergeAgent, PlatformKnowledgeEngine, ContextAwarenessEngine,
    UserSession, UserIntent, PlatformContext, ConciergeMode
)
from ghl_real_estate_ai.agents.property_intelligence_agent import (
    PropertyIntelligenceAgent, PropertyDataCollector, InvestmentAnalysisEngine,
    PropertyIntelligenceRequest, PropertyType, InvestmentStrategy, PropertyIntelligenceLevel
)
from ghl_real_estate_ai.agents.customer_journey_orchestrator import (
    CustomerJourneyOrchestrator, JourneyTemplateEngine, JourneyAnalyticsEngine,
    CustomerProfile, CustomerType, JourneyStage, JourneyPriority
)

class TestClaudeConciergeAgent:
    """Test suite for Claude Concierge Agent."""

    @pytest.fixture
    def mock_claude_assistant(self):
        mock_claude = AsyncMock()
        mock_claude.analyze_with_context.return_value = {
            "content": "I'm here to help you navigate Jorge's platform efficiently!"
        }
        return mock_claude

    @pytest.fixture
    def concierge_agent(self, mock_claude_assistant):
        with patch('ghl_real_estate_ai.agents.claude_concierge_agent.ClaudeAssistant',
                  return_value=mock_claude_assistant):
            with patch('ghl_real_estate_ai.agents.claude_concierge_agent.get_event_publisher') as mock_publisher:
                mock_publisher.return_value = AsyncMock()
                return ClaudeConciergeAgent()

    @pytest.mark.asyncio
    async def test_platform_knowledge_engine_initialization(self):
        """Test platform knowledge engine loads correctly."""
        knowledge_engine = PlatformKnowledgeEngine()

        assert "lead_management" in knowledge_engine.platform_features
        assert "adaptive_jorge" in knowledge_engine.agent_registry
        assert "new_user_onboarding" in knowledge_engine.user_workflows
        assert "ghl" in knowledge_engine.integration_points

        # Test agent capability structure
        jorge_agent = knowledge_engine.agent_registry["adaptive_jorge"]
        assert jorge_agent.agent_name == "Adaptive Jorge Seller Bot"
        assert "real_time_questioning" in jorge_agent.capabilities

    @pytest.mark.asyncio
    async def test_context_awareness_activity_tracking(self):
        """Test context awareness engine tracks user activity."""
        context_engine = ContextAwarenessEngine()

        # Track user activity
        activity = {
            "page": "lead_management",
            "action": "view_leads",
            "duration": 120
        }

        session = await context_engine.track_user_activity("user123", activity)

        assert session.user_id == "user123"
        assert session.current_context == PlatformContext.LEAD_MANAGEMENT
        assert session.detected_intent == UserIntent.WORKING
        assert len(session.activity_history) == 1

    @pytest.mark.asyncio
    async def test_context_detection_accuracy(self):
        """Test accurate context detection from activities."""
        context_engine = ContextAwarenessEngine()

        # Test different context scenarios
        test_cases = [
            ({"page": "dashboard", "action": "view"}, PlatformContext.DASHBOARD),
            ({"page": "property_analysis", "action": "generate_cma"}, PlatformContext.PROPERTY_ANALYSIS),
            ({"page": "bot_management", "action": "configure"}, PlatformContext.BOT_MANAGEMENT),
            ({"page": "reports", "action": "analyze"}, PlatformContext.REPORTS)
        ]

        for activity, expected_context in test_cases:
            detected_context = context_engine._detect_context(activity)
            assert detected_context == expected_context

    @pytest.mark.asyncio
    async def test_frustration_detection(self):
        """Test detection of user frustration indicators."""
        context_engine = ContextAwarenessEngine()

        user_session = UserSession(
            user_id="frustrated_user",
            session_start=datetime.now(),
            last_activity=datetime.now(),
            current_context=PlatformContext.DASHBOARD,
            detected_intent=UserIntent.TROUBLESHOOTING
        )

        # Simulate error activity
        error_activity = {"action": "error_encountered", "page": "lead_management"}
        context_engine._detect_frustration_indicators(user_session, error_activity)

        assert "error_encountered" in user_session.frustration_indicators

    @pytest.mark.asyncio
    async def test_concierge_user_interaction_processing(self, concierge_agent):
        """Test complete user interaction processing."""
        result = await concierge_agent.process_user_interaction(
            user_id="test_user",
            message="How do I set up Jorge's adaptive questioning?",
            context={
                "page": "bot_management",
                "action": "configuration",
                "device": "desktop"
            }
        )

        assert "concierge_response" in result
        assert "proactive_recommendations" in result
        assert "session_context" in result
        assert result["session_context"]["current_context"] == "bot_management"

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self, concierge_agent):
        """Test coordination with multiple agents."""
        coordinator = concierge_agent.multi_agent_coordinator

        # Create mock user session
        session = UserSession(
            user_id="test_user",
            session_start=datetime.now(),
            last_activity=datetime.now(),
            current_context=PlatformContext.LEAD_MANAGEMENT,
            detected_intent=UserIntent.WORKING
        )

        coordination_result = await coordinator.coordinate_agent_assistance(
            "I need help qualifying a seller lead",
            session
        )

        assert "coordinated_response" in coordination_result
        assert "agents_used" in coordination_result
        assert "coordination_plan" in coordination_result

    @pytest.mark.asyncio
    async def test_proactive_recommendations_generation(self, concierge_agent):
        """Test generation of proactive recommendations."""
        proactive_assistant = concierge_agent.proactive_assistant

        # Create session with frustration indicators
        session = UserSession(
            user_id="test_user",
            session_start=datetime.now(),
            last_activity=datetime.now(),
            current_context=PlatformContext.LEAD_MANAGEMENT,
            detected_intent=UserIntent.TROUBLESHOOTING,
            frustration_indicators=["error_encountered"]
        )

        recommendations = await proactive_assistant.generate_proactive_recommendations(session)

        assert len(recommendations) > 0
        assert any(rec.recommendation_type == "frustration_assistance" for rec in recommendations)

class TestPropertyIntelligenceAgent:
    """Test suite for Property Intelligence Agent."""

    @pytest.fixture
    def mock_claude_assistant(self):
        mock_claude = AsyncMock()
        mock_claude.analyze_with_context.return_value = {
            "content": "Comprehensive property analysis completed with strong investment potential."
        }
        return mock_claude

    @pytest.fixture
    def property_agent(self, mock_claude_assistant):
        with patch('ghl_real_estate_ai.agents.property_intelligence_agent.ClaudeAssistant',
                  return_value=mock_claude_assistant):
            with patch('ghl_real_estate_ai.agents.property_intelligence_agent.get_event_publisher') as mock_publisher:
                mock_publisher.return_value = AsyncMock()
                return PropertyIntelligenceAgent()

    @pytest.mark.asyncio
    async def test_property_data_collection(self):
        """Test comprehensive property data collection."""
        collector = PropertyDataCollector()

        property_data = await collector.collect_property_data(
            "123 Test St, Austin, TX",
            PropertyIntelligenceLevel.STANDARD
        )

        # Verify all required data sections
        required_sections = [
            "basic_info", "market_data", "neighborhood_data",
            "comparable_sales", "rental_comps", "public_records"
        ]

        for section in required_sections:
            assert section in property_data
            assert property_data[section] is not None

        # Test premium data inclusion
        premium_data = await collector.collect_property_data(
            "123 Test St, Austin, TX",
            PropertyIntelligenceLevel.PREMIUM
        )

        assert "investment_metrics" in premium_data
        assert "predictive_data" in premium_data

    @pytest.mark.asyncio
    async def test_investment_analysis_rental_strategy(self):
        """Test investment analysis for rental strategy."""
        analyzer = InvestmentAnalysisEngine()

        # Mock property data
        property_data = {
            "basic_info": {
                "square_footage": 2000,
                "current_list_price": 400000,
                "property_tax": 8000
            },
            "market_data": {
                "market_appreciation_5y": 25.0,
                "days_on_market_avg": 30,
                "market_trend": "seller_favorable"
            },
            "rental_comps": [
                {"rent_per_sqft": 1.25, "monthly_rent": 2500}
            ],
            "neighborhood_data": {
                "crime_index": 20
            }
        }

        scoring = await analyzer.analyze_investment_potential(
            property_data,
            InvestmentStrategy.RENTAL_INCOME,
            "intermediate"
        )

        assert isinstance(scoring.total_score, float)
        assert 0 <= scoring.total_score <= 100
        assert scoring.cap_rate is not None
        assert scoring.projected_roi > 0
        assert "break_even_analysis" in scoring.break_even_analysis

    @pytest.mark.asyncio
    async def test_investment_analysis_flip_strategy(self):
        """Test investment analysis for fix and flip strategy."""
        analyzer = InvestmentAnalysisEngine()

        property_data = {
            "basic_info": {
                "square_footage": 2000,
                "current_list_price": 300000
            },
            "market_data": {
                "price_per_sqft": 200,
                "days_on_market_avg": 25,
                "market_trend": "seller_favorable"
            }
        }

        scoring = await analyzer.analyze_investment_potential(
            property_data,
            InvestmentStrategy.FIX_AND_FLIP,
            "advanced"
        )

        assert scoring.cash_flow_score == 0  # No ongoing cash flow for flips
        assert scoring.appreciation_score > 0
        assert scoring.cap_rate is None  # Not applicable for flips
        assert "purchase_price" in scoring.break_even_analysis

    @pytest.mark.asyncio
    async def test_complete_property_analysis(self, property_agent):
        """Test complete property intelligence analysis."""
        request = PropertyIntelligenceRequest(
            property_address="123 Investment Ave, Austin, TX",
            property_type=PropertyType.SINGLE_FAMILY,
            intelligence_level=PropertyIntelligenceLevel.STANDARD,
            investment_strategy=InvestmentStrategy.BUY_AND_HOLD,
            investor_profile="intermediate"
        )

        with patch.object(property_agent.data_collector, 'collect_property_data') as mock_collector:
            mock_collector.return_value = {
                "basic_info": {"square_footage": 2000, "current_list_price": 400000},
                "market_data": {"market_appreciation_5y": 25.0},
                "neighborhood_data": {"crime_index": 15},
                "rental_comps": [{"rent_per_sqft": 1.3}],
                "comparable_sales": [],
                "public_records": {"permit_history": []}
            }

            report = await property_agent.analyze_property(request)

            assert report.property_address == request.property_address
            assert report.intelligence_level == request.intelligence_level
            assert report.investment_scoring is not None
            assert report.market_positioning is not None
            assert report.condition_assessment is not None
            assert report.neighborhood_intelligence is not None
            assert report.risk_assessment is not None

    @pytest.mark.asyncio
    async def test_market_positioning_analysis(self, property_agent):
        """Test market positioning analysis accuracy."""
        property_data = {
            "basic_info": {"square_footage": 2000, "current_list_price": 450000},
            "market_data": {"median_home_value": 400000, "days_on_market_avg": 35},
            "comparable_sales": [
                {"sale_price": 440000, "similarity_score": 0.9},
                {"sale_price": 460000, "similarity_score": 0.85}
            ]
        }

        positioning = await property_agent._analyze_market_positioning(property_data)

        assert positioning.competitive_rank in ["top_tier", "mid_market", "value_tier"]
        assert positioning.price_position in ["below_market", "at_market", "above_market"]
        assert positioning.days_on_market_prediction > 0
        assert len(positioning.comparable_properties) > 0

class TestCustomerJourneyOrchestrator:
    """Test suite for Customer Journey Orchestrator."""

    @pytest.fixture
    def mock_claude_assistant(self):
        mock_claude = AsyncMock()
        mock_claude.analyze_with_context.return_value = {
            "content": "Journey step completed successfully with comprehensive agent coordination."
        }
        return mock_claude

    @pytest.fixture
    def journey_orchestrator(self, mock_claude_assistant):
        with patch('ghl_real_estate_ai.agents.customer_journey_orchestrator.ClaudeAssistant',
                  return_value=mock_claude_assistant):
            with patch('ghl_real_estate_ai.agents.customer_journey_orchestrator.get_event_publisher') as mock_publisher:
                mock_publisher.return_value = AsyncMock()
                with patch('ghl_real_estate_ai.agents.customer_journey_orchestrator.get_claude_concierge') as mock_concierge:
                    mock_concierge.return_value = AsyncMock()
                    return CustomerJourneyOrchestrator()

    @pytest.mark.asyncio
    async def test_journey_template_engine_initialization(self):
        """Test journey template engine loads correctly."""
        template_engine = JourneyTemplateEngine()

        # Test template availability
        assert "first_time_buyer" in template_engine.journey_templates
        assert "investor" in template_engine.journey_templates
        assert "seller" in template_engine.journey_templates

        # Test first-time buyer template structure
        ftb_template = template_engine.get_journey_template(CustomerType.FIRST_TIME_BUYER)
        assert len(ftb_template) > 0
        assert all(hasattr(step, 'step_id') for step in ftb_template)
        assert all(hasattr(step, 'required_agents') for step in ftb_template)

    @pytest.mark.asyncio
    async def test_journey_template_customization(self):
        """Test journey template customization based on customer profile."""
        template_engine = JourneyTemplateEngine()

        # Create customer profile
        profile = CustomerProfile(
            customer_id="test_customer",
            customer_type=CustomerType.FIRST_TIME_BUYER,
            journey_stage=JourneyStage.DISCOVERY,
            priority_level=JourneyPriority.HIGH,
            response_speed_preference="immediate",
            investment_experience="advanced"
        )

        # Get and customize template
        template = template_engine.get_journey_template(CustomerType.FIRST_TIME_BUYER)
        customized = template_engine.customize_journey_template(template, profile)

        assert len(customized) == len(template)
        # Verify customization applied (advanced users get different agents)
        assert any("property_intelligence" in step.required_agents for step in customized)

    @pytest.mark.asyncio
    async def test_journey_analytics_performance_analysis(self):
        """Test journey analytics and performance analysis."""
        analytics = JourneyAnalyticsEngine()

        # Mock journey history
        journey_history = [
            {
                "step_name": "Education & Onboarding",
                "timestamp": "2026-01-01T10:00:00",
                "status": "completed",
                "duration": 60,
                "agents_used": ["claude_concierge"]
            },
            {
                "step_name": "Financial Qualification",
                "timestamp": "2026-01-03T14:00:00",
                "status": "completed",
                "duration": 120,
                "agents_used": ["adaptive_jorge"]
            }
        ]

        performance = await analytics.analyze_journey_performance("test_customer", journey_history)

        assert "journey_performance" in performance
        assert "optimization_opportunities" in performance
        assert "performance_grade" in performance
        assert performance["journey_performance"]["completion_rate"] == 100

    @pytest.mark.asyncio
    async def test_customer_journey_initiation(self, journey_orchestrator):
        """Test starting a new customer journey."""
        initial_context = {
            "priority": JourneyPriority.HIGH,
            "communication_preference": "sms",
            "budget_range": (300000, 500000)
        }

        result = await journey_orchestrator.start_customer_journey(
            customer_id="new_customer_123",
            customer_type=CustomerType.FIRST_TIME_BUYER,
            initial_context=initial_context
        )

        assert result["journey_id"] == "new_customer_123"
        assert "customer_profile" in result
        assert "journey_overview" in result
        assert "first_step_result" in result
        assert result["journey_overview"]["current_step"] == 1

    @pytest.mark.asyncio
    async def test_journey_advancement(self, journey_orchestrator):
        """Test advancing customer through journey steps."""
        # First start a journey
        initial_context = {"priority": JourneyPriority.MEDIUM}
        await journey_orchestrator.start_customer_journey(
            "advancement_test",
            CustomerType.SELLER,
            initial_context
        )

        # Advance to next step
        completion_data = {
            "motivation_confirmed": True,
            "timeline_established": True
        }

        advancement_result = await journey_orchestrator.advance_customer_journey(
            "advancement_test",
            completion_data
        )

        assert advancement_result["advancement_status"] == "advanced"
        assert "previous_step" in advancement_result
        assert "current_step" in advancement_result
        assert advancement_result["progress"] > 0

    @pytest.mark.asyncio
    async def test_agent_handoff_planning(self, journey_orchestrator):
        """Test agent handoff planning for journey steps."""
        from ghl_real_estate_ai.agents.customer_journey_orchestrator import JourneyStep

        # Create test step
        step = JourneyStep(
            step_id="test_001",
            step_name="Test Step",
            description="Test step description",
            required_agents=["claude_concierge", "adaptive_jorge"],
            estimated_duration="1 day",
            success_criteria=["Test completed"],
            exit_conditions=["Test failed"],
            next_steps=["test_002"]
        )

        # Create customer profile
        profile = CustomerProfile(
            customer_id="handoff_test",
            customer_type=CustomerType.INVESTOR,
            journey_stage=JourneyStage.EVALUATION,
            priority_level=JourneyPriority.HIGH
        )

        handoffs = await journey_orchestrator._plan_agent_handoffs(step, profile, {})

        assert len(handoffs) == 2  # One for each required agent
        assert handoffs[0].from_agent == "journey_orchestrator"
        assert handoffs[1].from_agent == "claude_concierge"
        assert all(handoff.priority == JourneyPriority.HIGH for handoff in handoffs)

    @pytest.mark.asyncio
    async def test_journey_status_retrieval(self, journey_orchestrator):
        """Test retrieving journey status for active customer."""
        # Start journey first
        await journey_orchestrator.start_customer_journey(
            "status_test",
            CustomerType.INVESTOR,
            {"priority": JourneyPriority.MEDIUM}
        )

        status = await journey_orchestrator.get_journey_status("status_test")

        assert status["customer_id"] == "status_test"
        assert status["journey_status"] == "active"
        assert status["customer_type"] == "investor"
        assert "current_step" in status
        assert "active_agents" in status

    @pytest.mark.asyncio
    async def test_journey_completion_analytics(self, journey_orchestrator):
        """Test journey completion and analytics generation."""
        # Mock a completed journey
        customer_id = "completion_test"
        journey_state = {
            "customer_profile": CustomerProfile(
                customer_id=customer_id,
                customer_type=CustomerType.SELLER,
                journey_stage=JourneyStage.OWNERSHIP,
                priority_level=JourneyPriority.MEDIUM
            ),
            "journey_history": [
                {
                    "step_name": "Seller Qualification",
                    "completion_time": datetime.now() - timedelta(days=5),
                    "status": "completed",
                    "satisfaction": 85
                },
                {
                    "step_name": "Property Valuation",
                    "completion_time": datetime.now() - timedelta(days=3),
                    "status": "completed",
                    "satisfaction": 90
                }
            ],
            "start_time": datetime.now() - timedelta(days=7)
        }

        journey_orchestrator.active_journeys[customer_id] = journey_state

        completion_result = await journey_orchestrator._complete_customer_journey(customer_id)

        assert completion_result["completion_status"] == "journey_completed"
        assert completion_result["customer_id"] == customer_id
        assert "performance_analysis" in completion_result
        assert "completion_report" in completion_result

class TestIntegratedAgentEcosystem:
    """Integration tests for the complete advanced agent ecosystem."""

    @pytest.mark.asyncio
    async def test_concierge_property_intelligence_integration(self):
        """Test integration between Concierge and Property Intelligence agents."""
        # Mock scenario: User asks Concierge about property analysis
        # Concierge should coordinate with Property Intelligence agent
        pass

    @pytest.mark.asyncio
    async def test_journey_orchestrator_agent_coordination(self):
        """Test Journey Orchestrator coordinating multiple agents."""
        # Mock scenario: Customer journey step requires multiple agents
        # Should properly hand off between agents and maintain context
        pass

    @pytest.mark.asyncio
    async def test_end_to_end_customer_experience(self):
        """Test complete end-to-end customer experience flow."""
        # Mock scenario: New customer enters system, goes through complete journey
        # Should involve all three new agents working together
        pass

    @pytest.mark.asyncio
    async def test_agent_ecosystem_performance_metrics(self):
        """Test performance metrics collection across agent ecosystem."""
        # Verify that all agents properly emit events and track performance
        pass

    @pytest.mark.asyncio
    async def test_agent_ecosystem_error_handling(self):
        """Test error handling and fallback mechanisms across agents."""
        # Verify graceful degradation when agents encounter errors
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])