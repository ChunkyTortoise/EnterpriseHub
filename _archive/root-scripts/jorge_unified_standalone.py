"""
Jorge AI Unified Bot Dashboard - Complete Standalone Edition
=========================================================

Professional dashboard for Jorge's real estate team.
Optimized for standalone deployment without dependencies.

Features:
🎯 Lead Bot - 3-7-30 day nurture sequences
🏠 Buyer Bot - Property matching & qualification
💼 Seller Bot - Jorge's confrontational methodology
📊 Real-time analytics & performance monitoring
📱 Mobile-responsive professional interface
⚙️ Bot configuration & settings
🔗 System health monitoring

Author: Claude Code Assistant
Optimized: 2026-01-25
Version: 2.0.0 Professional Standalone
License: Jorge Real Estate Team

Run with: streamlit run jorge_unified_standalone.py --server.port 8505
"""Jorge AI Unified Bot Dashboard - Standalone Edition
================================================

Optimized standalone version for Jorge's real estate team.
Manages Lead Bot, Buyer Bot, and Seller Bot with professional interface.

Features:
- 🎯 Live Chat Interfaces for all 3 bots
- 📊 Real-time KPIs & Performance Metrics
- 🧠 Analytics & Business Intelligence
- 💼 Lead & Property Management
- ⚙️ Bot Configuration & Settings
- 📱 Mobile-responsive design

Author: Claude Code Assistant
Optimized: 2026-01-25 for Jorge Real Estate Team
Version: 2.0.0 Standalone
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
import threading
from concurrent.futures import ThreadPoolExecutor

# Page Configuration - Optimized for performance
st.set_page_config(
    page_title="Jorge AI | Bot Command Center",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Jorge AI Bot Dashboard v2.0 - Professional Edition"
    }
)

# ============================================================================
# INLINED UTILITY FUNCTIONS (Removing external dependencies)
# ============================================================================

def run_async_safe(coro):
    """
    Safely run a coroutine in Streamlit environment.
    Optimized for standalone operation.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)

def inject_jorge_branding_css():
    """
    Inject professional Jorge-branded CSS for standalone operation.
    Optimized and streamlined from original obsidian theme.
    """
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@300;500;700&display=swap');

            :root {
                --jorge-dark: #0D1117;
                --jorge-card: rgba(22, 27, 34, 0.8);
                --jorge-border: rgba(255, 255, 255, 0.1);
                --jorge-accent: #1E88E5;
                --jorge-success: #00E676;
                --jorge-warning: #FF9800;
                --jorge-error: #F44336;
                --text-primary: #FFFFFF;
                --text-secondary: #8B949E;
                --glass-blur: blur(10px);
            }

            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
                color: var(--text-secondary) !important;
                background-color: var(--jorge-dark) !important;
            }

            .stAppViewContainer {
                background: linear-gradient(135deg, var(--jorge-dark) 0%, #161B22 100%) !important;
            }

            /* Header styling */
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Space Grotesk', sans-serif !important;
                color: var(--text-primary) !important;
                font-weight: 700 !important;
            }

            /* Card styling */
            div[data-testid="metric-container"] {
                background: var(--jorge-card) !important;
                border: 1px solid var(--jorge-border) !important;
                border-radius: 12px !important;
                backdrop-filter: var(--glass-blur) !important;
                padding: 1rem !important;
                transition: all 0.3s ease !important;
            }

            div[data-testid="metric-container"]:hover {
                border-color: var(--jorge-accent) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 32px rgba(30, 136, 229, 0.2) !important;
            }

            /* Button styling */
            .stButton > button {
                background: linear-gradient(135deg, var(--jorge-accent), #6366F1) !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 0.5rem 1rem !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
            }

            .stButton > button:hover {
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 16px rgba(30, 136, 229, 0.4) !important;
            }

            /* Sidebar styling */
            .css-1d391kg {
                background-color: var(--jorge-card) !important;
            }

            /* Chart improvements */
            .js-plotly-plot {
                background: transparent !important;
            }

            /* Mobile responsiveness */
            @media (max-width: 768px) {
                .stColumn {
                    min-width: 100% !important;
                }

                div[data-testid="metric-container"] {
                    margin-bottom: 1rem !important;
                }
            }

            /* Jorge branding */
            .jorge-header {
                background: linear-gradient(135deg, var(--jorge-accent) 0%, #6366F1 100%);
                padding: 2rem;
                border-radius: 16px;
                margin-bottom: 2rem;
                text-align: center;
                box-shadow: 0 8px 32px rgba(30, 136, 229, 0.3);
            }

            .jorge-brand {
                color: white;
                font-size: 2.5rem;
                font-weight: 700;
                margin: 0;
                text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }

            .jorge-tagline {
                color: rgba(255,255,255,0.9);
                font-size: 1.1rem;
                margin: 0.5rem 0 0 0;
                font-weight: 500;
            }

            /* Performance indicators */
            .status-online { color: var(--jorge-success) !important; }
            .status-warning { color: var(--jorge-warning) !important; }
            .status-offline { color: var(--jorge-error) !important; }

            /* Enhanced metrics */
            .metric-delta-positive { color: var(--jorge-success) !important; }
            .metric-delta-negative { color: var(--jorge-error) !important; }
        </style>
    """, unsafe_allow_html=True)

def style_chart_professional(fig):
    """
    Apply professional styling to charts for Jorge branding.
    Simplified from obsidian theme for performance.
    """
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FFFFFF', family='Inter'),
        title=dict(font=dict(size=16, color='#FFFFFF')),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            tickcolor='rgba(255,255,255,0.3)',
            color='#8B949E'
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            tickcolor='rgba(255,255,255,0.3)',
            color='#8B949E'
        ),
        legend=dict(
            bgcolor='rgba(22, 27, 34, 0.8)',
            bordercolor='rgba(255,255,255,0.1)',
            font=dict(color='#FFFFFF')
        )
    )
    return fig

# ============================================================================
# MOCK BOT SERVICES (Replacing real integrations for standalone demo)
# ============================================================================

class MockJorgeSellerBot:
    """Mock seller bot for standalone demo purposes."""

    async def process_seller_message(self, seller_id: str, seller_name: str, conversation: List[Dict]) -> Dict[str, Any]:
        """Simulate Jorge's confrontational seller qualification."""
        message = conversation[-1]['content'].lower()

        # Jorge's stall detection logic
        stall_detected = any(phrase in message for phrase in [
            'get back', 'think about', 'call you later', 'not sure', 'maybe'
        ])

        if stall_detected:
            responses = [
                f"{seller_name}, let me be straight with you. 'I'll think about it' usually means 'I'm not serious.' Are you actually ready to sell or just window shopping?",
                f"Look {seller_name}, I've heard that before. The market doesn't wait for people who 'think about it.' What's really holding you back?",
                f"{seller_name}, successful sellers make decisions. Unsuccessful ones 'think about it.' Which one are you?"
            ]
            tone = "confrontational"
            commitment_score = 35
        else:
            responses = [
                f"Good, {seller_name}. Now we're talking business. Let's get your property properly valued and on the market.",
                f"I appreciate the direct approach, {seller_name}. That's how we close deals. Here's what happens next...",
                f"Perfect, {seller_name}. You sound like someone who's serious about selling. Let's move forward."
            ]
            tone = "closing"
            commitment_score = 78

        return {
            "response_content": responses[0],
            "current_tone": tone,
            "stall_detected": stall_detected,
            "detected_stall_type": "delay_tactic" if stall_detected else None,
            "psychological_commitment": commitment_score,
            "next_action": "apply_pressure" if stall_detected else "move_to_close",
            "frs_score": 85 if not stall_detected else 45
        }

class MockLeadBot:
    """Mock lead bot for standalone demo purposes."""

    async def process_lead_message(self, lead_id: str, message: str, step: str) -> Dict[str, Any]:
        """Simulate lead nurturing sequence processing."""

        engagement_scores = {
            "day_3": 65,
            "day_7": 72,
            "day_14": 58,
            "day_30": 45
        }

        responses = {
            "day_3": f"Hi! Thanks for your interest in that property. I noticed you haven't heard back from anyone yet. Let me help you get the information you need. What questions can I answer?",
            "day_7": f"Hope you're doing well! I wanted to follow up about that property you inquired about. I have some similar options that just came on the market. Would you like to see them?",
            "day_14": f"Hi there! The market's been moving fast lately. I wanted to make sure you didn't miss out on some great opportunities. Are you still looking in the same area?",
            "day_30": f"Hey! I hope you found what you were looking for. If not, I've got some new listings that might be perfect. Quick question - what's your timeline looking like?"
        }

        next_steps = {
            "day_3": "day_7",
            "day_7": "day_14",
            "day_14": "day_30",
            "day_30": "long_term_nurture"
        }

        return {
            "response_content": responses.get(step, responses["day_3"]),
            "step_completed": step,
            "next_step": next_steps.get(step, "day_7"),
            "engagement_score": engagement_scores.get(step, 65),
            "sequence_type": "reengagement",
            "priority": "medium" if step in ["day_3", "day_7"] else "low"
        }

class MockBuyerBot:
    """Mock buyer bot for standalone demo purposes."""

    async def process_buyer_message(self, buyer_id: str, message: str) -> Dict[str, Any]:
        """Simulate buyer property matching and qualification."""

        message_lower = message.lower()

        # Extract preferences
        bedrooms = 3
        if 'bedroom' in message_lower or 'br' in message_lower:
            for i in range(2, 6):
                if str(i) in message_lower:
                    bedrooms = i
                    break

        # Mock property matches
        properties = [
            {"address": "123 Oak Lane, Rancho Cucamonga", "price": 675000, "beds": 3, "match_score": 92},
            {"address": "456 Cedar Drive, Victoria Gardens", "price": 650000, "beds": 4, "match_score": 88},
            {"address": "789 Pine Street, Etiwanda", "price": 720000, "beds": 3, "match_score": 85}
        ]

        # Filter by preferences
        matched_properties = [p for p in properties if p['beds'] >= bedrooms]

        return {
            "response_content": f"Excellent! I found {len(matched_properties)} properties that match your criteria. Based on your {bedrooms}+ bedroom requirement, here are the best options. Would you like me to schedule viewings?",
            "properties_matched": len(matched_properties),
            "matched_properties": matched_properties,
            "financial_readiness": 82,
            "urgency_level": "high" if "soon" in message_lower or "asap" in message_lower else "medium",
            "next_action": "schedule_showing"
        }

# ============================================================================
# UNIFIED BOT MANAGER (Standalone version)
# ============================================================================

class StandaloneJorgeBotManager:
    """
    Standalone bot manager for Jorge's unified dashboard.
    Optimized for performance and professional deployment.
    """

    def __init__(self):
        self.seller_bot = MockJorgeSellerBot()
        self.lead_bot = MockLeadBot()
        self.buyer_bot = MockBuyerBot()
        self.is_connected = True

    async def get_system_health(self) -> Dict[str, str]:
        """Get health status for all bot systems."""
        return {
            "seller_bot": "🟢 Online",
            "lead_bot": "🟢 Online",
            "buyer_bot": "🟢 Online",
            "system": "🟢 All Systems Operational"
        }

    async def get_lead_bot_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive Lead Bot metrics."""
        base_metrics = {
            "total_sequences": 127,
            "active_sequences": 23,
            "reengagement_rate": 78.5,
            "day_3_response_rate": 45.2,
            "day_7_call_success": 62.8,
            "day_30_recovery_rate": 23.4,
            "avg_engagement_score": 82.3,
            "hot_leads_generated": 8,
            "pipeline_conversion": 34.7,
            "avg_response_time": 2.3,
            "success_rate": 94.2,
            "uptime": 99.7
        }

        # Add some realistic variation
        import random
        for key, value in base_metrics.items():
            if isinstance(value, (int, float)):
                variation = random.uniform(0.95, 1.05)
                base_metrics[key] = round(value * variation, 1)

        return base_metrics

    async def get_seller_bot_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive Seller Bot metrics."""
        return {
            "total_qualifications": 89,
            "qualification_rate": 67.8,
            "stall_detection_rate": 91.3,  # Jorge's expertise
            "takeaway_close_success": 73.4,
            "avg_frs_score": 84.7,
            "avg_pcs_score": 75.6,
            "hot_leads": 12,
            "voice_handoffs": 8,
            "conversion_to_listing": 42.3,
            "avg_qualification_time": 4.2,
            "jorge_effectiveness": 91.5
        }

    async def get_buyer_bot_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive Buyer Bot metrics."""
        return {
            "total_buyers_qualified": 64,
            "property_matches_sent": 178,
            "showing_bookings": 23,
            "offer_submissions": 7,
            "avg_financial_readiness": 78.9,
            "avg_match_accuracy": 89.7,
            "buyer_satisfaction": 4.7,
            "closed_transactions": 3,
            "avg_days_to_offer": 18.5,
            "conversion_rate": 23.4
        }

    async def get_performance_summary(self) -> Dict[str, Dict[str, float]]:
        """Get cross-bot performance comparison."""
        return {
            "lead_bot": {
                "response_time": 2.3,
                "success_rate": 94.2,
                "efficiency": 87.5,
                "uptime": 99.7,
                "satisfaction": 4.6
            },
            "buyer_bot": {
                "response_time": 1.8,
                "match_accuracy": 89.7,
                "conversion_rate": 23.4,
                "uptime": 99.9,
                "satisfaction": 4.7
            },
            "seller_bot": {
                "response_time": 1.2,
                "qualification_speed": 4.2,
                "close_rate": 67.8,
                "uptime": 99.8,
                "effectiveness": 91.5
            }
        }

    async def get_real_time_activity(self) -> Dict[str, Any]:
        """Get live activity metrics."""
        return {
            "active_conversations": {
                "lead_bot": 12,
                "buyer_bot": 8,
                "seller_bot": 5
            },
            "messages_per_minute": {
                "lead_bot": 3.2,
                "buyer_bot": 2.8,
                "seller_bot": 4.1
            },
            "current_load": {
                "lead_bot": "Normal",
                "buyer_bot": "Light",
                "seller_bot": "High"
            },
            "system_status": "All systems operational",
            "last_updated": datetime.now().strftime("%H:%M:%S")
        }

@st.cache_resource
def get_jorge_bot_manager():
    """Get cached instance of Jorge bot manager."""
    return StandaloneJorgeBotManager()
# ============================================================================
# UI COMPONENTS FOR JORGE STANDALONE DASHBOARD
# ============================================================================

def render_jorge_header():
    """Render the professional Jorge-branded header."""
    st.markdown("""
        <div class="jorge-header">
            <h1 class="jorge-brand">🤖 JORGE AI</h1>
            <p class="jorge-tagline">Unified Bot Command Center | Real Estate Intelligence Platform</p>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar_navigation():
    """Render optimized sidebar navigation."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #1E88E5; font-family: 'Space Grotesk', sans-serif; margin-bottom: 0;">🤖 JORGE AI</h2>
            <p style="color: #8B949E; font-size: 0.8rem; letter-spacing: 0.1em; margin-top: 0.5rem;">BOT COMMAND CENTER</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Bot selection
        selected_bot = st.radio(
            "**Select Bot:**",
            ["🎯 Lead Bot", "🏠 Buyer Bot", "💼 Seller Bot"],
            index=0,
            key="bot_selection"
        )

        st.markdown("---")

        # System health status
        st.markdown("### 🔗 System Health")
        manager = get_jorge_bot_manager()
        health = run_async_safe(manager.get_system_health())

        for system, status in health.items():
            status_class = "status-online" if "🟢" in status else "status-warning" if "🟡" in status else "status-offline"
            st.markdown(f'<p class="{status_class}"><strong>{system.replace("_", " ").title()}:</strong> {status}</p>', unsafe_allow_html=True)

        st.markdown("---")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()

        with col2:
            if st.button("📊 Export", use_container_width=True):
                st.toast("Export initiated!", icon="📊")

        if st.button("📱 Mobile View", use_container_width=True, help="Optimize for mobile devices"):
            st.session_state['mobile_mode'] = not st.session_state.get('mobile_mode', False)
            st.rerun()

        st.markdown("---")
        st.caption("v2.0.0 Standalone | Jorge Real Estate")

        return selected_bot

def render_performance_metrics_grid(metrics: Dict[str, Any], bot_type: str):
    """Render a responsive metrics grid."""
    mobile_mode = st.session_state.get('mobile_mode', False)
    cols = 2 if mobile_mode else 4

    if bot_type == "lead":
        metric_groups = [
            [
                ("Active Sequences", metrics.get("active_sequences", 0), "+5"),
                ("Day 3 Response", f"{metrics.get('day_3_response_rate', 0):.1f}%", "+3.2%")
            ],
            [
                ("Re-engagement Rate", f"{metrics.get('reengagement_rate', 0):.1f}%", "+5.8%"),
                ("Day 7 Success", f"{metrics.get('day_7_call_success', 0):.1f}%", "+2.1%")
            ],
            [
                ("Hot Leads", metrics.get("hot_leads_generated", 0), "+3"),
                ("Avg Score", f"{metrics.get('avg_engagement_score', 0):.1f}", "+1.5")
            ],
            [
                ("Conversion", f"{metrics.get('pipeline_conversion', 0):.1f}%", "+4.2%"),
                ("Recovery Rate", f"{metrics.get('day_30_recovery_rate', 0):.1f}%", "+1.8%")
            ]
        ]
    elif bot_type == "seller":
        metric_groups = [
            [
                ("Qualifications", metrics.get("total_qualifications", 0), "+12"),
                ("Qualification Rate", f"{metrics.get('qualification_rate', 0):.1f}%", "+3.4%")
            ],
            [
                ("Stall Detection", f"{metrics.get('stall_detection_rate', 0):.1f}%", "+5.2%"),
                ("Take-Away Success", f"{metrics.get('takeaway_close_success', 0):.1f}%", "+8.1%")
            ],
            [
                ("Avg FRS Score", f"{metrics.get('avg_frs_score', 0):.1f}", "+2.3"),
                ("Hot Leads", metrics.get("hot_leads", 0), "+4")
            ],
            [
                ("Voice Handoffs", metrics.get("voice_handoffs", 0), "+2"),
                ("Listing Conv.", f"{metrics.get('conversion_to_listing', 0):.1f}%", "+6.7%")
            ]
        ]
    else:  # buyer
        metric_groups = [
            [
                ("Buyers Qualified", metrics.get("total_buyers_qualified", 0), "+8"),
                ("Financial Ready", f"{metrics.get('avg_financial_readiness', 0):.1f}%", "+2.3%")
            ],
            [
                ("Matches Sent", metrics.get("property_matches_sent", 0), "+23"),
                ("Match Accuracy", f"{metrics.get('avg_match_accuracy', 0):.1f}%", "+1.8%")
            ],
            [
                ("Showings", metrics.get("showing_bookings", 0), "+5"),
                ("Offers", metrics.get("offer_submissions", 0), "+2")
            ],
            [
                ("Closed", metrics.get("closed_transactions", 0), "+1"),
                ("Days to Offer", f"{metrics.get('avg_days_to_offer', 0):.1f}", "-2.3")
            ]
        ]

    # Create responsive grid
    if mobile_mode:
        for i in range(0, len(metric_groups), 2):
            col1, col2 = st.columns(2)
            with col1:
                if i < len(metric_groups):
                    for label, value, delta in metric_groups[i]:
                        st.metric(label, value, delta)
            with col2:
                if i + 1 < len(metric_groups):
                    for label, value, delta in metric_groups[i + 1]:
                        st.metric(label, value, delta)
    else:
        col1, col2, col3, col4 = st.columns(4)
        for i, col in enumerate([col1, col2, col3, col4]):
            if i < len(metric_groups):
                with col:
                    for label, value, delta in metric_groups[i]:
                        st.metric(label, value, delta)

def render_chat_interface(manager, bot_type: str):
    """Render unified chat interface for all bots."""
    st.subheader(f"💬 {bot_type.title()} Bot Chat Interface")

    # Chat history key
    chat_key = f"{bot_type}_chat_history"

    col1, col2 = st.columns([1, 2] if not st.session_state.get('mobile_mode', False) else [1, 1])

    with col1:
        # Bot-specific selection panel
        if bot_type == "lead":
            st.markdown("**Active Lead Selection**")
            selected_contact = st.selectbox(
                "Select Lead:",
                ["Sarah Johnson (Day 7)", "Mike Chen (Day 3)", "Jennifer White (Day 30)"],
                key=f"{bot_type}_contact_selection"
            )
            sequence_step = st.selectbox(
                "Sequence Step:",
                ["day_3", "day_7", "day_14", "day_30"],
                index=1,
                key=f"{bot_type}_sequence_step"
            )
        elif bot_type == "seller":
            st.markdown("**Active Seller Selection**")
            selected_contact = st.selectbox(
                "Select Seller:",
                ["Robert Miller (Motivated)", "Lisa Davis (Price Testing)", "Tom Wilson (Unresponsive)"],
                key=f"{bot_type}_contact_selection"
            )
            st.write("**Profile:**")
            st.write("• Property: 123 Maple St")
            st.write("• Est. Value: $850K")
            st.write("• Timeline: 30 days")
        else:  # buyer
            st.markdown("**Active Buyer Selection**")
            selected_contact = st.selectbox(
                "Select Buyer:",
                ["Alex Thompson (Pre-approved)", "Maria Garcia (Searching)", "John Smith (First-time)"],
                key=f"{bot_type}_contact_selection"
            )
            st.write("**Profile:**")
            st.write("• Budget: $600K-$800K")
            st.write("• Areas: Rancho Cucamonga, Victoria Gardens")
            st.write("• Timeline: 60 days")

    with col2:
        st.markdown("**Live Conversation**")

        # Initialize chat history
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        # Display chat history with improved styling
        chat_container = st.container()
        with chat_container:
            for i, msg in enumerate(st.session_state[chat_key]):
                if msg['sender'] == 'user':
                    st.markdown(f"""
                        <div style="text-align: right; margin: 0.5rem 0;">
                            <div style="background: #1E88E5; color: white; padding: 0.5rem 1rem; border-radius: 1rem 1rem 0.2rem 1rem; display: inline-block; max-width: 70%;">
                                <strong>Contact:</strong> {msg['content']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="text-align: left; margin: 0.5rem 0;">
                            <div style="background: #22272E; color: white; padding: 0.5rem 1rem; border-radius: 1rem 1rem 1rem 0.2rem; display: inline-block; max-width: 70%;">
                                <strong>{bot_type.title()} Bot:</strong> {msg['content']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        # Input section
        if bot_type == "lead":
            placeholder = "I might be interested but need to think about it..."
        elif bot_type == "seller":
            placeholder = "I'll get back to you next week, pretty busy right now..."
        else:
            placeholder = "I'm looking for a 3BR home with a good school district..."

        user_message = st.text_input(
            "Type message:",
            placeholder=placeholder,
            key=f"{bot_type}_user_input"
        )

        col_send, col_clear = st.columns([3, 1])
        with col_send:
            send_clicked = st.button(f"Send to {bot_type.title()} Bot", use_container_width=True, key=f"{bot_type}_send")
        with col_clear:
            if st.button("Clear", use_container_width=True, key=f"{bot_type}_clear"):
                st.session_state[chat_key] = []
                st.rerun()

        if send_clicked and user_message:
            # Add user message
            st.session_state[chat_key].append({
                'sender': 'user',
                'content': user_message,
                'timestamp': datetime.now()
            })

            # Get bot response
            try:
                if bot_type == "lead":
                    response = run_async_safe(manager.lead_bot.process_lead_message("demo_lead", user_message, sequence_step))
                elif bot_type == "seller":
                    response = run_async_safe(manager.seller_bot.process_seller_message("demo_seller", "Contact", [{"role": "user", "content": user_message}]))
                else:
                    response = run_async_safe(manager.buyer_bot.process_buyer_message("demo_buyer", user_message))

                # Add bot response
                st.session_state[chat_key].append({
                    'sender': 'bot',
                    'content': response['response_content'],
                    'timestamp': datetime.now()
                })

                # Show additional info for seller bot
                if bot_type == "seller" and 'stall_detected' in response:
                    if response['stall_detected']:
                        st.warning(f"⚠️ Stall Detected: {response.get('detected_stall_type', 'Unknown')}")
                        st.info(f"🎯 Jorge Strategy: {response.get('next_action', 'Continue')}")
                    else:
                        st.success("✅ Positive engagement detected")

                st.rerun()

            except Exception as e:
                st.error(f"Error processing message: {str(e)}")

def render_analytics_charts(metrics: Dict[str, Any], bot_type: str):
    """Render analytics charts optimized for each bot type."""
    col1, col2 = st.columns(2)

    with col1:
        if bot_type == "lead":
            st.markdown("**Sequence Performance**")
            step_data = pd.DataFrame({
                "Step": ["Day 3", "Day 7", "Day 14", "Day 30"],
                "Response Rate": [45.2, 62.8, 38.5, 23.4],
                "Conversion Rate": [12.5, 28.7, 15.2, 8.1]
            })
            fig = px.bar(step_data, x="Step", y=["Response Rate", "Conversion Rate"],
                        title="Lead Sequence Performance", barmode="group")

        elif bot_type == "seller":
            st.markdown("**Jorge Strategy Performance**")
            strategy_data = pd.DataFrame({
                "Strategy": ["Direct", "Take-Away", "Pressure", "Reality"],
                "Success Rate": [78.5, 84.2, 67.3, 72.8],
                "Usage": [45, 32, 16, 7]
            })
            fig = px.scatter(strategy_data, x="Usage", y="Success Rate", size="Success Rate",
                           hover_name="Strategy", title="Strategy Effectiveness vs Usage")

        else:  # buyer
            st.markdown("**Conversion Funnel**")
            funnel_data = pd.DataFrame({
                "Stage": ["Inquiry", "Qualified", "Matched", "Showing", "Offer", "Closed"],
                "Count": [100, 64, 45, 23, 7, 3]
            })
            fig = px.funnel(funnel_data, x="Count", y="Stage", title="Buyer Conversion Funnel")

        fig = style_chart_professional(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        if bot_type == "lead":
            st.markdown("**Engagement Trends (7 Days)**")
            dates = pd.date_range(start=datetime.now().date() - timedelta(days=6), periods=7)
            trend_data = pd.DataFrame({
                "Date": dates,
                "Engagements": [23, 31, 28, 35, 42, 38, 45],
                "Conversions": [3, 5, 4, 7, 9, 6, 8]
            })
            fig2 = px.line(trend_data, x="Date", y=["Engagements", "Conversions"], title="Weekly Trends")

        elif bot_type == "seller":
            st.markdown("**FRS Score Distribution**")
            frs_data = pd.DataFrame({
                "Score Range": ["90-100", "80-89", "70-79", "60-69"],
                "Count": [12, 23, 34, 18],
                "Conversion %": [85, 72, 54, 34]
            })
            fig2 = px.bar(frs_data, x="Score Range", y=["Count", "Conversion %"],
                         title="FRS Performance", barmode="group")

        else:  # buyer
            st.markdown("**Match Accuracy by Price Range**")
            accuracy_data = pd.DataFrame({
                "Price Range": ["$300-500K", "$500-700K", "$700-900K", "$900K+"],
                "Accuracy %": [85.2, 89.7, 92.1, 87.3]
            })
            fig2 = px.bar(accuracy_data, x="Price Range", y="Accuracy %", title="Match Accuracy")

        fig2 = style_chart_professional(fig2)
        st.plotly_chart(fig2, use_container_width=True)Jorge AI Standalone Dashboard - Main Application
=============================================

Complete standalone dashboard combining all components.
Optimized for Jorge's real estate team deployment.

Run with: streamlit run jorge_standalone_main.py --server.port 8505
"""

# Import all components from separate files
exec(open('jorge_standalone_dashboard.py').read())
exec(open('jorge_standalone_dashboard_ui.py').read())

# ============================================================================
# TAB RENDERING FUNCTIONS
# ============================================================================

def render_lead_bot_tab():
    """Render complete Lead Bot interface."""
    st.header("🎯 Lead Bot Command Center")
    st.markdown("**3-7-30 Day Follow-up Sequences & Lead Nurturing**")

    manager = get_jorge_bot_manager()
    metrics = run_async_safe(manager.get_lead_bot_metrics())

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Live Chat", "📊 KPIs", "📈 Analytics", "⚙️ Settings"])

    with tab1:
        render_chat_interface(manager, "lead")

    with tab2:
        st.subheader("📊 Lead Bot Performance KPIs")
        render_performance_metrics_grid(metrics, "lead")

        # Additional insights
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**💡 Performance Insights**")
            insights = [
                "🟢 Response time improved 15% this week",
                "🟡 Day 30 sequences need optimization",
                "🟢 Success rate above 85% target",
                "🔵 Peak performance during 9-5 PM"
            ]
            for insight in insights:
                st.markdown(f"• {insight}")

        with col2:
            st.markdown("**📈 Optimization Recommendations**")
            recommendations = [
                "📈 **Day 30 Refresh**: Update messaging templates",
                "⏰ **Weekend Strategy**: Deploy lighter approach",
                "🎯 **Peak Hours**: Increase capacity 9-5 PM",
                "🔄 **A/B Testing**: Try new email templates"
            ]
            for rec in recommendations:
                st.markdown(f"• {rec}")

    with tab3:
        st.subheader("📈 Lead Bot Analytics")
        render_analytics_charts(metrics, "lead")

        # Pipeline overview
        st.markdown("---")
        st.markdown("**🔄 Active Lead Pipeline**")
        pipeline_data = [
            {"Name": "Sarah Johnson", "Step": "Day 7 Call", "Status": "Scheduled", "Score": 85},
            {"Name": "Mike Chen", "Step": "Day 3 SMS", "Status": "Sent", "Score": 73},
            {"Name": "Jennifer White", "Step": "Day 30 Nudge", "Status": "Delivered", "Score": 91},
            {"Name": "David Brown", "Step": "Day 14 Email", "Status": "Opened", "Score": 67}
        ]

        df_pipeline = pd.DataFrame(pipeline_data)
        st.dataframe(df_pipeline, use_container_width=True)

    with tab4:
        st.subheader("⚙️ Lead Bot Configuration")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Sequence Timing**")
            day_3_delay = st.slider("Day 3 Delay (hours)", 24, 120, 72)
            day_7_delay = st.slider("Day 7 Delay (hours)", 120, 240, 168)

            st.markdown("**Response Thresholds**")
            engagement_threshold = st.slider("Engagement Score Threshold", 50, 100, 75)

        with col2:
            st.markdown("**Channel Preferences**")
            enable_sms = st.checkbox("Enable SMS Sequences", value=True)
            enable_calls = st.checkbox("Enable Voice AI Calls", value=True)
            enable_email = st.checkbox("Enable Email Follow-ups", value=True)

            st.markdown("**AI Behavior**")
            response_tone = st.selectbox("Response Tone", ["Professional", "Friendly", "Urgent"])

def render_seller_bot_tab():
    """Render complete Seller Bot interface."""
    st.header("💼 Jorge Seller Bot Command Center")
    st.markdown("**Confrontational Qualification & Stall-Breaking Protocol**")

    manager = get_jorge_bot_manager()
    metrics = run_async_safe(manager.get_seller_bot_metrics())

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Live Chat", "📊 KPIs", "📈 Analytics", "🧠 Jorge Insights"])

    with tab1:
        render_chat_interface(manager, "seller")

        # Jorge strategy monitor
        st.markdown("---")
        st.markdown("**🔴 Live Jorge Strategy Monitor**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info("🟢 3 active qualifications")
            st.caption("Avg session: 3.2 minutes")

        with col2:
            st.warning("🟡 2 stalls detected")
            st.caption("Auto-handling with take-away")

        with col3:
            st.success("🚀 1 take-away deployed")
            st.caption("Result pending...")

    with tab2:
        st.subheader("📊 Jorge Performance KPIs")
        render_performance_metrics_grid(metrics, "seller")

        # Jorge vs Human comparison
        st.markdown("---")
        st.markdown("**🤖 Jorge vs Human Agent Performance**")
        comparison_data = pd.DataFrame({
            "Metric": ["Qualification Time", "Close Rate", "Lead Quality", "Consistency"],
            "Jorge": [4.2, 67.8, 84.7, 98.2],
            "Human Average": [8.7, 45.3, 72.1, 76.5],
            "Industry Avg": [12.3, 38.7, 68.9, 65.2]
        })

        fig = px.bar(comparison_data, x="Metric", y=["Jorge", "Human Average", "Industry Avg"],
                     title="Performance Comparison", barmode="group")
        fig = style_chart_professional(fig)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("📈 Jorge Analytics")
        render_analytics_charts(metrics, "seller")

        # Stall detection insights
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🎯 Jorge's Tactical Performance**")
            jorge_moves = [
                {"move": "Price Reality Check", "success": 89.2},
                {"move": "Timeline Pressure", "success": 76.5},
                {"move": "Competition Angle", "success": 83.7},
                {"move": "Take-Away Close", "success": 91.4}
            ]

            for move in jorge_moves:
                st.markdown(f"**{move['move']}**")
                st.progress(move['success']/100)
                st.caption(f"Success Rate: {move['success']}%")

        with col2:
            st.markdown("**📊 Psychological Commitment Tracking**")
            pcs_data = [
                ("Initial Contact", 45.2, 12.3),
                ("2nd Exchange", 62.8, 34.7),
                ("3rd Exchange", 74.3, 58.9),
                ("4th+ Exchange", 81.7, 73.2)
            ]

            for interaction, pcs, conversion in pcs_data:
                st.metric(interaction, f"PCS: {pcs}", f"{conversion}% convert")

    with tab4:
        st.subheader("🧠 Jorge's Seller Intelligence")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Recent Qualification Insights**")
            insights = [
                {"seller": "Robert Miller", "insight": "High motivation but unrealistic timeline", "confidence": 87},
                {"seller": "Lisa Davis", "insight": "Price testing market, not serious", "confidence": 92},
                {"seller": "Tom Wilson", "insight": "Financial distress detected", "confidence": 78},
                {"seller": "Amy Chen", "insight": "Perfect candidate for quick close", "confidence": 95}
            ]

            for insight in insights:
                with st.container():
                    st.markdown(f"**{insight['seller']}**")
                    st.write(insight['insight'])
                    st.progress(insight['confidence']/100, text=f"Confidence: {insight['confidence']}%")
                    st.divider()

        with col2:
            st.markdown("**🧠 Market Psychology Patterns**")
            patterns = [
                "73% mention Zillow in first 3 messages",
                "'Get back to you' spikes 40% in tax season",
                "Motivated sellers use future tense 67% more",
                "Price objections peak on Mondays (+47%)"
            ]

            for pattern in patterns:
                st.markdown(f"• {pattern}")

            st.markdown("**💡 Jorge's Recommendations**")
            st.success("✅ Increase confrontational tone on Mondays")
            st.info("💡 Pre-emptive Zillow defense in opener")
            st.warning("⚠️ Timeline pressure more effective Q1")

def render_buyer_bot_tab():
    """Render complete Buyer Bot interface."""
    st.header("🏠 Buyer Bot Command Center")
    st.markdown("**Property Matching & Buyer Qualification**")

    manager = get_jorge_bot_manager()
    metrics = run_async_safe(manager.get_buyer_bot_metrics())

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Live Chat", "📊 KPIs", "🏠 Properties", "📈 Analytics"])

    with tab1:
        render_chat_interface(manager, "buyer")

    with tab2:
        st.subheader("📊 Buyer Bot Performance KPIs")
        render_performance_metrics_grid(metrics, "buyer")

        # Performance by hour heatmap
        st.markdown("---")
        st.markdown("**⏰ Performance by Hour of Day**")
        hours = list(range(24))
        performance_by_hour = [
            65, 70, 72, 68, 71, 75, 78, 82, 89, 91, 93, 92,
            90, 88, 87, 89, 91, 88, 85, 82, 78, 75, 72, 68
        ]

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=[performance_by_hour],
            x=hours,
            y=["Performance"],
            colorscale='Blues',
            showscale=True
        ))
        fig_heatmap.update_layout(title="Performance Heatmap", height=200)
        fig_heatmap = style_chart_professional(fig_heatmap)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    with tab3:
        st.subheader("🏠 Property Matching Interface")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Search Criteria**")
            price_min, price_max = st.slider("Price Range", 700000, 1200000, (600000, 800000), format="$%d")
            bedrooms = st.selectbox("Bedrooms", [2, 3, 4, 5], index=1)
            areas = st.multiselect("Areas", ["Rancho Cucamonga", "Victoria Gardens", "Etiwanda", "Day Creek"], default=["Rancho Cucamonga"])

            if st.button("🔍 Find Matches", use_container_width=True):
                st.session_state['search_triggered'] = True

        with col2:
            st.markdown("**Recent Property Matches**")
            properties = [
                {"Address": "123 Oak St, Rancho Cucamonga", "Price": "$725K", "Beds": 3, "Match": "92%"},
                {"Address": "456 Pine Ave, Victoria Gardens", "Price": "$685K", "Beds": 4, "Match": "88%"},
                {"Address": "789 Elm Dr, Etiwanda", "Price": "$750K", "Beds": 3, "Match": "85%"},
                {"Address": "321 Maple Ln, Day Creek", "Price": "$645K", "Beds": 3, "Match": "90%"}
            ]

            df_properties = pd.DataFrame(properties)
            st.dataframe(df_properties, use_container_width=True)

    with tab4:
        st.subheader("📈 Buyer Bot Analytics")
        render_analytics_charts(metrics, "buyer")

        # Advanced funnel analysis
        st.markdown("---")
        st.markdown("**🔄 Advanced Buyer Journey Analysis**")

        funnel_metrics = [
            ("Initial Inquiry", 100, 0),
            ("Properties Viewed", 78, 22),
            ("Matches Sent", 45, 42),
            ("Showings Scheduled", 34, 24),
            ("Offers Made", 23, 32),
            ("Closed Deals", 3, 87)
        ]

        for stage, count, drop in funnel_metrics:
            col_stage, col_count, col_drop = st.columns([2, 1, 1])
            with col_stage:
                st.write(f"**{stage}**")
            with col_count:
                st.write(f"{count} leads")
            with col_drop:
                if drop > 0:
                    st.write(f"📉 {drop}% drop")
                else:
                    st.write("🟢 Entry point")

def render_performance_summary():
    """Render cross-bot performance summary."""
    st.markdown("---")
    st.header("⚡ Cross-Bot Performance Dashboard")

    manager = get_jorge_bot_manager()
    performance_summary = run_async_safe(manager.get_performance_summary())
    real_time = run_async_safe(manager.get_real_time_activity())

    # Performance comparison
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🎯 Lead Bot**")
        lead_perf = performance_summary.get("lead_bot", {})
        st.metric("Success Rate", f"{lead_perf.get('success_rate', 0):.1f}%")
        st.metric("Response Time", f"{lead_perf.get('response_time', 0):.1f}s")
        st.metric("Efficiency", f"{lead_perf.get('efficiency', 0):.1f}/100")

    with col2:
        st.markdown("**🏠 Buyer Bot**")
        buyer_perf = performance_summary.get("buyer_bot", {})
        st.metric("Match Accuracy", f"{buyer_perf.get('match_accuracy', 0):.1f}%")
        st.metric("Response Time", f"{buyer_perf.get('response_time', 0):.1f}s")
        st.metric("Conversion Rate", f"{buyer_perf.get('conversion_rate', 0):.1f}%")

    with col3:
        st.markdown("**💼 Seller Bot**")
        seller_perf = performance_summary.get("seller_bot", {})
        st.metric("Close Rate", f"{seller_perf.get('close_rate', 0):.1f}%")
        st.metric("Response Time", f"{seller_perf.get('response_time', 0):.1f}s")
        st.metric("Effectiveness", f"{seller_perf.get('effectiveness', 0):.1f}/100")

    # Real-time activity monitor
    st.markdown("---")
    st.markdown("**🔴 Live Activity Monitor**")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        active_total = sum(real_time.get("active_conversations", {}).values())
        st.metric("Active Conversations", active_total, "+3 vs 1hr")

    with col2:
        messages_total = sum(real_time.get("messages_per_minute", {}).values())
        st.metric("Messages/Min", f"{messages_total:.1f}", "+0.8/min")

    with col3:
        st.metric("System Status", "🟢 Operational", "99.8% uptime")

    with col4:
        peak_bot = max(real_time.get("active_conversations", {}), key=real_time.get("active_conversations", {}).get, default="Seller Bot")
        st.metric("Peak Load Bot", peak_bot.replace("_", " ").title())

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""

    # Apply Jorge branding and styling
    inject_jorge_branding_css()

    # Render header
    render_jorge_header()

    # Sidebar navigation
    selected_bot = render_sidebar_navigation()

    # Main content area based on selection
    if selected_bot == "🎯 Lead Bot":
        render_lead_bot_tab()
    elif selected_bot == "🏠 Buyer Bot":
        render_buyer_bot_tab()
    elif selected_bot == "💼 Seller Bot":
        render_seller_bot_tab()

    # Global performance summary
    render_performance_summary()

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #8B949E; padding: 1rem;">
            <p>Jorge AI Unified Bot Dashboard v2.0 | Standalone Edition</p>
            <p>Optimized for Jorge Real Estate Team | © 2026</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()