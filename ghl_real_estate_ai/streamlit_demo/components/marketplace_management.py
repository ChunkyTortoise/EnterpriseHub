import json

import streamlit as st

from ghl_real_estate_ai.agent_system.hooks.architecture import MarketplaceGovernor


def render_marketplace_management():
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; border: 1px solid rgba(99, 102, 241, 0.3);'>
            <h1 style='color: white; margin: 0;'>🏪 Workflow Marketplace</h1>
            <p style='color: #a5b4fc; font-size: 1.1rem;'>Autonomous Governance & Skill Installation</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    governor = MarketplaceGovernor()

    # Marketplace Tabs
    tab1, tab2, tab3 = st.tabs(["🛍️ Browse Skills", "🛡️ Governance Queue", "📜 Audit Manifest"])

    with tab1:
        st.subheader("Available Skills")

        # Mock marketplace skills
        available_skills = [
            {
                "name": "Zillow Trend Predictor",
                "description": "Predicts neighborhood price shifts based on Zillow search volume.",
                "author": "DataCrunch AI",
                "security_audit_id": "AUDIT-2026-001",
                "workflow_sample": {"name": "Zillow Sync", "steps": ["Fetch Data", "Predict", "Notify"]},
            },
            {
                "name": "SMS Bulk Personalizer",
                "description": "Uses LLM to rewrite bulk SMS based on individual lead dossiers.",
                "author": "CommFlow",
                "security_audit_id": "AUDIT-2026-002",
                "workflow_sample": {"name": "SMS Persona", "steps": ["Read Dossier", "Generate Text", "Send"]},
            },
            {
                "name": "Unverified Scraper",
                "description": "Scrapes property data from non-standard sources. No security audit.",
                "author": "ShadowDev",
                # Missing security_audit_id to test rejection
                "workflow_sample": {"name": "Shadow Scrape", "steps": ["Scrape"]},
            },
        ]

        for skill in available_skills:
            with st.expander(f"📦 {skill['name']} by {skill['author']}"):
                st.write(skill["description"])
                st.code(json.dumps(skill["workflow_sample"], indent=2), language="json")

                if st.button(f"Install {skill['name']}", key=f"install_{skill['name']}"):
                    with st.spinner(f"Governor validating {skill['name']}..."):
                        success = governor.install_skill(skill)
                        if success:
                            st.success(f"✅ {skill['name']} installed successfully!")
                        else:
                            st.error(f"❌ Installation REJECTED by MarketplaceGovernor. See Audit Manifest.")

    with tab2:
        st.subheader("Governor Security Queue")
        st.info("The MarketplaceGovernor is actively scanning incoming skill requests.")

        col1, col2, col3 = st.columns(3)
        col1.metric("Validated Skills", "14")
        col2.metric("Rejected (Security)", "3", delta="-1", delta_color="inverse")
        col3.metric("Pending Review", "1")

        st.markdown("#### Recent Governor Actions")
        governance_history = [
            {
                "time": "10:45 AM",
                "skill": "Zillow Trend Predictor",
                "action": "APPROVED",
                "reason": "Audit ID Verified",
            },
            {
                "time": "09:30 AM",
                "skill": "Unverified Scraper",
                "action": "REJECTED",
                "reason": "Missing Security Audit ID",
            },
            {
                "time": "08:15 AM",
                "skill": "PII Harvester",
                "action": "BLOCKED",
                "reason": "Malicious patterns detected in scan",
            },
        ]

        for action in governance_history:
            color = "green" if action["action"] == "APPROVED" else "red"
            st.markdown(
                f"**{action['time']}** | {action['skill']} | <span style='color:{color}'>{action['action']}</span> - {action['reason']}",
                unsafe_allow_html=True,
            )

    with tab3:
        st.subheader("📜 Real-Time Audit Manifest")
        st.caption("Live feed from AUDIT_MANIFEST.md")

        try:
            with open("AUDIT_MANIFEST.md", "r") as f:
                manifest_content = f.read()
            st.markdown(manifest_content)
        except FileNotFoundError:
            st.warning("Audit Manifest not yet generated. Perform a governance action to initialize.")


def render_marketplace_sidebar_widget():
    """A small widget for the sidebar to show marketplace status."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏪 Marketplace Status")
    st.sidebar.markdown("**Active Skills:** 14")
    st.sidebar.markdown("**Governor:** 🛡️ PROTECTED")
    if st.sidebar.button("Manage Marketplace", use_container_width=True):
        st.session_state.current_hub = "Marketplace Management"
        st.rerun()
