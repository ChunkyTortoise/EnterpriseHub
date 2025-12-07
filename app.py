"""
Enterprise Hub - Main Application Entry Point.

A unified platform for market analysis and enterprise tooling
with multiple mission-critical modules.
"""
import importlib
import streamlit as st
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# ENTERPRISE CONFIGURATION
st.set_page_config(
    page_title="Unified Enterprise Hub | Cayman Roden",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/ChunkyTortoise/enterprise-hub',
        'Report a bug': "https://github.com/ChunkyTortoise/enterprise-hub/issues",
        'About': "# Enterprise Hub\nA unified platform for market analysis and enterprise tooling."
    }
)

# --- MODULE REGISTRY ---
# Maps sidebar navigation titles to module information.
# Format: "Page Title": ("module_filename", "Display Title")
MODULES = {
    "📊 Market Pulse": ("market_pulse", "Market Pulse"),
    "💼 Financial Analyst": ("financial_analyst", "Financial Analyst"),
    "💰 Margin Hunter": ("margin_hunter", "Margin Hunter"),
    "🤖 Agent Logic": ("agent_logic", "Agent Logic"),
    "✍️ Content Engine": ("content_engine", "Content Engine"),
    "🔍 Data Detective": ("data_detective", "Data Detective"),
    "📈 Marketing Analytics": ("marketing_analytics", "Marketing Analytics"),
}


def main() -> None:
    """Main application function."""
    try:
        # SIDEBAR NAVIGATION
        st.sidebar.title("🚀 Enterprise Hub")
        st.sidebar.markdown("**By Cayman Roden**")
        
        # Combine static pages with module pages for the radio options
        pages = ["🏠 Overview"] + list(MODULES.keys())
        page = st.sidebar.radio("Navigate:", pages)
        
        logger.info(f"User navigated to: {page}")
        
        # MAIN CONTAINER
        if page == "🏠 Overview":
            _render_overview()
        elif page in MODULES:
            module_name, module_title = MODULES[page]
            _render_module(module_name, module_title)
        else:
            # Renders a placeholder for any page not in the main logic (e.g., "Content Engine")
            _render_placeholder(page)
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        st.error("❌ An unexpected error occurred in the application.")
        if st.checkbox("Show error details"):
            st.exception(e)


def _render_overview() -> None:
    """Render the overview/home page."""
    st.title("The Unified Enterprise Hub")
    st.markdown("### 7 Mission-Critical Modules in One Platform")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Modules Deployed", f"{len(MODULES)}/7", delta="100%")
    with col2:
        st.metric("Cloud-Native", "✓", delta="Zero Infrastructure")
    with col3:
        st.metric("Time to Value", "< 2 min", delta="-98% vs Legacy")

    st.success("**✅ NEW MODULE:** Marketing Analytics Hub - Track campaigns, ROI, customer metrics, and A/B tests! 📈")

    st.markdown("---")
    st.markdown("### 📊 Available Modules")
    st.markdown("""
    - **Market Pulse** ⚡ *ACTIVE* - Candlesticks, RSI, MACD, Volume Analysis (4-panel layout)
    - **Financial Analyst** ✅ *ACTIVE* - Fundamental analysis, balance sheets, and key metrics
    - **Margin Hunter** 🏆 *HERO PROJECT* - Break-even analysis and profit optimization with CVP heatmaps
    - **Agent Logic** ✅ *ACTIVE* - AI-powered sentiment analysis and news scouting
    - **Content Engine** ✅ *ACTIVE* - AI-powered LinkedIn post generator with Claude API
    - **Data Detective** ✅ *ACTIVE* - AI-powered data analysis, profiling, and insights with Claude
    - **Marketing Analytics** ✨ *NEW* - Campaign tracking, ROI calculator, CAC/CLV, A/B testing, attribution
    """)


def _render_module(module_name: str, module_title: str) -> None:
    """
    Generic renderer for an enterprise module.
    
    Dynamically imports and renders a module specified by its name.
    
    Args:
        module_name: The file name of the module in the `modules` directory.
        module_title: The display title for the page.
    """
    st.title(module_title)
    try:
        module = importlib.import_module(f"modules.{module_name}")
        module.render()
    except ModuleNotFoundError:
        logger.warning(f"Module '{module_name}' not found, rendering placeholder.")
        _render_placeholder(module_title)
    except Exception as e:
        logger.error(f"Error loading {module_title} module: {e}", exc_info=True)
        st.error(f"❌ Failed to load {module_title} module.")
        # Use a unique key for the checkbox to prevent DuplicateWidgetID error
        if st.checkbox("Show error details", key=f"{module_name}_error"):
            st.exception(e)


def _render_placeholder(page: str) -> None:
    """
    Render placeholder for upcoming modules.
    
    Args:
        page: Name of the page/module
    """
    st.title(page)
    st.warning(f"⏳ **{page}** module pending Phase 3 deployment.")
    st.markdown("### Coming Soon")
    st.markdown("""
    This module is scheduled for Phase 3 development. Current roadmap:
    - **Phase 1:** ✅ Container & deployment infrastructure
    - **Phase 2:** ✅ Market Pulse basic visualization
    - **Phase 2.6:** ✅ Professional trading indicators (4-panel layout)
    - **Phase 3:** 🔜 Live APIs + Remaining 4 modules
    """)


if __name__ == "__main__":
    main()
