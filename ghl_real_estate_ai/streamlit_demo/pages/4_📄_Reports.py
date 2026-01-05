"""
GHL Real Estate AI - Report Generator
Automated report generation and insights delivery
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from ghl_real_estate_ai.services.report_generator import ReportGenerator
    SERVICE_AVAILABLE = True
except ImportError as e:
    SERVICE_AVAILABLE = False
    import_error = str(e)

# Page config
st.set_page_config(
    page_title="Report Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .report-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 15px 0;
    }
    .report-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        padding: 10px;
        border-bottom: 1px solid #eee;
    }
    .download-section {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📄 Report Generator")
st.markdown("**Automated insights and analytics reporting**")
st.markdown("---")

# Check service availability
if not SERVICE_AVAILABLE:
    st.error(f"⚠️ Report Generator service not available: {import_error}")
    st.info("💡 This page requires the ReportGenerator service to be properly configured.")
    st.stop()

# Initialize service
@st.cache_resource
def get_report_service():
    return ReportGenerator(data_dir="data")

report_gen = get_report_service()

# Sidebar - Report configuration
with st.sidebar:
    st.markdown("### 📋 Report Configuration")
    
    report_type = st.selectbox(
        "Report Type",
        ["Performance Summary", "Lead Analytics", "Revenue Analysis", 
         "Campaign Performance", "Agent Activity", "Custom Report"]
    )
    
    st.markdown("---")
    st.markdown("### 📅 Date Range")
    
    date_preset = st.selectbox(
        "Quick Select",
        ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "Last Quarter", "Custom"]
    )
    
    if date_preset == "Custom":
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        end_date = st.date_input("End Date", datetime.now())
    else:
        end_date = datetime.now()
        if date_preset == "Today":
            start_date = end_date
        elif date_preset == "Yesterday":
            start_date = end_date - timedelta(days=1)
        elif date_preset == "Last 7 Days":
            start_date = end_date - timedelta(days=7)
        elif date_preset == "Last 30 Days":
            start_date = end_date - timedelta(days=30)
        else:  # Last Quarter
            start_date = end_date - timedelta(days=90)
    
    st.markdown("---")
    st.markdown("### 🎨 Report Format")
    
    include_charts = st.checkbox("Include Charts", value=True)
    include_tables = st.checkbox("Include Data Tables", value=True)
    include_insights = st.checkbox("Include AI Insights", value=True)
    
    export_format = st.selectbox("Export Format", ["PDF", "Excel", "HTML", "JSON"])
    
    st.markdown("---")
    
    if st.button("📊 Generate Report", type="primary"):
        st.session_state.generate_report = True

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Quick Reports", "📈 Custom Builder", "📁 Saved Reports", "⏰ Scheduled"])

with tab1:
    st.markdown("### 📊 Quick Report Templates")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="report-card">
            <h4>📊 Daily Performance</h4>
            <p>Today's key metrics and activity summary</p>
            <ul>
                <li>Lead generation stats</li>
                <li>Conversion metrics</li>
                <li>Revenue summary</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Daily Report"):
            with st.spinner("Generating report..."):
                report = report_gen.generate_report("demo_location", "daily_performance")
                st.success("✅ Report generated!")
                st.session_state.current_report = report
    
    with col2:
        st.markdown("""
        <div class="report-card">
            <h4>📅 Weekly Summary</h4>
            <p>7-day performance overview</p>
            <ul>
                <li>Week-over-week trends</li>
                <li>Top performing campaigns</li>
                <li>Lead quality analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Weekly Report"):
            with st.spinner("Generating report..."):
                report = report_gen.generate_report("demo_location", "weekly_summary")
                st.success("✅ Report generated!")
                st.session_state.current_report = report
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("""
        <div class="report-card">
            <h4>📈 Monthly Analysis</h4>
            <p>Comprehensive monthly business review</p>
            <ul>
                <li>Monthly KPIs</li>
                <li>Pipeline analysis</li>
                <li>ROI calculations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Monthly Report"):
            with st.spinner("Generating report..."):
                report = report_gen.generate_report("demo_location", "monthly_analysis")
                st.success("✅ Report generated!")
                st.session_state.current_report = report
    
    with col4:
        st.markdown("""
        <div class="report-card">
            <h4>🎯 Executive Summary</h4>
            <p>High-level insights for leadership</p>
            <ul>
                <li>Strategic metrics</li>
                <li>Goal progress</li>
                <li>Recommendations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Executive Report"):
            with st.spinner("Generating report..."):
                report = report_gen.generate_report("demo_location", "executive_summary")
                st.success("✅ Report generated!")
                st.session_state.current_report = report
    
    # Display current report if available
    if hasattr(st.session_state, 'current_report'):
        st.markdown("---")
        st.markdown("### 📄 Generated Report Preview")
        
        report = st.session_state.current_report
        
        # Report header
        st.markdown(f"""
        <div class="report-header">
            <h2>{report.get('title', 'Performance Report')}</h2>
            <p><strong>Period:</strong> {report.get('period', 'Last 30 Days')}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key metrics
        st.markdown("#### 📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = report.get('metrics', {})
        with col1:
            st.metric("Total Leads", metrics.get('total_leads', 0))
        with col2:
            st.metric("Conversions", metrics.get('conversions', 0))
        with col3:
            st.metric("Revenue", f"${metrics.get('revenue', 0):,.2f}")
        with col4:
            st.metric("Conversion Rate", f"{metrics.get('conversion_rate', 0):.1f}%")
        
        # Charts
        if include_charts:
            st.markdown("#### 📈 Visualizations")
            
            # Trend chart
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            values = [1000 + (i * 50) for i in range(30)]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=values, mode='lines+markers', 
                                    name='Leads', line=dict(color='#667eea', width=2)))
            fig.update_layout(title="Lead Generation Trend", height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Download section
        st.markdown("""
        <div class="download-section">
            <h4>📥 Export Options</h4>
            <p>Download this report in your preferred format</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button("📄 Download PDF", "Report content here", "report.pdf", "application/pdf")
        with col2:
            st.download_button("📊 Download Excel", "Report data here", "report.xlsx", 
                              "application/vnd.ms-excel")
        with col3:
            st.download_button("🌐 Download HTML", "Report HTML here", "report.html", "text/html")

with tab2:
    st.markdown("### 📈 Custom Report Builder")
    
    st.info("💡 Build a custom report by selecting specific metrics and visualizations")
    
    # Report sections
    st.markdown("#### 📋 Select Report Sections")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Metrics**")
        include_lead_metrics = st.checkbox("Lead Metrics", value=True)
        include_revenue_metrics = st.checkbox("Revenue Metrics", value=True)
        include_conversion_metrics = st.checkbox("Conversion Metrics", value=True)
        include_engagement_metrics = st.checkbox("Engagement Metrics")
    
    with col2:
        st.markdown("**📈 Charts**")
        include_trend_chart = st.checkbox("Trend Analysis", value=True)
        include_funnel_chart = st.checkbox("Conversion Funnel", value=True)
        include_distribution_chart = st.checkbox("Lead Distribution")
        include_comparison_chart = st.checkbox("Period Comparison")
    
    with col3:
        st.markdown("**📋 Tables**")
        include_lead_table = st.checkbox("Lead Details", value=True)
        include_campaign_table = st.checkbox("Campaign Performance")
        include_agent_table = st.checkbox("Agent Activity")
        include_source_table = st.checkbox("Lead Sources")
    
    st.markdown("---")
    
    # Filters
    st.markdown("#### 🎯 Apply Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        lead_status_filter = st.multiselect("Lead Status", 
                                           ["New", "Contacted", "Qualified", "Converted"])
    with col2:
        lead_source_filter = st.multiselect("Lead Source", 
                                            ["Website", "Referral", "Social Media", "Advertisement"])
    with col3:
        score_range = st.slider("Lead Score Range", 0, 100, (0, 100))
    
    st.markdown("---")
    
    if st.button("🔨 Build Custom Report", type="primary"):
        with st.spinner("Building your custom report..."):
            custom_config = {
                "metrics": {
                    "leads": include_lead_metrics,
                    "revenue": include_revenue_metrics,
                    "conversion": include_conversion_metrics,
                    "engagement": include_engagement_metrics
                },
                "charts": {
                    "trend": include_trend_chart,
                    "funnel": include_funnel_chart,
                    "distribution": include_distribution_chart,
                    "comparison": include_comparison_chart
                },
                "tables": {
                    "leads": include_lead_table,
                    "campaigns": include_campaign_table,
                    "agents": include_agent_table,
                    "sources": include_source_table
                },
                "filters": {
                    "status": lead_status_filter,
                    "source": lead_source_filter,
                    "score_range": score_range
                }
            }
            
            report = report_gen.generate_custom_report("demo_location", custom_config)
            st.success("✅ Custom report built successfully!")
            st.session_state.current_report = report

with tab3:
    st.markdown("### 📁 Saved Reports")
    
    saved_reports = [
        {"name": "Q1 Performance Review", "date": "2026-01-01", "type": "Quarterly", "size": "2.4 MB"},
        {"name": "December Lead Analysis", "date": "2025-12-31", "type": "Monthly", "size": "1.8 MB"},
        {"name": "Holiday Campaign ROI", "date": "2025-12-25", "type": "Campaign", "size": "945 KB"},
        {"name": "Weekly Summary - Week 52", "date": "2025-12-27", "type": "Weekly", "size": "567 KB"},
    ]
    
    for report in saved_reports:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{report['name']}**")
        with col2:
            st.text(report['date'])
        with col3:
            st.text(report['type'])
        with col4:
            st.text(report['size'])
        with col5:
            if st.button("📥", key=f"download_{report['name']}"):
                st.success(f"Downloading {report['name']}...")
        
        st.markdown("---")

with tab4:
    st.markdown("### ⏰ Scheduled Reports")
    
    st.info("💡 Set up automatic report generation and delivery")
    
    # Existing schedules
    st.markdown("#### 📅 Active Schedules")
    
    schedules = [
        {"name": "Daily Performance", "frequency": "Daily", "time": "08:00 AM", "recipients": "team@company.com"},
        {"name": "Weekly Summary", "frequency": "Weekly", "time": "Monday 09:00 AM", "recipients": "managers@company.com"},
        {"name": "Monthly Review", "frequency": "Monthly", "time": "1st of month, 10:00 AM", "recipients": "executives@company.com"},
    ]
    
    for schedule in schedules:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 1])
        
        with col1:
            st.markdown(f"**{schedule['name']}**")
        with col2:
            st.text(schedule['frequency'])
        with col3:
            st.text(schedule['time'])
        with col4:
            st.text(schedule['recipients'])
        with col5:
            if st.button("✏️", key=f"edit_{schedule['name']}"):
                st.info("Edit functionality")
        
        st.markdown("---")
    
    # Create new schedule
    st.markdown("#### ➕ Create New Schedule")
    
    col1, col2 = st.columns(2)
    
    with col1:
        schedule_name = st.text_input("Schedule Name", "My Report")
        schedule_frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly", "Quarterly"])
        schedule_time = st.time_input("Delivery Time", datetime.now().time())
    
    with col2:
        schedule_recipients = st.text_area("Recipients (one per line)", 
                                          "email1@company.com\nemail2@company.com")
        schedule_format = st.selectbox("Report Format", ["PDF", "Excel", "HTML"])
        schedule_template = st.selectbox("Report Template", 
                                        ["Daily Performance", "Weekly Summary", "Monthly Analysis"])
    
    if st.button("➕ Create Schedule", type="primary"):
        st.success(f"✅ Schedule '{schedule_name}' created successfully!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>📄 Report Generator | Automated insights and analytics delivery</p>
    <p>Last generated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
