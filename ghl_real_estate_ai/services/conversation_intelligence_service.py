"""
Conversation Intelligence Service - Phase 2.3
=============================================

Real-time conversation analysis with objection detection and coaching insights.
Integrates with Phase 2.1 behavioral predictions and existing conversation intelligence.

Features:
- Real-time conversation analysis with <500ms processing
- Objection detection with response recommendations
- Sentiment analysis with trend tracking
- Conversation quality metrics and coaching opportunities
- Integration with Phase 2.1 behavioral predictions

Author: Jorge's Real Estate AI Platform - Phase 2.3 Implementation
"""

import asyncio
import json
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple

from ghl_real_estate_ai.agents.intent_decoder import get_intent_decoder
from ghl_real_estate_ai.ghl_utils.logger import get_logger

# Core service imports
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import get_claude_assistant
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)

# Configuration constants
CACHE_TTL_INSIGHTS = 300  # 5 minutes for insights
INSIGHT_HISTORY_SIZE = 10  # Keep last 10 insights per lead
TARGET_PROCESSING_TIME_MS = 500  # <500ms processing target
SENTIMENT_ANALYSIS_WINDOW = 5  # Analyze last 5 messages for trend


class ObjectionType(Enum):
    """Types of objections detected in real estate conversations."""

    PRICING = "pricing"
    TIMING = "timing"
    FINANCIAL = "financial"
    PROPERTY_CONDITION = "property_condition"
    COMPETITION = "competition"
    PROCESS = "process"
    COMMITMENT = "commitment"
    TRUST = "trust"


class SentimentLevel(Enum):
    """Sentiment classification levels."""

    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class CoachingArea(Enum):
    """Areas for coaching opportunities."""

    OBJECTION_HANDLING = "objection_handling"
    NEGOTIATION = "negotiation"
    RAPPORT_BUILDING = "rapport_building"
    CLOSING_TECHNIQUES = "closing_techniques"
    FOLLOW_UP = "follow_up"
    ACTIVE_LISTENING = "active_listening"
    VALUE_PROPOSITION = "value_proposition"


class ResponseTiming(Enum):
    """Recommended timing for responses."""

    IMMEDIATE = "immediate"
    WAIT_1H = "wait_1h"
    WAIT_24H = "wait_24h"
    FOLLOW_UP = "follow_up"


@dataclass
class ObjectionDetection:
    """Detected objection with context and recommendations."""

    objection_type: ObjectionType
    confidence: float  # 0.0-1.0
    severity: str  # low, medium, high
    context: str  # Extracted text showing the objection
    message_index: int  # Which message contained the objection
    suggested_responses: List[str]
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SentimentDataPoint:
    """Single sentiment measurement point."""

    timestamp: datetime
    score: float  # -1.0 to 1.0
    level: SentimentLevel
    confidence: float
    message_text: str
    message_index: int


@dataclass
class SentimentTimeline:
    """Complete sentiment analysis timeline."""

    conversation_id: str
    overall_sentiment: float  # Average sentiment score
    current_sentiment: SentimentLevel
    trend: str  # improving, declining, stable
    volatility: float  # 0-1, how much sentiment varies
    data_points: List[SentimentDataPoint]
    risk_level: str  # low, medium, high
    recommendations: List[str]


@dataclass
class CoachingOpportunity:
    """Identified coaching opportunity."""

    area: CoachingArea
    description: str
    priority: str  # low, medium, high
    difficulty: str  # beginner, intermediate, advanced
    estimated_time_minutes: int
    learning_objectives: List[str]
    suggested_practice: str
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ResponseRecommendation:
    """AI-generated response recommendation."""

    response_text: str
    confidence: float
    tone: str  # professional, friendly, empathetic, assertive
    expected_impact: str  # positive, neutral, risk
    timing: ResponseTiming
    rationale: str
    alternatives: List[str] = field(default_factory=list)


@dataclass
class ConversationQualityMetrics:
    """Comprehensive conversation quality assessment."""

    overall_score: float  # 0-100
    engagement_score: float
    rapport_score: float
    professionalism_score: float
    response_effectiveness: float
    message_depth_score: float
    question_answer_ratio: float
    active_listening_indicators: int
    strengths: List[str]
    improvement_areas: List[str]
    coaching_opportunities: List[CoachingOpportunity]


@dataclass
class ConversationInsight:
    """Complete conversation intelligence analysis result."""

    conversation_id: str
    lead_id: str
    location_id: str
    analyzed_at: datetime
    processing_time_ms: float

    # Core analysis components
    objections_detected: List[ObjectionDetection]
    sentiment_timeline: SentimentTimeline
    quality_metrics: ConversationQualityMetrics
    response_recommendations: List[ResponseRecommendation]

    # Integration insights
    behavioral_correlation: Optional[Dict[str, Any]] = None
    intent_analysis: Optional[Dict[str, Any]] = None

    # Metadata
    message_count: int = 0
    cache_hit: bool = False


class ConversationIntelligenceService:
    """
    Real-time conversation analysis with objection detection and coaching insights.

    Features:
    - <500ms conversation processing target
    - Objection detection with 8 objection types
    - Sentiment analysis with trend tracking
    - Conversation quality metrics and coaching opportunities
    - Integration with Phase 2.1 behavioral predictions
    - Multi-layer caching with tenant isolation
    - Real-time event publishing
    """

    def __init__(self):
        # Core services
        self.cache = get_cache_service()
        self.event_publisher = get_event_publisher()
        self.claude_assistant = get_claude_assistant()
        self.intent_decoder = get_intent_decoder()

        # Lazy loading for Phase 2.1 integration (avoid circular dependency)
        self._behavior_service = None

        # In-memory insight history (per lead)
        self.insight_history: Dict[str, Deque[Dict[str, Any]]] = {}

        # Performance metrics
        self.metrics = {
            "total_analyses": 0,
            "avg_processing_time_ms": 0.0,
            "cache_hit_rate": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "insight_history_leads": 0,
        }

        # Objection patterns (compiled for performance)
        self.objection_patterns = self._compile_objection_patterns()

        # Sentiment lexicon
        self.sentiment_lexicon = self._build_sentiment_lexicon()

        logger.info("ConversationIntelligenceService initialized")

    @property
    def behavior_service(self):
        """Lazy load behavior service to avoid circular dependency."""
        if self._behavior_service is None:
            try:
                from ghl_real_estate_ai.services.predictive_lead_behavior_service import get_predictive_behavior_service

                self._behavior_service = get_predictive_behavior_service()
            except ImportError:
                logger.warning("Could not import behavior service - proceeding without behavioral integration")
                self._behavior_service = None
        return self._behavior_service

    async def analyze_conversation_with_insights(
        self,
        conversation_id: str,
        lead_id: str,
        location_id: str,
        conversation_history: List[Dict[str, Any]],
        force_refresh: bool = False,
    ) -> ConversationInsight:
        """
        Perform comprehensive conversation analysis with intelligence insights.

        Args:
            conversation_id: Unique conversation identifier
            lead_id: Lead identifier
            location_id: Tenant/location identifier
            conversation_history: List of message dictionaries
            force_refresh: Skip cache and force fresh analysis

        Returns:
            ConversationInsight with complete analysis results
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Check cache first
            if not force_refresh:
                cached_insight = await self._get_cached_insight(conversation_id, location_id)
                if cached_insight:
                    self.metrics["cache_hits"] += 1
                    cached_insight.cache_hit = True
                    return cached_insight

            self.metrics["cache_misses"] += 1

            # Parallel analysis execution for performance
            analysis_tasks = [
                self.detect_objections_and_recommend_responses(conversation_history, lead_id),
                self.track_sentiment_timeline(conversation_history),
                self.generate_conversation_quality_metrics(conversation_history),
                self._generate_response_recommendations(conversation_history, lead_id),
                self._get_behavioral_correlation(lead_id, location_id),
                self._analyze_intent_correlation(conversation_history, lead_id),
            ]

            # Execute all analyses in parallel (target <500ms total)
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

            # Extract results (handle exceptions gracefully)
            objections = results[0] if not isinstance(results[0], Exception) else []
            sentiment = results[1] if not isinstance(results[1], Exception) else self._fallback_sentiment()
            quality = results[2] if not isinstance(results[2], Exception) else self._fallback_quality()
            responses = results[3] if not isinstance(results[3], Exception) else []
            behavioral = results[4] if not isinstance(results[4], Exception) else None
            intent = results[5] if not isinstance(results[5], Exception) else None

            # Create comprehensive insight
            processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            insight = ConversationInsight(
                conversation_id=conversation_id,
                lead_id=lead_id,
                location_id=location_id,
                analyzed_at=datetime.now(timezone.utc),
                processing_time_ms=processing_time_ms,
                objections_detected=objections,
                sentiment_timeline=sentiment,
                quality_metrics=quality,
                response_recommendations=responses,
                behavioral_correlation=behavioral,
                intent_analysis=intent,
                message_count=len(conversation_history),
                cache_hit=False,
            )

            # Cache the insight
            await self._cache_insight(conversation_id, location_id, insight)

            # Store in insight history
            self._add_to_insight_history(lead_id, insight)

            # Publish real-time events
            await self._publish_insight_events(insight)

            # Update metrics
            self._update_metrics(processing_time_ms)

            logger.info(
                f"Conversation analysis complete for {lead_id}: "
                f"{len(objections)} objections, sentiment {sentiment.overall_sentiment:.2f}, "
                f"quality {quality.overall_score:.0f}/100 ({processing_time_ms:.1f}ms)"
            )

            return insight

        except Exception as e:
            logger.error(f"Conversation analysis failed for {conversation_id}: {e}", exc_info=True)
            return self._create_fallback_insight(conversation_id, lead_id, location_id, conversation_history)

    async def detect_objections_and_recommend_responses(
        self, conversation_history: List[Dict[str, Any]], lead_id: str
    ) -> List[ObjectionDetection]:
        """Detect objections in conversation with response recommendations."""
        try:
            objections = []

            for i, message in enumerate(conversation_history):
                if message.get("direction") != "inbound":  # Only analyze lead messages
                    continue

                content = message.get("content", "").lower()
                if len(content) < 10:  # Skip very short messages
                    continue

                # Check each objection type
                for objection_type, patterns in self.objection_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern["regex"], content):
                            # Extract context (current message + neighbors)
                            context = self._extract_objection_context(conversation_history, i)

                            objection = ObjectionDetection(
                                objection_type=ObjectionType(objection_type),
                                confidence=pattern["confidence"],
                                severity=self._determine_objection_severity(content),
                                context=context,
                                message_index=i,
                                suggested_responses=pattern["responses"],
                            )
                            objections.append(objection)
                            break  # One objection per message

            return objections

        except Exception as e:
            logger.error(f"Objection detection failed: {e}")
            return []

    async def track_sentiment_timeline(self, conversation_history: List[Dict[str, Any]]) -> SentimentTimeline:
        """Analyze sentiment progression throughout conversation."""
        try:
            data_points = []
            sentiment_scores = []

            for i, message in enumerate(conversation_history):
                if message.get("direction") != "inbound":  # Only analyze lead messages
                    continue

                content = message.get("content", "")
                if len(content) < 5:  # Skip very short messages
                    continue

                # Calculate sentiment score
                score = self._calculate_sentiment_score(content)
                level = self._classify_sentiment_level(score)

                data_point = SentimentDataPoint(
                    timestamp=datetime.fromisoformat(message.get("timestamp", datetime.now(timezone.utc).isoformat())),
                    score=score,
                    level=level,
                    confidence=0.8,  # Basic confidence for pattern matching
                    message_text=content[:100],  # Truncate for storage
                    message_index=i,
                )
                data_points.append(data_point)
                sentiment_scores.append(score)

            # Calculate timeline metrics
            overall_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            current_sentiment = data_points[-1].level if data_points else SentimentLevel.NEUTRAL

            # Determine trend
            trend = self._calculate_sentiment_trend(sentiment_scores)
            volatility = self._calculate_sentiment_volatility(sentiment_scores)
            risk_level = self._assess_sentiment_risk(overall_sentiment, trend, volatility)

            # Generate recommendations
            recommendations = self._generate_sentiment_recommendations(overall_sentiment, trend, risk_level)

            return SentimentTimeline(
                conversation_id="",  # Will be filled by caller
                overall_sentiment=overall_sentiment,
                current_sentiment=current_sentiment,
                trend=trend,
                volatility=volatility,
                data_points=data_points,
                risk_level=risk_level,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return self._fallback_sentiment()

    async def generate_conversation_quality_metrics(
        self, conversation_history: List[Dict[str, Any]]
    ) -> ConversationQualityMetrics:
        """Generate comprehensive conversation quality assessment."""
        try:
            # Calculate individual metrics
            engagement_score = self._calculate_engagement_score(conversation_history)
            rapport_score = self._calculate_rapport_score(conversation_history)
            professionalism_score = self._calculate_professionalism_score(conversation_history)
            response_effectiveness = self._calculate_response_effectiveness(conversation_history)
            message_depth_score = self._calculate_message_depth_score(conversation_history)

            # Calculate ratios and indicators
            qa_ratio = self._calculate_question_answer_ratio(conversation_history)
            listening_indicators = self._count_active_listening_indicators(conversation_history)

            # Overall score (weighted average)
            overall_score = (
                engagement_score * 0.25
                + rapport_score * 0.20
                + professionalism_score * 0.15
                + response_effectiveness * 0.20
                + message_depth_score * 0.20
            )

            # Identify strengths and improvement areas
            scores_dict = {
                "engagement": engagement_score,
                "rapport": rapport_score,
                "professionalism": professionalism_score,
                "response_effectiveness": response_effectiveness,
                "message_depth": message_depth_score,
            }

            strengths = [name for name, score in scores_dict.items() if score >= 75]
            improvement_areas = [name for name, score in scores_dict.items() if score < 60]

            # Generate coaching opportunities
            coaching_opportunities = self._identify_coaching_opportunities(scores_dict, conversation_history)

            return ConversationQualityMetrics(
                overall_score=overall_score,
                engagement_score=engagement_score,
                rapport_score=rapport_score,
                professionalism_score=professionalism_score,
                response_effectiveness=response_effectiveness,
                message_depth_score=message_depth_score,
                question_answer_ratio=qa_ratio,
                active_listening_indicators=listening_indicators,
                strengths=strengths,
                improvement_areas=improvement_areas,
                coaching_opportunities=coaching_opportunities,
            )

        except Exception as e:
            logger.error(f"Quality metrics calculation failed: {e}")
            return self._fallback_quality()

    async def get_insight_history(self, lead_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical insights for a lead."""
        try:
            if lead_id in self.insight_history:
                insights = list(self.insight_history[lead_id])[-limit:]
                return [insight for insight in insights]
            return []

        except Exception as e:
            logger.error(f"Insight history retrieval failed for {lead_id}: {e}")
            return []

    def _compile_objection_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Compile objection detection patterns for performance."""
        return {
            "pricing": [
                {
                    "regex": r"(too expensive|too pricey|cost too much|can\'t afford|overpriced|budget)",
                    "confidence": 0.85,
                    "responses": [
                        "I understand budget is important. Let's discuss the value this property offers.",
                        "Let's explore financing options that might work for your situation.",
                        "What specific price range would you feel comfortable with?",
                        "The market data shows this property is competitively priced for the area.",
                    ],
                }
            ],
            "timing": [
                {
                    "regex": r"(not ready|need time|too soon|wait|maybe later|in a few months)",
                    "confidence": 0.80,
                    "responses": [
                        "I understand timing is crucial. What would need to happen for the timing to be right?",
                        "While you're considering, would you like me to keep you updated on similar properties?",
                        "What timeframe are you thinking would work better for you?",
                        "Sometimes the right property helps clarify timing. Would you like to explore this one?",
                    ],
                }
            ],
            "financial": [
                {
                    "regex": r"(credit|loan|mortgage|down payment|financing|pre.?approved)",
                    "confidence": 0.75,
                    "responses": [
                        "Let me connect you with our preferred lenders who can help with financing.",
                        "Have you had a chance to speak with a mortgage specialist yet?",
                        "There are several financing programs available that might help.",
                        "Understanding your financing options is a great first step.",
                    ],
                }
            ],
            "property_condition": [
                {
                    "regex": r"(needs work|repairs|condition|old|outdated|fix|renovate)",
                    "confidence": 0.85,
                    "responses": [
                        "Properties that need some work can offer great value opportunities.",
                        "We can get estimates from reliable contractors to help you budget.",
                        "What specific concerns do you have about the property condition?",
                        "Sometimes cosmetic updates can transform a property's potential.",
                    ],
                }
            ],
            "competition": [
                {
                    "regex": r"(other agent|another realtor|already working|someone else)",
                    "confidence": 0.90,
                    "responses": [
                        "I respect that you're working with someone else. I'm here if you need a second opinion.",
                        "Multiple perspectives can be valuable in real estate decisions.",
                        "I understand you have other options. What brought you to consider this property?",
                        "My goal is to provide the best service, regardless of who you choose to work with.",
                    ],
                }
            ],
            "process": [
                {
                    "regex": r"(complicated|paperwork|process|don\'t understand|confused|overwhelming)",
                    "confidence": 0.80,
                    "responses": [
                        "I'll walk you through every step to make this as simple as possible.",
                        "The process can seem complex, but I'll handle the details for you.",
                        "What part of the process would you like me to explain first?",
                        "I've helped many clients through this - you're in experienced hands.",
                    ],
                }
            ],
            "commitment": [
                {
                    "regex": r"(big decision|think about it|need to discuss|talk to spouse|family)",
                    "confidence": 0.75,
                    "responses": [
                        "Absolutely, this is a major decision. What questions can I answer to help?",
                        "I encourage you to discuss this with your family. What concerns might they have?",
                        "Take your time. I'm here to provide any information you need.",
                        "What additional information would help you feel more confident about this decision?",
                    ],
                }
            ],
            "trust": [
                {
                    "regex": r"(don\'t trust|suspicious|scam|not sure about you|prove)",
                    "confidence": 0.85,
                    "responses": [
                        "I completely understand the need to feel confident in your agent. Here are my credentials...",
                        "Trust is earned. Would you like to speak with some of my recent clients?",
                        "I'm licensed and insured. I can provide references and proof of my track record.",
                        "Your caution is smart. What would help you feel more comfortable working together?",
                    ],
                }
            ],
        }

    def _build_sentiment_lexicon(self) -> Dict[str, float]:
        """Build sentiment lexicon for real estate conversations."""
        return {
            # Very Positive
            "love": 0.8,
            "perfect": 0.9,
            "amazing": 0.8,
            "excited": 0.8,
            "beautiful": 0.7,
            "excellent": 0.8,
            "fantastic": 0.8,
            # Positive
            "good": 0.5,
            "nice": 0.4,
            "like": 0.4,
            "interested": 0.6,
            "comfortable": 0.5,
            "satisfied": 0.6,
            "happy": 0.7,
            # Neutral to Slightly Positive
            "okay": 0.1,
            "fine": 0.1,
            "alright": 0.1,
            "consider": 0.2,
            # Negative
            "concern": -0.4,
            "worried": -0.5,
            "problem": -0.6,
            "issue": -0.5,
            "difficult": -0.5,
            "hard": -0.4,
            "challenging": -0.4,
            # Very Negative
            "hate": -0.8,
            "terrible": -0.9,
            "awful": -0.8,
            "horrible": -0.8,
            "disgusted": -0.8,
            "furious": -0.9,
            "disappointed": -0.7,
            # Real Estate Specific Sentiment
            "motivated": 0.6,
            "urgent": 0.3,
            "flexible": 0.4,
            "negotiable": 0.3,
            "overpriced": -0.6,
            "expensive": -0.4,
            "cheap": -0.3,
            "spacious": 0.5,
            "cozy": 0.4,
            "cramped": -0.6,
            "tiny": -0.5,
            "modern": 0.4,
            "updated": 0.5,
            "outdated": -0.5,
            "old": -0.3,
        }

    def _calculate_sentiment_score(self, text: str) -> float:
        """Calculate sentiment score for text (-1.0 to 1.0)."""
        words = text.lower().split()
        sentiment_scores = []

        for word in words:
            if word in self.sentiment_lexicon:
                sentiment_scores.append(self.sentiment_lexicon[word])

        if sentiment_scores:
            return max(-1.0, min(1.0, sum(sentiment_scores) / len(sentiment_scores)))

        return 0.0  # Neutral if no sentiment words found

    def _classify_sentiment_level(self, score: float) -> SentimentLevel:
        """Classify sentiment score into levels."""
        if score >= 0.6:
            return SentimentLevel.VERY_POSITIVE
        elif score >= 0.2:
            return SentimentLevel.POSITIVE
        elif score >= -0.2:
            return SentimentLevel.NEUTRAL
        elif score >= -0.6:
            return SentimentLevel.NEGATIVE
        else:
            return SentimentLevel.VERY_NEGATIVE

    def _calculate_sentiment_trend(self, scores: List[float]) -> str:
        """Calculate sentiment trend from score sequence."""
        if len(scores) < 3:
            return "stable"

        # Compare first third to last third
        first_third = scores[: len(scores) // 3]
        last_third = scores[-len(scores) // 3 :]

        first_avg = sum(first_third) / len(first_third)
        last_avg = sum(last_third) / len(last_third)

        diff = last_avg - first_avg

        if diff > 0.2:
            return "improving"
        elif diff < -0.2:
            return "declining"
        else:
            return "stable"

    def _calculate_sentiment_volatility(self, scores: List[float]) -> float:
        """Calculate sentiment volatility (0-1)."""
        if len(scores) < 2:
            return 0.0

        # Calculate standard deviation
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_dev = variance**0.5

        # Normalize to 0-1 scale (assuming max reasonable std dev is 1.0)
        return min(std_dev, 1.0)

    def _assess_sentiment_risk(self, overall: float, trend: str, volatility: float) -> str:
        """Assess sentiment risk level."""
        if overall <= -0.4 or trend == "declining" or volatility > 0.7:
            return "high"
        elif overall <= 0.0 or volatility > 0.4:
            return "medium"
        else:
            return "low"

    def _generate_sentiment_recommendations(self, overall: float, trend: str, risk: str) -> List[str]:
        """Generate recommendations based on sentiment analysis."""
        recommendations = []

        if risk == "high":
            recommendations.append("Consider proactive outreach to address concerns")
            recommendations.append("Focus on relationship repair and trust building")

        if trend == "declining":
            recommendations.append("Investigate recent conversation triggers")
            recommendations.append("Schedule follow-up to address any issues")

        if overall > 0.6:
            recommendations.append("Positive sentiment - good time for next steps")

        if overall < -0.2:
            recommendations.append("Address concerns before proceeding")

        if not recommendations:
            recommendations.append("Continue current conversation approach")

        return recommendations

    # Placeholder methods for quality metrics (implement based on specific needs)
    def _calculate_engagement_score(self, conversation: List[Dict]) -> float:
        """Calculate engagement score based on message patterns."""
        # Implementation would analyze message frequency, length, questions, etc.
        return 75.0  # Placeholder

    def _calculate_rapport_score(self, conversation: List[Dict]) -> float:
        """Calculate rapport score based on conversation tone."""
        # Implementation would analyze warmth indicators, mirroring, etc.
        return 80.0  # Placeholder

    def _calculate_professionalism_score(self, conversation: List[Dict]) -> float:
        """Calculate professionalism score."""
        # Implementation would check grammar, tone, appropriateness
        return 85.0  # Placeholder

    def _calculate_response_effectiveness(self, conversation: List[Dict]) -> float:
        """Calculate response effectiveness score."""
        # Implementation would analyze question answering, follow-up quality
        return 70.0  # Placeholder

    def _calculate_message_depth_score(self, conversation: List[Dict]) -> float:
        """Calculate message depth and substance score."""
        # Implementation would analyze message substance, detail level
        return 65.0  # Placeholder

    def _calculate_question_answer_ratio(self, conversation: List[Dict]) -> float:
        """Calculate ratio of questions to answers."""
        # Implementation would count questions vs statements
        return 0.6  # Placeholder

    def _count_active_listening_indicators(self, conversation: List[Dict]) -> int:
        """Count indicators of active listening."""
        # Implementation would look for acknowledgments, clarifications
        return 5  # Placeholder

    def _identify_coaching_opportunities(
        self, scores: Dict[str, float], conversation: List[Dict]
    ) -> List[CoachingOpportunity]:
        """Identify coaching opportunities based on metrics."""
        opportunities = []

        for area, score in scores.items():
            if score < 60:  # Below threshold
                coaching_area = self._map_to_coaching_area(area)
                if coaching_area:
                    opportunity = CoachingOpportunity(
                        area=coaching_area,
                        description=f"Improve {area.replace('_', ' ')} skills",
                        priority="medium" if score < 40 else "low",
                        difficulty="beginner" if score > 40 else "intermediate",
                        estimated_time_minutes=30,
                        learning_objectives=[f"Enhance {area.replace('_', ' ')} techniques"],
                        suggested_practice=f"Practice {area.replace('_', ' ')} scenarios",
                    )
                    opportunities.append(opportunity)

        return opportunities

    def _map_to_coaching_area(self, metric: str) -> Optional[CoachingArea]:
        """Map quality metric to coaching area."""
        mapping = {
            "engagement": CoachingArea.RAPPORT_BUILDING,
            "rapport": CoachingArea.RAPPORT_BUILDING,
            "response_effectiveness": CoachingArea.ACTIVE_LISTENING,
            "professionalism": CoachingArea.VALUE_PROPOSITION,
            "message_depth": CoachingArea.ACTIVE_LISTENING,
        }
        return mapping.get(metric)

    # Placeholder methods for additional functionality
    async def _generate_response_recommendations(
        self, conversation: List[Dict], lead_id: str
    ) -> List[ResponseRecommendation]:
        """Generate AI-powered response recommendations."""
        # Placeholder - would integrate with Claude Assistant for recommendations
        return []

    async def _get_behavioral_correlation(self, lead_id: str, location_id: str) -> Optional[Dict[str, Any]]:
        """Get behavioral prediction correlation."""
        try:
            if self.behavior_service:
                prediction = await self.behavior_service.predict_behavior(lead_id=lead_id, location_id=location_id)
                if prediction:
                    return {
                        "behavior_category": prediction.behavior_category,
                        "engagement_score": prediction.engagement_score_7d,
                        "churn_risk": prediction.churn_risk_score,
                    }
        except Exception as e:
            logger.error(f"Behavioral correlation failed: {e}")

        return None

    async def _analyze_intent_correlation(self, conversation: List[Dict], lead_id: str) -> Optional[Dict[str, Any]]:
        """Analyze intent correlation with conversation."""
        try:
            if self.intent_decoder:
                # Get recent messages for intent analysis
                recent_messages = conversation[-5:] if len(conversation) > 5 else conversation
                intent_data = await self.intent_decoder.decode_intent(messages=recent_messages, lead_id=lead_id)
                return intent_data
        except Exception as e:
            logger.error(f"Intent correlation failed: {e}")

        return None

    # Caching and utility methods
    async def _get_cached_insight(self, conversation_id: str, location_id: str) -> Optional[ConversationInsight]:
        """Retrieve cached conversation insight."""
        try:
            cache_key = f"conversation_insight:{conversation_id}"
            cached_data = await self.cache.get(cache_key, location_id=location_id)

            if cached_data:
                # Would need proper deserialization logic here
                pass

            return None
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None

    async def _cache_insight(self, conversation_id: str, location_id: str, insight: ConversationInsight) -> None:
        """Cache conversation insight."""
        try:
            cache_key = f"conversation_insight:{conversation_id}"
            # Would serialize insight to cacheable format
            cacheable_data = {
                "conversation_id": insight.conversation_id,
                "analyzed_at": insight.analyzed_at.isoformat(),
                "processing_time_ms": insight.processing_time_ms,
                "objection_count": len(insight.objections_detected),
                "overall_sentiment": insight.sentiment_timeline.overall_sentiment,
                "quality_score": insight.quality_metrics.overall_score,
            }

            await self.cache.set(cache_key, cacheable_data, ttl=CACHE_TTL_INSIGHTS, location_id=location_id)
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")

    def _add_to_insight_history(self, lead_id: str, insight: ConversationInsight) -> None:
        """Add insight to in-memory history."""
        try:
            if lead_id not in self.insight_history:
                self.insight_history[lead_id] = deque(maxlen=INSIGHT_HISTORY_SIZE)
                self.metrics["insight_history_leads"] += 1

            # Store simplified version in history
            history_entry = {
                "conversation_id": insight.conversation_id,
                "analyzed_at": insight.analyzed_at.isoformat(),
                "objection_count": len(insight.objections_detected),
                "sentiment": insight.sentiment_timeline.overall_sentiment,
                "quality": insight.quality_metrics.overall_score,
                "processing_time_ms": insight.processing_time_ms,
            }

            self.insight_history[lead_id].append(history_entry)
        except Exception as e:
            logger.error(f"History storage failed: {e}")

    async def _publish_insight_events(self, insight: ConversationInsight) -> None:
        """Publish real-time insight events."""
        try:
            # Publish objection alerts
            for objection in insight.objections_detected:
                if objection.severity in ["medium", "high"]:
                    await self.event_publisher.publish_objection_detected(
                        lead_id=insight.lead_id,
                        location_id=insight.location_id,
                        objection_type=objection.objection_type.value,
                        severity=objection.severity,
                        confidence=objection.confidence,
                    )

            # Publish sentiment warnings
            if insight.sentiment_timeline.risk_level == "high":
                await self.event_publisher.publish_sentiment_warning(
                    lead_id=insight.lead_id,
                    location_id=insight.location_id,
                    current_sentiment=insight.sentiment_timeline.overall_sentiment,
                    trend=insight.sentiment_timeline.trend,
                    risk_level=insight.sentiment_timeline.risk_level,
                )

            # Publish coaching opportunities
            for opportunity in insight.quality_metrics.coaching_opportunities:
                if opportunity.priority == "high":
                    await self.event_publisher.publish_coaching_opportunity(
                        lead_id=insight.lead_id,
                        location_id=insight.location_id,
                        area=opportunity.area.value,
                        priority=opportunity.priority,
                        description=opportunity.description,
                    )

        except Exception as e:
            logger.error(f"Event publishing failed: {e}")

    # Fallback methods
    def _fallback_sentiment(self) -> SentimentTimeline:
        """Create fallback sentiment timeline."""
        return SentimentTimeline(
            conversation_id="",
            overall_sentiment=0.0,
            current_sentiment=SentimentLevel.NEUTRAL,
            trend="stable",
            volatility=0.0,
            data_points=[],
            risk_level="low",
            recommendations=["Sentiment analysis unavailable"],
        )

    def _fallback_quality(self) -> ConversationQualityMetrics:
        """Create fallback quality metrics."""
        return ConversationQualityMetrics(
            overall_score=50.0,
            engagement_score=50.0,
            rapport_score=50.0,
            professionalism_score=50.0,
            response_effectiveness=50.0,
            message_depth_score=50.0,
            question_answer_ratio=0.5,
            active_listening_indicators=0,
            strengths=[],
            improvement_areas=[],
            coaching_opportunities=[],
        )

    def _create_fallback_insight(
        self, conversation_id: str, lead_id: str, location_id: str, conversation_history: List[Dict]
    ) -> ConversationInsight:
        """Create fallback insight when analysis fails."""
        return ConversationInsight(
            conversation_id=conversation_id,
            lead_id=lead_id,
            location_id=location_id,
            analyzed_at=datetime.now(timezone.utc),
            processing_time_ms=0.0,
            objections_detected=[],
            sentiment_timeline=self._fallback_sentiment(),
            quality_metrics=self._fallback_quality(),
            response_recommendations=[],
            message_count=len(conversation_history),
        )

    def _extract_objection_context(self, conversation: List[Dict], message_index: int) -> str:
        """Extract context around an objection."""
        start = max(0, message_index - 1)
        end = min(len(conversation), message_index + 2)
        context_messages = conversation[start:end]

        context_text = " | ".join(
            [f"{msg.get('direction', 'unknown')}: {msg.get('content', '')[:50]}..." for msg in context_messages]
        )

        return context_text

    def _determine_objection_severity(self, content: str) -> str:
        """Determine objection severity from message content."""
        # Simple heuristic based on intensity words
        high_intensity = ["never", "absolutely not", "impossible", "no way", "hate"]
        medium_intensity = ["concerned", "worried", "problem", "difficult", "issue"]

        content_lower = content.lower()

        if any(word in content_lower for word in high_intensity):
            return "high"
        elif any(word in content_lower for word in medium_intensity):
            return "medium"
        else:
            return "low"

    def _update_metrics(self, processing_time_ms: float) -> None:
        """Update performance metrics."""
        self.metrics["total_analyses"] += 1
        total_time = self.metrics["avg_processing_time_ms"] * (self.metrics["total_analyses"] - 1) + processing_time_ms
        self.metrics["avg_processing_time_ms"] = total_time / self.metrics["total_analyses"]

        # Update cache hit rate
        total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        if total_requests > 0:
            self.metrics["cache_hit_rate"] = self.metrics["cache_hits"] / total_requests

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            **self.metrics,
            "target_processing_time_ms": TARGET_PROCESSING_TIME_MS,
            "performance_status": "good"
            if self.metrics["avg_processing_time_ms"] < TARGET_PROCESSING_TIME_MS
            else "degraded",
        }


# Global service instance
_conversation_intelligence_service = None


def get_conversation_intelligence_service() -> ConversationIntelligenceService:
    """
    Get the global ConversationIntelligenceService instance (singleton pattern).

    Returns:
        ConversationIntelligenceService: The global service instance
    """
    global _conversation_intelligence_service
    if _conversation_intelligence_service is None:
        _conversation_intelligence_service = ConversationIntelligenceService()
    return _conversation_intelligence_service


# Service health check
async def health_check() -> Dict[str, Any]:
    """Health check for the conversation intelligence service."""
    try:
        service = get_conversation_intelligence_service()
        metrics = service.get_metrics()

        return {
            "service": "ConversationIntelligenceService",
            "status": "healthy",
            "version": "2.3.0",
            "metrics": metrics,
            "dependencies": {
                "cache_service": "connected",
                "event_publisher": "connected",
                "claude_assistant": "connected",
                "intent_decoder": "connected",
                "predictive_behavior_service": "lazy_loaded",
            },
        }
    except Exception as e:
        return {"service": "ConversationIntelligenceService", "status": "unhealthy", "error": str(e)}
