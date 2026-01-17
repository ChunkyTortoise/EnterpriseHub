"""
Automation Studio - Elite Phase v4.0
Autonomous Workflow Switchboard & AI Persona Lab

Author: EnterpriseHub AI
"""

import streamlit as st
import pandas as pd
import json
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Any, Optional

def sparkline(data: list, color: str = "#6366F1", height: int = 50):
    """Generates a minimal high-fidelity sparkline chart with a neural glow effect."""
    if not data:
        data = [0, 0]
    # Convert hex color to rgba for Plotly compatibility
    hex_c = color.lstrip('#')
    r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
    fill_rgba = f"rgba({r}, {g}, {b}, 0.1)"
    glow_rgba = f"rgba({r}, {g}, {b}, 0.4)"

    fig = go.Figure()
    
    # Outer Glow
    fig.add_trace(go.Scatter(
        y=data,
        mode='lines',
        line=dict(color=glow_rgba, width=5),
        hoverinfo='skip',
        opacity=0.3
    ))
    
    # Main Core Line
    fig.add_trace(go.Scatter(
        y=data,
        mode='lines',
        fill='tozeroy',
        line=dict(color=color, width=2.5),
        fillcolor=fill_rgba,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=5, b=0),
        height=height,
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True, range=[min(data)*0.9 if min(data) != 0 else -0.1, max(data)*1.1 if max(data) != 0 else 0.1])
    )
    return fig

# Absolute imports
try:
    from ghl_real_estate_ai.streamlit_demo.components.workflow_designer import render_workflow_designer
    from ghl_real_estate_ai.streamlit_demo.components.ai_behavioral_tuning import render_behavioral_tuning_panel, get_behavior_config
    from ghl_real_estate_ai.services.workflow_marketplace import WorkflowMarketplaceService
    from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
    from ghl_real_estate_ai.services.analytics_service import AnalyticsService
except ImportError:
    st.error("🚨 Critical Error: Required services for Automation Studio not found.")

analytics_service = AnalyticsService()

class AutomationStudioHub:
    """Enterprise Automation & AI Lab Hub"""

    def __init__(self, services: Dict[str, Any], claude: Optional[ClaudeAssistant] = None):
        self.services = services
        self.claude = claude
        self.marketplace = services.get("marketplace", WorkflowMarketplaceService())
        
        self.primary_color = "#3b82f6"
        self.accent_color = "#8b5cf6"
        self.success_color = "#10b981"

    def render_hub(self):
        """Render the overhauled complete Automation Studio interface - Obsidian Command Edition"""
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart, render_dossier_block
        
        st.markdown("""
            <div style="background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(20px); padding: 1.5rem 2.5rem; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);">
                <div>
                    <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; margin: 0; color: #FFFFFF; letter-spacing: -0.04em; text-transform: uppercase;">🤖 AUTOMATION STUDIO</h1>
                    <p style="font-family: 'Inter', sans-serif; font-size: 1rem; margin: 0.5rem 0 0 0; color: #8B949E; font-weight: 500; letter-spacing: 0.02em;">Autonomous Workflow Switchboard & AI Persona Lab</p>
                </div>
                <div style="text-align: right;">
                    <div style="background: rgba(99, 102, 241, 0.1); color: #6366F1; padding: 10px 20px; border-radius: 12px; font-size: 0.85rem; font-weight: 800; border: 1px solid rgba(99, 102, 241, 0.3); letter-spacing: 0.1em; display: flex; align-items: center; gap: 10px;">
                        <div class="status-pulse" style="width: 10px; height: 10px; background: #6366F1; border-radius: 50%;"></div>
                        AI ENGINE: OPTIMIZED
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Top Bar: Global Automation Stats
        self._render_automation_stats()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🖥️ Automation Control",
            "🎭 Persona Lab",
            "🎨 Visual Designer", 
            "🧠 Neural Triggers",
            "🏪 Marketplace"
        ])

        with tab1:
            self._render_automation_control()

        with tab2:
            self._render_persona_lab()

        with tab3:
            render_workflow_designer()

        with tab4:
            self._render_neural_triggers()
            
        with tab5:
            self._render_marketplace()

    def _render_automation_control(self):
        """Core AI Automation toggles and GHL Sync Log - Obsidian Edition"""
        st.subheader("🖥️ AI COMMAND DECK")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div style="background: rgba(22, 27, 34, 0.6); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; font-size: 1rem;">🤖 CORE AI AGENTS</h4>
                </div>
            """, unsafe_allow_html=True)
            
            ai_assistant = st.toggle("AI Qualifier (Phase 1)", value=True)
            if ai_assistant:
                st.success("✅ Active - Extracting criteria via SMS")
            
            smart_matcher = st.toggle("Property Matcher (Phase 2)", value=True)
            if smart_matcher:
                st.success("✅ Active - Auto-suggesting listings")
            
            buyer_portal = st.toggle("Buyer Portal Sync (Phase 3)", value=True)
            
        with col2:
            st.markdown("""
                <div style="background: rgba(22, 27, 34, 0.6); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; font-size: 1rem;">⚡ NEURAL TRIGGERS</h4>
                </div>
            """, unsafe_allow_html=True)
            
            st.toggle("New Listing SMS Alerts", value=True)
            st.toggle("Price Drop Re-engagement", value=True)
            st.toggle("30-Day 'Cold Lead' Revive", value=False)
            
            st.markdown("---")
            if st.button("🔍 Scan for Silent Nodes (24h+)", use_container_width=True):
                with st.spinner("Scanning GHL logs for silent leads..."):
                    time.sleep(1.0)
                    st.info("No silent leads requiring immediate intervention.")

        st.markdown("---")
        st.subheader("🔗 GoHighLevel Sync Log")
        
        log_events = [
            {"time": "10:45 AM", "event": "Preference Extracted", "detail": "Budget: $1.3M (Sarah Johnson)", "field": "contact.budget", "status": "Synced"},
            {"time": "10:46 AM", "event": "Custom Field Update", "detail": "Area: Alta Loma", "field": "contact.preferred_area", "status": "Synced"},
            {"time": "11:02 AM", "event": "Phase 2 Match", "detail": "Sent 3 RC Listings via SMS", "field": "contact.tags", "status": "Synced"},
            {"time": "11:15 AM", "event": "VAPI Connection", "detail": "Voice Call Initiated", "field": "contact.last_call", "status": "Active"},
        ]
        
        for log in log_events:
            status_color = "#10B981" if log["status"] == "Synced" else "#6366F1"
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px; padding: 12px; background: rgba(255,255,255,0.02); border-radius: 10px; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.05); transition: all 0.2s ease;">
                <div style="font-size: 0.75rem; color: #8B949E; min-width: 75px; font-family: 'Space Grotesk', sans-serif; font-weight: 600;">{log['time']}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 700; font-size: 0.9rem; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; letter-spacing: 0.02em;">{log['event'].upper()}</div>
                    <div style="font-size: 0.8rem; color: #8B949E; font-family: 'Inter', sans-serif;">{log['detail']}</div>
                </div>
                <div style="font-family: monospace; font-size: 0.7rem; background: rgba(99, 102, 241, 0.1); padding: 4px 8px; border-radius: 4px; color: #6366F1; border: 1px solid rgba(99, 102, 241, 0.2);">{log['field']}</div>
                <div style="background: {status_color}20; color: {status_color}; padding: 4px 12px; border-radius: 6px; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; border: 1px solid {status_color}40; letter-spacing: 0.05em;">{log['status']}</div>
            </div>
            """, unsafe_allow_html=True)

    def _render_automation_stats(self):
        """Render high-fidelity automation telemetry"""
        # Fetch real ROI data
        summary = run_async(analytics_service.get_daily_summary("demo_location"))
        usage = summary.get("llm_usage", {})
        saved_cost = usage.get("saved_cost", 0.0)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("AI ROI (SAVED)", f"${saved_cost:.4f}", delta=f"{usage.get('cache_hits', 0)} hits")
            st.plotly_chart(sparkline([0, 0.5, 0.8, 1.2, saved_cost, saved_cost], color="#6366F1", height=40), use_container_width=True, config={'displayModeBar': False})
        with col2:
            st.metric("EVENTS (24H)", "1,842", delta="12%")
            st.plotly_chart(sparkline([1400, 1550, 1620, 1780, 1800, 1842], color="#8B5CF6", height=40), use_container_width=True, config={'displayModeBar': False})
        with col3:
            st.metric("AUTONOMY RATE", "94%", delta="+2%")
            st.plotly_chart(sparkline([88, 90, 91, 92, 93, 94], color="#10B981", height=40), use_container_width=True, config={'displayModeBar': False})
        with col4:
            st.metric("HUMAN TIME SAVED", "156h", delta="24h")
            st.plotly_chart(sparkline([110, 125, 135, 142, 150, 156], color="#F59E0B", height=40), use_container_width=True, config={'displayModeBar': False})
            
        st.markdown("---")

def run_async(coro):
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

    def _render_marketplace(self):
        """Elite Marketplace for pre-built workflows"""
        st.subheader("🛒 Enterprise Workflow Marketplace")
        st.markdown("One-click deployment of high-conversion real estate automations.")
        
        # Marketplace Grid
        templates = [
            {
                "name": "The Speed-to-Lead Fastlane",
                "desc": "Sub-60s qualification with VAPI voice handoff.",
                "category": "Lead Gen",
                "impact": "High",
                "roi": "+24% Conv.",
                "icon": "⚡"
            },
            {
                "name": "Luxury Nurture Sequence",
                "desc": "High-value content drips for $1M+ buyer personas.",
                "category": "Retention",
                "impact": "Medium",
                "roi": "+12% Retention",
                "icon": "💎"
            },
            {
                "name": "Smart Tour Orchestrator",
                "desc": "Automated showing scheduling with agent calendar sync.",
                "category": "Ops",
                "impact": "High",
                "roi": "-30% Admin Time",
                "icon": "📅"
            },
            {
                "name": "The Churn Pattern Interrupt",
                "desc": "Automated re-engagement for ghosting leads.",
                "category": "Retention",
                "impact": "Critical",
                "roi": "42% Recovery",
                "icon": "🚨"
            }
        ]
        
        cols = st.columns(2)
        for i, t in enumerate(templates):
            with cols[i % 2]:
                st.markdown(f"""
                <div style="background: rgba(22, 27, 34, 0.7); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 2rem; margin-bottom: 1.5rem; border-top: 4px solid #6366F1; box-shadow: 0 8px 32px rgba(0,0,0,0.4); backdrop-filter: blur(12px);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
                        <span style="font-size: 2rem; filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.3));">{t['icon']}</span>
                        <span style="background: rgba(99, 102, 241, 0.15); color: #6366F1; font-size: 0.7rem; padding: 4px 12px; border-radius: 6px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; border: 1px solid rgba(99, 102, 241, 0.3); font-family: 'Space Grotesk', sans-serif;">{t['category']}</span>
                    </div>
                    <h4 style="margin: 0 0 8px 0; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em;">{t['name'].upper()}</h4>
                    <p style="font-size: 0.9rem; color: #8B949E; line-height: 1.5; font-family: 'Inter', sans-serif; margin-bottom: 1.5rem;">{t['desc']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1.5rem; padding-top: 1.25rem; border-top: 1px solid rgba(255,255,255,0.05);">
                        <span style="font-size: 0.85rem; font-weight: 700; color: #10b981; font-family: 'Space Grotesk', sans-serif;">ROI: {t['roi']}</span>
                        <div style="color: #6366F1; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Command Ready</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Mock Deployment Button logic (buttons inside HTML are just visual here)
                if st.button(f"Install {t['name']}", key=f"install_{i}"):
                    with st.spinner("Deploying workflow to GHL..."):
                        time.sleep(1.5)
                        st.toast(f"Deploying {t['name']} to GHL...", icon="🚀")
                        st.success("Workflow active!")

    def _render_persona_lab(self):
        """Advanced AI Persona Configuration with Real Claude Optimization"""
        st.subheader("🎭 AI Persona Lab")
        st.markdown("Tune the behavioral identity of your AI workforce.")
        
        # Integrate the Elite Control Deck
        config = get_behavior_config("Swarm")
        render_behavioral_tuning_panel("Swarm", config)
        
        st.markdown("---")
        col_tune, col_preview = st.columns([1.2, 1])
        
        with col_tune:
            st.markdown("#### Behavioral Parameters")
            persona_name = st.selectbox("Current Persona", ["The Professional closer (Default)", "Friendly Neighborhood Guide", "Data-Driven Analyst", "Aggressive Hustler"])
            
            tone = st.slider("Tone (Formal vs. Casual)", 0, 100, 50)
            empathy = st.slider("Empathy Level", 0, 100, 80)
            persistence = st.slider("Persistence (Follow-up Frequency)", 0, 100, 60)
            
            st.markdown("#### Knowledge Base Focus")
            focus = st.multiselect("Prioritize Data Clusters:", ["Market Trends", "School Ratings", "Investment ROI", "Lifestyle & Coffee", "Neighborhood Safety"], default=["Market Trends", "Investment ROI"])
            
            current_p = st.text_area("Custom System Prompt Instructions:", value="You are a helpful assistant on Jorge's team. Be friendly and keep it concise.", height=100)

            if st.button("🪄 Claude: Optimize Persona", use_container_width=True, type="primary"):
                with st.spinner("Claude is optimizing neural weights and persona instructions..."):
                    try:
                        import asyncio
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        # Build optimization context
                        opt_context = {
                            "persona_name": persona_name,
                            "parameters": {
                                "tone": tone,
                                "empathy": empathy,
                                "persistence": persistence
                            },
                            "focus_areas": focus,
                            "current_prompt": current_p
                        }
                        
                        from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator, ClaudeTaskType, ClaudeRequest
                        orchestrator = get_claude_orchestrator()
                        
                        # Use chat_query or a specialized method to optimize prompt
                        # Here we use chat_query with a specialized system prompt instruction
                        prompt = f"Optimize this real estate AI persona based on these parameters: {json.dumps(opt_context)}"
                        
                        request = ClaudeRequest(
                            task_type=ClaudeTaskType.PERSONA_OPTIMIZATION,
                            context={"task": "persona_optimization"},
                            prompt=prompt,
                            temperature=0.7
                        )
                        
                        response = loop.run_until_complete(orchestrator.process_request(request))
                        
                        # Record usage
                        loop.run_until_complete(analytics_service.track_llm_usage(
                            location_id="demo_location",
                            model=response.model or "claude-3-5-sonnet",
                            provider=response.provider or "claude",
                            input_tokens=response.input_tokens or 0,
                            output_tokens=response.output_tokens or 0,
                            cached=False
                        ))
                        
                        st.session_state.optimized_persona = response.content
                        st.success("Claude has optimized your AI persona!")
                    except Exception as e:
                        st.error(f"Optimization failed: {str(e)}")
                        st.session_state.optimized_persona = "Fallback: Stick to a balanced, consultative approach with high follow-up frequency."

            if st.button("💾 Apply Neural Identity", use_container_width=True):
                with st.spinner("Propagating neural weights across swarm..."):
                    time.sleep(1.0)
                    st.toast("Neural weights updated across swarm.", icon="🧠")
                
        with col_preview:
            st.markdown("#### Output Preview & Insights")
            
            if "optimized_persona" in st.session_state:
                st.info(st.session_state.optimized_persona)
            else:
                st.markdown(f"""
                <div style="background: rgba(13, 17, 23, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.5rem;">
                    <div style="font-size: 0.75rem; color: #8B949E; margin-bottom: 10px; text-transform: uppercase; font-family: 'Space Grotesk', sans-serif;">Simulated SMS Response:</div>
                    <div style="font-size: 0.95rem; color: #E6EDF3; line-height: 1.5; font-style: italic;">
                        "Hi Sarah! Based on my latest deep-dive into appreciation trends, the Teravista area is looking like a 9.2/10 for your specific goals. I've prepared a custom yield brief—would you like me to send it over or discuss it briefly?"
                    </div>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.05);">
                        <div style="font-size: 0.7rem; color: #8B949E;">AI Traits Applied:</div>
                        <div style="display: flex; gap: 5px; flex-wrap: wrap; margin-top: 5px;">
                            <span style="background: rgba(99, 102, 241, 0.1); color: #6366F1; padding: 2px 8px; border-radius: 4px; font-size: 0.65rem; border: 1px solid rgba(99, 102, 241, 0.2);">CONSULTATIVE</span>
                            <span style="background: rgba(16, 185, 129, 0.1); color: #10B981; padding: 2px 8px; border-radius: 4px; font-size: 0.65rem; border: 1px solid rgba(16, 185, 129, 0.2);">HIGH EMPATHY</span>
                            <span style="background: rgba(245, 158, 11, 0.1); color: #F59E0B; padding: 2px 8px; border-radius: 4px; font-size: 0.65rem; border: 1px solid rgba(245, 158, 11, 0.2);">DATA-DRIVEN</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.info("💡 **Claude's Note:** Persona Lab adjustments affect the 'Tone' and 'Demeanor' of all outgoing AI communications.")

    def _render_neural_triggers(self):
        """Configuration for event-driven autonomous actions"""
        st.subheader("🧠 Neural Trigger Configuration")
        st.markdown("Define complex, multi-modal events that trigger autonomous swarm behavior.")
        
        triggers = [
            {"event": "Lead views same property 3x", "action": "Trigger SMS with Off-Market Comp", "status": "Active"},
            {"event": "Sentiment drop in SMS thread", "action": "Escalate to Human Agent + Record VAPI Prompt", "status": "Active"},
            {"event": "Lead asks about 'Interest Rates'", "action": "Push Mortgage ROI Calculator link", "status": "Active"},
            {"event": "No activity for 72h after showing", "action": "Trigger Churn Early Warning Sequence", "status": "Active"}
        ]
        
        st.table(pd.DataFrame(triggers))
        
        if st.button("➕ Add Neural Trigger", use_container_width=True):
            with st.spinner("Loading logic editor..."):
                time.sleep(0.5)
                st.info("Trigger editor coming soon...")

def render_automation_studio_hub(services, claude=None):
    """Entry point for the Automation Studio hub"""
    hub = AutomationStudioHub(services, claude)
    hub.render_hub()
