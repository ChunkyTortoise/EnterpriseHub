"""
Property Matcher AI Component
AI-powered property matching with reasoning and scoring breakdown
"""

from typing import Dict, List

import streamlit as st

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

# Import Primitive Components
from ghl_real_estate_ai.streamlit_demo.components.primitives import CardConfig, render_obsidian_card


def render_property_matcher(lead_context: Dict, elite_mode: bool = False, analysis_result=None):
    """
    AI-powered property matching with reasoning

    Args:
        lead_context: Dictionary containing lead preferences and information
        elite_mode: Whether to use elite phase features (Strategy Pattern)
        analysis_result: UnifiedScoringResult from Claude (optional)
    """
    st.markdown("### 🏠 AI Property Matcher")
    st.markdown("*Showing properties matched to lead criteria*")
    matches = generate_property_matches(lead_context, elite_mode=elite_mode)
    try:
        from components.property_cards import render_premium_property_grid

        st.markdown("#### 🏡 Top Property Matches")
        render_premium_property_grid(matches[:3])
        st.markdown("---")
        st.markdown("#### 📊 Detailed Analysis")
    except ImportError:
        st.info("🚀 Premium property cards available in enterprise version")
    if "compare_props" not in st.session_state:
        st.session_state.compare_props = set()
    if len(st.session_state.compare_props) >= 2:
        if st.button(
            f"⚖️ Compare Selected ({len(st.session_state.compare_props)})", type="primary", key="compare_btn_top"
        ):
            st.markdown("### ⚖️ Property Comparison")
            selected_matches = [m for m in matches if m["address"] in st.session_state.compare_props]
            if len(selected_matches) < 2:
                st.warning("Please select at least 2 properties to compare.")
            else:
                compare_subset = selected_matches[:3]
                cols = st.columns(len(compare_subset))
                for idx, col in enumerate(cols):
                    prop = compare_subset[idx]
                    with col:
                        render_obsidian_card(
                            title=prop["address"].upper(),
                            content=f"""
                            <div style='font-size: 2rem; margin-bottom: 0.75rem; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.3));'>{prop["icon"]}</div>
                            <div style='font-size: 1.5rem; color: #6366F1; font-weight: 700; margin: 0.75rem 0; font-family: "Space Grotesk", sans-serif;'>${prop["price"]:,}</div>
                            
                            <div style='background: rgba(255,255,255,0.03); padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.85rem; color: #E6EDF3; font-family: "Inter", sans-serif; border: 1px solid rgba(255,255,255,0.05);'>
                                🛏️ <b>{prop["beds"]}</b> bd | 🛁 <b>{prop["baths"]}</b> ba | 📏 <b>{prop["sqft"]:,}</b> sqft
                            </div>
                            
                            <div style='margin-top: 1.25rem;'>
                                <div style='font-size: 0.7rem; color: #8B949E; text-transform: uppercase; font-family: "Space Grotesk", sans-serif; font-weight: 700; letter-spacing: 0.1em;'>Alignment Score</div>
                                <div style='font-size: 1.75rem; font-weight: 700; color: #10b981; font-family: "Space Grotesk", sans-serif;'>{prop["match_score"]}%</div>
                            </div>
                            
                            <hr style='margin: 1.5rem 0; border-top: 1px dashed rgba(255,255,255,0.1);'>
                            
                            <div style='font-size: 0.85rem; color: #8B949E; font-family: "Inter", sans-serif;'>
                                <div style='margin-bottom: 0.5rem;'>📍 Sector: <b style="color: #FFFFFF;">{prop["neighborhood"]}</b></div>
                                <div style='margin-bottom: 0.5rem;'>💰 Fiscal: {("✅" if prop["budget_match"] else "⚠️")}</div>
                                <div>⭐ Signal: {("✅" if prop["features_match"] else "⚠️")}</div>
                            </div>
                            """,
                            config=CardConfig(variant="glass", padding="1.5rem"),
                        )
                if st.button("❌ Close Comparison", use_container_width=True):
                    st.session_state.compare_props = set()
                    st.rerun()
    for idx, property in enumerate(matches[:3]):
        with st.expander(
            f"{property['icon']} {property['address']} - {property['match_score']}% Match", expanded=idx == 0
        ):
            col_info, col_actions = st.columns([2, 1])
            with col_info:
                st.markdown(
                    f"**${property['price']:,}** | {property['beds']} bed, {property['baths']} bath | {property['sqft']:,} sqft"
                )
                st.markdown(f"**Location**: {property['neighborhood']}")
                st.markdown("#### 🎯 Why This Property?")
                for reason in property["match_reasons"]:
                    st.success(f"✅ {reason}")
                if analysis_result:
                    try:
                        from ghl_real_estate_ai.services.enhanced_lead_intelligence import (
                            get_enhanced_lead_intelligence,
                        )

                        eli = get_enhanced_lead_intelligence()

                        deep_reasoning = run_async(eli.get_psychological_property_fit(property, analysis_result))
                        st.info(f"🤖 **Claude's Psychological Insight:** {deep_reasoning}")
                    except Exception as e:
                        st.error(f"AI Insight failed: {e}")
                else:
                    try:
                        from ghl_real_estate_ai.services.property_matcher import PropertyMatcher

                        pm = PropertyMatcher()
                        deep_reasoning = pm.explain_match_with_claude(
                            property, lead_context.get("extracted_preferences", {})
                        )
                        st.info(f"🤖 **Claude's Psychological Insight:** {deep_reasoning}")
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).debug(f"AI Insight (fallback logic) failed: {str(e)}")
                        pass
                st.markdown("#### 📊 Match Score Breakdown with Gap Analysis")
                lead_budget = lead_context.get("extracted_preferences", {}).get("budget", 800000)
                property_price = property.get("price", 0)
                budget_diff = property_price - lead_budget
                budget_pct = property_price / lead_budget * 100 if lead_budget > 0 else 100
                st.markdown("**💰 Budget Analysis**")
                col_pref, col_vs, col_actual = st.columns([2, 1, 2])
                with col_pref:
                    render_obsidian_card(
                        title="",
                        content=f"""
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #6366F1; font-weight: 700; text-transform: uppercase; font-family: 'Space Grotesk', sans-serif;">NODE PREFERENCE</div>
                            <div style="font-size: 1.25rem; font-weight: 700; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;">${lead_budget:,}</div>
                        </div>
                        """,
                        config=CardConfig(variant="glass", padding="1rem"),
                    )
                with col_vs:
                    st.markdown(
                        "<div style='text-align: center; padding-top: 1rem; font-size: 1.5rem; filter: drop-shadow(0 0 10px rgba(255,255,255,0.2));'>⚖️</div>",
                        unsafe_allow_html=True,
                    )
                with col_actual:
                    render_obsidian_card(
                        title="",
                        content=f"""
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #10b981; font-weight: 700; text-transform: uppercase; font-family: 'Space Grotesk', sans-serif;">NODE LISTING</div>
                            <div style="font-size: 1.25rem; font-weight: 700; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;">${property_price:,}</div>
                        </div>
                        """,
                        config=CardConfig(variant="glass", padding="1rem"),
                    )
                if budget_diff > 0:
                    render_obsidian_card(
                        title="",
                        content=f"""<span style="color: #f59e0b; font-size: 0.85rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif;">⚠️ ${abs(budget_diff):,} ABOVE PREFERRED THRESHOLD (+{budget_pct - 100:.1f}%)</span>""",
                        config=CardConfig(variant="alert", glow_color="#f59e0b", padding="0.75rem 1rem"),
                    )
                elif budget_diff < -50000:
                    render_obsidian_card(
                        title="",
                        content=f"""<span style="color: #10b981; font-size: 0.85rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif;">✅ ${abs(budget_diff):,} BELOW THRESHOLD - OPTIMAL VALUE</span>""",
                        config=CardConfig(variant="alert", glow_color="#10b981", padding="0.75rem 1rem"),
                    )
                else:
                    render_obsidian_card(
                        title="",
                        content="""<span style="color: #6366F1; font-size: 0.85rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif;">✅ NODE ALIGNED WITHIN RANGE</span>""",
                        config=CardConfig(variant="alert", glow_color="#6366F1", padding="0.75rem 1rem"),
                    )
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**📍 SECTOR & SIGNAL ALIGNMENT**")

                # Radar Chart Implementation
                try:
                    import plotly.graph_objects as go

                    # Simulated data for the radar chart based on property scores
                    radar_labels = ["Price Match", "Location", "Features", "Schools", "Investment"]
                    # We derive these from the factors or property data
                    radar_values = [
                        property.get("match_score", 80),
                        85 if property.get("location_match") else 60,
                        90 if property.get("features_match") else 70,
                        80,  # Default for schools
                        75,  # Default for investment
                    ]

                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatterpolar(
                            r=radar_values + [radar_values[0]],
                            theta=radar_labels + [radar_labels[0]],
                            fill="toself",
                            line_color="#6366F1",
                            fillcolor="rgba(99, 102, 241, 0.3)",
                        )
                    )

                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True, range=[0, 100], showticklabels=False, gridcolor="rgba(255,255,255,0.1)"
                            ),
                            angularaxis=dict(
                                gridcolor="rgba(255,255,255,0.1)", tickfont=dict(size=10, color="#8B949E")
                            ),
                        ),
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=40, r=40, t=20, b=20),
                        height=250,
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                except Exception as e:
                    st.error(f"Radar visualization failed: {e}")

                # Keep existing factor bars as secondary detail
                factors = [
                    {"name": "Price Alignment", "score": radar_values[0], "icon": "💰", "status": True},
                    {"name": "Location Match", "score": radar_values[1], "icon": "📍", "status": True},
                    {"name": "Feature Coverage", "score": radar_values[2], "icon": "✨", "status": True},
                ]

                for factor in factors:
                    col_label, col_bar = st.columns([1, 3])
                    with col_label:
                        status_icon = "✅" if factor["status"] else "⚠️"
                        st.markdown(
                            f"<div style='font-size: 1.2rem; padding-top: 0.5rem;'>{factor['icon']} {status_icon}</div>",
                            unsafe_allow_html=True,
                        )
                    with col_bar:
                        color = (
                            "#10b981" if factor["score"] >= 85 else "#f59e0b" if factor["score"] >= 70 else "#ef4444"
                        )
                        st.markdown(
                            f"""\n                        <div style="margin-top: 0.5rem;">\n                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">\n                                <span style="font-size: 0.75rem; font-weight: 700; color: #8B949E; text-transform: uppercase; font-family: 'Space Grotesk', sans-serif;">{factor["name"]}</span>\n                                <span style="font-size: 0.75rem; font-weight: 700; color: {color}; font-family: 'Space Grotesk', sans-serif;">{factor["score"]}%</span>\n                            </div>\n                            <div style="background: rgba(255,255,255,0.05); height: 6px; border-radius: 3px; overflow: hidden;">\n                                <div style="background: {color}; width: {factor["score"]}%; height: 100%; box-shadow: 0 0 10px {color}40;"></div>\n                            </div>\n                        </div>\n                        """,
                            unsafe_allow_html=True,
                        )
            with col_actions:
                lead_id = lead_context.get("lead_id", "unknown")
                is_selected = property["address"] in st.session_state.compare_props
                if st.checkbox("Compare", key=f"compare_{lead_id}_{idx}", value=is_selected):
                    st.session_state.compare_props.add(property["address"])
                else:
                    st.session_state.compare_props.discard(property["address"])
                st.markdown("---")
                if st.button("📤 Send to Lead", key=f"send_{lead_id}_{idx}", use_container_width=True):
                    st.toast(f"Sent {property['address']} to lead!", icon="✅")
                if st.button("📅 Schedule Showing", key=f"schedule_{lead_id}_{idx}", use_container_width=True):
                    st.toast("Opening calendar...", icon="📅")
                if st.button("💾 Save for Later", key=f"save_{lead_id}_{idx}", use_container_width=True):
                    st.toast("Property saved!", icon="💾")
    st.markdown("---")
    col_batch1, col_batch2 = st.columns(2)
    with col_batch1:
        if st.button("📧 Send Top 3 Properties", use_container_width=True, type="primary"):
            st.success("Top 3 properties sent via email!")
    with col_batch2:
        if st.button("🔄 Find More Matches", use_container_width=True):
            st.info("Searching MLS database...")


@st.cache_data(ttl=300)
def generate_property_matches(lead_context: Dict, elite_mode: bool = False) -> List[Dict]:
    """
    Generate AI property matches using Strategy Pattern for flexible scoring algorithms.
    """
    try:
        from ghl_real_estate_ai.services.property_matcher import PropertyMatcher

        pm = PropertyMatcher()
        pm.set_strategy("ai" if elite_mode else "basic")
        extracted = lead_context.get("extracted_preferences", {})
        raw_matches = pm.find_matches(extracted, limit=5)
        formatted_matches = []
        for prop in raw_matches:
            formatted_matches.append(
                {
                    "id": prop.get("id", "unknown"),
                    "address": f"{prop.get('address', {}).get('street', 'Address')}, {prop.get('address', {}).get('city', 'City')}",
                    "price": prop.get("price", 750000),
                    "beds": prop.get("bedrooms", 3),
                    "baths": prop.get("bathrooms", 2.5),
                    "sqft": prop.get("sqft", 2100),
                    "neighborhood": prop.get("address", {}).get("neighborhood", "Area"),
                    "icon": _get_property_icon(prop),
                    "match_score": int(prop.get("match_score", 0) * 100),
                    "budget_match": prop.get("match_score", 0) > 0.7,
                    "location_match": True,
                    "features_match": True,
                    "match_reasons": [pm.generate_match_reasoning(prop, extracted)],
                    "match_type": prop.get("match_type", "Standard"),
                    "ai_reasoning": prop.get("ai_reasoning", ""),
                }
            )
        if formatted_matches:
            return formatted_matches
    except Exception as e:
        print(f"Error in dynamic property matching: {e}")
    return _get_fallback_properties(lead_context)


def _get_property_icon(property_data: Dict) -> str:
    """Get appropriate icon for property type"""
    property_type = property_data.get("property_type", "").lower()
    if "condo" in property_type:
        return "🏢"
    elif "townhome" in property_type:
        return "🏘️"
    elif "multi" in property_type:
        return "🏬"
    else:
        return "🏡"


def _load_demo_properties() -> List[Dict]:
    """
    Load demo property data for Strategy Pattern scoring.

    In production, this would load from MLS database, RAG system,
    or other property data sources.

    Returns:
        List of property data dictionaries for scoring
    """
    return [
        {
            "id": "prop-001",
            "address": "123 Oak Street",
            "price": 750000,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "sqft": 2100,
            "neighborhood": "Downtown",
            "property_type": "Single Family",
            "year_built": 2018,
            "recently_renovated": True,
            "amenities": ["garage", "updated_kitchen", "hardwood_floors"],
            "days_on_market": 12,
        },
        {
            "id": "prop-002",
            "address": "456 Maple Ave",
            "price": 780000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 2300,
            "neighborhood": "Domain",
            "property_type": "Single Family",
            "year_built": 2020,
            "recently_renovated": False,
            "amenities": ["pool", "garage", "outdoor_space"],
            "days_on_market": 8,
        },
        {
            "id": "prop-003",
            "address": "789 Cedar Lane",
            "price": 725000,
            "bedrooms": 4,
            "bathrooms": 2.5,
            "sqft": 2400,
            "neighborhood": "South Congress",
            "property_type": "Townhome",
            "year_built": 2019,
            "recently_renovated": False,
            "amenities": ["garage", "outdoor_space"],
            "days_on_market": 15,
        },
        {
            "id": "prop-004",
            "address": "321 Pine Boulevard",
            "price": 795000,
            "bedrooms": 3,
            "bathrooms": 3,
            "sqft": 2500,
            "neighborhood": "Westlake",
            "property_type": "Single Family",
            "year_built": 2021,
            "recently_renovated": False,
            "amenities": ["garage", "pool", "hardwood_floors", "updated_kitchen"],
            "days_on_market": 5,
        },
        {
            "id": "prop-005",
            "address": "555 Elm Drive",
            "price": 680000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 1950,
            "neighborhood": "Mueller",
            "property_type": "Single Family",
            "year_built": 2017,
            "recently_renovated": True,
            "amenities": ["garage", "outdoor_space", "updated_kitchen"],
            "days_on_market": 20,
        },
        {
            "id": "prop-006",
            "address": "888 Willow Way",
            "price": 850000,
            "bedrooms": 4,
            "bathrooms": 3.5,
            "sqft": 2800,
            "neighborhood": "Tarrytown",
            "property_type": "Single Family",
            "year_built": 2022,
            "recently_renovated": False,
            "amenities": ["garage", "pool", "hardwood_floors", "updated_kitchen", "outdoor_space"],
            "days_on_market": 3,
        },
        {
            "id": "prop-007",
            "address": "999 Highland Ave",
            "price": 720000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 2050,
            "neighborhood": "Highland",
            "property_type": "Single Family",
            "year_built": 2016,
            "recently_renovated": True,
            "amenities": ["garage", "hardwood_floors"],
            "days_on_market": 18,
        },
    ]


def _get_fallback_properties(lead_context: Dict) -> List[Dict]:
    """
    Ultimate fallback to static demo data when Strategy Pattern is unavailable.
    Persona-aware for high-impact demo scenarios.
    """
    lead_id = lead_context.get("lead_id", "unknown")
    extracted = lead_context.get("extracted_preferences", {})
    budget = extracted.get("budget", 800000)
    if lead_id == "tech_professional_sarah":
        return [
            {
                "address": "2847 Glenwood Trail",
                "price": 525000,
                "beds": 3,
                "baths": 2.5,
                "sqft": 2180,
                "neighborhood": "Teravista (Round Rock)",
                "icon": "🏡",
                "match_score": 95,
                "budget_match": True,
                "location_match": True,
                "features_match": True,
                "match_reasons": [
                    "Under SF-adjusted budget ($550k)",
                    "12-min commute to Apple campus",
                    "Gigabit fiber internet ready",
                    "Dedicated home office space",
                    "Round Rock ISD (9/10 rating)",
                ],
            },
            {
                "address": "15823 Fontana Lake Dr",
                "price": 585000,
                "beds": 4,
                "baths": 3,
                "sqft": 2650,
                "neighborhood": "Avery Ranch",
                "icon": "🏠",
                "match_score": 88,
                "budget_match": False,
                "location_match": True,
                "features_match": True,
                "match_reasons": [
                    "Premium location near Brushy Creek",
                    "Modern open floor plan",
                    "Large secondary office/flex space",
                    "Walkable to local coffee shops",
                    "High-speed networking installed",
                ],
            },
        ]
    elif lead_id == "investor_david":
        return [
            {
                "address": "14821 Willow Ridge Dr",
                "price": 285000,
                "beds": 3,
                "baths": 2,
                "sqft": 1420,
                "neighborhood": "Manor",
                "icon": "💰",
                "match_score": 98,
                "budget_match": True,
                "location_match": True,
                "features_match": True,
                "match_reasons": [
                    "Projected $270/mo positive cash flow",
                    "Turnkey condition (built 2018)",
                    "High rental demand (95% area occupancy)",
                    "Rapid appreciation forecast (12%+)",
                    "Manor tech-corridor growth zone",
                ],
            },
            {
                "address": "101 Cedar Rd",
                "price": 320000,
                "beds": 2,
                "baths": 1,
                "sqft": 1100,
                "neighborhood": "Del Valle",
                "icon": "🏬",
                "match_score": 91,
                "budget_match": True,
                "location_match": True,
                "features_match": True,
                "match_reasons": [
                    "Proximity to Tesla Giga Austin",
                    "Low maintenance exterior",
                    "Ideal entry-level rental",
                    "Strategic land-value hold",
                    "Near Austin Airport expansion",
                ],
            },
        ]
    location = extracted.get("location", "Austin")
    beds = extracted.get("bedrooms", 3)
    return [
        {
            "address": "123 Oak Street",
            "price": 750000,
            "beds": 3,
            "baths": 2.5,
            "sqft": 2100,
            "neighborhood": "Downtown",
            "icon": "🏡",
            "match_score": 92,
            "budget_match": True,
            "location_match": True,
            "features_match": True,
            "match_reasons": [
                f"Within budget (${budget:,})",
                f"Location compatibility ({location})",
                f"Exact bedroom count ({beds} beds)",
                "Newly renovated kitchen",
                "Walk to shops and restaurants",
            ],
        }
    ]
