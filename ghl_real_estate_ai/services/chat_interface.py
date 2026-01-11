"""
Specialized Chat Interfaces for Real Estate AI Platform

Streamlit-compatible chat interfaces for leads, buyers, and sellers with
ML integration, session persistence, and tenant-specific customization.
"""

import asyncio
import streamlit as st
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging

from .chatbot_manager import ChatbotManager, UserType, ConversationStage, MessageType
from .session_manager import SessionManager
from services.learning.interfaces import LearningContext

logger = logging.getLogger(__name__)


class ChatInterface:
    """
    Unified chat interface for Streamlit with ML integration.

    Features:
    - User type-specific chat experiences
    - Cross-session conversation persistence
    - Real-time ML insights and recommendations
    - Tenant-specific customization
    - Performance monitoring and analytics
    """

    def __init__(
        self,
        chatbot_manager: ChatbotManager,
        session_manager: SessionManager,
        tenant_id: str = "default"
    ):
        """Initialize chat interface"""
        self.chatbot_manager = chatbot_manager
        self.session_manager = session_manager
        self.tenant_id = tenant_id

        # Initialize session state keys
        self._init_session_state()

    def _init_session_state(self):
        """Initialize Streamlit session state for chat"""
        if 'chat_session_id' not in st.session_state:
            st.session_state.chat_session_id = str(uuid.uuid4())

        if 'chat_user_id' not in st.session_state:
            st.session_state.chat_user_id = None

        if 'chat_user_type' not in st.session_state:
            st.session_state.chat_user_type = None

        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []

        if 'chat_context' not in st.session_state:
            st.session_state.chat_context = {}

        if 'chat_insights' not in st.session_state:
            st.session_state.chat_insights = {}

    async def render_lead_chat(
        self,
        user_id: Optional[str] = None,
        initial_message: Optional[str] = None,
        show_insights: bool = True
    ) -> None:
        """Render chat interface optimized for leads"""

        st.subheader("🏠 Lead Qualification Chat")
        st.markdown("*AI-powered conversation to understand your property needs*")

        # Setup user session
        if not user_id:
            user_id = f"lead_{uuid.uuid4().hex[:8]}"

        await self._setup_chat_session(user_id, UserType.LEAD)

        # Render chat interface
        col1, col2 = st.columns([2, 1])

        with col1:
            await self._render_chat_messages()
            await self._handle_chat_input()

        with col2:
            if show_insights:
                await self._render_lead_insights()

    async def render_buyer_chat(
        self,
        user_id: Optional[str] = None,
        show_property_suggestions: bool = True
    ) -> None:
        """Render chat interface optimized for buyers"""

        st.subheader("🏡 Buyer Assistance Chat")
        st.markdown("*Personalized property recommendations and scheduling*")

        # Setup user session
        if not user_id:
            user_id = f"buyer_{uuid.uuid4().hex[:8]}"

        await self._setup_chat_session(user_id, UserType.BUYER)

        # Render interface with property suggestions
        if show_property_suggestions:
            col1, col2 = st.columns([3, 2])
        else:
            col1, col2 = st.columns([1, 0])

        with col1:
            await self._render_chat_messages()
            await self._handle_chat_input()

        if show_property_suggestions and col2:
            with col2:
                await self._render_property_suggestions()

    async def render_seller_chat(
        self,
        user_id: Optional[str] = None,
        show_valuation: bool = True
    ) -> None:
        """Render chat interface optimized for sellers"""

        st.subheader("💰 Seller Consultation Chat")
        st.markdown("*Property valuation and listing strategy discussion*")

        # Setup user session
        if not user_id:
            user_id = f"seller_{uuid.uuid4().hex[:8]}"

        await self._setup_chat_session(user_id, UserType.SELLER)

        # Render interface
        col1, col2 = st.columns([2, 1])

        with col1:
            await self._render_chat_messages()
            await self._handle_chat_input()

        with col2:
            if show_valuation:
                await self._render_valuation_tools()

    async def render_demo_chat(
        self,
        demo_persona: str = "lead",
        include_ml_insights: bool = True
    ) -> None:
        """Render demo chat interface for showcasing capabilities"""

        # Map demo persona to user type
        user_type_map = {
            "lead": UserType.LEAD,
            "buyer": UserType.BUYER,
            "seller": UserType.SELLER
        }

        user_type = user_type_map.get(demo_persona.lower(), UserType.LEAD)
        user_id = f"demo_{demo_persona}_{uuid.uuid4().hex[:8]}"

        st.subheader(f"🤖 {demo_persona.title()} AI Chat Demo")
        st.markdown(f"*Experience our AI assistant from a {demo_persona}'s perspective*")

        await self._setup_chat_session(user_id, user_type)

        # Render demo interface
        tab1, tab2 = st.tabs(["💬 Chat", "📊 AI Insights"])

        with tab1:
            await self._render_chat_messages()
            await self._handle_chat_input()

        with tab2:
            if include_ml_insights:
                await self._render_ml_insights()

    # Core interface methods

    async def _setup_chat_session(self, user_id: str, user_type: UserType):
        """Setup chat session for user"""

        st.session_state.chat_user_id = user_id
        st.session_state.chat_user_type = user_type

        # Get or create session
        session = await self.session_manager.get_user_session(user_id, self.tenant_id)

        if not session:
            device_info = {
                "platform": "streamlit",
                "browser": "web",
                "timestamp": datetime.now().isoformat()
            }

            session = await self.session_manager.create_session(
                user_id=user_id,
                tenant_id=self.tenant_id,
                user_type=user_type.value,
                device_info=device_info
            )

            st.session_state.chat_session_id = session.session_id

        # Load conversation history
        messages = await self.chatbot_manager.get_conversation_history(
            user_id, self.tenant_id
        )

        # Convert to Streamlit format
        st.session_state.chat_messages = [
            {
                "role": "assistant" if msg.message_type == MessageType.ASSISTANT_MESSAGE else "user",
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            }
            for msg in messages
        ]

        # Add welcome message if no history
        if not st.session_state.chat_messages:
            welcome_msg = self._get_welcome_message(user_type)
            st.session_state.chat_messages = [
                {"role": "assistant", "content": welcome_msg, "timestamp": datetime.now().isoformat(), "metadata": {}}
            ]

    async def _render_chat_messages(self):
        """Render chat message history"""
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Show message metadata if in demo mode
                if "metadata" in message and message["metadata"]:
                    with st.expander("🔍 Message Details", expanded=False):
                        st.json(message["metadata"])

    async def _handle_chat_input(self):
        """Handle new chat input"""
        if prompt := st.chat_input("Type your message..."):
            # Add user message to chat
            user_msg = {
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().isoformat(),
                "metadata": {}
            }
            st.session_state.chat_messages.append(user_msg)

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner("AI is thinking..."):
                    try:
                        response_content, response_metadata = await self.chatbot_manager.process_message(
                            user_id=st.session_state.chat_user_id,
                            tenant_id=self.tenant_id,
                            message_content=prompt,
                            session_id=st.session_state.chat_session_id,
                            user_type=st.session_state.chat_user_type
                        )

                        # Display response
                        st.markdown(response_content)

                        # Add to message history
                        assistant_msg = {
                            "role": "assistant",
                            "content": response_content,
                            "timestamp": datetime.now().isoformat(),
                            "metadata": response_metadata
                        }
                        st.session_state.chat_messages.append(assistant_msg)

                        # Update session activity
                        await self.session_manager.update_session_activity(
                            st.session_state.chat_session_id,
                            {
                                "message_count": len(st.session_state.chat_messages),
                                "last_response": response_content[:100],
                                "entities_detected": response_metadata.get("entities_detected", [])
                            }
                        )

                        # Show AI thinking process in demo mode
                        if response_metadata:
                            with st.expander("🧠 AI Analysis", expanded=False):
                                st.json(response_metadata)

                    except Exception as e:
                        st.error(f"Error generating response: {str(e)}")

    async def _render_lead_insights(self):
        """Render lead-specific insights sidebar"""
        st.subheader("📊 Lead Insights")

        if st.session_state.chat_user_id:
            try:
                insights = await self.chatbot_manager.get_user_insights(
                    st.session_state.chat_user_id,
                    self.tenant_id
                )

                if insights:
                    # Lead scoring
                    lead_score = insights.get("lead_scoring", {}).get("lead_score", 0)
                    st.metric("Lead Score", f"{lead_score:.0f}/100")

                    # Conversation progress
                    stage = insights.get("conversation_summary", {}).get("current_stage", "unknown")
                    st.metric("Conversation Stage", stage.replace("_", " ").title())

                    # Message count
                    msg_count = insights.get("conversation_summary", {}).get("total_messages", 0)
                    st.metric("Messages Exchanged", msg_count)

                    # Behavioral factors
                    if "behavioral_insights" in insights:
                        with st.expander("🧠 Behavioral Analysis"):
                            st.json(insights["behavioral_insights"])

            except Exception as e:
                st.error(f"Failed to load insights: {str(e)}")

    async def _render_property_suggestions(self):
        """Render property suggestions for buyers"""
        st.subheader("🏠 Property Suggestions")

        if st.session_state.chat_user_id:
            try:
                # Get ML-powered property recommendations
                if self.chatbot_manager.personalization_engine:
                    recommendations = await self.chatbot_manager.personalization_engine.get_recommendations(
                        entity_id=st.session_state.chat_user_id,
                        entity_type="buyer",
                        max_results=3
                    )

                    if recommendations:
                        for i, rec in enumerate(recommendations):
                            with st.container():
                                st.markdown(f"**Property {i+1}**")
                                st.markdown(f"Score: {rec.predicted_value:.2f}")
                                st.markdown(f"Confidence: {rec.confidence:.1%}")

                                if st.button(f"View Details", key=f"prop_{i}"):
                                    st.balloons()
                                    st.success("Property details opened!")
                    else:
                        st.info("Gathering preferences to suggest properties...")
                else:
                    # Fallback mock suggestions
                    st.info("Mock properties based on conversation:")
                    st.markdown("• **$450K Condo** - Downtown, 2BR/2BA")
                    st.markdown("• **$520K Townhome** - Suburbs, 3BR/2.5BA")
                    st.markdown("• **$380K Starter Home** - Near schools, 2BR/1BA")

            except Exception as e:
                st.warning(f"Property suggestions temporarily unavailable")

    async def _render_valuation_tools(self):
        """Render valuation tools for sellers"""
        st.subheader("💰 Property Valuation")

        # Mock valuation based on conversation
        if st.button("Generate Quick Estimate"):
            with st.spinner("Analyzing market data..."):
                # Simulate valuation calculation
                import time
                time.sleep(1)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Estimated Value", "$650,000")
                    st.metric("Price Range", "$620K - $680K")

                with col2:
                    st.metric("Market Trend", "📈 Rising")
                    st.metric("Days on Market", "12-18 days")

        st.markdown("---")
        st.markdown("**Next Steps:**")
        st.markdown("• Schedule home evaluation")
        st.markdown("• Review comparable sales")
        st.markdown("• Discuss listing strategy")

    async def _render_ml_insights(self):
        """Render comprehensive ML insights for demo"""
        st.subheader("🤖 AI Analysis Dashboard")

        if st.session_state.chat_user_id:
            try:
                insights = await self.chatbot_manager.get_user_insights(
                    st.session_state.chat_user_id,
                    self.tenant_id
                )

                if insights:
                    # Conversation metrics
                    conv_summary = insights.get("conversation_summary", {})

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Messages", conv_summary.get("total_messages", 0))
                    with col2:
                        st.metric("Duration", f"{conv_summary.get('conversation_duration', 0):.1f}h")
                    with col3:
                        st.metric("Sessions", conv_summary.get("session_count", 1))

                    # Lead scoring breakdown
                    scoring = insights.get("lead_scoring", {})
                    if scoring:
                        st.markdown("**Lead Scoring:**")
                        score = scoring.get("lead_score", 0)
                        prob = scoring.get("conversion_probability", 0)

                        st.progress(score / 100)
                        st.markdown(f"Lead Score: {score:.0f}/100")
                        st.markdown(f"Conversion Probability: {prob:.1%}")

                    # ML insights
                    if "ml_insights" in insights:
                        st.markdown("**ML Analysis:**")
                        ml_data = insights["ml_insights"]

                        st.markdown(f"• Features Extracted: {ml_data.get('feature_count', 0)}")
                        st.markdown(f"• Recommendations Available: {ml_data.get('recommendations_available', 0)}")
                        st.markdown(f"• Personalization Confidence: {ml_data.get('personalization_confidence', 0):.1%}")

            except Exception as e:
                st.error(f"ML insights temporarily unavailable: {str(e)}")

    def _get_welcome_message(self, user_type: UserType) -> str:
        """Get appropriate welcome message for user type"""
        messages = {
            UserType.LEAD: "Hi! I'm here to help you explore your real estate options. What brings you here today?",
            UserType.BUYER: "Welcome! I'm excited to help you find your perfect home. Let's start by understanding what you're looking for.",
            UserType.SELLER: "Hello! I understand you're considering selling your property. I'd love to help you get the best value. Let's start with some basic information about your home."
        }

        return messages.get(user_type, "Hi! How can I help you with your real estate needs today?")

    # Utility methods

    def clear_conversation(self):
        """Clear current conversation"""
        st.session_state.chat_messages = []
        if hasattr(st.session_state, 'chat_context'):
            st.session_state.chat_context = {}

    def export_conversation(self) -> Dict[str, Any]:
        """Export conversation data"""
        return {
            "user_id": st.session_state.get("chat_user_id"),
            "session_id": st.session_state.get("chat_session_id"),
            "user_type": st.session_state.get("chat_user_type"),
            "messages": st.session_state.get("chat_messages", []),
            "export_timestamp": datetime.now().isoformat()
        }

    async def get_session_analytics(self) -> Dict[str, Any]:
        """Get session analytics for current tenant"""
        try:
            stats = self.session_manager.get_session_stats(self.tenant_id)
            active_conversations = self.chatbot_manager.get_active_conversations(self.tenant_id)

            return {
                "session_stats": stats,
                "active_conversations": len(active_conversations),
                "conversation_details": active_conversations[:10]  # Top 10
            }
        except Exception as e:
            logger.error(f"Failed to get session analytics: {str(e)}")
            return {}


# Helper functions for Streamlit integration

def create_chat_interface(
    tenant_id: str = "default",
    enable_ml: bool = True
) -> ChatInterface:
    """Create chat interface with ML integration"""

    # Initialize components
    if enable_ml:
        try:
            # Import ML components
            from services.learning.tracking.behavior_tracker import InMemoryBehaviorTracker
            from services.learning.feature_engineering.standard_feature_engineer import StandardFeatureEngineer
            from services.learning.personalization.property_engine import PropertyPersonalizationEngine

            # Initialize ML pipeline
            tracker = InMemoryBehaviorTracker()
            feature_engineer = StandardFeatureEngineer(tracker)

            # Note: In production, you'd load trained models
            personalization_engine = None  # Would initialize with trained models

            chatbot_manager = ChatbotManager(tracker, feature_engineer, personalization_engine)

        except ImportError:
            # Fallback without ML integration
            chatbot_manager = ChatbotManager()

    else:
        chatbot_manager = ChatbotManager()

    session_manager = SessionManager()

    return ChatInterface(chatbot_manager, session_manager, tenant_id)

async def render_chat_demo(chat_type: str = "lead"):
    """Render quick chat demo"""
    interface = create_chat_interface()
    await interface.render_demo_chat(chat_type, include_ml_insights=True)