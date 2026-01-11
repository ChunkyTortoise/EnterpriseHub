"""
Churn Early Warning Dashboard - Real-time Churn Risk Monitoring

This component provides a comprehensive dashboard for monitoring churn risk across
the lead portfolio with real-time alerts, risk distribution analytics, and
intervention tracking capabilities.

Features:
- Real-time churn risk monitoring with automatic refresh
- Risk distribution charts and trend analysis
- High-risk lead priority queue with intervention recommendations
- Intervention effectiveness tracking and analytics
- Predictive insights and early warning alerts
- Agent workload distribution and performance metrics

Author: EnterpriseHub AI
Last Updated: 2026-01-09
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import asyncio
import json
from typing import Dict, List, Optional, Any
import numpy as np

# Component styling and configuration - only when run standalone
if __name__ == "__main__":
    st.set_page_config(
        page_title="Churn Early Warning System",
        page_icon="⚠️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Custom CSS for enhanced styling
st.markdown("""
<style>
    .metric-container {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .risk-critical {
        background: linear-gradient(135deg, #ff4757, #ff3742);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 4px solid #c23616;
    }

    .risk-high {
        background: linear-gradient(135deg, #ffa726, #ff9800);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 4px solid #e65100;
    }

    .risk-medium {
        background: linear-gradient(135deg, #66bb6a, #4caf50);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 4px solid #2e7d32;
    }

    .risk-low {
        background: linear-gradient(135deg, #42a5f5, #2196f3);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 4px solid #0d47a1;
    }

    .alert-banner {
        background: linear-gradient(45deg, #ff6b6b, #ee5a52);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }

    .intervention-success {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
    }

    .intervention-pending {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
    }

    .intervention-failed {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
    }
</style>
""", unsafe_allow_html=True)

class ChurnEarlyWarningDashboard:
    """Main dashboard class for churn risk monitoring"""

    def __init__(self):
        self.refresh_interval = 300  # 5 minutes
        self.risk_thresholds = {
            'critical': 80.0,
            'high': 60.0,
            'medium': 30.0,
            'low': 0.0
        }

    def render_dashboard(self):
        """Render the complete early warning dashboard"""
        st.title("🚨 Churn Early Warning Dashboard")
        st.markdown("*Real-time monitoring of lead churn risk and intervention effectiveness*")

        # Auto-refresh mechanism
        if st.button("🔄 Refresh Data", key="refresh_dashboard"):
            st.rerun()

        # Load dashboard data
        with st.spinner("Loading churn risk data..."):
            dashboard_data = self._load_dashboard_data()

        # Main dashboard layout
        self._render_alert_banner(dashboard_data)
        self._render_key_metrics(dashboard_data)

        # Create three columns for main content
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            self._render_risk_distribution_chart(dashboard_data)
            self._render_risk_trend_analysis(dashboard_data)

        with col2:
            self._render_intervention_effectiveness(dashboard_data)
            self._render_agent_workload_distribution(dashboard_data)

        with col3:
            self._render_high_risk_queue(dashboard_data)

        # Detailed sections
        st.markdown("---")
        self._render_detailed_analytics(dashboard_data)
        self._render_intervention_tracking(dashboard_data)

    def _load_dashboard_data(self) -> Dict[str, Any]:
        """Load and prepare dashboard data"""
        # In production, this would load from actual services
        # For demo purposes, generating realistic sample data

        current_time = datetime.now()

        # Sample churn predictions
        sample_predictions = [
            {
                'lead_id': f'LEAD_{i:04d}',
                'lead_name': f'Client {i}',
                'risk_score_14d': np.random.beta(2, 5) * 100,  # Skewed toward lower scores
                'risk_tier': self._calculate_risk_tier(np.random.beta(2, 5) * 100),
                'confidence': np.random.uniform(0.6, 0.95),
                'last_interaction_days': np.random.exponential(5),
                'predicted_churn_date': current_time + timedelta(days=np.random.uniform(3, 30)),
                'top_risk_factors': [
                    ('days_since_last_interaction', np.random.uniform(0.1, 0.3)),
                    ('response_rate_7d', np.random.uniform(0.1, 0.25)),
                    ('engagement_trend', np.random.uniform(0.05, 0.2))
                ]
            }
            for i in range(1, 151)  # 150 sample leads
        ]

        # Sample intervention data
        sample_interventions = [
            {
                'execution_id': f'INT_{i:04d}',
                'lead_id': f'LEAD_{np.random.randint(1, 151):04d}',
                'intervention_type': np.random.choice([
                    'email_reengagement', 'sms_urgent', 'phone_callback',
                    'property_alert', 'agent_escalation'
                ]),
                'status': np.random.choice(['completed', 'pending', 'failed'], p=[0.7, 0.2, 0.1]),
                'scheduled_time': current_time - timedelta(hours=np.random.uniform(0, 72)),
                'success_metrics': {
                    'engagement_increase': np.random.uniform(0, 30) if np.random.random() > 0.3 else 0
                }
            }
            for i in range(1, 101)  # 100 sample interventions
        ]

        return {
            'predictions': sample_predictions,
            'interventions': sample_interventions,
            'last_updated': current_time,
            'total_leads': len(sample_predictions),
            'high_risk_count': len([p for p in sample_predictions if p['risk_score_14d'] >= 60]),
            'critical_alerts': len([p for p in sample_predictions if p['risk_score_14d'] >= 80])
        }

    def _calculate_risk_tier(self, score: float) -> str:
        """Calculate risk tier based on score"""
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 30:
            return 'medium'
        else:
            return 'low'

    def _render_alert_banner(self, data: Dict[str, Any]):
        """Render critical alert banner if needed"""
        critical_count = data['critical_alerts']

        if critical_count > 0:
            st.markdown(
                f'<div class="alert-banner">🚨 CRITICAL ALERT: {critical_count} leads require immediate intervention!</div>',
                unsafe_allow_html=True
            )

    def _render_key_metrics(self, data: Dict[str, Any]):
        """Render key performance metrics"""
        st.subheader("📊 Key Metrics Overview")

        col1, col2, col3, col4, col5 = st.columns(5)

        predictions = data['predictions']
        interventions = data['interventions']

        # Calculate metrics
        total_leads = len(predictions)
        critical_risk = len([p for p in predictions if p['risk_score_14d'] >= 80])
        high_risk = len([p for p in predictions if p['risk_score_14d'] >= 60])
        avg_risk_score = np.mean([p['risk_score_14d'] for p in predictions])

        # Intervention metrics
        completed_interventions = len([i for i in interventions if i['status'] == 'completed'])
        intervention_success_rate = completed_interventions / len(interventions) * 100 if interventions else 0

        with col1:
            st.metric(
                label="Total Leads",
                value=f"{total_leads:,}",
                delta=f"+{np.random.randint(1, 5)} today"
            )

        with col2:
            st.metric(
                label="Critical Risk",
                value=f"{critical_risk}",
                delta=f"{'+' if critical_risk > 2 else ''}{critical_risk - 2 if critical_risk > 2 else critical_risk - 2}",
                delta_color="inverse"
            )

        with col3:
            st.metric(
                label="High Risk",
                value=f"{high_risk}",
                delta=f"{'+' if high_risk > 8 else ''}{high_risk - 8 if high_risk > 8 else high_risk - 8}",
                delta_color="inverse"
            )

        with col4:
            st.metric(
                label="Avg Risk Score",
                value=f"{avg_risk_score:.1f}%",
                delta=f"{avg_risk_score - 35:.1f}%"
            )

        with col5:
            st.metric(
                label="Intervention Success",
                value=f"{intervention_success_rate:.1f}%",
                delta=f"+{intervention_success_rate - 65:.1f}%"
            )

    def _render_risk_distribution_chart(self, data: Dict[str, Any]):
        """Render risk distribution visualization"""
        st.subheader("📈 Risk Distribution Analysis")

        predictions = data['predictions']
        risk_df = pd.DataFrame(predictions)

        # Risk tier distribution
        risk_counts = risk_df['risk_tier'].value_counts()

        fig = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            title="Lead Distribution by Risk Tier",
            color_discrete_map={
                'critical': '#ff4757',
                'high': '#ffa726',
                'medium': '#66bb6a',
                'low': '#42a5f5'
            }
        )

        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=True, height=400)

        st.plotly_chart(fig, width='stretch')

        # Risk score histogram
        fig2 = px.histogram(
            risk_df,
            x='risk_score_14d',
            nbins=20,
            title="Risk Score Distribution",
            color_discrete_sequence=['#3498db']
        )

        # Add risk threshold lines
        fig2.add_vline(x=80, line_dash="dash", line_color="red", annotation_text="Critical (80%)")
        fig2.add_vline(x=60, line_dash="dash", line_color="orange", annotation_text="High (60%)")
        fig2.add_vline(x=30, line_dash="dash", line_color="green", annotation_text="Medium (30%)")

        fig2.update_layout(
            xaxis_title="14-Day Risk Score (%)",
            yaxis_title="Number of Leads",
            height=350
        )

        st.plotly_chart(fig2, width='stretch')

    def _render_risk_trend_analysis(self, data: Dict[str, Any]):
        """Render risk trend analysis"""
        st.subheader("📉 Risk Trend Analysis")

        # Generate sample trend data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')

        # Simulate trend data
        np.random.seed(42)  # For consistent demo data
        critical_trend = np.random.poisson(3, len(dates)) + np.sin(np.arange(len(dates)) * 0.2) * 2
        high_trend = np.random.poisson(8, len(dates)) + np.sin(np.arange(len(dates)) * 0.15) * 3

        trend_df = pd.DataFrame({
            'date': dates,
            'critical_risk': np.maximum(0, critical_trend),
            'high_risk': np.maximum(0, high_trend),
            'total_risk': np.maximum(0, critical_trend + high_trend)
        })

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=trend_df['date'],
            y=trend_df['critical_risk'],
            mode='lines+markers',
            name='Critical Risk',
            line=dict(color='#ff4757', width=3),
            fill='tonexty'
        ))

        fig.add_trace(go.Scatter(
            x=trend_df['date'],
            y=trend_df['high_risk'],
            mode='lines+markers',
            name='High Risk',
            line=dict(color='#ffa726', width=2)
        ))

        fig.update_layout(
            title="30-Day Risk Trend",
            xaxis_title="Date",
            yaxis_title="Number of High-Risk Leads",
            height=350,
            hovermode='x unified'
        )

        st.plotly_chart(fig, width='stretch')

    def _render_intervention_effectiveness(self, data: Dict[str, Any]):
        """Render intervention effectiveness metrics"""
        st.subheader("🎯 Intervention Effectiveness")

        interventions = data['interventions']
        intervention_df = pd.DataFrame(interventions)

        # Success rate by intervention type
        success_rates = []
        intervention_types = intervention_df['intervention_type'].unique()

        for int_type in intervention_types:
            type_interventions = intervention_df[intervention_df['intervention_type'] == int_type]
            success_rate = len(type_interventions[type_interventions['status'] == 'completed']) / len(type_interventions) * 100
            success_rates.append({'type': int_type, 'success_rate': success_rate})

        success_df = pd.DataFrame(success_rates)

        fig = px.bar(
            success_df,
            x='type',
            y='success_rate',
            title="Success Rate by Intervention Type",
            color='success_rate',
            color_continuous_scale='RdYlGn'
        )

        fig.update_layout(
            xaxis_title="Intervention Type",
            yaxis_title="Success Rate (%)",
            height=350,
            xaxis_tickangle=45
        )

        st.plotly_chart(fig, width='stretch')

        # Intervention timeline
        intervention_df['scheduled_time'] = pd.to_datetime(intervention_df['scheduled_time'])
        daily_interventions = intervention_df.groupby(intervention_df['scheduled_time'].dt.date).size()

        fig2 = px.line(
            x=daily_interventions.index,
            y=daily_interventions.values,
            title="Daily Intervention Volume",
            markers=True
        )

        fig2.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Interventions",
            height=300
        )

        st.plotly_chart(fig2, width='stretch')

    def _render_agent_workload_distribution(self, data: Dict[str, Any]):
        """Render agent workload distribution"""
        st.subheader("👥 Agent Workload Distribution")

        # Simulate agent assignments
        agent_names = ['Sarah Miller', 'Mike Johnson', 'Emma Davis', 'Alex Chen', 'Lisa Rodriguez']
        agent_workloads = []

        for agent in agent_names:
            critical_leads = np.random.randint(0, 8)
            high_risk_leads = np.random.randint(2, 15)
            total_interventions = np.random.randint(5, 25)

            agent_workloads.append({
                'agent': agent,
                'critical_leads': critical_leads,
                'high_risk_leads': high_risk_leads,
                'total_interventions': total_interventions,
                'workload_score': critical_leads * 3 + high_risk_leads * 2 + total_interventions
            })

        workload_df = pd.DataFrame(agent_workloads)

        # Workload balance chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Critical Leads',
            x=workload_df['agent'],
            y=workload_df['critical_leads'],
            marker_color='#ff4757'
        ))

        fig.add_trace(go.Bar(
            name='High Risk Leads',
            x=workload_df['agent'],
            y=workload_df['high_risk_leads'],
            marker_color='#ffa726'
        ))

        fig.update_layout(
            title="Agent Risk Lead Distribution",
            barmode='stack',
            height=300,
            xaxis_tickangle=45
        )

        st.plotly_chart(fig, width='stretch')

        # Workload balance table
        st.subheader("Workload Balance")
        workload_display = workload_df[['agent', 'critical_leads', 'high_risk_leads', 'total_interventions', 'workload_score']]
        workload_display.columns = ['Agent', 'Critical', 'High Risk', 'Interventions', 'Score']
        st.dataframe(workload_display, width='stretch')

    def _render_high_risk_queue(self, data: Dict[str, Any]):
        """Render high-risk leads priority queue"""
        st.subheader("🚨 Priority Intervention Queue")

        predictions = data['predictions']

        # Filter and sort high-risk leads
        high_risk_leads = [p for p in predictions if p['risk_score_14d'] >= 60]
        high_risk_leads.sort(key=lambda x: x['risk_score_14d'], reverse=True)

        # Display top 10 high-risk leads
        for i, lead in enumerate(high_risk_leads[:10]):
            risk_class = f"risk-{lead['risk_tier']}"

            with st.container():
                st.markdown(f"""
                <div class="{risk_class}">
                    <strong>{lead['lead_name']}</strong><br>
                    Risk Score: {lead['risk_score_14d']:.1f}%<br>
                    Last Contact: {lead['last_interaction_days']:.0f} days ago<br>
                    Confidence: {lead['confidence']:.0%}
                </div>
                """, unsafe_allow_html=True)

                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📞 Call", key=f"call_{lead['lead_id']}"):
                        st.success(f"Call initiated for {lead['lead_name']}")

                with col2:
                    if st.button(f"✉️ Email", key=f"email_{lead['lead_id']}"):
                        st.success(f"Email sent to {lead['lead_name']}")

        if len(high_risk_leads) > 10:
            st.info(f"Showing top 10 of {len(high_risk_leads)} high-risk leads")

    def _render_detailed_analytics(self, data: Dict[str, Any]):
        """Render detailed analytics section"""
        st.subheader("📊 Detailed Analytics")

        tab1, tab2, tab3, tab4 = st.tabs([
            "Risk Factor Analysis",
            "Intervention Performance",
            "Lead Journey Mapping",
            "Predictive Insights"
        ])

        with tab1:
            self._render_risk_factor_analysis(data)

        with tab2:
            self._render_intervention_performance_details(data)

        with tab3:
            self._render_lead_journey_mapping(data)

        with tab4:
            self._render_predictive_insights(data)

    def _render_risk_factor_analysis(self, data: Dict[str, Any]):
        """Detailed risk factor analysis"""
        st.write("### Primary Risk Factors Contributing to Churn")

        # Aggregate risk factors
        factor_importance = {
            'days_since_last_interaction': 0.28,
            'response_rate_7d': 0.22,
            'engagement_trend': 0.18,
            'stage_stagnation_days': 0.12,
            'email_open_rate': 0.10,
            'call_pickup_rate': 0.06,
            'qualification_score_change': 0.04
        }

        factor_df = pd.DataFrame(list(factor_importance.items()), columns=['Factor', 'Importance'])
        factor_df['Importance_Pct'] = factor_df['Importance'] * 100

        fig = px.bar(
            factor_df,
            x='Importance_Pct',
            y='Factor',
            orientation='h',
            title="Risk Factor Importance Rankings",
            color='Importance_Pct',
            color_continuous_scale='Reds'
        )

        fig.update_layout(height=400)
        st.plotly_chart(fig, width='stretch')

        # Factor correlation matrix
        st.write("### Risk Factor Correlations")

        # Generate sample correlation data
        factors = list(factor_importance.keys())[:5]  # Top 5 factors
        correlation_matrix = np.random.rand(len(factors), len(factors))
        correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2  # Make symmetric
        np.fill_diagonal(correlation_matrix, 1)  # Diagonal = 1

        fig = px.imshow(
            correlation_matrix,
            x=factors,
            y=factors,
            color_continuous_scale='RdBu',
            aspect='auto',
            title="Risk Factor Correlation Heatmap"
        )

        fig.update_layout(height=400)
        st.plotly_chart(fig, width='stretch')

    def _render_intervention_performance_details(self, data: Dict[str, Any]):
        """Detailed intervention performance analysis"""
        st.write("### Intervention ROI Analysis")

        # Sample intervention ROI data
        intervention_roi = {
            'email_reengagement': {'cost': 5, 'success_rate': 65, 'avg_revenue_impact': 1200},
            'sms_urgent': {'cost': 8, 'success_rate': 75, 'avg_revenue_impact': 1800},
            'phone_callback': {'cost': 25, 'success_rate': 85, 'avg_revenue_impact': 2500},
            'agent_escalation': {'cost': 100, 'success_rate': 90, 'avg_revenue_impact': 3500}
        }

        roi_data = []
        for intervention, metrics in intervention_roi.items():
            roi = (metrics['avg_revenue_impact'] * metrics['success_rate'] / 100) / metrics['cost']
            roi_data.append({
                'intervention': intervention,
                'cost': metrics['cost'],
                'success_rate': metrics['success_rate'],
                'avg_revenue': metrics['avg_revenue_impact'],
                'roi': roi
            })

        roi_df = pd.DataFrame(roi_data)

        fig = px.scatter(
            roi_df,
            x='success_rate',
            y='avg_revenue',
            size='roi',
            color='intervention',
            title="Intervention Performance: Success Rate vs Revenue Impact",
            labels={
                'success_rate': 'Success Rate (%)',
                'avg_revenue': 'Average Revenue Impact ($)'
            }
        )

        st.plotly_chart(fig, width='stretch')

        # ROI ranking
        roi_df_sorted = roi_df.sort_values('roi', ascending=False)
        st.write("### ROI Rankings")
        st.dataframe(
            roi_df_sorted[['intervention', 'cost', 'success_rate', 'avg_revenue', 'roi']].round(2),
            width='stretch'
        )

    def _render_lead_journey_mapping(self, data: Dict[str, Any]):
        """Lead journey and churn risk mapping"""
        st.write("### Lead Journey Risk Progression")

        # Sample journey stages with risk progression
        journey_stages = [
            'Initial Contact', 'Qualification', 'Property Search',
            'Property Viewing', 'Offer Preparation', 'Negotiation', 'Closing'
        ]

        # Risk levels at each stage (sample data)
        stage_risks = [15, 25, 35, 45, 30, 20, 10]  # Risk decreases after offer

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=journey_stages,
            y=stage_risks,
            mode='lines+markers',
            name='Average Risk Level',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=10)
        ))

        # Add risk threshold lines
        fig.add_hline(y=30, line_dash="dash", line_color="orange", annotation_text="Medium Risk Threshold")
        fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="High Risk Threshold")

        fig.update_layout(
            title="Churn Risk by Lead Journey Stage",
            xaxis_title="Journey Stage",
            yaxis_title="Average Churn Risk (%)",
            height=400,
            xaxis_tickangle=45
        )

        st.plotly_chart(fig, width='stretch')

    def _render_predictive_insights(self, data: Dict[str, Any]):
        """Predictive insights and recommendations"""
        st.write("### Predictive Insights & Recommendations")

        # Key insights
        insights = [
            {
                'insight': 'Email Engagement Drop',
                'description': 'Leads with <30% email open rate in past 7 days have 75% higher churn risk',
                'action': 'Switch to SMS or phone outreach',
                'urgency': 'High'
            },
            {
                'insight': 'Stage Stagnation Alert',
                'description': 'Leads stuck in Property Search stage >14 days show 60% churn probability',
                'action': 'Schedule consultation to address barriers',
                'urgency': 'Medium'
            },
            {
                'insight': 'Response Pattern Change',
                'description': 'Sudden drop in response rate indicates 80% churn risk within 7 days',
                'action': 'Immediate agent escalation required',
                'urgency': 'Critical'
            },
            {
                'insight': 'Weekend Engagement',
                'description': 'Leads who engage on weekends have 40% lower churn risk',
                'action': 'Prioritize weekend property viewings',
                'urgency': 'Low'
            }
        ]

        for insight in insights:
            urgency_color = {
                'Critical': '#ff4757',
                'High': '#ffa726',
                'Medium': '#66bb6a',
                'Low': '#42a5f5'
            }

            st.markdown(f"""
            <div style="border-left: 4px solid {urgency_color[insight['urgency']]};
                        padding: 1rem; margin: 1rem 0; background: #f8f9fa;">
                <h4 style="color: {urgency_color[insight['urgency']]}; margin: 0;">
                    {insight['insight']} ({insight['urgency']} Priority)
                </h4>
                <p style="margin: 0.5rem 0;"><strong>Finding:</strong> {insight['description']}</p>
                <p style="margin: 0;"><strong>Recommended Action:</strong> {insight['action']}</p>
            </div>
            """, unsafe_allow_html=True)

    def _render_intervention_tracking(self, data: Dict[str, Any]):
        """Render intervention tracking section"""
        st.subheader("📋 Active Intervention Tracking")

        interventions = data['interventions']

        # Create tabs for different intervention statuses
        tab1, tab2, tab3 = st.tabs(["Pending", "Active", "Completed"])

        with tab1:
            pending_interventions = [i for i in interventions if i['status'] == 'pending']
            if pending_interventions:
                st.write(f"**{len(pending_interventions)} interventions pending execution**")

                for intervention in pending_interventions[:10]:
                    with st.container():
                        col1, col2, col3 = st.columns([2, 2, 1])

                        with col1:
                            st.write(f"**{intervention['lead_id']}**")
                            st.write(f"Type: {intervention['intervention_type']}")

                        with col2:
                            st.write(f"Scheduled: {intervention['scheduled_time'].strftime('%H:%M')}")
                            st.write("Status: ⏳ Pending")

                        with col3:
                            if st.button("Execute Now", key=f"exec_{intervention['execution_id']}"):
                                st.success("Intervention executed!")
            else:
                st.info("No pending interventions")

        with tab2:
            # Show interventions in progress (for demo, treating recent ones as active)
            recent_interventions = [i for i in interventions if i['status'] == 'completed' and
                                  (datetime.now() - i['scheduled_time']).hours < 2]

            if recent_interventions:
                st.write(f"**{len(recent_interventions)} interventions recently executed**")

                for intervention in recent_interventions:
                    st.markdown(f"""
                    <div class="intervention-success">
                        <strong>{intervention['lead_id']}</strong> - {intervention['intervention_type']}<br>
                        Status: ✅ Recently Completed<br>
                        Engagement Increase: {intervention['success_metrics'].get('engagement_increase', 0):.1f}%
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No active interventions")

        with tab3:
            completed_interventions = [i for i in interventions if i['status'] == 'completed']

            if completed_interventions:
                success_count = len([i for i in completed_interventions
                                   if i['success_metrics'].get('engagement_increase', 0) > 0])
                success_rate = success_count / len(completed_interventions) * 100

                st.metric(
                    label="Completed Interventions Success Rate",
                    value=f"{success_rate:.1f}%",
                    delta=f"+{success_rate - 65:.1f}%"
                )

                # Show recent completed interventions
                recent_completed = sorted(completed_interventions,
                                        key=lambda x: x['scheduled_time'], reverse=True)[:5]

                for intervention in recent_completed:
                    engagement_increase = intervention['success_metrics'].get('engagement_increase', 0)
                    success_class = "intervention-success" if engagement_increase > 0 else "intervention-failed"

                    st.markdown(f"""
                    <div class="{success_class}">
                        <strong>{intervention['lead_id']}</strong> - {intervention['intervention_type']}<br>
                        Completed: {intervention['scheduled_time'].strftime('%m/%d %H:%M')}<br>
                        Engagement Impact: {'✅' if engagement_increase > 0 else '❌'} {engagement_increase:.1f}%
                    </div>
                    """, unsafe_allow_html=True)

# Main execution
def main():
    """Main function to run the dashboard"""
    dashboard = ChurnEarlyWarningDashboard()
    dashboard.render_dashboard()

if __name__ == "__main__":
    main()