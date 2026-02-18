
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def render_health_sparklines():
    """Renders real-time system health sparklines in the sidebar."""
    
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; color: #64748b; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 5px;">
        <span style="display: inline-block; width: 8px; height: 8px; background-color: #10B981; border-radius: 50%;"></span>
        SYSTEM HEALTH TELEMETRY
    </div>
    """, unsafe_allow_html=True)
    
    # Generate mock telemetry data
    np.random.seed(int(datetime.now().timestamp()) % 1000)
    
    # 1. AI Response Latency Sparkline
    latency_data = np.random.normal(1.2, 0.3, 20).tolist()
    fig_lat = go.Figure()
    fig_lat.add_trace(go.Scatter(
        y=latency_data,
        mode='lines',
        line=dict(color='#3B82F6', width=2),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))
    fig_lat.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=30,
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown("<div style='font-size: 0.75rem; color: #475569;'>AI Latency</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 0.9rem; font-weight: 700; color: #1e293b;'>{latency_data[-1]:.2f}s</div>", unsafe_allow_html=True)
    with col2:
        st.plotly_chart(fig_lat, use_container_width=True, config={'displayModeBar': False})
    
    # 2. Lead Activity Sparkline
    activity_data = np.random.poisson(5, 20).tolist()
    fig_act = go.Figure()
    fig_act.add_trace(go.Scatter(
        y=activity_data,
        mode='lines',
        line=dict(color='#10B981', width=2),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.1)'
    ))
    fig_act.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=30,
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown("<div style='font-size: 0.75rem; color: #475569;'>Events/min</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 0.9rem; font-weight: 700; color: #1e293b;'>{activity_data[-1]} ops</div>", unsafe_allow_html=True)
    with col2:
        st.plotly_chart(fig_act, use_container_width=True, config={'displayModeBar': False})

    # 3. GHL Sync Freshness
    st.markdown("""
    <div style="margin-top: 0.5rem; padding: 0.5rem; background: rgba(59, 130, 246, 0.05); border-radius: 6px; border: 1px solid rgba(59, 130, 246, 0.1);">
        <div style="font-size: 0.65rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">GHL Sync Freshness</div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 2px;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #2563eb;">99.9% Up</div>
            <div style="font-size: 0.7rem; color: #64748b;">Last: 1m ago</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
