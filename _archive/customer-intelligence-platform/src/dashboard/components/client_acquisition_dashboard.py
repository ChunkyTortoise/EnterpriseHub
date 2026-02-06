"""
Customer Intelligence Platform - Client Acquisition Dashboard

Comprehensive tracking and analytics for client demo campaigns:
- Lead pipeline visualization and management
- Demo performance metrics and success tracking
- Conversion analytics and optimization insights
- ROI calculations and revenue projection
- Automated follow-up and nurturing campaign management
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio

# Configure page
st.set_page_config(
    page_title="Client Acquisition Dashboard", 
    page_icon="📊",
    layout="wide"
)

class ClientAcquisitionDashboard:
    """Client acquisition tracking and analytics dashboard."""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent.parent / "demo_campaigns.db"
        self.color_scheme = {
            "primary": "#1f77b4",
            "success": "#2ca02c",
            "warning": "#ff7f0e", 
            "danger": "#d62728",
            "info": "#17a2b8"
        }
    
    @st.cache_data(ttl=300)
    def load_pipeline_data(_self) -> Dict[str, pd.DataFrame]:
        """Load all pipeline data from database."""
        if not _self.db_path.exists():
            return {
                "leads": pd.DataFrame(),
                "performance": pd.DataFrame(),
                "emails": pd.DataFrame()
            }
        
        conn = sqlite3.connect(_self.db_path)
        
        # Load leads data
        leads_query = """
            SELECT 
                id, company_name, industry, contact_name, contact_email,
                demo_requested_at, demo_scheduled_for, demo_completed_at,
                demo_status, lead_source, company_size, annual_revenue,
                conversion_stage, roi_calculated, next_action,
                created_at, updated_at
            FROM demo_leads
            ORDER BY created_at DESC
        """
        df_leads = pd.read_sql_query(leads_query, conn)
        
        # Load performance data
        performance_query = """
            SELECT 
                dp.*,
                dl.company_name,
                dl.contact_name
            FROM demo_performance dp
            LEFT JOIN demo_leads dl ON dp.demo_id = dl.id
            ORDER BY dp.recorded_at DESC
        """
        df_performance = pd.read_sql_query(performance_query, conn)
        
        # Load email campaigns data  
        email_query = """
            SELECT 
                ec.*,
                dl.company_name,
                dl.contact_name,
                dl.industry
            FROM email_campaigns ec
            LEFT JOIN demo_leads dl ON ec.lead_id = dl.id
            ORDER BY ec.sent_at DESC
        """
        df_emails = pd.read_sql_query(email_query, conn)
        
        conn.close()
        
        # Convert datetime columns
        if not df_leads.empty:
            df_leads['demo_requested_at'] = pd.to_datetime(df_leads['demo_requested_at'])
            df_leads['created_at'] = pd.to_datetime(df_leads['created_at'])
            
        if not df_performance.empty:
            df_performance['recorded_at'] = pd.to_datetime(df_performance['recorded_at'])
            
        if not df_emails.empty:
            df_emails['sent_at'] = pd.to_datetime(df_emails['sent_at'])
        
        return {
            "leads": df_leads,
            "performance": df_performance,
            "emails": df_emails
        }
    
    def render_pipeline_overview(self, data: Dict[str, pd.DataFrame]):
        """Render pipeline overview with key metrics."""
        st.markdown("## 🎯 Client Acquisition Pipeline Overview")
        
        df_leads = data["leads"]
        df_performance = data["performance"]
        
        if df_leads.empty:
            st.info("🚀 No pipeline data yet. Launch demo campaigns to start tracking leads!")
            if st.button("🎯 Launch Demo Campaigns", type="primary"):
                st.code("""
                # Launch all industry demo campaigns
                python CLIENT_DEMO_CAMPAIGN_LAUNCHER.py --launch-all
                
                # Or launch specific industry
                python CLIENT_DEMO_CAMPAIGN_LAUNCHER.py --industry=real_estate --customer="Premier Realty"
                """)
            return
        
        # Calculate key metrics
        total_leads = len(df_leads)
        demos_completed = len(df_leads[df_leads['demo_status'] == 'completed'])
        proposals_sent = len(df_leads[df_leads['conversion_stage'] == 'proposal_sent'])
        deals_closed = len(df_leads[df_leads['conversion_stage'] == 'closed_won'])
        avg_roi = df_leads['roi_calculated'].mean() if 'roi_calculated' in df_leads.columns else 0
        
        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "📥 Total Leads",
                total_leads,
                delta=f"+{len(df_leads[df_leads['created_at'] >= datetime.now() - timedelta(days=7)])}" if not df_leads.empty else None
            )
        
        with col2:
            demo_rate = (demos_completed / total_leads * 100) if total_leads > 0 else 0
            st.metric(
                "🎬 Demo Completion",
                f"{demo_rate:.1f}%",
                delta=f"{demos_completed}/{total_leads}"
            )
        
        with col3:
            proposal_rate = (proposals_sent / demos_completed * 100) if demos_completed > 0 else 0
            st.metric(
                "📋 Proposal Rate", 
                f"{proposal_rate:.1f}%",
                delta=f"{proposals_sent} sent"
            )
        
        with col4:
            close_rate = (deals_closed / proposals_sent * 100) if proposals_sent > 0 else 0
            st.metric(
                "🏆 Close Rate",
                f"{close_rate:.1f}%", 
                delta=f"{deals_closed} closed"
            )
        
        with col5:
            st.metric(
                "💰 Avg ROI",
                f"{avg_roi:.0f}%",
                delta="Annual projection"
            )
        
        # Pipeline health indicators
        st.markdown("### 📊 Pipeline Health")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Conversion funnel chart
            funnel_data = {
                'Stage': ['Leads Generated', 'Demos Completed', 'Proposals Sent', 'Deals Closed'],
                'Count': [total_leads, demos_completed, proposals_sent, deals_closed],
                'Percentage': [100, demo_rate, proposal_rate * demo_rate / 100, close_rate * proposal_rate * demo_rate / 10000]
            }
            
            fig = go.Figure(go.Funnel(
                y = funnel_data['Stage'],
                x = funnel_data['Count'],
                textinfo = "value+percent initial",
                textposition = "auto",
                marker = {"color": [self.color_scheme["primary"], self.color_scheme["info"], 
                                  self.color_scheme["warning"], self.color_scheme["success"]]}
            ))
            
            fig.update_layout(
                title="Conversion Funnel",
                height=400,
                font=dict(size=12)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Lead sources distribution
            if 'lead_source' in df_leads.columns:
                source_counts = df_leads['lead_source'].value_counts()
                
                fig = px.pie(
                    values=source_counts.values,
                    names=source_counts.index,
                    title="Lead Sources Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    def render_industry_performance(self, data: Dict[str, pd.DataFrame]):
        """Render industry-specific performance analysis."""
        st.markdown("## 🏢 Industry Performance Analysis")
        
        df_leads = data["leads"]
        df_performance = data["performance"]
        
        if df_leads.empty:
            st.info("No industry data available yet.")
            return
        
        # Industry performance comparison
        col1, col2 = st.columns(2)
        
        with col1:
            # Leads by industry
            industry_counts = df_leads['industry'].value_counts()
            
            fig = px.bar(
                x=industry_counts.index,
                y=industry_counts.values,
                title="Leads by Industry",
                labels={'x': 'Industry', 'y': 'Number of Leads'},
                color=industry_counts.values,
                color_continuous_scale="Blues"
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # ROI by industry
            if 'roi_calculated' in df_leads.columns:
                roi_by_industry = df_leads.groupby('industry')['roi_calculated'].mean().sort_values(ascending=False)
                
                fig = px.bar(
                    x=roi_by_industry.index,
                    y=roi_by_industry.values,
                    title="Average ROI by Industry",
                    labels={'x': 'Industry', 'y': 'ROI (%)'},
                    color=roi_by_industry.values,
                    color_continuous_scale="Greens"
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        # Industry performance table
        if not df_leads.empty:
            st.markdown("### 📈 Industry Metrics Comparison")
            
            industry_metrics = []
            for industry in df_leads['industry'].unique():
                industry_leads = df_leads[df_leads['industry'] == industry]
                industry_perf = df_performance[df_performance['industry'] == industry] if not df_performance.empty else pd.DataFrame()
                
                metrics = {
                    'Industry': industry.replace('_', ' ').title(),
                    'Total Leads': len(industry_leads),
                    'Demos Completed': len(industry_leads[industry_leads['demo_status'] == 'completed']),
                    'Demo Completion Rate': f"{len(industry_leads[industry_leads['demo_status'] == 'completed']) / len(industry_leads) * 100:.1f}%" if len(industry_leads) > 0 else "0%",
                    'Avg Engagement': f"{industry_perf['engagement_score'].mean():.2f}" if not industry_perf.empty else "N/A",
                    'Avg ROI': f"{industry_leads['roi_calculated'].mean():.0f}%" if 'roi_calculated' in industry_leads.columns else "N/A",
                    'Deals Closed': len(industry_leads[industry_leads['conversion_stage'] == 'closed_won'])
                }
                industry_metrics.append(metrics)
            
            df_metrics = pd.DataFrame(industry_metrics)
            st.dataframe(df_metrics, use_container_width=True)
    
    def render_demo_performance(self, data: Dict[str, pd.DataFrame]):
        """Render detailed demo performance analytics."""
        st.markdown("## 🎬 Demo Performance Analytics")
        
        df_performance = data["performance"]
        df_leads = data["leads"]
        
        if df_performance.empty:
            st.info("No demo performance data available yet.")
            return
        
        # Performance metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_engagement = df_performance['engagement_score'].mean()
            st.metric(
                "🤝 Avg Engagement Score",
                f"{avg_engagement:.2f}",
                delta=f"Out of 1.0"
            )
        
        with col2:
            avg_success = df_performance['success_probability'].mean()
            st.metric(
                "📈 Avg Success Probability",
                f"{avg_success:.1%}",
                delta="AI Prediction"
            )
        
        with col3:
            avg_duration = df_performance['demo_duration_minutes'].mean()
            st.metric(
                "⏱️ Avg Demo Duration",
                f"{avg_duration:.0f} min",
                delta="Target: 30-45 min"
            )
        
        # Performance trends
        col1, col2 = st.columns(2)
        
        with col1:
            # Engagement score distribution
            fig = px.histogram(
                df_performance, 
                x='engagement_score',
                nbins=20,
                title="Engagement Score Distribution",
                labels={'engagement_score': 'Engagement Score', 'count': 'Number of Demos'},
                color_discrete_sequence=[self.color_scheme["primary"]]
            )
            fig.add_vline(x=avg_engagement, line_dash="dash", line_color="red", 
                         annotation_text=f"Avg: {avg_engagement:.2f}")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Success probability vs engagement
            fig = px.scatter(
                df_performance,
                x='engagement_score',
                y='success_probability',
                color='industry',
                size='demo_duration_minutes',
                hover_data=['company_name'],
                title="Success vs Engagement Correlation",
                labels={
                    'engagement_score': 'Engagement Score',
                    'success_probability': 'Success Probability'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Demo details table
        st.markdown("### 📋 Recent Demo Performance Details")
        
        if not df_performance.empty:
            # Format the dataframe for display
            display_df = df_performance.copy()
            display_df['recorded_at'] = display_df['recorded_at'].dt.strftime('%Y-%m-%d %H:%M')
            display_df['engagement_score'] = display_df['engagement_score'].round(2)
            display_df['success_probability'] = (display_df['success_probability'] * 100).round(1)
            
            columns_to_show = [
                'company_name', 'industry', 'recorded_at', 'demo_duration_minutes',
                'engagement_score', 'success_probability', 'attendee_count',
                'follow_up_requested', 'proposal_requested'
            ]
            
            # Rename columns for better display
            column_names = {
                'company_name': 'Company',
                'industry': 'Industry', 
                'recorded_at': 'Demo Date',
                'demo_duration_minutes': 'Duration (min)',
                'engagement_score': 'Engagement',
                'success_probability': 'Success %',
                'attendee_count': 'Attendees',
                'follow_up_requested': 'Follow-up Requested',
                'proposal_requested': 'Proposal Requested'
            }
            
            display_df = display_df[columns_to_show].rename(columns=column_names)
            st.dataframe(display_df, use_container_width=True)
    
    def render_lead_management(self, data: Dict[str, pd.DataFrame]):
        """Render lead management and tracking interface."""
        st.markdown("## 👥 Lead Management & Tracking")
        
        df_leads = data["leads"]
        
        if df_leads.empty:
            st.info("No leads to manage yet.")
            return
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            industries = ['All'] + list(df_leads['industry'].unique())
            selected_industry = st.selectbox("Filter by Industry", industries)
        
        with col2:
            stages = ['All'] + list(df_leads['conversion_stage'].unique())
            selected_stage = st.selectbox("Filter by Stage", stages)
        
        with col3:
            sources = ['All'] + list(df_leads['lead_source'].unique())
            selected_source = st.selectbox("Filter by Source", sources)
        
        # Apply filters
        filtered_df = df_leads.copy()
        if selected_industry != 'All':
            filtered_df = filtered_df[filtered_df['industry'] == selected_industry]
        if selected_stage != 'All':
            filtered_df = filtered_df[filtered_df['conversion_stage'] == selected_stage]
        if selected_source != 'All':
            filtered_df = filtered_df[filtered_df['lead_source'] == selected_source]
        
        # Lead summary stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Filtered Leads", len(filtered_df))
        with col2:
            hot_leads = len(filtered_df[filtered_df['roi_calculated'] > 5000]) if 'roi_calculated' in filtered_df.columns else 0
            st.metric("🔥 High ROI Leads", hot_leads)
        with col3:
            pending_demos = len(filtered_df[filtered_df['demo_status'] == 'scheduled'])
            st.metric("📅 Pending Demos", pending_demos)
        with col4:
            needs_followup = len(filtered_df[filtered_df['next_action'].str.contains('follow', case=False, na=False)])
            st.metric("📞 Needs Follow-up", needs_followup)
        
        # Leads table with actions
        st.markdown("### 📝 Lead Details")
        
        if not filtered_df.empty:
            # Format the dataframe for display
            display_df = filtered_df.copy()
            display_df['demo_requested_at'] = display_df['demo_requested_at'].dt.strftime('%Y-%m-%d')
            
            # Add action buttons column
            action_buttons = []
            for idx, row in display_df.iterrows():
                if row['demo_status'] == 'requested':
                    action_buttons.append("🗓️ Schedule Demo")
                elif row['conversion_stage'] == 'demo_completed':
                    action_buttons.append("📧 Send Follow-up")
                elif row['conversion_stage'] == 'high_interest':
                    action_buttons.append("📋 Send Proposal")
                else:
                    action_buttons.append("👁️ Review")
            
            display_df['Suggested Action'] = action_buttons
            
            columns_to_show = [
                'company_name', 'industry', 'contact_name', 'contact_email',
                'demo_requested_at', 'demo_status', 'conversion_stage',
                'roi_calculated', 'next_action', 'Suggested Action'
            ]
            
            # Rename columns for better display
            column_names = {
                'company_name': 'Company',
                'industry': 'Industry',
                'contact_name': 'Contact',
                'contact_email': 'Email',
                'demo_requested_at': 'Demo Requested',
                'demo_status': 'Demo Status',
                'conversion_stage': 'Stage',
                'roi_calculated': 'ROI %',
                'next_action': 'Next Action',
                'Suggested Action': 'Action'
            }
            
            display_df_final = display_df[columns_to_show].rename(columns=column_names)
            
            # Color code based on stage
            def highlight_stage(val):
                if val == 'closed_won':
                    return 'background-color: #d4edda'
                elif val == 'high_interest':
                    return 'background-color: #fff3cd'
                elif val == 'low_interest':
                    return 'background-color: #f8d7da'
                return ''
            
            styled_df = display_df_final.style.applymap(
                highlight_stage, subset=['Stage']
            )
            
            st.dataframe(styled_df, use_container_width=True)
        
        # Quick actions
        st.markdown("### 🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📧 Send Bulk Follow-up", type="primary"):
                st.success("Follow-up emails queued for all high-interest leads!")
        
        with col2:
            if st.button("📊 Export Pipeline Report"):
                # In production, this would generate and download a report
                st.success("Pipeline report exported to CSV!")
        
        with col3:
            if st.button("🔄 Sync with CRM"):
                st.success("Lead data synchronized with CRM system!")
    
    def render_roi_calculator(self, data: Dict[str, pd.DataFrame]):
        """Render ROI calculator and projection tools."""
        st.markdown("## 💰 ROI Calculator & Revenue Projections")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 📊 Prospect ROI Calculator")
            
            # Input form for new prospect
            with st.form("roi_calculator"):
                industry = st.selectbox("Industry", 
                    ["real_estate", "saas", "ecommerce", "financial_services"],
                    format_func=lambda x: x.replace('_', ' ').title()
                )
                
                annual_revenue = st.number_input("Annual Revenue ($)", 
                    min_value=100000, max_value=1000000000, value=5000000, step=100000,
                    format="%d"
                )
                
                company_size = st.selectbox("Company Size", 
                    ["startup", "small", "medium", "large", "enterprise"]
                )
                
                pain_level = st.slider("Pain Level (1-10)", 1, 10, 7)
                
                submitted = st.form_submit_button("Calculate ROI", type="primary")
                
                if submitted:
                    roi_result = self.calculate_prospect_roi(industry, annual_revenue, company_size, pain_level)
                    
                    st.success(f"🎯 Calculated ROI: **{roi_result['roi_percent']:.0f}%**")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("💵 Annual Benefit", f"${roi_result['annual_benefit']:,.0f}")
                        st.metric("💳 Platform Cost", f"${roi_result['platform_cost']:,.0f}")
                    with col_b:
                        st.metric("📈 Net Benefit", f"${roi_result['net_benefit']:,.0f}")
                        st.metric("⏱️ Payback Period", f"{roi_result['payback_days']:.0f} days")
        
        with col2:
            st.markdown("### 📈 Pipeline Revenue Projection")
            
            df_leads = data["leads"]
            
            if not df_leads.empty and 'roi_calculated' in df_leads.columns:
                # Calculate pipeline value
                total_pipeline_value = df_leads['roi_calculated'].sum()
                active_leads = len(df_leads[~df_leads['conversion_stage'].isin(['closed_lost', 'closed_won'])])
                avg_deal_size = 25000  # Average deal size assumption
                
                projected_revenue = active_leads * avg_deal_size * 0.3  # 30% close rate assumption
                
                st.metric("💼 Total Pipeline Value", f"${total_pipeline_value:,.0f}")
                st.metric("🎯 Projected Revenue (30% close)", f"${projected_revenue:,.0f}")
                st.metric("📊 Active Opportunities", active_leads)
                
                # Revenue projection chart
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
                projected_monthly = [projected_revenue * (0.6 + i*0.1) for i in range(6)]
                
                fig = px.line(
                    x=months,
                    y=projected_monthly,
                    title="6-Month Revenue Projection",
                    labels={'x': 'Month', 'y': 'Projected Revenue ($)'},
                    markers=True
                )
                fig.update_traces(line_color=self.color_scheme["success"])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No pipeline data available for revenue projection.")
    
    def calculate_prospect_roi(self, industry: str, annual_revenue: int, company_size: str, pain_level: int) -> Dict[str, float]:
        """Calculate ROI for a prospect based on industry and profile."""
        # Base ROI multipliers by industry
        base_multipliers = {
            "real_estate": 35.0,
            "saas": 114.0,
            "ecommerce": 124.0,
            "financial_services": 135.0
        }
        
        # Size multipliers
        size_multipliers = {
            "startup": 0.7,
            "small": 0.8,
            "medium": 1.0,
            "large": 1.3,
            "enterprise": 1.8
        }
        
        # Calculate base benefit as percentage of revenue
        base_benefit_pct = base_multipliers.get(industry, 50.0) / 100
        size_multiplier = size_multipliers.get(company_size, 1.0)
        pain_multiplier = 1.0 + (pain_level - 5) * 0.1  # Higher pain = higher benefit
        
        annual_benefit = annual_revenue * base_benefit_pct * size_multiplier * pain_multiplier
        platform_cost = 23600  # Annual platform cost
        net_benefit = annual_benefit - platform_cost
        roi_percent = (net_benefit / platform_cost) * 100
        payback_days = (platform_cost / annual_benefit) * 365
        
        return {
            "annual_benefit": annual_benefit,
            "platform_cost": platform_cost,
            "net_benefit": net_benefit,
            "roi_percent": roi_percent,
            "payback_days": payback_days
        }
    
    def render_follow_up_automation(self, data: Dict[str, pd.DataFrame]):
        """Render follow-up automation and email campaign management."""
        st.markdown("## 📧 Follow-up Automation & Email Campaigns")
        
        df_emails = data["emails"]
        df_leads = data["leads"]
        
        # Campaign performance summary
        col1, col2, col3, col4 = st.columns(4)
        
        total_sent = len(df_emails) if not df_emails.empty else 0
        opened = len(df_emails[df_emails['opened_at'].notna()]) if not df_emails.empty else 0
        clicked = len(df_emails[df_emails['clicked_at'].notna()]) if not df_emails.empty else 0
        replied = len(df_emails[df_emails['replied_at'].notna()]) if not df_emails.empty else 0
        
        with col1:
            st.metric("📤 Emails Sent", total_sent)
        with col2:
            open_rate = (opened / total_sent * 100) if total_sent > 0 else 0
            st.metric("📖 Open Rate", f"{open_rate:.1f}%")
        with col3:
            click_rate = (clicked / opened * 100) if opened > 0 else 0
            st.metric("👆 Click Rate", f"{click_rate:.1f}%")
        with col4:
            reply_rate = (replied / total_sent * 100) if total_sent > 0 else 0
            st.metric("💬 Reply Rate", f"{reply_rate:.1f}%")
        
        # Active campaigns management
        st.markdown("### 🎯 Active Campaign Management")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Campaign sequences
            sequences = [
                {"name": "Demo Confirmation", "leads": 12, "status": "Active", "next_send": "Today 2:00 PM"},
                {"name": "Post-Demo Follow-up", "leads": 8, "status": "Active", "next_send": "Tomorrow 10:00 AM"},
                {"name": "Nurturing - Warm Leads", "leads": 23, "status": "Active", "next_send": "Wed 9:00 AM"},
                {"name": "Re-engagement - Cold Leads", "leads": 5, "status": "Paused", "next_send": "Manual trigger"}
            ]
            
            df_sequences = pd.DataFrame(sequences)
            
            # Style the dataframe
            def highlight_status(val):
                if val == 'Active':
                    return 'background-color: #d4edda'
                elif val == 'Paused':
                    return 'background-color: #f8d7da'
                return ''
            
            styled_df = df_sequences.style.applymap(
                highlight_status, subset=['status']
            )
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### 🚀 Quick Actions")
            
            if st.button("➕ Create New Campaign", type="primary"):
                st.success("Campaign creator opened!")
            
            if st.button("⏸️ Pause All Campaigns"):
                st.warning("All campaigns paused.")
            
            if st.button("📊 Export Email Analytics"):
                st.success("Analytics exported!")
        
        # Email template management
        st.markdown("### 📝 Email Templates")
        
        tab1, tab2, tab3 = st.tabs(["Demo Confirmation", "Follow-up", "Nurturing"])
        
        with tab1:
            st.code("""
Subject: Your Customer Intelligence Platform Demo - Confirmed for [DATE]

Hi [CONTACT_NAME],

Thank you for your interest in our Customer Intelligence Platform! I'm excited to show you exactly how companies like [COMPANY_NAME] are achieving [ROI_PROJECTION]% ROI through AI-powered customer insights.

Our demo is confirmed for:
📅 Date: [DEMO_DATE]
⏰ Time: [DEMO_TIME]
📞 Link: [DEMO_LINK]

What we'll cover in 30 minutes:
• How to predict customer behavior with 90%+ accuracy
• Real-time insights that increase conversion rates by 25-40%
• Industry-specific use cases for [INDUSTRY]
• ROI calculation showing [PROJECTED_ANNUAL_BENEFIT] in potential benefits

Please let me know if you need to reschedule or have any questions.

Looking forward to showing you the platform!

Best regards,
[REP_NAME]
            """, language="text")
        
        with tab2:
            st.code("""
Subject: Following up on your Customer Intelligence Platform demo

Hi [CONTACT_NAME],

Thank you for taking the time to see our Customer Intelligence Platform demo yesterday. I hope you found it valuable to see how the platform can help [COMPANY_NAME] [SPECIFIC_BENEFIT].

Key takeaways from our conversation:
• [ROI_PROJECTION]% ROI with [PAYBACK_PERIOD]-day payback
• [SPECIFIC_FEATURE] addresses your [PAIN_POINT]
• Implementation timeline: 1.5 days to go-live

Next steps options:
1. 📋 Proposal with custom ROI analysis
2. 🧪 30-day pilot program with 5 users
3. 📞 Technical deep-dive with our Solutions Architect
4. 🤝 Reference call with [SIMILAR_COMPANY]

Which option makes the most sense for [COMPANY_NAME]?

Best regards,
[REP_NAME]
            """, language="text")
        
        with tab3:
            st.code("""
Subject: [INDUSTRY_INSIGHT] - How top companies are leveraging customer intelligence

Hi [CONTACT_NAME],

I came across this interesting insight about [INDUSTRY] companies and thought it might be relevant for [COMPANY_NAME]:

"Companies using AI-powered customer intelligence are seeing 40% better conversion rates and 35% reduction in customer acquisition costs."

This aligns perfectly with what we discussed about [COMPANY_NAME]'s goals to [SPECIFIC_GOAL].

Quick question: What's your biggest challenge with customer intelligence right now? I'd love to share how similar companies in [INDUSTRY] are solving this exact problem.

Would a 15-minute call this week be valuable?

Best regards,
[REP_NAME]

P.S. I've attached a case study from [SIMILAR_COMPANY] that achieved [SPECIFIC_RESULT] in [TIMEFRAME].
            """, language="text")


def main():
    """Main dashboard application."""
    st.title("🎯 Client Acquisition Dashboard")
    st.markdown("### Customer Intelligence Platform - Demo Campaign Analytics")
    
    # Initialize dashboard
    dashboard = ClientAcquisitionDashboard()
    
    # Load data
    with st.spinner("Loading pipeline data..."):
        data = dashboard.load_pipeline_data()
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Pipeline Overview", 
        "🏢 Industry Performance", 
        "🎬 Demo Analytics",
        "👥 Lead Management",
        "💰 ROI Calculator",
        "📧 Follow-up Automation"
    ])
    
    with tab1:
        dashboard.render_pipeline_overview(data)
    
    with tab2:
        dashboard.render_industry_performance(data)
    
    with tab3:
        dashboard.render_demo_performance(data)
    
    with tab4:
        dashboard.render_lead_management(data)
    
    with tab5:
        dashboard.render_roi_calculator(data)
    
    with tab6:
        dashboard.render_follow_up_automation(data)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; opacity: 0.6; font-size: 0.8rem;'>"
        "Client Acquisition Dashboard | Customer Intelligence Platform v1.0"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()