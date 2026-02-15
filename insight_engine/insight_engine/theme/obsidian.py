"""
Obsidian Command v2.0 - Premium dark theme CSS and Plotly styling.
SaaS-Noir aesthetics with glassmorphism and custom typography.
"""

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

            .stAppViewContainer {
                background-color: var(--obsidian-deep) !important;
                background-image:
                    radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(0, 229, 255, 0.08) 0%, transparent 40%),
                    linear-gradient(rgba(5, 7, 10, 0.98), rgba(5, 7, 10, 0.98)) !important;
                background-attachment: fixed;
            }

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

            @media (max-width: 768px) {
                .stMetric { padding: 0.5rem !important; }
                h1 { font-size: 1.8rem !important; }
                .elite-card { padding: 1rem !important; margin-bottom: 1rem !important; }
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

    for trace in fig.data:
        if hasattr(trace, "hoverlabel"):
            trace.update(hoverlabel=dict(namelength=-1))

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


def render_dossier_block(content, title="SECURE DATA DOSSIER"):
    """Renders a content block with the 'Dossier' scanline effect and glassmorphism."""
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
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_voice_waveform():
    """Renders the kinetic CSS-animated SVG waveform."""
    bars = "".join([f'<div class="waveform-bar" style="animation-delay: {i * 0.1}s"></div>' for i in range(20)])
    st.markdown(f'<div class="waveform-container">{bars}</div>', unsafe_allow_html=True)


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
                BIOMETRIC_SYNC // {urgency.upper()}
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


def render_countdown_gauge(days_remaining, total_days=30):
    """Predictive 'Time-to-Close' circular gauge."""
    import math
    percentage = max(0, min(100, (days_remaining / total_days) * 100))
    circumference = 2 * math.pi * 45
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
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
                    <div style="font-family: 'Space Grotesk'; font-size: 1.5rem; font-weight: 700; color: white;">{days_remaining}</div>
                    <div style="font-family: 'Inter'; font-size: 0.5rem; color: var(--text-secondary); text-transform: uppercase;">Days</div>
                </div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_decision_stream(decisions):
    """Global Decision Stream log - logs not just what, but WHY."""
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
                // GLOBAL_DECISION_STREAM
            </div>
            {items_html}
        </div>
    """,
        unsafe_allow_html=True,
    )
