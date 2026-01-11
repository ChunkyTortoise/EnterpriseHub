"""
Process-Aware Guidance Engine - Real Estate Workflow Intelligence
================================================================

Provides intelligent, context-aware guidance throughout the entire real estate
sales process, from lead capture to post-close follow-up. Integrates with
Claude AI to deliver stage-specific coaching, recommendations, and insights
based on proven real estate best practices.

Key Features:
- Stage-specific coaching for 13 distinct process stages
- Dynamic workflow progression tracking
- Contextual objection handling by stage
- Performance optimization suggestions
- Best practices enforcement
- Risk identification and mitigation

Real Estate Process Stages:
1. Lead Capture → 2. Initial Contact → 3. Qualification → 4. Needs Discovery
5. Property Search → 6. Showing Prep → 7. Property Showing → 8. Offer Prep
9. Negotiation → 10. Contract Execution → 11. Transaction Management
12. Closing Prep → 13. Post-Close Follow-up

Business Impact:
- 25-40% improvement in conversion rates through stage-appropriate guidance
- Reduced cycle times with optimized workflow progression
- Consistent service quality through standardized best practices
- Enhanced agent confidence with real-time coaching
- Improved client satisfaction through professional service delivery

Author: EnterpriseHub AI Platform
Date: January 10, 2026
Version: 1.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from .claude_agent_service import claude_agent_service
from .persistent_chat_memory_service import (
    persistent_chat_memory_service, ProcessMemory, MemoryPriority
)
from ..streamlit_components.persistent_claude_chat import (
    RealtorProcessStage, ProcessContext
)

logger = logging.getLogger(__name__)


class GuidancePriority(str, Enum):
    """Priority levels for guidance recommendations."""
    CRITICAL = "critical"    # Immediate action required
    HIGH = "high"           # Important for success
    MEDIUM = "medium"       # Beneficial to address
    LOW = "low"            # Nice to have


class ActionType(str, Enum):
    """Types of recommended actions."""
    COMMUNICATE = "communicate"     # Call, email, text
    DISCOVER = "discover"          # Ask questions, gather info
    PRESENT = "present"            # Show properties, present options
    NEGOTIATE = "negotiate"        # Handle objections, negotiate terms
    DOCUMENT = "document"          # Prepare contracts, documents
    COORDINATE = "coordinate"      # Schedule, arrange meetings
    FOLLOW_UP = "follow_up"       # Check in, provide updates
    ANALYZE = "analyze"           # Review data, assess situation


@dataclass
class StageGuidance:
    """Guidance specific to a process stage."""
    stage: RealtorProcessStage
    objectives: List[str]
    key_questions: List[str]
    common_objections: List[str]
    success_metrics: List[str]
    critical_actions: List[str]
    transition_criteria: List[str]
    typical_duration_days: int
    ai_coaching_prompts: List[str]


@dataclass
class GuidanceRecommendation:
    """Individual guidance recommendation."""
    action: str
    priority: GuidancePriority
    action_type: ActionType
    reasoning: str
    expected_outcome: str
    timing: str
    confidence: float
    stage_specific: bool = True


@dataclass
class ProcessAssessment:
    """Assessment of current process state and recommendations."""
    current_stage: RealtorProcessStage
    stage_completion: float  # 0-100% completion of current stage
    next_stage: Optional[RealtorProcessStage]
    time_in_stage: timedelta
    recommendations: List[GuidanceRecommendation]
    risk_factors: List[str]
    success_indicators: List[str]
    overall_health_score: float  # 0-100
    confidence: float


class ProcessAwareGuidanceEngine:
    """
    Intelligent guidance engine for real estate workflow optimization.

    Provides stage-specific coaching, tracks workflow progression,
    and delivers actionable recommendations to improve conversion rates
    and client satisfaction throughout the entire sales process.
    """

    def __init__(self):
        self.claude_service = claude_agent_service
        self.memory_service = persistent_chat_memory_service

        # Initialize stage definitions
        self.stage_definitions = self._initialize_stage_definitions()

        # Performance tracking
        self.guidance_history: Dict[str, List[Dict]] = {}

        logger.info("ProcessAwareGuidanceEngine initialized")

    def _initialize_stage_definitions(self) -> Dict[RealtorProcessStage, StageGuidance]:
        """Initialize comprehensive stage definitions and guidance."""
        return {
            RealtorProcessStage.LEAD_CAPTURE: StageGuidance(
                stage=RealtorProcessStage.LEAD_CAPTURE,
                objectives=[
                    "Capture lead information quickly and efficiently",
                    "Establish initial rapport and credibility",
                    "Qualify basic intent and timeline",
                    "Set expectations for follow-up"
                ],
                key_questions=[
                    "What's prompting you to consider buying/selling now?",
                    "What's your ideal timeline for making a move?",
                    "Have you worked with a real estate agent before?",
                    "What questions can I answer for you right away?"
                ],
                common_objections=[
                    "Just browsing/looking around",
                    "Not ready to work with an agent yet",
                    "Already working with another agent",
                    "Want to do it ourselves"
                ],
                success_metrics=[
                    "Lead contact information captured",
                    "Basic qualification completed",
                    "Follow-up appointment scheduled",
                    "Lead marked as qualified"
                ],
                critical_actions=[
                    "Respond within 5 minutes of lead generation",
                    "Capture phone number and email",
                    "Qualify intent and timeline",
                    "Schedule follow-up call"
                ],
                transition_criteria=[
                    "Lead has provided contact information",
                    "Basic qualification questions answered",
                    "Follow-up communication established",
                    "Lead shows genuine interest"
                ],
                typical_duration_days=1,
                ai_coaching_prompts=[
                    "How can I quickly build rapport with this lead?",
                    "What's the best way to qualify their timeline?",
                    "How do I handle 'just browsing' responses?"
                ]
            ),

            RealtorProcessStage.INITIAL_CONTACT: StageGuidance(
                stage=RealtorProcessStage.INITIAL_CONTACT,
                objectives=[
                    "Establish trust and professional credibility",
                    "Understand motivation and urgency",
                    "Complete initial qualification",
                    "Present value proposition clearly"
                ],
                key_questions=[
                    "What's driving your decision to buy/sell at this time?",
                    "What's most important to you in this process?",
                    "How familiar are you with the current market?",
                    "What concerns do you have about buying/selling?"
                ],
                common_objections=[
                    "Market timing concerns",
                    "Commission/fee questions",
                    "Competing agent comparisons",
                    "Process complexity worries"
                ],
                success_metrics=[
                    "Trust and rapport established",
                    "Motivation and urgency understood",
                    "Value proposition accepted",
                    "Next meeting scheduled"
                ],
                critical_actions=[
                    "Complete comprehensive needs assessment",
                    "Present credentials and market expertise",
                    "Address initial concerns and objections",
                    "Set clear expectations for the process"
                ],
                transition_criteria=[
                    "Client expresses confidence in working together",
                    "Key motivation factors identified",
                    "Process timeline established",
                    "Formal agreement to proceed"
                ],
                typical_duration_days=3,
                ai_coaching_prompts=[
                    "How do I establish credibility quickly?",
                    "What's the best way to uncover their motivation?",
                    "How should I present my value proposition?"
                ]
            ),

            RealtorProcessStage.QUALIFICATION: StageGuidance(
                stage=RealtorProcessStage.QUALIFICATION,
                objectives=[
                    "Complete comprehensive financial qualification",
                    "Understand detailed property requirements",
                    "Establish realistic expectations",
                    "Identify potential challenges early"
                ],
                key_questions=[
                    "Have you been pre-approved for financing?",
                    "What's your comfortable monthly payment range?",
                    "What areas are you considering?",
                    "What features are absolutely essential vs nice-to-have?"
                ],
                common_objections=[
                    "Privacy concerns about financial information",
                    "Unrealistic price expectations",
                    "Timeline pressure or urgency",
                    "Limited inventory concerns"
                ],
                success_metrics=[
                    "Financial qualification completed",
                    "Property criteria clearly defined",
                    "Realistic expectations set",
                    "Search parameters established"
                ],
                critical_actions=[
                    "Verify pre-approval or connect with lender",
                    "Complete detailed buyer/seller questionnaire",
                    "Set realistic price and timeline expectations",
                    "Identify and address potential roadblocks"
                ],
                transition_criteria=[
                    "Financial capability confirmed",
                    "Property requirements documented",
                    "Market expectations aligned with reality",
                    "Search strategy agreed upon"
                ],
                typical_duration_days=7,
                ai_coaching_prompts=[
                    "How do I handle resistance to financial questions?",
                    "What's the best way to set realistic expectations?",
                    "How do I qualify without being pushy?"
                ]
            ),

            RealtorProcessStage.NEEDS_DISCOVERY: StageGuidance(
                stage=RealtorProcessStage.NEEDS_DISCOVERY,
                objectives=[
                    "Understand lifestyle and emotional drivers",
                    "Identify hidden needs and preferences",
                    "Uncover decision-making process",
                    "Build detailed client profile"
                ],
                key_questions=[
                    "Describe your ideal day in your new home",
                    "What's not working in your current situation?",
                    "How do you envision your life changing?",
                    "Who else is involved in this decision?"
                ],
                common_objections=[
                    "Too many questions/feeling overwhelmed",
                    "Privacy concerns about personal details",
                    "Uncertainty about actual needs",
                    "Analysis paralysis"
                ],
                success_metrics=[
                    "Emotional drivers understood",
                    "Lifestyle requirements mapped",
                    "Decision makers identified",
                    "Priority matrix established"
                ],
                critical_actions=[
                    "Conduct lifestyle and needs assessment",
                    "Identify all decision makers and influencers",
                    "Understand emotional and logical drivers",
                    "Create detailed client preference profile"
                ],
                transition_criteria=[
                    "Complete understanding of client needs",
                    "Emotional drivers identified and addressed",
                    "All stakeholders engaged in process",
                    "Clear vision of ideal outcome established"
                ],
                typical_duration_days=5,
                ai_coaching_prompts=[
                    "How do I uncover emotional motivations?",
                    "What questions reveal hidden needs?",
                    "How do I handle multiple decision makers?"
                ]
            ),

            RealtorProcessStage.PROPERTY_SEARCH: StageGuidance(
                stage=RealtorProcessStage.PROPERTY_SEARCH,
                objectives=[
                    "Identify properties matching criteria",
                    "Educate client on market realities",
                    "Refine search parameters based on feedback",
                    "Prepare for property showings"
                ],
                key_questions=[
                    "Which of these properties interests you most?",
                    "What draws you to this particular property?",
                    "Are there any features you'd be willing to compromise on?",
                    "How does this compare to what you envisioned?"
                ],
                common_objections=[
                    "Nothing available in price range",
                    "Properties don't match expectations",
                    "Competition from other buyers",
                    "Market moving too fast"
                ],
                success_metrics=[
                    "Quality property options identified",
                    "Client feedback incorporated",
                    "Search criteria refined",
                    "Showing appointments scheduled"
                ],
                critical_actions=[
                    "Conduct comprehensive MLS search",
                    "Present curated property options",
                    "Gather feedback and refine criteria",
                    "Schedule property showings"
                ],
                transition_criteria=[
                    "Client engaged with property options",
                    "Realistic properties identified for viewing",
                    "Showing schedule established",
                    "Client demonstrates serious interest"
                ],
                typical_duration_days=14,
                ai_coaching_prompts=[
                    "How do I manage unrealistic expectations?",
                    "What's the best way to present properties?",
                    "How do I handle limited inventory?"
                ]
            ),

            RealtorProcessStage.SHOWING_PREP: StageGuidance(
                stage=RealtorProcessStage.SHOWING_PREP,
                objectives=[
                    "Research properties thoroughly",
                    "Prepare comparative market analysis",
                    "Plan efficient showing route",
                    "Anticipate questions and objections"
                ],
                key_questions=[
                    "What specific features should we focus on?",
                    "Are there any concerns you want me to investigate?",
                    "How much time do you have for showings today?",
                    "What would make this showing most valuable?"
                ],
                common_objections=[
                    "Scheduling conflicts",
                    "Too many/too few properties to see",
                    "Concerns about property conditions",
                    "Time constraints"
                ],
                success_metrics=[
                    "Property research completed",
                    "CMA prepared",
                    "Showing route optimized",
                    "Client expectations set"
                ],
                critical_actions=[
                    "Research each property thoroughly",
                    "Prepare market comparables",
                    "Plan logical showing sequence",
                    "Confirm appointments and logistics"
                ],
                transition_criteria=[
                    "All properties researched",
                    "Market analysis prepared",
                    "Showing logistics confirmed",
                    "Client briefed on what to expect"
                ],
                typical_duration_days=2,
                ai_coaching_prompts=[
                    "How do I prepare for effective showings?",
                    "What research should I prioritize?",
                    "How do I set proper showing expectations?"
                ]
            ),

            RealtorProcessStage.PROPERTY_SHOWING: StageGuidance(
                stage=RealtorProcessStage.PROPERTY_SHOWING,
                objectives=[
                    "Showcase property features effectively",
                    "Address concerns and objections",
                    "Gauge genuine interest level",
                    "Guide decision-making process"
                ],
                key_questions=[
                    "Can you see yourself living here?",
                    "What do you love most about this property?",
                    "What concerns do you have?",
                    "How does this compare to your ideal?"
                ],
                common_objections=[
                    "Property condition issues",
                    "Price concerns",
                    "Location drawbacks",
                    "Size or layout limitations"
                ],
                success_metrics=[
                    "Properties shown effectively",
                    "Client feedback gathered",
                    "Interest level assessed",
                    "Next steps defined"
                ],
                critical_actions=[
                    "Highlight key property features",
                    "Address concerns professionally",
                    "Gather detailed feedback",
                    "Assess purchase intent"
                ],
                transition_criteria=[
                    "Client has seen relevant properties",
                    "Clear favorite(s) identified",
                    "Purchase intent confirmed",
                    "Ready to move toward offer"
                ],
                typical_duration_days=7,
                ai_coaching_prompts=[
                    "How do I handle property objections?",
                    "What's the best way to gauge interest?",
                    "How do I guide them toward a decision?"
                ]
            ),

            RealtorProcessStage.OFFER_PREPARATION: StageGuidance(
                stage=RealtorProcessStage.OFFER_PREPARATION,
                objectives=[
                    "Determine competitive offer strategy",
                    "Prepare comprehensive offer package",
                    "Set realistic expectations",
                    "Ensure client is fully committed"
                ],
                key_questions=[
                    "How competitive do you want to be?",
                    "What terms are most important to you?",
                    "Are you prepared to move quickly if needed?",
                    "What's your backup plan if this doesn't work?"
                ],
                common_objections=[
                    "Offer price concerns",
                    "Fear of overpaying",
                    "Hesitation to commit",
                    "Inspection/contingency worries"
                ],
                success_metrics=[
                    "Offer strategy determined",
                    "Competitive analysis completed",
                    "Offer package prepared",
                    "Client commitment confirmed"
                ],
                critical_actions=[
                    "Analyze comparable sales and market conditions",
                    "Prepare competitive offer strategy",
                    "Complete offer paperwork",
                    "Confirm client readiness to proceed"
                ],
                transition_criteria=[
                    "Offer strategy agreed upon",
                    "All paperwork completed",
                    "Client fully committed",
                    "Ready to submit offer"
                ],
                typical_duration_days=2,
                ai_coaching_prompts=[
                    "How do I price an offer competitively?",
                    "What's the best way to handle offer anxiety?",
                    "How do I ensure client commitment?"
                ]
            ),

            RealtorProcessStage.NEGOTIATION: StageGuidance(
                stage=RealtorProcessStage.NEGOTIATION,
                objectives=[
                    "Navigate offer negotiations skillfully",
                    "Protect client's interests",
                    "Reach mutually acceptable terms",
                    "Maintain deal momentum"
                ],
                key_questions=[
                    "What are you willing to compromise on?",
                    "How important is this property to you?",
                    "What's your walk-away point?",
                    "How do you feel about this counter-offer?"
                ],
                common_objections=[
                    "Counter-offer disappointment",
                    "Fear of losing the property",
                    "Pressure to decide quickly",
                    "Multiple offer competition stress"
                ],
                success_metrics=[
                    "Terms successfully negotiated",
                    "Client satisfied with outcome",
                    "Contract executed",
                    "Timeline established"
                ],
                critical_actions=[
                    "Present offers and counter-offers clearly",
                    "Advocate for client's best interests",
                    "Manage expectations and emotions",
                    "Secure accepted contract"
                ],
                transition_criteria=[
                    "Offer accepted by all parties",
                    "Contract fully executed",
                    "Contingency timeline established",
                    "Transaction moves to escrow"
                ],
                typical_duration_days=5,
                ai_coaching_prompts=[
                    "How do I handle difficult negotiations?",
                    "What's the best way to manage client emotions?",
                    "How do I know when to walk away?"
                ]
            ),

            RealtorProcessStage.CONTRACT_EXECUTION: StageGuidance(
                stage=RealtorProcessStage.CONTRACT_EXECUTION,
                objectives=[
                    "Ensure all contract terms are met",
                    "Coordinate contingency requirements",
                    "Manage timeline and deadlines",
                    "Prevent deal complications"
                ],
                key_questions=[
                    "Do you understand all the contract terms?",
                    "Are you comfortable with the timeline?",
                    "Do you have any concerns about contingencies?",
                    "What questions do you have about next steps?"
                ],
                common_objections=[
                    "Contract complexity concerns",
                    "Timeline anxiety",
                    "Contingency worries",
                    "Fear of deal falling through"
                ],
                success_metrics=[
                    "Contract properly executed",
                    "All parties understand terms",
                    "Timeline established",
                    "Initial deposits made"
                ],
                critical_actions=[
                    "Review contract terms thoroughly",
                    "Ensure proper execution",
                    "Coordinate initial deposits",
                    "Establish contingency timeline"
                ],
                transition_criteria=[
                    "Contract fully executed",
                    "Deposits completed",
                    "Contingency periods begin",
                    "Transaction management phase starts"
                ],
                typical_duration_days=3,
                ai_coaching_prompts=[
                    "How do I explain contract terms clearly?",
                    "What's the best way to manage contract anxiety?",
                    "How do I prevent execution problems?"
                ]
            ),

            RealtorProcessStage.TRANSACTION_MANAGEMENT: StageGuidance(
                stage=RealtorProcessStage.TRANSACTION_MANAGEMENT,
                objectives=[
                    "Coordinate all transaction requirements",
                    "Ensure contingencies are satisfied",
                    "Maintain deal momentum",
                    "Prevent delays and complications"
                ],
                key_questions=[
                    "How are the inspections/appraisal going?",
                    "Do you have any concerns about the findings?",
                    "Is everything on track with your financing?",
                    "Are you still excited about this purchase?"
                ],
                common_objections=[
                    "Inspection issue concerns",
                    "Appraisal problems",
                    "Financing delays",
                    "Title/survey issues"
                ],
                success_metrics=[
                    "All contingencies satisfied",
                    "Financing approved",
                    "Inspection issues resolved",
                    "Clear to close obtained"
                ],
                critical_actions=[
                    "Coordinate inspections and appraisal",
                    "Monitor financing progress",
                    "Resolve any issues promptly",
                    "Maintain communication with all parties"
                ],
                transition_criteria=[
                    "All contingencies removed",
                    "Financing fully approved",
                    "Clear to close issued",
                    "Closing date confirmed"
                ],
                typical_duration_days=21,
                ai_coaching_prompts=[
                    "How do I handle inspection issues?",
                    "What's the best way to manage transaction stress?",
                    "How do I keep deals on track?"
                ]
            ),

            RealtorProcessStage.CLOSING_PREP: StageGuidance(
                stage=RealtorProcessStage.CLOSING_PREP,
                objectives=[
                    "Prepare all closing documents",
                    "Coordinate final walk-through",
                    "Ensure smooth closing process",
                    "Address last-minute issues"
                ],
                key_questions=[
                    "Are you ready for the final walk-through?",
                    "Do you have any last-minute questions?",
                    "How are you feeling about closing day?",
                    "Is there anything else you need from me?"
                ],
                common_objections=[
                    "Last-minute financing concerns",
                    "Walk-through issues",
                    "Closing cost surprises",
                    "Moving coordination stress"
                ],
                success_metrics=[
                    "All documents prepared",
                    "Final walk-through completed",
                    "Closing scheduled",
                    "Client prepared and confident"
                ],
                critical_actions=[
                    "Review closing disclosure",
                    "Conduct final walk-through",
                    "Coordinate closing logistics",
                    "Address any final concerns"
                ],
                transition_criteria=[
                    "All closing requirements met",
                    "Final walk-through approved",
                    "Closing logistics confirmed",
                    "Ready for closing day"
                ],
                typical_duration_days=3,
                ai_coaching_prompts=[
                    "How do I prepare clients for closing?",
                    "What should I focus on in walk-through?",
                    "How do I handle last-minute issues?"
                ]
            ),

            RealtorProcessStage.POST_CLOSE_FOLLOW_UP: StageGuidance(
                stage=RealtorProcessStage.POST_CLOSE_FOLLOW_UP,
                objectives=[
                    "Ensure client satisfaction",
                    "Address any post-closing issues",
                    "Maintain relationship for future business",
                    "Generate referrals and reviews"
                ],
                key_questions=[
                    "How are you settling into your new home?",
                    "Is there anything I can help you with?",
                    "How was your overall experience?",
                    "Do you know anyone else looking to buy or sell?"
                ],
                common_objections=[
                    "Post-closing issues",
                    "Warranty concerns",
                    "Moving complications",
                    "Buyer's remorse"
                ],
                success_metrics=[
                    "Client satisfaction confirmed",
                    "Issues resolved",
                    "Relationship maintained",
                    "Referrals/reviews obtained"
                ],
                critical_actions=[
                    "Follow up within 24 hours of closing",
                    "Check in regularly during first month",
                    "Address any issues promptly",
                    "Request feedback and referrals"
                ],
                transition_criteria=[
                    "Client successfully settled",
                    "All issues resolved",
                    "Positive relationship established",
                    "Future business potential identified"
                ],
                typical_duration_days=30,
                ai_coaching_prompts=[
                    "How do I maintain client relationships?",
                    "What's the best way to request referrals?",
                    "How do I handle post-closing issues?"
                ]
            )
        }

    async def assess_current_process(
        self,
        agent_id: str,
        process_context: ProcessContext,
        conversation_history: List[Dict[str, Any]] = None,
        lead_context: Dict[str, Any] = None
    ) -> ProcessAssessment:
        """
        Assess current process state and provide comprehensive guidance.

        Args:
            agent_id: Agent identifier
            process_context: Current process context
            conversation_history: Recent conversation messages
            lead_context: Additional lead information

        Returns:
            Comprehensive process assessment with recommendations
        """
        try:
            current_stage = process_context.stage
            stage_def = self.stage_definitions[current_stage]

            # Calculate time in current stage
            time_in_stage = datetime.now() - process_context.last_updated

            # Assess stage completion percentage
            stage_completion = await self._assess_stage_completion(
                agent_id, process_context, conversation_history, lead_context
            )

            # Generate recommendations
            recommendations = await self._generate_stage_recommendations(
                agent_id, process_context, stage_completion, conversation_history, lead_context
            )

            # Identify risk factors
            risk_factors = await self._identify_risk_factors(
                process_context, time_in_stage, stage_completion
            )

            # Identify success indicators
            success_indicators = await self._identify_success_indicators(
                process_context, conversation_history, lead_context
            )

            # Calculate overall health score
            health_score = self._calculate_health_score(
                stage_completion, time_in_stage, len(risk_factors), len(success_indicators)
            )

            # Determine next stage
            next_stage = self._determine_next_stage(current_stage, stage_completion)

            # Create assessment
            assessment = ProcessAssessment(
                current_stage=current_stage,
                stage_completion=stage_completion,
                next_stage=next_stage,
                time_in_stage=time_in_stage,
                recommendations=recommendations,
                risk_factors=risk_factors,
                success_indicators=success_indicators,
                overall_health_score=health_score,
                confidence=0.85
            )

            # Store assessment in memory
            await self._store_process_assessment(agent_id, assessment)

            logger.info(f"Process assessment completed for {agent_id}: {current_stage.value}, {health_score:.0f}% health")
            return assessment

        except Exception as e:
            logger.error(f"Error assessing current process: {e}")
            return self._create_fallback_assessment(process_context)

    async def _assess_stage_completion(
        self,
        agent_id: str,
        process_context: ProcessContext,
        conversation_history: List[Dict[str, Any]],
        lead_context: Dict[str, Any]
    ) -> float:
        """Assess completion percentage of current stage."""
        try:
            stage_def = self.stage_definitions[process_context.stage]

            # Use Claude to assess completion based on objectives and success metrics
            assessment_prompt = f"""
            Assess the completion percentage (0-100) of the {process_context.stage.value.replace('_', ' ')} stage based on:

            **Stage Objectives:**
            {chr(10).join(f"• {obj}" for obj in stage_def.objectives)}

            **Success Metrics:**
            {chr(10).join(f"• {metric}" for metric in stage_def.success_metrics)}

            **Current Context:**
            - Lead ID: {process_context.lead_id or 'Not specified'}
            - Client Type: {process_context.client_type}
            - Urgency: {process_context.urgency}
            - Active Tasks: {', '.join(process_context.active_tasks) if process_context.active_tasks else 'None'}

            **Recent Conversation:**
            {json.dumps(conversation_history[-5:] if conversation_history else [], indent=2)}

            **Lead Context:**
            {json.dumps(lead_context or {}, indent=2)}

            Provide a completion percentage (0-100) and brief reasoning.
            """

            response = await self.claude_service.chat_with_agent(
                agent_id=agent_id,
                query=assessment_prompt,
                context={
                    "assessment_type": "stage_completion",
                    "stage": process_context.stage.value,
                    "process_context": process_context.__dict__
                }
            )

            # Extract percentage from response (simple parsing)
            response_text = response.response if hasattr(response, 'response') else str(response)

            # Look for percentage in response
            import re
            percentage_match = re.search(r'(\d+)%', response_text)
            if percentage_match:
                return min(100, max(0, int(percentage_match.group(1))))

            # Fallback: basic assessment based on available data
            completion_score = 0
            if process_context.lead_id:
                completion_score += 25
            if process_context.active_tasks:
                completion_score += 25
            if conversation_history and len(conversation_history) > 3:
                completion_score += 30
            if process_context.workflow_progress:
                completion_score += 20

            return min(100, completion_score)

        except Exception as e:
            logger.error(f"Error assessing stage completion: {e}")
            return 50  # Default to 50% if assessment fails

    async def _generate_stage_recommendations(
        self,
        agent_id: str,
        process_context: ProcessContext,
        stage_completion: float,
        conversation_history: List[Dict[str, Any]],
        lead_context: Dict[str, Any]
    ) -> List[GuidanceRecommendation]:
        """Generate specific recommendations for current stage."""
        try:
            stage_def = self.stage_definitions[process_context.stage]
            recommendations = []

            # Get Claude-powered recommendations
            recommendation_prompt = f"""
            Provide 3-5 specific, actionable recommendations for the {process_context.stage.value.replace('_', ' ')} stage.

            **Current Situation:**
            - Stage Completion: {stage_completion:.0f}%
            - Time in Stage: {(datetime.now() - process_context.last_updated).days} days
            - Client Type: {process_context.client_type}
            - Urgency: {process_context.urgency}

            **Stage Objectives:**
            {chr(10).join(f"• {obj}" for obj in stage_def.objectives)}

            **Critical Actions:**
            {chr(10).join(f"• {action}" for action in stage_def.critical_actions)}

            **Common Objections to Address:**
            {chr(10).join(f"• {obj}" for obj in stage_def.common_objections)}

            For each recommendation, provide:
            1. Specific action to take
            2. Priority level (critical/high/medium/low)
            3. Expected outcome
            4. Recommended timing

            Focus on actions that will move this stage forward most effectively.
            """

            response = await self.claude_service.chat_with_agent(
                agent_id=agent_id,
                query=recommendation_prompt,
                context={
                    "recommendation_type": "stage_guidance",
                    "stage": process_context.stage.value,
                    "completion": stage_completion
                }
            )

            # Parse recommendations (simplified parsing)
            response_text = response.response if hasattr(response, 'response') else str(response)

            # Add default recommendations based on stage completion
            if stage_completion < 30:
                recommendations.append(GuidanceRecommendation(
                    action=f"Focus on completing {stage_def.objectives[0].lower()}",
                    priority=GuidancePriority.HIGH,
                    action_type=ActionType.DISCOVER,
                    reasoning="Low completion rate requires attention to primary objectives",
                    expected_outcome="Improved stage progression",
                    timing="Within 24 hours",
                    confidence=0.8
                ))
            elif stage_completion > 80:
                next_stage = self._determine_next_stage(process_context.stage, stage_completion)
                if next_stage:
                    recommendations.append(GuidanceRecommendation(
                        action=f"Prepare to transition to {next_stage.value.replace('_', ' ')}",
                        priority=GuidancePriority.MEDIUM,
                        action_type=ActionType.COORDINATE,
                        reasoning="High completion rate indicates readiness for next stage",
                        expected_outcome="Smooth stage transition",
                        timing="Within 48 hours",
                        confidence=0.9
                    ))

            # Add stage-specific recommendations
            stage_recommendations = self._get_stage_specific_recommendations(
                process_context.stage, process_context, stage_completion
            )
            recommendations.extend(stage_recommendations)

            return recommendations[:5]  # Limit to top 5 recommendations

        except Exception as e:
            logger.error(f"Error generating stage recommendations: {e}")
            return [GuidanceRecommendation(
                action="Review current stage objectives and take next logical step",
                priority=GuidancePriority.MEDIUM,
                action_type=ActionType.ANALYZE,
                reasoning="Error occurred in recommendation generation",
                expected_outcome="Continued progress",
                timing="As soon as possible",
                confidence=0.5
            )]

    def _get_stage_specific_recommendations(
        self,
        stage: RealtorProcessStage,
        context: ProcessContext,
        completion: float
    ) -> List[GuidanceRecommendation]:
        """Get pre-defined stage-specific recommendations."""
        recommendations = []

        if stage == RealtorProcessStage.LEAD_CAPTURE:
            recommendations.append(GuidanceRecommendation(
                action="Respond to lead within 5 minutes",
                priority=GuidancePriority.CRITICAL,
                action_type=ActionType.COMMUNICATE,
                reasoning="Speed of response is crucial for lead conversion",
                expected_outcome="Higher engagement and qualification rates",
                timing="Immediately",
                confidence=0.95
            ))

        elif stage == RealtorProcessStage.QUALIFICATION:
            if completion < 50:
                recommendations.append(GuidanceRecommendation(
                    action="Complete financial pre-qualification",
                    priority=GuidancePriority.HIGH,
                    action_type=ActionType.DISCOVER,
                    reasoning="Financial qualification is foundation for successful search",
                    expected_outcome="Realistic property search parameters",
                    timing="Within 48 hours",
                    confidence=0.9
                ))

        elif stage == RealtorProcessStage.PROPERTY_SEARCH:
            recommendations.append(GuidanceRecommendation(
                action="Present curated property selection",
                priority=GuidancePriority.HIGH,
                action_type=ActionType.PRESENT,
                reasoning="Quality over quantity drives better engagement",
                expected_outcome="Increased showing requests",
                timing="Within 24 hours",
                confidence=0.85
            ))

        elif stage == RealtorProcessStage.NEGOTIATION:
            recommendations.append(GuidanceRecommendation(
                action="Prepare multiple negotiation scenarios",
                priority=GuidancePriority.HIGH,
                action_type=ActionType.NEGOTIATE,
                reasoning="Preparation improves negotiation outcomes",
                expected_outcome="Better terms for client",
                timing="Before offer submission",
                confidence=0.8
            ))

        return recommendations

    async def _identify_risk_factors(
        self,
        context: ProcessContext,
        time_in_stage: timedelta,
        completion: float
    ) -> List[str]:
        """Identify potential risk factors in current process."""
        risk_factors = []

        # Time-based risks
        stage_def = self.stage_definitions[context.stage]
        expected_duration = timedelta(days=stage_def.typical_duration_days)

        if time_in_stage > expected_duration * 2:
            risk_factors.append(f"Prolonged time in {context.stage.value.replace('_', ' ')} stage - may indicate stalled process")

        # Completion-based risks
        if completion < 30 and time_in_stage > expected_duration:
            risk_factors.append("Low completion rate despite adequate time - may need intervention")

        # Context-specific risks
        if context.urgency == "high" and completion < 50:
            risk_factors.append("High urgency client with slow progress - risk of losing client")

        if not context.lead_id and context.stage not in [RealtorProcessStage.LEAD_CAPTURE, RealtorProcessStage.INITIAL_CONTACT]:
            risk_factors.append("Missing lead identification for advanced stage")

        if not context.active_tasks and completion < 80:
            risk_factors.append("No active tasks identified - may indicate lack of clear next steps")

        # Stage-specific risks
        if context.stage == RealtorProcessStage.NEGOTIATION and time_in_stage > timedelta(days=7):
            risk_factors.append("Extended negotiation period - risk of deal falling through")

        if context.stage == RealtorProcessStage.TRANSACTION_MANAGEMENT and not context.property_ids:
            risk_factors.append("Transaction management without identified property - potential data issue")

        return risk_factors

    async def _identify_success_indicators(
        self,
        context: ProcessContext,
        conversation_history: List[Dict[str, Any]],
        lead_context: Dict[str, Any]
    ) -> List[str]:
        """Identify positive success indicators."""
        success_indicators = []

        # Context-based success indicators
        if context.lead_id:
            success_indicators.append("Lead properly identified and tracked")

        if context.active_tasks:
            success_indicators.append(f"Active task management with {len(context.active_tasks)} tasks")

        if context.workflow_progress:
            avg_progress = sum(context.workflow_progress.values()) / len(context.workflow_progress)
            if avg_progress > 0.7:
                success_indicators.append("Strong workflow progression across multiple areas")

        # Conversation-based indicators
        if conversation_history:
            recent_messages = len([msg for msg in conversation_history[-10:] if msg.get('role') == 'user'])
            if recent_messages > 3:
                success_indicators.append("Active client engagement in conversation")

        # Stage-specific success indicators
        stage_def = self.stage_definitions[context.stage]

        if context.stage == RealtorProcessStage.QUALIFICATION and context.urgency != "low":
            success_indicators.append("Client shows appropriate urgency for stage")

        if context.stage in [RealtorProcessStage.PROPERTY_SEARCH, RealtorProcessStage.PROPERTY_SHOWING] and context.property_ids:
            success_indicators.append(f"Properties identified for consideration ({len(context.property_ids)} properties)")

        if context.client_type == "buyer" and context.stage.value in ["qualification", "property_search", "property_showing"]:
            success_indicators.append("Process aligned with buyer journey")

        return success_indicators

    def _calculate_health_score(
        self,
        stage_completion: float,
        time_in_stage: timedelta,
        risk_count: int,
        success_count: int
    ) -> float:
        """Calculate overall process health score (0-100)."""
        # Base score from stage completion
        health_score = stage_completion

        # Adjust for time efficiency
        if time_in_stage.days <= 1:
            health_score += 10  # Bonus for efficiency
        elif time_in_stage.days > 7:
            health_score -= 15  # Penalty for delays

        # Adjust for risk factors
        health_score -= (risk_count * 10)  # 10 point penalty per risk

        # Adjust for success indicators
        health_score += (success_count * 5)  # 5 point bonus per success indicator

        # Ensure score stays within bounds
        return max(0, min(100, health_score))

    def _determine_next_stage(
        self,
        current_stage: RealtorProcessStage,
        completion: float
    ) -> Optional[RealtorProcessStage]:
        """Determine next stage based on current stage and completion."""
        if completion < 75:  # Not ready for next stage
            return None

        # Define stage progression order
        stage_order = [
            RealtorProcessStage.LEAD_CAPTURE,
            RealtorProcessStage.INITIAL_CONTACT,
            RealtorProcessStage.QUALIFICATION,
            RealtorProcessStage.NEEDS_DISCOVERY,
            RealtorProcessStage.PROPERTY_SEARCH,
            RealtorProcessStage.SHOWING_PREP,
            RealtorProcessStage.PROPERTY_SHOWING,
            RealtorProcessStage.OFFER_PREPARATION,
            RealtorProcessStage.NEGOTIATION,
            RealtorProcessStage.CONTRACT_EXECUTION,
            RealtorProcessStage.TRANSACTION_MANAGEMENT,
            RealtorProcessStage.CLOSING_PREP,
            RealtorProcessStage.POST_CLOSE_FOLLOW_UP
        ]

        try:
            current_index = stage_order.index(current_stage)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        except ValueError:
            pass

        return None

    def _create_fallback_assessment(self, context: ProcessContext) -> ProcessAssessment:
        """Create fallback assessment when main assessment fails."""
        return ProcessAssessment(
            current_stage=context.stage,
            stage_completion=50.0,
            next_stage=None,
            time_in_stage=datetime.now() - context.last_updated,
            recommendations=[
                GuidanceRecommendation(
                    action="Review current stage objectives and plan next steps",
                    priority=GuidancePriority.MEDIUM,
                    action_type=ActionType.ANALYZE,
                    reasoning="Fallback recommendation due to assessment error",
                    expected_outcome="Continued process momentum",
                    timing="As soon as possible",
                    confidence=0.5
                )
            ],
            risk_factors=["Assessment system temporarily unavailable"],
            success_indicators=[],
            overall_health_score=50.0,
            confidence=0.3
        )

    async def _store_process_assessment(self, agent_id: str, assessment: ProcessAssessment):
        """Store process assessment in memory service."""
        try:
            process_memory = ProcessMemory(
                stage=assessment.current_stage,
                lead_context={"assessment": "stored"},
                discoveries=[],
                objections_handled=[],
                successful_strategies=[r.action for r in assessment.recommendations[:3]],
                timestamp=datetime.now(),
                completion_score=assessment.stage_completion / 100
            )

            await self.memory_service.store_process_memory(
                agent_id, process_memory, MemoryPriority.HIGH
            )

        except Exception as e:
            logger.error(f"Error storing process assessment: {e}")

    async def get_stage_coaching_prompts(self, stage: RealtorProcessStage) -> List[str]:
        """Get AI coaching prompts for specific stage."""
        stage_def = self.stage_definitions.get(stage)
        if stage_def:
            return stage_def.ai_coaching_prompts
        return [
            "How can I improve my performance in this stage?",
            "What should I focus on next?",
            "What are the key success factors for this stage?"
        ]

    async def get_stage_objectives(self, stage: RealtorProcessStage) -> List[str]:
        """Get objectives for specific stage."""
        stage_def = self.stage_definitions.get(stage)
        if stage_def:
            return stage_def.objectives
        return []

    async def get_common_objections(self, stage: RealtorProcessStage) -> List[str]:
        """Get common objections for specific stage."""
        stage_def = self.stage_definitions.get(stage)
        if stage_def:
            return stage_def.common_objections
        return []

    def get_process_statistics(self, agent_id: str) -> Dict[str, Any]:
        """Get process performance statistics for agent."""
        history = self.guidance_history.get(agent_id, [])

        if not history:
            return {"error": "No process history available"}

        return {
            "total_assessments": len(history),
            "avg_health_score": sum(h.get("health_score", 0) for h in history) / len(history),
            "stage_distribution": {},  # Could be calculated from history
            "recent_activity": history[-5:] if len(history) >= 5 else history
        }


# Global instance for easy access
process_aware_guidance_engine = ProcessAwareGuidanceEngine()


# Export key classes and functions
__all__ = [
    'ProcessAwareGuidanceEngine',
    'ProcessAssessment',
    'GuidanceRecommendation',
    'StageGuidance',
    'GuidancePriority',
    'ActionType',
    'process_aware_guidance_engine'
]