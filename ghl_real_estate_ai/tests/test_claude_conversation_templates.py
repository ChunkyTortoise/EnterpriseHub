"""
Test Suite for Claude Conversation Templates Service

Comprehensive tests for conversation template management, agent preferences,
customization, and analytics functionality.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from services.claude_conversation_templates import (
    ClaudeConversationTemplateService,
    ConversationTemplate,
    ConversationFlow,
    AgentConversationPreferences,
    ConversationAnalytics,
    ConversationScenario,
    AgentExperienceLevel,
    ConversationStyle,
    conversation_template_service,
    get_conversation_template,
    get_conversation_flow,
    customize_agent_prompt,
    update_conversation_preferences,
    track_conversation_effectiveness
)


class TestClaudeConversationTemplateService:
    """Test cases for Claude Conversation Template Service"""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ClaudeConversationTemplateService()
        self.test_agent_id = "test_agent_001"
        self.test_template_id = "test_template_001"
        self.test_session_id = "test_session_001"

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization and default templates."""
        assert len(self.service.templates) > 0
        assert len(self.service.flows) > 0
        assert isinstance(self.service.agent_preferences, dict)
        assert isinstance(self.service.analytics, list)

        # Check default templates exist
        template_scenarios = [t.scenario for t in self.service.templates.values()]
        assert ConversationScenario.LEAD_QUALIFICATION in template_scenarios
        assert ConversationScenario.PROPERTY_MATCHING in template_scenarios

    @pytest.mark.asyncio
    async def test_get_agent_preferences(self):
        """Test getting agent preferences."""
        # First call should create default preferences
        preferences = await self.service.get_agent_preferences(self.test_agent_id)

        assert preferences.agent_id == self.test_agent_id
        assert isinstance(preferences.experience_level, AgentExperienceLevel)
        assert isinstance(preferences.preferred_style, ConversationStyle)
        assert isinstance(preferences.favorite_templates, list)
        assert isinstance(preferences.custom_prompts, dict)
        assert isinstance(preferences.conversation_history, list)

        # Second call should return existing preferences
        same_preferences = await self.service.get_agent_preferences(self.test_agent_id)
        assert preferences.agent_id == same_preferences.agent_id

    @pytest.mark.asyncio
    async def test_update_agent_preferences(self):
        """Test updating agent preferences."""
        updates = {
            "experience_level": AgentExperienceLevel.EXPERT,
            "preferred_style": ConversationStyle.ANALYTICAL,
            "specializations": ["Luxury Properties", "Investment Properties"],
            "market_focus": ["Downtown", "Waterfront"]
        }

        updated_preferences = await self.service.update_agent_preferences(
            self.test_agent_id, updates
        )

        assert updated_preferences.experience_level == AgentExperienceLevel.EXPERT
        assert updated_preferences.preferred_style == ConversationStyle.ANALYTICAL
        assert "Luxury Properties" in updated_preferences.specializations
        assert "Downtown" in updated_preferences.market_focus
        assert updated_preferences.last_updated is not None

    @pytest.mark.asyncio
    async def test_get_template_by_scenario(self):
        """Test getting templates by scenario and agent preferences."""
        # Set up agent preferences
        await self.service.update_agent_preferences(
            self.test_agent_id,
            {
                "experience_level": AgentExperienceLevel.ROOKIE,
                "preferred_style": ConversationStyle.CONSULTATIVE
            }
        )

        template = await self.service.get_template(
            ConversationScenario.LEAD_QUALIFICATION,
            self.test_agent_id
        )

        assert template is not None
        assert template.scenario == ConversationScenario.LEAD_QUALIFICATION
        assert isinstance(template, ConversationTemplate)
        assert len(template.conversation_starters) > 0
        assert len(template.expected_outcomes) > 0

    @pytest.mark.asyncio
    async def test_get_template_with_context(self):
        """Test getting templates with context information."""
        context = {
            "lead_contact_info": {"name": "John Doe", "phone": "555-1234"},
            "initial_inquiry_details": {"property_type": "condo", "budget": 500000}
        }

        template = await self.service.get_template(
            ConversationScenario.PROPERTY_MATCHING,
            self.test_agent_id,
            context
        )

        assert template is not None
        assert template.scenario == ConversationScenario.PROPERTY_MATCHING

    @pytest.mark.asyncio
    async def test_customize_prompt(self):
        """Test prompt customization for agent and context."""
        # Get a template first
        template = await self.service.get_template(
            ConversationScenario.LEAD_QUALIFICATION,
            self.test_agent_id
        )

        context = {"lead_id": "lead_123", "budget": 750000}

        customized_prompt = await self.service.customize_prompt(
            template.id,
            self.test_agent_id,
            context
        )

        assert customized_prompt is not None
        assert len(customized_prompt) > len(template.system_prompt)
        assert self.test_agent_id in customized_prompt or "Agent Experience Level" in customized_prompt
        assert "Current Context" in customized_prompt

    @pytest.mark.asyncio
    async def test_conversation_flow_retrieval(self):
        """Test getting conversation flows."""
        flow = await self.service.get_conversation_flow(
            ConversationScenario.LEAD_QUALIFICATION,
            self.test_agent_id
        )

        assert flow is not None
        assert flow.scenario == ConversationScenario.LEAD_QUALIFICATION
        assert len(flow.steps) > 0
        assert flow.estimated_duration > 0

        # Check flow step structure
        first_step = flow.steps[0]
        assert "step" in first_step
        assert "name" in first_step
        assert "prompt" in first_step

    @pytest.mark.asyncio
    async def test_track_conversation_analytics(self):
        """Test conversation analytics tracking."""
        template = await self.service.get_template(
            ConversationScenario.LEAD_QUALIFICATION,
            self.test_agent_id
        )

        start_time = datetime.utcnow()
        await self.service.track_conversation_analytics(
            template_id=template.id,
            agent_id=self.test_agent_id,
            session_id=self.test_session_id,
            scenario=ConversationScenario.LEAD_QUALIFICATION,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30),
            outcome="successful_qualification",
            effectiveness_score=0.85,
            lead_id="lead_123",
            context_data={"budget_discovered": True},
            feedback_rating=5,
            notes="Excellent conversation flow"
        )

        # Check analytics was recorded
        assert len(self.service.analytics) > 0
        latest_analytics = self.service.analytics[-1]
        assert latest_analytics.template_id == template.id
        assert latest_analytics.agent_id == self.test_agent_id
        assert latest_analytics.effectiveness_score == 0.85

        # Check template effectiveness was updated
        updated_template = self.service.templates[template.id]
        assert updated_template.effectiveness_score > 0

    @pytest.mark.asyncio
    async def test_template_recommendations(self):
        """Test template recommendations for agents."""
        # Set up agent preferences
        await self.service.update_agent_preferences(
            self.test_agent_id,
            {
                "experience_level": AgentExperienceLevel.EXPERIENCED,
                "preferred_style": ConversationStyle.DATA_DRIVEN,
                "specializations": ["Market Analysis"],
                "favorite_templates": []
            }
        )

        context = {"market_data": True, "client_type": "investor"}

        recommendations = await self.service.get_template_recommendations(
            self.test_agent_id,
            context
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Check recommendation structure
        template, score = recommendations[0]
        assert isinstance(template, ConversationTemplate)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_template_scoring(self):
        """Test template scoring algorithm."""
        # Create test preferences
        preferences = AgentConversationPreferences(
            agent_id=self.test_agent_id,
            experience_level=AgentExperienceLevel.EXPERT,
            preferred_style=ConversationStyle.ANALYTICAL,
            favorite_templates=["test_template"],
            custom_prompts={},
            conversation_history=[],
            performance_metrics={},
            specializations=["Investment Properties"],
            market_focus=["Downtown"]
        )

        # Create test template that should score well
        template = ConversationTemplate(
            id="test_high_score",
            name="Test Template",
            scenario=ConversationScenario.MARKET_ANALYSIS,
            description="Test template",
            system_prompt="Test prompt",
            conversation_starters=["Test"],
            follow_up_prompts=["Test"],
            expected_outcomes=["Test"],
            required_context=["market_data"],
            experience_level=AgentExperienceLevel.EXPERT,  # Matches
            style=ConversationStyle.ANALYTICAL,  # Matches
            tags=["test"],
            effectiveness_score=0.9  # High effectiveness
        )

        context = {"market_data": True}
        score = await self.service._calculate_template_score(template, preferences, context)

        # Should score highly due to matches
        assert score > 0.5
        assert score <= 1.0

    @pytest.mark.asyncio
    async def test_dynamic_template_creation(self):
        """Test dynamic template creation when no match exists."""
        # Create preferences for a scenario with no templates
        preferences = AgentConversationPreferences(
            agent_id=self.test_agent_id,
            experience_level=AgentExperienceLevel.ROOKIE,
            preferred_style=ConversationStyle.DIRECT,
            favorite_templates=[],
            custom_prompts={},
            conversation_history=[],
            performance_metrics={},
            specializations=[],
            market_focus=[]
        )

        context = {"test_context": "value"}

        # This should create a dynamic template
        dynamic_template = await self.service._create_dynamic_template(
            ConversationScenario.CLOSING_PREPARATION,
            preferences,
            context
        )

        assert dynamic_template.id.startswith("dynamic_")
        assert dynamic_template.scenario == ConversationScenario.CLOSING_PREPARATION
        assert dynamic_template.experience_level == AgentExperienceLevel.ROOKIE
        assert dynamic_template.style == ConversationStyle.DIRECT
        assert "test_context" in dynamic_template.required_context

    @pytest.mark.asyncio
    async def test_export_import_agent_data(self):
        """Test exporting and importing agent data."""
        # Set up agent with data
        await self.service.update_agent_preferences(
            self.test_agent_id,
            {
                "experience_level": AgentExperienceLevel.EXPERT,
                "specializations": ["Luxury Properties"],
                "custom_prompts": {"lead_qualification": "Custom prompt"}
            }
        )

        # Add some analytics
        await self.service.track_conversation_analytics(
            template_id="test_template",
            agent_id=self.test_agent_id,
            session_id=self.test_session_id,
            scenario=ConversationScenario.LEAD_QUALIFICATION,
            effectiveness_score=0.8,
            start_time=datetime.utcnow()
        )

        # Export data
        exported_data = await self.service.export_agent_templates(self.test_agent_id)

        assert exported_data["agent_id"] == self.test_agent_id
        assert "preferences" in exported_data
        assert "analytics" in exported_data
        assert "export_date" in exported_data

        # Test import (create new service instance)
        new_service = ClaudeConversationTemplateService()
        import_success = await new_service.import_agent_templates(exported_data)

        assert import_success is True
        assert self.test_agent_id in new_service.agent_preferences

    def test_service_stats(self):
        """Test service statistics generation."""
        stats = self.service.get_service_stats()

        assert "total_templates" in stats
        assert "total_flows" in stats
        assert "total_agents" in stats
        assert "total_conversations" in stats
        assert "average_effectiveness" in stats
        assert "most_used_templates" in stats
        assert "scenarios_covered" in stats
        assert "service_health" in stats

        assert isinstance(stats["total_templates"], int)
        assert isinstance(stats["average_effectiveness"], float)
        assert isinstance(stats["most_used_templates"], list)
        assert isinstance(stats["scenarios_covered"], list)

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test invalid template ID
        with pytest.raises(ValueError):
            await self.service.customize_prompt(
                "nonexistent_template",
                self.test_agent_id,
                {}
            )

        # Test invalid scenario (should handle gracefully)
        template = await self.service.get_template(
            ConversationScenario.LEAD_QUALIFICATION,
            "invalid_agent",
            {}
        )
        assert template is not None  # Should return fallback


class TestConversationTemplateEnums:
    """Test conversation template enums and data structures."""

    def test_conversation_scenario_enum(self):
        """Test ConversationScenario enum values."""
        scenarios = list(ConversationScenario)
        assert len(scenarios) > 5
        assert ConversationScenario.LEAD_QUALIFICATION in scenarios
        assert ConversationScenario.PROPERTY_MATCHING in scenarios
        assert ConversationScenario.MARKET_ANALYSIS in scenarios

    def test_agent_experience_level_enum(self):
        """Test AgentExperienceLevel enum values."""
        levels = list(AgentExperienceLevel)
        assert AgentExperienceLevel.ROOKIE in levels
        assert AgentExperienceLevel.EXPERT in levels
        assert AgentExperienceLevel.TOP_PERFORMER in levels

    def test_conversation_style_enum(self):
        """Test ConversationStyle enum values."""
        styles = list(ConversationStyle)
        assert ConversationStyle.ANALYTICAL in styles
        assert ConversationStyle.RELATIONSHIP_FOCUSED in styles
        assert ConversationStyle.DATA_DRIVEN in styles


class TestConversationTemplateDataStructures:
    """Test data structure validation and functionality."""

    def test_conversation_template_creation(self):
        """Test ConversationTemplate data structure."""
        template = ConversationTemplate(
            id="test_template",
            name="Test Template",
            scenario=ConversationScenario.LEAD_QUALIFICATION,
            description="Test description",
            system_prompt="Test system prompt",
            conversation_starters=["Starter 1", "Starter 2"],
            follow_up_prompts=["Follow-up 1"],
            expected_outcomes=["Outcome 1"],
            required_context=["context1"],
            experience_level=AgentExperienceLevel.DEVELOPING,
            style=ConversationStyle.CONSULTATIVE,
            tags=["test", "qualification"]
        )

        assert template.id == "test_template"
        assert template.scenario == ConversationScenario.LEAD_QUALIFICATION
        assert len(template.conversation_starters) == 2
        assert template.last_updated is not None
        assert template.usage_count == 0
        assert template.effectiveness_score == 0.0

    def test_conversation_flow_creation(self):
        """Test ConversationFlow data structure."""
        flow = ConversationFlow(
            id="test_flow",
            name="Test Flow",
            scenario=ConversationScenario.LEAD_QUALIFICATION,
            description="Test flow description",
            steps=[
                {
                    "step": 1,
                    "name": "Initial Contact",
                    "prompt": "Test prompt",
                    "context_required": [],
                    "expected_output": "contact_assessment"
                }
            ],
            branching_rules={"high_urgency": "fast_track"},
            success_criteria=["Contact established"],
            fallback_strategies=["Email follow-up"],
            estimated_duration=15
        )

        assert flow.id == "test_flow"
        assert flow.scenario == ConversationScenario.LEAD_QUALIFICATION
        assert len(flow.steps) == 1
        assert flow.estimated_duration == 15
        assert "high_urgency" in flow.branching_rules

    def test_agent_conversation_preferences_creation(self):
        """Test AgentConversationPreferences data structure."""
        preferences = AgentConversationPreferences(
            agent_id="test_agent",
            experience_level=AgentExperienceLevel.EXPERIENCED,
            preferred_style=ConversationStyle.ANALYTICAL,
            favorite_templates=["template1", "template2"],
            custom_prompts={"scenario1": "custom prompt"},
            conversation_history=[],
            performance_metrics={"effectiveness": 0.85},
            specializations=["Luxury", "Commercial"],
            market_focus=["Downtown"]
        )

        assert preferences.agent_id == "test_agent"
        assert preferences.experience_level == AgentExperienceLevel.EXPERIENCED
        assert len(preferences.favorite_templates) == 2
        assert "Luxury" in preferences.specializations
        assert preferences.last_updated is not None

    def test_conversation_analytics_creation(self):
        """Test ConversationAnalytics data structure."""
        analytics = ConversationAnalytics(
            template_id="template_123",
            agent_id="agent_456",
            session_id="session_789",
            scenario=ConversationScenario.PROPERTY_MATCHING,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(minutes=30),
            outcome="successful_match",
            effectiveness_score=0.9,
            lead_id="lead_101",
            context_data={"property_type": "condo"},
            feedback_rating=5,
            notes="Excellent conversation"
        )

        assert analytics.template_id == "template_123"
        assert analytics.scenario == ConversationScenario.PROPERTY_MATCHING
        assert analytics.effectiveness_score == 0.9
        assert analytics.context_data["property_type"] == "condo"


class TestConversationTemplateIntegration:
    """Integration tests for conversation template system."""

    @pytest.mark.asyncio
    async def test_complete_conversation_workflow(self):
        """Test complete conversation workflow from start to finish."""
        service = ClaudeConversationTemplateService()
        agent_id = "integration_test_agent"

        # Step 1: Set agent preferences
        await service.update_agent_preferences(
            agent_id,
            {
                "experience_level": AgentExperienceLevel.EXPERIENCED,
                "preferred_style": ConversationStyle.CONSULTATIVE,
                "specializations": ["First-Time Buyers"]
            }
        )

        # Step 2: Get appropriate template
        template = await service.get_template(
            ConversationScenario.LEAD_QUALIFICATION,
            agent_id
        )

        assert template is not None

        # Step 3: Customize prompt
        context = {"lead_id": "lead_999", "inquiry_type": "first_time_buyer"}
        customized_prompt = await service.customize_prompt(
            template.id,
            agent_id,
            context
        )

        assert "First-Time Buyers" in customized_prompt or "first_time_buyer" in customized_prompt

        # Step 4: Track conversation
        start_time = datetime.utcnow()
        await service.track_conversation_analytics(
            template.id,
            agent_id,
            "integration_session",
            ConversationScenario.LEAD_QUALIFICATION,
            start_time,
            effectiveness_score=0.8,
            outcome="qualified_lead"
        )

        # Step 5: Get recommendations
        recommendations = await service.get_template_recommendations(agent_id, context)
        assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_template_usage_tracking(self):
        """Test template usage tracking and effectiveness updates."""
        service = ClaudeConversationTemplateService()
        agent_id = "usage_test_agent"

        # Get initial template
        template = await service.get_template(
            ConversationScenario.MARKET_ANALYSIS,
            agent_id
        )

        initial_usage = template.usage_count
        initial_effectiveness = template.effectiveness_score

        # Use template multiple times with different effectiveness scores
        effectiveness_scores = [0.7, 0.8, 0.9, 0.6, 0.85]

        for i, score in enumerate(effectiveness_scores):
            await service.track_conversation_analytics(
                template.id,
                agent_id,
                f"session_{i}",
                ConversationScenario.MARKET_ANALYSIS,
                datetime.utcnow(),
                effectiveness_score=score,
                outcome=f"outcome_{i}"
            )

        # Check template was updated
        updated_template = service.templates[template.id]
        assert updated_template.usage_count > initial_usage

        # Effectiveness should be updated (running average)
        assert updated_template.effectiveness_score != initial_effectiveness

    @pytest.mark.asyncio
    async def test_fallback_mechanisms(self):
        """Test fallback mechanisms for edge cases."""
        service = ClaudeConversationTemplateService()

        # Test with unknown agent
        template = await service.get_template(
            ConversationScenario.LEAD_QUALIFICATION,
            "unknown_agent_12345"
        )
        assert template is not None  # Should create default preferences and return template

        # Test with scenario that has no specific templates
        # (This might create a dynamic template)
        flow = await service.get_conversation_flow(
            ConversationScenario.CLOSING_PREPARATION,
            "test_agent"
        )
        assert flow is not None  # Should return a basic flow


# Utility functions for testing
@pytest.fixture
async def sample_template():
    """Create a sample template for testing."""
    return ConversationTemplate(
        id="sample_template_001",
        name="Sample Lead Qualification",
        scenario=ConversationScenario.LEAD_QUALIFICATION,
        description="Sample template for testing",
        system_prompt="You are a helpful real estate assistant for lead qualification.",
        conversation_starters=["Tell me about your ideal property"],
        follow_up_prompts=["What's your budget range?"],
        expected_outcomes=["Budget identified", "Timeline established"],
        required_context=["lead_contact"],
        experience_level=AgentExperienceLevel.DEVELOPING,
        style=ConversationStyle.CONSULTATIVE,
        tags=["sample", "test", "qualification"]
    )


@pytest.fixture
async def sample_agent_preferences():
    """Create sample agent preferences for testing."""
    return AgentConversationPreferences(
        agent_id="sample_agent_001",
        experience_level=AgentExperienceLevel.EXPERIENCED,
        preferred_style=ConversationStyle.ANALYTICAL,
        favorite_templates=["template_1", "template_2"],
        custom_prompts={"lead_qualification": "Focus on investment potential"},
        conversation_history=[],
        performance_metrics={"effectiveness": 0.85, "satisfaction": 4.5},
        specializations=["Investment Properties", "Market Analysis"],
        market_focus=["Downtown", "Waterfront"]
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])