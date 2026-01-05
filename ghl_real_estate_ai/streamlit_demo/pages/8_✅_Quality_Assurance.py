"""
GHL Real Estate AI - Quality Assurance
Monitor conversation quality and compliance
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from ghl_real_estate_ai.services.quality_assurance import QualityAssuranceEngine
    SERVICE_AVAILABLE = True
except ImportError as e:
    SERVICE_AVAILABLE = False
    import_error = str(e)

# Page config
st.set_page_config(
    page_title="Quality Assurance",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .qa-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 15px 0;
    }
    .qa-score-excellent {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .qa-score-good {
        background: linear-gradient(135deg, #17a2b8 0%, #0dcaf0 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .qa-score-warning {
        background: linear-gradient(135deg, #ffc107 0%, #ffca2c 100%);
        color: black;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .qa-score-danger {
        background: linear-gradient(135deg, #dc3545 0%, #e35d6a 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .issue-card {
        border-left: 4px solid #dc3545;
        background-color: #f8f9fa;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .compliance-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 15px;
        font-size: 0.85em;
        font-weight: bold;
        margin: 3px;
    }
    .badge-pass {
        background-color: #28a745;
        color: white;
    }
    .badge-fail {
        background-color: #dc3545;
        color: white;
    }
    .badge-warning {
        background-color: #ffc107;
        color: black;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("✅ Quality Assurance")
st.markdown("**Monitor conversation quality and ensure compliance**")
st.markdown("---")

# Check service availability
if not SERVICE_AVAILABLE:
    st.error(f"⚠️ Quality Assurance service not available: {import_error}")
    st.info("💡 This page requires the QualityAssuranceEngine service to be properly configured.")
    st.stop()

# Initialize service
@st.cache_resource
def get_qa_engine():
    return QualityAssuranceEngine(data_dir="data")

qa_engine = get_qa_engine()

# Sidebar - Settings
with st.sidebar:
    st.markdown("### 📅 Time Period")
    
    time_period = st.selectbox(
        "Select Period",
        ["Today", "Last 7 Days", "Last 30 Days", "Last Quarter"]
    )
    
    st.markdown("---")
    st.markdown("### 🎯 Quality Filters")
    
    score_threshold = st.slider("Quality Score Threshold", 0, 100, 70)
    
    show_passed = st.checkbox("Show Passed", value=True)
    show_failed = st.checkbox("Show Failed", value=True)
    show_warnings = st.checkbox("Show Warnings", value=True)
    
    st.markdown("---")
    st.markdown("### 🔍 Compliance Checks")
    
    check_professionalism = st.checkbox("Professionalism", value=True)
    check_accuracy = st.checkbox("Information Accuracy", value=True)
    check_compliance = st.checkbox("Regulatory Compliance", value=True)
    check_tone = st.checkbox("Appropriate Tone", value=True)
    
    st.markdown("---")
    
    if st.button("🔄 Run QA Check"):
        st.cache_resource.clear()
        st.rerun()

# Get QA data
location_id = "demo_location"
qa_data = qa_engine.get_qa_report(location_id, days=7)

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔍 Conversation Review", "⚠️ Issues", "📋 Reports"])

with tab1:
    st.markdown("### 📊 Quality Assurance Overview")
    
    # Overall quality score
    overall_score = qa_data.get("overall_score", 85)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score_class = "qa-score-excellent" if overall_score >= 80 else \
                     "qa-score-good" if overall_score >= 70 else \
                     "qa-score-warning" if overall_score >= 60 else "qa-score-danger"
        
        st.markdown(f"""
        <div class="{score_class}">
            <h4>Overall Quality</h4>
            <h2 style="margin: 15px 0;">{overall_score}/100</h2>
            <p>Excellent Performance</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Conversations Reviewed", "1,247", "+123")
    
    with col3:
        pass_rate = qa_data.get("pass_rate", 92.5)
        st.metric("Pass Rate", f"{pass_rate}%", "+2.3%")
    
    with col4:
        issues_count = qa_data.get("issues_count", 18)
        st.metric("Active Issues", issues_count, "-5")
    
    st.markdown("---")
    
    # Quality metrics breakdown
    st.markdown("#### 📈 Quality Metrics Breakdown")
    
    metrics = {
        "Professionalism": 92,
        "Response Accuracy": 88,
        "Tone & Empathy": 85,
        "Information Completeness": 87,
        "Compliance": 95,
        "Grammar & Spelling": 94
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig_bar = go.Figure()
        
        colors = ['#28a745' if v >= 90 else '#17a2b8' if v >= 80 else '#ffc107' if v >= 70 else '#dc3545' 
                 for v in metrics.values()]
        
        fig_bar.add_trace(go.Bar(
            x=list(metrics.keys()),
            y=list(metrics.values()),
            marker_color=colors,
            text=list(metrics.values()),
            texttemplate='%{text}',
            textposition='outside'
        ))
        
        fig_bar.update_layout(
            title="Quality Score by Category",
            yaxis_title="Score",
            yaxis_range=[0, 110],
            height=400
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.markdown("#### 🎯 Status Summary")
        
        for metric, score in metrics.items():
            if score >= 90:
                emoji = "🟢"
                status = "Excellent"
            elif score >= 80:
                emoji = "🟡"
                status = "Good"
            elif score >= 70:
                emoji = "🟠"
                status = "Fair"
            else:
                emoji = "🔴"
                status = "Needs Work"
            
            st.markdown(f"{emoji} **{metric}**: {score} ({status})")
    
    st.markdown("---")
    
    # Trend over time
    st.markdown("#### 📈 Quality Score Trend")
    
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    scores = [80 + (i * 0.3) + (5 if i % 7 == 0 else 0) for i in range(30)]
    
    fig_trend = go.Figure()
    
    fig_trend.add_trace(go.Scatter(
        x=dates,
        y=scores,
        mode='lines+markers',
        name='Quality Score',
        line=dict(color='#667eea', width=3),
        marker=dict(size=6),
        fill='tozeroy'
    ))
    
    # Add threshold line
    fig_trend.add_hline(y=score_threshold, line_dash="dash", line_color="red", 
                       annotation_text="Threshold")
    
    fig_trend.update_layout(
        title="30-Day Quality Score Evolution",
        xaxis_title="Date",
        yaxis_title="Quality Score",
        yaxis_range=[0, 100],
        height=400
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)

with tab2:
    st.markdown("### 🔍 Conversation Quality Review")
    
    st.info("💡 Review individual conversations for quality and compliance")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        review_status = st.selectbox("Status", ["All", "Pending Review", "Approved", "Flagged"])
    with col2:
        quality_level = st.selectbox("Quality", ["All", "High", "Medium", "Low"])
    with col3:
        date_filter = st.date_input("Date", datetime.now())
    
    st.markdown("---")
    
    # Sample conversations
    conversations = [
        {
            "id": "conv_12345",
            "contact": "John Doe",
            "date": "2026-01-04 10:30",
            "quality_score": 92,
            "issues": 0,
            "status": "Approved"
        },
        {
            "id": "conv_12346",
            "contact": "Jane Smith",
            "date": "2026-01-04 11:15",
            "quality_score": 88,
            "issues": 0,
            "status": "Approved"
        },
        {
            "id": "conv_12347",
            "contact": "Bob Johnson",
            "date": "2026-01-04 12:00",
            "quality_score": 65,
            "issues": 2,
            "status": "Flagged"
        },
        {
            "id": "conv_12348",
            "contact": "Alice Williams",
            "date": "2026-01-04 13:45",
            "quality_score": 78,
            "issues": 1,
            "status": "Pending Review"
        }
    ]
    
    for conv in conversations:
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{conv['contact']}**")
        with col2:
            st.text(conv['date'])
        with col3:
            score_color = "#28a745" if conv['quality_score'] >= 80 else \
                         "#ffc107" if conv['quality_score'] >= 70 else "#dc3545"
            st.markdown(f"<span style='color: {score_color}; font-weight: bold;'>Score: {conv['quality_score']}</span>", 
                       unsafe_allow_html=True)
        with col4:
            issue_color = "#28a745" if conv['issues'] == 0 else "#dc3545"
            st.markdown(f"<span style='color: {issue_color};'>Issues: {conv['issues']}</span>", 
                       unsafe_allow_html=True)
        with col5:
            if conv['status'] == "Approved":
                st.markdown('<span class="compliance-badge badge-pass">✓ Approved</span>', 
                           unsafe_allow_html=True)
            elif conv['status'] == "Flagged":
                st.markdown('<span class="compliance-badge badge-fail">✗ Flagged</span>', 
                           unsafe_allow_html=True)
            else:
                st.markdown('<span class="compliance-badge badge-warning">⏳ Pending</span>', 
                           unsafe_allow_html=True)
        with col6:
            if st.button("👁️", key=f"view_{conv['id']}"):
                st.session_state.selected_conv = conv['id']
        
        st.markdown("---")
    
    # Conversation detail view
    if hasattr(st.session_state, 'selected_conv'):
        st.markdown("#### 💬 Conversation Detail")
        
        st.markdown("""
        **Conversation ID:** conv_12345  
        **Contact:** John Doe  
        **Date:** 2026-01-04 10:30  
        **Quality Score:** 92/100
        """)
        
        st.markdown("##### 📝 Transcript:")
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; max-height: 300px; overflow-y: auto;">
            <p><strong>Agent:</strong> Hi! Thanks for reaching out. How can I help you today?</p>
            <p><strong>Contact:</strong> I'm looking for a 3-bedroom home in the downtown area.</p>
            <p><strong>Agent:</strong> Great! I'd be happy to help you find the perfect home. What's your budget range?</p>
            <p><strong>Contact:</strong> Around $400,000 to $500,000.</p>
            <p><strong>Agent:</strong> Perfect. I have several properties in that range. When would you like to schedule a viewing?</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("##### ✅ Quality Checks:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success("✓ Professionalism: 95/100")
            st.success("✓ Response Time: Excellent")
        with col2:
            st.success("✓ Information Accuracy: 90/100")
            st.success("✓ Tone: Appropriate")
        with col3:
            st.success("✓ Compliance: Pass")
            st.success("✓ Grammar: Perfect")

with tab3:
    st.markdown("### ⚠️ Quality Issues & Alerts")
    
    # Issue summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Critical Issues", 2, "🔴")
    with col2:
        st.metric("Warnings", 8, "🟡")
    with col3:
        st.metric("Resolved Today", 5, "✅")
    
    st.markdown("---")
    
    # Active issues
    st.markdown("#### 🚨 Active Issues")
    
    issues = [
        {
            "severity": "Critical",
            "type": "Compliance Violation",
            "conversation": "conv_12347",
            "description": "Potentially misleading information provided about property taxes",
            "detected": "2026-01-04 12:00",
            "status": "Under Review"
        },
        {
            "severity": "Critical",
            "type": "Inappropriate Response",
            "conversation": "conv_12351",
            "description": "Response time exceeded 5 minutes without acknowledgment",
            "detected": "2026-01-04 14:30",
            "status": "Pending Action"
        },
        {
            "severity": "Warning",
            "type": "Tone Issue",
            "conversation": "conv_12349",
            "description": "Response may have sounded dismissive to customer concern",
            "detected": "2026-01-04 11:45",
            "status": "Under Review"
        },
        {
            "severity": "Warning",
            "type": "Incomplete Information",
            "conversation": "conv_12350",
            "description": "Failed to provide requested property details",
            "detected": "2026-01-04 13:00",
            "status": "Acknowledged"
        }
    ]
    
    for issue in issues:
        severity_color = "#dc3545" if issue['severity'] == "Critical" else "#ffc107"
        border_style = f"border-left: 5px solid {severity_color};"
        
        st.markdown(f"""
        <div class="issue-card" style="{border_style}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: {severity_color};">{issue['severity']}: {issue['type']}</h4>
                    <p style="margin: 5px 0;"><strong>Conversation:</strong> {issue['conversation']}</p>
                    <p style="margin: 5px 0;">{issue['description']}</p>
                    <p style="margin: 5px 0; font-size: 0.9em; color: gray;">Detected: {issue['detected']}</p>
                </div>
                <div>
                    <p><strong>Status:</strong> {issue['status']}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔍 Review", key=f"review_{issue['conversation']}"):
                st.info(f"Opening {issue['conversation']} for review")
        with col2:
            if st.button("✅ Resolve", key=f"resolve_{issue['conversation']}"):
                st.success(f"Issue resolved for {issue['conversation']}")
        with col3:
            if st.button("⏭️ Escalate", key=f"escalate_{issue['conversation']}"):
                st.warning(f"Issue escalated for {issue['conversation']}")
        
        st.markdown("---")
    
    # Issue trends
    st.markdown("#### 📊 Issue Trends")
    
    issue_types = ["Compliance", "Response Time", "Tone", "Accuracy", "Completeness"]
    issue_counts = [5, 8, 12, 6, 4]
    
    fig_issues = go.Figure(data=[go.Bar(
        x=issue_types,
        y=issue_counts,
        marker_color=['#dc3545', '#ffc107', '#17a2b8', '#ffc107', '#28a745'],
        text=issue_counts,
        textposition='auto'
    )])
    
    fig_issues.update_layout(
        title="Issues by Type (Last 30 Days)",
        xaxis_title="Issue Type",
        yaxis_title="Count",
        height=350
    )
    
    st.plotly_chart(fig_issues, use_container_width=True)

with tab4:
    st.markdown("### 📋 Quality Assurance Reports")
    
    # Report templates
    st.markdown("#### 📄 Available Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="qa-card">
            <h4>📊 Daily QA Summary</h4>
            <p>Overview of daily quality metrics and issues</p>
            <ul>
                <li>Quality score trends</li>
                <li>Issue summary</li>
                <li>Agent performance</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Daily Report"):
            st.success("✅ Daily report generated!")
    
    with col2:
        st.markdown("""
        <div class="qa-card">
            <h4>📅 Weekly Compliance Report</h4>
            <p>Compliance audit and regulatory review</p>
            <ul>
                <li>Compliance violations</li>
                <li>Resolved issues</li>
                <li>Risk assessment</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Compliance Report"):
            st.success("✅ Compliance report generated!")
    
    st.markdown("---")
    
    # Export options
    st.markdown("#### 📥 Export Options")
    
    export_format = st.selectbox("Export Format", ["PDF", "Excel", "CSV", "JSON"])
    include_transcripts = st.checkbox("Include Full Transcripts", value=False)
    include_metadata = st.checkbox("Include Metadata", value=True)
    
    if st.button("📥 Export Report", type="primary"):
        st.success(f"✅ Report exported as {export_format}")
        st.download_button(
            label="📄 Download File",
            data="Report data here",
            file_name=f"qa_report_{datetime.now().strftime('%Y%m%d')}.{export_format.lower()}",
            mime="application/octet-stream"
        )
    
    st.markdown("---")
    
    # Scheduled reports
    st.markdown("#### ⏰ Scheduled Reports")
    
    schedules = [
        {"name": "Daily QA Summary", "frequency": "Daily at 9:00 AM", "recipients": "qa@company.com"},
        {"name": "Weekly Compliance", "frequency": "Monday at 8:00 AM", "recipients": "compliance@company.com"},
        {"name": "Monthly Review", "frequency": "1st of month at 10:00 AM", "recipients": "management@company.com"}
    ]
    
    for schedule in schedules:
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            st.markdown(f"**{schedule['name']}**")
        with col2:
            st.text(schedule['frequency'])
        with col3:
            st.text(schedule['recipients'])
        st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>✅ Quality Assurance | Ensuring excellence in every conversation</p>
    <p>Last QA check: {} | Next scheduled: {}</p>
</div>
""".format(
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
), unsafe_allow_html=True)
