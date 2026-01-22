"""
Revenue Intelligence Platform - Interactive ROI Calculator

Stunning ROI calculator that demonstrates the proven 3x lead generation value
proposition with interactive customization for different industries and company sizes.

Features:
- Interactive business metrics input
- Real-time ROI calculations based on proven AgentForge results
- Industry benchmarking and customization
- Visual ROI presentation with charts and graphs
- Export capabilities for executive presentations

Author: Cave (Duke LLMOps Certified)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Color scheme for executive-grade design
COLORS = {
    'primary': '#1B365D',
    'success': '#27AE60',
    'premium': '#F39C12',
    'urgent': '#E74C3C',
    'neutral': '#95A5A6',
    'background': '#FAFBFC'
}

def render_roi_calculator():
    """Main ROI calculator interface"""
    
    st.set_page_config(
        page_title="Revenue Intelligence ROI Calculator",
        page_icon="💰",
        layout="wide"
    )
    
    # Header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['primary']}, #2C3E50); 
                padding: 2rem; border-radius: 12px; color: white; text-align: center; margin-bottom: 2rem;">
        <h1 style="margin: 0; color: white;">💰 Revenue Intelligence ROI Calculator</h1>
        <h3 style="margin: 0.5rem 0; color: white; opacity: 0.9;">Calculate Your Revenue Transformation</h3>
        <p style="margin: 0; opacity: 0.8;">Based on proven 3x lead generation results from AgentForge case study</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📊 Current Business Metrics")
        render_current_state_inputs()
    
    with col2:
        st.markdown("### 🚀 Revenue Intelligence Impact")
        render_transformation_results()
    
    st.markdown("---")
    
    # Visual ROI Analysis
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_roi_visualization()
    
    with col2:
        render_investment_breakdown()
    
    st.markdown("---")
    
    # Industry Benchmarks
    render_industry_benchmarks()
    
    st.markdown("---")
    
    # Implementation Timeline
    render_implementation_value_timeline()
    
    # Export Options
    render_export_options()

def render_current_state_inputs():
    """Render input fields for current business metrics"""
    
    # Company profile
    st.markdown("#### Company Profile")
    
    company_size = st.selectbox(
        "Company Size",
        ["Startup (1-10 employees)", "Small (11-50 employees)", "Medium (51-200 employees)", 
         "Large (201-1000 employees)", "Enterprise (1000+ employees)"],
        index=2
    )
    
    industry = st.selectbox(
        "Industry",
        ["B2B SaaS", "Professional Services", "Financial Services", "Healthcare", 
         "Manufacturing", "Real Estate", "Technology Consulting", "E-commerce"],
        index=0
    )
    
    # Sales metrics
    st.markdown("#### Current Sales Metrics")
    
    current_leads = st.number_input(
        "Monthly Qualified Leads",
        min_value=1,
        max_value=10000,
        value=get_industry_default(industry, "leads"),
        help="Number of qualified leads your sales team works monthly"
    )
    
    current_conversion = st.number_input(
        "Current Conversion Rate (%)",
        min_value=0.1,
        max_value=50.0,
        value=get_industry_default(industry, "conversion"),
        step=0.1,
        help="Percentage of qualified leads that convert to customers"
    )
    
    avg_deal_value = st.number_input(
        "Average Deal Value ($)",
        min_value=100,
        max_value=1000000,
        value=get_industry_default(industry, "deal_value"),
        help="Average value of a closed deal"
    )
    
    sales_cycle_days = st.number_input(
        "Average Sales Cycle (Days)",
        min_value=1,
        max_value=365,
        value=get_industry_default(industry, "sales_cycle"),
        help="Average days from qualified lead to closed deal"
    )
    
    # Team metrics
    st.markdown("#### Sales Team")
    
    num_sales_reps = st.number_input(
        "Number of Sales Reps",
        min_value=1,
        max_value=500,
        value=get_company_size_default(company_size, "sales_reps")
    )
    
    avg_rep_cost = st.number_input(
        "Average Rep Cost (Annual $)",
        min_value=30000,
        max_value=300000,
        value=get_company_size_default(company_size, "rep_cost"),
        help="Fully loaded cost per sales rep (salary + benefits + commissions)"
    )
    
    # Store in session state for use in other components
    st.session_state.update({
        'company_size': company_size,
        'industry': industry,
        'current_leads': current_leads,
        'current_conversion': current_conversion,
        'avg_deal_value': avg_deal_value,
        'sales_cycle_days': sales_cycle_days,
        'num_sales_reps': num_sales_reps,
        'avg_rep_cost': avg_rep_cost
    })

def render_transformation_results():
    """Show transformation results based on proven AgentForge methodology"""
    
    # Get current metrics from session state
    current_leads = st.session_state.get('current_leads', 100)
    current_conversion = st.session_state.get('current_conversion', 3.0)
    avg_deal_value = st.session_state.get('avg_deal_value', 25000)
    num_sales_reps = st.session_state.get('num_sales_reps', 5)
    
    # Calculate current state
    current_monthly_deals = current_leads * (current_conversion / 100)
    current_monthly_revenue = current_monthly_deals * avg_deal_value
    current_annual_revenue = current_monthly_revenue * 12
    
    st.markdown("#### Proven Transformation Results")
    
    # AgentForge proven improvements
    st.info("""
    **Based on documented AgentForge case study:**
    - 3x Lead Generation Improvement  
    - 45% Conversion Rate Boost
    - 50% Sales Productivity Gain
    """)
    
    # Calculate improvements
    improved_leads = current_leads * 3.0  # 3x improvement
    improved_conversion = current_conversion * 1.45  # 45% improvement
    
    # With productivity gains, assume 20% better deal values from better qualification
    improved_deal_value = avg_deal_value * 1.20
    
    # Calculate new performance
    improved_monthly_deals = improved_leads * (improved_conversion / 100)
    improved_monthly_revenue = improved_monthly_deals * improved_deal_value
    improved_annual_revenue = improved_monthly_revenue * 12
    
    # Display improvements
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Monthly Leads",
            f"{improved_leads:,.0f}",
            delta=f"+{improved_leads - current_leads:,.0f} ({300:.0f}%)"
        )
        
        st.metric(
            "Conversion Rate",
            f"{improved_conversion:.1f}%",
            delta=f"+{improved_conversion - current_conversion:.1f}% ({45:.0f}%)"
        )
    
    with col2:
        st.metric(
            "Monthly Revenue",
            f"${improved_monthly_revenue:,.0f}",
            delta=f"+${improved_monthly_revenue - current_monthly_revenue:,.0f}"
        )
        
        st.metric(
            "Annual Revenue",
            f"${improved_annual_revenue:,.0f}",
            delta=f"+${improved_annual_revenue - current_annual_revenue:,.0f}"
        )
    
    # Store calculated improvements
    st.session_state.update({
        'current_annual_revenue': current_annual_revenue,
        'improved_annual_revenue': improved_annual_revenue,
        'revenue_increase': improved_annual_revenue - current_annual_revenue,
        'improved_leads': improved_leads,
        'improved_conversion': improved_conversion,
        'improved_monthly_revenue': improved_monthly_revenue
    })

def render_roi_visualization():
    """Create comprehensive ROI visualization"""
    
    # Get metrics
    current_annual_revenue = st.session_state.get('current_annual_revenue', 1000000)
    improved_annual_revenue = st.session_state.get('improved_annual_revenue', 2000000)
    revenue_increase = st.session_state.get('revenue_increase', 1000000)
    num_sales_reps = st.session_state.get('num_sales_reps', 5)
    
    # Platform investment calculation
    st.markdown("#### 📈 Investment Analysis")
    
    pricing_model = st.selectbox(
        "Pricing Model",
        ["Performance-Based (2% of additional revenue)", 
         "SaaS Subscription ($10K per rep annually)",
         "Enterprise License ($50K annually)",
         "Custom Implementation ($100K one-time + $25K annually)"],
        help="Choose the pricing model that fits your organization"
    )
    
    # Calculate investment based on pricing model
    if "Performance-Based" in pricing_model:
        annual_investment = revenue_increase * 0.02  # 2% of additional revenue
        investment_type = "Performance-Based"
    elif "SaaS Subscription" in pricing_model:
        annual_investment = num_sales_reps * 10000  # $10K per rep
        investment_type = "SaaS Subscription"
    elif "Enterprise License" in pricing_model:
        annual_investment = 50000
        investment_type = "Enterprise License"
    else:  # Custom Implementation
        annual_investment = 125000  # $100K + $25K
        investment_type = "Custom Implementation"
    
    # ROI Calculations
    net_gain = revenue_increase - annual_investment
    roi_percentage = (net_gain / annual_investment) * 100 if annual_investment > 0 else 0
    payback_months = (annual_investment / (revenue_increase / 12)) if revenue_increase > 0 else 0
    
    # Create visualization
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Revenue Comparison', 'ROI Analysis', 'Monthly Impact', 'Investment Breakdown'),
        specs=[[{"type": "bar"}, {"type": "indicator"}],
               [{"type": "scatter"}, {"type": "pie"}]]
    )
    
    # Revenue comparison
    fig.add_trace(
        go.Bar(
            name="Annual Revenue",
            x=["Current State", "With Revenue Intelligence"],
            y=[current_annual_revenue, improved_annual_revenue],
            marker_color=[COLORS['neutral'], COLORS['success']]
        ),
        row=1, col=1
    )
    
    # ROI Indicator
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=roi_percentage,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "ROI %"},
            delta={'reference': 1000},
            gauge={
                'axis': {'range': [None, 5000]},
                'bar': {'color': COLORS['success']},
                'steps': [{'range': [0, 1000], 'color': "lightgray"},
                         {'range': [1000, 3000], 'color': "gray"}],
                'threshold': {'line': {'color': "red", 'width': 4},
                            'thickness': 0.75, 'value': 2000}
            }
        ),
        row=1, col=2
    )
    
    # Monthly impact timeline
    months = list(range(1, 13))
    monthly_increase = revenue_increase / 12
    cumulative_impact = [monthly_increase * i for i in months]
    
    fig.add_trace(
        go.Scatter(
            x=months,
            y=cumulative_impact,
            mode='lines+markers',
            name='Cumulative Revenue Impact',
            line=dict(color=COLORS['success'], width=3)
        ),
        row=2, col=1
    )
    
    # Investment breakdown
    fig.add_trace(
        go.Pie(
            labels=["Platform Investment", "Additional Revenue"],
            values=[annual_investment, net_gain],
            hole=0.4,
            marker_colors=[COLORS['premium'], COLORS['success']]
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        height=800,
        title_text="Revenue Intelligence Platform ROI Analysis",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Key metrics summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Annual Investment",
            f"${annual_investment:,.0f}",
            delta=f"{investment_type}"
        )
    
    with col2:
        st.metric(
            "Net Annual Gain",
            f"${net_gain:,.0f}",
            delta="After platform cost"
        )
    
    with col3:
        st.metric(
            "ROI",
            f"{roi_percentage:,.0f}%",
            delta="Annual return"
        )
    
    with col4:
        st.metric(
            "Payback Period",
            f"{payback_months:.1f} months",
            delta="Break-even time"
        )

def render_investment_breakdown():
    """Render detailed investment breakdown"""
    
    st.markdown("#### 💼 Investment Components")
    
    # Platform costs
    platform_cost = st.session_state.get('annual_investment', 100000)
    
    investment_breakdown = {
        "Platform License": platform_cost * 0.60,
        "Implementation": platform_cost * 0.25,
        "Training & Support": platform_cost * 0.10,
        "Integration": platform_cost * 0.05
    }
    
    for component, cost in investment_breakdown.items():
        st.markdown(f"**{component}**: ${cost:,.0f}")
    
    st.markdown("#### 🎯 Success Guarantees")
    
    guarantees = [
        "✅ 3x lead generation or money back",
        "✅ Sub-100ms response time SLA",
        "✅ 99.9% uptime guarantee", 
        "✅ 90-day performance guarantee",
        "✅ Unlimited training and support"
    ]
    
    for guarantee in guarantees:
        st.markdown(guarantee)
    
    st.markdown("#### 📈 Value Drivers")
    
    value_drivers = [
        "🚀 Lead generation efficiency",
        "🎯 Sales rep productivity gains",
        "📊 Conversion rate optimization",
        "⚡ Faster deal closure",
        "🔍 Better lead qualification",
        "📞 Real-time sales coaching"
    ]
    
    for driver in value_drivers:
        st.markdown(driver)

def render_industry_benchmarks():
    """Show industry-specific benchmarks and comparisons"""
    
    st.markdown("### 📊 Industry Benchmarks & Competitive Analysis")
    
    industry = st.session_state.get('industry', 'B2B SaaS')
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Industry benchmark data
        benchmark_data = get_industry_benchmarks(industry)
        
        fig = go.Figure()
        
        metrics = list(benchmark_data.keys())
        industry_avg = list(benchmark_data.values())
        with_platform = [val * 2.5 for val in industry_avg]  # Conservative 2.5x improvement
        
        fig.add_trace(go.Scatterpolar(
            r=industry_avg,
            theta=metrics,
            fill='toself',
            name=f'{industry} Average',
            line_color=COLORS['neutral']
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=with_platform,
            theta=metrics,
            fill='toself',
            name='With Revenue Intelligence',
            line_color=COLORS['success']
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(with_platform)]
                )
            ),
            title=f"{industry} Performance Comparison",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Industry Insights")
        
        industry_insights = get_industry_insights(industry)
        for insight in industry_insights:
            st.markdown(f"• {insight}")
        
        st.markdown("#### Competitive Advantages")
        
        competitive_advantages = [
            "Only platform with proven 3x results",
            "30-day deployment vs 6-12 months",
            "Performance-based pricing available", 
            "Real-time voice coaching included",
            "Enterprise security & compliance"
        ]
        
        for advantage in competitive_advantages:
            st.markdown(f"✅ {advantage}")

def render_implementation_value_timeline():
    """Show value realization timeline"""
    
    st.markdown("### ⏰ Implementation & Value Timeline")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Timeline data
        weeks = ["Week 1", "Week 2", "Week 3", "Week 4", "Month 2", "Month 3", "Month 6", "Month 12"]
        value_realized = [0, 15, 35, 60, 75, 85, 95, 100]
        investment_made = [25, 50, 75, 100, 100, 100, 100, 100]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=weeks,
            y=value_realized,
            mode='lines+markers',
            name='Value Realized (%)',
            line=dict(color=COLORS['success'], width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=weeks,
            y=investment_made,
            mode='lines+markers',
            name='Investment Made (%)',
            line=dict(color=COLORS['premium'], width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Value Realization Timeline",
            xaxis_title="Timeline",
            yaxis_title="Percentage (%)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Milestone Values")
        
        revenue_increase = st.session_state.get('revenue_increase', 1000000)
        
        milestones = [
            ("30 Days", f"${revenue_increase * 0.15 / 12:,.0f}/month"),
            ("60 Days", f"${revenue_increase * 0.35 / 12:,.0f}/month"),
            ("90 Days", f"${revenue_increase * 0.60 / 12:,.0f}/month"),
            ("6 Months", f"${revenue_increase * 0.95 / 12:,.0f}/month")
        ]
        
        for timeline, value in milestones:
            st.metric(timeline, value)

def render_export_options():
    """Render export and sharing options"""
    
    st.markdown("### 📤 Export & Share Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Executive Summary", use_container_width=True):
            # Generate executive summary
            summary_data = generate_executive_summary()
            st.download_button(
                label="Download PDF Report",
                data=summary_data,
                file_name=f"revenue_intelligence_roi_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
    
    with col2:
        if st.button("📈 Export Financial Model", use_container_width=True):
            # Generate financial model
            financial_data = generate_financial_model()
            st.download_button(
                label="Download Excel Model", 
                data=financial_data,
                file_name=f"revenue_intelligence_financial_model_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col3:
        if st.button("🎯 Schedule Executive Briefing", use_container_width=True):
            st.markdown("""
            **Ready to discuss your results?**
            
            📧 **Email**: revenue-intelligence@platform.ai  
            📞 **Phone**: 1-800-REVENUE  
            🗓️ **Calendar**: [Schedule 30-min briefing](https://platform.ai/demo)
            
            *Custom demo with your actual data*
            """)

# Helper functions

def get_industry_default(industry: str, metric: str) -> float:
    """Get industry default values for metrics"""
    
    defaults = {
        'B2B SaaS': {
            'leads': 200,
            'conversion': 3.5,
            'deal_value': 45000,
            'sales_cycle': 45
        },
        'Professional Services': {
            'leads': 150,
            'conversion': 5.0,
            'deal_value': 25000,
            'sales_cycle': 60
        },
        'Financial Services': {
            'leads': 100,
            'conversion': 8.0,
            'deal_value': 75000,
            'sales_cycle': 90
        },
        'Healthcare': {
            'leads': 80,
            'conversion': 6.0,
            'deal_value': 50000,
            'sales_cycle': 120
        },
        'Manufacturing': {
            'leads': 60,
            'conversion': 4.0,
            'deal_value': 125000,
            'sales_cycle': 180
        }
    }
    
    return defaults.get(industry, defaults['B2B SaaS']).get(metric, 100)

def get_company_size_default(company_size: str, metric: str) -> int:
    """Get company size defaults"""
    
    if "Startup" in company_size:
        defaults = {'sales_reps': 2, 'rep_cost': 75000}
    elif "Small" in company_size:
        defaults = {'sales_reps': 5, 'rep_cost': 85000}
    elif "Medium" in company_size:
        defaults = {'sales_reps': 15, 'rep_cost': 95000}
    elif "Large" in company_size:
        defaults = {'sales_reps': 50, 'rep_cost': 110000}
    else:  # Enterprise
        defaults = {'sales_reps': 150, 'rep_cost': 125000}
    
    return defaults.get(metric, 75000)

def get_industry_benchmarks(industry: str) -> Dict[str, float]:
    """Get industry benchmark metrics for radar chart"""
    
    benchmarks = {
        'B2B SaaS': {
            'Lead Quality': 70,
            'Conversion Rate': 65,
            'Sales Velocity': 60,
            'Deal Size': 75,
            'Rep Productivity': 55
        },
        'Professional Services': {
            'Lead Quality': 65,
            'Conversion Rate': 70,
            'Sales Velocity': 50,
            'Deal Size': 60,
            'Rep Productivity': 65
        }
    }
    
    return benchmarks.get(industry, benchmarks['B2B SaaS'])

def get_industry_insights(industry: str) -> List[str]:
    """Get industry-specific insights"""
    
    insights = {
        'B2B SaaS': [
            "Average lead qualification cost: $240",
            "Typical sales cycle: 45-90 days",
            "Conversion rates declining 3% annually",
            "Voice coaching shows 67% improvement"
        ],
        'Professional Services': [
            "Relationship-driven sales process",
            "Longer decision cycles but higher values",
            "Trust and expertise critical",
            "Referral optimization important"
        ]
    }
    
    return insights.get(industry, insights['B2B SaaS'])

def generate_executive_summary() -> bytes:
    """Generate executive summary PDF"""
    # Placeholder - would generate actual PDF
    return b"PDF data would be generated here"

def generate_financial_model() -> bytes:
    """Generate Excel financial model"""
    # Placeholder - would generate actual Excel file
    return b"Excel data would be generated here"

if __name__ == "__main__":
    render_roi_calculator()