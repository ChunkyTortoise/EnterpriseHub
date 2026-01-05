"""
GHL Real Estate AI - Analytics Dashboard
Multi-tenant analytics with conversation metrics, lead scoring, and system health monitoring.
"""
import streamlit as st
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict

# Add project root to sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import campaign analytics
try:
    from ghl_real_estate_ai.services.campaign_analytics import CampaignTracker
    CAMPAIGN_ANALYTICS_AVAILABLE = True
except ImportError:
    CAMPAIGN_ANALYTICS_AVAILABLE = False

# Import lead lifecycle
try:
    from ghl_real_estate_ai.services.lead_lifecycle import LeadLifecycleTracker
    LEAD_LIFECYCLE_AVAILABLE = True
except ImportError:
    LEAD_LIFECYCLE_AVAILABLE = False

# Import bulk operations
try:
    from ghl_real_estate_ai.services.bulk_operations import BulkOperationsManager
    BULK_OPERATIONS_AVAILABLE = True
except ImportError:
    BULK_OPERATIONS_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="GHL AI Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better mobile responsiveness
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    @media (max-width: 768px) {
        .stMetric {
            font-size: 0.9em;
        }
    }
</style>
""", unsafe_allow_html=True)

# Load mock data
@st.cache_data(ttl=60)
def load_mock_data() -> Dict[str, Any]:
    """Load mock analytics data from JSON file."""
    mock_file = project_root / "data" / "mock_analytics.json"
    if mock_file.exists():
        with open(mock_file, "r") as f:
            return json.load(f)
    return {
        "tenants": [],
        "conversations": [],
        "system_health": {}
    }

def filter_conversations_by_date(
    conversations: List[Dict],
    start_date: datetime,
    end_date: datetime
) -> List[Dict]:
    """Filter conversations by date range."""
    from datetime import timezone
    
    # Ensure start_date and end_date are timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    
    filtered = []
    for conv in conversations:
        conv_date = datetime.fromisoformat(conv["start_time"].replace("Z", "+00:00"))
        if start_date <= conv_date <= end_date:
            filtered.append(conv)
    return filtered

def calculate_aggregate_metrics(conversations: List[Dict]) -> Dict[str, Any]:
    """Calculate aggregate metrics from conversations."""
    if not conversations:
        return {
            "total_conversations": 0,
            "total_messages": 0,
            "avg_lead_score": 0,
            "hot_leads": 0,
            "warm_leads": 0,
            "cold_leads": 0,
            "total_contacts": 0,
            "avg_response_time": 0,
            "conversion_rate": 0
        }

    total_messages = sum(c["message_count"] for c in conversations)
    total_score = sum(c["lead_score"] for c in conversations)
    hot_leads = len([c for c in conversations if c["classification"] == "hot"])
    warm_leads = len([c for c in conversations if c["classification"] == "warm"])
    cold_leads = len([c for c in conversations if c["classification"] == "cold"])
    unique_contacts = len(set(c["contact_id"] for c in conversations))
    avg_response_time = sum(c["response_time_avg_seconds"] for c in conversations) / len(conversations)
    avg_conversion = sum(c["conversion_probability"] for c in conversations) / len(conversations)

    return {
        "total_conversations": len(conversations),
        "total_messages": total_messages,
        "avg_lead_score": total_score / len(conversations) if conversations else 0,
        "hot_leads": hot_leads,
        "warm_leads": warm_leads,
        "cold_leads": cold_leads,
        "total_contacts": unique_contacts,
        "avg_response_time": avg_response_time,
        "conversion_rate": avg_conversion
    }

def create_lead_score_distribution_chart(conversations: List[Dict]) -> go.Figure:
    """Create histogram of lead score distribution."""
    scores = [c["lead_score"] for c in conversations]

    fig = go.Figure(data=[go.Histogram(
        x=scores,
        nbinsx=20,
        marker_color='#1f77b4',
        opacity=0.75,
        name='Lead Scores'
    )])

    fig.update_layout(
        title="Lead Score Distribution",
        xaxis_title="Lead Score",
        yaxis_title="Count",
        showlegend=False,
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

def create_classification_pie_chart(conversations: List[Dict]) -> go.Figure:
    """Create pie chart of lead classifications."""
    classifications = [c["classification"] for c in conversations]
    class_counts = {
        "hot": classifications.count("hot"),
        "warm": classifications.count("warm"),
        "cold": classifications.count("cold")
    }

    colors = {'hot': '#ff4b4b', 'warm': '#ffa500', 'cold': '#4b9aff'}

    fig = go.Figure(data=[go.Pie(
        labels=list(class_counts.keys()),
        values=list(class_counts.values()),
        marker_colors=[colors[k] for k in class_counts.keys()],
        hole=0.3
    )])

    fig.update_layout(
        title="Lead Classification Breakdown",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

def create_conversation_timeline(conversations: List[Dict]) -> go.Figure:
    """Create timeline chart of conversations per day."""
    # Group by date
    date_counts = defaultdict(int)
    for conv in conversations:
        conv_date = datetime.fromisoformat(conv["start_time"].replace("Z", "+00:00")).date()
        date_counts[conv_date] += 1

    if not date_counts:
        return go.Figure()

    dates = sorted(date_counts.keys())
    counts = [date_counts[d] for d in dates]

    fig = go.Figure(data=[go.Scatter(
        x=dates,
        y=counts,
        mode='lines+markers',
        marker=dict(size=8, color='#1f77b4'),
        line=dict(width=2, color='#1f77b4'),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.2)'
    )])

    fig.update_layout(
        title="Conversation Volume Over Time",
        xaxis_title="Date",
        yaxis_title="Number of Conversations",
        showlegend=False,
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

def create_response_time_chart(conversations: List[Dict]) -> go.Figure:
    """Create bar chart of average response times by classification."""
    hot_times = [c["response_time_avg_seconds"] for c in conversations if c["classification"] == "hot"]
    warm_times = [c["response_time_avg_seconds"] for c in conversations if c["classification"] == "warm"]
    cold_times = [c["response_time_avg_seconds"] for c in conversations if c["classification"] == "cold"]

    avg_hot = sum(hot_times) / len(hot_times) if hot_times else 0
    avg_warm = sum(warm_times) / len(warm_times) if warm_times else 0
    avg_cold = sum(cold_times) / len(cold_times) if cold_times else 0

    fig = go.Figure(data=[go.Bar(
        x=['Hot Leads', 'Warm Leads', 'Cold Leads'],
        y=[avg_hot, avg_warm, avg_cold],
        marker_color=['#ff4b4b', '#ffa500', '#4b9aff']
    )])

    fig.update_layout(
        title="Avg Response Time by Lead Type (seconds)",
        xaxis_title="Lead Type",
        yaxis_title="Avg Response Time (s)",
        showlegend=False,
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

def create_intent_breakdown(conversations: List[Dict]) -> go.Figure:
    """Create bar chart of intent distribution."""
    intents = [c["intent"] for c in conversations]
    intent_counts = {
        "buyer": intents.count("buyer"),
        "seller": intents.count("seller"),
        "browsing": intents.count("browsing")
    }

    fig = go.Figure(data=[go.Bar(
        x=list(intent_counts.keys()),
        y=list(intent_counts.values()),
        marker_color='#2ecc71'
    )])

    fig.update_layout(
        title="Contact Intent Distribution",
        xaxis_title="Intent Type",
        yaxis_title="Count",
        showlegend=False,
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

# Main App
st.title("📊 GHL Real Estate AI - Analytics Dashboard")
st.markdown("Real-time insights into multi-tenant performance, lead quality, and system health.")

# Load data
data = load_mock_data()
tenants = data.get("tenants", [])
all_conversations = data.get("conversations", [])
system_health = data.get("system_health", {})

# Sidebar - Filters
st.sidebar.header("Filters")

# Tenant selection
tenant_options = ["All Tenants"] + [t["name"] for t in tenants]
selected_tenant = st.sidebar.selectbox("Select Tenant", tenant_options)

# Date range
st.sidebar.subheader("Date Range")
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

date_preset = st.sidebar.selectbox(
    "Quick Select",
    ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"]
)

if date_preset == "Last 7 Days":
    start_date = end_date - timedelta(days=7)
elif date_preset == "Last 30 Days":
    start_date = end_date - timedelta(days=30)
elif date_preset == "Last 90 Days":
    start_date = end_date - timedelta(days=90)
else:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start", start_date)
    with col2:
        end_date = st.date_input("End", end_date)

    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

# Lead type filter
lead_types = st.sidebar.multiselect(
    "Lead Classification",
    ["hot", "warm", "cold"],
    default=["hot", "warm", "cold"]
)

# Filter conversations
filtered_conversations = all_conversations

# Filter by tenant
if selected_tenant != "All Tenants":
    tenant_id = next((t["location_id"] for t in tenants if t["name"] == selected_tenant), None)
    if tenant_id:
        filtered_conversations = [c for c in filtered_conversations if c["location_id"] == tenant_id]

# Filter by date
filtered_conversations = filter_conversations_by_date(filtered_conversations, start_date, end_date)

# Filter by lead type
filtered_conversations = [c for c in filtered_conversations if c["classification"] in lead_types]

# Tabs
tabs_list = ["📈 Overview", "🏢 Tenant Details", "⚙️ System Health"]
tab_index = 3

if CAMPAIGN_ANALYTICS_AVAILABLE:
    tabs_list.append("🎯 Campaign Analytics")
    campaign_tab_idx = tab_index
    tab_index += 1

if LEAD_LIFECYCLE_AVAILABLE:
    tabs_list.append("🔄 Lead Lifecycle")
    lifecycle_tab_idx = tab_index
    tab_index += 1

if BULK_OPERATIONS_AVAILABLE:
    tabs_list.append("⚡ Bulk Operations")
    bulk_tab_idx = tab_index
    tab_index += 1

tabs = st.tabs(tabs_list)
tab1 = tabs[0]
tab2 = tabs[1]
tab3 = tabs[2]

if CAMPAIGN_ANALYTICS_AVAILABLE:
    tab4 = tabs[campaign_tab_idx]
if LEAD_LIFECYCLE_AVAILABLE:
    tab5 = tabs[lifecycle_tab_idx]
if BULK_OPERATIONS_AVAILABLE:
    tab6 = tabs[bulk_tab_idx]

# TAB 1: OVERVIEW
with tab1:
    st.header("Performance Overview")

    # Calculate metrics
    metrics = calculate_aggregate_metrics(filtered_conversations)

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Conversations",
            f"{metrics['total_conversations']:,}",
            delta=f"{metrics['total_contacts']} contacts"
        )

    with col2:
        st.metric(
            "Avg Lead Score",
            f"{metrics['avg_lead_score']:.1f}",
            delta=f"{metrics['hot_leads']} hot leads"
        )

    with col3:
        st.metric(
            "Total Messages",
            f"{metrics['total_messages']:,}",
            delta=f"{metrics['total_messages'] / max(metrics['total_conversations'], 1):.1f} avg/conv"
        )

    with col4:
        st.metric(
            "Conversion Rate",
            f"{metrics['conversion_rate']*100:.1f}%",
            delta=f"{metrics['avg_response_time']:.1f}s response"
        )

    st.divider()

    # Lead breakdown row
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🔥 Hot Leads", metrics['hot_leads'])
    with col2:
        st.metric("🌡️ Warm Leads", metrics['warm_leads'])
    with col3:
        st.metric("❄️ Cold Leads", metrics['cold_leads'])

    st.divider()

    # Charts section
    st.subheader("📊 Visualization Insights")

    if filtered_conversations:
        # Row 1: Timeline + Classification
        col1, col2 = st.columns(2)

        with col1:
            timeline_chart = create_conversation_timeline(filtered_conversations)
            st.plotly_chart(timeline_chart, use_container_width=True)

        with col2:
            pie_chart = create_classification_pie_chart(filtered_conversations)
            st.plotly_chart(pie_chart, use_container_width=True)

        # Row 2: Score Distribution + Response Time
        col1, col2 = st.columns(2)

        with col1:
            score_chart = create_lead_score_distribution_chart(filtered_conversations)
            st.plotly_chart(score_chart, use_container_width=True)

        with col2:
            response_chart = create_response_time_chart(filtered_conversations)
            st.plotly_chart(response_chart, use_container_width=True)

        # Row 3: Intent Breakdown
        intent_chart = create_intent_breakdown(filtered_conversations)
        st.plotly_chart(intent_chart, use_container_width=True)
    else:
        st.info("No conversations found for the selected filters. Try adjusting your date range or tenant selection.")

# TAB 2: TENANT DETAILS
with tab2:
    st.header("Tenant Drill-Down")

    if not tenants:
        st.warning("No tenant data available.")
    else:
        # Tenant summary table
        st.subheader("📋 Tenant Summary")

        tenant_stats = []
        for tenant in tenants:
            tenant_convs = [c for c in all_conversations if c["location_id"] == tenant["location_id"]]
            tenant_convs_filtered = filter_conversations_by_date(tenant_convs, start_date, end_date)
            tenant_metrics = calculate_aggregate_metrics(tenant_convs_filtered)

            tenant_stats.append({
                "Tenant": tenant["name"],
                "Region": tenant["region"],
                "Tier": tenant["tier"].upper(),
                "Conversations": tenant_metrics["total_conversations"],
                "Avg Score": f"{tenant_metrics['avg_lead_score']:.1f}",
                "Hot Leads": tenant_metrics["hot_leads"],
                "Conversion Rate": f"{tenant_metrics['conversion_rate']*100:.1f}%"
            })

        st.table(tenant_stats)

        st.divider()

        # Individual tenant deep dive
        st.subheader("🔍 Individual Tenant Analysis")

        selected_tenant_detail = st.selectbox(
            "Select Tenant for Detailed View",
            [t["name"] for t in tenants]
        )

        tenant_detail = next((t for t in tenants if t["name"] == selected_tenant_detail), None)

        if tenant_detail:
            st.markdown(f"### {tenant_detail['name']}")

            # Tenant info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Location ID:** `{tenant_detail['location_id']}`")
            with col2:
                st.markdown(f"**Region:** {tenant_detail['region']}")
            with col3:
                st.markdown(f"**Tier:** {tenant_detail['tier'].upper()}")

            st.divider()

            # Get tenant conversations
            tenant_convs = [c for c in all_conversations if c["location_id"] == tenant_detail["location_id"]]
            tenant_convs_filtered = filter_conversations_by_date(tenant_convs, start_date, end_date)

            if tenant_convs_filtered:
                # Metrics
                tenant_metrics = calculate_aggregate_metrics(tenant_convs_filtered)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Conversations", tenant_metrics["total_conversations"])
                with col2:
                    st.metric("Avg Score", f"{tenant_metrics['avg_lead_score']:.1f}")
                with col3:
                    st.metric("Hot Leads", tenant_metrics["hot_leads"])
                with col4:
                    st.metric("Messages", tenant_metrics["total_messages"])

                # Charts
                col1, col2 = st.columns(2)
                with col1:
                    score_chart = create_lead_score_distribution_chart(tenant_convs_filtered)
                    st.plotly_chart(score_chart, use_container_width=True)

                with col2:
                    intent_chart = create_intent_breakdown(tenant_convs_filtered)
                    st.plotly_chart(intent_chart, use_container_width=True)

                # Recent conversations table
                st.subheader("Recent Conversations")
                recent_convs = sorted(
                    tenant_convs_filtered,
                    key=lambda x: x["start_time"],
                    reverse=True
                )[:10]

                conv_table = []
                for conv in recent_convs:
                    conv_table.append({
                        "Contact": conv["contact_name"],
                        "Date": datetime.fromisoformat(conv["start_time"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M"),
                        "Messages": conv["message_count"],
                        "Score": conv["lead_score"],
                        "Classification": conv["classification"].upper(),
                        "Intent": conv["intent"].capitalize(),
                        "Budget": conv["budget"]
                    })

                st.table(conv_table)
            else:
                st.info("No conversations found for this tenant in the selected date range.")

# TAB 3: SYSTEM HEALTH
with tab3:
    st.header("System Health & Performance")

    if not system_health:
        st.warning("No system health data available.")
    else:
        # Top-level health metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            uptime = system_health.get("uptime_percentage", 0)
            st.metric(
                "Uptime",
                f"{uptime:.2f}%",
                delta="Excellent" if uptime > 99.5 else "Good"
            )

        with col2:
            error_rate = system_health.get("error_rate_percentage", 0)
            st.metric(
                "Error Rate",
                f"{error_rate:.2f}%",
                delta="Healthy" if error_rate < 1 else "Warning",
                delta_color="inverse"
            )

        with col3:
            api_calls = system_health.get("total_api_calls_24h", 0)
            st.metric(
                "API Calls (24h)",
                f"{api_calls:,}",
                delta=f"{api_calls / 24:.0f}/hour"
            )

        with col4:
            response_time = system_health.get("avg_response_time_ms", 0)
            st.metric(
                "Avg Response Time",
                f"{response_time}ms",
                delta="Fast" if response_time < 500 else "Slow"
            )

        st.divider()

        # Performance metrics
        st.subheader("⚡ Performance Metrics")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**API Performance**")
            st.metric("Anthropic API Latency", f"{system_health.get('anthropic_api_latency_avg_ms', 0)}ms")
            st.metric("Cache Hit Rate", f"{system_health.get('cache_hit_rate', 0)*100:.1f}%")
            st.metric("Active Webhooks", system_health.get("active_webhooks", 0))

        with col2:
            st.markdown("**Infrastructure**")
            st.metric("CPU Usage", f"{system_health.get('cpu_usage_percentage', 0)}%")
            st.metric("Memory Usage", f"{system_health.get('memory_usage_mb', 0)} MB")
            st.metric("Disk Usage", f"{system_health.get('disk_usage_gb', 0):.1f} GB")

        st.divider()

        # Database connections
        st.subheader("🗄️ Database & Resources")

        db_active = system_health.get("database_connections_active", 0)
        db_max = system_health.get("database_connections_max", 50)
        db_usage_pct = (db_active / db_max) * 100 if db_max > 0 else 0

        st.progress(db_usage_pct / 100, text=f"Database Connections: {db_active}/{db_max} ({db_usage_pct:.1f}%)")

        # SMS Compliance
        st.divider()
        st.subheader("📱 SMS & Communication")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("SMS Sent (24h)", f"{system_health.get('sms_sent_24h', 0):,}")
        with col2:
            compliance = system_health.get('sms_compliance_rate', 0)
            st.metric("Compliance Rate", f"{compliance*100:.1f}%", delta="Compliant" if compliance > 0.95 else "Review")
        with col3:
            tokens = system_health.get('anthropic_tokens_used_24h', 0)
            st.metric("AI Tokens (24h)", f"{tokens:,}")

        # Health status indicator
        st.divider()

        overall_health = "HEALTHY"
        if uptime < 99 or error_rate > 2 or response_time > 1000:
            overall_health = "DEGRADED"
        if uptime < 95 or error_rate > 5:
            overall_health = "CRITICAL"

        status_color = {
            "HEALTHY": "🟢",
            "DEGRADED": "🟡",
            "CRITICAL": "🔴"
        }

        st.markdown(f"### Overall System Status: {status_color[overall_health]} **{overall_health}**")

# Campaign Analytics Tab (if available)
if CAMPAIGN_ANALYTICS_AVAILABLE:
    with tab4:
        st.header("📈 Campaign Performance Analytics")
        
        if selected_tenant == "All Tenants":
            st.info("Please select a specific tenant to view campaign analytics.")
        else:
            tracker = CampaignTracker(selected_tenant)
            active_campaigns = tracker.list_active_campaigns()
            
            if not active_campaigns:
                st.warning("No active campaigns found. Create a campaign to start tracking performance.")
                
                with st.expander("➕ Create New Campaign"):
                    with st.form("create_campaign"):
                        camp_name = st.text_input("Campaign Name", placeholder="e.g., Spring SMS Blast")
                        camp_channel = st.selectbox("Channel", ["sms", "email", "social", "paid_ads", "organic"])
                        camp_budget = st.number_input("Budget ($)", min_value=0.0, value=1000.0, step=100.0)
                        camp_start = st.date_input("Start Date", value=datetime.now())
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            target_leads = st.number_input("Target Leads", min_value=0, value=100, step=10)
                        with col2:
                            target_conversions = st.number_input("Target Conversions", min_value=0, value=10, step=1)
                        with col3:
                            target_roi = st.number_input("Target ROI", min_value=0.0, value=2.0, step=0.1)
                        
                        submitted = st.form_submit_button("Create Campaign")
                        if submitted:
                            campaign_id = tracker.create_campaign(
                                name=camp_name,
                                channel=camp_channel,
                                budget=camp_budget,
                                start_date=camp_start.isoformat(),
                                target_metrics={
                                    "target_leads": target_leads,
                                    "target_conversions": target_conversions,
                                    "target_roi": target_roi
                                }
                            )
                            st.success(f"✅ Campaign created: {campaign_id}")
                            st.rerun()
            else:
                # Campaign selector
                campaign_names = {c["name"]: c["id"] for c in active_campaigns}
                selected_campaign_name = st.selectbox(
                    "Select Campaign",
                    options=list(campaign_names.keys())
                )
                selected_campaign_id = campaign_names[selected_campaign_name]
                
                # Get campaign performance
                performance = tracker.get_campaign_performance(selected_campaign_id)
                
                if "error" not in performance:
                    # Key Metrics Row
                    st.subheader("📊 Campaign Overview")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    perf = performance["performance"]
                    roi_data = performance["roi_analysis"]
                    
                    with col1:
                        st.metric("Leads Generated", f"{perf['leads_generated']:,}")
                    with col2:
                        st.metric("Conversions", f"{perf['conversions']:,}")
                    with col3:
                        st.metric("ROI", f"{roi_data['roi_percentage']:.1f}%", 
                                 delta="Profitable" if roi_data['roi_percentage'] > 0 else "Loss")
                    with col4:
                        st.metric("Cost per Lead", f"${perf['cost_per_lead']:.2f}")
                    with col5:
                        st.metric("Conversion Rate", f"{perf['conversion_rate']*100:.1f}%")
                    
                    st.divider()
                    
                    # ROI Analysis
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("💰 ROI Analysis")
                        
                        # ROI breakdown
                        fig_roi = go.Figure()
                        
                        fig_roi.add_trace(go.Bar(
                            name='Spent',
                            x=['Campaign'],
                            y=[roi_data['total_spent']],
                            marker_color='#ff4b4b'
                        ))
                        
                        fig_roi.add_trace(go.Bar(
                            name='Revenue',
                            x=['Campaign'],
                            y=[roi_data['revenue_generated']],
                            marker_color='#2ecc71'
                        ))
                        
                        fig_roi.update_layout(
                            title="Budget vs Revenue",
                            yaxis_title="Amount ($)",
                            barmode='group',
                            height=300,
                            showlegend=True
                        )
                        
                        st.plotly_chart(fig_roi, use_container_width=True)
                        
                        # ROI metrics table
                        st.markdown("**Financial Metrics:**")
                        st.markdown(f"- **Total Spent:** ${roi_data['total_spent']:,.2f}")
                        st.markdown(f"- **Revenue Generated:** ${roi_data['revenue_generated']:,.2f}")
                        st.markdown(f"- **Net Profit:** ${roi_data['net_profit']:,.2f}")
                        st.markdown(f"- **Profit Margin:** {roi_data['profit_margin']:.1f}%")
                    
                    with col2:
                        st.subheader("🔄 Conversion Funnel")
                        
                        funnel = performance["funnel_metrics"]["stages"]
                        
                        # Create funnel chart
                        fig_funnel = go.Figure(go.Funnel(
                            y=['Awareness', 'Interest', 'Consideration', 'Intent', 'Conversion'],
                            x=[
                                funnel['awareness'],
                                funnel['interest'],
                                funnel['consideration'],
                                funnel['intent'],
                                funnel['conversion']
                            ],
                            textinfo="value+percent initial",
                            marker={"color": ["#3498db", "#2ecc71", "#f39c12", "#e74c3c", "#9b59b6"]}
                        ))
                        
                        fig_funnel.update_layout(
                            title=f"Funnel Efficiency: {performance['funnel_metrics']['overall_efficiency']:.1f}%",
                            height=350
                        )
                        
                        st.plotly_chart(fig_funnel, use_container_width=True)
                        
                        # Funnel conversion rates
                        st.markdown("**Stage Conversion Rates:**")
                        rates = performance["funnel_metrics"]["conversion_rates"]
                        for stage, rate in rates.items():
                            st.markdown(f"- **{stage.replace('_', ' ').title()}:** {rate:.1f}%")
                    
                    st.divider()
                    
                    # Target Comparison
                    st.subheader("🎯 Target Performance")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    targets = performance["target_comparison"]
                    
                    with col1:
                        st.markdown("**Leads vs Target**")
                        leads_data = targets["leads_vs_target"]
                        progress = min(leads_data["achievement_rate"], 100)
                        st.progress(progress / 100)
                        st.markdown(f"{leads_data['actual']} / {leads_data['target']} ({leads_data['achievement_rate']:.0f}%)")
                    
                    with col2:
                        st.markdown("**Conversions vs Target**")
                        conv_data = targets["conversions_vs_target"]
                        progress = min(conv_data["achievement_rate"], 100)
                        st.progress(progress / 100)
                        st.markdown(f"{conv_data['actual']} / {conv_data['target']} ({conv_data['achievement_rate']:.0f}%)")
                    
                    with col3:
                        st.markdown("**ROI vs Target**")
                        roi_target = targets["roi_vs_target"]
                        progress = min(roi_target["achievement_rate"], 100)
                        st.progress(progress / 100)
                        st.markdown(f"{roi_target['actual']:.2f}x / {roi_target['target']:.2f}x ({roi_target['achievement_rate']:.0f}%)")
                    
                    st.divider()
                    
                    # Trend Data
                    if performance["trend_data"]:
                        st.subheader("📈 Performance Trends")
                        
                        trend_dates = [t["date"] for t in performance["trend_data"]]
                        trend_leads = [t["cumulative"]["leads_generated"] for t in performance["trend_data"]]
                        trend_conversions = [t["cumulative"]["conversions"] for t in performance["trend_data"]]
                        
                        fig_trend = go.Figure()
                        
                        fig_trend.add_trace(go.Scatter(
                            x=trend_dates,
                            y=trend_leads,
                            mode='lines+markers',
                            name='Leads',
                            line=dict(color='#3498db', width=2)
                        ))
                        
                        fig_trend.add_trace(go.Scatter(
                            x=trend_dates,
                            y=trend_conversions,
                            mode='lines+markers',
                            name='Conversions',
                            line=dict(color='#2ecc71', width=2)
                        ))
                        
                        fig_trend.update_layout(
                            title="Campaign Performance Over Time",
                            xaxis_title="Date",
                            yaxis_title="Count",
                            height=300,
                            showlegend=True
                        )
                        
                        st.plotly_chart(fig_trend, use_container_width=True)
                    
                    # Campaign Actions
                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📝 Update Metrics"):
                            st.info("Use the API or admin panel to update campaign metrics in real-time.")
                    
                    with col2:
                        if st.button("📊 Generate Report"):
                            st.success("Report generation coming soon!")
                    
                    with col3:
                        if st.button("✅ Complete Campaign"):
                            tracker.complete_campaign(selected_campaign_id)
                            st.success("Campaign marked as completed!")
                            st.rerun()
                
                # Channel Analytics
                st.divider()
                st.subheader("📡 Channel Performance")
                
                channel_data = tracker.get_channel_analytics()
                
                if channel_data:
                    # Create channel comparison chart
                    channels = list(channel_data.keys())
                    channel_leads = [channel_data[ch]["total_leads"] for ch in channels]
                    channel_roi = [channel_data[ch]["avg_roi"] * 100 for ch in channels]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_channel_leads = go.Figure(data=[go.Bar(
                            x=channels,
                            y=channel_leads,
                            marker_color='#3498db'
                        )])
                        
                        fig_channel_leads.update_layout(
                            title="Leads by Channel",
                            xaxis_title="Channel",
                            yaxis_title="Total Leads",
                            height=300
                        )
                        
                        st.plotly_chart(fig_channel_leads, use_container_width=True)
                    
                    with col2:
                        fig_channel_roi = go.Figure(data=[go.Bar(
                            x=channels,
                            y=channel_roi,
                            marker_color='#2ecc71'
                        )])
                        
                        fig_channel_roi.update_layout(
                            title="ROI by Channel (%)",
                            xaxis_title="Channel",
                            yaxis_title="ROI (%)",
                            height=300
                        )
                        
                        st.plotly_chart(fig_channel_roi, use_container_width=True)

# Lead Lifecycle Tab (if available)
if LEAD_LIFECYCLE_AVAILABLE:
    with tab5:
        st.header("🔄 Lead Lifecycle Visualization")
        
        if selected_tenant == "All Tenants":
            st.info("Please select a specific tenant to view lead lifecycle data.")
        else:
            tracker = LeadLifecycleTracker(selected_tenant)
            
            if not tracker.journeys:
                st.warning("No lead journeys found. Start tracking leads to visualize their lifecycle.")
                
                with st.expander("ℹ️ About Lead Lifecycle Tracking"):
                    st.markdown("""
                    **Lead Lifecycle Visualization** helps you understand:
                    - How leads progress through your sales funnel
                    - Where leads get stuck (bottlenecks)
                    - Time spent in each stage
                    - Conversion patterns and trends
                    
                    **Stages Tracked:**
                    1. 🆕 New - Initial contact
                    2. 📞 Contacted - First response sent
                    3. ✅ Qualified - Basic info gathered
                    4. 💬 Engaged - Active conversation
                    5. 🔥 Hot - High intent, ready to act
                    6. 📅 Appointment - Scheduled meeting
                    7. 🎉 Converted - Deal closed
                    8. ❌ Lost - Chose competitor
                    9. 😴 Dormant - No activity
                    """)
            else:
                # Conversion Funnel Overview
                st.subheader("📊 Conversion Funnel Overview")
                
                funnel_data = tracker.get_conversion_funnel()
                funnel_counts = funnel_data["funnel"]
                
                # Create funnel visualization
                stages_display = []
                counts_display = []
                for stage in ["new", "contacted", "qualified", "engaged", "hot", "appointment", "converted"]:
                    if funnel_counts[stage] > 0:
                        stages_display.append(stage.title())
                        counts_display.append(funnel_counts[stage])
                
                if stages_display:
                    fig_funnel = go.Figure(go.Funnel(
                        y=stages_display,
                        x=counts_display,
                        textinfo="value+percent initial",
                        marker={"color": ["#3498db", "#2ecc71", "#f39c12", "#e74c3c", "#9b59b6", "#1abc9c", "#2ecc71"]}
                    ))
                    
                    fig_funnel.update_layout(
                        title="Lead Progression Funnel",
                        height=400
                    )
                    
                    st.plotly_chart(fig_funnel, use_container_width=True)
                
                # Funnel Metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Journeys", funnel_data["total_journeys"])
                with col2:
                    st.metric("Currently Active", funnel_counts.get("engaged", 0) + funnel_counts.get("hot", 0))
                with col3:
                    conversion_rate = (funnel_counts.get("converted", 0) / funnel_data["total_journeys"] * 100) if funnel_data["total_journeys"] > 0 else 0
                    st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
                with col4:
                    lost_rate = (funnel_counts.get("lost", 0) / funnel_data["total_journeys"] * 100) if funnel_data["total_journeys"] > 0 else 0
                    st.metric("Lost Rate", f"{lost_rate:.1f}%")
                
                st.divider()
                
                # Stage Analytics
                st.subheader("📈 Stage Performance Analytics")
                
                stage_analytics = tracker.get_stage_analytics()
                
                # Create stage performance table
                stage_data = []
                for stage in ["new", "contacted", "qualified", "engaged", "hot", "appointment", "converted"]:
                    if stage in stage_analytics and stage_analytics[stage]["total_entries"] > 0:
                        stats = stage_analytics[stage]
                        stage_data.append({
                            "Stage": stage.title(),
                            "Entries": stats["total_entries"],
                            "Currently In": stats["currently_in_stage"],
                            "Avg Duration (min)": f"{stats['avg_duration_minutes']:.1f}",
                            "Avg Lead Score": f"{stats['avg_lead_score']:.0f}",
                            "Progression %": f"{stats['progression_rate']:.0f}%",
                            "Regression %": f"{stats['regression_rate']:.0f}%"
                        })
                
                if stage_data:
                    import pandas as pd
                    df_stages = pd.DataFrame(stage_data)
                    st.dataframe(df_stages, use_container_width=True, hide_index=True)
                
                st.divider()
                
                # Bottleneck Analysis
                st.subheader("🚧 Bottleneck Analysis")
                
                bottleneck_analysis = tracker.analyze_bottlenecks()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Slowest Stages**")
                    
                    if bottleneck_analysis["slowest_stages"]:
                        for i, (stage, metrics) in enumerate(bottleneck_analysis["slowest_stages"], 1):
                            st.markdown(f"""
                            **{i}. {stage.title()}**
                            - Average: {metrics['avg_minutes']:.1f} minutes
                            - Median: {metrics['median_minutes']:.1f} minutes
                            - Range: {metrics['min_minutes']:.1f} - {metrics['max_minutes']:.1f} min
                            """)
                    else:
                        st.info("Insufficient data for bottleneck analysis")
                
                with col2:
                    st.markdown("**Drop-off Points**")
                    
                    if bottleneck_analysis["common_drop_off_points"]:
                        for drop in bottleneck_analysis["common_drop_off_points"][:3]:
                            st.markdown(f"""
                            **{drop['stage'].title()}**
                            - Regression Rate: {drop['regression_rate']:.0f}%
                            - Total Exits: {drop['total_exits']}
                            """)
                    else:
                        st.success("No significant drop-off points detected")
                
                # Recommendations
                if bottleneck_analysis["recommendations"]:
                    st.divider()
                    st.subheader("💡 Optimization Recommendations")
                    
                    for rec in bottleneck_analysis["recommendations"][:3]:
                        priority_color = {
                            "critical": "🔴",
                            "high": "🟠",
                            "medium": "🟡",
                            "low": "🟢"
                        }.get(rec["priority"], "⚪")
                        
                        with st.expander(f"{priority_color} {rec['stage'].title()} - {rec['type'].title()}"):
                            st.markdown(f"**Issue:** {rec['issue']}")
                            st.markdown(f"**Suggestion:** {rec['suggestion']}")
                            st.markdown(f"**Expected Impact:** {rec['expected_impact']}")
                
                st.divider()
                
                # Individual Journey Viewer
                st.subheader("🔍 Individual Journey Viewer")
                
                # Get list of journeys
                journey_list = []
                for journey_id, journey in tracker.journeys.items():
                    journey_list.append({
                        "id": journey_id,
                        "name": journey["contact_name"],
                        "stage": journey["current_stage"],
                        "status": journey["status"]
                    })
                
                if journey_list:
                    # Create selector
                    journey_names = {f"{j['name']} ({j['stage']})": j['id'] for j in journey_list}
                    selected_journey_name = st.selectbox(
                        "Select a lead to view their journey:",
                        options=list(journey_names.keys())
                    )
                    
                    if selected_journey_name:
                        selected_journey_id = journey_names[selected_journey_name]
                        summary = tracker.get_journey_summary(selected_journey_id)
                        
                        if "error" not in summary:
                            # Journey Info Cards
                            col1, col2, col3, col4 = st.columns(4)
                            
                            info = summary["journey_info"]
                            metrics = summary["conversion_metrics"]
                            
                            with col1:
                                st.metric("Current Stage", info["current_stage"].title())
                            with col2:
                                st.metric("Status", info["status"].title())
                            with col3:
                                st.metric("Duration", f"{info['duration_hours']:.1f}h")
                            with col4:
                                st.metric("Touchpoints", metrics["total_touchpoints"])
                            
                            st.divider()
                            
                            # Timeline Visualization
                            st.markdown("**📅 Journey Timeline**")
                            
                            timeline = summary["timeline"]
                            
                            for i, stage_entry in enumerate(timeline):
                                stage_name = stage_entry["stage"].title()
                                entered_time = datetime.fromisoformat(stage_entry["entered_at"]).strftime("%b %d, %I:%M %p")
                                duration = stage_entry.get("duration_minutes")
                                lead_score = stage_entry.get("lead_score", 0)
                                
                                # Stage icon
                                stage_icons = {
                                    "new": "🆕",
                                    "contacted": "📞",
                                    "qualified": "✅",
                                    "engaged": "💬",
                                    "hot": "🔥",
                                    "appointment": "📅",
                                    "converted": "🎉",
                                    "lost": "❌",
                                    "dormant": "😴"
                                }
                                icon = stage_icons.get(stage_entry["stage"], "📍")
                                
                                # Display stage
                                if duration:
                                    st.markdown(f"""
                                    {icon} **{stage_name}**  
                                    *Entered:* {entered_time} | *Duration:* {duration:.1f} min | *Score:* {lead_score}
                                    """)
                                else:
                                    st.markdown(f"""
                                    {icon} **{stage_name}** (Current)  
                                    *Entered:* {entered_time} | *Score:* {lead_score}
                                    """)
                                
                                # Show events in this stage
                                if stage_entry["events"]:
                                    with st.expander(f"View {len(stage_entry['events'])} events"):
                                        for event in stage_entry["events"]:
                                            event_time = datetime.fromisoformat(event["timestamp"]).strftime("%I:%M %p")
                                            st.markdown(f"- {event_time}: {event['description']}")
                            
                            st.divider()
                            
                            # Key Moments
                            st.markdown("**⭐ Key Moments**")
                            
                            key_moments = summary["key_moments"]
                            
                            for moment in key_moments:
                                moment_time = datetime.fromisoformat(moment["timestamp"]).strftime("%b %d, %I:%M %p")
                                moment_type_icons = {
                                    "first_contact": "👋",
                                    "progression": "📈",
                                    "conversion": "🎉",
                                    "lost": "❌"
                                }
                                moment_icon = moment_type_icons.get(moment["type"], "📍")
                                
                                st.markdown(f"{moment_icon} **{moment_time}** - {moment['description']}")
                            
                            st.divider()
                            
                            # Conversion Metrics Summary
                            st.markdown("**📊 Journey Metrics**")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Messages Exchanged", metrics["messages_exchanged"])
                            with col2:
                                st.metric("Progression Rate", f"{metrics['progression_rate']:.0f}%")
                            with col3:
                                st.metric("Stage Efficiency", f"{len(metrics['stage_efficiency'])} stages")

# Bulk Operations Tab (if available)
if BULK_OPERATIONS_AVAILABLE:
    with tab6:
        st.header("⚡ Bulk Operations Dashboard")
        
        if selected_tenant == "All Tenants":
            st.info("Please select a specific tenant to perform bulk operations.")
        else:
            manager = BulkOperationsManager(selected_tenant)
            
            # Operation Type Selector
            st.subheader("📋 Create New Bulk Operation")
            
            operation_type = st.selectbox(
                "Operation Type",
                ["Batch Scoring", "Bulk Messaging", "Tag Management", "Lead Assignment", "Stage Transition", "Data Export"]
            )
            
            # Map display names to operation types
            operation_map = {
                "Batch Scoring": "score",
                "Bulk Messaging": "message",
                "Tag Management": "tag",
                "Lead Assignment": "assign",
                "Stage Transition": "stage",
                "Data Export": "export"
            }
            
            selected_op_type = operation_map[operation_type]
            
            # Lead Selection
            st.markdown("**Select Target Leads:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                selection_method = st.radio(
                    "Selection Method",
                    ["Manual Entry", "Filter Criteria", "Upload CSV"]
                )
            
            with col2:
                if selection_method == "Manual Entry":
                    contact_ids_input = st.text_area(
                        "Enter Contact IDs (one per line)",
                        placeholder="contact_123\ncontact_456\ncontact_789"
                    )
                    target_leads = [cid.strip() for cid in contact_ids_input.split('\n') if cid.strip()]
                elif selection_method == "Filter Criteria":
                    st.markdown("Filter leads by:")
                    filter_stage = st.multiselect("Stage", ["new", "contacted", "qualified", "engaged", "hot"])
                    filter_score = st.slider("Minimum Lead Score", 0, 100, 50)
                    # In production, query leads based on filters
                    target_leads = []  # Placeholder
                    st.info(f"Would select leads with stage in {filter_stage} and score >= {filter_score}")
                else:
                    uploaded_file = st.file_uploader("Upload CSV with contact IDs", type="csv")
                    target_leads = []
                    if uploaded_file:
                        import csv
                        import io
                        content = uploaded_file.read().decode('utf-8')
                        reader = csv.reader(io.StringIO(content))
                        target_leads = [row[0] for row in reader if row]
            
            st.metric("Leads Selected", len(target_leads))
            
            st.divider()
            
            # Operation-Specific Parameters
            st.markdown("**Operation Parameters:**")
            
            parameters = {}
            
            if selected_op_type == "score":
                st.markdown("Batch scoring will calculate lead scores for all selected contacts.")
                col1, col2 = st.columns(2)
                with col1:
                    default_budget = st.number_input("Default Budget (if missing)", value=0, step=10000)
                with col2:
                    default_timeline = st.selectbox("Default Timeline", ["", "urgent", "flexible", "long-term"])
                
                parameters = {
                    "context": {
                        "budget": default_budget,
                        "timeline": default_timeline
                    }
                }
            
            elif selected_op_type == "message":
                st.markdown("Send personalized messages to selected leads.")
                
                # Template selection or custom
                use_template = st.checkbox("Use Template")
                
                if use_template:
                    templates = manager.list_templates()
                    if templates:
                        template_names = {t["name"]: t["template_id"] for t in templates}
                        selected_template = st.selectbox("Select Template", list(template_names.keys()))
                        template_id = template_names[selected_template]
                        template = manager.get_template(template_id)
                        message_text = st.text_area("Message Preview", value=template["text"], height=150)
                    else:
                        st.info("No templates available. Create one below or write a custom message.")
                        message_text = st.text_area("Message Text", height=150)
                else:
                    message_text = st.text_area(
                        "Message Text",
                        placeholder="Hi {first_name}, we have properties in {location} that match your criteria!",
                        height=150
                    )
                
                message_type = st.radio("Message Type", ["sms", "email"], horizontal=True)
                
                parameters = {
                    "template": message_text,
                    "message_type": message_type,
                    "contact_data": {}  # In production, fetch from database
                }
                
                st.markdown("**Available Placeholders:** {first_name}, {last_name}, {email}, {phone}, {budget}, {location}")
            
            elif selected_op_type == "tag":
                action = st.radio("Action", ["Add Tags", "Remove Tags"], horizontal=True)
                tags_input = st.text_input("Tags (comma-separated)", placeholder="hot-lead, follow-up-needed, austin")
                tags = [t.strip() for t in tags_input.split(',') if t.strip()]
                
                parameters = {
                    "action": "add" if action == "Add Tags" else "remove",
                    "tags": tags
                }
                
                st.info(f"Will {action.lower()} these tags: {', '.join(tags)}")
            
            elif selected_op_type == "assign":
                assigned_to = st.text_input("Assign To (User ID or Name)", placeholder="agent_john_doe")
                
                parameters = {
                    "assigned_to": assigned_to
                }
            
            elif selected_op_type == "stage":
                new_stage = st.selectbox(
                    "New Stage",
                    ["new", "contacted", "qualified", "engaged", "hot", "appointment", "converted", "lost", "dormant"]
                )
                reason = st.text_input("Reason for Transition", placeholder="Bulk stage update")
                
                parameters = {
                    "stage": new_stage,
                    "reason": reason
                }
            
            elif selected_op_type == "export":
                export_format = st.radio("Export Format", ["csv", "json"], horizontal=True)
                fields = st.multiselect(
                    "Fields to Export",
                    ["contact_id", "name", "email", "phone", "lead_score", "stage", "tags", "created_at"]
                )
                
                parameters = {
                    "format": export_format,
                    "fields": fields
                }
            
            # Execute Button
            st.divider()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🚀 Execute Operation", type="primary", disabled=len(target_leads) == 0):
                    if target_leads:
                        # Create operation
                        operation_id = manager.create_operation(
                            operation_type=selected_op_type,
                            target_leads=target_leads,
                            parameters=parameters,
                            created_by="user"
                        )
                        
                        # Execute immediately
                        with st.spinner(f"Executing {operation_type}..."):
                            results = manager.execute_operation(operation_id)
                        
                        # Show results
                        st.success(f"✅ Operation completed!")
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Processed", results.get("processed", 0))
                        with col_b:
                            st.metric("Successful", results.get("successful", 0), delta="Success")
                        with col_c:
                            st.metric("Failed", results.get("failed", 0), delta="Errors" if results.get("failed", 0) > 0 else None)
                        
                        if results.get("errors"):
                            with st.expander("View Errors"):
                                for error in results["errors"][:10]:
                                    st.error(f"Contact: {error.get('contact_id', 'N/A')} - {error.get('error', 'Unknown error')}")
            
            with col2:
                if st.button("💾 Save as Draft"):
                    st.info("Draft functionality coming soon!")
            
            with col3:
                if st.button("📅 Schedule for Later"):
                    st.info("Scheduling functionality coming soon!")
            
            # Recent Operations
            st.divider()
            st.subheader("📊 Recent Operations")
            
            recent_ops = manager.list_operations(limit=10)
            
            if recent_ops:
                import pandas as pd
                
                df_ops = pd.DataFrame(recent_ops)
                df_ops["created_at"] = pd.to_datetime(df_ops["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
                
                # Rename columns for display
                df_ops = df_ops.rename(columns={
                    "operation_id": "Operation ID",
                    "operation_type": "Type",
                    "status": "Status",
                    "target_count": "Targets",
                    "successful": "Success",
                    "failed": "Failed",
                    "created_at": "Created"
                })
                
                st.dataframe(df_ops, use_container_width=True, hide_index=True)
            else:
                st.info("No operations yet. Create your first bulk operation above!")
            
            # Analytics
            st.divider()
            st.subheader("📈 Bulk Operations Analytics")
            
            analytics = manager.get_analytics()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Operations", analytics["total_operations"])
            with col2:
                st.metric("Success Rate", f"{analytics['success_rate']:.1f}%")
            with col3:
                st.metric("Leads Processed", analytics["total_leads_processed"])
            with col4:
                st.metric("Avg Duration", f"{analytics['avg_duration_seconds']:.1f}s")
            
            if analytics["by_type"]:
                st.markdown("**Operations by Type:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Bar chart of operations by type
                    fig_types = go.Figure(data=[go.Bar(
                        x=list(analytics["by_type"].keys()),
                        y=list(analytics["by_type"].values()),
                        marker_color='#3498db'
                    )])
                    
                    fig_types.update_layout(
                        title="Operations by Type",
                        xaxis_title="Operation Type",
                        yaxis_title="Count",
                        height=300
                    )
                    
                    st.plotly_chart(fig_types, use_container_width=True)
                
                with col2:
                    # Pie chart of operations by status
                    if analytics["by_status"]:
                        fig_status = go.Figure(data=[go.Pie(
                            labels=list(analytics["by_status"].keys()),
                            values=list(analytics["by_status"].values()),
                            marker_colors=['#2ecc71', '#3498db', '#e74c3c', '#f39c12']
                        )])
                        
                        fig_status.update_layout(
                            title="Operations by Status",
                            height=300
                        )
                        
                        st.plotly_chart(fig_status, use_container_width=True)
            
            # Message Templates Management
            st.divider()
            st.subheader("📝 Message Templates")
            
            with st.expander("➕ Create New Template"):
                with st.form("create_template"):
                    tmpl_name = st.text_input("Template Name", placeholder="Follow-up Message")
                    tmpl_category = st.selectbox("Category", ["general", "welcome", "followup", "reengagement", "appointment"])
                    tmpl_text = st.text_area(
                        "Template Text",
                        placeholder="Hi {first_name}, just following up on our conversation about properties in {location}...",
                        height=100
                    )
                    tmpl_desc = st.text_input("Description", placeholder="Follow-up message for warm leads")
                    
                    if st.form_submit_button("Create Template"):
                        if tmpl_name and tmpl_text:
                            template_id = manager.create_message_template(
                                template_name=tmpl_name,
                                template_text=tmpl_text,
                                description=tmpl_desc,
                                category=tmpl_category
                            )
                            st.success(f"✅ Template created: {template_id}")
                            st.rerun()
            
            templates = manager.list_templates()
            if templates:
                st.markdown(f"**Available Templates:** {len(templates)}")
                
                for tmpl in templates[:5]:
                    with st.expander(f"{tmpl['name']} ({tmpl['category']})"):
                        st.markdown(f"**Text:** {tmpl['text']}")
                        if tmpl['description']:
                            st.markdown(f"**Description:** {tmpl['description']}")
                        st.markdown(f"**Created:** {tmpl['created_at']}")
            else:
                st.info("No templates yet. Create your first template above!")

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 0.9em;'>
        GHL Real Estate AI Analytics Dashboard v2.2 with Campaign, Lifecycle & Bulk Operations | Last updated: {now}
    </div>
    """.format(now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)
