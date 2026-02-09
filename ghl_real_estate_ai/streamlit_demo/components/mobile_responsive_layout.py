"""
Mobile Responsive Layout Manager for GHL Real Estate AI

Provides intelligent layout management with:
- CSS Grid responsive design
- Mobile-first approach
- Adaptive component sizing
- Touch-friendly interfaces
- Performance optimization
"""

from typing import Any, Dict, List, Optional

import streamlit as st


def inject_responsive_css():
    """Inject comprehensive responsive CSS"""
    st.markdown(
        "\n    <style>\n    /* Mobile Responsive Framework */\n    :root {\n        --mobile-breakpoint: 768px;\n        --tablet-breakpoint: 1024px;\n        --desktop-breakpoint: 1200px;\n\n        --spacing-xs: 0.25rem;\n        --spacing-sm: 0.5rem;\n        --spacing-md: 1rem;\n        --spacing-lg: 1.5rem;\n        --spacing-xl: 2rem;\n\n        --border-radius-sm: 8px;\n        --border-radius-md: 12px;\n        --border-radius-lg: 16px;\n        --border-radius-xl: 20px;\n\n        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1);\n        --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.1);\n        --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.15);\n        --shadow-xl: 0 12px 32px rgba(0, 0, 0, 0.2);\n    }\n\n    /* Global Responsive Container */\n    .responsive-container {\n        width: 100%;\n        max-width: 1200px;\n        margin: 0 auto;\n        padding: var(--spacing-md);\n        box-sizing: border-box;\n    }\n\n    /* CSS Grid Layout System */\n    .grid-container {\n        display: grid;\n        grid-template-columns: repeat(12, 1fr);\n        gap: var(--spacing-md);\n        width: 100%;\n        margin: var(--spacing-md) 0;\n    }\n\n    .grid-item {\n        grid-column: span 12;\n        min-height: 0;\n        overflow: hidden;\n    }\n\n    /* Responsive Grid Spans */\n    .col-1 { grid-column: span 1; }\n    .col-2 { grid-column: span 2; }\n    .col-3 { grid-column: span 3; }\n    .col-4 { grid-column: span 4; }\n    .col-5 { grid-column: span 5; }\n    .col-6 { grid-column: span 6; }\n    .col-7 { grid-column: span 7; }\n    .col-8 { grid-column: span 8; }\n    .col-9 { grid-column: span 9; }\n    .col-10 { grid-column: span 10; }\n    .col-11 { grid-column: span 11; }\n    .col-12 { grid-column: span 12; }\n\n    /* Mobile-First Responsive Design */\n    @media (max-width: 767px) {\n        .responsive-container {\n            padding: var(--spacing-sm);\n        }\n\n        .grid-container {\n            gap: var(--spacing-sm);\n            margin: var(--spacing-sm) 0;\n        }\n\n        /* Mobile: All items full width except specified */\n        .grid-item,\n        .col-1, .col-2, .col-3, .col-4, .col-5, .col-6,\n        .col-7, .col-8, .col-9, .col-10, .col-11, .col-12 {\n            grid-column: span 12;\n        }\n\n        /* Mobile specific classes */\n        .col-mobile-6 { grid-column: span 6; }\n        .col-mobile-4 { grid-column: span 4; }\n        .col-mobile-3 { grid-column: span 3; }\n\n        /* Mobile layout adjustments */\n        .mobile-stack {\n            display: flex !important;\n            flex-direction: column !important;\n            gap: var(--spacing-sm) !important;\n        }\n\n        .mobile-hide {\n            display: none !important;\n        }\n\n        .mobile-center {\n            text-align: center !important;\n        }\n\n        /* Touch-friendly buttons */\n        .stButton > button {\n            min-height: 44px !important;\n            touch-action: manipulation;\n            -webkit-tap-highlight-color: transparent;\n        }\n\n        /* Larger form inputs */\n        .stSelectbox > div > div {\n            min-height: 44px !important;\n        }\n\n        .stTextInput > div > div > input {\n            min-height: 44px !important;\n        }\n    }\n\n    /* Tablet Responsive Design */\n    @media (min-width: 768px) and (max-width: 1023px) {\n        .grid-container {\n            grid-template-columns: repeat(8, 1fr);\n        }\n\n        /* Tablet specific spans */\n        .col-tablet-1 { grid-column: span 1; }\n        .col-tablet-2 { grid-column: span 2; }\n        .col-tablet-3 { grid-column: span 3; }\n        .col-tablet-4 { grid-column: span 4; }\n        .col-tablet-5 { grid-column: span 5; }\n        .col-tablet-6 { grid-column: span 6; }\n        .col-tablet-7 { grid-column: span 7; }\n        .col-tablet-8 { grid-column: span 8; }\n\n        .tablet-hide {\n            display: none !important;\n        }\n\n        .tablet-show {\n            display: block !important;\n        }\n    }\n\n    /* Desktop Responsive Design */\n    @media (min-width: 1024px) {\n        .desktop-hide {\n            display: none !important;\n        }\n\n        .desktop-show {\n            display: block !important;\n        }\n\n        /* Desktop specific spans maintain full 12-column grid */\n        .col-desktop-1 { grid-column: span 1; }\n        .col-desktop-2 { grid-column: span 2; }\n        .col-desktop-3 { grid-column: span 3; }\n        .col-desktop-4 { grid-column: span 4; }\n        .col-desktop-5 { grid-column: span 5; }\n        .col-desktop-6 { grid-column: span 6; }\n        .col-desktop-7 { grid-column: span 7; }\n        .col-desktop-8 { grid-column: span 8; }\n        .col-desktop-9 { grid-column: span 9; }\n        .col-desktop-10 { grid-column: span 10; }\n        .col-desktop-11 { grid-column: span 11; }\n        .col-desktop-12 { grid-column: span 12; }\n    }\n\n    /* Large Desktop */\n    @media (min-width: 1200px) {\n        .responsive-container {\n            padding: var(--spacing-lg);\n        }\n\n        .grid-container {\n            gap: var(--spacing-lg);\n        }\n    }\n\n    /* Component-Specific Mobile Optimizations */\n    .card-mobile {\n        border-radius: var(--border-radius-md) !important;\n        margin: var(--spacing-sm) 0 !important;\n        padding: var(--spacing-md) !important;\n        box-shadow: var(--shadow-sm) !important;\n    }\n\n    @media (max-width: 767px) {\n        .card-mobile {\n            border-radius: var(--border-radius-sm) !important;\n            margin: var(--spacing-xs) 0 !important;\n            padding: var(--spacing-sm) !important;\n        }\n    }\n\n    /* Chart Responsive Containers */\n    .chart-responsive {\n        width: 100% !important;\n        height: auto !important;\n        min-height: 300px;\n    }\n\n    @media (max-width: 767px) {\n        .chart-responsive {\n            min-height: 250px;\n        }\n    }\n\n    /* Navigation Responsive */\n    .nav-responsive {\n        display: flex;\n        flex-wrap: wrap;\n        gap: var(--spacing-sm);\n        justify-content: center;\n        margin: var(--spacing-md) 0;\n    }\n\n    @media (max-width: 767px) {\n        .nav-responsive {\n            flex-direction: column;\n            gap: var(--spacing-xs);\n        }\n\n        .nav-responsive .stButton {\n            width: 100%;\n        }\n    }\n\n    /* Text Responsive Sizing */\n    .text-responsive {\n        font-size: 1rem;\n        line-height: 1.5;\n    }\n\n    .text-responsive.large {\n        font-size: 1.25rem;\n    }\n\n    .text-responsive.small {\n        font-size: 0.875rem;\n    }\n\n    @media (max-width: 767px) {\n        .text-responsive {\n            font-size: 0.875rem;\n        }\n\n        .text-responsive.large {\n            font-size: 1rem;\n        }\n\n        .text-responsive.small {\n            font-size: 0.75rem;\n        }\n    }\n\n    /* Performance Optimizations */\n    .performance-optimized {\n        will-change: transform;\n        transform: translateZ(0);\n        -webkit-font-smoothing: antialiased;\n        -moz-osx-font-smoothing: grayscale;\n    }\n\n    /* Scrollable Content on Mobile */\n    .scroll-mobile {\n        overflow-x: auto;\n        -webkit-overflow-scrolling: touch;\n        scrollbar-width: thin;\n        scrollbar-color: rgba(0, 0, 0, 0.2) transparent;\n    }\n\n    .scroll-mobile::-webkit-scrollbar {\n        height: 4px;\n    }\n\n    .scroll-mobile::-webkit-scrollbar-track {\n        background: transparent;\n    }\n\n    .scroll-mobile::-webkit-scrollbar-thumb {\n        background: rgba(0, 0, 0, 0.2);\n        border-radius: 4px;\n    }\n\n    /* Accessibility Improvements */\n    @media (prefers-reduced-motion: reduce) {\n        * {\n            animation-duration: 0.01ms !important;\n            animation-iteration-count: 1 !important;\n            transition-duration: 0.01ms !important;\n        }\n    }\n\n    /* High Contrast Mode Support */\n    @media (prefers-contrast: high) {\n        .card-mobile {\n            border: 2px solid currentColor !important;\n        }\n\n        .stButton > button {\n            border: 2px solid currentColor !important;\n        }\n    }\n\n    /* Print Styles */\n    @media print {\n        .mobile-hide, .tablet-hide, .desktop-hide {\n            display: none !important;\n        }\n\n        .responsive-container {\n            padding: 0 !important;\n            box-shadow: none !important;\n        }\n\n        .grid-container {\n            display: block !important;\n        }\n\n        .grid-item {\n            break-inside: avoid;\n            margin-bottom: var(--spacing-md);\n        }\n    }\n\n    /* Custom Streamlit Overrides for Mobile */\n    @media (max-width: 767px) {\n        /* Hide Streamlit branding on mobile for cleaner look */\n        .css-1d391kg {\n            padding: 0.5rem !important;\n        }\n\n        /* Adjust sidebar on mobile */\n        .css-1cypcdb {\n            width: 100% !important;\n        }\n\n        /* Mobile-friendly metrics */\n        .metric-container {\n            margin: 0.25rem 0 !important;\n        }\n\n        /* Smaller charts on mobile */\n        .js-plotly-plot {\n            margin: 0.5rem 0 !important;\n        }\n    }\n\n    /* Dark Mode Responsive Adjustments */\n    @media (prefers-color-scheme: dark) {\n        :root {\n            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);\n            --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.3);\n            --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.4);\n            --shadow-xl: 0 12px 32px rgba(0, 0, 0, 0.5);\n        }\n    }\n\n    /* Orientation Change Support */\n    @media (orientation: landscape) and (max-height: 600px) {\n        .responsive-container {\n            padding: var(--spacing-sm) !important;\n        }\n\n        .grid-container {\n            gap: var(--spacing-sm) !important;\n        }\n    }\n    </style>\n    ",
        unsafe_allow_html=True,
    )


class ResponsiveLayoutManager:
    """Manages responsive layouts with mobile-first design"""

    def __init__(self):
        self.breakpoints = {"mobile": 768, "tablet": 1024, "desktop": 1200}
        inject_responsive_css()
        self._detect_device()

    def _detect_device(self):
        """Detect device type using JavaScript (approximation)"""
        if "device_type" not in st.session_state:
            st.session_state.device_type = "desktop"
            st.session_state.is_mobile = False
            st.session_state.is_tablet = False

    def create_responsive_grid(self, layout_config: Dict[str, Any]) -> str:
        """Create responsive grid layout"""
        grid_id = f"grid_{hash(str(layout_config))}"
        mobile_cols = layout_config.get("mobile_columns", 1)
        tablet_cols = layout_config.get("tablet_columns", 2)
        desktop_cols = layout_config.get("desktop_columns", 3)
        gap = layout_config.get("gap", "md")
        grid_html = f'\n        <div class="grid-container responsive-grid-{grid_id}" id="{grid_id}">\n        '
        return grid_html

    def responsive_columns(self, mobile: int = 1, tablet: Optional[int] = None, desktop: Optional[int] = None) -> List:
        """Create responsive columns that adapt to screen size"""
        tablet = tablet or min(mobile * 2, 3)
        desktop = desktop or min(tablet * 2, 4)
        columns = st.columns(desktop)
        if "responsive_layout" not in st.session_state:
            st.session_state.responsive_layout = {}
        st.session_state.responsive_layout["current_columns"] = {"mobile": mobile, "tablet": tablet, "desktop": desktop}
        return columns

    def mobile_card_container(self, content_func, **kwargs):
        """Create mobile-optimized card container"""
        title = kwargs.get("title", "")
        mobile_height = kwargs.get("mobile_height", "auto")
        padding = kwargs.get("padding", "md")
        st.markdown(f'<div class="card-mobile" style="height: {mobile_height};">', unsafe_allow_html=True)
        if title:
            st.markdown(f'<h3 class="text-responsive large">{title}</h3>', unsafe_allow_html=True)
        content_func()
        st.markdown("</div>", unsafe_allow_html=True)

    def adaptive_chart_height(self, base_height: int = 400) -> int:
        """Get adaptive chart height based on screen size"""
        device_type = st.session_state.get("device_type", "desktop")
        height_map = {"mobile": int(base_height * 0.7), "tablet": int(base_height * 0.85), "desktop": base_height}
        return height_map.get(device_type, base_height)

    def mobile_navigation(self, nav_items: List[Dict[str, str]], current_selection: str = None):
        """Create mobile-friendly navigation"""
        st.markdown('<div class="nav-responsive">', unsafe_allow_html=True)
        if st.session_state.get("is_mobile", False):
            options = [item["label"] for item in nav_items]
            current_index = 0
            if current_selection:
                for i, item in enumerate(nav_items):
                    if item["key"] == current_selection:
                        current_index = i
                        break
            selected = st.selectbox("Navigate to:", options, index=current_index, key="mobile_nav")
            for item in nav_items:
                if item["label"] == selected:
                    return item["key"]
        else:
            columns = st.columns(len(nav_items))
            for i, item in enumerate(nav_items):
                with columns[i]:
                    button_type = "primary" if item["key"] == current_selection else "secondary"
                    if st.button(item["label"], key=f"nav_{item['key']}", type=button_type, use_container_width=True):
                        return item["key"]
        st.markdown("</div>", unsafe_allow_html=True)
        return current_selection

    def responsive_metrics_grid(self, metrics: List[Dict[str, Any]]):
        """Create responsive metrics grid"""
        num_metrics = len(metrics)
        device_type = st.session_state.get("device_type", "desktop")
        if device_type == "mobile":
            cols_per_row = 2
        elif device_type == "tablet":
            cols_per_row = min(3, num_metrics)
        else:
            cols_per_row = min(4, num_metrics)
        for i in range(0, num_metrics, cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                metric_idx = i + j
                if metric_idx < num_metrics:
                    metric = metrics[metric_idx]
                    with cols[j]:
                        st.metric(
                            label=metric["label"],
                            value=metric["value"],
                            delta=metric.get("delta", None),
                            delta_color=metric.get("delta_color", "normal"),
                        )

    def mobile_optimized_dataframe(self, df, **kwargs):
        """Render mobile-optimized dataframe"""
        if st.session_state.get("is_mobile", False):
            max_cols = kwargs.get("mobile_max_columns", 3)
            if len(df.columns) > max_cols:
                all_columns = df.columns.tolist()
                default_columns = all_columns[:max_cols]
                selected_columns = st.multiselect(
                    "Select columns to display:", all_columns, default=default_columns, key="mobile_df_columns"
                )
                if selected_columns:
                    df_display = df[selected_columns]
                else:
                    df_display = df.iloc[:, :max_cols]
            else:
                df_display = df
            st.markdown('<div class="scroll-mobile">', unsafe_allow_html=True)
            st.dataframe(df_display, use_container_width=True, **kwargs)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.dataframe(df, use_container_width=True, **kwargs)

    def responsive_plotly_chart(self, fig, **kwargs):
        """Render responsive Plotly chart"""
        base_height = kwargs.get("height", 400)
        adaptive_height = self.adaptive_chart_height(base_height)
        if st.session_state.get("is_mobile", False):
            fig.update_layout(
                height=adaptive_height,
                margin=dict(l=20, r=20, t=30, b=20),
                font=dict(size=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            )
        else:
            fig.update_layout(height=adaptive_height)
        st.markdown('<div class="chart-responsive">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, **kwargs)
        st.markdown("</div>", unsafe_allow_html=True)

    def device_specific_content(self, mobile_content=None, tablet_content=None, desktop_content=None):
        """Render device-specific content"""
        device_type = st.session_state.get("device_type", "desktop")
        if device_type == "mobile" and mobile_content:
            mobile_content()
        elif device_type == "tablet" and tablet_content:
            tablet_content()
        elif desktop_content:
            desktop_content()

    @st.cache_data(ttl=300)
    def get_responsive_sidebar_config(self) -> Dict[str, Any]:
        """Get sidebar configuration based on device"""
        device_type = st.session_state.get("device_type", "desktop")
        if device_type == "mobile":
            return {"collapsed": True, "show_controls": False, "compact_mode": True}
        elif device_type == "tablet":
            return {"collapsed": False, "show_controls": True, "compact_mode": True}
        else:
            return {"collapsed": False, "show_controls": True, "compact_mode": False}

    def mobile_friendly_tabs(self, tab_data: List[Dict[str, Any]], default_tab: str = None):
        """Create mobile-friendly tab navigation"""
        if st.session_state.get("is_mobile", False):
            tab_labels = [tab["label"] for tab in tab_data]
            tab_keys = [tab["key"] for tab in tab_data]
            default_index = 0
            if default_tab:
                try:
                    default_index = tab_keys.index(default_tab)
                except ValueError:
                    pass
            selected_label = st.selectbox("Select section:", tab_labels, index=default_index, key="mobile_tabs")
            for tab in tab_data:
                if tab["label"] == selected_label:
                    return (tab["key"], tab["content"])
        else:
            tab_keys = [tab["key"] for tab in tab_data]
            tab_labels = [tab["label"] for tab in tab_data]
            cols = st.columns(len(tab_data))
            selected_tab = default_tab or tab_keys[0]
            for i, (tab_key, tab_label) in enumerate(zip(tab_keys, tab_labels)):
                with cols[i]:
                    button_type = (
                        "primary" if tab_key == st.session_state.get("current_tab", default_tab) else "secondary"
                    )
                    if st.button(tab_label, key=f"tab_{tab_key}", type=button_type, use_container_width=True):
                        st.session_state.current_tab = tab_key
                        selected_tab = tab_key
            for tab in tab_data:
                if tab["key"] == selected_tab:
                    return (tab["key"], tab["content"])
        return (tab_data[0]["key"], tab_data[0]["content"])


layout_manager = ResponsiveLayoutManager()


@st.cache_data(ttl=300)
def get_layout_manager() -> ResponsiveLayoutManager:
    """Get the global layout manager instance"""
    return layout_manager


def responsive_container(content_func):
    """Decorator for responsive containers"""

    def wrapper(*args, **kwargs):
        st.markdown('<div class="responsive-container">', unsafe_allow_html=True)
        result = content_func(*args, **kwargs)
        st.markdown("</div>", unsafe_allow_html=True)
        return result

    return wrapper
