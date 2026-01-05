"""
Property matching cards component.
"""
import streamlit as st


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


def render_property_card(property: dict):
    """Render single property card."""
    neighborhood = property.get('neighborhood', '')
    if not neighborhood:
        address = property.get('address', {})
        if isinstance(address, dict):
            neighborhood = address.get('neighborhood', 'Unknown')
        else:
            neighborhood = 'Unknown'

    st.markdown(f"""
    <div style='padding: 15px; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 10px; min-height: 200px;'>
        <h4 style='margin-top: 0;'>{neighborhood}</h4>
        <p style='font-size: 1.2em; color: #1f77b4;'><strong>${property.get('price', 0):,}</strong></p>
        <p>{property.get('bedrooms', 0)} BR | {property.get('bathrooms', 0)} BA</p>
        <p>{property.get('sqft', 0):,} sqft</p>
        <p style='color: green;'><strong>Match: {property.get('match_score', 0):.0f}%</strong></p>
    </div>
    """, unsafe_allow_html=True)