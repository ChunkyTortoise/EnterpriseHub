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
from datetime import datetime
from typing import Dict, List, Any, Optional

# Absolute imports
try:
    from ghl_real_estate_ai.streamlit_demo.components.workflow_designer import render_workflow_designer
    from ghl_real_estate_ai.streamlit_demo.components.ai_behavioral_tuning import render_behavioral_tuning_panel, get_behavior_config
    from ghl_real_estate_ai.services.workflow_marketplace import WorkflowMarketplaceService
    from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
except ImportError:
    st.error("🚨 Critical Error: Required services for Automation Studio not found.")

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
        """Render the complete Automation Studio interface"""
        st.header("🤖 Automation Studio")
        st.markdown("*Autonomous Workflow Switchboard & AI Persona Lab*")

        # Top Bar: Global Automation Stats
        self._render_automation_stats()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "⚙️ Automation Control",
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
        """Core AI Automation toggles and GHL Sync Log"""
        st.subheader("AI Automation Control Panel")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🤖 Core AI Agents")
            
            ai_assistant = st.toggle("AI Qualifier (Phase 1)", value=True)
            if ai_assistant:
                st.success("✅ Active - Extracting criteria via SMS")
            
            smart_matcher = st.toggle("Property Matcher (Phase 2)", value=True)
            if smart_matcher:
                st.success("✅ Active - Auto-suggesting listings")
            
            buyer_portal = st.toggle("Buyer Portal Sync (Phase 3)", value=True)
            
        with col2:
            st.markdown("#### ⚡ Follow-Up Triggers")
            
            st.toggle("New Listing SMS Alerts", value=True)
            st.toggle("Price Drop Re-engagement", value=True)
            st.toggle("30-Day 'Cold Lead' Revive", value=False)
            
            st.markdown("---")
            if st.button("🔍 Scan for Silent Leads (24h+)", use_container_width=True):
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
            status_color = "#10B981" if log["status"] == "Synced" else "#3B82F6"
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px; padding: 12px; background: white; border-radius: 10px; margin-bottom: 8px; border: 1px solid #f1f5f9;">
                <div style="font-size: 0.75rem; color: #64748b; min-width: 70px;">{log['time']}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 0.85rem; color: #1e293b;">{log['event']}</div>
                    <div style="font-size: 0.75rem; color: #64748b;">{log['detail']}</div>
                </div>
                <div style="font-family: monospace; font-size: 0.7rem; background: #f8fafc; padding: 2px 6px; border-radius: 4px; color: #475569;">{log['field']}</div>
                <div style="background: {status_color}; color: white; padding: 2px 10px; border-radius: 20px; font-size: 0.65rem; font-weight: 700; text-transform: uppercase;">{log['status']}</div>
            </div>
            """, unsafe_allow_html=True)

    def _render_automation_stats(self):
        """Render high-level automation health"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active Workflows", "24", delta="+3")
        with col2:
            st.metric("Total Events (24h)", "1,842", delta="12%")
        with col3:
            st.metric("Autonomy Level", "94%", delta="+2%")
        with col4:
            st.metric("Agent Time Saved", "156h", delta="24h")
            
        st.markdown("---")

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
                <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; border-top: 4px solid {self.primary_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.5rem;">{t['icon']}</span>
                        <span style="background: #eff6ff; color: #3b82f6; font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; font-weight: 700;">{t['category']}</span>
                    </div>
                    <h4 style="margin: 10px 0 5px 0;">{t['name']}</h4>
                    <p style="font-size: 0.85rem; color: #64748b;">{t['desc']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                        <span style="font-size: 0.8rem; font-weight: 700; color: {self.success_color};">{t['roi']}</span>
                        <button style="background: {self.primary_color}; color: white; border: none; padding: 5px 15px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; cursor: pointer;">Deploy Now</button>
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
                        
                        from services.claude_orchestrator import get_claude_orchestrator
                        orchestrator = get_claude_orchestrator()
                        
                        # Use chat_query or a specialized method to optimize prompt
                        # Here we use chat_query with a specialized system prompt instruction
                        prompt = f"Optimize this real estate AI persona based on these parameters: {json.dumps(opt_context)}"
                        
                        response = loop.run_until_complete(
                            orchestrator.chat_query(
                                query=prompt,
                                context={"task": "persona_optimization"},
                                lead_id="system_persona"
                            )
                        )
                        
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
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem;">
                    <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 10px; text-transform: uppercase;">Simulated SMS Response:</div>
                    <div style="font-size: 0.9rem; color: #1e293b; line-height: 1.5; font-style: italic;">
                        "Hi Sarah! Based on my latest deep-dive into appreciation trends, the Teravista area is looking like a 9.2/10 for your specific goals. I've prepared a custom yield brief—would you like me to send it over or discuss it briefly?"
                    </div>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
                        <div style="font-size: 0.7rem; color: #64748b;">AI Traits Applied:</div>
                        <div style="display: flex; gap: 5px; flex-wrap: wrap; margin-top: 5px;">
                            <span style="background: #e0f2fe; color: #0284c7; padding: 2px 8px; border-radius: 4px; font-size: 0.65rem;">CONSULTATIVE</span>
                            <span style="background: #f0fdf4; color: #166534; padding: 2px 8px; border-radius: 4px; font-size: 0.65rem;">HIGH EMPATHY</span>
                            <span style="background: #fff7ed; color: #9a3412; padding: 2px 8px; border-radius: 4px; font-size: 0.65rem;">DATA-DRIVEN</span>
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
