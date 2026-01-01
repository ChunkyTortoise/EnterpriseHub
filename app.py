"""
Enterprise Hub - Main Application Entry Point.

A unified platform for market analysis and enterprise tooling
with multiple mission-critical modules.
"""

import streamlit as st
import sys

# FAST BOOT: Minimal imports at top level
# We delay importing 'utils.ui' and 'modules.*' until inside main()

# ENTERPRISE CONFIGURATION
st.set_page_config(
    page_title="Unified Enterprise Hub | Cayman Roden",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/ChunkyTortoise/enterprise-hub",
        "Report a bug": "https://github.com/ChunkyTortoise/enterprise-hub/issues",
        "About": (
            "# Enterprise Hub\nA unified platform for market analysis and enterprise tooling."
        ),
    },
)

# --- MODULE REGISTRY ---
MODULES = {
    "📊 Market Pulse": ("market_pulse", "Market Pulse", "assets/icons/market_pulse.png"),
    "💼 Financial Analyst": ("financial_analyst", "Financial Analyst", "assets/icons/financial_analyst.png"),
    "💰 Margin Hunter": ("margin_hunter", "Margin Hunter", "assets/icons/margin_hunter.png"),
    "🤖 Agent Logic": ("agent_logic", "Agent Logic", "assets/icons/agent_logic.svg"),
    "✍️ Content Engine": ("content_engine", "Content Engine", "assets/icons/content_engine.png"),
    "🔍 Data Detective": ("data_detective", "Data Detective", "assets/icons/data_detective.png"),
    "📈 Marketing Analytics": ("marketing_analytics", "Marketing Analytics", "assets/icons/marketing_analytics.svg"),
    "🤖 Multi-Agent Workflow": ("multi_agent", "Multi-Agent Workflow", "assets/icons/multi_agent.svg"),
    "🧠 Smart Forecast": ("smart_forecast", "Smart Forecast Engine", "assets/icons/smart_forecast.svg"),
    "🎨 Design System": ("design_system", "Design System Gallery", "assets/icons/design_system.svg"),
}

def main():
    """Main application function with Lazy Loading."""
    
    # Lazy Import UI to prevent import loops or early crashes
    try:
        import utils.ui as ui
        from utils.logger import get_logger
        logger = get_logger(__name__)
    except ImportError as e:
        st.error(f"Critical System Error: Failed to load core utilities. {e}")
        st.stop()

    # Initialize session state
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    if "username" not in st.session_state:
        st.session_state.username = "Guest"

    try:
        # PRODUCTION GATEWAY (Optional - removed for public demo)
        # if not ui.login_modal(): st.stop()

        # Initialize page variable to default
        page = "🏠 Overview"

        # SIDEBARNAVIGATION
        with st.sidebar:
            st.markdown(
                f"""
                <div style='margin-bottom: 32px;'>
                    <h1 style='
                        font-family: sans-serif;
                        font-size: 1.5rem;
                        font-weight: 800;
                        letter-spacing: -0.05em;
                        margin: 0;
                    '>
                        ENTERPRISE<span style='color: #4f46e5;'>HUB</span>
                    </h1>
                    <div style='
                        color: #64748b;
                        font-size: 0.7rem;
                        font-weight: 600;
                        letter-spacing: 0.1em;
                        text-transform: uppercase;
                    '>
                        Platform Console v4.0
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Theme Toggle
            st.markdown("---")
            st.markdown("**🎨 Theme**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("☀️ Light", use_container_width=True):
                    st.session_state.theme = "light"
                    st.rerun()
            with col2:
                if st.button("🌙 Dark", use_container_width=True):
                    st.session_state.theme = "dark"
                    st.rerun()

            # Navigation
            st.markdown("---")
            pages = ["🏠 Overview"] + list(MODULES.keys())
            # THIS ASSIGNS THE VARIABLE CORRECTLY NOW
            page = st.radio("Navigate:", pages, label_visibility="collapsed")

            st.markdown("---")
            st.markdown("### 👤 **Cayman Roden**")
            st.markdown("Full-Stack Python Developer")
            st.markdown("[View Portfolio](https://chunkytortoise.github.io/EnterpriseHub/)")

        # Setup UI
        ui.setup_interface(st.session_state.theme)

        # MAIN CONTAINER
        if page == "🏠 Overview":
            _render_overview(ui)
        elif page in MODULES:
            module_name, module_title, _ = MODULES[page]
            _load_and_render_module(module_name, module_title)
        
        # Footer
        ui.footer()

    except Exception as e:
        st.error("❌ An unexpected error occurred in the application.")
        st.exception(e)

def _load_and_render_module(module_name, module_title):
    """Dynamically imports and renders a module to save memory/startup time."""
    import importlib
    import streamlit as st
    import utils.ui as ui  # Re-import locally to be safe

    ui.section_header(module_title)

    with st.spinner(f"Loading {module_title}..."):
        try:
            # THIS IS THE KEY FIX: Import only when requested
            module = importlib.import_module(f"modules.{module_name}")
            module.render()
        except ModuleNotFoundError:
            st.warning(f"⚠️ Module '{module_name}' is not yet deployed.")
        except Exception as e:
            st.error(f"❌ Failed to load {module_title}")
            st.exception(e)

def _render_overview(ui):
    """Render the overview/home page."""
    import streamlit as st
    
    # Hero Section
    ui.hero_section(
        "Unified Enterprise Hub",
        "A production-grade business intelligence platform consolidating "
        "9 mission-critical tools into a single, cloud-native interface."
    )

    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1: ui.card_metric("Active Modules", f"{len(MODULES)}/10", "100% Ready")
    with col2: ui.card_metric("Test Coverage", "220+", "Passing")
    with col3: ui.card_metric("Architecture", "Serverless", "Python + Streamlit")
    with col4: ui.card_metric("Performance", "Lazy-Loaded", "Optimized")

    ui.spacer(40)
    st.markdown("### 🛠️ Module Suite (Select from Sidebar)")
    
    # Simple Grid for Overview
    cols = st.columns(3)
    for i, (name, (mod_id, title, icon)) in enumerate(MODULES.items()):
        with cols[i % 3]:
            st.info(f"**{name}**\n\nReady for launch.")

if __name__ == "__main__":
    main()
