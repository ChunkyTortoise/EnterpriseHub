"""
Mobile Responsive Layout Manager for GHL Real Estate AI

Provides intelligent layout management with:
- CSS Grid responsive design
- Mobile-first approach
- Adaptive component sizing
- Touch-friendly interfaces
- Performance optimization
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
import json

def inject_responsive_css():
    """Inject comprehensive responsive CSS"""
    st.markdown("""
    <style>
    /* Mobile Responsive Framework */
    :root {
        --mobile-breakpoint: 768px;
        --tablet-breakpoint: 1024px;
        --desktop-breakpoint: 1200px;

        --spacing-xs: 0.25rem;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;

        --border-radius-sm: 8px;
        --border-radius-md: 12px;
        --border-radius-lg: 16px;
        --border-radius-xl: 20px;

        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1);
        --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.15);
        --shadow-xl: 0 12px 32px rgba(0, 0, 0, 0.2);
    }

    /* Global Responsive Container */
    .responsive-container {
        width: 100%;
        max-width: 1200px;
        margin: 0 auto;
        padding: var(--spacing-md);
        box-sizing: border-box;
    }

    /* CSS Grid Layout System */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: var(--spacing-md);
        width: 100%;
        margin: var(--spacing-md) 0;
    }

    .grid-item {
        grid-column: span 12;
        min-height: 0;
        overflow: hidden;
    }

    /* Responsive Grid Spans */
    .col-1 { grid-column: span 1; }
    .col-2 { grid-column: span 2; }
    .col-3 { grid-column: span 3; }
    .col-4 { grid-column: span 4; }
    .col-5 { grid-column: span 5; }
    .col-6 { grid-column: span 6; }
    .col-7 { grid-column: span 7; }
    .col-8 { grid-column: span 8; }
    .col-9 { grid-column: span 9; }
    .col-10 { grid-column: span 10; }
    .col-11 { grid-column: span 11; }
    .col-12 { grid-column: span 12; }

    /* Mobile-First Responsive Design */
    @media (max-width: 767px) {
        .responsive-container {
            padding: var(--spacing-sm);
        }

        .grid-container {
            gap: var(--spacing-sm);
            margin: var(--spacing-sm) 0;
        }

        /* Mobile: All items full width except specified */
        .grid-item,
        .col-1, .col-2, .col-3, .col-4, .col-5, .col-6,
        .col-7, .col-8, .col-9, .col-10, .col-11, .col-12 {
            grid-column: span 12;
        }

        /* Mobile specific classes */
        .col-mobile-6 { grid-column: span 6; }
        .col-mobile-4 { grid-column: span 4; }
        .col-mobile-3 { grid-column: span 3; }

        /* Mobile layout adjustments */
        .mobile-stack {
            display: flex !important;
            flex-direction: column !important;
            gap: var(--spacing-sm) !important;
        }

        .mobile-hide {
            display: none !important;
        }

        .mobile-center {
            text-align: center !important;
        }

        /* Touch-friendly buttons */
        .stButton > button {
            min-height: 44px !important;
            touch-action: manipulation;
            -webkit-tap-highlight-color: transparent;
        }

        /* Larger form inputs */
        .stSelectbox > div > div {
            min-height: 44px !important;
        }

        .stTextInput > div > div > input {
            min-height: 44px !important;
        }
    }

    /* Tablet Responsive Design */
    @media (min-width: 768px) and (max-width: 1023px) {
        .grid-container {
            grid-template-columns: repeat(8, 1fr);
        }

        /* Tablet specific spans */
        .col-tablet-1 { grid-column: span 1; }
        .col-tablet-2 { grid-column: span 2; }
        .col-tablet-3 { grid-column: span 3; }
        .col-tablet-4 { grid-column: span 4; }
        .col-tablet-5 { grid-column: span 5; }
        .col-tablet-6 { grid-column: span 6; }
        .col-tablet-7 { grid-column: span 7; }
        .col-tablet-8 { grid-column: span 8; }

        .tablet-hide {
            display: none !important;
        }

        .tablet-show {
            display: block !important;
        }
    }

    /* Desktop Responsive Design */
    @media (min-width: 1024px) {
        .desktop-hide {
            display: none !important;
        }

        .desktop-show {
            display: block !important;
        }

        /* Desktop specific spans maintain full 12-column grid */
        .col-desktop-1 { grid-column: span 1; }
        .col-desktop-2 { grid-column: span 2; }
        .col-desktop-3 { grid-column: span 3; }
        .col-desktop-4 { grid-column: span 4; }
        .col-desktop-5 { grid-column: span 5; }
        .col-desktop-6 { grid-column: span 6; }
        .col-desktop-7 { grid-column: span 7; }
        .col-desktop-8 { grid-column: span 8; }
        .col-desktop-9 { grid-column: span 9; }
        .col-desktop-10 { grid-column: span 10; }
        .col-desktop-11 { grid-column: span 11; }
        .col-desktop-12 { grid-column: span 12; }
    }

    /* Large Desktop */
    @media (min-width: 1200px) {
        .responsive-container {
            padding: var(--spacing-lg);
        }

        .grid-container {
            gap: var(--spacing-lg);
        }
    }

    /* Component-Specific Mobile Optimizations */
    .card-mobile {
        border-radius: var(--border-radius-md) !important;
        margin: var(--spacing-sm) 0 !important;
        padding: var(--spacing-md) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    @media (max-width: 767px) {
        .card-mobile {
            border-radius: var(--border-radius-sm) !important;
            margin: var(--spacing-xs) 0 !important;
            padding: var(--spacing-sm) !important;
        }
    }

    /* Chart Responsive Containers */
    .chart-responsive {
        width: 100% !important;
        height: auto !important;
        min-height: 300px;
    }

    @media (max-width: 767px) {
        .chart-responsive {
            min-height: 250px;
        }
    }

    /* Navigation Responsive */
    .nav-responsive {
        display: flex;
        flex-wrap: wrap;
        gap: var(--spacing-sm);
        justify-content: center;
        margin: var(--spacing-md) 0;
    }

    @media (max-width: 767px) {
        .nav-responsive {
            flex-direction: column;
            gap: var(--spacing-xs);
        }

        .nav-responsive .stButton {
            width: 100%;
        }
    }

    /* Text Responsive Sizing */
    .text-responsive {
        font-size: 1rem;
        line-height: 1.5;
    }

    .text-responsive.large {
        font-size: 1.25rem;
    }

    .text-responsive.small {
        font-size: 0.875rem;
    }

    @media (max-width: 767px) {
        .text-responsive {
            font-size: 0.875rem;
        }

        .text-responsive.large {
            font-size: 1rem;
        }

        .text-responsive.small {
            font-size: 0.75rem;
        }
    }

    /* Performance Optimizations */
    .performance-optimized {
        will-change: transform;
        transform: translateZ(0);
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Scrollable Content on Mobile */
    .scroll-mobile {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
        scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
    }

    .scroll-mobile::-webkit-scrollbar {
        height: 4px;
    }

    .scroll-mobile::-webkit-scrollbar-track {
        background: transparent;
    }

    .scroll-mobile::-webkit-scrollbar-thumb {
        background: rgba(0, 0, 0, 0.2);
        border-radius: 4px;
    }

    /* Accessibility Improvements */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }

    /* High Contrast Mode Support */
    @media (prefers-contrast: high) {
        .card-mobile {
            border: 2px solid currentColor !important;
        }

        .stButton > button {
            border: 2px solid currentColor !important;
        }
    }

    /* Print Styles */
    @media print {
        .mobile-hide, .tablet-hide, .desktop-hide {
            display: none !important;
        }

        .responsive-container {
            padding: 0 !important;
            box-shadow: none !important;
        }

        .grid-container {
            display: block !important;
        }

        .grid-item {
            break-inside: avoid;
            margin-bottom: var(--spacing-md);
        }
    }

    /* Custom Streamlit Overrides for Mobile */
    @media (max-width: 767px) {
        /* Hide Streamlit branding on mobile for cleaner look */
        .css-1d391kg {
            padding: 0.5rem !important;
        }

        /* Adjust sidebar on mobile */
        .css-1cypcdb {
            width: 100% !important;
        }

        /* Mobile-friendly metrics */
        .metric-container {
            margin: 0.25rem 0 !important;
        }

        /* Smaller charts on mobile */
        .js-plotly-plot {
            margin: 0.5rem 0 !important;
        }
    }

    /* Dark Mode Responsive Adjustments */
    @media (prefers-color-scheme: dark) {
        :root {
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
            --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.3);
            --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.4);
            --shadow-xl: 0 12px 32px rgba(0, 0, 0, 0.5);
        }
    }

    /* Orientation Change Support */
    @media (orientation: landscape) and (max-height: 600px) {
        .responsive-container {
            padding: var(--spacing-sm) !important;
        }

        .grid-container {
            gap: var(--spacing-sm) !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

class ResponsiveLayoutManager:
    """Manages responsive layouts with mobile-first design"""

    def __init__(self):
        self.breakpoints = {
            'mobile': 768,
            'tablet': 1024,
            'desktop': 1200
        }

        # Inject responsive CSS
        inject_responsive_css()

        # Initialize device detection
        self._detect_device()

    def _detect_device(self):
        """Detect device type using JavaScript (approximation)"""
        # In a real implementation, this would use JavaScript to detect screen size
        # For demo purposes, we'll use session state
        if 'device_type' not in st.session_state:
            st.session_state.device_type = 'desktop'  # Default
            st.session_state.is_mobile = False
            st.session_state.is_tablet = False

    def create_responsive_grid(self, layout_config: Dict[str, Any]) -> str:
        """Create responsive grid layout"""
        grid_id = f"grid_{hash(str(layout_config))}"

        mobile_cols = layout_config.get('mobile_columns', 1)
        tablet_cols = layout_config.get('tablet_columns', 2)
        desktop_cols = layout_config.get('desktop_columns', 3)

        gap = layout_config.get('gap', 'md')

        grid_html = f"""
        <div class="grid-container responsive-grid-{grid_id}" id="{grid_id}">
        """

        return grid_html

    def responsive_columns(self,
                         mobile: int = 1,
                         tablet: Optional[int] = None,
                         desktop: Optional[int] = None) -> List:
        """Create responsive columns that adapt to screen size"""

        # Default values
        tablet = tablet or min(mobile * 2, 3)
        desktop = desktop or min(tablet * 2, 4)

        # For Streamlit, we'll use the desktop value but add responsive classes
        columns = st.columns(desktop)

        # Add responsive metadata to session state for components to use
        if 'responsive_layout' not in st.session_state:
            st.session_state.responsive_layout = {}

        st.session_state.responsive_layout['current_columns'] = {
            'mobile': mobile,
            'tablet': tablet,
            'desktop': desktop
        }

        return columns

    def mobile_card_container(self, content_func, **kwargs):
        """Create mobile-optimized card container"""

        # Extract card options
        title = kwargs.get('title', '')
        mobile_height = kwargs.get('mobile_height', 'auto')
        padding = kwargs.get('padding', 'md')

        # Start container
        st.markdown(f'<div class="card-mobile" style="height: {mobile_height};">',
                   unsafe_allow_html=True)

        if title:
            st.markdown(f'<h3 class="text-responsive large">{title}</h3>',
                       unsafe_allow_html=True)

        # Render content
        content_func()

        # End container
        st.markdown('</div>', unsafe_allow_html=True)

    def adaptive_chart_height(self, base_height: int = 400) -> int:
        """Get adaptive chart height based on screen size"""
        device_type = st.session_state.get('device_type', 'desktop')

        height_map = {
            'mobile': int(base_height * 0.7),
            'tablet': int(base_height * 0.85),
            'desktop': base_height
        }

        return height_map.get(device_type, base_height)

    def mobile_navigation(self, nav_items: List[Dict[str, str]], current_selection: str = None):
        """Create mobile-friendly navigation"""

        st.markdown('<div class="nav-responsive">', unsafe_allow_html=True)

        # For mobile, create a single-column layout
        if st.session_state.get('is_mobile', False):
            # Use selectbox for mobile navigation
            options = [item['label'] for item in nav_items]
            current_index = 0

            if current_selection:
                for i, item in enumerate(nav_items):
                    if item['key'] == current_selection:
                        current_index = i
                        break

            selected = st.selectbox(
                "Navigate to:",
                options,
                index=current_index,
                key="mobile_nav"
            )

            # Return the selected key
            for item in nav_items:
                if item['label'] == selected:
                    return item['key']
        else:
            # Desktop/tablet horizontal buttons
            columns = st.columns(len(nav_items))

            for i, item in enumerate(nav_items):
                with columns[i]:
                    button_type = "primary" if item['key'] == current_selection else "secondary"
                    if st.button(
                        item['label'],
                        key=f"nav_{item['key']}",
                        type=button_type,
                        use_container_width=True
                    ):
                        return item['key']

        st.markdown('</div>', unsafe_allow_html=True)

        return current_selection

    def responsive_metrics_grid(self, metrics: List[Dict[str, Any]]):
        """Create responsive metrics grid"""

        # Determine columns based on number of metrics and device
        num_metrics = len(metrics)
        device_type = st.session_state.get('device_type', 'desktop')

        if device_type == 'mobile':
            cols_per_row = 2
        elif device_type == 'tablet':
            cols_per_row = min(3, num_metrics)
        else:
            cols_per_row = min(4, num_metrics)

        # Create metric rows
        for i in range(0, num_metrics, cols_per_row):
            cols = st.columns(cols_per_row)

            for j in range(cols_per_row):
                metric_idx = i + j
                if metric_idx < num_metrics:
                    metric = metrics[metric_idx]

                    with cols[j]:
                        st.metric(
                            label=metric['label'],
                            value=metric['value'],
                            delta=metric.get('delta', None),
                            delta_color=metric.get('delta_color', 'normal')
                        )

    def mobile_optimized_dataframe(self, df, **kwargs):
        """Render mobile-optimized dataframe"""

        if st.session_state.get('is_mobile', False):
            # For mobile, show fewer columns and add horizontal scroll
            max_cols = kwargs.get('mobile_max_columns', 3)

            if len(df.columns) > max_cols:
                # Show column selector for mobile
                all_columns = df.columns.tolist()

                # Always include first column (usually ID or name)
                default_columns = all_columns[:max_cols]

                selected_columns = st.multiselect(
                    "Select columns to display:",
                    all_columns,
                    default=default_columns,
                    key="mobile_df_columns"
                )

                if selected_columns:
                    df_display = df[selected_columns]
                else:
                    df_display = df.iloc[:, :max_cols]
            else:
                df_display = df

            # Wrap in scrollable container
            st.markdown('<div class="scroll-mobile">', unsafe_allow_html=True)
            st.dataframe(df_display, use_container_width=True, **kwargs)
            st.markdown('</div>', unsafe_allow_html=True)

        else:
            # Regular dataframe for desktop/tablet
            st.dataframe(df, use_container_width=True, **kwargs)

    def responsive_plotly_chart(self, fig, **kwargs):
        """Render responsive Plotly chart"""

        # Get adaptive height
        base_height = kwargs.get('height', 400)
        adaptive_height = self.adaptive_chart_height(base_height)

        # Update figure layout for mobile optimization
        if st.session_state.get('is_mobile', False):
            fig.update_layout(
                height=adaptive_height,
                margin=dict(l=20, r=20, t=30, b=20),
                font=dict(size=10),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                )
            )
        else:
            fig.update_layout(height=adaptive_height)

        # Add responsive container
        st.markdown('<div class="chart-responsive">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, **kwargs)
        st.markdown('</div>', unsafe_allow_html=True)

    def device_specific_content(self,
                              mobile_content=None,
                              tablet_content=None,
                              desktop_content=None):
        """Render device-specific content"""

        device_type = st.session_state.get('device_type', 'desktop')

        if device_type == 'mobile' and mobile_content:
            mobile_content()
        elif device_type == 'tablet' and tablet_content:
            tablet_content()
        elif desktop_content:
            desktop_content()

    def get_responsive_sidebar_config(self) -> Dict[str, Any]:
        """Get sidebar configuration based on device"""

        device_type = st.session_state.get('device_type', 'desktop')

        if device_type == 'mobile':
            return {
                'collapsed': True,
                'show_controls': False,
                'compact_mode': True
            }
        elif device_type == 'tablet':
            return {
                'collapsed': False,
                'show_controls': True,
                'compact_mode': True
            }
        else:
            return {
                'collapsed': False,
                'show_controls': True,
                'compact_mode': False
            }

    def mobile_friendly_tabs(self, tab_data: List[Dict[str, Any]], default_tab: str = None):
        """Create mobile-friendly tab navigation"""

        if st.session_state.get('is_mobile', False):
            # Mobile: Use selectbox for tab selection
            tab_labels = [tab['label'] for tab in tab_data]
            tab_keys = [tab['key'] for tab in tab_data]

            default_index = 0
            if default_tab:
                try:
                    default_index = tab_keys.index(default_tab)
                except ValueError:
                    pass

            selected_label = st.selectbox(
                "Select section:",
                tab_labels,
                index=default_index,
                key="mobile_tabs"
            )

            # Find selected tab data
            for tab in tab_data:
                if tab['label'] == selected_label:
                    return tab['key'], tab['content']

        else:
            # Desktop/tablet: Use horizontal tabs
            tab_keys = [tab['key'] for tab in tab_data]
            tab_labels = [tab['label'] for tab in tab_data]

            # Create tab buttons
            cols = st.columns(len(tab_data))
            selected_tab = default_tab or tab_keys[0]

            for i, (tab_key, tab_label) in enumerate(zip(tab_keys, tab_labels)):
                with cols[i]:
                    button_type = "primary" if tab_key == st.session_state.get('current_tab', default_tab) else "secondary"
                    if st.button(
                        tab_label,
                        key=f"tab_{tab_key}",
                        type=button_type,
                        use_container_width=True
                    ):
                        st.session_state.current_tab = tab_key
                        selected_tab = tab_key

            # Get current tab content
            for tab in tab_data:
                if tab['key'] == selected_tab:
                    return tab['key'], tab['content']

        return tab_data[0]['key'], tab_data[0]['content']


# Global layout manager instance
layout_manager = ResponsiveLayoutManager()

def get_layout_manager() -> ResponsiveLayoutManager:
    """Get the global layout manager instance"""
    return layout_manager

def responsive_container(content_func):
    """Decorator for responsive containers"""
    def wrapper(*args, **kwargs):
        st.markdown('<div class="responsive-container">', unsafe_allow_html=True)
        result = content_func(*args, **kwargs)
        st.markdown('</div>', unsafe_allow_html=True)
        return result
    return wrapper