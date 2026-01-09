import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add project root to sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
from ghl_real_estate_ai.services.demo_state import DemoStateManager

# Page config - Mobile style
st.set_page_config(
    page_title="My Home Search - Jorge Salas",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Mobile App Look
st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f5;
        background-image: radial-gradient(#e5e7eb 1px, transparent 1px);
        background-size: 20px 20px;
    }
    .main .block-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem 1rem;
        background-color: white;
        border-radius: 30px;
        box-shadow: 0 20px 40px -5px rgba(0,0,0,0.2);
        border: 8px solid #1a1a1a;
        min-height: 80vh;
        position: relative;
    }
    /* Hide default Streamlit elements for app-feel */
    [data-testid="stHeader"] {
        display: none;
    }
    [data-testid="stSidebar"] {
        display: none;
    }
    .property-card {
        background-color: white;
        padding: 0;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid #eee;
        overflow: hidden;
    }
    .card-img-placeholder {
        height: 180px;
        background: linear-gradient(135deg, #e0e7ff 0%, #f3f4f6 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
    }
    .card-content {
        padding: 1.25rem;
    }
    .price-tag {
        color: #006AFF;
        font-size: 1.4rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
    }
    .badge {
        background-color: #f0f7ff;
        color: #006AFF;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 4px;
    }
    .bottom-nav {
        position: absolute;
        bottom: 20px;
        left: 20px;
        right: 20px;
        background: white;
        padding: 1rem;
        display: flex;
        justify-content: space-around;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown("""
<div style='text-align: center; padding: 1rem 0 2rem 0;'>
    <h3 style='margin-bottom: 0;'>Welcome back, Michael! 👋</h3>
    <p style='color: #666; font-size: 0.9rem;'>Jorge's AI found new matches for you today.</p>
</div>
""", unsafe_allow_html=True)

# Initialize Matcher
market = st.session_state.get("market_key", "Rancho")
listings_file = "property_listings_rancho.json" if market == "Rancho" else "property_listings.json"
listings_path = project_root / "ghl_real_estate_ai" / "data" / "knowledge_base" / listings_file
matcher = PropertyMatcher(listings_path=str(listings_path))

# Initialize State Manager
state_mgr = DemoStateManager()
custom_listings = state_mgr.get_all_listings()

# Sidebar Settings (Hidden by default but accessible)
with st.sidebar:
    st.header("Search Settings")
    current_market = st.selectbox("Market", ["Austin", "Rancho"], index=0 if market == "Austin" else 1)
    if st.button("Apply Changes"):
        st.session_state.market_key = current_market
        st.rerun()
    
    if st.button("Reset Demo Data"):
        state_mgr.clear_listings()
        st.rerun()

# User Criteria Toggles
with st.expander("🎯 My Search Criteria"):
    budget = st.slider("Max Budget", 300000, 2000000, 1200000, step=50000)
    beds = st.number_input("Min Bedrooms", 1, 6, 3)
    location = st.text_input("Preferred Neighborhood", "Alta Loma" if market == "Rancho" else "Downtown")
    
    if st.button("Update My Profile", use_container_width=True):
        st.success("Synced with Jorge's team!")
        st.balloons()

# Property Feed
st.markdown("#### 🏠 Your Top Matches")

# Get standard matches
standard_matches = matcher.find_matches({"budget": budget, "bedrooms": beds, "location": location})

# Combine with custom listings (Custom first)
matches = custom_matches + standard_matches

if not matches:
    st.info("No matches found for your exact criteria. broadening your search...")
    matches = matcher.find_matches({"budget": budget * 1.2}, limit=2)

for prop in matches:
    with st.container():
        st.markdown(f"""
        <div class="property-card">
            <div class="card-img-placeholder">🏠</div>
            <div class="card-content">
                <div class="price-tag">${prop['price']:,}</div>
                <div style='font-weight: 700; font-size: 1.1rem; margin-bottom: 0.25rem;'>{prop['title']}</div>
                <div style='color: #666; font-size: 0.85rem; margin-bottom: 0.75rem;'>
                    📍 {prop['address']['neighborhood']}
                </div>
                <div style='margin-bottom: 0.75rem;'>
                    <span class="badge">{prop['bedrooms']} Beds</span>
                    <span class="badge">{prop['bathrooms']} Baths</span>
                    <span class="badge">{prop.get('sqft', 'N/A')} sqft</span>
                </div>
                <div style='font-size: 0.8rem; color: #444; line-height: 1.4;'>
                    {prop['description'][:90]}...
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("❤️ Save", key=f"save_{prop['id']}", use_container_width=True):
                st.toast(f"Saved {prop['title']}!")
        with c2:
            if st.button("💬 Chat about it", key=f"chat_{prop['id']}", use_container_width=True):
                st.toast("Connecting to Jorge's AI...")

# Footer / Bottom Nav Spacer
st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

st.markdown("""
<div class='bottom-nav'>
    <div style='text-align: center; color: #006AFF;'>
        <div style='font-size: 1.5rem;'>🏠</div>
        <div style='font-size: 0.7rem; font-weight: 700;'>Feed</div>
    </div>
    <div style='text-align: center; color: #999;'>
        <div style='font-size: 1.5rem;'>❤️</div>
        <div style='font-size: 0.7rem;'>Saved</div>
    </div>
    <div style='text-align: center; color: #999;'>
        <div style='font-size: 1.5rem;'>💬</div>
        <div style='font-size: 0.7rem;'>Chat</div>
    </div>
    <div style='text-align: center; color: #999;'>
        <div style='font-size: 1.5rem;'>⚙️</div>
        <div style='font-size: 0.7rem;'>Settings</div>
    </div>
</div>
""", unsafe_allow_html=True)
