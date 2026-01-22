"""
Jorge's AI Seller Bot - Unified Dashboard with Tactical Negotiation
Complete seller automation system integrating:
- 4-Question Qualification Engine
- Vague Answer Detection (Pillar 1)
- Take-Away Close Escalation
- Semantic Response Quality Analysis
- Vapi Voice AI Handoff Integration
- Tone & Compliance Monitoring

Built specifically for Jorge's GHL system.
"""

import streamlit as st
import asyncio
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys
import os

# Add the services directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services'))

from ghl_real_estate_ai.streamlit_demo.obsidian_theme import (
    inject_elite_css,
    style_obsidian_chart,
    render_dossier_block,
    render_neural_progress,
    get_svg_icon,
    render_terminal_log,
    render_voice_waveform,
    render_tactical_dock,
    render_journey_line
)

class JorgeSellerAPIClient:
    """Client for Jorge's Seller Negotiation API."""
    
    async def get_seller_metrics(self) -> Dict[str, Any]:
        return {
            "negotiation_stats": {
                "active_negotiations": 12,
                "qualification_rate": 68.5,
                "avg_motivation_score": 82.4,
                "vague_answers_caught": 45,
                "take_away_closes_triggered": 8
            },
            "performance": {
                "conversion_rate": 12.5,
                "avg_response_time": "45s",
                "compliance_score": 99.8
            }
        }

    async def get_seller_pipeline(self) -> List[Dict[str, Any]]:
        return [
            {"id": "seller_001", "name": "Robert Miller", "property": "123 Maple St", "score": 92.5, "priority": "immediate", "motivation": "Relocating", "status": "Negotiation Active"},
            {"id": "seller_002", "name": "Linda Garcia", "property": "456 Oak Ave", "score": 78.2, "priority": "high", "motivation": "Upsizing", "status": "Qualification Phase"},
            {"id": "seller_003", "name": "Thomas Wright", "property": "789 Pine Dr", "score": 45.0, "priority": "cold", "motivation": "Just checking", "status": "Dormant"}
        ]

@st.cache_resource
def get_seller_api_client():
    return JorgeSellerAPIClient()

def render_seller_negotiation_section(api_client: JorgeSellerAPIClient):
    """Render the Seller Negotiation section."""
    st.markdown(f'### {get_svg_icon(