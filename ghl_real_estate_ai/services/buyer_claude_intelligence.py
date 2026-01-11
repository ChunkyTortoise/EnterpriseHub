"""
Buyer-Claude Intelligence Service

Advanced intelligence layer specifically designed for buyer interactions through Claude AI.
Provides contextual property insights, conversation-driven analytics, and intelligent
decision support for real estate buyers.

Business Impact: Enhanced buyer conversion rates, personalized property recommendations, optimal timing guidance
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
from .claude_seller_agent import ConversationIntent  # Reuse for buyer conversations
from .advanced_cache_optimization import advanced_cache
from ..models.buyer_models import BuyerLead, BuyerGoals, BuyerProperty
from ..utils.ai_insights_generator import generate_ai_insights
from ..utils.conversation_analyzer import analyze_conversation_sentiment

logger = logging.getLogger(__name__)


class BuyerReadinessLevel(Enum):
    """Buyer readiness to purchase property"""
    EXPLORING = "exploring"               # Just browsing, 6+ months out
    RESEARCHING = "researching"           # Serious research, 3-6 months
    ACTIVELY_SEARCHING = "actively_searching"  # Committed to buying, 1-3 months
    PRE_APPROVED = "pre_approved"         # Financing ready, <1 month
    READY_TO_OFFER = "ready_to_offer"     # Ready for immediate purchase
    UNDER_CONTRACT = "under_contract"     # Already in transaction


class BuyerMotivation(Enum):
    """Primary buyer motivation categories"""
    FIRST_TIME_BUYER = "first_time_buyer"     # First home purchase
    UPSIZING = "upsizing"                     # Need larger space
    DOWNSIZING = "downsizing"                 # Simplifying lifestyle
    RELOCATION = "relocation"                 # Moving for work/life
    INVESTMENT = "investment"                 # Investment property
    LIFESTYLE = "lifestyle"                   # Lifestyle upgrade
    URGENT = "urgent"                         # Time-sensitive need


@dataclass
class BuyerIntelligenceProfile:
    """Comprehensive buyer intelligence profile"""
    buyer_id: str
    readiness_level: BuyerReadinessLevel
    motivation: BuyerMotivation
    timeline_urgency: float  # 0-1 scale
    budget_flexibility: float  # 0-1 scale (how flexible on budget)
    market_knowledge: float  # 0-1 scale (how much they know)

    # Financial characteristics
    budget_max: Optional[int]
    budget_comfortable: Optional[int]
    financing_status: str  # pre_approval, pre_qualification, cash, unknown
    down_payment_ready: bool

    # Property preferences
    property_type_priorities: List[str]
    location_preferences: List[str]
    must_have_features: List[str]
    nice_to_have_features: List[str]

    # Market position
    competitive_advantage_score: float  # 0-100 (financing, speed, etc.)
    offer_readiness_score: float  # 0-100 (how ready to make offers)
    market_timing_score: float  # 0-100 (how well positioned for current market)

    # Conversation insights
    conversation_sentiment: float  # -1 to 1 (negative to positive)
    engagement_level: float  # 0-1 scale
    question_frequency: float  # Questions per conversation
    concern_patterns: List[str]

    # Behavioral indicators
    property_view_frequency: float  # 0-1 (how often viewing properties)
    search_consistency: float  # 0-1 (consistency in search criteria)
    decision_confidence: float  # 0-1 (confidence in buying decision)
    agent_trust_level: float  # 0-1 (trust in agent/process)

    last_updated: datetime


@dataclass
class BuyerConversationInsight:
    """Insights extracted from buyer conversations"""
    conversation_id: str
    buyer_id: str
    timestamp: datetime

    # Intent analysis
    primary_intent: ConversationIntent
    secondary_intents: List[ConversationIntent]
    intent_confidence: float

    # Information extracted
    property_preferences: Dict[str, Any]
    budget_updates: Optional[Dict[str, Any]]
    timeline_updates: Optional[Dict[str, Any]]
    concerns_identified: List[str]

    # Emotional analysis
    sentiment_score: float  # -1 to 1
    excitement_level: float  # 0-1
    stress_indicators: List[str]
    confidence_indicators: List[str]

    # Market context awareness
    market_awareness_level: float  # 0-1
    pricing_expectations: Optional[Dict[str, Any]]
    competition_understanding: bool

    # Action indicators
    offer_readiness: float  # 0-1
    need_for_guidance: float  # 0-1
    urgency_level: float  # 0-1

    # Recommendations
    suggested_properties: List[str]
    recommended_next_actions: List[str]
    warning_flags: List[str]


@dataclass
class ClaudeBuyerContext:
    """Market and property context formatted specifically for Claude conversations"""
    summary_message: str
    key_talking_points: List[str]
    property_recommendations: str
    market_context: str
    financing_context: str

    # Supporting data for deeper discussions
    detailed_insights: Dict[str, Any]
    conversation_starters: List[str]
    objection_responses: Dict[str, str]

    # Contextual recommendations
    immediate_actions: List[str]
    strategic_considerations: List[str]
    risk_mitigation: List[str]


@dataclass
class BuyerContext:
    """Buyer context for conversation processing"""
    lead_id: str
    contact_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    source: str = 'unknown'

    # Buyer-specific context
    budget_max: Optional[int] = None
    timeline: Optional[str] = None
    preferences: Dict[str, Any] = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}


class BuyerClaudeIntelligence:
    """
    Advanced intelligence service for buyer-Claude interactions.

    Provides contextual property insights, conversation analytics, and intelligent
    decision support specifically designed for Claude AI conversations with buyers.
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

    async def analyze_buyer_conversation(
        self,
        conversation_text: str,
        buyer_context: BuyerContext,
        previous_insights: Optional[List[BuyerConversationInsight]] = None
    ) -> BuyerConversationInsight:
        """
        Analyze buyer conversation and extract actionable insights
        """
        try:
            # Extract conversation metadata
            conversation_id = f"conv_{buyer_context.lead_id}_{int(datetime.utcnow().timestamp())}"

            # Analyze conversation intent using Claude
            intent_analysis = await self._analyze_conversation_intent(
                conversation_text, buyer_context
            )

            # Extract property preferences and budget information
            preference_updates = await self._extract_buyer_preferences(
                conversation_text, buyer_context
            )

            # Analyze emotional indicators
            emotional_analysis = await self._analyze_conversation_emotions(
                conversation_text, buyer_context
            )

            # Assess market awareness and knowledge level
            market_awareness = await self._assess_market_awareness(
                conversation_text, buyer_context
            )

            # Identify concerns and hesitations
            concerns = await self._identify_buyer_concerns(
                conversation_text, buyer_context
            )

            # Generate property recommendations based on conversation
            property_suggestions = await self._generate_property_suggestions(
                conversation_text, buyer_context, preference_updates
            )

            # Generate actionable recommendations
            recommendations = await self._generate_buyer_recommendations(
                intent_analysis, preference_updates, emotional_analysis,
                market_awareness, concerns, buyer_context
            )

            insight = BuyerConversationInsight(
                conversation_id=conversation_id,
                buyer_id=buyer_context.lead_id,
                timestamp=datetime.utcnow(),
                primary_intent=intent_analysis['primary_intent'],
                secondary_intents=intent_analysis['secondary_intents'],
                intent_confidence=intent_analysis['confidence'],
                property_preferences=preference_updates['preferences'],
                budget_updates=preference_updates.get('budget'),
                timeline_updates=preference_updates.get('timeline'),
                concerns_identified=concerns['concerns'],
                sentiment_score=emotional_analysis['sentiment'],
                excitement_level=emotional_analysis['excitement'],
                stress_indicators=emotional_analysis['stress_indicators'],
                confidence_indicators=emotional_analysis['confidence_indicators'],
                market_awareness_level=market_awareness['awareness_level'],
                pricing_expectations=market_awareness.get('pricing_expectations'),
                competition_understanding=market_awareness['competition_understanding'],
                offer_readiness=recommendations['offer_readiness'],
                need_for_guidance=recommendations['guidance_need'],
                urgency_level=recommendations['urgency_level'],
                suggested_properties=property_suggestions,
                recommended_next_actions=recommendations['next_actions'],
                warning_flags=recommendations['warning_flags']
            )

            # Update buyer intelligence profile
            await self._update_buyer_intelligence_profile(insight, buyer_context)

            logger.info(f"Buyer conversation analysis completed for {buyer_context.lead_id}")
            return insight

        except Exception as e:
            logger.error(f"Buyer conversation analysis failed: {e}")
            # Return minimal insight
            return BuyerConversationInsight(
                conversation_id=f"conv_{buyer_context.lead_id}_{int(datetime.utcnow().timestamp())}",
                buyer_id=buyer_context.lead_id,
                timestamp=datetime.utcnow(),
                primary_intent=ConversationIntent.INFORMATION_GATHERING,
                secondary_intents=[],
                intent_confidence=0.3,
                property_preferences={},
                concerns_identified=[],
                sentiment_score=0.0,
                excitement_level=0.0,
                stress_indicators=[],
                confidence_indicators=[],
                market_awareness_level=0.5,
                competition_understanding=False,
                offer_readiness=0.5,
                need_for_guidance=0.7,
                urgency_level=0.3,
                suggested_properties=[],
                recommended_next_actions=["Gather more buyer preferences"],
                warning_flags=["Limited conversation data available"]
            )

    async def get_claude_buyer_context(
        self,
        buyer_context: BuyerContext,
        conversation_intent: ConversationIntent,
        include_deep_insights: bool = False
    ) -> ClaudeBuyerContext:
        """
        Generate buyer context specifically formatted for Claude conversations
        """
        try:
            cache_key = f"buyer_context_{buyer_context.lead_id}_{conversation_intent.value}"

            # Check cache first
            cached_context = await self._get_cached_context(cache_key)
            if cached_context and not include_deep_insights:
                return ClaudeBuyerContext(**cached_context)

            # Get buyer preferences
            buyer_data = await self._get_buyer_data(buyer_context)

            # Get comprehensive market analysis for buyer's area of interest
            market_report = await self.market_intelligence.analyze_market(
                buyer_data.get('preferred_area', 'Austin'),
                depth="comprehensive" if include_deep_insights else "standard"
            )

            # Generate conversation-specific context
            context = await self._format_buyer_context_for_claude(
                market_report, buyer_context, conversation_intent, buyer_data
            )

            # Cache for future use
            await self._cache_buyer_context(cache_key, context)

            return context

        except Exception as e:
            logger.error(f"Failed to generate Claude buyer context: {e}")
            return await self._generate_fallback_buyer_context(buyer_context, conversation_intent)

    async def get_buyer_intelligence_profile(
        self,
        buyer_context: BuyerContext,
        refresh: bool = False
    ) -> BuyerIntelligenceProfile:
        """
        Get or build comprehensive buyer intelligence profile
        """
        try:
            cache_key = f"buyer_profile_{buyer_context.lead_id}"

            if not refresh:
                cached_profile = await self._get_cached_profile(cache_key)
                if cached_profile:
                    return BuyerIntelligenceProfile(**cached_profile)

            # Build comprehensive profile
            profile = await self._build_buyer_intelligence_profile(buyer_context)

            # Cache profile
            await self._cache_buyer_profile(cache_key, profile)

            return profile

        except Exception as e:
            logger.error(f"Failed to get buyer intelligence profile: {e}")
            return await self._generate_default_buyer_profile(buyer_context)

    async def get_property_recommendations(
        self,
        buyer_context: BuyerContext,
        recent_insights: List[BuyerConversationInsight],
        include_market_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Generate intelligent property recommendations for buyer
        """
        try:
            # Get buyer profile
            profile = await self.get_buyer_intelligence_profile(buyer_context)

            # Get market context if requested
            market_context = None
            if include_market_analysis:
                market_context = await self.get_claude_buyer_context(
                    buyer_context, ConversationIntent.PROPERTY_SEARCH
                )

            # Analyze conversation history patterns
            preference_patterns = await self._analyze_buyer_preferences(recent_insights)

            # Generate personalized property recommendations
            recommendations = await self._generate_personalized_property_recommendations(
                profile, preference_patterns, market_context
            )

            return {
                'recommended_properties': recommendations['properties'],
                'search_criteria': recommendations['criteria'],
                'market_insights': recommendations['market_insights'],
                'financing_options': recommendations['financing'],
                'next_best_actions': recommendations['actions'],
                'timing_considerations': recommendations['timing'],
                'competitive_advantages': recommendations['advantages']
            }

        except Exception as e:
            logger.error(f"Failed to generate property recommendations: {e}")
            return await self._generate_fallback_property_recommendations(buyer_context)

    async def track_buyer_engagement(
        self,
        buyer_context: BuyerContext,
        engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track and analyze buyer engagement patterns for intelligence
        """
        try:
            engagement_metrics = {
                'property_views_per_week': engagement_data.get('property_views', 0),
                'conversation_frequency': engagement_data.get('conversations_per_week', 1),
                'response_time': engagement_data.get('avg_response_time_hours', 24),
                'search_consistency': engagement_data.get('search_consistency', 0.5),
                'showing_requests': engagement_data.get('showing_requests', 0),
                'offer_considerations': engagement_data.get('offers_considered', 0),
                'referral_interactions': engagement_data.get('referral_activity', 0)
            }

            # Calculate engagement score
            engagement_score = await self._calculate_buyer_engagement_score(engagement_metrics)

            # Identify engagement trends
            engagement_trends = await self._analyze_buyer_engagement_trends(
                buyer_context, engagement_metrics
            )

            # Generate engagement insights
            insights = await self._generate_buyer_engagement_insights(
                engagement_score, engagement_trends, buyer_context
            )

            return {
                'engagement_score': engagement_score,
                'trends': engagement_trends,
                'insights': insights,
                'recommendations': await self._get_buyer_engagement_recommendations(
                    engagement_score, engagement_trends
                )
            }

        except Exception as e:
            logger.error(f"Buyer engagement tracking failed: {e}")
            return {'error': 'Engagement tracking temporarily unavailable'}

    # Private helper methods for conversation analysis

    async def _analyze_conversation_intent(
        self,
        conversation_text: str,
        buyer_context: BuyerContext
    ) -> Dict[str, Any]:
        """Analyze conversation intent using AI"""
        # This would use Claude or another AI to analyze intent
        # Placeholder implementation with buyer-specific intent classification
        text_lower = conversation_text.lower()

        if any(word in text_lower for word in ['house', 'home', 'property', 'buy', 'purchase']):
            if any(word in text_lower for word in ['price', 'cost', 'afford', 'budget']):
                primary_intent = ConversationIntent.PRICING_DISCUSSION
            elif any(word in text_lower for word in ['area', 'neighborhood', 'location', 'school']):
                primary_intent = ConversationIntent.PROPERTY_SEARCH
            elif any(word in text_lower for word in ['loan', 'mortgage', 'finance', 'down payment']):
                primary_intent = ConversationIntent.FINANCING_INQUIRY
            else:
                primary_intent = ConversationIntent.PROPERTY_INQUIRY
        else:
            primary_intent = ConversationIntent.INFORMATION_GATHERING

        return {
            'primary_intent': primary_intent,
            'secondary_intents': [ConversationIntent.MARKET_RESEARCH],
            'confidence': 0.85
        }

    async def _extract_buyer_preferences(
        self,
        conversation_text: str,
        buyer_context: BuyerContext
    ) -> Dict[str, Any]:
        """Extract buyer preferences from conversation"""
        # AI-powered preference extraction
        text_lower = conversation_text.lower()

        preferences = {}

        # Extract property type preferences
        if 'condo' in text_lower:
            preferences['property_type'] = 'condo'
        elif 'house' in text_lower or 'home' in text_lower:
            preferences['property_type'] = 'single_family'
        elif 'townhome' in text_lower or 'townhouse' in text_lower:
            preferences['property_type'] = 'townhome'

        # Extract budget information
        budget_keywords = ['budget', 'afford', 'max', 'limit', 'price range']
        if any(keyword in text_lower for keyword in budget_keywords):
            # Simple budget extraction (would be more sophisticated in production)
            import re
            amounts = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:k|K)?)', conversation_text)
            if amounts:
                preferences['budget_indication'] = amounts[0]

        return {
            'preferences': preferences,
            'budget': preferences.get('budget_indication'),
            'timeline': None  # Would extract timeline information
        }

    async def _analyze_conversation_emotions(
        self,
        conversation_text: str,
        buyer_context: BuyerContext
    ) -> Dict[str, Any]:
        """Analyze emotional indicators in conversation"""
        text_lower = conversation_text.lower()

        # Simple emotion analysis (would be more sophisticated in production)
        excitement_words = ['excited', 'love', 'perfect', 'amazing', 'great', 'wonderful']
        stress_words = ['worried', 'concerned', 'anxious', 'nervous', 'stressed', 'overwhelmed']
        confidence_words = ['ready', 'sure', 'confident', 'decided', 'certain']

        excitement_score = sum(1 for word in excitement_words if word in text_lower) / len(excitement_words)
        stress_indicators = [word for word in stress_words if word in text_lower]
        confidence_indicators = [word for word in confidence_words if word in text_lower]

        sentiment = 0.1 + excitement_score * 0.4 - len(stress_indicators) * 0.1

        return {
            'sentiment': max(-1, min(1, sentiment)),
            'excitement': excitement_score,
            'stress_indicators': stress_indicators,
            'confidence_indicators': confidence_indicators
        }

    async def _assess_market_awareness(
        self,
        conversation_text: str,
        buyer_context: BuyerContext
    ) -> Dict[str, Any]:
        """Assess buyer's market knowledge level"""
        text_lower = conversation_text.lower()

        market_terms = ['market', 'rates', 'prices', 'trends', 'appreciation', 'competition']
        awareness_score = sum(1 for term in market_terms if term in text_lower) / len(market_terms)

        return {
            'awareness_level': min(1.0, awareness_score * 2),  # Scale up
            'pricing_expectations': None,
            'competition_understanding': 'competition' in text_lower or 'bidding' in text_lower
        }

    async def _identify_buyer_concerns(
        self,
        conversation_text: str,
        buyer_context: BuyerContext
    ) -> Dict[str, Any]:
        """Identify buyer concerns and hesitations"""
        text_lower = conversation_text.lower()

        concern_keywords = {
            'pricing': ['expensive', 'cost', 'afford', 'budget'],
            'market_timing': ['timing', 'wait', 'rush', 'hurry'],
            'financing': ['loan', 'credit', 'down payment', 'qualify'],
            'competition': ['bidding', 'competition', 'multiple offers'],
            'location': ['area', 'neighborhood', 'commute', 'schools']
        }

        concerns = []
        for concern_type, keywords in concern_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                concerns.append(concern_type)

        return {
            'concerns': concerns
        }

    async def _generate_property_suggestions(
        self,
        conversation_text: str,
        buyer_context: BuyerContext,
        preference_updates: Dict[str, Any]
    ) -> List[str]:
        """Generate property suggestions based on conversation"""
        # This would integrate with actual property database
        suggestions = []

        preferences = preference_updates.get('preferences', {})

        if preferences.get('property_type') == 'condo':
            suggestions.extend(['Modern downtown condo', 'Luxury high-rise unit'])
        elif preferences.get('property_type') == 'single_family':
            suggestions.extend(['Family home with yard', 'Updated single-family home'])

        return suggestions[:5]  # Limit to 5 suggestions

    async def _generate_buyer_recommendations(
        self,
        intent_analysis: Dict,
        preference_updates: Dict,
        emotional_analysis: Dict,
        market_awareness: Dict,
        concerns: Dict,
        buyer_context: BuyerContext
    ) -> Dict[str, Any]:
        """Generate actionable recommendations from analysis"""

        # Calculate readiness scores
        offer_readiness = 0.5
        guidance_need = 0.6
        urgency = 0.4

        # Adjust based on conversation content
        if intent_analysis['primary_intent'] == ConversationIntent.PROPERTY_INQUIRY:
            offer_readiness += 0.2

        if emotional_analysis['excitement'] > 0.5:
            offer_readiness += 0.1
            urgency += 0.1

        if len(concerns['concerns']) > 2:
            guidance_need += 0.2

        next_actions = ['Show relevant properties', 'Discuss financing options']
        warning_flags = []

        if emotional_analysis['sentiment'] < 0:
            warning_flags.append('Negative sentiment detected')
            next_actions.append('Address concerns and build confidence')

        return {
            'offer_readiness': min(1.0, offer_readiness),
            'guidance_need': min(1.0, guidance_need),
            'urgency_level': min(1.0, urgency),
            'next_actions': next_actions,
            'warning_flags': warning_flags
        }

    # Additional helper methods (simplified for demo purposes)

    async def _build_buyer_intelligence_profile(
        self,
        buyer_context: BuyerContext
    ) -> BuyerIntelligenceProfile:
        """Build comprehensive buyer intelligence profile"""
        return BuyerIntelligenceProfile(
            buyer_id=buyer_context.lead_id,
            readiness_level=BuyerReadinessLevel.RESEARCHING,
            motivation=BuyerMotivation.FIRST_TIME_BUYER,
            timeline_urgency=0.6,
            budget_flexibility=0.5,
            market_knowledge=0.4,
            budget_max=buyer_context.budget_max,
            budget_comfortable=int(buyer_context.budget_max * 0.8) if buyer_context.budget_max else None,
            financing_status='pre_qualification',
            down_payment_ready=False,
            property_type_priorities=['single_family', 'townhome'],
            location_preferences=['Austin', 'Cedar Park'],
            must_have_features=['parking', 'updated_kitchen'],
            nice_to_have_features=['pool', 'large_yard'],
            competitive_advantage_score=60.0,
            offer_readiness_score=50.0,
            market_timing_score=70.0,
            conversation_sentiment=0.1,
            engagement_level=0.6,
            question_frequency=0.3,
            concern_patterns=[],
            property_view_frequency=0.4,
            search_consistency=0.6,
            decision_confidence=0.5,
            agent_trust_level=0.7,
            last_updated=datetime.utcnow()
        )

    async def _format_buyer_context_for_claude(
        self,
        market_report: MarketIntelligenceReport,
        buyer_context: BuyerContext,
        conversation_intent: ConversationIntent,
        buyer_data: Dict
    ) -> ClaudeBuyerContext:
        """Format buyer context for Claude conversations"""

        # Generate buyer-focused summary
        if market_report.market_trend.value in ['bullish_strong', 'bullish_moderate']:
            summary = f"The {market_report.area} market is competitive for buyers, with rising prices and high demand. This creates urgency but also opportunities for well-positioned buyers."
        elif market_report.market_trend.value in ['bearish_moderate', 'bearish_strong']:
            summary = f"The {market_report.area} market favors buyers with more inventory and negotiation opportunities."
        else:
            summary = f"The {market_report.area} market is balanced, offering good opportunities for prepared buyers."

        # Buyer-focused talking points
        talking_points = []

        if market_report.inventory_intelligence.market_hotness_score > 70:
            talking_points.append(f"Fast-moving market - properties selling in {market_report.inventory_intelligence.average_days_on_market} days")

        if market_report.price_intelligence.price_momentum_score > 20:
            talking_points.append(f"Home prices trending upward with {market_report.price_intelligence.price_change_1y:.1%} growth")

        if market_report.competitive_intelligence.overpriced_listings_percentage > 15:
            talking_points.append("Some overpriced properties present negotiation opportunities")

        # Property recommendations context
        median_price = market_report.price_intelligence.current_median_price
        recommendations_context = f"Current median home price in {market_report.area} is ${median_price:,}"

        if buyer_context.budget_max:
            budget_context = f"With your budget of ${buyer_context.budget_max:,}, you have good options in this market"
        else:
            budget_context = "Let's discuss your budget to identify the best properties for you"

        # Market timing context for buyers
        market_context = f"Market timing is {market_report.market_timing.value.replace('_', ' ')} for buyers"

        if market_report.market_timing.value in ['excellent_buy', 'good_buy']:
            market_context += " - favorable conditions for making competitive offers"
        elif market_report.market_timing.value == 'wait':
            market_context += " - consider waiting for more favorable conditions"

        # Financing context
        financing_context = "Current interest rates create opportunities for qualified buyers"
        if market_report.market_trend.value in ['bullish_strong']:
            financing_context += ". Pre-approval strengthens your position in competitive situations"

        return ClaudeBuyerContext(
            summary_message=summary,
            key_talking_points=talking_points,
            property_recommendations=recommendations_context,
            market_context=market_context,
            financing_context=financing_context,
            detailed_insights=asdict(market_report),
            conversation_starters=[
                "What type of property are you most excited about?",
                "How does your timeline align with current market conditions?",
                "What questions do you have about the buying process?"
            ],
            objection_responses={
                "too_expensive": "Let's explore different areas and property types that fit your budget",
                "too_competitive": "I can help you position your offer competitively with the right strategy",
                "timing_concerns": "We can monitor market conditions and time your search optimally"
            },
            immediate_actions=[
                "Clarify budget and financing status",
                "Identify preferred neighborhoods and property types",
                "Schedule property viewings based on preferences"
            ],
            strategic_considerations=[
                "Pre-approval strengthens negotiating position",
                "Flexible closing timeline can be competitive advantage",
                "Market knowledge helps identify good value opportunities"
            ],
            risk_mitigation=[
                "Thorough property inspection to avoid costly surprises",
                "Multiple property options to avoid emotional overpaying",
                "Clear financing contingencies for protection"
            ]
        )

    # Cache and utility methods (simplified implementations)

    async def _get_cached_context(self, cache_key: str) -> Optional[Dict]:
        """Get cached context data"""
        return None

    async def _cache_buyer_context(self, cache_key: str, context: ClaudeBuyerContext) -> None:
        """Cache buyer context for performance"""
        pass

    async def _get_cached_profile(self, cache_key: str) -> Optional[Dict]:
        """Get cached profile data"""
        return None

    async def _cache_buyer_profile(self, cache_key: str, profile: BuyerIntelligenceProfile) -> None:
        """Cache buyer profile for performance"""
        pass

    async def _get_buyer_data(self, buyer_context: BuyerContext) -> Dict[str, Any]:
        """Get buyer data for analysis"""
        return {
            'preferred_area': 'Austin',
            'budget_max': buyer_context.budget_max or 500000,
            'property_type': 'single_family'
        }

    async def _update_buyer_intelligence_profile(
        self,
        insight: BuyerConversationInsight,
        buyer_context: BuyerContext
    ) -> None:
        """Update buyer intelligence profile based on conversation"""
        pass

    async def _generate_fallback_buyer_context(
        self,
        buyer_context: BuyerContext,
        conversation_intent: ConversationIntent
    ) -> ClaudeBuyerContext:
        """Generate fallback context when market data unavailable"""
        return ClaudeBuyerContext(
            summary_message="Let's focus on finding you the perfect property that meets your needs and budget.",
            key_talking_points=[
                "Every buyer's situation is unique",
                "The right property and timing depend on your specific goals",
                "We'll find properties that match your criteria and budget"
            ],
            property_recommendations="Property recommendations will be based on your preferences and budget",
            market_context="Market conditions vary by area and price range",
            financing_context="Multiple financing options available for qualified buyers",
            detailed_insights={},
            conversation_starters=[
                "What type of home are you looking for?",
                "What's your ideal timeline for purchasing?",
                "What features are most important to you?"
            ],
            objection_responses={
                "budget_concerns": "We can explore options within your comfort zone",
                "market_uncertainty": "I'll provide current market insights to guide your decision"
            },
            immediate_actions=[
                "Understand buyer preferences and budget",
                "Identify suitable properties",
                "Discuss financing options"
            ],
            strategic_considerations=[
                "Budget alignment with market reality",
                "Timing based on personal and market factors",
                "Property selection strategy"
            ],
            risk_mitigation=[
                "Thorough market analysis before making offers",
                "Professional guidance throughout the process",
                "Careful evaluation of all property options"
            ]
        )

    async def _generate_default_buyer_profile(
        self,
        buyer_context: BuyerContext
    ) -> BuyerIntelligenceProfile:
        """Generate default profile when data unavailable"""
        return BuyerIntelligenceProfile(
            buyer_id=buyer_context.lead_id,
            readiness_level=BuyerReadinessLevel.EXPLORING,
            motivation=BuyerMotivation.FIRST_TIME_BUYER,
            timeline_urgency=0.5,
            budget_flexibility=0.5,
            market_knowledge=0.3,
            budget_max=buyer_context.budget_max,
            budget_comfortable=None,
            financing_status='unknown',
            down_payment_ready=False,
            property_type_priorities=[],
            location_preferences=[],
            must_have_features=[],
            nice_to_have_features=[],
            competitive_advantage_score=40.0,
            offer_readiness_score=30.0,
            market_timing_score=50.0,
            conversation_sentiment=0.0,
            engagement_level=0.3,
            question_frequency=0.2,
            concern_patterns=[],
            property_view_frequency=0.2,
            search_consistency=0.3,
            decision_confidence=0.3,
            agent_trust_level=0.5,
            last_updated=datetime.utcnow()
        )

    # Additional utility methods for buyer engagement and recommendations

    async def _analyze_buyer_preferences(
        self,
        insights: List[BuyerConversationInsight]
    ) -> Dict[str, Any]:
        """Analyze patterns across buyer conversation insights"""
        return {
            'preference_consistency': 'high',
            'budget_evolution': 'stable',
            'location_focus': 'narrowing'
        }

    async def _generate_personalized_property_recommendations(
        self,
        profile: BuyerIntelligenceProfile,
        patterns: Dict[str, Any],
        market_context: Optional[ClaudeBuyerContext]
    ) -> Dict[str, Any]:
        """Generate personalized property recommendations"""
        return {
            'properties': ['123 Main St', '456 Oak Ave', '789 Pine Rd'],
            'criteria': {'bedrooms': 3, 'bathrooms': 2, 'price_max': profile.budget_max},
            'market_insights': ['Good value opportunities in target area'],
            'financing': ['Conventional loan options', 'FHA programs available'],
            'actions': ['Schedule property viewings', 'Get pre-approved'],
            'timing': ['Current market timing favorable for buyers'],
            'advantages': ['Strong financing', 'Flexible timeline']
        }

    async def _generate_fallback_property_recommendations(
        self,
        buyer_context: BuyerContext
    ) -> Dict[str, Any]:
        """Generate fallback recommendations when analysis unavailable"""
        return {
            'recommended_properties': [],
            'search_criteria': {'status': 'Need more buyer information'},
            'market_insights': ['General market information available'],
            'financing_options': ['Consult with lender for options'],
            'next_best_actions': ['Clarify buyer preferences'],
            'timing_considerations': ['Market timing varies by situation'],
            'competitive_advantages': ['To be determined based on buyer situation']
        }

    async def _calculate_buyer_engagement_score(
        self,
        engagement_metrics: Dict[str, float]
    ) -> float:
        """Calculate overall buyer engagement score"""
        weights = {
            'property_views_per_week': 0.3,
            'conversation_frequency': 0.2,
            'response_time': 0.1,
            'search_consistency': 0.2,
            'showing_requests': 0.15,
            'offer_considerations': 0.05
        }

        # Normalize metrics to 0-1 scale and apply weights
        normalized_metrics = {}
        for metric, value in engagement_metrics.items():
            if metric == 'response_time':
                # Lower response time = higher engagement
                normalized_metrics[metric] = max(0, 1 - (value / 48))  # 48 hours = 0 engagement
            elif metric == 'property_views_per_week':
                normalized_metrics[metric] = min(1, value / 10)  # 10 views per week = max
            else:
                normalized_metrics[metric] = min(1, value / 5)  # Scale other metrics

        score = sum(
            normalized_metrics.get(metric, 0) * weight
            for metric, weight in weights.items()
        )

        return min(1.0, max(0.0, score))

    async def _analyze_buyer_engagement_trends(
        self,
        buyer_context: BuyerContext,
        engagement_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze buyer engagement trends over time"""
        return {
            'trend_direction': 'increasing',
            'consistency': 'moderate',
            'peak_engagement_activities': ['property_viewing', 'market_research']
        }

    async def _generate_buyer_engagement_insights(
        self,
        engagement_score: float,
        engagement_trends: Dict[str, Any],
        buyer_context: BuyerContext
    ) -> List[str]:
        """Generate insights from buyer engagement analysis"""
        insights = []

        if engagement_score > 0.7:
            insights.append("Buyer shows high engagement and purchase intent")
        elif engagement_score > 0.4:
            insights.append("Moderate engagement - opportunities to increase interest")
        else:
            insights.append("Low engagement detected - may need different approach")

        return insights

    async def _get_buyer_engagement_recommendations(
        self,
        engagement_score: float,
        engagement_trends: Dict[str, Any]
    ) -> List[str]:
        """Get recommendations to improve buyer engagement"""
        recommendations = []

        if engagement_score < 0.5:
            recommendations.extend([
                "Show more relevant properties matching preferences",
                "Provide market insights to build confidence",
                "Schedule property viewings to increase engagement"
            ])

        return recommendations


# Global instance for easy access
buyer_claude_intelligence = BuyerClaudeIntelligence(
    market_intelligence=RealTimeMarketIntelligence()
)


# Convenience functions for easy integration
async def analyze_buyer_conversation(
    conversation_text: str,
    buyer_context: BuyerContext
) -> BuyerConversationInsight:
    """Convenience function to analyze buyer conversation"""
    return await buyer_claude_intelligence.analyze_buyer_conversation(
        conversation_text, buyer_context
    )


async def get_claude_buyer_context(
    buyer_context: BuyerContext,
    conversation_intent: ConversationIntent
) -> ClaudeBuyerContext:
    """Convenience function to get Claude-formatted buyer context"""
    return await buyer_claude_intelligence.get_claude_buyer_context(
        buyer_context, conversation_intent
    )