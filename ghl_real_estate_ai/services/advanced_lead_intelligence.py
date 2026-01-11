"""
Advanced Lead Intelligence Module

Enhances the chatbot system with sophisticated lead qualification,
real-time scoring, conversation intelligence, and predictive analytics.
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import re

from .chatbot_manager import ChatbotManager, UserType, ConversationStage
from .chat_ml_integration import ChatMLIntegration

logger = logging.getLogger(__name__)


class LeadQualificationLevel(Enum):
    """Lead qualification maturity levels"""
    UNQUALIFIED = "unqualified"
    INITIAL_INTEREST = "initial_interest"
    BASIC_QUALIFIED = "basic_qualified"
    SALES_QUALIFIED = "sales_qualified"
    HOT_PROSPECT = "hot_prospect"


class ConversationIntent(Enum):
    """Detected conversation intents"""
    INFORMATION_GATHERING = "info_gathering"
    PROPERTY_SEARCH = "property_search"
    PRICE_INQUIRY = "price_inquiry"
    TIMELINE_DISCUSSION = "timeline"
    FINANCING_QUESTIONS = "financing"
    NEIGHBORHOOD_RESEARCH = "neighborhood"
    OBJECTION_HANDLING = "objection"
    BOOKING_REQUEST = "booking"
    URGENT_NEED = "urgent"


class ConversationSentiment(Enum):
    """Conversation sentiment analysis"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CONCERNED = "concerned"
    FRUSTRATED = "frustrated"


@dataclass
class LeadQualificationCriteria:
    """Advanced lead qualification framework"""
    # Basic Info (0-25 points)
    has_name: bool = False
    has_contact_info: bool = False
    has_location_preference: bool = False

    # Financial Qualification (0-30 points)
    has_budget_range: bool = False
    has_financing_info: bool = False
    pre_approved: bool = False

    # Motivation & Timeline (0-25 points)
    has_timeline: bool = False
    has_motivation: bool = False
    urgency_level: int = 0  # 1-10

    # Property Criteria (0-20 points)
    has_property_type: bool = False
    has_size_requirements: bool = False
    has_features_list: bool = False

    def calculate_score(self) -> int:
        """Calculate qualification score (0-100)"""
        score = 0

        # Basic Info (25 points max)
        basic_score = sum([self.has_name, self.has_contact_info, self.has_location_preference]) * 8.33
        score += min(25, basic_score)

        # Financial (30 points max)
        financial_score = (
            self.has_budget_range * 10 +
            self.has_financing_info * 10 +
            self.pre_approved * 10
        )
        score += financial_score

        # Motivation (25 points max)
        motivation_score = (
            self.has_timeline * 10 +
            self.has_motivation * 10 +
            self.urgency_level * 0.5  # 0-5 points
        )
        score += motivation_score

        # Property Criteria (20 points max)
        property_score = sum([
            self.has_property_type,
            self.has_size_requirements,
            self.has_features_list
        ]) * 6.67
        score += min(20, property_score)

        return min(100, int(score))


@dataclass
class ConversationIntelligence:
    """Real-time conversation analysis"""
    message_count: int = 0
    avg_response_time: float = 0.0
    engagement_score: float = 0.0
    sentiment: ConversationSentiment = ConversationSentiment.NEUTRAL
    detected_intents: List[ConversationIntent] = None
    urgency_signals: List[str] = None
    objection_signals: List[str] = None
    buying_signals: List[str] = None

    def __post_init__(self):
        if self.detected_intents is None:
            self.detected_intents = []
        if self.urgency_signals is None:
            self.urgency_signals = []
        if self.objection_signals is None:
            self.objection_signals = []
        if self.buying_signals is None:
            self.buying_signals = []


@dataclass
class FollowUpRecommendation:
    """Intelligent follow-up suggestions"""
    priority: int  # 1-10
    action_type: str
    suggested_message: str
    timing_delay: timedelta
    reasoning: str
    success_probability: float


class AdvancedLeadIntelligence:
    """
    Advanced lead intelligence system for enhanced chatbot capabilities.

    Features:
    - Multi-dimensional lead qualification
    - Real-time conversation intelligence
    - Predictive lead scoring
    - Intelligent follow-up recommendations
    - Advanced analytics and insights
    """

    def __init__(self, chatbot_manager: ChatbotManager, ml_integration: ChatMLIntegration):
        self.chatbot_manager = chatbot_manager
        self.ml_integration = ml_integration

        # Intelligence tracking
        self.qualification_data: Dict[str, LeadQualificationCriteria] = {}
        self.conversation_intelligence: Dict[str, ConversationIntelligence] = {}

        # Pattern recognition for advanced analysis
        self._initialize_patterns()

        logger.info("Advanced Lead Intelligence system initialized")

    def _initialize_patterns(self):
        """Initialize pattern recognition for conversation analysis"""
        self.intent_patterns = {
            ConversationIntent.PRICE_INQUIRY: [
                r'\b(?:price|cost|expensive|affordable|budget|how much)\b',
                r'\$[\d,]+',
                r'\b(?:thousand|million|k)\b'
            ],
            ConversationIntent.TIMELINE_DISCUSSION: [
                r'\b(?:when|timeline|soon|asap|immediately|month|year)\b',
                r'\b(?:moving|relocating|buying|selling)\b.*\b(?:by|before|within)\b'
            ],
            ConversationIntent.FINANCING_QUESTIONS: [
                r'\b(?:mortgage|loan|financing|pre-approved|down payment|interest rate)\b',
                r'\b(?:bank|lender|credit|qualify)\b'
            ],
            ConversationIntent.URGENT_NEED: [
                r'\b(?:urgent|immediately|asap|emergency|quick|fast|need now)\b',
                r'\b(?:closing soon|contract|deadline)\b'
            ]
        }

        self.sentiment_patterns = {
            ConversationSentiment.VERY_POSITIVE: [
                r'\b(?:love|amazing|perfect|exactly|dream|ideal|wonderful)\b',
                r'\b(?:excited|thrilled|can\'t wait)\b'
            ],
            ConversationSentiment.FRUSTRATED: [
                r'\b(?:frustrated|annoyed|tired|giving up|difficult|problem)\b',
                r'\b(?:waste|time|disappointing|not working)\b'
            ],
            ConversationSentiment.CONCERNED: [
                r'\b(?:worried|concern|nervous|unsure|hesitant|doubt)\b',
                r'\b(?:risk|problem|issue|challenge)\b'
            ]
        }

        self.urgency_signals = [
            r'\b(?:moving|relocating).*(?:next month|weeks?|soon)\b',
            r'\b(?:lease|rent).*(?:ending|expires?|up)\b',
            r'\b(?:job|work|transfer).*(?:starting|new|relocating)\b',
            r'\b(?:closing|sold).*(?:home|house|property)\b'
        ]

        self.buying_signals = [
            r'\b(?:ready|prepared|looking).*(?:to buy|purchase|move forward)\b',
            r'\b(?:pre-approved|approved|financing|mortgage).*(?:ready|in place)\b',
            r'\b(?:schedule|book|arrange).*(?:viewing|showing|tour|visit)\b',
            r'\b(?:put|make).*(?:offer|bid)\b'
        ]

        self.objection_signals = [
            r'\b(?:too expensive|can\'t afford|out of budget|over priced)\b',
            r'\b(?:not sure|maybe|thinking about it|need time)\b',
            r'\b(?:compare|other|competition|shopping around)\b',
            r'\b(?:commission|fees?).*(?:high|expensive|too much)\b'
        ]

    async def analyze_conversation_turn(
        self,
        user_id: str,
        tenant_id: str,
        message_content: str,
        response_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """Analyze a single conversation turn for intelligence insights"""

        conversation_key = f"{tenant_id}:{user_id}"

        # Initialize tracking if needed
        if conversation_key not in self.conversation_intelligence:
            self.conversation_intelligence[conversation_key] = ConversationIntelligence()

        if conversation_key not in self.qualification_data:
            self.qualification_data[conversation_key] = LeadQualificationCriteria()

        intel = self.conversation_intelligence[conversation_key]
        qual = self.qualification_data[conversation_key]

        # Update basic metrics
        intel.message_count += 1
        if response_time:
            intel.avg_response_time = (
                (intel.avg_response_time * (intel.message_count - 1) + response_time)
                / intel.message_count
            )

        # Analyze message content
        analysis_result = await self._analyze_message_content(message_content, qual, intel)

        # Update qualification score
        qualification_score = qual.calculate_score()

        # Generate intelligence insights
        insights = {
            "qualification_score": qualification_score,
            "qualification_level": self._get_qualification_level(qualification_score),
            "conversation_intelligence": asdict(intel),
            "detected_intents": [intent.value for intent in intel.detected_intents],
            "sentiment": intel.sentiment.value,
            "urgency_level": qual.urgency_level,
            "analysis_result": analysis_result,
            "timestamp": datetime.now().isoformat()
        }

        return insights

    async def _analyze_message_content(
        self,
        message: str,
        qualification: LeadQualificationCriteria,
        intelligence: ConversationIntelligence
    ) -> Dict[str, Any]:
        """Detailed message content analysis"""

        message_lower = message.lower()
        analysis = {
            "qualification_updates": [],
            "detected_patterns": [],
            "extracted_entities": []
        }

        # Intent Detection
        detected_intents = []
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    detected_intents.append(intent)
                    analysis["detected_patterns"].append(f"Intent: {intent.value}")

        intelligence.detected_intents = list(set(intelligence.detected_intents + detected_intents))

        # Sentiment Analysis
        sentiment_score = 0
        for sentiment, patterns in self.sentiment_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    if sentiment == ConversationSentiment.VERY_POSITIVE:
                        sentiment_score += 2
                    elif sentiment == ConversationSentiment.FRUSTRATED:
                        sentiment_score -= 2
                    elif sentiment == ConversationSentiment.CONCERNED:
                        sentiment_score -= 1

        # Update sentiment based on score
        if sentiment_score >= 2:
            intelligence.sentiment = ConversationSentiment.VERY_POSITIVE
        elif sentiment_score >= 1:
            intelligence.sentiment = ConversationSentiment.POSITIVE
        elif sentiment_score <= -2:
            intelligence.sentiment = ConversationSentiment.FRUSTRATED
        elif sentiment_score <= -1:
            intelligence.sentiment = ConversationSentiment.CONCERNED
        else:
            intelligence.sentiment = ConversationSentiment.NEUTRAL

        # Signal Detection
        for pattern in self.urgency_signals:
            if re.search(pattern, message_lower):
                urgency_text = re.search(pattern, message_lower).group()
                intelligence.urgency_signals.append(urgency_text)
                qualification.urgency_level = min(10, qualification.urgency_level + 2)
                analysis["detected_patterns"].append(f"Urgency: {urgency_text}")

        for pattern in self.buying_signals:
            if re.search(pattern, message_lower):
                buying_text = re.search(pattern, message_lower).group()
                intelligence.buying_signals.append(buying_text)
                analysis["detected_patterns"].append(f"Buying Signal: {buying_text}")

        for pattern in self.objection_signals:
            if re.search(pattern, message_lower):
                objection_text = re.search(pattern, message_lower).group()
                intelligence.objection_signals.append(objection_text)
                analysis["detected_patterns"].append(f"Objection: {objection_text}")

        # Entity Extraction for Qualification
        await self._extract_qualification_entities(message, qualification, analysis)

        return analysis

    async def _extract_qualification_entities(
        self,
        message: str,
        qualification: LeadQualificationCriteria,
        analysis: Dict[str, Any]
    ):
        """Extract qualification entities from message"""

        message_lower = message.lower()

        # Name detection
        if not qualification.has_name:
            name_patterns = [
                r'\b(?:my name is|i\'m|i am|call me)\s+([a-z]+)\b',
                r'\b([A-Z][a-z]+)\s+speaking\b'
            ]
            for pattern in name_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    qualification.has_name = True
                    analysis["qualification_updates"].append("Name captured")
                    analysis["extracted_entities"].append(f"Name: {match.group(1)}")
                    break

        # Contact info detection
        if not qualification.has_contact_info:
            contact_patterns = [
                r'\b[\d\-\(\)\s]{10,}\b',  # Phone
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
            ]
            for pattern in contact_patterns:
                if re.search(pattern, message):
                    qualification.has_contact_info = True
                    analysis["qualification_updates"].append("Contact info captured")
                    break

        # Budget detection
        if not qualification.has_budget_range:
            budget_patterns = [
                r'\$[\d,]+',
                r'\b\d+k?\b.*(?:budget|afford|spend)',
                r'(?:budget|afford|spend).*\$?[\d,]+k?'
            ]
            for pattern in budget_patterns:
                if re.search(pattern, message_lower):
                    qualification.has_budget_range = True
                    analysis["qualification_updates"].append("Budget range captured")
                    break

        # Timeline detection
        if not qualification.has_timeline:
            timeline_patterns = [
                r'\b(?:next|within|by)\s+(?:\d+)?\s*(?:month|year|week)s?\b',
                r'\b(?:soon|immediately|asap|quick)\b'
            ]
            for pattern in timeline_patterns:
                if re.search(pattern, message_lower):
                    qualification.has_timeline = True
                    analysis["qualification_updates"].append("Timeline captured")
                    break

        # Location preference
        if not qualification.has_location_preference:
            location_patterns = [
                r'\b(?:in|near|around|close to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
                r'\b([A-Z][a-z]+)\s+(?:area|neighborhood|district)\b'
            ]
            for pattern in location_patterns:
                match = re.search(pattern, message)
                if match:
                    qualification.has_location_preference = True
                    analysis["qualification_updates"].append("Location preference captured")
                    analysis["extracted_entities"].append(f"Location: {match.group(1)}")
                    break

        # Property type detection
        if not qualification.has_property_type:
            property_patterns = [
                r'\b(?:house|home|condo|apartment|townhouse|mansion|villa)\b'
            ]
            for pattern in property_patterns:
                if re.search(pattern, message_lower):
                    qualification.has_property_type = True
                    analysis["qualification_updates"].append("Property type captured")
                    break

        # Financing info
        if not qualification.has_financing_info:
            financing_patterns = [
                r'\b(?:pre-approved|approved|mortgage|loan|financing|cash)\b'
            ]
            for pattern in financing_patterns:
                if re.search(pattern, message_lower):
                    qualification.has_financing_info = True
                    analysis["qualification_updates"].append("Financing info captured")
                    if "pre-approved" in message_lower or "approved" in message_lower:
                        qualification.pre_approved = True
                    break

    def _get_qualification_level(self, score: int) -> LeadQualificationLevel:
        """Determine qualification level based on score"""
        if score >= 80:
            return LeadQualificationLevel.HOT_PROSPECT
        elif score >= 60:
            return LeadQualificationLevel.SALES_QUALIFIED
        elif score >= 40:
            return LeadQualificationLevel.BASIC_QUALIFIED
        elif score >= 20:
            return LeadQualificationLevel.INITIAL_INTEREST
        else:
            return LeadQualificationLevel.UNQUALIFIED

    async def generate_follow_up_recommendations(
        self,
        user_id: str,
        tenant_id: str
    ) -> List[FollowUpRecommendation]:
        """Generate intelligent follow-up recommendations"""

        conversation_key = f"{tenant_id}:{user_id}"

        if (conversation_key not in self.qualification_data or
            conversation_key not in self.conversation_intelligence):
            return []

        qual = self.qualification_data[conversation_key]
        intel = self.conversation_intelligence[conversation_key]

        recommendations = []

        # Score-based recommendations
        score = qual.calculate_score()

        if score >= 70:
            # High-qualified lead recommendations
            if intel.buying_signals:
                recommendations.append(FollowUpRecommendation(
                    priority=9,
                    action_type="schedule_call",
                    suggested_message="I noticed you're ready to move forward. Would you like to schedule a call to discuss your next steps?",
                    timing_delay=timedelta(hours=1),
                    reasoning="Strong buying signals detected",
                    success_probability=0.8
                ))

            if ConversationIntent.PROPERTY_SEARCH in intel.detected_intents:
                recommendations.append(FollowUpRecommendation(
                    priority=8,
                    action_type="send_listings",
                    suggested_message="Based on our conversation, I found some properties that match your criteria perfectly. Would you like me to send them over?",
                    timing_delay=timedelta(hours=2),
                    reasoning="Property search intent with high qualification",
                    success_probability=0.75
                ))

        elif score >= 40:
            # Mid-qualified lead recommendations
            if not qual.has_budget_range:
                recommendations.append(FollowUpRecommendation(
                    priority=6,
                    action_type="budget_qualification",
                    suggested_message="To help me find the perfect options for you, what budget range are you comfortable with?",
                    timing_delay=timedelta(hours=4),
                    reasoning="Missing budget information for qualified lead",
                    success_probability=0.6
                ))

            if not qual.has_timeline:
                recommendations.append(FollowUpRecommendation(
                    priority=5,
                    action_type="timeline_qualification",
                    suggested_message="When are you hoping to make your move?",
                    timing_delay=timedelta(hours=6),
                    reasoning="Missing timeline information",
                    success_probability=0.5
                ))

        else:
            # Low-qualified lead recommendations
            recommendations.append(FollowUpRecommendation(
                priority=3,
                action_type="nurture_content",
                suggested_message="I thought you might find this market report interesting. It shows current trends in your area of interest.",
                timing_delay=timedelta(days=1),
                reasoning="Low qualification - focus on nurturing",
                success_probability=0.3
            ))

        # Sentiment-based recommendations
        if intel.sentiment == ConversationSentiment.FRUSTRATED:
            recommendations.append(FollowUpRecommendation(
                priority=7,
                action_type="address_concerns",
                suggested_message="I want to make sure we address any concerns you might have. Is there something specific I can help clarify?",
                timing_delay=timedelta(hours=3),
                reasoning="Frustrated sentiment detected",
                success_probability=0.4
            ))

        # Urgency-based recommendations
        if qual.urgency_level >= 7:
            recommendations.append(FollowUpRecommendation(
                priority=10,
                action_type="urgent_response",
                suggested_message="I understand this is time-sensitive. Let me connect you with our senior agent who can expedite your search.",
                timing_delay=timedelta(minutes=30),
                reasoning="High urgency detected",
                success_probability=0.9
            ))

        # Sort by priority and return top recommendations
        recommendations.sort(key=lambda x: x.priority, reverse=True)
        return recommendations[:5]

    async def get_conversation_analytics(
        self,
        tenant_id: str,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """Get comprehensive conversation analytics"""

        analytics = {
            "total_conversations": 0,
            "qualification_distribution": {},
            "intent_distribution": {},
            "sentiment_distribution": {},
            "average_qualification_score": 0,
            "conversion_predictions": {},
            "top_objections": [],
            "engagement_metrics": {}
        }

        # Analyze all conversations for tenant
        qualification_scores = []
        all_intents = []
        all_sentiments = []
        all_objections = []

        for conv_key, intel in self.conversation_intelligence.items():
            if conv_key.startswith(f"{tenant_id}:"):
                analytics["total_conversations"] += 1

                # Get qualification data
                if conv_key in self.qualification_data:
                    qual = self.qualification_data[conv_key]
                    score = qual.calculate_score()
                    qualification_scores.append(score)

                    level = self._get_qualification_level(score)
                    analytics["qualification_distribution"][level.value] = (
                        analytics["qualification_distribution"].get(level.value, 0) + 1
                    )

                # Collect intents
                all_intents.extend([intent.value for intent in intel.detected_intents])

                # Collect sentiments
                all_sentiments.append(intel.sentiment.value)

                # Collect objections
                all_objections.extend(intel.objection_signals)

        # Calculate distributions
        if qualification_scores:
            analytics["average_qualification_score"] = sum(qualification_scores) / len(qualification_scores)

        # Intent distribution
        from collections import Counter
        intent_counts = Counter(all_intents)
        analytics["intent_distribution"] = dict(intent_counts.most_common(10))

        # Sentiment distribution
        sentiment_counts = Counter(all_sentiments)
        analytics["sentiment_distribution"] = dict(sentiment_counts)

        # Top objections
        objection_counts = Counter(all_objections)
        analytics["top_objections"] = [
            {"objection": obj, "count": count}
            for obj, count in objection_counts.most_common(5)
        ]

        return analytics

    async def suggest_conversation_improvements(
        self,
        user_id: str,
        tenant_id: str
    ) -> List[str]:
        """Suggest improvements for ongoing conversation"""

        conversation_key = f"{tenant_id}:{user_id}"
        suggestions = []

        if conversation_key not in self.qualification_data:
            return ["Start basic qualification process"]

        qual = self.qualification_data[conversation_key]
        intel = self.conversation_intelligence[conversation_key]

        # Qualification gap analysis
        if not qual.has_name:
            suggestions.append("Ask for the lead's name to personalize the conversation")

        if not qual.has_contact_info:
            suggestions.append("Collect contact information for follow-up")

        if not qual.has_budget_range:
            suggestions.append("Understand their budget to qualify properly")

        if not qual.has_timeline:
            suggestions.append("Determine their timeline to prioritize urgency")

        if not qual.has_location_preference:
            suggestions.append("Ask about preferred neighborhoods or areas")

        # Behavioral analysis suggestions
        if intel.sentiment == ConversationSentiment.FRUSTRATED:
            suggestions.append("Address concerns or frustrations immediately")

        if intel.objection_signals:
            suggestions.append("Handle objections with empathy and solutions")

        if intel.buying_signals and qual.calculate_score() < 50:
            suggestions.append("Accelerate qualification - buying signals detected but low score")

        if qual.urgency_level >= 5 and intel.message_count > 10:
            suggestions.append("Consider escalating to senior agent due to urgency")

        return suggestions[:5]


async def integrate_advanced_intelligence(
    chatbot_manager: ChatbotManager,
    ml_integration: ChatMLIntegration
) -> AdvancedLeadIntelligence:
    """Factory function to create and integrate advanced intelligence system"""

    intelligence_system = AdvancedLeadIntelligence(chatbot_manager, ml_integration)

    # Enhance the existing chatbot manager with intelligence hooks
    original_process_message = chatbot_manager.process_message

    async def enhanced_process_message(
        user_id: str,
        tenant_id: str,
        message_content: str,
        session_id: Optional[str] = None,
        user_type: Optional[UserType] = None
    ):
        """Enhanced message processing with intelligence analysis"""

        # Record processing start time
        start_time = datetime.now()

        # Process message normally
        response, metadata = await original_process_message(
            user_id, tenant_id, message_content, session_id, user_type
        )

        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()

        # Run intelligence analysis
        try:
            intelligence_insights = await intelligence_system.analyze_conversation_turn(
                user_id, tenant_id, message_content, response_time
            )

            # Add intelligence data to response metadata
            metadata["intelligence"] = intelligence_insights

            # Add follow-up recommendations if high priority
            if intelligence_insights["qualification_score"] >= 60:
                recommendations = await intelligence_system.generate_follow_up_recommendations(
                    user_id, tenant_id
                )
                metadata["follow_up_recommendations"] = [
                    asdict(rec) for rec in recommendations[:3]
                ]

        except Exception as e:
            logger.warning(f"Intelligence analysis failed: {str(e)}")

        return response, metadata

    # Replace the process_message method
    chatbot_manager.process_message = enhanced_process_message

    return intelligence_system