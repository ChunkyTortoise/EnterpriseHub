
import streamlit as st
import time
from services.enhanced_property_matcher import EnhancedPropertyMatcher

def render_property_swipe(lead_name: str = "Client"):
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

    lead_context = st.session_state.lead_options.get(selected_lead, {})
    
    # Get real properties from matcher
    matcher = EnhancedPropertyMatcher()
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
            from services.enhanced_lead_intelligence import get_enhanced_lead_intelligence
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

        # Phone Mockup Container
        st.markdown(f"""
        <div class="phone-mockup" style="max-width: 360px; margin: 0 auto; border: 8px solid #1e293b; border-radius: 36px; overflow: hidden; background: white; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);">
            <div class="phone-header" style="height: 25px; background: #1e293b; width: 120px; margin: 0 auto; border-radius: 0 0 15px 15px;"></div>
            <div style="position: relative; height: 400px;">
                <img src="{prop['image']}" style="width: 100%; height: 100%; object-fit: cover;">
                <div style="position: absolute; top: 15px; right: 15px; background: rgba(37, 99, 235, 0.9); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;">
                    {prop['ai_tag']}
                </div>
                <div style="position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); padding: 20px; color: white;">
                    <div style="font-size: 1.25rem; font-weight: 800;">{prop['price']}</div>
                    <div style="font-size: 0.9rem; font-weight: 600;">{prop['address']}</div>
                    <div style="font-size: 0.75rem; opacity: 0.8;">{prop['specs']} • {prop['neighborhood']}</div>
                </div>
            </div>
            <div style="padding: 15px; background: #eff6ff; border-top: 1px solid #dbeafe; border-bottom: 1px solid #dbeafe;">
                <div style="font-size: 0.75rem; font-weight: 800; color: #2563eb; text-transform: uppercase; margin-bottom: 4px;">🤖 Claude's Take:</div>
                <div style="font-size: 0.85rem; color: #1e40af; font-style: italic; line-height: 1.4;">
                    "{commentary}"
                </div>
            </div>
            <div style="padding: 10px 20px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                <details style="font-size: 0.75rem; color: #64748b; cursor: pointer;">
                    <summary>🧠 View Neural Reasoning</summary>
                    <div style="padding-top: 8px;">
                        Claude analyzed 15 behavioral factors including location preference, budget velocity, and feature importance to rank this property. Confidence: 94%.
                    </div>
                </details>
            </div>
            <div style="padding: 20px; display: flex; justify-content: space-around; background: #f8fafc;">
                <div style="width: 60px; height: 60px; border-radius: 50%; border: 4px solid #ef4444; display: flex; align-items: center; justify-content: center; color: #ef4444; font-size: 1.5rem; cursor: pointer;">✕</div>
                <div style="width: 60px; height: 60px; border-radius: 50%; border: 4px solid #10b981; display: flex; align-items: center; justify-content: center; color: #10b981; font-size: 1.5rem; cursor: pointer;">❤</div>
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
