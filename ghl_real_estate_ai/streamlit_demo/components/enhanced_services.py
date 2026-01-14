"""
Enhanced Services - AI Lead Intelligence Component

Provides comprehensive behavioral insights and analytics for leads including:
- Health score visualization
- Engagement timeline tracking
- Sentiment analysis
- Property interest heatmap
- Urgency indicators
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def render_ai_lead_insights(lead_data):
    """
    Renders comprehensive AI-powered lead intelligence visualizations
    
    Args:
        lead_data (dict): Lead information including:
            - name, health_score, engagement_level
            - last_contact, communication_preference
            - urgency_indicators, extracted_preferences
            - conversation_history
    """
    
    st.markdown("### 🧠 AI Lead Intelligence")
    st.markdown("*Deep behavioral analysis powered by Claude AI*")
    
    # Section 1: Health Score Overview
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.markdown("#### 💓 Lead Health Score")
        
        health_score = lead_data.get('health_score', 75)
        
        # Health Score Gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Engagement Health", 'font': {'size': 14, 'color': '#1e293b'}},
            number={'font': {'size': 36, 'color': '#1e293b'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#64748b", 'tickfont': {'color': '#475569'}},
                'bar': {'color': "#10b981" if health_score >= 70 else "#f59e0b" if health_score >= 40 else "#ef4444"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#e2e8f0",
                'steps': [
                    {'range': [0, 40], 'color': '#fee2e2'},
                    {'range': [40, 70], 'color': '#fef3c7'},
                    {'range': [70, 100], 'color': '#d1fae5'}
                ],
                'threshold': {
                    'line': {'color': "#10b981", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        
        fig.update_layout(
            height=240,
            margin=dict(t=30, b=10, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': '#1e293b'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Key Metrics
        engagement_level = lead_data.get('engagement_level', 'medium')
        comm_pref = lead_data.get('communication_preference', 'text')
        
        st.markdown(f"""
        <div style='background: white; padding: 1rem; border-radius: 12px; border: 1px solid #e2e8f0; margin-top: 1rem;'>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;'>
                <div>
                    <div style='color: #64748b; font-size: 0.7rem; text-transform: uppercase;'>Engagement</div>
                    <div style='color: #1e293b; font-weight: 600; margin-top: 2px;'>{engagement_level.title()}</div>
                </div>
                <div>
                    <div style='color: #64748b; font-size: 0.7rem; text-transform: uppercase;'>Preferred</div>
                    <div style='color: #1e293b; font-weight: 600; margin-top: 2px;'>{comm_pref.upper()}</div>
                </div>
                <div>
                    <div style='color: #64748b; font-size: 0.7rem; text-transform: uppercase;'>Last Contact</div>
                    <div style='color: #1e293b; font-weight: 600; margin-top: 2px;'>{lead_data.get('last_contact', 'N/A')}</div>
                </div>
                <div>
                    <div style='color: #64748b; font-size: 0.7rem; text-transform: uppercase;'>Stage</div>
                    <div style='color: #1e293b; font-weight: 600; margin-top: 2px;'>{lead_data.get('stage', 'N/A').title()}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Section 2: Engagement Timeline
        st.markdown("#### 📈 30-Day Engagement Timeline")
        
        # Generate sample timeline data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        # Simulate engagement activity
        np.random.seed(42)
        base_activity = np.random.poisson(3, 30)
        activity_scores = np.maximum(0, base_activity + np.random.normal(0, 1, 30))
        
        timeline_df = pd.DataFrame({
            'date': dates,
            'activity': activity_scores,
            'type': np.random.choice(['email', 'sms', 'property_view', 'form'], 30)
        })
        
        # Create timeline chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timeline_df['date'],
            y=timeline_df['activity'],
            mode='lines+markers',
            name='Activity Score',
            line={'color': '#2563eb', 'width': 2, 'shape': 'spline'},
            fill='tozeroy',
            fillcolor='rgba(37, 99, 235, 0.1)',
            marker={'size': 6, 'color': '#2563eb'}
        ))
        
        # Add event markers
        key_events = [
            {'date': dates[5], 'y': activity_scores[5], 'text': '📧 Email Open'},
            {'date': dates[15], 'y': activity_scores[15], 'text': '🏠 Property View'},
            {'date': dates[25], 'y': activity_scores[25], 'text': '📝 Form Submit'}
        ]
        
        for event in key_events:
            fig.add_annotation(
                x=event['date'],
                y=event['y'],
                text=event['text'],
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="#64748b",
                font={'size': 10, 'color': '#1e293b'},
                bgcolor="white",
                bordercolor="#e2e8f0",
                borderwidth=1
            )
        
        fig.update_layout(
            xaxis_title=None,
            yaxis_title="Activity Level",
            height=240,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            hovermode='x unified'
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Section 3: Sentiment Analysis & Property Interest
    st.markdown("---")
    col3, col4 = st.columns([1, 1])
    
    with col3:
        st.markdown("#### 😊 Sentiment Analysis")
        
        # Sample sentiment data
        sentiments = {
            'Positive': 72,
            'Neutral': 20,
            'Negative': 8
        }
        
        sentiment_df = pd.DataFrame({
            'sentiment': sentiments.keys(),
            'percentage': sentiments.values()
        })
        
        # Sentiment donut chart
        colors = {'Positive': '#10b981', 'Neutral': '#64748b', 'Negative': '#ef4444'}
        
        fig = px.pie(
            sentiment_df,
            values='percentage',
            names='sentiment',
            hole=0.5,
            color='sentiment',
            color_discrete_map=colors
        )
        
        fig.update_traces(textposition='outside', textinfo='label+percent')
        fig.update_layout(
            showlegend=False,
            height=220,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        # Add center annotation
        fig.add_annotation(
            text=f"<b>{sentiments['Positive']}%</b>",
            showarrow=False,
            font={'size': 24, 'color': '#10b981'},
            y=0.55
        )
        fig.add_annotation(
            text="Positive",
            showarrow=False,
            font={'size': 12, 'color': '#64748b'},
            y=0.45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent conversation excerpt
        st.markdown("""
        <div style='background: #f8fafc; padding: 0.75rem; border-radius: 8px; border-left: 3px solid #10b981; font-size: 0.85rem; font-style: italic; color: #475569; margin-top: 0.5rem;'>
            "We're really excited about the downtown area. The walkability is exactly what we're looking for!"
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("#### 🏠 Property Interest Heatmap")
        
        # Sample property interest data
        properties = [
            {'name': 'Downtown Condo', 'views': 8, 'dwell': 12},
            {'name': 'Clarksville Townhome', 'views': 5, 'dwell': 8},
            {'name': 'Steiner Ranch House', 'views': 3, 'dwell': 5},
            {'name': 'South Congress Loft', 'views': 2, 'dwell': 3}
        ]
        
        for prop in properties:
            interest_score = (prop['views'] * 2) + prop['dwell']
            bar_width = min((interest_score / 35) * 100, 100)
            
            color = "#10b981" if interest_score >= 20 else "#f59e0b" if interest_score >= 10 else "#64748b"
            
            st.markdown(f"""
            <div style='background: white; padding: 0.75rem; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 0.5rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;'>
                    <div style='font-weight: 600; font-size: 0.85rem; color: #1e293b;'>{prop['name']}</div>
                    <div style='font-size: 0.7rem; color: #64748b;'>{prop['views']} views · {prop['dwell']}min</div>
                </div>
                <div style='background: #f1f5f9; height: 6px; border-radius: 3px; overflow: hidden;'>
                    <div style='background: {color}; width: {bar_width}%; height: 100%;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Section 4: Urgency Indicators
    urgency_indicators = lead_data.get('urgency_indicators', [])
    
    if urgency_indicators:
        st.markdown("---")
        st.markdown("#### ⚡ Urgency Indicators")
        
        for indicator in urgency_indicators[:3]:  # Show top 3
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #fef3c7 0%, #fef9e7 100%); 
                        padding: 0.75rem; border-radius: 8px; border-left: 4px solid #f59e0b; 
                        margin-bottom: 0.5rem; display: flex; align-items: center; gap: 10px;'>
                <span style='font-size: 1.2rem;'>⚠️</span>
                <div>
                    <div style='font-weight: 600; color: #78350f; font-size: 0.9rem;'>{indicator}</div>
                    <div style='color: #92400e; font-size: 0.75rem;'>Immediate attention recommended</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
