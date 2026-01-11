"""
AI Performance Metrics Dashboard - Shows real-time AI performance statistics
"""
import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
from typing import Dict, List, Any


def render_ai_metrics_dashboard():
    """
    Render comprehensive AI performance metrics dashboard
    """
    
    st.markdown("### 📊 AI Performance Metrics")
    st.markdown("*Real-time conversational AI statistics (Last 7 Days)*")
    
    # Get metrics data
    metrics = get_ai_performance_metrics()
    
    # Top-level KPI cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                    padding: 1.5rem; border-radius: 12px; color: white; text-align: center;'>
            <div style='font-size: 2.5rem; font-weight: 900; margin-bottom: 0.5rem;'>{metrics['avg_response_time']}</div>
            <div style='font-size: 0.875rem; opacity: 0.9;'>Avg Response Time</div>
            <div style='font-size: 0.75rem; opacity: 0.8; margin-top: 0.5rem;'>⚡ Lightning fast</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                    padding: 1.5rem; border-radius: 12px; color: white; text-align: center;'>
            <div style='font-size: 2.5rem; font-weight: 900; margin-bottom: 0.5rem;'>{metrics['messages_handled']:,}</div>
            <div style='font-size: 0.875rem; opacity: 0.9;'>Messages Handled</div>
            <div style='font-size: 0.75rem; opacity: 0.8; margin-top: 0.5rem;'>📈 +23% vs last week</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                    padding: 1.5rem; border-radius: 12px; color: white; text-align: center;'>
            <div style='font-size: 2.5rem; font-weight: 900; margin-bottom: 0.5rem;'>{metrics['automation_rate']}%</div>
            <div style='font-size: 0.875rem; opacity: 0.9;'>Automation Rate</div>
            <div style='font-size: 0.75rem; opacity: 0.8; margin-top: 0.5rem;'>🤖 AI handles most</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); 
                    padding: 1.5rem; border-radius: 12px; color: white; text-align: center;'>
            <div style='font-size: 2.5rem; font-weight: 900; margin-bottom: 0.5rem;'>{metrics['showings_scheduled']}</div>
            <div style='font-size: 0.875rem; opacity: 0.9;'>Showings Scheduled</div>
            <div style='font-size: 0.75rem; opacity: 0.8; margin-top: 0.5rem;'>📅 Auto-booked</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    
    # Detailed metrics in columns
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 🎯 AI Activity Breakdown")
        
        # Activity table
        activities = [
            {"type": "Questions Answered", "count": metrics['questions_answered'], "icon": "❓"},
            {"type": "Leads Qualified", "count": metrics['leads_qualified'], "icon": "✅"},
            {"type": "Property Matches Sent", "count": metrics['property_matches'], "icon": "🏠"},
            {"type": "Showings Scheduled", "count": metrics['showings_scheduled'], "icon": "📅"},
            {"type": "Follow-ups Sent", "count": metrics['followups_sent'], "icon": "💬"},
            {"type": "Human Handoffs", "count": metrics['human_handoffs'], "icon": "👤"}
        ]
        
        for activity in activities:
            st.markdown(f"""
            <div style='display: flex; justify-content: space-between; align-items: center; 
                        padding: 0.75rem 1rem; background: white; border-radius: 8px; 
                        border: 1px solid #e5e7eb; margin-bottom: 0.5rem;'>
                <div style='display: flex; align-items: center; gap: 0.75rem;'>
                    <span style='font-size: 1.25rem;'>{activity['icon']}</span>
                    <span style='font-size: 0.9rem; color: #374151;'>{activity['type']}</span>
                </div>
                <span style='font-size: 1.1rem; font-weight: 700; color: #1e293b;'>{activity['count']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Success rate
        success_rate = (1 - (metrics['human_handoffs'] / metrics['messages_handled'])) * 100
        st.markdown(f"""
        <div style='background: #ecfdf5; padding: 1rem; border-radius: 8px; border-left: 4px solid #10b981; margin-top: 1rem;'>
            <div style='font-size: 0.875rem; color: #065f46; font-weight: 600;'>SUCCESS RATE</div>
            <div style='font-size: 1.5rem; font-weight: 900; color: #10b981; margin: 0.5rem 0;'>{success_rate:.1f}%</div>
            <div style='font-size: 0.75rem; color: #047857;'>
                AI successfully handles {success_rate:.1f}% of conversations without human intervention
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_right:
        st.markdown("#### 📈 Response Time Trend")
        
        # Response time chart
        fig = create_response_time_chart(metrics['daily_response_times'])
        st.plotly_chart(fig, width='stretch')
        
        st.markdown("#### ⏱️ Time Saved")
        
        time_saved_minutes = metrics['messages_handled'] * 2.5  # Avg 2.5 min per manual response
        time_saved_hours = time_saved_minutes / 60
        
        st.markdown(f"""
        <div style='background: #eff6ff; padding: 1rem; border-radius: 8px; border-left: 4px solid #3b82f6;'>
            <div style='font-size: 0.875rem; color: #1e40af; font-weight: 600;'>ESTIMATED TIME SAVINGS</div>
            <div style='font-size: 1.5rem; font-weight: 900; color: #2563eb; margin: 0.5rem 0;'>{time_saved_hours:.1f} hours</div>
            <div style='font-size: 0.75rem; color: #1e40af;'>
                Based on {metrics['messages_handled']} messages × 2.5 min avg manual response time
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Cost savings
        hourly_rate = 50  # Assume $50/hr agent rate
        cost_saved = time_saved_hours * hourly_rate
        
        st.markdown(f"""
        <div style='background: #f0fdf4; padding: 1rem; border-radius: 8px; border-left: 4px solid #10b981; margin-top: 1rem;'>
            <div style='font-size: 0.875rem; color: #065f46; font-weight: 600;'>COST SAVINGS</div>
            <div style='font-size: 1.5rem; font-weight: 900; color: #10b981; margin: 0.5rem 0;'>${cost_saved:,.0f}</div>
            <div style='font-size: 0.75rem; color: #047857;'>
                Estimated at ${hourly_rate}/hr agent rate ({time_saved_hours:.1f} hours saved)
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_ai_metrics_compact():
    """Render compact metrics for sidebar or small spaces"""
    
    metrics = get_ai_performance_metrics()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Response Time", metrics['avg_response_time'], delta="-0.3s", delta_color="inverse")
    
    with col2:
        st.metric("Messages", f"{metrics['messages_handled']:,}", delta="+23%")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.metric("Automation", f"{metrics['automation_rate']}%", delta="+2%")
    
    with col4:
        st.metric("Showings", metrics['showings_scheduled'], delta="+4")


def get_ai_performance_metrics() -> Dict[str, Any]:
    """
    Get AI performance metrics
    In production, this would query actual monitoring data
    """
    
    # Mock data for demo
    # In production, replace with actual monitoring service:
    # from services.monitoring import get_metrics
    # return get_metrics(days=7)
    
    return {
        "avg_response_time": "1.2s",
        "messages_handled": 247,
        "questions_answered": 189,
        "leads_qualified": 34,
        "showings_scheduled": 12,
        "property_matches": 56,
        "followups_sent": 78,
        "human_handoffs": 8,
        "automation_rate": 96.8,
        "daily_response_times": [
            {"day": "Mon", "avg_time": 1.4},
            {"day": "Tue", "avg_time": 1.3},
            {"day": "Wed", "avg_time": 1.2},
            {"day": "Thu", "avg_time": 1.1},
            {"day": "Fri", "avg_time": 1.2},
            {"day": "Sat", "avg_time": 1.3},
            {"day": "Sun", "avg_time": 1.2}
        ]
    }


def create_response_time_chart(daily_data: List[Dict[str, Any]]) -> go.Figure:
    """Create response time trend chart"""
    
    days = [d['day'] for d in daily_data]
    times = [d['avg_time'] for d in daily_data]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=days,
        y=times,
        mode='lines+markers',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=10, color='#2563eb', line=dict(color='white', width=2)),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)',
        hovertemplate='<b>%{x}</b><br>Avg: %{y:.1f}s<extra></extra>'
    ))
    
    fig.update_layout(
        title=None,
        xaxis_title="Day of Week",
        yaxis_title="Response Time (seconds)",
        template='plotly_white',
        height=250,
        margin=dict(l=40, r=20, t=20, b=40),
        font=dict(size=11),
        hovermode='x unified'
    )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='#f1f5f9', range=[0, max(times) * 1.2])
    
    return fig
