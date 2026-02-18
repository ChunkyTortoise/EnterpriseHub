"""
Claude Proactive Suggestions System

Analyzes user behavior, lead data, and platform activity to provide intelligent,
timely suggestions that help real estate professionals stay ahead of opportunities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SuggestionType(str, Enum):
    """Types of proactive suggestions."""
    LEAD_OPPORTUNITY = "lead_opportunity"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    MARKET_INSIGHT = "market_insight"
    PROCESS_OPTIMIZATION = "process_optimization"
    STRATEGIC_RECOMMENDATION = "strategic_recommendation"


class SuggestionPriority(str, Enum):
    """Priority levels for suggestions."""
    CRITICAL = "critical"    # Immediate action needed
    HIGH = "high"           # Action needed today
    MEDIUM = "medium"       # Action needed this week
    LOW = "low"             # Informational/nice-to-have


@dataclass
class ProactiveSuggestion:
    """Individual proactive suggestion from Claude."""
    id: str
    type: SuggestionType
    priority: SuggestionPriority
    title: str
    message: str
    action_items: List[str]
    context_data: Dict[str, Any]
    expires_at: datetime
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class ClaudeProactiveSuggestions:
    """Proactive suggestions engine powered by Claude intelligence."""

    def __init__(self):
        """Initialize proactive suggestions system."""
        self.suggestions_cache = []
        self.user_preferences = {}
        self.last_analysis = None

    async def generate_suggestions(
        self,
        user_context: Dict[str, Any],
        lead_data: Optional[List[Dict[str, Any]]] = None,
        activity_data: Optional[Dict[str, Any]] = None
    ) -> List[ProactiveSuggestion]:
        """
        Generate proactive suggestions based on current context and data.

        Args:
            user_context: Current user context and preferences
            lead_data: Recent lead activity and status
            activity_data: Platform usage and performance data

        Returns:
            List of prioritized proactive suggestions
        """
        suggestions = []

        # Analyze different data sources for opportunities
        suggestions.extend(await self._analyze_lead_opportunities(lead_data or []))
        suggestions.extend(await self._analyze_follow_up_opportunities(lead_data or []))
        suggestions.extend(await self._analyze_market_opportunities(user_context))
        suggestions.extend(await self._analyze_process_optimizations(activity_data or {}))

        # Sort by priority and relevance
        suggestions = self._prioritize_suggestions(suggestions)

        # Store for caching
        self.suggestions_cache = suggestions
        self.last_analysis = datetime.now()

        return suggestions[:8]  # Return top 8 suggestions

    async def _analyze_lead_opportunities(self, lead_data: List[Dict[str, Any]]) -> List[ProactiveSuggestion]:
        """Analyze leads for immediate opportunities."""
        suggestions = []

        for lead in lead_data:
            # High-engagement leads needing immediate attention
            if self._is_hot_lead(lead):
                suggestions.append(ProactiveSuggestion(
                    id=f"hot_lead_{lead.get('id', 'unknown')}",
                    type=SuggestionType.LEAD_OPPORTUNITY,
                    priority=SuggestionPriority.CRITICAL,
                    title=f"🔥 {lead.get('name', 'Lead')} is showing high interest!",
                    message=f"{lead.get('name', 'This lead')} has viewed {lead.get('properties_viewed', 3)} properties and their timeline is {lead.get('timeline', 'immediate')}. Perfect time for direct outreach!",
                    action_items=[
                        "Call within next 2 hours while interest is peak",
                        "Send personalized property recommendations",
                        "Schedule property viewing this week"
                    ],
                    context_data=lead,
                    expires_at=datetime.now() + timedelta(hours=6)
                ))

            # Budget-qualified leads with timeline urgency
            elif self._is_qualified_urgent(lead):
                suggestions.append(ProactiveSuggestion(
                    id=f"urgent_qualified_{lead.get('id', 'unknown')}",
                    type=SuggestionType.LEAD_OPPORTUNITY,
                    priority=SuggestionPriority.HIGH,
                    title=f"⏰ {lead.get('name', 'Lead')} has urgent timeline",
                    message=f"Qualified lead with ${lead.get('budget', 'unknown'):,} budget needs to move by {lead.get('timeline', 'soon')}. High conversion potential.",
                    action_items=[
                        "Fast-track property search and viewing",
                        "Connect with preferred lender immediately",
                        "Provide comprehensive area analysis"
                    ],
                    context_data=lead,
                    expires_at=datetime.now() + timedelta(days=2)
                ))

        return suggestions

    async def _analyze_follow_up_opportunities(self, lead_data: List[Dict[str, Any]]) -> List[ProactiveSuggestion]:
        """Identify leads needing follow-up attention."""
        suggestions = []

        for lead in lead_data:
            last_contact = lead.get('last_contact_date')
            if last_contact:
                days_since_contact = (datetime.now() - datetime.fromisoformat(last_contact)).days

                # Leads going cold (no contact in 3+ days)
                if days_since_contact >= 3 and lead.get('interest_level', 'medium') in ['high', 'medium']:
                    suggestions.append(ProactiveSuggestion(
                        id=f"followup_needed_{lead.get('id', 'unknown')}",
                        type=SuggestionType.FOLLOW_UP_REMINDER,
                        priority=SuggestionPriority.HIGH,
                        title=f"📞 {lead.get('name', 'Lead')} needs follow-up",
                        message=f"It's been {days_since_contact} days since last contact. {lead.get('interest_level', 'Medium')} interest lead may be cooling off.",
                        action_items=[
                            "Send value-add market update",
                            "Share new listings matching criteria",
                            "Schedule check-in call"
                        ],
                        context_data=lead,
                        expires_at=datetime.now() + timedelta(days=1)
                    ))

        return suggestions

    async def _analyze_market_opportunities(self, context: Dict[str, Any]) -> List[ProactiveSuggestion]:
        """Identify market-based opportunities."""
        suggestions = []

        # Seasonal market insights
        current_month = datetime.now().month

        if current_month in [3, 4, 5]:  # Spring market
            suggestions.append(ProactiveSuggestion(
                id="spring_market_opportunity",
                type=SuggestionType.MARKET_INSIGHT,
                priority=SuggestionPriority.MEDIUM,
                title="🌸 Spring market heating up!",
                message="Spring buyer surge is starting. This is typically the best time for listings and buyer activity increases 40%.",
                action_items=[
                    "Reach out to potential sellers about spring listings",
                    "Accelerate buyer lead qualification and showings",
                    "Prepare market analysis reports for Q2 trends"
                ],
                context_data={"season": "spring", "market_activity": "increasing"},
                expires_at=datetime.now() + timedelta(days=7)
            ))

        # Market conditions suggestions (mock data - would integrate with real market APIs)
        suggestions.append(ProactiveSuggestion(
            id="interest_rate_opportunity",
            type=SuggestionType.STRATEGIC_RECOMMENDATION,
            priority=SuggestionPriority.MEDIUM,
            title="📈 Interest rates favorable for buyers",
            message="Current rates at 6.8% create opportunity window. Buyers with pre-approval have competitive advantage.",
            action_items=[
                "Emphasize pre-approval importance to prospects",
                "Create urgency messaging around rate locks",
                "Connect unqualified leads with preferred lenders"
            ],
            context_data={"rates": "6.8%", "trend": "stable"},
            expires_at=datetime.now() + timedelta(days=14)
        ))

        return suggestions

    async def _analyze_process_optimizations(self, activity_data: Dict[str, Any]) -> List[ProactiveSuggestion]:
        """Identify process improvement opportunities."""
        suggestions = []

        # Response time optimization
        avg_response_time = activity_data.get('avg_response_time_hours', 12)
        if avg_response_time > 4:
            suggestions.append(ProactiveSuggestion(
                id="response_time_optimization",
                type=SuggestionType.PROCESS_OPTIMIZATION,
                priority=SuggestionPriority.MEDIUM,
                title="⚡ Improve response times for better conversion",
                message=f"Current average response time is {avg_response_time} hours. Industry best practice is under 1 hour for hot leads.",
                action_items=[
                    "Set up mobile notifications for new leads",
                    "Create quick response templates",
                    "Consider auto-responder for immediate acknowledgment"
                ],
                context_data={"current_time": avg_response_time, "target_time": 1},
                expires_at=datetime.now() + timedelta(days=30)
            ))

        # Qualification rate optimization
        qualification_rate = activity_data.get('qualification_rate', 0.65)
        if qualification_rate < 0.75:
            suggestions.append(ProactiveSuggestion(
                id="qualification_optimization",
                type=SuggestionType.PROCESS_OPTIMIZATION,
                priority=SuggestionPriority.LOW,
                title="🎯 Boost lead qualification effectiveness",
                message=f"Current qualification rate is {qualification_rate:.0%}. Target is 75%+ for optimal pipeline health.",
                action_items=[
                    "Refine qualification questions script",
                    "Implement BANT qualification framework",
                    "Review and improve lead source quality"
                ],
                context_data={"current_rate": qualification_rate, "target_rate": 0.75},
                expires_at=datetime.now() + timedelta(days=21)
            ))

        return suggestions

    def _is_hot_lead(self, lead: Dict[str, Any]) -> bool:
        """Determine if lead is showing hot engagement signals."""
        properties_viewed = lead.get('properties_viewed', 0)
        timeline = lead.get('timeline', '').lower()
        last_activity_hours = lead.get('last_activity_hours', 999)

        return (
            properties_viewed >= 3 or
            timeline in ['immediate', 'asap', '1 month', 'urgent'] or
            last_activity_hours <= 24
        )

    def _is_qualified_urgent(self, lead: Dict[str, Any]) -> bool:
        """Determine if lead is qualified with urgent timeline."""
        budget = lead.get('budget', 0)
        timeline = lead.get('timeline', '').lower()
        financing = lead.get('financing_status', '').lower()

        return (
            budget > 200000 and
            timeline in ['1 month', '2 months', '3 months', 'immediate'] and
            financing in ['pre-approved', 'pre-qualified', 'cash']
        )

    def _prioritize_suggestions(self, suggestions: List[ProactiveSuggestion]) -> List[ProactiveSuggestion]:
        """Sort suggestions by priority and relevance."""
        priority_order = {
            SuggestionPriority.CRITICAL: 1,
            SuggestionPriority.HIGH: 2,
            SuggestionPriority.MEDIUM: 3,
            SuggestionPriority.LOW: 4
        }

        return sorted(
            suggestions,
            key=lambda s: (
                priority_order[s.priority],
                -len(s.action_items),  # More actionable items = higher priority
                s.created_at
            )
        )

    def get_cached_suggestions(self) -> List[ProactiveSuggestion]:
        """Get cached suggestions without regenerating."""
        # Filter out expired suggestions
        now = datetime.now()
        valid_suggestions = [s for s in self.suggestions_cache if s.expires_at > now]
        return valid_suggestions

    async def dismiss_suggestion(self, suggestion_id: str) -> bool:
        """Dismiss a specific suggestion."""
        self.suggestions_cache = [
            s for s in self.suggestions_cache
            if s.id != suggestion_id
        ]
        return True

    def get_suggestion_metrics(self) -> Dict[str, Any]:
        """Get metrics about suggestion generation and effectiveness."""
        active_suggestions = self.get_cached_suggestions()

        return {
            "total_active": len(active_suggestions),
            "by_priority": {
                priority.value: len([s for s in active_suggestions if s.priority == priority])
                for priority in SuggestionPriority
            },
            "by_type": {
                stype.value: len([s for s in active_suggestions if s.type == stype])
                for stype in SuggestionType
            },
            "last_generated": self.last_analysis.isoformat() if self.last_analysis else None
        }


# Global instance for easy access
claude_proactive_suggestions = ClaudeProactiveSuggestions()


# Usage example:
"""
# Generate suggestions based on current context
suggestions = await claude_proactive_suggestions.generate_suggestions(
    user_context={"location": "Austin", "focus": "buyers"},
    lead_data=[
        {
            "id": "lead_001",
            "name": "Sarah Johnson",
            "budget": 400000,
            "timeline": "immediate",
            "properties_viewed": 5,
            "last_contact_date": "2026-01-10",
            "interest_level": "high"
        }
    ]
)

# Display in Streamlit
for suggestion in suggestions:
    st.success(f"{suggestion.title}")
    st.write(suggestion.message)
    for action in suggestion.action_items:
        st.write(f"• {action}")
"""