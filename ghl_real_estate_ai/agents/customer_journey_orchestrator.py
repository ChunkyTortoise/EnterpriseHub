"""
Customer Journey Orchestrator - End-to-End Experience Coordination
Orchestrates the complete customer journey across all 40+ specialized agents.

This orchestrator ensures seamless handoffs, optimal experience flow, and intelligent
agent coordination based on customer context, preferences, and journey stage.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re

from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.agents.claude_concierge_agent import get_claude_concierge
from ghl_real_estate_ai.agents.enhanced_bot_orchestrator import get_enhanced_bot_orchestrator
from ghl_real_estate_ai.agents.property_intelligence_agent import get_property_intelligence_agent
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class JourneyStage(Enum):
    """Customer journey stages."""
    DISCOVERY = "discovery"               # Initial awareness/research
    EXPLORATION = "exploration"           # Active property searching
    EVALUATION = "evaluation"            # Comparing options/analysis
    NEGOTIATION = "negotiation"          # Making offers/negotiating
    TRANSACTION = "transaction"          # Under contract/closing
    OWNERSHIP = "ownership"              # Post-purchase support
    SELLING = "selling"                  # Property disposition

class CustomerType(Enum):
    """Customer type classifications."""
    FIRST_TIME_BUYER = "first_time_buyer"
    EXPERIENCED_BUYER = "experienced_buyer"
    INVESTOR = "investor"
    SELLER = "seller"
    DEVELOPER = "developer"
    COMMERCIAL_CLIENT = "commercial_client"

class JourneyPriority(Enum):
    """Priority levels for journey optimization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    VIP = "vip"

class AgentHandoffType(Enum):
    """Types of agent handoffs."""
    SEQUENTIAL = "sequential"           # One agent after another
    COLLABORATIVE = "collaborative"    # Multiple agents working together
    ESCALATION = "escalation"          # Moving to higher-level agent
    SPECIALIZATION = "specialization"  # Moving to domain expert
    FALLBACK = "fallback"              # Falling back to simpler agent

@dataclass
class CustomerProfile:
    """Comprehensive customer profile."""
    customer_id: str
    customer_type: CustomerType
    journey_stage: JourneyStage
    priority_level: JourneyPriority

    # Preferences and characteristics
    communication_preference: str  # "sms", "email", "phone", "chat"
    response_speed_preference: str  # "immediate", "same_day", "flexible"
    information_depth_preference: str  # "brief", "moderate", "detailed"
    decision_making_style: str  # "analytical", "intuitive", "collaborative"

    # Financial profile
    budget_range: Optional[Tuple[int, int]] = None
    financing_status: Optional[str] = None
    investment_experience: str = "beginner"  # beginner, intermediate, advanced

    # Behavioral patterns
    engagement_score: float = 0.0
    responsiveness_score: float = 0.0
    conversion_likelihood: float = 0.0
    satisfaction_score: float = 0.0

    # Journey tracking
    journey_start_date: datetime = field(default_factory=datetime.now)
    current_properties: List[str] = field(default_factory=list)
    completed_actions: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    success_moments: List[str] = field(default_factory=list)

@dataclass
class JourneyStep:
    """Individual step in the customer journey."""
    step_id: str
    step_name: str
    description: str
    required_agents: List[str]
    estimated_duration: str
    success_criteria: List[str]
    exit_conditions: List[str]
    next_steps: List[str]

@dataclass
class AgentHandoff:
    """Agent handoff coordination."""
    from_agent: str
    to_agent: str
    handoff_type: AgentHandoffType
    context_data: Dict[str, Any]
    handoff_reason: str
    priority: JourneyPriority
    estimated_completion_time: Optional[datetime] = None

@dataclass
class JourneyOptimization:
    """Journey optimization recommendations."""
    optimization_type: str
    current_performance: float
    target_performance: float
    recommended_changes: List[str]
    expected_impact: str
    implementation_complexity: str

class JourneyTemplateEngine:
    """Manages journey templates for different customer types."""

    def __init__(self):
        self.journey_templates = self._load_journey_templates()

    def _load_journey_templates(self) -> Dict[str, List[JourneyStep]]:
        """Load predefined journey templates."""
        return {
            "first_time_buyer": [
                JourneyStep(
                    step_id="ftb_001",
                    step_name="Education & Onboarding",
                    description="Educate first-time buyer on process and requirements",
                    required_agents=["claude_concierge", "adaptive_jorge"],
                    estimated_duration="2-5 days",
                    success_criteria=["Process understanding confirmed", "Budget established"],
                    exit_conditions=["Customer decides not to proceed"],
                    next_steps=["ftb_002"]
                ),
                JourneyStep(
                    step_id="ftb_002",
                    step_name="Financial Qualification",
                    description="Establish financing options and budget constraints",
                    required_agents=["adaptive_jorge", "realtime_intent"],
                    estimated_duration="3-7 days",
                    success_criteria=["Pre-approval obtained", "Budget finalized"],
                    exit_conditions=["Financing not available"],
                    next_steps=["ftb_003"]
                ),
                JourneyStep(
                    step_id="ftb_003",
                    step_name="Property Search",
                    description="Search and identify potential properties",
                    required_agents=["predictive_lead", "property_intelligence"],
                    estimated_duration="2-6 weeks",
                    success_criteria=["Properties identified", "Showing scheduled"],
                    exit_conditions=["No suitable properties found"],
                    next_steps=["ftb_004"]
                ),
                JourneyStep(
                    step_id="ftb_004",
                    step_name="Property Evaluation",
                    description="Detailed analysis of target properties",
                    required_agents=["property_intelligence", "cma_generator"],
                    estimated_duration="1-2 weeks",
                    success_criteria=["Property analyzed", "Decision made"],
                    exit_conditions=["Property not suitable"],
                    next_steps=["ftb_005"]
                ),
                JourneyStep(
                    step_id="ftb_005",
                    step_name="Offer & Negotiation",
                    description="Make offer and negotiate terms",
                    required_agents=["voss_negotiation", "adaptive_jorge"],
                    estimated_duration="1-2 weeks",
                    success_criteria=["Offer accepted", "Contract signed"],
                    exit_conditions=["Offer rejected", "Terms not acceptable"],
                    next_steps=["ftb_006"]
                ),
                JourneyStep(
                    step_id="ftb_006",
                    step_name="Transaction Management",
                    description="Manage closing process and documentation",
                    required_agents=["lead_bot", "claude_concierge"],
                    estimated_duration="3-6 weeks",
                    success_criteria=["Closing completed", "Keys transferred"],
                    exit_conditions=["Transaction falls through"],
                    next_steps=["ftb_007"]
                ),
                JourneyStep(
                    step_id="ftb_007",
                    step_name="Post-Purchase Support",
                    description="Provide ongoing support and relationship management",
                    required_agents=["claude_concierge", "predictive_lead"],
                    estimated_duration="Ongoing",
                    success_criteria=["Customer satisfaction", "Referral potential"],
                    exit_conditions=["Customer relationship ends"],
                    next_steps=[]
                )
            ],

            "investor": [
                JourneyStep(
                    step_id="inv_001",
                    step_name="Investment Strategy Consultation",
                    description="Define investment goals and strategy",
                    required_agents=["property_intelligence", "epsilon_predictive"],
                    estimated_duration="1-3 days",
                    success_criteria=["Strategy defined", "Criteria established"],
                    exit_conditions=["No clear investment thesis"],
                    next_steps=["inv_002"]
                ),
                JourneyStep(
                    step_id="inv_002",
                    step_name="Market Analysis",
                    description="Comprehensive market and opportunity analysis",
                    required_agents=["property_intelligence", "kappa_competitive", "quant_agent"],
                    estimated_duration="3-7 days",
                    success_criteria=["Market analysis complete", "Opportunities identified"],
                    exit_conditions=["Market not suitable"],
                    next_steps=["inv_003"]
                ),
                JourneyStep(
                    step_id="inv_003",
                    step_name="Property Sourcing",
                    description="Identify and source investment properties",
                    required_agents=["predictive_lead", "property_intelligence"],
                    estimated_duration="2-8 weeks",
                    success_criteria=["Properties sourced", "Analysis completed"],
                    exit_conditions=["No suitable properties"],
                    next_steps=["inv_004"]
                ),
                JourneyStep(
                    step_id="inv_004",
                    step_name="Due Diligence",
                    description="Comprehensive property and investment analysis",
                    required_agents=["property_intelligence", "quant_agent"],
                    estimated_duration="1-2 weeks",
                    success_criteria=["Due diligence complete", "Investment approved"],
                    exit_conditions=["Investment thesis not met"],
                    next_steps=["inv_005"]
                ),
                JourneyStep(
                    step_id="inv_005",
                    step_name="Acquisition",
                    description="Execute property acquisition",
                    required_agents=["voss_negotiation", "adaptive_jorge"],
                    estimated_duration="2-4 weeks",
                    success_criteria=["Property acquired", "Terms optimized"],
                    exit_conditions=["Unable to acquire on terms"],
                    next_steps=["inv_006"]
                ),
                JourneyStep(
                    step_id="inv_006",
                    step_name="Portfolio Management",
                    description="Ongoing investment performance monitoring",
                    required_agents=["iota_revenue", "property_intelligence"],
                    estimated_duration="Ongoing",
                    success_criteria=["Performance tracking", "Optimization opportunities"],
                    exit_conditions=["Investment disposed"],
                    next_steps=[]
                )
            ],

            "seller": [
                JourneyStep(
                    step_id="sel_001",
                    step_name="Seller Qualification",
                    description="Understand motivation and timeline",
                    required_agents=["adaptive_jorge", "realtime_intent"],
                    estimated_duration="1-3 days",
                    success_criteria=["Motivation confirmed", "Timeline established"],
                    exit_conditions=["Not serious about selling"],
                    next_steps=["sel_002"]
                ),
                JourneyStep(
                    step_id="sel_002",
                    step_name="Property Valuation",
                    description="Comprehensive market analysis and pricing",
                    required_agents=["property_intelligence", "cma_generator"],
                    estimated_duration="2-5 days",
                    success_criteria=["Valuation complete", "Pricing strategy set"],
                    exit_conditions=["Unrealistic price expectations"],
                    next_steps=["sel_003"]
                ),
                JourneyStep(
                    step_id="sel_003",
                    step_name="Listing Preparation",
                    description="Prepare property for market",
                    required_agents=["property_intelligence", "claude_concierge"],
                    estimated_duration="1-4 weeks",
                    success_criteria=["Property ready", "Marketing materials prepared"],
                    exit_conditions=["Property not marketable"],
                    next_steps=["sel_004"]
                ),
                JourneyStep(
                    step_id="sel_004",
                    step_name="Marketing & Showings",
                    description="Market property and manage showings",
                    required_agents=["predictive_lead", "claude_concierge"],
                    estimated_duration="2-12 weeks",
                    success_criteria=["Offers received", "Buyer interest"],
                    exit_conditions=["No market interest"],
                    next_steps=["sel_005"]
                ),
                JourneyStep(
                    step_id="sel_005",
                    step_name="Negotiation & Sale",
                    description="Negotiate and close sale",
                    required_agents=["voss_negotiation", "adaptive_jorge"],
                    estimated_duration="3-8 weeks",
                    success_criteria=["Sale completed", "Proceeds received"],
                    exit_conditions=["Sale falls through"],
                    next_steps=["sel_006"]
                ),
                JourneyStep(
                    step_id="sel_006",
                    step_name="Post-Sale Relationship",
                    description="Maintain relationship for future opportunities",
                    required_agents=["predictive_lead", "claude_concierge"],
                    estimated_duration="Ongoing",
                    success_criteria=["Relationship maintained", "Referral potential"],
                    exit_conditions=["Relationship ends"],
                    next_steps=[]
                )
            ]
        }

    def get_journey_template(self, customer_type: CustomerType) -> List[JourneyStep]:
        """Get journey template for customer type."""
        template_key = customer_type.value
        return self.journey_templates.get(template_key, self.journey_templates["first_time_buyer"])

    def customize_journey_template(self, template: List[JourneyStep], profile: CustomerProfile) -> List[JourneyStep]:
        """Customize journey template based on customer profile."""
        customized_template = []

        for step in template:
            customized_step = step

            # Adjust duration based on customer preferences
            if profile.response_speed_preference == "immediate":
                # Accelerate timeline for urgent customers
                if "weeks" in step.estimated_duration:
                    customized_step.estimated_duration = step.estimated_duration.replace("weeks", "days")

            # Adjust agents based on customer sophistication
            if profile.investment_experience == "advanced" and "adaptive_jorge" in step.required_agents:
                # Use more sophisticated agents for advanced customers
                customized_step.required_agents = [agent if agent != "adaptive_jorge"
                                                 else "property_intelligence" for agent in step.required_agents]

            customized_template.append(customized_step)

        return customized_template

class JourneyAnalyticsEngine:
    """Analyzes journey performance and optimization opportunities."""

    def __init__(self):
        self.journey_metrics = {
            "average_journey_time": {},
            "conversion_rates": {},
            "satisfaction_scores": {},
            "drop_off_points": {},
            "bottlenecks": {}
        }

    async def analyze_journey_performance(self, customer_id: str, journey_history: List[Dict]) -> Dict[str, Any]:
        """Analyze performance of customer journey."""

        # Calculate journey metrics
        total_duration = self._calculate_total_duration(journey_history)
        completion_rate = self._calculate_completion_rate(journey_history)
        satisfaction_score = self._calculate_satisfaction_score(journey_history)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(journey_history)

        # Optimization opportunities
        optimizations = await self._identify_optimizations(journey_history)

        return {
            "journey_performance": {
                "total_duration_days": total_duration,
                "completion_rate": completion_rate,
                "satisfaction_score": satisfaction_score,
                "bottlenecks": bottlenecks
            },
            "optimization_opportunities": optimizations,
            "performance_grade": self._calculate_performance_grade(completion_rate, satisfaction_score),
            "recommendations": await self._generate_recommendations(journey_history, optimizations)
        }

    def _calculate_total_duration(self, journey_history: List[Dict]) -> float:
        """Calculate total journey duration in days."""
        if not journey_history:
            return 0

        start_time = datetime.fromisoformat(journey_history[0]["timestamp"])
        end_time = datetime.fromisoformat(journey_history[-1]["timestamp"])
        return (end_time - start_time).days

    def _calculate_completion_rate(self, journey_history: List[Dict]) -> float:
        """Calculate journey completion rate."""
        if not journey_history:
            return 0

        completed_steps = len([step for step in journey_history if step.get("status") == "completed"])
        total_steps = len(journey_history)
        return (completed_steps / total_steps) * 100 if total_steps > 0 else 0

    def _calculate_satisfaction_score(self, journey_history: List[Dict]) -> float:
        """Calculate customer satisfaction score."""
        satisfaction_events = [step for step in journey_history if "satisfaction" in step]
        if not satisfaction_events:
            return 75  # Default moderate satisfaction

        scores = [event["satisfaction"] for event in satisfaction_events]
        return sum(scores) / len(scores)

    def _identify_bottlenecks(self, journey_history: List[Dict]) -> List[Dict]:
        """Identify bottlenecks in the journey."""
        bottlenecks = []

        for i, step in enumerate(journey_history[:-1]):
            current_time = datetime.fromisoformat(step["timestamp"])
            next_time = datetime.fromisoformat(journey_history[i + 1]["timestamp"])
            duration = (next_time - current_time).total_seconds() / 3600  # Hours

            if duration > 48:  # More than 48 hours
                bottlenecks.append({
                    "step": step["step_name"],
                    "duration_hours": duration,
                    "severity": "high" if duration > 168 else "medium"  # 1 week threshold
                })

        return bottlenecks

    async def _identify_optimizations(self, journey_history: List[Dict]) -> List[JourneyOptimization]:
        """Identify optimization opportunities."""
        optimizations = []

        # Agent efficiency optimization
        agent_performance = {}
        for step in journey_history:
            agents = step.get("agents_used", [])
            for agent in agents:
                if agent not in agent_performance:
                    agent_performance[agent] = {"total_time": 0, "count": 0}
                agent_performance[agent]["total_time"] += step.get("duration", 0)
                agent_performance[agent]["count"] += 1

        # Identify slow agents
        for agent, metrics in agent_performance.items():
            avg_time = metrics["total_time"] / metrics["count"] if metrics["count"] > 0 else 0
            if avg_time > 120:  # More than 2 hours average
                optimizations.append(JourneyOptimization(
                    optimization_type="agent_performance",
                    current_performance=avg_time,
                    target_performance=60,  # 1 hour target
                    recommended_changes=[f"Optimize {agent} response time", "Consider alternative agents"],
                    expected_impact="Reduce journey time by 25-40%",
                    implementation_complexity="medium"
                ))

        return optimizations

    def _calculate_performance_grade(self, completion_rate: float, satisfaction_score: float) -> str:
        """Calculate overall performance grade."""
        overall_score = (completion_rate * 0.6 + satisfaction_score * 0.4)

        if overall_score >= 90:
            return "A"
        elif overall_score >= 80:
            return "B"
        elif overall_score >= 70:
            return "C"
        elif overall_score >= 60:
            return "D"
        else:
            return "F"

    async def _generate_recommendations(self, journey_history: List[Dict], optimizations: List[JourneyOptimization]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if optimizations:
            recommendations.append("Implement identified optimization opportunities")

        # Check for common improvement areas
        if len(journey_history) > 10:
            recommendations.append("Consider journey simplification - too many steps")

        if self._calculate_satisfaction_score(journey_history) < 70:
            recommendations.append("Focus on customer satisfaction improvements")

        return recommendations

class CustomerJourneyOrchestrator:
    """
    Customer Journey Orchestrator - End-to-End Experience Coordination

    Orchestrates the complete customer journey across all specialized agents,
    ensuring seamless handoffs, optimal experience flow, and intelligent
    agent coordination based on customer context and preferences.
    """

    def __init__(self):
        self.claude_assistant = ClaudeAssistant()
        self.event_publisher = get_event_publisher()

        # Initialize sub-components
        self.template_engine = JourneyTemplateEngine()
        self.analytics_engine = JourneyAnalyticsEngine()

        # Access other orchestrators
        self.concierge = get_claude_concierge()
        self.bot_orchestrator = get_enhanced_bot_orchestrator()
        self.property_intelligence = get_property_intelligence_agent()

        # State management
        self.active_journeys: Dict[str, Dict] = {}
        self.customer_profiles: Dict[str, CustomerProfile] = {}

    async def start_customer_journey(self,
                                   customer_id: str,
                                   customer_type: CustomerType,
                                   initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate a new customer journey."""

        logger.info(f"Starting customer journey for {customer_id} as {customer_type.value}")

        # Create customer profile
        profile = CustomerProfile(
            customer_id=customer_id,
            customer_type=customer_type,
            journey_stage=JourneyStage.DISCOVERY,
            priority_level=initial_context.get("priority", JourneyPriority.MEDIUM),
            communication_preference=initial_context.get("communication_preference", "sms"),
            response_speed_preference=initial_context.get("response_speed", "same_day"),
            information_depth_preference=initial_context.get("info_depth", "moderate"),
            decision_making_style=initial_context.get("decision_style", "analytical")
        )

        # Get and customize journey template
        template = self.template_engine.get_journey_template(customer_type)
        customized_journey = self.template_engine.customize_journey_template(template, profile)

        # Initialize journey state
        journey_state = {
            "customer_profile": profile,
            "journey_template": customized_journey,
            "current_step": 0,
            "active_agents": [],
            "journey_history": [],
            "start_time": datetime.now(),
            "estimated_completion": datetime.now() + timedelta(days=30)  # Default estimate
        }

        # Store journey state
        self.active_journeys[customer_id] = journey_state
        self.customer_profiles[customer_id] = profile

        # Start first journey step
        first_step_result = await self._execute_journey_step(customer_id, 0, initial_context)

        # Publish journey start event
        await self.event_publisher.publish_journey_started(
            customer_id=customer_id,
            customer_type=customer_type.value,
            journey_template=len(customized_journey),
            estimated_duration=30
        )

        return {
            "journey_id": customer_id,
            "customer_profile": profile,
            "journey_overview": {
                "total_steps": len(customized_journey),
                "current_step": 1,
                "estimated_completion": journey_state["estimated_completion"].isoformat()
            },
            "first_step_result": first_step_result,
            "next_actions": customized_journey[0].success_criteria
        }

    async def advance_customer_journey(self,
                                     customer_id: str,
                                     completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Advance customer to next journey step."""

        if customer_id not in self.active_journeys:
            raise ValueError(f"No active journey found for customer {customer_id}")

        journey_state = self.active_journeys[customer_id]
        current_step_index = journey_state["current_step"]
        journey_template = journey_state["journey_template"]

        # Validate step completion
        current_step = journey_template[current_step_index]
        completion_valid = await self._validate_step_completion(current_step, completion_data)

        if not completion_valid:
            return {
                "advancement_status": "blocked",
                "reason": "Step completion criteria not met",
                "required_actions": current_step.success_criteria
            }

        # Record step completion
        journey_state["journey_history"].append({
            "step_id": current_step.step_id,
            "step_name": current_step.step_name,
            "completion_time": datetime.now(),
            "agents_used": journey_state.get("active_agents", []),
            "status": "completed",
            "completion_data": completion_data
        })

        # Advance to next step
        next_step_index = current_step_index + 1
        if next_step_index >= len(journey_template):
            # Journey completed
            return await self._complete_customer_journey(customer_id)

        journey_state["current_step"] = next_step_index

        # Execute next step
        next_step_result = await self._execute_journey_step(customer_id, next_step_index, completion_data)

        # Update journey stage
        await self._update_journey_stage(customer_id, next_step_index)

        # Publish advancement event
        await self.event_publisher.publish_journey_advanced(
            customer_id=customer_id,
            from_step=current_step.step_name,
            to_step=journey_template[next_step_index].step_name,
            completion_data=completion_data
        )

        return {
            "advancement_status": "advanced",
            "previous_step": current_step.step_name,
            "current_step": journey_template[next_step_index].step_name,
            "progress": (next_step_index + 1) / len(journey_template) * 100,
            "next_step_result": next_step_result
        }

    async def _execute_journey_step(self,
                                  customer_id: str,
                                  step_index: int,
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific journey step."""

        journey_state = self.active_journeys[customer_id]
        customer_profile = journey_state["customer_profile"]
        step = journey_state["journey_template"][step_index]

        logger.info(f"Executing step {step.step_name} for customer {customer_id}")

        # Determine required agent handoffs
        handoffs = await self._plan_agent_handoffs(step, customer_profile, context)

        # Execute agent coordination
        results = []
        for handoff in handoffs:
            handoff_result = await self._execute_agent_handoff(handoff, context)
            results.append(handoff_result)

        # Update active agents
        journey_state["active_agents"] = step.required_agents

        # Generate step summary
        step_summary = await self._generate_step_summary(step, results, customer_profile)

        return {
            "step_name": step.step_name,
            "agents_coordinated": step.required_agents,
            "handoffs_executed": len(handoffs),
            "results": results,
            "step_summary": step_summary,
            "estimated_duration": step.estimated_duration,
            "success_criteria": step.success_criteria
        }

    async def _plan_agent_handoffs(self,
                                 step: JourneyStep,
                                 profile: CustomerProfile,
                                 context: Dict[str, Any]) -> List[AgentHandoff]:
        """Plan agent handoffs for journey step."""

        handoffs = []

        # Create handoffs for each required agent
        for i, agent in enumerate(step.required_agents):
            if i == 0:
                # First agent - direct assignment
                handoff_type = AgentHandoffType.SEQUENTIAL
                from_agent = "journey_orchestrator"
            else:
                # Subsequent agents - handoff from previous
                handoff_type = AgentHandoffType.COLLABORATIVE
                from_agent = step.required_agents[i - 1]

            handoffs.append(AgentHandoff(
                from_agent=from_agent,
                to_agent=agent,
                handoff_type=handoff_type,
                context_data={
                    "customer_profile": profile,
                    "journey_step": step.step_name,
                    "step_context": context
                },
                handoff_reason=f"Journey step: {step.step_name}",
                priority=profile.priority_level
            ))

        return handoffs

    async def _execute_agent_handoff(self, handoff: AgentHandoff, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific agent handoff."""

        logger.info(f"Executing handoff from {handoff.from_agent} to {handoff.to_agent}")

        # Route to appropriate agent based on to_agent
        if handoff.to_agent == "claude_concierge":
            result = await self.concierge.process_user_interaction(
                user_id=handoff.context_data["customer_profile"].customer_id,
                message=f"Journey step: {handoff.context_data['journey_step']}",
                context=context
            )
        elif handoff.to_agent in ["adaptive_jorge", "predictive_lead", "realtime_intent"]:
            result = await self.bot_orchestrator.orchestrate_conversation(
                lead_id=handoff.context_data["customer_profile"].customer_id,
                lead_name=handoff.context_data["customer_profile"].customer_id,
                message=f"Journey step execution",
                conversation_type="seller" if "jorge" in handoff.to_agent else "lead_sequence"
            )
        elif handoff.to_agent == "property_intelligence":
            # Mock property intelligence call
            result = {
                "agent_response": f"Property intelligence analysis for {handoff.context_data['journey_step']}",
                "analysis_type": "journey_step"
            }
        else:
            # Generic agent response
            result = {
                "agent_response": f"{handoff.to_agent} executed for journey step",
                "handoff_type": handoff.handoff_type.value
            }

        return {
            "handoff_id": f"{handoff.from_agent}_to_{handoff.to_agent}",
            "agent_result": result,
            "execution_time": datetime.now(),
            "success": True
        }

    async def _validate_step_completion(self, step: JourneyStep, completion_data: Dict[str, Any]) -> bool:
        """Validate that step completion criteria are met."""

        # Check if all success criteria are addressed
        for criteria in step.success_criteria:
            criteria_key = criteria.lower().replace(" ", "_")
            if criteria_key not in completion_data:
                return False

        return True

    async def _update_journey_stage(self, customer_id: str, step_index: int):
        """Update customer journey stage based on progress."""

        journey_state = self.active_journeys[customer_id]
        total_steps = len(journey_state["journey_template"])
        progress = step_index / total_steps

        # Map progress to journey stages
        if progress < 0.2:
            new_stage = JourneyStage.DISCOVERY
        elif progress < 0.4:
            new_stage = JourneyStage.EXPLORATION
        elif progress < 0.6:
            new_stage = JourneyStage.EVALUATION
        elif progress < 0.8:
            new_stage = JourneyStage.NEGOTIATION
        elif progress < 0.95:
            new_stage = JourneyStage.TRANSACTION
        else:
            new_stage = JourneyStage.OWNERSHIP

        # Update customer profile
        customer_profile = self.customer_profiles[customer_id]
        customer_profile.journey_stage = new_stage

    async def _complete_customer_journey(self, customer_id: str) -> Dict[str, Any]:
        """Complete customer journey and generate analytics."""

        journey_state = self.active_journeys[customer_id]
        journey_history = journey_state["journey_history"]

        # Analyze journey performance
        performance_analysis = await self.analytics_engine.analyze_journey_performance(
            customer_id, journey_history
        )

        # Generate completion report
        completion_report = await self._generate_completion_report(customer_id, performance_analysis)

        # Archive journey
        archived_journey = self.active_journeys.pop(customer_id)

        # Publish completion event
        await self.event_publisher.publish_journey_completed(
            customer_id=customer_id,
            total_duration=(datetime.now() - archived_journey["start_time"]).days,
            performance_grade=performance_analysis["performance_grade"],
            satisfaction_score=performance_analysis["journey_performance"]["satisfaction_score"]
        )

        return {
            "completion_status": "journey_completed",
            "customer_id": customer_id,
            "completion_report": completion_report,
            "performance_analysis": performance_analysis,
            "final_satisfaction": performance_analysis["journey_performance"]["satisfaction_score"]
        }

    async def _generate_step_summary(self,
                                   step: JourneyStep,
                                   results: List[Dict],
                                   profile: CustomerProfile) -> str:
        """Generate summary of step execution."""

        summary_prompt = f"""
        Generate a brief summary of the journey step execution:

        Step: {step.step_name}
        Description: {step.description}
        Customer Type: {profile.customer_type.value}
        Agents Used: {', '.join(step.required_agents)}

        Results: {len(results)} agent interactions completed

        Create a 1-2 sentence summary of what was accomplished.
        """

        response = await self.claude_assistant.analyze_with_context(summary_prompt)
        return response.get("content", f"Completed {step.step_name} with {len(results)} agent interactions.")

    async def _generate_completion_report(self, customer_id: str, performance_analysis: Dict) -> str:
        """Generate comprehensive journey completion report."""

        journey_state = self.active_journeys.get(customer_id, {})
        customer_profile = self.customer_profiles.get(customer_id)

        report_prompt = f"""
        Generate a completion report for customer journey:

        Customer Type: {customer_profile.customer_type.value if customer_profile else 'Unknown'}
        Journey Duration: {performance_analysis['journey_performance']['total_duration_days']} days
        Completion Rate: {performance_analysis['journey_performance']['completion_rate']}%
        Satisfaction Score: {performance_analysis['journey_performance']['satisfaction_score']}/100
        Performance Grade: {performance_analysis['performance_grade']}

        Create a 2-3 sentence executive summary of the journey outcome.
        """

        response = await self.claude_assistant.analyze_with_context(report_prompt)
        return response.get("content", "Customer journey completed successfully with comprehensive agent coordination.")

    async def get_journey_status(self, customer_id: str) -> Dict[str, Any]:
        """Get current journey status for customer."""

        if customer_id not in self.active_journeys:
            return {"status": "no_active_journey"}

        journey_state = self.active_journeys[customer_id]
        customer_profile = self.customer_profiles[customer_id]

        current_step_index = journey_state["current_step"]
        total_steps = len(journey_state["journey_template"])
        current_step = journey_state["journey_template"][current_step_index]

        return {
            "customer_id": customer_id,
            "journey_status": "active",
            "customer_type": customer_profile.customer_type.value,
            "journey_stage": customer_profile.journey_stage.value,
            "current_step": {
                "step_name": current_step.step_name,
                "description": current_step.description,
                "progress": (current_step_index + 1) / total_steps * 100
            },
            "active_agents": journey_state["active_agents"],
            "journey_start": journey_state["start_time"].isoformat(),
            "estimated_completion": journey_state["estimated_completion"].isoformat()
        }

# --- Factory Functions ---

_orchestrator_instance: Optional[CustomerJourneyOrchestrator] = None

def get_customer_journey_orchestrator() -> CustomerJourneyOrchestrator:
    """Get singleton Customer Journey Orchestrator instance."""
    global _orchestrator_instance

    if _orchestrator_instance is None:
        _orchestrator_instance = CustomerJourneyOrchestrator()

    return _orchestrator_instance

# --- Event Publisher Extensions ---

async def publish_journey_started(event_publisher, **kwargs):
    """Publish journey started event."""
    await event_publisher.publish_event(
        event_type="journey_started",
        data={**kwargs, "timestamp": datetime.now().isoformat()}
    )

async def publish_journey_advanced(event_publisher, **kwargs):
    """Publish journey advanced event."""
    await event_publisher.publish_event(
        event_type="journey_advanced",
        data={**kwargs, "timestamp": datetime.now().isoformat()}
    )

async def publish_journey_completed(event_publisher, **kwargs):
    """Publish journey completed event."""
    await event_publisher.publish_event(
        event_type="journey_completed",
        data={**kwargs, "timestamp": datetime.now().isoformat()}
    )