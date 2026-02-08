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
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.database_service import get_database

logger = get_logger(__name__)


class BehavioralSignal(Enum):
    """Types of behavioral signals for prediction - 25+ signals for comprehensive analysis."""

    # Property Research Signals
    PROPERTY_SEARCH = "property_search"
    NEIGHBORHOOD_RESEARCH = "neighborhood_research"
    PRICING_TOOL_USAGE = "pricing_tool_usage"
    LISTING_VIEWS = "listing_views"
    VIRTUAL_TOUR_VIEWS = "virtual_tour_views"
    PROPERTY_DETAIL_DOWNLOADS = "property_detail_downloads"
    MAP_INTERACTIONS = "map_interactions"
    SCHOOL_DISTRICT_RESEARCH = "school_district_research"
    COMMUTE_TIME_CHECKS = "commute_time_checks"
    PROPERTY_COMPARISON_USAGE = "property_comparison_usage"

    # Communication Signals
    AGENT_INQUIRY = "agent_inquiry"
    EMAIL_OPENS = "email_opens"
    SMS_RESPONSES = "sms_responses"
    PHONE_CALL_DURATION = "phone_call_duration"
    CALLBACK_REQUESTS = "callback_requests"
    FORM_SUBMISSIONS = "form_submissions"
    CHAT_INTERACTIONS = "chat_interactions"
    SOCIAL_MEDIA_ENGAGEMENT = "social_media_engagement"

    # Engagement Signals
    WEBSITE_VISITS = "website_visits"
    MARKET_REPORT_ENGAGEMENT = "market_report_engagement"
    NEWSLETTER_ENGAGEMENT = "newsletter_engagement"
    VIDEO_CONSUMPTION = "video_consumption"
    WEBINAR_ATTENDANCE = "webinar_attendance"
    BLOG_POST_ENGAGEMENT = "blog_post_engagement"
    TESTIMONIAL_VIEWS = "testimonial_views"

    # Intent Signals
    MORTGAGE_CALCULATOR_USAGE = "mortgage_calculator_usage"
    PRE_APPROVAL_INQUIRY = "pre_approval_inquiry"
    HOME_VALUATION_REQUESTS = "home_valuation_requests"
    CLOSING_COST_CALCULATOR = "closing_cost_calculator"
    RENT_VS_BUY_CALCULATOR = "rent_vs_buy_calculator"
    INSPECTION_SERVICE_INQUIRY = "inspection_service_inquiry"
    INSURANCE_QUOTE_REQUESTS = "insurance_quote_requests"

    # Behavioral Patterns
    REPEAT_VISITOR = "repeat_visitor"
    SESSION_DURATION_LONG = "session_duration_long"
    MOBILE_USAGE_PATTERN = "mobile_usage_pattern"
    WEEKEND_BROWSING = "weekend_browsing"
    EVENING_ACTIVITY = "evening_activity"
    MULTIPLE_DEVICE_ACCESS = "multiple_device_access"

    # Advanced Signals
    DOCUMENT_UPLOADS = "document_uploads"
    CALENDAR_SCHEDULING = "calendar_scheduling"
    REFERRAL_ACTIVITY = "referral_activity"
    REVIEW_SUBMISSION = "review_submission"
    SAVED_SEARCHES = "saved_searches"
    PRICE_ALERT_SUBSCRIPTIONS = "price_alert_subscriptions"


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

        # Signal weights (calibrated for real estate leads - comprehensive scoring)
        self.signal_weights = {
            # High Intent Signals (15-30%)
            BehavioralSignal.PRE_APPROVAL_INQUIRY: 0.30,
            BehavioralSignal.PRICING_TOOL_USAGE: 0.25,
            BehavioralSignal.AGENT_INQUIRY: 0.25,
            BehavioralSignal.HOME_VALUATION_REQUESTS: 0.20,
            BehavioralSignal.CALLBACK_REQUESTS: 0.20,
            BehavioralSignal.MORTGAGE_CALCULATOR_USAGE: 0.18,
            BehavioralSignal.CALENDAR_SCHEDULING: 0.18,
            BehavioralSignal.DOCUMENT_UPLOADS: 0.15,
            # Medium Intent Signals (8-15%)
            BehavioralSignal.NEIGHBORHOOD_RESEARCH: 0.15,
            BehavioralSignal.MARKET_REPORT_ENGAGEMENT: 0.15,
            BehavioralSignal.CLOSING_COST_CALCULATOR: 0.12,
            BehavioralSignal.RENT_VS_BUY_CALCULATOR: 0.12,
            BehavioralSignal.VIRTUAL_TOUR_VIEWS: 0.12,
            BehavioralSignal.FORM_SUBMISSIONS: 0.10,
            BehavioralSignal.PROPERTY_SEARCH: 0.10,
            BehavioralSignal.PROPERTY_COMPARISON_USAGE: 0.10,
            BehavioralSignal.CHAT_INTERACTIONS: 0.10,
            BehavioralSignal.PHONE_CALL_DURATION: 0.10,
            BehavioralSignal.INSPECTION_SERVICE_INQUIRY: 0.08,
            BehavioralSignal.INSURANCE_QUOTE_REQUESTS: 0.08,
            # Engagement Signals (4-8%)
            BehavioralSignal.PROPERTY_DETAIL_DOWNLOADS: 0.08,
            BehavioralSignal.SCHOOL_DISTRICT_RESEARCH: 0.07,
            BehavioralSignal.MAP_INTERACTIONS: 0.07,
            BehavioralSignal.COMMUTE_TIME_CHECKS: 0.07,
            BehavioralSignal.SAVED_SEARCHES: 0.06,
            BehavioralSignal.PRICE_ALERT_SUBSCRIPTIONS: 0.06,
            BehavioralSignal.WEBINAR_ATTENDANCE: 0.06,
            BehavioralSignal.VIDEO_CONSUMPTION: 0.05,
            BehavioralSignal.LISTING_VIEWS: 0.05,
            BehavioralSignal.EMAIL_OPENS: 0.05,
            BehavioralSignal.NEWSLETTER_ENGAGEMENT: 0.04,
            BehavioralSignal.BLOG_POST_ENGAGEMENT: 0.04,
            # Behavioral Pattern Signals (2-5%)
            BehavioralSignal.SESSION_DURATION_LONG: 0.05,
            BehavioralSignal.REPEAT_VISITOR: 0.04,
            BehavioralSignal.WEEKEND_BROWSING: 0.04,
            BehavioralSignal.EVENING_ACTIVITY: 0.04,
            BehavioralSignal.MULTIPLE_DEVICE_ACCESS: 0.03,
            BehavioralSignal.MOBILE_USAGE_PATTERN: 0.03,
            BehavioralSignal.SMS_RESPONSES: 0.03,
            BehavioralSignal.WEBSITE_VISITS: 0.03,
            # Community Signals (2-4%)
            BehavioralSignal.SOCIAL_MEDIA_ENGAGEMENT: 0.04,
            BehavioralSignal.TESTIMONIAL_VIEWS: 0.03,
            BehavioralSignal.REFERRAL_ACTIVITY: 0.03,
            BehavioralSignal.REVIEW_SUBMISSION: 0.02,
        }

        # Recency decay factor (hours)
        self.recency_decay_hours = 72  # 3 days

    async def analyze_lead_behavior(self, lead_id: str, activity_data: Dict[str, Any]) -> PredictiveSellScore:
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
        contact_window = await self._predict_optimal_contact_time(lead_id, activity_data)

        # Determine best channel
        recommended_channel = await self._predict_best_channel(activity_data)

        # Generate personalized message
        recommended_message = await self._generate_personalized_message(lead_id, patterns, intent_level)

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

    async def detect_selling_signals(self, contact_id: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
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

    async def get_high_intent_leads(self, min_likelihood: float = 50.0, limit: int = 50) -> List[str]:
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

    async def _extract_patterns(self, lead_id: str, activity_data: Dict[str, Any]) -> List[BehavioralPattern]:
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
                    score_impact = self._calculate_signal_impact(signal_type, frequency, recency_hours, trend)

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
        trend_multiplier = {"increasing": 1.3, "stable": 1.0, "decreasing": 0.7}.get(trend, 1.0)

        impact = base_weight * freq_multiplier * recency_multiplier * trend_multiplier

        return min(impact, 1.0)

    async def _calculate_likelihood_score(self, patterns: List[BehavioralPattern]) -> float:
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

    async def _predict_optimal_contact_time(self, lead_id: str, activity_data: Dict[str, Any]) -> Tuple[int, int]:
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
                        dt = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
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
            email_opens = sum(1 for e in activity_data["email_interactions"] if e.get("opened"))
            channel_scores["email"] = email_opens

        # Score SMS engagement
        if "sms_responses" in activity_data:
            sms_responses = len(activity_data["sms_responses"])
            channel_scores["sms"] = sms_responses * 1.5  # Weight SMS higher

        # Score call engagement
        if "agent_inquiries" in activity_data:
            call_inquiries = sum(1 for a in activity_data["agent_inquiries"] if a.get("type") == "call")
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
                # High Intent Signals
                BehavioralSignal.PRE_APPROVAL_INQUIRY: "🏠 I see you're exploring pre-approval options! I work with top lenders who can fast-track your application. Ready to get started?",
                BehavioralSignal.PRICING_TOOL_USAGE: "I noticed you've been researching property values in your area. I'd love to provide you with a complimentary market analysis - would that be helpful?",
                BehavioralSignal.AGENT_INQUIRY: "Thanks for your interest in connecting! I'm available to discuss your real estate needs. What's the best time for a quick chat?",
                BehavioralSignal.HOME_VALUATION_REQUESTS: "💰 I see you're curious about your home's value! I can provide a detailed CMA with recent sales data. Interested?",
                BehavioralSignal.CALLBACK_REQUESTS: "📞 Thanks for requesting a callback! I'm ready to discuss your real estate goals. What time works best today?",
                BehavioralSignal.MORTGAGE_CALCULATOR_USAGE: "🧮 I noticed you're running mortgage calculations! I can connect you with lenders offering great rates. Want to explore your options?",
                BehavioralSignal.CALENDAR_SCHEDULING: "📅 I see you're looking to schedule time! I have openings this week to discuss your property needs. Shall we set something up?",
                BehavioralSignal.DOCUMENT_UPLOADS: "📄 Thank you for uploading documents! I'm reviewing everything and will have insights ready for our next conversation.",
                # Medium Intent Signals
                BehavioralSignal.NEIGHBORHOOD_RESEARCH: "I see you've been exploring neighborhoods. I have deep market knowledge in this area and would be happy to share insights. When works for you?",
                BehavioralSignal.MARKET_REPORT_ENGAGEMENT: "Great to see you're staying informed on the market! I can provide exclusive insights on current trends. Interested in learning more?",
                BehavioralSignal.CLOSING_COST_CALCULATOR: "💸 I noticed you're calculating closing costs. I can break down all the numbers and fees for you. Want a detailed estimate?",
                BehavioralSignal.RENT_VS_BUY_CALCULATOR: "🏡 Weighing rent vs. buy? Smart move! I can show you scenarios specific to your situation. Ready to crunch the real numbers?",
                BehavioralSignal.VIRTUAL_TOUR_VIEWS: "🎥 I saw you took virtual tours! Nothing beats seeing properties in person. Want to schedule some showings this weekend?",
                BehavioralSignal.FORM_SUBMISSIONS: "✅ Thanks for reaching out! I've received your information and have some great properties that match your criteria.",
                BehavioralSignal.PROPERTY_SEARCH: "I noticed you've been looking at properties. I can help you navigate the current market and find exactly what you're looking for. Let's connect!",
                BehavioralSignal.PROPERTY_COMPARISON_USAGE: "📊 Great to see you comparing properties! I can provide insights on each and help you make the best choice.",
                BehavioralSignal.CHAT_INTERACTIONS: "💬 Enjoyed our chat! I'm here whenever you have more questions about the market or specific properties.",
                BehavioralSignal.PHONE_CALL_DURATION: "📱 Thanks for taking time to chat! Following up on our conversation - do you have any other questions?",
                # Engagement Signals
                BehavioralSignal.PROPERTY_DETAIL_DOWNLOADS: "📋 I see you downloaded property details! I have additional market insights that could be valuable. Want to see them?",
                BehavioralSignal.SCHOOL_DISTRICT_RESEARCH: "🎓 Researching schools shows great planning! I know the best family-friendly neighborhoods. Want the inside scoop?",
                BehavioralSignal.MAP_INTERACTIONS: "🗺️ I noticed you're exploring the area on maps! I can share insider tips about different neighborhoods. Interested?",
                BehavioralSignal.COMMUTE_TIME_CHECKS: "⏰ Smart to check commute times! I know properties with the best access to major routes. Want to see options?",
                BehavioralSignal.SAVED_SEARCHES: "🔍 I see you saved some searches! I get notified of new listings daily and can share matches. Sound good?",
                BehavioralSignal.PRICE_ALERT_SUBSCRIPTIONS: "🔔 Great job setting up price alerts! I can also watch for off-market opportunities. Want me to keep an eye out?",
                BehavioralSignal.WEBINAR_ATTENDANCE: "🎯 Thanks for joining the webinar! I have additional resources that dive deeper into the topics we covered.",
                BehavioralSignal.VIDEO_CONSUMPTION: "🎬 Glad you found our video content helpful! I have more insider tips to share. Coffee chat soon?",
                # Behavioral Patterns
                BehavioralSignal.SESSION_DURATION_LONG: "⏱️ I can see you're seriously researching! Your dedication shows you're ready to make a move. Let's talk strategy.",
                BehavioralSignal.REPEAT_VISITOR: "👋 Welcome back! I love that you keep checking in. Ready to take the next step in your property search?",
                BehavioralSignal.WEEKEND_BROWSING: "🌅 I notice you browse on weekends! Perfect time for property tours too. Want to see some this Saturday?",
                BehavioralSignal.EVENING_ACTIVITY: "🌙 I see you research in the evenings! I'm available for after-hours calls if that works better for your schedule.",
                # Community Signals
                BehavioralSignal.SOCIAL_MEDIA_ENGAGEMENT: "📱 Thanks for following on social! I share exclusive market insights there. Seen anything interesting lately?",
                BehavioralSignal.REFERRAL_ACTIVITY: "🤝 Thank you for the referral! I'm committed to providing the same excellent service to everyone you send my way.",
                BehavioralSignal.REVIEW_SUBMISSION: "⭐ Thank you for the review! It means the world to me. I'm here for any future real estate needs.",
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
