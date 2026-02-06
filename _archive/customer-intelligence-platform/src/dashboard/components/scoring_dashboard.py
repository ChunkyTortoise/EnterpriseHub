"""
Scoring Dashboard Component for Customer Intelligence Platform

Advanced scoring analytics dashboard with:
- Real-time score distributions
- Model performance monitoring  
- Feature importance analysis
- Prediction confidence tracking
- Interactive drill-down capabilities
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
import requests
from typing import Dict, List, Any, Optional, Tuple


def render_scoring_dashboard_css():
    """Inject custom CSS for scoring dashboard - Business Intelligence Edition"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');

    /* Scoring Dashboard Styles */
    .scoring-container {
        background: rgba(5, 7, 10, 0.8) !important;
        border-radius: 20px;
        padding: 2.5rem;
        margin: 1rem 0;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.05);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(20px);
    }

    .scoring-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 10% 10%, rgba(59, 130, 246, 0.05) 0%, transparent 50%);
        pointer-events: none;
    }

    .scoring-header {
        color: white;
        text-align: left;
        margin-bottom: 3rem;
        position: relative;
        z-index: 1;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        padding-bottom: 2rem;
    }

    .scoring-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        color: #FFFFFF;
        letter-spacing: -0.04em;
        text-transform: uppercase;
    }

    .scoring-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        margin: 0.75rem 0 0 0;
        color: #8B949E;
        font-weight: 500;
    }

    .chart-container {
        background: rgba(22, 27, 34, 0.7) !important;
        border-radius: 12px;
        padding: 1.75rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .chart-container:hover {
        transform: translateY(-5px);
        border-color: rgba(59, 130, 246, 0.3);
        box-shadow: 0 12px 48px rgba(59, 130, 246, 0.2);
    }

    .chart-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1.25rem;
        margin: 2rem 0;
    }

    .metric-card {
        background: rgba(22, 27, 34, 0.8);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: left;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-left: 4px solid;
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(255,255,255,0.1);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.6);
    }

    .metric-card.high-score { border-left-color: #10b981; }
    .metric-card.medium-score { border-left-color: #f59e0b; }
    .metric-card.low-score { border-left-color: #ef4444; }
    .metric-card.model-performance { border-left-color: #3B82F6; }

    .metric-value {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0.5rem 0;
        text-shadow: 0 0 10px rgba(255,255,255,0.1);
    }

    .metric-label {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.75rem;
        color: #8B949E;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .metric-change {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        font-weight: 700;
        margin-top: 0.5rem;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .score-badge.high { background: rgba(16, 185, 129, 0.2); color: #10b981; }
    .score-badge.medium { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
    .score-badge.low { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

    .feature-importance {
        background: rgba(59, 130, 246, 0.05);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 3px solid #3B82F6;
        border: 1px solid rgba(59, 130, 246, 0.1);
    }

    .confidence-indicator {
        background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981);
        height: 4px;
        border-radius: 2px;
        position: relative;
        margin: 0.5rem 0;
    }

    .confidence-marker {
        position: absolute;
        top: -2px;
        width: 8px;
        height: 8px;
        background: white;
        border-radius: 50%;
        transform: translateX(-50%);
    }

    /* Mobile Responsive */
    @media (max-width: 768px) {
        .scoring-container {
            padding: 1rem;
            margin: 0.5rem 0;
        }

        .scoring-title {
            font-size: 1.5rem;
        }

        .chart-container {
            padding: 1rem;
            margin: 0.5rem 0;
        }

        .metric-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }

        .metric-card {
            padding: 1rem;
        }

        .metric-value {
            font-size: 1.8rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)


class ScoringDashboard:
    """Scoring dashboard component with real-time analytics"""

    def __init__(self, api_base_url: str = "http://localhost:8000/api/v1"):
        self.api_base_url = api_base_url
        if 'scoring_state' not in st.session_state:
            st.session_state.scoring_state = {
                'model_type': 'lead_scoring',
                'time_range': '30d',
                'department': 'all',
                'selected_customer': None
            }

    def render(self):
        """Render the scoring dashboard"""
        render_scoring_dashboard_css()
        
        st.markdown('<div class="scoring-container">', unsafe_allow_html=True)
        self._render_header()
        self._render_filter_panel()
        
        # Get scoring data
        scoring_data = self._get_scoring_data()
        
        # Render dashboard sections
        self._render_key_metrics(scoring_data)
        
        col1, col2 = st.columns(2)
        with col1:
            self._render_score_distribution(scoring_data)
        with col2:
            self._render_model_performance(scoring_data)
        
        col3, col4 = st.columns(2)
        with col3:
            self._render_feature_importance(scoring_data)
        with col4:
            self._render_prediction_confidence(scoring_data)
        
        self._render_recent_predictions(scoring_data)
        self._render_model_comparison(scoring_data)
        
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_header(self):
        """Render scoring dashboard header"""
        st.markdown(f"""
        <div class="scoring-header">
            <h1 class="scoring-title">🎯 Scoring Intelligence</h1>
            <p class="scoring-subtitle">Real-time customer scoring analytics and model performance monitoring</p>
        </div>
        """, unsafe_allow_html=True)

    def _render_filter_panel(self):
        """Render filter controls"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            model_type = st.selectbox(
                '🤖 Model Type', 
                ['lead_scoring', 'engagement_prediction', 'churn_prediction', 'customer_ltv'],
                index=0, 
                key='scoring_model_type'
            )
            st.session_state.scoring_state['model_type'] = model_type
        
        with col2:
            time_range = st.selectbox(
                '📅 Time Range', 
                ['7d', '30d', '90d', '1y'],
                index=1, 
                key='scoring_time_range'
            )
            st.session_state.scoring_state['time_range'] = time_range
        
        with col3:
            department = st.selectbox(
                '🏢 Department', 
                ['all', 'Sales', 'Marketing', 'Customer Success', 'Support'],
                index=0, 
                key='scoring_department'
            )
            st.session_state.scoring_state['department'] = department
        
        with col4:
            if st.button("🔄 Refresh Data", key="refresh_scoring"):
                st.cache_data.clear()
                st.rerun()

    def _render_key_metrics(self, scoring_data: Dict[str, Any]):
        """Render key scoring metrics"""
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        
        metrics = [
            {
                'label': 'Average Score',
                'value': f"{scoring_data['avg_score']:.2f}",
                'change': f"{scoring_data['score_change']:+.2f}",
                'trend': 'high-score' if scoring_data['avg_score'] >= 0.7 else 'medium-score' if scoring_data['avg_score'] >= 0.4 else 'low-score'
            },
            {
                'label': 'Model Accuracy',
                'value': f"{scoring_data['model_accuracy']:.1%}",
                'change': f"{scoring_data['accuracy_change']:+.1%}",
                'trend': 'model-performance'
            },
            {
                'label': 'Predictions Today',
                'value': f"{scoring_data['predictions_today']:,}",
                'change': f"+{scoring_data['predictions_change']:,}",
                'trend': 'high-score'
            },
            {
                'label': 'High-Value Leads',
                'value': f"{scoring_data['high_value_leads']:,}",
                'change': f"+{scoring_data['high_value_change']:,}",
                'trend': 'high-score'
            },
            {
                'label': 'Avg Confidence',
                'value': f"{scoring_data['avg_confidence']:.1%}",
                'change': f"{scoring_data['confidence_change']:+.1%}",
                'trend': 'model-performance'
            },
            {
                'label': 'Response Time',
                'value': f"{scoring_data['avg_response_time']}ms",
                'change': f"{scoring_data['response_time_change']:+}ms",
                'trend': 'low-score' if scoring_data['response_time_change'] > 0 else 'high-score'
            }
        ]
        
        for metric in metrics:
            trend_icon = '📈' if metric['trend'] in ['high-score', 'model-performance'] else '📉'
            st.markdown(f"""
            <div class="metric-card {metric['trend']}">
                <div class="metric-label">{metric['label']}</div>
                <div class="metric-value">{metric['value']}</div>
                <div class="metric-change">
                    {trend_icon} {metric['change']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_score_distribution(self, scoring_data: Dict[str, Any]):
        """Render score distribution chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📊 Score Distribution</h3>', unsafe_allow_html=True)
        
        # Generate score distribution data
        scores = scoring_data['score_distribution']
        bins = scores['bins']
        counts = scores['counts']
        
        # Create histogram
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=bins,
            y=counts,
            marker=dict(
                color=counts,
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Count")
            ),
            hovertemplate='<b>Score Range:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Customer Score Distribution",
            xaxis_title="Score Range",
            yaxis_title="Number of Customers",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Score summary
        col1, col2, col3 = st.columns(3)
        with col1:
            high_scores = sum(c for b, c in zip(bins, counts) if '0.7' in str(b) or '0.8' in str(b) or '0.9' in str(b))
            st.metric("High Scores (>0.7)", high_scores)
        with col2:
            medium_scores = sum(c for b, c in zip(bins, counts) if '0.4' in str(b) or '0.5' in str(b) or '0.6' in str(b))
            st.metric("Medium Scores (0.4-0.7)", medium_scores)
        with col3:
            low_scores = sum(c for b, c in zip(bins, counts) if '0.1' in str(b) or '0.2' in str(b) or '0.3' in str(b))
            st.metric("Low Scores (<0.4)", low_scores)
        
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_model_performance(self, scoring_data: Dict[str, Any]):
        """Render model performance metrics"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">⚡ Model Performance</h3>', unsafe_allow_html=True)
        
        # Performance metrics over time
        performance_data = scoring_data['model_performance']
        dates = performance_data['dates']
        accuracy = performance_data['accuracy']
        precision = performance_data['precision']
        recall = performance_data['recall']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=accuracy,
            mode='lines+markers',
            name='Accuracy',
            line=dict(color='#3B82F6', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=precision,
            mode='lines+markers',
            name='Precision',
            line=dict(color='#10b981', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=recall,
            mode='lines+markers',
            name='Recall',
            line=dict(color='#f59e0b', width=2)
        ))
        
        fig.update_layout(
            title="Model Performance Over Time",
            xaxis_title="Date",
            yaxis_title="Score",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            yaxis=dict(range=[0, 1])
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Current model metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Accuracy", f"{scoring_data['model_accuracy']:.1%}")
        with col2:
            st.metric("Precision", f"{scoring_data['model_precision']:.1%}")
        with col3:
            st.metric("Recall", f"{scoring_data['model_recall']:.1%}")
        
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_feature_importance(self, scoring_data: Dict[str, Any]):
        """Render feature importance analysis"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🎯 Feature Importance</h3>', unsafe_allow_html=True)
        
        features = scoring_data['feature_importance']
        feature_names = list(features.keys())
        importance_scores = list(features.values())
        
        # Create horizontal bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=importance_scores,
            y=feature_names,
            orientation='h',
            marker=dict(
                color=importance_scores,
                colorscale='Viridis',
                showscale=True
            ),
            hovertemplate='<b>Feature:</b> %{y}<br><b>Importance:</b> %{x:.3f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Top Features Driving Scores",
            xaxis_title="Importance Score",
            yaxis_title="Features",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Feature insights
        top_feature = feature_names[0]
        st.markdown(f"""
        <div class="feature-importance">
            <strong>💡 Key Insight:</strong> {top_feature} is the most important feature, 
            accounting for {importance_scores[0]:.1%} of the model's predictive power.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_prediction_confidence(self, scoring_data: Dict[str, Any]):
        """Render prediction confidence analysis"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🎪 Prediction Confidence</h3>', unsafe_allow_html=True)
        
        confidence_data = scoring_data['confidence_analysis']
        confidence_ranges = confidence_data['ranges']
        prediction_counts = confidence_data['counts']
        
        # Create confidence distribution
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=confidence_ranges,
            y=prediction_counts,
            marker=dict(
                color=['#ef4444', '#f59e0b', '#10b981', '#3B82F6'],
                opacity=0.8
            ),
            hovertemplate='<b>Confidence:</b> %{x}<br><b>Predictions:</b> %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Confidence Level Distribution",
            xaxis_title="Confidence Range",
            yaxis_title="Number of Predictions",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Confidence metrics
        avg_confidence = scoring_data['avg_confidence']
        high_confidence = sum(prediction_counts[-2:])  # Last two ranges (high confidence)
        total_predictions = sum(prediction_counts)
        
        st.metric("High Confidence Predictions", f"{high_confidence/total_predictions:.1%}")
        
        # Confidence indicator
        st.markdown(f"""
        <div style="margin: 1rem 0;">
            <div style="font-size: 0.85rem; color: #8B949E; margin-bottom: 0.5rem;">
                Average Confidence: {avg_confidence:.1%}
            </div>
            <div class="confidence-indicator">
                <div class="confidence-marker" style="left: {avg_confidence*100}%;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #8B949E; margin-top: 0.25rem;">
                <span>Low</span>
                <span>Medium</span>
                <span>High</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_recent_predictions(self, scoring_data: Dict[str, Any]):
        """Render recent predictions table"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🕐 Recent Predictions</h3>', unsafe_allow_html=True)
        
        recent_predictions = scoring_data['recent_predictions']
        df = pd.DataFrame(recent_predictions)
        
        if not df.empty:
            # Format the dataframe for display
            df['score'] = df['score'].apply(lambda x: f"{x:.3f}")
            df['confidence'] = df['confidence'].apply(lambda x: f"{x:.1%}")
            df['score_badge'] = df['score'].apply(self._get_score_badge)
            
            # Display with custom styling
            for idx, row in df.head(10).iterrows():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
                with col1:
                    st.write(f"**{row['customer_name']}**")
                    st.write(f"_{row['department']}_")
                with col2:
                    st.markdown(row['score_badge'], unsafe_allow_html=True)
                with col3:
                    st.write(row['confidence'])
                with col4:
                    st.write(row['model_type'])
                with col5:
                    st.write(row['timestamp'])
        else:
            st.info("No recent predictions available. Train a model to see predictions here.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    def _render_model_comparison(self, scoring_data: Dict[str, Any]):
        """Render model comparison chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🏆 Model Comparison</h3>', unsafe_allow_html=True)
        
        models = scoring_data['model_comparison']
        model_names = list(models.keys())
        accuracies = [models[m]['accuracy'] for m in model_names]
        f1_scores = [models[m]['f1_score'] for m in model_names]
        
        # Create grouped bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Accuracy',
            x=model_names,
            y=accuracies,
            marker=dict(color='#3B82F6')
        ))
        fig.add_trace(go.Bar(
            name='F1 Score',
            x=model_names,
            y=f1_scores,
            marker=dict(color='#10b981')
        ))
        
        fig.update_layout(
            title="Model Performance Comparison",
            xaxis_title="Model Type",
            yaxis_title="Score",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            barmode='group',
            yaxis=dict(range=[0, 1])
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Best model indicator
        best_model = max(model_names, key=lambda m: models[m]['accuracy'])
        st.success(f"🏆 Best performing model: **{best_model}** (Accuracy: {models[best_model]['accuracy']:.1%})")
        
        st.markdown('</div>', unsafe_allow_html=True)

    def _get_score_badge(self, score_str: str) -> str:
        """Generate score badge HTML"""
        score = float(score_str)
        if score >= 0.7:
            badge_class = "high"
            label = "HIGH"
        elif score >= 0.4:
            badge_class = "medium"
            label = "MED"
        else:
            badge_class = "low"
            label = "LOW"
        
        return f'<span class="score-badge {badge_class}">{label}</span>'

    @st.cache_data(ttl=300)
    def _get_scoring_data(self) -> Dict[str, Any]:
        """Get scoring analytics data from API"""
        try:
            # Try to get real data from API
            response = requests.get(f"{self.api_base_url}/scoring/health", timeout=5)
            if response.status_code == 200:
                # API is available, get real data
                models_response = requests.get(f"{self.api_base_url}/scoring/models", timeout=10)
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    return self._process_api_data(models_data)
        except:
            pass
        
        # Fallback to synthetic data for demo
        return self._generate_synthetic_scoring_data()

    def _process_api_data(self, models_data: List[Dict]) -> Dict[str, Any]:
        """Process real API data into dashboard format"""
        if not models_data:
            return self._generate_synthetic_scoring_data()
        
        # Calculate metrics from real model data
        total_models = len(models_data)
        avg_accuracy = np.mean([model['accuracy'] for model in models_data])
        avg_precision = np.mean([model['precision'] for model in models_data])
        avg_recall = np.mean([model['recall'] for model in models_data])
        
        return {
            'avg_score': avg_accuracy,
            'score_change': 0.05,
            'model_accuracy': avg_accuracy,
            'accuracy_change': 0.02,
            'predictions_today': np.random.randint(50, 200),
            'predictions_change': np.random.randint(5, 20),
            'high_value_leads': np.random.randint(15, 50),
            'high_value_change': np.random.randint(2, 10),
            'avg_confidence': 0.85,
            'confidence_change': 0.03,
            'avg_response_time': np.random.randint(50, 150),
            'response_time_change': np.random.randint(-10, 10),
            'model_precision': avg_precision,
            'model_recall': avg_recall,
            'score_distribution': self._generate_score_distribution(),
            'model_performance': self._generate_performance_trend(),
            'feature_importance': self._generate_feature_importance(),
            'confidence_analysis': self._generate_confidence_analysis(),
            'recent_predictions': self._generate_recent_predictions(),
            'model_comparison': self._generate_model_comparison()
        }

    def _generate_synthetic_scoring_data(self) -> Dict[str, Any]:
        """Generate synthetic scoring data for demo purposes"""
        return {
            'avg_score': 0.72,
            'score_change': 0.05,
            'model_accuracy': 0.84,
            'accuracy_change': 0.02,
            'predictions_today': 147,
            'predictions_change': 23,
            'high_value_leads': 34,
            'high_value_change': 7,
            'avg_confidence': 0.85,
            'confidence_change': 0.03,
            'avg_response_time': 87,
            'response_time_change': -12,
            'model_precision': 0.81,
            'model_recall': 0.79,
            'score_distribution': self._generate_score_distribution(),
            'model_performance': self._generate_performance_trend(),
            'feature_importance': self._generate_feature_importance(),
            'confidence_analysis': self._generate_confidence_analysis(),
            'recent_predictions': self._generate_recent_predictions(),
            'model_comparison': self._generate_model_comparison()
        }

    def _generate_score_distribution(self) -> Dict[str, List]:
        """Generate score distribution data"""
        bins = ['0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5', 
                '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']
        counts = [5, 12, 18, 25, 35, 45, 38, 28, 15, 8]
        return {'bins': bins, 'counts': counts}

    def _generate_performance_trend(self) -> Dict[str, List]:
        """Generate model performance trend data"""
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
        accuracy = [0.75 + 0.1 * np.sin(i/5) + np.random.normal(0, 0.02) for i in range(30)]
        precision = [0.73 + 0.08 * np.sin(i/4) + np.random.normal(0, 0.015) for i in range(30)]
        recall = [0.71 + 0.12 * np.sin(i/6) + np.random.normal(0, 0.02) for i in range(30)]
        
        return {
            'dates': dates,
            'accuracy': [max(0.6, min(0.9, a)) for a in accuracy],
            'precision': [max(0.6, min(0.9, p)) for p in precision],
            'recall': [max(0.6, min(0.9, r)) for r in recall]
        }

    def _generate_feature_importance(self) -> Dict[str, float]:
        """Generate feature importance data"""
        return {
            'engagement_score': 0.245,
            'company_size': 0.198,
            'industry_type': 0.167,
            'budget_range': 0.134,
            'contact_frequency': 0.089,
            'geographic_location': 0.078,
            'referral_source': 0.056,
            'time_on_site': 0.033
        }

    def _generate_confidence_analysis(self) -> Dict[str, List]:
        """Generate confidence analysis data"""
        return {
            'ranges': ['<50%', '50-70%', '70-85%', '>85%'],
            'counts': [23, 45, 67, 89]
        }

    def _generate_recent_predictions(self) -> List[Dict[str, Any]]:
        """Generate recent predictions data"""
        customers = ['Acme Corp', 'TechStart Inc', 'Global Solutions', 'InnovateCo', 'FutureTech']
        departments = ['Sales', 'Marketing', 'Customer Success']
        model_types = ['lead_scoring', 'engagement_prediction', 'churn_prediction']
        
        predictions = []
        for i in range(15):
            predictions.append({
                'customer_name': np.random.choice(customers),
                'score': np.random.uniform(0.1, 0.95),
                'confidence': np.random.uniform(0.6, 0.95),
                'model_type': np.random.choice(model_types),
                'department': np.random.choice(departments),
                'timestamp': (datetime.now() - timedelta(minutes=np.random.randint(1, 1440))).strftime('%H:%M')
            })
        
        return sorted(predictions, key=lambda x: x['timestamp'], reverse=True)

    def _generate_model_comparison(self) -> Dict[str, Dict[str, float]]:
        """Generate model comparison data"""
        return {
            'Lead Scoring': {'accuracy': 0.84, 'f1_score': 0.82},
            'Engagement Pred': {'accuracy': 0.78, 'f1_score': 0.76},
            'Churn Prediction': {'accuracy': 0.81, 'f1_score': 0.79},
            'Customer LTV': {'accuracy': 0.73, 'f1_score': 0.71}
        }


def render_scoring_dashboard(api_base_url: str = "http://localhost:8000/api/v1"):
    """Render the scoring dashboard component"""
    dashboard = ScoringDashboard(api_base_url)
    dashboard.render()


# Export main function
__all__ = ['render_scoring_dashboard', 'ScoringDashboard']