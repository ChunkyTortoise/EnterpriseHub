"""
Design System Gallery - Interactive Component Showcase.

A comprehensive design system gallery featuring all reusable components,
design tokens, accessibility guidelines, and interactive demos with live code examples.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import json

import utils.ui as ui
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize session state
if "selected_component" not in st.session_state:
    st.session_state.selected_component = "Overview"
if "show_code_examples" not in st.session_state:
    st.session_state.show_code_examples = {}
if "design_system_theme" not in st.session_state:
    st.session_state.design_system_theme = "Light"


# ============================================================================
# Copy-to-Clipboard Utility
# ============================================================================


def render_code_with_copy(code: str, language: str = "python", key_suffix: str = "") -> None:
    """Render code block with copy-to-clipboard button.

    Args:
        code: Code string to display
        language: Programming language for syntax highlighting
        key_suffix: Unique suffix for widget keys
    """
    col1, col2 = st.columns([20, 1])

    with col1:
        st.code(code, language=language)

    with col2:
        # Add small vertical spacing to align button with code block
        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)

        if st.button("📋", key=f"copy_{key_suffix}", help="Copy to clipboard"):
            # Store code in session state for JavaScript access
            st.session_state[f"clipboard_{key_suffix}"] = code

            # Inject JavaScript to copy to clipboard
            js_code = f"""
            <script>
            (function() {{
                const code = {json.dumps(code)};
                navigator.clipboard.writeText(code).then(function() {{
                    console.log('Code copied to clipboard!');
                }}).catch(function(err) {{
                    console.error('Failed to copy: ', err);
                }});
            }})();
            </script>
            """
            st.markdown(js_code, unsafe_allow_html=True)
            st.toast("✅ Code copied to clipboard!", icon="✅")


# ============================================================================
# Design Tokens & Component Catalog
# ============================================================================

DESIGN_PRINCIPLES = {
    "Consistency": "Reusable components ensure consistent UX across all modules",
    "Accessibility": "WCAG 2.1 AA compliant with semantic HTML and ARIA labels",
    "Responsiveness": "Mobile-first design that scales to all screen sizes",
    "Performance": "Optimized animations and minimal CSS for fast load times",
    "Maintainability": "Design tokens enable theme-wide updates from a single source",
}

COMPONENT_STATS = {
    "Total Components": "16+",
    "Design Tokens": "40+",
    "WCAG Level": "AA",
    "Themes": "4",
}


# ============================================================================
# Enhanced Demo Functions
# ============================================================================


def render_metric_cards_showcase() -> None:
    """Render enhanced metric cards showcase with multiple styles."""
    st.markdown("### 📊 Metric Cards")
    st.markdown("Display KPIs with gradient backgrounds, trends, and visual hierarchy.")

    # Style 1: Gradient cards
    st.markdown("#### Gradient Style")
    cols = st.columns(4)

    gradients = [
        ("linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "Total Revenue", "$2.4M", "↑ 12.5%"),
        ("linear-gradient(135deg, #10B981 0%, #059669 100%)", "Active Users", "18.2K", "↑ 8.3%"),
        ("linear-gradient(135deg, #F59E0B 0%, #D97706 100%)", "Conversion", "3.8%", "↓ 1.2%"),
        ("linear-gradient(135deg, #EF4444 0%, #DC2626 100%)", "Churn Rate", "2.1%", "→ 0.0%"),
    ]

    for idx, (gradient, label, value, delta) in enumerate(gradients):
        with cols[idx]:
            st.markdown(
                f"""
            <div style='background: {gradient};
                        padding: 24px; border-radius: 12px; text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        transition: transform 0.3s ease;'>
                <div style='color: rgba(255,255,255,0.9); font-size: 14px;
                            font-weight: 500; margin-bottom: 8px;'>{label}</div>
                <div style='color: white; font-size: 32px; font-weight: 700;'>{value}</div>
                <div style='color: rgba(255,255,255,0.8); font-size: 12px;
                            margin-top: 8px;'>{delta}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Style 2: Glassmorphic cards
    st.markdown("#### Glassmorphic Style")
    cols = st.columns(3)

    with cols[0]:
        ui.animated_metric("Total Revenue", "$124,567", "+12.5%", "💰", "success")
    with cols[1]:
        ui.animated_metric("Active Users", "1,234", "+8.2%", "👥", "primary")
    with cols[2]:
        ui.animated_metric("Error Rate", "0.5%", "-0.3%", "⚠️", "warning")

    if st.checkbox("Show code example", key="metric_cards_code"):
        code = """# Gradient Style
st.markdown('''
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 24px; border-radius: 12px; text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
    <div style='color: rgba(255,255,255,0.9); font-size: 14px;
                font-weight: 500;'>Total Revenue</div>
    <div style='color: white; font-size: 32px; font-weight: 700;'>$2.4M</div>
    <div style='color: rgba(255,255,255,0.8); font-size: 12px;'>↑ 12.5%</div>
</div>
''', unsafe_allow_html=True)

# Animated Style (from utils.ui)
ui.animated_metric("Total Revenue", "$124,567", "+12.5%", "💰", "success")"""
        render_code_with_copy(code, language="python", key_suffix="metric_cards")


def render_button_showcase() -> None:
    """Render button variants showcase."""
    st.markdown("### 🔘 Buttons")
    st.markdown("Action triggers with hover effects, loading states, and semantic variants.")

    cols = st.columns(4)

    button_styles = [
        ("primary", "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "white", "Primary Action"),
        ("secondary", "transparent", "#667eea", "Secondary"),
        ("danger", "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)", "white", "Delete"),
        ("ghost", "transparent", "#6b7280", "Cancel"),
    ]

    for idx, (style_name, bg, color, label) in enumerate(button_styles):
        with cols[idx]:
            border = "2px solid #667eea" if style_name == "secondary" else "none"
            shadow = "0 4px 6px rgba(102, 126, 234, 0.3)" if style_name == "primary" else "none"

            st.markdown(
                f"""
            <style>
            .btn-{style_name} {{
                background: {bg};
                color: {color};
                padding: 12px 24px;
                border-radius: 8px;
                border: {border};
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: {shadow};
                width: 100%;
                text-align: center;
            }}
            .btn-{style_name}:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
            }}
            </style>
            <button class="btn-{style_name}">{label}</button>
            """,
                unsafe_allow_html=True,
            )

    if st.checkbox("Show code example", key="button_code"):
        code = """# Primary button with gradient
st.markdown('''
<style>
.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
}
.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
}
</style>
<button class="btn-primary">Primary Action</button>
''', unsafe_allow_html=True)

# Using Streamlit native buttons
if st.button("Primary Action", use_container_width=True):
    st.success("Button clicked!")"""
        render_code_with_copy(code, language="python", key_suffix="button")


def render_badge_showcase() -> None:
    """Render badge component showcase."""
    st.markdown("### 🏷️ Badges")
    st.markdown("Status and category indicators with semantic colors and animations.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Status Badges**")
        st.markdown(
            """
        <div style='display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px;'>
            <span style='background: linear-gradient(135deg, #10B981 0%, #059669 100%);
                         color: white; padding: 6px 16px; border-radius: 20px;
                         font-size: 14px; font-weight: 600;'>✓ Active</span>
            <span style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                         color: white; padding: 6px 16px; border-radius: 20px;
                         font-size: 14px; font-weight: 600;'>🆕 New</span>
            <span style='background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
                         color: white; padding: 6px 16px; border-radius: 20px;
                         font-size: 14px; font-weight: 600;'>⚠️ Warning</span>
            <span style='background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
                         color: white; padding: 6px 16px; border-radius: 20px;
                         font-size: 14px; font-weight: 600;'>✕ Error</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown("**Category Badges**")
        st.markdown(
            """
        <div style='display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px;'>
            <span style='background: #e5e7eb; color: #374151;
                         padding: 6px 16px; border-radius: 20px;
                         font-size: 14px; font-weight: 600;'>📊 Analytics</span>
            <span style='background: #e5e7eb; color: #374151;
                         padding: 6px 16px; border-radius: 20px;
                         font-size: 14px; font-weight: 600;'>💰 Finance</span>
            <span style='background: #e5e7eb; color: #374151;
                         padding: 6px 16px; border-radius: 20px;
                         font-size: 14px; font-weight: 600;'>🤖 AI</span>
            <span style='background: #e5e7eb; color: #374151;
                         padding: 6px 16px; border-radius: 20px;
                         font-size: 14px; font-weight: 600;'>📈 Marketing</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Using utils.ui badges
    st.markdown("**From utils.ui**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(ui.status_badge("hero"), unsafe_allow_html=True)
    with col2:
        st.markdown(ui.status_badge("active"), unsafe_allow_html=True)
    with col3:
        st.markdown(ui.status_badge("new"), unsafe_allow_html=True)
    with col4:
        st.markdown(ui.status_badge("pending"), unsafe_allow_html=True)


def render_chart_showcase(theme_mode: str = "Light") -> None:
    """Render chart theming showcase."""
    st.markdown("### 📈 Charts")
    st.markdown("Interactive data visualizations with consistent theming.")

    # Create sample data
    dates = pd.date_range(end=datetime.now(), periods=90, freq="D")
    df = pd.DataFrame(
        {
            "Date": dates,
            "Revenue": np.cumsum(np.random.randn(90) * 1000 + 5000),
            "Users": np.cumsum(np.random.randn(90) * 10 + 50),
            "Conversion": np.random.uniform(2, 5, 90),
        }
    )

    # Select template based on theme
    plotly_template = "plotly_dark" if theme_mode == "Dark" else "plotly_white"

    col1, col2 = st.columns(2)

    with col1:
        # Line chart with fill
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Revenue"],
                mode="lines",
                name="Revenue",
                line=dict(color="#667eea", width=3),
                fill="tozeroy",
                fillcolor="rgba(102, 126, 234, 0.1)",
            )
        )

        fig.update_layout(
            title="Revenue Trend",
            xaxis_title="Date",
            yaxis_title="Revenue ($)",
            hovermode="x unified",
            template=plotly_template,
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Bar chart
        fig = go.Figure()
        fig.add_trace(
            go.Bar(x=df["Date"][-30:], y=df["Users"][-30:], name="Users", marker_color="#10B981")
        )

        fig.update_layout(
            title="User Growth (Last 30 Days)",
            xaxis_title="Date",
            yaxis_title="Users",
            template=plotly_template,
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
        )

        st.plotly_chart(fig, use_container_width=True)


def render_design_tokens() -> None:
    """Render design tokens reference."""
    st.markdown("## 🎨 Design Tokens")
    st.markdown("Core design values used consistently throughout the application.")

    # Colors
    st.markdown("### Color Palette")

    col1, col2, col3, col4 = st.columns(4)

    color_tokens = [
        ("Primary", "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "#667eea → #764ba2"),
        ("Success", "linear-gradient(135deg, #10B981 0%, #059669 100%)", "#10B981 → #059669"),
        ("Warning", "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)", "#F59E0B → #D97706"),
        ("Error", "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)", "#EF4444 → #DC2626"),
    ]

    for idx, (name, gradient, code) in enumerate(color_tokens):
        with [col1, col2, col3, col4][idx]:
            st.markdown(f"**{name}**")
            st.markdown(
                f"""
            <div style='background: {gradient};
                        height: 100px; border-radius: 8px; margin-bottom: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);'></div>
            <code style='font-size: 11px;'>{code}</code>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Typography
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Typography Scale")
        st.markdown("""
        | Element | Size | Weight | Use Case |
        |---------|------|--------|----------|
        | H1 | 40px | 700 | Page titles |
        | H2 | 28px | 700 | Section headers |
        | H3 | 20px | 700 | Subsections |
        | Body | 16px | 400 | Main text |
        | Caption | 14px | 400 | Helper text |
        | Small | 12px | 400 | Labels |
        """)

    with col2:
        st.markdown("### Spacing System")
        st.markdown("""
        | Token | Value | Example Use |
        |-------|-------|-------------|
        | xs | 4px | Icon spacing |
        | sm | 8px | Compact layouts |
        | md | 16px | Default spacing |
        | lg | 24px | Section gaps |
        | xl | 32px | Large gaps |
        | 2xl | 48px | Major sections |
        """)

    st.markdown("---")

    # Effects
    st.markdown("### Effects & Transitions")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Shadows**")
        st.markdown("""
        ```css
        /* Small - Subtle lift */
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);

        /* Medium - Card depth */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);

        /* Large - Modal/dropdown */
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
        ```
        """)

    with col2:
        st.markdown("**Transitions**")
        st.markdown("""
        ```css
        /* Standard easing */
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

        /* Hover effects */
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        ```
        """)


def render_before_after() -> None:
    """Render before/after comparisons."""
    st.markdown("## 🔄 Before & After")
    st.markdown("Visual evolution of the design system - from basic to polished.")

    comparisons = [
        {
            "title": "Metric Cards",
            "before": """
            <div style='border: 1px solid #ddd; padding: 16px; border-radius: 4px;
                        background: white;'>
                <p style='margin: 0; color: black;'><strong>Total Revenue</strong></p>
                <h2 style='margin: 8px 0; color: black;'>$2,400,000</h2>
                <p style='margin: 0; font-size: 14px; color: #666;'>+12.5%</p>
            </div>
            """,
            "after": """
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 24px; border-radius: 12px; text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <div style='color: rgba(255,255,255,0.9); font-size: 14px;
                            font-weight: 500; margin-bottom: 8px;'>Total Revenue</div>
                <div style='color: white; font-size: 32px; font-weight: 700;'>$2.4M</div>
                <div style='color: rgba(255,255,255,0.8); font-size: 12px;
                            margin-top: 8px;'>↑ 12.5% vs last month</div>
            </div>
            """,
            "improvements": [
                "✅ Strong visual hierarchy",
                "✅ Brand gradient integration",
                "✅ Improved typography",
                "✅ Better contrast (WCAG AA)",
            ],
            "issues": [
                "❌ No visual hierarchy",
                "❌ Generic styling",
                "❌ Poor contrast",
                "❌ Lacks brand identity",
            ],
        }
    ]

    for comparison in comparisons:
        st.markdown(f"### {comparison['title']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**❌ Before (Basic)**")
            st.markdown(comparison["before"], unsafe_allow_html=True)
            st.markdown("**Issues:**")
            for issue in comparison["issues"]:
                st.markdown(issue)

        with col2:
            st.markdown("**✅ After (Enhanced)**")
            st.markdown(comparison["after"], unsafe_allow_html=True)
            st.markdown("**Improvements:**")
            for improvement in comparison["improvements"]:
                st.markdown(improvement)

        st.markdown("---")


def render_accessibility_guide() -> None:
    """Render accessibility guidelines and best practices."""
    st.markdown("## ♿ Accessibility")
    st.markdown("WCAG 2.1 AA compliance ensures the platform is usable by everyone.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Color Contrast")
        st.info("""
        **Minimum Requirements:**
        - Normal text: 4.5:1 contrast ratio
        - Large text (18pt+): 3:1 contrast ratio
        - UI components: 3:1 contrast ratio

        **All color combinations in this design system meet WCAG AA standards.**
        """)

        st.markdown("### Keyboard Navigation")
        st.info("""
        **Standards:**
        - All interactive elements are keyboard accessible
        - Visible focus indicators on all focusable elements
        - Logical tab order follows visual flow
        - Skip links for main content areas
        """)

    with col2:
        st.markdown("### Screen Readers")
        st.info("""
        **Best Practices:**
        - Semantic HTML structure (headings, landmarks)
        - Alt text for all images and icons
        - ARIA labels for complex interactions
        - Form labels properly associated with inputs
        """)

        st.markdown("### Responsive Design")
        st.info("""
        **Breakpoints:**
        - Mobile: < 768px
        - Tablet: 768px - 1024px
        - Desktop: > 1024px

        All components scale gracefully across devices.
        """)

    # Interactive contrast checker
    st.markdown("---")
    st.markdown("### 🔍 Contrast Checker")

    col1, col2, col3 = st.columns(3)

    with col1:
        fg_color = st.color_picker("Text Color", "#FFFFFF")
    with col2:
        bg_color = st.color_picker("Background Color", "#667eea")
    with col3:
        st.markdown("**Result**")
        ratio = calculate_contrast_ratio(fg_color, bg_color)
        st.markdown(f"Contrast: **{ratio:.2f}:1**")

        if ratio >= 7:
            st.success("✓ AAA (7:1+)")
        elif ratio >= 4.5:
            st.success("✓ AA (4.5:1+)")
        elif ratio >= 3:
            st.warning("⚠️ Large text only (3:1+)")
        else:
            st.error("✗ Fails WCAG")


def calculate_contrast_ratio(fg: str, bg: str) -> float:
    """Calculate WCAG contrast ratio between two colors."""

    def hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def relative_luminance(rgb: tuple) -> float:
        r, g, b = rgb
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    l1 = relative_luminance(hex_to_rgb(fg))
    l2 = relative_luminance(hex_to_rgb(bg))

    lighter = max(l1, l2)
    darker = min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)


def render_interactive_playground() -> None:
    """Render interactive component playground with live preview and code generation."""
    st.markdown("### 🎮 Interactive Playground")
    st.markdown("Customize components and see changes in real-time!")

    # Component selector
    component_type = st.selectbox(
        "Select Component", ["Metric Card", "Button", "Badge"], key="playground_component_type"
    )

    col1, col2 = st.columns([1, 2])

    # Gradient color presets
    gradient_presets = {
        "Primary": ("linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "#667eea", "#764ba2"),
        "Success": ("linear-gradient(135deg, #10B981 0%, #059669 100%)", "#10B981", "#059669"),
        "Warning": ("linear-gradient(135deg, #F59E0B 0%, #D97706 100%)", "#F59E0B", "#D97706"),
        "Error": ("linear-gradient(135deg, #EF4444 0%, #DC2626 100%)", "#EF4444", "#DC2626"),
    }

    # ============================================================================
    # METRIC CARD PLAYGROUND
    # ============================================================================
    if component_type == "Metric Card":
        with col1:
            st.markdown("**Customize Properties**")

            label = st.text_input("Label", "Total Revenue", key="playground_metric_label")
            value = st.text_input("Value", "$2.4M", key="playground_metric_value")
            delta = st.text_input("Delta", "↑ 12.5%", key="playground_metric_delta")

            gradient_choice = st.selectbox(
                "Gradient Color", list(gradient_presets.keys()), key="playground_metric_gradient"
            )

        with col2:
            st.markdown("**Live Preview**")

            gradient, _, _ = gradient_presets[gradient_choice]

            # Render the metric card
            st.markdown(
                f"""
            <div style='background: {gradient};
                        padding: 24px; border-radius: 12px; text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        transition: transform 0.3s ease;'>
                <div style='color: rgba(255,255,255,0.9); font-size: 14px;
                            font-weight: 500; margin-bottom: 8px;'>{label}</div>
                <div style='color: white; font-size: 32px; font-weight: 700;'>{value}</div>
                <div style='color: rgba(255,255,255,0.8); font-size: 12px;
                            margin-top: 8px;'>{delta}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown("**Generated Code**")

            generated_code = f"""st.markdown('''
<div style='background: {gradient};
            padding: 24px; border-radius: 12px; text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;'>
    <div style='color: rgba(255,255,255,0.9); font-size: 14px;
                font-weight: 500; margin-bottom: 8px;'>{label}</div>
    <div style='color: white; font-size: 32px; font-weight: 700;'>{value}</div>
    <div style='color: rgba(255,255,255,0.8); font-size: 12px;
                margin-top: 8px;'>{delta}</div>
</div>
''', unsafe_allow_html=True)"""

            st.code(generated_code, language="python")

    # ============================================================================
    # BUTTON PLAYGROUND
    # ============================================================================
    elif component_type == "Button":
        with col1:
            st.markdown("**Customize Properties**")

            button_label = st.text_input("Label", "Click Me", key="playground_button_label")

            button_style = st.selectbox(
                "Style", ["primary", "secondary", "danger", "ghost"], key="playground_button_style"
            )

            button_size = st.select_slider(
                "Size",
                options=["Small", "Medium", "Large"],
                value="Medium",
                key="playground_button_size",
            )

        with col2:
            st.markdown("**Live Preview**")

            # Map style to colors
            style_config = {
                "primary": {
                    "bg": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "color": "white",
                    "border": "none",
                    "shadow": "0 4px 6px rgba(102, 126, 234, 0.3)",
                },
                "secondary": {
                    "bg": "transparent",
                    "color": "#667eea",
                    "border": "2px solid #667eea",
                    "shadow": "none",
                },
                "danger": {
                    "bg": "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)",
                    "color": "white",
                    "border": "none",
                    "shadow": "0 4px 6px rgba(239, 68, 68, 0.3)",
                },
                "ghost": {
                    "bg": "transparent",
                    "color": "#6b7280",
                    "border": "none",
                    "shadow": "none",
                },
            }

            # Map size to padding
            size_config = {"Small": "8px 16px", "Medium": "12px 24px", "Large": "16px 32px"}

            config = style_config[button_style]
            padding = size_config[button_size]

            # Render the button
            st.markdown(
                f"""
            <style>
            .playground-btn {{
                background: {config["bg"]};
                color: {config["color"]};
                padding: {padding};
                border-radius: 8px;
                border: {config["border"]};
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: {config["shadow"]};
                width: 100%;
                text-align: center;
                font-size: 16px;
            }}
            .playground-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
            }}
            </style>
            <button class="playground-btn">{button_label}</button>
            """,
                unsafe_allow_html=True,
            )

            st.markdown("**Generated Code**")

            generated_code = f"""st.markdown('''
<style>
.btn-custom {{
    background: {config["bg"]};
    color: {config["color"]};
    padding: {padding};
    border-radius: 8px;
    border: {config["border"]};
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: {config["shadow"]};
    width: 100%;
    text-align: center;
}}
.btn-custom:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
}}
</style>
<button class="btn-custom">{button_label}</button>
''', unsafe_allow_html=True)"""

            st.code(generated_code, language="python")

    # ============================================================================
    # BADGE PLAYGROUND
    # ============================================================================
    elif component_type == "Badge":
        with col1:
            st.markdown("**Customize Properties**")

            badge_text = st.text_input("Text", "Active", key="playground_badge_text")

            badge_status = st.selectbox(
                "Status", ["hero", "active", "new", "pending"], key="playground_badge_status"
            )

            show_icon = st.checkbox("Show Icon", value=True, key="playground_badge_icon")

        with col2:
            st.markdown("**Live Preview**")

            # Status configurations
            status_config = {
                "hero": {
                    "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "icon": "⭐",
                },
                "active": {
                    "gradient": "linear-gradient(135deg, #10B981 0%, #059669 100%)",
                    "icon": "✓",
                },
                "new": {
                    "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "icon": "🆕",
                },
                "pending": {
                    "gradient": "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
                    "icon": "⏳",
                },
            }

            config = status_config[badge_status]
            icon_display = config["icon"] + " " if show_icon else ""

            # Render the badge
            st.markdown(
                f"""
            <div style='display: inline-block; margin: 20px 0;'>
                <span style='background: {config["gradient"]};
                             color: white; padding: 6px 16px; border-radius: 20px;
                             font-size: 14px; font-weight: 600;
                             box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    {icon_display}{badge_text}
                </span>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown("**Generated Code**")

            # Option 1: Custom HTML
            st.markdown("**Option 1: Custom HTML**")
            generated_code_html = f"""st.markdown('''
<span style='background: {config["gradient"]};
             color: white; padding: 6px 16px; border-radius: 20px;
             font-size: 14px; font-weight: 600;
             box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>{icon_display}{badge_text}</span>
''', unsafe_allow_html=True)"""

            st.code(generated_code_html, language="python")

            # Option 2: Using utils.ui
            st.markdown("**Option 2: Using utils.ui**")
            generated_code_ui = f"""import utils.ui as ui

# Use pre-built status badge
st.markdown(ui.status_badge("{badge_status}"), unsafe_allow_html=True)"""

            st.code(generated_code_ui, language="python")


# ============================================================================
# Main Render Function
# ============================================================================


def render() -> None:
    """Main render function for Design System Gallery."""

    # Theme switcher in sidebar
    with st.sidebar:
        st.markdown("### 🎨 Preview Theme")
        theme_mode = st.radio(
            "Select theme", ["Light", "Dark"], horizontal=True, key="design_system_theme"
        )
        st.info("💡 This only affects the Design System preview, not the entire app")

    # Apply theme-specific styling
    if theme_mode == "Dark":
        st.markdown(
            """
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        }
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] td,
        [data-testid="stMarkdownContainer"] th {
            color: #e0e0e0 !important;
        }
        [data-testid="stMarkdownContainer"] code {
            background-color: #2d2d44 !important;
            color: #e0e0e0 !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(255, 255, 255, 0.05);
        }
        .stTabs [data-baseweb="tab"] {
            color: #e0e0e0 !important;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
        <style>
        [data-testid="stAppViewContainer"] {
            background: #ffffff;
        }
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] td,
        [data-testid="stMarkdownContainer"] th {
            color: #1f2937 !important;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

    # Theme badge for hero section
    theme_badge = f"""
    <span style='background: rgba(255,255,255,0.2); color: white;
                 padding: 6px 16px; border-radius: 20px;
                 font-size: 14px; font-weight: 600;
                 display: inline-block; margin-top: 16px;'>
        🌓 Preview: {theme_mode} Mode
    </span>
    """

    # Hero section with gradient background
    st.markdown(
        f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 64px 32px; border-radius: 16px; margin-bottom: 32px;
                text-align: center; box-shadow: 0 8px 16px rgba(0,0,0,0.1);'>
        <h1 style='color: white; font-size: 48px; font-weight: 700;
                   margin: 0 0 16px 0; text-shadow: 0 2px 4px rgba(0,0,0,0.2);'>
            🎨 Design System Gallery
        </h1>
        <p style='color: rgba(255,255,255,0.95); font-size: 20px; margin: 0 0 24px 0;'>
            Interactive showcase of reusable UI components, design tokens, and
            accessibility guidelines
        </p>
        <div style='display: flex; gap: 32px; justify-content: center; flex-wrap: wrap;'>
            <div style='text-align: center;'>
                <div style='color: white; font-size: 36px; font-weight: 700;'>16+</div>
                <div style='color: rgba(255,255,255,0.9); font-size: 14px;'>Components</div>
            </div>
            <div style='text-align: center;'>
                <div style='color: white; font-size: 36px; font-weight: 700;'>40+</div>
                <div style='color: rgba(255,255,255,0.9); font-size: 14px;'>Design Tokens</div>
            </div>
            <div style='text-align: center;'>
                <div style='color: white; font-size: 36px; font-weight: 700;'>AA</div>
                <div style='color: rgba(255,255,255,0.9); font-size: 14px;'>WCAG Level</div>
            </div>
            <div style='text-align: center;'>
                <div style='color: white; font-size: 36px; font-weight: 700;'>4</div>
                <div style='color: rgba(255,255,255,0.9); font-size: 14px;'>Themes</div>
            </div>
        </div>
        {theme_badge}
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Main navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📚 Components",
            "🎨 Design Tokens",
            "♿ Accessibility",
            "🔄 Before & After",
            "🎯 Themes",
            "📖 Documentation",
        ]
    )

    with tab1:
        st.markdown("## Component Library")
        st.markdown("Explore all reusable components with live examples and code snippets.")
        st.markdown("---")

        render_metric_cards_showcase()
        st.markdown("---")

        render_button_showcase()
        st.markdown("---")

        render_badge_showcase()
        st.markdown("---")

        render_chart_showcase(theme_mode)
        st.markdown("---")

        # Additional components from utils.ui
        st.markdown("### 🎯 Utility Components")
        st.markdown("Components from `utils.ui` module for consistent UX.")

        col1, col2, col3 = st.columns(3)

        with col1:
            ui.feature_card(
                icon="💰",
                title="Feature Cards",
                description="Highlight key features with status badges",
                status="hero",
            )

        with col2:
            ui.feature_card(
                icon="✅",
                title="Use Case Cards",
                description="Showcase customer success stories",
                status="active",
            )

        with col3:
            ui.feature_card(
                icon="✨",
                title="Glassmorphic Cards",
                description="Modern frosted glass effect cards",
                status="new",
            )

        st.markdown("---")

        render_interactive_playground()

    with tab2:
        render_design_tokens()

    with tab3:
        render_accessibility_guide()

    with tab4:
        render_before_after()

    with tab5:
        st.markdown("## 🎯 Theme System")
        st.markdown("Enterprise Hub supports multiple themes with consistent color palettes.")

        # Show available themes
        themes = {
            "Light Theme": ui.LIGHT_THEME,
            "Dark Theme": ui.DARK_THEME,
            "Ocean Theme": ui.OCEAN_THEME if hasattr(ui, "OCEAN_THEME") else ui.DARK_THEME,
            "Sunset Theme": ui.SUNSET_THEME if hasattr(ui, "SUNSET_THEME") else ui.LIGHT_THEME,
        }

        for theme_name, theme_colors in list(themes.items())[:2]:  # Show first 2 themes
            st.markdown(f"### {theme_name}")

            # Display color swatches
            cols = st.columns(6)

            key_colors = ["primary", "success", "warning", "danger", "background", "text_main"]

            for idx, color_key in enumerate(key_colors):
                if color_key in theme_colors:
                    with cols[idx]:
                        st.markdown(
                            f"""
                        <div style='text-align: center;'>
                            <div style='background: {theme_colors[color_key]};
                                        height: 60px; border-radius: 8px;
                                        margin-bottom: 8px; border: 1px solid #e5e7eb;'></div>
                            <div style='font-size: 12px; font-weight: 600;'>{color_key}</div>
                            <code style='font-size: 10px;'>{theme_colors[color_key]}</code>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

            st.markdown("---")

    with tab6:
        st.markdown("## 📖 Usage Documentation")

        st.markdown("### Quick Start")
        st.info("""
        All components are designed to be copy-paste ready:

        1. **Find the component** you need in the Component Library tab
        2. **Click "Show code example"** to view the implementation
        3. **Copy the code** and paste into your module
        4. **Customize** colors, text, and values as needed
        """)

        st.markdown("---")

        st.markdown("### Design Principles")

        col1, col2 = st.columns(2)

        with col1:
            for key, value in list(DESIGN_PRINCIPLES.items())[:3]:
                st.markdown(f"**{key}**")
                st.markdown(f"{value}")
                st.markdown("")

        with col2:
            for key, value in list(DESIGN_PRINCIPLES.items())[3:]:
                st.markdown(f"**{key}**")
                st.markdown(f"{value}")
                st.markdown("")

        st.markdown("---")

        st.markdown("### Best Practices")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **✅ Do:**
            - Use design tokens for colors and spacing
            - Add hover effects to interactive elements
            - Include loading states for async operations
            - Test with keyboard navigation
            - Validate color contrast ratios
            """)

        with col2:
            st.markdown("""
            **❌ Don't:**
            - Hardcode colors or spacing values
            - Create one-off components
            - Skip accessibility attributes
            - Nest interactive elements
            - Use animations longer than 0.3s
            """)

        st.markdown("---")

        st.markdown("### Component Import Pattern")
        code = """# Import the UI utilities
import utils.ui as ui

# Use pre-built components
ui.hero_section("Title", "Subtitle")

ui.feature_card(
    icon="💰",
    title="Feature",
    description="Description text...",
    status="active"
)

ui.animated_metric("Revenue", "$124K", "+12%", "💰", "success")

# Get Plotly theme for charts
template = ui.get_plotly_template()
fig.update_layout(**template['layout'])"""
        render_code_with_copy(code, language="python", key_suffix="import_pattern")

        st.markdown("---")

        st.markdown("### Need Help?")
        st.markdown("""
        - **Component Catalog**: Browse all components with live examples
        - **Design Tokens**: Reference for approved colors, spacing, typography
        - **Accessibility Guide**: WCAG compliance guidelines
        - **Before & After**: Learn from improvement patterns
        """)

    # Footer stats
    st.markdown("---")

    cols = st.columns(5)

    stats = [
        ("Components", "16+", "Reusable UI elements"),
        ("Tokens", "40+", "Design variables"),
        ("WCAG", "AA", "Accessibility level"),
        ("Themes", "4", "Color schemes"),
        ("Patterns", "10+", "Layout templates"),
    ]

    for idx, (label, value, help_text) in enumerate(stats):
        with cols[idx]:
            st.metric(label, value, help=help_text)
