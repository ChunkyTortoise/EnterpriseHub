"""
Enhanced Chatbot Integration Layer

Integrates the Lead Evaluation Orchestrator, Claude Semantic Analyzer,
and Agent Assistance Dashboard with the existing chat interface to provide
real-time agent assistance during conversations with prospects.

This layer enhances existing chat functionality without breaking compatibility.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import streamlit as st
import redis.asyncio as redis
from pathlib import Path

# Import our new components
from services.lead_evaluation_orchestrator import LeadEvaluationOrchestrator, create_lead_evaluator
from services.claude_semantic_analyzer import (
    ClaudeSemanticAnalyzer,
    ConversationContext,
    AnalysisType,
    create_claude_analyzer
)
from streamlit_components.agent_assistance_dashboard import AgentAssistanceDashboard, create_agent_dashboard
from models.evaluation_models import (
    LeadEvaluationResult,
    ConversationEvaluationContext,
    QualificationStatus,
    SentimentType,
    EngagementLevel,
    ActionPriority
)

# Import existing chat system
from services.streamlit_chat_component import (
    initialize_chat_system,
    render_chat_demo,
    render_lead_chat,
    add_chat_to_page
)

logger = logging.getLogger(__name__)


@dataclass
class EnhancedChatConfig:
    """Configuration for enhanced chat integration."""
    enable_real_time_evaluation: bool = True
    enable_semantic_analysis: bool = True
    enable_agent_dashboard: bool = True
    enable_objection_detection: bool = True
    enable_auto_suggestions: bool = True
    evaluation_interval_seconds: int = 3
    max_conversation_history: int = 50
    cache_enabled: bool = True
    debug_mode: bool = False


@dataclass
class ChatMessage:
    """Standardized chat message structure."""
    role: str  # 'agent', 'prospect', 'system'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class EnhancedChatbotIntegration:
    """
    Enhanced chatbot integration that provides real-time agent assistance
    during conversations with prospects.
    """

    def __init__(
        self,
        config: Optional[EnhancedChatConfig] = None,
        redis_url: str = "redis://localhost:6379/0"
    ):
        """
        Initialize enhanced chatbot integration.

        Args:
            config: Configuration for enhanced features
            redis_url: Redis URL for caching and real-time updates
        """
        self.config = config or EnhancedChatConfig()
        self.redis_url = redis_url

        # Initialize components
        self.orchestrator: Optional[LeadEvaluationOrchestrator] = None
        self.semantic_analyzer: Optional[ClaudeSemanticAnalyzer] = None
        self.dashboard: Optional[AgentAssistanceDashboard] = None

        # Conversation state management
        self.conversation_states: Dict[str, Dict[str, Any]] = {}
        self.active_evaluations: Dict[str, asyncio.Task] = {}

        # Performance tracking
        self.stats = {
            "conversations_analyzed": 0,
            "objections_detected": 0,
            "recommendations_provided": 0,
            "average_response_time_ms": 0.0
        }

        # Initialize session state keys
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Initialize Streamlit session state for enhanced chat."""
        session_defaults = {
            "enhanced_chat_enabled": True,
            "current_conversation_id": None,
            "conversation_history": [],
            "latest_evaluation": None,
            "agent_assistance_visible": True,
            "objection_alerts": [],
            "suggested_responses": [],
            "conversation_analytics": {},
            "real_time_updates": True
        }

        for key, default_value in session_defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    async def initialize_components(self) -> None:
        """Initialize all AI components asynchronously."""
        try:
            # Initialize orchestrator
            if self.config.enable_real_time_evaluation:
                self.orchestrator = await create_lead_evaluator(
                    redis_url=self.redis_url,
                    enable_caching=self.config.cache_enabled
                )
                logger.info("Lead evaluation orchestrator initialized")

            # Initialize semantic analyzer
            if self.config.enable_semantic_analysis:
                self.semantic_analyzer = create_claude_analyzer()
                logger.info("Claude semantic analyzer initialized")

            # Initialize dashboard
            if self.config.enable_agent_dashboard:
                self.dashboard = create_agent_dashboard()
                logger.info("Agent assistance dashboard initialized")

            logger.info("Enhanced chatbot integration initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize enhanced chat components: {e}")
            raise

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.semantic_analyzer:
            await self.semantic_analyzer.close()

        # Cancel active evaluation tasks
        for task in self.active_evaluations.values():
            task.cancel()

        logger.info("Enhanced chatbot integration cleaned up")

    def render_enhanced_chat_interface(
        self,
        lead_id: str,
        lead_data: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> None:
        """
        Render the enhanced chat interface with real-time agent assistance.

        Args:
            lead_id: Unique lead identifier
            lead_data: Lead information and context
            conversation_id: Optional conversation ID (auto-generated if None)
        """
        # Generate conversation ID if not provided
        if conversation_id is None:
            conversation_id = f"conv_{lead_id}_{int(time.time())}"

        # Update session state
        st.session_state.current_conversation_id = conversation_id

        # Create layout for enhanced interface
        self._render_enhanced_layout(lead_id, lead_data, conversation_id)

    def _render_enhanced_layout(
        self,
        lead_id: str,
        lead_data: Optional[Dict[str, Any]],
        conversation_id: str
    ) -> None:
        """Render the enhanced chat layout with real-time assistance."""

        # Header with enhanced controls
        st.markdown("""
        <div class="enhanced-chat-header" style="
            background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%);
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            color: white;
            text-align: center;
        ">
            <h2 style="margin: 0; font-size: 1.5rem; font-weight: 700;">
                🤖 Enhanced AI Conversation Assistant
            </h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">
                Real-time lead evaluation and agent guidance
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Control panel
        self._render_control_panel()

        # Main chat layout
        if st.session_state.agent_assistance_visible:
            # Two-column layout with chat and assistance
            chat_col, assist_col = st.columns([3, 2])
        else:
            # Full-width chat
            chat_col = st.container()
            assist_col = None

        with chat_col:
            self._render_chat_interface(lead_id, conversation_id, lead_data)

        if assist_col and st.session_state.agent_assistance_visible:
            with assist_col:
                self._render_real_time_assistance(lead_id, conversation_id)

        # Real-time evaluation trigger
        if st.session_state.real_time_updates and st.session_state.enhanced_chat_enabled:
            self._trigger_real_time_evaluation(lead_id, conversation_id, lead_data)

    def _render_control_panel(self) -> None:
        """Render enhanced chat control panel."""
        with st.expander("⚙️ Enhanced Chat Controls", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.session_state.enhanced_chat_enabled = st.checkbox(
                    "🚀 Enhanced AI",
                    value=st.session_state.enhanced_chat_enabled,
                    help="Enable real-time AI analysis and assistance"
                )

            with col2:
                st.session_state.agent_assistance_visible = st.checkbox(
                    "📊 Show Dashboard",
                    value=st.session_state.agent_assistance_visible,
                    help="Show agent assistance dashboard"
                )

            with col3:
                st.session_state.real_time_updates = st.checkbox(
                    "🔄 Live Updates",
                    value=st.session_state.real_time_updates,
                    help="Enable real-time conversation analysis"
                )

            with col4:
                if st.button("🧹 Clear History"):
                    st.session_state.conversation_history = []
                    st.session_state.objection_alerts = []
                    st.session_state.suggested_responses = []
                    st.toast("Chat history cleared!")

    def _render_chat_interface(
        self,
        lead_id: str,
        conversation_id: str,
        lead_data: Optional[Dict[str, Any]]
    ) -> None:
        """Render the enhanced chat interface."""
        st.markdown("### 💬 Conversation")

        # Chat history container
        chat_container = st.container()

        with chat_container:
            # Display conversation history
            for message in st.session_state.conversation_history:
                self._render_chat_message(message)

        # Message input with enhanced features
        st.markdown("---")

        # Quick actions for agents
        if st.session_state.enhanced_chat_enabled:
            self._render_quick_actions()

        # Message input
        col_input, col_send = st.columns([4, 1])

        with col_input:
            message_text = st.text_input(
                "Your message:",
                key="chat_message_input",
                placeholder="Type your message to the prospect..."
            )

        with col_send:
            if st.button("📤 Send", key="send_button", type="primary"):
                if message_text.strip():
                    self._handle_message_send(message_text, lead_id, conversation_id)

        # Suggested responses
        if st.session_state.suggested_responses and st.session_state.enhanced_chat_enabled:
            self._render_suggested_responses()

    def _render_chat_message(self, message: Dict[str, Any]) -> None:
        """Render a single chat message with enhanced styling."""
        role = message.get("role", "unknown")
        content = message.get("content", "")
        timestamp = message.get("timestamp", datetime.now())

        # Determine message styling based on role
        if role == "agent":
            bg_color = "#e0f2fe"
            align = "right"
            icon = "👨‍💼"
            name = "Agent"
        elif role == "prospect":
            bg_color = "#f0f9ff"
            align = "left"
            icon = "👤"
            name = "Prospect"
        else:
            bg_color = "#f8fafc"
            align = "center"
            icon = "🤖"
            name = "System"

        st.markdown(f"""
        <div style="
            display: flex;
            justify-content: {align};
            margin-bottom: 1rem;
        ">
            <div style="
                background: {bg_color};
                padding: 1rem;
                border-radius: 12px;
                max-width: 70%;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    margin-bottom: 0.5rem;
                    font-weight: 600;
                    color: #1e293b;
                    font-size: 0.875rem;
                ">
                    <span style="margin-right: 0.5rem;">{icon}</span>
                    {name}
                    <span style="
                        margin-left: auto;
                        font-weight: 400;
                        color: #64748b;
                        font-size: 0.75rem;
                    ">{timestamp.strftime('%H:%M')}</span>
                </div>
                <div style="
                    color: #334155;
                    line-height: 1.5;
                ">{content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _render_quick_actions(self) -> None:
        """Render quick action buttons for agents."""
        st.markdown("**⚡ Quick Actions:**")

        col1, col2, col3, col4 = st.columns(4)

        quick_responses = [
            "Thank you for your interest!",
            "Let me get that information for you.",
            "Would you like to schedule a showing?",
            "What's your timeline for purchasing?"
        ]

        for i, (col, response) in enumerate(zip([col1, col2, col3, col4], quick_responses)):
            with col:
                if st.button(f"💬 {response[:12]}...", key=f"quick_{i}"):
                    st.session_state.chat_message_input = response

    def _render_suggested_responses(self) -> None:
        """Render AI-suggested responses."""
        st.markdown("### 🎯 AI Suggestions")

        for i, suggestion in enumerate(st.session_state.suggested_responses[:3]):
            if st.button(f"💡 {suggestion[:50]}...", key=f"suggestion_{i}"):
                st.session_state.chat_message_input = suggestion

    def _render_real_time_assistance(self, lead_id: str, conversation_id: str) -> None:
        """Render real-time agent assistance panel."""
        st.markdown("### 🎯 Agent Assistant")

        # Show latest evaluation if available
        if st.session_state.latest_evaluation:
            evaluation_result = st.session_state.latest_evaluation

            # Use the dashboard component
            if self.dashboard:
                self.dashboard.render_main_dashboard(
                    evaluation_result=evaluation_result,
                    live_mode=True
                )
            else:
                self._render_basic_assistance(evaluation_result)
        else:
            st.info("Start the conversation to see AI insights...")

        # Objection alerts
        if st.session_state.objection_alerts:
            st.markdown("### ⚠️ Objection Alerts")
            for alert in st.session_state.objection_alerts[-3:]:  # Show last 3
                st.warning(f"**{alert['type']}**: {alert['text']}")

    def _render_basic_assistance(self, evaluation_result: LeadEvaluationResult) -> None:
        """Render basic assistance when dashboard is not available."""
        # Lead score
        score = evaluation_result.scoring_breakdown.composite_score
        st.metric("Lead Score", f"{score:.1f}", delta=None)

        # Qualification progress
        progress = evaluation_result.qualification_progress.completion_percentage
        st.progress(progress / 100.0)
        st.caption(f"Qualification: {progress:.1f}% complete")

        # Top recommendations
        if evaluation_result.recommended_actions:
            st.markdown("**🎯 Top Recommendations:**")
            for action in evaluation_result.recommended_actions[:3]:
                st.markdown(f"• {action.description}")

    def _handle_message_send(self, message_text: str, lead_id: str, conversation_id: str) -> None:
        """Handle sending a message and trigger analysis."""
        # Add message to conversation history
        message = {
            "role": "agent",
            "content": message_text,
            "timestamp": datetime.now(),
            "conversation_id": conversation_id
        }

        st.session_state.conversation_history.append(message)

        # Clear input
        st.session_state.chat_message_input = ""

        # Simulate prospect response (in real app, this would come from actual prospect)
        self._simulate_prospect_response(lead_id, conversation_id)

        # Trigger real-time analysis
        if st.session_state.enhanced_chat_enabled:
            # Schedule async evaluation
            asyncio.create_task(self._analyze_conversation_async(lead_id, conversation_id))

        # Refresh interface
        st.rerun()

    def _simulate_prospect_response(self, lead_id: str, conversation_id: str) -> None:
        """Simulate a prospect response for demo purposes."""
        import random

        sample_responses = [
            "I'm interested but the prices seem high...",
            "When would be a good time to see some properties?",
            "I need to discuss this with my partner first.",
            "What areas do you recommend for families?",
            "I'm pre-approved for up to $500k.",
            "The market seems crazy right now. Is it a good time to buy?",
            "I saw a listing online that caught my eye.",
            "How long does the buying process usually take?"
        ]

        # Add a slight delay simulation
        time.sleep(1)

        prospect_message = {
            "role": "prospect",
            "content": random.choice(sample_responses),
            "timestamp": datetime.now(),
            "conversation_id": conversation_id
        }

        st.session_state.conversation_history.append(prospect_message)

    def _trigger_real_time_evaluation(
        self,
        lead_id: str,
        conversation_id: str,
        lead_data: Optional[Dict[str, Any]]
    ) -> None:
        """Trigger real-time conversation evaluation."""
        if not st.session_state.conversation_history:
            return

        # Check if enough time has passed since last evaluation
        last_eval_time = getattr(st.session_state, 'last_evaluation_time', 0)
        current_time = time.time()

        if current_time - last_eval_time < self.config.evaluation_interval_seconds:
            return

        # Update last evaluation time
        st.session_state.last_evaluation_time = current_time

        # Create evaluation task
        try:
            # For Streamlit compatibility, we'll do synchronous evaluation
            evaluation_result = self._evaluate_conversation_sync(lead_id, conversation_id, lead_data)

            if evaluation_result:
                st.session_state.latest_evaluation = evaluation_result

                # Update suggestions and alerts
                self._update_suggestions_and_alerts(evaluation_result)

        except Exception as e:
            logger.error(f"Real-time evaluation failed: {e}")

    def _evaluate_conversation_sync(
        self,
        lead_id: str,
        conversation_id: str,
        lead_data: Optional[Dict[str, Any]]
    ) -> Optional[LeadEvaluationResult]:
        """Synchronous conversation evaluation for Streamlit compatibility."""
        try:
            # Prepare conversation data
            conversation_messages = st.session_state.conversation_history[-10:]  # Last 10 messages

            # Extract conversation text for analysis
            conversation_text = " ".join([msg.get("content", "") for msg in conversation_messages])

            # Simple lead data preparation
            lead_evaluation_data = {
                "lead_id": lead_id,
                "conversation_id": conversation_id,
                "conversation_history": conversation_messages,
                "conversation_text": conversation_text,
                "message_count": len(st.session_state.conversation_history),
                "last_message_time": datetime.now().isoformat(),
                **(lead_data or {})
            }

            # Create mock evaluation result for demo
            # In production, this would call the actual orchestrator
            evaluation_result = self._create_mock_evaluation_result(lead_id, lead_evaluation_data)

            return evaluation_result

        except Exception as e:
            logger.error(f"Synchronous evaluation failed: {e}")
            return None

    def _create_mock_evaluation_result(
        self,
        lead_id: str,
        lead_data: Dict[str, Any]
    ) -> LeadEvaluationResult:
        """Create a mock evaluation result for demonstration."""
        from models.evaluation_models import (
            ScoringBreakdown,
            QualificationProgress,
            AgentAssistanceData,
            RecommendedAction,
            UrgencySignals
        )

        # Calculate basic scores based on conversation
        message_count = lead_data.get("message_count", 0)
        conversation_text = lead_data.get("conversation_text", "")

        # Simple scoring logic for demo
        base_score = min(50 + (message_count * 5), 95)
        engagement_bonus = 10 if len(conversation_text) > 100 else 0
        final_score = min(base_score + engagement_bonus, 100)

        # Create scoring breakdown
        scoring_breakdown = ScoringBreakdown(
            basic_rules_score=final_score * 0.8,
            advanced_intelligence_score=final_score * 0.9,
            predictive_ml_score=final_score * 0.85,
            urgency_detection_score=final_score * 0.7,
            budget_alignment=final_score * 0.9,
            location_preference=final_score * 0.8,
            timeline_urgency=final_score * 0.75,
            engagement_level=final_score * 0.95,
            communication_quality=final_score * 0.9,
            qualification_completeness=final_score * 0.6,
            composite_score=final_score,
            confidence_interval=(final_score - 5, final_score + 5)
        )

        # Create qualification progress
        qualification_progress = QualificationProgress(
            total_fields=10,
            completed_fields=min(message_count, 8),
            partial_fields=1,
            missing_fields=max(1, 10 - message_count),
            completion_percentage=min((message_count / 10) * 100, 90),
            critical_fields_complete=message_count > 5,
            qualification_tier="warm_lead" if final_score > 70 else "developing_lead",
            next_priority_fields=["budget", "timeline", "location"][:max(0, 3 - message_count // 2)]
        )

        # Create agent assistance data
        agent_assistance = AgentAssistanceData(
            current_sentiment=SentimentType.POSITIVE if "interested" in conversation_text else SentimentType.NEUTRAL,
            engagement_level=EngagementLevel.ENGAGED if message_count > 3 else EngagementLevel.MODERATELY_ENGAGED,
            conversation_flow_stage="qualification",
            detected_objections=[],
            urgency_signals=UrgencySignals(),
            qualification_gaps=["budget", "timeline"][:max(0, 2 - message_count // 3)],
            immediate_actions=[],
            suggested_questions=[
                "What's your ideal budget range?",
                "When are you looking to make a purchase?",
                "What areas interest you most?"
            ][:max(0, 3 - message_count // 2)],
            conversation_effectiveness=min(5.0 + (message_count * 0.5), 10.0),
            rapport_building_score=min(4.0 + (message_count * 0.6), 10.0),
            information_gathering_rate=min(3.0 + (message_count * 0.8), 10.0)
        )

        # Create recommended actions
        recommended_actions = []
        if final_score > 80:
            recommended_actions.append(
                RecommendedAction(
                    action_type="schedule_showing",
                    priority=ActionPriority.HIGH,
                    description="Schedule property showing",
                    reasoning="Lead is highly qualified",
                    confidence=0.9,
                    estimated_duration=5
                )
            )

        return LeadEvaluationResult(
            lead_id=lead_id,
            evaluation_id=f"eval_{int(time.time())}",
            scoring_breakdown=scoring_breakdown,
            qualification_progress=qualification_progress,
            qualification_fields={},
            agent_assistance=agent_assistance,
            recommended_actions=recommended_actions,
            evaluation_duration_ms=50,
            confidence_score=0.85,
            data_freshness_score=0.95,
            evaluation_quality_score=0.9
        )

    def _update_suggestions_and_alerts(self, evaluation_result: LeadEvaluationResult) -> None:
        """Update suggestions and alerts based on evaluation."""
        # Update suggested responses
        suggestions = evaluation_result.agent_assistance.suggested_questions
        if suggestions:
            st.session_state.suggested_responses = suggestions

        # Update objection alerts (demo - would analyze conversation for real objections)
        conversation_text = " ".join([
            msg.get("content", "")
            for msg in st.session_state.conversation_history[-3:]
        ]).lower()

        alerts = []
        if "expensive" in conversation_text or "price" in conversation_text or "cost" in conversation_text:
            alerts.append({
                "type": "Price Objection",
                "text": "Prospect may have price concerns",
                "severity": "medium"
            })

        if "think about it" in conversation_text or "discuss" in conversation_text:
            alerts.append({
                "type": "Decision Delay",
                "text": "Prospect wants to delay decision",
                "severity": "low"
            })

        st.session_state.objection_alerts = alerts

    async def _analyze_conversation_async(self, lead_id: str, conversation_id: str) -> None:
        """Async conversation analysis (for future real-time updates)."""
        try:
            # This would be the full async analysis in production
            # For now, we'll use the sync version
            pass
        except Exception as e:
            logger.error(f"Async conversation analysis failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get integration performance statistics."""
        return {
            **self.stats,
            "components_initialized": {
                "orchestrator": self.orchestrator is not None,
                "semantic_analyzer": self.semantic_analyzer is not None,
                "dashboard": self.dashboard is not None
            },
            "active_conversations": len(self.conversation_states),
            "session_state_keys": len([k for k in st.session_state.keys() if "enhanced_chat" in k])
        }


# Factory function for easy integration
def create_enhanced_chatbot_integration(
    config: Optional[EnhancedChatConfig] = None
) -> EnhancedChatbotIntegration:
    """
    Factory function to create enhanced chatbot integration.

    Args:
        config: Configuration for enhanced features

    Returns:
        Initialized EnhancedChatbotIntegration
    """
    return EnhancedChatbotIntegration(config=config)


# Enhanced chat interface wrapper
def render_enhanced_lead_chat(
    lead_id: str,
    lead_data: Optional[Dict[str, Any]] = None,
    enable_real_time_assistance: bool = True
) -> None:
    """
    Render enhanced lead chat interface with real-time AI assistance.

    Args:
        lead_id: Unique lead identifier
        lead_data: Lead context and information
        enable_real_time_assistance: Enable real-time AI features
    """
    # Create configuration
    config = EnhancedChatConfig(
        enable_real_time_evaluation=enable_real_time_assistance,
        enable_semantic_analysis=enable_real_time_assistance,
        enable_agent_dashboard=enable_real_time_assistance,
        enable_objection_detection=enable_real_time_assistance
    )

    # Initialize integration
    integration = create_enhanced_chatbot_integration(config)

    # Render enhanced interface
    integration.render_enhanced_chat_interface(lead_id, lead_data)


# Integration with existing app
def enhance_existing_chat_interface() -> None:
    """
    Enhance the existing chat interface with AI capabilities.
    This function can be called from the main app to add enhanced features.
    """
    if st.session_state.get("enhanced_chat_available", False):
        st.success("🚀 Enhanced AI Chat Features Active")

        # Add enhanced chat toggle to sidebar
        with st.sidebar:
            st.markdown("### 🤖 Enhanced AI Features")

            enhanced_enabled = st.checkbox(
                "Enable Real-time AI Assistance",
                value=st.session_state.get("enhanced_chat_enabled", True),
                help="Provides real-time lead evaluation and conversation guidance"
            )

            st.session_state.enhanced_chat_enabled = enhanced_enabled

            if enhanced_enabled:
                st.markdown("✅ **Active Features:**")
                st.markdown("• Real-time lead scoring")
                st.markdown("• Objection detection")
                st.markdown("• Response suggestions")
                st.markdown("• Qualification tracking")

                # Performance stats
                integration = create_enhanced_chatbot_integration()
                stats = integration.get_stats()

                st.markdown("### 📊 AI Performance")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Conversations", stats.get("conversations_analyzed", 0))
                with col2:
                    st.metric("Objections", stats.get("objections_detected", 0))


# Usage example and integration pattern:
"""
# In your main Streamlit app (app.py), add this to the Lead Intelligence Hub:

def render_enhanced_lead_chat_interface():
    st.header("💬 Enhanced Lead Conversation")

    # Get selected lead
    lead_id = st.session_state.get("selected_lead_name", "lead_001")
    lead_data = get_lead_data(lead_id)  # Your existing function

    # Render enhanced chat
    render_enhanced_lead_chat(
        lead_id=lead_id,
        lead_data=lead_data,
        enable_real_time_assistance=True
    )

# Add to your main hub routing:
if selected_hub == "🧠 Lead Intelligence Hub":
    # Add enhanced chat tab
    tabs = st.tabs(["🎯 Lead Scoring", "💬 Enhanced Chat", ...])

    with tabs[1]:  # Enhanced Chat tab
        render_enhanced_lead_chat_interface()
"""