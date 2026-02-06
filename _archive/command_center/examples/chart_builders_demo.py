"""
Jorge's Chart Builders Demo

Comprehensive demonstration of the chart builders utility with:
- Real-world data examples
- Interactive dashboard scenarios
- ML model performance visualization
- Real estate analytics showcase
- Export functionality demonstration

Run this script to see the chart builders in action and generate
sample visualizations for testing and validation.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from command_center.utils.chart_builders import (
    ChartFactory,
    JorgeTheme,
    quick_roc_curve,
    quick_lead_analysis,
    quick_kpi_card
)


def generate_sample_data():
    """Generate realistic sample data for demonstrations."""
    np.random.seed(42)
    
    # ML Performance Data
    ml_data = {
        'y_true': np.random.choice([0, 1], size=1000, p=[0.7, 0.3]),
        'y_scores_model_1': np.random.beta(2, 5, size=1000),
        'y_scores_model_2': np.random.beta(3, 4, size=1000),
        'feature_names': [
            'Credit_Score', 'Income', 'Age', 'Property_Value', 'Down_Payment_Percent',
            'Debt_to_Income', 'Employment_Length', 'Previous_Properties', 'Location_Score',
            'Market_Conditions', 'Interest_Rate_Sensitivity', 'Mortgage_Type_Preference'
        ],
        'feature_importance': np.array([0.15, 0.12, 0.08, 0.14, 0.11, 0.09, 0.07, 0.06, 0.08, 0.05, 0.03, 0.02])
    }
    
    # Lead Data with realistic real estate patterns
    dates = pd.date_range('2024-01-01', periods=500, freq='D')
    lead_data = pd.DataFrame({
        'lead_id': range(500),
        'score': np.random.beta(2, 5, size=500) * 100,
        'converted': np.random.choice([0, 1], size=500, p=[0.85, 0.15]),  # 15% conversion rate
        'source': np.random.choice(
            ['Website_Organic', 'Google_Ads', 'Facebook_Ads', 'Referrals', 'Zillow', 'Realtor.com'], 
            size=500, 
            p=[0.25, 0.20, 0.15, 0.20, 0.10, 0.10]
        ),
        'date': np.random.choice(dates, size=500),
        'estimated_value': np.random.normal(450000, 150000, size=500),  # Property values
        'budget_max': np.random.normal(500000, 200000, size=500),  # Lead budgets
        'bedrooms': np.random.choice([2, 3, 4, 5], size=500, p=[0.15, 0.40, 0.35, 0.10]),
        'location_preference': np.random.choice(
            ['Downtown', 'Suburbs', 'Waterfront', 'Mountain', 'Rural'], 
            size=500, 
            p=[0.30, 0.35, 0.15, 0.10, 0.10]
        )
    })
    
    # Market Trends Data
    market_dates = pd.date_range('2023-01-01', '2024-12-31', freq='M')
    market_data = pd.DataFrame({
        'date': market_dates,
        'avg_price': 400000 + np.cumsum(np.random.normal(2000, 5000, size=len(market_dates))),  # Trending upward
        'price_per_sqft': 180 + np.cumsum(np.random.normal(1, 3, size=len(market_dates))),
        'active_listings': np.random.poisson(450, size=len(market_dates)) + 50 * np.sin(np.arange(len(market_dates)) * 2 * np.pi / 12),  # Seasonal
        'avg_dom': 25 + 10 * np.sin(np.arange(len(market_dates)) * 2 * np.pi / 12) + np.random.normal(0, 3, size=len(market_dates)),  # Seasonal
        'sales_volume': np.random.poisson(80, size=len(market_dates)) + 20 * np.sin(np.arange(len(market_dates)) * 2 * np.pi / 12),
        'new_listings': np.random.poisson(120, size=len(market_dates)) + 30 * np.sin(np.arange(len(market_dates)) * 2 * np.pi / 12)
    })
    
    # Conversion Funnel Data
    funnel_data = pd.DataFrame({
        'stage': [
            'Website Visitors',
            'Lead Capture',
            'Qualified Leads',
            'Property Viewings',
            'Offer Submissions',
            'Accepted Offers',
            'Closed Deals'
        ],
        'count': [10000, 2500, 1500, 800, 300, 180, 150]
    })
    
    # Attribution Data
    attribution_data = pd.DataFrame({
        'source': [
            'Organic Search',
            'Google Ads',
            'Facebook Ads',
            'Referrals',
            'Zillow',
            'Realtor.com',
            'Direct Traffic',
            'Email Marketing'
        ],
        'count': [450, 380, 290, 340, 180, 150, 120, 90],
        'conversion_rate': [0.18, 0.12, 0.08, 0.28, 0.15, 0.14, 0.22, 0.25],
        'cost_per_lead': [0, 85, 62, 0, 45, 38, 0, 15],
        'avg_deal_value': [465000, 420000, 385000, 520000, 440000, 435000, 480000, 495000]
    })
    
    # Time Series Data for Real-time Metrics
    time_series_dates = pd.date_range('2024-01-01', periods=90, freq='D')
    time_series_data = pd.DataFrame({
        'timestamp': time_series_dates,
        'daily_leads': np.random.poisson(12, size=90) + 3 * np.sin(np.arange(90) * 2 * np.pi / 7),  # Weekly pattern
        'daily_revenue': np.random.exponential(scale=8000, size=90) * (1 + 0.3 * np.sin(np.arange(90) * 2 * np.pi / 30)),  # Monthly pattern
        'active_conversations': np.random.poisson(25, size=90),
        'conversion_rate': 0.15 + 0.05 * np.sin(np.arange(90) * 2 * np.pi / 30) + np.random.normal(0, 0.02, size=90)
    })
    
    # Forecast Data
    forecast_dates = pd.date_range('2024-04-01', periods=30, freq='D')
    base_forecast = 8500 * (1 + np.arange(30) * 0.02)  # 2% growth trend
    forecast_data = pd.DataFrame({
        'date': forecast_dates,
        'daily_revenue': base_forecast + np.random.normal(0, 500, size=30),
        'upper_bound': base_forecast * 1.15,
        'lower_bound': base_forecast * 0.85
    })
    
    return {
        'ml_data': ml_data,
        'lead_data': lead_data,
        'market_data': market_data,
        'funnel_data': funnel_data,
        'attribution_data': attribution_data,
        'time_series_data': time_series_data,
        'forecast_data': forecast_data
    }


def demonstrate_chart_factory():
    """Demonstrate the main chart factory functionality."""
    st.title("🏠 Jorge's Chart Builders Demo")
    st.markdown("**Comprehensive visualization toolkit for real estate AI analytics**")
    
    # Generate sample data
    data = generate_sample_data()
    
    # Theme Selection
    st.sidebar.title("🎨 Theme Configuration")
    dark_mode = st.sidebar.checkbox("Dark Mode", value=False)
    colorblind_friendly = st.sidebar.checkbox("Colorblind Friendly", value=False)
    
    # Initialize Chart Factory
    factory = ChartFactory(dark_mode=dark_mode, colorblind_friendly=colorblind_friendly)
    
    # Display Theme Colors
    st.sidebar.subheader("Current Theme Colors")
    colors = factory.get_theme_colors()
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.color_picker("Primary Blue", colors['primary_blue'], disabled=True)
        st.color_picker("Primary Gold", colors['primary_gold'], disabled=True)
    with col2:
        st.color_picker("Success", colors['success'], disabled=True)
        st.color_picker("Warning", colors['warning'], disabled=True)
    
    # Navigation
    demo_sections = [
        "📊 Dashboard KPIs",
        "🎯 ML Performance Charts", 
        "🏘️ Real Estate Analytics",
        "📈 Interactive Widgets",
        "⚡ Quick Functions Demo",
        "📤 Export Functionality"
    ]
    
    selected_section = st.selectbox("Choose Demo Section", demo_sections)
    
    if selected_section == "📊 Dashboard KPIs":
        demonstrate_dashboard_kpis(factory, data)
    elif selected_section == "🎯 ML Performance Charts":
        demonstrate_ml_charts(factory, data)
    elif selected_section == "🏘️ Real Estate Analytics":
        demonstrate_real_estate_charts(factory, data)
    elif selected_section == "📈 Interactive Widgets":
        demonstrate_interactive_widgets(factory, data)
    elif selected_section == "⚡ Quick Functions Demo":
        demonstrate_quick_functions(data)
    elif selected_section == "📤 Export Functionality":
        demonstrate_export_functionality(factory, data)


def demonstrate_dashboard_kpis(factory, data):
    """Demonstrate KPI card creation."""
    st.subheader("📊 Dashboard KPI Cards")
    st.markdown("Real-time business metrics with trend indicators")
    
    # Calculate sample metrics
    lead_data = data['lead_data']
    conversion_rate = lead_data['converted'].mean()
    avg_lead_value = lead_data['estimated_value'].mean()
    total_leads = len(lead_data)
    
    # Create KPI cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        revenue_kpi = factory.create_chart(
            'kpi_card',
            "Monthly Revenue",
            value=125000,
            change=0.15,
            format_type="currency"
        )
        st.plotly_chart(revenue_kpi, use_container_width=True)
    
    with col2:
        leads_kpi = factory.create_chart(
            'kpi_card',
            "Total Leads",
            value=total_leads,
            change=0.08,
            format_type="number"
        )
        st.plotly_chart(leads_kpi, use_container_width=True)
    
    with col3:
        conversion_kpi = factory.create_chart(
            'kpi_card',
            "Conversion Rate",
            value=conversion_rate,
            change=-0.02,
            format_type="percentage"
        )
        st.plotly_chart(conversion_kpi, use_container_width=True)
    
    # Additional KPIs
    col4, col5, col6 = st.columns(3)
    
    with col4:
        avg_value_kpi = factory.create_chart(
            'kpi_card',
            "Avg Lead Value",
            value=avg_lead_value,
            change=0.05,
            format_type="currency"
        )
        st.plotly_chart(avg_value_kpi, use_container_width=True)
    
    with col5:
        pipeline_kpi = factory.create_chart(
            'kpi_card',
            "Pipeline Value",
            value=2500000,
            change=0.22,
            format_type="currency"
        )
        st.plotly_chart(pipeline_kpi, use_container_width=True)
    
    with col6:
        active_listings_kpi = factory.create_chart(
            'kpi_card',
            "Active Listings",
            value=347,
            change=-0.05,
            format_type="number"
        )
        st.plotly_chart(active_listings_kpi, use_container_width=True)


def demonstrate_ml_charts(factory, data):
    """Demonstrate ML performance chart creation."""
    st.subheader("🎯 ML Performance Visualization")
    st.markdown("Advanced analytics for model evaluation and feature analysis")
    
    ml_data = data['ml_data']
    
    # Model Selection
    model_option = st.selectbox(
        "Choose Model Analysis",
        ["Single Model ROC", "Multi-Model Comparison", "Feature Importance", "Confusion Matrix"]
    )
    
    if model_option == "Single Model ROC":
        st.subheader("ROC Curve Analysis")
        roc_fig = factory.create_chart(
            'roc_curve',
            ml_data['y_true'],
            y_scores=ml_data['y_scores_model_1'],
            model_names=["Lead Scoring Model v2.1"]
        )
        st.plotly_chart(roc_fig, use_container_width=True)
        
        # Add interpretation
        st.info("**ROC Curve Interpretation**: The curve shows the trade-off between true positive rate and false positive rate. The closer the curve is to the top-left corner, the better the model performance.")
    
    elif model_option == "Multi-Model Comparison":
        st.subheader("Multi-Model ROC Comparison")
        y_scores_multi = np.column_stack([ml_data['y_scores_model_1'], ml_data['y_scores_model_2']])
        multi_roc_fig = factory.create_chart(
            'roc_curve',
            ml_data['y_true'],
            y_scores=y_scores_multi,
            model_names=["Lead Scoring Model v2.1", "Enhanced Model v3.0"]
        )
        st.plotly_chart(multi_roc_fig, use_container_width=True)
        
        # Precision-Recall Comparison
        st.subheader("Precision-Recall Curves")
        pr_fig = factory.create_chart(
            'precision_recall',
            ml_data['y_true'],
            y_scores=y_scores_multi,
            model_names=["Lead Scoring Model v2.1", "Enhanced Model v3.0"]
        )
        st.plotly_chart(pr_fig, use_container_width=True)
    
    elif model_option == "Feature Importance":
        st.subheader("Feature Importance Analysis")
        fi_fig = factory.create_chart(
            'feature_importance',
            ml_data['feature_names'],
            importance_scores=ml_data['feature_importance'],
            model_name="Lead Scoring Model v2.1"
        )
        st.plotly_chart(fi_fig, use_container_width=True)
        
        # Feature insights
        st.markdown("**Key Insights:**")
        top_features = sorted(zip(ml_data['feature_names'], ml_data['feature_importance']), 
                             key=lambda x: x[1], reverse=True)[:3]
        for i, (feature, importance) in enumerate(top_features, 1):
            st.write(f"{i}. **{feature}**: {importance:.1%} importance")
    
    elif model_option == "Confusion Matrix":
        st.subheader("Confusion Matrix")
        y_pred = (ml_data['y_scores_model_1'] > 0.5).astype(int)
        cm_fig = factory.create_chart(
            'confusion_matrix',
            ml_data['y_true'],
            y_pred,
            labels=["No Conversion", "Conversion"]
        )
        st.plotly_chart(cm_fig, use_container_width=True)


def demonstrate_real_estate_charts(factory, data):
    """Demonstrate real estate analytics charts."""
    st.subheader("🏘️ Real Estate Analytics Dashboard")
    st.markdown("Comprehensive market analysis and lead intelligence")
    
    chart_type = st.selectbox(
        "Choose Analytics View",
        ["Lead Score Analysis", "Conversion Funnel", "Market Trends", "Attribution Analysis"]
    )
    
    if chart_type == "Lead Score Analysis":
        st.subheader("Lead Score Distribution & Analysis")
        lead_fig = factory.create_chart('lead_score_distribution', data['lead_data'])
        st.plotly_chart(lead_fig, use_container_width=True)
        
        # Lead insights
        lead_data = data['lead_data']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Score", f"{lead_data['score'].mean():.1f}")
        with col2:
            st.metric("High-Quality Leads", f"{(lead_data['score'] > 75).sum()}")
        with col3:
            st.metric("Conversion Rate", f"{lead_data['converted'].mean():.1%}")
    
    elif chart_type == "Conversion Funnel":
        st.subheader("Lead Conversion Funnel")
        funnel_fig = factory.create_chart('conversion_funnel', data['funnel_data'])
        st.plotly_chart(funnel_fig, use_container_width=True)
        
        # Funnel metrics
        funnel_data = data['funnel_data']
        st.markdown("**Conversion Rates by Stage:**")
        for i in range(len(funnel_data) - 1):
            current_stage = funnel_data.iloc[i]
            next_stage = funnel_data.iloc[i + 1]
            conversion_rate = next_stage['count'] / current_stage['count']
            st.write(f"• {current_stage['stage']} → {next_stage['stage']}: {conversion_rate:.1%}")
    
    elif chart_type == "Market Trends":
        st.subheader("Market Trends Analysis")
        market_fig = factory.create_chart('market_trends', data['market_data'])
        st.plotly_chart(market_fig, use_container_width=True)
        
        # Market insights
        market_data = data['market_data']
        latest_data = market_data.iloc[-1]
        previous_data = market_data.iloc[-12]  # Year over year
        
        col1, col2, col3 = st.columns(3)
        with col1:
            price_change = (latest_data['avg_price'] - previous_data['avg_price']) / previous_data['avg_price']
            st.metric("Avg Price YoY", f"${latest_data['avg_price']:,.0f}", f"{price_change:+.1%}")
        with col2:
            st.metric("Active Listings", f"{latest_data['active_listings']:.0f}")
        with col3:
            st.metric("Avg Days on Market", f"{latest_data['avg_dom']:.0f}")
    
    elif chart_type == "Attribution Analysis":
        st.subheader("Lead Source Attribution")
        attribution_fig = factory.create_chart('attribution_analysis', data['attribution_data'])
        st.plotly_chart(attribution_fig, use_container_width=True)
        
        # Attribution insights
        attribution_data = data['attribution_data']
        best_source = attribution_data.loc[attribution_data['conversion_rate'].idxmax()]
        st.success(f"**Best Performing Source**: {best_source['source']} with {best_source['conversion_rate']:.1%} conversion rate")


def demonstrate_interactive_widgets(factory, data):
    """Demonstrate interactive dashboard widgets."""
    st.subheader("📈 Interactive Dashboard Widgets")
    st.markdown("Real-time metrics and forecasting capabilities")
    
    widget_type = st.selectbox(
        "Choose Widget Type",
        ["Real-time Metrics", "Forecasting", "Performance Tracking"]
    )
    
    if widget_type == "Real-time Metrics":
        st.subheader("Real-time Business Metrics")
        
        metric_choice = st.selectbox("Select Metric", ["Daily Leads", "Daily Revenue", "Conversion Rate"])
        
        if metric_choice == "Daily Leads":
            leads_fig = factory.create_chart(
                'real_time_metric',
                data['time_series_data'],
                metric_column='daily_leads',
                time_column='timestamp'
            )
            st.plotly_chart(leads_fig, use_container_width=True)
        
        elif metric_choice == "Daily Revenue":
            revenue_fig = factory.create_chart(
                'real_time_metric',
                data['time_series_data'],
                metric_column='daily_revenue',
                time_column='timestamp'
            )
            st.plotly_chart(revenue_fig, use_container_width=True)
        
        elif metric_choice == "Conversion Rate":
            conversion_fig = factory.create_chart(
                'real_time_metric',
                data['time_series_data'],
                metric_column='conversion_rate',
                time_column='timestamp'
            )
            st.plotly_chart(conversion_fig, use_container_width=True)
    
    elif widget_type == "Forecasting":
        st.subheader("Revenue Forecasting")
        forecast_fig = factory.create_chart(
            'forecast_chart',
            historical_data=data['time_series_data'][['timestamp', 'daily_revenue']].rename(columns={'timestamp': 'date'}),
            forecast_data=data['forecast_data'],
            value_column='daily_revenue',
            time_column='date'
        )
        st.plotly_chart(forecast_fig, use_container_width=True)
        
        st.info("**Forecast Model**: 30-day revenue prediction with 85% confidence intervals based on historical trends and seasonal patterns.")


def demonstrate_quick_functions(data):
    """Demonstrate quick convenience functions."""
    st.subheader("⚡ Quick Chart Functions")
    st.markdown("Rapid chart creation with minimal code")
    
    function_demo = st.selectbox(
        "Choose Quick Function",
        ["quick_roc_curve", "quick_lead_analysis", "quick_kpi_card"]
    )
    
    if function_demo == "quick_roc_curve":
        st.subheader("Quick ROC Curve")
        st.code("""
from command_center.utils.chart_builders import quick_roc_curve

fig = quick_roc_curve(y_true, y_scores)
        """)
        
        ml_data = data['ml_data']
        roc_fig = quick_roc_curve(ml_data['y_true'], ml_data['y_scores_model_1'])
        st.plotly_chart(roc_fig, use_container_width=True)
    
    elif function_demo == "quick_lead_analysis":
        st.subheader("Quick Lead Analysis")
        st.code("""
from command_center.utils.chart_builders import quick_lead_analysis

fig = quick_lead_analysis(lead_dataframe)
        """)
        
        lead_fig = quick_lead_analysis(data['lead_data'])
        st.plotly_chart(lead_fig, use_container_width=True)
    
    elif function_demo == "quick_kpi_card":
        st.subheader("Quick KPI Card")
        st.code("""
from command_center.utils.chart_builders import quick_kpi_card

fig = quick_kpi_card("Revenue", 125000)
        """)
        
        kpi_fig = quick_kpi_card("Quick KPI Demo", 98765)
        st.plotly_chart(kpi_fig, use_container_width=True)


def demonstrate_export_functionality(factory, data):
    """Demonstrate chart export capabilities."""
    st.subheader("📤 Export Functionality")
    st.markdown("Chart export for reports and presentations")
    
    # Create sample charts for export demo
    charts_to_export = {
        'revenue_kpi': factory.create_chart('kpi_card', "Revenue", value=125000),
        'lead_analysis': factory.create_chart('lead_score_distribution', data['lead_data']),
        'market_trends': factory.create_chart('market_trends', data['market_data'])
    }
    
    st.subheader("Available Charts for Export")
    for chart_name in charts_to_export.keys():
        st.write(f"• {chart_name.replace('_', ' ').title()}")
    
    export_format = st.selectbox("Export Format", ["PNG", "HTML", "PDF", "SVG"])
    
    if st.button("Generate Export Demo"):
        st.info(f"Charts would be exported as {export_format} format in a production environment.")
        st.code(f"""
# Example export code
charts = {charts_to_export.keys()}
exported_files = factory.batch_export(
    charts, 
    base_path="./reports",
    formats=["{export_format.lower()}"]
)
        """)
    
    # Show theme colors for reference
    st.subheader("Current Theme Configuration")
    colors = factory.get_theme_colors()
    st.json(colors)


def main():
    """Main demo application."""
    st.set_page_config(
        page_title="Jorge's Chart Builders Demo",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        padding: 1rem 0;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #F59E0B;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    demonstrate_chart_factory()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Jorge's Chart Builders Demo** | "
        "Advanced Real Estate AI Visualization Platform | "
        f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


if __name__ == "__main__":
    main()