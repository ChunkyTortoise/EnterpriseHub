
import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import random
import time
from typing import List, Dict

def render_swarm_visualizer():
    """
    Renders the "Swarm Intelligence" Visualization.
    Shows agents as nodes in a network, pulsing when active.
    """
    st.markdown("## 🐝 Swarm Intelligence Center")
    st.markdown("Real-time visualization of autonomous agent collaboration.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Create a random graph to simulate agent network
        num_agents = 15
        G = nx.erdos_renyi_graph(n=num_agents, p=0.3, seed=42)
        
        # Spring layout
        pos = nx.spring_layout(G, seed=42)
        
        # Edge trace
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.append(x0)
            edge_x.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        # Node trace
        node_x = []
        node_y = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

        # Assign random roles and statuses
        roles = ['Orchestrator', 'Security', 'Analyst', 'Closer', 'Researcher']
        statuses = ['Active', 'Thinking', 'Idle']
        colors = {'Active': '#10b981', 'Thinking': '#f59e0b', 'Idle': '#64748b'}
        
        node_adjacencies = []
        node_text = []
        node_color = []
        
        for node, adjacencies in enumerate(G.adjacency()):
            node_adjacencies.append(len(adjacencies[1]))
            role = random.choice(roles)
            status = random.choice(statuses)
            info = f"Agent-{node:02d}<br>Role: {role}<br>Status: {status}"
            node_text.append(info)
            node_color.append(colors[status])

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                showscale=False,
                colorscale='YlGnBu',
                reversescale=True,
                color=node_color,
                size=20,
                line_width=2))

        fig = go.Figure(data=[edge_trace, node_trace],
                     layout=go.Layout(
                        title='<br>Active Agent Network',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[ dict(
                            text="Live Swarm Topology",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002 ) ],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Agent Activity Log")
        
        activities = [
            ("🛡️ Security Agent", "Scanning inbound webhooks..."),
            ("🧠 Orchestrator", "Delegating task #4921 to Analyst..."),
            ("📊 Analyst Agent", "Calculating churn probability for Lead #12..."),
            ("🤝 Closer Agent", "Drafting proposal for Client A..."),
            ("🔍 Researcher", "Enriching profile for Lead #88...")
        ]
        
        for agent, action in activities:
             st.markdown(f"""
            <div class="agent-card" style="margin-bottom: 10px; border-left: 3px solid #006AFF; background: #f8fafc; color: #1e293b;">
                <div style="font-weight: 700; font-size: 0.9rem;">{agent}</div>
                <div style="font-size: 0.8rem; color: #64748b;">{action}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.button("Spawn New Agent", type="secondary")
        st.button("Emergency Halt", type="primary")

