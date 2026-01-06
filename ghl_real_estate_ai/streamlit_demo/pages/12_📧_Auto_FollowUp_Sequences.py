"""
Auto Follow-Up Sequences Demo - Agent 4: Automation Genius
Demo page for automated nurture campaigns
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.auto_followup_sequences import (
    AutoFollowUpSequences, 
    Channel, 
    TriggerType, 
    SequenceStatus
)

# Page config
st.set_page_config(
    page_title="Auto Follow-Up Sequences",
    page_icon="📧",
    layout="wide"
)

# Initialize service
if 'followup_service' not in st.session_state:
    st.session_state.followup_service = AutoFollowUpSequences()
if 'sequences' not in st.session_state:
    st.session_state.sequences = {}
if 'enrollments' not in st.session_state:
    st.session_state.enrollments = []

# Header
st.title("📧 Auto Follow-Up Sequences")
st.markdown("### Smart nurture campaigns that never let a lead go cold")

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Time Saved", "10-12 hrs/week")
with col2:
    st.metric("Lead Recovery", "+30%")
with col3:
    st.metric("Revenue Impact", "+$30K-40K/yr")
with col4:
    st.metric("Active Sequences", len(st.session_state.sequences))

st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Create Sequence", 
    "👥 Enroll Contacts", 
    "📊 Performance", 
    "🤖 AI Optimization",
    "⚙️ Manage Sequences"
])

with tab1:
    st.subheader("Create New Follow-Up Sequence")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Sequence Details**")
        seq_name = st.text_input("Sequence Name", "New Lead Nurture - 7 Day")
        
        trigger = st.selectbox(
            "Trigger Event",
            options=[t.value for t in TriggerType],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        target_segment = st.multiselect(
            "Target Segment (Optional)",
            ["Active Buyers", "Sellers", "Investors", "First-Time Buyers", "Luxury"],
            default=["Active Buyers"]
        )
        
        st.markdown("**Sequence Goals**")
        goals = st.multiselect(
            "What do you want to achieve?",
            ["Schedule Showing", "Get Pre-Approval", "Submit Offer", "Build Relationship"],
            default=["Schedule Showing", "Build Relationship"]
        )
    
    with col2:
        st.markdown("**Preview Template**")
        
        template_option = st.selectbox(
            "Start from Template",
            [
                "Custom (Build from Scratch)",
                "New Lead Nurture (7 days)",
                "Showing Follow-Up (3 days)",
                "Offer Submitted (5 days)",
                "Cold Lead Re-Engagement (10 days)"
            ]
        )
        
        if template_option != "Custom (Build from Scratch)":
            st.info(f"📋 Using template: {template_option}")
            if template_option == "New Lead Nurture (7 days)":
                st.markdown("""
                **Includes:**
                - Day 0: Welcome email
                - Day 1: SMS check-in
                - Day 3: Property recommendations email
                - Day 5: Phone call
                - Day 7: Market update email
                """)
    
    st.divider()
    
    st.markdown("**Sequence Steps**")
    
    num_steps = st.number_input("Number of Steps", min_value=1, max_value=15, value=5)
    
    steps = []
    for i in range(num_steps):
        with st.expander(f"📌 Step {i+1}", expanded=(i==0)):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                channel = st.selectbox(
                    "Channel",
                    options=[c.value for c in Channel],
                    key=f"channel_{i}",
                    format_func=lambda x: x.upper()
                )
            
            with col2:
                delay = st.number_input(
                    "Delay (hours)",
                    min_value=0,
                    max_value=720,
                    value=24 * i if i > 0 else 0,
                    key=f"delay_{i}"
                )
            
            with col3:
                wait_for = st.selectbox(
                    "Wait For",
                    ["Time Only", "Response", "Action"],
                    key=f"wait_{i}"
                )
            
            if channel == "email":
                subject = st.text_input(
                    "Subject Line",
                    value=f"Step {i+1}: Follow up on your home search",
                    key=f"subject_{i}"
                )
                body = st.text_area(
                    "Email Body",
                    value=f"Hi {{{{first_name}}}},\n\nJust checking in on your home search...",
                    height=100,
                    key=f"body_{i}"
                )
                content = {"subject": subject, "body": body}
                
            elif channel == "sms":
                message = st.text_area(
                    "SMS Message (160 chars)",
                    value=f"Hi {{{{first_name}}}}, quick check-in on your search! Any questions?",
                    max_chars=160,
                    key=f"sms_{i}"
                )
                content = {"message": message}
                
            elif channel == "call":
                script = st.text_area(
                    "Call Script",
                    value=f"Hi {{{{first_name}}}}, this is [Agent]. I wanted to follow up...",
                    height=100,
                    key=f"script_{i}"
                )
                content = {"script": script}
            
            else:
                content = {}
            
            steps.append({
                "channel": channel,
                "delay_hours": delay,
                "content": content,
                "wait_for": wait_for
            })
    
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("✨ Create Sequence", type="primary", use_container_width=True):
            with st.spinner("Creating sequence..."):
                sequence = st.session_state.followup_service.create_sequence(
                    name=seq_name,
                    trigger=TriggerType[trigger.upper()],
                    steps=steps,
                    target_segment={"segments": target_segment, "goals": goals}
                )
                
                st.session_state.sequences[sequence['id']] = sequence
                st.success(f"✅ Sequence '{seq_name}' created with {len(steps)} steps!")
                st.balloons()

with tab2:
    st.subheader("Enroll Contacts in Sequences")
    
    if not st.session_state.sequences:
        st.warning("⚠️ Create a sequence first in the 'Create Sequence' tab")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Select Sequence**")
            sequence_options = {seq['name']: seq_id for seq_id, seq in st.session_state.sequences.items()}
            selected_seq_name = st.selectbox("Sequence", options=list(sequence_options.keys()))
            selected_seq_id = sequence_options[selected_seq_name]
            
            selected_seq = st.session_state.sequences[selected_seq_id]
            
            # Show sequence preview
            st.info(f"""
            **{selected_seq['name']}**
            - Steps: {len(selected_seq['steps'])}
            - Trigger: {selected_seq['trigger']}
            - Status: {selected_seq['status']}
            """)
        
        with col2:
            st.markdown("**Contact Information**")
            contact_first = st.text_input("First Name", "John")
            contact_last = st.text_input("Last Name", "Doe")
            contact_email = st.text_input("Email", "john.doe@example.com")
            contact_phone = st.text_input("Phone", "+1-555-0100")
        
        st.divider()
        
        st.markdown("**Enrollment Options**")
        
        col1, col2 = st.columns(2)
        with col1:
            start_immediately = st.checkbox("Start Immediately", value=True)
            if not start_immediately:
                start_date = st.date_input("Start Date")
                start_time = st.time_input("Start Time")
        
        with col2:
            send_notification = st.checkbox("Send Enrollment Notification", value=True)
            skip_if_engaged = st.checkbox("Skip if Recently Engaged", value=True)
        
        # Custom fields
        st.markdown("**Custom Fields (for personalization)**")
        col1, col2, col3 = st.columns(3)
        with col1:
            property_type = st.selectbox("Property Interest", ["Single Family", "Condo", "Townhouse"])
        with col2:
            price_range = st.selectbox("Price Range", ["$300K-$400K", "$400K-$500K", "$500K+"])
        with col3:
            location = st.text_input("Preferred Location", "Austin, TX")
        
        custom_fields = {
            "property_type": property_type,
            "price_range": price_range,
            "location": location
        }
        
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("👤 Enroll Contact", type="primary", use_container_width=True):
                with st.spinner("Enrolling contact..."):
                    contact_data = {
                        "first_name": contact_first,
                        "last_name": contact_last,
                        "email": contact_email,
                        "phone": contact_phone
                    }
                    
                    enrollment = st.session_state.followup_service.enroll_contact(
                        sequence_id=selected_seq_id,
                        contact_id=f"contact_{len(st.session_state.enrollments)}",
                        contact_data=contact_data,
                        custom_fields=custom_fields
                    )
                    
                    st.session_state.enrollments.append(enrollment)
                    st.success(f"✅ {contact_first} {contact_last} enrolled!")
                    
                    # Show schedule
                    st.markdown("**Scheduled Touchpoints:**")
                    for step in enrollment['schedule']:
                        st.write(f"- Step {step['step_number']} ({step['channel']}): {step['scheduled_for']}")

with tab3:
    st.subheader("Sequence Performance Analytics")
    
    if not st.session_state.sequences:
        st.info("👆 Create sequences to see performance data")
    else:
        # Sequence selector
        sequence_options = {seq['name']: seq_id for seq_id, seq in st.session_state.sequences.items()}
        selected_seq_name = st.selectbox("Select Sequence", options=list(sequence_options.keys()), key="perf_seq")
        selected_seq_id = sequence_options[selected_seq_name]
        
        # Get performance data
        performance = st.session_state.followup_service.get_sequence_performance(selected_seq_id)
        
        # Key metrics
        st.markdown("**Overall Performance**")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Enrolled", performance['metrics']['total_enrolled'])
        with col2:
            st.metric("Completed", performance['metrics']['completed'])
        with col3:
            st.metric("Active", performance['metrics']['active'])
        with col4:
            st.metric("Conversion Rate", f"{performance['metrics']['conversion_rate']:.1%}")
        with col5:
            st.metric("Avg Time to Convert", performance['metrics']['avg_time_to_conversion'])
        
        st.divider()
        
        # Channel performance
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📧 Email Performance**")
            email_perf = performance['channel_performance']['email']
            
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                st.metric("Sent", email_perf['sent'])
                st.metric("Opened", email_perf['opened'])
            with subcol2:
                st.metric("Open Rate", f"{email_perf['open_rate']:.1%}")
                st.metric("Click Rate", f"{email_perf['click_rate']:.1%}")
        
        with col2:
            st.markdown("**📱 SMS Performance**")
            sms_perf = performance['channel_performance']['sms']
            
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                st.metric("Sent", sms_perf['sent'])
                st.metric("Replied", sms_perf['replied'])
            with subcol2:
                st.metric("Response Rate", f"{sms_perf['response_rate']:.1%}")
        
        st.divider()
        
        # Engagement over time
        st.markdown("**📈 Engagement Over Time**")
        
        dates = pd.date_range(start='2026-01-01', end='2026-01-07', freq='D')
        engagement_data = pd.DataFrame({
            'Date': dates,
            'Email Opens': [45, 67, 89, 123, 145, 167, 189],
            'SMS Replies': [12, 18, 24, 30, 36, 42, 48],
            'Calls Connected': [8, 11, 15, 19, 23, 27, 31]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=engagement_data['Date'], y=engagement_data['Email Opens'], 
                                name='Email Opens', mode='lines+markers'))
        fig.add_trace(go.Scatter(x=engagement_data['Date'], y=engagement_data['SMS Replies'], 
                                name='SMS Replies', mode='lines+markers'))
        fig.add_trace(go.Scatter(x=engagement_data['Date'], y=engagement_data['Calls Connected'], 
                                name='Calls Connected', mode='lines+markers'))
        
        fig.update_layout(title='Engagement Trends', xaxis_title='Date', yaxis_title='Count')
        st.plotly_chart(fig, use_container_width=True)
        
        # Step performance
        st.markdown("**📊 Step-by-Step Performance**")
        
        step_data = pd.DataFrame([
            {"Step": "Step 1 (Email)", "Sent": 250, "Engaged": 180, "Rate": 0.72},
            {"Step": "Step 2 (SMS)", "Sent": 240, "Engaged": 165, "Rate": 0.69},
            {"Step": "Step 3 (Email)", "Sent": 235, "Engaged": 155, "Rate": 0.66},
            {"Step": "Step 4 (Call)", "Sent": 230, "Engaged": 140, "Rate": 0.61},
            {"Step": "Step 5 (Email)", "Sent": 225, "Engaged": 130, "Rate": 0.58}
        ])
        
        fig = px.bar(step_data, x='Step', y='Engaged', title='Engagement by Step')
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("🤖 AI-Powered Optimization")
    
    if not st.session_state.sequences:
        st.info("👆 Create sequences to get AI optimization recommendations")
    else:
        sequence_options = {seq['name']: seq_id for seq_id, seq in st.session_state.sequences.items()}
        selected_seq_name = st.selectbox("Select Sequence to Optimize", options=list(sequence_options.keys()), key="opt_seq")
        selected_seq_id = sequence_options[selected_seq_name]
        
        st.markdown("**Optimization Goals**")
        optimization_goals = st.multiselect(
            "What would you like to optimize?",
            ["increase_open_rate", "increase_engagement", "increase_conversion", "reduce_drop_off"],
            default=["increase_conversion"]
        )
        
        if st.button("🔍 Analyze & Get Recommendations", type="primary"):
            with st.spinner("AI analyzing sequence performance..."):
                recommendations = st.session_state.followup_service.optimize_sequence(
                    selected_seq_id,
                    optimization_goals
                )
                
                st.success("✅ Analysis Complete!")
                
                # Current vs Predicted
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📊 Current Performance**")
                    st.metric("Conversion Rate", 
                             f"{recommendations['current_performance']['conversion_rate']:.1%}")
                
                with col2:
                    st.markdown("**🎯 Predicted After Optimization**")
                    predicted = recommendations['predicted_impact']['predicted_conversion_rate']
                    current = recommendations['current_performance']['conversion_rate']
                    delta = predicted - current
                    st.metric("Conversion Rate", 
                             f"{predicted:.1%}",
                             delta=f"+{delta:.1%}")
                
                st.divider()
                
                st.markdown("**💡 Recommendations**")
                
                for i, rec in enumerate(recommendations['recommendations'], 1):
                    with st.expander(f"Recommendation {i}: {rec['type'].replace('_', ' ').title()}", expanded=True):
                        st.markdown(f"**{rec['recommendation']}**")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Predicted Improvement", f"+{rec['predicted_improvement']:.1%}")
                        with col2:
                            st.metric("Confidence", f"{rec['confidence']:.0%}")
                        
                        if st.button(f"Apply Recommendation {i}", key=f"apply_{i}"):
                            st.success("✅ Recommendation applied!")

with tab5:
    st.subheader("⚙️ Manage Active Sequences")
    
    if not st.session_state.sequences:
        st.info("👆 No sequences created yet")
    else:
        for seq_id, seq in st.session_state.sequences.items():
            with st.expander(f"📧 {seq['name']} - {seq['status'].upper()}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Details**")
                    st.write(f"Trigger: {seq['trigger']}")
                    st.write(f"Steps: {len(seq['steps'])}")
                    st.write(f"Created: {seq['created_at'][:10]}")
                
                with col2:
                    st.markdown("**Stats**")
                    st.write(f"Enrolled: {seq['stats']['total_enrolled']}")
                    st.write(f"Active: {seq['stats']['active']}")
                    st.write(f"Completed: {seq['stats']['completed']}")
                
                with col3:
                    st.markdown("**Actions**")
                    
                    if seq['status'] == 'active':
                        if st.button("⏸️ Pause", key=f"pause_{seq_id}"):
                            st.session_state.followup_service.pause_sequence(seq_id)
                            st.success("Sequence paused")
                    else:
                        if st.button("▶️ Resume", key=f"resume_{seq_id}"):
                            st.session_state.followup_service.resume_sequence(seq_id)
                            st.success("Sequence resumed")
                    
                    if st.button("📝 Edit", key=f"edit_{seq_id}"):
                        st.info("Edit functionality coming soon!")
                    
                    if st.button("🗑️ Delete", key=f"delete_{seq_id}"):
                        del st.session_state.sequences[seq_id]
                        st.success("Sequence deleted")
                        st.rerun()

# Footer
st.divider()
st.markdown("""
**💡 Pro Tips:**
- Start with proven templates and customize
- Use multiple channels for better engagement
- Test send times for your audience
- Monitor performance and optimize regularly
- Personalize with custom fields
""")
