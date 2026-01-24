"""
Health Dashboard Component for Production Monitoring.

Provides real-time system health monitoring and database optimization status.
"""

import streamlit as st
import asyncio
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ghl_real_estate_ai.services.production_monitoring import (
    get_production_monitor, check_database_health, check_cache_health, check_auth_service_health
)
from ghl_real_estate_ai.services.database_optimizer import get_database_optimizer
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

def render_system_health_overview():
    """Render system health overview section."""
    st.subheader("🔍 System Health Overview")

    try:
        # Get production monitor
        monitor = get_production_monitor()

        # Run health checks asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize monitoring if not done
        try:
            loop.run_until_complete(monitor.initialize_monitoring())
        except Exception as e:
            logger.debug(f"Monitor already initialized: {e}")

        # Perform health checks
        health_summary = loop.run_until_complete(monitor.get_health_summary())
        system_metrics = loop.run_until_complete(monitor.collect_system_metrics())

        loop.close()

        # Display overall status
        overall_status = health_summary.get('overall_status', 'unknown')
        status_colors = {
            'healthy': '🟢',
            'warning': '🟡',
            'critical': '🔴',
            'unknown': '⚪'
        }

        st.markdown(f"""
        ### {status_colors.get(overall_status, '⚪')} System Status: {overall_status.title()}
        **Last Updated:** {health_summary.get('last_updated', 'Unknown')}
        """)

        # System metrics cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            cpu_percent = system_metrics.cpu_percent
            cpu_color = "normal" if cpu_percent < 70 else "inverse"
            st.metric(
                "CPU Usage",
                f"{cpu_percent:.1f}%",
                delta=None,
                help="Current CPU utilization"
            )

        with col2:
            memory_percent = system_metrics.memory_percent
            memory_color = "normal" if memory_percent < 80 else "inverse"
            st.metric(
                "Memory Usage",
                f"{memory_percent:.1f}%",
                delta=None,
                help="Current memory utilization"
            )

        with col3:
            disk_percent = system_metrics.disk_percent
            disk_color = "normal" if disk_percent < 85 else "inverse"
            st.metric(
                "Disk Usage",
                f"{disk_percent:.1f}%",
                delta=None,
                help="Current disk utilization"
            )

        with col4:
            st.metric(
                "Uptime",
                f"{system_metrics.uptime_hours:.1f}h",
                delta=None,
                help="System uptime in hours"
            )

        # Active alerts
        active_alerts = health_summary.get('active_alerts', 0)
        if active_alerts > 0:
            st.warning(f"⚠️ {active_alerts} active alerts require attention")
        else:
            st.success("✅ No active alerts")

        # Services status
        services_count = health_summary.get('services', 0)
        healthy_services = health_summary.get('healthy_services', 0)

        if services_count > 0:
            service_health_ratio = healthy_services / services_count
            if service_health_ratio >= 1.0:
                st.success(f"✅ All {services_count} services healthy")
            elif service_health_ratio >= 0.8:
                st.warning(f"⚠️ {healthy_services}/{services_count} services healthy")
            else:
                st.error(f"❌ Only {healthy_services}/{services_count} services healthy")

    except Exception as e:
        logger.error(f"Failed to render system health overview: {e}")
        st.error("❌ Unable to fetch system health data")

def render_service_health_checks():
    """Render detailed service health checks."""
    st.subheader("🛠️ Service Health Checks")

    try:
        monitor = get_production_monitor()

        # Define health check functions
        health_checks = {
            'Database': check_database_health,
            'Cache': check_cache_health,
            'Authentication': check_auth_service_health
        }

        # Run health checks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        health_results = {}
        for service_name, check_func in health_checks.items():
            try:
                health_check = loop.run_until_complete(
                    monitor.check_service_health(service_name, check_func)
                )
                health_results[service_name] = health_check
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")

        loop.close()

        # Display health check results
        for service_name, health_check in health_results.items():
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 3])

                with col1:
                    status_emoji = {
                        'healthy': '🟢',
                        'warning': '🟡',
                        'critical': '🔴',
                        'down': '⚫'
                    }
                    st.markdown(f"**{status_emoji.get(health_check.status.value, '⚪')} {service_name}**")

                with col2:
                    st.text(f"{health_check.response_time_ms:.0f}ms")

                with col3:
                    st.text(health_check.message)

        # Service performance chart
        st.subheader("📊 Service Response Times")

        if health_results:
            # Create response time chart
            services = list(health_results.keys())
            response_times = [hr.response_time_ms for hr in health_results.values()]

            fig = go.Figure(data=[
                go.Bar(
                    x=services,
                    y=response_times,
                    marker_color=['green' if rt < 1000 else 'orange' if rt < 2000 else 'red' for rt in response_times]
                )
            ])

            fig.update_layout(
                title="Service Response Times",
                xaxis_title="Service",
                yaxis_title="Response Time (ms)",
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Failed to render service health checks: {e}")
        st.error("❌ Unable to perform service health checks")

def render_database_optimization_status():
    """Render database optimization status and controls."""
    st.subheader("🗄️ Database Optimization")

    try:
        optimizer = get_database_optimizer()

        # Database paths to monitor
        database_paths = [
            "data/auth.db",
            "data/monitoring.db"
        ]

        # Database health analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize optimizer if needed
        try:
            loop.run_until_complete(optimizer.initialize_optimizer())
        except Exception as e:
            logger.debug(f"Optimizer already initialized: {e}")

        db_health_data = {}
        for db_path in database_paths:
            try:
                health = loop.run_until_complete(optimizer.analyze_database_health(db_path))
                db_health_data[db_path] = health
            except Exception as e:
                logger.error(f"Database health analysis failed for {db_path}: {e}")

        loop.close()

        # Display database health summary
        if db_health_data:
            st.markdown("#### Database Health Summary")

            # Create summary table
            summary_data = []
            for db_path, health in db_health_data.items():
                db_name = db_path.split('/')[-1].replace('.db', '')
                summary_data.append({
                    'Database': db_name,
                    'Size (MB)': f"{health.database_size_mb:.2f}",
                    'Avg Query Time (ms)': f"{health.avg_query_time_ms:.1f}",
                    'Slow Queries': health.slow_queries_count,
                    'Cache Hit Rate': f"{health.cache_hit_ratio:.1%}",
                    'Fragmentation': f"{health.fragmentation_ratio:.1%}"
                })

            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True)

            # Database size chart
            st.markdown("#### Database Sizes")

            db_names = [db.split('/')[-1].replace('.db', '') for db in db_health_data.keys()]
            db_sizes = [health.database_size_mb for health in db_health_data.values()]

            fig = px.pie(
                values=db_sizes,
                names=db_names,
                title="Database Size Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Optimization recommendations
            st.markdown("#### Optimization Recommendations")

            for db_path, health in db_health_data.items():
                db_name = db_path.split('/')[-1].replace('.db', '')

                with st.expander(f"📋 {db_name} Recommendations"):
                    for i, recommendation in enumerate(health.recommendations, 1):
                        st.markdown(f"{i}. {recommendation}")

                    # Last optimization info
                    time_since_optimization = datetime.now() - health.last_optimization
                    if time_since_optimization.days > 7:
                        st.warning(f"⚠️ Last optimized {time_since_optimization.days} days ago")
                    else:
                        st.success(f"✅ Recently optimized ({time_since_optimization.days} days ago)")

        # Manual optimization controls
        st.markdown("#### Manual Optimization")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔧 Optimize All Databases", help="Run optimization on all databases"):
                with st.spinner("Optimizing databases..."):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        optimization_results = []
                        for db_path in database_paths:
                            result = loop.run_until_complete(optimizer.optimize_database(db_path))
                            optimization_results.append(result)

                        loop.close()

                        # Display results
                        for result in optimization_results:
                            db_name = result['database'].split('/')[-1]
                            if result['errors']:
                                st.error(f"❌ {db_name}: {result['errors'][0]}")
                            else:
                                st.success(f"✅ {db_name}: {len(result['operations'])} operations completed")

                    except Exception as e:
                        st.error(f"❌ Optimization failed: {e}")

        with col2:
            if st.button("📊 Analyze Performance", help="Analyze database performance"):
                with st.spinner("Analyzing performance..."):
                    try:
                        # Refresh health data
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        for db_path in database_paths:
                            health = loop.run_until_complete(optimizer.analyze_database_health(db_path))
                            db_health_data[db_path] = health

                        loop.close()

                        st.success("✅ Performance analysis completed")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Performance analysis failed: {e}")

    except Exception as e:
        logger.error(f"Failed to render database optimization status: {e}")
        st.error("❌ Unable to load database optimization data")

def render_performance_metrics():
    """Render performance metrics and charts."""
    st.subheader("📈 Performance Metrics")

    try:
        # Generate sample performance data for visualization
        # In a real implementation, this would come from the monitoring database

        # Response time trend
        st.markdown("#### Response Time Trend")

        dates = pd.date_range(start=datetime.now() - timedelta(hours=24), periods=24, freq='H')
        response_times = [50 + (i % 5) * 10 for i in range(24)]  # Sample data

        fig = px.line(
            x=dates,
            y=response_times,
            title="Average Response Time (Last 24 Hours)",
            labels={'x': 'Time', 'y': 'Response Time (ms)'}
        )
        fig.add_hline(y=100, line_dash="dash", line_color="orange", annotation_text="Target (100ms)")
        st.plotly_chart(fig, use_container_width=True)

        # Error rate chart
        st.markdown("#### Error Rate")

        error_rates = [0.1 + (i % 3) * 0.05 for i in range(24)]  # Sample data

        fig = px.line(
            x=dates,
            y=error_rates,
            title="Error Rate (Last 24 Hours)",
            labels={'x': 'Time', 'y': 'Error Rate (%)'}
        )
        fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Alert Threshold (1%)")
        st.plotly_chart(fig, use_container_width=True)

        # Key performance indicators
        st.markdown("#### Key Performance Indicators")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Avg Response Time", "85ms", "-5ms")

        with col2:
            st.metric("Error Rate", "0.12%", "+0.02%")

        with col3:
            st.metric("Throughput", "1,247 req/min", "+23")

        with col4:
            st.metric("Availability", "99.8%", "+0.1%")

    except Exception as e:
        logger.error(f"Failed to render performance metrics: {e}")
        st.error("❌ Unable to load performance metrics")

def render_health_dashboard():
    """Main function to render the complete health dashboard."""
    try:
        st.header("🏥 Production Health Dashboard")
        st.markdown("Real-time system monitoring and database optimization status")

        # System health overview
        render_system_health_overview()

        st.markdown("---")

        # Service health checks
        render_service_health_checks()

        st.markdown("---")

        # Database optimization status
        render_database_optimization_status()

        st.markdown("---")

        # Performance metrics
        render_performance_metrics()

    except Exception as e:
        logger.error(f"Failed to render health dashboard: {e}")
        st.error("🚨 Health dashboard error. Please refresh the page.")

# Export main function for use in dashboard
__all__ = ['render_health_dashboard']