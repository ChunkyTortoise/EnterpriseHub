#!/usr/bin/env python3
"""
AI Smart Segmentation Demo Page
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from services.ai_smart_segmentation import AISmartSegmentationService
except ImportError:
    AISmartSegmentationService = None

st.set_page_config(page_title="AI Smart Segmentation", page_icon="🎯", layout="wide")

st.title("🎯 AI Smart Segmentation")
st.markdown("**Automatically segment leads with AI-powered behavioral analysis**")

# Service status
if AISmartSegmentationService:
    st.success("✅ Smart Segmentation AI is active")
else:
    st.warning("⚠️ Running in demo mode")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Segmentation Controls")
    
    segmentation_method = st.selectbox(
        "Segmentation Method",
        ["Behavioral", "Demographic", "Predictive", "Auto (Combined)"]
    )
    
    if st.button("🚀 Run Segmentation", type="primary"):
        with st.spinner("Analyzing leads and creating segments..."):
            # Demo data
            sample_leads = [
                {
                    "id": "lead_001",
                    "name": "John Smith",
                    "engagement_score": 92,
                    "lead_score": 88,
                    "budget": 750000,
                    "last_activity_days_ago": 1,
                    "buyer_type": "first_time_buyer",
                    "interested_property_type": "condo",
                    "location": "Downtown"
                },
                {
                    "id": "lead_002",
                    "name": "Sarah Johnson",
                    "engagement_score": 45,
                    "lead_score": 55,
                    "budget": 1500000,
                    "last_activity_days_ago": 20,
                    "buyer_type": "luxury_buyer",
                    "interested_property_type": "estate",
                    "location": "Waterfront"
                },
                {
                    "id": "lead_003",
                    "name": "Mike Chen",
                    "engagement_score": 88,
                    "lead_score": 92,
                    "budget": 900000,
                    "last_activity_days_ago": 2,
                    "buyer_type": "investor",
                    "interested_property_type": "multi_family",
                    "location": "Urban Core"
                },
                {
                    "id": "lead_004",
                    "name": "Emily Davis",
                    "engagement_score": 35,
                    "lead_score": 40,
                    "budget": 500000,
                    "last_activity_days_ago": 45,
                    "buyer_type": "relocating",
                    "interested_property_type": "townhouse",
                    "location": "Suburbs"
                },
                {
                    "id": "lead_005",
                    "name": "Robert Wilson",
                    "engagement_score": 78,
                    "lead_score": 82,
                    "budget": 650000,
                    "last_activity_days_ago": 5,
                    "buyer_type": "first_time_buyer",
                    "interested_property_type": "single_family",
                    "location": "Growing Neighborhood"
                }
            ]
            
            # Display results
            st.success("✅ Segmentation Complete!")
            
            st.subheader("📊 Segment Overview")
            
            # Behavioral segments (demo)
            segments = {
                "🔥 Hot Engagers": {
                    "size": 2,
                    "leads": ["John Smith", "Mike Chen"],
                    "avg_score": 90,
                    "actions": ["Immediate follow-up", "VIP treatment", "Fast-track closings"]
                },
                "🌡️ Warming Up": {
                    "size": 1,
                    "leads": ["Robert Wilson"],
                    "avg_score": 78,
                    "actions": ["Regular property updates", "Educational content", "Open house invites"]
                },
                "❄️ Re-engagement Needed": {
                    "size": 2,
                    "leads": ["Sarah Johnson", "Emily Davis"],
                    "avg_score": 40,
                    "actions": ["Win-back campaign", "Special offers", "Market updates"]
                }
            }
            
            for seg_name, seg_data in segments.items():
                with st.expander(f"{seg_name} ({seg_data['size']} leads)", expanded=True):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Segment Size", seg_data['size'])
                    with col_b:
                        st.metric("Avg Score", f"{seg_data['avg_score']}/100")
                    with col_c:
                        st.metric("Total Value", f"${seg_data['size'] * 750000:,.0f}")
                    
                    st.write("**Leads in Segment:**")
                    for lead in seg_data['leads']:
                        st.write(f"• {lead}")
                    
                    st.write("**Recommended Actions:**")
                    for action in seg_data['actions']:
                        st.write(f"✓ {action}")

with col2:
    st.subheader("📈 Segmentation Insights")
    
    st.metric("Total Leads Analyzed", "5")
    st.metric("Segments Created", "3")
    st.metric("Conversion Rate Lift", "+45%")
    
    st.divider()
    
    st.subheader("💡 Key Insights")
    st.info("""
    **Hot Engagers segment** shows highest potential:
    - 40% of total leads
    - 90/100 avg score
    - Ready for immediate action
    """)
    
    st.warning("""
    **Re-engagement segment** needs attention:
    - 40% of total leads
    - Risk of churn
    - Launch win-back campaign
    """)

# Features section
st.divider()
st.subheader("🎯 Segmentation Features")

feature_cols = st.columns(4)

with feature_cols[0]:
    st.markdown("### 🧠 AI Learning")
    st.write("Continuously improves segmentation based on outcomes")

with feature_cols[1]:
    st.markdown("### 📊 Multi-Factor")
    st.write("Analyzes behavior, demographics, and predictions")

with feature_cols[2]:
    st.markdown("### ⚡ Real-Time")
    st.write("Updates segments as lead behavior changes")

with feature_cols[3]:
    st.markdown("### 🎯 Actionable")
    st.write("Provides specific actions for each segment")

# ROI Calculator
st.divider()
st.subheader("💰 Segmentation ROI Calculator")

calc_col1, calc_col2 = st.columns(2)

with calc_col1:
    total_leads = st.number_input("Total Leads", value=100, min_value=1)
    avg_deal_value = st.number_input("Avg Deal Value ($)", value=15000, min_value=1000)
    baseline_conversion = st.slider("Baseline Conversion Rate (%)", 1, 20, 5)

with calc_col2:
    segmented_lift = st.slider("Expected Lift from Segmentation (%)", 10, 100, 45)
    
    # Calculate ROI
    baseline_deals = (total_leads * baseline_conversion) / 100
    baseline_revenue = baseline_deals * avg_deal_value
    
    new_conversion = baseline_conversion * (1 + segmented_lift / 100)
    new_deals = (total_leads * new_conversion) / 100
    new_revenue = new_deals * avg_deal_value
    
    additional_revenue = new_revenue - baseline_revenue
    
    st.metric("Additional Revenue", f"${additional_revenue:,.0f}", f"+{segmented_lift}%")
    st.metric("Additional Deals", f"{new_deals - baseline_deals:.1f}")
    st.metric("Time Saved", "15 hours/week", "Automated segmentation")

st.success(f"💡 **Smart segmentation can generate ${additional_revenue:,.0f} in additional revenue!**")
