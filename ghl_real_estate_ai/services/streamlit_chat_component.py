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

# Import async utilities for safe execution
from ..utils.async_utils import safe_run_async, handle_streamlit_async_error

# Import our chat system components (with fallback handling)
try:
    from .chatbot_manager import ChatbotManager, UserType
    from .session_manager import SessionManager
    from .chat_interface import ChatInterface
    from .chat_ml_integration import ChatMLIntegration
    CHAT_COMPONENTS_AVAILABLE = True
except ImportError as e:
    st.warning(f"Chat system components not available: {e}")
    CHAT_COMPONENTS_AVAILABLE = False
    # Create placeholder classes to prevent runtime errors
    class ChatbotManager: pass
    class SessionManager: pass
    class ChatInterface: pass
    class ChatMLIntegration: pass
    class UserType: pass

@st.cache_resource
def initialize_chat_system(tenant_id: str = "streamlit_demo") -> ChatInterface:
    """Initialize and cache the chat system"""
    if not CHAT_COMPONENTS_AVAILABLE:
        st.error("Chat system components are not available")
        return None

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

        except ImportError as import_error:
            st.info("💬 Basic chat system loaded (ML features unavailable)")
            try:
                ml_integration = ChatMLIntegration(chatbot_manager, session_manager)
            except Exception as ml_error:
                st.warning(f"ML integration unavailable: {ml_error}")
                ml_integration = None

        # Create chat interface
        chat_interface = ChatInterface(chatbot_manager, session_manager, tenant_id)

        # Store ML integration in the interface for access
        if ml_integration:
            chat_interface.ml_integration = ml_integration

        return chat_interface

    except Exception as e:
        st.error(f"Failed to initialize chat system: {str(e)}")
        st.info("💡 Try refreshing the page to resolve initialization issues")
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
        safe_run_async(chat_interface.render_demo_chat(
            demo_persona=user_type,
            include_ml_insights=True
        ))

    except Exception as e:
        handle_streamlit_async_error(e, "chat demo rendering")

def render_lead_chat(user_id: Optional[str] = None):
    """Render lead qualification chat"""
    chat_interface = initialize_chat_system()
    if not chat_interface:
        return

    try:
        safe_run_async(chat_interface.render_lead_chat(
            user_id=user_id or f"lead_{uuid.uuid4().hex[:8]}",
            show_insights=True
        ))
    except Exception as e:
        handle_streamlit_async_error(e, "lead chat")

def render_buyer_chat(user_id: Optional[str] = None):
    """Render buyer assistance chat"""
    chat_interface = initialize_chat_system()
    if not chat_interface:
        return

    try:
        safe_run_async(chat_interface.render_buyer_chat(
            user_id=user_id or f"buyer_{uuid.uuid4().hex[:8]}",
            show_property_suggestions=True
        ))
    except Exception as e:
        handle_streamlit_async_error(e, "buyer chat")

def render_seller_chat(user_id: Optional[str] = None):
    """Render seller consultation chat"""
    chat_interface = initialize_chat_system()
    if not chat_interface:
        render_fallback_seller_chat()
        return

    try:
        safe_run_async(chat_interface.render_seller_chat(
            user_id=user_id or f"seller_{uuid.uuid4().hex[:8]}",
            show_valuation=True
        ))
    except Exception as e:
        handle_streamlit_async_error(e, "seller chat")
        render_fallback_seller_chat()

def render_fallback_seller_chat():
    """Render a simple fallback chat interface for sellers"""
    st.markdown("### 🏡 Seller AI Assistant")
    st.info("""
    **Welcome to the Seller AI Assistant!**

    The advanced chat system is currently initializing. Here's what this assistant helps with:

    🔍 **Property Valuation**
    - Market analysis and pricing recommendations
    - Comparative market analysis (CMA)
    - Property enhancement suggestions

    📈 **Marketing Strategy**
    - Professional listing optimization
    - Photography and staging advice
    - Target buyer identification

    ⏰ **Timing & Market Insights**
    - Best time to list analysis
    - Market trend insights
    - Seasonal considerations

    💰 **Financial Planning**
    - Cost estimation for improvements
    - Net proceeds calculations
    - Tax implications guidance
    """)

    st.markdown("---")
    st.markdown("**Quick Actions:**")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Get Property Valuation", help="Start property valuation process"):
            st.success("Valuation request submitted! A specialist will contact you soon.")

    with col2:
        if st.button("📸 Schedule Photos", help="Schedule professional photography"):
            st.success("Photography consultation scheduled!")

    with col3:
        if st.button("📅 Market Timing", help="Get market timing advice"):
            st.success("Market analysis requested!")

    # Simple message interface
    st.markdown("### Quick Questions")

    if "fallback_messages" not in st.session_state:
        st.session_state.fallback_messages = [
            {"role": "assistant", "content": "Hi! I'm your Seller AI Assistant. How can I help you with your property today?"}
        ]

    # Display chat messages
    for message in st.session_state.fallback_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about selling your property..."):
        st.session_state.fallback_messages.append({"role": "user", "content": prompt})

        # Simple response logic
        response = generate_simple_seller_response(prompt)
        st.session_state.fallback_messages.append({"role": "assistant", "content": response})
        st.rerun()

def generate_simple_seller_response(question: str) -> str:
    """Generate simple responses for common seller questions"""
    question_lower = question.lower()

    if any(word in question_lower for word in ["price", "value", "worth", "cost"]):
        return """Great question about property value! Here are key factors that affect your home's worth:

🏠 **Location & Neighborhood**
🏗️ **Property condition and age**
📏 **Square footage and lot size**
🛏️ **Number of bedrooms/bathrooms**
🚗 **Garage and parking**
🌟 **Recent upgrades and improvements**

For an accurate valuation, I recommend scheduling a professional CMA (Comparative Market Analysis). Would you like me to arrange that?"""

    elif any(word in question_lower for word in ["time", "when", "season", "market"]):
        return """Market timing is crucial for maximizing your sale! Consider these factors:

📈 **Current Market Conditions**
- Inventory levels in your area
- Average days on market
- Price trends

🗓️ **Seasonal Factors**
- Spring: Highest buyer activity
- Summer: Good for families
- Fall: Serious buyers
- Winter: Less competition

📊 **Personal Timing**
- Your next home plans
- Financial readiness
- Property preparation time

Would you like a detailed market analysis for your area?"""

    elif any(word in question_lower for word in ["marketing", "photos", "listing", "advertise"]):
        return """Effective marketing is key to a successful sale! Here's our approach:

📸 **Professional Photography**
- High-quality interior/exterior shots
- Drone photography for large properties
- Virtual staging if needed

📝 **Compelling Listing Description**
- Highlight unique features
- Target the right buyers
- SEO-optimized for online searches

🌐 **Multi-Platform Marketing**
- MLS listing
- Major real estate websites
- Social media promotion
- Email campaigns to our network

Would you like to discuss a custom marketing strategy for your property?"""

    elif any(word in question_lower for word in ["prepare", "stage", "improve", "repair"]):
        return """Property preparation can significantly impact your sale! Here's what typically adds value:

🧹 **Essential Preparations**
- Deep cleaning throughout
- Declutter and depersonalize
- Minor repairs and touch-ups

🎨 **Staging & Aesthetics**
- Neutral paint colors
- Update fixtures if needed
- Professional staging consultation

💡 **High-Impact Improvements**
- Kitchen and bathroom updates
- Curb appeal enhancements
- Energy-efficient upgrades

🚫 **Avoid Over-Improving**
- Don't invest more than 75% of expected return
- Focus on buyer preferences in your price range

Would you like a personalized preparation checklist for your property?"""

    else:
        return """Thank you for your question! I'm here to help with all aspects of selling your property.

**I can assist with:**
• Property valuation and pricing strategy
• Market timing and conditions
• Marketing and listing optimization
• Property preparation and staging
• Financial planning and net proceeds

Feel free to ask me about any of these topics, or let me know what specific aspect of selling concerns you most!

For complex questions, our full AI system will be available shortly with enhanced capabilities."""

def render_chat_analytics():
    """Render chat system analytics"""
    st.subheader("📊 Chat System Analytics")

    chat_interface = initialize_chat_system()
    if not chat_interface:
        return

    try:
        # Get session analytics
        analytics = safe_run_async(chat_interface.get_session_analytics())

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
        handle_streamlit_async_error(e, "chat analytics")

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
                    cleaned = safe_run_async(
                        chat_interface.session_manager.cleanup_expired_sessions()
                    )
                    st.success(f"Cleaned {cleaned} expired sessions")
                except Exception as e:
                    handle_streamlit_async_error(e, "session cleanup")

        with col2:
            if st.button("📊 Export Session Data", help="Export conversation data"):
                try:
                    export_data = safe_run_async(
                        chat_interface.chatbot_manager.export_conversation_data("streamlit_demo")
                    )
                    st.download_button(
                        "💾 Download Export",
                        data=str(export_data),
                        file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    handle_streamlit_async_error(e, "session export")

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