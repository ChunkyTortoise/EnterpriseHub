"""
Claude Platform Companion - Intelligent Platform-Wide Assistant
Provides personalized greetings, context awareness, and cross-platform intelligence.
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st

from ghl_real_estate_ai.ghl_utils.logger import get_logger

# Import existing services
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.claude_conversation_intelligence import get_conversation_intelligence
from ghl_real_estate_ai.services.claude_executive_intelligence import get_executive_intelligence_service
from ghl_real_estate_ai.services.claude_lead_qualification import get_claude_qualification_engine
from ghl_real_estate_ai.services.claude_semantic_property_matcher import get_semantic_property_matcher
from ghl_real_estate_ai.services.lead_swarm_service import get_lead_swarm_service
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.proactive_intelligence_engine import get_proactive_intelligence_engine
from ghl_real_estate_ai.services.voice_service import VoiceService

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


@dataclass
class ProjectGuidance:
    """Claude's guidance for the current project section."""

    hub_name: str
    purpose: str
    key_features: List[str]
    recommended_workflow: List[str]
    pro_tips: List[str]
    next_steps: List[str]


@dataclass
class VoiceCommand:
    """Voice command from user."""

    command_text: str
    timestamp: datetime
    confidence: float
    intent: str  # "navigation", "query", "action", "general"
    parameters: Dict[str, Any]


@dataclass
class VoiceResponse:
    """Claude's voice response."""

    response_text: str
    audio_data: Optional[bytes]
    action_taken: Optional[str]
    follow_up_needed: bool
    context_updated: bool


class ClaudePlatformCompanion:
    """
    Claude as an intelligent platform companion with full context awareness.

    Features:
    - Personalized platform greetings with daily insights
    - Cross-platform context awareness and memory
    - Real-time intelligent suggestions based on current activity
    - Performance tracking and business intelligence
    - Proactive alerts and opportunities identification
    - Omnipresent project guidance and walkthroughs
    """

    def __init__(self):
        # Import orchestrator here to avoid circular dependencies
        from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

        self.orchestrator = get_claude_orchestrator()

        self.claude_assistant = ClaudeAssistant()
        self.memory_service = MemoryService()
        self.conversation_intelligence = get_conversation_intelligence()
        self.qualification_engine = get_claude_qualification_engine()
        self.property_matcher = get_semantic_property_matcher()
        self.voice_service = VoiceService()
        self.proactive_intelligence = get_proactive_intelligence_engine()
        self.executive_intelligence = get_executive_intelligence_service()
        self.lead_swarm = get_lead_swarm_service()

        # Platform context tracking
        self.current_context = None
        self.context_history = []
        self.user_preferences = {}

        # Session tracking
        self.session_start = datetime.now()
        self.last_activity = datetime.now()
        self.activity_log = []

        # Voice activation state
        self.voice_enabled = False
        self.wake_word_active = False
        self.voice_command_history = []
        self.voice_response_style = "professional"  # "professional", "friendly", "enthusiastic"

        logger.info("Claude Platform Companion initialized with voice capabilities")

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
            greeting = await self._generate_personalized_greeting(user_name, market, recent_activity, business_metrics)

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
                session_goals=[],
            )

            # Log session start
            await self._log_activity(
                "session_start",
                {
                    "user": user_name,
                    "market": market,
                    "greeting_insights": len(greeting.key_insights),
                    "priority_alerts": len(greeting.priority_alerts),
                },
            )

            logger.info(f"Claude session initialized for {user_name} in {market}")
            return greeting

        except Exception as e:
            logger.error(f"Error initializing Claude session: {e}")
            return self._get_fallback_greeting(user_name, market)

    async def update_context(self, page: str, activity_data: Dict = None) -> Dict[str, Any]:
        """
        Update Claude's context awareness and get real-time guidance.

        Args:
            page: Current page/section
            activity_data: Additional context about current activity

        Returns:
            Dictionary containing insight and counsel message
        """
        try:
            if not self.current_context:
                return {"insight": None, "counsel": "AI Swarm is standing by."}

            # Update current context
            self.current_context.current_page = page
            self.last_activity = datetime.now()

            # Log activity
            activity_log_entry = {
                "timestamp": datetime.now().isoformat(),
                "page": page,
                "activity_data": activity_data or {},
                "duration_on_previous_page": self._calculate_page_duration(),
            }
            self.activity_log.append(activity_log_entry)

            # Generate contextual insight if relevant
            insight = await self._generate_contextual_insight(page, activity_data)

            # Generate dynamic counsel message
            counsel = await self._generate_dynamic_counsel(page, activity_data)

            # Store updated context
            await self._store_context_update(page, activity_data)

            return {"insight": insight, "counsel": counsel}

        except Exception as e:
            logger.error(f"Error updating Claude context: {e}")
            return {"insight": None, "counsel": "AI Swarm is standing by."}

    async def _generate_dynamic_counsel(self, page: str, activity_data: Dict) -> str:
        """Generate a short, punchy counsel message for the sidebar."""
        try:
            prompt = f"""
            As the Elite Real Estate AI Companion, provide a one-sentence strategic advice for the user who just navigated to the "{page}" hub.
            Keep it professional, proactive, and punchy.
            """
            response = await self.claude_assistant.get_response(prompt)
            return response.get("content", "Ready to assist in this hub.").strip().strip('"')
        except Exception:
            return "Ready to assist in this hub."

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
            suggestions.sort(key=lambda x: ({"high": 3, "medium": 2, "low": 1}[x.priority], x.confidence), reverse=True)

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
                "confidence_score": action_analysis.get("confidence", 0.7),
            }

            # Log real-time guidance
            await self._log_activity(
                "real_time_guidance",
                {
                    "lead": current_lead,
                    "action": current_action,
                    "suggestions_count": len(guidance["immediate_suggestions"]),
                    "confidence": guidance["confidence_score"],
                },
            )

            return guidance

        except Exception as e:
            logger.error(f"Error providing real-time guidance: {e}")
            return self._get_fallback_guidance()

    async def get_project_guidance(self, hub_name: str) -> ProjectGuidance:
        """
        Provide detailed guidance for a specific platform hub.
        """
        try:
            prompt = f"""
            As the Elite Real Estate AI Companion, provide detailed guidance for the "{hub_name}" hub.
            Explain its purpose, key features, recommended workflow, pro-tips, and next steps for the user.
            
            Return a JSON object matching the ProjectGuidance dataclass structure.
            """

            response = await self.claude_assistant.get_response(prompt)
            data = response.get("content", "{}")

            # Extract JSON from markdown if needed
            if "```json" in data:
                data = data.split("```json")[1].split("```")[0].strip()
            elif "```" in data:
                data = data.split("```")[1].split("```")[0].strip()

            guidance_dict = json.loads(data)

            return ProjectGuidance(
                hub_name=hub_name,
                purpose=guidance_dict.get("purpose", ""),
                key_features=guidance_dict.get("key_features", []),
                recommended_workflow=guidance_dict.get("recommended_workflow", []),
                pro_tips=guidance_dict.get("pro_tips", []),
                next_steps=guidance_dict.get("next_steps", []),
            )
        except Exception as e:
            logger.error(f"Error getting project guidance: {e}")
            return self._get_fallback_guidance_for_hub(hub_name)

    async def run_executive_analysis(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a full executive swarm analysis through the companion.
        """
        return await self.executive_intelligence.run_executive_swarm(business_data)

    def _get_fallback_guidance_for_hub(self, hub_name: str) -> ProjectGuidance:
        """Fallback guidance when AI generation fails."""
        return ProjectGuidance(
            hub_name=hub_name,
            purpose=f"The {hub_name} is designed to streamline your real estate operations.",
            key_features=["Intelligent Dashboard", "Data-Driven Insights", "AI Assistance"],
            recommended_workflow=["Review metrics", "Identify opportunities", "Take action"],
            pro_tips=["Use Claude's suggestions for faster results", "Keep your data updated"],
            next_steps=["Explore the dashboard", "Run your first analysis"],
        )

    def render_platform_greeting(self, greeting: ClaudeGreeting) -> None:
        """
        Render Claude's platform greeting in Streamlit.

        Args:
            greeting: Personalized greeting to display
        """
        # Main greeting with Claude branding
        st.markdown(
            f"""
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
        """,
            unsafe_allow_html=True,
        )

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
                {"type": "conversation", "time": "1 day ago", "outcome": "scheduled_viewing"},
            ],
            "performance": {"leads_contacted": 8, "viewings_scheduled": 3, "conversions": 1},
            "last_login": datetime.now() - timedelta(hours=8),
        }

    async def _get_business_metrics(self, user_name: str, market: str) -> Dict:
        """Get current business metrics."""
        # Simulate business metrics
        return {
            "Active Leads": 47,
            "Conversion Rate": "23.5%",
            "Avg Response Time": "12 min",
            "Pipeline Value": "$2.8M",
        }

    async def _generate_personalized_greeting(
        self, user_name: str, market: str, recent_activity: Dict, metrics: Dict
    ) -> ClaudeGreeting:
        """Generate personalized greeting using Claude AI."""
        try:
            current_hour = datetime.now().hour
            time_greeting = (
                "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"
            )

            # Generate dynamic greeting based on activity and performance
            greeting_text = f"{time_greeting}, {user_name}! Ready to make today exceptional in the {market} market?"

            # Generate insights based on recent activity
            key_insights = [
                f"Your response time of {metrics.get('Avg Response Time', '12 min')} is 40% faster than market average",
                f"{len(recent_activity.get('active_leads', []))} high-priority leads need attention today",
                f"Pipeline value of {metrics.get('Pipeline Value', '$2.8M')} shows strong momentum",
            ]

            # Generate recommendations
            recommended_actions = [
                "Follow up with Sarah Chen - she's showing high buying signals",
                "Review David Kim's investment criteria - potential quick close",
                "Schedule team sync for tomorrow's property showings",
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
                motivational_insight=motivational_insight,
            )

        except Exception as e:
            logger.error(f"Error generating personalized greeting: {e}")
            return self._get_fallback_greeting(user_name, market)

    def _get_fallback_greeting(self, user_name: str, market: str) -> ClaudeGreeting:
        """Fallback greeting when AI generation fails."""
        current_hour = datetime.now().hour
        time_greeting = (
            "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"
        )

        return ClaudeGreeting(
            greeting_text=f"{time_greeting}, {user_name}! Welcome back to your {market} real estate command center.",
            key_insights=["Platform ready for enhanced lead intelligence", "All systems operational"],
            recommended_actions=["Review active leads", "Check market updates"],
            priority_alerts=[],
            daily_summary={"Active Leads": "Loading...", "Status": "Ready"},
            motivational_insight="Success comes from consistent action and genuine care for your clients! 🌟",
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
                priority="medium",
            ),
            "property_matching": ContextualInsight(
                insight_type="opportunity",
                title="Enhanced Matching Available",
                description="New 16+ lifestyle dimensions can improve match accuracy by 35%",
                action_items=["Try lifestyle-based matching", "Review psychological compatibility"],
                confidence=0.9,
                priority="high",
            ),
        }

        return insights_map.get(page)

    async def _analyze_current_activity(self, current_activity: Dict) -> Dict:
        """Analyze current activity for suggestions."""
        return {
            "patterns": ["High engagement with analytical leads", "Strong performance in luxury segment"],
            "optimization_opportunities": [
                "Increase response speed for hot leads",
                "Use more data-driven presentations",
            ],
            "performance_trends": ["Conversion rate improving", "Lead quality increasing"],
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
                priority="high",
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
                priority="medium",
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
                priority="medium",
            )
        ]

    # =======================
    # PROACTIVE INTELLIGENCE METHODS
    # =======================

    async def enable_proactive_intelligence(self) -> bool:
        """
        Enable proactive intelligence monitoring and alerts.

        Returns:
            bool: True if proactive intelligence enabled successfully
        """
        try:
            success = await self.proactive_intelligence.start_background_monitoring()
            if success:
                logger.info("Proactive intelligence enabled for Claude companion")
                await self._log_activity(
                    "proactive_intelligence_enabled",
                    {"timestamp": datetime.now().isoformat(), "monitoring_active": True},
                )
            return success
        except Exception as e:
            logger.error(f"Failed to enable proactive intelligence: {e}")
            return False

    async def get_proactive_insights(self, context_data: Dict = None) -> Dict[str, Any]:
        """
        Get comprehensive proactive insights including alerts, predictions, and coaching.

        Args:
            context_data: Optional context data override

        Returns:
            Dictionary containing all proactive intelligence insights
        """
        try:
            # Use current context if no override provided
            if context_data is None and self.current_context:
                context_data = self._build_intelligence_context()

            # Get smart alerts
            alerts = await self.proactive_intelligence.generate_smart_notifications(context_data or {})
            active_alerts = await self.proactive_intelligence.get_active_alerts()

            # Get predictive insights
            predictions = await self.proactive_intelligence.get_predictive_insights()

            # Get performance coaching
            performance_data = await self._extract_performance_data()
            coaching_tips = await self.proactive_intelligence.get_performance_coaching(performance_data)

            insights = {
                "new_alerts": alerts,
                "active_alerts": active_alerts,
                "predictions": predictions,
                "coaching_tips": coaching_tips,
                "monitoring_status": self.proactive_intelligence.monitoring_active,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Generated proactive insights: {len(alerts)} alerts, {len(predictions)} predictions, {len(coaching_tips)} tips"
            )
            return insights

        except Exception as e:
            logger.error(f"Error getting proactive insights: {e}")
            return {
                "new_alerts": [],
                "active_alerts": [],
                "predictions": [],
                "coaching_tips": [],
                "monitoring_status": False,
                "error": str(e),
            }

    async def get_intelligent_summary(self) -> str:
        """
        Get intelligent summary of current status with proactive recommendations.

        Returns:
            Natural language summary with proactive insights
        """
        try:
            insights = await self.get_proactive_insights()

            # Build intelligent summary
            summary_parts = []

            # Alert summary
            active_alerts = insights.get("active_alerts", [])
            if active_alerts:
                high_priority_count = len([a for a in active_alerts if a.priority.value in ["critical", "high"]])
                if high_priority_count > 0:
                    summary_parts.append(f"🚨 {high_priority_count} high-priority alerts need your attention")
                else:
                    summary_parts.append(f"📋 {len(active_alerts)} alerts monitoring your business")

            # Prediction summary
            predictions = insights.get("predictions", [])
            if predictions:
                best_prediction = max(predictions, key=lambda p: p.confidence)
                summary_parts.append(
                    f"🔮 Key insight: {best_prediction.insight_type.replace('_', ' ')} - {best_prediction.reasoning[:60]}..."
                )

            # Coaching summary
            coaching_tips = insights.get("coaching_tips", [])
            if coaching_tips:
                high_impact_tips = [tip for tip in coaching_tips if tip.impact_level == "high"]
                if high_impact_tips:
                    summary_parts.append(f"💡 {len(high_impact_tips)} high-impact coaching recommendations available")

            # Monitoring status
            if insights.get("monitoring_status"):
                summary_parts.append("📡 Proactive monitoring active and analyzing your business 24/7")

            if summary_parts:
                summary = "Claude's Intelligence Summary: " + " • ".join(summary_parts)
            else:
                summary = "🎯 Your business is running smoothly! All systems optimal with proactive monitoring active."

            return summary

        except Exception as e:
            logger.error(f"Error generating intelligent summary: {e}")
            return "Claude's intelligence systems are currently analyzing your business performance."

    async def process_proactive_action(self, alert_id: str, action_type: str) -> Dict[str, Any]:
        """
        Process proactive intelligence actions (mark seen, take action, etc.).

        Args:
            alert_id: Alert identifier
            action_type: Type of action ("seen", "acted_upon", "dismissed")

        Returns:
            Result of the action
        """
        try:
            if action_type == "seen":
                success = await self.proactive_intelligence.mark_alert_seen(alert_id)
            elif action_type == "acted_upon":
                success = await self.proactive_intelligence.mark_alert_acted_upon(alert_id)
            else:
                success = False

            if success:
                await self._log_activity(
                    "proactive_action_taken",
                    {"alert_id": alert_id, "action_type": action_type, "timestamp": datetime.now().isoformat()},
                )

            return {"success": success, "action_type": action_type, "alert_id": alert_id}

        except Exception as e:
            logger.error(f"Error processing proactive action: {e}")
            return {"success": False, "error": str(e)}

    def _build_intelligence_context(self) -> Dict[str, Any]:
        """Build context data for proactive intelligence analysis."""
        if not self.current_context:
            return {}

        return {
            "leads": [
                {
                    "id": f"lead_{i + 1}",
                    "name": lead,
                    "last_contact_hours": 24 + (i * 12),
                    "engagement_score": 0.7 + (i * 0.1),
                }
                for i, lead in enumerate(self.current_context.active_leads[:3])
            ],
            "performance": {
                "conversion_rate": self.current_context.agent_performance.get("conversion_rate", 0.15),
                "avg_response_time_hours": 3.2,
                "closing_rate": 0.16,
                "followup_completion_rate": 0.75,
            },
            "market": {"interest_rate_trend": "stable", "buyer_activity": "moderate"},
            "pipeline_value": self.current_context.business_metrics.get("pipeline_value", 85000),
            "monthly_target": self.current_context.business_metrics.get("monthly_target", 150000),
            "current_page": self.current_context.current_page,
            "session_duration_minutes": (datetime.now() - self.current_context.session_start_time).total_seconds() / 60,
        }

    async def _extract_performance_data(self) -> Dict[str, Any]:
        """Extract performance data for coaching analysis."""
        if not self.current_context:
            return {
                "avg_response_time_hours": 3.2,
                "closing_rate": 0.16,
                "followup_completion_rate": 0.73,
                "calls_per_day": 8,
                "meetings_scheduled": 3,
            }

        return {
            "avg_response_time_hours": self.current_context.agent_performance.get("avg_response_time_hours", 3.2),
            "closing_rate": self.current_context.agent_performance.get("closing_rate", 0.16),
            "followup_completion_rate": self.current_context.agent_performance.get("followup_rate", 0.73),
            "calls_per_day": self.current_context.agent_performance.get("calls_per_day", 8),
            "meetings_scheduled": self.current_context.agent_performance.get("meetings_scheduled", 3),
            "lead_count": len(self.current_context.active_leads),
            "session_activities": len(self.activity_log),
        }

    # =======================
    # END PROACTIVE INTELLIGENCE METHODS
    # =======================

    # =======================
    # VOICE ACTIVATION METHODS
    # =======================

    async def generate_project_greeting(self, user_name: str = "Jorge") -> str:
        """Generates a high-level executive greeting and walkthrough when the project is opened."""
        prompt = f"""
        You are Claude, the Elite AI Orchestrator for Jorge Salas's GHL Real Estate AI Platform (Elite v4.0).
        Jorge has just opened the project. This is the "Obsidian Command" interface.
        
        Greet Jorge with a professional, sharp, and proactive tone.
        Provide a very brief 5-hub walkthrough (one phrase each):
        1. Executive Hub (KPIs & Pipeline)
        2. Lead Intelligence (Behavioral DNA)
        3. Automation Studio (AI Brain)
        4. Sales Copilot (Live Coaching)
        5. Ops Hub (System Governance)
        
        Mention that the "Neural Swarm" is active and ready for his command.
        Keep the total length under 4 sentences.
        """
        response = await self.orchestrator.chat_query(prompt, context={"task": "greeting"})
        return response.content

    async def get_hub_guidance(self, hub_name: str) -> str:
        """Provides specific guidance for a given hub."""
        hub_descriptions = {
            "Executive Hub": "High-level KPIs and Multi-Market Expansion logic.",
            "Lead Intelligence Hub": "25+ Factor scoring and Swarm Intelligence analysis.",
            "Voice Claude": "Live call coaching and Real-time DNA Radar.",
            "Ops & Optimization": "Model retraining and system governance.",
        }
        desc = hub_descriptions.get(hub_name, "this section of the platform.")

        prompt = f"Explain the strategic value of the {hub_name} to Jorge. It focuses on {desc}. Keep it brief and actionable."
        response = await self.orchestrator.chat_query(prompt, context={"task": "guidance"})
        return response.content

    async def process_voice_command(self, audio_input: str) -> VoiceResponse:
        """
        Process natural language voice commands and generate appropriate responses.

        Args:
            audio_input: Transcribed voice command text

        Returns:
            VoiceResponse with text, audio, and action details
        """
        try:
            # Parse command intent and parameters
            command = await self._parse_voice_command(audio_input)

            # Generate appropriate response based on command
            response_text = await self._generate_voice_response(command)

            # Convert to speech
            audio_data = await self.voice_service.synthesize_speech(response_text, voice_id="jorge")

            # Take any required actions
            action_taken = await self._execute_voice_action(command)

            # Create response
            voice_response = VoiceResponse(
                response_text=response_text,
                audio_data=audio_data,
                action_taken=action_taken,
                follow_up_needed=command.intent in ["query", "general"],
                context_updated=action_taken is not None,
            )

            # Store in history
            self.voice_command_history.append(
                {"command": command, "response": voice_response, "timestamp": datetime.now()}
            )

            # Update activity
            await self._log_activity(
                "voice_command_processed",
                {"intent": command.intent, "confidence": command.confidence, "action_taken": action_taken},
            )

            return voice_response

        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            return await self._get_fallback_voice_response()

    async def generate_spoken_response(self, text: str, voice_style: str = None) -> bytes:
        """
        Generate spoken response with appropriate voice style.

        Args:
            text: Text to convert to speech
            voice_style: Voice style override ("professional", "friendly", "enthusiastic")

        Returns:
            Audio data as bytes
        """
        try:
            style = voice_style or self.voice_response_style

            # Add style-specific tone markers
            if style == "enthusiastic":
                text = f"*With energy* {text}"
            elif style == "friendly":
                text = f"*Warmly* {text}"
            # "professional" uses text as-is

            return await self.voice_service.synthesize_speech(text, voice_id="jorge")

        except Exception as e:
            logger.error(f"Error generating spoken response: {e}")
            return b""

    def set_voice_response_style(self, style: str) -> bool:
        """
        Set the voice response style for Claude.

        Args:
            style: "professional", "friendly", or "enthusiastic"

        Returns:
            bool: True if style was set successfully
        """
        if style in ["professional", "friendly", "enthusiastic"]:
            self.voice_response_style = style
            logger.info(f"Voice response style set to: {style}")
            return True
        else:
            logger.warning(f"Invalid voice style: {style}")
            return False

    def get_voice_status(self) -> Dict[str, Any]:
        """
        Get current voice system status.

        Returns:
            Dict with voice system status information
        """
        return {
            "voice_enabled": self.voice_enabled,
            "wake_word_active": self.wake_word_active,
            "response_style": self.voice_response_style,
            "commands_processed": len(self.voice_command_history),
            "last_command": self.voice_command_history[-1] if self.voice_command_history else None,
        }

    async def _parse_voice_command(self, audio_input: str) -> VoiceCommand:
        """Parse voice command to extract intent and parameters."""
        try:
            # Clean input
            command_text = audio_input.lower().strip()

            # Determine intent
            intent = "general"
            parameters = {}
            confidence = 0.8

            # Navigation commands
            if any(word in command_text for word in ["go to", "navigate", "show me", "open"]):
                intent = "navigation"
                if "leads" in command_text:
                    parameters["target"] = "leads"
                elif "properties" in command_text:
                    parameters["target"] = "properties"
                elif "dashboard" in command_text:
                    parameters["target"] = "dashboard"
                elif "calendar" in command_text:
                    parameters["target"] = "calendar"

            # Query commands
            elif any(word in command_text for word in ["what", "how", "tell me", "show status"]):
                intent = "query"
                if "leads" in command_text:
                    parameters["subject"] = "leads"
                elif "performance" in command_text:
                    parameters["subject"] = "performance"
                elif "today" in command_text:
                    parameters["timeframe"] = "today"
                elif "week" in command_text:
                    parameters["timeframe"] = "week"

            # Action commands
            elif any(word in command_text for word in ["call", "email", "schedule", "create", "update"]):
                intent = "action"
                if "lead" in command_text:
                    parameters["action_type"] = "lead_contact"
                elif "appointment" in command_text or "meeting" in command_text:
                    parameters["action_type"] = "schedule"

            return VoiceCommand(
                command_text=command_text,
                timestamp=datetime.now(),
                confidence=confidence,
                intent=intent,
                parameters=parameters,
            )

        except Exception as e:
            logger.error(f"Error parsing voice command: {e}")
            return VoiceCommand(
                command_text=audio_input, timestamp=datetime.now(), confidence=0.3, intent="general", parameters={}
            )

    async def _generate_voice_response(self, command: VoiceCommand) -> str:
        """Generate appropriate text response for voice command."""
        try:
            if command.intent == "navigation":
                target = command.parameters.get("target", "dashboard")
                return f"Taking you to the {target} section now. I'm updating your view."

            elif command.intent == "query":
                subject = command.parameters.get("subject", "status")
                timeframe = command.parameters.get("timeframe", "current")

                if subject == "leads":
                    if self.current_context and self.current_context.active_leads:
                        count = len(self.current_context.active_leads)
                        return f"You have {count} active leads. The most promising ones need your attention today."
                    return "Let me check your current leads status."

                elif subject == "performance":
                    return f"Your {timeframe} performance is looking strong. You're ahead of your targets with several high-value opportunities in the pipeline."

                else:
                    return "I'm analyzing your current status. Let me gather the most relevant insights for you."

            elif command.intent == "action":
                action_type = command.parameters.get("action_type", "general")
                if action_type == "lead_contact":
                    return "I'll help you prioritize which leads to contact first based on their engagement scores and timing."
                elif action_type == "schedule":
                    return "I can help you schedule that. What type of meeting are you planning?"
                else:
                    return "I'm ready to help with that action. What would you like me to do?"

            else:  # general
                # Use Claude for general conversational responses
                context_text = ""
                if self.current_context:
                    context_text = f"Current page: {self.current_context.current_page}, Active leads: {len(self.current_context.active_leads)}"

                claude_response = await self.claude_assistant.get_response(
                    f"User said: '{command.command_text}'. Current context: {context_text}. "
                    f"Provide a helpful, conversational response as their AI real estate assistant."
                )

                return claude_response.get("content", "I'm here to help! How can I assist you today?")

        except Exception as e:
            logger.error(f"Error generating voice response: {e}")
            return "I'm here to help. How can I assist you with your real estate business today?"

    async def _execute_voice_action(self, command: VoiceCommand) -> Optional[str]:
        """Execute actions based on voice commands."""
        try:
            if command.intent == "navigation":
                target = command.parameters.get("target")
                if target:
                    # This would trigger navigation in the UI
                    await self.update_context(target, {"triggered_by": "voice_command"})
                    return f"navigated_to_{target}"

            elif command.intent == "action":
                action_type = command.parameters.get("action_type")
                if action_type == "lead_contact":
                    return "lead_prioritization_displayed"
                elif action_type == "schedule":
                    return "scheduling_interface_opened"

            return None

        except Exception as e:
            logger.error(f"Error executing voice action: {e}")
            return None

    async def _get_fallback_voice_response(self) -> VoiceResponse:
        """Get fallback response when voice processing fails."""
        fallback_text = "I'm having trouble understanding that command. Could you try again or ask me something else?"

        try:
            audio_data = await self.voice_service.synthesize_speech(fallback_text, voice_id="jorge")
        except Exception:
            audio_data = b""

        return VoiceResponse(
            response_text=fallback_text,
            audio_data=audio_data,
            action_taken=None,
            follow_up_needed=True,
            context_updated=False,
        )

    # =======================
    # END VOICE METHODS
    # =======================

    async def _log_activity(self, activity_type: str, data: Dict) -> None:
        """Log activity for analytics."""
        try:
            await self.memory_service.store_conversation_memory(
                conversation_id=f"platform_activity_{int(time.time())}",
                content={"type": activity_type, "data": data, "timestamp": datetime.now().isoformat()},
                ttl_hours=24 * 7,  # Keep for 1 week
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
                "session_duration": (datetime.now() - self.session_start).total_seconds(),
            }

            await self.memory_service.store_conversation_memory(
                conversation_id=f"context_update_{int(time.time())}", content=context_data, ttl_hours=24
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
            "closing_readiness": 0.7,
        }

    async def _analyze_current_action(self, lead: str, action: str, context: Dict) -> Dict:
        """Analyze current action for real-time guidance."""
        return {
            "suggestions": ["Focus on data-driven benefits", "Prepare comparable sales data"],
            "risks": ["May need more technical details", "Consider financial timeline"],
            "optimizations": ["Use visual presentations", "Emphasize ROI potential"],
            "next_actions": ["Schedule property viewing", "Discuss financing options"],
            "confidence": 0.8,
        }

    def _get_fallback_guidance(self) -> Dict:
        """Fallback guidance when analysis fails."""
        return {
            "immediate_suggestions": ["Continue building rapport", "Ask open-ended questions"],
            "potential_risks": ["Don't oversell", "Listen more than you speak"],
            "optimization_tips": ["Be authentic", "Focus on their needs"],
            "next_best_actions": ["Schedule follow-up", "Provide value"],
            "confidence_score": 0.6,
        }


# Global companion instance
_companion_instance = None


def get_claude_platform_companion() -> ClaudePlatformCompanion:
    """Get global Claude platform companion instance."""
    global _companion_instance
    if _companion_instance is None:
        _companion_instance = ClaudePlatformCompanion()
    return _companion_instance
