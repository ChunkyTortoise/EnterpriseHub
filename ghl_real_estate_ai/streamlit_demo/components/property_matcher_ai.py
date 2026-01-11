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
                if st.button("📤 Send to Lead", key=f"send_{idx}", width='stretch'):
                    st.toast(f"Sent {property['address']} to lead!", icon="✅")
                
                if st.button("📅 Schedule Showing", key=f"schedule_{idx}", width='stretch'):
                    st.toast("Opening calendar...", icon="📅")
                
                if st.button("💾 Save for Later", key=f"save_{idx}", width='stretch'):
                    st.toast("Property saved!", icon="💾")
    
    # Batch actions
    st.markdown("---")
    col_batch1, col_batch2 = st.columns(2)
    
    with col_batch1:
        if st.button("📧 Send Top 3 Properties", width='stretch', type="primary"):
            st.success("Top 3 properties sent via email!")
    
    with col_batch2:
        if st.button("🔄 Find More Matches", width='stretch'):
            st.info("Searching MLS database...")


def generate_property_matches(lead_context: Dict) -> List[Dict]:
    """
    Generate AI property matches using Strategy Pattern for flexible scoring algorithms.

    Enterprise-grade property matching with configurable strategies:
    1. Load property data from available sources
    2. Apply configurable scoring strategy (Basic, Enhanced, ML)
    3. Generate detailed reasoning and confidence scores
    4. Return ranked properties with transparent AI decisions

    Strategies automatically selected based on context:
    - High-volume: Basic scorer (1000+ props/sec)
    - Balanced: Enhanced scorer (200-500 props/sec)
    - ML-powered: Advanced scorer with behavioral learning

    Args:
        lead_context: Dictionary containing lead preferences and context

    Returns:
        List of property dictionaries with strategy-based scoring and reasoning
    """

    # Import the new Strategy Pattern implementation
    try:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent.parent))

        from services.scoring import (
            create_property_matcher,
            ScoringContext,
            get_scoring_factory
        )

        # Extract lead preferences from context
        extracted = lead_context.get('extracted_preferences', {})

        # Create scoring context for strategy selection
        scoring_context = ScoringContext(
            lead_id=lead_context.get('lead_id'),
            agent_id=lead_context.get('agent_id'),
            market_area='austin',
            performance_priority='balanced',  # Use enhanced strategy
            enable_learning=True,
            min_confidence=60.0,
            max_properties=10
        )

        # Create property matcher with strategy and fallback
        matcher = create_property_matcher(
            strategy_name="enhanced",      # Primary: Advanced 15-factor scoring
            fallback_strategy="basic",     # Fallback: Fast rule-based scoring
            enable_monitoring=True,        # Track performance metrics
            enable_caching=False          # Disable for demo (would use Redis in prod)
        )

        # Load demo property data (in production, this would come from MLS/database)
        demo_properties = _load_demo_properties()

        # Enhanced preferences for strategy-based matching
        lead_preferences = {
            'budget': extracted.get('budget', 800000),
            'location': extracted.get('location', 'Downtown'),
            'bedrooms': extracted.get('bedrooms', 3),
            'bathrooms': extracted.get('bathrooms', 2),
            'property_type': extracted.get('property_type', 'Single Family'),
            'must_haves': extracted.get('must_haves', ['garage']),
            'nice_to_haves': extracted.get('nice_to_haves', ['pool', 'good_schools']),
            'work_location': extracted.get('work_location', 'downtown'),
            'has_children': extracted.get('has_children', False),
            'min_sqft': extracted.get('min_sqft', 1800)
        }

        # Score properties using Strategy Pattern
        scored_properties = matcher.score_multiple_properties(
            properties=demo_properties,
            lead_preferences=lead_preferences,
            context=scoring_context,
            max_workers=2  # Parallel processing for demo
        )

        # Convert strategy results to UI format
        formatted_matches = []
        for property_data in scored_properties[:5]:  # Top 5 matches
            formatted_match = {
                'address': property_data.get('address', 'Property Address'),
                'price': property_data.get('price', 750000),
                'beds': property_data.get('bedrooms', property_data.get('beds', 3)),
                'baths': property_data.get('bathrooms', property_data.get('baths', 2.5)),
                'sqft': property_data.get('sqft', property_data.get('square_feet', 2100)),
                'neighborhood': property_data.get('neighborhood', 'Austin Area'),
                'icon': _get_property_icon(property_data),
                'match_score': int(property_data.get('overall_score', 75)),
                'budget_match': property_data.get('budget_match', False),
                'location_match': property_data.get('location_match', False),
                'features_match': property_data.get('features_match', False),
                'match_reasons': property_data.get('match_reasons', ['Property matched']),
                'confidence_level': property_data.get('confidence_level', 'medium'),
                'strategy_metadata': property_data.get('scoring_metadata', {})
            }
            formatted_matches.append(formatted_match)

        # Log performance metrics for monitoring
        metrics = matcher.get_performance_metrics()
        print(f"Strategy Pattern Performance: {metrics.get('average_time_per_score', 'N/A')}s per property")

        return formatted_matches

    except ImportError as e:
        print(f"Strategy Pattern not available, using fallback: {e}")
    except Exception as e:
        print(f"Strategy Pattern error, using fallback: {e}")

    # Ultimate fallback to static demo data
    return _get_fallback_properties(lead_context)

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
            'id': 'prop-001',
            'address': '123 Oak Street',
            'price': 750000,
            'bedrooms': 3,
            'bathrooms': 2.5,
            'sqft': 2100,
            'neighborhood': 'Downtown',
            'property_type': 'Single Family',
            'year_built': 2018,
            'recently_renovated': True,
            'amenities': ['garage', 'updated_kitchen', 'hardwood_floors'],
            'days_on_market': 12
        },
        {
            'id': 'prop-002',
            'address': '456 Maple Ave',
            'price': 780000,
            'bedrooms': 3,
            'bathrooms': 2,
            'sqft': 2300,
            'neighborhood': 'Domain',
            'property_type': 'Single Family',
            'year_built': 2020,
            'recently_renovated': False,
            'amenities': ['pool', 'garage', 'outdoor_space'],
            'days_on_market': 8
        },
        {
            'id': 'prop-003',
            'address': '789 Cedar Lane',
            'price': 725000,
            'bedrooms': 4,
            'bathrooms': 2.5,
            'sqft': 2400,
            'neighborhood': 'South Congress',
            'property_type': 'Townhome',
            'year_built': 2019,
            'recently_renovated': False,
            'amenities': ['garage', 'outdoor_space'],
            'days_on_market': 15
        },
        {
            'id': 'prop-004',
            'address': '321 Pine Boulevard',
            'price': 795000,
            'bedrooms': 3,
            'bathrooms': 3,
            'sqft': 2500,
            'neighborhood': 'Westlake',
            'property_type': 'Single Family',
            'year_built': 2021,
            'recently_renovated': False,
            'amenities': ['garage', 'pool', 'hardwood_floors', 'updated_kitchen'],
            'days_on_market': 5
        },
        {
            'id': 'prop-005',
            'address': '555 Elm Drive',
            'price': 680000,
            'bedrooms': 3,
            'bathrooms': 2,
            'sqft': 1950,
            'neighborhood': 'Mueller',
            'property_type': 'Single Family',
            'year_built': 2017,
            'recently_renovated': True,
            'amenities': ['garage', 'outdoor_space', 'updated_kitchen'],
            'days_on_market': 20
        },
        {
            'id': 'prop-006',
            'address': '888 Willow Way',
            'price': 850000,
            'bedrooms': 4,
            'bathrooms': 3.5,
            'sqft': 2800,
            'neighborhood': 'Tarrytown',
            'property_type': 'Single Family',
            'year_built': 2022,
            'recently_renovated': False,
            'amenities': ['garage', 'pool', 'hardwood_floors', 'updated_kitchen', 'outdoor_space'],
            'days_on_market': 3
        },
        {
            'id': 'prop-007',
            'address': '999 Highland Ave',
            'price': 720000,
            'bedrooms': 3,
            'bathrooms': 2,
            'sqft': 2050,
            'neighborhood': 'Highland',
            'property_type': 'Single Family',
            'year_built': 2016,
            'recently_renovated': True,
            'amenities': ['garage', 'hardwood_floors'],
            'days_on_market': 18
        }
    ]


def _get_fallback_properties(lead_context: Dict) -> List[Dict]:
    """
    Ultimate fallback to static demo data when Strategy Pattern is unavailable.

    Maintains backward compatibility and ensures demo always works.

    Args:
        lead_context: Lead context for basic customization

    Returns:
        List of formatted property matches
    """
    extracted = lead_context.get('extracted_preferences', {})
    budget = extracted.get('budget', 800000)
    location = extracted.get('location', 'Downtown')
    beds = extracted.get('bedrooms', 3)

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
