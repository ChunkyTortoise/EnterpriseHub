import streamlit as st
import pandas as pd
import time
import numpy as np
from io import BytesIO
try:
    import qrcode
except ImportError:
    qrcode = None

def render_seller_portal_manager(seller_name: str = "Elite Seller"):
    """
    Seller portal configuration and performance telemetry
    """
    
    st.markdown("### 🌐 Branded Seller Portal")
    st.markdown(f"*Custom portal management and listing performance telemetry for {seller_name}*")
    
    col_config, col_preview = st.columns([1, 1.2])
    
    with col_config:
        st.markdown("#### ⚙️ Portal Configuration")
        
        with st.container(border=True):
            # Branding options
            portal_logo = st.file_uploader("Upload Seller-Specific Logo", type=['png', 'jpg'])
            primary_color = st.color_picker("Portal Accent Color", "#10b981")
            
            # Portal features
            st.markdown("**Enable Features for Seller:**")
            c1, c2 = st.columns(2)
            with c1:
                enable_feedback = st.checkbox("Live Showing Feedback", value=True)
                enable_views = st.checkbox("Real-time View Counts", value=True)
            with c2:
                enable_docs = st.checkbox("Document Secure Box", value=True)
                enable_timeline = st.checkbox("Transaction Timeline", value=True)
            
            # Generate portal URL
            portal_url = f"https://portal.jorgesalas.com/listings/{seller_name.lower().replace(' ', '-')}"
            
            st.markdown("**Access Link:**")
            st.code(portal_url, language=None)
            
            # QR Code generation
            if st.button("📱 Generate Access QR", use_container_width=True, type="primary"):
                with st.spinner("Generating unique architectural QR..."):
                    time.sleep(1.0)
                    if qrcode is None:
                        st.error("The 'qrcode' library is required. Please install it.")
                    else:
                        qr = qrcode.QRCode(version=1, box_size=10, border=5)
                        qr.add_data(portal_url)
                        qr.make(fit=True)
                        
                        img = qr.make_image(fill_color="black", back_color="white")
                        
                        # Display QR code
                        buf = BytesIO()
                        img.save(buf, format='PNG')
                        st.image(buf.getvalue(), width=200)
                        
                        st.download_button(
                            "⬇️ Download QR Code",
                            data=buf.getvalue(),
                            file_name=f"{seller_name}_seller_portal_qr.png",
                            mime="image/png",
                            use_container_width=True
                        )

    with col_preview:
        st.markdown("#### 📊 Listing Velocity & Preview")
        
        # Analytics Ribbon
        a1, a2, a3 = st.columns(3)
        with a1:
            st.metric("Web Views", "2,842", "+312")
        with a2:
            st.metric("Inquiries", "47", "+5")
        with a3:
            st.metric("Showings", "18", "+3")

        # Performance Pulse
        st.markdown("**Listing Performance Pulse (7 Days)**")
        chart_data = pd.DataFrame(
            np.random.randn(7, 2) / [10, 10] + [1.0, 0.8],
            columns=['Property Views', 'Buyer Saves']
        )
        st.line_chart(chart_data, height=150)

        # Mock portal preview - Obsidian Edition
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {primary_color} 0%, #05070A 100%); padding: 1.25rem; border-radius: 12px 12px 0 0; text-align: center; margin-top: 1rem; border: 1px solid rgba(255,255,255,0.1);'>
            <div style='color: white; font-size: 0.9rem; font-weight: 700; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.1em;'>YOUR PROPERTY STATUS PORTAL</div>
        </div>
        <div style='background: rgba(22, 27, 34, 0.8); border: 1px solid rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 0 0 12px 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); backdrop-filter: blur(10px);'>
            <div style='margin-bottom: 1.5rem;'>
                <div style='font-size: 0.7rem; color: #8B949E; text-transform: uppercase; font-weight: 800; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>CURRENT MILESTONE</div>
                <div style='font-size: 1.25rem; font-weight: 700; color: #FFFFFF; margin-top: 4px; font-family: "Space Grotesk", sans-serif;'>NAVIGATING OFFERS</div>
                <div style='height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; margin-top: 12px; overflow: hidden;'>
                    <div style='width: 65%; height: 100%; background: {primary_color}; box-shadow: 0 0 10px {primary_color};'></div>
                </div>
            </div>
            <div style='display: flex; gap: 0.75rem;'>
                <button style='flex: 1; padding: 0.75rem; background: {primary_color}; color: white; border: none; border-radius: 8px; font-weight: 700; font-size: 0.75rem; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;'>REVIEW FEEDBACK</button>
                <button style='flex: 1; padding: 0.75rem; background: transparent; border: 1px solid rgba(255,255,255,0.2); color: #FFFFFF; border-radius: 8px; font-weight: 600; font-size: 0.75rem; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;'>MESSAGE JORGE</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.caption("✅ Sellers receive instant notifications when new milestones are achieved.")
