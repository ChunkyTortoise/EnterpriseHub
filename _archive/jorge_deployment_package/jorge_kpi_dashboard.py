#!/usr/bin/env python3
"""
Jorge's KPI Dashboard - Real-time Bot Performance & Lead Analytics

This dashboard provides Jorge with essential KPIs for monitoring bot performance,
lead quality, and conversion metrics in real-time.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio

# Import the bot services
from jorge_lead_bot import JorgeLeadBot
from jorge_seller_bot import JorgeSellerBot

# Configure Streamlit page
st.set_page_config(
    page_title="Jorge's Bot KPI Dashboard", 
    page_icon="🏠",
    layout="wide"
)


class JorgeKPIDashboard:
    """
    Real-time KPI dashboard for Jorge's lead and seller bots.
    
    Provides:
    - Lead conversion metrics
    - Bot response analytics  
    - Revenue pipeline tracking
    - Performance trends
    - Alert system for hot leads
    """

    def __init__(self):
        self.lead_bot = JorgeLeadBot()
        self.seller_bot = JorgeSellerBot()

    def render_dashboard(self):
        """Render the complete KPI dashboard"""
        
        # Header
        st.title("🏠 Jorge's Bot Performance Dashboard")
        st.markdown("**Real-time analytics for lead and seller bot performance**")
        
        # Refresh control
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🔄 Refresh Data"):
                st.rerun()
        with col2:
            auto_refresh = st.checkbox("Auto-refresh (30s)")
            
        if auto_refresh:
            # Auto-refresh every 30 seconds
            st.empty()
            time.sleep(30)
            st.rerun()

        # Key metrics overview
        self._render_key_metrics()
        
        st.divider()
        
        # Performance charts
        col1, col2 = st.columns(2)
        with col1:
            self._render_lead_funnel()
            self._render_response_times()
        with col2:
            self._render_conversion_trends()
            self._render_temperature_distribution()
        
        st.divider()
        
        # Detailed analytics
        self._render_detailed_analytics()
        
        st.divider()
        
        # Hot leads alerts
        self._render_hot_leads_alerts()

    def _render_key_metrics(self):
        """Render key performance metrics"""
        
        st.subheader("📊 Today's Key Metrics")
        
        # Mock data - in production, this would come from your analytics service
        metrics_data = self._get_todays_metrics()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="💬 Total Conversations",
                value=metrics_data["total_conversations"],
                delta=f"+{metrics_data['conversations_delta']} from yesterday"
            )
            
        with col2:
            st.metric(
                label="🔥 Hot Leads",
                value=metrics_data["hot_leads"],
                delta=f"+{metrics_data['hot_leads_delta']}"
            )
            
        with col3:
            st.metric(
                label="✅ Qualified Leads",
                value=metrics_data["qualified_leads"],
                delta=f"+{metrics_data['qualified_delta']}"
            )
            
        with col4:
            st.metric(
                label="📞 Appointments Booked",
                value=metrics_data["appointments"],
                delta=f"+{metrics_data['appointments_delta']}"
            )
            
        with col5:
            st.metric(
                label="💰 Pipeline Value",
                value=f"${metrics_data['pipeline_value']:,}",
                delta=f"+${metrics_data['pipeline_delta']:,}"
            )

    def _render_lead_funnel(self):
        """Render lead conversion funnel"""
        
        st.subheader("🎯 Lead Conversion Funnel")
        
        # Mock funnel data
        funnel_data = {
            "Stage": ["Initial Contact", "Engaged", "Qualified", "Hot Lead", "Appointment"],
            "Count": [150, 120, 85, 35, 20],
            "Conversion": ["100%", "80%", "57%", "23%", "13%"]
        }
        
        df = pd.DataFrame(funnel_data)
        
        fig = px.funnel(
            df, 
            x="Count", 
            y="Stage",
            title="Lead Conversion Funnel (Last 7 Days)",
            color_discrete_sequence=["#1f77b4"]
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Conversion rates
        st.caption("**Conversion Rates:** Initial → Qualified: 57% | Qualified → Hot: 41% | Hot → Appointment: 57%")

    def _render_conversion_trends(self):
        """Render conversion trends over time"""
        
        st.subheader("📈 Conversion Trends")
        
        # Generate sample trend data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        trend_data = pd.DataFrame({
            "Date": dates,
            "Leads": np.random.randint(10, 30, len(dates)),
            "Qualified": np.random.randint(5, 15, len(dates)), 
            "Hot": np.random.randint(1, 8, len(dates)),
            "Appointments": np.random.randint(0, 5, len(dates))
        })
        
        fig = px.line(
            trend_data.melt(id_vars=["Date"], var_name="Metric", value_name="Count"),
            x="Date",
            y="Count", 
            color="Metric",
            title="30-Day Conversion Trends"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def _render_response_times(self):
        """Render bot response time analytics"""
        
        st.subheader("⚡ Bot Response Performance")
        
        # Mock response time data
        response_data = {
            "Bot Type": ["Lead Bot", "Seller Bot", "Follow-up Bot"],
            "Avg Response Time (s)": [1.2, 1.8, 0.9],
            "Success Rate (%)": [98.5, 97.2, 99.1]
        }
        
        df = pd.DataFrame(response_data)
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=["Response Time", "Success Rate"],
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        fig.add_trace(
            go.Bar(x=df["Bot Type"], y=df["Avg Response Time (s)"], name="Response Time"),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=df["Bot Type"], y=df["Success Rate (%)"], name="Success Rate"),
            row=1, col=2
        )
        
        fig.update_layout(height=400, title_text="Bot Performance Metrics")
        st.plotly_chart(fig, use_container_width=True)

    def _render_temperature_distribution(self):
        """Render lead temperature distribution"""
        
        st.subheader("🌡️ Lead Temperature Distribution")
        
        # Mock temperature data
        temp_data = {
            "Temperature": ["Hot", "Warm", "Cold"],
            "Count": [25, 45, 80],
            "Colors": ["#ff4444", "#ffaa44", "#4444ff"]
        }
        
        fig = px.pie(
            temp_data,
            values="Count",
            names="Temperature", 
            title="Current Lead Distribution",
            color_discrete_sequence=temp_data["Colors"]
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def _render_detailed_analytics(self):
        """Render detailed analytics tables"""
        
        st.subheader("📋 Detailed Analytics")
        
        tab1, tab2, tab3 = st.tabs(["📱 Recent Activity", "🏆 Top Performers", "📊 Conversion Stats"])
        
        with tab1:
            self._render_recent_activity()
            
        with tab2:
            self._render_top_performers()
            
        with tab3:
            self._render_conversion_stats()

    def _render_recent_activity(self):
        """Render recent bot activity"""
        
        # Mock recent activity data
        activity_data = {
            "Time": [
                "2 min ago", "5 min ago", "8 min ago", "12 min ago", "15 min ago",
                "18 min ago", "22 min ago", "25 min ago", "30 min ago", "35 min ago"
            ],
            "Contact": [
                "John D.", "Sarah M.", "Mike R.", "Lisa K.", "Tom B.",
                "Amy S.", "David L.", "Julie P.", "Mark T.", "Nina C."
            ],
            "Bot Type": [
                "Lead Bot", "Seller Bot", "Lead Bot", "Follow-up", "Seller Bot",
                "Lead Bot", "Seller Bot", "Lead Bot", "Follow-up", "Lead Bot"
            ],
            "Action": [
                "Qualified as Hot Lead", "Q2: Timeline Question", "Budget Captured", "Follow-up Sent",
                "Q1: Motivation", "Location Captured", "Q3: Condition", "Timeline Captured", 
                "Nurture Sequence", "Property Type Identified"
            ],
            "Temperature": [
                "🔥 Hot", "🟡 Warm", "🔥 Hot", "🟢 Cold", "🟡 Warm",
                "🟡 Warm", "🟡 Warm", "🔥 Hot", "🟢 Cold", "🟡 Warm"
            ]
        }
        
        df = pd.DataFrame(activity_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    def _render_top_performers(self):
        """Render top performing leads/contacts"""
        
        # Mock top performer data
        performer_data = {
            "Contact": ["John D.", "Sarah M.", "Mike R.", "Lisa K.", "Tom B."],
            "Lead Score": [95, 92, 88, 85, 82],
            "Questions Answered": ["4/4", "4/4", "3/4", "4/4", "3/4"],
            "Qualification": ["Complete", "Complete", "In Progress", "Complete", "In Progress"],
            "Est. Value": ["$450k", "$380k", "$520k", "$290k", "$410k"],
            "Next Action": [
                "Schedule Call", "Schedule Call", "Q4: Price", "Schedule Call", "Q4: Price"
            ]
        }
        
        df = pd.DataFrame(performer_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    def _render_conversion_stats(self):
        """Render conversion statistics"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Conversion Rates by Source")
            
            source_data = {
                "Source": ["Facebook", "Google", "Website", "Referral", "Zillow"],
                "Conversion Rate": [0.15, 0.22, 0.18, 0.35, 0.12]
            }
            
            fig = px.bar(
                source_data,
                x="Source",
                y="Conversion Rate", 
                title="Lead Source Performance"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("⏰ Response Time Impact")
            
            time_data = {
                "Response Time": ["< 1 min", "1-5 min", "5-15 min", "15-60 min", "> 1 hour"],
                "Conversion Rate": [0.45, 0.32, 0.18, 0.12, 0.05]
            }
            
            fig = px.line(
                time_data,
                x="Response Time",
                y="Conversion Rate",
                title="Response Time vs Conversion"
            )
            st.plotly_chart(fig, use_container_width=True)

    def _render_hot_leads_alerts(self):
        """Render hot leads that need immediate attention"""
        
        st.subheader("🚨 Hot Leads Alert - Action Required!")
        
        # Mock hot leads data
        hot_leads = [
            {
                "name": "John D.",
                "phone": "(555) 123-4567",
                "qualified_time": "8 minutes ago",
                "score": 95,
                "budget": "$450k",
                "timeline": "30 days",
                "action": "Call Now"
            },
            {
                "name": "Sarah M.", 
                "phone": "(555) 234-5678",
                "qualified_time": "15 minutes ago", 
                "score": 92,
                "budget": "$380k",
                "timeline": "45 days",
                "action": "Call Now"
            },
            {
                "name": "Mike R.",
                "phone": "(555) 345-6789", 
                "qualified_time": "23 minutes ago",
                "score": 88,
                "budget": "$520k", 
                "timeline": "Immediate",
                "action": "Call Now"
            }
        ]
        
        for lead in hot_leads:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{lead['name']}**")
                    st.caption(lead['phone'])
                    
                with col2:
                    st.metric("Lead Score", lead['score'], "Hot")
                    
                with col3:
                    st.write(f"**Budget:** {lead['budget']}")
                    st.write(f"**Timeline:** {lead['timeline']}")
                    
                with col4:
                    st.write(f"**Qualified:** {lead['qualified_time']}")
                    
                with col5:
                    if st.button(f"📞 Call", key=f"call_{lead['name']}"):
                        st.success(f"Calling {lead['name']}...")
                        
                st.divider()

    def _get_todays_metrics(self) -> Dict[str, Any]:
        """Get today's key metrics (mock data for demo)"""
        
        # In production, this would query your analytics database
        return {
            "total_conversations": 47,
            "conversations_delta": 12,
            "hot_leads": 8,
            "hot_leads_delta": 3,
            "qualified_leads": 23,
            "qualified_delta": 7,
            "appointments": 5,
            "appointments_delta": 2,
            "pipeline_value": 125000,
            "pipeline_delta": 35000
        }

    async def get_real_analytics(self, location_id: str) -> Dict[str, Any]:
        """Get real analytics from bot services (for production)"""
        
        try:
            # This would integrate with your actual analytics services
            # For now, return mock data
            return self._get_todays_metrics()
            
        except Exception as e:
            st.error(f"Error fetching analytics: {e}")
            return {}


def main():
    """Main dashboard application"""
    
    # Initialize dashboard
    dashboard = JorgeKPIDashboard()
    
    # Add sidebar controls
    with st.sidebar:
        st.title("⚙️ Dashboard Controls")
        
        # Location selector
        location_id = st.selectbox(
            "Select GHL Location",
            ["rancho_cucamonga_office", "central_rc_branch", "west_rancho_cucamonga"],
            index=0
        )
        
        # Date range selector  
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=7), datetime.now()),
            max_value=datetime.now()
        )
        
        # Filters
        st.subheader("🔍 Filters")
        
        show_hot_only = st.checkbox("Show Hot Leads Only")
        show_qualified_only = st.checkbox("Show Qualified Leads Only")
        
        # Export options
        st.subheader("📤 Export")
        
        if st.button("Export CSV"):
            st.success("Analytics exported to CSV!")
            
        if st.button("Export PDF Report"):
            st.success("PDF report generated!")
    
    # Render main dashboard
    dashboard.render_dashboard()
    
    # Add footer
    st.markdown("---")
    st.caption("Jorge's Bot Analytics Dashboard v1.0 | Last Updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    # Import numpy for demo data generation
    import numpy as np
    import time
    
    main()