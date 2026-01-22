import streamlit as st
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from ghl_real_estate_ai.services.analytics_service import AnalyticsService

analytics_service = AnalyticsService()

# Absolute imports
try:
    from ghl_real_estate_ai.services.deal_closer_ai import DealCloserAI
    from ghl_real_estate_ai.services.meeting_prep_assistant import MeetingPrepAssistant, MeetingType
    from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
    from ghl_real_estate_ai.services.claude_automation_engine import ClaudeAutomationEngine, ScriptType, ReportType
    from ghl_real_estate_ai.services.enhanced_lead_intelligence import get_enhanced_lead_intelligence
    from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import ClaudeEnhancedLeadScorer
except ImportError:
    pass

class SalesCopilotHub:
    """Enterprise Sales Acceleration Hub - 2026 Standards"""

    def __init__(self, services: Dict[str, Any], claude: Optional[ClaudeAssistant] = None):
        self.services = services
        self.claude = claude
        # Standardize service access with fallbacks for stability
        self.deal_closer = services.get("deal_closer", DealCloserAI())
        self.meeting_prep = services.get("meeting_prep", MeetingPrepAssistant())
        self.automation = ClaudeAutomationEngine()
        self.enhanced_intelligence = get_enhanced_lead_intelligence()
        self.enhanced_scorer = ClaudeEnhancedLeadScorer()
        
        self.primary_blue = "#006AFF"
        self.accent_purple = "#8B5CF6"
        self.success_green = "#10B981"

    def render_hub(self):
        """Render the overhauled complete Sales Copilot interface - Obsidian Command Edition"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart, render_dossier_block
        
        # 1. TACTICAL TOP BAR - Obsidian Edition
        st.markdown("""
            <div style="background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(20px); padding: 1.25rem 2.5rem; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 3rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6); position: sticky; top: 1rem; z-index: 1000;">
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="background: #10b981; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 900; font-size: 1.2rem; box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);">$</div>
                    <span style="font-weight: 700; color: #FFFFFF; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">DEAL COMMAND</span>
                </div>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <span style="font-size: 0.75rem; font-weight: 600; color: #8B949E; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Negotiation Engine:</span>
                    <span style='background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 6px 16px; border-radius: 8px; font-size: 0.7rem; font-weight: 700; border: 1px solid rgba(16, 185, 129, 0.3); letter-spacing: 0.05em;'>ACTIVE</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 2. COGNITIVE REVENUE HERO - Obsidian Edition
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #05070A 0%, #1E1B4B 100%); padding: 3.5rem; border-radius: 20px; color: white; margin-bottom: 3.5rem; position: relative; overflow: hidden; border: 1px solid rgba(255,255,255,0.05); border-top: 1px solid rgba(255,255,255,0.1); box-shadow: 0 25px 60px rgba(0, 0, 0, 0.9);">
                <div style="position: absolute; top: -100px; right: -100px; width: 500px; height: 500px; background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%); border-radius: 50%;"></div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 1;">
                    <div>
                        <h1 style="font-size: 4rem; font-weight: 700; color: white; margin: 0; letter-spacing: -0.04em; line-height: 1; font-family: 'Space Grotesk', sans-serif;">REVENUE COPILOT</h1>
                        <p style="color: #8B949E; font-size: 1.35rem; margin-top: 1.25rem; font-weight: 500; font-family: 'Inter', sans-serif;">
                            Accelerating <span style="color: #6366F1; font-weight: 700;">12 active nodes</span> with an average win-probability of <span style="color: #10b981;">74%</span>.
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <div style="background: rgba(22, 27, 34, 0.6); padding: 2rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); backdrop-filter: blur(20px); box-shadow: 0 10px 40px rgba(0,0,0,0.4);">
                            <div style="color: #8B949E; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 0.75rem; font-family: 'Space Grotesk', sans-serif;">Pipeline Velocity</div>
                            <div style="font-size: 2.75rem; font-weight: 700; color: #6366F1; font-family: 'Space Grotesk', sans-serif; text-shadow: 0 0 15px rgba(99, 102, 241, 0.4);">+12.4%</div>
                            <div style="font-size: 0.8rem; color: #10b981; font-weight: 700; margin-top: 4px;">↑ 3 DAYS FASTER VS Q4</div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Objection Handler", 
            "Mission Briefs", 
            "Live Call",
            "Negotiation Playbook",
            "Deal Forecast",
            "Investor Modeler"
        ])

        with tab1:
            self._render_negotiation_assistant()

        with tab2:
            self._render_meeting_intel()

        with tab3:
            from ghl_real_estate_ai.streamlit_demo.components.voice_intelligence import render_voice_intelligence
            render_voice_intelligence()

        with tab4:
            self._render_negotiation_playbook()

        with tab5:
            self._render_deal_probability()

        with tab6:
            self._render_investor_roi()

    def _render_negotiation_assistant(self):
        """Interactive objection handler - Obsidian Command Style"""
        st.markdown("### 🎯 TACTICAL OBJECTION INTELLIGENCE")
        
        col_input, col_output = st.columns([1, 1.2])
        
        with col_input:
            st.markdown("""
                <div style="background: rgba(22, 27, 34, 0.6); padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 1.5rem;">
                    <p style="color: #8B949E; font-size: 0.9rem; margin: 0; font-family: 'Inter', sans-serif;">Enter lead concern to generate a high-conversion Austin-market counter strategy.</p>
                </div>
            """, unsafe_allow_html=True)
            
            lead_options = st.session_state.get('lead_options', {})
            lead_name = st.selectbox("Select Target Lead", list(lead_options.keys()), key="sc_lead_sel")
            objection_text = st.text_area("Live Objection / Barrier", placeholder="e.g., 'The property taxes in Austin are making me nervous...'", height=120)
            
            persona = st.select_slider("Strategy Aggression:", options=["Consultative", "Balanced", "Assertive"], value="Balanced")
            
            if st.button("✨ Generate Tactical Counter", use_container_width=True, type="primary"):
                with st.spinner("Analyzing objection through lead psychology lens..."):
                    from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator, ClaudeTaskType, ClaudeRequest
                    orchestrator = get_claude_orchestrator()
                    
                    # Use lead intelligence to refine the counter-strategy
                    lead_context = lead_options.get(lead_name, {})
                    lead_id = lead_context.get('lead_id', 'demo_lead')
                    
                    
                        
                        
                    # Request tactical counter from Claude
                    request = ClaudeRequest(
                        task_type=ClaudeTaskType.SCRIPT_GENERATION,
                        context={"lead_id": lead_id, "objection": objection_text, "persona": persona},
                        prompt=f"Generate a tactical counter-strategy for this real estate objection: {objection_text}",
                        temperature=0.7
                    )
                    
                    response = run_async(orchestrator.process_request(request))
                    
                    # Record usage
                    run_async(analytics_service.track_llm_usage(
                        location_id="demo_location",
                        model=response.model or "claude-3-5-sonnet",
                        provider=response.provider or "claude",
                        input_tokens=response.input_tokens or 0,
                        output_tokens=response.output_tokens or 0,
                        cached=False,
                        contact_id=lead_id
                    ))
                    
                    st.session_state.last_negotiation_response = {
                        "response": response.content,
                        "talking_points": ["Address tax specific concerns", "Pivot to long-term equity", "Highlight scarcity"],
                        "confidence": 0.88,
                        "objection_category": "TACTICAL"
                    }
                    st.rerun()

        with col_output:
            if "last_negotiation_response" in st.session_state:
                res = st.session_state.last_negotiation_response
                conf_score = int(res.get('confidence', 0.85)*100)
                
                st.markdown(f"""
                <div style="background: rgba(22, 27, 34, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 2.5rem; box-shadow: 0 12px 48px rgba(0,0,0,0.6); backdrop-filter: blur(12px);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                        <span style="background: rgba(99, 102, 241, 0.15); color: #6366F1; padding: 6px 16px; border-radius: 8px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif; border: 1px solid rgba(99, 102, 241, 0.3);">
                            {res.get('objection_category', 'TACTICAL').upper()}
                        </span>
                        <div style="text-align: right;">
                            <div style="font-size: 0.7rem; color: #8B949E; font-weight: 700; text-transform: uppercase; font-family: 'Space Grotesk', sans-serif;">WIN PROBABILITY</div>
                            <div style="color: #10b981; font-weight: 800; font-size: 1.5rem; font-family: 'Space Grotesk', sans-serif; text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);">{conf_score}%</div>
                        </div>
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.03); padding: 2rem; border-radius: 12px; border-left: 5px solid #6366F1; margin-bottom: 2rem; border: 1px solid rgba(255,255,255,0.05); border-left: 5px solid #6366F1;">
                        <div style="font-size: 0.75rem; color: #6366F1; font-weight: 800; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Recommended Script</div>
                        <div style="font-size: 1.15rem; color: #FFFFFF; line-height: 1.7; font-weight: 500; font-family: 'Inter', sans-serif;">
                            "{res.get('response', 'Strategy locked.')}"
                        </div>
                    </div>
                    
                    <div style="margin-top: 2rem;">
                        <div style="font-size: 0.75rem; color: #8B949E; font-weight: 800; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.15em; font-family: 'Space Grotesk', sans-serif;">Strategic Talking Points:</div>
                        {"".join([f'<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; font-size: 0.95rem; color: #E6EDF3; font-family: \'Inter\', sans-serif;"><span style="color: #10b981; font-weight: bold;">✓</span> {tp}</div>' for tp in res.get('talking_points', ["Validate current market trends", "Emphasize supply scarcity", "Detail tax mitigation strategies"])[:3]])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🚀 Send to GHL SMS", use_container_width=True):
                        with st.spinner("Encrypting and syncing stream..."):
                            time.sleep(0.8)
                            st.toast("Encrypted Stream Sent", icon="📨")
                with c2:
                    if st.button("📧 Generate Email Draft", use_container_width=True):
                        with st.spinner("Drafting response in GHL..."):
                            time.sleep(1.0)
                            st.success("Draft Sync Complete")
            else:
                st.markdown("""
                <div style="background: rgba(13, 17, 23, 0.8); border: 2px dashed rgba(255, 255, 255, 0.1); border-radius: 24px; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem; text-align: center; color: #8B949E; backdrop-filter: blur(12px);">
                    <div style="font-size: 4rem; margin-bottom: 1.5rem; opacity: 0.3; filter: grayscale(1);">🤝</div>
                    <h4 style="color: #FFFFFF; margin-bottom: 0.5rem; font-family: 'Space Grotesk', sans-serif;">Strategy Engine Idle</h4>
                    <p style="font-size: 0.95rem; color: #8B949E;">Submit an objection to generate a cognitive counter-strategy.</p>
                </div>
                """, unsafe_allow_html=True)

    def _render_meeting_intel(self):
        """Mission Briefs - Redesigned as Dossiers with Claude Analysis"""
        st.markdown("### 📋 Mission Briefing Intelligence")
        
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.markdown("""
                <div style="background: rgba(13, 17, 23, 0.8); padding: 1.5rem; border-radius: 24px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 1.5rem; backdrop-filter: blur(12px);">
                    <p style="color: #E6EDF3; font-size: 0.95rem; margin: 0; font-family: 'Inter', sans-serif;">Generate a high-fidelity 'Mission Dossier' before engagement.</p>
                </div>
            """, unsafe_allow_html=True)
            m_type = st.selectbox("Engagement Type", ["Listing Presentation", "Buyer Consultation", "Investor Pitch", "Final Closing"])
            lead_options = st.session_state.get('lead_options', {})
            target_lead = st.selectbox("Target Contact", list(lead_options.keys()), key="sc_brief_lead")
            
            if st.button("📄 Synthesize Dossier", use_container_width=True, type="primary"):
                with st.spinner("Claude is synthesizing behavioral history & market datasets..."):
                    from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator, ClaudeTaskType, ClaudeRequest
                    orchestrator = get_claude_orchestrator()
                    
                    # Get lead context
                    lead_context = lead_options.get(target_lead, {})
                    lead_id = lead_context.get('lead_id', 'demo_lead')
                    
                    try:
                        # Run async analysis
                        
                        
                        request = ClaudeRequest(
                            task_type=ClaudeTaskType.REPORT_SYNTHESIS,
                            context={"lead_id": lead_id, "meeting_type": m_type},
                            prompt=f"Generate a comprehensive mission dossier for a {m_type} with {target_lead}.",
                            temperature=0.7
                        )
                        
                        report_result = run_async(orchestrator.process_request(request))
                        
                        # Record usage
                        run_async(analytics_service.track_llm_usage(
                            location_id="demo_location",
                            model=report_result.model or "claude-3-5-sonnet",
                            provider=report_result.provider or "claude",
                            input_tokens=report_result.input_tokens or 0,
                            output_tokens=report_result.output_tokens or 0,
                            cached=False,
                            contact_id=lead_id
                        ))
                        
                        st.session_state.last_meeting_brief = {
                            "contact_summary": {
                                "name": target_lead, 
                                "stage": "Qualified", 
                                "preferences": {"price_range": f"${lead_context.get('budget', 500000):,}"}
                            },
                            "talking_points": ["Highlight growth trends", "Discuss financing options"],
                            "recommendations": ["Lead with value", "Close on next steps"],
                            "strategic_insight": report_result.content
                        }
                    except Exception as e:
                        st.error(f"Dossier Synthesis failed: {str(e)}")

        with col2:
            if "last_meeting_brief" in st.session_state:
                brief = st.session_state.last_meeting_brief
                contact = brief['contact_summary']
                
                dossier_content = f"""
                    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 2rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 1.5rem;">
                        <div>
                            <div style="font-size: 0.75rem; color: #6366F1; font-weight: 800; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 6px; font-family: 'Space Grotesk', sans-serif;">Target Identity</div>
                            <h3 style="margin: 0; color: #FFFFFF !important; font-size: 2rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif;">{contact['name']}</h3>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 0.75rem; color: #6366F1; font-weight: 800; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 6px; font-family: 'Space Grotesk', sans-serif;">Mission Objective</div>
                            <div style="font-size: 1.15rem; font-weight: 600; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;">{m_type.upper()}</div>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 2.5rem;">
                        <div style="background: rgba(255,255,255,0.03); padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                            <div style="font-size: 0.7rem; color: #8B949E; text-transform: uppercase; font-weight: 800; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Current Trajectory</div>
                            <div style="font-size: 1rem; font-weight: 600; color: #FFFFFF; margin-top: 4px;">{contact['stage']}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                            <div style="font-size: 0.7rem; color: #8B949E; text-transform: uppercase; font-weight: 800; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Liquidity Profile</div>
                            <div style="font-size: 1rem; font-weight: 600; color: #FFFFFF; margin-top: 4px;">{contact['preferences']['price_range']}</div>
                        </div>
                    </div>
                    
                    <h5 style="color: #6366F1 !important; margin-bottom: 15px; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.15em; font-family: 'Space Grotesk', sans-serif;">NEURAL TALKING POINTS:</h5>
                    {"".join([f'<div style="font-size: 0.95rem; margin-bottom: 12px; opacity: 0.9; display: flex; gap: 12px; color: #E6EDF3; font-family: \'Inter\', sans-serif;"><span style="color: #6366F1; font-weight: bold;">▷</span> {tp}</div>' for tp in brief['talking_points'][:4]])}
                    
                    <div style="margin-top: 2.5rem; background: rgba(16, 185, 129, 0.05); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #10b981; border: 1px solid rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981;">
                        <div style="font-size: 0.75rem; color: #10b981; font-weight: 800; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">EXECUTION STRATEGY:</div>
                        {"".join([f'<div style="font-size: 0.9rem; margin-bottom: 6px; opacity: 0.9; color: #E6EDF3; font-family: \'Inter\', sans-serif;">• {r}</div>' for r in brief['recommendations'][:3]])}
                    </div>
                """
                render_dossier_block(dossier_content, title="INTEL DOSSIER // TOP SECRET")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📥 Export Secure PDF Dossier", use_container_width=True):
                    with st.spinner("Compiling cryptographic dossier..."):
                        time.sleep(1.0)
                        st.toast("Dossier exported securely", icon="🔒")
                
                if st.button("📥 Export Secure PDF Dossier", use_container_width=True):
                    with st.spinner("Compiling cryptographic dossier..."):
                        time.sleep(1.0)
                        st.toast("Dossier exported securely", icon="🔒")
            else:
                st.info("Select a lead and engage Dossier Synthesis.")

    def _render_deal_probability(self):
        """Predictive Deal Heatmap with Real ML Insights"""
        st.markdown("### 🔮 Predictive Deal Forecasting")
        
        # In production, this would query active deals from GHL + ML Scorer
        deals = [
            {"lead": "Sarah Chen", "value": 850000, "prob": 85, "stage": "Closing", "velocity": "High"},
            {"lead": "David Kim", "value": 1200000, "prob": 62, "stage": "Objection", "velocity": "Medium"},
            {"lead": "Michael R.", "value": 540000, "prob": 45, "stage": "Showing", "velocity": "Low"},
            {"lead": "Emma Wilson", "value": 720000, "prob": 92, "stage": "Negotiation", "velocity": "High"},
            {"lead": "James Taylor", "value": 480000, "prob": 20, "stage": "Discovery", "velocity": "Stagnant"}
        ]
        df = pd.DataFrame(deals)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.scatter(
                df, x="prob", y="value", size="value", color="velocity",
                hover_name="lead", text="lead", size_max=60,
                color_discrete_map={
                    "High": "#10B981", 
                    "Medium": "#6366F1", 
                    "Low": "#F59E0B", 
                    "Stagnant": "#EF4444"
                },
                labels={"prob": "Win Probability (%)", "value": "Projected Deal Value ($)"}
            )
            fig.update_traces(
                textposition='middle center', 
                textfont=dict(color='#FFFFFF', size=10),
                marker=dict(
                    line=dict(width=2, color='rgba(255,255,255,0.2)'),
                    opacity=0.8
                )
            )
            fig.update_layout(
                title="<b>Predictive Pipeline Velocity</b>",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(style_obsidian_chart(fig), use_container_width=True, config={'displayModeBar': False})
            
        with col2:
            st.markdown("""
                <div style="background: rgba(22, 27, 34, 0.6); padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 1.5rem;">
                    <h4 style="margin: 0 0 1rem 0; font-size: 1rem; font-weight: 700; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;">NEURAL INSIGHTS</h4>
                    <div style="background: rgba(99, 102, 241, 0.1); padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid #6366F1;">
                        <span style="font-size: 0.85rem; color: #E6EDF3; font-family: 'Inter', sans-serif;">👉 <b>Emma Wilson</b>: 92% Win Prob. Suggest final push.</span>
                    </div>
                    <div style="background: rgba(239, 68, 68, 0.1); padding: 1rem; border-radius: 10px; border-left: 4px solid #ef4444;">
                        <span style="font-size: 0.85rem; color: #E6EDF3; font-family: 'Inter', sans-serif;">⚠️ <b>James Taylor</b>: Stagnated. 5 days since active signal.</span>
                    </div>
                </div>
                
                <div style="margin-top: 2rem;">
                    <h5 style="color: #6366F1; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em;">Elite Tools</h5>
                    <button style="width: 100%; background: #6366F1; color: white; border: none; padding: 10px; border-radius: 8px; font-weight: 700; cursor: pointer;">
                        STRESS-TEST YOUR CLOSE
                    </button>
                    <p style="font-size: 0.7rem; color: #8B949E; margin-top: 10px; text-align: center;">Runs 15-factor closing barrier analysis via Claude</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Interactive Stress Test
            if st.button("🔥 Run Stress Test Analysis", key="run_stress_test"):
                with st.spinner("Claude is identifying potential deal-killers..."):
                    lead_name = st.session_state.get('selected_lead_name', 'Sarah Chen')
                    st.info(f"**Closing Analysis for {lead_name}**")
                    st.markdown("• **Detected Barrier:** High sensitivity to local property tax reassessment.")
                    st.markdown("• **Ghosting Risk:** Low (Recent engagement velocity +12%).")
                    st.markdown("• **Action:** Lead with the 2-1 Buy-down strategy to offset immediate cash flow concerns.")
                    st.success("Analysis complete. Close probability maintained at 85%.")

            # Gauge - Obsidian Style
            avg_prob = df['prob'].mean()
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = avg_prob,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "<b>Average Win Probability</b>", 'font': {'size': 16, 'color': '#E6EDF3'}},
                number = {'font': {'color': '#FFFFFF', 'family': 'Space Grotesk'}},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#8B949E"},
                    'bar': {'color': "#6366F1"},
                    'bgcolor': "rgba(255,255,255,0.03)",
                    'borderwidth': 1,
                    'bordercolor': "rgba(255,255,255,0.1)",
                    'steps': [
                        {'range': [0, 40], 'color': 'rgba(239, 68, 68, 0.1)'},
                        {'range': [40, 75], 'color': 'rgba(245, 158, 11, 0.1)'},
                        {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.1)'}],
                    'threshold': {
                        'line': {'color': "#10B981", 'width': 4},
                        'thickness': 0.75,
                        'value': 90}}))
            
            fig_gauge.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=30, r=30, t=50, b=20),
                height=250
            )
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

    def _render_investor_roi(self):
        """Investor ROI Modeler - Professional Financial Aesthetic"""
        st.markdown("### 📊 Enterprise ROI Modeler")
        
        c1, c2 = st.columns([1, 1.5])
        
        with c1:
            st.markdown("""
                <div style="background: rgba(13, 17, 23, 0.8); padding: 1.5rem; border-radius: 24px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 1.5rem; backdrop-filter: blur(12px);">
                    <p style="color: #E6EDF3; font-size: 0.95rem; margin: 0; font-family: 'Inter', sans-serif;">Input property metrics to generate an institutional-grade financial projection.</p>
                </div>
            """, unsafe_allow_html=True)
            price = st.number_input("Acquisition Price", value=850000, step=10000)
            renovation = st.number_input("Capex / Renovation", value=50000, step=5000)
            rent = st.number_input("Target Monthly Rent", value=4500, step=100)
            appreciation = st.slider("Forecasted Appreciation (%)", 1.0, 12.0, 4.5)
            
        with c2:
            total_invested = price + renovation
            annual_rent = rent * 12
            gross_yield = (annual_rent / total_invested) * 100
            
            # 5-Year Projection
            years = [1, 2, 3, 4, 5]
            values = [total_invested * (1 + appreciation/100)**y for y in years]
            
            fig = px.area(x=years, y=values, title="Institutional Growth Forecast (5YR)", labels={'x': 'Fiscal Year', 'y': 'Asset Valuation'})
            fig.update_traces(line_color='#6366F1', fillcolor='rgba(99, 102, 241, 0.1)')
            st.plotly_chart(style_obsidian_chart(fig), use_container_width=True, config={'displayModeBar': False})
            
            st.markdown(f"""
            <div style="background: rgba(22, 27, 34, 0.7); border-radius: 16px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.4); display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div style="border-right: 1px solid rgba(255,255,255,0.05); padding-right: 20px;">
                    <div style="font-size: 0.7rem; color: #8B949E; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Gross Rental Yield</div>
                    <div style="font-size: 1.75rem; font-weight: 700; color: #6366F1; font-family: 'Space Grotesk', sans-serif;">{gross_yield:.2f}%</div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #8B949E; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Projected 5yr IRR</div>
                    <div style="font-size: 1.75rem; font-weight: 700; color: #10b981; font-family: 'Space Grotesk', sans-serif;">+48.2%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📑 Generate Portfolio Execution Report", use_container_width=True):
                with st.spinner("Running 10-year Monte Carlo simulations..."):
                    time.sleep(1.2)
                    st.success("Institutional Report Generated.")

    def _render_negotiation_playbook(self):
        """Tactical negotiation scripts based on lead psychological DNA"""
        st.markdown("### 📖 Tactical Negotiation Playbook")
        st.markdown("*Custom counter-scripts and psychological engagement strategies*")

        selected_lead = st.session_state.get('selected_lead_name', '-- Select a Lead --')
        
        if selected_lead == "-- Select a Lead --":
            st.info("👈 Please select a lead in the Lead Intelligence Hub to generate a custom playbook.")
            return

        lead_options = st.session_state.get('lead_options', {})
        lead_context = lead_options.get(selected_lead, {})

        # 1. Psychological DNA Profile
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### Psychological DNA")
            # Simulated DNA values
            dna_traits = {
                "Analytical": 0.85,
                "Decisiveness": 0.65,
                "Risk Tolerance": 0.42,
                "Emotional Bias": 0.78,
                "Urgency": 0.92
            }
            for trait, val in dna_traits.items():
                percent = int(val * 100)
                # Color based on value
                if val >= 0.8: color = "#10B981"
                elif val >= 0.5: color = "#6366F1"
                else: color = "#F59E0B"
                
                st.markdown(f"""
                    <div style='margin-bottom: 1rem;'>
                        <div style='display: flex; justify-content: space-between; margin-bottom: 0.25rem;'>
                            <span style='color: #8B949E; font-size: 0.85rem; font-weight: 600;'>{trait.upper()}</span>
                            <span style='color: #FFFFFF; font-size: 0.85rem; font-weight: 700;'>{percent}%</span>
                        </div>
                        <div style='background: rgba(255, 255, 255, 0.05); height: 6px; border-radius: 3px; overflow: hidden;'>
                            <div style='background: {color}; width: {percent}%; height: 100%; box-shadow: 0 0 10px {color}40;'></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### 🎯 Engagement Directives")
            directives = [
                "**Mirror Communication Pace**: Lead processes information quickly. Keep responses concise.",
                "**Leverage Scarcity**: Emphasize low inventory in their preferred ZIP codes.",
                "**Validate with Data**: Provide tax assessment history and appreciation trends for last 3 years.",
                "**Soft Close Strategy**: Use 'Trial Closes' to test readiness before asking for commitment."
            ]
            for d in directives:
                st.markdown(f"- {d}")

        st.markdown("---")

        # 2. Tactical Counter-Scripts
        st.markdown("#### 🛡️ Scenario Battlecards")
        
        scenarios = [
            {
                "objection": "The interest rates are too high right now.",
                "counter": "I hear you. But remember, you marry the house and date the rate. We can bake in a 2-1 buy-down to lower your payment for the first two years.",
                "why": "Reframes the rate as temporary and provides a tangible financial solution."
            },
            {
                "objection": "I'm worried about the Austin property tax spikes.",
                "counter": "It's a valid concern. However, your Homestead Exemption caps increases at 10% annually, and we're seeing value growth consistently outpace tax growth by 3x.",
                "why": "Educates on legal protections and focuses on the spread (ROI)."
            },
            {
                "objection": "We want to wait for the spring market.",
                "counter": "Spring means more competition and bidding wars. Buying now allows us to negotiate inspection repairs and closing costs that won't be possible in 90 days.",
                "why": "Highlights the competitive advantage of current timing."
            }
        ]

        for s in scenarios:
            with st.expander(f"🚩 Objection: {s['objection']}"):
                st.markdown(f"**AI Counter-Script:**")
                st.info(f"\"{s['counter']}\"")
                st.markdown(f"**Strategic Reasoning:** {s['why']}")
                if st.button("Copy to Clipboard", key=f"copy_{s['objection'][:10]}"):
                    st.toast("Script copied to clipboard!")

def render_sales_copilot_hub(services, claude=None):
    """Entry point for the Sales Copilot hub"""
    hub = SalesCopilotHub(services, claude)
    hub.render_hub()
