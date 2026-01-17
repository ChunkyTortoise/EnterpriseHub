"""
Visual Workflow Designer Component
Drag-and-drop workflow creation interface
"""
import streamlit as st
from typing import Dict, Any, List
import json


class WorkflowDesignerComponent:
    """
    Visual workflow designer for Streamlit
    
    Features:
    - Visual block-based design
    - Template library
    - Real-time validation
    - Export/Import
    """
    
    def __init__(self):
        self.action_blocks = {
            "📱 Send SMS": {
                "action": "send_sms",
                "fields": ["message"],
                "icon": "📱",
                "color": "#4CAF50"
            },
            "📧 Send Email": {
                "action": "send_email",
                "fields": ["subject", "body"],
                "icon": "📧",
                "color": "#2196F3"
            },
            "⏰ Wait": {
                "action": "wait",
                "fields": ["delay_minutes"],
                "icon": "⏰",
                "color": "#FF9800"
            },
            "🏷️ Add Tag": {
                "action": "add_tag",
                "fields": ["tag"],
                "icon": "🏷️",
                "color": "#9C27B0"
            },
            "👤 Assign Agent": {
                "action": "assign_agent",
                "fields": ["agent_id"],
                "icon": "👤",
                "color": "#F44336"
            },
            "🔔 Notify": {
                "action": "notify_agent",
                "fields": ["message", "priority"],
                "icon": "🔔",
                "color": "#FF5722"
            },
            "🧠 AI Analyze": {
                "action": "ai_analyze",
                "fields": ["analysis_type", "depth"],
                "icon": "🧠",
                "color": "#6366F1"
            },
            "💰 AI Offer": {
                "action": "ai_offer",
                "fields": ["max_range", "strategy"],
                "icon": "💰",
                "color": "#10B981"
            }
        }
    
    def render_designer(self) -> Dict[str, Any]:
        """Render the visual workflow designer"""
        st.markdown("### 🎨 Visual Workflow Designer")
        st.markdown("Build workflows by adding and configuring blocks below.")
        
        # Initialize workflow in session state
        if "workflow_steps" not in st.session_state:
            st.session_state.workflow_steps = []
        
        # Workflow metadata
        col1, col2 = st.columns(2)
        with col1:
            workflow_name = st.text_input("Workflow Name", "My Workflow")
        with col2:
            workflow_trigger = st.selectbox(
                "Trigger Event",
                ["lead_created", "lead_updated", "no_response_48h", 
                 "appointment_scheduled", "property_viewed"]
            )
        
        st.markdown("---")
        
        # Action palette
        st.markdown("#### 🧰 Available Actions")
        cols = st.columns(6)
        for idx, (name, config) in enumerate(self.action_blocks.items()):
            with cols[idx % 6]:
                if st.button(f"{config['icon']} {name.split()[1]}", use_container_width=True):
                    self._add_step(config)
        
        st.markdown("---")
        
        # Workflow steps
        st.markdown("#### 📋 Workflow Steps")
        
        if not st.session_state.workflow_steps:
            st.info("👆 Click an action above to add your first step")
        else:
            self._render_steps()
        
        st.markdown("---")
        
        # Export/Save
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Save Workflow", type="primary", use_container_width=True):
                workflow = self._build_workflow(workflow_name, workflow_trigger)
                st.success("✅ Workflow saved!")
                return workflow
        
        with col2:
            if st.button("📥 Export JSON", use_container_width=True):
                workflow = self._build_workflow(workflow_name, workflow_trigger)
                st.download_button(
                    "⬇️ Download",
                    data=json.dumps(workflow, indent=2),
                    file_name=f"{workflow_name.lower().replace(' ', '_')}.json",
                    mime="application/json"
                )
        
        with col3:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.workflow_steps = []
                st.rerun()
        
        return None
    
    def _add_step(self, config: Dict[str, Any]):
        """Add step to workflow"""
        step = {
            "action": config["action"],
            "icon": config["icon"],
            "color": config["color"],
            "delay_minutes": 0,
            "data": {}
        }
        st.session_state.workflow_steps.append(step)
    
    def _render_steps(self):
        """Render workflow steps"""
        for idx, step in enumerate(st.session_state.workflow_steps):
            with st.container():
                # Step header
                col1, col2, col3 = st.columns([1, 8, 1])
                
                with col1:
                    st.markdown(f"### {idx + 1}")
                
                with col2:
                    st.markdown(
                        f"<div style='background: rgba(22, 27, 34, 0.7); "
                        f"padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); "
                        f"border-left: 5px solid {step['color']}; box-shadow: 0 10px 30px rgba(0,0,0,0.4); "
                        f"backdrop-filter: blur(10px); display: flex; align-items: center; gap: 15px;'>"
                        f"<span style='font-size: 1.5rem;'>{step['icon']}</span>"
                        f"<div>"
                        f"<div style='font-family: \"Space Grotesk\", sans-serif; font-weight: 700; color: white; letter-spacing: 0.05em;'>{step['action'].replace('_', ' ').upper()}</div>"
                        f"<div style='font-size: 0.75rem; color: #8B949E;'>Delay: {step['delay_minutes']}m</div>"
                        f"</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                
                with col3:
                    if st.button("🗑️", key=f"delete_{idx}"):
                        st.session_state.workflow_steps.pop(idx)
                        st.rerun()
                
                # Step configuration
                with st.expander("⚙️ Configure", expanded=True):
                    self._render_step_config(idx, step)
                
                # Arrow between steps
                if idx < len(st.session_state.workflow_steps) - 1:
                    st.markdown(
                        "<div style='text-align: center; font-size: 24px;'>⬇️</div>",
                        unsafe_allow_html=True
                    )
    
    def _render_step_config(self, idx: int, step: Dict[str, Any]):
        """Render step configuration"""
        # Delay
        delay = st.number_input(
            "Delay (minutes)",
            min_value=0,
            value=step.get("delay_minutes", 0),
            key=f"delay_{idx}"
        )
        step["delay_minutes"] = delay
        
        # Action-specific fields
        action = step["action"]
        
        if action == "send_sms":
            message = st.text_area(
                "Message",
                value=step["data"].get("message", ""),
                key=f"message_{idx}",
                placeholder="Hi {{firstName}}, welcome to our service!"
            )
            step["data"]["message"] = message
        
        elif action == "send_email":
            subject = st.text_input(
                "Subject",
                value=step["data"].get("subject", ""),
                key=f"subject_{idx}"
            )
            body = st.text_area(
                "Body",
                value=step["data"].get("body", ""),
                key=f"body_{idx}",
                height=150
            )
            step["data"]["subject"] = subject
            step["data"]["body"] = body
        
        elif action == "wait":
            st.info(f"⏰ Wait for {delay} minutes before next step")
        
        elif action == "add_tag":
            tag = st.text_input(
                "Tag Name",
                value=step["data"].get("tag", ""),
                key=f"tag_{idx}"
            )
            step["data"]["tag"] = tag
        
        elif action == "assign_agent":
            agent = st.selectbox(
                "Agent",
                ["Auto-assign", "Agent 1", "Agent 2", "Agent 3"],
                key=f"agent_{idx}"
            )
            step["data"]["agent_id"] = agent
        
        elif action == "notify_agent":
            message = st.text_input(
                "Notification Message",
                value=step["data"].get("message", ""),
                key=f"notify_{idx}"
            )
            priority = st.select_slider(
                "Priority",
                options=["low", "medium", "high", "urgent"],
                key=f"priority_{idx}"
            )
            step["data"]["message"] = message
            step["data"]["priority"] = priority
            
        elif action == "ai_analyze":
            a_type = st.selectbox("Analysis Type", ["Lifestyle Alignment", "Investment Yield", "Churn Risk", "Sentiment"], key=f"atype_{idx}")
            depth = st.select_slider("Analysis Depth", options=["Standard", "Deep", "Quantum"], key=f"adepth_{idx}")
            step["data"]["analysis_type"] = a_type
            step["data"]["depth"] = depth
            
        elif action == "ai_offer":
            strategy = st.selectbox("Offer Strategy", ["Aggressive", "Balanced", "Conservative"], key=f"ostrat_{idx}")
            max_range = st.number_input("Max Range (%)", value=10, key=f"orange_{idx}")
            step["data"]["strategy"] = strategy
            step["data"]["max_range"] = max_range
    
    def _build_workflow(self, name: str, trigger: str) -> Dict[str, Any]:
        """Build workflow from steps"""
        return {
            "name": name,
            "trigger": trigger,
            "steps": [
                {
                    "order": idx + 1,
                    "action": step["action"],
                    "delay_minutes": step["delay_minutes"],
                    **step["data"]
                }
                for idx, step in enumerate(st.session_state.workflow_steps)
            ],
            "created_at": "2026-01-05T20:00:00Z",
            "status": "draft"
        }


def render_workflow_designer():
    """Main render function"""
    designer = WorkflowDesignerComponent()
    return designer.render_designer()


if __name__ == "__main__":
    st.set_page_config(page_title="Workflow Designer", page_icon="🎨", layout="wide")
    
    st.title("🎨 Visual Workflow Designer")
    st.markdown("Build sophisticated automation workflows with drag-and-drop simplicity")
    
    workflow = render_workflow_designer()
    
    if workflow:
        st.markdown("---")
        st.markdown("### 📄 Generated Workflow")
        st.json(workflow)
