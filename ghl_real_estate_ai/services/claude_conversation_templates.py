"""
Claude Conversation Templates Service

Provides agent-specific conversation templates, prompts, and adaptive conversation flows
for real estate scenarios. Enhances agent productivity with pre-built, domain-specific
Claude interactions.
"""

import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConversationScenario(Enum):
    """Different real estate conversation scenarios."""
    LEAD_QUALIFICATION = "lead_qualification"
    PROPERTY_MATCHING = "property_matching"
    MARKET_ANALYSIS = "market_analysis"
    FOLLOW_UP_STRATEGY = "follow_up_strategy"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING_PREPARATION = "closing_preparation"
    CLIENT_CONSULTATION = "client_consultation"
    PRICING_STRATEGY = "pricing_strategy"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    DAILY_BRIEFING = "daily_briefing"


class AgentExperienceLevel(Enum):
    """Agent experience levels for template adaptation."""
    ROOKIE = "rookie"
    DEVELOPING = "developing"
    EXPERIENCED = "experienced"
    EXPERT = "expert"
    TOP_PERFORMER = "top_performer"


class ConversationStyle(Enum):
    """Different conversation styles for agent personalization."""
    ANALYTICAL = "analytical"
    RELATIONSHIP_FOCUSED = "relationship_focused"
    DIRECT = "direct"
    CONSULTATIVE = "consultative"
    DATA_DRIVEN = "data_driven"


@dataclass
class ConversationTemplate:
    """Template for Claude conversations."""
    id: str
    name: str
    scenario: ConversationScenario
    description: str
    system_prompt: str
    conversation_starters: List[str]
    follow_up_prompts: List[str]
    expected_outcomes: List[str]
    required_context: List[str]
    experience_level: AgentExperienceLevel
    style: ConversationStyle
    tags: List[str]
    usage_count: int = 0
    effectiveness_score: float = 0.0
    last_updated: datetime = None
    created_by: str = "system"

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.utcnow()


@dataclass
class ConversationFlow:
    """Multi-step conversation flow with branching logic."""
    id: str
    name: str
    scenario: ConversationScenario
    description: str
    steps: List[Dict[str, Any]]
    branching_rules: Dict[str, Any]
    success_criteria: List[str]
    fallback_strategies: List[str]
    estimated_duration: int  # minutes
    success_rate: float = 0.0
    usage_count: int = 0


@dataclass
class AgentConversationPreferences:
    """Agent-specific conversation preferences and customizations."""
    agent_id: str
    experience_level: AgentExperienceLevel
    preferred_style: ConversationStyle
    favorite_templates: List[str]
    custom_prompts: Dict[str, str]
    conversation_history: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    specializations: List[str]
    market_focus: List[str]
    last_updated: datetime = None

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.utcnow()


@dataclass
class ConversationAnalytics:
    """Analytics for conversation template usage and effectiveness."""
    template_id: str
    agent_id: str
    session_id: str
    scenario: ConversationScenario
    start_time: datetime
    end_time: Optional[datetime]
    outcome: Optional[str]
    effectiveness_score: float
    lead_id: Optional[str]
    context_data: Dict[str, Any]
    feedback_rating: Optional[int]
    notes: Optional[str]


class ClaudeConversationTemplateService:
    """Service for managing Claude conversation templates and agent-specific prompts."""

    def __init__(self):
        """Initialize the conversation template service."""
        self.templates: Dict[str, ConversationTemplate] = {}
        self.flows: Dict[str, ConversationFlow] = {}
        self.agent_preferences: Dict[str, AgentConversationPreferences] = {}
        self.analytics: List[ConversationAnalytics] = []
        self._initialize_default_templates()
        self._initialize_default_flows()

    def _initialize_default_templates(self):
        """Initialize default conversation templates."""
        templates = [
            ConversationTemplate(
                id="lead_qual_rookie",
                name="Lead Qualification - Rookie Agent",
                scenario=ConversationScenario.LEAD_QUALIFICATION,
                description="Structured lead qualification for new agents",
                system_prompt="""You are an AI assistant helping a new real estate agent qualify leads.
                Provide structured, step-by-step guidance focusing on the basics: budget, timeline,
                location preferences, and motivation. Use simple, clear language and include specific
                questions the agent should ask. Always explain why each question is important.""",
                conversation_starters=[
                    "Help me qualify this new lead - what should I ask first?",
                    "I have a lead who seems interested but vague - how do I get specifics?",
                    "What's the most important information to gather from a new prospect?"
                ],
                follow_up_prompts=[
                    "Based on their responses, what should I ask next?",
                    "They seem hesitant about budget - how do I approach this sensitively?",
                    "What red flags should I watch for in their answers?"
                ],
                expected_outcomes=[
                    "Clear budget range identified",
                    "Timeline for purchase established",
                    "Location preferences defined",
                    "Motivation level assessed"
                ],
                required_context=["lead_contact_info", "initial_inquiry_details"],
                experience_level=AgentExperienceLevel.ROOKIE,
                style=ConversationStyle.CONSULTATIVE,
                tags=["qualification", "beginner", "structured"]
            ),
            ConversationTemplate(
                id="property_match_expert",
                name="Advanced Property Matching - Expert Agent",
                scenario=ConversationScenario.PROPERTY_MATCHING,
                description="Sophisticated property matching for experienced agents",
                system_prompt="""You are an AI assistant helping an expert real estate agent with
                advanced property matching. Focus on nuanced client preferences, market positioning,
                investment potential, and strategic considerations. Provide insights on market trends,
                comparative analysis, and negotiation positioning. Assume the agent has deep market knowledge.""",
                conversation_starters=[
                    "Analyze these properties for my high-net-worth client's portfolio strategy",
                    "Compare these listings considering current market dynamics and future appreciation",
                    "What strategic advantages does each property offer for my investor client?"
                ],
                follow_up_prompts=[
                    "How do these properties position against recent comparable sales?",
                    "What negotiation strategy would you recommend for each property?",
                    "Identify any potential issues or opportunities I might have missed"
                ],
                expected_outcomes=[
                    "Strategic property recommendations",
                    "Market positioning analysis",
                    "Negotiation strategy developed",
                    "Investment potential assessed"
                ],
                required_context=["client_investment_goals", "market_analysis", "property_details"],
                experience_level=AgentExperienceLevel.EXPERT,
                style=ConversationStyle.ANALYTICAL,
                tags=["property_matching", "expert", "investment", "strategy"]
            ),
            ConversationTemplate(
                id="market_analysis_data_driven",
                name="Market Analysis - Data-Driven Approach",
                scenario=ConversationScenario.MARKET_ANALYSIS,
                description="Data-focused market analysis and insights",
                system_prompt="""You are an AI assistant specializing in data-driven real estate
                market analysis. Focus on quantitative metrics, statistical trends, predictive
                indicators, and evidence-based insights. Provide specific numbers, percentages,
                and data points. Support all recommendations with concrete market data.""",
                conversation_starters=[
                    "Analyze the current market metrics for this area - what do the numbers tell us?",
                    "What statistical indicators suggest about future price movements?",
                    "Compare this market's performance against regional and national benchmarks"
                ],
                follow_up_prompts=[
                    "What specific data points support this market assessment?",
                    "How do these metrics compare to historical patterns?",
                    "What predictive indicators should we monitor going forward?"
                ],
                expected_outcomes=[
                    "Quantitative market assessment",
                    "Statistical trend analysis",
                    "Predictive market indicators",
                    "Data-supported recommendations"
                ],
                required_context=["market_data", "historical_trends", "regional_comparisons"],
                experience_level=AgentExperienceLevel.EXPERIENCED,
                style=ConversationStyle.DATA_DRIVEN,
                tags=["market_analysis", "data", "statistics", "trends"]
            ),
            ConversationTemplate(
                id="objection_handling_relationship",
                name="Objection Handling - Relationship-Focused",
                scenario=ConversationScenario.OBJECTION_HANDLING,
                description="Empathetic objection handling building relationships",
                system_prompt="""You are an AI assistant helping agents handle objections through
                relationship-building and empathy. Focus on understanding the client's underlying
                concerns, validating their feelings, and building trust. Provide responses that
                acknowledge emotions while addressing practical concerns. Emphasize long-term
                relationship building over immediate sales.""",
                conversation_starters=[
                    "My client is hesitant about the price - how do I address this while maintaining trust?",
                    "They're concerned about the timing - help me understand and address their fears",
                    "I'm getting pushback on our recommendation - how do I handle this sensitively?"
                ],
                follow_up_prompts=[
                    "How do I validate their concerns while still moving forward?",
                    "What questions can help me understand their real underlying issues?",
                    "How do I maintain the relationship if they're not ready to proceed?"
                ],
                expected_outcomes=[
                    "Client concerns understood and addressed",
                    "Trust and rapport maintained",
                    "Path forward established",
                    "Relationship strengthened"
                ],
                required_context=["client_history", "previous_conversations", "relationship_status"],
                experience_level=AgentExperienceLevel.DEVELOPING,
                style=ConversationStyle.RELATIONSHIP_FOCUSED,
                tags=["objection_handling", "relationship", "empathy", "trust"]
            )
        ]

        for template in templates:
            self.templates[template.id] = template

    def _initialize_default_flows(self):
        """Initialize default conversation flows."""
        flows = [
            ConversationFlow(
                id="complete_lead_qualification_flow",
                name="Complete Lead Qualification Flow",
                scenario=ConversationScenario.LEAD_QUALIFICATION,
                description="End-to-end lead qualification process",
                steps=[
                    {
                        "step": 1,
                        "name": "Initial Contact Assessment",
                        "prompt": "Assess this lead's initial inquiry and recommend the best approach for first contact",
                        "context_required": ["inquiry_details", "contact_method"],
                        "expected_output": "contact_strategy"
                    },
                    {
                        "step": 2,
                        "name": "Budget and Timeline Discovery",
                        "prompt": "Help me discover their budget range and timeline without being too direct",
                        "context_required": ["contact_strategy", "initial_response"],
                        "expected_output": "budget_timeline_assessment"
                    },
                    {
                        "step": 3,
                        "name": "Needs and Preferences Analysis",
                        "prompt": "Analyze their stated needs and help me uncover hidden preferences",
                        "context_required": ["budget_timeline_assessment", "stated_needs"],
                        "expected_output": "comprehensive_needs_profile"
                    },
                    {
                        "step": 4,
                        "name": "Motivation and Urgency Evaluation",
                        "prompt": "Evaluate their motivation level and true urgency to buy/sell",
                        "context_required": ["comprehensive_needs_profile", "conversation_tone"],
                        "expected_output": "motivation_urgency_score"
                    },
                    {
                        "step": 5,
                        "name": "Next Steps and Follow-up Strategy",
                        "prompt": "Based on all information gathered, recommend the optimal next steps and follow-up approach",
                        "context_required": ["all_previous_outputs"],
                        "expected_output": "action_plan_with_timeline"
                    }
                ],
                branching_rules={
                    "high_urgency": "accelerated_timeline",
                    "budget_concerns": "financial_consultation_branch",
                    "multiple_decision_makers": "stakeholder_engagement_branch",
                    "first_time_buyer": "education_focused_branch"
                },
                success_criteria=[
                    "Budget range identified within 20%",
                    "Timeline established with specific dates",
                    "Decision-making process understood",
                    "Next appointment scheduled"
                ],
                fallback_strategies=[
                    "If budget discussion stalls, focus on monthly payment comfort",
                    "If timeline is vague, anchor with market conditions",
                    "If multiple stakeholders, request group meeting"
                ],
                estimated_duration=30
            )
        ]

        for flow in flows:
            self.flows[flow.id] = flow

    async def get_template(
        self,
        scenario: ConversationScenario,
        agent_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ConversationTemplate:
        """Get the best template for the scenario and agent."""
        try:
            # Get agent preferences
            preferences = await self.get_agent_preferences(agent_id)

            # Filter templates by scenario
            matching_templates = [
                template for template in self.templates.values()
                if template.scenario == scenario
            ]

            if not matching_templates:
                return await self._create_dynamic_template(scenario, preferences, context)

            # Score and rank templates based on agent preferences
            scored_templates = []
            for template in matching_templates:
                score = await self._calculate_template_score(template, preferences, context)
                scored_templates.append((template, score))

            # Return the highest-scoring template
            best_template = max(scored_templates, key=lambda x: x[1])[0]
            best_template.usage_count += 1

            return best_template

        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            # Return a basic template as fallback
            return await self._create_basic_template(scenario)

    async def get_agent_preferences(self, agent_id: str) -> AgentConversationPreferences:
        """Get or create agent conversation preferences."""
        if agent_id not in self.agent_preferences:
            # Create default preferences for new agent
            self.agent_preferences[agent_id] = AgentConversationPreferences(
                agent_id=agent_id,
                experience_level=AgentExperienceLevel.DEVELOPING,
                preferred_style=ConversationStyle.CONSULTATIVE,
                favorite_templates=[],
                custom_prompts={},
                conversation_history=[],
                performance_metrics={},
                specializations=[],
                market_focus=[]
            )

        return self.agent_preferences[agent_id]

    async def update_agent_preferences(
        self,
        agent_id: str,
        updates: Dict[str, Any]
    ) -> AgentConversationPreferences:
        """Update agent conversation preferences."""
        preferences = await self.get_agent_preferences(agent_id)

        for key, value in updates.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)

        preferences.last_updated = datetime.utcnow()
        return preferences

    async def get_conversation_flow(
        self,
        scenario: ConversationScenario,
        agent_id: str
    ) -> ConversationFlow:
        """Get the best conversation flow for the scenario and agent."""
        try:
            preferences = await self.get_agent_preferences(agent_id)

            # Find flows matching the scenario
            matching_flows = [
                flow for flow in self.flows.values()
                if flow.scenario == scenario
            ]

            if not matching_flows:
                return await self._create_basic_flow(scenario)

            # For now, return the first matching flow
            # In the future, we could add scoring based on agent preferences
            best_flow = matching_flows[0]
            best_flow.usage_count += 1

            return best_flow

        except Exception as e:
            logger.error(f"Error getting conversation flow: {str(e)}")
            return await self._create_basic_flow(scenario)

    async def customize_prompt(
        self,
        template_id: str,
        agent_id: str,
        context: Dict[str, Any]
    ) -> str:
        """Customize a prompt for specific agent and context."""
        try:
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")

            preferences = await self.get_agent_preferences(agent_id)

            # Start with base system prompt
            customized_prompt = template.system_prompt

            # Add agent-specific customizations
            customized_prompt += f"\n\nAgent Experience Level: {preferences.experience_level.value}"
            customized_prompt += f"\nPreferred Style: {preferences.preferred_style.value}"

            # Add specializations if available
            if preferences.specializations:
                customized_prompt += f"\nAgent Specializations: {', '.join(preferences.specializations)}"

            # Add market focus if available
            if preferences.market_focus:
                customized_prompt += f"\nMarket Focus: {', '.join(preferences.market_focus)}"

            # Add context-specific information
            if context:
                customized_prompt += f"\n\nCurrent Context:\n{json.dumps(context, indent=2)}"

            # Add any custom prompts from agent preferences
            if template.scenario.value in preferences.custom_prompts:
                custom_addition = preferences.custom_prompts[template.scenario.value]
                customized_prompt += f"\n\nAgent-Specific Instructions:\n{custom_addition}"

            return customized_prompt

        except Exception as e:
            logger.error(f"Error customizing prompt: {str(e)}")
            return template.system_prompt if template else "You are a helpful real estate AI assistant."

    async def track_conversation_analytics(
        self,
        template_id: str,
        agent_id: str,
        session_id: str,
        scenario: ConversationScenario,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        outcome: Optional[str] = None,
        effectiveness_score: float = 0.0,
        lead_id: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        feedback_rating: Optional[int] = None,
        notes: Optional[str] = None
    ):
        """Track analytics for conversation usage."""
        analytics = ConversationAnalytics(
            template_id=template_id,
            agent_id=agent_id,
            session_id=session_id,
            scenario=scenario,
            start_time=start_time,
            end_time=end_time or datetime.utcnow(),
            outcome=outcome,
            effectiveness_score=effectiveness_score,
            lead_id=lead_id,
            context_data=context_data or {},
            feedback_rating=feedback_rating,
            notes=notes
        )

        self.analytics.append(analytics)

        # Update template effectiveness
        if template_id in self.templates:
            template = self.templates[template_id]
            # Simple running average for now
            template.effectiveness_score = (
                template.effectiveness_score * template.usage_count + effectiveness_score
            ) / (template.usage_count + 1)

    async def get_template_recommendations(
        self,
        agent_id: str,
        current_context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ConversationTemplate, float]]:
        """Get template recommendations for an agent."""
        try:
            preferences = await self.get_agent_preferences(agent_id)
            recommendations = []

            for template in self.templates.values():
                score = await self._calculate_template_score(template, preferences, current_context)
                if score > 0.3:  # Only recommend templates with reasonable scores
                    recommendations.append((template, score))

            # Sort by score descending
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:10]  # Return top 10

        except Exception as e:
            logger.error(f"Error getting template recommendations: {str(e)}")
            return []

    async def _calculate_template_score(
        self,
        template: ConversationTemplate,
        preferences: AgentConversationPreferences,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate a score for how well a template matches agent preferences."""
        score = 0.0

        # Experience level match
        if template.experience_level == preferences.experience_level:
            score += 0.3
        elif abs(list(AgentExperienceLevel).index(template.experience_level) -
                list(AgentExperienceLevel).index(preferences.experience_level)) <= 1:
            score += 0.15

        # Style preference match
        if template.style == preferences.preferred_style:
            score += 0.25

        # Favorite templates boost
        if template.id in preferences.favorite_templates:
            score += 0.2

        # Effectiveness score
        score += template.effectiveness_score * 0.15

        # Usage popularity (but not too much weight)
        if template.usage_count > 0:
            score += min(template.usage_count / 100.0, 0.1)

        # Context relevance (if available)
        if context and template.required_context:
            matching_context = sum(1 for req in template.required_context if req in context)
            context_score = matching_context / len(template.required_context) * 0.1
            score += context_score

        return min(score, 1.0)  # Cap at 1.0

    async def _create_dynamic_template(
        self,
        scenario: ConversationScenario,
        preferences: AgentConversationPreferences,
        context: Optional[Dict[str, Any]]
    ) -> ConversationTemplate:
        """Create a dynamic template when no matching template exists."""
        template_id = f"dynamic_{scenario.value}_{preferences.agent_id}_{int(datetime.utcnow().timestamp())}"

        return ConversationTemplate(
            id=template_id,
            name=f"Dynamic {scenario.value.replace('_', ' ').title()}",
            scenario=scenario,
            description=f"Dynamically generated template for {scenario.value}",
            system_prompt=f"You are an AI assistant helping with {scenario.value.replace('_', ' ')}. "
                         f"Adapt your responses to a {preferences.experience_level.value} agent "
                         f"who prefers a {preferences.preferred_style.value} approach.",
            conversation_starters=[
                f"Help me with this {scenario.value.replace('_', ' ')} situation",
                f"I need guidance on {scenario.value.replace('_', ' ')}",
                f"What's the best approach for {scenario.value.replace('_', ' ')}?"
            ],
            follow_up_prompts=[
                "What should I do next?",
                "How do I handle any objections?",
                "What are the key points to remember?"
            ],
            expected_outcomes=[
                f"Clear {scenario.value} strategy",
                "Actionable next steps",
                "Improved client relationship"
            ],
            required_context=list(context.keys()) if context else [],
            experience_level=preferences.experience_level,
            style=preferences.preferred_style,
            tags=["dynamic", scenario.value],
            created_by=f"system_dynamic_{preferences.agent_id}"
        )

    async def _create_basic_template(self, scenario: ConversationScenario) -> ConversationTemplate:
        """Create a basic template as fallback."""
        return ConversationTemplate(
            id=f"basic_{scenario.value}",
            name=f"Basic {scenario.value.replace('_', ' ').title()}",
            scenario=scenario,
            description=f"Basic template for {scenario.value}",
            system_prompt=f"You are a helpful real estate AI assistant specialized in {scenario.value.replace('_', ' ')}.",
            conversation_starters=[f"Help me with {scenario.value.replace('_', ' ')}"],
            follow_up_prompts=["What should I do next?"],
            expected_outcomes=["Clear guidance"],
            required_context=[],
            experience_level=AgentExperienceLevel.DEVELOPING,
            style=ConversationStyle.CONSULTATIVE,
            tags=["basic", scenario.value]
        )

    async def _create_basic_flow(self, scenario: ConversationScenario) -> ConversationFlow:
        """Create a basic conversation flow as fallback."""
        return ConversationFlow(
            id=f"basic_flow_{scenario.value}",
            name=f"Basic {scenario.value.replace('_', ' ').title()} Flow",
            scenario=scenario,
            description=f"Basic conversation flow for {scenario.value}",
            steps=[
                {
                    "step": 1,
                    "name": "Initial Assessment",
                    "prompt": f"Help me assess this {scenario.value.replace('_', ' ')} situation",
                    "context_required": [],
                    "expected_output": "initial_assessment"
                },
                {
                    "step": 2,
                    "name": "Action Planning",
                    "prompt": "Based on the assessment, what should I do next?",
                    "context_required": ["initial_assessment"],
                    "expected_output": "action_plan"
                }
            ],
            branching_rules={},
            success_criteria=[f"Clear {scenario.value} outcome"],
            fallback_strategies=["Request additional guidance if needed"],
            estimated_duration=15
        )

    async def export_agent_templates(self, agent_id: str) -> Dict[str, Any]:
        """Export agent's templates and preferences for backup/transfer."""
        preferences = await self.get_agent_preferences(agent_id)

        agent_analytics = [
            asdict(analytics) for analytics in self.analytics
            if analytics.agent_id == agent_id
        ]

        return {
            "agent_id": agent_id,
            "preferences": asdict(preferences),
            "favorite_templates": [
                asdict(self.templates[template_id])
                for template_id in preferences.favorite_templates
                if template_id in self.templates
            ],
            "analytics": agent_analytics,
            "export_date": datetime.utcnow().isoformat()
        }

    async def import_agent_templates(self, agent_data: Dict[str, Any]) -> bool:
        """Import agent templates and preferences from exported data."""
        try:
            agent_id = agent_data["agent_id"]

            # Import preferences
            preferences_data = agent_data["preferences"]
            preferences = AgentConversationPreferences(**preferences_data)
            self.agent_preferences[agent_id] = preferences

            # Import favorite templates
            for template_data in agent_data.get("favorite_templates", []):
                template = ConversationTemplate(**template_data)
                self.templates[template.id] = template

            return True

        except Exception as e:
            logger.error(f"Error importing agent templates: {str(e)}")
            return False

    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics and health metrics."""
        total_templates = len(self.templates)
        total_flows = len(self.flows)
        total_agents = len(self.agent_preferences)
        total_conversations = len(self.analytics)

        # Calculate average effectiveness
        avg_effectiveness = sum(t.effectiveness_score for t in self.templates.values()) / max(total_templates, 1)

        # Most used templates
        most_used = sorted(self.templates.values(), key=lambda x: x.usage_count, reverse=True)[:5]

        return {
            "total_templates": total_templates,
            "total_flows": total_flows,
            "total_agents": total_agents,
            "total_conversations": total_conversations,
            "average_effectiveness": avg_effectiveness,
            "most_used_templates": [{"name": t.name, "usage_count": t.usage_count} for t in most_used],
            "scenarios_covered": list(set(t.scenario.value for t in self.templates.values())),
            "service_health": "healthy" if total_templates > 0 else "needs_initialization"
        }


# Global service instance
conversation_template_service = ClaudeConversationTemplateService()


# Convenience functions for easy import
async def get_conversation_template(
    scenario: ConversationScenario,
    agent_id: str,
    context: Optional[Dict[str, Any]] = None
) -> ConversationTemplate:
    """Get a conversation template for the specified scenario and agent."""
    return await conversation_template_service.get_template(scenario, agent_id, context)


async def get_conversation_flow(
    scenario: ConversationScenario,
    agent_id: str
) -> ConversationFlow:
    """Get a conversation flow for the specified scenario and agent."""
    return await conversation_template_service.get_conversation_flow(scenario, agent_id)


async def customize_agent_prompt(
    template_id: str,
    agent_id: str,
    context: Dict[str, Any]
) -> str:
    """Customize a prompt for specific agent and context."""
    return await conversation_template_service.customize_prompt(template_id, agent_id, context)


async def update_conversation_preferences(
    agent_id: str,
    updates: Dict[str, Any]
) -> AgentConversationPreferences:
    """Update agent conversation preferences."""
    return await conversation_template_service.update_agent_preferences(agent_id, updates)


async def track_conversation_effectiveness(
    template_id: str,
    agent_id: str,
    session_id: str,
    scenario: ConversationScenario,
    effectiveness_score: float,
    **kwargs
):
    """Track conversation effectiveness for analytics."""
    await conversation_template_service.track_conversation_analytics(
        template_id=template_id,
        agent_id=agent_id,
        session_id=session_id,
        scenario=scenario,
        start_time=datetime.utcnow(),
        effectiveness_score=effectiveness_score,
        **kwargs
    )