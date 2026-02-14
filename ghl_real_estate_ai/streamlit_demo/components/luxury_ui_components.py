"""
Executive-Level UI/UX Components for Luxury Client Experience
Sophisticated, elegant UI components designed for UHNW clients

This module provides premium UI/UX components that reflect the luxury positioning
and justify premium commission rates through superior client experience.

Features:
- Executive-grade visual design
- Sophisticated data visualization
- White-glove user experience patterns
- Premium styling and typography
- Luxury brand aesthetics
- High-end client interaction patterns
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Union

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


@dataclass
class LuxuryTheme:
    """Luxury UI theme configuration"""

    primary_gold: str = "#D4AF37"  # Luxury gold
    secondary_gold: str = "#FFD700"  # Bright gold
    deep_navy: str = "#1B263B"  # Executive navy
    charcoal: str = "#2D3748"  # Professional charcoal
    pearl_white: str = "#F7FAFC"  # Pearl white
    silver: str = "#C0C5CE"  # Luxury silver
    accent_blue: str = "#4A90E2"  # Sophisticated blue
    success_green: str = "#48BB78"  # Success green
    warning_amber: str = "#ED8936"  # Attention amber


class LuxuryUIComponents:
    """
    Executive-level UI components for luxury client experience

    Provides sophisticated, elegant components that reflect premium
    positioning and enhance UHNW client interactions.
    """

    def __init__(self):
        self.theme = LuxuryTheme()
        self._apply_luxury_styling()

    def _apply_luxury_styling(self):
        """Apply global luxury styling to the Streamlit app"""

        luxury_css = f"""
        <style>
        /* Import Google Fonts for luxury typography */
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global luxury styling */
        .main {{
            background: linear-gradient(135deg, {self.theme.pearl_white} 0%, #FFFFFF 100%);
            font-family: 'Inter', sans-serif;
        }}

        /* Luxury header styling */
        .luxury-header {{
            background: linear-gradient(135deg, {self.theme.deep_navy} 0%, {self.theme.charcoal} 100%);
            color: {self.theme.primary_gold};
            font-family: 'Playfair Display', serif;
            font-weight: 700;
            text-align: center;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}

        /* Executive card styling */
        .executive-card {{
            background: white;
            border: 1px solid {self.theme.silver};
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin: 1rem 0;
            transition: all 0.3s ease;
        }}

        .executive-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.12);
        }}

        /* Premium metric card */
        .premium-metric {{
            background: linear-gradient(135deg, {self.theme.primary_gold} 0%, {self.theme.secondary_gold} 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(212, 175, 55, 0.3);
        }}

        /* Luxury section divider */
        .luxury-divider {{
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, {self.theme.primary_gold} 50%, transparent 100%);
            margin: 2rem 0;
        }}

        /* Executive button styling */
        .stButton > button {{
            background: linear-gradient(135deg, {self.theme.deep_navy} 0%, {self.theme.charcoal} 100%);
            color: {self.theme.primary_gold};
            border: none;
            border-radius: 8px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
        }}

        .stButton > button:hover {{
            background: linear-gradient(135deg, {self.theme.primary_gold} 0%, {self.theme.secondary_gold} 100%);
            color: {self.theme.deep_navy};
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
        }}

        /* Premium data table styling */
        .dataframe {{
            border: none !important;
            border-radius: 8px !important;
            overflow: hidden !important;
        }}

        .dataframe thead {{
            background: {self.theme.deep_navy} !important;
            color: {self.theme.primary_gold} !important;
        }}

        .dataframe tbody tr:nth-child(even) {{
            background-color: {self.theme.pearl_white} !important;
        }}

        /* Luxury sidebar styling */
        .css-1d391kg {{
            background: linear-gradient(180deg, {self.theme.deep_navy} 0%, {self.theme.charcoal} 100%);
        }}

        /* Premium selectbox styling */
        .stSelectbox label {{
            color: {self.theme.deep_navy} !important;
            font-weight: 600 !important;
        }}

        /* Executive typography */
        .luxury-title {{
            font-family: 'Playfair Display', serif;
            font-weight: 700;
            color: {self.theme.deep_navy};
            text-align: center;
            margin: 2rem 0;
        }}

        .executive-subtitle {{
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            color: {self.theme.charcoal};
            margin: 1rem 0;
        }}

        /* White-glove service indicator */
        .white-glove-badge {{
            background: linear-gradient(135deg, {self.theme.primary_gold} 0%, {self.theme.secondary_gold} 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin: 0.5rem;
        }}

        /* Luxury progress indicator */
        .luxury-progress {{
            height: 8px;
            background: {self.theme.silver};
            border-radius: 4px;
            overflow: hidden;
            margin: 1rem 0;
        }}

        .luxury-progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, {self.theme.primary_gold} 0%, {self.theme.secondary_gold} 100%);
            border-radius: 4px;
            transition: width 0.5s ease;
        }}

        /* Executive alert styling */
        .luxury-alert {{
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(255, 215, 0, 0.1) 100%);
            border-left: 4px solid {self.theme.primary_gold};
            padding: 1rem;
            border-radius: 0 8px 8px 0;
            margin: 1rem 0;
        }}
        </style>
        """

        st.markdown(luxury_css, unsafe_allow_html=True)

    def render_luxury_header(self, title: str, subtitle: str = ""):
        """Render luxury application header"""

        header_html = f"""
        <div class="luxury-header">
            <h1 style="margin: 0; font-size: 2.5rem;">{title}</h1>
            {f'<p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">{subtitle}</p>' if subtitle else ""}
        </div>
        """

        st.markdown(header_html, unsafe_allow_html=True)

    def render_executive_metrics_grid(self, metrics: Dict[str, Dict[str, Union[str, float]]]):
        """Render executive-level metrics in luxury grid format"""

        cols = st.columns(len(metrics))

        for i, (metric_name, metric_data) in enumerate(metrics.items()):
            with cols[i]:
                value = metric_data.get("value", "0")
                delta = metric_data.get("delta", "")
                description = metric_data.get("description", "")

                metric_html = f"""
                <div class="executive-card">
                    <div style="text-align: center;">
                        <h3 style="color: {self.theme.deep_navy}; margin: 0; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">{metric_name}</h3>
                        <div style="font-size: 2.5rem; font-weight: 700; color: {self.theme.primary_gold}; margin: 0.5rem 0;">{value}</div>
                        {f'<div style="font-size: 0.9rem; color: {self.theme.success_green}; font-weight: 500;">{delta}</div>' if delta else ""}
                        {f'<div style="font-size: 0.8rem; color: {self.theme.charcoal}; margin-top: 0.5rem;">{description}</div>' if description else ""}
                    </div>
                </div>
                """

                st.markdown(metric_html, unsafe_allow_html=True)

    def render_luxury_divider(self):
        """Render luxury section divider"""
        st.markdown('<div class="luxury-divider"></div>', unsafe_allow_html=True)

    def render_premium_property_card(self, property_data: Dict[str, Any]):
        """Render premium property card with luxury styling"""

        property_html = f"""
        <div class="executive-card" style="background: linear-gradient(135deg, white 0%, {self.theme.pearl_white} 100%);">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                <div>
                    <h3 style="color: {self.theme.deep_navy}; margin: 0; font-family: 'Playfair Display', serif;">{property_data.get("address", "Luxury Property")}</h3>
                    <p style="color: {self.theme.charcoal}; margin: 0.5rem 0; font-weight: 500;">{property_data.get("neighborhood", "Premium Location")}</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.8rem; font-weight: 700; color: {self.theme.primary_gold};">${property_data.get("price", 0):,}</div>
                    <div style="font-size: 0.9rem; color: {self.theme.charcoal};">${property_data.get("price_per_sqft", 0)}/sq ft</div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1rem 0;">
                <div style="text-align: center;">
                    <div style="font-weight: 600; color: {self.theme.deep_navy};">{property_data.get("bedrooms", 0)}</div>
                    <div style="font-size: 0.8rem; color: {self.theme.charcoal};">Bedrooms</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-weight: 600; color: {self.theme.deep_navy};">{property_data.get("bathrooms", 0)}</div>
                    <div style="font-size: 0.8rem; color: {self.theme.charcoal};">Bathrooms</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-weight: 600; color: {self.theme.deep_navy};">{property_data.get("square_feet", 0):,}</div>
                    <div style="font-size: 0.8rem; color: {self.theme.charcoal};">Sq Ft</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-weight: 600; color: {self.theme.deep_navy};">{property_data.get("days_on_market", 0)}</div>
                    <div style="font-size: 0.8rem; color: {self.theme.charcoal};">Days</div>
                </div>
            </div>

            <div style="margin-top: 1rem;">
                <div style="font-size: 0.9rem; font-weight: 600; color: {self.theme.deep_navy}; margin-bottom: 0.5rem;">Luxury Amenities</div>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    {"".join([f'<span style="background: {self.theme.primary_gold}; color: white; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.7rem;">{amenity}</span>' for amenity in property_data.get("amenities", [])[:6]])}
                </div>
            </div>
        </div>
        """

        st.markdown(property_html, unsafe_allow_html=True)

    def render_luxury_progress_indicator(self, label: str, value: float, max_value: float = 100):
        """Render luxury progress indicator"""

        percentage = (value / max_value) * 100

        progress_html = f"""
        <div style="margin: 1rem 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="font-weight: 600; color: {self.theme.deep_navy};">{label}</span>
                <span style="font-weight: 600; color: {self.theme.primary_gold};">{value:.1f}</span>
            </div>
            <div class="luxury-progress">
                <div class="luxury-progress-fill" style="width: {percentage}%;"></div>
            </div>
        </div>
        """

        st.markdown(progress_html, unsafe_allow_html=True)

    def render_white_glove_service_badge(self, service_level: str):
        """Render white-glove service indicator badge"""

        badge_colors = {
            "Standard": (self.theme.silver, self.theme.charcoal),
            "Premium": (self.theme.accent_blue, "white"),
            "White-Glove": (
                f"linear-gradient(135deg, {self.theme.primary_gold} 0%, {self.theme.secondary_gold} 100%)",
                "white",
            ),
            "Concierge": (
                f"linear-gradient(135deg, {self.theme.deep_navy} 0%, {self.theme.primary_gold} 100%)",
                "white",
            ),
        }

        bg_color, text_color = badge_colors.get(service_level, badge_colors["Standard"])

        badge_html = f"""
        <div style="background: {bg_color}; color: {text_color}; padding: 0.5rem 1rem; border-radius: 20px;
                    font-size: 0.8rem; font-weight: 600; display: inline-block; margin: 0.5rem; text-transform: uppercase;
                    letter-spacing: 1px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            ✨ {service_level} Service
        </div>
        """

        st.markdown(badge_html, unsafe_allow_html=True)

    def create_luxury_chart(self, data: pd.DataFrame, chart_type: str = "line", **kwargs) -> go.Figure:
        """Create luxury-styled chart with premium aesthetics"""

        # Common luxury chart styling
        luxury_layout = {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": self.theme.deep_navy},
            "title": {
                "font": {"family": "Playfair Display, serif", "size": 18, "color": self.theme.deep_navy},
                "x": 0.5,
                "xanchor": "center",
            },
            "xaxis": {
                "gridcolor": f"{self.theme.silver}40",
                "linecolor": self.theme.silver,
                "tickcolor": self.theme.silver,
                "title": {"font": {"color": self.theme.charcoal, "weight": 600}},
            },
            "yaxis": {
                "gridcolor": f"{self.theme.silver}40",
                "linecolor": self.theme.silver,
                "tickcolor": self.theme.silver,
                "title": {"font": {"color": self.theme.charcoal, "weight": 600}},
            },
        }

        # Luxury color palette
        luxury_colors = [
            self.theme.primary_gold,
            self.theme.deep_navy,
            self.theme.accent_blue,
            self.theme.success_green,
            self.theme.warning_amber,
        ]

        if chart_type == "line":
            fig = go.Figure()

            for i, column in enumerate(data.columns[1:]):  # Skip first column (assumed to be x-axis)
                fig.add_trace(
                    go.Scatter(
                        x=data.iloc[:, 0],
                        y=data[column],
                        name=column,
                        line=dict(color=luxury_colors[i % len(luxury_colors)], width=3),
                        mode="lines+markers",
                        marker=dict(size=6, color=luxury_colors[i % len(luxury_colors)]),
                    )
                )

        elif chart_type == "bar":
            fig = go.Figure()

            for i, column in enumerate(data.columns[1:]):
                fig.add_trace(
                    go.Bar(
                        x=data.iloc[:, 0],
                        y=data[column],
                        name=column,
                        marker_color=luxury_colors[i % len(luxury_colors)],
                        marker_line=dict(width=0),
                    )
                )

        elif chart_type == "pie":
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=data.iloc[:, 0],
                        values=data.iloc[:, 1],
                        marker_colors=luxury_colors,
                        hole=0.4,
                        textinfo="label+percent",
                        textfont_size=12,
                    )
                ]
            )

        # Apply luxury styling
        fig.update_layout(**luxury_layout)

        # Add subtle shadow effect
        fig.update_layout(
            margin=dict(l=40, r=40, t=60, b=40),
            showlegend=True,
            legend=dict(
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor=self.theme.silver,
                borderwidth=1,
                font=dict(color=self.theme.deep_navy),
            ),
        )

        return fig

    def render_luxury_data_table(self, data: pd.DataFrame, title: str = ""):
        """Render luxury-styled data table"""

        if title:
            st.markdown(f'<h3 class="executive-subtitle">{title}</h3>', unsafe_allow_html=True)

        # Apply luxury styling to dataframe
        styled_df = data.style.set_table_styles(
            [
                {
                    "selector": "thead th",
                    "props": [
                        ("background-color", self.theme.deep_navy),
                        ("color", self.theme.primary_gold),
                        ("font-weight", "600"),
                        ("text-align", "center"),
                        ("border", "none"),
                    ],
                },
                {
                    "selector": "tbody td",
                    "props": [("text-align", "center"), ("padding", "12px"), ("border", "1px solid #e2e8f0")],
                },
                {"selector": "tbody tr:nth-child(even)", "props": [("background-color", self.theme.pearl_white)]},
                {
                    "selector": "",
                    "props": [("border-radius", "8px"), ("overflow", "hidden"), ("border-collapse", "separate")],
                },
            ]
        )

        st.dataframe(styled_df, use_container_width=True)

    def render_executive_alert(self, message: str, alert_type: str = "info"):
        """Render executive-style alert"""

        alert_configs = {
            "info": (self.theme.accent_blue, "ℹ️"),
            "success": (self.theme.success_green, "✅"),
            "warning": (self.theme.warning_amber, "⚠️"),
            "luxury": (self.theme.primary_gold, "💎"),
        }

        border_color, icon = alert_configs.get(alert_type, alert_configs["info"])

        alert_html = f"""
        <div style="background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, {self.theme.pearl_white} 100%);
                    border-left: 4px solid {border_color}; padding: 1rem; border-radius: 0 8px 8px 0;
                    margin: 1rem 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.2rem;">{icon}</span>
                <span style="color: {self.theme.deep_navy}; font-weight: 500;">{message}</span>
            </div>
        </div>
        """

        st.markdown(alert_html, unsafe_allow_html=True)

    def render_luxury_client_card(self, client_data: Dict[str, Any]):
        """Render luxury client profile card"""

        client_html = f"""
        <div class="executive-card" style="background: linear-gradient(135deg, white 0%, {self.theme.pearl_white} 100%);
                                          border: 2px solid {self.theme.primary_gold}20;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h3 style="color: {self.theme.deep_navy}; margin: 0; font-family: 'Playfair Display', serif; font-size: 1.4rem;">
                        {client_data.get("name", "UHNW Client")}
                    </h3>
                    <p style="color: {self.theme.charcoal}; margin: 0.5rem 0; font-weight: 500;">
                        Net Worth: ${client_data.get("net_worth", 0):,}
                    </p>
                </div>
                <div style="text-align: right;">
                    {f'<div class="white-glove-badge">{client_data.get("service_level", "Premium")}</div>' if client_data.get("service_level") else ""}
                </div>
            </div>

            <div style="margin: 1.5rem 0;">
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                    <div style="text-align: center; padding: 1rem; background: {self.theme.pearl_white}; border-radius: 8px;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: {self.theme.primary_gold};">
                            {client_data.get("satisfaction_score", 0):.1f}%
                        </div>
                        <div style="font-size: 0.8rem; color: {self.theme.charcoal}; text-transform: uppercase; letter-spacing: 1px;">
                            Satisfaction
                        </div>
                    </div>
                    <div style="text-align: center; padding: 1rem; background: {self.theme.pearl_white}; border-radius: 8px;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: {self.theme.success_green};">
                            ${client_data.get("portfolio_value", 0):,.0f}
                        </div>
                        <div style="font-size: 0.8rem; color: {self.theme.charcoal}; text-transform: uppercase; letter-spacing: 1px;">
                            Portfolio Value
                        </div>
                    </div>
                    <div style="text-align: center; padding: 1rem; background: {self.theme.pearl_white}; border-radius: 8px;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: {self.theme.accent_blue};">
                            {client_data.get("referrals_given", 0)}
                        </div>
                        <div style="font-size: 0.8rem; color: {self.theme.charcoal}; text-transform: uppercase; letter-spacing: 1px;">
                            Referrals
                        </div>
                    </div>
                </div>
            </div>

            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid {self.theme.silver};">
                <div style="font-size: 0.9rem; font-weight: 600; color: {self.theme.deep_navy}; margin-bottom: 0.5rem;">
                    Preferred Locations
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    {"".join([f'<span style="background: {self.theme.deep_navy}; color: {self.theme.primary_gold}; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.7rem;">{location}</span>' for location in client_data.get("preferred_locations", [])[:4]])}
                </div>
            </div>
        </div>
        """

        st.markdown(client_html, unsafe_allow_html=True)

    def render_luxury_stats_grid(self, stats: Dict[str, Dict[str, Any]], columns: int = 3):
        """Render luxury statistics in grid format"""

        stats_items = list(stats.items())
        rows = [stats_items[i : i + columns] for i in range(0, len(stats_items), columns)]

        for row in rows:
            cols = st.columns(len(row))

            for i, (stat_name, stat_data) in enumerate(row):
                with cols[i]:
                    value = stat_data.get("value", "0")
                    trend = stat_data.get("trend", "")
                    icon = stat_data.get("icon", "📊")

                    stat_html = f"""
                    <div class="executive-card" style="text-align: center; min-height: 150px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                        <div style="font-size: 2rem; font-weight: 700; color: {self.theme.primary_gold}; margin-bottom: 0.5rem;">
                            {value}
                        </div>
                        <div style="font-size: 0.9rem; font-weight: 600; color: {self.theme.deep_navy}; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">
                            {stat_name}
                        </div>
                        {f'<div style="font-size: 0.8rem; color: {self.theme.success_green}; font-weight: 500;">{trend}</div>' if trend else ""}
                    </div>
                    """

                    st.markdown(stat_html, unsafe_allow_html=True)

    def render_premium_feature_showcase(self, features: List[Dict[str, str]]):
        """Render premium feature showcase"""

        showcase_html = f"""
        <div class="executive-card" style="background: linear-gradient(135deg, {self.theme.deep_navy} 0%, {self.theme.charcoal} 100%); color: white;">
            <h3 style="color: {self.theme.primary_gold}; text-align: center; font-family: 'Playfair Display', serif; margin-bottom: 2rem;">
                Premium Platform Features
            </h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem;">
        """

        for feature in features:
            showcase_html += f"""
            <div style="padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 8px;
                        border-left: 4px solid {self.theme.primary_gold};">
                <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">{feature.get("icon", "⚡")}</div>
                <div style="font-weight: 600; color: {self.theme.primary_gold}; margin-bottom: 0.5rem;">
                    {feature.get("title", "Premium Feature")}
                </div>
                <div style="font-size: 0.9rem; opacity: 0.9;">
                    {feature.get("description", "Advanced functionality for luxury clients")}
                </div>
            </div>
            """

        showcase_html += """
            </div>
        </div>
        """

        st.markdown(showcase_html, unsafe_allow_html=True)

    def render_luxury_footer(self):
        """Render luxury application footer"""

        footer_html = f"""
        <div style="margin-top: 4rem; padding: 2rem; text-align: center;
                    background: linear-gradient(135deg, {self.theme.pearl_white} 0%, white 100%);
                    border-top: 2px solid {self.theme.primary_gold}20;">
            <div style="color: {self.theme.deep_navy}; font-family: 'Playfair Display', serif; font-size: 1.2rem; margin-bottom: 0.5rem;">
                Jorge's Premium Real Estate Technology Platform
            </div>
            <div style="color: {self.theme.charcoal}; font-size: 0.9rem;">
                Transforming luxury real estate through AI-enhanced service delivery
            </div>
            <div style="margin-top: 1rem;">
                <span class="white-glove-badge">✨ White-Glove Service Excellence</span>
                <span class="white-glove-badge">🤖 AI-Powered Intelligence</span>
                <span class="white-glove-badge">💎 UHNW Specialist</span>
            </div>
        </div>
        """

        st.markdown(footer_html, unsafe_allow_html=True)


# Example usage and demo functions


def demo_luxury_components():
    """Demonstrate luxury UI components"""

    # Initialize luxury components
    luxury_ui = LuxuryUIComponents()

    # Luxury header
    luxury_ui.render_luxury_header(
        "Jorge's Elite Real Estate Intelligence", "Premium Platform for Ultra-High-Net-Worth Clients"
    )

    # Executive metrics
    executive_metrics = {
        "Total Portfolio": {"value": "$47.2M", "delta": "+$12.3M YTD", "description": "UHNW Client Assets"},
        "Client Satisfaction": {"value": "96.8%", "delta": "+2.1% vs Q3", "description": "White-Glove Service"},
        "Commission Rate": {"value": "3.8%", "delta": "+0.9% Premium", "description": "Above Market Rate"},
        "Referral Rate": {"value": "73%", "delta": "Industry Leading", "description": "Client Referrals"},
    }

    luxury_ui.render_executive_metrics_grid(executive_metrics)

    luxury_ui.render_luxury_divider()

    # Premium property showcase
    st.markdown('<h2 class="luxury-title">Featured Luxury Properties</h2>', unsafe_allow_html=True)

    sample_properties = [
        {
            "address": "123 Alta Loma Estate",
            "neighborhood": "Alta Loma",
            "price": 4_850_000,
            "price_per_sqft": 675,
            "bedrooms": 6,
            "bathrooms": 5.5,
            "square_feet": 7200,
            "days_on_market": 28,
            "amenities": ["Wine Cellar", "Home Theater", "Pool", "Tennis Court", "Guest House", "Spa"],
        },
        {
            "address": "456 North Rancho Manor",
            "neighborhood": "North Rancho",
            "price": 3_200_000,
            "price_per_sqft": 580,
            "bedrooms": 5,
            "bathrooms": 4.5,
            "square_feet": 5500,
            "days_on_market": 15,
            "amenities": ["Gourmet Kitchen", "Library", "Private Dock", "Gardens", "Art Studio"],
        },
    ]

    cols = st.columns(2)
    for i, property_data in enumerate(sample_properties):
        with cols[i]:
            luxury_ui.render_premium_property_card(property_data)

    luxury_ui.render_luxury_divider()

    # Client showcase
    st.markdown('<h2 class="luxury-title">UHNW Client Portfolio</h2>', unsafe_allow_html=True)

    sample_clients = [
        {
            "name": "Executive Client Alpha",
            "net_worth": 25_000_000,
            "service_level": "White-Glove",
            "satisfaction_score": 97.5,
            "portfolio_value": 8_500_000,
            "referrals_given": 5,
            "preferred_locations": ["Alta Loma", "North Rancho", "Deer Creek"],
        },
        {
            "name": "Investment Group Beta",
            "net_worth": 45_000_000,
            "service_level": "Concierge",
            "satisfaction_score": 98.2,
            "portfolio_value": 15_200_000,
            "referrals_given": 8,
            "preferred_locations": ["Downtown", "Victoria Gardens", "Alta Loma", "Central Rancho"],
        },
    ]

    client_cols = st.columns(2)
    for i, client_data in enumerate(sample_clients):
        with client_cols[i]:
            luxury_ui.render_luxury_client_card(client_data)

    luxury_ui.render_luxury_divider()

    # Premium features showcase
    premium_features = [
        {
            "icon": "🤖",
            "title": "AI Market Intelligence",
            "description": "Advanced property analysis and market forecasting powered by Claude AI",
        },
        {
            "icon": "💎",
            "title": "Investment Portfolio Management",
            "description": "Comprehensive portfolio tracking with ROI analysis and tax optimization",
        },
        {
            "icon": "🏆",
            "title": "White-Glove Service Tracking",
            "description": "Premium service delivery monitoring with quality assurance",
        },
        {
            "icon": "📊",
            "title": "Luxury Market Analytics",
            "description": "Real-time luxury market data integration and competitive intelligence",
        },
        {
            "icon": "🎯",
            "title": "UHNW Lead Scoring",
            "description": "Sophisticated lead qualification with net worth integration",
        },
        {
            "icon": "✨",
            "title": "Concierge Service Network",
            "description": "Access to luxury service providers and exclusive amenities",
        },
    ]

    luxury_ui.render_premium_feature_showcase(premium_features)

    # Service level badges
    st.markdown('<h3 class="executive-subtitle">Service Level Excellence</h3>', unsafe_allow_html=True)

    service_levels = ["Standard", "Premium", "White-Glove", "Concierge"]
    for level in service_levels:
        luxury_ui.render_white_glove_service_badge(level)

    luxury_ui.render_luxury_divider()

    # Progress indicators
    st.markdown('<h3 class="executive-subtitle">Performance Metrics</h3>', unsafe_allow_html=True)

    luxury_ui.render_luxury_progress_indicator("Client Satisfaction", 96.8)
    luxury_ui.render_luxury_progress_indicator("Service Quality Score", 94.2)
    luxury_ui.render_luxury_progress_indicator("Market Share (Luxury)", 12.5)
    luxury_ui.render_luxury_progress_indicator("Commission Premium", 31.0)

    # Executive alerts
    luxury_ui.render_executive_alert("New UHNW lead qualified: $35M net worth, immediate buyer", "luxury")
    luxury_ui.render_executive_alert("Portfolio performance exceeding targets by 15.2%", "success")
    luxury_ui.render_executive_alert("Luxury market showing strong momentum - acquisition opportunity", "info")

    # Luxury footer
    luxury_ui.render_luxury_footer()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Luxury UI Components Demo", page_icon="💎", layout="wide", initial_sidebar_state="expanded"
    )

    demo_luxury_components()
