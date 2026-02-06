"""
ML Scoring Dashboard - Jorge's Real Estate AI Platform
Advanced machine learning model performance monitoring and A/B testing dashboard.

Features:
- Model Performance Metrics UI with real-time tracking
- ROC-AUC, precision, recall visualization using Plotly charts
- Confidence Distribution Analysis with confidence threshold visualization
- A/B Testing Dashboard for champion vs challenger model comparison
- Integration with existing dashboard patterns from /command_center/dashboard.py

Author: Jorge's AI Assistant
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import json
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Theme constants following Jorge's patterns
JORGE_THEME = {
    'primary': '#3b82f6',
    'secondary': '#1e3a8a',
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'accent': '#8b5cf6',
    'background': 'rgba(255,255,255,0.02)',
    'border': 'rgba(255,255,255,0.05)',
    'text_primary': '#FFFFFF',
    'text_secondary': '#8B949E',
    'font_primary': 'Space Grotesk',
    'font_secondary': 'Inter'
}

class ModelType(Enum):
    """Model types for ML scoring."""
    LEAD_SCORING = "lead_scoring"
    PROPERTY_VALUATION = "property_valuation"
    CHURN_PREDICTION = "churn_prediction"
    CONVERSION_PREDICTION = "conversion_prediction"

@dataclass
class ModelMetrics:
    """Data structure for model performance metrics."""
    model_name: str
    model_type: ModelType
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    confidence_scores: List[float]
    prediction_counts: Dict[str, int]
    inference_latency: float
    throughput: float
    cache_hit_rate: float
    timestamp: datetime

@dataclass
class ABTestResult:
    """Data structure for A/B test results."""
    test_id: str
    champion_model: str
    challenger_model: str
    test_start: datetime
    test_end: Optional[datetime]
    champion_metrics: ModelMetrics
    challenger_metrics: ModelMetrics
    traffic_split: float
    statistical_significance: float
    winner: Optional[str]

# Streamlit page configuration and styling
def apply_ml_dashboard_styles():
    """Apply custom CSS styling for ML dashboard following Jorge's theme."""
    st.markdown(f"""
    <style>
        /* Main dashboard styling */
        .main .block-container {{
            padding: 1rem 2rem;
            max-width: 100%;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }}

        /* Header styling */
        .ml-dashboard-header {{
            background: linear-gradient(90deg, {JORGE_THEME['secondary']} 0%, {JORGE_THEME['primary']} 100%);
            color: {JORGE_THEME['text_primary']};
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}

        .ml-dashboard-header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
            font-family: '{JORGE_THEME['font_primary']}', sans-serif;
        }}

        .ml-dashboard-header .subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
            margin-top: 0.5rem;
            font-family: '{JORGE_THEME['font_secondary']}', sans-serif;
        }}

        /* Metric card styling */
        .metric-card {{
            background: {JORGE_THEME['background']};
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid {JORGE_THEME['border']};
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            backdrop-filter: blur(12px);
            text-align: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 48px rgba(0,0,0,0.4);
        }}

        .metric-value {{
            font-size: 2.25rem;
            font-weight: 700;
            margin: 8px 0;
            font-family: '{JORGE_THEME['font_primary']}', sans-serif;
            color: {JORGE_THEME['text_primary']};
        }}

        .metric-label {{
            font-size: 0.75rem;
            color: {JORGE_THEME['text_secondary']};
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-family: '{JORGE_THEME['font_primary']}', sans-serif;
        }}

        .metric-delta {{
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-top: 8px;
        }}

        /* Section styling */
        .dashboard-section {{
            background: {JORGE_THEME['background']};
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid {JORGE_THEME['border']};
            margin-bottom: 2rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }}

        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: {JORGE_THEME['text_primary']};
            margin-bottom: 1.5rem;
            font-family: '{JORGE_THEME['font_primary']}', sans-serif;
        }}

        /* Status indicators */
        .status-indicator {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }}

        .status-champion {{
            background: rgba(16, 185, 129, 0.2);
            color: {JORGE_THEME['success']};
            border: 1px solid {JORGE_THEME['success']};
        }}

        .status-challenger {{
            background: rgba(245, 158, 11, 0.2);
            color: {JORGE_THEME['warning']};
            border: 1px solid {JORGE_THEME['warning']};
        }}

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2px;
            background-color: rgba(255,255,255,0.05);
            padding: 0.5rem;
            border-radius: 12px;
        }}

        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            font-family: '{JORGE_THEME['font_secondary']}', sans-serif;
        }}

        /* Alert boxes */
        .alert-box {{
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-family: '{JORGE_THEME['font_secondary']}', sans-serif;
        }}

        .alert-success {{
            background-color: rgba(16, 185, 129, 0.1);
            border: 1px solid {JORGE_THEME['success']};
            color: {JORGE_THEME['success']};
        }}

        .alert-warning {{
            background-color: rgba(245, 158, 11, 0.1);
            border: 1px solid {JORGE_THEME['warning']};
            color: {JORGE_THEME['warning']};
        }}

        /* Responsive design */
        @media (max-width: 768px) {{
            .main .block-container {{
                padding: 0.5rem 1rem;
            }}
            .ml-dashboard-header h1 {{
                font-size: 1.8rem;
            }}
            .metric-value {{
                font-size: 1.8rem;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)

def render_dashboard_header():
    """Render the ML dashboard header with live status."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    st.markdown(f"""
    <div class="ml-dashboard-header">
        <h1>🤖 ML Scoring Intelligence Dashboard</h1>
        <div class="subtitle">
            Advanced Model Performance Analytics • Jorge's AI Platform • Updated: {current_time}
        </div>
    </div>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_model_performance_data() -> Dict[str, ModelMetrics]:
    """
    Retrieve current model performance metrics.
    In production, this would query actual ML monitoring systems.
    """
    # Simulate realistic model performance data
    models = {}

    # Lead Scoring Model
    models['lead_scoring_v2'] = ModelMetrics(
        model_name="Lead Scoring v2.1",
        model_type=ModelType.LEAD_SCORING,
        accuracy=0.847,
        precision=0.789,
        recall=0.823,
        f1_score=0.806,
        roc_auc=0.892,
        confidence_scores=np.random.beta(2, 1, 1000).tolist(),
        prediction_counts={'qualified': 234, 'unqualified': 567, 'follow_up': 89},
        inference_latency=45.2,
        throughput=1250.0,
        cache_hit_rate=0.834,
        timestamp=datetime.now()
    )

    # Property Valuation Model
    models['property_valuation_v1'] = ModelMetrics(
        model_name="Property Valuation v1.3",
        model_type=ModelType.PROPERTY_VALUATION,
        accuracy=0.912,
        precision=0.887,
        recall=0.895,
        f1_score=0.891,
        roc_auc=0.923,
        confidence_scores=np.random.beta(3, 1, 1000).tolist(),
        prediction_counts={'accurate': 456, 'overvalued': 123, 'undervalued': 78},
        inference_latency=78.5,
        throughput=890.0,
        cache_hit_rate=0.756,
        timestamp=datetime.now()
    )

    # Churn Prediction Model
    models['churn_prediction_v1'] = ModelMetrics(
        model_name="Churn Prediction v1.0",
        model_type=ModelType.CHURN_PREDICTION,
        accuracy=0.783,
        precision=0.742,
        recall=0.798,
        f1_score=0.769,
        roc_auc=0.856,
        confidence_scores=np.random.beta(2, 2, 1000).tolist(),
        prediction_counts={'high_risk': 89, 'medium_risk': 145, 'low_risk': 234},
        inference_latency=32.1,
        throughput=1580.0,
        cache_hit_rate=0.892,
        timestamp=datetime.now()
    )

    return models

@st.cache_data(ttl=300)
def get_ab_test_data() -> List[ABTestResult]:
    """
    Retrieve A/B test results for model comparisons.
    In production, this would query actual A/B testing framework.
    """
    tests = []

    # Active Lead Scoring A/B Test
    champion_metrics = ModelMetrics(
        model_name="Lead Scoring v2.0 (Champion)",
        model_type=ModelType.LEAD_SCORING,
        accuracy=0.834,
        precision=0.778,
        recall=0.812,
        f1_score=0.794,
        roc_auc=0.881,
        confidence_scores=np.random.beta(2, 1.2, 500).tolist(),
        prediction_counts={'qualified': 112, 'unqualified': 278, 'follow_up': 43},
        inference_latency=52.3,
        throughput=1180.0,
        cache_hit_rate=0.823,
        timestamp=datetime.now()
    )

    challenger_metrics = ModelMetrics(
        model_name="Lead Scoring v2.1 (Challenger)",
        model_type=ModelType.LEAD_SCORING,
        accuracy=0.847,
        precision=0.789,
        recall=0.823,
        f1_score=0.806,
        roc_auc=0.892,
        confidence_scores=np.random.beta(2, 1, 500).tolist(),
        prediction_counts={'qualified': 122, 'unqualified': 289, 'follow_up': 46},
        inference_latency=45.2,
        throughput=1250.0,
        cache_hit_rate=0.834,
        timestamp=datetime.now()
    )

    tests.append(ABTestResult(
        test_id="lead_scoring_test_001",
        champion_model="lead_scoring_v2_0",
        challenger_model="lead_scoring_v2_1",
        test_start=datetime.now() - timedelta(days=7),
        test_end=None,
        champion_metrics=champion_metrics,
        challenger_metrics=challenger_metrics,
        traffic_split=0.5,
        statistical_significance=0.89,
        winner="challenger"
    ))

    return tests

def render_model_performance_overview():
    """Render the model performance overview section."""
    st.markdown('<div class="section-title">📊 Model Performance Overview</div>', unsafe_allow_html=True)

    models = get_model_performance_data()

    # Create metrics columns
    cols = st.columns(len(models))

    for idx, (model_id, metrics) in enumerate(models.items()):
        with cols[idx]:
            # Determine metric color based on performance
            if metrics.roc_auc >= 0.9:
                color = JORGE_THEME['success']
                status = "🟢 EXCELLENT"
            elif metrics.roc_auc >= 0.8:
                color = JORGE_THEME['primary']
                status = "🔵 GOOD"
            else:
                color = JORGE_THEME['warning']
                status = "🟡 NEEDS ATTENTION"

            st.markdown(f"""
            <div style='background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1);
                        {JORGE_THEME['background'][8:-1]}; border-top: 4px solid {color};'
                        class='metric-card'>
                <div class='metric-value'>{metrics.roc_auc:.3f}</div>
                <div class='metric-label'>{metrics.model_name}</div>
                <div class='metric-delta' style='color: {color};'>{status}</div>
            </div>
            """, unsafe_allow_html=True)

    # Detailed metrics table
    st.markdown("### 📈 Detailed Performance Metrics")

    metrics_df = pd.DataFrame([
        {
            'Model': metrics.model_name,
            'Type': metrics.model_type.value.replace('_', ' ').title(),
            'Accuracy': f"{metrics.accuracy:.3f}",
            'Precision': f"{metrics.precision:.3f}",
            'Recall': f"{metrics.recall:.3f}",
            'F1-Score': f"{metrics.f1_score:.3f}",
            'ROC-AUC': f"{metrics.roc_auc:.3f}",
            'Latency (ms)': f"{metrics.inference_latency:.1f}",
            'Throughput': f"{metrics.throughput:.0f}/sec",
            'Cache Hit Rate': f"{metrics.cache_hit_rate:.1%}"
        }
        for metrics in models.values()
    ])

    st.dataframe(metrics_df, use_container_width=True)

def create_roc_curve_chart(models: Dict[str, ModelMetrics]) -> go.Figure:
    """Create ROC curve comparison chart for multiple models."""
    fig = go.Figure()

    colors = [JORGE_THEME['primary'], JORGE_THEME['success'], JORGE_THEME['accent']]

    for idx, (model_id, metrics) in enumerate(models.items()):
        # Simulate ROC curve data points
        fpr = np.linspace(0, 1, 100)
        tpr = np.power(fpr, 1/metrics.roc_auc)  # Approximate TPR from AUC

        fig.add_trace(go.Scatter(
            x=fpr,
            y=tpr,
            mode='lines',
            name=f"{metrics.model_name} (AUC: {metrics.roc_auc:.3f})",
            line=dict(color=colors[idx % len(colors)], width=3),
            hovertemplate='<b>%{fullData.name}</b><br>FPR: %{x:.3f}<br>TPR: %{y:.3f}<extra></extra>'
        ))

    # Add diagonal reference line
    fig.add_trace(go.Scatter(
        x=[0, 1],
        y=[0, 1],
        mode='lines',
        name='Random Classifier',
        line=dict(color='gray', width=1, dash='dash'),
        showlegend=False
    ))

    fig.update_layout(
        title='ROC Curve Comparison',
        xaxis_title='False Positive Rate',
        yaxis_title='True Positive Rate',
        template='plotly_dark',
        height=400,
        showlegend=True,
        legend=dict(
            yanchor="bottom",
            y=0.02,
            xanchor="right",
            x=0.98
        )
    )

    return fig

def create_confidence_distribution_chart(models: Dict[str, ModelMetrics]) -> go.Figure:
    """Create confidence score distribution visualization."""
    fig = make_subplots(
        rows=len(models), cols=1,
        subplot_titles=[metrics.model_name for metrics in models.values()],
        vertical_spacing=0.1
    )

    colors = [JORGE_THEME['primary'], JORGE_THEME['success'], JORGE_THEME['accent']]

    for idx, (model_id, metrics) in enumerate(models.items()):
        # Create histogram of confidence scores
        fig.add_trace(
            go.Histogram(
                x=metrics.confidence_scores,
                nbinsx=50,
                name=metrics.model_name,
                marker_color=colors[idx % len(colors)],
                opacity=0.7,
                showlegend=False
            ),
            row=idx+1, col=1
        )

        # Add threshold lines
        thresholds = [0.5, 0.7, 0.9]
        for threshold in thresholds:
            fig.add_vline(
                x=threshold,
                line_dash="dash",
                line_color="white",
                opacity=0.5,
                row=idx+1, col=1
            )

    fig.update_layout(
        title='Model Confidence Score Distributions',
        template='plotly_dark',
        height=300 * len(models),
        showlegend=False
    )

    fig.update_xaxes(title_text="Confidence Score", row=len(models), col=1)
    fig.update_yaxes(title_text="Frequency")

    return fig

def render_performance_visualizations():
    """Render performance visualization charts."""
    st.markdown('<div class="section-title">📈 Performance Visualizations</div>', unsafe_allow_html=True)

    models = get_model_performance_data()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ROC Curve Analysis")
        roc_fig = create_roc_curve_chart(models)
        st.plotly_chart(roc_fig, use_container_width=True)

    with col2:
        st.markdown("#### Feature Importance (SHAP Values)")
        # Simulate feature importance data
        features = ['Lead Source Quality', 'Response Time', 'Budget Range', 'Location Preference',
                   'Previous Interactions', 'Property Type', 'Financing Status', 'Contact Frequency']
        importance = np.random.exponential(0.5, len(features))
        importance = importance / importance.sum()

        fig = go.Figure(go.Bar(
            x=importance,
            y=features,
            orientation='h',
            marker_color=JORGE_THEME['primary']
        ))

        fig.update_layout(
            title='Top Feature Importance',
            xaxis_title='SHAP Value',
            template='plotly_dark',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    # Confidence distribution chart
    st.markdown("#### Confidence Score Analysis")
    conf_fig = create_confidence_distribution_chart(models)
    st.plotly_chart(conf_fig, use_container_width=True)

def render_ab_testing_dashboard():
    """Render A/B testing dashboard for model comparison."""
    st.markdown('<div class="section-title">🧪 A/B Testing Dashboard</div>', unsafe_allow_html=True)

    ab_tests = get_ab_test_data()

    if not ab_tests:
        st.info("🔄 No active A/B tests currently running.")
        return

    # Test overview
    for test in ab_tests:
        st.markdown(f"#### Test: {test.test_id}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Duration", f"{(datetime.now() - test.test_start).days} days")
        with col2:
            st.metric("Traffic Split", f"{test.traffic_split:.0%}")
        with col3:
            st.metric("Statistical Significance", f"{test.statistical_significance:.1%}")
        with col4:
            winner_display = test.winner.title() if test.winner else "TBD"
            st.metric("Winner", winner_display)

        # Champion vs Challenger comparison
        st.markdown("##### 🏆 Champion vs 🥇 Challenger Comparison")

        comparison_df = pd.DataFrame({
            'Metric': ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'ROC-AUC', 'Latency (ms)', 'Throughput'],
            'Champion': [
                f"{test.champion_metrics.accuracy:.3f}",
                f"{test.champion_metrics.precision:.3f}",
                f"{test.champion_metrics.recall:.3f}",
                f"{test.champion_metrics.f1_score:.3f}",
                f"{test.champion_metrics.roc_auc:.3f}",
                f"{test.champion_metrics.inference_latency:.1f}",
                f"{test.champion_metrics.throughput:.0f}"
            ],
            'Challenger': [
                f"{test.challenger_metrics.accuracy:.3f}",
                f"{test.challenger_metrics.precision:.3f}",
                f"{test.challenger_metrics.recall:.3f}",
                f"{test.challenger_metrics.f1_score:.3f}",
                f"{test.challenger_metrics.roc_auc:.3f}",
                f"{test.challenger_metrics.inference_latency:.1f}",
                f"{test.challenger_metrics.throughput:.0f}"
            ]
        })

        # Add improvement indicators
        improvements = []
        for i, metric in enumerate(['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']):
            champ_val = getattr(test.champion_metrics, metric)
            chall_val = getattr(test.challenger_metrics, metric)
            improvement = ((chall_val - champ_val) / champ_val) * 100
            if improvement > 0:
                improvements.append(f"↗️ +{improvement:.1f}%")
            elif improvement < 0:
                improvements.append(f"↘️ {improvement:.1f}%")
            else:
                improvements.append("➖ 0.0%")

        # Add latency and throughput improvements
        latency_improvement = ((test.champion_metrics.inference_latency - test.challenger_metrics.inference_latency) / test.champion_metrics.inference_latency) * 100
        throughput_improvement = ((test.challenger_metrics.throughput - test.champion_metrics.throughput) / test.champion_metrics.throughput) * 100

        improvements.append(f"↗️ +{latency_improvement:.1f}%" if latency_improvement > 0 else f"↘️ {latency_improvement:.1f}%")
        improvements.append(f"↗️ +{throughput_improvement:.1f}%" if throughput_improvement > 0 else f"↘️ {throughput_improvement:.1f}%")

        comparison_df['Improvement'] = improvements

        st.dataframe(comparison_df, use_container_width=True)

        # Statistical significance visualization
        st.markdown("##### 📊 Statistical Analysis")

        if test.statistical_significance >= 0.95:
            significance_status = "🟢 Statistically Significant"
            significance_color = JORGE_THEME['success']
        elif test.statistical_significance >= 0.8:
            significance_status = "🟡 Approaching Significance"
            significance_color = JORGE_THEME['warning']
        else:
            significance_status = "🔴 Not Significant"
            significance_color = JORGE_THEME['error']

        st.markdown(f"""
        <div class="alert-box alert-success">
            <strong>{significance_status}</strong><br>
            Confidence Level: {test.statistical_significance:.1%}<br>
            Recommendation: {"Deploy challenger model" if test.winner == "challenger" and test.statistical_significance >= 0.95 else "Continue testing"}
        </div>
        """, unsafe_allow_html=True)

def render_inference_performance_dashboard():
    """Render inference performance monitoring dashboard."""
    st.markdown('<div class="section-title">⚡ Inference Performance Dashboard</div>', unsafe_allow_html=True)

    models = get_model_performance_data()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🚀 Latency & Throughput")

        latency_data = [(metrics.model_name, metrics.inference_latency) for metrics in models.values()]
        throughput_data = [(metrics.model_name, metrics.throughput) for metrics in models.values()]

        # Latency chart
        fig_latency = go.Figure(data=[
            go.Bar(
                x=[name for name, _ in latency_data],
                y=[latency for _, latency in latency_data],
                marker_color=JORGE_THEME['primary'],
                text=[f"{latency:.1f}ms" for _, latency in latency_data],
                textposition='auto',
            )
        ])

        fig_latency.update_layout(
            title='Model Inference Latency',
            yaxis_title='Latency (milliseconds)',
            template='plotly_dark',
            height=300
        )

        st.plotly_chart(fig_latency, use_container_width=True)

    with col2:
        st.markdown("#### 💾 Cache Performance")

        cache_data = [(metrics.model_name, metrics.cache_hit_rate) for metrics in models.values()]

        # Cache hit rate chart
        fig_cache = go.Figure(data=[
            go.Bar(
                x=[name for name, _ in cache_data],
                y=[rate for _, rate in cache_data],
                marker_color=JORGE_THEME['success'],
                text=[f"{rate:.1%}" for _, rate in cache_data],
                textposition='auto',
            )
        ])

        fig_cache.update_layout(
            title='Cache Hit Rate by Model',
            yaxis_title='Cache Hit Rate (%)',
            yaxis=dict(range=[0, 1], tickformat='.0%'),
            template='plotly_dark',
            height=300
        )

        st.plotly_chart(fig_cache, use_container_width=True)

    # Real-time throughput metrics
    st.markdown("#### 📈 Real-time Performance Metrics")

    perf_cols = st.columns(4)

    total_throughput = sum(metrics.throughput for metrics in models.values())
    avg_latency = sum(metrics.inference_latency for metrics in models.values()) / len(models)
    avg_cache_hit = sum(metrics.cache_hit_rate for metrics in models.values()) / len(models)

    with perf_cols[0]:
        st.metric("Total Throughput", f"{total_throughput:,.0f}/sec", "+12%")
    with perf_cols[1]:
        st.metric("Avg Latency", f"{avg_latency:.1f}ms", "-8%")
    with perf_cols[2]:
        st.metric("Avg Cache Hit Rate", f"{avg_cache_hit:.1%}", "+3%")
    with perf_cols[3]:
        st.metric("Active Models", len(models), "0")

def render_model_health_alerts():
    """Render model health monitoring and alert system."""
    st.markdown('<div class="section-title">🚨 Model Health & Alerts</div>', unsafe_allow_html=True)

    models = get_model_performance_data()

    # Check for performance issues
    alerts = []

    for model_id, metrics in models.items():
        # Performance thresholds
        if metrics.roc_auc < 0.8:
            alerts.append({
                'level': 'error',
                'model': metrics.model_name,
                'message': f'ROC-AUC below threshold: {metrics.roc_auc:.3f} < 0.8'
            })

        if metrics.inference_latency > 100:
            alerts.append({
                'level': 'warning',
                'model': metrics.model_name,
                'message': f'High inference latency: {metrics.inference_latency:.1f}ms > 100ms'
            })

        if metrics.cache_hit_rate < 0.7:
            alerts.append({
                'level': 'warning',
                'model': metrics.model_name,
                'message': f'Low cache hit rate: {metrics.cache_hit_rate:.1%} < 70%'
            })

    if not alerts:
        st.markdown("""
        <div class="alert-box alert-success">
            <strong>✅ All Systems Operational</strong><br>
            All models are performing within expected parameters.
        </div>
        """, unsafe_allow_html=True)
    else:
        for alert in alerts:
            if alert['level'] == 'error':
                alert_class = 'alert-error'
                icon = '🚨'
            else:
                alert_class = 'alert-warning'
                icon = '⚠️'

            st.markdown(f"""
            <div class="alert-box {alert_class}">
                <strong>{icon} {alert['model']}</strong><br>
                {alert['message']}
            </div>
            """, unsafe_allow_html=True)

def main():
    """Main ML Scoring Dashboard application."""
    # Apply custom styling
    apply_ml_dashboard_styles()

    # Render header
    render_dashboard_header()

    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Model Overview",
        "📈 Performance Charts",
        "🧪 A/B Testing",
        "⚡ Inference Performance",
        "🚨 Health & Alerts"
    ])

    with tab1:
        render_model_performance_overview()

    with tab2:
        render_performance_visualizations()

    with tab3:
        render_ab_testing_dashboard()

    with tab4:
        render_inference_performance_dashboard()

    with tab5:
        render_model_health_alerts()

    # Footer with refresh controls
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Refresh Data", help="Refresh all dashboard data"):
            st.cache_data.clear()
            st.rerun()

    with col2:
        st.write(f"🕒 **Last Updated:** {datetime.now().strftime('%H:%M:%S')}")

    with col3:
        st.write("🤖 **ML Dashboard v1.0**")

if __name__ == "__main__":
    main()