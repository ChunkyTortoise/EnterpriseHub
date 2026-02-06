"""
Technical Due Diligence Module
Rigorous technical evaluation of AI systems for PE firms and investors (Service 2).
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import utils.ui as ui
import time

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
    
    with st.expander("🚀 **Interactive: Generate Preliminary Audit Report**", expanded=False):
        _render_audit_generator()

def _render_audit_generator():
    st.markdown("### 📝 AI-Powered Architecture Audit Generator")
    st.write("Enter system details and optionally upload architecture files for comprehensive analysis.")
    
    with st.form("audit_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            target_name = st.text_input("Target System/Company Name", placeholder="e.g., Nexus AI Corp")
            tech_stack = st.text_area("High-Level Tech Stack", placeholder="e.g., Python, FastAPI, OpenAI API, Pinecone, AWS Lambda", height=100)
        
        with col2:
            compliance_needs = st.multiselect("Compliance Requirements", ["SOC2", "HIPAA", "GDPR", "PCI-DSS", "None"])
            
            st.markdown("**📎 Optional: Upload Architecture Files**")
            uploaded_file = st.file_uploader(
                "Upload JSON, Terraform, or YAML config", 
                type=['json', 'tf', 'yaml', 'yml', 'txt'],
                help="Upload infrastructure-as-code or config files for deeper analysis"
            )
        
        col_submit1, col_submit2 = st.columns([3, 1])
        with col_submit1:
            submitted = st.form_submit_button("🚀 Generate Audit Report", type="primary", use_container_width=True)
        with col_submit2:
            st.caption("Takes ~2 seconds")
        
        if submitted:
            if not target_name:
                st.error("Please provide a target name.")
            else:
                from utils.audit_agent import AuditAgent
                
                # Process uploaded file
                file_content = None
                file_type = None
                if uploaded_file:
                    file_content = uploaded_file.read().decode('utf-8')
                    file_type = uploaded_file.name.split('.')[-1]
                    st.success(f"✅ Analyzing uploaded {file_type.upper()} file: {uploaded_file.name}")
                
                agent = AuditAgent(target_name, tech_stack, compliance_needs, file_content, file_type)
                
                with st.spinner("🧠 AI Agent scanning architecture patterns & security vulnerabilities..."):
                    time.sleep(2.0) # Simulate deep analysis
                    
                    st.success(f"✅ Audit Report Generated for {target_name}")
                    ui.toast(f"Audit report generated for {target_name}", "success")
                    
                    # Get all findings (base + file analysis)
                    findings = agent.get_all_findings()
                    
                    # Summary metrics
                    st.markdown("---")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        critical_count = len([f for f in findings if f['severity'] == 'Critical'])
                        ui.card_metric("Critical Issues", str(critical_count), "🚨 Urgent")
                    with col2:
                        high_count = len([f for f in findings if f['severity'] == 'High'])
                        ui.card_metric("High Priority", str(high_count), "⚠️ Important")
                    with col3:
                        medium_count = len([f for f in findings if f['severity'] == 'Medium'])
                        ui.card_metric("Medium Risk", str(medium_count), "📊 Review")
                    with col4:
                        ui.card_metric("Total Findings", str(len(findings)), "Complete Scan")
                    
                    st.markdown("---")
                    
                    c1, c2 = st.columns([3, 2])
                    
                    with c1:
                        st.markdown(f"#### 🚩 Priority Findings for {target_name}")
                        
                        # Group by severity
                        for severity in ['Critical', 'High', 'Medium', 'Low']:
                            severity_findings = [f for f in findings if f['severity'] == severity]
                            if severity_findings:
                                st.markdown(f"##### {severity} Severity ({len(severity_findings)})")
                                
                                for f in severity_findings:
                                    severity_color = {"Critical": "red", "High": "orange", "Medium": "blue", "Low": "gray"}.get(f['severity'], "gray")
                                    with st.expander(f":{severity_color}[{f.get('category', 'General')}] - {f['issue']}", expanded=(severity == 'Critical')):
                                        st.write(f"**Details:** {f['details']}")
                                        st.info(f"**Remediation:** {f['remediation']}")
                    
                    with c2:
                        st.markdown("#### 📊 System Debt Distribution")
                        debt_data = agent.get_system_debt_data()
                        fig = go.Figure(data=[
                            go.Bar(
                                x=debt_data['nodes'], 
                                y=debt_data['debt_scores'],
                                marker_color=["#ef4444" if s > 60 else "#3b82f6" for s in debt_data['debt_scores']]
                            )
                        ])
                        fig.update_layout(
                            height=300, 
                            margin=dict(l=10, r=10, t=10, b=10),
                            yaxis_title="Debt Index",
                            template=ui.get_plotly_template()
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption("Visualizing estimated technical debt across core infrastructure components.")

                    st.divider()
                    
                    # Export options
                    st.markdown("#### 📥 Export Audit Report")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Generate markdown report
                        markdown_report = agent.generate_audit_report_markdown()
                        st.download_button(
                            label="📄 Download Markdown Report",
                            data=markdown_report,
                            file_name=f"audit_report_{target_name.replace(' ', '_')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    
                    with col2:
                        st.button("📧 Email to Team", use_container_width=True, disabled=True)
                        st.caption("Coming in v6.5")
                    
                    with col3:
                        st.button("📊 Generate PDF", use_container_width=True, disabled=True)
                        st.caption("Coming in v6.5")
                    
                    st.divider()
                    st.info("💡 **Next Step:** Proceed to **S2 Deep-Dive** for full source code scanning, dependency analysis, and vulnerability mapping.")
                    st.markdown("[📅 Schedule Deep-Dive Assessment](mailto:caymanroden@gmail.com?subject=S2%20Technical%20Due%20Diligence)")

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
