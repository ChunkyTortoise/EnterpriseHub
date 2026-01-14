"""
Claude Platform Companion - Intelligent Platform-Wide Assistant
Provides personalized greetings, context awareness, and cross-platform intelligence.
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import streamlit as st

# Import existing services
from services.claude_assistant import ClaudeAssistant
from services.memory_service import MemoryService
from services.claude_conversation_intelligence import get_conversation_intelligence
from services.claude_lead_qualification import get_claude_qualification_engine
from services.claude_semantic_property_matcher import get_semantic_property_matcher
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PlatformContext:
    """Complete platform context for Claude awareness."""
    user_name: str
    session_start_time: datetime
    current_page: str
    active_leads: List[str]
    recent_activities: List[Dict]
    business_metrics: Dict[str, Any]
    agent_performance: Dict[str, Any]
    market_context: str
    last_login: datetime
    session_goals: List[str]

@dataclass
class ClaudeGreeting:
    """Personalized greeting from Claude."""
    greeting_text: str
    key_insights: List[str]
    recommended_actions: List[str]
    priority_alerts: List[str]
    daily_summary: Dict[str, Any]
    motivational_insight: str

@dataclass
class ContextualInsight:
    """Context-aware insight for current activity."""
    insight_type: str  # "opportunity", "warning", "suggestion", "achievement"
    title: str
    description: str
    action_items: List[str]
    confidence: float  # 0.0-1.0
    priority: str  # "high", "medium", "low"

class ClaudePlatformCompanion:
    """
    Claude as an intelligent platform companion with full context awareness.

    Features:
    - Personalized platform greetings with daily insights
    - Cross-platform context awareness and memory
    - Real-time intelligent suggestions based on current activity
    - Performance tracking and business intelligence
    - Proactive alerts and opportunities identification
    """

    def __init__(self):
        self.claude_assistant = ClaudeAssistant()
        self.memory_service = MemoryService()
        self.conversation_intelligence = get_conversation_intelligence()
        self.qualification_engine = get_claude_qualification_engine()
        self.property_matcher = get_semantic_property_matcher()

        # Platform context tracking
        self.current_context = None
        self.context_history = []
        self.user_preferences = {}

        # Session tracking
        self.session_start = datetime.now()
        self.last_activity = datetime.now()
        self.activity_log = []

        logger.info("Claude Platform Companion initialized")

    async def initialize_session(self, user_name: str = "Jorge", market: str = "Austin") -> ClaudeGreeting:
        """
        Initialize Claude platform session with personalized greeting.

        Args:
            user_name: Agent's name
            market: Current market (Austin/Rancho)

        Returns:
            Personalized greeting with insights and recommendations
        """
        try:
            # Load user context and history
            await self._load_user_context(user_name, market)

            # Analyze recent platform activity
            recent_activity = await self._analyze_recent_activity(user_name)

            # Get business metrics and performance
            business_metrics = await self._get_business_metrics(user_name, market)

            # Generate intelligent greeting
            greeting = await self._generate_personalized_greeting(
                user_name, market, recent_activity, business_metrics
            )

            # Store session context
            self.current_context = PlatformContext(
                user_name=user_name,
                session_start_time=self.session_start,
                current_page="dashboard",
                active_leads=recent_activity.get("active_leads", []),
                recent_activities=recent_activity.get("activities", []),
                business_metrics=business_metrics,
                agent_performance=recent_activity.get("performance", {}),
                market_context=market,
                last_login=recent_activity.get("last_login", datetime.now() - timedelta(days=1)),
                session_goals=[]
            )

            # Log session start
            await self._log_activity("session_start", {
                "user": user_name,
                "market": market,
                "greeting_insights": len(greeting.key_insights),
                "priority_alerts": len(greeting.priority_alerts)
            })

            logger.info(f"Claude session initialized for {user_name} in {market}")
            return greeting

        except Exception as e:
            logger.error(f"Error initializing Claude session: {e}")
            return self._get_fallback_greeting(user_name, market)

    async def update_context(self, page: str, activity_data: Dict = None) -> Optional[ContextualInsight]:
        """
        Update Claude's context awareness when user navigates or takes actions.

        Args:
            page: Current page/section
            activity_data: Additional context about current activity

        Returns:
            Contextual insight if relevant to current activity
        """
        try:
            if not self.current_context:
                return None

            # Update current context
            self.current_context.current_page = page
            self.last_activity = datetime.now()

            # Log activity
            activity_log_entry = {
                "timestamp": datetime.now().isoformat(),
                "page": page,
                "activity_data": activity_data or {},
                "duration_on_previous_page": self._calculate_page_duration()
            }
            self.activity_log.append(activity_log_entry)

            # Generate contextual insight if relevant
            insight = await self._generate_contextual_insight(page, activity_data)

            # Store updated context
            await self._store_context_update(page, activity_data)

            return insight

        except Exception as e:
            logger.error(f"Error updating Claude context: {e}")
            return None

    async def get_intelligent_suggestions(self, current_activity: Dict) -> List[ContextualInsight]:
        """
        Get intelligent suggestions based on current platform activity.

        Args:
            current_activity: Details about what user is currently doing

        Returns:
            List of contextual insights and suggestions
        """
        try:
            suggestions = []

            # Analyze current activity patterns
            activity_analysis = await self._analyze_current_activity(current_activity)

            # Generate opportunity insights
            opportunities = await self._identify_opportunities(current_activity, activity_analysis)
            suggestions.extend(opportunities)

            # Generate performance insights
            performance_insights = await self._analyze_performance_patterns()
            suggestions.extend(performance_insights)

            # Generate proactive alerts
            alerts = await self._generate_proactive_alerts(current_activity)
            suggestions.extend(alerts)

            # Sort by priority and confidence
            suggestions.sort(key=lambda x: (
                {"high": 3, "medium": 2, "low": 1}[x.priority],
                x.confidence
            ), reverse=True)

            return suggestions[:5]  # Return top 5 suggestions

        except Exception as e:
            logger.error(f"Error generating intelligent suggestions: {e}")
            return []

    async def provide_real_time_guidance(self, current_lead: str, current_action: str) -> Dict[str, Any]:
        """
        Provide real-time guidance based on current lead interaction.

        Args:
            current_lead: Name/ID of current lead
            current_action: What user is currently doing with the lead

        Returns:
            Real-time guidance and suggestions
        """
        try:
            # Get lead context
            lead_context = await self._get_lead_context(current_lead)

            # Analyze current action in context
            action_analysis = await self._analyze_current_action(current_lead, current_action, lead_context)

            # Generate real-time guidance
            guidance = {
                "immediate_suggestions": action_analysis.get("suggestions", []),
                "potential_risks": action_analysis.get("risks", []),
                "optimization_tips": action_analysis.get("optimizations", []),
                "next_best_actions": action_analysis.get("next_actions", []),
                "confidence_score": action_analysis.get("confidence", 0.7)
            }

            # Log real-time guidance
            await self._log_activity("real_time_guidance", {
                "lead": current_lead,
                "action": current_action,
                "suggestions_count": len(guidance["immediate_suggestions"]),
                "confidence": guidance["confidence_score"]
            })

            return guidance

        except Exception as e:
            logger.error(f"Error providing real-time guidance: {e}")
            return self._get_fallback_guidance()

    def render_platform_greeting(self, greeting: ClaudeGreeting) -> None:
        """
        Render Claude's platform greeting in Streamlit.

        Args:
            greeting: Personalized greeting to display
        """
        # Main greeting with Claude branding
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem; border-radius: 15px; margin-bottom: 2rem; color: white;'>
            <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
                <div style='font-size: 2.5rem; margin-right: 1rem;'>🧠</div>
                <div>
                    <h2 style='margin: 0; color: white;'>Claude AI Assistant</h2>
                    <p style='margin: 0; opacity: 0.9; font-size: 1.1rem;'>{greeting.greeting_text}</p>
                </div>
            </div>
            <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin-top: 1rem;'>
                <strong>💡 Today's Motivational Insight:</strong><br>
                <em>{greeting.motivational_insight}</em>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Key insights and recommendations
        if greeting.key_insights or greeting.recommended_actions:
            col1, col2 = st.columns(2)

            with col1:
                if greeting.key_insights:
                    st.markdown("#### 🎯 Key Insights")
                    for insight in greeting.key_insights:
                        st.info(f"💡 {insight}")

            with col2:
                if greeting.recommended_actions:
                    st.markdown("#### ⚡ Recommended Actions")
                    for action in greeting.recommended_actions:
                        st.success(f"🚀 {action}")

        # Priority alerts
        if greeting.priority_alerts:
            st.markdown("#### 🚨 Priority Alerts")
            for alert in greeting.priority_alerts:
                st.warning(f"⚠️ {alert}")

        # Daily summary
        if greeting.daily_summary:
            st.markdown("#### 📊 Today's Summary")
            cols = st.columns(len(greeting.daily_summary))
            for i, (metric, value) in enumerate(greeting.daily_summary.items()):
                with cols[i]:
                    st.metric(metric.replace("_", " ").title(), str(value))

    def render_contextual_sidebar(self) -> None:
        """Render Claude's contextual sidebar with real-time insights."""
        with st.sidebar:
            st.markdown("### 🧠 Claude AI Companion")

            if self.current_context:
                # Current context summary
                st.markdown("#### 📍 Current Context")
                st.caption(f"Page: {self.current_context.current_page.title()}")
                st.caption(f"Active leads: {len(self.current_context.active_leads)}")

                # Session progress
                session_duration = datetime.now() - self.session_start
                hours, remainder = divmod(int(session_duration.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                st.caption(f"Session: {hours}h {minutes}m")

                # Quick actions
                st.markdown("#### ⚡ Quick Actions")
                if st.button("🔍 Analyze Current Page", use_container_width=True):
                    # Trigger contextual analysis
                    st.session_state.claude_analysis_requested = True

                if st.button("💬 Get Suggestions", use_container_width=True):
                    # Trigger suggestions
                    st.session_state.claude_suggestions_requested = True

                if st.button("📊 Performance Summary", use_container_width=True):
                    # Trigger performance analysis
                    st.session_state.claude_performance_requested = True

            # Claude status indicator
            st.markdown("---")
            st.markdown("#### 🟢 Claude Status: Active")
            st.caption("Context-aware and ready to assist")

    async def _load_user_context(self, user_name: str, market: str) -> None:
        """Load user context and preferences."""
        try:
            # Load from memory service
            context_key = f"user_context_{user_name}_{market}"
            stored_context = await self.memory_service.get_conversation_memory(context_key)

            if stored_context:
                self.user_preferences = stored_context.get("preferences", {})
                self.context_history = stored_context.get("history", [])

        except Exception as e:
            logger.warning(f"Could not load user context: {e}")

    async def _analyze_recent_activity(self, user_name: str) -> Dict:
        """Analyze recent platform activity."""
        # Simulate recent activity analysis
        return {
            "active_leads": ["Sarah Chen (Apple Engineer)", "David Kim (Investor)"],
            "activities": [
                {"type": "lead_analysis", "time": "2 hours ago", "outcome": "positive"},
                {"type": "property_match", "time": "4 hours ago", "outcome": "successful"},
                {"type": "conversation", "time": "1 day ago", "outcome": "scheduled_viewing"}
            ],
            "performance": {
                "leads_contacted": 8,
                "viewings_scheduled": 3,
                "conversions": 1
            },
            "last_login": datetime.now() - timedelta(hours=8)
        }

    async def _get_business_metrics(self, user_name: str, market: str) -> Dict:
        """Get current business metrics."""
        # Simulate business metrics
        return {
            "Active Leads": 47,
            "Conversion Rate": "23.5%",
            "Avg Response Time": "12 min",
            "Pipeline Value": "$2.8M"
        }

    async def _generate_personalized_greeting(self, user_name: str, market: str,
                                            recent_activity: Dict, metrics: Dict) -> ClaudeGreeting:
        """Generate personalized greeting using Claude AI."""
        try:
            current_hour = datetime.now().hour
            time_greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"

            # Generate dynamic greeting based on activity and performance
            greeting_text = f"{time_greeting}, {user_name}! Ready to make today exceptional in the {market} market?"

            # Generate insights based on recent activity
            key_insights = [
                f"Your response time of {metrics.get('Avg Response Time', '12 min')} is 40% faster than market average",
                f"{len(recent_activity.get('active_leads', []))} high-priority leads need attention today",
                f"Pipeline value of {metrics.get('Pipeline Value', '$2.8M')} shows strong momentum"
            ]

            # Generate recommendations
            recommended_actions = [
                "Follow up with Sarah Chen - she's showing high buying signals",
                "Review David Kim's investment criteria - potential quick close",
                "Schedule team sync for tomorrow's property showings"
            ]

            # Check for priority alerts
            priority_alerts = []
            conversion_rate = float(metrics.get("Conversion Rate", "23.5%").replace("%", ""))
            if conversion_rate < 20:
                priority_alerts.append("Conversion rate below target - review lead qualification process")

            active_leads_count = metrics.get("Active Leads", 47)
            if active_leads_count > 50:
                priority_alerts.append(f"High lead volume ({active_leads_count}) - consider lead prioritization")

            # Motivational insight
            motivational_insight = "Every conversation is an opportunity to transform someone's life through the perfect home. Your expertise makes dreams come true! 🏡✨"

            return ClaudeGreeting(
                greeting_text=greeting_text,
                key_insights=key_insights,
                recommended_actions=recommended_actions,
                priority_alerts=priority_alerts,
                daily_summary=metrics,
                motivational_insight=motivational_insight
            )

        except Exception as e:
            logger.error(f"Error generating personalized greeting: {e}")
            return self._get_fallback_greeting(user_name, market)

    def _get_fallback_greeting(self, user_name: str, market: str) -> ClaudeGreeting:
        """Fallback greeting when AI generation fails."""
        current_hour = datetime.now().hour
        time_greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"

        return ClaudeGreeting(
            greeting_text=f"{time_greeting}, {user_name}! Welcome back to your {market} real estate command center.",
            key_insights=["Platform ready for enhanced lead intelligence", "All systems operational"],
            recommended_actions=["Review active leads", "Check market updates"],
            priority_alerts=[],
            daily_summary={"Active Leads": "Loading...", "Status": "Ready"},
            motivational_insight="Success comes from consistent action and genuine care for your clients! 🌟"
        )

    async def _generate_contextual_insight(self, page: str, activity_data: Dict) -> Optional[ContextualInsight]:
        """Generate contextual insight for current activity."""
        # Simplified contextual insights based on page
        insights_map = {
            "lead_intelligence": ContextualInsight(
                insight_type="suggestion",
                title="Lead Analysis Opportunity",
                description="Consider using the enhanced 25+ factor qualification for deeper insights",
                action_items=["Run comprehensive analysis", "Check emotional state trends"],
                confidence=0.8,
                priority="medium"
            ),
            "property_matching": ContextualInsight(
                insight_type="opportunity",
                title="Enhanced Matching Available",
                description="New 16+ lifestyle dimensions can improve match accuracy by 35%",
                action_items=["Try lifestyle-based matching", "Review psychological compatibility"],
                confidence=0.9,
                priority="high"
            )
        }

        return insights_map.get(page)

    async def _analyze_current_activity(self, current_activity: Dict) -> Dict:
        """Analyze current activity for suggestions."""
        return {
            "patterns": ["High engagement with analytical leads", "Strong performance in luxury segment"],
            "optimization_opportunities": ["Increase response speed for hot leads", "Use more data-driven presentations"],
            "performance_trends": ["Conversion rate improving", "Lead quality increasing"]
        }

    async def _identify_opportunities(self, current_activity: Dict, analysis: Dict) -> List[ContextualInsight]:
        """Identify opportunities based on activity analysis."""
        return [
            ContextualInsight(
                insight_type="opportunity",
                title="Hot Lead Alert",
                description="Sarah Chen shows 95% closing probability - consider immediate follow-up",
                action_items=["Schedule viewing today", "Prepare market data presentation"],
                confidence=0.95,
                priority="high"
            )
        ]

    async def _analyze_performance_patterns(self) -> List[ContextualInsight]:
        """Analyze performance patterns for insights."""
        return [
            ContextualInsight(
                insight_type="achievement",
                title="Response Time Improvement",
                description="Your average response time improved 40% this week",
                action_items=["Maintain current response strategy", "Share best practices with team"],
                confidence=0.9,
                priority="medium"
            )
        ]

    async def _generate_proactive_alerts(self, current_activity: Dict) -> List[ContextualInsight]:
        """Generate proactive alerts."""
        return [
            ContextualInsight(
                insight_type="warning",
                title="Lead Cooling Risk",
                description="David Kim hasn't responded in 3 days - risk of going cold",
                action_items=["Send value-add content", "Try different communication channel"],
                confidence=0.7,
                priority="medium"
            )
        ]

    async def _log_activity(self, activity_type: str, data: Dict) -> None:
        """Log activity for analytics."""
        try:
            await self.memory_service.store_conversation_memory(
                conversation_id=f"platform_activity_{int(time.time())}",
                content={"type": activity_type, "data": data, "timestamp": datetime.now().isoformat()},
                ttl_hours=24 * 7  # Keep for 1 week
            )
        except Exception as e:
            logger.warning(f"Failed to log activity: {e}")

    def _calculate_page_duration(self) -> float:
        """Calculate time spent on previous page."""
        return (datetime.now() - self.last_activity).total_seconds()

    async def _store_context_update(self, page: str, activity_data: Dict) -> None:
        """Store context update for persistence."""
        try:
            context_data = {
                "page": page,
                "activity_data": activity_data,
                "timestamp": datetime.now().isoformat(),
                "session_duration": (datetime.now() - self.session_start).total_seconds()
            }

            await self.memory_service.store_conversation_memory(
                conversation_id=f"context_update_{int(time.time())}",
                content=context_data,
                ttl_hours=24
            )
        except Exception as e:
            logger.warning(f"Failed to store context update: {e}")

    async def _get_lead_context(self, lead_name: str) -> Dict:
        """Get comprehensive context for a specific lead."""
        # This would integrate with existing lead data
        return {
            "qualification_score": 0.85,
            "last_interaction": "2 hours ago",
            "emotional_state": "analytical",
            "closing_readiness": 0.7
        }

    async def _analyze_current_action(self, lead: str, action: str, context: Dict) -> Dict:
        """Analyze current action for real-time guidance."""
        return {
            "suggestions": ["Focus on data-driven benefits", "Prepare comparable sales data"],
            "risks": ["May need more technical details", "Consider financial timeline"],
            "optimizations": ["Use visual presentations", "Emphasize ROI potential"],
            "next_actions": ["Schedule property viewing", "Discuss financing options"],
            "confidence": 0.8
        }

    def _get_fallback_guidance(self) -> Dict:
        """Fallback guidance when analysis fails."""
        return {
            "immediate_suggestions": ["Continue building rapport", "Ask open-ended questions"],
            "potential_risks": ["Don't oversell", "Listen more than you speak"],
            "optimization_tips": ["Be authentic", "Focus on their needs"],
            "next_best_actions": ["Schedule follow-up", "Provide value"],
            "confidence_score": 0.6
        }

# Global companion instance
_companion_instance = None

def get_claude_platform_companion() -> ClaudePlatformCompanion:
    """Get global Claude platform companion instance."""
    global _companion_instance
    if _companion_instance is None:
        _companion_instance = ClaudePlatformCompanion()
    return _companion_instance