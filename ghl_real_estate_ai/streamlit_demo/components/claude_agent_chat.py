"""
Claude Agent Chat Interface

Interactive conversational interface for real estate agents to chat with Claude
about leads, get insights, and receive AI-powered recommendations.
"""

import streamlit as st
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# Import the Claude Agent Service
try:
    from ...services.claude_agent_service import (
        claude_agent_service,
        chat_with_claude,
        get_claude_lead_insights,
        get_claude_follow_up_actions
    )
    from ...services.lead_intelligence_integration import get_lead_analytics
except ImportError:
    # Fallback for demo mode
    claude_agent_service = None


def render_claude_agent_interface():
    """
    Render the main Claude Agent chat interface for real estate agents.

    Provides conversational AI interaction for lead intelligence, insights,
    and property recommendations.
    """

    st.markdown("### 🤖 Claude AI Assistant")
    st.markdown("*Get instant insights about your leads and personalized recommendations*")

    # Initialize session state for chat
    if 'claude_chat_history' not in st.session_state:
        st.session_state.claude_chat_history = []
    if 'current_agent_id' not in st.session_state:
        st.session_state.current_agent_id = "agent_001"
    if 'selected_lead_for_chat' not in st.session_state:
        st.session_state.selected_lead_for_chat = None

    # Agent and Lead Selection
    col_agent, col_lead = st.columns([1, 1])

    with col_agent:
        agent_id = st.text_input(
            "Agent ID",
            value=st.session_state.current_agent_id,
            help="Your unique agent identifier"
        )
        st.session_state.current_agent_id = agent_id

    with col_lead:
        # Lead selection (optional - for focused queries)
        lead_options = ["All Leads"] + get_sample_lead_options()
        selected_lead = st.selectbox(
            "Focus on specific lead",
            lead_options,
            help="Select a specific lead for targeted insights"
        )
        if selected_lead != "All Leads":
            st.session_state.selected_lead_for_chat = selected_lead
        else:
            st.session_state.selected_lead_for_chat = None

    st.markdown("---")

    # Quick Action Buttons
    st.markdown("#### ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔥 Hot Leads", help="Show me my highest priority leads"):
            quick_query = "Show me all hot leads (80+ score) and what makes them high priority. What should I focus on with each?"
            handle_quick_query(agent_id, quick_query)

    with col2:
        if st.button("📞 Follow-up Due", help="Who needs immediate follow-up"):
            quick_query = "Which leads need immediate follow-up today? Give me specific actions for each."
            handle_quick_query(agent_id, quick_query)

    with col3:
        if st.button("🏠 Property Matches", help="Find property opportunities"):
            quick_query = "Analyze my active leads and suggest the best property matches or market opportunities I should present."
            handle_quick_query(agent_id, quick_query)

    with col4:
        if st.button("📊 Daily Summary", help="Get your daily lead summary"):
            quick_query = "Give me a comprehensive daily summary of my lead portfolio. What are today's priorities?"
            handle_quick_query(agent_id, quick_query)

    st.markdown("---")

    # Chat Interface
    st.markdown("#### 💬 Chat with Claude")

    # Chat container with scrollable history
    chat_container = st.container()

    with chat_container:
        # Display chat history
        for i, message in enumerate(st.session_state.claude_chat_history):
            if message["role"] == "user":
                st.markdown(f"""
                <div style='background: #f0f9ff; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid #3b82f6;'>
                    <div style='font-weight: 600; color: #1e40af; margin-bottom: 0.5rem;'>👤 You</div>
                    <div style='color: #1e293b;'>{message['content']}</div>
                    <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.5rem;'>{message['timestamp']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Claude response with structured formatting
                response_data = message.get('structured_data', {})

                st.markdown(f"""
                <div style='background: #f8fafc; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid #10b981;'>
                    <div style='font-weight: 600; color: #059669; margin-bottom: 0.5rem;'>🤖 Claude AI</div>
                    <div style='color: #1e293b; margin-bottom: 1rem;'>{message['content']}</div>
                """, unsafe_allow_html=True)

                # Show insights if available
                if response_data.get('insights'):
                    st.markdown("**💡 Key Insights:**")
                    for insight in response_data['insights']:
                        st.markdown(f"• {insight}")

                # Show recommendations if available
                if response_data.get('recommendations'):
                    st.markdown("**⚡ Recommendations:**")
                    for rec in response_data['recommendations']:
                        st.markdown(f"• {rec}")

                # Show follow-up questions if available
                if response_data.get('follow_up_questions'):
                    st.markdown("**❓ Follow-up Questions:**")
                    for question in response_data['follow_up_questions']:
                        if st.button(f"🔍 {question}", key=f"followup_{i}_{hash(question)}"):
                            handle_quick_query(agent_id, question)

                st.markdown(f"""
                    <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.5rem;'>{message['timestamp']}</div>
                </div>
                """, unsafe_allow_html=True)

    # Chat input
    st.markdown("#### 💭 Ask Claude anything about your leads...")

    # Text input for questions
    user_input = st.text_area(
        "Your question",
        height=100,
        placeholder="Examples:\n• How should I prioritize my leads today?\n• What's the best approach for lead_123?\n• Which properties should I show to high-budget leads?\n• Give me talking points for my 2pm call",
        label_visibility="collapsed"
    )

    col_send, col_clear = st.columns([1, 1])

    with col_send:
        if st.button("🚀 Send Message", type="primary", disabled=not user_input.strip()):
            if user_input.strip():
                handle_user_query(agent_id, user_input.strip(), st.session_state.selected_lead_for_chat)

    with col_clear:
        if st.button("🗑️ Clear Chat"):
            st.session_state.claude_chat_history = []
            st.rerun()

    # Agent Statistics Sidebar
    with st.sidebar:
        st.markdown("### 📊 Agent Activity")

        if claude_agent_service:
            try:
                stats = claude_agent_service.get_agent_stats(agent_id)

                st.metric("Total Conversations", stats.get('total_conversations', 0))
                st.metric("Active Leads", stats.get('active_leads', 0))

                status = stats.get('status', 'unknown')
                status_color = "#10b981" if status == "active" else "#f59e0b"
                st.markdown(f"""
                <div style='padding: 0.5rem; background: {status_color}15; border-radius: 8px; border: 1px solid {status_color}50;'>
                    <div style='color: {status_color}; font-weight: 600;'>Status: {status.title()}</div>
                    <div style='font-size: 0.8rem; color: #64748b;'>Last activity: {stats.get('last_activity', 'Never')}</div>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.warning(f"Could not load agent stats: {str(e)}")

        st.markdown("### 🎯 Quick Lead Actions")

        if st.session_state.selected_lead_for_chat:
            lead_id = st.session_state.selected_lead_for_chat

            if st.button("🔍 Deep Analysis", key="deep_analysis"):
                query = f"Give me a complete analysis of {lead_id}. Include behavior patterns, conversion probability, best approach, and optimal timing for next contact."
                handle_quick_query(agent_id, query)

            if st.button("📋 Action Plan", key="action_plan"):
                query = f"Create a detailed action plan for {lead_id}. What should I do in the next 24 hours, next week, and next month?"
                handle_quick_query(agent_id, query)

            if st.button("🏠 Property Strategy", key="property_strategy"):
                query = f"Based on {lead_id}'s profile, what properties should I focus on? Give me a property presentation strategy."
                handle_quick_query(agent_id, query)


def handle_user_query(agent_id: str, query: str, lead_id: Optional[str] = None):
    """Handle a user query and get Claude's response"""

    if not claude_agent_service:
        # Demo mode response
        demo_response = generate_demo_response(query, lead_id)
        add_message_to_chat("user", query)
        add_message_to_chat("assistant", demo_response['response'], demo_response)
        st.rerun()
        return

    try:
        # Show processing spinner
        with st.spinner("Claude is analyzing..."):
            # Use asyncio to run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                chat_with_claude(agent_id, query, lead_id)
            )
            loop.close()

        # Add messages to chat history
        add_message_to_chat("user", query)
        add_message_to_chat("assistant", response.response, {
            'insights': response.insights,
            'recommendations': response.recommendations,
            'follow_up_questions': response.follow_up_questions,
            'confidence': response.confidence
        })

        # Success toast
        st.toast("✅ Response generated!", icon="🎉")
        st.rerun()

    except Exception as e:
        st.error(f"Error getting Claude response: {str(e)}")
        add_message_to_chat("user", query)
        add_message_to_chat("assistant", "I apologize, but I encountered an error. Please try again.", {})
        st.rerun()


def handle_quick_query(agent_id: str, query: str):
    """Handle quick action queries"""
    handle_user_query(agent_id, query, st.session_state.selected_lead_for_chat)


def add_message_to_chat(role: str, content: str, structured_data: Optional[Dict] = None):
    """Add a message to the chat history"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "structured_data": structured_data or {}
    }
    st.session_state.claude_chat_history.append(message)


def get_sample_lead_options() -> List[str]:
    """Get sample lead options for the dropdown"""
    return [
        "lead_001 (Sarah Johnson)",
        "lead_002 (Mike Chen)",
        "lead_003 (Emily Davis)",
        "lead_004 (Robert Wilson)",
        "lead_005 (Lisa Anderson)"
    ]


def generate_demo_response(query: str, lead_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate a demo response when Claude service is not available"""

    if "hot leads" in query.lower():
        return {
            "response": "I've identified 3 hot leads in your pipeline that need immediate attention. Sarah Johnson (score: 92) is actively looking for luxury properties in Austin with a $800k budget - she's engaged and ready to move quickly. Mike Chen (score: 85) has been consistently responding and viewing listings in the $450k range. Emily Rodriguez (score: 81) just submitted a pre-approval letter and is looking to close within 30 days.",
            "insights": [
                "Sarah Johnson shows highest engagement with luxury listings",
                "Mike Chen responds fastest to SMS communications",
                "Emily Rodriguez has financing pre-approved - ready to close"
            ],
            "recommendations": [
                "Call Sarah within 2 hours - she's actively browsing",
                "Send Mike 3 curated property options via text"
            ],
            "follow_up_questions": [
                "Which lead would you like to focus on first?",
                "Do you want specific talking points for any of these calls?"
            ]
        }
    elif "follow-up" in query.lower():
        return {
            "response": "You have 4 leads requiring follow-up today. Sarah Johnson hasn't responded to your property suggestions from yesterday - try a different approach with market insights. Mike Chen asked about neighborhood schools 2 days ago but no follow-up sent. Emily Davis requested a showing but scheduling is pending. Robert Wilson needs budget re-qualification based on his recent inquiries.",
            "insights": [
                "Sarah may need value-focused messaging instead of features",
                "Mike's school question indicates family priorities",
                "Emily is the warmest lead for immediate conversion"
            ],
            "recommendations": [
                "Schedule Emily's showing first - highest conversion probability",
                "Send Mike school district report for target neighborhoods"
            ],
            "follow_up_questions": [
                "What time works best for Emily's showing?",
                "Should I prepare school district analysis for Mike?"
            ]
        }
    else:
        return {
            "response": f"I've analyzed your query about '{query}'. Based on current lead data, here's what I recommend focusing on. Your lead pipeline shows strong activity with several high-priority prospects requiring strategic follow-up approaches.",
            "insights": [
                "Multiple leads in qualification phase",
                "Strong engagement patterns in luxury segment",
                "Follow-up timing is critical for conversion"
            ],
            "recommendations": [
                "Prioritize warm leads with immediate timeline",
                "Focus on value proposition for budget-conscious prospects"
            ],
            "follow_up_questions": [
                "Would you like me to elaborate on any specific lead?",
                "What's your biggest challenge with current leads?"
            ]
        }


# Convenience function for external use
def render_claude_chat_interface():
    """External interface function"""
    render_claude_agent_interface()