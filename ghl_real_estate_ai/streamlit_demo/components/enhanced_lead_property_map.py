"""
Enhanced Lead Property Map Component

Advanced interactive map combining lead intelligence with property data
from Zillow and Redfin for comprehensive market visualization.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
import json
import asyncio
from datetime import datetime

# Import property services
try:
    from ...services.zillow_integration_service import search_zillow_properties, PropertyData
    from ...services.redfin_integration_service import search_redfin_properties, RedfinPropertyData
    from .interactive_lead_map import generate_sample_lead_data
except ImportError:
    # Fallback for demo mode
    search_zillow_properties = None
    search_redfin_properties = None


def render_enhanced_lead_property_map(
    leads_data: List[Dict[str, Any]],
    market: str = "Austin",
    show_properties: bool = True
):
    """
    Enhanced interactive map with lead markers and property overlays from Zillow/Redfin.

    Args:
        leads_data: List of lead dictionaries with lat, lon, and lead details
        market: Market name for centering the map
        show_properties: Whether to show property overlays
    """

    st.markdown("### 📍 Enhanced Lead Intelligence & Property Map")
    st.markdown("*Interactive visualization combining lead data with live property market information*")

    # Enhanced controls
    render_map_controls(market, show_properties)

    # Get map configuration
    config = get_map_config(market)

    # Create the enhanced map
    map_data = prepare_map_data(leads_data, market, show_properties)

    # Render the interactive map
    fig = create_enhanced_map(map_data, config)

    # Display map with interaction handling
    col_map, col_panel = st.columns([2.5, 1.5])

    with col_map:
        selected_points = st.plotly_chart(
            fig,
            use_container_width=True,
            key="enhanced_lead_property_map",
            on_select="rerun"
        )

        # Map legend
        render_enhanced_legend()

    with col_panel:
        render_enhanced_detail_panel(leads_data, map_data.get('properties', []))


def render_map_controls(market: str, show_properties: bool):
    """Render enhanced map controls"""

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        # View mode selector
        if 'enhanced_map_view' not in st.session_state:
            st.session_state.enhanced_map_view = "Leads + Properties"

        view_mode = st.selectbox(
            "Map View",
            ["Leads Only", "Properties Only", "Leads + Properties", "Heat Map"],
            key="enhanced_view_selector",
            index=2
        )
        st.session_state.enhanced_map_view = view_mode

    with col2:
        # Property source selector
        if 'property_source' not in st.session_state:
            st.session_state.property_source = "Both"

        property_source = st.selectbox(
            "Property Data",
            ["Zillow", "Redfin", "Both", "None"],
            key="property_source_selector"
        )
        st.session_state.property_source = property_source

    with col3:
        # Price range filter
        price_range = st.selectbox(
            "Price Range",
            ["All Prices", "$0-$500K", "$500K-$1M", "$1M+"],
            key="price_filter"
        )

    with col4:
        # Refresh data button
        if st.button("🔄 Refresh Data", help="Reload property and lead data"):
            # Clear relevant caches
            if 'property_cache' in st.session_state:
                del st.session_state.property_cache
            if 'map_data_cache' in st.session_state:
                del st.session_state.map_data_cache
            st.rerun()


def get_map_config(market: str) -> Dict[str, Any]:
    """Get map configuration based on market"""

    configs = {
        "Austin": {
            "center_lat": 30.2672,
            "center_lon": -97.7431,
            "zoom": 11,
            "bounds": {
                "north": 30.5,
                "south": 30.0,
                "east": -97.5,
                "west": -98.0
            }
        },
        "Rancho": {
            "center_lat": 34.1200,
            "center_lon": -117.5700,
            "zoom": 12,
            "bounds": {
                "north": 34.2,
                "south": 34.0,
                "east": -117.4,
                "west": -117.7
            }
        }
    }

    return configs.get(market, configs["Austin"])


def prepare_map_data(
    leads_data: List[Dict[str, Any]],
    market: str,
    show_properties: bool
) -> Dict[str, Any]:
    """Prepare combined lead and property data for the map"""

    map_data = {
        "leads": leads_data,
        "properties": [],
        "market_stats": {}
    }

    if not show_properties or st.session_state.get('property_source') == "None":
        return map_data

    # Check cache first
    cache_key = f"map_data_{market}_{st.session_state.get('property_source', 'Both')}"
    if cache_key in st.session_state.get('map_data_cache', {}):
        cached_data = st.session_state.map_data_cache[cache_key]
        if (datetime.now() - cached_data['timestamp']).seconds < 300:  # 5 min cache
            return cached_data['data']

    # Load property data
    try:
        properties = load_property_data(market)
        map_data["properties"] = properties

        # Calculate market stats
        if properties:
            prices = [p.get('price', 0) for p in properties if p.get('price')]
            if prices:
                map_data["market_stats"] = {
                    "avg_price": int(sum(prices) / len(prices)),
                    "median_price": int(sorted(prices)[len(prices)//2]),
                    "total_listings": len(properties),
                    "price_range": f"${min(prices):,} - ${max(prices):,}"
                }

        # Cache the data
        if 'map_data_cache' not in st.session_state:
            st.session_state.map_data_cache = {}
        st.session_state.map_data_cache[cache_key] = {
            'data': map_data,
            'timestamp': datetime.now()
        }

    except Exception as e:
        st.warning(f"Could not load property data: {str(e)}")
        # Use demo data
        map_data["properties"] = get_demo_property_data(market)

    return map_data


def load_property_data(market: str) -> List[Dict[str, Any]]:
    """Load property data from Zillow and Redfin"""

    properties = []
    source = st.session_state.get('property_source', 'Both')

    # Get price filter
    price_filter = st.session_state.get('price_filter', 'All Prices')
    filters = {}
    if price_filter == "$0-$500K":
        filters = {"max_price": 500000}
    elif price_filter == "$500K-$1M":
        filters = {"min_price": 500000, "max_price": 1000000}
    elif price_filter == "$1M+":
        filters = {"min_price": 1000000}

    # Load from Zillow
    if source in ["Zillow", "Both"] and search_zillow_properties:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            zillow_props = loop.run_until_complete(
                search_zillow_properties(market, filters, 10)
            )
            loop.close()

            for prop in zillow_props:
                properties.append({
                    "source": "Zillow",
                    "id": prop.zpid,
                    "address": prop.address,
                    "price": prop.price,
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms,
                    "sqft": prop.sqft,
                    "lat": prop.lat,
                    "lon": prop.lon,
                    "property_type": prop.property_type,
                    "zestimate": getattr(prop, 'zestimate', None)
                })
        except Exception as e:
            st.warning(f"Zillow data loading failed: {str(e)}")

    # Load from Redfin
    if source in ["Redfin", "Both"] and search_redfin_properties:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            redfin_props = loop.run_until_complete(
                search_redfin_properties(market, filters, 10)
            )
            loop.close()

            for prop in redfin_props:
                properties.append({
                    "source": "Redfin",
                    "id": prop.property_id,
                    "address": prop.address,
                    "price": prop.price,
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms,
                    "sqft": prop.sqft,
                    "lat": prop.lat,
                    "lon": prop.lon,
                    "property_type": prop.property_type,
                    "days_on_market": getattr(prop, 'days_on_market', None)
                })
        except Exception as e:
            st.warning(f"Redfin data loading failed: {str(e)}")

    # Fallback to demo data if no properties loaded
    if not properties:
        properties = get_demo_property_data(market)

    return properties


def get_demo_property_data(market: str) -> List[Dict[str, Any]]:
    """Get demo property data when real APIs are not available"""

    if market == "Austin":
        return [
            {
                "source": "Zillow",
                "id": "zil_001",
                "address": "123 Demo St",
                "price": 750000,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "sqft": 2100,
                "lat": 30.2672,
                "lon": -97.7431,
                "property_type": "Single Family",
                "zestimate": 765000
            },
            {
                "source": "Redfin",
                "id": "rf_001",
                "address": "456 Sample Ave",
                "price": 525000,
                "bedrooms": 2,
                "bathrooms": 2.0,
                "sqft": 1650,
                "lat": 30.2700,
                "lon": -97.7300,
                "property_type": "Townhouse",
                "days_on_market": 15
            },
            {
                "source": "Zillow",
                "id": "zil_002",
                "address": "789 Example Ln",
                "price": 1200000,
                "bedrooms": 4,
                "bathrooms": 3.5,
                "sqft": 3200,
                "lat": 30.2500,
                "lon": -97.7800,
                "property_type": "Single Family",
                "zestimate": 1250000
            }
        ]
    else:
        return [
            {
                "source": "Zillow",
                "id": "zil_rc_001",
                "address": "321 Rancho Way",
                "price": 850000,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "sqft": 2200,
                "lat": 34.1200,
                "lon": -117.5700,
                "property_type": "Single Family",
                "zestimate": 870000
            }
        ]


def create_enhanced_map(map_data: Dict[str, Any], config: Dict[str, Any]) -> go.Figure:
    """Create enhanced Plotly map with leads and properties"""

    fig = go.Figure()
    view_mode = st.session_state.get('enhanced_map_view', 'Leads + Properties')

    # Add lead markers
    if view_mode in ["Leads Only", "Leads + Properties"]:
        add_lead_markers(fig, map_data["leads"])

    # Add property markers
    if view_mode in ["Properties Only", "Leads + Properties"]:
        add_property_markers(fig, map_data["properties"])

    # Add heat map if selected
    if view_mode == "Heat Map":
        add_combined_heat_map(fig, map_data["leads"], map_data["properties"])

    # Configure map layout
    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=config['center_lat'], lon=config['center_lon']),
            zoom=config['zoom']
        ),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        hovermode='closest',
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig


def add_lead_markers(fig: go.Figure, leads_data: List[Dict[str, Any]]):
    """Add lead markers to the map"""

    if not leads_data:
        return

    lats, lons, colors, sizes, texts, names = [], [], [], [], [], []

    for lead in leads_data:
        lats.append(lead.get('lat', 0))
        lons.append(lead.get('lon', 0))

        # Color and size based on lead score
        score = lead.get('lead_score', 50)
        if score >= 80:
            colors.append('#ef4444')
            sizes.append(16)
        elif score >= 50:
            colors.append('#f59e0b')
            sizes.append(14)
        else:
            colors.append('#3b82f6')
            sizes.append(12)

        # Hover text
        name = lead.get('name', 'Unknown Lead')
        budget = lead.get('budget', 0)
        hover_text = f"<b>👤 {name}</b><br>" \
                    f"Score: {score}<br>" \
                    f"Budget: ${budget:,}<br>" \
                    f"<i>Lead</i>"
        texts.append(hover_text)
        names.append(name)

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
        customdata=names,
        name='Leads',
        legendgroup='leads'
    ))


def add_property_markers(fig: go.Figure, properties_data: List[Dict[str, Any]]):
    """Add property markers to the map"""

    if not properties_data:
        return

    # Separate Zillow and Redfin properties
    zillow_props = [p for p in properties_data if p.get('source') == 'Zillow']
    redfin_props = [p for p in properties_data if p.get('source') == 'Redfin']

    # Add Zillow properties
    if zillow_props:
        add_property_trace(fig, zillow_props, 'Zillow', '#9333ea', '🏠')

    # Add Redfin properties
    if redfin_props:
        add_property_trace(fig, redfin_props, 'Redfin', '#dc2626', '🏡')


def add_property_trace(fig: go.Figure, properties: List[Dict[str, Any]], source: str, color: str, icon: str):
    """Add a property trace to the map"""

    lats, lons, texts, sizes = [], [], [], []

    for prop in properties:
        lats.append(prop.get('lat', 0))
        lons.append(prop.get('lon', 0))

        # Size based on price
        price = prop.get('price', 0)
        if price >= 1000000:
            sizes.append(14)
        elif price >= 500000:
            sizes.append(12)
        else:
            sizes.append(10)

        # Hover text
        address = prop.get('address', 'Unknown Address')
        price_text = f"${price:,}" if price else "Price N/A"
        beds = prop.get('bedrooms', 'N/A')
        baths = prop.get('bathrooms', 'N/A')
        sqft = prop.get('sqft', 'N/A')

        hover_text = f"<b>{icon} {address}</b><br>" \
                    f"Price: {price_text}<br>" \
                    f"Beds/Baths: {beds}/{baths}<br>" \
                    f"Sqft: {sqft}<br>" \
                    f"<i>Source: {source}</i>"
        texts.append(hover_text)

    fig.add_trace(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='markers',
        marker=dict(
            size=sizes,
            color=color,
            opacity=0.7,
            symbol='circle',
            line=dict(width=2, color='white')
        ),
        text=texts,
        hovertemplate='%{text}<extra></extra>',
        name=f'{source} Properties',
        legendgroup='properties'
    ))


def add_combined_heat_map(fig: go.Figure, leads_data: List[Dict[str, Any]], properties_data: List[Dict[str, Any]]):
    """Add combined heat map showing activity density"""

    # Combine lead and property coordinates with weights
    all_points = []

    # Add leads with higher weight
    for lead in leads_data:
        score = lead.get('lead_score', 50)
        weight = score / 100 * 2  # Lead weight 0-2
        all_points.append({
            'lat': lead.get('lat', 0),
            'lon': lead.get('lon', 0),
            'weight': weight
        })

    # Add properties with price-based weight
    for prop in properties_data:
        price = prop.get('price', 0)
        weight = min(price / 1000000, 1.0)  # Property weight 0-1
        all_points.append({
            'lat': prop.get('lat', 0),
            'lon': prop.get('lon', 0),
            'weight': weight
        })

    if all_points:
        lats = [p['lat'] for p in all_points]
        lons = [p['lon'] for p in all_points]
        weights = [p['weight'] for p in all_points]

        fig.add_trace(go.Densitymapbox(
            lat=lats,
            lon=lons,
            z=weights,
            radius=25,
            colorscale=[
                [0, '#3b82f6'],
                [0.5, '#f59e0b'],
                [1, '#ef4444']
            ],
            opacity=0.6,
            name='Activity Density'
        ))


def render_enhanced_legend():
    """Render enhanced map legend"""

    view_mode = st.session_state.get('enhanced_map_view', 'Leads + Properties')

    legend_html = "<div style='display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center; margin-top: 1rem; font-size: 0.85rem;'>"

    if view_mode in ["Leads Only", "Leads + Properties"]:
        legend_html += """
        <div style='display: flex; align-items: center; gap: 0.5rem;'>
            <div style='width: 16px; height: 16px; background: #ef4444; border-radius: 50%; border: 2px solid white;'></div>
            <span>🔥 Hot Leads (80+)</span>
        </div>
        <div style='display: flex; align-items: center; gap: 0.5rem;'>
            <div style='width: 14px; height: 14px; background: #f59e0b; border-radius: 50%; border: 2px solid white;'></div>
            <span>🔸 Warm Leads (50-79)</span>
        </div>
        <div style='display: flex; align-items: center; gap: 0.5rem;'>
            <div style='width: 12px; height: 12px; background: #3b82f6; border-radius: 50%; border: 2px solid white;'></div>
            <span>❄️ Cold Leads (0-49)</span>
        </div>
        """

    if view_mode in ["Properties Only", "Leads + Properties"]:
        legend_html += """
        <div style='display: flex; align-items: center; gap: 0.5rem;'>
            <div style='width: 14px; height: 14px; background: #9333ea; border-radius: 50%; border: 2px solid white;'></div>
            <span>🏠 Zillow Properties</span>
        </div>
        <div style='display: flex; align-items: center; gap: 0.5rem;'>
            <div style='width: 14px; height: 14px; background: #dc2626; border-radius: 50%; border: 2px solid white;'></div>
            <span>🏡 Redfin Properties</span>
        </div>
        """

    legend_html += "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)


def render_enhanced_detail_panel(leads_data: List[Dict[str, Any]], properties_data: List[Dict[str, Any]]):
    """Render enhanced detail panel with lead and property information"""

    st.markdown("#### 🎯 Market Intelligence")

    # Market stats summary
    if properties_data:
        total_properties = len(properties_data)
        avg_price = sum(p.get('price', 0) for p in properties_data if p.get('price', 0)) / max(1, len([p for p in properties_data if p.get('price', 0)]))

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Properties", total_properties)
        with col2:
            st.metric("Avg Price", f"${avg_price:,.0f}" if avg_price > 0 else "N/A")

    # Lead selector
    st.markdown("##### 👥 Select Lead")
    if leads_data:
        lead_options = ["Select a lead..."] + [f"{lead.get('name', 'Unknown')} ({lead.get('lead_score', 0)})" for lead in leads_data]
        selected_lead = st.selectbox(
            "Lead",
            lead_options,
            key="enhanced_lead_selector",
            label_visibility="collapsed"
        )

        if selected_lead != "Select a lead...":
            # Find and display selected lead
            lead_name = selected_lead.split(" (")[0]
            for lead in leads_data:
                if lead.get('name') == lead_name:
                    render_lead_detail_card(lead)
                    break

    st.markdown("---")

    # Property selector
    st.markdown("##### 🏠 Select Property")
    if properties_data:
        property_options = ["Select a property..."] + [f"{prop.get('address', 'Unknown')} - ${prop.get('price', 0):,}" for prop in properties_data]
        selected_property = st.selectbox(
            "Property",
            property_options,
            key="enhanced_property_selector",
            label_visibility="collapsed"
        )

        if selected_property != "Select a property...":
            # Find and display selected property
            property_address = selected_property.split(" - $")[0]
            for prop in properties_data:
                if prop.get('address') == property_address:
                    render_property_detail_card(prop)
                    break


def render_lead_detail_card(lead: Dict[str, Any]):
    """Render detailed lead information card"""

    name = lead.get('name', 'Unknown')
    score = lead.get('lead_score', 0)
    budget = lead.get('budget', 0)

    # Color based on score
    if score >= 80:
        color = "#ef4444"
        status = "🔥 HOT"
    elif score >= 50:
        color = "#f59e0b"
        status = "🔸 WARM"
    else:
        color = "#3b82f6"
        status = "❄️ COLD"

    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
                padding: 1rem; border-radius: 8px; border-left: 4px solid {color};'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <h4 style='margin: 0; color: #1e293b;'>{name}</h4>
            <span style='background: {color}; color: white; padding: 0.25rem 0.5rem;
                         border-radius: 4px; font-size: 0.75rem; font-weight: bold;'>{status}</span>
        </div>
        <div style='margin-top: 0.5rem; color: #475569;'>
            <div>Score: {score}/100</div>
            <div>Budget: ${budget:,}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_property_detail_card(prop: Dict[str, Any]):
    """Render detailed property information card"""

    address = prop.get('address', 'Unknown')
    price = prop.get('price', 0)
    source = prop.get('source', 'Unknown')
    beds = prop.get('bedrooms', 'N/A')
    baths = prop.get('bathrooms', 'N/A')
    sqft = prop.get('sqft', 'N/A')

    # Color based on source
    color = "#9333ea" if source == "Zillow" else "#dc2626"
    icon = "🏠" if source == "Zillow" else "🏡"

    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
                padding: 1rem; border-radius: 8px; border-left: 4px solid {color};'>
        <div style='display: flex; justify-content: space-between; align-items: start;'>
            <div style='flex: 1;'>
                <h4 style='margin: 0; color: #1e293b; font-size: 0.9rem;'>{icon} {address}</h4>
                <div style='margin-top: 0.5rem; color: #475569; font-size: 0.85rem;'>
                    <div><strong>${price:,}</strong></div>
                    <div>{beds} bed • {baths} bath • {sqft} sqft</div>
                </div>
            </div>
            <div style='background: {color}; color: white; padding: 0.25rem 0.5rem;
                        border-radius: 4px; font-size: 0.7rem; font-weight: bold;'>{source}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Main rendering function for external use
def render_enhanced_interactive_lead_map():
    """Main entry point for the enhanced lead property map"""

    # Get sample lead data
    market = st.selectbox("Market", ["Austin", "Rancho"], index=0, key="enhanced_market_selector")
    leads_data = generate_sample_lead_data(market)

    render_enhanced_lead_property_map(leads_data, market, True)