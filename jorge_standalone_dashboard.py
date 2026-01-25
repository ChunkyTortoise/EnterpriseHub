"""
Jorge AI Unified Bot Dashboard - Standalone Edition
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
