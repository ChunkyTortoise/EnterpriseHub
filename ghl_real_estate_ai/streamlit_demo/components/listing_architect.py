
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
import time
import asyncio
from ghl_real_estate_ai.services.intelligent_listing_generator import IntelligentListingGenerator

def render_listing_architect():
    """
    Elite AI Listing Architect - Obsidian Command Edition.
    Generates high-conversion property descriptions and social syndication plans.
    """
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart, render_dossier_block
    import pandas as pd
    import plotly.express as px
    
    # Initialize generator
    if 'listing_generator' not in st.session_state:
        st.session_state.listing_generator = IntelligentListingGenerator()
    
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
            address = st.text_input("Address", "1234 Oak Hill Drive, Austin, TX 78704")
            zip_code = st.text_input("ZIP Code", "78704")
            price = st.number_input("Listing Price ($)", value=815000)
            
            style = st.selectbox("Preferred Narrative", ["Luxury/Elegant", "Family/Warm", "Investor/ROI", "Modern/Minimalist"])
            
            features = st.multiselect(
                "Key Highlights",
                ["Chef's Kitchen", "Rooftop Deck", "Smart Home", "Pool", "Walkable", "Guest Suite", "Solar Panels", "Updated HVAC"],
                default=["Chef's Kitchen", "Rooftop Deck"]
            )
            
            target_audience = st.radio("Target Persona", ["Young Professionals", "Growing Families", "Retirees", "Institutional Investors"])
            
            if st.button("🚀 Architect Campaign", use_container_width=True, type="primary"):
                with st.spinner("Claude is analyzing local market trends and crafting copy..."):
                    # Prepare property data
                    prop_data = {
                        "address": address,
                        "zip_code": zip_code,
                        "price": price,
                        "features": features,
                        "type": "Single Family" # Simplified
                    }
                    
                    # Run async generation
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        listings = run_async(
                            st.session_state.listing_generator.generate_enhanced_listings(prop_data)
                        )
                        st.session_state.architect_results = listings
                        st.session_state.listing_generated = True
                        st.toast("Campaign Architected!", icon="✨")
                    except Exception as e:
                        st.error(f"Generation failed: {e}")

    with col_output:
        if st.session_state.get('listing_generated') and 'architect_results' in st.session_state:
            st.markdown("#### 📄 MULTI-CHANNEL DEPLOYMENT")
            
            results = st.session_state.architect_results
            # Map style selection to result index if possible, or just show all
            
            tab_z, tab_fb, tab_sms = st.tabs(["🏡 MLS / ZILLOW", "🟦 SOCIAL AD", "📱 SMS BLAST"])
            
            with tab_z:
                # Show the most relevant result based on style
                # results: [emotional, analytical, premium]
                selected_result = results[0] # Default
                if "Luxury" in style: selected_result = results[2]
                elif "Investor" in style: selected_result = results[1]
                
                render_dossier_block(selected_result['text'], title=f"PUBLIC MLS DESCRIPTION ({selected_result['tone'].upper()})")
                
                if selected_result.get('market_summary'):
                    st.caption(f"💡 Market Context Injected: {selected_result['market_summary']}")
                
                st.button("📋 Copy to Clipboard", key="copy_z", use_container_width=True)
                
            with tab_fb:
                # Generate a social ad variation
                fb_copy = f"🔥 JUST LISTED in {results[0].get('neighborhood', 'Austin')}!\n\nStop scrolling. This is the one. 🥂\n"
                for f in features[:2]:
                    fb_copy += f"✨ {f}\n"
                fb_copy += f"\nIdeal for {target_audience.lower()}!\n\n📍 {address}\n💰 ${price:,}\n\nDM for a private VIP tour before it hits Zillow! 📩"
                
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); font-family: 'Inter', sans-serif; line-height: 1.6; white-space: pre-wrap;">
{fb_copy}
                </div>
                """, unsafe_allow_html=True)
                st.button("🚀 Sync to Meta Ad Manager", use_container_width=True)
                
            with tab_sms:
                sms_copy = f"Hey! Just listed a gem in {results[0].get('neighborhood', 'your area')} that matches your profile. It has a {features[0]} you have to see. Want the private link? - Jorge"
                st.info(sms_copy)
                st.button("📨 Blast to Matching Nodes", type="primary", use_container_width=True)
                
            st.markdown("---")
            st.markdown("#### 📈 PREDICTIVE PERFORMANCE")
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Estimated CTR", "5.2%", "+1.6%")
            with m2:
                st.metric("Market Fit", "94/100", "High")
            
            # Reach chart
            df_reach = pd.DataFrame({
                'Channel': ['Organic', 'Paid Social', 'SMS'],
                'Reach': [1450, 5200, 186]
            })
            fig = px.bar(df_reach, x='Channel', y='Reach', color='Channel', color_discrete_sequence=['#6366F1', '#8B5CF6', '#10B981'])
            st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        else:
            st.info("Define the Property DNA to initialize the architectural campaign engine.")
