"""
Premium Property Cards Component
Enterprise-grade property display with enhanced visual design
"""

from typing import Any, Dict, List

import streamlit as st


def render_property_matches():
    """Render matched properties."""
    st.markdown("### 🏠 Property Matches")

    # Check if we have preferences to match against
    prefs = st.session_state.get("extracted_data", {})
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
    Uses CSS classes defined in styles.css for high-impact visual appeal.
    """
    # Extract property details with fallbacks
    price = property.get("price", 0)
    beds = property.get("beds", property.get("bedrooms", 3))
    baths = property.get("baths", property.get("bathrooms", 2))
    sqft = property.get("sqft", 2000)
    address = property.get("address", "Address TBD")
    neighborhood = property.get("neighborhood", "Rancho Cucamonga Area")
    match_score = property.get("match_score", 85)

    # AI reasoning fallback
    ai_insight = property.get("match_reasons", ["Matches your budget and location preferences."])[0]

    # Map match score to confidence level
    confidence = "High" if match_score >= 90 else "Medium" if match_score >= 80 else "Low"

    # Use the sophisticated HTML structure from styles.css
    st.markdown(
        f"""
    <div class="holographic-card premium-property-card">
        <div class="property-image-container">
            <div class="match-score-badge">
                <span>✨ {match_score}% Match</span>
            </div>
            <div class="favorite-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l8.84-8.84 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
            </div>
            <img src="https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&q=80&w=600" class="property-image" alt="Property">
        </div>
        <div class="property-card-content">
            <div class="property-card-header">
                <div class="property-title" style="color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;">{address.upper()}</div>
                <div class="property-price-premium">${price:,}</div>
            </div>
            <div class="property-location">
                <span style="color: #8B949E; font-family: 'Inter', sans-serif; font-weight: 600;">📍 {neighborhood.upper()}</span>
            </div>
            
            <div class="property-specs" style="border-color: rgba(255,255,255,0.05);">
                <div class="property-spec-item" style="color: #E6EDF3;">🛏️ {beds} BEDS</div>
                <div class="property-spec-item" style="color: #E6EDF3;">🚿 {baths} BATHS</div>
                <div class="property-spec-item" style="color: #E6EDF3;">📐 {sqft:,} SQFT</div>
            </div>
            
            <div class="ai-insight-box">
                <div class="ai-insight-text" style="color: #E6EDF3; font-family: 'Inter', sans-serif; opacity: 0.9;">{ai_insight}</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Action buttons using Streamlit columns for interactivity
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Send to Lead", key=f"premium_send_{index}", use_container_width=True, type="primary"):
            st.toast(f"Sent {address} to lead!", icon="✅")
    with col2:
        if st.button("📅 Schedule Tour", key=f"premium_schedule_{index}", use_container_width=True):
            st.toast("Opening calendar...", icon="📅")

    st.markdown("<br>", unsafe_allow_html=True)


def render_property_card(property: dict):
    """
    Legacy property card renderer for backward compatibility.
    Enhanced with improved styling.
    """
    neighborhood = property.get("neighborhood", "")
    if not neighborhood:
        address = property.get("address", {})
        if isinstance(address, dict):
            neighborhood = address.get("neighborhood", "Unknown")
        else:
            neighborhood = "Unknown"

    price = property.get("price", 0)
    bedrooms = property.get("bedrooms", 0)
    bathrooms = property.get("bathrooms", 0)
    sqft = property.get("sqft", 0)
    match_score = property.get("match_score", 0)

    # Enhanced card styling - Obsidian Edition
    st.markdown(
        f"""

        <div class="holographic-card" style='

            background: rgba(22, 27, 34, 0.7);

            padding: 1.5rem;

            border: 1px solid rgba(255, 255, 255, 0.05);

            border-top: 1px solid rgba(255, 255, 255, 0.1);

            border-radius: 12px;

            margin-bottom: 1.25rem;

            min-height: 240px;

            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6);

            backdrop-filter: blur(12px);

            transition: transform 0.3s ease, border-color 0.3s ease;

        '>

            <h4 style='margin: 0 0 1rem 0; color: #FFFFFF; font-size: 1.1rem; font-weight: 700; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.05em;'>

                📍 {neighborhood.upper()}

            </h4>

    

            <div style='font-size: 1.75rem; color: #6366F1; font-weight: 700; margin-bottom: 1rem; font-family: "Space Grotesk", sans-serif;'>

                ${price:,}

            </div>

    

            <div style='display: flex; justify-content: space-between; margin-bottom: 1.25rem; font-size: 0.85rem; color: #8B949E; font-family: "Inter", sans-serif; font-weight: 600;'>

                <span><b style="color: #E6EDF3;">{bedrooms}</b> BR</span>

                <span><b style="color: #E6EDF3;">{bathrooms}</b> BA</span>

                <span><b style="color: #E6EDF3;">{sqft:,}</b> SQFT</span>

            </div>

    

            <div style='

                background: rgba(99, 102, 241, 0.1);

                color: #6366F1;

                padding: 10px 15px;

                border-radius: 8px;

                text-align: center;

                font-weight: 700;

                font-size: 0.8rem;

                border: 1px solid rgba(99, 102, 241, 0.2);

                font-family: "Space Grotesk", sans-serif;

                text-transform: uppercase;

                letter-spacing: 0.1em;

            '>

                SIGNAL MATCH: {match_score:.0f}%

            </div>

        </div>

        """,
        unsafe_allow_html=True,
    )
