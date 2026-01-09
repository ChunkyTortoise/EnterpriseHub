"""
Premium Property Cards Component
Enterprise-grade property display with enhanced visual design
"""
import streamlit as st
from typing import Dict, List, Any


def render_property_matches():
    """Render matched properties."""
    st.markdown("### 🏠 Property Matches")

    # Check if we have preferences to match against
    prefs = st.session_state.get('extracted_data', {})
    if not prefs:
        st.info("Share your preferences in the chat to see property matches!")
        return

    # Get property matches from mock RAG
    from streamlit_demo.mock_services.mock_rag import MockRAGService

    rag = MockRAGService()
    matches = rag.search_properties(prefs, top_k=3)

    if not matches:
        st.warning("No matches found - try adjusting your criteria!")
        return

    # Display properties
    cols = st.columns(3)

    for i, prop in enumerate(matches):
        with cols[i]:
            render_property_card(prop)


def render_premium_property_grid(properties: List[Dict], max_properties: int = 3):
    """Render properties in premium grid layout with enhanced cards."""

    # Display in responsive columns
    if len(properties) == 1:
        cols = [st.container()]
    elif len(properties) == 2:
        cols = st.columns(2)
    else:
        cols = st.columns(min(3, len(properties)))

    for i, property in enumerate(properties[:max_properties]):
        with cols[i % len(cols)]:
            render_premium_property_card(property, index=i)


def render_premium_property_card(property: Dict[str, Any], index: int = 0):
    """
    Render a single premium property card with enterprise styling.

    Args:
        property: Property data dictionary
        index: Card index for unique keys
    """
    # Extract property details with fallbacks
    price = property.get('price', 0)
    beds = property.get('beds', property.get('bedrooms', 3))
    baths = property.get('baths', property.get('bathrooms', 2))
    sqft = property.get('sqft', 2000)
    address = property.get('address', 'Address TBD')
    neighborhood = property.get('neighborhood', 'Austin Area')
    match_score = property.get('match_score', 85)

    # Color coding based on match score
    if match_score >= 90:
        match_color = "#10b981"
        match_bg = "#dcfce7"
        card_bg = "#f0fdf4"
        border_color = "#10b981"
    elif match_score >= 80:
        match_color = "#3b82f6"
        match_bg = "#dbeafe"
        card_bg = "#eff6ff"
        border_color = "#3b82f6"
    else:
        match_color = "#f59e0b"
        match_bg = "#fef3c7"
        card_bg = "#fffbeb"
        border_color = "#f59e0b"

    # Use Streamlit native components with simplified styling
    with st.container():
        # Property card container with background
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {card_bg} 0%, #ffffff 100%);
            border-radius: 16px;
            border: 2px solid {border_color};
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        </div>
        """, unsafe_allow_html=True)

        # Match score badge and header
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"### 🏡 {address}")
            st.markdown(f"📍 **{neighborhood}**")

        with col2:
            st.markdown(f"""
            <div style="
                background: {match_bg};
                color: {match_color};
                padding: 8px 16px;
                border-radius: 20px;
                text-align: center;
                font-weight: bold;
                font-size: 0.9rem;">
                {match_score}% Match
            </div>
            """, unsafe_allow_html=True)

        # Price display
        st.markdown(f"""
        <div style="
            font-size: 2rem;
            font-weight: bold;
            color: #059669;
            margin: 16px 0;">
            ${price:,}
        </div>
        """, unsafe_allow_html=True)

        # Property stats using Streamlit columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Bedrooms",
                value=str(beds)
            )

        with col2:
            st.metric(
                label="Bathrooms",
                value=str(baths)
            )

        with col3:
            st.metric(
                label="Sq Ft",
                value=f"{sqft:,}"
            )

        # Action buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "📤 Send to Lead",
                key=f"premium_send_{index}",
                use_container_width=True,
                type="primary"
            ):
                st.toast(f"Sent {address} to lead!", icon="✅")

        with col2:
            if st.button(
                "📅 Schedule Tour",
                key=f"premium_schedule_{index}",
                use_container_width=True
            ):
                st.toast("Opening calendar...", icon="📅")

        # Add spacing
        st.markdown("<br>", unsafe_allow_html=True)


def render_property_card(property: dict):
    """
    Legacy property card renderer for backward compatibility.
    Enhanced with improved styling.
    """
    neighborhood = property.get('neighborhood', '')
    if not neighborhood:
        address = property.get('address', {})
        if isinstance(address, dict):
            neighborhood = address.get('neighborhood', 'Unknown')
        else:
            neighborhood = 'Unknown'

    price = property.get('price', 0)
    bedrooms = property.get('bedrooms', 0)
    bathrooms = property.get('bathrooms', 0)
    sqft = property.get('sqft', 0)
    match_score = property.get('match_score', 0)

    # Enhanced card styling
    st.markdown(f"""
    <div style='
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 20px;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        margin-bottom: 16px;
        min-height: 220px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    '>
        <h4 style='margin: 0 0 12px 0; color: #1e293b; font-size: 1.2rem; font-weight: 600;'>
            📍 {neighborhood}
        </h4>

        <div style='font-size: 1.5rem; color: #059669; font-weight: 700; margin-bottom: 12px;'>
            ${price:,}
        </div>

        <div style='display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 0.95rem; color: #475569;'>
            <span><strong>{bedrooms}</strong> BR</span>
            <span><strong>{bathrooms}</strong> BA</span>
            <span><strong>{sqft:,}</strong> sqft</span>
        </div>

        <div style='
            background: {"#dcfce7" if match_score >= 90 else "#dbeafe" if match_score >= 80 else "#fef3c7"};
            color: {"#166534" if match_score >= 90 else "#1e40af" if match_score >= 80 else "#92400e"};
            padding: 8px 12px;
            border-radius: 6px;
            text-align: center;
            font-weight: 600;
            font-size: 0.9rem;
        '>
            🎯 Match: {match_score:.0f}%
        </div>
    </div>
    """, unsafe_allow_html=True)