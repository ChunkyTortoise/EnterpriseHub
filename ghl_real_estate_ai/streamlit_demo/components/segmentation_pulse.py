"""
Segmentation Pulse Dashboard Component
Enhanced data visualization for Smart Segmentation with KPI ribbon and distribution chart
"""
import streamlit as st
import plotly.graph_objects as go
from typing import Dict, List, Any


def render_segmentation_pulse(segment_data: Dict[str, Any]):
    """
    Render the enhanced Segmentation Pulse dashboard with:
    - KPI Ribbon with key metrics
    - Lead Score Distribution Chart
    - Export functionality
    
    Args:
        segment_data: Dictionary containing segment characteristics and metrics
    """
    
    # Extract metrics from segment data
    char = segment_data.get('characteristics', {})
    
    # KPI Ribbon - High-Impact Metric Cards
    st.markdown("### 📊 Segmentation Pulse")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style='background: white; padding: 1.5rem; border-radius: 16px; border: 1px solid #f1f5f9; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
            <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                <div style='padding: 0.75rem; background: #f0fdf4; border-radius: 12px; font-size: 1.75rem; line-height: 1;'>📈</div>
                <span style='color: #22c55e; font-size: 0.75rem; font-weight: 700;'>+12%</span>
            </div>
            <p style='font-size: 0.875rem; color: #64748b; margin: 0 0 0.5rem 0;'>Avg Engagement</p>
            <h3 style='font-size: 2rem; font-weight: 800; color: #0f172a; margin: 0;'>{char.get('avg_engagement', 0)}%</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='background: white; padding: 1.5rem; border-radius: 16px; border: 1px solid #f1f5f9; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
            <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                <div style='padding: 0.75rem; background: #eff6ff; border-radius: 12px; font-size: 1.75rem; line-height: 1;'>🎯</div>
                <span style='color: #3b82f6; font-size: 0.75rem; font-weight: 700;'>+5.2</span>
            </div>
            <p style='font-size: 0.875rem; color: #64748b; margin: 0 0 0.5rem 0;'>Avg Lead Score</p>
            <h3 style='font-size: 2rem; font-weight: 800; color: #0f172a; margin: 0;'>{char.get('avg_lead_score', 0):.1f}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_value = char.get('total_value', 0)
        st.markdown(f"""
        <div style='background: white; padding: 1.5rem; border-radius: 16px; border: 1px solid #f1f5f9; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
            <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                <div style='padding: 0.75rem; background: #ecfdf5; border-radius: 12px; font-size: 1.75rem; line-height: 1;'>💰</div>
                <span style='color: #10b981; font-size: 0.75rem; font-weight: 700;'>+$2.4M</span>
            </div>
            <p style='font-size: 0.875rem; color: #64748b; margin: 0 0 0.5rem 0;'>Total Value</p>
            <h3 style='font-size: 2rem; font-weight: 800; color: #0f172a; margin: 0;'>${total_value:,.0f}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        segment_size = segment_data.get('size', 0)
        st.markdown(f"""
        <div style='background: white; padding: 1.5rem; border-radius: 16px; border: 1px solid #f1f5f9; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
            <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                <div style='padding: 0.75rem; background: #f8fafc; border-radius: 12px; font-size: 1.75rem; line-height: 1;'>👥</div>
                <span style='color: #64748b; font-size: 0.75rem; font-weight: 700;'>+4 today</span>
            </div>
            <p style='font-size: 0.875rem; color: #64748b; margin: 0 0 0.5rem 0;'>Segment Size</p>
            <h3 style='font-size: 2rem; font-weight: 800; color: #0f172a; margin: 0;'>{segment_size} Leads</h3>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    
    # Lead Score Distribution Chart
    render_lead_score_distribution()
    
    # Quick Actions
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        if st.button("📧 Send Campaign to Segment", use_container_width=True):
            st.success("Campaign queued for this segment!")
    
    with col_b:
        if st.button("📊 View All Leads", use_container_width=True):
            st.info("Opening lead details...")
    
    with col_c:
        # Export functionality with segment-specific data
        import pandas as pd
        export_data = {
            "Metric": ["Avg Engagement", "Avg Lead Score", "Total Value", "Segment Size"],
            "Value": [f"{char.get('avg_engagement', 0)}%", f"{char.get('avg_lead_score', 0):.1f}", 
                     f"${char.get('total_value', 0):,.0f}", f"{segment_size}"],
            "Trend": ["+12%", "+5.2", "+$2.4M", "+4 today"]
        }
        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            "📥 Export Segment CSV",
            data=csv,
            file_name=f"segment_{segment_data.get('name', 'data')}.csv",
            mime="text/csv",
            use_container_width=True
        )


def render_lead_score_distribution():
    """Render interactive lead score distribution bar chart"""
    
    # Mock distribution data (in production, this would come from actual segment leads)
    distribution_data = {
        '0-20': 3,
        '21-40': 8,
        '41-60': 15,
        '61-80': 22,
        '81-100': 14
    }
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=list(distribution_data.keys()),
        y=list(distribution_data.values()),
        marker=dict(
            color='#2563eb',
            line=dict(color='#1e40af', width=1)
        ),
        hovertemplate='<b>Score Range: %{x}</b><br>Leads: %{y}<extra></extra>',
        text=list(distribution_data.values()),
        textposition='outside'
    ))
    
    fig.update_layout(
        title={
            'text': '<b>Lead Score Distribution</b>',
            'font': {'size': 18, 'color': '#0f172a'}
        },
        xaxis_title='Score Range',
        yaxis_title='Number of Leads',
        template='plotly_white',
        height=350,
        margin=dict(l=40, r=40, t=60, b=40),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(color='#64748b'),
        xaxis=dict(
            gridcolor='#f1f5f9',
            showline=False,
            zeroline=False
        ),
        yaxis=dict(
            gridcolor='#f1f5f9',
            showline=False,
            zeroline=False
        ),
        bargap=0.2,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True, key="lead_score_dist")
    
    # Insights below chart
    col_i1, col_i2, col_i3 = st.columns(3)
    
    with col_i1:
        st.markdown("""
        <div style='background: #eff6ff; padding: 1rem; border-radius: 8px; border-left: 3px solid #3b82f6;'>
            <div style='font-size: 0.75rem; color: #1e40af; font-weight: 600; margin-bottom: 0.25rem;'>PEAK RANGE</div>
            <div style='font-size: 1.25rem; font-weight: 700; color: #1e40af;'>61-80 Range</div>
            <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;'>22 leads ready to convert</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_i2:
        st.markdown("""
        <div style='background: #fef3c7; padding: 1rem; border-radius: 8px; border-left: 3px solid #f59e0b;'>
            <div style='font-size: 0.75rem; color: #92400e; font-weight: 600; margin-bottom: 0.25rem;'>NEEDS NURTURE</div>
            <div style='font-size: 1.25rem; font-weight: 700; color: #92400e;'>21-60 Range</div>
            <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;'>23 leads need follow-up</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_i3:
        st.markdown("""
        <div style='background: #ecfdf5; padding: 1rem; border-radius: 8px; border-left: 3px solid #10b981;'>
            <div style='font-size: 0.75rem; color: #065f46; font-weight: 600; margin-bottom: 0.25rem;'>HOT ZONE</div>
            <div style='font-size: 1.25rem; font-weight: 700; color: #065f46;'>81-100 Range</div>
            <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;'>14 leads ready to close</div>
        </div>
        """, unsafe_allow_html=True)
