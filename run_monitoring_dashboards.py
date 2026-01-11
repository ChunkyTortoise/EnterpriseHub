#!/usr/bin/env python3
"""
Run EnterpriseHub Monitoring Dashboards
======================================

Script to launch the comprehensive monitoring dashboard suite for the
GHL Real Estate AI platform. Provides options to run individual dashboards
or the complete monitoring application.

Usage:
    # Run complete monitoring suite
    python run_monitoring_dashboards.py

    # Run specific dashboard
    python run_monitoring_dashboards.py --dashboard executive
    python run_monitoring_dashboards.py --dashboard operations
    python run_monitoring_dashboards.py --dashboard ml_performance
    python run_monitoring_dashboards.py --dashboard security

    # Run with custom configuration
    python run_monitoring_dashboards.py --config custom_config.json

    # Run in development mode
    python run_monitoring_dashboards.py --dev

Environment Variables:
    STREAMLIT_SERVER_PORT: Port to run the dashboard (default: 8501)
    STREAMLIT_SERVER_ADDRESS: Address to bind to (default: 0.0.0.0)
    REDIS_URL: Redis connection URL for caching
    DATABASE_URL: PostgreSQL connection URL
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import streamlit as st
from streamlit.web import cli as stcli

from ghl_real_estate_ai.streamlit_components.monitoring_app import MonitoringApp
from ghl_real_estate_ai.streamlit_components.monitoring_dashboard_suite import (
    MonitoringDashboardSuite,
    DashboardConfig,
    DashboardType
)
from ghl_real_estate_ai.services.monitoring_data_service import monitoring_data_service
from ghl_real_estate_ai.config.monitoring_config import monitoring_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run EnterpriseHub Monitoring Dashboards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--dashboard",
        choices=["executive", "operations", "ml_performance", "security"],
        help="Run specific dashboard (default: run complete suite)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("STREAMLIT_SERVER_PORT", "8501")),
        help="Port to run the dashboard server"
    )

    parser.add_argument(
        "--host",
        default=os.getenv("STREAMLIT_SERVER_ADDRESS", "0.0.0.0"),
        help="Host address to bind to"
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to custom configuration file"
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode with debug logging"
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable Redis caching"
    )

    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Use sample data instead of real metrics"
    )

    return parser.parse_args()


async def initialize_services(args):
    """Initialize monitoring services."""
    try:
        logger.info("Initializing monitoring services...")

        # Initialize data service
        await monitoring_data_service.initialize()

        # Configure monitoring based on arguments
        if args.no_cache:
            monitoring_config.cache.redis_enabled = False
            logger.info("Redis caching disabled")

        if args.sample_data:
            logger.info("Using sample data for testing")

        if args.dev:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("Debug logging enabled")

        logger.info("Monitoring services initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        raise


def create_dashboard_app(dashboard_type=None):
    """Create dashboard application."""
    if dashboard_type:
        # Create specific dashboard
        config = DashboardConfig(
            refresh_interval=10,
            max_data_points=200,
            enable_realtime=True,
            enable_exports=True,
            theme="real_estate_professional",
            mobile_responsive=True
        )

        dashboard_suite = MonitoringDashboardSuite(config)

        # Set page config
        st.set_page_config(
            page_title=f"EnterpriseHub {dashboard_type.title()} Dashboard",
            page_icon="🏢",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Render specific dashboard
        if dashboard_type == "executive":
            dashboard_suite.render_executive_dashboard()
        elif dashboard_type == "operations":
            dashboard_suite.render_operations_dashboard()
        elif dashboard_type == "ml_performance":
            dashboard_suite.render_ml_performance_dashboard()
        elif dashboard_type == "security":
            dashboard_suite.render_security_dashboard()

    else:
        # Create complete monitoring application
        app = MonitoringApp()
        app.run()


def run_streamlit_app(args):
    """Run Streamlit application."""
    # Create temporary main script for Streamlit
    temp_script = project_root / "temp_monitoring_dashboard.py"

    script_content = f'''
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from run_monitoring_dashboards import create_dashboard_app

# Run the dashboard
create_dashboard_app({repr(args.dashboard)})
'''

    try:
        # Write temporary script
        with open(temp_script, 'w') as f:
            f.write(script_content)

        # Configure Streamlit arguments
        streamlit_args = [
            "streamlit",
            "run",
            str(temp_script),
            "--server.port", str(args.port),
            "--server.address", args.host,
            "--server.headless", "true",
            "--server.runOnSave", "true" if args.dev else "false",
        ]

        # Add development options
        if args.dev:
            streamlit_args.extend([
                "--logger.level", "debug",
                "--client.showErrorDetails", "true"
            ])

        logger.info(f"Starting Streamlit dashboard on http://{args.host}:{args.port}")
        logger.info(f"Dashboard type: {args.dashboard or 'complete suite'}")

        # Run Streamlit
        sys.argv = streamlit_args
        stcli.main()

    finally:
        # Clean up temporary script
        if temp_script.exists():
            temp_script.unlink()


def print_startup_info(args):
    """Print startup information."""
    print("\n" + "="*80)
    print("🏢 EnterpriseHub Monitoring Dashboard Suite")
    print("="*80)
    print(f"Dashboard: {args.dashboard or 'Complete Suite'}")
    print(f"URL: http://{args.host}:{args.port}")
    print(f"Environment: {'Development' if args.dev else 'Production'}")
    print(f"Caching: {'Disabled' if args.no_cache else 'Enabled'}")
    print(f"Data Source: {'Sample Data' if args.sample_data else 'Real Metrics'}")
    print("\nFeatures:")
    print("  📊 Executive Dashboard - Business KPIs & ROI tracking")
    print("  ⚙️ Operations Dashboard - System health & performance")
    print("  🤖 ML Performance Dashboard - Model accuracy & drift detection")
    print("  🔒 Security Dashboard - Compliance & security monitoring")
    print("\nPress Ctrl+C to stop the dashboard")
    print("="*80 + "\n")


async def main():
    """Main application entry point."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Print startup information
        print_startup_info(args)

        # Initialize services
        await initialize_services(args)

        # Run Streamlit dashboard
        run_streamlit_app(args)

    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the application
    asyncio.run(main())