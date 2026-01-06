#!/usr/bin/env python3
"""
AI Content Personalization Demo Page
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from services.ai_content_personalization import AIContentPersonalizationService
except ImportError:
    AIContentPersonalizationService = None

st.set_page_config(page_title="AI Content Personalization", page_icon="🎨", layout="wide")

st.title("🎨 AI Content Personalization")
st.markdown("**Deliver personalized experiences across all touchpoints**")

# Service status
if AIContentPersonalizationService:
    st.success("✅ Content Personalization AI is active")
else:
    st.warning("⚠️ Running in demo mode")

# Lead selector
st.subheader("Select Lead Profile")
lead_profile = st.selectbox(
    "Choose a lead to personalize content for:",
    ["Jane Smith (High Engagement)", "Robert Chen (Medium Engagement)", "Emily Davis (Low Engagement)"]
)

# Lead data mapping
lead_data_map = {
    "Jane Smith (High Engagement)": {
        "name": "Jane Smith",
        "budget": 850000,
        "engagement_score": 88,
        "last_activity_days_ago": 1,
        "location": "Austin, TX",
        "interested_property_type": "modern_condo",
        "buyer_type": "first_time_buyer"
    },
    "Robert Chen (Medium Engagement)": {
        "name": "Robert Chen",
        "budget": 1200000,
        "engagement_score": 55,
        "last_activity_days_ago": 12,
        "location": "San Francisco, CA",
        "interested_property_type": "luxury_estate",
        "buyer_type": "investor"
    },
    "Emily Davis (Low Engagement)": {
        "name": "Emily Davis",
        "budget": 450000,
        "engagement_score": 28,
        "last_activity_days_ago": 35,
        "location": "Portland, OR",
        "interested_property_type": "starter_home",
        "buyer_type": "relocating"
    }
}

selected_lead = lead_data_map[lead_profile]

# Display lead info
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Engagement Score", f"{selected_lead['engagement_score']}/100")
with col2:
    st.metric("Budget", f"${selected_lead['budget']:,.0f}")
with col3:
    st.metric("Last Activity", f"{selected_lead['last_activity_days_ago']} days ago")
with col4:
    st.metric("Location", selected_lead['location'].split(',')[0])

st.divider()

# Personalization tabs
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Property Recommendations", "📧 Email Content", "🌐 Landing Page", "💬 Messaging"])

with tab1:
    st.subheader("Personalized Property Recommendations")
    
    if st.button("🎯 Generate Recommendations", key="prop_btn"):
        with st.spinner("Analyzing preferences and generating matches..."):
            st.success("✅ Recommendations Generated!")
            
            # Demo recommendations
            recs = [
                {
                    "title": "Modern Downtown Loft",
                    "price": selected_lead['budget'] * 0.95,
                    "match_score": 94,
                    "why": "Perfect match for your budget, style, and location preferences",
                    "priority": "🔥 High Priority"
                },
                {
                    "title": "Stylish Urban Condo",
                    "price": selected_lead['budget'] * 0.85,
                    "match_score": 88,
                    "why": "Great value with modern amenities you're looking for",
                    "priority": "⭐ Recommended"
                },
                {
                    "title": "Premium Corner Unit",
                    "price": selected_lead['budget'] * 1.08,
                    "match_score": 82,
                    "why": "Worth considering - exceptional features justify the premium",
                    "priority": "💎 Stretch Option"
                }
            ]
            
            for rec in recs:
                with st.container():
                    st.markdown(f"### {rec['title']}")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Price", f"${rec['price']:,.0f}")
                    with col_b:
                        st.metric("Match Score", f"{rec['match_score']}/100")
                    with col_c:
                        st.write(f"**{rec['priority']}**")
                    
                    st.info(f"**Why Recommended:** {rec['why']}")
                    st.button(f"Schedule Viewing →", key=f"view_{rec['title']}")
                    st.divider()

with tab2:
    st.subheader("Personalized Email Content")
    
    if st.button("✉️ Generate Email", key="email_btn"):
        engagement = selected_lead['engagement_score']
        name = selected_lead['name'].split()[0]
        
        if engagement > 70:
            subject = f"{name}, Your Dream Properties Are Here! 🏠"
            preview = "We found amazing properties matching exactly what you're looking for..."
            tone = "Enthusiastic & Urgent"
        elif engagement > 40:
            subject = f"{name}, New Listings You'll Love"
            preview = "Based on your recent activity, we think you'll love these..."
            tone = "Helpful & Informative"
        else:
            subject = f"{name}, Market Update & Property Insights"
            preview = "Staying informed helps you make the best decision. Here's what's new..."
            tone = "Educational & Patient"
        
        st.success("✅ Personalized Email Generated!")
        
        st.markdown("### Email Preview")
        st.text_input("Subject Line", value=subject, disabled=True)
        st.text_input("Preview Text", value=preview, disabled=True)
        st.text_input("Tone", value=tone, disabled=True)
        
        st.markdown("### Email Body")
        st.text_area(
            "Content",
            value=f"""Hi {name},

{preview}

Based on your preferences for {selected_lead['interested_property_type']} properties in {selected_lead['location']}, I've hand-picked 3 exceptional options that match your ${selected_lead['budget']:,.0f} budget.

Each property has been carefully selected to match your unique needs and preferences.

Ready to explore? Let's schedule a time to discuss these opportunities.

Best regards,
Your Real Estate Team""",
            height=300,
            disabled=True
        )
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.info(f"📅 Best Send Time: 9:00 AM {selected_lead['location'].split(',')[1].strip()}")
        with col_b:
            st.info(f"📊 Expected Open Rate: {65 if engagement > 60 else 45}%")

with tab3:
    st.subheader("Personalized Landing Page")
    
    if st.button("🌐 Generate Landing Page", key="landing_btn"):
        st.success("✅ Landing Page Personalized!")
        
        st.markdown("### Landing Page Preview")
        
        # Hero section
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 10px; color: white;'>
            <h1>Find Your Perfect Home in {selected_lead['location'].split(',')[0]}</h1>
            <p style='font-size: 1.2em;'>Personalized property matches based on your preferences</p>
            <button style='background: white; color: #667eea; padding: 15px 30px; border: none; border-radius: 5px; font-size: 1.1em; cursor: pointer;'>
                {"See My Matches →" if selected_lead['engagement_score'] > 60 else "Explore Properties →"}
            </button>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Featured Properties")
        prop_cols = st.columns(3)
        for i, col in enumerate(prop_cols):
            with col:
                st.image("https://via.placeholder.com/300x200/667eea/ffffff?text=Property+Image", use_container_width=True)
                st.write(f"**Property {i+1}**")
                st.write(f"${selected_lead['budget'] * (0.9 + i * 0.1):,.0f}")
                st.button("View Details", key=f"prop_{i}")
        
        st.markdown("### Why This Works")
        st.info(f"""
        **Personalization Elements:**
        - ✅ Location-specific headline ({selected_lead['location']})
        - ✅ Budget-aligned property display
        - ✅ Engagement-based CTA text
        - ✅ Device-optimized layout
        - ✅ Behavioral triggers
        """)

with tab4:
    st.subheader("Personalized Messaging")
    
    if st.button("💬 Generate Message", key="msg_btn"):
        engagement = selected_lead['engagement_score']
        name = selected_lead['name'].split()[0]
        
        if engagement > 80:
            message = f"Hi {name}! 🏠 Quick question - when would you like to schedule a viewing? I have 3 perfect matches!"
            urgency = "🔴 High Priority"
            channel = "SMS (Fastest)"
        elif engagement > 50:
            message = f"Hey {name}, I have some exciting new listings to share that match your search. Interested? 😊"
            urgency = "🟡 Medium Priority"
            channel = "SMS or Email"
        else:
            message = f"Hi {name}, hope you're doing well! Just checking in to see if you need any help with your property search."
            urgency = "🟢 Low Priority"
            channel = "Email (Patient)"
        
        st.success("✅ Personalized Message Generated!")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.text_area("Message", value=message, height=150, disabled=True)
        with col_b:
            st.metric("Urgency", urgency)
            st.metric("Best Channel", channel)
            st.metric("Expected Response Time", f"{4 if engagement > 60 else 24} hours")
        
        st.info(f"💡 **Strategy:** {'Aggressive follow-up' if engagement > 70 else 'Gentle nurturing'}")

# ROI Section
st.divider()
st.subheader("💰 Personalization Impact")

impact_cols = st.columns(4)
with impact_cols[0]:
    st.metric("Conversion Rate Lift", "+67%", "vs generic content")
with impact_cols[1]:
    st.metric("Email Open Rate", "+45%", "vs batch emails")
with impact_cols[2]:
    st.metric("Time Saved", "20 hrs/week", "automated personalization")
with impact_cols[3]:
    st.metric("Revenue Impact", "$125K/year", "additional deals")

st.success("🎨 **AI personalization delivers the right message to the right person at the right time!**")
