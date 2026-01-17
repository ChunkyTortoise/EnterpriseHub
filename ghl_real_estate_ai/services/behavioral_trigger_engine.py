"""
Behavioral Trigger Engine - Predictive Lead Scoring with Behavioral Analysis.

Implements 2026 real estate best practices:
- Predictive seller intelligence
- Behavioral pattern detection
- Optimal contact time prediction
- Multi-signal analysis (engagement, timing, market conditions)

Based on research: "Predictive seller intelligence will dominate" - Fello.ai 2026
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import numpy as np

from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.database_service import get_database

logger = get_logger(__name__)


class BehavioralSignal(Enum):
    """Types of behavioral signals for prediction."""

    PROPERTY_SEARCH = "property_search"
    NEIGHBORHOOD_RESEARCH = "neighborhood_research"
    PRICING_TOOL_USAGE = "pricing_tool_usage"
    AGENT_INQUIRY = "agent_inquiry"
    MARKET_REPORT_ENGAGEMENT = "market_report_engagement"
    EMAIL_OPENS = "email_opens"
    SMS_RESPONSES = "sms_responses"
    WEBSITE_VISITS = "website_visits"
    LISTING_VIEWS = "listing_views"
    VIRTUAL_TOUR_VIEWS = "virtual_tour_views"


class IntentLevel(Enum):
    """Lead intent levels based on behavioral analysis."""

    COLD = "cold"  # <20% likelihood
    WARM = "warm"  # 20-50% likelihood
    HOT = "hot"  # 50-80% likelihood
    URGENT = "urgent"  # >80% likelihood


@dataclass
class BehavioralPattern:
    """Detected behavioral pattern for a lead."""

    lead_id: str
    signal_type: BehavioralSignal
    frequency: int  # Number of occurrences
    recency_hours: float  # Hours since last occurrence
    trend: str  # "increasing", "stable", "decreasing"
    score_impact: float  # -1.0 to 1.0


@dataclass
class PredictiveSellScore:
    """Predictive scoring result with timing and messaging recommendations."""

    lead_id: str
    likelihood_score: float  # 0-100
    intent_level: IntentLevel
    optimal_contact_window: Tuple[int, int]  # (hour_start, hour_end) in 24h format
    recommended_channel: str  # "sms", "email", "call"
    recommended_message: str
    confidence: float  # 0-1.0
    key_signals: List[BehavioralPattern] = field(default_factory=list)
    market_context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class BehavioralTriggerEngine:
    """
    Analyzes engagement patterns to predict listing likelihood and optimal contact strategy.

    Key Features:
    - Multi-signal behavioral analysis
    - Time-series pattern detection
    - Optimal contact time prediction
    - Personalized message generation
    - Market condition integration
    """

    def __init__(self):
        self.cache = get_cache_service()

        # Signal weights (calibrated for real estate leads)
        self.signal_weights = {
            BehavioralSignal.PRICING_TOOL_USAGE: 0.25,
            BehavioralSignal.AGENT_INQUIRY: 0.20,
            BehavioralSignal.NEIGHBORHOOD_RESEARCH: 0.15,
            BehavioralSignal.MARKET_REPORT_ENGAGEMENT: 0.15,
            BehavioralSignal.PROPERTY_SEARCH: 0.10,
            BehavioralSignal.LISTING_VIEWS: 0.05,
            BehavioralSignal.EMAIL_OPENS: 0.05,
            BehavioralSignal.WEBSITE_VISITS: 0.03,
            BehavioralSignal.SMS_RESPONSES: 0.02,
        }

        # Recency decay factor (hours)
        self.recency_decay_hours = 72  # 3 days

    async def analyze_lead_behavior(
        self, lead_id: str, activity_data: Dict[str, Any]
    ) -> PredictiveSellScore:
        """
        Analyze lead behavior and generate predictive score.

        Args:
            lead_id: Lead identifier
            activity_data: Dictionary containing lead activity metrics:
                {
                    "property_searches": List[Dict],
                    "email_interactions": List[Dict],
                    "website_visits": List[Dict],
                    "pricing_tool_uses": List[Dict],
                    "agent_inquiries": List[Dict],
                    ...
                }

        Returns:
            PredictiveSellScore with likelihood and recommendations
        """
        # Check cache first
        cache_key = f"behavioral_score:{lead_id}"
        cached_score = await self.cache.get(cache_key)

        if cached_score:
            logger.info(f"✅ Retrieved cached behavioral score for lead {lead_id}")
            return cached_score

        # Extract behavioral patterns
        patterns = await self._extract_patterns(lead_id, activity_data)

        # Calculate composite score
        likelihood_score = await self._calculate_likelihood_score(patterns)

        # Determine intent level
        intent_level = self._classify_intent(likelihood_score)

        # Predict optimal contact time
        contact_window = await self._predict_optimal_contact_time(
            lead_id, activity_data
        )

        # Determine best channel
        recommended_channel = await self._predict_best_channel(activity_data)

        # Generate personalized message
        recommended_message = await self._generate_personalized_message(
            lead_id, patterns, intent_level
        )

        # Calculate confidence
        confidence = self._calculate_confidence(patterns)

        # Get market context
        market_context = await self._get_market_context()

        # Create predictive score
        score = PredictiveSellScore(
            lead_id=lead_id,
            likelihood_score=likelihood_score,
            intent_level=intent_level,
            optimal_contact_window=contact_window,
            recommended_channel=recommended_channel,
            recommended_message=recommended_message,
            confidence=confidence,
            key_signals=patterns,
            market_context=market_context,
        )

        # Cache for 1 hour
        await self.cache.set(cache_key, score, ttl=3600)

        logger.info(
            f"✅ Behavioral analysis complete for lead {lead_id}: "
            f"{likelihood_score:.1f}% likelihood ({intent_level.value})"
        )

        return score

    async def detect_selling_signals(
        self, contact_id: str, activity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect selling signals for a contact (predictive intelligence).

        Args:
            contact_id: Contact identifier
            activity_data: Activity data for analysis

        Returns:
            Dictionary with selling signals and recommendations
        """
        score = await self.analyze_lead_behavior(contact_id, activity_data)

        return {
            "contact_id": contact_id,
            "selling_likelihood": score.likelihood_score,
            "intent_level": score.intent_level.value,
            "optimal_contact_time": f"{score.optimal_contact_window[0]:02d}:00 - {score.optimal_contact_window[1]:02d}:00",
            "recommended_channel": score.recommended_channel,
            "recommended_message": score.recommended_message,
            "confidence": score.confidence,
            "key_signals": [
                {
                    "type": p.signal_type.value,
                    "frequency": p.frequency,
                    "recency_hours": p.recency_hours,
                    "trend": p.trend,
                }
                for p in score.key_signals
            ],
            "timestamp": score.timestamp.isoformat(),
        }

    async def get_high_intent_leads(
        self, min_likelihood: float = 50.0, limit: int = 50
    ) -> List[str]:
        """
        Get leads with high intent scores for autonomous follow-up.

        Args:
            min_likelihood: Minimum likelihood threshold (0-100)
            limit: Maximum number of leads to return

        Returns:
            List of lead IDs sorted by likelihood (highest first)
        """
        try:
            db = await get_database()
            return await db.get_high_intent_leads(min_score=int(min_likelihood), limit=limit)
        except Exception as e:
            logger.error(f"Error getting high intent leads from database: {e}")
            return []

    # Private helper methods

    async def _extract_patterns(
        self, lead_id: str, activity_data: Dict[str, Any]
    ) -> List[BehavioralPattern]:
        """Extract behavioral patterns from activity data."""
        patterns = []

        # Analyze each signal type
        for signal_type in BehavioralSignal:
            signal_key = signal_type.value + "s"  # e.g., "property_searches"

            if signal_key in activity_data:
                activities = activity_data[signal_key]

                if activities:
                    # Calculate frequency
                    frequency = len(activities)

                    # Calculate recency (hours since last activity)
                    last_activity = max(
                        (
                            datetime.fromisoformat(a["timestamp"])
                            if isinstance(a.get("timestamp"), str)
                            else a.get("timestamp", datetime.now())
                        )
                        for a in activities
                    )
                    recency_hours = (datetime.now() - last_activity).total_seconds() / 3600

                    # Detect trend (simple: compare first half to second half)
                    trend = self._detect_trend(activities)

                    # Calculate score impact
                    score_impact = self._calculate_signal_impact(
                        signal_type, frequency, recency_hours, trend
                    )

                    pattern = BehavioralPattern(
                        lead_id=lead_id,
                        signal_type=signal_type,
                        frequency=frequency,
                        recency_hours=recency_hours,
                        trend=trend,
                        score_impact=score_impact,
                    )

                    patterns.append(pattern)

        return patterns

    def _detect_trend(self, activities: List[Dict]) -> str:
        """Detect trend in activity frequency."""
        if len(activities) < 4:
            return "stable"

        mid = len(activities) // 2
        first_half = len(activities[:mid])
        second_half = len(activities[mid:])

        if second_half > first_half * 1.5:
            return "increasing"
        elif second_half < first_half * 0.5:
            return "decreasing"
        else:
            return "stable"

    def _calculate_signal_impact(
        self, signal_type: BehavioralSignal, frequency: int, recency_hours: float, trend: str
    ) -> float:
        """Calculate impact of a signal on overall score."""
        # Base weight for this signal type
        base_weight = self.signal_weights.get(signal_type, 0.05)

        # Frequency multiplier (logarithmic scale)
        freq_multiplier = min(np.log1p(frequency) / 3, 1.0)

        # Recency decay (exponential)
        recency_multiplier = np.exp(-recency_hours / self.recency_decay_hours)

        # Trend multiplier
        trend_multiplier = {"increasing": 1.3, "stable": 1.0, "decreasing": 0.7}.get(
            trend, 1.0
        )

        impact = base_weight * freq_multiplier * recency_multiplier * trend_multiplier

        return min(impact, 1.0)

    async def _calculate_likelihood_score(
        self, patterns: List[BehavioralPattern]
    ) -> float:
        """Calculate composite likelihood score (0-100)."""
        if not patterns:
            return 0.0

        # Weighted sum of signal impacts
        total_impact = sum(p.score_impact for p in patterns)

        # Normalize to 0-100 scale
        likelihood = min(total_impact * 100, 100.0)

        return likelihood

    def _classify_intent(self, likelihood_score: float) -> IntentLevel:
        """Classify intent level based on likelihood score."""
        if likelihood_score >= 80:
            return IntentLevel.URGENT
        elif likelihood_score >= 50:
            return IntentLevel.HOT
        elif likelihood_score >= 20:
            return IntentLevel.WARM
        else:
            return IntentLevel.COLD

    async def _predict_optimal_contact_time(
        self, lead_id: str, activity_data: Dict[str, Any]
    ) -> Tuple[int, int]:
        """
        Predict optimal contact time window based on activity patterns.

        Returns:
            Tuple of (start_hour, end_hour) in 24h format
        """
        # Analyze historical engagement times
        engagement_hours = []

        for activity_type in ["email_interactions", "sms_responses", "website_visits"]:
            if activity_type in activity_data:
                for activity in activity_data[activity_type]:
                    timestamp = activity.get("timestamp")
                    if timestamp:
                        dt = (
                            datetime.fromisoformat(timestamp)
                            if isinstance(timestamp, str)
                            else timestamp
                        )
                        engagement_hours.append(dt.hour)

        if engagement_hours:
            # Find peak engagement window
            hour_counts = {}
            for hour in engagement_hours:
                hour_counts[hour] = hour_counts.get(hour, 0) + 1

            peak_hour = max(hour_counts, key=hour_counts.get)

            # Return 2-hour window around peak
            start_hour = max(peak_hour - 1, 9)  # Not before 9 AM
            end_hour = min(peak_hour + 1, 18)  # Not after 6 PM

            return (start_hour, end_hour)

        # Default to business hours midday
        return (12, 14)

    async def _predict_best_channel(self, activity_data: Dict[str, Any]) -> str:
        """Predict best communication channel based on response rates."""
        channel_scores = {"email": 0, "sms": 0, "call": 0}

        # Score email engagement
        if "email_interactions" in activity_data:
            email_opens = sum(
                1 for e in activity_data["email_interactions"] if e.get("opened")
            )
            channel_scores["email"] = email_opens

        # Score SMS engagement
        if "sms_responses" in activity_data:
            sms_responses = len(activity_data["sms_responses"])
            channel_scores["sms"] = sms_responses * 1.5  # Weight SMS higher

        # Score call engagement
        if "agent_inquiries" in activity_data:
            call_inquiries = sum(
                1 for a in activity_data["agent_inquiries"] if a.get("type") == "call"
            )
            channel_scores["call"] = call_inquiries * 2  # Weight calls highest

        # Return channel with highest score
        if max(channel_scores.values()) > 0:
            return max(channel_scores, key=channel_scores.get)

        # Default to SMS for real estate
        return "sms"

    async def _generate_personalized_message(
        self, lead_id: str, patterns: List[BehavioralPattern], intent_level: IntentLevel
    ) -> str:
        """Generate personalized outreach message based on behavioral patterns."""
        # Identify dominant signal
        if patterns:
            dominant_pattern = max(patterns, key=lambda p: p.score_impact)

            message_templates = {
                BehavioralSignal.PRICING_TOOL_USAGE: "I noticed you've been researching property values in your area. I'd love to provide you with a complimentary market analysis - would that be helpful?",
                BehavioralSignal.AGENT_INQUIRY: "Thanks for your interest in connecting! I'm available to discuss your real estate needs. What's the best time for a quick chat?",
                BehavioralSignal.NEIGHBORHOOD_RESEARCH: "I see you've been exploring neighborhoods. I have deep market knowledge in this area and would be happy to share insights. When works for you?",
                BehavioralSignal.MARKET_REPORT_ENGAGEMENT: "Great to see you're staying informed on the market! I can provide exclusive insights on current trends. Interested in learning more?",
                BehavioralSignal.PROPERTY_SEARCH: "I noticed you've been looking at properties. I can help you navigate the current market and find exactly what you're looking for. Let's connect!",
            }

            base_message = message_templates.get(
                dominant_pattern.signal_type,
                "I'd love to help with your real estate needs. When's a good time to connect?",
            )

            # Adjust urgency based on intent level
            if intent_level == IntentLevel.URGENT:
                base_message = f"🔥 URGENT: {base_message}"
            elif intent_level == IntentLevel.HOT:
                base_message = f"⭐ {base_message}"

            return base_message

        return "I'd love to help with your real estate needs. When's a good time to connect?"

    async def _get_market_context(self) -> Dict[str, Any]:
        """Get current market context for enhanced predictions."""
        # In production, this would fetch real market data
        # For now, return placeholder

        return {
            "market_trend": "sellers_market",
            "average_days_on_market": 25,
            "inventory_level": "low",
            "median_price_trend": "increasing",
        }

    def _calculate_confidence(self, patterns: List[BehavioralPattern]) -> float:
        """Calculate confidence score (0-1.0) based on data quality."""
        if not patterns:
            return 0.0

        # More patterns = higher confidence
        pattern_confidence = min(len(patterns) / 5, 1.0)

        # Recent data = higher confidence
        avg_recency = sum(p.recency_hours for p in patterns) / len(patterns)
        recency_confidence = np.exp(-avg_recency / self.recency_decay_hours)

        # Combined confidence
        confidence = (pattern_confidence + recency_confidence) / 2

        return min(confidence, 1.0)


# Global singleton
_behavioral_engine = None


def get_behavioral_trigger_engine() -> BehavioralTriggerEngine:
    """Get singleton behavioral trigger engine."""
    global _behavioral_engine
    if _behavioral_engine is None:
        _behavioral_engine = BehavioralTriggerEngine()
    return _behavioral_engine
