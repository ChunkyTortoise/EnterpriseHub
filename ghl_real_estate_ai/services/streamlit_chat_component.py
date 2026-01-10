"""
Streamlit Chat Component Integration

Easy-to-use component for adding chatbot functionality to the Streamlit demo app.
Provides drop-in chat interfaces for leads, buyers, and sellers with full session tracking.
"""

import streamlit as st
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import our chat system components
from .chatbot_manager import ChatbotManager, UserType
from .session_manager import SessionManager
from .chat_interface import ChatInterface
from .chat_ml_integration import ChatMLIntegration

@st.cache_resource
def initialize_chat_system(tenant_id: str = "streamlit_demo") -> ChatInterface:
    """Initialize and cache the chat system"""
    try:
        # Initialize core components
        session_manager = SessionManager(
            storage_path="./session_data",
            session_timeout_hours=24 * 7  # 7 days
        )

        chatbot_manager = ChatbotManager()

        # Try to initialize ML components (gracefully handle if not available)
        ml_integration = None
        try:
            from services.learning.tracking.behavior_tracker import InMemoryBehaviorTracker
            from services.learning.feature_engineering.standard_feature_engineer import StandardFeatureEngineer

            behavior_tracker = InMemoryBehaviorTracker()
            feature_engineer = StandardFeatureEngineer(behavior_tracker)

            ml_integration = ChatMLIntegration(
                chatbot_manager, session_manager,
                behavior_tracker, feature_engineer, None
            )

            st.success("🧠 ML-enhanced chat system loaded")

        except ImportError:
            st.info("💬 Basic chat system loaded (ML features unavailable)")
            ml_integration = ChatMLIntegration(chatbot_manager, session_manager)

        # Create chat interface
        chat_interface = ChatInterface(chatbot_manager, session_manager, tenant_id)

        # Store ML integration in the interface for access
        chat_interface.ml_integration = ml_integration

        return chat_interface

    except Exception as e:
        st.error(f"Failed to initialize chat system: {str(e)}")
        # Return a minimal fallback
        return None

def render_chat_demo():
    """Render comprehensive chat demo"""
    st.subheader("🤖 AI Chat System Demo")
    st.markdown("*Experience our intelligent chatbot for real estate leads, buyers, and sellers*")

    # Initialize chat system
    chat_interface = initialize_chat_system()
    if not chat_interface:
        st.error("Chat system initialization failed")
        return

    # Chat persona selection
    persona = st.selectbox(
        "Select Demo Persona:",
        ["🏠 Lead (Initial Inquiry)", "🏡 Buyer (Property Search)", "💰 Seller (Property Valuation)"],
        help="Choose which type of user interaction to demonstrate"
    )

    # Map persona to user type
    user_type_map = {
        "🏠 Lead (Initial Inquiry)": "lead",
        "🏡 Buyer (Property Search)": "buyer",
        "💰 Seller (Property Valuation)": "seller"
    }

    user_type = user_type_map[persona]

    # Render appropriate chat interface
    try:
        asyncio.run(chat_interface.render_demo_chat(
            demo_persona=user_type,
            include_ml_insights=True
        ))

    except Exception as e:
        st.error(f"Chat demo failed: {str(e)}")
        st.info("Please try refreshing the page")

def render_lead_chat(user_id: Optional[str] = None):
    """Render lead qualification chat"""
    chat_interface = initialize_chat_system()
    if not chat_interface:
        return

    try:
        asyncio.run(chat_interface.render_lead_chat(
            user_id=user_id or f"lead_{uuid.uuid4().hex[:8]}",
            show_insights=True
        ))
    except Exception as e:
        st.error(f"Lead chat failed: {str(e)}")

def render_buyer_chat(user_id: Optional[str] = None):
    """Render buyer assistance chat"""
    chat_interface = initialize_chat_system()
    if not chat_interface:
        return

    try:
        asyncio.run(chat_interface.render_buyer_chat(
            user_id=user_id or f"buyer_{uuid.uuid4().hex[:8]}",
            show_property_suggestions=True
        ))
    except Exception as e:
        st.error(f"Buyer chat failed: {str(e)}")

def render_seller_chat(user_id: Optional[str] = None):
    """Render seller consultation chat"""
    chat_interface = initialize_chat_system()
    if not chat_interface:
        return

    try:
        asyncio.run(chat_interface.render_seller_chat(
            user_id=user_id or f"seller_{uuid.uuid4().hex[:8]}",
            show_valuation=True
        ))
    except Exception as e:
        st.error(f"Seller chat failed: {str(e)}")

def render_chat_analytics():
    """Render chat system analytics"""
    st.subheader("📊 Chat System Analytics")

    chat_interface = initialize_chat_system()
    if not chat_interface:
        return

    try:
        # Get session analytics
        analytics = asyncio.run(chat_interface.get_session_analytics())

        if analytics:
            # Session statistics
            session_stats = analytics.get("session_stats", {})

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Sessions", session_stats.get("total_sessions", 0))

            with col2:
                st.metric("Active Sessions", session_stats.get("active_sessions", 0))

            with col3:
                avg_messages = session_stats.get("average_message_count", 0)
                st.metric("Avg Messages/Session", f"{avg_messages:.1f}")

            with col4:
                st.metric("Active Conversations", analytics.get("active_conversations", 0))

            # User type breakdown
            if "user_types" in session_stats:
                st.subheader("User Type Distribution")
                user_types = session_stats["user_types"]

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Leads", user_types.get("lead", 0))
                with col2:
                    st.metric("Buyers", user_types.get("buyer", 0))
                with col3:
                    st.metric("Sellers", user_types.get("seller", 0))

            # Conversation stages
            if "session_stages" in session_stats:
                st.subheader("Conversation Stages")
                stages = session_stats["session_stages"]

                for stage, count in stages.items():
                    st.metric(stage.replace("_", " ").title(), count)

            # Recent conversations
            recent_conversations = analytics.get("conversation_details", [])
            if recent_conversations:
                st.subheader("Recent Conversations")

                for conv in recent_conversations[:5]:
                    with st.expander(f"{conv['user_type'].title()} - {conv['user_id'][:12]}..."):
                        st.json(conv)

        else:
            st.info("No chat analytics available yet. Start some conversations to see data here.")

    except Exception as e:
        st.error(f"Analytics failed: {str(e)}")

def render_admin_chat_controls():
    """Render admin controls for chat system"""
    st.subheader("⚙️ Chat System Administration")

    chat_interface = initialize_chat_system()
    if not chat_interface:
        return

    tab1, tab2, tab3 = st.tabs(["🔧 System Status", "📊 Analytics", "🧹 Maintenance"])

    with tab1:
        st.markdown("**System Status**")

        # Check ML integration status
        if hasattr(chat_interface, 'ml_integration') and chat_interface.ml_integration:
            status = chat_interface.ml_integration.get_integration_status()

            if status["ml_enabled"]:
                st.success("🧠 ML Integration: Active")
            else:
                st.info("💬 ML Integration: Basic Mode")

            # Component status
            components = status.get("components", {})
            col1, col2, col3 = st.columns(3)

            with col1:
                status_icon = "✅" if components.get("behavior_tracker") else "❌"
                st.markdown(f"{status_icon} Behavior Tracker")

            with col2:
                status_icon = "✅" if components.get("feature_engineer") else "❌"
                st.markdown(f"{status_icon} Feature Engineer")

            with col3:
                status_icon = "✅" if components.get("personalization_engine") else "❌"
                st.markdown(f"{status_icon} Personalization Engine")

        # Session manager status
        try:
            tenant_stats = chat_interface.session_manager.get_session_stats("streamlit_demo")
            st.metric("Session Storage", f"{tenant_stats['storage_path']}")
            st.metric("Last Cleanup", tenant_stats.get('last_cleanup', 'Unknown'))
        except:
            st.warning("Session manager status unavailable")

    with tab2:
        render_chat_analytics()

    with tab3:
        st.markdown("**Maintenance Operations**")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🧹 Cleanup Expired Sessions", help="Remove old session data"):
                try:
                    cleaned = asyncio.run(
                        chat_interface.session_manager.cleanup_expired_sessions()
                    )
                    st.success(f"Cleaned {cleaned} expired sessions")
                except Exception as e:
                    st.error(f"Cleanup failed: {str(e)}")

        with col2:
            if st.button("📊 Export Session Data", help="Export conversation data"):
                try:
                    export_data = asyncio.run(
                        chat_interface.chatbot_manager.export_conversation_data("streamlit_demo")
                    )
                    st.download_button(
                        "💾 Download Export",
                        data=str(export_data),
                        file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")

# Helper functions for integration with existing Streamlit app

def add_chat_to_page(page_title: str, user_type: str = "lead"):
    """Add chat functionality to any Streamlit page"""
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**💬 AI Assistant**")

        if st.button("Start Chat", key=f"chat_{page_title}"):
            if user_type == "lead":
                render_lead_chat()
            elif user_type == "buyer":
                render_buyer_chat()
            elif user_type == "seller":
                render_seller_chat()

def render_mini_chat(height: int = 400):
    """Render a compact chat interface"""
    with st.container():
        st.markdown("**Quick Chat**")

        # Mini chat implementation
        if "mini_chat_messages" not in st.session_state:
            st.session_state.mini_chat_messages = [
                {"role": "assistant", "content": "Hi! How can I help you today?"}
            ]

        # Display messages in a container with limited height
        with st.container():
            for msg in st.session_state.mini_chat_messages[-5:]:  # Show last 5 messages
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Chat input
        if prompt := st.chat_input("Ask me anything..."):
            st.session_state.mini_chat_messages.append(
                {"role": "user", "content": prompt}
            )

            # Simple response (could be enhanced with full chat system)
            response = "Thanks for your message! This is a demo response. Use the full chat interface for comprehensive assistance."

            st.session_state.mini_chat_messages.append(
                {"role": "assistant", "content": response}
            )

            st.rerun()