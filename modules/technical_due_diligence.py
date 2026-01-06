"""
Technical Due Diligence Module
Rigorous technical evaluation of AI systems for PE firms and investors (Service 2).
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import utils.ui as ui

def render():
    """Main render function for Technical Due Diligence."""
    ui.section_header("Technical Due Diligence", "The AI Audit: Know exactly what you're buying, building, or inheriting.")
    
    tabs = st.tabs(["🔍 Audit Framework", "📉 Risk Register", "💰 Valuation Impact"])
    
    with tabs[0]:
        _render_audit_framework()
    
    with tabs[1]:
        _render_risk_register()
        
    with tabs[2]:
        _render_valuation_impact()

def _render_audit_framework():
    st.markdown("### 📋 AI System Audit Framework")
    st.write("Evaluate system maturity across 5 critical dimensions.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        architecture = st.select_slider("Architecture & Scalability", options=["Legacy", "Modular", "Cloud-Native", "Self-Healing"])
        code_quality = st.select_slider("Code Quality & Security", options=["Critical Debt", "Basic", "Clean", "Elite"])
        model_perf = st.select_slider("Model Performance", options=["High Hallucination", "Variable", "Stable", "State-of-the-Art"])
        data_infra = st.select_slider("Data Infrastructure", options=["Messy", "Siloed", "Integrated", "Compliant (SOC2/HIPAA)"])
        ops_maturity = st.select_slider("Ops Maturity (MLOps)", options=["Manual", "Basic CI/CD", "Automated", "Autonomous"])

    # Score calculation
    scores = {
        "Architecture": ["Legacy", "Modular", "Cloud-Native", "Self-Healing"].index(architecture) + 1,
        "Code": ["Critical Debt", "Basic", "Clean", "Elite"].index(code_quality) + 1,
        "Model": ["High Hallucination", "Variable", "Stable", "State-of-the-Art"].index(model_perf) + 1,
        "Data": ["Messy", "Siloed", "Integrated", "Compliant (SOC2/HIPAA)"].index(data_infra) + 1,
        "Ops": ["Manual", "Basic CI/CD", "Automated", "Autonomous"].index(ops_maturity) + 1
    }
    
    avg_score = sum(scores.values()) / len(scores)
    
    with col2:
        st.markdown("#### 📊 Maturity Radar")
        fig = go.Figure(data=go.Scatterpolar(
            r=list(scores.values()),
            theta=list(scores.keys()),
            fill='toself',
            marker_color=ui.THEME["accent"]
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 4])), showlegend=False, height=350)
        st.plotly_chart(fig, use_container_width=True)
        
        ui.animated_metric("Composite Maturity Score", f"{avg_score:.1f}/4.0", delta=f"{'High Risk' if avg_score < 2 else 'Low Risk'}")

def _render_risk_register():
    st.markdown("### 📉 Technical Risk Register")
    
    risks = pd.DataFrame([
        {"Category": "Technical Debt", "Risk": "Monolithic architecture limiting horizontal scale", "Severity": "High", "Remediation": "$150k Refactor"},
        {"Category": "Security", "Risk": "Lack of SOC2 compliant audit trails for LLM inputs", "Severity": "Medium", "Remediation": "Implement Logging"},
        {"Category": "Operational", "Risk": "Manual retraining pipeline causing model drift", "Severity": "High", "Remediation": "Deploy MLOps Hub"},
        {"Category": "Legal", "Risk": "Undefined IP ownership of training synthetic data", "Severity": "Critical", "Remediation": "Legal Audit"}
    ])
    
    st.table(risks)
    st.info("💡 **ROI Example:** Technical due diligence prevents $200k-$2M+ in acquisition value destruction.")

def _render_valuation_impact():
    st.markdown("### 💰 Valuation Impact Assessment")
    
    col1, col2 = st.columns(2)
    with col1:
        deal_value = st.number_input("Proposed Deal Value ($M)", value=10.0, step=1.0)
        tech_discount = st.slider("Tech Debt Valuation Discount (%)", 0, 30, 15)
    
    impact = deal_value * (tech_discount / 100)
    final_val = deal_value - impact
    
    with col2:
        ui.animated_metric("Valuation Adjustment", f"-${impact:.1f}M", icon="⚠️")
        ui.animated_metric("Risk-Adjusted Value", f"${final_val:.1f}M", icon="💰")
        
    st.success(f"Identification of technical debt enables **{tech_discount}%** negotiation leverage on the final deal structure.")
