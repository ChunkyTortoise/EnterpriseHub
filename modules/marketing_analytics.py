"""
Marketing Analytics Hub - Comprehensive Marketing Performance Tracking.

Track campaigns across channels, calculate ROI, analyze customer metrics,
and optimize marketing spend with data-driven insights.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from scipy import stats
import io
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_CONFIDENCE_LEVEL = 0.95
MIN_SAMPLE_SIZE = 30
ATTRIBUTION_MODELS = ["First-Touch", "Last-Touch", "Linear", "Time-Decay", "Position-Based"]


def render() -> None:
    """Main render function for Marketing Analytics Hub."""
    st.markdown("### 📊 Marketing Analytics Hub")
    st.markdown("""
    Track campaign performance, calculate ROI, analyze customer metrics, and optimize
    your marketing spend across all channels.
    """)

    # Initialize session state
    if 'campaign_data' not in st.session_state:
        st.session_state.campaign_data = _get_sample_campaign_data()

    # Create tabs for different analytics sections
    tabs = st.tabs([
        "📈 Campaign Dashboard",
        "💰 ROI Calculator",
        "👥 Customer Metrics",
        "🧪 A/B Testing",
        "🎯 Attribution",
        "📥 Reports"
    ])

    with tabs[0]:
        _render_campaign_dashboard()

    with tabs[1]:
        _render_roi_calculator()

    with tabs[2]:
        _render_customer_metrics()

    with tabs[3]:
        _render_ab_testing()

    with tabs[4]:
        _render_attribution_modeling()

    with tabs[5]:
        _render_reports()


def _render_campaign_dashboard() -> None:
    """Render multi-channel campaign performance dashboard."""
    st.markdown("### 📈 Campaign Performance Dashboard")

    # Channel selector
    channels = ["All Channels", "Social Media", "Email", "Paid Ads", "Organic", "Content"]
    selected_channel = st.selectbox("Select Channel", channels)

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now()
        )

    st.markdown("---")

    # Key Metrics
    st.markdown("#### 📊 Key Performance Indicators")

    # Generate sample metrics based on channel
    metrics = _calculate_channel_metrics(selected_channel)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Total Spend",
            f"${metrics['spend']:,.0f}",
            delta=f"{metrics['spend_change']:+.1f}%"
        )
    with col2:
        st.metric(
            "Revenue",
            f"${metrics['revenue']:,.0f}",
            delta=f"{metrics['revenue_change']:+.1f}%"
        )
    with col3:
        st.metric(
            "ROI",
            f"{metrics['roi']:.2f}x",
            delta=f"{metrics['roi_change']:+.1f}%"
        )
    with col4:
        st.metric(
            "Conversions",
            f"{metrics['conversions']:,}",
            delta=f"{metrics['conversion_change']:+.1f}%"
        )

    st.markdown("---")

    # Performance visualizations
    st.markdown("#### 📉 Performance Trends")

    # Generate time series data
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    trend_data = _generate_trend_data(dates, selected_channel)

    col1, col2 = st.columns(2)

    with col1:
        # Spend vs Revenue chart
        fig_spend_revenue = go.Figure()
        fig_spend_revenue.add_trace(go.Scatter(
            x=trend_data['date'],
            y=trend_data['spend'],
            name='Spend',
            mode='lines',
            line=dict(color='red', width=2)
        ))
        fig_spend_revenue.add_trace(go.Scatter(
            x=trend_data['date'],
            y=trend_data['revenue'],
            name='Revenue',
            mode='lines',
            line=dict(color='green', width=2)
        ))
        fig_spend_revenue.update_layout(
            title="Spend vs Revenue Over Time",
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            hovermode='x unified'
        )
        st.plotly_chart(fig_spend_revenue, use_container_width=True)

    with col2:
        # Conversion rate chart
        fig_conversion = go.Figure()
        fig_conversion.add_trace(go.Scatter(
            x=trend_data['date'],
            y=trend_data['conversion_rate'],
            name='Conversion Rate',
            mode='lines+markers',
            line=dict(color='blue', width=2),
            fill='tozeroy'
        ))
        fig_conversion.update_layout(
            title="Conversion Rate Trend",
            xaxis_title="Date",
            yaxis_title="Conversion Rate (%)",
            hovermode='x unified'
        )
        st.plotly_chart(fig_conversion, use_container_width=True)

    # Channel breakdown
    st.markdown("#### 📊 Channel Performance Breakdown")

    if selected_channel == "All Channels":
        channel_breakdown = _get_channel_breakdown()

        fig_channels = go.Figure(data=[
            go.Bar(
                name='Spend',
                x=channel_breakdown['channel'],
                y=channel_breakdown['spend'],
                marker_color='lightcoral'
            ),
            go.Bar(
                name='Revenue',
                x=channel_breakdown['channel'],
                y=channel_breakdown['revenue'],
                marker_color='lightgreen'
            )
        ])
        fig_channels.update_layout(
            title="Spend vs Revenue by Channel",
            xaxis_title="Channel",
            yaxis_title="Amount ($)",
            barmode='group'
        )
        st.plotly_chart(fig_channels, use_container_width=True)

        # Channel efficiency table
        st.markdown("**Channel Efficiency Metrics**")
        efficiency_df = channel_breakdown.copy()
        efficiency_df['ROI'] = (efficiency_df['revenue'] / efficiency_df['spend']).round(2)
        efficiency_df['CPA'] = (efficiency_df['spend'] / efficiency_df['conversions']).round(2)
        efficiency_df = efficiency_df[['channel', 'spend', 'revenue', 'conversions', 'ROI', 'CPA']]
        efficiency_df.columns = ['Channel', 'Spend ($)', 'Revenue ($)', 'Conversions', 'ROI', 'CPA ($)']
        st.dataframe(efficiency_df, use_container_width=True)


def _render_roi_calculator() -> None:
    """Render campaign ROI calculator."""
    st.markdown("### 💰 Campaign ROI Calculator")
    st.markdown("Calculate return on investment for your marketing campaigns")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📥 Campaign Inputs")

        campaign_spend = st.number_input(
            "Campaign Spend ($)",
            min_value=0.0,
            value=5000.0,
            step=100.0,
            help="Total amount spent on the campaign"
        )

        revenue_generated = st.number_input(
            "Revenue Generated ($)",
            min_value=0.0,
            value=15000.0,
            step=100.0,
            help="Total revenue attributed to the campaign"
        )

        customers_acquired = st.number_input(
            "Customers Acquired",
            min_value=0,
            value=50,
            step=1,
            help="Number of new customers from the campaign"
        )

        avg_order_value = st.number_input(
            "Average Order Value ($)",
            min_value=0.0,
            value=300.0,
            step=10.0,
            help="Average purchase value per customer"
        )

    with col2:
        st.markdown("#### 📊 ROI Metrics")

        # Calculate metrics
        roi = ((revenue_generated - campaign_spend) / campaign_spend) * 100 if campaign_spend > 0 else 0
        roas = revenue_generated / campaign_spend if campaign_spend > 0 else 0
        cpa = campaign_spend / customers_acquired if customers_acquired > 0 else 0
        profit = revenue_generated - campaign_spend

        # Display metrics
        st.metric("ROI", f"{roi:.1f}%", help="Return on Investment")
        st.metric("ROAS", f"{roas:.2f}x", help="Return on Ad Spend")
        st.metric("CPA", f"${cpa:.2f}", help="Cost Per Acquisition")
        st.metric("Profit", f"${profit:,.2f}", delta=f"{roi:.1f}% return")

        # Visual ROI indicator
        if roi > 0:
            st.success(f"✅ Profitable campaign with {roi:.1f}% ROI")
        elif roi == 0:
            st.warning("⚠️ Break-even campaign (0% ROI)")
        else:
            st.error(f"❌ Unprofitable campaign ({roi:.1f}% loss)")

    st.markdown("---")

    # ROI Scenario Analysis
    st.markdown("#### 🎯 Scenario Analysis")
    st.markdown("Explore how changes in conversion rate or AOV affect ROI")

    col1, col2 = st.columns(2)

    with col1:
        conversion_range = st.slider(
            "Conversion Rate Range (%)",
            min_value=0.5,
            max_value=10.0,
            value=(2.0, 8.0),
            step=0.5
        )

    with col2:
        aov_range = st.slider(
            "AOV Range ($)",
            min_value=100,
            max_value=1000,
            value=(200, 500),
            step=50
        )

    # Generate scenario heatmap
    conversion_rates = np.linspace(conversion_range[0], conversion_range[1], 10)
    aov_values = np.linspace(aov_range[0], aov_range[1], 10)

    roi_matrix = np.zeros((len(conversion_rates), len(aov_values)))

    for i, conv_rate in enumerate(conversion_rates):
        for j, aov in enumerate(aov_values):
            # Assume 1000 visitors as base
            visitors = 1000
            conversions = visitors * (conv_rate / 100)
            revenue = conversions * aov
            roi_value = ((revenue - campaign_spend) / campaign_spend) * 100
            roi_matrix[i, j] = roi_value

    fig_heatmap = go.Figure(data=go.Heatmap(
        z=roi_matrix,
        x=[f"${int(aov)}" for aov in aov_values],
        y=[f"{conv_rate:.1f}%" for conv_rate in conversion_rates],
        colorscale='RdYlGn',
        text=roi_matrix.round(1),
        texttemplate='%{text}%',
        textfont={"size": 10},
        colorbar=dict(title="ROI %")
    ))

    fig_heatmap.update_layout(
        title="ROI Scenario Matrix: Conversion Rate × Average Order Value",
        xaxis_title="Average Order Value",
        yaxis_title="Conversion Rate",
        height=400
    )

    st.plotly_chart(fig_heatmap, use_container_width=True)


def _render_customer_metrics() -> None:
    """Render customer acquisition and lifetime value metrics."""
    st.markdown("### 👥 Customer Metrics")

    # CAC Calculator
    st.markdown("#### 💵 Customer Acquisition Cost (CAC)")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_marketing_spend = st.number_input(
            "Total Marketing Spend ($)",
            min_value=0.0,
            value=10000.0,
            step=500.0
        )

    with col2:
        total_sales_costs = st.number_input(
            "Total Sales Costs ($)",
            min_value=0.0,
            value=5000.0,
            step=500.0
        )

    with col3:
        new_customers = st.number_input(
            "New Customers Acquired",
            min_value=1,
            value=100,
            step=5
        )

    cac = (total_marketing_spend + total_sales_costs) / new_customers

    st.metric("Customer Acquisition Cost (CAC)", f"${cac:.2f}")

    st.markdown("---")

    # CLV Calculator
    st.markdown("#### 💎 Customer Lifetime Value (CLV)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**CLV Inputs**")

        avg_purchase_value = st.number_input(
            "Average Purchase Value ($)",
            min_value=0.0,
            value=100.0,
            step=5.0
        )

        purchase_frequency = st.number_input(
            "Purchase Frequency (per year)",
            min_value=0.0,
            value=4.0,
            step=0.5,
            help="Average number of purchases per customer per year"
        )

        customer_lifespan = st.number_input(
            "Customer Lifespan (years)",
            min_value=0.0,
            value=3.0,
            step=0.5,
            help="Average number of years a customer stays active"
        )

        profit_margin = st.slider(
            "Profit Margin (%)",
            min_value=0,
            max_value=100,
            value=30,
            help="Average profit margin on sales"
        ) / 100

    with col2:
        st.markdown("**CLV Metrics**")

        # Calculate CLV
        customer_value = avg_purchase_value * purchase_frequency
        clv = customer_value * customer_lifespan * profit_margin

        st.metric("Customer Lifetime Value (CLV)", f"${clv:.2f}")
        st.metric("Annual Customer Value", f"${customer_value:.2f}")

        # CLV to CAC ratio
        clv_cac_ratio = clv / cac if cac > 0 else 0

        st.metric("CLV:CAC Ratio", f"{clv_cac_ratio:.2f}x")

        # Interpretation
        if clv_cac_ratio >= 3:
            st.success("✅ Healthy ratio (≥3:1) - Sustainable growth")
        elif clv_cac_ratio >= 1:
            st.warning("⚠️ Acceptable ratio (1-3:1) - Room for improvement")
        else:
            st.error("❌ Poor ratio (<1:1) - Losing money on customers")

    st.markdown("---")

    # Cohort Analysis Visualization
    st.markdown("#### 📊 Customer Cohort Analysis")

    cohort_data = _generate_cohort_data()

    fig_cohort = go.Figure(data=go.Heatmap(
        z=cohort_data.values,
        x=cohort_data.columns,
        y=cohort_data.index,
        colorscale='Blues',
        text=cohort_data.values,
        texttemplate='%{text}%',
        textfont={"size": 10},
        colorbar=dict(title="Retention %")
    ))

    fig_cohort.update_layout(
        title="Customer Retention by Cohort",
        xaxis_title="Months Since First Purchase",
        yaxis_title="Cohort Month",
        height=400
    )

    st.plotly_chart(fig_cohort, use_container_width=True)


def _render_ab_testing() -> None:
    """Render A/B/n test significance calculator."""
    st.markdown("### 🧪 Statistical Testing Calculator")
    st.markdown("Determine if your test results are statistically significant")

    # Test mode selector
    test_mode = st.radio(
        "Select Test Type",
        ["A/B Testing (2 variants)", "Multi-Variant Testing (3-10 variants)"],
        horizontal=True
    )

    st.markdown("---")

    if test_mode == "A/B Testing (2 variants)":
        _render_ab_test()
    else:
        _render_multivariant_test()


def _render_ab_test() -> None:
    """Render standard A/B test (2 variants)."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🅰️ Variant A (Control)")

        visitors_a = st.number_input(
            "Visitors A",
            min_value=0,
            value=1000,
            step=50,
            key="visitors_a"
        )

        conversions_a = st.number_input(
            "Conversions A",
            min_value=0,
            value=50,
            step=5,
            key="conversions_a"
        )

        conversion_rate_a = (conversions_a / visitors_a * 100) if visitors_a > 0 else 0

        st.metric("Conversion Rate A", f"{conversion_rate_a:.2f}%")

    with col2:
        st.markdown("#### 🅱️ Variant B (Test)")

        visitors_b = st.number_input(
            "Visitors B",
            min_value=0,
            value=1000,
            step=50,
            key="visitors_b"
        )

        conversions_b = st.number_input(
            "Conversions B",
            min_value=0,
            value=65,
            step=5,
            key="conversions_b"
        )

        conversion_rate_b = (conversions_b / visitors_b * 100) if visitors_b > 0 else 0

        st.metric("Conversion Rate B", f"{conversion_rate_b:.2f}%")

    st.markdown("---")

    # Calculate statistical significance
    if visitors_a >= MIN_SAMPLE_SIZE and visitors_b >= MIN_SAMPLE_SIZE:
        result = _calculate_ab_test_significance(
            visitors_a, conversions_a,
            visitors_b, conversions_b
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            lift = result['lift']
            st.metric(
                "Lift",
                f"{lift:+.2f}%",
                delta=f"{'Improvement' if lift > 0 else 'Decline'}"
            )

        with col2:
            st.metric("P-Value", f"{result['p_value']:.4f}")

        with col3:
            confidence = (1 - result['p_value']) * 100
            st.metric("Confidence", f"{confidence:.1f}%")

        # Interpretation
        st.markdown("#### 📊 Test Results")

        if result['significant']:
            if lift > 0:
                st.success(f"✅ **Statistically Significant Winner!** Variant B is {abs(lift):.2f}% better than A with {confidence:.1f}% confidence.")
            else:
                st.error(f"❌ **Statistically Significant Loss!** Variant B is {abs(lift):.2f}% worse than A with {confidence:.1f}% confidence.")
        else:
            st.warning(f"⚠️ **Not Statistically Significant** - Need more data. Current difference: {lift:+.2f}%")

        # Visual comparison
        fig_ab = go.Figure(data=[
            go.Bar(
                name='Variant A',
                x=['Conversion Rate'],
                y=[conversion_rate_a],
                marker_color='lightblue',
                text=[f"{conversion_rate_a:.2f}%"],
                textposition='auto'
            ),
            go.Bar(
                name='Variant B',
                x=['Conversion Rate'],
                y=[conversion_rate_b],
                marker_color='lightgreen' if lift > 0 else 'lightcoral',
                text=[f"{conversion_rate_b:.2f}%"],
                textposition='auto'
            )
        ])

        fig_ab.update_layout(
            title="A/B Test Comparison",
            yaxis_title="Conversion Rate (%)",
            barmode='group',
            showlegend=True
        )

        st.plotly_chart(fig_ab, use_container_width=True)

        # Sample size recommendation
        st.markdown("#### 💡 Sample Size Recommendation")

        recommended_sample = _calculate_required_sample_size(
            conversion_rate_a / 100,
            abs(lift) / 100,
            DEFAULT_CONFIDENCE_LEVEL
        )

        if visitors_a < recommended_sample or visitors_b < recommended_sample:
            st.info(f"📊 For {DEFAULT_CONFIDENCE_LEVEL*100:.0f}% confidence with this lift, you need approximately **{recommended_sample:,} visitors per variant**. Current: A={visitors_a:,}, B={visitors_b:,}")
        else:
            st.success(f"✅ Sample size is sufficient for {DEFAULT_CONFIDENCE_LEVEL*100:.0f}% confidence level")

    else:
        st.warning(f"⚠️ Need at least {MIN_SAMPLE_SIZE} visitors per variant for statistical analysis")


def _render_multivariant_test() -> None:
    """Render multi-variant test (3-10 variants) using Chi-square test."""
    st.markdown("#### 🔢 Multi-Variant Testing (Chi-Square Test)")
    st.markdown("Test multiple variants simultaneously to find the best performer")

    # Number of variants
    num_variants = st.slider("Number of Variants", min_value=3, max_value=10, value=3)

    # Collect data for each variant
    variant_data = []
    variant_names = ['A (Control)', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']

    st.markdown("#### 📊 Enter Data for Each Variant")

    cols = st.columns(min(num_variants, 3))  # Max 3 columns for layout

    for i in range(num_variants):
        col_idx = i % 3
        with cols[col_idx]:
            st.markdown(f"**Variant {variant_names[i]}**")

            visitors = st.number_input(
                f"Visitors {variant_names[i]}",
                min_value=0,
                value=1000,
                step=50,
                key=f"mv_visitors_{i}",
                label_visibility="collapsed"
            )

            conversions = st.number_input(
                f"Conversions {variant_names[i]}",
                min_value=0,
                value=50 + (i * 5),  # Slightly different default for each
                step=5,
                key=f"mv_conversions_{i}",
                label_visibility="collapsed"
            )

            conv_rate = (conversions / visitors * 100) if visitors > 0 else 0
            st.metric("Conv. Rate", f"{conv_rate:.2f}%")

            variant_data.append({
                'name': variant_names[i],
                'visitors': visitors,
                'conversions': conversions,
                'conv_rate': conv_rate
            })

    st.markdown("---")

    # Check minimum sample size
    all_sufficient = all(v['visitors'] >= MIN_SAMPLE_SIZE for v in variant_data)

    if all_sufficient:
        # Calculate Chi-square test
        result = _calculate_multivariant_significance(variant_data)

        # Display results
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Chi-Square Statistic", f"{result['chi_square']:.2f}")

        with col2:
            st.metric("P-Value", f"{result['p_value']:.4f}")

        with col3:
            confidence = (1 - result['p_value']) * 100
            st.metric("Confidence", f"{confidence:.1f}%")

        # Interpretation
        st.markdown("#### 📊 Test Results")

        if result['significant']:
            st.success(f"✅ **Statistically Significant Difference Detected!** At least one variant performs differently from the others with {confidence:.1f}% confidence.")

            # Show best performer
            best_variant = result['best_variant']
            st.info(f"🏆 **Best Performer**: Variant **{best_variant['name']}** with **{best_variant['conv_rate']:.2f}%** conversion rate")

            # Pairwise comparisons with best
            st.markdown("**Comparison to Best Performer:**")
            comparison_data = []
            for v in variant_data:
                if v['name'] != best_variant['name']:
                    lift = ((v['conv_rate'] - best_variant['conv_rate']) / best_variant['conv_rate'] * 100) if best_variant['conv_rate'] > 0 else 0
                    comparison_data.append({
                        'Variant': v['name'],
                        'Conv. Rate': f"{v['conv_rate']:.2f}%",
                        'Lift vs Best': f"{lift:+.1f}%"
                    })

            if comparison_data:
                comp_df = pd.DataFrame(comparison_data)
                st.dataframe(comp_df, use_container_width=True)

        else:
            st.warning(f"⚠️ **No Significant Difference** - All variants perform similarly. Current p-value: {result['p_value']:.4f}")

        # Visualization
        st.markdown("#### 📈 Conversion Rate Comparison")

        # Create bar chart
        fig_mv = go.Figure(data=[
            go.Bar(
                x=[v['name'] for v in variant_data],
                y=[v['conv_rate'] for v in variant_data],
                text=[f"{v['conv_rate']:.2f}%" for v in variant_data],
                textposition='auto',
                marker_color=['gold' if v['name'] == result['best_variant']['name'] else 'lightblue' for v in variant_data]
            )
        ])

        fig_mv.update_layout(
            title="Conversion Rates Across All Variants",
            xaxis_title="Variant",
            yaxis_title="Conversion Rate (%)",
            showlegend=False
        )

        st.plotly_chart(fig_mv, use_container_width=True)

        # Summary table
        st.markdown("#### 📋 Summary Table")
        summary_data = pd.DataFrame([{
            'Variant': v['name'],
            'Visitors': f"{v['visitors']:,}",
            'Conversions': f"{v['conversions']:,}",
            'Conv. Rate': f"{v['conv_rate']:.2f}%"
        } for v in variant_data])
        st.dataframe(summary_data, use_container_width=True)

    else:
        st.warning(f"⚠️ Need at least {MIN_SAMPLE_SIZE} visitors per variant for statistical analysis")
        insufficient = [v['name'] for v in variant_data if v['visitors'] < MIN_SAMPLE_SIZE]
        st.info(f"Insufficient data for: {', '.join(insufficient)}")


def _calculate_multivariant_significance(variant_data: List[Dict]) -> Dict:
    """Calculate Chi-square test for multiple variants."""
    # Create contingency table
    conversions = [v['conversions'] for v in variant_data]
    non_conversions = [v['visitors'] - v['conversions'] for v in variant_data]

    # Contingency table: rows = [conversions, non-conversions], cols = variants
    contingency_table = np.array([conversions, non_conversions])

    # Perform Chi-square test
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

    # Find best performer
    best_variant = max(variant_data, key=lambda x: x['conv_rate'])

    return {
        'chi_square': chi2,
        'p_value': p_value,
        'degrees_of_freedom': dof,
        'significant': p_value < 0.05,
        'best_variant': best_variant
    }


def _render_attribution_modeling() -> None:
    """Render marketing attribution analysis."""
    st.markdown("### 🎯 Marketing Attribution Modeling")
    st.markdown("Understand which touchpoints drive conversions")

    # Attribution model selector
    model = st.selectbox(
        "Select Attribution Model",
        ATTRIBUTION_MODELS,
        help="Different methods to credit touchpoints in the customer journey"
    )

    st.markdown("---")

    # Sample customer journey data
    st.markdown("#### 🛤️ Customer Journey Example")

    journey_data = _get_sample_journey_data()

    st.dataframe(journey_data, use_container_width=True)

    st.markdown("---")

    # Attribution calculation
    st.markdown(f"#### 📊 Attribution Results - {model} Model")

    attribution_results = _calculate_attribution(journey_data, model)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Attribution chart
        fig_attribution = px.bar(
            attribution_results,
            x='channel',
            y='credit',
            title=f"Conversion Credit by Channel - {model}",
            labels={'channel': 'Channel', 'credit': 'Conversion Credit'},
            color='credit',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_attribution, use_container_width=True)

    with col2:
        # Attribution table
        st.markdown("**Attribution Breakdown**")
        results_df = attribution_results.copy()
        results_df['credit'] = results_df['credit'].round(2)
        results_df['percentage'] = (results_df['credit'] / results_df['credit'].sum() * 100).round(1)
        results_df.columns = ['Channel', 'Credit', 'Share (%)']
        st.dataframe(results_df, use_container_width=True)

    # Model explanation
    st.markdown("#### 💡 Model Explanation")

    explanations = {
        "First-Touch": "100% credit to the first touchpoint in the customer journey",
        "Last-Touch": "100% credit to the last touchpoint before conversion",
        "Linear": "Equal credit distributed across all touchpoints",
        "Time-Decay": "More credit to recent touchpoints, less to earlier ones",
        "Position-Based": "40% to first touch, 40% to last touch, 20% distributed evenly among middle touchpoints (U-shaped)"
    }

    st.info(f"**{model}**: {explanations[model]}")


def _render_reports() -> None:
    """Render marketing reports export section."""
    st.markdown("### 📥 Marketing Reports")

    # Report type selector
    report_type = st.selectbox(
        "Select Report Type",
        ["Campaign Performance", "Customer Metrics", "A/B Test Results", "Attribution Analysis"]
    )

    # Date range for report
    col1, col2 = st.columns(2)
    with col1:
        report_start = st.date_input("Report Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        report_end = st.date_input("Report End Date", value=datetime.now())

    st.markdown("---")

    # Generate report preview
    st.markdown("#### 📊 Report Preview")

    report_data = _generate_report_data(report_type, report_start, report_end)

    st.dataframe(report_data, use_container_width=True)

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📄 Export as CSV")

        csv_buffer = io.StringIO()
        report_data.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=f"{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    with col2:
        st.markdown("#### 📊 Export as Excel")

        excel_buffer = io.BytesIO()
        report_data.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="⬇️ Download Excel",
            data=excel_data,
            file_name=f"{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# Helper functions

def _get_sample_campaign_data() -> pd.DataFrame:
    """Generate sample campaign data for demonstration."""
    return pd.DataFrame({
        'campaign': ['Summer Sale', 'Holiday Promo', 'New Product', 'Retargeting'],
        'channel': ['Social Media', 'Email', 'Paid Ads', 'Paid Ads'],
        'spend': [5000, 3000, 8000, 2000],
        'impressions': [50000, 25000, 100000, 15000],
        'clicks': [2500, 1500, 5000, 900],
        'conversions': [125, 90, 200, 50],
        'revenue': [15000, 12000, 30000, 7500]
    })


def _calculate_channel_metrics(channel: str) -> Dict:
    """Calculate metrics for selected channel."""
    # Sample data - in production, this would query real data
    base_spend = 10000 if channel == "All Channels" else 5000
    base_revenue = 25000 if channel == "All Channels" else 12000

    return {
        'spend': base_spend * np.random.uniform(0.9, 1.1),
        'revenue': base_revenue * np.random.uniform(0.9, 1.1),
        'roi': (base_revenue / base_spend) * np.random.uniform(0.95, 1.05),
        'conversions': int(150 * np.random.uniform(0.9, 1.1)),
        'spend_change': np.random.uniform(-10, 20),
        'revenue_change': np.random.uniform(-5, 25),
        'roi_change': np.random.uniform(-8, 15),
        'conversion_change': np.random.uniform(-12, 18)
    }


def _generate_trend_data(dates: pd.DatetimeIndex, channel: str) -> pd.DataFrame:
    """Generate sample trend data."""
    n_days = len(dates)

    # Add some seasonality and trend
    trend = np.linspace(1000, 1500, n_days)
    seasonality = 200 * np.sin(np.linspace(0, 4 * np.pi, n_days))
    noise = np.random.normal(0, 100, n_days)

    spend = trend + seasonality + noise
    revenue = spend * np.random.uniform(2.0, 3.0, n_days)
    conversion_rate = np.random.uniform(2, 5, n_days)

    return pd.DataFrame({
        'date': dates,
        'spend': np.maximum(spend, 0),
        'revenue': np.maximum(revenue, 0),
        'conversion_rate': conversion_rate
    })


def _get_channel_breakdown() -> pd.DataFrame:
    """Get performance breakdown by channel."""
    return pd.DataFrame({
        'channel': ['Social Media', 'Email', 'Paid Ads', 'Organic', 'Content'],
        'spend': [5000, 2000, 8000, 1000, 3000],
        'revenue': [12000, 8000, 20000, 5000, 9000],
        'conversions': [120, 160, 200, 100, 90]
    })


def _calculate_ab_test_significance(
    visitors_a: int, conversions_a: int,
    visitors_b: int, conversions_b: int,
    confidence: float = DEFAULT_CONFIDENCE_LEVEL
) -> Dict:
    """Calculate A/B test statistical significance."""
    # Calculate conversion rates
    rate_a = conversions_a / visitors_a if visitors_a > 0 else 0
    rate_b = conversions_b / visitors_b if visitors_b > 0 else 0

    # Calculate lift
    lift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0

    # Calculate standard error
    se_a = np.sqrt(rate_a * (1 - rate_a) / visitors_a) if visitors_a > 0 else 0
    se_b = np.sqrt(rate_b * (1 - rate_b) / visitors_b) if visitors_b > 0 else 0
    se_diff = np.sqrt(se_a**2 + se_b**2)

    # Calculate z-score and p-value
    z_score = (rate_b - rate_a) / se_diff if se_diff > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # Two-tailed test

    # Determine significance
    significant = p_value < (1 - confidence)

    return {
        'lift': lift,
        'p_value': p_value,
        'z_score': z_score,
        'significant': significant
    }


def _calculate_required_sample_size(
    baseline_rate: float,
    mde: float,  # Minimum detectable effect
    confidence: float = DEFAULT_CONFIDENCE_LEVEL,
    power: float = 0.8
) -> int:
    """Calculate required sample size for A/B test."""
    # Z-scores for confidence and power
    z_alpha = stats.norm.ppf(1 - (1 - confidence) / 2)
    z_beta = stats.norm.ppf(power)

    # Calculate sample size
    p1 = baseline_rate
    p2 = baseline_rate + mde

    pooled_p = (p1 + p2) / 2

    numerator = (z_alpha * np.sqrt(2 * pooled_p * (1 - pooled_p)) +
                 z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))**2
    denominator = (p2 - p1)**2

    sample_size = int(np.ceil(numerator / denominator))

    return max(sample_size, MIN_SAMPLE_SIZE)


def _generate_cohort_data() -> pd.DataFrame:
    """Generate sample cohort retention data."""
    cohorts = ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024', 'May 2024']
    months = ['Month 0', 'Month 1', 'Month 2', 'Month 3', 'Month 4']

    data = []
    for i, cohort in enumerate(cohorts):
        row = [100]  # Month 0 is always 100%
        retention = 100
        for j in range(1, 5 - i):
            retention *= np.random.uniform(0.70, 0.85)  # Decay rate
            row.append(round(retention, 1))

        # Fill remaining with NaN
        row.extend([np.nan] * i)
        data.append(row)

    df = pd.DataFrame(data, columns=months, index=cohorts)
    return df


def _get_sample_journey_data() -> pd.DataFrame:
    """Get sample customer journey data."""
    return pd.DataFrame({
        'Customer': ['Customer 1'] * 5,
        'Step': [1, 2, 3, 4, 5],
        'Touchpoint': ['Social Media Ad', 'Website Visit', 'Email', 'Retargeting Ad', 'Direct'],
        'Channel': ['Social Media', 'Organic', 'Email', 'Paid Ads', 'Direct'],
        'Days Since First Touch': [0, 2, 5, 7, 10],
        'Converted': [False, False, False, False, True]
    })


def _calculate_attribution(journey_df: pd.DataFrame, model: str) -> pd.DataFrame:
    """Calculate attribution credit for each channel."""
    channels = journey_df['Channel'].unique()

    if model == "First-Touch":
        # 100% credit to first touchpoint
        first_channel = journey_df.iloc[0]['Channel']
        credits = {ch: (1.0 if ch == first_channel else 0.0) for ch in channels}

    elif model == "Last-Touch":
        # 100% credit to last touchpoint
        last_channel = journey_df.iloc[-1]['Channel']
        credits = {ch: (1.0 if ch == last_channel else 0.0) for ch in channels}

    elif model == "Linear":
        # Equal credit across all touchpoints
        n_touches = len(journey_df)
        credit_per_touch = 1.0 / n_touches
        credits = journey_df['Channel'].value_counts().to_dict()
        credits = {ch: count * credit_per_touch for ch, count in credits.items()}

    elif model == "Time-Decay":
        # More credit to recent touchpoints
        n_touches = len(journey_df)
        decay_weights = np.array([2**i for i in range(n_touches)])
        decay_weights = decay_weights / decay_weights.sum()

        credits = {}
        for idx, row in journey_df.iterrows():
            ch = row['Channel']
            credits[ch] = credits.get(ch, 0) + decay_weights[idx]

    elif model == "Position-Based":
        # U-shaped: 40% first, 40% last, 20% distributed among middle
        n_touches = len(journey_df)
        credits = {}

        if n_touches == 1:
            # Only one touchpoint gets 100%
            ch = journey_df.iloc[0]['Channel']
            credits[ch] = 1.0
        elif n_touches == 2:
            # Two touchpoints: 50% each
            first_ch = journey_df.iloc[0]['Channel']
            last_ch = journey_df.iloc[-1]['Channel']
            credits[first_ch] = credits.get(first_ch, 0) + 0.5
            credits[last_ch] = credits.get(last_ch, 0) + 0.5
        else:
            # Three or more touchpoints: 40-20-40 distribution
            first_ch = journey_df.iloc[0]['Channel']
            last_ch = journey_df.iloc[-1]['Channel']
            middle_touches = n_touches - 2
            middle_credit = 0.20 / middle_touches if middle_touches > 0 else 0

            # First touchpoint: 40%
            credits[first_ch] = credits.get(first_ch, 0) + 0.40

            # Last touchpoint: 40%
            credits[last_ch] = credits.get(last_ch, 0) + 0.40

            # Middle touchpoints: 20% distributed evenly
            for idx in range(1, n_touches - 1):
                ch = journey_df.iloc[idx]['Channel']
                credits[ch] = credits.get(ch, 0) + middle_credit

    # Convert to DataFrame
    result_df = pd.DataFrame(list(credits.items()), columns=['channel', 'credit'])
    result_df = result_df.sort_values('credit', ascending=False).reset_index(drop=True)

    return result_df


def _generate_report_data(report_type: str, start_date, end_date) -> pd.DataFrame:
    """Generate sample report data."""
    if report_type == "Campaign Performance":
        return _get_sample_campaign_data()
    elif report_type == "Customer Metrics":
        return pd.DataFrame({
            'Metric': ['CAC', 'CLV', 'CLV:CAC Ratio', 'Avg Order Value', 'Purchase Frequency'],
            'Value': ['$50.00', '$450.00', '9.0x', '$100.00', '4.5/year']
        })
    elif report_type == "A/B Test Results":
        return pd.DataFrame({
            'Variant': ['A (Control)', 'B (Test)'],
            'Visitors': [1000, 1000],
            'Conversions': [50, 65],
            'Conversion Rate': ['5.0%', '6.5%'],
            'Lift': ['-', '+30%'],
            'Significant': ['-', 'Yes']
        })
    else:  # Attribution Analysis
        return pd.DataFrame({
            'Channel': ['Social Media', 'Email', 'Paid Ads', 'Organic', 'Direct'],
            'First-Touch': [0.20, 0.30, 0.25, 0.15, 0.10],
            'Last-Touch': [0.10, 0.15, 0.35, 0.20, 0.20],
            'Linear': [0.20, 0.20, 0.20, 0.20, 0.20],
            'Time-Decay': [0.12, 0.18, 0.28, 0.22, 0.20]
        })
