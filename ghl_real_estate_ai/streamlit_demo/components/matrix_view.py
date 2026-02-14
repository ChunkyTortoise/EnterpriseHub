
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_matrix_view():
    """
    Renders the 'Matrix' 3D Heatmap of Jorge's pipeline.
    Visualizes lead quality as 'Height' and urgency as 'Color Intensity'.
    """
    st.markdown("### 🧬 The Matrix: 3D Pipeline Intelligence")
    st.markdown("*Real-time holographic visualization of lead quality, urgency, and geographical clusters.*")

    # Generate Mock Data for Rancho Cucamonga Market
    num_leads = 40
    np.random.seed(42)

    # Coordinates (Approx Rancho Cucamonga area)
    lat = np.random.uniform(30.2, 30.4, num_leads)
    lon = np.random.uniform(-97.8, -97.6, num_leads)

    # Lead Metrics
    # Quality (Height) 0-100
    quality = np.random.randint(10, 100, num_leads)
    # Urgency (Color Intensity) 0-100
    urgency = np.random.randint(5, 100, num_leads)
    # Deal Size (Size of point)
    deal_size = np.random.randint(250000, 1500000, num_leads)

    names = [f"Lead #{i:03d}" for i in range(num_leads)]

    df = pd.DataFrame(
        {
            "name": names,
            "lat": lat,
            "lon": lon,
            "quality": quality,
            "urgency": urgency,
            "deal_size": deal_size,
            "size_norm": deal_size / 20000,  # For visualization
        }
    )

    # Create 3D Scatter Plot
    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=df["lon"],
                y=df["lat"],
                z=df["quality"],
                mode="markers",
                text=df["name"],
                marker=dict(
                    size=df["size_norm"],
                    color=df["urgency"],  # set color to urgency
                    colorscale="Viridis",  # one of plotly colorscales
                    opacity=0.8,
                    colorbar=dict(title="Urgency Index"),
                    line=dict(width=0.5, color="white"),
                ),
            )
        ]
    )

    # Add 'Matrix' floor grid
    fig.add_trace(
        go.Surface(
            x=np.linspace(-97.8, -97.6, 10),
            y=np.linspace(30.2, 30.4, 10),
            z=np.zeros((10, 10)),
            showscale=False,
            opacity=0.1,
            colorscale=[[0, "#6366F1"], [1, "#6366F1"]],
        )
    )

    fig.update_layout(
        title="3D Lead Intensity Map (Rancho Cucamonga Metro)",
        scene=dict(
            xaxis_title="Longitude",
            yaxis_title="Latitude",
            zaxis_title="Lead Quality Score",
            xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.05)"),
            zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,0.05)"),
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=700,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Matrix Insights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🧬 Cluster Density", "High (West Rancho Cucamonga)", delta="+14%")
    with col2:
        st.metric("🔥 Avg Urgency", "72/100", delta="Strategic Shift")
    with col3:
        st.metric("💎 High-Value Nodes", "8 detected", delta="Focus Area")
