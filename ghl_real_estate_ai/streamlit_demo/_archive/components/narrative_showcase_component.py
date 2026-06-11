"""
Narrative Showcase Component - Demonstrates PersonalizedNarrativeEngine integration.

Shows how to integrate the PersonalizedNarrativeEngine into existing Streamlit
property matching workflows for enhanced user experience.
"""

import asyncio
import time
from typing import Any, Dict, Optional

import streamlit as st

from ghl_real_estate_ai.models.matching_models import LifestyleScores
from ghl_real_estate_ai.services.personalized_narrative_engine import (
    NarrativeLength,
    NarrativeStyle,
    PersonalizedNarrativeEngine,
)
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async


@st.cache_resource
def get_narrative_engine() -> PersonalizedNarrativeEngine:
    """Get cached narrative engine instance."""
    return PersonalizedNarrativeEngine(enable_caching=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def generate_narrative_sync(
    property_data: Dict[str, Any],
    lead_data: Dict[str, Any],
    lifestyle_scores: Optional[LifestyleScores],
    style: str,
    length: str,
) -> Dict[str, Any]:
    """Synchronous wrapper for narrative generation (for Streamlit caching)."""
    try:
        engine = get_narrative_engine()

        # Convert string enums back to proper types
        narrative_style = NarrativeStyle(style)
        narrative_length = NarrativeLength(length)

        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        narrative = run_async(
            engine.generate_personalized_narrative(
                property_data=property_data,
                lead_data=lead_data,
                lifestyle_scores=lifestyle_scores,
                style=narrative_style,
                length=narrative_length,
            )
        )

        loop.close()

        # Convert to dict for caching
        return {
            "property_id": narrative.property_id,
            "lead_id": narrative.lead_id,
            "narrative_text": narrative.narrative_text,
            "style": narrative.style.value,
            "length": narrative.length.value,
            "appeal_score": narrative.overall_appeal_score,
            "key_selling_points": narrative.key_selling_points,
            "emotional_themes": narrative.emotional_themes,
            "call_to_action": narrative.call_to_action,
            "generation_time_ms": narrative.generation_time_ms,
            "model_used": narrative.model_used,
            "cached": narrative.cached,
            "fallback_used": narrative.fallback_used,
        }
    except Exception as e:
        st.error(f"Narrative generation error: {e}")
        return None


def render_narrative_showcase():
    """Main narrative showcase component."""

    st.markdown(
        """
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;
                box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);'>
        <h2 style='color: white !important; margin: 0 0 1rem 0; text-align: center;'>
            🤖 PersonalizedNarrativeEngine Showcase
        </h2>
        <p style='color: rgba(255,255,255,0.9); margin: 0; text-align: center; font-size: 1.1rem;'>
            Transform generic property listings into compelling, personalized lifestyle stories
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Configuration section
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown("### 🎯 Narrative Style")
        style = st.selectbox(
            "Select style",
            options=["emotional", "professional", "investment", "luxury", "lifestyle"],
            index=0,
            help="Choose the narrative style that matches your buyer persona",
        )

    with col2:
        st.markdown("### 📏 Narrative Length")
        length = st.selectbox(
            "Select length",
            options=["short", "medium", "long"],
            index=1,
            help="Short: SMS/quick preview, Medium: email/cards, Long: presentations",
        )

    with col3:
        st.markdown("### 🏡 Property Selection")
        property_choice = st.selectbox(
            "Choose property",
            options=[
                "Westlake Hills - $485K (Family Home)",
                "Downtown Rancho Cucamonga - $620K (Urban Condo)",
                "Haven City - $395K (Growing Community)",
            ],
            index=0,
        )

    # Sample data based on selection
    properties = {
        "Westlake Hills - $485K (Family Home)": {
            "id": "prop_westlake_001",
            "address": "123 Hill Country Dr, Westlake Hills, CA",
            "price": 485000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 2100,
            "neighborhood": "Westlake Hills",
            "features": ["pool", "deck", "two-car garage", "updated kitchen"],
            "property_type": "single_family",
        },
        "Downtown Rancho Cucamonga - $620K (Urban Condo)": {
            "id": "prop_downtown_002",
            "address": "456 Congress Ave, Downtown Rancho Cucamonga, CA",
            "price": 620000,
            "bedrooms": 2,
            "bathrooms": 2,
            "sqft": 1650,
            "neighborhood": "Downtown Rancho Cucamonga",
            "features": ["city views", "rooftop pool", "concierge", "parking garage"],
            "property_type": "condo",
        },
        "Haven City - $395K (Growing Community)": {
            "id": "prop_haven city_003",
            "address": "789 Haven City Blvd, Haven City, CA",
            "price": 395000,
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 2400,
            "neighborhood": "Haven City",
            "features": ["open floor plan", "master suite", "backyard", "community amenities"],
            "property_type": "single_family",
        },
    }

    property_data = properties[property_choice]

    # Lead profile selection
    st.markdown("### 👤 Buyer Profile")
    lead_cols = st.columns([1, 1])

    with lead_cols[0]:
        lead_choice = st.selectbox(
            "Select buyer persona",
            options=[
                "Sarah Chen - Family (Tech Professional)",
                "David Kim - Young Professional",
                "Maria Gonzalez - Real Estate Investor",
            ],
            index=0,
        )

    leads = {
        "Sarah Chen - Family (Tech Professional)": {
            "lead_id": "lead_sarah_chen",
            "lead_name": "Sarah Chen",
            "family_status": "family_with_kids",
            "workplace": "Apple",
            "budget_max": 500000,
            "lifestyle_priorities": ["schools", "commute", "safety"],
            "age": 34,
            "children_ages": [7, 10],
        },
        "David Kim - Young Professional": {
            "lead_id": "lead_david_kim",
            "lead_name": "David Kim",
            "family_status": "young_professional",
            "workplace": "Downtown Rancho Cucamonga",
            "budget_max": 650000,
            "lifestyle_priorities": ["walkability", "nightlife", "commute"],
            "age": 28,
            "children_ages": [],
        },
        "Maria Gonzalez - Real Estate Investor": {
            "lead_id": "lead_maria_gonzalez",
            "lead_name": "Maria Gonzalez",
            "family_status": "investor",
            "workplace": "Remote",
            "budget_max": 450000,
            "lifestyle_priorities": ["investment_potential", "rental_income", "appreciation"],
            "age": 42,
            "children_ages": [],
        },
    }

    lead_data = leads[lead_choice]

    with lead_cols[1]:
        st.markdown("**Selected Profile:**")
        st.write(f"👤 {lead_data['lead_name']}")
        st.write(f"👨‍👩‍👧‍👦 {lead_data['family_status'].replace('_', ' ').title()}")
        st.write(f"💰 Budget: ${lead_data['budget_max']:,}")

    # Generate button
    if st.button("🚀 Generate Personalized Narrative", type="primary", use_container_width=True):
        with st.spinner("Generating personalized narrative..."):
            start_time = time.time()

            # Generate narrative
            narrative_data = generate_narrative_sync(
                property_data=property_data,
                lead_data=lead_data,
                lifestyle_scores=None,  # Could be integrated from lifestyle service
                style=style,
                length=length,
            )

            generation_time = (time.time() - start_time) * 1000

        if narrative_data:
            # Display results
            st.markdown("---")
            st.markdown("## 📝 Generated Narrative")

            # Metrics row
            metric_cols = st.columns(4)
            with metric_cols[0]:
                st.metric("Generation Time", f"{generation_time:.0f}ms")
            with metric_cols[1]:
                st.metric("Appeal Score", f"{narrative_data['appeal_score']:.1f}/10")
            with metric_cols[2]:
                cache_status = "✅ Cache Hit" if narrative_data["cached"] else "🆕 Generated"
                st.metric("Cache Status", cache_status)
            with metric_cols[3]:
                model_display = (
                    "📝 Template" if narrative_data["fallback_used"] else f"🤖 {narrative_data['model_used']}"
                )
                st.metric("Model Used", model_display)

            # Main narrative display
            st.markdown(
                f"""
            <div style='background: #f8f9fa; padding: 2rem; border-radius: 12px; border-left: 4px solid #667eea; margin: 1rem 0;'>
                <h4 style='color: #333; margin-top: 0;'>
                    🏡 {property_data["address"]} • {style.title()} Style • {length.title()} Length
                </h4>
                <div style='font-size: 1.1rem; line-height: 1.6; color: #444;'>
                    {narrative_data["narrative_text"]}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Additional details in expandable sections
            col1, col2 = st.columns(2)

            with col1:
                with st.expander("🎯 Key Selling Points"):
                    for i, point in enumerate(narrative_data["key_selling_points"][:5], 1):
                        st.write(f"{i}. {point}")

                with st.expander("💫 Emotional Themes"):
                    for theme in narrative_data["emotional_themes"]:
                        st.write(f"• {theme.replace('_', ' ').title()}")

            with col2:
                with st.expander("📞 Call to Action"):
                    st.write(narrative_data["call_to_action"])

                with st.expander("⚡ Performance Details"):
                    st.write(f"**Generation Time**: {narrative_data.get('generation_time_ms', 0)}ms")
                    st.write(f"**Cached**: {'Yes' if narrative_data['cached'] else 'No'}")
                    st.write(f"**Fallback Used**: {'Yes' if narrative_data['fallback_used'] else 'No'}")
                    st.write(f"**Word Count**: {len(narrative_data['narrative_text'].split())} words")

            # Action buttons
            st.markdown("---")
            action_cols = st.columns(4)

            with action_cols[0]:
                if st.button("📧 Send via Email"):
                    st.success("Narrative queued for email delivery!")

            with action_cols[1]:
                if st.button("📱 Send via SMS"):
                    if length == "short":
                        st.success("Narrative sent via SMS!")
                    else:
                        st.warning("Consider 'Short' length for SMS delivery")

            with action_cols[2]:
                if st.button("📋 Copy to Clipboard"):
                    st.info("Narrative copied! (Feature requires client-side JavaScript)")

            with action_cols[3]:
                if st.button("🔄 Generate Variant"):
                    st.rerun()


def render_batch_narrative_demo():
    """Demonstrate batch narrative generation."""

    st.markdown("### 🚀 Batch Narrative Generation")
    st.markdown("*Simulate property search results with personalized narratives*")

    if st.button("Generate Narratives for All Properties", type="secondary"):
        with st.spinner("Generating batch narratives..."):
            # Sample properties
            properties = [
                {
                    "id": "prop_1",
                    "address": "123 Hill Country Dr, Westlake Hills, CA",
                    "price": 485000,
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "neighborhood": "Westlake Hills",
                },
                {
                    "id": "prop_2",
                    "address": "456 Congress Ave, Downtown Rancho Cucamonga, CA",
                    "price": 620000,
                    "bedrooms": 2,
                    "bathrooms": 2,
                    "neighborhood": "Downtown Rancho Cucamonga",
                },
                {
                    "id": "prop_3",
                    "address": "789 Haven City Blvd, Haven City, CA",
                    "price": 395000,
                    "bedrooms": 4,
                    "bathrooms": 3,
                    "neighborhood": "Haven City",
                },
            ]

            # Sample lead
            lead_data = {
                "lead_id": "lead_demo",
                "lead_name": "Demo User",
                "family_status": "family_with_kids",
                "budget_max": 500000,
                "lifestyle_priorities": ["schools", "commute", "safety"],
            }

            start_time = time.time()

            # Generate narratives for all properties
            narratives = []
            for prop in properties:
                narrative_data = generate_narrative_sync(
                    property_data=prop, lead_data=lead_data, lifestyle_scores=None, style="emotional", length="short"
                )
                if narrative_data:
                    narratives.append((prop, narrative_data))

            total_time = (time.time() - start_time) * 1000

            # Display results
            st.success(f"Generated {len(narratives)} narratives in {total_time:.0f}ms!")

            for prop, narrative in narratives:
                with st.container():
                    st.markdown(
                        f"""
                    <div style='border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;'>
                        <h5 style='margin: 0 0 0.5rem 0; color: #333;'>
                            {prop["address"].split(",")[0]} • ${prop["price"]:,}
                        </h5>
                        <p style='margin: 0; color: #666; font-size: 0.9rem;'>
                            {narrative["narrative_text"][:150]}...
                        </p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )


def render_performance_metrics():
    """Show engine performance metrics."""
    try:
        engine = get_narrative_engine()
        metrics = engine.get_performance_metrics()

        st.markdown("### ⚡ Engine Performance Metrics")

        metric_cols = st.columns(3)
        with metric_cols[0]:
            st.metric("Total Generations", metrics["total_generations"])
        with metric_cols[1]:
            st.metric("Cache Hit Rate", f"{metrics['cache_hit_rate_percent']:.1f}%")
        with metric_cols[2]:
            st.metric("Fallback Rate", f"{metrics['fallback_rate_percent']:.1f}%")

    except Exception as e:
        st.error(f"Unable to load metrics: {e}")


# Main component function
def main():
    """Main showcase component."""
    st.set_page_config(page_title="PersonalizedNarrativeEngine Showcase", page_icon="🤖", layout="wide")

    render_narrative_showcase()

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        render_batch_narrative_demo()
    with col2:
        render_performance_metrics()


if __name__ == "__main__":
    main()
