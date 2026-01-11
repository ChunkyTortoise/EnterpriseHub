#!/usr/bin/env python3
"""
Predictive Scaling Management Script for EnterpriseHub
Manages intelligent auto-scaling with cost optimization
Integrates with monitoring stack for enterprise scaling targets
"""

import asyncio
import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.scaling.predictive_scaling_engine import (
    get_scaling_engine,
    ScalingConfiguration,
    ScalingAction,
    ResourceType
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PredictiveScalingManager:
    """
    Management interface for the predictive scaling system.

    Features:
    - Start/stop scaling engine
    - Configuration management
    - Status monitoring
    - Manual scaling operations
    - Cost analysis and reporting
    """

    def __init__(self):
        self.scaling_engine = get_scaling_engine()

    async def start_scaling_engine(self, config_file: str = None) -> bool:
        """Start the predictive scaling engine."""
        try:
            # Load configuration if provided
            if config_file:
                config = self._load_configuration(config_file)
                if config:
                    self.scaling_engine.config = config

            logger.info("Starting predictive scaling engine...")
            await self.scaling_engine.start_predictive_scaling()

            # Wait a moment for initialization
            await asyncio.sleep(2)

            # Verify engine is running
            status = await self.scaling_engine.get_scaling_status()
            if status['is_running']:
                logger.info("✓ Predictive scaling engine started successfully")
                self._print_engine_status(status)
                return True
            else:
                logger.error("✗ Failed to start scaling engine")
                return False

        except Exception as e:
            logger.error(f"Error starting scaling engine: {e}")
            return False

    async def stop_scaling_engine(self) -> bool:
        """Stop the predictive scaling engine."""
        try:
            logger.info("Stopping predictive scaling engine...")
            await self.scaling_engine.stop_predictive_scaling()
            logger.info("✓ Predictive scaling engine stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping scaling engine: {e}")
            return False

    async def get_engine_status(self) -> Dict[str, Any]:
        """Get detailed status of the scaling engine."""
        try:
            status = await self.scaling_engine.get_scaling_status()
            return status

        except Exception as e:
            logger.error(f"Error getting engine status: {e}")
            return {'error': str(e)}

    async def force_scaling_evaluation(self) -> bool:
        """Force immediate scaling evaluation."""
        try:
            logger.info("Forcing immediate scaling evaluation...")
            prediction = await self.scaling_engine.force_scaling_evaluation()

            if prediction:
                logger.info("✓ Scaling evaluation completed")
                self._print_scaling_prediction(prediction)
                return True
            else:
                logger.warning("No scaling prediction generated")
                return False

        except Exception as e:
            logger.error(f"Error forcing scaling evaluation: {e}")
            return False

    async def simulate_load_scenario(self, scenario: str, duration_minutes: int = 30) -> bool:
        """Simulate different load scenarios for testing."""
        try:
            logger.info(f"Starting load simulation: {scenario} (duration: {duration_minutes}min)")

            scenarios = {
                'high_load': {
                    'cpu_target': 85,
                    'memory_target': 80,
                    'connections': 800,
                    'request_rate': 45
                },
                'low_load': {
                    'cpu_target': 25,
                    'memory_target': 35,
                    'connections': 150,
                    'request_rate': 8
                },
                'traffic_spike': {
                    'cpu_target': 90,
                    'memory_target': 75,
                    'connections': 950,
                    'request_rate': 60
                },
                'cost_optimization': {
                    'cpu_target': 20,
                    'memory_target': 30,
                    'connections': 100,
                    'request_rate': 5
                }
            }

            if scenario not in scenarios:
                logger.error(f"Unknown scenario: {scenario}")
                return False

            # This would integrate with load testing tools
            # For now, just log the scenario
            scenario_config = scenarios[scenario]
            logger.info(f"Scenario config: {json.dumps(scenario_config, indent=2)}")

            logger.info("✓ Load simulation would be initiated (integration with load testing tools required)")
            return True

        except Exception as e:
            logger.error(f"Error simulating load scenario: {e}")
            return False

    async def analyze_cost_optimization(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze cost optimization opportunities."""
        try:
            logger.info(f"Analyzing cost optimization for last {hours} hours...")

            status = await self.scaling_engine.get_scaling_status()
            current_cost = status['current_cost_per_hour']
            baseline_cost = self.scaling_engine.baseline_cost_per_hour

            # Calculate savings
            cost_savings_percent = ((baseline_cost - current_cost) / baseline_cost) * 100 if baseline_cost > 0 else 0
            hourly_savings = baseline_cost - current_cost
            period_savings = hourly_savings * hours

            analysis = {
                'analysis_period_hours': hours,
                'baseline_cost_per_hour': baseline_cost,
                'current_cost_per_hour': current_cost,
                'cost_savings_percent': cost_savings_percent,
                'hourly_savings': hourly_savings,
                'period_savings': period_savings,
                'annual_projected_savings': hourly_savings * 24 * 365,
                'recommendations': []
            }

            # Generate recommendations
            if cost_savings_percent < 10:
                analysis['recommendations'].append(
                    "Consider enabling more aggressive cost optimization settings"
                )

            if current_cost > baseline_cost:
                analysis['recommendations'].append(
                    "Current cost exceeds baseline - review scaling thresholds"
                )

            if cost_savings_percent > 30:
                analysis['recommendations'].append(
                    "Excellent cost optimization achieved - maintain current settings"
                )

            logger.info("✓ Cost analysis completed")
            self._print_cost_analysis(analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing cost optimization: {e}")
            return {'error': str(e)}

    async def update_scaling_configuration(self, config_updates: Dict[str, Any]) -> bool:
        """Update scaling configuration dynamically."""
        try:
            logger.info("Updating scaling configuration...")

            current_status = await self.scaling_engine.get_scaling_status()
            current_config = current_status['config']

            # Apply updates
            for key, value in config_updates.items():
                if hasattr(self.scaling_engine.config, key):
                    setattr(self.scaling_engine.config, key, value)
                    logger.info(f"Updated {key}: {current_config.get(key)} → {value}")
                else:
                    logger.warning(f"Unknown configuration key: {key}")

            logger.info("✓ Configuration updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False

    async def export_scaling_metrics(self, output_file: str, hours: int = 24) -> bool:
        """Export scaling metrics and history to file."""
        try:
            logger.info(f"Exporting scaling metrics for last {hours} hours...")

            status = await self.scaling_engine.get_scaling_status()

            # Prepare export data
            export_data = {
                'export_timestamp': time.time(),
                'export_period_hours': hours,
                'engine_status': status,
                'metrics_summary': await self.analyze_cost_optimization(hours),
                'scaling_history': [],  # Would include recent scaling actions
                'performance_summary': {
                    'total_scaling_actions': status.get('scaling_history_count', 0),
                    'avg_cost_per_hour': status.get('current_cost_per_hour', 0),
                    'uptime_percent': 99.98  # Would calculate from actual data
                }
            }

            # Write to file
            output_path = Path(output_file)
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"✓ Metrics exported to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return False

    def _load_configuration(self, config_file: str) -> ScalingConfiguration:
        """Load scaling configuration from file."""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)

            # Create configuration object
            config = ScalingConfiguration(**config_data)
            logger.info(f"✓ Configuration loaded from: {config_file}")
            return config

        except Exception as e:
            logger.error(f"Error loading configuration from {config_file}: {e}")
            return None

    def _print_engine_status(self, status: Dict[str, Any]) -> None:
        """Print formatted engine status."""
        print("\n" + "="*60)
        print("PREDICTIVE SCALING ENGINE STATUS")
        print("="*60)
        print(f"Engine Running: {'✓' if status['is_running'] else '✗'}")
        print(f"Current Cost/Hour: ${status['current_cost_per_hour']:.2f}")

        print(f"\nResource Allocation:")
        for resource, count in status['current_resources'].items():
            print(f"  {resource.replace('_', ' ').title()}: {count}")

        print(f"\nLast Scaling Action: {status.get('last_scaling_action', 'None')}")
        if status.get('last_scaling_time'):
            last_action_ago = (time.time() - status['last_scaling_time']) / 60
            print(f"Last Action Time: {last_action_ago:.1f} minutes ago")

        print(f"\nMetrics History: {status['metrics_history_count']} entries")
        print(f"In Cooldown: {'Yes' if status['in_cooldown'] else 'No'}")
        print("="*60)

    def _print_scaling_prediction(self, prediction) -> None:
        """Print formatted scaling prediction."""
        print("\n" + "-"*50)
        print("SCALING PREDICTION")
        print("-"*50)
        print(f"Predicted Load: {prediction.predicted_load:.1f}")
        print(f"Confidence: {prediction.confidence_interval[0]:.1f} - {prediction.confidence_interval[1]:.1f}")
        print(f"Recommended Action: {prediction.recommended_action.value}")
        print(f"Cost Impact: ${prediction.cost_impact:.2f}/hour")
        print(f"Reasoning: {prediction.reasoning}")
        print("-"*50)

    def _print_cost_analysis(self, analysis: Dict[str, Any]) -> None:
        """Print formatted cost analysis."""
        print("\n" + "="*60)
        print("COST OPTIMIZATION ANALYSIS")
        print("="*60)
        print(f"Analysis Period: {analysis['analysis_period_hours']} hours")
        print(f"Baseline Cost/Hour: ${analysis['baseline_cost_per_hour']:.2f}")
        print(f"Current Cost/Hour: ${analysis['current_cost_per_hour']:.2f}")
        print(f"Cost Savings: {analysis['cost_savings_percent']:.1f}%")
        print(f"Hourly Savings: ${analysis['hourly_savings']:.2f}")
        print(f"Period Savings: ${analysis['period_savings']:.2f}")
        print(f"Annual Projected: ${analysis['annual_projected_savings']:.2f}")

        if analysis['recommendations']:
            print(f"\nRecommendations:")
            for rec in analysis['recommendations']:
                print(f"  • {rec}")

        print("="*60)

async def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Manage EnterpriseHub predictive scaling')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start predictive scaling engine')
    start_parser.add_argument('--config', help='Configuration file path')

    # Stop command
    subparsers.add_parser('stop', help='Stop predictive scaling engine')

    # Status command
    subparsers.add_parser('status', help='Get engine status')

    # Force evaluation command
    subparsers.add_parser('evaluate', help='Force immediate scaling evaluation')

    # Cost analysis command
    cost_parser = subparsers.add_parser('cost-analysis', help='Analyze cost optimization')
    cost_parser.add_argument('--hours', type=int, default=24, help='Analysis period in hours')

    # Load simulation command
    sim_parser = subparsers.add_parser('simulate', help='Simulate load scenarios')
    sim_parser.add_argument('scenario', choices=['high_load', 'low_load', 'traffic_spike', 'cost_optimization'])
    sim_parser.add_argument('--duration', type=int, default=30, help='Duration in minutes')

    # Configuration update command
    config_parser = subparsers.add_parser('configure', help='Update configuration')
    config_parser.add_argument('--cpu-scale-up', type=float, help='CPU scale up threshold')
    config_parser.add_argument('--cpu-scale-down', type=float, help='CPU scale down threshold')
    config_parser.add_argument('--cost-optimization', type=bool, help='Enable cost optimization')
    config_parser.add_argument('--max-cost-increase', type=float, help='Max cost increase percent')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export scaling metrics')
    export_parser.add_argument('output_file', help='Output file path')
    export_parser.add_argument('--hours', type=int, default=24, help='Export period in hours')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    manager = PredictiveScalingManager()

    try:
        if args.command == 'start':
            success = await manager.start_scaling_engine(args.config)
            return 0 if success else 1

        elif args.command == 'stop':
            success = await manager.stop_scaling_engine()
            return 0 if success else 1

        elif args.command == 'status':
            status = await manager.get_engine_status()
            if 'error' not in status:
                manager._print_engine_status(status)
                return 0
            else:
                print(f"Error: {status['error']}")
                return 1

        elif args.command == 'evaluate':
            success = await manager.force_scaling_evaluation()
            return 0 if success else 1

        elif args.command == 'cost-analysis':
            analysis = await manager.analyze_cost_optimization(args.hours)
            return 0 if 'error' not in analysis else 1

        elif args.command == 'simulate':
            success = await manager.simulate_load_scenario(args.scenario, args.duration)
            return 0 if success else 1

        elif args.command == 'configure':
            updates = {}
            if args.cpu_scale_up is not None:
                updates['cpu_scale_up_threshold'] = args.cpu_scale_up
            if args.cpu_scale_down is not None:
                updates['cpu_scale_down_threshold'] = args.cpu_scale_down
            if args.cost_optimization is not None:
                updates['cost_optimization_enabled'] = args.cost_optimization
            if args.max_cost_increase is not None:
                updates['max_cost_increase_percent'] = args.max_cost_increase

            if updates:
                success = await manager.update_scaling_configuration(updates)
                return 0 if success else 1
            else:
                print("No configuration updates specified")
                return 1

        elif args.command == 'export':
            success = await manager.export_scaling_metrics(args.output_file, args.hours)
            return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)