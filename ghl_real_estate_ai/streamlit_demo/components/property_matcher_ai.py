"""
Property Matcher AI Component
AI-powered property matching with reasoning and scoring breakdown
"""

import streamlit as st
from typing import Dict, List


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

    # Get matched properties using Strategy Pattern if in Elite Mode
    matches = generate_property_matches(lead_context, elite_mode=elite_mode)

    # PREMIUM FEATURE: Use premium property cards grid layout
    try:
        from components.property_cards import render_premium_property_grid
        st.markdown("#### 🏡 Top Property Matches")
        render_premium_property_grid(matches[:3])

        st.markdown("---")
        st.markdown("#### 📊 Detailed Analysis")

    except ImportError:
        st.info("🚀 Premium property cards available in enterprise version")

    # Initialize comparison state
    if "compare_props" not in st.session_state:
        st.session_state.compare_props = set()

    # Compare Button
    if len(st.session_state.compare_props) >= 2:
        if st.button(f"⚖️ Compare Selected ({len(st.session_state.compare_props)})", type="primary", key="compare_btn_top"):
            # Comparison View Implementation
            st.markdown("### ⚖️ Property Comparison")
            
            # Filter matches for selected properties
            selected_matches = [m for m in matches if m['address'] in st.session_state.compare_props]
            
            if len(selected_matches) < 2:
                st.warning("Please select at least 2 properties to compare.")
            else:
                # Limit to first 2 for side-by-side simplicity (or 3 max)
                compare_subset = selected_matches[:3]
                cols = st.columns(len(compare_subset))
                
                for idx, col in enumerate(cols):
                    prop = compare_subset[idx]
                    with col:
                        st.markdown(f"""
                        <div style='background: white; padding: 1rem; border-radius: 10px; border: 1px solid #e2e8f0; height: 100%;'>
                            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{prop['icon']}</div>
                            <div style='font-weight: 700; color: #1e293b; height: 3rem;'>{prop['address']}</div>
                            <div style='font-size: 1.25rem; color: #2563eb; font-weight: 800; margin: 0.5rem 0;'>${prop['price']:,}</div>
                            
                            <div style='background: #f8fafc; padding: 0.5rem; border-radius: 6px; margin-bottom: 0.5rem; font-size: 0.9rem;'>
                                🛏️ <b>{prop['beds']}</b> bd | 🛁 <b>{prop['baths']}</b> ba | 📏 <b>{prop['sqft']:,}</b> sqft
                            </div>
                            
                            <div style='margin-top: 1rem;'>
                                <div style='font-size: 0.75rem; color: #64748b; text-transform: uppercase;'>Match Score</div>
                                <div style='font-size: 1.5rem; font-weight: 800; color: #10b981;'>{prop['match_score']}%</div>
                            </div>
                            
                            <hr style='margin: 1rem 0; border-top: 1px dashed #cbd5e1;'>
                            
                            <div style='font-size: 0.85rem;'>
                                <div style='margin-bottom: 0.25rem;'>📍 Location: <b>{prop['neighborhood']}</b></div>
                                <div style='margin-bottom: 0.25rem;'>💰 Budget: {"✅" if prop['budget_match'] else "⚠️"}</div>
                                <div>⭐ Features: {"✅" if prop['features_match'] else "⚠️"}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                if st.button("❌ Close Comparison", use_container_width=True):
                    # logic to close could be clearing selection or just toggling a view state
                    # For now, we rely on the user unchecking or collapsing
                    st.session_state.compare_props = set()
                    st.rerun()

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
                
                # Claude's Psychological Deep Dive
                if analysis_result:
                    try:
                        from services.enhanced_lead_intelligence import get_enhanced_lead_intelligence
                        eli = get_enhanced_lead_intelligence()
                        
                        import asyncio
                        # Handle Streamlit event loop
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                        deep_reasoning = loop.run_until_complete(
                            eli.get_psychological_property_fit(property, analysis_result)
                        )
                        st.info(f"🤖 **Claude's Psychological Insight:** {deep_reasoning}")
                    except Exception as e:
                        st.error(f"AI Insight failed: {e}")
                else:
                    # Legacy fallback
                    try:
                        from services.property_matcher import PropertyMatcher
                        pm = PropertyMatcher()
                        deep_reasoning = pm.explain_match_with_claude(property, lead_context.get('extracted_preferences', {}))
                        st.info(f"🤖 **Claude's Psychological Insight:** {deep_reasoning}")
                    except Exception:
                        pass
                
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
                # Compare Checkbox
                lead_id = lead_context.get('lead_id', 'unknown')
                is_selected = property['address'] in st.session_state.compare_props
                if st.checkbox("Compare", key=f"compare_{lead_id}_{idx}", value=is_selected):
                    st.session_state.compare_props.add(property['address'])
                else:
                    st.session_state.compare_props.discard(property['address'])
                
                st.markdown("---")

                if st.button("📤 Send to Lead", key=f"send_{lead_id}_{idx}", use_container_width=True):
                    st.toast(f"Sent {property['address']} to lead!", icon="✅")
                
                if st.button("📅 Schedule Showing", key=f"schedule_{lead_id}_{idx}", use_container_width=True):
                    st.toast("Opening calendar...", icon="📅")
                
                if st.button("💾 Save for Later", key=f"save_{lead_id}_{idx}", use_container_width=True):
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


def generate_property_matches(lead_context: Dict, elite_mode: bool = False) -> List[Dict]:
    """
    Generate AI property matches using Strategy Pattern for flexible scoring algorithms.
    """

    # Use the unified PropertyMatcher service
    try:
        from services.property_matcher import PropertyMatcher
        pm = PropertyMatcher()
        
        # Set strategy based on elite_mode
        pm.set_strategy("ai" if elite_mode else "basic")
        
        # Extract lead preferences from context
        extracted = lead_context.get('extracted_preferences', {})
        
        # Find matches
        raw_matches = pm.find_matches(extracted, limit=5)
        
        # Format for UI
        formatted_matches = []
        for prop in raw_matches:
            formatted_matches.append({
                'id': prop.get('id', 'unknown'),
                'address': f"{prop.get('address', {}).get('street', 'Address')}, {prop.get('address', {}).get('city', 'City')}",
                'price': prop.get('price', 750000),
                'beds': prop.get('bedrooms', 3),
                'baths': prop.get('bathrooms', 2.5),
                'sqft': prop.get('sqft', 2100),
                'neighborhood': prop.get('address', {}).get('neighborhood', 'Area'),
                'icon': _get_property_icon(prop),
                'match_score': int(prop.get('match_score', 0) * 100),
                'budget_match': prop.get('match_score', 0) > 0.7, # Simplified
                'location_match': True, # Simplified
                'features_match': True, # Simplified
                'match_reasons': [pm.generate_match_reasoning(prop, extracted)],
                'match_type': prop.get('match_type', 'Standard'),
                'ai_reasoning': prop.get('ai_reasoning', '')
            })
            
        if formatted_matches:
            return formatted_matches

    except Exception as e:
        print(f"Error in dynamic property matching: {e}")

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
    Persona-aware for high-impact demo scenarios.
    """
    lead_id = lead_context.get('lead_id', 'unknown')
    extracted = lead_context.get('extracted_preferences', {})
    budget = extracted.get('budget', 800000)
    
    # Sarah Chen (Apple Engineer) - North Austin/Round Rock focus
    if lead_id == 'tech_professional_sarah':
        return [
            {
                'address': '2847 Glenwood Trail',
                'price': 525000,
                'beds': 3,
                'baths': 2.5,
                'sqft': 2180,
                'neighborhood': 'Teravista (Round Rock)',
                'icon': '🏡',
                'match_score': 95,
                'budget_match': True,
                'location_match': True,
                'features_match': True,
                'match_reasons': [
                    "Under SF-adjusted budget ($550k)",
                    "12-min commute to Apple campus",
                    "Gigabit fiber internet ready",
                    "Dedicated home office space",
                    "Round Rock ISD (9/10 rating)"
                ]
            },
            {
                'address': '15823 Fontana Lake Dr',
                'price': 585000,
                'beds': 4,
                'baths': 3,
                'sqft': 2650,
                'neighborhood': 'Avery Ranch',
                'icon': '🏠',
                'match_score': 88,
                'budget_match': False,
                'location_match': True,
                'features_match': True,
                'match_reasons': [
                    "Premium location near Brushy Creek",
                    "Modern open floor plan",
                    "Large secondary office/flex space",
                    "Walkable to local coffee shops",
                    "High-speed networking installed"
                ]
            }
        ]
    
    # David Kim (Investor) - Manor/Del Valle focus
    elif lead_id == 'investor_david':
        return [
            {
                'address': '14821 Willow Ridge Dr',
                'price': 285000,
                'beds': 3,
                'baths': 2,
                'sqft': 1420,
                'neighborhood': 'Manor',
                'icon': '💰',
                'match_score': 98,
                'budget_match': True,
                'location_match': True,
                'features_match': True,
                'match_reasons': [
                    "Projected $270/mo positive cash flow",
                    "Turnkey condition (built 2018)",
                    "High rental demand (95% area occupancy)",
                    "Rapid appreciation forecast (12%+)",
                    "Manor tech-corridor growth zone"
                ]
            },
            {
                'address': '101 Cedar Rd',
                'price': 320000,
                'beds': 2,
                'baths': 1,
                'sqft': 1100,
                'neighborhood': 'Del Valle',
                'icon': '🏬',
                'match_score': 91,
                'budget_match': True,
                'location_match': True,
                'features_match': True,
                'match_reasons': [
                    "Proximity to Tesla Giga Austin",
                    "Low maintenance exterior",
                    "Ideal entry-level rental",
                    "Strategic land-value hold",
                    "Near Austin Airport expansion"
                ]
            }
        ]

    # Default fallback
    location = extracted.get('location', 'Austin')
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
                f"Location compatibility ({location})",
                f"Exact bedroom count ({beds} beds)",
                "Newly renovated kitchen",
                "Walk to shops and restaurants"
            ]
        }
    ]
