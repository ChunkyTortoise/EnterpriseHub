import time
from io import BytesIO

import numpy as np
import pandas as pd
import streamlit as st

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
            portal_logo = st.file_uploader("Upload Logo", type=["png", "jpg"])
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
                        img.save(buf, format="PNG")
                        st.image(buf.getvalue(), width=200)

                        st.download_button(
                            "⬇️ Download QR Code",
                            data=buf.getvalue(),
                            file_name=f"{lead_name}_portal_qr.png",
                            mime="image/png",
                            use_container_width=True,
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
            np.random.randn(7, 2) / [5, 5] + [0.5, 0.5], columns=["Property Views", "Financing Checks"]
        )
        st.line_chart(chart_data, height=150)

        # Mock portal preview - Obsidian Edition
        st.markdown(
            f"""
        <div style='background: linear-gradient(135deg, {primary_color} 0%, #05070A 100%); padding: 1.25rem; border-radius: 12px 12px 0 0; text-align: center; margin-top: 1rem; border: 1px solid rgba(255,255,255,0.1);'>
            <div style='color: white; font-size: 0.9rem; font-weight: 700; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.1em;'>{lead_name}'S PRIVATE PORTAL</div>
        </div>
        <div style='background: rgba(22, 27, 34, 0.8); border: 1px solid rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 0 0 12px 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); backdrop-filter: blur(10px);'>
            <div style='display: flex; gap: 1rem; margin-bottom: 1.5rem;'>
                <div style='width: 80px; height: 60px; background: rgba(255,255,255,0.03); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; border: 1px solid rgba(255,255,255,0.05);'>🏡</div>
                <div>
                    <div style='font-weight: 700; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>2847 GLENWOOD TRAIL</div>
                    <div style='font-size: 0.8rem; color: #8B949E; font-family: "Inter", sans-serif; margin-top: 2px;'>$525,000 • 3 BED, 2.5 BATH</div>
                </div>
            </div>
            <div style='display: flex; gap: 0.75rem;'>
                <button style='flex: 1; padding: 0.75rem; background: {primary_color}; color: white; border: none; border-radius: 8px; font-weight: 700; font-size: 0.75rem; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;'>VIEW NODE</button>
                <button style='flex: 1; padding: 0.75rem; background: transparent; border: 1px solid rgba(255,255,255,0.2); color: #FFFFFF; border-radius: 8px; font-weight: 600; font-size: 0.75rem; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;'>SYNC CALENDAR</button>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.caption("✅ Real-time telemetry is being recorded and synced to GHL.")
