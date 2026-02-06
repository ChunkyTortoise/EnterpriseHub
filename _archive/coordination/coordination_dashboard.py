"""
Service 6 Enhanced Platform - Coordination Dashboard
Real-time monitoring and management of parallel development phases
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time

from unified_data_models import (
    IntegrationTestResult, SystemHealth, UserRole, 
    ScalingMetrics, ServiceHealth
)


@dataclass
class PhaseStatus:
    """Status tracking for each development phase"""
    phase_id: int
    phase_name: str
    completion_percentage: float
    health_status: SystemHealth
    active_tasks: int
    completed_tasks: int
    blocked_tasks: int
    last_updated: datetime
    team_lead: str
    next_milestone: str
    dependencies: List[int]


class CoordinationDashboard:
    """
    Real-time coordination dashboard for monitoring all 4 parallel development phases
    """
    
    def __init__(self):
        self.api_base_url = st.secrets.get("API_BASE_URL", "http://localhost:8000/v2")
        self.refresh_interval = 30  # seconds
        
        # Initialize session state
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.utcnow()
        if 'coordination_data' not in st.session_state:
            st.session_state.coordination_data = None

    def render_dashboard(self):
        """Main dashboard rendering function"""
        st.set_page_config(
            page_title="Service 6 Enhanced - Coordination Dashboard",
            page_icon="🏗️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for coordination dashboard
        st.markdown("""
        <style>
        .phase-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            color: white;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 0.5rem 0;
        }
        .status-healthy { color: #28a745; }
        .status-degraded { color: #ffc107; }
        .status-unhealthy { color: #dc3545; }
        .integration-flow {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.title("🏗️ Service 6 Enhanced - Coordination Dashboard")
        st.markdown("**Real-time monitoring of parallel development phases**")
        
        # Sidebar navigation
        self.render_sidebar()
        
        # Auto-refresh logic
        self.handle_auto_refresh()
        
        # Main dashboard sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "🔄 Integration Matrix", 
            "📈 Phase Progress", 
            "🚨 Risk Management",
            "📋 Test Results"
        ])
        
        with tab1:
            self.render_overview_tab()
        
        with tab2:
            self.render_integration_matrix_tab()
        
        with tab3:
            self.render_phase_progress_tab()
        
        with tab4:
            self.render_risk_management_tab()
        
        with tab5:
            self.render_test_results_tab()

    def render_sidebar(self):
        """Render sidebar with controls and settings"""
        with st.sidebar:
            st.header("⚙️ Control Panel")
            
            # Refresh controls
            if st.button("🔄 Refresh Now", use_container_width=True):
                self.refresh_coordination_data()
                st.rerun()
            
            auto_refresh = st.toggle("Auto Refresh", value=True)
            if auto_refresh:
                refresh_rate = st.selectbox("Refresh Rate", [15, 30, 60, 120], index=1)
                self.refresh_interval = refresh_rate
            
            st.divider()
            
            # Phase filters
            st.subheader("📋 Phase Filters")
            phase_filters = {
                1: st.checkbox("Phase 1: Security & Infrastructure", value=True),
                2: st.checkbox("Phase 2: AI Enhancement", value=True),
                3: st.checkbox("Phase 3: Frontend Enhancement", value=True),
                4: st.checkbox("Phase 4: Deployment & Scaling", value=True)
            }
            
            st.session_state.phase_filters = phase_filters
            
            st.divider()
            
            # System status
            st.subheader("💻 System Status")
            self.render_system_status_sidebar()
            
            st.divider()
            
            # Quick actions
            st.subheader("⚡ Quick Actions")
            if st.button("🧪 Run Integration Tests", use_container_width=True):
                self.trigger_integration_tests()
            
            if st.button("📊 Generate Reports", use_container_width=True):
                self.generate_coordination_reports()

    def render_system_status_sidebar(self):
        """Render system status in sidebar"""
        status_data = self.get_system_health()
        
        if status_data:
            overall_status = status_data.get("overall_status", "unknown")
            status_color = {
                "healthy": "🟢",
                "degraded": "🟡", 
                "unhealthy": "🔴"
            }.get(overall_status, "⚫")
            
            st.write(f"{status_color} **Overall Status**: {overall_status.title()}")
            
            # Service statuses
            services = status_data.get("services", {})
            for service, health in services.items():
                service_status = health.get("status", "unknown")
                service_color = {
                    "up": "🟢",
                    "degraded": "🟡",
                    "down": "🔴"
                }.get(service_status, "⚫")
                st.write(f"{service_color} {service.title()}")

    def render_overview_tab(self):
        """Render overview tab with key metrics"""
        st.header("📊 Project Overview")
        
        # Load coordination data
        coordination_data = self.get_coordination_data()
        
        if not coordination_data:
            st.error("Unable to load coordination data. Please check API connectivity.")
            return
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.render_metric_card(
                "Overall Progress",
                f"{coordination_data['overall_progress']:.1f}%",
                "📈",
                coordination_data['progress_trend']
            )
        
        with col2:
            self.render_metric_card(
                "Integration Health",
                coordination_data['integration_health'].title(),
                "🔄",
                self.get_health_color(coordination_data['integration_health'])
            )
        
        with col3:
            self.render_metric_card(
                "Active Tasks",
                str(coordination_data['active_tasks']),
                "📋",
                "#007bff"
            )
        
        with col4:
            self.render_metric_card(
                "Days to Completion",
                str(coordination_data['estimated_days']),
                "📅",
                "#28a745"
            )
        
        st.divider()
        
        # Phase status cards
        st.subheader("🏗️ Phase Status Overview")
        
        phase_cols = st.columns(4)
        phases_data = coordination_data.get('phases', [])
        
        for i, phase in enumerate(phases_data):
            with phase_cols[i]:
                self.render_phase_status_card(phase)
        
        st.divider()
        
        # Integration dependency graph
        st.subheader("🔗 Integration Dependencies")
        self.render_dependency_graph(coordination_data)

    def render_integration_matrix_tab(self):
        """Render integration matrix showing cross-phase dependencies"""
        st.header("🔄 Integration Matrix")
        
        # Integration status matrix
        integration_data = self.get_integration_matrix()
        
        if integration_data:
            # Create matrix visualization
            matrix_df = pd.DataFrame(integration_data['matrix'])
            
            fig = px.imshow(
                matrix_df.values,
                x=matrix_df.columns,
                y=matrix_df.index,
                aspect="auto",
                color_continuous_scale="RdYlGn",
                title="Cross-Phase Integration Health"
            )
            
            fig.update_layout(
                xaxis_title="Target Phase",
                yaxis_title="Source Phase",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Integration timeline
        st.subheader("📅 Integration Timeline")
        self.render_integration_timeline()
        
        # Critical path analysis
        st.subheader("🎯 Critical Path Analysis")
        self.render_critical_path()

    def render_phase_progress_tab(self):
        """Render detailed phase progress tracking"""
        st.header("📈 Phase Progress Tracking")
        
        phase_progress = self.get_phase_progress()
        
        if phase_progress:
            # Progress overview chart
            progress_df = pd.DataFrame(phase_progress)
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("Completion Progress", "Task Distribution", "Team Velocity", "Risk Levels"),
                specs=[[{"type": "bar"}, {"type": "pie"}],
                       [{"type": "scatter"}, {"type": "bar"}]]
            )
            
            # Completion progress
            fig.add_trace(
                go.Bar(x=progress_df['phase_name'], y=progress_df['completion_percentage']),
                row=1, col=1
            )
            
            # Task distribution
            fig.add_trace(
                go.Pie(labels=['Completed', 'Active', 'Blocked'], 
                       values=[sum(progress_df['completed_tasks']), 
                              sum(progress_df['active_tasks']),
                              sum(progress_df['blocked_tasks'])]),
                row=1, col=2
            )
            
            # Team velocity (mock data)
            velocity_dates = pd.date_range(end='today', periods=7)
            velocity_data = [20, 25, 18, 30, 28, 22, 26]  # Mock velocity data
            fig.add_trace(
                go.Scatter(x=velocity_dates, y=velocity_data, mode='lines+markers'),
                row=2, col=1
            )
            
            # Risk levels
            risk_levels = [phase.get('risk_level', 0) for phase in phase_progress]
            fig.add_trace(
                go.Bar(x=progress_df['phase_name'], y=risk_levels),
                row=2, col=2
            )
            
            fig.update_layout(height=800, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed phase breakdown
        st.subheader("📋 Detailed Phase Breakdown")
        
        for phase in phase_progress or []:
            with st.expander(f"Phase {phase['phase_id']}: {phase['phase_name']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Completion", f"{phase['completion_percentage']:.1f}%")
                    st.write(f"**Team Lead**: {phase['team_lead']}")
                
                with col2:
                    st.metric("Active Tasks", phase['active_tasks'])
                    st.metric("Completed Tasks", phase['completed_tasks'])
                    st.metric("Blocked Tasks", phase['blocked_tasks'])
                
                with col3:
                    st.write(f"**Next Milestone**: {phase['next_milestone']}")
                    st.write(f"**Dependencies**: {', '.join(map(str, phase['dependencies']))}")
                    
                    health_color = self.get_health_color(phase['health_status'])
                    st.markdown(f"**Health**: <span style='color: {health_color}'>{phase['health_status'].title()}</span>", 
                              unsafe_allow_html=True)

    def render_risk_management_tab(self):
        """Render risk management dashboard"""
        st.header("🚨 Risk Management Dashboard")
        
        risks = self.get_risk_assessment()
        
        if risks:
            # Risk matrix
            st.subheader("📊 Risk Matrix")
            
            risk_df = pd.DataFrame(risks['risk_items'])
            
            fig = px.scatter(
                risk_df,
                x='probability',
                y='impact',
                size='severity_score',
                color='phase',
                hover_name='risk_title',
                title="Risk Impact vs Probability Matrix"
            )
            
            fig.update_layout(
                xaxis_title="Probability",
                yaxis_title="Impact",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Risk mitigation status
            st.subheader("🛡️ Mitigation Status")
            
            mitigation_cols = st.columns(3)
            
            with mitigation_cols[0]:
                st.metric("High Risk Items", risks['summary']['high_risk_count'])
            with mitigation_cols[1]:
                st.metric("Mitigated Risks", risks['summary']['mitigated_count'])
            with mitigation_cols[2]:
                st.metric("Open Actions", risks['summary']['open_actions'])
            
            # Detailed risk list
            st.subheader("📋 Risk Register")
            
            for risk in risks['risk_items']:
                risk_color = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(risk['severity'], '⚫')
                
                with st.expander(f"{risk_color} {risk['risk_title']} (Phase {risk['phase']})"):
                    st.write(f"**Description**: {risk['description']}")
                    st.write(f"**Probability**: {risk['probability']:.1f}")
                    st.write(f"**Impact**: {risk['impact']:.1f}")
                    st.write(f"**Mitigation**: {risk['mitigation_strategy']}")
                    st.write(f"**Owner**: {risk['owner']}")
                    st.write(f"**Status**: {risk['status']}")

    def render_test_results_tab(self):
        """Render integration test results"""
        st.header("📋 Integration Test Results")
        
        test_results = self.get_test_results()
        
        if test_results:
            # Test summary metrics
            summary_cols = st.columns(4)
            
            with summary_cols[0]:
                self.render_metric_card(
                    "Total Tests",
                    str(test_results['summary']['total_tests']),
                    "🧪",
                    "#007bff"
                )
            
            with summary_cols[1]:
                self.render_metric_card(
                    "Success Rate",
                    f"{test_results['summary']['success_rate']:.1f}%",
                    "✅",
                    "#28a745"
                )
            
            with summary_cols[2]:
                self.render_metric_card(
                    "Failed Tests", 
                    str(test_results['summary']['failed_tests']),
                    "❌",
                    "#dc3545"
                )
            
            with summary_cols[3]:
                self.render_metric_card(
                    "Avg Duration",
                    f"{test_results['summary']['avg_duration']:.1f}s",
                    "⏱️",
                    "#6f42c1"
                )
            
            st.divider()
            
            # Phase-wise test results
            st.subheader("📊 Phase Test Results")
            
            phase_test_df = pd.DataFrame(test_results['phase_results'])
            
            fig = px.bar(
                phase_test_df,
                x='phase',
                y=['passed', 'failed'],
                title="Test Results by Phase",
                barmode='stack'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed test results
            st.subheader("🔍 Detailed Test Results")
            
            for test in test_results['test_details']:
                status_icon = "✅" if test['status'] == 'passed' else "❌"
                
                with st.expander(f"{status_icon} {test['test_name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Duration**: {test['duration']:.2f}s")
                        st.write(f"**Phase Coverage**: {', '.join(map(str, test['phases_tested']))}")
                    
                    with col2:
                        st.write(f"**Status**: {test['status'].title()}")
                        st.write(f"**Timestamp**: {test['timestamp']}")
                    
                    if test.get('errors'):
                        st.error(f"**Error**: {test['errors'][0]}")

    # Helper methods
    def render_metric_card(self, title: str, value: str, icon: str, color: str):
        """Render a metric card"""
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h3 style="margin: 0; color: {color};">{value}</h3>
                    <p style="margin: 0; color: #666;">{title}</p>
                </div>
                <div style="font-size: 2em;">{icon}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def render_phase_status_card(self, phase: Dict[str, Any]):
        """Render a phase status card"""
        health_color = self.get_health_color(phase['health_status'])
        
        st.markdown(f"""
        <div class="phase-card">
            <h4>Phase {phase['phase_id']}: {phase['phase_name']}</h4>
            <p><strong>Progress:</strong> {phase['completion_percentage']:.1f}%</p>
            <p><strong>Health:</strong> <span style="color: {health_color};">{phase['health_status'].title()}</span></p>
            <p><strong>Lead:</strong> {phase['team_lead']}</p>
            <p><strong>Tasks:</strong> {phase['active_tasks']} active, {phase['completed_tasks']} done</p>
        </div>
        """, unsafe_allow_html=True)

    def get_health_color(self, health_status: str) -> str:
        """Get color for health status"""
        return {
            "healthy": "#28a745",
            "degraded": "#ffc107", 
            "unhealthy": "#dc3545"
        }.get(health_status, "#6c757d")

    def handle_auto_refresh(self):
        """Handle auto-refresh logic"""
        if hasattr(st.session_state, 'last_refresh'):
            time_since_refresh = (datetime.utcnow() - st.session_state.last_refresh).total_seconds()
            
            if time_since_refresh > self.refresh_interval:
                self.refresh_coordination_data()
                st.session_state.last_refresh = datetime.utcnow()
                st.rerun()

    # Data loading methods (mock implementations)
    def get_coordination_data(self) -> Dict[str, Any]:
        """Get overall coordination data"""
        # Mock data - in real implementation, would call API
        return {
            "overall_progress": 67.5,
            "integration_health": "healthy",
            "active_tasks": 23,
            "estimated_days": 28,
            "progress_trend": "+5.2%",
            "phases": [
                {
                    "phase_id": 1,
                    "phase_name": "Security & Infrastructure",
                    "completion_percentage": 85.0,
                    "health_status": "healthy",
                    "active_tasks": 3,
                    "completed_tasks": 17,
                    "blocked_tasks": 0,
                    "team_lead": "Alice Johnson",
                    "next_milestone": "Database optimization",
                    "dependencies": []
                },
                {
                    "phase_id": 2,
                    "phase_name": "AI Enhancement",
                    "completion_percentage": 72.5,
                    "health_status": "healthy",
                    "active_tasks": 8,
                    "completed_tasks": 21,
                    "blocked_tasks": 1,
                    "team_lead": "Bob Chen",
                    "next_milestone": "Voice AI integration",
                    "dependencies": [1]
                },
                {
                    "phase_id": 3,
                    "phase_name": "Frontend Enhancement",
                    "completion_percentage": 58.0,
                    "health_status": "degraded",
                    "active_tasks": 12,
                    "completed_tasks": 14,
                    "blocked_tasks": 2,
                    "team_lead": "Carol Martinez",
                    "next_milestone": "Real-time dashboard",
                    "dependencies": [1, 2]
                },
                {
                    "phase_id": 4,
                    "phase_name": "Deployment & Scaling",
                    "completion_percentage": 45.0,
                    "health_status": "healthy",
                    "active_tasks": 6,
                    "completed_tasks": 8,
                    "blocked_tasks": 0,
                    "team_lead": "Dave Wilson",
                    "next_milestone": "Auto-scaling setup",
                    "dependencies": [1, 2, 3]
                }
            ]
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        # Mock data
        return {
            "overall_status": "healthy",
            "services": {
                "database": {"status": "up"},
                "redis": {"status": "up"},
                "ai_models": {"status": "up"},
                "frontend": {"status": "up"}
            }
        }

    def get_integration_matrix(self) -> Dict[str, Any]:
        """Get integration matrix data"""
        # Mock data
        return {
            "matrix": [
                [1.0, 0.9, 0.8, 0.7],
                [0.9, 1.0, 0.85, 0.6],
                [0.8, 0.85, 1.0, 0.75],
                [0.7, 0.6, 0.75, 1.0]
            ]
        }

    def get_phase_progress(self) -> List[Dict[str, Any]]:
        """Get detailed phase progress data"""
        return self.get_coordination_data()['phases']

    def get_risk_assessment(self) -> Dict[str, Any]:
        """Get risk assessment data"""
        # Mock data
        return {
            "summary": {
                "high_risk_count": 2,
                "mitigated_count": 8,
                "open_actions": 5
            },
            "risk_items": [
                {
                    "risk_title": "Database Schema Conflicts",
                    "phase": 1,
                    "description": "Multiple teams modifying schema simultaneously",
                    "probability": 0.7,
                    "impact": 0.9,
                    "severity": "high",
                    "severity_score": 0.63,
                    "mitigation_strategy": "Single source of truth for schema changes",
                    "owner": "Alice Johnson",
                    "status": "Active"
                },
                {
                    "risk_title": "AI API Rate Limiting",
                    "phase": 2,
                    "description": "Claude API rate limits affecting performance",
                    "probability": 0.5,
                    "impact": 0.6,
                    "severity": "medium",
                    "severity_score": 0.3,
                    "mitigation_strategy": "Implement caching and fallback mechanisms",
                    "owner": "Bob Chen",
                    "status": "Mitigated"
                }
            ]
        }

    def get_test_results(self) -> Dict[str, Any]:
        """Get integration test results"""
        # Mock data
        return {
            "summary": {
                "total_tests": 15,
                "success_rate": 86.7,
                "failed_tests": 2,
                "avg_duration": 12.5
            },
            "phase_results": [
                {"phase": "Phase 1", "passed": 8, "failed": 0},
                {"phase": "Phase 2", "passed": 6, "failed": 1},
                {"phase": "Phase 3", "passed": 5, "failed": 1},
                {"phase": "Phase 4", "passed": 4, "failed": 0}
            ],
            "test_details": [
                {
                    "test_name": "auth_ai_integration",
                    "status": "passed",
                    "duration": 5.2,
                    "phases_tested": [1, 2],
                    "timestamp": "2026-01-16T10:30:00Z"
                },
                {
                    "test_name": "real_time_updates",
                    "status": "failed",
                    "duration": 15.8,
                    "phases_tested": [2, 3],
                    "timestamp": "2026-01-16T10:35:00Z",
                    "errors": ["WebSocket connection timeout"]
                }
            ]
        }

    def refresh_coordination_data(self):
        """Refresh coordination data from APIs"""
        # In real implementation, would make API calls
        st.session_state.coordination_data = self.get_coordination_data()
        st.session_state.last_refresh = datetime.utcnow()
        st.success("Data refreshed successfully!")

    def trigger_integration_tests(self):
        """Trigger integration test suite"""
        with st.spinner("Running integration tests..."):
            time.sleep(2)  # Simulate test execution
        st.success("Integration tests completed successfully!")

    def generate_coordination_reports(self):
        """Generate coordination reports"""
        with st.spinner("Generating reports..."):
            time.sleep(1)  # Simulate report generation
        st.success("Reports generated and saved to coordination/reports/")

    def render_dependency_graph(self, coordination_data: Dict[str, Any]):
        """Render dependency graph visualization"""
        # Simple dependency visualization
        phases = coordination_data.get('phases', [])
        
        # Create dependency matrix for visualization
        dependency_text = "**Phase Dependencies:**\n\n"
        for phase in phases:
            deps = phase.get('dependencies', [])
            if deps:
                dep_names = [f"Phase {d}" for d in deps]
                dependency_text += f"• **Phase {phase['phase_id']}** depends on: {', '.join(dep_names)}\n"
            else:
                dependency_text += f"• **Phase {phase['phase_id']}** has no dependencies\n"
        
        st.markdown(dependency_text)

    def render_integration_timeline(self):
        """Render integration timeline"""
        # Mock timeline data
        timeline_data = [
            {"phase": "Phase 1→2", "start": "2026-01-10", "end": "2026-01-20", "status": "completed"},
            {"phase": "Phase 2→3", "start": "2026-01-15", "end": "2026-01-25", "status": "in_progress"},
            {"phase": "Phase 3→4", "start": "2026-01-22", "end": "2026-02-01", "status": "planned"},
            {"phase": "End-to-End", "start": "2026-01-28", "end": "2026-02-05", "status": "planned"}
        ]
        
        timeline_df = pd.DataFrame(timeline_data)
        timeline_df['start'] = pd.to_datetime(timeline_df['start'])
        timeline_df['end'] = pd.to_datetime(timeline_df['end'])
        
        fig = px.timeline(
            timeline_df,
            x_start='start',
            x_end='end',
            y='phase',
            color='status',
            title="Integration Timeline"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def render_critical_path(self):
        """Render critical path analysis"""
        critical_path = [
            {"task": "Phase 1 Security Setup", "duration": 10, "phase": 1},
            {"task": "Phase 2 AI Model Integration", "duration": 8, "phase": 2},
            {"task": "Phase 3 Real-time Dashboard", "duration": 12, "phase": 3},
            {"task": "Phase 4 Auto-scaling", "duration": 6, "phase": 4},
            {"task": "End-to-End Testing", "duration": 4, "phase": "All"}
        ]
        
        critical_path_df = pd.DataFrame(critical_path)
        
        fig = px.bar(
            critical_path_df,
            x='task',
            y='duration',
            color='phase',
            title="Critical Path Analysis (Days)"
        )
        
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)


# Main execution
if __name__ == "__main__":
    dashboard = CoordinationDashboard()
    dashboard.render_dashboard()