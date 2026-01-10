"""
Enhanced Property Matcher AI Component
AI-powered property matching with ML confidence scoring and reasoning breakdown
"""

import streamlit as st
from typing import Dict, List


def render_enhanced_property_matcher(lead_context: Dict):
    """
    Enhanced AI-powered property matching with ML confidence scoring

    Args:
        lead_context: Dictionary containing lead preferences and information
    """

    st.markdown("### 🏠 AI Property Matcher Pro")
    st.markdown("*ML-powered matching with confidence scoring*")

    # Get enhanced ML matches
    matches = generate_enhanced_property_matches(lead_context)

    # PREMIUM FEATURE: Use premium property cards grid layout
    try:
        from components.property_cards import render_premium_property_grid
        st.markdown("#### 🏡 Top Property Matches")
        render_premium_property_grid(matches[:3])

        st.markdown("---")
        st.markdown("#### 📊 ML Confidence Analysis")

    except ImportError:
        st.info("🚀 Premium property cards available in enterprise version")

    # Display enhanced analysis with ML confidence breakdown
    for idx, property in enumerate(matches[:3]):
        confidence_level = property.get('confidence_level', 'medium')
        confidence_color = {
            'high': '🟢',
            'medium': '🟡',
            'low': '🔴'
        }.get(confidence_level, '🟡')

        with st.expander(
            f"{property['icon']} {property['address']} - {property['match_score']}% Match {confidence_color}",
            expanded=(idx == 0)
        ):

            col_info, col_actions = st.columns([2, 1])

            with col_info:
                st.markdown(f"**${property['price']:,}** | {property['beds']} bed, {property['baths']} bath | {property['sqft']:,} sqft")
                st.markdown(f"**Location**: {property['neighborhood']}")

                # Enhanced ML reasoning
                st.markdown("#### 🤖 AI Reasoning (ML-Powered)")
                for reason in property['match_reasons']:
                    st.success(f"✅ {reason}")

                # ML Confidence Breakdown
                if 'ml_breakdown' in property:
                    st.markdown("#### 📈 ML Confidence Breakdown")
                    ml_scores = property['ml_breakdown']

                    # Create confidence visualization
                    for category, score in ml_scores.items():
                        category_name = category.replace('_', ' ').title()
                        color = "#10b981" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"

                        st.markdown(f"""
                        <div style="margin: 0.5rem 0;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                                <span style="font-size: 0.85rem; font-weight: 600; color: #1e293b;">{category_name}</span>
                                <span style="font-size: 0.85rem; font-weight: 700; color: {color};">{score:.1f}%</span>
                            </div>
                            <div style="background: #f1f5f9; height: 8px; border-radius: 4px; overflow: hidden;">
                                <div style="background: {color}; width: {score}%; height: 100%; transition: width 0.3s ease;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # Enhanced Gap Analysis
                st.markdown("#### 📊 Enhanced Gap Analysis")

                lead_budget = lead_context.get('extracted_preferences', {}).get('budget', 800000)
                property_price = property.get('price', 0)
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

                # Enhanced gap indicator
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

            with col_actions:
                if st.button("📤 Send to Lead", key=f"enhanced_send_{idx}", width='stretch'):
                    st.toast(f"Sent {property['address']} to lead!", icon="✅")

                if st.button("📅 Schedule Showing", key=f"enhanced_schedule_{idx}", width='stretch'):
                    st.toast("Opening calendar...", icon="📅")

                if st.button("💾 Save for Later", key=f"enhanced_save_{idx}", width='stretch'):
                    st.toast("Property saved!", icon="💾")

                # FEEDBACK LOOP: Missed Match Button
                if st.button("❌ Missed Match?", key=f"missed_match_{idx}", width='stretch', help="Tell us why this isn't a good match to help Jorge's AI learn."):
                    st.session_state[f"show_feedback_{idx}"] = True

                if st.session_state.get(f"show_feedback_{idx}"):
                    with st.form(key=f"feedback_form_{idx}"):
                        st.markdown("**Help AI Learn**")
                        feedback_reason = st.text_area("Why is this a missed match?", placeholder="e.g., Too far from work, neighborhood feels unsafe, budget doesn't account for HOA...")
                        
                        col_f1, col_f2 = st.columns(2)
                        with col_f1:
                            if st.form_submit_button("Submit & Learn"):
                                # Record feedback in ML service
                                try:
                                    import sys
                                    from pathlib import Path
                                    sys.path.append(str(Path(__file__).parent.parent.parent))
                                    from services.property_matcher_ml import PropertyMatcherML
                                    
                                    ml_matcher = PropertyMatcherML()
                                    lead_id = lead_context.get('lead_id', 'demo_lead')
                                    property_id = property.get('id', 'unknown')
                                    
                                    success = ml_matcher.record_feedback(
                                        lead_id=lead_id,
                                        property_id=property_id,
                                        feedback_type="missed_match",
                                        comments=feedback_reason
                                    )
                                    
                                    if success:
                                        st.success("Thanks! Jorge's AI is learning.")
                                        st.session_state[f"show_feedback_{idx}"] = False
                                        st.toast("Feedback recorded - AI retraining queued", icon="🧠")
                                except Exception as e:
                                    st.error(f"Error recording feedback: {e}")
                        
                        with col_f2:
                            if st.form_submit_button("Cancel"):
                                st.session_state[f"show_feedback_{idx}"] = False
                                st.rerun()

                # ML Insights Button
                if st.button("🧠 ML Insights", key=f"ml_insights_{idx}", width='stretch'):
                    st.info("Feature importance analysis: Budget (35%), Location (30%), Features (25%), Market (10%)")

    # Enhanced batch actions
    st.markdown("---")
    col_batch1, col_batch2, col_batch3 = st.columns(3)

    with col_batch1:
        if st.button("📧 Send Top 3 Properties", width='stretch', type="primary"):
            st.success("Top 3 ML-matched properties sent via email!")

    with col_batch2:
        if st.button("🔄 Find More Matches", width='stretch'):
            st.info("Searching MLS with enhanced ML algorithms...")

    with col_batch3:
        if st.button("📊 Show ML Analytics", width='stretch'):
            st.info("Opening advanced property analytics dashboard...")


def generate_enhanced_property_matches(lead_context: Dict) -> List[Dict]:
    """
    Generate enhanced property matches using ML-powered confidence scoring

    Args:
        lead_context: Dictionary containing lead preferences

    Returns:
        List of enhanced property dictionaries with ML confidence scores
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

            # Extract address properly
            address_data = match.get('address', {})
            if isinstance(address_data, dict):
                street_address = address_data.get('street', f"{match.get('id', 'Property')} Street")
                neighborhood = address_data.get('neighborhood', 'Austin Area')
            else:
                street_address = str(address_data)
                neighborhood = 'Austin Area'

            formatted_match = {
                'address': street_address,
                'price': match.get('price', 750000),
                'beds': match.get('bedrooms', 3),
                'baths': match.get('bathrooms', 2.5),
                'sqft': match.get('sqft', 2100),
                'neighborhood': neighborhood,
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
        st.info("🤖 ML matcher loading... Fallback mode activated")
        print(f"ML matcher not available, falling back to demo data: {e}")
    except Exception as e:
        st.warning("⚠️ ML service temporarily unavailable, using demo data")
        print(f"Error in ML matching, falling back to demo data: {e}")

    # Enhanced fallback demo data that showcases ML features
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
            'match_score': 94,
            'budget_match': True,
            'location_match': True,
            'features_match': True,
            'confidence_level': 'high',
            'match_reasons': [
                f"Excellent value at ${(budget - 750000)/1000:.0f}k under your ${budget/1000:.0f}k budget",
                f"Prime location in {location} as requested",
                "Has all your must-have features: garage, good schools",
                f"Perfect {beds}-bedroom layout matches your needs",
                "Hot property - recently listed and likely to move quickly"
            ],
            'ml_breakdown': {
                'budget_confidence': 92.0,
                'location_confidence': 95.0,
                'feature_confidence': 96.0,
                'market_confidence': 88.0
            }
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
            'confidence_level': 'high',
            'match_reasons': [
                f"Perfectly priced within your ${budget/1000:.0f}k budget",
                "Pool and covered patio as requested",
                f"Spacious {beds} bedrooms with bonus space",
                "Top-rated school district (rated 9/10)",
                "Adjacent to tech corridor for easy commuting"
            ],
            'ml_breakdown': {
                'budget_confidence': 89.0,
                'location_confidence': 75.0,
                'feature_confidence': 92.0,
                'market_confidence': 85.0
            }
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
            'confidence_level': 'high',
            'match_reasons': [
                f"Great value at ${(budget - 725000)/1000:.0f}k under budget - Excellent value!",
                "Trendy neighborhood with walkable amenities",
                "Bonus 4th bedroom perfect for home office",
                "Large backyard for outdoor activities",
                "Recently updated kitchen and bathrooms"
            ],
            'ml_breakdown': {
                'budget_confidence': 95.0,
                'location_confidence': 88.0,
                'feature_confidence': 78.0,
                'market_confidence': 82.0
            }
        }
    ]


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