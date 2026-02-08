"""
Voice AI Interface - Interactive Voice Assistant for Real Estate Agents

Provides an intuitive Streamlit interface for Jorge's Voice AI capabilities:
- Real-time voice interaction controls
- Live transcription and AI responses
- Voice analytics and insights dashboard
- Session management and history
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.voice_ai_service import (
    VoiceAnalyticsType,
    VoiceInteractionType,
    get_cached_voice_service,
)

logger = get_logger(__name__)


class VoiceAIInterface:
    """Interactive Voice AI Interface for Streamlit"""

    def __init__(self):
        self.voice_service = get_cached_voice_service()
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state for voice interface."""
        if "voice_session_active" not in st.session_state:
            st.session_state.voice_session_active = False

        if "current_interaction_id" not in st.session_state:
            st.session_state.current_interaction_id = None

        if "voice_transcript" not in st.session_state:
            st.session_state.voice_transcript = []

        if "ai_responses" not in st.session_state:
            st.session_state.ai_responses = []

        if "voice_analytics" not in st.session_state:
            st.session_state.voice_analytics = {}

    def render_voice_controls(self, agent_id: str = "demo_agent") -> Dict[str, Any]:
        """Render voice interaction controls and interface."""

        st.markdown("### 🎤 **Jorge's Voice AI Assistant**")
        st.markdown("*Real-time conversational AI for lead engagement*")

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            # Interaction type selector
            interaction_types = {
                "Lead Qualification": VoiceInteractionType.LEAD_QUALIFICATION,
                "Property Search": VoiceInteractionType.PROPERTY_SEARCH,
                "Market Inquiry": VoiceInteractionType.MARKET_INQUIRY,
                "Appointment Booking": VoiceInteractionType.APPOINTMENT_BOOKING,
                "Follow-up Call": VoiceInteractionType.FOLLOWUP_CALL,
                "General Inquiry": VoiceInteractionType.GENERAL_INQUIRY,
            }

            selected_type = st.selectbox("Interaction Type", options=list(interaction_types.keys()), index=0)

        with col2:
            # Lead ID input (optional)
            lead_id = st.text_input(
                "Lead ID (optional)", placeholder="LEAD_12345", help="Associate this conversation with a specific lead"
            )

        with col3:
            # Voice session controls
            st.markdown("**Session Controls**")

            if not st.session_state.voice_session_active:
                if st.button("🎙️ Start Voice Session", type="primary", use_container_width=True):
                    self._start_voice_session(agent_id, interaction_types[selected_type], lead_id if lead_id else None)
            else:
                col_pause, col_end = st.columns(2)
                with col_pause:
                    if st.button("⏸️ Pause", use_container_width=True):
                        st.session_state.voice_session_paused = True

                with col_end:
                    if st.button("🛑 End Session", type="secondary", use_container_width=True):
                        self._end_voice_session()

        return {"session_active": st.session_state.voice_session_active}

    def render_live_interaction(self) -> None:
        """Render live voice interaction interface."""

        if not st.session_state.voice_session_active:
            st.info("👆 Start a voice session to begin interacting with Jorge's AI")
            return

        st.markdown("---")
        st.markdown("### 🗣️ **Live Conversation**")

        # Live status indicator
        status_col, metrics_col = st.columns([1, 3])

        with status_col:
            if st.session_state.get("voice_session_paused", False):
                st.markdown("🟡 **Status:** Paused")
            else:
                st.markdown("🟢 **Status:** Active")

        with metrics_col:
            # Real-time metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Duration", "12:34", help="Current session duration")

            with col2:
                st.metric("Sentiment", "😊 Positive", "+0.3", help="Current conversation sentiment")

            with col3:
                st.metric("Engagement", "85%", "+5%", help="Lead engagement level")

            with col4:
                st.metric("Conv. Prob", "72%", "+12%", help="Conversion probability")

        # Simulated voice input
        st.markdown("#### 📝 Voice Input Simulation")

        # Demo transcript input
        demo_inputs = [
            "Hi, I'm looking for a 3-bedroom house in Austin under $500k",
            "Can you show me some properties in the Cedar Park area?",
            "What's the market like right now? Are prices going up?",
            "I need to move by the end of next month, can you help?",
            "Do you have any properties with a good school district?",
        ]

        selected_input = st.selectbox("Simulate Voice Input:", options=["Custom input..."] + demo_inputs, index=0)

        if selected_input == "Custom input...":
            voice_input = st.text_area(
                "Type what the client said:", placeholder="Enter simulated voice input...", height=100
            )
        else:
            voice_input = selected_input
            st.text_area("Client said:", value=voice_input, height=100, disabled=True)

        if st.button("🔄 Process Voice Input", type="primary", disabled=not voice_input):
            with st.spinner("🤖 Jorge is thinking..."):
                self._process_simulated_input(voice_input)

        # Conversation history
        self._render_conversation_history()

    def render_voice_analytics(self) -> Dict[str, Any]:
        """Render voice analytics and insights dashboard."""

        st.markdown("### 📊 **Voice Analytics Dashboard**")

        # Get analytics data
        analytics_data = self._get_demo_analytics_data()

        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Calls", "47", "+12 this week", help="Total voice interactions this period")

        with col2:
            st.metric("Avg Duration", "12.3 min", "+2.1 min", help="Average call duration")

        with col3:
            st.metric("Conversion Rate", "34.2%", "+8.1%", help="Voice-to-conversion rate")

        with col4:
            st.metric("Avg Sentiment", "0.72", "+0.15", help="Average sentiment score")

        with col5:
            st.metric("AI Accuracy", "91.3%", "+2.4%", help="AI response accuracy")

        # Analytics visualizations
        col_left, col_right = st.columns(2)

        with col_left:
            # Sentiment distribution
            st.markdown("#### 😊 Sentiment Distribution")

            sentiment_data = analytics_data["sentiment_distribution"]
            fig_sentiment = px.pie(
                values=list(sentiment_data.values()),
                names=list(sentiment_data.keys()),
                color_discrete_map={"positive": "#00D4AA", "neutral": "#FFB800", "negative": "#FF4B4B"},
            )
            fig_sentiment.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_sentiment, use_container_width=True)

        with col_right:
            # Conversion by interaction type
            st.markdown("#### 🎯 Conversion by Type")

            conversion_data = analytics_data["conversion_by_type"]
            fig_conversion = px.bar(
                x=list(conversion_data.values()),
                y=list(conversion_data.keys()),
                orientation="h",
                color=list(conversion_data.values()),
                color_continuous_scale="Viridis",
            )
            fig_conversion.update_layout(
                xaxis_title="Conversion Rate (%)", yaxis_title="Interaction Type", showlegend=False
            )
            st.plotly_chart(fig_conversion, use_container_width=True)

        # Top intents table
        st.markdown("#### 🎯 **Top Client Intents**")

        intents_data = analytics_data["top_intents"]

        for i, intent in enumerate(intents_data):
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.write(f"**{intent['intent'].replace('_', ' ').title()}**")

            with col2:
                st.write(f"{intent['count']} times")

            with col3:
                percentage = (intent["count"] / sum(item["count"] for item in intents_data)) * 100
                st.write(f"{percentage:.1f}%")

        return analytics_data

    def _start_voice_session(
        self, agent_id: str, interaction_type: VoiceInteractionType, lead_id: Optional[str] = None
    ):
        """Start a new voice interaction session."""
        try:
            # Simulate starting session (would be async in production)
            interaction_id = f"voice_{agent_id}_{int(time.time())}"

            st.session_state.voice_session_active = True
            st.session_state.current_interaction_id = interaction_id
            st.session_state.voice_transcript = []
            st.session_state.ai_responses = []
            st.session_state.voice_analytics = {}

            st.success(f"🎙️ Voice session started! Session ID: {interaction_id}")
            logger.info(f"Voice session started: {interaction_id}")

        except Exception as e:
            st.error(f"Failed to start voice session: {e}")
            logger.error(f"Voice session start failed: {e}")

    def _end_voice_session(self):
        """End the current voice interaction session."""
        try:
            if st.session_state.current_interaction_id:
                # Generate session summary
                summary = {
                    "interaction_id": st.session_state.current_interaction_id,
                    "duration": "12:34",
                    "total_exchanges": len(st.session_state.voice_transcript),
                    "final_sentiment": "Positive",
                    "conversion_probability": "72%",
                    "next_best_action": "Schedule property viewing",
                }

                st.session_state.voice_session_active = False
                st.session_state.current_interaction_id = None

                st.success("✅ Voice session ended successfully!")

                # Display session summary
                with st.expander("📋 Session Summary", expanded=True):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**Session Details**")
                        st.write(f"• Duration: {summary['duration']}")
                        st.write(f"• Exchanges: {summary['total_exchanges']}")
                        st.write(f"• Final Sentiment: {summary['final_sentiment']}")

                    with col2:
                        st.write("**Insights & Actions**")
                        st.write(f"• Conversion Probability: {summary['conversion_probability']}")
                        st.write(f"• Next Best Action: {summary['next_best_action']}")

                logger.info("Voice session ended successfully")

        except Exception as e:
            st.error(f"Failed to end voice session: {e}")
            logger.error(f"Voice session end failed: {e}")

    def _process_simulated_input(self, voice_input: str):
        """Process simulated voice input and generate AI response."""
        try:
            # Add to transcript
            st.session_state.voice_transcript.append(
                {"timestamp": datetime.now().strftime("%H:%M:%S"), "speaker": "Client", "content": voice_input}
            )

            # Simulate AI response generation
            ai_responses = [
                "That's a great budget range for Austin! I have several 3-bedroom properties under $500K that would be perfect for you. Let me show you some options in areas with excellent value.",
                "Cedar Park is an excellent choice! It's known for great schools and family-friendly neighborhoods. I have 8 properties there that match your criteria. Would you like to see them?",
                "The Austin market is quite dynamic right now. While there's been some appreciation, we're seeing good opportunities for buyers with your budget. Interest rates are favorable too.",
                "Absolutely! With your timeline, we'll want to move quickly. I can arrange viewings this week and have you under contract within 2 weeks if we find the right property.",
                "School districts are definitely important! Cedar Park and Round Rock ISD are top-rated. I have several properties in those areas that would be perfect for your family.",
            ]

            # Select appropriate response (simplified logic)
            import random

            ai_response = random.choice(ai_responses)

            # Add AI response to transcript
            st.session_state.ai_responses.append(
                {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": ai_response,
                    "sentiment_score": 0.8,
                    "confidence": 0.92,
                }
            )

            st.session_state.voice_transcript.append(
                {"timestamp": datetime.now().strftime("%H:%M:%S"), "speaker": "Jorge AI", "content": ai_response}
            )

            st.success("✅ Voice input processed successfully!")

        except Exception as e:
            st.error(f"Failed to process voice input: {e}")
            logger.error(f"Voice input processing failed: {e}")

    def _render_conversation_history(self):
        """Render the conversation history."""
        if st.session_state.voice_transcript:
            st.markdown("#### 💬 **Conversation History**")

            # Create a scrollable container for conversation
            with st.container():
                for entry in st.session_state.voice_transcript[-10:]:  # Show last 10 exchanges
                    if entry["speaker"] == "Client":
                        st.markdown(
                            f"""
                        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin: 5px 0;">
                        <strong>🗣️ Client ({entry["timestamp"]}):</strong><br>
                        {entry["content"]}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                        <div style="background-color: #e8f4fd; padding: 10px; border-radius: 10px; margin: 5px 0;">
                        <strong>🤖 Jorge AI ({entry["timestamp"]}):</strong><br>
                        {entry["content"]}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

    def _get_demo_analytics_data(self) -> Dict[str, Any]:
        """Get demonstration analytics data."""
        return {
            "total_interactions": 47,
            "avg_duration_minutes": 12.3,
            "conversion_rate": 34.2,
            "avg_sentiment_score": 0.72,
            "top_intents": [
                {"intent": "property_viewing", "count": 23},
                {"intent": "market_inquiry", "count": 18},
                {"intent": "budget_discussion", "count": 15},
                {"intent": "school_district", "count": 12},
                {"intent": "timeline_discussion", "count": 9},
            ],
            "sentiment_distribution": {"positive": 68.1, "neutral": 23.4, "negative": 8.5},
            "conversion_by_type": {
                "lead_qualification": 45.2,
                "property_search": 31.8,
                "market_inquiry": 22.7,
                "appointment_booking": 38.5,
                "followup_call": 28.9,
            },
            "ai_performance": {"response_accuracy": 91.3, "avg_response_time": 1.2, "user_satisfaction": 4.6},
        }


# Component function for easy integration
def render_voice_ai_interface(agent_id: str = "demo_agent") -> Dict[str, Any]:
    """
    Main function to render the complete Voice AI interface.

    Args:
        agent_id: The real estate agent ID

    Returns:
        Dict containing session status and analytics data
    """
    interface = VoiceAIInterface()

    # Render voice controls
    session_status = interface.render_voice_controls(agent_id)

    # Render live interaction interface
    interface.render_live_interaction()

    st.markdown("---")

    # Render analytics dashboard
    analytics_data = interface.render_voice_analytics()

    return {"session_active": session_status["session_active"], "analytics": analytics_data}


if __name__ == "__main__":
    # Test the voice AI interface
    st.set_page_config(page_title="Voice AI Interface Test", page_icon="🎤", layout="wide")

    st.title("🎤 Jorge's Voice AI Interface - Test")
    render_voice_ai_interface("test_agent")
