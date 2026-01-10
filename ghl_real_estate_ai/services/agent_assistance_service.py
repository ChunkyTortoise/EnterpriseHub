"""
Agent Assistance Service for Real Estate AI.

Provides intelligent conversation suggestions, objection handling strategies,
and performance coaching for real estate agents using Claude and behavioral data.

Key Features:
- Conversation strategy suggestions based on lead behavior
- Objection handling with proven scripts
- Performance analytics and coaching recommendations
- Real-time conversation guidance
- Lead progression optimization
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

try:
    from ghl_real_estate_ai.core.llm_client import LLMClient
    from ghl_real_estate_ai.ghl_utils.config import settings
    from ghl_real_estate_ai.ghl_utils.logger import get_logger
except ImportError:
    # Fallback for streamlit demo context
    from core.llm_client import LLMClient
    from ghl_utils.config import settings
    from ghl_utils.logger import get_logger

logger = get_logger(__name__)


class ConversationStage(Enum):
    """Conversation stage identification."""
    INITIAL_CONTACT = "initial_contact"
    QUALIFYING = "qualifying"
    PRESENTING = "presenting"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"
    NURTURING = "nurturing"


class ObjectionType(Enum):
    """Common real estate objection categories."""
    PRICE = "price"              # "Too expensive"
    TIMING = "timing"            # "Not ready yet"
    TRUST = "trust"              # "Need to think about it"
    AUTHORITY = "authority"      # "Need to discuss with spouse"
    NEED = "need"                # "Don't really need to move"
    COMPARISON = "comparison"    # "Want to see other options"
    FINANCING = "financing"      # "Can't get approved"


class ConversationMomentum(Enum):
    """Conversation momentum levels."""
    HIGH = "high"        # Engaged, asking questions, sharing details
    MEDIUM = "medium"    # Responding but not deeply engaged
    LOW = "low"          # Short responses, disengaged
    STALLED = "stalled"  # No recent responses


@dataclass
class ConversationSuggestion:
    """Conversation strategy suggestion."""
    suggestion_type: str
    priority: str  # "high", "medium", "low"
    message: str
    reasoning: str
    confidence: float
    timing_recommendation: str
    alternatives: List[str]


@dataclass
class ObjectionResponse:
    """Objection handling response strategy."""
    objection_type: ObjectionType
    response_script: str
    follow_up_questions: List[str]
    alternative_approaches: List[str]
    success_probability: float
    coaching_notes: str


@dataclass
class PerformanceInsight:
    """Performance coaching insight."""
    area: str
    current_performance: Dict[str, Any]
    benchmark: Dict[str, Any]
    improvement_suggestion: str
    impact_level: str
    implementation_difficulty: str


@dataclass
class AgentGuidance:
    """Complete agent assistance package."""
    conversation_suggestions: List[ConversationSuggestion]
    objection_responses: List[ObjectionResponse]
    performance_insights: List[PerformanceInsight]
    lead_progression_strategy: Dict[str, Any]
    next_best_actions: List[str]
    conversation_momentum: ConversationMomentum
    confidence_score: float


class AgentAssistanceService:
    """
    Provides real-time assistance and coaching for real estate agents.

    Analyzes conversations, identifies opportunities, suggests responses,
    and provides performance coaching based on behavioral data.
    """

    def __init__(self, tenant_id: str, llm_client: Optional[LLMClient] = None):
        """
        Initialize agent assistance service.

        Args:
            tenant_id: Tenant identifier for multi-tenant support
            llm_client: Optional LLM client for testing
        """
        self.tenant_id = tenant_id
        self.llm_client = llm_client or LLMClient(
            provider="claude",
            model=settings.claude_model
        )

        # Performance tracking (would be database in production)
        self.performance_data = {}
        self.conversation_patterns = {}

        logger.info(f"Agent assistance service initialized for tenant {tenant_id}")

    async def generate_conversation_assistance(
        self,
        contact_id: str,
        conversation_history: List[Dict[str, Any]],
        extracted_preferences: Dict[str, Any],
        lead_score: int,
        behavioral_context: Optional[Dict[str, Any]] = None
    ) -> AgentGuidance:
        """
        Generate comprehensive conversation assistance for an agent.

        Args:
            contact_id: Contact identifier
            conversation_history: Full conversation history
            extracted_preferences: Lead's extracted preferences
            lead_score: Current lead score
            behavioral_context: Optional behavioral insights

        Returns:
            AgentGuidance with suggestions and strategies
        """
        try:
            # 1. Analyze conversation stage and momentum
            conversation_stage = self._identify_conversation_stage(
                conversation_history,
                extracted_preferences,
                lead_score
            )

            momentum = self._assess_conversation_momentum(conversation_history)

            # 2. Generate conversation suggestions
            conversation_suggestions = await self._generate_conversation_suggestions(
                conversation_history,
                extracted_preferences,
                lead_score,
                conversation_stage,
                momentum
            )

            # 3. Identify and prepare objection responses
            objection_responses = await self._prepare_objection_responses(
                conversation_history,
                extracted_preferences,
                conversation_stage
            )

            # 4. Analyze performance and provide coaching
            performance_insights = await self._generate_performance_insights(
                contact_id,
                conversation_history,
                lead_score,
                conversation_stage
            )

            # 5. Develop lead progression strategy
            progression_strategy = await self._develop_progression_strategy(
                extracted_preferences,
                lead_score,
                conversation_stage,
                momentum,
                behavioral_context
            )

            # 6. Determine next best actions
            next_best_actions = self._determine_next_best_actions(
                conversation_stage,
                momentum,
                lead_score,
                extracted_preferences
            )

            # 7. Calculate overall confidence
            confidence_score = self._calculate_confidence_score(
                conversation_suggestions,
                momentum,
                lead_score
            )

            return AgentGuidance(
                conversation_suggestions=conversation_suggestions,
                objection_responses=objection_responses,
                performance_insights=performance_insights,
                lead_progression_strategy=progression_strategy,
                next_best_actions=next_best_actions,
                conversation_momentum=momentum,
                confidence_score=confidence_score
            )

        except Exception as e:
            logger.error(f"Failed to generate conversation assistance: {str(e)}")
            return await self._fallback_agent_guidance()

    def _identify_conversation_stage(
        self,
        conversation_history: List[Dict[str, Any]],
        extracted_preferences: Dict[str, Any],
        lead_score: int
    ) -> ConversationStage:
        """Identify current conversation stage."""
        if not conversation_history:
            return ConversationStage.INITIAL_CONTACT

        # Analyze recent messages for stage indicators
        recent_messages = conversation_history[-5:]
        combined_text = " ".join(
            msg.get("content", "").lower()
            for msg in recent_messages
            if msg.get("role") == "user"
        ).lower()

        # Stage identification logic
        if lead_score >= 3:
            if any(word in combined_text for word in ["see", "visit", "show", "appointment", "schedule"]):
                return ConversationStage.CLOSING
            elif any(word in combined_text for word in ["compare", "other", "think about", "consider"]):
                return ConversationStage.OBJECTION_HANDLING
            else:
                return ConversationStage.PRESENTING

        elif lead_score >= 2:
            if any(word in combined_text for word in ["not sure", "maybe", "depends", "but"]):
                return ConversationStage.OBJECTION_HANDLING
            else:
                return ConversationStage.QUALIFYING

        elif len(conversation_history) > 4:
            return ConversationStage.NURTURING

        else:
            return ConversationStage.INITIAL_CONTACT

    def _assess_conversation_momentum(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> ConversationMomentum:
        """Assess current conversation momentum."""
        if not conversation_history:
            return ConversationMomentum.LOW

        # Get recent user messages
        user_messages = [
            msg for msg in conversation_history[-6:]
            if msg.get("role") == "user"
        ]

        if not user_messages:
            return ConversationMomentum.STALLED

        # Check timing of last message
        last_message_time = user_messages[-1].get("timestamp")
        if last_message_time:
            try:
                last_time = datetime.fromisoformat(last_message_time.replace("Z", "+00:00"))
                hours_since = (datetime.utcnow() - last_time.replace(tzinfo=None)).total_seconds() / 3600

                if hours_since > 48:
                    return ConversationMomentum.STALLED
            except:
                pass

        # Analyze message content quality
        total_length = sum(len(msg.get("content", "")) for msg in user_messages)
        avg_length = total_length / len(user_messages) if user_messages else 0

        # Check for engagement indicators
        engagement_indicators = 0
        for msg in user_messages:
            content = msg.get("content", "").lower()
            if "?" in content:
                engagement_indicators += 1
            if any(word in content for word in ["when", "how", "what", "where", "tell me"]):
                engagement_indicators += 1
            if any(word in content for word in ["interested", "love", "perfect", "great"]):
                engagement_indicators += 2

        # Determine momentum
        if engagement_indicators >= 4 and avg_length > 30:
            return ConversationMomentum.HIGH
        elif engagement_indicators >= 2 or avg_length > 15:
            return ConversationMomentum.MEDIUM
        else:
            return ConversationMomentum.LOW

    async def _generate_conversation_suggestions(
        self,
        conversation_history: List[Dict[str, Any]],
        extracted_preferences: Dict[str, Any],
        lead_score: int,
        stage: ConversationStage,
        momentum: ConversationMomentum
    ) -> List[ConversationSuggestion]:
        """Generate context-aware conversation suggestions."""
        suggestions = []

        # Stage-specific suggestions
        if stage == ConversationStage.INITIAL_CONTACT:
            suggestions.extend(await self._get_initial_contact_suggestions(
                extracted_preferences, momentum
            ))
        elif stage == ConversationStage.QUALIFYING:
            suggestions.extend(await self._get_qualifying_suggestions(
                extracted_preferences, lead_score
            ))
        elif stage == ConversationStage.PRESENTING:
            suggestions.extend(await self._get_presenting_suggestions(
                extracted_preferences, lead_score
            ))
        elif stage == ConversationStage.CLOSING:
            suggestions.extend(await self._get_closing_suggestions(
                extracted_preferences, momentum
            ))
        elif stage == ConversationStage.NURTURING:
            suggestions.extend(await self._get_nurturing_suggestions(
                conversation_history, extracted_preferences
            ))

        # Momentum-specific adjustments
        if momentum == ConversationMomentum.LOW:
            suggestions = self._adjust_for_low_momentum(suggestions)
        elif momentum == ConversationMomentum.STALLED:
            suggestions = await self._get_reengagement_suggestions(
                conversation_history, extracted_preferences
            )

        return suggestions[:3]  # Top 3 suggestions

    async def _get_initial_contact_suggestions(
        self,
        extracted_preferences: Dict[str, Any],
        momentum: ConversationMomentum
    ) -> List[ConversationSuggestion]:
        """Get suggestions for initial contact stage."""
        suggestions = []

        # Rapport building
        suggestions.append(ConversationSuggestion(
            suggestion_type="rapport_building",
            priority="high",
            message="Thanks for reaching out! I'd love to learn more about what you're looking for. What's prompting your interest in real estate right now?",
            reasoning="Build rapport and understand motivation",
            confidence=0.9,
            timing_recommendation="immediate",
            alternatives=[
                "Hi! What brings you to the market right now?",
                "Great to connect! Tell me about your real estate goals."
            ]
        ))

        # Value proposition
        if momentum != ConversationMomentum.LOW:
            suggestions.append(ConversationSuggestion(
                suggestion_type="value_proposition",
                priority="medium",
                message="I help families find their perfect home in this market. With my local expertise and current inventory knowledge, I can save you time and get you the best deal.",
                reasoning="Establish expertise and value",
                confidence=0.8,
                timing_recommendation="after_rapport",
                alternatives=[
                    "I specialize in this area and know the market inside out.",
                    "Let me put my local expertise to work for you."
                ]
            ))

        return suggestions

    async def _get_qualifying_suggestions(
        self,
        extracted_preferences: Dict[str, Any],
        lead_score: int
    ) -> List[ConversationSuggestion]:
        """Get suggestions for qualifying stage."""
        suggestions = []

        missing_qualifiers = []
        if not extracted_preferences.get("budget"):
            missing_qualifiers.append("budget")
        if not extracted_preferences.get("location"):
            missing_qualifiers.append("location")
        if not extracted_preferences.get("timeline"):
            missing_qualifiers.append("timeline")

        if missing_qualifiers:
            primary_qualifier = missing_qualifiers[0]

            qualifier_questions = {
                "budget": "What price range are you comfortable with?",
                "location": "Which areas are you focusing on?",
                "timeline": "What's your timeline for making a move?"
            }

            suggestions.append(ConversationSuggestion(
                suggestion_type="qualifying_question",
                priority="high",
                message=qualifier_questions[primary_qualifier],
                reasoning=f"Need to gather {primary_qualifier} to improve lead score",
                confidence=0.85,
                timing_recommendation="next_message",
                alternatives=[
                    f"Help me understand your {primary_qualifier} preferences.",
                    f"What are you thinking for {primary_qualifier}?"
                ]
            ))

        return suggestions

    async def _get_presenting_suggestions(
        self,
        extracted_preferences: Dict[str, Any],
        lead_score: int
    ) -> List[ConversationSuggestion]:
        """Get suggestions for presenting stage."""
        suggestions = []

        suggestions.append(ConversationSuggestion(
            suggestion_type="property_presentation",
            priority="high",
            message="Based on what you've told me, I have some properties that would be perfect for you. Would you like me to send over a few options?",
            reasoning="Present relevant properties based on preferences",
            confidence=0.9,
            timing_recommendation="immediate",
            alternatives=[
                "I found some great matches for your criteria. Want to see them?",
                "Perfect! I have properties that fit exactly what you're looking for."
            ]
        ))

        return suggestions

    async def _get_closing_suggestions(
        self,
        extracted_preferences: Dict[str, Any],
        momentum: ConversationMomentum
    ) -> List[ConversationSuggestion]:
        """Get suggestions for closing stage."""
        suggestions = []

        if momentum == ConversationMomentum.HIGH:
            suggestions.append(ConversationSuggestion(
                suggestion_type="appointment_close",
                priority="high",
                message="You seem excited about these properties! When would be a good time for us to see them in person?",
                reasoning="High momentum indicates readiness to schedule",
                confidence=0.95,
                timing_recommendation="immediate",
                alternatives=[
                    "Let's schedule a time to view these together!",
                    "When works best for you to see these properties?"
                ]
            ))
        else:
            suggestions.append(ConversationSuggestion(
                suggestion_type="soft_close",
                priority="medium",
                message="Would it be helpful to set up a quick call to discuss these options?",
                reasoning="Lower momentum requires softer approach",
                confidence=0.7,
                timing_recommendation="after_value_add",
                alternatives=[
                    "Should we hop on a brief call to go over the details?",
                    "Would you like to discuss these over the phone?"
                ]
            ))

        return suggestions

    async def _get_nurturing_suggestions(
        self,
        conversation_history: List[Dict[str, Any]],
        extracted_preferences: Dict[str, Any]
    ) -> List[ConversationSuggestion]:
        """Get suggestions for nurturing stage."""
        suggestions = []

        suggestions.append(ConversationSuggestion(
            suggestion_type="value_add_nurture",
            priority="medium",
            message="I just wanted to share a quick market update that might interest you. Home prices in your area have increased 3% this quarter.",
            reasoning="Provide value without being pushy",
            confidence=0.7,
            timing_recommendation="weekly",
            alternatives=[
                "Here's an interesting market trend I thought you'd want to know about.",
                "Quick update on the market that affects your area."
            ]
        ))

        return suggestions

    async def _get_reengagement_suggestions(
        self,
        conversation_history: List[Dict[str, Any]],
        extracted_preferences: Dict[str, Any]
    ) -> List[ConversationSuggestion]:
        """Get suggestions for re-engaging stalled conversations."""
        suggestions = []

        suggestions.append(ConversationSuggestion(
            suggestion_type="reengagement",
            priority="high",
            message="Hi! Just wanted to check in. Are you still looking in the market, or have your plans changed?",
            reasoning="Direct but friendly reengagement approach",
            confidence=0.6,
            timing_recommendation="immediate",
            alternatives=[
                "Hope you're doing well! Still house hunting?",
                "Quick check-in - how's the home search going?"
            ]
        ))

        return suggestions

    async def _prepare_objection_responses(
        self,
        conversation_history: List[Dict[str, Any]],
        extracted_preferences: Dict[str, Any],
        conversation_stage: ConversationStage
    ) -> List[ObjectionResponse]:
        """Prepare responses for likely objections."""
        objection_responses = []

        # Identify potential objections based on conversation patterns
        if extracted_preferences.get("budget"):
            objection_responses.append(ObjectionResponse(
                objection_type=ObjectionType.PRICE,
                response_script="I understand price is important. Let me show you the value comparison with similar properties and help you understand the investment perspective.",
                follow_up_questions=[
                    "What specific aspect of the pricing concerns you most?",
                    "Would it help to look at the price per square foot compared to the neighborhood?",
                    "Are there particular costs you'd like me to explain?"
                ],
                alternative_approaches=[
                    "Focus on long-term value and appreciation",
                    "Compare with rental costs over time",
                    "Highlight unique features that justify price"
                ],
                success_probability=0.75,
                coaching_notes="Price objections often mask budget concerns. Dig deeper to understand the real issue."
            ))

        # Authority objection preparation
        objection_responses.append(ObjectionResponse(
            objection_type=ObjectionType.AUTHORITY,
            response_script="Of course! Major decisions like this should involve everyone. Would it be helpful to schedule a time when you can both be present?",
            follow_up_questions=[
                "When would be a good time for both of you?",
                "What information would help them make the decision?",
                "Are there specific concerns they have?"
            ],
            alternative_approaches=[
                "Offer to provide information packet for discussion",
                "Schedule three-way conversation",
                "Address specific spousal concerns"
            ],
            success_probability=0.85,
            coaching_notes="Authority objections are often legitimate. Embrace the additional decision maker."
        ))

        return objection_responses

    async def _generate_performance_insights(
        self,
        contact_id: str,
        conversation_history: List[Dict[str, Any]],
        lead_score: int,
        conversation_stage: ConversationStage
    ) -> List[PerformanceInsight]:
        """Generate performance coaching insights."""
        insights = []

        # Response time analysis
        if len(conversation_history) >= 4:
            response_times = self._calculate_response_times(conversation_history)
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            if avg_response_time > 60:  # More than 1 hour average
                insights.append(PerformanceInsight(
                    area="response_time",
                    current_performance={"avg_response_minutes": avg_response_time},
                    benchmark={"target_response_minutes": 15},
                    improvement_suggestion="Aim to respond within 15 minutes during business hours for better engagement",
                    impact_level="high",
                    implementation_difficulty="medium"
                ))

        # Question-to-statement ratio
        agent_messages = [msg for msg in conversation_history if msg.get("role") == "assistant"]
        if agent_messages:
            questions_asked = sum(msg.get("content", "").count("?") for msg in agent_messages)
            total_messages = len(agent_messages)
            question_ratio = questions_asked / total_messages if total_messages > 0 else 0

            if question_ratio < 0.5:  # Less than 50% questions
                insights.append(PerformanceInsight(
                    area="questioning_technique",
                    current_performance={"question_ratio": question_ratio},
                    benchmark={"target_question_ratio": 0.7},
                    improvement_suggestion="Ask more open-ended questions to engage prospects and gather information",
                    impact_level="high",
                    implementation_difficulty="low"
                ))

        return insights

    async def _develop_progression_strategy(
        self,
        extracted_preferences: Dict[str, Any],
        lead_score: int,
        conversation_stage: ConversationStage,
        momentum: ConversationMomentum,
        behavioral_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Develop lead progression strategy."""
        strategy = {
            "current_stage": conversation_stage.value,
            "current_momentum": momentum.value,
            "lead_score": lead_score,
            "progression_plan": []
        }

        # Define progression steps based on current state
        if lead_score < 2:
            strategy["progression_plan"] = [
                "Build rapport and trust",
                "Gather qualifying information",
                "Provide value through market insights",
                "Schedule appointment when qualified"
            ]
        elif lead_score < 3:
            strategy["progression_plan"] = [
                "Present relevant properties",
                "Address any concerns or objections",
                "Create urgency through market conditions",
                "Schedule viewing appointment"
            ]
        else:
            strategy["progression_plan"] = [
                "Schedule property viewing immediately",
                "Prepare offer strategy",
                "Handle final objections",
                "Close the deal"
            ]

        # Add momentum-specific adjustments
        if momentum == ConversationMomentum.LOW:
            strategy["progression_plan"].insert(0, "Re-engage and rebuild momentum")
        elif momentum == ConversationMomentum.STALLED:
            strategy["progression_plan"] = [
                "Reactivate conversation",
                "Provide new value proposition",
                "Reassess needs and timeline"
            ]

        return strategy

    def _determine_next_best_actions(
        self,
        conversation_stage: ConversationStage,
        momentum: ConversationMomentum,
        lead_score: int,
        extracted_preferences: Dict[str, Any]
    ) -> List[str]:
        """Determine next best actions for the agent."""
        actions = []

        # Stage-specific actions
        if conversation_stage == ConversationStage.INITIAL_CONTACT:
            actions.extend([
                "Establish rapport and build trust",
                "Ask about their real estate motivation",
                "Gather basic qualifying information"
            ])
        elif conversation_stage == ConversationStage.QUALIFYING:
            missing_info = []
            if not extracted_preferences.get("budget"):
                missing_info.append("budget")
            if not extracted_preferences.get("location"):
                missing_info.append("location")
            if not extracted_preferences.get("timeline"):
                missing_info.append("timeline")

            if missing_info:
                actions.append(f"Gather {', '.join(missing_info)} information")

        elif conversation_stage == ConversationStage.PRESENTING:
            actions.extend([
                "Send relevant property matches",
                "Highlight properties that meet their criteria",
                "Ask for feedback on presented options"
            ])

        elif conversation_stage == ConversationStage.CLOSING:
            actions.extend([
                "Schedule property viewing appointment",
                "Prepare showing materials",
                "Follow up within 2 hours of scheduling"
            ])

        # Priority adjustments based on momentum
        if momentum == ConversationMomentum.HIGH:
            actions.insert(0, "PRIORITY: Strike while momentum is high")
        elif momentum == ConversationMomentum.STALLED:
            actions = ["Reactivate conversation with value-add message"] + actions

        return actions[:4]  # Top 4 actions

    def _calculate_response_times(self, conversation_history: List[Dict[str, Any]]) -> List[float]:
        """Calculate response times between messages."""
        response_times = []

        for i in range(1, len(conversation_history)):
            prev_msg = conversation_history[i-1]
            curr_msg = conversation_history[i]

            # Only calculate when agent responds to user
            if (prev_msg.get("role") == "user" and
                curr_msg.get("role") == "assistant"):

                prev_time = prev_msg.get("timestamp")
                curr_time = curr_msg.get("timestamp")

                if prev_time and curr_time:
                    try:
                        prev_dt = datetime.fromisoformat(prev_time.replace("Z", "+00:00"))
                        curr_dt = datetime.fromisoformat(curr_time.replace("Z", "+00:00"))

                        diff_minutes = (curr_dt - prev_dt).total_seconds() / 60
                        response_times.append(diff_minutes)
                    except:
                        continue

        return response_times

    def _adjust_for_low_momentum(
        self,
        suggestions: List[ConversationSuggestion]
    ) -> List[ConversationSuggestion]:
        """Adjust suggestions for low momentum conversations."""
        adjusted = []

        for suggestion in suggestions:
            # Make messages more engaging and value-focused
            if suggestion.suggestion_type == "qualifying_question":
                suggestion.message = f"I'd love to help you find the perfect property. {suggestion.message}"
                suggestion.reasoning += " (Adjusted for low engagement)"

            adjusted.append(suggestion)

        return adjusted

    def _calculate_confidence_score(
        self,
        conversation_suggestions: List[ConversationSuggestion],
        momentum: ConversationMomentum,
        lead_score: int
    ) -> float:
        """Calculate overall confidence in suggestions."""
        base_confidence = 0.7

        # Adjust based on momentum
        momentum_adjustments = {
            ConversationMomentum.HIGH: 0.2,
            ConversationMomentum.MEDIUM: 0.1,
            ConversationMomentum.LOW: -0.1,
            ConversationMomentum.STALLED: -0.2
        }

        base_confidence += momentum_adjustments.get(momentum, 0)

        # Adjust based on lead score
        if lead_score >= 3:
            base_confidence += 0.15
        elif lead_score >= 2:
            base_confidence += 0.05
        else:
            base_confidence -= 0.05

        # Factor in suggestion confidence
        if conversation_suggestions:
            avg_suggestion_confidence = sum(s.confidence for s in conversation_suggestions) / len(conversation_suggestions)
            base_confidence = (base_confidence + avg_suggestion_confidence) / 2

        return max(0.0, min(1.0, base_confidence))

    async def _fallback_agent_guidance(self) -> AgentGuidance:
        """Generate fallback guidance when main process fails."""
        fallback_suggestions = [
            ConversationSuggestion(
                suggestion_type="general",
                priority="medium",
                message="How can I help you with your real estate needs today?",
                reasoning="Fallback general engagement",
                confidence=0.5,
                timing_recommendation="immediate",
                alternatives=["What questions do you have about the market?"]
            )
        ]

        return AgentGuidance(
            conversation_suggestions=fallback_suggestions,
            objection_responses=[],
            performance_insights=[],
            lead_progression_strategy={"status": "fallback_mode"},
            next_best_actions=["Engage in conversation", "Gather basic information"],
            conversation_momentum=ConversationMomentum.MEDIUM,
            confidence_score=0.5
        )

    async def track_conversation_outcome(
        self,
        contact_id: str,
        guidance_used: AgentGuidance,
        actual_response: str,
        outcome_metrics: Dict[str, Any]
    ) -> None:
        """
        Track conversation outcomes to improve future suggestions.

        Args:
            contact_id: Contact identifier
            guidance_used: The guidance that was provided
            actual_response: What the agent actually said
            outcome_metrics: Metrics about the outcome (engagement, progression, etc.)
        """
        # In production, this would update ML models and improve suggestions
        performance_key = f"{self.tenant_id}:{contact_id}"

        if performance_key not in self.performance_data:
            self.performance_data[performance_key] = []

        self.performance_data[performance_key].append({
            "timestamp": datetime.utcnow(),
            "guidance_confidence": guidance_used.confidence_score,
            "outcome_metrics": outcome_metrics,
            "actual_response_length": len(actual_response),
            "suggestions_count": len(guidance_used.conversation_suggestions)
        })

        logger.info(
            f"Tracked conversation outcome for {contact_id}",
            extra={
                "confidence": guidance_used.confidence_score,
                "outcome": outcome_metrics
            }
        )

    async def get_agent_performance_summary(
        self,
        agent_id: str,
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """
        Get performance summary for an agent.

        Args:
            agent_id: Agent identifier
            date_range: Date range for analysis

        Returns:
            Performance summary with metrics and insights
        """
        # In production, this would analyze real performance data
        return {
            "agent_id": agent_id,
            "date_range": date_range,
            "conversations_assisted": 25,
            "average_response_time_minutes": 18,
            "lead_progression_rate": 0.68,
            "appointment_scheduling_rate": 0.35,
            "top_performing_strategies": [
                "Rapport building in initial contact",
                "Value-add nurturing messages",
                "Direct appointment closing"
            ],
            "improvement_opportunities": [
                "Faster response times during peak hours",
                "More qualifying questions in early stage",
                "Better objection handling for price concerns"
            ]
        }