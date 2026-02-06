"""
Service Selector Module
Interactive AI Strategy Planner overhaul aligned with the 31-service catalog.
"""
import streamlit as st
import utils.ui as ui

SERVICES = {
    "Strategic": {
        "S1": {"title": "AI Strategy & Readiness", "roi": "Prevents $50k-$200k misallocated spend", "investment": "$6,400+"}, "S2": {"title": "Technical Due Diligence", "roi": "Identifies $50k-$300k hidden costs", "investment": "$8,000+"}, "S25": {"title": "Fractional AI Leadership", "roi": "119% 12-month ROI", "investment": "$8,000/mo"}, "S23": {"title": "AI Compliance (HIPAA/SOC2)", "roi": "Mitigates $200k-$2M risk", "investment": "$4,000+"}
    },
    "Automation": {
        "S3": {"title": "Custom RAG Agents", "roi": "60% reduction in support load", "investment": "$3,600+"}, "S4": {"title": "Multi-Agent Swarms", "roi": "10,000%+ ROI (Lead Research)", "investment": "$5,200+"}, "S6": {"title": "Business Automation", "roi": "15-20 hours saved weekly", "investment": "$1,400+"}, "S12": {"title": "Programmatic SEO Engine", "roi": "17,000%+ 12-month ROI", "investment": "$4,400+"}
    },
    "Data & BI": {
        "S8": {"title": "Interactive BI Dashboards", "roi": "8,000% ROI (Churn Reduction)", "investment": "$3,200+"}, "S9": {"title": "Automated Reporting", "roi": "19 hours saved weekly", "investment": "$2,200+"}, "S10": {"title": "Predictive Lead Scoring", "roi": "8,000% ROI (Sales focus)", "investment": "$4,400+"}, "S11": {"title": "Data Rescue (Cleanup)", "roi": "800% ROI (Data accuracy)", "investment": "$960+"}
    }
}

def render():
    tabs = st.tabs(["🎯 Strategy Diagnostic", "💰 Fixed-Price Catalog", "🎓 Credentials"])
    with tabs[0]: _render_diagnostic()
    with tabs[1]: _render_catalog()
    with tabs[2]: ui.credential_inventory()

def _render_diagnostic():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### 🔍 Business Diagnostic")
        challenge = st.selectbox("1. Primary Business Challenge", [
            "Manual processes consuming team time",
            "Poor data visibility / decision-making",
            "Growth / Customer acquisition issues",
            "Legacy systems / Fragile Excel sheets",
            "Regulatory / Compliance concerns",
            "Need high-level AI strategy guidance"
        ])
        budget = st.select_slider("2. Available Budget Range", options=["Under $2k", "$2k - $10k", "$10k - $25k", "$25k+"])
        timeline = st.selectbox("3. Implementation Timeline", ["This week (Immediate)", "This month (Tactical)", "This quarter (Strategic)"])
        industry = st.selectbox("4. Industry Vertical", ["B2B SaaS", "E-commerce", "Healthcare", "Professional Services", "Real Estate", "Manufacturing"])
        
        if st.button("Generate Strategy Roadmap", type="primary"):
            _generate_roadmap(challenge, budget, timeline, industry)
    
    with col2:
        st.markdown("#### 💡 Recommended Architecture")
        if "recs_v3" in st.session_state:
            for s_code in st.session_state.recs_v3:
                for cat, svcs in SERVICES.items():
                    if s_code in svcs:
                        s = svcs[s_code]
                        ui.use_case_card(icon="✅", title=s["title"], description=f"**{s_code}**<br>ROI: {s['roi']}<br>Investment: {s['investment']}")
        else:
            st.info("Complete the diagnostic to see recommendations.")

def _render_catalog():
    st.markdown("### 📋 2026 Professional Services Catalog")
    for category, items in SERVICES.items():
        with st.expander(f"**{category} Services**", expanded=True):
            cols = st.columns(2)
            for i, (code, svc) in enumerate(items.items()):
                with cols[i % 2]:
                    st.markdown(f"**{code}: {svc['title']}**\n\n*ROI: {svc['roi']}*\n\n**Investment: {svc['investment']}**")
                    st.divider()

def _generate_roadmap(challenge, budget, timeline, industry):
    recs = []
    if "Manual" in challenge: recs.extend(["S3", "S4", "S6"])
    if "visibility" in challenge: recs.extend(["S8", "S9", "S10"])
    if "Growth" in challenge: recs.extend(["S12", "S10"])
    if "Compliance" in challenge: recs.append("S23")
    if "Strategy" in challenge: recs.append("S1")
    
    if budget == "Under $2k": recs = [r for r in recs if r in ["S6", "S11"]]
    elif budget == "$2k - $10k": recs = [r for r in recs if r not in ["S2", "S25"]]
    
    st.session_state.recs_v3 = list(dict.fromkeys(recs))[:4] or ["S1"]
    st.success("Strategy Roadmap Generated!")
