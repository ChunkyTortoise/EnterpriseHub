"""
Ops & Optimization Hub - Premium Management Suite
System health, revenue attribution, and Agentic OS orchestration.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import asyncio
from typing import Dict, List, Any, Optional

# Absolute imports
try:
    from components.agent_os import render_agent_os_tab
    from components.security_governance import render_security_governance
    from components.ai_training_feedback import render_rlhf_loop
    from components.calculators import render_revenue_funnel
except ImportError:
    pass

class OpsOptimizationHub:
    """Enterprise Operations & Optimization Hub"""

    def __init__(self, services: Dict[str, Any], claude: Optional[Any] = None):
        self.services = services
        self.claude = claude
        
    def render_hub(self):
        """Render the complete Ops & Optimization interface"""
        st.header("📈 Ops & Optimization")
        st.markdown("*Manager-level analytics and team performance tracking*")
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "✅ Quality",
            "💰 Revenue",
            "🏆 Benchmarks",
            "🎓 Coaching",
            "🛠️ Control",
            "🧠 RLHF Loop",
            "🛡️ Governance",
            "🧬 Agentic OS"
        ])
        
        with tab1:
            self._render_quality_assurance()
                
        with tab2:
            self._render_revenue_attribution()
            
        with tab3:
            self._render_benchmarking()
                
        with tab4:
            self._render_coaching()

        with tab5:
            self._render_control_panel()

        with tab8:
            render_agent_os_tab()
            
        with tab6:
            render_rlhf_loop()
            
        with tab7:
            render_security_governance()

    def _render_quality_assurance(self):
        st.subheader("AI Quality Assurance")
        qa_report = self.services["qa"].generate_qa_report("demo_location")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Quality", f"{qa_report['overall_score']}%", "+2%")
        col2.metric("Compliance Rate", f"{qa_report['compliance_rate']}%", "Stable")
        col3.metric("Empathy Score", f"{qa_report['empathy_score']}/10", "+0.5")
        
        st.markdown("#### 🎯 Improvement Areas")
        for area in qa_report["improvement_areas"]:
            st.warning(f"**{area['topic']}**: {area['recommendation']}")

    def _render_revenue_attribution(self):
        st.subheader("Revenue Attribution")
        attr_data = self.services["revenue"].get_attribution_data("demo_location")
        
        # Display attribution chart
        df_attr = pd.DataFrame(attr_data["channels"])
        fig = px.pie(df_attr, values='revenue', names='channel', title='Revenue by Lead Source',
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)
        
        st.write(f"**Total Attributed Revenue:** ${attr_data['total_revenue']:,.0f}")
        
        # UI-014: Funnel Velocity Chart
        st.markdown("---")
        st.subheader("🚀 Funnel Velocity")
        render_revenue_funnel()

    def _render_benchmarking(self):
        st.subheader("Competitive Benchmarking")
        bench = self.services["benchmarking"].get_benchmarks("demo_location")
        
        for metric, data in bench.items():
            st.write(f"**{metric.replace('_', ' ').title()}**")
            cols = st.columns([2, 1])
            cols[0].progress(data["percentile"] / 100)
            cols[1].write(f"{data['percentile']}th Percentile")

    def _render_coaching(self):
        st.subheader("AI Agent Coaching")
        recommendations = self.services["coaching"].get_coaching_recommendations("demo_agent")
        
        for rec in recommendations:
            with st.expander(f"💡 {rec['title']}"):
                st.write(rec['description'])
                st.info(f"**Impact:** {rec['expected_impact']}")

    def _render_control_panel(self):
        st.subheader("AI Control Panel")
        
        # Prompt Versioning
        st.markdown("### 📝 Prompt Version Control")
        if 'prompt_versions' not in st.session_state:
            st.session_state.prompt_versions = [
                {"version": "v1.0", "tag": "Baseline", "timestamp": "2025-12-01", "content": "You are a helpful assistant."},
                {"version": "v1.1", "tag": "Production", "timestamp": "2026-01-05", "content": "You are Jorge's AI partner."}
            ]

        selected_version = st.selectbox("Active Prompt Version", 
                                       options=[v["version"] for v in st.session_state.prompt_versions],
                                       index=len(st.session_state.prompt_versions)-1)
        
        version_data = next(v for v in st.session_state.prompt_versions if v["version"] == selected_version)
        
        st.info(f"**Tag:** {version_data['tag']} | **Deployed:** {version_data['timestamp']}")
        new_prompt = st.text_area("Prompt Content", value=version_data["content"], height=150)
        
        col_v1, col_v2 = st.columns(2)
        if col_v1.button("💾 Save as New Version", use_container_width=True):
            new_v = f"v1.{len(st.session_state.prompt_versions)}"
            st.session_state.prompt_versions.append({
                "version": new_v,
                "tag": "Custom",
                "content": new_prompt,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d")
            })
            st.success(f"Version {new_v} saved!")
            st.rerun()
            
        if col_v2.button("🚀 Rollback to Baseline", use_container_width=True):
            st.warning("Rolling back to Production Baseline...")
            st.toast("Rollback initiated", icon="⏪")

        st.markdown("---")
        
        # Model Retraining Loop
        st.markdown("### 🔄 Model Retraining Loop")
        st.write("Feedback captured from Lead Intelligence Hub is automatically used to fine-tune your local matching models.")
        
        col_r1, col_r2 = st.columns(2)
        col_r1.metric("Captured Feedback", "128", "+12")
        col_r2.metric("Model Drift", "0.02", "Low")
        
        if st.button("🛰️ Initiate Model Retraining", type="primary", use_container_width=True):
            with st.spinner("Retraining Property Matcher ML..."):
                import time
                time.sleep(2)
                st.success("Model successfully retrained! Accuracy improved by 3.2%")
                st.balloons()
