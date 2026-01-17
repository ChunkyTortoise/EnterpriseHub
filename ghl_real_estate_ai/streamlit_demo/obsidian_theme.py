import streamlit as st
import plotly.graph_objects as go

def inject_elite_css():
    """
    Injects 'The Obsidian Command v2.0' Visual Overhaul CSS.
    Implements SaaS-Noir aesthetics, Glassmorphism, and custom typography.
    Includes Font Awesome 6.5.1 for icon system.
    """
    st.markdown("""
        <!-- Font Awesome 6.5.1 -->
        <link rel="stylesheet"
              href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
              integrity="sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA=="
              crossorigin="anonymous"
              referrerpolicy="no-referrer" />

        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;700&display=swap');

            /* Global Typography */
            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
                color: #E6EDF3 !important;
            }

            h1, h2, h3, h4, h5, h6, [data-testid="stHeader"] {
                font-family: 'Space Grotesk', sans-serif !important;
                font-weight: 700 !important;
                letter-spacing: -0.03em !important;
                color: #FFFFFF !important;
            }

            p, li, label, span {
                color: #E6EDF3 !important;
            }

            /* Main App Background - Ambient Deep Space */
            .stAppViewContainer {
                background-color: #05070A !important;
                background-image: 
                    radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
                    radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 50%),
                    linear-gradient(rgba(5, 7, 10, 0.98), rgba(5, 7, 10, 0.98)) !important;
                background-attachment: fixed;
            }

            /* Animated Neural Mesh Overlay */
            @keyframes mesh-drift {
                0% { background-position: 0% 0%; }
                100% { background-position: 100% 100%; }
            }

            .stAppViewContainer::before {
                content: "";
                position: fixed;
                top: 0; left: 0; width: 100%; height: 100%;
                background-image: 
                    linear-gradient(rgba(99, 102, 241, 0.03) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(99, 102, 241, 0.03) 1px, transparent 1px);
                background-size: 60px 60px;
                mask-image: radial-gradient(ellipse at center, black, transparent 80%);
                animation: mesh-drift 60s linear infinite;
                pointer-events: none;
                z-index: 0;
            }

            /* Premium Glassmorphism Cards */
            div[data-testid="metric-container"], .stExpander, .element-container div.stMarkdown div.dossier-container {
                background: rgba(13, 17, 23, 0.8) !important;
                backdrop-filter: blur(20px) !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 16px !important;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }

            div[data-testid="metric-container"]:hover {
                transform: translateY(-5px);
                border-color: rgba(99, 102, 241, 0.4) !important;
                box-shadow: 0 15px 50px rgba(99, 102, 241, 0.15) !important;
                background: rgba(22, 27, 34, 0.9) !important;
            }

            /* Metric Styling - Neon Accents */
            [data-testid="stMetricValue"] {
                font-family: 'Space Grotesk', sans-serif !important;
                font-weight: 700 !important;
                color: #FFFFFF !important;
                letter-spacing: -0.02em;
            }

            [data-testid="stMetricLabel"] {
                color: #8B949E !important;
                font-family: 'Space Grotesk', sans-serif !important;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-size: 0.75rem !important;
                font-weight: 600 !important;
            }

            /* Premium Sidebar Navigation */
            [data-testid="stSidebar"] {
                background-color: #0D1117 !important;
                border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
                box-shadow: 10px 0 50px rgba(0, 0, 0, 0.6) !important;
            }

            [data-testid="stSidebar"] * {
                color: #E6EDF3 !important;
            }

            [data-testid="stSidebarNav"] {
                background: transparent !important;
            }

            /* Radio Buttons (Hub Selector) Styling */
            div[data-testid="stSidebar"] .stRadio > div {
                gap: 8px !important;
            }

            div[data-testid="stSidebar"] .stRadio label {
                background: rgba(255, 255, 255, 0.02) !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
                border-radius: 10px !important;
                padding: 10px 15px !important;
                color: #8B949E !important;
                transition: all 0.3s ease !important;
                cursor: pointer;
            }

            div[data-testid="stSidebar"] .stRadio label:hover {
                background: rgba(99, 102, 241, 0.05) !important;
                border-color: rgba(99, 102, 241, 0.3) !important;
                color: #E6EDF3 !important;
            }

            div[data-testid="stSidebar"] .stRadio label[data-selected="true"] {
                background: linear-gradient(90deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.1)) !important;
                border-color: #6366F1 !important;
                color: #FFFFFF !important;
                box-shadow: 0 0 20px rgba(99, 102, 241, 0.1) !important;
                font-weight: 600 !important;
            }

            /* Buttons - The Final Polish */
            .stButton > button {
                background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%) !important;
                color: #FFFFFF !important;
                border: 1px solid rgba(99, 102, 241, 0.3) !important;
                border-radius: 12px !important;
                padding: 0.6rem 1.8rem !important;
                font-family: 'Space Grotesk', sans-serif !important;
                font-weight: 600 !important;
                letter-spacing: 0.02em !important;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            }

            .stButton > button:hover {
                background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%) !important;
                border-color: #6366F1 !important;
                box-shadow: 0 0 30px rgba(99, 102, 241, 0.3) !important;
                transform: translateY(-2px);
            }

            .stButton > button:active {
                transform: scale(0.98);
            }

            /* Neural Pulse Animation */
            @keyframes neural-pulse {
                0% { transform: scale(0.95); opacity: 0.4; filter: blur(1px); }
                50% { transform: scale(1.1); opacity: 1; filter: blur(0px); box-shadow: 0 0 15px #6366F1; }
                100% { transform: scale(0.95); opacity: 0.4; filter: blur(1px); }
            }

            .status-pulse {
                display: inline-block;
                width: 8px;
                height: 8px;
                background-color: #6366F1;
                border-radius: 50%;
                margin-right: 12px;
                animation: neural-pulse 3s infinite ease-in-out;
            }

            /* Enhanced Dossier View */
            .dossier-container {
                position: relative;
                overflow: hidden;
                background: rgba(13, 17, 23, 0.9) !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
                padding: 2.5rem !important;
                border-radius: 16px !important;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8) !important;
            }

            .dossier-container::before {
                content: "";
                position: absolute;
                top: 0; left: 0; width: 100%; height: 100%;
                background: repeating-linear-gradient(0deg, transparent, transparent 1px, rgba(99, 102, 241, 0.03) 1px, rgba(99, 102, 241, 0.03) 2px);
                pointer-events: none;
            }

            /* Scrollbar Style */
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-track { background: #05070A; }
            ::-webkit-scrollbar-thumb { background: #161B22; border-radius: 10px; border: 2px solid #05070A; }
            ::-webkit-scrollbar-thumb:hover { background: #6366F1; }
        </style>
    """, unsafe_allow_html=True)

def style_obsidian_chart(fig):
    """
    Applies 'The Obsidian Command' aesthetics to Plotly figures.
    Optimized for high-contrast readability on dark backgrounds.
    """
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#E6EDF3", size=12),
        title_font=dict(family="Space Grotesk, sans-serif", size=20, color="#FFFFFF"),
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(13, 17, 23, 0.9)",
            font_size=13,
            font_family="Inter, sans-serif"
        ),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.08)',
            zerolinecolor='rgba(255,255,255,0.15)',
            tickfont=dict(size=11, color="#8B949E"),
            showgrid=True,
            linecolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.08)',
            zerolinecolor='rgba(255,255,255,0.15)',
            tickfont=dict(size=11, color="#8B949E"),
            showgrid=True,
            linecolor='rgba(255,255,255,0.1)'
        ),
        legend=dict(
            bgcolor='rgba(13, 17, 23, 0.6)',
            bordercolor='rgba(255,255,255,0.1)',
            borderwidth=1,
            font=dict(size=11, color="#E6EDF3")
        )
    )
    
    # Add subtle glow to lines if it's a scatter/line chart
    fig.update_traces(hoverlabel=dict(namelength=-1))
    
    # connectgaps is only valid for certain trace types (scatter, heatmap, etc.)
    # Using a selector to avoid errors on trace types like 'pie'
    fig.update_traces(
        connectgaps=True,
        selector=dict(type='scatter')
    )
    fig.update_traces(
        connectgaps=True,
        selector=dict(type='scatterpolar')
    )
    
    return fig

def render_dossier_block(content, title="SECURE DATA DOSSIER"):
    """
    Renders a content block with the 'Dossier' scanline effect.
    """
    st.markdown(f"""
        <div class="dossier-container">
            <div class="scanline-overlay"></div>
            <div style="font-family: 'Space Grotesk', sans-serif; font-size: 0.7rem; color: #6366F1; letter-spacing: 0.2em; margin-bottom: 1rem; font-weight: 700;">
                // {title}
            </div>
            <div style="font-family: 'Inter', sans-serif; font-size: 0.95rem; line-height: 1.6; color: #E6EDF3;">
                {content}
            </div>
        </div>
    """, unsafe_allow_html=True)
