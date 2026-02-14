"""
Real-Time Negotiation Coaching Interface

Advanced Streamlit interface for live negotiation coaching with conversation analysis,
tactical adjustments, and strategic guidance during active negotiations.
"""

from datetime import datetime
from typing import Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.services.ai_negotiation_partner import get_ai_negotiation_partner


@st.cache_resource
def get_coaching_partner():
    """Get cached negotiation partner for coaching"""
    return get_ai_negotiation_partner()


class RealTimeNegotiationCoaching:
    """
    Real-time coaching interface for active negotiations with conversation analysis
    and adaptive strategic guidance.
    """

    def __init__(self):
        self.coaching_partner = get_coaching_partner()

        # Initialize session state for coaching
        if "active_coaching_session" not in st.session_state:
            st.session_state.active_coaching_session = None
        if "coaching_conversation_log" not in st.session_state:
            st.session_state.coaching_conversation_log = []
        if "coaching_insights_history" not in st.session_state:
            st.session_state.coaching_insights_history = []
        if "live_coaching_enabled" not in st.session_state:
            st.session_state.live_coaching_enabled = False

    def render(self):
        """Render the complete real-time coaching interface"""

        st.title("💬 Real-Time Negotiation Coaching")
        st.markdown("**AI-powered live coaching for active negotiations**")

        # Coaching status header
        self.render_coaching_status_header()

        # Main coaching interface
        if st.session_state.active_coaching_session:
            self.render_active_coaching_interface()
        else:
            self.render_coaching_setup()

    def render_coaching_status_header(self):
        """Render coaching status and controls"""

        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            if st.session_state.active_coaching_session:
                session = st.session_state.active_coaching_session
                st.success(f"🟢 **Coaching Active:** {session['property_id']}")
                st.caption(f"Started: {session['start_time'].strftime('%H:%M:%S')}")
            else:
                st.info("🔵 **No Active Coaching Session**")

        with col2:
            if st.session_state.coaching_conversation_log:
                st.metric("Conversation Entries", len(st.session_state.coaching_conversation_log))
            else:
                st.metric("Conversation Entries", 0)

        with col3:
            if st.session_state.coaching_insights_history:
                latest_insight = st.session_state.coaching_insights_history[-1]
                confidence = latest_insight.get("confidence", "N/A")
                st.metric("Latest Confidence", f"{confidence}%")
            else:
                st.metric("Latest Confidence", "N/A")

        with col4:
            if st.session_state.active_coaching_session:
                if st.button("🛑 End Session", type="secondary"):
                    self.end_coaching_session()
                    st.rerun()

    def render_coaching_setup(self):
        """Render coaching session setup interface"""

        st.header("Start Real-Time Coaching Session")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Session setup form
            with st.form("start_coaching_session"):
                st.subheader("Negotiation Details")

                property_id = st.text_input("Property ID", value="PROP_789123")
                negotiation_phase = st.selectbox(
                    "Negotiation Phase",
                    ["Initial Contact", "Offer Presentation", "Counter-Negotiation", "Final Terms", "Contract Review"],
                )

                col1a, col1b = st.columns(2)
                with col1a:
                    buyer_type = st.selectbox(
                        "Buyer Type", ["First-Time Buyer", "Move-Up Buyer", "Investor", "Cash Buyer"]
                    )

                with col1b:
                    urgency_level = st.selectbox("Perceived Urgency", ["Low", "Moderate", "High", "Critical"])

                communication_channel = st.selectbox(
                    "Communication Channel", ["Phone Call", "In-Person Meeting", "Video Call", "Text/Email"]
                )

                initial_context = st.text_area(
                    "Initial Situation Context",
                    placeholder="Describe the current situation and what has happened so far...",
                    height=100,
                )

                if st.form_submit_button("🚀 Start Coaching Session", type="primary"):
                    self.start_coaching_session(
                        property_id,
                        negotiation_phase,
                        buyer_type,
                        urgency_level,
                        communication_channel,
                        initial_context,
                    )
                    st.rerun()

        with col2:
            # Coaching capabilities overview
            st.subheader("Coaching Capabilities")

            st.markdown("""
            **Real-Time Analysis:**
            - Conversation sentiment tracking
            - Strategic opportunity identification
            - Risk alert monitoring
            
            **Adaptive Guidance:**
            - Tactical adjustments
            - Script suggestions
            - Objection responses
            
            **Performance Tracking:**
            - Negotiation progress metrics
            - Strategy effectiveness
            - Outcome predictions
            """)

            # Available negotiations
            self.render_available_negotiations()

    def render_active_coaching_interface(self):
        """Render the active coaching interface"""

        # Create coaching tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            ["💬 Live Conversation", "🎯 Strategic Guidance", "📊 Progress Tracking", "⚠️ Risk Monitoring"]
        )

        with tab1:
            self.render_conversation_interface()

        with tab2:
            self.render_strategic_guidance()

        with tab3:
            self.render_progress_tracking()

        with tab4:
            self.render_risk_monitoring()

    def render_conversation_interface(self):
        """Render live conversation tracking and analysis"""

        st.header("Live Conversation Tracking")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Conversation input
            st.subheader("Add Conversation Entry")

            with st.form("add_conversation", clear_on_submit=True):
                speaker = st.selectbox("Speaker", ["Agent", "Buyer", "Seller", "Other"])

                conversation_text = st.text_area(
                    "What was said?", placeholder="Enter the conversation details...", height=100
                )

                col1a, col1b = st.columns(2)
                with col1a:
                    emotional_tone = st.selectbox(
                        "Emotional Tone", ["Neutral", "Positive", "Concerned", "Excited", "Frustrated", "Confident"]
                    )

                with col1b:
                    urgency_change = st.selectbox("Urgency Change", ["No Change", "Increased", "Decreased"])

                if st.form_submit_button("📝 Add Entry", type="primary"):
                    self.add_conversation_entry(speaker, conversation_text, emotional_tone, urgency_change)
                    st.rerun()

            # Quick coaching request
            st.subheader("Quick Coaching Request")
            current_situation = st.selectbox(
                "Current Situation",
                [
                    "Need immediate guidance",
                    "Handling objection",
                    "Making counter-offer",
                    "Closing negotiation",
                    "Addressing concerns",
                    "Building rapport",
                ],
            )

            if st.button("🎯 Get Instant Coaching", type="secondary"):
                self.get_instant_coaching(current_situation)
                st.rerun()

        with col2:
            # Conversation summary
            self.render_conversation_summary()

        # Conversation log
        st.subheader("Conversation Log")
        if st.session_state.coaching_conversation_log:
            for i, entry in enumerate(reversed(st.session_state.coaching_conversation_log[-10:])):
                with st.expander(
                    f"{entry['timestamp'].strftime('%H:%M:%S')} - {entry['speaker']}", expanded=(i == 0)
                ):  # Expand most recent
                    st.write(f"**{entry['speaker']}:** {entry['text']}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"Tone: {entry['emotional_tone']}")
                    with col2:
                        st.caption(f"Urgency: {entry['urgency_change']}")
                    with col3:
                        if entry.get("coaching_triggered"):
                            st.success("✅ Coaching provided")
        else:
            st.info("No conversation entries yet. Add entries above to start tracking.")

    def render_strategic_guidance(self):
        """Render strategic guidance and recommendations"""

        st.header("Strategic Guidance")

        if not st.session_state.coaching_insights_history:
            st.info("Add conversation entries to receive strategic guidance.")
            return

        # Latest coaching insights
        latest_insights = st.session_state.coaching_insights_history[-1]

        col1, col2 = st.columns(2)

        with col1:
            # Immediate guidance
            st.subheader("🎯 Immediate Guidance")
            guidance = latest_insights.get("immediate_guidance", "No guidance available")
            st.info(guidance)

            # Tactical adjustments
            st.subheader("🔧 Tactical Adjustments")
            adjustments = latest_insights.get("tactical_adjustments", [])
            if adjustments:
                for adjustment in adjustments:
                    st.write(f"• {adjustment}")
            else:
                st.write("No tactical adjustments needed.")

            # Next steps
            st.subheader("👣 Next Steps")
            next_steps = latest_insights.get("next_steps", [])
            if next_steps:
                for i, step in enumerate(next_steps, 1):
                    st.write(f"{i}. {step}")
            else:
                st.write("Continue with current approach.")

        with col2:
            # Conversation suggestions
            st.subheader("💬 Conversation Scripts")
            suggestions = latest_insights.get("conversation_suggestions", {})

            if suggestions:
                for situation, suggestion in suggestions.items():
                    with st.expander(f"{situation.replace('_', ' ').title()}"):
                        st.write(suggestion)
                        if st.button(f"Copy {situation}", key=f"copy_{situation}"):
                            st.success("Script copied to clipboard!")

            # Strategy confidence
            st.subheader("📈 Strategy Confidence")
            confidence = latest_insights.get("confidence", 75)

            # Confidence gauge
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=confidence,
                    ontario_mills={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Confidence %"},
                    gauge={
                        "axis": {"range": [None, 100]},
                        "bar": {"color": "darkgreen"},
                        "steps": [
                            {"range": [0, 50], "color": "lightgray"},
                            {"range": [50, 80], "color": "yellow"},
                            {"range": [80, 100], "color": "lightgreen"},
                        ],
                    },
                )
            )
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)

        # Strategy evolution chart
        self.render_strategy_evolution_chart()

    def render_progress_tracking(self):
        """Render negotiation progress tracking"""

        st.header("Negotiation Progress")

        # Progress metrics
        session = st.session_state.active_coaching_session
        duration = datetime.now() - session["start_time"]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Session Duration", f"{duration.seconds // 60}m")

        with col2:
            st.metric("Conversation Entries", len(st.session_state.coaching_conversation_log))

        with col3:
            coaching_count = len(st.session_state.coaching_insights_history)
            st.metric("Coaching Interventions", coaching_count)

        with col4:
            if st.session_state.coaching_insights_history:
                latest_confidence = st.session_state.coaching_insights_history[-1].get("confidence", 0)
                st.metric("Current Confidence", f"{latest_confidence}%")

        # Progress timeline
        st.subheader("Negotiation Timeline")
        if st.session_state.coaching_conversation_log:
            self.render_timeline_chart()

        # Emotional sentiment tracking
        st.subheader("Emotional Sentiment Tracking")
        if st.session_state.coaching_conversation_log:
            self.render_sentiment_chart()

        # Key milestones
        st.subheader("Key Milestones")
        milestones = self.extract_negotiation_milestones()
        if milestones:
            for milestone in milestones:
                st.success(f"✅ {milestone['event']} - {milestone['timestamp'].strftime('%H:%M:%S')}")
        else:
            st.info("No major milestones yet.")

    def render_risk_monitoring(self):
        """Render risk monitoring and alerts"""

        st.header("Risk Monitoring")

        # Risk alerts
        if st.session_state.coaching_insights_history:
            latest_insights = st.session_state.coaching_insights_history[-1]
            risk_alerts = latest_insights.get("risk_alerts", [])

            if risk_alerts:
                st.subheader("⚠️ Active Risk Alerts")
                for risk in risk_alerts:
                    st.error(f"🚨 {risk}")
            else:
                st.success("✅ No active risk alerts")

        # Risk analysis
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Risk Factors")

            # Analyze conversation for risk indicators
            risk_factors = self.analyze_risk_factors()

            if risk_factors:
                for category, risks in risk_factors.items():
                    with st.expander(f"{category} Risks"):
                        for risk in risks:
                            st.write(f"• {risk}")
            else:
                st.info("No significant risk factors detected.")

        with col2:
            st.subheader("Mitigation Strategies")

            # Provide risk mitigation guidance
            mitigation_strategies = self.get_mitigation_strategies()

            if mitigation_strategies:
                for strategy in mitigation_strategies:
                    st.write(f"• {strategy}")
            else:
                st.info("Continue with current approach.")

        # Risk trend chart
        st.subheader("Risk Trend Analysis")
        if len(st.session_state.coaching_insights_history) > 1:
            self.render_risk_trend_chart()

    def render_conversation_summary(self):
        """Render conversation summary and insights"""

        st.subheader("Conversation Summary")

        if not st.session_state.coaching_conversation_log:
            st.info("No conversation data yet.")
            return

        # Summary statistics
        total_entries = len(st.session_state.coaching_conversation_log)
        speaker_counts = {}
        tone_counts = {}

        for entry in st.session_state.coaching_conversation_log:
            speaker = entry["speaker"]
            tone = entry["emotional_tone"]

            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
            tone_counts[tone] = tone_counts.get(tone, 0) + 1

        # Speaker distribution
        if speaker_counts:
            fig = px.pie(
                values=list(speaker_counts.values()),
                names=list(speaker_counts.keys()),
                title="Conversation Distribution",
            )
            fig.update_layout(height=200)
            st.plotly_chart(fig, use_container_width=True)

        # Tone analysis
        if tone_counts:
            st.write("**Emotional Tone Distribution:**")
            for tone, count in tone_counts.items():
                percentage = (count / total_entries) * 100
                st.write(f"• {tone}: {count} ({percentage:.1f}%)")

    def render_timeline_chart(self):
        """Render negotiation timeline chart"""

        timeline_data = []
        for i, entry in enumerate(st.session_state.coaching_conversation_log):
            timeline_data.append(
                {
                    "Time": entry["timestamp"],
                    "Event": f"{entry['speaker']}: {entry['text'][:50]}...",
                    "Speaker": entry["speaker"],
                    "Tone": entry["emotional_tone"],
                    "Index": i,
                }
            )

        df = pd.DataFrame(timeline_data)

        fig = px.scatter(
            df, x="Time", y="Index", color="Speaker", hover_data=["Event", "Tone"], title="Negotiation Timeline"
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    def render_sentiment_chart(self):
        """Render emotional sentiment tracking chart"""

        sentiment_mapping = {
            "Frustrated": -2,
            "Concerned": -1,
            "Neutral": 0,
            "Positive": 1,
            "Confident": 2,
            "Excited": 2,
        }

        sentiment_data = []
        for entry in st.session_state.coaching_conversation_log:
            sentiment_data.append(
                {
                    "Time": entry["timestamp"],
                    "Sentiment": sentiment_mapping.get(entry["emotional_tone"], 0),
                    "Speaker": entry["speaker"],
                }
            )

        df = pd.DataFrame(sentiment_data)

        fig = px.line(df, x="Time", y="Sentiment", color="Speaker", title="Emotional Sentiment Over Time")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    def render_strategy_evolution_chart(self):
        """Render strategy evolution over time"""

        if len(st.session_state.coaching_insights_history) < 2:
            return

        st.subheader("Strategy Evolution")

        evolution_data = []
        for insight in st.session_state.coaching_insights_history:
            evolution_data.append(
                {
                    "Time": insight["timestamp"],
                    "Confidence": insight.get("confidence", 50),
                    "Risk_Level": len(insight.get("risk_alerts", [])) * 20,  # Convert to 0-100 scale
                }
            )

        df = pd.DataFrame(evolution_data)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["Time"],
                y=df["Confidence"],
                mode="lines+markers",
                name="Strategy Confidence",
                line=dict(color="green"),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["Time"],
                y=df["Risk_Level"],
                mode="lines+markers",
                name="Risk Level",
                line=dict(color="red"),
                yaxis="y2",
            )
        )

        fig.update_layout(
            title="Strategy Evolution Over Time",
            yaxis=dict(title="Confidence %"),
            yaxis2=dict(title="Risk Level", overlaying="y", side="right"),
            height=300,
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_risk_trend_chart(self):
        """Render risk trend analysis chart"""

        risk_data = []
        for insight in st.session_state.coaching_insights_history:
            risk_count = len(insight.get("risk_alerts", []))
            risk_data.append({"Time": insight["timestamp"], "Risk_Count": risk_count})

        df = pd.DataFrame(risk_data)

        fig = px.line(df, x="Time", y="Risk_Count", title="Risk Alert Trend", markers=True)
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)

    def render_available_negotiations(self):
        """Render list of available negotiations for coaching"""

        st.subheader("Available Negotiations")

        # Get active negotiations from coaching partner
        active_negotiations = self.coaching_partner.active_negotiations

        if active_negotiations:
            for property_id, negotiation in active_negotiations.items():
                with st.expander(f"Property: {property_id}"):
                    intelligence = negotiation["intelligence"]
                    st.write(f"**Strategy:** {intelligence.negotiation_strategy.primary_tactic}")
                    st.write(f"**Win Probability:** {intelligence.win_probability.win_probability:.1f}%")
                    st.write(f"**Created:** {negotiation['created_at'].strftime('%Y-%m-%d %H:%M')}")

                    if st.button(f"Start Coaching for {property_id}", key=f"start_{property_id}"):
                        self.start_coaching_from_existing(property_id)
                        st.rerun()
        else:
            st.info("No active negotiations available. Run a negotiation analysis first.")

    def start_coaching_session(
        self, property_id: str, phase: str, buyer_type: str, urgency: str, channel: str, context: str
    ):
        """Start a new coaching session"""

        st.session_state.active_coaching_session = {
            "property_id": property_id,
            "start_time": datetime.now(),
            "negotiation_phase": phase,
            "buyer_type": buyer_type,
            "urgency_level": urgency,
            "communication_channel": channel,
            "initial_context": context,
        }

        # Clear previous session data
        st.session_state.coaching_conversation_log = []
        st.session_state.coaching_insights_history = []

        st.success(f"✅ Coaching session started for {property_id}")

    def start_coaching_from_existing(self, property_id: str):
        """Start coaching session from existing negotiation"""

        negotiation = self.coaching_partner.active_negotiations.get(property_id)
        if not negotiation:
            st.error("Negotiation not found")
            return

        st.session_state.active_coaching_session = {
            "property_id": property_id,
            "start_time": datetime.now(),
            "negotiation_phase": "Ongoing",
            "existing_intelligence": negotiation["intelligence"],
        }

        # Clear previous session data
        st.session_state.coaching_conversation_log = []
        st.session_state.coaching_insights_history = []

        st.success(f"✅ Coaching session started for existing negotiation {property_id}")

    def end_coaching_session(self):
        """End the current coaching session"""

        # Save session summary
        if st.session_state.active_coaching_session:
            session_summary = {
                "property_id": st.session_state.active_coaching_session["property_id"],
                "duration": datetime.now() - st.session_state.active_coaching_session["start_time"],
                "conversation_entries": len(st.session_state.coaching_conversation_log),
                "coaching_interventions": len(st.session_state.coaching_insights_history),
                "final_confidence": st.session_state.coaching_insights_history[-1].get("confidence", 0)
                if st.session_state.coaching_insights_history
                else 0,
            }

            st.success(f"✅ Coaching session ended for {session_summary['property_id']}")
            st.info(
                f"Session lasted {session_summary['duration'].seconds // 60} minutes with {session_summary['conversation_entries']} conversation entries"
            )

        # Clear session data
        st.session_state.active_coaching_session = None
        st.session_state.coaching_conversation_log = []
        st.session_state.coaching_insights_history = []

    def add_conversation_entry(self, speaker: str, text: str, tone: str, urgency_change: str):
        """Add a conversation entry and trigger coaching analysis"""

        entry = {
            "timestamp": datetime.now(),
            "speaker": speaker,
            "text": text,
            "emotional_tone": tone,
            "urgency_change": urgency_change,
            "coaching_triggered": False,
        }

        st.session_state.coaching_conversation_log.append(entry)

        # Trigger coaching analysis if significant entry
        if len(text) > 20 or urgency_change != "No Change" or tone in ["Frustrated", "Concerned"]:
            self.trigger_coaching_analysis(text, f"{speaker} conversation")
            entry["coaching_triggered"] = True

        st.success("✅ Conversation entry added")

    def get_instant_coaching(self, situation: str):
        """Get instant coaching for current situation"""

        # Build conversation context
        recent_context = ""
        if st.session_state.coaching_conversation_log:
            recent_entries = st.session_state.coaching_conversation_log[-3:]  # Last 3 entries
            recent_context = "\n".join([f"{entry['speaker']}: {entry['text']}" for entry in recent_entries])

        self.trigger_coaching_analysis(recent_context, situation)
        st.success("🎯 Coaching guidance updated!")

    def trigger_coaching_analysis(self, conversation_context: str, current_situation: str):
        """Trigger coaching analysis and store insights"""

        # Simulate coaching analysis (in production, would call real coaching service)
        coaching_insights = {
            "timestamp": datetime.now(),
            "immediate_guidance": f"For {current_situation.lower()}, maintain confident position while showing flexibility on non-price terms.",
            "tactical_adjustments": [
                "Emphasize buyer qualifications",
                "Reference timeline pressure",
                "Highlight market comparables",
            ],
            "next_steps": [
                "Listen for seller concerns",
                "Address objections with data",
                "Present win-win alternatives",
                "Set next communication timeline",
            ],
            "conversation_suggestions": {
                "opening": f"Based on our conversation, I understand your position on {current_situation.lower()}...",
                "objection_handling": "Let me share some market data that addresses that concern...",
                "closing": "What would need to happen for this to work for both parties?",
            },
            "risk_alerts": [],
            "confidence": 78 + len(st.session_state.coaching_conversation_log) * 2,  # Increases with engagement
        }

        # Add risk alerts based on conversation analysis
        if "frustrated" in conversation_context.lower():
            coaching_insights["risk_alerts"].append("Emotional escalation detected")
        if "other offers" in conversation_context.lower():
            coaching_insights["risk_alerts"].append("Competitive pressure increased")
        if "think about it" in conversation_context.lower():
            coaching_insights["risk_alerts"].append("Decision delay - maintain engagement")

        st.session_state.coaching_insights_history.append(coaching_insights)

    def analyze_risk_factors(self) -> Dict[str, List[str]]:
        """Analyze conversation for risk factors"""

        risk_factors = {"Communication": [], "Timeline": [], "Financial": [], "Emotional": []}

        for entry in st.session_state.coaching_conversation_log:
            text = entry["text"].lower()
            tone = entry["emotional_tone"]

            # Communication risks
            if tone == "Frustrated":
                risk_factors["Communication"].append("Frustration detected in conversation")
            if "confused" in text or "don't understand" in text:
                risk_factors["Communication"].append("Understanding issues identified")

            # Timeline risks
            if "delay" in text or "postpone" in text:
                risk_factors["Timeline"].append("Timeline delays mentioned")
            if "rush" in text or "pressure" in text:
                risk_factors["Timeline"].append("Time pressure concerns")

            # Financial risks
            if "budget" in text or "afford" in text:
                risk_factors["Financial"].append("Budget concerns raised")
            if "financing" in text or "loan" in text:
                risk_factors["Financial"].append("Financing issues mentioned")

            # Emotional risks
            if tone in ["Frustrated", "Concerned"]:
                risk_factors["Emotional"].append(f"{tone} emotional state detected")

        # Filter out empty categories
        return {k: v for k, v in risk_factors.items() if v}

    def get_mitigation_strategies(self) -> List[str]:
        """Get risk mitigation strategies"""

        risk_factors = self.analyze_risk_factors()
        strategies = []

        if "Communication" in risk_factors:
            strategies.append("Slow down pace and confirm understanding frequently")
            strategies.append("Use simpler language and provide clear summaries")

        if "Timeline" in risk_factors:
            strategies.append("Address timeline concerns with specific next steps")
            strategies.append("Offer flexibility where possible")

        if "Financial" in risk_factors:
            strategies.append("Provide detailed financial breakdown")
            strategies.append("Explore creative financing options")

        if "Emotional" in risk_factors:
            strategies.append("Acknowledge emotions and show empathy")
            strategies.append("Focus on shared goals and mutual benefits")

        return strategies

    def extract_negotiation_milestones(self) -> List[Dict]:
        """Extract key negotiation milestones from conversation"""

        milestones = []

        milestone_keywords = {
            "offer": "Offer discussed",
            "counter": "Counter-offer made",
            "accept": "Agreement reached",
            "contract": "Contract terms discussed",
            "close": "Closing timeline set",
        }

        for entry in st.session_state.coaching_conversation_log:
            text = entry["text"].lower()
            for keyword, event in milestone_keywords.items():
                if keyword in text:
                    milestones.append({"event": event, "timestamp": entry["timestamp"], "details": entry["text"]})

        return milestones


def render_realtime_negotiation_coaching():
    """Main function to render the real-time negotiation coaching interface"""
    coaching_interface = RealTimeNegotiationCoaching()
    coaching_interface.render()
