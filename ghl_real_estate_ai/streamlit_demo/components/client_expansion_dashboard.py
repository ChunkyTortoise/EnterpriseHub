#!/usr/bin/env python3
"""
Client Expansion Intelligence Dashboard

Interactive Streamlit dashboard for visualizing and executing client expansion
framework. Provides real-time insights, opportunity prioritization, action
tracking, and revenue forecasting for scaling $130K → $400K MRR.
"""

import streamlit as st
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio

from ghl_real_estate_ai.services.client_expansion_intelligence import (
    get_expansion_intelligence,
    ExpansionTier,
    ReadinessLevel
)


def render_client_expansion_dashboard():
    """Render comprehensive client expansion dashboard."""

    st.title("💰 Client Expansion Intelligence Dashboard")
    st.markdown("### Strategic Framework: $130K → $400K MRR in 90 Days")

    # Get expansion intelligence
    expansion_service = get_expansion_intelligence()

    # Sidebar filters
    st.sidebar.header("Dashboard Filters")
    show_tier_filter = st.sidebar.multiselect(
        "Expansion Tiers",
        options=[
            ExpansionTier.TIER_1_10X.value,
            ExpansionTier.TIER_2_5X.value,
            ExpansionTier.TIER_3_2X.value
        ],
        default=[
            ExpansionTier.TIER_1_10X.value,
            ExpansionTier.TIER_2_5X.value,
            ExpansionTier.TIER_3_2X.value
        ]
    )

    show_readiness_filter = st.sidebar.multiselect(
        "Readiness Levels",
        options=[
            ReadinessLevel.READY_NOW.value,
            ReadinessLevel.READY_SOON.value,
            ReadinessLevel.NEEDS_NURTURE.value
        ],
        default=[
            ReadinessLevel.READY_NOW.value,
            ReadinessLevel.READY_SOON.value
        ]
    )

    # Generate framework button
    if st.sidebar.button("🔄 Generate Expansion Framework", type="primary"):
        with st.spinner("Analyzing 50+ clients and generating expansion opportunities..."):
            framework = run_async(
                expansion_service.generate_expansion_framework(include_action_plan=True)
            )
            st.session_state['expansion_framework'] = framework
            st.success("Framework generated successfully!")

    # Check if framework exists
    if 'expansion_framework' not in st.session_state:
        st.info("👆 Click 'Generate Expansion Framework' to begin analysis")
        return

    framework = st.session_state['expansion_framework']

    # Overview metrics
    render_overview_metrics(framework)

    # Tab navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🎯 Top 20 Opportunities",
        "📈 Revenue Projections",
        "✅ Action Plan",
        "💡 Value Propositions"
    ])

    with tab1:
        render_overview_tab(framework, show_tier_filter)

    with tab2:
        render_opportunities_tab(framework, show_tier_filter, show_readiness_filter)

    with tab3:
        render_revenue_projections_tab(framework)

    with tab4:
        render_action_plan_tab(framework)

    with tab5:
        render_value_propositions_tab(framework)


def render_overview_metrics(framework: dict):
    """Render high-level overview metrics."""

    overview = framework.get('overview', {})
    revenue_projections = framework.get('revenue_projections', {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Current MRR",
            f"${overview.get('current_mrr', 0):,.0f}",
            delta=None
        )

    with col2:
        st.metric(
            "Target MRR",
            f"${overview.get('target_mrr', 0):,.0f}",
            delta=f"+${overview.get('expansion_needed', 0):,.0f}"
        )

    with col3:
        st.metric(
            "Opportunities",
            overview.get('opportunities_identified', 0),
            delta=None
        )

    with col4:
        weighted_potential = revenue_projections.get('weighted_potential', 0)
        target_achievement = revenue_projections.get('target_achievement_percentage', 0)
        st.metric(
            "Weighted Pipeline",
            f"${weighted_potential:,.0f}",
            delta=f"{target_achievement:.0f}% of target"
        )

    st.markdown("---")


def render_overview_tab(framework: dict, tier_filter: list):
    """Render overview tab with tier analysis and charts."""

    st.subheader("Client Segmentation by Expansion Tier")

    tier_analysis = framework.get('tier_segmentation', {})

    # Tier comparison
    tier_data = []
    for tier_key, tier_info in tier_analysis.items():
        tier_name = tier_key.replace('_', ' ').title()
        tier_data.append({
            'Tier': tier_name,
            'Client Count': tier_info.get('count', 0),
            'Total Potential ($)': tier_info.get('total_potential', 0),
            'Avg Potential ($)': tier_info.get('avg_potential', 0),
            'Success Rate (%)': tier_info.get('avg_success_probability', 0) * 100
        })

    df_tiers = pd.DataFrame(tier_data)

    # Display tier table
    st.dataframe(
        df_tiers.style.format({
            'Total Potential ($)': '${:,.0f}',
            'Avg Potential ($)': '${:,.0f}',
            'Success Rate (%)': '{:.1f}%'
        }),
        use_container_width=True
    )

    # Tier distribution chart
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Client Distribution by Tier")
        fig_dist = px.pie(
            df_tiers,
            values='Client Count',
            names='Tier',
            title='Client Count by Tier',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with col2:
        st.markdown("#### Revenue Potential by Tier")
        fig_revenue = px.bar(
            df_tiers,
            x='Tier',
            y='Total Potential ($)',
            title='Total Expansion Potential',
            color='Success Rate (%)',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_revenue, use_container_width=True)


def render_opportunities_tab(framework: dict, tier_filter: list, readiness_filter: list):
    """Render top 20 opportunities with filtering and details."""

    st.subheader("🎯 Top 20 Prioritized Expansion Opportunities")

    opportunities = framework.get('top_20_opportunities', [])

    if not opportunities:
        st.warning("No opportunities found matching filters")
        return

    # Convert to DataFrame
    opp_data = []
    for opp in opportunities:
        # Apply filters
        if opp['expansion_tier'] not in tier_filter:
            continue
        if opp['readiness_level'] not in readiness_filter:
            continue

        opp_data.append({
            'Priority': opp['strategic_priority'],
            'Client': opp['client_name'],
            'Tier': opp['expansion_tier'].replace('_', ' ').title(),
            'Current ARR': float(opp['current_arr']),
            'Target ARR': float(opp['target_arr']),
            'Expansion $': float(opp['expansion_potential']),
            'Multiple': f"{opp['expansion_multiple']:.1f}x",
            'Readiness': opp['readiness_level'].replace('_', ' ').title(),
            'Score': opp['readiness_score'],
            'Success %': f"{opp['success_probability'] * 100:.0f}%",
            'Close Days': opp['estimated_close_days'],
            'Next Action': opp['next_action'],
            'Whale': '🐋' if opp.get('whale_potential') else '',
            'Reference': '⭐' if opp.get('reference_value') else ''
        })

    df_opps = pd.DataFrame(opp_data)

    if df_opps.empty:
        st.warning("No opportunities matching selected filters")
        return

    # Sort by priority
    df_opps = df_opps.sort_values('Priority', ascending=False)

    # Display opportunities table
    st.dataframe(
        df_opps.style.background_gradient(
            subset=['Priority', 'Score'],
            cmap='RdYlGn'
        ).format({
            'Current ARR': '${:,.0f}',
            'Target ARR': '${:,.0f}',
            'Expansion $': '${:,.0f}',
            'Score': '{:.1f}'
        }),
        use_container_width=True,
        height=600
    )

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Opportunities",
            len(df_opps),
            delta=None
        )

    with col2:
        total_expansion = df_opps['Expansion $'].sum()
        st.metric(
            "Total Potential",
            f"${total_expansion:,.0f}",
            delta=None
        )

    with col3:
        avg_deal = df_opps['Expansion $'].mean()
        st.metric(
            "Avg Deal Size",
            f"${avg_deal:,.0f}",
            delta=None
        )

    with col4:
        avg_close = df_opps['Close Days'].mean()
        st.metric(
            "Avg Close Time",
            f"{avg_close:.0f} days",
            delta=None
        )

    # Readiness distribution
    st.markdown("### Readiness Distribution")
    col1, col2 = st.columns(2)

    with col1:
        readiness_counts = df_opps['Readiness'].value_counts()
        fig_readiness = px.bar(
            x=readiness_counts.index,
            y=readiness_counts.values,
            title='Opportunities by Readiness Level',
            labels={'x': 'Readiness Level', 'y': 'Count'}
        )
        st.plotly_chart(fig_readiness, use_container_width=True)

    with col2:
        tier_revenue = df_opps.groupby('Tier')['Expansion $'].sum().reset_index()
        fig_tier_rev = px.pie(
            tier_revenue,
            values='Expansion $',
            names='Tier',
            title='Revenue Distribution by Tier'
        )
        st.plotly_chart(fig_tier_rev, use_container_width=True)


def render_revenue_projections_tab(framework: dict):
    """Render revenue projections and forecasting."""

    st.subheader("📈 Revenue Projections & Forecasting")

    projections = framework.get('revenue_projections', {})

    # Key metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Potential",
            f"${projections.get('total_potential', 0):,.0f}",
            delta=None
        )

    with col2:
        st.metric(
            "Weighted (Risk-Adjusted)",
            f"${projections.get('weighted_potential', 0):,.0f}",
            delta=None
        )

    with col3:
        target_pct = projections.get('target_achievement_percentage', 0)
        st.metric(
            "Target Achievement",
            f"{target_pct:.0f}%",
            delta=f"{target_pct - 100:.0f}pp vs target"
        )

    # 30/60/90 day projections
    st.markdown("### Timeline-Based Revenue Forecast")

    timeline_data = {
        'Period': ['30 Days', '60 Days', '90 Days'],
        'Projected ARR': [
            projections.get('day_30_projection', 0),
            projections.get('day_60_projection', 0),
            projections.get('day_90_projection', 0)
        ]
    }

    # Calculate cumulative
    timeline_data['Cumulative ARR'] = [
        sum(timeline_data['Projected ARR'][:i+1])
        for i in range(len(timeline_data['Projected ARR']))
    ]

    timeline_data['Monthly MRR'] = [
        arr / 12 for arr in timeline_data['Cumulative ARR']
    ]

    df_timeline = pd.DataFrame(timeline_data)

    # Display timeline chart
    fig_timeline = go.Figure()

    fig_timeline.add_trace(go.Bar(
        name='Period ARR',
        x=df_timeline['Period'],
        y=df_timeline['Projected ARR'],
        text=[f"${v:,.0f}" for v in df_timeline['Projected ARR']],
        textposition='auto',
    ))

    fig_timeline.add_trace(go.Scatter(
        name='Cumulative ARR',
        x=df_timeline['Period'],
        y=df_timeline['Cumulative ARR'],
        mode='lines+markers+text',
        text=[f"${v:,.0f}" for v in df_timeline['Cumulative ARR']],
        textposition='top center',
        line=dict(color='green', width=3)
    ))

    fig_timeline.update_layout(
        title='Revenue Projection Timeline',
        xaxis_title='Time Period',
        yaxis_title='Annual Recurring Revenue ($)',
        barmode='group',
        height=400
    )

    st.plotly_chart(fig_timeline, use_container_width=True)

    # Display detailed table
    st.dataframe(
        df_timeline.style.format({
            'Projected ARR': '${:,.0f}',
            'Cumulative ARR': '${:,.0f}',
            'Monthly MRR': '${:,.0f}'
        }),
        use_container_width=True
    )

    # MRR progression chart
    st.markdown("### MRR Growth Trajectory")

    current_mrr = framework.get('overview', {}).get('current_mrr', 130000)
    target_mrr = framework.get('overview', {}).get('target_mrr', 400000)

    mrr_progression = {
        'Milestone': ['Current', 'Month 1', 'Month 2', 'Month 3', 'Target'],
        'MRR': [
            current_mrr,
            current_mrr + df_timeline.loc[0, 'Monthly MRR'],
            current_mrr + df_timeline.loc[1, 'Monthly MRR'],
            current_mrr + df_timeline.loc[2, 'Monthly MRR'],
            target_mrr
        ]
    }

    df_mrr = pd.DataFrame(mrr_progression)

    fig_mrr = px.line(
        df_mrr,
        x='Milestone',
        y='MRR',
        title='MRR Growth Trajectory',
        markers=True,
        text='MRR'
    )

    fig_mrr.update_traces(
        texttemplate='$%{text:,.0f}',
        textposition='top center'
    )

    fig_mrr.add_hline(
        y=target_mrr,
        line_dash="dash",
        line_color="green",
        annotation_text="Target MRR"
    )

    fig_mrr.update_layout(height=400)

    st.plotly_chart(fig_mrr, use_container_width=True)


def render_action_plan_tab(framework: dict):
    """Render 30/60/90-day action plan."""

    st.subheader("✅ 30/60/90-Day Execution Action Plan")

    action_plan = framework.get('action_plan')

    if not action_plan:
        st.warning("Action plan not generated")
        return

    # Plan overview
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Target Revenue",
            f"${float(action_plan['total_target_revenue']):,.0f}",
            delta=None
        )

    with col2:
        st.metric(
            "Target Clients",
            action_plan['target_client_count'],
            delta=None
        )

    with col3:
        kpis = action_plan.get('kpis', {})
        st.metric(
            "Target Close Rate",
            f"{kpis.get('target_close_rate', 0) * 100:.0f}%",
            delta=None
        )

    # 30-day plan
    st.markdown("### 🎯 30-Day Plan: Foundation & Quick Wins")

    day_30 = action_plan.get('day_30_targets', {})
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Target Clients", day_30.get('target_clients', 0))
    with col2:
        st.metric("Target Revenue", f"${day_30.get('target_revenue', 0):,.0f}")
    with col3:
        st.metric("Meetings", day_30.get('target_meetings', 0))
    with col4:
        st.metric("Proposals", day_30.get('target_proposals', 0))

    # Actions
    st.markdown("#### Key Actions")
    actions_30 = action_plan.get('day_30_actions', [])
    if actions_30:
        df_actions_30 = pd.DataFrame(actions_30[:5])
        st.dataframe(
            df_actions_30.style.format({
                'potential_value': '${:,.0f}'
            }),
            use_container_width=True
        )

    # Milestones
    st.markdown("#### Success Milestones")
    for milestone in action_plan.get('day_30_milestones', []):
        st.markdown(f"- {milestone}")

    st.markdown("---")

    # 60-day plan
    st.markdown("### 📊 60-Day Plan: Momentum & Scale")

    day_60 = action_plan.get('day_60_targets', {})
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Target Clients", day_60.get('target_clients', 0))
    with col2:
        st.metric("Target Revenue", f"${day_60.get('target_revenue', 0):,.0f}")
    with col3:
        st.metric("Meetings", day_60.get('target_meetings', 0))
    with col4:
        st.metric("Proposals", day_60.get('target_proposals', 0))

    # Actions
    st.markdown("#### Key Actions")
    actions_60 = action_plan.get('day_60_actions', [])
    if actions_60:
        df_actions_60 = pd.DataFrame(actions_60[:5])
        st.dataframe(
            df_actions_60.style.format({
                'potential_value': '${:,.0f}'
            }),
            use_container_width=True
        )

    # Milestones
    st.markdown("#### Success Milestones")
    for milestone in action_plan.get('day_60_milestones', []):
        st.markdown(f"- {milestone}")

    st.markdown("---")

    # 90-day plan
    st.markdown("### 🚀 90-Day Plan: Final Push & Goal Achievement")

    day_90 = action_plan.get('day_90_targets', {})
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Target Clients", day_90.get('target_clients', 0))
    with col2:
        st.metric("Target Revenue", f"${day_90.get('target_revenue', 0):,.0f}")
    with col3:
        st.metric("Meetings", day_90.get('target_meetings', 0))
    with col4:
        st.metric("Proposals", day_90.get('target_proposals', 0))

    # Actions
    st.markdown("#### Key Actions")
    actions_90 = action_plan.get('day_90_actions', [])
    if actions_90:
        df_actions_90 = pd.DataFrame(actions_90[:5])
        st.dataframe(
            df_actions_90.style.format({
                'potential_value': '${:,.0f}'
            }),
            use_container_width=True
        )

    # Milestones
    st.markdown("#### Success Milestones")
    for milestone in action_plan.get('day_90_milestones', []):
        st.markdown(f"- {milestone}")

    # Success criteria
    st.markdown("---")
    st.markdown("### 🏆 Overall Success Criteria")
    for criteria in action_plan.get('success_criteria', []):
        st.markdown(f"✓ {criteria}")

    # Resources required
    st.markdown("---")
    st.markdown("### 🛠️ Resources Required")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Team Resources")
        team = action_plan.get('team_resources', {})
        for role, count in team.items():
            st.markdown(f"- **{role.replace('_', ' ').title()}**: {count} FTE")

    with col2:
        st.markdown("#### Budget & Tools")
        st.metric("Budget Required", f"${float(action_plan.get('budget_required', 0)):,.0f}")

        st.markdown("**Tools Needed:**")
        for tool in action_plan.get('tools_needed', []):
            st.markdown(f"- {tool}")


def render_value_propositions_tab(framework: dict):
    """Render custom value propositions for top clients."""

    st.subheader("💡 Custom Value Propositions")

    value_props = framework.get('value_propositions', [])

    if not value_props:
        st.warning("No value propositions generated yet")
        st.info("Value propositions are automatically generated for the top 10 priority opportunities")
        return

    # Client selector
    client_names = [vp['client_name'] for vp in value_props]
    selected_client = st.selectbox("Select Client", client_names)

    # Find selected value prop
    selected_vp = None
    for vp in value_props:
        if vp['client_name'] == selected_client:
            selected_vp = vp
            break

    if not selected_vp:
        return

    # Display value proposition
    st.markdown(f"## {selected_vp['client_name']}")
    st.markdown(f"**Generated**: {selected_vp['generated_at']}")

    # Pain points & solutions
    st.markdown("### 🎯 Pain Points & Solutions")

    for pain, solution in selected_vp.get('solution_mapping', {}).items():
        with st.expander(f"**{pain}**"):
            st.markdown(f"**Solution**: {solution}")

    # ROI projection
    st.markdown("### 📊 ROI Projection")

    roi_data = selected_vp.get('roi_projection', {})

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Current ROI",
            f"{roi_data.get('current_roi_percentage', 0):,.0f}%"
        )

    with col2:
        st.metric(
            "Projected ROI",
            f"{roi_data.get('projected_roi_percentage', 0):,.0f}%",
            delta=f"+{roi_data.get('projected_roi_percentage', 0) - roi_data.get('current_roi_percentage', 0):,.0f}%"
        )

    with col3:
        st.metric(
            "Payback Period",
            f"{roi_data.get('payback_period_months', 0)} months"
        )

    # Financial impact
    st.markdown("#### Financial Impact")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Incremental Revenue",
            f"${roi_data.get('incremental_revenue_impact', 0):,.0f}"
        )

    with col2:
        st.metric(
            "3-Year Value",
            f"${roi_data.get('3_year_value', 0):,.0f}"
        )

    # Success stories
    st.markdown("### ⭐ Comparable Success Stories")
    for story in selected_vp.get('comparable_success_stories', []):
        st.markdown(f"- {story}")

    # Features needed
    st.markdown("### 🔧 Specific Features Recommended")
    for feature in selected_vp.get('specific_features_needed', []):
        st.markdown(f"- {feature}")

    # Competitive advantages
    st.markdown("### 🏆 Competitive Advantages")
    for advantage in selected_vp.get('competitive_advantages', []):
        st.markdown(f"- {advantage}")

    # Pricing
    st.markdown("### 💰 Pricing Strategy")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Proposed Monthly",
            f"${float(selected_vp.get('proposed_pricing', 0)):,.2f}"
        )

    with col2:
        st.metric(
            "Payment Terms",
            selected_vp.get('payment_terms', 'Monthly')
        )

    st.markdown(f"**Justification**: {selected_vp.get('pricing_justification', '')}")

    if selected_vp.get('discount_strategy'):
        st.success(f"🎁 **Special Offer**: {selected_vp['discount_strategy']}")

    # Objection handling
    st.markdown("### 🛡️ Objection Handling")

    for objection, response in selected_vp.get('objection_responses', {}).items():
        with st.expander(f"**Objection**: {objection}"):
            st.markdown(response)

    # Next steps
    st.markdown("### ✅ Recommended Next Steps")
    for step in selected_vp.get('recommended_next_steps', []):
        st.markdown(f"- {step}")

    # Urgency factors
    st.markdown("### ⚡ Urgency Factors")
    for factor in selected_vp.get('urgency_factors', []):
        st.markdown(f"- {factor}")

    # Export button
    if st.button("📄 Export Value Proposition", type="primary"):
        # In production, would generate PDF/DOCX
        st.success("Value proposition exported! (Feature coming soon)")


# Main entry point
if __name__ == "__main__":
    st.set_page_config(
        page_title="Client Expansion Intelligence",
        page_icon="💰",
        layout="wide"
    )

    render_client_expansion_dashboard()
