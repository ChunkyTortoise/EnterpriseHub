"""
Theme Manager - Enterprise Command Center

Provides consistent theming and styling across all command center components:
- Dark enterprise theme with professional styling
- Consistent color palette and typography
- Responsive design utilities
- Component-specific theme variations
- Plotly chart styling integration

Designed to work seamlessly with Predictive Insights Dashboard and other components.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class ThemeVariant(Enum):
    """Theme variant options"""
    ENTERPRISE = "enterprise"
    PROFESSIONAL = "professional"
    MINIMAL = "minimal"
    HIGH_CONTRAST = "high_contrast"

@dataclass
class ColorPalette:
    """Color palette definition"""
    primary: str
    secondary: str
    accent: str
    success: str
    warning: str
    danger: str
    info: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    border: str

class ThemeManager:
    """
    Enterprise theme manager for consistent styling
    
    Features:
    - Unified color schemes
    - Typography management
    - Component styling
    - Plotly chart theming
    - Responsive design utilities
    """
    
    def __init__(self, variant: ThemeVariant = ThemeVariant.ENTERPRISE):
        self.variant = variant
        self.palette = self._get_color_palette(variant)
        self.typography = self._get_typography_config()
        
    def apply_theme(self, inject_css: bool = True):
        """Apply theme globally"""
        if inject_css:
            self._inject_global_css()
        self._configure_streamlit()
    
    def _get_color_palette(self, variant: ThemeVariant) -> ColorPalette:
        """Get color palette for theme variant"""
        palettes = {
            ThemeVariant.ENTERPRISE: ColorPalette(
                primary="#3b82f6",       # Blue
                secondary="#6366f1",     # Indigo
                accent="#8b5cf6",        # Purple
                success="#10b981",       # Emerald
                warning="#f59e0b",       # Amber
                danger="#ef4444",        # Red
                info="#06b6d4",          # Cyan
                background="#0f172a",    # Slate 900
                surface="#1e293b",       # Slate 800
                text_primary="#f8fafc",  # Slate 50
                text_secondary="#cbd5e1", # Slate 300
                border="#334155"         # Slate 700
            ),
            ThemeVariant.PROFESSIONAL: ColorPalette(
                primary="#2563eb",       # Blue 600
                secondary="#7c3aed",     # Violet 600
                accent="#dc2626",        # Red 600
                success="#059669",       # Emerald 600
                warning="#d97706",       # Amber 600
                danger="#dc2626",        # Red 600
                info="#0891b2",          # Cyan 600
                background="#111827",    # Gray 900
                surface="#374151",       # Gray 700
                text_primary="#f9fafb",  # Gray 50
                text_secondary="#d1d5db", # Gray 300
                border="#4b5563"         # Gray 600
            ),
            ThemeVariant.MINIMAL: ColorPalette(
                primary="#374151",       # Gray 700
                secondary="#6b7280",     # Gray 500
                accent="#9ca3af",        # Gray 400
                success="#065f46",       # Emerald 800
                warning="#92400e",       # Amber 800
                danger="#991b1b",        # Red 800
                info="#155e75",          # Cyan 800
                background="#ffffff",    # White
                surface="#f9fafb",       # Gray 50
                text_primary="#111827",  # Gray 900
                text_secondary="#6b7280", # Gray 500
                border="#e5e7eb"         # Gray 200
            )
        }
        
        return palettes.get(variant, palettes[ThemeVariant.ENTERPRISE])
    
    def _get_typography_config(self) -> Dict[str, str]:
        """Get typography configuration"""
        return {
            'primary_font': "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            'mono_font': "'Space Mono', 'SF Mono', Monaco, 'Cascadia Code', monospace",
            'display_font': "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
        }
    
    def _inject_global_css(self):
        """Inject global CSS styles"""
        css = f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');
        
        /* Root variables */
        :root {{
            --primary: {self.palette.primary};
            --secondary: {self.palette.secondary};
            --accent: {self.palette.accent};
            --success: {self.palette.success};
            --warning: {self.palette.warning};
            --danger: {self.palette.danger};
            --info: {self.palette.info};
            --background: {self.palette.background};
            --surface: {self.palette.surface};
            --text-primary: {self.palette.text_primary};
            --text-secondary: {self.palette.text_secondary};
            --border: {self.palette.border};
            --font-primary: {self.typography['primary_font']};
            --font-mono: {self.typography['mono_font']};
        }}
        
        /* Global styles */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        
        /* Enhanced card styling */
        .enterprise-card {{
            background: linear-gradient(135deg, 
                rgba(30, 41, 59, 0.95) 0%, 
                rgba(51, 65, 85, 0.9) 100%);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(20px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .enterprise-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
            border-color: rgba(59, 130, 246, 0.3);
        }}
        
        /* Header styling */
        .dashboard-header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem;
            background: linear-gradient(135deg, 
                rgba(59, 130, 246, 0.1) 0%, 
                rgba(147, 51, 234, 0.1) 100%);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 20px;
            backdrop-filter: blur(20px);
        }}
        
        .dashboard-title {{
            font-family: var(--font-primary);
            font-size: 3rem;
            font-weight: 800;
            color: var(--text-primary);
            margin: 0;
            text-shadow: 0 0 30px rgba(59, 130, 246, 0.5);
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .dashboard-subtitle {{
            font-family: var(--font-primary);
            font-size: 1.2rem;
            color: var(--text-secondary);
            margin: 1rem 0 0 0;
            font-weight: 500;
        }}
        
        /* Metric cards */
        .metric-card {{
            background: linear-gradient(135deg, 
                rgba(15, 23, 42, 0.8) 0%, 
                rgba(30, 41, 59, 0.6) 100%);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }}
        
        .metric-card:hover {{
            transform: translateY(-3px);
            border-color: rgba(59, 130, 246, 0.4);
            box-shadow: 0 10px 25px rgba(59, 130, 246, 0.2);
        }}
        
        .metric-value {{
            font-family: var(--font-mono);
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 0.5rem 0;
            text-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
        }}
        
        .metric-label {{
            font-family: var(--font-primary);
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        /* Status indicators */
        .status-positive {{
            color: var(--success);
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-weight: 600;
        }}
        
        .status-negative {{
            color: var(--danger);
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-weight: 600;
        }}
        
        .status-neutral {{
            color: var(--warning);
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.3);
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-weight: 600;
        }}
        
        /* Navigation and tabs */
        .nav-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}
        
        .nav-item {{
            background: linear-gradient(135deg, 
                rgba(51, 65, 85, 0.7) 0%, 
                rgba(71, 85, 105, 0.5) 100%);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 10px;
            padding: 1rem 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(8px);
        }}
        
        .nav-item:hover {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-color: var(--primary);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
        }}
        
        .nav-item.active {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-color: var(--primary);
            color: white;
        }}
        
        /* Chart containers */
        .chart-container {{
            background: linear-gradient(135deg, 
                rgba(15, 23, 42, 0.6) 0%, 
                rgba(30, 41, 59, 0.4) 100%);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 16px;
            padding: 2rem;
            margin: 1.5rem 0;
            backdrop-filter: blur(15px);
        }}
        
        .chart-title {{
            font-family: var(--font-primary);
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1.5rem;
            text-align: center;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid rgba(59, 130, 246, 0.3);
        }}
        
        /* Alert styling */
        .alert {{
            border-radius: 10px;
            padding: 1rem 1.5rem;
            margin: 1rem 0;
            border-left: 4px solid;
            backdrop-filter: blur(10px);
        }}
        
        .alert-info {{
            background: rgba(59, 130, 246, 0.1);
            border-color: var(--info);
            color: var(--text-primary);
        }}
        
        .alert-warning {{
            background: rgba(245, 158, 11, 0.1);
            border-color: var(--warning);
            color: var(--text-primary);
        }}
        
        .alert-danger {{
            background: rgba(239, 68, 68, 0.1);
            border-color: var(--danger);
            color: var(--text-primary);
        }}
        
        .alert-success {{
            background: rgba(16, 185, 129, 0.1);
            border-color: var(--success);
            color: var(--text-primary);
        }}
        
        /* Grid layouts */
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
            margin: 1.5rem 0;
        }}
        
        .grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin: 1.5rem 0;
        }}
        
        .grid-4 {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            margin: 1.5rem 0;
        }}
        
        .grid-auto {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin: 1.5rem 0;
        }}
        
        /* Responsive breakpoints */
        @media (max-width: 768px) {{
            .grid-2, .grid-3, .grid-4 {{
                grid-template-columns: 1fr;
            }}
            
            .dashboard-title {{
                font-size: 2rem;
            }}
            
            .nav-container {{
                grid-template-columns: 1fr;
            }}
        }}
        
        /* Custom scrollbars */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(30, 41, 59, 0.3);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: rgba(59, 130, 246, 0.6);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(59, 130, 246, 0.8);
        }}
        
        /* Animation utilities */
        .fade-in {{
            animation: fadeIn 0.6s ease-in;
        }}
        
        .slide-up {{
            animation: slideUp 0.5s ease-out;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        @keyframes slideUp {{
            from {{ 
                transform: translateY(20px); 
                opacity: 0; 
            }}
            to {{ 
                transform: translateY(0); 
                opacity: 1; 
            }}
        }}
        
        /* Focus states for accessibility */
        .nav-item:focus,
        .metric-card:focus {{
            outline: 2px solid var(--primary);
            outline-offset: 2px;
        }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def _configure_streamlit(self):
        """Configure Streamlit-specific settings"""
        # Hide Streamlit style elements
        hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        </style>
        """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    def style_plotly_chart(self, fig: go.Figure, 
                          title: Optional[str] = None,
                          height: int = 400,
                          margin: Optional[Dict[str, int]] = None) -> go.Figure:
        """Apply enterprise theme to Plotly chart"""
        
        if margin is None:
            margin = dict(t=50, r=30, b=50, l=60)
        
        # Update layout with theme colors
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_family=self.typography['primary_font'],
            font_color=self.palette.text_primary,
            font_size=12,
            title=dict(
                text=title,
                font=dict(
                    size=16,
                    color=self.palette.text_primary,
                    family=self.typography['primary_font']
                ),
                x=0.5,
                xanchor='center'
            ) if title else None,
            height=height,
            margin=margin,
            showlegend=True,
            legend=dict(
                bgcolor='rgba(30, 41, 59, 0.8)',
                bordercolor=self.palette.border,
                borderwidth=1,
                font=dict(color=self.palette.text_primary)
            ),
            hoverlabel=dict(
                bgcolor='rgba(30, 41, 59, 0.95)',
                bordercolor=self.palette.border,
                font_color=self.palette.text_primary
            ),
            xaxis=dict(
                gridcolor='rgba(148, 163, 184, 0.1)',
                color=self.palette.text_secondary,
                tickfont=dict(color=self.palette.text_secondary)
            ),
            yaxis=dict(
                gridcolor='rgba(148, 163, 184, 0.1)',
                color=self.palette.text_secondary,
                tickfont=dict(color=self.palette.text_secondary)
            )
        )
        
        return fig
    
    def create_gradient_colorscale(self, colors: List[str]) -> List[List]:
        """Create gradient colorscale for Plotly"""
        n_colors = len(colors)
        step = 1.0 / (n_colors - 1)
        
        colorscale = []
        for i, color in enumerate(colors):
            colorscale.append([i * step, color])
        
        return colorscale
    
    def get_color_sequence(self) -> List[str]:
        """Get color sequence for multiple data series"""
        return [
            self.palette.primary,
            self.palette.secondary,
            self.palette.accent,
            self.palette.success,
            self.palette.warning,
            self.palette.info,
            self.palette.danger
        ]
    
    def render_header(self, title: str, subtitle: Optional[str] = None, icon: str = "🏢"):
        """Render styled dashboard header"""
        subtitle_html = f'<p class="dashboard-subtitle">{subtitle}</p>' if subtitle else ''
        
        st.markdown(f"""
        <div class="dashboard-header fade-in">
            <h1 class="dashboard-title">{icon} {title}</h1>
            {subtitle_html}
        </div>
        """, unsafe_allow_html=True)
    
    def render_metric_card(self, title: str, value: str, 
                          change: Optional[str] = None,
                          change_type: str = "neutral",
                          icon: str = "📊"):
        """Render styled metric card"""
        change_class = f"status-{change_type}"
        change_html = f'<div class="{change_class}">{change}</div>' if change else ''
        
        return f"""
        <div class="metric-card slide-up">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            {change_html}
        </div>
        """
    
    def render_alert(self, message: str, alert_type: str = "info", 
                    title: Optional[str] = None, icon: str = "ℹ️"):
        """Render styled alert"""
        title_html = f'<strong>{icon} {title}</strong><br>' if title else f'{icon} '
        
        st.markdown(f"""
        <div class="alert alert-{alert_type}">
            {title_html}{message}
        </div>
        """, unsafe_allow_html=True)
    
    def create_chart_container(self, title: str, icon: str = "📊") -> str:
        """Create chart container with title"""
        return f"""
        <div class="chart-container">
            <h3 class="chart-title">{icon} {title}</h3>
        """
    
    def close_chart_container(self) -> str:
        """Close chart container"""
        return "</div>"


# Theme presets
class ThemePresets:
    """Predefined theme configurations"""
    
    @staticmethod
    def enterprise() -> ThemeManager:
        """Enterprise theme - professional dark theme"""
        return ThemeManager(ThemeVariant.ENTERPRISE)
    
    @staticmethod
    def professional() -> ThemeManager:
        """Professional theme - clean business theme"""
        return ThemeManager(ThemeVariant.PROFESSIONAL)
    
    @staticmethod
    def minimal() -> ThemeManager:
        """Minimal theme - clean light theme"""
        return ThemeManager(ThemeVariant.MINIMAL)


def apply_enterprise_theme():
    """Quick function to apply enterprise theme"""
    theme = ThemePresets.enterprise()
    theme.apply_theme()
    return theme


def style_enterprise_chart(fig: go.Figure, title: Optional[str] = None) -> go.Figure:
    """Quick function to style chart with enterprise theme"""
    theme = ThemePresets.enterprise()
    return theme.style_plotly_chart(fig, title)


# Testing and demo
if __name__ == "__main__":
    st.title("🎨 Theme Manager Demo")
    
    # Apply theme
    theme = apply_enterprise_theme()
    
    # Demo header
    theme.render_header(
        title="Enterprise Dashboard",
        subtitle="Advanced analytics and insights platform"
    )
    
    # Demo metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(theme.render_metric_card(
            "Revenue", "$125K", "+12%", "positive", "💰"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(theme.render_metric_card(
            "Conversion", "15.3%", "+2.1%", "positive", "🎯"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(theme.render_metric_card(
            "Leads", "1,247", "-5%", "negative", "👥"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(theme.render_metric_card(
            "Quality", "87%", "0%", "neutral", "⭐"
        ), unsafe_allow_html=True)
    
    # Demo alerts
    theme.render_alert(
        "System performance is optimal", 
        "success", 
        "System Status", 
        "✅"
    )
    
    theme.render_alert(
        "Lead volume is below expected threshold", 
        "warning", 
        "Performance Alert", 
        "⚠️"
    )
    
    # Demo chart
    import numpy as np
    
    x = np.arange(30)
    y = np.random.normal(100, 15, 30).cumsum()
    
    fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines'))
    styled_fig = theme.style_plotly_chart(fig, "Sample Trend Chart")
    
    st.plotly_chart(styled_fig, use_container_width=True)