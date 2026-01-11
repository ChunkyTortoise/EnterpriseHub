"""
Predictive Engagement Engine

AI-powered system for predicting optimal lead engagement timing and conversion
likelihood. Uses behavioral patterns, conversation history, and market intelligence
to maximize agent productivity and lead conversion rates.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from .redis_conversation_service import redis_conversation_service
from .advanced_market_intelligence import AdvancedMarketIntelligenceEngine
from ..ghl_utils.config import settings

logger = logging.getLogger(__name__)


class EngagementUrgency(Enum):
    """Engagement urgency levels"""
    CRITICAL = "critical"      # Contact within 1 hour
    HIGH = "high"             # Contact within 4 hours
    MEDIUM = "medium"         # Contact within 24 hours
    LOW = "low"               # Contact within 3 days
    NURTURE = "nurture"       # Add to nurture campaign


class ConversionStage(Enum):
    """Lead conversion stages"""
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    INTENT = "intent"
    EVALUATION = "evaluation"
    DECISION = "decision"


class EngagementChannel(Enum):
    """Optimal engagement channels"""
    PHONE = "phone"
    SMS = "sms"
    EMAIL = "email"
    VIDEO = "video"
    IN_PERSON = "in_person"


@dataclass
class EngagementPrediction:
    """Prediction for optimal lead engagement"""
    lead_id: str
    agent_id: str
    urgency: EngagementUrgency
    optimal_time: datetime
    conversion_stage: ConversionStage
    conversion_probability: float
    recommended_channel: EngagementChannel
    recommended_message: str
    key_talking_points: List[str]
    confidence_score: float
    reasoning: List[str]


@dataclass
class BehavioralSignal:
    """Individual behavioral signal"""
    signal_type: str
    strength: float  # 0-1
    timestamp: datetime
    context: Dict[str, Any]


@dataclass
class EngagementHistory:
    """Historical engagement data for prediction"""
    lead_id: str
    previous_engagements: List[Dict[str, Any]]
    response_patterns: Dict[str, Any]
    optimal_times: List[datetime]
    channel_preferences: Dict[str, float]


class PredictiveEngagementEngine:
    """
    Predictive engagement engine for optimal lead interaction timing.

    Features:
    - Behavioral pattern analysis
    - Conversion probability prediction
    - Optimal timing calculation
    - Channel preference learning
    - Market-aware engagement strategies
    """

    def __init__(self):
        self.redis_service = redis_conversation_service
        self.market_intelligence = AdvancedMarketIntelligenceEngine("default_location")

        # Behavioral signal weights
        self.signal_weights = {
            "website_activity": 0.25,
            "email_engagement": 0.20,
            "property_views": 0.30,
            "conversation_sentiment": 0.15,
            "market_activity": 0.10
        }

        # Time zone considerations (simplified for demo)
        self.optimal_contact_hours = {
            "morning": (9, 11),    # 9-11 AM
            "midday": (12, 14),    # 12-2 PM
            "afternoon": (15, 17), # 3-5 PM
            "evening": (18, 20)    # 6-8 PM
        }

    async def predict_optimal_engagement(
        self,
        lead_id: str,
        agent_id: str,
        current_context: Optional[Dict[str, Any]] = None
    ) -> EngagementPrediction:
        """
        Predict optimal engagement strategy for a lead.

        Args:
            lead_id: Lead identifier
            agent_id: Agent identifier
            current_context: Current conversation/interaction context

        Returns:
            EngagementPrediction with optimal strategy
        """
        try:
            logger.info(f"Generating engagement prediction for lead {lead_id}")

            # Gather behavioral signals
            behavioral_signals = await self._collect_behavioral_signals(lead_id)

            # Analyze engagement history
            engagement_history = await self._analyze_engagement_history(lead_id, agent_id)

            # Determine conversion stage
            conversion_stage = await self._determine_conversion_stage(
                lead_id, behavioral_signals, current_context
            )

            # Calculate conversion probability
            conversion_probability = await self._calculate_conversion_probability(
                behavioral_signals, engagement_history, conversion_stage
            )

            # Determine urgency level
            urgency = self._determine_engagement_urgency(
                behavioral_signals, conversion_stage, conversion_probability
            )

            # Calculate optimal timing
            optimal_time = await self._calculate_optimal_timing(
                lead_id, behavioral_signals, engagement_history
            )

            # Determine recommended channel
            recommended_channel = await self._determine_optimal_channel(
                behavioral_signals, engagement_history, conversion_stage
            )

            # Generate personalized message
            recommended_message = await self._generate_recommended_message(
                lead_id, conversion_stage, current_context
            )

            # Generate talking points
            talking_points = await self._generate_talking_points(
                lead_id, conversion_stage, behavioral_signals, current_context
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                behavioral_signals, engagement_history
            )

            # Generate reasoning
            reasoning = self._generate_prediction_reasoning(
                behavioral_signals, conversion_stage, urgency
            )

            prediction = EngagementPrediction(
                lead_id=lead_id,
                agent_id=agent_id,
                urgency=urgency,
                optimal_time=optimal_time,
                conversion_stage=conversion_stage,
                conversion_probability=conversion_probability,
                recommended_channel=recommended_channel,
                recommended_message=recommended_message,
                key_talking_points=talking_points,
                confidence_score=confidence_score,
                reasoning=reasoning
            )

            # Store prediction for learning
            await self._store_prediction(prediction)

            logger.info(f"Engagement prediction generated: {urgency.value} urgency, {conversion_probability:.1%} conversion probability")
            return prediction

        except Exception as e:
            logger.error(f"Error generating engagement prediction: {str(e)}")
            return await self._generate_fallback_prediction(lead_id, agent_id)

    async def get_daily_engagement_priorities(
        self,
        agent_id: str,
        lead_ids: List[str],
        target_date: Optional[datetime] = None
    ) -> List[EngagementPrediction]:
        """
        Get prioritized daily engagement list for an agent.

        Args:
            agent_id: Agent identifier
            lead_ids: List of lead IDs to prioritize
            target_date: Target date for engagement (defaults to today)

        Returns:
            Prioritized list of engagement predictions
        """
        try:
            if target_date is None:
                target_date = datetime.now()

            predictions = []

            # Generate predictions for all leads
            for lead_id in lead_ids:
                prediction = await self.predict_optimal_engagement(lead_id, agent_id)
                predictions.append(prediction)

            # Sort by urgency and conversion probability
            def sort_key(p: EngagementPrediction) -> Tuple[int, float]:
                urgency_priority = {
                    EngagementUrgency.CRITICAL: 5,
                    EngagementUrgency.HIGH: 4,
                    EngagementUrgency.MEDIUM: 3,
                    EngagementUrgency.LOW: 2,
                    EngagementUrgency.NURTURE: 1
                }
                return (urgency_priority[p.urgency], p.conversion_probability)

            predictions.sort(key=sort_key, reverse=True)

            logger.info(f"Generated daily priorities for agent {agent_id}: {len(predictions)} leads")
            return predictions

        except Exception as e:
            logger.error(f"Error generating daily priorities: {str(e)}")
            return []

    async def _collect_behavioral_signals(self, lead_id: str) -> List[BehavioralSignal]:
        """Collect and analyze behavioral signals for a lead"""
        signals = []

        try:
            # Website activity signals (demo implementation)
            website_activity = await self._get_website_activity_signals(lead_id)
            signals.extend(website_activity)

            # Email engagement signals
            email_signals = await self._get_email_engagement_signals(lead_id)
            signals.extend(email_signals)

            # Property viewing signals
            property_signals = await self._get_property_viewing_signals(lead_id)
            signals.extend(property_signals)

            # Conversation sentiment signals
            conversation_signals = await self._get_conversation_sentiment_signals(lead_id)
            signals.extend(conversation_signals)

            # Market activity signals
            market_signals = await self._get_market_activity_signals(lead_id)
            signals.extend(market_signals)

        except Exception as e:
            logger.warning(f"Error collecting behavioral signals: {str(e)}")

        return signals

    async def _get_website_activity_signals(self, lead_id: str) -> List[BehavioralSignal]:
        """Get website activity behavioral signals"""
        signals = []

        # Simulate website activity data
        activity_data = {
            "page_views_24h": 5 + hash(lead_id) % 10,
            "time_on_site": 300 + hash(lead_id) % 600,  # seconds
            "property_searches": 2 + hash(lead_id) % 5,
            "calculator_usage": hash(lead_id) % 3 > 0
        }

        # Convert to signals
        if activity_data["page_views_24h"] > 8:
            signals.append(BehavioralSignal(
                signal_type="high_website_activity",
                strength=0.8,
                timestamp=datetime.now() - timedelta(hours=2),
                context={"page_views": activity_data["page_views_24h"]}
            ))

        if activity_data["time_on_site"] > 600:
            signals.append(BehavioralSignal(
                signal_type="extended_session",
                strength=0.7,
                timestamp=datetime.now() - timedelta(hours=1),
                context={"session_time": activity_data["time_on_site"]}
            ))

        if activity_data["calculator_usage"]:
            signals.append(BehavioralSignal(
                signal_type="mortgage_calculator_usage",
                strength=0.9,
                timestamp=datetime.now() - timedelta(minutes=30),
                context={"tool": "mortgage_calculator"}
            ))

        return signals

    async def _get_email_engagement_signals(self, lead_id: str) -> List[BehavioralSignal]:
        """Get email engagement behavioral signals"""
        signals = []

        # Simulate email engagement data
        engagement_data = {
            "recent_opens": hash(lead_id) % 4,
            "click_through_rate": 0.1 + (hash(lead_id) % 30) / 100,
            "reply_rate": 0.05 + (hash(lead_id) % 15) / 100,
            "email_preference": ["morning", "afternoon", "evening"][hash(lead_id) % 3]
        }

        if engagement_data["recent_opens"] > 2:
            signals.append(BehavioralSignal(
                signal_type="high_email_engagement",
                strength=0.6,
                timestamp=datetime.now() - timedelta(hours=6),
                context={"opens": engagement_data["recent_opens"]}
            ))

        if engagement_data["click_through_rate"] > 0.2:
            signals.append(BehavioralSignal(
                signal_type="high_click_through",
                strength=0.7,
                timestamp=datetime.now() - timedelta(hours=8),
                context={"ctr": engagement_data["click_through_rate"]}
            ))

        return signals

    async def _get_property_viewing_signals(self, lead_id: str) -> List[BehavioralSignal]:
        """Get property viewing behavioral signals"""
        signals = []

        # Simulate property viewing data
        viewing_data = {
            "properties_viewed_24h": 1 + hash(lead_id) % 6,
            "favorite_saves": hash(lead_id) % 4,
            "virtual_tours": hash(lead_id) % 3,
            "price_range_searches": hash(lead_id) % 5
        }

        if viewing_data["properties_viewed_24h"] > 4:
            signals.append(BehavioralSignal(
                signal_type="intensive_property_research",
                strength=0.85,
                timestamp=datetime.now() - timedelta(hours=3),
                context={"properties_viewed": viewing_data["properties_viewed_24h"]}
            ))

        if viewing_data["favorite_saves"] > 2:
            signals.append(BehavioralSignal(
                signal_type="property_shortlisting",
                strength=0.9,
                timestamp=datetime.now() - timedelta(hours=4),
                context={"favorites": viewing_data["favorite_saves"]}
            ))

        if viewing_data["virtual_tours"] > 1:
            signals.append(BehavioralSignal(
                signal_type="virtual_tour_engagement",
                strength=0.8,
                timestamp=datetime.now() - timedelta(hours=2),
                context={"tours": viewing_data["virtual_tours"]}
            ))

        return signals

    async def _get_conversation_sentiment_signals(self, lead_id: str) -> List[BehavioralSignal]:
        """Get conversation sentiment signals"""
        signals = []

        try:
            # Get recent conversation history from Redis
            recent_messages = await self.redis_service.get_conversation_history(
                f"lead_{lead_id}", limit=10
            )

            positive_sentiment_count = 0
            urgency_indicators = 0

            for message in recent_messages:
                content = message.content.lower()

                # Check for positive sentiment
                positive_words = ["love", "perfect", "great", "excited", "interested", "ready"]
                if any(word in content for word in positive_words):
                    positive_sentiment_count += 1

                # Check for urgency indicators
                urgency_words = ["asap", "urgent", "soon", "quickly", "immediately"]
                if any(word in content for word in urgency_words):
                    urgency_indicators += 1

            if positive_sentiment_count > 2:
                signals.append(BehavioralSignal(
                    signal_type="positive_conversation_sentiment",
                    strength=0.7,
                    timestamp=datetime.now() - timedelta(hours=1),
                    context={"positive_messages": positive_sentiment_count}
                ))

            if urgency_indicators > 0:
                signals.append(BehavioralSignal(
                    signal_type="urgency_expression",
                    strength=0.95,
                    timestamp=datetime.now() - timedelta(minutes=30),
                    context={"urgency_count": urgency_indicators}
                ))

        except Exception as e:
            logger.warning(f"Error analyzing conversation sentiment: {str(e)}")

        return signals

    async def _get_market_activity_signals(self, lead_id: str) -> List[BehavioralSignal]:
        """Get market activity signals that may influence engagement timing"""
        signals = []

        try:
            # Get market intelligence for lead's area (simplified)
            area = "Austin"  # In production, get from lead data

            market_context = await self.market_intelligence.get_claude_market_context(area)

            if market_context and not market_context.get("error"):
                market_summary = market_context.get("market_summary", {})
                activity_level = market_summary.get("activity_level", "Moderate")

                if activity_level == "High":
                    signals.append(BehavioralSignal(
                        signal_type="hot_market_conditions",
                        strength=0.6,
                        timestamp=datetime.now(),
                        context={"market_activity": activity_level}
                    ))

        except Exception as e:
            logger.warning(f"Error getting market signals: {str(e)}")

        return signals

    async def _analyze_engagement_history(self, lead_id: str, agent_id: str) -> EngagementHistory:
        """Analyze historical engagement patterns"""
        try:
            # Get conversation history from Redis
            conversation_history = await self.redis_service.get_conversation_history(
                f"agent_{agent_id}_lead_{lead_id}", limit=50
            )

            # Analyze patterns (simplified implementation)
            response_patterns = {
                "avg_response_time_hours": 2.5 + (hash(lead_id) % 10),
                "preferred_communication_time": ["morning", "afternoon", "evening"][hash(lead_id) % 3],
                "response_rate": 0.6 + (hash(lead_id) % 30) / 100
            }

            optimal_times = [
                datetime.now() - timedelta(days=i, hours=(hash(lead_id + str(i)) % 8) + 9)
                for i in range(1, 6)
            ]

            channel_preferences = {
                "phone": 0.3 + (hash(lead_id + "phone") % 40) / 100,
                "sms": 0.4 + (hash(lead_id + "sms") % 35) / 100,
                "email": 0.2 + (hash(lead_id + "email") % 25) / 100,
                "video": 0.1 + (hash(lead_id + "video") % 15) / 100
            }

            return EngagementHistory(
                lead_id=lead_id,
                previous_engagements=[],  # Simplified for demo
                response_patterns=response_patterns,
                optimal_times=optimal_times,
                channel_preferences=channel_preferences
            )

        except Exception as e:
            logger.warning(f"Error analyzing engagement history: {str(e)}")
            return EngagementHistory(
                lead_id=lead_id,
                previous_engagements=[],
                response_patterns={"avg_response_time_hours": 4, "response_rate": 0.5},
                optimal_times=[],
                channel_preferences={"sms": 0.5, "phone": 0.3, "email": 0.2}
            )

    async def _determine_conversion_stage(
        self,
        lead_id: str,
        behavioral_signals: List[BehavioralSignal],
        current_context: Optional[Dict[str, Any]] = None
    ) -> ConversionStage:
        """Determine current conversion stage based on behavioral signals"""

        # Score signals for different stages
        stage_scores = {stage: 0 for stage in ConversionStage}

        for signal in behavioral_signals:
            if signal.signal_type in ["high_website_activity", "email_engagement"]:
                stage_scores[ConversionStage.AWARENESS] += signal.strength * 0.3
                stage_scores[ConversionStage.INTEREST] += signal.strength * 0.4

            elif signal.signal_type in ["property_viewing", "property_shortlisting"]:
                stage_scores[ConversionStage.INTEREST] += signal.strength * 0.3
                stage_scores[ConversionStage.CONSIDERATION] += signal.strength * 0.5

            elif signal.signal_type in ["mortgage_calculator_usage", "virtual_tour_engagement"]:
                stage_scores[ConversionStage.CONSIDERATION] += signal.strength * 0.4
                stage_scores[ConversionStage.INTENT] += signal.strength * 0.6

            elif signal.signal_type in ["urgency_expression", "positive_conversation_sentiment"]:
                stage_scores[ConversionStage.INTENT] += signal.strength * 0.4
                stage_scores[ConversionStage.EVALUATION] += signal.strength * 0.5

        # Return stage with highest score
        return max(stage_scores.items(), key=lambda x: x[1])[0]

    async def _calculate_conversion_probability(
        self,
        behavioral_signals: List[BehavioralSignal],
        engagement_history: EngagementHistory,
        conversion_stage: ConversionStage
    ) -> float:
        """Calculate conversion probability based on signals and history"""

        base_probability = {
            ConversionStage.AWARENESS: 0.1,
            ConversionStage.INTEREST: 0.2,
            ConversionStage.CONSIDERATION: 0.35,
            ConversionStage.INTENT: 0.55,
            ConversionStage.EVALUATION: 0.75,
            ConversionStage.DECISION: 0.9
        }

        probability = base_probability[conversion_stage]

        # Adjust based on behavioral signal strength
        signal_boost = sum(signal.strength for signal in behavioral_signals) * 0.05
        probability += signal_boost

        # Adjust based on engagement history
        response_rate = engagement_history.response_patterns.get("response_rate", 0.5)
        probability += (response_rate - 0.5) * 0.2

        return min(0.95, max(0.05, probability))

    def _determine_engagement_urgency(
        self,
        behavioral_signals: List[BehavioralSignal],
        conversion_stage: ConversionStage,
        conversion_probability: float
    ) -> EngagementUrgency:
        """Determine engagement urgency level"""

        # Check for critical urgency signals
        for signal in behavioral_signals:
            if signal.signal_type == "urgency_expression" and signal.strength > 0.8:
                return EngagementUrgency.CRITICAL

        # High urgency conditions
        if conversion_stage in [ConversionStage.INTENT, ConversionStage.EVALUATION] and conversion_probability > 0.7:
            return EngagementUrgency.HIGH

        # Medium urgency conditions
        if conversion_stage in [ConversionStage.CONSIDERATION, ConversionStage.INTENT]:
            return EngagementUrgency.MEDIUM

        # High activity signals warrant medium urgency
        high_activity_signals = [s for s in behavioral_signals if s.strength > 0.7]
        if len(high_activity_signals) > 2:
            return EngagementUrgency.MEDIUM

        # Low urgency conditions
        if conversion_stage in [ConversionStage.INTEREST, ConversionStage.CONSIDERATION]:
            return EngagementUrgency.LOW

        # Default to nurture
        return EngagementUrgency.NURTURE

    async def _calculate_optimal_timing(
        self,
        lead_id: str,
        behavioral_signals: List[BehavioralSignal],
        engagement_history: EngagementHistory
    ) -> datetime:
        """Calculate optimal timing for next engagement"""

        base_time = datetime.now()

        # Get preferred time from history
        preferred_time = engagement_history.response_patterns.get("preferred_communication_time", "afternoon")

        # Map to specific hours
        time_ranges = {
            "morning": (9, 11),
            "midday": (12, 14),
            "afternoon": (15, 17),
            "evening": (18, 20)
        }

        start_hour, end_hour = time_ranges.get(preferred_time, (14, 16))

        # Calculate next occurrence of optimal time
        optimal_time = base_time.replace(
            hour=start_hour,
            minute=0,
            second=0,
            microsecond=0
        )

        # If time has passed today, schedule for tomorrow
        if optimal_time <= base_time:
            optimal_time += timedelta(days=1)

        # Adjust based on urgency signals
        urgent_signals = [s for s in behavioral_signals if s.strength > 0.8]
        if urgent_signals:
            # Schedule sooner for urgent signals
            optimal_time = min(optimal_time, base_time + timedelta(hours=2))

        return optimal_time

    async def _determine_optimal_channel(
        self,
        behavioral_signals: List[BehavioralSignal],
        engagement_history: EngagementHistory,
        conversion_stage: ConversionStage
    ) -> EngagementChannel:
        """Determine optimal communication channel"""

        # Get channel preferences from history
        channel_prefs = engagement_history.channel_preferences

        # Adjust based on conversion stage
        stage_channel_modifiers = {
            ConversionStage.AWARENESS: {"email": 1.2, "sms": 1.1},
            ConversionStage.INTEREST: {"sms": 1.2, "phone": 1.1},
            ConversionStage.CONSIDERATION: {"phone": 1.3, "video": 1.2},
            ConversionStage.INTENT: {"phone": 1.4, "video": 1.3},
            ConversionStage.EVALUATION: {"phone": 1.5, "in_person": 1.4},
            ConversionStage.DECISION: {"phone": 1.6, "in_person": 1.5}
        }

        # Apply stage modifiers
        adjusted_prefs = channel_prefs.copy()
        for channel, modifier in stage_channel_modifiers.get(conversion_stage, {}).items():
            if channel in adjusted_prefs:
                adjusted_prefs[channel] *= modifier

        # Check for urgency signals
        urgent_signals = [s for s in behavioral_signals if s.signal_type == "urgency_expression"]
        if urgent_signals:
            adjusted_prefs["phone"] *= 1.5

        # Return channel with highest score
        optimal_channel = max(adjusted_prefs.items(), key=lambda x: x[1])[0]

        # Map to enum
        channel_map = {
            "phone": EngagementChannel.PHONE,
            "sms": EngagementChannel.SMS,
            "email": EngagementChannel.EMAIL,
            "video": EngagementChannel.VIDEO,
            "in_person": EngagementChannel.IN_PERSON
        }

        return channel_map.get(optimal_channel, EngagementChannel.PHONE)

    async def _generate_recommended_message(
        self,
        lead_id: str,
        conversion_stage: ConversionStage,
        current_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate personalized message recommendation"""

        stage_templates = {
            ConversionStage.AWARENESS: "Hi! I saw you've been exploring properties online. I'd love to help you understand the current market and what options might work best for you.",

            ConversionStage.INTEREST: "I noticed you've been looking at several properties in the area. Would you like me to send you some additional options that match your criteria?",

            ConversionStage.CONSIDERATION: "It looks like you're seriously considering some great properties! I'd be happy to schedule a viewing or answer any questions about the neighborhoods.",

            ConversionStage.INTENT: "I can see you're actively evaluating properties. This is a great time to discuss financing options and what we'd need to move forward with an offer.",

            ConversionStage.EVALUATION: "You've done great research on these properties! Let's schedule a time to discuss your top choices and potentially put together a competitive offer.",

            ConversionStage.DECISION: "It looks like you're ready to make a decision! I'm here to help guide you through the offer process and negotiate the best terms."
        }

        base_message = stage_templates.get(conversion_stage, stage_templates[ConversionStage.INTEREST])

        # Add context-specific elements if available
        if current_context:
            location = current_context.get("location", "")
            if location:
                base_message += f" I have some great insights about the {location} market to share with you."

        return base_message

    async def _generate_talking_points(
        self,
        lead_id: str,
        conversion_stage: ConversionStage,
        behavioral_signals: List[BehavioralSignal],
        current_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate key talking points for the conversation"""

        talking_points = []

        # Stage-specific talking points
        stage_points = {
            ConversionStage.AWARENESS: [
                "Explain current market conditions and trends",
                "Understand their timeline and requirements",
                "Introduce your services and expertise"
            ],
            ConversionStage.INTEREST: [
                "Present curated property options",
                "Discuss neighborhood insights and amenities",
                "Explain the viewing process"
            ],
            ConversionStage.CONSIDERATION: [
                "Schedule property viewings",
                "Discuss financing and pre-approval",
                "Address specific property questions"
            ],
            ConversionStage.INTENT: [
                "Review offer strategy and pricing",
                "Discuss closing timeline and process",
                "Address any concerns or objections"
            ],
            ConversionStage.EVALUATION: [
                "Compare property options side-by-side",
                "Discuss negotiation strategies",
                "Plan next steps for making offers"
            ],
            ConversionStage.DECISION: [
                "Guide through offer preparation",
                "Explain contract terms and conditions",
                "Coordinate with lenders and attorneys"
            ]
        }

        talking_points.extend(stage_points.get(conversion_stage, stage_points[ConversionStage.INTEREST]))

        # Add signal-based talking points
        for signal in behavioral_signals:
            if signal.signal_type == "mortgage_calculator_usage":
                talking_points.append("Discuss financing options and connect with preferred lenders")
            elif signal.signal_type == "virtual_tour_engagement":
                talking_points.append("Offer in-person viewing of similar properties")
            elif signal.signal_type == "hot_market_conditions":
                talking_points.append("Emphasize market timing and competitive positioning")

        return talking_points[:4]  # Return top 4 talking points

    def _calculate_confidence_score(
        self,
        behavioral_signals: List[BehavioralSignal],
        engagement_history: EngagementHistory
    ) -> float:
        """Calculate confidence score for the prediction"""

        base_confidence = 0.7

        # Higher confidence with more signals
        signal_boost = min(0.2, len(behavioral_signals) * 0.03)
        base_confidence += signal_boost

        # Higher confidence with strong signals
        strong_signals = [s for s in behavioral_signals if s.strength > 0.7]
        strength_boost = min(0.15, len(strong_signals) * 0.05)
        base_confidence += strength_boost

        # Higher confidence with good response history
        response_rate = engagement_history.response_patterns.get("response_rate", 0.5)
        if response_rate > 0.7:
            base_confidence += 0.1

        return min(0.95, base_confidence)

    def _generate_prediction_reasoning(
        self,
        behavioral_signals: List[BehavioralSignal],
        conversion_stage: ConversionStage,
        urgency: EngagementUrgency
    ) -> List[str]:
        """Generate reasoning for the prediction"""

        reasoning = []

        # Stage reasoning
        reasoning.append(f"Lead is in {conversion_stage.value} stage based on behavioral analysis")

        # Signal reasoning
        strong_signals = [s for s in behavioral_signals if s.strength > 0.7]
        if strong_signals:
            reasoning.append(f"Detected {len(strong_signals)} strong engagement signals")

        # Urgency reasoning
        if urgency == EngagementUrgency.CRITICAL:
            reasoning.append("Critical urgency due to explicit urgency expressions")
        elif urgency == EngagementUrgency.HIGH:
            reasoning.append("High urgency based on conversion readiness and activity")

        # Activity reasoning
        if len(behavioral_signals) > 5:
            reasoning.append("High activity level indicates active property search")

        return reasoning[:3]

    async def _store_prediction(self, prediction: EngagementPrediction):
        """Store prediction for learning and analytics"""
        try:
            if self.redis_service.redis_client:
                prediction_key = f"engagement_prediction:{prediction.lead_id}:{int(datetime.now().timestamp())}"
                prediction_data = {
                    "lead_id": prediction.lead_id,
                    "agent_id": prediction.agent_id,
                    "urgency": prediction.urgency.value,
                    "conversion_probability": prediction.conversion_probability,
                    "confidence_score": prediction.confidence_score,
                    "timestamp": datetime.now().isoformat()
                }

                self.redis_service.redis_client.setex(
                    prediction_key,
                    24 * 60 * 60,  # 24 hour TTL
                    json.dumps(prediction_data)
                )

        except Exception as e:
            logger.warning(f"Could not store prediction: {str(e)}")

    async def _generate_fallback_prediction(self, lead_id: str, agent_id: str) -> EngagementPrediction:
        """Generate fallback prediction when analysis fails"""
        return EngagementPrediction(
            lead_id=lead_id,
            agent_id=agent_id,
            urgency=EngagementUrgency.MEDIUM,
            optimal_time=datetime.now() + timedelta(hours=4),
            conversion_stage=ConversionStage.INTEREST,
            conversion_probability=0.5,
            recommended_channel=EngagementChannel.PHONE,
            recommended_message="Following up on your property search. Would love to help you find the perfect home!",
            key_talking_points=["Understand their needs", "Present property options", "Schedule viewing"],
            confidence_score=0.6,
            reasoning=["Default prediction due to limited data"]
        )

    async def health_check(self) -> Dict[str, Any]:
        """Health check for predictive engagement engine"""
        try:
            start_time = datetime.now()
            test_prediction = await self.predict_optimal_engagement("test_lead", "test_agent")
            response_time = (datetime.now() - start_time).total_seconds()

            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000),
                "redis_available": self.redis_service.redis_client is not None,
                "market_intelligence_available": hasattr(self.market_intelligence, 'get_claude_market_context'),
                "test_confidence": test_prediction.confidence_score,
                "last_test": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global service instance
predictive_engagement_engine = PredictiveEngagementEngine()