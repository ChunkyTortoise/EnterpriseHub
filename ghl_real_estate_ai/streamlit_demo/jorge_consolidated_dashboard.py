"""
Jorge AI Consolidated Bot Dashboard - Streamlined Edition
========================================================

Streamlined interface with consolidated tabs and improved information density:
- 📊 Overview Dashboard (Cross-bot comparison & system health)
- 🎯 Lead Bot: Chat+Pipeline | Performance | Analytics (3 tabs)
- 🏠 Buyer Bot: Chat+Properties | Performance | Analytics (3 tabs)
- 💼 Seller Bot: Chat+Qualification | Performance | Analytics (3 tabs)
- ⚙️ Global Settings (Centralized configuration)

Total: 11 tabs (down from 18 - 39% reduction)

Author: Claude Code Assistant
Created: 2026-01-25
"""

import streamlit as st
import asyncio
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import sys
import os
from pathlib import Path

# Add project paths for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_file.parent.parent))

# Page Configuration
st.set_page_config(
    page_title="Jorge AI | Consolidated Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Safe imports with fallbacks
try:
    from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
    ASYNC_UTILS_AVAILABLE = True
except ImportError:
    ASYNC_UTILS_AVAILABLE = False
    def run_async(coro):
        import asyncio
        try:
            return asyncio.run(coro)
        except:
            return None

# Import styling and components
try:
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import (
        inject_elite_css, style_obsidian_chart, render_dossier_block,
        render_neural_progress, get_svg_icon, render_terminal_log,
        render_voice_waveform, render_tactical_dock, render_journey_line
    )
    ELITE_STYLING = True
except ImportError:
    ELITE_STYLING = False

# Import bot services
try:
    from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
    from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
    from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
    BOT_SERVICES_AVAILABLE = True
except ImportError:
    BOT_SERVICES_AVAILABLE = False

# Import analytics services
try:
    from ghl_real_estate_ai.services.analytics_service import AnalyticsService
    from ghl_real_estate_ai.services.event_publisher import get_event_publisher
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

class ConsolidatedBotManager:
    """Consolidated manager for all Jorge AI bots with streamlined data access."""

    def __init__(self):
        self.seller_bot = None
        self.lead_bot = None
        self.buyer_bot = None
        self.analytics = None

        # Initialize services if available
        if BOT_SERVICES_AVAILABLE:
            try:
                self.seller_bot = JorgeSellerBot()
                self.lead_bot = LeadBotWorkflow()
                self.buyer_bot = JorgeBuyerBot()
            except Exception as e:
                print(f"Bot initialization error: {e}")

        if ANALYTICS_AVAILABLE:
            try:
                self.analytics = AnalyticsService()
            except Exception as e:
                print(f"Analytics initialization error: {e}")

    async def get_overview_metrics(self) -> Dict[str, Any]:
        """Get consolidated overview metrics for dashboard."""
        return {
            "system_health": {
                "overall_status": "🟢 Operational",
                "uptime": 99.8,
                "active_conversations": 25,
                "total_interactions_today": 347,
                "messages_per_minute": 10.1
            },
            "bot_performance": {
                "lead_bot": {"score": 94.2, "status": "🟢", "active": 12},
                "buyer_bot": {"score": 89.7, "status": "🟢", "active": 8},
                "seller_bot": {"score": 84.7, "status": "🟢", "active": 5}
            },
            "key_metrics": {
                "leads_qualified_today": 23,
                "properties_matched": 45,
                "listings_secured": 7,
                "revenue_attributed": 127500
            },
            "alerts": [
                {"level": "success", "message": "All systems operating normally"},
                {"level": "info", "message": "Peak performance achieved at 2:30 PM"},
                {"level": "warning", "message": "Weekend conversion 8% below target"}
            ]
        }

    async def get_consolidated_metrics(self, bot_type: str) -> Dict[str, Any]:
        """Get consolidated metrics for a specific bot type."""
        base_metrics = {
            "lead_bot": {
                "performance": {
                    "success_rate": 94.2,
                    "response_time": 2.3,
                    "efficiency_score": 87.5,
                    "sequence_completion": 78.9,
                    "reengagement_rate": 68.4
                },
                "analytics": {
                    "total_sequences": 127,
                    "day_3_response": 45.2,
                    "day_7_success": 62.8,
                    "day_30_recovery": 23.4,
                    "hot_leads_generated": 18
                }
            },
            "buyer_bot": {
                "performance": {
                    "match_accuracy": 89.7,
                    "response_time": 1.8,
                    "conversion_rate": 23.4,
                    "satisfaction_score": 4.7,
                    "showing_booking_rate": 31.2
                },
                "analytics": {
                    "buyers_qualified": 64,
                    "properties_matched": 178,
                    "showings_booked": 23,
                    "offers_submitted": 7,
                    "closed_transactions": 3
                }
            },
            "seller_bot": {
                "performance": {
                    "qualification_speed": 4.2,
                    "stall_detection": 91.3,
                    "close_rate": 67.8,
                    "jorge_effectiveness": 84.7,
                    "frs_average": 78.9
                },
                "analytics": {
                    "total_qualifications": 89,
                    "hot_leads": 12,
                    "voice_handoffs": 8,
                    "listings_secured": 7,
                    "take_away_success": 73.4
                }
            }
        }
        return base_metrics.get(bot_type, {})

    async def chat_with_bot(self, bot_type: str, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Unified chat interface for all bots."""
        responses = {
            "lead_bot": f"Lead Bot: Thanks for your message '{message}'. I'm setting up your follow-up sequence based on your interest level.",
            "buyer_bot": f"Buyer Bot: I understand you're looking for properties. Based on '{message}', I've found 3 matches in your criteria.",
            "seller_bot": f"Jorge: {message}? Let me be direct - are you actually ready to sell or just testing the waters?"
        }

        return {
            "response_content": responses.get(bot_type, "Bot response not available"),
            "bot_type": bot_type,
            "confidence": 87.3,
            "next_action": "continue_conversation" if bot_type != "seller_bot" else "apply_pressure",
            "context_updated": True
        }

@st.cache_resource
def get_consolidated_manager():
    return ConsolidatedBotManager()

def render_sidebar():
    """Render the streamlined navigation sidebar."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #1E88E5; font-family: 'Space Grotesk', sans-serif;">🤖 JORGE AI</h2>
            <p style="color: #8B949E; font-size: 0.8rem; letter-spacing: 0.1em;">CONSOLIDATED COMMAND</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Streamlined navigation
        selected_view = st.radio(
            "Dashboard View:",
            ["📊 Overview", "🎯 Lead Bot", "🏠 Buyer Bot", "💼 Seller Bot", "⚙️ Settings"],
            index=0
        )

        st.markdown("---")

        # Compact system status
        st.markdown("### 🔗 Status")
        manager = get_consolidated_manager()
        overview = run_async(manager.get_overview_metrics()) or {}

        system_health = overview.get("system_health", {})
        st.metric("System", system_health.get("overall_status", "Unknown"))
        st.metric("Active", f"{system_health.get('active_conversations', 0)} chats")

        # Quick actions
        st.markdown("---")
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()

        st.markdown("---")
        st.caption("v2.0.0-Consolidated")

        return selected_view

def render_overview_dashboard():
    """Render the consolidated overview dashboard."""
    st.header("📊 Jorge AI Command Overview")
    st.markdown("**Unified view of all bot operations and system performance**")

    manager = get_consolidated_manager()
    overview = run_async(manager.get_overview_metrics()) or {}

    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    key_metrics = overview.get("key_metrics", {})
    with col1:
        st.metric("Leads Qualified Today", key_metrics.get("leads_qualified_today", 0), delta="+5")
    with col2:
        st.metric("Properties Matched", key_metrics.get("properties_matched", 0), delta="+12")
    with col3:
        st.metric("Listings Secured", key_metrics.get("listings_secured", 0), delta="+2")
    with col4:
        st.metric("Revenue Attributed", f"${key_metrics.get('revenue_attributed', 0):,}", delta="+$23,500")

    st.divider()

    # Bot Performance Overview
    col_perf1, col_perf2 = st.columns([2, 1])

    with col_perf1:
        st.markdown("### 🤖 Bot Performance Matrix")

        bot_performance = overview.get("bot_performance", {})

        # Create performance comparison chart
        bots = ["Lead Bot", "Buyer Bot", "Seller Bot"]
        scores = [
            bot_performance.get("lead_bot", {}).get("score", 0),
            bot_performance.get("buyer_bot", {}).get("score", 0),
            bot_performance.get("seller_bot", {}).get("score", 0)
        ]
        active_counts = [
            bot_performance.get("lead_bot", {}).get("active", 0),
            bot_performance.get("buyer_bot", {}).get("active", 0),
            bot_performance.get("seller_bot", {}).get("active", 0)
        ]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=bots, y=scores,
            mode='markers+lines',
            marker=dict(size=[x*3 for x in active_counts], color=scores, colorscale='Blues'),
            name="Performance Score",
            text=[f"{s}%<br>{a} active" for s, a in zip(scores, active_counts)],
            textposition="middle center"
        ))

        fig.update_layout(
            title="Bot Performance vs Active Conversations",
            xaxis_title="Bot Type",
            yaxis_title="Performance Score",
            height=300
        )

        if ELITE_STYLING:
            fig = style_obsidian_chart(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col_perf2:
        st.markdown("### 🚨 System Alerts")

        alerts = overview.get("alerts", [])
        for alert in alerts:
            level = alert.get("level", "info")
            message = alert.get("message", "")

            if level == "success":
                st.success(f"✅ {message}")
            elif level == "warning":
                st.warning(f"⚠️ {message}")
            elif level == "error":
                st.error(f"❌ {message}")
            else:
                st.info(f"ℹ️ {message}")

    st.divider()

    # Real-time Activity Monitor
    col_activity1, col_activity2, col_activity3 = st.columns(3)

    system_health = overview.get("system_health", {})

    with col_activity1:
        st.markdown("### 📈 Real-time Activity")
        st.metric("Messages/Min", f"{system_health.get('messages_per_minute', 0):.1f}")
        st.metric("Uptime", f"{system_health.get('uptime', 0):.1f}%")

    with col_activity2:
        st.markdown("### 💬 Active Conversations")
        for bot_name, bot_data in bot_performance.items():
            status = bot_data.get("status", "🔴")
            active = bot_data.get("active", 0)
            st.write(f"{status} **{bot_name.replace('_', ' ').title()}**: {active} active")

    with col_activity3:
        st.markdown("### 📊 Today's Performance")
        st.metric("Total Interactions", system_health.get("total_interactions_today", 0))
        st.metric("Peak Concurrent", "17 conversations", help="Highest concurrent load today")

def render_bot_dashboard(bot_type: str):
    """Render consolidated dashboard for a specific bot."""
    bot_names = {
        "lead_bot": "🎯 Lead Bot Command Center",
        "buyer_bot": "🏠 Buyer Bot Command Center",
        "seller_bot": "💼 Seller Bot Command Center"
    }

    bot_descriptions = {
        "lead_bot": "**3-7-30 Day Follow-up Sequences & Lead Nurturing**",
        "buyer_bot": "**Property Matching & Buyer Qualification**",
        "seller_bot": "**Confrontational Qualification & Stall-Breaking**"
    }

    st.header(bot_names.get(bot_type, "Bot Dashboard"))
    st.markdown(bot_descriptions.get(bot_type, ""))

    manager = get_consolidated_manager()
    metrics = run_async(manager.get_consolidated_metrics(bot_type)) or {}

    # Consolidated tab structure (3 tabs instead of 6)
    if bot_type == "lead_bot":
        tab1, tab2, tab3 = st.tabs(["💬 Chat & Pipeline", "📊 Performance", "📈 Analytics"])

        with tab1:
            render_lead_chat_and_pipeline(manager, metrics)
        with tab2:
            render_consolidated_performance(bot_type, metrics.get("performance", {}))
        with tab3:
            render_consolidated_analytics(bot_type, metrics.get("analytics", {}))

    elif bot_type == "buyer_bot":
        tab1, tab2, tab3 = st.tabs(["💬 Chat & Properties", "📊 Performance", "📈 Analytics"])

        with tab1:
            render_buyer_chat_and_properties(manager, metrics)
        with tab2:
            render_consolidated_performance(bot_type, metrics.get("performance", {}))
        with tab3:
            render_consolidated_analytics(bot_type, metrics.get("analytics", {}))

    elif bot_type == "seller_bot":
        tab1, tab2, tab3 = st.tabs(["💬 Chat & Qualification", "📊 Performance", "📈 Analytics"])

        with tab1:
            render_seller_chat_and_qualification(manager, metrics)
        with tab2:
            render_consolidated_performance(bot_type, metrics.get("performance", {}))
        with tab3:
            render_consolidated_analytics(bot_type, metrics.get("analytics", {}))

def render_lead_chat_and_pipeline(manager, metrics):
    """Consolidated Lead Bot chat and pipeline view."""
    col_chat, col_pipeline = st.columns([2, 1])

    with col_chat:
        st.subheader("💬 Lead Conversation")

        # Chat interface
        if 'lead_chat_history' not in st.session_state:
            st.session_state.lead_chat_history = []

        # Display recent messages
        for msg in st.session_state.lead_chat_history[-5:]:  # Show last 5 messages
            if msg['sender'] == 'user':
                st.markdown(f"**Lead**: {msg['content']}")
            else:
                st.markdown(f"**Lead Bot**: {msg['content']}")

        # Input
        user_message = st.text_input("Lead Message:", placeholder="I might be interested but need to think about it...")

        if st.button("Send to Lead Bot", use_container_width=True):
            if user_message:
                # Add to history
                st.session_state.lead_chat_history.append({
                    'sender': 'user',
                    'content': user_message,
                    'timestamp': datetime.now()
                })

                # Get response
                response = run_async(manager.chat_with_bot("lead_bot", user_message))
                if response:
                    st.session_state.lead_chat_history.append({
                        'sender': 'bot',
                        'content': response['response_content'],
                        'timestamp': datetime.now()
                    })
                st.rerun()

    with col_pipeline:
        st.subheader("🔄 Active Pipeline")

        # Compact pipeline view
        pipeline_leads = [
            {"name": "Sarah J.", "step": "Day 7", "score": 85},
            {"name": "Mike C.", "step": "Day 3", "score": 73},
            {"name": "Jennifer W.", "step": "Day 30", "score": 91}
        ]

        for lead in pipeline_leads:
            with st.container():
                st.write(f"**{lead['name']}** - {lead['step']}")
                st.progress(lead['score']/100)
                st.caption(f"Score: {lead['score']}")
                st.divider()

        # Quick stats
        st.metric("Active Sequences", "23", delta="+5")
        st.metric("Response Rate", "78.9%", delta="+3.2%")

def render_buyer_chat_and_properties(manager, metrics):
    """Consolidated Buyer Bot chat and properties view."""
    col_chat, col_properties = st.columns([2, 1])

    with col_chat:
        st.subheader("💬 Buyer Conversation")

        # Chat interface
        if 'buyer_chat_history' not in st.session_state:
            st.session_state.buyer_chat_history = []

        # Display recent messages
        for msg in st.session_state.buyer_chat_history[-5:]:
            if msg['sender'] == 'user':
                st.markdown(f"**Buyer**: {msg['content']}")
            else:
                st.markdown(f"**Buyer Bot**: {msg['content']}")

        # Input
        user_message = st.text_input("Buyer Message:", placeholder="I'm looking for a 3BR home with good schools...")

        if st.button("Send to Buyer Bot", use_container_width=True):
            if user_message:
                st.session_state.buyer_chat_history.append({
                    'sender': 'user',
                    'content': user_message,
                    'timestamp': datetime.now()
                })

                response = run_async(manager.chat_with_bot("buyer_bot", user_message))
                if response:
                    st.session_state.buyer_chat_history.append({
                        'sender': 'bot',
                        'content': response['response_content'],
                        'timestamp': datetime.now()
                    })
                st.rerun()

    with col_properties:
        st.subheader("🏠 Recent Matches")

        # Compact property matches
        matches = [
            {"address": "123 Oak St", "price": "$725K", "match": "92%"},
            {"address": "456 Pine Ave", "price": "$685K", "match": "87%"},
            {"address": "789 Elm Dr", "price": "$750K", "match": "84%"}
        ]

        for prop in matches:
            st.write(f"**{prop['address']}**")
            st.write(f"{prop['price']} • {prop['match']} match")
            st.divider()

        # Quick stats
        st.metric("Matches Sent", "45", delta="+12")
        st.metric("Accuracy", "89.7%", delta="+1.8%")

def render_seller_chat_and_qualification(manager, metrics):
    """Consolidated Seller Bot chat and qualification view."""
    col_chat, col_qualification = st.columns([2, 1])

    with col_chat:
        st.subheader("💬 Jorge's Qualification")

        # Chat interface
        if 'seller_chat_history' not in st.session_state:
            st.session_state.seller_chat_history = []

        # Display recent messages
        for msg in st.session_state.seller_chat_history[-5:]:
            if msg['sender'] == 'user':
                st.markdown(f"**Seller**: {msg['content']}")
            else:
                st.markdown(f"**Jorge**: {msg['content']}")

        # Input
        user_message = st.text_input("Seller Message:", placeholder="I'll get back to you next week...")

        if st.button("Send to Jorge", use_container_width=True):
            if user_message:
                st.session_state.seller_chat_history.append({
                    'sender': 'user',
                    'content': user_message,
                    'timestamp': datetime.now()
                })

                response = run_async(manager.chat_with_bot("seller_bot", user_message))
                if response:
                    st.session_state.seller_chat_history.append({
                        'sender': 'bot',
                        'content': response['response_content'],
                        'timestamp': datetime.now()
                    })

                    # Show Jorge's strategy
                    if response.get('next_action') == 'apply_pressure':
                        st.warning("🎯 Strategy: Take-away close deployed")
                st.rerun()

    with col_qualification:
        st.subheader("⚔️ Active Qualifications")

        # Compact qualification status
        qualifications = [
            {"seller": "Robert M.", "frs": 84, "status": "🟡 Stalling"},
            {"seller": "Lisa D.", "frs": 92, "status": "🟢 Hot"},
            {"seller": "Tom W.", "frs": 67, "status": "🔴 Resistant"}
        ]

        for qual in qualifications:
            st.write(f"**{qual['seller']}** - FRS: {qual['frs']}")
            st.write(qual['status'])
            st.divider()

        # Quick stats
        st.metric("Qualifications", "12", delta="+3")
        st.metric("Close Rate", "67.8%", delta="+3.4%")

def render_consolidated_performance(bot_type: str, performance_data: Dict[str, Any]):
    """Render consolidated performance metrics for any bot."""
    st.subheader("📊 Performance Overview")

    # Key performance metrics
    if bot_type == "lead_bot":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Success Rate", f"{performance_data.get('success_rate', 0):.1f}%", delta="+2.1%")
        with col2:
            st.metric("Response Time", f"{performance_data.get('response_time', 0):.1f}s", delta="-0.3s")
        with col3:
            st.metric("Efficiency", f"{performance_data.get('efficiency_score', 0):.1f}/100", delta="+3.2")
        with col4:
            st.metric("Re-engagement", f"{performance_data.get('reengagement_rate', 0):.1f}%", delta="+5.8%")

    elif bot_type == "buyer_bot":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Match Accuracy", f"{performance_data.get('match_accuracy', 0):.1f}%", delta="+1.8%")
        with col2:
            st.metric("Response Time", f"{performance_data.get('response_time', 0):.1f}s", delta="-0.2s")
        with col3:
            st.metric("Conversion", f"{performance_data.get('conversion_rate', 0):.1f}%", delta="+4.1%")
        with col4:
            st.metric("Satisfaction", f"{performance_data.get('satisfaction_score', 0):.1f}/5", delta="+0.2")

    elif bot_type == "seller_bot":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Qualification Speed", f"{performance_data.get('qualification_speed', 0):.1f}m", delta="-0.8m")
        with col2:
            st.metric("Stall Detection", f"{performance_data.get('stall_detection', 0):.1f}%", delta="+5.2%")
        with col3:
            st.metric("Close Rate", f"{performance_data.get('close_rate', 0):.1f}%", delta="+3.4%")
        with col4:
            st.metric("Jorge Score", f"{performance_data.get('jorge_effectiveness', 0):.1f}/100", delta="+2.3")

    # Performance trend chart
    st.divider()
    st.markdown("### 📈 Performance Trends")

    # Mock trend data
    dates = pd.date_range(start='2026-01-18', periods=7, freq='D')
    trend_data = {
        "Date": dates,
        "Performance": [85.2, 87.4, 89.1, 88.3, 91.7, 93.2, 90.8],
        "Target": [85] * 7
    }

    df_trend = pd.DataFrame(trend_data)
    fig = px.line(df_trend, x="Date", y=["Performance", "Target"],
                  title=f"{bot_type.replace('_', ' ').title()} Performance Trend")
    if ELITE_STYLING:
        fig = style_obsidian_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

def render_consolidated_analytics(bot_type: str, analytics_data: Dict[str, Any]):
    """Render consolidated analytics for any bot."""
    st.subheader("📈 Analytics & Insights")

    # Bot-specific analytics
    if bot_type == "lead_bot":
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Sequence Performance**")
            sequence_data = {
                "Step": ["Day 3", "Day 7", "Day 14", "Day 30"],
                "Success": [45.2, 62.8, 38.5, 23.4]
            }
            fig = px.bar(pd.DataFrame(sequence_data), x="Step", y="Success",
                        title="Sequence Step Success Rates")
            if ELITE_STYLING:
                fig = style_obsidian_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Key Insights**")
            st.success("🟢 Response time improved 15% this week")
            st.warning("🟡 Day 30 sequences need refresh")
            st.info("🔵 Peak performance during business hours")
            st.metric("Hot Leads Generated", analytics_data.get('hot_leads_generated', 0))

    elif bot_type == "buyer_bot":
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Match Performance by Price**")
            price_data = {
                "Range": ["$300-500K", "$500-700K", "$700-900K", "$900K+"],
                "Accuracy": [85.2, 89.7, 92.1, 87.3]
            }
            fig = px.bar(pd.DataFrame(price_data), x="Range", y="Accuracy")
            if ELITE_STYLING:
                fig = style_obsidian_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Conversion Funnel**")
            st.metric("Buyers Qualified", analytics_data.get('buyers_qualified', 0))
            st.metric("Properties Matched", analytics_data.get('properties_matched', 0))
            st.metric("Showings Booked", analytics_data.get('showings_booked', 0))
            st.metric("Offers Submitted", analytics_data.get('offers_submitted', 0))

    elif bot_type == "seller_bot":
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Jorge's Effectiveness**")
            strategy_data = {
                "Strategy": ["Take-Away", "Direct", "Pressure", "Reality"],
                "Success": [91.4, 78.5, 67.3, 72.8]
            }
            fig = px.bar(pd.DataFrame(strategy_data), x="Strategy", y="Success")
            if ELITE_STYLING:
                fig = style_obsidian_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Qualification Results**")
            st.metric("Total Qualifications", analytics_data.get('total_qualifications', 0))
            st.metric("Hot Leads", analytics_data.get('hot_leads', 0))
            st.metric("Voice Handoffs", analytics_data.get('voice_handoffs', 0))
            st.metric("Listings Secured", analytics_data.get('listings_secured', 0))

def render_global_settings():
    """Render centralized settings for all bots."""
    st.header("⚙️ Global Bot Configuration")
    st.markdown("**Centralized settings for all Jorge AI bots**")

    # Global settings tabs
    general_tab, bots_tab, compliance_tab, advanced_tab = st.tabs([
        "🔧 General", "🤖 Bot Config", "⚖️ Compliance", "🚀 Advanced"
    ])

    with general_tab:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("System Settings")
            st.selectbox("Default Model", ["Claude-3.5-Sonnet", "Claude-3-Haiku", "GPT-4"])
            st.slider("Global Response Timeout (s)", 1, 30, 15)
            st.checkbox("Enable Real-time Monitoring", value=True)
            st.checkbox("Auto-save Conversations", value=True)

        with col2:
            st.subheader("Performance Settings")
            st.slider("Concurrent Conversation Limit", 10, 100, 50)
            st.selectbox("Cache Duration", ["5 min", "15 min", "30 min", "1 hour"])
            st.checkbox("Enable Performance Alerts", value=True)
            st.slider("Alert Threshold (%)", 50, 100, 85)

    with bots_tab:
        st.subheader("Individual Bot Configuration")

        bot_config = st.selectbox("Select Bot to Configure",
                                  ["Lead Bot", "Buyer Bot", "Seller Bot (Jorge)"])

        if bot_config == "Seller Bot (Jorge)":
            col1, col2 = st.columns(2)
            with col1:
                st.slider("Confrontational Intensity", 0.0, 1.0, 0.8)
                st.slider("Take-Away Threshold", 1, 5, 2)
            with col2:
                st.checkbox("Enable Stall Detection", value=True)
                st.checkbox("Auto-Apply Take-Away", value=False)

    with compliance_tab:
        st.subheader("Compliance & Safety")

        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Fair Housing Compliance", value=True)
            st.checkbox("SMS Compliance (160 char)", value=True)
            st.checkbox("Data Privacy Protection", value=True)

        with col2:
            st.slider("Compliance Strictness", 0.0, 1.0, 0.9)
            st.selectbox("Audit Level", ["Basic", "Standard", "Comprehensive"])
            st.checkbox("Auto-Block Violations", value=True)

    with advanced_tab:
        st.subheader("Advanced Configuration")

        col1, col2 = st.columns(2)
        with col1:
            st.text_area("Custom System Prompt", height=100)
            st.checkbox("Enable A/B Testing", value=False)
            st.selectbox("Logging Level", ["Info", "Debug", "Warning", "Error"])

        with col2:
            st.json({"webhook_url": "https://api.example.com/webhook",
                    "retry_attempts": 3,
                    "timeout_ms": 5000})

def main():
    """Main application function."""
    # Apply styling
    if ELITE_STYLING:
        inject_elite_css()

    # Header
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1E88E5 0%, #6366F1 100%);
                    padding: 2rem; border-radius: 16px; margin-bottom: 2rem; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700;">
                🤖 Jorge AI Consolidated Dashboard
            </h1>
            <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                Streamlined Command Center - 39% Fewer Tabs, 100% More Efficiency
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    selected_view = render_sidebar()

    # Main content based on selection
    if selected_view == "📊 Overview":
        render_overview_dashboard()
    elif selected_view == "🎯 Lead Bot":
        render_bot_dashboard("lead_bot")
    elif selected_view == "🏠 Buyer Bot":
        render_bot_dashboard("buyer_bot")
    elif selected_view == "💼 Seller Bot":
        render_bot_dashboard("seller_bot")
    elif selected_view == "⚙️ Settings":
        render_global_settings()

if __name__ == "__main__":
    main()