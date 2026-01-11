"""
Enhanced Claude Agent Service - Agent Profile Aware AI Coaching

Extends the base ClaudeAgentService with multi-tenant agent profile integration,
role-specific coaching, and session-based context management.

Key Enhancements:
- Agent profile integration (seller/buyer/transaction coordinator specialization)
- Role-specific coaching prompts and guidance types
- Session-based context awareness
- Personalized communication styles
- Multi-tenant shared agent pool support
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from anthropic import AsyncAnthropic

from ..ghl_utils.config import settings
from .claude_agent_service import (
    ClaudeAgentService, ClaudeResponse, CoachingResponse,
    ObjectionResponse, QuestionSuggestion, AgentQuery
)
from .agent_profile_service import AgentProfileService
from ..models.agent_profile_models import (
    AgentProfile, AgentSession, AgentRole, GuidanceType,
    ConversationStage, CoachingStylePreference, CommunicationStyle
)

logger = logging.getLogger(__name__)


@dataclass
class EnhancedCoachingResponse:
    """Enhanced coaching response with agent profile context"""
    coaching_suggestions: List[str]
    objection_detected: Optional[str]
    recommended_response: Optional[str]
    next_question: Optional[str]
    conversation_stage: str
    confidence: float
    urgency: str
    reasoning: str
    timestamp: datetime = datetime.now()

    # Enhanced fields
    agent_role: str
    guidance_types_applied: List[str]
    role_specific_insights: List[str]
    coaching_style_adaptation: str
    session_context: Optional[Dict[str, Any]] = None


@dataclass
class RoleSpecificGuidance:
    """Role-specific guidance templates and coaching strategies"""
    buyer_agent_prompts: Dict[str, str]
    seller_agent_prompts: Dict[str, str]
    transaction_coordinator_prompts: Dict[str, str]
    guidance_type_templates: Dict[str, Dict[str, str]]


class EnhancedClaudeAgentService:
    """
    Agent profile aware Claude service with role-specific coaching.

    Provides specialized coaching for:
    - Buyer Agents: Property search, qualification, offer strategy
    - Seller Agents: Pricing, marketing, negotiation tactics
    - Transaction Coordinators: Compliance, timeline, documentation
    """

    def __init__(self):
        # Initialize base Claude service
        self.base_service = ClaudeAgentService()
        self.client = self.base_service.client

        # Initialize agent profile service
        self.agent_profile_service = AgentProfileService()

        # Role-specific guidance system
        self.role_guidance = self._initialize_role_guidance()

        # Enhanced session context cache
        self.enhanced_context_cache: Dict[str, Dict[str, Any]] = {}

    async def get_agent_aware_coaching(
        self,
        agent_id: str,
        session_id: str,
        conversation_context: Dict[str, Any],
        prospect_message: str,
        conversation_stage: str = "discovery",
        location_id: Optional[str] = None
    ) -> EnhancedCoachingResponse:
        """
        Get role-specific coaching based on agent profile and session context.

        Args:
            agent_id: Agent identifier
            session_id: Current agent session ID
            conversation_context: Full conversation context and lead data
            prospect_message: Latest message from the prospect
            conversation_stage: Current conversation stage
            location_id: Location context for multi-tenant access

        Returns:
            EnhancedCoachingResponse with role-specific coaching and insights
        """
        try:
            # Get agent profile and session context
            agent_profile = await self.agent_profile_service.get_agent_profile(
                agent_id=agent_id,
                requester_location_id=location_id or conversation_context.get("location_id")
            )

            agent_session = await self.agent_profile_service.get_agent_session(session_id)

            if not agent_profile:
                logger.warning(f"Agent profile not found for {agent_id}, falling back to base service")
                base_response = await self.base_service.get_real_time_coaching(
                    agent_id, conversation_context, prospect_message, conversation_stage
                )
                return await self._enhance_base_response(base_response, "unknown", [])

            # Filter guidance types based on agent preferences and session configuration
            active_guidance_types = self._get_active_guidance_types(agent_profile, agent_session)

            # Build role-specific coaching prompt
            enhanced_prompt = await self._build_role_specific_coaching_prompt(
                agent_profile, agent_session, conversation_stage, conversation_context
            )

            # Create enhanced coaching query with role context
            coaching_query = await self._build_enhanced_coaching_query(
                agent_profile, agent_session, prospect_message,
                conversation_context, active_guidance_types
            )

            # Get Claude's enhanced coaching response
            response = await self.client.messages.create(
                model=settings.claude_model,
                max_tokens=800,
                temperature=0.3,  # Lower temperature for consistent coaching
                system=enhanced_prompt,
                messages=[{"role": "user", "content": coaching_query}]
            )

            claude_text = response.content[0].text

            # Parse enhanced coaching response
            enhanced_response = await self._parse_enhanced_coaching_response(
                claude_text, agent_profile, agent_session,
                active_guidance_types, conversation_stage
            )

            # Update session metrics and store coaching interaction
            await self._update_session_coaching_metrics(agent_session, enhanced_response)

            # Store coaching history for learning and improvement
            await self._store_coaching_interaction(
                agent_id, session_id, coaching_query, claude_text, enhanced_response
            )

            logger.info(
                f"Enhanced coaching provided for {agent_profile.primary_role.value} agent {agent_id}, "
                f"guidance types: {[gt.value for gt in active_guidance_types]}"
            )

            return enhanced_response

        except Exception as e:
            logger.error(f"Error in enhanced agent-aware coaching: {str(e)}")
            # Fallback to base service
            base_response = await self.base_service.get_real_time_coaching(
                agent_id, conversation_context, prospect_message, conversation_stage
            )
            return await self._enhance_base_response(base_response, "fallback", [])

    async def start_agent_coaching_session(
        self,
        agent_id: str,
        location_id: str,
        lead_id: Optional[str] = None,
        guidance_types: Optional[List[GuidanceType]] = None,
        conversation_stage: ConversationStage = ConversationStage.DISCOVERY
    ) -> Dict[str, Any]:
        """
        Start an enhanced coaching session with agent profile context.

        Args:
            agent_id: Agent identifier
            location_id: Location context for multi-tenant access
            lead_id: Optional lead context
            guidance_types: Specific guidance types for this session
            conversation_stage: Starting conversation stage

        Returns:
            Session information with enhanced coaching capabilities
        """
        try:
            # Get agent profile
            agent_profile = await self.agent_profile_service.get_agent_profile(
                agent_id=agent_id,
                requester_location_id=location_id
            )

            if not agent_profile:
                return {
                    "error": f"Agent profile not found for {agent_id} in location {location_id}",
                    "fallback": "Use base claude_agent_service for coaching"
                }

            # Determine guidance types (user preferences or agent defaults)
            active_guidance_types = guidance_types or agent_profile.preferred_guidance_types

            # Start agent session
            agent_session = await self.agent_profile_service.start_agent_session(
                agent_id=agent_id,
                location_id=location_id,
                current_lead_id=lead_id,
                conversation_stage=conversation_stage,
                active_guidance_types=active_guidance_types
            )

            # Build role-specific coaching context
            coaching_context = await self._build_initial_coaching_context(
                agent_profile, agent_session
            )

            return {
                "session_id": agent_session.session_id,
                "agent_id": agent_id,
                "agent_role": agent_profile.primary_role.value,
                "secondary_roles": [role.value for role in agent_profile.secondary_roles],
                "active_guidance_types": [gt.value for gt in active_guidance_types],
                "coaching_style": agent_profile.coaching_style_preference.value,
                "communication_style": agent_profile.communication_style.value,
                "conversation_stage": conversation_stage.value,
                "coaching_context": coaching_context,
                "enhanced_features": True,
                "location_id": location_id,
                "lead_id": lead_id,
                "session_start_time": agent_session.session_start_time.isoformat(),
                "status": "active"
            }

        except Exception as e:
            logger.error(f"Error starting enhanced coaching session: {str(e)}")
            return {
                "error": str(e),
                "fallback": "Use base claude_agent_service for coaching"
            }

    async def get_role_specific_insights(
        self,
        agent_id: str,
        session_id: str,
        lead_data: Dict[str, Any],
        query_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Get role-specific insights based on agent specialization.

        Args:
            agent_id: Agent identifier
            session_id: Current session
            lead_data: Lead information and context
            query_type: Type of insights (comprehensive, qualification, strategy, closing)

        Returns:
            Role-specific insights and recommendations
        """
        try:
            # Get agent profile and session
            agent_profile = await self.agent_profile_service.get_agent_profile(agent_id)
            agent_session = await self.agent_profile_service.get_agent_session(session_id)

            if not agent_profile:
                return {"error": "Agent profile not found"}

            # Build role-specific query based on agent specialization
            insights_query = await self._build_role_specific_insights_query(
                agent_profile, lead_data, query_type
            )

            # Get enhanced insights from Claude
            response = await self.client.messages.create(
                model=settings.claude_model,
                max_tokens=600,
                temperature=0.4,
                system=await self._build_insights_system_prompt(agent_profile),
                messages=[{"role": "user", "content": insights_query}]
            )

            claude_text = response.content[0].text

            # Parse and structure insights by role
            structured_insights = await self._parse_role_specific_insights(
                claude_text, agent_profile, lead_data
            )

            return {
                "agent_id": agent_id,
                "agent_role": agent_profile.primary_role.value,
                "query_type": query_type,
                "insights": structured_insights,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "enhanced_features": True
            }

        except Exception as e:
            logger.error(f"Error getting role-specific insights: {str(e)}")
            return {"error": str(e)}

    def _get_active_guidance_types(
        self,
        agent_profile: AgentProfile,
        agent_session: Optional[AgentSession] = None
    ) -> List[GuidanceType]:
        """Determine active guidance types for the session."""
        if agent_session and agent_session.active_guidance_types:
            return agent_session.active_guidance_types
        return agent_profile.preferred_guidance_types

    async def _build_role_specific_coaching_prompt(
        self,
        agent_profile: AgentProfile,
        agent_session: Optional[AgentSession],
        conversation_stage: str,
        conversation_context: Dict[str, Any]
    ) -> str:
        """Build role-specific coaching prompt for Claude."""

        # Get base role prompt
        role = agent_profile.primary_role
        base_prompt = self.role_guidance.buyer_agent_prompts.get("base", "")

        if role == AgentRole.SELLER_AGENT:
            base_prompt = self.role_guidance.seller_agent_prompts.get("base", "")
        elif role == AgentRole.TRANSACTION_COORDINATOR:
            base_prompt = self.role_guidance.transaction_coordinator_prompts.get("base", "")
        elif role == AgentRole.DUAL_AGENT:
            # For dual agents, adapt based on lead context
            lead_type = conversation_context.get("lead_type", "buyer")
            if lead_type == "seller":
                base_prompt = self.role_guidance.seller_agent_prompts.get("base", "")
            else:
                base_prompt = self.role_guidance.buyer_agent_prompts.get("base", "")

        # Get guidance type specific prompts
        active_guidance_types = self._get_active_guidance_types(agent_profile, agent_session)
        guidance_prompts = []

        for guidance_type in active_guidance_types:
            guidance_key = guidance_type.value.lower()
            if guidance_key in self.role_guidance.guidance_type_templates:
                role_templates = self.role_guidance.guidance_type_templates[guidance_key]
                role_key = role.value.lower()
                if role_key in role_templates:
                    guidance_prompts.append(role_templates[role_key])

        # Build comprehensive prompt
        enhanced_prompt = f"""{base_prompt}

AGENT SPECIALIZATION: {role.value.replace('_', ' ').title()}
YEARS OF EXPERIENCE: {agent_profile.years_experience} years
SPECIALIZATIONS: {', '.join(agent_profile.specializations)}
COACHING STYLE PREFERENCE: {agent_profile.coaching_style_preference.value}
COMMUNICATION STYLE: {agent_profile.communication_style.value}

ACTIVE GUIDANCE TYPES:
{chr(10).join(f"- {gt.value}: {desc}" for gt, desc in zip(active_guidance_types, guidance_prompts))}

CONVERSATION STAGE: {conversation_stage}
CURRENT SESSION CONTEXT: {json.dumps(conversation_context.get('session_context', {}), indent=2)}

ROLE-SPECIFIC COACHING FOCUS:
{chr(10).join(guidance_prompts)}

Current date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

RESPONSE FORMAT - Provide role-specific coaching with these sections:
1. **IMMEDIATE FOCUS**: Priority actions for a {role.value.replace('_', ' ')} specialist
2. **ROLE-SPECIFIC INSIGHTS**: Insights specific to {role.value.replace('_', ' ')} expertise
3. **RECOMMENDED RESPONSE**: Tailored to {agent_profile.communication_style.value} style
4. **NEXT QUESTION**: Best follow-up for {role.value.replace('_', ' ')} specialization
5. **URGENCY & REASONING**: Context-aware urgency assessment"""

        return enhanced_prompt

    async def _build_enhanced_coaching_query(
        self,
        agent_profile: AgentProfile,
        agent_session: Optional[AgentSession],
        prospect_message: str,
        conversation_context: Dict[str, Any],
        active_guidance_types: List[GuidanceType]
    ) -> str:
        """Build enhanced coaching query with agent profile context."""

        query = f"""
        ENHANCED ROLE-SPECIFIC COACHING REQUEST:

        Agent Profile:
        - Role: {agent_profile.primary_role.value}
        - Experience: {agent_profile.years_experience} years
        - Specializations: {', '.join(agent_profile.specializations)}
        - Communication Style: {agent_profile.communication_style.value}
        - Coaching Style: {agent_profile.coaching_style_preference.value}

        Session Context:
        - Session ID: {agent_session.session_id if agent_session else 'N/A'}
        - Active Guidance Types: {[gt.value for gt in active_guidance_types]}
        - Current Stage: {agent_session.conversation_stage.value if agent_session else 'unknown'}
        - Lead ID: {agent_session.current_lead_id if agent_session else conversation_context.get('lead_id')}

        Latest Prospect Message: "{prospect_message}"

        Lead Context: {json.dumps(conversation_context.get('lead_data', {}), indent=2)}

        Please provide specialized coaching for this {agent_profile.primary_role.value.replace('_', ' ')} based on:

        1. Their specific role expertise and specializations
        2. Their preferred coaching and communication style
        3. The active guidance types they want to focus on
        4. The current conversation stage and lead context

        Focus on actionable, role-specific advice that leverages their expertise while adapting to their preferred coaching style.
        """

        return query

    async def _parse_enhanced_coaching_response(
        self,
        claude_text: str,
        agent_profile: AgentProfile,
        agent_session: Optional[AgentSession],
        active_guidance_types: List[GuidanceType],
        conversation_stage: str
    ) -> EnhancedCoachingResponse:
        """Parse Claude's response into enhanced coaching structure."""

        # Use base service parsing as foundation
        base_response = await self.base_service._parse_coaching_response(
            claude_text, conversation_stage, ""
        )

        # Extract role-specific insights
        role_specific_insights = []
        coaching_style_adaptation = ""

        try:
            lines = claude_text.split('\n')
            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Look for role-specific insights section
                if any(keyword in line.lower() for keyword in ["role-specific", "specialist", "expertise"]):
                    current_section = "role_insights"
                    continue
                elif any(keyword in line.lower() for keyword in ["coaching style", "adaptation", "communication"]):
                    current_section = "style_adaptation"
                    continue

                # Extract content
                if current_section == "role_insights" and (line.startswith('-') or line.startswith('•')):
                    role_specific_insights.append(line.lstrip('-•* '))
                elif current_section == "style_adaptation" and not line.startswith('**'):
                    if coaching_style_adaptation == "":
                        coaching_style_adaptation = line.lstrip('-•* ')

            # Fallback content
            if not role_specific_insights:
                role_name = agent_profile.primary_role.value.replace('_', ' ')
                role_specific_insights = [
                    f"Apply {role_name} expertise to this situation",
                    f"Leverage {role_name} specializations: {', '.join(agent_profile.specializations[:2])}"
                ]

            if not coaching_style_adaptation:
                coaching_style_adaptation = f"Adapted for {agent_profile.coaching_style_preference.value} coaching style"

        except Exception as e:
            logger.warning(f"Error parsing enhanced coaching response: {str(e)}")
            role_specific_insights = ["Apply role-specific expertise"]
            coaching_style_adaptation = "Standard coaching adaptation"

        # Build session context
        session_context = None
        if agent_session:
            session_context = {
                "session_id": agent_session.session_id,
                "duration_minutes": agent_session.get_session_duration_minutes(),
                "messages_exchanged": agent_session.messages_exchanged,
                "guidance_requests": agent_session.guidance_requests,
                "effectiveness_score": agent_session.coaching_effectiveness_score
            }

        return EnhancedCoachingResponse(
            coaching_suggestions=base_response.coaching_suggestions,
            objection_detected=base_response.objection_detected,
            recommended_response=base_response.recommended_response,
            next_question=base_response.next_question,
            conversation_stage=base_response.conversation_stage,
            confidence=base_response.confidence,
            urgency=base_response.urgency,
            reasoning=base_response.reasoning,
            timestamp=datetime.now(),
            agent_role=agent_profile.primary_role.value,
            guidance_types_applied=[gt.value for gt in active_guidance_types],
            role_specific_insights=role_specific_insights,
            coaching_style_adaptation=coaching_style_adaptation,
            session_context=session_context
        )

    async def _build_initial_coaching_context(
        self,
        agent_profile: AgentProfile,
        agent_session: AgentSession
    ) -> Dict[str, Any]:
        """Build initial coaching context for new sessions."""

        return {
            "role_specialization": {
                "primary_role": agent_profile.primary_role.value,
                "secondary_roles": [role.value for role in agent_profile.secondary_roles],
                "specializations": agent_profile.specializations,
                "years_experience": agent_profile.years_experience
            },
            "coaching_preferences": {
                "coaching_style": agent_profile.coaching_style_preference.value,
                "communication_style": agent_profile.communication_style.value,
                "preferred_guidance_types": [gt.value for gt in agent_profile.preferred_guidance_types]
            },
            "session_setup": {
                "conversation_stage": agent_session.conversation_stage.value,
                "active_guidance_types": [gt.value for gt in agent_session.active_guidance_types],
                "session_goals": self._get_role_specific_session_goals(agent_profile.primary_role)
            },
            "performance_context": {
                "skill_levels": agent_profile.skill_levels,
                "performance_metrics": agent_profile.performance_metrics_summary
            }
        }

    def _get_role_specific_session_goals(self, role: AgentRole) -> List[str]:
        """Get default session goals based on agent role."""

        goals_map = {
            AgentRole.BUYER_AGENT: [
                "Qualify buyer's budget and financing",
                "Understand property preferences and requirements",
                "Schedule property showings",
                "Guide through offer and negotiation process"
            ],
            AgentRole.SELLER_AGENT: [
                "Assess property pricing and market position",
                "Develop marketing strategy",
                "Coordinate showings and open houses",
                "Negotiate offers and counteroffers"
            ],
            AgentRole.TRANSACTION_COORDINATOR: [
                "Ensure compliance with all requirements",
                "Coordinate timeline and milestones",
                "Manage documentation and paperwork",
                "Facilitate communication between parties"
            ],
            AgentRole.DUAL_AGENT: [
                "Balance buyer and seller interests ethically",
                "Manage dual representation disclosure",
                "Coordinate both sides of transaction",
                "Ensure fair and transparent process"
            ]
        }

        return goals_map.get(role, ["Provide excellent client service", "Navigate transaction successfully"])

    async def _update_session_coaching_metrics(
        self,
        agent_session: Optional[AgentSession],
        coaching_response: EnhancedCoachingResponse
    ):
        """Update session metrics based on coaching interaction."""

        if not agent_session:
            return

        try:
            # Update guidance request count
            agent_session.guidance_requests += 1

            # Update coaching effectiveness score based on response quality
            new_effectiveness = coaching_response.confidence * 0.3 + agent_session.coaching_effectiveness_score * 0.7
            agent_session.coaching_effectiveness_score = min(1.0, new_effectiveness)

            # Update session activity
            agent_session.last_activity = datetime.now()

            # Save updated session
            await self.agent_profile_service.update_agent_session(agent_session)

        except Exception as e:
            logger.warning(f"Error updating session coaching metrics: {str(e)}")

    async def _store_coaching_interaction(
        self,
        agent_id: str,
        session_id: str,
        coaching_query: str,
        claude_response: str,
        enhanced_response: EnhancedCoachingResponse
    ):
        """Store coaching interaction for learning and improvement."""

        try:
            # Create coaching history entry
            from ..models.agent_profile_models import CreateCoachingHistoryRequest

            coaching_history = CreateCoachingHistoryRequest(
                agent_id=agent_id,
                session_id=session_id,
                location_id=enhanced_response.session_context.get("location_id") if enhanced_response.session_context else "unknown",
                guidance_type=enhanced_response.guidance_types_applied[0] if enhanced_response.guidance_types_applied else "response_suggestions",
                user_message=coaching_query[:500],  # Truncate for storage
                claude_response={
                    "response": claude_response[:1000],  # Truncate for storage
                    "confidence": enhanced_response.confidence,
                    "urgency": enhanced_response.urgency,
                    "role_specific_insights": enhanced_response.role_specific_insights,
                    "guidance_types_applied": enhanced_response.guidance_types_applied
                },
                lead_stage=enhanced_response.conversation_stage,
                context={
                    "agent_role": enhanced_response.agent_role,
                    "coaching_style_adaptation": enhanced_response.coaching_style_adaptation
                }
            )

            await self.agent_profile_service.record_coaching_interaction(coaching_history)

        except Exception as e:
            logger.warning(f"Error storing coaching interaction: {str(e)}")

    async def _enhance_base_response(
        self,
        base_response: CoachingResponse,
        agent_role: str,
        guidance_types: List[str]
    ) -> EnhancedCoachingResponse:
        """Convert base coaching response to enhanced format for fallback scenarios."""

        return EnhancedCoachingResponse(
            coaching_suggestions=base_response.coaching_suggestions,
            objection_detected=base_response.objection_detected,
            recommended_response=base_response.recommended_response,
            next_question=base_response.next_question,
            conversation_stage=base_response.conversation_stage,
            confidence=base_response.confidence,
            urgency=base_response.urgency,
            reasoning=base_response.reasoning,
            timestamp=base_response.timestamp,
            agent_role=agent_role,
            guidance_types_applied=guidance_types,
            role_specific_insights=["Fallback mode - enhance with agent profile integration"],
            coaching_style_adaptation="Standard coaching approach",
            session_context=None
        )

    async def _build_role_specific_insights_query(
        self,
        agent_profile: AgentProfile,
        lead_data: Dict[str, Any],
        query_type: str
    ) -> str:
        """Build role-specific insights query for comprehensive lead analysis."""

        role_context = {
            AgentRole.BUYER_AGENT: {
                "focus": "buyer qualification, property matching, offer strategy",
                "key_questions": "Budget verification, timeline, property preferences, financing pre-approval"
            },
            AgentRole.SELLER_AGENT: {
                "focus": "pricing strategy, marketing approach, showing management",
                "key_questions": "Motivation to sell, timeline, pricing expectations, property condition"
            },
            AgentRole.TRANSACTION_COORDINATOR: {
                "focus": "compliance, documentation, timeline management",
                "key_questions": "Required disclosures, inspection contingencies, financing deadlines"
            }
        }

        context = role_context.get(agent_profile.primary_role, role_context[AgentRole.BUYER_AGENT])

        query = f"""
        ROLE-SPECIFIC LEAD INSIGHTS REQUEST

        Agent Specialization: {agent_profile.primary_role.value} ({agent_profile.years_experience} years experience)
        Agent Specializations: {', '.join(agent_profile.specializations)}
        Query Type: {query_type}

        Lead Data: {json.dumps(lead_data, indent=2)}

        As a {agent_profile.primary_role.value.replace('_', ' ')} specialist, analyze this lead focusing on:

        Primary Focus Areas: {context['focus']}
        Key Assessment Questions: {context['key_questions']}

        Provide insights specifically relevant to a {agent_profile.primary_role.value.replace('_', ' ')} including:
        1. Role-specific qualification assessment
        2. Recommended next steps for this specialization
        3. Potential challenges specific to this role
        4. Opportunities to leverage your expertise
        5. Timeline and priority recommendations
        """

        return query

    async def _build_insights_system_prompt(self, agent_profile: AgentProfile) -> str:
        """Build insights-focused system prompt."""

        return f"""You are an expert real estate insights specialist for {agent_profile.primary_role.value.replace('_', ' ')} agents.

Your role is to provide specialized insights that help agents in this specific role maximize their effectiveness and serve their clients better.

Agent Context:
- Primary Role: {agent_profile.primary_role.value}
- Experience Level: {agent_profile.years_experience} years
- Specializations: {', '.join(agent_profile.specializations)}

Focus on insights that are:
1. Specifically relevant to this agent's role and expertise
2. Actionable and practical for immediate implementation
3. Based on the agent's experience level and specializations
4. Aligned with current market conditions and best practices

Structure your insights with clear sections for:
- Role-Specific Assessment
- Recommended Actions
- Potential Challenges
- Success Opportunities
- Timeline & Priorities"""

    async def _parse_role_specific_insights(
        self,
        claude_text: str,
        agent_profile: AgentProfile,
        lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse role-specific insights from Claude response."""

        try:
            # Parse sections from Claude's response
            insights = {
                "role_assessment": [],
                "recommended_actions": [],
                "potential_challenges": [],
                "success_opportunities": [],
                "timeline_priorities": [],
                "raw_response": claude_text
            }

            lines = claude_text.split('\n')
            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Detect sections
                if any(keyword in line.lower() for keyword in ["assessment", "evaluation"]):
                    current_section = "role_assessment"
                elif any(keyword in line.lower() for keyword in ["recommended", "actions", "next steps"]):
                    current_section = "recommended_actions"
                elif any(keyword in line.lower() for keyword in ["challenges", "concerns", "risks"]):
                    current_section = "potential_challenges"
                elif any(keyword in line.lower() for keyword in ["opportunities", "potential", "success"]):
                    current_section = "success_opportunities"
                elif any(keyword in line.lower() for keyword in ["timeline", "priorities", "urgency"]):
                    current_section = "timeline_priorities"

                # Extract content
                if current_section and (line.startswith('-') or line.startswith('•')):
                    insights[current_section].append(line.lstrip('-•* '))

            # Ensure we have content in each section
            for section in ["role_assessment", "recommended_actions", "potential_challenges", "success_opportunities", "timeline_priorities"]:
                if not insights[section]:
                    insights[section] = [f"No specific {section.replace('_', ' ')} identified"]

            return insights

        except Exception as e:
            logger.warning(f"Error parsing role-specific insights: {str(e)}")
            return {
                "role_assessment": ["Analysis completed"],
                "recommended_actions": ["Review lead data and follow up appropriately"],
                "potential_challenges": ["Standard lead qualification challenges"],
                "success_opportunities": ["Build rapport and understand client needs"],
                "timeline_priorities": ["Schedule follow-up within 24-48 hours"],
                "error": str(e),
                "raw_response": claude_text
            }

    def _initialize_role_guidance(self) -> RoleSpecificGuidance:
        """Initialize role-specific guidance templates and prompts."""

        buyer_agent_prompts = {
            "base": """You are an expert buyer agent coach specializing in helping agents guide clients through property searches, qualification, and purchase processes. Your expertise includes:

- Buyer qualification and pre-approval guidance
- Property search strategy and showing coordination
- Offer strategy and negotiation tactics
- Market analysis for buyers
- First-time homebuyer education
- Investment property analysis""",

            "qualification": "Focus on budget verification, timeline assessment, and property requirements gathering",
            "discovery": "Explore lifestyle needs, location preferences, and property must-haves vs nice-to-haves",
            "objection_handling": "Address budget concerns, market timing, and property-specific objections",
            "closing": "Guide toward property showings, offer preparation, and purchase decisions"
        }

        seller_agent_prompts = {
            "base": """You are an expert seller agent coach specializing in helping agents guide clients through property marketing, pricing, and sale processes. Your expertise includes:

- Pricing strategy and market analysis
- Marketing and staging recommendations
- Showing coordination and feedback management
- Offer evaluation and negotiation
- Market timing and positioning
- Property preparation and presentation""",

            "qualification": "Assess motivation to sell, timeline flexibility, and pricing expectations",
            "discovery": "Understand property features, neighborhood advantages, and seller priorities",
            "objection_handling": "Address pricing concerns, market conditions, and timing objections",
            "closing": "Guide toward listing agreements, pricing decisions, and marketing approval"
        }

        transaction_coordinator_prompts = {
            "base": """You are an expert transaction coordination coach specializing in helping agents manage compliance, timelines, and documentation. Your expertise includes:

- Contract compliance and requirement tracking
- Timeline management and milestone coordination
- Documentation and disclosure management
- Communication facilitation between parties
- Problem resolution and contingency handling
- Closing preparation and coordination""",

            "qualification": "Verify contract requirements, contingency timelines, and compliance needs",
            "discovery": "Identify potential issues, required documentation, and key deadlines",
            "objection_handling": "Address timeline concerns, documentation requirements, and process questions",
            "closing": "Guide toward successful closing completion and post-closing requirements"
        }

        guidance_type_templates = {
            "response_suggestions": {
                "buyer_agent": "Provide specific response suggestions that help qualify buyers and advance toward showings",
                "seller_agent": "Suggest responses that position your expertise and move toward listing agreements",
                "transaction_coordinator": "Recommend responses that ensure compliance and maintain timeline momentum"
            },
            "strategy_coaching": {
                "buyer_agent": "Coach on buyer consultation strategy, property search approach, and offer tactics",
                "seller_agent": "Guide pricing strategy, marketing positioning, and negotiation approach",
                "transaction_coordinator": "Strategic timeline management and proactive issue resolution"
            },
            "process_navigation": {
                "buyer_agent": "Navigate pre-approval process, property search, and purchase workflow",
                "seller_agent": "Guide listing process, marketing execution, and sale completion",
                "transaction_coordinator": "Manage contract-to-close process and compliance requirements"
            },
            "performance_insights": {
                "buyer_agent": "Analyze conversion rates, showing efficiency, and client satisfaction",
                "seller_agent": "Assess pricing accuracy, marketing effectiveness, and time-on-market",
                "transaction_coordinator": "Track compliance rates, timeline adherence, and closing success"
            }
        }

        return RoleSpecificGuidance(
            buyer_agent_prompts=buyer_agent_prompts,
            seller_agent_prompts=seller_agent_prompts,
            transaction_coordinator_prompts=transaction_coordinator_prompts,
            guidance_type_templates=guidance_type_templates
        )


# Global instance for easy access
enhanced_claude_agent_service = EnhancedClaudeAgentService()


async def get_agent_aware_coaching(
    agent_id: str,
    session_id: str,
    conversation_context: Dict[str, Any],
    prospect_message: str,
    conversation_stage: str = "discovery",
    location_id: Optional[str] = None
) -> EnhancedCoachingResponse:
    """Convenience function for agent-aware coaching"""
    return await enhanced_claude_agent_service.get_agent_aware_coaching(
        agent_id, session_id, conversation_context, prospect_message, conversation_stage, location_id
    )


async def start_enhanced_coaching_session(
    agent_id: str,
    location_id: str,
    lead_id: Optional[str] = None,
    guidance_types: Optional[List[GuidanceType]] = None
) -> Dict[str, Any]:
    """Convenience function for starting enhanced coaching sessions"""
    return await enhanced_claude_agent_service.start_agent_coaching_session(
        agent_id, location_id, lead_id, guidance_types
    )