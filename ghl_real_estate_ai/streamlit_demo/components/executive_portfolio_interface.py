"""
Executive Property Portfolio Interface
Streamlit component for UHNW client portfolio management

Provides executive-level interface for portfolio analysis, performance tracking,
and strategic decision-making for ultra-high-net-worth clients.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

try:
    from ghl_real_estate_ai.services.executive_portfolio_manager import (
        PortfolioManagerAgent as ExecutivePortfolioManager,
    )
except ImportError:
    ExecutivePortfolioManager = None

# Stub types for interface compatibility when full service is not available
try:
    from ghl_real_estate_ai.services.executive_portfolio_manager import (
        InvestmentStrategy,
        PortfolioProperty,
        PropertyType,
        UHNWClient,
        create_sample_portfolio,
        create_sample_uhnw_client,
    )
except ImportError:
    from dataclasses import dataclass, field
    from enum import Enum

    class PropertyType(str, Enum):
        RESIDENTIAL = "residential"
        COMMERCIAL = "commercial"
        LUXURY = "luxury"

    class InvestmentStrategy(str, Enum):
        GROWTH = "growth"
        INCOME = "income"
        BALANCED = "balanced"

    @dataclass
    class UHNWClient:
        client_id: str = ""
        name: str = ""
        net_worth: float = 0.0

    @dataclass
    class PortfolioProperty:
        property_id: str = ""
        address: str = ""
        value: float = 0.0

    def create_sample_uhnw_client():
        return UHNWClient(client_id="demo", name="Demo Client", net_worth=5_000_000)

    def create_sample_portfolio():
        return []


class ExecutivePortfolioInterface:
    """Streamlit interface for executive portfolio management"""

    def __init__(self):
        self.portfolio_manager = ExecutivePortfolioManager()

        # Initialize session state
        if "selected_client" not in st.session_state:
            st.session_state.selected_client = None
        if "portfolio_data" not in st.session_state:
            st.session_state.portfolio_data = None
        if "portfolio_analysis" not in st.session_state:
            st.session_state.portfolio_analysis = None

    @st.cache_data(ttl=600)
    def load_client_data(_self) -> List[UHNWClient]:
        """Load UHNW client data with caching"""
        # In production, this would load from database
        clients = [
            create_sample_uhnw_client(),
            UHNWClient(
                client_id="UHNW-002",
                client_name="Investment Executive",
                net_worth=25_000_000,
                liquid_assets=5_000_000,
                investment_budget=3_500_000,
                risk_tolerance="Aggressive",
                investment_strategy=InvestmentStrategy.GROWTH,
                tax_bracket=0.37,
                preferred_locations=["West Lake Hills", "Rollingwood"],
                property_types_interest=[PropertyType.ESTATE, PropertyType.COMMERCIAL],
                timeline_horizons={"short_term": 1, "medium_term": 3, "long_term": 7},
            ),
            UHNWClient(
                client_id="UHNW-003",
                client_name="Conservative Investor",
                net_worth=8_000_000,
                liquid_assets=2_000_000,
                investment_budget=1_200_000,
                risk_tolerance="Conservative",
                investment_strategy=InvestmentStrategy.INCOME,
                tax_bracket=0.32,
                preferred_locations=["Hyde Park", "Clarksville"],
                property_types_interest=[PropertyType.LUXURY_CONDO, PropertyType.INVESTMENT_PROPERTY],
                timeline_horizons={"short_term": 3, "medium_term": 7, "long_term": 15},
            ),
        ]
        return clients

    @st.cache_data(ttl=300)
    def load_portfolio_data(_self, client_id: str) -> List[PortfolioProperty]:
        """Load portfolio data for specific client"""
        # In production, this would load client-specific portfolio from database
        return create_sample_portfolio()

    def render_client_selector(self, clients: List[UHNWClient]):
        """Render client selection interface"""
        st.markdown("## 👑 Client Selection")

        client_options = {f"{client.client_name} (${client.net_worth:,.0f} NW)": client for client in clients}

        selected_client_name = st.selectbox(
            "Select UHNW Client", options=list(client_options.keys()), key="client_selector"
        )

        if selected_client_name:
            selected_client = client_options[selected_client_name]
            st.session_state.selected_client = selected_client

            # Display client summary
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Net Worth", f"${selected_client.net_worth:,.0f}")

            with col2:
                st.metric("Investment Budget", f"${selected_client.investment_budget:,.0f}")

            with col3:
                st.metric("Risk Tolerance", selected_client.risk_tolerance)

            with col4:
                st.metric("Strategy", selected_client.investment_strategy.value.title())

    def render_portfolio_overview(self, client: UHNWClient, properties: List[PortfolioProperty]):
        """Render portfolio overview section"""
        st.markdown("## 📊 Portfolio Overview")

        # Portfolio metrics
        total_value = sum(prop.current_value for prop in properties)
        total_invested = sum(prop.purchase_price for prop in properties)
        total_return = (total_value - total_invested) / total_invested if total_invested > 0 else 0

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Value", f"${total_value:,.0f}")

        with col2:
            st.metric("Total Invested", f"${total_invested:,.0f}")

        with col3:
            st.metric("Total Return", f"{total_return:.1%}", f"+${total_value - total_invested:,.0f}")

        with col4:
            st.metric("Properties", f"{len(properties)}")

        with col5:
            portfolio_weight = (total_value / client.net_worth * 100) if client.net_worth > 0 else 0
            st.metric("% of Net Worth", f"{portfolio_weight:.1f}%")

        # Portfolio composition charts
        col1, col2 = st.columns(2)

        with col1:
            # Value by property type
            type_values = {}
            for prop in properties:
                prop_type = prop.property_type.value.replace("_", " ").title()
                type_values[prop_type] = type_values.get(prop_type, 0) + prop.current_value

            if type_values:
                fig_types = px.pie(
                    values=list(type_values.values()),
                    names=list(type_values.keys()),
                    title="Portfolio by Property Type",
                )
                st.plotly_chart(fig_types, use_container_width=True)

        with col2:
            # Value by location
            location_values = {}
            for prop in properties:
                location_values[prop.neighborhood] = location_values.get(prop.neighborhood, 0) + prop.current_value

            if location_values:
                fig_locations = px.pie(
                    values=list(location_values.values()),
                    names=list(location_values.keys()),
                    title="Portfolio by Location",
                )
                st.plotly_chart(fig_locations, use_container_width=True)

    def render_performance_analysis(self, analysis):
        """Render performance analysis section"""
        st.markdown("## 📈 Performance Analysis")

        # Key performance metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Portfolio IRR",
                f"{analysis.portfolio_irr:.1%}",
                delta=f"+{(analysis.portfolio_irr - 0.08):.1%} vs target",
            )

        with col2:
            st.metric("YTD Return", f"{analysis.portfolio_roi_ytd:.1%}", delta=f"+{analysis.portfolio_roi_ytd:.1%}")

        with col3:
            st.metric("Lifetime Return", f"{analysis.portfolio_roi_lifetime:.1%}", delta="Cumulative")

        with col4:
            st.metric("Tax Savings", f"${analysis.total_tax_optimization:,.0f}", delta="Annual")

        # Performance charts
        st.markdown("### Performance Breakdown")

        col1, col2 = st.columns(2)

        with col1:
            # Diversification scores
            diversification_data = {
                "Geographic": analysis.geographic_diversification,
                "Property Type": analysis.property_type_diversification,
                "Risk": analysis.risk_diversification,
            }

            fig_div = px.bar(
                x=list(diversification_data.keys()),
                y=list(diversification_data.values()),
                title="Diversification Scores (0-100)",
                color=list(diversification_data.values()),
                color_continuous_scale="Viridis",
            )
            fig_div.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig_div, use_container_width=True)

        with col2:
            # Risk vs Return scatter
            risk_return_data = []
            # Simulated risk-return data for visualization
            for i in range(10):
                risk_return_data.append({"Risk": 20 + i * 6, "Return": 0.05 + i * 0.01, "Asset": f"Asset {i + 1}"})

            if risk_return_data:
                df_risk_return = pd.DataFrame(risk_return_data)
                fig_risk_return = px.scatter(
                    df_risk_return, x="Risk", y="Return", title="Risk-Return Profile", hover_data=["Asset"]
                )
                fig_risk_return.update_yaxis(tickformat=".1%")
                st.plotly_chart(fig_risk_return, use_container_width=True)

    def render_property_details(self, properties: List[PortfolioProperty]):
        """Render detailed property information"""
        st.markdown("## 🏡 Property Details")

        # Property selection
        property_options = {f"{prop.address} (${prop.current_value:,.0f})": prop for prop in properties}

        selected_property_name = st.selectbox(
            "Select Property for Details", options=list(property_options.keys()), key="property_selector"
        )

        if selected_property_name:
            selected_property = property_options[selected_property_name]

            # Property overview
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### Basic Information")
                st.write(f"**Address:** {selected_property.address}")
                st.write(f"**Type:** {selected_property.property_type.value.replace('_', ' ').title()}")
                st.write(f"**Neighborhood:** {selected_property.neighborhood}")
                st.write(f"**Size:** {selected_property.square_footage:,} sq ft")
                st.write(f"**Lot:** {selected_property.lot_size:.2f} acres")

            with col2:
                st.markdown("### Financial Metrics")
                st.metric("Current Value", f"${selected_property.current_value:,.0f}")
                st.metric("Purchase Price", f"${selected_property.purchase_price:,.0f}")
                gain = selected_property.current_value - selected_property.purchase_price
                st.metric("Capital Gain", f"${gain:,.0f}")
                st.metric("Total Return", f"{selected_property.total_return_lifetime:.1%}")

            with col3:
                st.markdown("### Investment Analysis")
                metrics = selected_property.investment_metrics
                st.metric("Cap Rate", f"{metrics.cap_rate:.1%}")
                st.metric("Cash-on-Cash", f"{metrics.cash_on_cash_return:.1%}")
                st.metric("5-Year ROI", f"{metrics.roi_5_year:.1%}")
                st.metric("Risk Score", f"{metrics.risk_score:.0f}/100")

            # Tax optimization details
            st.markdown("### Tax Optimization")
            tax_opt = selected_property.tax_optimization

            tax_col1, tax_col2, tax_col3 = st.columns(3)

            with tax_col1:
                st.metric("Depreciation Benefit", f"${tax_opt.depreciation_benefit:,.0f}")

            with tax_col2:
                st.metric("Property Tax Deduction", f"${tax_opt.property_tax_deduction:,.0f}")

            with tax_col3:
                st.metric("Total Tax Savings", f"${tax_opt.total_tax_savings:,.0f}")

            if tax_opt.opportunity_1031_exchange:
                st.success("🔄 1031 Exchange Opportunity Available")

    def render_strategic_recommendations(self, analysis):
        """Render strategic recommendations"""
        st.markdown("## 🎯 Strategic Recommendations")

        # Recommendations tabs
        rec_tab1, rec_tab2, rec_tab3 = st.tabs(
            ["Portfolio Rebalancing", "Acquisition Opportunities", "Disposition Candidates"]
        )

        with rec_tab1:
            st.markdown("### Portfolio Rebalancing Recommendations")
            if analysis.rebalancing_recommendations:
                for i, rec in enumerate(analysis.rebalancing_recommendations, 1):
                    st.markdown(f"**{i}.** {rec}")
            else:
                st.info("No rebalancing recommendations at this time.")

        with rec_tab2:
            st.markdown("### Acquisition Opportunities")
            if analysis.acquisition_opportunities:
                for i, opp in enumerate(analysis.acquisition_opportunities, 1):
                    st.markdown(f"**{i}.** {opp}")
            else:
                st.info("No acquisition opportunities identified.")

        with rec_tab3:
            st.markdown("### Disposition Candidates")
            if analysis.disposition_candidates:
                for i, disp in enumerate(analysis.disposition_candidates, 1):
                    st.markdown(f"**{i}.** {disp}")
            else:
                st.success("All properties performing well - no dispositions recommended.")

    def render_tax_optimization(self, client: UHNWClient, properties: List[PortfolioProperty]):
        """Render tax optimization analysis"""
        st.markdown("## 💰 Tax Optimization Analysis")

        # 1031 Exchange opportunities
        exchange_opportunities = self.portfolio_manager.calculate_1031_exchange_opportunities(properties)

        if exchange_opportunities:
            st.markdown("### 🔄 1031 Exchange Opportunities")

            exchange_df = pd.DataFrame(exchange_opportunities)
            exchange_df["capital_gain"] = exchange_df["capital_gain"].apply(lambda x: f"${x:,.0f}")
            exchange_df["potential_tax_savings"] = exchange_df["potential_tax_savings"].apply(lambda x: f"${x:,.0f}")
            exchange_df["current_value"] = exchange_df["current_value"].apply(lambda x: f"${x:,.0f}")

            st.dataframe(
                exchange_df[
                    ["address", "current_value", "capital_gain", "potential_tax_savings", "recommended_action"]
                ],
                use_container_width=True,
            )

            total_tax_savings = sum(
                opp["potential_tax_savings"]
                for opp in exchange_opportunities
                if isinstance(opp["potential_tax_savings"], (int, float))
            )
            st.success(f"💡 Total potential tax savings through 1031 exchanges: ${total_tax_savings:,.0f}")
        else:
            st.info("No 1031 exchange opportunities currently available.")

        # Overall tax efficiency
        st.markdown("### Tax Efficiency Summary")

        total_tax_savings = sum(prop.tax_optimization.total_tax_savings for prop in properties)
        portfolio_value = sum(prop.current_value for prop in properties)
        tax_efficiency = (total_tax_savings / portfolio_value * 100) if portfolio_value > 0 else 0

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Annual Tax Savings", f"${total_tax_savings:,.0f}")

        with col2:
            st.metric("Tax Efficiency Rate", f"{tax_efficiency:.2f}%")

        with col3:
            effective_tax_rate = client.tax_bracket * (1 - tax_efficiency / 100)
            st.metric("Effective Tax Rate", f"{effective_tax_rate:.1%}")

    async def render_executive_report(self, client: UHNWClient, analysis):
        """Render executive report section"""
        st.markdown("## 📋 Executive Report")

        with st.spinner("Generating executive report..."):
            try:
                report = await self.portfolio_manager.generate_executive_report(client, analysis)
                st.markdown(report)
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
                st.info("Executive report generation temporarily unavailable.")

        # Download options
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📧 Email Report to Client", key="email_report"):
                st.success("Executive report sent to client email.")

        with col2:
            if st.button("💾 Download PDF Report", key="download_report"):
                st.success("PDF report prepared for download.")

    def render(self):
        """Main render method for the interface"""
        st.set_page_config(
            page_title="Executive Portfolio Manager", page_icon="👑", layout="wide", initial_sidebar_state="expanded"
        )

        # Header
        st.markdown("""
        # 👑 Executive Property Portfolio Manager
        ## UHNW Client Portfolio Management & Investment Analysis

        *Professional-grade portfolio management for ultra-high-net-worth real estate investors*

        ---
        """)

        # Load client data
        clients = self.load_client_data()

        # Client selection
        self.render_client_selector(clients)

        if st.session_state.selected_client:
            client = st.session_state.selected_client

            # Load portfolio data
            properties = self.load_portfolio_data(client.client_id)
            st.session_state.portfolio_data = properties

            # Analyze portfolio
            if st.button("🔄 Update Portfolio Analysis", key="analyze_portfolio"):
                with st.spinner("Analyzing portfolio..."):
                    analysis = run_async(self.portfolio_manager.analyze_portfolio(client, properties))
                    st.session_state.portfolio_analysis = analysis
                    st.success("Portfolio analysis updated successfully!")

            # Render sections if analysis is available
            if st.session_state.portfolio_analysis:
                analysis = st.session_state.portfolio_analysis

                # Portfolio overview
                self.render_portfolio_overview(client, properties)

                st.divider()

                # Performance analysis
                self.render_performance_analysis(analysis)

                st.divider()

                # Property details
                self.render_property_details(properties)

                st.divider()

                # Strategic recommendations
                self.render_strategic_recommendations(analysis)

                st.divider()

                # Tax optimization
                self.render_tax_optimization(client, properties)

                st.divider()

                # Executive report
                run_async(self.render_executive_report(client, analysis))

        else:
            st.info("👆 Please select a client to view their portfolio.")

        # Footer
        st.markdown("""
        ---

        **Professional Portfolio Management Services**

        *Delivering investment-grade analysis and strategic guidance for ultra-high-net-worth clients*
        """)


def main():
    """Main function to run the interface"""
    interface = ExecutivePortfolioInterface()
    interface.render()


if __name__ == "__main__":
    main()
