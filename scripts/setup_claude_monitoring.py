#!/usr/bin/env python3
"""
Claude Services Monitoring Setup Script

Automated setup script for comprehensive monitoring of Claude services
including Prometheus configuration, Grafana dashboards, and alerting rules.

Usage:
    python scripts/setup_claude_monitoring.py --install
    python scripts/setup_claude_monitoring.py --configure
    python scripts/setup_claude_monitoring.py --dashboards
    python scripts/setup_claude_monitoring.py --full-setup

Created: January 2026
Author: Enterprise Development Team
"""

import asyncio
import argparse
import logging
import sys
import json
import yaml
import requests
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClaudeMonitoringSetup:
    """Setup and configuration manager for Claude services monitoring."""

    def __init__(self):
        self.project_root = project_root
        self.config_dir = project_root / "config" / "monitoring"
        self.scripts_dir = project_root / "scripts"

        # Service configurations
        self.prometheus_config = self.config_dir / "prometheus_claude.yml"
        self.grafana_dashboard = self.config_dir / "claude_dashboards.json"

        # Default endpoints
        self.prometheus_url = "http://localhost:9090"
        self.grafana_url = "http://localhost:3000"
        self.grafana_credentials = ("admin", "admin")  # Default credentials

    async def install_monitoring_stack(self) -> bool:
        """Install Prometheus and Grafana using Docker."""
        print("🔧 Installing Claude monitoring stack...")

        try:
            # Check if Docker is available
            result = subprocess.run(["docker", "--version"],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker is required but not found")
                return False

            # Create docker-compose for monitoring stack
            docker_compose_content = self._generate_docker_compose()

            compose_file = self.project_root / "docker-compose.monitoring.yml"
            with open(compose_file, 'w') as f:
                f.write(docker_compose_content)

            print("📄 Created docker-compose.monitoring.yml")

            # Start monitoring services
            cmd = [
                "docker-compose",
                "-f", str(compose_file),
                "up", "-d"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to start monitoring services: {result.stderr}")
                return False

            print("✅ Monitoring stack started successfully")

            # Wait for services to be ready
            print("⏳ Waiting for services to start...")
            await self._wait_for_services()

            return True

        except Exception as e:
            print(f"❌ Error installing monitoring stack: {e}")
            return False

    def _generate_docker_compose(self) -> str:
        """Generate Docker Compose configuration for monitoring."""
        return """
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: claude-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/monitoring/prometheus_claude.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: claude-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/monitoring:/etc/grafana/provisioning
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: claude-node-exporter
    ports:
      - "9100:9100"
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    restart: unless-stopped

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: claude-redis-exporter
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis://host.docker.internal:6379
    restart: unless-stopped

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: claude-postgres-exporter
    ports:
      - "9187:9187"
    environment:
      - DATA_SOURCE_NAME=postgresql://postgres:password@host.docker.internal:5432/enterprisehub?sslmode=disable
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
"""

    async def _wait_for_services(self):
        """Wait for monitoring services to be ready."""
        services = [
            ("Prometheus", self.prometheus_url, "/api/v1/status/config"),
            ("Grafana", self.grafana_url, "/api/health")
        ]

        for service_name, base_url, endpoint in services:
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        print(f"✅ {service_name} is ready")
                        break
                except requests.exceptions.RequestException:
                    pass

                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                else:
                    print(f"⚠️  {service_name} may not be ready")

    async def configure_prometheus(self) -> bool:
        """Configure Prometheus for Claude services monitoring."""
        print("⚙️ Configuring Prometheus for Claude services...")

        try:
            # Validate Prometheus configuration
            if not self.prometheus_config.exists():
                print(f"❌ Prometheus config not found: {self.prometheus_config}")
                return False

            # Test configuration syntax
            cmd = [
                "docker", "exec", "claude-prometheus",
                "promtool", "check", "config", "/etc/prometheus/prometheus.yml"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Invalid Prometheus configuration: {result.stderr}")
                return False

            print("✅ Prometheus configuration validated")

            # Reload Prometheus configuration
            reload_url = f"{self.prometheus_url}/-/reload"
            response = requests.post(reload_url)

            if response.status_code == 200:
                print("✅ Prometheus configuration reloaded")
                return True
            else:
                print(f"❌ Failed to reload Prometheus: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error configuring Prometheus: {e}")
            return False

    async def setup_grafana_dashboards(self) -> bool:
        """Setup Grafana dashboards for Claude services."""
        print("📊 Setting up Grafana dashboards for Claude services...")

        try:
            # Add Prometheus data source
            if not await self._add_prometheus_datasource():
                return False

            # Import Claude dashboard
            if not await self._import_claude_dashboard():
                return False

            print("✅ Grafana dashboards configured successfully")
            return True

        except Exception as e:
            print(f"❌ Error setting up Grafana dashboards: {e}")
            return False

    async def _add_prometheus_datasource(self) -> bool:
        """Add Prometheus as a data source in Grafana."""
        print("  🔗 Adding Prometheus data source...")

        datasource_config = {
            "name": "Prometheus",
            "type": "prometheus",
            "url": "http://prometheus:9090",
            "access": "proxy",
            "isDefault": True
        }

        try:
            auth = self.grafana_credentials
            response = requests.post(
                f"{self.grafana_url}/api/datasources",
                json=datasource_config,
                auth=auth,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in [200, 409]:  # 409 = already exists
                print("  ✅ Prometheus data source configured")
                return True
            else:
                print(f"  ❌ Failed to add data source: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"  ❌ Error adding data source: {e}")
            return False

    async def _import_claude_dashboard(self) -> bool:
        """Import Claude services dashboard into Grafana."""
        print("  📈 Importing Claude services dashboard...")

        try:
            if not self.grafana_dashboard.exists():
                print(f"  ❌ Dashboard file not found: {self.grafana_dashboard}")
                return False

            # Load dashboard configuration
            with open(self.grafana_dashboard, 'r') as f:
                dashboard_config = json.load(f)

            # Import dashboard
            import_config = {
                "dashboard": dashboard_config["dashboard"],
                "overwrite": True,
                "inputs": [
                    {
                        "name": "DS_PROMETHEUS",
                        "type": "datasource",
                        "pluginId": "prometheus",
                        "value": "Prometheus"
                    }
                ]
            }

            auth = self.grafana_credentials
            response = requests.post(
                f"{self.grafana_url}/api/dashboards/import",
                json=import_config,
                auth=auth,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                dashboard_data = response.json()
                dashboard_url = f"{self.grafana_url}/d/{dashboard_data['uid']}"
                print(f"  ✅ Dashboard imported: {dashboard_url}")
                return True
            else:
                print(f"  ❌ Failed to import dashboard: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"  ❌ Error importing dashboard: {e}")
            return False

    async def setup_alerting(self) -> bool:
        """Setup alerting rules for Claude services."""
        print("🚨 Setting up alerting for Claude services...")

        try:
            # Create alerting rules file
            alerts_config = self._generate_alerting_rules()
            alerts_file = self.config_dir / "claude_alerts.yml"

            with open(alerts_file, 'w') as f:
                yaml.dump(alerts_config, f, default_flow_style=False)

            print("📄 Created alerting rules file")

            # Validate alerting rules
            cmd = [
                "docker", "exec", "claude-prometheus",
                "promtool", "check", "rules", "/etc/prometheus/claude_alerts.yml"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Invalid alerting rules: {result.stderr}")
                return False

            print("✅ Alerting rules validated and configured")
            return True

        except Exception as e:
            print(f"❌ Error setting up alerting: {e}")
            return False

    def _generate_alerting_rules(self) -> Dict[str, Any]:
        """Generate alerting rules configuration."""
        return {
            "groups": [
                {
                    "name": "claude_service_alerts",
                    "rules": [
                        {
                            "alert": "ClaudeServiceDown",
                            "expr": "claude_service_up == 0",
                            "for": "1m",
                            "labels": {"severity": "critical"},
                            "annotations": {
                                "summary": "Claude service {{ $labels.service }} is down",
                                "description": "Claude service {{ $labels.service }} has been down for more than 1 minute."
                            }
                        },
                        {
                            "alert": "ClaudeHighErrorRate",
                            "expr": "rate(claude_errors_total[5m]) / rate(claude_requests_total[5m]) > 0.05",
                            "for": "5m",
                            "labels": {"severity": "warning"},
                            "annotations": {
                                "summary": "Claude services high error rate",
                                "description": "Claude services error rate is above 5% for more than 5 minutes."
                            }
                        },
                        {
                            "alert": "ClaudeHighLatency",
                            "expr": "histogram_quantile(0.95, rate(claude_request_duration_seconds_bucket[5m])) > 1",
                            "for": "2m",
                            "labels": {"severity": "warning"},
                            "annotations": {
                                "summary": "Claude services high latency",
                                "description": "Claude services 95th percentile latency is above 1 second for more than 2 minutes."
                            }
                        }
                    ]
                }
            ]
        }

    async def validate_monitoring_setup(self) -> Dict[str, bool]:
        """Validate the complete monitoring setup."""
        print("✅ Validating Claude monitoring setup...")

        validation_results = {}

        # Check Prometheus
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=10)
            validation_results["prometheus"] = response.status_code == 200
        except:
            validation_results["prometheus"] = False

        # Check Grafana
        try:
            response = requests.get(f"{self.grafana_url}/api/health", timeout=10)
            validation_results["grafana"] = response.status_code == 200
        except:
            validation_results["grafana"] = False

        # Check dashboards
        try:
            auth = self.grafana_credentials
            response = requests.get(f"{self.grafana_url}/api/search?query=Claude",
                                  auth=auth, timeout=10)
            dashboards = response.json() if response.status_code == 200 else []
            validation_results["dashboards"] = len(dashboards) > 0
        except:
            validation_results["dashboards"] = False

        # Check alerting rules
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/rules", timeout=10)
            rules_data = response.json() if response.status_code == 200 else {}
            claude_rules = any("claude" in str(group).lower()
                             for group in rules_data.get("data", {}).get("groups", []))
            validation_results["alerting"] = claude_rules
        except:
            validation_results["alerting"] = False

        # Print validation results
        for component, status in validation_results.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component.title()}: {'OK' if status else 'FAILED'}")

        return validation_results

    def generate_monitoring_summary(self) -> str:
        """Generate monitoring setup summary."""
        return f"""
🎯 Claude Services Monitoring Setup Complete

📊 Components Installed:
   ✅ Prometheus (metrics collection)
   ✅ Grafana (visualization dashboards)
   ✅ Node Exporter (system metrics)
   ✅ Redis Exporter (cache metrics)
   ✅ PostgreSQL Exporter (database metrics)

🔗 Access URLs:
   Prometheus: {self.prometheus_url}
   Grafana: {self.grafana_url}

📈 Dashboards:
   Claude Services Overview
   Performance Monitoring
   Business Intelligence KPIs
   Real Estate Metrics

🚨 Alerting:
   Service health monitoring
   Performance threshold alerts
   Business KPI degradation alerts

⚙️ Configuration:
   Prometheus: {self.prometheus_config}
   Grafana: {self.grafana_dashboard}

🔍 Monitoring Targets:
   - Agent Orchestrator (:8001)
   - Enterprise Intelligence (:8002)
   - Business Intelligence (:8003)
   - API Integration (:8000)
   - Management Orchestration (:8004)

📊 Key Metrics Tracked:
   - Service availability and health
   - Request rates and response times
   - Error rates and failure patterns
   - Resource utilization (CPU, memory, disk)
   - Business KPIs (lead scoring, property matching)
   - Real estate specific metrics
"""

async def main():
    """Main monitoring setup script entry point."""
    parser = argparse.ArgumentParser(description="Claude Services Monitoring Setup")
    parser.add_argument("--install", action="store_true", help="Install monitoring stack")
    parser.add_argument("--configure", action="store_true", help="Configure monitoring services")
    parser.add_argument("--dashboards", action="store_true", help="Setup Grafana dashboards")
    parser.add_argument("--alerting", action="store_true", help="Setup alerting rules")
    parser.add_argument("--validate", action="store_true", help="Validate monitoring setup")
    parser.add_argument("--full-setup", action="store_true", help="Complete monitoring setup")

    args = parser.parse_args()

    if not any(vars(args).values()):
        args.full_setup = True  # Default to full setup

    setup = ClaudeMonitoringSetup()
    success = True

    try:
        if args.full_setup:
            print("🚀 Starting complete Claude monitoring setup...")

            success = await setup.install_monitoring_stack()
            if success:
                success = await setup.configure_prometheus()
            if success:
                success = await setup.setup_grafana_dashboards()
            if success:
                success = await setup.setup_alerting()

        else:
            if args.install:
                success = await setup.install_monitoring_stack()

            if args.configure and success:
                success = await setup.configure_prometheus()

            if args.dashboards and success:
                success = await setup.setup_grafana_dashboards()

            if args.alerting and success:
                success = await setup.setup_alerting()

        if args.validate or args.full_setup:
            validation_results = await setup.validate_monitoring_setup()
            validation_success = all(validation_results.values())
            if not validation_success:
                success = False

        if success:
            print("\n" + setup.generate_monitoring_summary())
            print("🎉 Claude monitoring setup completed successfully!")
        else:
            print("❌ Claude monitoring setup failed!")

        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Monitoring setup failed: {e}")
        print(f"❌ Setup failed: {e}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())