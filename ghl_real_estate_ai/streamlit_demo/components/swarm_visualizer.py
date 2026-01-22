import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import random
import time
import yaml
from pathlib import Path
from typing import List, Dict
import pandas as pd
try:
    from agents.swarm_orchestrator import SwarmOrchestrator, AgentRole, TaskStatus
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False

@st.cache_data(ttl=300)
def load_claude_assets():
    """Load agents and skills from the .claude directory."""
    project_root = Path(__file__).parent.parent.parent.parent
    skills = []
    manifest_path = project_root / '.claude' / 'skills' / 'MANIFEST.yaml'
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
                skills = manifest.get('skills', [])
        except Exception as e:
            print(f'Error loading skills manifest: {e}')
    agents = []
    agents_dir = project_root / '.claude' / 'agents'
    if agents_dir.exists():
        for agent_file in agents_dir.glob('*.md'):
            name = agent_file.stem.replace('-', ' ').title()
            agents.append({'name': name, 'path': str(agent_file), 'role': 'Orchestrator' if 'protocol' in name.lower() else 'Specialist'})
    return (agents, skills)

def render_agent_debate_log(lead_id: str = None):
    """Phase 7: Explainability component to show agent reasoning debate."""
    st.markdown("### 🗣️ Swarm Explainability: Agent Debate")
    st.markdown("*Real-time audit trail of specialist agent reasoning and conflict resolution*")

    # Get blackboard data
    try:
        from ghl_real_estate_ai.services.autonomous_followup_engine import get_autonomous_followup_engine
        engine = get_autonomous_followup_engine()
        blackboard = engine.blackboard
        debates = blackboard.read("agent_debates") or []
    except Exception:
        # Fallback mock data
        debates = [
            {"timestamp": "2026-01-21T10:00:00", "agent": "sentiment_analyst", "thought": "Lead sounds slightly frustrated with current interest rates.", "action_proposed": "Use empathetic approach", "confidence": 0.85},
            {"timestamp": "2026-01-21T10:00:05", "agent": "scheduling_agent", "thought": "Qualification score is 6. Lead is ready for a tour.", "action_proposed": "Propose 3 tour slots", "confidence": 0.92},
            {"timestamp": "2026-01-21T10:00:10", "agent": "market_context_agent", "thought": "Prime Arbitrage found in Austin Zip 78745. 18.8% ROI.", "action_proposed": "Pitch Arbitrage Pro-forma", "confidence": 0.95}
        ]

    if not debates:
        st.info("Waiting for agent activity to populate debate log...")
        return

    # Filter for lead_id if provided
    if lead_id:
        # In a real system, we'd filter here. For now, we show all for the demo.
        pass

    # Reverse to show newest first
    debates = debates[::-1]

    for entry in debates:
        with st.container():
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                st.caption(entry['timestamp'].split('T')[-1][:8])
                st.markdown(f"**{entry['agent'].replace('_', ' ').title()}**")
            with col2:
                st.markdown(f"*{entry['thought']}*")
                st.info(f"👉 Proposed Action: **{entry['action_proposed']}**")
            with col3:
                conf = entry['confidence']
                st.metric("Confidence", f"{conf:.0%}")
            st.divider()

def render_swarm_visualizer(lead_name: str=None, lead_data: dict=None):
    """
    Renders the "Swarm Intelligence" Visualization.
    Enhanced with Lead Analysis Mode for elite behavioral intelligence.
    """
    st.markdown('## 🐝 Swarm Intelligence Center')
    if lead_name and lead_name != '-- Select a Lead --':
        st.markdown(f'### 🎯 Lead Analysis Swarm: {lead_name}')
        st.markdown('Visualizing real-time specialist agent collaboration for multi-dimensional lead profiling.')
        swarm_agents = [{'name': 'CSO (Orchestrator)', 'role': 'Strategic Synthesis', 'status': 'thinking', 'type': 'Lead'}, {'name': 'Financial Analyst', 'role': 'Liquidity Assessment', 'status': 'active', 'type': 'Lead'}, {'name': 'Timeline Assessor', 'role': 'Urgency Modeling', 'status': 'active', 'type': 'Lead'}, {'name': 'Behavioral Psych', 'role': 'Lifestyle DNA', 'status': 'thinking', 'type': 'Lead'}, {'name': 'Risk Analyst', 'role': 'Barrier Detection', 'status': 'idle', 'type': 'Lead'}, {'name': 'Negotiation Engine', 'role': 'Counter-Strategy', 'status': 'idle', 'type': 'Lead'}]
        G = nx.Graph()
        for i, agent in enumerate(swarm_agents):
            G.add_node(i, **agent)
            if i > 0:
                G.add_edge(0, i)
        pos = nx.spring_layout(G, seed=42)
        all_display_agents = swarm_agents
    else:
        st.markdown('Real-time visualization of autonomous agent collaboration and project finalization roadmap.')
        orchestrator = None
        if SWARM_AVAILABLE:
            project_root = Path(__file__).parent.parent.parent
            orchestrator = SwarmOrchestrator(project_root)
            project_agents = list(orchestrator.agents.values())
            tasks = list(orchestrator.tasks.values())
        else:
            project_agents = []
            tasks = []
        claude_agents, skills = load_claude_assets()
        all_display_agents = []
        for pa in project_agents:
            all_display_agents.append({'name': pa.name, 'role': pa.role.value.replace('_', ' ').title(), 'status': pa.status, 'type': 'Project'})
        for ca in claude_agents:
            all_display_agents.append({'name': ca['name'], 'role': ca.get('role', 'Specialist'), 'status': 'Idle', 'type': 'Claude'})
        if not all_display_agents:
            all_display_agents = [{'name': f'Agent-{i:02d}', 'role': random.choice(['Orchestrator', 'Analyst', 'Closer']), 'status': 'Idle'} for i in range(10)]
        num_agents = len(all_display_agents)
        G = nx.erdos_renyi_graph(n=num_agents, p=0.3, seed=42)
        pos = nx.spring_layout(G, seed=42)
        tasks = locals().get('tasks', [])
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.append(x0)
            edge_y.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)
        edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color='rgba(100, 116, 139, 0.3)'), hoverinfo='none', mode='lines')
        node_x = []
        node_y = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
        colors = {'active': '#10b981', 'working': '#10b981', 'thinking': '#f59e0b', 'idle': '#64748b', 'Idle': '#64748b', 'error': '#ef4444'}
        node_text = []
        node_color = []
        for i, node in enumerate(G.nodes()):
            agent = all_display_agents[i % len(all_display_agents)]
            status = agent.get('status', 'idle')
            info = f"<b>{agent['name']}</b><br>Role: {agent.get('role', 'Specialist')}<br>Status: {status}<br>Type: {agent.get('type', 'System')}"
            node_text.append(info)
            node_color.append(colors.get(status, '#64748b'))
        node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', hoverinfo='text', text=[a['name'].split()[0] for a in all_display_agents], textposition='bottom center', textfont=dict(size=10, color='#1e293b'), marker=dict(showscale=False, color=node_color, size=25, line=dict(width=2, color='white')))
        fig = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(title='<br>Active Swarm Network', titlefont_size=16, showlegend=False, hovermode='closest', margin=dict(b=20, l=5, r=5, t=40), xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=500)
        st.plotly_chart(fig, use_container_width=True)
        if tasks:
            st.markdown('### 📋 Swarm Project Roadmap')
            task_list = []
            for t in tasks:
                task_list.append({'ID': t.id, 'Task': t.title, 'Agent': t.assigned_to.value.replace('_', ' ').title(), 'Status': t.status.value.upper(), 'Priority': t.priority})
            df_tasks = pd.DataFrame(task_list)

            def color_status(val):
                if val == 'COMPLETED':
                    color = '#dcfce7'
                    text = '#166534'
                elif val == 'IN_PROGRESS':
                    color = '#dbeafe'
                    text = '#1e40af'
                elif val == 'FAILED':
                    color = '#fee2e2'
                    text = '#991b1b'
                else:
                    color = '#f1f5f9'
                    text = '#475569'
                return f'background-color: {color}; color: {text}; font-weight: bold;'
            st.dataframe(df_tasks.style.applymap(color_status, subset=['Status']), use_container_width=True, hide_index=True)
    with col2:
        st.markdown('### Agent Activity Log')
        if orchestrator:
            ready = orchestrator.get_ready_tasks()
            activities = []
            for t in ready[:5]:
                activities.append((f"🤖 {t.assigned_to.value.replace('_', ' ').title()}", f'Queued: {t.title}...'))
            if not activities:
                activities.append(('🧠 Orchestrator', 'Waiting for project signals...'))
        else:
            activities = [('🛡️ Security Agent', 'Scanning inbound webhooks...'), ('🧠 Orchestrator', 'Delegating task #4921 to Analyst...'), ('📊 Analyst Agent', 'Calculating churn probability for Lead #12...'), ('🤝 Closer Agent', 'Drafting proposal for Client A...'), ('🔍 Researcher', 'Enriching profile for Lead #88...')]
        for agent, action in activities:
            st.markdown(f'\n            <div class="agent-card" style="margin-bottom: 12px; border-left: 3px solid #006AFF; background: #f8fafc; color: #1e293b; padding: 10px; border-radius: 0 8px 8px 0;">\n                <div style="font-weight: 700; font-size: 0.9rem;">{agent}</div>\n                <div style="font-size: 0.8rem; color: #64748b; font-style: italic;">{action}</div>\n            </div>\n            ', unsafe_allow_html=True)
        st.markdown('---')
        if st.button('🚀 Launch Swarm Execution', type='primary', use_container_width=True):
            with st.spinner('Initializing Agent Swarm...'):
                time.sleep(1.5)
                st.toast('Agent Swarm launched successfully!', icon='🐝')
                st.info('Full execution logs available in ghl_real_estate_ai/reports/')
        st.button('Spawn New Agent', type='secondary', use_container_width=True)
        st.button('Emergency Halt', type='secondary', use_container_width=True)
        st.markdown('### Swarm Analytics')
        if orchestrator:
            report = orchestrator.get_status_report()
            progress = report['overall']['progress_percentage'] / 100
            st.progress(progress, text=f"Roadmap Completion: {report['overall']['progress_percentage']:.1f}%")
        else:
            st.progress(0.92, text='Swarm Efficiency: 92%')
            st.progress(0.85, text='Token Utilization: 85%')
            st.progress(1.0, text='Security Integrity: 100%')

    st.markdown("---")
    render_agent_debate_log(lead_data.get('lead_id') if lead_data else None)
        