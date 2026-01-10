"""
Enhanced Lead Intelligence Hub Integration

Integration module that brings together all enhanced AI components:
- Lead Evaluation Orchestrator
- Claude Semantic Analyzer
- Agent Assistance Dashboard
- Qualification Tracker
- Enhanced Chatbot Integration

This module provides a comprehensive enhanced interface for the demo.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

import streamlit as st
import pandas as pd

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import enhanced components
try:
    from services.enhanced_chatbot_integration import (
        EnhancedChatbotIntegration,
        EnhancedChatConfig,
        render_enhanced_lead_chat
    )
    from streamlit_components.agent_assistance_dashboard import (
        AgentAssistanceDashboard,
        create_agent_dashboard
    )
    from streamlit_components.qualification_tracker import (
        QualificationTracker,
        create_qualification_tracker
    )
    from streamlit_components.nurturing_campaign_manager import (
        NurturingCampaignManager
    )
    from services.lead_nurturing_agent import LeadNurturingAgent
    from services.nurturing_trigger_integration import NurturingTriggerIntegration
    from models.evaluation_models import (
        LeadEvaluationResult,
        ScoringBreakdown,
        QualificationProgress,
        AgentAssistanceData,
        RecommendedAction,
        SentimentType,
        EngagementLevel,
        ActionPriority
    )
    from models.nurturing_models import (
        NurturingCampaign,
        LeadType,
        CampaignStatus
    )
    ENHANCED_COMPONENTS_AVAILABLE = True
    NURTURING_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced components not available: {e}")
    ENHANCED_COMPONENTS_AVAILABLE = False
    NURTURING_COMPONENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


def render_enhanced_lead_intelligence_hub():
    """
    Render the enhanced Lead Intelligence Hub with all AI-powered features.
    """
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    ">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">
            🧠 Enhanced Lead Intelligence Hub
        </h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            AI-Powered Lead Evaluation with Real-Time Agent Assistance
        </p>
        <div style="
            background: rgba(255,255,255,0.2);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            display: inline-block;
            margin-top: 1rem;
            font-size: 0.9rem;
        ">
            🚀 Enhanced AI • 💬 Smart Chat • 📊 Real-Time Analytics • 🎯 Qualification Tracking
        </div>
    </div>
    """, unsafe_allow_html=True)

    # System status check
    if not ENHANCED_COMPONENTS_AVAILABLE:
        st.error("🚫 Enhanced components not available. Please check the installation.")
        render_fallback_interface()
        return

    # Enhanced features status
    st.success("✅ Enhanced AI Components Loaded Successfully!")

    # Lead selector
    lead_options = get_demo_lead_options()

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        selected_lead = st.selectbox(
            "🎯 Select Lead for Analysis",
            options=list(lead_options.keys()),
            index=0,
            help="Choose a lead to analyze with enhanced AI features"
        )

    with col2:
        demo_mode = st.selectbox(
            "🔧 Demo Mode",
            ["Full Demo", "Chat Only", "Analytics Only"],
            index=0
        )

    with col3:
        if st.button("🔄 Refresh Analysis", type="primary"):
            st.session_state.enhanced_evaluation_cache = {}
            st.toast("Analysis refreshed!")

    # Get lead data
    lead_data = lead_options[selected_lead]

    st.markdown("---")

    # Main interface based on demo mode
    if demo_mode == "Full Demo":
        render_full_enhanced_demo(selected_lead, lead_data)
    elif demo_mode == "Chat Only":
        render_enhanced_chat_demo(selected_lead, lead_data)
    else:
        render_analytics_demo(selected_lead, lead_data)


def render_full_enhanced_demo(lead_name: str, lead_data: Dict[str, Any]):
    """Render the full enhanced demo with all components."""

    # Create tabs for different features
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🤖 Enhanced Chat",
        "📊 Live Analytics",
        "📋 Qualification Tracker",
        "🎯 Agent Dashboard",
        "🎯 Nurturing Campaigns",
        "📈 Performance Metrics"
    ])

    with tab1:
        render_enhanced_chat_demo(lead_name, lead_data)

    with tab2:
        render_live_analytics_demo(lead_name, lead_data)

    with tab3:
        render_qualification_demo(lead_name, lead_data)

    with tab4:
        render_agent_dashboard_demo(lead_name, lead_data)

    with tab5:
        render_nurturing_campaigns_demo(lead_name, lead_data)

    with tab6:
        render_performance_metrics_demo()


def render_enhanced_chat_demo(lead_name: str, lead_data: Dict[str, Any]):
    """Render enhanced chat interface demo."""
    st.markdown("### 💬 Enhanced AI Conversation Assistant")

    # Chat configuration
    st.markdown("#### ⚙️ AI Assistant Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        enable_real_time = st.checkbox("🔄 Real-time Analysis", value=True)
    with col2:
        enable_objection_detection = st.checkbox("⚠️ Objection Detection", value=True)
    with col3:
        enable_suggestions = st.checkbox("💡 Response Suggestions", value=True)

    if enable_real_time:
        st.info("🚀 Real-time lead evaluation and conversation analysis active")

    # Demo conversation interface
    render_demo_conversation_interface(lead_name, lead_data, {
        'real_time': enable_real_time,
        'objection_detection': enable_objection_detection,
        'suggestions': enable_suggestions
    })


def render_demo_conversation_interface(
    lead_name: str,
    lead_data: Dict[str, Any],
    config: Dict[str, bool]
):
    """Render the demo conversation interface."""

    # Initialize conversation state
    conv_key = f"conv_{lead_name}"
    if conv_key not in st.session_state:
        st.session_state[conv_key] = []

    # Chat container
    chat_container = st.container()

    # Demo conversation history
    if not st.session_state[conv_key]:
        # Initialize with sample conversation
        st.session_state[conv_key] = [
            {
                "role": "agent",
                "content": f"Hi {lead_name}! I understand you're interested in finding a home. What brings you to the market?",
                "timestamp": datetime.now()
            },
            {
                "role": "prospect",
                "content": "Hi! Yes, we're looking to buy our first home. We've been renting for a few years but ready to own.",
                "timestamp": datetime.now()
            },
            {
                "role": "agent",
                "content": "That's exciting! Congratulations on taking this big step. What's your ideal budget range for your first home?",
                "timestamp": datetime.now()
            }
        ]

    # Display conversation
    with chat_container:
        for message in st.session_state[conv_key]:
            render_chat_message_demo(message)

    # Real-time analysis (if enabled)
    if config['real_time']:
        render_real_time_analysis_demo(lead_name, st.session_state[conv_key])

    # Message input
    st.markdown("---")

    col_input, col_send = st.columns([4, 1])

    with col_input:
        new_message = st.text_input(
            "Your response:",
            key=f"input_{conv_key}",
            placeholder="Type your response to the prospect..."
        )

    with col_send:
        if st.button("📤 Send", key=f"send_{conv_key}"):
            if new_message.strip():
                # Add agent message
                st.session_state[conv_key].append({
                    "role": "agent",
                    "content": new_message,
                    "timestamp": datetime.now()
                })

                # Simulate prospect response
                prospect_responses = [
                    "We're looking at homes around $400k to $500k.",
                    "That sounds reasonable, but we're worried about the market being overpriced.",
                    "We need at least 3 bedrooms and prefer a good school district.",
                    "Timeline-wise, we'd like to be in our new home by summer.",
                    "We have some concerns about the buying process being too complicated."
                ]

                import random
                st.session_state[conv_key].append({
                    "role": "prospect",
                    "content": random.choice(prospect_responses),
                    "timestamp": datetime.now()
                })

                st.rerun()

    # Quick response buttons (if suggestions enabled)
    if config['suggestions']:
        render_quick_responses_demo()


def render_chat_message_demo(message: Dict[str, Any]):
    """Render individual chat message with enhanced styling."""
    role = message["role"]
    content = message["content"]
    timestamp = message["timestamp"]

    if role == "agent":
        bg_color = "#E0F2FE"
        align = "right"
        icon = "👨‍💼"
        name = "Agent"
    else:
        bg_color = "#F0F9FF"
        align = "left"
        icon = "👤"
        name = "Prospect"

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


def render_real_time_analysis_demo(lead_name: str, conversation: List[Dict[str, Any]]):
    """Render real-time conversation analysis."""

    with st.sidebar:
        st.markdown("### 🔄 Real-Time Analysis")

        # Mock evaluation based on conversation
        analysis = generate_mock_analysis(conversation)

        # Lead score
        st.metric("Lead Score", f"{analysis['score']:.1f}", delta=f"+{analysis['score_change']:.1f}")

        # Sentiment
        sentiment_color = get_sentiment_color(analysis['sentiment'])
        st.markdown(f"""
        <div style="
            background: {sentiment_color}15;
            border: 1px solid {sentiment_color};
            padding: 0.5rem;
            border-radius: 8px;
            text-align: center;
            margin: 0.5rem 0;
        ">
            <strong style="color: {sentiment_color};">
                {analysis['sentiment_icon']} {analysis['sentiment']}
            </strong>
        </div>
        """, unsafe_allow_html=True)

        # Objection alerts
        if analysis['objections']:
            st.markdown("#### ⚠️ Detected Concerns")
            for objection in analysis['objections']:
                st.warning(f"**{objection['type']}**: {objection['text']}")

        # Suggestions
        st.markdown("#### 💡 Suggestions")
        for suggestion in analysis['suggestions'][:3]:
            st.markdown(f"• {suggestion}")


def render_quick_responses_demo():
    """Render quick response suggestions."""
    st.markdown("#### 🚀 Quick Responses")

    col1, col2 = st.columns(2)

    quick_responses = [
        "That's a great budget range for this market!",
        "Let me show you some properties in your area.",
        "Would you like to schedule a showing?",
        "What neighborhoods interest you most?"
    ]

    for i, response in enumerate(quick_responses):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(f"💬 {response[:30]}...", key=f"quick_{i}"):
                st.success(f"Selected: {response}")


def render_live_analytics_demo(lead_name: str, lead_data: Dict[str, Any]):
    """Render live analytics demonstration."""
    st.markdown("### 📊 Live Lead Analytics")

    # Generate comprehensive mock evaluation
    evaluation_result = generate_comprehensive_mock_evaluation(lead_name, lead_data)

    # Use our agent assistance dashboard
    try:
        dashboard = create_agent_dashboard()
        dashboard.render_main_dashboard(
            evaluation_result=evaluation_result,
            live_mode=True
        )
    except Exception as e:
        st.error(f"Dashboard error: {e}")
        render_fallback_analytics(evaluation_result)


def render_qualification_demo(lead_name: str, lead_data: Dict[str, Any]):
    """Render qualification tracker demonstration."""
    st.markdown("### 📋 Qualification Progress Tracker")

    # Generate mock evaluation for qualification
    evaluation_result = generate_comprehensive_mock_evaluation(lead_name, lead_data)

    try:
        tracker = create_qualification_tracker()
        tracker.render_qualification_tracker(
            lead_id=lead_name.lower().replace(" ", "_"),
            lead_data=lead_data,
            evaluation_result=evaluation_result
        )
    except Exception as e:
        st.error(f"Qualification tracker error: {e}")
        render_fallback_qualification()


def render_agent_dashboard_demo(lead_name: str, lead_data: Dict[str, Any]):
    """Render agent dashboard demonstration."""
    st.markdown("### 🎯 Agent Intelligence Dashboard")

    evaluation_result = generate_comprehensive_mock_evaluation(lead_name, lead_data)

    # Real-time metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Conversation Score", "8.5/10", "+0.5")
    with col2:
        st.metric("Rapport Level", "High", "+1")
    with col3:
        st.metric("Qualification", "75%", "+15%")
    with col4:
        st.metric("Next Action", "Schedule", "Priority: High")

    # Detailed dashboard
    try:
        dashboard = create_agent_dashboard()

        # Render specific dashboard components
        col1, col2 = st.columns(2)

        with col1:
            dashboard._render_lead_score_card(evaluation_result)
            dashboard._render_qualification_progress(evaluation_result.qualification_progress)

        with col2:
            dashboard._render_conversation_analysis(evaluation_result.agent_assistance)
            dashboard._render_recommended_actions(evaluation_result.recommended_actions)

    except Exception as e:
        st.error(f"Agent dashboard error: {e}")


def render_nurturing_campaigns_demo(lead_name: str, lead_data: Dict[str, Any]):
    """Render nurturing campaigns demonstration."""
    st.markdown("### 🎯 Automated Lead Nurturing Campaign Management")

    if not NURTURING_COMPONENTS_AVAILABLE:
        st.warning("⚠️ Nurturing components not available. Showing preview interface.")
        render_nurturing_preview(lead_name, lead_data)
        return

    try:
        # Initialize nurturing campaign manager
        campaign_manager = NurturingCampaignManager()

        # Demo header with campaign status for current lead
        render_nurturing_demo_header(lead_name, lead_data)

        # Main nurturing interface
        campaign_manager.render()

        # Lead-specific nurturing actions
        render_lead_specific_nurturing_actions(lead_name, lead_data)

    except Exception as e:
        st.error(f"Nurturing campaign error: {str(e)}")
        render_nurturing_preview(lead_name, lead_data)


def render_nurturing_demo_header(lead_name: str, lead_data: Dict[str, Any]):
    """Render demo header for nurturing campaigns."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1a365d 0%, #2c5aa0 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    ">
        <h3 style="margin: 0; color: white;">🎯 Campaign Status for {lead_name}</h3>
        <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        ">
            <div>
                <strong>Campaign:</strong><br/>
                <span style="color: #a0c4ff;">First-Time Buyer Journey</span>
            </div>
            <div>
                <strong>Status:</strong><br/>
                <span style="color: #48bb78;">✅ Active</span>
            </div>
            <div>
                <strong>Progress:</strong><br/>
                <span style="color: #a0c4ff;">Step 2 of 5</span>
            </div>
            <div>
                <strong>Next Action:</strong><br/>
                <span style="color: #fbbf24;">📧 Tomorrow 2:00 PM</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_lead_specific_nurturing_actions(lead_name: str, lead_data: Dict[str, Any]):
    """Render lead-specific nurturing actions."""
    st.markdown("### 🚀 Lead-Specific Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(f"🎯 Enroll {lead_name} in Premium Sequence", type="primary"):
            st.success(f"✅ {lead_name} enrolled in Luxury Buyer sequence!")

    with col2:
        if st.button("⚡ Send Immediate Follow-up"):
            st.success("📧 Immediate follow-up message sent!")

    with col3:
        if st.button("⏸️ Pause Current Campaign"):
            st.warning("Campaign paused. Resume anytime.")

    # Enrollment recommendations
    st.markdown("#### 💡 AI Enrollment Recommendations")

    evaluation_result = generate_comprehensive_mock_evaluation(lead_name, lead_data)
    score = evaluation_result.scoring_breakdown.composite_score

    if score > 85:
        recommended_sequence = "Luxury Buyer Experience"
        priority = "HIGH"
        color = "#10B981"
    elif score > 70:
        recommended_sequence = "First-Time Buyer Journey"
        priority = "MEDIUM"
        color = "#F59E0B"
    else:
        recommended_sequence = "Re-engagement Sequence"
        priority = "LOW"
        color = "#6B7280"

    st.markdown(f"""
    <div style="
        background: {color}15;
        border: 1px solid {color};
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    ">
        <h5 style="color: {color}; margin-top: 0;">
            Recommended: {recommended_sequence}
        </h5>
        <p style="margin-bottom: 0;">
            Based on lead score of {score:.1f}, this sequence has a
            <strong>{85 if score > 85 else 65}% predicted success rate</strong> for this lead type.
        </p>
        <small style="color: {color};">Priority: {priority}</small>
    </div>
    """, unsafe_allow_html=True)


def render_nurturing_preview(lead_name: str, lead_data: Dict[str, Any]):
    """Render preview when nurturing components aren't available."""
    st.markdown("### 🎯 Lead Nurturing Campaign Preview")

    st.info("🚀 **Coming Soon**: Automated lead nurturing with personalized follow-up sequences!")

    # Mock campaign data
    st.markdown("#### 📊 Example Campaign Performance")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Campaigns", "42", "+8")
    with col2:
        st.metric("Response Rate", "34.7%", "+4.2%")
    with col3:
        st.metric("Engagement Score", "8.5/10", "+0.3")
    with col4:
        st.metric("Conversions", "23", "+5")

    # Example sequence
    st.markdown("#### 📋 Example: First-Time Buyer Sequence")

    sequence_steps = [
        {"step": 1, "delay": "2 hours", "action": "Welcome & Education Email", "response_rate": "42%"},
        {"step": 2, "delay": "1 day", "action": "Buying Process Guide", "response_rate": "38%"},
        {"step": 3, "delay": "3 days", "action": "Pre-qualification SMS", "response_rate": "29%"},
        {"step": 4, "delay": "5 days", "action": "Property Matches", "response_rate": "45%"},
        {"step": 5, "delay": "1 week", "action": "Market Insights", "response_rate": "31%"}
    ]

    for step in sequence_steps:
        col1, col2, col3, col4 = st.columns([1, 2, 3, 1])

        with col1:
            st.write(f"**Step {step['step']}**")
        with col2:
            st.write(step['delay'])
        with col3:
            st.write(step['action'])
        with col4:
            st.write(step['response_rate'])


def render_performance_metrics_demo():
    """Render system performance metrics."""
    st.markdown("### 📈 System Performance Metrics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎯 AI Performance")
        st.metric("Evaluation Speed", "245ms", "-15ms")
        st.metric("Accuracy Score", "94.2%", "+1.2%")
        st.metric("Cache Hit Rate", "87%", "+5%")

    with col2:
        st.markdown("#### 📊 Usage Statistics")
        st.metric("Conversations Today", "47", "+12")
        st.metric("Objections Detected", "18", "+3")
        st.metric("Successful Qualifications", "23", "+8")

    # Add nurturing metrics if available
    if NURTURING_COMPONENTS_AVAILABLE:
        st.markdown("#### 🎯 Nurturing Performance")

        col3, col4 = st.columns(2)

        with col3:
            st.metric("Active Campaigns", "42", "+8")
            st.metric("Response Rate", "34.7%", "+4.2%")

        with col4:
            st.metric("Engagement Score", "8.5/10", "+0.3")
            st.metric("Campaign Completions", "23", "+5")

    # Performance charts
    render_performance_charts()


def render_performance_charts():
    """Render performance visualization charts."""
    import plotly.graph_objects as go

    # Response time chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(10)),
        y=[250, 230, 245, 220, 235, 215, 240, 225, 230, 210],
        mode='lines+markers',
        name='Response Time (ms)',
        line=dict(color='#3B82F6')
    ))

    fig.update_layout(
        title="AI Response Time Trend",
        xaxis_title="Time",
        yaxis_title="Response Time (ms)",
        height=300
    )

    st.plotly_chart(fig, width='stretch')


def generate_mock_analysis(conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate mock real-time analysis."""
    message_count = len(conversation)

    # Calculate mock score based on conversation length and content
    base_score = min(40 + (message_count * 8), 95)

    # Check for positive indicators
    all_text = " ".join([msg.get("content", "") for msg in conversation]).lower()

    if "budget" in all_text or "afford" in all_text:
        base_score += 5
    if "timeline" in all_text or "when" in all_text:
        base_score += 5
    if "interested" in all_text or "excited" in all_text:
        base_score += 3

    # Detect objections
    objections = []
    if "expensive" in all_text or "overpriced" in all_text:
        objections.append({
            "type": "Price Concern",
            "text": "Prospect mentioned price concerns"
        })
    if "complicated" in all_text or "worried" in all_text:
        objections.append({
            "type": "Process Concern",
            "text": "Prospect has process-related concerns"
        })

    # Determine sentiment
    if "excited" in all_text or "great" in all_text:
        sentiment = "Positive"
        sentiment_icon = "😊"
    elif "worried" in all_text or "concerned" in all_text:
        sentiment = "Concerned"
        sentiment_icon = "😟"
    else:
        sentiment = "Neutral"
        sentiment_icon = "😐"

    return {
        'score': base_score,
        'score_change': 2.5,
        'sentiment': sentiment,
        'sentiment_icon': sentiment_icon,
        'objections': objections,
        'suggestions': [
            "Ask about specific neighborhoods of interest",
            "Discuss pre-approval status",
            "Suggest scheduling a property showing",
            "Address any concerns about the market"
        ]
    }


def generate_comprehensive_mock_evaluation(lead_name: str, lead_data: Dict[str, Any]) -> LeadEvaluationResult:
    """Generate comprehensive mock evaluation result."""

    # Create mock scoring breakdown
    scoring_breakdown = ScoringBreakdown(
        basic_rules_score=85.0,
        advanced_intelligence_score=78.0,
        predictive_ml_score=82.0,
        urgency_detection_score=75.0,
        budget_alignment=88.0,
        location_preference=76.0,
        timeline_urgency=80.0,
        engagement_level=92.0,
        communication_quality=85.0,
        qualification_completeness=65.0,
        composite_score=82.5,
        confidence_interval=(78.0, 87.0)
    )

    # Create qualification progress
    qualification_progress = QualificationProgress(
        total_fields=15,
        completed_fields=9,
        partial_fields=3,
        missing_fields=3,
        completion_percentage=65.0,
        critical_fields_complete=True,
        qualification_tier="warm_lead",
        next_priority_fields=["square_footage", "timeline", "motivation"]
    )

    # Create agent assistance data
    agent_assistance = AgentAssistanceData(
        current_sentiment=SentimentType.POSITIVE,
        engagement_level=EngagementLevel.ENGAGED,
        conversation_flow_stage="qualification",
        qualification_gaps=["timeline", "specific_location"],
        suggested_questions=[
            "What's your ideal timeline for purchasing?",
            "Which neighborhoods appeal to you most?",
            "Have you been pre-approved for financing?"
        ],
        conversation_effectiveness=8.5,
        rapport_building_score=9.2,
        information_gathering_rate=7.8
    )

    # Create recommended actions
    recommended_actions = [
        RecommendedAction(
            action_type="schedule_showing",
            priority=ActionPriority.HIGH,
            description="Schedule property showing for this weekend",
            reasoning="Lead is highly engaged and qualified",
            confidence=0.9,
            estimated_duration=15
        ),
        RecommendedAction(
            action_type="gather_financing_info",
            priority=ActionPriority.MEDIUM,
            description="Confirm pre-approval status",
            reasoning="Financial qualification needs verification",
            confidence=0.7,
            estimated_duration=10
        )
    ]

    return LeadEvaluationResult(
        lead_id=lead_name.lower().replace(" ", "_"),
        evaluation_id=f"eval_{int(time.time())}",
        scoring_breakdown=scoring_breakdown,
        qualification_progress=qualification_progress,
        qualification_fields={},
        agent_assistance=agent_assistance,
        recommended_actions=recommended_actions,
        evaluation_duration_ms=180,
        confidence_score=0.88,
        data_freshness_score=0.95,
        evaluation_quality_score=0.91
    )


def get_demo_lead_options() -> Dict[str, Dict[str, Any]]:
    """Get demo lead options for testing."""
    return {
        "Sarah Chen": {
            "id": "lead_001",
            "phone": "+1-555-0101",
            "email": "sarah.chen@email.com",
            "budget": "$450,000 - $550,000",
            "property_type": "Single Family Home",
            "location": "Westfield, Downtown area",
            "timeline": "3-4 months",
            "status": "Hot Lead",
            "score": 87.5,
            "notes": ["First-time buyer", "Pre-approved", "Flexible on location"]
        },
        "Michael Rodriguez": {
            "id": "lead_002",
            "phone": "+1-555-0102",
            "email": "m.rodriguez@email.com",
            "budget": "$300,000 - $400,000",
            "property_type": "Condo or Townhome",
            "location": "Near public transit",
            "timeline": "6-8 months",
            "status": "Warm Lead",
            "score": 72.0,
            "notes": ["Young professional", "Concerned about commute", "Budget conscious"]
        },
        "Jennifer & David Park": {
            "id": "lead_003",
            "phone": "+1-555-0103",
            "email": "parkfamily@email.com",
            "budget": "$600,000 - $750,000",
            "property_type": "Single Family Home",
            "location": "Good school district",
            "timeline": "ASAP",
            "status": "Hot Lead",
            "score": 93.2,
            "notes": ["Growing family", "Need 4+ bedrooms", "Cash buyers", "School district priority"]
        }
    }


def get_sentiment_color(sentiment: str) -> str:
    """Get color for sentiment display."""
    sentiment_colors = {
        "Positive": "#10B981",
        "Neutral": "#6B7280",
        "Concerned": "#F59E0B",
        "Negative": "#EF4444"
    }
    return sentiment_colors.get(sentiment, "#6B7280")


def render_fallback_interface():
    """Render fallback interface when enhanced components aren't available."""
    st.warning("⚠️ Enhanced AI components not available. Showing standard interface.")

    st.markdown("### 🎯 Standard Lead Analysis")

    # Basic lead selector
    leads = get_demo_lead_options()
    selected_lead = st.selectbox("Select Lead", list(leads.keys()))

    lead_data = leads[selected_lead]

    # Basic metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Lead Score", lead_data['score'])
    with col2:
        st.metric("Status", lead_data['status'])
    with col3:
        st.metric("Timeline", lead_data['timeline'])

    # Lead details
    st.markdown("#### 📋 Lead Details")
    for key, value in lead_data.items():
        if key not in ['id', 'score', 'status']:
            st.text(f"{key.title()}: {value}")


def render_fallback_analytics(evaluation_result: LeadEvaluationResult):
    """Render fallback analytics when dashboard fails."""
    st.markdown("#### 📊 Basic Analytics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Lead Score", f"{evaluation_result.scoring_breakdown.composite_score:.1f}")
    with col2:
        st.metric("Qualification", f"{evaluation_result.qualification_progress.completion_percentage:.1f}%")
    with col3:
        st.metric("Actions", len(evaluation_result.recommended_actions))


def render_fallback_qualification():
    """Render fallback qualification interface."""
    st.markdown("#### 📋 Basic Qualification")

    fields = ["Budget", "Timeline", "Location", "Property Type", "Financing"]

    for field in fields:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(field, key=f"qual_{field}")
        with col2:
            st.checkbox("✓", key=f"complete_{field}")


# Test function for validation
def test_enhanced_components():
    """Test all enhanced components for functionality."""
    st.markdown("### 🧪 Component Testing")

    test_results = {}

    # Test imports
    try:
        from services.enhanced_chatbot_integration import EnhancedChatbotIntegration
        test_results['chatbot_integration'] = "✅ Available"
    except Exception as e:
        test_results['chatbot_integration'] = f"❌ Error: {str(e)}"

    try:
        from streamlit_components.agent_assistance_dashboard import AgentAssistanceDashboard
        test_results['agent_dashboard'] = "✅ Available"
    except Exception as e:
        test_results['agent_dashboard'] = f"❌ Error: {str(e)}"

    try:
        from streamlit_components.qualification_tracker import QualificationTracker
        test_results['qualification_tracker'] = "✅ Available"
    except Exception as e:
        test_results['qualification_tracker'] = f"❌ Error: {str(e)}"

    try:
        from streamlit_components.nurturing_campaign_manager import NurturingCampaignManager
        test_results['nurturing_campaigns'] = "✅ Available"
    except Exception as e:
        test_results['nurturing_campaigns'] = f"❌ Error: {str(e)}"

    try:
        from services.lead_nurturing_agent import LeadNurturingAgent
        test_results['nurturing_agent'] = "✅ Available"
    except Exception as e:
        test_results['nurturing_agent'] = f"❌ Error: {str(e)}"

    # Display test results
    for component, status in test_results.items():
        st.markdown(f"**{component}**: {status}")

    return all("✅" in status for status in test_results.values())


# Main function for integration
def main():
    """Main function for testing the enhanced hub."""
    st.set_page_config(
        page_title="Enhanced Lead Intelligence Hub",
        page_icon="🧠",
        layout="wide"
    )

    render_enhanced_lead_intelligence_hub()


if __name__ == "__main__":
    main()