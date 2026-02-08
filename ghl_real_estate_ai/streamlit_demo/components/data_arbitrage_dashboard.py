"""
Data Arbitrage Dashboard - Vanguard 1
Visualizes pre-MLS data intelligence including Probate and Tax Liens.
"""

import pandas as pd
import streamlit as st

from ghl_real_estate_ai.services.data_arbitrage_service import get_data_arbitrage_service
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async


def render_data_arbitrage_dashboard():
    st.markdown("### 🕵️ Data Arbitrage: Pre-MLS Intelligence")
    st.markdown("*Identifying motivated sellers 60-90 days before they hit the MLS*")

    arbitrage_service = get_data_arbitrage_service()

    zip_code = st.text_input("Enter Zip Code for Arbitrage Scan:", value="78701")

    if st.button("🚀 Run Deep Arbitrage Scan"):
        with st.spinner("🧠 Scanning County Records, Tax Liens, and Probate Filings..."):
            col1, col2 = st.columns(2)

            probate_leads = st.session_state.get(f"probate_{zip_code}")
            if not probate_leads:
                import asyncio

                loop = asyncio.new_event_loop()
                probate_leads = run_async(arbitrage_service.get_probate_leads(zip_code))
                st.session_state[f"probate_{zip_code}"] = probate_leads

            with col1:
                st.markdown("#### ⚖️ Recent Probate Filings")
                df_probate = pd.DataFrame(probate_leads)
                st.dataframe(df_probate[["address", "owner_name", "filing_date", "propensity_score"]])

                for lead in probate_leads:
                    with st.expander(f"Details: {lead['address']}"):
                        st.write(f"**Owner:** {lead['owner_name']}")
                        st.write(f"**Value:** ${lead['estimated_value']:,}")
                        st.write(f"**Notes:** {lead['notes']}")
                        st.progress(lead["propensity_score"], text=f"Propensity: {lead['propensity_score'] * 100}%")

            with col2:
                st.markdown("#### 🏛️ Tax Liens & Life Events")
                import asyncio

                loop = asyncio.new_event_loop()
                liens = run_async(arbitrage_service.get_tax_liens(zip_code))

                df_liens = pd.DataFrame(liens)
                st.dataframe(df_liens[["address", "lien_amount", "filing_date", "propensity_score"]])

                st.info(
                    "💡 **Strategy:** Out-of-state heirs in probate have a 5-7x higher response rate to direct mail vs. standard sellers."
                )

            st.markdown("---")
            st.markdown("#### 📈 Propensity Decay Tracking")
            days = st.slider("Days since discovery:", 0, 180, 0)
            base_score = 40
            decayed = arbitrage_service.calculate_decay_score(base_score, days)
            st.metric("Trigger Priority Score", f"{decayed:.1f} pts", delta=f"{decayed - base_score:.1f} pts")
            st.caption("Score decays over time as more agents discover the lead. Speed-to-lead is critical.")
