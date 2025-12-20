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
    # 1. SETUP UI
    ui.setup_interface()

    try:
        # SIDEBARNAVIGATION
        with st.sidebar:
            st.title("🚀 Enterprise Hub")
            st.markdown(
                "<div style='margin-top: -15px; color: #64748B; font-size: 0.9em; margin-bottom: 20px;'>Enterprise Intelligence Platform</div>",
                unsafe_allow_html=True,
            )

            # Navigation
            pages = ["🏠 Overview"] + list(MODULES.keys())
            page = st.radio("Navigate:", pages, label_visibility="collapsed")

            st.markdown("---")
            st.markdown("### 👤 **Cayman Roden**")
            st.markdown("Full-Stack Python Developer")
            st.markdown(
                "[View Portfolio](https://github.com/ChunkyTortoise/enterprise-hub) | [LinkedIn](https://linkedin.com/in/caymanroden)"
            )

        logger.info(f"User navigated to: {page}")

        # MAIN CONTAINER
        if page == "🏠 Overview":
            _render_overview()
        elif page in MODULES:
            module_name, module_title = MODULES[page]
            _render_module(module_name, module_title)
        else:
            _render_placeholder(page)

    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        st.error("❌ An unexpected error occurred in the application.")
        if st.checkbox("Show error details"):
            st.exception(e)


def _render_overview() -> None:
    """Render the overview/home page with the new Design System."""

    # Hero Section
    st.markdown(
        "<h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>Unified Enterprise Hub</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='font-size: 1.25rem; color: #64748B; max-width: 800px;'>A production-grade business intelligence platform consolidating 7 mission-critical tools into a single, cloud-native interface.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ui.card_metric("Active Modules", f"{len(MODULES)}/7", "100% Ready")
    with col2:
        ui.card_metric("Test Coverage", "220+", "Passing")
    with col3:
        ui.card_metric("Architecture", "Serverless", "Python + Streamlit")
    with col4:
        ui.card_metric("Performance", "< 50ms", "Latency")

    st.markdown("### 🛠️ Module Suite")

    # Feature Grid - Row 1
    c1, c2, c3 = st.columns(3)

    with c1:
        ui.feature_card(
            icon="💰",
            title="Margin Hunter",
            description="Real-time Cost-Volume-Profit analysis with 10x10 sensitivity heatmaps and break-even modeling.",
            status="hero",
        )
    with c2:
        ui.feature_card(
            icon="📊",
            title="Market Pulse",
            description="Institutional-grade technical analysis dashboard with RSI, MACD, and multi-panel charting.",
            status="active",
        )
    with c3:
        ui.feature_card(
            icon="🔍",
            title="Data Detective",
            description="AI-powered data profiling and statistical analysis. Upload any CSV/Excel for instant insights.",
            status="new",
        )

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    # Feature Grid - Row 2
    c4, c5, c6 = st.columns(3)

    with c4:
        ui.feature_card(
            icon="📈",
            title="Marketing Analytics",
            description="Comprehensive campaign tracking, ROI calculators, multi-variant testing, and attribution modeling.",
            status="new",
        )
    with c5:
        ui.feature_card(
            icon="✍️",
            title="Content Engine",
            description="Generate professional LinkedIn content in seconds using Anthropic's Claude 3.5 Sonnet API.",
            status="active",
        )
    with c6:
        ui.feature_card(
            icon="🤖",
            title="Agent Logic",
            description="Automated market research and news sentiment analysis using NLP and web scraping.",
            status="active",
        )

    # Financial Analyst (7th module)
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    c7, c8, c9 = st.columns([1, 1, 1])
    with c8:  # Center the 7th module
        ui.feature_card(
            icon="💼",
            title="Financial Analyst",
            description="Fundamental stock analysis with financial statements, ratios, and valuation metrics.",
            status="active",
        )

    # Social Proof Section
    st.markdown("---")
    ui.section_header(
        "Built For Real Business Challenges",
        "See how EnterpriseHub replaces manual workflows and expensive subscriptions",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
        <div class="metric-card">
            <h3 style="margin-top: 0;">💡 For SaaS Founders</h3>
            <p style="color: #64748B; line-height: 1.6;">
                <strong>Margin Hunter</strong> replaces Excel spreadsheet chaos for pricing decisions.
                Run 100 profit scenarios simultaneously with sensitivity heatmaps.
                Break-even analysis that updates in real-time as you adjust prices.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class="metric-card" style="margin-top: 1rem;">
            <h3 style="margin-top: 0;">📊 For Finance Teams</h3>
            <p style="color: #64748B; line-height: 1.6;">
                <strong>Market Pulse</strong> eliminates Bloomberg Terminal dependency for basic technical analysis.
                4-panel charts (Price/RSI/MACD/Volume) with institutional-grade indicators.
                Save $24,000/year in subscriptions.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="metric-card">
            <h3 style="margin-top: 0;">🔍 For Data Analysts</h3>
            <p style="color: #64748B; line-height: 1.6;">
                <strong>Data Detective</strong> reduces exploratory data analysis from 2 hours to 2 minutes.
                AI-powered insights, correlation heatmaps, and quality scoring.
                Upload CSV → Get actionable findings instantly.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class="metric-card" style="margin-top: 1rem;">
            <h3 style="margin-top: 0;">📈 For Marketing Teams</h3>
            <p style="color: #64748B; line-height: 1.6;">
                <strong>Marketing Analytics</strong> replaces agency dashboards costing $200-500/month.
                5 attribution models, A/B test calculators, and campaign ROI tracking.
                One-time build you own forever.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Comparison Table
    st.markdown("---")
    ui.section_header("Why EnterpriseHub?", "See how we compare to alternatives")

    st.markdown(
        """
    <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
            <thead>
                <tr style="background-color: #F8FAFC; border-bottom: 2px solid #E2E8F0;">
                    <th style="padding: 12px; text-align: left; font-weight: 600;">Capability</th>
                    <th style="padding: 12px; text-align: center; font-weight: 600; color: #2563EB;">EnterpriseHub</th>
                    <th style="padding: 12px; text-align: center; font-weight: 600;">Excel Spreadsheets</th>
                    <th style="padding: 12px; text-align: center; font-weight: 600;">Bloomberg Terminal</th>
                    <th style="padding: 12px; text-align: center; font-weight: 600;">Agency Dashboards</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 12px;"><strong>Cost</strong></td>
                    <td style="padding: 12px; text-align: center; color: #10B981; font-weight: 600;">$0 (Open Source)</td>
                    <td style="padding: 12px; text-align: center;">$0-200/year</td>
                    <td style="padding: 12px; text-align: center;">$24,000/year</td>
                    <td style="padding: 12px; text-align: center;">$200-500/month</td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0; background-color: #F8FAFC;">
                    <td style="padding: 12px;"><strong>Setup Time</strong></td>
                    <td style="padding: 12px; text-align: center; color: #10B981; font-weight: 600;">< 5 minutes</td>
                    <td style="padding: 12px; text-align: center;">2-4 hours</td>
                    <td style="padding: 12px; text-align: center;">1-2 weeks</td>
                    <td style="padding: 12px; text-align: center;">2-6 weeks</td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 12px;"><strong>Technical Analysis</strong></td>
                    <td style="padding: 12px; text-align: center; color: #10B981; font-weight: 600;">✓ RSI, MACD, MA</td>
                    <td style="padding: 12px; text-align: center;">Manual formulas</td>
                    <td style="padding: 12px; text-align: center;">✓ Advanced</td>
                    <td style="padding: 12px; text-align: center;">✗</td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0; background-color: #F8FAFC;">
                    <td style="padding: 12px;"><strong>AI-Powered Insights</strong></td>
                    <td style="padding: 12px; text-align: center; color: #10B981; font-weight: 600;">✓ Claude 3.5 Sonnet</td>
                    <td style="padding: 12px; text-align: center;">✗</td>
                    <td style="padding: 12px; text-align: center;">Limited</td>
                    <td style="padding: 12px; text-align: center;">✗</td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 12px;"><strong>Scenario Modeling</strong></td>
                    <td style="padding: 12px; text-align: center; color: #10B981; font-weight: 600;">✓ 100 scenarios/heatmap</td>
                    <td style="padding: 12px; text-align: center;">Manual copy-paste</td>
                    <td style="padding: 12px; text-align: center;">✗</td>
                    <td style="padding: 12px; text-align: center;">✗</td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0; background-color: #F8FAFC;">
                    <td style="padding: 12px;"><strong>Attribution Modeling</strong></td>
                    <td style="padding: 12px; text-align: center; color: #10B981; font-weight: 600;">✓ 5 models</td>
                    <td style="padding: 12px; text-align: center;">Manual calculation</td>
                    <td style="padding: 12px; text-align: center;">✗</td>
                    <td style="padding: 12px; text-align: center;">Limited</td>
                </tr>
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 12px;"><strong>Automated Testing</strong></td>
                    <td style="padding: 12px; text-align: center; color: #10B981; font-weight: 600;">✓ 220+ tests</td>
                    <td style="padding: 12px; text-align: center;">✗</td>
                    <td style="padding: 12px; text-align: center;">Proprietary</td>
                    <td style="padding: 12px; text-align: center;">✗</td>
                </tr>
                <tr style="background-color: #F8FAFC;">
                    <td style="padding: 12px;"><strong>Ownership</strong></td>
                    <td style="padding: 12px; text-align: center; color: #10B981; font-weight: 600;">✓ Full source code</td>
                    <td style="padding: 12px; text-align: center;">You own files</td>
                    <td style="padding: 12px; text-align: center;">✗ Subscription only</td>
                    <td style="padding: 12px; text-align: center;">✗ Subscription only</td>
                </tr>
            </tbody>
        </table>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Tech Stack Badge Section
    st.markdown("---")
    ui.section_header(
        "Technical Foundation", "Built with modern, production-grade tools"
    )

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
        st.markdown("""
        This module is scheduled for Phase 3 development. Current roadmap:
        - **Phase 1:** ✅ Container & deployment infrastructure
        - **Phase 2:** ✅ Market Pulse basic visualization
        - **Phase 2.6:** ✅ Professional trading indicators (4-panel layout)
        - **Phase 3:** 🔜 Live APIs + Remaining 4 modules
        """)


if __name__ == "__main__":
    main()
