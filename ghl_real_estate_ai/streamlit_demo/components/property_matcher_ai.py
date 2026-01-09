"""
Property Matcher AI Component
AI-powered property matching with reasoning and scoring breakdown
"""

import streamlit as st
from typing import Dict, List


def render_property_matcher(lead_context: Dict):
    """
    AI-powered property matching with reasoning
    
    Args:
        lead_context: Dictionary containing lead preferences and information
    """
    
    st.markdown("### 🏠 AI Property Matcher")
    st.markdown("*Showing properties matched to lead criteria*")

    # Get matched properties (mock for demo)
    matches = generate_property_matches(lead_context)

    # PREMIUM FEATURE: Use premium property cards grid layout
    try:
        from components.property_cards import render_premium_property_grid
        st.markdown("#### 🏡 Top Property Matches")
        render_premium_property_grid(matches[:3])

        st.markdown("---")
        st.markdown("#### 📊 Detailed Analysis")

    except ImportError:
        st.info("🚀 Premium property cards available in enterprise version")

    # Display detailed analysis in expandable format for additional properties
    for idx, property in enumerate(matches[:3]):
        with st.expander(
            f"{property['icon']} {property['address']} - {property['match_score']}% Match", 
            expanded=(idx == 0)
        ):
            
            col_info, col_actions = st.columns([2, 1])
            
            with col_info:
                st.markdown(f"**${property['price']:,}** | {property['beds']} bed, {property['baths']} bath | {property['sqft']:,} sqft")
                st.markdown(f"**Location**: {property['neighborhood']}")
                
                # Match reasoning
                st.markdown("#### 🎯 Why This Property?")
                for reason in property['match_reasons']:
                    st.success(f"✅ {reason}")
                
                # Score breakdown with Gap Analysis
                st.markdown("#### 📊 Match Score Breakdown with Gap Analysis")
                
                # Get lead preferences and property details
                lead_budget = lead_context.get('extracted_preferences', {}).get('budget', 800000)
                property_price = property.get('price', 0)
                
                # Calculate budget gap
                budget_diff = property_price - lead_budget
                budget_pct = (property_price / lead_budget * 100) if lead_budget > 0 else 100
                
                # Budget comparison scale
                st.markdown("**💰 Budget Analysis**")
                col_pref, col_vs, col_actual = st.columns([2, 1, 2])
                
                with col_pref:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.5rem; background: #f0f9ff; border-radius: 6px;">
                        <div style="font-size: 0.7rem; color: #0369a1; font-weight: 600;">LEAD'S PREFERENCE</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #0c4a6e;">${lead_budget:,}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_vs:
                    st.markdown("<div style='text-align: center; padding-top: 0.75rem; font-size: 1.2rem;'>⚖️</div>", unsafe_allow_html=True)
                
                with col_actual:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.5rem; background: #f0fdf4; border-radius: 6px;">
                        <div style="font-size: 0.7rem; color: #065f46; font-weight: 600;">PROPERTY PRICE</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #064e3b;">${property_price:,}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Gap indicator with color coding
                if budget_diff > 0:
                    st.markdown(f"""
                    <div style="background: #fef3c7; border-left: 3px solid #f59e0b; padding: 0.5rem 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
                        <span style="color: #92400e; font-size: 0.8rem; font-weight: 600;">⚠️ ${abs(budget_diff):,} over preferred budget (+{budget_pct - 100:.1f}%)</span>
                    </div>
                    """, unsafe_allow_html=True)
                elif budget_diff < -50000:
                    st.markdown(f"""
                    <div style="background: #dcfce7; border-left: 3px solid #10b981; padding: 0.5rem 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
                        <span style="color: #065f46; font-size: 0.8rem; font-weight: 600;">✅ ${abs(budget_diff):,} under budget - Excellent value!</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: #dbeafe; border-left: 3px solid #3b82f6; padding: 0.5rem 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
                        <span style="color: #1e40af; font-size: 0.8rem; font-weight: 600;">✅ Perfectly within range</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Location & Features comparison scales
                st.markdown("**📍 Location & Features**")
                
                # Progress bars with gap analysis
                factors = [
                    {
                        "name": "Location Match",
                        "icon": "📍",
                        "score": 90 if property['location_match'] else 60,
                        "status": property['location_match']
                    },
                    {
                        "name": "Feature Match", 
                        "icon": "⭐",
                        "score": 95 if property['features_match'] else 70,
                        "status": property['features_match']
                    }
                ]
                
                for factor in factors:
                    col_label, col_bar = st.columns([1, 3])
                    with col_label:
                        status_icon = "✅" if factor['status'] else "⚠️"
                        st.markdown(f"{factor['icon']} {status_icon}")
                    with col_bar:
                        color = "#10b981" if factor['score'] >= 85 else "#f59e0b" if factor['score'] >= 70 else "#ef4444"
                        st.markdown(f"""
                        <div style="margin-top: 0.5rem;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                                <span style="font-size: 0.75rem; font-weight: 600; color: #1e293b;">{factor['name']}</span>
                                <span style="font-size: 0.75rem; font-weight: 700; color: {color};">{factor['score']}%</span>
                            </div>
                            <div style="background: #f1f5f9; height: 6px; border-radius: 3px; overflow: hidden;">
                                <div style="background: {color}; width: {factor['score']}%; height: 100%; transition: width 0.3s ease;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            with col_actions:
                if st.button("📤 Send to Lead", key=f"send_{idx}", use_container_width=True):
                    st.toast(f"Sent {property['address']} to lead!", icon="✅")
                
                if st.button("📅 Schedule Showing", key=f"schedule_{idx}", use_container_width=True):
                    st.toast("Opening calendar...", icon="📅")
                
                if st.button("💾 Save for Later", key=f"save_{idx}", use_container_width=True):
                    st.toast("Property saved!", icon="💾")
    
    # Batch actions
    st.markdown("---")
    col_batch1, col_batch2 = st.columns(2)
    
    with col_batch1:
        if st.button("📧 Send Top 3 Properties", use_container_width=True, type="primary"):
            st.success("Top 3 properties sent via email!")
    
    with col_batch2:
        if st.button("🔄 Find More Matches", use_container_width=True):
            st.info("Searching MLS database...")


def generate_property_matches(lead_context: Dict) -> List[Dict]:
    """
    Generate AI property matches based on lead context using ML-enhanced matching

    Uses ML-powered confidence scoring for sophisticated property matching:
    1. Query MLS database
    2. Apply ML-based confidence scoring
    3. Generate detailed reasoning
    4. Rank by composite confidence scores

    Args:
        lead_context: Dictionary containing lead preferences

    Returns:
        List of property dictionaries with ML confidence scores and reasoning
    """

    # Import the ML-enhanced matcher
    try:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from services.property_matcher_ml import PropertyMatcherML

        # Initialize ML matcher
        ml_matcher = PropertyMatcherML()

        # Extract lead preferences from context
        extracted = lead_context.get('extracted_preferences', {})

        # Enhanced preferences for ML matching
        ml_preferences = {
            'budget': extracted.get('budget', 800000),
            'location': extracted.get('location', 'Downtown'),
            'bedrooms': extracted.get('bedrooms', 3),
            'property_type': extracted.get('property_type', 'Single Family'),
            'must_haves': extracted.get('must_haves', ['garage']),
            'nice_to_haves': extracted.get('nice_to_haves', ['pool', 'good_schools'])
        }

        # Get ML-enhanced matches
        ml_matches = ml_matcher.find_enhanced_matches(
            ml_preferences,
            limit=5,
            min_confidence=60.0
        )

        # Convert to UI format while preserving ML insights
        formatted_matches = []
        for match in ml_matches:
            confidence_score = match['confidence_score']

            formatted_match = {
                'address': match.get('address', {}).get('street', f"{match.get('id', 'Property')} Street"),
                'price': match.get('price', 750000),
                'beds': match.get('bedrooms', 3),
                'baths': match.get('bathrooms', 2.5),
                'sqft': match.get('sqft', 2100),
                'neighborhood': match.get('address', {}).get('neighborhood', 'Austin Area'),
                'icon': _get_property_icon(match),
                'match_score': int(confidence_score.overall),
                'budget_match': confidence_score.budget_match > 80,
                'location_match': confidence_score.location_match > 80,
                'features_match': confidence_score.feature_match > 80,
                'match_reasons': confidence_score.reasoning[:5],  # Limit to top 5 reasons
                'confidence_level': confidence_score.get_confidence_level(),
                'ml_breakdown': {
                    'budget_confidence': confidence_score.budget_match,
                    'location_confidence': confidence_score.location_match,
                    'feature_confidence': confidence_score.feature_match,
                    'market_confidence': confidence_score.market_context
                }
            }
            formatted_matches.append(formatted_match)

        # If we have ML matches, return them
        if formatted_matches:
            return formatted_matches

    except ImportError as e:
        print(f"ML matcher not available, falling back to basic matcher: {e}")
    except Exception as e:
        print(f"Error in ML matching, falling back to basic matcher: {e}")

    # Fallback to original implementation
    extracted = lead_context.get('extracted_preferences', {})
    budget = extracted.get('budget', 800000)
    location = extracted.get('location', 'Downtown')
    beds = extracted.get('bedrooms', 3)

def _get_property_icon(property_data: Dict) -> str:
    """Get appropriate icon for property type"""
    property_type = property_data.get('property_type', '').lower()
    if 'condo' in property_type:
        return '🏢'
    elif 'townhome' in property_type:
        return '🏘️'
    elif 'multi' in property_type:
        return '🏬'
    else:
        return '🏡'  # Default single family


    # Fallback to original static data for demo
    return [
        {
            'address': '123 Oak Street',
            'price': 750000,
            'beds': 3,
            'baths': 2.5,
            'sqft': 2100,
            'neighborhood': 'Downtown',
            'icon': '🏡',
            'match_score': 92,
            'budget_match': True,
            'location_match': True,
            'features_match': True,
            'match_reasons': [
                f"Within budget (${budget:,})",
                f"Perfect location ({location})",
                f"Exact bedroom count ({beds} beds)",
                "Newly renovated kitchen",
                "Walk to shops and restaurants"
            ]
        },
        {
            'address': '456 Maple Ave',
            'price': 780000,
            'beds': 3,
            'baths': 2,
            'sqft': 2300,
            'neighborhood': 'Domain',
            'icon': '🏠',
            'match_score': 88,
            'budget_match': True,
            'location_match': False,
            'features_match': True,
            'match_reasons': [
                f"Within budget (${budget:,})",
                "Pool and covered patio",
                f"{beds} bedrooms as requested",
                "Top-rated school district",
                "Adjacent to tech corridor"
            ]
        },
        {
            'address': '789 Cedar Lane',
            'price': 725000,
            'beds': 4,
            'baths': 2.5,
            'sqft': 2400,
            'neighborhood': 'South Congress',
            'icon': '🏘️',
            'match_score': 85,
            'budget_match': True,
            'location_match': True,
            'features_match': False,
            'match_reasons': [
                f"Great value (${budget - 725000:,} under budget)",
                "Trendy neighborhood",
                "Bonus 4th bedroom (home office?)",
                "Large backyard",
                "Recently listed"
            ]
        },
        {
            'address': '321 Pine Boulevard',
            'price': 795000,
            'beds': 3,
            'baths': 3,
            'sqft': 2500,
            'neighborhood': 'Westlake',
            'icon': '🏡',
            'match_score': 82,
            'budget_match': True,
            'location_match': False,
            'features_match': True,
            'match_reasons': [
                f"Just under budget (${budget:,})",
                "Luxury finishes throughout",
                f"{beds} bedrooms as requested",
                "Private backyard with lake views",
                "Gated community with amenities"
            ]
        },
        {
            'address': '555 Elm Drive',
            'price': 680000,
            'beds': 3,
            'baths': 2,
            'sqft': 1950,
            'neighborhood': 'Mueller',
            'icon': '🏠',
            'match_score': 79,
            'budget_match': True,
            'location_match': True,
            'features_match': True,
            'match_reasons': [
                f"Excellent value (${budget - 680000:,} under budget)",
                "Walk to Mueller Lake Park",
                f"Perfect {beds} bedroom layout",
                "Energy-efficient smart home",
                "Close to dining and shopping"
            ]
        }
    ]
