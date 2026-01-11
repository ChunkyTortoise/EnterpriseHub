"""
Seller-Claude Intelligence Integration Service

Advanced intelligence layer specifically designed for seller interactions through Claude AI.
Provides contextual market insights, conversation-driven analytics, and intelligent
decision support for real estate sellers.

Business Impact: Enhanced seller conversion rates, reduced time-to-list, improved pricing accuracy
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

from .real_time_market_intelligence import (
    RealTimeMarketIntelligence,
    MarketIntelligenceReport,
    PriceIntelligence,
    MarketTrend,
    MarketTiming
)
from .claude_seller_agent import SellerContext, ConversationIntent
from .intelligent_seller_nurturing import NurturingTrigger, SellerProfile
from .advanced_cache_optimization import advanced_cache
from ..models.seller_models import (
    SellerLead, SellerProperty, SellerGoals,
    MarketInsight, ConversationContext
)
from ..utils.ai_insights_generator import generate_ai_insights
from ..utils.conversation_analyzer import analyze_conversation_sentiment

logger = logging.getLogger(__name__)


class SellerReadinessLevel(Enum):
    """Seller readiness to list property"""
    NOT_READY = "not_ready"           # Just exploring, 3+ months out
    CONSIDERING = "considering"       # Serious interest, 1-3 months
    ACTIVELY_PREPARING = "preparing"  # Committed to selling, <1 month
    READY_TO_LIST = "ready_to_list"   # Ready for immediate listing
    URGENT = "urgent"                 # Time-sensitive selling need


class SellerMotivation(Enum):
    """Primary seller motivation categories"""
    UPSIZING = "upsizing"             # Growing family, need more space
    DOWNSIZING = "downsizing"         # Empty nesters, simpler living
    RELOCATION = "relocation"         # Job change, lifestyle change
    FINANCIAL = "financial"           # Debt relief, investment liquidation
    LIFESTYLE = "lifestyle"           # Neighborhood change, amenity access
    INVESTMENT = "investment"         # Portfolio optimization
    URGENT = "urgent"                 # Divorce, job loss, financial stress


@dataclass
class SellerIntelligenceProfile:
    """Comprehensive seller intelligence profile"""
    seller_id: str
    readiness_level: SellerReadinessLevel
    motivation: SellerMotivation
    timeline_urgency: float  # 0-1 scale
    price_flexibility: float  # 0-1 scale (how flexible on price)
    market_knowledge: float  # 0-1 scale (how much they know)

    # Property characteristics
    property_type: str
    property_value_estimate: Optional[int]
    property_condition: str  # excellent, good, fair, needs_work
    unique_selling_points: List[str]
    potential_concerns: List[str]

    # Market position
    competitive_advantage_score: float  # 0-100
    pricing_competitiveness: float  # 0-100
    market_timing_score: float  # 0-100

    # Conversation insights
    conversation_sentiment: float  # -1 to 1 (negative to positive)
    engagement_level: float  # 0-1 scale
    question_frequency: float  # Questions per conversation
    objection_patterns: List[str]

    # Behavioral indicators
    research_depth: float  # 0-1 (how much research they've done)
    decision_confidence: float  # 0-1 (confidence in selling decision)
    agent_trust_level: float  # 0-1 (trust in agent/process)

    last_updated: datetime


@dataclass
class SellerConversationInsight:
    """Insights extracted from seller conversations"""
    conversation_id: str
    seller_id: str
    timestamp: datetime

    # Intent analysis
    primary_intent: ConversationIntent
    secondary_intents: List[ConversationIntent]
    intent_confidence: float

    # Information extracted
    new_property_details: Dict[str, Any]
    timeline_updates: Optional[Dict[str, Any]]
    motivation_updates: Optional[Dict[str, Any]]
    concerns_identified: List[str]

    # Emotional analysis
    sentiment_score: float  # -1 to 1
    confidence_level: float  # 0-1
    stress_indicators: List[str]
    excitement_indicators: List[str]

    # Market context awareness
    market_awareness_level: float  # 0-1
    pricing_expectations: Optional[Dict[str, Any]]
    competition_awareness: bool

    # Action indicators
    readiness_to_proceed: float  # 0-1
    need_for_education: float  # 0-1
    urgency_level: float  # 0-1

    # Recommendations
    suggested_next_actions: List[str]
    recommended_talking_points: List[str]
    warning_flags: List[str]


@dataclass
class ClaudeMarketContext:
    """Market context formatted specifically for Claude conversations"""
    summary_message: str
    key_talking_points: List[str]
    pricing_context: str
    timing_context: str
    competition_context: str

    # Supporting data for deeper discussions
    detailed_insights: Dict[str, Any]
    conversation_starters: List[str]
    objection_responses: Dict[str, str]

    # Contextual recommendations
    immediate_actions: List[str]
    strategic_considerations: List[str]
    risk_mitigation: List[str]


class SellerClaudeIntelligence:
    """
    Advanced intelligence service for seller-Claude interactions.

    Provides contextual market insights, conversation analytics, and intelligent
    decision support specifically designed for Claude AI conversations with sellers.
    """

    def __init__(self, market_intelligence: RealTimeMarketIntelligence):
        self.market_intelligence = market_intelligence
        self.conversation_analyzer = None  # Initialize conversation analysis AI
        self.insight_generator = None  # Initialize AI insight generator

        # Intelligence caching
        self.cache_ttl = {
            'profile': 3600,  # 1 hour
            'insights': 1800,  # 30 minutes
            'market_context': 900,  # 15 minutes
            'conversation': 300   # 5 minutes
        }

    async def analyze_seller_conversation(
        self,
        conversation_text: str,
        seller_context: SellerContext,
        previous_insights: Optional[List[SellerConversationInsight]] = None
    ) -> SellerConversationInsight:
        """
        Analyze seller conversation and extract actionable insights
        """
        try:
            # Extract conversation metadata
            conversation_id = f"conv_{seller_context.lead_id}_{int(datetime.utcnow().timestamp())}"

            # Analyze conversation intent using Claude
            intent_analysis = await self._analyze_conversation_intent(
                conversation_text, seller_context
            )

            # Extract property and timeline information
            property_updates = await self._extract_property_information(
                conversation_text, seller_context
            )

            # Analyze emotional indicators
            emotional_analysis = await self._analyze_conversation_emotions(
                conversation_text, seller_context
            )

            # Assess market awareness and knowledge level
            market_awareness = await self._assess_market_awareness(
                conversation_text, seller_context
            )

            # Identify concerns and objections
            concerns = await self._identify_seller_concerns(
                conversation_text, seller_context
            )

            # Generate actionable recommendations
            recommendations = await self._generate_conversation_recommendations(
                intent_analysis, property_updates, emotional_analysis,
                market_awareness, concerns, seller_context
            )

            insight = SellerConversationInsight(
                conversation_id=conversation_id,
                seller_id=seller_context.lead_id,
                timestamp=datetime.utcnow(),
                primary_intent=intent_analysis['primary_intent'],
                secondary_intents=intent_analysis['secondary_intents'],
                intent_confidence=intent_analysis['confidence'],
                new_property_details=property_updates['details'],
                timeline_updates=property_updates.get('timeline'),
                motivation_updates=property_updates.get('motivation'),
                concerns_identified=concerns['concerns'],
                sentiment_score=emotional_analysis['sentiment'],
                confidence_level=emotional_analysis['confidence'],
                stress_indicators=emotional_analysis['stress_indicators'],
                excitement_indicators=emotional_analysis['excitement_indicators'],
                market_awareness_level=market_awareness['awareness_level'],
                pricing_expectations=market_awareness.get('pricing_expectations'),
                competition_awareness=market_awareness['competition_awareness'],
                readiness_to_proceed=recommendations['readiness_score'],
                need_for_education=recommendations['education_need'],
                urgency_level=recommendations['urgency_level'],
                suggested_next_actions=recommendations['next_actions'],
                recommended_talking_points=recommendations['talking_points'],
                warning_flags=recommendations['warning_flags']
            )

            # Update seller intelligence profile
            await self._update_seller_intelligence_profile(insight, seller_context)

            logger.info(f"Conversation analysis completed for seller {seller_context.lead_id}")
            return insight

        except Exception as e:
            logger.error(f"Conversation analysis failed: {e}")
            # Return minimal insight
            return SellerConversationInsight(
                conversation_id=f"conv_{seller_context.lead_id}_{int(datetime.utcnow().timestamp())}",
                seller_id=seller_context.lead_id,
                timestamp=datetime.utcnow(),
                primary_intent=ConversationIntent.INFORMATION_GATHERING,
                secondary_intents=[],
                intent_confidence=0.3,
                new_property_details={},
                concerns_identified=[],
                sentiment_score=0.0,
                confidence_level=0.0,
                stress_indicators=[],
                excitement_indicators=[],
                market_awareness_level=0.5,
                competition_awareness=False,
                readiness_to_proceed=0.5,
                need_for_education=0.7,
                urgency_level=0.3,
                suggested_next_actions=["Gather more seller information"],
                recommended_talking_points=["Ask about property details and timeline"],
                warning_flags=["Limited conversation data available"]
            )

    async def get_claude_market_context(
        self,
        seller_context: SellerContext,
        conversation_intent: ConversationIntent,
        include_deep_insights: bool = False
    ) -> ClaudeMarketContext:
        """
        Generate market context specifically formatted for Claude conversations
        """
        try:
            cache_key = f"claude_context_{seller_context.lead_id}_{conversation_intent.value}"

            # Check cache first
            cached_context = await self._get_cached_context(cache_key)
            if cached_context and not include_deep_insights:
                return ClaudeMarketContext(**cached_context)

            # Get property information
            property_data = await self._get_seller_property_data(seller_context)

            # Get comprehensive market analysis
            market_report = await self.market_intelligence.analyze_market(
                property_data.get('area', 'Austin'),
                depth="comprehensive" if include_deep_insights else "standard"
            )

            # Generate conversation-specific context
            context = await self._format_market_context_for_claude(
                market_report, seller_context, conversation_intent, property_data
            )

            # Cache for future use
            await self._cache_claude_context(cache_key, context)

            return context

        except Exception as e:
            logger.error(f"Failed to generate Claude market context: {e}")
            return await self._generate_fallback_context(seller_context, conversation_intent)

    async def get_seller_intelligence_profile(
        self,
        seller_context: SellerContext,
        refresh: bool = False
    ) -> SellerIntelligenceProfile:
        """
        Get or build comprehensive seller intelligence profile
        """
        try:
            cache_key = f"seller_profile_{seller_context.lead_id}"

            if not refresh:
                cached_profile = await self._get_cached_profile(cache_key)
                if cached_profile:
                    return SellerIntelligenceProfile(**cached_profile)

            # Build comprehensive profile
            profile = await self._build_seller_intelligence_profile(seller_context)

            # Cache profile
            await self._cache_seller_profile(cache_key, profile)

            return profile

        except Exception as e:
            logger.error(f"Failed to get seller intelligence profile: {e}")
            return await self._generate_default_profile(seller_context)

    async def get_conversation_recommendations(
        self,
        seller_context: SellerContext,
        recent_insights: List[SellerConversationInsight],
        market_context: Optional[ClaudeMarketContext] = None
    ) -> Dict[str, Any]:
        """
        Generate intelligent conversation recommendations for Claude
        """
        try:
            # Get seller profile
            profile = await self.get_seller_intelligence_profile(seller_context)

            # Get market context if not provided
            if not market_context:
                market_context = await self.get_claude_market_context(
                    seller_context, ConversationIntent.CONSULTATION
                )

            # Analyze conversation history patterns
            conversation_patterns = await self._analyze_conversation_patterns(recent_insights)

            # Generate personalized recommendations
            recommendations = await self._generate_personalized_recommendations(
                profile, conversation_patterns, market_context
            )

            return {
                'immediate_priorities': recommendations['immediate'],
                'conversation_starters': recommendations['starters'],
                'key_questions': recommendations['questions'],
                'objection_handlers': recommendations['objections'],
                'market_talking_points': recommendations['market_points'],
                'next_best_actions': recommendations['actions'],
                'timing_considerations': recommendations['timing'],
                'risk_mitigation': recommendations['risks']
            }

        except Exception as e:
            logger.error(f"Failed to generate conversation recommendations: {e}")
            return await self._generate_fallback_recommendations(seller_context)

    async def track_seller_engagement(
        self,
        seller_context: SellerContext,
        engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track and analyze seller engagement patterns for intelligence
        """
        try:
            engagement_metrics = {
                'conversation_frequency': engagement_data.get('conversations_per_week', 1),
                'response_time': engagement_data.get('avg_response_time_hours', 24),
                'message_length': engagement_data.get('avg_message_length', 50),
                'question_ratio': engagement_data.get('questions_per_message', 0.2),
                'emotional_engagement': engagement_data.get('sentiment_trend', 0.0),
                'topic_diversity': engagement_data.get('unique_topics_discussed', 3),
                'decision_indicators': engagement_data.get('commitment_statements', 0)
            }

            # Calculate engagement score
            engagement_score = await self._calculate_engagement_score(engagement_metrics)

            # Identify engagement trends
            engagement_trends = await self._analyze_engagement_trends(
                seller_context, engagement_metrics
            )

            # Generate engagement insights
            insights = await self._generate_engagement_insights(
                engagement_score, engagement_trends, seller_context
            )

            return {
                'engagement_score': engagement_score,
                'trends': engagement_trends,
                'insights': insights,
                'recommendations': await self._get_engagement_recommendations(
                    engagement_score, engagement_trends
                )
            }

        except Exception as e:
            logger.error(f"Seller engagement tracking failed: {e}")
            return {'error': 'Engagement tracking temporarily unavailable'}

    # Private helper methods for conversation analysis

    async def _analyze_conversation_intent(
        self,
        conversation_text: str,
        seller_context: SellerContext
    ) -> Dict[str, Any]:
        """Analyze conversation intent using AI"""
        # This would use Claude or another AI to analyze intent
        # Placeholder implementation
        return {
            'primary_intent': ConversationIntent.INFORMATION_GATHERING,
            'secondary_intents': [ConversationIntent.MARKET_RESEARCH],
            'confidence': 0.85
        }

    async def _extract_property_information(
        self,
        conversation_text: str,
        seller_context: SellerContext
    ) -> Dict[str, Any]:
        """Extract property details from conversation"""
        # AI-powered information extraction
        return {
            'details': {},
            'timeline': None,
            'motivation': None
        }

    async def _analyze_conversation_emotions(
        self,
        conversation_text: str,
        seller_context: SellerContext
    ) -> Dict[str, Any]:
        """Analyze emotional indicators in conversation"""
        return {
            'sentiment': 0.2,
            'confidence': 0.7,
            'stress_indicators': [],
            'excitement_indicators': []
        }

    async def _assess_market_awareness(
        self,
        conversation_text: str,
        seller_context: SellerContext
    ) -> Dict[str, Any]:
        """Assess seller's market knowledge level"""
        return {
            'awareness_level': 0.6,
            'pricing_expectations': None,
            'competition_awareness': False
        }

    async def _identify_seller_concerns(
        self,
        conversation_text: str,
        seller_context: SellerContext
    ) -> Dict[str, Any]:
        """Identify seller concerns and objections"""
        return {
            'concerns': []
        }

    async def _generate_conversation_recommendations(
        self,
        intent_analysis: Dict,
        property_updates: Dict,
        emotional_analysis: Dict,
        market_awareness: Dict,
        concerns: Dict,
        seller_context: SellerContext
    ) -> Dict[str, Any]:
        """Generate actionable recommendations from analysis"""
        return {
            'readiness_score': 0.6,
            'education_need': 0.4,
            'urgency_level': 0.3,
            'next_actions': ["Schedule property evaluation"],
            'talking_points': ["Discuss current market conditions"],
            'warning_flags': []
        }

    async def _build_seller_intelligence_profile(
        self,
        seller_context: SellerContext
    ) -> SellerIntelligenceProfile:
        """Build comprehensive seller intelligence profile"""
        return SellerIntelligenceProfile(
            seller_id=seller_context.lead_id,
            readiness_level=SellerReadinessLevel.CONSIDERING,
            motivation=SellerMotivation.LIFESTYLE,
            timeline_urgency=0.5,
            price_flexibility=0.6,
            market_knowledge=0.4,
            property_type="single_family",
            property_value_estimate=None,
            property_condition="good",
            unique_selling_points=[],
            potential_concerns=[],
            competitive_advantage_score=70.0,
            pricing_competitiveness=65.0,
            market_timing_score=75.0,
            conversation_sentiment=0.1,
            engagement_level=0.6,
            question_frequency=0.3,
            objection_patterns=[],
            research_depth=0.5,
            decision_confidence=0.4,
            agent_trust_level=0.7,
            last_updated=datetime.utcnow()
        )

    async def _format_market_context_for_claude(
        self,
        market_report: MarketIntelligenceReport,
        seller_context: SellerContext,
        conversation_intent: ConversationIntent,
        property_data: Dict
    ) -> ClaudeMarketContext:
        """Format market intelligence for Claude conversations"""

        # Generate summary based on market conditions
        if market_report.market_trend.value in ['bullish_strong', 'bullish_moderate']:
            summary = f"The {market_report.area} market is showing strong seller-favorable conditions with rising prices and high buyer demand."
        elif market_report.market_trend.value in ['bearish_moderate', 'bearish_strong']:
            summary = f"The {market_report.area} market is currently buyer-favorable, presenting opportunities for strategic pricing and positioning."
        else:
            summary = f"The {market_report.area} market is balanced, offering good opportunities for well-positioned properties."

        # Key talking points based on market intelligence
        talking_points = []

        if market_report.price_intelligence.price_momentum_score > 20:
            talking_points.append(f"Prices are trending upward with {market_report.price_intelligence.price_change_1y:.1%} growth over the past year")

        if market_report.inventory_intelligence.market_hotness_score > 70:
            talking_points.append(f"Market is very active with properties selling in an average of {market_report.inventory_intelligence.average_days_on_market} days")

        if market_report.behavioral_intelligence.seller_motivation_index > 70:
            talking_points.append("Current market conditions favor motivated sellers with good timing")

        # Pricing context
        median_price = market_report.price_intelligence.current_median_price
        pricing_context = f"Current median home price in {market_report.area} is ${median_price:,}"

        if market_report.price_intelligence.predicted_price_1m:
            price_direction = "expected to increase" if market_report.price_intelligence.predicted_price_1m > median_price else "may stabilize"
            pricing_context += f", {price_direction} based on current trends"

        # Timing context
        timing_context = f"Market timing is {market_report.market_timing.value.replace('_', ' ')}"
        if market_report.inventory_intelligence.fast_selling_percentage > 25:
            timing_context += f" with {market_report.inventory_intelligence.fast_selling_percentage:.1f}% of properties selling quickly"

        # Competition context
        competition_context = "Competition among listings is "
        if market_report.competitive_intelligence.competitive_advantage_score > 70:
            competition_context += "strong, requiring high-quality presentation and strategic pricing"
        elif market_report.competitive_intelligence.competitive_advantage_score < 40:
            competition_context += "moderate, providing opportunities for well-prepared sellers"
        else:
            competition_context += "balanced, favoring properties with good positioning"

        return ClaudeMarketContext(
            summary_message=summary,
            key_talking_points=talking_points,
            pricing_context=pricing_context,
            timing_context=timing_context,
            competition_context=competition_context,
            detailed_insights=asdict(market_report),
            conversation_starters=[
                "What specific aspects of the current market are you most curious about?",
                "How does your timeline align with current market conditions?",
                "What's driving your interest in selling at this time?"
            ],
            objection_responses={
                "market_timing": "Current market data suggests this is actually a favorable time for sellers in your area",
                "pricing_concerns": "We can position your property competitively while maximizing your return",
                "competition_worry": "Your property's unique features can differentiate it from the competition"
            },
            immediate_actions=[
                "Discuss property evaluation and competitive market analysis",
                "Review timeline and market timing considerations",
                "Address any specific concerns about current market conditions"
            ],
            strategic_considerations=[
                "Optimal pricing strategy based on current market dynamics",
                "Timeline flexibility to maximize market opportunities",
                "Property preparation to compete effectively"
            ],
            risk_mitigation=[
                "Monitor market changes and adjust strategy as needed",
                "Maintain pricing flexibility based on market feedback",
                "Consider backup plans if market conditions shift"
            ]
        )

    # Cache management methods
    async def _get_cached_context(self, cache_key: str) -> Optional[Dict]:
        """Get cached context data"""
        # Implementation would use actual cache service
        return None

    async def _cache_claude_context(self, cache_key: str, context: ClaudeMarketContext) -> None:
        """Cache Claude context for performance"""
        # Implementation would use actual cache service
        pass

    async def _get_cached_profile(self, cache_key: str) -> Optional[Dict]:
        """Get cached profile data"""
        return None

    async def _cache_seller_profile(self, cache_key: str, profile: SellerIntelligenceProfile) -> None:
        """Cache seller profile for performance"""
        pass

    # Fallback methods
    async def _generate_fallback_context(
        self,
        seller_context: SellerContext,
        conversation_intent: ConversationIntent
    ) -> ClaudeMarketContext:
        """Generate fallback context when market data unavailable"""
        return ClaudeMarketContext(
            summary_message="Market analysis is temporarily updating. Let's focus on your specific property and goals.",
            key_talking_points=[
                "Every property is unique and has its own market position",
                "Timing and preparation are key factors in successful selling",
                "Understanding your goals helps determine the best strategy"
            ],
            pricing_context="Property valuation will depend on specific characteristics, condition, and location",
            timing_context="Market timing varies by property type, location, and individual circumstances",
            competition_context="Strategic positioning can help your property stand out regardless of market conditions",
            detailed_insights={},
            conversation_starters=[
                "Tell me about your property and what makes it special",
                "What's motivating your decision to sell?",
                "What timeline are you considering for selling?"
            ],
            objection_responses={
                "market_uncertainty": "We can help you navigate market conditions with data-driven insights",
                "timing_concerns": "The best time to sell is when it aligns with your personal goals and circumstances"
            },
            immediate_actions=[
                "Gather detailed property information",
                "Understand seller goals and timeline",
                "Discuss property evaluation process"
            ],
            strategic_considerations=[
                "Property preparation and positioning strategy",
                "Pricing approach based on goals and timeline",
                "Market monitoring and strategy adjustments"
            ],
            risk_mitigation=[
                "Flexible strategy based on market feedback",
                "Clear communication about market realities",
                "Backup plans for different scenarios"
            ]
        )

    async def _generate_default_profile(
        self,
        seller_context: SellerContext
    ) -> SellerIntelligenceProfile:
        """Generate default profile when data unavailable"""
        return SellerIntelligenceProfile(
            seller_id=seller_context.lead_id,
            readiness_level=SellerReadinessLevel.CONSIDERING,
            motivation=SellerMotivation.LIFESTYLE,
            timeline_urgency=0.5,
            price_flexibility=0.5,
            market_knowledge=0.5,
            property_type="unknown",
            property_value_estimate=None,
            property_condition="unknown",
            unique_selling_points=[],
            potential_concerns=[],
            competitive_advantage_score=50.0,
            pricing_competitiveness=50.0,
            market_timing_score=50.0,
            conversation_sentiment=0.0,
            engagement_level=0.5,
            question_frequency=0.2,
            objection_patterns=[],
            research_depth=0.3,
            decision_confidence=0.3,
            agent_trust_level=0.5,
            last_updated=datetime.utcnow()
        )

    async def _generate_fallback_recommendations(
        self,
        seller_context: SellerContext
    ) -> Dict[str, Any]:
        """Generate fallback recommendations when analysis unavailable"""
        return {
            'immediate_priorities': ["Establish seller needs and timeline"],
            'conversation_starters': ["What's prompting your interest in selling?"],
            'key_questions': ["What are your goals for selling?", "What's your ideal timeline?"],
            'objection_handlers': {},
            'market_talking_points': ["Focus on property-specific advantages"],
            'next_best_actions': ["Schedule property consultation"],
            'timing_considerations': ["Align timing with seller goals"],
            'risk_mitigation': ["Gather more information before advising"]
        }

    # Utility methods
    async def _get_seller_property_data(self, seller_context: SellerContext) -> Dict[str, Any]:
        """Get seller property data for analysis"""
        return {
            'area': 'Austin',  # Default area
            'property_type': 'single_family',
            'estimated_value': 500000
        }

    async def _update_seller_intelligence_profile(
        self,
        insight: SellerConversationInsight,
        seller_context: SellerContext
    ) -> None:
        """Update seller intelligence profile based on conversation insights"""
        # Implementation would update profile in database/cache
        pass

    async def _analyze_conversation_patterns(
        self,
        insights: List[SellerConversationInsight]
    ) -> Dict[str, Any]:
        """Analyze patterns across conversation insights"""
        return {
            'engagement_trend': 'stable',
            'sentiment_trend': 'positive',
            'readiness_progression': 'advancing'
        }

    async def _generate_personalized_recommendations(
        self,
        profile: SellerIntelligenceProfile,
        patterns: Dict[str, Any],
        market_context: ClaudeMarketContext
    ) -> Dict[str, Any]:
        """Generate personalized recommendations for Claude"""
        return {
            'immediate': ["Address seller timeline questions"],
            'starters': market_context.conversation_starters,
            'questions': ["What aspects of selling concern you most?"],
            'objections': market_context.objection_responses,
            'market_points': market_context.key_talking_points,
            'actions': market_context.immediate_actions,
            'timing': ["Discuss optimal timing based on market conditions"],
            'risks': market_context.risk_mitigation
        }

    async def _calculate_engagement_score(
        self,
        engagement_metrics: Dict[str, float]
    ) -> float:
        """Calculate overall engagement score"""
        # Weighted calculation of engagement metrics
        weights = {
            'conversation_frequency': 0.2,
            'response_time': 0.15,
            'message_length': 0.15,
            'question_ratio': 0.2,
            'emotional_engagement': 0.15,
            'topic_diversity': 0.1,
            'decision_indicators': 0.05
        }

        score = sum(
            min(1.0, max(0.0, metric_value)) * weights.get(metric, 0)
            for metric, metric_value in engagement_metrics.items()
        )

        return min(1.0, max(0.0, score))

    async def _analyze_engagement_trends(
        self,
        seller_context: SellerContext,
        engagement_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze engagement trends over time"""
        return {
            'trend_direction': 'increasing',
            'consistency': 'high',
            'peak_engagement_topics': ['pricing', 'timeline']
        }

    async def _generate_engagement_insights(
        self,
        engagement_score: float,
        engagement_trends: Dict[str, Any],
        seller_context: SellerContext
    ) -> List[str]:
        """Generate insights from engagement analysis"""
        insights = []

        if engagement_score > 0.7:
            insights.append("Seller shows high engagement and interest")
        elif engagement_score > 0.4:
            insights.append("Seller engagement is moderate - opportunities to increase")
        else:
            insights.append("Low engagement detected - may need different approach")

        return insights

    async def _get_engagement_recommendations(
        self,
        engagement_score: float,
        engagement_trends: Dict[str, Any]
    ) -> List[str]:
        """Get recommendations to improve engagement"""
        recommendations = []

        if engagement_score < 0.5:
            recommendations.extend([
                "Ask more open-ended questions",
                "Provide market insights to build interest",
                "Address any concerns more directly"
            ])

        return recommendations


# Global instance for easy access
seller_claude_intelligence = SellerClaudeIntelligence(
    market_intelligence=RealTimeMarketIntelligence()
)


# Convenience functions for easy integration
async def analyze_seller_conversation(
    conversation_text: str,
    seller_context: SellerContext
) -> SellerConversationInsight:
    """Convenience function to analyze seller conversation"""
    return await seller_claude_intelligence.analyze_seller_conversation(
        conversation_text, seller_context
    )


async def get_claude_seller_context(
    seller_context: SellerContext,
    conversation_intent: ConversationIntent
) -> ClaudeMarketContext:
    """Convenience function to get Claude-formatted market context"""
    return await seller_claude_intelligence.get_claude_market_context(
        seller_context, conversation_intent
    )