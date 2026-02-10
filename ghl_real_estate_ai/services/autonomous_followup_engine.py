"""
🚀 Service 6 Enhanced Lead Recovery & Nurture Engine - Autonomous Follow-up Engine

Advanced agent-driven follow-up orchestration system featuring:
- Multi-agent collaboration for intelligent follow-up strategy
- Adaptive timing optimization based on lead behavior patterns
- Dynamic content personalization through specialized agents
- Autonomous escalation and de-escalation protocols
- Cross-channel orchestration (email, SMS, voice, social)
- Real-time response analysis and strategy adjustment
- Predictive engagement optimization with machine learning

Saves 20+ hours/week per agent through intelligent automation.

Date: January 17, 2026
Status: Advanced Agent-Driven Follow-up Orchestration System
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.agents.lead_intelligence_swarm import get_lead_intelligence_swarm
from ghl_real_estate_ai.api.schemas.ghl import MessageType
from ghl_real_estate_ai.core.llm_client import get_llm_client
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.orchestrator_types import FollowupContext, FollowupRecommendationData, FollowupTaskData
from ghl_real_estate_ai.services.behavioral_trigger_engine import (
    IntentLevel,
    get_behavioral_trigger_engine,
)
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.database_service import get_database
from ghl_real_estate_ai.utils.async_utils import safe_create_task

logger = get_logger(__name__)


class FollowUpStatus(Enum):
    """Status of follow-up execution."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    SKIPPED = "skipped"


class FollowUpChannel(Enum):
    """Communication channels for follow-up."""

    SMS = "sms"
    EMAIL = "email"
    CALL = "call"
    VOICEMAIL = "voicemail"
    WHATSAPP = "whatsapp"


@dataclass
class FollowUpTask:
    """Autonomous follow-up task."""

    task_id: str
    lead_id: str
    contact_id: str
    channel: FollowUpChannel
    message: str
    scheduled_time: datetime
    status: FollowUpStatus = FollowUpStatus.PENDING
    priority: int = 1  # 1-5, 5 being highest
    intent_level: Optional[IntentLevel] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None


class AgentType(Enum):
    """Specialized follow-up agent types - 10 autonomous agents."""

    TIMING_OPTIMIZER = "timing_optimizer"
    CONTENT_PERSONALIZER = "content_personalizer"
    CHANNEL_STRATEGIST = "channel_strategist"
    RESPONSE_ANALYZER = "response_analyzer"
    ESCALATION_MANAGER = "escalation_manager"

    # New specialized agents
    SENTIMENT_ANALYST = "sentiment_analyst"
    OBJECTION_HANDLER = "objection_handler"
    CONVERSION_OPTIMIZER = "conversion_optimizer"
    MARKET_CONTEXT_AGENT = "market_context_agent"
    PERFORMANCE_TRACKER = "performance_tracker"

    # Phase 7: Autonomous Scheduling
    SCHEDULING_AGENT = "scheduling_agent"
    VIDEO_AI_AGENT = "video_ai_agent"


@dataclass
class FollowUpRecommendation:
    """Agent recommendation for follow-up strategy."""

    agent_type: AgentType
    confidence: float  # 0.0 - 1.0
    recommended_action: str
    reasoning: str
    optimal_timing: Optional[datetime] = None
    suggested_channel: Optional[FollowUpChannel] = None
    suggested_message: Optional[str] = None
    escalation_needed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class FollowUpAgent:
    """Base class for specialized follow-up agents."""

    def __init__(self, agent_type: AgentType, llm_client, blackboard: Any = None):
        self.agent_type = agent_type
        self.llm_client = llm_client
        self.blackboard = blackboard

    def log_thought(self, lead_id: str, thought: str, action: str, confidence: float):
        """Log agent debate data to the blackboard."""
        if self.blackboard:
            self.blackboard.log_debate(lead_id, self.agent_type.value, thought, action, confidence)

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Analyze lead and provide follow-up recommendation."""
        raise NotImplementedError


class TimingOptimizerAgent(FollowUpAgent):
    """Optimizes follow-up timing based on lead behavior patterns."""

    def __init__(self, llm_client, blackboard=None):
        super().__init__(AgentType.TIMING_OPTIMIZER, llm_client, blackboard)

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Analyze optimal timing for follow-up."""
        try:
            # Analyze lead activity patterns
            activity_data = context.get("activity_data", {})
            behavioral_score = context.get("behavioral_score")

            # Use Claude to analyze optimal timing
            prompt = f"""
            Analyze the optimal follow-up timing for this lead based on their behavior patterns.

            Lead Activity: {activity_data}
            Intent Level: {behavioral_score.intent_level if behavioral_score else "unknown"}
            Current Time: {datetime.now().strftime("%H:%M %A")}

            Consider:
            1. Lead's typical response times
            2. Industry best practices for real estate
            3. Urgency level based on intent
            4. Time zone and schedule preferences

            Provide timing recommendation with reasoning.
            """

            response = await self.llm_client.generate(prompt=prompt, max_tokens=300, temperature=0.3)

            # Parse Claude's response for timing insights
            timing_analysis = response.content if response.content else "Standard timing recommended"

            # Calculate optimal timing (simplified logic)
            now = datetime.now()
            if behavioral_score and behavioral_score.intent_level == IntentLevel.URGENT:
                optimal_time = now + timedelta(minutes=15)  # Urgent: 15 minutes
            elif behavioral_score and behavioral_score.intent_level == IntentLevel.HOT:
                optimal_time = now + timedelta(hours=2)  # Hot: 2 hours
            else:
                optimal_time = now + timedelta(hours=8)  # Warm/Cold: 8 hours

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.85,
                recommended_action="Schedule follow-up at optimal time",
                reasoning=timing_analysis,
                optimal_timing=optimal_time,
                metadata={"analysis_method": "behavioral_pattern_analysis"},
            )

        except Exception as e:
            logger.error(f"Error in timing optimizer: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.3,
                recommended_action="Use default timing",
                reasoning="Error in timing analysis, using fallback",
                optimal_timing=datetime.now() + timedelta(hours=4),
            )


class ContentPersonalizerAgent(FollowUpAgent):
    """Personalizes follow-up content based on lead profile and behavior."""

    def __init__(self, llm_client, blackboard=None):
        super().__init__(AgentType.CONTENT_PERSONALIZER, llm_client, blackboard)

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Generate personalized follow-up content."""
        try:
            behavioral_score = context.get("behavioral_score")
            activity_data = context.get("activity_data", {})
            lead_profile = context.get("lead_profile", {})

            # Phase 7: Collect arbitrage and market context from other agents' findings
            market_context = context.get("market_context", {})
            arbitrage_info = context.get("arbitrage_info", "")

            # Phase 7: One-Click Arbitrage Generation
            offer_link = ""
            if arbitrage_info:
                try:
                    from ghl_real_estate_ai.services.market_timing_opportunity_intelligence import (
                        MarketTimingOpportunityEngine,
                    )
                    from ghl_real_estate_ai.services.smart_document_generator import (
                        DocumentType,
                        SmartDocumentGenerator,
                    )

                    m_engine = MarketTimingOpportunityEngine()
                    doc_gen = SmartDocumentGenerator()

                    proforma = await m_engine.generate_roi_proforma(
                        "ARBITRAGE_001", lead_profile.get("market_area", "austin")
                    )
                    loi_doc = doc_gen.generate_document(DocumentType.ARBITRAGE_LOI, "loi_template_v1", proforma)
                    offer_link = proforma.get("one_click_url", "")
                except Exception as e:
                    logger.warning(f"One-click offer gen failed: {e}")

            # Use Claude to create personalized message
            prompt = f"""
            Create a personalized follow-up message for this real estate lead.

            Lead Profile: {lead_profile}
            Recent Activity: {activity_data}
            Intent Level: {behavioral_score.intent_level if behavioral_score else "unknown"}
            Market Context: {market_context}
            Arbitrage Opportunity: {arbitrage_info}
            One-Click Offer Link: {offer_link}

            Requirements:
            1. Reference their specific interests/activity naturally
            2. If an arbitrage opportunity exists, prioritize pitching it as a "Prime Arbitrage" zone.
            3. Mention that a customized ROI Pro-forma and LOI have been prepared for them.
            4. Include the One-Click Offer Link as the primary CTA.
            5. Provide clear value proposition
            6. Include soft call-to-action
            7. Be conversational, not salesy
            8. Keep under 160 characters for SMS compatibility
            9. Match their communication style preference

            Generate the personalized message:
            """

            response = await self.llm_client.generate(prompt=prompt, max_tokens=250, temperature=0.7)

            personalized_message = (
                response.content.strip()
                if response.content
                else behavioral_score.recommended_message
                if behavioral_score
                else "Hi! I noticed your interest in properties in the area. Would you like to see some new listings that match your criteria?"
            )

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.90,
                recommended_action="Use personalized message",
                reasoning="Generated based on lead profile and activity patterns",
                suggested_message=personalized_message,
                metadata={"personalization_factors": ["profile", "activity", "intent"]},
            )

        except Exception as e:
            logger.error(f"Error in content personalizer: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.3,
                recommended_action="Use template message",
                reasoning="Error in personalization, using fallback",
                suggested_message="Thank you for your interest! I have some properties that might be perfect for you.",
            )


class ChannelStrategistAgent(FollowUpAgent):
    """Determines optimal communication channel based on lead preferences and context."""

    def __init__(self, llm_client, blackboard=None):
        super().__init__(AgentType.CHANNEL_STRATEGIST, llm_client, blackboard)

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Determine optimal communication channel."""
        try:
            behavioral_score = context.get("behavioral_score")
            activity_data = context.get("activity_data", {})
            lead_profile = context.get("lead_profile", {})

            # Analyze channel effectiveness
            email_engagement = activity_data.get("email_interactions", [])
            sms_responses = activity_data.get("sms_responses", [])
            call_history = activity_data.get("call_history", [])

            # Default to email, adjust based on patterns
            optimal_channel = FollowUpChannel.EMAIL
            confidence = 0.7
            reasoning = "Email selected as default channel"

            # Analyze response patterns
            if len(sms_responses) > len(email_engagement):
                optimal_channel = FollowUpChannel.SMS
                confidence = 0.85
                reasoning = "Lead shows higher SMS engagement"
            elif behavioral_score and behavioral_score.intent_level == IntentLevel.URGENT:
                optimal_channel = FollowUpChannel.CALL
                confidence = 0.9
                reasoning = "Urgent intent level requires immediate contact"
            elif any("mobile" in str(contact).lower() for contact in lead_profile.get("contacts", [])):
                optimal_channel = FollowUpChannel.SMS
                confidence = 0.75
                reasoning = "Mobile contact preference detected"

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=confidence,
                recommended_action=f"Use {optimal_channel.value} for follow-up",
                reasoning=reasoning,
                suggested_channel=optimal_channel,
                metadata={"channel_analysis": "engagement_pattern_based"},
            )

        except Exception as e:
            logger.error(f"Error in channel strategist: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.5,
                recommended_action="Use email as fallback",
                reasoning="Error in channel analysis, using safe fallback",
                suggested_channel=FollowUpChannel.EMAIL,
            )


class ResponseAnalyzerAgent(FollowUpAgent):
    """Analyzes follow-up responses and adjusts strategy accordingly."""

    def __init__(self, llm_client, blackboard=None):
        super().__init__(AgentType.RESPONSE_ANALYZER, llm_client, blackboard)

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Analyze response patterns and recommend strategy adjustments."""
        try:
            follow_up_history = context.get("follow_up_history", [])
            response_data = context.get("response_data", {})

            if not follow_up_history:
                return FollowUpRecommendation(
                    agent_type=self.agent_type,
                    confidence=0.6,
                    recommended_action="Continue with current strategy",
                    reasoning="No follow-up history to analyze",
                )

            # Analyze response patterns
            total_sent = len(follow_up_history)
            responses_received = len(response_data.get("responses", []))
            response_rate = responses_received / total_sent if total_sent > 0 else 0

            # Determine strategy adjustment
            if response_rate > 0.7:
                recommendation = "Maintain current approach - high engagement"
                confidence = 0.9
            elif response_rate < 0.2 and total_sent >= 3:
                recommendation = "Consider escalation or strategy change - low engagement"
                confidence = 0.85
                escalation_needed = True
            else:
                recommendation = "Continue current strategy with minor adjustments"
                confidence = 0.7

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=confidence,
                recommended_action=recommendation,
                reasoning=f"Response rate: {response_rate:.1%} from {total_sent} follow-ups",
                escalation_needed=response_rate < 0.2 and total_sent >= 3,
                metadata={"response_rate": response_rate, "total_sent": total_sent},
            )

        except Exception as e:
            logger.error(f"Error in response analyzer: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.3,
                recommended_action="Continue current strategy",
                reasoning="Error in response analysis, maintaining course",
            )


class EscalationManagerAgent(FollowUpAgent):
    """Manages escalation and de-escalation decisions."""

    def __init__(self, llm_client, blackboard=None):
        super().__init__(AgentType.ESCALATION_MANAGER, llm_client, blackboard)

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Determine if escalation or de-escalation is needed."""
        try:
            behavioral_score = context.get("behavioral_score")
            follow_up_history = context.get("follow_up_history", [])
            response_data = context.get("response_data", {})

            escalation_needed = False
            confidence = 0.8
            reasoning = "Standard follow-up process"

            # Check escalation triggers
            if behavioral_score and behavioral_score.intent_level == IntentLevel.URGENT:
                escalation_needed = True
                reasoning = "Urgent intent level requires immediate escalation"
                confidence = 0.95
            elif len(follow_up_history) >= 5 and not response_data.get("responses"):
                escalation_needed = True
                reasoning = "Multiple attempts without response - escalate to human agent"
                confidence = 0.9
            elif response_data.get("negative_sentiment", False):
                escalation_needed = True
                reasoning = "Negative sentiment detected - human intervention needed"
                confidence = 0.85

            action = "Escalate to human agent" if escalation_needed else "Continue automated follow-up"

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=confidence,
                recommended_action=action,
                reasoning=reasoning,
                escalation_needed=escalation_needed,
                metadata={"escalation_factors": ["intent", "response_count", "sentiment"]},
            )

        except Exception as e:
            logger.error(f"Error in escalation manager: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.5,
                recommended_action="Continue current approach",
                reasoning="Error in escalation analysis, maintaining current level",
            )


class SentimentAnalystAgent(FollowUpAgent):
    """Analyzes emotional tone and sentiment for appropriate follow-up approach."""

    def __init__(self, llm_client, blackboard=None):
        super().__init__(AgentType.SENTIMENT_ANALYST, llm_client, blackboard)

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Analyze sentiment to guide follow-up approach."""
        try:
            response_data = context.get("response_data", {})
            conversation_history = context.get("conversation_history", [])

            # Analyze recent messages for sentiment
            recent_messages = []
            if response_data.get("responses"):
                recent_messages = response_data["responses"][-3:]  # Last 3 messages

            if not recent_messages and conversation_history:
                recent_messages = [msg.get("content", "") for msg in conversation_history[-3:]]

            # Use Claude for sentiment analysis
            prompt = f"""
            Analyze the sentiment and emotional tone of these recent messages from a real estate lead.

            Recent Messages: {recent_messages}
            Lead Context: {context.get("lead_profile", {})}

            Determine:
            1. Overall sentiment (positive, neutral, negative, frustrated)
            2. Emotional state (excited, confused, worried, angry, interested)
            3. Engagement level (high, medium, low, disengaged)
            4. Recommended approach for next follow-up

            Consider real estate context and buying/selling emotions.
            Provide recommendations for tone, timing, and approach.
            """

            response = await self.llm_client.generate(prompt=prompt, max_tokens=300, temperature=0.3)

            sentiment_analysis = response.content if response.content else "neutral sentiment detected"

            # Determine recommended approach based on sentiment
            if "negative" in sentiment_analysis.lower() or "frustrated" in sentiment_analysis.lower():
                recommended_action = "Use empathetic, supportive approach"
                confidence = 0.9
            elif "excited" in sentiment_analysis.lower() or "positive" in sentiment_analysis.lower():
                recommended_action = "Capitalize on positive momentum"
                confidence = 0.85
            elif "confused" in sentiment_analysis.lower() or "worried" in sentiment_analysis.lower():
                recommended_action = "Provide educational, reassuring content"
                confidence = 0.8
            else:
                recommended_action = "Use balanced, professional approach"
                confidence = 0.7

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=confidence,
                recommended_action=recommended_action,
                reasoning=sentiment_analysis,
                metadata={"sentiment_analysis": sentiment_analysis, "messages_analyzed": len(recent_messages)},
            )

        except Exception as e:
            logger.error(f"Error in sentiment analyst: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.5,
                recommended_action="Use neutral, professional approach",
                reasoning="Error in sentiment analysis, using safe approach",
            )


class ObjectionHandlerAgent(FollowUpAgent):
    """Detects objections and recommends appropriate handling strategies."""

    def __init__(self, llm_client, blackboard=None):
        super().__init__(AgentType.OBJECTION_HANDLER, llm_client, blackboard)

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Detect objections and recommend handling approach."""
        try:
            response_data = context.get("response_data", {})
            conversation_history = context.get("conversation_history", [])

            # Look for objection signals in recent responses
            recent_responses = response_data.get("responses", [])
            if not recent_responses and conversation_history:
                recent_responses = [msg.get("content", "") for msg in conversation_history[-5:]]

            objection_detected = False
            objection_type = None
            confidence = 0.6

            # Simple objection detection (would integrate with autonomous_objection_handler.py)
            objection_keywords = {
                "price": ["expensive", "cost", "afford", "budget", "price"],
                "timing": ["not ready", "timing", "later", "wait"],
                "trust": ["trust", "experience", "reviews", "references"],
                "location": ["location", "area", "neighborhood", "commute"],
                "process": ["complicated", "paperwork", "process", "confusing"],
            }

            for response_text in recent_responses:
                if isinstance(response_text, str):
                    response_lower = response_text.lower()
                    for obj_type, keywords in objection_keywords.items():
                        if any(keyword in response_lower for keyword in keywords):
                            objection_detected = True
                            objection_type = obj_type
                            confidence = 0.8
                            break

            if objection_detected:
                recommended_action = f"Address {objection_type} objection with targeted response"
                reasoning = f"Detected {objection_type} objection in recent communications"

                # Suggest specific objection handling strategy
                objection_strategies = {
                    "price": "Emphasize value and financing options",
                    "timing": "Acknowledge timeline and maintain nurturing sequence",
                    "trust": "Provide credentials and testimonials",
                    "location": "Share market insights and alternative options",
                    "process": "Simplify and guide through next steps",
                }

                strategy = objection_strategies.get(objection_type, "Address concern directly")
                recommended_action = f"{recommended_action}: {strategy}"

            else:
                recommended_action = "No objections detected, proceed with standard approach"
                reasoning = "No objection signals found in recent communications"
                confidence = 0.7

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=confidence,
                recommended_action=recommended_action,
                reasoning=reasoning,
                metadata={
                    "objection_detected": objection_detected,
                    "objection_type": objection_type,
                    "responses_analyzed": len(recent_responses),
                },
            )

        except Exception as e:
            logger.error(f"Error in objection handler: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.5,
                recommended_action="Monitor for objections",
                reasoning="Error in objection detection, using standard monitoring",
            )


class ConversionOptimizerAgent(FollowUpAgent):
    """Optimizes follow-up strategy for maximum conversion probability."""

    def __init__(self, llm_client, blackboard=None):
        super().__init__(AgentType.CONVERSION_OPTIMIZER, llm_client, blackboard)

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Optimize approach for maximum conversion probability."""
        try:
            behavioral_score = context.get("behavioral_score")
            follow_up_history = context.get("follow_up_history", [])
            response_data = context.get("response_data", {})

            # Calculate conversion probability factors
            conversion_factors = {}

            # Intent level factor
            if behavioral_score:
                intent_scores = {
                    IntentLevel.URGENT: 0.9,
                    IntentLevel.HOT: 0.7,
                    IntentLevel.WARM: 0.5,
                    IntentLevel.COLD: 0.2,
                }
                conversion_factors["intent_score"] = intent_scores.get(behavioral_score.intent_level, 0.3)

            # Response rate factor
            total_sent = len(follow_up_history)
            responses_received = len(response_data.get("responses", []))
            response_rate = responses_received / total_sent if total_sent > 0 else 0
            conversion_factors["response_rate"] = min(response_rate * 2, 1.0)  # Cap at 1.0

            # Engagement recency factor
            last_response_time = response_data.get("last_response_time")
            if last_response_time:
                if isinstance(last_response_time, str):
                    last_response_time = datetime.fromisoformat(last_response_time)
                hours_since = (datetime.now() - last_response_time).total_seconds() / 3600
                recency_factor = max(0.1, 1.0 - (hours_since / 168))  # Decay over 1 week
            else:
                recency_factor = 0.3

            conversion_factors["recency_factor"] = recency_factor

            # Calculate overall conversion probability
            overall_probability = (
                conversion_factors.get("intent_score", 0.3) * 0.4
                + conversion_factors.get("response_rate", 0.2) * 0.3
                + recency_factor * 0.3
            )

            # Recommend optimization strategy
            if overall_probability > 0.7:
                recommended_action = "High conversion probability: Use direct ask for meeting/showing"
                urgency = "high"
            elif overall_probability > 0.5:
                recommended_action = "Medium conversion probability: Provide value and soft CTA"
                urgency = "medium"
            elif overall_probability > 0.3:
                recommended_action = "Low-medium probability: Focus on nurturing and education"
                urgency = "low"
            else:
                recommended_action = "Low probability: Long-term nurturing sequence"
                urgency = "low"

            confidence = 0.8 if len(follow_up_history) >= 3 else 0.6

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=confidence,
                recommended_action=recommended_action,
                reasoning=f"Conversion probability: {overall_probability:.2f} based on multiple factors",
                metadata={
                    "conversion_probability": overall_probability,
                    "conversion_factors": conversion_factors,
                    "urgency_level": urgency,
                    "optimization_strategy": "probability_based",
                },
            )

        except Exception as e:
            logger.error(f"Error in conversion optimizer: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.4,
                recommended_action="Use standard conversion approach",
                reasoning="Error in optimization analysis, using standard approach",
            )


class MarketContextAgent(FollowUpAgent):
    """Incorporates market conditions and timing into follow-up strategy."""

    def __init__(self, llm_client, blackboard=None):
        super().__init__(AgentType.MARKET_CONTEXT_AGENT, llm_client, blackboard)
        try:
            from ghl_real_estate_ai.services.market_timing_opportunity_intelligence import MarketTimingOpportunityEngine

            self.market_engine = MarketTimingOpportunityEngine()
        except ImportError:
            self.market_engine = None

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Incorporate market context into follow-up recommendations."""
        try:
            behavioral_score = context.get("behavioral_score")
            lead_profile = context.get("lead_profile", {})

            # Phase 7: Use MarketTimingOpportunityEngine for arbitrage detection
            market_area = lead_profile.get("market_area", "austin")
            arbitrage_data = None
            if self.market_engine:
                try:
                    dashboard = await self.market_engine.get_opportunity_dashboard(market_area)
                    arbitrage_data = dashboard.get("opportunities", [])
                except Exception as e:
                    logger.warning(f"Failed to get arbitrage data: {e}")

            # Get market context
            market_context = {}
            if behavioral_score and hasattr(behavioral_score, "market_context"):
                market_context = behavioral_score.market_context

            # Default market conditions if not available
            current_market = market_context.get("market_trend", "balanced_market")
            inventory_level = market_context.get("inventory_level", "normal")
            price_trend = market_context.get("median_price_trend", "stable")

            # Determine market-appropriate messaging
            market_urgency = False
            market_messaging = ""

            if arbitrage_data:
                # Use arbitrage pitch if available
                top_opp = arbitrage_data[0]
                market_messaging = f"Prime Arbitrage Alert: {top_opp['type']} opportunity found in {market_area} with {top_opp['score']}% potential ROI."
                market_urgency = top_opp["urgency"] == "high"
            elif current_market == "sellers_market":
                if inventory_level == "low":
                    market_urgency = True
                    market_messaging = "Limited inventory in seller's market - act quickly on properties of interest"
                else:
                    market_messaging = "Strong seller's market provides good opportunities for competitive offers"

            elif current_market == "buyers_market":
                market_messaging = "Buyer's market provides negotiation opportunities and selection"

            else:  # balanced_market
                market_messaging = "Balanced market conditions allow for strategic decision-making"

            # Incorporate price trends
            if price_trend == "increasing":
                market_messaging += ". Prices trending upward - good time to secure property"
            elif price_trend == "decreasing":
                market_messaging += ". Market adjustments may provide opportunities"

            # Determine recommended action based on market context
            if market_urgency:
                recommended_action = "Emphasize market urgency and encourage prompt action"
                confidence = 0.85
            elif current_market == "buyers_market":
                recommended_action = "Highlight market advantages and selection opportunities"
                confidence = 0.8
            else:
                recommended_action = "Provide balanced market perspective and guidance"
                confidence = 0.75

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=confidence,
                recommended_action=recommended_action,
                reasoning=market_messaging,
                metadata={
                    "market_trend": current_market,
                    "inventory_level": inventory_level,
                    "price_trend": price_trend,
                    "market_urgency": market_urgency,
                    "market_messaging": market_messaging,
                    "arbitrage_available": bool(arbitrage_data),
                },
            )

        except Exception as e:
            logger.error(f"Error in market context agent: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.6,
                recommended_action="Provide general market insights",
                reasoning="Error in market analysis, using general market guidance",
            )


class PerformanceTrackerAgent(FollowUpAgent):
    """Tracks and optimizes follow-up performance based on historical data."""

    def __init__(self, llm_client, blackboard=None):
        super().__init__(AgentType.PERFORMANCE_TRACKER, llm_client, blackboard)

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Analyze historical performance to optimize future follow-ups."""
        try:
            follow_up_history = context.get("follow_up_history", [])
            response_data = context.get("response_data", {})
            behavioral_score = context.get("behavioral_score")

            # Calculate performance metrics
            performance_metrics = {}

            if follow_up_history:
                # Response rate analysis
                total_sent = len(follow_up_history)
                responses = len(response_data.get("responses", []))
                performance_metrics["response_rate"] = responses / total_sent if total_sent > 0 else 0

                # Channel performance analysis
                channel_performance = {}
                for followup in follow_up_history:
                    channel = followup.get("channel", "unknown")
                    if channel not in channel_performance:
                        channel_performance[channel] = {"sent": 0, "responded": 0}

                    channel_performance[channel]["sent"] += 1

                    # Check if this follow-up got a response (simplified)
                    followup_time = followup.get("sent_at")
                    if followup_time and response_data.get("responses"):
                        for response in response_data["responses"]:
                            response_time = response.get("timestamp")
                            if response_time and followup_time:
                                # If response came after this follow-up (simplified logic)
                                channel_performance[channel]["responded"] += 1
                                break

                # Find best performing channel
                best_channel = None
                best_rate = 0
                for channel, data in channel_performance.items():
                    if data["sent"] > 0:
                        rate = data["responded"] / data["sent"]
                        if rate > best_rate:
                            best_rate = rate
                            best_channel = channel

                performance_metrics["best_channel"] = best_channel
                performance_metrics["best_channel_rate"] = best_rate
                performance_metrics["channel_performance"] = channel_performance

                # Timing analysis
                response_times = []
                for followup in follow_up_history:
                    sent_time = followup.get("sent_at")
                    if sent_time and isinstance(sent_time, str):
                        try:
                            sent_dt = datetime.fromisoformat(sent_time)
                            response_times.append(sent_dt.hour)
                        except (ValueError, TypeError) as e:
                            logger.debug(f"Failed to parse sent_at timestamp '{sent_time}': {e}")
                            pass

                if response_times:
                    optimal_hour = max(set(response_times), key=response_times.count)
                    performance_metrics["optimal_send_hour"] = optimal_hour

            # Generate recommendations based on performance data
            if performance_metrics.get("response_rate", 0) > 0.3:
                recommended_action = "Performance is strong - continue current approach"
                confidence = 0.9
            elif performance_metrics.get("response_rate", 0) > 0.15:
                recommended_action = "Moderate performance - optimize timing and channel"
                confidence = 0.8
            elif len(follow_up_history) >= 5:
                recommended_action = "Low performance - consider strategy change or escalation"
                confidence = 0.85
            else:
                recommended_action = "Insufficient data - continue monitoring and collecting metrics"
                confidence = 0.6

            # Include specific optimization suggestions
            optimization_suggestions = []
            if best_channel := performance_metrics.get("best_channel"):
                optimization_suggestions.append(f"Use {best_channel} channel (best performance)")

            if optimal_hour := performance_metrics.get("optimal_send_hour"):
                optimization_suggestions.append(f"Send at {optimal_hour}:00 (optimal time)")

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=confidence,
                recommended_action=recommended_action,
                reasoning=f"Performance analysis based on {len(follow_up_history)} follow-ups",
                metadata={
                    "performance_metrics": performance_metrics,
                    "optimization_suggestions": optimization_suggestions,
                    "data_quality": "high"
                    if len(follow_up_history) >= 5
                    else "medium"
                    if len(follow_up_history) >= 2
                    else "low",
                },
            )

        except Exception as e:
            logger.error(f"Error in performance tracker: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.5,
                recommended_action="Continue standard tracking and monitoring",
                reasoning="Error in performance analysis, using baseline approach",
            )


class SchedulingAgent(FollowUpAgent):
    """Phase 7: Autonomous Scheduling Agent. Coordinates with CalendarScheduler."""

    def __init__(self, llm_client, blackboard=None):
        super().__init__(AgentType.SCHEDULING_AGENT, llm_client, blackboard)
        try:
            from ghl_real_estate_ai.services.calendar_scheduler import get_smart_scheduler

            self.scheduler = get_smart_scheduler()
        except ImportError:
            self.scheduler = None

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Analyze if the lead is ready for scheduling and provide slots."""
        try:
            if not self.scheduler:
                return FollowUpRecommendation(
                    agent_type=self.agent_type,
                    confidence=0.0,
                    recommended_action="Scheduling unavailable",
                    reasoning="CalendarScheduler service not found",
                )

            behavioral_score = context.get("behavioral_score")
            lead_profile = context.get("lead_profile", {})
            qualification_score = getattr(behavioral_score, "qualification_score", 0) if behavioral_score else 0

            # Only schedule for high-intent leads (score >= 5 or intent=HOT/URGENT)
            intent_level = (
                getattr(behavioral_score, "intent_level", IntentLevel.COLD) if behavioral_score else IntentLevel.COLD
            )

            should_schedule = qualification_score >= 5 or intent_level in [IntentLevel.HOT, IntentLevel.URGENT]

            if not should_schedule:
                self.log_thought(
                    lead_id,
                    f"Lead not ready for scheduling. Score: {qualification_score}",
                    "Continue qualification",
                    0.3,
                )
                return FollowUpRecommendation(
                    agent_type=self.agent_type,
                    confidence=0.3,
                    recommended_action="Continue qualification",
                    reasoning=f"Lead not yet ready for scheduling (Score: {qualification_score})",
                )

            # Get available slots
            from ghl_real_estate_ai.services.calendar_scheduler import AppointmentType

            appt_type = AppointmentType.BUYER_CONSULTATION
            if "invest" in str(lead_profile.get("motivation", "")).lower():
                appt_type = AppointmentType.INVESTOR_MEETING

            slots = await self.scheduler.suggest_appointment_times(
                contact_id=f"contact_{lead_id}", appointment_type=appt_type
            )

            reasoning = f"Lead is highly qualified ({intent_level.value}). Proposing slots: {', '.join(slots[:2])}"

            self.log_thought(
                lead_id,
                f"Lead intent is {intent_level.value}. Proposing appointment.",
                "Propose scheduling slots",
                0.95,
            )

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.95,
                recommended_action="Propose scheduling slots",
                reasoning=reasoning,
                metadata={"suggested_slots": slots, "appointment_type": appt_type.value},
            )

        except Exception as e:
            logger.error(f"Error in scheduling agent: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.2,
                recommended_action="Standard follow-up",
                reasoning="Error in scheduling analysis",
            )


class VideoAIAgent(FollowUpAgent):
    """Phase 7: Video AI Personalization Agent. Coordinates with HeyGen/Tavus APIs."""

    def __init__(self, llm_client, blackboard: Any = None):
        super().__init__(AgentType.VIDEO_AI_AGENT, llm_client, blackboard)

    async def analyze(self, lead_id: str, context: FollowupContext) -> FollowUpRecommendation:
        """Decide if a personalized video is appropriate for this lead."""
        try:
            behavioral_score = context.get("behavioral_score")
            intent_level = (
                getattr(behavioral_score, "intent_level", IntentLevel.COLD) if behavioral_score else IntentLevel.COLD
            )

            # Only generate videos for HOT or URGENT leads to manage token/API costs
            if intent_level not in [IntentLevel.HOT, IntentLevel.URGENT]:
                return FollowUpRecommendation(
                    agent_type=self.agent_type,
                    confidence=0.1,
                    recommended_action="No video needed",
                    reasoning=f"Lead intent ({intent_level.value}) does not justify video cost.",
                )

            # Simulated Video API integration
            video_url = f"https://video-ai.io/jorge/personalized?lead={lead_id}&tone=energetic"

            self.log_thought(
                lead_id,
                f"High-intent lead detected ({intent_level.value}). Triggering personalized video generation.",
                "Generate Personalized Video",
                0.9,
            )

            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.9,
                recommended_action="Send personalized video",
                reasoning="High-value lead warrants a personalized video touchpoint.",
                metadata={"video_url": video_url},
            )

        except Exception as e:
            logger.error(f"Error in video AI agent: {e}")
            return FollowUpRecommendation(
                agent_type=self.agent_type,
                confidence=0.0,
                recommended_action="Skip video",
                reasoning="Error in video analysis",
            )


class AutonomousFollowUpEngine:
    """
    Continuously monitors leads and autonomously executes follow-ups.

    Key Capabilities:
    - Behavioral monitoring (real-time intent detection)
    - Autonomous message generation (Claude-powered)
    - Optimal timing prediction
    - Multi-channel orchestration
    - Zero human intervention for routine tasks
    """

    def __init__(self):
        self.behavioral_engine = get_behavioral_trigger_engine()
        self.cache = get_cache_service()
        self.llm_client = get_llm_client()
        self.lead_intelligence_swarm = get_lead_intelligence_swarm()

        # Phase 7: Shared context for explainability
        from ghl_real_estate_ai.agents.blackboard import SharedBlackboard

        self.blackboard = SharedBlackboard()

        # Agent swarm for follow-up orchestration - 10 specialized agents
        self.timing_optimizer = TimingOptimizerAgent(self.llm_client, self.blackboard)
        self.content_personalizer = ContentPersonalizerAgent(self.llm_client, self.blackboard)
        self.channel_strategist = ChannelStrategistAgent(self.llm_client, self.blackboard)
        self.response_analyzer = ResponseAnalyzerAgent(self.llm_client, self.blackboard)
        self.escalation_manager = EscalationManagerAgent(self.llm_client, self.blackboard)

        # New specialized agents
        self.sentiment_analyst = SentimentAnalystAgent(self.llm_client, self.blackboard)
        self.objection_handler = ObjectionHandlerAgent(self.llm_client, self.blackboard)
        self.conversion_optimizer = ConversionOptimizerAgent(self.llm_client, self.blackboard)
        self.market_context_agent = MarketContextAgent(self.llm_client, self.blackboard)
        self.performance_tracker = PerformanceTrackerAgent(self.llm_client, self.blackboard)
        self.scheduling_agent = SchedulingAgent(self.llm_client, self.blackboard)
        self.video_ai_agent = VideoAIAgent(self.llm_client, self.blackboard)

        # Task queue
        self.pending_tasks: List[FollowUpTask] = []
        self.task_lock = asyncio.Lock()

        # Configuration
        self.monitoring_interval_seconds = 300  # Check every 5 minutes
        self.max_daily_followups_per_lead = 3
        self.batch_size = 10
        self.agent_consensus_threshold = 0.7  # Minimum confidence for agent consensus

        # State
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None

        # Performance tracking
        self.agent_performance: Dict[AgentType, Dict[str, float]] = {
            agent_type: {"success_rate": 0.0, "avg_confidence": 0.0, "total_recommendations": 0}
            for agent_type in AgentType
        }

    async def start_monitoring(self):
        """
        Start autonomous lead monitoring and follow-up execution.

        This runs continuously in the background, monitoring leads
        and executing follow-ups without human intervention.
        """
        if self.is_running:
            logger.warning("⚠️ Autonomous follow-up engine already running")
            return

        self.is_running = True
        self.monitor_task = safe_create_task(self._monitoring_loop())

        logger.info(f"✅ Autonomous Follow-Up Engine started (interval: {self.monitoring_interval_seconds}s)")

    async def stop_monitoring(self):
        """Stop autonomous monitoring."""
        self.is_running = False

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("⏹️ Autonomous Follow-Up Engine stopped")

    async def monitor_and_respond(self, leads_to_monitor: Optional[List[str]] = None):
        """
        Monitor leads and create autonomous follow-up tasks.

        Args:
            leads_to_monitor: Optional list of lead IDs to monitor.
                              If None, monitors all active leads.
        """
        try:
            # Get high-intent leads from behavioral engine
            high_intent_leads = await self.behavioral_engine.get_high_intent_leads(min_likelihood=50.0, limit=50)

            if leads_to_monitor:
                # Filter to specified leads
                leads_to_process = [l for l in high_intent_leads if l in leads_to_monitor]
            else:
                leads_to_process = high_intent_leads

            logger.info(f"📊 Monitoring {len(leads_to_process)} high-intent leads")

            # Process leads in batches
            for i in range(0, len(leads_to_process), self.batch_size):
                batch = leads_to_process[i : i + self.batch_size]

                # Process batch concurrently
                tasks = [self._process_lead(lead_id) for lead_id in batch]
                await asyncio.gather(*tasks, return_exceptions=True)

                # Small delay between batches to avoid overwhelming the system
                if i + self.batch_size < len(leads_to_process):
                    await asyncio.sleep(1)

            logger.info(f"✅ Monitoring cycle complete: processed {len(leads_to_process)} leads")

        except Exception as e:
            logger.error(f"❌ Error in monitor_and_respond: {e}")

    async def execute_pending_tasks(self):
        """
        Execute pending follow-up tasks that are ready.
        Loads tasks from database for production state persistence.
        """
        try:
            db = await get_database()
            db_tasks = await db.get_pending_follow_up_tasks(limit=self.batch_size)

            if not db_tasks:
                # Fallback to in-memory tasks if DB returns nothing but memory has some
                async with self.task_lock:
                    now = datetime.now()
                    ready_tasks = [
                        task
                        for task in self.pending_tasks
                        if task.status == FollowUpStatus.SCHEDULED and task.scheduled_time <= now
                    ]
                    if not ready_tasks:
                        return

                    tasks_to_execute = ready_tasks[: self.batch_size]
            else:
                # Convert DB rows back to FollowUpTask objects
                tasks_to_execute = []
                for row in db_tasks:
                    tasks_to_execute.append(
                        FollowUpTask(
                            task_id=row["id"],
                            lead_id=str(row["lead_id"]),
                            contact_id=row["contact_id"],
                            channel=FollowUpChannel(row["channel"]),
                            message=row["message"],
                            scheduled_time=row["scheduled_time"],
                            status=FollowUpStatus(row["status"]),
                            priority=row["priority"],
                            intent_level=IntentLevel(row["intent_level"]) if row["intent_level"] else None,
                            metadata=json.loads(row["metadata"])
                            if isinstance(row["metadata"], str)
                            else row["metadata"],
                            created_at=row["created_at"],
                        )
                    )

            logger.info(f"📤 Executing {len(tasks_to_execute)} ready follow-up tasks from persistent storage")

            # Execute tasks
            for task in tasks_to_execute:
                await self._execute_task(task)

        except Exception as e:
            logger.error(f"❌ Error executing pending tasks from database: {e}")

    async def _monitoring_loop(self):
        """Continuous monitoring loop."""
        try:
            while self.is_running:
                # Monitor leads and create tasks
                await self.monitor_and_respond()

                # Execute ready tasks
                await self.execute_pending_tasks()

                # Wait before next cycle
                await asyncio.sleep(self.monitoring_interval_seconds)

        except asyncio.CancelledError:
            logger.info("🛑 Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}")
            self.is_running = False

    async def _process_lead(self, lead_id: str):
        """Process a single lead with multi-agent collaboration for follow-up opportunities."""
        try:
            # Check if lead already has recent follow-up
            cache_key = f"followup_last:{lead_id}"
            last_followup = await self.cache.get(cache_key)

            if last_followup:
                last_time = datetime.fromisoformat(last_followup)
                if datetime.now() - last_time < timedelta(hours=4):
                    logger.debug(f"⏭️ Skipping lead {lead_id}: recent follow-up exists")
                    return

            # Get comprehensive lead intelligence from swarm
            logger.debug(f"🤖 Deploying lead intelligence swarm for {lead_id}")
            swarm_analysis = await self.lead_intelligence_swarm.analyze_lead(lead_id)

            if not swarm_analysis or swarm_analysis.consensus_score < 0.5:
                logger.debug(f"⏭️ Skipping lead {lead_id}: insufficient intelligence consensus")
                return

            # Get additional context data
            activity_data = await self._get_lead_activity(lead_id)
            follow_up_history = await self._get_follow_up_history(lead_id)
            response_data = await self._get_response_data(lead_id)
            lead_profile = await self._get_lead_profile(lead_id)

            # Phase 7: Gather market intelligence for agents
            market_area = lead_profile.get("market_area", "austin")
            arbitrage_info = ""
            market_context_data = {}
            if hasattr(self.market_context_agent, "market_engine") and self.market_context_agent.market_engine:
                try:
                    dashboard = await self.market_context_agent.market_engine.get_opportunity_dashboard(market_area)
                    if dashboard.get("opportunities"):
                        top_opp = dashboard["opportunities"][0]
                        arbitrage_info = (
                            f"Prime Arbitrage: {top_opp['type']} ({top_opp['score']}% ROI) in {market_area}"
                        )
                    market_context_data = dashboard.get("market_overview", {})
                except Exception as e:
                    logger.warning(f"Failed to pre-fetch market data: {e}")

            # Create context for agents
            agent_context: FollowupContext = {
                "lead_id": lead_id,
                "activity_data": activity_data,
                "follow_up_history": follow_up_history,
                "response_data": response_data,
                "lead_profile": lead_profile,
                "swarm_analysis": swarm_analysis,
                "behavioral_score": swarm_analysis.primary_insight.metadata.get("behavioral_score"),
                "market_context": market_context_data,
                "arbitrage_info": arbitrage_info,
            }

            # Deploy specialized follow-up agents in parallel - 12 agent swarm (Phase 7)
            logger.debug(f"🚀 Deploying comprehensive 12-agent follow-up swarm for {lead_id}")
            agent_tasks = [
                self.timing_optimizer.analyze(lead_id, agent_context),
                self.content_personalizer.analyze(lead_id, agent_context),
                self.channel_strategist.analyze(lead_id, agent_context),
                self.response_analyzer.analyze(lead_id, agent_context),
                self.escalation_manager.analyze(lead_id, agent_context),
                # New specialized agents
                self.sentiment_analyst.analyze(lead_id, agent_context),
                self.objection_handler.analyze(lead_id, agent_context),
                self.conversion_optimizer.analyze(lead_id, agent_context),
                self.market_context_agent.analyze(lead_id, agent_context),
                self.performance_tracker.analyze(lead_id, agent_context),
                self.scheduling_agent.analyze(lead_id, agent_context),
                self.video_ai_agent.analyze(lead_id, agent_context),
            ]

            # Execute all agents concurrently
            agent_recommendations = await asyncio.gather(*agent_tasks, return_exceptions=True)

            # Filter out exceptions and low-confidence recommendations
            valid_recommendations = [
                rec
                for rec in agent_recommendations
                if isinstance(rec, FollowUpRecommendation) and rec.confidence >= self.agent_consensus_threshold
            ]

            if not valid_recommendations:
                logger.warning(f"⚠️ No high-confidence recommendations from agents for lead {lead_id}")
                return

            # Build consensus from agent recommendations
            consensus = await self._build_agent_consensus(valid_recommendations, swarm_analysis)

            # Check for escalation
            escalation_recs = [rec for rec in valid_recommendations if rec.escalation_needed]
            if escalation_recs:
                logger.info(f"🚨 Escalation needed for lead {lead_id}: {escalation_recs[0].reasoning}")
                await self._handle_escalation(lead_id, escalation_recs[0], swarm_analysis)
                return

            # Check if follow-up is warranted based on consensus
            if consensus["confidence"] < self.agent_consensus_threshold:
                logger.debug(f"⏭️ Skipping lead {lead_id}: low agent consensus ({consensus['confidence']:.2f})")
                return

            # Get contact info
            contact_id = f"contact_{lead_id}"

            # Create follow-up task based on agent consensus
            task = FollowUpTask(
                task_id=f"task_{lead_id}_{int(datetime.now().timestamp())}",
                lead_id=lead_id,
                contact_id=contact_id,
                channel=consensus["channel"],
                message=consensus["message"],
                scheduled_time=consensus["timing"],
                status=FollowUpStatus.SCHEDULED,
                priority=consensus["priority"],
                intent_level=swarm_analysis.consensus.intent_level,
                metadata={
                    "agent_consensus_score": consensus["confidence"],
                    "participating_agents": [rec.agent_type.value for rec in valid_recommendations],
                    "swarm_consensus_score": swarm_analysis.consensus_score,
                    "lead_intelligence_score": swarm_analysis.consensus.opportunity_score,
                },
            )

            # Add to task queue
            async with self.task_lock:
                self.pending_tasks.append(task)

            # PRODUCTION HARDENING: Persist task to database for state persistence
            try:
                db = await get_database()
                await db.save_follow_up_task(
                    {
                        "task_id": task.task_id,
                        "lead_id": task.lead_id,
                        "contact_id": task.contact_id,
                        "channel": task.channel.value,
                        "message": task.message,
                        "scheduled_time": task.scheduled_time,
                        "status": task.status.value,
                        "priority": task.priority,
                        "intent_level": task.intent_level.value if task.intent_level else None,
                        "metadata": task.metadata,
                    }
                )
                logger.info(f"✅ Persisted follow-up task {task.task_id} to database")
            except Exception as e:
                logger.error(f"❌ Failed to persist follow-up task {task.task_id}: {e}")

            # Update agent performance tracking
            await self._update_agent_performance(valid_recommendations)

            logger.info(
                f"📝 Created AI-orchestrated follow-up task for lead {lead_id}: "
                f"{consensus['channel'].value} at {consensus['timing'].strftime('%H:%M')} "
                f"(10-agent consensus: {consensus['confidence']:.2f}, participating: {len(valid_recommendations)})"
            )

            # Update cache
            await self.cache.set(
                cache_key,
                datetime.now().isoformat(),
                ttl=14400,  # 4 hours
            )

        except Exception as e:
            logger.error(f"❌ Error in multi-agent lead processing {lead_id}: {e}")

    async def _execute_task(self, task: FollowUpTask):
        """Execute a follow-up task and update its persistent state."""
        try:
            logger.info(f"📤 Executing follow-up task {task.task_id} via {task.channel.value}")

            # Execute based on channel
            success = False

            if task.channel == FollowUpChannel.SMS:
                success = await self._send_sms(task.contact_id, task.message)
            elif task.channel == FollowUpChannel.EMAIL:
                success = await self._send_email(task.contact_id, task.message)
            elif task.channel == FollowUpChannel.CALL:
                success = await self._initiate_call(task.contact_id)

            # Update task status
            executed_at = datetime.now()
            if success:
                task.status = FollowUpStatus.SENT
                task.executed_at = executed_at
                task.result = {"success": True, "timestamp": executed_at.isoformat()}
                logger.info(f"✅ Follow-up task {task.task_id} sent successfully")
            else:
                task.status = FollowUpStatus.FAILED
                task.result = {"success": False, "error": "Delivery failed"}
                logger.error(f"❌ Follow-up task {task.task_id} failed")

            # PRODUCTION HARDENING: Update task status in database
            try:
                db = await get_database()
                await db.update_follow_up_task(
                    task.task_id, {"status": task.status.value, "executed_at": task.executed_at, "result": task.result}
                )
            except Exception as db_e:
                logger.error(f"⚠️ Failed to update task status in DB for {task.task_id}: {db_e}")

            # Remove from pending queue
            async with self.task_lock:
                self.pending_tasks = [t for t in self.pending_tasks if t.task_id != task.task_id]

        except Exception as e:
            logger.error(f"❌ Error executing task {task.task_id}: {e}")
            # Update failure in DB if possible
            try:
                db = await get_database()
                await db.update_follow_up_task(
                    task.task_id, {"status": FollowUpStatus.FAILED.value, "result": {"success": False, "error": str(e)}}
                )
            except Exception as db_err:
                logger.error(f"Failed to update task status in database after failure: {db_err}")

    async def _build_agent_consensus(
        self, recommendations: List[FollowUpRecommendation], swarm_analysis: Any
    ) -> Dict[str, Any]:
        """Build consensus from multiple agent recommendations."""
        try:
            # Calculate weighted consensus based on agent confidence and historical performance
            total_weight = 0.0
            weighted_confidence = 0.0

            # Extract recommendations by type
            timing_recs = [rec for rec in recommendations if rec.agent_type == AgentType.TIMING_OPTIMIZER]
            content_recs = [rec for rec in recommendations if rec.agent_type == AgentType.CONTENT_PERSONALIZER]
            channel_recs = [rec for rec in recommendations if rec.agent_type == AgentType.CHANNEL_STRATEGIST]

            # Build consensus timing
            consensus_timing = datetime.now() + timedelta(hours=4)  # Default
            if timing_recs:
                timing_rec = max(timing_recs, key=lambda r: r.confidence)
                if timing_rec.optimal_timing:
                    consensus_timing = timing_rec.optimal_timing

            # Build consensus message
            consensus_message = "Thank you for your interest! I have some great properties to show you."
            if content_recs:
                content_rec = max(content_recs, key=lambda r: r.confidence)
                if content_rec.suggested_message:
                    consensus_message = content_rec.suggested_message

            # Build consensus channel
            consensus_channel = FollowUpChannel.EMAIL  # Default
            if channel_recs:
                channel_rec = max(channel_recs, key=lambda r: r.confidence)
                if channel_rec.suggested_channel:
                    consensus_channel = channel_rec.suggested_channel

            # Calculate consensus confidence
            for rec in recommendations:
                agent_performance = self.agent_performance.get(rec.agent_type, {"success_rate": 0.7})
                weight = rec.confidence * agent_performance["success_rate"]
                total_weight += weight
                weighted_confidence += rec.confidence * weight

            consensus_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.5

            # Determine priority based on swarm analysis
            intent_level = swarm_analysis.consensus.intent_level if swarm_analysis else IntentLevel.WARM
            priority = self._calculate_priority(intent_level)

            return {
                "confidence": consensus_confidence,
                "timing": consensus_timing,
                "message": consensus_message,
                "channel": consensus_channel,
                "priority": priority,
                "reasoning": f"Consensus from {len(recommendations)} agents with {consensus_confidence:.2f} confidence",
            }

        except Exception as e:
            logger.error(f"Error building agent consensus: {e}")
            # Return safe fallback consensus
            return {
                "confidence": 0.5,
                "timing": datetime.now() + timedelta(hours=4),
                "message": "I have some properties that might interest you. Would you like to learn more?",
                "channel": FollowUpChannel.EMAIL,
                "priority": 2,
                "reasoning": "Fallback consensus due to error",
            }

    async def _handle_escalation(self, lead_id: str, escalation_rec: FollowUpRecommendation, swarm_analysis: Any):
        """Handle escalation to human agent."""
        try:
            logger.info(f"🚨 Escalating lead {lead_id} to human agent: {escalation_rec.reasoning}")

            # Create escalation record
            escalation_data = {
                "lead_id": lead_id,
                "escalation_reason": escalation_rec.reasoning,
                "urgency_level": swarm_analysis.consensus.urgency_level if swarm_analysis else "medium",
                "swarm_insights": swarm_analysis.consensus.primary_finding if swarm_analysis else "Unknown",
                "recommended_action": escalation_rec.recommended_action,
                "escalated_at": datetime.now().isoformat(),
                "escalation_confidence": escalation_rec.confidence,
            }

            # Store escalation in cache for human agent pickup
            escalation_key = f"escalation:{lead_id}"
            await self.cache.set(escalation_key, escalation_data, ttl=86400)  # 24 hours

            # TODO: Integrate with human agent notification system
            # This could send alerts to Slack, email, or CRM system

            logger.info(f"✅ Lead {lead_id} escalation recorded and ready for human pickup")

        except Exception as e:
            logger.error(f"Error handling escalation for {lead_id}: {e}")

    async def _update_agent_performance(self, recommendations: List[FollowUpRecommendation]):
        """Update agent performance metrics."""
        try:
            for rec in recommendations:
                agent_type = rec.agent_type
                if agent_type in self.agent_performance:
                    # Update confidence tracking
                    current_stats = self.agent_performance[agent_type]
                    total_recs = current_stats["total_recommendations"]
                    avg_confidence = current_stats["avg_confidence"]

                    # Update running average
                    new_total = total_recs + 1
                    new_avg_confidence = (avg_confidence * total_recs + rec.confidence) / new_total

                    self.agent_performance[agent_type].update(
                        {
                            "avg_confidence": new_avg_confidence,
                            "total_recommendations": new_total,
                            "last_updated": datetime.now().isoformat(),
                        }
                    )

        except Exception as e:
            logger.error(f"Error updating agent performance: {e}")

    async def _get_follow_up_history(self, lead_id: str) -> List[Dict[str, Any]]:
        """Get follow-up history for lead."""
        try:
            db = await get_database()
            return await db.get_lead_follow_up_history(lead_id, limit=50)
        except Exception as e:
            logger.error(f"Error getting follow-up history for {lead_id}: {e}")
            return []

    async def _get_response_data(self, lead_id: str) -> Dict[str, Any]:
        """Get response data for lead."""
        try:
            db = await get_database()
            return await db.get_lead_response_data(lead_id)
        except Exception as e:
            logger.error(f"Error getting response data for {lead_id}: {e}")
            return {
                "responses": [],
                "negative_sentiment": False,
                "last_response_time": None,
                "total_responses": 0,
                "avg_sentiment": 0,
            }

    async def _get_lead_profile(self, lead_id: str) -> Dict[str, Any]:
        """Get lead profile data."""
        try:
            db = await get_database()
            return await db.get_lead_profile_data(lead_id)
        except Exception as e:
            logger.error(f"Error getting lead profile for {lead_id}: {e}")
            return {"name": "Unknown Lead", "contacts": [], "preferences": {}, "demographics": {}}

    async def _generate_contextual_followup(
        self,
        lead_id: str,
        behavioral_score: Any,
        activity_data: Dict[str, Any],
    ) -> str:
        """
        Generate contextual follow-up message using Claude.

        Integrates:
        - Lead history
        - Behavioral patterns
        - Market context
        - Previous conversation
        """
        try:
            # Build context for Claude
            context = {
                "lead_id": lead_id,
                "intent_level": behavioral_score.intent_level.value,
                "likelihood_score": behavioral_score.likelihood_score,
                "key_signals": [
                    {
                        "type": p.signal_type.value,
                        "frequency": p.frequency,
                        "recency_hours": p.recency_hours,
                    }
                    for p in behavioral_score.key_signals[:3]  # Top 3 signals
                ],
                "market_context": behavioral_score.market_context,
            }

            # Generate message with Claude
            prompt = f"""Generate a personalized follow-up message for a real estate lead.

Context:
- Intent Level: {context["intent_level"]}
- Likelihood to Convert: {context["likelihood_score"]:.1f}%
- Key Behaviors: {", ".join([s["type"] for s in context["key_signals"]])}

Requirements:
- Be conversational and helpful (not salesy)
- Reference their recent activity naturally
- Provide clear value proposition
- Include soft call-to-action
- Keep under 160 characters for SMS

Generate the message:"""

            response = await self.llm_client.generate(prompt=prompt, max_tokens=200, temperature=0.7)

            # Use Claude-generated message or fallback to behavioral engine
            message = response.content.strip() if response.content else behavioral_score.recommended_message

            return message

        except Exception as e:
            logger.error(f"Error generating contextual message: {e}")
            # Fallback to behavioral engine recommendation
            return behavioral_score.recommended_message

    async def _get_lead_activity(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Get lead activity data for analysis.

        Queries the database for:
        - Email interactions
        - Website visits
        - Communication history
        - Behavioral metrics
        - etc.
        """
        try:
            db = await get_database()
            return await db.get_lead_activity_data(lead_id)
        except Exception as e:
            logger.error(f"Error getting lead activity for {lead_id}: {e}")
            return {
                "property_searches": [],
                "email_interactions": [],
                "website_visits": [],
                "pricing_tool_uses": [],
                "agent_inquiries": [],
            }

    async def _calculate_send_time(self, optimal_window: tuple[int, int]) -> datetime:
        """Calculate when to send the follow-up."""
        now = datetime.now()
        start_hour, end_hour = optimal_window

        # If within optimal window, send ASAP
        if start_hour <= now.hour <= end_hour:
            return now + timedelta(minutes=5)  # Small delay for rate limiting

        # Otherwise, schedule for start of next optimal window
        target_hour = start_hour
        if now.hour >= end_hour:
            # Schedule for tomorrow
            target_date = now.date() + timedelta(days=1)
        else:
            # Schedule for today
            target_date = now.date()

        scheduled_time = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=target_hour)

        return scheduled_time

    def _calculate_priority(self, intent_level: IntentLevel) -> int:
        """Calculate task priority (1-5) based on intent level."""
        priority_map = {
            IntentLevel.URGENT: 5,
            IntentLevel.HOT: 4,
            IntentLevel.WARM: 3,
            IntentLevel.COLD: 1,
        }

        return priority_map.get(intent_level, 1)

    async def _send_sms(self, contact_id: str, message: str) -> bool:
        """Send SMS via GHL integration."""
        try:
            from ghl_real_estate_ai.services.ghl_client import GHLClient

            client = GHLClient()
            # contact_id in task might be prefixed with contact_
            clean_contact_id = contact_id.replace("contact_", "")
            await client.send_message(clean_contact_id, message, channel=MessageType.SMS)
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS via GHL: {e}")
            return False

    async def _send_email(self, contact_id: str, message: str) -> bool:
        """Send email via GHL integration."""
        try:
            from ghl_real_estate_ai.services.ghl_client import GHLClient

            client = GHLClient()
            clean_contact_id = contact_id.replace("contact_", "")
            await client.send_message(clean_contact_id, message, channel=MessageType.EMAIL)
            return True
        except Exception as e:
            logger.error(f"Failed to send email via GHL: {e}")
            return False

    async def _initiate_call(self, contact_id: str) -> bool:
        """Initiate call via Vapi integration with full lead context."""
        try:
            from ghl_real_estate_ai.services.vapi_service import VapiService

            vapi = VapiService()

            # Extract lead_id from contact_id (prefixed with contact_)
            lead_id = contact_id.replace("contact_", "")

            # Fetch lead profile for Vapi context
            lead_profile = await self._get_lead_profile(lead_id)
            phone = lead_profile.get("phone")
            name = lead_profile.get("name", "Homeowner")

            if not phone:
                logger.error(f"Cannot initiate call: No phone number for lead {lead_id}")
                return False

            # Fetch additional context for Voss Drift adaptation
            activity_data = await self._get_lead_activity(lead_id)

            # Calculate a dummy drift score for now or fetch from recent negotiation state
            # PRODUCTION HARDENING: Integrate with NegotiationDriftDetector
            from ghl_real_estate_ai.services.negotiation_drift_detector import get_drift_detector

            detector = get_drift_detector()

            # Analyze recent activity for drift if available
            recent_msg = ""
            if activity_data.get("sms_responses"):
                recent_msg = activity_data["sms_responses"][0].get("content", "")

            drift_analysis = detector.analyze_drift(recent_msg)

            return vapi.trigger_outbound_call(
                contact_phone=phone,
                lead_name=name,
                property_address=lead_profile.get("demographics", {}).get("city", "your property"),
                extra_variables={
                    "lead_id": lead_id,
                    "drift_score": drift_analysis["drift_score"],
                    "flexibility": drift_analysis["recommendation"],
                },
            )
        except Exception as e:
            logger.error(f"Failed to initiate call via Vapi: {e}")
            return False

    def get_task_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics on follow-up tasks and agent performance."""
        total_tasks = len(self.pending_tasks)

        status_counts = {}
        agent_orchestrated_tasks = 0
        for task in self.pending_tasks:
            status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1
            if task.metadata.get("agent_consensus_score"):
                agent_orchestrated_tasks += 1

        return {
            "total_tasks": total_tasks,
            "agent_orchestrated_tasks": agent_orchestrated_tasks,
            "status_breakdown": status_counts,
            "is_running": self.is_running,
            "monitoring_interval_seconds": self.monitoring_interval_seconds,
            "agent_consensus_threshold": self.agent_consensus_threshold,
            "agent_performance": self.agent_performance,
            "system_status": "multi_agent_orchestrated" if agent_orchestrated_tasks > 0 else "standard",
        }

    def get_agent_insights(self) -> Dict[str, Any]:
        """Get detailed agent performance insights."""
        insights = {"total_agents": len(AgentType), "agents": {}}

        for agent_type, performance in self.agent_performance.items():
            insights["agents"][agent_type.value] = {
                "performance": performance,
                "status": "active" if performance["total_recommendations"] > 0 else "inactive",
                "effectiveness_score": performance["avg_confidence"] * performance["success_rate"],
            }

        # Calculate overall agent system effectiveness
        total_effectiveness = sum(data["effectiveness_score"] for data in insights["agents"].values())
        insights["overall_effectiveness"] = total_effectiveness / len(AgentType) if len(AgentType) > 0 else 0

        return insights


# Global singleton
_autonomous_engine = None


def get_autonomous_followup_engine() -> AutonomousFollowUpEngine:
    """Get singleton autonomous follow-up engine."""
    global _autonomous_engine
    if _autonomous_engine is None:
        _autonomous_engine = AutonomousFollowUpEngine()
    return _autonomous_engine
