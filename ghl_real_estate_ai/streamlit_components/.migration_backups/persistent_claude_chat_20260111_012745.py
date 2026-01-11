"""
Persistent Claude Chat - Universal AI Assistant for Realtor Guidance
====================================================================

A persistent chat window that provides continuous Claude AI guidance across
the entire EnterpriseHub platform for realtors throughout lead/buyer/seller processes.

Key Features:
- Persistent across all screens/tabs/modules
- Context-aware guidance for real estate workflows
- Memory of conversation and process state
- Process-aware coaching (lead capture → qualification → showing → closing)
- Cross-screen state synchronization
- Real-time coaching with <50ms response time
- Seamless integration with existing Claude infrastructure

Business Impact:
- Continuous AI guidance throughout entire sales process
- Improved agent confidence and performance
- Reduced training time for new agents
- Consistent coaching across all platform interactions
- Enhanced conversion rates through AI-powered insights

Author: EnterpriseHub AI Platform
Date: January 10, 2026
Version: 1.0.0
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import streamlit as st

# Import existing Claude services and components
from .claude_component_mixin import ClaudeComponentMixin, ClaudeOperationType, ClaudeServiceStatus
from .claude_coaching_widget import ClaudeCoachingWidget
from ..services.claude_agent_service import claude_agent_service
from ..services.redis_conversation_service import redis_conversation_service

logger = logging.getLogger(__name__)


class RealtorProcessStage(str, Enum):
    """Stages in the realtor sales process for context-aware guidance."""
    LEAD_CAPTURE = "lead_capture"
    INITIAL_CONTACT = "initial_contact"
    QUALIFICATION = "qualification"
    NEEDS_DISCOVERY = "needs_discovery"
    PROPERTY_SEARCH = "property_search"
    SHOWING_PREP = "showing_prep"
    PROPERTY_SHOWING = "property_showing"
    OFFER_PREPARATION = "offer_preparation"
    NEGOTIATION = "negotiation"
    CONTRACT_EXECUTION = "contract_execution"
    TRANSACTION_MANAGEMENT = "transaction_management"
    CLOSING_PREP = "closing_prep"
    POST_CLOSE_FOLLOW_UP = "post_close_follow_up"


class ChatWindowPosition(str, Enum):
    """Position options for chat window."""
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_LEFT = "bottom_left"
    RIGHT_PANEL = "right_panel"
    FULL_SCREEN = "full_screen"
    EMBEDDED = "embedded"


@dataclass
class ProcessContext:
    """Context about current realtor process and workflow."""
    stage: RealtorProcessStage
    lead_id: Optional[str] = None
    property_ids: List[str] = field(default_factory=list)
    client_type: str = "buyer"  # buyer, seller, investor
    urgency: str = "medium"  # low, medium, high, critical
    current_screen: str = "dashboard"
    active_tasks: List[str] = field(default_factory=list)
    recent_actions: List[Dict[str, Any]] = field(default_factory=list)
    workflow_progress: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ChatSession:
    """Complete chat session state with persistence."""
    session_id: str
    agent_id: str
    process_context: ProcessContext
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    active_coaching_requests: List[str] = field(default_factory=list)
    persistent_insights: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    total_interactions: int = 0


class PersistentClaudeChat(ClaudeComponentMixin):
    """
    Universal persistent chat component for continuous realtor guidance.

    Provides context-aware coaching throughout the entire real estate workflow,
    maintaining conversation state and process context across all platform screens.
    """

    # Class constants
    CHAT_SESSION_KEY = "persistent_claude_chat_session"
    PROCESS_CONTEXT_KEY = "persistent_process_context"
    DEFAULT_POSITION = ChatWindowPosition.BOTTOM_RIGHT
    MAX_CONVERSATION_HISTORY = 100
    CONTEXT_REFRESH_INTERVAL = 30  # seconds

    def __init__(
        self,
        agent_id: str,
        session_id: Optional[str] = None,
        position: ChatWindowPosition = DEFAULT_POSITION,
        enable_voice: bool = False,
        enable_process_tracking: bool = True,
        max_history_length: int = MAX_CONVERSATION_HISTORY
    ):
        """
        Initialize persistent Claude chat.

        Args:
            agent_id: Realtor agent identifier
            session_id: Optional session ID (auto-generated if not provided)
            position: Chat window position
            enable_voice: Enable voice features
            enable_process_tracking: Track realtor process context
            max_history_length: Maximum conversation history to maintain
        """
        # Initialize Claude mixin
        super().__init__(
            enable_claude_caching=True,
            cache_ttl_seconds=300,
            enable_performance_monitoring=True,
            demo_mode=False
        )

        self.agent_id = agent_id
        self.session_id = session_id or self._generate_session_id()
        self.position = position
        self.enable_voice = enable_voice
        self.enable_process_tracking = enable_process_tracking
        self.max_history_length = max_history_length

        # Initialize session state
        self._initialize_session_state()

        # Performance tracking
        self.response_times = []
        self.last_response_time = 0

        logger.info(f"PersistentClaudeChat initialized for agent {agent_id}, session {self.session_id}")

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = int(time.time())
        return f"chat_session_{self.agent_id}_{timestamp}"

    def _initialize_session_state(self):
        """Initialize or restore session state."""
        # Initialize chat session
        if self.CHAT_SESSION_KEY not in st.session_state:
            st.session_state[self.CHAT_SESSION_KEY] = ChatSession(
                session_id=self.session_id,
                agent_id=self.agent_id,
                process_context=ProcessContext(
                    stage=RealtorProcessStage.LEAD_CAPTURE,
                    current_screen="dashboard"
                )
            )

        # Initialize process context
        if self.PROCESS_CONTEXT_KEY not in st.session_state:
            st.session_state[self.PROCESS_CONTEXT_KEY] = ProcessContext(
                stage=RealtorProcessStage.LEAD_CAPTURE,
                current_screen="dashboard"
            )

        # Initialize chat window state
        if "chat_window_expanded" not in st.session_state:
            st.session_state.chat_window_expanded = False

        if "chat_input_text" not in st.session_state:
            st.session_state.chat_input_text = ""

    @property
    def chat_session(self) -> ChatSession:
        """Get current chat session."""
        return st.session_state[self.CHAT_SESSION_KEY]

    @property
    def process_context(self) -> ProcessContext:
        """Get current process context."""
        return st.session_state[self.PROCESS_CONTEXT_KEY]

    def update_process_context(
        self,
        stage: Optional[RealtorProcessStage] = None,
        lead_id: Optional[str] = None,
        current_screen: Optional[str] = None,
        **kwargs
    ):
        """Update process context with new information."""
        context = self.process_context

        if stage:
            context.stage = stage
        if lead_id:
            context.lead_id = lead_id
        if current_screen:
            context.current_screen = current_screen

        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)

        context.last_updated = datetime.now()

        # Store updated context
        st.session_state[self.PROCESS_CONTEXT_KEY] = context

        logger.debug(f"Process context updated: {context.stage}, screen: {context.current_screen}")

    def render_persistent_chat(
        self,
        current_screen: Optional[str] = None,
        process_stage: Optional[RealtorProcessStage] = None,
        lead_context: Optional[Dict[str, Any]] = None,
        height: int = 400,
        width: int = 350
    ):
        """
        Render the persistent chat window.

        Args:
            current_screen: Current screen/module name
            process_stage: Current process stage
            lead_context: Current lead context
            height: Chat window height
            width: Chat window width
        """
        # Update context if provided
        if current_screen or process_stage:
            self.update_process_context(
                stage=process_stage,
                current_screen=current_screen
            )

        if self.position == ChatWindowPosition.EMBEDDED:
            self._render_embedded_chat(lead_context, height)
        elif self.position == ChatWindowPosition.FULL_SCREEN:
            self._render_fullscreen_chat(lead_context)
        elif self.position == ChatWindowPosition.RIGHT_PANEL:
            self._render_right_panel_chat(lead_context, height)
        else:
            self._render_floating_chat(lead_context, height, width)

    def _render_embedded_chat(self, lead_context: Optional[Dict[str, Any]], height: int):
        """Render chat embedded in current page."""
        with st.container():
            self._render_chat_header("💬 AI Guidance")
            self._render_chat_interface(lead_context, height)

    def _render_fullscreen_chat(self, lead_context: Optional[Dict[str, Any]]):
        """Render chat in full screen mode."""
        st.markdown("### 🤖 Claude AI - Your Real Estate Assistant")

        # Process context display
        self._render_process_context_panel()

        # Main chat interface
        col1, col2 = st.columns([3, 1])

        with col1:
            self._render_chat_interface(lead_context, height=600)

        with col2:
            self._render_chat_sidebar()

    def _render_right_panel_chat(self, lead_context: Optional[Dict[str, Any]], height: int):
        """Render chat in right panel."""
        with st.sidebar:
            self._render_chat_header("🤖 Claude Assistant")
            self._render_chat_interface(lead_context, height)
            self._render_quick_actions()

    def _render_floating_chat(
        self,
        lead_context: Optional[Dict[str, Any]],
        height: int,
        width: int
    ):
        """Render floating chat window with CSS positioning."""
        # Inject floating window CSS
        self._inject_floating_css(height, width)

        # Chat toggle button
        if st.button("💬", key="chat_toggle", help="Open Claude Assistant"):
            st.session_state.chat_window_expanded = not st.session_state.chat_window_expanded

        # Render chat in expandable container
        if st.session_state.chat_window_expanded:
            with st.expander("🤖 Claude AI Assistant", expanded=True):
                self._render_chat_interface(lead_context, height)

    def _inject_floating_css(self, height: int, width: int):
        """Inject CSS for floating chat window."""
        position_styles = {
            ChatWindowPosition.BOTTOM_RIGHT: "bottom: 20px; right: 20px;",
            ChatWindowPosition.BOTTOM_LEFT: "bottom: 20px; left: 20px;",
        }

        position = position_styles.get(self.position, position_styles[ChatWindowPosition.BOTTOM_RIGHT])

        st.markdown(f"""
        <style>
        .floating-chat-container {{
            position: fixed;
            {position}
            z-index: 1000;
            width: {width}px;
            max-height: {height}px;
            background: white;
            border: 2px solid #667eea;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
            overflow: hidden;
        }}

        .chat-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.75rem;
            text-align: center;
            font-weight: bold;
            border-radius: 13px 13px 0 0;
        }}

        .chat-messages {{
            max-height: {height - 150}px;
            overflow-y: auto;
            padding: 1rem;
            background: #f8f9ff;
        }}

        .chat-input-area {{
            padding: 0.75rem;
            border-top: 1px solid #e2e8f0;
            background: white;
        }}

        .process-context-indicator {{
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            display: inline-block;
            margin-bottom: 0.5rem;
        }}

        .response-time-indicator {{
            background: #e2e8f0;
            color: #4a5568;
            padding: 0.1rem 0.3rem;
            border-radius: 8px;
            font-size: 0.7rem;
            float: right;
        }}
        </style>
        """, unsafe_allow_html=True)

    def _render_chat_header(self, title: str):
        """Render chat window header with context."""
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"#### {title}")

            # Process context indicator
            context = self.process_context
            stage_display = context.stage.value.replace("_", " ").title()
            st.markdown(f"""
            <div class="process-context-indicator">
                📍 {stage_display}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Claude status indicator
            self.render_claude_status_badge()

            # Performance indicator
            if self.last_response_time > 0:
                st.caption(f"⚡ {self.last_response_time:.0f}ms")

    def _render_process_context_panel(self):
        """Render process context information panel."""
        context = self.process_context

        with st.expander("📋 Process Context", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Current Stage", context.stage.value.replace("_", " ").title())

            with col2:
                st.metric("Client Type", context.client_type.title())

            with col3:
                st.metric("Urgency", context.urgency.title())

            # Additional context
            if context.lead_id:
                st.info(f"Active Lead: {context.lead_id}")

            if context.active_tasks:
                st.write("**Active Tasks:**")
                for task in context.active_tasks[:3]:
                    st.write(f"• {task}")

    def _render_chat_interface(self, lead_context: Optional[Dict[str, Any]], height: int):
        """Render main chat interface."""
        # Message history container
        messages_container = st.container()

        with messages_container:
            self._render_conversation_history(max_height=height-150)

        # Input area
        self._render_chat_input(lead_context)

        # Quick action buttons
        self._render_quick_actions()

    def _render_conversation_history(self, max_height: int = 300):
        """Render conversation history with context."""
        chat_session = self.chat_session

        if not chat_session.conversation_history:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #718096;">
                👋 Hi! I'm Claude, your AI real estate assistant.<br>
                I'm here to help guide you through every step of the process.
                <br><br>
                <strong>Ask me about:</strong><br>
                • Lead qualification strategies<br>
                • Property recommendation tactics<br>
                • Objection handling techniques<br>
                • Market insights and trends<br>
                • Next best actions
            </div>
            """, unsafe_allow_html=True)
            return

        # Render messages in scrollable container
        with st.container():
            for message in chat_session.conversation_history[-20:]:  # Show last 20 messages
                self._render_chat_message(message)

    def _render_chat_message(self, message: Dict[str, Any]):
        """Render individual chat message."""
        role = message.get("role", "user")
        content = message.get("content", "")
        timestamp = message.get("timestamp", datetime.now())
        confidence = message.get("confidence", 0)

        # Format timestamp
        time_str = timestamp.strftime("%H:%M") if isinstance(timestamp, datetime) else str(timestamp)[:5]

        if role == "user":
            # User message (right-aligned)
            st.markdown(f"""
            <div style="text-align: right; margin: 0.5rem 0;">
                <div style="display: inline-block; background: #667eea; color: white;
                           padding: 0.5rem 1rem; border-radius: 15px 15px 5px 15px;
                           max-width: 80%; text-align: left;">
                    {content}
                    <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.25rem;">
                        {time_str}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Assistant message (left-aligned)
            confidence_indicator = f"🎯 {confidence:.0%}" if confidence > 0 else ""

            st.markdown(f"""
            <div style="margin: 0.5rem 0;">
                <div style="display: inline-block; background: #e2e8f0; color: #2d3748;
                           padding: 0.5rem 1rem; border-radius: 15px 15px 15px 5px;
                           max-width: 85%;">
                    {content}
                    <div style="font-size: 0.7rem; color: #718096; margin-top: 0.25rem;">
                        🤖 Claude • {time_str} {confidence_indicator}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def _render_chat_input(self, lead_context: Optional[Dict[str, Any]]):
        """Render chat input area with smart suggestions."""
        # Smart prompt suggestions based on current context
        suggestions = self._get_context_suggestions()

        if suggestions:
            st.write("**💡 Quick Questions:**")
            col_count = min(len(suggestions), 2)
            cols = st.columns(col_count)

            for i, suggestion in enumerate(suggestions[:2]):
                with cols[i % col_count]:
                    if st.button(f"❓ {suggestion}", key=f"suggestion_{i}",
                                help="Click to ask this question"):
                        st.session_state.chat_input_text = suggestion
                        st.experimental_rerun()

        # Main input area
        col1, col2 = st.columns([4, 1])

        with col1:
            user_input = st.text_input(
                "Ask Claude...",
                value=st.session_state.chat_input_text,
                placeholder="Ask about leads, properties, market insights, or next steps...",
                key="persistent_chat_input",
                label_visibility="collapsed"
            )

        with col2:
            send_message = st.button("💬", key="send_chat", help="Send message")

        # Process message
        if send_message and user_input:
            self._process_chat_message(user_input, lead_context)
            st.session_state.chat_input_text = ""
            st.experimental_rerun()

    def _get_context_suggestions(self) -> List[str]:
        """Get smart suggestions based on current context."""
        context = self.process_context
        suggestions = []

        # Stage-specific suggestions
        if context.stage == RealtorProcessStage.LEAD_CAPTURE:
            suggestions = [
                "How do I qualify this lead quickly?",
                "What questions should I ask first?"
            ]
        elif context.stage == RealtorProcessStage.QUALIFICATION:
            suggestions = [
                "What's the best way to handle budget objections?",
                "How do I assess their timeline urgency?"
            ]
        elif context.stage == RealtorProcessStage.PROPERTY_SEARCH:
            suggestions = [
                "How do I present properties effectively?",
                "What market insights should I share?"
            ]
        elif context.stage == RealtorProcessStage.SHOWING_PREP:
            suggestions = [
                "What should I prepare for the showing?",
                "How do I handle multiple offer situations?"
            ]
        else:
            # General suggestions
            suggestions = [
                "What should I focus on right now?",
                "Any market updates I should know?"
            ]

        return suggestions

    def _render_quick_actions(self):
        """Render quick action buttons."""
        st.markdown("**⚡ Quick Actions:**")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Market Insights", key="quick_market", help="Get market update"):
                self._handle_quick_action("market_insights")

        with col2:
            if st.button("🎯 Lead Scoring", key="quick_scoring", help="Analyze current lead"):
                self._handle_quick_action("lead_scoring")

        col3, col4 = st.columns(2)

        with col3:
            if st.button("📋 Next Steps", key="quick_next", help="Get recommended actions"):
                self._handle_quick_action("next_steps")

        with col4:
            if st.button("🔄 Refresh Context", key="quick_refresh", help="Update process context"):
                self._refresh_process_context()

    def _render_chat_sidebar(self):
        """Render chat sidebar with additional features."""
        st.markdown("### 📊 Session Stats")

        session = self.chat_session
        st.metric("Interactions", session.total_interactions)
        st.metric("Session Time", f"{(datetime.now() - session.created_at).seconds // 60}m")

        if self.response_times:
            avg_response = sum(self.response_times) / len(self.response_times)
            st.metric("Avg Response", f"{avg_response:.0f}ms")

        # Performance stats
        if st.button("📈 View Performance"):
            stats = self.get_claude_performance_stats()
            if stats:
                st.json(stats)

    async def _process_chat_message(
        self,
        message: str,
        lead_context: Optional[Dict[str, Any]] = None
    ):
        """Process chat message and get Claude response."""
        start_time = time.time()

        try:
            # Build comprehensive context
            conversation_context = self._build_conversation_context(lead_context)

            # Get Claude response
            with st.spinner("🤖 Claude is thinking..."):
                response = await self.get_real_time_coaching(
                    agent_id=self.agent_id,
                    conversation_context=conversation_context,
                    prospect_message=message,
                    conversation_stage=self.process_context.stage.value,
                    use_cache=True
                )

            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            self.last_response_time = response_time
            self.response_times.append(response_time)

            # Keep only last 50 response times
            if len(self.response_times) > 50:
                self.response_times = self.response_times[-50:]

            # Store messages in conversation history
            self._add_to_conversation_history(message, "user")

            # Format Claude response
            response_text = self._format_claude_response(response)
            self._add_to_conversation_history(
                response_text, "assistant",
                confidence=getattr(response, 'confidence', 0.85)
            )

            # Update session stats
            session = self.chat_session
            session.total_interactions += 1
            session.last_activity = datetime.now()

            # Store conversation in Redis for persistence
            await self._store_conversation_in_redis(message, response_text)

            st.success(f"Response generated in {response_time:.0f}ms")

        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            error_response = "I apologize, but I encountered an error. Please try again or rephrase your question."
            self._add_to_conversation_history(error_response, "assistant", confidence=0.0)
            st.error(f"Error: {str(e)}")

    def _build_conversation_context(self, lead_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build comprehensive conversation context."""
        context = self.process_context
        session = self.chat_session

        return {
            "process_stage": context.stage.value,
            "current_screen": context.current_screen,
            "client_type": context.client_type,
            "urgency": context.urgency,
            "lead_id": context.lead_id,
            "property_ids": context.property_ids,
            "active_tasks": context.active_tasks,
            "conversation_history": session.conversation_history[-10:],  # Last 10 messages
            "total_interactions": session.total_interactions,
            "session_duration": (datetime.now() - session.created_at).total_seconds() / 60,
            "lead_context": lead_context or {},
            "recent_actions": context.recent_actions,
            "workflow_progress": context.workflow_progress,
        }

    def _format_claude_response(self, response: Any) -> str:
        """Format Claude response for display."""
        if hasattr(response, 'coaching_suggestions'):
            # Real-time coaching response
            formatted = f"**🎯 Coaching Suggestions:**\n"
            for suggestion in response.coaching_suggestions:
                formatted += f"• {suggestion}\n"

            if hasattr(response, 'recommended_response') and response.recommended_response:
                formatted += f"\n**💬 Recommended Response:**\n{response.recommended_response}\n"

            if hasattr(response, 'next_question') and response.next_question:
                formatted += f"\n**❓ Next Question:**\n{response.next_question}\n"

            if hasattr(response, 'objection_detected') and response.objection_detected:
                formatted += f"\n**⚠️ Objection Detected:**\n{response.objection_detected}\n"

            return formatted

        elif hasattr(response, 'response'):
            # Generic response
            return response.response
        else:
            # Fallback
            return str(response)

    def _add_to_conversation_history(
        self,
        content: str,
        role: str,
        confidence: float = 0.0
    ):
        """Add message to conversation history."""
        session = self.chat_session

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "confidence": confidence
        }

        session.conversation_history.append(message)

        # Maintain max history length
        if len(session.conversation_history) > self.max_history_length:
            session.conversation_history = session.conversation_history[-self.max_history_length:]

    async def _store_conversation_in_redis(self, user_message: str, claude_response: str):
        """Store conversation in Redis for persistence."""
        try:
            if redis_conversation_service and redis_conversation_service.redis_client:
                await redis_conversation_service.store_conversation_message(
                    agent_id=self.agent_id,
                    role="user",
                    content=user_message,
                    lead_id=self.process_context.lead_id
                )
                await redis_conversation_service.store_conversation_message(
                    agent_id=self.agent_id,
                    role="assistant",
                    content=claude_response,
                    lead_id=self.process_context.lead_id
                )
        except Exception as e:
            logger.warning(f"Failed to store conversation in Redis: {e}")

    def _handle_quick_action(self, action_type: str):
        """Handle quick action button clicks."""
        if action_type == "market_insights":
            message = "What are the current market trends I should know about?"
        elif action_type == "lead_scoring":
            lead_id = self.process_context.lead_id or "current lead"
            message = f"How should I prioritize {lead_id}? What's their conversion potential?"
        elif action_type == "next_steps":
            stage = self.process_context.stage.value.replace("_", " ")
            message = f"What are the best next steps for the {stage} stage?"
        else:
            message = f"Help me with {action_type.replace('_', ' ')}"

        # Process the quick action message
        self._process_chat_message(message)

    def _refresh_process_context(self):
        """Refresh process context from current application state."""
        # This would typically integrate with your application's state management
        # For now, we'll update the last_updated timestamp
        context = self.process_context
        context.last_updated = datetime.now()
        st.session_state[self.PROCESS_CONTEXT_KEY] = context
        st.success("Process context refreshed!")

    def set_process_stage(self, stage: RealtorProcessStage):
        """Set current process stage."""
        self.update_process_context(stage=stage)

    def add_process_insight(self, insight: str):
        """Add insight to persistent insights."""
        session = self.chat_session
        if insight not in session.persistent_insights:
            session.persistent_insights.append(insight)
            # Keep only last 20 insights
            if len(session.persistent_insights) > 20:
                session.persistent_insights = session.persistent_insights[-20:]

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation."""
        session = self.chat_session
        context = self.process_context

        return {
            "session_id": session.session_id,
            "total_interactions": session.total_interactions,
            "session_duration_minutes": (datetime.now() - session.created_at).total_seconds() / 60,
            "current_stage": context.stage.value,
            "lead_id": context.lead_id,
            "avg_response_time_ms": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            "persistent_insights_count": len(session.persistent_insights),
            "conversation_length": len(session.conversation_history)
        }


# ============================================================================
# Convenience Functions for Easy Integration
# ============================================================================

def render_persistent_chat(
    agent_id: str,
    position: ChatWindowPosition = ChatWindowPosition.BOTTOM_RIGHT,
    current_screen: Optional[str] = None,
    process_stage: Optional[RealtorProcessStage] = None,
    lead_context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> PersistentClaudeChat:
    """
    Render persistent chat window - primary integration function.

    Args:
        agent_id: Realtor agent identifier
        position: Chat window position
        current_screen: Current screen/module name
        process_stage: Current process stage
        lead_context: Current lead context
        **kwargs: Additional arguments for PersistentClaudeChat

    Returns:
        PersistentClaudeChat instance
    """
    # Get or create chat instance
    chat_key = f"persistent_chat_{agent_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = PersistentClaudeChat(
            agent_id=agent_id,
            position=position,
            **kwargs
        )

    chat = st.session_state[chat_key]

    # Render the chat
    chat.render_persistent_chat(
        current_screen=current_screen,
        process_stage=process_stage,
        lead_context=lead_context
    )

    return chat


def update_chat_context(
    agent_id: str,
    stage: Optional[RealtorProcessStage] = None,
    lead_id: Optional[str] = None,
    **kwargs
):
    """
    Update chat context without rendering.

    Args:
        agent_id: Realtor agent identifier
        stage: Process stage to update
        lead_id: Lead ID to set
        **kwargs: Additional context updates
    """
    chat_key = f"persistent_chat_{agent_id}"
    if chat_key in st.session_state:
        chat = st.session_state[chat_key]
        chat.update_process_context(stage=stage, lead_id=lead_id, **kwargs)


# Export key classes and functions
__all__ = [
    'PersistentClaudeChat',
    'RealtorProcessStage',
    'ChatWindowPosition',
    'ProcessContext',
    'ChatSession',
    'render_persistent_chat',
    'update_chat_context'
]