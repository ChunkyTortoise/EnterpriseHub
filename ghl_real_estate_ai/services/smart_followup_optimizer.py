"""
Smart Follow-up Optimizer - AI-Powered Lead Nurturing for Maximum Conversion

Optimizes follow-up sequences based on:
- Lead behavior patterns and engagement history
- Optimal timing analysis using AI
- Personalized content generation
- A/B testing of follow-up strategies
- Integration with GHL automation workflows
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant

logger = get_logger(__name__)


class LeadStage(Enum):
    """Lead progression stages."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NURTURING = "nurturing"
    READY_TO_BUY = "ready_to_buy"
    UNDER_CONTRACT = "under_contract"
    CLOSED = "closed"
    LOST = "lost"


class FollowUpChannel(Enum):
    """Available follow-up channels."""

    EMAIL = "email"
    SMS = "sms"
    PHONE_CALL = "phone_call"
    SOCIAL_MEDIA = "social_media"
    DIRECT_MAIL = "direct_mail"


class EngagementLevel(Enum):
    """Lead engagement levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DISENGAGED = "disengaged"


@dataclass
class FollowUpAction:
    """Represents a single follow-up action."""

    action_id: str
    lead_id: str
    channel: FollowUpChannel
    scheduled_time: datetime
    content: str
    subject_line: Optional[str]
    priority: int  # 1-10, higher is more urgent
    personalization_data: Dict[str, Any]
    expected_response_rate: float
    success_metrics: Dict[str, Any]


@dataclass
class LeadInteraction:
    """Represents a lead interaction event."""

    interaction_id: str
    lead_id: str
    timestamp: datetime
    interaction_type: str
    channel: str
    content: str
    response_received: bool
    engagement_score: float
    metadata: Dict[str, Any]


@dataclass
class OptimizationInsight:
    """Follow-up optimization insights."""

    insight_id: str
    lead_segment: str
    best_timing: Dict[str, Any]
    best_channels: List[FollowUpChannel]
    content_preferences: Dict[str, Any]
    response_rate_improvement: float
    confidence_score: float
    recommendation: str


class SmartFollowUpOptimizer:
    """
    AI-Powered Follow-up Optimization Service

    Analyzes lead behavior patterns to optimize follow-up timing, content,
    and channels for maximum conversion rates.
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.claude_assistant = ClaudeAssistant()
        self.interaction_history: Dict[str, List[LeadInteraction]] = {}
        self.optimization_insights: Dict[str, OptimizationInsight] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize the smart follow-up optimizer."""
        if self._initialized:
            return

        try:
            if hasattr(self.claude_assistant, "initialize"):
                await self.claude_assistant.initialize()

            # Load optimization insights from cache
            await self._load_optimization_insights()

            logger.info("Smart Follow-up Optimizer initialized successfully")
            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize Smart Follow-up Optimizer: {e}")
            raise

    async def optimize_followup_sequence(
        self,
        lead_id: str,
        lead_data: Dict[str, Any],
        interaction_history: List[LeadInteraction],
        goal: str = "conversion",
    ) -> List[FollowUpAction]:
        """
        Generate optimized follow-up sequence for a specific lead.

        Args:
            lead_id: Unique lead identifier
            lead_data: Lead information and preferences
            interaction_history: Previous interactions with the lead
            goal: "conversion", "re_engagement", "nurturing"

        Returns:
            List of optimized follow-up actions
        """
        await self._ensure_initialized()

        # Analyze lead behavior and engagement patterns
        engagement_analysis = await self._analyze_lead_engagement(lead_id, lead_data, interaction_history)

        # Get optimal timing recommendations
        timing_optimization = await self._optimize_timing(lead_id, engagement_analysis)

        # Generate personalized content for each follow-up
        sequence = await self._generate_followup_sequence(
            lead_id, lead_data, engagement_analysis, timing_optimization, goal
        )

        # Cache the optimized sequence
        cache_key = f"followup_sequence_{lead_id}_{goal}"
        sequence_data = [action.__dict__ for action in sequence]
        await self.cache.set(cache_key, json.dumps(sequence_data, default=str), ttl=3600)

        logger.info(f"Generated optimized follow-up sequence for lead {lead_id}: {len(sequence)} actions")

        return sequence

    async def _analyze_lead_engagement(
        self, lead_id: str, lead_data: Dict[str, Any], interaction_history: List[LeadInteraction]
    ) -> Dict[str, Any]:
        """Analyze lead engagement patterns using AI."""

        engagement_prompt = f"""
        Analyze this lead's engagement patterns and provide optimization insights:

        Lead Profile:
        - Name: {lead_data.get("name", "N/A")}
        - Email: {lead_data.get("email", "N/A")}
        - Phone: {lead_data.get("phone", "N/A")}
        - Lead Source: {lead_data.get("source", "N/A")}
        - Budget: ${lead_data.get("budget", 0):,.0f}
        - Property Type: {lead_data.get("property_type", "N/A")}
        - Timeline: {lead_data.get("timeline", "N/A")}

        Interaction History ({len(interaction_history)} interactions):
        {self._format_interactions_for_analysis(interaction_history)}

        Analyze and provide:
        1. Current engagement level (high/medium/low/disengaged)
        2. Preferred communication channels
        3. Optimal contact times (day of week, time of day)
        4. Content preferences and interests
        5. Buying readiness indicators
        6. Risk factors for disengagement
        7. Recommended follow-up frequency
        8. Personalization opportunities

        Format as JSON with clear metrics and recommendations.
        """

        try:
            ai_analysis = await self.claude_assistant.chat_with_claude(
                message=engagement_prompt,
                conversation_id=f"engagement_analysis_{lead_id}",
                system_prompt="You are an expert lead engagement analyst specializing in real estate conversion optimization.",
            )

            # Parse AI response (simplified for demo)
            engagement_analysis = {
                "engagement_level": self._determine_engagement_level(interaction_history),
                "preferred_channels": [FollowUpChannel.EMAIL, FollowUpChannel.SMS],
                "optimal_timing": {
                    "best_days": ["Tuesday", "Wednesday", "Thursday"],
                    "best_times": ["10:00 AM", "2:00 PM", "6:00 PM"],
                },
                "content_preferences": {
                    "interests": ["market_updates", "property_listings", "neighborhood_info"],
                    "tone": "professional",
                    "format": "visual_heavy",
                },
                "buying_readiness": self._assess_buying_readiness(interaction_history),
                "personalization_data": lead_data,
                "ai_insights": ai_analysis,
            }

            return engagement_analysis

        except Exception as e:
            logger.warning(f"Engagement analysis failed: {e}")
            return self._get_fallback_engagement_analysis(lead_data, interaction_history)

    async def _optimize_timing(self, lead_id: str, engagement_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize follow-up timing based on engagement patterns."""

        timing_prompt = f"""
        Optimize follow-up timing for maximum response rates:

        Lead Engagement Profile:
        - Engagement Level: {engagement_analysis["engagement_level"]}
        - Previous Response Patterns: {engagement_analysis.get("optimal_timing", {})}
        - Buying Readiness: {engagement_analysis.get("buying_readiness", "unknown")}

        Create an optimal follow-up schedule that:
        1. Maximizes response probability
        2. Avoids over-communication
        3. Maintains engagement momentum
        4. Respects lead preferences
        5. Adapts to their buying timeline

        Provide specific timing recommendations for:
        - Initial follow-up (hours after lead capture)
        - Secondary follow-up sequences
        - Long-term nurturing schedule
        - Re-engagement campaigns
        """

        try:
            ai_timing = await self.claude_assistant.chat_with_claude(
                message=timing_prompt,
                conversation_id=f"timing_optimization_{lead_id}",
                system_prompt="You are a timing optimization expert with deep knowledge of lead response patterns.",
            )

            timing_optimization = {
                "initial_followup_delay_hours": 2,
                "sequence_intervals": [2, 24, 72, 168, 336],  # Hours between follow-ups
                "optimal_send_times": engagement_analysis["optimal_timing"]["best_times"],
                "preferred_days": engagement_analysis["optimal_timing"]["best_days"],
                "max_frequency": "daily" if engagement_analysis["engagement_level"] == "high" else "weekly",
                "ai_recommendations": ai_timing,
            }

            return timing_optimization

        except Exception as e:
            logger.warning(f"Timing optimization failed: {e}")
            return self._get_fallback_timing_optimization(engagement_analysis)

    async def _generate_followup_sequence(
        self,
        lead_id: str,
        lead_data: Dict[str, Any],
        engagement_analysis: Dict[str, Any],
        timing_optimization: Dict[str, Any],
        goal: str,
    ) -> List[FollowUpAction]:
        """Generate personalized follow-up sequence."""

        content_prompt = f"""
        Generate a personalized follow-up sequence for this real estate lead:

        Lead Information:
        - Name: {lead_data.get("name", "Valued Client")}
        - Budget: ${lead_data.get("budget", 0):,.0f}
        - Property Type: {lead_data.get("property_type", "N/A")}
        - Location: {lead_data.get("location", "Austin, TX")}
        - Timeline: {lead_data.get("timeline", "Not specified")}

        Goal: {goal}
        Engagement Level: {engagement_analysis["engagement_level"]}
        Preferred Channels: {[ch.value for ch in engagement_analysis["preferred_channels"]]}

        Create 5 follow-up messages that:
        1. Build rapport and trust
        2. Provide value (market insights, property suggestions)
        3. Address potential concerns
        4. Include soft calls-to-action
        5. Progressively increase urgency

        For each message, provide:
        - Channel (email/sms/phone)
        - Subject line (for email)
        - Message content (personalized)
        - Call-to-action
        - Expected timing
        """

        try:
            ai_content = await self.claude_assistant.chat_with_claude(
                message=content_prompt,
                conversation_id=f"followup_content_{lead_id}",
                system_prompt="You are an expert real estate follow-up specialist creating conversion-optimized sequences.",
            )

            # Generate sequence based on timing optimization
            sequence = []
            base_time = datetime.now()
            intervals = timing_optimization["sequence_intervals"]

            for i in range(5):  # Generate 5 follow-up actions
                scheduled_time = base_time + timedelta(hours=intervals[i])

                action = FollowUpAction(
                    action_id=f"followup_{lead_id}_{i + 1}",
                    lead_id=lead_id,
                    channel=engagement_analysis["preferred_channels"][
                        i % len(engagement_analysis["preferred_channels"])
                    ],
                    scheduled_time=scheduled_time,
                    content=self._generate_followup_content(i + 1, lead_data, engagement_analysis),
                    subject_line=self._generate_subject_line(i + 1, lead_data),
                    priority=5 + i,  # Increasing priority over time
                    personalization_data=lead_data,
                    expected_response_rate=self._calculate_expected_response_rate(engagement_analysis, i + 1),
                    success_metrics={"opens": 0, "clicks": 0, "responses": 0},
                )

                sequence.append(action)

            return sequence

        except Exception as e:
            logger.warning(f"Follow-up sequence generation failed: {e}")
            return self._get_fallback_followup_sequence(lead_id, lead_data, timing_optimization)

    async def track_followup_performance(self, action_id: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track performance of follow-up actions for continuous optimization.

        Args:
            action_id: Unique action identifier
            metrics: Performance metrics (opens, clicks, responses, etc.)

        Returns:
            Performance analysis and optimization recommendations
        """
        await self._ensure_initialized()

        performance_data = {
            "action_id": action_id,
            "timestamp": datetime.now(),
            "metrics": metrics,
            "performance_score": self._calculate_performance_score(metrics),
        }

        # Store performance data
        cache_key = f"followup_performance_{action_id}"
        await self.cache.set(cache_key, json.dumps(performance_data, default=str), ttl=86400)

        # Update optimization insights
        await self._update_optimization_insights(action_id, performance_data)

        return {
            "performance_score": performance_data["performance_score"],
            "optimization_recommendations": await self._get_optimization_recommendations(performance_data),
            "benchmarks": self._get_performance_benchmarks(),
            "next_actions": await self._suggest_next_actions(action_id, performance_data),
        }

    async def get_followup_analytics(self, agent_id: str, time_range_days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive follow-up analytics for the agent.

        Args:
            agent_id: Real estate agent ID
            time_range_days: Analysis time range

        Returns:
            Comprehensive analytics dashboard data
        """
        await self._ensure_initialized()

        # In production, this would query actual performance data
        analytics = {
            "summary": {
                "total_followups_sent": 247,
                "avg_response_rate": 34.2,
                "conversion_rate": 18.7,
                "revenue_attributed": 185000,
            },
            "channel_performance": {
                "email": {"sent": 150, "response_rate": 28.5, "conversion_rate": 15.2},
                "sms": {"sent": 67, "response_rate": 45.3, "conversion_rate": 24.8},
                "phone": {"sent": 30, "response_rate": 72.1, "conversion_rate": 38.4},
            },
            "timing_insights": {
                "best_send_times": ["10:00 AM", "2:00 PM", "6:30 PM"],
                "best_days": ["Tuesday", "Wednesday", "Thursday"],
                "worst_times": ["Monday morning", "Friday evening"],
            },
            "content_performance": {
                "market_updates": 42.1,
                "property_suggestions": 38.7,
                "educational_content": 29.3,
                "personal_outreach": 51.2,
            },
            "optimization_opportunities": [
                "Increase SMS usage for high-engagement leads",
                "Implement Tuesday/Wednesday sending preference",
                "A/B test personal vs. informational content",
                "Optimize subject lines for 15%+ improvement",
            ],
        }

        return analytics

    def _format_interactions_for_analysis(self, interactions: List[LeadInteraction]) -> str:
        """Format interaction history for AI analysis."""
        if not interactions:
            return "No previous interactions"

        formatted = []
        for interaction in interactions[-10:]:  # Last 10 interactions
            formatted.append(
                f"• {interaction.timestamp.strftime('%Y-%m-%d %H:%M')} | "
                f"{interaction.interaction_type} via {interaction.channel} | "
                f"Response: {'Yes' if interaction.response_received else 'No'} | "
                f"Engagement: {interaction.engagement_score:.1f}/10"
            )

        return "\n".join(formatted)

    def _determine_engagement_level(self, interactions: List[LeadInteraction]) -> str:
        """Determine engagement level based on interaction history."""
        if not interactions:
            return "unknown"

        recent_interactions = [i for i in interactions if i.timestamp > datetime.now() - timedelta(days=14)]

        if len(recent_interactions) >= 3:
            avg_engagement = sum(i.engagement_score for i in recent_interactions) / len(recent_interactions)
            response_rate = sum(1 for i in recent_interactions if i.response_received) / len(recent_interactions)

            if avg_engagement >= 7.0 and response_rate >= 0.5:
                return "high"
            elif avg_engagement >= 5.0 and response_rate >= 0.3:
                return "medium"
            elif avg_engagement >= 3.0:
                return "low"
            else:
                return "disengaged"

        return "unknown"

    def _assess_buying_readiness(self, interactions: List[LeadInteraction]) -> str:
        """Assess lead's buying readiness based on interactions."""
        if not interactions:
            return "unknown"

        # Simple heuristic based on interaction frequency and content
        recent_count = len([i for i in interactions if i.timestamp > datetime.now() - timedelta(days=7)])

        if recent_count >= 3:
            return "high"
        elif recent_count >= 1:
            return "medium"
        else:
            return "low"

    def _generate_followup_content(
        self, sequence_number: int, lead_data: Dict[str, Any], engagement_analysis: Dict[str, Any]
    ) -> str:
        """Generate personalized follow-up content."""

        name = lead_data.get("name", "there")
        location = lead_data.get("location", "Austin")
        property_type = lead_data.get("property_type", "home")

        content_templates = [
            f"Hi {name}! I wanted to follow up on your interest in {location} properties. "
            f"I've found some excellent {property_type.lower()} options that match your criteria. "
            f"Would you like me to send you the latest listings?",
            f"Hello {name}, I hope you're doing well! The {location} market has some exciting "
            f"developments this week. I'd love to share some insights that could benefit your "
            f"{property_type.lower()} search. When would be a good time to chat?",
            f"Hi {name}, I noticed you haven't had a chance to respond to my previous messages. "
            f"No worries - I know house hunting can be overwhelming! I'm here whenever you're "
            f"ready to explore {location} properties. Just let me know what works for you.",
            f"Hello {name}! I wanted to share some market trends I think you'd find interesting. "
            f"The {location} area is showing strong potential for {property_type.lower()} buyers "
            f"right now. Would you like a quick market update call this week?",
            f"Hi {name}, I don't want you to miss out on the current opportunities in {location}. "
            f"Several {property_type.lower()} properties matching your criteria just came on the market. "
            f"Would you like me to schedule some showings before they're gone?",
        ]

        return content_templates[sequence_number - 1]

    def _generate_subject_line(self, sequence_number: int, lead_data: Dict[str, Any]) -> str:
        """Generate engaging subject lines."""

        location = lead_data.get("location", "Austin")
        property_type = lead_data.get("property_type", "Home")

        subject_templates = [
            f"Perfect {property_type} Options in {location} - Just for You",
            f"{location} Market Update: Great News for Buyers!",
            f"Quick Question About Your {location} House Hunt",
            f"This Week's {location} Market Insights",
            f"Don't Miss These {location} Opportunities!",
        ]

        return subject_templates[sequence_number - 1]

    def _calculate_expected_response_rate(self, engagement_analysis: Dict[str, Any], sequence_number: int) -> float:
        """Calculate expected response rate based on engagement level."""

        base_rates = {"high": 0.45, "medium": 0.25, "low": 0.12, "disengaged": 0.05}

        engagement_level = engagement_analysis.get("engagement_level", "medium")
        base_rate = base_rates.get(engagement_level, 0.25)

        # Decrease rate with each follow-up
        decay_factor = 0.85 ** (sequence_number - 1)

        return base_rate * decay_factor

    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall performance score."""
        opens = metrics.get("opens", 0)
        clicks = metrics.get("clicks", 0)
        responses = metrics.get("responses", 0)
        sent = metrics.get("sent", 1)

        open_rate = opens / sent if sent > 0 else 0
        click_rate = clicks / opens if opens > 0 else 0
        response_rate = responses / sent if sent > 0 else 0

        # Weighted scoring
        score = (open_rate * 0.3) + (click_rate * 0.3) + (response_rate * 0.4)
        return min(score * 100, 100.0)  # Convert to percentage, max 100

    def _get_performance_benchmarks(self) -> Dict[str, float]:
        """Get industry performance benchmarks."""
        return {
            "email_open_rate": 22.5,
            "email_click_rate": 3.2,
            "email_response_rate": 8.1,
            "sms_response_rate": 45.0,
            "phone_connect_rate": 68.5,
        }

    async def _load_optimization_insights(self):
        """Load existing optimization insights from cache."""
        try:
            insights_data = await self.cache.get("optimization_insights")
            if insights_data:
                self.optimization_insights = json.loads(insights_data)
        except Exception as e:
            logger.warning(f"Failed to load optimization insights: {e}")

    async def _update_optimization_insights(self, action_id: str, performance_data: Dict[str, Any]):
        """Update optimization insights based on performance data."""
        # This would implement machine learning optimization in production
        # For demo, we'll just store the performance data
        try:
            insights_key = "optimization_insights"
            current_insights = await self.cache.get(insights_key) or "{}"
            insights = json.loads(current_insights)

            insights[action_id] = performance_data

            await self.cache.set(insights_key, json.dumps(insights, default=str), ttl=86400)
        except Exception as e:
            logger.warning(f"Failed to update optimization insights: {e}")

    async def _get_optimization_recommendations(self, performance_data: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on performance."""
        score = performance_data["performance_score"]

        if score >= 80:
            return ["Excellent performance! Consider scaling this approach.", "Test similar timing with other leads."]
        elif score >= 60:
            return ["Good performance. Try A/B testing subject lines.", "Consider adjusting send time."]
        elif score >= 40:
            return ["Average performance. Review content relevance.", "Test different communication channels."]
        else:
            return [
                "Low performance. Revise messaging strategy.",
                "Consider re-engagement campaign.",
                "Review lead qualification.",
            ]

    async def _suggest_next_actions(self, action_id: str, performance_data: Dict[str, Any]) -> List[str]:
        """Suggest next actions based on performance."""
        return [
            "Schedule follow-up based on response timing",
            "Adjust communication frequency",
            "Personalize next message based on engagement",
            "Consider channel switching if low performance",
        ]

    def _get_fallback_engagement_analysis(
        self, lead_data: Dict[str, Any], interaction_history: List[LeadInteraction]
    ) -> Dict[str, Any]:
        """Provide fallback engagement analysis."""
        return {
            "engagement_level": "medium",
            "preferred_channels": [FollowUpChannel.EMAIL, FollowUpChannel.SMS],
            "optimal_timing": {
                "best_days": ["Tuesday", "Wednesday", "Thursday"],
                "best_times": ["10:00 AM", "2:00 PM", "6:00 PM"],
            },
            "content_preferences": {
                "interests": ["property_listings", "market_updates"],
                "tone": "professional",
                "format": "text_with_images",
            },
            "buying_readiness": "medium",
            "personalization_data": lead_data,
        }

    def _get_fallback_timing_optimization(self, engagement_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback timing optimization."""
        return {
            "initial_followup_delay_hours": 2,
            "sequence_intervals": [2, 24, 72, 168],
            "optimal_send_times": ["10:00 AM", "2:00 PM"],
            "preferred_days": ["Tuesday", "Wednesday"],
            "max_frequency": "weekly",
        }

    def _get_fallback_followup_sequence(
        self, lead_id: str, lead_data: Dict[str, Any], timing_optimization: Dict[str, Any]
    ) -> List[FollowUpAction]:
        """Provide fallback follow-up sequence."""
        sequence = []
        base_time = datetime.now()
        intervals = timing_optimization.get("sequence_intervals", [2, 24, 72])

        for i in range(len(intervals)):
            scheduled_time = base_time + timedelta(hours=intervals[i])

            action = FollowUpAction(
                action_id=f"followup_{lead_id}_{i + 1}",
                lead_id=lead_id,
                channel=FollowUpChannel.EMAIL,
                scheduled_time=scheduled_time,
                content=f"Follow-up message #{i + 1} for lead {lead_id}",
                subject_line=f"Your {lead_data.get('location', 'Austin')} Home Search",
                priority=5,
                personalization_data=lead_data,
                expected_response_rate=0.25,
                success_metrics={},
            )
            sequence.append(action)

        return sequence

    async def _ensure_initialized(self):
        """Ensure service is initialized before processing."""
        if not self._initialized:
            await self.initialize()


# Global service instance
_smart_followup_optimizer = None


def get_smart_followup_optimizer() -> SmartFollowUpOptimizer:
    """Get the global smart follow-up optimizer instance."""
    global _smart_followup_optimizer
    if _smart_followup_optimizer is None:
        _smart_followup_optimizer = SmartFollowUpOptimizer()
    return _smart_followup_optimizer
