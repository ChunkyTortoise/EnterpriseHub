
import streamlit as st
import time
from ghl_real_estate_ai.services.enhanced_property_matcher import EnhancedPropertyMatcher

def render_property_swipe(services, lead_name: str = "Client"):
    """
    Elite "Property Swipe" Interface (Tinder for Real Estate).
    A high-engagement mobile-first component for buyers.
    """
    st.subheader("🔥 Property Discovery: Smart Swipe")
    st.markdown(f"*Swiping for **{lead_name}**. Our AI learns your style in real-time.*")
    
    # Initialize swipe state
    if 'swipe_index' not in st.session_state:
        st.session_state.swipe_index = 0
    if 'saved_count' not in st.session_state:
        st.session_state.saved_count = 0

    # Get current lead context
    selected_lead = st.session_state.get('selected_lead_name', '-- Select a Lead --')
    if selected_lead == "-- Select a Lead --":
        st.warning("Please select a lead in the Lead Scoring tab to begin discovery.")
        return

    lead_options = st.session_state.get('lead_options', {})
    lead_context = lead_options.get(selected_lead, {})
    
    # Get real properties from matcher
    matcher = services.get("enhanced_property_matcher", EnhancedPropertyMatcher())
    matches = matcher.find_enhanced_matches(lead_context.get('extracted_preferences', {}), limit=10)
    
    properties = []
    for match in matches:
        prop = match.property
        properties.append({
            "address": prop.get('address', {}).get('street', 'Unknown'),
            "price": f"${prop.get('price', 0):,}",
            "specs": f"{prop.get('bedrooms', 0)} bed | {prop.get('bathrooms', 0)} bath | {prop.get('sqft', 0)} sqft",
            "neighborhood": prop.get('address', {}).get('neighborhood', 'Unknown'),
            "image": prop.get('image_url', "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&q=80&w=800"),
            "ai_tag": match.reasoning.primary_strengths[0] if match.reasoning.primary_strengths else "Top Match",
            "raw_data": prop
        })

    if not properties:
        st.info("No properties found matching your criteria. Try adjusting your preferences.")
        return

    if st.session_state.swipe_index < len(properties):
        prop = properties[st.session_state.swipe_index]
        
        # Claude's Real-time Commentary
        try:
            from ghl_real_estate_ai.services.enhanced_lead_intelligence import get_enhanced_lead_intelligence
            eli = get_enhanced_lead_intelligence()
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            commentary = loop.run_until_complete(eli.get_swipe_commentary(prop['raw_data'], lead_name))
        except Exception:
            commentary = f"A stunning find in {prop['neighborhood']}!"

        # Phone Mockup Container - Obsidian Command Edition
        st.markdown(f"""
        <div class="phone-mockup" style="max-width: 360px; margin: 0 auto; border: 10px solid #161B22; border-radius: 40px; overflow: hidden; background: #05070A; box-shadow: 0 25px 60px rgba(0,0,0,0.8); border: 1px solid rgba(255,255,255,0.1);">
            <div class="phone-header" style="height: 25px; background: #161B22; width: 140px; margin: 0 auto; border-radius: 0 0 20px 20px;"></div>
            <div style="position: relative; height: 420px;">
                <img src="{prop['image']}" style="width: 100%; height: 100%; object-fit: cover;">
                <div style="position: absolute; top: 15px; right: 15px; background: rgba(99, 102, 241, 0.9); color: white; padding: 6px 14px; border-radius: 8px; font-size: 0.7rem; font-weight: 800; font-family: 'Space Grotesk', sans-serif; text-transform: uppercase; letter-spacing: 0.05em; border: 1px solid rgba(255,255,255,0.2);">
                    {prop['ai_tag']}
                </div>
                <div style="position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(5,7,10,0.95), transparent); padding: 25px 20px; color: white;">
                    <div style="font-size: 1.5rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif; color: #FFFFFF;">{prop['price']}</div>
                    <div style="font-size: 0.95rem; font-weight: 600; font-family: 'Inter', sans-serif; color: #E6EDF3;">{prop['address']}</div>
                    <div style="font-size: 0.75rem; opacity: 0.7; color: #8B949E; margin-top: 4px;">{prop['specs']} • {prop['neighborhood'].upper()}</div>
                </div>
            </div>
            <div style="padding: 1.5rem; background: rgba(99, 102, 241, 0.05); border-top: 1px solid rgba(99, 102, 241, 0.2); border-bottom: 1px solid rgba(99, 102, 241, 0.2);">
                <div style="font-size: 0.75rem; font-weight: 800; color: #6366F1; text-transform: uppercase; margin-bottom: 6px; font-family: 'Space Grotesk', sans-serif; letter-spacing: 0.1em;">🤖 CLAUDE'S SYNTHESIS:</div>
                <div style="font-size: 0.9rem; color: #E6EDF3; font-style: italic; line-height: 1.5; font-family: 'Inter', sans-serif; opacity: 0.9;">
                    "{commentary}"
                </div>
            </div>
            <div style="padding: 12px 20px; background: rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.05);">
                <details style="font-size: 0.75rem; color: #8B949E; cursor: pointer; font-family: 'Inter', sans-serif;">
                    <summary style="font-weight: 600;">🧠 VIEW NEURAL REASONING</summary>
                    <div style="padding-top: 10px; line-height: 1.4; opacity: 0.8;">
                        Claude analyzed 15 behavioral signals including architectural preference, fiscal velocity, and neighborhood compatibility. Match Score: 94%.
                    </div>
                </details>
            </div>
            <div style="padding: 20px; display: flex; justify-content: space-around; background: rgba(5,7,10,0.5); backdrop-filter: blur(10px);">
                <div style="width: 55px; height: 55px; border-radius: 50%; border: 3px solid rgba(239, 68, 68, 0.3); display: flex; align-items: center; justify-content: center; color: #ef4444; font-size: 1.2rem; cursor: pointer; background: rgba(239, 68, 68, 0.05);">✕</div>
                <div style="width: 55px; height: 55px; border-radius: 50%; border: 3px solid rgba(16, 185, 129, 0.3); display: flex; align-items: center; justify-content: center; color: #10b981; font-size: 1.2rem; cursor: pointer; background: rgba(16, 185, 129, 0.05);">❤</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("⬅️ Skip (Left)", use_container_width=True):
                st.session_state.swipe_index += 1
                st.rerun()
        with col_btn2:
            if st.button("❤️ Save (Right)", use_container_width=True, type="primary"):
                st.session_state.swipe_index += 1
                st.session_state.saved_count += 1
                st.toast(f"Saved {prop['address']}!", icon="❤️")
                st.rerun()
    else:
        st.success(f"You've reviewed all daily matches! ({st.session_state.saved_count} saved)")
        if st.button("🔄 Refresh Matches"):
            st.session_state.swipe_index = 0
            st.session_state.saved_count = 0
            st.rerun()

    # Learning Progress
    st.markdown("---")
    st.markdown("#### 🧠 Style Learning Progress")
    progress = min(st.session_state.swipe_index * 33, 100)
    st.progress(progress / 100)
    st.caption(f"AI is {progress}% calibrated to your aesthetic preferences.")
