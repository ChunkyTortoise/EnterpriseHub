"""
Executive Command Center - Real-time dashboard for Jorge
Beautiful, actionable, single-pane-of-glass view
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

def render_executive_dashboard(mock_data: bool = True):
    """
    Render the Executive Command Center dashboard.
    
    Args:
        mock_data: If True, use mock data for demo purposes
    """
    st.markdown("# 🎯 Executive Command Center")
    st.markdown("**Real-time intelligence for your real estate business**")
    st.markdown("---")
    
    # Top-level metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #00A32A 0%, #00C853 100%); 
                    padding: 20px; border-radius: 12px; color: white;'>
            <div style='font-size: 0.9rem; opacity: 0.9;'>🔥 HOT LEADS</div>
            <div style='font-size: 2.5rem; font-weight: 700; margin: 8px 0;'>3</div>
            <div style='font-size: 0.85rem; opacity: 0.8;'>+2 from yesterday</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #F59E0B 0%, #F97316 100%); 
                    padding: 20px; border-radius: 12px; color: white;'>
            <div style='font-size: 0.9rem; opacity: 0.9;'>⚡ WARM LEADS</div>
            <div style='font-size: 2.5rem; font-weight: 700; margin: 8px 0;'>8</div>
            <div style='font-size: 0.85rem; opacity: 0.8;'>Follow up today</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #006AFF 0%, #0052CC 100%); 
                    padding: 20px; border-radius: 12px; color: white;'>
            <div style='font-size: 0.9rem; opacity: 0.9;'>💰 PIPELINE</div>
            <div style='font-size: 2.5rem; font-weight: 700; margin: 8px 0;'>$2.4M</div>
            <div style='font-size: 0.85rem; opacity: 0.8;'>Projected closings</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%); 
                    padding: 20px; border-radius: 12px; color: white;'>
            <div style='font-size: 0.9rem; opacity: 0.9;'>⏱️ AVG RESPONSE</div>
            <div style='font-size: 2.5rem; font-weight: 700; margin: 8px 0;'>2.3m</div>
            <div style='font-size: 0.85rem; opacity: 0.8;'>AI response time</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        # Market Velocity Gauge
        velocity_score = 78
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=velocity_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "MARKET VELOCITY", 'font': {'size': 12, 'color': 'white'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#ffffff"},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "white",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(255,255,255,0.1)'},
                    {'range': [50, 100], 'color': 'rgba(255,255,255,0.2)'}
                ],
            }
        ))
        fig_gauge.update_layout(
            height=140, 
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor='rgba(139, 92, 246, 0.9)',
            font={'color': "white", 'family': "Arial"},
            bordercolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Hot Leads Feed
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### 🔥 Today's Hot Leads")
        
        # Hot lead cards
        hot_leads = [
            {
                "name": "Sarah Martinez",
                "score": 5,
                "budget": "$425K",
                "location": "Round Rock",
                "timeline": "ASAP - Pre-approved",
                "last_message": "Can we see it this weekend?",
                "minutes_ago": 12
            },
            {
                "name": "Mike Johnson",
                "score": 4,
                "budget": "$380K",
                "location": "Pflugerville",
                "timeline": "End of month",
                "last_message": "What's your cash offer?",
                "minutes_ago": 45
            },
            {
                "name": "Jennifer Wu",
                "score": 4,
                "budget": "$500K",
                "location": "Hyde Park",
                "timeline": "Flexible",
                "last_message": "Love that area. Let's talk.",
                "minutes_ago": 120
            }
        ]
        
        for lead in hot_leads:
            st.markdown(f"""
            <div style='background: white; padding: 16px; border-radius: 12px; 
                        margin-bottom: 12px; border-left: 4px solid #00A32A;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-size: 1.1rem; font-weight: 700; color: #2A2A33;'>
                            {lead['name']}
                            <span style='background: #DCFCE7; color: #166534; 
                                        padding: 2px 8px; border-radius: 12px; 
                                        font-size: 0.75rem; margin-left: 8px;'>
                                {lead['score']} questions answered
                            </span>
                        </div>
                        <div style='color: #6B7280; font-size: 0.9rem; margin-top: 4px;'>
                            💰 {lead['budget']} | 📍 {lead['location']} | ⏰ {lead['timeline']}
                        </div>
                        <div style='color: #2A2A33; font-size: 0.95rem; margin-top: 8px; 
                                    font-style: italic;'>
                            "{lead['last_message']}"
                        </div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='color: #6B7280; font-size: 0.85rem;'>
                            {lead['minutes_ago']}m ago
                        </div>
                    </div>
                </div>
                <div style='margin-top: 12px; display: flex; gap: 8px;'>
                    <button style='background: #006AFF; color: white; border: none; 
                                   padding: 8px 16px; border-radius: 6px; cursor: pointer;
                                   font-weight: 600; font-size: 0.9rem;'>
                        📞 Call Now
                    </button>
                    <button style='background: #F3F4F6; color: #2A2A33; border: none; 
                                   padding: 8px 16px; border-radius: 6px; cursor: pointer;
                                   font-weight: 600; font-size: 0.9rem;'>
                        📅 Schedule
                    </button>
                    <button style='background: #F3F4F6; color: #2A2A33; border: none; 
                                   padding: 8px 16px; border-radius: 6px; cursor: pointer;
                                   font-weight: 600; font-size: 0.9rem;'>
                        💬 Send SMS
                    </button>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_right:
        # AI Performance Scorecard
        st.markdown("### 📊 AI Performance")
        st.markdown("""
        <div style='background: white; padding: 16px; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);'>
            <div style='margin-bottom: 16px;'>
                <div style='color: #6B7280; font-size: 0.85rem;'>Response Rate</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: #00A32A;'>94%</div>
                <div style='background: #E5E7EB; height: 8px; border-radius: 4px; margin-top: 8px;'>
                    <div style='background: #00A32A; width: 94%; height: 100%; border-radius: 4px;'></div>
                </div>
            </div>
            <div style='margin-bottom: 16px;'>
                <div style='color: #6B7280; font-size: 0.85rem;'>Qualification Accuracy</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: #006AFF;'>88%</div>
                <div style='background: #E5E7EB; height: 8px; border-radius: 4px; margin-top: 8px;'>
                    <div style='background: #006AFF; width: 88%; height: 100%; border-radius: 4px;'></div>
                </div>
            </div>
            <div>
                <div style='color: #6B7280; font-size: 0.85rem;'>Conversion to Hot</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: #F59E0B;'>27%</div>
                <div style='background: #E5E7EB; height: 8px; border-radius: 4px; margin-top: 8px;'>
                    <div style='background: #F59E0B; width: 27%; height: 100%; border-radius: 4px;'></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        st.markdown("""
        <div style='background: white; padding: 16px; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);'>
            <button style='width: 100%; background: #006AFF; color: white; border: none; 
                           padding: 12px; border-radius: 8px; cursor: pointer;
                           font-weight: 600; margin-bottom: 8px;'>
                📨 Blast Hot Leads
            </button>
            <button style='width: 100%; background: #F3F4F6; color: #2A2A33; border: none; 
                           padding: 12px; border-radius: 8px; cursor: pointer;
                           font-weight: 600; margin-bottom: 8px;'>
                📊 Export Report
            </button>
            <button style='width: 100%; background: #F3F4F6; color: #2A2A33; border: none; 
                           padding: 12px; border-radius: 8px; cursor: pointer;
                           font-weight: 600;'>
                ⚙️ AI Settings
            </button>
        </div>
        """, unsafe_allow_html=True)
    
    # Activity Feed and Market Intelligence
    st.markdown("<br>", unsafe_allow_html=True)
    col_bottom_left, col_bottom_right = st.columns([1, 1])
    
    with col_bottom_left:
        st.markdown("### 🗺️ Market Intelligence Heatmap")
        st.markdown("""
        <div class="activity-heatmap">
            <div class="activity-heatmap-title">Lead Density by Neighborhood (Last 24h)</div>
            <div class="activity-heatmap-grid">
                <!-- Row 1 -->
                <div class="activity-cell activity-hot" title="Downtown: 42 leads"></div>
                <div class="activity-cell activity-high" title="Domain: 28 leads"></div>
                <div class="activity-cell activity-medium" title="Zilker: 15 leads"></div>
                <div class="activity-cell activity-low" title="Mueller: 5 leads"></div>
                <div class="activity-cell activity-high" title="East Austin: 31 leads"></div>
                <div class="activity-cell activity-medium" title="Rainey: 12 leads"></div>
                <div class="activity-cell activity-hot" title="Round Rock: 38 leads"></div>
                <!-- Row 2 -->
                <div class="activity-cell activity-medium" title="Pflugerville: 19 leads"></div>
                <div class="activity-cell activity-low" title="Cedar Park: 8 leads"></div>
                <div class="activity-cell activity-high" title="Lakeway: 24 leads"></div>
                <div class="activity-cell activity-hot" title="South Lamar: 45 leads"></div>
                <div class="activity-cell activity-medium" title="Barton Hills: 14 leads"></div>
                <div class="activity-cell activity-low" title="Circle C: 6 leads"></div>
                <div class="activity-cell activity-medium" title="Avery Ranch: 11 leads"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.7rem; color: #64748b;">
                <span>Low Activity</span>
                <span>High Activity</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Lead Velocity Sparklines
        st.markdown("### 📈 Lead Velocity (7d)")
        
        velocity_cols = st.columns(3)
        with velocity_cols[0]:
            st.markdown("**New Leads**")
            st.plotly_chart(sparkline([10, 15, 8, 22, 18, 25, 30], color="#006AFF"), use_container_width=True)
        with velocity_cols[1]:
            st.markdown("**Hot Quals**")
            st.plotly_chart(sparkline([2, 5, 3, 8, 6, 10, 12], color="#10B981"), use_container_width=True)
        with velocity_cols[2]:
            st.markdown("**Closings**")
            st.plotly_chart(sparkline([0, 1, 0, 2, 1, 0, 3], color="#8B5CF6"), use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔮 Predictive Revenue Roadmap (Q1 2026)")
    # Forecast data
    months = ["Jan", "Feb", "Mar", "Apr"]
    forecast = [2.4, 3.1, 4.2, 5.5]
    confidence_upper = [2.5, 3.5, 4.8, 6.2]
    confidence_lower = [2.3, 2.7, 3.6, 4.8]
    
    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(x=months, y=forecast, mode='lines+markers', name='AI Projection', line=dict(color='#006AFF', width=4)))
    fig_forecast.add_trace(go.Scatter(x=months, y=confidence_upper, mode='lines', line=dict(width=0), showlegend=False))
    fig_forecast.add_trace(go.Scatter(x=months, y=confidence_lower, mode='lines', fill='tonexty', fillcolor='rgba(0, 106, 255, 0.1)', line=dict(width=0), name='Confidence Band'))
    
    fig_forecast.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title="Timeline",
        yaxis_title="Pipeline Value ($M)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_forecast, use_container_width=True)
    st.caption("Revenue projections based on current lead velocity and AI-driven conversion optimization.")

    with col_bottom_right:
        # Activity Feed
        st.markdown("### 📱 Recent Activity")
        
        activities = [
            {"type": "hot", "icon": "🔥", "message": "Sarah Martinez became a HOT lead", "time": "12m ago"},
            {"type": "message", "icon": "💬", "message": "AI sent follow-up to Mike Johnson", "time": "45m ago"},
            {"type": "appointment", "icon": "📅", "message": "Showing scheduled for Jennifer Wu - Tomorrow 2pm", "time": "2h ago"},
            {"type": "message", "icon": "💬", "message": "New lead: David Chen asking about Hyde Park", "time": "3h ago"},
            {"type": "warm", "icon": "⚡", "message": "Emma Davis answered 2 questions - now WARM", "time": "4h ago"},
        ]
        
        for activity in activities:
            border_color = "#00A32A" if activity["type"] == "hot" else "#E5E7EB"
            st.markdown(f"""
            <div style='background: white; padding: 12px 16px; border-radius: 8px; 
                        margin-bottom: 8px; border-left: 3px solid {border_color};
                        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
                        display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <span style='font-size: 1.2rem; margin-right: 8px;'>{activity['icon']}</span>
                    <span style='color: #2A2A33; font-weight: 500;'>{activity['message']}</span>
                </div>
                <div style='color: #6B7280; font-size: 0.85rem;'>{activity['time']}</div>
            </div>
            """, unsafe_allow_html=True)

def sparkline(data: list, color: str = "#2563eb", height: int = 60):
    """Generates a minimal sparkline chart using Plotly."""
    import plotly.graph_objects as go
    fig = go.Figure(go.Scatter(
        y=data,
        mode='lines',
        fill='tozeroy',
        line=dict(color=color, width=2),
        fillcolor=f"{color}33"
    ))
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True)
    )
    return fig
