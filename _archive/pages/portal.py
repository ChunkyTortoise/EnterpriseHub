import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime
import json
import asyncio

# Add project root to sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
from ghl_real_estate_ai.services.demo_state import DemoStateManager
from ghl_real_estate_ai.services.telemetry_service import TelemetryService
from ghl_real_estate_ai.ghl_utils.ghl_api_client import GHLAPIClient

# Page config - Mobile style
st.set_page_config(
    page_title="Architectural Portal - Lyrio.io",
    page_icon="🏘️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize Services
telemetry = TelemetryService()
state_mgr = DemoStateManager()
matcher = PropertyMatcher()
ghl_client = GHLAPIClient()

# Mock Lead ID for Demo (In production, this is from the URL slug)
# For demo purposes, we mapping michael_scott_789 to a real GHL contact if available
contact_id = st.query_params.get("contact_id", "REDACTED_CONTACT_ID")
lead_id = st.query_params.get("id", "michael_scott_789")
lead_name = lead_id.split("_")[0].capitalize()

# Custom CSS for Architectural Branding
st.markdown("""
<style>
    .stApp {
        background-color: #FAFAFA;
    }
    .main .block-container {
        max-width: 450px;
        margin: 1rem auto;
        padding: 2rem 1.5rem;
        background-color: white;
        border-radius: 40px;
        box-shadow: 0 30px 60px -12px rgba(0,0,0,0.25);
        border: 12px solid #0F172A;
        min-height: 90vh;
        position: relative;
    }
    .property-card {
        background: white;
        border-radius: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
        border: 1px solid #F1F5F9;
        overflow: hidden;
        transition: transform 0.2s;
    }
    .agentic-summary {
        background-color: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 1rem;
        font-size: 0.85rem;
        color: #334155;
        font-style: italic;
        margin-top: 1rem;
        border-radius: 0 8px 8px 0;
    }
    .price-badge {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1E293B;
    }
    .status-pill {
        background: #DCFCE7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 99px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown(f"""
<div style='text-align: left; padding: 0.5rem 0 1.5rem 0;'>
    <span class="status-pill">Architectural Match Active</span>
    <h2 style='margin-top: 0.5rem;'>For {lead_name}</h2>
    <p style='color: #64748B; font-size: 0.95rem;'>Proprietary matches identified by Lyrio AI.</p>
</div>
""", unsafe_allow_html=True)

# Search Criteria (Linked to GHL Bi-Directional Sync)
with st.expander("🛠️ Architectural Search Criteria"):
    budget = st.slider("Target Cap", 300000, 2000000, 1200000, step=50000)
    beds = st.number_input("Min Bedrooms", 1, 6, 3)
    location = st.text_input("Geography", "Rancho Cucamonga, CA")
    
    if st.button("Synchronize with Lyrio Core", use_container_width=True):
        # 1. Telemetry
        telemetry.record_interaction(lead_id, "update_criteria", {"budget": budget, "beds": beds, "location": location})
        
        # 2. Bi-Directional GHL Sync (Phase 3)
        try:
            # Update GHL Custom Fields
            # Note: In production, these field IDs would come from settings
            ghl_client.update_custom_field(contact_id, "budget", budget)
            ghl_client.update_custom_field(contact_id, "preferred_location", location)
            
            # Add 'Architectural Update' Tag
            ghl_client.add_tag_to_contact(contact_id, "Portal-Activity")
            ghl_client.add_tag_to_contact(contact_id, "Strategic-Update")
            
            st.success("Preferences Hardened & Synced to GHL!")
            st.balloons()
        except Exception as e:
            # Fallback for demo mode
            st.warning("Ecosystem Sync: Simulation Mode Active (Local Only)")
            st.info("In production, this would update GHL Custom Fields via API.")
            st.balloons()

# Property Feed Logic
st.markdown("#### 💎 Priority Matches")

# Get standard matches
criteria = {"budget": budget, "bedrooms": beds, "location": location}
matches = matcher.find_matches(criteria)

async def display_matches():
    for prop in matches:
        with st.container():
            # Get Agentic Reasoning (Phase 2 Upgrade)
            reasoning = await matcher.agentic_explain_match(prop, criteria)
            
            st.markdown(f"""
            <div class="property-card">
                <div style="height: 200px; background: #E2E8F0; display: flex; align-items: center; justify-content: center; font-size: 4rem;">🏘️</div>
                <div style="padding: 1.5rem;">
                    <div class="price-badge">${prop['price']:,}</div>
                    <div style="font-weight: 700; color: #475569; margin-bottom: 0.5rem;">{prop['address']['street']}, {prop['address']['city']}</div>
                    <div style="display: flex; gap: 10px; margin-bottom: 1rem;">
                        <span style="font-size: 0.8rem; color: #64748B;">🛏️ {prop['bedrooms']} Beds</span>
                        <span style="font-size: 0.8rem; color: #64748B;">🛁 {prop['bathrooms']} Baths</span>
                    </div>
                    <div class="agentic-summary">
                        "Architect's Note: {reasoning}"
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔒 Secure Listing", key=f"save_{prop['id']}", use_container_width=True):
                    telemetry.record_interaction(lead_id, "save", {"prop_id": prop['id']})
                    st.toast("Listing Secured in your Vault.")
            with c2:
                if st.button("💬 Consult AI", key=f"chat_{prop['id']}", use_container_width=True):
                    telemetry.record_interaction(lead_id, "chat", {"prop_id": prop['id']})
                    st.toast("Architectural Consultant Notified.")

# Run async display
asyncio.run(display_matches())

# Footer Nav
st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); width: 350px; background: #0F172A; padding: 1rem; border-radius: 30px; display: flex; justify-content: space-around; z-index: 1000;'>
    <div style='color: white; font-size: 1.2rem;'>🏠</div>
    <div style='color: #64748B; font-size: 1.2rem;'>💎</div>
    <div style='color: #64748B; font-size: 1.2rem;'>🧠</div>
    <div style='color: #64748B; font-size: 1.2rem;'>👤</div>
</div>
""", unsafe_allow_html=True)