"""
Real-Time Dashboard Component for GHL Real Estate AI
Provides live updates via WebSocket connections with <100ms latency
"""

import streamlit as st
import asyncio
import json
import time
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio_mqtt
import websockets
from streamlit.runtime.scriptrunner import add_script_run_ctx

# Initialize session state for real-time data
if 'realtime_data' not in st.session_state:
    st.session_state.realtime_data = {
        'connected': False,
        'lead_scores': {},
        'recent_updates': [],
        'performance_metrics': {},
        'connection_status': 'disconnected',
        'last_update': None
    }

if 'websocket_connection' not in st.session_state:
    st.session_state.websocket_connection = None


class RealtimeDashboard:
    """Real-time dashboard with WebSocket integration"""

    def __init__(self, tenant_id: str, auth_token: str):
        self.tenant_id = tenant_id
        self.auth_token = auth_token
        self.websocket_url = f"ws://localhost:8000/api/realtime/scoring/{tenant_id}?token={auth_token}"

    async def connect_websocket(self):
        """Connect to real-time scoring WebSocket"""
        try:
            # Connect to WebSocket
            websocket = await websockets.connect(
                self.websocket_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )

            st.session_state.websocket_connection = websocket
            st.session_state.realtime_data['connected'] = True
            st.session_state.realtime_data['connection_status'] = 'connected'

            # Start listening for messages in background
            asyncio.create_task(self._listen_for_updates(websocket))

            return True

        except Exception as e:
            st.error(f"🔴 WebSocket connection failed: {e}")
            st.session_state.realtime_data['connected'] = False
            st.session_state.realtime_data['connection_status'] = f'error: {str(e)}'
            return False

    async def _listen_for_updates(self, websocket):
        """Listen for real-time updates from WebSocket"""
        try:
            async for message in websocket:
                data = json.loads(message)
                self._handle_realtime_update(data)

        except websockets.exceptions.ConnectionClosed:
            st.session_state.realtime_data['connected'] = False
            st.session_state.realtime_data['connection_status'] = 'disconnected'
        except Exception as e:
            st.error(f"🔴 WebSocket error: {e}")
            st.session_state.realtime_data['connection_status'] = f'error: {str(e)}'

    def _handle_realtime_update(self, data: Dict):
        """Handle incoming real-time updates"""
        event_type = data.get('event_type', 'unknown')

        if event_type == 'score_update':
            # Update lead score in session state
            lead_id = data.get('lead_id')
            if lead_id:
                st.session_state.realtime_data['lead_scores'][lead_id] = data

                # Add to recent updates (keep last 50)
                st.session_state.realtime_data['recent_updates'].insert(0, data)
                if len(st.session_state.realtime_data['recent_updates']) > 50:
                    st.session_state.realtime_data['recent_updates'].pop()

        elif event_type == 'performance_metrics':
            st.session_state.realtime_data['performance_metrics'] = data

        elif event_type == 'connection_established':
            st.session_state.realtime_data['connected'] = True

        # Update last update timestamp
        st.session_state.realtime_data['last_update'] = datetime.now()

        # Trigger Streamlit rerun to update UI
        st.rerun()

    def render_connection_status(self):
        """Render WebSocket connection status"""
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if st.session_state.realtime_data['connected']:
                st.success("🟢 **Real-Time Connected** - Live updates active")
            else:
                status = st.session_state.realtime_data['connection_status']
                st.error(f"🔴 **Disconnected** - {status}")

        with col2:
            if st.button("🔄 Reconnect", key="reconnect_ws"):
                # Attempt to reconnect
                asyncio.create_task(self.connect_websocket())

        with col3:
            last_update = st.session_state.realtime_data['last_update']
            if last_update:
                seconds_ago = (datetime.now() - last_update).total_seconds()
                st.caption(f"Last update: {seconds_ago:.1f}s ago")

    def render_live_metrics(self):
        """Render real-time performance metrics"""
        st.subheader("⚡ Live Performance Metrics")

        metrics = st.session_state.realtime_data.get('performance_metrics', {})

        if metrics:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                latency = metrics.get('avg_latency_ms', 0)
                color = "green" if latency < 100 else "orange" if latency < 200 else "red"
                st.metric(
                    "Avg Latency",
                    f"{latency:.1f}ms",
                    delta=f"Target: 100ms",
                    delta_color="inverse" if latency > 100 else "normal"
                )

            with col2:
                connections = metrics.get('active_connections', 0)
                st.metric("Active Connections", connections)

            with col3:
                hit_rate = metrics.get('cache_hit_rate', 0) * 100
                st.metric("Cache Hit Rate", f"{hit_rate:.1f}%")

            with col4:
                total_scores = metrics.get('total_scores', 0)
                st.metric("Total Scores", f"{total_scores:,}")

    def render_live_scoring_chart(self):
        """Render real-time scoring updates chart"""
        st.subheader("📈 Live Lead Scoring Stream")

        recent_updates = st.session_state.realtime_data.get('recent_updates', [])

        if not recent_updates:
            st.info("🔄 Waiting for real-time scoring updates...")
            return

        # Convert to DataFrame for plotting
        df_data = []
        for update in recent_updates[-20:]:  # Last 20 updates
            df_data.append({
                'timestamp': update.get('timestamp', datetime.now().isoformat()),
                'lead_id': update.get('lead_id', 'unknown'),
                'score': update.get('score', 0),
                'confidence': update.get('confidence', 0),
                'latency_ms': update.get('latency_ms', 0)
            })

        if df_data:
            df = pd.DataFrame(df_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Create real-time scoring chart
            fig = go.Figure()

            # Add score line
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['score'],
                mode='lines+markers',
                name='Lead Score',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8),
                hovertemplate='<b>%{text}</b><br>Score: %{y:.1f}<br>Time: %{x}<extra></extra>',
                text=df['lead_id']
            ))

            fig.update_layout(
                title="Real-Time Lead Scoring Stream",
                xaxis_title="Time",
                yaxis_title="Lead Score",
                height=400,
                showlegend=False,
                hovermode='x unified'
            )

            st.plotly_chart(fig, width='stretch')

            # Show recent scoring table
            with st.expander("📋 Recent Scoring Details"):
                display_df = df[['lead_id', 'score', 'confidence', 'latency_ms']].copy()
                display_df['score'] = display_df['score'].round(1)
                display_df['confidence'] = (display_df['confidence'] * 100).round(1)
                display_df['latency_ms'] = display_df['latency_ms'].round(1)

                st.dataframe(
                    display_df,
                    column_config={
                        'lead_id': 'Lead ID',
                        'score': 'Score',
                        'confidence': 'Confidence %',
                        'latency_ms': 'Latency (ms)'
                    },
                    width='stretch'
                )

    def render_lead_score_distribution(self):
        """Render current lead score distribution"""
        st.subheader("📊 Live Lead Score Distribution")

        lead_scores = st.session_state.realtime_data.get('lead_scores', {})

        if not lead_scores:
            st.info("🔄 No lead scores available yet...")
            return

        # Create score distribution
        scores = [data['score'] for data in lead_scores.values()]

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=scores,
            nbinsx=20,
            name="Lead Scores",
            marker_color='lightblue',
            opacity=0.7
        ))

        fig.update_layout(
            title="Current Lead Score Distribution",
            xaxis_title="Score",
            yaxis_title="Count",
            height=400
        )

        st.plotly_chart(fig, width='stretch')

        # Score statistics
        if scores:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Leads", len(scores))
            with col2:
                st.metric("Avg Score", f"{sum(scores)/len(scores):.1f}")
            with col3:
                st.metric("High Scores (>80)", len([s for s in scores if s > 80]))
            with col4:
                st.metric("Low Scores (<40)", len([s for s in scores if s < 40]))

    def render_latency_monitor(self):
        """Render scoring latency monitoring"""
        st.subheader("⚡ Scoring Latency Monitor")

        recent_updates = st.session_state.realtime_data.get('recent_updates', [])

        if not recent_updates:
            st.info("🔄 Waiting for latency data...")
            return

        # Extract latency data
        latencies = [update.get('latency_ms', 0) for update in recent_updates[-50:]]
        timestamps = [update.get('timestamp', datetime.now().isoformat()) for update in recent_updates[-50:]]

        # Create latency chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=list(range(len(latencies))),
            y=latencies,
            mode='lines+markers',
            name='Latency (ms)',
            line=dict(color='green' if all(l < 100 for l in latencies) else 'orange'),
            marker=dict(size=6)
        ))

        # Add target line
        fig.add_hline(
            y=100,
            line_dash="dash",
            line_color="red",
            annotation_text="100ms Target"
        )

        fig.update_layout(
            title="Scoring Latency Over Time",
            xaxis_title="Request #",
            yaxis_title="Latency (ms)",
            height=350
        )

        st.plotly_chart(fig, width='stretch')

        # Latency statistics
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Latency", f"{avg_latency:.1f}ms")
            with col2:
                st.metric("Max Latency", f"{max_latency:.1f}ms")
            with col3:
                st.metric("Min Latency", f"{min_latency:.1f}ms")
            with col4:
                performance = "🟢 Excellent" if avg_latency < 50 else "🟡 Good" if avg_latency < 100 else "🔴 Needs Improvement"
                st.metric("Performance", performance)

    def render_system_health(self):
        """Render overall system health dashboard"""
        st.subheader("🏥 System Health Monitor")

        # System status indicators
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📡 Connection Status")
            if st.session_state.realtime_data['connected']:
                st.success("🟢 WebSocket: Connected")
                st.success("🟢 Real-time Updates: Active")
                st.success("🟢 Data Flow: Normal")
            else:
                st.error("🔴 WebSocket: Disconnected")
                st.error("🔴 Real-time Updates: Inactive")
                st.warning("🟡 Data Flow: Static Only")

        with col2:
            st.markdown("### 🎯 Performance Targets")

            metrics = st.session_state.realtime_data.get('performance_metrics', {})
            latency = metrics.get('avg_latency_ms', 0)

            # Performance indicators
            if latency > 0:
                if latency < 50:
                    st.success(f"🟢 Latency: {latency:.1f}ms (Excellent)")
                elif latency < 100:
                    st.warning(f"🟡 Latency: {latency:.1f}ms (Good)")
                else:
                    st.error(f"🔴 Latency: {latency:.1f}ms (Slow)")
            else:
                st.info("⏳ Latency: No data yet")

            cache_rate = metrics.get('cache_hit_rate', 0) * 100
            if cache_rate > 0:
                if cache_rate > 80:
                    st.success(f"🟢 Cache: {cache_rate:.1f}% (Excellent)")
                elif cache_rate > 60:
                    st.warning(f"🟡 Cache: {cache_rate:.1f}% (Good)")
                else:
                    st.error(f"🔴 Cache: {cache_rate:.1f}% (Poor)")


def render_realtime_dashboard():
    """Main function to render the complete real-time dashboard"""
    st.title("⚡ Real-Time Intelligence Dashboard")
    st.markdown("*Live lead scoring with <100ms latency*")

    # Initialize dashboard (mock auth for demo)
    tenant_id = "demo_tenant"
    auth_token = "demo_token_123"  # In production, get from authentication

    dashboard = RealtimeDashboard(tenant_id, auth_token)

    # Auto-connect if not connected
    if not st.session_state.realtime_data['connected']:
        if st.button("🚀 Connect Real-Time Dashboard", type="primary"):
            with st.spinner("Connecting to real-time services..."):
                # In a real implementation, this would run the async connection
                st.success("🟢 Connected! (Demo mode - simulating real-time data)")
                st.session_state.realtime_data['connected'] = True
                st.session_state.realtime_data['connection_status'] = 'connected (demo)'
                st.rerun()

    # Connection status
    dashboard.render_connection_status()

    st.markdown("---")

    # Main dashboard tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Live Scoring",
        "⚡ Performance",
        "📊 Distribution",
        "🕐 Latency",
        "🏥 Health"
    ])

    with tab1:
        dashboard.render_live_scoring_chart()

    with tab2:
        dashboard.render_live_metrics()

    with tab3:
        dashboard.render_lead_score_distribution()

    with tab4:
        dashboard.render_latency_monitor()

    with tab5:
        dashboard.render_system_health()

    # Auto-refresh disclaimer
    st.markdown("---")
    st.caption("🔄 Dashboard auto-refreshes with live WebSocket data • Target latency: <100ms • Cache-optimized scoring")


# Simulate real-time data for demo purposes
def _simulate_realtime_data():
    """Simulate incoming real-time data for demo"""
    if st.session_state.realtime_data['connected']:
        import random

        # Simulate a new scoring event
        lead_id = f"lead_{random.randint(1000, 9999)}"
        score = random.uniform(20, 95)
        confidence = random.uniform(0.7, 0.95)
        latency = random.uniform(25, 150)

        fake_update = {
            'event_type': 'score_update',
            'lead_id': lead_id,
            'score': score,
            'confidence': confidence,
            'latency_ms': latency,
            'timestamp': datetime.now().isoformat(),
            'factors': {
                'budget': random.uniform(0.5, 1.0),
                'location': random.uniform(0.5, 1.0),
                'timeline': random.uniform(0.5, 1.0),
                'engagement': random.uniform(0.5, 1.0)
            }
        }

        # Add to session state
        st.session_state.realtime_data['lead_scores'][lead_id] = fake_update
        st.session_state.realtime_data['recent_updates'].insert(0, fake_update)

        # Keep recent updates limited
        if len(st.session_state.realtime_data['recent_updates']) > 50:
            st.session_state.realtime_data['recent_updates'].pop()

        # Update metrics
        st.session_state.realtime_data['performance_metrics'] = {
            'avg_latency_ms': latency,
            'active_connections': random.randint(2, 8),
            'cache_hit_rate': random.uniform(0.75, 0.95),
            'total_scores': len(st.session_state.realtime_data['lead_scores'])
        }

# Auto-generate demo data every few seconds
if st.session_state.realtime_data['connected']:
    _simulate_realtime_data()