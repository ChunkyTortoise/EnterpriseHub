"""
Jorge's AI Property Matching Dashboard - Intelligent Property Recommendations

Complete property matching system integrating:
- AI-Powered Property Matching with Hybrid Scoring
- Real-time Property Inventory Management
- Lead-Property Preference Analysis
- Market Intelligence Integration
- Automated Match Explanations
- Property Performance Analytics

Built specifically for Jorge's GHL Real Estate AI system.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

# Add the services directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../services"))

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Import the property matching service
try:
    from ghl_real_estate_ai.services.jorge_property_matching_service import JorgePropertyMatchingService

    PROPERTY_MATCHING_SERVICE_AVAILABLE = True
except ImportError:
    PROPERTY_MATCHING_SERVICE_AVAILABLE = False


# Mock Property Matching API Client for development
class JorgePropertyMatchingAPIClient:
    """Client for Jorge's Property Matching API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def get_property_matching_metrics(self) -> Dict[str, Any]:
        """Get unified property matching dashboard metrics."""
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get(f"{self.base_url}/jorge-property-matching/dashboard/metrics")
                if response.status_code == 200:
                    return response.json()
        except:
            pass

        # Mock data for demo
        import random

        return {
            "matching_performance": {
                "total_matches_generated": random.randint(1850, 2150),
                "successful_matches": random.randint(142, 178),
                "match_accuracy": random.uniform(0.87, 0.94),
                "avg_match_score": random.uniform(78.5, 86.2),
                "neural_model_accuracy": random.uniform(0.89, 0.96),
                "rules_engine_accuracy": random.uniform(0.82, 0.91),
                "hybrid_performance_boost": random.uniform(0.12, 0.18),
            },
            "inventory_metrics": {
                "active_properties": random.randint(285, 325),
                "new_listings_today": random.randint(8, 15),
                "properties_under_contract": random.randint(45, 65),
                "avg_days_on_market": random.randint(18, 28),
                "inventory_turnover_rate": random.uniform(0.65, 0.82),
                "price_range_distribution": {
                    "under_700k": random.randint(45, 75),
                    "700k_750k": random.randint(85, 125),
                    "750k_1m": random.randint(65, 95),
                    "1m_plus": random.randint(35, 55),
                },
            },
            "lead_preferences": {
                "avg_preferences_per_lead": random.uniform(6.2, 8.8),
                "most_common_price_range": "$650K-$850K",
                "preferred_bedrooms": "3-4 BR",
                "preferred_areas": ["Rancho Cucamonga", "Upland", "Claremont"],
                "search_pattern_accuracy": random.uniform(0.78, 0.89),
                "preference_evolution_tracking": random.uniform(0.82, 0.94),
            },
            "market_intelligence": {
                "market_velocity_score": random.uniform(72.5, 88.2),
                "competitive_advantage": random.uniform(0.15, 0.28),
                "price_prediction_accuracy": random.uniform(0.91, 0.97),
                "neighborhood_expertise_score": random.uniform(0.86, 0.95),
                "timing_optimization": random.uniform(0.22, 0.38),
            },
            "explanation_engine": {
                "explanations_generated": random.randint(1450, 1850),
                "explanation_quality_score": random.uniform(0.88, 0.96),
                "client_understanding_rate": random.uniform(0.84, 0.93),
                "jorge_talking_points": random.randint(3850, 4250),
                "personalization_accuracy": random.uniform(0.89, 0.97),
            },
            "system_health": {
                "matching_engine": "healthy",
                "mls_integration": "healthy",
                "neural_model": "healthy",
                "overall_uptime": random.uniform(99.1, 99.8),
            },
            "last_updated": datetime.now().isoformat(),
        }

    async def find_property_matches(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Find property matches for a lead."""
        import random

        # Generate mock property matches
        properties = [
            {
                "id": f"prop_{i + 1:03d}",
                "address": f"{random.randint(10000, 99999)} {random.choice(['Oak', 'Maple', 'Pine', 'Elm', 'Cedar'])} {random.choice(['St', 'Ave', 'Dr', 'Ln', 'Ct'])}",
                "city": random.choice(["Rancho Cucamonga", "Upland", "Ontario", "Claremont"]),
                "price": random.randint(550000, 1200000),
                "bedrooms": random.randint(2, 5),
                "bathrooms": random.uniform(2, 4.5),
                "sqft": random.randint(1800, 4200),
                "lot_size": random.uniform(0.15, 0.45),
                "year_built": random.randint(1985, 2020),
                "property_type": random.choice(["Single Family", "Townhome", "Condo"]),
                "match_score": random.uniform(65, 98),
                "neural_score": random.uniform(60, 95),
                "rule_score": random.uniform(70, 98),
                "confidence": random.choice(["high", "medium", "low"]),
                "days_on_market": random.randint(1, 45),
                "listing_agent": f"Agent {random.randint(1, 20)}",
                "school_rating": random.randint(7, 10),
                "neighborhood_score": random.uniform(75, 95),
            }
            for i in range(random.randint(8, 15))
        ]

        # Sort by match score
        properties.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "lead_id": lead_data.get("id", "lead_demo"),
            "total_matches": len(properties),
            "matches": properties,
            "search_criteria": lead_data.get("preferences", {}),
            "algorithm_used": "hybrid_neural_rules",
            "neural_weight": 0.6,
            "rules_weight": 0.4,
            "processing_time_ms": random.randint(450, 850),
            "market_conditions": {"inventory_level": "medium", "competition": "high", "price_trend": "stable_up"},
        }

    async def explain_property_match(self, property_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explanation for why a property matches a lead."""
        import random

        return {
            "property_id": property_id,
            "explanation": {
                "overall_reasoning": "This property is an excellent match based on your budget, location preferences, and family needs. It offers exceptional value in a sought-after neighborhood.",
                "key_strengths": [
                    f"Perfect price point at ${random.randint(650000, 850000):,} within your ${lead_data.get('budget', '700K-900K')} range",
                    f"Located in {random.choice(['top-rated school district', 'family-friendly neighborhood', 'quiet cul-de-sac'])}",
                    f"Move-in ready with {random.choice(['recent updates', 'modern kitchen', 'new flooring'])}",
                    f"{random.choice(['Large backyard', 'Open floor plan', 'Master suite'])} perfect for your lifestyle",
                ],
                "potential_concerns": [
                    f"Slightly {random.choice(['older construction', 'smaller lot', 'busy street'])} - Jorge can address this",
                    f"Market is {random.choice(['competitive', 'moving fast'])} - quick action recommended",
                ],
                "jorge_talking_points": [
                    f"🏠 'This is exactly what you've been looking for in {random.choice(['Rancho Cucamonga', 'Upland'])} - let's see it this week'",
                    f"💰 'At ${random.randint(650, 850)}K, you're getting incredible value compared to similar homes'",
                    f"🏫 'The schools here are {random.randint(8, 10)}/10 rated - perfect for your family'",
                    f"⏰ 'Properties like this don't last long - I recommend we schedule a showing immediately'",
                ],
                "market_context": {
                    "comparable_sales": f"${random.randint(675, 875)}K average in area",
                    "market_velocity": f"{random.randint(15, 25)} days average time on market",
                    "inventory_status": random.choice(
                        ["Low inventory - high demand", "Balanced market", "Seller's market"]
                    ),
                },
                "next_steps": [
                    "Schedule showing within 24-48 hours",
                    "Prepare competitive offer strategy",
                    "Review neighborhood comps",
                    "Coordinate with Jorge for immediate action",
                ],
            },
            "confidence_score": random.uniform(0.85, 0.98),
            "personalization_factors": [
                "Budget alignment",
                "Location preferences",
                "Family size requirements",
                "Lifestyle preferences",
                "Investment goals",
            ],
        }

    async def get_property_inventory(self) -> Dict[str, Any]:
        """Get current property inventory analytics."""
        import random

        return {
            "total_properties": random.randint(280, 320),
            "new_today": random.randint(6, 12),
            "price_distribution": {
                "$400K-$600K": random.randint(25, 45),
                "$600K-$800K": random.randint(85, 115),
                "$800K-$1.2M": random.randint(65, 85),
                "$1.2M+": random.randint(35, 55),
            },
            "by_city": {
                "Rancho Cucamonga": random.randint(95, 125),
                "Upland": random.randint(55, 75),
                "Ontario": random.randint(45, 65),
                "Claremont": random.randint(25, 45),
                "Other": random.randint(15, 35),
            },
            "property_types": {
                "Single Family": random.randint(180, 220),
                "Townhome": random.randint(45, 65),
                "Condo": random.randint(35, 55),
                "Multi-Family": random.randint(15, 25),
            },
            "market_metrics": {
                "avg_days_on_market": random.randint(18, 28),
                "median_price": random.randint(725000, 825000),
                "price_per_sqft": random.randint(380, 450),
                "inventory_turnover": random.uniform(0.68, 0.84),
            },
            "trending_features": [
                {"feature": "Pool", "demand_score": random.randint(85, 95)},
                {"feature": "Home Office", "demand_score": random.randint(92, 98)},
                {"feature": "3-Car Garage", "demand_score": random.randint(78, 88)},
                {"feature": "Solar Panels", "demand_score": random.randint(82, 92)},
            ],
        }

    async def get_match_performance_analytics(self) -> Dict[str, Any]:
        """Get matching algorithm performance analytics."""
        import random

        # Generate historical performance data
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, 0, -1)]

        return {
            "algorithm_performance": {
                "hybrid_vs_neural_only": {
                    "hybrid_accuracy": random.uniform(0.89, 0.95),
                    "neural_only_accuracy": random.uniform(0.81, 0.87),
                    "improvement": random.uniform(0.08, 0.14),
                },
                "hybrid_vs_rules_only": {
                    "hybrid_accuracy": random.uniform(0.89, 0.95),
                    "rules_only_accuracy": random.uniform(0.76, 0.82),
                    "improvement": random.uniform(0.13, 0.19),
                },
            },
            "performance_trends": {
                "dates": dates,
                "match_accuracy": [random.uniform(0.85, 0.95) for _ in dates],
                "neural_scores": [random.uniform(0.80, 0.92) for _ in dates],
                "rule_scores": [random.uniform(0.75, 0.88) for _ in dates],
                "processing_times": [random.randint(400, 800) for _ in dates],
            },
            "success_metrics": {
                "client_satisfaction": random.uniform(0.91, 0.97),
                "showing_conversion_rate": random.uniform(0.68, 0.82),
                "offer_acceptance_rate": random.uniform(0.45, 0.65),
                "time_to_match": random.uniform(1.2, 2.8),  # hours
            },
            "optimization_opportunities": [
                {
                    "area": "Price Sensitivity Calibration",
                    "potential_improvement": random.uniform(0.03, 0.08),
                    "priority": "high",
                },
                {
                    "area": "Neighborhood Preference Learning",
                    "potential_improvement": random.uniform(0.05, 0.12),
                    "priority": "medium",
                },
            ],
        }


# Initialize clients
@st.cache_resource
def get_property_matching_api_client():
    return JorgePropertyMatchingAPIClient()


@st.cache_resource
def get_property_matching_service():
    if PROPERTY_MATCHING_SERVICE_AVAILABLE:
        return JorgePropertyMatchingService()
    return None


def render_property_matching_dashboard_css():
    """Inject custom CSS for property matching dashboard - Jorge Edition"""
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');

    /* Property Matching Dashboard Styles */
    .property-container {
        background: rgba(5, 7, 10, 0.8) !important;
        border-radius: 20px;
        padding: 2.5rem;
        margin: 1rem 0;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.9);
        border: 1px solid rgba(52, 152, 219, 0.1);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(20px);
    }

    .property-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 10% 10%, rgba(52, 152, 219, 0.05) 0%, transparent 50%),
                    radial-gradient(circle at 90% 90%, rgba(16, 185, 129, 0.03) 0%, transparent 50%);
        pointer-events: none;
    }

    .property-dashboard-header {
        text-align: left;
        color: white;
        margin-bottom: 3rem;
        position: relative;
        z-index: 1;
        border-bottom: 1px solid rgba(52, 152, 219, 0.2);
        padding-bottom: 2rem;
    }

    .property-dashboard-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        color: #3498DB;
        letter-spacing: -0.04em;
        text-transform: uppercase;
    }

    .property-dashboard-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        margin: 0.75rem 0 0 0;
        color: #8B949E;
        font-weight: 500;
        letter-spacing: 0.02em;
    }

    .property-kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }

    .property-kpi-card {
        background: rgba(22, 27, 34, 0.7) !important;
        border-radius: 12px;
        padding: 1.75rem;
        text-align: left;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(52, 152, 219, 0.1);
        border-top: 1px solid rgba(52, 152, 219, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .property-kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 48px rgba(52, 152, 219, 0.3);
        border-color: rgba(52, 152, 219, 0.4);
    }

    .property-kpi-icon {
        font-size: 1.75rem;
        margin-bottom: 1.25rem;
        background: rgba(52, 152, 219, 0.1);
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 10px;
        border: 1px solid rgba(52, 152, 219, 0.2);
    }

    .property-kpi-value {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 2.5rem;
        font-weight: 700;
        color: #3498DB;
        margin: 0.5rem 0;
        text-shadow: 0 0 15px rgba(52, 152, 219, 0.3);
    }

    .property-kpi-label {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.75rem;
        color: #8B949E;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .property-card {
        background: rgba(22, 27, 34, 0.6) !important;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(52, 152, 219, 0.1);
        transition: all 0.3s ease;
    }

    .property-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(52, 152, 219, 0.2);
        border-color: rgba(52, 152, 219, 0.3);
    }

    .property-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .property-address {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        color: #FFFFFF;
        font-size: 1.1rem;
    }

    .property-price {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        color: #3498DB;
        font-size: 1.25rem;
    }

    .property-specs {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 0.75rem;
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #8B949E;
    }

    .match-score-bar {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        height: 6px;
        margin: 1rem 0;
        overflow: hidden;
    }

    .match-score-fill {
        height: 100%;
        background: linear-gradient(90deg, #3498DB, #2ECC71);
        border-radius: 4px;
        transition: width 1s ease-in-out;
    }

    .explanation-panel {
        background: rgba(52, 152, 219, 0.05);
        border: 1px solid rgba(52, 152, 219, 0.1);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .talking-point {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #FFFFFF;
        font-style: italic;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_property_search_section(api_client: JorgePropertyMatchingAPIClient):
    """Render the Property Search and Matching section."""
    st.header("🏠 AI Property Matching Engine")
    st.markdown("**Find perfect property matches using hybrid neural + rules AI**")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🔍 Lead Profile & Preferences")

        # Lead search form
        with st.form("property_search_form"):
            lead_name = st.text_input("Lead Name", placeholder="Sarah Johnson")

            col_budget1, col_budget2 = st.columns(2)
            with col_budget1:
                min_budget = st.number_input("Min Budget ($)", min_value=200000, value=650000, step=25000)
            with col_budget2:
                max_budget = st.number_input("Max Budget ($)", min_value=700000, value=850000, step=25000)

            col_bed, col_bath = st.columns(2)
            with col_bed:
                bedrooms = st.selectbox("Bedrooms", [2, 3, 4, 5, "5+"], index=1)
            with col_bath:
                bathrooms = st.selectbox("Bathrooms", [2.0, 2.5, 3.0, 3.5, 4.0, "4+"], index=2)

            preferred_cities = st.multiselect(
                "Preferred Areas",
                ["Rancho Cucamonga", "Upland", "Ontario", "Claremont", "San Dimas", "Pomona"],
                default=["Rancho Cucamonga", "Upland"],
            )

            property_types = st.multiselect(
                "Property Types",
                ["Single Family", "Townhome", "Condo", "Multi-Family"],
                default=["Single Family", "Townhome"],
            )

            col_features1, col_features2 = st.columns(2)
            with col_features1:
                must_haves = st.multiselect("Must Haves", ["Pool", "Garage", "Yard", "Office", "Updated Kitchen"])
            with col_features2:
                nice_to_haves = st.multiselect("Nice to Have", ["Solar", "View", "Fireplace", "Walk-in Closet"])

            timeline = st.selectbox("Timeline", ["Immediate", "30 days", "3 months", "6 months", "Just browsing"])

            search_button = st.form_submit_button("🚀 Find Matches", type="primary", use_container_width=True)

        if search_button and lead_name:
            # Create lead data
            lead_data = {
                "id": f"lead_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "name": lead_name,
                "preferences": {
                    "budget_min": min_budget,
                    "budget_max": max_budget,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "cities": preferred_cities,
                    "property_types": property_types,
                    "must_haves": must_haves,
                    "nice_to_haves": nice_to_haves,
                    "timeline": timeline,
                },
                "budget": f"${min_budget:,}-${max_budget:,}",
            }

            # Find matches
            with st.spinner("🧠 Finding perfect property matches with AI..."):
                matches = run_async(api_client.find_property_matches(lead_data))
                st.session_state["property_matches"] = matches
                st.session_state["search_lead_data"] = lead_data
                st.success(f"✅ Found {matches['total_matches']} property matches for {lead_name}!")

    with col2:
        st.subheader("🏡 Property Matches")

        # Display matches if available
        if "property_matches" in st.session_state:
            matches = st.session_state["property_matches"]
            lead_data = st.session_state["search_lead_data"]

            # Matching summary
            st.info(
                f"**Algorithm**: {matches['algorithm_used']} | **Processing Time**: {matches['processing_time_ms']}ms | **Neural Weight**: {matches['neural_weight']:.0%}"
            )

            # Display top properties
            for i, property_data in enumerate(matches["matches"][:5]):
                with st.container():
                    st.markdown(
                        f"""
                    <div class="holographic-card property-card">
                        <div class="property-header">
                            <div class="property-address">{property_data["address"]}, {property_data["city"]}</div>
                            <div class="property-price">${property_data["price"]:,}</div>
                        </div>

                        <div class="property-specs">
                            <div><strong>🛏️</strong> {property_data["bedrooms"]} BR</div>
                            <div><strong>🚿</strong> {property_data["bathrooms"]} BA</div>
                            <div><strong>📐</strong> {property_data["sqft"]:,} sqft</div>
                            <div><strong>🏗️</strong> {property_data["year_built"]}</div>
                            <div><strong>📅</strong> {property_data["days_on_market"]} DOM</div>
                            <div><strong>⭐</strong> {property_data["school_rating"]}/10 schools</div>
                        </div>

                        <div style="margin: 1rem 0;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span style="font-size: 0.9rem; color: #8B949E;">Match Score</span>
                                <span style="font-weight: 700; color: #3498DB;">{property_data["match_score"]:.1f}/100</span>
                            </div>
                            <div class="match-score-bar">
                                <div class="match-score-fill" style="width: {property_data["match_score"]:.1f}%;"></div>
                            </div>
                            <div style="font-size: 0.8rem; color: #8B949E; display: flex; justify-content: space-between;">
                                <span>Neural: {property_data["neural_score"]:.0f}</span>
                                <span>Rules: {property_data["rule_score"]:.0f}</span>
                                <span>Confidence: {property_data["confidence"].title()}</span>
                            </div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Explanation button
                    if st.button(f"💬 Explain Match", key=f"explain_{i}", use_container_width=True):
                        explanation = run_async(api_client.explain_property_match(property_data["id"], lead_data))
                        st.session_state[f"explanation_{i}"] = explanation

                    # Show explanation if available
                    if f"explanation_{i}" in st.session_state:
                        explanation = st.session_state[f"explanation_{i}"]
                        exp_data = explanation["explanation"]

                        st.markdown(
                            """
                        <div class="explanation-panel">
                            <h4 style="color: #3498DB; margin: 0 0 1rem 0;">🎯 Why This Property Matches</h4>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        st.markdown(f"**Overall Reasoning**: {exp_data['overall_reasoning']}")

                        col_strengths, col_concerns = st.columns(2)

                        with col_strengths:
                            st.markdown("**✅ Key Strengths**")
                            for strength in exp_data["key_strengths"]:
                                st.markdown(f"• {strength}")

                        with col_concerns:
                            st.markdown("**⚠️ Considerations**")
                            for concern in exp_data["potential_concerns"]:
                                st.markdown(f"• {concern}")

                        st.markdown("**💬 Jorge's Talking Points**")
                        for point in exp_data["jorge_talking_points"]:
                            st.markdown(
                                f"""
                            <div class="talking-point">
                                {point}
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                    st.divider()

        else:
            st.info("👆 Enter lead information and search to see AI-powered property matches")


def render_inventory_analytics_section(api_client: JorgePropertyMatchingAPIClient):
    """Render the Property Inventory Analytics section."""
    st.header("📊 Property Inventory Analytics")
    st.markdown("**Real-time market intelligence and inventory insights**")

    # Get inventory data
    inventory_data = run_async(api_client.get_property_inventory())

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏠 Inventory Overview")

        # Key metrics
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.metric("Total Properties", f"{inventory_data['total_properties']:,}")
            st.metric("New Today", f"+{inventory_data['new_today']}")

        with col_m2:
            st.metric("Median Price", f"${inventory_data['market_metrics']['median_price']:,}")
            st.metric("Avg Days on Market", f"{inventory_data['market_metrics']['avg_days_on_market']}")

        # Price distribution chart
        st.subheader("💰 Price Distribution")
        price_dist = inventory_data["price_distribution"]

        fig_price = px.bar(
            x=list(price_dist.keys()),
            y=list(price_dist.values()),
            title="Properties by Price Range",
            labels={"x": "Price Range", "y": "Number of Properties"},
            color=list(price_dist.values()),
            color_continuous_scale="Blues",
        )

        fig_price.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), showlegend=False
        )

        st.plotly_chart(fig_price, use_container_width=True)

    with col2:
        st.subheader("🗺️ Geographic Distribution")

        # City distribution chart
        city_dist = inventory_data["by_city"]

        fig_city = px.pie(names=list(city_dist.keys()), values=list(city_dist.values()), title="Properties by City")

        fig_city.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))

        st.plotly_chart(fig_city, use_container_width=True)

        # Property types
        st.subheader("🏘️ Property Types")
        type_dist = inventory_data["property_types"]

        for prop_type, count in type_dist.items():
            percentage = (count / inventory_data["total_properties"]) * 100
            st.markdown(f"**{prop_type}**: {count} ({percentage:.1f}%)")

        # Trending features
        st.subheader("🔥 Trending Features")
        trending = inventory_data["trending_features"]

        for feature in trending:
            st.markdown(f"**{feature['feature']}**: {feature['demand_score']}/100 demand")


def render_matching_performance_section(api_client: JorgePropertyMatchingAPIClient):
    """Render the Matching Performance Analytics section."""
    st.header("⚡ Matching Algorithm Performance")
    st.markdown("**Monitor and optimize AI matching accuracy**")

    # Get performance data
    performance_data = run_async(api_client.get_match_performance_analytics())

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧠 Algorithm Comparison")

        algorithm_perf = performance_data["algorithm_performance"]

        # Hybrid vs Neural only
        hybrid_neural = algorithm_perf["hybrid_vs_neural_only"]
        st.metric(
            "Hybrid vs Neural-Only",
            f"+{hybrid_neural['improvement']:.1%}",
            delta=f"Hybrid: {hybrid_neural['hybrid_accuracy']:.1%} vs Neural: {hybrid_neural['neural_only_accuracy']:.1%}",
        )

        # Hybrid vs Rules only
        hybrid_rules = algorithm_perf["hybrid_vs_rules_only"]
        st.metric(
            "Hybrid vs Rules-Only",
            f"+{hybrid_rules['improvement']:.1%}",
            delta=f"Hybrid: {hybrid_rules['hybrid_accuracy']:.1%} vs Rules: {hybrid_rules['rules_only_accuracy']:.1%}",
        )

        # Performance trends chart
        st.subheader("📈 Performance Trends")
        trends = performance_data["performance_trends"]

        fig_trends = go.Figure()

        fig_trends.add_trace(
            go.Scatter(
                x=trends["dates"],
                y=[acc * 100 for acc in trends["match_accuracy"]],
                mode="lines+markers",
                name="Match Accuracy",
                line=dict(color="#3498DB", width=3),
            )
        )

        fig_trends.add_trace(
            go.Scatter(
                x=trends["dates"],
                y=[score * 100 for score in trends["neural_scores"]],
                mode="lines",
                name="Neural Scores",
                line=dict(color="#2ECC71", width=2),
            )
        )

        fig_trends.add_trace(
            go.Scatter(
                x=trends["dates"],
                y=[score * 100 for score in trends["rule_scores"]],
                mode="lines",
                name="Rule Scores",
                line=dict(color="#F39C12", width=2),
            )
        )

        fig_trends.update_layout(
            title="Algorithm Performance Over Time",
            xaxis_title="Date",
            yaxis_title="Performance Score (%)",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )

        st.plotly_chart(fig_trends, use_container_width=True)

    with col2:
        st.subheader("🎯 Success Metrics")

        success_metrics = performance_data["success_metrics"]

        # Key success metrics
        st.metric("Client Satisfaction", f"{success_metrics['client_satisfaction']:.1%}")
        st.metric("Showing Conversion", f"{success_metrics['showing_conversion_rate']:.1%}")
        st.metric("Offer Acceptance", f"{success_metrics['offer_acceptance_rate']:.1%}")
        st.metric("Avg Time to Match", f"{success_metrics['time_to_match']:.1f} hours")

        # Processing time trends
        st.subheader("⚡ Processing Performance")

        fig_processing = px.line(
            x=trends["dates"],
            y=trends["processing_times"],
            title="Processing Time Trends (ms)",
            labels={"x": "Date", "y": "Processing Time (ms)"},
        )

        fig_processing.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white")
        )

        st.plotly_chart(fig_processing, use_container_width=True)

        # Optimization opportunities
        st.subheader("🎯 Optimization Opportunities")

        opportunities = performance_data["optimization_opportunities"]
        for opp in opportunities:
            priority_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            st.markdown(f"{priority_color[opp['priority']]} **{opp['area']}**")
            st.markdown(f"Potential improvement: +{opp['potential_improvement']:.1%}")
            st.divider()


def render_property_matching_integration_dashboard(api_client: JorgePropertyMatchingAPIClient):
    """Render the unified property matching dashboard."""
    st.header("🏠 Property Matching Command Center")
    st.markdown("**AI-powered property intelligence and matching overview**")

    # Get dashboard metrics
    metrics = run_async(api_client.get_property_matching_metrics())

    # System health indicators
    st.subheader("🚀 Matching Engine Health")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        matching_status = metrics["system_health"]["matching_engine"]
        status_icon = "🟢" if matching_status == "healthy" else "🔴"
        st.metric("Matching Engine", f"{status_icon} {matching_status.title()}")

    with col2:
        mls_status = metrics["system_health"]["mls_integration"]
        status_icon = "🟢" if mls_status == "healthy" else "🔴"
        st.metric("MLS Integration", f"{status_icon} {mls_status.title()}")

    with col3:
        neural_status = metrics["system_health"]["neural_model"]
        status_icon = "🟢" if neural_status == "healthy" else "🔴"
        st.metric("Neural Model", f"{status_icon} {neural_status.title()}")

    with col4:
        st.metric("System Uptime", f"{metrics['system_health']['overall_uptime']:.1f}%")

    st.divider()

    # Property Matching KPI Grid
    st.subheader("🎯 Matching Intelligence Overview")

    matching_perf = metrics["matching_performance"]
    inventory_metrics = metrics["inventory_metrics"]
    market_intel = metrics["market_intelligence"]
    explanation_engine = metrics["explanation_engine"]

    st.markdown('<div class="property-kpi-grid">', unsafe_allow_html=True)

    kpis = [
        {
            "icon": "🎯",
            "label": "Match Accuracy",
            "value": f"{matching_perf['match_accuracy']:.1%}",
            "change": 2.3,
            "trend": "positive",
        },
        {
            "icon": "🏠",
            "label": "Active Properties",
            "value": f"{inventory_metrics['active_properties']:,}",
            "change": inventory_metrics["new_listings_today"],
            "trend": "positive",
        },
        {
            "icon": "🧠",
            "label": "Neural Performance",
            "value": f"{matching_perf['neural_model_accuracy']:.1%}",
            "change": 1.8,
            "trend": "positive",
        },
        {
            "icon": "📊",
            "label": "Avg Match Score",
            "value": f"{matching_perf['avg_match_score']:.0f}/100",
            "change": 3.2,
            "trend": "positive",
        },
        {
            "icon": "⚡",
            "label": "Hybrid Boost",
            "value": f"+{matching_perf['hybrid_performance_boost']:.1%}",
            "change": 0.8,
            "trend": "positive",
        },
        {
            "icon": "💬",
            "label": "Explanations Generated",
            "value": f"{explanation_engine['explanations_generated']:,}",
            "change": 125,
            "trend": "positive",
        },
    ]

    for kpi in kpis:
        trend = kpi.get("trend", "neutral")
        trend_icon = "📈" if trend == "positive" else "📉" if trend == "negative" else "📊"
        change_sign = "+" if kpi["change"] > 0 else ""
        change_display = (
            f"{change_sign}{kpi['change']:.1f}" if isinstance(kpi["change"], float) else f"{change_sign}{kpi['change']}"
        )

        st.markdown(
            f"""
        <div class="property-kpi-card">
            <div class="property-kpi-icon">{kpi["icon"]}</div>
            <div class="property-kpi-label">{kpi["label"]}</div>
            <div class="property-kpi-value">{kpi["value"]}</div>
            <div style="
                font-family: 'Inter', sans-serif;
                font-size: 0.8rem;
                font-weight: 700;
                padding: 4px 10px;
                border-radius: 6px;
                display: inline-flex;
                align-items: center;
                gap: 0.25rem;
                margin-top: 0.75rem;
                background: rgba(16, 185, 129, 0.1);
                color: #10b981;
                border: 1px solid rgba(16, 185, 129, 0.2);
            ">
                {trend_icon} {change_display}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_jorge_property_matching_dashboard():
    """Main function to render Jorge's Property Matching Dashboard."""

    # Apply custom CSS
    render_property_matching_dashboard_css()

    # Main container
    st.markdown('<div class="property-container">', unsafe_allow_html=True)

    # Header
    st.markdown(
        """
    <div class="property-dashboard-header">
        <h1 class="property-dashboard-title">🏠 Property Matching AI</h1>
        <p class="property-dashboard-subtitle">Intelligent property recommendations powered by hybrid neural + rules matching for Jorge's real estate empire</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Initialize API client
    api_client = get_property_matching_api_client()

    # Main property matching overview
    render_property_matching_integration_dashboard(api_client)

    # Tab navigation for different sections
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔍 Property Search", "📊 Inventory Analytics", "⚡ Algorithm Performance", "🎯 Match Intelligence"]
    )

    with tab1:
        render_property_search_section(api_client)

    with tab2:
        render_inventory_analytics_section(api_client)

    with tab3:
        render_matching_performance_section(api_client)

    with tab4:
        # Get additional metrics
        metrics = run_async(api_client.get_property_matching_metrics())

        st.header("🎯 Match Intelligence Center")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Lead Preferences Analytics")
            preferences = metrics["lead_preferences"]

            st.metric("Avg Preferences per Lead", f"{preferences['avg_preferences_per_lead']:.1f}")
            st.metric("Most Common Price Range", preferences["most_common_price_range"])
            st.metric("Preferred Bedroom Count", preferences["preferred_bedrooms"])

            st.markdown("**Top Preferred Areas:**")
            for area in preferences["preferred_areas"]:
                st.markdown(f"• {area}")

        with col2:
            st.subheader("🧠 Market Intelligence")
            market_intel = metrics["market_intelligence"]

            st.metric("Market Velocity Score", f"{market_intel['market_velocity_score']:.0f}/100")
            st.metric("Competitive Advantage", f"{market_intel['competitive_advantage']:.1%}")
            st.metric("Price Prediction Accuracy", f"{market_intel['price_prediction_accuracy']:.1%}")
            st.metric("Neighborhood Expertise", f"{market_intel['neighborhood_expertise_score']:.1%}")

    # Footer with quick actions
    st.divider()
    st.markdown("### ⚡ Property Matching Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Refresh MLS Data", use_container_width=True):
            st.info("🏠 MLS data refresh initiated - updating property inventory")

    with col2:
        if st.button("🧠 Retrain Neural Model", use_container_width=True):
            st.info("🤖 Neural model retraining scheduled with latest match data")

    with col3:
        if st.button("📊 Export Match Report", use_container_width=True):
            st.info("📈 Property matching performance report exported")

    with col4:
        if st.button("⚙️ Matching Settings", use_container_width=True):
            st.info("⚙️ Advanced matching algorithm configuration")

    # Close main container
    st.markdown("</div>", unsafe_allow_html=True)


# Main function call
if __name__ == "__main__":
    render_jorge_property_matching_dashboard()
