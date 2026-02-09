from datetime import datetime

import streamlit as st


def inject_elite_css():
    """
    Injects 'The Obsidian Command v2.0' Visual Overhaul CSS.
    Implements SaaS-Noir aesthetics, Glassmorphism, and custom typography.
    Includes Font Awesome 6.5.1 and custom SVG icon support.
    """
    st.markdown(
        """
        <!-- Font Awesome 6.5.1 -->
        <link rel="stylesheet"
              href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
              integrity="sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA=="
              crossorigin="anonymous"
              referrerpolicy="no-referrer" />

        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@300;500;700&family=JetBrains+Mono:wght@400;700&display=swap');

            /* Global Typography */
            :root {
                --obsidian-deep: #05070A;
                --obsidian-card: rgba(13, 17, 23, 0.7);
                --obsidian-border: rgba(255, 255, 255, 0.08);
                --elite-accent: #6366F1;
                --negotiation-neon: #00E5FF;
                --text-primary: #FFFFFF;
                --text-secondary: #8B949E;
                --glass-blur: blur(20px);
                --pivot-warning: #FF3D00;
            }

            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
                color: var(--text-secondary) !important;
            }

            h1, h2, h3, h4, h5, h6, [data-testid="stHeader"] {
                font-family: 'Space Grotesk', sans-serif !important;
                font-weight: 700 !important;
                letter-spacing: -0.04em !important;
                color: var(--text-primary) !important;
                text-transform: uppercase;
            }

            /* Main App Background - Ambient Deep Space */
            .stAppViewContainer {
                background-color: var(--obsidian-deep) !important;
                background-image: 
                    radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(0, 229, 255, 0.08) 0%, transparent 40%),
                    linear-gradient(rgba(5, 7, 10, 0.98), rgba(5, 7, 10, 0.98)) !important;
                background-attachment: fixed;
            }

            /* Premium Glassmorphism Cards */
            div[data-testid="stVerticalBlock"] > div[style*="background-color: rgba(0, 0, 0, 0)"] > div,
            div[data-testid="metric-container"], 
            .stExpander, 
            .dossier-container,
            .elite-card {
                background: var(--obsidian-card) !important;
                backdrop-filter: var(--glass-blur) !important;
                -webkit-backdrop-filter: var(--glass-blur) !important;
                border: 0.5px solid var(--obsidian-border) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.12) !important;
                border-radius: 16px !important;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6) !important;
                transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
                overflow: hidden;
            }

            .elite-card:hover {
                transform: translateY(-5px);
                border-color: rgba(99, 102, 241, 0.4) !important;
                box-shadow: 0 25px 60px rgba(99, 102, 241, 0.15) !important;
                background: rgba(22, 27, 34, 0.85) !important;
            }

            /* Custom Progress Bars with Glow */
            .neural-progress-container {
                width: 100%;
                height: 8px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
                margin: 8px 0;
                overflow: hidden;
                position: relative;
            }

            .neural-progress-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--elite-accent), var(--negotiation-neon));
                box-shadow: 0 0 15px var(--elite-accent);
                border-radius: 4px;
                transition: width 1s ease-in-out;
            }

            /* Negotiation Intensity Indicator */
            .intensity-bar {
                display: flex;
                gap: 4px;
                margin-top: 10px;
            }

            .intensity-segment {
                flex: 1;
                height: 6px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
            }

            .intensity-segment.active.low { background: #10b981; box-shadow: 0 0 10px #10b981; }
            .intensity-segment.active.med { background: #f59e0b; box-shadow: 0 0 10px #f59e0b; }
            .intensity-segment.active.high { background: #ef4444; box-shadow: 0 0 10px #ef4444; }
            .intensity-segment.active.neon { background: var(--negotiation-neon); box-shadow: 0 0 10px var(--negotiation-neon); }

            /* Animated Transitions */
            .stTabs [data-baseweb="tab-list"] {
                gap: 24px;
                background-color: transparent !important;
            }

            .stTabs [data-baseweb="tab"] {
                height: 50px !important;
                background-color: transparent !important;
                border-radius: 0px !important;
                border: none !important;
                color: var(--text-secondary) !important;
                font-family: 'Space Grotesk', sans-serif !important;
                font-weight: 500 !important;
                transition: all 0.3s ease !important;
            }

            .stTabs [data-baseweb="tab"]:hover {
                color: var(--text-primary) !important;
            }

            .stTabs [aria-selected="true"] {
                color: var(--elite-accent) !important;
                border-bottom: 2px solid var(--elite-accent) !important;
            }

            /* Dossier Sparkline Container */
            .sparkline-container {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-top: 5px;
            }

            /* SVG Icon Styles */
            .elite-icon {
                width: 24px;
                height: 24px;
                fill: var(--elite-accent);
                filter: drop-shadow(0 0 5px var(--elite-accent));
            }

            .neon-icon {
                width: 24px;
                height: 24px;
                fill: var(--negotiation-neon);
                filter: drop-shadow(0 0 5px var(--negotiation-neon));
            }

            /* --- Phase 4: Swarm Sovereign Orchestration --- */

            /* Handoff Pulse Animation */
            .handoff-pulse-active {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 100vw;
                height: 100vh;
                background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
                pointer-events: none;
                z-index: 999998;
                animation: handoff-glow 2s ease-out forwards;
            }

            @keyframes handoff-glow {
                0% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); }
                30% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
                100% { opacity: 0; transform: translate(-50%, -50%) scale(1.5); }
            }

            /* Strategy Pivot Warning */
            .pivot-warning-card {
                border-left: 4px solid var(--pivot-warning) !important;
                background: rgba(255, 61, 0, 0.05) !important;
                animation: pivot-shimmer 2s infinite;
            }

            @keyframes pivot-shimmer {
                0% { border-left-color: var(--pivot-warning); box-shadow: 0 0 5px rgba(255, 61, 0, 0.2); }
                50% { border-left-color: #FF8A65; box-shadow: 0 0 15px rgba(255, 61, 0, 0.4); }
                100% { border-left-color: var(--pivot-warning); box-shadow: 0 0 5px rgba(255, 61, 0, 0.2); }
            }

            /* Global Decision Stream */
            .decision-stream-container {
                background: rgba(5, 7, 10, 0.8);
                border-top: 1px solid var(--obsidian-border);
                padding: 1rem;
                font-family: 'JetBrains Mono', monospace;
                max-height: 150px;
                overflow-y: auto;
            }

            .decision-item {
                display: flex;
                gap: 15px;
                padding: 5px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.03);
                font-size: 0.75rem;
            }

            .decision-why { color: var(--negotiation-neon); font-style: italic; }
            .decision-action { color: var(--elite-accent); font-weight: bold; }

            /* --- Phase 3: Strategic Foresight UI --- */

            /* Neural Heatmap Radar Sweep */
            .radar-container {
                position: relative;
                width: 300px;
                height: 300px;
                margin: 0 auto;
                background: radial-gradient(circle, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
                border-radius: 50%;
                border: 1px solid rgba(255, 255, 255, 0.05);
                overflow: hidden;
            }

            .radar-sweep {
                position: absolute;
                top: 50%;
                left: 50%;
                width: 50%;
                height: 50%;
                background: conic-gradient(from 0deg, var(--elite-accent) 0%, transparent 40%);
                transform-origin: top left;
                animation: radar-rotate 4s linear infinite;
                opacity: 0.3;
                filter: blur(5px);
            }

            @keyframes radar-rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }

            .heatmap-point {
                position: absolute;
                width: 8px;
                height: 8px;
                background: var(--negotiation-neon);
                border-radius: 50%;
                box-shadow: 0 0 15px var(--negotiation-neon);
                animation: pulse-point 2s infinite;
            }

            @keyframes pulse-point {
                0%, 100% { transform: scale(1); opacity: 0.6; }
                50% { transform: scale(1.5); opacity: 1; }
            }

            /* Biometric Heartbeat EKG */
            .heartbeat-container {
                height: 40px;
                width: 100%;
                background: rgba(0, 0, 0, 0.2);
                overflow: hidden;
                position: relative;
                border-radius: 4px;
            }

            .heartbeat-path {
                stroke: var(--negotiation-neon);
                stroke-width: 2;
                fill: none;
                stroke-dasharray: 1000;
                stroke-dashoffset: 1000;
                animation: heartbeat-dash 2s linear infinite;
                filter: drop-shadow(0 0 5px var(--negotiation-neon));
            }

            @keyframes heartbeat-dash {
                to { stroke-dashoffset: 0; }
            }

            /* Swarm Communication Pulse */
            .swarm-sync-animation {
                animation: swarm-pulse 1.5s ease-in-out;
            }

            @keyframes swarm-pulse {
                0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.7); }
                70% { box-shadow: 0 0 0 20px rgba(99, 102, 241, 0); }
                100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
            }

            /* The Data Moat Hex Grid */
            .moat-overlay {
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                background-image: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iMzQuNjQiIHZpZXdCb3g9IjAgMCA0MCAzNC42NCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAgMEwyMCAxNy4zMkwxMCAzNC42NEwwIDE3LjMyTDEwIDBaIiBmaWxsPSJub25lIiBzdHJva2U9InJnYmEoOTksIDEwMiwgMjQxLCAwLjE1KSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9zdmc+');
                background-size: 40px 34.64px;
                pointer-events: none;
                z-index: 1;
                transition: all 0.5s ease;
            }

            .moat-active {
                background-image: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iMzQuNjQiIHZpZXdCb3g9IjAgMCA0MCAzNC42NCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAgMEwyMCAxNy4zMkwxMCAzNC42NEwwIDE3LjMyTDEwIDBaIiBmaWxsPSJub25lIiBzdHJva2U9InJnYmEoMCwgMjI5LCAyNTUsIDAuMykiIHN0cm9rZS13aWR0aD0iMSIvPjwvc3ZnPg==');
                filter: drop-shadow(0 0 5px rgba(0, 229, 255, 0.2));
            }

            /* --- Phase 2: Tactical UI Components --- */

            /* Neural Uplink Terminal */
            .terminal-window {
                background: rgba(5, 7, 10, 0.95) !important;
                border: 1px solid var(--obsidian-border) !important;
                border-top: 2px solid var(--negotiation-neon) !important;
                border-radius: 8px;
                padding: 1.5rem;
                font-family: 'JetBrains Mono', monospace !important;
                font-size: 0.85rem;
                color: var(--negotiation-neon);
                height: 220px;
                overflow-y: auto;
                position: relative;
                box-shadow: inset 0 0 30px rgba(0, 229, 255, 0.05), 0 10px 40px rgba(0,0,0,0.8);
                margin-top: 2rem;
            }

            .terminal-line {
                margin-bottom: 8px;
                line-height: 1.5;
                white-space: pre-wrap;
                opacity: 0.9;
                border-left: 2px solid transparent;
                padding-left: 10px;
                transition: all 0.3s;
            }

            .terminal-line:hover {
                background: rgba(0, 229, 255, 0.05);
                border-left: 2px solid var(--negotiation-neon);
                opacity: 1;
            }

            .terminal-prefix { color: var(--elite-accent); font-weight: bold; }
            .terminal-timestamp { color: var(--text-secondary); font-size: 0.75rem; margin-right: 10px; }

            /* Kinetic Voice Waveform */
            .waveform-container {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 4px;
                height: 60px;
                padding: 10px;
                background: rgba(255, 255, 255, 0.02);
                border-radius: 12px;
                border: 1px solid var(--obsidian-border);
            }

            .waveform-bar {
                width: 4px;
                height: 20%;
                background: var(--negotiation-neon);
                border-radius: 2px;
                animation: waveform-pulse 1.2s ease-in-out infinite;
                box-shadow: 0 0 10px var(--negotiation-neon);
            }

            @keyframes waveform-pulse {
                0%, 100% { height: 20%; opacity: 0.4; }
                50% { height: 80%; opacity: 1; filter: brightness(1.2); }
            }

            /* Holographic Property Dossier */
            .holographic-card {
                position: relative;
                background: var(--obsidian-card) !important;
                border: 1px solid var(--obsidian-border) !important;
                border-radius: 16px !important;
                overflow: hidden;
                transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
            }

            .holographic-card::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                background-image: 
                    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
                background-size: 24px 24px;
                z-index: 0;
                pointer-events: none;
            }

            .holographic-card::after {
                content: '';
                position: absolute;
                top: -100%; left: -100%; width: 300%; height: 300%;
                background: linear-gradient(
                    45deg,
                    transparent 0%,
                    rgba(255, 255, 255, 0) 45%,
                    rgba(255, 255, 255, 0.08) 50%,
                    rgba(255, 255, 255, 0) 55%,
                    transparent 100%
                );
                transform: rotate(45deg);
                transition: all 0.8s ease-in-out;
                z-index: 1;
                pointer-events: none;
            }

            .holographic-card:hover {
                transform: translateY(-8px) scale(1.02);
                border-color: var(--negotiation-neon) !important;
                box-shadow: 0 30px 60px rgba(0, 229, 255, 0.15) !important;
            }

            .holographic-card:hover::after {
                transform: translate(30%, 30%) rotate(45deg);
            }

            /* Tactical Command Dock */
            .tactical-dock {
                position: fixed;
                bottom: 25px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(13, 17, 23, 0.85);
                backdrop-filter: blur(15px);
                -webkit-backdrop-filter: blur(15px);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-top: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 50px;
                padding: 12px 35px;
                display: flex;
                gap: 25px;
                z-index: 999999;
                box-shadow: 0 15px 50px rgba(0, 0, 0, 0.8), 0 0 20px rgba(99, 102, 241, 0.2);
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }

            .tactical-dock:hover {
                bottom: 30px;
                border-color: var(--elite-accent);
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.9), 0 0 30px rgba(99, 102, 241, 0.3);
            }

            .dock-item {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 5px;
                color: var(--text-secondary);
                text-decoration: none;
                transition: all 0.3s;
                cursor: pointer;
            }

            .dock-item:hover {
                color: var(--text-primary);
                transform: scale(1.1);
            }

            .dock-item i { font-size: 1.2rem; }
            .dock-item span { font-size: 0.65rem; font-family: 'Space Grotesk', sans-serif; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }

            /* Journey Glow Mapping */
            .journey-line-container {
                width: 100%;
                height: 6px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 3px;
                overflow: hidden;
                position: relative;
            }

            .journey-line-glow {
                height: 100%;
                border-radius: 3px;
                transition: all 1.5s cubic-bezier(0.4, 0, 0.2, 1);
            }

            .glow-cold { background: #3B82F6; box-shadow: 0 0 10px #3B82F6; }
            .glow-warm { background: var(--elite-accent); box-shadow: 0 0 15px var(--elite-accent); animation: glow-pulse 2s infinite; }
            .glow-hot { background: #F43F5E; box-shadow: 0 0 20px #F43F5E; animation: glow-pulse 0.8s infinite; }

            @keyframes glow-pulse {
                0%, 100% { opacity: 0.8; filter: brightness(1); }
                50% { opacity: 1; filter: brightness(1.4); }
            }

            /* --- Mobile Responsiveness --- */
            @media (max-width: 768px) {
                .stMetric {
                    padding: 0.5rem !important;
                }
                h1 {
                    font-size: 1.8rem !important;
                }
                .elite-card {
                    padding: 1rem !important;
                    margin-bottom: 1rem !important;
                }
                .tactical-dock {
                    width: 90%;
                    padding: 8px 10px;
                    gap: 10px;
                    bottom: 15px;
                }
                .dock-item span {
                    display: none;
                }
                [data-testid="stSidebar"] {
                    width: 100% !important;
                }
            }
        </style>
    """,
        unsafe_allow_html=True,
    )


def style_obsidian_chart(fig):
    """
    Applies 'The Obsidian Command' aesthetics to Plotly figures.
    Optimized for high-contrast readability on dark backgrounds.
    """
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#E6EDF3", size=12),
        title_font=dict(family="Space Grotesk, sans-serif", size=18, color="#FFFFFF"),
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(13, 17, 23, 0.9)", font_size=13, font_family="Inter, sans-serif"),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            zerolinecolor="rgba(255,255,255,0.1)",
            tickfont=dict(size=11, color="#8B949E"),
            showgrid=True,
            linecolor="rgba(255,255,255,0.08)",
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            zerolinecolor="rgba(255,255,255,0.1)",
            tickfont=dict(size=11, color="#8B949E"),
            showgrid=True,
            linecolor="rgba(255,255,255,0.08)",
        ),
        legend=dict(
            bgcolor="rgba(13, 17, 23, 0.6)",
            bordercolor="rgba(255,255,255,0.08)",
            borderwidth=1,
            font=dict(size=11, color="#E6EDF3"),
        ),
    )

    # Add subtle glow to lines if it's a scatter/line chart
    for trace in fig.data:
        if hasattr(trace, "hoverlabel"):
            trace.update(hoverlabel=dict(namelength=-1))

    # Custom colors for radar charts (Neural Health)
    if any(trace.type == "scatterpolar" for trace in fig.data):
        fig.update_traces(
            fill="toself",
            fillcolor="rgba(99, 102, 241, 0.2)",
            line=dict(color="#6366F1", width=3),
            marker=dict(size=8, color="#00E5FF"),
        )
        fig.update_polars(
            radialaxis=dict(gridcolor="rgba(255,255,255,0.1)", linecolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)", linecolor="rgba(255,255,255,0.1)"),
        )

    return fig


def get_svg_icon(name, color="var(--elite-accent)"):
    """Returns SVG path for high-fidelity icons."""
    icons = {
        "voice": '<svg class="elite-icon" viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>',
        "negotiation": '<svg class="elite-icon" viewBox="0 0 24 24"><path d="M14 6l-3.75 3.75 1.5 1.5L14 9l4.5 4.5-1.5 1.5-4.5-4.5-3.75 3.75L12 18H3l9-9 3-3 6 6-1.5 1.5L14 6z"/></svg>',
        "referral": '<svg class="elite-icon" viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>',
        "intelligence": '<svg class="elite-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>',
    }
    return icons.get(name, "")


def render_dossier_block(content, title="SECURE DATA DOSSIER"):
    """
    Renders a content block with the 'Dossier' scanline effect and glassmorphism.
    """
    st.markdown(
        f"""
        <div class="dossier-container" style="position: relative; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div style="font-family: 'Space Grotesk', sans-serif; font-size: 0.7rem; color: var(--elite-accent); letter-spacing: 0.2em; margin-bottom: 1rem; font-weight: 700;">
                // {title}
            </div>
            <div style="font-family: 'Inter', sans-serif; font-size: 0.9rem; line-height: 1.6; color: #E6EDF3;">
                {content}
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_neural_progress(label, value, color_type="elite"):
    """Renders a custom progress bar with glow effect."""
    color = "var(--elite-accent)" if color_type == "elite" else "var(--negotiation-neon)"
    st.markdown(
        f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px; font-family: 'Space Grotesk', sans-serif;">
                <span>{label}</span>
                <span>{value}%</span>
            </div>
            <div class="neural-progress-container">
                <div class="neural-progress-fill" style="width: {value}%; background: {color}; box-shadow: 0 0 10px {color};"></div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_terminal_log(logs):
    """Renders the Neural Uplink Terminal with typewriter effect simulation."""
    log_html = "".join(
        [
            f'<div class="terminal-line"><span class="terminal-timestamp">[{datetime.now().strftime("%H:%M:%S")}]</span> <span class="terminal-prefix">{log["prefix"]}</span> {log["message"]}</div>'
            for log in logs
        ]
    )

    st.markdown(
        f"""
        <div class="terminal-window">
            <div style="position: sticky; top: 0; background: rgba(5,7,10,0.9); padding-bottom: 10px; margin-bottom: 10px; border-bottom: 1px solid rgba(0,229,255,0.1); font-weight: bold; letter-spacing: 0.1em; font-size: 0.7rem; color: var(--elite-accent);">
                > NEURAL_UPLINK_TERMINAL // SESSION_ACTIVE
            </div>
            {log_html}
            <div class="terminal-line" style="border-right: 2px solid var(--negotiation-neon); width: fit-content; animation: blink 0.5s step-end infinite;">_</div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_voice_waveform():
    """Renders the kinetic CSS-animated SVG waveform."""
    bars = "".join([f'<div class="waveform-bar" style="animation-delay: {i * 0.1}s"></div>' for i in range(20)])
    st.markdown(
        f"""
        <div class="waveform-container">
            {bars}
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_tactical_dock():
    """Renders the floating tactical command dock."""
    st.markdown(
        """
        <div class="tactical-dock">
            <div class="dock-item">
                <i class="fas fa-bolt"></i>
                <span>Force Direct</span>
            </div>
            <div class="dock-item">
                <i class="fas fa-brain"></i>
                <span>Intelligence Export</span>
            </div>
            <div class="dock-item">
                <i class="fas fa-shield-halved"></i>
                <span>Override Mode</span>
            </div>
            <div class="dock-item">
                <i class="fas fa-satellite-dish"></i>
                <span>Swarm Sync</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_journey_line(temperature="warm", progress=65):
    """Renders the kinetic journey line mapping."""
    glow_class = "glow-cold" if temperature == "cold" else "glow-hot" if temperature == "hot" else "glow-warm"
    st.markdown(
        f"""
        <div style="margin: 15px 0;">
            <div style="display: flex; justify-content: space-between; font-size: 0.65rem; margin-bottom: 5px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; color: var(--text-secondary);">
                <span>JOURNEY_PATH</span>
                <span>{temperature.upper()} PHASE</span>
            </div>
            <div class="journey-line-container">
                <div class="journey-line-glow {glow_class}" style="width: {progress}%;"></div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_biometric_heartbeat(urgency="normal"):
    """Renders a pulsing EKG-style biometric heartbeat."""
    speed = "1.5s" if urgency == "normal" else "0.8s" if urgency == "high" else "0.4s"
    st.markdown(
        f"""
        <div style="margin: 15px 0;">
            <div style="font-family: 'Space Grotesk', sans-serif; font-size: 0.65rem; color: var(--text-secondary); font-weight: 700; margin-bottom: 5px; letter-spacing: 0.1em;">
                BIOMETRIC_NEGOTIATION_SYNC // {urgency.upper()}
            </div>
            <div class="heartbeat-container">
                <svg viewBox="0 0 400 40" preserveAspectRatio="none" style="width: 100%; height: 100%;">
                    <path class="heartbeat-path" d="M0 20 L40 20 L50 10 L60 30 L70 20 L110 20 L120 20 L130 5 L140 35 L150 20 L200 20 L240 20 L250 10 L260 30 L270 20 L310 20 L320 20 L330 5 L340 35 L350 20 L400 20" 
                          style="animation-duration: {speed};" />
                </svg>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_neural_heatmap(points=None):
    """Renders a geographic 'Lead Cluster' radar heatmap."""
    if points is None:
        points = [
            {"top": "30%", "left": "40%"},
            {"top": "60%", "left": "70%"},
            {"top": "45%", "left": "25%"},
            {"top": "80%", "left": "50%"},
        ]

    points_html = "".join(
        [f'<div class="heatmap-point" style="top: {p["top"]}; left: {p["left"]};"></div>' for p in points]
    )

    st.markdown(
        f"""
        <div class="radar-container">
            <div class="radar-sweep"></div>
            {points_html}
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: rgba(255,255,255,0.1); font-family: 'Space Grotesk'; font-size: 0.5rem; letter-spacing: 0.5em;">
                SCANNING...
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_moat_overlay(active=False):
    """Renders a hexagonal 'Data Moat' security overlay."""
    active_class = "moat-active" if active else ""
    st.markdown(f'<div class="moat-overlay {active_class}"></div>', unsafe_allow_html=True)


def render_countdown_gauge(days_remaining, total_days=30):
    """
    Phase 4: Predictive 'Time-to-Close' Clock.
    Uses a circular SVG to predict days remaining based on negotiation velocity.
    """
    percentage = max(0, min(100, (days_remaining / total_days) * 100))
    circumference = 2 * 3.14159 * 45
    offset = circumference * (1 - (100 - percentage) / 100)

    color = "var(--negotiation-neon)" if days_remaining < 7 else "var(--elite-accent)"

    st.markdown(
        f"""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1rem;">
            <div style="position: relative; width: 120px; height: 120px;">
                <svg viewBox="0 0 100 100" style="transform: rotate(-90deg); width: 100%; height: 100%;">
                    <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="8" />
                    <circle cx="50" cy="50" r="45" fill="none" stroke="{color}" stroke-width="8" 
                            stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                            style="transition: stroke-dashoffset 1s ease-in-out; filter: drop-shadow(0 0 5px {color});" />
                </svg>
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(0deg); text-align: center;">
                    <div style="font-family: 'Space Grotesk'; font-size: 1.5rem; font-weight: 700; color: white;">{days_remaining}</div>
                    <div style="font-family: 'Inter'; font-size: 0.5rem; color: var(--text-secondary); text-transform: uppercase;">Days</div>
                </div>
            </div>
            <div style="font-family: 'Space Grotesk'; font-size: 0.65rem; color: var(--text-secondary); margin-top: 10px; font-weight: 700; letter-spacing: 0.1em;">
                PREDICTED_TIME_TO_CLOSE
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_decision_stream(decisions):
    """
    Phase 4: Global Decision Stream log.
    Logs not just what, but WHY.
    """
    items_html = "".join(
        [
            f'<div class="decision-item">'
            f'<span style="color: #4B5563;">[{d.get("time", datetime.now().strftime("%H:%M:%S"))}]</span> '
            f'<span class="decision-action">{d["action"]}</span> '
            f'<span class="decision-why">Reason: {d["why"]}</span>'
            f"</div>"
            for d in decisions
        ]
    )

    st.markdown(
        f"""
        <div class="decision-stream-container">
            <div style="font-family: 'Space Grotesk'; font-size: 0.6rem; color: var(--elite-accent); margin-bottom: 8px; font-weight: 700; letter-spacing: 0.2em;">
                // GLOBAL_DECISION_STREAM_V4.2.0
            </div>
            {items_html}
        </div>
    """,
        unsafe_allow_html=True,
    )
