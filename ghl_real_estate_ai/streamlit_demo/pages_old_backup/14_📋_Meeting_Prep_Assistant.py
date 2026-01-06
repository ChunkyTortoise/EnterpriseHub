"""
Meeting Prep Assistant Demo - Agent 4: Automation Genius
Demo page for automated meeting preparation and briefing documents
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.meeting_prep_assistant import MeetingPrepAssistant, MeetingType

# Page config
st.set_page_config(
    page_title="Meeting Prep Assistant",
    page_icon="📋",
    layout="wide"
)

# Initialize service
if 'meeting_service' not in st.session_state:
    st.session_state.meeting_service = MeetingPrepAssistant()
if 'briefs' not in st.session_state:
    st.session_state.briefs = []

# Header
st.title("📋 Meeting Prep Assistant")
st.markdown("### Auto-generated briefing documents for every client meeting")

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Time Saved", "2-3 hrs/week")
with col2:
    st.metric("Briefs Created", len(st.session_state.briefs))
with col3:
    st.metric("Revenue Impact", "+$15K-20K/yr")
with col4:
    st.metric("Success Rate", "92%")

st.divider()

# Main content
tab1, tab2, tab3 = st.tabs(["🎯 Generate Brief", "📚 Recent Briefs", "📊 Analytics"])

with tab1:
    st.subheader("Generate Meeting Brief")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Meeting Details**")
        meeting_type = st.selectbox(
            "Meeting Type",
            options=[m.value for m in MeetingType],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        meeting_date = st.date_input("Meeting Date", value=datetime.now())
        meeting_time = st.time_input("Meeting Time", value=datetime.now().time())
        
        contact_name = st.text_input("Contact Name", "John Doe")
        contact_id = st.text_input("Contact ID (from GHL)", "contact_12345")
    
    with col2:
        st.markdown("**Additional Context**")
        property_id = st.text_input("Property ID (optional)", "")
        
        include_sections = st.multiselect(
            "Include Sections",
            [
                "Contact Summary",
                "Recent Activity",
                "Property Info",
                "Talking Points",
                "Recommendations",
                "Required Documents",
                "Meeting Agenda"
            ],
            default=[
                "Contact Summary",
                "Recent Activity",
                "Talking Points",
                "Recommendations"
            ]
        )
    
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("📋 Generate Brief", type="primary", use_container_width=True):
            with st.spinner("Generating meeting brief..."):
                brief = st.session_state.meeting_service.prepare_meeting_brief(
                    meeting_type=MeetingType[meeting_type.upper()],
                    contact_id=contact_id,
                    property_id=property_id if property_id else None,
                    meeting_date=datetime.combine(meeting_date, meeting_time)
                )
                
                st.session_state.briefs.append(brief)
                
                st.success("✅ Meeting brief generated!")
                
                # Display brief
                st.divider()
                st.markdown("### 📄 Meeting Brief Preview")
                
                # Header
                st.markdown(f"**{meeting_type.replace('_', ' ').title()}**")
                st.markdown(f"**Date:** {meeting_date} at {meeting_time}")
                st.markdown(f"**Contact:** {brief['contact_summary']['name']}")
                
                st.divider()
                
                # Contact Summary
                if "Contact Summary" in include_sections:
                    st.markdown("### 👤 Contact Summary")
                    summary = brief['contact_summary']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Stage:** {summary['stage']}")
                        st.write(f"**First Contact:** {summary['first_contact']}")
                    with col2:
                        st.write(f"**Total Interactions:** {summary['total_interactions']}")
                        st.write(f"**Last Interaction:** {summary['last_interaction']}")
                    with col3:
                        st.write(f"**Email:** {summary['email']}")
                        st.write(f"**Phone:** {summary['phone']}")
                    
                    st.markdown("**Preferences:**")
                    for key, value in summary['preferences'].items():
                        st.write(f"- {key.replace('_', ' ').title()}: {value}")
                
                # Recent Activity
                if "Recent Activity" in include_sections:
                    st.divider()
                    st.markdown("### 📊 Recent Activity")
                    for activity in brief['recent_activity']:
                        st.write(f"**{activity['date']}** - {activity['type'].replace('_', ' ').title()}: {activity['details']}")
                
                # Property Info
                if "Property Info" in include_sections and brief.get('property_info'):
                    st.divider()
                    st.markdown("### 🏠 Property Information")
                    prop = brief['property_info']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Address:** {prop['address']}")
                        st.write(f"**Price:** ${prop['price']:,}")
                        st.write(f"**Beds/Baths:** {prop['bedrooms']}BR / {prop['bathrooms']}BA")
                    with col2:
                        st.write(f"**Days on Market:** {prop['days_on_market']}")
                        st.write(f"**Status:** Active")
                
                # Talking Points
                if "Talking Points" in include_sections:
                    st.divider()
                    st.markdown("### 💡 Talking Points")
                    for i, point in enumerate(brief['talking_points'], 1):
                        st.write(f"{i}. {point}")
                
                # Recommendations
                if "Recommendations" in include_sections:
                    st.divider()
                    st.markdown("### ✅ Recommended Actions")
                    for i, rec in enumerate(brief['recommendations'], 1):
                        st.write(f"{i}. {rec}")
                
                # Required Documents
                if "Required Documents" in include_sections:
                    st.divider()
                    st.markdown("### 📁 Documents to Bring")
                    for doc in brief['documents_to_bring']:
                        st.write(f"📄 {doc}")
                
                # Agenda
                if "Meeting Agenda" in include_sections:
                    st.divider()
                    st.markdown("### 🕐 Meeting Agenda")
                    for item in brief['agenda']:
                        st.write(f"**{item['time']}** - {item['topic']}")
                
                st.balloons()

with tab2:
    st.subheader("Recent Meeting Briefs")
    
    if not st.session_state.briefs:
        st.info("👆 Generate your first meeting brief to see it here")
    else:
        for brief in reversed(st.session_state.briefs[-10:]):  # Show last 10
            with st.expander(
                f"📋 {brief['meeting_type'].replace('_', ' ').title()} - "
                f"{brief['contact_summary']['name']} - "
                f"{brief['meeting_date'][:10]}"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Contact:**")
                    st.write(f"Name: {brief['contact_summary']['name']}")
                    st.write(f"Stage: {brief['contact_summary']['stage']}")
                    st.write(f"Interactions: {brief['contact_summary']['total_interactions']}")
                
                with col2:
                    st.markdown("**Meeting:**")
                    st.write(f"Type: {brief['meeting_type'].replace('_', ' ').title()}")
                    st.write(f"Date: {brief['meeting_date'][:10]}")
                    st.write(f"Generated: {brief['generated_at'][:10]}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📥 Download PDF", key=f"download_{brief['id']}"):
                        st.success("Brief downloaded!")
                with col2:
                    if st.button("📧 Email Brief", key=f"email_{brief['id']}"):
                        st.success("Brief emailed!")
                with col3:
                    if st.button("🔄 Regenerate", key=f"regen_{brief['id']}"):
                        st.info("Regenerating...")

with tab3:
    st.subheader("Meeting Analytics")
    
    # Sample data
    import pandas as pd
    import plotly.express as px
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Meetings by Type**")
        meeting_types = pd.DataFrame({
            'Type': ['Buyer Consultation', 'Seller Consultation', 'Showing', 'Offer Review'],
            'Count': [12, 8, 15, 5]
        })
        fig = px.pie(meeting_types, values='Count', names='Type')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Meeting Success Rate**")
        success_data = pd.DataFrame({
            'Outcome': ['Successful', 'Follow-up Needed', 'Not Interested'],
            'Count': [23, 12, 5]
        })
        fig = px.bar(success_data, x='Outcome', y='Count')
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.markdown("**Meetings Over Time**")
    dates = pd.date_range(start='2026-01-01', end='2026-01-07', freq='D')
    meetings_data = pd.DataFrame({
        'Date': dates,
        'Meetings': [3, 5, 4, 6, 5, 7, 6]
    })
    fig = px.line(meetings_data, x='Date', y='Meetings')
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.divider()
st.markdown("""
**💡 Pro Tips:**
- Generate briefs 24 hours before meetings
- Review recent activity for conversation starters
- Update contact preferences after each meeting
- Use talking points to stay on track
- Follow up on recommended actions
""")
