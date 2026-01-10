"""
Enhanced Lead Intelligence Dashboard

Advanced Streamlit interface for the lead intelligence system with
real-time analytics, conversation insights, and AI recommendations.
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from .advanced_lead_intelligence import (
    AdvancedLeadIntelligence,
    LeadQualificationLevel,
    ConversationSentiment,
    ConversationIntent
)
from .streamlit_chat_component import initialize_chat_system


class EnhancedLeadIntelligenceDashboard:
    """Enhanced dashboard for advanced lead intelligence features"""

    def __init__(self, intelligence_system: AdvancedLeadIntelligence):
        self.intelligence = intelligence_system

    def render_enhanced_lead_hub(self):
        """Render the complete enhanced lead intelligence hub"""

        st.title("🧠 Enhanced Lead Intelligence Hub")
        st.markdown("*AI-powered lead qualification, conversation intelligence, and predictive analytics*")

        # Enhanced tabs with new intelligence features
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "💬 Intelligent Chat",
            "📊 Real-Time Analytics",
            "🎯 Lead Qualification",
            "🔮 Conversation Intelligence",
            "📈 Predictive Insights",
            "⚙️ AI Configuration"
        ])

        with tab1:
            self.render_intelligent_chat_interface()

        with tab2:
            self.render_real_time_analytics()

        with tab3:
            self.render_advanced_qualification_dashboard()

        with tab4:
            self.render_conversation_intelligence()

        with tab5:
            self.render_predictive_insights()

        with tab6:
            self.render_ai_configuration()

    def render_intelligent_chat_interface(self):
        """Enhanced chat interface with real-time intelligence"""

        st.subheader("💬 AI-Enhanced Lead Chat")
        st.markdown("*Chat with real-time qualification scoring and intelligence analysis*")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Main chat interface
            st.markdown("**Conversation**")

            # Initialize chat system
            chat_interface = initialize_chat_system("enhanced_intelligence")

            if chat_interface:
                try:
                    # Enhanced chat with intelligence integration
                    asyncio.run(self._render_enhanced_chat(chat_interface))
                except Exception as e:
                    st.error(f"Enhanced chat temporarily unavailable: {str(e)}")
            else:
                st.error("Chat system unavailable")

        with col2:
            # Real-time intelligence panel
            st.markdown("**Live Intelligence**")
            self.render_live_intelligence_panel()

    async def _render_enhanced_chat(self, chat_interface):
        """Render chat with enhanced intelligence features"""

        # Get selected lead for demo
        if "demo_lead_id" not in st.session_state:
            st.session_state.demo_lead_id = "lead_demo_001"

        demo_lead_id = st.session_state.demo_lead_id

        # Chat interface
        if "intelligence_messages" not in st.session_state:
            st.session_state.intelligence_messages = [
                {"role": "assistant", "content": "Hi! I'm your AI assistant. I'll help you find the perfect property while learning about your needs. What brings you here today?"}
            ]

        # Display messages with intelligence annotations
        for i, msg in enumerate(st.session_state.intelligence_messages):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

                # Show intelligence insights for user messages
                if msg["role"] == "user" and "intelligence" in msg:
                    with st.expander("🧠 AI Analysis", expanded=False):
                        intel = msg["intelligence"]
                        st.json(intel)

        # Chat input
        if prompt := st.chat_input("Type your message..."):
            st.session_state.intelligence_messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            # Process with intelligence
            with st.chat_message("assistant"):
                with st.spinner("Processing with AI intelligence..."):
                    # Simulate intelligence analysis
                    intelligence_result = await self.intelligence.analyze_conversation_turn(
                        demo_lead_id, "demo_tenant", prompt
                    )

                    # Generate response based on intelligence
                    response = self._generate_intelligent_response(prompt, intelligence_result)

                    st.markdown(response)

                    # Add intelligence data to user message
                    st.session_state.intelligence_messages[-1]["intelligence"] = intelligence_result

                    # Add assistant response
                    st.session_state.intelligence_messages.append({
                        "role": "assistant",
                        "content": response
                    })

                    # Show real-time insights
                    if intelligence_result["qualification_score"] > 60:
                        st.success(f"🎯 High-quality lead detected! Score: {intelligence_result['qualification_score']}")

                    if "urgency_level" in intelligence_result and intelligence_result["urgency_level"] > 7:
                        st.warning("🚨 High urgency detected - consider priority handling")

    def _generate_intelligent_response(self, user_message: str, intelligence: Dict) -> str:
        """Generate contextually aware response based on intelligence analysis"""

        score = intelligence["qualification_score"]
        level = intelligence["qualification_level"]
        sentiment = intelligence.get("conversation_intelligence", {}).get("sentiment", "neutral")

        # Base response logic
        user_lower = user_message.lower()

        # Qualification-aware responses
        if score < 20:
            # Low qualification - focus on basic info gathering
            if any(word in user_lower for word in ["hi", "hello", "hey"]):
                return "Hello! I'd love to help you with your real estate needs. To get started, could you tell me a bit about what you're looking for?"
            elif any(word in user_lower for word in ["budget", "price", "cost"]):
                return "Understanding your budget helps me find the best options for you. What price range are you comfortable with?"
            else:
                return "I'd like to learn more about your needs. Are you looking to buy or just exploring options at this stage?"

        elif score < 50:
            # Medium qualification - gather missing pieces
            if "budget" not in intelligence.get("analysis_result", {}).get("extracted_entities", []):
                return "Great! I'm getting a good sense of what you're looking for. To narrow down the perfect options, what budget range works best for you?"
            elif not any("timeline" in str(entity) for entity in intelligence.get("analysis_result", {}).get("extracted_entities", [])):
                return "Perfect! When are you hoping to make your move? This helps me prioritize the best opportunities for you."
            else:
                return "Excellent! You're well qualified. Let me show you some properties that match exactly what you're looking for."

        else:
            # High qualification - focus on conversion
            if sentiment == "very_positive":
                return "I can tell you're excited about this! Based on everything you've shared, I have some perfect matches. Would you like to schedule a viewing this week?"
            elif "buying_signals" in intelligence.get("conversation_intelligence", {}):
                return "It sounds like you're ready to move forward! Let me connect you with our senior agent who can expedite your search and help you secure the right property."
            else:
                return "You're an excellent fit for several properties I have in mind. Would you like me to send you the top 3 matches today?"

        # Sentiment-aware adjustments
        if sentiment == "frustrated":
            return "I understand your frustration, and I want to make this as smooth as possible for you. Let me personally ensure we find exactly what you need. What's the most important thing I can help you with right now?"
        elif sentiment == "concerned":
            return "I can sense you might have some concerns, which is completely normal. Would you like to discuss any specific questions or worries you have about the process?"

        return "Thank you for sharing that information. It helps me understand exactly what you're looking for. Let me see how I can best assist you next."

    def render_live_intelligence_panel(self):
        """Real-time intelligence monitoring panel"""

        if "demo_lead_id" not in st.session_state:
            return

        demo_lead_id = st.session_state.demo_lead_id
        conversation_key = f"demo_tenant:{demo_lead_id}"

        # Get current intelligence data
        if hasattr(self.intelligence, 'qualification_data') and conversation_key in self.intelligence.qualification_data:
            qual = self.intelligence.qualification_data[conversation_key]
            score = qual.calculate_score()

            # Score visualization
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Lead Score"},
                delta={'reference': 50},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 25], 'color': "lightgray"},
                        {'range': [25, 50], 'color': "yellow"},
                        {'range': [50, 75], 'color': "orange"},
                        {'range': [75, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 80
                    }
                }
            ))
            fig.update_layout(height=200)
            st.plotly_chart(fig, use_container_width=True)

            # Qualification checklist
            st.markdown("**Qualification Status:**")
            checklist = {
                "Name": "✅" if qual.has_name else "❌",
                "Contact": "✅" if qual.has_contact_info else "❌",
                "Budget": "✅" if qual.has_budget_range else "❌",
                "Timeline": "✅" if qual.has_timeline else "❌",
                "Location": "✅" if qual.has_location_preference else "❌",
                "Financing": "✅" if qual.has_financing_info else "❌"
            }

            for item, status in checklist.items():
                st.markdown(f"{status} {item}")

            # Urgency indicator
            if qual.urgency_level > 5:
                st.error(f"🚨 High Urgency: {qual.urgency_level}/10")
            elif qual.urgency_level > 2:
                st.warning(f"⚠️ Moderate Urgency: {qual.urgency_level}/10")
            else:
                st.info(f"🕐 Standard Timeline: {qual.urgency_level}/10")

        # Intelligence insights
        if hasattr(self.intelligence, 'conversation_intelligence') and conversation_key in self.intelligence.conversation_intelligence:
            intel = self.intelligence.conversation_intelligence[conversation_key]

            st.markdown("**Conversation Insights:**")
            st.markdown(f"**Messages:** {intel.message_count}")
            st.markdown(f"**Sentiment:** {intel.sentiment.value.replace('_', ' ').title()}")

            if intel.detected_intents:
                st.markdown("**Detected Intents:**")
                for intent in intel.detected_intents[-3:]:  # Last 3 intents
                    st.markdown(f"• {intent.value.replace('_', ' ').title()}")

            if intel.buying_signals:
                st.success("🎯 Buying signals detected!")

            if intel.objection_signals:
                st.warning("⚠️ Objections detected")

    def render_real_time_analytics(self):
        """Real-time analytics dashboard"""

        st.subheader("📊 Real-Time Lead Intelligence Analytics")

        # Get analytics data
        try:
            analytics = asyncio.run(
                self.intelligence.get_conversation_analytics("demo_tenant")
            )

            # Key metrics row
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Conversations",
                    analytics["total_conversations"],
                    delta="+12 today"
                )

            with col2:
                avg_score = analytics["average_qualification_score"]
                st.metric(
                    "Avg. Qualification Score",
                    f"{avg_score:.1f}",
                    delta="+5.2 vs last week"
                )

            with col3:
                qualified_pct = sum(
                    count for level, count in analytics["qualification_distribution"].items()
                    if level in ["sales_qualified", "hot_prospect"]
                ) / max(analytics["total_conversations"], 1) * 100
                st.metric(
                    "Qualified Leads %",
                    f"{qualified_pct:.1f}%",
                    delta="+8% vs last week"
                )

            with col4:
                positive_sentiment_pct = analytics["sentiment_distribution"].get("positive", 0) + \
                                       analytics["sentiment_distribution"].get("very_positive", 0)
                total_sentiment = sum(analytics["sentiment_distribution"].values())
                if total_sentiment > 0:
                    positive_pct = positive_sentiment_pct / total_sentiment * 100
                else:
                    positive_pct = 0
                st.metric(
                    "Positive Sentiment %",
                    f"{positive_pct:.1f}%",
                    delta="+3% vs last week"
                )

            # Charts row
            col1, col2 = st.columns(2)

            with col1:
                # Qualification distribution
                st.markdown("**Lead Qualification Distribution**")
                if analytics["qualification_distribution"]:
                    qual_df = pd.DataFrame([
                        {"Level": level.replace("_", " ").title(), "Count": count}
                        for level, count in analytics["qualification_distribution"].items()
                    ])
                    fig = px.pie(qual_df, values="Count", names="Level",
                               title="Lead Quality Distribution")
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No qualification data available yet")

            with col2:
                # Intent analysis
                st.markdown("**Top Conversation Intents**")
                if analytics["intent_distribution"]:
                    intent_df = pd.DataFrame([
                        {"Intent": intent.replace("_", " ").title(), "Frequency": freq}
                        for intent, freq in list(analytics["intent_distribution"].items())[:5]
                    ])
                    fig = px.bar(intent_df, x="Intent", y="Frequency",
                               title="Most Common Conversation Topics")
                    fig.update_layout(height=300, xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No intent data available yet")

            # Sentiment analysis
            st.markdown("**Sentiment Analysis Trends**")
            if analytics["sentiment_distribution"]:
                sentiment_df = pd.DataFrame([
                    {"Sentiment": sent.replace("_", " ").title(), "Count": count}
                    for sent, count in analytics["sentiment_distribution"].items()
                ])
                fig = px.bar(sentiment_df, x="Sentiment", y="Count",
                           color="Count", color_continuous_scale="RdYlGn",
                           title="Lead Sentiment Distribution")
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sentiment data available yet")

        except Exception as e:
            st.error(f"Analytics temporarily unavailable: {str(e)}")

    def render_advanced_qualification_dashboard(self):
        """Advanced lead qualification management"""

        st.subheader("🎯 Advanced Lead Qualification")

        # Qualification framework overview
        st.markdown("**AI-Powered Qualification Framework**")
        st.markdown("""
        Our advanced system evaluates leads across multiple dimensions:
        - **Basic Information** (25 points): Name, contact, location
        - **Financial Qualification** (30 points): Budget, financing, pre-approval
        - **Motivation & Timeline** (25 points): Timeline, motivation, urgency
        - **Property Criteria** (20 points): Type, size, features
        """)

        # Real-time qualification tracking
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**Active Lead Scoring**")

            # Demo qualification scores
            demo_leads = [
                {"name": "Sarah Johnson", "score": 85, "level": "Hot Prospect", "urgency": 8},
                {"name": "Mike Chen", "score": 72, "level": "Sales Qualified", "urgency": 5},
                {"name": "Lisa Rodriguez", "score": 45, "level": "Basic Qualified", "urgency": 3},
                {"name": "Anonymous Lead", "score": 15, "level": "Initial Interest", "urgency": 1}
            ]

            for lead in demo_leads:
                with st.expander(f"{lead['name']} - Score: {lead['score']}", expanded=False):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**Level:** {lead['level']}")
                        st.markdown(f"**Urgency:** {lead['urgency']}/10")
                    with col_b:
                        # Progress bar for score
                        st.progress(lead['score'] / 100)
                        if lead['score'] >= 70:
                            st.success("Ready for sales handoff")
                        elif lead['score'] >= 40:
                            st.warning("Needs more qualification")
                        else:
                            st.info("Early stage lead")

        with col2:
            st.markdown("**Qualification Insights**")

            # Most common gaps
            st.markdown("**Top Qualification Gaps:**")
            gaps = [
                "Budget range - 45% of leads",
                "Timeline - 38% of leads",
                "Financing status - 32% of leads",
                "Property preferences - 28% of leads"
            ]
            for gap in gaps:
                st.markdown(f"• {gap}")

            # Recommendations
            st.markdown("**AI Recommendations:**")
            recommendations = [
                "Focus budget qualification early in conversation",
                "Use urgency signals to prioritize follow-ups",
                "Implement financing pre-qualification",
                "Create property preference templates"
            ]
            for rec in recommendations:
                st.markdown(f"✅ {rec}")

    def render_conversation_intelligence(self):
        """Conversation intelligence and analysis"""

        st.subheader("🔮 Conversation Intelligence")

        # Intelligence overview
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Real-Time Analysis Features**")
            features = [
                "🎯 **Intent Detection** - Automatically identifies conversation goals",
                "😊 **Sentiment Analysis** - Tracks emotional state throughout conversation",
                "🚨 **Urgency Detection** - Identifies time-sensitive leads",
                "💰 **Buying Signals** - Recognizes purchase-ready indicators",
                "⚠️ **Objection Recognition** - Detects and categorizes concerns",
                "📊 **Engagement Scoring** - Measures conversation quality"
            ]
            for feature in features:
                st.markdown(feature)

        with col2:
            st.markdown("**Live Intelligence Patterns**")

            # Sample patterns detected
            patterns = [
                {"type": "🎯 Buying Signal", "text": "ready to move forward", "confidence": 92},
                {"type": "⚠️ Objection", "text": "commission seems high", "confidence": 88},
                {"type": "🚨 Urgency", "text": "lease ends next month", "confidence": 95},
                {"type": "😊 Positive Sentiment", "text": "love this area", "confidence": 85}
            ]

            for pattern in patterns:
                st.markdown(f"**{pattern['type']}**")
                st.markdown(f"Text: \"{pattern['text']}\"")
                st.markdown(f"Confidence: {pattern['confidence']}%")
                st.markdown("---")

        # Conversation flow analysis
        st.markdown("**Conversation Flow Intelligence**")

        # Sample conversation stages
        stages_data = {
            "Stage": ["Initial Contact", "Qualification", "Needs Assessment", "Property Discussion", "Closing"],
            "Avg Duration (min)": [3.5, 8.2, 12.1, 15.8, 22.3],
            "Conversion Rate (%)": [85, 72, 68, 58, 45],
            "Drop-off Rate (%)": [15, 13, 4, 10, 55]
        }
        stages_df = pd.DataFrame(stages_data)

        # Conversion funnel
        fig = px.funnel(stages_df, x="Conversion Rate (%)", y="Stage",
                       title="Lead Conversation Funnel Analysis")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def render_predictive_insights(self):
        """Predictive analytics and AI insights"""

        st.subheader("📈 Predictive Intelligence & AI Insights")

        # Predictive models overview
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Conversion Prediction Models**")

            # Model performance metrics
            models = [
                {"name": "Lead Scoring Model", "accuracy": 89.3, "status": "Active"},
                {"name": "Timeline Prediction", "accuracy": 82.7, "status": "Active"},
                {"name": "Churn Prevention", "accuracy": 91.2, "status": "Active"},
                {"name": "Price Sensitivity", "accuracy": 78.9, "status": "Training"}
            ]

            for model in models:
                st.markdown(f"**{model['name']}**")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"Accuracy: {model['accuracy']}%")
                with col_b:
                    if model['status'] == 'Active':
                        st.success(model['status'])
                    else:
                        st.warning(model['status'])
                st.markdown("---")

        with col2:
            st.markdown("**AI-Generated Follow-up Recommendations**")

            # Sample recommendations
            recommendations = [
                {
                    "lead": "Sarah J.",
                    "action": "Schedule Call",
                    "priority": "High",
                    "timing": "1 hour",
                    "reason": "Strong buying signals + high urgency"
                },
                {
                    "lead": "Mike C.",
                    "action": "Send Listings",
                    "priority": "Medium",
                    "timing": "2 hours",
                    "reason": "Budget qualified + property search intent"
                },
                {
                    "lead": "Lisa R.",
                    "action": "Budget Follow-up",
                    "priority": "Medium",
                    "timing": "4 hours",
                    "reason": "Missing budget qualification"
                }
            ]

            for rec in recommendations:
                with st.container():
                    st.markdown(f"**{rec['lead']}** - {rec['action']}")
                    priority_color = "🔴" if rec['priority'] == "High" else "🟡"
                    st.markdown(f"{priority_color} {rec['priority']} Priority")
                    st.markdown(f"⏰ Follow up in: {rec['timing']}")
                    st.markdown(f"💡 Reason: {rec['reason']}")
                    st.markdown("---")

        # Predictive trends
        st.markdown("**Predictive Trend Analysis**")

        # Sample trend data
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        trend_data = pd.DataFrame({
            'Date': dates,
            'Predicted Conversions': [15, 18, 22, 16, 25, 28, 20, 19, 24, 27,
                                    30, 26, 23, 28, 32, 29, 25, 31, 35, 28,
                                    27, 33, 36, 31, 29, 34, 38, 33, 30, 35],
            'Actual Conversions': [14, 17, 20, 18, 24, 26, 22, 18, 23, 25,
                                 28, 24, 25, 27, 30, 28, 27, 29, 33, 30,
                                 26, 31, 34, 29, 31, 32, 36, 31, 32, 33]
        })

        fig = px.line(trend_data, x='Date', y=['Predicted Conversions', 'Actual Conversions'],
                     title="AI Prediction vs Actual Performance",
                     labels={'value': 'Conversions', 'variable': 'Type'})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def render_ai_configuration(self):
        """AI system configuration and tuning"""

        st.subheader("⚙️ AI Intelligence Configuration")

        # Model configuration
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Qualification Thresholds**")

            # Adjustable thresholds
            hot_prospect_threshold = st.slider(
                "Hot Prospect Threshold",
                min_value=70, max_value=95, value=80,
                help="Minimum score for hot prospect classification"
            )

            sales_qualified_threshold = st.slider(
                "Sales Qualified Threshold",
                min_value=50, max_value=80, value=60,
                help="Minimum score for sales qualified leads"
            )

            urgency_threshold = st.slider(
                "High Urgency Threshold",
                min_value=5, max_value=10, value=7,
                help="Minimum urgency score for priority handling"
            )

        with col2:
            st.markdown("**Intelligence Settings**")

            # Feature toggles
            enable_sentiment = st.checkbox("Enable Sentiment Analysis", value=True)
            enable_intent = st.checkbox("Enable Intent Detection", value=True)
            enable_urgency = st.checkbox("Enable Urgency Detection", value=True)
            enable_predictions = st.checkbox("Enable Predictive Analytics", value=True)

            # Response timing
            response_delay = st.select_slider(
                "AI Response Timing",
                options=["Instant", "Natural (1-2s)", "Thoughtful (3-5s)"],
                value="Natural (1-2s)",
                help="Simulate human-like response timing"
            )

        # Advanced settings
        with st.expander("Advanced AI Configuration", expanded=False):
            st.markdown("**Pattern Recognition Sensitivity**")

            col_a, col_b = st.columns(2)
            with col_a:
                buying_signal_sensitivity = st.slider("Buying Signals", 1, 10, 7)
                objection_sensitivity = st.slider("Objections", 1, 10, 8)

            with col_b:
                urgency_sensitivity = st.slider("Urgency Detection", 1, 10, 6)
                sentiment_sensitivity = st.slider("Sentiment Analysis", 1, 10, 7)

            # Training data preferences
            st.markdown("**Model Training Preferences**")
            training_focus = st.multiselect(
                "Focus Areas for Model Training",
                ["Lead Qualification", "Conversation Intelligence", "Predictive Analytics",
                 "Follow-up Timing", "Objection Handling", "Buying Signal Recognition"],
                default=["Lead Qualification", "Conversation Intelligence"]
            )

        # Save configuration
        if st.button("💾 Save AI Configuration", type="primary"):
            config = {
                "thresholds": {
                    "hot_prospect": hot_prospect_threshold,
                    "sales_qualified": sales_qualified_threshold,
                    "urgency": urgency_threshold
                },
                "features": {
                    "sentiment": enable_sentiment,
                    "intent": enable_intent,
                    "urgency": enable_urgency,
                    "predictions": enable_predictions
                },
                "sensitivity": {
                    "buying_signals": buying_signal_sensitivity,
                    "objections": objection_sensitivity,
                    "urgency": urgency_sensitivity,
                    "sentiment": sentiment_sensitivity
                },
                "response_timing": response_delay,
                "training_focus": training_focus
            }
            st.success("✅ AI Configuration saved successfully!")
            st.json(config)


def render_enhanced_lead_intelligence_hub():
    """Main function to render the enhanced lead intelligence dashboard"""

    try:
        # Initialize the intelligence system (would be integrated with actual system)
        from .chatbot_manager import ChatbotManager
        from .chat_ml_integration import ChatMLIntegration
        from .advanced_lead_intelligence import integrate_advanced_intelligence

        # For demo purposes, create mock instances
        chatbot_manager = None  # Would be actual instance
        ml_integration = None   # Would be actual instance

        # Create dashboard with mock intelligence system
        dashboard = EnhancedLeadIntelligenceDashboard(None)  # Mock for demo
        dashboard.render_enhanced_lead_hub()

    except Exception as e:
        st.error(f"Enhanced Lead Intelligence temporarily unavailable: {str(e)}")

        # Fallback interface
        st.markdown("**Quick Intelligence Overview**")
        st.info("""
        🧠 **Advanced Lead Intelligence Features:**
        - Multi-dimensional lead qualification (0-100 scoring)
        - Real-time conversation intelligence with sentiment analysis
        - Predictive analytics for conversion probability
        - AI-powered follow-up recommendations
        - Advanced pattern recognition for buying signals and objections
        - Comprehensive analytics and insights dashboard
        """)

        st.markdown("**System Status:** Initializing enhanced intelligence features...")