
import streamlit as st
import time

def render_property_swipe():
    """
    Elite "Property Swipe" Interface (Tinder for Real Estate).
    A high-engagement mobile-first component for buyers.
    """
    st.subheader("🔥 Property Discovery: Smart Swipe")
    st.markdown("*Swipe right to save, left to skip. Our AI learns your style in real-time.*")
    
    # Initialize swipe state
    if 'swipe_index' not in st.session_state:
        st.session_state.swipe_index = 0
    if 'saved_count' not in st.session_state:
        st.session_state.saved_count = 0

    properties = [
        {
            "address": "742 Evergreen Terrace",
            "price": "$815,000",
            "specs": "4 bed | 3 bath | 2,800 sqft",
            "neighborhood": "Zilker",
            "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&q=80&w=800",
            "ai_tag": "High ROI Potential"
        },
        {
            "address": "101 Skyline Drive",
            "price": "$1,250,000",
            "specs": "3 bed | 3.5 bath | 3,200 sqft",
            "neighborhood": "West Lake Hills",
            "image": "https://images.unsplash.com/photo-1600585014340-be6161a56a0c?auto=format&fit=crop&q=80&w=800",
            "ai_tag": "Luxury Pick"
        },
        {
            "address": "404 Error Lane",
            "price": "$550,000",
            "specs": "2 bed | 1 bath | 1,100 sqft",
            "neighborhood": "East Austin",
            "image": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?auto=format&fit=crop&q=80&w=800",
            "ai_tag": "Trendy Area"
        }
    ]

    if st.session_state.swipe_index < len(properties):
        prop = properties[st.session_state.swipe_index]
        
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
