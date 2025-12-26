"""
Enterprise Hub - Main Application Entry Point.

A unified platform for market analysis and enterprise tooling
with multiple mission-critical modules.
"""

import importlib

import streamlit as st

import utils.ui as ui  # Import the new UI module
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# ENTERPRISE CONFIGURATION
st.set_page_config(
    page_title="Unified Enterprise Hub | Cayman Roden",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/ChunkyTortoise/enterprise-hub",
        "Report a bug": "https://github.com/ChunkyTortoise/enterprise-hub/issues",
        "About": "# Enterprise Hub\nA unified platform for market analysis and enterprise tooling.",
    },
)

# --- MODULE REGISTRY ---
# Maps sidebar navigation titles to module information.
MODULES = {
    "📊 Market Pulse": ("market_pulse", "Market Pulse", "assets/icons/market_pulse.png"),
    "💼 Financial Analyst": (
        "financial_analyst",
        "Financial Analyst",
        "assets/icons/financial_analyst.png",
    ),
    "💰 Margin Hunter": ("margin_hunter", "Margin Hunter", "assets/icons/margin_hunter.png"),
    "🤖 Agent Logic": ("agent_logic", "Agent Logic", "assets/icons/agent_logic.svg"),
    "✍️ Content Engine": ("content_engine", "Content Engine", "assets/icons/content_engine.png"),
    "🔍 Data Detective": ("data_detective", "Data Detective", "assets/icons/data_detective.png"),
    "📈 Marketing Analytics": (
        "marketing_analytics",
        "Marketing Analytics",
        "assets/icons/marketing_analytics.svg",
    ),
    "🤖 Multi-Agent Workflow": (
        "multi_agent",
        "Multi-Agent Workflow",
        "assets/icons/multi_agent.svg",
    ),
    "🧠 Smart Forecast": (
        "smart_forecast",
        "Smart Forecast Engine",
        "assets/icons/smart_forecast.svg",
    ),
    "🎨 Design System": (
        "design_system",
        "Design System Gallery",
        "assets/icons/design_system.svg",
    ),
}


def main() -> None:
    """Main application function."""
    # Initialize theme in session state
    if "theme" not in st.session_state:
        st.session_state.theme = "light"

    try:
        # PRODUCTION GATEWAY
        if not ui.login_modal():
            st.stop()

        # SIDEBAR NAVIGATION
        with st.sidebar:
            st.markdown(
                f"""
                <div style='margin-bottom: 32px;'>
                    <h1 style='font-family: {ui.THEME["header_font"]}; font-size: 1.5rem; font-weight: 800; letter-spacing: -0.05em; margin: 0;'>
                        ENTERPRISE<span style='color: {ui.THEME["accent"]};'>HUB</span>
                    </h1>
                    <div style='color: {ui.THEME["secondary"]}; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase;'>
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
                if st.button(
                    "☀️ Light",
                    use_container_width=True,
                    type="primary" if st.session_state.theme == "light" else "secondary",
                ):
                    st.session_state.theme = "light"
                    st.rerun()
                if st.button(
                    "🌊 Ocean",
                    use_container_width=True,
                    type="primary" if st.session_state.theme == "ocean" else "secondary",
                ):
                    st.session_state.theme = "ocean"
                    st.rerun()
            with col2:
                if st.button(
                    "🌙 Dark",
                    use_container_width=True,
                    type="primary" if st.session_state.theme == "dark" else "secondary",
                ):
                    st.session_state.theme = "dark"
                    st.rerun()
                if st.button(
                    "🌅 Sunset",
                    use_container_width=True,
                    type="primary" if st.session_state.theme == "sunset" else "secondary",
                ):
                    st.session_state.theme = "sunset"
                    st.rerun()

            # Navigation
            st.markdown("---")
            pages = ["🏠 Overview"] + list(MODULES.keys())
            page = st.radio("Navigate:", pages, label_visibility="collapsed")

            st.markdown("---")
            st.markdown("### 👤 **Cayman Roden**")
            st.markdown("Full-Stack Python Developer")
            st.markdown(
                "[View Portfolio](https://github.com/ChunkyTortoise/enterprise-hub) | [LinkedIn](https://linkedin.com/in/caymanroden)"
            )

        # Setup UI with selected theme (must be after sidebar to read session state)
        ui.setup_interface(st.session_state.theme)

        logger.info(f"User navigated to: {page}")

        # MAIN CONTAINER
        if page == "🏠 Overview":
            _render_overview()
        elif page in MODULES:
            module_name, module_title = MODULES[page]
            _render_module(module_name, module_title)
        else:
            _render_placeholder(page)

        # Footer
        ui.footer()

    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        st.error("❌ An unexpected error occurred in the application.")
        if st.checkbox("Show error details"):
            st.exception(e)


def _render_overview() -> None:
    """Render the overview/home page with the new Design System."""

    # Hero Section with Editorial Background
    ui.hero_section(
        "Unified Enterprise Hub",
        "A production-grade business intelligence platform consolidating 9 mission-critical tools into a single, cloud-native interface.",
        background_image="assets/hero/background_editorial.png",
    )

    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ui.card_metric("Active Modules", f"{len(MODULES)}/7", "100% Ready")
    with col2:
        ui.card_metric("Test Coverage", "220+", "Passing")
    with col3:
        ui.card_metric("Architecture", "Serverless", "Python + Streamlit")
    with col4:
        ui.card_metric("Performance", "Cache-Optimized", "5-min TTL")

    ui.spacer(40)
    st.markdown("### 🛠️ Module Suite")

    # Feature Grid - Row 1
    c1, c2, c3 = st.columns(3)

    with c1:
        module_info = MODULES.get("💰 Margin Hunter")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "💰",
            title=module_info[1],
            description="Real-time Cost-Volume-Profit analysis with 10x10 sensitivity heatmaps and break-even modeling.",
            status="hero",
            icon_path=module_info[2] if module_info[2] else None,
        )
    with c2:
        module_info = MODULES.get("📊 Market Pulse")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "📊",
            title=module_info[1],
            description="Institutional-grade technical analysis dashboard with RSI, MACD, and multi-panel charting.",
            status="active",
            icon_path=module_info[2] if module_info[2] else None,
        )
    with c3:
        module_info = MODULES.get("🔍 Data Detective")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "🔍",
            title=module_info[1],
            description="AI-powered data profiling and statistical analysis. Upload any CSV/Excel for instant insights.",
            status="new",
            icon_path=module_info[2] if module_info[2] else None,
        )

    ui.spacer(20)

    # Feature Grid - Row 2
    c4, c5, c6 = st.columns(3)

    with c4:
        module_info = MODULES.get("📈 Marketing Analytics")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "📈",
            title=module_info[1],
            description="Comprehensive campaign tracking, ROI calculators, multi-variant testing, and attribution modeling.",
            status="new",
            icon_path=module_info[2] if module_info[2] else None,
        )
    with c5:
        module_info = MODULES.get("✍️ Content Engine")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "✍️",
            title=module_info[1],
            description="Generate professional LinkedIn content in seconds using Anthropic's Claude 3.5 Sonnet API.",
            status="active",
            icon_path=module_info[2] if module_info[2] else None,
        )
    with c6:
        module_info = MODULES.get("🤖 Agent Logic")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "🤖",
            title=module_info[1],
            description="Automated market research and news sentiment analysis using NLP and web scraping.",
            status="active",
            icon_path=module_info[2] if module_info[2] else None,
        )

    # Row 3: Financial Analyst, Multi-Agent, Smart Forecast
    ui.spacer(20)
    c7, c8, c9 = st.columns(3)

    with c7:
        module_info = MODULES.get("💼 Financial Analyst")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "💼",
            title=module_info[1],
            description="Fundamental stock analysis with financial statements, ratios, and valuation metrics.",
            status="active",
            icon_path=module_info[2] if module_info[2] else None,
        )

    with c8:
        module_info = MODULES.get("🤖 Multi-Agent Workflow")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "🤖",
            title=module_info[1],
            description="Orchestrates 4 specialized agents (Data, Tech, News, Chief) to perform deep-dive asset analysis.",
            status="new",
            icon_path=module_info[2] if module_info[2] else None,
        )

    with c9:
        module_info = MODULES.get("🧠 Smart Forecast")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "🧠",
            title=module_info[1],
            description="AI-powered time series forecasting using Random Forest and Rolling Window analysis.",
            status="new",
            icon_path=module_info[2] if module_info[2] else None,
        )

    ui.spacer(40)
    ui.section_header(
        "Built For Real Business Challenges",
        "See how EnterpriseHub replaces manual workflows and expensive subscriptions",
    )

    col1, col2 = st.columns(2)
    with col1:
        ui.use_case_card(
            icon="💡",
            title="For SaaS Founders",
            description="""
                <strong>Margin Hunter</strong> replaces Excel spreadsheet chaos for pricing decisions.
                Run 100 profit scenarios simultaneously with sensitivity heatmaps.
                Break-even analysis that updates in real-time as you adjust prices.
            """,
        )

        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

        ui.use_case_card(
            icon="📊",
            title="For Finance Teams",
            description="""
                <strong>Market Pulse</strong> eliminates Bloomberg Terminal dependency for basic technical analysis.
                4-panel charts (Price/RSI/MACD/Volume) with institutional-grade indicators.
                Save $24,000/year in subscriptions.
            """,
        )

    with col2:
        ui.use_case_card(
            icon="🔍",
            title="For Data Analysts",
            description="""
                <strong>Data Detective</strong> reduces exploratory data analysis from 2 hours to 2 minutes.
                AI-powered insights, correlation heatmaps, and quality scoring.
                Upload CSV → Get actionable findings instantly.
            """,
        )

        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

        ui.use_case_card(
            icon="📈",
            title="For Marketing Teams",
            description="""
                **Marketing Analytics** replaces agency dashboards costing $200-500/month.
                5 attribution models, A/B test calculators, and campaign ROI tracking.
                One-time build you own forever.
            """,
        )

    ui.spacer(40)
    ui.section_header("Why EnterpriseHub?", "See how we compare to alternatives")
    ui.comparison_table()

    # Tech Stack Badge Section
    ui.spacer(40)
    ui.section_header("Technical Foundation", "Built with modern, production-grade tools")

    st.markdown(
        """
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 1rem;">
        <span style="background-color: #DBEAFE; color: #1E40AF; padding: 6px 12px; border-radius: 6px; font-weight: 500;">Python 3.11</span>
        <span style="background-color: #DBEAFE; color: #1E40AF; padding: 6px 12px; border-radius: 6px; font-weight: 500;">Streamlit 1.40+</span>
        <span style="background-color: #DBEAFE; color: #1E40AF; padding: 6px 12px; border-radius: 6px; font-weight: 500;">Claude 3.5 Sonnet</span>
        <span style="background-color: #DBEAFE; color: #1E40AF; padding: 6px 12px; border-radius: 6px; font-weight: 500;">Plotly</span>
        <span style="background-color: #DBEAFE; color: #1E40AF; padding: 6px 12px; border-radius: 6px; font-weight: 500;">pandas</span>
        <span style="background-color: #DBEAFE; color: #1E40AF; padding: 6px 12px; border-radius: 6px; font-weight: 500;">NumPy</span>
        <span style="background-color: #DBEAFE; color: #1E40AF; padding: 6px 12px; border-radius: 6px; font-weight: 500;">yfinance</span>
        <span style="background-color: #DCFCE7; color: #166534; padding: 6px 12px; border-radius: 6px; font-weight: 500;">pytest (220+ tests)</span>
        <span style="background-color: #DCFCE7; color: #166534; padding: 6px 12px; border-radius: 6px; font-weight: 500;">85% Coverage</span>
        <span style="background-color: #FEF3C7; color: #92400E; padding: 6px 12px; border-radius: 6px; font-weight: 500;">CI/CD (GitHub Actions)</span>
    </div>
    """,
        unsafe_allow_html=True,
    )


def _render_module(module_name: str, module_title: str) -> None:
    """
    Generic renderer for an enterprise module.
    """
    # Use the new header style
    ui.section_header(module_title)

    try:
        module = importlib.import_module(f"modules.{module_name}")
        module.render()
    except ModuleNotFoundError:
        logger.warning(f"Module '{module_name}' not found, rendering placeholder.")
        _render_placeholder(module_title)
    except Exception as e:
        logger.error(f"Error loading {module_title} module: {e}", exc_info=True)
        st.error(f"❌ Failed to load {module_title} module.")
        if st.checkbox("Show error details", key=f"{module_name}_error"):
            st.exception(e)


def _render_placeholder(page: str) -> None:
    """Render placeholder for upcoming modules."""
    ui.section_header(page)
    st.warning(f"⏳ **{page}** module pending Phase 3 deployment.")

    with st.expander("View Roadmap", expanded=True):
        st.markdown(
            """
        This module is scheduled for Phase 3 development. Current roadmap:
        - **Phase 1:** ✅ Container & deployment infrastructure
        - **Phase 2:** ✅ Market Pulse basic visualization
        - **Phase 2.6:** ✅ Professional trading indicators (4-panel layout)
        - **Phase 3:** 🔜 Live APIs + Remaining 4 modules
        """
        )


if __name__ == "__main__":
    main()
