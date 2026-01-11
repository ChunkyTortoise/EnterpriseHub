#!/usr/bin/env python3
"""
EnterpriseHub Monitoring Management Script
Manages Prometheus + Grafana + AlertManager monitoring stack
Supports enterprise scaling and 99.95% uptime SLA monitoring
"""

import asyncio
import subprocess
import sys
import os
import json
import time
import argparse
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import requests
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoringManager:
    """
    Comprehensive monitoring stack management for EnterpriseHub.

    Features:
    - Docker Compose orchestration
    - Configuration validation
    - Health checks and diagnostics
    - Dashboard deployment
    - Alert rule management
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.monitoring_config_dir = self.project_root / "config" / "monitoring"
        self.docker_compose_file = self.monitoring_config_dir / "docker-compose.monitoring.yml"

        # Service endpoints
        self.services = {
            'prometheus': {'url': 'http://localhost:9090', 'health_path': '/-/healthy'},
            'grafana': {'url': 'http://localhost:3000', 'health_path': '/api/health'},
            'alertmanager': {'url': 'http://localhost:9093', 'health_path': '/-/healthy'},
            'node_exporter': {'url': 'http://localhost:9100', 'health_path': '/'},
            'enterprise_metrics': {'url': 'http://localhost:8000', 'health_path': '/metrics'}
        }

    def start_monitoring_stack(self) -> bool:
        """Start the complete monitoring stack."""
        logger.info("Starting EnterpriseHub monitoring stack...")

        try:
            # Validate configuration files
            if not self._validate_configurations():
                logger.error("Configuration validation failed")
                return False

            # Start services
            cmd = [
                'docker-compose',
                '-f', str(self.docker_compose_file),
                'up', '-d'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Failed to start monitoring stack: {result.stderr}")
                return False

            logger.info("Monitoring stack started successfully")

            # Wait for services to be healthy
            return self._wait_for_services_healthy()

        except Exception as e:
            logger.error(f"Error starting monitoring stack: {e}")
            return False

    def stop_monitoring_stack(self) -> bool:
        """Stop the monitoring stack."""
        logger.info("Stopping EnterpriseHub monitoring stack...")

        try:
            cmd = [
                'docker-compose',
                '-f', str(self.docker_compose_file),
                'down'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Failed to stop monitoring stack: {result.stderr}")
                return False

            logger.info("Monitoring stack stopped successfully")
            return True

        except Exception as e:
            logger.error(f"Error stopping monitoring stack: {e}")
            return False

    def restart_monitoring_stack(self) -> bool:
        """Restart the monitoring stack."""
        logger.info("Restarting monitoring stack...")
        return self.stop_monitoring_stack() and self.start_monitoring_stack()

    def check_stack_health(self) -> Dict[str, Any]:
        """Check health of all monitoring services."""
        logger.info("Checking monitoring stack health...")

        health_status = {
            'overall_healthy': True,
            'services': {},
            'timestamp': time.time()
        }

        for service_name, config in self.services.items():
            try:
                health_url = f"{config['url']}{config['health_path']}"
                response = requests.get(health_url, timeout=10)

                is_healthy = response.status_code == 200
                health_status['services'][service_name] = {
                    'healthy': is_healthy,
                    'status_code': response.status_code,
                    'response_time_ms': response.elapsed.total_seconds() * 1000
                }

                if not is_healthy:
                    health_status['overall_healthy'] = False

                logger.info(f"Service {service_name}: {'✓' if is_healthy else '✗'}")

            except Exception as e:
                health_status['services'][service_name] = {
                    'healthy': False,
                    'error': str(e)
                }
                health_status['overall_healthy'] = False
                logger.error(f"Service {service_name}: ✗ ({e})")

        return health_status

    def deploy_dashboards(self) -> bool:
        """Deploy Grafana dashboards via API."""
        logger.info("Deploying Grafana dashboards...")

        grafana_url = "http://localhost:3000"
        auth = ('admin', os.getenv('GRAFANA_ADMIN_PASSWORD', 'enterprisehub_admin'))

        dashboards_dir = self.monitoring_config_dir / "grafana" / "dashboards"

        if not dashboards_dir.exists():
            logger.error(f"Dashboards directory not found: {dashboards_dir}")
            return False

        success_count = 0
        total_count = 0

        for dashboard_file in dashboards_dir.glob("*.json"):
            total_count += 1

            try:
                with open(dashboard_file, 'r') as f:
                    dashboard_data = json.load(f)

                # Prepare dashboard for API
                api_payload = {
                    "dashboard": dashboard_data.get("dashboard", dashboard_data),
                    "overwrite": True
                }

                response = requests.post(
                    f"{grafana_url}/api/dashboards/db",
                    json=api_payload,
                    auth=auth,
                    timeout=30
                )

                if response.status_code in [200, 201]:
                    logger.info(f"✓ Deployed dashboard: {dashboard_file.name}")
                    success_count += 1
                else:
                    logger.error(f"✗ Failed to deploy {dashboard_file.name}: {response.text}")

            except Exception as e:
                logger.error(f"✗ Error deploying {dashboard_file.name}: {e}")

        logger.info(f"Dashboard deployment complete: {success_count}/{total_count} successful")
        return success_count == total_count

    def reload_prometheus_config(self) -> bool:
        """Reload Prometheus configuration without restart."""
        logger.info("Reloading Prometheus configuration...")

        try:
            response = requests.post(
                "http://localhost:9090/-/reload",
                timeout=30
            )

            if response.status_code == 200:
                logger.info("✓ Prometheus configuration reloaded successfully")
                return True
            else:
                logger.error(f"✗ Failed to reload Prometheus config: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"✗ Error reloading Prometheus config: {e}")
            return False

    def test_alert_rules(self) -> Dict[str, Any]:
        """Test alert rules configuration."""
        logger.info("Testing alert rules configuration...")

        try:
            # Query Prometheus for rule validation
            response = requests.get(
                "http://localhost:9090/api/v1/rules",
                timeout=30
            )

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to query rules: {response.status_code}'
                }

            rules_data = response.json()

            rule_groups = rules_data.get('data', {}).get('groups', [])

            results = {
                'success': True,
                'total_groups': len(rule_groups),
                'total_rules': 0,
                'groups': []
            }

            for group in rule_groups:
                group_info = {
                    'name': group.get('name'),
                    'file': group.get('file'),
                    'rules': len(group.get('rules', [])),
                    'interval': group.get('interval'),
                    'valid': True
                }

                results['total_rules'] += group_info['rules']
                results['groups'].append(group_info)

            logger.info(f"✓ Alert rules validation: {results['total_groups']} groups, {results['total_rules']} rules")
            return results

        except Exception as e:
            logger.error(f"✗ Error testing alert rules: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of key enterprise metrics."""
        logger.info("Retrieving enterprise metrics summary...")

        metrics_queries = {
            'service_availability': '1 - (rate(http_requests_total{code=~"5.."}[5m]) / rate(http_requests_total[5m]))',
            'api_response_time_95th': 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))',
            'active_connections': 'active_websocket_connections',
            'ml_inference_time': 'histogram_quantile(0.95, rate(ml_inference_duration_seconds_bucket[5m]))',
            'coaching_effectiveness': '(sum(rate(coaching_sessions_improved_total[1h])) / sum(rate(coaching_sessions_total[1h]))) * 100',
            'monthly_roi': 'coaching_revenue_impact_monthly'
        }

        summary = {
            'timestamp': time.time(),
            'metrics': {}
        }

        for metric_name, query in metrics_queries.items():
            try:
                response = requests.get(
                    f"http://localhost:9090/api/v1/query",
                    params={'query': query},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    result = data.get('data', {}).get('result', [])

                    if result:
                        value = float(result[0]['value'][1])
                        summary['metrics'][metric_name] = {
                            'value': value,
                            'status': 'ok'
                        }
                    else:
                        summary['metrics'][metric_name] = {
                            'value': None,
                            'status': 'no_data'
                        }

            except Exception as e:
                summary['metrics'][metric_name] = {
                    'value': None,
                    'status': 'error',
                    'error': str(e)
                }

        return summary

    def _validate_configurations(self) -> bool:
        """Validate monitoring configuration files."""
        logger.info("Validating monitoring configurations...")

        required_files = [
            'prometheus.yml',
            'alert_rules.yml',
            'coaching_alerts.yml',
            'alertmanager.yml',
            'docker-compose.monitoring.yml'
        ]

        for file_name in required_files:
            file_path = self.monitoring_config_dir / file_name
            if not file_path.exists():
                logger.error(f"Required configuration file missing: {file_path}")
                return False

        # Validate YAML syntax
        yaml_files = ['prometheus.yml', 'alert_rules.yml', 'coaching_alerts.yml', 'alertmanager.yml']

        for yaml_file in yaml_files:
            file_path = self.monitoring_config_dir / yaml_file
            try:
                with open(file_path, 'r') as f:
                    yaml.safe_load(f)
                logger.info(f"✓ {yaml_file} syntax valid")
            except yaml.YAMLError as e:
                logger.error(f"✗ {yaml_file} syntax error: {e}")
                return False

        logger.info("✓ All configuration files validated")
        return True

    def _wait_for_services_healthy(self, timeout: int = 300) -> bool:
        """Wait for all services to become healthy."""
        logger.info(f"Waiting for services to become healthy (timeout: {timeout}s)...")

        start_time = time.time()
        check_interval = 10

        while time.time() - start_time < timeout:
            health_status = self.check_stack_health()

            if health_status['overall_healthy']:
                logger.info("✓ All monitoring services are healthy")
                return True

            logger.info(f"Waiting for services... ({int(time.time() - start_time)}s elapsed)")
            time.sleep(check_interval)

        logger.error("✗ Timeout waiting for services to become healthy")
        return False

def main():
    parser = argparse.ArgumentParser(description='Manage EnterpriseHub monitoring stack')
    parser.add_argument('--project-root', default='.', help='Project root directory')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Start command
    subparsers.add_parser('start', help='Start monitoring stack')

    # Stop command
    subparsers.add_parser('stop', help='Stop monitoring stack')

    # Restart command
    subparsers.add_parser('restart', help='Restart monitoring stack')

    # Health check command
    subparsers.add_parser('health', help='Check stack health')

    # Deploy dashboards command
    subparsers.add_parser('deploy-dashboards', help='Deploy Grafana dashboards')

    # Reload config command
    subparsers.add_parser('reload-prometheus', help='Reload Prometheus configuration')

    # Test alerts command
    subparsers.add_parser('test-alerts', help='Test alert rules configuration')

    # Metrics summary command
    subparsers.add_parser('metrics-summary', help='Get enterprise metrics summary')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    manager = MonitoringManager(args.project_root)

    try:
        if args.command == 'start':
            success = manager.start_monitoring_stack()
            if success:
                print("✓ Monitoring stack started successfully")
                print("Access points:")
                print("  - Grafana: http://localhost:3000 (admin/enterprisehub_admin)")
                print("  - Prometheus: http://localhost:9090")
                print("  - AlertManager: http://localhost:9093")
            return 0 if success else 1

        elif args.command == 'stop':
            success = manager.stop_monitoring_stack()
            return 0 if success else 1

        elif args.command == 'restart':
            success = manager.restart_monitoring_stack()
            return 0 if success else 1

        elif args.command == 'health':
            health_status = manager.check_stack_health()
            print(json.dumps(health_status, indent=2))
            return 0 if health_status['overall_healthy'] else 1

        elif args.command == 'deploy-dashboards':
            success = manager.deploy_dashboards()
            return 0 if success else 1

        elif args.command == 'reload-prometheus':
            success = manager.reload_prometheus_config()
            return 0 if success else 1

        elif args.command == 'test-alerts':
            results = manager.test_alert_rules()
            print(json.dumps(results, indent=2))
            return 0 if results['success'] else 1

        elif args.command == 'metrics-summary':
            summary = manager.get_metrics_summary()
            print(json.dumps(summary, indent=2))
            return 0

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())