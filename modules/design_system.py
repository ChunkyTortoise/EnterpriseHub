"""
Design System Gallery - Interactive Component Showcase.

This module showcases all UI components from utils.ui, demonstrating the
complete design system with live examples, color palettes, typography,
and interactive component demonstrations.
"""
from typing import Dict

import streamlit as st

import utils.ui as ui
from utils.logger import get_logger

logger = get_logger(__name__)


def render() -> None:
    """Design System Gallery entry point."""
    st.title("Design System Gallery")
    st.markdown(
        "<p style='font-size: 1.1rem; margin-bottom: 2rem;'>"
        "Explore the complete component library and design tokens that power "
        "Enterprise Hub's professional interface.</p>",
        unsafe_allow_html=True,
    )

    # Create tabs for different sections
    tabs = st.tabs(
        [
            "🎨 Colors",
            "📝 Typography",
            "🧩 Components",
            "🎯 Interactive Elements",
            "📋 Patterns",
        ]
    )

    with tabs[0]:
        _render_colors_tab()

    with tabs[1]:
        _render_typography_tab()

    with tabs[2]:
        _render_components_tab()

    with tabs[3]:
        _render_interactive_tab()

    with tabs[4]:
        _render_patterns_tab()


def _render_colors_tab() -> None:
    """Render the color palette showcase."""
    st.markdown("## Color System")
    st.markdown(
        "All colors meet WCAG AAA compliance standards (7:1+ contrast ratio) "
        "for optimal accessibility."
    )

    # Light Theme
    st.markdown("---")
    st.markdown("### ☀️ Light Theme")

    light_colors = ui.LIGHT_THEME
    _render_color_palette(light_colors, "light")

    # Dark Theme
    st.markdown("---")
    st.markdown("### 🌙 Dark Theme")

    dark_colors = ui.DARK_THEME
    _render_color_palette(dark_colors, "dark")

    # Color Usage Guide
    st.markdown("---")
    st.markdown("### 📖 Color Usage Guide")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        **Primary Colors**
        - `primary`: Main brand color for buttons, links, headings
        - `primary_dark`: Hover states, accents
        - `primary_light`: Backgrounds, subtle highlights

        **Semantic Colors**
        - `success`: Positive actions, confirmations
        - `warning`: Caution, important notices
        - `danger`: Errors, destructive actions
        """
        )

    with col2:
        st.markdown(
            """
        **Neutrals**
        - `background`: Page background
        - `surface`: Card/panel background
        - `border`: Dividers, outlines
        - `text_main`: Primary text
        - `text_light`: Secondary text, captions
        - `secondary`: Muted UI elements
        """
        )


def _render_color_palette(colors: Dict[str, str], theme_name: str) -> None:
    """Render a color palette with swatches and hex codes."""
    # Group colors by category
    primary_colors = {k: v for k, v in colors.items() if "primary" in k}
    semantic_colors = {
        k: v for k, v in colors.items() if k in ["success", "warning", "danger"]
    }
    neutral_colors = {
        k: v
        for k, v in colors.items()
        if k in ["background", "surface", "border", "secondary"]
    }
    text_colors = {k: v for k, v in colors.items() if "text" in k or k == "button_text"}

    # Primary Colors
    st.markdown("#### Primary Brand Colors")
    cols = st.columns(len(primary_colors))
    for idx, (name, hex_code) in enumerate(primary_colors.items()):
        with cols[idx]:
            _render_color_swatch(name, hex_code, theme_name)

    # Semantic Colors
    st.markdown("#### Semantic Colors")
    cols = st.columns(len(semantic_colors))
    for idx, (name, hex_code) in enumerate(semantic_colors.items()):
        with cols[idx]:
            _render_color_swatch(name, hex_code, theme_name)

    # Neutral Colors
    st.markdown("#### Neutral Colors")
    cols = st.columns(len(neutral_colors))
    for idx, (name, hex_code) in enumerate(neutral_colors.items()):
        with cols[idx]:
            _render_color_swatch(name, hex_code, theme_name)

    # Text Colors
    st.markdown("#### Text Colors")
    cols = st.columns(len(text_colors))
    for idx, (name, hex_code) in enumerate(text_colors.items()):
        with cols[idx]:
            _render_color_swatch(name, hex_code, theme_name)


def _render_color_swatch(name: str, hex_code: str, theme_name: str) -> None:
    """Render a single color swatch with name and hex code."""
    # Determine text color for contrast
    text_color = (
        "#FFFFFF"
        if theme_name == "light" and "light" not in name and name != "background"
        else "#0F172A"
    )

    if "background" in name or "light" in name or theme_name == "dark":
        text_color = "#0F172A" if "light" in name or name == "background" else "#FFFFFF"

    html = f"""
    <div style="text-align: center; margin-bottom: 1rem;">
        <div style="
            background-color: {hex_code};
            height: 100px;
            border-radius: 8px;
            border: 1px solid {ui.THEME['border']};
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        ">
            <span style="
                color: {text_color};
                font-weight: 600;
                font-size: 0.9rem;
                text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            ">{hex_code}</span>
        </div>
        <div style="
            font-weight: 600;
            color: {ui.THEME['text_main']};
            font-size: 0.85rem;
            margin-bottom: 0.25rem;
        ">{name}</div>
        <code style="
            font-size: 0.75rem;
            color: {ui.THEME['text_light']};
            background: {ui.THEME['background']};
            padding: 2px 6px;
            border-radius: 4px;
        ">{hex_code}</code>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def _render_typography_tab() -> None:
    """Render the typography showcase."""
    st.markdown("## Typography System")
    st.markdown(
        "Enterprise Hub uses **Inter** for all text, with carefully calibrated sizes and weights."
    )

    # Font Family
    st.markdown("---")
    st.markdown("### Font Family")
    st.code(
        "font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;"
    )

    # Headings
    st.markdown("---")
    st.markdown("### Headings")

    st.markdown(
        """
    # Heading 1 (H1)
    **Usage:** Page titles, hero sections
    **Size:** 2.5rem (40px) | **Weight:** 700 | **Color:** Gradient (primary → primary_dark)
    """
    )

    st.markdown("---")

    st.markdown(
        """
    ## Heading 2 (H2)
    **Usage:** Section headers, major divisions
    **Size:** 1.75rem (28px) | **Weight:** 700 | **Color:** text_main
    """
    )

    st.markdown("---")

    st.markdown(
        """
    ### Heading 3 (H3)
    **Usage:** Subsections, card titles
    **Size:** 1.25rem (20px) | **Weight:** 700 | **Color:** text_main
    """
    )

    # Body Text
    st.markdown("---")
    st.markdown("### Body Text")

    st.markdown(
        """
    This is regular body text at the default size (1rem / 16px). It uses the primary
    text color (`text_main`) with a weight of 400 for optimal readability. The line
    height is set to 1.6 for comfortable reading across multiple lines.

    **Font Size:** 1rem (16px)
    **Weight:** 400
    **Line Height:** 1.6
    **Color:** text_main
    """
    )

    # Typography Scale
    st.markdown("---")
    st.markdown("### Typography Scale")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        **Heading Scale**
        - H1: 2.5rem (40px)
        - H2: 1.75rem (28px)
        - H3: 1.25rem (20px)
        - Body: 1rem (16px)
        """
        )

    with col2:
        st.markdown(
            """
        **Weight Scale**
        - Regular: 400
        - Medium: 500
        - Semibold: 600
        - Bold: 700
        - Extrabold: 800
        """
        )

    # Special Typography
    st.markdown("---")
    st.markdown("### Special Text Styles")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        **Metric Labels**
        <span style="font-size: 0.875rem; color: #64748B; font-weight: 600;
                     text-transform: uppercase; letter-spacing: 0.05em;">
            REVENUE GROWTH</span>

        `font-size: 0.875rem` | `text-transform: uppercase` | `letter-spacing: 0.05em`
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        **Metric Values**
        <span style="font-size: 2rem; font-weight: 700;
                     color: {ui.THEME['primary']}; font-feature-settings: 'tnum';
                     font-variant-numeric: tabular-nums;">$124,567</span>

        `font-size: 2rem` | `weight: 700` | `tabular-nums enabled`
        """,
            unsafe_allow_html=True,
        )


def _render_components_tab() -> None:
    """Render the components showcase."""
    st.markdown("## Component Library")
    st.markdown("Pre-built components with consistent styling and behavior.")

    # Hero Section
    st.markdown("---")
    st.markdown("### Hero Section")
    st.markdown("**Usage:** Landing pages, module introductions")

    ui.hero_section(
        "Welcome to Enterprise Hub",
        "A production-grade business intelligence platform with 7 mission-critical "
        "tools in one unified interface.",
    )

    with st.expander("View Code"):
        st.code(
            """
ui.hero_section(
    "Welcome to Enterprise Hub",
    "A production-grade business intelligence platform..."
)
        """,
            language="python",
        )

    # Feature Cards
    st.markdown("---")
    st.markdown("### Feature Cards")
    st.markdown("**Usage:** Module showcases, feature highlights")

    col1, col2, col3 = st.columns(3)

    with col1:
        ui.feature_card(
            icon="💰",
            title="Hero Feature",
            description="Highlight your most important capability with the hero status badge.",
            status="hero",
        )

    with col2:
        ui.feature_card(
            icon="✅",
            title="Active Feature",
            description="Show production-ready features with the active status badge.",
            status="active",
        )

    with col3:
        ui.feature_card(
            icon="✨",
            title="New Feature",
            description="Highlight recently launched features with the new status badge.",
            status="new",
        )

    with st.expander("View Code"):
        st.code(
            """
ui.feature_card(
    icon="💰",
    title="Hero Feature",
    description="Highlight your most important capability...",
    status="hero"  # or "active", "new", "pending"
)
        """,
            language="python",
        )

    # Use Case Cards
    st.markdown("---")
    st.markdown("### Use Case Cards")
    st.markdown("**Usage:** Customer stories, social proof sections")

    col1, col2 = st.columns(2)

    with col1:
        ui.use_case_card(
            icon="💡",
            title="For SaaS Founders",
            description=(
                "Run 100 profit scenarios simultaneously with sensitivity heatmaps. "
                "Break-even analysis that updates in real-time."
            ),
        )

    with col2:
        ui.use_case_card(
            icon="📊",
            title="For Finance Teams",
            description=(
                "4-panel charts with institutional-grade indicators. "
                "Save $24,000/year in Bloomberg subscriptions."
            ),
        )

    with st.expander("View Code"):
        st.code(
            """
ui.use_case_card(
    icon="💡",
    title="For SaaS Founders",
    description="Run 100 profit scenarios simultaneously..."
)
        """,
            language="python",
        )

    # Status Badges
    st.markdown("---")
    st.markdown("### Status Badges")
    st.markdown("**Usage:** Labels, tags, state indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(ui.status_badge("hero"), unsafe_allow_html=True)
        st.caption("Hero status")

    with col2:
        st.markdown(ui.status_badge("active"), unsafe_allow_html=True)
        st.caption("Active status")

    with col3:
        st.markdown(ui.status_badge("new"), unsafe_allow_html=True)
        st.caption("New status")

    with col4:
        st.markdown(ui.status_badge("pending"), unsafe_allow_html=True)
        st.caption("Pending status")

    with st.expander("View Code"):
        st.code(
            """
# Returns HTML string - use with st.markdown(..., unsafe_allow_html=True)
badge_html = ui.status_badge("hero")  # or "active", "new", "pending"
st.markdown(badge_html, unsafe_allow_html=True)
        """,
            language="python",
        )

    # Section Headers
    st.markdown("---")
    st.markdown("### Section Headers")
    st.markdown("**Usage:** Page sections, content divisions")

    ui.section_header(
        "Section Title",
        "Optional subtitle text provides additional context and description for the section below.",
    )

    st.markdown("Content goes here...")

    with st.expander("View Code"):
        st.code(
            """
ui.section_header(
    "Section Title",
    "Optional subtitle text provides additional context..."
)
        """,
            language="python",
        )

    # Comparison Table
    st.markdown("---")
    st.markdown("### Comparison Table")
    st.markdown("**Usage:** Product comparisons, competitive analysis")

    ui.comparison_table()

    with st.expander("View Code"):
        st.code(
            """
ui.comparison_table()  # Renders pre-configured comparison table
        """,
            language="python",
        )


def _render_interactive_tab() -> None:
    """Render interactive elements showcase."""
    st.markdown("## Interactive Elements")
    st.markdown("Buttons, inputs, and interactive components with consistent styling.")

    # Buttons
    st.markdown("---")
    st.markdown("### Buttons")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Primary Button**")
        if st.button("Primary Action", key="btn_primary", use_container_width=True):
            st.success("Primary button clicked!")
        st.caption("Default button style for primary actions")

    with col2:
        st.markdown("**Secondary Button**")
        if st.button(
            "Secondary Action",
            key="btn_secondary",
            type="secondary",
            use_container_width=True,
        ):
            st.info("Secondary button clicked!")
        st.caption("Secondary style for less prominent actions")

    with col3:
        st.markdown("**Disabled Button**")
        st.button(
            "Disabled", key="btn_disabled", disabled=True, use_container_width=True
        )
        st.caption("Disabled state for unavailable actions")

    with st.expander("View Code"):
        st.code(
            """
# Primary button (default)
st.button("Primary Action")

# Secondary button
st.button("Secondary Action", type="secondary")

# Disabled button
st.button("Disabled", disabled=True)
        """,
            language="python",
        )

    # Metrics
    st.markdown("---")
    st.markdown("### Metric Cards")
    st.markdown("Display key performance indicators with optional delta values.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ui.card_metric("Revenue", "$124.5K", "+12.5%")

    with col2:
        ui.card_metric("Users", "1,234", "+8.2%")

    with col3:
        ui.card_metric("Conversion", "3.2%", "-0.5%")

    with col4:
        ui.card_metric("MRR", "$45.2K", "+15.3%")

    with st.expander("View Code"):
        st.code(
            """
ui.card_metric(
    label="Revenue",
    value="$124.5K",
    delta="+12.5%",  # Optional
    help="Monthly recurring revenue"  # Optional
)
        """,
            language="python",
        )

    # Form Elements
    st.markdown("---")
    st.markdown("### Form Elements")

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Text Input", placeholder="Enter text here...", key="demo_text")
        st.selectbox(
            "Select Dropdown", ["Option 1", "Option 2", "Option 3"], key="demo_select"
        )
        st.slider("Slider", 0, 100, 50, key="demo_slider")

    with col2:
        st.number_input(
            "Number Input", min_value=0, max_value=100, value=50, key="demo_number"
        )
        st.date_input("Date Picker", key="demo_date")
        st.time_input("Time Picker", key="demo_time")

    with st.expander("View Code"):
        st.code(
            """
# Text input
st.text_input("Label", placeholder="Placeholder...")

# Dropdown
st.selectbox("Label", ["Option 1", "Option 2"])

# Slider
st.slider("Label", 0, 100, 50)

# Number input
st.number_input("Label", min_value=0, max_value=100)
        """,
            language="python",
        )

    # Alerts
    st.markdown("---")
    st.markdown("### Alert Messages")

    st.success("Success! Your operation completed successfully.")
    st.info("Info: Here's some helpful information for you.")
    st.warning("Warning: Please review this important notice.")
    st.error("Error: Something went wrong. Please try again.")

    with st.expander("View Code"):
        st.code(
            """
st.success("Success! Your operation completed successfully.")
st.info("Info: Here's some helpful information...")
st.warning("Warning: Please review this important notice.")
st.error("Error: Something went wrong...")
        """,
            language="python",
        )


def _render_patterns_tab() -> None:
    """Render common UI patterns and layouts."""
    st.markdown("## Common Patterns")
    st.markdown("Reusable layout patterns and composition examples.")

    # Column Layouts
    st.markdown("---")
    st.markdown("### Column Layouts")

    st.markdown("#### Two Column Layout (50/50)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
        <div style='background: {0}; padding: 2rem; border-radius: 8px; border: 1px solid {1};'>
            <h4 style='margin-top: 0;'>Left Column</h4>
            <p>Equal width columns for balanced content.</p>
        </div>
        """.format(
                ui.THEME["surface"], ui.THEME["border"]
            ),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
        <div style='background: {0}; padding: 2rem; border-radius: 8px; border: 1px solid {1};'>
            <h4 style='margin-top: 0;'>Right Column</h4>
            <p>Use for side-by-side comparisons.</p>
        </div>
        """.format(
                ui.THEME["surface"], ui.THEME["border"]
            ),
            unsafe_allow_html=True,
        )

    st.markdown("#### Three Column Layout (33/33/33)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Column 1**")
        st.markdown("Feature cards, metrics")
    with col2:
        st.markdown("**Column 2**")
        st.markdown("Balanced trifecta layout")
    with col3:
        st.markdown("**Column 3**")
        st.markdown("Great for dashboards")

    st.markdown("#### Weighted Columns (1:3 ratio)")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("**Sidebar**")
        st.markdown("Narrow sidebar for filters or navigation")
    with col2:
        st.markdown("**Main Content**")
        st.markdown("Wide main content area for primary information")

    with st.expander("View Code"):
        st.code(
            """
# Equal columns
col1, col2 = st.columns(2)
col1, col2, col3 = st.columns(3)

# Weighted columns (ratios)
col1, col2 = st.columns([1, 3])  # 25% / 75%
col1, col2, col3 = st.columns([2, 3, 2])  # 2/7, 3/7, 2/7
        """,
            language="python",
        )

    # Tabs Pattern
    st.markdown("---")
    st.markdown("### Tab Navigation")
    st.markdown("Use tabs to organize related content without overwhelming the user.")

    demo_tabs = st.tabs(["Overview", "Details", "Settings"])

    with demo_tabs[0]:
        st.markdown("**Overview Tab**")
        st.markdown("High-level summary and key metrics go here.")

    with demo_tabs[1]:
        st.markdown("**Details Tab**")
        st.markdown("Detailed information and analysis.")

    with demo_tabs[2]:
        st.markdown("**Settings Tab**")
        st.markdown("Configuration options and controls.")

    with st.expander("View Code"):
        st.code(
            """
tabs = st.tabs(["Overview", "Details", "Settings"])

with tabs[0]:
    st.markdown("Overview content...")

with tabs[1]:
    st.markdown("Details content...")

with tabs[2]:
    st.markdown("Settings content...")
        """,
            language="python",
        )

    # Expanders Pattern
    st.markdown("---")
    st.markdown("### Expanders (Accordions)")
    st.markdown("Hide detailed content until the user needs it.")

    with st.expander("Expandable Section 1", expanded=True):
        st.markdown("This expander is open by default (`expanded=True`).")
        st.markdown("Use for important content you want visible initially.")

    with st.expander("Expandable Section 2"):
        st.markdown("This expander is closed by default.")
        st.markdown("Use for supplementary information or advanced options.")

    with st.expander("View Code"):
        st.code(
            """
# Open by default
with st.expander("Section Title", expanded=True):
    st.markdown("Content...")

# Closed by default
with st.expander("Section Title"):
    st.markdown("Content...")
        """,
            language="python",
        )

    # Spacing Pattern
    st.markdown("---")
    st.markdown("### Spacing & Dividers")

    st.markdown("Use horizontal rules for visual separation:")
    st.markdown("---")
    st.markdown("Content after divider")

    st.markdown("Use custom spacing with HTML:")
    st.markdown("<div style='height: 40px'></div>", unsafe_allow_html=True)
    st.markdown("Content with 40px spacing above")

    with st.expander("View Code"):
        st.code(
            """
# Horizontal rule
st.markdown("---")

# Custom spacing (use sparingly)
st.markdown("<div style='height: 40px'></div>", unsafe_allow_html=True)
        """,
            language="python",
        )

    # Full Page Example
    st.markdown("---")
    st.markdown("### Complete Page Pattern")
    st.markdown("Putting it all together - a typical module structure:")

    with st.expander("View Full Module Template"):
        st.code(
            '''
def render() -> None:
    """Module entry point."""
    # 1. Title and description
    st.title("Module Name")
    st.markdown("Brief description of what this module does.")

    # 2. Hero section (optional)
    ui.hero_section(
        "Welcome to Module",
        "Compelling subtitle that explains the value proposition."
    )

    # 3. Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ui.card_metric("Metric 1", "1,234", "+12%")
    with col2:
        ui.card_metric("Metric 2", "567", "+8%")
    with col3:
        ui.card_metric("Metric 3", "89%", "+3%")
    with col4:
        ui.card_metric("Metric 4", "$45K", "+15%")

    # 4. Main content with tabs
    tabs = st.tabs(["Analysis", "Settings", "Export"])

    with tabs[0]:
        ui.section_header("Analysis", "Detailed insights and visualizations")
        # Main content here

    with tabs[1]:
        ui.section_header("Settings", "Configure your parameters")
        # Settings form here

    with tabs[2]:
        ui.section_header("Export", "Download your results")
        # Export options here

    # 5. Footer (handled by app.py, but you can add module-specific footer)
        ''',
            language="python",
        )

    # Design Principles
    st.markdown("---")
    st.markdown("### Design Principles")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        **Consistency**
        - Use the same component for the same purpose
        - Maintain consistent spacing (multiples of 8px)
        - Follow established patterns across modules

        **Hierarchy**
        - Use heading levels appropriately (H1 → H2 → H3)
        - Employ visual weight to guide attention
        - Group related content together
        """
        )

    with col2:
        st.markdown(
            """
        **Accessibility**
        - All colors meet WCAG AAA standards
        - Provide descriptive labels for all inputs
        - Use semantic HTML where possible

        **Performance**
        - Cache expensive operations with `@st.cache_data`
        - Lazy load heavy components in tabs/expanders
        - Minimize recomputation on reruns
        """
        )
