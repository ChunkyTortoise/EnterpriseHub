"""
Interactive Lead Map Component
Clickable geographic visualization with lead-specific AI analysis
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
import json


def render_interactive_lead_map(leads_data: List[Dict[str, Any]], market: str = "Austin"):
    """
    Render an interactive map with clickable lead markers and optional heat map overlay
    
    Args:
        leads_data: List of lead dictionaries with lat, lon, and lead details
        market: Market name for centering the map
    """
    
    st.markdown("### 📍 Interactive Lead Intelligence Map")
    
    # Layer controls
    col_title, col_controls = st.columns([2, 1])
    
    with col_title:
        st.markdown("*Click on any marker to view detailed AI analysis*")
    
    with col_controls:
        # Initialize session state for map view mode
        if 'map_view_mode' not in st.session_state:
            st.session_state.map_view_mode = "Markers"
        
        view_mode = st.selectbox(
            "View Mode:",
            ["Markers", "Heat Map", "Both"],
            key="map_view_selector",
            label_visibility="collapsed",
            help="Switch between marker view, heat map, or combined view"
        )
        st.session_state.map_view_mode = view_mode
    
    # Initialize session state for selected lead
    if 'selected_lead_marker' not in st.session_state:
        st.session_state.selected_lead_marker = None
    
    # Map configuration based on market
    map_config = {
        "Austin": {"center_lat": 30.2672, "center_lon": -97.7431, "zoom": 11},
        "Rancho": {"center_lat": 34.1200, "center_lon": -117.5700, "zoom": 12}
    }
    
    config = map_config.get(market, map_config["Austin"])
    
    # Create layout with map and detail panel
    col_map, col_detail = st.columns([2, 1])
    
    with col_map:
        # Create interactive Plotly map based on view mode
        view_mode = st.session_state.map_view_mode
        
        if view_mode == "Heat Map":
            fig = create_heat_map(leads_data, config)
        elif view_mode == "Both":
            fig = create_combined_map(leads_data, config)
        else:  # Markers
            fig = create_plotly_map(leads_data, config)
        
        # Capture click events using Plotly events
        selected_points = st.plotly_chart(
            fig, 
            use_container_width=True,
            key="lead_map",
            on_select="rerun"
        )
        
        # Map legend - conditional based on view mode
        if view_mode in ["Markers", "Both"]:
            st.markdown("""
            <div style='display: flex; gap: 1.5rem; justify-content: center; margin-top: 1rem; font-size: 0.85rem;'>
                <div style='display: flex; align-items: center; gap: 0.5rem;'>
                    <div style='width: 16px; height: 16px; background: #ef4444; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2);'></div>
                    <span style='color: #64748b;'>Hot Leads (80+)</span>
                </div>
                <div style='display: flex; align-items: center; gap: 0.5rem;'>
                    <div style='width: 16px; height: 16px; background: #f59e0b; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2);'></div>
                    <span style='color: #64748b;'>Warm Leads (50-79)</span>
                </div>
                <div style='display: flex; align-items: center; gap: 0.5rem;'>
                    <div style='width: 16px; height: 16px; background: #3b82f6; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2);'></div>
                    <span style='color: #64748b;'>Cold Leads (0-49)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if view_mode in ["Heat Map", "Both"]:
            st.markdown("""
            <div style='display: flex; gap: 1.5rem; justify-content: center; margin-top: 1rem; font-size: 0.85rem;'>
                <div style='display: flex; align-items: center; gap: 0.5rem;'>
                    <div style='width: 20px; height: 12px; background: linear-gradient(to right, #3b82f6, #f59e0b, #ef4444);'></div>
                    <span style='color: #64748b;'>Low → High Activity Density</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_detail:
        render_lead_detail_panel(leads_data)


def create_plotly_map(leads_data: List[Dict[str, Any]], config: Dict[str, Any]) -> go.Figure:
    """Create interactive Plotly map with colored markers based on lead score"""
    
    # Prepare data for plotting
    lats, lons, colors, sizes, texts, lead_ids = [], [], [], [], [], []
    
    for lead in leads_data:
        lats.append(lead.get('lat', config['center_lat']))
        lons.append(lead.get('lon', config['center_lon']))
        
        # Color based on lead score
        score = lead.get('lead_score', 50)
        if score >= 80:
            colors.append('#ef4444')  # Red for hot
            sizes.append(16)
        elif score >= 50:
            colors.append('#f59e0b')  # Orange for warm
            sizes.append(14)
        else:
            colors.append('#3b82f6')  # Blue for cold
            sizes.append(12)
        
        # Hover text
        name = lead.get('name', 'Unknown Lead')
        budget = lead.get('budget', 0)
        location = lead.get('location', 'Unknown')
        
        hover_text = f"<b>{name}</b><br>" \
                    f"Score: {score}<br>" \
                    f"Budget: ${budget:,}<br>" \
                    f"Area: {location}<br>" \
                    f"<i>Click for details</i>"
        texts.append(hover_text)
        lead_ids.append(lead.get('id', ''))
    
    # Create scatter mapbox
    fig = go.Figure()
    
    fig.add_trace(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors,
            opacity=0.9,
            sizemode='diameter'
        ),
        text=texts,
        hovertemplate='%{text}<extra></extra>',
        customdata=lead_ids,
        name='Leads'
    ))
    
    # Map layout
    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=config['center_lat'], lon=config['center_lon']),
            zoom=config['zoom']
        ),
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        hovermode='closest',
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def create_heat_map(leads_data: List[Dict[str, Any]], config: Dict[str, Any]) -> go.Figure:
    """Create heat map visualization showing lead activity density"""
    
    # Calculate activity density metrics for each lead
    heat_points = []
    
    for lead in leads_data:
        lat = lead.get('lat', config['center_lat'])
        lon = lead.get('lon', config['center_lon'])
        
        # Calculate heat intensity based on multiple factors
        score = lead.get('lead_score', 50)
        engagement = lead.get('engagement_score', 50)
        budget = lead.get('budget', 0)
        
        # Weighted heat calculation
        # High score + high engagement + high budget = hottest point
        score_weight = score / 100  # 0-1
        engagement_weight = engagement / 100  # 0-1
        budget_weight = min(budget / 2000000, 1.0)  # Cap at 2M, 0-1
        
        # Combined heat intensity (0-3 scale, then normalized)
        heat_intensity = (score_weight * 1.5) + (engagement_weight * 1.0) + (budget_weight * 0.5)
        
        heat_points.append({
            'lat': lat,
            'lon': lon,
            'intensity': heat_intensity,
            'name': lead.get('name', 'Unknown'),
            'score': score,
            'budget': budget
        })
    
    # Create density map using Plotly's density_mapbox
    fig = go.Figure()
    
    lats = [p['lat'] for p in heat_points]
    lons = [p['lon'] for p in heat_points]
    intensities = [p['intensity'] for p in heat_points]
    
    fig.add_trace(go.Densitymapbox(
        lat=lats,
        lon=lons,
        z=intensities,
        radius=30,  # Radius of influence for each point
        colorscale=[
            [0, '#3b82f6'],      # Blue - low activity
            [0.3, '#60a5fa'],    # Light blue
            [0.5, '#f59e0b'],    # Orange - medium activity
            [0.7, '#fb923c'],    # Light orange
            [1, '#ef4444']       # Red - high activity
        ],
        opacity=0.6,
        hovertemplate='<b>Activity Density</b><br>Intensity: %{z:.2f}<extra></extra>',
        showscale=True,
        colorbar=dict(
            title="Activity<br>Level",
            thickness=15,
            len=0.7,
            x=1.02,
            tickvals=[0, 1, 2, 3],
            ticktext=['Low', 'Medium', 'High', 'Very High']
        )
    ))
    
    # Map layout
    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=config['center_lat'], lon=config['center_lon']),
            zoom=config['zoom']
        ),
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        hovermode='closest',
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def create_combined_map(leads_data: List[Dict[str, Any]], config: Dict[str, Any]) -> go.Figure:
    """Create combined map with both heat map and markers"""
    
    # Start with heat map
    fig = create_heat_map(leads_data, config)
    
    # Add markers on top
    lats, lons, colors, sizes, texts = [], [], [], [], []
    
    for lead in leads_data:
        lats.append(lead.get('lat', config['center_lat']))
        lons.append(lead.get('lon', config['center_lon']))
        
        # Color based on lead score
        score = lead.get('lead_score', 50)
        if score >= 80:
            colors.append('#ef4444')  # Red
            sizes.append(14)
        elif score >= 50:
            colors.append('#f59e0b')  # Orange
            sizes.append(12)
        else:
            colors.append('#3b82f6')  # Blue
            sizes.append(10)
        
        # Hover text
        name = lead.get('name', 'Unknown Lead')
        budget = lead.get('budget', 0)
        location = lead.get('location', 'Unknown')
        
        hover_text = f"<b>{name}</b><br>" \
                    f"Score: {score}<br>" \
                    f"Budget: ${budget:,}<br>" \
                    f"Area: {location}<br>" \
                    f"<i>Click for details</i>"
        texts.append(hover_text)
    
    # Add scatter markers
    fig.add_trace(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors,
            opacity=0.9,
            sizemode='diameter'
        ),
        text=texts,
        hovertemplate='%{text}<extra></extra>',
        name='Leads'
    ))
    
    return fig


def render_lead_detail_panel(leads_data: List[Dict[str, Any]]):
    """Render the lead detail panel with AI analysis"""
    
    # Lead selector
    st.markdown("#### 🎯 Lead Details")
    
    lead_names = ["Select a lead..."] + [lead.get('name', f"Lead {i}") for i, lead in enumerate(leads_data)]
    
    selected_name = st.selectbox(
        "Choose lead:",
        lead_names,
        key="lead_selector_detail",
        label_visibility="collapsed"
    )
    
    if selected_name == "Select a lead...":
        st.markdown("""
        <div style='background: #f8fafc; padding: 2rem 1.5rem; border-radius: 12px; text-align: center; border: 2px dashed #cbd5e1;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>📍</div>
            <h4 style='color: #475569; margin: 0 0 0.5rem 0;'>Select a Lead</h4>
            <p style='color: #64748b; font-size: 0.875rem; margin: 0;'>
                Click a marker on the map or use the dropdown to view AI analysis
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Find selected lead
    selected_lead = None
    for lead in leads_data:
        if lead.get('name') == selected_name:
            selected_lead = lead
            break
    
    if not selected_lead:
        st.warning("Lead data not found")
        return
    
    # Display lead analysis
    render_lead_analysis(selected_lead)


def render_lead_analysis(lead: Dict[str, Any]):
    """Render detailed AI analysis for a specific lead"""
    
    name = lead.get('name', 'Unknown')
    score = lead.get('lead_score', 0)
    budget = lead.get('budget', 0)
    location = lead.get('location', 'Unknown')
    timeline = lead.get('timeline', 'Unknown')
    
    # Lead header card
    score_color = "#ef4444" if score >= 80 else "#f59e0b" if score >= 50 else "#3b82f6"
    score_label = "🔥 HOT" if score >= 80 else "🔸 WARM" if score >= 50 else "❄️ COLD"
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {score_color}15 0%, {score_color}05 100%); 
                padding: 1.5rem; border-radius: 12px; border-left: 4px solid {score_color}; margin-bottom: 1.5rem;'>
        <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;'>
            <h3 style='margin: 0; color: #1e293b; font-size: 1.25rem;'>{name}</h3>
            <span style='background: {score_color}; color: white; padding: 0.25rem 0.75rem; 
                         border-radius: 6px; font-size: 0.75rem; font-weight: 700;'>{score_label}</span>
        </div>
        <div style='display: flex; align-items: center; gap: 0.5rem; color: #475569; font-size: 0.875rem;'>
            <div style='font-size: 2rem; font-weight: 800; color: {score_color};'>{score}</div>
            <div style='font-size: 0.75rem; color: #64748b;'>/ 100<br/>Lead Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    st.markdown("##### 📊 Key Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Budget", f"${budget:,}")
        st.metric("Timeline", timeline)
    
    with col2:
        st.metric("Location", location)
        engagement = lead.get('engagement_score', 0)
        st.metric("Engagement", f"{engagement}%")
    
    st.markdown("---")
    
    # AI Analysis
    st.markdown("##### 🤖 AI Analysis")
    
    # Generate dynamic AI insights
    insights = generate_lead_insights(lead)
    
    for insight in insights:
        icon = insight.get('icon', '💡')
        text = insight.get('text', '')
        insight_type = insight.get('type', 'info')
        
        if insight_type == 'success':
            st.success(f"{icon} {text}")
        elif insight_type == 'warning':
            st.warning(f"{icon} {text}")
        else:
            st.info(f"{icon} {text}")
    
    st.markdown("---")
    
    # Recommended actions
    st.markdown("##### ⚡ Recommended Actions")
    
    actions = generate_recommended_actions(lead)
    
    for action in actions:
        action_id = action.get('id')
        lead_id = lead.get('id', 'unknown')
        sync_key = f"synced_{lead_id}"
        
        # Check if already synced
        is_synced = st.session_state.get(sync_key, False)
        
        button_label = action.get('label', 'Action')
        if action_id == 'sync_crm' and is_synced:
            button_label = "Re-Sync to CRM"
            
        button_icon = action.get('icon', '▶️')
        
        if st.button(f"{button_icon} {button_label}", use_container_width=True, key=f"action_{action_id}_{lead_id}"):
            if action_id == 'sync_crm':
                with st.spinner("🔌 Establishing secure handshake with GHL API..."):
                    import time
                    time.sleep(0.8)
                    st.session_state[sync_key] = True
                    st.toast(f"✅ Successfully synced {lead.get('name')} to HighLevel CRM!", icon="🔗")
            else:
                st.toast(f"✅ {action.get('toast', 'Action triggered!')}", icon="🚀")
                
    # Show sync status badge if applicable
    if st.session_state.get(f"synced_{lead.get('id', 'unknown')}", False):
        st.markdown("""
        <div style='background: #dcfce7; color: #166534; padding: 0.5rem; border-radius: 6px; 
                    text-align: center; font-size: 0.85rem; font-weight: 600; margin-top: 0.5rem;
                    border: 1px solid #bbf7d0;'>
            ✅ Synced with GoHighLevel
        </div>
        """, unsafe_allow_html=True)
    
    # Activity timeline
    st.markdown("---")
    st.markdown("##### 📅 Recent Activity")
    
    activities = lead.get('activities', [
        {"time": "2 hours ago", "action": "Viewed property listing", "icon": "👀"},
        {"time": "1 day ago", "action": "Responded to SMS", "icon": "💬"},
        {"time": "3 days ago", "action": "Submitted inquiry form", "icon": "📝"}
    ])
    
    for activity in activities:
        st.markdown(f"""
        <div style='display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem; 
                    background: #f8fafc; border-radius: 8px; margin-bottom: 0.5rem;'>
            <div style='font-size: 1.2rem;'>{activity['icon']}</div>
            <div style='flex: 1;'>
                <div style='font-size: 0.875rem; color: #1e293b; font-weight: 500;'>{activity['action']}</div>
                <div style='font-size: 0.75rem; color: #64748b;'>{activity['time']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def generate_sample_lead_data(market: str = "Austin") -> List[Dict[str, Any]]:
    """Generate sample lead data for map visualization when real data is unavailable."""
    if market == "Rancho":
        # Rancho Cucamonga cluster
        return [
            {
                "id": "lead_001",
                "name": "Sarah Johnson",
                "lat": 34.1200,
                "lon": -117.5700,
                "lead_score": 92,
                "engagement_score": 85,
                "budget": 1300000,
                "location": "Alta Loma",
                "timeline": "ASAP"
            },
            {
                "id": "lead_002",
                "name": "Mike Chen",
                "lat": 34.1100,
                "lon": -117.5800,
                "lead_score": 65,
                "engagement_score": 45,
                "budget": 700000,
                "location": "Victoria Gardens",
                "timeline": "6 months"
            },
            {
                "id": "lead_003",
                "name": "Emily Davis",
                "lat": 34.1000,
                "lon": -117.5600,
                "lead_score": 42,
                "engagement_score": 30,
                "budget": 1000000,
                "location": "Rancho Cucamonga",
                "timeline": "Exploring"
            }
        ]
    else:
        # Austin cluster
        return [
            {
                "id": "lead_001",
                "name": "Sarah Johnson",
                "lat": 30.2672,
                "lon": -97.7431,
                "lead_score": 92,
                "engagement_score": 85,
                "budget": 800000,
                "location": "Downtown",
                "timeline": "ASAP"
            },
            {
                "id": "lead_002",
                "name": "Mike Chen",
                "lat": 30.2700,
                "lon": -97.7500,
                "lead_score": 65,
                "engagement_score": 45,
                "budget": 450000,
                "location": "East Austin",
                "timeline": "6 months"
            },
            {
                "id": "lead_003",
                "name": "Emily Davis",
                "lat": 30.2500,
                "lon": -97.7300,
                "lead_score": 42,
                "engagement_score": 30,
                "budget": 300000,
                "location": "South Austin",
                "timeline": "Exploring"
            }
        ]


def generate_lead_insights(lead: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate AI insights based on lead data"""
    
    insights = []
    score = lead.get('lead_score', 0)
    budget = lead.get('budget', 0)
    timeline = lead.get('timeline', '').lower()
    engagement = lead.get('engagement_score', 0)
    
    # Score-based insights
    if score >= 80:
        insights.append({
            'icon': '🔥',
            'text': 'High-priority lead! Strong buying signals detected.',
            'type': 'success'
        })
    elif score >= 50:
        insights.append({
            'icon': '🎯',
            'text': 'Qualified lead with moderate interest. Follow-up recommended.',
            'type': 'info'
        })
    else:
        insights.append({
            'icon': '🌱',
            'text': 'Early-stage lead. Nurture with educational content.',
            'type': 'warning'
        })
    
    # Budget insights
    if budget >= 1000000:
        insights.append({
            'icon': '💎',
            'text': f'Luxury buyer segment (${budget:,}). Show premium listings.',
            'type': 'success'
        })
    elif budget > 0:
        insights.append({
            'icon': '💰',
            'text': f'Budget confirmed at ${budget:,}. Property matcher active.',
            'type': 'info'
        })
    
    # Timeline insights
    if 'asap' in timeline or 'now' in timeline or '30' in timeline:
        insights.append({
            'icon': '⏰',
            'text': 'Urgent timeline detected. Prioritize immediate showing.',
            'type': 'warning'
        })
    
    # Engagement insights
    if engagement >= 70:
        insights.append({
            'icon': '📈',
            'text': f'High engagement ({engagement}%). Lead is actively searching.',
            'type': 'success'
        })
    
    return insights


def generate_recommended_actions(lead: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate recommended actions based on lead profile"""
    
    actions = []
    score = lead.get('lead_score', 0)
    name = lead.get('name', 'Lead')
    
    if score >= 80:
        actions.extend([
            {
                'id': 'call_now',
                'label': 'Call Now',
                'icon': '📞',
                'toast': f'Calling {name}...'
            },
            {
                'id': 'schedule_showing',
                'label': 'Schedule Showing',
                'icon': '📅',
                'toast': 'Opening calendar...'
            }
        ])
    
    actions.extend([
        {
            'id': 'sync_crm',
            'label': 'Sync to CRM',
            'icon': '🔄',
            'toast': 'Syncing lead data to GoHighLevel...'
        },
        {
            'id': 'send_properties',
            'label': 'Send Property Matches',
            'icon': '🏠',
            'toast': f'Sending top 3 matches to {name}'
        },
        {
            'id': 'send_sms',
            'label': 'Send Follow-Up SMS',
            'icon': '💬',
            'toast': 'SMS queued in GHL'
        },
        {
            'id': 'view_conversation',
            'label': 'View Full Conversation',
            'icon': '💭',
            'toast': 'Loading conversation history...'
        }
    ])
    
    return actions
