
import streamlit as st
import time

def render_listing_architect():
    """
    Elite AI Listing Architect - Obsidian Command Edition.
    Generates high-conversion property descriptions and social syndication plans.
    """
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart, render_dossier_block
    
    st.markdown("""
        <div style="background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(20px); padding: 1.5rem 2.5rem; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);">
            <div>
                <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; margin: 0; color: #FFFFFF; letter-spacing: -0.04em; text-transform: uppercase;">✍️ LISTING ARCHITECT</h1>
                <p style="font-family: 'Inter', sans-serif; font-size: 1rem; margin: 0.5rem 0 0 0; color: #8B949E; font-weight: 500; letter-spacing: 0.02em;">Multi-channel marketing copy optimized for quantum CTR</p>
            </div>
            <div style="text-align: right;">
                <div style="background: rgba(139, 92, 246, 0.1); color: #8B5CF6; padding: 10px 20px; border-radius: 12px; font-size: 0.85rem; font-weight: 800; border: 1px solid rgba(139, 92, 246, 0.3); letter-spacing: 0.1em; display: flex; align-items: center; gap: 10px;">
                    <div class="status-pulse" style="width: 10px; height: 10px; background: #8B5CF6; border-radius: 50%;"></div>
                    CREATIVE ENGINE: ACTIVE
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col_input, col_output = st.columns([1, 1.2])
    
    with col_input:
        st.markdown("#### 🏗️ PROPERTY DNA")
        
        with st.container(border=True):
            address = st.text_input("Address", "742 Evergreen Terrace")
            price = st.number_input("Listing Price ($)", value=815000)
            
            style = st.selectbox("Narrative Style", ["Luxury/Elegant", "Family/Warm", "Modern/Minimalist", "Investor/ROI"])
            
            features = st.multiselect(
                "Key Highlights",
                ["Chef's Kitchen", "Rooftop Deck", "Smart Home", "Pool", "Walkable", "Guest Suite"],
                default=["Chef's Kitchen", "Rooftop Deck"]
            )
            
            target_audience = st.radio("Target Persona", ["Young Professionals", "Growing Families", "Retirees", "Institutional Investors"])
            
            if st.button("🚀 Architect Campaign", use_container_width=True, type="primary"):
                with st.spinner("Claude is analyzing local market trends and crafting copy..."):
                    time.sleep(1.5)
                    st.session_state.listing_generated = True
                    st.toast("Campaign Architected!", icon="✨")

    with col_output:
        if st.session_state.get('listing_generated'):
            st.markdown("#### 📄 MULTI-CHANNEL DEPLOYMENT")
            
            tab_z, tab_fb, tab_sms = st.tabs(["🏡 MLS / ZILLOW", "🟦 SOCIAL AD", "📱 SMS BLAST"])
            
            with tab_z:
                mls_copy = f"Rare opportunity in the heart of Zilker! This {style.lower()} masterpiece at {address} features a {features[0]} and a breathtaking {features[1]}. Perfect for {target_audience.lower()} seeking the ultimate Austin lifestyle. Priced competitively at ${price:,}."
                render_dossier_block(mls_copy, title="PUBLIC MLS DESCRIPTION")
                st.button("📋 Copy to Clipboard", key="copy_z", use_container_width=True)
                
            with tab_fb:
                fb_copy = f"🔥 JUST LISTED in Zilker!\n\nStop scrolling. This is the one. 🥂\n✨ {features[0]}\n✨ {features[1]}\n\nIdeal for {target_audience.lower()}!\n\n📍 {address}\n💰 ${price:,}\n\nDM for a private VIP tour before it hits Zillow! 📩"
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); font-family: 'Inter', sans-serif; line-height: 1.6; white-space: pre-wrap;">
{fb_copy}
                </div>
                """, unsafe_allow_html=True)
                st.button("🚀 Sync to Meta Ad Manager", use_container_width=True)
                
            with tab_sms:
                sms_copy = f"Hey! Just listed a gem in Zilker that matches your luxury profile. It has a {features[1]} you have to see. Want the private link? - Jorge"
                st.info(sms_copy)
                st.button("📨 Blast to 142 Matching Nodes", type="primary", use_container_width=True)
                
            st.markdown("---")
            st.markdown("#### 📈 PREDICTIVE CTR ANALYSIS")
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Estimated CTR", "4.8%", "+1.2%")
            with m2:
                st.metric("Viral Potential", "High", "82/100")
            
            # Simple bar chart for reach
            df_reach = pd.DataFrame({
                'Channel': ['Organic', 'Paid Social', 'SMS'],
                'Reach': [1200, 4500, 142]
            })
            fig = px.bar(df_reach, x='Channel', y='Reach', color='Channel', color_discrete_sequence=['#6366F1', '#8B5CF6', '#10B981'])
            st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        else:
            st.info("Define the Property DNA to initialize the architectural campaign engine.")
