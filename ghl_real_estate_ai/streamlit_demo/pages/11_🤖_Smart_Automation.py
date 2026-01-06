"""
Smart Automation Dashboard - Follow-Up Automation Control
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.smart_automation import SmartAutomationEngine

st.set_page_config(page_title="Smart Automation", page_icon="🤖", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .automation-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .scheduled { border-left-color: #3B82F6; }
    .sent { border-left-color: #10B981; }
    .pending { border-left-color: #F59E0B; }
    
    .sequence-step {
        background: #F9FAFB;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #6B7280;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🤖 Smart Follow-Up Automation")
st.markdown("**Never Let a Lead Fall Through the Cracks**")

# Initialize service
automation_service = SmartAutomationEngine()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 Active Automations", "🎯 Create Sequence", "📊 Performance", "⚙️ Settings"])

with tab1:
    st.subheader("Active Automated Sequences")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.multiselect("Status", ["Scheduled", "Sent", "Pending Response"], default=["Scheduled", "Pending Response"])
    with col2:
        lead_stage = st.selectbox("Lead Stage", ["All", "Hot", "Warm", "Cold"])
    with col3:
        date_range = st.date_input("Date Range", value=(datetime.now(), datetime.now() + timedelta(days=7)))
    
    # Demo automated actions
    demo_actions = [
        {
            'lead_name': 'Carlos Mendez',
            'action_type': 'SMS',
            'scheduled_time': datetime.now() + timedelta(hours=2),
            'message': "Hey Carlos! Just checking in - still interested in Doral or should we close your file?",
            'status': 'Scheduled',
            'priority': 3,
            'sequence_step': '1 of 3'
        },
        {
            'lead_name': 'Jennifer Wilson',
            'action_type': 'SMS',
            'scheduled_time': datetime.now() + timedelta(hours=24),
            'message': "Jennifer - real talk. Are you actually still looking or should we close your file?",
            'status': 'Scheduled',
            'priority': 2,
            'sequence_step': '2 of 3'
        },
        {
            'lead_name': 'Maria Rodriguez',
            'action_type': 'Call',
            'scheduled_time': datetime.now() + timedelta(minutes=15),
            'message': "Hot lead follow-up call",
            'status': 'Pending Response',
            'priority': 1,
            'sequence_step': 'Immediate'
        }
    ]
    
    for action in demo_actions:
        status_class = action['status'].lower().replace(' ', '_')
        priority_icon = "🔥" if action['priority'] == 1 else "⚠️" if action['priority'] == 2 else "📅"
        
        st.markdown(f"""
        <div class='automation-card {status_class}'>
            <h3>{priority_icon} {action['lead_name']} - {action['action_type']}</h3>
            <p><strong>Scheduled:</strong> {action['scheduled_time'].strftime('%Y-%m-%d %I:%M %p')}</p>
            <p><strong>Sequence:</strong> Step {action['sequence_step']}</p>
            <p><strong>Message:</strong> "{action['message']}"</p>
            <p><strong>Status:</strong> <span style='color: {"#3B82F6" if action["status"] == "Scheduled" else "#10B981" if action["status"] == "Sent" else "#F59E0B"}'>{action['status']}</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        with col_btn1:
            if st.button("✏️ Edit", key=f"edit_{action['lead_name']}"):
                st.info("Edit functionality")
        with col_btn2:
            if st.button("⏭️ Send Now", key=f"send_{action['lead_name']}"):
                st.success("Message sent!")
        with col_btn3:
            if st.button("⏸️ Pause", key=f"pause_{action['lead_name']}"):
                st.warning("Sequence paused")
        with col_btn4:
            if st.button("🗑️ Cancel", key=f"cancel_{action['lead_name']}"):
                st.error("Sequence cancelled")

with tab2:
    st.subheader("Create New Automation Sequence")
    
    col_create1, col_create2 = st.columns(2)
    
    with col_create1:
        st.markdown("**Select Lead:**")
        lead_select = st.selectbox("Lead", ["Carlos Mendez", "Jennifer Wilson", "Maria Rodriguez", "Mike Chen"])
        
        st.markdown("**Sequence Type:**")
        sequence_type = st.radio(
            "Type",
            ["Re-engagement (3-step)", "Follow-up (2-step)", "Break-up Text (1-step)", "Custom"]
        )
        
        st.markdown("**Start Time:**")
        start_time = st.selectbox("When to start?", ["Immediately", "In 2 hours", "In 24 hours", "In 3 days", "Custom"])
    
    with col_create2:
        st.markdown("**Preview Sequence:**")
        
        if sequence_type == "Re-engagement (3-step)":
            st.markdown("""
            <div class='sequence-step'>
                <strong>Step 1 (Day 0):</strong><br>
                "Hey {name}! Just checking in - still interested in {location} or should we close your file?"
            </div>
            <div class='sequence-step'>
                <strong>Step 2 (Day 2 if no response):</strong><br>
                "{name} - real talk. Are you actually still looking or should we close your file?"
            </div>
            <div class='sequence-step'>
                <strong>Step 3 (Day 4 if no response):</strong><br>
                "Hey {name}, last text! If you want back in later just reply 'I'm back'"
            </div>
            """, unsafe_allow_html=True)
        elif sequence_type == "Follow-up (2-step)":
            st.markdown("""
            <div class='sequence-step'>
                <strong>Step 1 (Day 0):</strong><br>
                "Hey {name}! Quick update on {location} properties. Want me to send what I found?"
            </div>
            <div class='sequence-step'>
                <strong>Step 2 (Day 2 if no response):</strong><br>
                "Still thinking about it or should we hold off for now? No worries either way!"
            </div>
            """, unsafe_allow_html=True)
        elif sequence_type == "Break-up Text (1-step)":
            st.markdown("""
            <div class='sequence-step'>
                <strong>Single Message:</strong><br>
                "{name} - just checking. Still interested or should we close your file? No judgment!"
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🚀 Create Automation", type="primary"):
        st.success(f"✅ Automation sequence created for {lead_select}!")
        st.balloons()

with tab3:
    st.subheader("Automation Performance Metrics")
    
    # Summary metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        st.metric("Active Sequences", "45", "+5 today")
    with col_m2:
        st.metric("Messages Sent", "23 today", "+3")
    with col_m3:
        st.metric("Response Rate", "42%", "+8%")
    with col_m4:
        st.metric("Re-engagement Success", "38%", "+12%")
    
    st.markdown("---")
    
    # Performance by sequence type
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("**Response Rate by Sequence Type**")
        import pandas as pd
        data = pd.DataFrame({
            'Sequence': ['Break-up Text', 'Re-engagement', 'Follow-up', 'Custom'],
            'Response Rate': [42, 38, 28, 31]
        })
        st.bar_chart(data.set_index('Sequence'))
    
    with col_chart2:
        st.markdown("**Best Sending Times**")
        time_data = pd.DataFrame({
            'Time': ['9-11am', '12-2pm', '3-5pm', '6-8pm'],
            'Response Rate': [35, 42, 38, 29]
        })
        st.bar_chart(time_data.set_index('Time'))
    
    st.markdown("---")
    
    st.markdown("### 📊 Detailed Statistics")
    
    stats_data = {
        'Metric': ['Total Sequences Created', 'Currently Active', 'Completed Successfully', 'Cancelled/Stopped', 'Average Response Time', 'Best Performing Day', 'Most Effective Message'],
        'Value': ['312', '45', '198 (63%)', '69 (22%)', '2.3 hours', 'Tuesday', 'Break-up text variant A']
    }
    
    st.table(pd.DataFrame(stats_data))
    
    st.info("💡 **Insight:** Break-up texts sent on Tuesday afternoon (2-4pm) have the highest response rate at 48%")

with tab4:
    st.subheader("⚙️ Automation Settings")
    
    st.markdown("### General Settings")
    
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.checkbox("Enable automation for new leads", value=True)
        st.checkbox("Auto-pause after 3 no-responses", value=True)
        st.checkbox("Send notifications on responses", value=True)
        
        st.markdown("**Default Timing:**")
        st.slider("Hours between re-engagement attempts", 24, 120, 48)
        st.slider("Maximum follow-up attempts", 1, 5, 3)
    
    with col_s2:
        st.checkbox("Respect quiet hours (9pm-9am)", value=True)
        st.checkbox("Skip weekends", value=False)
        st.checkbox("A/B test message variations", value=True)
        
        st.markdown("**Priority Settings:**")
        st.selectbox("Hot leads:", ["Call first, then SMS", "SMS only", "Both simultaneously"])
        st.selectbox("Cold leads:", ["Standard sequence", "Aggressive re-engagement", "Minimal touch"])
    
    st.markdown("---")
    
    st.markdown("### Jorge's Break-Up Text Variations")
    
    st.text_area("Variation A (Current Winner - 42% response rate):", 
                 "Hey {name}, just checking - still interested or should we close your file? No worries either way!")
    
    st.text_area("Variation B (Testing - 38% response rate):",
                 "{name} - real talk. Are you actually still looking or have you given up? No judgment!")
    
    st.text_area("Variation C (Testing - 35% response rate):",
                 "Hey {name}, last check. Still want us looking out for you or we good to close this out?")
    
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6B7280; padding: 2rem;'>
    <p><strong>🤖 Smart Automation Engine</strong> | Powered by Jorge's Proven Sequences</p>
    <p style='font-size: 0.875rem;'>42% response rate on break-up texts • Never drop a lead again</p>
</div>
""", unsafe_allow_html=True)
