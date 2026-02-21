"""Warm Handoff Card Preview Component

Streamlit component for previewing and downloading warm handoff qualification cards.
Displays recent handoffs, generates PDF cards on-demand, and provides download functionality.

Usage:
    from ghl_real_estate_ai.streamlit_demo.components.handoff_card_preview import (
        render_handoff_card_preview,
    )
    render_handoff_card_preview()
"""

import base64
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from ghl_real_estate_ai.services.handoff_card_generator import generate_card

logger = logging.getLogger(__name__)

# Temperature emoji mapping
TEMPERATURE_EMOJI = {
    "hot": "🔥",
    "warm": "☀️",
    "lukewarm": "🌤️",
    "cold": "❄️",
}

# Bot emoji mapping
BOT_EMOJI = {
    "lead": "🎯",
    "buyer": "🏠",
    "seller": "📍",
}


def get_sample_handoff_data() -> List[Dict[str, Any]]:
    """Get sample handoff data for demonstration.

    In production, this would query the database or handoff service
    for recent handoff records.
    """
    from datetime import timezone

    return [
        {
            "contact_id": "demo_buyer_001",
            "contact_name": "Sarah Johnson",
            "contact_email": "sarah.j@example.com",
            "contact_phone": "+1-555-0100",
            "source_bot": "lead",
            "target_bot": "buyer",
            "confidence": 0.87,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "enriched_context": {
                "source_qualification_score": 82.5,
                "source_temperature": "hot",
                "budget_range": {"min": 450000, "max": 600000},
                "property_address": None,
                "cma_summary": None,
                "conversation_summary": "Pre-approved buyer looking for 3-4BR home in Rancho Cucamonga. "
                "Timeline: 2-3 months. Wants newer construction with good schools.",
                "key_insights": {
                    "pre_approval": True,
                    "budget_confirmed": True,
                    "timeline": "2-3 months",
                    "bedrooms": "3-4",
                    "location_preference": "Rancho Cucamonga",
                    "school_priority": True,
                    "construction_preference": "newer",
                },
                "urgency_level": "3_months",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
        {
            "contact_id": "demo_seller_001",
            "contact_name": "Michael Chen",
            "contact_email": "m.chen@example.com",
            "contact_phone": "+1-555-0101",
            "source_bot": "lead",
            "target_bot": "seller",
            "confidence": 0.79,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "enriched_context": {
                "source_qualification_score": 75.0,
                "source_temperature": "warm",
                "budget_range": None,
                "property_address": "8765 Elm Avenue, Rancho Cucamonga, CA 91730",
                "cma_summary": {
                    "estimated_value": 685000,
                    "value_range": {"min": 660000, "max": 710000},
                    "comparable_sales": 4,
                },
                "conversation_summary": "Motivated seller looking to list property due to job relocation. "
                "Property is well-maintained 4BR/3BA built in 2015. Wants to list within 4-6 weeks.",
                "key_insights": {
                    "motivation": "relocation",
                    "timeline": "4-6 weeks",
                    "property_condition": "well-maintained",
                    "bedrooms": 4,
                    "bathrooms": 3,
                    "year_built": 2015,
                },
                "urgency_level": "immediate",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
        {
            "contact_id": "demo_buyer_002",
            "contact_name": "Emily Rodriguez",
            "contact_email": "emily.r@example.com",
            "contact_phone": "+1-555-0102",
            "source_bot": "lead",
            "target_bot": "buyer",
            "confidence": 0.72,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "enriched_context": {
                "source_qualification_score": 68.0,
                "source_temperature": "lukewarm",
                "budget_range": {"min": 350000, "max": 450000},
                "property_address": None,
                "cma_summary": None,
                "conversation_summary": "First-time buyer exploring options. Pre-qualification in progress. "
                "Looking for 2-3BR starter home. Timeline flexible.",
                "key_insights": {
                    "first_time_buyer": True,
                    "pre_qualification_status": "in_progress",
                    "timeline": "flexible",
                    "bedrooms": "2-3",
                    "property_type": "starter home",
                },
                "urgency_level": "browsing",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    ]


def format_handoff_direction(source_bot: str, target_bot: str) -> str:
    """Format handoff direction with emojis."""
    source_emoji = BOT_EMOJI.get(source_bot, "🤖")
    target_emoji = BOT_EMOJI.get(target_bot, "🤖")
    return f"{source_emoji} {source_bot.capitalize()} → {target_emoji} {target_bot.capitalize()}"


def format_temperature(temperature: str) -> str:
    """Format temperature with emoji."""
    emoji = TEMPERATURE_EMOJI.get(temperature, "⚪")
    return f"{emoji} {temperature.capitalize()}"


def create_download_button(pdf_bytes: bytes, filename: str, key: str) -> None:
    """Create a download button for PDF bytes.

    Args:
        pdf_bytes: PDF content as bytes
        filename: Suggested filename for download
        key: Unique key for the download button
    """
    # Encode PDF to base64 for download
    b64 = base64.b64encode(pdf_bytes).decode()

    st.download_button(
        label="📥 Download Card",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        key=key,
        use_container_width=True,
    )


def render_handoff_card_preview(handoff_service=None) -> None:
    """Render the handoff card preview dashboard.

    Args:
        handoff_service: Optional JorgeHandoffService instance for fetching
            real handoff data. If None, displays sample data.
    """
    st.subheader("🤝 Warm Handoff Qualification Cards")

    st.markdown(
        """
        Professional PDF qualification cards for agent handoffs. Each card provides
        a quick visual summary of lead qualification, scores, and conversation insights.
        """
    )

    # Tabs for different views
    tab_preview, tab_generate, tab_recent = st.tabs(["Card Preview", "Generate Card", "Recent Handoffs"])

    with tab_preview:
        _render_preview_tab()

    with tab_generate:
        _render_generate_tab()

    with tab_recent:
        _render_recent_tab(handoff_service)


def _render_preview_tab() -> None:
    """Render the card preview tab with sample cards."""
    st.markdown("### Sample Handoff Cards")

    sample_data = get_sample_handoff_data()

    # Display first sample card by default
    selected_idx = st.selectbox(
        "Select sample handoff:",
        range(len(sample_data)),
        format_func=lambda idx: (
            f"{sample_data[idx]['contact_name']} ({sample_data[idx]['source_bot']} → {sample_data[idx]['target_bot']})"
        ),
        key="preview_sample_select",
    )

    selected_handoff = sample_data[selected_idx]

    # Display handoff details
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Direction",
            format_handoff_direction(selected_handoff["source_bot"], selected_handoff["target_bot"]),
        )
    with col2:
        context = selected_handoff["enriched_context"]
        st.metric(
            "Temperature",
            format_temperature(context["source_temperature"]),
        )
    with col3:
        st.metric(
            "Qualification Score",
            f"{context['source_qualification_score']:.1f}/100",
        )

    st.divider()

    # Generate and display download button
    try:
        pdf_bytes = generate_card(selected_handoff)
        filename = f"handoff_card_{selected_handoff['contact_id']}.pdf"

        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ Card generated successfully ({len(pdf_bytes):,} bytes)")
        with col2:
            create_download_button(pdf_bytes, filename, f"download_preview_{selected_idx}")

    except Exception as e:
        st.error(f"Failed to generate card: {e}")
        logger.error(f"Card generation error: {e}", exc_info=True)


def _render_generate_tab() -> None:
    """Render the card generation tab with custom input."""
    st.markdown("### Generate Custom Card")

    with st.form("custom_card_form"):
        st.markdown("**Contact Information**")
        col1, col2 = st.columns(2)
        with col1:
            contact_name = st.text_input("Contact Name*", placeholder="John Doe")
            contact_email = st.text_input("Email", placeholder="john@example.com")
        with col2:
            contact_id = st.text_input("Contact ID*", placeholder="contact_123")
            contact_phone = st.text_input("Phone", placeholder="+1-555-0123")

        st.divider()

        st.markdown("**Handoff Details**")
        col1, col2, col3 = st.columns(3)
        with col1:
            source_bot = st.selectbox("Source Bot*", ["lead", "buyer", "seller"])
        with col2:
            target_bot = st.selectbox("Target Bot*", ["lead", "buyer", "seller"])
        with col3:
            confidence = st.slider("Confidence", 0.0, 1.0, 0.75, 0.05)

        st.divider()

        st.markdown("**Qualification Data**")
        col1, col2, col3 = st.columns(3)
        with col1:
            qual_score = st.number_input("Qualification Score*", 0.0, 100.0, 70.0, 1.0)
        with col2:
            temperature = st.selectbox("Temperature*", ["hot", "warm", "lukewarm", "cold"])
        with col3:
            urgency = st.selectbox(
                "Urgency Level*",
                ["immediate", "3_months", "6_months", "browsing"],
                format_func=lambda x: x.replace("_", " ").title(),
            )

        conversation_summary = st.text_area(
            "Conversation Summary",
            placeholder="Summarize the key points from the conversation...",
            height=100,
        )

        # Budget range (optional)
        include_budget = st.checkbox("Include Budget Range", value=False)
        budget_min, budget_max = None, None
        if include_budget:
            col1, col2 = st.columns(2)
            with col1:
                budget_min = st.number_input("Budget Min ($)", 0, 10000000, 400000, 10000)
            with col2:
                budget_max = st.number_input("Budget Max ($)", 0, 10000000, 600000, 10000)

        submit = st.form_submit_button("Generate Card", use_container_width=True)

        if submit:
            # Validate required fields
            if not contact_name or not contact_id:
                st.error("Please fill in all required fields (marked with *).")
                return

            # Build handoff data
            handoff_data = {
                "contact_id": contact_id,
                "contact_name": contact_name,
                "contact_email": contact_email or "N/A",
                "contact_phone": contact_phone or "N/A",
                "source_bot": source_bot,
                "target_bot": target_bot,
                "confidence": confidence,
                "enriched_context": {
                    "source_qualification_score": qual_score,
                    "source_temperature": temperature,
                    "budget_range": ({"min": budget_min, "max": budget_max} if include_budget else None),
                    "conversation_summary": conversation_summary,
                    "key_insights": {},
                    "urgency_level": urgency,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            # Generate card
            try:
                with st.spinner("Generating card..."):
                    pdf_bytes = generate_card(handoff_data)
                    filename = f"handoff_card_{contact_id}.pdf"

                st.success(f"✅ Card generated successfully ({len(pdf_bytes):,} bytes)")
                create_download_button(pdf_bytes, filename, "download_custom")

            except Exception as e:
                st.error(f"Failed to generate card: {e}")
                logger.error(f"Custom card generation error: {e}", exc_info=True)


def _render_recent_tab(handoff_service: Optional[Any]) -> None:
    """Render the recent handoffs tab.

    Args:
        handoff_service: Optional JorgeHandoffService instance for fetching
            real handoff data. If None, displays sample data.
    """
    st.markdown("### Recent Handoffs")

    # For now, use sample data (in production, query handoff_service)
    if handoff_service is None:
        st.info("Displaying sample data. Connect handoff service for live data.")
        recent_handoffs = get_sample_handoff_data()
    else:
        # ROADMAP-070: Query live handoff data from service
        try:
            analytics = handoff_service.get_analytics_summary()
            live_handoffs = analytics.get("recent_handoffs", [])
            if live_handoffs:
                recent_handoffs = live_handoffs
            else:
                st.info("No recent live handoffs. Showing sample data.")
                recent_handoffs = get_sample_handoff_data()
        except Exception as e:
            logger.warning(f"Failed to fetch live handoff data: {e}")
            st.warning("Could not fetch live data. Showing sample data.")
            recent_handoffs = get_sample_handoff_data()

    if not recent_handoffs:
        st.info("No recent handoffs to display.")
        return

    # Display handoffs in a table
    for idx, handoff in enumerate(recent_handoffs):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1, 1])

            with col1:
                st.text(handoff["contact_name"])
                st.caption(handoff["contact_id"])

            with col2:
                direction = format_handoff_direction(handoff["source_bot"], handoff["target_bot"])
                st.text(direction)

            with col3:
                context = handoff["enriched_context"]
                temp = format_temperature(context["source_temperature"])
                st.text(temp)
                st.caption(f"Score: {context['source_qualification_score']:.1f}")

            with col4:
                confidence_pct = f"{handoff['confidence'] * 100:.0f}%"
                st.metric("Confidence", confidence_pct)

            with col5:
                # Generate card button
                if st.button("Generate", key=f"gen_recent_{idx}", use_container_width=True):
                    try:
                        pdf_bytes = generate_card(handoff)
                        filename = f"handoff_card_{handoff['contact_id']}.pdf"
                        create_download_button(pdf_bytes, filename, f"download_recent_{idx}")
                    except Exception as e:
                        st.error(f"Failed: {e}")
                        logger.error(f"Recent card generation error: {e}", exc_info=True)

            st.divider()


# Convenience function for standalone use
def render_handoff_card_dashboard() -> None:
    """Render the full handoff card dashboard (alias for render_handoff_card_preview)."""
    render_handoff_card_preview()
