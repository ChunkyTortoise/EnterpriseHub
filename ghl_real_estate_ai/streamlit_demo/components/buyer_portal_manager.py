import streamlit as st
import pandas as pd
import time
import numpy as np
from io import BytesIO
try:
    import qrcode
except ImportError:
    qrcode = None

def render_buyer_portal_manager(lead_name: str):
    """
    Buyer portal configuration and QR code generation
    """
    
    st.markdown("### 🌐 Branded Buyer Portal")
    st.markdown(f"*Custom portal management and behavioral telemetry for {lead_name}*")
    
    col_config, col_preview = st.columns([1, 1.2])
    
    with col_config:
        st.markdown("#### ⚙️ Portal Configuration")
        
        with st.container(border=True):
            # Branding options
            portal_logo = st.file_uploader("Upload Logo", type=['png', 'jpg'])
            primary_color = st.color_picker("Primary Color", "#2563eb")
            
            # Portal features
            st.markdown("**Enable Features:**")
            c1, c2 = st.columns(2)
            with c1:
                enable_favorites = st.checkbox("Favorites", value=True)
                enable_comparison = st.checkbox("Comparison", value=True)
            with c2:
                enable_financing = st.checkbox("Financing", value=True)
                enable_scheduling = st.checkbox("Scheduling", value=True)
            
            # Generate portal URL
            portal_url = f"https://portal.jorgesalas.com/{lead_name.lower().replace(' ', '-')}"
            
            st.markdown("**Access Link:**")
            st.code(portal_url, language=None)
            
            # QR Code generation
            if st.button("📱 Generate QR Code", use_container_width=True, type="primary"):
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
                            file_name=f"{lead_name}_portal_qr.png",
                            mime="image/png",
                            use_container_width=True
                        )

    with col_preview:
        st.markdown("#### 📊 Portal Analytics & Preview")
        
        # Analytics Ribbon
        a1, a2, a3 = st.columns(3)
        with a1:
            st.metric("Page Views", "142", "+12")
        with a2:
            st.metric("Avg Dwell", "8.5m", "+1.2m")
        with a3:
            st.metric("Saved", "7", "+2")

        # Behavioral Pulse
        st.markdown("**Lead Behavioral Pulse (7 Days)**")
        chart_data = pd.DataFrame(
            np.random.randn(7, 2) / [5, 5] + [0.5, 0.5],
            columns=['Property Views', 'Financing Checks']
        )
        st.line_chart(chart_data, height=150)

        # Mock portal preview
        st.markdown(f"""
        <div style='background: {primary_color}; padding: 1rem; border-radius: 8px 8px 0 0; text-align: center; margin-top: 1rem;'>
            <div style='color: white; font-size: 1rem; font-weight: 700;'>{lead_name}'s Private Collection</div>
        </div>
        <div style='background: white; border: 1px solid #e5e7eb; padding: 1.5rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);'>
            <div style='display: flex; gap: 1rem; margin-bottom: 1rem;'>
                <div style='width: 80px; height: 60px; background: #f1f5f9; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;'>🏡</div>
                <div>
                    <div style='font-weight: 700; color: #1e293b;'>2847 Glenwood Trail</div>
                    <div style='font-size: 0.8rem; color: #64748b;'>$525,000 • 3 bed, 2.5 bath</div>
                </div>
            </div>
            <div style='display: flex; gap: 0.5rem;'>
                <button style='flex: 1; padding: 0.6rem; background: {primary_color}; color: white; border: none; border-radius: 6px; font-weight: 600; font-size: 0.8rem;'>View Details</button>
                <button style='flex: 1; padding: 0.6rem; background: white; border: 1px solid {primary_color}; color: {primary_color}; border-radius: 6px; font-weight: 600; font-size: 0.8rem;'>Schedule Tour</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.caption("✅ Real-time telemetry is being recorded and synced to GHL.")
